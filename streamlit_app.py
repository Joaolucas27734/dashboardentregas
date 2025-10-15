import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- Configuração da página ---
st.set_page_config(page_title="Dashboard Entregas", layout="wide")

# --- Planilha ---
sheet_id = "1dYVZjzCtDBaJ6QdM81WP2k51QodDGZHzKEhzKHSp7v8"
url_pedidos = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&sheet=Pedidos"
url_login = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&sheet=Login"

# --- Carregar dados ---
df = pd.read_csv(url_pedidos)
df_login = pd.read_csv(url_login)

# --- Processar datas ---
df["data_envio"] = pd.to_datetime(df.iloc[:,1], errors="coerce")
df["data_entrega"] = pd.to_datetime(df.iloc[:,2], errors="coerce")
df["dias_entrega"] = (df["data_entrega"] - df["data_envio"]).dt.days
df["estado"] = df.iloc[:,3].str.upper()
df["cidade"] = df.iloc[:,4].astype(str).str.title()
df["numero_pedido"] = df.iloc[:,0]
df["status"] = df["data_entrega"].apply(lambda x: "Entregue" if pd.notna(x) else "Não Entregue")

# --- Inicializar session_state ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""

# --- Login ---
if not st.session_state.logged_in:
    st.title("🔐 Login")
    usuario_input = st.text_input("Usuário")
    senha_input = st.text_input("Senha", type="password")
    login_button = st.button("Login")

    if login_button:
        user_valid = df_login[(df_login.iloc[:,0]==usuario_input) & (df_login.iloc[:,1]==senha_input)]
        if not user_valid.empty:
            st.session_state.logged_in = True
            st.session_state.usuario = usuario_input
            st.success("Login realizado com sucesso!")
            st.experimental_rerun()  # Atualiza a página para mostrar abas
        else:
            st.error("Usuário ou senha incorretos.")
else:
    # --- Abas do dashboard ---
    st.sidebar.info(f"Usuário logado: {st.session_state.usuario}")
    tab1, tab2 = st.tabs(["Dashboard", "Resumo de Pedidos"])

    with tab1:
        st.subheader("📦 Dashboard de Entregas – Brasil")

        # --- Filtro por data ---
        st.markdown("### 📅 Filtrar por Data de Envio")
        start_date = st.date_input("Data inicial", value=df["data_envio"].min())
        end_date = st.date_input("Data final", value=df["data_envio"].max())
        df_filtered = df[(df["data_envio"] >= pd.to_datetime(start_date)) & 
                         (df["data_envio"] <= pd.to_datetime(end_date))]

        # --- Métricas ---
        df_valid = df_filtered.dropna(subset=["dias_entrega"])
        total = len(df_valid)
        media = df_valid["dias_entrega"].mean() if total>0 else 0
        mediana = df_valid["dias_entrega"].median() if total>0 else 0
        pct_ate3 = (df_valid["dias_entrega"]<=3).sum()/total*100 if total>0 else 0
        pct_atraso5 = (df_valid["dias_entrega"]>5).sum()/total*100 if total>0 else 0
        desvio = df_valid["dias_entrega"].std() if total>0 else 0
        entregues = (df_filtered["status"]=="Entregue").sum()
        nao_entregues = (df_filtered["status"]=="Não Entregue").sum()

        st.subheader("📊 Principais Métricas")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("Tempo médio (dias)", f"{media:.1f}")
        col2.metric("Mediana (dias)", f"{mediana:.0f}")
        col3.metric("% Entregas ≤3 dias", f"{pct_ate3:.1f}%")
        col4.metric("% Atrasos (>5 dias)", f"{pct_atraso5:.1f}%")
        col5.metric("Desvio Padrão", f"{desvio:.1f}")
        col6.metric("Pedidos Entregues / Não Entregues", f"{entregues} / {nao_entregues}")

        # --- Resumo por estado ---
        resumo_estado = df_valid.groupby("estado")["dias_entrega"].agg([
            ("Total Pedidos","count"),
            ("% Entregas ≤3 dias", lambda x: (x<=3).sum()/len(x)*100)
        ]).reset_index()

        # --- Mapa do Brasil ---
        st.subheader("🌎 Mapa do Brasil – % Entregas ≤3 dias")
        fig_map = px.choropleth_mapbox(
            resumo_estado,
            geojson="https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson",
            locations="estado",
            featureidkey="properties.sigla",
            color="% Entregas ≤3 dias",
            hover_data=["Total Pedidos"],
            color_continuous_scale="Greens",
            mapbox_style="carto-positron",
            zoom=3.5,
            center={"lat":-14.2350,"lon":-51.9253},
            opacity=0.6
        )
        st.plotly_chart(fig_map, use_container_width=True)

        # --- Dropdown Estado / Boxplot cidades ---
        st.subheader("📈 Entregas por Estado e Cidade")
        estados = sorted(df_valid["estado"].unique())
        estado_sel = st.selectbox("Selecione um estado para ver as cidades", ["Todos"] + estados)

        if estado_sel == "Todos":
            fig_estado = px.bar(
                resumo_estado,
                x="estado",
                y="% Entregas ≤3 dias",
                hover_data=["Total Pedidos"],
                color="% Entregas ≤3 dias",
                color_continuous_scale="Greens",
                title="Entregas ≤3 dias por Estado"
            )
            st.plotly_chart(fig_estado, use_container_width=True)
        else:
            df_cidades = df_valid[df_valid["estado"]==estado_sel]
            resumo_cidade = df_cidades.groupby("cidade")["dias_entrega"].agg([
                ("Total Pedidos","count"),
                ("Média Dias","mean"),
                ("Mediana Dias","median")
            ]).reset_index()
            fig_cidade = px.box(
                df_cidades,
                x="cidade",
                y="dias_entrega",
                points="all",
                color="cidade",
                title=f"Distribuição de Dias de Entrega por Cidade - {estado_sel}"
            )
            st.plotly_chart(fig_cidade, use_container_width=True)

        # --- Histograma ---
        st.subheader("📊 Distribuição de Dias de Entrega")
        freq = df_valid["dias_entrega"].value_counts().sort_index()
        st.bar_chart(freq)

    with tab2:
        st.subheader("📝 Resumo de Pedidos")
        st.dataframe(df_filtered[["numero_pedido","data_envio","data_entrega","dias_entrega","estado","cidade","status"]].sort_values(by="data_envio"))

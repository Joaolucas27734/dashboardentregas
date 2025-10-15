import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- Configuração da página ---
st.set_page_config(page_title="Dashboard Interativo de Entregas", layout="wide")

# --- Inicializar session_state para login ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.usuario = ""

# --- Carregar dados ---
sheet_id = "1dYVZjzCtDBaJ6QdM81WP2k51QodDGZHzKEhzKHSp7v8"

# URL da aba Login
url_login = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=1093122103"
df_login = pd.read_csv(url_login)

# URL da aba de pedidos (supondo que seja a aba principal, gid=0)
url_pedidos = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
df = pd.read_csv(url_pedidos)

# --- Login ---
if not st.session_state.logged_in:
    st.title("🔐 Login")
    usuario_input = st.text_input("Usuário")
    senha_input = st.text_input("Senha", type="password")
    login_button = st.button("Login")
    
    if login_button:
        valid_user = df_login[(df_login.iloc[:,0]==usuario_input) & (df_login.iloc[:,1]==senha_input)]
        if not valid_user.empty:
            st.session_state.logged_in = True
            st.session_state.usuario = usuario_input
            st.success(f"Login realizado com sucesso! Bem-vindo, {usuario_input}")
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha incorretos.")
else:
    st.title(f"📦 Dashboard Interativo de Entregas – Bem-vindo {st.session_state.usuario}")

    # --- Filtro por data ---
    df["data_envio"] = pd.to_datetime(df.iloc[:,1], errors="coerce")
    df["data_entrega"] = pd.to_datetime(df.iloc[:,2], errors="coerce")
    df["dias_entrega"] = (df["data_entrega"] - df["data_envio"]).dt.days
    df["estado"] = df.iloc[:,3].str.upper()
    df["cidade"] = df.iloc[:,4].astype(str).str.title()
    df["pedido_status"] = df["data_entrega"].notna().map({True:"Entregue", False:"Não entregue"})

    st.subheader("📅 Filtro de Datas")
    min_data = df["data_envio"].min()
    max_data = df["data_envio"].max()
    data_range = st.date_input("Selecione o período de envio", [min_data, max_data])

    df_filtered = df[(df["data_envio"] >= pd.to_datetime(data_range[0])) & 
                     (df["data_envio"] <= pd.to_datetime(data_range[1]))]
    
    # --- Métricas principais ---
    df_valid = df_filtered.dropna(subset=["dias_entrega"])
    total = len(df_valid)
    media = df_valid["dias_entrega"].mean() if total>0 else 0
    mediana = df_valid["dias_entrega"].median() if total>0 else 0
    pct_ate3 = (df_valid["dias_entrega"]<=3).sum()/total*100 if total>0 else 0
    pct_atraso5 = (df_valid["dias_entrega"]>5).sum()/total*100 if total>0 else 0
    desvio = df_valid["dias_entrega"].std() if total>0 else 0
    total_entregue = (df_filtered["pedido_status"]=="Entregue").sum()
    total_nao_entregue = (df_filtered["pedido_status"]=="Não entregue").sum()

    st.subheader("📊 Principais Métricas")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Tempo médio (dias)", f"{media:.1f}")
    col2.metric("Mediana (dias)", f"{mediana:.0f}")
    col3.metric("% Entregas ≤3 dias", f"{pct_ate3:.1f}%")
    col4.metric("% Atrasos (>5 dias)", f"{pct_atraso5:.1f}%")
    col5.metric("Desvio Padrão", f"{desvio:.1f}")
    col6.metric("Pedidos Entregues / Não Entregues", f"{total_entregue} / {total_nao_entregue}")

    # --- Mapa do Brasil ---
    st.subheader("🌎 Mapa do Brasil – % Entregas ≤3 dias por Estado")
    resumo_estado = df_valid.groupby("estado")["dias_entrega"].agg([
        ("Total Pedidos","count"),
        ("% Entregas ≤3 dias", lambda x: (x<=3).sum()/len(x)*100)
    ]).reset_index()

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

    # --- Dropdown por estado para ver cidades ---
    st.subheader("📈 Gráfico de Entregas por Cidade")
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

        fig_cidade = px.bar(
            resumo_cidade,
            x="cidade",
            y="Média Dias",
            hover_data=["Total Pedidos","Mediana Dias"],
            color="Média Dias",
            color_continuous_scale="Blues",
            title=f"Tempo médio de entrega por Cidade - {estado_sel}"
        )
        st.plotly_chart(fig_cidade, use_container_width=True)

    # --- Tabela de pedidos ---
    st.subheader("📋 Resumo de Pedidos")
    st.dataframe(df_filtered[["pedido_numero", "estado", "cidade", "data_envio", "data_entrega", "dias_entrega", "pedido_status"]])

    # --- Histograma ---
    st.subheader("📊 Distribuição de Dias de Entrega")
    freq = df_valid["dias_entrega"].value_counts().sort_index()
    st.bar_chart(freq)

    # --- Instruções ---
    st.markdown("""
### ℹ️ Como interpretar este dashboard
- **Tempo médio**: média de dias que os pedidos levam para chegar
- **Mediana**: dia mais comum de entrega
- **% Entregas ≤3 dias**: rapidez das entregas
- **% Atrasos >5 dias**: alertas de atraso
- **Desvio padrão**: consistência do tempo de entrega
- **Mapa do Brasil**: verde = entregas rápidas
- **Dropdown de Estado**: filtra cidades de cada estado (mostra média/mediana)
- **Tabela de Pedidos**: detalhes completos de cada pedido
- **Histograma**: visualiza a distribuição dos dias de entrega
""")

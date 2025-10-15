import streamlit as st
import pandas as pd
import plotly.express as px

# --- Configuração da página ---
st.set_page_config(page_title="Dashboard Interativo de Entregas", layout="wide")
st.title("📦 Dashboard Interativo de Entregas – Brasil")

# --- Ler planilha ---
sheet_id = "1dYVZjzCtDBaJ6QdM81WP2k51QodDGZHzKEhzKHSp7v8"
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
df = pd.read_csv(url)

# --- Processar datas ---
df["data_envio"] = pd.to_datetime(df.iloc[:,1], errors="coerce")
df["data_entrega"] = pd.to_datetime(df.iloc[:,2], errors="coerce")
df["dias_entrega"] = (df["data_entrega"] - df["data_envio"]).dt.days

# --- Colunas de estado, cidade e código de rastreio ---
df["estado"] = df.iloc[:,3].str.upper()  # coluna D
df["cidade"] = df.iloc[:,4].astype(str).str.title()  # coluna E
df["codigo_rastreio"] = df.iloc[:,5].astype(str)  # coluna F
df["link_jt"] = df["codigo_rastreio"].apply(
    lambda x: f"https://www.jtexpress.com.br/rastreamento?codigo={x}" if x.strip() != "" else ""
)

# --- Status de entrega ---
df["Status"] = df["data_entrega"].apply(lambda x: "Entregue" if pd.notna(x) else "Não entregue")

# --- Filtro por data ---
st.sidebar.subheader("📅 Filtrar por Data de Envio")
data_min = df["data_envio"].min()
data_max = df["data_envio"].max()
data_inicio, data_fim = st.sidebar.date_input("Selecione o período:", [data_min, data_max])
df_filtrado = df[(df["data_envio"] >= pd.to_datetime(data_inicio)) & (df["data_envio"] <= pd.to_datetime(data_fim))]

# --- Dados válidos ---
df_valid = df_filtrado.dropna(subset=["dias_entrega"])
total = len(df_valid)
media = df_valid["dias_entrega"].mean() if total>0 else 0
mediana = df_valid["dias_entrega"].median() if total>0 else 0
pct_ate3 = (df_valid["dias_entrega"]<=3).sum()/total*100 if total>0 else 0
pct_atraso5 = (df_valid["dias_entrega"]>5).sum()/total*100 if total>0 else 0
desvio = df_valid["dias_entrega"].std() if total>0 else 0

# --- Contagem entregues/não entregues ---
qtd_entregue = (df_filtrado["Status"]=="Entregue").sum()
qtd_nao_entregue = (df_filtrado["Status"]=="Não entregue").sum()

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📝 Resumo de Pedidos", "📊 Probabilidade de Entrega"])

# ------------------- Aba 1: Dashboard -------------------
with tab1:
    # --- Cards principais ---
    st.subheader("📊 Principais Métricas")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Tempo médio (dias)", f"{media:.1f}")
    col2.metric("Mediana (dias)", f"{mediana:.0f}")
    col3.metric("% Entregas ≤3 dias", f"{pct_ate3:.1f}%")
    col4.metric("% Atrasos (>5 dias)", f"{pct_atraso5:.1f}%")
    col5.metric("Desvio Padrão", f"{desvio:.1f}")
    col6.metric("Entregues / Não", f"{qtd_entregue} / {qtd_nao_entregue}")

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

    # --- Dropdown para selecionar estado ---
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

        fig_box = px.box(
            df_cidades,
            x="cidade",
            y="dias_entrega",
            color="cidade",
            title=f"Distribuição de Dias de Entrega por Cidade - {estado_sel}",
            points="all"
        )
        st.plotly_chart(fig_box, use_container_width=True)

    # --- Histograma de dias de entrega ---
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
    - **Dropdown de Estado**: filtra cidades de cada estado (boxplot mostra distribuição)
    - **Tabela de Pedidos**: detalhes completos de cada pedido
    - **Histograma**: visualiza a distribuição dos dias de entrega
    """)

# ------------------- Aba 2: Resumo de Pedidos -------------------
with tab2:
    st.subheader("📝 Tabela de Pedidos")
    tabela_resumo = df_filtrado[[df.columns[0], "data_envio", "data_entrega", "dias_entrega",
                                 "estado", "cidade", "Status", "codigo_rastreio", "link_jt"]].sort_values("data_envio")
    tabela_resumo = tabela_resumo.rename(columns={df.columns[0]: "Número do Pedido",
                                                  "codigo_rastreio": "Código de Rastreio",
                                                  "link_jt": "Link J&T"})
    st.dataframe(tabela_resumo)

# ------------------- Aba 3: Probabilidade de Entrega -------------------
with tab3:
    st.subheader("📈 Probabilidade de Entrega por Estado")

    prob_estado = df_valid.groupby("estado")["dias_entrega"].agg([
        ("Total Pedidos", "count"),
        ("Prob ≤3 dias", lambda x: (x <= 3).sum() / len(x) * 100),
        ("Prob ≤5 dias", lambda x: (x <= 5).sum() / len(x) * 100)
    ]).reset_index()

    # Tabela de probabilidades
    st.dataframe(prob_estado.sort_values("Prob ≤3 dias", ascending=False))

    # Gráfico comparativo
    fig_prob = px.bar(
        prob_estado.melt(id_vars="estado", value_vars=["Prob ≤3 dias", "Prob ≤5 dias"],
                         var_name="Prazo", value_name="Probabilidade (%)"),
        x="estado",
        y="Probabilidade (%)",
        color="Prazo",
        barmode="group",
        title="Probabilidade de Entrega ≤3 e ≤5 dias por Estado",
        text_auto=True
    )
    st.plotly_chart(fig_prob, use_container_width=True)

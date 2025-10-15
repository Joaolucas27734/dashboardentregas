import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# --- Configuração da página ---
st.set_page_config(page_title="Dashboard Interativo de Entregas", layout="wide")
st.title("📦 Dashboard Didático de Entregas – Brasil")

# --- Session state para drill-down ---
if "estado_selecionado" not in st.session_state:
    st.session_state.estado_selecionado = None

# --- Ler planilha ---
sheet_id = "1dYVZjzCtDBaJ6QdM81WP2k51QodDGZHzKEhzKHSp7v8"
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
df = pd.read_csv(url)

# --- Processar datas ---
df["data_envio"] = pd.to_datetime(df.iloc[:,1], errors="coerce")
df["data_entrega"] = pd.to_datetime(df.iloc[:,2], errors="coerce")
df["dias_entrega"] = (df["data_entrega"] - df["data_envio"]).dt.days

# --- Colunas de estado e cidade ---
df["estado"] = df.iloc[:,3].str.upper()  # coluna D
df["cidade"] = df.iloc[:,4].astype(str).str.title()  # coluna E

# --- Filtro por estado ---
regioes = sorted(df["estado"].dropna().unique())
regiao_sel = st.selectbox("Filtrar por Estado", ["Todos"] + regioes)
df_filtrado = df if regiao_sel=="Todos" else df[df["estado"]==regiao_sel]
df_valid = df_filtrado.dropna(subset=["dias_entrega"])
total = len(df_valid)

# --- Métricas principais ---
media = df_valid["dias_entrega"].mean() if total>0 else 0
mediana = df_valid["dias_entrega"].median() if total>0 else 0
pct_ate3 = (df_valid["dias_entrega"]<=3).sum()/total*100 if total>0 else 0
pct_atraso5 = (df_valid["dias_entrega"]>5).sum()/total*100 if total>0 else 0

# --- Cards coloridos ---
st.subheader("📊 Principais Métricas")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Tempo médio (dias)", f"{media:.1f}")
col2.metric("Mediana (dias)", f"{mediana:.0f}")
col3.metric("% Entregas ≤3 dias", f"{pct_ate3:.1f}%")
col4.metric("% Atrasos (>5 dias)", f"{pct_atraso5:.1f}%")

# --- Tabela resumo por estado ---
st.subheader("📋 Resumo por Estado")
resumo = df.groupby("estado")["dias_entrega"].agg([
    ("Total Pedidos","count"),
    ("Média Dias","mean"),
    ("Mediana Dias","median"),
    ("% Entregas ≤3 dias", lambda x: (x<=3).sum()/len(x)*100),
    ("% Atrasos >5 dias", lambda x: (x>5).sum()/len(x)*100)
]).reset_index()
st.dataframe(resumo)

# --- Histograma de dias de entrega ---
st.subheader("📈 Distribuição de Dias de Entrega")
freq = df_valid["dias_entrega"].value_counts().sort_index()
st.bar_chart(freq)

# --- Mapa interativo ---
st.subheader("🌎 Mapa Interativo de Entregas")

if st.session_state.estado_selecionado is None:
    # --- Mapa do Brasil ---
    resumo_brasil = df.groupby("estado")["dias_entrega"].agg([
        ("Total","count"),
        ("% ≤3 dias", lambda x: (x<=3).sum()/len(x)*100)
    ]).reset_index()

    geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    geojson = requests.get(geojson_url).json()

    fig = px.choropleth_mapbox(
        resumo_brasil,
        geojson=geojson,
        locations="estado",
        featureidkey="properties.sigla",
        color="% ≤3 dias",
        hover_data=["Total","% ≤3 dias"],
        color_continuous_scale="Greens",
        mapbox_style="carto-positron",
        zoom=3.5,
        center={"lat":-14.2350,"lon":-51.9253},
        opacity=0.6
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- Seleção de estado para drill-down ---
    estado_click = st.selectbox("Clique no estado para ver cidades:", [""] + list(resumo_brasil["estado"]))
    if estado_click:
        st.session_state.estado_selecionado = estado_click

else:
    # --- Mapa do Estado selecionado ---
    st.subheader(f"🗺️ Mapa do Estado: {st.session_state.estado_selecionado}")
    df_estado = df[df["estado"]==st.session_state.estado_selecionado]
    resumo_cidades = df_estado.groupby("cidade")["dias_entrega"].agg([
        ("Total","count"),
        ("% ≤3 dias", lambda x: (x<=3).sum()/len(x)*100)
    ]).reset_index()

    # GeoJSON cidades do estado (exemplo RJ)
    geojson_url = f"https://raw.githubusercontent.com/kelvins/BR-municipios/master/csv/geojson/{st.session_state.estado_selecionado}.json"
    geojson = requests.get(geojson_url).json()

    fig = px.choropleth_mapbox(
        resumo_cidades,
        geojson=geojson,
        locations="cidade",
        featureidkey="properties.name",
        color="% ≤3 dias",
        hover_data=["Total","% ≤3 dias"],
        color_continuous_scale="Greens",
        mapbox_style="carto-positron",
        zoom=6,
        opacity=0.6
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- Botão voltar ao Brasil ---
    if st.button("⬅️ Voltar ao mapa do Brasil"):
        st.session_state.estado_selecionado = None

# --- Seção explicativa ---
st.markdown("""
### ℹ️ Como interpretar este dashboard
- **Tempo médio**: média de dias que os pedidos levam para chegar
- **Mediana**: dia mais comum de entrega
- **% Entregas ≤3 dias**: rapidez das entregas
- **% Atrasos >5 dias**: alertas de atraso
- **Mapa do Brasil**: verde = entregas rápidas, vermelho = atrasos
- **Mapa do Estado**: detalhamento por cidades
""")

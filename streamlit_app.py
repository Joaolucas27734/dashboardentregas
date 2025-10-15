import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# --- Configuração da página ---
st.set_page_config(page_title="Dashboard de Entregas - Brasil", layout="wide")
st.title("📦 Dashboard Didático de Entregas – Brasil")

# --- Ler planilha ---
sheet_id = "1dYVZjzCtDBaJ6QdM81WP2k51QodDGZHzKEhzKHSp7v8"
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
df = pd.read_csv(url)

# --- Processar datas ---
df["data_envio"] = pd.to_datetime(df.iloc[:,1], errors="coerce")
df["data_entrega"] = pd.to_datetime(df.iloc[:,2], errors="coerce")
df["dias_entrega"] = (df["data_entrega"] - df["data_envio"]).dt.days
df["estado"] = df.iloc[:,3].str.upper()

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
geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
geojson = requests.get(geojson_url).json()

fig = px.choropleth_mapbox(
    resumo,
    geojson=geojson,
    locations="estado",
    featureidkey="properties.sigla",
    color="% Entregas ≤3 dias",
    hover_data=["Total Pedidos","Média Dias","Mediana Dias","% Atrasos >5 dias"],
    color_continuous_scale="Greens",
    mapbox_style="carto-positron",
    zoom=3.5,
    center={"lat":-14.2350,"lon":-51.9253},
    opacity=0.6
)
st.plotly_chart(fig, use_container_width=True)

# --- Seção explicativa ---
st.markdown("""
### ℹ️ Como interpretar este dashboard
- **Tempo médio**: média de dias que os pedidos levam para chegar
- **Mediana**: dia mais comum de entrega
- **% Entregas ≤3 dias**: rapidez das entregas
- **% Atrasos >5 dias**: alertas de atraso
- **Mapa**: verde = entregas rápidas, vermelho = atrasos
""")

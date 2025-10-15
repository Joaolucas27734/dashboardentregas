import streamlit as st
import pandas as pd
import plotly.express as px

# --- Configuração da página ---
st.set_page_config(page_title="Dashboard de Entregas", layout="wide")
st.title("📦 Dashboard de Entregas por Estado/Região")

# --- Link da planilha Google Sheets (export CSV) ---
sheet_id = "1dYVZjzCtDBaJ6QdM81WP2k51QodDGZHzKEhzKHSp7v8"
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

# --- Ler dados ---
df = pd.read_csv(url)

# --- Converter colunas para datetime ---
df["data_envio"] = pd.to_datetime(df.iloc[:, 1], errors="coerce")   # coluna B
df["data_entrega"] = pd.to_datetime(df.iloc[:, 2], errors="coerce") # coluna C

# --- Criar coluna dias de entrega ---
df["dias_entrega"] = (df["data_entrega"] - df["data_envio"]).dt.days

# --- Coluna de estado/região (coluna D) ---
df["estado"] = df.iloc[:, 3].str.upper()  # garante que siglas fiquem maiúsculas

# --- Filtro por estado ---
regioes = sorted(df["estado"].dropna().unique())
regiao_sel = st.selectbox("Filtrar por Estado/Região", ["Todos"] + regioes)

if regiao_sel != "Todos":
    df_filtrado = df[df["estado"] == regiao_sel]
else:
    df_filtrado = df

# --- Filtrar apenas valores válidos de dias ---
df_valid = df_filtrado.dropna(subset=["dias_entrega"])
total = len(df_valid)

# --- Métricas principais ---
media = df_valid["dias_entrega"].mean() if total > 0 else 0
mediana = df_valid["dias_entrega"].median() if total > 0 else 0
pct_ate3 = (df_valid["dias_entrega"] <= 3).sum() / total * 100 if total > 0 else 0
pct_atraso5 = (df_valid["dias_entrega"] > 5).sum() / total * 100 if total > 0 else 0

# --- Exibição das métricas ---
st.subheader("📊 Métricas principais")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Tempo médio (dias)", f"{media:.1f}")
col2.metric("Mediana (dias)", f"{mediana:.0f}")
col3.metric("% em até 3 dias", f"{pct_ate3:.1f}%")
col4.metric("% atrasos (+5 dias)", f"{pct_atraso5:.1f}%")

# --- Tabela resumo por estado (todas as regiões) ---
st.subheader("📋 Métricas por Região")
resumo_por_regiao = df.groupby("estado")["dias_entrega"].agg([
    ("Total Pedidos", "count"),
    ("Média Dias", "mean"),
    ("Mediana Dias", "median"),
    ("% Até 3 Dias", lambda x: (x <= 3).sum()/len(x)*100),
    ("% Atrasos +5 Dias", lambda x: (x > 5).sum()/len(x)*100)
]).reset_index()
st.dataframe(resumo_por_regiao)

# --- Histograma de dias de entrega ---
st.subheader("📈 Distribuição de Dias de Entrega")
freq = df_valid["dias_entrega"].value_counts().sort_index()
st.bar_chart(freq)

# --- Mapa do Brasil interativo ---
st.subheader("🌎 Mapa de Entregas por Estado (% ≤3 dias)")

# Adiciona prefixo BR- para Plotly
df_mapa = resumo_por_regiao.copy()
df_mapa["codigo_plotly"] = "BR-" + df_mapa["estado"]

# Plotly choropleth
fig = px.choropleth(
    df_mapa,
    locations="codigo_plotly",       # usa coluna com BR-RJ, BR-SP etc.
    locationmode="ISO-3166-2",
    color="% Até 3 Dias",
    color_continuous_scale="Greens",
    scope="south america",
    labels={"% Até 3 Dias":"% Entregas ≤3 dias"}
)

st.plotly_chart(fig, use_container_width=True)

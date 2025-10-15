import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Dashboard de Entregas", layout="wide")
st.title("📦 Dashboard de Entregas por Estado/Região")

# --- Link da planilha Google Sheets (export CSV) ---
sheet_id = "1dYVZjzCtDBaJ6QdM81WP2k51QodDGZHzKEhzKHSp7v8"
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

# --- Ler dados ---
df = pd.read_csv(url)

# --- Converter colunas para datetime ---
df["data_envio"] = pd.to_datetime(df["Data Envio"], errors="coerce")
df["data_entrega"] = pd.to_datetime(df["Data Entrega"], errors="coerce")

# --- Criar coluna dias de entrega ---
df["dias_entrega"] = (df["data_entrega"] - df["data_envio"]).dt.days

# --- Verifica se existe coluna de estado/UF ---
if "Estado" in df.columns:
    df["estado"] = df["Estado"]
else:
    df["estado"] = "Todos"

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

# --- Tabela resumo por estado ---
st.subheader("📋 Resumo por Estado")
resumo = df.groupby("estado")["dias_entrega"].agg(["count","mean","median"])
st.dataframe(resumo)

# --- Histograma de dias de entrega ---
st.subheader("📈 Distribuição de Dias de Entrega")
freq = df_valid["dias_entrega"].value_counts().sort_index()
st.bar_chart(freq)

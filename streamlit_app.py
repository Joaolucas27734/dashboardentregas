import streamlit as st
import pandas as pd

st.set_page_config(page_title="Probabilidade de Entrega", layout="wide")

st.title("📦 Dashboard de Entregas por Região")

# Leitura da planilha (pode ser link bruto do GitHub)
url = "https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/data/pedidos.csv"
df = pd.read_csv(url, parse_dates=["data_envio", "data_entrega"])

# Calcular dias de entrega
df["dias_entrega"] = (df["data_entrega"] - df["data_envio"]).dt.days

# Filtrar regiões únicas
regioes = sorted(df["estado"].unique())
regiao_sel = st.selectbox("Filtrar por Estado/Região", ["Todos"] + regioes)

if regiao_sel != "Todos":
    df = df[df["estado"] == regiao_sel]

# Métricas principais
total = len(df)
media = df["dias_entrega"].mean()
mediana = df["dias_entrega"].median()
ate3 = (df["dias_entrega"] <= 3).sum() / total * 100
atrasos = (df["dias_entrega"] > 5).sum() / total * 100

st.metric("Tempo médio de entrega (dias)", f"{media:.1f}")
st.metric("Mediana", f"{mediana:.0f}")
st.metric("% em até 3 dias", f"{ate3:.1f}%")
st.metric("% atrasados (+5 dias)", f"{atrasos:.1f}%")

# Tabela resumo por estado
resumo = df.groupby("estado")["dias_entrega"].agg(["count","mean","median"])
st.subheader("📊 Resumo por Região")
st.dataframe(resumo)

# Histograma
st.bar_chart(df["dias_entrega"].value_counts().sort_index())

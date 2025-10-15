import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard de Entregas", layout="wide")

st.title("📦 Probabilidade de Entrega por Estado")

# → Link da planilha no Google Sheets (modo export CSV)
sheet_id = "1dYVZjzCtDBaJ6QdM81WP2k51QodDGZHzKEhzKHSp7v8"
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

# Lê os dados
df = pd.read_csv(url, parse_dates=["Data Envio", "Data Entrega"])

# Ajustar nomes das colunas para facilitar
# (depende exatamente como suas colunas estão nomeadas)
df = df.rename(columns={
    "Data Envio": "data_envio",
    "Data Entrega": "data_entrega",
    "Pedido": "pedido"
})
# Se tiver coluna de estado/região, renomeie: ex:
# df = df.rename(columns={"Estado": "estado"})

# Calcula dias de entrega
df["dias_entrega"] = (df["data_entrega"] - df["data_envio"]).dt.days

# Se houver coluna de estado/região
if "estado" in df.columns:
    regioes = sorted(df["estado"].dropna().unique())
else:
    # Se não tiver, criar dummy “Todos”
    df["estado"] = "Todos"
    regioes = ["Todos"]

regiao_sel = st.selectbox("Selecionar Estado / Região", ["Todos"] + regioes)

if regiao_sel != "Todos":
    df_filtrado = df[df["estado"] == regiao_sel]
else:
    df_filtrado = df

# Filtra valores válidos
df_valid = df_filtrado.dropna(subset=["dias_entrega"])
total = len(df_valid)

# Cálculos principais
media = df_valid["dias_entrega"].mean() if total > 0 else None
mediana = df_valid["dias_entrega"].median() if total > 0 else None
pct_ate3 = (df_valid["dias_entrega"] <= 3).sum() / total * 100 if total > 0 else None
pct_atraso5 = (df_valid["dias_entrega"] > 5).sum() / total * 100 if total > 0 else None

# Exibição
st.metric("Tempo médio (dias)", f"{media:.1f}" if media is not None else "—")
st.metric("Mediana (dias)", f"{mediana:.0f}" if mediana is not None else "—")
st.metric("% em até 3 dias", f"{pct_ate3:.1f}%" if pct_ate3 is not None else "—")
st.metric("% atrasos (+5 dias)", f"{pct_atraso5:.1f}%" if pct_atraso5 is not None else "—")

st.subheader("Resumo por Estado")
resumo = df.groupby("estado")["dias_entrega"].agg(["count", "mean", "median"])
st.dataframe(resumo)

st.subheader("Distribuição de dias de entrega")
# histograma de frequência
freq = df_valid["dias_entrega"].value_counts().sort_index()
st.bar_chart(freq)

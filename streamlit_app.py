import streamlit as st
import pandas as pd
import plotly.express as px

# --- Configuração da página ---
st.set_page_config(page_title="Dashboard Didático de Entregas", layout="wide")
st.title("📦 Dashboard Interativo de Entregas – Brasil")

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

# --- Resumo por cidade ---
st.subheader(f"📋 Resumo por Cidade {'do Brasil' if regiao_sel=='Todos' else 'do Estado '+regiao_sel}")
resumo_cidade = df_valid.groupby(["estado","cidade"])["dias_entrega"].agg([
    ("Total Pedidos","count"),
    ("Média Dias","mean"),
    ("Mediana Dias","median"),
    ("% Entregas ≤3 dias", lambda x: (x<=3).sum()/len(x)*100),
    ("% Atrasos >5 dias", lambda x: (x>5).sum()/len(x)*100)
]).reset_index()

if regiao_sel=="Todos":
    st.dataframe(resumo_cidade)
else:
    st.dataframe(resumo_cidade[resumo_cidade["estado"]==regiao_sel])

# --- Gráfico interativo por cidade ---
st.subheader("📈 Gráfico de Entregas por Cidade")
if regiao_sel=="Todos":
    fig = px.bar(resumo_cidade, x="cidade", y="% Entregas ≤3 dias", color="estado",
                 hover_data=["Total Pedidos","Média Dias","Mediana Dias","% Atrasos >5 dias"],
                 title="Entregas ≤3 dias por Cidade (Brasil)")
else:
    df_graf = resumo_cidade[resumo_cidade["estado"]==regiao_sel]
    fig = px.bar(df_graf, x="cidade", y="% Entregas ≤3 dias", color="cidade",
                 hover_data=["Total Pedidos","Média Dias","Mediana Dias","% Atrasos >5 dias"],
                 title=f"Entregas ≤3 dias por Cidade - {regiao_sel}")

st.plotly_chart(fig, use_container_width=True)

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
- **Gráfico por cidade**: barras mostram rapidez por cidade, hover com detalhes
- **Dropdown de Estado**: filtra cidades de cada estado
""")

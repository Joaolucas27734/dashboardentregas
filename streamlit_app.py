import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Configuração da página ---
st.set_page_config(page_title="Dashboard Avançado de Entregas", layout="wide")
st.title("📦 Dashboard Avançado de Entregas – Brasil")

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

# --- Sidebar para filtro de período ---
st.sidebar.header("Filtros")
data_inicio = st.sidebar.date_input("Data inicial", df["data_envio"].min())
data_fim = st.sidebar.date_input("Data final", df["data_envio"].max())
df = df[(df["data_envio"]>=pd.to_datetime(data_inicio)) & (df["data_envio"]<=pd.to_datetime(data_fim))]

# --- Métricas principais ---
df_valid = df.dropna(subset=["dias_entrega"])
total = len(df_valid)
media = df_valid["dias_entrega"].mean() if total>0 else 0
mediana = df_valid["dias_entrega"].median() if total>0 else 0
pct_ate3 = (df_valid["dias_entrega"]<=3).sum()/total*100 if total>0 else 0
pct_atraso5 = (df_valid["dias_entrega"]>5).sum()/total*100 if total>0 else 0
std_entrega = df_valid["dias_entrega"].std() if total>0 else 0

# --- Cards principais ---
st.subheader("📊 Principais Métricas")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Tempo médio (dias)", f"{media:.1f}")
col2.metric("Mediana (dias)", f"{mediana:.0f}")
col3.metric("% Entregas ≤3 dias", f"{pct_ate3:.1f}%")
col4.metric("% Atrasos (>5 dias)", f"{pct_atraso5:.1f}%")
col5.metric("Desvio padrão", f"{std_entrega:.1f}")

# --- Resumo por estado ---
resumo_estado = df_valid.groupby("estado")["dias_entrega"].agg([
    ("Total Pedidos","count"),
    ("Média Dias","mean"),
    ("% Entregas ≤3 dias", lambda x: (x<=3).sum()/len(x)*100),
    ("% Atrasos >5 dias", lambda x: (x>5).sum()/len(x)*100)
]).reset_index()

# --- Mapa do Brasil ---
st.subheader("🌎 Mapa do Brasil – % Entregas ≤3 dias")
fig_map = px.choropleth_mapbox(
    resumo_estado,
    geojson="https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson",
    locations="estado",
    featureidkey="properties.sigla",
    color="% Entregas ≤3 dias",
    hover_data=["Total Pedidos","Média Dias","% Atrasos >5 dias"],
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
    # Gráfico por estado
    fig_estado = px.bar(
        resumo_estado,
        x="estado",
        y="% Entregas ≤3 dias",
        hover_data=["Total Pedidos","Média Dias","% Atrasos >5 dias"],
        color="% Entregas ≤3 dias",
        color_continuous_scale="Greens",
        title="Entregas ≤3 dias por Estado"
    )
    st.plotly_chart(fig_estado, use_container_width=True)
else:
    # Boxplot por cidade mostrando distribuição dos dias de entrega
    df_cidades = df_valid[df_valid["estado"]==estado_sel]
    fig_cidade = px.box(
        df_cidades,
        x="cidade",
        y="dias_entrega",
        color="cidade",
        points="all",
        title=f"Distribuição dos Dias de Entrega por Cidade - {estado_sel}",
        labels={"dias_entrega":"Dias de Entrega"}
    )
    st.plotly_chart(fig_cidade, use_container_width=True)

# --- Tabela detalhada ---
st.subheader("📝 Resumo dos Pedidos")
tabela_resumo = df_valid[["data_envio","data_entrega","dias_entrega","estado","cidade"]].sort_values("data_envio")
st.dataframe(tabela_resumo)

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
- **Tabela**: resumo detalhado dos pedidos
- **Histograma**: visualiza a distribuição dos dias de entrega
""")

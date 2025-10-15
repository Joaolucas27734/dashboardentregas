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

# --- Colunas de estado e cidade ---
df["estado"] = df.iloc[:,3].str.upper()  # coluna D
df["cidade"] = df.iloc[:,4].astype(str).str.title()  # coluna E

# --- Tabs: Dashboard / Resumo de Pedido ---
tab1, tab2 = st.tabs(["📊 Dashboard", "📝 Resumo do Pedido"])

with tab1:
    # --- Métricas principais ---
    df_valid = df.dropna(subset=["dias_entrega"])
    total = len(df_valid)
    media = df_valid["dias_entrega"].mean() if total>0 else 0
    mediana = df_valid["dias_entrega"].median() if total>0 else 0
    pct_ate3 = (df_valid["dias_entrega"]<=3).sum()/total*100 if total>0 else 0
    pct_atraso5 = (df_valid["dias_entrega"]>5).sum()/total*100 if total>0 else 0

    st.subheader("📊 Principais Métricas")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tempo médio (dias)", f"{media:.1f}")
    col2.metric("Mediana (dias)", f"{mediana:.0f}")
    col3.metric("% Entregas ≤3 dias", f"{pct_ate3:.1f}%")
    col4.metric("% Atrasos (>5 dias)", f"{pct_atraso5:.1f}%")

    # --- Resumo por estado ---
    resumo_estado = df_valid.groupby("estado")["dias_entrega"].agg([
        ("Total Pedidos","count"),
        ("Média Dias","mean"),
        ("Mediana Dias","median"),
        ("Dias Mínimos","min"),
        ("Dias Máximos","max"),
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
        hover_data=["Total Pedidos","Média Dias","Mediana Dias"],
        color_continuous_scale="Greens",
        mapbox_style="carto-positron",
        zoom=3.5,
        center={"lat":-14.2350,"lon":-51.9253},
        opacity=0.6
    )
    st.plotly_chart(fig_map, use_container_width=True)

    # --- Dropdown para selecionar estado ---
    st.subheader("📈 Gráfico de Entregas por Estado / Cidade")
    estados = sorted(df_valid["estado"].unique())
    estado_sel = st.selectbox("Selecione um estado para ver as cidades", ["Todos"] + estados)

    if estado_sel == "Todos":
        # Gráfico por estado
        fig_estado = px.bar(
            resumo_estado,
            x="estado",
            y="% Entregas ≤3 dias",
            hover_data=["Total Pedidos","Média Dias","Mediana Dias"],
            color="% Entregas ≤3 dias",
            color_continuous_scale="Greens",
            title="Entregas ≤3 dias por Estado"
        )
        st.plotly_chart(fig_estado, use_container_width=True)
        
        # Tabela resumo por estado
        st.subheader("📋 Tabela de Resumo por Estado")
        st.dataframe(resumo_estado)

    else:
        # Filtrar cidades do estado selecionado
        df_cidades = df_valid[df_valid["estado"]==estado_sel]
        resumo_cidade = df_cidades.groupby("cidade")["dias_entrega"].agg([
            ("Total Pedidos","count"),
            ("Média Dias","mean"),
            ("Mediana Dias","median"),
            ("Dias Mínimos","min"),
            ("Dias Máximos","max"),
            ("% Entregas ≤3 dias", lambda x: (x<=3).sum()/len(x)*100)
        ]).reset_index()

        fig_cidade = px.bar(
            resumo_cidade,
            x="cidade",
            y="Média Dias",
            hover_data=["Total Pedidos","Mediana Dias","Dias Mínimos","Dias Máximos","% Entregas ≤3 dias"],
            color="Média Dias",
            color_continuous_scale="Blues",
            title=f"Tempo médio de entrega por Cidade - {estado_sel}"
        )
        st.plotly_chart(fig_cidade, use_container_width=True)
        
        # Tabela resumo por cidade
        st.subheader(f"📋 Tabela de Resumo por Cidade - {estado_sel}")
        st.dataframe(resumo_cidade)

    # --- Histograma de dias de entrega ---
    st.subheader("📊 Distribuição de Dias de Entrega")
    freq = df_valid["dias_entrega"].value_counts().sort_index()
    st.bar_chart(freq)

with tab2:
    st.subheader("📝 Resumo do Pedido")
    st.markdown("Aqui você pode exibir informações detalhadas de cada pedido individual:")
    st.dataframe(df)

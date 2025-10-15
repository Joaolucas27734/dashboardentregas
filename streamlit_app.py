import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# --- Session state para drill-down ---
if "estado_selecionado" not in st.session_state:
    st.session_state.estado_selecionado = None

# --- Dados exemplo ---
sheet_id = "1dYVZjzCtDBaJ6QdM81WP2k51QodDGZHzKEhzKHSp7v8"
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
df = pd.read_csv(url)
df["dias_entrega"] = (pd.to_datetime(df.iloc[:,2]) - pd.to_datetime(df.iloc[:,1])).dt.days
df["estado"] = df.iloc[:,3].str.upper()
df["cidade"] = df.iloc[:,4].str.title() if df.shape[1]>4 else "Cidade Exemplo"

# --- Brasil ou Estado ---
if st.session_state.estado_selecionado is None:
    st.subheader("🌎 Mapa do Brasil")
    resumo = df.groupby("estado")["dias_entrega"].agg([
        ("Total","count"),
        ("% ≤3 dias", lambda x: (x<=3).sum()/len(x)*100)
    ]).reset_index()

    geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    geojson = requests.get(geojson_url).json()

    fig = px.choropleth_mapbox(
        resumo,
        geojson=geojson,
        locations="estado",
        featureidkey="properties.sigla",
        color="% ≤3 dias",
        hover_data=["Total","% ≤3 dias"],
        mapbox_style="carto-positron",
        zoom=3.5,
        center={"lat":-14.2350,"lon":-51.9253},
        opacity=0.6
    )
    # TODO: adicionar clique nos estados para mudar session_state
    st.plotly_chart(fig, use_container_width=True)
else:
    st.subheader(f"🗺️ Mapa do Estado: {st.session_state.estado_selecionado}")
    df_estado = df[df["estado"]==st.session_state.estado_selecionado]
    resumo_cidades = df_estado.groupby("cidade")["dias_entrega"].agg([
        ("Total","count"),
        ("% ≤3 dias", lambda x: (x<=3).sum()/len(x)*100)
    ]).reset_index()
    
    # GeoJSON cidades do estado
    geojson_url = f"https://raw.githubusercontent.com/kelvins/BR-municipios/master/csv/geojson/{st.session_state.estado_selecionado}.json"
    geojson = requests.get(geojson_url).json()
    
    fig = px.choropleth_mapbox(
        resumo_cidades,
        geojson=geojson,
        locations="cidade",
        featureidkey="properties.name",
        color="% ≤3 dias",
        hover_data=["Total","% ≤3 dias"],
        mapbox_style="carto-positron",
        zoom=6,
        opacity=0.6
    )
    st.plotly_chart(fig, use_container_width=True)

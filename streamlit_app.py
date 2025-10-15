import streamlit as st
import pandas as pd
import json
import plotly.express as px
import requests

st.title("📦 Dashboard Interativo de Entregas por Estado")

# --- Ler planilha ---
sheet_id = "1dYVZjzCtDBaJ6QdM81WP2k51QodDGZHzKEhzKHSp7v8"
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
df = pd.read_csv(url)

# --- Processar datas ---
df["data_envio"] = pd.to_datetime(df.iloc[:,1], errors="coerce")
df["data_entrega"] = pd.to_datetime(df.iloc[:,2], errors="coerce")
df["dias_entrega"] = (df["data_entrega"] - df["data_envio"]).dt.days
df["estado"] = df.iloc[:,3].str.upper()

# --- Resumo por estado ---
resumo = df.groupby("estado")["dias_entrega"].agg([
    ("Total Pedidos","count"),
    ("Média Dias","mean"),
    ("Mediana Dias","median"),
    ("% Até 3 Dias", lambda x: (x<=3).sum()/len(x)*100)
]).reset_index()

# --- GeoJSON dos estados do Brasil ---
geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
geojson = requests.get(geojson_url).json()

# --- Map choropleth ---
fig = px.choropleth_mapbox(
    resumo,
    geojson=geojson,
    locations="estado",
    featureidkey="properties.sigla",  # no GeoJSON, sigla do estado
    color="% Até 3 Dias",
    color_continuous_scale="Greens",
    mapbox_style="carto-positron",
    zoom=3.5,
    center = {"lat":-14.2350, "lon": -51.9253},
    opacity=0.6,
    hover_data=["Total Pedidos","Média Dias","Mediana Dias"]
)

st.plotly_chart(fig, use_container_width=True)

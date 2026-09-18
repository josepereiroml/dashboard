import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import os

st.set_page_config(page_title="Conciertos AR - Traffic", layout="wide")
engine = create_engine(f"sqlite:///{os.path.join('data','conciertos.db')}")

@st.cache_data(ttl=300)
def q(sql):
    return pd.read_sql(sql, engine)

st.title("🎤 Radar de Conciertos Argentina")
st.caption("Detección de oportunidades de cobertura y traffic")

# --- KPIs ---
col1, col2, col3, col4 = st.columns(4)
total = q("SELECT COUNT(*) c FROM eventos").iloc[0]["c"]
sold = q("SELECT COUNT(*) c FROM eventos WHERE disponible=0").iloc[0]["c"]
ciudades = q("SELECT COUNT(DISTINCT ciudad) c FROM eventos WHERE ciudad != ''").iloc[0]["c"]
trends_alto = q("SELECT COUNT(DISTINCT keyword) c FROM trends WHERE interes > 50").iloc[0]["c"]

col1.metric("Eventos monitoreados", total)
col2.metric("Agotados", sold)
col3.metric("Ciudades", ciudades)
col4.metric("Artistas trending", trends_alto)

st.divider()

# --- Oportunidades ---
st.subheader("🔥 Oportunidades de Traffic")
st.caption("Alto interés en Google Trends + poca oferta de eventos = tema para cubrir")

opp = q("""
    SELECT t.keyword AS artista,
           AVG(t.interes) AS interes,
           COUNT(DISTINCT e.id) AS eventos
    FROM trends t
    LEFT JOIN eventos e ON LOWER(e.artista) LIKE '%' || LOWER(t.keyword) || '%'
    WHERE t.fecha >= date('now', '-7 day')
    GROUP BY t.keyword
    HAVING interes > 20
""")
if not opp.empty:
    opp["score"] = opp["interes"] / (opp["eventos"] + 1)
    opp = opp.sort_values("score", ascending=False)
    fig = px.bar(opp, x="artista", y="score",
                 color="interes", hover_data=["eventos"],
                 title="Score de oportunidad = interés / (eventos + 1)")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Agotados ---
st.subheader("🚨 Shows agotados")
agotados = q("SELECT artista, evento, venue, ciudad, url FROM eventos WHERE disponible=0 LIMIT 30")
st.dataframe(agotados, use_container_width=True)

# --- Precios ---
st.subheader("💰 Comparativa de precios por artista")
precios = q("""
    SELECT artista, AVG(precio_min) precio_prom, COUNT(*) n
    FROM eventos WHERE precio_min IS NOT NULL
    GROUP BY artista ORDER BY precio_prom DESC LIMIT 20
""")
if not precios.empty:
    fig = px.bar(precios, x="artista", y="precio_prom", hover_data=["n"])
    st.plotly_chart(fig, use_container_width=True)

# --- Trends ---
st.subheader("📈 Evolución de interés (Google Trends AR)")
trends = q("""
    SELECT keyword, fecha, interes FROM trends
    WHERE fecha >= date('now', '-14 day')
    ORDER BY fecha
""")
if not trends.empty:
    fig = px.line(trends, x="fecha", y="interes", color="keyword")
    st.plotly_chart(fig, use_container_width=True)

# --- Spotify Top AR ---
st.subheader("🎧 Top 50 Spotify Argentina")
sp = q("""
    SELECT artista, posicion FROM spotify_charts
    WHERE pais='AR' ORDER BY scraped_at DESC, posicion ASC LIMIT 20
""")
st.dataframe(sp, use_container_width=True)

# --- Fuentes ---
st.subheader("🔗 Todos los eventos")
all_ev = q("SELECT fuente, artista, venue, ciudad, precio_min, disponible, url FROM eventos ORDER BY scraped_at DESC LIMIT 200")
st.dataframe(all_ev, use_container_width=True)
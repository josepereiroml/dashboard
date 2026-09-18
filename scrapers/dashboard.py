$content = @'
"""
Dashboard - Radar de Conciertos Argentina.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from pathlib import Path

st.set_page_config(page_title="Conciertos AR - Traffic", layout="wide")

DB_PATH = Path(__file__).resolve().parent / "data" / "conciertos.db"
engine = create_engine(f"sqlite:///{DB_PATH}")


@st.cache_data(ttl=300)
def q(sql):
    return pd.read_sql(sql, engine)


st.title("Radar de Conciertos Argentina")
st.caption("Deteccion de oportunidades de cobertura y traffic")

try:
    total = q("SELECT COUNT(*) c FROM eventos").iloc[0]["c"]
    sold = q("SELECT COUNT(*) c FROM eventos WHERE disponible=0").iloc[0]["c"]
    ciudades = q("SELECT COUNT(DISTINCT ciudad) c FROM eventos WHERE ciudad IS NOT NULL AND ciudad != ''").iloc[0]["c"]
    fuentes = q("SELECT COUNT(DISTINCT fuente) c FROM eventos").iloc[0]["c"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Eventos monitoreados", total)
    col2.metric("Agotados", sold)
    col3.metric("Ciudades", ciudades)
    col4.metric("Fuentes", fuentes)
except Exception as e:
    st.error(f"Error leyendo DB: {e}")
    st.stop()

st.divider()

st.subheader("Eventos por fuente")
try:
    por_fuente = q("SELECT fuente, COUNT(*) n FROM eventos GROUP BY fuente ORDER BY n DESC")
    fig = px.bar(por_fuente, x="fuente", y="n", color="fuente")
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.warning(f"Sin datos: {e}")

st.divider()

st.subheader("Shows agotados")
try:
    agotados = q("SELECT fuente, artista, venue, ciudad, url FROM eventos WHERE disponible=0 ORDER BY scraped_at DESC LIMIT 30")
    if agotados.empty:
        st.info("No hay eventos agotados detectados todavia.")
    else:
        st.dataframe(agotados, use_container_width=True)
except Exception as e:
    st.warning(f"Error: {e}")

st.divider()

st.subheader("Eventos con fecha detectada")
try:
    con_fecha = q("SELECT fuente, artista, venue, ciudad, fecha, precio_min FROM eventos WHERE fecha IS NOT NULL AND fecha != '' ORDER BY scraped_at DESC LIMIT 50")
    if con_fecha.empty:
        st.info("Aun no hay eventos con fecha parseada.")
    else:
        st.dataframe(con_fecha, use_container_width=True)
except Exception as e:
    st.warning(f"Error: {e}")

st.divider()

st.subheader("Comparativa de precios")
try:
    precios = q("SELECT artista, AVG(precio_min) precio_prom, COUNT(*) n FROM eventos WHERE precio_min IS NOT NULL AND precio_min > 0 GROUP BY artista ORDER BY precio_prom DESC LIMIT 20")
    if precios.empty:
        st.info("Todavia no hay precios parseados.")
    else:
        fig = px.bar(precios, x="artista", y="precio_prom", hover_data=["n"])
        st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.warning(f"Error: {e}")

st.divider()

st.subheader("Google Trends AR (ultimos 14 dias)")
try:
    trends = q("SELECT keyword, fecha, interes FROM trends WHERE fecha >= date('now', '-14 day') ORDER BY fecha")
    if trends.empty:
        st.info("Sin datos de trends todavia.")
    else:
        fig = px.line(trends, x="fecha", y="interes", color="keyword")
        st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.warning(f"Error: {e}")

st.divider()

st.subheader("Todos los eventos")
try:
    all_ev = q("SELECT fuente, artista, venue, ciudad, precio_min, disponible, url FROM eventos ORDER BY scraped_at DESC LIMIT 200")
    st.dataframe(all_ev, use_container_width=True)
except Exception as e:
    st.warning(f"Error: {e}")
'@

[System.IO.File]::WriteAllText("C:\Users\josep\Desktop\concert-traffic-ar\dashboard.py", $content, [System.Text.Encoding]::UTF8)

Write-Host "dashboard.py creado OK"
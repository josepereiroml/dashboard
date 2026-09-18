"""Dashboard de conciertos Argentina."""
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from pathlib import Path

st.set_page_config(page_title="Conciertos AR", layout="wide")

DB_PATH = Path(__file__).resolve().parent / "data" / "conciertos.db"
engine = create_engine(f"sqlite:///{DB_PATH}")

@st.cache_data(ttl=300)
def q(sql):
    return pd.read_sql(sql, engine)

st.title("Radar de Conciertos Argentina")
st.caption("Deteccion de oportunidades de cobertura y traffic")

# --- KPIs ---
try:
    total = q("SELECT COUNT(*) c FROM eventos").iloc[0]["c"]
    sold = q("SELECT COUNT(*) c FROM eventos WHERE disponible=0").iloc[0]["c"]
    fuentes = q("SELECT COUNT(DISTINCT fuente) c FROM eventos").iloc[0]["c"]
    ciudades = q("SELECT COUNT(DISTINCT ciudad) c FROM eventos WHERE ciudad IS NOT NULL AND ciudad != ''").iloc[0]["c"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Eventos", total)
    c2.metric("Agotados", sold)
    c3.metric("Fuentes", fuentes)
    c4.metric("Ciudades", ciudades)
except Exception as e:
    st.error(f"Error leyendo DB: {e}")
    st.stop()

st.divider()

# --- Por fuente ---
st.subheader("Eventos por fuente")
try:
    df = q("SELECT fuente, COUNT(*) n FROM eventos GROUP BY fuente ORDER BY n DESC")
    st.plotly_chart(px.bar(df, x="fuente", y="n", color="fuente"),
                    use_container_width=True)
except Exception as e:
    st.warning(f"Sin datos: {e}")

st.divider()

# --- Agotados ---
st.subheader("Shows agotados")
try:
    df = q("""SELECT fuente, artista, venue, ciudad, url
              FROM eventos WHERE disponible=0
              ORDER BY scraped_at DESC LIMIT 30""")
    if df.empty:
        st.info("No hay agotados detectados todavia.")
    else:
        st.dataframe(df, use_container_width=True)
except Exception as e:
    st.warning(f"Error: {e}")

st.divider()

# --- Eventos con fecha ---
st.subheader("Eventos con fecha detectada")
try:
    df = q("""SELECT fuente, artista, venue, ciudad, fecha, precio_min
              FROM eventos
              WHERE fecha IS NOT NULL AND fecha != ''
              ORDER BY scraped_at DESC LIMIT 50""")
    if df.empty:
        st.info("Aun no hay eventos con fecha parseada.")
    else:
        st.dataframe(df, use_container_width=True)
except Exception as e:
    st.warning(f"Error: {e}")

st.divider()

# --- Precios ---
st.subheader("Precios promedio por artista")
try:
    df = q("""SELECT artista, AVG(precio_min) precio_prom, COUNT(*) n
              FROM eventos
              WHERE precio_min IS NOT NULL AND precio_min > 0
              GROUP BY artista ORDER BY precio_prom DESC LIMIT 20""")
    if df.empty:
        st.info("Todavia no hay precios parseados.")
    else:
        st.plotly_chart(px.bar(df, x="artista", y="precio_prom",
                               hover_data=["n"]),
                        use_container_width=True)
except Exception as e:
    st.warning(f"Error: {e}")

st.divider()

# --- Trends ---
st.subheader("Google Trends AR (ultimos 14 dias)")
try:
    df = q("""SELECT keyword, fecha, interes FROM trends
              WHERE fecha >= date('now', '-14 day') ORDER BY fecha""")
    if df.empty:
        st.info("Sin datos de trends todavia.")
    else:
        st.plotly_chart(px.line(df, x="fecha", y="interes", color="keyword"),
                        use_container_width=True)
except Exception as e:
    st.warning(f"Error: {e}")

st.divider()

# --- Todos ---
st.subheader("Todos los eventos")
try:
    df = q("""SELECT fuente, artista, venue, ciudad, fecha, precio_min,
                     disponible, url
              FROM eventos ORDER BY scraped_at DESC LIMIT 200""")
    st.dataframe(df, use_container_width=True)
except Exception as e:
    st.warning(f"Error: {e}")
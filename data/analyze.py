"""
Detecta oportunidades de 'traffic' combinando señales:
- Eventos agotados rápido
- Artistas con alto interés en Trends pero poca cobertura
- Comparativas de precios
"""
import pandas as pd
from sqlalchemy import create_engine
import os

DB = os.path.join("data", "conciertos.db")
engine = create_engine(f"sqlite:///{DB}")

def eventos_agotados():
    q = """
    SELECT artista, evento, venue, ciudad, precio_min, url, scraped_at
    FROM eventos
    WHERE disponible = 0
    ORDER BY scraped_at DESC
    LIMIT 50
    """
    return pd.read_sql(q, engine)

def precios_por_artista():
    q = """
    SELECT artista, AVG(precio_min) AS precio_prom,
           MIN(precio_min) AS precio_min,
           MAX(precio_min) AS precio_max,
           COUNT(*) AS n_eventos
    FROM eventos
    WHERE precio_min IS NOT NULL
    GROUP BY artista
    HAVING n_eventos >= 1
    ORDER BY precio_prom DESC
    LIMIT 30
    """
    return pd.read_sql(q, engine)

def trending_sin_cobertura():
    """
    Cruza Trends con cantidad de eventos: mucho interés + pocos eventos
    = oportunidad de cobertura.
    """
    q = """
    SELECT t.keyword AS artista,
           AVG(t.interes) AS interes_prom,
           COUNT(DISTINCT e.id) AS n_eventos
    FROM trends t
    LEFT JOIN eventos e ON LOWER(e.artista) LIKE '%' || LOWER(t.keyword) || '%'
    WHERE t.fecha >= date('now', '-7 day')
    GROUP BY t.keyword
    HAVING interes_prom > 30
    ORDER BY interes_prom DESC
    """
    return pd.read_sql(q, engine)

def oportunidades_traffic():
    """Ranking combinado de 'qué está explotando'."""
    trends = trending_sin_cobertura()
    if trends.empty:
        return trends
    # Score: interés alto + pocos eventos = mayor oportunidad
    trends["score"] = trends["interes_prom"] / (trends["n_eventos"] + 1)
    return trends.sort_values("score", ascending=False)

if __name__ == "__main__":
    print("\n=== AGOTADOS ===")
    print(eventos_agotados().to_string())
    print("\n=== PRECIOS ===")
    print(precios_por_artista().to_string())
    print("\n=== OPORTUNIDADES DE TRAFFIC ===")
    print(oportunidades_traffic().to_string())
import sqlite3
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "conciertos.db")

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS eventos (
            id TEXT PRIMARY KEY,
            fuente TEXT,
            artista TEXT,
            evento TEXT,
            venue TEXT,
            ciudad TEXT,
            fecha TEXT,
            precio_min REAL,
            precio_max REAL,
            disponible INTEGER,
            url TEXT,
            scraped_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT,
            fecha TEXT,
            interes INTEGER,
            scraped_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS spotify_charts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            artista TEXT,
            posicion INTEGER,
            pais TEXT,
            fecha TEXT,
            scraped_at TEXT
        )
    """)
    conn.commit()
    return conn

def upsert_evento(conn, ev):
    conn.execute("""
        INSERT OR REPLACE INTO eventos
        (id, fuente, artista, evento, venue, ciudad, fecha,
         precio_min, precio_max, disponible, url, scraped_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        ev["id"], ev["fuente"], ev["artista"], ev["evento"],
        ev["venue"], ev["ciudad"], ev["fecha"],
        ev.get("precio_min"), ev.get("precio_max"),
        1 if ev.get("disponible", True) else 0,
        ev.get("url"), datetime.now().isoformat()
    ))
    conn.commit()
"""
Spotify Charts - scraping del sitio público.
Sin API, sin tokens, sin 403.
"""
import sys
import requests
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import get_conn

TIMEOUT = 20

URLS = [
    # Chart diario regional Argentina
    ("regional-ar-daily", "https://charts.spotify.com/charts/view/regional-ar-daily/latest"),
    # Viral 50 Argentina
    ("regional-ar-viral", "https://charts.spotify.com/charts/view/regional-ar-viral/latest"),
]


def scrape_chart(nombre, url):
    print(f"  → {nombre}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=TIMEOUT)
    except Exception as e:
        print(f"     Error: {e}")
        return []

    if r.status_code != 200:
        print(f"     HTTP {r.status_code}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    # Los datos están en un __NEXT_DATA__ JSON embebido
    import json
    script = soup.find("script", id="__NEXT_DATA__")
    if not script:
        print("     No se encontró __NEXT_DATA__")
        return []

    try:
        data = json.loads(script.string)
        # Navegar la estructura (puede cambiar)
        entries = (
            data.get("props", {})
            .get("pageProps", {})
            .get("chartData", {})
            .get("entries", [])
        )
        return entries
    except Exception as e:
        print(f"     Parse error: {e}")
        return []


def scrape():
    conn = get_conn()
    fecha = datetime.now().date().isoformat()
    ahora = datetime.now().isoformat()
    total = 0

    for nombre, url in URLS:
        entries = scrape_chart(nombre, url)
        print(f"     {len(entries)} entradas")
        for pos, entry in enumerate(entries[:50], start=1):
            # Estructura típica: {"trackName": ..., "artistNames": ..., ...}
            artistas = entry.get("artistNames") or entry.get("artists", "")
            if isinstance(artistas, list):
                artistas = ", ".join(a.get("name", "") for a in artistas)
            track = entry.get("trackName", "")
            if not artistas:
                continue
            conn.execute("""
                INSERT INTO spotify_charts (artista, posicion, pais, fecha, scraped_at)
                VALUES (?,?,?,?,?)
            """, (f"{artistas} — {track}" if track else artistas,
                  pos, "AR", fecha, ahora))
            total += 1
        conn.commit()

    conn.close()
    print(f"\n🎉 OK — {total} registros guardados")


if __name__ == "__main__":
    scrape()
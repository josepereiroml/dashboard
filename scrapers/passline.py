"""
Passline (ex EntradaUno) - scraping ligero con requests.
"""
import requests, hashlib, re
from bs4 import BeautifulSoup
from db import get_conn, upsert_evento

BASE = "https://www.passline.com"

def scrape():
    conn = get_conn()
    r = requests.get(f"{BASE}/eventos", headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    for card in soup.select("a.event, div.event-card a, a[href*='/evento/']"):
        try:
            url = card.get("href", "")
            if not url.startswith("http"):
                url = BASE + url

            text = card.get_text(" ", strip=True)
            if not text:
                continue

            artista = text.split(" ")[0:3]
            artista = " ".join(artista)
            disponible = "agotado" not in text.lower()
            precios = re.findall(r"\$\s?([\d\.]+)", text)
            precio_min = float(precios[0].replace(".", "")) if precios else None

            ev_id = hashlib.md5(url.encode()).hexdigest()[:16]
            upsert_evento(conn, {
                "id": ev_id, "fuente": "passline",
                "artista": artista, "evento": artista,
                "venue": "", "ciudad": "",
                "fecha": "", "precio_min": precio_min,
                "precio_max": None, "disponible": disponible,
                "url": url
            })
        except Exception as e:
            print(f"[passline] {e}")
    conn.close()
    print("[passline] OK")

if __name__ == "__main__":
    scrape()
"""
DF Entertainment - Lollapalooza AR, Cosquín Rock, shows internacionales.
Saca el nombre del artista del slug de la URL cuando el texto es genérico.
"""
import sys, hashlib, re
import requests
from bs4 import BeautifulSoup
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import get_conn, upsert_evento

BASE = "https://www.dfentertainment.com"
URLS = [f"{BASE}/", f"{BASE}/eventos", f"{BASE}/shows"]

GENERICOS = {
    "más info", "mas info", "ver más", "ver mas", "info",
    "comprar", "entradas", "tickets", "ver", "ir",
    "click aquí", "click aqui", "leer más", "leer mas",
    "conocer más", "conocer mas", "ver show", "ir al show",
    "todos los shows", "ver todos", "próximos shows", "proximos shows",
}

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def nombre_desde_url(url):
    """Extrae 'Foo Fighters' de https://www.dfentertainment.com/shows/foo-fighters"""
    if not url:
        return None
    url = url.split("?")[0].split("#")[0].rstrip("/")
    slug = url.split("/")[-1]
    if UUID_RE.match(slug) or len(slug) < 3:
        return None
    nombre = " ".join(p.capitalize() for p in slug.split("-") if p)
    return nombre if len(nombre) >= 3 else None


def scrape():
    conn = get_conn()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/120.0 Safari/537.36"}
    vistos = set()
    count = 0

    for url in URLS:
        try:
            r = requests.get(url, headers=headers, timeout=20)
        except Exception:
            continue
        if r.status_code != 200:
            continue

        print(f"[df] {url} → {r.status_code}")
        soup = BeautifulSoup(r.text, "html.parser")

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href in vistos:
                continue
            if not any(k in href.lower() for k in ["evento", "show", "festival"]):
                continue
            vistos.add(href)

            if not href.startswith("http"):
                href = BASE + href if href.startswith("/") else f"{BASE}/{href}"

            # Texto del link
            texto = link.get_text(" ", strip=True)

            # Determinar si el texto sirve
            texto_util = (
                texto
                and len(texto) >= 3
                and texto.lower().strip() not in GENERICOS
            )

            # Si no sirve, sacar del slug de la URL
            artista = texto if texto_util else nombre_desde_url(href)

            if not artista or len(artista) < 3:
                continue

            # Detectar sold out
            disponible = "agotado" not in (texto or "").lower()

            ev_id = hashlib.md5(href.encode()).hexdigest()[:16]
            upsert_evento(conn, {
                "id": ev_id, "fuente": "df_entertainment",
                "artista": artista[:120],
                "evento": artista[:200],
                "venue": "", "ciudad": "",
                "fecha": "", "precio_min": None, "precio_max": None,
                "disponible": disponible,
                "url": href,
            })
            count += 1

    conn.close()
    print(f"[df] OK — {count} eventos")


if __name__ == "__main__":
    scrape()
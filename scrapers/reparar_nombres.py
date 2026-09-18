"""
Repara eventos guardados con UUID o nombres genéricos.
- Si el artista es un UUID, saca el nombre del slug de la URL.
- Si el nombre es genérico ("Más info"), usa el slug.
"""
import sys, re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import get_conn

GENERICOS = {
    "más info", "mas info", "ver más", "ver mas", "info",
    "comprar", "entradas", "tickets", "ver", "ir",
    "click aquí", "click aqui", "leer más", "leer mas",
    "conocer más", "conocer mas", "ver show", "ir al show",
    "todos los shows", "ver todos",
}

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def nombre_desde_url(url):
    if not url:
        return None
    url = url.split("?")[0].split("#")[0].rstrip("/")
    slug = url.split("/")[-1]
    if UUID_RE.match(slug) or len(slug) < 3:
        return None
    nombre = " ".join(p.capitalize() for p in slug.split("-") if p)
    return nombre if len(nombre) >= 3 else None


def reparar():
    conn = get_conn()
    rows = conn.execute("SELECT id, artista, url FROM eventos").fetchall()

    arreglados = 0
    sin_solucion = 0

    for ev_id, artista, url in rows:
        necesita = False

        if not artista or len(artista.strip()) < 3:
            necesita = True
        elif UUID_RE.match(artista.strip()):
            necesita = True
        elif artista.strip().lower() in GENERICOS:
            necesita = True

        if not necesita:
            continue

        nuevo = nombre_desde_url(url)
        if nuevo:
            conn.execute(
                "UPDATE eventos SET artista = ?, evento = ? WHERE id = ?",
                (nuevo, nuevo, ev_id)
            )
            arreglados += 1
            print(f"  ✅ {(artista or '(vacío)')[:50]}  →  {nuevo}")
        else:
            sin_solucion += 1
            print(f"  ⚠️  Sin solución: {url[:80]}")

    conn.commit()
    conn.close()
    print(f"\n✅ {arreglados} arreglados | ⚠️  {sin_solucion} sin solución")


if __name__ == "__main__":
    reparar()
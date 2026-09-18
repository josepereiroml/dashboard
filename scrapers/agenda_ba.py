"""
Agenda BA - API oficial del GCBA.
Todos los eventos culturales de CABA, gratis, sin auth.
Doc: https://api.buenosaires.gob.ar/
"""
import sys, hashlib
import requests
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import get_conn, upsert_evento

# Endpoint público de la agenda cultural
URL = "https://apis.buenosaires.gob.ar/v1/eventos"


def scrape():
    conn = get_conn()
    headers = {"User-Agent": "Mozilla/5.0"}

    params = {
        "limit": 100,
        "offset": 0,
        # Podés filtrar por categoría, fecha, etc.
    }

    try:
        r = requests.get(URL, headers=headers, params=params, timeout=25)
        print(f"[agenda_ba] HTTP {r.status_code}")
        if r.status_code != 200:
            print(f"[agenda_ba] {r.text[:300]}")
            return
        data = r.json()
    except Exception as e:
        print(f"[agenda_ba] Error: {e}")
        return

    # Estructura esperada: {"results": [...]} o lista directa
    eventos = data.get("results", data if isinstance(data, list) else [])
    print(f"[agenda_ba] {len(eventos)} eventos")

    count = 0
    for ev in eventos:
        try:
            titulo = ev.get("name") or ev.get("title", "")
            if not titulo:
                continue
            venue = ev.get("venue", {}) or {}
            lugar = venue.get("name") if isinstance(venue, dict) else ev.get("lugar", "")

            ev_id = hashlib.md5(str(ev.get("id", titulo)).encode()).hexdigest()[:16]
            upsert_evento(conn, {
                "id": ev_id, "fuente": "agenda_ba",
                "artista": titulo[:120], "evento": titulo[:200],
                "venue": lugar or "", "ciudad": "CABA",
                "fecha": (ev.get("start_date") or ev.get("fecha", ""))[:10],
                "precio_min": None, "precio_max": None,
                "disponible": True,
                "url": ev.get("url") or ev.get("link", "")
            })
            count += 1
        except Exception as e:
            print(f"[agenda_ba] error: {e}")

    conn.commit()
    conn.close()
    print(f"[agenda_ba] OK — {count} eventos")


if __name__ == "__main__":
    scrape()
"""
Google Trends (pytrends) - interés de búsqueda de artistas en Argentina.
"""
import time
import random
from pytrends.request import TrendReq
from datetime import datetime
from db import get_conn

ARTISTAS_BASE = [
    "Duki", "Bad Bunny", "Taylor Swift", "María Becerra",
    "Coldplay", "Tini", "Lali", "Tan Biónica"
]

def scrape():
    conn = get_conn()
    pytrends = TrendReq(hl="es-AR", tz=-180)
    ok, fail = 0, 0

    for artista in ARTISTAS_BASE:
        try:
            pytrends.build_payload([artista], geo="AR", timeframe="now 7-d")
            df = pytrends.interest_over_time()
            if df.empty:
                print(f"[trends] {artista}: sin datos")
                continue
            for fecha, row in df.iterrows():
                conn.execute("""
                    INSERT INTO trends (keyword, fecha, interes, scraped_at)
                    VALUES (?,?,?,?)
                """, (artista, fecha.isoformat(), int(row[artista]),
                      datetime.now().isoformat()))
            conn.commit()
            ok += 1
            print(f"[trends] {artista} OK")

            # Pausa aleatoria de 5-12 s entre cada artista → evita 429
            time.sleep(random.uniform(5, 12))

        except Exception as e:
            fail += 1
            print(f"[trends] {artista}: {e}")
            # Si Google nos bloqueó, esperamos más antes de seguir
            time.sleep(random.uniform(30, 60))

    conn.close()
    print(f"[trends] fin: {ok} OK / {fail} fallidos")

if __name__ == "__main__":
    scrape()
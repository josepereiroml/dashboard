"""
Scrapea listado de eventos de Ticketek Argentina.
Usa Playwright porque el sitio carga contenido dinámico.
"""
import asyncio, hashlib, re
from playwright.async_api import async_playwright
from db import get_conn, upsert_evento

BASE = "https://www.ticketek.com.ar"

async def scrape():
    conn = get_conn()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(BASE, wait_until="networkidle")

        # Esperar tarjetas de evento
        await page.wait_for_timeout(3000)

        cards = await page.query_selector_all("a[href*='/evento/'], a[href*='/espectaculo/']")
        seen = set()
        for c in cards:
            try:
                url = await c.get_attribute("href")
                if not url or url in seen:
                    continue
                seen.add(url)
                if not url.startswith("http"):
                    url = BASE + url

                text = (await c.inner_text()).strip()
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                if not lines:
                    continue

                artista = lines[0]
                evento = lines[1] if len(lines) > 1 else artista
                venue = next((l for l in lines if any(k in l for k in
                              ["Arena", "Estadio", "Luna Park", "Teatro", "Movistar", "Vélez", "River", "Bombonera"])), "")
                ciudad = "CABA" if "Buenos Aires" in text or "CABA" in text else ""

                # Detectar sold out
                disponible = "agotado" not in text.lower() and "sold out" not in text.lower()

                # Precio (regex simple)
                precios = re.findall(r"\$\s?([\d\.]+)", text)
                precio_min = float(precios[0].replace(".", "")) if precios else None

                ev_id = hashlib.md5(url.encode()).hexdigest()[:16]
                upsert_evento(conn, {
                    "id": ev_id, "fuente": "ticketek",
                    "artista": artista, "evento": evento,
                    "venue": venue, "ciudad": ciudad,
                    "fecha": "", "precio_min": precio_min,
                    "precio_max": None, "disponible": disponible,
                    "url": url
                })
            except Exception as e:
                print(f"[ticketek] error en card: {e}")

        await browser.close()
    conn.close()
    print("[ticketek] OK")

if __name__ == "__main__":
    asyncio.run(scrape())
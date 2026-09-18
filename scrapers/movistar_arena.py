"""
Movistar Arena - scraper optimizado con Playwright.
Extrae nombre del artista usando og:title / page.title() como fallback.
"""
import sys, hashlib, re, asyncio
from pathlib import Path
from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import get_conn, upsert_evento

BASE = "https://www.movistararena.com.ar"
LISTADO_URLS = [f"{BASE}/", f"{BASE}/shows"]
MAX_CONCURRENT = 10
MAX_SHOWS = None

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


async def extraer_shows(page):
    links = await page.eval_on_selector_all(
        "a[href*='/show/']",
        "els => els.map(el => el.href)"
    )
    urls = set()
    for href in links:
        if "/show/" in href:
            urls.add(href.split("?")[0].rstrip("/"))
    return sorted(urls)


async def scrape_show(page, url):
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(800)

        titulo = ""

        # 1. og:title (el más confiable)
        try:
            og = await page.get_attribute('meta[property="og:title"]', "content")
            if og and len(og.strip()) >= 3:
                titulo = og.strip()
        except Exception:
            pass

        # 2. <title> de la pestaña
        if not titulo or len(titulo) < 3:
            try:
                t = await page.title()
                if t and len(t.strip()) >= 3:
                    titulo = t.strip()
            except Exception:
                pass

        # 3. <h1> como último recurso
        if not titulo or len(titulo) < 3:
            try:
                h1 = await page.inner_text("h1")
                if h1 and len(h1.strip()) >= 3:
                    titulo = h1.strip().split("\n")[0]
            except Exception:
                pass

        # Limpiar sufijos del venue
        if titulo:
            titulo = re.split(r"\s*[\|\-–]\s*Movistar Arena", titulo, flags=re.IGNORECASE)[0].strip()
            titulo = re.sub(r"\s*[\|\-–]\s*$", "", titulo).strip()
            titulo = titulo[:150]

        # Si sigue siendo UUID o vacío, no guardamos
        if not titulo or len(titulo) < 3 or UUID_RE.match(titulo):
            print(f"[movistar] ⚠️  sin título válido: {url}")
            return None

        body = await page.inner_text("body")

        # Fecha
        fecha = ""
        m = re.search(r"(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})", body)
        if m:
            fecha = m.group(1)
        else:
            m = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})", body)
            if m:
                fecha = m.group(1)

        # Precio
        precios = re.findall(r"\$\s?([\d\.]+)", body)
        precio_min = None
        if precios:
            try:
                precio_min = float(precios[0].replace(".", ""))
            except ValueError:
                pass

        # Disponibilidad
        disponible = not any(k in body.lower() for k in
                             ["agotado", "sold out", "sin stock"])

        return {
            "titulo": titulo,
            "fecha": fecha,
            "precio_min": precio_min,
            "disponible": disponible,
        }
    except Exception as e:
        print(f"[movistar] error: {url} → {e}")
        return None


async def worker(context, url, conn, sem):
    async with sem:
        page = await context.new_page()
        try:
            data = await scrape_show(page, url)
        finally:
            await page.close()

        if not data:
            return 0

        ev_id = hashlib.md5(url.encode()).hexdigest()[:16]
        upsert_evento(conn, {
            "id": ev_id, "fuente": "movistar_arena",
            "artista": data["titulo"], "evento": data["titulo"],
            "venue": "Movistar Arena", "ciudad": "CABA",
            "fecha": data["fecha"],
            "precio_min": data["precio_min"], "precio_max": None,
            "disponible": data["disponible"], "url": url,
        })
        print(f"[movistar] ✅ {data['titulo'][:70]}")
        return 1


async def scrape_async():
    conn = get_conn()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0 Safari/537.36"
        )

        todas = set()
        page = await context.new_page()
        for listado in LISTADO_URLS:
            print(f"[movistar] Listando {listado}")
            try:
                await page.goto(listado, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(2500)
                urls = await extraer_shows(page)
                print(f"[movistar]   {len(urls)} shows")
                todas.update(urls)
            except Exception as e:
                print(f"[movistar]   error: {e}")
        await page.close()

        urls_final = sorted(todas)
        if MAX_SHOWS:
            urls_final = urls_final[:MAX_SHOWS]
        print(f"[movistar] Total a procesar: {len(urls_final)}\n")

        sem = asyncio.Semaphore(MAX_CONCURRENT)
        tareas = [worker(context, u, conn, sem) for u in urls_final]
        resultados = await asyncio.gather(*tareas)
        count = sum(resultados)

        await browser.close()

    conn.close()
    print(f"\n[movistar] OK — {count} eventos guardados")


def scrape():
    asyncio.run(scrape_async())


if __name__ == "__main__":
    scrape()
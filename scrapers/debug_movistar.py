"""
Diagnóstico de Movistar Arena con Playwright.
Guarda screenshot + HTML renderizado + links encontrados.
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE = "https://movistararena.com.ar"
URLS = [
    f"{BASE}/eventos/",
    f"{BASE}/",
    f"{BASE}/shows/",
    f"{BASE}/cartelera/",
]


async def main():
    out_dir = Path(__file__).resolve().parent / "debug_movistar"
    out_dir.mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0 Safari/537.36"
        )

        for i, url in enumerate(URLS):
            print(f"\n=== {url} ===")
            try:
                resp = await page.goto(url, wait_until="networkidle", timeout=30000)
                print(f"HTTP {resp.status if resp else '?'}")
            except Exception as e:
                print(f"Error: {e}")
                continue

            await page.wait_for_timeout(5000)

            # Guardar HTML renderizado
            html = await page.content()
            slug = url.rstrip("/").split("/")[-1] or "home"
            html_file = out_dir / f"{i}_{slug}.html"
            html_file.write_text(html, encoding="utf-8")
            print(f"HTML: {len(html)} bytes → {html_file.name}")

            # Screenshot
            shot = out_dir / f"{i}_{slug}.png"
            await page.screenshot(path=str(shot), full_page=True)
            print(f"Screenshot: {shot.name}")

            # Contar links
            links = await page.eval_on_selector_all(
                "a",
                """els => els.map(el => ({
                    href: el.href,
                    text: el.innerText.trim()
                }))"""
            )
            print(f"Total links: {len(links)}")

            # Links que parecen eventos
            eventos = [
                l for l in links
                if l["text"] and len(l["text"]) > 5
                and any(k in l["href"].lower() for k in
                        ["evento", "show", "entrada", "ticket", "artista"])
            ]
            print(f"Links tipo evento: {len(eventos)}")
            for l in eventos[:15]:
                print(f"  {l['text'][:60]}  →  {l['href']}")

            # Buscar texto que contenga palabras clave
            body_text = await page.inner_text("body")
            for kw in ["AGOTADO", "SOLD OUT", "Entradas", "Comprar", "Tickets"]:
                if kw.lower() in body_text.lower():
                    print(f"  Contiene: '{kw}'")

        await browser.close()
    print(f"\n✅ Listo. Revisá la carpeta: {out_dir}")


if __name__ == "__main__":
    asyncio.run(main())
"""
Orquestador de scrapers.
Detecta su propia ubicación, así funciona desde cualquier carpeta.
"""
import subprocess
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)

try:
    import schedule
    HAS_SCHEDULE = True
except ImportError:
    HAS_SCHEDULE = False

ROOT = Path(__file__).resolve().parent
SCRAPERS_DIR = ROOT / "scrapers"

JOBS = [
    "ticketek.py",
    "passline.py",
    "movistar_arena.py",
    "df_entertainment.py",
    # "all_access.py",       # no existe todavía
    # "agenda_ba.py",        # endpoint roto
    # "bandsintown.py",      # no existe todavía
    "trends.py",
]


def run_all():
    print(f"Proyecto: {ROOT}")
    print(f"Scrapers: {SCRAPERS_DIR}\n")

    for job in JOBS:
        script = SCRAPERS_DIR / job
        if not script.exists():
            print(f"[skip] No existe: {script.name}")
            continue

        print(f"=== {script.name} ===")
        try:
            result = subprocess.run(
                [sys.executable, script.name],
                cwd=str(SCRAPERS_DIR),
                timeout=900,   # 15 min máximo por scraper
            )
            if result.returncode != 0:
                print(f"[warn] {script.name} terminó con código {result.returncode}")
        except subprocess.TimeoutExpired:
            print(f"[timeout] {script.name} tardó más de 15 min, salteado")
        print()


if __name__ == "__main__":
    print(f"Python: {sys.executable}\n")

    # Reparar nombres viejos primero
    reparar = SCRAPERS_DIR / "reparar_nombres.py"
    if reparar.exists():
        print("=== reparar_nombres.py ===")
        subprocess.run([sys.executable, reparar.name], cwd=str(SCRAPERS_DIR))
        print()

    run_all()

    if not HAS_SCHEDULE:
        print("[info] 'schedule' no instalado. Corrida única.")
        sys.exit(0)

    schedule.every(6).hours.do(run_all)
    print("[info] Próxima corrida en 6 h. Ctrl+C para salir.\n")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n[info] Detenido por el usuario.")
"""
Lanzador del dashboard de conciertos.
- Verifica que existan las dependencias
- Verifica que exista la DB
- Lanza Streamlit
Uso: python run_dashboard.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DASHBOARD = ROOT / "dashboard.py"
DB = ROOT / "data" / "conciertos.db"

# --- Verificaciones ---
if not DASHBOARD.exists():
    print(f"ERROR: no existe {DASHBOARD}")
    print("Creá dashboard.py primero con el script que te pasé.")
    sys.exit(1)

if not DB.exists():
    print(f"AVISO: no existe {DB}")
    print("Corré primero algún scraper:")
    print("  python scrapers/ticketek.py")
    print("  python scrapers/passline.py")
    print("  python scrapers/movistar_arena.py")
    print("\nLanzo el dashboard igual (vas a ver tablas vacías).\n")

try:
    import streamlit  # noqa
    import plotly     # noqa
    import pandas     # noqa
    import sqlalchemy # noqa
except ImportError as e:
    print(f"Falta dependencia: {e}")
    print("Instalando...")
    subprocess.run([sys.executable, "-m", "pip", "install",
                    "streamlit", "plotly", "pandas", "sqlalchemy"])

# --- Lanzar Streamlit ---
print(f"Lanzando dashboard desde {ROOT}")
print(f"Python: {sys.executable}")
print(f"Dashboard: {DASHBOARD}\n")

subprocess.run([
    sys.executable, "-m", "streamlit", "run",
    str(DASHBOARD),
    "--server.headless=false",
])
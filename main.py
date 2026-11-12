"""SAM - extractor del ranking diario de TikTok LIVE.

Uso:
  python main.py check      Verifica que el Android esta conectado.
  python main.py inspect    Guarda captura + estructura de la pantalla actual (para calibrar).
  python main.py run        Recorre el ranking abierto y guarda Excel + txt en output/.
"""
import sys

from sam import device, export, ranking
from sam.config import load_config


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    cfg = load_config()
    d = device.connect(cfg.get("device_serial"))

    if cmd == "check":
        return
    if cmd == "inspect":
        device.dump_screen(d, sys.argv[2] if len(sys.argv) > 2 else "inspect")
        return
    if cmd == "run":
        results = ranking.scrape(d, cfg)
        export.save(results)
        missing = sum(1 for r in results if not r["username"])
        print(f"Listo: {len(results)} filas, {missing} sin username.")
        return
    print(__doc__)


if __name__ == "__main__":
    main()

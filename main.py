"""SAM - extractor del ranking diario de TikTok LIVE.

Uso:
  python main.py check      Verifica que el Android esta conectado.
  python main.py liga       Muestra la liga del ranking abierto.
  python main.py inspect    Guarda captura + estructura de la pantalla actual (para calibrar).
  python main.py run [N] [--liga D5]
                            Recorre el ranking (N puestos, por defecto 100) y guarda Excel + txt
                            en output/. Con --liga busca un LIVE de esa liga si el abierto es de otra.

Todos los toques pasan por sam/guard.py: si TikTok no esta al frente (llamada, otra app,
notificacion encima) el script espera y vuelve a TikTok antes de seguir.
"""
import sys

from sam import device, export, ranking
from sam.guard import SafeDevice, NotInTikTok
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
    if cmd == "liga":
        print("Liga abierta:", ranking.current_league(d))
        return
    if cmd == "run":
        args = sys.argv[2:]
        league = None
        if "--liga" in args:
            i = args.index("--liga")
            league = args[i + 1]
            args = args[:i] + args[i + 2:]
        if args:
            cfg["target_count"] = int(args[0])
        sd = SafeDevice(d, cfg.get("max_wait_outside_sec", 900))
        try:
            sd.ensure_tiktok()
        except NotInTikTok as e:
            print(e)
            return
        results = ranking.scrape(sd, cfg, league)
        try:
            lg = ranking.current_league(d) or league or "liga"
        except Exception:
            lg = league or "liga"
        export.save(results, lg)
        missing = sum(1 for r in results if not r["username"])
        print(f"Listo: {len(results)} filas, {missing} sin username.")
        return
    print(__doc__)


if __name__ == "__main__":
    main()

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
import os
import sys
from datetime import datetime
from pathlib import Path


class _Tee:
    """Muestra en consola al instante y guarda cada linea en logs/ con la hora."""

    def __init__(self, stream, path):
        self.stream, self.f, self.bol = stream, open(path, "a", encoding="utf-8", buffering=1), True

    def write(self, s):
        self.stream.write(s)
        self.stream.flush()
        for part in s.splitlines(keepends=True):
            if self.bol:
                self.f.write(datetime.now().strftime("%H:%M:%S ") )
            self.f.write(part)
            self.bol = part.endswith("\n")
        self.f.flush()

    def flush(self):
        self.stream.flush()
        self.f.flush()


def _no_quickedit():
    """En Windows, un clic dentro de la consola activa el 'modo seleccion' y congela el
    programa al imprimir. Se desactiva ese modo (QuickEdit) en esta ventana."""
    if os.name != "nt":
        return
    try:
        import ctypes
        k = ctypes.windll.kernel32
        h = k.GetStdHandle(-10)  # STD_INPUT_HANDLE
        mode = ctypes.c_uint32()
        if k.GetConsoleMode(h, ctypes.byref(mode)):
            ENABLE_QUICK_EDIT, ENABLE_EXTENDED_FLAGS = 0x0040, 0x0080
            k.SetConsoleMode(h, (mode.value & ~ENABLE_QUICK_EDIT) | ENABLE_EXTENDED_FLAGS)
    except Exception:
        pass


_LOCK = None


def _single_instance():
    """Candado del sistema: solo una extraccion a la vez. Se libera solo si el proceso
    termina o se cae, asi que una ventana colgada que ya se cerro no bloquea nada."""
    global _LOCK
    path = Path(__file__).parent / "logs" / ".run.lock"
    path.parent.mkdir(exist_ok=True)
    _LOCK = open(path, "a+")
    try:
        if os.name == "nt":
            import msvcrt
            _LOCK.seek(0)
            msvcrt.locking(_LOCK.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(_LOCK, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def _setup_log(name):
    logs = Path(__file__).parent / "logs"
    logs.mkdir(exist_ok=True)
    path = logs / f"{datetime.now():%Y-%m-%d_%H%M}_{name}.log"
    sys.stdout = _Tee(sys.stdout, path)
    sys.stderr = _Tee(sys.stderr, path)
    print(f"Log: {path}")
    _watchdog(path)


def _watchdog(path, idle_sec=150):
    """Si el log no avanza en idle_sec, guarda en el log donde esta trabado el programa."""
    import faulthandler, threading, time, os
    def run():
        dumped = 0.0
        while True:
            time.sleep(20)
            try:
                last = os.path.getmtime(path)
            except OSError:
                continue
            if time.time() - last > idle_sec and last != dumped:
                dumped = last
                with open(path, "a", encoding="utf-8") as f:
                    f.write(f"\n[watchdog] sin avance {idle_sec}s; pila actual:\n")
                    f.flush()
                    faulthandler.dump_traceback(file=f, all_threads=True)
    threading.Thread(target=run, daemon=True).start()


def _open_watch():
    """Abre la ventana de seguimiento (seguir.ps1) si no hay una abierta ya."""
    import os, subprocess
    if os.name != "nt" or os.environ.get("TIKTOK_FILTER_CONSOLE") == "1":
        return
    root = Path(__file__).parent
    pidf = root / "logs" / ".watch.pid"
    try:
        pid = int(pidf.read_text().strip())
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                             capture_output=True, text=True).stdout
        if str(pid) in out:
            return
    except Exception:
        pass
    try:
        subprocess.Popen(["powershell", "-NoExit", "-ExecutionPolicy", "Bypass",
                          "-File", str(root / "seguir.ps1")],
                         creationflags=subprocess.CREATE_NEW_CONSOLE)
    except Exception as e:
        print(f"No pude abrir la ventana de seguimiento: {e}")

from sam import device, export, ranking
from sam.guard import SafeDevice, NotInTikTok
from sam.config import load_config


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    try:
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
        sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)
    except Exception:
        pass
    if cmd == "run":
        _no_quickedit()
        if not _single_instance():
            print("Ya hay otra extraccion corriendo con este celular. Cierra esa ventana")
            print("o espera a que termine antes de abrir otra.")
            if os.environ.get("TIKTOK_FILTER_CONSOLE") == "1":
                input("Enter para cerrar...")
            return
        _setup_log("run_" + "_".join(a.lstrip("-") for a in sys.argv[2:]) if len(sys.argv) > 2 else "run")
        _open_watch()
        print(f"Inicio: {datetime.now():%Y-%m-%d %H:%M:%S}  comando: {' '.join(sys.argv[1:])}")
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
        # --liga acepta varias separadas por coma: se extrae cada una en cuanto
        # aparece un LIVE de cualquiera de ellas, hasta completar todas.
        if league:
            from sam.ligas import normalize
            pending, bad = normalize(league)
            if bad:
                print(f"Ignoro ligas no validas: {', '.join(bad)} (validas: A1-A3, B1-B5, C1-C5, D1-D5)")
            if not pending:
                print("No hay ninguna liga valida para buscar.")
                return
        else:
            pending = [None]
        done = []
        while pending:
            want = ",".join(pending) if pending[0] else None
            results = ranking.scrape(sd, cfg, want)
            lg = ranking.LAST_LEAGUE
            if not lg:
                try:
                    lg = ranking.current_league(d)
                except Exception:
                    lg = None
            if league and (not lg or lg not in pending or not results):
                print(f"No pude extraer ninguna de: {', '.join(pending)}")
                break
            export.save(results, lg or "liga")
            missing = sum(1 for r in results if not r["username"])
            print(f"Listo {lg or ''}: {len(results)} filas, {missing} sin username.  {datetime.now():%H:%M:%S}")
            done.append(lg)
            if not league:
                break
            pending.remove(lg)
            if pending:
                print(f"Faltan: {', '.join(pending)}")
        if league:
            print(f"Ligas extraidas: {', '.join(done) or 'ninguna'}"
                  + (f"  |  sin extraer: {', '.join(pending)}" if pending else ""))
        print(f"Fin: {datetime.now():%H:%M:%S}")
        return
    print(__doc__)


if __name__ == "__main__":
    main()

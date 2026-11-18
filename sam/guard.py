"""Proteccion contra pantallas ajenas a TikTok (llamadas, notificaciones, otras apps).

Antes de cada toque, swipe o 'atras' se verifica que:
  1. No haya una llamada sonando o en curso (si la hay, se espera sin tocar nada).
  2. La app en primer plano sea TikTok (si no, se espera y se vuelve a abrir TikTok).
  3. El punto a tocar no este tapado por un elemento de otra app
     (ej. notificacion flotante); si lo esta, se espera a que desaparezca.
"""
import re
import time
import xml.etree.ElementTree as ET

TIKTOK_PKG = "com.zhiliaoapp.musically"
CALL_RE = re.compile(r"mCallState=(\d)")
BOUNDS_RE = re.compile(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]")
STATUS_BAR_MAX_Y = 130   # la barra de estado siempre esta; se ignora


class NotInTikTok(Exception):
    """No se pudo volver a TikTok de forma segura."""


def in_call(d):
    """True si hay una llamada sonando o en curso. El resultado se reutiliza 1.5s:
    dumpsys tarda y, en la misma fila, el toque y el 'atras' caen dentro de esa ventana."""
    now = time.time()
    hit = getattr(in_call, "_hit", None)
    if hit and now - hit[0] < 1.5:
        return hit[1]
    result = False
    for cmd in ("dumpsys telephony.registry | grep mCallState", "dumpsys telephony.registry"):
        try:
            out = d.shell(cmd, timeout=6).output
        except Exception:
            continue
        if out and "mCallState=" in out:
            result = any(s != "0" for s in CALL_RE.findall(out))
            break
    in_call._hit = (now, result)
    return result


TOP_RE = re.compile(r"(?:topResumedActivity|mResumedActivity|ResumedActivity|mCurrentFocus|mFocusedApp)[=:].*?\s([\w.]+)/([\w.$]+)")


def current_app(d):
    """App y activity realmente al frente. app_current() de uiautomator2 se confunde en
    algunos celulares (p. ej. Honor) cuando otra app tiene una ventana en segundo plano.
    Primero la consulta corta (ventana enfocada); el volcado de activities es el respaldo."""
    for cmd in ("dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'",
                "dumpsys activity activities | grep -E 'topResumedActivity|ResumedActivity'"):
        try:
            out = d.shell(cmd, timeout=10).output
        except Exception:
            continue
        m = TOP_RE.search(out)
        if m:
            pkg, act = m.group(1), m.group(2)
            if act.startswith("."):
                act = pkg + act
            return {"package": pkg, "activity": act}
    try:
        return d.app_current()
    except Exception:
        return {}


def _foreground(d):
    return (current_app(d) or {}).get("package")


def _overlay_at(d, x, y):
    """True si en (x, y) hay un elemento de otra app (notificacion flotante, dialogo)."""
    try:
        root = ET.fromstring(d.dump_hierarchy(compressed=False))
    except Exception:
        return False
    for n in root.iter("node"):
        pkg = n.attrib.get("package", "")
        if not pkg or pkg == TIKTOK_PKG:
            continue
        m = BOUNDS_RE.match(n.attrib.get("bounds", ""))
        if not m:
            continue
        x1, y1, x2, y2 = map(int, m.groups())
        if y2 <= STATUS_BAR_MAX_Y:
            continue
        if x1 <= x <= x2 and y1 <= y <= y2:
            return True
    return False


class SafeDevice:
    """Envuelve el dispositivo de uiautomator2: click/swipe/press solo se ejecutan si
    TikTok esta al frente y nada ajeno tapa la zona. El resto de metodos pasa directo."""

    def __init__(self, d, max_wait_sec=900):
        self._d = d
        self.max_wait_sec = max_wait_sec
        self.recovered = False   # se pone True si hubo que volver a TikTok
        self._front_until = 0.0    # hasta cuando damos por bueno que TikTok sigue al frente
        self._overlay_until = 0.0  # hasta cuando damos por bueno que no hay nada ajeno encima

    def __getattr__(self, name):
        return getattr(self._d, name)

    def app_current(self):
        return current_app(self._d)

    def ensure_tiktok(self):
        start = time.time()
        warned = False
        while time.time() - start < self.max_wait_sec:
            if in_call(self._d):
                self._front_until = 0.0
                if not warned:
                    print("  [guard] Llamada en curso: espero sin tocar nada...")
                    warned = True
                time.sleep(5)
                continue
            # Acabamos de comprobarlo: el 'atras' de la misma fila no vuelve a preguntar.
            if time.time() < self._front_until:
                return
            pkg = _foreground(self._d)
            if pkg == TIKTOK_PKG:
                self._front_until = time.time() + 2.5
                if warned:
                    print("  [guard] De vuelta en TikTok.")
                return
            print(f"  [guard] En primer plano esta '{pkg}', no TikTok. Vuelvo a TikTok...")
            warned = True
            self.recovered = True
            self._front_until = 0.0
            self._overlay_until = 0.0
            time.sleep(3)   # por si era algo pasajero
            if _foreground(self._d) != TIKTOK_PKG and not in_call(self._d):
                self._d.app_start(TIKTOK_PKG)   # trae TikTok al frente sin reiniciarlo
                time.sleep(4)
        raise NotInTikTok(f"No pude volver a TikTok en {self.max_wait_sec}s.")

    def _wait_clear(self, x, y, timeout=20):
        if time.time() < self._overlay_until:
            return True
        start = time.time()
        while _overlay_at(self._d, x, y):
            self._overlay_until = 0.0
            if time.time() - start > timeout:
                print("  [guard] Algo sigue tapando la pantalla; continuo con precaucion.")
                return False
            print("  [guard] Notificacion encima: espero a que se quite...")
            time.sleep(3)
            self.ensure_tiktok()
        self._overlay_until = time.time() + 4.0
        return True

    def click(self, x, y):
        self.ensure_tiktok()
        if not self._wait_clear(x, y):
            return   # mejor no tocar si sigue tapado
        self._d.click(x, y)

    def swipe(self, x1, y1, x2, y2, **kw):
        self.ensure_tiktok()
        self._wait_clear(x1, y1)
        self._d.swipe(x1, y1, x2, y2, **kw)

    def press(self, key):
        self.ensure_tiktok()
        self._d.press(key)

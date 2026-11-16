import time
from datetime import datetime
from pathlib import Path

import uiautomator2 as u2

from .config import ROOT


def connect(serial=None):
    d = u2.connect(serial) if serial else u2.connect()
    info = d.info
    print(f"Conectado: {d.serial} ({info.get('productName')}) pantalla {info.get('displayWidth')}x{info.get('displayHeight')}")
    return d


def dump_screen(d, label="screen"):
    """Guarda captura + jerarquia de la UI para calibrar los selectores."""
    out = ROOT / "dumps"
    out.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    png = out / f"{stamp}_{label}.png"
    xml = out / f"{stamp}_{label}.xml"
    d.screenshot(str(png))
    xml.write_text(d.dump_hierarchy(compressed=False), encoding="utf-8")
    print(f"Guardado: {png.name} y {xml.name}")
    return png, xml


def sleep(sec):
    """Pausa con una pequena variacion al azar para no tener un ritmo de robot."""
    import random
    time.sleep(max(0.0, sec + random.uniform(0.0, 0.25)))

"""Respaldo de la extraccion: cada usuario se guarda al momento en output/respaldo/.

Si el programa se cierra, se cuelga o se apaga la PC, lo extraido no se pierde, y la
proxima corrida de esa misma liga (el mismo dia, dentro de RETOMAR_HORAS) sigue desde ahi.
"""
import ast
import re
import time
from datetime import datetime

from .config import ROOT

DIR = ROOT / "output" / "respaldo"
CAMPOS = ("puesto", "nombre_visible", "username", "puntos")
RETOMAR_HORAS = 3


def _path(league):
    return DIR / f"parcial_{league or 'liga'}_{datetime.now():%Y-%m-%d}.tsv"


def _limpio(v):
    return str(v or "").replace("\t", " ").replace("\r", " ").replace("\n", " ")


def load(league):
    """Filas ya extraidas hoy de esa liga (si el respaldo es reciente)."""
    p = _path(league)
    if not p.exists():
        return []
    if time.time() - p.stat().st_mtime > RETOMAR_HORAS * 3600:
        # muy viejo: el ranking ya cambio mucho, se empieza de cero
        p.rename(p.with_name(p.stem + f"_viejo_{datetime.now():%H%M}.tsv"))
        return []
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines()[1:]:
        parts = line.split("\t")
        if len(parts) >= 3 and parts[0].strip():
            parts += [""] * (len(CAMPOS) - len(parts))
            rows.append(dict(zip(CAMPOS, parts)))
    return rows


def append(league, row):
    DIR.mkdir(parents=True, exist_ok=True)
    p = _path(league)
    nuevo = not p.exists()
    with open(p, "a", encoding="utf-8") as f:
        if nuevo:
            f.write("\t".join(CAMPOS) + "\n")
        f.write("\t".join(_limpio(row.get(k)) for k in CAMPOS) + "\n")
        f.flush()


def close(league):
    """La liga se termino y se guardo su Excel: el respaldo queda marcado como completo."""
    p = _path(league)
    if p.exists():
        p.rename(p.with_name(p.stem + f"_completo_{datetime.now():%H%M}.tsv"))


LIGA_RE = re.compile(r"== Extrayendo liga (\w+) ==")
FILA_RE = re.compile(r"^\d\d:\d\d:\d\d \[\d+/\d+\]\s+(\d+)\. (.+) -> @(\S*)\s+\[\w+\]\s*$")


def from_log(path):
    """Recupera las filas extraidas de un log: {liga: [filas]}."""
    ligas, cur = {}, "liga"
    for line in open(path, encoding="utf-8", errors="replace"):
        m = LIGA_RE.search(line)
        if m:
            cur = m.group(1)
            continue
        m = FILA_RE.match(line.rstrip("\n"))
        if m:
            try:
                nombre = ast.literal_eval(m.group(2))
            except Exception:
                nombre = m.group(2)
            user = "" if m.group(3) == "None" else m.group(3)
            ligas.setdefault(cur, []).append(
                {"puesto": m.group(1), "nombre_visible": nombre, "username": user, "puntos": ""})
    return ligas

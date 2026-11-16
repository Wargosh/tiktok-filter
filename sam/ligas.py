"""Normaliza lo que escribe el usuario como ligas: ' c5; c4 . d1 ' -> 'C5,C4,D1'.

Uso desde consola:  python -m sam.ligas "c5, c4"   -> imprime C5,C4 (o error y sale con 1)
"""
import re
import sys

VALID = {f"{l}{n}" for l, top in (("A", 3), ("B", 5), ("C", 5), ("D", 5)) for n in range(1, top + 1)}


def normalize(text):
    """Devuelve (ligas_validas_sin_repetir, partes_invalidas)."""
    s = (text or "").upper()
    s = re.sub(r"LIGA|LEAGUE", " ", s)
    s = re.sub(r"[^A-Z0-9]+", " ", s)          # cualquier separador -> espacio
    s = re.sub(r"([A-Z])\s+(\d)", r"\1\2", s)   # 'C 5' -> 'C5'
    ok, bad = [], []
    for part in s.split():
        found = re.findall(r"[A-Z]\d", part)    # 'C5C4' -> C5, C4
        if not found or "".join(found) != part:
            bad.append(part)
            continue
        for lg in found:
            if lg not in VALID:
                bad.append(lg)
            elif lg not in ok:
                ok.append(lg)
    return ok, bad


if __name__ == "__main__":
    ok, bad = normalize(" ".join(sys.argv[1:]))
    if bad or not ok:
        print("INVALIDO:" + ",".join(bad or ["(vacio)"]))
        sys.exit(1)
    print(",".join(ok))
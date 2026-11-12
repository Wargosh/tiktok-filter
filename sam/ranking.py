"""Recorre el ranking diario abierto en pantalla y obtiene el @username de cada puesto.

Flujo: el usuario (o un paso previo) deja abierto el ranking diario de la liga.
Por cada fila visible: tocar -> leer @username en la tarjeta/perfil -> volver.
Cuando se acaban las filas visibles, hace scroll y sigue hasta llegar a target_count.
"""
import re

from .device import dump_screen, sleep

USERNAME_RE = re.compile(r"@?([A-Za-z0-9._]{2,24})")


def _visible_rows(d, sel):
    rows = d(**sel["ranking_row"])
    return [rows[i] for i in range(rows.count)] if rows.exists else []


def _row_key(row, sel):
    """Identificador de la fila (nombre visible + puesto) para no repetirla tras el scroll."""
    pos, name = "", ""
    try:
        p = row.child(**sel["row_position"])
        if p.exists:
            pos = p.get_text() or ""
        n = row.child(**sel["row_display_name"])
        if n.exists:
            name = n.get_text() or ""
    except Exception:
        pass
    return pos.strip(), name.strip()


def _read_username(d, sel, timeout=4):
    el = d(**sel["profile_username"])
    if el.wait(timeout=timeout):
        m = USERNAME_RE.search(el.get_text() or "")
        if m:
            return m.group(1)
    return None


def scrape(d, cfg):
    sel = cfg["selectors"]
    target = cfg["target_count"]
    results, seen = [], set()
    scrolls = 0

    while len(results) < target and scrolls <= cfg["max_scrolls"]:
        new_in_screen = 0
        for row in _visible_rows(d, sel):
            key = _row_key(row, sel)
            if key in seen or key == ("", ""):
                continue
            seen.add(key)
            new_in_screen += 1

            row.click()
            sleep(cfg["tap_delay_sec"])
            username = _read_username(d, sel)
            if not username:
                dump_screen(d, f"sin_username_{len(results)+1}")
            results.append({
                "puesto": key[0] or str(len(results) + 1),
                "nombre_visible": key[1],
                "username": username or "",
            })
            print(f"{len(results):>3}. {key[1]!r} -> @{username}")
            d.press("back")
            sleep(cfg["back_delay_sec"])
            if len(results) >= target:
                break

        if len(results) >= target:
            break
        d.swipe_ext("up", scale=0.6)
        sleep(cfg["scroll_delay_sec"])
        scrolls += 1
        if new_in_screen == 0 and scrolls > 3:
            print("No aparecen filas nuevas; fin de la lista o selectores incorrectos.")
            break

    return results

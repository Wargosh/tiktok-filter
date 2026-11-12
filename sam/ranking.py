"""Recorre el ranking de liga (TikTok LIVE) abierto en pantalla y obtiene el @username de cada puesto.

Pantalla esperada: un LIVE con la hoja "Daily Ranking" abierta en la pestaña "League DX".
Por cada fila: tocar -> se abre la tarjeta del usuario -> leer el username (debajo del nombre)
-> atras -> siguiente. Cuando se acaban las filas visibles, scroll dentro de la lista.

Se lee la jerarquia de la UI (no OCR) y se evita depender de ids ofuscados de TikTok:
solo se usa el id estable "user_name" y el texto "followers"/"seguidores" de la tarjeta.
"""
import re
import xml.etree.ElementTree as ET

from .device import dump_screen, sleep

BOUNDS_RE = re.compile(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]")
FOLLOWERS_RE = re.compile(r"(followers|seguidores)", re.I)


def _bounds(node):
    m = BOUNDS_RE.match(node.attrib.get("bounds", ""))
    return tuple(map(int, m.groups())) if m else (0, 0, 0, 0)


def _rid(node):
    return node.attrib.get("resource-id", "").split("/")[-1]


def _tree(d):
    return ET.fromstring(d.dump_hierarchy(compressed=False))


def _ranking_list(root):
    """RecyclerView scrollable que contiene filas con user_name."""
    for n in root.iter("node"):
        if n.attrib.get("scrollable") == "true" and "RecyclerView" in n.attrib.get("class", ""):
            if any(_rid(c) == "user_name" for c in n.iter("node")):
                return n
    return None


def _rows(root):
    """Devuelve filas visibles: puesto, nombre visible, puntos y centro para tocar."""
    lst = _ranking_list(root)
    if lst is None:
        return [], None
    lb = _bounds(lst)
    rows = []
    for row in lst:
        texts = [(n.attrib.get("text", ""), _rid(n), _bounds(n)) for n in row.iter("node")]
        name = next((t for t, r, _ in texts if r == "user_name"), None)
        if name is None:
            continue
        pos = next((t for t, r, b in texts if t.strip().isdigit() and b[0] < 150), "")
        score = next((t for t, r, b in texts if b[0] > 850 and t.strip()), "")
        x1, y1, x2, y2 = _bounds(row)
        # solo filas completamente dentro de la lista visible
        if y1 < lb[1] or y2 > lb[3]:
            continue
        rows.append({"puesto": pos.strip(), "nombre_visible": name.strip(), "puntos": score.strip(),
                     "tap": ((x1 + x2) // 2, (y1 + y2) // 2)})
    return rows, lb


def _find(root, pred):
    return next((n for n in root.iter("node") if pred(n)), None)


def _center(node):
    x1, y1, x2, y2 = _bounds(node)
    return (x1 + x2) // 2, (y1 + y2) // 2


def _card_username(root):
    """Username de la tarjeta de usuario (texto user_name justo encima de 'followers')."""
    fol = _find(root, lambda n: FOLLOWERS_RE.search(n.attrib.get("text", "")))
    if fol is None:
        return None
    ftop = _bounds(fol)[1]
    cands = [n for n in root.iter("node")
             if _rid(n) == "user_name" and ftop - 350 < _bounds(n)[3] <= ftop]
    if not cands:
        return None
    return cands[-1].attrib.get("text", "").strip().lstrip("@") or None


def _ranking_entrance(root):
    return _find(root, lambda n: _rid(n) == "tv_ranking_entrance_text")


def _host_block(root):
    """Bloque del anfitrion arriba a la izquierda del LIVE (contiene user_name)."""
    name = _find(root, lambda n: _rid(n) == "user_name" and _bounds(n)[1] < 400)
    return name


def _wait_state(d, timeout=6.0):
    """Espera hasta reconocer la pantalla: 'card', 'list' o 'live'."""
    waited = 0.0
    root = None
    while waited <= timeout:
        root = _tree(d)
        if _card_username(root):
            return "card", root
        if _ranking_list(root) is not None and waited > 2.5:
            return "list", root
        if _ranking_entrance(root) is not None and _ranking_list(root) is None and waited > 2.0:
            return "live", root
        sleep(0.5)
        waited += 0.5
    return "unknown", root


LEAGUE_RE = re.compile(r"(?:League|Liga)\s*([A-Z]\d)", re.I)


def current_league(d=None, root=None):
    """Devuelve la liga de la pestana del ranking abierto (ej. 'D5') o None."""
    root = root if root is not None else _tree(d)
    for n in root.iter("node"):
        m = LEAGUE_RE.search(n.attrib.get("text", ""))
        if m and 900 < _bounds(n)[1] < 1300:
            return m.group(1).upper()
    return None


def _close_sheet(d):
    """Cierra la hoja del ranking tocando sobre el video, encima de la hoja."""
    d.click(540, 450)
    sleep(1.0)


def find_league(d, target, max_lives=80):
    """Desde un LIVE, pasa de LIVE en LIVE hasta encontrar uno cuya liga sea `target`
    y deja abierto su ranking en la pestana de liga."""
    target = target.upper()
    for i in range(max_lives):
        root = _tree(d)
        if _ranking_list(root) is not None:
            lg = current_league(root=root)
            print(f"  LIVE {i+1}: liga {lg}")
            if lg == target:
                return True
            _close_sheet(d)
            root = _tree(d)
        ent = _ranking_entrance(root)
        if ent is not None:
            pill = ent.attrib.get("text", "")
            m = LEAGUE_RE.search(pill)
            if m and m.group(1).upper() != target:
                print(f"  LIVE {i+1}: liga {m.group(1).upper()}")
            else:
                d.click(*_center(ent))
                sleep(2.0)
                select_league_tab(d)
                continue
        # siguiente LIVE
        d.swipe(540, 1700, 540, 500, duration=0.3)
        sleep(3.0)
    print(f"No encontre un LIVE de la liga {target} en {max_lives} intentos.")
    return False


def select_league_tab(d):
    """En la hoja de ranking, toca la pestana 'League ...' si existe."""
    root = _tree(d)
    tab = _find(root, lambda n: n.attrib.get("text", "").strip().startswith(("League", "Liga"))
                and 900 < _bounds(n)[1] < 1300)
    if tab is not None:
        d.click(*_center(tab))
        sleep(1.5)
        return True
    return False


def reopen_ranking(d):
    """Desde un LIVE, abre la hoja de ranking y la pestana de liga."""
    for _ in range(3):
        root = _tree(d)
        ent = _ranking_entrance(root)
        if ent is not None:
            d.click(*_center(ent))
            sleep(2.0)
            select_league_tab(d)
            if _ranking_list(_tree(d)) is not None:
                return True
        sleep(1.0)
    return False


def _username_from_live(d, root):
    """Estamos dentro del LIVE del usuario: toca al anfitrion y lee su username de la tarjeta."""
    host = _host_block(root)
    if host is None:
        return None
    d.click(*_center(host))
    sleep(1.5)
    state, root2 = _wait_state(d, timeout=4)
    username = _card_username(root2) if state == "card" else None
    if state == "card":
        d.press("back")
        sleep(1.0)
    return username


def scroll_to_top(d, max_swipes=40):
    """Sube la lista hasta que se vea el puesto 1."""
    for _ in range(max_swipes):
        rows, lb = _rows(_tree(d))
        if lb is None:
            return False
        if any(r["puesto"] == "1" for r in rows):
            return True
        x = (lb[0] + lb[2]) // 2
        d.swipe(x, lb[1] + 60, x, lb[3] - 60, duration=0.25)
        sleep(0.6)
    return False


def scrape(d, cfg, league=None):
    target = cfg["target_count"]
    if league:
        if current_league(d) != league.upper() and not find_league(d, league, cfg.get("max_lives_search", 80)):
            return []
    results, seen = [], set()
    stale_scrolls = 0
    select_league_tab(d)
    scroll_to_top(d)

    while len(results) < target and stale_scrolls < 3:
        rows, lb = _rows(_tree(d))
        if lb is None:
            if reopen_ranking(d):
                continue
            dump_screen(d, "sin_lista")
            print("No encuentro la lista del ranking en pantalla. Abre 'Daily Ranking' > 'League' y reintenta.")
            break

        rows = [r for r in rows if r["puesto"]]
        new_rows = [r for r in rows if (r["puesto"], r["nombre_visible"]) not in seen]
        last_pos = max((int(r["puesto"]) for r in rows), default=0)
        max_seen = max((int(p) for p, _ in seen), default=0)

        if not new_rows and last_pos >= max_seen and rows:
            stale_scrolls += 1
        else:
            stale_scrolls = 0

        lost_list = False
        for r in new_rows:
            seen.add((r["puesto"], r["nombre_visible"]))
            d.click(*r["tap"])
            sleep(cfg["tap_delay_sec"])
            state, root = _wait_state(d)
            username = None
            if state == "card":
                username = _card_username(root)
                d.press("back")
                sleep(cfg["back_delay_sec"])
            elif state == "live":
                username = _username_from_live(d, root)
                lost_list = True
            if not username:
                dump_screen(d, f"sin_username_{r['puesto']}")
            r["username"] = username or ""
            results.append({k: r[k] for k in ("puesto", "nombre_visible", "username", "puntos")})
            print(f"{r['puesto']:>3}. {r['nombre_visible']!r} -> @{username}  [{state}]")
            if len(results) >= target or lost_list or state == "unknown":
                break

        if len(results) >= target:
            break
        if lost_list or state == "unknown":
            if not reopen_ranking(d):
                dump_screen(d, "no_reabre")
                print("No pude volver a abrir el ranking.")
                break
            continue
        # scroll dentro de la lista (de abajo hacia arriba)
        x = (lb[0] + lb[2]) // 2
        d.swipe(x, lb[3] - 60, x, lb[1] + 60, duration=0.4)
        sleep(cfg["scroll_delay_sec"])

    if stale_scrolls >= 3:
        print("No aparecen filas nuevas: fin de la lista.")
    results.sort(key=lambda r: int(r["puesto"]) if r["puesto"].isdigit() else 999)
    return results

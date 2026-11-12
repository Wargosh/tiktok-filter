from datetime import datetime

from openpyxl import Workbook

from .config import ROOT


def save(results, league="liga"):
    out = ROOT / "output"
    out.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    xlsx = out / f"ranking_{league}_{stamp}.xlsx"
    txt = out / f"ranking_{league}_{stamp}.txt"

    wb = Workbook()
    ws = wb.active
    ws.title = "Ranking"
    ws.append(["Liga", "Puesto", "Nombre visible", "Username", "Puntos"])
    for r in results:
        ws.append([league, r["puesto"], r["nombre_visible"], r["username"], r.get("puntos", "")])
    wb.save(xlsx)

    txt.write_text("\n".join(r["username"] for r in results if r["username"]), encoding="utf-8")
    print(f"Guardado: {xlsx} y {txt}")
    return xlsx

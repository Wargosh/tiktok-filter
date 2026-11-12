from datetime import datetime

from openpyxl import Workbook

from .config import ROOT


def save(results):
    out = ROOT / "output"
    out.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    xlsx = out / f"ranking_{stamp}.xlsx"
    txt = out / f"ranking_{stamp}.txt"

    wb = Workbook()
    ws = wb.active
    ws.title = "Ranking"
    ws.append(["Puesto", "Nombre visible", "Username"])
    for r in results:
        ws.append([r["puesto"], r["nombre_visible"], r["username"]])
    wb.save(xlsx)

    txt.write_text("\n".join(r["username"] for r in results if r["username"]), encoding="utf-8")
    print(f"Guardado: {xlsx} y {txt}")
    return xlsx

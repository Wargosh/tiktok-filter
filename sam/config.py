import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_config() -> dict:
    path = ROOT / "config.json"
    if not path.exists():
        path = ROOT / "config.example.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)

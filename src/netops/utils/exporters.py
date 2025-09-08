import json, csv
from pathlib import Path

def to_json(path: str, data):
    Path(path).write_text(json.dumps(data, indent=2))

def to_csv(path: str, rows: list[dict]):
    if not rows:
        Path(path).write_text("")
        return
    keys = rows[0].keys()
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)

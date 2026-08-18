#!/usr/bin/env python3
"""
embed_data.py — re-embed the raw data-pack CSVs into index.html's DATA_PREM / DATA_URC
arrays. This is the "refresh index.html from the directory" step: it reads the two pack
CSVs in the repo root and replaces the embedded JSON arrays in place.

The CSV->JSON typing is per-cell dynamic (int / float / string; empty cell -> ""), which
reproduces the app's existing embedded arrays byte-for-byte on unchanged data (validated).

Run after updating the pack CSVs (e.g. transfers/build_projections.py):
    python3 transfers/embed_data.py
Std-lib only.
"""

import csv, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
PACKS = {"DATA_PREM": "PREM 25_26 Data Pack - SEASON TOTALS (17).csv",
         "DATA_URC":  "URC 25_26 Data Pack - SEASON TOTALS (17).csv"}


def conv(s):
    if s is None or s == "":
        return ""
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    try:
        return float(s)
    except ValueError:
        return s


def load(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [{k: conv(v) for k, v in row.items()} for row in csv.DictReader(f)]


def replace_array(html, varname, arr_json):
    marker = f"const {varname} = ["
    i = html.find(marker)
    if i < 0:
        raise SystemExit(f"Could not find `{marker}`")
    start = html.find("[", i)
    depth = 0
    for k in range(start, len(html)):
        if html[k] == "[":
            depth += 1
        elif html[k] == "]":
            depth -= 1
            if depth == 0:
                return html[:start] + arr_json + html[k + 1:]
    raise SystemExit(f"Unbalanced brackets for {varname}")


def main():
    html = INDEX.read_text(encoding="utf-8")
    for var, name in PACKS.items():
        rows = load(ROOT / name)
        blob = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
        html = replace_array(html, var, blob)
        active = sum(1 for r in rows if str(r.get("PROJ RANK", "")).strip() != "")
        print(f"{var}: embedded {len(rows)} rows ({active} with a projection)")
    INDEX.write_text(html, encoding="utf-8")
    print("index.html DATA arrays refreshed.")


if __name__ == "__main__":
    main()

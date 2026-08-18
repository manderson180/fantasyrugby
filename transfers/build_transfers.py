#!/usr/bin/env python3
"""
build_transfers.py — turn the offseason squads sheet into a transfer-comment layer.

What it does (mirrors injury/build_injury.py so the two layers stay consistent):
  1. Reads the live game data (DATA_URC / DATA_PREM) straight out of ../index.html,
     so the join always runs against exactly what the app is shipping.
  2. Reads ../"25-26 Squads - Copy of 26-27 Squads (1).csv" and, for every player
     whose change_type is move / departed / retired, builds a short comment:
        move     -> "Moved to {team_2627}"
        departed -> "Left the club ({notes})"
        retired  -> "Retired"
     (new / stay / anything else -> no comment.)
  3. Matches each of those players to an app player. The squads sheet's own `team`
     column is NOT reliable (it reflects the 26-27 snapshot, e.g. Ben Healy reads
     "Edinburgh Rugby" there but "Newcastle Red Bull" in last season's data), so the
     match is: exact team+name first, then a GLOBALLY-UNIQUE name fallback. Names that
     are ambiguous, or players with no row in the season data at all (fringe/academy),
     are left unmatched and listed in the report.
  4. Emits a compact TRANSFER_DATA object keyed `LEAGUE|TEAM|PLAYER` (the app row's own
     team, so the runtime attach lines up) and injects it into ../index.html between
     /* TRANSFER_DATA:START */ ... /* TRANSFER_DATA:END */ markers (idempotent).
  5. Writes transfers/join_report.txt so every run is auditable.

Re-run after dropping in a new squads sheet with:
    python3 transfers/build_transfers.py

Only the standard library is used.
"""

import csv
import datetime as dt
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
INDEX_HTML = HERE.parent / "index.html"
SQUADS_CSV = HERE.parent / "25-26 Squads - Copy of 26-27 Squads (1).csv"
REPORT_PATH = HERE / "join_report.txt"

# Squads-sheet team name -> app team name. Empty for now: the sheet's team strings
# already match the app's TEAM strings for every exact match. Kept for parity with the
# injury build so a future sheet with different spellings has an obvious place to land.
TEAM_ALIASES = {}

# Squads player name -> app player name. Add curated nickname/formal-name pairs here
# when join_report.txt shows an unmatched row that is really a naming variant.
PLAYER_ALIASES = {}

# change_type -> the comment template. Only these three produce a comment.
ACTIONABLE = {"move", "departed", "retired"}


def norm_name(s: str) -> str:
    """Uppercase, strip diacritics/punctuation, collapse whitespace — for matching.
    (Identical to the injury build so both layers join the same way.)"""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.upper().replace("'", " ").replace("-", " ").replace(".", " ")
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def clean_departed_notes(notes: str) -> str:
    """The `notes` on a departed row is normally a clean destination ("To Toulon") or
    "Released — destination TBC". A handful instead carry the curator's data-cleaning
    prose ("Duplicate resolved: … departed to La Rochelle (France). Dropped …"). Those
    would leak internal text into the UI, so pull the real destination back out and
    reformat it to the same "To X" style as the clean rows."""
    notes = (notes or "").strip()
    if notes.lower().startswith("duplicate resolved"):
        m = re.search(r"departed to ([^.;(]+)", notes, re.I)
        if m:
            return "To " + m.group(1).strip()
        if re.search(r"released", notes, re.I):
            return "Released — destination TBC"
        return "destination TBC"
    return notes


def build_comment(change_type: str, rec: dict):
    """Return the display comment for an actionable row, or None to skip."""
    if change_type == "move":
        dest = (rec.get("team_2627") or "").strip()
        return f"Moved to {dest}" if dest else "Moved to another club"
    if change_type == "departed":
        notes = clean_departed_notes(rec.get("notes"))
        return f"Left the club ({notes})" if notes else "Left the club"
    if change_type == "retired":
        return "Retired"
    return None


def extract_array(html: str, varname: str):
    """Locate `const <varname> = [ ... ]` and JSON-parse the bracketed array."""
    marker = f"const {varname} = ["
    i = html.find(marker)
    if i < 0:
        raise SystemExit(f"Could not find `{marker}` in index.html")
    start = html.find("[", i)
    depth = 0
    for k in range(start, len(html)):
        c = html[k]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return json.loads(html[start:k + 1])
    raise SystemExit(f"Unbalanced brackets while parsing {varname}")


def main():
    html = INDEX_HTML.read_text(encoding="utf-8")

    # Build the pool of app players, tagged with their league.
    app_rows = []
    for league, var in (("URC", "DATA_URC"), ("PREM", "DATA_PREM")):
        for row in extract_array(html, var):
            app_rows.append({"league": league, "team": row["TEAM"], "player": row["PLAYER"]})

    by_team_name = {}   # (team, norm_name) -> [app_row, ...]
    by_name = {}        # norm_name -> [app_row, ...]
    for ar in app_rows:
        by_team_name.setdefault((ar["team"], norm_name(ar["player"])), []).append(ar)
        by_name.setdefault(norm_name(ar["player"]), []).append(ar)

    transfer_data = {}
    stats = {"rows": 0, "actionable": 0, "matched": 0, "exact": 0, "name_only": 0,
             "unmatched": 0, "ambiguous": 0}
    by_type = {"move": 0, "departed": 0, "retired": 0}
    unmatched, name_only_list, ambiguous_list = [], [], []

    with SQUADS_CSV.open(encoding="utf-8-sig") as f:
        for rec in csv.DictReader(f):
            stats["rows"] += 1
            change_type = (rec.get("change_type") or "").strip().lower()
            if change_type not in ACTIONABLE:
                continue
            comment = build_comment(change_type, rec)
            if not comment:
                continue
            stats["actionable"] += 1

            name = (rec.get("player") or "").strip()
            csv_name = PLAYER_ALIASES.get(name, name)
            nname = norm_name(csv_name)
            squad_team = (rec.get("team") or "").strip()
            app_team = TEAM_ALIASES.get(squad_team, squad_team)

            # 1) exact team+name.
            matches = by_team_name.get((app_team, nname), [])
            match_kind = "exact"
            # 2) fallback: a globally unique name (covers the sheet's unreliable team column).
            if not matches:
                cand = by_name.get(nname, [])
                uniq = {(c["league"], c["team"], c["player"]) for c in cand}
                if len(uniq) == 1:
                    matches, match_kind = cand, "name_only"
                elif len(uniq) > 1:
                    stats["ambiguous"] += 1
                    ambiguous_list.append(
                        f"{name} [{squad_team}] -> {sorted(t for _, t, _ in uniq)}")

            if not matches:
                stats["unmatched"] += 1
                comp = (rec.get("team_provider") or "").strip()
                unmatched.append(f"{change_type:9} {squad_team:24} {name}")
                continue

            stats["matched"] += 1
            stats[match_kind] += 1
            by_type[change_type] += 1
            if match_kind == "name_only":
                name_only_list.append(
                    f"{name} [{squad_team}]  ->  {matches[0]['player']} [{matches[0]['team']}]")

            entry = {"comment": comment, "type": change_type}
            # de-dupe on the app row; first actionable row for a player wins.
            for ar in matches:
                key = f"{ar['league']}|{ar['team']}|{ar['player']}"
                transfer_data.setdefault(key, entry)

    inject(html, transfer_data)
    write_report(stats, by_type, unmatched, name_only_list, ambiguous_list)

    print(f"TRANSFER_DATA: {len(transfer_data)} entries written to index.html")
    print(f"  actionable rows {stats['actionable']} "
          f"(move {by_type['move']}, departed {by_type['departed']}, retired {by_type['retired']} matched)")
    print(f"  matched {stats['matched']} (exact {stats['exact']}, name-only {stats['name_only']}); "
          f"unmatched {stats['unmatched']}; ambiguous {stats['ambiguous']}")
    print(f"  full audit -> {REPORT_PATH.relative_to(HERE.parent)}")


def inject(html, transfer_data):
    blob = json.dumps(transfer_data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    block = ("/* TRANSFER_DATA:START (generated by transfers/build_transfers.py — do not edit) */\n"
             f"const TRANSFER_DATA = {blob};\n"
             "/* TRANSFER_DATA:END */")
    pattern = re.compile(r"/\* TRANSFER_DATA:START.*?TRANSFER_DATA:END \*/", re.DOTALL)
    if pattern.search(html):
        html = pattern.sub(lambda _m: block, html, count=1)
    else:
        # First run: insert after the INJURY_DATA:END marker if present, else after DATA_PREM.
        lines = html.split("\n")
        for i, line in enumerate(lines):
            if "INJURY_DATA:END" in line:
                lines.insert(i + 1, block)
                break
        else:
            for i, line in enumerate(lines):
                if line.startswith("const DATA_PREM = ["):
                    lines.insert(i + 1, block)
                    break
            else:
                raise SystemExit("Could not find INJURY_DATA:END or the DATA_PREM line to insert after")
        html = "\n".join(lines)
    INDEX_HTML.write_text(html, encoding="utf-8")


def write_report(stats, by_type, unmatched, name_only_list, ambiguous_list):
    lines = [
        f"Transfer join report — {dt.datetime.now().isoformat(timespec='seconds')}",
        "=" * 60,
        f"Squads rows processed     : {stats['rows']}",
        f"Actionable (move/dep/ret) : {stats['actionable']}",
        f"Matched to an app player  : {stats['matched']} "
        f"(exact {stats['exact']}, name-only {stats['name_only']})",
        f"  by type (matched)       : move {by_type['move']}, "
        f"departed {by_type['departed']}, retired {by_type['retired']}",
        f"Unmatched (no app row)    : {stats['unmatched']}",
        f"Ambiguous name (skipped)  : {stats['ambiguous']}",
        "",
        "── Name-only matches, team differed in the sheet (verify these) ──",
        *(sorted(name_only_list) or ["(none)"]),
        "",
        "── Ambiguous names (>1 app player, left unmatched) ──",
        *(sorted(ambiguous_list) or ["(none)"]),
        "",
        "── Unmatched actionable rows (no season-totals row to annotate) ──",
        *(sorted(unmatched) or ["(none)"]),
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())

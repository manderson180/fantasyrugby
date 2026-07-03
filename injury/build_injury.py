#!/usr/bin/env python3
"""
build_injury.py — turn the researched injury sweep into a live availability layer.

What it does (see injury/methodology.md for the research background):
  1. Reads the live game data (DATA_URC / DATA_PREM) straight out of ../index.html,
     so the join always runs against exactly what the app is shipping.
  2. Matches every player in player_availability.csv to an app player
     (team-alias normalisation + name matching, with a conservative fuzzy fallback).
  3. Resolves stale "doubtful" flags against per-round appearance data: if a flagged
     player scored in any round dated AFTER their injury date, they are downgraded to
     a confirmed "Healthy" (methodology section 5).
  4. Emits a compact INJURY_DATA object and injects it into ../index.html between
     /* INJURY_DATA:START */ ... /* INJURY_DATA:END */ markers (idempotent).
  5. Writes injury/join_report.txt so every run is auditable.

Re-run after refreshing player_availability.csv (or round_dates.json) with:
    python3 injury/build_injury.py

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
CSV_PATH = HERE / "player_availability.csv"
ROUND_DATES_PATH = HERE / "round_dates.json"
REPORT_PATH = HERE / "join_report.txt"

ROUNDS = [f"R{i}" for i in range(1, 19)]

# Injury-sweep team name -> app team name. Only the ones that differ are listed;
# everything else already matches the app's TEAM strings exactly.
TEAM_ALIASES = {
    "Bath": "Bath Rugby",
    "Connacht": "Connacht Rugby",
    "Emirates Lions": "Lions",
    "Gloucester": "Gloucester Rugby",
    "Leinster": "Leinster Rugby",
    "Munster": "Munster Rugby",
    "Newcastle Red Bulls": "Newcastle Red Bull",
    "Ulster": "Ulster Rugby",
}

# Injury-sweep player name -> app player name. Curated nickname/formal-name pairs that
# can't be matched safely by string similarity alone (a loose surname+initial guess would
# also wrongly merge distinct players, e.g. Callum vs Connor Hancock). Add to this list
# when join_report.txt shows an unmatched row that is really a naming variant.
PLAYER_ALIASES = {
    "Oli Spencer": "Oliver Spencer",
    "Rob du Preez": "Robert du Preez",
    "Paddy Harrison": "Patrick Harrison",
    "Tom Dyer": "Thomas Dyer",
}

# user_status -> (severity, show-in-grid?)
# Severity drives colour in the UI; grid icons (keyed off status) show for actionable statuses.
STATUS_META = {
    "Injured":                      ("out",      True),
    "Suspended":                    ("out",      True),
    "Retired (Medical)":            ("out",      True),
    "Unavailable (Other)":          ("out",      True),
    "Potential Injury":             ("doubtful", True),
    "International Duty":            ("away",     True),
    "Unclear":                      ("doubtful", False),
    "Likely Healthy (Unconfirmed)": ("likely",   False),
    "Healthy":                      ("ok",       False),
}

# internal_status / presumption combos whose "doubt" a later appearance can clear.
RESOLVABLE_INTERNAL = {"injured", "unknown_potentially_injured"}


# ── helpers ────────────────────────────────────────────────────────────────
def norm_name(s: str) -> str:
    """Uppercase, strip diacritics/punctuation, collapse whitespace — for matching."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.upper().replace("'", " ").replace("-", " ").replace(".", " ")
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_date(s: str):
    s = (s or "").strip()
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
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


# ── main ───────────────────────────────────────────────────────────────────
def main():
    html = INDEX_HTML.read_text(encoding="utf-8")
    round_dates = json.loads(ROUND_DATES_PATH.read_text(encoding="utf-8"))

    # Build the pool of app players, tagged with their league.
    app_rows = []
    for league, var in (("URC", "DATA_URC"), ("PREM", "DATA_PREM")):
        for row in extract_array(html, var):
            app_rows.append({"league": league, "team": row["TEAM"],
                             "player": row["PLAYER"], "row": row})

    # Lookup indexes.
    by_team_name = {}   # (team, norm_name) -> [app_row, ...]
    by_name = {}        # norm_name -> [app_row, ...] (all leagues)
    for ar in app_rows:
        by_team_name.setdefault((ar["team"], norm_name(ar["player"])), []).append(ar)
        by_name.setdefault(norm_name(ar["player"]), []).append(ar)

    injury_data = {}
    stats = {"rows": 0, "matched": 0, "exact": 0, "name_only": 0, "aliased": 0,
             "unmatched": 0, "resolved": 0}
    unmatched, resolved_list, name_only_list, alias_list = [], [], [], []

    with CSV_PATH.open(encoding="utf-8") as f:
        for rec in csv.DictReader(f):
            name = (rec.get("player_name") or "").strip()
            internal = (rec.get("internal_status") or "").strip()
            if not name or internal in ("coverage_gap", "review_item"):
                continue
            stats["rows"] += 1

            comp = (rec.get("competition") or "").strip().upper()
            leagues = {comp} if comp in ("URC", "PREM") else {"URC", "PREM"}  # BOTH -> either
            app_team = TEAM_ALIASES.get(rec["team"].strip(), rec["team"].strip())
            csv_name = PLAYER_ALIASES.get(name, name)
            aliased = csv_name != name
            nname = norm_name(csv_name)

            # 1) exact team+name within the candidate league(s).
            matches = [a for a in by_team_name.get((app_team, nname), [])
                       if a["league"] in leagues]
            match_kind = "exact"
            # 2) fallback: a GLOBALLY UNIQUE name (covers transfers where the sweep lists a
            #    player under a different club/league than last season's app data). Requires
            #    exactly one app player with that name; ambiguous names are left unmatched.
            if not matches:
                cand = by_name.get(nname, [])
                if len({(c["league"], c["team"], c["player"]) for c in cand}) == 1:
                    matches, match_kind = cand, "name_only"

            if not matches:
                stats["unmatched"] += 1
                unmatched.append(f"{rec['competition']:4} {rec['team']:22} {name}")
                continue

            stats["matched"] += 1
            stats[match_kind] += 1
            if aliased:
                stats["aliased"] += 1
                alias_list.append(f"{name}  ->  {matches[0]['player']} ({matches[0]['team']})")
            if match_kind == "name_only":
                name_only_list.append(
                    f"{name} [{rec['team']}]  ->  {matches[0]['player']} [{matches[0]['team']}]")

            ref_date = parse_date(rec.get("injury_date")) or parse_date(rec.get("last_verified"))
            qualifies = (rec.get("presumption_rule_applied") == "yes"
                         or internal in RESOLVABLE_INTERNAL)

            for ar in matches:
                entry = build_entry(rec, ar, ref_date, qualifies, round_dates)
                if entry.get("resolved"):
                    stats["resolved"] += 1
                    resolved_list.append(
                        f"{ar['player']} ({ar['team']}): "
                        f"{entry['resolved']['original_status']} -> Healthy "
                        f"(played {entry['resolved']['via_round']} {entry['resolved']['via_date']})")
                key = f"{ar['league']}|{ar['team']}|{ar['player']}"
                injury_data[key] = entry

    inject(html, injury_data)
    write_report(stats, unmatched, resolved_list, name_only_list, alias_list)
    print(f"INJURY_DATA: {len(injury_data)} entries written to index.html")
    print(f"  matched {stats['matched']}/{stats['rows']} "
          f"(exact {stats['exact']}, name-only {stats['name_only']}, "
          f"of which aliased {stats['aliased']}); "
          f"resolved-to-Healthy {stats['resolved']}; unmatched {stats['unmatched']}")
    print(f"  full audit -> {REPORT_PATH.relative_to(HERE.parent)}")


def build_entry(rec, ar, ref_date, qualifies, round_dates):
    league = ar["league"]
    status = (rec.get("user_status") or "").strip() or "Unclear"
    notes = (rec.get("user_notes") or "").strip()
    resolved = None

    if qualifies and ref_date:
        rd = round_dates.get(league, {})
        played_after = []
        for r in ROUNDS:
            d = parse_date(rd.get(r))
            try:
                score = float(ar["row"].get(r) or 0)
            except (TypeError, ValueError):
                score = 0.0
            if d and d > ref_date and score != 0:
                played_after.append((r, d))
        if played_after:
            via_round, via_date = played_after[-1]  # latest appearance
            resolved = {"via_round": via_round, "via_date": via_date.isoformat(),
                        "original_status": status}
            notes = (f"Confirmed fit — appeared for {ar['team']} in {via_round} "
                     f"({via_date.isoformat()}). Earlier note: {notes}")
            status = "Healthy"

    severity, grid = STATUS_META.get(status, ("doubtful", False))
    entry = {
        "status": status,
        "severity": severity,
        "grid": grid,
        "notes": notes,
        "injury_type": (rec.get("injury_type") or "").strip(),
        "body_part": (rec.get("body_part") or "").strip(),
        "expected_return": (rec.get("expected_return") or "").strip(),
        "injury_date": (rec.get("injury_date") or "").strip(),
        "last_verified": (rec.get("last_verified") or "").strip(),
        "confidence": (rec.get("confidence") or "").strip(),
        "source_name": (rec.get("source_name") or "").strip(),
        "source_url": (rec.get("source_url") or "").strip(),
        "source_date": (rec.get("source_date") or "").strip(),
        "internal_status": (rec.get("internal_status") or "").strip(),
        "presumption_rule_applied": (rec.get("presumption_rule_applied") or "").strip(),
    }
    if resolved:
        entry["resolved"] = resolved
    return entry


def inject(html, injury_data):
    blob = json.dumps(injury_data, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))
    block = ("/* INJURY_DATA:START (generated by injury/build_injury.py — do not edit) */\n"
             f"const INJURY_DATA = {blob};\n"
             "/* INJURY_DATA:END */")
    pattern = re.compile(
        r"/\* INJURY_DATA:START.*?INJURY_DATA:END \*/", re.DOTALL)
    if pattern.search(html):
        html = pattern.sub(lambda _m: block, html, count=1)
    else:
        # First run: insert the block on its own line right after the DATA_PREM line.
        lines = html.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("const DATA_PREM = ["):
                lines.insert(i + 1, block)
                break
        else:
            raise SystemExit("Could not find the DATA_PREM line to insert after")
        html = "\n".join(lines)
    INDEX_HTML.write_text(html, encoding="utf-8")


def write_report(stats, unmatched, resolved_list, name_only_list, alias_list):
    lines = [
        f"Injury join report — {dt.datetime.now().isoformat(timespec='seconds')}",
        "=" * 60,
        f"CSV player rows processed : {stats['rows']}",
        f"Matched to an app player  : {stats['matched']} "
        f"(exact {stats['exact']}, name-only {stats['name_only']}, of which aliased {stats['aliased']})",
        f"Resolved to Healthy       : {stats['resolved']} (played after injury date)",
        f"Unmatched (no app player) : {stats['unmatched']}",
        "",
        "── Resolved to Healthy via appearance ──",
        *(resolved_list or ["(none)"]),
        "",
        "── Name aliases applied (curated PLAYER_ALIASES) ──",
        *(alias_list or ["(none)"]),
        "",
        "── Name-only matches, team differed (verify these) ──",
        *(name_only_list or ["(none)"]),
        "",
        "── Unmatched injury rows (kept in CSV, no display entry) ──",
        *(unmatched or ["(none)"]),
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
build_international_squads.py — the international-duty half of the injury scan.

Encodes the researched squads for the CURRENTLY OPEN international window as data and writes
injury/international_squads.csv. build_injury.py then folds these in as "International Duty" for any
of our URC/PREM players named in a squad (a club injury/suspension always takes precedence).

IMPORTANT — only encode windows that are open *now*. The overlay tells users a player is away, so a
squad from a window that has closed (or not yet opened) is a stale source and shows wrong icons.
When a window closes, move its squads to injury/archive/ and replace them (or leave SQUADS empty).
The July 2026 Nations Championship squads (England, Scotland, Italy, South Africa, Argentina,
Australia, Fiji) were archived on 2026-09-24 to
    injury/archive/international_squads_2026-07-nations-championship.csv
because that window closed in July.

Windows / dates to check on each sweep (2026 calendar):
  - Nations Championship: 4 Jul - 29 Nov (July window done; the November window opens with
    squad announcements from ~late October — Wallabies v England is 8 Nov, etc.).
  - Rugby's Greatest Rivalry (NZ tour of South Africa): 7 Aug - 12 Sep (done).
  - Australia tour of Argentina: 29 Aug - 5 Sep (done). Pacific Nations Cup: 12 - 19 Sep (done).
  - Wallabies v Springboks, Perth, Sun 27 Sep 2026 (done; squads archived 2026-10-01 to
    injury/archive/international_squads_2026-09-27-perth-test.csv).
  - Next: Nations Championship November window — Italy v South Africa (Turin) 7 Nov, Wallabies v England
    8 Nov, finals weekend 27-29 Nov. Squads expected ~20 Oct; re-check then. SQUADS is empty until then.

To refresh: update SQUADS from the latest squad announcements and re-run:
    python3 injury/build_international_squads.py
    python3 injury/build_injury.py

Scope note: Wales and Ireland are covered in player_availability.csv when relevant.
"""

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent

# nation -> (window, source_name, source_url, source_date, [players])
# Empty: no window open as of the 2026-10-01 sweep (next: Nations Championship November Tests, squads ~20 Oct).
SQUADS = {}


def main():
    rows = []
    for nation, (window, sname, surl, sdate, players) in SQUADS.items():
        for p in players:
            rows.append({"nation": nation, "player_name": p, "window": window,
                         "source_name": sname, "source_url": surl, "source_date": sdate})
    out = HERE / "international_squads.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["nation", "player_name", "window",
                                          "source_name", "source_url", "source_date"])
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} squad rows across {len(SQUADS)} nations -> {out.name}")


if __name__ == "__main__":
    main()

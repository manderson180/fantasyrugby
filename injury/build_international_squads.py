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
  - Wallabies v Springboks, Perth, Sun 27 Sep 2026 (OPEN as of the 2026-09-24 sweep) <- encoded below.

To refresh: update SQUADS from the latest squad announcements and re-run:
    python3 injury/build_international_squads.py
    python3 injury/build_injury.py

Scope note: Wales and Ireland are covered in player_availability.csv when relevant.
"""

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent

# nation -> (window, source_name, source_url, source_date, [players])
SQUADS = {
    "South Africa": (
        "the Springboks' Test against Australia in Perth (Sun 27 Sep 2026)",
        "Springboks matchday 23 for the Perth Test (Rugby Australia 22 Sep 2026; names cross-checked against "
        "Planet Rugby / 2oceansvibe / RugbyPass team reports)",
        "https://www.rugby.com.au/news/springboks-side-wallabies-team-perth-rugby-union-south-africa-2026922",
        "2026-09-22",
        ["Aphelele Fassi", "Edwill van der Merwe", "Canan Moodie", "Andre Esterhuizen", "Ethan Hooker",
         "Handre Pollard", "Herschel Jantjies", "Marco van Staden", "Elrigh Louw", "Paul de Villiers",
         "Franco Mostert", "Eben Etzebeth", "Zachary Porthen", "Johan Grobbelaar", "Jan-Hendrik Wessels",
         "Malcolm Marx", "Ox Nche", "Wilco Louw", "Lood de Jager", "Jasper Wiese", "Morne van den Berg",
         "Sacha Feinberg-Mngomezulu", "Quan Horn"],
    ),
    "Australia": (
        "the Wallabies' Test against South Africa in Perth (Sun 27 Sep 2026)",
        "Australia (Wallabies) 34-man squad for the Perth Test (ABC News, 14 Sep 2026)",
        "https://www.abc.net.au/news/2026-09-14/jordan-petaia-returns-to-wallabies-squad-springboks/107151810",
        "2026-09-14",
        ["Allan Alaalatoa", "Angus Bell", "Charlie Cale", "Josh Canham", "Tom Hooper", "Isaac Kailea",
         "Fraser McReight", "Josh Nasser", "Zane Nonggorr", "Brandon Paenga-Amosa", "Billy Pollard",
         "Aidan Ross", "Lukhan Salakaia-Loto", "Lachlan Shaw", "Carlo Tizzano", "Taniela Tupou",
         "Rob Valetini", "Jeremy Williams", "Harry Wilson", "Jock Campbell", "Ben Donaldson", "Isaac Henry",
         "Len Ikitau", "Max Jorgensen", "Ryan Lonergan", "Tate McDermott", "Harry McLaughlin-Phillips",
         "Declan Meredith", "Hunter Paisami", "Jordan Petaia", "Harry Potter", "Joseph-Aukuso Suaalii",
         "Kalani Thomas", "Tom Wright"],
    ),
}


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

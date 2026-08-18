#!/usr/bin/env python3
"""
build_projections.py — apply offseason-transfer logic to the projection columns of the
raw PREM/URC data packs. Touches ONLY projection columns on existing rows (plus adds
projection-only rows); every other raw stat is left exactly as-is.

Rules (see the session that produced this / transfers/new_player_ratings.csv):
  1. Cross-league mover (URC<->PREM): blank their projection in the OLD league; add a
     projection-only row in the NEW league with PROJ_PPG rescaled by the position-specific
     league factor (median PROJ_PPG[new,pos] / median[old,pos]).
  2. Departed / retired (left the leagues): blank their projection in their league.
  3. Same-league mover: no projection change.
  4. New player (transfers/new_player_ratings.csv): add a projection-only row in the
     destination league; PROJ_PPG = the value at quality_pctl within that position+league.

Then, per league: PROJ_TOTAL = PROJ_PPG*EXPECTED_GMS; PROJ RANK / POS RANK / PERCENTILE
recomputed over the active pool; PROJ_TIER assigned to affected players only (fitted
position-percentile cutoffs) — every unaffected player keeps the sheet's tier.

Re-runnable: originals are backed up once to transfers/orig/ and always used as the source,
so editing new_player_ratings.csv and re-running is safe.  Std-lib only.
"""

import csv, re, shutil, unicodedata, datetime as dt
from pathlib import Path
from collections import defaultdict

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PACKS = {"PREM": "PREM 25_26 Data Pack - SEASON TOTALS (17).csv",
         "URC":  "URC 25_26 Data Pack - SEASON TOTALS (17).csv"}
SQUADS = ROOT / "25-26 Squads - Copy of 26-27 Squads (1).csv"
RATINGS = HERE / "new_player_ratings.csv"
ORIG_DIR = HERE / "orig"
REPORT = HERE / "projections_report.txt"

# Only these columns are ever written on an existing row. PERCENTILE (last-season) and
# CONSISTENCY_LABEL (last-season variance) are deliberately NOT touched.
PROJ_COLS = ["PROJ_PPG", "EXPECTED_GMS", "PROJ_TOTAL_EXPECTED_GMS",
             "PROJ_TIER", "PROJ RANK", "PROJ POS RANK", "PROJ PERCENTILE"]

POS_STD = {"lock": "Lock", "loose-forward": "Loose Forward", "outside-back": "Outside Back",
           "prop": "Prop", "centre": "Centre", "fly-half": "Fly Half",
           "scrum-half": "Scrum Half", "hooker": "Hooker"}


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.upper().replace("'", " ").replace("-", " ").replace(".", " ")
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def fmt(x):
    """Match the sheet's minimal number style (24.4 not 24.40)."""
    r = round(float(x), 2)
    return str(int(r)) if r == int(r) else str(r)


def load(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        return r.fieldnames, list(r)


def backup_originals():
    ORIG_DIR.mkdir(exist_ok=True)
    for lg, name in PACKS.items():
        dst = ORIG_DIR / name
        if not dst.exists():
            shutil.copy2(ROOT / name, dst)
    return {lg: load(ORIG_DIR / name) for lg, name in PACKS.items()}


def pctl_value(sorted_vals, pctl):
    """Linear-interpolated value at percentile pctl (0-100) over an ascending list."""
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = (pctl / 100.0) * (len(sorted_vals) - 1)
    lo = int(pos); hi = min(lo + 1, len(sorted_vals) - 1)
    frac = pos - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def median(vals):
    v = sorted(vals)
    n = len(v)
    if n == 0:
        return None
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


def main():
    # Pristine source (backed up once) drives every computation.
    if not (ORIG_DIR / PACKS["PREM"]).exists():
        print("First run: backing up original packs to transfers/orig/")
    orig = backup_originals()
    fieldnames = {lg: orig[lg][0] for lg in PACKS}
    # Working copies of every row (dicts) from the pristine originals.
    rows = {lg: [dict(r) for r in orig[lg][1]] for lg in PACKS}

    team_league = {r["TEAM"].strip(): lg for lg in PACKS for r in rows[lg]}

    # POS -> abbreviation, learned from existing PROJ POS RANK values (e.g. "OB #1").
    pos_abbr = {}
    for lg in PACKS:
        for r in rows[lg]:
            m = re.match(r"\s*([A-Z0-9]+)\s*#", r.get("PROJ POS RANK", "") or "")
            if m and r["POS"] not in pos_abbr:
                pos_abbr[r["POS"]] = m.group(1)

    # Reference distributions from ORIGINAL data.
    orig_ppg = {lg: defaultdict(list) for lg in PACKS}      # (lg)[pos] -> [ppg,...] all
    reg_ppg = {lg: defaultdict(list) for lg in PACKS}       # regulars (EXPECTED_GMS>=5)
    for lg in PACKS:
        for r in rows[lg]:
            p = num(r["PROJ_PPG"])
            if p is None:
                continue
            orig_ppg[lg][r["POS"]].append(p)
            if (num(r["EXPECTED_GMS"]) or 0) >= 5:
                reg_ppg[lg][r["POS"]].append(p)
    for lg in PACKS:
        for pos in orig_ppg[lg]:
            orig_ppg[lg][pos].sort()

    def factor(pos, from_lg, to_lg):
        a, b = median(reg_ppg[from_lg].get(pos, [])), median(reg_ppg[to_lg].get(pos, []))
        return (b / a) if a and b else 1.0

    # Fitted tier cutoffs (position-percentile) per league, calibrated to reproduce counts.
    tier_cut = {}
    TIERS = ["Elite", "Premium", "Good", "Squad", "Fringe"]
    for lg in PACKS:
        bypos = defaultdict(list)
        for r in rows[lg]:
            if num(r["PROJ_TOTAL_EXPECTED_GMS"]) is not None:
                bypos[r["POS"]].append(r)
        recs = []
        for pos, pr in bypos.items():
            s = sorted(pr, key=lambda r: -num(r["PROJ_TOTAL_EXPECTED_GMS"])); n = len(s)
            for i, r in enumerate(s):
                recs.append((100 * (n - i - 0.5) / n, (r.get("PROJ_TIER") or "").strip()))
        from collections import Counter
        cnt = Counter(t for _, t in recs if t)
        recs.sort(key=lambda x: -x[0])
        cum = 0; cut = {}
        for t in TIERS[:-1]:
            cum += cnt[t]
            cut[t] = recs[min(cum, len(recs) - 1)][0]
        tier_cut[lg] = cut

    def tier_for(pctl_pos, lg):
        c = tier_cut[lg]
        if pctl_pos >= c["Elite"]:   return "Elite"
        if pctl_pos >= c["Premium"]: return "Premium"
        if pctl_pos >= c["Good"]:    return "Good"
        if pctl_pos >= c["Squad"]:   return "Squad"
        return "Fringe"

    # --- Classify existing players via the squads sheet (matched by unique name) ---
    squad = {}
    for r in load(SQUADS)[1]:
        ct = (r.get("change_type") or "").strip().lower()
        if ct in ("move", "departed", "retired"):
            squad[norm(r["player"])] = {"ct": ct, "dest_team": (r.get("team_2627") or "").strip()}

    report = {"removed": defaultdict(list), "moved_out": [], "new": [], "skipped_move_norow": []}
    pending_new = {"PREM": [], "URC": []}   # rows to append per league

    for lg in PACKS:
        for r in rows[lg]:
            info = squad.get(norm(r["PLAYER"]))
            if not info:
                continue
            ct = info["ct"]
            if ct in ("departed", "retired"):
                report["removed"][ct].append(f"{lg} {r['TEAM']} {r['PLAYER']}")
                for c in PROJ_COLS:
                    r[c] = ""
            elif ct == "move":
                dest_lg = team_league.get(info["dest_team"])
                if dest_lg and dest_lg != lg:
                    old_ppg, old_gms = num(r["PROJ_PPG"]), num(r["EXPECTED_GMS"])
                    for c in PROJ_COLS:
                        r[c] = ""
                    if old_ppg is None or old_gms is None:
                        report["skipped_move_norow"].append(f"{r['PLAYER']} (no old projection)")
                        continue
                    f = factor(r["POS"], lg, dest_lg)
                    new_ppg = old_ppg * f
                    pending_new[dest_lg].append({
                        "PLAYER": r["PLAYER"], "TEAM": info["dest_team"], "POS": r["POS"],
                        "PROJ_PPG": new_ppg, "EXPECTED_GMS": old_gms})
                    report["moved_out"].append(
                        f"{r['PLAYER']:24} {lg}->{dest_lg} {r['POS']:13} "
                        f"PPG {fmt(old_ppg)}->{fmt(new_ppg)} (x{f:.3f})")
                # same-league move -> untouched

    # --- New players from the ratings file ---
    for r in load(RATINGS)[1]:
        lg = r["dest_league"].strip()
        pos = POS_STD.get(r["position"].strip(), r["position"].strip())
        pctl = num(r["quality_pctl"]) or 40
        gms = num(r["exp_gms"]) or 6
        ppg = pctl_value(orig_ppg[lg].get(pos, []), pctl)
        # PLAYER is stored UPPERCASE in the packs — match that so new names render consistently.
        pending_new[lg].append({"PLAYER": r["player"].strip().upper(), "TEAM": r["dest_team"].strip(),
                                 "POS": pos, "PROJ_PPG": ppg, "EXPECTED_GMS": gms})
        report["new"].append(f"{lg} {r['dest_team']:20} {pos:13} {r['player']:24} "
                             f"pctl{int(pctl)} gms{int(gms)} -> PPG {fmt(ppg)}")

    # --- Materialise appended rows (projection-only: all other cells blank) ---
    affected_ids = {lg: set() for lg in PACKS}   # id() of appended rows -> assign tier later
    for lg in PACKS:
        for nr in pending_new[lg]:
            row = {k: "" for k in fieldnames[lg]}
            row["PLAYER"] = nr["PLAYER"]; row["TEAM"] = nr["TEAM"]; row["POS"] = nr["POS"]
            row["PROJ_PPG"] = fmt(nr["PROJ_PPG"])
            row["EXPECTED_GMS"] = fmt(nr["EXPECTED_GMS"])
            row["PROJ_TOTAL_EXPECTED_GMS"] = fmt(nr["PROJ_PPG"] * nr["EXPECTED_GMS"])
            rows[lg].append(row)
            affected_ids[lg].add(id(row))

    # --- Recompute PROJ RANK / POS RANK / PERCENTILE league-wide over the active pool ---
    for lg in PACKS:
        active = [r for r in rows[lg] if num(r["PROJ_TOTAL_EXPECTED_GMS"]) is not None]
        active.sort(key=lambda r: -num(r["PROJ_TOTAL_EXPECTED_GMS"]))
        N = len(active)
        for i, r in enumerate(active):
            r["PROJ RANK"] = str(i + 1)
            r["PROJ PERCENTILE"] = str(round(100 * (N - (i + 1)) / (N - 1)) if N > 1 else 100)
        bypos = defaultdict(list)
        for r in active:
            bypos[r["POS"]].append(r)
        for pos, pr in bypos.items():
            pr.sort(key=lambda r: -num(r["PROJ_TOTAL_EXPECTED_GMS"]))
            M = len(pr); ab = pos_abbr.get(pos, "".join(w[0] for w in pos.split())[:2].upper())
            for k, r in enumerate(pr):
                r["PROJ POS RANK"] = f"{ab} #{k + 1}"
            # Tier only for affected (new/moved) rows; others keep the sheet's tier.
            # Assign each affected player the tier of the nearest EXISTING player in the
            # same position (by PROJ_TOTAL) — faithful to the sheet's real tier bands and
            # guaranteed consistent with the players ranked around them. Cutoff rule is a
            # fallback for positions with no existing tiered players.
            existing = [r for r in pr if id(r) not in affected_ids[lg]
                        and (r.get("PROJ_TIER") or "").strip()]
            for k, r in enumerate(pr):
                if id(r) not in affected_ids[lg]:
                    continue
                t = num(r["PROJ_TOTAL_EXPECTED_GMS"])
                if existing:
                    r["PROJ_TIER"] = min(
                        existing, key=lambda e: abs(num(e["PROJ_TOTAL_EXPECTED_GMS"]) - t)
                    )["PROJ_TIER"]
                else:
                    r["PROJ_TIER"] = tier_for(100 * (M - k - 0.5) / M, lg)

    # --- Write packs back (original column order; original rows in place + appended) ---
    for lg, name in PACKS.items():
        with open(ROOT / name, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames[lg])
            w.writeheader()
            w.writerows(rows[lg])

    write_report(report, tier_cut, rows)
    print("PROJECTIONS updated:")
    print(f"  removed from projections : departed {len(report['removed']['departed'])}, "
          f"retired {len(report['removed']['retired'])}")
    print(f"  cross-league moved+rescaled: {len(report['moved_out'])}")
    print(f"  new players added        : {len(report['new'])} "
          f"(PREM {sum(1 for x in report['new'] if x.startswith('PREM'))}, "
          f"URC {sum(1 for x in report['new'] if x.startswith('URC'))})")
    for lg in PACKS:
        act = sum(1 for r in rows[lg] if num(r["PROJ_TOTAL_EXPECTED_GMS"]) is not None)
        print(f"  {lg}: {len(rows[lg])} rows, {act} with a projection")
    print(f"  audit -> {REPORT.relative_to(ROOT)}")


def write_report(report, tier_cut, rows):
    L = [f"Projections transfer refresh — {dt.datetime.now().isoformat(timespec='seconds')}",
         "=" * 64,
         f"Tier cutoffs (position-percentile): {tier_cut}", "",
         f"── Cross-league movers rescaled ({len(report['moved_out'])}) ──",
         *(sorted(report["moved_out"]) or ["(none)"]), "",
         f"── New players added ({len(report['new'])}) ──",
         *(sorted(report["new"]) or ["(none)"]), "",
         f"── Removed from projections: departed ({len(report['removed']['departed'])}) ──",
         *(sorted(report["removed"]["departed"]) or ["(none)"]), "",
         f"── Removed from projections: retired ({len(report['removed']['retired'])}) ──",
         *(sorted(report["removed"]["retired"]) or ["(none)"]), "",
         f"── Cross-league move skipped, no prior projection ({len(report['skipped_move_norow'])}) ──",
         *(sorted(report["skipped_move_norow"]) or ["(none)"]), ""]
    REPORT.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()

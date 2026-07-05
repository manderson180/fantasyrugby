# Injury/Availability Research Playbook

A step-by-step recipe for re-running the manual research sweep that produced
`player_availability.csv` and `international_squads.csv`. This is the procedure
that was actually followed the first time (see `methodology.md` for the
retrospective write-up); this file is the forward-looking script for doing it
again consistently. It's designed to be handed to an agent (or followed by
hand) with minimal ambiguity.

**When to run:** pre-season, mid-season, and around any transfer/squad-naming
deadline. Not more than weekly — see "Cost" below.

## 0. Before you start

1. Read the previous `player_availability.csv` and `international_squads.csv` in full.
2. Read `join_report.txt` from the last `build_injury.py` run to see which
   rows are unmatched/stale.
3. Treat the previous sweep as the baseline. This run's job is to **update
   it**, not replace it from scratch — see §5 (carry-forward rule).

## 1. Per-club research loop

For each of the 26 clubs (10 PREM, 16 URC), run this loop. Use
`club_injury_sources.csv` (built by `build_sources.py`) to check which
outlets are the good ones for that club before searching blind — e.g.
Saracens/Leicester/Sale publish structured official updates; Harlequins/
Zebre/Dragons don't, so lean on beat journalists (WalesOnline, RugbyPass, etc).

1. Search: `"<club name> injury news <month> <year>"` and `"<club> squad update"`.
2. Also check, once per sweep (not per club):
   - The most recent RugbyPass/Planet Rugby "injury list roundup" article, if
     one exists for this window — these aggregate many clubs at once and are
     the highest-value single source when available.
   - National union sites (IRFU, WRU, SRU, RFU, FIR, SA Rugby) for squad
     announcements — these double as both injury evidence (player X ruled out)
     and international-duty evidence (player Y named, therefore fit).
   - **Squad withdrawals/replacements for the current international window** —
     search `"<nation> squad withdrawal"` / `"<nation> injury replacement"` in
     addition to the original selection announcement. Federations reliably
     issue a follow-up release when a player withdraws mid-window (they have
     to, in order to name the replacement), so this is a real, findable
     source — not a guess. This is how a player who was correctly flagged
     International Duty gets caught if they're later injured *while away*
     (see §1a below) — skipping this search is the most likely way such a
     case gets missed entirely.
   - Disciplinary pages (URC Disciplinary Press Releases, RFU disciplinary
     decisions, EPCR judicial notices) for suspensions — these are the most
     standardized source in the sport, always check them.
3. Read the highest-value 2-5 results per club (official club news > beat
   journalist with a named byline > aggregator/syndication).
4. For every fact that will go in the CSV, keep the source name, exact date,
   and URL. **Never write a row without a traceable source.**

## 1a. Players injured while on international duty

A player can be selected for their country (so `international_squads.csv` is
correct to list them) and *then* pick up an injury during that window —
Eben Etzebeth and Siya Kolisi both withdrew from South Africa's Nations
Championship squad shortly before a Test due to injury (July 2026) despite
having been legitimately named in the squad weeks earlier.

**Don't build a separate "concurrent status" field for this.** `build_injury.py`
already resolves club-sourced injury status ahead of international-duty status
(§204-223 of that script: an international-duty row from `international_squads.csv`
only overwrites a player whose existing status is blank/Healthy/Likely-Healthy —
a real injury already on file always wins). So the correct fix is purely a
research-process one:

- When a squad-withdrawal-due-to-injury is found (via the §1 search above),
  write/update a normal row in **`player_availability.csv`** (not
  `international_squads.csv`) with `internal_status = injured` (or
  `unknown_potentially_injured` if details are vague) — do not invent an
  "international_duty_injured" status.
- Use the federation's own withdrawal announcement as the source — these
  usually name the injury and the replacement call-up in the same release.
- Put the international context in `user_notes`/`internal_notes` as narrative
  (e.g. "withdrew from the Springboks' Nations Championship squad before the
  first Test due to a hip injury"), not as a separate tag.
- This row then automatically inherits all the normal ongoing-monitoring
  machinery — the staleness rule and the match-appearance auto-resolve
  (§5/methodology.md §5) — with zero extra code. Once the player appears in
  a subsequent match for anyone, they'll resolve to Healthy the same way any
  other injury does.

## 2. Schema (must match exactly — `build_injury.py` depends on these columns)

`player_availability.csv` columns, in order:

```
competition, team, player_name, user_status, user_notes, expected_return,
injury_date, injury_type, body_part, confidence, last_verified,
internal_status, presumption_rule_applied, source_name, source_date,
source_url, internal_notes
```

**All three date columns (`injury_date`, `last_verified`, `source_date`) must be
ISO format (`YYYY-MM-DD`), never `DD/MM/YYYY` or any other format.**
`build_injury.py`'s `parse_date()` (line 97) calls `dt.date.fromisoformat()`
directly with no fallback — a non-ISO date doesn't raise a visible error, it
just silently returns `None`. That quietly disables the match-appearance
auto-resolve (§5) for every affected row, with no warning in `join_report.txt`
to flag it. This has actually happened once already (the whole CSV got
reformatted to `DD/MM/YYYY` by an unknown process, which dropped
"resolved-to-Healthy" from 58 rows to 0 with no error). If a rewrite/reformat
of this file is ever necessary, verify dates are still ISO afterward by
checking that `resolved-to-Healthy` in `join_report.txt` hasn't collapsed to 0.

`international_squads.csv` columns, in order:

```
nation, player_name, window, source_name, source_url, source_date
```

## 3. Status taxonomy (do not invent new values)

**`internal_status`** (evidence-grounded): `healthy`, `injured`,
`unknown_potentially_injured`, `international_duty`, `retired_medical`,
`unavailable_other`, `suspended`, `coverage_gap`, `review_item`.

**`user_status`** (display layer, derived — see `STATUS_LABELS` in
`build_availability_v2.py`): `Healthy`, `Injured`, `Potential Injury`,
`Likely Healthy (Unconfirmed)`, `Unclear`, `International Duty`,
`Retired (Medical)`, `Unavailable (Other)`, `Suspended`, blank (for
`coverage_gap`/`review_item` rows).

`confidence` is `high`/`medium`/`low` and reflects evidence strength only —
never adjust it to make a row "feel" more resolved.

## 4. The staleness/presumption rule (apply after all rows are drafted)

If a row's *only* evidence is a generic aggregator list (no specific injury
type/body part, just a name on an "unavailable" list) and enough time has
passed that a normal soft-tissue injury would plausibly have resolved:
reclassify `user_status` to `Likely Healthy (Unconfirmed)`, rewrite
`user_notes` accordingly, and set `presumption_rule_applied = yes`.
Leave `internal_status`, `confidence`, and `last_verified` untouched — this
is a display-layer-only rule, fully reversible, fully auditable.

Do **not** apply this to rows with any specific diagnosis, surgery, "ruled
out for the season" language, or a chronic/recurring description — those
stay as genuinely uncertain `Potential Injury`.

## 5. Carry-forward rule (this is what makes reruns consistent)

For every player already in the previous CSV:

- If the new sweep finds **no new information**, keep the previous row
  as-is (same status, same notes, same source) rather than re-writing it in
  new words. Don't paraphrase for the sake of it — identical rows across
  runs are the goal, not a sign of laziness.
- If the new sweep finds a **materially different fact** (status changed,
  new source, resolved/returned, new injury), overwrite the row and note in
  `internal_notes` what changed and when (e.g. "Updated 2026-09-01: confirmed
  fit, see new source").
- If a player from the previous CSV no longer appears in current squad
  data (transferred, retired, dropped from league), leave the row as
  historical rather than silently deleting it — `build_injury.py` already
  only joins rows that match current player data, so stale rows are
  harmless.
- Prefer resolving stale `Likely Healthy (Unconfirmed)` rows via the
  match-appearance check (methodology.md §5: any non-zero score in a round
  after the injury date = healthy) over a fresh web search — it's free
  (no searches needed) and more reliable than press coverage.

## 6. Known permanent gaps

Saracens, Cardiff Rugby, Dragons RFC, Zebre Parma, and Emirates Lions have
historically had little to no capturable injury coverage. Don't burn search
budget re-discovering this each time — check `club_injury_sources.csv`
first; if a club is still flagged `no`/`provisional` there, do one quick
search and move on rather than exhausting the loop on a club that won't
yield results.

## 7. After the CSVs are updated

1. Run `python3 injury/build_availability_v2.py` equivalent (i.e., regenerate
   the CSV from your updated rows) — or edit the CSV directly if that's
   simpler for a small delta update.
2. Run `python3 injury/apply_presumption_rule.py` to reapply staleness logic.
3. Run `python3 injury/build_injury.py` to join into `index.html` and
   regenerate `join_report.txt`.
4. Read `join_report.txt` — check match rate hasn't regressed and skim the
   diff of `INJURY_DATA` in `index.html` for anything surprising.

## 8. Cost expectations

A full 26-club sweep from scratch (searches + reading full article pages +
transcription) runs roughly a few hundred thousand tokens — driven almost
entirely by search/fetch volume, not the transcription step. That's fine for
a pre-season or deadline-day run, but not something to schedule daily or
weekly. An **incremental** rerun (§5 carry-forward — only researching clubs/
players flagged as stale or newly relevant) should cost a fraction of that,
since most clubs will short-circuit to "no new information, keep previous
row." Budget for a full sweep at season boundaries, and incremental sweeps
in between.

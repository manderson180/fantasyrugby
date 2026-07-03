# Methodology: How the first-sweep availability CSV was built

This documents the actual process used to produce `player_availability_first_sweep.csv`,
so it can be extended (e.g. joined with match/squad data) in a separate thread without
re-deriving the approach. It's a manual research sweep, not an automated pipeline — see
`rugby-availability-tracker-plan.md` for the target automated system this is bootstrapping.

## 1. What was actually done

For each of the 26 clubs (10 PREM, 16 URC), I ran web searches such as
`"<club name> injury news June 2026"` and `"<club> squad update"`, then read the highest-value
results (club news pages, beat-journalist match reports, disciplinary releases, national squad
announcements). Every fact that made it into the CSV is traceable to a specific source, recorded
in `source_name` / `source_date` / `source_url`.

One important structural finding shaped the whole sweep: a RugbyPass article dated **26 April
2026** ("The mind-blowing injury lists mounting up across PREM and URC") had already aggregated
each club's official "unavailable for selection" list — 12 of the 26 clubs, ~155 players. This
was the single richest source, but it's a **name list only** — no per-player diagnosis, date, or
severity. Everything else in the sweep (club statements, press-conference transcripts, IRFU/WRU
squad announcements, disciplinary releases) was used either to add detail on top of that list or
to independently discover players not on it.

Two scripts in this project produced the file, run in sequence:
- `build_availability_v2.py` — encodes every researched fact as a `row(...)` call: one row per
  player per status, with structured fields (status, injury date, type, body part, expected
  return, confidence, source) plus a parallel user-facing status/note. Read this file directly to
  see exactly what evidence backs every row — the source URL is on every line.
- `apply_presumption_rule.py` — a post-processing pass implementing the staleness/severity rule
  described in §4 below.

`build_sources.py` produced the companion `club_injury_sources.csv` (the per-club source map:
which outlets are Tier 1/2/3 for each club, and how reliable/structured their coverage is).

## 2. Status taxonomy

**Internal status** (`internal_status`) — the evidence-grounded classification:
`healthy`, `injured`, `unknown_potentially_injured`, `international_duty`, `retired_medical`,
`unavailable_other`, `suspended`, plus two housekeeping values `coverage_gap` and `review_item`
for rows that aren't real players (used to flag clubs/topics with no data captured this sweep).

**User-facing status** (`user_status`) — a friendlier layer derived from the internal status,
with one deliberate refinement (see §4):
- `Healthy` — confirmed fit, including recovered-and-returned cases
- `Injured` — specific injury confirmed, even if return date is unknown
- `Potential Injury` — real, *recent and specific* signal of a problem, not yet confirmed
- `Likely Healthy (Unconfirmed)` — presumed recovered under the staleness rule (§4)
- `Unclear` — the ambiguity is about the reason itself, not just severity/timing
- `International Duty`, `Retired (Medical)`, `Unavailable (Other)` — self-explanatory
- blank — the row is a coverage-gap/review placeholder, not a player

## 3. Confidence and evidence fields

`confidence` (high/medium/low) and `last_verified` reflect the strength of the underlying
evidence and are **never** adjusted by presumption rules — only by new evidence. `injury_date_type`
distinguishes a known injury-occurrence date from a first-reported date, since these are often
different (e.g. a player picked up an injury weeks before it surfaced in press coverage).

## 4. The staleness/severity presumption rule (added this pass)

Problem: ~157 of the ~248 rows trace back only to the undetailed 26 April name list. Left alone,
these would sit indefinitely as "doubtful" even though a full off-season has since passed and most
such absences (calf strains, ankle knocks, etc.) resolve within weeks — genuinely serious injuries
tend to get reported *with* a diagnosis, which is exactly why the well-documented cases in this
dataset (Simone Ferrari's neck surgery, Feyi-Waboso's facial fracture, Oli Jager's retirement)
already look different from the generic list entries.

**Rule:** if a player's *only* evidence is the generic 26 April list (`source_name ==
"RugbyPass injury-list audit"` and `injury_type == "unspecified"`), reclassify `user_status` to
`Likely Healthy (Unconfirmed)` and rewrite `user_notes` to say so plainly. This is a **display-layer
rule only** — `internal_status`, `confidence`, and `last_verified` are left untouched, so the
original evidence trail is fully preserved and auditable. A new column, `presumption_rule_applied`
(`yes`/`no`), flags every row this touched, so it can be found and overridden later.

This rule explicitly does **not** apply to entries with any specific injury detail attached (a
body part with real diagnosis, "ruled out for the season" language, surgery, a chronic/recurring
description, etc.) — those 8 remaining `Potential Injury` rows are genuinely uncertain and recent,
not just stale.

## 5. How to join with match/squad data (for the next thread)

This is the authoritative fix and should override the presumption rule wherever it applies. The
join key is `(team, player_name)` — note names are as commonly reported in press coverage, not
necessarily exactly as they'd appear in an official squad list, so expect to need fuzzy matching
(nicknames, initials, diacritics) rather than an exact string join.

Recommended resolution logic once matchday/appearance data is available:
1. For any row with `presumption_rule_applied == "yes"` or `internal_status ==
   "unknown_potentially_injured"`: if the player appears in **any** matchday squad (bench counts;
   actually playing is stronger) dated after `injury_date` (or `last_verified` if `injury_date` is
   blank), resolve to `Healthy`, confidence `high`, `last_verified` = that appearance date, and
   note it plainly (e.g. "Confirmed fit — appeared for `<team>` on `<date>`").
2. For rows currently `Injured` with `expected_return` unresolved: the same appearance check
   resolves them the same way.
3. Absence is **not** proof of injury on its own — a player can be absent for rotation, form, or
   the international-duty/suspension reasons already captured elsewhere in this file. Only treat
   an *unexplained* absence spanning 2+ consecutive rounds (i.e. not covered by an
   `International Duty`/`Suspended` row already in this dataset) as a fresh signal worth
   downgrading toward `Potential Injury` — never straight to `Injured`.
4. Please don't silently drop the pre-join versions — keep `internal_notes`/`source_url` intact so
   anyone auditing later can see both what the April sweep said and what the match data later
   confirmed.

## 6. Known gaps in this sweep (unchanged from before)

Saracens, Cardiff Rugby, Dragons RFC, Zebre Parma, and Emirates Lions have no injury data captured
(flagged as `coverage_gap` rows) despite some of them — Saracens especially — running good
structured official sources per `club_injury_sources.csv`. Full England/Scotland/Springbok/Italy
squad lists weren't ingested (only Wales's 33 and named Irish call-ups), and a 12 June URC
disciplinary release wasn't reviewed. These are flagged as `review_item`/`coverage_gap` rows rather
than silently omitted.

# OWNER decision site (D037, site v2)

Local pages for the OWNER walk-through. Serve with `python3 serve.py` (http://127.0.0.1:8768).
Build from the repo root:

```
python3 experiments/0005-prototype-fullstack/workflow/2026-11-08/review-site/build.py
```

## Structure

→ `index.html`: next-question button, three stacks, Eingang, "Was ist neu", all pages
→ `next.html`: one card at a time (A/B/C choose, Enter saves note, N next, M push-to-talk)
→ `schnell.html`: Schnelldurchgang, open cards in three tiers (`TIER` in `build.py`)
⠀⠀↳ tier 1/2 bulk "Alle hier so lassen"; tier 3 list only
⠀⠀↳ unlisted open card = tier 2; decided and parked never show
→ `01-…12b-….html`: one page per group (topic); default groups have a bulk action
→ `eingang.html`: new cards for frozen pages, newest first, with date and source
→ `entschieden.html`: decided cards, newest first, plus your answers on open cards
→ `aenderungen.html`: the full change log

## Stacks

→ Blockt Arbeit: status `open`, or `gate=True` (Migrate question that gates the next slice)
→ Gebaute Defaults: status `default`
→ Ideen für später: status `parked`, group `12b-register`, or `later=True`
→ Entschieden: status `decided`

## Rules

→ Eingefroren: a page with an OWNER answer gets no new cards.
⠀⠀↳ OWNER answer = an entry in `feedback/answers.jsonl`,
⠀⠀↳ or the item's `decided` time,
⠀⠀↳ or a `decided` card with `13ue` in `by` (from its `added` time).
→ A card with `added` later than the first OWNER answer of its page goes to the Eingang.
→ `items.json` is the snapshot of the last build. Do not edit it.
→ `changelog.jsonl` is append-only. Each build that changes the item set or a status appends lines:
⠀⠀↳ `ts`, `id`, `page`, `change` (added / status decided / moved to Eingang / removed), `by`.
⠀⠀↳ Lines with `seed: true` were rebuilt from git on the first v2 build.
→ `feedback/*` is append-only and belongs to the OWNER. The build only reads it.

## Add an item

→ Add `it(...)` to its group in `build.py`, with `added=` (UTC time, ISO) and `source=`.
⠀⠀↳ Without them the item takes the group's `added`; on an old group that is too early.
→ Set `gate=True` for a Migrate question that gates a slice, `later=True` for a parked idea.
→ For an OWNER decision taken in chat: status `decided`, `decided=` time, `dl=`.
→ Code blocks: one complete unit (TYPE + constructor clauses + `migrate`), max ~14 lines.
⠀⠀↳ `//` comments only; a sketch starts with "noch nicht gebaut".
→ Never reuse or change an item id, status, `by`, `dl`, option letter or `built` flag.

## Read the answers

→ `GET /api/answers`: latest per id, with `choice_ts` and `note_ts`.
→ `choice: ""` (Rückgängig) clears the choice; the history stays in `answers.jsonl`.
→ Bulk accept writes one answer per card: built letter plus note "Gruppe abgenickt".
⠀⠀↳ It skips cards that already have a choice or a note. One `bulk-accept` act event.
→ `feedback/actions.jsonl`: every click, key, voice and bulk action.
→ `serve.py PORT` runs a test copy; `REVIEW_NO_BUS=1` keeps it off the job bus.

## Notes: decisions (By: Opus (site-v2))

→ Fates page frozen from FATE (13ue, DL-125) at 08:26 statt nur Site-Antworten, weil sonst VERSION-RULE nicht in den Eingang ginge (Brief verlangt das).
→ D025 in "Ideen für später" statt "Blockt Arbeit", weil die Karte sagt: nur notiert, nicht geplant.
→ M3 and M5 gate the fate slice (D036 trigger), so they are in "Blockt Arbeit" although parked.
→ Group pages keep their decided cards; "Entschieden" is an extra view, not a move.
→ Stack page lists on the index link the group pages; no separate stack pages.
→ Code blocks M4, FATE, BLOCKS, M3 rewritten as complete units; FATE and M3 sketches now use `migrate Order v1 -> v2` on the 0005 base `Order` (was v2 -> v3 / v3 -> v4 without the TYPE).
→ DL-147 stays twice (10-misc and 12-decided); "Entschieden" shows it once.
→ Seeded change log: `added` from git commit times of `build.py`; original 74 items = 2026-11-07.
→ Schnelldurchgang is a view, not a card: one `view added` line in the change log, no freeze effect.
→ TIER ids QV3-7 and Q5-1 do not exist as cards; they are ignored.

# Docs output: EXPERIMENT 0005 (PROTOTYPE) and the OWNER walk-through list

**[Verified]** Docs phase, 2026-11-08, after TEST `0315cf2f` (GREEN `d4e11f78`). No code, test or fixture change; `main.rs` and `app/` untouched. Not committed.
By: Opus (docs exp0005) for every line of this file.

## Files

→ `experiments/0005-prototype-fullstack/README.md`: status verified; result section (ownership table, flow, use cases, screens, limits, next test); prerequisite states; repeatable command with `-B`, `db-reset`, `db-down`
→ `experiments/0005-prototype-fullstack/workflow/2026-11-07/owner-review.md`: walk-through on top, old text unchanged below a line
→ `wiki/planning/decisions-to-be-made.md`: D037 (before "Answered 2026-11-07"); `updated` 2026-11-08
→ `wiki/planning/research-and-development.md`: 0005 row
→ `wiki/concepts/vertical-integration.md`: section "The first full vertical line: form to row and back"
→ `GLOSSARY.md`: STORED ROW, PROTOTYPE
→ `docs/index.html`: Verified item, three screens, "Decided, next"; date 2026-11-08
→ `docs/img/prototype-{orders-new,orders,notes}.png`: copies of `screens/*.png` (22 to 29 KB, unchanged)
→ `README.md`: part 6 roadmap row
→ `wiki/log.md`: one entry

## Checks

→ `python3 scripts/lint_wiki.py`: 85 files, 0 errors
→ Links and anchors of the touched Markdown files: all resolve (lint functions, own check)
→ No secret, no test MARKER, no stored value in the docs. Screens show demo rows only.

## Decisions

**Undo**
→ Old owner-review text kept verbatim below a line, so existing anchors still resolve → By: Opus (docs exp0005)
→ Screens copied unchanged to `docs/img/` (already small) → By: Opus (docs exp0005)
→ Lines the ledger marked big but the task list did not name stay in "Other defaults" with "(big)" → By: Opus (docs exp0005)
→ "No DL-101 shape check" listed as superseded by P4c, not as its own question → By: Opus (docs exp0005)
→ PDB-24 merged into the count-line group (same question) → By: Opus (docs exp0005)

**Repair**
→ Option letters written by docs where the ledger had none (QDB-6b, G6D-03, G6D-04, QDB-3, QDB-4, PDB-18, small GREEN lines) statt open text, weil the OWNER answers by letter. Commits us to: each such line says "(letters: docs)" → By: Opus (docs exp0005)
→ D037 counts: 19 big lines in 9 groups, 35 other, 6 parked statt one total, weil the OWNER plans the walk-through by the big list → By: Opus (docs exp0005)
→ Smallest next test = O3 public projection statt O1 or O2, weil it is the only host-API item the PROTOTYPE already depends on → By: Opus (docs exp0005)

**Migrate** (OWNER chooses, D037)
→ Every line of the owner-review walk-through; nothing decided here → By: Opus (docs exp0005, open)

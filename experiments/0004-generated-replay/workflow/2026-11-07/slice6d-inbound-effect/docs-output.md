# DOCS output: slice 6d, the ENTRY LINE

**[Observed]** DOCS phase, 2026-11-07, HEAD `545dded0`. By: Opus (docs slice6d). Docs only: no code, test or fixture change; `main.rs` and the decision log entries untouched. No commit.

## Files

| File | Change |
|---|---|
| `experiments/0004-generated-replay/README.md` | New section "Slice 6d: the ENTRY LINE (inbound EFFECT)": owner table, form (DL-130, DL-132), drift rule, checks, `ui_<event>/1` (DL-131), `Rejected` (DL-133, `<Module>.Rejected` note), ENTRY RECORD keys with a placeholder example (DL-141, DL-142), `--stored` (DL-134, DL-138), DL-040 parity block and RETIRE LINE, tested flow, limits, built defaults G6D-03/04/12 (default, open) |
| `wiki/planning/research-and-development.md` | Slice 6d row; full run `results/20261107T220212948306Z` labelled "before the TEST repair"; re-check note; limit line |
| `wiki/log.md` | One entry |
| `GLOSSARY.md` | ENTRY LINE and ENTRY RECORD rows updated to the built forms; RESPONSE RECORD: D024 closed by DL-134. UI EVENT existed; no REJECTED STRUCT row (not needed) |
| `wiki/concepts/vertical-integration.md` | Section "The inbound side (2026-11-07)", [Verified] with test names |
| `docs/index.html` | Part 6: slice 6d in Verified; "Decided, next": record format v3, slice 6e, `db.*` transports; second sample (ENTRY LINE + form TYPE) |
| `README.md` | Part 6 roadmap row |

## Checks

- **[Observed]** The `docs/index.html` sample compiles with a scratch build of `git archive HEAD` (`545dded0`): `--stored` with an empty snapshot, exit 0, `def ui_place` generated; `fmt` leaves it unchanged; highlighted with `integrations/zed-beaml/preview.py --chat`.
- **[Observed]** `python3 scripts/lint_wiki.py`: 85 files, 0 errors.
- **[Observed]** No stored value and no test MARKER in the docs: the ENTRY RECORD example holds placeholders only.

## Notes

- The review notes duplicate IDs DL-140 and DL-141 in the decision log. Not renumbered here (task: decision log entries untouched).

## Decisions

**Repair**
→ Full run of `35c7e3bf` kept as full-run evidence, labelled "before the TEST repair" statt a new full run, weil docs runs no tests and the re-check covers the repair. By: Opus (docs slice6d)
→ Host claim reads "undefined-function warning, not an error" statt "undefined remote call", weil R6D-11 shows `elixirc --warnings-as-errors` exits 0. By: Opus (docs slice6d)

**Undo**
→ One README section after the RED TEAM 01 repairs. By: Opus (docs slice6d)
→ ENTRY RECORD example with placeholders only. By: Opus (docs slice6d)
→ New docs sample (`PlaceForm`) instead of the fixture text. By: Opus (docs slice6d)
→ No REJECTED STRUCT glossary row. By: Opus (docs slice6d)
→ Glossary RESPONSE RECORD sentence on D024 corrected (stale). By: Opus (docs slice6d)
→ Duplicate DL IDs left for the OWNER or main agent. By: Opus (docs slice6d)

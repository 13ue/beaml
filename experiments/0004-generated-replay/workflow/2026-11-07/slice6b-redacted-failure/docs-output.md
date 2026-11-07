# Docs output: slice 6b steps 6b and 6c (REDACTED FIELD, redacted copies)

Phase: DOCS of the implement-step pipeline, 2026-11-07. Base: HEAD 5b7feb92 (TEST PASS at 16d48f93 per the brief). No code, test, fixture or decision log change. No commit.
By: Opus (docs slice6b/6c) for every item in this file.

## Files

- `experiments/0004-generated-replay/README.md`: new sections "Slice 6b step 6b: redacted fields", "Slice 6b step 6c: redacted copies", "Decisions (Decision4, slice 6b DOCS 6b and 6c)". Forms, projections, DL-116 walk, stored-value block, cases g1 to g5 and l1 to l8, owner tables, results, limits (D6B-184, D6B-31, slice 5 PIN, O1, O2, D6B-191, `o |> holder |> Holder`).
- `wiki/planning/research-and-development.md`: register rows for 6b and 6c with limit lines and the result `results/20261107T200526124175Z`.
- `wiki/log.md`: one entry.
- `wiki/concepts/vertical-integration.md`: one dated **[Verified]** sub-line under the DL-089 line.
- `GLOSSARY.md`: new row REDACTED FIELD.
- `README.md` (root): roadmap row 6.
- `docs/index.html`: part 6 moves the two `redacted` items from "Decided, next" to "Verified" (steps 6b, 6c, with the derived-copy limit); the Concept item names DL-029; the sample has a REDACTED FIELD, `with card_holder` and an allowed copy, highlighted with `integrations/zed-beaml/preview.py --chat`.
- `workflow/2026-11-07/slice6b-redacted-fields/spec.md`: dated additions (O2 forms, D6B-184 wording limit, D6B-31 parse-error form).
- `workflow/2026-11-07/slice6b-redacted-fields/notes.md`: dated additions (missed slice 5 PIN and its move to `461d024e`, 80 re-pinned hashes, full run, hygiene of `20261107T200257991414Z`).
- `workflow/2026-11-07/slice6b-redacted-failure/spec.md`: dated additions (`o |> holder |> Holder` limit, O1, O2, D6B-191).
- This file.

## Checks (observed)

- Sample of `docs/index.html`: scratch `git archive` build of HEAD 5b7feb92, `--stored stored/empty.jsonl`: exit 0, three DEAD LINE warnings. With a plain `Receipt.holder` the build gives the DL-112 text. sha256 of the sample source: `9cabb715…211f6e`.
- `with card.holder` in the sample: `expected identifier at byte N` (D6B-31 form).
- `python3 scripts/lint_wiki.py`: 85 files, 0 errors.

## Decisions

### Undo

- Steps 6b and 6c in one DOCS pass with the shared full-suite run `20261107T200526124175Z`. → By: Opus (docs slice6b/6c)
- "README.md (slice 6 sections)" read as the EXPERIMENT 0004 README; the root README gets only the roadmap row. → By: Opus (docs slice6b/6c)
- O1, O2 (6c), O3 (6b) and the D6B-184 wording stated as open limits, no fix proposed in code. → By: Opus (docs slice6b/6c)
- No glossary terms for "direct value", "identity fn" or "accessor"; the 6c ledger defines them. → By: Opus (docs slice6b/6c)
- "MARKER scan" written as "marker scan of the test" in the README, so no new term is needed. → By: Opus (docs slice6b/6c)
- The sample keeps `type Payment v3` from the earlier sample. `fmt` rewrites it to `type Payment {` (observed); the sample is therefore not in `fmt` form. → By: Opus (docs slice6b/6c)
- Root README row 6, next step: "Entry points as inbound EFFECTS (DL-128)", the first decided item on the roadmap page. DL-029 stays a concept. → By: Opus (docs slice6b/6c)

### Repair

- Ledger docs defects appended as dated additions over edits of the RED text, because the ledger is a phase record. Commits us to: a reader reads the addition after the contract. → By: Opus (docs slice6b/6c)
- Glossary row REDACTED FIELD over lowercase prose only, because the job title and the controlled-language rule need the term in GLOSSARY first. Commits us to: later docs write REDACTED FIELD in capitals. → By: Opus (docs slice6b/6c)
- D6B-184 limit stated in the 6b `spec.md` (as D6B-184 commits the docs phase) and in the README, not only in the README. → By: Opus (docs slice6b/6c)

## Limits

- The README claims come from the ledgers and reviews; only the sample, the `with card.holder` form and the missing `result.json` were checked again here.
- `docs/index.html` was not rendered in a browser in this pass.

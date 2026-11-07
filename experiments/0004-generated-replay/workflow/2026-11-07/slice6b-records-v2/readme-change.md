# README change for the 6a docs phase

**[Proposal]** By: Opus (RED, slice6b-records-v2). Text for the docs phase. The RED phase does not edit the README.

## Where

`experiments/0004-generated-replay/README.md`: one note under each "Pass and reject rule" heading of slices 1 to 5 (`### Pass and reject rule`, `### LIB comparison and pass and reject rule`, `### Pass and reject rule (slice 3)`, `(slice 4)`, `(slice 5)`), and one row in the slice 1 test list (case (c), line "`0003/run.py` passes in the GEN tree ... `tests/overlay_diff_test.py` passes first").

## Note text (each pass and reject rule)

> **[Verified] Cut at slice 6b step 6a (DL-110, OWNER, Q6B-10 option B).** LIB comparison up to slice 6b step 5; evidence retained. From 6a on GEN stores RESPONSE RECORD version 2 (the projection, DL-105) and LIB keeps the raw body. The 0003 copy run (cases (c) runner, (d), (e)) and `tests/overlay_diff_test.py` leave the check list of `run.py` and `tests/arms_test.py`. The slice 1 to 5 result directories stay as evidence. This rule is not checked again after 6a.

## Case (c) line

> After slice 6b step 6a (DL-110): this case keeps only the GEN structure check (`GenStructure`). The 0003 runner in the GEN tree and the overlay diff are retained evidence of slices 1 to 5.

## Glossary row (plan, docs in 6a)

The row RESPONSE RECORD says "body bytes". New text: the declared keys of the response (`value`), the names of other keys, and a digest of both; never the raw body (DL-105).

## Open

DRIFT (f) and the LIB freeze step stay in `run.py` (notes.md O1). The README text does not change for them in 6a.

**[Verified] Done (DOCS, 2026-11-07).** The note text is under the five pass and reject rules, the case (c) line is in the README, and the glossary row is changed. The "Open" item above is superseded: DL-118 and D6B-96 changed DRIFT (f) in 6a; the README case (f) note and the [slice 6b step 6a section](../../../README.md#slice-6b-step-6a-response-record-version-2) state the GEN-only rows and the repair check. By: Opus (DOCS, slice6b 6a+11)

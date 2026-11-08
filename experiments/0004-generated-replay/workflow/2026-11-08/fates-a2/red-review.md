# RED review: fates-a2a (record format draft 4)

**[Verified]** Fresh RED review, 2026-11-08, target RED commit `fc4e3acf` (HEAD `8d9db655`: review-site files only since then).
By: Opus (RED review fates-a2a). Normal fresh review, not a Devil's Advocate checkpoint. No test, production file or commit changed.
Inputs: [plan.md](plan.md) (with "Repairs"), [plan-review.md](plan-review.md), [red-plan.md](red-plan.md),
[red-output.md](red-output.md), [convert_v4.py](convert_v4.py), `git show fc4e3acf`.
Basis: the built default of QA2-1 (not signed by the OWNER; DL-139 holds GREEN until the sign).

## Verdict

**GO for GREEN** after the OWNER signs QA2-1 (DL-139 gate, not a review block). No critical or high objection.
Two medium objections are recorded below; GREEN does not have to resolve them.

## Re-run at HEAD (scratch builds, `git archive HEAD experiments/0001-syntax-to-beam`, `cargo build --offline`)

| Run | Command | Result | Matches red-output.md |
|---|---|---|---|
| HEAD | `BEAML_SPIKE=<head>/target/debug/beaml-spike python3 -B tests/slice6_fates_test.py FatesA2a` | 8 tests, `FAILED (failures=39)`; V4i passes | yes (39 of 40) |
| Depth probe | same binary with `if n == "3" => None` → `"4"` at the 3 readers (5058, 5936, 6612); V4d to V4h | 6 tests, `FAILED (failures=20)`; 8 controls pass | yes (20 of 28) |

Probe failure reasons (observed): V4d v3 refused with the DL-143 text; V4e 7 forms build and the ROW counts as checked;
V4f / V4f2 exit 0; V4g v2 values print the a1 `fate:` line instead of the constructor block; V4g v2 `"app"` is mapped;
V4h v2 `"web"` gets the DL-140 moved block. Each is the planned reason, not setup.
N16 (0005) and `convert_v4.py --check` (26 files, 53 records) not re-run; I accept red-output.md Runs 3 and 4.

## Challenges

| Question | Finding |
|---|---|
| Reader accepts both 3 and 4? | **Refuted.** V4d pins exit 1 and the exact `version 4 only (DL-168)` text for a v3 ROW, RESPONSE RECORD and ENTRY RECORD, plus two draft 4 controls that must build. |
| `{3, nil}` too loose? | **Refuted.** `{3, nil}` is only the observed RED value. Every writer case asserts exact equality with `{4, <nested>}` (`want(...)`), incl. head `{"Order", 1}` in V4c. |
| LIST nested shape (review O1) pinned? | **Yes.** Writer: V4b / V4c list records exact `{"items": {"version": 1, "nested": {...}}}`. Reader: V4e 3 malformed LIST forms; V4g LIST item at `amount` 2 blocks and at 1 is fated, so a reader that ignores the element entry fails. V4f LIST item pins a prefix only (RA-09). |
| SQUASH and newer-version texts distinct? | **Yes.** Two constants; V4f (ROW, ENTRY exact) and V4f2 (exact, plus no `migrate Channel` in stderr). A shared prefix `holds Channel vN in field` exists, but the exact subtests separate them. |
| `convert_v4.py` sets every non-String field to 1: right? | **Right for all 26 files.** Observed non-String fields: `Amount` (constructor `fn Amount` in every paired source), `Channel` and `PaymentState` (enum). No VERSION MARK in the paired sources; no LIST field (the converter asserts). 12 of 53 records get `{}`. Ceiling: a primitive non-String field (e.g. `Int`) would wrongly get 1; none exists. |
| Hand edit between two declared versions caught? | **Confirmed: nothing catches it.** See O1. |

## Objections

### O1 (medium): a downgrade edit of `nested` turns a block into a silent fate

- Evidence: V4g pairs the same value `"0"` at `nested.amount` 2 (blocks) and 1 (quarantined). V4g map pairs `"app"` at
  `channel` 2 (lost literal, blocks) and 1 (mapped). The Int alone decides. V4i pins that `value_sha256` is the value
  digest only; `fingerprint` covers the head TYPE only (plan section 2).
- Consequence: an edit `amount 2 -> 1` (or `channel 2 -> 1`) makes the build pass with a park or a map. After a2b the
  run time parks or maps the value too. No text reports the edit. [Inference]
- Resolving test (only under QA2-1 option C): a v2 ROW with `"0"` and a hand-set `nested.amount 1` blocks with the digest text.
- Disposition: OWNER question QA2-1 (already noted in plan "Repairs"). Not a GREEN block under the built default.

### O2 (medium): the ROW reader is strict only for a missing `nested`

- Evidence: V4e pins 7 malformed forms for a RESPONSE RECORD, but only "no nested" for a ROW (RA-07: counted not decodable, exit 0).
- Consequence: a GREEN that validates `nested` for records but reads a ROW `amount: "1"` or `items: 1` as v1 passes every test.
  The value is then fated or built at a guessed version (against review O1 "no reader guesses").
- Smallest test: add the "a String version" and "a LIST field as an Int" forms to the V4e ROW subtest, expected `counted(1, 0, 1)`.

## Tests that change if the OWNER picks another QA2-1 option

**Option C (digest also covers `type` / `nested`):**
- V4i inverts (the digest is no longer the value-only digest).
- `draft4()` must recompute the digest; else P2b (DL-164) blocks first in every `--stored` case: V4d controls, V4e (8),
  V4f (4), V4f2, V4g (8), V4h (2). V4d v3 cases keep (v3 digest).
- `convert_v4.py`: the digest assert stays for the v3 input, but it must write a new digest.
- Outside a2a [Inference]: P2b digest tests (`slice6_db_stored_test.py`, `record_v3_test.py` V18b), 0005 N15, the
  `sd.core()` / `type_of()` rewrite. O1 closes; its resolving test is new.
- V4a to V4c and N16 keep (they read `version` and `nested` only).

**Option B (omit `nested` when empty):**
- V4b `V4b_entry_record_empty_nested` and V4c `V4c_string_only_row_has_empty_nested` (expect `{}`).
- `convert_v4.nested()` must drop the key: 12 records in 11 fixture files.
- V4e "no nested" and the ROW form keep only if the reader decides "required" from the source TYPE (Order has
  constructor and enum fields); then they keep.
- `sd.type_of()` in GREEN (String-only TYPES).

## Decisions

### Undo
→ Verdict GO for GREEN; the OWNER sign of QA2-1 stays the GREEN gate (DL-139). By: Opus (RED review fates-a2a)
→ Re-run in scratch copies, not in the repo target, because other workers may write `main.rs`. By: Opus (RED review fates-a2a)
→ Converter "non-String = 1" accepted for the 26 files; a primitive-field check is dropped as low. By: Opus (RED review fates-a2a)

### Repair
→ O1 medium, not high, because the plan records the gap and only QA2-1 C closes it. Commits us to: the OWNER card carries it. By: Opus (RED review fates-a2a)
→ O2 medium, not high, because a ROW with a malformed `nested` already counts as not decodable for the pinned form. Commits us to: GREEN may add the two ROW forms. By: Opus (RED review fates-a2a)

### Migrate (OWNER)
→ QA2-1 (open): default A, or B / C / D as in plan.md section 10. The test impact of B and C is listed above.

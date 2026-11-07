# Review: slice 6b step 6b (`redacted` fields, `with`, projections, stored-value block)

Phase: TEST and normal fresh review, 2026-11-07. Target: commit 461d024e (GREEN with the D6B-172 re-pin).
HEAD during the run: 4c48842d (step 6c Solve/RED). That commit changes no compiler file (`git diff 461d024e 4c48842d -- experiments/0001-syntax-to-beam` is empty), so the compiler under test is the 461d024e compiler.
No source and no test changed. No commit. Probes ran in a scratch directory with a scratch build of the same source and a scratch build of 3ae17088 (the parent).
By: Opus (TEST/review, slice6b-redacted-fields) for every judgement in this file.

## Verdict

**FAIL. Two high objections block.** The 6b behaviour is correct for every case that the spec names. The full suite fails in `slice5-syntax`, and an output TYPE with a constructor above a nested redacted field stores the redacted value. By: Opus (TEST/review, slice6b-redacted-fields)

## TEST results (observed)

| Check | Result | Evidence |
|---|---|---|
| `python3 -B experiments/0004-generated-replay/run.py` | **fail**: 13 of 14 steps pass; `slice5-syntax` 60 tests, 33 failures | `results/20261107T192950686106Z/` (`result.json`, `slice5-syntax.stderr`) |
| run.py step counts | compiler (cargo test) pass, lib-freeze pass, arms 11, drift pass, stored-types 33, slice2-replay 21, slice3-types 69, slice3-replay 31, slice4-retire 87, slice4-replay 27, slice5-syntax 60 (33 F), slice5-squash 24, slice5-replay 12, slice5-rewrite 5 | same directory |
| unittest, slice 6 | constructor 25, decode_ctor 8, decode 10, effect_reach 8, enum 20, failure 22, fmt 25, host_struct 3, int 16, pipe 12, record 5, redacted 19, stored_elixir 15, struct_order 3: all OK | scratch logs, one per file |
| unittest, `drift_test.py` | 5 OK | scratch log |
| unittest, `slice6_redacted_failure_test.py` | 8 tests, 13 failures: the step 6c RED of 4c48842d, not in scope of 6b; not counted | scratch log |
| slice 2 to 5 files | run by `run.py` in the same run (row above); not run a second time | `results/20261107T192950686106Z/` |
| `python3 -B experiments/0001-syntax-to-beam/run.py` | pass | `experiments/0001-syntax-to-beam/results/20261107T194357183214Z/result.json` |
| `cargo fmt --check`, `cargo clippy -- -D warnings`, `cargo test` (0001) | clean, clean, 21 and 14 passed | scratch log |
| `python3 scripts/lint_wiki.py` | 82 files, 0 errors | scratch log |
| `tree-sitter test --rebuild` (CLI at `/private/tmp/beaml-zed-highlighting/tools/tree-sitter`, present) | 23 of 23 parses, 4 highlight files pass | scratch log |

Machine-readable summary: `{"run": "20261107T192950686106Z", "run_py": "fail", "steps_pass": 13, "steps": 14, "slice6_unittest": "pass", "drift_test": "pass", "cargo": "pass", "lint": "pass", "grammar": "pass", "verdict": "fail"}`.

## Objections

### O1 · high · observed · the D6B-172 re-pin missed the `slice5_syntax_test` PIN

- Evidence: `slice5-syntax.stderr`: `test_F01_B5_builds_and_equals_the_base_output` (2) and `test_A2_rewritten_sources_build_like_the_base` (31 sources) fail. Each compares the HEAD build with the output of the PIN compiler `237a4578` (`slice5_syntax_test.py:39`). The first differing text is `__beaml_keys__`, the D6B-172 helper.
- Cause: the GREEN notes say "slice 2 to 5 tests were not run again after the re-pin". D6B-172 changes every EFFECT source, so the PIN guard changes too. The re-pin moved three pins but not this one.
- Consequence: the full suite fails at the GREEN commit. The acceptance line "the existing checks pass" does not hold.
- Precedent: step 12 moved the same PIN with a diff proof (commit f3a52261).
- Minimum repair: move `PIN` to the 461d024e compiler after the diff proof below, which already covers these sources. Then run `slice5_syntax_test.py` and the full `run.py` again. No compiler change.
- By: Opus (TEST/review, slice6b-redacted-fields)

### O2 · high · observed · a constructor input above a nested redacted field is stored in the record `value`

- Probe `enum_leak.beaml` (scratch): `type Holder { name: redacted String }`, `enum Pay { Card(Holder) Cash Unknown(String) }`, a constructor `fn Pay kind: String, name: String -> Pay` with `fn Pay "card", n -> Pay = Card(Holder { name: n })`, and `Payment { ... pay: Pay }` as the EFFECT output. The build passes (exit 0). The response holds the MARKER in `pay.name`.
- Observed: live and REPLAY RUN give `Card(%{"name" => MARKER})`. The record has `redacted: []`. The record `value` holds `pay.kind` and `pay.name`. The scan finds the MARKER in plain form in `responses.jsonl`.
- Second form, same cause: `ctor_leak.beaml`: `type Inner { s: redacted String }`, `type Amount { inner: Inner }`, `fn Amount v: String -> Amount = Amount { inner: Inner { s: v } }`, output field `amount: Amount`. The build passes. The record `value` holds `amount.v` with the MARKER. The decode then fails, and it also fails without `redacted` and with the parent build, so that half is an older defect, not 6b.
- Cause: the DL-116 walk in `Checker::effects` (`main.rs`, about 1520 to 1550) follows `Definition::Record` only, and checks the constructor of the TYPE that holds the field only. It skips enum payloads. It ignores a constructor of a TYPE above the field. D6B-106 stores the constructor inputs in `value`, so the input that fills the redacted field is stored.
- Consequence: a field that the source declares `redacted` is stored as plain text in the RESPONSE RECORD. DL-105 says this never happens. The spec exclusion "a nested TYPE with a constructor is a DL-116 reject" covers only the case where the TYPE that holds the field has the constructor. No ledger excludes these two forms. The DL-116 reason applies here: the constructor would need the value, and the value must not be stored.
- Smallest resolving test: the two scratch sources as `bad/` fixtures, each with the expected compile error. This is the interim rule in the DL-116 form. A redacted field below a constructor TYPE or an enum payload of an EFFECT output is a reject.
- Text: the exact error text is a GREEN default. Recording it as a D6B entry is enough: an Undo or Repair decision, and the OWNER is not needed.
- By: Opus (TEST/review, slice6b-redacted-fields)

### O3 · medium · observed · the D6B-72 block reads no `status`; noted, not a block

- Observed: a 503 record whose `request` holds `mid.inner.secret` gives the D6B-72 block (exit 1). The `held` count in `check_stored` reads no `status`.
- Judgement: for privacy this is correct: DL-111 counts what lies in the store, whatever the status. It also widens the C2 surface: one more `--stored` block that applies to records the REPLAY RUN never decodes. M1 (C2, C5) should name the D6B-72 block in its scope.
- By: Opus (TEST/review, slice6b-redacted-fields)

## Review probes (observed)

Each probe uses its own random MARKER. Output shows key names only. The scan (`slice6_redacted_test.scan`: plain, hex, decimal bytes, base64 at offsets 0 to 2) covers the run directory, compiler stderr, Elixir stdout and stderr, `responses.jsonl`, `spans.txt`, `events.txt`, `attributes.txt` and `.beaml/actions.jsonl` of the compile directory.

### Leak hunt

- Depth 3 input (`Order.mid.inner.secret`, no `with`, the service echoes the request and an undeclared `extra.inner.secret` holding the MARKER): the wire, the record `request` and the span input have no `mid.inner.secret`. `unknown_keys` lists names only. The full-input `request` gives `:request_mismatch`. Live and replay are `{:ok, _}`. Scan: **no hit in any channel**.
- Enum payload in an EFFECT input: not reachable. `Order { pay: Pay }` is rejected by D6B-40. An enum input to a pure step reaches no channel: no span on a pure step (DL-119), the event holds the step name only. Enum payload in an EFFECT output: see O2. The channel that holds the MARKER is **`responses.jsonl`, `value`**.
- Lists: BEAML has no list TYPE in the 0001 compiler (no source, no parser form). Not testable.
- An invalid value under a redacted output field (a map or a list that holds the MARKER): live gives `decode`. The record `value`, `redacted` and `unknown_keys` hold no MARKER. Scan clean.

### `with`

- `orders_with.beaml`: the MARKER is in the wire body only. The record `request` holds only `order_id`. Span, event, record, stderr and actions: no hit.
- `with card.holder` (nested name): compile error, but in the generic parse form `expected identifier at byte 279`. D6B-31 holds; the text names no rule (docs item).
- `with card` (a record field that holds a redacted field) and `with order_id` (plain): `error: with names F, which is not a redacted field of Order` (D6B-65).

### Output side

- Redacted String output (`echo_declared.beaml`): live gets the value. Replay gives `card_holder: :redacted` (DL-115). The record lists `redacted: ["card_holder"]`, and `value` and the scan hold no MARKER.
- Redacted Int output: passes DL-116 and stops at `effect payments.authorize: slice 1 decodes String fields only, not Payment.n` (D6B-156, as specified).
- DL-116 fixtures `output_constructor_type`, `output_constructor_field`, `output_enum`, `output_record`: the exact DL-116 head line. A constructor on the output TYPE itself stops earlier at D6B-19, not DL-116 (expected: D6B-19 rejects a constructor TYPE at the EFFECT).
- MIGRATE CHAIN (`Payment v2` and `migrate Payment v1 -> v2 { add holder: String = "x" }`) and a VERSION MARK alone: both give the D6B-169 text.
- DL-113 (`echo_plain.beaml` and a scratch source): builds. Live and replay give the value. The MARKER is in `responses.jsonl` only, in plain form, as declared.

### Stored-value block (D6B-72)

- `request`, depth 3, a clean line, two hit lines (2 and 4), and line 3 with a plain top-level `secret` at another path: `2 stored RESPONSE RECORDS ... hold ... mid.inner.secret in request`, `line 2`. Line 3 is not counted. A file with line 3 only: exit 0 (R1 closed).
- `value`: two records with the MARKER in `card_holder` against `output_redacted.beaml`: the DL-111 1A path error and the D6B-72 block with count 2, `in value`.
- No MARKER byte in stdout or stderr in any stored probe. `.beaml/actions.jsonl` of the probe directory holds no MARKER.
- `value` at depth: not testable. A nested plain record output fails the slice 1 decode limit (spec exclusion).

### D6B-172 diff proof

- `slice3/M/orders.beaml`, parent build against 461d024e build, `--stored stored/empty.jsonl`: both exit 0, stderr equal. The diff is `135a136,137`, `150c152`, `156c158`: the two `__beaml_keys__` lines, the nested key list and the top-level `unknown_keys` list. This equals the notes line for this source.
- `payments.generated.snapshot`: `payments.beaml` has no `effect` line. The 461d024e build output equals the snapshot byte for byte. The snapshot is unchanged in 461d024e. Claim confirmed.

### Red-team touchpoints

- C2: **no** change to the existing checks. The diff of `check_stored` adds the `held` count and the D6B-72 errors only. No existing branch reads or ignores `status` differently. The new block also reads no `status` (O3).
- C1 (DRIVER): **no** change. No hunk of the 461d024e diff touches `const DRIVER` or the Elixir child code (the last hunk ends at about line 4264; DRIVER starts at line 5252).
- B2, B4, B5, C5: not touched by 6b, and nothing is worse.

## Docs defects (for the docs phase; list only)

- `notes.md`, "GREEN re-pin": add the missed `slice5_syntax_test` PIN (O1) and the result of the next full run.
- `spec.md`, "Exclusions and limits": the sentence "a nested TYPE with a constructor is a DL-116 reject" is too wide. State the two forms of O2 and how they are handled.
- D6B-31: state that `with` on a nested name is a parse error (`expected identifier at byte N`) and not a named rule text.
- `notes.md`, GREEN results: the claim "No existing assertion changed" holds for the first GREEN only. The re-pin changed 80 pinned hashes.
- The register and the log must not show the 6b slice as "full suite pass" until O1 is repaired.

## Limits

- Release path (real ProbeSupport, Logger handler, OTel exporter): not run (plan limit L1). The probes use the file-backed stubs of `slice6_redacted_test.py`.
- Upper-case hex and JSON `\u` escapes are outside the scan (as in the RED re-check).
- The `ctor_leak` decode failure is older than 6b. It was not analysed further.
- The step 6c RED failure count (13 failures in 8 tests) was not checked against its ledger.

## Decisions

### Undo

- Counted the slice 2 to 5 files from the `run.py` run of this phase and did not run them a second time. By: Opus (TEST/review, slice6b-redacted-fields)
- Excluded `slice6_redacted_failure_test.py` (6c RED, 4c48842d) from the 6b count. By: Opus (TEST/review, slice6b-redacted-fields)
- Wrote the machine-readable summary into this file, not into a separate `test-output.log`, because the brief allows one file only. By: Opus (TEST/review, slice6b-redacted-fields)

### Repair

- Chose: O2 at high, blocking. Over: medium. Because: a declared redacted value lies in the store, and only the DL-111 eager removal can take it out again. Commits us to: a GREEN repair with RED for the two fixtures before the slice closes. By: Opus (TEST/review, slice6b-redacted-fields)

## Re-check after review repair (acf12d75)

Phase: TEST and normal fresh review, 2026-11-07. Target: commit acf12d75 (review repair O1, O2). HEAD during the run: 51fd79b2 (step 6c GREEN), so the compiler under test also holds the 6c check. No source and no test changed. No commit. Probes ran in a scratch directory with a scratch `git archive` build of HEAD.
By: Opus (TEST/review, slice6b-redacted-fields) for every judgement in this section.

### Verdict

**PASS.** O1 and O2 are closed. No new objection at critical or high. One docs limit (D6B-184) stays. By: Opus (TEST/review, slice6b-redacted-fields)

### TEST results (observed)

| Check | Result | Evidence |
|---|---|---|
| `python3 -B experiments/0004-generated-replay/run.py` | **pass**, 14 of 14 steps | `results/20261107T200526124175Z/result.json` |
| run.py step counts | compiler pass, lib-freeze pass, arms 11, drift pass, stored-types 33, slice2-replay 21, slice3-types 69, slice3-replay 31, slice4-retire 87, slice4-replay 27, **slice5-syntax 60 OK**, slice5-squash 24, slice5-replay 12, slice5-rewrite 5 | same directory, `*.stderr` |
| unittest, slice 6 | constructor 25, decode_ctor 8, decode 10, effect_reach 8, enum 20, failure 22, fmt 25, host_struct 3, int 16, pipe 12, record 5, redacted 20, redacted_failure 8, stored_elixir 15, struct_order 3: all OK | scratch logs |
| unittest, `drift_test.py` | 5 OK | scratch log |
| `redteam_b3`, `redteam_c1`, `redteam_c3` | RED, expected red, not counted: 1 test 1 failure; 8 tests 6 failures; 5 tests 10 failures | scratch logs |
| `python3 -B experiments/0001-syntax-to-beam/run.py` | pass | `experiments/0001-syntax-to-beam/results/20261107T202140254071Z/result.json` |
| `cargo fmt --check`, `cargo clippy -- -D warnings`, `cargo test` | clean, clean, 21 and 14 passed | scratch log |
| `python3 scripts/lint_wiki.py` | 82 files, 0 errors | scratch log |
| `tree-sitter test --rebuild` (CLI present) | 23 of 23 parses, 4 highlight files pass | scratch log |

### O1 (observed): closed

- `slice5-syntax` passes in the full run: 60 tests, OK. The PIN at `461d024e` holds with the 6c compiler too: the 6c byte check changes the 13 RED fixtures only. By: Opus (TEST/review, slice6b-redacted-fields)

### O2 (observed): closed

- The two fixtures `bad/output_enum_payload.beaml` and `bad/output_constructor_above.beaml`: exit 1, empty stdout, the DL-116 head line with `Holder.name` and `Inner.s`.
- Own probes, each with the DL-116 text, exit 1, no stdout: an enum payload two levels above (`enum Pay { Card(Wrapper) }`, `Wrapper { h: Holder }`); an enum field inside a plain record field of the output (`Box { pay: Pay }`); a constructor two TYPES above the field (`Amount` with a constructor, `Mid`, `Inner.s`).
- No value reaches `responses.jsonl`: the build rejects, so no module exists and no live or REPLAY RUN can start. The runtime half of the O2 probe has no target now. By: Opus (TEST/review, slice6b-redacted-fields)

### D6B-184 wording limit (observed)

- The text says "must be a String or Int field of a TYPE without a constructor". For `Holder.name` below an enum payload this is false as written: `Holder.name` is a String field of a TYPE without a constructor. The text gives no reason for the reject. The help line ("remove redacted from Holder.name") is correct. For `Inner.s` below `Amount` the same holds: `Inner` has no constructor. Docs item, not an objection: D6B-184 records the limit and an OWNER-visible new text is a later choice. By: Opus (TEST/review, slice6b-redacted-fields)

### Docs defects (list only)

- `spec.md`, "Exclusions and limits": state the D6B-184 limit: the DL-116 text names the field, not the enum or the constructor TYPE above it, and its "TYPE without a constructor" clause does not describe these two cases.
- `notes.md`, "Review repair": "Not run: the full `run.py`" can now point to `results/20261107T200526124175Z` (pass, `slice5-syntax` 60 OK).
- Hygiene: commit 51fd79b2 holds the run directory `results/20261107T200257991414Z` without `result.json`; its files changed after the commit (dirty tree at the start of this phase). A run wrote while the commit ran. The register must not cite this directory as a complete run.

### Decisions

#### Undo

- Counted the redteam files as RED, not as failures of this step. By: Opus (TEST/review, slice6b-redacted-fields)
- Checked O2 at compile time only; a reject leaves no runtime channel to scan. By: Opus (TEST/review, slice6b-redacted-fields)

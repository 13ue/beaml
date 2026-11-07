# Review: slice 6b step 6c (no non-redacted copy of a redacted value)

Phase: TEST and normal fresh review, 2026-11-07. Target: commit 51fd79b2 (GREEN). HEAD during the run: 51fd79b2. No source and no test changed. No commit. Probes ran in a scratch directory with a scratch `git archive` build of HEAD. Runtime probe: the harness of `slice6_redacted_test.py` (file-backed stubs, loopback stub, own random MARKER, its `scan`).
By: Opus (TEST/review, slice6b-redacted-failure) for every judgement in this file.

## Verdict

**PASS.** Every case of the spec and every probe of the brief behaves as specified. Three medium objections, noted, not blocking. By: Opus (TEST/review, slice6b-redacted-failure)

## TEST results (observed)

| Check | Result | Evidence |
|---|---|---|
| `python3 -B experiments/0004-generated-replay/run.py` | **pass**, 14 of 14 steps (slice5-syntax 60 OK) | `results/20261107T200526124175Z/result.json` |
| `slice6_redacted_failure_test.py` | 8 tests, OK | scratch log |
| other slice 6 unittest | constructor 25, decode_ctor 8, decode 10, effect_reach 8, enum 20, failure 22, fmt 25, host_struct 3, int 16, pipe 12, record 5, redacted 20, stored_elixir 15, struct_order 3: all OK | scratch logs |
| `drift_test.py` | 5 OK | scratch log |
| `redteam_b3`, `redteam_c1`, `redteam_c3` | RED, expected red, not counted: 1/1, 6 failures in 8, 10 failures in 5 | scratch logs |
| 0001 `run.py`; cargo fmt, clippy, test | pass (`experiments/0001-syntax-to-beam/results/20261107T202140254071Z/`); clean, clean, 21 and 14 | scratch log |
| `scripts/lint_wiki.py`; `tree-sitter test --rebuild` | 82 files, 0 errors; 23 of 23 parses, 4 highlight files | scratch logs |

## Probes (observed)

| Probe | Result |
|---|---|
| Two-clause accessor, both clauses return `card_holder`, `Receipt { holder: holder(o) }` | rejected, D6B-175 text |
| `o \|> holder \|> Held` | rejected, payload text (DL-112) |
| `o \|> holder \|> Holder` (constructor of a plain `Holder { name: String }`) | builds (limit `l2`) |
| Copy into a `redacted` target field | builds |
| Copy into an enum payload `Held(card_holder)` | rejected, payload text |
| Failure value `Bad { reason: card_holder }` | rejected, D6B-67 text (DL-105) |
| DL-113: same name `card_holder` bound from a plain TYPE | builds |
| Depth 3 pattern `Order { mid: Mid { inner: Inner { secret } } }` | rejected, `secret of Inner` |
| EFFECT output `Payment { card_holder: redacted String }`, then `\|> receipt` with a pattern bind and a copy | rejected, `card_holder of Payment` |
| Two-element record literal `Pair { a: card_holder, b: "x" }`, then destructured | rejected at the literal (`a` of `Pair` is plain); with `a` redacted the bind stays redacted, so no bypass |
| Copy in a constructor body, in a record literal inside a variant, in an enum constructor clause | rejected (3 of 3) |
| `fmt` of `f1_failure_record.beaml` | exit 0, bytes unchanged; `build` of the same file: exit 1 |

## Objections

### O1 · medium · observed · a derived copy reaches the record `request` and the span in plain text

- Probe `q3_runtime` (scratch): `fn holder Order { card_holder } -> String = card_holder`, `fn wrap s: String -> Lookup = Lookup { name: s }`, `fn place o: Order -> Payment ! PaymentError = o |> holder |> wrap |> payments.authorize`. The build passes.
- Live run with the own MARKER: the scan finds it in plain form in `responses.jsonl` and `spans.txt`. Wire keys: `name`.
- Cause: the accessor makes a direct value; `wrap` is a record-building fn, so the value is derived (D6B-174, limit `l3`). This is in the DL-112 limit ("only the direct copy is caught").
- Consequence: a two-line helper puts a declared redacted value into the store, with no `with` and no compile error. The D6B-72 stored-value block does not see it later: the stored field `name` is not redacted. The spec names `l3` as "derived, not checked", but no ledger states that this path ends in the store.
- Smallest resolving test: none in this step. Docs: state this path as an observed plain-text path to the store under the DL-112 limit, as evidence for DL-029.
- By: Opus (TEST/review, slice6b-redacted-failure)

### O2 · medium · observed · reach depends on arity: a two-parameter accessor and a failure builder pass

- `fn pick Order { card_holder }, x: String -> String = card_holder` and `Receipt { holder: pick(o, "x") }`: builds. The same body with one parameter is `d8` and rejects.
- `fn bad s: String -> Bad = Bad { reason: s }` and `fn check Order { card_holder } -> String ! Bad = card_holder |> bad`: builds. A redacted value lands in the failure TYPE, the DL-105 case.
- Cause: D6B-174 and D6B-182 accept only one-parameter fns; the builder is `l3` again.
- Consequence: the "accessor" rule covers one arity only. A program that adds an unused parameter bypasses it. Not a spec defect (the spec says "one parameter"), but the bypass is cheaper than the spec limits suggest.
- Smallest resolving test: a limit fixture for the two-parameter accessor, so a later reach change is visible.
- By: Opus (TEST/review, slice6b-redacted-failure)

### O3 · medium · observed · `fmt` accepts a source that `build` rejects (D6B-191)

- `fmt` of `f1_failure_record.beaml`: exit 0, bytes unchanged; `build`: exit 1.
- Judgement: this is the D6B-191 decision, not a defect. `fmt` emits no code, so no value reaches a channel. A gap only if a tool or hook treats `fmt` exit 0 as "the source is valid". No such use is known.
- Resolving step: none; the docs state "`fmt` is not a check".
- By: Opus (TEST/review, slice6b-redacted-failure)

## Docs defects (list only)

- `spec.md`, "Exclusions and limits": add O1 (derived path ends in `responses.jsonl` and the span) and O2 (one-parameter reach only; a two-parameter accessor and a failure builder pass).
- `spec.md`, Contract: the probe `o |> holder |> Holder` (accessor into a constructor) is a limit like `l2`; notes.md has it as a probe only.
- D6B-191: say that `fmt` is not a validity check.
- Hygiene: commit 51fd79b2 holds the run directory `results/20261107T200257991414Z` without `result.json`; its files changed after the commit. A run wrote while the commit ran. Do not cite it as a complete run.

## Limits

- Release path (real ProbeSupport, Logger handler, OTel exporter): not run. The runtime probe uses the file-backed stubs.
- False-negative hunt: about 10 minutes, compile probes and one runtime probe. Not exhaustive.
- No list TYPE and no field access form exist, so no probe for them.

## Decisions

### Undo

- Counted the redteam files as RED, not as failures of this step. By: Opus (TEST/review, slice6b-redacted-failure)
- Ran one runtime probe (O1) through the `slice6_redacted_test.py` harness from scratch; no repo file changed. By: Opus (TEST/review, slice6b-redacted-failure)

### Repair

- Chose: O1 at medium. Over: high. Because: DL-112 (OWNER) limits the rule to the direct copy, and `l3` pins this limit. Commits us to: the plain-text store path stays open until DL-029. By: Opus (TEST/review, slice6b-redacted-failure)

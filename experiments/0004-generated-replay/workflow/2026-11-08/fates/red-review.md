# RED review: fates-a1

**[Verified]** Fresh-context RED review (normal, not Devil's Advocate), 2026-11-08, RED commit `a500306e`.
By: Opus (RED review fates-a1). Inputs: [plan.md](plan.md) with "Plan repair after plan check", [decisions.md](decisions.md),
[red-plan.md](red-plan.md), [red-output.md](red-output.md), [red-probe.diff](red-probe.diff), `tests/slice6_fates_test.py`,
`slice6/db/fates/`. Basis: DL-102, DL-122, DL-125, DL-152, DL-155, DL-156, DL-157, DL-160. No production file, no commit.

## Runs (own, scratch copies)

```
git archive HEAD experiments/0001-syntax-to-beam   # HEAD a500306e; main.rs sha256 460c3c31…, equal to the working tree
patch -p1 < red-probe.diff                         # second copy: parse-only probe, applies clean
cargo build --offline (debug, release; probe release), cargo 1.94.0
BEAML_SPIKE=<bin> python3 -B experiments/0004-generated-replay/tests/slice6_fates_test.py
```

| Compiler | Tests | Failing (subTests or tests) | Passing |
|---|---|---|---|
| HEAD release | 22 | 61, 0 errors | the setup controls in F7, F7b; guards S3b `stricter_v1`, `channel_v1`; S5 "no variant" |
| HEAD debug | 22 | 61, same list | same |
| parse-only probe | 22 | 55 | F1, F2, F3; F4 two build subTests; **F7 `order_map`** |

Equal to [red-output.md](red-output.md). Byte guards at HEAD with the new fixtures tracked: `slice6_db_test` N13,
`slice6_entry_test` n13, `slice6_multi_test` n13, `slice5_syntax_test` (60 tests), `slice6_host_struct_test` byte guard,
`slice6_pipe_test` byte guard: all OK. `run.py` holds no `fates` step (DL-147).

## Per test

| Test | Genuine (HEAD) | Right against the decisions | False-pass risk |
|---|---|---|---|
| F1 | yes: `unsupported migrate step: quarantine` | form A (QF-3 ruling, DL-155) | build test; passes on probe by design |
| F2 | yes: `expected '{'` (no enum mark) | enum form, RF-04 two literals | passes on probe by design; F8 and S3 enum guard the mark |
| F3 | yes: `unsupported migrate step: map` | qualified form in the last owner step | build test only |
| F4 | yes: parse error; old K8 text | PF-05 | low: the K8 text subTest fails on probe |
| F5 (20+1) | yes: parse text instead of each pinned text | PF-06, PF-08, PF-11, RF-02 to RF-06, RF-12 | low: whole stderr compared; `error: ` optional only (RF-11) |
| F6 | yes: parse error | PF-09; DL-160 does not change a1 (RF-14) | low |
| F7 | yes for `amount_v2`, `channel_v2` | ruling on O1 | **medium: `order_map` passes on probe (objection 3)** |
| F7b | yes: exit 1 | ruling on O1 | low for the nested step; no record-chain case |
| F8 | yes: `expected '{'` | TYPE mark rule on enums | low: probe fails it (mark ignored) |
| S1 | yes: told `[]` | DL-102 lifted by `quarantine`; a1 stop line (O2) | **medium: count 1 only (objection 2)**; rows line optional, PF-14 unpinned in a1 |
| S1b (4) | yes: only the help line differs | DL-155 help, PF-21 `value` / `currency` | low |
| S1c | yes | PF-12 | **PF-17 (count once per list record) unproven: one failing item only (objection 2)** |
| S1d | yes | PF-12, DL-134 | low |
| S1e | yes | a line frees its own TYPE only | low |
| S1f | yes | `quarantine` does not lift DL-122 | low (RF-10 leaves the fate line open) |
| S2 (2) | yes | DL-122 lifted by `map`, bare and qualified | **high: every lost literal is `"app"`; see objection 1** |
| S2b (2) | yes: old D6B-39 help | DL-155 enum help, DL-124 placeholder | low: `"app"` absence checked |
| S2c (2) | yes | DL-142 kept value not mapped | "kept alone" passes on any build without the W2 DEAD LINE; the pair carries the proof |
| S3 (3) | yes: old help or parse error | DL-155 gate: mark alone does not lift (type and enum), RF-08 `v3` | low: proves "fate line per affected value", not "version bumped" |
| S3b (4) | 2 of 4 (plain cases pass at HEAD) | DL-155 "without affected values free" | plain cases are regression guards only; the fate cases prove "an unhit fate line builds, exit 0" |
| S4 (6) | yes: anchor missing | DL-124, DL-032 | **medium: blind to stored Strings under 5 chars (`0`, `app`, `tv`, `EUR`)** |
| S5 (3) | 2 of 3 (guard passes at HEAD) | plan repair 5, RF-09 | **high: no case with a fate line present (objection 1)** |

Checks asked for:

- **Text anchors.** `rejects()` drops one leading `error: ` and compares the rest exactly (RF-11): acceptable. `told()` keeps
  only lines with the prefixes `error`, `warning`, `note`, `fate:`, two blanks; any other new line is dropped. S4 covers
  those lines only for stored words of 5 chars or more.
- **`fate:` line format.** Exact, but only `count == 1` is tested; the plural `S` branch never runs.
- **GREEN that lifts the block without counting.** Fails S1, S1c, S1d, S2 (exact `fate:` line). A GREEN that prints a
  constant `1` passes (objection 2).
- **Enum VERSION MARK ignored by the parser.** F2 passes; F8 and S3 "enum mark without a step" fail. Covered.
- **S3b controls.** The plain cases (`stricter_v1`, `channel_v1`) prove nothing new (pass at HEAD); they guard against a
  GREEN that blocks every source with a stricter rule. The fate cases are the real S3b proof.
- **Fixtures.** Corpus syntax plus the new lines only; `//` comments only; no person name; no secret-like string (trace and
  span ids are synthetic hex counters); `stricter_v1` equals 0005 `variants/stricter/orders.beaml` except the header comment
  (RF-13); every fixture holds `= db.put(` so the N13 filter skips it; wrong forms stay inline.

## Objections (max three)

1. **High · Lift scope is not pinned.** "`quarantine` lifts DL-102 only, `map` lifts DL-122 only" is tested in one
   direction (S1f). No test runs a no-signature or shape fault under `amount_v2` (S5 uses `stricter_v1`, no line), and no
   test has a lost literal other than `"app"` under a `map "app"` line. A GREEN that quarantines every DL-102 site of
   `Amount`, or that maps every lost literal of `Channel` once any map line exists, passes all 22 tests.
   Consequence: a decode fault is parked as quarantined (hides broken rows, DL-150) or a lost literal leaves the block
   with no line that names it (DL-122, DL-155).
2. **Medium · Counts never exceed 1.** Every `fate:` expectation has `count == 1`; S1c has one failing item. A constant
   `1`, a per-item count for list records (against PF-17) or a missing plural pass. Consequence: the build report
   under-counts, against DL-157 ("a page never claims 10 orders while it shows 5").
3. **Medium · F7 `order_map` does not test the O1 rule.** It passes on the parse-only probe: the v1 row keeps every
   step of the `Order` chain live, so W2 never fires. The "fate step is never a DEAD LINE" ruling is proven for nested
   steps only.

Dispositions: pending (main agent / OWNER). None accepted here.

## RED repairs for GREEN to apply first (before any `main.rs` change)

- **R-1 (objection 1).** S5b: `AMOUNT_V2` with `row(string_amount)` gives the no-signature block with `NO_SIGNATURE_HELP`
  and no `fate:` line; the same for a "no String value" row (shape fault) with the DL-102 help.
  S2d: `CHANNEL_V2` with `rows=[row(APP), row(dict(WIRE1, order_id="order-tablet", channel="tablet"))]` gives the
  `fate:` line with count 1 and the DL-122 block for line 2 (help per RF-08: `enum Channel v3 … migrate Channel v2 -> v3`),
  exit 1. Optional: a stricter `Amount` under a `map` line still blocks (`map` does not lift DL-102).
- **R-2 (objection 2).** S1 with two `ZERO`-form rows (distinct `order_id`) gives `fate: 2 stored ROWS …` and
  `rows: 3 rows, 3 checked, 0 not decodable`; S1c with one list record holding two failing items gives
  `fate: 1 stored RESPONSE RECORD …`; one mixed case (rows and responses) gives both lines (compare as a set; PF-13 sets no
  order between streams).
- **R-3 (objection 3).** F7 `order_map`: rows typed `Order v3` only; control: `warning: DEAD LINE: migrate Order v1 -> v2`
  is printed; check: no DEAD LINE on `migrate Order v2 -> v3`. Add the same source to F7b (the fate step stays).
- **R-4 (note).** S4: for the quarantine cases assert that no `told()` line other than the pinned ones exists, or add
  the short stored words that are not source text (`"0"` quoted, `order-`) to the check. `"app"` stays source text in the
  `map` line.
- **R-5 (note).** Mark PF-24 superseded by DL-160 in decisions.md (RF-14 says it, PF-24 still reads "DL-116 stays").

## RED decisions checked (RF-01 to RF-14)

- RF-02 (`quarantine amount` on `Order` is an error naming the `Amount` step): follows the QF-3 A ruling; QF-3 C was
  "not built", an error is the loud form of that. Not a silent change.
- RF-03 (`quarantine channel` is an error): narrows the DL-155 reading ("a fate line … or a map line" for any affected
  value). Recorded as an open OWNER line; an error is reversible. Its class is Migrate-pending, not Repair.
- RF-08 (help names newest + 1): the plan rule and DL-058. Consistent; S3 pins it.
- RF-09 (no-signature sites get no version help): departs from the DL-155 effect text "the help names the version form",
  with a recorded reason. It also fixes "no signature = decode fault, never quarantined", a stored-data outcome.
- RF-01, RF-04 to RF-07, RF-10 to RF-13: no decided default changes.
- QF-3 and QF-7 were ruled by Fable on the signed picture and lowered from Migrate to Repair; recorded with reason.

## Migrate items the OWNER has not answered

- DL-156 scope: DL-140 swap detection in fates-a (needs the previous literal table, QF-8) or fates-b (PF-01).
- May `quarantine` park a lost ENUM LITERAL beside `map` (RF-03 makes it an error for now)?
- QF-2: nested TYPE VERSION source-only (default A built in a1).
- QF-5 texts: the help, `fate:` and stop-line texts of RF-01 to RF-09 are RED defaults.
- **[Inference]** RF-09 reading: a value that matches no signature of a constructor TYPE is a decode fault and never
  quarantined (DL-102 "fails a new rule" could cover it).
- QF-3 A and QF-7 A: ruled on evidence by Fable, not answered by the OWNER in words.

## Limits

- The probe is the RED's own; no second mutation was built. Objection 1 and 2 come from reading the tests (no case
  exists), not from a built wrong GREEN.
- Elixir is needed for the constructor runs (D6B-105); this machine has it.

# GREEN output: fates-a4

**[Verified]** GREEN on HEAD `0ecf80c1` (working tree, not committed), 2026-11-08. By: Opus (GREEN fates-a4).
Inputs: [plan.md](plan.md) with Repairs, [red-output.md](red-output.md), [red-review.md](red-review.md), rulings O1 to O3 (By: Fable).

## 1. Changes

| File | Change |
|---|---|
| `experiments/0001-syntax-to-beam/src/main.rs` | `fmt_mark(mark, chain, fate)`: a chain with a fate line keeps its mark (QA4-1 A), per chain; `bodies` gets a MIGRATE STEP branch (QA4-2): split at top-level `,`, comma right after its change, shared `body()` writer for TYPE, ENUM and MIGRATE bodies; comment body stays; no alignment (QA4-3); unit test `fmt_mark_follows_dl104` + 1 case |
| `experiments/0004-generated-replay/tests/slice6_fmt_test.py` | T2c `test_mark_rule_per_chain_not_per_file` (O1) |
| `integrations/zed-beaml/grammar.js` | `enum_declaration` optional `version`; `quarantine_operation`, `map_operation`, `redact_operation`, `retire_operation` in `_migrate_operation` |
| `integrations/zed-beaml/languages/beaml/highlights.scm` | `"quarantine" "map" "redact"` keywords |
| `integrations/zed-beaml/grammars/beaml.wasm` | rebuilt, `tree-sitter build --wasm` (offline) |

`src/` (parser.c, grammar.json, node-types.json) is regenerated with `tree-sitter generate --abi 15 --js-runtime native`; it is git-ignored.

## 2. RED first (rulings O1, O2)

- **T2c at HEAD:** fail, `b'\ntype Order v3 {\n' not found` (both marks lost). GREEN: pass.
- **O2 whole-line checks** (preview from a `git archive HEAD` copy of the grammar vs. the working tree):

| Check | HEAD | GREEN |
|---|---|---|
| (a) `channel_v2` line `migrate Channel v1 -> v2 { map "app" -> Mobile }`, exact fragment from red-review.md | fail | pass |
| (b) `amount_v2`: `<i class=k>quarantine</i> <i class=p>value</i>` | fail | pass |
| (c) enum mark | cited: G1 entry 11 and G3 pass | |

## 3. Checks (observed)

| Command | Result |
|---|---|
| `cargo build --offline` (debug) and `--release` | exit 0 |
| `cargo fmt --check` | pass |
| `cargo clippy --offline -- -D warnings` | exit 0 |
| `cargo test --offline` | 22 unit + 14 cli pass |
| `python3 -B experiments/0004-generated-replay/tests/slice6_fmt_test.py` | Ran 38, OK (T1 to T6, T2c, G3 included) |
| `tree-sitter test --rebuild` | 31 of 31 parses, 5 highlight files pass (fates.beaml 27 assertions) |
| `tree-sitter test --wasm --rebuild` | same, pass |
| `tree-sitter parse --wasm -q slice6/db/fates/*/orders.beaml` (committed-path wasm) | exit 0, no ERROR |
| `python3 -B experiments/0004-generated-replay/run.py` | run `results/20261108T145443950765Z`: 39 of 40 steps pass; only `slice6-fates` fails |
| `python3 -B experiments/0005-prototype-fullstack/run.py db-up` | `results/20261108T151155877378Z` pass |
| `python3 -B experiments/0005-prototype-fullstack/run.py run` | `results/20261108T151202728219Z` status fail; acceptance list = `exp0005-N16` only (step `test-n8`); N17 pass; 24 pass, 1 fail, 1 blocked (N9, D036) |

**`slice6-fates` failure is the a2a RED (fc4e3acf), not a4.** `slice6_fates_test.py` with a HEAD compiler
(`git archive HEAD`, `BEAML_SPIKE`) and with the GREEN compiler: 39 failures each, identical sorted FAIL lists
(V4ab to V4h). **0005:** accepted per DL-173 (N16 only failure, N17 passes).

**Byte pins:** no pin site moved. The pin guards run in 0004 steps `slice5-syntax`, `slice6-entry`, `slice6-multi`,
`slice6-db`, `slice6-pipe`, `slice6-host-struct`, `slice6-effect-reach`: all pass. No pin file and no `.beaml` fixture changed.

## 4. Retained runs and a note

- 0004 run `results/20261108T143501248455Z` (first full run): `slice6-fmt` failed G3 (5 subtests) in addition to
  `slice6-fates`. Cause (observed): my HEAD preview probe compiled the HEAD grammar into the shared tree-sitter cache
  `~/Library/Caches/tree-sitter/lib/beaml.dylib` (15:34), newer than `src/parser.c`, so `parse` used the old grammar.
  `tree-sitter test --rebuild` rewrote the cache; G3 passes since. Kept as a failed run. **TEST:** run
  `tree-sitter test --rebuild` before G3 so the cache matches `src/`.
- 0004 dirs created during the run by its own steps are kept untouched.

## 5. Decisions (By: Opus, GREEN fates-a4)

**Repair**
→ fate flag in `fmt_mark` statt a separate check in `formatted`, weil the unit test pins the rule in one place
⠀⠀↳ commits us to: QA4-1 B or C changes one match arm
→ MIGRATE body from `program.migrations` ranges statt a token scan for `migrate`, weil the parser already owns the range
→ T2c with a multi-line Chained body statt the one-line `marks.beaml` form, weil the type body rule would add a diff

**Undo**
→ shared `body()` writer for TYPE, ENUM and MIGRATE bodies
→ comma depth counts `(` and `[` only
→ a MIGRATE line with text before it on its line stays as written (as TYPE)
→ `retire_operation` field `duration` as in `retire_declaration`

A PASS does not establish production readiness.

# RED output: fates-a4

**[Verified]** Runs at HEAD `d6ab59c9` (working tree with the RED tests only), 2026-11-08. Compiler: `cargo build --offline`
debug `beaml-spike`; tree-sitter CLI 0.26.5 at `/private/tmp/beaml-zed-highlighting/tools/tree-sitter`.
By: Opus (RED fates-a4).

## 1. `fmt` tests

```sh
python3 -B experiments/0004-generated-replay/tests/slice6_fmt_test.py
```

Result: `Ran 37 tests`, `FAILED (failures=29)`. All 29 failures are subtests of the six new RED tests. The 30 earlier
tests pass (`test_mark_removed_when_a_chain_from_v1_implies_it` = T2b included). T5 passes (guard).

| Test | Failing subtests | Reason at HEAD (observed) |
|---|---|---|
| T1 | 3 of 7: `amount_v2`, `order_map`, `two_ctor` | stdout is a diff `-type Amount v2 {` / `+type Amount {` (`v3` for Order); 4 guards pass |
| T2 | 1 | `b'\ntype Order v3 {\n' not found`: fmt writes `type Order {` |
| T3 | 8 of 8 | the MIGRATE body stays as written (`{map channel "app" -> Mobile,   quarantine …}`) |
| T4 | 2 of 2 | `{quarantine "fax"}` and the multi-line single change stay |
| T6 | 10 of 10 | "first fmt": mark removed and body unchanged; the setup build of every input passes (exit 0) |
| G3 | 5 of 12 | `parse -q` exit 1 with `ERROR`: `amount_v2`, `channel_swap`, `channel_v2`, `order_map`, `two_ctor`; `channel_v1`, `stricter_v1` and the five 0005 sources pass |

Probes behind the inputs: every T3/T4/T5 input passes `validate` (`fmt` exit 0 at HEAD) and builds with
`--stored slice6/db/stored/responses.jsonl` (exit 0). A fate line in the first of two steps is rejected by the checker
("a fate line stands only in the last MIGRATE STEP"), so T2 uses the last step.

## 2. Tree-sitter corpus and highlights

```sh
cd integrations/zed-beaml && tree-sitter test --rebuild
cd integrations/zed-beaml && tree-sitter test --wasm --rebuild
cd integrations/zed-beaml && tree-sitter test --rebuild -e "fate|Fate|ENUM VERSION|quarantine|fate lines"
```

- `test --rebuild`: exit 1, 6 failures, all in `fates.txt`: entries 11 to 15 and 17 parse to `ERROR` nodes (enum version,
  `quarantine`, `map`, `redact`, `retire` in a migrate body). Entry 16 (keyword controls, guard) and the 24 earlier entries pass.
- `test --wasm --rebuild`: same 6 failures. It ran offline (no download needed).
- With the fates entries excluded the highlight tests run: `fates.beaml` fails at `row: 4, column: 27, expected highlight
  'keyword', actual highlights: none` (the `map` of `migrate Channel v1 -> v2 { map "app" -> Mobile, … }`). The CLI reports
  the first failing assertion only. The other highlight files pass.

## 3. Preview (TEST check, run once to see if it works offline)

`python3 integrations/zed-beaml/preview.py --chat …/fates/channel_v2/orders.beaml`: exit 0, offline. The fragment has
no `<i class=k>map</i>`, so the planned check fails at HEAD. **[Inference]** `<i class=c>v2</i>` occurs twice already at
HEAD (the versions of the `migrate` line), so the "enum mark is `c`" part of the preview check has no test power. TEST
must check the `enum Channel v2` line itself.

## 4. EXPERIMENT 0005 N17 (guard)

```sh
python3 -B experiments/0005-prototype-fullstack/run.py run
```

Run `results/20261108T142521399517Z`: status `fail`. `exp0005-N17` = `pass` (5 sources, fmt twice each, exit 0, empty
stdout; `fmt-*` copies kept in the run dir). The only failure is `exp0005-N16: fail: ExUnit.AssertionError` (step
`test-n8`), the open fates-a2a RED (commit `fc4e3acf`), not a4. `lib/generated/orders.ex` and the sources are unchanged
(`git status`). N17 stays a guard until a3 lands a fate source in 0005.

## 5. Pins and limits

- No pin moved: no tracked `slice*/**.beaml` added; changed files are `slice6_fmt_test.py`, 0005 `run.py`, and the new
  untracked `test/corpus/fates.txt`, `test/highlight/fates.beaml` (outside every hash-guard glob).
- Not run: the full 0004 `run.py` (it runs `slice6_fmt_test.py`, now RED by design); 0001 `cargo test` (no Rust change).
- The `fmt_mark_follows_dl104` unit case is GREEN work. The RED depth probe was not run; **[Inference]** by construction
  a mark-only build still fails T3, T4, T6 (body) and a body-only build still fails T1, T2, T6 (mark).
- A PASS does not establish production readiness.

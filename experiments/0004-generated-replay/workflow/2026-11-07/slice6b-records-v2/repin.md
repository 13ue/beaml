# RE-PIN of the EFFECT byte guards after step 6a (slice 6b)

**[Observed]** 2026-11-07, git HEAD `0747c315` (step 6a GREEN), branch `main`. Not committed.
By: Opus (RE-PIN, slice6b-records-v2) for every entry in this file.

## Result

- **FINDING.** Not every hunk is in the five named functions. Each changed EFFECT output also changes `Replay.run/3` (the REPLAY RUN chain) in 2 lines.
- The task rule says: do not re-pin a source with a hunk elsewhere. All 31 sources with a change and the 21 B5 texts have this hunk.
- Thus the re-pin is **not applied** to the working tree. The test files in the repository are unchanged.
- **[Verified] Later (DOCS, 2026-11-07):** commit `1bd1217b` applied this re-pin; its message accepts the `Replay.run/3` hunk as part of the 6a change. By: Opus (DOCS, slice6b 6a+11)
- The re-pin is prepared as [repin.patch](repin.patch). It was tested in a scratch git worktree at `0747c315`. Counts are below.
- **[Inference]** The `Replay.run/3` hunk is the GREEN change `emit_chain (REPLAY RUN)` in [notes.md](notes.md#changes-in-mainrs-functions) (D6B-60). It only adds `keys` to the two call sites of `body/1` and `__beaml_result_E`. The OWNER or the main agent decides if this hunk is in scope.

## Compilers

| Name | Commit | Use |
|---|---|---|
| BASE | `f29e3f12` | slice 5 base compiler, old source text |
| PRE 6A | `4a7cffba` | last compiler before step 6a; `experiments/0001-syntax-to-beam` last changed at `3b76596d` |
| HEAD | `0747c315` | step 6a GREEN compiler (working tree, `main.rs` unchanged) |

Each was built with `git archive <commit> experiments/0001-syntax-to-beam | tar -x -C <scratch>` and `cargo build --offline --quiet --manifest-path <scratch>/experiments/0001-syntax-to-beam/Cargo.toml --target-dir <scratch>/target`. HEAD is the repository build (`target/debug/beaml-spike`, `BEAML_SPIKE` set to it for the scripts).

## Diff proof

Method: compile each source with PRE 6A and HEAD, `--stored stored/empty.jsonl` when the source has `effect` or `retire`. Compare stdout line by line (`difflib`). Give each changed line the nearest `def`, `defp` or `defmodule` above it. Also compare BASE (old source, after `shift_offsets`, `normalise`, `without_last_step_warnings` as in A2) with PRE 6A and with HEAD. Scripts: `inventory.py`, `runcheck.py`, `b5check.py` in the session scratchpad (not retained).

**[Observed]** Sources: the 47 A2 sources (`rewrite_sources()` at BASE). The 2 `EFFECT_OUTPUTS` sources are A2 sources.

| Group | Count | Hunks PRE 6A to HEAD | Functions |
|---|---|---|---|
| EFFECT sources, exit 0 | 31 | 10 each, same shape | see below |
| no EFFECT, exit 0 (`example.beaml`, `orders.beaml` 0002, `payments.beaml` 0002, `drift/*/payments.beaml`, `slice4/P`, `slice4/P+r`) | 8 | 0 | none |
| reject, exit 1 (`bad/*` 5, `slice3/D7`, `slice3/M-nodrop`, `slice4/B+r`) | 8 | 0 (stdout and stderr equal) | none |
| B5 for F01 (fixture and 20 TEMPLATE draws) | 21 | 10 each | see below |

**[Observed]** For every source: stderr PRE 6A equals stderr HEAD; exit codes are equal. BASE after the A2 normalisation equals PRE 6A byte for byte for each of the 39 sources with BASE exit 0. BASE to HEAD gives the same hunks as PRE 6A to HEAD.

The 10 hunks of each EFFECT output (line numbers of `arms/gen/orders.beaml`, PRE 6A / HEAD):

| # | Lines | Function | Change |
|---|---|---|---|
| 1 | 88-91 / 88-94 | `__beaml_project_E/1` (new), `__beaml_result_E` | new project helper before the result helper |
| 2 | 92 / 96-115 | `__beaml_project_E/1`, `__beaml_result_E` | project helper body, new `/1` wrapper, new `extra` parameter |
| 3 | 94 / 117-118 | `__beaml_result_E` | span `unknown_keys` is the sorted union with `extra` |
| 4-7 | 207-227 / 232-246 | `Replay.record/3` | project call, `version: 2`, `value`, `redacted`, `value_sha256`, body keys removed |
| 8 | 240-241 / 259-260 | **`Replay.run/3`** | `{:ok, bytes, keys} <- body(record)`; `__beaml_result_E(bytes, [record["type"],] keys)` |
| 9 | 257-265 / 276-282 | `body/1` | version 2 reader; its 2 new comment lines lie after `expect/3`, so the scan also names `expect` (no `expect` line changed) |
| 10 | 268 / 286-298 | `digest/3` (new) | the D6B-58 digest |

**[Observed]** `runcheck.py`: in all 31 sources, hunk 8 equals the PRE 6A lines with exactly two edits: `{:ok, bytes}` to `{:ok, bytes, keys}`, and `, keys` added as the last argument of `__beaml_result_E`. 11 sources have the chain form with `record["type"]`.

**FINDING (hunk 8).** `Replay.run/3` is not in the named set (`__beaml_project_E`, `__beaml_result_E`, `digest/3`, `Replay.record`, `body/1`). Re-pin held back for all 31 sources and B5.

## Prepared re-pin (repin.patch)

**`tests/slice6_pipe_test.py`** `EFFECT_OUTPUTS` (stdout SHA-256, `--stored stored/empty.jsonl`). `slice6_struct_order_test.py` reads the same dict.

| Source | Old (PRE 6A, equal to the pin) | New (HEAD) |
|---|---|---|
| `arms/gen/orders.beaml` | `25ecec1b54fc4949871b7485c9fe8243b06bfda637fa943ab2867adb0a2eb752` | `009d8ab3127b8734e14555d7c87cc337e438cda8ae583a7cbbb2c8d065c92343` |
| `slice2/reuse/orders.beaml` | `ba63e1e87474e8c435fa1b9eadbcb4bc050628ae07b12475e6e57b2b1f62e529` | `e7899cc35816804ac7a1d5f26654a7c23558a33e1403daa2023a942567650d31` |

**`tests/slice5_syntax_test.py`** F01 and A2. The file pins by commit (`BASE`). The HEAD compiler rejects the old syntax (`interface`, F2), so BASE cannot be swapped for `0747c315`. The patch keeps both intents:

- R-EQ: BASE (old source) against PRE 6A (`4a7cffba`, new source), with the same normalisation as before.
- Byte guard: PIN (`0747c315`, new source) against the working tree compiler: exit, stdout and stderr equal.
- `base_compiler()` becomes `compiler_at(commit)` with one build per commit.

## Commands

From the repository root (scratch worktree for the patch run). This Python has no pytest; the runner is `unittest`:

```
python3 -B experiments/0004-generated-replay/tests/slice6_pipe_test.py
python3 -B experiments/0004-generated-replay/tests/slice6_struct_order_test.py
python3 -B experiments/0004-generated-replay/tests/slice5_syntax_test.py
python3 -B experiments/0004-generated-replay/tests/slice6_record_test.py
python3 -B experiments/0004-generated-replay/tests/arms_test.py
```

## Counts

**[Observed]** With repin.patch, scratch git worktree at `0747c315` (removed after the run):

| File | Result |
|---|---|
| `slice6_pipe_test.py` | 12 tests OK |
| `slice6_struct_order_test.py` | 3 tests OK |
| `slice5_syntax_test.py` | 60 tests OK (F01 Fixture, F01 Template, A2 with 47 sources) |
| `slice6_record_test.py` | 5 tests OK |
| `arms_test.py` | 11 tests OK |

**[Observed]** Guard check: `BEAML_SPIKE` set to the PRE 6A compiler (a known byte change). F01 and A2 give FAILED (failures=33): 2 F01 and 31 A2, each at the PIN assertion only; R-EQ passes. `test_effect_fixture_outputs_stay_byte_equal` gives FAILED (failures=2). So a later byte change still fails.

**[Observed]** Repository working tree: the test files are unchanged. Without the patch, the 37 failures of the GREEN stay (33 `slice5_syntax_test.py`, 2 `slice6_pipe_test.py`, 2 `slice6_struct_order_test.py`).

Apply after a decision: `git apply experiments/0004-generated-replay/workflow/2026-11-07/slice6b-records-v2/repin.patch` from the repository root.

## Decisions

**Undo**
- → Held back the re-pin: `Replay.run/3` hunk is outside the named set (task rule). By: Opus (RE-PIN, slice6b-records-v2)
- → Diff proof against PRE 6A, plus BASE after the A2 normalisation. By: Opus (RE-PIN, slice6b-records-v2)
- → Patch tested in a scratch git worktree, not in the shared tree. By: Opus (RE-PIN, slice6b-records-v2)
- → The `expect` name of hunk 9 is a scan artefact (comment lines). By: Opus (RE-PIN, slice6b-records-v2)

**Repair**
- → **Chose:** F01 and A2 as R-EQ against PRE 6A plus a byte pin against `0747c315`. **Over:** a stdout normaliser that rewrites the BASE record writer; a pin against `0747c315` only. **Because:** the HEAD compiler rejects the old syntax; a normaliser copies the generator; a pin only drops R-EQ. **Commits us to:** three compiler builds per `slice5_syntax_test.py` run; the 6a delta itself is proven here once, not by the test. By: Opus (RE-PIN, slice6b-records-v2)

# GREEN output: fates-a1 (syntax, checks, `--stored`)

**[Verified]** GREEN phase, 2026-11-08, base HEAD `fae530bd` (DL-162 commit). By: Opus (GREEN fates-a1). No commit.
Inputs: [plan.md](plan.md) with both repair sections, [decisions.md](decisions.md), [red-plan.md](red-plan.md) (incl.
"RED repair after RED review"), [red-review.md](red-review.md), DL-161, DL-162, the rulings of Fable on Q1 (previous enum
declaration in the source, card ENUM-V1-DECL) and Q2 (one `fate:` form), DL-166 scope ruling (a1b).

## 1. RED repair on HEAD

Scratch build: `git archive HEAD experiments/0001-syntax-to-beam`, `cargo build --release --offline`.
`BEAML_SPIKE=<scratch>/target/release/beaml-spike python3 -B experiments/0004-generated-replay/tests/slice6_fates_test.py`
→ 32 tests, all 32 fail, 89 failing subTests, 0 errors ([red-repair-run-head.log](red-repair-run-head.log)).
Every new form fails at the parser (`unsupported migrate step: quarantine|map`, `expected '{'` for `enum E vN`); the
guards pass (S3b `stricter_v1`, `channel_v1`; S5 "no variant"; F7 / F7b setup controls). Test file sha256
`001bd84f…`; fixtures `channel_v2` `3b45d516…` (now with `enum Channel v1`), new `channel_swap` `3a1be772…`, others unchanged.

## 2. `fmt` on the fixtures

HEAD `fmt` on copies: `stricter_v1`, `channel_v1` exit 0, byte-equal; the other five exit 1 (parse error), as RED said.
New binary: all seven exit 0; a second run prints nothing (idempotent). The first run changes three files: it removes
`type Amount v2` (`amount_v2`, `two_ctor`) and `type Order v3` (`order_map`), the DL-104 `fmt_mark` rule for a chain that
starts at v1. `enum E vN` marks stay. Not changed in a1 (fmt is a4); fixtures stay as they are (S3 needs the mark). GF-12.

## 3. `main.rs` changes (sha256 `367d0f0e…`)

| Place | Change |
|---|---|
| `Change`, `fate_text`, `Fate`, `Literal`, `variant_of`, `EnumTable` | new variants `Quarantine(Option<field>, Option<literal>)`, `Map(Option<field>, old, V)`, `Redact`, `Retire`; `Change::fate`; source text of a fate line |
| `Program` | `enum_marks`, `old_enums` (older `enum E vK` declarations, ruling on DL-161) |
| `Parser::change` | `quarantine f`, `quarantine "old"`, `quarantine f "old"`, `map [f] "old" -> V` (payload: parse error `a map target takes no payload (QF-6 A)`), `redact f`, `retire f keep N days`; unknown-word text names the fate words (GF-10) |
| `Parser::program` `enum` | optional VERSION MARK; two marked declarations of one enum: the newest is the enum, older ones go to `old_enums` |
| `derive_versions`, `enum_chain`, `empty_step`, `mark_agrees(kind, …)` | enum chains: gaps, `enum` mark text (F8), K8 text with "fate line" (PF-05), PF-06 text with quarantine; record chains skip fate lines in K7 and in the shape derivation |
| `Checker::fates`, `fate_literal`, `fate_once` | F5 checks (PF-07 to PF-11, RF-02, RF-04 to RF-06, DL-161 GF-04, DL-162), the old-declaration rules (GF-01, Q1 ruling), PF-09 texts |
| `enum_newest`, `prev_table`, `fate_in`, `literal_fate`, `ctor_fate`, `literal_verdict`, `failing_param`, `help_literal`, `record_lines` | lookup helpers; PF-21 parameter mirror (`ponytail:` comment) |
| `ValueChecks` | `moved` (DL-140 / DL-161), `fated` (record lines per fate line), `params` (PF-21) |
| `value_checks` | literal fields through `literal_verdict`: lost, moved, fated or fine |
| `value_errors` | DL-155 helps per site (RF-09, GF-06), the moved block (GF-03), `quarantine` lifts a failed constructor rule after the Elixir run, `fate:` lines (beside a block, GF-05, or into the notes) |
| `check_entries` | fills a `ValueChecks` and calls `value_errors` (GF-07) |
| `dead_lines` | a step with a fate line is never a DEAD LINE (ruling on O1) |
| `build_with_refusals` | a1 stop lines (RF-01) when a `fate:` line is hit |
| `emit_chain` | fate lines emit nothing (`ponytail:`, fates-a2) |

PF-16: codegen changes only through the steps of sources with fate lines; no shared helper changed. Fate lines are a
`--stored` check only.

## 4. Checks

```
cargo build --release --offline; cargo build --offline                       ok
cargo test --offline                                                         22 + 14 passed
cargo clippy --offline -- -D warnings                                        ok
cargo fmt --check                                                            ok
python3 -B experiments/0004-generated-replay/run.py   (run 1)                {"run": ".../results/20261108T103046767011Z", "status": "fail"}
python3 -B experiments/0004-generated-replay/run.py   (run 2)                {"run": ".../results/20261108T105029441772Z", "status": "pass"}
python3 -B experiments/0005-prototype-fullstack/run.py db-up                 {"run": ".../results/20261108T110939283073Z", "status": "pass"}
python3 -B experiments/0005-prototype-fullstack/run.py run                   {"run": ".../results/20261108T110946954003Z", "status": "pass"}
```

Run 1 failed only in `slice3-types` (`EMPTY_STEP`, the K8 token, GF-14); fixed, run 2 passes every step. The 0005 run
writes no tracked file (`app/lib/generated/orders.ex` unchanged). Toolchain: cargo 1.94.0, Python 3.13.12, Elixir 1.18.1.

Counts from run 2 (tests, result): slice6-fates 32 OK · slice6-db-stored 49 OK (3 skipped, as before) · slice6-entry 20 ·
slice6-stored-elixir 15 · slice6-decode 8 · slice6-db 15 (1 skipped) · slice6-decode-ctor 8 · slice6-m4 14 ·
record-v3 26 (1 skipped) · redteam-c1 8 · redteam-c3 5 (C4 passes: the new step is in `run.py`) · slice3-types 69.

## 5. Pins

| Site | Moved? |
|---|---|
| `slice6_pipe_test` `EFFECT_OUTPUTS`, `slice6_host_struct_test` `BYTE_GUARD`, `effect-reach/byte-guard.json` (digest) | no: steps pass unchanged |
| `slice5_syntax_test` `PIN`, `slice6_entry_test` / `slice6_multi_test` `BASE`, `slice6_db_test` `P4_BASE` (hash) | no: steps pass unchanged |
| `record_v3_test` V18b | re-pinned: `HELP_REPIN`, five pairs change only the help line (GF-08; the plan said four) |

Help constants changed (text change only): `slice6_db_stored_test` (`CTOR_HELP_PREFIX` new, `LITERAL_HELP`; `HELP_PREFIX`
stays for shape faults), `slice6_entry_test` (`CTOR_BLOCK`, `LITERAL_BLOCK`), `slice6_stored_elixir_test`
(`CTOR_FAILS`, e6, `LOST_LITERAL`), `slice6_db_test` (`LITERAL_BLOCK`), `slice6_decode_ctor_test` (`help_quarantine`,
`help_literal`, `HELP_ENUM_NOMATCH`, `HELP_ENUM_FAIL`; `HELP_MIGRATE` stays for shape faults), `record_v3_test` V14b,
`redteam_c1_test` `FAILS`, `slice6_m4_test` (`CTOR_HELP_PREFIX`), `slice3_types_test` `EMPTY_STEP`.
`slice6_decode_test` 214 (no variant) and `slice6_m4_test` `rename_text` unchanged.

## 6. Limits

- **[Verified]** A hit fate line exits 1 with the a1 stop line; nothing runs at run time (a2).
- **[Inference]** GF-02: the swap check compares with the table of the version before the newest only (QF-2).
- **[Unknown]** GF-11: the SQUASH block of the Q1 ruling is not built (no per-value enum version).
- **[Verified]** fmt removes `type T v2` on a chain from v1 (GF-12, a4).
- `slice6_db_stored_test` keeps two `skip` cases that name DL-140 and the missing `map` form; a2 or later revisits them.
- DL-166 (rename onto an enum or constructor field) is not in a1: step a1b (GF-13).
- A PASS does not establish production readiness.

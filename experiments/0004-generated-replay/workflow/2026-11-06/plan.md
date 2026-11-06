# Plan: EXPERIMENT 0004, slice 1 (revision 3)

**Task.** Owner decisions 2026-11-06 replace revision 2. GEN: `effect` with `http.post`, one `!` failure TYPE, `|>` with failure pass-on, generated decode, `Replay.record`, `Replay.run`, flow `place` in BEAML. LIB in parallel, no kill switch. Cases (a)–(f): [README](../../README.md#slice-1-acceptance-cases-in-order). Test-first applies.

**Files**
- Compiler: `experiments/0001-syntax-to-beam/src/main.rs` (lexer: `|>`, `!`, dotted names; parser: `effect`, pipe body; checker: pipe TYPES and `!` list; emit), `tests/cli.rs`.
- Fixtures: `experiments/0004-generated-replay/arms/gen/orders.beaml` (README source), `bad/*.beaml` (5 negatives), `drift/{R,N,Q}/` (both BEAML files).
- Router (GEN overlay): `arms/gen/router.ex` calls `OrdersBeamlSpike.place/1`; delete `payment_http.ex`, `replay.ex`; changed `query.py` lines.
- LIB overlay: `arms/lib/replay_lib.ex` (≤ 60 lines), `replay_descriptor.ex` (≈ 15), one `ReplayLib.record` call in `payment_http.ex`; delete `replay.ex`.
- Tests: 0003 `tests/*.py` get one root parameter (default 0002 tree). New `0004/run.py` (overlay builds), `tests/arms_test.py` (c, d, e), `tests/drift_test.py` (f).
- Unchanged: 0002 tree, `probe_support.ex`, `payments.beaml`, 0003 runner.

**First failing test**
- `orders_cli_accepts_effect_pipe_place` (cli.rs): compile the slice 1 source, expect exit 0 and `def place(`. RED: "expected interface, enum, or fn", no stdout.
- LIB in parallel: `test_lib_arm_replays_matrix` with `arm=lib`. RED: `ReplayLib` undefined.

**Minimal changes, in order (GEN)**
1. (a) Lex and parse `effect NAME T -> T ! E = http.post("path")` and a pipe body. Check each step: known fn or EFFECT, input = previous output, every step failure in the `!` list (message names step and TYPE). Reject non-`http` kinds.
2. (a) Five negative CLI tests: unknown fn, TYPE mismatch, undeclared failure, field not in TYPE, `db.get`.
3. (b) Emit `place/1`, `payments_authorize/1` (gen_tcp, 0002 framing, `ProbeSupport` spans and counter), typed decode, `PaymentError` struct, `Replay.record/3`, `Replay.run/3`. Template control on DRIFT-R.
4. (c) GEN router and deletes; run 0003 live tests with the README assertion table.
5. (d) 8-case matrix on `OrdersBeamlSpike.Replay.run/3`, zero transport.
6. (e) LIB matrix (parallel worker, own directory). (f) DRIFT R/N/Q × 2 arms; outcome classes, change sites; apply pass and reject rule.

**Checks**
- `cargo test --offline --manifest-path experiments/0001-syntax-to-beam/Cargo.toml` (incl. 0003 gate 1).
- `python3 experiments/0003-source-linked-replay/run.py` (default root, control) and with the GEN and LIB roots.
- `python3 -B experiments/0004-generated-replay/tests/arms_test.py`; `tests/drift_test.py`.
- `payments.beaml` output byte-identical. `probe_support.ex` SHA-256 unchanged. `mix format --check-formatted`; generated Elixir with warnings as errors.
- Count replay lines and manual change sites per arm; domain validation and test edits apart.

**Exclusions.** `with`, `name!/n`, formatter alignment, db/queue/mail EFFECTS, second EFFECT, Q3, Q4, retries, timeouts, REPLAY CAPSULE, D001/D002 choices, Zed grammar, value gate, BAML arm.

**Glossary proposals (not added).** FAILURE TYPE (the TYPE after `!`), PIPE STEP, DRIFT, MANUAL CHANGE SITE, LIBRARY ARM, RESPONSE RECORD.

# Plan: EXPERIMENT 0004, slice 1 (revision 4)

**Task.** Owner decisions 2026-11-06. GEN: `effect` with `http.post`, one `!` failure TYPE, `|>` with failure pass-on, generated decode, `Replay.record`, `Replay.run`, flow `place` in BEAML. LIB: strongest fair library, built in parallel, frozen before GEN results are judged. Cases (a)–(f) with (d2): [README](../../README.md#slice-1-acceptance-cases-in-order). Revision 4 repairs the [review of revision 3](plan-review.md#review-of-revision-3). Test-first applies.

**Files**
- Compiler: `experiments/0001-syntax-to-beam/src/main.rs` (lexer: `|>`, `!`, dotted names; parser: `effect`, pipe body; checker: pipe TYPES and `!` list; emit incl. the `payment_request_prepared` event), `tests/cli.rs`.
- Fixtures: `experiments/0004-generated-replay/arms/gen/orders.beaml` (README source), `bad/*.beaml` (5 negatives), `drift/{R,N,Q}/` (both BEAML files).
- GEN overlay: `arms/gen/router.ex` calls `OrdersBeamlSpike.place/1`; delete `payment_http.ex`, `replay.ex`; copies of `query.py` and 0003 `tests/*.py` with the GEN rows of the README table; `assertion-changes.json`.
- LIB overlay: `arms/lib/replay_lib.ex` (≤ 60 lines, whole values, mandatory typed `rescue`), `replay_descriptor.ex` (≈ 10, no key list), one `ReplayLib.record` call in `payment_http.ex`; delete `replay.ex`; test copies with the LIB row; `assertion-changes.json`.
- New: `0004/run.py` (temporary tree with the repository layout, overlays, LIB freeze hashes), `tests/overlay_diff_test.py`, `tests/arms_test.py` (c, d, d2, e), `tests/drift_test.py` (f).
- Unchanged (control): 0002 tree, `probe_support.ex`, `payments.beaml`, `0003/run.py`, original 0003 tests.

**First failing tests**
- `orders_cli_accepts_effect_pipe_place` (cli.rs): compile the slice 1 source, expect exit 0 and `def place(`. RED: "expected interface, enum, or fn", no stdout.
- `test_overlay_copies_equal_change_table`: RED while the copies are missing.
- LIB in parallel: `test_lib_arm_replays_matrix` with `arm=lib`. RED: `ReplayLib` undefined.

**Minimal changes, in order (GEN)**
1. (a) Lex and parse `effect NAME T -> T ! E = http.post("path")` and a pipe body. Check each step: known fn or EFFECT, input = previous output, every step failure in the `!` list (message names step and TYPE). Reject non-`http` kinds.
2. (a) Five negative CLI tests: unknown fn, TYPE mismatch, undeclared failure, field not in TYPE, `db.get`.
3. (b) Emit `place/1`, `payments_authorize/1` (gen_tcp, 0002 framing, record before status check), exact-key typed decode, `PaymentError`, `Replay.record/3`, `Replay.run/3`, the prepared event. Template control on DRIFT-R.
4. (c) Overlay copies and `overlay_diff_test.py` first; then GEN router and deletes; `0003/run.py` in the GEN tree.
5. (d) 8-case matrix on `OrdersBeamlSpike.Replay.run/3`, zero transport.
6. (d2) R1 decode reject (missing key), R2 replay of the L1 record, L1 extra key → 502 [Proposal: reject], L2 503 → 502 with one record, P1 pipe stop. All: `finish` count 0.
7. (e) LIB: 8 cases, LIB copies, R1/R2/L1/L2 recorded; freeze hashes. Only then judge GEN (d2) and run (f).
8. (f) DRIFT R/N/Q × 2 arms against the frozen LIB; outcome classes, change sites; pass and reject rule.

**Checks**
- `cargo test --offline --manifest-path experiments/0001-syntax-to-beam/Cargo.toml` (incl. 0003 gate 1).
- `python3 experiments/0003-source-linked-replay/run.py` (control, originals); the same runner in the GEN and LIB trees.
- `python3 -B experiments/0004-generated-replay/tests/overlay_diff_test.py`; `arms_test.py`; `drift_test.py`.
- Originals of 0002 and 0003 unchanged by SHA-256. `payments.beaml` output byte-identical. `mix format --check-formatted`; generated Elixir with warnings as errors.
- Count replay lines and manual change sites per arm; domain validation and test edits apart.

**Exclusions.** `with`, `name!/n`, formatter alignment, db/queue/mail EFFECTS, second EFFECT, Q3, Q4, retries, timeouts, REPLAY CAPSULE, D001/D002 choices, Zed grammar, value gate, BAML arm, weak LIB form.

**Glossary proposals (not added).** FAILURE TYPE, PIPE STEP, DRIFT, MANUAL CHANGE SITE, LIBRARY ARM, RESPONSE RECORD, TEST COPY.

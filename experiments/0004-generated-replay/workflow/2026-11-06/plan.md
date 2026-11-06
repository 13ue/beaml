# Plan: generated REPLAY RUN against a library arm (EXPERIMENT 0004, slice 1)

**Task.** Revision 2 after [plan-review.md](plan-review.md) (BLOCK). Slice 1: case (a), case (b) and DRIFT on `payments.authorize` (`prepare`, `finish`). Arm GEN: the compiler emits `Replay.record` and `Replay.run` from a declaration with typed record fields. Arm LIB: a generic Elixir library plus a hand-written descriptor. Pass and reject rule: [README](../../README.md#pass-and-reject-rule). **GEN is blocked on Q1, Q2 and Q5.** LIB is not blocked. Test-first applies.

**Files**
- `experiments/0004-generated-replay/arms/lib/`: `replay_lib.ex` (≤ 60 lines), `replay_descriptor.ex` (≈ 15 lines), CAPTURE call in `payment_http.ex`.
- `experiments/0004-generated-replay/arms/gen/`: delete `replay.ex`, CAPTURE call to `OrdersBeamlSpike.Replay.record/3`, `orders.beaml` with the declaration.
- `experiments/0001-syntax-to-beam/src/main.rs`, `tests/cli.rs`: parse, resolve typed record fields, emit nested `Replay`.
- `experiments/0003-source-linked-replay/tests/replay_run_test.py`: arm parameter only (default: 0003 runner).
- New: `experiments/0004-generated-replay/run.py` (overlay builds), `tests/replay_arms_test.py`, `tests/drift_test.py`, `drift/{R,N,Q}/` BEAML derivatives.
- Read only: 0002 tree, `router.ex`, `probe_support.ex`, `payments.beaml`, 0002 `run.py`.

**Order (LIB first, kill switch)**
1. LIB: write library and descriptor (fresh worker, no GEN access). Run case (b) on LIB.
2. DRIFT on LIB: R, N, Q. Record outcome classes and change sites. If LIB catches all three with zero change sites, stop and apply the reject rule.
3. GEN case (a): parser, resolver, emitter. Payments output byte-identical (control).
4. GEN case (b): 8 cases, zero transport, `replay.ex` deleted.
5. DRIFT on GEN: R, N, Q. Same counts. Apply the pass and reject rule.

**First failing tests**
- LIB: `test_lib_arm_replays_matrix`: harness with `arm=lib`. RED: `ReplayLib` is undefined.
- GEN: `orders_cli_emits_typed_replay_record_and_run`: expect exit 0, nested `defmodule Replay do`, `def record(`, `def run(`, the `Order` and `Payment` field keys. RED: "expected interface, enum, or fn", no stdout.
- GEN negative: unknown function; request TYPE ≠ `prepare` output; response TYPE ≠ `finish` input; field not in TYPE (`request.amount`); no recorded field. Each: exit ≠ 0, clear error, no stdout.
- GEN template control: compile DRIFT-R; the emitted field set must contain `reference`.

**Checks**
- `cargo test --offline --manifest-path experiments/0001-syntax-to-beam/Cargo.toml` (incl. gate 1).
- `python3 -B experiments/0004-generated-replay/tests/replay_arms_test.py` (8 cases per arm, zero transport).
- `python3 -B experiments/0004-generated-replay/tests/drift_test.py` (3 derivatives × 2 arms; outcome class per build, new record, old record).
- `python3 experiments/0003-source-linked-replay/run.py` (5 steps, control, unchanged tree).
- SHA-256 unchanged: `router.ex`, `probe_support.ex`. `mix format --check-formatted`. Generated Elixir compiles with warnings as errors.
- Count per arm: replay lines (CAPTURE call, hooks, call site, caller checks, descriptor, library) and manual change sites per DRIFT. Domain validation and test expectation edits apart.

**Exclusions.** Second EFFECT, old-record policy (Q4), generated artifact check (Q3) → slice 2. Retries, timeouts, REPLAY CAPSULE, sampling (D003), Zed grammar, operator value gate, BAML arm. No D001 or D002 choice.

**Glossary proposals (not added).** EFFECT DECLARATION, GENERATED RUNNER, RESPONSE RECORD, HOST HOOK (as in revision 1). DRIFT: a BEAML-only TYPE or signature change with no edit to host replay code. MANUAL CHANGE SITE: one edited hunk in a hand-written file that an arm needs after a DRIFT. LIBRARY ARM: a generic host replay library with a hand-written descriptor.

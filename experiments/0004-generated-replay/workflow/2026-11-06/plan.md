# Plan: generated REPLAY RUN runner (EXPERIMENT 0004)

**Task.** The compiler emits the REPLAY RUN runner for `orders` from the BEAML declaration. See [README](../../README.md). **Blocked on Q1 and Q2** (syntax, hook contract). Test-first applies.

**Files**
- `experiments/0001-syntax-to-beam/src/main.rs`: parse and check the EFFECT declaration; emit nested `Replay` module.
- `experiments/0001-syntax-to-beam/tests/cli.rs`: new test `orders_cli_emits_generated_replay_runner`.
- `experiments/0002-http-correlation/apps/orders_api/priv/orders.beaml`: add the declaration.
- `experiments/0002-http-correlation/apps/orders_api/lib/orders_api/replay.ex`: delete (case c).
- `experiments/0003-source-linked-replay/tests/replay_run_test.py`: entry parameter only (default `OrdersApi.Replay.run`).
- New: `experiments/0004-generated-replay/run.py`, `tests/generated_replay_test.py`, `tests/second_effect_test.py`, `tests/schema_change_test.py`.
- Read only: `router.ex`, `payment_http.ex`, `probe_support.ex`, `payments.beaml`, 0002 `run.py`.

**First failing test.** `orders_cli_emits_generated_replay_runner`: compile `orders.beaml` with the declaration. Expect exit 0, one `defmodule BeamlSpike do`, one nested `defmodule Replay do`, `def run(`, the literal `payments.authorize`, and the six reason atoms. Genuine RED: the compiler rejects the new keyword ("expected interface, enum, or fn") with no stdout. Negative cases: unknown function name, request TYPE not equal to `prepare` output, no recorded field.

**Minimal changes, in order**
1. Parser and checker for the chosen form. Emit `Replay.run/3` (or `/4` per Q2) with the 0003 check order.
2. Payments output byte-identical (control).
3. Point the 0003 harness at `OrdersBeamlSpike.Replay.run`. Run the 8 cases (case b). Then delete `replay.ex` (case c).
4. Second EFFECT on the loopback stub (case d). SCHEMA change derivative (case e).

**Checks**
- `cargo test --offline --manifest-path experiments/0001-syntax-to-beam/Cargo.toml` (all, incl. gate 1).
- `python3 -B experiments/0004-generated-replay/tests/generated_replay_test.py` (8 cases, zero transport).
- `python3 experiments/0003-source-linked-replay/run.py` (5 steps, regression).
- SHA-256 unchanged: `router.ex`, `payment_http.ex`, `probe_support.ex`. `mix format --check-formatted`. Generated Elixir compiles with warnings as errors.
- Host-diff check for cases c, d, e: zero replay lines.

**Exclusions.** CAPTURE generation, retries, timeouts, REPLAY CAPSULE, sampling (D003), Zed grammar, value gate, BAML arm. No D001 or D002 choice.

**Glossary proposals (not added).** EFFECT DECLARATION: source that names an outbound EFFECT, its operation, request and response functions and recorded fields. GENERATED RUNNER: REPLAY RUN entry emitted by the compiler from an EFFECT DECLARATION. RESPONSE RECORD: the predecode CAPTURE record of one PROVIDER ATTEMPT (0003 format version 1). HOST HOOK: an existing host function that generated code calls under the GENERATED ABI.

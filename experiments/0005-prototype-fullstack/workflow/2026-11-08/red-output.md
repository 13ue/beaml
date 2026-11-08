# RED output: EXPERIMENT 0005 (PROTOTYPE), N-TESTS

**[Verified]** Solve/RED phase, 2026-11-08, HEAD b332b12c. Mapping and contract: [red-plan.md](red-plan.md).
By: Opus (RED exp0005) for every line of this file. Not committed.

## Commands

```
git archive HEAD experiments/0001-syntax-to-beam | tar -x -C <scratch>; cargo build -q   # in <scratch>/experiments/0001-syntax-to-beam
python3 -B experiments/0005-prototype-fullstack/run.py db-up
BEAML_SPIKE=<scratch>/experiments/0001-syntax-to-beam/target/debug/beaml-spike python3 -B experiments/0005-prototype-fullstack/run.py
python3 -B experiments/0005-prototype-fullstack/run.py db-down
```

Compiler sha256 `74203f7227851ea4425495d409b8e4749648bb5a6bf4cde932ad108c44e4c2f3`. Toolchain: Python 3.13.12, Elixir 1.18.1 / OTP 27, pg_ctl 17.11 (Postgres.app).

## Source proof (HEAD compiler, scratch, empty `rows.jsonl` + `responses.jsonl`)

| Source | Exit | stderr | Module |
|---|---|---|---|
| `orders.beaml` | 0 | `rows: 0 rows, 0 checked, 0 not decodable` | `defmodule Orders do`, `def ui_place(`, `ui_orders(`, `ui_note(`, `ui_notes(` |
| `variants/stricter` | 0 | rows line | `Orders`, 4 `def ui_` |
| `variants/no_place` | 0 | rows line | `Orders`, 3 `def ui_` (no `ui_place`) |
| `variants/note_v2` | 0 | rows line + DEAD LINE warning `migrate Note v1 -> v2` (no v1 row) | `Orders`, 4 `def ui_` |
| `variants/note_v2` + one Note v1 row | 0 | `rows: 1 rows, 1 checked, 0 not decodable` | the chain is live |

Without `--stored` the compiler stops: `stored TYPE VERSIONS unknown` (expected). Source sha256: orders `bba45329…8282`, note_v2 `ddd06aef…731c`.

## RED run [20261108T001345855302Z](../../results/20261108T001345855302Z/result.json)

| Step | Exit | Reason |
|---|---|---|
| truncate ×2 | 0 | |
| stored-orders | 1 | `** (Mix) The task "beaml.stored" could not be found` |
| gen-orders | 1 | no snapshot, no build; `lib/generated/orders.ex` not written |
| compile | 0 | host without BEAML wiring |
| test (phase A) | 2 | 26 tests, 10 failures, 8 excluded, 1 skipped |
| test-n8 | 2 | 4 failures |
| test-n7_seed | 2 | 1 failure |
| stored/gen note_v2 | 1 | no task |
| compile-note_v2 | 0 | |
| test-n7_read | 2 | 3 failures |
| final stored/gen orders | 1 | no task; nothing written, nothing left in `lib/generated/` |

**Use cases (20):** 18 fail, 1 pass (N13), 1 blocked (N9).

| Failure | Count | Tests | Genuine because |
|---|---|---|---|
| `FunctionClauseError` in `LiveViewTest.connect_from_static_token/3`, conn holds `no route found for GET /orders/new` | 13 | N2, N2c, N3, N4 ×2, N5, N6, N12, N8 ×2, N8b, N8c, N7 seed | no LiveView route (host) |
| `Mix.NoTaskError` `beaml.stored` | 2 | N1, N10 | no host snapshot task |
| `AssertionError` "the host runs no Note v2 module" | 2 | N7 read, N7b | gen note_v2 needs the task |
| `AssertionError` `left: []` (no Note rows) | 1 | N11 | earlier phases wrote none |
| pass | 1 | N13 | guard; scaffold already meets it |
| skipped | 1 | N9 | `blocked: fate slice (D036)` |

No failure comes from a compile error, a missing dep or a test typo: all test files compile under `mix test --warnings-as-errors`, and the 7 other host tests pass.

## Helper probes (not RED, harness check)

→ Host copy build (N1/N10 path) with the generated orders module: exit 1 in 1 s, deps reused; warnings `BeamlDb.put/3 is undefined`, `BeamlDb.list/3 is undefined`. So after GREEN adds the task, N1 still fails until `BeamlDb` exists.
→ `mix run` probe with a hand snapshot of the empty table: `psql_ids` `[]`, `provenance!` ok, `build("stricter")` exit 0 with the rows line, `assert_no_ddl!` true.

## Earlier runs (kept, not RED evidence)

→ `20261108T001114281442Z`: harness bug, `not nil` in my DataCase change (`ArgumentError` in every setup). Fixed to `!tags[:committed]`.
→ `20261108T001146639467Z`, `20261108T001257453187Z`: same RED; superseded (80 start events from excluded tests; empty hash list). Formatter now writes start at finish; run.py records the source hash also when the snapshot fails.
→ `20261108T001113667008Z`, `…001336230106Z`, `…001352742420Z`: db-up / db-down, pass.

## Limits

→ **[Inference]** N13 passes at RED: a guard, not behaviour RED.
→ **[Unknown]** The page markup and the `mix beaml.stored` contract are pinned by these tests; GREEN may find a LiveView detail (flash rendering, `push_navigate` return) that needs a test repair.
→ **[Inference]** N7 read, N7b and N11 fail through earlier steps; their own assertions run first after GREEN.
→ Result files hold the OS account name in paths (as in earlier runs). No stored value, no secret in any note.

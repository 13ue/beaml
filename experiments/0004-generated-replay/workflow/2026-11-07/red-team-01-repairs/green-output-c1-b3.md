# GREEN output: RED TEAM 01 repairs C1 and B3

**[Verified]** GREEN phase, 2026-11-07. By: Opus (GREEN red-team-01-repairs C1/B3).
Scope: D6B-187 (C1) and D6B-188 (B3) of [spec.md](spec.md). C3 and C4 are out of scope (see [green-output-c3-c4.md](green-output-c3-c4.md)).

## What changed

One file: `experiments/0001-syntax-to-beam/src/main.rs` (10 insertions, 4 deletions).

1. C1, `DRIVER`: one new `case` clause after the struct clause.
   `{:ok, {^type, variant, payload}} when is_binary(variant) and is_list(payload) -> IO.puts("ok")`.
   `type` is the `type` String of the call. Every other shape still raises. No `rescue`, `catch` or `try` (D6B-122).
   `run_elixir`, `parse_elixir_results` and `ctor_pick` are unchanged: the run error was only the raise in the DRIVER.
2. B3, `fn action`: the event line with its `\n` goes into one `String`, then one `write_all` on the `append(true)` file.
   A `ponytail:` comment names the ceiling (short line, local file system; a lock for a network file system).

## Test results

| Command | Result |
|---|---|
| `cargo fmt` | no change after the edit |
| `cargo clippy` | 0 warnings |
| `cargo test` | 21 + 14 passed, 0 failed |
| `tests/redteam_c1_test.py` | 8 of 8 OK (was 6 FAIL) |
| `tests/redteam_b3_test.py` | 1 of 1 OK (was FAIL) |
| `tests/slice5_syntax_test.py` | 60 of 60 OK |
| `tests/slice6_*_test.py` (14 files, without `slice6_entry_test.py`) | 228 of 228 OK |

`tests/slice6_entry_test.py` was not run: it holds the open RED of slice 6d.

## EFFECT bytes

No EFFECT byte change. The four pin sites (`slice5_syntax_test.py` PIN, `slice6_pipe_test.py` EFFECT_OUTPUTS, `slice6_host_struct_test.py` BYTE_GUARD, `slice6/effect-reach/byte-guard.json`) are unchanged and their tests pass.

## Decisions

**Repair**
→ One `case` clause in the DRIVER statt a separate enum branch in `parse_elixir_results`, weil the raise is in the DRIVER only. By: Opus (GREEN red-team-01-repairs C1/B3)
→ Guard `is_binary(variant) and is_list(payload)` statt a match on the exact variant list, weil the spec (D6B-187) names only that shape and C1h pins the wrong shapes. By: Opus (GREEN red-team-01-repairs C1/B3)
→ `format!` plus one `write_all` statt a `flock`, weil D6B-188 chose that shape; the `ponytail:` comment names the ceiling. By: Opus (GREEN red-team-01-repairs C1/B3)

**Undo**
→ No change to `run.py`, tests or pin sites. By: Opus (GREEN red-team-01-repairs C1/B3)
→ No commit; the main agent commits after its check. By: Opus (GREEN red-team-01-repairs C1/B3)

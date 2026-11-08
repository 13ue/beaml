# GREEN output: slice 6d, the ENTRY LINE (inbound EFFECT)

**[Observed]** GREEN phase, 2026-11-07, base git HEAD 0397d62e (N13 base compiler 857fb310). Inputs: [plan.md](plan.md) with Plan repair, [decisions.md](decisions.md), [red-plan.md](red-plan.md), [red-output.md](red-output.md), [red-review.md](red-review.md) ("Re-check after RED repair": PASS).
By: Opus (GREEN slice6d). No commit. `run.py` not run (TEST phase).

## Diff summary

`git diff --stat`: 4 files, +683 / -176. Most of the removed lines are moved code (decode and projection helpers).

| File | Change |
|---|---|
| `experiments/0001-syntax-to-beam/src/main.rs` | ENTRY LINE parse, checks, codegen, `--stored` over `entries.jsonl`, fmt row. Details below. |
| `slice6/entry/orders.beaml`, `slice6/entry/echo.beaml` | One line each: the second `fn Amount` clause gets the DL-083 column alignment (G6D-02). |
| `tests/slice6_entry_test.py` | N13 source filter (G6D-01); `AMOUNT_EMPTY` anchor for `STRICTER` (G6D-02); `import re`. |

`main.rs`, by part:

- **Parse.** `struct Entry` in `Program.entries`. In the `effect` branch, `|> f` after `kind("text")` makes the line an ENTRY LINE (DL-130). No new top-level word, so the fallback text and `slice5_syntax_test` F02 stay.
- **Checks** (`Checker::entries`, end of `validate`, R6D-03 order): one ENTRY LINE (D6B-147); `namespace.operation` name; transport `ui.event` only; target not a constructor (DL-120); target declared; one parameter; drift rule input, output, failure with `none` (DL-130); input TYPE without constructor, without MIGRATE CHAIN or VERSION MARK (D6B-130); literal enum fields need a keep-value variant; constructor fields need `name: String` signatures and pass `ctor_keeps`; a reaching target must be the flow of each EFFECT it reaches (D6B-129); `duplicate name: ui_<event>` (R6D-10); TYPE `Rejected` reserved (DL-133). `retires()` also rejects a RETIRE LINE for an ENTRY LINE operation.
- **Refactor, no byte change.** `decode_parts`, `plain_decode` and `emit_project` are moved verbatim out of `emit_effect` (parameter `ty` for `effect.output`). N13 proves equal bytes for 122 sources.
- **Codegen** (`emit_entry`): `defmodule Rejected` (`defstruct [:reason]`); the input TYPE decode through the shared helpers; `def ui_<event>(a0)`: root span `<service>.<op>` (`:server`, input `nil`), D6B-143 term check, JSON encode, decode, ENTRY RECORD write (flow targets only), target call. A reject raises `BeamlFailure` inside the span (`reason` attribute) and returns `{:error, %Rejected{reason: r}}` outside it. A pure source also gets `__beaml_attempt__` and `BeamlFailure`. The `{:error, reason}` clauses stand only with constructor fields (no dead-clause warning).
- **Replay** (`emit_replay_entry`, a `{entry}` slot in the `Replay` module that is empty without an ENTRY LINE): `entry_record/2` writes `"entries"` with the 14 keys of `ENTRY_KEYS` (`value: :null`, `unknown_keys: []` after a term check reject; `outcome`, `reason`); `entry/2` checks the operation, the digest (`body/1`), decodes the re-encoded `value` and runs `run/3`.
- **`--stored`** (`check_entries`): reads `entries.jsonl` beside the `--stored` file when it exists (R6D-04). Accepted records of the ENTRY LINE: DL-122 lost literals, DL-102 constructors (one Elixir run, D6B-105). Rejected records are counted, not checked (DL-138). A record without ENTRY LINE and without RETIRE LINE gives the DL-040 parity block, counting all records (R6D-15). ENTRY RECORD operations join the RECORD SNAPSHOT, so a RETIRE LINE for them is no DEAD LINE. The count line `N entries, K checked, M rejected at capture` goes to stderr as a note.
- **fmt.** ENTRY LINES join the EFFECT rows of `aligned` (R6D-06).
- **Spans.** A source with an ENTRY LINE needs a lowercase file stem (it names the root span), as an EFFECT source does.

## Commands and results

```sh
cd experiments/0001-syntax-to-beam
cargo fmt
cargo clippy --offline --all-targets -- -D warnings
cargo test --offline --no-fail-fast
cd ../0004-generated-replay
python3 -B tests/<file>   # each file below, one after the other
```

Toolchain: Elixir 1.18.1, Erlang/OTP 27.3.4 (as in RED).

| Check | Result |
|---|---|
| `cargo fmt --check` | clean |
| `cargo clippy --offline --all-targets -- -D warnings` | clean |
| `cargo test --offline --no-fail-fast` | 21 + 14 passed, 0 failed |
| `tests/slice6_entry_test.py` | 18 tests OK (34 RED subtests green; guards `test_h2`, `test_n13` green, N13: 122 sources) |
| `tests/slice5_syntax_test.py` | 60 tests OK |
| `tests/slice6_*_test.py` (16 files) | all OK: constructor 25, decode_ctor 8, decode 10, effect_reach 8, entry 18, enum 20, failure 22, fmt 25, host_struct 3, int 16, pipe 12, record 5, redacted_failure 8, redacted 20, stored_elixir 15, struct_order 3 |
| `tests/redteam_c1_test.py` | 8 tests OK |
| `tests/redteam_b3_test.py` | 1 test OK |
| `tests/redteam_c3_test.py` | 5 tests OK |
| `tests/drift_test.py` | 7 tests OK |

- **[Observed]** `elixirc` on the generated `orders`, `echo` and `count` modules without stubs: only "is undefined" warnings for the stub modules. No other warning.
- **[Observed]** No EFFECT byte changed: N13 green, and the four pin sites (`slice5_syntax_test` PIN, `slice6_pipe_test` EFFECT_OUTPUTS, `slice6_host_struct_test` BYTE_GUARD, `slice6/effect-reach/byte-guard.json`) are untouched and their tests pass.

## Where the tests and the ledger differ

- **N13 against N10.** `bad/transport_route.beaml` has an ENTRY LINE with `http.route(`, not `ui.event(`. N13 filtered by `ui.event(` and so required the pre-6d parse error, while N10 requires the new transport text. RED hid this, because both compilers were the HEAD build. See G6D-01.
- **N11 against DL-083.** The fixtures were not fmt-stable: **[Observed]** the pre-6d fmt (857fb310) aligns the two single-line `fn Amount` clauses (`fn Amount _,     ""       ->`). RED hid this behind the parse error. See G6D-02.
- **`type` key field order.** The test (`PLACE_TYPE`) and `entries.jsonl` hold the fields in source order; a RESPONSE RECORD `type` key sorts them (`sorted_fields`). The fingerprint is the same (it sorts). GREEN follows the tests. See G6D-03.

## Limits

- **[Inference]** An input TYPE and the EFFECT output TYPE that share a literal enum or a constructor TYPE get duplicate helper defs (`__beaml_literal_E`, `__beaml_from_T`); the same input and output TYPE duplicate `__beaml_decode_t`. No fixture has it. Upgrade: emit each helper once per TYPE.
- **[Inference]** A constructor or literal enum field below the top level of the input TYPE is not decoded through its constructor; such a value always gets the reject `decode` (no crash). Same limit as the outbound decode.
- **[Inference]** A pure target in a source with an outbound EFFECT writes no ENTRY RECORD and has no `Replay.entry` (G6D-04).
- DL-103 notes ("a literal maps a kept value now") are not given for ENTRY RECORDS. The count line is plural for one record ("1 entries").
- R1 (red-review, medium): a captured reject that a looser rule accepts now is not reported. Not closed: a test needs a replay of line 4 against a looser `Amount` and an OWNER answer on the expected result. Still open.
- R2 (red-review, medium): the `outcome`/`reason` key shape (R6D-13) and `unknown_fields` (R6D-05) are built as DL-139 defaults; they go to the OWNER walk-through.
- No `cargo` unit test for the ENTRY LINE (plan "entry_line_parses"); the 18 Python tests cover parse and checks end to end.

## Decisions

**Repair**

**G6D-01 · Repair · N13 selects sources by ENTRY LINE, not by `ui.event(`.**
Chose: the filter `^effect .*\)\s*\|>` (an `effect` line with `|>` after the call). Over: keep `ui.event(` (N13 and N10 then contradict each other on `transport_route`); change the fixture. Because: the N13 docstring says "every tracked source without an ENTRY LINE"; 122 sources stay in the guard (was 123, one ENTRY LINE source less). Commits us to: a later ENTRY LINE form without `|>` must change this filter.
→ By: Opus (GREEN slice6d)

**G6D-02 · Repair · The two fixtures take the DL-083 alignment of the `fn Amount` clauses.**
Chose: `fn Amount _,     ""       -> ...` in `orders.beaml` and `echo.beaml`, and the test anchor `AMOUNT_EMPTY` for `STRICTER`. Over: change fmt (changes the output of every source with aligned clauses); weaken N11 to the ENTRY LINE only. Because: **[Observed]** the pre-6d fmt makes the same edit; N11 says "fmt keeps the fixtures". The `bad/` copies keep the old spacing (no fmt test reads them). Commits us to: a fixture edit must stay fmt-stable.
→ By: Opus (GREEN slice6d)

**G6D-03 · Repair · The ENTRY RECORD `type` key lists the fields in source order.**
Chose: the order of the test and of `entries.jsonl`. Over: the RESPONSE RECORD order (sorted by field name). Because: the tests win; the `--stored` check reads `value`, not this list, and the fingerprint sorts. Commits us to: two field orders in two record streams until the OWNER sets DL-139.
→ By: Opus (GREEN slice6d)

**G6D-05 · Repair · Shared decode helpers instead of a second decode emitter.**
Chose: move the step 7/8 decode helpers, the plain decode and the projection out of `emit_effect` and call them for the input TYPE. Over: a copy for the input TYPE. Because: one decode for the outbound EFFECT, the live entry and the REPLAY RUN (D6B-132); N13 proves no byte change.
→ By: Opus (GREEN slice6d)

**G6D-06 · Repair · A reject raises `BeamlFailure` inside the root span.**
Chose: raise inside, `__beaml_attempt__` outside (D6B-133); a pure source gets its own `__beaml_attempt__` and `BeamlFailure`. Over: return the reject inside the span. Because: **[Observed]** the 0002 `ProbeSupport.span` sets outcome `error` only on a raise.
→ By: Opus (GREEN slice6d)

**G6D-07 · Repair · The ENTRY RECORD is written after the decode, before the target call.**
Chose: one write with `outcome` and `reason` from the decode result. Over: write before the decode (D6B-135 wording). Because: DL-138 needs the outcome in the record; `N8_record_kinds` still sees `entries` before `responses`.
→ By: Opus (GREEN slice6d)

**Undo**

→ G6D-04: a pure target in a source with an EFFECT writes no ENTRY RECORD and has no `Replay.entry` (default, open). By: Opus (GREEN slice6d)
→ G6D-08: the count line only when `entries.jsonl` exists beside `--stored`; then on every passing build, as a note on stderr. By: Opus (GREEN slice6d)
→ G6D-09: a stored ENTRY RECORD without `outcome` `accepted` or `rejected` is a block (`has no capture outcome`). By: Opus (GREEN slice6d)
→ G6D-10: a RETIRE LINE for the operation of an ENTRY LINE gets the existing "still declares effect" text. By: Opus (GREEN slice6d)
→ G6D-11: the term check also rejects Strings and keys that are not valid UTF-8 and improper lists (`:json.encode` would raise). By: Opus (GREEN slice6d)
→ G6D-12: the input TYPE also needs a keep-value variant for literal enum fields and `name: String` constructor signatures, with the outbound texts in the `effect <op>:` form. Not pinned by a test. By: Opus (GREEN slice6d)
→ G6D-13: R1 left open (no cheap test without an OWNER answer). By: Opus (GREEN slice6d)

**Migrate**

→ None new. G6D-03 joins R2 (DL-139 record layout) for the OWNER walk-through under DL-144: built default, open.

## TEST repair, 2026-11-07

By: Opus (GREEN repair slice6d), after the TEST BLOCK in [review.md](review.md) (O1 high, O2 and O3 medium). Rulings: Fable, under DL-144. No commit.

**O1 RED** ([test-repair-red.log](test-repair-red.log)). Compiler from `git archive HEAD` (9f101f95), run through `BEAML_SPIKE`.
- **[Observed]** `test_n10_rejects [nested_enum]` and `[nested_constructor]`: exit 0 with Elixir on stdout, expected exit 1 and the limit text. Genuine behavior RED.
- **[Observed]** Control `test_o1_top_level_enum_and_constructor_and_nested_record_accept_a_good_event` passes at HEAD and after GREEN (a guard against an over-wide check, not a RED).

**O1 GREEN, diff summary**
- `main.rs` (+24): `entries()` walks the plain record fields below the top level of the input TYPE; an enum or constructor field there is a compile error. Top-level constructor TYPEs are not walked (their decode is the constructor call).
- Text: `error: effect <op>: the <enum|constructor> field <T>.<field> below the top level of <input> is a slice 6d limit (DL-144)` and `help: move <T>.<field> to the top level of <input>; slice 6d decodes enum and constructor fields at the top level only`.
- `slice6/entry/bad/nested_enum.beaml`, `bad/nested_constructor.beaml` (new); `slice6_entry_test.py` (+18): two BAD_CASES rows, the `nested` text helper, the control test.
- **[Observed]** Probe (scratch): a field two levels down (`PlaceOrder.line.inner.channel`) names `Inner.channel`, exit 1.
- The limit note above ("same limit as the outbound decode") is superseded: the inbound case is now a build error, as outbound.

**Checks (observed, after GREEN)**

| Check | Result |
|---|---|
| `cargo fmt --check` | clean |
| `cargo clippy --offline --all-targets -- -D warnings` | clean |
| `cargo test --offline --no-fail-fast` | 21 + 14 passed |
| `slice6_entry_test.py` | 19 OK (was 18; N10 has 16 rows, N13 green) |
| `slice5_syntax_test.py` | 60 OK |
| `slice6_*_test.py` (16 files) | all OK: constructor 25, decode_ctor 8, decode 10, effect_reach 8, entry 19, enum 20, failure 22, fmt 25, host_struct 3, int 16, pipe 12, record 5, redacted_failure 8, redacted 20, stored_elixir 15, struct_order 3 |
| `redteam_b3` / `redteam_c1` / `redteam_c3` | 1 / 8 / 5 OK |
| `drift_test.py` | 7 OK |
| `scripts/lint_wiki.py` | 0 errors |

- **[Observed]** No EFFECT byte changed: the five pin sites are untouched and their tests pass (slice5 PIN, pipe EFFECT_OUTPUTS, host_struct BYTE_GUARD, `effect-reach/byte-guard.json` through effect_reach, entry N13 BASE).
- **[Observed]** One of 12 `slice6_entry_test.py` runs failed (1 failure, in the loop over all suites); the next 11 runs passed. The failing test was not captured. **[Unknown]** cause; a parallel worker or the N7 closed-port probe are candidates. Not reproduced.
- Full `run.py` not run (task rule).

**O2.** G6D-04 is Repair `(default, open)`, listed with G6D-03 and G6D-12 under "Slice 6d built defaults" in [owner-review.md](../../../../0005-prototype-fullstack/workflow/2026-11-07/owner-review.md).

**O3.** R1 and the ENTRY stream digest gap (`check_entries` does not verify `value_sha256`) are appended to D035 in [decisions to be made](../../../../../wiki/planning/decisions-to-be-made.md).

### Decisions

**Repair**
→ O1: nested enum or constructor field is a compile error statt decode it, weil the error is the smaller repair (TEST O1, ruling). By: Opus (GREEN repair slice6d)
→ Any enum below the top level is blocked, literal or not, statt literal enums only, weil a plain enum there has no decode either. By: Opus (GREEN repair slice6d)
→ G6D-04 raised Undo to Repair, `(default, open)`. By: Fable (ruling O2), recorded by Opus (GREEN repair slice6d)

**Undo**
→ The limit text cites DL-144 (the ruling's frame), not a new ID. By: Opus (GREEN repair slice6d)
→ Top-level constructor TYPEs are not walked for nested fields. By: Opus (GREEN repair slice6d)
→ The control also holds a nested plain record (the TEST accepted case). By: Opus (GREEN repair slice6d)
→ O3: R1 and the digest gap appended to D035. By: Fable (ruling O3), recorded by Opus (GREEN repair slice6d)
→ The single unreproduced entry-test failure is recorded, not chased. By: Opus (GREEN repair slice6d)

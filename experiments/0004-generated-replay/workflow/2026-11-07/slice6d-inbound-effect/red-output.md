# RED output: slice 6d, the ENTRY LINE

**[Observed]** 2026-11-07, git HEAD 857fb310. Plan: [red-plan.md](red-plan.md). Full log: [red-output.log](red-output.log).
By: Opus (RED slice6d).

## Command

```sh
git archive HEAD experiments/0001-syntax-to-beam | tar -x -C <scratch>
cargo build --offline --quiet   # in <scratch>/experiments/0001-syntax-to-beam
BEAML_SPIKE=<scratch>/experiments/0001-syntax-to-beam/target/debug/beaml-spike \
  python3 -B experiments/0004-generated-replay/tests/slice6_entry_test.py
```

Toolchain: Elixir 1.18.1, Erlang/OTP 27.3.4. The working copy of `main.rs` is not used (another worker writes it).

## Result

- 16 tests, 32 failing subtests, exit 1. Guards passing: 2 tests (`test_h2`, `test_n13`, 111 sources).
- Every failure has one reason: the HEAD parser stops at the ENTRY LINE (`expected identifier at byte N`, the byte after `ui.event(`). The same sources without the ENTRY LINE compile at HEAD (probe below).

| Test | Red subtests | Reason today |
|---|---|---|
| `test_n1_entry_line_gives_one_function` | 3 | parse error, exit 1 |
| `test_n1b_event_name_is_free_text` | 1 | parse error |
| `test_n2_to_n5_echo_runtime` | 1 (19 cases) | setup: compile exit 1 |
| `test_n4_count_runtime` | 1 (2 cases) | setup: compile exit 1 |
| `test_n5_to_n9_orders_runtime` | 1 (14 cases) | setup: compile exit 1 |
| `test_h1_host_build_with_the_entry_has_no_warning` | 1 | parse error |
| `test_n10_rejects` | 14 | parse error instead of the planned text |
| `test_n11_fmt_keeps_the_fixtures`, `test_n11b_...` | 4 | fmt exit 1, parse error |
| `test_s1`, `test_s2`, `test_s3`, `test_s3b` | 4 | parse error |
| `test_s4_no_stored_value_in_output` | 2 | no `stored ENTRY RECORD` block in stderr |
| `test_h2_host_build_without_the_entry_warns` | guard, passes | — |
| `test_n13_sources_without_an_entry_keep_their_bytes` | guard, passes | — |

## Checks against a false RED or a false pass

- **Base sources compile.** HEAD compiles `orders`, `echo`, `count` and every `bad/` source with the ENTRY LINE removed (exit 0). So the parse error is the only blocker.
- **Harness runs.** The three `checks.exs` scripts run (exit 0) against the HEAD module of each source without the ENTRY LINE. Each case fails with `UndefinedFunctionError` for `ui_echo/1`, `ui_count/1`, `ui_place/1` or `BeamlSpike.Rejected`, not with a script error.
- **Positive control.** A hand-written `BeamlSpike.ui_count/1` and `Rejected` struct make the two count cases and `DL133_rejected_shape` PASS. The harness can pass.
- **`test_s4` hardened.** A first run passed `test_s4` with the parse error (no stored word in it). It now also needs the block text in stderr, so it is red today.
- **Host probe.** `elixirc --warnings-as-errors` exits 0 with the undefined-function warning (R6D-11), so H1 and H2 read the warning text.

## Limits

- **[Inference]** Error texts, the `unknown_fields` key and the sibling `entries.jsonl` are RED decisions (R6D-04, R6D-05, R6D-07), not OWNER rules.
- **[Unknown]** Whether `Replay` `body/1` accepts `value: null`. `N9_nested_nil_...` tests it; the digest helper passes `:null` through `:json.encode/1`.
- No test for the MIGRATE STEP that frees the build (M1, Migrate) or for stored ENTRY RECORDS without an ENTRY LINE (M2).

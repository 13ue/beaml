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

## RED repair

**[Observed]** 2026-11-07, git HEAD 5aee6d47 (compiler from `git archive HEAD`, same command as above). Plan: [red-plan.md](red-plan.md) section "RED repair". Log: [red-repair-output.log](red-repair-output.log).
By: Opus (RED repair slice6d).

### Probe: a removed EFFECT with stored RESPONSE RECORDS (O3)

Source with no `effect`, snapshot with two `payments.authorize` records (status 200 and 503):

- Without a RETIRE LINE: exit 1, `error: stored RESPONSE RECORD of operation payments.authorize has no effect in the source`, `stored RESPONSE RECORDS of operation payments.authorize: 2`, help `retire payments.authorize keep <n> days`. The 503 record counts.
- With `retire payments.authorize keep 30 days`: exit 0, empty stderr.

So today's behaviour is defined (block, RETIRE LINE frees). R6D-15 pins the same for ENTRY RECORDS; no question needed.

### Result

- 18 tests, 34 failing subtests, exit 1. Guards passing: `test_h2`, `test_n13`.
- 32 failures keep the old reason (parse error at the ENTRY LINE, `expected identifier at byte N`). The changed `test_s1` to `test_s4` and the new runtime cases sit behind the same parse error.
- 2 new failures, both genuine:

| Test | Today | Expected |
|---|---|---|
| `test_s5_removed_entry_line_with_stored_entries_blocks` | exit 0, Elixir on stdout: HEAD reads no `entries.jsonl`, the entries are lost silently | exit 1, the parity block text |
| `test_s5b_retire_line_frees_the_removed_entry_line` | exit 0 with `warning: DEAD LINE: retire ui.place ...` (no stored record of `ui.place` known) | exit 0, no DEAD LINE |

### Checks against a false pass

- **[Observed]** The five `entries.jsonl` digests: lines 1 to 3 still match `value_sha256` of `stored_types_test`; lines 4 and 5 are computed by the same helper (line 5 over `null`).
- **[Inference]** A GREEN that checks rejects too fails `test_s1` (line 4 fails `Amount`), `test_s2` (4 records, not 3) and `test_s3` (line 4 holds `App`, 2 records). A GREEN that crashes on `null` fails `test_s1`.
- **[Inference]** `test_s5` fails a GREEN that skips orphan entries silently (today's output) and one that counts only accepted entries (3, not 5).

### Limits

- **[Inference]** The `outcome`/`reason` shape (R6D-13), the help line (R6D-14) and the orphan count (R6D-15) are RED decisions under DL-138, not OWNER rules.
- **[Unknown]** An accepted record with `value: null` (not written by D6B-145). Not tested.
- The DL-122 header still reads `TYPE PlaceOrder v1:`: it names the stored TYPE VERSION of the record, not a help step. Left as is.


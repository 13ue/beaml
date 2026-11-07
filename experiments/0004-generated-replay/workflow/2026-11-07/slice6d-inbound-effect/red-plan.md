# RED plan: slice 6d, the ENTRY LINE (inbound EFFECT)

**[Proposal]** Solve/RED phase, 2026-11-07, git HEAD 857fb310. Test file: `tests/slice6_entry_test.py`. Fixtures: `slice6/entry/` (orders, echo, count, `stored/`, `bad/`). Evidence: [red-output.md](red-output.md), [red-output.log](red-output.log).
By: Opus (RED slice6d) for every proposal in this file. No `main.rs`, `run.py` or byte-pin edit.

## OWNER answers in force (override plan.md)

- **DL-130.** `effect ui.place PlaceOrder -> Payment ! PaymentError = ui.event("place") |> place`. Drift rule: head TYPEs equal the fn TYPEs. No `on`.
- **DL-131.** `BeamlSpike.ui_place(params)`, one per ENTRY LINE. RED probes the host build.
- **DL-133.** `{:error, %BeamlSpike.Rejected{reason: "decode" | "constructor"}}`.
- **DL-134.** `--stored` also reads `entries.jsonl`; constructors and literals of the input TYPE; DL-124 text rule.
- **DL-132.** `//` comments; enum and type forms as in the slice 6 corpus.

## Plan N-tests mapped onto the answers

| Plan | Change by the answers | Test |
|---|---|---|
| N1 | `on` line becomes the `effect` line (DL-130) | `test_n1_entry_line_gives_one_function` (orders, echo, count) |
| — | event String is free text (R6D-02) | `test_n1b_event_name_is_free_text` |
| N2, N3 | none; `Channel` has `Web`, `App` and `Unknown(String)` | `test_n2_to_n5_echo_runtime` |
| N4 (+ repair) | reject is `Rejected` (DL-133); + nested atom key, struct, pid/ref/fun | echo and `test_n4_count_runtime` |
| N5 | span name from the head name `ui.place` (R6D-01) | `N5_root_span_and_children`, `N5_echo_root_span_only` |
| N6 | none | `N6_reject_inside_the_root_span` |
| N7 | none | `N7_domain_failure_passes` |
| N8 | + `unknown_fields` key (R6D-05) | `N8_*` (7 cases) |
| N9 (+ repair) | none | `N9_*` (5 cases) |
| N10 | texts in the `effect <op>:` form (R6D-07); event regex dropped (R6D-02); name text reused (R6D-10) | `test_n10_rejects`, 14 files in `bad/` |
| N11 | ENTRY LINE is an EFFECT line in fmt (R6D-06) | `test_n11_fmt_keeps_the_fixtures`, `test_n11b_...` |
| N12 | + no `ui.event(` and no stored value in events | every compile (`compile()`) |
| N13 | base 857fb310, 111 tracked sources (R6D-12) | `test_n13_...` (guard) |
| N14 | grammar parses E' today (R6D-09) | none in this RED |
| Existing assertions table | no new top-level word: `slice5_syntax_test` F02 and `cli.rs` line 208 stay unchanged | none |

## New tests from the answers

- **DL-130 drift rule.** `bad/drift_input`, `drift_output`, `drift_failure`, `drift_failure_head_none`, `drift_failure_fn_none`.
- **DL-131 host build.** `test_h1_...`: host module `handle_event("place", ...)` calls `ui_place`; no "undefined" warning. `test_h2_...` (guard): the same host against the source without the ENTRY LINE warns `BeamlSpike.ui_place/1 is undefined or private`.
- **DL-133.** `DL133_rejected_shape` (struct keys `[:reason]` only, also in a source without a failure TYPE); every N4 case through `Rejected`.
- **DL-134.** `test_s1_...` (three stored ENTRY RECORDS build; line 3 is a kept `Unknown`); `test_s2_...` (stricter `Amount` constructor, 3 records); `test_s3_...`, `test_s3b_...` (removed or changed `App` literal, line 2); `test_s4_...` (DL-124: the block stands in stderr and names no stored value).
- **Not written: a MIGRATE STEP that frees the build.** Migrate, see M1.

## Decisions

**R6D-01 · Repair · Names come from the head name.**
Chose: `ui.place` gives `ui_place`, the record `operation` and the root span `<service>.ui.place`, as `payments.authorize` gives `payments_authorize`. Over: names from the event String (D6B-131). Because: DL-130 "inbound like outbound". Commits us to: D6B-128 (`on` node), D6B-142 (grammar rule) and the fallback text change drop.
→ By: Opus (RED slice6d)

**R6D-02 · Undo · The event String is free text; no namespace rule on the head name.**
Chose: `ui.event("echo-order")` compiles. Over: the D6B-129 regex. Because: no generated name comes from the String now.
→ By: Opus (RED slice6d)

**R6D-03 · Repair · Check order for an ENTRY LINE.**
Chose: target kind (constructor), parameter count, drift rule, input TYPE rules, flow rule, name rules. Each `bad/` file breaks one rule only. Commits us to: GREEN keeps this order so each text is reachable.
→ By: Opus (RED slice6d)

**R6D-04 · Repair · `--stored S` reads `entries.jsonl` in the directory of S.**
Chose: a sibling file, as `ProbeSupport.Capture` writes `<kind>.jsonl` side by side; no file means no stored ENTRY RECORDS. Over: a second flag; ENTRY RECORDS inside S. Because: inside S a record of operation `ui.place` would reach the RESPONSE RECORD path (the ENTRY LINE is an `effect` now) and be checked against the output TYPE. Commits us to: `stored/empty.jsonl` has no sibling `entries.jsonl`.
→ By: Opus (RED slice6d)

**R6D-05 · Repair · The ENTRY RECORD also has `unknown_fields`.**
Chose: the names of enum fields kept as `Unknown` at capture, as in a RESPONSE RECORD since step 7. Amends D6B-135. Over: D6B-135 keys only. Because: DL-122 tells a kept value from a lost literal by this key. Without it, a stored `Unknown("phone")` blocks the build (false block, `test_s1`). Commits us to: one more key; `[]` after a term check reject.
→ By: Opus (RED slice6d)

**R6D-06 · Repair · fmt treats the ENTRY LINE as an EFFECT line.**
Chose: the DL-013 head normalization (single spaces). Supersedes D6B-140. Over: keep bytes. Because: DL-130.
→ By: Opus (RED slice6d)

**R6D-07 · Repair · Error texts.**
Chose: `effect <op>: ...` texts as in `BAD_CASES`; drift: `the <role> TYPE is <A> in the head but <B> in fn <f> (DL-130)` plus a help line, `none` for a missing failure TYPE. Stored blocks: the RESPONSE RECORD texts of DL-102 and DL-122 with `ENTRY RECORD`. Over: new texts for stored blocks. Because: one rule, one text.
→ By: Opus (RED slice6d)

**R6D-08 · Undo · A pure source with an ENTRY LINE needs no `--stored`.**
Chose: it writes no ENTRY RECORD (D6B-136), so there is nothing to check. A source with an outbound EFFECT needs `--stored` as before.
→ By: Opus (RED slice6d)

**R6D-09 · Undo · No grammar change and no corpus case in this RED.**
Chose: drop N14. Because: **[Observed]** `tree-sitter 0.26.5 parse --wasm` gives an `effect_declaration` with `body: (pipe left: (call ...))` for the ENTRY LINE, no ERROR. The CLI is not on PATH, so a test would depend on a scratch tool.
→ By: Opus (RED slice6d)

**R6D-10 · Undo · A fn `ui_place` gives the existing `duplicate name: ui_place`.**
Chose: the outbound text. Over: the D6B-138 text.
→ By: Opus (RED slice6d)

**R6D-11 · Repair · The host probe judges the warning text, not the exit code.**
Chose: H1 and H2 read elixirc stderr. Because: **[Observed]** Elixir 1.18.1 `elixirc --warnings-as-errors` exits 0 on warnings (also an unused variable). `Kernel.ParallelCompiler` ignores the option; only `mix compile` honours it. Commits us to: the [Unknown] in plan.md resolves as "warning, not error" for `elixirc`.
→ By: Opus (RED slice6d)

**R6D-12 · Undo · N13 source set.**
Chose: tracked `.beaml` under 0001, 0002 `apps/`, 0004 `slice*/`, `drift/`, `bad/` (111 files), without `ui.event(`. Over: all 2064 tracked files (1935 in `results/`).
→ By: Opus (RED slice6d)

## Migrate: stopped, not decided

**M1 · Migrate · Which MIGRATE STEP frees a stored ENTRY RECORD block?**
- **[Verified]** No fate form exists in the compiler (only `rename`, `add`, `drop`). The RESPONSE RECORD texts say "slice 6b has no MIGRATE STEP form" (DL-122), and DL-125 forms wait for a follow-up.
- **[Verified]** D6B-130 forbids a MIGRATE CHAIN or VERSION MARK on the input TYPE. The DL-102 help asks for "a MIGRATE STEP to a new TYPE VERSION of PlaceOrder". The two rules conflict.
- **Option A.** Parity with RESPONSE RECORDS: the block holds until the DL-125 follow-up; restoring the rule frees the build (`test_s1`); D6B-130 stays.
- **Option B.** 6d lifts D6B-130 for the input TYPE and builds DL-125 `quarantine f` / `map f "old" -> V` for ENTRY RECORDS.
- Why Migrate: it sets the fate syntax and the TYPE VERSION rule of the input TYPE for every later record stream (DL-134 reason).
- By: open, `13ue`. Question by Opus (RED slice6d).

**M2 · Migrate (note) · Stored ENTRY RECORDS whose ENTRY LINE is gone.**
- A RESPONSE RECORD without its EFFECT blocks with "has no effect in the source" until a RETIRE LINE. DL-134 does not say whether `retire ui.place keep N days` covers ENTRY RECORDS. Not tested.
- By: open, `13ue`. Question by Opus (RED slice6d).

## Out-of-scope finding

- **[Observed]** `elixirc --warnings-as-errors` is no gate in Elixir 1.18.1 (R6D-11). Every 0004 runtime harness that relies on it gets no warning check. Not changed here.

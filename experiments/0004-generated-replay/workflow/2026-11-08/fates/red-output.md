# RED output: fates-a1

**[Verified]** RED run, 2026-11-08. By: Opus (RED fates-a1). Plan: [red-plan.md](red-plan.md).

## Commands and toolchain

```
git archive 396405aa experiments/0001-syntax-to-beam | tar -x -C <scratch>/head      # main.rs sha256 460c3c31…, byte-equal to the working tree and to HEAD 7587e5f0
cargo build --offline --quiet; cargo build --release --offline --quiet               # in <scratch>/head/experiments/0001-syntax-to-beam
BEAML_SPIKE=<scratch>/head/…/target/release/beaml-spike python3 -B experiments/0004-generated-replay/tests/slice6_fates_test.py
BEAML_SPIKE=<scratch>/head/…/target/debug/beaml-spike   python3 -B experiments/0004-generated-replay/tests/slice6_fates_test.py
BEAML_SPIKE=<scratch>/probe/…/target/release/beaml-spike python3 -B experiments/0004-generated-replay/tests/slice6_fates_test.py
```

cargo 1.94.0, rustc 1.94.0, Python 3.13.12, Elixir 1.18.1 (OTP 27). HEAD moved from `396405aa` to `7587e5f0` during the
run (docs and site commits only); `main.rs` is the same file. Test file sha256 `e8cb6755…`, fixtures
`amount_v2` `8bb42259…`, `channel_v1` `c7b17fea…`, `channel_v2` `80cb34ba…`, `order_map` `a0d5c0da…`, `stricter_v1`
`55a54c24…`, `two_ctor` `0784b273…`.

Raw logs: [red-run-release.log](red-run-release.log), [red-run-debug.log](red-run-debug.log) (same 61 failures),
[red-probe-run.log](red-probe-run.log) (summary of the probe run), [red-probe.diff](red-probe.diff).

## Result

22 tests, 22 fail on release and on debug (61 failing subTests or tests, 0 errors). The setup controls inside F7 and F7b
(the `drop` step on nested `Amount` is a DEAD LINE and `--remove-dead` removes it) and the guards (S3b
`stricter_v1`, `channel_v1`; S5 "no variant") pass at HEAD, as planned.

`fmt` at HEAD: `stricter_v1` and `channel_v1` exit 0 and stay byte-equal. `amount_v2`, `channel_v2`, `order_map`,
`two_ctor` exit 1 with the same parse error as the build: the new forms cannot be fmt-checked before GREEN (a4 adds the
MIGRATE STEP body rule).

## Per test

| Test | Exit (HEAD) | Failing assertion | Why the failure is right | False-pass risk |
|---|---|---|---|---|
| F1 | 1 | `(0, True) != (1, False)`; `unsupported migrate step: quarantine … at byte 548` | the parser rejects `quarantine` | low: exit 0 and the module are needed |
| F2 | 1 | `expected '{' at byte 449` | `enum Channel v2` has no mark rule | low; the subTest writes `orders.beaml` so the module is `Orders` |
| F3 | 1 | `unsupported migrate step: map` | the parser rejects `map` | a parse-only build passes it (probe), by design: F3 is a build test |
| F4 | 1 | builds fail on parse; the empty step gives `… rename, add or drop` | K8 text names no fate line | low |
| F5 | 1 (each) | 20 subTests: `unsupported migrate step: …` or `expected '{' …` instead of the pinned text | no fate check exists | low: exact text per case; the payload case needs the parse text and a byte offset |
| F6 | 1 | `unsupported migrate step: redact` / `retire` | the parser rejects both words | low: exact PF-09 text |
| F7 | 1 | `amount_v2`, `channel_v2`: parse error instead of `rows:` only; `order_map`: exit 1 | the parser rejects the words | medium: the rule could pass by never firing W2 for nested steps at all; the setup control (a `drop` step must be a DEAD LINE) blocks that |
| F7b | 1 | quarantine copy: exit 1 (file unchanged because nothing ran) | parse error | covered: the expected exit is 0, so "nothing ran" cannot pass; the control proves removal works |
| F8 | 1 | `expected '{' at byte 449` | no enum mark | low: exact text with `enum` |
| S1 | 1 | told lines `[]` (only the parse error) instead of the `fate:` line and `NOT_BUILT_Q` | parse error | low: exact list; an a1 GREEN that keeps the DL-102 error fails (probe) |
| S1b | 1 (each) | only the help line differs: `declare the fate of these records … of Order (DL-102)` (entry: the D6B-130 help) | the DL-155 help is not built | low: the first two lines match today, so the test isolates the help |
| S1c | 1 | told `[]` | parse error | low |
| S1d | 1 | told `[]` | parse error | low; the ENTRY RECORD is written beside responses.jsonl as DL-134 reads it |
| S1e | 1 | the Tip block is missing (parse error) | parse error | low: on the probe the Amount error stands and fails the second check |
| S1f | 1 | the DL-122 block is missing (parse error) | parse error | medium: the test does not pin whether a `fate:` line is printed beside the block (RF-10) |
| S2 | 1 (both) | told `[]` | parse error | low |
| S2b | 1 (both) | only the help line differs (the D6B-39 text) | DL-155 enum help not built | low |
| S2c | 1 (both) | parse error | parse error | the "kept alone" subTest would pass on a parse-only build without DEAD LINE; the pair subTest (count 1, not 2) does not |
| S3 | 1 (each) | help line (no mark, type mark) or parse error (enum mark) | DL-155 help not built | low: the mark cases pin `v3` |
| S3b | 1 (2 of 4) | `amount_v2`, `channel_v2`: parse error; `stricter_v1`, `channel_v1` pass (guards) | parse error | the guards pass before and after, on purpose |
| S4 | 1 (each) | anchor missing: parse error, or the old help (no `declare the next TYPE VERSION`) | no fate line, no new help | low: the anchor prevents a pass on a parse error |
| S5 | 1 (2 of 3) | help line differs (DL-102 text) | RF-09 help not built | the "no variant" guard passes before and after |

## Depth probe (parse-only build)

**[Verified]** [red-probe.diff](red-probe.diff), 97 lines: the parser accepts and drops the fate lines and the enum mark,
K8 lets a fate-only step pass, `derive_versions` skips an enum chain. Release build of the patched scratch copy.

Result: 22 tests, 19 fail (55 failing subTests or tests). Passing on the probe: F1, F2, F3 (build tests only, as
expected). Failing, with the reason:

- **S1b, S2b, S3** (gate): the old DL-102 / D6B-39 help line. **S5**: the old DL-102 help.
- **S2c**: the pair gives the DL-122 block (no lift); "kept alone" gives a DEAD LINE warning on `migrate Channel v1 -> v2`.
- **F5**: every subTest; the wrong forms build or give another text (for example `quarantine nope` builds).
- **F4** empty step: the old K8 text. **F6**: exit 0 instead of the PF-09 texts. **F8**: exit 0 (no mark check).
- **S1, S1c, S1d, S2**: the DL-102 or DL-122 block stands, no `fate:` line, no stop line (the O2 "a1-only build" case:
  nothing exits 0 there). **S1e**: the Amount error stands beside the Tip error. **S1f**: old help.
- **F7, F7b, S3b** (fate variants): the W2 rule reports the fate step as a DEAD LINE; `--remove-dead` removes it.
- **S4**: the anchors (`fate:`, the new help) are missing.

So no test of the a1 behavior passes on parsing alone; only the three plain build tests do.

## Limits

- The help and error texts are RED defaults (RF-01 to RF-12, decisions.md), not OWNER texts. A GREEN that finds a
  better text changes the constant and records it; the structure (which site gets which exit) is the tested part.
- A compile error may carry `error: ` or not (both forms exist in `main.rs`); F5, F4, F6 accept both.
- The constructor check runs Elixir (D6B-105); a machine without Elixir fails S1b, S1e, S3, S5 for a setup reason.
- `redteam_c3_test` C4 fails in the full run until the GREEN adds the `run.py` step (DL-147).
- DL-160 (By: 13ue, committed during this run) supersedes DL-116 and closes M3; it changes the meaning of `redact` for
  fates-b only. a1 rejects `redact` (PF-09), so no a1 test changes. PF-24 ("DL-116 stays") is stale.

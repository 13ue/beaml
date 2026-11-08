# RED review: fates-a1b

**[Verified]** RED REVIEW, 2026-11-08, target RED commit `1e0e08df`. By: Opus (RED REVIEW fates-a1b).
Normal fresh review, not a Devil's Advocate. No commit, no test or production change.
Basis: [plan.md](plan.md) with "Repairs", [plan-review.md](plan-review.md), [red-plan.md](red-plan.md),
[red-output.md](red-output.md); DL-166, DL-172 in the [decision log](../../../../../wiki/planning/decision-log.md).

## Verdict

**GO to GREEN.** No critical or high objection. One medium objection (O1) and one note for GREEN.

## Re-run at HEAD (own run)

Binary: `git archive 1e0e08df experiments/0001-syntax-to-beam` into the scratchpad, `cargo build --offline`
(repo `main.rs` clean against HEAD).

| Run | Tests | Failures | Failing items |
|---|---|---|---|
| `slice6_m4_test.py` | 16 | 14 | N12 builds 4/4 subTests, runtime, stored 8/8 subTests, R3 |
| `slice6_fates_test.py` | 36 | 5 | S1g, S1h, S1i (value-clause subTest), S1j 2/2 |

Counts equal [red-output.md](red-output.md). All guards pass (S1i guard subTest, F5 with `two_fate_lines_one_field`,
N33, N34, R3b and the rest).

## Checks

- **[Verified] Failures are genuine.** All 14 m4 failures show the QM4-1 A text (`waits for the fate forms`, 14 hits
  in the log), no setup error. S1g / S1i / S1j fail because HEAD prints a `fate:` line and the a1 stop line where a
  block is wanted; S1h fails on the PF-11 "has two" error. All planned reasons.
- **[Verified] The 14 m4 tests assert the new positive behavior, not only the absence of the old text.** Builds:
  exit 0 and the module on stdout. Runtime: exact decoded values (`channel` Web, `amount` built), PASS per case.
  Stored: exact stderr lines (`counted(1, 1, 0)`, the DL-122 block for `TYPE Order v1` / `v2`, the ctor block with
  the `currency` help, the map `fate:` line plus `NOT_BUILT_M`). R3: an Elixir decode result compared by value.
  The RED probe (only `renamed_onto` removed) still fails all 7 old-row stored subTests, so the check deletion alone
  cannot pass them.
- **[Verified] False-pass paths are closed by sibling subTests.** "Skip missing keys" passes `web` but fails `tv lost`;
  `kept` by the newest name fails `tv kept`; a last-step-only or forward step walk fails `chain v1`; a walk that
  ignores `version` fails `chain v2` (wrong text); no ctor check fails `bad currency`.
- **[Verified] DL-172 and repair O1.** S1g, S1i and S1j assert exact lines (via `told`) with no `fate:` line; S1h and
  the S1i guard need real lifts, so a "never lift" GREEN fails. S1i pins first-match order. S1j pins the QB-2
  default "not lifted" and the `NO_LITERAL_HELP` text under both lines; the param names come from the signature
  (`value: String, currency: String`), so name and position agree.
- **[Verified]** Setup asserts guard every text replace (`swap` counts 1, `assertNotEqual`); no subTest is skipped
  silently.

## Objections

### O1 (medium): the order inside one step is not tested

- **Evidence.** Plan "Repairs" O2 specifies "inside a step undo the changes in reverse order". The chain subTests use
  one rename per step; `rename and map` has one rename. A rotation in one step (`rename a -> c, rename b -> a,
  rename c -> b`, the `slice2/rotation` shape) onto an enum field is not in the RED.
- **Consequence.** **[Inference]** A forward walk inside a step passes every RED test and reads the wrong key for a
  rotated enum field: a false block, or a false "fine" on another field's value.
- **Resolving test.** A subTest with two renames in one step whose order matters (e.g. `rename via -> ch, rename
  ch -> channel` in one step, if the checker accepts it; else a rotation). Add in TEST or a later RED; no block.

## Note for GREEN (not an objection)

- The O1 help pins (`record_v3_test.py` 173 to 175, `slice6_stored_elixir_test.py` 41) are not moved in RED, by plan.
  S1j forces the new help, so these pins fail after GREEN until moved. GREEN must move them in the same change and
  list them; TEST checks that no other `help_quarantine` use with a no-literal clause stays.

## Decisions

**Undo**
→ Verdict GO to GREEN; O1 medium, no block. By: Opus (RED REVIEW fates-a1b)
→ Own HEAD build from `git archive`, not the repo target. By: Opus (RED REVIEW fates-a1b)

**Repair**
→ Within-step order as a TEST-phase subTest statt a RED repair now, weil the chain subTests close the main walk errors and the case is medium. By: Opus (RED REVIEW fates-a1b)

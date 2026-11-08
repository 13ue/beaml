# TEST and review: fates-a1b

**[Verified]** TEST run, 2026-11-08, target GREEN commit `018cf1ea`. By: Opus (TEST fates-a1b).
Normal fresh review, not a Devil's Advocate. No commit. Basis: [plan.md](plan.md) with "Repairs",
[plan-review.md](plan-review.md), [red-review.md](red-review.md), [green-output.md](green-output.md); DL-166, DL-172.

## Verdict

**PASS.** No critical or high objection. Two medium gaps closed by new tests (O1, O2); one medium note (O3).

## Test changes (this phase)

| File | Change |
|---|---|
| `tests/slice6_m4_test.py` | subTest "order inside one step: K7 rejects a chain in one step" in `test_N12_rename_onto_stored` (RED review O1) |
| `tests/slice6_fates_test.py` | `test_S1k_either_tested_parameter_lifts`: clause `"0", ""`, row `{"0", ""}`; `quarantine value` and `quarantine currency` each lift (QB-1 built default PB-03) |

## Probes (scratchpad `git archive HEAD` trees; repo `main.rs` never edited, `git diff --quiet HEAD -- experiments/0001-syntax-to-beam/src` clean)

| Probe | Change in the probe tree | Result |
|---|---|---|
| head | none | m4 16 OK, fates 37 OK |
| fwd | `stored_key` walks the changes of a step forward | m4 16 OK (see O1: cannot fail) |
| first | `tested_params` keeps only the first literal parameter | fates: S1k `[quarantine currency]` FAIL, rest OK |
| nokey | `stored_key` returns the newest name | N14 gen over the 0005 snapshot: exit 1, "no variant of Channel for field source" |

## Runs

| Command | Result | Result dir |
|---|---|---|
| `python3 experiments/0004-generated-replay/run.py` | pass, 40/40 steps, 781 tests (780 + S1k) | `experiments/0004-generated-replay/results/20261108T121801888868Z` (sub-run dir `20261108T122018584962Z`) |
| `python3 -B run.py db-up` (0005) | pass | `experiments/0005-prototype-fullstack/results/20261108T123540407690Z` |
| `python3 -B run.py run` (0005) | pass, 19/19 steps, use cases 22 pass + 1 blocked (N9), acceptance empty; N14 pass, stderr exactly `rows: 2 rows, 2 checked, 0 not decodable`, `written: false` | `experiments/0005-prototype-fullstack/results/20261108T123541367741Z` |

No failed run in this phase.

## Review checks

- **[Verified] stored_key.** Chain v1 and v2 rows, rename + map in one step, `kept` by the old key (`tv kept`), ctor field
  by the old key (`bad currency`): all tested in `test_N12_rename_onto_stored`. N14 is no false pass (probe nokey).
- **[Verified] QB-1.** Was untested (no two-literal clause, plan §9). Closed by S1k; probe first fails it.
- **[Verified] QB-2.** S1j: both `quarantine value` and `quarantine currency` leave the `Code` rule blocked with
  `NO_LITERAL_HELP`. HELP_REPIN and CTOR_FAILS moved to `help_no_literal`; they pass in the 0004 run.
- **[Verified] Several quarantine lines per TYPE.** S1h (PF-11 text removed). RF-04 still errors:
  `two_fate_lines_one_field` passes.
- **[Verified] Byte pins.** No pin file in the GREEN diff or the work tree; their tests pass in the 0004 run.
- **[Verified] N14.** `run.py` compares the whole stderr to the one count line; exit 0 alone does not pass.

## Objections

### O1 (medium, closed): order inside one step

- **Evidence.** K7 (`main.rs` type_versions) names a field at most once per MIGRATE STEP. `rename via -> ch, rename
  ch -> channel` in one step is rejected. So one name matches at most one `rename` of a step, and its old name
  matches no other: forward and reverse walks give the same key. Probe fwd passes all tests.
- **Consequence.** **[Inference]** A forward walk cannot be made to fail while K7 holds; the RED review O1 risk
  does not exist today. It returns if K7 is relaxed.
- **Resolving test.** The new subTest pins K7 for this shape. If K7 changes, that subTest fails first.

### O2 (medium, closed): QB-1 "either" untested

- **Evidence.** No fixture had a clause with two literals. **Resolving test.** S1k (probe first fails it).

### O3 (medium, note): QB-2 help on a mirror miss

- **Evidence.** `tested_params` returns empty also when no Rust-mirrored clause matches (green-output Undo 3);
  the help then says "tests no parameter with a literal", which is wrong for a guard or Int pattern the mirror
  cannot read. **Consequence.** A misleading help, no wrong build (no lift either way). **Resolving test.** When a
  new pattern kind enters (the `ponytail:` note at `tested_params`), add a case for its help text.

## Limits

R3, R4 stay excluded. QB-1, QB-2 stay open for the OWNER; S1k and S1j pin the built defaults only.

## Decisions

**Undo**
→ Verdict PASS; O1, O2 closed by tests, O3 noted. By: Opus (TEST fates-a1b)
→ Probes in scratchpad trees statt edit and restore of repo `main.rs`. By: Opus (TEST fates-a1b)

**Repair**
→ K7 guard subTest statt a forward-walk-failing subTest, weil K7 makes a failing one impossible to write. Commits us to: revisit stored_key order if K7 changes. By: Opus (TEST fates-a1b)
→ Added S1k (QB-1) in TEST statt leaving it to OWNER review, weil the built default had no test. By: Opus (TEST fates-a1b)

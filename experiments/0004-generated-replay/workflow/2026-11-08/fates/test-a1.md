# TEST and review: fates-a1 (GREEN `d9c1fac0`)

**[Verified]** TEST phase, 2026-11-08, HEAD `d9c1fac0`. By: Opus (TEST fates-a1). Normal fresh review, not a Devil's
Advocate. No commit, no production change. Job bus: `fates-a1-test`.

## Verdict

**PASS.** No critical or high objection. One medium objection is recorded below; it does not block.

## Commands and result dirs

| Command | Result |
|---|---|
| `python3 experiments/0004-generated-replay/run.py` | `experiments/0004-generated-replay/results/20261108T111157964364Z`, status pass, 40 of 40 steps pass |
| `python3 -B experiments/0005-prototype-fullstack/run.py db-up` | `experiments/0005-prototype-fullstack/results/20261108T112915816350Z`, pass |
| `python3 -B experiments/0005-prototype-fullstack/run.py run` | `experiments/0005-prototype-fullstack/results/20261108T112920757345Z`, pass |

The runs changed no tracked file (`git status`: only the two review-site feedback files, modified before this phase).

## Counts (0004 run, from the step stderr)

slice6-fates 32 OK · slice6-db-stored 49 OK (3 skipped) · slice6-entry 20 · slice6-stored-elixir 15 · slice6-decode 8 ·
slice6-db 15 (1 skipped) · slice6-decode-ctor 8 · slice6-m4 14 · record-v3 26 (1 skipped) · redteam-c1 8 · redteam-c3 5 ·
slice3-types 69. The counts equal the GREEN run 2 counts in [green-output.md](green-output.md).

## Review checks

- **Pins.** The commit changes none of `slice6_pipe_test`, `slice6_host_struct_test`, `effect-reach/byte-guard.json`,
  `slice5_syntax_test`, `slice6_multi_test`; the `slice6_entry_test` and `slice6_db_test` hunks touch no `BASE` /
  `P4_BASE` line. Only `record_v3_test` V18b moves: `HELP_REPIN`, five pairs, help line only, with a setup assert that
  the base help line occurs once. **[Verified]**
- **RED file.** `slice6_fates_test.py` sha256 `001bd84f…` equals the RED-repair file run on HEAD
  ([red-repair-run-head.log](red-repair-run-head.log): 32 of 32 fail before `main.rs` changed). No test would pass
  with the feature removed. **[Verified]**
- **Exit codes.** A hit fate line exits 1 with the a1 stop line (`build_with_refusals`); a line no value hits exits 0
  (S3b, W3). A db source without `--stored` exits 1 (probe), so a fate line never builds without the store check.
- **`fate:` form.** One form `fate: N stored NOUN[S] of PLACE quarantined|mapped by migrate E vA -> vB (LINE)`; counts
  per record line (a `BTreeSet`, so a list record counts once); beside a block the lines stand first (GF-05).
- **ENUM-V1-DECL.** An enum step without `enum E vK` gives the loud `enum Channel v1 is not declared …` error (F5,
  W4); an old declaration without its step gives GF-01.
- **DL-161 swap.** Probe: a `"web"` row on `channel_swap` blocks with the DL-140 text that names both variants
  (observed). W1 to W4 pin both literals, both-line lift, one-line partial lift, and the old-table rule.
- **DL-162.** `quarantine "app"` (bare, rows and ENTRY RECORDS) and `quarantine channel "app"` (owner step) park the
  literal (Q1, Q2); `quarantine channel` without a literal is an error naming the DL-162 form (F5).
- **Lift scope.** Probe: a `map` line does not lift a failed `Amount` rule (observed). S5b, S2d pin the other direction.

## Objections

1. **Medium · `quarantine value` parks any failed rule of the constructor TYPE, also the rule of another parameter.**
   Probe (observed): `amount_v2` with a row `currency: ""` (the `_, ""` rule, already in v1) prints
   `fate: 1 stored ROW … quarantined by migrate Amount v1 -> v2 (quarantine value)`. Without the line, the help for the
   same row says `quarantine currency` (PF-21, S1b `rows_currency`), but PF-11 allows one line per constructor TYPE.
   Consequence: a row that broke an old rule is parked under a line that names another parameter; the help suggests a
   parameter choice that the lift ignores. Visible in the count and blocked by the a1 stop line, so not high.
   Smallest test: `AMOUNT_V2` + `row(NO_CURRENCY)`; pin either the PF-11 whole-constructor lift (and a help that does
   not suggest a per-parameter choice) or a per-parameter lift that blocks this row. Owner of the choice: main agent
   (PF-11 / PF-21 consistency, before a2 builds the run-time skip).

Dropped as low: no test stores a `"fax"` row against `channel_swap` (the same code path is pinned by Q1 with `"app"`).
Known limits, not objections: GF-02 (last table only), GF-11 (no SQUASH block), DL-166 (step a1b), DL-168 (a2).

## Decisions

**Undo**
→ Probes in the scratchpad only; no repo test added. By: Opus (TEST fates-a1)
→ Objection 1 noted as medium, not blocking. By: Opus (TEST fates-a1)

**Repair**
→ Verdict PASS over FAIL, because every run passes and the only objection is medium (skill: block on critical or high
only). By: Opus (TEST fates-a1)

A PASS does not establish production readiness.

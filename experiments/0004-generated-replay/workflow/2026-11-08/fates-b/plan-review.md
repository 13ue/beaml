# Plan review: fates-b

**[Proposal]** PLAN CHECK phase, 2026-11-08, target `plan.md` and `plan.json` at `aa6acb28`. Fresh-context normal check, not a
Devil's Advocate round. No code, no test, no commit. By: Opus (PLAN CHECK fates-b).

## Verdict

**REPAIR, then go.** One high objection (O1) blocks the b3 RED until the plan states the b3 completeness rule. b1a and b1b are
not blocked. O2 and O3 are medium: fix them in the same plan repair.

Confirmed (observed):
- Split and order a2a → a2b → b3 → b1a → b1b → b2a are sound. b3 uses only what a2a/a2b build; b1a after a2a avoids a second
  fixture rewrite; one `main.rs` writer at a time.
- Answer class is right for b1c (removal of hidden values), b2b (row deletion) and A3 (age source). No planned buildable step
  deletes or overwrites stored production data: b3 rewrites the user's source (git revert undoes it), b1a rewrites repo
  fixtures and their records (git revert undoes it), b2a is read-only with the A5 guard. `main.rs` has no delete path today.
- QB-9 is stated correctly in substance: slice 4 RETIRE LINE keeps RESPONSE RECORDS in the file (`Replay.retired/0`,
  `not_retired/1`, main.rs 5180); DL-163 chose deletion of STORED ROWS only. Attribution fix: DL-057 itself does not say
  "the file stays"; that is the slice 4 behavior and the DL-163 evidence line. Cite those, not DL-057.
- b3 rule "dead when no stored value holds X below vB" matches the existing W2 rule (`oldest <= from`, main.rs 6504) and
  DL-070 (the last step can be dead, VERSION MARK kept). It is correct only for a complete, current store (O1).

## Objections

**O1 (high, blocks b3 RED): the completeness guard does not cover fate steps or a stale snapshot.**
- observed: `refusals` (main.rs 6539-6544) refuses a dead MIGRATE STEP only when `snapshot.oldest` has no entry for the TYPE.
  One `Amount v2` row is evidence enough; then `--remove-dead` runs without `--assume-complete`.
- observed: `oldest` is keyed by the top-level stored name and counts only accepted values of read TYPES (main.rs 5988, 6650).
  `snapshot-meta.json` checks only the row count (main.rs 6580-6583), not the query time.
- consequence: Q5 ("without `--assume-complete`: the existing refusal text") cannot pass with the Q1/Q3 snapshot. The plan's
  risk line "`--assume-complete` is the existing guard" is false for this case. A stale snapshot (taken before a v1 write)
  removes the quarantine/map step and the `enum X vA` block without any flag. Deployed code then meets a v1 row it cannot
  decode (DL-150 blocks at build only). No data is deleted; production reads fail until a revert.
- gap: which values keep a fate step alive is not exact. W2 says RETIRED RECORDS keep no step alive; under DL-163 a row due
  for deletion still exists until b2b, and a rejected or non-read row may hold vA too.
- resolving test: rule "a fate-step removal always needs `--assume-complete`" (refusal text names DL-151 live reads);
  Q5b: snapshot with v2 rows only, no flag, refusal. Q2b: a retired-but-not-deleted v1 row keeps the step alive.

**O2 (medium): class marking and guard text disagree in three places.**
- §2 table marks b2a "Migrate gate"; §4 A3 and plan.json `stop_for_owner` make QF-4 Answer. Use Answer for the QF-4 part.
- Guard rule 1 ("no delete outside a temporary copy in the same test process") contradicts rule 5 and N18 (SQL delete in the
  run's own seeded Postgres). Write rule 1 "except rule 5".
- No rule says where `--remove-dead` writes. Add: b3 tests and N18 run `--remove-dead` on a copy, never on a tracked source
  (`app/beaml/orders.beaml`). b1a's record rewrite never touches retained `results/` directories.

**O3 (medium): five of the 14 questions are not OWNER-level under DL-139.**
- QB-1: DL-168 Effect already puts `type.nested` on every field whose TYPE has a constructor; the marker is unchanged. It is a
  confirmation inside QA2-1, not a new question.
- QB-3: PB-08 already builds the block as a default; §5 says it waits. It is a default (safe side, one repair step).
- QB-4, QB-11: defaults (the plan agrees).
- QB-5: the line text is a default. The dry-run flag is avoidable: `--stored` always prints the count and keeps exit 1.
- Real OWNER questions: QB-2, QB-6, QB-7, QB-8, QB-9, QB-10, QB-12, QF-4, QF-9.

## Decisions

### Undo
→ PC-01: review only, no plan edit, no commit. By: Opus (PLAN CHECK fates-b)

### Repair
→ PC-02: block b3 RED on O1 statt pass, weil Q5 cannot pass and a stale snapshot removes a fate step silently. By: Opus (PLAN CHECK fates-b)
→ PC-03: b1a, b1b not blocked statt all blocked, weil O1 touches only b3. By: Opus (PLAN CHECK fates-b)
→ PC-04: O2, O3 medium statt high, weil none reaches stored production data. By: Opus (PLAN CHECK fates-b)
→ PC-05: QB-1, QB-3, QB-4, QB-5 (text), QB-11 as DL-139 defaults statt OWNER questions; the main agent decides the limit (DL-139, By: Fable). By: Opus (PLAN CHECK fates-b, proposal)

### Answer
→ none new. A1, A2, A3 stay with the OWNER, unchanged.

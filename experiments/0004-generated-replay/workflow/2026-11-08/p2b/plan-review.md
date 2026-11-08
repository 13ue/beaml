# Plan review: P2b

**[Proposal]** PLAN CHECK, 2026-11-08, target [plan.md](plan.md) at `10d55103`. By: Opus (PLAN CHECK P2b).
Normal fresh review, not a Devil's Advocate. No commit, no production change.
Basis: DL-164, DL-136, DL-150, DL-151, DL-157 ([decision log](../../../../../wiki/planning/decision-log.md)); D035
([decisions to be made](../../../../../wiki/planning/decisions-to-be-made.md)); `experiments/0001-syntax-to-beam/src/main.rs`;
Erlang/OTP 28.3.1 `stdlib-7.2/src/json.erl` (local install).

## Verdict

**GO with repairs.** One high objection (O1) must be repaired in the plan before RED. O2 and O3 are medium: take O2 in
RED, put the O3 evidence beside the OWNER default.

## What holds (checked against HEAD)

- **[Verified]** Reading of DL-164 / D035: "digest" = `value_sha256` per stored RESPONSE RECORD, ENTRY RECORD and ROW,
  over `{"redacted", "unknown_keys", "value"}` (DL-164 Effect names the QV3-6 scope; D035 names `value_sha256`). It is
  not snapshot provenance (DL-151 owns A3). Correct.
- **[Verified]** HEAD gaps as stated: `check_rows` 6595 folds `!digest_holds` into `continue`; `check_stored` 5946 and
  `check_entries` 5093 never call `digest_holds`; line 6049 prints `digest not verified (P2b)`. R1, R3, R4 fail at
  HEAD for the stated reason.
- **[Verified]** Emitter and checker digest the same stored projection: `record/3` (4312), `entry_record` (5016) and
  `db_core` (5229) write `digest(value, keys, redacted)` over the values they store; `digest_holds` reads the same three
  keys back. REDACTED values: both sides digest the stored (already redacted) projection, so no clear value is needed
  to check. Nested values: Erlang `sorted` and Rust `canonical` both sort object keys at every level, byte order on
  both sides; lists keep order on both sides.
- **[Verified]** Criterion 7 is a real false-pass guard: a checker over the wrong canonical form would block every good
  record in 0004 and the 0005 run. **[Inference]** It only guards content that the fixtures hold (see O1).
- **[Verified]** Pins: P2b changes only the Rust checker; no generated EFFECT byte moves. The six pin sites stay.
- **[Verified]** O2 (quarantine cannot park a bad-digest row) and O3 (count line does not name digest faults) are the
  safer defaults: a fate line answers a TYPE change, not corruption; the error line holds the count.

## Objections

### O1 (high): Rust and Erlang canonical forms differ on control characters; P2b turns that into a false block

- **Evidence.** OTP `json.erl` 476-496 escapes `\x0b`, `\x0e`, `\x0f`, `\x1a`-`\x1f` with UPPER-case hex
  (`\u000B`, `\u001B`). Rust `canonical` (main.rs ~5714) writes `\\u{:04x}`, lower case. Python
  `stored_types_test.value_sha256` (`json.dumps`) also writes lower case. Observed:
  `elixir -e ':json.encode(%{"a" => "x\vy\ez"})'` gives `\u000By\u001Bz`; Python gives `\u000by\u001bz`.
- **Consequence.** A genuine record or row whose String value holds such a character (a vertical tab from pasted
  office text, an ESC) carries an Erlang digest that `digest_holds` rejects. After P2b the build blocks on good data,
  and the help tells the user to delete the row. At HEAD the same row is silently skipped from the check. The tests
  cannot see it: plan section 3 takes expected digests from Python, which agrees with Rust, so RED and GREEN pass
  over the wrong form. The plan's line "Not RED: the digest algorithm itself" hides the gap.
- **Repair.** In GREEN, write `\\u{:04X}` in `canonical` (checker only, no pin moves). Add one RED whose record digest
  comes from the generated `Replay.digest/3` (or a fixture value pinned from the Erlang output above), not from
  Python: a good record with `\x0b` in a String value builds exit 0. Fix or note `stored_types_test.value_sha256`
  so later fixtures do not repeat the lower-case form. 0005 N15 control may carry such a character in `good()` as a
  cheap end-to-end cross-check.

### O2 (medium): criterion 3 (digest before path and value errors) is tested for ROWS only

- **Evidence.** R2 pins the order for rows. For RESPONSE RECORDS the REDACTED held-path count (5928-5939) runs before
  `checked += 1`, where the plan inserts the digest call; R3 and R4 tamper the value with a valid `99.00` text, so no
  second error can appear.
- **Consequence.** A GREEN that reports held-path or literal/constructor errors before (or beside) the digest error,
  or that does not `continue` after a digest fault, passes R3 and R4.
- **Repair (RED).** Let R3 tamper the value so it also fails a value check (lost literal or constructor reject) and
  holds a REDACTED path; let R4 tamper so a literal check fails. Assert only the digest error appears.

### O3 (medium): O1 default leaves a run-time outage for rows of a read TYPE with outcome not `accepted`

- **Evidence.** Generated `row_<type>/1` (main.rs 4542) matches `type` and `body(core)` only; it ignores `outcome`.
  So `db.list` reads every row of the TYPE and fails on its bad digest. `check_rows` skips digest for `!accepted`
  rows, and G1 pins that skip as exit 0. The db replay step also runs `body(record)` on rejected db RESPONSE RECORDS
  (4058).
- **Consequence.** A hand edit that flips `outcome` and changes the value builds green and breaks `db.list`, the exact
  case DL-164 "Because" excludes. Rows with no reader and retired records are not read at run time, so O1 is safe for
  them.
- **Repair.** Keep O1 as the OWNER question, but state this evidence in section 9 O1. Proposal for the built default:
  verify the digest of every row of a read TYPE, whatever its `outcome`; G1 then pins only no-reader rows, retired
  records and rejected HTTP records. Not blocking: DL-164 says "every checked record and row".

## Notes (not objections)

- **[Verified]** The digest does not cover `type`, `outcome`, `unknown_fields`, `request`, `status` (QV3-6 scope).
  A `stored_version` failure (6592) still skips the row before the digest; that is DL-150 ground (plan risk R4).
- **[Verified]** No Float TYPE exists in the compiler, so the Postgres number rewrite of plan risk R2 does not reach
  today's values.

## Decisions

**Undo**
→ Review only, no RED probe run. By: Opus (PLAN CHECK P2b)

**Repair**
→ O1 high, over medium, because a build blocks on good data and no planned test can see it. By: Opus (PLAN CHECK P2b)
→ O3 medium, over high, because DL-164 text names checked items and the OWNER owns O1. By: Opus (PLAN CHECK P2b)

**Migrate (OWNER chooses)**
→ O1 scope with the O3 evidence; O2 and O3 defaults confirmed as safer. By: Opus (PLAN CHECK P2b), assessment only.

# Plan check: the FATE slice, fates-a

**[Proposal]** Fresh-context plan check (normal review, not a Devil's Advocate round), 2026-11-08, of [plan.md](plan.md),
[decisions.md](decisions.md) and [plan.json](plan.json) at commit `dafe1dc3`. No production file, no test, no commit.
By: Opus (plan check fates).

Evidence: decision log DL-102, DL-122, DL-125, DL-137, DL-139, DL-140, DL-141, DL-150, DL-152, DL-153, DL-155, DL-156;
register D035, D036 (M3, M5), D041, D042; `experiments/0001-syntax-to-beam/src/main.rs`; tests under
`experiments/0004-generated-replay/tests/`; 0005 `app/beaml/variants/`, `app/test/`, `run.py`; the OWNER review site
`experiments/0005-prototype-fullstack/workflow/2026-11-08/review-site/build.py` (cards FATE, VERSION-RULE, FATE-NEXT).
Probes ran on a release build of `dafe1dc3` in a scratch copy (git archive), not retained.

## Observed

- **[Verified]** Decode path today (generated from 0005 `variants/stricter`, empty store): `__beaml_from_Amount` returns
  `:constructor`; `__beaml_decode_order` returns `{:error, "constructor"}`; `row_order` passes it on; `rows_order`
  halts on the first error; `list_orders_list` calls `__beaml_fail_orders_list(db_failed(…, "constructor"))`, which
  writes a rejected record and raises `BeamlFailure` with `StoreError{reason: "constructor"}`. `/orders`
  (`OrderListLive.mount`) then shows no orders at all, the good one included, plus an error flash.
- **[Verified]** A removed literal decodes at run time to the KEEP-VALUE VARIANT:
  `__beaml_literal_E(v) when is_binary(v)` gives `{E, Unknown, [v]}` (main.rs line 4187).
- **[Verified]** Probe: 0005 `stricter` with `type Amount v2` and `migrate Amount v1 -> v2 { drop note: String }`, over the
  two Order rows of `slice6/db/stored/meta/`: exit 0, then
  `warning: DEAD LINE: migrate Amount v1 -> v2 … no stored RESPONSE RECORD of TYPE Amount has v1 or older` and the
  `--remove-dead` help. `--remove-dead` refuses without `--assume-complete`; with it, the line goes. Cause: the W2 rule
  looks for records whose core `type.name` is `Amount`; a nested TYPE never has one (QF-2 A).
- **[Verified]** 0005 `--stored` reads rows only: `provenance!/1` asserts `responses.jsonl == ""`. RESPONSE RECORDS and
  ENTRY RECORDS are covered only by 0004 S1c and S1d.
- **[Verified]** 0005 `run.py` runs `gen(None)` and `gen("order_v2")` only. No step writes `gen-stricter.stderr`;
  `live_build/2` writes `build.stderr` under `<run>/n-tests/<n>-<label>/`. `EXPECTED` pins the N9 test name
  `"N9 quarantine amount frees the stricter build and the list omits order-zero"`.
- **[Verified]** `record_v3_test.py` `test_V18b_converted_fixtures_keep_exit_and_stderr` (passes at `dafe1dc3`, run here)
  compares exit and stderr of the `P2_BASE` (`545dded0`) compiler with the current one. Five of its pairs block with a
  help line today: `slice6/decode/stored-fail.jsonl`, `slice6/decode-ctor/stored-fail.jsonl`,
  `slice6/decode-ctor/stored-nomatch.jsonl`, `slice6/stored-elixir/nested-fail.jsonl`,
  `slice6/stored-elixir/pipe-fail.jsonl`, each `help: declare the fate of these records in a MIGRATE STEP to a new TYPE
  VERSION of Payment (DL-102)`. The plan's pin table does not list this site.
- **[Verified]** `slice6/decode-ctor/stored-nomatch.jsonl` blocks with `matches no signature of PaymentState` (an ENUM
  CONSTRUCTOR, `fn PaymentState`). There is no failing clause, and fates-a gives an ENUM CONSTRUCTOR no exit
  (PF-06: enum steps hold bare `map` only; PF-23: `map` rejects enums with `fn E`).
- **[Verified]** `slice6_m4_test.py` `rename_text` pins `… waits for the fate forms (M3, DL-152)`. The plan does not say
  whether this text stays once the fate forms exist. `LITERAL_HELP` reaches it by import from `slice6_db_stored_test`.
- **[Verified]** OWNER pictures: card FATE (decided, 13ue) shows `migrate Order v1 -> v2 { quarantine amount; map channel
  "mobile" -> App }`; card FATE-NEXT (decided A, DL-156) says "Use Case: 0005 N9 mit `quarantine amount`"; card
  VERSION-RULE (DL-155) says "`type Amount v2` oder `enum Channel v2` plus `migrate v1 -> v2` mit Fate oder `map`" and
  names no TYPE for the block. The DL-156 log text says "`quarantine value` on the stricter `Amount`". No OWNER-facing
  picture outside this plan shows `migrate Amount v1 -> v2 { quarantine value }`.
- **[Verified]** DL-156 (13ue) lists "the three blocks DL-102/DL-122/DL-140 lifted by a fate line" in the fate slice.
  PF-01 moves DL-140 to fates-b.
- **[Verified]** DL-150 (13ue) rejected option B "db.list skips the row and reports it" for not-decodable rows. D042
  records the OWNER lean "value comes back with a mark, never a crash, never a silent skip".
- **[Verified]** DL-141 (13ue): `reason` is a fixed key; "a later reason needs no format change". DL-139 keeps "record
  formats … and anything that host code calls" out of built defaults. `StoreError.reason` reaches host code
  (`OrderListLive` flash).
- **[Verified]** Pin sources: the three digest pins and the four hash guards (slice 5 `PIN`, entry and multi `BASE`,
  db `P4_BASE`) compile with an empty store; help lines need a stored hit, so they do not show there. The N13 globs
  include `experiments/0004-generated-replay/slice*/*.beaml` and `bad/*.beaml`; the git pathspec `*` crosses `/`
  (23 files under `slice6/db/` are listed). The db filter is `= *db\.\w+\(|: *\[`. No guard glob reaches
  `integrations/zed-beaml/` or 0005 `variants/`. slice 5 `A2` reads only files that exist at `f29e3f12`.
- **[Verified]** PF-20 at `dafe1dc3`: none of the 2136 tracked `.beaml` files holds `quarantine`, `enum E vN`, `map "…"`,
  `map f "…"` or `redact` in a MIGRATE STEP.
- **[Verified]** `versioned_decode` emits one block per `Change` arm of each step (main.rs from line 4290). A step with
  only `rename`, `add`, `drop` emits the same bytes whatever new arms exist.

## Inferred

- **[Inference]** (1) fates-a closes "block → fate → green" for DL-102 over 0005 rows only after a2 (runtime skip) and
  a3 (N9 host list). With a1 alone the build is green and `/orders` loses the whole list, not one row. For DL-122 a1
  alone is worse: the build is green and the `"app"` row reads as `Unknown("app")` with no error, the silent change that
  DL-122 exists to block. N9 and N9b test only the row stream in 0005; the RESPONSE RECORD and ENTRY RECORD streams
  rest on 0004 S1c, S1d, R5.
- **[Inference]** (3) The gated decode keeps String-only chained TYPES byte-equal by construction, if GREEN only adds
  `Change` arms and leaves the guard, `by_version` and `checked` parts unchanged. Not testable before GREEN; R7 is the
  check. PF-16 is worded too narrowly: the parent of a quarantined TYPE (`__beaml_decode_order`, `row_order`,
  `rows_order`, `replay_*`) must change too, although `Order` has no fate line. The pins still hold, because no pinned
  source has a fate line. The correct unit is "sources with a fate line".
- **[Inference]** (3) None of the eight help constants stands in a pinned file. One hash-pin site moves with the help
  text: `record_v3_test` V18b (five pairs, `P2_BASE`). So "no pin moves" is false for a1 as planned.
- **[Inference]** (4) What the a1 gate proves: every accepted stored value (row, RESPONSE RECORD, ENTRY RECORD) either
  passes the newest rules and literal table, or fails a constructor or lost-literal check that a fate line in the last
  step names. Lost literals are fully visible without the previous table, because `unknown_fields` separates "Unknown
  at capture" from "literal lost today". What it does not prove:
  - that the TYPE VERSION was bumped for this change: an earlier `quarantine` line covers a later stricter rule on the
    same version (the in-place gap; same cause as QF-8);
  - a known-to-known swap (DL-140), literal or ENUM CONSTRUCTOR clause order;
  - a constructor change that still succeeds but gives another value (a normalising rule): the check looks at pass or
    fail only;
  - that a mark plus fate line was needed at all (no dead-fate note);
  - anything about redacted values (absent, D042).
  So the gate covers literal removal and failures visible under the new rule, as the task suspected.
- **[Inference]** (6) DL-155 and DL-156 name `type Amount v2` and `quarantine value` on `Amount` (form A). DL-125 ("records
  whose field fails its rule") and both decided pictures use the owner form `quarantine amount` (form C). A and C are
  both supported by signed material. The line form is syntax under DL-139, so QF-3 is not a buildable default.

## Objections (max three)

**O1 · high · Form A is not OWNER-settled, and the existing DEAD LINE rule fires on it.**
Evidence: the FATE and FATE-NEXT cards show `quarantine amount` (form C); the probe shows a step on the nested `Amount`
reported as a DEAD LINE with the `--remove-dead` help. Consequence: if the OWNER picks C, a1 rebuilds parser, checker
and help texts (the DL-139 case). If A stays, every N9-style build tells the user to remove the very line that frees
it, and `--remove-dead --assume-complete` removes it; the next build blocks again or, after a2, the skip goes. The same
holds for `enum Channel v2` + `migrate Channel v1 -> v2`. Resolving test: F1 and N9 assert no `DEAD LINE` line in
stderr; a W2 case with `--remove-dead --assume-complete` keeps a nested fate step while a parent row holds the TYPE.

**O2 · high · a1 lifts the build block with no runtime counterpart, and a2 waits on QF-1.**
Evidence: the decode path above; plan.json puts QF-1 before a2 GREEN only. Consequence: between a1 GREEN and a2 GREEN,
main holds a compiler where `quarantine` gives a green build and a page with no list, and `map` gives a green build and a
silent `Unknown("app")`. That is the DL-150 hazard and the DL-122 case, committed on purpose, for an open time. QF-1 A
also takes the runtime shape the OWNER rejected for DL-150 (B) and that D042 calls a silent skip. Resolving test: the
RED depth probe gets a case "a1-only build": a source whose fate line is hit by `--stored` must not exit 0 before R1
and R3 pass.

**O3 · medium · Pin and help impact are under-listed; one help case is undefined.**
Evidence: `record_v3_test` V18b; `slice6_m4_test` `rename_text`; `stored-nomatch.jsonl` (ENUM CONSTRUCTOR, no
failing clause); `gen-stricter.stderr` does not exist; the N9 test name sits in `run.py` `EXPECTED`. Consequence: a1
GREEN fails the full run late (the lesson of the PIN misses), or the help names a fate form the checker then rejects.
Resolving test: S1b-ctor-enum (a `matches no signature` hit: the help names no `quarantine` or `map` line, or the exit
that fates-a really has); V18b re-pinned in the a1 GREEN with the hunk list.

**Noted (medium, not an objection):** PF-01 narrows DL-156 (13ue): DL-140 leaves the slice. Show this to the OWNER as
its own question; do not record it as a Repair only.

## Dispositions

All pending. No OWNER answer is implied by this record.

| ID | Disposition |
|---|---|
| O1 | pending |
| O2 | pending |
| O3 | pending |
| Noted (DL-156 scope) | pending |

## Plan repairs (proposed)

1. **QF-3 before a1 GREEN** (O1). Move QF-3 into plan.json `owner_before_green` of a1, beside QF-7. Show the OWNER both
   signed sources (cards FATE and FATE-NEXT vs DL-155 and DL-156) and the probe result.
2. **DEAD LINE rule for nested TYPE steps** (O1). In a1: a step of a TYPE that no record names in its core `type` but
   that a stored parent holds is never a DEAD LINE (or: a step with a fate line is never dead while its count is above
   0). Add RED F7 (no `DEAD LINE` for `migrate Amount v1 -> v2 { quarantine value }` over the N18 rows) and F7b
   (`--remove-dead --assume-complete` keeps it).
3. **No green build without the runtime** (O2). Pick one: (a) ask QF-1 now, with QF-7 and QF-3, and land a1 and a2 back
   to back; or (b) a1 gives exit 1 with `fate: quarantine at run time is not built yet (a2, QF-1)` and `fate: map at run
   time is not built yet (a2)` when a fate line is hit, and a2 removes both texts. (b) keeps a1 independent of the
   OWNER answer.
4. **Pin table** (O3). Add `tests/record_v3_test.py` V18b (`P2_BASE`, five pairs) to the byte-pin table as a site that
   moves in a1 GREEN, with the two-commit rule. Add `slice6_m4_test.py` `rename_text` to the help-text list, with a
   decision on whether "waits for the fate forms" stays for `rename`, `add`, `drop` on enum and constructor fields
   (QM4-4 is still an open default).
5. **ENUM CONSTRUCTOR help** (O3). Define the DL-102 help for `matches no signature of E` and for an enum constructor
   that fails: under PF-06 and PF-23 fates-a has no exit, so the help must say so (D041 open), not name the version
   form. PF-21 needs a rule for "no failing clause".
6. **PF-16 wording**. "Only sources with a fate line change their generated bytes." R7 excludes exactly those sources.
7. **N9 evidence path**. Replace `gen-stricter.stderr` with `<run>/n-tests/<n>-n9/build.stderr`, or add a `run.py` step;
   note that `gen()` writes `lib/generated/orders.ex` on exit 0, so a stricter gen step must not run before other
   N-TESTS. Rename the `EXPECTED` entry and the test name together (QF-3 outcome).
8. **Fixture placement** (PF-20). Fate fixtures under `slice6/db/fates/` must hold a db EFFECT line or a `: [` field (the
   N13 filter); wrong-form fixtures go inline or under `slice6/db/fates/bad/`, never under `bad/` or `slice6/db/bad/`
   (the `BAD_CASES` setup check).
9. **Missing RED cases** (add to the a1 or a2 table):
   - F5 subTest: `quarantine f` where `f` is a field of `Amount` but not a parameter name of `fn Amount` (PF-11 has no text).
   - F5 subTest: two `quarantine` lines on two parameters of one constructor TYPE (PF-11); two bare `map "app"` lines
     with different targets; a bare `map "app"` in `Channel` and a qualified `map channel "app"` in `Order` for the same
     literal (which wins, or an error).
   - F5 subTests: `map "app" -> Unknown` without parentheses (checker text "carries a payload") and
     `-> Unknown("x")` (parse error), as two cases.
   - F8: `enum Channel v2` with no `migrate Channel v1 -> v2` over a lost-literal row still blocks (S3b for enums);
     `enum Channel v3` with only `migrate Channel v1 -> v2` gives the chain error.
   - S1f: one row with `Amount "0"` and a lost channel literal without `map` still blocks; R1b: the same row still fails
     `db.list` at run time (not quarantined). Today's decode checks the `:constructor` sentinel first, so this is the
     main false-pass risk of "the only failure".
   - R5b: an ENTRY RECORD (`Replay.entry`) with a quarantined value gets no REPLAY RUN (not only a RESPONSE RECORD).
   - R1c: a live ENTRY LINE event with `"0"` is `rejected` / `constructor`, not quarantined (PF-22 for entries).
   - R8: a quarantined row, then the same order re-entered with a valid amount: `db.get` gives the new row (QDB-3),
     `db.list` lists it once, the old row stays skipped, and the build still prints the `fate:` count 1.

## QF-1, proposed OWNER question text

> **QF-1 · An old row fails the new `Amount` rule and the source declares `quarantine` for it. What does the running app
> get when it reads the table?**
> → A **Skip:** `db.list` returns the other rows; `db.get` of that row fails with reason `quarantined`; the skip count
> stands only on the span and in the build report. The page and the list record show nothing.
> → B **Mark:** the row comes back as a marked value (for example `Quarantined(Order)`); every signature and page that
> reads `Order` must handle it (D042 A direction; new syntax and host code).
> → C **Fail:** the read fails as today (QDB-4). The build is green, the page shows an error until someone acts.
> → D **Skip and record:** as A, and the list record names the skipped count in a new key (record format change).
>
> Your earlier answers: for an undeclared bad row you chose "block the build", not "skip and report" (DL-150); for an old
> value you leaned to "a mark, never a crash, never a silent skip" (D042). Is A a silent skip for you?

Class: Migrate. Not a buildable default under DL-139: A, B and D reach host code (`StoreError.reason`, signatures or
record keys). DL-150 does not formally conflict with a runtime skip (it governs undeclared, not-decodable rows at build
time; a quarantined row counts as checked, PF-14), but A takes the runtime shape the OWNER rejected there.

## Pin verification result

- PF-20: holds at `dafe1dc3` (no tracked source uses the new syntax). It stays true only with repair 8.
- String-only chained TYPES: byte-equal by construction of `versioned_decode` (one block per `Change` arm); R7 must check
  it after GREEN.
- The six (seven with `P4_BASE`) listed pin sites do not move under PF-16 (reworded) and PF-20.
- One unlisted hash-pin site moves with the DL-155 help text: `record_v3_test` V18b (`P2_BASE`, five fixture pairs).
- The eight help constants are not in pinned files. `slice6_m4_test` holds a ninth related text (`rename_text`).

## Limits

- No fates-a code exists. Every runtime statement comes from the generated Elixir of `dafe1dc3`, not from a run of 0005.
- The DEAD LINE probe used `drop note: String`, because a fate-only step does not parse today. The W2 rule does not
  read the step body, so the result should carry over. That is an inference.
- V18b was run at `dafe1dc3`. That it fails after a help change is an inference from its `assertEqual` on stderr.

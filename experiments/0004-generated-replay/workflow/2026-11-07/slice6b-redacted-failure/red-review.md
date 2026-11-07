# RED review: slice 6b step 6c (a direct copy of a redacted value into a non-redacted place, DL-112)

Phase: RED review, 2026-11-07. Base: HEAD 4c48842d. Fresh context. Review only: no test, fixture or production file changed. `run.py` not run. No commit.
Inputs: [spec.md](spec.md), [notes.md](notes.md) D6B-174 to D6B-181, [red-output.log](red-output.log), the plan ledger [slice6b-redacted](../slice6b-redacted/plan.md) ("Failure TYPE rule (6c)", D6B-67), the [decision log](../../../../../wiki/planning/decision-log.md) DL-105, DL-111, DL-112, DL-113, DL-116, DL-119, `tests/slice6_redacted_failure_test.py`, the 20 fixtures in `slice6/redacted-failure/`, `main.rs` (`Program.redacted`, `is_redacted`).

**Verdict: BLOCK** (one high objection, O1). By: Opus (RED review, slice6b-redacted-failure)

## Re-run

- **[Observed]** Scratch build of HEAD (`git archive HEAD experiments/0001-syntax-to-beam`, `cargo build --offline`), passed by `BEAML_SPIKE`. `Ran 8 tests`, `FAILED (failures=11)`. Same set as `red-output.log`: 3 methods fail (F1, failure TYPES 3, DL-112 7), 5 pass. By: Opus (RED review, slice6b-redacted-failure)
- **[Observed]** All 11 failures are `(0, [])`: exit 0, no stderr. Missing behaviour, not setup. The setup control builds each RED source without `redacted`. By: Opus (RED review, slice6b-redacted-failure)
- **[Observed]** The SHA-256 of the 20 fixtures and the test file are equal to the hashes in `red-output.log`. By: Opus (RED review, slice6b-redacted-failure)

## D6B-178: the success body (question 2)

- **[Observed]** No field access form exists. A fn that has a whole `o: Order` can read `card_holder` only through an accessor fn with a record pattern, which is the `l5` shape. By: Opus (RED review, slice6b-redacted-failure)
- **[Observed]** Probe on the HEAD build, scratch only:
  ```
  fn holder Order { card_holder } -> String = card_holder
  fn receipt o: Order -> Receipt = Receipt { holder: holder(o) }
  fn receipt2 o: Order -> Receipt = Receipt { holder: o |> holder }
  ```
  Exit 0. The generated code puts `__MODULE__.holder(v_o)` into the plain `holder` key. Under D6B-174 this still builds after GREEN: `o` is a parameter (never direct), and `holder` is not an identity fn. By: Opus (RED review, slice6b-redacted-failure)
- **[Inference]** Answer: yes, this is a copy into a non-redacted place under DL-112. The value is not changed (no `+`, no constructor). It is the same value hop that D6B-174 counts as direct for `same(card_holder)`. D6B-174 catches the hop that nobody writes (an identity fn) and lets pass the hop that every program needs (an accessor). Logs and events stay covered by DL-089; the open place is a plain record field or payload, and from there the next EFFECT (DL-112 question). By: Opus (RED review, slice6b-redacted-failure)
- **[Inference]** `l5` itself must still build: no `-> redacted String` form exists (plan: `redacted` in signature lines is out of scope), so a reject of `l5` blocks every accessor, also a legal one that feeds a redacted field. The place is the call site, not the return. By: Opus (RED review, slice6b-redacted-failure)

## Reach (question 3)

- **[Observed]** A GREEN that checks only a bare pattern-bound name fails `d2` (`card_holder |> same`) and `d3` (`same(card_holder)`). The hop is tested for the call and the pipe form. By: Opus (RED review, slice6b-redacted-failure)
- **[Observed]** A GREEN that treats every call with a direct argument as direct fails `l2` (constructor) and `l4` (`again`, not an identity body). A GREEN that follows identity fns transitively fails `l4`. So "one level" is pinned. By: Opus (RED review, slice6b-redacted-failure)
- **[Observed]** `l1` to `l5` pass today and stay `assert_builds` after GREEN. They are real limit tests. By: Opus (RED review, slice6b-redacted-failure)
- **[Observed]** Every identity fn in the fixtures has one clause. "Every clause body" (D6B-174) is not tested. See O2. By: Opus (RED review, slice6b-redacted-failure)

## Over-reject guards (question 4)

- **[Observed]** "Reject every use of a redacted-bound variable in a literal": fails `g1`, `g2` (redacted target), `l1` (`+`). By: Opus (RED review, slice6b-redacted-failure)
- **[Observed]** "Reject by field name" (DL-113): fails `g3` (`card_holder: order_id`). "Reject every record literal in a fn with a redacted binding": fails `g3`. By: Opus (RED review, slice6b-redacted-failure)
- **[Observed]** "Reject a whole record of a TYPE with a redacted field": fails `g4`. "Reject a constructor result": fails `l2`. "Reject a direct success body": fails `l5`. "Reject a direct argument to any fn": fails `l3`, `l4`. By: Opus (RED review, slice6b-redacted-failure)
- **[Inference]** The guards are strong enough. No over-broad GREEN that I found passes the RED. By: Opus (RED review, slice6b-redacted-failure)

## Texts (question 5)

- **[Observed]** The texts name only the fn, the redacted field, its declaring TYPE, the dotted target, the target TYPE and the DL. No expression text and no literal is interpolated. By: Opus (RED review, slice6b-redacted-failure)
- **[Inference]** A redacted value is a runtime input, so no value exists at compile time; the texts cannot leak one. `Program.redacted` holds (TYPE, field) pairs, so the declaring TYPE of D6B-177 is available. By: Opus (RED review, slice6b-redacted-failure)

## Objections

- **O1 · high · blocks.** The RED misses the accessor case, and D6B-178 lowers DL-112 without the OWNER. Consequence: after GREEN, `Receipt { holder: holder(o) }` and `o |> holder` build with exit 0, and the redacted value stands in a plain field that the next EFFECT sends without `with`. This is the common shape, because no field access form exists. DL-112 is an Answer ("everywhere"); D6B-178 narrows it as a Repair, which Decision4 does not allow silently. Smallest resolving rule: extend D6B-174 by one symmetric hop. A call `f(x)` or a pipe step `x |> f` is direct when `f` has one parameter and every clause body of `f` is a direct value of that clause (a pattern-bound redacted field), with F of T from the callee pattern. `l5` keeps building. Resolving test: a new RED fixture `d8_accessor_call` with the two receipt fns above (one file per case: `d8` call, `d9` pipe), expected text `error: fn receipt copies the redacted field card_holder of Order into holder of the TYPE Receipt, which is not redacted` and the DL-112 help. If the team does not extend the reach, D6B-178 goes to the OWNER as an Answer question, not a Repair. By: Opus (RED review, slice6b-redacted-failure)
- **O2 · medium · noted.** "Every clause body is the parameter unchanged" (D6B-174) has no multi-clause case. Consequence: a GREEN that reads only the first clause passes the RED, and a two-clause fn whose second clause transforms the value becomes direct (a false reject) or the reverse. Resolving test: one limit fixture with a two-clause fn, one clause identity and one `s + ""`, that builds. By: Opus (RED review, slice6b-redacted-failure)

## Counts

- 11 RED subtests in 3 methods, all `(0, [])`. 4 guards, 5 limits, 11 setup controls, 20 `fmt` cases, 1 set check pass. 2 objections: 1 high, 1 medium. By: Opus (RED review, slice6b-redacted-failure)

## Limits of this review

- Compile only, one round. The accessor probe source stays in the scratch directory; no file in the repo tree changed except this review. By: Opus (RED review, slice6b-redacted-failure)

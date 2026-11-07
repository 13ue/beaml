# Notes: slice 6b step 6c RED

Phase: Solve / RED, 2026-11-07. Base: HEAD 461d024e. No production file changed. `run.py` not run. No commit.
By: Opus (RED, slice6b-redacted-failure) for every item in this file.

## Result

- **[Observed]** 8 test methods, 11 RED subtests. Exit 1, `FAILED (failures=11)`. Each failure is `(0, [])`: the build passes with exit 0 and no stderr (missing behaviour, not setup).
- **[Observed]** 5 methods pass: guards, limits, setup control, `fmt`, fixture set.
- **[Observed]** Compiler: a scratch build of HEAD by `git archive` (`BEAML_SPIKE`). Hashes of the fixtures and the test file are at the end of [red-output.log](red-output.log).
- **[Observed]** No field access form: `Receipt { holder: o.card_holder }` gives `expected identifier at byte 146`.

## Decisions

### Repair

- D6B-174 · Repair · Reach of a direct value. Chose: a pattern-bound variable (any depth, any binding name), plus one call or pipe step into a fn with one parameter whose every clause body is that parameter unchanged. Over: the plan text "a call or a pipe makes a derived value" (D6B-67), and a flow check into the callee. Because: the task names the one-level helper and the pipe step as DL-112 cases; an identity fn is the smallest reach that catches them without a flow analysis. Commits us to: `l3` (a fn that builds the record from its parameter) and `l4` (two identity levels) pass and are recorded as limits; a later flow check (DL-029) changes them. By: Opus (RED, slice6b-redacted-failure)
- D6B-175 · Repair · DL-112 text outside failure TYPES. Chose: the D6B-67 text with `the TYPE R` in place of `the failure TYPE E`, help ends `(DL-112)`. Over: one text for both. Because: the help points to the decision that applies. Commits us to: GREEN emits two help suffixes. By: Opus (RED, slice6b-redacted-failure)
- D6B-176 · Repair · Help line for (b) and (c): `  help: do not copy the value (DL-105)`, `(DL-112)` outside failure TYPES. Chose: a short help. Over: "mark ... as redacted". Because: a payload cannot be redacted (D6B-64), and a body TYPE has no field to mark. Commits us to: the text changes when a redacted payload exists. By: Opus (RED, slice6b-redacted-failure)
- D6B-177 · Repair · Names in the text. Chose: F of T is the redacted field and its declaring TYPE (`holder of Card` for a nested pattern); G is dotted from the outer literal (`inner.text`); the help names the target field and its declaring TYPE (`mark text as redacted in Inner`). Over: a dotted source path (`card.holder of Order`). Because: the help must name the line to change; the target path shows the place. Commits us to: GREEN keeps the declaring TYPE for each bound variable. By: Opus (RED, slice6b-redacted-failure)
- D6B-178 · Repair · A direct redacted value as the success body (`l5`) is not checked. Chose: not checked. Over: a reject. Because: DL-112 names record literals and payloads; D6B-67 (c) names the failure TYPE only. Commits us to: a caller that puts the result into a plain field is derived (D6B-174). By: Opus (RED, slice6b-redacted-failure)

### Undo

- D6B-179 · Undo · One case per fixture file, so the first error is the tested one. The plan cases F2 to F6 keep their plan names in the docstrings (F2 = `g2`, F5 = `l1`, F6 = `g4`). By: Opus (RED, slice6b-redacted-failure)
- D6B-180 · Undo · Extra stderr lines after the two exact lines may only be `  at byte N` (D6B-153). By: Opus (RED, slice6b-redacted-failure)
- D6B-181 · Undo · The setup control removes `: redacted ` from each RED source and expects a build. By: Opus (RED, slice6b-redacted-failure)

## Deferred edits

- None. No existing test file changes.
- **[Observed]** No tracked `.beaml` source with `redacted` outside `slice6/redacted-failure/` has a fn record pattern (`git grep` over `slice6/redacted/` and `integrations/zed-beaml/test/highlight/forms.beaml`). **[Inference]** So the 6c rule rejects no existing fixture. GREEN confirms by the byte check.

## Limits

- The test has its own `compiler()` and `build`; it imports only `arm_tree`.
- The rule is syntactic. The limit tests show four bypasses (`+`, constructor, record-building fn, two levels).

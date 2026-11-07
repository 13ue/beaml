# Notes: slice 6b step 11 (constructor TYPES are structs at the host, `T.new/1`)

Phase: Solve / RED, 2026-11-07. Base: HEAD 52550d4f. No production file changed. `run.py` not run. No commit.
Inputs: [plan.md](plan.md), [decisions.md](decisions.md), [plan-review.md](plan-review.md), DL-106, DL-117, DL-120 in the [decision log](../../../../../wiki/planning/decision-log.md).
Test: `tests/slice6_host_struct_test.py`. Fixture: `slice6/host-struct/nonzero.beaml`. Contract: [spec.md](spec.md). Run: [red-output.log](red-output.log).
"Constructor TYPE" stays plain text (D6B-83).

## RED result

- **[Observed]** 3 test methods, 23 runtime cases, 46 byte-guard subtests. Exit 1, `FAILED (failures=19)`.
- **[Observed]** 19 cases fail: H1 (2), H2 (7), H3 (2), H3e (2), H4 (1), H9 (4), H7 (1).
- **[Observed]** 5 checks pass today, all guards: H1g, H5, H6 (2 cases), H8 (whole test).
- Failure reasons, every one a missing behaviour:
  - A String-key map passes the input check (H1, H3, H3e map cases: `invalid.(...)` gives `false`).
  - The struct fails the input check (`h1_struct_passes`, H7: `ArgumentError invalid BEAML input`; the check wants `map_size == 1` and String keys).
  - `T.new/1` is absent: `BeamlSpike.NonZeroInt.new/1 is undefined or private` (H2, H3 and H3e struct cases); `module BeamlSpike.Pair is not available`, same for `Label` (H9).
  - `wrap(5)` gives the String-key map (H4: `false`).
- No setup failure: the fixture compiles, `elixirc --warnings-as-errors` passes, `checks.exs` runs to its end. The test asserts each setup step with a `setup:` message.
- **[Observed]** `BeamlSpike.NonZeroInt` exists today as a struct module, because `twice` uses NonZeroInt as a failure TYPE. So H2 fails on the absent function `new/1`, not on an absent module.

## Changed plan lines

### Undo

- U1: H2 takes the DL-117 form `NonZeroInt.new(%{n: 3})`, not `NonZeroInt.new(3)`. The key `n` is the parameter name of the signature. By: Opus (RED, slice6b-host-structs)
- U2: H2 `new("3")` becomes `new(%{n: "3"})`: the keys match, the value TYPE is wrong, so it raises `invalid BEAML input`. By: Opus (RED, slice6b-host-structs)
- U3: H9 is no longer open (DL-117). `Pair.new(%{x: "x", y: "y"}) == {:ok, %Pair{a: "x", b: "y"}}`. The plan interim "no `new` for several parameters" ends. By: Opus (RED, slice6b-host-structs)
- U4: H9 adds TYPE `Label` with two signatures (`text`; `first, last`). Each key set picks its own signature. Reason: DL-117 "the keys pick the signature" needs two signatures to be tested. By: Opus (RED, slice6b-host-structs)
- U5: H3 uses the valid value `4` in the nested map, not `0`. Reason: the plan-check O1 argument; a GREEN that runs the constructor on the map must not pass. By: Opus (RED, slice6b-host-structs)
- U6: Fixture directory `slice6/host-struct/` (task text), not `slice6/host-structs/` (D6B-80). The fixture also holds `Pair` and `Label`. By: Opus (RED, slice6b-host-structs)
- U7: H8 names `slice6/enum/literals.beaml`. The plan's `slice6/enum/enum.beaml` does not exist. H8 also covers `slice6/failure/overlap.beaml`. By: Opus (RED, slice6b-host-structs)
- U8: H8 stores the stdout sha256 and the exit code of the pre-step compiler (scratch `git archive` build of HEAD 52550d4f), as step 5 S12. The test does not build the base compiler. Three sources exit 1 (`slice3/D7`, `slice3/M-nodrop`, `slice4/B+r`); they keep exit 1 and an empty stdout. By: Opus (RED, slice6b-host-structs)
- U9: The checks build structs with `struct!/2` at run time (`st.(mod, fields)`), not with `%Mod{}` literals. Reason: a literal of an absent module (`Pair`, `Label`) is a compile error of the whole script, which is a setup failure. `struct!/2` fails one case only. By: Opus (RED, slice6b-host-structs)
- U10: The test has its own `compiler()` and `build`. It imports only `arm_tree` (paths), no other test module. By: Opus (RED, slice6b-host-structs)
- U11: No RESPONSE RECORD fixture. The fixture is a pure module (no EFFECT), so the 6a version 2 record shape does not apply. No fixture relies on DL-120: no constructor reaches an EFFECT. By: Opus (RED, slice6b-host-structs)
- U12: H7 stays a test with the name `test_limit_deliberate_struct_literal_is_not_caught` (plan H7). Its docstring says that it records the DL-106 limit. It fails today, because the input check wants a String-key map. The task text says "no test" for this limit; the plan asks for H7. The main agent can drop the method without effect on the other cases. By: Opus (RED, slice6b-host-structs)

### Repair

- D6B-97 · Repair · A map that matches no signature gives `{:error, {:no_signature, text}}`. Text: `T.new/1: no signature takes these keys`. Chose: a two-tuple with an atom tag. Over: a raise, or a BEAML failure struct. Because: DL-117 names `{:error, ...}`; an atom-tag two-tuple never equals a BEAML failure value (struct, three-tuple with binaries, or scalar). Commits us to: the host branches on `{:error, {:no_signature, _}}` apart from the constructor failures. By: Opus (RED, slice6b-host-structs)
- D6B-98 · Repair · The help line `  help: keys must be atoms; decode outside data through the EFFECT` follows the text on a new line when a key of the map is not an atom. A map with atom keys that match no signature gets the text only. Chose: two texts. Over: the help line always. Because: the help line is wrong for `%{m: 3}`. Commits us to: GREEN checks the key kinds before it gives the error. By: Opus (RED, slice6b-host-structs)
- D6B-99 · Repair · A key set matches a signature only when it is equal to the parameter names. An extra key or a missing key matches no signature (`%{n: 3, m: 4}`, `Pair.new(%{x: "x"})`). Chose: equal sets. Over: a subset match. Because: DL-117 "whose keys match"; an extra key that is dropped silently hides a host error. By: Opus (RED, slice6b-host-structs)
- D6B-100 · Repair · A value that is not a map (`NonZeroInt.new(3)`) raises `ArgumentError, "invalid BEAML input"` (D6B-82 text). Chose: the raise. Over: `{:error, {:no_signature, ...}}`. Because: DL-117 says a naked value is not a form; a wrong argument kind is a host error like a wrong TYPE. Commits us to: `new/1` checks `is_map` first. By: Opus (RED, slice6b-host-structs)
- D6B-101 · Repair · When the keys match a signature and a value has the wrong TYPE, `new/1` raises `invalid BEAML input` through the `new_T_k` input check. It does not try the next signature. Because: DL-117 "the keys pick the signature". By: Opus (RED, slice6b-host-structs)

## Open points for the RED review

- **[Unknown]** D6B-97 to D6B-101 are new IDs. Another worker can take the same numbers in parallel. The main agent checks for a collision before the commit.
- **[Inference]** D6B-97 to D6B-101 change a host-facing form. If the main agent reads them as Migrate, they go to the OWNER before GREEN.
- **[Proposal]** The changed existing assertions of the plan table stay as written, with one addition: no existing test calls `T.new`, so DL-117 changes no existing line.
- Two signatures with the same key set and other TYPES are not tested (D6B-101 covers them by the first-match rule).

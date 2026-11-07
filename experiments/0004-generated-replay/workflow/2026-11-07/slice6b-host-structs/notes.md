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

## GREEN

Phase: GREEN, 2026-11-07. Base: HEAD 0ac1a8d2. No commit. `run.py` not run. By: Opus (GREEN, slice6b-host-structs).

### Changes in `experiments/0001-syntax-to-beam/src/main.rs`, by function

- `ctor_args` (new): the parameters of a signature key; `ctor_signatures` now uses it (same result).
- `ctor_record` (new): a record TYPE with a constructor `fn T`. Enum constructors stay tuples (D6B-79).
- `emit_node`: a constructor TYPE literal or pattern is `%__MODULE__.T{f: v}` (D6B-75). Plain records keep `%{<<"f">> => v}`.
- `emit`: `is_struct: 2` and `defmodule: 2` join the import list only when a constructor TYPE exists (byte guard H8).
  `__beaml_valid__(v, "T")` for a constructor TYPE is `when is_struct(v, __MODULE__.T)` plus the field checks through `Map.get(v, :f)` (D6B-76).
  The top struct list holds every constructor TYPE; the list after the EFFECTS excludes them (one module per TYPE).
- `emit_structs`: iterates over the failure structs and the constructor TYPES; a constructor TYPE gets `emit_new`.
- `emit_new` (new): the struct module with `import Kernel`, `@parent`, `defstruct` and `new/1` (DL-117, D6B-74, D6B-97 to D6B-101).
  One clause per signature `def new(%{k1: a0, ...} = m) when map_size(m) == N`; a signature without failures is wrapped in `{:ok, _}`.
  Then `{:error, {:no_signature, text}}` for another map, with the help line when a key is not an atom; a non-map raises `invalid BEAML input`.
- `result`: a constructor TYPE failure passes through unchanged (D6B-77), not rebuilt with String-key `Map.get`.
- Unit test `constructor_types_are_structs` (literal, pattern, input check, `new/1` clause).

### Test tightening (red-review M2)

- `m2_struct_wrong_field_type_rejected`: `keep(%NonZeroInt{value: "4"})` raises `invalid BEAML input`. Passes.
- `m2_nested_atom_key_map_rejected`: `unbox(%{"n" => %{value: 4}})` raises `invalid BEAML input`. Passes.
- **[Inference]** Both pass also on the base compiler (the review calls them guards). They stop a GREEN with `is_struct` only and no field check.

### Changed existing assertions (red-review M3), each with its plan row

| File | Assertion | Plan row | New value |
|---|---|---|---|
| `slice6_constructor_test.py` | `constructor_ok` | `constructor_ok` | `{:ok, %BeamlSpike.NonZeroInt{value: 3}}` |
| `slice6_constructor_test.py` | `wrap_ok` | `wrap_ok` | `{:ok, %BeamlSpike.NonZeroInt{value: 5}}` |
| `slice6_constructor_test.py` | `read_pattern` | `read_pattern` | `read(%BeamlSpike.NonZeroInt{value: 4}) == 4` |
| `slice6_constructor_test.py` | `keep_passes` | `keep_passes` | struct in, struct out |
| `slice6_constructor_test.py` | `plain_ok` | `plain_ok` | `{:ok, %BeamlSpike.NonZeroInt{value: 2}}` |
| `slice6_constructor_test.py` | `call_form` | `call_form` | `%BeamlSpike.F{reason: "x"}` |
| `slice6_constructor_test.py` | build lines of both fixtures | build lines 96 and 105 | `{:ok, %__MODULE__.NonZeroInt{value: v_n}}` |
| `slice6_pipe_test.py` | `record_field_in_constructor` | same | `%BeamlSpike.Pair{a: "(x)", b: "y"}` |
| `slice6_pipe_test.py` | `first_clause_ok`, `second_clause_ok` | same | `{:ok, %BeamlSpike.NonZeroInt{value: 2}}`, `... 3}}` |
| `slice6_enum_test.py` | line 38 (`pair_declined_pipe`), `call_pair` | same | payload `%BeamlSpike.DeclineReason{text: ...}` |
| `slice6_decode_ctor_test.py` | `EUR` | `EUR` (line 52) | `%BeamlSpike.Amount{value: "12.50", currency: "EUR"}` |
| `slice6_decode_ctor_test.py` | `declined_via_pipe`, `replay_declined` | same | payload `%BeamlSpike.DeclineReason{text: "card"}` |
| `slice6_constructor_test.py` | `test_nonzero_fixture_compiles_to_the_planned_shape`: `"defmodule NonZeroInt do"` moves from `absent` to present (row 13) | DL-106, outside the plan table, decided by the main agent (Repair, By: Fable) | present line |

- Not changed: wire inputs `eur`, `st`, the stored records, every reject text.
- **STOP, resolved by row 13:** `slice6_constructor_test.py` `test_nonzero_fixture_compiles_to_the_planned_shape` has `absent=[..., "defmodule NonZeroInt do"]` (step 3). The plan table does not list it.
  D6B-73 needs that module, so the test fails: `([], ['defmodule NonZeroInt do'])`. The main agent decides the edit.

### Results

- **[Observed]** `slice6_host_struct_test.py`: 3 of 3 OK (24 runtime cases plus 2 M2 cases, H7, H8 46 subtests).
- **[Observed]** OK: `slice6_decode_ctor` 8, `slice6_decode` 10, `slice6_enum` 20, `slice6_failure` 22, `slice6_fmt` 25, `slice6_int` 16, `slice6_pipe` 12, `slice6_record` 5, `slice6_struct_order` 3, `arms_test` 11.
- **[Observed]** `slice6_constructor_test.py`: 24 of 25 before row 13; after row 13: 25 of 25 OK (re-run).
- **[Observed]** OK: `slice2_replay` 21, `slice3_replay` 31, `slice3_types` 69, `slice4_replay` 27, `slice4_retire` 87, `slice5_replay` 12, `slice5_rewrite` 5, `slice5_squash` 24, `slice5_syntax` 60.
- **[Observed]** `cargo fmt --check` OK, `cargo clippy --offline --all-targets -- -D warnings` OK, `cargo test --offline --no-fail-fast` 19 + 14 pass.
- **[Observed]** `payments.generated.snapshot`: byte-equal (`cmp`).

### Decisions

#### Undo

- G1: `new/1` calls the parent through `@parent` (as `Replay`), not a fixed `BeamlSpike.` name. By: Opus (GREEN, slice6b-host-structs)
- G2: The struct module of a constructor TYPE imports all of `Kernel`; it defines only `new/1`. By: Opus (GREEN, slice6b-host-structs)
- G3: An unnamed constructor parameter gets the key `aI` (marked `ponytail:`); no fixture has one. By: Opus (GREEN, slice6b-host-structs)
- G4: `T.new/1` text names the short TYPE name (`Label.new/1`), as the test wants. By: Opus (GREEN, slice6b-host-structs)

#### Repair

- G5: Exact key set through a map pattern plus `map_size` guard. Chose: pattern and guard per signature. Over: `Map.keys` sort and compare. Because: one clause per signature, first match by clause order (D6B-99, D6B-101). Commits us to: the clause order is the signature order. By: Opus (GREEN, slice6b-host-structs)
- G6: A constructor TYPE failure in `result` gives `{:error, value}` for a literal and a non-literal body. Chose: pass through. Over: rebuild with atom `Map.get`. Because: the value is already the struct (D6B-77). Commits us to: the emitted body of a constructor TYPE is always a struct. By: Opus (GREEN, slice6b-host-structs)

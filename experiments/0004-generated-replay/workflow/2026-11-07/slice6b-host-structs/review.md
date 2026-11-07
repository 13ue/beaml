# TEST and review: slice 6b step 11 (constructor TYPES are structs at the host, `T.new/1`)

**[Observed]** TEST phase and normal fresh review, 2026-11-07. Base: HEAD 45f43bc2. No source and no test changed. No commit.
Read: [plan.md](plan.md), [spec.md](spec.md), [notes.md](notes.md) (GREEN, 13-row table, D6B-97 to D6B-101), [red-review.md](red-review.md) (M1 to M3), DL-106, DL-117, DL-120 in the [decision log](../../../../../wiki/planning/decision-log.md), `git show 45f43bc2`.
By: Opus (TEST/review, slice6b-host-structs) for every judgement in this file.

## Verdict

- **PASS. No block.** Two medium notes. Docs defects listed for the docs phase.
- By: Opus (TEST/review, slice6b-host-structs)

## TEST results

- **[Observed]** `python3 -B experiments/0004-generated-replay/run.py`: exit 0, status `pass`, 14 of 14 steps pass.
  Result dir: `experiments/0004-generated-replay/results/20261107T165145154357Z` (drift sub-run `results/20261107T165212652407Z`).
  - compiler (cargo test 19 + 14), lib-freeze, arms 11, drift, stored-types 33, slice2-replay 21, slice3-types 69, slice3-replay 31, slice4-retire 87, slice4-replay 27, slice5-syntax 60, slice5-squash 24, slice5-replay 12, slice5-rewrite 5.
- **[Observed]** unittest, one file each, all OK:
  - `drift_test` 5, `slice6_constructor` 25, `slice6_decode_ctor` 8, `slice6_decode` 10, `slice6_enum` 20, `slice6_failure` 22.
  - `slice6_fmt` 25, `slice6_host_struct` 3, `slice6_int` 16, `slice6_pipe` 12, `slice6_record` 5, `slice6_struct_order` 3.
  - slice6 total 149 of 149 (146 before step 11, plus 3 in `slice6_host_struct`).
- **[Observed]** `experiments/0001-syntax-to-beam/run.py`: pass, `results/20261107T170743976936Z`.
- **[Observed]** 0001: `cargo fmt --check` OK, `cargo clippy -- -D warnings` OK, `cargo test` 19 + 14 pass.
- **[Observed]** `scripts/lint_wiki.py`: 81 files, 0 errors.
- By: Opus (TEST/review, slice6b-host-structs)

## M3 check: changed assertions against the plan table

- **[Observed]** `git show 45f43bc2 -- experiments/0004-generated-replay/tests/`, compared row by row with the plan table.
- Rows 1 to 12 match the plan wording: `constructor_ok`, `wrap_ok`, `read_pattern`, `keep_passes`, `plain_ok`, `call_form`, both build lines, `record_field_in_constructor`, `first_clause_ok`, `second_clause_ok`, `pair_declined_pipe`, `call_pair`, `EUR`, `declined_via_pipe`, `replay_declined`.
- Row 13 (`"defmodule NonZeroInt do"` from `absent` to present) is outside the plan table. notes.md records it as a main-agent Repair under DL-106 (By: Fable). D6B-73 requires that module. Accepted.
- Two additions in `slice6_host_struct_test.py` (`m2_struct_wrong_field_type_rejected`, `m2_nested_atom_key_map_rejected`) tighten the new test (red-review M2). They loosen nothing.
- No other test line changed. No reject text, wire input or stored record changed. RED review M3 is closed.
- By: Opus (TEST/review, slice6b-host-structs)

## Hand probes (scratch dir, no fixture change)

Source: TYPE `Sup { a, b }` with signatures `(a, b)` and `(a)`; TYPE `Two` with failing signatures `(n, m)` and `(n)`; `NonZeroInt` with `fn hold`.

| Probe | Result | Rule |
|---|---|---|
| `Sup.new(%{a: 1, b: 2})` | `{:ok, %Sup{a: 1, b: 2}}` | D6B-99 |
| `Sup.new(%{a: 1})` | `{:ok, %Sup{a: 1, b: 0}}` (second signature) | D6B-99 |
| `Sup.new(%{a: 1, c: 3})` | `{:error, {:no_signature, "Sup.new/1: ..."}}`, no help line | D6B-97, D6B-98 |
| `Sup.new(%{"a" => 1, b: 2})` | `:no_signature` with the help line | D6B-98 |
| `Sup.new(%{a: "1"})` | raises `invalid BEAML input` | D6B-101 |
| `Two.new(%{n: 0, m: 5})` | `{:error, %IsZero{}}`; signature 2 is not tried | D6B-101 |
| `hold(struct!(Other.NonZeroInt, value: 4))` | raises `invalid BEAML input` | nominal check |
| `hold(struct!(Other.BeamlSpike.NonZeroInt, ...))` | raises | nominal check |
| `hold(%BeamlSpike.NonZeroInt{value: 0})` | passes | DL-106 limit |
| `hold(%BeamlSpike.NonZeroInt{})` (nil field) | raises | D6B-76 |
| `NonZeroInt.new(3)`, `new([n: 3])` | raise | D6B-100 |

- **[Observed]** The COMPILER rejects a subset signature before a superset signature (`unreachable signature`). So the superset case only exists with the superset first. Exact key match then picks the right signature.
- **[Observed]** `new/1` runs the signature clauses in source order. The first clause whose key pattern and `map_size` match runs, and its result is final, also an `{:error, _}`.
- **[Observed]** A forged map `%{__struct__: BeamlSpike.NonZeroInt, value: 4, x: 1}` passes the input check (no `map_size` on the struct check). Same class as the DL-106 deliberate-forgery limit. Dropped as low.
- By: Opus (TEST/review, slice6b-host-structs)

## DL-106 limit statement

- **[Observed]** Stated in [spec.md](spec.md) (Contract, Limit), [plan.md](plan.md) (Exclusions, H7) and the H7 test docstring.
- **[Observed]** Not stated in `experiments/0004-generated-replay/README.md`: the README has no step 11 text. Docs defect D1.
- By: Opus (TEST/review, slice6b-host-structs)

## Objections (medium, recorded, no block)

**N1 · Medium · The full-suite `pass` holds no step 11 evidence.**
- **[Observed]** `run.py` runs no `slice6_*_test.py` and no `drift_test.py`. The step 11 tests ran only through unittest, and unittest keeps no result directory.
- **[Inference]** Wrong outcome: the retained run `20261107T165145154357Z` reads as the step 11 proof, but a step 11 regression would not change it. The evidence for 149 of 149 is this file only.
- Smallest check: add the slice6 files to `run.py` as steps, or retain the unittest output in a result dir. A separate decision; not done here.
- By: Opus (TEST/review, slice6b-host-structs)

**N2 · Medium · D6B-97, D6B-98, D6B-100 stay a host-facing form without an OWNER entry.**
- **[Observed]** The `{:error, {:no_signature, text}}` tuple and the raise for a non-map are now generated and tested. The decision log has DL-117 only; red-review M1 asked for the class.
- **[Inference]** If the OWNER wants a raise, host code and tests change again. Smallest check: the main agent records the class of D6B-97 to D6B-100 in the decision log.
- By: Opus (TEST/review, slice6b-host-structs)

## Docs defects (list only, for the docs phase)

- D1: README has no step 11 section: struct form, `T.new/1` key-set rule, `:no_signature` tuple, DL-106 limit.
- D2: D6B-97 to D6B-101 are not in the decision log or `decisions-to-be-made.md`.
- D3: The register and `wiki/log.md` do not name the step 11 TEST run yet.
- D4: The limit "forged map with `__struct__` and extra keys passes" is not stated with the DL-106 limit.
- D5: The plan Limit "a struct from an older build with another field set" is untested; keep it as **[Inference]** in the README.
- By: Opus (TEST/review, slice6b-host-structs)

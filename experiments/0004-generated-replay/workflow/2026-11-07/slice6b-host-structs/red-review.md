# RED review: slice 6b step 11 (constructor TYPES are structs at the host, `T.new/1`)

**[Observed]** Fresh-context RED review, 2026-11-07. Base: HEAD bd8cb895. No compiler or test changed. `run.py` not run. No commit.
Read: [plan.md](plan.md), [plan-review.md](plan-review.md), [spec.md](spec.md), [notes.md](notes.md) (D6B-97 to D6B-101), [red-output.log](red-output.log), DL-106, DL-117, DL-120 in the [decision log](../../../../../wiki/planning/decision-log.md), `tests/slice6_host_struct_test.py`, `slice6/host-struct/nonzero.beaml`, `git show bd8cb895 --stat`.
By: Opus (RED review, slice6b-host-structs) for every judgement in this file.

## Verdict

- **PASS. No block.** Three medium notes below. GREEN can start after the main agent classifies note M1.
- By: Opus (RED review, slice6b-host-structs)

## Re-run

- **[Observed]** Scratch build: `git archive HEAD experiments/0001-syntax-to-beam`, `cargo build --offline`. Run with `BEAML_SPIKE=<scratch>/target/debug/beaml-spike python3 -B experiments/0004-generated-replay/tests/slice6_host_struct_test.py`.
- **[Observed]** Exit 1, `Ran 3 tests`, `FAILED (failures=19)`. Same as `red-output.log`.
- **[Observed]** 19 fail: H1 (2), H2 (7), H3 (2), H3e (2), H4 (1), H9 (4), H7 (1).
- **[Observed]** 5 guards pass: H1g, H5, H6 (2 cases), H8 (45 sources and `payments.beaml`).
- **[Observed]** Every failure reason is missing behaviour: `false` (a String-key map passes), `invalid BEAML input` on the struct, `NonZeroInt.new/1 is undefined`, `module BeamlSpike.Pair` / `Label is not available`. No setup failure: compile, `elixirc --warnings-as-errors` and `checks.exs` all run.
- **[Observed]** `git diff 52550d4f bd8cb895 -- experiments/0001-syntax-to-beam` is empty. So the H8 hashes of the 52550d4f build equal the HEAD build, and they are fixed literals in the test. A GREEN build cannot re-compute them.
- **[Observed]** No H8 source has a record constructor (scan of `type X` and `fn X`). No D6B-97 to D6B-101 collision in `wiki/` or other ledgers.
- By: Opus (RED review, slice6b-host-structs)

## Faithfulness to DL-106 and DL-117

- **[Verified]** One map with atom keys, also for one parameter: H2 uses `new(%{n: 3})`; H2 naked `new(3)` is not a form.
- **[Verified]** Keys pick the signature: H9 `Label` picks signature 1 or 2; the second result `"a b"` proves that the clause body runs.
- **[Verified]** String keys match no signature, with the help line: `h2_new_string_keys_help`. It also stops a GREEN that converts String keys to atoms.
- **[Verified]** Struct result, `{:ok, struct}` / `{:error, failure}`: H2, H4. `{:ok, map}` fails H2 and H4: a map is never `==` to a struct.
- **[Verified]** Host check requires the struct, also nested: H1, H1g, H3, H3e use a valid value `4`, so a check that runs the constructor on the map fails.
- **[Verified]** Constructor runs in `new/1`: `new(%{n: 0})` must give `IsZero`; `Pair` maps keys `x, y` to fields `a, b`.
- Stricter than the decisions: D6B-97 (exact error tuple and text), D6B-98 (help line only for a non-atom key), D6B-99 (equal key sets), D6B-100 (raise for a non-map). DL-117 does not state these. See M1.
- By: Opus (RED review, slice6b-host-structs)

## DL-120 and steps 12, 12b

- **[Verified]** The fixture has no EFFECT. No constructor reaches an EFFECT. DL-120 and the step 12 span rule do not touch it.
- By: Opus (RED review, slice6b-host-structs)

## Objections (medium, recorded, no block)

**M1 · Medium · D6B-97, D6B-98 and D6B-100 fix a host-facing form that DL-117 left open.**
- **[Inference]** DL-117 is an OWNER (Migrate) decision. It says a String-key map "fails with a help line", not how. The tests now pin `{:error, {:no_signature, text}}` and a raise for a non-map. Host code will branch on this tuple.
- **[Inference]** Wrong outcome if the OWNER wanted a raise: the host-facing contract changes after GREEN, with a second test edit.
- Smallest check: the main agent classifies D6B-97, D6B-98, D6B-100 (Repair or Migrate) before GREEN. The RED author raised the same point in `notes.md`.
- By: Opus (RED review, slice6b-host-structs)

**M2 · Medium · No case checks the field TYPES inside the struct, nor an atom-key map in a nested field.**
- **[Inference]** A GREEN with only `is_struct(v, __MODULE__.NonZeroInt)` and no field check passes all 24 cases. D6B-76 asks for field checks through `Map.get(v, :f)`.
- **[Inference]** Wrong outcome: `keep(%NonZeroInt{value: "4"})` or `keep(%NonZeroInt{})` (field `nil`) passes, and a wrong TYPE reaches BEAML code. This is a TYPE error, not the DL-106 rule limit of H7.
- Smallest test: `invalid.(fn -> BeamlSpike.keep(st.(NZ, value: "4")) end)` and `invalid.(fn -> BeamlSpike.unbox(%{"n" => %{value: 4}}) end)`. Both pass today (guards).
- By: Opus (RED review, slice6b-host-structs)

**M3 · Medium · The changed existing assertions stay to GREEN.**
- **[Observed]** The plan table lists 12 assertions in four existing test files. RED did not change them (notes.md, open points).
- **[Inference]** So the GREEN worker edits expected values in tests. A false pass is possible when GREEN copies its own output.
- Smallest check: the TEST or review phase diffs each changed assertion against the plan table value, line by line.
- By: Opus (RED review, slice6b-host-structs)

## Dropped (low)

- H8 does not cover `drift/*`, `bad/*`, `examples/order-flow.beaml`, `slice6/fmt/header*`, `slice6/fmt/marks*`. The plan says "at least"; other suites compile these.
- Three H8 sources exit 1 with empty stdout; they guard the exit code only.
- By: Opus (RED review, slice6b-host-structs)

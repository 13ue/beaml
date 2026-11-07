# Decisions: slice 6b step 11 (constructor TYPES are structs at the host)

**[Proposal]** PLAN phase, 2026-11-07. Design decisions that DL-106 and the decision log do not settle.
Classes follow Decision4. Undo and Repair entries give the default that the step worker takes. Migrate and Answer entries are OWNER questions.
Every entry carries a `By:` line (DL-107). The worker records each taken default again in its `notes.md` (DL-097). A Repair that changes language behaviour or a check also gets a decision-log entry at the end of its phase.

## OWNER question

### Q6B-16 · Migrate · The form of `T.new` for a constructor with more than one parameter or more than one signature (blocks H9 only)

- **Context.** **[Verified]** DL-106 names `new/1`. The DL-092 example `NonZeroInt` has one parameter, so `NonZeroInt.new(3)` fits both options. **[Verified]** `Pair` (`slice6/pipe/pipe.beaml`) and `Amount` (`slice6/decode-ctor/orders.beaml`) have two. **[Verified]** A record constructor can have several signature lines; the code call picks one statically by arity and TYPE (D6B-16). The host call has no static TYPE.
- **Option A, positional.** `T.new/n` with the constructor parameters in order: `Pair.new("x", "y")`. Several signatures of one arity: the first signature whose `__beaml_valid__` checks accept the inputs, in source order. Challenge: `new/1` holds only for one parameter; the name differs from DL-106 text for the others.
- **Option B, one map.** Always `T.new/1`. One parameter: the value itself (`NonZeroInt.new(3)`). Several parameters: a map with the parameter names as String keys (`Pair.new(%{"x" => "x", "y" => "y"})`), the same form and signature choice as the decode through a constructor (DL-099, DL-084 K1, step 8 G4). Challenge: a one-parameter signature and a several-parameter signature of one TYPE read the argument differently; a map argument of a one-parameter `Map` field TYPE is ambiguous (no such TYPE today).
- **Option C, keyword list.** `Pair.new(x: "x", y: "y")`. Named and order-free like B. No conflict with a `Map` field TYPE. Challenges: atom names at the host; it differs from the String-key form of the decode (DL-099). By: Opus (PLAN REPAIR, slice6b-host-structs) (plan check, Q6B-16)
- **Why Migrate.** Host code calls it. A wrong form makes every host call site change.
- **Interim.** H1 to H8 use `NonZeroInt` only. H9 and the `T.new` of a several-parameter constructor wait. Until the answer, GREEN emits `T.new/1` only for one-parameter constructors with one signature, and no `new` for the others (the `new_T_k` functions stay).
- By: open, decided later by `13ue`. Question by Opus (PLAN, slice6b-host-structs).

## Undo and Repair defaults

Format: **ID · class · decision.** Chose / Over / Because. Commits us to (Repair only).

**D6B-73 · Repair · One nested struct module per constructor TYPE, atom keys, at the top of `BeamlSpike`.**
Chose: `defmodule T do import Kernel, only: [defstruct: 1, def: 2] defstruct [:f1, ...] ... end`, emitted by `emit_structs` with the failure structs, before the first function. A TYPE that is a constructor TYPE and a failure TYPE gets one module. Over: String-key maps with a tag key. Because: DL-106 "structs like the failure records of step 2"; step 8 G3 showed that a struct module must come before its first use. Commits us to: a constructor TYPE has one Elixir form (struct) as success and as failure; D6B-07 "two forms" stays for plain records.
By: Opus (PLAN, slice6b-host-structs)

**D6B-74 · Repair · `T.new` calls the constructor and always returns a tuple; `new_T_k` stays.**
Chose: `def new(a0)` inside the struct module calls the parent `new_T_1(a0)` through the `@parent` pattern of `Replay` (the arm tree renames the module). A constructor without `!` gives `{:ok, struct}` too. The public `new_T_k` functions stay: the generated code and the step 3, 5, 8 tests call them. Over: rename `new_T_k` to `T.new`. Because: DL-106 names `{:ok, struct}` or `{:error, failure}`; both entries run the same clauses, so neither is a way around the constructor. Commits us to: two public names for one constructor. Form for several parameters: Q6B-16.
By: Opus (PLAN, slice6b-host-structs)

**D6B-75 · Undo · Literal and pattern of a constructor TYPE emit `%__MODULE__.T{f: v}`.**
In the one `Node::Record` arm of `emit_node`. A pattern with fewer fields stays a partial struct pattern. Alternative: a converter call after the map literal. Reason: one emit point, no runtime step.
By: Opus (PLAN, slice6b-host-structs)

**D6B-76 · Repair · The host input check requires the struct, at every depth.**
Chose: `defp __beaml_valid__(v, "T") when is_struct(v, __MODULE__.T)` with the field checks on `Map.get(v, :f)`. A String-key map of the same shape falls to `__beaml_valid__(_, _), do: false`. Nested fields and enum payloads follow, because they call the same function. Over: a check at the top-level argument only. Because: DL-106 "also in nested fields". Commits us to: every public wrapper, the output check and the decode shape check reject a map where a constructor TYPE stands; the error text stays `invalid BEAML input` (D6B-82).
By: Opus (PLAN, slice6b-host-structs)

**D6B-77 · Repair · `result()` passes a constructor TYPE failure value through.**
Chose: a non-literal body whose failure TYPE is a constructor TYPE gives `{:error, value}`; a literal body gives the struct literal. Over: today's rebuild `%F{f: Map.get(v, <<"f">>)}`. Because: on a struct the String-key `Map.get` gives `nil` for every field (inference from `result()`; H6 checks it). Commits us to: H6.
By: Opus (PLAN, slice6b-host-structs)

**D6B-78 · Undo · The decode through a constructor returns the struct from `new_T_k`.**
No change to `__beaml_from_T` (step 8 G4) or to the Rust `--stored` check (step 8 G7). The shape check sees the struct through D6B-76. The RESPONSE RECORD holds wire values only (today `body_base64`, after 6a `value`). Reason: DL-101 already routes the decode through the constructor.
By: Opus (PLAN, slice6b-host-structs)

**D6B-79 · Undo · Enum values stay tuples; plain records stay String-key maps.**
An enum with a constructor is the decode path only (DL-100), so its variants have no only-way-in to protect. A plain record that holds a constructor field is a String-key map with a struct inside (DL-106 "plain records keep their form").
By: Opus (PLAN, slice6b-host-structs)

**D6B-80 · Undo · Fixture and test file names.**
Fixture `slice6/host-structs/nonzero.beaml`; test `tests/slice6_host_struct_test.py`; ledger `slice6b-host-structs/`. Alternative: extend `slice6_constructor_test.py`. Reason: one ledger per step; the step 3 file only changes its named assertions.
By: Opus (PLAN, slice6b-host-structs)

**D6B-81 · Undo · No new check for struct module names.**
A constructor TYPE named `Http`, `Replay` or `Retired` collides with a generated module, as a failure TYPE already can. Alternative: a reserved-name reject now. Reason: an existing gap, not new in step 11; recorded as a limit.
By: Opus (PLAN, slice6b-host-structs)

**D6B-82 · Undo · The input check keeps the text `invalid BEAML input`.**
Alternative: a text that names `T.new`. Reason: every wrapper has one raise text today; a better text is a separate change.
By: Opus (PLAN, slice6b-host-structs)

**D6B-83 · Undo · "Constructor TYPE" is plain text in this step, not a glossary term.**
Alternative: add RECORD CONSTRUCTOR to `GLOSSARY.md` now. Reason: the PLAN changes task records only. The docs phase of step 11 adds the term first, then uses it.
By: Opus (PLAN, slice6b-host-structs)

## Points the decisions do not settle (for the worker, class Undo)

- `is_struct/2` or a struct pattern in the `defp` head. Either is fine if `--warnings-as-errors` passes.
- The exact place of `def new` inside the struct module (before or after `defstruct`).
- The unit test name `constructor_types_are_structs` and its three emit asserts.

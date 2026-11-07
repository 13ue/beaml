# Decisions: slice 6b compiler

**[Proposal]** PLAN phase, 2026-11-07. Each entry is a design decision that the code needs and the decision log does not settle.
Classes follow Decision4 (Undo / Repair / Migrate / Answer). Undo and Repair entries give the default that the step worker takes.
Migrate and Answer entries are OWNER questions. A step that depends on one is blocked until the OWNER answers.
A step worker records each taken default again in its `notes.md` (DL-097). A Repair that changes language behavior or a check also gets a decision-log entry at the end of its phase.

## OWNER questions

### Q6B-1 · Migrate · Where does the decode read the inputs of an enum constructor? (blocks step 8)

- **Context.** DL-084 K1: the parameter names of a signature are the body keys. A field `state: PaymentState` with `fn PaymentState status: String, decline_reason: String` does not say from which JSON object `status` and `decline_reason` come, nor what the key `state` does.
- **Option A.** Keys of the object that holds the field. The body is `{"order_id": .., "status": "declined", "decline_reason": "card"}`. The key `state` is not read; the field name is only the name inside BEAML. Two fields with constructors that share a key read the same value.
- **Option B.** Keys inside the field's own value. The body is `{"order_id": .., "state": {"status": "declined", "decline_reason": "card"}}`. A one-input signature reads the field's value directly (`"state": "ok"`), the same key as ENUM LITERALS.
- **Why it is Migrate.** Every source with a constructor field depends on it, and the producer's body shape must match it. A wrong guess reads wrong keys in every decode.

### Q6B-2 · Migrate · Does an enum constructor make itself the only way to build its variants? (blocks step 9)

- **Context.** DL-092 restricts the record literal of a TYPE with a constructor to that constructor's clauses, and says every type "gets the same checked-constructor pattern". DL-082 and DL-088 describe the enum constructor as the decode path only.
- **Option A.** Yes. `Pending` as an expression is legal only inside `fn PaymentState` clauses; ordinary code calls the constructor. Patterns stay free.
- **Option B.** No. The enum constructor is only the decode path of outside data. Code builds variants directly.
- **Interim.** Step 4 builds no restriction (the state before the decision). Step 9 adds the check only for option A.

### Q6B-3 · Migrate · Does the decode of outside data go through the constructor of a record TYPE?

- **Context.** DL-092 makes the constructor the only way in. The generated EFFECT decode builds the output record directly, which would bypass the check.
- **Option A.** Yes. The decode calls the constructor; its failure becomes the typed reject `decode` (or a new reason).
- **Option B.** No. A TYPE with a constructor cannot be an EFFECT input, output or failure TYPE, nor a field of one.
- **Interim.** Slice 6b rejects such a TYPE in every EFFECT position (D6B-19). This blocks no step; it limits steps 3 and 7.

### Q6B-4 · Answer · Redacted fields in an EFFECT output and the stored body

- **Evidence.** **[Verified]** The RESPONSE RECORD stores the raw response body (`body_base64`, `body_sha256`) and the full EFFECT input (`request`), `main.rs` `emit_effect`. **[Verified]** DL-089: "Spans, logs and records never hold the value". **[Verified]** DL-029: privacy is the highest goal. **[Inference]** A response with a redacted field stored raw breaks DL-089. A body with the key removed fails the replay decode of a required field and changes `body_sha256`. **[Unknown]** Whether a later production store keeps RESPONSE RECORDS; a stored PII value cannot be taken back.
- **Option A.** A redacted field in an EFFECT output TYPE stays a compile error.
- **Option B.** The RESPONSE RECORD stores the body without redacted keys, with a digest of the cut body; the replay decode accepts a missing redacted field as a marked absent value.
- **Challenges.** Option A blocks real responses with PII (a card holder echoed back). Option B changes the RESPONSE RECORD contract and the replay check for the request and the body, and needs a new TYPE state "absent because redacted".
- **Interim.** Step 6 rejects a redacted field in any EFFECT output TYPE (D6B-34). No recommendation.

## Undo and Repair defaults

Format: **ID · class · decision.** Chose / Over / Because. Commits us to (Repair only).

### Baseline

**D6B-01 · Repair · Step 0 repairs the formatting and lint baseline before any behavior step.**
Chose: `cargo fmt` and two lint rewrites, no behavior change. Over: accept the 4 fmt hunks and 2 clippy errors in every step. Because: every step check must be green, and `0001/run.py` fails today. Commits us to: one extra commit before step 1.

### Int (step 1)

**D6B-02 · Repair · `Int` is a built-in TYPE with integer literal patterns and expressions.**
Chose: `Int` like `String`: literals, patterns, coverage with an `other-int` sentinel, `is_integer` validity. Over: a String-based fixture for DL-092. Because: DL-092 and DL-093 use `Int` in their examples. Commits us to: `Int` in the language before arithmetic is decided.

**D6B-03 · Undo · No arithmetic, no negative literal, no `Int` in EFFECT inputs or outputs in 6b.**
The lexer limit (u32) stays. EFFECT decode stays String (plus enums, step 7).

### Failure position (step 2)

**D6B-04 · Repair · Any TYPE can stand after `!` on a `fn`.**
Chose: `String`, `Int`, records and enums. Over: records only (today). Because: DL-092 "Any type can stand on the failure side", DL-093 `-> String ! Int`. Commits us to: a non-record failure has no struct module. The EFFECT rule (one record with `reason: String`) stays.

**D6B-05 · Repair · The TYPE of a clause body decides success or failure (E1).**
Chose: a body of the output TYPE emits `{:ok, v}`, a body of a failure TYPE emits `{:error, v}`; a whole-body pipe may end in either. Over: a marker. Because: DL-093 E1, no `fail` keyword, and non-overlap makes the TYPE decide statically. Commits us to: the overlap check is the only guard of this rule.

**D6B-06 · Repair · The overlap check uses `same_type`.**
Chose: two records with equal fields overlap (structural records). Over: name equality only. Because: with structural records the body TYPE could not decide between them. Commits us to: a structural pair is an error with the same help line.

**D6B-07 · Repair · A record failure value from a clause body is the failure struct.**
Chose: `%__MODULE__.IsZero{...}` with atom keys, the same shape as an EFFECT failure. Struct modules are emitted whenever a record failure TYPE exists; with an EFFECT they stay at their place today, so the orders output stays byte-identical. Over: a plain map. Because: one failure TYPE gets one shape on `{:error, _}`, also through a pipe. Commits us to: a record TYPE has two Elixir forms (map as value, struct as failure).

**D6B-08 · Undo · The overlap check also runs on EFFECTS.**

**D6B-09 · Undo · Error text.** `error: fn f: the success TYPE String is also a failure TYPE` and `help: give the failure a TYPE of its own (for example type FError { reason: String }), or remove String after !`. The worker fixes the exact text in the step.

**D6B-10 · Undo · A variant is no TYPE.** A variant name in a TYPE position stays `unknown type`, with a help line that names its enum. So "a variant against its enum" cannot overlap; `-> E ! E` is the overlap case.

### Record constructor (step 3)

**D6B-11 · Repair · A constructor is an uppercase `fn` named like a declared `type` or `enum`; its output is that TYPE.**
Chose: any other uppercase `fn` name or another output is an error. Over: free uppercase functions. Because: DL-092 and DL-082 name the constructor after its TYPE. Commits us to: uppercase `fn` names mean constructors only.

**D6B-12 · Repair · A signature line is a `fn` without `=`, with `name: TYPE` parameters only.**
Chose: the clauses below take their TYPES by position; a clause annotation must equal the signature TYPE. Over: patterns in a signature line. Because: DL-084 K1 needs a name per input. Commits us to: a signature line names every input.

**D6B-13 · Repair · A clause belongs to the nearest earlier signature line of the same name.**
Chose: when a name has a signature line, a clause before the first one is an error. Without a signature line, today's rule stays (each clause types its own parameters). Over: grouping by arity or TYPES. Because: the source order is the rule (DL-085). Commits us to: moving a clause changes its signature.

**D6B-14 · Repair · Several signature lines only for constructors.**
Chose: a lowercase `fn` has at most one signature line. Over: overloading for every function. Because: DL-084 allows several signatures "of one constructor". Commits us to: widen later if needed.

**D6B-15 · Repair · Each signature compiles to its own Elixir function `new_<TYPE>_<k>` (k from 1 in source order).**
Chose: public `def new_<TYPE>_<k>` with the validity wrapper like every `fn`, private clauses `__beaml_new_<TYPE>_<k>`; a clash with a user `fn` name is a `duplicate name` error. Over: one Elixir function for all signatures. Because: clauses of two signatures with the same arity would mix (a catch-all of signature 1 would take an `Int` of signature 2). Commits us to: these names are the host-visible constructor names.

**D6B-16 · Repair · A call `T(args)` or a pipe step `|> T` takes the first signature whose arity and input TYPES fit.**
Chose: static choice in source order; no fit is an error that names the argument TYPES. Over: runtime dispatch. Because: DL-085 order rule, and all TYPES are known at compile time. Commits us to: two signatures with equal TYPES: calls always use the first.

**D6B-17 · Repair · A TYPE with a constructor is nominal.**
Chose: `same_type` is name equality when either side has a constructor. Other records stay structural. Over: all records nominal. Because: DL-092 "an Int is not a NonZeroInt"; a structural twin would bypass the constructor. Commits us to: a possible later OWNER question "all records nominal?" (not needed by 6b).

**D6B-18 · Repair · The record literal of a TYPE with a constructor is legal only in expressions of its own constructor clauses; record patterns stay legal everywhere.**
Chose: construction is restricted, reading is not. Over: patterns restricted too. Because: DL-092 speaks of "the way in". Commits us to: matching `NonZeroInt { value }` stays free.

**D6B-19 · Repair · A TYPE with a constructor is rejected as EFFECT input, output or failure TYPE and as a field of one (interim for Q6B-3).**

### Enum (step 4)

**D6B-20 · Undo · A bare variant `A` means `A()` in patterns and expressions.** `A()` stays legal (existing tests). In a pattern, an uppercase bare name is a variant, never a variable.

**D6B-21 · Repair · ENUM LITERAL rules.**
Chose: in an enum with literals, every variant has a literal and no payload, except at most one keep-value variant `X(String)` without a literal. The keep-value variant is found by its shape, not by the name `Unknown`. Over: the reserved name `Unknown`. Because: DL-062 U1 makes `Unknown(String)` a normal declared variant. Commits us to: a rename of `Unknown` keeps the behavior.

**D6B-22 · Undo · DL-088 error text.** `error: enum E has literals and a constructor` and `help: keep the literals for a 1:1 mapping or the constructor fn E, not both`.

**D6B-23 · Repair · An unreachable signature is an error.**
Chose: signature B below A is unreachable when every `(name, TYPE)` of A is also in B. Over: no check, or a check by TYPES only. Because: DL-085 note and DL-087; with these keys present, A always matches first. Commits us to: a key-subset check for every constructor, used in decode or not. Two equal literals are an unreachable literal, also an error.

**D6B-24 · Repair · First match wins in the generated code.**
Chose: Elixir clauses of a signature stay in source order (today); the decode tries the signatures in source order (step 8). Over: sorted clauses. Because: DL-085. Commits us to: source order is part of the semantics.

**D6B-51 · Repair · An enum without literals and without a constructor in an EFFECT output field is a compile error.** No decode path exists for it.

### Pipe (step 5)

**D6B-25 · Repair · `|>` binds weaker than `+` and ends at `,` and `)`.**
Chose: `a + b |> f` is `f(a + b)` (the Elixir order); steps stay bare names. Over: steps with arguments. Because: DL-086 decides the place, not new step forms. Commits us to: `|> f(x)` needs a later decision.

**D6B-26 · Repair · Step kinds: a 1-input `fn`, an EFFECT, a constructor (D6B-16 with one input), a variant with exactly one payload.**

**D6B-27 · Repair · A nested pipe (not the whole body) with an EFFECT step or a failing step is a compile error in 6b.**
Chose: error with `help: make the pipe the whole body`. Over: lift nested failing steps into a `with`. Because: smallest correct emit; DL-086 keeps the `!` rule but does not ask for nested failing steps. Commits us to: a later step may lift the limit without breaking sources.

**D6B-28 · Repair · Spans and the one-clause rule stay only for a whole-body pipe with an EFFECT step.**
Chose: that pipe keeps `emit_chain` with spans (byte-equal orders output). Every other pipe compiles to plain calls (a `with` for failing steps), no spans. Over: spans for every pipe. Because: a constructor clause with a pipe body would otherwise need `ProbeSupport` in a module without EFFECTS. Commits us to: pure pipes are not traced per step.

### Redacted (step 6)

**D6B-29 · Repair · `redacted` stands before a field TYPE in a `type` only.** Not in enum payloads, signature lines or MIGRATE CHANGES in 6b.

**D6B-30 · Repair · `redacted` is not part of the TYPE VERSION fingerprint.**
Chose: the `type` key and the `--stored` compare ignore it. Over: a new TYPE VERSION when a field becomes redacted. Because: the data shape does not change. Commits us to: marking a field redacted needs no MIGRATE STEP.

**D6B-31 · Repair · `with` list: `with f1, f2` after the `)` of the EFFECT target.**
Chose: comma separated, at least one name, each a top-level redacted field of the EFFECT input TYPE, no duplicates; else a compile error. Over: dotted paths. Because: DL-089 shows one top-level name. Commits us to: a nested redacted field can never be sent in 6b.

**D6B-32 · Repair · Two projections.**
Chose: the wire body drops every redacted field (any depth) except the `with` names. Spans, `ProbeSupport.event`, the RESPONSE RECORD `request` and the replay `request_mismatch` compare use the value without any redacted field. Over: one projection. Because: DL-089 "Spans, logs and records never hold the value", also for named fields. Commits us to: replay compares redacted requests only.

**D6B-33 · Repair · Redaction removes the key; no placeholder value.**
Over: a `"[redacted]"` marker. Because: smallest change; a marker would break the TYPE validity of the field. Commits us to: a reader cannot tell "redacted" from "absent" in a record.

**D6B-34 · Repair · A redacted field in an EFFECT output TYPE (any depth) is a compile error (interim for Q6B-4).**

### Decode of literals (step 7)

**D6B-35 · Repair · An ENUM LITERAL field reads its own key.**
Chose: the field `state` reads the key `state`; a literal gives its variant, another String gives the keep-value variant, a non-String is the typed reject `decode`. Over: anything else. Because: DL-082 L is a 1:1 mapping of a String. Commits us to: literal enums read flat String values.

**D6B-36 · Repair · An enum field in an EFFECT output needs a keep-value variant (DL-065).** Without one: a compile error with a help line to add `Unknown(String)`.

**D6B-37 · Repair · `Unknown` is not stored separately.**
Chose: the RESPONSE RECORD keeps the raw body as today; a replay decodes again. A decode that yields a keep-value variant sets the span attribute `unknown_fields` (sorted field names, no values). Over: a new RESPONSE RECORD key. Because: the raw body already keeps the value; DL-028 asks that Unknown stays visible. Commits us to: the record format stays version 1.

**D6B-38 · Repair · The fingerprint of an enum field holds the enum name only.**
Chose: a new literal does not change the TYPE VERSION. Over: the literals in the fingerprint. Because: the record shape does not change. Commits us to: a replay of an old record uses the current mapping (an old `Unknown("refunded")` can replay as `Refunded`).

**D6B-39 · Repair · An enum field in an EFFECT output TYPE with a MIGRATE CHAIN or a VERSION MARK is a compile error in 6b.** The versioned decode validates raw values before the steps; enums need a mapping there first.

**D6B-40 · Repair · An enum field in an EFFECT input TYPE is a compile error.** **[Inference]** Today such a source compiles and the tuple form has no JSON encoding; this closes an existing gap.

### Decode through a constructor (step 8, blocked by Q6B-1)

**D6B-48 · Repair · A signature matches when all its keys are present and each value is valid for its TYPE.** A wrong TYPE tries the next signature; no match is the typed reject `decode`.

**D6B-49 · Repair · `unknown_keys` treats every parameter name of every signature as declared.**

**D6B-50 · Repair · Keep-value check (DL-065).**
Chose: for a constructor used in an EFFECT decode, the last clause of each signature binds every input as a variable or `_`, and its body puts at least one String input variable into the keep-value variant. Over: every input kept. Because: the OWNER example `fn PaymentState other, _ -> PaymentState = Unknown(other)` drops `decline_reason`. Commits us to: a constructor may drop the other inputs.

### `beaml fmt` (step 10)

**D6B-41 · Repair · `beaml-spike fmt SOURCE.beaml` rewrites the file in place.**
Chose: `write_atomic`, the unified diff on stdout, exit 0; an invalid source writes nothing and exits 1. Over: print the result. Because: DL-081 "writes"; the `--remove-dead` path already has both parts. Commits us to: no `--check` until needed.

**D6B-42 · Repair · `fmt` edits source text by token ranges.**
Chose: only the VERSION MARK tokens and the spaces before argument columns, `->` and `=` change; comments and every other byte stay. Over: print from the AST. Because: the lexer drops comments. Commits us to: other style rules need their own decision.

**D6B-43 · Repair · VERSION MARK form (b), the safe reading of DL-081.**
Chose: remove a mark only when the newest version stays the same without it (a chain from v1 that ends at the mark, or `v1` with no chain); write `v<newest>` when the chain starts above v1 and has no mark; keep every other mark. Over: the literal text "removes a mark when there is no chain". Because: **[Verified]** `newest_version` reads a mark without a chain as the newest version, so `type T v3 { }` without a chain would become version 1 and renumber stored records. Commits us to: a contradiction in DL-081 text, shown to the OWNER in the step report.

**D6B-44 · Repair · Alignment groups.**
Chose: consecutive single-line clauses of one `fn` name, with no blank line and no comment line between, form one group; each argument column, the `->` and the `=` are padded to one column. Consecutive single-line `effect` lines align `->` and `=` (DL-013). A multi-line clause ends a group. Over: aligning multi-line clauses. Because: DL-083 asks for a table of clauses. Commits us to: a blank line is the way to stop alignment.

**D6B-45 · Undo · `fmt` invariants as tests:** `fmt(fmt(s)) == fmt(s)`; the compiled output of `s` and `fmt(s)` is equal except the `beaml-declaration-v1` byte offsets.

**D6B-46 · Undo · `fmt` posts the action event `fmt` with the count of changed lines; no source text, no path.**

### Ledger

**D6B-47 · Undo · Fixtures in `experiments/0004-generated-replay/slice6/<step>/`, tests in `tests/slice6_<step>_test.py` plus Rust unit tests in `main.rs`.**

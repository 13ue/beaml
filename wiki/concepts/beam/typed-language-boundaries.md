# Types on BEAM: static meaning versus runtime evidence

Status: **[Verified]** selected precedents; **[Inference]** boundary consequences; **[Proposal]** BEAML decisions/examples. [Typed-source inventory](../../sources/typed-beam-languages.md); [VM evidence](../../sources/beam-vm-internals.md).

## Three different questions

| Question | Suitable evidence | What it does not establish |
|---|---|---|
| Does the compiler reject a mismatch in its supported core? | Type/effect/refinement rules plus pass invariants and negative cases | Correctness of foreign code, runtime data or a model's factual claim |
| Can static analysis find definite inconsistencies in this program? | A scoped analysis such as success typing or gradual inference | Acceptance by an all-paths safe-language type discipline |
| Does this untrusted value satisfy this runtime schema now? | Decoder/validator result tied to schema/version | Truthfulness, authorization, confidentiality or all future uses |

**[Inference]** These can complement one another. Calling all three “typed” hides the proof boundary central to the [product contract](../product-contract.md).

## Dialyzer's success-typing boundary

**[Verified]** The official analysis model says Dialyzer can miss bugs it cannot establish. When a source spec exists, it checks overlap with inferred argument/result types; overlap is not exact equality or full subset conformance. It can then trust their intersection, so an inaccurately restrictive spec can influence downstream diagnostics. [Pinned model/examples](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/lib/dialyzer/doc/guides/dialyzer_chapter.md#how-dialyzer-uses-function-specifications).

**[Proposal]** Constructed boundary example:

```text
foreign function declared: decode_invoice(raw) -> Validated<Invoice>
actual implementation:    returns raw map unchanged
```

Emitting a matching Erlang `-spec` does not make this implementation a decoder. A wrong overlapping spec can even narrow what another analysis sees. BEAML's boundary must perform the declared checks or explicitly mark the foreign function trusted/UNKNOWN; a clean Dialyzer report cannot certify the missing validator.

## Gleam shows ordinary-term code generation

**[Verified]** The inspected Gleam backend emits fieldless constructors as atoms and constructors with fields as tag-headed tuples, while generating type specifications separately. It has explicit phantom-variable handling in typespec generation. [Pinned constructor generator](https://github.com/gleam-lang/gleam/blob/69822bed994794f5c7d356eca53bf8e5bbaffdc8/compiler-core/src/erlang.rs#L367-L415).

**[Verified]** Gleam's official externals documentation says annotations are required/trusted for foreign implementations; incorrect annotations can cause runtime failures. Its guide documents ordinary target representations, including UTF-8 binaries for Gleam strings rather than Erlang character lists. [Externs tour](https://tour.gleam.run/advanced-features/externals/); [Representation guide](https://gleam.run/documentation/externals/).

**[Inference]** This is evidence that a typed language can use ordinary BEAM terms while checking more at compile time; it is not evidence those terms are unforgeable by arbitrary Erlang/Elixir. **[Proposal]** A proposed `InvoiceId` wrapper and `Validated<T>` tag must have a documented trust scope. If trusted foreign code can construct the same term, a tag alone is not proof of authorized creation. Runtime validators, module/process-controlled handles, version checks and explicit foreign trust serve different goals; choose the minimum mechanism consistent with the threat model.

## Prior art: Gleam

Evidence: [Gleam typed OTP source](../../sources/gleam-typed-otp.md) (`gleam_erlang` and `gleam_otp` v1.3.0). Questions: [D046](../../planning/decisions-to-be-made.md#d046--async-compute-otp-and-oban-from-beaml), [D049](../../planning/decisions-to-be-made.md#d049--pubsub-and-sockets-as-hard-typed-effects).

**[Inference]** Gleam types the send and the receive inside one program, at compile time. The wire stays an ordinary tuple, so anything outside the program (Erlang code, another node, older code after a reload) is trusted or decoded from `Dynamic`. BEAML's open part sits exactly there: records, replay and TYPE VERSIONS of messages in flight.

| Gleam construct | BEAML question | Copy or add |
|---|---|---|
| `Subject(message)`: one TYPE per channel | One TYPE (or an enum of TYPES) per topic (D049) | **[Proposal]** Copy: a topic declaration names its message TYPE once; publish and subscribe check against it. |
| Owner-only `receive`, `Selector(payload)` maps every source into one TYPE | Inbound ENTRY LINE for receive | **[Proposal]** Copy: a subscribe ENTRY LINE decodes into the head TYPE, as `ui.event` does; several topics feed one handler only through an explicit enum. |
| `select_other` / `select_record` give `Dynamic`; `decode` returns typed errors | Messages from host code or other nodes | **[Proposal]** Copy the split: a typed path for BEAML senders, a decode path for every foreign term. **[Inference]** BEAML's generated decode already plays the role of `decode`. |
| `actor.new` / `on_message` / `continue` / `stop` with typed state | GenServer from BEAML (D046) | **[Proposal]** Copy the shape: a handler `fn(state, msg) -> next` with closed outcomes. |
| `call` with a reply `Subject(reply)` inside the message | Request/reply between processes | **[Proposal]** Copy: the reply TYPE is part of the message TYPE, not a separate untyped return. |
| `Name(message)`, atoms made once, `register` takes any pid | Named processes, restart take-over | **[Inference]** Gleam trusts the name's TYPE. **[Proposal]** BEAML declares names statically and checks the registering module's handler TYPE at build. |
| `ChildSpecification(data)`, data not returned by the supervisor | Supervision from BEAML | **[Proposal]** Copy the builder; reach restarted children through declared names, not stored pids. |
| No record of a message | Every message is a record (format v3) | **[Proposal]** Add: publish and receive each write a record with the RECORD CORE, so a message is replayable. |
| No TYPE VERSION; FAQ: upgrades are not type checked | Old subscriber reads a new message | **[Proposal]** Add: a message carries its TYPE VERSION; the receiver runs the MIGRATE CHAIN on read, as for rows. |
| Glyn: PubSub with a decoder per scope; no official Phoenix.PubSub binding | Phoenix.PubSub as an EFFECT transport | **[Proposal]** Add a `pubsub` transport that wraps Phoenix.PubSub on the host; the decode on receive is generated, not hand-written. |

**[Inference]** The three most useful constructs: the typed `Subject`, the `Selector` that maps all sources into one payload TYPE, and the explicit `Dynamic` plus `decode` path for foreign messages. **[Unknown]** Whether BEAML wraps OTP itself or lets the host own the processes (D046) is not settled by this evidence.

## Elixir's current gradual system is not just typespecs

**[Verified]** Elixir v1.20's announcement describes inference and gradual checking without new user annotations, with types narrowed by use and further signature/recursive/parametric work still ahead. [Release explanation](https://elixir-lang.org/blog/2026/06/03/elixir-v1-20-0-released/). At v1.20.5, `Module.Types` documents static/dynamic/infer modes; `Module.Types.Descr` represents set operations and dynamic bounds using structures including BDDs. These are internal implementation precedents, not stable APIs. [Inference modes](https://github.com/elixir-lang/elixir/blob/4a28692668bef879029291b7ff329a84a1f933bb/lib/elixir/lib/module/types.ex#L1-L45); [Descriptor representation](https://github.com/elixir-lang/elixir/blob/4a28692668bef879029291b7ff329a84a1f933bb/lib/elixir/lib/module/types/descr.ex#L1-L140).

**[Proposal]** Worked narrowing problem: an Elixir assign map may reveal `amount` is numeric after an operation, yet that does not show a browser value is a positive `Decimal`, belongs to the current tenant, or retains its confidentiality label. Reusing host metadata can improve diagnostics within a declared supported subset; it must not upgrade dynamic host facts into stronger BEAML refinement/authorization/IFC evidence.

## Generic witnesses, typestate and effects need explicit lowering

**[Requirement]** The spec calls for schema witnesses, nominal newtypes, refinements, effect sets and typestate; affine streams are later. [Type-system source](../../sources/engineering-spec-v0.5.md). **[Proposal]** Distinguish static erasure from runtime evidence in the ABI:

```text
Extract<T>(text)
  compile-time: T must satisfy Schema + Validate
  runtime:     a specialized decoder OR explicit descriptor/witness for T
  boundary:    raw -> parsed -> validated -> checked refinement
```

A runtime generic function receiving only `text` cannot infer the intended schema from erased static intent. Decide specialization versus dictionary/witness arguments, stable schema identity, recursive schema support, cache invalidation and version compatibility. A phantom `Stream<Complete>` parameter can prevent certain source programs but cannot stop foreign code duplicating a handle or sending a late message. The runtime state/ownership protocol must match the static transitions; see [process lifecycle](processes-messages-and-otp.md).

**[Proposal]** Lower explicit effect-handler dictionaries as explicit runtime arguments/state where chosen. Define whether each call can allocate, throw, exit, block, send, or disclose; a host function that looks pure syntactically may invoke hidden effects. Tests should include a forged witness, wrong schema version, duplicate stream use, unknown foreign call and secret-valued error, with exact status/diagnostic and no unauthorized effect.

**[Unknown]** No reviewed BEAML soundness theorem, coherent trait algorithm, generic ABI or cross-language type-evidence format exists yet. These precedents identify mechanisms and failure cases; they do not settle those language decisions or endorse compatibility.

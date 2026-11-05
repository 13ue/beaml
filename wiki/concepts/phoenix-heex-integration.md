# Phoenix and HEEx integration

Status: **[Verified]** upstream facts and **[Proposal]** feasibility work; no integration has been executed. [Source inventory](../sources/beam-otp-phoenix.md).

## Preserve the framework boundary

**[Requirement]** Elixir owns LiveView callbacks, HEEx/components and routes; BEAML supplies optional contracts, descriptors and guarded domain APIs. [Product contract](product-contract.md). This research does not resolve the inconsistent language examples or generated exports identified in [specification gaps](../planning/specification-gaps.md).

**[Verified]** HEEx validates template structure. Component declarations warn about missing/unknown attributes and certain incorrect literal values, but do not perform runtime validation. [Phoenix.Component](https://phoenix-live-view.hexdocs.pm/Phoenix.Component.html#attr/3).

**[Inference]** Existing warnings cannot certify model schemas, nominal IDs, refinements, authorization, or every dynamic expression. **[Proposal]** Document exactly what BEAML adds and emit scoped evidence; do not turn a successfully compiled HEEx template into a universal safety claim.

## Official parser reuse has an API limit

**[Verified]** `TagEngine.compile/2` returns Elixir AST and accepts caller/file/line/indentation context. Its docs present it as an engine building block rather than a direct application API. [TagEngine](https://phoenix-live-view.hexdocs.pm/Phoenix.LiveView.TagEngine.html#compile/2).

**[Verified]** Tagged LiveView `v1.2.13` source calls `TagEngine.Parser.parse!` then `TagEngine.Compiler.compile`. Parser and compiler are marked `@moduledoc false`. Parsed node types retain tag open/close metadata and expression source; this is source inspection, not a stable external API guarantee. [Engine source](https://github.com/phoenixframework/phoenix_live_view/blob/v1.2.13/lib/phoenix_live_view/tag_engine.ex); [parser](https://github.com/phoenixframework/phoenix_live_view/blob/v1.2.13/lib/phoenix_live_view/tag_engine/parser.ex).

**[Verified]** Elixir AST has public line/location metadata, optional token metadata and columns; quoted code discards some positions. Private metadata can change; marking code generated can suppress warnings. [Macro metadata](https://elixir.hexdocs.pm/Macro.html#t:metadata/0).

**[Proposal]** The first adapter should cover named components, literal event names, declared assigns and constrained expressions. Parse `.heex` and `~H` using pinned official behavior, preserving original byte spans before transformations. Keep BEAML semantic IDs and mapping as a separate artifact; do not rely on AST metadata surviving expansion. Dynamic attributes/events, metaprogramming and unsupported forms produce UNKNOWN/refused edits. A long-lived editor parser must also avoid atom exhaustion and avoid compiling untrusted macros merely to obtain metadata. Pin/test any undocumented parser dependency and report unsupported versions explicitly.

## LiveView lifetime is observable behavior

**[Verified]** Mount runs for disconnected HTTP rendering and again for the connected LiveView process; reconnection can mount again. Async tasks start only when connected. Same-name async calls ignore older results; cancellation explicitly kills the underlying task, and linked descendants can still affect LiveView failure behavior. [LiveView lifecycle and async](https://phoenix-live-view.hexdocs.pm/Phoenix.LiveView.html#start_async/4); [cancel_async](https://phoenix-live-view.hexdocs.pm/Phoenix.LiveView.html#cancel_async/3).

**[Proposal]** Avoid charging for model calls in both mount phases. Use an explicit connected/event policy and request identity; decide which operations survive navigation. Authenticate and validate each command boundary, including reconnects and stale events. Killing a task does not by itself prove provider/native work stopped; see [runtime cancellation](beam-runtime-and-interop.md).

## Forms and events remain untrusted

**[Verified]** `Phoenix.HTML.FormData` adapts data to form structures and exposes input values and HTML5 validations. [FormData](https://phoenix-html.hexdocs.pm/Phoenix.HTML.FormData.html).

**[Proposal]** Reuse that protocol for a small form adapter; it is not a substitute for server decoding. Define missing/empty/null/optional semantics, nominal-ID conversion, nested error paths and validation timing. Keep partial form errors separate from a validated command. Browser attributes and strings cannot confer the BEAML witness required at a public call.

## Smallest useful feasibility corpus

**[Proposal]** Before a broad UI framework, prove one typed command through a real LiveView/HEEx sample. The fixture should include valid/invalid nominal IDs, missing required input, optional/empty values, nested errors, and a dynamic unsupported event. Confirm invalid input produces no command effect; test loading/error/complete/cancelled and reconnect paths. Add `.heex` plus inline `~H` with heredoc indentation, Unicode and nested slots to verify exact diagnostic/rename spans. Change an imported contract and confirm only valid outputs remain after recompilation. Pin the tested version tuple and record actual results; no such results exist yet.

# BEAM, Elixir, Mix and Phoenix integration evidence

Status: ingested, selected primary documentation and source inspection; **[Verified]** means checked against these sources, not tested in BEAML.

- Publishers: Ericsson / Erlang/OTP, Elixir contributors, Phoenix contributors.
- Accessed: 2026-11-05.
- Versions observed: OTP 29.1.2 / ERTS 17.1.1; Elixir 1.20.5; Mix compiler behaviour 1.20.5, compile task 1.20.4; LiveView 1.2.13; Phoenix.HTML 4.3.0. These are evidence versions, not chosen BEAML dependencies.
- Raw evidence and exact URL inventory: [research capture](../../raw/research/beam-phoenix/capture-2026-11-05.md).
- Code pin: Phoenix LiveView `v1.2.13`, [TagEngine parser](https://github.com/phoenixframework/phoenix_live_view/blob/v1.2.13/lib/phoenix_live_view/tag_engine/parser.ex) and surrounding engine/compiler source. Read through GitHub connector.
- Coverage/retention: selected researcher notes; original documentation bodies/code are not redistributed. Upstream source licenses remain upstream; no project-wide license inferred.
- Limits: floating docs had mixed cached versions and versioned documentation URLs were unavailable; tagged Phoenix code confirms its parser assertions. No local runtime execution or compatibility matrix validation.

## Compiled pages

- [BEAM runtime and interop](../concepts/beam-runtime-and-interop.md): ABI, Mix, tasks/cancellation, native and schema boundaries.
- [Phoenix and HEEx integration](../concepts/phoenix-heex-integration.md): supported static subset, parser support, form/event trust and feasibility probes.

Read alongside the [product contract](../concepts/product-contract.md) and [specification gaps](../planning/specification-gaps.md). The supplied spec is authoritative about desired BEAML behavior; these upstream sources constrain feasibility without settling the language grammar or ABI.

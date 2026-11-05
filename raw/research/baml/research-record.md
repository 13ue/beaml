# BAML research record

Retrieved 2026-11-05. Primary-source observations; no implementation or conformance run.

- Repository default is `canary`, pinned to `a5db82f06c1da0dfac28e283a15d19d37a3f2cf2`; manifest records downloaded-file hashes. The branch README now describes a general agent language. Established docs still center structured-output functions and generated host SDKs. Treat these as separate evidence tracks.
- GitHub latest-release API returned `baml-language-0.23.1-nightly.20261104.a`, target `c83cef10dd18741b47c5a3fb5d2334d076ff6e17`, published `2026-11-05T09:07:44Z`, `prerelease=false`. Do not infer stable semantics from this flag/name combination.
- `baml_language/ARCHITECTURE.md`: compiler2 uses lossless CST, desugared AST, HIR/TIR semantic queries, MIR control flow, BexVM bytecode. Salsa query granularity and span separation are documented explicitly.
- `baml_language/TYPE_SYSTEM.md`: nominal concrete identities, transparent aliases, runtime type membership, invariant collections, typed/inferred errors, trait-like interfaces. The document itself is semantics guidance, not a published compatibility guarantee.
- `engine/baml-lib/jsonish/README.md`: parser receives output-format metadata, target type, raw text, and `allow_partials`; returns values with flags. Repairs/coercions are part of the behavior.
- `baml_language/FUNCTION_SPEC_STREAMING_DESIGN.md`: implemented-design note discusses rooted nominal runtime values across FFI, exact companion identities, stream cancellation and lifetime. Its status text is an upstream claim, not independently reproduced here.

## Official documentation read

All URLs below were read as HTML on 2026-11-05. They are mutable, unversioned documentation; numeric versions in examples do not establish a release baseline.

- https://docs.boundaryml.com/llms.txt — official documentation inventory.
- https://docs.boundaryml.com/ref/baml/types — primitive/composite types, aliases, ordered parsing unions, unsupported types.
- https://docs.boundaryml.com/ref/baml/function — explicit signature, client, prompt, Jinja and role helpers.
- https://docs.boundaryml.com/ref/baml/template-string — reusable prompt fragments, known linter analysis limit.
- https://docs.boundaryml.com/ref/prompt-syntax/ctx-output-format — schema-to-prompt rendering distinct from JSON Schema serialization.
- https://docs.boundaryml.com/guide/baml-basics/streaming — partial/final types, number completion, done/not_null/with_state.
- https://docs.boundaryml.com/guide/baml-advanced/checks-and-asserts — hard assertions versus returned check outcomes; container filtering caveat.
- https://docs.boundaryml.com/ref/baml/client-llm — provider options and composed clients.
- https://docs.boundaryml.com/ref/llm-client-strategies/retry-policy — additional retries, delays, network failures.
- https://docs.boundaryml.com/ref/llm-client-strategies/fallback — ordered/nested fallbacks and whole-chain retry.
- https://docs.boundaryml.com/guide/baml-advanced/llm-client-registry — per-call runtime provider/model overrides.
- https://docs.boundaryml.com/ref/baml/test — test declarations, arguments, checks and dynamic type builders.
- https://docs.boundaryml.com/ref/baml/generator — multiple targets and output/runtime version configuration.
- https://docs.boundaryml.com/guide/development/upgrade-baml-versions — align generator, SDK, and extension.
- https://docs.boundaryml.com/guide/installation-language/elixir — explicitly unstable community integration.
- https://docs.boundaryml.com/guide/introduction/what-is-baml — DSL → generated client → host function workflow.

## Unresolved investigations

No exhaustive provider/retry error taxonomy audit; no complete canary grammar; no test execution; no claim that a canary feature exists in an established SDK release. Full upstream source/doc copies are omitted; hashes and links permit targeted re-fetching. Future adoption needs an explicit release/commit baseline and legal review of copied components plus dependencies.

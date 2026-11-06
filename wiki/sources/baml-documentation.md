---
id: source-baml-documentation
title: "BAML: established documentation track"
kind: source
status: researched
updated: 2026-11-06
---

# BAML: established documentation track

Status: researched source summary, not BEAML specification. Retrieved 2026-11-05. These official pages are mutable and not pinned to a single package release. See [raw record](../../raw/research/baml/research-record.md) and [provenance](../../raw/research/baml/provenance.json).

**[Verified]** Source observations below were checked directly, not tested in BEAML. Publisher: BoundaryML. Upstream source/code remains subject to its own license; these are attributed research summaries.

## Source findings

The documented development flow is typed `.baml` functions, generated `baml_client`, and calls from a host language. Code generation bundles the integration needed for requests, parsing and errors; it is not evidence that BAML source itself compiles to BEAM. [Developer flow](https://docs.boundaryml.com/guide/introduction/what-is-baml)

A function declares typed arguments and a return type, chooses a client, and carries a raw block-string prompt. The prompt uses Jinja substitutions/conditionals/loops. `ctx.output_format` renders return-type instructions and `_.role` segments messages. Reusable `template_string` declarations can nest, although the documented linter has static-analysis limitations. [Functions](https://docs.boundaryml.com/ref/baml/function), [templates](https://docs.boundaryml.com/ref/baml/template-string)

The type reference covers primitives, classes/enums, nullable types, ordered union parsing, arrays/maps, literal types and recursive aliases through containers. It distinguishes class-field syntax from argument syntax. Its limitations and examples belong to this documentation track; do not apply them automatically to compiler2. [Types](https://docs.boundaryml.com/ref/baml/types)

Client declarations select provider-specific request options; shorthand selects a provider/model. `openai-generic` supports compatible endpoints, while dedicated adapters cover several APIs. Runtime registries can replace named clients or select a primary per call. This makes the actual data destination a runtime concern. [Clients](https://docs.boundaryml.com/ref/baml/client-llm), [registry](https://docs.boundaryml.com/guide/baml-advanced/llm-client-registry)

Retries are described for network errors: `max_retries` counts additional attempts. Constant delay and exponential backoff are documented. Fallback tries an ordered nonempty client list; a retry on the fallback retries the entire failed chain. These pages do not establish an exhaustive policy for validation failures or streamed retries. [Retry](https://docs.boundaryml.com/ref/llm-client-strategies/retry-policy), [fallback](https://docs.boundaryml.com/ref/llm-client-strategies/fallback)

Tests are language declarations containing function targets, argument fixtures and optional checks/assertions/type-builder configuration. Generators may target multiple host languages. Generator/runtime/extension versions should align; example version strings are not a claim about the latest release. [Tests](https://docs.boundaryml.com/ref/baml/test), [generators](https://docs.boundaryml.com/ref/baml/generator), [upgrades](https://docs.boundaryml.com/guide/development/upgrade-baml-versions)

The official Elixir integration page explicitly calls its support unstable and community provided. It does not establish a supported BEAM compiler backend. [Elixir](https://docs.boundaryml.com/guide/installation-language/elixir)

## BEAML relevance

### Product-benefit follow-up

**[Verified]** On 2026-11-05, the official [Collector reference](https://docs.boundaryml.com/guide/baml-advanced/collector-track-tokens) documents call identity, timing, usage and constituent model attempts.
The newer [error chapter](https://developer.boundaryml.com/baml/book/errors) documents inferred error propagation and exhaustive handlers.
These are separate documentation tracks, not a tested combined package version.
The [selected follow-up capture](../../raw/requirements/2026-11-05-product-benefit-followup.md) records coverage and limits.
No full deterministic replay or flawless execution guarantee was established.

### Debugging and replay of a recorded call (2026-11-06)

**[Verified]** Accessed 2026-11-06. Each page below now says it documents BAML v0, the legacy DSL; BAML v1 is a separate language. [Capture](../../raw/research/baml/debugging-replay-2026-11-06.md)

- **[Verified]** The [Collector reference](https://docs.boundaryml.com/guide/baml-advanced/collector-track-tokens) records per function log `id`, `function_name`, `timing`, `usage`, `calls`, `raw_llm_response` and `tags`. Each call keeps its raw `http_request` and `http_response`; the response is null for streaming.
- **[Verified]** The [modular API](https://docs.boundaryml.com/guide/baml-advanced/modular-api) parses a reply string with `b.parse.<Fn>` and `b.parse_stream.<Fn>`. The caller extracts the message text from the provider envelope first. The batch example parses saved output.
- **[Verified]** [Boundary Studio](https://docs.boundaryml.com/guide/boundary-cloud/observability/tracking-usage) shows traced inputs, outputs and tags. The page documents no re-run, replay or "open in playground".
- **[Verified]** [Test blocks](https://docs.boundaryml.com/ref/baml/test) and [`baml-cli test`](https://docs.boundaryml.com/ref/baml-cli/test) document no mocked or recorded model response. The CLI examples set provider API keys.
- **[Unknown]** Whether a test block calls the live provider is not stated on these pages. **[Inference]** The API-key examples suggest live calls.

**[Verified]** The v1 code track adds `baml query` and `F@parse`. See [BAML internals](baml-internals.md#recorded-calls-and-offline-parse-2026-11-06).

**[Inference]** These mechanisms support a product hypothesis: keep application functions small while shared tools retain structured failure evidence.
Whether this is BoundaryML's largest benefit is a product judgment, not established by these references.
The [comparison proposal](../planning/product-benefit-probe.md) tests a narrow BEAML version of that hypothesis.

**[Inference]** The following implications are research conclusions, not adopted semantics.

Adopt the product concepts selectively: typed prompt contracts, previewable prompts, reusable templates, provider configuration and first-class fixtures. A TypeScript-looking BEAML can preserve these ideas while choosing different syntax and execution semantics. Compatibility would require fixture-based agreement on prompt rendering, parse/coercion rules, union ambiguity, errors, retries and stream lifecycle; matching signatures alone is insufficient.

See [language/tooling synthesis](../concepts/baml-language-and-tooling.md) and [structured output/streaming](../concepts/structured-output-and-streaming.md).

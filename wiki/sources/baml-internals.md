---
id: source-baml-internals
title: BAML compiler and runtime source trace
kind: source
status: inspected-not-executed
updated: 2026-11-06
---

# BAML compiler and runtime source trace

**[Verified]** Publisher: BoundaryML. Commit `a5db82f06c1da0dfac28e283a15d19d37a3f2cf2`, retrieved 2026-11-05. Selected source/fixture assertions inspected, not run. [Raw corrections/observations](../../raw/research/baml-internals/record-2026-11-05.md), [file hashes/URLs](../../raw/research/baml-internals/provenance-2026-11-05.json). No implementation copied; [reuse boundary](baml-license.md).

## Exact paths and mechanisms

Paths below are under `baml_language/crates/` at the pin.

| Source / symbol | Checked mechanism |
|---|---|
| [parser/lib.rs](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler_parser/src/lib.rs), `parse_result`, `syntax_tree` | Salsa parse result, green tree and errors |
| [ast/companions.rs](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_ast/src/companions.rs), `expand_companions` | Synthesized @spec/render_prompt/build_request/parse/stream functions |
| [hir/item_data.rs](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_hir/src/item_data.rs), [functions.rs](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_hir/src/item_data/functions.rs) | Equality-checked span-free semantic firewall, separate source maps |
| [hir_ty/infer.rs](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_hir_ty/src/infer.rs), `infer_body`, `infer_function_body` | Bidirectional per-owner inference/member resolution/throws cycles |
| [hir_ty/llm_output.rs](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_hir_ty/src/llm_output.rs) | JSON-inhabitance warnings; generic/unknown output checks deferred to runtime |
| [db/check.rs](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_db/src/check.rs), [program.rs](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_db/src/program.rs), `CheckedWorld::check` | Error-gated revision before emit/link; span-less errors count |
| [mir/lower.rs](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_mir/src/lower.rs), `lower_function` | Typed runtime lowering and indirect-call-layout checks |
| [mir/optimize.rs](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_mir/src/optimize.rs), `optimize_body` | CFG/copy/dead-store/local cleanup; O2 constants, operand materialization, RPO |
| [emit/lib.rs](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_emit/src/lib.rs), [verifier.rs](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_emit/src/verifier.rs) | Stackification/runtime templates/debug-test invariants |
| [bex_project/lib.rs](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/bex_project/src/lib.rs), [bex_engine/lib.rs](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/bex_engine/src/lib.rs) | Compile/runtime seam, VM/I/O loop, active heap permit GC |
| [VM future.rs](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/bex_vm/src/package_baml/future.rs) | Heap future state/cancel CAS settling; not OTP supervision |
| [ai/spec.baml](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_builtins2/baml_std/ai/spec.baml) | FunctionSpec<Out>, reflection, parsing, request preview and agent call |
| [sap.baml](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_builtins2/baml_std/baml/ns_sap/sap.baml), [VM sap.rs](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/bex_vm/src/package_baml/sap.rs) | Realized-type parse cache, shaped conversion/refusal, typed heap landing |
| [sap_model/mod.rs](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/bex_sap/src/sap_model/mod.rs), [coerce_union.rs](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/bex_sap/src/deserializer/coercer/coerce_union.rs) | Partial/final defaults; candidate scoring/order/hints |
| [ai stream.baml](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_builtins2/baml_std/ai/ns_stream/stream.baml) | Shared-T partial/final, accumulated text, cached terminal outcome and cleanup |
| [test_streaming.rs](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/bex_sap/src/tests/test_streaming.rs), [stream fixture](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_tests/baml_src/ns_streaming_partial_parse/streaming_partial_parse.baml) | Missing/default/final/error/cleanup assertions, not observed passes |

## Recorded calls and offline parse (2026-11-06)

**[Verified]** Read 2026-11-06, not run. Default branch `canary` at `6a3eb3dfb2908bac750ad0e4cd9d6a086a72f211`. The first three files have the same blob at the pin. [Capture with hashes](../../raw/research/baml/debugging-replay-2026-11-06.md)

| Source at the pin | Checked content |
|---|---|
| [skills/baml-core/SKILL.md](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/skills/baml-core/SKILL.md), "Debugging a recorded call" | `baml query` finds a failed span, its type arguments and the child network span's raw HTTP response. A test then calls `F@parse` on the reply text, with no model call. Replay or caching is user code that implements `ai.Runner`, or a fake `ai.Client` |
| [baml_query_btel/src/catalog.rs](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_query_btel/src/catalog.rs), relations `spans`, `processes` | Span ids, parent, times, `type_args`, `input_args`, `output_value`, `error_value`, usage. Network span request and `network_event_values` (status, headers, body or SSE events; body null when not recorded). CAS id of the BAML sources that ran |
| [btel_bcs/README.md](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/btel_bcs/README.md) | `BAML_TELEMETRY` levels; default `medium` gives auto LLM functions spans with default captures. Local recording without cloud credentials |
| [baml_query_btel/tests/network.rs](https://github.com/BoundaryML/baml/blob/6a3eb3dfb2908bac750ad0e4cd9d6a086a72f211/baml_language/crates/baml_query_btel/tests/network.rs) (canary) | Fixture stores the response body as a JSON string |

**[Verified]** Default-branch code search found no `cassette`, `ReplayHttp` or `record_replay`. Other "replay" hits are telemetry re-delivery, REPL source and UI. Pull request [#3336](https://github.com/BoundaryML/baml/pull/3336) proposes playground HTTP record and pinned replay. It is open and not merged; only its description was read.

**[Inference]** BAML v1 records enough to re-parse a failed call offline. It has no built-in REPLAY RUN with identity checks or a live-call count. **[Unknown]** Exact wire-byte fidelity of the stored body and the default body-recording policy.

**[Verified]** Update 2026-11-06: at the newer pin `989676dd5169497c0d2a8d8e1d10914e987ae262`, network spans record bodies by default, with an 8 MiB truncation limit. Wire-byte fidelity is still **[Unknown]**. [BAML v1 source page](baml-v1.md#observability)

## Correction scope

The earlier [architecture-prose note](baml-canary-compiler.md) is now qualified: conceptual TIR corresponds to actual `hir_ty`; the concrete query is per-body inference. Engine README epoch-GC prose lags permit-based source. Established SDK docs' nullable partial types/Jinja syntax differ from canary shared T/backtick/colon syntax. Neither track should be applied silently to the other. [Correction record](../../raw/research/baml-internals/record-2026-11-05.md)

**[Unknown]** No full grammar/SDK/provider/FFI/memory audit. **[Inference]** Shared-T streaming ensures a runtime-representable type while readiness remains separate; it does not establish BEAML validation/refinement typestates. See [walkthrough](../concepts/compilers/baml.md).

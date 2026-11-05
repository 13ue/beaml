---
id: concept-compiler-verification
title: Compiler verification, fuzzing and release evidence
kind: synthesis
status: proposed-not-executed
updated: 2026-11-05
---

# Compiler verification, fuzzing and release evidence

**[Requirement]** The PDF requires compile-fail, MIR golden, differential, fuzz/property, LSP stale-edit and runtime-provider/security tests; no unresolved P0/P1 defects and no unapproved over-budget regression at release. It proposes M1 1M parser inputs and later 10M hardening/adapter gates, not completed runs. [Spec pp.3,5–7 §§4,11–14; pp.10,14 §§29,44](../../sources/engineering-spec-v0.5.md)

**[Proposal]** The following evidence design covers those obligations without declaring tests equivalent to formal proofs. [Primary-source evidence/versions](../../sources/compiler-verification.md). No compiler, fuzz corpus or benchmark was run here.

## Choose an oracle for each claim

| Claim | Small independent oracle | What it cannot establish |
|---|---|---|
| Lossless/recovering parser | Input equals concatenated tokens/trivia; bounded arbitrary bytes/text never crash; malformed fixtures give scoped diagnostics | Accepted syntax has the intended language semantics |
| Formatter | Idempotence plus semantic/tree-equivalence under canonical grammar; comment/trivia placement fixtures | Readability or correct preservation of unsupported syntax |
| Typing/effects | Normative positive/negative judgments, expected error code/span, substitution/instantiation laws | Full soundness of unspecific rules or foreign code |
| MIR well formed | Structural/type/effect/label invariants checked after each relevant pass | All observable behavior is preserved |
| Optimization | Normative evaluator/O0 vs optimized output including result/error/effect order/cancellation/sinks | Correctness where both paths share the same bug or input has undefined/unspecified behavior |
| Incrementality | Incremental result equals fresh DB after edit sequence; query counts separately measure locality | Every source/policy input was included without adversarial edits |
| Runtime boundary | Invalid/forged inputs rejected before command effects; ABI roundtrip/version mismatch fixtures | Arbitrary trusted VM/foreign code cannot forge/misbehave |
| Streams | Same recorded response under different chunk partitions; final/error/readiness/revision contract | Live model truthfulness or provider determinism |
| IFC | Formal flow rule plus direct/implicit/error-path negatives and sink canaries | A sampled canary search is a no-leak proof |

**[Verified]** Rust's phase-aware MIR validator checks structure/types/debug records. BAML's emitter verifier checks dense IDs, redirect termination and unreachable defaults for exhaustive switches; its debug/test configuration matters. Both exemplify executable invariants rather than full semantic verification. [Rust validator](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_mir_transform/src/validate.rs), [BAML verifier](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_emit/src/verifier.rs)

## Specify IR invariants before snapshotting

**[Proposal]** For BEAML's supported core, invariants should name: each referenced local/block/symbol exists; terminators/edges satisfy the current phase; every expression/call has a resolved type/layout; error/cancellation/unwind paths retain obligations; validation evidence dominates its use; effect sets/capabilities and labels survive lowering; every permitted declassification is explicit; and source origins remain attributable. Exact dominance/control-flow rules require the chosen semantics, not a generic checklist.

Run a cheap invariant checker after construction and transformations in development/CI. Include deliberate malformed-IR unit fixtures to prove the verifier detects violations. Refuse internal inconsistency instead of substituting a runnable default body. BAML's CheckedWorld revision gate and checked indirect-call-layout errors are relevant precedents. [Admission/lowering](../compilers/baml.md#4-a-checked-revision-reaches-mir-and-bytecode)

## Goldens need review, differential tests need independent paths

**[Verified]** Rust UI tests compare normalized stdout/stderr, and maintainers review generated expected output when blessing snapshots. MIR-opt tests can isolate a pass and compare before/after dumps or FileCheck patterns, with bit-width distinctions. [UI guide](https://github.com/rust-lang/rustc-dev-guide/blob/a29f8285990b8254783202aa0d86322eb21edf61/src/tests/ui.md), [MIR-opt contract](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/tests/mir-opt/README.md)

**[Proposal]** Version goldens for syntax recovery, inferred types, diagnostics, MIR, descriptors/manifests and generated source. Normalize only unstable paths/timestamps/IDs whose meaning is separately checked. Do not normalize away error locations, branch order, sink decisions or statuses merely to make snapshots pass. A snapshot update is a changed expected behavior requiring explanation.

For semantic differential tests, define the observable trace: return/error outcome, externally visible effect sequence, validation result, cancellation/cleanup and policy decisions. Generate well-typed small programs under explicit fuel/size bounds; compare a simple normative evaluator with backend results or compare O0/O2 plus another independent oracle. Skip/UNKNOWN unsupported semantics explicitly. Live HTTP/LLM effects should be fixtures or controlled adapters; do not infer determinism from a recorded seed alone.

Metamorphic cases can vary whitespace/alpha-renaming/parentheses, chunk partitions or equivalent pure expressions only where the language law permits it. Do not commute effectful operations, reorder parsing unions or erase validation labels. Assert the transformation's preconditions before using its relation as an oracle.

## Fuzzing is a corpus process, not a large integer

**[Verified]** libFuzzer uses coverage-guided in-process mutation and corpus retention, with deterministic repeated-call target expectations and saved crash/timeout inputs. It can replay saved files and merge a coverage-preserving corpus. [LLVM documentation](https://llvm.org/docs/LibFuzzer.html)

**[Proposal]** Separate targets for lexer/CST/recovery, prompt interpolation, schema/SAP, generated ABI decoders, label algebra and HEEx adapter. Bound bytes/nesting/fuel/memory/time and disallow network/secret access. Seed valid and invalid Unicode, delimiters, truncated multimodal data, recursive schemas, union ambiguity and prior failures. Memory sanitizers apply to applicable native builds; semantic assertions extend beyond crash detection.

Store exact target/build/options/corpus hash and tested iterations, not only elapsed time. Minimize failures, add a human-readable regression and keep the original triggering artifact. Report crash/hang/OOM/timeout categories, coverage and skipped corpus cases separately. A stage's 1M or 10M count must identify which inputs/targets ran; zero observed crashes means TESTED on that corpus, not mathematically safe. [Spec stage gates](../../sources/engineering-spec-v0.5.md#delivery-and-exit-criteria)

## Reproducibility is wider than a random seed

**[Proposal]** A failure bundle contains compiler/language/checker/generator/runtime revisions, features/target/optimization, source and dependency/interface/ABI/policy fingerprints, property/corpus identity, RNG algorithm/seed, size/fuel/reject/shrink budgets, original/minimized input or trace, fixture/provider response version, normalized diagnostics and actual command/environment. Sensitive payloads remain subject to policy; a public seed must not be a disguised secret fixture identifier.

For concurrency, record an explicitly controlled scheduler trace only if the harness controls it. A sequential command seed cannot reproduce arbitrary BEAM message scheduling. Preserve deterministic provider replay separately from scheduler replay. [Stateful testing](generators-and-stateful-properties.md), [spec replay boundary](../observability-and-replay.md)

## Benchmark statistics and the release gate

**[Requirement]** Baseline specifies pinned Linux x86-64, 8 dedicated vCPUs/32 GiB/NVMe, warm filesystem cache, at least 30 iterations, p50/p95/max/confidence interval, with network/model latency excluded. UI extension uses a different machine/percentile protocol including p99. Preserve both until a shared protocol is chosen. Cache-hit >=95% applies only to the named controlled edit fixture; property throughput separates scalar/refined/stateful cases. [Exact target tables](../../sources/engineering-spec-v0.5.md#exact-acceptance-targets-and-reproducibility-contracts)

**[Verified]** NIST distinguishes a mean's uncertainty interval from an individual observation and explains bootstrap estimation/cautions for other statistics. A t interval for a mean does not describe p95/p99 uncertainty. [Mean interval](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm), [bootstrap](https://www.itl.nist.gov/div898/handbook/eda/section3/eda334.htm)

**[Proposal]** Define independent sampling units, warmup/exclusion rules, clock and CPU/power/parallel-load controls, full-vs-incremental cache state and confidence level/method before measuring. Retain all raw samples with fixtures/toolchain/hardware/OS identity; avoid silently discarding slow runs. Compare like-for-like baseline/candidate builds in randomized or paired order where appropriate. Report absolute latency and regression ratio with uncertainty; unresolved/noisy cases rerun or remain inconclusive under explicit release policy.

**[Inference]** Thirty runs is a minimum protocol requirement, not enough evidence for a precise p99: under an independent sample model the expected number beyond the population p99 is only 30×0.01=0.3. Resampling cannot invent unobserved tail behavior. Specify more measurements or a scoped tail-estimation method before enforcing a confident p99 claim. Do not use mean intervals to make percentile gates look satisfied.

**[Proposal]** Release evidence should list every mandatory suite, exact fixture and target, status, counterexample/regression, budget result and approved exception. Missing/skipped/exhausted/unsupported are explicit outcomes. A signed performance waiver changes release disposition, not the measured statistic or proof status. Defect severity P0/P1 and feature rollout P0/P1 must have different fields. No new numeric gate is adopted on this page.

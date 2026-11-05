---
id: source-compiler-verification
title: Compiler verification and generated testing evidence
kind: source
status: inspected-not-executed
updated: 2026-11-05
---

# Compiler verification and generated testing evidence

**[Verified]** Retrieved 2026-11-05. Publishers: Rust Project, BoundaryML, Proptest developers, LLVM Project and NIST/SEMATECH. [Raw observations](../../raw/research/compiler-verification/record-2026-11-05.md), [versions/hashes/coverage](../../raw/research/compiler-verification/provenance-2026-11-05.json). No upstream or BEAML tests were run; upstream copyright/license terms remain separate.

## Source evidence

| Source | Mechanism checked / limit |
|---|---|
| [rustc validate.rs](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_mir_transform/src/validate.rs) | Phase-aware MIR CFG/type/debuginfo checks; not full semantic equivalence |
| [Rust MIR-opt README](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/tests/mir-opt/README.md) | Per-pass dumps/diffs, FileCheck and bit-width-specific artifacts |
| [Pinned UI test guide](https://github.com/rust-lang/rustc-dev-guide/blob/a29f8285990b8254783202aa0d86322eb21edf61/src/tests/ui.md), [compiletest](https://github.com/rust-lang/rustc-dev-guide/blob/a29f8285990b8254783202aa0d86322eb21edf61/src/tests/compiletest.md) | Diagnostic snapshots, expected compile/run outcomes, revisions and test suites |
| [BAML optimizer](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_mir/src/optimize.rs), [emitter verifier](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_emit/src/verifier.rs) | Debug/test invariants and optimization paths |
| [BAML type harness](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_tests/src/type_spec/harness.rs) | Type annotation/diagnostic/snapshot inspection; no observed test pass |
| [Strategy tutorial](https://github.com/proptest-rs/proptest/blob/70cf37d46b7d83393b6ed94c611f8c52209f585d/book/src/proptest/tutorial/strategy-basics.md), [shrinking](https://github.com/proptest-rs/proptest/blob/70cf37d46b7d83393b6ed94c611f8c52209f585d/book/src/proptest/tutorial/shrinking-basics.md) | Strategy/ValueTree generation and domain-preserving simplify/complicate |
| [Filtering](https://github.com/proptest-rs/proptest/blob/70cf37d46b7d83393b6ed94c611f8c52209f585d/book/src/proptest/tutorial/filtering.md), [runner errors](https://github.com/proptest-rs/proptest/blob/70cf37d46b7d83393b6ed94c611f8c52209f585d/proptest/src/test_runner/errors.rs), [config](https://github.com/proptest-rs/proptest/blob/70cf37d46b7d83393b6ed94c611f8c52209f585d/proptest/src/test_runner/config.rs) | Rejection budgets and Abort distinct from counterexample |
| [Sequential strategy](https://github.com/proptest-rs/proptest/blob/70cf37d46b7d83393b6ed94c611f8c52209f585d/proptest-state-machine/src/strategy.rs), [SUT runner](https://github.com/proptest-rs/proptest/blob/70cf37d46b7d83393b6ed94c611f8c52209f585d/proptest-state-machine/src/test_runner.rs) | Preconditions, reference transitions, invariant checks and trace shrinking |
| [Persistence](https://github.com/proptest-rs/proptest/blob/70cf37d46b7d83393b6ed94c611f8c52209f585d/book/src/proptest/failure-persistence.md) | Seed replay can change meaning when strategies change |
| [LLVM libFuzzer](https://llvm.org/docs/LibFuzzer.html) | In-process coverage-guided corpus mutation/replay; bounded deterministic targets; mutable docs |
| [NIST mean confidence limits](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm), [bootstrap](https://www.itl.nist.gov/div898/handbook/eda/section3/eda334.htm) | Uncertainty method/assumptions, mean vs other estimators, bootstrap cautions |

Rust source pin is 1.99.1 (`58cf8f9c35b355199727627d07ae34a4e2846d67`); guide `a29f8285990b8254783202aa0d86322eb21edf61`; BAML `a5db82f06c1da0dfac28e283a15d19d37a3f2cf2`; Proptest `70cf37d46b7d83393b6ed94c611f8c52209f585d`. Official web docs/handbooks are date-scoped, not claimed identical to those source revisions. QuickCheck author manual was inaccessible; no unread paper is used as evidence.

**[Inference]** No one mechanism proves compiler correctness, domain correctness or noninterference. See [compiler verification plan](../concepts/testing/compiler-verification.md) and [generators/stateful properties](../concepts/testing/generators-and-stateful-properties.md).

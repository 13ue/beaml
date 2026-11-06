# EXPERIMENT 0001: syntax to BEAM

**[Requirement]** Implement the [accepted syntax subset](../../wiki/sources/syntax-spike-requirement.md) as a small executable probe.
**[Proposal]** Hypothesis: exact data interfaces and nested function-head patterns can lower to guarded Elixir functions.

Candidate ownership: LANGUAGE/COMPILATION owns the compiler. EXECUTION owns the host boundary and execution checks.
See the [R&D register](../../wiki/planning/research-and-development.md) and [context map](../../wiki/planning/context-map.md).
No separate domain service, database or message broker is needed.

## Run

From the repository root, use installed Rust with rustfmt and Clippy, Cargo, Elixir and OTP:

```sh
python3 experiments/0001-syntax-to-beam/run.py
```

The runner tests the compiler, generates Elixir, compiles a `.beam` file and runs ExUnit against that file.
Each run creates `results/<UTC-run-id>/result.json`, input/output hashes, generated source and per-step stdout/stderr.
Build output and `.beam` files are ignored by Git. Retain text evidence; do not replace old runs.
The result file records exact local toolchain versions. No Cargo dependencies or network access are required.

To generate Elixir only:

```sh
cargo run --offline --quiet --manifest-path experiments/0001-syntax-to-beam/Cargo.toml -- experiments/0001-syntax-to-beam/example.beaml
```

The CLI emits source to stdout only after parsing and checking succeed. Errors go to stderr with a nonzero exit.
Action events append to `.beaml/actions.jsonl` in the current directory. The runner uses the repository root.
Events contain operation, target and result status. They omit source text and input paths. Logging failure does not stop compilation.
The runner also records use-case start, each step and final pass/fail events. These records are not complete replay evidence.

## Supported experimental contract

**[Verified]** The [compiler](src/main.rs), [source example](example.beaml), [CLI test](tests/cli.rs) and [BEAM tests](tests/runtime_test.exs) implement and exercise:

- ASCII identifiers, UTF-8 strings, selected escapes, `//` comments and String concatenation with `+`.
- Exact structural interfaces with named fields. Field order does not determine interface compatibility.
- Concrete enums with globally unique constructor names. Even zero-argument variants use parentheses, such as `Waiting()`.
- Function definitions without outer parameter parentheses. Calls use parentheses and commas.
- Explicit parameter annotations for variable/wildcard heads. Constructors and record patterns determine their input TYPE.
- An explicit return TYPE on every clause. All clauses of a function share the same declared signature and arity.
- Nested literal, constructor and record patterns. Record patterns may omit fields without `..`; `_` ignores one value.
- First matching clause, duplicate-binding rejection, bounded pattern-coverage checks and unreachable-clause errors.
- Exact construction, function/constructor arity, reference and return-TYPE checks before generation.

A constructor pattern such as `Ok(Order { customer: Customer { name } })` selects fields without weakening input validation.
The host boundary requires all declared fields, rejects extra fields and checks nested variants and UTF-8 strings.
The declaration syntax is an open R&D choice. [D001: `enum` or `type`](../../wiki/planning/decisions-to-be-made.md#d001--enum-or-type-declarations)

## Experimental host representation

**[Verified]** Records lower to maps with string keys, without nominal record tags.
Enums lower to `{enum_name, constructor_name, [arguments]}`, with string names. No input string becomes an atom.
Generated public functions validate arguments and results. Matching clauses are private.
Invalid host input raises `ArgumentError` with a fixed message. Typed error-return APIs are deferred.
Source strings lower to byte literals to prevent Elixir interpolation or code injection.
This format is not a stable GENERATED ABI. Shape validation does not establish authorization, provenance or factual truth.

## Acceptance criteria

1. The example compiles and `sample()` returns `Kunde bestellt aus Berlin, Deutschland` on the BEAM.
2. Nested literal and general patterns select the expected clauses. Both error variants return their expected text.
3. Missing/extra construction fields, invalid calls, wrong TYPEs and unknown names fail compilation without generated stdout.
4. Missing match cases and unreachable clauses fail for the supported finite TYPEs and String-literal partitions.
5. Missing/extra host fields, invalid nested values and unknown enum representations fail before private dispatch.
6. Source interpolation remains data. The generated module compiles with warnings treated as errors.

## Evidence and limits

**[Verified]** The [accepted run](results/20261105T202319485083Z/result.json) passes all pipeline steps: nine compiler unit tests, one CLI integration test and eight BEAM tests. The coverage unit test checks all sixteen subsets of a four-value truth table.
Retained result directories also include an early generator failure. Hashes bind each result to the tested inputs.

**[Unknown]** No generic enums, recursive TYPEs, numeric TYPEs, methods, overloads, modules, effects, LSP, provider calls or streaming are supported.
No MIR, stable source maps, broad inference, hostile-input hardening, security proof or performance result is claimed.
Input, nesting, TYPE depth and coverage work have explicit limits. Exceeding a supported limit returns a compiler error.
The generated boundary does not implement schema evolution, cancellation, full typed replay or a trusted nominal-value protocol.
This experiment is smaller than the historical [build-readiness slice](../../wiki/planning/build-readiness.md). It completes neither M0 nor M3.

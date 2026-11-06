---
id: source-baml-v1
title: "BAML v1: language, runtime and release status"
kind: source
status: inspected-not-executed
updated: 2026-11-06
---

# BAML v1: language, runtime and release status

Status: selected research captures, read and not run. Upstream capability is not BEAML capability. No BAML package was installed or run, and no test was executed.

## Origin, coverage and limits

**[Verified]** Publisher: BoundaryML. Repository: https://github.com/BoundaryML/baml, default branch `canary`. Access date: 2026-11-06.

| Capture | Content | Coverage |
|---|---|---|
| [Release status](../../raw/research/baml/v1-status-2026-11-06.md) | GitHub releases and tags, PyPI and npm, docs sites, homepage, pricing, blog, talk listings | Paraphrases, short fragments, API values. Web pages read through a summarizing fetch tool |
| [Language and repository](../../raw/research/baml/v1-language-repo-2026-11-06.md) | Language surface, standard library, runtime, hosts, tooling, observability, maturity | Code read at the pin, not built. Pull requests: descriptions only, not diffs |

**[Verified]** Source pin: `989676dd5169497c0d2a8d8e1d10914e987ae262`, committer date 2026-11-06T07:51:53Z. Permalinks below use this pin. At the pin: 11,462 tracked files, 77 crates under `baml_language/crates/` (about 693,000 lines of Rust) and about 37,900 lines of BAML in the standard library.

**[Verified]** The capture does not repeat the compiler pipeline, schema-aligned parsing, streaming and `baml query` schema. These are in [BAML internals](baml-internals.md) at the earlier pin `a5db82f06c1da0dfac28e283a15d19d37a3f2cf2`.

**[Unknown]** Star trend, version use of named customers, the content of the talk that the owner attended, and the date of the Linux Foundation keynote.

## Licence and attribution

**[Verified]** The GitHub API reports SPDX `Apache-2.0`. The workspace [Cargo.toml](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/Cargo.toml) sets `license = "Apache-2.0"`. The pricing page says BAML is free and open source, and the local toolchain needs no Boundary server.

**[Unknown]** Vendored and forked crates (`forks/`, `vendor/`) can have other terms; not audited. No upstream code is copied into BEAML. This page contains attributed summaries and short identifiers only. See the [reuse boundary](baml-license.md).

## Versions and release lines

**[Verified]** BAML has two separate release lines. ([Status capture §1](../../raw/research/baml/v1-status-2026-11-06.md#1-release-status))

| Line | Tags | Latest observed | Packages |
|---|---|---|---|
| BAML v1 ("BAML Language") | `baml-language-<x.y.z>` | `0.25.1`, 2026-11-06T05:24Z; `0.25.0` and `0.24.0` one day earlier | PyPI `baml-bridge` 0.25.1, npm `@boundaryml/baml-bridge` 0.25.1 |
| BAML v0 ("legacy DSL") | `0.226.x` / `v0.226.x` | `0.226.3` (GitHub release 2026-10-28; root CHANGELOG 2026-10-27) | PyPI `baml-py` 0.226.3, npm `@boundaryml/baml` |

**[Verified]** In the code, the stamped product version is `0.25.1`, channel `canary` ([baml_version/src/lib.rs#L3-L5](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_version/src/lib.rs#L3-L5)). The Rust workspace version is `0.0.0-beta` ([Cargo.toml#L67](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/Cargo.toml#L67)). The `baml` wrapper (toolchain version manager) is `0.3.1`.

**[Verified]** No tag or release named `1.0` or `v1.*` exists. All v1 releases have `prerelease: false`. Near-daily `0.23.1-nightly.*` builds exist. [RELEASING.md](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/RELEASING.md) gives a nightly build from the newest green `canary` commit and a weekly canary release.

**[Verified]** "v1" is a product name, not a version number. The v1 line uses 0.x numbers. The v0 line uses higher 0.226.x numbers. Do not compare the two lines by version number.

**[Verified]** The v0 docs now say that they document "BAML v0, the legacy DSL". They call v1 a separate language in public beta. The v1 docs are on developer.boundaryml.com; the CLI reference there is indexed at v0.23.0. A blog post of 2026-11-05 says the team prepares a 1.0 release and calls the core language design nearly complete.

**[Verified]** Status words conflict. v0 docs: "public beta". Homepage, explore page and the 2026-11-05 blog: "private beta" with a founder call for access. Quickstart: "early access" for the cloud platform.

**[Inference]** v1 is a public, installable 0.x toolchain in beta, with 1.0 announced as in preparation. "Private beta" probably applies to the full stack with Boundary Cloud; the sources do not say this.

**[Unknown — owner-reported]** The repository owner attended a talk by the BoundaryML founder on 2026-11-05. The owner reports that v1 is very far along and maybe finished. No public listing, abstract or recording of this talk was found. **[Inference]** The captures support "very far along". They do not support "finished": no 1.0 tag exists and the code says beta.

## What v1 is

**[Verified]** GitHub description: "The programming language for agents". Homepage: "The hyper-observable programming language". v1 runs standalone or is called from host languages. ([Status capture §3](../../raw/research/baml/v1-status-2026-11-06.md#3-positioning-users-licence))

**[Inference]** v1 is a general-purpose language with a general-purpose standard library. BoundaryML positions it for agent software. LLM functions are one feature among many, not the whole language. This differs from v0, which is a schema and prompt DSL with generated host clients.

### Language surface

All rows **[Verified]**. Main source: [skills/baml-core/SKILL.md#L44-L75](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/skills/baml-core/SKILL.md#L44-L75), with [TYPE_SYSTEM.md](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/TYPE_SYSTEM.md).

| Area | Observation |
|---|---|
| Types | Classes (reference types, mutable fields, methods, no inheritance). `interface` with default methods, associated types and dynamic dispatch. Operators are interfaces. Data-free enums; data variants as unions of classes. Literal unions, `T?`, `map<K,V>`, `never`, `unknown`, `bigint` |
| Generics and runtime types | Generics, variance rules, equirecursive aliases, `let type T = e;`. Types persist at runtime with full reflection (`reflect.Type.of<T>()`) |
| Control flow | Expression blocks, `if` as expression, `for`, `while`, `while let`, closures, top-level `const` evaluated once at startup |
| Pattern matching | `match` with exhaustiveness, guards, destructuring, `is`, `if let`. Narrowing applies to locals only, not field paths |
| Errors | Errors are class values. `-> T throws E`, implicit propagation, `catch` for named types, exhaustive `catch_all`, cause chain in `catch (e, ctx)` ([SKILL.md#L77-L82](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/skills/baml-core/SKILL.md#L77-L82)). Separate panic family ([panics.baml](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_builtins2/baml_std/baml/ns_panics/panics.baml)) |
| Concurrency | `spawn { }` returns `Future<T, E>`; `await`; `all`, `race`, `with_timeout`. Modifiers `Limit`, `CancelToken`, `Root`. `defer` and `cleanup(self)` ([spawn.baml#L4-L23](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_builtins2/baml_std/baml/ns_spawn/spawn.baml#L4-L23), [future.baml#L94-L136](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_builtins2/baml_std/baml/ns_future/future.baml#L94-L136)) |
| LLM functions | A DSL that desugars into ordinary code. `F(args)` runs `F@spec(args)` through `ai.Agent`. Clients are values; the old `client<llm>` block is removed ([SKILL.md#L89-L115](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/skills/baml-core/SKILL.md#L89-L115)) |
| Modules and packages | Namespaces from `ns_<name>/` directories; no `import`. Packages use `baml.toml` with path dependencies only; no registry ([manifest.rs#L128-L138](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_db/src/manifest.rs#L128-L138)) |

### Standard library

**[Verified]** [`baml_std`](https://github.com/BoundaryML/baml/tree/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_builtins2/baml_std) has 14 prelude packages: `ai`, `anthropic`, `assert`, `aws`, `baml`, `claude_code`, `google`, `log`, `openai`, `reflect`, `testing`, `trace`, `typesafeai`, `vercel`.

**[Verified]** Package `baml` covers files, paths, glob, subprocess and shell, HTTP client, a minimal HTTP and WebSocket server, raw sockets, crypto, hash, JSON, YAML, TOML, CSV, regex, time and random. Package `ai` covers clients (`Retry`, `Fallback`, `RoundRobin`), MCP, tools, streams, `Agent`/`Runner`, `FunctionSpec` and an in-memory `Journal`.

### Runtime

- **[Verified]** `bex_vm` runs bytecode until I/O. `bex_engine` drives it in an event loop; external operations go through a `SysOp` enum and a resource registry ([bex_engine/src/lib.rs#L1-L47](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/bex_engine/src/lib.rs#L1-L47)).
- **[Verified]** `baml_compiler2_rust` compiles MIR to Rust functions. A function with no lowering stays bytecode ([lib.rs](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_compiler2_rust/src/lib.rs)).
- **[Verified]** One shared heap for all VMs of an engine. The collector is a safepoint-based copying collector; every collection is full and compacting. Running VMs park at safepoints during GC ([gc.rs#L1-L11](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/bex_heap/src/gc.rs#L1-L11), [gc_policy.rs#L1-L10](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/bex_heap/src/gc_policy.rs#L1-L10)). The engine README still describes epoch coordination; the code uses permits.
- **[Verified]** Each spawned task is a `BexThread` on the tokio runtime. Child cancellation tokens are children of the parent token, so cancellation cascades down the spawn tree ([lib.rs#L5826-L5840](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/bex_engine/src/lib.rs#L5826-L5840)).
- **[Verified]** Cancellation is cooperative. It fires at the next `await` or I/O call as panic `baml.panics.Cancelled`.
- **[Verified]** Retries are library code: `ai.clients.Retry` (default 3 attempts, backoff, `retry_if`). A typed failure is retried only when its `retry_safety()` is `Safe` ([clients.baml#L61-L91](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_builtins2/baml_std/ai/ns_clients/clients.baml#L61-L91), [#L255-L275](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_builtins2/baml_std/ai/ns_clients/clients.baml#L255-L275)).
- **[Verified]** Timeouts are library code. `with_timeout` uses `spawn`, `CancelToken` and `sleep` ([future.baml#L282-L323](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_builtins2/baml_std/baml/ns_future/future.baml#L282-L323)). LLM clients have total, connect, first-token and between-token deadlines; each retry attempt starts new clocks ([ai/timeouts.baml](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_builtins2/baml_std/ai/timeouts.baml)).
- **[Verified]** No supervision construct, link or monitor was found. Unobserved task errors are reported ([spawn.baml#L132-L183](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_builtins2/baml_std/baml/ns_spawn/spawn.baml#L132-L183)).
- **[Verified]** No durability on the default branch. `ai.Journal` is in memory for one run ([journal.baml](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_builtins2/baml_std/ai/journal.baml)); telemetry has no durable spool ([telemetry.rs#L364](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/bex_engine/src/telemetry.rs#L364)). Pull request [#4956](https://github.com/BoundaryML/baml/pull/4956) (durable snapshots, resume in another process) is an open draft from 2026-09-21. Its description calls it a proof of concept, not a release candidate.
- **[Inference]** Tasks share one heap and mutable globals. This is shared-memory concurrency, not message passing. No sandbox or capability model was found in the `sys_*` crates. **[Unknown]** OS-level sandboxing by hosts.

### Hosts

- **[Verified]** Standalone: `baml run`, `baml test`, `baml pack` (a standalone executable) ([commands.rs#L116](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_cli/src/commands.rs#L116)).
- **[Verified]** Generators: Python, TypeScript (node and web), Swift, Go, Rust, Java, C++, C# ([generate.rs#L816](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_cli/src/generate.rs#L816)). Bridges ship as a CFFI library, native npm, WebAssembly npm, PyPI, Maven, NuGet, crates.io, Go and Swift (RELEASING.md). No Elixir or Erlang host was found.
- **[Verified]** Host callback results are checked against the declared `T` and `E`. A violation is an uncatchable `HostContractViolation` ([host.baml#L1-L20](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_builtins2/baml_std/baml/ns_host/host.baml#L1-L20)).
- **[Verified]** The shipped `baml` wrapper is a packed BAML program, 14 files, about 2,750 lines ([wrapper/README.md](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/wrapper/README.md)).

### Tooling

- **[Verified]** CLI: `check`, `describe`, `query`, `fmt`, `generate`, `test`, `init`, `new`, `run`, `pack`, `ide`, `agent`, `playground`, `codequality`, `lsp`, `telemetry` and others. `clean` is marked unavailable. `serve`, `dev`, `repl` and `optimize` are commented out ([commands.rs#L116](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_cli/src/commands.rs#L116)).
- **[Verified]** LSP (completion, definition, rename, usages, outline), formatter, VS Code and Cursor integration. Test blocks `test` and `testset` in BAML ([SKILL.md#L158-L163](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/skills/baml-core/SKILL.md#L158-L163)). The wrapper adds toolchain channels `canary` and `nightly` with per-project pins.
- **[Verified]** `baml agent install` and `baml describe` target AI coding agents. `baml codequality` and `baml fmt --check` are recent additions.

### Observability

- **[Verified]** `BAML_TELEMETRY` levels `low`, `medium` (default), `high`, `off`. At `medium`, LLM functions get spans with default captures and other functions get timing ([mode.rs#L9-L24](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/btel_settings/src/mode.rs#L9-L24)).
- **[Verified]** Network spans record HTTP request and response bodies by default (`omit_http_bodies` defaults to `false`). A body over 8 MiB is recorded as truncated. Identical bodies share one CAS blob. Header and query values outside an allowlist are stored as SHA-256 hashes ([artifact.rs#L1-L13](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/btel_settings/src/artifact.rs#L1-L13), [#L116-L119](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/btel_settings/src/artifact.rs#L116-L119), [network.rs#L1-L9](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/btel_settings/src/network.rs#L1-L9)).
- **[Verified]** `baml query` runs SQL over local recordings or Boundary Cloud ([query_command.rs](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_cli/src/query_command.rs)). The homepage says the runtime records the program and sends it to Boundary Cloud with no SDK or collector.
- **[Verified]** No replay on the default branch. Pull request [#3336](https://github.com/BoundaryML/baml/pull/3336) (playground HTTP record and pinned replay) is still open, last update 2026-04-08. The homepage and the v1 get-started page name no replay.
- **[Unknown]** Wire-byte fidelity of the stored body.

See the [Observatory comparison](../concepts/observability-and-replay.md#baml-recorded-call-debugging-compared-with-experiment-0003).

## Maturity signals

| Signal | Observation |
|---|---|
| Version | **[Verified]** 0.x product version, workspace `0.0.0-beta`, compiler feature flag `beta`, no 1.0 tag |
| Activity | **[Verified]** 191 commits on `canary` from 2026-10-07 to 2026-11-06, 147 in `baml_language/`, 12 author identities. Weekly commits in the last 12 weeks: 21 to 88 |
| Tests | **[Verified]** Static counts, not executed: 6,007 Rust tests and 6,136 BAML test blocks in `crates/`; 1,352 `.baml` files |
| Adoption | **[Verified]** 9,485 stars, 512 forks, about 113 contributors. Last month: `baml-bridge` (v1) 13,953 PyPI downloads; `baml-py` (v0) 593,281 |
| Stability markers | **[Verified]** Recent syntax changes (client blocks and `#"` strings removed). Stale module docs (`thread.rs`, engine README). Commented-out commands. No release notes after 0.23.0 |

**[Inference]** v1 bridge downloads are about 2% of v0 Python downloads; most users are still on v0. v1 is very active and broad, but pre-1.0. Treat it as a fast-moving beta, not a stable baseline. Any comparison must pin the exact toolchain build.

## Gaps

- **[Unknown]** Whether pull request #4956 (durability) or #3336 (replay) will merge.
- **[Unknown]** Any upstream plan for supervision, distribution or hot code loading.
- **[Unknown]** Performance of BAML green threads; no benchmark was read or run.
- **[Unknown]** Licence terms of vendored and forked crates.
- **[Unknown]** Which version named customers use.

## BEAML relevance

**[Inference]** v1 overlaps much of the BEAML surface idea: typed LLM functions, typed errors with `throws`, exhaustive `match`, structured concurrency with cancellation, typed client composition and telemetry recorded by default. Its retry safety gate and per-attempt clocks are evidence for the PROVIDER ATTEMPT decisions in the [glossary](../../GLOSSARY.md).

See the [BAML v1 vs BEAM/OTP comparison](../concepts/baml-language-and-tooling.md#baml-v1-vs-beamotp), [round 3, objection 2](../planning/roasting-rounds.md#2-baml-is-a-moving-baseline-with-overlapping-features) and [BAML internals](baml-internals.md).

---
id: raw-baml-v1-language-repo-2026-11-06
kind: research-capture
date: 2026-11-06
status: captured-not-ingested
---

# BAML v1 language, runtime, tooling and maturity: selected source capture

## Origin

- Repository: https://github.com/BoundaryML/baml (publisher: BoundaryML). Tree: `baml_language/`, plus `skills/` and root files.
- Access: 2026-11-06. Shallow, blobless, sparse clone into a scratch directory, plus GitHub REST API (`gh api`, `gh search prs`).
- Researcher: fresh worker for the BEAML knowledge base. Code read, not built and not run. No test was executed.
- Coverage: paraphrases, short identifiers and researcher notes. No upstream file is copied in full. Pull request text: only descriptions were read, not their diffs.
- Scope boundary: this capture does not repeat the compiler pipeline, SAP parsing, streaming and `baml query` schema already captured at pin `a5db82f06c1da0dfac28e283a15d19d37a3f2cf2` (see [baml-internals source page](../../../wiki/sources/baml-internals.md) and [debugging-replay capture](debugging-replay-2026-11-06.md)).

## Pinned commit

- Default branch: `canary`.
- Pin: `989676dd5169497c0d2a8d8e1d10914e987ae262`, committer date 2026-11-06T07:51:53Z ("Fix release docs job and setup-baml for wrapper 0.3 output (#5557)").
- Permalink base below: `P` = `https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/`.
- Tracked files at the pin: 11,462. `baml_language/crates/`: 77 crates, about 693,000 lines of Rust. Standard library sources (`baml_std`): about 37,900 lines of BAML.

## Licence note

**[Verified]** GitHub API reports SPDX `Apache-2.0` for the repository; workspace `Cargo.toml` sets `license = "Apache-2.0"` ([P/baml_language/Cargo.toml](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/Cargo.toml)). Vendored and forked crates (`forks/`, `vendor/`) can carry their own terms; not audited. No upstream code is copied into BEAML. See [license note](../../../wiki/sources/baml-license.md).

## 1. Language surface of v1

**Types**
- **[Verified]** Classes with mutable fields, static and `self` methods, struct-update spread, empty classes; classes are reference types. No inheritance; `interface` with `requires`, default methods, associated types and dynamic dispatch. Operators are interfaces (`baml.ops.Add`, `Compare`, `Equals`). Source: [P/skills/baml-core/SKILL.md#L44-L75](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/skills/baml-core/SKILL.md#L44-L75).
- **[Verified]** Enums are plain variants with no data and no methods. Data-carrying variants use a union of classes (`type Shape = Circle | Rect`). Literal unions, optionals `T?`, `map<K,V>`, arrays, `never`, `unknown`, `bigint`, `uint8array`. Same source.
- **[Verified]** Generics on functions and types, associated types, `Self`, equirecursive type aliases, variance rules, "scoped runtime type bindings" (`let type T = e;`). Types persist at runtime and support full reflection (`reflect.Type.of<T>()`, runtime-built classes and enums). Source: section list of [P/baml_language/TYPE_SYSTEM.md](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/TYPE_SYSTEM.md).

**Functions and control flow**
- **[Verified]** Expression-oriented blocks; `if`/`else` is an expression (no ternary); `for (let x in xs)`, `while`, `while let`, `break`, `continue`, `return`. Default parameters must be passed by name. Closures `(x) -> { ... }`. Top-level `const` is a global evaluated once at startup. Source: SKILL.md L44–L75.
- **[Verified]** Lexer keyword set includes `await`, `spawn`, `match`, `is`, `throws`, `throw`, `catch`, `catch_all`, `defer`, `interface`, `implements`, `requires`, `with`, `test`, `testset`, `client`, `template_string`, `generator`, `retry_policy`. No `async` keyword and no `import` keyword. Source: [P/baml_language/crates/baml_compiler_lexer/src](https://github.com/BoundaryML/baml/tree/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_compiler_lexer/src).
- **[Verified]** LLM functions are a DSL (`function F(...) -> T { client: ... prompt: ... }`) that desugars into ordinary code. `F(args)` is shorthand for running `F@spec(args)` through `ai.Agent`. Clients are values (`openai.ResponsesClient.new(...)`); the old `client<llm>` block is removed. Source: [SKILL.md#L89-L115](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/skills/baml-core/SKILL.md#L89-L115).

**Pattern matching**
- **[Verified]** `match (v) { pattern => expr }` with literals, `let x: T` (bind and narrow), class destructuring, or-patterns, guards, `_`; exhaustiveness is required. Also `v is T` and `if let`. Narrowing applies to locals only, not to field paths. Source: SKILL.md L44–L75; TYPE_SYSTEM.md "Pattern Matching", "Flow Narrowing".

**Errors**
- **[Verified]** Errors are ordinary class values. `throw`, signature `-> T throws E`, implicit propagation. `catch` handles named types and lets others pass; `catch_all` is exhaustive. `catch (e, ctx)` gives a `baml.errors.Context` cause chain. Source: [SKILL.md#L77-L82](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/skills/baml-core/SKILL.md#L77-L82).
- **[Verified]** A separate panic family (`baml.panics.*`: `DivisionByZero`, `IndexOutOfBounds`, `MapKeyNotFound`, stack overflow, `Cancelled`, `HostContractViolation`). Source: [P/baml_language/crates/baml_builtins2/baml_std/baml/ns_panics/panics.baml](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_builtins2/baml_std/baml/ns_panics/panics.baml).

**Async and futures**
- **[Verified]** "Colorless" green threads: `spawn { ... }` returns `baml.future.Future<T, E>`; `await` collects it. Combinators `all`, `all_settled`, `race`, `any`, `with_timeout`. Spawn modifiers via `spawn with m1, m2 { }`: `Limit` (concurrency cap), `CancelToken` (cooperative cancel), `Root` (detach from parent cancellation). `defer` runs at scope exit (LIFO); a `cleanup(self)` method is a finalizer. Sources: [ns_spawn/spawn.baml#L4-L23](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_builtins2/baml_std/baml/ns_spawn/spawn.baml#L4-L23), [#L132-L183](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_builtins2/baml_std/baml/ns_spawn/spawn.baml#L132-L183), [ns_future/future.baml#L94-L136](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_builtins2/baml_std/baml/ns_future/future.baml#L94-L136), [SKILL.md#L84-L87](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/skills/baml-core/SKILL.md#L84-L87).

**Modules and packages**
- **[Verified]** Namespaces come from `ns_<name>/` directories; no imports; cross-namespace access by absolute path `root.<ns>.<name>`. Source: SKILL.md L44–L75.
- **[Verified]** A package is a directory with `baml.toml`. `[dependencies]` supports path dependencies only (`x = { path = "../x" }`); no registry, git or version dependencies. Source: [P/baml_language/crates/baml_db/src/manifest.rs#L128-L138](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_db/src/manifest.rs#L128-L138).

**Standard library namespaces**
- **[Verified]** `baml_std` has 14 packages, each with `prelude = true` (available without a dependency entry): `ai`, `anthropic`, `assert`, `aws`, `baml`, `claude_code`, `google`, `log`, `openai`, `reflect`, `testing`, `trace`, `typesafeai`, `vercel`. Source: [P/baml_language/crates/baml_builtins2/baml_std](https://github.com/BoundaryML/baml/tree/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_builtins2/baml_std) and each package `baml.toml`. The root `baml.toml` there is a format workspace, not a package.
- **[Verified]** Package `baml` namespaces: `archive`, `crypto`, `csv`, `env`, `errors`, `events`, `fs`, `future`, `glob`, `hash`, `host`, `http` (client and a minimal HTTP/WebSocket server), `io`, `iter`, `json`, `media`, `net`, `ops`, `panics`, `path`, `random`, `regex`, `sap`, `spawn`, `sys` (subprocess, shell, sleep), `time`, `toml`, `ws`, `yaml`, plus core types.
- **[Verified]** Package `ai` namespaces: `clients` (Retry, Fallback, RoundRobin, StreamRelay), `content`, `errors`, `events`, `mcp`, `stream`, `tools`, `wire`, plus `Agent`/`Runner`, `FunctionSpec`, `Journal`, `LlmTimeoutOptions`.
- **[Inference]** `ai` is one package among many. The stdlib is general purpose (files, processes, HTTP server, crypto, time). Provider packages (`openai`, `anthropic`, `google`, `aws`, `vercel`, `claude_code`, `typesafeai`) are separate preludes.

## 2. Runtime

**VM and engine**
- **[Verified]** `bex_vm` executes bytecode synchronously until I/O. `bex_engine` drives it in a Deno-inspired event loop; external operations go through a `SysOp` enum and a `ResourceRegistry` that hands integer IDs to the VM. Source: [P/baml_language/crates/bex_engine/src/lib.rs#L1-L47](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/bex_engine/src/lib.rs#L1-L47).
- **[Verified]** `baml_compiler2_rust` compiles MIR to Rust functions that the VM runs in place of bytecode; a function with no lowering stays bytecode. Source: [P/baml_language/crates/baml_compiler2_rust/src/lib.rs](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_compiler2_rust/src/lib.rs).

**GC**
- **[Verified]** One shared heap (`BexHeap` in an `Arc`) for all VMs of an engine. Safepoint-based copying collector: Gen0 nursery carved into TLABs, Gen2 survivors, every collection is full and compacting. Coordination by heap permits: GC drains permits, running VMs park at safepoints, roots come from parked VMs and FFI handles. Allocation spending triggers collection; it is headroom, not a hard heap limit. Sources: [bex_heap/src/gc.rs#L1-L11](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/bex_heap/src/gc.rs#L1-L11), [gc_policy.rs#L1-L10](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/bex_heap/src/gc_policy.rs#L1-L10), engine lib.rs L24–L47.
- **[Verified]** The `bex_engine/README.md` still describes epoch-based coordination; the code doc describes permits. The prose lags the code (as noted at the earlier pin).

**Concurrency model**
- **[Verified]** Each spawned task is a `BexThread` (a VM plus metadata) that runs its own event loop on the tokio runtime (`wasm_bindgen_futures::spawn_local` on wasm). A child cancellation token is a child of the parent token, so parent cancellation cascades down the spawn tree. Source: [bex_engine/src/lib.rs#L5826-L5840](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/bex_engine/src/lib.rs#L5826-L5840), [bex_engine/src/thread.rs](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/bex_engine/src/thread.rs).
- **[Verified]** `thread.rs` module doc still says "Phase A" with one root thread; the engine has `spawn_thread`. The doc comment is stale.
- **[Inference]** Tasks share one heap and can alias mutable class values. The skill warns that tasks can interleave between statements, which is why field narrowing is not allowed. This is shared-memory concurrency, not message passing.

**I/O**
- **[Verified]** Stdlib I/O: files, paths, glob, subprocess and shell with pipes, HTTP client with transport timeouts, HTTP and WebSocket server, raw sockets (`net`), env, sleep. Sources: `baml_std/baml/ns_sys/sys.baml`, `ns_http/server.baml`, namespace list above.

**Embedding and hosts**
- **[Verified]** Standalone: `baml run`, `baml test`, and `baml pack` (package a target as a standalone executable). Source: [P/baml_language/crates/baml_cli/src/commands.rs#L116](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_cli/src/commands.rs#L116).
- **[Verified]** Generators: `python/pydantic`, `python/pydantic/v1`, `typescript/node`, `typescript/web`, `swift`, `go`, `rust`, `java`, `cpp`, `csharp`. Source: [P/baml_language/crates/baml_cli/src/generate.rs#L816](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_cli/src/generate.rs#L816). `sdks/` also has `ruby`.
- **[Verified]** Bridges ship as CFFI library, PyPI `baml-bridge`, npm `@boundaryml/baml-bridge` (native) and `-web` (WebAssembly, browsers and Cloudflare Workers), Maven, NuGet, crates.io, Go and Swift repos. Source: [P/baml_language/RELEASING.md](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/RELEASING.md).
- **[Verified]** Host callbacks: compiler-synthesized wrappers call host closures; returned values are checked against the declared `T` and `E`; violations are an uncatchable `HostContractViolation`. Source: [baml_std/baml/ns_host/host.baml#L1-L20](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_builtins2/baml_std/baml/ns_host/host.baml#L1-L20).
- **[Verified]** Dogfooding: the shipped `baml` wrapper (toolchain selector and installer) is a packed BAML program, 14 files, about 2,750 lines. Source: [P/baml_language/wrapper/README.md](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/wrapper/README.md).

**Process and isolation**
- **[Inference]** No process isolation between tasks inside one engine: shared heap, shared mutable globals ("one engine-wide value", SKILL.md L44–L75). No capability or sandbox model was found in `sys_*` crates (search for `sandbox`/`capabilit` found nothing). **[Unknown]** OS-level sandboxing by the hosts.

**Retries, cancellation, timeouts**
- **[Verified]** Retries are library code: `ai.clients.Retry` (default 3 attempts, `Backoff`, `retry_if`), `Fallback`, `RoundRobin`. A shared safety gate retries a typed failure only when its `retry_safety()` is `Safe`; refused, invalid-request, parse and finish-reason failures are not retried; a member's own `Timeout` is retried. Source: [ai/ns_clients/clients.baml#L61-L91](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_builtins2/baml_std/ai/ns_clients/clients.baml#L61-L91), [#L255-L275](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_builtins2/baml_std/ai/ns_clients/clients.baml#L255-L275).
- **[Verified]** Cancellation: cooperative; it fires at the next checkpoint (an `await` or an I/O call) as panic `baml.panics.Cancelled`, and cascades to non-`Root` children. Source: spawn.baml L4–L23.
- **[Verified]** Timeouts: `baml.future.with_timeout` is BAML code built on `spawn`, `CancelToken` and `sleep`. LLM clients take `LlmTimeoutOptions` with total (default 5 min), connect (default 10 s), first-token and between-token deadlines; each retry attempt starts its own clocks. Sources: [future.baml#L282-L323](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_builtins2/baml_std/baml/ns_future/future.baml#L282-L323), [ai/timeouts.baml](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_builtins2/baml_std/ai/timeouts.baml).

**Supervision and durability**
- **[Verified] No supervision.** A search for "supervis" in crates, SDKs and skills found no runtime supervision construct. Unobserved task errors are "still reported" (spawn.baml L178–L183), but no restart strategy, link or monitor exists.
- **[Verified] No durability on the default branch.** `ai.Journal` is an in-memory append-only list of events for one run ([ai/journal.baml](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_builtins2/baml_std/ai/journal.baml)). Engine telemetry code says there is no durable spool ([telemetry.rs#L364](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/bex_engine/src/telemetry.rs#L364)). No `bex_snapshot` crate exists at the pin.
- **[Verified] Durability is a draft proof of concept.** Pull request [#4956](https://github.com/BoundaryML/baml/pull/4956) "Durable BAML functions: pause a running program, resume it anywhere": open, draft, created 2026-09-21, last update 2026-09-21, head `3658d431916747d2551a4865b3079b31eb54a712`, 156 files. Its description (only the description was read):
  - snapshot of call stacks, reachable heap, futures and cancel tokens, pointer-free, restored in another process;
  - resume cost proportional to heap, not history; no determinism constraint on user code (stated contrast to journal-and-replay systems);
  - durable sleep, remote calls with cascading cancellation, content-addressed program store, fork by loading a snapshot twice;
  - hidden `baml worker` and `baml program-store` subcommands;
  - known limits: globals not in snapshots; host callbacks and live host resources (sockets, unread HTTP responses, SSE streams) block a snapshot; LLM calls not covered; `@@durable` attribute designed, not built;
  - it says "a POC on a feature branch, not a release candidate".

## 3. Tooling

- **[Verified]** CLI subcommands at the pin ([commands.rs#L116](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_cli/src/commands.rs#L116)): `check`, `clean` (marked "currently unavailable"), `describe`, `query`, `auth`, `update`/`upgrade`, `feedback`, `fmt`, `generate`, `test`, `init`, `new`, `run`, `pack`, `ide`, `agent` (installs the bundled agent skill), `playground`, `codequality`, `lsp`, `help`, `telemetry`, hidden `__flush-telemetry`. Commented out: `serve`, `dev`, `repl`, `optimize`, HIR and bytecode dumps.
- **[Verified]** The wrapper adds `toolchain use|install|update` with `canary` and `nightly` channels and per-project pins in `baml.toml` (wrapper README).
- **[Verified]** LSP: `baml_lsp`, `baml_lsp_server`, `baml_ide` (completion, definition, rename, usages, outline, describe, tokens). Formatter: `baml_fmt` and `baml_fmt_wasm`. Editor integrations: VS Code `.vsix`, `baml ide install --code|--cursor` (RELEASING.md, commands.rs).
- **[Verified]** Test runner: `test "name" { }` and `testset` blocks in BAML; six asserts; IDs `root::Test`; `-i`/`-x` filters. Source: [SKILL.md#L158-L163](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/skills/baml-core/SKILL.md#L158-L163).
- **[Verified]** Playground: `baml playground` serves a project to a browser.
- **[Verified]** Package manager: none beyond path dependencies. Toolchain management is the wrapper. `baml agent install` and `baml describe` target AI coding agents.
- **[Verified]** Compiler feature flags: `-F/--features` with values `beta` and `display_all_warnings` (commands.rs L100–L112).

## 4. Observability and debug

- **[Verified]** `BAML_TELEMETRY` levels `low`, `medium` (default), `high`, `off`. At `medium`, LLM functions get spans and default captures; ordinary functions get timing. Source: [btel_settings/src/mode.rs#L9-L24](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/btel_settings/src/mode.rs#L9-L24).
- **[Verified]** HTTP bodies: network spans record request and response bodies unless the publisher sets `http_bodies = false` (field `omit_http_bodies`, default `false`). A body over 8 MiB is recorded as truncated. Identical bodies share one CAS blob. Non-allowlisted header and query values are stored as SHA-256 hashes. Sources: [btel_settings/src/artifact.rs#L1-L13](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/btel_settings/src/artifact.rs#L1-L13), [#L116-L119](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/btel_settings/src/artifact.rs#L116-L119), [network.rs#L1-L9](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/btel_settings/src/network.rs#L1-L9). This resolves the earlier **[Unknown]** about the default body policy for the code track: bodies are recorded by default. **[Unknown]** Wire-byte fidelity of the stored body (still open). The packed wrapper itself sets bodies off.
- **[Verified]** `baml query` runs SQL over local recordings or Boundary cloud (`--local`, `--project`, `--environment`). Source: [baml_cli/src/query_command.rs](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_cli/src/query_command.rs).
- **[Verified]** Replay status:
  - [#3336](https://github.com/BoundaryML/baml/pull/3336) (playground HTTP record and pinned replay): still open, not merged, last update 2026-04-08. Unchanged since the earlier capture.
  - [#4860](https://github.com/BoundaryML/baml/pull/4860) "Btel replay benchmarks": closed (telemetry replay benchmarks, not call replay).
  - [#4956](https://github.com/BoundaryML/baml/pull/4956) (durable snapshots, section 2) is the nearest newer work. It is resume from state, not record-and-replay.
  - Merged recording work in the window: network spans for HTTP requests (#5068), recorded context in `baml query` (#5087), class and enum definitions as CAS blobs (#5169, #5171), streamed LLM function as its own span (#5258), `baml_code(v)` to rebuild recorded types in tests (#5334), bridge traces found by `baml query --local` (#5485).
- **[Inference]** Built-in path stays: record by default, query with SQL, re-parse with `F@parse` in a test. Replay or caching of model calls is user code (`ai.Runner`, fake `ai.Client`). No REPLAY RUN with identity checks exists on the default branch.

## 5. Maturity signals

- **[Verified]** Versions:
  - Rust workspace version `0.0.0-beta` ([Cargo.toml#L67](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/Cargo.toml#L67)).
  - Stamped product version `0.25.1`, channel `canary` ([baml_version/src/lib.rs#L3-L5](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/baml_language/crates/baml_version/src/lib.rs#L3-L5)); `release.toml` `canary_version = "0.25.1"`; PyPI `baml_bridge` and npm `@boundaryml/baml-bridge` both `0.25.1`.
  - Wrapper crate `baml` version `0.3.1`.
  - The legacy line (BAML v0) continues separately: `0.226.3` on 2026-10-27 in root `CHANGELOG.md`; the root README badge still points to PyPI `baml-py` (the v0 package).
- **[Verified]** Release tags: v1 tags use prefix `baml-language-`. Recent: `baml-language-0.25.1` (2026-11-06, target `6a3eb3d…`), `0.25.0` (2026-11-06), `0.24.0` (2026-11-05), plus near-daily `0.23.1-nightly.*` tags. All have `prerelease=false`. No `v1.*` or `1.0` tag exists; the `v0.2xx` tags belong to the legacy line.
- **[Verified]** Release process: nightly from the newest green `canary` commit; a canary release every Friday by the oncall (RELEASING.md).
- **[Verified]** Markers: workspace version `-beta`; compiler feature flag `beta`; `clean` "currently unavailable"; several commands commented out with a TODO; [CONTRACTS.md](https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/CONTRACTS.md) marks a 2026-09 model as superseded; stale module docs in `thread.rs` and the engine README. An earlier capture of v0 docs records "public beta" for v1; no "public beta" string was found in the repository files searched.
- **[Verified]** Test counts at the pin (static counts of test attributes and test blocks, not executed): `crates/` 6,007 Rust tests and 6,136 BAML `test` blocks; `sdks/` 690; `sdk_tests/` 336; `forks/` 173; `vendor/` 13. 1,352 `.baml` files.
- **[Verified]** Activity, 2026-10-07 to 2026-11-06 on `canary`: 191 commits, 147 of them touch `baml_language/`, 12 distinct author identities. Repository: 9,485 stars, 365 open issues, last push 2026-11-06T08:22:27Z.
- **[Inference]** Readiness: very active and broad (10 host languages, wasm, packed binaries, self-hosted wrapper, large test corpus), but pre-1.0. Version numbers are 0.x, the workspace says beta, syntax changed recently (client blocks and `#"` strings removed), and supporting docs lag the code. Treat it as a fast-moving beta, not a stable baseline.

## 6. Implications for BEAML [Inference]

**Overlap**
- **[Inference]** BAML v1 already covers much of the BEAML surface idea: typed LLM functions with a schema from the return type, typed errors with `throws`, exhaustive `match`, structured concurrency with cancellation, typed client composition (retry, fallback), telemetry recorded by default, offline re-parse, an agent-oriented CLI (`describe`, `codequality`, `agent install`).
- **[Inference]** Its retry safety gate (`RetrySafety.Safe`) and per-attempt clocks are close to the BEAML PROVIDER ATTEMPT topic; they are evidence for the retry-rule decisions in the glossary note.

**Where BEAM/OTP differs**
- **Processes and isolation**: BAML tasks share one heap and mutable globals; GC is a stop-the-world full copy across all VMs of an engine. BEAM processes have private heaps, per-process GC and copy-on-send. A BEAML design gets isolation and per-task GC from the VM, not from language rules.
- **Failure handling**: BAML has cancellation cascade only, and an "unobserved error is reported". OTP adds links, monitors and supervisors with restart strategies. This is a clear BEAML differentiator for long-running agents.
- **Distribution**: BAML has no distribution on the default branch. Remote calls exist only in the draft durable POC. BEAM has native distribution, but cross-node calls still need explicit CONTRACTS and failure semantics.
- **Hot code**: no hot code loading for running BAML programs was found (only a wasm build-identity hook and a "watch command experiment" PR). BEAM supports two module versions at once. A BEAML design must define how a running WORKFLOW RUN treats a code change, which also affects any REPLAY CAPSULE.
- **Durability**: BAML's draft approach snapshots heap state and rejects determinism constraints. A BEAM approach would more likely use an event log or CHECKPOINT per process. Neither is established for BEAML.
- **Host model**: BAML embeds into 10 host languages with generated SDKs and a CFFI/wasm bridge. A BEAM-hosted language naturally targets Elixir/Erlang hosts; FFI to other hosts needs ports or NIFs and a GENERATED ABI decision.

**[Unknown]** Performance of BAML green threads against BEAM processes; any upstream plan for supervision; whether #4956 will merge.

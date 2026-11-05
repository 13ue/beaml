# BEAM runtime and interop

Status: **[Verified]** upstream facts with **[Proposal]** design implications. [Source inventory and limits](../sources/beam-otp-phoenix.md).

## Generated code and build boundary

**[Requirement]** The first BEAML backend emits Erlang/Elixir-compatible source, with Mix invoking the standalone Rust compiler. The generated public API, effect dictionaries, schema witnesses and cancellation representation remain unspecified. [Product contract](product-contract.md); [gaps](../planning/specification-gaps.md).

**[Verified]** `Code.compile_quoted/2` and `compile_string/2` produce module/bytecode pairs and accept a diagnostic filename. Compilation can execute arbitrary code with VM privileges. The parser offers atom and source-position options. [Code](https://elixir.hexdocs.pm/Code.html#compile_quoted/2).

**[Verified]** A Mix compiler implements `run/1`, returns diagnostics, and supplies manifests/cleanup when it tracks or writes artifacts. The project orders compiler tasks. [Compiler behaviour](https://mix.hexdocs.pm/Mix.Task.Compiler.html); [mix compile](https://mix.hexdocs.pm/Mix.Tasks.Compile.html#configuration).

**[Proposal]** Start with one generated source route and a versioned boundary descriptor, not two backends. Pin supported Rust/OTP/Elixir/Phoenix versions. Define module/function names, ordinary term representations, errors, validation entry points, effect dictionary arguments and schema fingerprints before exposing the API. Mix should track source/import/compiler-version dependencies, remove deleted outputs and reject failed/stale generation. Test clean, no-change, imported-schema change, file removal and compiler failure; merely generating a file is insufficient build integration.

## Validation survives the foreign boundary

**[Verified]** Elixir typespecs document types and feed tools such as Dialyzer; the compiler does not use them to optimize/modify code. They are distinct from Elixir's developing set-theoretic type system. [Typespecs](https://elixir.hexdocs.pm/typespecs.html).

**[Inference]** Emitting `@spec` or `@opaque` cannot establish BEAML trust states for arbitrary foreign values. **[Proposal]** Retain runtime decoders/validators at public entry points. Keep nominal identity and schema-version checks explicit; test forged maps/structs, missing/extra fields, wrong versions and malformed nested data before domain effects. An opaque representation limits normal API use, not arbitrary trusted VM code.

**[Verified]** Atoms are not collected; arbitrary string-to-atom conversion can exhaust the VM. Existing-atom conversion requires preexisting vocabulary. [OTP caveats](https://www.erlang.org/doc/system/commoncaveats.html#list_to_atom-1-binary_to_atom-1-2). Safe external-term decoding does not establish application validity. [binary_to_term/2](https://www.erlang.org/doc/apps/erts/erlang.html#binary_to_term/2).

**[Proposal]** Keep model/browser identifiers and map keys binary by default; map only a closed compile-time vocabulary to atoms. Bound identifiers from compiler sources too, especially an editor process consuming many files. Test arbitrary input cannot create unbounded atoms; parser atom-safety settings need a separate prototype because alternative encoders may produce analysis-only AST.

## Tasks, streams and cancellation

**[Verified]** Supervised async tasks can remain linked to their caller. `async_nolink` avoids that link, requires temporary task restart semantics, and produces result and DOWN messages. [Task.Supervisor](https://elixir.hexdocs.pm/Task.Supervisor.html#async_nolink/3). `Task.shutdown/2` unlinks/stops a task and may race with a final reply. [Task](https://elixir.hexdocs.pm/Task.html#shutdown/2).

**[Proposal]** Define each model call's owner, monitor/reference, timeout/deadline, cancellation result and terminal-state precedence. Request IDs must suppress stale replies without masking resource leaks. Bound stream queues, define consumer-demand/buffer behavior and close on owner death. Provider retries need idempotency and budget rules; supervision alone must not replay chargeable requests. Test owner death, timeout/completion races, slow consumers, collector outages, transport cleanup and retry limits independently.

**[Verified]** Native crashes can crash the VM; long normal NIF calls damage scheduler responsiveness. Dirty schedulers accommodate long work, but native execution can continue after the Erlang process terminates. [NIF API](https://www.erlang.org/doc/apps/erts/erl_nif.html#functionality).

**[Inference]** A Rust NIF is neither a sandbox nor guaranteed interruptible cancellation. **[Proposal]** Keep compilation out of the application VM initially, as specified; any later native runtime parser requires bounded work, cooperative cancellation and explicit trust review. A separate OS process is an alternative where crash containment outweighs call overhead; neither route is selected here.

## Upgrade is a protocol problem too

**[Verified]** BEAM keeps old/current module code; fully qualified calls use current code. [Code replacement](https://www.erlang.org/doc/system/code_loading.html#code-replacement). OTP does not support loading compiled code on older releases. [Compatibility](https://www.erlang.org/doc/system/misc.html#compatibility). `GenServer.code_change/3` handles state reshaping; it can reject a migration. `format_status/1` can redact diagnostic state. [GenServer](https://elixir.hexdocs.pm/GenServer.html#c:code_change/3).

**[Proposal]** Version generated schema/event/API descriptors separately from compiler and application versions. Pin descriptor identity for in-flight calls; reject incompatible messages instead of decoding with the new schema accidentally. Treat hot state migration, queued message compatibility and rolling-deployment skew as explicit features requiring tests, not benefits automatically inherited from BEAM loading. Include process status/crash reports in redaction coverage; Observatory export policy cannot alone cover them.

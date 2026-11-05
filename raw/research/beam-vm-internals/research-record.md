# OTP VM internals: selected evidence record

Publisher: Ericsson AB / Erlang/OTP contributors. Retrieved 2026-11-05. Tag `OTP-29.1.2`, commit `d199a49a01a2079afb6f2c5c9ae047cd4555e68d`; exact files and inspected areas are in [provenance](provenance.json). This is researcher paraphrase, not a full source mirror. Source files carry their own Apache-2.0 notices. Status: source/documentation checked, no experimental validation.

## Compiler and execution observations

`compile.erl` names and orders the passes. At this pin, `kernel_passes/0` retains an old name/comment but dispatches `core_to_ssa`; the implementation calls `beam_core_to_ssa`, not a separately inferred Kernel representation. SSA records have blocks, assignments and explicit terminators. The internal SSA document requires exceptional edges into landing pads, ordered exception extraction and correct try-tag lifetime. Validator comments explicitly concern generated code that could damage the emulator; they do not claim the user's program is free of type errors.

`genop.tab` documents generic instruction semantics, including continuation pointers, tail calls, heap needs and live X registers. `ops.tab` is the loader/emulator specialization layer and distinguishes internal opcodes from file opcodes. `beam_load.c` reads/parses a BEAM file, checks module/opcode compatibility and prepares emitted code. BeamAsm compiles at loading, preserving runtime term/process/GC mechanisms. Its x86 return emitter decrements the reduction counter and dispatches when exhausted. An x86 register listing is not a portable language ABI.

## Representation and memory observations

`erl_term.h` defines primary/header/immediate tags. `erl_bits.h` in this pin uses `ErlHeapBits`, `ErlSubBits`, and `BinRef`; the old efficiency-guide description warns it has not been fully updated for the OTP27 binary rewrite. `erl_map.h` uses flat maps for small maps and HAMT structures for larger maps; normal/debug thresholds differ. `erl_fun.h` separates local function entries, external exports and a variable-sized environment.

The GC description explains roots, copying, young/old generations and off-heap/message tradeoffs. It links historical OTP18/19 implementation examples, so those instruction listings and exact allocation policies are not current experiments. Functional immutability supports heap-generation invariants, but readers must not infer that no compiler optimization can perform a proven-safe physical update. Process messages ordinarily copy compound terms; shared refc binaries/literals are exceptions. A small sub-binary or closure can keep a large source alive. Allocation pressure, queue contents and references determine lifetime; no blanket zeroization follows from dropping a variable.

## Scheduling, messaging and failure observations

Normal schedulers run many processes using reduction accounting and runtime cooperation. Native code has explicit scheduling/resource responsibilities. The dirty-NIF documentation says termination can release Erlang-visible resources and deliver monitor/link signals while native execution continues. I/O uses polling/check_io/driver or NIF interfaces rather than one universal blocking-call model.

The process reference distinguishes asynchronous signal reception from receive selection. Ordering guarantees are per sender and destination, not a global total order. OTP28 priority messages can alter mailbox order between priority and ordinary messages despite preserved signal delivery ordering. Selective receive may scan a long queue; compiler-recognized fresh-reference patterns can skip older messages. Aliases suppress later arrivals after deactivation but do not remove queued messages or cancel remote work. Distribution can lose signals on disconnect; output-channel flow control can suspend an apparently asynchronous send. Fully asynchronous distribution moves the burden to bounded application flow control.

Supervision defines start/stop order, restart sets and intensity, not business transaction rollback. Callback cleanup is conditional on termination path; an untrappable kill is not a finally block. Monitors describe process/node observations, not whether a paid provider request executed before failure.

## Shared state, distribution and operations observations

ETS has an owner, explicit permissions and lifecycle; unreachable tables are not automatically reclaimed while their owner survives. Operations copy terms, and individual atomic operations are not whole workflow transactions. `persistent_term` reads avoid copying but complex replacement/deletion can schedule all processes for scans and copy retained values. This creates a meaningful latency/secret-retention tradeoff.

Distributed Erlang is a cluster trust mechanism. Its official guide warns against unprotected distribution and documents cookies/TLS; application tenant authorization is separate. ETF roundtripping does not prove schema validity. Local monotonic clocks cannot be compared across VM instances. Current/old code coexist, local/external call choices affect upgrades, and captured local functions can retain old code. SASL appup/relup release handling coordinates changes but does not solve incompatible queued messages or rolling schema changes automatically.

Profiling tools differ in overhead and observability: detailed tracing can materially perturb the workload, sampling/aggregate counters answer different questions, and memory from allocators can differ from OS RSS. Crash dumps contain process/memory details and can expose secrets. `process_flag(sensitive,true)` suppresses specified introspection/tracing surfaces, not authorized outbound effects or arbitrary native/host access.

## Explicit limits

Not a full OTP audit, a hardware benchmark, scheduler model proof, source-level compiler correctness proof, confidentiality theorem or stable ABI specification. Worked examples in the wiki are constructed explanations/proposed probes and were not executed. Numeric source examples that identify older OTP versions remain historical. Read this alongside the supplied BEAML specification's runtime, trust, source-map, security and performance requirements.

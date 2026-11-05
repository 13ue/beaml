# Inspection, privacy and realistic performance evidence

Status: **[Verified]** primary tool/runtime descriptions; **[Proposal]** BEAML measurement and privacy procedures. [Source inventory](../../sources/beam-vm-internals.md).

## Inspection is an effectful data path

**[Verified]** OTP tools can inspect processes, stacks, messages, dictionaries, tables, code and memory. Crash dumps contain structured runtime details including process and binary/message-related state. Detailed tracing may record arguments/results and significantly perturb execution; profiler modes vary. [Crash dump contents](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/erts/doc/guides/crash_dump.md); [Profiling guide](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/system/doc/efficiency_guide/profiling.md).

**[Verified]** `process_flag(sensitive,true)` suppresses specified tracing, queue/dictionary inspection, stack and dump details for that process. It is selective introspection control, not isolation from arbitrary trusted native/host code. Local monotonic timestamps are not comparable across independent VM instances. [BIF documentation](https://www.erlang.org/doc/apps/erts/erlang.html#process_flag/2); [Monotonic time](https://www.erlang.org/doc/apps/erts/erlang.html#monotonic_time/0).

**[Proposal]** A secret wrapper's custom inspection does not cover raw binary copies in a message, exception arguments, a driver, ETS, a process dictionary or a crash dump. Test the actual configured sinks and operational capture paths with canaries. Use metadata/allowlisted counts for routine Observatory views; privileged raw inspection requires its own access/audit policy. Preserve useful redacted status through `format_status` without claiming other inspection surfaces inherit it. Never enable broad production argument tracing as an unrecorded debugging convenience.

## Choose the tool for the question

| Question | Primary mechanism/tool | Limit to record |
|---|---|---|
| Where is wall latency spent? | End-to-end monotonic intervals plus scoped spans | Network, queueing, scheduling, GC and provider time need distinct boundaries. |
| Which functions dominate calls/time/heap allocation? | OTP `tprof`; detailed `fprof`; call counters | Tracing changes work and can retain sensitive data. Compare profiled and unprofiled cases. |
| Which runtime subsystem consumes scheduler time? | `msacc` | Aggregate runtime states do not identify a domain command by themselves. |
| Are locks the bottleneck? | `lcnt` | Requires suitable runtime build/support and targeted workload; not an always-on product feature. |
| Is native/JIT execution CPU-heavy? | OS sampling and supported BeamAsm perf metadata | Architecture, JIT flags and symbol capture matter; no single speedup multiplier. |
| Why does RSS grow? | VM memory/allocator data, process/ETS/binary info plus OS measurement | Allocator reservation/fragmentation and shared binaries prevent naïve summation. |

The tool facts derive from the [pinned profiling guide](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/system/doc/efficiency_guide/profiling.md); choosing them for BEAML is **[Proposal]**. No profiler was run in this research.

## Worked measurement design

**[Proposal]** Measure one recorded-response decode as a whole operation, then split: waiting in queue -> parsing -> validation/refinement -> domain transition -> safe instrumentation. Run four input families: tiny valid scalar, nested valid record, near-limit malformed input, and long stream with a slow consumer. Add cancellation and collector outage. Count rejected input's domain effects, bytes retained, dropped observations and terminal cleanup alongside latency. This stops a faster parser from hiding unbounded retention or false validation.

Run warm and cold compiler/query cases separately from runtime requests. Exclude actual model/network time from compiler/LSP budgets as the spec requires. Keep a provider fixture's token partition/revision behavior fixed so a runtime change is not confused with different model output.

**[Verified]** OTP's benchmark guide distinguishes wall and CPU time, recommends sufficiently long measurements and fresh processes to avoid heap-history bias, and warns against generalizing across architectures. Its example microbenchmarks and suggestion to inspect the best achievable time do not replace BEAML's declared percentile/iteration acceptance protocol. [Benchmarking](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/system/doc/efficiency_guide/benchmarking.md).

**[Proposal]** Report the exact OTP/ERTS/Elixir/compiler commit, JIT/interpreter/build mode, CPU/memory/OS, scheduler/dirty scheduler counts, workload concurrency, corpus hash, warmup, cache state and run count. Capture wall latency percentiles and CPU/allocations, queue length/bytes, referenced binaries, ETS and RSS. Do not average away timeouts or trim outage runs. Separate profiler overhead and ordinary telemetry overhead by running comparable control/treatment workloads. A single process/ring can remain sequential; worker count is not achieved parallelism.

**[Requirement]** The PDF's quantitative targets are proposed, including baseline 30 iterations and specified hardware/percentiles; UI tables use a different hardware/percentile vocabulary. Preserve the discrepancy and adopt one explicit comparison protocol before reporting success. [Exact acceptance source](../../sources/engineering-spec-v0.5.md); [gap queue](../../planning/specification-gaps.md).

## What evidence would count

**[Proposal]** Store raw measurements, fixture/version identifiers, command lines, normalized diagnostics and a readable result with exclusions. Use source maps to attribute runtime failures to authored spans but acknowledge stack optimizations/tail calls and macro lowering can remove or change frames. Cross-node spans need explicit context propagation; monotonic duration math must stay within the same clock domain.

**[Unknown]** No current BEAML performance, supported instrumentation overhead, production memory bound, scheduler fairness theorem or canary-leak result exists. Understanding ERTS mechanisms helps design the measurement; it cannot satisfy a gate without actual execution.

# Scheduling, native code and I/O boundaries

Status: **[Verified]** selected source mechanisms; **[Proposal]** generated-runtime choices and probes. [Pinned inventory](../../sources/beam-vm-internals.md).

## Reductions are a cooperation mechanism

**[Verified]** The VM multiplexes Erlang processes across scheduler threads. Reduction accounting gives runnable processes turns; it is not a public promise of one reduction per CPU instruction or an exact wall-clock deadline. BeamAsm carries the remaining reduction counter in runtime state; its x86 return emitter decrements/checks it and dispatches when exhausted. Runtime/BIF paths also participate in yielding/accounting. [BeamAsm model](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/erts/emulator/internal_doc/BeamAsm.md); [Return emitter](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/erts/emulator/beam/jit/x86/instr_call.cpp#L43-L75).

**[Inference]** A loop in ordinary BEAM code, a long native function, a process waiting for network, and a runnable process waiting for CPU have different latency causes. Adding workers helps only if the workload has parallel runnable work and no dominating serial bottleneck. One GenServer doing all parse/dispatch work can serialize a request stream despite thousands of child processes.

**[Proposal]** Worked load model: eight CPU-bound validators compete with one LiveView and telemetry flush task. Measure scheduler runnable queues, CPU/reductions, validation duration and UI tail latency. Then repeat with validators inside a normal NIF and on dirty CPU schedulers. These are three different experiments; throughput alone can hide a UI starvation regression. Do not assume raising the LiveView priority solves it: higher-priority long work can starve normal OTP servers.

## Native code is inside the VM trust boundary

**[Verified]** NIF code executes with native access inside the VM. A crash or invalid memory operation can damage the whole node. Normal NIF work must be short; longer work needs splitting/rescheduling or correctly classified dirty CPU/I/O jobs. Dirty scheduling protects ordinary schedulers from one class of blocking but does not provide memory isolation. Resource objects have lifetime/destructor rules distinct from a source-language handle variable. [NIF reference: long-running functions/resources](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/erts/doc/references/erl_nif.md).

**[Verified]** Terminating a process executing a dirty NIF can release its visible resources and trigger monitors/links while the native function continues. The native implementation can check liveness and cooperate; the VM does not forcibly interrupt arbitrary native computation safely. [Dirty NIF termination](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/erts/doc/references/erl_nif.md#functionality).

**[Proposal]** A cancellation contract needs three states, not just a killed pid: result publication stopped, transport/provider cancellation requested, and owned resources actually released. A provider may still bill or finish. Record which guarantee each adapter gives. Test cancellation during native parsing, socket read, retry delay and completed-but-undelivered reply; never classify a monitor DOWN alone as proof all external work ceased.

## Ports and asynchronous I/O have distinct boundaries

**[Verified]** An external program reached through a port is an OS-process boundary; linked-in port drivers remain native code loaded into the VM. “Port” is not automatically synonymous with isolation. The check-I/O subsystem connects platform polling to drivers through `driver_select` and to NIFs through `enif_select`; ports/NIFs are notified of readiness rather than making every wait block an ordinary scheduler. [Ports](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/system/doc/reference_manual/ports.md); [I/O event path](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/erts/emulator/internal_doc/CheckIO.md#checking-for-io-events).

| Candidate boundary | Gains | Responsibilities still needed |
|---|---|---|
| Ordinary BEAM runtime module | VM scheduling/GC/process integration | Bound parsing/queues; explicit foreign effects and errors |
| Dirty or yielding NIF | Low-call-overhead native implementation | Native memory/resource safety, CPU/I/O classification, cooperation, platform builds |
| External compiler/helper process | OS crash containment and independent toolchain | Framing/size limits, exit/timeout/restart handling, stdout/stderr privacy, concurrent request IDs |

**[Proposal]** The spec already chooses the compiler as an external Rust executable; keep that boundary until measured evidence requires change. A future native runtime parser is a separate design decision. For an external helper, treat malformed length prefixes, huge replies, process death mid-frame and cancellation races as validation boundaries. For a NIF, exception wrappers cannot catch a native segmentation fault.

## Backpressure is part of the protocol

**[Inference]** BEAM process isolation does not prevent an unbounded producer mailbox or shared binary retention. Dirty schedulers can also saturate. “Asynchronous” describes who waits for a result; it does not establish bounded memory, fair throughput or a workload deadline.

**[Proposal]** Use explicit demand/credits or a byte/item limit at the provider-stream edge; define overflow policy and consumer death. Keep routine telemetry best-effort and bounded separately from security audit. Preserve an absolute operation deadline across retries rather than resetting the full budget on each stage. The [stream design](../structured-output-and-streaming.md), [process failure model](processes-messages-and-otp.md) and [performance protocol](inspection-and-performance.md) must be specified together. No scheduler experiment has been run here.

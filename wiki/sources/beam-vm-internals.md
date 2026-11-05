# BEAM VM, compiler and OTP internals

Status: researched; **[Verified]** means selected primary-source reading, not BEAML/runtime execution. Publisher: Ericsson AB / Erlang/OTP contributors. Retrieved 2026-11-05. Pin: [OTP-29.1.2](https://github.com/erlang/otp/tree/d199a49a01a2079afb6f2c5c9ae047cd4555e68d), compiler 10.0.7 / ERTS 17.1.1 / STDLIB 8.1.1. [Exact provenance/file inventory](../../raw/research/beam-vm-internals/provenance.json); [selected observation record](../../raw/research/beam-vm-internals/research-record.md). Upstream code/docs carry their original Apache-2.0 notices; only our paraphrases are retained.

## Mechanism-level reading map

| Area | Primary entry points at the pin | Compiled explanation |
|---|---|---|
| Compilation | `lib/compiler/src/compile.erl`, `beam_core_to_ssa.erl`, `beam_ssa.hrl`, internal SSA invariants, `beam_validator.erl` | [Execution and compilation](../concepts/beam/execution-and-compilation.md) |
| Instructions/load/JIT | `genop.tab`; `erts/emulator/beam/emu/ops.tab`; `beam_file.c`, `beam_load.c`; `internal_doc/BeamAsm.md`; x86 `instr_call.cpp` | Generic file instructions, runtime specialization, loader compatibility, reductions and tail calls |
| Terms/GC | `erl_term.h`, `erl_bits.h`, `erl_map.h`, `erl_fun.h`, `erl_process.h`, selected `erl_gc.c`/`erl_message.c`; official GC/binary/map guides | [Terms, memory and GC](../concepts/beam/terms-memory-and-gc.md) |
| Schedulers/native/I/O | BeamAsm, `CheckIO.md`, NIF reference, ports/drivers guides | [Scheduling and native boundaries](../concepts/beam/scheduling-and-native-boundaries.md) |
| Processes/OTP | `ref_man_processes.md`, supervisor guide, selected `gen_server.erl` docs | [Processes, messages and OTP](../concepts/beam/processes-messages-and-otp.md) |
| Storage/distribution/upgrade | `ets.erl`, `persistent_term.erl`, distribution/TLS docs, `code.erl`, code-loading and release-handling guides | [Distribution, storage and upgrades](../concepts/beam/distribution-storage-and-upgrades.md) |
| Debugging/performance | profiling/benchmark guides, crash-dump docs, selected `erlang` BIF docs | [Inspection and performance](../concepts/beam/inspection-and-performance.md) |

**[Verified]** Current tagged documentation can contain historical examples. The memory table identifies OTP19, process allocation example identifies OTP27, GC internal links include OTP18/19, and the binary guide acknowledges an incomplete post-OTP27 representation update. Current declarations were checked where relevant; historical numbers are not reported as current measurements. A stale `kernel_passes` name/comment is not evidence of a current Kernel IR stage.

**[Unknown]** Full instruction/loader verification, all scheduler/allocator race invariants, platform-specific layouts and actual BEAML costs remain unverified. This is a substantial reference slice, not “everything about BEAM.” Pair it with [typed-language boundaries](../concepts/beam/typed-language-boundaries.md), the existing [runtime/interop overview](../concepts/beam-runtime-and-interop.md), and [specification gaps](../planning/specification-gaps.md).

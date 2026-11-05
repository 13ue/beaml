# From generated source to running BEAM code

Status: **[Verified]** selected OTP source mechanisms; **[Inference]** BEAML implications; **[Proposal]** unexecuted examples/probes. [Pinned source inventory and limits](../../sources/beam-vm-internals.md).

## The current pipeline, and an outdated name

**[Verified]** At OTP-29.1.2, `compile.erl` expands/checks Erlang forms, produces Core, runs Core transforms, lowers through `beam_core_to_ssa`, performs SSA optimizations, prepares register/code generation, validates generated assembly, runs assembly optimizations, validates again and assembles the BEAM container. `kernel_passes/0` still has a Kernel-related comment, but its dispatched pass is `core_to_ssa`. Do not reconstruct a separate Kernel stage from an old diagram or function name. [Pass definitions](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/lib/compiler/src/compile.erl#L1745-L1905).

The converter's own historical note says the earlier route used `v3_kernel` (Core to Kernel) followed by `beam_kernel_to_ssa` (Kernel to SSA); the current converter integrates translation, lambda lifting/usage/last-call handling and SSA conversion. This is a versioned change, not a claim Kernel Erlang never existed. [Current converter and historical note](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/lib/compiler/src/beam_core_to_ssa.erl#L22-L59).

```text
BEAML typed MIR                    (our future semantics, not OTP's)
  -> generated Erlang/Elixir source
  -> host frontend / Erlang forms
  -> Core -> OTP SSA -> BEAM assembly -> .beam container
  -> loader transformations -> interpreter or BeamAsm native code
```

**[Inference]** OTP's SSA is not BEAML's MIR: the latter must retain the specified type/effect/validation/security obligations before emitting host code. A later OTP pass knowing an integer range does not establish an earlier BEAML label-flow proof. Elixir's frontend is an additional layer; this is an Erlang compiler path, not a claim that every source frontend uses identical transformations.

## What must survive an SSA transformation

**[Verified]** OTP SSA represents each function as labeled blocks of assignments ending in return, branch or switch terminators. Exception behavior also has explicit structural invariants: potentially failing operations in protected blocks need edges to the landing pad; try-tag cleanup occurs on both normal and exceptional paths; re-raising follows cleanup. Non-tail calls normally have a `succeeded:body` check, with documented statically established exceptions. [Records](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/lib/compiler/src/beam_ssa.hrl); [SSA invariants](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/lib/compiler/internal_doc/beam_ssa.md).

**[Proposal]** Consider a generated validation call followed by `charge_customer`. An optimizer must not move the charge before validation or route validation failure through the success block. Model the call's success, error, exit and cancellation paths explicitly. Preserve source span, obligation ID, effect order and label on every relevant edge. Compare baseline and optimized outcomes on both valid data and failure; successful-path equality alone misses the wrong lowering.

**[Verified]** OTP's BEAM validator checks constraints whose violation could crash or confuse the emulator. It distinguishes initialized/uninitialized registers and fragile terms; GC cannot be given arbitrary garbage as a live root. Its own comments exclude ordinary user type errors that produce normal runtime exceptions from its purpose. [Validator purpose/state](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/lib/compiler/src/beam_validator.erl#L108-L205).

**[Inference]** “The BEAM validator accepted it” is neither language type safety nor information-flow assurance. BEAML needs its own semantic invariants and tests before the host compiler.

## Registers, stack and tail calls

**[Verified]** Generic instructions document X registers as value/argument locations, Y operands as stack locations, continuation handling and explicit allocation/live-root counts. `allocate` saves continuation state; `test_heap` includes a live-X count for collection; `call` records a return address; `call_only`/`call_last` implement tail calls without adding another ordinary return continuation, optionally deallocating the frame. Exact interpreter/JIT stack machinery can differ. [Generic instruction specification](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/lib/compiler/src/genop.tab#L38-L150); [BeamAsm stack transitions](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/erts/emulator/internal_doc/BeamAsm.md#running-erlang-code).

**[Proposal]** Worked frame reasoning: a function must retain `invoice_id` while it calls a decoder. That live value needs a location surviving the call; a dead prompt temporary should stop being a root. In an event loop, `loop(NewState)` in final position replaces the frame; `loop(NewState), log_done()` retains a continuation on every iteration because there is still work after the recursive call. Generated source should expose the intended tail position and avoid retaining large secrets through unnecessary live variables. These are explanatory cases, not captured disassemblies.

## Container, loader and JIT are separate contracts

**[Verified]** `genop.tab` defines file-level generic opcodes. Loader/emulator `ops.tab` defines internal specializations that can change without changing old file instruction definitions. `beam_load.c` parses the file, validates its module identity and checks opcode-version constraints before preparing loaded code. [Specialization rules](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/erts/emulator/beam/emu/ops.tab#L23-L36); [Loader](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/erts/emulator/beam/beam_load.c).

**[Verified]** BeamAsm emits native code when loading BEAM instructions, reducing dispatch overhead and specializing instruction operands. It retains the runtime's process, register, GC and scheduling machinery; it is not a general replacement with another language's optimizing native compiler. x86 `emit_return_do` decrements remaining reductions and jumps to dispatch when needed. [BeamAsm](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/erts/emulator/internal_doc/BeamAsm.md); [Return emitter](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/erts/emulator/beam/jit/x86/instr_call.cpp#L43-L75).

**[Proposal]** Preserve generated source, compiler versions and portable source maps as the first backend contract. Inspect `erlc -S` and selected SSA dumps for one pure expression, one decoder and one exception branch only after a supported toolchain is installed. Record actual emitted instructions rather than asserting this constructed explanation is an exact listing. Direct BEAM bytecode remains outside the [product contract](../product-contract.md).

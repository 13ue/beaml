# Terms, memory and garbage collection

Status: **[Verified]** selected OTP-29.1.2 implementation; **[Inference]** implications; **[Proposal]** examples/probes not executed. [Sources and historical-doc caveats](../../sources/beam-vm-internals.md).

## A value is not its printed representation

**[Verified]** `Eterm` tags distinguish immediate data, cons pointers and boxed pointers. The pinned header uses two primary tag bits and further immediate/header tags. Small integers embed in a word; larger integers use boxed signed magnitudes/digits. Atoms encode a table identity, not the atom's text. A cons cell holds head/tail, tuples have a header plus elements, boxed floats carry their numeric payload, and binary/map/function objects have their own headers. These are internal layouts, not serialized wire formats or a stable BEAML FFI memory ABI. [Tag definitions](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/erts/emulator/beam/erl_term.h).

| BEAML design question | Relevant mechanism | Consequence / proposed decision |
|---|---|---|
| `Int` overflow and numeric limits | Erlang integer representation grows beyond immediate range | Specify BEAML integer semantics and resource limits; do not silently equate every `Int` with a Rust `i64` or JSON consumer range. |
| `Decimal` and currency | Binary floating point is a different value domain | Decide an explicit decimal representation/normalization; term tags alone supply no monetary semantics. |
| Strings and bytes | Erlang character lists, binaries and bitstrings differ | Specify UTF-8 validity, normalization and byte versus grapheme operations; ordinary `binary()` does not certify UTF-8. |
| ADT/newtype witness | Atoms/tuples/maps are ordinary terms | A public constructor-shaped tuple is forgeable by foreign code; guard entry points and schema identity. |
| Collection cost | Lists are linked cells, tuples contiguous slots, maps specialized | Choose for required operations, not surface syntax familiarity; measure large nested validator workloads. |

The table's last column is **[Proposal]**, not an implemented ABI. See [typed-language boundaries](typed-language-boundaries.md).

**[Verified]** Small maps use a flat structure with a key tuple and values; larger maps use HAMT nodes. The normal-build threshold in `erl_map.h` is 32 entries, but the debug threshold is 3. Reusing literal key shapes can share key tuples; adding/removing keys can change representation. [Map layout](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/erts/emulator/beam/erl_map.h#L57-L97); [Map guide](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/system/doc/efficiency_guide/maps.md#how-maps-are-implemented).

**[Verified]** A function value can hold an environment of free variables. Local function entries and external export entries have different code identity/dispatch roles. [Function layout](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/erts/emulator/beam/erl_fun.h#L37-L105). **[Inference]** Capturing an entire request in a retry closure can retain its prompt and token even when only the request ID is needed.

## Copying collection and roots

**[Verified]** Process heap and stack share an allocated region and grow toward one another. Collection follows roots, copies reachable terms, updates references and reclaims the old allocation region. A forwarding marker prevents duplicating a shared object during one collection. Young/old generations reduce repeated scanning of longer-lived data; full collection also reclaims old-generation garbage. Heap fragments and binary references complicate a simplistic “one contiguous heap” model. [GC explanation](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/erts/emulator/internal_doc/GarbageCollection.md); [Current process fields](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/erts/emulator/beam/erl_process.h#L989-L1055).

**[Inference]** Source scope ending is not an immediate release/zeroization event. A register, stack frame, process dictionary, queue, closure, ETS row, literal or another process can still retain the value. Even later reclamation is not a memory-scrubbing contract. Representation choices and boundaries can reduce copies; they cannot make the spec's blanket erasure non-guarantee disappear.

**[Verified]** Local process messages normally copy compound data, except shared reference-counted binaries and literals. Copying can lose internal sharing. Literals may move into process heaps when their module is unloaded. [Message/literal mechanisms](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/system/doc/efficiency_guide/eff_guide_processes.md#sending-messages).

**[Proposal]** Worked ownership example: `T = {payload, LargeTree}`, then sending `{T,T}` to ten workers does not establish ten cheap pointer copies for arbitrary `LargeTree`. Model copy volume and heap roots, then compare sending the full parsed record against sending a request ID plus the minimal needed fields. Passing a binary can share payload bytes locally but extends their lifetime across all consumers. “Shared” and “already erased in the producer” cannot both be assumed.

## Binary retention and streaming

**[Verified]** Current `erl_bits.h` uses `ErlHeapBits`, `ErlSubBits` and `BinRef`; its on-heap binary limit is 64 bytes. Sub-bitstrings describe a slice/backing origin. The efficiency guide explicitly warns its older representation description has not caught up with the OTP27 rewrite; its behavioral append/match lessons should not be mistaken for today's exact structs. [Current binary definitions](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/erts/emulator/beam/erl_bits.h#L50-L168); [Guide warning](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/system/doc/efficiency_guide/binaryhandling.md#how-binaries-are-implemented).

**[Proposal]** Constructed retention example: parse a 10 MiB provider response and keep a 20-byte sub-binary in an error/stream accumulator. It can retain the large backing allocation. Copying the tiny slice at a deliberate long-lived boundary may release the backing binary sooner; blindly copying every token instead can harm throughput. The numbers illustrate the ratio, not measured allocations. Test retained bytes after completion/cancel/timeout with and without a copying boundary.

**[Verified]** Binary append optimization depends on how the accumulator is used; publication or later use of older versions can force copying. `message_queue_data` also changes whether incoming messages are allocated on the receiver heap or in fragments; `off_heap` trades allocation cost against receiver-lock/GC pressure. It does not bound the queue. [Binary append conditions](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/system/doc/efficiency_guide/binaryhandling.md#circumstances-that-force-copying); [Message allocation](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/erts/emulator/internal_doc/GarbageCollection.md#messages).

**[Proposal]** Keep stream revision/buffer ownership explicit, cap bytes as well as items, and remove terminal-operation state. Measure live process heaps, referenced binaries, ETS and OS RSS separately; one count cannot establish total memory or erasure. See [inspection/performance](inspection-and-performance.md).

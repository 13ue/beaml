# Distribution, shared storage and upgrades

Status: **[Verified]** selected OTP mechanisms; **[Proposal]** BEAML boundaries/probes. [Pinned evidence](../../sources/beam-vm-internals.md).

## Shared storage changes lifetime and ownership

**[Verified]** ETS tables belong to a process and have explicit access modes. Owner death normally destroys the table unless ownership is transferred or an heir applies. Losing all table references does not collect a table while its owner survives. Insertion/lookups copy objects; individual atomic operations are not a transaction over multiple calls, tables and external effects. Ordered-set numeric-key comparison also differs from exact-match set keys. [ETS source documentation](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/lib/stdlib/src/ets.erl#L24-L105).

**[Proposal]** Worked race: two processes read `{budget,1}`, each decides to permit a model request, then each writes `{budget,0}`. Both can charge despite individually successful table operations. Choose an atomic counter/conditional operation or a serialized owner and specify the crash point between authorization and external request. This example is explanatory, not an executed race test. Compiler-pure aggregate transitions do not establish database/ETS/distributed atomicity.

**[Verified]** `persistent_term:get` avoids normal copying/locks on reads; writes copy the key structure, and replacement/deletion of complex terms can schedule process scans and major collection/copying in processes retaining the old value. Immediate-value deletion is optimized differently. [Persistent-term mechanism and caveats](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/erts/preloaded/src/persistent_term.erl#L24-L125).

**[Inference]** It suits stable descriptors better than per-request state or rapidly changing secret policies. Deleting a credential from a shared table/global term does not erase copies already held by workers. **[Proposal]** Give descriptors immutable version identities, keep revocation checks explicit, and test update latency/old-reference retention before selecting this storage mechanism.

## Distribution is transport plus a cluster trust domain

**[Verified]** Local messages and remote messages have different paths: remote terms are encoded in external term format and decoded at the receiver. Process identifiers, links and monitors hide part of this location difference; names still need node qualification. The guide warns about unprotected distribution and documents cookies as node authentication plus TLS distribution configuration. Cookies are not application tenant authorization or payload encryption. [Distributed Erlang](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/system/doc/reference_manual/distributed.md); [TLS distribution](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/lib/ssl/doc/guides/ssl_distribution.md).

**[Proposal]** Validate schema/version/principal at every inter-node protocol boundary; do not treat an ETF-shaped tuple as a BEAML validated command. Define allowed peers, TLS certificate verification, node-cookie handling and operational access separately from type checking. A cluster observer or remote shell is privileged; an opaque pid is not a user authorization capability.

**[Verified]** Signals can be lost on distribution disconnect. Per-sender ordering is not an exactly-once guarantee. Busy distribution output buffers can suspend senders, delaying observation even of a nominal timeout. `async_dist` avoids that particular suspension but requires another flow-control mechanism to bound memory. [Delivery and blocking signaling](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/system/doc/reference_manual/ref_man_processes.md#irregularities).

**[Proposal]** Worked uncertain outcome: node A sends command R; node B performs an external action; connection breaks before reply. A's DOWN/timeout means “outcome unknown,” not “safe to repeat.” Persist/deduplicate command identity or provide an explicit reconciliation path. Keep cross-node source/schema/trace identity but independently validate principal/purpose. Monitor events cannot resolve partitions into certainty about remote side effects.

## Code replacement and ABI evolution are related but separate

**[Verified]** A module can have current and old code. Fully qualified calls target current code; local execution/closures can keep older code relevant. `soft_purge` can refuse when old code is still in use; hard purge can terminate processes relying on old code. Loading and publication have runtime code-index coordination. [Code-loading semantics](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/system/doc/reference_manual/code_loading.md); [Code API](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/lib/kernel/src/code.erl); [Code-index internals](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/erts/emulator/internal_doc/CodeLoading.md).

**[Proposal]** Do not generate an unbounded module name per prompt/schema revision: atom/code/literal retention becomes part of the design. A long-lived retry closure may retain code and data; prefer explicit stable dispatch plus a pinned operation descriptor where semantics permit. A new module interpreting an old queued command still needs old-schema compatibility or an explicit migration/rejection.

**[Verified]** SASL release handling uses application `.appup` and release `relup` instructions; dependencies and continued execution during upgrade can complicate safe ordering. `code_change` handles behavior state conversion, not arbitrary queued external messages or application-owned durable records. [Release workflow/caveats](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/system/doc/design_principles/release_handling.md).

**[Proposal]** Worked compatibility matrix: command v1 has `amount_minor`; v2 adds required `currency`. Test old sender/new receiver, new sender/old receiver, queued v1 after upgrade, retry with old schema witness, and rollback. Decide whether missing currency is a known-version default, a migration or rejection; do not infer it from the VM's ability to load new code. Distinguish source/API version, schema/event version, policy/manifest version, compiler ABI version and application release. A first release may choose restart-based deployment rather than hot upgrade; neither choice has been made or tested here.

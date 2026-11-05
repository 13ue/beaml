# Processes, messages and OTP lifecycle

Status: **[Verified]** OTP semantics at the pinned sources; **[Proposal]** worked protocol cases, not executed traces. [Evidence inventory](../../sources/beam-vm-internals.md).

## Signal delivery is not receive selection

**[Verified]** Runtime signals arrive asynchronously, independently of when the process executes `receive`. A message signal normally adds a term to a queue; a later receive selects a matching message. The only language ordering guarantee is for signals from one entity to the same destination: later signals do not overtake earlier surviving signals. It does not order different senders or prove distributed delivery. [Signals/delivery](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/system/doc/reference_manual/ref_man_processes.md#delivery-of-signals).

**[Verified]** OTP28 introduced opt-in priority reception. Priority and ordinary messages maintain order within their classes but priority insertion can place a later same-sender message ahead of an earlier ordinary one. This changes mailbox order without violating signal-delivery order. Blanket “mailboxes are FIFO” is therefore too strong. [Queue insertion/priority semantics](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/system/doc/reference_manual/ref_man_processes.md#adding-messages-to-the-message-queue).

**[Proposal]** Worked queue case: ordinary `{chunk,1}`, ordinary `{chunk,2}`, then an accepted priority cancellation. The cancellation can be selected first; already admitted data still needs explicit discard/cleanup. Another consumer without priority reception sees different queue behavior. BEAML must define terminal-state precedence without relying on an assumed universal FIFO.

**[Verified]** Selective receive may scan queued unmatched messages. A recognized fresh-reference request/reply pattern can mark the queue position and avoid searching older messages. All relevant clauses must satisfy the optimization's conditions; generated code can request `recv_opt_info` for evidence. [Receive optimization](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/system/doc/efficiency_guide/eff_guide_processes.md#fetching-received-messages).

**[Proposal]** If a process has 50,000 unrelated notifications, waiting for `{RequestRef,Reply}` without a recognized fresh-ref pattern can repeatedly scan them. Separate unrelated responsibilities or use the documented request pattern, then inspect the actual compiler report. Do not claim an optimization from similar-looking source alone.

## Replies, aliases, timeouts and cancellation

**[Verified]** A process alias can identify a reply destination. Deactivation drops later alias-addressed arrivals before queue insertion, but does not remove messages already queued, deactivate someone else's alias, or stop the server's work. [Aliases](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/system/doc/reference_manual/ref_man_processes.md#process-aliases).

**[Proposal]** Constructed timeline:

```text
t0 caller starts request R, holds monitor/alias A
t1 provider accepts request and may begin charging
t2 caller deadline expires, deactivates A, asks adapter to cancel
t3 worker finishes, attempts reply via A (may now be discarded)
```

The timeout means the caller stopped accepting a result, not that the provider did nothing. If reply entered the queue before t2, alias deactivation alone does not drain it. Track `R`, terminal state and cleanup acknowledgment; decide whether a late successful effect requires compensation. Request identity and idempotency are distinct from pid identity. A process restart creates another lifetime even when the registered name is unchanged.

## Links, monitors and exceptions answer different questions

**[Verified]** Links are bidirectional failure relationships. Monitors report the observed entity's termination/disconnection through a reference-specific DOWN message without creating the same bidirectional fate relationship. Exit signals can terminate, be ignored, or become messages depending on reason/state; untrappable kill behavior differs from ordinary trapped exits. A distributed monitor losing connectivity cannot prove the remote process no longer exists. [Links/monitors and exit handling](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/system/doc/reference_manual/ref_man_processes.md#links).

**[Inference]** Returning `{:error,invalid_input}` is an API result; raising is a language exception; process exit is a lifetime outcome; DOWN is an observer message. Treating all four as the same error loses ownership and retry semantics. Native crashes remain outside ordinary exception containment; see [native boundaries](scheduling-and-native-boundaries.md).

## Supervisors restore processes, not transactions

**[Verified]** Supervisors start children in specification order and stop them in reverse. Strategies restart the failed child, all children, or the failed child plus those after it in start order. Child restart type and exit reason affect whether restart occurs; intensity/period can terminate a repeatedly failing supervisor. Shutdown policy can allow graceful termination, time out into forced death, or kill directly. [Supervisor principles](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/system/doc/design_principles/sup_princ.md).

**[Proposal]** Suppose A is a connection owner and B a stream parser requiring A. `rest_for_one` with A before B can restore the dependency ordering; it cannot undo a payment/model call completed before the crash. A temporary request task should not become an automatic charge replay merely because a permanent child specification was convenient. Record state reconstruction and replay/idempotency rules separately from restart strategy.

**[Verified]** A GenServer serializes its callbacks and integrates system behavior, state changes and termination/status hooks. `terminate` is not guaranteed on every death path. Hot state conversion uses `code_change`; diagnostic status formatting is another explicit hook. [GenServer documentation in source](https://github.com/erlang/otp/blob/d199a49a01a2079afb6f2c5c9ae047cd4555e68d/lib/stdlib/src/gen_server.erl).

**[Proposal]** Keep long provider waits out of the coordinating callback when it must remain responsive; use a monitored child/request protocol, process results/DOWN without blocking ordinary messages, and clean up owned transport state on all supported terminal paths. Test normal result, validation error, thrown exception, server exit, owner exit, deadline and reconnect separately. A typestate transition must reflect actual protocol evidence, not simply the fact that a supervisor exists.

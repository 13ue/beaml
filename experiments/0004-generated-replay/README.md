---
id: experiment-0004-generated-replay-plan
kind: experiment
status: proposed
updated: 2026-11-06
revision: 7.1 (slice 3 plan repair)
---

# EXPERIMENT 0004 — Generated REPLAY RUN

**[Requirement]** Can the BEAML compiler generate the flow, the HTTP EFFECT, the decode, the CAPTURE and the REPLAY RUN runner from one BEAML source, so that the host writes no replay code and no transport? Does the generated arm do more than a shared Elixir replay library with a hand-written descriptor? The section [Owner decisions (2026-11-06)](#owner-decisions-2026-11-06) is the authority. It overrides older plan text.

**[Verified]** [EXPERIMENT 0003](../0003-source-linked-replay/README.md#gate-status) passed with a hand-written runner, [`OrdersApi.Replay.run/3`](../0002-http-correlation/apps/orders_api/lib/orders_api/replay.ex), and a hand-written CAPTURE, `capture/3` in [`payment_http.ex`](../0002-http-correlation/apps/orders_api/lib/orders_api/payment_http.ex). The host [router](../0002-http-correlation/apps/orders_api/lib/orders_api/router.ex) owns the order prepare → `authorize/2` → finish. The [0001 compiler](../0001-syntax-to-beam/src/main.rs) parses `interface`, `enum` and `fn` only. Its interfaces are structural and exact.

**[Verified]** The 0003 live tests check the 0002 trace contract in [`query.py`](../0002-http-correlation/query.py): spans `orders.request`, `orders.prepare`, `orders.payment_http`, `orders.finish` and the log `payment_request_prepared`. `ProbeSupport.span/5` sets `outcome: "error"` only when the wrapped function raises.

**[Proposal]** Hypothesis: with the flow, the EFFECT and its failure type in BEAML, a BEAML-only TYPE change (DRIFT) needs fewer manual change sites in the generated arm (GEN) than in the library arm (LIB). GEN also catches a DRIFT that LIB misses.

## Plan history

- **Revision 1.** Generated runner next to a host flow. Plan review: BLOCK (1 critical, 2 high). [plan-review.md](workflow/2026-11-06/plan-review.md)
- **Revision 2.** LIB arm first as a kill switch, typed record fields, DRIFT R/N/Q, pass and reject rule, three syntax options (A, B, C) with owner questions Q1–Q5.
- **Revision 3.** The owner chose option B with `effect`, `!` and `|>`, a generated decode, no kill switch and LIB in parallel. Q1, Q2 and Q5 are answered. Syntax options A and C are closed; [syntax-options.beaml](syntax-options.beaml) stays as history. Use git history for the full revision 2 text. Plan review: BLOCK (1 critical, 2 high).
- **Revision 4.** Repairs the three objections of the revision 3 review: one strongest LIB form, frozen before any GEN result is judged; a complete 0003 change table, checked by a diff test on test copies; asserted TYPE mismatch cases, live and in a REPLAY RUN. [Disposition](workflow/2026-11-06/plan-review.md#disposition-main-agent-2026-11-06-1).
- **Revision 5.** Adds the [slice 1 verdict](#slice-1-verdict-2026-11-06) and the [slice 2 plan](#slice-2). Slice 1 text above stays unchanged. The slice 1 pass and reject rule does not apply to slice 2.
- **Revision 6.** Applies the OWNER answers O1–O4 to [slice 2](#slice-2): a MIGRATE CHAIN replaces the RENAME ALIAS options S1, S2 and S3; the record carries the TYPE version number; the build fails only when a stored TYPE VERSION has no path through the chain; C5 (DRIFT R without a chain) is now a compile error. Only the slice 2 section changes.
- **Revision 7.** Adds the [slice 3 plan](#slice-3): `add` with a constant and `drop` with a TYPE in the MIGRATE CHAIN (DL-042). The slice 1 and slice 2 text stays unchanged.
- **Revision 7.1 (this page).** Repairs the slice 3 plan after its fresh check: the `add` constant always wins in a REPLAY RUN (DL-048, D8, new D11b); K checks run before the EFFECT output check, so K2 and K4 are reachable; `drop` takes `String` only (K6, D7, D5c); new help cases D2b and D5b; `unknown_keys == []` stated for D11 and D14. Only the slice 3 section changes.

## Slice 1 scope

- **In [Requirement].** `effect` declarations with `http.post`. One `!` failure type. Pipe `|>` that passes a failure on, with the compile check against the `!` list. A decode generated from the declared TYPE. A generated `record` (CAPTURE) and a generated REPLAY RUN runner. The flow `place` in BEAML. The router calls only generated code.
- **Later [Requirement] (slice 2+).** `with ... else`, the Elixir `name`/`name!` pair, the formatter alignment rule, other EFFECT kinds (db, queue, mail), a second EFFECT, the old-record policy (Q4), the artifact check in the runner (Q3).

```mermaid
flowchart LR
  subgraph GEN["Arm GEN"]
    S["BEAML · orders.beaml: effect, prepare, finish, place"] --> C["BEAML · compiler, one invocation"]
    C --> P["BEAML · generated place, prepare, finish"]
    C --> T["BEAML · generated HTTP EFFECT and typed decode"]
    C --> R["BEAML · generated Replay.record and Replay.run"]
  end
  subgraph LIB["Arm LIB (comparison)"]
    LH["Host · 0002 router, transport, :json.decode"] --> LL["Host · ReplayLib (whole values, typed rescue) + descriptor"]
  end
  H["Host · router: validate order, call place, validate payment, reply"] --> P
  P --> T --> R
  R --> ST["Host · ProbeSupport: spans, counter, CAPTURE store"]
  LL --> ST
  X["Host · test harness: 0003 test copies, 8 cases, TYPE mismatch cases, DRIFT per arm"] --> R
  X --> LL
```

## Slice 1 BEAML source (orders)

**[Proposal]** The fixture `orders.beaml` for GEN. The syntax follows the owner example [order-flow.beaml](examples/order-flow.beaml). `payments.beaml` stays unchanged.

```beaml
interface Order { order_id: String }
interface Payment { order_id: String status: String }
interface PaymentError { reason: String }

// Leaves the module. Recorded live, substituted in a REPLAY RUN.
effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize")

fn prepare Order { order_id } -> Order = Order { order_id: order_id + "" }
fn finish Payment { order_id, status } -> Payment = Payment { order_id: order_id + "", status: status }

// The flow lives in BEAML. A failed step stops the pipe and passes PaymentError on.
fn place order: Order -> Payment ! PaymentError =
  order
  |> prepare
  |> payments.authorize
  |> finish
```

**[Proposal]** Generated Elixir, in the one module that 0002 `run.py` renames to `OrdersBeamlSpike`:

- `prepare/1`, `finish/1` as today. `place/1` returns `{:ok, payment}` or `{:error, %OrdersBeamlSpike.PaymentError{reason: r}}`. The `place!/1` half of the pair is slice 2.
- `payments_authorize/1`: the HTTP EFFECT. POST to `/payments/authorize` on `127.0.0.1` and the port from `ProbeSupport.config(:payments_port)`. Trace context injection, `ProbeSupport.increment/0`, Content-Length framing as in 0002. Then `Replay.record/3` with the actual status (revision 4: the record comes before the status check). Then status 200 only, then the typed decode.
- Typed decode of `Payment`: `:json.decode/1`, then an exact key set with String values. A missing key or a non-String value gives `reason: "decode"`. An extra key is accepted and recorded as `unknown_keys` (owner decision: tolerant with a hint). Transport failure gives `reason: "transport"`, another status gives `reason: "status"`.
- Spans through `ProbeSupport.span/5`: `orders.prepare`, `orders.payments.authorize` (client), `orders.finish`. A failure raises inside the span and becomes `{:error, ...}` outside it, so `outcome: "error"` stays. A failed step stops the pipe: no later step and no later span runs.
- One Orders log, revision 4 [Proposal]: inside the span of the pure step directly before an EFFECT, the generated code calls `ProbeSupport.event("<output TYPE, lower case>_request_prepared", "<step>")`. For `place` this is the existing `payment_request_prepared` under `orders.prepare`. So the 0002 `LOGS` contract and the log counts stay unchanged.
- `Replay.record/3` writes the 0003 RESPONSE RECORD format version 1 to `ProbeSupport.Capture.write/2`. `Replay.run/3` takes `(order, trace_id, records)` and returns only `{:ok, payment}` or `{:error, reason}`; the `unknown_keys` hint goes to the replay EFFECT span and the replay report, not to the return value. It runs `place` with the EFFECT step replaced by the record checks, then the same typed decode and `finish`. It returns `{:ok, payment}`, one of the six 0003 atoms, or `{:error, %PaymentError{}}`.

## Fixed inputs and ownership

- **LANGUAGE/COMPILATION.** The 0001 compiler gets `effect`, `!`, `|>` and the emit above. One invocation, one stdout. `payments.beaml` output stays byte-identical.
- **EXECUTION.** Reuse the two 0002 releases, the ports, the HTTP path, RESPONSE RECORD format version 1 and `ProbeSupport` (unchanged SHA-256). The router keeps `orders.request`, `valid_order!/1`, `valid_payment!/2` and the reply. It calls `OrdersBeamlSpike.place/1` and nothing else of the flow.
- **EXECUTION.** Each arm is an overlay, applied by `0004/run.py` to a temporary tree with the repository layout: `experiments/0001-syntax-to-beam` (current compiler), `experiments/0002-http-correlation` (copy plus overlay) and `experiments/0003-source-linked-replay` (`run.py` and copies of `tests/*.py`). The path constants of the copies (`EXPERIMENT`, `REPO`, `HTTP`, `COMPILER`) then need no edit. The overlay holds the edited copies of `query.py` and the 0003 tests. `0003/run.py` runs unchanged in that tree.
- **EXECUTION, control.** The 0002 tree, `0003/run.py` and the original 0003 tests stay unchanged in the repository. They run at their default root as the control. An arm run does not change their SHA-256 values.
- **R&D process.** Follow [implement-step](../../skills/implement-step/SKILL.md). Devil's Advocate at the plan, the RED review and the final review, in the gate ledger only.

## Comparison arm LIB

**[Requirement]** No kill switch. LIB is built in parallel with GEN, as the comparison.

**[Proposal] Revision 4: LIB is the strongest fair library.** The plan fixes its form. The LIB worker does not choose a weaker form.

- **Descriptor.** One Elixir map per EFFECT: operation, attempt, expected status, request function (`&OrdersBeamlSpike.prepare/1`), decode function, finish function. No request or response key list, no field name, no other TYPE fact. Budget: about 10 lines.
- **Whole values.** `ReplayLib.record(descriptor, request, status, bytes)` records the whole request value and the whole body bytes. `run` compares the whole recorded request with the request function result (`request_mismatch`), as 0003 does.
- **Typed rescue (mandatory).** `ReplayLib.run(descriptor, order, trace_id, records)` wraps decode and finish in one `rescue`. It returns `{:error, %ReplayLib.Error{step: "decode" | "finish", reason: <exception module name>}}`, never a raise. The six 0003 atoms and their check order stay. Budget: maximum 60 lines.
- **Live path.** The 0002 router, transport and `payment_request_prepared` log stay. The CAPTURE body in `payment_http.ex` becomes one `ReplayLib.record` call. `replay.ex` is deleted.
- **Fairness.** A fresh worker writes LIB without access to the GEN emitter, the 0004 BEAML fixture or any GEN result. LIB may call the public generated `prepare` and `finish`. It may not read BEAML source or metadata that 0004 adds to the generated module.
- **Freeze.** LIB passes (e) before any GEN result of (d2) or (f) is judged. `0004/run.py` records the SHA-256 of `replay_lib.ex` and the descriptor. DRIFT (f) runs only against that frozen LIB. A repair of LIB after the freeze counts as manual change sites.
- **No weak form.** The plan builds no LIB with a key list or without the `rescue`. The pass and reject rule uses only this LIB.
- **[Inference]** This LIB has no stale descriptor. It probably gives a typed reject for an old record after DRIFT-R and DRIFT-N, and `request_mismatch` after DRIFT-Q. Then the reject rule may apply. That is a valid result of slice 1.

## Slice 1: acceptance cases in order

1. **(a) Parse and check.** The compiler accepts the slice 1 source above, exit 0. Each bad declaration fails with exit ≠ 0, a clear message and no stdout:
   - unknown fn in a pipe (`|> charge`);
   - TYPE mismatch in a pipe (`|> finish` directly after `|> prepare`: `Order` is not `Payment`);
   - undeclared failure in a pipe (`place` without `! PaymentError`); the message names the step `payments.authorize` and the type `PaymentError`;
   - field not in TYPE (`finish` reads `amount`, which `Payment` does not have);
   - unsupported EFFECT kind (`db.get`) in slice 1.
2. **(b) Emit.** One compiler run writes the Elixir module with `place/1`, `payments_authorize/1`, the typed decode, `Replay.record/3` and `Replay.run/3`, the `PaymentError` struct and one `beaml-declaration-v1` comment per declaration. The module compiles with warnings as errors. Template control: compile DRIFT-R; the generated decode must contain `reference`. The 0003 gate 1 test `payments_cli_emits_checked_authorize_reference` still passes.
3. **(c) Live.** The GEN router calls only `OrdersBeamlSpike.place/1`. `payment_http.ex` and `replay.ex` are deleted. `0003/run.py` passes in the GEN tree, all five default steps (compiler reference, trace lookup, trace lookup repair, response capture, replay run). The test `tests/overlay_diff_test.py` passes first: per arm, the line diff of each copy against its original equals `arms/<arm>/assertion-changes.json`, which equals the table below. No other line changes.
4. **(d) Replay.** The 0003 8-case matrix passes against `OrdersBeamlSpike.Replay.run/3`: valid, A1 non-canonical, missing, operation, attempt, request, status, digest. Expected values stay as in 0003. Router, transport and `:gen_tcp.connect/4` count zero in all 8 cases. Live and replay use the same generated decode.
5. **(d2) TYPE mismatch, live and in a REPLAY RUN [Requirement].** In `tests/arms_test.py`, not in the 0003 copies. Replay cases use the 0003 harness with the arm's runner. Live cases use one Orders release against the 0003 loopback stub (`http.server`, Content-Length framing). Cases R1, R2, L1, L2, P1 below.
6. **(e) LIB.** The LIB form above passes the same 8 cases with the same counts, in the LIB tree, with the LIB rows of the table only. Before the freeze, LIB R1 must return `%ReplayLib.Error{step, reason}` with step "decode" or "finish" (asserted). It then runs R2, L1, L2, L3; those outcomes are recorded, not asserted. Then the freeze.
7. **(f) DRIFT.** Starts after the freeze. Per arm, change only BEAML TYPES or signatures; do not touch the LIB descriptor or host replay code. Regenerate and rebuild. Derivatives:
   - **DRIFT-R.** Add `reference: String` to `Payment` in both BEAML files.
   - **DRIFT-N.** Rename the `Payment` field `status` to `state` in both BEAML files.
   - **DRIFT-Q.** Add a field with a literal value to the request TYPE that `prepare` returns, and the matching Payments input.
   For each derivative and arm, record the outcome at build, on a new live record and on the pre-change record. Outcome classes: compile error with a clear message, typed reject, correct accept, false reject, wrong accept, crash without a typed reason. Then repair each arm until (d) or (e) passes again. Count manual change sites per arm.

### Case (d2): TYPE mismatch cases

**[Proposal]** Each case asserts the result, the counts and, live, the spans and records. "finish 0" is the runtime half of the pipe rule: a failed step stops the pipe.

- **R1 Replay, missing key.** Record of the first live call with body `{"order_id":"order-1"}`, `body_length` and `body_sha256` recomputed, status 200. Expect `{:error, %OrdersBeamlSpike.PaymentError{reason: "decode"}}`, `:json.decode/1` 1, `finish/1` 0, `valid_payment!/2` 0, transport 0.
- **R2 Replay, extra key.** The RESPONSE RECORD from L1. Expect the same success as L1 and the same `unknown_keys` hint. Live and replay use the same decode.
- **R3 Replay, wrong field TYPE.** A declared field with the wrong TYPE (`status: 7`). Expect `PaymentError` with reason "decode" and zero `finish` calls.
- **L3 Live, missing key.** The stub returns 200 with a body without `status`. Expect HTTP 502 `downstream_failure`, span `orders.payments.authorize` with `outcome: "error"` and `reason: "decode"`, one RESPONSE RECORD byte-exact, zero `orders.finish`, transport count 1.
- **L1 Live, extra key [Requirement: accept with hint].** The stub returns 200 with an extra key `fraud_score`. Expect HTTP 200, one `orders.finish`, one RESPONSE RECORD with the bytes byte-exact and `unknown_keys == ["fraud_score"]`, and the same attribute on the `orders.payments.authorize` span.
- **L2 Live, status 503.** The stub returns 503 with a valid `Payment` body. Expect HTTP 502, client span `outcome: "error"`, one RESPONSE RECORD with status 503, no `orders.finish` span, transport count 1.
- **P1 Pipe stop.** In an eval VM (0003 harness), `OrdersBeamlSpike.place/1` with a refused port. Expect `{:error, %OrdersBeamlSpike.PaymentError{reason: "transport"}}`, `prepare/1` 1, `finish/1` 0.

**[Unknown]** A recorded live 503 replays as the 0003 `status_mismatch` atom, not as `PaymentError{reason: "status"}`. The 0003 matrix keeps this. Slice 2 can revisit it with D001.

### 0003 lines that change in the arm copies

**[Proposal]** Each GEN change follows from "the router calls only generated code". The copies live in the overlay; the originals stay the control. `overlay_diff_test.py` compares each copy line by line with its original and requires the result to equal this table. Line numbers refer to the original files at the plan commit.

| Arm | File | Line | Original | Copy | Reason |
| --- | --- | --- | --- | --- | --- |
| GEN | 0002 `query.py` | 12 | `CONTRACT` key `orders.payment_http` | `orders.payments.authorize` | Generated span name `<service>.<step>` |
| GEN | 0002 `query.py` | 13 | parent of `payments.request`: `orders.payment_http` | `orders.payments.authorize` | Same rename |
| GEN | 0003 `response_capture_test.py` | 175 | client span filter `orders.payment_http` | `orders.payments.authorize` | Same rename |
| GEN | 0003 `response_capture_test.py` | 213 | observer control span `orders.payment_http` (twice) | `orders.payments.authorize` | Same rename; `outcome: "error"` stays |
| GEN | 0003 `replay_run_test.py` | 32 | `WATCHED` key `OrdersApi.PaymentHttp.authorize/2` | `OrdersBeamlSpike.payments_authorize/1` | The transport is generated |
| GEN | 0003 `replay_run_test.py` | 48 | `HARNESS` watched `{OrdersApi.PaymentHttp, :authorize, 2}` | `{OrdersBeamlSpike, :payments_authorize, 1}` | Same |
| GEN | 0003 `replay_run_test.py` | 56 | `HARNESS` control `OrdersApi.PaymentHttp.authorize(prepare(order), [])` | `OrdersBeamlSpike.payments_authorize(prepare(order))` | Same |
| GEN | 0003 `replay_run_test.py` | 57 | `HARNESS` replay `OrdersApi.Replay.run(order, trace_id, responses)` | `with {:ok, p} <- OrdersBeamlSpike.Replay.run(ProbeSupport.valid_order!(order), ...), do: {:ok, ProbeSupport.valid_payment!(p, order)}` | Domain validation stays host code, as in the router |
| GEN | 0003 `replay_run_test.py` | 292 | control result `{"raised": "MatchError"}` | `{"error": "%OrdersBeamlSpike.PaymentError{reason: \"transport\"}"}` | The EFFECT returns a typed failure; counts stay |
| GEN | 0003 `replay_run_test.py` | 293 | control key `OrdersApi.PaymentHttp.authorize/2` | `OrdersBeamlSpike.payments_authorize/1` | Same as line 32 |
| GEN | 0003 `replay_run_test.py` | 301 | `isolated` key `OrdersApi.PaymentHttp.authorize/2` | `OrdersBeamlSpike.payments_authorize/1` | Same as line 32 |
| GEN | 0003 `replay_run_test.py` | 141 | compiler call `"--", archived]` | `"--", archived, "--stored", <copy dir>/stored-empty.jsonl]` | Slice 2 (C10): a source with an `effect` needs a RECORD SNAPSHOT; the copy passes the empty one |
| GEN | 0003 `response_capture_test.py` | 92 | compiler call `"--", archived]` | `"--", archived, "--stored", <copy dir>/stored-empty.jsonl]` | Same as `replay_run_test.py` line 141 |
| GEN | 0003 `trace_lookup_test.py` | 51 | compiler call `"--", source]` | `"--", source, "--stored", <copy dir>/stored-empty.jsonl]` | Same as `replay_run_test.py` line 141 |
| LIB | 0003 `replay_run_test.py` | 57 | `HARNESS` replay `OrdersApi.Replay.run(order, trace_id, responses)` | `with {:ok, p} <- ReplayLib.run(OrdersApi.ReplayDescriptor.authorize(), ProbeSupport.valid_order!(order), ...), do: {:ok, ProbeSupport.valid_payment!(p, order)}` | `replay.ex` is deleted; same host validation as GEN |

**[Proposal]** Unchanged in both arms, because the Orders log stays (line text **[Verified]** at the plan commit): `query.py` line 17 (`LOGS`), `trace_lookup_test.py` line 175 (`len(checked["logs"]) == 2 * call`) and line 184 (`"logs": 4`). `trace_lookup_repair_test.py` and `run_test.py` have no changed line. The comment lines 38–39 of `replay_run_test.py` stay as history.

**[Inference]** If GEN cannot emit the log, lines 17, 175 and 184 change. That is a table change: it needs a new plan revision, and the verdict records "no Orders log" as a lost check.

All counts in the 8-case matrix stay as in 0003. The revision 2 SHA-256 check of `router.ex` is removed: the router changes by owner decision.

### Replay lines and manual change sites

- **Replay line.** A host line that exists only for replay: CAPTURE, the `record` call, hook wiring, the runner call site, caller-side validation or artifact checks, the LIB descriptor and library. Count them in both arms. Generated and compiler lines are not host lines; report compiler size as a one-time cost.
- **Manual change site.** One contiguous edited hunk in a hand-written file that an arm needs to pass (d) or (e) after a DRIFT. Exclude the BEAML DRIFT edit. Count domain validation edits (`valid_payment!/2`) and test expectation edits apart; they are equal in both arms.

### Pass and reject rule

- **Comparison arm [Proposal].** Judge every clause below only against the frozen LIB of [Comparison arm LIB](#comparison-arm-lib). No other LIB form enters the verdict.
- **Pass [Proposal].** The language claim holds for slice 1 only if both are true: (1) summed over the DRIFT derivatives, GEN needs fewer manual change sites than LIB; (2) for at least one derivative, GEN gives a compile error, a typed reject or a correct accept, while LIB gives a wrong accept or a crash without a typed reason. GEN has no wrong accept in any derivative.
- **Reject [Proposal].** Reject the claim for this slice if LIB needs the same number or fewer manual change sites, if LIB misses no DRIFT that GEN catches, or if GEN gives a wrong accept. Record the reject in the register.
- **Miss [Requirement].** A crash without a typed reason counts as a missed DRIFT (owner decision).
- **No verdict.** If GEN fails (a)–(d2), or LIB fails (e) or is not frozen before (f), slice 1 fails as an implementation and gives no verdict on the claim.

## Decisions (Decision4)

| Decision | Class | Choice and reason |
| --- | --- | --- |
| Failure TYPE as an interface `PaymentError { reason: String }` with the values `transport`, `status`, `decode` | Repair | The smallest typed struct with a named field. No enum payload rules needed. Q6 can replace it |
| `place/1` returns `{:ok, v}` or `{:error, struct}` only | Repair | It is the `name/n` half of the owner pair; `name!/n` is slice 2 and adds, not changes |
| Generated span names `<service>.<step>` | Repair | Derived, not a literal from 0002. Commits us to the listed assertion changes |
| Keep `payment_request_prepared`: emit `<output TYPE>_request_prepared` in the span of the pure step before an EFFECT (revision 4) | Undo | A local emit rule with no new syntax. Keeps the 0002 `LOGS` contract and the log counts. A BEAML log statement can replace it later |
| Generated code calls `ProbeSupport` for spans, counter, config and CAPTURE store | Repair | The existing 0002 adapter, unchanged. A language runtime contract replaces it later |
| Target from `<namespace>_port` config, host `127.0.0.1` | Repair | Matches 0002 configuration. Real addressing waits for Q7 |
| Transport with `:gen_tcp` and 0002 framing | Repair | Keeps the `:gen_tcp.connect/4` and transport counters of the 0003 observer |
| Host keeps `valid_order!/1` and `valid_payment!/2`; harness calls them around `Replay.run/3` | Repair | Domain validation is host code; keeps the 0003 counts |
| Replay evidence errors stay the six 0003 atoms; flow failures are `PaymentError` | Repair | Keeps the 0003 matrix unchanged. Revisit with D001 |
| Copies of the 0003 tests and `query.py` in the overlay, in a temporary tree with the repository layout; diff checked against the table (revision 4) | Undo | Originals stay the control; no arm switch in the 0003 files; no path edits in the copies |
| Typed decode accepts an extra key and records it as a hint (owner decision, replaces revision 4 reject) | Requirement | Matches the exact 0001 interfaces and the generated `finish` pattern. Relaxing it later is one emit change |
| `Replay.record/3` before the status check; the record holds the actual status (revision 4) | Repair | Case L2 needs one record for a 503. The 0003 matrix still expects status 200 in a valid record |
| LIB form fixed: no key list, mandatory typed `rescue`, frozen before (d2) and (f) are judged; no weak LIB (revision 4) | Repair | The verdict must not depend on a free choice of the LIB worker |
| LIB error shape `%ReplayLib.Error{step, reason}` (revision 4) | Undo | Local to the LIB arm; any typed shape counts |
| Elixir name `payments_authorize/1`, nested `Replay` and `PaymentError` modules | Undo | Local naming inside one generated module |
| Reject non-`http` EFFECT kinds at compile time in slice 1 | Undo | Keeps the slice boundary visible; slice 2 removes the reject |
| LIB worker runs in parallel with GEN, in its own directory; tests serialized | Undo | Owner decision overrides the one-writer rule; no shared build output |
| `http.post("payments/authorize")` as the slice 1 call form | Migrate | Taken from the owner example; source files depend on it. Q7 confirms |

**[Verified]** No decision is Answer: 0004 publishes nothing and makes no external claim.

### Owner questions

- **Q1, Q2, Q5.** Answered by the owner decisions: option B with `effect` and `|>`; BEAML owns the decode; a crash without a typed reason is a miss.
- **Q3. Artifact check (slice 2).** (i) The generated runner rejects a record with another `artifact_id` (`artifact_mismatch`). (ii) The caller keeps the check; it counts as replay lines. Slice 1 uses (ii). Depends on [D002](../../wiki/planning/decisions-to-be-made.md#d002--scope-of-the-replay-artifact-identity).
- **Q4. Old record after a SCHEMA change (slice 2).** (i) Typed reject from a SCHEMA version in the record. (ii) Typed reject from `artifact_id` (needs Q3 (i)). (iii) The generated decode rejects it with `PaymentError` (slice 1 behavior).
- **Q6. Shape of an EFFECT failure TYPE (Migrate, before slice 2).** (i) User-declared interface with `reason: String` (slice 1 default). (ii) User-declared `enum` with fixed variant names per EFFECT kind, for example `Transport`, `Status`, `Decode`. (iii) A built-in `HttpError` TYPE that the user names after `!`.
- **Q7. HTTP call form and target (Migrate, before slice 2).** (i) `http.post("payments/authorize")` with the target from configuration by namespace (slice 1 default). (ii) A named target declaration in BEAML, for example `target payments = env("PAYMENTS_URL")`. (iii) Another form from the owner.

## Evidence and limits

**[Unknown]** No run exists. This page is a plan.

**[Inference]** DRIFT-R and DRIFT-N need a `valid_payment!/2` edit in both arms. It counts apart, not as a replay site.

**[Unknown]** Limits carried from 0003: the body digest is integrity, not tamper protection (R2). The RESPONSE RECORD has no timestamp (D003). The check order of the six reasons is not tested. Two records for one trace give `missing_response` without a test.

**[Unknown]** One EFFECT and three DRIFT derivatives are a small sample. A pass shows an advantage for this slice only.

**[Inference]** An extra key is accepted with a hint, so a Payments service may add a field without breaking Orders. The hint makes such a change visible to observation.

**[Unknown]** Revision 4: the generated client span and `Replay.record/3` in an eval VM without the OpenTelemetry application (case P1 and the observer control) are not tested yet. RED shows whether the harness needs a change; such a change is a table change.

### Out of scope

- Everything in "Later" above.
- Retries, attempts > 1, timeouts, uncertain outcomes (round 3, objection 3).
- A REPLAY CAPSULE format, durable storage, trace sampling (D003).
- Zed/LSP support for the new syntax.
- A BAML comparison and the operator-time value gate. [BAML v1](../../wiki/sources/baml-v1.md#observability) has no replay on its default branch at the pin.

**[Proposal]** Smallest next test after slice 1: a second EFFECT in both arms, with change sites counted the same way.

## Owner decisions (2026-11-06)

- **[Requirement]** BEAML owns the call order. Syntax option B: the flow `place` is written in BEAML. The host router only calls generated code.
- **[Requirement]** BEAML makes the HTTP call itself. No hand-written host transport.
- **[Requirement]** BEAML generates the response decode from the declared type. A response that does not match the type gives a typed error, live and in a REPLAY RUN.
- **[Requirement]** In the comparison, a runtime crash without a typed reason counts as a missed DRIFT.
- **[Requirement]** No kill switch. Start the generated arm directly. Build the library arm in parallel as the comparison.
- **[Requirement]** Long-term direction: applications are written in BEAML. Only a pure interface layer (for example LiveView) stays in Elixir and uses generated event handlers.
- **[Proposal]** Main agent: the generated HTTP code may use a socket or an HTTP library inside. The 0003 live tests run again against the changed router.
- **[Unknown]** Open: the BEAML syntax of the HTTP call itself.
- **[Requirement]** BEAML has a pipe operator `|>`. The flow `place` uses it instead of nested calls.
- **[Requirement]** Formatter rule: consecutive `effect` lines (no blank line between them) align three columns: the input type after the longest name, `->` after the longest input type, `=` after the longest output type. A blank line starts a new block.
- **[Proposal]** `effect` marks every call that leaves the function: HTTP, other apps (also over BEAM messages), database, queue, file, time, randomness. Every `effect` result is recorded; a REPLAY RUN substitutes it. The keyword name is still open.
- **[Requirement]** BEAML allows `with ... do ... else ... end`. `<-` binds the success value of a step that can fail; `=` binds a pure step.
- **[Requirement]** An `effect` or `fn` declares its failure type with `!` after the success type, for example `String -> Order ! LoadError`. `<-` binds only the success type. A failure goes to `else`.
- **[Requirement]** The compiler collects the failure types of all `<-` steps. The `else` branch must cover each of them, or compilation fails.
- **[Requirement]** A function may pass failures on with `!` in its own signature, for example `-> Payment ! LoadError | StockError | PaymentError`.
- **[Requirement]** A pipe step may fail. The pipe stops and passes the failure on. The compiler rejects a pipe step whose failure type is not in the `!` list of the enclosing function, with a message that names the step and the missing type.
- **[Requirement]** `!` in a type stays, although Elixir uses `!` in names for "raises". The owner accepts this.
- **[Requirement]** For each BEAML function that can fail, the Elixir output has two functions: `name/n` returns `{:ok, value}` or `{:error, error}`; `name!/n` returns the value or raises an exception generated from the failure type.
- **[Requirement]** Generated Elixir errors are typed structs with named fields, for example `%Orders.LoadError.NotFound{id: "order-1"}`. Not plain tuples.
- **[Requirement]** Generated decode is tolerant with a hint, as in BAML v1 (`ExtraKey` flag in `coerce_class.rs` at pin `989676dd`). An unknown key is accepted when every declared field is present with its TYPE. Each unknown key name is recorded in the response record and on the EFFECT span. A missing or wrong declared field stays a typed error. This replaces the earlier strict default (same day). A strict `exact interface` form may come later.

## Slice 1 verdict (2026-11-06)

**[Verified]** Final review of slice 1: the implementation passes with notes. The claim is REJECTED under the [slice 1 pass and reject rule](#pass-and-reject-rule). Evidence: the GREEN-2 DRIFT table in [notes.md](workflow/2026-11-06/notes.md#green-2).

- Manual change sites: GEN 0, LIB 0. The rule needs GEN < LIB.
- The build passed in all 6 DRIFT rows (R, N, Q per arm). No compile error caught a DRIFT.
- The only arm difference is DRIFT-Q `new_live`: GEN gives a typed reject, LIB an untyped crash. The cause is the old 0002 transport that LIB keeps (`payment_http.ex:31` matches status 200). The cause is not the TYPE.
- Note 1: the host check raise is labelled typed in rows R and N (`run.py:410-411`).
- Note 2: the LIB freeze was committed only after the runs. The timestamps show a consistent order.

**[Requirement]** OWNER statement: the slice 1 rule measured the wrong thing. The goal is [vertical integration](../../wiki/concepts/vertical-integration.md): the compiler knows the TYPE of stored records, so a breaking TYPE change fails at compile time.

**[Inference]** Why the slice 1 rule is superseded for slice 2. A LIB with no TYPE facts needs no edit after a field change, so a count of manual change sites cannot favor GEN. The count also cannot show a failed build, because no arm had TYPE facts about stored records. Slice 2 therefore uses an absolute rule against stored TYPE VERSIONS. LIB stays as a control.

## Slice 2

### Question and claim

**[Requirement]** Can the compiler refuse a rename of a response field (DRIFT N, `status` → `state`) without a `rename` step in its MIGRATE CHAIN, because stored RESPONSE RECORDS hold the old TYPE VERSION? With the `rename` step, the source compiles and the old RESPONSE RECORDS replay as `correct_accept` through the generated decode.

### How the compiler learns the stored TYPE VERSIONS

**[Verified]** Slice 1 facts in the [0001 compiler](../0001-syntax-to-beam/src/main.rs): the generated `Replay.record/3` writes RESPONSE RECORD format version 1 to `ProbeSupport.Capture.write("responses", …)`, which appends to `<output>/responses.jsonl`. The record holds `artifact_id` (the BEAM hash of the build), not a TYPE fact. The compiler CLI takes exactly one argument, the source path.

**[Verified]** The 0003 test `response_capture_test.py` compares a fixed subset of record keys. Slice 1 added `unknown_keys` and kept format version 1.

**Common part of both options [Proposal], revision 6.** The generated `record/3` writes one more key, `type`: `{"name": "Payment", "version": 1, "fields": [["order_id", "String"], ["status", "String"]], "fingerprint": "<64 hex>"}`. This is the TYPE VERSION of the EFFECT output TYPE at the time of the write. `version` is the newest version number of the MIGRATE CHAIN of the build (1 without a chain). `fields` is sorted by field name. The fingerprint is the lower-case hex SHA-256 of the compact JSON text of `fields`, for example `[["order_id","String"],["status","String"]]` (no spaces, sorted by field name). The TYPE name is not part of the fingerprint. The format version stays 1, as with `unknown_keys`. The record names the full field list, so the compiler can name the old field in its message.

**Option A, RECORD SNAPSHOT input [Proposal].** The compiler takes a second input, `--stored PATH`, a RECORD SNAPSHOT (a copy of `responses.jsonl`). It reads the distinct `type` values per `operation`. It reads no body bytes.

- For: the compiler checks against observed stored data. The case "no stored records" is an empty file.
- For: one source of truth. Nothing can claim a TYPE VERSION that no record holds.
- Against: the build reads environment data. A build is reproducible only with the same RECORD SNAPSHOT (`run.py` records its SHA-256).
- Against: a large store needs an index or an export later.

**Option B, TYPE lock file [Proposal].** A file `orders.types.lock` next to the source lists the known TYPE VERSIONS per TYPE. A separate step writes it from the store. The compiler reads only the lock file.

- For: a reviewable file in git. The build reads no environment data.
- Against: a second source that can go stale or lie. The lock can list a TYPE VERSION that no record holds, or miss one that a record holds.
- Against: the case "no stored records" needs a count per TYPE VERSION in the lock.

**[Proposal] Recommendation for slice 2: Option A.** The claim is "the compiler knows the stored records". Option A reads them directly; Option B adds a claim between the store and the compiler. Rejected alternative: infer the stored TYPE from body keys. That mixes a Payments change (an extra key) with a TYPE VERSION of Orders.

**[Proposal]** A source with an `effect` and no `--stored` input fails with `stored TYPE VERSIONS unknown`. An unknown store is not an empty store. A source without an `effect` (`payments.beaml`) needs no input; its output stays byte-identical.

**Migrate [OWNER].** The production source of truth for stored TYPE VERSIONS (RECORD SNAPSHOT, lock file, or a live query of the deployed nodes). It fixes the record format and the deploy workflow of every later environment. Slice 2 uses a fixture file and does not decide it.

### MIGRATE CHAIN syntax (OWNER answer O1, revision 6)

**[Requirement]** OWNER answer O1. The `interface` is always the newest TYPE VERSION. The TYPE history is a MIGRATE CHAIN in the same source. Each step names the TYPE, two explicit version numbers and its changes. Slice 2 implements the step `rename` only. The DRIFT N source of `orders.beaml` with its chain:

```beaml
interface Payment { order_id: String state: String }
migrate Payment 1 -> 2 { rename status -> state }
```

- The newest version number is the target of the last `migrate` step of the TYPE. Without a chain it is 1.
- The compiler derives each old TYPE VERSION backwards from the newest one. Here: version 2 is `Payment { order_id: String state: String }`; version 1 is `Payment { order_id: String status: String }`.
- The RENAME ALIAS of the plan is now the `rename` step. The options S1, S2 and S3 are closed. The S3 sketch `Payment@1` is not used.
- `payments.beaml` stores no records and needs no chain.

### Check rule and generated decode

**[Requirement] Path check (OWNER answer 2).** For each `operation` in the RECORD SNAPSHOT, take its EFFECT output TYPE. For each stored TYPE VERSION (name, `version`, fingerprint) of that TYPE: it must equal the derived version with the same number. Equal means the same fingerprint, computed by the compiler from the derived field list. Then the chain gives a path from it to the newest version. A stored TYPE VERSION without such a path is a compile error. The build fails only for this reason; an empty RECORD SNAPSHOT gives no error.

**[Proposal]** The compiler reads the field list from the record only for its message. It compares fingerprints.

**[Requirement] Rename step check (OWNER answer O3).** A `rename old -> new` step whose old field is in no stored TYPE VERSION and in no derived version is a compile error. **[Inference]** With the backwards derivation, the old field is always in the derived version before the step. In slice 2 the observable case is C4: a wrong old name (`statuz`) gives a derived version 1 that no stored record has, so the path check fails and names `statuz`.

**[Verified] Decode (revised after the final review).** The generated decode goes by TYPE VERSION. A REPLAY RUN of a record of version n applies the `rename` steps n → newest in order. A live body is the newest version and gets no rename. The record body and its digest stay unchanged. The first form (fall back to an old name when the current name is missing) decoded wrong when a chain reuses a field name; see notes.md, "Slice 2 final review repair".

**[Proposal] Compile error text** (case C1). Exit ≠ 0, no stdout:

```text
error: TYPE Payment cannot read 1 stored RESPONSE RECORD of operation payments.authorize
  stored TYPE VERSION: Payment 1 { order_id: String status: String } (fingerprint <first 12 hex>)
  newest TYPE VERSION: Payment 1 { order_id: String state: String }
  record source: <the --stored path>
  no path from the stored TYPE VERSION to the newest TYPE VERSION
  field status: String is in the stored TYPE VERSION, not in the newest TYPE VERSION
  field state: String is in the newest TYPE VERSION, not in the stored TYPE VERSION
  help: if state is status renamed, declare: migrate Payment 1 -> 2 { rename status -> state }
```

The tests assert these tokens, not the full text: `Payment`, the old field, the new field, the `--stored` path, and the `help` form `migrate Payment <stored> -> <next> { rename <old> -> <new> }`. `<stored>` is the version number of the stored record. `<next>` is the newest version number plus 1. Compiler action events do not record the path (AGENTS rule).

**[Proposal] CLI form.** `beaml-spike SOURCE.beaml --stored SNAPSHOT.jsonl`. The `--stored` input comes after the source path.

### Cases with expected outcomes

**[Proposal]** `run.py` builds the slice 2 GEN tree with the `type` key, runs one live call per order, and retains the result as the RECORD SNAPSHOT fixture `v1` (TYPE VERSION `Payment 1 { order_id status }`). DRIFT edits follow slice 1 (both BEAML files). The domain edit of `valid_payment!/2` counts apart, as in slice 1.

**[Proposal] Revision 6, RED fixtures.** Until GREEN writes the `type` key, RED uses hand-built fixtures in `stored/`: `v1.jsonl` (one slice 1 L0 record plus the `type` key of `Payment 1 { order_id status }`), `v1-v2.jsonl` (C3: the `v1` record and one record of `Payment 2 { order_id state }`) and `empty.jsonl`. The case sources are in `slice2/<derivative>/orders.beaml` (the file stem is the service name). The compile tests also build each case from a template with other TYPE and field names, so that no fixture name in the compiler can pass them.

| ID | Source | RECORD SNAPSHOT | Build | Old record (REPLAY RUN) | New live call |
| --- | --- | --- | --- | --- | --- |
| C1 | N, no chain | `v1` | compile error, text above | not run | not run |
| C2 | N, `migrate Payment 1 -> 2 { rename status -> state }` | `v1` | exit 0 | `correct_accept`: `{:ok, %{order_id, state: <stored status value>}}`, decode 1, `finish/1` 1, transport 0 | `correct_accept`; the new record holds `Payment 2 { order_id state }` with its fingerprint |
| C3 | C2 source | `v1` plus a version 2 record (two TYPE VERSIONS) | exit 0 | both versions `correct_accept` | not run |
| C4 | N, `migrate Payment 1 -> 2 { rename statuz -> state }` | `v1` | compile error (no path) that names `Payment`, `statuz`, `status` and the `--stored` path | not run | not run |
| C5 | R (add `reference`), no chain | `v1` | compile error (no path) that names `Payment`, `reference` and the `--stored` path | not run | not run |
| C6 | N, no chain | empty file | exit 0 | none stored | `correct_accept` |
| C7 | slice 1 source (revision 6: `v1` has a path, so the missing key is the only fault) | `v1` plus one record without the `type` key (slice 1 format), at line 2 | compile error `stored RESPONSE RECORD has no TYPE VERSION`, names the `--stored` path and the line number | not run | not run |
| C8 | slice 1 source | no `--stored` input | compile error `stored TYPE VERSIONS unknown` | not run | not run |
| C9 | C6 build (empty snapshot, no chain) | `v1` record replayed against it (stale snapshot) | exit 0 | `typed_reject`: `PaymentError{reason: "decode"}`, `finish/1` 0, no crash | not run |
| C10 | slice 1 source (no chain, newest version 1) | `v1` for the build; empty file for the slice 1 tests (list below) | exit 0 | slice 1 (a)–(d2) pass again; `payments.beaml` output byte-identical; 0003 record key subset passes | as slice 1 |
| C11 | C2 build | `v1` | exit 0 | hand-built old record, body `{"order_id":"order-1","status":"<status value>","fraud_score":"0.9"}`, `type` key of `v1`, digest recomputed: `correct_accept` with `state: <status value>`, not `"0.9"`; `unknown_keys == ["fraud_score"]` | not run |
| C12 | C2 build | `v1` | exit 0 | hand-built old record with both names, `"state":"settled"` and `"status":"authorized"`: `correct_accept` with `state: "settled"` (the current name wins); `unknown_keys == ["status"]` | not run |
| C13 | C2 build | `v1` | exit 0 | hand-built old record with neither `state` nor `status`, plus `"fraud_score":"0.9"`: `typed_reject`, `PaymentError{reason: "decode"}`, `finish/1` 0 | not run |
| C14 | N2: `Payment` field `order_id` renamed `order_ref`, `migrate Payment 1 -> 2 { rename order_id -> order_ref }`, `status` unchanged | `v1` | exit 0 | `correct_accept`: `{:ok, %{order_ref: <stored order_id value>, status}}`, `finish/1` 1 | not run |
| C15 | N2, no chain | `v1` | compile error with the C1 tokens for `order_id` and `order_ref` | not run | not run |
| C16 | `bad/unknown_pipe_step.beaml` | no `--stored` input | compile error that names `charge`, not `stored TYPE VERSIONS unknown` | not run | not run |

**[Requirement]** The cases use the MIGRATE CHAIN of OWNER answer O1. The C2 new call runs the generated `place/1` in an eval VM against the Payments stub, not through the router: the host `valid_payment!/2` checks `status` (slice 1 DRIFT N, domain site).

**[Inference]** C11 and C13 kill a decode that falls back to any unknown String key: `fraud_score` sorts before `status`, and C13 must not accept `fraud_score` as `state`. C12 kills a decode that prefers the old name. C14 and C15 kill a check or decode with the names `status` and `state` written into the compiler: the field names must come from the RECORD SNAPSHOT and the MIGRATE CHAIN. The template compile tests with other names do the same for the TYPE name.

**[Proposal] Artifact check for old records.** An old record comes from another build, so its `artifact_id` (BEAM hash) differs from the replay build. The generated runner has no artifact check (slice 1 uses Q3 (ii)). For the cross-build cases C2, C3, C9, C11–C14, the harness skips only the caller artifact check. It asserts that the record `artifact_id` differs from the build `artifact_id` and writes both to the result. The other caller checks stay. C10 and the 0003 8-case matrix keep the artifact check. Q3 and D002 decide artifact identity across builds later.

**[Proposal] Order of the `--stored` check.** The compiler reports parse and TYPE errors first. It reports `stored TYPE VERSIONS unknown` only for a source without such errors (C16).

**[Proposal] Slice 1 tests that change (C10).** Each one passes `--stored` with an empty snapshot file, so the slice 1 outcomes stay:

- `0001-syntax-to-beam/tests/cli.rs`: `orders_cli_accepts_effect_pipe_place`, `orders_cli_emits_flow_effect_decode_and_replay`, `orders_cli_template_control_drift_r_decode_names_reference`, `orders_cli_template_control_drift_n_decode_follows_field_rename`.
- `tests/arms_test.py` (the GEN `generate-orders` build) and `run.py` (the GEN `generate-orders` step, also used by the (f) DRIFT rows of `tests/drift_test.py`).
- Unchanged: the five `bad/*` tests in `cli.rs` (parse and TYPE errors come first), all `payments_cli_*` tests, and the LIB `generate-orders` step (the LIB `orders.beaml` has no `effect`).
- **[Verified] Gap found in RED (revision 6).** Three GEN 0003 copies call the compiler on the GEN `orders.beaml` without `--stored`: `arms/gen/overlay/.../tests/replay_run_test.py:140`, `response_capture_test.py:91`, `trace_lookup_test.py:50`. They pass today. After GREEN (OWNER answer O2) they fail, and with them the arms tests (c) and (d) and the DRIFT repair check. GREEN must add the empty snapshot there. That changes the 0003 change table of slice 1 and the overlay diff test; the RED worker did not change them. **[Verified] GREEN closed the gap.** The changed lines are 141, 92 and 51 (the second line of each call). Each copy passes `--stored` with the empty file `stored-empty.jsonl` of the GEN overlay. The change table above and `overlay_diff_test.py` have the three rows.

**[Proposal] Slice 2 test files (revision 6).** `tests/stored_types_test.py`: compile cases C1–C8, C10, C14, C15, each with the fixture names and with random TYPE and field names. `tests/slice2_replay_test.py`: replay cases C2, C3, C9, C11–C14 and the C2 new call. `tests/cli.rs`: C8 and C16. C3 replays both records on the C2 build; the C3 build with `v1-v2.jsonl` is checked in `stored_types_test.py`.

**[Requirement]** OWNER answer O4 (revision 6). An added field without `migrate ... { add <field>: <TYPE> = <constant> }` leaves the stored records without a path, so C5 is a compile error. With the `add` step the source compiles and old records decode with the constant. Slice 2 implements only `rename`; C5 is the one control for this rule. The old C5 gap is closed.

**[Inference]** C6 against C1 is the key control. The source is the same; only the stored records differ. The compile error must come from the stored TYPE VERSION, not from the source.

### LIB comparison and pass and reject rule

**[Inference] What a fair LIB can do.** LIB holds no TYPE facts (revision 4 form: no key list, no field name). It cannot fail a build on a TYPE change. It can give a typed reject of the old record in a REPLAY RUN (slice 1: `ReplayLib.Error finish`). A host test that replays all stored records after each build can find the break, but only after the build, as a test failure, with no TYPE name and no alias proposal. A hand-written key fallback in the LIB decode can accept the old record; that is a manual change site.

**[Proposal] LIB run.** Run the frozen LIB of slice 1 on DRIFT N with the `v1` RECORD SNAPSHOT copied into its tree. Expected: build exit 0, old record `typed_reject`. Record the result as a control. LIB is not part of the pass clause.

**[Proposal] Pass.** The claim holds for slice 2 only if all are true:

1. C1 fails at compile time with exit ≠ 0, no stdout, and all asserted tokens.
2. C6 compiles. So the C1 error comes from the stored records.
3. C2, C3, C11, C12 and C14 give `correct_accept` for every old record with the expected values, and C2 gives `correct_accept` for a new call with the version 2 record.
4. C4, C5, C7, C8, C15 and C16 fail at compile time with the expected message. C9 and C13 give a typed reject.
5. C10 passes. GEN gives no `wrong_accept` and no untyped crash in any case.

**[Proposal] Reject.** Any unmet pass clause rejects the claim for slice 2. The one exception is a failed C10: it gives no verdict (below). Record the reject in the register. Examples of a reject:

- C1 compiles (exit 0) with old TYPE VERSIONS in the RECORD SNAPSHOT.
- C6 also fails. Then the error comes from the source, not from the stored records.
- C2 or C3 gives anything other than `correct_accept` for an old record.
- Any case gives a `wrong_accept`, for example C2 with `state` empty or taken from the wrong field.
- C5 compiles. Then a stored TYPE VERSION without a path does not block.

**No verdict.** If C10 fails, slice 2 fails as an implementation and gives no verdict on the claim.

### Out of scope

- Every `migrate` step other than `rename`: `add <field>: <TYPE> = <constant>`, `drop`, a changed field TYPE. C5 shows only that an added field without a step is a compile error.
- A record whose `version` and fingerprint disagree with each other, and a chain with gaps or repeated version numbers.
- Per-environment levels (an environment with lower priority that does not block).
- More than one environment, mixed-version live traffic and a live query of deployed nodes.
- The lifetime of a `rename` step after no stored record needs it.
- Everything in slice 1 "Later", except the old-record policy (Q4), which slice 2 answers for renames only.

### Decisions (Decision4, slice 2 plan)

| Decision | Class | Choice and reason |
| --- | --- | --- |
| Slice 1 rule superseded for slice 2 by an absolute rule; LIB is a control | Repair | OWNER statement. Commits slice 2 to the cases above, not to a count |
| `type` key (name, version, fields, fingerprint) in the RESPONSE RECORD, format version 1 kept | Repair | Over a new format version: `unknown_keys` set the precedent, the 0003 key subset still passes. Commits every later record to the key |
| Recommend Option A (RECORD SNAPSHOT via `--stored`) | Repair | Over Option B: one source of truth, no stale lock. Slice 2 only; production choice is Migrate |
| Production source of truth for stored TYPE VERSIONS | Migrate | OWNER chooses between snapshot, lock file and live query |
| MIGRATE CHAIN `migrate T a -> b { rename old -> new }`, `interface` = newest version | OWNER (O1) | Answered 2026-11-06. S1, S2, S3 closed |
| No `--stored` input for a source with an `effect` is a compile error | Repair | Over "treat as empty": an unknown store is not an empty store. Commits slice 1 CLI tests to pass an empty snapshot |
| Build fails only when a stored TYPE VERSION has no path; R without a chain is a compile error | OWNER (answer 2, O4) | Answered 2026-11-06. `add` is out of scope for slice 2 |
| `rename` with an old field in no stored and no derived version is a compile error | OWNER (O3) | Answered 2026-11-06, as planned |
| ~~Decode reads the old name of a `rename` step as a fallback, live and replay~~ Superseded: decode by record version (final review, DL-043) | Repair | The fallback form swapped values when a chain reuses a field name |
| Fingerprint = SHA-256 of the compact JSON of the field list sorted by name, TYPE name not included | Undo | Local to generated code and the compiler until GREEN writes records |
| `--stored` after the source path | Undo | One CLI form in the tests |
| C2 new call through the eval `place/1`, not the router | Repair | Over the slice 1 DRIFT N domain repair of `valid_payment!/2`: the host check is not the TYPE claim. Commits C2 to an eval VM run |
| C6 against C1 as the main control | Undo | Same source, different store; shows the error comes from records |
| Harness skips only the caller artifact check for cross-build old records; asserts the `artifact_id` differs | Repair | Over re-recording `v1` per build: an old record must come from an old build. Commits slice 2 to no artifact identity across builds; Q3 and D002 decide later |
| `--stored` check after parse and TYPE errors | Undo | Keeps the five slice 1 `bad/*` tests unchanged. One check order to change later |
| With a `rename` step, the current name wins; an old name next to it is an unknown key (C12) | Undo | Local to the generated decode. Keeps one hint rule for every unread key |

### OWNER questions (slice 2)

- **O1. Answered 2026-11-06.** A MIGRATE CHAIN in the same source: `migrate Payment 1 -> 2 { rename status -> state }`. The `interface` is the newest version; old versions are derived backwards. S1, S2 and S3 are closed.
- **O2. Answered 2026-11-06.** A source with an `effect` and no RECORD SNAPSHOT is a compile error. An unknown store is not an empty store.
- **O3. Answered 2026-11-06.** A `rename` whose old field is in no stored and no derived version is a compile error.
- **O4. Answered 2026-11-06.** DRIFT R with old records and no `add` step is a compile error (no path). With `migrate ... { add <field>: <TYPE> = <constant> }` it compiles. Slice 2 implements only `rename`.
- **O5 (Migrate), open.** Production source of truth for stored TYPE VERSIONS: RECORD SNAPSHOT, lock file or live query of the deployed nodes?

## Slice 3

**[Requirement]** DL-042 fixes the content: `add` with a constant and `drop` with a TYPE in the MIGRATE CHAIN. The slice 2 text above stays unchanged. Its pass and reject rule does not apply to slice 3. The slice 2 tests must stay green.

### Question and claim (slice 3)

**[Requirement]** Can the compiler refuse an added or a removed response field without an `add` or `drop` MIGRATE CHANGE, because stored RESPONSE RECORDS hold the old TYPE VERSION? With the MIGRATE CHANGE, the source compiles. Old RESPONSE RECORDS then replay as `correct_accept`: an `add` fills its constant, a `drop` removes the field. The decode goes by TYPE VERSION (DL-043), also in a chain that mixes `rename`, `add` and `drop` and reuses a field name.

**[Requirement]** OWNER decisions for slice 3:

- `add <field>: <TYPE> = <constant>`. The constant is an explicit statement about old data (DL-028). A REPLAY RUN of an older record fills the constant.
- `drop <field>: <TYPE>`. The TYPE makes every old TYPE VERSION fully typed (DL-023). A REPLAY RUN of an older record removes the field. The dropped value is not used. In slice 3 the TYPE is `String` (revision 7.1, DL-044).
- The MIGRATE CHANGES of one MIGRATE STEP are separated by commas. Slice 3 implements `rename`, `add` and `drop` only.
- The build fails only when a stored TYPE VERSION has no path (DL-031). A field added without `add` or removed without `drop` leaves no path. The error has a `help` line with the missing MIGRATE CHANGE.

### Syntax (slice 3)

**[Requirement]** Example with all three MIGRATE CHANGES:

```beaml
interface Payment { order_id: String state: String status: String }
migrate Payment 1 -> 2 { rename status -> state, add channel: String = "web" }
migrate Payment 2 -> 3 { drop channel: String, add status: String = "migrated" }
```

**[Proposal]** Grammar of a MIGRATE STEP:

```text
migrate  = "migrate" TYPE NUMBER "->" NUMBER "{" change ( "," change )* "}"
change   = "rename" FIELD "->" FIELD
         | "add" FIELD ":" TYPE "=" constant
         | "drop" FIELD ":" TYPE
constant = STRING_LITERAL
```

- **[Proposal]** A comma is necessary between two MIGRATE CHANGES. A trailing comma is a parse error. The slice 2 parser accepts a missing comma; no slice 2 source or test uses two MIGRATE CHANGES in one step, so this change breaks no slice 2 case.
- **[Proposal]** `add` needs `=` and a constant. There is no default value (DL-028).
- **[Proposal]** In slice 3 the constant is a string literal, and the field of an `add` has the TYPE `String`. The compiler has no `Int` TYPE and no literal form for a record or an `enum` value.
- **[Proposal]** The TYPE of a `drop` is `String` (revision 7.1, DL-044). Any other TYPE, declared (for example `PaymentError`) or unknown (for example `Int`), is a compile error (K6). The generated decode checks `String` values only, so a `drop` of a declared TYPE has no replay case in slice 3.
- **[Proposal]** Any other word in a MIGRATE STEP is an error. A computed assignment such as `amount = Money(amount_cents, currency)` is not supported.

### Derivation backwards (slice 3)

**[Requirement]** The `interface` is the newest TYPE VERSION. The compiler derives version a from version b for each MIGRATE STEP `a -> b`, from the newest step to the oldest:

- `rename old -> new`: the field `new` of version b has the name `old` in version a (slice 2).
- `add f: T = c`: version a is version b without the field `f`.
- `drop f: String`: version a is version b with the field `f: String`.

**[Inference]** Example above: version 3 is `{ order_id state status }`. Version 2 is `{ order_id state channel }`. Version 1 is `{ order_id status }`. The name `status` leaves in step 1 -> 2 and comes back with another meaning in step 2 -> 3. The field `channel` lives only in version 2.

### Consistency checks (slice 3)

**[Proposal]** The compiler checks each MIGRATE STEP against the source alone. It reports these errors before the `--stored` check (as C16). They fail also with an empty RECORD SNAPSHOT.

**[Proposal] Check order (revision 7.1).** The K checks run where the MIGRATE CHAIN is derived (`derive_versions`). The compiler calls it before the EFFECT check that allows `String` output fields only (`main.rs`, `Checker::new` calls `derive_versions` before `effects()`). So K2 and K4 report their own message for the EFFECT output TYPE, not the EFFECT message. In one MIGRATE STEP, K7 and K8 run before the checks of the single MIGRATE CHANGES (K1–K6).

| ID | Source fault | Error, asserted tokens |
| --- | --- | --- |
| K1 | `add f` where `f` is not in version b | `migrate T a -> b`, `add f`, `not in T b` |
| K2 | `add f: X` where `f` has another TYPE Y in version b | `add f`, `X`, `Y` |
| K3 | `add f: String = 5` (the constant is not a string literal) | `add f`, `5`, `String` |
| K4 | `add f: X = "c"` where `X` is not `String` (and `f: X` in version b). Reachable only by the check order above | `add f`, `X`, `String fields only` |
| K5 | `drop f` where `f` is in version b | `drop f`, `still in T b` |
| K6 | `drop f: X` where `X` is not `String`, for example `Int` (unknown) or `PaymentError` (declared) | `drop f`, `X`, `String fields only` |
| K7 | One field name two times in one MIGRATE STEP, for example `{ drop f: String, add f: String = "c" }` or `{ rename f -> g, add f: String = "c" }` | `migrate T a -> b`, `f`, `two times` |
| K8 | Empty MIGRATE STEP `{ }` | `migrate T a -> b`, `at least one rename, add or drop` |
| K9 | Missing comma: `{ add f: String = "c" drop g: String }` | `expected ','` |
| K10 | Trailing comma: `{ drop g: String, }` | `expected rename, add or drop` |
| K11 | `add f: String` without `= constant` | `expected '='` |
| K12 | Computed assignment `{ f = Money(g, h) }` | `unsupported migrate step`, `rename`, `add`, `drop` |

**[Proposal]** K7 counts the old and the new name of a `rename`. With K7 the MIGRATE CHANGES of one step do not depend on their order. A field that leaves and comes back needs two MIGRATE STEPS (case D11, D14).

**[Inference]** Two faults are not visible in the source alone. They fail through the path check, as the misspelled `rename` of slice 2 (DL-036):

- An `add f` for a field that old records already hold. The derived old version lacks `f`; a stored record with `f` has no path (case D15).
- Revision 7.1: a `drop f: X` with a TYPE other than `String` is now a source error (K6, case D7), not a path error.

**[Proposal]** `add` of a field in one step and `drop` of the same field in a later step is legal (field `channel` above). Each MIGRATE STEP is a statement about one pair of versions, and records of the middle version can exist. `drop` and a later `add` of the same name is also legal (name reuse, case D14).

### Generated decode (slice 3)

**[Requirement]** The decode goes by TYPE VERSION (DL-043). A body of version v gets the MIGRATE STEPS v -> v+1 -> ... -> newest in chain order. A live body is the newest version and gets no MIGRATE CHANGE.

**[Proposal]** Each MIGRATE CHANGE of a step, applied to the body:

- `rename old -> new`: `old` is read as `new` only when the body has no `new` (slice 2, F4 and C12). The `rename` always removes `old` from the working body (DL-048). When the body also holds `new`, the value of `old` is not read, and `old` goes into `unknown_keys`.
- `add f: String = c`: the decode always puts `c` (DL-048). When the working body holds a key `f`, its value is not read, and `f` goes into `unknown_keys`. A body value never wins over the constant.
- `drop f: String`: the body must hold `f` with a `String` value. Otherwise the decode gives `PaymentError{reason: "decode"}`. Then the decode removes `f`. A dropped key is consumed; it is not an unknown key.

**[Proposal]** `unknown_keys` holds, sorted and each key once, every key of the stored body that the decode does not read: a key that a `rename` or an `add` removes unread, and every key outside the declared fields at the end. This keeps the slice 2 cases C11 and C12 unchanged.

**[Proposal]** The record body and its digest stay unchanged. The live path never puts a constant. A TYPE without a MIGRATE CHAIN keeps the slice 1 decode (payments output byte-identical).

### Path errors and help lines (slice 3)

**[Proposal]** The path check of slice 2 stays: equal means the same fingerprint as the derived version with the same number. Only the `help` lines change. `<stored>` is the stored version; `<next>` is the newest version plus 1 (slice 2 rule). `<constant>` stays a placeholder: the compiler does not guess a value (DL-028).

| Difference between stored and newest TYPE VERSION | `help` line, asserted |
| --- | --- |
| Only added fields `a: String`, `b: String` | `migrate T <stored> -> <next> { add a: String = <constant>, add b: String = <constant> }` |
| Only removed fields `x: String`, `y: String` | `migrate T <stored> -> <next> { drop x: String, drop y: String }` |
| One removed `x: String`, one added `a: String` (slice 2 rename case) | first line unchanged (`rename x -> a`); second line `migrate T <stored> -> <next> { drop x: String, add a: String = <constant> }` |
| Removed and added fields in other counts | one line with all `drop` MIGRATE CHANGES, then all `add` MIGRATE CHANGES, each group sorted by field name |
| A removed field with a TYPE other than `String` (revision 7.1) | no `drop` form; the line says `drop supports String fields only` |
| The same field name with another TYPE | no `help` line (a changed field TYPE is out of scope) |
| A stored version older than the newest without a path | `help: the MIGRATE CHAIN of T must derive version <stored> with the fields of the stored TYPE VERSION; check its rename, add and drop steps` |

Example (case D5):

```text
error: TYPE Payment cannot read 1 stored RESPONSE RECORD of operation payments.authorize
  stored TYPE VERSION: Payment 1 { order_id: String status: String } (fingerprint <first 12 hex>)
  newest TYPE VERSION: Payment 1 { order_id: String }
  record source: <the --stored path>
  no path from the stored TYPE VERSION to the newest TYPE VERSION
  field status: String is in the stored TYPE VERSION, not in the newest TYPE VERSION
  help: if status is removed, declare: migrate Payment 1 -> 2 { drop status: String }
```

**[Inference] Revision 7.1.** The row "an added field with a TYPE other than `String`" is removed. An added field is in the newest TYPE VERSION, and the EFFECT check rejects a newest field other than `String` before the `--stored` check. No source can reach that row.

**[Proposal]** The tests assert tokens, not the full text: the TYPE name, each named field, the `--stored` path and the asserted `help` form. Compiler action events do not record the path (AGENTS rule).

### Cases (slice 3)

**[Proposal]** Fixture names follow slice 2: TYPE `Payment`, fields `order_id`, `status`, added field `reference`, constant `"pre-v2"`. Sources are in `slice3/<case>/orders.beaml`. `stored/v1.jsonl` is reused; other snapshots are written per test (pattern S15). Every compile and replay case also runs from a template with random TYPE names, field names and constants. A random constant holds a quote, a backslash and a non-ASCII letter, so that a constant written into the compiler or a wrong escape fails. Replay cases use the slice 2 harness mode `replay_plain`. Live calls run the generated `place/1` in an eval VM against the unchanged Payments stub (slice 2, S5). The stub body is `{order_id, status}`.

Sources:

- **R+add.** `interface Payment { order_id: String status: String reference: String }`, `migrate Payment 1 -> 2 { add reference: String = "pre-v2" }`.
- **R2.** `interface Payment { order_id: String status: String reference: String channel: String }` without a chain (two added fields).
- **R.** The R+add interface without a chain (slice 2 C5 source).
- **D+drop.** `interface Payment { order_id: String }`, `migrate Payment 1 -> 2 { drop status: String }`.
- **D.** The D+drop interface without a chain.
- **M.** The example of the syntax section (three versions, `rename`, `add` and `drop`, name reuse of `status`, `channel` only in version 2).
- **Z.** `interface Payment { order_id: String status: String }`, `migrate Payment 1 -> 2 { drop status: String }`, `migrate Payment 2 -> 3 { add status: String = "new" }`. Version 1 and version 3 have the same fields and the same fingerprint.

| ID | Source | RECORD SNAPSHOT | Build | Old record (REPLAY RUN) | Live call |
| --- | --- | --- | --- | --- | --- |
| D1 | R+add | `v1` | exit 0 | `correct_accept` `{order_id, reference: "pre-v2", status}`, `unknown_keys == []`, `finish/1` 1 | not run |
| D2 | R | `v1` | compile error: `Payment`, `reference`, path, help `migrate Payment 1 -> 2 { add reference: String = <constant> }` | not run | not run |
| D2b | R2 | `v1` | compile error: `Payment`, `channel`, `reference`, path, help `migrate Payment 1 -> 2 { add channel: String = <constant>, add reference: String = <constant> }` (sorted by field name) | not run | not run |
| D3 | R | empty | exit 0 | none | not run |
| D4 | D+drop | `v1` | exit 0 | `correct_accept` `{order_id}`, `unknown_keys == []` (`status` consumed), `finish/1` 1 | `correct_accept` `{order_id}`, `unknown_keys == ["status"]`; new record holds `Payment 2 { order_id }` and its fingerprint |
| D5 | D | `v1` | compile error: `Payment`, `status`, `String`, path, help `migrate Payment 1 -> 2 { drop status: String }` | not run | not run |
| D5b | DRIFT N (`interface Payment { order_id: String state: String }`, slice 2 C1 source) | `v1` | compile error: `Payment`, path, help `migrate Payment 1 -> 2 { rename status -> state }` and help `migrate Payment 1 -> 2 { drop status: String, add state: String = <constant> }` | not run | not run |
| D5c | D | hand-built `v1` record with `status: PaymentError` in the TYPE VERSION | compile error: `Payment`, `status`, `PaymentError`, path, `drop supports String fields only`; no `drop status: PaymentError` form | not run | not run |
| D6 | D | empty | exit 0 | none | `correct_accept` |
| D7 | D+drop with `drop status: PaymentError` | `v1` | compile error K6: `drop status`, `PaymentError`, `String fields only`, no stdout | not run | not run |
| D7b | D7 source | empty | the same compile error: a source error, independent of the records | none | not run |
| D8 | R+add build | `v1` | exit 0 | hand-built `v1` record with `"reference":"r-9"` in the body: `correct_accept` with `reference: "pre-v2"`, `unknown_keys == ["reference"]` (DL-048) | not run |
| D9 | D+drop build | `v1` | exit 0 | hand-built `v1` record without `status`: `typed_reject` `decode`, `finish/1` 0. Second record with `"status":7`: the same | not run |
| D10 | R+add build | `v1` | exit 0 | not run | `typed_reject` `decode`, `finish/1` 0: the stub body has no `reference`, and a live body gets no constant. The new record holds version 2 |
| D11 | M | records of version 1, 2 and 3 | exit 0 | v1 `{status: "authorized"}` → `{state: "authorized", status: "migrated"}`, `unknown_keys == []`; v2 `{state: "settled", channel: "app"}` → `{state: "settled", status: "migrated"}`, `unknown_keys == []`; v3 body unchanged, `unknown_keys == []` | not run |
| D11b | M build | records of version 1, 2 and 3 | exit 0 | hand-built v1 record with both keys `{state: "settled", status: "authorized"}` → `{state: "settled", status: "migrated"}`, `unknown_keys == ["status"]`. The old `status` value is only in `unknown_keys` (DL-048) | not run |
| D12 | M without `drop channel: String` in step 2 -> 3 | empty | compile error K1: `migrate Payment 1 -> 2`, `add channel`, `not in Payment 2` | not run | not run |
| D13 | M | a version 2 record without `channel` | compile error (no path): `Payment`, `channel`, `derived TYPE VERSION 2`, path | not run | not run |
| D14 | Z | `v1` | exit 0 | `correct_accept` with `status: "new"`, not the stored value, `unknown_keys == []` | live body `{order_id, status}` keeps its `status` value, `unknown_keys == []`; new record holds version 3 |
| D15 | `interface Payment { order_id: String status: String }`, `migrate Payment 1 -> 2 { add status: String = "x" }` | `v1` | compile error (no path): `Payment`, `status`, `derived TYPE VERSION 1`, path | not run | not run |
| D15b | D15 source | empty | exit 0 | none | not run |
| K1–K12 | per the consistency table, built on the R+add or D+drop source | empty | compile error with the K tokens, no stdout | not run | not run |
| D16 | all slice 1 and slice 2 tests | as before | as before | as before | as before |

**[Inference]** What each control kills:

- D3, D6 and D15b against D2, D5 and D15: the error must come from the stored records, not from the source (as C6 against C1). D7b against D7 shows the opposite: K6 is a source error.
- D10: a decode that puts the constant also into live bodies (a guess on new data).
- D11 v1 and D14: a decode by key presence or by body shape. Both keep the stored `status` value. D14 has the same fingerprint for versions 1 and 3, so only the record version tells the decode which steps to apply.
- D11 v2: a decode that applies the steps of version 1 to a version 2 body, or that does not consume a dropped key.
- D9: a `drop` that removes a field without its TYPE check (DL-023).
- D8 and D11b: a decode that keeps a body value over the constant (decode by key presence, rejected in DL-048). In D11b the stray value comes through a `rename` step with both keys in the body.
- D2b and D5b: help lines with one MIGRATE CHANGE only, or in another order.
- D5c: a `drop` help form for a TYPE that `drop` does not take.
- The template runs: a compiler with the fixture names or the fixture constant in it.

**[Proposal] Test files.** `tests/slice3_types_test.py` holds the compile cases D2, D2b, D3, D5–D7b, D12, D13, D15, D15b, K1–K12 and the builds of D1, D4, D11 and D14. `tests/slice3_replay_test.py` holds the replay and live cases D1, D4, D8–D11b and D14. New files keep the SHA-256 of all slice 2 test files unchanged; D16 runs them unchanged.

**[Proposal] Compiler change sites.** `Migration` holds a list of MIGRATE CHANGES. The parser reads `rename`, `add` and `drop` with comma separators. `derive_versions` applies the three backward rules and checks K1–K8. The decode generator emits one block per MIGRATE CHANGE. `no_path` emits the new `help` lines.

### Pass and reject rule (slice 3)

**[Proposal] Pass.** The claim holds for slice 3 only if all are true:

1. D2, D2b, D5, D5b and D5c fail at compile time with exit ≠ 0, no stdout and all asserted tokens, with fixture names and with random names.
2. D3 and D6 compile. So the D2 and D5 errors come from the stored records.
3. D1, D4, D8, D11, D11b and D14 give `correct_accept` for every old record with exactly the expected values and `unknown_keys`.
4. D7, D7b, D12, D13, D15 and K1–K12 fail at compile time with their tokens. D15b compiles. D9 and D10 give `typed_reject` `decode`.
5. D16 passes: every slice 1 and slice 2 test, unchanged.
6. GEN gives no `wrong_accept` and no untyped crash in any case.

**[Proposal] Reject.** Any unmet pass clause rejects the claim for slice 3, except a failed D16 (below). Record the reject in the register. Examples:

- D2 or D5 compiles with the `v1` RECORD SNAPSHOT.
- D3 or D6 also fails.
- D10 accepts: the constant filled a live body.
- D11, D11b or D14 accepts with the stored `status` value instead of the constant (`wrong_accept`).
- D8 accepts with `reference: "r-9"` (`wrong_accept`).
- D9 accepts a version 1 body without the dropped field.

**No verdict.** If D16 fails, slice 3 fails as an implementation and gives no verdict on the claim.

### Out of scope (slice 3)

- Computed MIGRATE CHANGES (`amount = Money(...)`), `Unknown`, `enum` matching in a step, PII.
- An `Int` TYPE and constants other than a string literal. `add` or `drop` for a field of a record or `enum` TYPE (revision 7.1: `drop` takes `String` only).
- A changed field TYPE under the same name in one step (K7 rejects `drop f` with `add f` in one step).
- The run of migrations over stored values (DL-027) and rollback windows for a lossy `drop`.
- The lifetime of a MIGRATE STEP after no stored record needs it.
- The LIB arm. Slice 2 shows that LIB holds no TYPE facts; slice 3 adds no LIB run.
- The production source of stored TYPE VERSIONS (O5, open).

### Decisions (Decision4, slice 3 plan)

| Decision | Class | Choice and reason |
| --- | --- | --- |
| `add` with constant, `drop` with TYPE, commas, `rename`/`add`/`drop` only, path rule unchanged, decode by version | OWNER (DL-022, DL-023, DL-028, DL-031, DL-042, DL-043) | Given for slice 3 |
| Comma necessary between MIGRATE CHANGES; trailing comma is an error | Undo | Over optional commas: a missing comma becomes visible (K9, K10). No slice 2 source has two changes in a step |
| `add` only for `String` fields with a string literal constant | Repair | Over adding `Int` and record or `enum` literals: the compiler has only `String` and declared TYPES. Commits slice 3 sources to `String` constants |
| ~~`drop` TYPE is `String` or a declared TYPE~~ Superseded in revision 7.1: `drop` TYPE is `String` only (DL-044) | Repair | Chose `String` only. Over a declared TYPE: the generated decode checks `String` values only, and no case replays a dropped value of a declared TYPE, so the claim would be untested. Because a fresh check found that gap. Commits a record or `enum` `drop` to a later slice with a nested decode |
| One field name at most once per MIGRATE STEP (K7) | Undo | Over order-dependent changes in one step. A field that leaves and comes back takes two steps. A later relaxation breaks no source |
| `add` then a later `drop` of the same field, and `drop` then a later `add`, are legal | Repair | Over a reject: each step is a statement about one version pair, and middle-version records can exist. Commits the decode to version dispatch (D11, D14) |
| `add` of a field that old records hold fails through the path check | Repair | Same reason as DL-036: the source alone cannot show it; with an empty snapshot it compiles. Revision 7.1: a `drop` TYPE other than `String` is a source error (K6) |
| ~~`add` in the decode: the body value wins when the body has the field~~ Superseded by DL-048: the `add` constant always wins in a REPLAY RUN; the body key goes into `unknown_keys`; a `rename` removes the old key from the working body | Repair (DL-048) | Over a body value that wins: a body value read as typed data is decode by key presence (rejected in DL-043), and it overrides the constant, which DL-028 makes a statement about all old records. Commits D8 and D11b |
| K checks run before the EFFECT output check; K2 and K4 stay; the help row for an added field with a TYPE other than `String` is removed (revision 7.1) | Repair | Chose the check order that `Checker::new` already has (`derive_versions` before `effects()`). Over dropping K2 and K4: the order costs no extra compiler code and keeps a precise message. Because no source can reach the removed help row. Commits GREEN to keep that order |
| New help cases D2b, D5b, D5c (revision 7.1) | Undo | Test cases for planned help rows; no new rule |
| `drop` in the decode checks the dropped value against its TYPE; a missing or wrong value is a typed `decode` reject | Repair | Over removing without a check: DL-023 says old versions are fully typed. Commits every old body to its full TYPE VERSION (D9) |
| A live body never gets a constant | Repair | DL-028: the constant is a statement about old data only. Commits live traffic to the newest TYPE (D10) |
| `help` lines name the missing `add` or `drop` with a `<constant>` placeholder | Undo | Message text only. The compiler does not guess a constant |
| New test files for slice 3; slice 2 test files unchanged | Undo | Keeps the slice 2 SHA-256 as regression evidence |
| No LIB run in slice 3 | Repair | Over a LIB control per slice: LIB holds no TYPE facts (slice 2). Commits the slice 3 verdict to GEN cases only |
| New GLOSSARY terms MIGRATE STEP and MIGRATE CHANGE | Undo | One name for the `migrate` line and one for its entries; slice 2 text used "step" for both |

### OWNER questions (slice 3)

**[Inference]** No new Migrate question. Every syntax that slice 3 uses is decided (DL-022, DL-023, DL-028). O5 stays open from slice 2.

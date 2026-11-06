# Record the REPLAY RUN and invalid replay record RED (0003)

**[Requirement]** This is behavior gate 4 in the [remaining gates](../notes.md). Follow acceptance cases 4 and 5 in the [EXPERIMENT](../../../README.md). The owner accepted review advisory A1 into this gate. [CAPTURE review](../capture/review.md#advisory-items)

**[Verified]** The owner chose fresh Claude Opus 5.5 workers instead of GPT-6.1 Sol. GPT-6.1 Sol is not available in Claude Code.

**[Verified]** Revision 1 below is superseded by owner decisions of 2026-11-06. See [RED revision 2](#red-revision-2-separate-runner). Revision 1 stays as historical evidence.

## Decision

**[Proposal]** Use the [Ponytail Lite](../proposal-lite.md) replay shape: run the retained Orders release modules in a fresh VM without a release start. Use the [Ponytail Ultra](../proposal-ultra.md) error codes `missing_response`, `operation_mismatch` and `attempt_mismatch`.

- **Entry.** `bin/orders eval` of the retained Orders release, after both live releases stop. Elixir loads the runtime configuration and starts no application, listener or Payments peer.
- **Path.** The harness calls the real `OrdersApi.Router` with one in-process `POST /orders` conn (`Plug.Test`). The REPLAY RUN thus uses the live order validation, preparation, finish and PAYMENT validation by construction.
- **Replay input.** `conn.private.beaml_replay` holds the first receipt trace and the saved response records. An HTTP client cannot set conn private data. Orders must select the record for that trace and substitute it at the outbound boundary.
- **Observer.** The existing transport counter, plus BEAM call counts on `OrdersBeamlSpike.finish/1`, `ProbeSupport.valid_payment!/2`, `OrdersApi.PaymentHttp.authorize/2` and `:gen_tcp.connect/4`. The Payments port in the replay VM is refused.
- **Artifact check.** Before replay, the test compares the retained release `OrdersBeamlSpike` BEAM with the run manifest and the record `artifact_id`. The replay VM reports the same hash for the loaded module.
- **A1.** A separate Orders release calls a Python loopback stub Payments. The stub returns a valid PAYMENT with non-canonical JSON (spaces, newline, other key order).

**[Proposal]** Rejected complexity:

- A new `replay.exs` or `OrdersApi.Replay` entry. A missing entry gives only an undefined-function failure, not behavior RED. It also needs a second copy of the router's finish and validation step.
- An Orders module-set digest and a replay archive. A3 is an open decision and out of scope.
- A replay release with a listener, or an app-env replay switch. `conn.private` is per call and not reachable from HTTP.
- Self-reported replay step lists. BEAM call counts observe finish and transport from outside the Orders code.

## Run

Run from the repository root with an offline Mix cache and loopback TCP. Run serially.

```sh
python3 -B experiments/0003-source-linked-replay/tests/replay_run_test.py
```

Test: `test_isolated_replay_reproduces_first_call_and_rejects_invalid_records` in [replay_run_test.py](../../../tests/replay_run_test.py), SHA-256 `d316a542…88f250`.

**[Verified]** Baseline passed. Both fresh releases matched the archived BEAMs. Two calls returned HTTP 200 with the authorized PAYMENT and one correlated trace each. Payments counted two requests. The Orders transport counted `[1, 2]`. Two response records matched the receipt traces. The first record has `payments.authorize`, attempt 1, the Orders artifact ID and the order request. Both releases exited 0. No capture loss.

**[Verified]** A1 baseline passed. The stub received one request. Orders returned HTTP 200 with the PAYMENT and counted one transport entry. The record bytes equal the sent bytes exactly (`a1_record_bytes_equal_sent_bytes`). This assertion passes now: CAPTURE already keeps raw bytes.

**[Verified]** Replay VM control passed. Without replay data, the same eval harness reached the real transport: HTTP 502 `downstream_failure`, transport 1, one `authorize/2` call and one `connect/4` call. Only `kernel`, `stdlib`, `compiler`, `elixir` and `logger` ran. The loaded `OrdersBeamlSpike` hash equals the run record.

| Assertion | Expected | Actual |
| --- | --- | --- |
| `replay_first_call` | 200, PAYMENT, transport 0, finish 1, `valid_payment!` 1, `authorize/2` 0, `connect/4` 0 | 502, `downstream_failure`, transport 1, finish 0, `valid_payment!` 0, `authorize/2` 1, `connect/4` 1 |
| `replay_a1_noncanonical_body` | Same as `replay_first_call` | Same actual as `replay_first_call` |
| `replay_missing_response` | 502, `missing_response`, transport 0, finish 0, `valid_payment!` 0, `authorize/2` 0, `connect/4` 0 | 502, `downstream_failure`, transport 1, finish 0, `valid_payment!` 0, `authorize/2` 1, `connect/4` 1 |
| `replay_operation_mismatch` | 502, `operation_mismatch`, all counts 0 | Same actual as `replay_missing_response` |
| `replay_attempt_mismatch` | 502, `attempt_mismatch`, all counts 0 | Same actual as `replay_missing_response` |

**[Verified]** This is a genuine behavior RED. All setup, baseline and control assertions passed. Every replay case reached the real router. The router ignores the replay data, calls `authorize/2` and enters the live transport. The refused port then gives `downstream_failure`. The failures show exactly the missing outbound substitution and the missing record checks. The original `responses.jsonl` hash did not change.

**[Verified]** No production file changed. `payment_http.ex` keeps the gate 3 SHA-256 `b0f5bba3…a67f5`.

See the [output](red-output.log), [run result](../../../results/20261106T065754008821Z/result.json), [commands](../../../results/20261106T065754008821Z/commands.json), [toolchain](../../../results/20261106T065754008821Z/toolchain.json), [input hashes](../../../results/20261106T065754008821Z/input-hashes.json), [output hashes](../../../results/20261106T065754008821Z/output-hashes.json), [replay reports](../../../results/20261106T065754008821Z/replay/) and [action events](action-events.jsonl).

## GREEN estimate

**[Proposal]** About 25–40 Elixir lines in two files. No change to Payments, ProbeSupport, the query or the test.

- **`payment_http.ex`.** Move line 40 into `decode/1` and call it from `authorize/2` (review A2). Add `replay/2`: select exactly one record by trace, else `missing_response`. Compare `operation`, `attempt` and `request` with the prepared request. Then call `decode/1` on the Base64 bytes. Do not call `authorize/2`.
- **`router.ex`.** At line 30, call `replay/2` when `conn.private[:beaml_replay]` is set. Reply 502 with the specific error code for a replay evidence error, before `orders.finish`.

## Open questions

- **[Unknown]** Owner review: is a replay branch in the live router acceptable when only `conn.private` can select it?
- **[Unknown]** Error status 502 is a test contract choice. The owner can choose another status before GREEN.
- **[Unknown]** The test cannot show that live and replay call the same decode function. The A1 non-canonical replay shows a real decode of the bytes. The GREEN review must check the shared call.
- **[Unknown]** A3 stays open. The test checks only the `OrdersBeamlSpike` hash and the unchanged release directory. Host decode and validation modules are not bound to the record.
- **[Unknown]** The test does not check `body_sha256` or `status` of the record in replay. Add a digest control only if the owner wants it.

## RED revision 2: separate runner

### Owner decisions (2026-11-06, conversation, German)

- **[Requirement]** No replay branch in the live router. Owner: "wir sollen im echten Router keine Replay-Weiche. Das ist nicht geil." Replay is a debug tool, not an HTTP path.
- **[Requirement]** No HTTP status for replay errors. Replay is not HTTP. A wrong client input is a 400 in HTTP only. The runner returns `{:ok, payment}` or `{:error, reason}`. Reasons: `missing_response`, `operation_mismatch`, `attempt_mismatch`, `body_digest_mismatch`.
- **[Requirement]** Add a body digest check. A tampered body fails with `body_digest_mismatch` before decode, with zero transport entries.
- **[Requirement]** Option A: the runner is a separate module in the Orders app, outside the router. Live `authorize/2` and the runner share one decode and validation function (review A2). The runner does not call `authorize/2`, `connect` or the router. Owner: "let's do it".
- **[Requirement]** Keep A1. A3 stays open as [D002](../../../../../wiki/planning/decisions-to-be-made.md). Fresh Claude Opus 5.5 workers replace GPT-6.1 Sol.

### Contract

**[Proposal]** `OrdersApi.Replay.run(order, trace_id, records)` returns `{:ok, payment}` or `{:error, reason}`.

- **Entry.** `bin/orders eval` of the retained Orders release, after both live releases stop. No application starts.
- **Observer.** BEAM call counts on `OrdersApi.Router.call/2`, `OrdersApi.PaymentHttp.authorize/2`, `:gen_tcp.connect/4`, `OrdersBeamlSpike.prepare/1`, `:json.decode/1`, `OrdersBeamlSpike.finish/1` and `ProbeSupport.valid_payment!/2`. Plus the Orders transport counter (A4: transport entries).
- **Valid record.** Result `{:ok, PAYMENT}` equal to the live receipt body. Prepare, decode, finish and `valid_payment!` once each. Router, `authorize/2`, `connect` and transport zero.
- **Invalid record.** Result `{:error, reason}`. Decode, finish, `valid_payment!`, router, `authorize/2`, `connect` and transport zero. Prepare is not constrained.
- **Digest case.** The first record with other body bytes: same length, other SHA-256, still a valid PAYMENT. Only a digest check rejects it. Decode count zero shows "before decode".

### Scaffolding

**[Verified]** New file `experiments/0002-http-correlation/apps/orders_api/lib/orders_api/replay.ex`, SHA-256 `0b3a531b…92e32`. It holds only `run/3`, which returns `{:error, :not_implemented}`. No logic. Purpose: a behavior RED instead of an undefined-function failure. No other production file changed. `payment_http.ex` keeps `b0f5bba3…a67f5`. `router.ex` keeps `67ce7dc8…6918d`. `mix format --check-formatted` passed on the stub.

### Run

```sh
python3 -B experiments/0003-source-linked-replay/tests/replay_run_test.py
```

Test: `test_separate_runner_replays_first_call_and_rejects_invalid_records` in [replay_run_test.py](../../../tests/replay_run_test.py), SHA-256 `a07034f9…a510f9`. Run serially on loopback.

**[Verified]** Live baseline passed. Fresh releases matched the archived BEAMs. Two HTTP 200 calls returned the PAYMENT with one correlated trace each. Transport `[1, 2]`. Two response records matched the receipt traces. Both releases exited 0. No capture loss.

**[Verified]** A1 baseline passed. The stub got one request. Record bytes equal sent bytes.

**[Verified]** Observer control passed. In the eval VM, `authorize/2` against a refused port raised `MatchError`. Transport 1, `authorize/2` 1, `connect` 1, router 0. Only `kernel`, `stdlib`, `compiler`, `elixir` and `logger` ran. The loaded `OrdersBeamlSpike` hash equals the run record.

| Assertion | Expected | Actual |
| --- | --- | --- |
| `replay_first_call` | `{ok: PAYMENT}`, prepare 1, decode 1, finish 1, `valid_payment!` 1, others 0 | `{error: not_implemented}`, all counts 0 |
| `replay_a1_noncanonical_body` | Same as `replay_first_call` | Same as `replay_first_call` |
| `replay_missing_response` | `{error: missing_response}`, all counts 0 | `{error: not_implemented}`, all counts 0 |
| `replay_operation_mismatch` | `{error: operation_mismatch}`, all counts 0 | `{error: not_implemented}`, all counts 0 |
| `replay_attempt_mismatch` | `{error: attempt_mismatch}`, all counts 0 | `{error: not_implemented}`, all counts 0 |
| `replay_body_digest_mismatch` | `{error: body_digest_mismatch}`, all counts 0 | `{error: not_implemented}`, all counts 0 |

**[Verified]** This is a genuine behavior RED. All setup, baseline and control assertions passed. The runner entry loads and returns a typed result. Every case fails only on the result value and on the missing decision calls. The isolation counts already hold (zero), so GREEN must keep them. The original `responses.jsonl` hash did not change.

**[Inference]** The observer control shows the transport, `authorize/2` and `connect` counters work in the eval VM. It does not show a nonzero `:json.decode/1` count. GREEN valid cases need decode 1, so a dead decode counter fails GREEN. It cannot give a false pass.

See the [output](red-output.log) (revision 2 appended), [run result](../../../results/20261106T074837838124Z/result.json), [commands](../../../results/20261106T074837838124Z/commands.json), [toolchain](../../../results/20261106T074837838124Z/toolchain.json), [input hashes](../../../results/20261106T074837838124Z/input-hashes.json), [output hashes](../../../results/20261106T074837838124Z/output-hashes.json), [replay reports](../../../results/20261106T074837838124Z/replay/) and [action events](action-events.jsonl).

**[Verified]** Limit: the revision 1 test file was replaced in place and was not under version control. Its SHA-256 `d316a542…88f250`, its run directory and its output stay retained. Its text is not retained.

### GREEN estimate

**[Proposal]** About 25–35 Elixir lines in two files. No change to the router, Payments, ProbeSupport or the test.

- **`payment_http.ex`.** Move `:json.decode(bytes)` (line 40) into a public `decode/1`. Call it from `authorize/2` (A2).
- **`replay.ex`.** `run/3`: `valid_order!`, `prepare`, select one record by trace (else `missing_response`). Check `operation` and `attempt`. Check `body_length` and `body_sha256` of the Base64 bytes. Then `PaymentHttp.decode/1`, `finish`, `valid_payment!`. Return `{:ok, payment}`.

### Open questions

- **[Unknown]** Should the runner also compare the record `request` with the prepared request, and the record `status`? The owner list has no reason for them. Not tested.
- **[Unknown]** Should a length-only mismatch have its own case? The digest case keeps the length and changes the SHA-256.
- **[Unknown]** A raised error in the runner (bad order, bad Base64, bad JSON) is reported as `raised`. Should these become typed reasons?
- **[Unknown]** The test cannot show that live and runner call the same decode function. The GREEN review must check the shared call (A2).
- **[Unknown]** A3 / D002 stays open. Only the `OrdersBeamlSpike` hash is checked.

## RED revision 3: status and request checks

### Changes

**[Verified]** The main agent accepted three findings of the [RED review](red-review.md). This revision adds them to the test. All other cases and assertions stay unchanged. The test name stays unchanged.

- **F1.** The harness called `Atom.to_string(reason)` outside the `try`. A non-atom reason crashed the eval and gave `test_setup_failed`. Now a guard `when is_atom(reason)` handles atoms. A fallback clause reports `inspect(reason)`. A non-atom reason is now a reported mismatch, not a crash. [F1](red-review.md#f1--low-fix-before-green-non-atom-error-reason-crashes-the-harness)
- **F2.** The recorded `status` was not checked. A runner that ignored `status` passed. New case `replay_status_mismatch`: the first record with `status` 503, body unchanged. Expected `{error: status_mismatch}`. [F2](red-review.md#f2--medium-owner-decision-recorded-status-is-not-checked)
- **F3.** The record `request` was not compared with the prepared request. New case `replay_request_mismatch`: the first record with `request` `{"order_id": "order-2"}`. Expected `{error: request_mismatch}`. [F3](red-review.md#f3--medium-owner-decision-record-request-is-not-compared-with-the-prepared-request)

**[Proposal]** Both new cases use the invalid-record contract. Decode, finish, `valid_payment!`, router, `authorize/2`, `connect` and transport must be zero. Prepare is not constrained. The runner contract now has six reasons: `missing_response`, `operation_mismatch`, `attempt_mismatch`, `body_digest_mismatch`, `status_mismatch`, `request_mismatch`.

### Run

```sh
python3 -B experiments/0003-source-linked-replay/tests/replay_run_test.py
```

Test: `test_separate_runner_replays_first_call_and_rejects_invalid_records` in [replay_run_test.py](../../../tests/replay_run_test.py), SHA-256 `e38a88cf5a442d698f9e9d4b237ca1c78e8fee384b252d55eb624e0fd2801b94`. Run directory: [results/20261106T075903031507Z](../../../results/20261106T075903031507Z/result.json). Exit code 1. Run serially on loopback.

**[Verified]** All setup, baseline and control assertions passed. All commands exited 0, including the 9 eval runs. Fresh releases matched the archived BEAMs. Two HTTP 200 calls returned the PAYMENT with one correlated trace each. Transport `[1, 2]`. Both releases exited 0. The A1 record bytes equal the sent bytes. The observer control counted transport 1, `authorize/2` 1, `connect` 1, prepare 1 and router 0. Only `kernel`, `stdlib`, `compiler`, `elixir` and `logger` ran. The loaded `OrdersBeamlSpike` hash equals the run record. The original `responses.jsonl` hash did not change during the run.

| Assertion | Expected | Actual |
| --- | --- | --- |
| `replay_first_call` | `{ok: PAYMENT}`, prepare 1, decode 1, finish 1, `valid_payment!` 1, others 0 | `{error: not_implemented}`, all counts 0 |
| `replay_a1_noncanonical_body` | Same as `replay_first_call` | Same as `replay_first_call` |
| `replay_missing_response` | `{error: missing_response}`, all counts 0 | `{error: not_implemented}`, all counts 0 |
| `replay_operation_mismatch` | `{error: operation_mismatch}`, all counts 0 | `{error: not_implemented}`, all counts 0 |
| `replay_attempt_mismatch` | `{error: attempt_mismatch}`, all counts 0 | `{error: not_implemented}`, all counts 0 |
| `replay_body_digest_mismatch` | `{error: body_digest_mismatch}`, all counts 0 | `{error: not_implemented}`, all counts 0 |
| `replay_status_mismatch` | `{error: status_mismatch}`, all counts 0 | `{error: not_implemented}`, all counts 0 |
| `replay_request_mismatch` | `{error: request_mismatch}`, all counts 0 | `{error: not_implemented}`, all counts 0 |

"All counts 0" in the invalid rows excludes prepare, which is not constrained.

**[Verified]** This is a genuine behavior RED. The 6 invalid cases fail only on the result value. The two valid cases fail on the result value and on the missing decision counts (prepare, decode, finish, `valid_payment!`). The isolation counts already hold (zero), so GREEN must keep them.

**[Inference]** The F1 fallback did not run in this RED: the stub returns the atom `not_implemented`. It matters only when GREEN returns a non-atom reason.

**[Verified]** No production file changed. SHA-256 before and after the run: `replay.ex` `0b3a531b…92e32`, `payment_http.ex` `b0f5bba3…a67f5`, `router.ex` `67ce7dc8…6918d`.

See the [output](red-output.log) (revision 3 appended), [run result](../../../results/20261106T075903031507Z/result.json), [commands](../../../results/20261106T075903031507Z/commands.json), [input hashes](../../../results/20261106T075903031507Z/input-hashes.json), [output hashes](../../../results/20261106T075903031507Z/output-hashes.json), [replay reports](../../../results/20261106T075903031507Z/replay/) and [action events](action-events.jsonl).

### Open questions

- **[Unknown]** F4 and F5 move to the GREEN review checklist. See the [disposition](red-review.md#disposition-main-agent-2026-11-06).
- **[Unknown]** The order of checks among the six reasons is not tested. Each derivative changes one field only.

### RED revision 3 check (fresh agent, Devil's Advocate code mode)

**[Verified]** Verdict PASS WITH CHANGES. No critical or high objection. Genuine behavior RED. The ledger matches the run evidence.

**[Proposal]** Disposition (main agent, 2026-11-06): the medium objections move to the GREEN review checklist. They need no new RED round.

- **O1, medium.** The status case uses only 503. A GREEN with a rule like `status >= 400` passes, but then a 201 record replays as ok. Live `authorize/2` accepts exactly 200. GREEN review: the runner accepts exactly status 200.
- **O2, medium.** Generated `prepare/1` is identity, so the request case cannot tell "record request equals the input order" from "record request equals `prepare(order)`". GREEN review: the runner compares the record request with the result of `prepare/1`.
- **O3, low.** A self-contradicting sentence in this section. Fixed.

GREEN review checklist for gate 4: `router.ex` SHA-256 unchanged (F4). Live `authorize/2` and the runner call one shared decode function (F5). Status rule is exactly 200 (O1). Request check uses `prepare/1` (O2).

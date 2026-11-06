# Record the CAPTURE and transport observer RED (0003)

**[Requirement]** This is behavior gate 3 in the [remaining gates](../notes.md). Follow acceptance cases 1 and 4 and the CAPTURE paragraph in the [EXPERIMENT](../../../README.md). REPLAY RUN is a later gate.

**[Verified]** The owner chose fresh Claude Opus 5.5 workers instead of GPT-6.1 Sol. GPT-6.1 Sol is not available in Claude Code.

## Decision

**[Proposal]** Use the [Ponytail Lite](../proposal-lite.md) observer and the [Ponytail Ultra](../proposal-ultra.md) code location. Both put the boundary in `OrdersApi.PaymentHttp`.

- **Counter.** Reuse the existing per-release atomics counter and its `count` field in the Orders control reply. Orders does not use it today.
- **Record.** Write one record per live response with `ProbeSupport.Capture` to a dedicated `responses.jsonl`. The existing capture store bounds it and reports loss.
- **Artifact.** Use the Orders generated BEAM hash as the Orders artifact ID. This matches the Payments artifact ID.
- **Failure control.** Use a separate Orders release with a refused loopback port. Send one invalid order first. It must not reach the transport.

**[Proposal]** Rejected complexity for this gate:

- A new decision module, an Orders module-set digest and a replay archive. The REPLAY RUN gate needs them, this gate does not.
- A peer that accepts and closes. A refused connect is simpler and checks entry before the first socket operation.
- A separate counter field, telemetry or a run ID in the record. The result directory binds the run.

## Record contract

**[Proposal]** The test expects these fields in the first record. It expects one record per receipt, in receipt order.

| Field | Expected value |
| --- | --- |
| `version` | `1` |
| `trace_id` | First receipt trace |
| `client_span_id` | `orders.payment_http` span in that trace |
| `artifact_id` | Orders generated BEAM SHA-256 |
| `operation`, `attempt` | `payments.authorize`, `1` |
| `request` | Prepared request `{"order_id":"order-1"}` |
| `status` | `200` |
| `body_base64`, `body_length`, `body_sha256` | Exact bytes before decode, 1–1024 bytes, JSON equals the authorized PAYMENT |

## Run

Run from the repository root with an offline Mix cache and loopback TCP. Run serially.

```sh
python3 -B experiments/0003-source-linked-replay/tests/response_capture_test.py
```

**[Verified]** Baseline passed. Both fresh releases matched the archived BEAMs. Two calls returned HTTP 200 with the authorized PAYMENT. Each call added one correlated trace. Payments counted two requests. No capture loss. Both releases exited 0.

**[Verified]** Failure control reached the real transport. The invalid order returned 400. The refused connect returned 502 with one `orders.payment_http` span with outcome `error`. The control release exited 0.

| Assertion | Expected | Actual |
| --- | --- | --- |
| `orders_transport_attempts_after_each_call` | `[1, 2]` | `[0, 0]` |
| `response_record_traces` | Receipt 1 and receipt 2 traces | `[]` |
| `observer_control_attempts_invalid_then_refused` | `[0, 1]` | `[0, 0]` |

**[Verified]** This is a genuine behavior RED. All setup and baseline assertions passed. The Orders transport has no counter call and no record before `:json.decode/1`. The three failures show exactly that absence. The first record field checks were not reached because no record exists.

See the [output](red-output.log), [run result](../../../results/20261106T062703346937Z/result.json), [commands](../../../results/20261106T062703346937Z/commands.json), [toolchain](../../../results/20261106T062703346937Z/toolchain.json), [input hashes](../../../results/20261106T062703346937Z/input-hashes.json), [output hashes](../../../results/20261106T062703346937Z/output-hashes.json) and [action events](action-events.jsonl). The [first run](../../../results/20261106T062629075343Z/result.json) had the same three failures before the transport span check was added. The action events cover both runs.

## GREEN estimate

**[Proposal]** Change only `OrdersApi.PaymentHttp`, about 15–25 Elixir lines. Call `ProbeSupport.increment()` before `:gen_tcp.connect`. Write the record after the body read and before `:json.decode/1`. No change to the router, Payments or the query.

**[Verified]** Owner RED review is complete. See CAPTURE GREEN below.

## CAPTURE GREEN

**[Verified]** The owner reviewed the RED and approved GREEN for this gate: "Ja, beide speichern. Let's go." The owner confirmed one response record per live receipt, for both calls. A fresh Claude Opus 5.5 worker did this step. The owner chose this instead of GPT-6.1 Sol.

**[Verified]** One file changed: [`OrdersApi.PaymentHttp`](../../../../0002-http-correlation/apps/orders_api/lib/orders_api/payment_http.ex), 22 lines added, 0 removed.

- **Counter.** `ProbeSupport.increment()` before `:gen_tcp.connect` (line 7). The Payments router is the only other caller. Its count stays per release.
- **Record.** `capture/3` (lines 46–63) writes one `responses` record with `ProbeSupport.Capture.write`. The call is after the body read and before `:json.decode/1` (line 39). Trace and client span come from the current `orders.payment_http` span.
- **Unchanged.** Router, Payments, ProbeSupport, query and the test. The test SHA-256 is `da92ade2…626fc` before and after.

| Assertion | Expected | RED actual | GREEN actual |
| --- | --- | --- | --- |
| `orders_transport_attempts_after_each_call` | `[1, 2]` | `[0, 0]` | `[1, 2]` |
| `response_record_traces` | Receipt 1 and receipt 2 traces | `[]` | Both receipt traces, in order |
| `first_response_record` | Record contract | Not reached | Match |
| `first_response_body` | 1–1024 bytes, authorized PAYMENT | Not reached | Match, 44 bytes |
| `observer_control_attempts_invalid_then_refused` | `[0, 1]` | `[0, 0]` | `[0, 1]` |
| `observer_control_response_records` | `0` | `0` | `0` |

**[Verified]** Regression passed, run serially:

| Command | Exit | Run |
| --- | --- | --- |
| `response_capture_test.py` | 0 | [20261106T063611579325Z](../../../results/20261106T063611579325Z/result.json) |
| `trace_lookup_test.py` | 0 | [20261106T063640182581Z](../../../results/20261106T063640182581Z/result.json) |
| `trace_lookup_repair_test.py --source-run` the run above | 0 | [20261106T063703460086Z](../../../results/20261106T063703460086Z/result.json) |
| 0002 `tests/test_query.py` | 0 | 6 tests OK |
| `mix format --check-formatted` on the changed file | 0 | — |

See the [output](green-output.log), [GREEN result](green-result.json) and [action events](action-events.jsonl). No release build printed a compiler warning.

**[Unknown]** REPLAY RUN, invalid replay records and the malformed `service` parser crash stay open for later gates. A capture write error does not stop the live call. The capture store reports it as loss.

## CAPTURE TEST

**[Verified]** A fresh independent Claude Opus 5.5 tester ran this step. The owner chose this instead of GPT-6.1 Sol. The tester changed no code and no test.

| Check | Exit | Result | Run |
| --- | --- | --- | --- |
| Test SHA-256, all three tests | — | pass | — |
| `response_capture_test.py` | 0 | pass | [20261106T063936223444Z](../../../results/20261106T063936223444Z/result.json) |
| `trace_lookup_test.py` | 0 | pass | [20261106T063955977442Z](../../../results/20261106T063955977442Z/result.json) |
| `trace_lookup_repair_test.py --source-run` the run above | 0 | pass | [20261106T064015898229Z](../../../results/20261106T064015898229Z/result.json) |
| 0002 `unittest discover -s tests -v` | 0 | pass, 8 tests | — |
| `mix format --check-formatted` on the changed file | 0 | pass | — |
| Release builds without a compiler warning | — | pass | — |
| Whitespace check on the changed file | 0 | pass | — |
| Two response records, one per receipt | — | pass | — |
| Output hashes of the three fresh runs | — | pass | — |

**[Verified]** 8 versus 6 tests: no test is lost. Earlier gates used `unittest discover`. It runs `test_query.py` (6 tests) and `test_runner.py` (2 tests). The GREEN worker ran only `tests/test_query.py`. The tester ran both commands: discover 8, `test_query.py` 6.

**[Verified]** Both records have exactly the contract fields. Each record matches its receipt trace, its `orders.payment_http` client span and the Orders BEAM hash. Base64 decodes to 44 bytes. Length and SHA-256 match the bytes. The JSON equals the receipt PAYMENT. The retained copy equals the live `responses.jsonl`. The failure control has 0 records.

**[Inference]** The bytes are predecode. The `capture/3` call is before `:json.decode/1` in the code. The test cannot tell raw bytes from re-encoded bytes with this compact PAYMENT.

**[Verified]** The 0002 directory is not tracked by git. A plain `git diff --check` sees no diff. The tester also checked the file against `/dev/null`: no whitespace error.

See the [test output](test-output.log), [test result](test-result.json) and [tester run](../../../results/20261106T063936155429Z/result.json).

## Owner decisions after review

**[Requirement]** The owner decided these items on 2026-11-06, after the [review](review.md#advisory-items). Approval: "Ja, let's go. Stufe 4. Passt so."

- **A1.** Add the non-canonical body check to the gate 4 RED. A loopback stub returns non-compact JSON. The test compares the exact record bytes.
- **A3.** Do not solve now. Keep it open as [D002](../../../../../wiki/planning/decisions-to-be-made.md#d002--scope-of-the-replay-artifact-identity).
- **Timestamp.** Do not add a timestamp to the response record. The reason is data economy at large volume. The time comes from the span through `trace_id` and `client_span_id`. The span has start and end in Unix nanoseconds since the lookup repair.

**[Inference]** Sampled traces can remove the time of a retained record. This is open as [D003](../../../../../wiki/planning/decisions-to-be-made.md#d003--trace-sampling-and-retained-response-records).

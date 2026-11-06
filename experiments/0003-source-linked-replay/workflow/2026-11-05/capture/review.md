# Review the CAPTURE and transport observer GREEN (0003, gate 3)

**[Verified]** A fresh independent Claude Opus 5.5 reviewer did this step. The owner chose this instead of GPT-6.1 Sol. The reviewer changed no code and no test.

## Verdict

**Pass. No repair needed.** The reviewer found no concrete defect. Four advisory items follow. None blocks this gate.

## Scope check

- **[Verified]** One production file changed. The reviewer removed lines 6–7, 39 and 45–63 from [`payment_http.ex`](../../../../0002-http-correlation/apps/orders_api/lib/orders_api/payment_http.ex). The result has the RED input hash `805de6e3…3ce43`. That is exactly +22/−0.
- **[Verified]** The RED run `20261106T062703346937Z` and the tester run `20261106T063936223444Z` differ in one input hash only: `payment_http.ex`. The current file hash is `b0f5bba3…a67f5`. It matches [test-result.json](test-result.json).
- **[Verified]** The test SHA-256 is `da92ade2…626fc` in RED, GREEN and TEST.
- **[Verified]** Genuine RED, owner RED review and approval, GREEN and independent TEST are in [notes.md](notes.md). The owner decision "one record per live receipt" replaces "first call" in the README CAPTURE paragraph.
- **[Verified]** `OrdersApi.Router` line 30 is the only caller of `PaymentHttp.authorize/2`. The lookup gate and the repair gate passed again in GREEN and in TEST.

## Checked questions

**Predecode.** **[Verified]** `bytes` comes from a raw `:gen_tcp.recv` of exactly `Content-Length` bytes (`payment_http.ex:37-38`). `capture/3` gets these bytes unchanged at line 39, before `:json.decode/1` at line 40. The record holds Base64, length and SHA-256 of the same binary (lines 59–61). See advisory A1 for the test limit.

**Counter placement.** **[Verified]** `ProbeSupport.increment()` (line 7) is the last statement before `:gen_tcp.connect` (line 10). No branch is between them. A raise in `config`, `json` or the header map (lines 3–5) stops the call before both counter and socket. So a count without a connect attempt, or a connect without a count, cannot occur. The refused-connect control shows count 1 and the invalid order shows count 0.

**Shared counter.** **[Verified]** Each release has its own `:atomics` counter in `:persistent_term` (`probe_support.ex:8`). In the Orders release, only `payment_http.ex:7` increments it. In the Payments release, only `payments_api/router.ex:8` increments it. See advisory A4.

**Record binding.** **[Verified]** Trace and client span come from the current span context (`payment_http.ex:48`). The router calls `authorize/2` inside the `orders.payment_http` client span (`router.ex:24-30`). The test matches both receipts to their trace and client span. The record also has `artifact_id`, `operation`, `attempt`, `request` and `status`. **[Inference]** This is enough for gate 4 and gate 5 to reject a changed operation, a changed attempt and a missing record for a receipt trace. `status: 200` is a literal (line 39). It equals the observed status, because line 31 accepts only 200 before line 39.

**Failure semantics.** **[Verified]** A failed write returns `:error` and the live call continues (`capture.ex:10-14`). A file error or an overflow adds `responses` to `loss` (`capture.ex:27-32`). The control reply shows `loss` (`probe_support.ex:118`). The test asserts no loss after each call (`response_capture_test.py:146`). **[Inference]** This agrees with acceptance case 1. "Fail on capture loss" is a run verdict, not a live-call failure. A dead capture process makes the control call fail, so the run fails too. A write timeout returns `:error` without a `loss` entry, but the store still writes the record later. Spans use the same store, so this is not new.

## Advisory items

| ID | Severity | Location | Finding | Minimum action |
| --- | --- | --- | --- | --- |
| A1 | Low | `response_capture_test.py:183-192` | **[Inference]** Payments sends compact JSON with the same `:json.encode`. Re-encoded bytes after decode would be the same 44 bytes. The test cannot show that the bytes are raw. Only the code order shows it. **[Inference]** Gate 4 is not exposed in its result: re-encoded bytes decode to the same term. Only the byte-exact claim is unproven. | Add one check when convenient: point a separate Orders release at a Python loopback stub. Let the stub return a valid but non-canonical body, for example `{ "status" : "authorized", "order_id" : "order-1" }`. Assert that the record bytes equal the stub bytes exactly. |
| A2 | Info, gate 4 input | `payment_http.ex:9-40` | **[Inference]** `authorize/2` joins transport and decode. Gate 4 must use "the same decode and validation path" with zero transport entries. No seam for that exists now. | In gate 4, move the decode at line 40 into one function. Call it from the live path and from replay. Replay must not call `authorize/2`. |
| A3 | Info, gate 4 input | `payment_http.ex:54` | **[Verified]** `artifact_id` is the hash of `OrdersBeamlSpike` only. It covers preparation and finish. It does not cover the decode (line 40) or `valid_payment!` (`router.ex:35`). The notes defer an Orders module-set digest to gate 4. | Decide in gate 4 if replay must also bind the host decode and validation code. |
| A4 | Info | `probe_support.ex:117` | **[Verified]** The control field `count` means "transport entries" in Orders and "handler entries" in Payments. Each release is a separate VM, so the value is not ambiguous. | None. Keep the meaning per service in the gate 4 test text. |

## Not reviewed

**[Unknown]** REPLAY RUN, invalid replay records and the malformed `service` parser crash are out of scope. The README gate table (line 58) still says "Not started". The documentation step owns that update.

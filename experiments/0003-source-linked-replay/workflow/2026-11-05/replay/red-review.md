# RED review: gate 4, revision 2 (separate runner)

**[Verified]** Independent adversarial review of the gate 4 RED, revision 2. Fresh Claude Opus 5.5 worker, 2026-11-06. The reviewer did not run the test. The retained run matches the current files: test SHA-256 `a07034f9…a510f9`, `replay.ex` `0b3a531b…92e32`, `payment_http.ex` `b0f5bba3…a67f5`, `router.ex` `67ce7dc8…6918d` (local `shasum` equals [input hashes](../../../results/20261106T074837838124Z/input-hashes.json)). No code, test or ledger file changed.

## Verdict

**PASS WITH CHANGES.** The RED is a genuine behavior RED and follows the owner decisions. No finding blocks GREEN. One harness fix (F1) is cheap and should go in before GREEN. F2 and F3 need an owner decision on the contract. The rest are GREEN review checks or ledger hygiene.

## Answers

### 1. Genuine behavior RED

**[Verified]** Yes.

- All commands exited 0, including the 7 eval runs ([commands.json](../../../results/20261106T074837838124Z/commands.json)). Failures come only from `check` (test line 103–106, 334).
- Each report has `started` ⊆ base apps and the run artifact ID ([replay/*/report.json](../../../results/20261106T074837838124Z/replay/)). Test line 281–282 passed.
- `trace_pattern` returned 1 for all 7 MFAs (harness line 50 is a hard match). The entry `OrdersApi.Replay.run/3` loads and returns `{:error, :not_implemented}` (`replay.ex:4`).
- Error cases differ from expected only in `result`. Valid cases differ in `result` and in prepare/decode/finish/`valid_payment!` 0 vs 1 ([result.json](../../../results/20261106T074837838124Z/result.json) `assertion_failures`).
- The observer control shows live counters in the eval VM: transport 1, `authorize/2` 1, `connect/4` 1, `prepare/1` 1, router 0 ([control report](../../../results/20261106T074837838124Z/replay/control-transport-observer/report.json)).
- **[Inference]** At RED, the isolation zeros are vacuous (the stub calls nothing). They become meaningful only in the GREEN run.

### 2. Owner decisions

**[Verified]** The test matches all of them.

| Decision | Evidence |
| --- | --- |
| No router replay branch | Runner called directly (harness line 56). Router `call/2` must be 0 (test line 297). See F4 for the structural limit. |
| No HTTP status for replay errors | Report maps only `{:ok,_}`, `{:error,atom}`, raised, other (harness line 61–66). No status field. |
| Typed `{:ok,_}` / `{:error,reason}` | Same. Reasons are the four owner reasons (test line 316–322). |
| Digest before decode | Digest case expects `:json.decode/1` 0 (test line 299, 326). Tampered body has same length, still a valid PAYMENT (test line 312–315). |
| Shared decode with live `authorize/2` | Only indirect: `:json.decode/1` 1 and `valid_payment!` 1. Not enforced, see F5. |
| A1 non-canonical body | A1 record replayed with decode 1 and the live result (test line 309–310). A digest over re-encoded JSON would fail this case. |

### 3. False-pass risks

**[Verified]** Covered by the test:

- **Hardcoded result.** Needs prepare, decode, finish and `valid_payment!` exactly once each (test line 297–300, 307). `valid_payment!` accepts only the exact PAYMENT (`probe_support.ex:37–41`).
- **Skip decode.** Valid cases need `:json.decode/1` 1.
- **Network.** `authorize/2`, `connect/4` and transport must be 0. Payments is stopped and the port is refused (test line 266–268), so no network path can return a PAYMENT.
- **Ignore the trace.** `missing_response` keeps the second record with a valid body and identity (test line 317). A runner that takes any record returns `{:ok,_}` and fails.
- **Digest after decode.** Digest case requires decode 0.
- **Dead `:json.decode/1` counter.** **[Verified]** Local check on Elixir 1.18.1 / OTP 27: `trace_pattern({:json,:decode,1}, true, [:call_count])` counts calls in any process (3 calls, one in a Task, gave 3). **[Inference]** In GREEN, the valid cases need decode 1 in the same run. So a dead counter fails GREEN; it cannot make the digest case pass falsely. The ledger claim (notes line 121) holds.

**[Verified]** Not covered: wrong `status` (F2), wrong `request` (F3), duplicate records for one trace (F6), structural router branch (F4), copied decode instead of shared decode (F5).

### 4. Acceptance cases 4 and 5

- Case 4 "stop both releases", "verify the Orders artifact", "one outbound attempt per live call and zero during replay": covered (test line 214–218, 254, 264, 282, 297).
- Case 4 "substitute the recorded **status** and body": the body is covered; the status is not (F2).
- Case 4 "one matching requested operation and attempt": operation and attempt are covered. The prepared request is not compared with the record `request` (F3).
- Case 5: missing response, operation and attempt identity, specific error before finish, transport 0: all covered (test line 316–326).

### 5. Ledger claims

- **[Verified]** Hashes, counts, control values, started apps, unchanged `responses.jsonl` hash (`b2dccd14…`), and the failure table match the run evidence.
- F7: README gate table still says gate 4 "Not started".

## Findings

### F1 — Low (fix before GREEN): non-atom error reason crashes the harness

**Evidence.** Harness line 63: `{:error, reason} -> %{error: Atom.to_string(reason)}` is outside the `try` (line 51–60). A GREEN that returns a string or tuple reason raises, the eval exits non-zero, `command` asserts (test line 96), and the run logs `test_setup_failed` instead of an assertion mismatch.

**Minimum change.** Guard the clause: `{:error, reason} when is_atom(reason) -> …`. The `other ->` clause then reports it as `unexpected`.

### F2 — Medium (owner decision): recorded status is not checked

**Evidence.** Acceptance case 4 (README line 43) says to substitute the recorded status. Live `authorize/2` accepts only 200 (`payment_http.ex:31`). No derivative changes `status` (test line 316–322). A runner that ignores `status` passes. The ledger lists this as open (notes line 136).

**Minimum change.** After the owner names a reason (for example `status_mismatch`), add `{**records[0], "status": 503}` to `derivatives` with all counts 0. If the owner decides status is out of scope, record that against case 4.

### F3 — Medium (owner decision): record `request` is not compared with the prepared request

**Evidence.** Prepare must run once (test line 307), but its result is not bound to the record. A runner can call `prepare/1` and discard the value. Revision 1's GREEN estimate compared `request` (notes line 82); revision 2 dropped it without an owner reason (notes line 136).

**Minimum change.** After an owner decision, add `{**records[0], "request": {"order_id": "order-2"}}` with a named reason and all decision counts 0.

### F4 — Low (GREEN review): "no router branch" is checked only by behavior

**Evidence.** Router `call/2` 0 proves the runner does not call the router. It does not prove `router.ex` has no replay branch. The input hash is recorded (input-hashes.json) but not asserted.

**Minimum change.** Assert `digest(HTTP / "apps/orders_api/lib/orders_api/router.ex")` equals `67ce7dc8…6918d`, or make the router hash a GREEN review item.

### F5 — Low (GREEN review): shared decode (A2) is not enforced

**Evidence.** A runner with its own `:json.decode/1` call passes. The ledger records this (notes line 139).

**Minimum change.** None for RED. In GREEN review, check that `authorize/2` and `Replay.run/3` call one function (for example `PaymentHttp.decode/1`). Optionally add that MFA to `WATCHED` after GREEN fixes its name.

### F6 — Low: duplicate records for one trace are not tested

**Evidence.** All derivatives have at most one record per trace. The revision 1 decision said "exactly one". A runner that takes the first match of several passes.

**Minimum change.** Optional: add `[records[0], records[0]]` with an owner-named reason, or record "first match wins" as the contract.

### F7 — Low (ledger): README gate status is stale

**Evidence.** README line 59 says gate 4 "**[Unknown]** Not started". The ledger has a confirmed RED revision 2 with owner RED review pending (result.json `status`, `owner_red_review`).

**Minimum change.** Set the row to RED revision 2 recorded, owner RED review pending, with a link to the notes.

## Limits

**[Unknown]** The reviewer did not rerun the test. The `:json.decode/1` counter check ran in a plain `elixir` VM, not in the release eval VM. The GREEN run itself proves the counter in the release VM.

## Disposition (main agent, 2026-11-06)

- **F1, F2, F3.** Accepted into [RED revision 3](notes.md#red-revision-3-status-and-request-checks). New reasons: `status_mismatch`, `request_mismatch`.
- **F4.** Moves to the GREEN review checklist. Check that the `router.ex` SHA-256 stays `67ce7dc8…6918d`.
- **F5.** Moves to the GREEN review checklist. Check that live `authorize/2` and the runner call one shared decode function.
- **F6.** Dropped as low.
- **F7.** Fixed in the [README](../../../README.md) gate table.

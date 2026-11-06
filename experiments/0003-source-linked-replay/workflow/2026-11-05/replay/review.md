# Review: gate 4 REPLAY RUN and invalid replay records (0003)

**[Verified]** Fresh Claude Opus 5.5 reviewer, 2026-11-06. Devil's Advocate checkpoint, code mode (`advocatus-diaboli`). Read only. No test or release ran in this review.

Target: GREEN commit `66e52aa`, RED revision 3 commit `17679a4`. Acceptance cases 4 and 5 of the [EXPERIMENT](../../../README.md).

## Verdict

**PASS WITH CHANGES.** No critical or high objection. Two medium objections go into the ledger as limits. They do not block.

## GREEN review checklist

| Item | Result | Evidence |
| --- | --- | --- |
| F4 `router.ex` unchanged | Pass | SHA-256 `67ce7dc8…6918d` now; last change in commit `1fc2722`; `66e52aa` changes only `payment_http.ex` and `replay.ex` in `apps/` |
| F5 one shared decode | Pass | `payment_http.ex:40` and `replay.ex:16` call `PaymentHttp.decode/1` (`payment_http.ex:47`), the only `:json.decode` call in the two files |
| O1 status exactly 200 | Pass | `replay.ex:12` with strict `expect/3` (`replay.ex:33-34`); live accepts only 200 (`payment_http.ex:31`) |
| O2 request against `prepare/1` | Pass | `replay.ex:6`, `replay.ex:11` |

**[Verified]** Decision path. Live: `valid_order!` → `prepare` → `authorize` (status 200, framing, `decode`) → `finish` → `valid_payment!` (`router.ex:12-35`). Replay: `valid_order!` → `prepare` → record checks → `decode` → `finish` → `valid_payment!` (`replay.ex:5-18`). Same functions in the same order. All evidence checks run before decode (`replay.ex:8-13`). The GREEN run shows decode, finish and `valid_payment!` count 0 in all six invalid cases, and transport, router, `authorize/2` and `connect/4` count 0 in all eight cases (`results/20261106T080316413341Z/result.json`, all 9 assertions expected = actual).

**[Verified]** Ledger claims match the evidence: hashes, the eight assertion values, status `pass`, unchanged test SHA-256 `e38a88cf…2801b94`.

## Objections

### R1 · medium · implementation — the runner does not bind the record to the loaded Orders artifact

- **Claim.** `replay.ex:8-13` never reads `record["artifact_id"]`. Only the test checks the artifact (`replay_run_test.py:225`, `:267`, `:285`). Called on a record from another Orders build, `run/3` decodes it and runs the current `finish/1`.
- **Consequence.** As a debug tool, the runner returns `{:ok, payment}` for a record of a different build with different `finish` logic. That is the gate 3 "other build" failure, moved to replay. Case 4 is met for this gate only because the harness does the check.
- **Smallest fix.** Owner decision: add `expect(record["artifact_id"], ProbeSupport.beam_hash(OrdersBeamlSpike), :artifact_mismatch)` before decode, plus one derivative case. Or record in the ledger Limits that `run/3` trusts the caller for the artifact check. This is narrower than A3 / D002 (module set), which stays open.

### R2 · medium · risk — the body digest check detects inconsistency, not tampering

- **Claim.** `body_sha256` and `body_length` come from the same record as the body (`payment_http.ex:62-64`). `replay.ex:36-40` compares the record with itself. The derivative in `replay_run_test.py:323` changes only `body_base64`.
- **Consequence.** A record edited in all three fields (body, length, SHA-256) replays as `{:ok, …}` with the edited PAYMENT. The owner requirement "A tampered body fails with `body_digest_mismatch`" (`notes.md:78`) holds only for a partial edit. The ledger text at `notes.md:90` reads stronger than the evidence.
- **Smallest fix.** Add a ledger limit: the digest check protects against partial edits only. For real tamper evidence, the caller must compare `responses.jsonl` with the run's retained output hash (`output-hashes.json`) before replay. Owner decides whether that belongs in the runner.

No third objection meets the evidence bar.

## Deliberately not challenged

- **Framing divergence.** Live accepts a body of 1–1024 bytes only (`payment_http.ex:76`). Replay has no size limit. Records come only from accepted live responses, so a larger body needs a forged record. R2 covers forged records.
- **Untyped raises.** An invalid order, bad JSON or a failed `finish` raises in `run/3`. Case 5 demands typed errors only for record evidence, and all those checks precede the raises.
- **Untested check order, duplicate records, O1/O2 only by review.** The ledger already states these limits (`notes.md:273-279`). Code reading confirms O1 and O2.

## Evidence not inspected

`green-output.log`, `commands.json`, the toolchain and input-hash files of the GREEN run, and the RED reviews in detail. The other gate tests (CAPTURE, lookup, repair) were taken from the ledger table, not reopened.

## Disposition (main agent, 2026-11-06)

**[Proposal]** Both objections are medium. They do not block the gate. They are recorded as limits, with no code change.

- **R1.** **[Unknown]** `OrdersApi.Replay.run/3` does not compare the record `artifact_id` with the loaded build. Only the test harness checks the build. This belongs to the open decision [D002](../../../../../wiki/planning/decisions-to-be-made.md#d002--scope-of-the-replay-artifact-identity). A runner check `:artifact_mismatch` waits for D002.
- **R2.** **[Unknown]** The digest check detects a body that does not match its own record. It does not detect an edit of body, length and SHA-256 together. It is an integrity check, not tamper protection. Tamper protection needs a digest from outside the record, for example the run output hashes.

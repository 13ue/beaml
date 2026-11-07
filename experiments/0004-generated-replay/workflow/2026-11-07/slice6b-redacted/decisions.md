# Decisions: slice 6b step 6 (`redacted`, `with`, RESPONSE RECORD projection)

**[Proposal]** PLAN phase, 2026-11-07. Design decisions that DL-105 and the decision log do not settle.
Classes follow Decision4. Undo and Repair entries give the default that the sub-step worker takes. Migrate and Answer entries are OWNER questions.
Every entry carries a `By:` line (DL-107). OWNER questions get `By: 13ue` when they are answered.
A sub-step worker records each taken default again in its `notes.md` (DL-097).

## OWNER questions

### Q6B-10 · Migrate · The GEN arm and the 0003 RESPONSE RECORD contract (blocks 6a)

- **Context.** **[Verified]** GEN runs copies of the 0003 tests with a fixed change table (`tests/overlay_diff_test.py`, `arms/gen/assertion-changes.json`, README "0003 lines that change"). **[Verified]** LIB is frozen (`arms/lib/freeze.json`) and its `replay_lib.ex` stores the raw body. **[Verified]** These GEN copy lines read the raw body: `response_capture_test.py` l. 180-192; `replay_run_test.py` l. 227, 262-263, 312-323 and the stub record writer (`stub/responses.jsonl`). **[Inference]** DL-105 removes the raw body from every GEN record, so these lines and the change table must change. The cases `replay_a1_noncanonical_body` and `replay_body_digest_mismatch` lose their byte meaning.
- **Option A.** GEN copies get new change rows in projection form. LIB stays frozen on the raw body. The arm result states that GEN and LIB now store different record contracts. `a1` becomes "key order does not matter"; the digest case tampers `value`.
- **Option B.** The arm comparison stops at 6a. Its slice 1 to 5 results stay retained evidence. `run.py` and `arms_test.py` keep only the GEN-only replay and type cases; the 0003 copy run and `overlay_diff_test.py` leave the check list.
- **Option C.** LIB stays frozen as its own record version. The GEN copies keep their test names. The record-byte lines (`body_length`, `body_sha256`, the a1 non-canonical body, the body tamper) become "not applicable" rows. The arm comparison then compares outcomes and call counts only. Cheaper than A (no new meaning for a1); keeps more than B.
  By: Opus (PLAN REPAIR, slice6b-redacted), from plan check PC6R-3.
- **Why Migrate.** It changes the evidence base of EXPERIMENT 0004 (the GEN against LIB claim) and the frozen comparison rule of the README.
- **What it blocks.** Only the GEN copy run and `overlay_diff_test.py`. The 6a RED and GREEN on `slice6_record_test.py` and the other record tests can start before the answer.
  By: Opus (PLAN REPAIR, slice6b-redacted), from the plan check order note.
- By: open, decided later by `13ue`. Question by Opus (PLAN, slice6b-redacted).

### Q6B-11 · Migrate · A field that becomes `redacted` while stored records hold its value (blocks 6b GREEN of R7 and R8)

- **Context.** Plan review O1, plan check O2. **[Inference]** After 6a, old records hold the value of a field that becomes redacted. Two places:
  - **Input case.** An EFFECT input field (the DL-089 case `Order.card_holder`). The value is in the record `request`. **[Verified]** The record `type` key and the `--stored` check hold the output TYPE only; the input TYPE has no fingerprint in the record. Without a check the build passes, and every old record gives `:request_mismatch` at replay.
  - **Output case.** An EFFECT output field. The value is in the record `value`.
- **Interim (Repair, D6B-72).** `--stored` counts stored values under a now-redacted field, in `request` and in `value`, and blocks. This holds under every option below. The block has no exit in 6b.
- **Part 1, detection (absorbs D6B-66).**
  - **Option 1A.** `redacted` is part of the TYPE VERSION fingerprint: the field TYPE text is `redacted String` (old D6B-66). An output field that becomes redacted makes a new TYPE VERSION. Challenge: the input case still needs D6B-72; a fingerprint change is a stored-record change.
  - **Option 1B.** `redacted` is not part of the fingerprint (D6B-30). Only the D6B-72 value check blocks. Challenge: the TYPE VERSION does not show the change; the exit then cannot name a new TYPE VERSION.
- **Part 2, exit.**
  - **Option 2A.** A MIGRATE CHANGE `redact f`. The REPLAY RUN removes and marks the old value at read, in `request` and in `value`. The old value stays in the store until a `retire` keep window ends.
  - **Option 2B.** No MIGRATE CHANGE. The only fates are those of DL-102 for the old TYPE VERSION: `retire` with a keep window or `quarantine`. Challenge: an input field has no TYPE VERSION in the record.
- **Why Migrate.** Stored records and retention of PII (DL-029). Plan check PC6R-2 (D6B-66 raised).
- By: open, decided later by `13ue`. Question by Opus (PLAN, slice6b-redacted). Input case, Part 1, interim: Opus (PLAN REPAIR, slice6b-redacted).

### Q6B-14 · Migrate · How a REPLAY RUN shows a marked field (was D6B-62, blocks 6b GREEN of R5)

- **Context.** DL-105: a redacted field replays "as absent and marked". **[Inference]** The atom makes the field present with a non-String value in a String field. Host replay code that matches `is_binary` takes another branch than live.
- **Option A.** The atom `:redacted` in the field. `__beaml_valid__` accepts it only for a redacted field. Challenge: host code sees a value that live never gives; a pure step that computes with it may raise (L3).
- **Option B.** The key is absent, and the result carries the `redacted` list. Challenge: the result is not TYPE-valid by today's `__beaml_valid__`; host code needs a second check.
- **Why Migrate.** Generated behaviour that the OWNER and host code see (plan check PC6R-2).
- By: open, decided later by `13ue`. Question by Opus (PLAN REPAIR, slice6b-redacted).

### Q6B-15 · Migrate · Interim limit: `redacted` output only on a top-level String field (was D6B-63, blocks 6b GREEN of R6)

- **Context.** DL-105 superseded D6B-34 because a compile error forbids a basic feature. **[Inference]** DL-102 cannot run a rule over a value that the record does not have, and a constructor would get the marker as input.
- **Option A.** Compile error for every other redacted output field: `error: redacted field F of T in an EFFECT output must be a String field of a TYPE without a constructor (slice 6b)`. Challenge: a new interim compile error on a basic feature.
- **Option B.** Any field TYPE. The REPLAY RUN and the DL-102 check skip the rules of a marked field. Challenge: a constructor or enum rule over that field is not checked at replay.
- **Why Migrate.** A syntax limit that the OWNER must accept (plan check PC6R-2).
- By: open, decided later by `13ue`. Question by Opus (PLAN REPAIR, slice6b-redacted).

### Q6B-12 · Answer · A direct copy of a redacted value into a non-redacted field of a non-failure TYPE (does not block)

- **Evidence.**
  - **[Verified]** DL-105 names only failure TYPES: "A failure TYPE may carry a redacted field only when that field is `redacted` there too."
  - **[Verified]** DL-089 (R3) strips redacted fields from the EFFECT input unless `with` names them.
  - **[Inference]** `fn prepare Order { card_holder } -> Receipt = Receipt { holder: card_holder }` with a non-redacted `holder` sends the value on the wire of an EFFECT that takes `Receipt`, without `with`. Spans and records then also hold it.
  - **[Inference]** The check code is the same as the 6c failure rule, applied to every record literal and variant payload.
  - **[Verified]** DL-029: values derived by a branch are PII; implicit flow is a target, not the next slice.
  - **[Unknown]** How many real flows copy a PII field into another TYPE on purpose (for example a display name).
- **Option A.** The 6c compile error applies to every record literal and variant payload, not only failure values.
- **Option B.** Failure TYPES only now (DL-105 text). Other direct copies wait for the flow check.
- **Challenges.** A: stricter than the OWNER text; legal copies need a `redacted` mark on the target. B: a one-step copy bypasses R3 until the flow check exists.
- **Interim.** 6c builds the DL-105 text (failure TYPES only). No recommendation.
- By: open, decided later by `13ue`. Evidence by Opus (PLAN, slice6b-redacted).

### Q6B-13 · Answer · A redacted input field and a same-named plain output field of the same EFFECT (blocks 6b GREEN of R4c)

- **Evidence.**
  - **[Verified]** DL-089: spans, logs and records never hold the value of a redacted field.
  - **[Verified]** DL-105: the output TYPE protects the record; `value` holds the declared non-redacted fields.
  - **[Inference]** `type Order { card_holder: redacted String }` as input and `type Receipt { card_holder: String }` as output. A service that echoes the input puts the value into `value` (D6B-54). The live result carries it to the host. No compile signal today.
  - **[Inference]** The same name does not prove the same value. A service may return a different holder string on purpose.
  - **[Unknown]** How many real EFFECTS return an input PII field under the same name.
- **Option A.** Compile error.
- **Option B.** Compile warning; the build passes.
- **Option C.** Allowed. The OWNER declares the output field plain, and the record holds the value.
- **Challenges.** A: blocks a legal display field; a different name bypasses it. B: a warning does not stop a stored value, which cannot be taken back (DL-029). C: the record holds a value that the input marks as PII.
- **No recommendation** (Answer class).
- By: open, decided later by `13ue`. Evidence by Opus (PLAN REPAIR, slice6b-redacted), from plan check O3.

## Superseded and kept entries of the slice 6b plan

- D6B-29 kept. D6B-31 kept. D6B-32 kept (two projections). D6B-33 kept for the wire body and `request`; the output uses the `redacted` list (D6B-55).
- D6B-30 stays until Q6B-11 Part 1 is answered (D6B-66 raised to Migrate, plan check PC6R-2). D6B-34 superseded by DL-105. D6B-37 "the record keeps the raw body" superseded by DL-105; its `unknown_fields` part stays (step 7 S4).
- By: Opus (PLAN, slice6b-redacted).

## Undo and Repair defaults

Format: **ID · class · decision.** Chose / Over / Because / Commits us to (Repair only). By.

### Order and test changes

**D6B-52 · Repair · 6a runs after steps 7 and 8 GREEN, and adapts every record test in one pass.**
Chose: 7, 8, then 6a, 6b, 6c. Over: 6a first. Because: the step 7 and 8 RED files hold reviewed raw-body fixtures; one pass changes all record tests once. Commits us to: steps 7 and 8 GREEN write raw-body code that 6a replaces in `emit_effect`. The change of the old tests is Repair: our own contract, pre-production, except the GEN copies of 0003 (Q6B-10).
By: Opus (PLAN, slice6b-redacted).

### RESPONSE RECORD version 2 (6a)

**D6B-53 · Repair · Key set of version 2.**
Chose: `version: 2`, `trace_id`, `client_span_id`, `artifact_id`, `operation`, `attempt`, `request`, `status`, `value`, `redacted`, `unknown_keys`, `value_sha256`, `type`, plus `unknown_fields` if step 7 keeps it. `body_base64`, `body_length`, `body_sha256` go. Over: other names; a nested `projection` object. Because: DL-105 sketch names; flat keys keep the existing readers simple. Commits us to: every record reader names `value`.
By: Opus (PLAN, slice6b-redacted).

**D6B-54 · Repair · `value` holds the wire values under the declared keys, not the decoded value.**
Chose: `Map.take` of the declared keys of the newest TYPE VERSION, nested by DL-099 and D6B-49, not validated, redacted keys removed. `null` when the body is not a JSON object. Over: the decoded typed value (variant tuples, structs). Because: DL-102 runs today's rules over stored values: a non-String `7` must still block, and an enum constructor needs its inputs (`status`, `decline_reason`) to run again. DL-105 "a decode change cannot be replayed against an old raw body" then means that undeclared keys are lost. Commits us to: `value` can hold an invalid declared value; the replay decode rejects it as today.
By: Opus (PLAN, slice6b-redacted).

**D6B-55 · Repair · `redacted` lists the redacted fields that were present and valid at write time.**
Chose: sorted names; a missing or invalid redacted field is not listed. Over: list every redacted declared field. Because: the replay then gives the same `decode` reject as live for a missing or wrong redacted value. Commits us to: the record shows "was there and valid", never the value.
By: Opus (PLAN, slice6b-redacted).

**D6B-56 · Repair · `unknown_keys` keeps its meaning and is now also written for a body that fails the decode.**
Chose: sorted names of all keys outside `value` and `redacted`, dotted for nested keys (step 8 S8). Over: `[]` on a failed decode (today). Because: the projection is one function, independent of validity; names are allowed (DL-105). Commits us to: a failed record can show key names.
By: Opus (PLAN, slice6b-redacted).
Repair amendment: a dotted name per level, also below an undeclared key whose value is an object. An echo `{"echo": {"order_id": .., "card_holder": ..}}` gives `echo`, `echo.card_holder`, `echo.order_id`. Because: step 8 S8 names; plan check O3 (R4 expectation). Commits us to: names of every level, never values.
By: Opus (PLAN REPAIR, slice6b-redacted).

**D6B-57 · Repair · The same projection for every status.**
Chose: a 503 body is projected like a 200 body. Over: no `value` for non-200. Because: one rule; the REPLAY RUN checks `status` before it reads `value`. Commits us to: an error body keeps only declared keys of the output TYPE.
By: Opus (PLAN, slice6b-redacted).

**D6B-58 · Repair · Digest `value_sha256` and the reason name.**
Chose: lower-case hex SHA-256 of the compact JSON of `{"redacted": .., "unknown_keys": .., "value": ..}`, keys sorted at every level, UTF-8, non-ASCII not escaped (Python: `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False)`). The generated code sorts explicitly. A mismatch keeps the reason `:body_digest_mismatch`. Over: a new reason name; a digest over the whole record. Because: the six 0003 reasons and the `EIGHT_CASES` names stay; `type` and `request` were never under the body digest. Commits us to: a parity check (6a P5); the reason name says "body" for a projection.
By: Opus (PLAN, slice6b-redacted).

**D6B-59 · Repair · A record whose `version` is not `2` blocks the build at `--stored`; the REPLAY RUN keeps `:body_digest_mismatch` as a second guard.**
Chose: `stored_version` reads the record key `version`. Any value other than `2` (also a missing key) is a build error: `error: stored RESPONSE RECORD has record version V; this build reads record version 2 only (DL-105)` and `  record source: S:N (line N)` (the existing `at` line). For a missing key V is `none`. Over: a replay reason only (old D6B-59); a reader for raw-body records. Because: plan check O1: a record that the build cannot read must block (DL-031, DL-040); `:body_digest_mismatch` alone also states tampering, which is false. Commits us to: one more `--stored` error text; 6a test P6.
By: Opus (PLAN, slice6b-redacted). Build rule and text: Opus (PLAN REPAIR, slice6b-redacted).

**D6B-60 · Repair · The replay decode reads `value` through the existing decode path.**
Chose: re-encode `value` with `:json.encode` and call the same decode (versioned or slice 1 form), with the `redacted` list as an extra input (6b). The replay span `unknown_keys` is the sorted union of the record `unknown_keys` and the stray keys the decode finds in `value`. Over: a second decode for maps. Because: one decode path; the arm counts keep `":json.decode/1": 1`; hand-built records with keys of another TYPE VERSION (C11, C12, D11b, D11c) keep their meaning. Commits us to: a hand-built `value` may hold keys that the writer never writes.
By: Opus (PLAN, slice6b-redacted).

**D6B-61 · Undo · In 6a `request` stays the full input.** No field is redacted before 6b.
By: Opus (PLAN, slice6b-redacted).

**D6B-68 · Undo · One test helper `with_value(record, value, unknown_keys=(), redacted=())` in `tests/stored_types_test.py`.** It sets `version: 2`, removes the body keys and recomputes `value_sha256`. It replaces `arms_test.with_body`, `slice4_retire_test.with_body` and the inline builder of `slice5_syntax_test.make_record`.
By: Opus (PLAN, slice6b-redacted).

**D6B-69 · Repair · Convert the stored fixtures in place.**
Chose: a one-off script in the 6a ledger rewrites `stored/v1.jsonl`, `stored/v1-v2.jsonl`, `slice6/decode/stored*.jsonl`, `slice6/decode-ctor/stored*.jsonl` to version 2 (value by the record's own TYPE VERSION fields). Git history keeps the old form. Over: new file names beside the old ones. Because: every test reads these paths; `raw/` immutability does not cover fixtures. Commits us to: old result directories name fixture hashes that no longer match HEAD.
By: Opus (PLAN, slice6b-redacted).

### `redacted` and `with` (6b)

**D6B-62 · raised to Migrate, now Q6B-14 (plan check PC6R-2).** The text below is option A there. No worker takes it as a default.
By: Opus (PLAN REPAIR, slice6b-redacted).
Original entry: A marked field replays as the atom `:redacted`.
Chose: the REPLAY RUN puts `:redacted` in each field of the `redacted` list; `__beaml_valid__` accepts it only for a redacted field. Over: drop the key (breaks TYPE validity of the result); a placeholder String (looks like a real value). Because: JSON never decodes to an atom, so live and replay values cannot be confused; DL-105 "absent and marked". Commits us to: host replay code sees `:redacted`; a pure step that computes with it may raise (plan L3).
By: Opus (PLAN, slice6b-redacted).

**D6B-63 · raised to Migrate, now Q6B-15 (plan check PC6R-2).** The text below is option A there. No worker takes it as a default.
By: Opus (PLAN REPAIR, slice6b-redacted).
Original entry: in an EFFECT output TYPE, `redacted` only on a top-level `String` field of a TYPE without a constructor.
Chose: an enum, constructor or record field, or a field of a constructor TYPE (DL-101, DL-106), gives `error: redacted field F of T in an EFFECT output must be a String field of a TYPE without a constructor (slice 6b)`. Over: any field TYPE. Because: DL-102 cannot run a rule over a value it does not have, and a constructor would get `:redacted` as input. Commits us to: a redacted enum or Amount output waits for a later step.
By: Opus (PLAN, slice6b-redacted).

**D6B-64 · Undo · Text: `error: redacted stands only before a field TYPE in a type (D6B-29)`** for an enum payload, a signature line and a MIGRATE CHANGE.
By: Opus (PLAN, slice6b-redacted).

**D6B-65 · Undo · `with` texts.** `error: with names F, which is not a field of T`; `error: with names F, which is not a redacted field of T`; `error: with names F twice`. T is the EFFECT input TYPE. `with` concerns the input only.
By: Opus (PLAN, slice6b-redacted).

**D6B-66 · raised to Migrate, folded into Q6B-11 Part 1 as option 1A (plan check PC6R-2).** No worker takes it as a default. D6B-72 is the interim block.
By: Opus (PLAN REPAIR, slice6b-redacted).
Original entry: `redacted` is part of the TYPE VERSION fingerprint (replaces D6B-30).
Chose: the field TYPE text in the `type` key and in the fingerprint is `redacted String`. Over: D6B-30 (not part). Because: with the projection the stored shape changes (the value is not in `value`), so the old reason "the data shape does not change" is false now; a field that becomes redacted then blocks a build with stored records of the old form (existing check, DL-031). Commits us to: the block has no exit in 6b until Q6B-11 is answered; TYPES without `redacted` keep their fingerprints.
By: Opus (PLAN, slice6b-redacted).

**D6B-72 · Repair · `--stored` blocks on a stored value under a field that is now `redacted`, in `request` and in `value`.**
Chose: for each record, take the EFFECT of its `operation`. Count the records whose `request` holds a key that is redacted in the input TYPE, and whose `value` holds a key that is redacted in the output TYPE, at any depth of the declared fields. One error per TYPE, operation, field and place, with count and first line, never the value (DL-032): `error: TYPE T: N stored RESPONSE RECORDS of operation OP hold a value of the redacted field F in P` (P is `request` or `value`), the `record source` line, and `  help: these records hold a value that is now redacted; their fate is an OWNER decision (Q6B-11)`. Over: block by the fingerprint only (D6B-66). Because: plan check O2: the input TYPE has no fingerprint in the record, so an input field that becomes redacted passes the build and keeps PII (DL-029, DL-031). The check holds under every Q6B-11 option. Commits us to: `--stored` reads `request`; the block has no exit in 6b; test R8.
By: Opus (PLAN REPAIR, slice6b-redacted).

**D6B-70 · Undo · Echo test MARKER.** `MARKER-` plus a random hex string per run, passed by environment variable only. The loopback stub keeps the received request and its response in memory. The RUN DIRECTORY holds the generated module, beams, stub files, the harness script, stdout and stderr, `responses.jsonl`, the span and event dumps. The scan covers every file there and `.beaml/actions.jsonl`.
By: Opus (PLAN, slice6b-redacted).
Repair amendment (plan check O3): the harness stubs `:otel_span.set_attribute` so that it appends its arguments to a file in the RUN DIRECTORY. The scan looks for the MARKER in plain text, in base64 at the three byte offsets (the MARKER after 0, 1 and 2 prefix bytes, boundary characters cut) and in lower-case hex. The scan self-check plants all three forms.
By: Opus (PLAN REPAIR, slice6b-redacted).

**D6B-71 · Repair · Redaction helpers work on the plain map form.**
Chose: one generated helper per TYPE with redacted fields (`Map.drop` at each depth); a struct input of a constructor TYPE (DL-106) goes through `Map.from_struct/1` first. Over: a struct-aware drop. Because: the wire encode and the `request` compare already use maps. Commits us to: if the DL-106 step lands first, the 6b worker adds this one call.
By: Opus (PLAN, slice6b-redacted).

### Failure TYPE rule (6c)

**D6B-67 · Repair · What counts as a direct copy into a failure value.**
Chose: a variable bound to a redacted field by a record pattern (any pattern depth), used unchanged as (a) a field value of a record literal of the failure TYPE or of a record literal nested in it, where that field is not `redacted`; (b) a variant payload of a failure enum; (c) the whole clause body when its TYPE is the failure TYPE. `+`, calls and pipes are derived values and are not checked. A whole record of a TYPE with a redacted field is legal (the TYPE keeps the mark). Text: `error: fn N copies the redacted field F of T into G of the failure TYPE E, which is not redacted` and `  help: mark G as redacted in E, or do not copy the value (DL-105)`; for (b) and (c) `... into the failure TYPE E, which cannot hold a redacted value`. Over: a flow check through calls. Because: DL-105 names the failure TYPE rule and puts derived values later. Commits us to: a one-step `+ ""` bypasses the rule (test F5 records it).
By: Opus (PLAN, slice6b-redacted).

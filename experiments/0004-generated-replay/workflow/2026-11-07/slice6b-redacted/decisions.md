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
- **Why Migrate.** It changes the evidence base of EXPERIMENT 0004 (the GEN against LIB claim) and the frozen comparison rule of the README.
- By: open, decided later by `13ue`. Question by Opus (PLAN, slice6b-redacted).

### Q6B-11 · Migrate · A field that becomes `redacted` while stored records hold its value (does not block 6b)

- **Context.** Plan review O1. **[Inference]** After 6a, old records of that TYPE hold the value in `value` and in `request`. The interim D6B-66 puts `redacted` into the fingerprint, so the build blocks with the existing `--stored` error. The help line then asks for a MIGRATE STEP that 6b cannot write.
- **Option A.** A MIGRATE CHANGE `redact f`. The REPLAY RUN removes and marks the old value at read. The old value stays in the store until a `retire` keep window ends.
- **Option B.** No MIGRATE CHANGE. The only fates are those of DL-102 for the old TYPE VERSION: `retire` with a keep window or `quarantine`.
- **Why Migrate.** Stored records and retention of PII (DL-029).
- By: open, decided later by `13ue`. Question by Opus (PLAN, slice6b-redacted).

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

## Superseded and kept entries of the slice 6b plan

- D6B-29 kept. D6B-31 kept. D6B-32 kept (two projections). D6B-33 kept for the wire body and `request`; the output uses the `redacted` list (D6B-55).
- D6B-30 replaced by D6B-66. D6B-34 superseded by DL-105. D6B-37 "the record keeps the raw body" superseded by DL-105; its `unknown_fields` part stays (step 7 S4).
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

**D6B-57 · Repair · The same projection for every status.**
Chose: a 503 body is projected like a 200 body. Over: no `value` for non-200. Because: one rule; the REPLAY RUN checks `status` before it reads `value`. Commits us to: an error body keeps only declared keys of the output TYPE.
By: Opus (PLAN, slice6b-redacted).

**D6B-58 · Repair · Digest `value_sha256` and the reason name.**
Chose: lower-case hex SHA-256 of the compact JSON of `{"redacted": .., "unknown_keys": .., "value": ..}`, keys sorted at every level, UTF-8, non-ASCII not escaped (Python: `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False)`). The generated code sorts explicitly. A mismatch keeps the reason `:body_digest_mismatch`. Over: a new reason name; a digest over the whole record. Because: the six 0003 reasons and the `EIGHT_CASES` names stay; `type` and `request` were never under the body digest. Commits us to: a parity check (6a P5); the reason name says "body" for a projection.
By: Opus (PLAN, slice6b-redacted).

**D6B-59 · Repair · A version 1 record (raw body, no `value`) gives `:body_digest_mismatch`.**
Over: a reader for raw-body records. Because: DL-105 "stored nowhere"; the pre-production store holds only fixtures, which 6a converts. Commits us to: no replay of an unconverted old record.
By: Opus (PLAN, slice6b-redacted).

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

**D6B-62 · Repair · A marked field replays as the atom `:redacted`.**
Chose: the REPLAY RUN puts `:redacted` in each field of the `redacted` list; `__beaml_valid__` accepts it only for a redacted field. Over: drop the key (breaks TYPE validity of the result); a placeholder String (looks like a real value). Because: JSON never decodes to an atom, so live and replay values cannot be confused; DL-105 "absent and marked". Commits us to: host replay code sees `:redacted`; a pure step that computes with it may raise (plan L3).
By: Opus (PLAN, slice6b-redacted).

**D6B-63 · Repair · In an EFFECT output TYPE, `redacted` only on a top-level `String` field of a TYPE without a constructor.**
Chose: an enum, constructor or record field, or a field of a constructor TYPE (DL-101, DL-106), gives `error: redacted field F of T in an EFFECT output must be a String field of a TYPE without a constructor (slice 6b)`. Over: any field TYPE. Because: DL-102 cannot run a rule over a value it does not have, and a constructor would get `:redacted` as input. Commits us to: a redacted enum or Amount output waits for a later step.
By: Opus (PLAN, slice6b-redacted).

**D6B-64 · Undo · Text: `error: redacted stands only before a field TYPE in a type (D6B-29)`** for an enum payload, a signature line and a MIGRATE CHANGE.
By: Opus (PLAN, slice6b-redacted).

**D6B-65 · Undo · `with` texts.** `error: with names F, which is not a field of T`; `error: with names F, which is not a redacted field of T`; `error: with names F twice`. T is the EFFECT input TYPE. `with` concerns the input only.
By: Opus (PLAN, slice6b-redacted).

**D6B-66 · Repair · `redacted` is part of the TYPE VERSION fingerprint (replaces D6B-30).**
Chose: the field TYPE text in the `type` key and in the fingerprint is `redacted String`. Over: D6B-30 (not part). Because: with the projection the stored shape changes (the value is not in `value`), so the old reason "the data shape does not change" is false now; a field that becomes redacted then blocks a build with stored records of the old form (existing check, DL-031). Commits us to: the block has no exit in 6b until Q6B-11 is answered; TYPES without `redacted` keep their fingerprints.
By: Opus (PLAN, slice6b-redacted).

**D6B-70 · Undo · Echo test MARKER.** `MARKER-` plus a random hex string per run, passed by environment variable only. The loopback stub keeps the received request and its response in memory. The RUN DIRECTORY holds the generated module, beams, stub files, the harness script, stdout and stderr, `responses.jsonl`, the span and event dumps. The scan covers every file there and `.beaml/actions.jsonl`.
By: Opus (PLAN, slice6b-redacted).

**D6B-71 · Repair · Redaction helpers work on the plain map form.**
Chose: one generated helper per TYPE with redacted fields (`Map.drop` at each depth); a struct input of a constructor TYPE (DL-106) goes through `Map.from_struct/1` first. Over: a struct-aware drop. Because: the wire encode and the `request` compare already use maps. Commits us to: if the DL-106 step lands first, the 6b worker adds this one call.
By: Opus (PLAN, slice6b-redacted).

### Failure TYPE rule (6c)

**D6B-67 · Repair · What counts as a direct copy into a failure value.**
Chose: a variable bound to a redacted field by a record pattern (any pattern depth), used unchanged as (a) a field value of a record literal of the failure TYPE or of a record literal nested in it, where that field is not `redacted`; (b) a variant payload of a failure enum; (c) the whole clause body when its TYPE is the failure TYPE. `+`, calls and pipes are derived values and are not checked. A whole record of a TYPE with a redacted field is legal (the TYPE keeps the mark). Text: `error: fn N copies the redacted field F of T into G of the failure TYPE E, which is not redacted` and `  help: mark G as redacted in E, or do not copy the value (DL-105)`; for (b) and (c) `... into the failure TYPE E, which cannot hold a redacted value`. Over: a flow check through calls. Because: DL-105 names the failure TYPE rule and puts derived values later. Commits us to: a one-step `+ ""` bypasses the rule (test F5 records it).
By: Opus (PLAN, slice6b-redacted).

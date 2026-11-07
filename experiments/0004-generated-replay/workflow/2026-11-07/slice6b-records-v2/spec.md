# Slice 6b step 6a: RESPONSE RECORD version 2 (the projection)

**[Proposal]** SOLVE / RED, 2026-11-07. Ledger of sub-step 6a of the [step 6 plan](../slice6b-redacted/plan.md#sub-step-order).
By: Opus (RED, slice6b-records-v2). The plan names the ledger `slice6b-record/`; the task names `slice6b-records-v2/` (notes.md R1).

## Concern

Every RESPONSE RECORD becomes version 2. The raw body is stored nowhere (DL-105). No `redacted` field exists yet (6b).

## Contract (from the plan, D6B-53 to D6B-61)

- Writer keys: `version: 2`, `trace_id`, `client_span_id`, `artifact_id`, `operation`, `attempt`, `request` (unchanged, D6B-61), `status`, `value`, `redacted: []`, `unknown_keys`, `value_sha256`, `type`, and `unknown_fields` where step 7 writes it.
- `value`: the wire values under the declared keys of the newest TYPE VERSION, nested by DL-099 and D6B-49. Not validated. `null` when the body is not a JSON object (D6B-54). The same rule for every status (D6B-57).
- `unknown_keys`: sorted names of the other keys, dotted per level, also for a body that fails the decode (D6B-56).
- `value_sha256`: lower-case hex SHA-256 of the compact JSON of `{"redacted", "unknown_keys", "value"}`, keys sorted at every level, UTF-8, non-ASCII not escaped (D6B-58).
- `body_base64`, `body_length`, `body_sha256` go (DL-105).
- REPLAY RUN: the checks keep their order and reasons. The body check becomes the digest check of the projection; a mismatch stays `:body_digest_mismatch`. A record without `value` gives `:body_digest_mismatch` (second guard). The decode re-encodes `value` and uses the existing decode path (D6B-60). The replay span `unknown_keys` is the sorted union of the record `unknown_keys` and the stray keys in `value`.
- `--stored`: a record whose `version` is not `2` is a build error (D6B-59, plan repair O1). Text:
  `error: stored RESPONSE RECORD has record version V; this build reads record version 2 only (DL-105)` and `  record source: S:N (line N)`. A missing key gives `V` = `none`.
- `--stored` DL-102 checks read `value`, not the body.
- The record keeps the request side unchanged (D6B-61). DL-115 (`:redacted` in a REPLAY RUN) is 6b; the record shape keeps the key `redacted` for it.

## Check list change (DL-110, Q6B-10 option B)

The GEN against LIB comparison ends with 6a. The 0003 copy run and `overlay_diff_test.py` leave the check list of `run.py` and `arms_test.py`. Slice 1 to 5 results stay retained evidence. README text for the docs phase: [readme-change.md](readme-change.md).

## Tests

- New: `tests/slice6_record_test.py` (P1 to P6, a1). Fixture `slice6/record/stored-v1.jsonl` (the version 1 record of `stored/v1.jsonl` before the conversion).
- Adapted: `tests/arms_test.py`, `tests/slice2_replay_test.py`, `tests/slice3_replay_test.py`, `tests/slice4_retire_test.py`, `tests/slice5_syntax_test.py`, `tests/stored_types_test.py`, `tests/slice6_decode_test.py`, `tests/slice6_decode_ctor_test.py`, `run.py`.
- Converted fixtures (D6B-69, script [convert_fixtures.py](convert_fixtures.py)): `stored/v1.jsonl`, `stored/v1-v2.jsonl`, `slice6/decode/stored*.jsonl`, `slice6/decode-ctor/stored*.jsonl`.
- Every changed assertion and its class: [notes.md](notes.md#changed-assertions).

## Acceptance (GREEN)

- `slice6_record_test.py` passes.
- Every adapted test file passes with only the listed changes.
- `payments.generated.snapshot` stays byte-equal. Every existing reject keeps its message.

# Decisions: RECORD FORMAT v3 (EXPERIMENT 0005 prerequisite P2)

**[Proposal]** PLAN phase, 2026-11-07. Design decisions that DL-143 and the decision log do not settle.
Classes follow Decision4. Free run (DL-144): every Migrate question has a built default marked `(default, open)`; "big" marks a record format detail. The OWNER signs each off one by one (DL-139 sign-off rule). The same list stands in [owner-review.md](../../../../0005-prototype-fullstack/workflow/2026-11-07/owner-review.md#record-format-v3-p2).
ID check: no `RV3-` or `QV3-` ID existed in the repository at this plan (git grep).

## Migrate questions (built defaults, open)

### QV3-1 · Migrate · big · The marker of the record format

- **A (default).** The key `version` with the value `3`, as v1 and v2.
- **B.** A new key `format` (for example `"beaml.record/3"`); `version` goes.
- **C.** The file name (`responses.v3.jsonl`).
- **Because A.** The D6B-59 reader keeps one key and one text form. C is lost in a database row (Q5-10 B). Challenge: `version` can be misread as a TYPE VERSION; that stays `type.version`.
- → By: Opus (PLAN record-v3, default, open)

### QV3-2 · Migrate · big · The span id key

- **A (default).** One core key `span_id` (client span for HTTP, root server span for UI, client span for db).
- **B.** Keep `client_span_id` and `server_span_id` as transport extras; the core has none.
- **C.** `span_id` plus `span_kind` (`"client"`, `"server"`).
- **Because A.** DL-143 puts "a span id" in the core; one name lets one reader join records to spans. The kind is in the trace itself. Challenge: a reader of the file alone cannot tell the kind; C adds it with one key.
- → By: Opus (PLAN record-v3, default, open)

### QV3-3 · Migrate · big · Where the transport extras stand

- **A (default).** Flat top-level keys (`status`, `request`), as today.
- **B.** Nested under one key (`transport: {status, request}`).
- **Because A.** The REPLAY RUN keeps `record["status"]` and `record["request"]`; no hunk in `Replay.run/3`. Challenge: a generic reader cannot list the extras without the stream; B makes the core set exact.
- → By: Opus (PLAN record-v3, default, open)

### QV3-4 · Migrate · big · `outcome` and `reason` of a RESPONSE RECORD

- **A (default).** Written at capture: `status != 200` gives `rejected`/`"status"`; a 200 body that fails the decode gives `rejected`/`"decode"` or `rejected`/`"constructor"`; else `accepted`/`null`. The record `reason` equals the live failure `reason`.
- **B.** Status only (the DL-136 wording): 200 gives `accepted`, other gives `rejected`/`"status"`; a decode failure stays `accepted`.
- **Because A.** Parity with the ENTRY RECORD (DL-138): a reject at capture is no TYPE change. Challenge: `--stored` then skips a 200 record that failed at capture, which DL-136 did not name; a looser constructor later is not seen on it.
- → By: Opus (PLAN record-v3, default, open)

### QV3-5 · Migrate · big · Old v1 and v2 files

- **A (default).** One-time rewrite of the tracked v2 fixtures (`convert_v3.py`); `--stored` reads version 3 only, the D6B-59 form with `3` and DL-143.
- **B.** The reader accepts v2 and v3 and derives `outcome` from `status` for v2.
- **Because A.** DL-143 says one shape; the v2 step used the same pattern (D6B-69); no live v2 data exists outside retained runs (0005 starts after P2). Challenge: a retained `results/*` record cannot be fed to `--stored` again without the script.
- → By: Opus (PLAN record-v3, default, open)

### QV3-6 · Migrate · big · What `value_sha256` covers

- **A (default).** Unchanged D6B-58: `redacted`, `unknown_keys`, `value`.
- **B.** Also `unknown_fields`, `outcome`, `reason`.
- **Because A.** No stored digest changes, the converter stays a key rename, the REPLAY RUN `digest/3` keeps its bytes. Challenge: an edited `outcome` is not detected and `--stored` trusts it.
- → By: Opus (PLAN record-v3, default, open)

### QV3-7 · Migrate · When the RESPONSE count line prints

- **A (default).** `N records, K checked, M not replayable` only when M > 0.
- **B.** Always when the file has a record (parity with the ENTRY line).
- **Because A.** No existing stderr assertion moves (about 30 stderr checks read `--stored` builds over 200 fixtures). Challenge: it reads DL-136 ("prints one count line") narrowly; a clean file shows no proof that the check ran.
- → By: Opus (PLAN record-v3, default, open)

### QV3-8 · Migrate · What a rejected RESPONSE RECORD skips

- **A (default).** Only the value checks: DL-102 constructors and DL-122 literals (the 6d `check_entries` rule). The TYPE path check, the redacted-held check and the orphan count read every record.
- **B.** Also the TYPE path check and the W2 version count.
- **Because A.** Parity with 6d; the redacted-held check is a privacy check and must read every record. Challenge: an old 503 record of a TYPE VERSION without a path still blocks, which DL-136 ("only replayable records are checked") would skip.
- → By: Opus (PLAN record-v3, default, open)

## Repair and Undo

**RV3-01 · Repair · P2 changes record keys and the `outcome` reader only.**
Chose: the core keys, the extras, `outcome`/`reason` on the RESPONSE RECORD, the version reader and the skip of rejected records. Over: also the DL-136 digest half, the db writer. Because: P5-18 (record keys only, M8 and M9 untouched); one concern per step. Commits us to: P2b for the digest half.
→ By: Opus (PLAN record-v3)

**RV3-02 · Undo · `value` of a RESPONSE RECORD stays the DL-105 projection of the decoded JSON body.**
Chose: no raw body, no `body_base64` mapping. Over: the raw body in `value`. Because: DL-105 (OWNER) settled it; v2 already writes it. Undo: no change in P2.
→ By: Opus (PLAN record-v3)

**RV3-03 · Repair · `unknown_fields` is written in every record (`[]` without a keep-value variant).**
Chose: an exact key set per stream. Over: the step 7 conditional key. Because: DL-142 and DL-143 put both lists in the core; the reader already treats an absent key as `[]`. Commits us to: every EFFECT output changes `record/3` bytes (inside the allowed hunk).
→ By: Opus (PLAN record-v3)

**RV3-04 · Repair · The REPLAY RUN reads no new key.**
Chose: `Replay.run/3`, `body/1`, `digest/3`, `Replay.entry/2` keep their bytes; the status check stays (HTTP extra). Over: a `version` or `outcome` check in the REPLAY RUN. Because: the replay recomputes the outcome from the data; the diff proof then has one allowed function per writer. Commits us to: a v2 record still replays (limit).
→ By: Opus (PLAN record-v3)

**RV3-05 · Undo · The DRIVER does not change.**
Chose: no edit. Because: it reads no record key (observed).
→ By: Opus (PLAN record-v3)

**RV3-06 · Repair · `--stored` checks the ENTRY RECORD version too.**
Chose: `stored ENTRY RECORD has record version V; this build reads record version 3 only (DL-143)`. Over: no check (6d). Because: one shape for every stream; a v2 entry with `server_span_id` must not pass silently.
→ By: Opus (PLAN record-v3)

**RV3-07 · Repair · The DL-136 digest half is a follow-up step P2b.**
Chose: P2 skips only `rejected` records; a bad-digest record is still checked. Over: a Rust D6B-58 digest in P2. Because: the digest is a read-time fact, not a record key; it needs a canonical JSON writer in Rust and covers both streams. Commits us to: DL-121 parity for bad-digest records waits for P2b. Not a change of DL-136, a deferral.
→ By: Opus (PLAN record-v3)

**RV3-08 · Undo · `convert_v3.py` lives in this ledger and runs once.**
Chose: the D6B-69 pattern. Over: a converter in `run.py`. Because: one-time use.
→ By: Opus (PLAN record-v3)

**RV3-09 · Repair · Five pin sites, not four.**
Chose: the 6d N13 `BASE` in `slice6_entry_test.py` moves with the four sites of the byte-pin note. Over: four sites. Because: N13 compares every source without an ENTRY LINE against the pre-6d compiler; every EFFECT output changes in P2, so N13 fails if its base stays. Commits us to: the re-pin prompt lists five sites.
→ By: Opus (PLAN record-v3)

**RV3-10 · Undo · The new test file is `tests/record_v3_test.py`.**
Chose: one file for V1 to V17. Over: edits inside `slice6_record_test.py` only. Because: the v2 step kept its own file; changed v2 assertions are listed by name.
→ By: Opus (PLAN record-v3)

**RV3-11 · Undo · The version texts cite DL-143.**
Chose: `(DL-143)` instead of `(DL-105)`. Because: DL-143 sets the one format.
→ By: Opus (PLAN record-v3)

**RV3-12 · Repair · The converter derives the v2 RESPONSE outcome from `status` only.**
Chose: 200 gives `accepted`/`null`; other gives `rejected`/`"status"`. Over: running the decode over each fixture. Because: the capture-time rule of a fixture is unknown (many fixtures stand for records captured under an older, looser rule); every fixture is 200, so every `--stored` result stays. Commits us to: limit "a converted 200 record that failed at capture is accepted".
→ By: Opus (PLAN record-v3)

**RV3-13 · Repair · `record/3` computes `outcome` itself from `status` and the decode.**
Chose: one `case` inside `record/3` over `@parent.__beaml_decode_E(bytes)`. Over: passing the result of the live call into `record/3`. Because: the live EFFECT function then keeps its bytes; the decode is already called there for keep-value outputs. Commits us to: one more decode per 200 call for other outputs.
→ By: Opus (PLAN record-v3)

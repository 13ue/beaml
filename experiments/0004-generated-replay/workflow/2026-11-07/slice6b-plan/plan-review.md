# Plan review: slice 6b compiler plan

**[Proposal]** Fresh-context PLAN CHECK, 2026-11-07. Not a Devil's Advocate round. No production file changed.
Read: `plan.md`, `plan.json` (not in full), `decisions.md`, DL-062, DL-065, DL-070, DL-071, DL-080 to DL-097, and `experiments/0001-syntax-to-beam/src/main.rs` at the named places.

## Verdict

**BLOCK steps 6 and 7. Steps 0 to 5 can start.** Two high objections touch stored records and privacy. One medium objection touches step 10.

## Objections (max three)

### O1 · high · D6B-30, D6B-32 and D6B-38 change stored-record behaviour, but the plan classes them Repair

- **Wrong outcome.** D6B-38: a new ENUM LITERAL does not change the TYPE VERSION. A replay of an old record then gives a different variant (`Unknown("refunded")` becomes `Refunded`). No drift reject fires. The replay no longer shows what production did.
- **Wrong outcome.** D6B-30 with D6B-32: a field becomes `redacted` without a TYPE VERSION change. Old RESPONSE RECORDS still hold the value in `request`. Either every old record gives `request_mismatch`, or the compare strips both sides and the stored PII stays silently. Both are OWNER-visible results on stored records and privacy (DL-029).
- **Class.** Migrate, by the check rule (stored records, privacy). DL-097 says a step stops at the first Migrate question.
- **Smallest test.** (a) Record `"state": "refunded"` under an enum without `Refunded`. Add `Refunded = "refunded"`. Replay. Observe the variant and any reject. (b) Record a request with `card_holder`. Mark the field `redacted`. Replay. Observe `request_mismatch` and the bytes of the store.
- **Fix in the plan.** Add OWNER questions for D6B-38 and for D6B-30/D6B-32 (old records with a now-redacted value). Block steps 6 and 7 on them.

### O2 · high · Step 6 can pass while RESPONSE RECORDS hold a redacted value

- **Wrong outcome.** The RESPONSE RECORD stores the raw body (`body_base64`, observed in `emit` of `Replay.record`). D6B-34 rejects only declared output fields. A service that echoes `card_holder` in an undeclared key stores it raw. The key name also goes into `unknown_keys`. DL-089 "records never hold the value" is then false.
- **False pass.** The step 6 stub captures the request only. If it does not echo, the "marker not found in the run directory" check passes.
- **Smallest test.** The loopback stub echoes the full request body in its response. Assert that the marker is not in any file of the run directory.
- **Fix in the plan.** Add the echo case to the step 6 test. Add this evidence to Q6B-4 (Answer): the compiler cannot know undeclared keys, so option A does not protect the stored body.

### O3 · medium · D6B-43 is safe except for `type T v1` without a chain

- **Wrong outcome.** **[Verified]** `versioned()` is true when a TYPE has a mark or a chain (`main.rs`, near line 1690). D6B-43 removes `v1` with no chain. The decode of an EFFECT output TYPE then changes from the versioned form to the slice 1 form. `fmt` changes generated behaviour.
- **False pass.** Invariant D6B-45 (f) catches it only with a fixture. Step 10 case (c) has no `type T v1` fixture without a chain.
- **Smallest test.** Fixture: `type Payment v1 { ... }` as EFFECT output, no chain. Run `fmt`. Compare the compiled output.
- **Fix.** Keep a `v1` mark without a chain. Or add the fixture and let the test decide.

## Answers to the five checks

### (1) Defaults against the decision log

- No default contradicts a DL entry in its decided text.
- Raise to Migrate (one line each):
  - **D6B-38.** Replay of stored records changes its result without a TYPE VERSION change (O1).
  - **D6B-30.** Marking a field `redacted` leaves PII in old records and needs no MIGRATE STEP (O1).
  - **D6B-32.** The replay compare of old records with a now-redacted value is an OWNER choice (O1).
  - **D6B-43.** It reads an OWNER Migrate text against its words. Send it as an OWNER question (see (3)).
- Note, not raised:
  - D6B-15. `new_<TYPE>_<k>` becomes the host-visible API. Reversible while no host calls it.
  - D6B-23. The key-subset check also rejects a signature that code calls can reach (larger arity). DL-087 speaks of "always matches first"; for code calls that is not true. Medium.
  - D6B-16. Two signatures with equal TYPES and other names: code always calls the first. The second is reachable only by decode. Not a contradiction.

### (2) Step order

- **Hidden dependency, step 3 on step 5.** **[Verified]** Today every pipe body sets `spans` and emits `ProbeSupport.span` per step (`main.rs` near lines 1832 and 2946). Step 3 (`wrap = n |> NonZeroInt`, module without EFFECTS) expects a plain `with`. That is D6B-28, which the plan puts in step 5. The step 3 worker must move D6B-28 forward, or the runtime check fails. Move D6B-28 to step 3 in the plan.
- Step 7 on step 6 is a file-conflict order, not a logic dependency. Correct as stated.
- No other step depends on a later one.

### (3) DL-081 contradiction and D6B-43

- The contradiction is real. The literal text ("removes a mark ... when there is no chain") also contradicts DL-070 ("version numbers only grow") and DL-071 (`--remove-dead` writes the mark).
- The safe reading keeps `newest_version` stable in every case. It is safe for stored records, except `v1` without a chain (O3).
- **Send it to the OWNER now as Q6B-5, Migrate.** It reinterprets an OWNER decision. Step 10 is the last step, so the question blocks nothing before it.

### (4) OWNER questions

- **Q6B-1.** The two options are real. Add: under option A, a change from literals to a constructor changes the wire key (`state` to `status`). Under option B, D6B-49 `unknown_keys` reads nested keys.
- **Q6B-2.** Real. Nothing missing.
- **Q6B-3.** Real. The interim D6B-19 is the smallest safe state.
- **Q6B-4.** Add the echo evidence (O2). Without it, option A looks safer than it is.
- **Missing.** Questions for D6B-38, D6B-30/D6B-32 (O1) and D6B-43 (Q6B-5).

### (5) First failing tests, steps 0 to 3

- **Step 0.** The clippy loop at line 3039 is in the difflib port (`matching_blocks`). The byte-equal compile of three sources does not run it. Name the difflib parity test (DL-067) in the step 0 check.
- **Step 1.** Genuine for the first source. The two reject cases fail today too (`expected expression or pattern`, `unknown type: Int`). Assert the message text (`non-exhaustive function: f`, `type mismatch`), not only "is an error".
- **Step 2.** Today `-> String ! String` gives `unknown type: String`. That names `String`. Assert the D6B-09 text ("is also a failure TYPE"), not "names String".
- **Step 3.** Today the source fails with `invalid function name: NonZeroInt`. That names the constructor. "Names the constructor" passes today and after a wrong fix. Assert a message part specific to the record-literal rule. Keep each reject in its own source, so that the first error is the tested one.

## Limits

- `plan.json` was not checked line by line against `plan.md`.
- `run.py` and the replay tests were not run. All findings are from reading.
- The replay compare code (`request_mismatch`) was not read in detail. O1 names both possible outcomes for that reason.

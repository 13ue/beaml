# Slice 6b step 8: REVIEW (fresh context)

Target: [spec.md](spec.md), [notes.md](notes.md) (S1 to S15, R1 to R5, GREEN G1 to G11, P1 to P11), [red-review.md](red-review.md), plan step 8, D6B-48 to D6B-50, DL-084, DL-085, DL-099, DL-101, DL-102, DL-106, DL-109, the diff `git diff 078bbf6f..8924cb3f` of `main.rs`, `tests/slice6_decode_ctor_test.py` and `tests/slice6_struct_order_test.py`.
Normal review, not a Devil's Advocate round. HEAD `8924cb3f`. TEST evidence: [test-output.log](test-output.log), [test-result.json](test-result.json). No code or test was changed.

**Verdict: PASS for the step.** P11 is a real false pass of the DL-102 block (D1, high for the slice). It is recorded in the ledger as a `ponytail:` limit. It must close before slice 6b closes.

## Step met

- **[Observed]** `slice6_decode_ctor_test.py` 8 of 8, `slice6_constructor_test.py` 25 of 25, `slice6_struct_order_test.py` 3 of 3 at HEAD (TEST).
- **[Verified]** `__beaml_from_T` is a `cond` over the signatures in source order (DL-085). An object signature needs every key with a valid String; a one-parameter signature reads the field value (DL-099 B). A constructor failure gives `:constructor`; no match gives `:error` (D6B-48).
- **[Verified]** `ctor_keeps` gives the D6B-50 error when the last clause of a signature does not put a bound String input into a keep-value variant.
- **[Verified]** The `--stored` check (`ctor_fault`) picks the first matching signature and the first matching clause. A failure TYPE body gives the DL-102 block line; no signature gives the `no signature` line.
- **[Observed]** D6B-19 stays for the output TYPE itself, the input and a failure TYPE (step 3 tests pass). D6B-40 is a plan decision; its test was written and seen RED before the code (green-output.log).

## Adversarial probes (scratch, HEAD binary, exact output)

The probes reuse the step 8 fixture. Records are copies of `stored.jsonl` line 1 with a new body, body length, body hash and trace id. Probe 7 uses the fingerprint rule of `slice3_types_test.type_version`.

| # | Source and records | Result |
|---|---|---|
| 6 | P11: `fn Amount value, c -> Amount ! NoCurrency = value \|> cur \|> Amount`, `cur ""` fails with `NoCurrency`, a second signature `fn Amount value: String -> Amount`. Stored record `amount: {"value":"","currency":"EUR"}`. | `--stored`: **exit 0, empty stderr (false pass).** Runtime decode of the same body: `{:error, %BeamlSpike.PaymentError{reason: "constructor"}}`. Control record `currency: ""` (literal failure clause): exit 1, `1 stored RESPONSE RECORD ... fails the constructor of Amount for field amount with NoCurrency`. |
| 7 | `Payment { order_id amount: Amount fee: Fee }`, both constructors have the parameter `value`. 3 records: both fail, only `fee` fails, none fails. | exit 1, two messages: `1 ... fails the constructor of Amount for field amount with NoCurrency` and `2 ... fail the constructor of Fee for field fee with Zero`, each `record source: ...:1`. Runtime: stray keys `["amount.note", "fee.currency"]` (each field has its own declared names); `fee` failure gives `constructor`; missing key gives `decode`. |
| 8a | `Money { amount: Amount }` with `fn Money amount: Amount -> Money`, field `money: Money` | exit 1, `effect payments.authorize: slice 1 decodes String fields only, not Payment.money` (S4, G10). |
| 8b | Plain record `Wrap { amount: Amount }`, field `w: Wrap` | exit 1, `effect payments.authorize: slice 1 decodes String fields only, not Payment.w`. |
| 9 | Stored records with an array: `state: ["ok",""]`, `amount: ["1","EUR"]`, `state.status: ["ok"]` | exit 1: `1 ... matches no signature of Amount for field amount` (line 2) and `2 ... match no signature of PaymentState for field state` (line 1). Runtime: each body gives `{:error, %BeamlSpike.PaymentError{reason: "decode"}}`. |

## Defects

### D1 · high for the slice, not for the step · P11: the `--stored` check passes a record that the runtime rejects

- **Wrong outcome.** Probe 6: a constructor whose failure is reached only through a pipe step passes `--stored`. A REPLAY RUN of that record then gives the reject `constructor`. DL-102 (OWNER, Migrate) says such a record blocks the build.
- **Why PASS for the step.** The spec cases pass. G7 records the limit; the code has a `ponytail:` comment; P11 is open in notes.md. No fixture of the step reaches it.
- **Must close before slice 6b closes: yes.** The DL-102 block is the safety check of this slice. A silent pass gives a replay failure later.
- **Class: Repair.** The check is compiler code before production. A fix reverses with one change.
- **Minimum repair.** In `effects()`, reject at compile time a constructor field TYPE whose clause body is a pipe with a failing step. Text in the D6B-50 form. Add probe 6 as the RED. Later: evaluate the pipe in `ctor_fault`.

### D2 · low · G9 has no test

- The D6B-39 text for a constructor field in a versioned TYPE is a new error path. No test asserts it. Add one `assert_rejected` case.

### D3 · low · Stale texts

- spec.md "Files" says 7 tests; GREEN has 8 (G2).
- DL-109 says `unknown_fields` is written "only for literal outputs". Step 8 also writes it for constructor enum fields (S5, G5). Update the DL-109 text or link S5.

## Consistency of RED, reviews and GREEN

- **[Observed]** RED 6 tests 6 FAIL; RED repair 7 of 7 FAIL plus the step 3 case (24 of 25); GREEN 8 OK (7 and D6B-40); TEST 8 of 8. Constructor 25 of 25 in GREEN and TEST.
- **[Observed]** red-review objection 1 closed by R1, objection 2 by the struct-order mini-step R5 and G3, objection 3 by R2. The P1 class change (Migrate to Repair, by the main agent) is recorded in S6, P1 and R4.
- **[Observed]** GREEN struct-order 3 (2 and P2) agrees with TEST.

## Decisions

| # | Class | Decision | By |
|---|---|---|---|
| RV1 | Repair | **Chose:** PASS for the step with D1 open. **Over:** BLOCK the step. **Because:** the limit is recorded (G7, P11, `ponytail:` comment) and no step case reaches it. **Commits us to:** P11 closes before slice 6b closes. | Opus (REVIEW, slice6b-decode-constructor) |
| RV2 | Repair | **Chose:** class P11 as Repair. **Over:** Migrate. **Because:** it changes no OWNER rule; it makes the compiler follow DL-102. | Opus (REVIEW, slice6b-decode-constructor) |
| RV3 | Undo | D2 and D3 are low. They do not block. | Opus (REVIEW, slice6b-decode-constructor) |

## Limits

- The probe files are in the scratch directory only. The runtime probes use the step 7 stubs, not a release.
- Probe 6 is one form of P11. An enum constructor with `!` (P9) was not probed.

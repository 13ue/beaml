# RED review: P2b (DL-164, a wrong digest blocks the build)

**[Verified]** Fresh RED review, 2026-11-08, HEAD `53aed354` (RED commit). By: Opus (RED REVIEW P2b). Normal fresh
review, not Devil's Advocate. No test or production change, no commit.
Inputs: [plan.md](plan.md) with Repairs, [plan-review.md](plan-review.md), [red-plan.md](red-plan.md),
[red-output.md](red-output.md), DL-164.

## Verdict

**GO for GREEN.** No critical or high objection. Two medium notes, one ledger correction.

## Re-run at HEAD

Commands: `git archive HEAD experiments/0001-syntax-to-beam` into scratch, `cargo build --offline`,
`BEAML_SPIKE=<scratch>/…/beaml-spike python3 -B tests/<file>.py`. rustc as in red-output; Elixir 1.18.1 / OTP 27.

| File | Ran | Fail | Skip | Fails |
|---|---|---|---|---|
| `slice6_db_stored_test.py` | 54 | 6 | 3 | R1, R2, R2b, R5, R6, N25 control |
| `record_v3_test.py` | 28 | 7 (subtests) | 1 | R3 [valid, constructor, held], V14, V14c, V22, V23 |
| `slice6_entry_test.py` | 22 | 2 (subtests) | 0 | R4 [valid, value_faults] |
| `stored_types_test.py` | 33 | 0 | 0 | none |

→ 15 failures, all planned. All guards pass (G1 in three files, N21, N29 rest, V15 and the others).
→ Ledger correction: red-output.md has the `Ran` column permuted (it says 28 / 33 / 22 / 54). Fail counts are right.

## Each RED: genuine, for the planned reason

→ **R1, R2, R6** rows: exit 0, no error; HEAD folds `!digest_holds` into `continue`. R6 rationale holds:
  generated `row_order/1` (gen.ex) reads `type`, `body(core)`, version; it never reads `outcome`.
→ **R2b**: exit 0, the STRICTER constructor never runs; expected digest error only.
→ **R3**: valid = exit 0 with Elixir; constructor = DL-102 text; held = D6B-72 text. Exactly the planned reasons.
→ **R4**: valid = exit 0; value_faults = the DL-122 ENUM LITERAL text.
→ **R5**: `0 checked, 1 not decodable` against expected `1 checked, 0 not decodable`. Rust writes `\u000b`.
→ **V14, V14c, V22, V23, N25 control**: the extra line `digest not verified (P2b)`.
→ No import, setup or syntax failure. Expected texts come from `st.digest_error`, not from a compiler.

## Against DL-164 and the Repairs

→ **Erlang upper-case `\u` hex**: R5 pin verified independently. I emitted `slice6/db/orders.beaml` with the HEAD
  compiler, ran its `digest/3` under `elixir` over `:json.decode` of `CONTROL`: `8dd130c3c0a2…151a` = `ERLANG_DIGEST`.
→ **Helper vs emitter, wider**: same `digest/3` vs `st.value_sha256` on `\b \f \x7f U+2028 / é 😀`, a literal
  backslash-`u00ab`, `\x00 \x1f \n \t \r " \\`: all four values equal. The digest output itself is lower case on both
  sides (`Base.encode16(..., case: :lower)`, `hexdigest()`).
→ **Self-consistency risk of the helper change**: low. The regex only touches `\uXXXX` escapes, which Python writes
  only for control characters without a short form. Only one Python canonical helper exists (`rg`). The R5 helper
  guard anchors it to a real emit, so the helper cannot drift with Rust.
→ **Digest error first and alone**: R2 (off-chain fingerprint), R2b (constructor), R3 constructor/held, R4
  value_faults each compare the full error lines exactly. A path or value text beside it fails the test.
→ **Every row of a read TYPE, whatever its outcome**: R6 (`rejected` row blocks) plus G1 (no-reader INVOICE row
  counted). Both directions pinned.
→ **Block tests and empty stdout**: not a false-pass risk. Rows compare the exact list of non-count lines; R3 and R4
  compare the exact stderr minus count lines. `stdout == ""` is one field beside the exact text.

## Objections (max three)

1. **Medium: grouping and plural untested.** Every block case has one bad item (`count` = 1). A GREEN that writes one
   message per row, or the wrong first line, passes. Plan section 4 decides "one message per (TYPE, place)".
   ⠀⠀↳ Smallest test: two bad rows of ORDERS at lines 2 and 3 → `2 stored ROWS … have`, `rows.jsonl:2 (line 2)`.
   ⠀⠀↳ Not blocking. Main decides: small RED repair before GREEN, or record as a known gap.
2. **Medium: rejected RESPONSE RECORDS reach `body/1` at run time.** [Verified] generated `run/4` for `orders.save`,
   `orders.load`, `orders.list` (slice6/db) and the http run (decode-ctor) call `body(record)` before the outcome is
   used. So a rejected record with a wrong digest builds green and fails at run time with `:body_digest_mismatch`.
   This is the R6 rationale, but Repairs O3 keeps records at "checked items only", and G1 (record) pins that.
   ⠀⠀↳ Not a RED defect: the ruling is explicit and open. Put it on the OWNER card with O1 / O3.
   ⠀⠀↳ Smallest test if the OWNER widens: the G1 record case flips to the digest error.
3. **Low, dropped**: the retired-entry G1 checks only `"error" not in stderr`. Enough for a guard.

## Limits

→ R5 covers rows only. Records and entries reach the same Rust `digest_holds` per the plan; no RED pins that GREEN
  uses the shared function for them with a control character. [Inference] low risk, one shared function.
→ 0005 N15 is not in this RED (GREEN per DL-158). Not reviewed here.

## Decisions

**Undo**
→ Verified the R5 pin by a live `elixir` emit, not by reading red-plan. By: Opus (RED REVIEW P2b)
→ Objection 3 dropped as low. By: Opus (RED REVIEW P2b)

**Repair**
→ GO over "repair first", because no high objection and every RED fails for the planned reason. By: Opus (RED REVIEW P2b)
→ Objection 2 to the OWNER card over a RED change, because Repairs O3 ruled it explicitly. By: Opus (RED REVIEW P2b)

**Migrate (OWNER chooses)**
→ Rejected RESPONSE RECORDS: keep "checked only" (built) or verify every record that reaches `body/1`.

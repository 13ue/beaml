# RED review: M4 step 1, lift D6B-39, migrate first

**[Observed]** RED review (normal, fresh context, not Devil's Advocate), 2026-11-08, HEAD `850b52ee`, `main.rs` unchanged.
Target: the RED of [red-plan.md](red-plan.md) and [red-output.md](red-output.md) against [plan.md](plan.md) (with "Plan repair
after plan check") and DL-152 / DL-153. By: Opus (RED review m4-lift).

## Evidence (re-run by this review)

- HEAD debug `ce7cd3d6…6f34`, HEAD release `b3f60ef3…5d01`: `slice6_m4_test.py` exit 1, 12 tests, 13 failures, every one on a D6B-39 text.
- Depth probe rebuilt in scratch (`git archive HEAD`, only the two `output_fields` D6B-39 branches deleted): sha256
  `f916fe6f…a0e5`, equal to red-output.md. Same 11 failures and the same `got` terms (`decode`, `got R8: :error`).
- Probe generated `__beaml_decode_order/2` and `__beaml_decode_payment/2` read by hand: per-version list holds
  `{"channel","Channel"}`, `{"amount","Amount"}` (and `PaymentState`), `Map.put(note)` after the check, no literal map or
  constructor call. The test fingerprints (`ORDER_V1 7f3dba23…`, `ORDER_V2_TYPE 08a9aac4…`, `PAYMENT_V1 4a6c5ecd…`) equal
  the compiled ones, so the probe `:error` comes from the per-version check, not from a wrong test TYPE.
- Old suites at HEAD: `slice6_db_test` OK, `slice6_decode_test` OK, `slice6_db_stored_test` OK. `redteam_c3_test` C4 fails
  (`slice6_m4_test.py` not in `run.py`): the DL-147 effect, as red-output.md states.
- 0005 HEAD run `results/20261108T072659428712Z`: fail on test-n7_seed (R9 `{1, [D6B-39 …]}`), gen-order_v2 (D6B-39
  constructor text), test-n7_read (`order_v2!()` / `v2_module!()` guards, N11 `[1]`). 0005 probe run
  `results/20261108T072731299858Z`: n7_seed and gen pass; compile-order_v2 fails (`--warnings-as-errors`, never-match
  clause); test-n7_read fails R10 (`has_element? order-1`) and R11 (`{3, "rejected"}` in the list trace).
  `app/lib/generated/orders.ex` restored to HEAD bytes after each run.
- `slice6_m4_test` is in no `run.py` (DL-147 holds). Fixtures use corpus forms only (`rename a -> b` as `CHAIN`;
  comma changes as `slice3/M`) and only `//` comments. The 0005 `order_v2` source is in `fmt` form (probe `fmt` prints
  no diff). The 0004 `bad_rename/` files keep the one-line style of `bad/` (no fmt test reads them).
- Extra probe: a redacted String field in a chained http output gives the redacted D6B-39 text at HEAD and in the probe.

## Per test (genuine / right / false-pass risk)

| Test | Genuine (planned reason) | Right (DL-152/153, plan) | False-pass risk |
|---|---|---|---|
| R1 `test_N33_order_v2_builds` | yes, D6B-39 constructor | yes | low: R13 and N33 catch a wrong module |
| R2 `test_N12_rename_rejects` (2) | yes; probe exit 0 + DEAD LINE, so the rename check is needed | yes, QM4-1 A, QM4-4 A | none: exact text, table equals dir |
| R13 `steps_before_the_tail` | yes; probe `(True, False, False)` | yes, DL-152 effect (1) | low: a check-first GREEN fails it; only a dead earlier `Map.put` text passes it (O3) |
| N33 (10 cases) | yes; probe 6 `decode`, 4 guards pass | yes: full v2 values by exact `==` (Amount struct, Web tuple, note `""`), not only `:ok` | low: guards stop a looser tail; `constructor` reason matches the plain path (`slice6_db_test` line 113) |
| R4 rows of both versions | D6B-39 only (probe passes, PM4-08) | yes | low |
| R5 lost literal blocks | D6B-39 only (probe passes) | yes, DL-122 text for `TYPE Order v1` | medium-limit: in step 1 it cannot tell migrate-first from check-first in `--stored` (same keys); it still proves the check runs on a chained TYPE after GREEN |
| R5 control | D6B-39 only | yes | none |
| R6 constructor blocks | D6B-39 only | yes (text form as the plain `--stored` test: `TYPE Order:` without `v1`, pre-existing) | low: help by prefix |
| R6b v1 record builds | D6B-39 only | yes | low: P2 lines not exact (PM4-19) |
| R3 rename in a chain (http) | yes; probe builds | yes | none: exact text |
| R3b version mark builds | yes | yes (PM4-04) | none |
| R8 v1 body decode | yes; probe `:error` (per-version check) | yes: exact return, `["extra"]` (no `legacy`) pins the joined `unread` | medium: top-level only; nested `amount.extra` untested (O1) |
| R9 n7_seed build | yes, D6B-39 | yes | none: `rows()` pins exactly 2 rows and both ids in `row_ids`, so `counted(2, 2, 0)` is tied to the fixture rows |
| R10 n7_read Order v1 lists | yes (guard at HEAD; list decode in probe) | yes, record value with `note: ""`, row stays v1 | low: guard plus page plus record value |
| Note N7, Note N7b (controls) | same module cause | yes, `counted(3, 3, 0)` | none |
| R11 place submit under v2 | yes (guard; probe list `rejected`) | yes | low: `counted(4, 4, 0)` depends on the definition order (`--seed 0`, plan repair 1) |
| N11 | yes (`[1]`) | yes | none |
| R12 `run.py run` | yes, but not only on gen-order_v2: HEAD fails n7_seed, gen-order_v2, n7_read (one cause); probe fails compile-order_v2 and n7_read | yes | none: acceptance needs every EXPECTED case and the 2-row snapshot |

## Objections (max three)

**O1 · medium · Nested unknown keys of a chained constructor output have no test.**
Evidence: plan "Live decode" item 5 requires `unread` plus nested keys; plan repair 5 leaves it untested because "no http
case has a chained constructor field". After GREEN such a case builds (the lift covers every output). The plain path
names `FIELD.KEY` (`slice6_decode_ctor_test` `stray_key_in_field_value`). Consequence: a GREEN that drops nested keys in
the versioned decode passes; the RESPONSE RECORD `unknown_keys` (part of `value_sha256`) loses keys silently.
Resolving test: R8b below.

**O2 · medium · The kept redacted D6B-39 branch (PM4-05, acceptance 7) has no pin.**
Evidence: no test file holds `the redacted field … cannot stand in a TYPE with a MIGRATE CHAIN`; the extra probe shows the
text at HEAD. The GREEN deletes the two branches next to it. Consequence: a GREEN that also deletes this branch passes
every test; a redacted output field then decodes in a versioned TYPE without its mark (DL-125 gap).
Resolving test: R14 below (a guard; it passes at HEAD and must still pass after GREEN).

**O3 · low · R13 accepts an earlier dead `Map.put` text.**
Evidence: R13 uses the first `find` of the put; a check-first GREEN with an extra put text (or a comment holding it)
above the tail passes. A check-first GREEN without that text fails (names before the put, or no names in the body).
Resolving test: R13 repair below.

Dispositions: pending (main agent). None blocks GREEN; no critical or high objection.

## RED repairs for the GREEN worker to apply first (before any main.rs change)

1. **R8b (O1)** in `M4Decode`: source = `slice6/decode-ctor/orders.beaml` text with `note: String` added to `Payment` and
   `migrate Payment v1 -> v2 { add note: String = "" }`; decode a v1 body (v1 `type` from `type_of`, fields without `note`)
   whose `amount` holds `"extra": "y"` and whose top level holds `"extra": "z"`; assert the exact return
   `{:ok, %{… "note" => ""}, ["amount.extra", "extra"]}` (sorted as the plain path sorts; confirm the order against the plain
   decode of the same body without the chain, not against the new compiler). Record the HEAD and probe failures.
2. **R14 (O2)** in `M4Decode`: `slice6/redacted/output_redacted.beaml` text plus
   `migrate Payment v1 -> v2 { add status: String = "x" }` gives exit 1 and exactly
   `error: effect payments.authorize: the redacted field Payment.card_holder cannot stand in a TYPE with a MIGRATE CHAIN or a VERSION MARK in slice 6b (D6B-39)`
   `  help: remove the MIGRATE CHAIN and the VERSION MARK of Payment`. Guard: passes at HEAD and in the probe.
3. **R13 (O3)**: also assert `body.count(put) == 1` and no line of the body starts with `#` after whitespace.
4. **red-plan.md Limits**: add "R5 to R6b cannot tell migrate-first from check-first in `--stored` in step 1 (PM4-08)" and
   "R12 fails at HEAD on three steps from one cause".

## Limits

- One review round; no GREEN code read or run. The probe deletes only the two branches; it does not show GREEN output.
- The 0005 Postgres cluster was up after `db-up`; this review did not stop it.
- `beaml-spike fmt FILE` rewrites the file in place and prints a diff. The review's `fmt` check rewrote
  `order_v2/orders.beaml` and `bad_rename/row_rename_enum.beaml`; both were restored to HEAD bytes with `git checkout`,
  and `slice6_m4`, `slice6_db`, `slice6_decode`, `slice6_db_stored` were re-run on the HEAD bytes (same results).
- The 2-byte drift of `app/lib/generated/orders.ex` against `orders.beaml` (red-output.md) is pre-existing; not reviewed.

# RED output: fates-a1b

**[Verified]** RED run, 2026-11-08. By: Opus (RED fates-a1b). Raw output: [red-output.log](red-output.log).
Toolchain: cargo 1.94.0, rustc 1.94.0, Python 3.13.12, Elixir 1.18.1 (OTP 27).

## Binaries

- **HEAD**: `git archive HEAD experiments/0001-syntax-to-beam` into the scratchpad, `cargo build --offline`.
  `main.rs` of the scratch tree equals `git show HEAD:…/main.rs` (HEAD `5cdd0975`; main.rs unchanged since `fafc9195`).
- **PROBE**: the same archive with only the two `self.renamed_onto(…)?` calls in `output_fields` deleted
  (`#[allow(dead_code)]` on the fn). Scratch only; the repo `main.rs` never changed (`git diff --quiet HEAD -- main.rs`: clean).

## Commands

```
BEAML_SPIKE=<scratch>/head/…/target/debug/beaml-spike  python3 -B experiments/0004-generated-replay/tests/slice6_m4_test.py
BEAML_SPIKE=<scratch>/head/…/target/debug/beaml-spike  python3 -B experiments/0004-generated-replay/tests/slice6_fates_test.py
BEAML_SPIKE=<scratch>/probe/…/target/debug/beaml-spike python3 -B experiments/0004-generated-replay/tests/slice6_m4_test.py
```

## Results

| Run | Tests | Failures | Failing items |
|---|---|---|---|
| m4 at HEAD | 16 | 14 | N12 builds 4/4, runtime, stored 8/8, R3 |
| fates at HEAD | 36 | 5 | S1g, S1h, S1i (value-clause subTest), S1j 2/2 |
| m4 at PROBE | 16 | 7 | stored: web, tv kept, tv lost, bad currency, chain v1, chain v2, rename and map |

All guards pass at HEAD (11 in m4, 31 in fates, incl. the S1i guard subTest).

## Failure reasons (HEAD)

- **N12 builds, runtime, stored (all 8, also v2 control), R3**: exit 1 with the QM4-1 A text
  `… names the enum field Order.channel; a MIGRATE STEP on an enum or constructor field waits for the fate forms (M3, DL-152)`
  (constructor: `… names the constructor field Order.amount …`; R3: `… Payment.state …`). Planned reason.
- **S1g**: HEAD lifts `NO_CURRENCY` under `quarantine value`: `fate: 1 stored ROW … (quarantine value)` + `NOT_BUILT_Q`
  instead of the ctor block with the `currency` help. Planned.
- **S1h**: `migrate Amount v1 -> v2: one quarantine line per constructor TYPE; Amount has two (PF-11)`. Planned.
- **S1i**: HEAD lifts `{"0", ""}` under `quarantine currency` (fate line + `NOT_BUILT_Q`) instead of the block with the
  `value` help. Planned.
- **S1j**: HEAD lifts the catch-all failure under either line (`fate: 1 stored RESPONSE RECORD of operation
  payments.authorize quarantined … `) instead of the NoCurrency block with `NO_LITERAL_HELP`. Planned (O1).

## RED probe (false-pass guard)

With only `renamed_onto` removed: builds 4/4, runtime and R3 **pass** (the live decode needs no other change, plan §1 A
holds; the runtime expectations match a real decode), `v2 control` passes. All 7 old-row stored subTests still fail on
`error: TYPE Order: 1 stored ROW of table records has no variant of Channel …` (enum) or `… matches no signature of
Amount for field amount` (constructor). So the stored tests cannot pass on the check deletion alone; `stored_key` is
needed. The chain and rename+map subTests fail on the same "no variant" text, so they test the old-key read too.

## Decisions

**Undo**
→ 0005 `rename_channel` left for GREEN (DL-158, plan §3). By: Opus (RED fates-a1b)
→ `LIST_TAIL` inline (db.list + ENTRY LINE), no new fixture file (PB-02). By: Opus (RED fates-a1b)
→ Plain fixtures check module `BeamlSpike` (no ENTRY LINE, Q6E-1 C). By: Opus (RED fates-a1b)
→ `v2 control` asserts exit 0 and no error line; the W2 DEAD LINE warning may print. By: Opus (RED fates-a1b)
→ S1h compares the two `fate:` lines as a set; order not pinned. By: Opus (RED fates-a1b)
→ S1g / S1i help uses `help_q("Amount", 2, …)`: amount_v2 is newest v2 (as S3). By: Opus (RED fates-a1b)
→ O1 help pins and `bad_rename` headers move in GREEN, not RED. By: Opus (RED fates-a1b)
→ Stale comment in `slice6_db_test.py` line 354 updated. By: Opus (RED fates-a1b)

**Repair**
→ `NO_LITERAL_HELP` pins the plan-review text statt a new wording, weil help and lift must agree (O1) and the text names QB-2. Commits us to: GREEN prints this exact help. By: Opus (RED fates-a1b)
→ S1j covers both `quarantine value` and `quarantine currency` statt only `value`, weil a fallback to any parameter would pass a one-line test. By: Opus (RED fates-a1b)

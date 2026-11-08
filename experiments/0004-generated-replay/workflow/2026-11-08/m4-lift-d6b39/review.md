# TEST review: M4 step 1, lift D6B-39, migrate first

**[Observed]** TEST phase, 2026-11-08, HEAD `26b73524` (GREEN). Normal review, code mode (not Devil's Advocate).
Basis: [DL-152, DL-153](../../../../../wiki/planning/decision-log.md). Ledger: [plan.md](plan.md), [decisions.md](decisions.md),
[red-output.md](red-output.md), [red-review.md](red-review.md), [green-output.md](green-output.md).
By: Opus (m4-lift, TEST) for every line in this file. No repair. No commit.

**Verdict: TEST PASS.**

## Toolchain and binaries

- **[Observed]** `cargo build --offline --release` and `cargo build --offline` in `experiments/0001-syntax-to-beam`:
  release `526670ba…8d61`, debug `6118f4c4…0d71`. Both equal to green-output.md.
- **[Observed]** Old release from `git archive 850b52ee` (scratch): `b3f60ef3…5d01`, equal to the RED HEAD release.
- **[Observed]** Probe release from `git archive 850b52ee`, only the two D6B-39 branches of `output_fields` deleted
  (10 lines): `f916fe6f…a0e5`, equal to the red-output.md probe hash.

## Test files (HEAD debug binary)

| File | Result |
|---|---|
| `tests/slice6_m4_test.py` | 14 OK (also 14 OK with the release binary) |
| `tests/slice6_db_test.py` | 15 OK, 1 skip (N2c, pre-existing) |
| `tests/slice6_decode_test.py` | 8 OK |
| `tests/slice6_db_stored_test.py` | 49 OK, 3 skips (N28b, N30, N30b, pre-existing) |
| `tests/slice6_pipe_test.py` (pin) | 12 OK |
| `tests/slice6_host_struct_test.py` (pin) | 3 OK |
| `tests/slice6_effect_reach_test.py` (pin) | 8 OK |
| `tests/slice5_syntax_test.py` (pin) | 60 OK |

## Challenges

### (a) PM4-24: the repaired `N33_v1_unknown_channel`

- **[Observed]** The RED form put `l = ...; [rec] = resp.(); {l, ...}` into the `actual` slot of `want`. `want` writes
  `r = ACTUAL`, so `r` bound to the list result only and the case could not pass. A false fail, not a false pass.
- **[Observed]** The new form keeps the list call and the record read in the setup and compares
  `{l, rec["unknown_fields"]}` with the exact `{{:ok, items with Unknown("tv") and note ""}, ["items.0.channel"]}`.
  Both parts must hold.
- **[Observed]** Probe binary: `got N33_v1_unknown_channel: {{:error, %Orders.StoreError{reason: "decode"}}, []}`, FAIL.
  HEAD: PASS. The repaired case is still a proof and still fails for the planned reason.

### (b) Steps first with a removed ENUM LITERAL (throwaway, not committed)

Variant of `order_v2/orders.beaml` without `App = "app"` (keeps `Unknown(String)` and `add note`), a v1 row with
`channel: "app"`:

- **[Observed]** `--stored` with the v1 row: exit 1, no stdout, `error: TYPE Order v1: 1 stored ROW of table records has
  a value of field channel that is no ENUM LITERAL of Channel now (DL-122)`, with the record source line and the
  DL-122 help (QM4-3 A text). The block fires at build time.
- **[Observed]** The same row marked kept (`unknown_fields: ["channel"]`): exit 0, the module, `rows: 1 rows, 1 checked,
  0 not decodable`.
- **[Observed]** Live decode of that v1 row through `Orders.list_orders`: `{:ok, %{"items" => [... "channel" =>
  {"Channel", "Unknown", ["app"]}, "note" => ""]}}` and the RESPONSE RECORD `unknown_fields` `["items.0.channel"]`. PASS.

### (c) The per-version `unread` join (throwaway, not committed)

Source: `CTOR_CHAIN` of `slice6_m4_test.py` (decode-ctor `Payment` plus `add note`). Body with `amount.extra` and a
top-level `extra`.

| Case | HEAD | Probe |
|---|---|---|
| live v2 body, `__beaml_result_payments_authorize`: `unknown_keys` span attribute | `["amount.extra", "extra"]` PASS | PASS (the plain projection) |
| `Replay.record` written to a JSONL file and read back: `unknown_keys`, `outcome` | `["amount.extra", "extra"]`, `accepted` PASS | FAIL |
| replay of that v2 record file (digest check of `body/1`) | `{:ok, _}`, keys joined PASS | FAIL |
| v1 record file (`type` = `Payment v1`, body without `note`), replay | file `unknown_keys` `["amount.extra", "extra"]`, `{:ok, %{"note" => ""}}`, span keys `["amount.extra", "extra"]` PASS | FAIL: `{:error, PaymentError{reason: "decode"}}` |

- **[Observed]** Python check of the record file: `value_sha256 == st.value_sha256(value, unknown_keys, redacted)` is
  true for the v1 record. The v3 digest verifies in Elixir (replay) and in the Python reference.
- **[Inference]** A live body is always read as the newest TYPE VERSION (`type_version` nil); the per-version join
  matters for a REPLAY RUN of a v1 record and for a v1 ROW, not for live HTTP.

### (d) No byte change for String-only chained TYPES

- **[Observed]** Every tracked fixture with a `migrate` line (31 files, without `order_v2/` and `bad_rename/`), compiled
  with the 850b52ee release and the HEAD release (`--stored stored/empty.jsonl`, db fixtures
  `--stored slice6/db/stored/responses.jsonl`): stdout, stderr and exit byte-equal for all 31. 26 build (among them
  `slice6/db/plain_v2`, `slice6/db/two_rows`, `slice2/N-chain`, `slice3/R-add`, `slice4/Q4`, `slice5/Q4`), 5 reject
  equally (exit 1).

### (e) 0005 live check

- **[Observed]** `run.py db-up`: pass. `run.py run`: **pass**,
  [20261108T081341856399Z](../../../../0005-prototype-fullstack/results/20261108T081341856399Z/result.json), compiler
  `6118f4c4…0d71`, 17 steps pass, use cases 21 pass, 1 blocked (N9). `mix test`: 29 tests, 0 failures, 10 excluded,
  1 skipped. The tracked `app/lib/generated/orders.ex` is unchanged after the run.
- **[Observed]** Dev server on `127.0.0.1:4000` (already running). One v1 `Order` row (core of the run snapshot, TYPE
  `Order v1`) inserted into `proto_dev` by `psql` on the Unix socket `app/.pgsock` (trust auth).
  - Base module (Order v1): `curl /orders` renders one `data-order` row `order-1 12.50 EUR`. RESPONSE RECORD value has
    no `note`.
  - The run's `gen-order_v2.ex` copied into `app/lib/generated/orders.ex` (code reload on request): `curl /orders`
    renders the same row; the RESPONSE RECORD of `orders.list` is `accepted` with
    `{"items": [{"order_id": "order-1", "amount": {...}, "channel": "web", "note": ""}]}`, `unknown_fields` `[]`.
    The table row stays `version 1` (lazy read, DL-127).
- **[Observed]** Restore: `orders.ex` copied back (git status clean), `proto_dev` truncated (`count = 0`), the page shows
  "No orders yet." The ignored `app/.capture/` holds the three extra response lines of this check.
- **[Inference]** The `/orders` page has no note column, so "empty note" is visible in the RESPONSE RECORD and the
  encoder value, not in the HTML (see O1).

## Objections (max three)

**O1 · Medium · The 0005 page cannot show the empty note.** The `/orders` table renders order id, amount, currency and
channel only. N7 (R10) and this live check prove note `""` through the RESPONSE RECORD, not on the page. Consequence:
a host that drops the note silently would still pass the page check. Resolving test: a note cell
(`data-note`) on `/orders` and `has_element?(view, ~s([data-order] [data-note=""]))` in R10. Disposition: pending.

**O2 · Medium · The record file and replay path of a chained constructor output has no committed test.** R8 and R8b
check the return value of `__beaml_decode_payment` only. The throwaway (c) shows the file `unknown_keys`, the digest
and the v1 replay; the probe fails it, so it discriminates. Consequence: a later change of `Replay.record` or of the
replay key join for chained outputs passes the committed suite. Resolving test: add case (c) as R8c to
`slice6_m4_test.py`. Disposition: pending.

Dropped as low: the PM4-21 text swap (`replacen`) is a silent no-op if the tail text changes; R8 (enum tail) and R8b
(constructor tail) pin both tail forms, so a change fails a test.

## Limits

- **[Observed]** The throwaway checks (b) and (c) ran from the scratchpad and are not in the repository.
- **[Observed]** No 0004 full run in TEST; GREEN reported 39/39 (`results/20261108T074403452811Z`).
- **[Unknown]** Behavior with real Postgres for a removed ENUM LITERAL (b) was checked on the 0004 fake BeamlDb only.

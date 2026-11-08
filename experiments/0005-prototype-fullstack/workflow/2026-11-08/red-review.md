# RED review: EXPERIMENT 0005 (PROTOTYPE), N-TESTS

**Verdict: BLOCK** (one high objection with a small test-only resolving change; two medium notes).
Phase: RED review per `skills/implement-step/SKILL.md`. Fresh context, normal check, not a Devil's Advocate.
Inputs: [README](../../README.md), [plan.md](../2026-11-07/plan.md) (incl. Plan repair and Plan repair 2), [decisions.md](../2026-11-07/decisions.md), [plan-review.md](../2026-11-07/plan-review.md), [owner-review.md](../2026-11-07/owner-review.md), [red-plan.md](red-plan.md), [red-output.md](red-output.md), the RED run `results/20261108T001345855302Z/`, `app/beaml/`, `app/test/prototype/`, `app/test/support/`, `run.py`.
By: Opus (RED review exp0005) for every line of this file. Not committed.

## Observed (2026-11-08)

**Own run.** HEAD compiler from `git archive HEAD experiments/0001-syntax-to-beam` in scratch, `cargo build -q`; `run.py db-up`; `BEAML_SPIKE=<scratch> run.py`; `run.py db-down`.

→ **[Verified]** Run [20261108T001736866737Z](../../results/20261108T001736866737Z/result.json): status `fail`, exit 1.
→ **[Verified]** Use cases: 18 fail, N13 `pass`, N9 `blocked: fate slice (D036)`. Same set as the RED run.
⠀⠀↳ 13 `FunctionClauseError` (no route `/orders/new`)
⠀⠀↳ 2 `Mix.NoTaskError` (N1, N10)
⠀⠀↳ 3 `AssertionError` (N7 read, N7b, N11)
→ **[Verified]** Steps: `stored-*` exit 1 (no task), `gen-*` recorded as failed, `compile` and `compile-note_v2` exit 0, the four test steps exit 2, both resets exit 0, the final `gen-orders` fails and leaves no `lib/generated/orders.ex`.
→ **[Verified]** Every failure is missing host code (route, LiveView, `mix beaml.stored`). No compile error, no dep error, no test typo.
→ **[Verified]** Source hashes equal red-output (orders `bba45329…8282`, note_v2 `ddd06aef…731c`).
→ **[Observed]** Compiler sha256 `c14313a3…e330` differs from red-output `74203f72…c2f3`. No 0001 change since b332b12c. **[Inference]** The debug build embeds the scratch path.

**Source (item 6).** HEAD compiler, empty `rows.jsonl` and `responses.jsonl`:

| Source | Exit | `def ui_` | Module |
|---|---|---|---|
| `orders.beaml` | 0 | 4 | `Orders` |
| `variants/stricter` | 0 | 4 | `Orders` |
| `variants/no_place` | 0 | 3 (no `ui_place`) | `Orders` |
| `variants/note_v2` | 0 | 4 + DEAD LINE warning (no v1 row) | `Orders` |

→ **[Verified]** Corpus syntax only, `//` comments, variant diffs equal the red-plan table.

## Per-item findings

**(2) Thesis chain**
→ **[Verified]** N7 seed: Order and Note v1 rows written through the pages; note_v2 live build `rows: 2 rows, 2 checked, 0 not decodable`; the Note row id is in `row_ids`.
→ **[Verified]** N7 read: `Orders.Note` has `tag`; the row stays version 1. N7b: a version 2 row with `tag ""`; second live build `3 checked`.
→ **[Verified]** N11 is not vacuous: Note rows of versions 1 and 2 exist before the migration and column check.
→ **[Verified]** N8c in every `snapshot!`: files new, meta keys, `row_ids` and count equal a separate `psql` read. N8b: delete by SQL, then stricter exit 0.
→ **[Verified]** Committed rows: `sandbox: false` owner; `psql` is a separate process, so it sees committed rows only.
→ **Gap (O1):** no test proves the list pages read through `Orders.ui_notes/1` / `ui_orders/1` (db.list, row decode, MIGRATE CHAIN). See O1.
→ **Remaining false-pass path (snapshot):** `run.py`'s own out-of-VM `mix beaml.stored` before `gen-note_v2` has no provenance check. An empty snapshot still generates note_v2 (exit 0, DEAD LINE warning only). Effect is limited: the in-VM N7 seed build already proves the live check. The `database` meta key compares with the same VM's `Repo.config`; **[Inference]** near-tautological, the id comparison carries the proof. Folded into O2.

**(3) Value and secret checks**
→ **[Verified]** N2c: `jsonb_typeof(value->'reason') = 'null'` separates JSON null from a missing key (SQL NULL).
→ **[Verified]** N3: the three form values absent outside `value` (entry) and outside `value`, `request` (db record, QDB-5 A).
→ **[Verified]** N12: `place` results `ok`, `rejected:constructor`; no form value, app path or source text in new action lines.
→ **N13:** scans `git ls-files` for db dirs and env files, and `config/*.exs` only for `key: "` literals. Not `lib/`. See O3.
⠀⠀↳ **[Verified]** today: salts and key base are runtime or MFA values

**(4) Defaults and markup**
→ **[Verified]** Both `(default, open)` items are in [owner-review.md "0005 RED defaults"](../2026-11-07/owner-review.md#0005-red-defaults).
→ **[Verified]** Page markup and action names are Undo lines in red-plan, not in owner-review. **[Inference]** correct class: host-internal, a test repair undoes them.
→ **Contract** (GREEN must not move): row core fields and `reason` null (N2, N2c); one trace for ENTRY RECORD and db record (N3); reject reason `constructor`, no row, no `orders.save` record (N4); Unknown channel stored as text (N4, N6); newest first (N5, Q5-2); `tag ""` and version 1 kept (N7); version 2 row (N7b); the P4 block line, no stored value (N8); snapshot files and meta keys (N8c); `Orders.ui_place/1` in the host error (N10); no DDL change (N11); no value in action lines (N12).
→ **Incidental** (a GREEN test repair is allowed with a ledger line): `#place`, `#note`, `order[...]`, `note[text]`, `[data-order]`, `[data-note]`, `data-tag` attribute form; `{:live_redirect, %{to: "/orders"}}` (push_navigate); flash text `form rejected: <reason>`; result string `rejected:constructor`; `--seed 0` order.

**(5) run.py**
→ **[Verified]** Every step runs and records `command`, `exit_code`, stdout and stderr; one failed step, or a failed final gen, fails the run (exit 1).
→ **[Verified]** `result.json` has command, toolchain (Python, Elixir, OTP, pg_ctl), compiler path and sha256, source and output hashes, `use_cases`.
→ **Gap (O2):** status uses step exits only, not the use-case set. See O2.

## Objections

### O1 · high · N5, N7 and N7b do not prove the list goes through BEAML

- **Evidence.** No test asserts a `ui.orders`, `ui.notes`, `orders.list` or `notes.list` record (`rg` over `app/test`: only the N1 and N10 name checks). N5 reads the page only. N7 reads `[data-note][data-tag=""]`. N7b also never checks a `notes.save` record.
- **Consequence.** A host page that reads `records` by SQL and renders a missing `tag` as `""` passes N5, N7 and N7b. The thesis "a v1 row is read under the v2 TYPE through the MIGRATE CHAIN" (hypothesis 2, DL-127) then passes with no BEAML read.
- **Resolving test.** As N3 does: mark the `entries` and `responses` capture files before each list mount (N5, N7, N7b) and the N7b submit. Assert one `ui.notes` ENTRY RECORD and one `notes.list` record, `accepted`, one shared `trace_id` (N5: `ui.orders`, `orders.list`; N7b submit: `ui.note`, `notes.save`). In N7 also assert the `notes.list` record value lists the item with `tag ""` (inside `value` only, never logged).
- → By: Opus (RED review exp0005) · class Repair (test design inside the team)

### O2 · medium · a run can pass with a skipped or missing N-test

- **Evidence.** `run_all` returns `all(oks)` and the last step status. A `@tag skip`, a wrong `phase` tag or a renamed `use_case` gives exit 0 and status `pass`. `use_cases` is only reported. `gen-note_v2` uses an unchecked out-of-VM snapshot (item 2).
- **Consequence.** The acceptance line ("passes N1 to N7, N7b, N8, N8b, N8c, N10 to N13; N9 blocked") can read `pass` while a test did not run.
- **Resolving test.** In `run_all`, compare `use_cases` with the expected 20 (use case, test) pairs: every one `pass`, only N9 `blocked: …`; else fail the run. Assert `stored-note_v2/snapshot-meta.json` `row_count` = 2 and no DEAD LINE in `gen-note_v2.stderr`.
- → By: Opus (RED review exp0005) · class Repair · noted, not blocking

### O3 · medium · N13 misses `lib/` and other literal forms

- **Evidence.** The literal scan reads `config/*.exs` with `(secret_key_base|signing_salt|password)\s*:\s*"`. `lib/proto_web/endpoint.ex` holds `signing_salt` (today an MFA tuple). `secret_key_base = "…"` or a module attribute do not match.
- **Consequence.** A GREEN change that writes a literal salt into `lib/` or a `=` form passes the guard.
- **Resolving test.** Scan `config/**/*.exs` and `lib/**/*.{ex,exs,heex}`; match `:` and `=` forms and `@`-attributes. Print file and line only.
- → By: Opus (RED review exp0005) · class Repair · noted, not blocking

## Dropped (low)

→ Test-file and `mix.lock` hashes not in `result.json`; git commit covers them.
→ Compiler sha differs per build path; record the path, as done.

## Database state

→ **[Verified]** `run.py db-down` ran after the review run; the cluster is stopped.

## Decisions

**Repair**
→ BLOCK on O1 statt PASS, weil the thesis read can pass without BEAML. Commits us to: one RED repair, then a re-check. → By: Opus (RED review exp0005)
→ O2, O3 noted statt blocking, weil a GREEN pass cannot silently fake the thesis through them. → By: Opus (RED review exp0005)

**Undo**
→ Markup and redirect form classed incidental. → By: Opus (RED review exp0005)
→ Compiler sha difference accepted as build-path effect. → By: Opus (RED review exp0005)
→ Own run kept as `results/20261108T001736866737Z/`. → By: Opus (RED review exp0005)

## Re-check after RED repair (2026-11-08)

**Verdict: PASS** (O1 closed for the BEAML read; O2, O3 closed; two medium notes, no block).
Phase: one re-check round after the BLOCK, new evidence only. Fresh context, normal check.
Inputs: [red-output.md "RED repair"](red-output.md), [red-plan.md](red-plan.md), `app/test/support/prototype.ex`, `app/test/prototype/*.exs`, `run.py`, run `results/20261108T002308453139Z/`.
By: Opus (RED re-check exp0005) for every line of this section. Not committed.

**Own run**
→ **[Verified]** HEAD compiler from `git archive` in scratch, `cargo build -q`; `run.py db-up`, `run`, `db-down`.
→ **[Verified]** Run [20261108T002633535758Z](../../results/20261108T002633535758Z/result.json): status `fail`, exit 1.
→ **[Verified]** Use cases: 18 fail, N13 `pass`, N9 `blocked: fate slice (D036)`. Same error kinds as the RED run.
→ **[Verified]** `acceptance`: the 18 failed pairs plus `stored-note_v2: no snapshot-meta (FileNotFoundError)`.
→ **[Verified]** db-up `20261108T002632924001Z`, db-down `20261108T002640208707Z`: pass. `pg_ctl status`: no server running.

**(1) O1: closed for the BEAML read**
→ **[Verified]** SQL-only host (no `ui_orders/1`, `ui_notes/1`): no new ENTRY RECORD, so `through_beaml!` fails at `es != []`.
⠀⠀↳ the `for db <- through_beaml!(...)` form calls the helper first
→ **[Verified]** Helper: one ENTRY op, one db op per window; all `{3, "accepted"}`; unique 32-hex traces; trace multisets equal.
⠀⠀↳ two mounts (dead, live) give two pairs; each pair checked
→ **[Verified]** N5 asserts `orders.list` items `order-2`, `order-1`; N7 asserts `notes.list` value `tag ""`; N7b both items.
→ **[Verified]** N7b submit: exactly one `ui.note` + `notes.save` pair.
→ **Open (medium, R1):** host calls `ui_notes/1`, discards the value and renders `records` by SQL with a missing `tag` as `""`.
⠀⠀↳ N7 and N7b still pass: SQL render and chain default give the same page
⠀⠀↳ the record proves the BEAML read; the page use is not proven
⠀⠀↳ smallest close: N13-style scan, no `Repo.` or `"records"` in `lib/proto_web`
⠀⠀↳ not a block: the thesis read (v1 row under the v2 TYPE) now needs BEAML
→ **Open (medium, R2):** N7b submit window allows only `ui.note`/`notes.save`.
⠀⠀↳ a `handle_event` that re-lists by `ui_notes/1` gives a false RED
⠀⠀↳ plan.md P4 host text does not forbid the re-list
⠀⠀↳ GREEN either uses `push_navigate` (as `/orders/new`) or repairs the test with a ledger line

**(2) O2: closed**
→ **[Verified]** `run_all` returns false when `acceptance()` is non-empty.
→ **[Verified]** Scratch self-check of `acceptance()` (import of `run.py`, synthetic cases):
⠀⠀↳ full set: `[]`
⠀⠀↳ skip of N5: `exp0005-N5: skip`
⠀⠀↳ rename of N7b: missing + unexpected
⠀⠀↳ wrong `use_case` tag: missing + unexpected
⠀⠀↳ excluded (wrong `phase` tag, not run): missing
⠀⠀↳ N9 `pass`: flagged
→ **[Verified]** `row_count` 2 check and `"DEAD LINE"` substring; compiler text is `warning: DEAD LINE: …` (`main.rs`).
→ **[Inference]** Two Order rows and no Note row give `row_count` 2, but then the DEAD LINE check fails. Closed.

**(3) O3: closed**
→ **[Verified]** N13 scans `config/**/*.exs` and `lib/**/*.{ex,exs,heex}`; matches `key: "`, `key = "`, `@…key… "`; prints file and line only.
→ **[Verified]** N13 `pass` in the own run.
→ Dropped (low): map form `"signing_salt" => "…"` and sigils not matched.

**(4) Hidden Migrate decisions**
→ **[Verified]** None found. The pairing rule extends the N3 contract (plan.md N3, one shared `trace_id`) to list reads.
→ **[Verified]** red-plan line 61 states it. Test design inside the team: Repair, not owner-review.

### Decisions

**Repair**
→ PASS statt BLOCK, weil a SQL-only host now fails N5, N7, N7b. → By: Opus (RED re-check exp0005)
→ R1 noted statt blocking, weil the BEAML read is proven; only page use is open. → By: Opus (RED re-check exp0005)
→ R2 noted statt blocking, weil it gives a false RED, never a false pass. → By: Opus (RED re-check exp0005)
→ Pairing rule classed Repair statt Migrate, weil it extends the N3 trace contract. → By: Opus (RED re-check exp0005)

**Undo**
→ Own run kept as `results/20261108T002633535758Z/`. → By: Opus (RED re-check exp0005)
→ `acceptance()` mutation check in scratch only, no repo file. → By: Opus (RED re-check exp0005)

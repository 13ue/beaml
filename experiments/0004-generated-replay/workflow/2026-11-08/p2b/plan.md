# Plan: P2b (DL-164, a wrong digest blocks the build)

**[Proposal]** PLAN phase, 2026-11-08, HEAD `8e0f8bf3`. By: Opus (PLAN P2b). No commit, no production change.
Basis: DL-164 (By: 13ue), D035 (closed), DL-136, DL-150, DL-151, DL-158, DL-165. Compiler:
`experiments/0001-syntax-to-beam/src/main.rs`.

Test-first applies: the change makes `--stored` block where HEAD exits 0. One behavior, three streams, one checker
helper: one RED, one RED review, one GREEN.

## 1. What "digest" means here

- **[Verified]** The digest is `value_sha256` inside every stored RESPONSE RECORD, ENTRY RECORD and ROW (record
  format draft 3): lower-case hex SHA-256 of the canonical JSON of `{"redacted", "unknown_keys", "value"}` (D6B-58).
  Writer: `digest/3` in the generated `Replay` (main.rs ~5371). Rust mirror: `digest_holds` (main.rs ~5672).
- **[Verified]** It is **not** snapshot provenance. Slice 6 final review A3 ("compiler cannot tell which database a ROW
  SNAPSHOT came from") is answered by DL-151 (live `--stored`, its own slice). P2b does not read `snapshot-meta.json`
  beyond today's `row_count`, and does not touch provenance.
- **[Verified] HEAD behavior per stream:**
  → RESPONSE RECORDS (`check_stored` ~5888): digest never computed; a changed value is checked as if genuine; when
    M > 0 rejected, the count line is followed by `digest not verified (P2b)` (~6049).
  → ENTRY RECORDS (`check_entries` ~5035): digest never computed (D035 [Observed], the 6d C5 gap).
  → ROWS (`check_rows` ~6595): `!digest_holds` → `continue`; the row is counted in `M not decodable`, build exit 0.
- **[Verified]** Run time already rejects a bad digest (`body/1` → `:body_digest_mismatch`, ~5359); a `db.list` with one
  such row fails as a whole (DL-150 evidence). So HEAD builds green against data the run time refuses.

## 2. Acceptance criteria

1. An accepted ROW whose TYPE has a reader (`db.get` / `db.list`) and whose digest does not hold: exit 1, stdout empty,
   the digest error (section 4) with count and record source.
2. The same for an accepted RESPONSE RECORD of an operation with an `effect`, and for an accepted ENTRY RECORD of an
   ENTRY LINE.
3. Read order PDB-15 holds: a bad-digest row or record gets the digest error, not the path error or a value error.
4. Rows and records that are not checked stay counted, not verified (built default, O1): outcome `rejected`, a ROW
   TYPE with no reader, a record of a RETIRE LINE operation.
5. The line `digest not verified (P2b)` is never printed. The count lines keep their text otherwise.
6. No message holds a stored value, row id or trace id (DL-124). Names, counts, lines only.
7. Good data: every existing 0004 step and the 0005 `run.py run` pass with unchanged stderr except the removed line.
8. 0005 use case N15 passes (section 7).

## 3. RED tests (all fail at HEAD `8e0f8bf3`)

| Test | File (0004 `tests/`) | Fails at HEAD on |
|---|---|---|
| `test_P2b_R1_wrong_digest_row_blocks` (rows `[row(WIRE1), row(WIRE2, value_sha256=st.value_sha256(WIRE1))]`, ORDERS) | `slice6_db_stored_test.py` | exit 0 and `rows: 2 rows, 1 checked, 1 not decodable` instead of exit 1 and the digest error at line 2 |
| `test_P2b_R2_digest_before_type_version` (replaces N29 digest case: bad digest + off-chain fingerprint) | `slice6_db_stored_test.py` | exit 0, `counted(1, 0, 1)`; expected digest error, no `cannot read` |
| `test_P2b_R3_wrong_digest_response_record_blocks` (accepted 200 record, value changed, old digest) | `record_v3_test.py` | exit 0; no digest error |
| `test_P2b_R4_wrong_digest_entry_record_blocks` (accepted entry, value changed, old digest) | `slice6_entry_test.py` | exit 0 with the `N entries, …` line |
| `count_lines()` and N25 control without `DIGEST_LINE` (edit of the expectation) | `record_v3_test.py`, `slice6_db_stored_test.py` (~351) | HEAD prints the extra line `digest not verified (P2b)` |
| N21 rewritten: keep the INVOICE (no reader) case, move the bad-digest case to R1 | `slice6_db_stored_test.py` | (guard, passes both) |
| `test_P2b_G1_unchecked_items_are_not_verified` (rejected row, rejected record, no-reader row, each with a wrong digest: counted, exit 0) | `slice6_db_stored_test.py` | (guard, passes both; fixes default O1) |

R1, R3, R4 also assert that the tampered value text (`99.00`-style marker) is absent from stderr (criterion 6).
Expected texts come from this plan and `stored_types_test.value_sha256`, never from the new compiler.

Not RED: the digest algorithm itself (unchanged, `digest_holds` exists and is tested by N21/N29 today).

## 4. Error text (draft)

One message per (TYPE, place), first line of the group, as the other `--stored` blocks:

```
error: TYPE Order: 1 stored ROW of table records has a wrong digest: value_sha256 does not match value, unknown_keys and redacted (DL-164)
  record source: <dir>/rows.jsonl:2 (line 2)
  help: the stored value changed without a new digest (a hand edit or corruption); restore or delete the ROW, then build again
```

→ plural: `2 stored ROWS … have a wrong digest`.
→ RESPONSE RECORD: `of operation <op>`, TYPE = `effect.output`. ENTRY RECORD: `of operation <op>`, TYPE = entry input.
→ ROW: TYPE = stored `type.name`.
→ Exit code 1 (the existing `main` error path, main.rs ~7938). No new flag, no usage change.

## 5. Files touched

→ `experiments/0001-syntax-to-beam/src/main.rs`: one `digest_errors` collector per check, a shared formatter;
  `check_rows` splits `!digest_holds` off the `continue`; `check_stored` and `check_entries` call `digest_holds` after
  `checked += 1`; delete the `digest not verified (P2b)` push. `emit` untouched.
→ `experiments/0004-generated-replay/tests/slice6_db_stored_test.py`, `record_v3_test.py`, `slice6_entry_test.py`
  (tests above; module docstrings that say "a bad digest is counted").
→ 0005: `app/test/prototype/stored_test.exs` (N15), `run.py` (`EXPECTED` gets N15).
→ Not touched by this step: wiki, READMEs (docs worker), fixtures (section 8, R1).

## 6. Pin impact

→ Digest pins (`slice6_pipe_test.py` EFFECT_OUTPUTS, `slice6_host_struct_test.py` BYTE_GUARD,
  `slice6/effect-reach/byte-guard.json`): **no move**. P2b changes the checker, not generated EFFECT bytes.
→ Hash pins (`slice5_syntax_test.py` PIN, `slice6_entry_test.py` BASE, `slice6_multi_test.py` BASE,
  `slice6_db_test.py` P4_BASE): **no move** (same reason). TEST confirms with `slice5-syntax` first.
→ V18b (`record_v3_test.py`): **[Inference]** no move. No PAIRS fixture holds a rejected RESPONSE RECORD (the only
  source of `digest not verified (P2b)`); the entries pair runs with an empty `responses.jsonl`. **[Verified]** all 54
  checked-in records and rows with `value_sha256` outside `results/` hold their digest (planner scan, Python
  `stored_types_test` canonical form). If V18b moves after all, add a `DIGEST_LINE` drop beside `HELP_REPIN`, not a
  looser compare.
→ Help pins: no existing help line changes.

## 7. Use case in EXPERIMENT 0005 (DL-158)

→ **N15 an SQL edit of a row value without a new digest blocks the build** (`stored_test.exs`, phase `n8`,
  `@tag use_case: "N15"`).
→ Steps: `place(conn, good())`; `UPDATE records SET value = jsonb_set(value, '{value,amount,value}', '"99.00"') WHERE
  id = $1`; `live_build(nil, "n15")` → `{1, "", lines}`; first non-`rows:` line is the digest error; `99.00`, the
  order id and trace id are not in the text; `assert_no_ddl!()`. Control in the same test: restore the row by
  `DELETE`, build again → exit 0, `counted(0, 0, 0)`.
→ HEAD: exit 0 with `counted(1, 0, 1)` (the row is skipped). This is the D035 site example (SQL edit without a new
  digest).
→ `run.py` `EXPECTED` gets the N15 pair; `run.py run` must pass with it before TEST.

## 8. Risks

→ **R1 hidden stale digests in generated test records.** Some Python tests may build records with `dict(…, value=…)`
  and keep an old digest; at HEAD they pass silently. GREEN runs the full 0004 `run.py`; a failure there gets the
  digest recomputed in the test (`st.with_value`), never a looser check. Count and list them in `green-output.md`.
→ **R2 number text.** `canonical` keeps number text as read (ponytail note ~5693). Postgres `jsonb` rewrites `1e2` to
  `100`. **[Verified]** live 0005 rows hold today (N14: `2 checked, 0 not decodable`). An Int or exponent value from
  another encoder could false-block; out of scope, noted.
→ **R3 run time unchanged.** A row edited after the build still fails `db.list` at run time (`:body_digest_mismatch`).
  That is DL-150 / fates-a2 ground, not P2b.
→ **R4 DL-150 is not built.** HEAD still counts other not-decodable rows (bad `type` key) and exits 0. P2b closes the
  digest half only. Flag for main: DL-150 A needs its own step or a scope line.

## 9. Open OWNER questions (built default in brackets)

→ **O1** Verify only checked items, or every item with a digest (rejected, no reader, retired)? [only checked, DL-164
  wording "every checked record and row"; guard G1 pins it.]
→ **O2** May a `quarantine` line park a bad-digest row (DL-164 "plan option")? [No. A digest fault is no TYPE change; a
  fate line answers a TYPE change; run-time quarantine is not built (fates-a2). The help names restore or delete.]
→ **O3** Should the count line also name the digest faults (`…, M not decodable, D wrong digest`)? [No. The build
  blocks; the error line holds the count.]

## 10. Decisions

**Undo**
→ Tests go into the three existing test files, no new `run.py` step. By: Opus (PLAN P2b)
→ No `plan.json`: the 2026-11-08 ledgers keep `plan.md` only. By: Opus (PLAN P2b)

**Repair**
→ Digest error before path and value checks, over "all errors at once", because PDB-15 read order and an untrusted
  value must not drive a constructor run. By: Opus (PLAN P2b)
→ One message per (TYPE, place), over one per line, because every other `--stored` block groups so. By: Opus (PLAN P2b)
→ N15 in phase n8 `stored_test.exs`, over a new phase, because it reuses `live_build` and the truncate tag. By: Opus
  (PLAN P2b)
→ Provenance (A3) out of scope, over folding it in, because DL-151 owns it. By: Opus (PLAN P2b)

**Migrate (OWNER chooses; defaults built)**
→ O1, O2, O3 above. By: Opus (PLAN P2b), defaults only.

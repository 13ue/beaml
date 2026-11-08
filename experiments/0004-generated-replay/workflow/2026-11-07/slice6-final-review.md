# Final review of slice 6 (Devil's Advocate, code mode)

Target: slice 6 end to end at HEAD `7be296e2` (steps 6a, 11, 12/12b, 13, 6b/6c, 6d, record format v3, several EFFECTS per source, P4a/P4b/P4c, RED TEAM 01 repairs, EXPERIMENT 0005 as the proof).
Mode: code. Skill: `advocatus-diaboli`. Read-only: no source, test or fixture changed. Not committed. Date 2026-11-08.
By: Opus (final review slice 6) for every line of this file.

Probe setup: `git archive HEAD experiments/0001-syntax-to-beam` into the scratchpad, `cargo build -q`, probes from a scratch `cwd`. No full `run.py`; the last full run is `results/20261108T005120819231Z` (status `pass`, 38 steps). Probe inputs are copies of the tracked fixture `slice6/db/stored/meta/rows.jsonl` and `slice6/db/orders.beaml`. No stored value or MARKER is written here.

## The work, fairly

→ **[Observed]** One source owns TYPES, ENTRY LINES, flow and rows of a LiveView page; `Orders.ui_*` is the only path in (N3, N5, N7).
→ **[Observed]** A stricter `Amount` blocks the build against a row snapshot; delete frees it; DDL never moves (N8, N8c, N11).
→ **[Observed]** A String-only `Note` v1 row reads through the MIGRATE CHAIN; v2 writes version 2 (N7, N7b).
→ **[Observed]** Every RED TEAM 01 high has an OWNER answer (DL-135 to DL-140); C1, C3, C4, B3 are built and tested.
→ **[Observed]** The limits are mostly written down: M4, O1 to O3, QDB-4, Q5-4, R6D-11, the DL-136/DL-140 "answered, not built" line (0004 README `:1943`).

The work is honest about many of its gaps. The objections below are about what the PASS is allowed to mean.

## Objections (block level: three)

### A1 · premise · high · The 0005 PASS answers a narrower question than the thesis

→ Claim: the thesis says "a TYPE change travels ... with no second migration system, and the build sees every stored value that the new rules would break". At HEAD, for the real domain TYPE `Order`, the build does not see a literal remap, the TYPE cannot get a new VERSION, and the only exit from a block is SQL.
→ Evidence:
⠀⠀↳ **[Observed]** probe: swap `Web`/`App` literals in `slice6/db/orders.beaml`; `--stored` over two `channel` rows gives exit 0 for base and swap, both `rows: 2 rows, 2 checked, 0 not decodable`. Every stored row now reads as the other variant. DL-140 (OWNER, A) says this must block; it is "answered, not built" (0004 README `:1943`). The 0005 README limits do not name it.
⠀⠀↳ **[Observed]** D6B-39 forbids a MIGRATE CHAIN on `Order` (constructor and enum fields); the chain is proven only on the String-only `Note` (0005 README limits, QDB-8 B).
⠀⠀↳ **[Observed]** N8c frees the stricter build by an SQL delete; N9 (`quarantine`) is blocked (D036). For `Order` the only working fate is host SQL: a second migration path by hand.
⠀⠀↳ **[Observed]** the v2 to v3 record format change was migrated by a one-time Python rewrite (`record-format-v3/convert_v3.py`, QV3-5 A). A stored-format change used a script outside the language.
⠀⠀↳ **[Observed]** 0005 snapshots STORED ROWS only with an empty `responses.jsonl` (owner-review "Snapshot record set" A). The ENTRY RECORDS that `ui_place/1` writes are never checked in 0005; under QV3-7 A the empty record stream prints nothing.
→ Consequence: a reader of "TEST PASS" plus the 0005 Question takes the thesis as shown for a real TYPE. It is shown for constructor tightening on a v1 `Order`, and for add-field on a String-only TYPE. A typo fix of an ENUM LITERAL silently re-reads every stored order.
→ Smallest refuting test: the literal swap on the 0005 `orders.beaml` against one live `Order` row; expect exit 1 (DL-140). Until it passes, the 0005 README states "DL-140 not built: a literal swap passes" beside the PASS.

### A2 · implementation · high · A row the build counts as "not decodable" takes the whole `db.list` down at run time

→ Claim: DL-136 "counted, not checked" was copied from RESPONSE RECORDS to rows (`check_rows`, `main.rs` about `:5858`). A REPLAY RUN skips a non-replayable record. `db.list` does not skip a non-decodable row: QDB-4 A halts on the first bad row (`rows_order`, `app/lib/generated/orders.ex:531`).
→ Evidence:
⠀⠀↳ **[Observed]** probe: one row with a wrong `value_sha256` → exit 0, `rows: 2 rows, 1 checked, 1 not decodable`.
⠀⠀↳ **[Observed]** probe: one row with a changed field and the old digest (an SQL `UPDATE` without a digest) → exit 0, `rows: 1 rows, 0 checked, 1 not decodable`. P4c blocks only when the digest was recomputed.
⠀⠀↳ **[Observed]** 0005 TEST probe: one undecodable `Order` row makes `/orders` show `store failed: decode` and no row (review §2).
→ Consequence: wrong outcome. A green build ships a page that fails for every user. DL-121 ("the check result equals the REPLAY RUN result") and DL-137 ("only rows that `db.list` would decode are checked") hold literally, but the run-time read is not the REPLAY RUN. The db-transport review even names "count as not decodable" as a safe P4c remedy (`db-transport/review.md:60`).
→ Smallest refuting test: the digest-tamper row in `proto_test` plus `variants/` build: expect exit 1, or `db.list` returns the good rows. Either answer is an OWNER choice (QDB-4 against DL-136 for rows).

### A3 · risk · high · The compiler cannot tell which database a ROW SNAPSHOT came from; the repeatable command ships against 0 rows

→ Claim: DL-127 and DL-137 say `--stored` reads the table live. Built Q5-4 B: a host task writes a file. The compiler reads only `row_count`, and only when `snapshot-meta.json` exists (`main.rs` `:5873` to `:5886`, `:6351` `.ok()`).
→ Evidence:
⠀⠀↳ **[Observed]** probe: the same rows without `snapshot-meta.json` → exit 0, no warning.
⠀⠀↳ **[Observed]** `database`, `table`, `query_time` and `row_ids` are never read by the compiler. The provenance check exists only in the 0005 test harness (`provenance!/1`).
⠀⠀↳ **[Observed]** `run.py run` truncates `proto_dev` and `proto_test`, then builds the shipped `orders.ex` against 0 rows (TEST O1).
→ Consequence: a stale or foreign snapshot (test DB, last week) gives a green build over a table it never saw. The gate is only as good as a host file nobody checks. In the experiment's own repeatable command it is green by construction.
→ Smallest refuting test: build with a `rows.jsonl` and no meta, and with a meta naming another database: expect exit 1 (or a printed provenance line the OWNER accepts). Q5-4 and TEST O1 are already open; this adds the compiler side.

## Noted (medium)

→ **M-a · risk** · `elixirc --warnings-as-errors` exits 0 on warnings (**[Observed]** probe: unused variable and undefined `Nope.h/1`, exit 0, Elixir 1.18.1). About ten slice 6 harnesses claim a warning gate they do not have. R6D-11 records it; no register entry; D-register line 497 still says Unknown. Test: grep the `elixirc` stderr for `warning:` in one harness.
→ **M-b · implementation** · The three N13 guards share the text filter `: *\[`. **[Observed]** today all 28 excluded tracked sources are db sources, so nothing escapes yet. A future non-db source with `: [` in a comment or an http LIST TYPE leaves every byte guard silently.
→ **M-c · implementation** · DL-147 against C4: `redteam_c3_test` C4 globs every `slice6_*_test.py`. **[Inferred]** the next slice 6 RED file fails the full run through C4, the case DL-147 exists to avoid. A `slice7_` file is not covered by C4 at all.
→ **M-d · implementation** · R1: `--stored` skips entries rejected at capture (DL-138). **[Inferred]** after a rule loosens, the REPLAY RUN of such an entry takes the accepted path with no recorded db response. Not probed. **[Unknown]** the actual replay class.
→ **M-e · risk** · Flakes: slice6d entry test 1 of 12, `N17b` once beside a parallel run; no test name kept. **[Unknown]** cause. A flake in a gate test makes a later real failure easy to wave off.
→ **M-f · implementation** · http RESPONSE RECORD shape gap (N32e) stays open as Migrate default A. Same class as A2 for http records; it replays, so the cost is bounded.

Dropped as low or already surfaced: QV3-7 A silence (folded into A1), the six byte-pin sites (R2-5, review diff covers it), `__beaml_encode_order/1` (TEST O3, owner-review Big item 2).

## Specification quality (owner-review.md)

→ **[Inferred]** "Snapshot record set A: an empty `responses.jsonl`" with "QV3-7 A" reads two ways: "0005 checks no records" or "0005 checked records and found none". Both print nothing.
→ **[Inferred]** "QDB-4 A as built (letters: docs)" with "DL-136 counted, not checked" reads two ways: a bad row is "tolerated" (build) or "fatal" (run time). See A2.
→ **[Inferred]** "Q5-4 B host task writes a snapshot" does not say who guarantees freshness or origin. See A3.

## Dispositions

All objections: `disposition: pending`, `disposition_rationale: null`. Nothing here is accepted, deferred or rejected.

## Deliberately not challenged

→ The stored-value rule DL-124: **[Observed]** the stricter and shape probes print counts only; no fixture value in stderr. The RED reviews scan this per test.
→ `Orders.__beaml_encode_order/1`: already Big item 2 with options; a new objection adds no evidence.
→ Record format v3 key choices (QV3-1 to QV3-6): OWNER-facing defaults, no wrong outcome found.

## Evidence not inspected

→ The full `run.py` (not run, per brief); the slice 6a to 13 ledgers in detail; the `--stored` Elixir driver after C1; `vertical-integration.md` beyond the P4 paragraph; the 0005 LiveView and test code beyond the generated list decode; the R1 replay path (M-d).

## Decisions

**Undo**
→ Probes on copies of tracked fixtures, scratch compiler from `git archive HEAD` → By: Opus (final review slice 6)
→ QV3-7 folded into A1 statt own objection → By: Opus (final review slice 6)
→ O3 encoder name not re-raised → By: Opus (final review slice 6)

**Repair**
→ A2 high statt medium, weil a green build gives a dead page and the probe shows it with an SQL update → By: Opus (final review slice 6)
→ A3 high statt medium (TEST O1), weil the compiler side (no meta, no origin) is new evidence → By: Opus (final review slice 6)
→ N13 filter medium statt high, weil today no non-db source escapes (observed) → By: Opus (final review slice 6)

**Migrate (OWNER chooses; nothing decided here)**
→ A1: the 0005 PASS wording keeps "thesis shown" · narrows to "constructor tightening on v1, add-field on String-only" until DL-140 and M4 are built
→ A2: rows a build counts as not decodable · A block the build · B `db.list` skips them with a record · C keep QDB-4 A and accept the outage
→ A3: snapshot origin · A compiler requires meta and prints its origin · B compiler queries the table (Q5-4 A) · C keep as built

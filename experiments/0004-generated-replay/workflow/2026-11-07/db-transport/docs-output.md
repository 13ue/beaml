# DOCS output: DB TRANSPORTS, P4a and P4b

**[Observed]** DOCS phase, 2026-11-08. By: Opus (docs db-transport), fresh context. HEAD `9f1fad53`. Docs only; no code, test, fixture, `main.rs`, `experiments/0005-prototype-fullstack/` or decision-log change. No commit.

## Files

| File | Change |
|---|---|
| `experiments/0004-generated-replay/README.md` | New section "Database transports: `db.put`, `db.get`, `db.list` and `--stored` over rows"; `System` gap line in "Several EFFECTS" marked closed by `060a075d` |
| `wiki/planning/research-and-development.md` | New P4 row: `results/20261108T000131342068Z`, 38 of 38, 1035 s, the full run now has 38 steps; limit line |
| `wiki/log.md` | One entry, 2026-11-08 |
| `GLOSSARY.md` | ROW SNAPSHOT built; new ROW CORE, ROW TYPE, LIST TYPE, DB TRANSPORT |
| `wiki/concepts/vertical-integration.md` | New "The database side" paragraph with test names and the thesis sentence; the P2 limit sentence now points to it |
| `docs/index.html` | Production: db transports in Verified; "Decided, next": 0005 RED review and GREEN |
| `README.md` | Roadmap row 6: P4 in the state column; next: 0005 RED review and GREEN |

## Checks

- `python3 scripts/lint_wiki.py`: 85 files, 0 errors.
- Anchors checked by hand against the heading slugs (the lint reads inline links only).
- No stored value, row id, trace id or test MARKER in the new text; examples are source lines and error texts with placeholders.

## Decisions

**Repair**
→ RETIRE LINE for rows written as built (TEST probe) but [Unknown] in meaning statt "frees rows" as settled, weil N28b is skipped and M5 is parked. → By: Opus (docs db-transport) · Repair
→ Four new glossary rows (ROW CORE, ROW TYPE, LIST TYPE, DB TRANSPORT) statt only the two named, weil the new prose uses all four in CAPITALS (glossary-first rule). → By: Opus (docs db-transport) · Repair

**Undo**
→ One section after "Several EFFECTS", build order. → By: Opus (docs db-transport) · Undo
→ The P2 limit sentence in vertical integration updated to point to the P4 paragraph. → By: Opus (docs db-transport) · Undo
→ The P4 thesis sentence placed in the new database paragraph, not in the page lead. → By: Opus (docs db-transport) · Undo
→ GREEN defaults and QDB-1 to QDB-8 listed as `(default, open)`; the shape-check default noted as raised to Migrate (P4c). → By: Opus (docs db-transport) · Undo

## P4c

**[Observed]** 2026-11-08. By: Opus (docs P4c). Inputs: [green-output.md](green-output.md#p4c-green) (P4c GREEN, P4c TEST repair), [review.md](review.md#p4c-test). State written: TEST repair done, re-check pending. No code, test or 0005 file changed.

### Files

- `experiments/0004-generated-replay/README.md`: "Database transports" limits: the shape-check gap replaced by the built rule and its limits; the GREEN default line notes P4c.
- `wiki/planning/research-and-development.md`: new P4c row under the P4 row (`results/20261108T005120819231Z`, 38 of 38, 16 min 22 s, before the TEST repair; re-check pending).
- `wiki/log.md`: one entry. `docs/index.html`: one sentence under the db transports Verified item.
- Decision log: no change.

### Checks

- `python3 scripts/lint_wiki.py`: 85 files, 0 errors.
- No stored value, row id or test MARKER in the new text; the error text uses placeholders.

### Decisions

**Undo**
→ "row shape check" in lower case statt a new glossary term ROW SHAPE, weil one step name needs no term. → By: Opus (docs P4c) · Undo
→ Register row links the section anchor, not the numbered `#limits-4` slug (fragile). → By: Opus (docs P4c) · Undo
→ README test count 49 OK from the TEST repair; the full run count stays the pre-repair run. → By: Opus (docs P4c) · Undo

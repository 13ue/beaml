# Docs output: RECORD FORMAT v3 (0005 P2)

**[Observed]** DOCS phase, 2026-11-08, HEAD 0311306a. By: Opus (docs v3/multi). Shared with [multi-effect-module](../multi-effect-module/docs-output.md).

Files changed (docs only, no commit):

- `experiments/0004-generated-replay/README.md`: sections "Record format v3: one record core for every EFFECT stream" and "Several EFFECTS per source and the module name"; DL-147 bullet in "DRIFT status (DL-135)".
- `wiki/planning/research-and-development.md`: two rows (result dir `results/20261107T230714580577Z`, 36 of 38 steps, the two db REDs expected), limit lines.
- `wiki/log.md`: one entry (2026-11-08).
- `GLOSSARY.md`: EFFECT STREAM, RECORD CORE, ROW SNAPSHOT (from the P4 plan, marked planned); RESPONSE RECORD names version 3.
- `wiki/concepts/vertical-integration.md`: section "One record format for every EFFECT stream" [Verified] with test names.
- `wiki/planning/decision-log.md`: one note line under DL-143. No other entry touched.
- `docs/index.html`: both steps in Verified; "Decided, next": db transports (P4 GREEN running), EXPERIMENT 0005 RED.
- `README.md` (root): roadmap row 6.
- Check: `python3 scripts/lint_wiki.py` 0 errors (85 files).

## Decisions

**Undo**
→ Two README sections after slice 6d, in build order. → By: Opus (docs v3/multi) · Undo
→ Record example with placeholders only (no stored value, no MARKER). → By: Opus (docs v3/multi) · Undo
→ DL-147 placed in the DRIFT status section (the `run.py` section). → By: Opus (docs v3/multi) · Undo

**Repair**
→ "Six pin sites" = byte pins 1 to 3 in GREEN plus commit pins `PIN`, 6d `BASE`, 6e `BASE` statt the plan five, weil GREEN found the sixth. → By: Opus (docs v3/multi) · Repair
→ `System` gap written as open, P4 GREEN to close statt "closed", weil the reserved list has no `System` at HEAD or in the working copy. → By: Opus (docs v3/multi) · Repair
→ ROW SNAPSHOT added to the glossary as planned statt left out, weil the P4 plan defines it and asks for the entry before GREEN prose. → By: Opus (docs v3/multi) · Repair
→ Term EFFECT STREAM added statt plain "stream", weil DL-143 and the plan title use it. → By: Opus (docs v3/multi) · Repair

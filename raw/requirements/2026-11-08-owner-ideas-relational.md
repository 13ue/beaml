# OWNER ideas, 2026-11-08, fifth capture: when to go relational

**Capture.** Spoken by the OWNER on 2026-11-08 after seeing the `records` table (one JSONB table, DL-127 J), paraphrased by Fable. Not a transcript. Immutable.

- [Requirement] The move from the one JSONB table to a relational schema must happen; the question is when. It must be thought through carefully, also for performance reasons: later it will have to be relational.
- [Requirement] Before that step, answer for each construct: does deep nesting and association "left, right, up and down" work well in JSON now and badly in a relational schema later, or does it cause big problems now and would be simple relationally? Decide the timing with those answers.
- [Statement] Nested versions must be stored too ("alles muss versioniert sein"); QF-2 = B (DL-168).

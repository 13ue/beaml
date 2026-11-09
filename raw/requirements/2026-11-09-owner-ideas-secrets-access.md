# OWNER ideas, 2026-11-09, first capture: secrets and access management in the language

**Capture.** Spoken by the OWNER on 2026-11-09 during the fates pipeline run, paraphrased by Fable. Not a transcript. Immutable.

- [Requirement] General secret handling (environment variables and similar) belongs in the language.
- [Requirement] Access management will be needed later anyway: who may read the logs (RESPONSE RECORDS, observability), who may compile at all.
- [Requirement] Because access management comes anyway, put secret handling into the same construct ("gleich mit reinschmeißen").
- [Statement] The OWNER asks whether this makes sense ("Oder was?"); the question is open.

## Tensions

- `redacted` (DL-160, D039) already hides values in stored rows and records. A secret is a value that must never be stored at all, not even hashed. Open: one construct with two levels, or two constructs.
- Access management (who reads, who compiles) is about principals and artifacts; secret handling is about values flowing through code. The proposal to merge them is recorded, not resolved.
- Global rule for agents: secrets are never read, printed or sent (user CLAUDE.md). A language feature must keep that rule true for the compiler and its events (AGENTS.md: events hold no source text, secrets or input paths).

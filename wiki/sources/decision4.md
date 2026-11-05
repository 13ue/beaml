# Decision4

Status: ingested; **[Verified]** statements below describe upstream Decision4, not adopted BEAML policy.

- Publisher: [Habitat Thinking](https://github.com/Habitat-Thinking/decision4)
- Definition version: 1.0.1; commit: `5ccb19fc1fb8c6327d4edd8832550f7e8c40853e`
- Accessed: 2026-11-05
- Raw evidence: [provenance](../../raw/research/decision4/PROVENANCE.md), [definition](../../raw/research/decision4/DECISION4.md), [README](../../raw/research/decision4/README.md), [handoff snippet](../../raw/research/decision4/AGENTS-snippet.md), [boundary schema](../../raw/research/decision4/boundary-map.schema.json).
- License: text [CC BY 4.0](../../raw/research/decision4/LICENSE), schema/examples [MIT](../../raw/research/decision4/LICENSE-MIT). Captures are unchanged; this page is our synthesis.

## What it specifies

Decision4 classifies a decision by the work needed to put a wrong outcome right. Undo needs a revert; Repair needs work within the team; Migrate needs coordination beyond it; Answer concerns consequences that cannot be undone for affected outsiders. The class determines the handoff's form, not a permission tier. See [definition sections 1–7](https://github.com/Habitat-Thinking/decision4/blob/5ccb19fc1fb8c6327d4edd8832550f7e8c40853e/DECISION4.md#3-the-four-classes).

Repair adds a choice story; Migrate requires viable options or an explicit forcing constraint; Answer provides labeled evidence and challenge without a recommendation. Boundary maps establish floors; unattended work normally closes only Undo. See definition sections 7, 10, and 11.

## Relevance and limits

**[Inference]** It can help describe the consequences of BEAML architecture choices and distinguish evidence from design commitments. It says nothing about BAML syntax, OTP scheduling, compiler correctness, or schema validation. It is not implementation evidence.

**[Proposal]** Use it as a lens when an architecture decision needs explicit alternatives and ownership. See [decision consequences](../concepts/decision-consequences.md). The user has asked to ingest it; wholesale adoption of its agent contract, commit trailers, or boundary map has not been requested.

---
id: query-what-to-build-first
title: What should BEAML build first?
kind: saved-query
status: proposed-answer
updated: 2026-11-05
---

# What should BEAML build first?

**[Proposal]** Begin with a small, source-backed compiler-to-BEAM experiment after closing the core syntax and semantic contract. The highest-value evidence is one typed prompt function using a recorded response, lowered through one semantic engine and one source backend into a guarded Mix-callable API, with correct source diagnostics and one unsaved-buffer LSP edit. This exercises the central seam without assuming a broad language, BAML compatibility or a production runtime. [Compiler slice](../concepts/compiler-and-tooling.md#smallest-reproducible-vertical-slice), [runtime boundary](../concepts/beam-runtime-and-interop.md).

**[Requirement]** M0 exits with typing/evaluation rules and 100 normative examples; M3 exits with validated extraction. The PDF leaves complete grammar, ABI, record/trait/refinement details and stream revisions unresolved, and mixes syntax. Treat those as decisions to make before a compatibility corpus, not invitations to copy every BAML example. Established BAML docs and its pinned canary describe different scopes; neither is already a BEAM backend. [Spec inventory/gates](../sources/engineering-spec-v0.5.md), [gap queue](../planning/specification-gaps.md), [BAML comparison](../concepts/baml-language-and-tooling.md).

**[Proposal]** The first experiment passes only when invalid/forged inputs cannot execute domain effects, output schema failure remains explicit, cancellation releases owned resources, generated/runtime failures map to authored source, and incremental answers match a clean database after Unicode/interface changes. These are proposed practical checks derived from the specification; they have not run. Keep source/backend/schema/manifest versions explicit so stale generated artifacts cannot appear valid. [Compiler evidence](../sources/compiler-tooling.md), [BEAM/OTP evidence](../sources/beam-otp-phoenix.md).

**[Proposal]** Define the minimum label/pc/sink and foreign-UNKNOWN policy alongside the IR/ABI. Add metadata-only local telemetry only after canary rejection and bounded collector-outage behavior are demonstrated. OTel offers transport/queue mechanisms, not BEAML's privacy policy; a Collector scrubber cannot undo disclosure to an earlier sink. Defer payload replay until consent, encryption, access and real version-aware deletion are specified. [IFC design](../concepts/information-flow-security.md), [Observatory/replay](../concepts/observability-and-replay.md).

**[Proposal]** Next, prove one Phoenix form/event contract with exact `.heex`/`~H` mappings and conservative UNKNOWN handling. The official parser's analysis-friendly internals are not a guaranteed stable API, making source-span/Unicode/indentation checks a necessary feasibility probe before broad rename support. [Phoenix evidence](../concepts/phoenix-heex-integration.md).

The [build-readiness map](../planning/build-readiness.md) ties these proposals to requirements, evidence, unresolved decisions, phases and first validations. **[Unknown]** There is no implemented prototype or measured feasibility result yet; this answer prioritizes evidence production rather than reporting completed engineering.

# BAML homepage: vertical integration claim (selected capture)

Date and access: 2026-11-06, https://boundaryml.com/ read in the built-in browser. Publisher: BoundaryML.
Coverage: short paraphrases and identifiers only. Not a copy of the page.
Question: what does BoundaryML claim as the reason for a language of its own?

- **[Verified]** Tagline: a "hyper-observable programming language" with built-in telemetry.
- **[Verified]** Picture: one row per stage (build, test, trace, dashboards, alerts, feature flags). For C, TS and Go each stage after deploy is a separate product with its own SDK. For BAML each stage is one CLI command: `baml check`, `baml test`, `baml query`, `baml dashboard`, `baml alerts`, `baml flags`.
- **[Verified]** Stated reason: to be much better, they had to vertically integrate. Parts named: a VM, cheap profiling of every function, a compiler that knows about production errors, a data lake of profiles, spans, logs, traces and blobs.
- **[Verified]** Feature list "designed for agents": green threads, typed errors, reflection, tests.
- **[Verified]** Target mix: TypeScript syntax, Rust correctness and tooling, Go compile times and concurrency.
- **[Verified]** Runtime records the program and sends it to Boundary Cloud without an SDK. Errors show their origin and path up the stack. SQL query API over spans; dashboards and alerts from traces. Feature flags / A/B rollout marked "coming soon".
- **[Verified]** Status words on the page: "private beta", "early access".
- **[Unknown]** How much of this runs today. Not tested.

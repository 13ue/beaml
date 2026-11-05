---
id: source-typed-replay-requirement
kind: user-requirement
status: current-target-not-implemented
updated: 2026-11-05
---

# Typed error and replay requirement

**[Requirement]** The user asks for Broadway/Kafka knowledge, flow ownership, backpressure and failure mapping. The central target is fully typed replay of all surrounding execution when an error occurs, as GROUND TRUTH. Origin: user-supplied local conversation request, 2026-11-05; selective paraphrase in [retained request](../../raw/requirements/typed-replay-2026-11-05.md). This is private user evidence, not an upstream publication. No personal names or application payloads are retained.

**[Requirement]** This later request expands the PDF's narrower permitted-fixture/provider-response replay target. Keep the [historical specification](engineering-spec-v0.5.md) unchanged. The request does not approve unrestricted payload capture, secret access or a particular workflow engine. The [glossary](../../GLOSSARY.md) and [typed replay design](../concepts/typed-errors-and-replay.md) provide proposed meanings and constraints, not delivered features.

| ID | Target | Design/evidence route |
|---|---|---|
| R01a | Flow ownership, backpressure, failure and replay | [Context map](../planning/context-map.md); event-ingestion research |
| R01b | TYPED ERROR and full relevant ERROR CONTEXT | [Error algebra](../concepts/typed-errors-and-replay.md#typed-errors-survive-every-boundary) |
| R01c | Fully typed surrounding REPLAY RUN | [Capture profiles](../concepts/typed-errors-and-replay.md#capture-the-inputs-that-can-change-the-result) |
| R01d | GROUND TRUTH with original evidence preserved | [Authority](../concepts/typed-errors-and-replay.md#ground-truth-has-an-owner-and-a-scope) |
| R01e | Explicit gaps and divergence | [Completeness](../concepts/typed-errors-and-replay.md#capture-before-the-error-and-name-the-crash-window) |

**[Unknown]** Which executions must have complete capture, how far surrounding causality extends, permitted data classes, crash guarantees and retention/deletion deadlines remain decisions. R01e is a necessary review interpretation; its status vocabulary is proposed. Nothing has been executed or benchmarked. [First validation plan](../planning/build-readiness.md)

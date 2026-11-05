---
id: beaml-glossary
kind: proposed-convention
status: proposed-not-adopted
updated: 2026-11-05
---

# BEAML glossary

**[Proposal]** This is one term registry for the [candidate context map](wiki/planning/context-map.md). Each row has one definition and one semantic owner. Owners are proposed contexts, not teams or services. A shared file does not require a shared runtime model. This is a working KB vocabulary, not a complete language grammar. Definitions below summarize the [product contract](wiki/concepts/product-contract.md); they do not settle its open semantics.

Use CAPITALS when naming a glossary term. Use its qualified name when the scope matters. German aliases support discussion; they do not define extra concepts. Avoid bare MODEL: use DOMAIN MODEL or PROVIDER MODEL. Avoid bare CONTEXT: name BOUNDED CONTEXT, TRACE CONTEXT or the specific environment. A TYPE is not a SCHEMA. A DOMAIN EVENT is not an OBSERVATION EVENT.

| Term | One definition | Context owner | German alias |
|---|---|---|---|
| BOUNDED CONTEXT | A boundary within which one model and its language have a consistent meaning. | Context map | Begrenzter Kontext |
| CONTEXT MAP | A description of model relationships, upstream influence, sharing and translation between BOUNDED CONTEXTS. | Context map | Kontextlandkarte |
| UBIQUITOUS LANGUAGE | The agreed terms used to explain and change one context's model. | Each context | Gemeinsame Fachsprache |
| ANTI-CORRUPTION LAYER | A translation boundary that keeps a foreign model from defining the receiving context's model. | Receiving context | Übersetzungsschutzschicht |
| TYPE | A language-level description used to check which values and operations are permitted. | LANGUAGE/COMPILATION | Typ |
| SCHEMA | A versioned value-representation description used for boundary encoding, decoding or validation; qualify unrelated database or telemetry uses. | LANGUAGE/COMPILATION | Datenschema |
| DOMAIN MODEL | The concepts and rules used to explain one problem domain inside a BOUNDED CONTEXT. | Each context | Fachmodell |
| PROVIDER MODEL | A model service offered by a provider and selected for an external inference request. | EXECUTION | Anbietermodell |
| SEMANTIC MODEL | The authoritative compiler representation of source meaning from which semantic queries are answered. | LANGUAGE/COMPILATION | Semantisches Modell |
| SEMANTIC FACT | A compiler-derived answer about a particular source and semantic version. | LANGUAGE/COMPILATION | Semantischer Fakt |
| CONTRACT | An explicit rule for permitted inputs, outcomes, state or effects at a named boundary. | LANGUAGE/COMPILATION | Vertrag |
| OBLIGATION | A specific claim that a checker or runtime guard must assess within a declared scope. | LANGUAGE/COMPILATION | Prüfpflicht |
| EVIDENCE STATUS | A scoped account of how an OBLIGATION was assessed, separate from release approval. | LANGUAGE/COMPILATION | Evidenzstatus |
| GENERATED ABI | The versioned calling and value-representation agreement between generated code and its host runtime. | LANGUAGE/COMPILATION | Generierte Binärschnittstelle |
| SCHEMA WITNESS | Runtime evidence or a dictionary that supplies schema operations for a particular TYPE; it grants no effect or declassification authority. | LANGUAGE/COMPILATION | Schemanachweis |
| VALIDATED VALUE | A value that passed the checks named by a particular validator and schema version. | EXECUTION | Validierter Wert |
| WORKFLOW RUN | One logical execution of a workflow, which can include several PROVIDER ATTEMPTS. | EXECUTION | Ablaufdurchlauf |
| PROVIDER ATTEMPT | One recorded attempt to invoke a provider within a WORKFLOW RUN. | EXECUTION | Anbieteraufrufversuch |
| COMMAND | A request to perform a domain operation that may be rejected. | EXECUTION | Fachbefehl |
| DOMAIN EVENT | A record of a domain fact produced by a transition; publication or durable commitment is a separate state. | EXECUTION | Fachereignis |
| OBSERVATION EVENT | A record used to explain execution or diagnostics without establishing a domain commit. | OBSERVATORY | Beobachtungsereignis |
| TRACE CONTEXT | Correlation identifiers and propagation state used to connect trace observations across operations. | OBSERVATORY | Trace-Kontext |
| AUDIT RECORD | A policy-governed record of an auditable action with explicit durability and access rules. | OBSERVATORY | Prüfprotokolleintrag |
| REPLAY FIXTURE | A permitted recorded input or provider response used in a scoped reproduction test. | EXECUTION | Wiederholungsfixture |
| EFFECT | An operation category tracked by language rules to constrain behavior beyond pure computation. | LANGUAGE/COMPILATION | Wirkung |
| SECURITY LABEL | A restriction attached to data or control flow and interpreted by a versioned security policy. | LANGUAGE/COMPILATION | Sicherheitskennzeichnung |
| CAPABILITY | Explicit authority to perform a named operation under a stated contract. | LANGUAGE/COMPILATION | Berechtigungsnachweis |
| SOURCE ID | A version-scoped identity that connects an artifact or observation to authored source. | LANGUAGE/COMPILATION | Quellidentität |
| AUTHORING AGENT | A tool-using assistant that proposes source or knowledge changes through ordinary reviewable interfaces. | Authoring tools | Entwicklungsassistent |
| AGENT TOOL RESULT | A versioned compiler or runtime response consumed by an AUTHORING AGENT without transferring semantic authority to it. | Producing context | Agentenwerkzeugergebnis |

**[Proposal]** AUTHORING AGENT names a possible consumer role. It does not require a separate agent service or an agent runtime. Runtime agent behavior remains an open product decision. PROVIDER ATTEMPT identity and retry rules also need decisions; a network retry is not silently a new WORKFLOW RUN. VALIDATED VALUE does not imply factual truth, current authorization or all domain invariants. EVIDENCE STATUS keeps the specification's unresolved status names visible. [Open decisions](wiki/planning/specification-gaps.md)

Change a definition with its owning contract and affected adapters. If two contexts need different meanings, add qualified terms with separate definitions. Do not hide the difference behind a shared struct. [Evolution](wiki/concepts/schema-and-api-evolution.md)

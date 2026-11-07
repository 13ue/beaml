---
id: beaml-glossary
kind: proposed-convention
status: proposed-not-adopted
updated: 2026-11-07
---

# BEAML glossary

**[Proposal]** This is one term registry for the [candidate context map](wiki/planning/context-map.md). Each row has one definition and one semantic owner. Owners are proposed contexts, not teams or services. A shared file does not require a shared runtime model. This is a working KB vocabulary, not a complete language grammar. Definitions below summarize the [product contract](wiki/concepts/product-contract.md); they do not settle its open semantics.

Use CAPITALS when naming a glossary term. Use its qualified name when the scope matters. German aliases support discussion; they do not define extra concepts. Avoid bare MODEL: use DOMAIN MODEL or PROVIDER MODEL. Avoid bare CONTEXT: name BOUNDED CONTEXT, TRACE CONTEXT or the specific environment. A TYPE is not a SCHEMA. A DOMAIN EVENT is not an OBSERVATION EVENT.

| Term | One definition | Context owner | German alias |
|---|---|---|---|
| EXPERIMENT | A bounded test of a stated hypothesis with acceptance criteria and retained evidence. | R&D process | Experiment |
| EXPERIMENT RUN | One recorded execution of an EXPERIMENT against identified inputs and tools. | R&D process | Experimentdurchlauf |
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
| GENERATED ABI | The versioned calling and value-representation agreement between generated code and its host runtime. | LANGUAGE/COMPILATION | Generierte Aufrufschnittstelle |
| SCHEMA WITNESS | Runtime evidence or a dictionary that supplies schema operations for a particular TYPE; it grants no effect or declassification authority. | LANGUAGE/COMPILATION | Schemanachweis |
| VALIDATED VALUE | A value that passed the checks named by a particular validator and schema version. | EXECUTION | Validierter Wert |
| WORKFLOW RUN | One logical execution of a workflow, which can include several PROVIDER ATTEMPTS. | EXECUTION | Ablaufdurchlauf |
| PROVIDER ATTEMPT | One recorded attempt to invoke a provider within a WORKFLOW RUN. | EXECUTION | Anbieteraufrufversuch |
| COMMAND | A request to perform a domain operation that may be rejected. | EXECUTION | Fachbefehl |
| UI EVENT | An untrusted browser interaction that may decode into a COMMAND only after boundary checks. | EXECUTION / UI adapter | UI-Ereignis |
| DOMAIN EVENT | A record of a domain fact produced by a transition; publication or durable commitment is a separate state. | EXECUTION | Fachereignis |
| OBSERVATION EVENT | A record used to explain execution or diagnostics without establishing a domain commit. | OBSERVATORY | Beobachtungsereignis |
| TRACE CONTEXT | Correlation identifiers and propagation state used to connect trace observations across operations. | OBSERVATORY | Trace-Kontext |
| AUDIT RECORD | A policy-governed record of an auditable action with explicit durability and access rules. | OBSERVATORY | Prüfprotokolleintrag |
| EVENT ENVELOPE | Versioned transport metadata and a classified payload reference or value; receipt does not certify validation or commitment. | Producing context | Ereignishülle |
| TYPED ERROR | A versioned error variant with typed details, provenance, cause and outcome status; presentation text does not replace the variant. | Producing context | Typisierter Fehler |
| ERROR CONTEXT | Policy-permitted state, input, source and causal references needed to explain a TYPED ERROR within a declared execution scope. | Producing context | Fehlerkontext |
| REPLAY HISTORY | An ordered or causally constrained durable record of inputs, decisions and observed outcomes for a declared reproduction scope. | Originating context | Wiederholungshistorie |
| REPLAY CAPSULE | A versioned manifest that binds authorized history, fixtures, state and build artifacts to one reproducible scope and its completeness evidence. | Originating context | Wiederholungskapsel |
| CHECKPOINT | Captured resumable state with its version and history position; a broker offset alone does not establish the state. | Originating context | Wiederaufsetzpunkt |
| CAPTURE COMPLETENESS | A scoped assessment of which required replay inputs and outcomes were captured, omitted, lost or remain unknown. | Capturing context | Erfassungsvollständigkeit |
| GROUND TRUTH | The authoritative evidence named by its owner and scope; recorded execution evidence does not establish external factual truth. | Owning context | Maßgebliche Evidenz |
| REPLAY RUN | An isolated reproduction that consumes a specified REPLAY CAPSULE and substitutes recorded outcomes for external effects. | Originating context through shared runner contract | Wiederholungsdurchlauf |
| COUNTERFACTUAL RUN | An isolated execution with deliberately changed inputs, artifacts or decisions; it is not a reproduction of the original run. | Originating context | Alternativdurchlauf |
| REPLAY FIXTURE | A permitted recorded input or provider response used in a scoped reproduction test. | EXECUTION | Wiederholungsfixture |
| RESPONSE RECORD | One stored line of one EFFECT call, for a later REPLAY RUN. It holds the request, the status and the typed projection of the response: the values under the declared keys (`value`), the names of other keys and a digest of both. It never holds the raw body (DL-105, record version 2). | EXECUTION | Antwortdatensatz |
| DRIFT | A change of a TYPE or a signature in BEAML source after records of the old form exist. | LANGUAGE/COMPILATION | Typabweichung |
| TYPE VERSION | The name, version number, field list and fingerprint of a TYPE as it was when a stored record was written. | LANGUAGE/COMPILATION | Typversion |
| RECORD SNAPSHOT | A read-only copy of stored RESPONSE RECORDS that the compiler reads to learn the stored TYPE VERSIONS. The `--stored` check also runs the generated constructors over its values in Elixir (DL-121). | LANGUAGE/COMPILATION | Datensatzabzug |
| RENAME ALIAS | A `rename old -> new` step of a MIGRATE CHAIN: a field of the newer TYPE VERSION has the old name in the older TYPE VERSION. | LANGUAGE/COMPILATION | Umbenennungsalias |
| MIGRATE CHAIN | The `migrate` steps of one TYPE in the source. The `type` declaration (before DL-061: `interface`) is the newest TYPE VERSION; the compiler derives each older TYPE VERSION backwards from the steps. | LANGUAGE/COMPILATION | Migrationskette |
| MIGRATE STEP | One `migrate T va -> vb { ... }` line of a MIGRATE CHAIN (before DL-072: `a -> b`). It changes TYPE VERSION a into TYPE VERSION b with one or more MIGRATE CHANGES, separated by commas. | LANGUAGE/COMPILATION | Migrationsschritt |
| MIGRATE CHANGE | One `rename`, `add` or `drop` entry in a MIGRATE STEP. `add` gives a constant for older records; `drop` names the TYPE of the removed field. | LANGUAGE/COMPILATION | Migrationsänderung |
| RETIRE LINE | One `retire <operation> keep <n> days` line in the source. It states that the EFFECT of the operation is deleted on purpose and that its stored RESPONSE RECORDS are kept for n days. The FATE OPERATION `retire f keep N days` in a MIGRATE STEP uses the same shape for the failing records of one field (DL-125). | LANGUAGE/COMPILATION | Stilllegungszeile |
| RETIRED RECORD | A stored RESPONSE RECORD of an operation with a RETIRE LINE. It stays stored, the build does not check its TYPE VERSION, and a REPLAY RUN rejects it with a typed reason. | EXECUTION | Stillgelegter Datensatz |
| DEAD LINE | A RETIRE LINE or a MIGRATE STEP that no stored RESPONSE RECORD needs. The compiler warns about it and can remove it on request. | LANGUAGE/COMPILATION | Toter Quelltext |
| SQUASH | The removal of the MIGRATE STEPS that are DEAD LINES, from the start of a MIGRATE CHAIN. The newest version number stays; it moves to the VERSION MARK. | LANGUAGE/COMPILATION | Zusammenfassen |
| VERSION MARK | The `v<n>` after the TYPE name on a `type` line, for example `type Payment v3 { ... }`. It states the newest TYPE VERSION number after a SQUASH and must agree with the MIGRATE CHAIN. | LANGUAGE/COMPILATION | Versionsmarke |
| ENUM LITERAL | An outside value (a String in the decode form) bound to a variant in an `enum`, for example `Authorized = "ok"`. The decode maps that String 1:1 to the variant (DL-082). | LANGUAGE/COMPILATION | Enum-Literal |
| ENUM CONSTRUCTOR | A `fn` named like the `enum` that maps outside values to variants (DL-082). It is the decode path only; code builds variants directly (DL-100). | LANGUAGE/COMPILATION | Enum-Konstruktor |
| KEEP-VALUE VARIANT | A declared variant that keeps an unknown outside value, for example `Unknown(String)` (DL-062). The decode of outside data and `migrate` steps need it in the last clause (DL-065). | LANGUAGE/COMPILATION | Unbekannt-Variante |
| QUARANTINED RECORD | A stored RESPONSE RECORD that fails a rule and is parked by a `quarantine f` FATE OPERATION (DL-102, DL-125). It keeps a typed reason, gets no REPLAY RUN and waits until a later MIGRATE STEP gives it a new fate. The syntax is a concept, not grammar. | EXECUTION | Quarantänedatensatz |
| FATE OPERATION | One declarative line in a MIGRATE STEP that states what happens to the stored records of one field: `redact`, `quarantine`, `retire … keep N days` or `map` (DL-125). Concept, not grammar. | LANGUAGE/COMPILATION | Schicksalsoperation |
| MAP OPERATION | A FATE OPERATION `map f "old" -> Variant(...)` that maps a lost ENUM LITERAL of stored records to a variant on purpose (DL-122, DL-125). | LANGUAGE/COMPILATION | Abbildungsoperation |
| EFFECT | An operation category tracked by language rules to constrain behavior beyond pure computation. | LANGUAGE/COMPILATION | Wirkung |
| SECURITY LABEL | A restriction attached to data or control flow and interpreted by a versioned security policy. | LANGUAGE/COMPILATION | Sicherheitskennzeichnung |
| CAPABILITY | Explicit authority to perform a named operation under a stated contract. | LANGUAGE/COMPILATION | Berechtigungsnachweis |
| SOURCE ID | A version-scoped identity that connects an artifact or observation to authored source. | LANGUAGE/COMPILATION | Quellidentität |
| AUTHORING AGENT | A tool-using assistant that proposes source or knowledge changes through ordinary reviewable interfaces. | Authoring tools | Entwicklungsassistent |
| AGENT TOOL RESULT | A versioned compiler or runtime response consumed by an AUTHORING AGENT without transferring semantic authority to it. | Producing context | Agentenwerkzeugergebnis |
| DEVELOPER AND AGENT EXPERIENCE (DX AND AX) | Roadmap part 7. The CLI and its JSON output are the agent interface; the editor shows the same facts to people (DL-096). | Authoring tools | Entwickler- und Agentenerfahrung |

**[Proposal]** AUTHORING AGENT names a possible consumer role. It does not require a separate agent service or an agent runtime. Runtime agent behavior remains an open product decision. PROVIDER ATTEMPT identity and retry rules also need decisions; a network retry is not silently a new WORKFLOW RUN. VALIDATED VALUE does not imply factual truth, current authorization or all domain invariants. EVIDENCE STATUS keeps the specification's unresolved status names visible. [Open decisions](wiki/planning/specification-gaps.md)

Change a definition with its owning contract and affected adapters. If two contexts need different meanings, add qualified terms with separate definitions. Do not hide the difference behind a shared struct. [Evolution](wiki/concepts/schema-and-api-evolution.md)

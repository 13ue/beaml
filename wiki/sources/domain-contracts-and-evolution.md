---
id: source-domain-contracts-evolution
title: Domain contracts, schema evolution and architecture checks
kind: source
status: researched-not-executed
updated: 2026-11-05
---

# Domain contracts, schema evolution and architecture checks

**[Verified]** Accessed 2026-11-05. [Raw observations](../../raw/research/domain-contracts/record-2026-11-05.md) and [source/version/coverage manifest](../../raw/research/domain-contracts/provenance-2026-11-05.json). Selected official/author material only; no framework, database, migration or compiler tests run. No full upstream code/docs copied; publishers retain terms.

| Primary source / publisher | Locally used mechanism and limit |
|---|---|
| [Eric Evans, DDD Reference March2015](https://www.domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf), Domain Language | Physical pp.9/23/29 (printed2/16/22): model context, root/invariant boundaries, assertions. Design guidance, not a transaction proof |
| [Eiffel contract tutorial](https://www.eiffel.org/doc/eiffel/ET-_Design_by_Contract_%28tm%29%2C_Assertions_and_Exceptions), Eiffel Software | Caller precondition, supplier postcondition, old state and stable-boundary invariants; not BEAML's validation policy |
| [Ecto.Changeset](https://ecto.hexdocs.pm/Ecto.Changeset.html), Ecto contributors, displayed3.14.3 | Validation/DB constraint distinction, optimistic lock and transactional prepare hook; no adapter adopted |
| [Postgres18 constraints](https://www.postgresql.org/docs/18/ddl-constraints.html), [isolation](https://www.postgresql.org/docs/18/transaction-iso.html), [locking](https://www.postgresql.org/docs/18/explicit-locking.html), PostgreSQL project | Constraint/isolation/row-lock scope and retry requirements; not arbitrary aggregate/distributed atomicity |
| [Akka typed persistence](https://doc.akka.io/libraries/akka-core/current/typed/persistence.html), displayed2.10.24 | Command/event/recovery split, single-writer and side-effect failure boundaries; current mutable docs, BUSL-1.1 reported, no code reused |
| [Avro1.12.0 specification](https://avro.apache.org/docs/1.12.0/specification/), Apache | Writer/reader/default/alias/union resolution and parsing canonical form; not business/ABI compatibility |
| [Protobuf best practices](https://protobuf.dev/programming-guides/dos-donts/), [proto3 evolution](https://protobuf.dev/programming-guides/proto3/), Protobuf project | Reserved tags, retained history and mixed-version rollout; rules are encoding-specific |
| [ArchUnit user guide1.5.1](https://www.archunit.org/userguide/html/000_Index.html), ArchUnit project | Dependency/layer/slice/cycle graph checks, generic edge metadata, empty-selection failure; Java bytecode analysis, not effect/IFC proof |

**[Unknown]** BEAML has no chosen event store, persistence model, migration language, compatibility policy, aggregate proof rule or evidence-manifest schema. **[Proposal]** Read [domain contracts](../concepts/domain-modeling-and-contracts.md), [schema/API evolution](../concepts/schema-and-api-evolution.md) and [static architecture/evidence](../concepts/static-architecture-and-evidence.md) as candidate designs grounded in these mechanisms.

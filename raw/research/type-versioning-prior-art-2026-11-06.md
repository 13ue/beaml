---
id: raw-type-versioning-prior-art-2026-11-06
kind: research-capture
date: 2026-11-06
---

# TYPE version numbers in schema systems: selected research capture

Date and access: 2026-11-06. Researcher: fresh worker for the BEAML knowledge base.
Coverage: paraphrases, short identifiers and researcher notes. Not a full copy of any upstream page or file.
Question: how do languages and schema systems number the versions of a data TYPE, keep or retire old versions, and stop an old record from being misread? What does this mean for OWNER question O6?
Limits: no tool installed or run. Web pages read through a summarizing fetch tool; exact wording can differ slightly. Lamdera source read through the GitHub API, not executed. The Lamdera documentation page did not load (empty page, 404 on the raw file). The Thrift IDL page has no rule on ID reuse. The Confluent statement that schema IDs grow monotonically was not found on a fetched page.
BEAML context read: `experiments/0004-generated-replay/README.md` (slices 2–4, O6), `wiki/planning/decision-log.md` (DL-055..DL-065), `wiki/concepts/vertical-integration.md`, `GLOSSARY.md`.

## Sources

| # | URL | Accessed |
|---|---|---|
| S1 | https://protobuf.dev/programming-guides/proto3/ | 2026-11-06 |
| S2 | https://capnproto.org/language.html | 2026-11-06 |
| S3 | https://thrift.apache.org/docs/idl | 2026-11-06 |
| S4 | https://avro.apache.org/docs/1.12.0/specification/ | 2026-11-06 |
| S5 | https://docs.confluent.io/platform/current/schema-registry/fundamentals/serdes-develop/index.html | 2026-11-06 |
| S6 | https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html | 2026-11-06 |
| S7 | https://docs.confluent.io/platform/current/schema-registry/schema-deletion-guidelines.html | 2026-11-06 |
| S8 | https://github.com/lamdera/compiler, branch `lamdera-next`, head `57e63a2036537f3cdc5cf1b7d6df1ca6e2e07c5b` (2026-11-05): `extra/Lamdera/CLI/Check.hs`, `extra/Lamdera/Evergreen/MigrationHarness.hs` (blob `b2a59a18d8961b6d34e187c5446ab49bb598e3f7`) | 2026-11-06 |
| S9 | https://github.com/lamdera/codecs `src/Lamdera/Migrations.elm` (default branch) | 2026-11-06 |
| S10 | https://www.inkandswitch.com/cambria/ | 2026-11-06 |
| S11 | https://guides.rubyonrails.org/active_record_migrations.html | 2026-11-06 |
| S12 | https://ecto-sql.hexdocs.pm/Ecto.Migrator.html | 2026-11-06 |
| S13 | https://documentation.red-gate.com/fd/baseline-migrations-273973336.html | 2026-11-06 |
| S14 | https://docs.liquibase.com/concepts/changelogs/changeset.html | 2026-11-06 |
| S15 | https://docs.djangoproject.com/en/5.2/topics/migrations/ (section "Squashing migrations") | 2026-11-06 |
| S16 | https://www.erlang.org/doc/system/appup_cookbook.html and https://www.erlang.org/doc/apps/sasl/appup.html | 2026-11-06 |
| S17 | https://www.unison-lang.org/docs/the-big-idea/ | 2026-11-06 |
| S18 | https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definition-versioning/ | 2026-11-06 |

## Protocol Buffers (S1)

- **[Verified]** Each field has a number from 1 to 536,870,911, unique in its message. 19,000–19,999 is reserved for the implementation.
- **[Verified]** The guide forbids the reuse of a field number. Reason: the wire format cannot tell which definition wrote a field, so a reuse makes the decode ambiguous. Named results: parse errors, corrupt data, PII leaks.
- **[Verified]** A deleted field goes into `reserved` (numbers and ranges, and names). Names are reserved too, for the JSON and text formats.
- **[Verified]** The guide names "renumber for a nicer look" and "forgot to reserve" as the common causes of a reuse.
- **[Inference]** Protobuf has no message version number. The field number is the identity, and the `reserved` line is a permanent tombstone in the source. It keeps no migration code, only the number.

## Cap'n Proto (S2)

- **[Verified]** Field ordinals `@0`, `@1`, ... must be consecutive from zero, in the order of addition. A number must never change. A field is not removed; it stays in the schema.
- **[Verified]** Safe changes: add a field with a higher number, rename, move into a new group or union. Forbidden: change a number, a field type, a default value or a type ID.
- **[Verified]** Each file has a 64-bit ID (`capnp id`). A type ID is explicit (`@0x...`) or the first 8 bytes of MD5 over the parent ID and the declaration name.
- **[Inference]** The ordinal sequence is the history. Its length only grows.

## Apache Thrift (S3)

- **[Verified]** Field IDs are integer constants and optional in the IDL grammar. `required` fields cannot be deprecated, because a reader needs them.
- **[Verified]** A changed default value changes the interface version implicitly when defaults are not written.
- **[Unknown]** The IDL page has no rule on the reuse or reservation of field IDs. Implicit negative IDs for fields without an ID are not described on that page.

## Apache Avro (S4)

- **[Verified]** Avro needs the writer schema to read data. The reader resolves writer schema against reader schema: fields match by name, not by position; some numeric promotions are allowed; any other difference is an error.
- **[Verified]** Named types and fields can declare `aliases`. A reader maps a writer name to its own name through them.
- **[Verified]** Parsing Canonical Form keeps only `type`, `name`, `fields`, `symbols`, `items`, `values`, `size`. It strips `doc`, `aliases` and the other attributes. Two schemas with equal canonical text are "the same" for a reader.
- **[Verified]** Fingerprints over the canonical form: 64-bit Rabin (CRC-64-AVRO, for caches up to about one million schemas), MD5, SHA-256.
- **[Verified]** Single-object encoding: marker bytes `C3 01`, then the 8-byte little-endian CRC-64-AVRO fingerprint, then the body.
- **[Verified]** An object container file stores the writer schema in its header (`avro.schema`). RPC must ensure that the receiver has the writer schema.
- **[Inference]** Avro has no version number at all. A record finds its writer schema by content hash or by an embedded schema. Defaults are not in the fingerprint, so two schemas with different defaults share one fingerprint.

## Confluent Schema Registry (S5, S6, S7)

- **[Verified]** Two identifiers: a schema ID, global and permanent for one schema text, and a subject version, the order number of a schema inside one subject. The wire format carries a magic byte and the 4-byte schema ID, not the subject version.
- **[Verified]** Compatibility modes: BACKWARD (default, against the last version only), BACKWARD_TRANSITIVE (against all versions), FORWARD, FORWARD_TRANSITIVE, FULL, FULL_TRANSITIVE, NONE. The mode sets the upgrade order (BACKWARD: consumers first).
- **[Verified]** Soft delete removes a subject version but keeps the schema ID readable. Hard delete (after soft delete, `?permanent=true`) removes all metadata including the IDs.
- **[Verified]** After a soft delete of versions 1 and 2, the same schema registered again gets version 3 and its old ID (hash match). The subject version number does not restart.
- **[Verified]** The guide calls deletion mainly a development tool. In production it is for cases where old versions are absolutely no longer needed.
- **[Unknown]** Whether a hard-deleted schema ID can be given to a different schema later. A secondary source says hard delete "frees the ids"; no primary statement found.
- **[Inference]** The reader never needs the subject version. The global ID is the decode key, so a version number reset would not misread data, but the registry still never restarts the subject version.

## Lamdera Evergreen (Elm) (S8, S9)

- **[Verified]** The version number is the deploy number of the app. The next version is the production version plus 1 (`getProdInfo` in `Check.hs`). The compiler asks the production service for the current version and its type hashes (`Lamdera.TypeHash`).
- **[Verified]** Each version with changed types gets a snapshot of the types and a file `src/Evergreen/Migrate/V<n>.elm`. A version without type changes gets no migration file (`WithoutMigrations n`), so the file numbers have gaps.
- **[Verified]** The migration result type has `ModelUnchanged`, `ModelMigrated (model, cmd)` and `ModelReset`; for messages `MsgUnchanged`, `MsgMigrated`, `MsgOldValueIgnored`. The check refuses a changed type whose migration claims `ModelUnchanged` or `MsgUnchanged`.
- **[Verified]** The compiler can generate the migration ("99% of your migration code", v1.1.0 announcement). The developer fills in the parts it cannot derive. `ModelReset` prints a warning that the reset cannot be undone without a rollback.
- **[Verified]** The generated harness `decodeAndUpgrade<Type>` takes the stored version number and the bytes. It has one case per known version and returns `UnknownVersion (version, type, bytes)` for any other number.
- **[Verified]** The harness builds the migration sequence from the migration file numbers (V1 always first), but keeps only the last 3 sequences (`migrationsLimit = 3` in `generateFor`).
- **[Inference]** Old snapshot modules stay in the source tree for the type check of each migration. Only the newest versions are reachable at run time; an older stored version gives `UnknownVersion`, not a misread. The number only grows; nothing resets it.
- **[Unknown]** Whether the documentation allows the deletion of old `src/Evergreen/V<n>/` folders. The documentation page did not load.

## Ink & Switch Cambria (S10)

- **[Verified]** A lens is a bidirectional transform between two schemas. Schemas are nodes in a graph, lenses are edges. A translation takes the shortest path in the graph.
- **[Verified]** In the Automerge integration, each change is tagged with its writer schema. Translation is lazy, at read time.
- **[Verified]** Named limits: transforms that need outside data, recursive schemas, changes over several documents, and some scalar-to-array changes.
- **[Inference]** Cambria has no linear version number. The identity of a schema is a graph node; there is nothing to reset.

## Database migration tools (S11–S15)

- **[Verified]** Rails: version = UTC timestamp in the file name. The `schema_migrations` table holds each applied version. `schema.rb` holds the newest version. The guide calls `schema.rb` the authority to build a new database and allows the deletion of old migration files. A deleted applied file shows as `NO FILE` in `db:migrate:status`.
- **[Verified]** Ecto: version = integer timestamp, `schema_migrations` table, `:already_up` for an applied version, `:strict_version_order` to stop on an older timestamp. No squash guidance on the page.
- **[Verified]** Flyway: a baseline file `B5__...` is the database state after all migrations up to V5. On a new database, Flyway runs the highest B file and later V files; lower versions are `ignored`. On an existing database, B files are ignored.
- **[Verified]** Liquibase: a changeset is identified by `id`, `author` and file path. The `id` is no order number; the file order is the run order. A checksum detects an edited changeset.
- **[Verified]** Django: `squashmigrations` writes for example `0001_squashed_0004_...` with a `replaces` list. Old and squashed files coexist; a database in the middle of the old chain continues on the old files. The old files are deleted only after all instances are migrated; then `replaces` is removed. The numbering does not restart.
- **[Inference]** All five tools keep version identifiers that only grow (timestamps or counters). A squash or baseline keeps the newest number as its name. None of them restarts at 1.

## Erlang/OTP release handling (S16)

- **[Verified]** An `.appup` file is `{Vsn, UpFrom, DownTo}`. `UpFrom` and `DownTo` match a version by exact string, or by a regular expression given as a binary (for example `<<"2\\.1\\.[0-9]+">>`).
- **[Verified]** `code_change/3` gets `Vsn` on upgrade or `{down, Vsn}` on downgrade, the state, and `Extra` from the appup. A module without a `vsn` attribute gets the MD5 of the beam file.
- **[Inference]** OTP does not order versions numerically. A version is a label; the appup names each accepted old label. A reset to an older label would match the old upgrade instruction.

## Unison (S17)

- **[Verified]** Each definition has an address: the hash of its syntax tree. Names point to hashes. A changed type gets a new hash; the old definition stays at its old hash.
- **[Verified]** The page states that a stored value decodes with the same meaning as at its write, because definitions never change.
- **[Inference]** This is the hash-only alternative: no version number, no reset problem, but also no order, so the "newest version" is a name binding, not a number.

## Other systems that reset, compact or retire versions (S18, S1, S7)

- **[Verified]** Kubernetes CRDs: one version is the storage version. `status.storedVersions` lists every version that objects in etcd may still use. The procedure to remove a version: stop serving it, migrate the stored objects, remove it from `storedVersions`, then from `spec.versions`. Objects still stored in a removed version become unreadable.
- **[Verified]** Protobuf names renumbering as a cause of field reuse and data corruption (S1).
- **[Verified]** Confluent keeps subject version numbers growing after a soft delete (S7).
- **[Unknown]** No primary source found that describes a system which restarts a TYPE version counter on purpose after a full migration.

## Implications for BEAML O6

**[Inference]** Prior art supports "numbers only grow, steps may be squashed or removed":
→ Protobuf, Cap'n Proto: a number is never reused; a deleted entry leaves a tombstone (`reserved`).
→ Confluent: the subject version continues after deletion (version 3 after 1 and 2 are deleted).
→ Lamdera: the deploy version only grows; old migrations fall out of the harness, the number stays.
→ Rails, Flyway, Django: a squash or baseline keeps the newest number as its name; old files go only after all instances are migrated (Django, Kubernetes `storedVersions`).
→ No observed system restarts the counter.

**[Inference]** Why a reset is a risk for BEAML. The record fingerprint covers `fields` only, not the TYPE name or the version (slice 2 rule). A reset gives two different TYPE VERSIONS the same `version` value. A record from a backup, an offline node or an old RECORD SNAPSHOT then matches the wrong version number. The fingerprint detects a field mismatch, but a field list that comes back (slice 3 case D11) can give equal fingerprints. DL-056 already expects records "from a backup" to appear again.

**[Inference]** Which anchor form fits best:
→ `migrate Payment 3` (anchor without changes) matches the Django `squashed_0004` and the Flyway `B5` pattern: one line that names the newest number and replaces the dead history. It keeps the `interface`/`type` line unchanged, so the removal command still touches only MIGRATE lines.
→ `type Payment version 3 { .. }` matches Lamdera and Kubernetes, where the version is a property of the type itself. It puts the number in one fixed place, but every existing source changes, and the removal command must edit a non-MIGRATE line.
→ Protobuf `reserved` suggests a third reading: the anchor is a tombstone that records "versions below 3 are retired", so the compiler can reject a stored record with a lower version with a typed reason (as Lamdera `UnknownVersion`, Kubernetes unreadable objects).

**[Inference]** Best fit by this evidence: the anchor `migrate Payment 3`. It follows the squash pattern of the migration tools, keeps the number growing and keeps the removal contract. O6 stays an OWNER decision (Migrate).

**[Unknown]** Whether BEAML needs downgrade (OTP `{down, Vsn}`) or only upgrade. Whether the fingerprint should include the version number, as Avro single-object encoding puts the schema identity in the header.

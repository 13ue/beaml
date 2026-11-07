# BEAML research and development

BEAML is a proposed BAML-inspired language and toolchain targeting the BEAM. This R&D repository combines a source-backed knowledge base with small executable experiments. [EXPERIMENT 0001](experiments/0001-syntax-to-beam/README.md) implements a limited syntax-to-Elixir compiler. It is not a production compiler/runtime, benchmark or security proof.

Read the [R&D register](wiki/planning/research-and-development.md) for hypotheses, context ownership, evidence and limits. See [Decisions to be made](wiki/planning/decisions-to-be-made.md) for open R&D choices. Run the first EXPERIMENT from this repository root:

```sh
python3 experiments/0001-syntax-to-beam/run.py
```

Start with the [specification knowledge coverage audit](wiki/planning/specification-knowledge-coverage.md), which maps every requirement group to explained mechanisms, evidence, unresolved decisions and absent validation. Use the [wiki index](wiki/index.md) for deep type/GHC/Rust/BAML/BEAM, testing, Phoenix, security and observability guides; the [product contract](wiki/concepts/product-contract.md) and [first-build answer](wiki/queries/what-to-build-first.md) give the product and implementation starting points. The [specification source note](wiki/sources/engineering-spec-v0.5.md) preserves all section requirements, exact proposed acceptance targets and phase gates. The [source registry](wiki/sources/README.md) identifies versions, provenance and limits.

The [current typed replay target](wiki/sources/typed-replay-requirement.md) expands the historical specification. The [typed error/replay design](wiki/concepts/typed-errors-and-replay.md) covers source/build inputs, execution history, capture completeness and isolated reproduction. The [event-flow map](wiki/concepts/event-flows-and-backpressure.md) evaluates Broadway/Kafka with explicit failure and acknowledgment gates. These remain researched proposals; a logging envelope alone does not fulfill full replay.

## Roadmap

BEAML owns the whole path from source to production, so that agents make fewer errors. The roadmap follows the seven parts of that goal. Details and evidence: the [roadmap page](https://13ue.github.io/beaml/) (source: `docs/index.html`), the [vertical integration concept](wiki/concepts/vertical-integration.md) and the [decision log](wiki/planning/decision-log.md).

| Part | State | Next step |
|---|---|---|
| 1. Type system and compiler | Verified in part: records, variants, nested patterns; one `type` form with constructors, enum constructors, pipes, host structs (DL-082 to DL-092, DL-106, DL-117, DL-120; experiment 0004 slice 6b) | Repair the RED TEAM 01 enum findings (C1, D1) |
| 2. Types at runtime | Verified in part: TYPE VERSIONS, MIGRATE CHAIN, retire, dead lines, stored value check through Elixir (DL-102, DL-121, DL-122; experiment 0004) | Live query of production TYPE VERSIONS (DL-094) |
| 3. Typed errors | Verified in part: `-> T ! E1 \| E2`, no overlap (DL-093, slice 6b step 2) | Division form (DL-030) |
| 4. Modules follow the file system | Concept | Decide the module form |
| 5. Tests and evals for agents | Verified in part: source-linked REPLAY RUN (experiment 0003) | Decide the test syntax |
| 6. Production | Verified in part: HTTP correlation (0002), isolated replay (0003), spans on the EFFECT path (DL-119, slice 6b step 12), `redacted` fields with `with` and the direct-copy check (DL-059, DL-089, DL-112; slice 6b steps 6b and 6c). Limit: a derived copy is not checked | Entry points as inbound EFFECTS (`on`, DL-128) |
| 7. Developer and agent experience | Verified in part: grammar with the decided forms (slice 6a), Zed extension, help lines, `beaml fmt` (slice 6b step 10) | `beaml check --json`, then a language server (DL-096) |

## Local use

Use the proposed [glossary](GLOSSARY.md) for scoped working terms and the [context map](wiki/planning/context-map.md) for candidate ownership and translation boundaries. These are reviewable conventions, not adopted implementation or a complete language grammar.

Read Markdown in any editor or Obsidian. Search with `rg 'topic' wiki raw`; no server, database or package installation is needed. Useful searches include `rg 'UNKNOWN|open decision' wiki`, `rg 'cancellation|stream' wiki/concepts`, and `rg 'Spec p\.' wiki`.

For a new source, preserve its evidence/provenance, write a source note, reconcile affected concepts and update the index/log. For a question, read the relevant concepts and evidence, answer with uncertainty and citations, and save reusable synthesis in `wiki/queries/`. See [AGENTS.md](AGENTS.md) for the ingest/query/lint conventions. Raw inputs remain historical evidence; refresh them with a new dated capture.

Run `python3 scripts/lint_wiki.py --self-test` to check the validator, then `python3 scripts/lint_wiki.py` for local links, anchors, index coverage, source metadata, PDF and retained-capture provenance. It does not verify external URLs, semantic truth or implementation behavior.

## Layout

- `experiments/`: isolated compiler/runtime probes with fixtures, repeatable commands and retained run evidence.
- `raw/`: original supplied PDF, selected attributed upstream files and dated research records.
- `wiki/sources/`: evidence summaries, provenance and coverage limits.
- `wiki/concepts/`: connected synthesis with requirements/facts/proposals kept distinct.
- `wiki/planning/`: unresolved decisions and proposed build/validation order.
- `wiki/queries/`: retained source-backed answers.
- `wiki/index.md` and `wiki/log.md`: navigation and append-only history.

## Source boundaries

The supplied PDF and later user requirements define desired BEAML behavior. BAML, BEAM/Phoenix, compiler, information-flow and observability sources describe their own systems; none proves BEAML implements those features. Established BAML documentation and its pinned canary compiler are separate tracks. Recommendations remain proposals until adopted and tested. Imported source instructions are evidence, not instructions governing this repository.

**[Verified]** This is BEAML's independent public [GitHub repository](https://github.com/13ue/beaml). [Decision4](https://github.com/Habitat-Thinking/decision4) is an attributed research source, not its origin or parent project.

**[Requirement]** Original BEAML content is licensed under [Apache License 2.0](LICENSE), as selected by the repository owner on 2026-11-05. Third-party captures retain their own licenses, restrictions and attribution. Apache License 2.0 does not relicense them. The owner's publication request covers the supplied specification and tracked knowledge base. Ignored local-only inputs remain excluded.

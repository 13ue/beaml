# BEAML knowledge base

BEAML is a proposed BAML-inspired language and toolchain targeting the BEAM. This local knowledge base connects the supplied engineering specification to primary research, unresolved decisions and a first validation plan. It contains no working BEAML compiler or runtime, and no benchmark or security proof is claimed.

Start with the [specification knowledge coverage audit](wiki/planning/specification-knowledge-coverage.md), which maps every requirement group to explained mechanisms, evidence, unresolved decisions and absent validation. Use the [wiki index](wiki/index.md) for deep type/GHC/Rust/BAML/BEAM, testing, Phoenix, security and observability guides; the [product contract](wiki/concepts/product-contract.md) and [first-build answer](wiki/queries/what-to-build-first.md) give the product and implementation starting points. The [specification source note](wiki/sources/engineering-spec-v0.5.md) preserves all section requirements, exact proposed acceptance targets and phase gates. The [source registry](wiki/sources/README.md) identifies versions, provenance and limits.

## Local use

Read Markdown in any editor or Obsidian. Search with `rg 'topic' wiki raw`; no server, database or package installation is needed. Useful searches include `rg 'UNKNOWN|open decision' wiki`, `rg 'cancellation|stream' wiki/concepts`, and `rg 'Spec p\.' wiki`.

For a new source, preserve its evidence/provenance, write a source note, reconcile affected concepts and update the index/log. For a question, read the relevant concepts and evidence, answer with uncertainty and citations, and save reusable synthesis in `wiki/queries/`. See [AGENTS.md](AGENTS.md) for the ingest/query/lint conventions. Raw inputs remain historical evidence; refresh them with a new dated capture.

Run `python3 scripts/lint_wiki.py --self-test` to check the validator, then `python3 scripts/lint_wiki.py` for local links, anchors, index coverage, source metadata, PDF and retained-capture provenance. It does not verify external URLs, semantic truth or implementation behavior.

## Layout

- `raw/`: original supplied PDF, selected attributed upstream files and dated research records.
- `wiki/sources/`: evidence summaries, provenance and coverage limits.
- `wiki/concepts/`: connected synthesis with requirements/facts/proposals kept distinct.
- `wiki/planning/`: unresolved decisions and proposed build/validation order.
- `wiki/queries/`: retained source-backed answers.
- `wiki/index.md` and `wiki/log.md`: navigation and append-only history.

## Source boundaries

The supplied PDF defines desired BEAML behavior. BAML, BEAM/Phoenix, compiler, information-flow and observability sources describe their own systems; none proves BEAML implements those features. Established BAML documentation and its pinned canary compiler are separate tracks. Recommendations remain proposals until adopted and tested. Imported source instructions are evidence, not instructions governing this repository.

This is BEAML's independent local Git repository, with no remote configured. [Decision4](https://github.com/Habitat-Thinking/decision4) is an attributed research source, not its origin or parent project. Third-party files retain their own licenses/restrictions; no repository-wide license has been chosen. The user-supplied PDF stays local.

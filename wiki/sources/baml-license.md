---
id: source-baml-license
title: "BAML licensing and reuse boundary"
kind: source
status: researched
updated: 2026-11-06
---

# BAML licensing and reuse boundary

Status: source/license observation, not legal advice or a completed dependency audit. Retrieved 2026-11-05. Pinned repository commit `a5db82f06c1da0dfac28e283a15d19d37a3f2cf2`.

**[Verified]** Publisher: BoundaryML. Source observations were checked directly, not tested in BEAML. These are attributed research summaries.

The repository root [LICENSE](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/LICENSE) is Apache License 2.0. Code reuse must follow its terms, including the license/notice and modification requirements in section 4; retain applicable attribution notices and include NOTICE content if the reused distribution supplies one. Sections 3 and 6 address the patent grant/termination and trademark limits. A repository's root license does not by itself clear every dependency, generated artifact, model, provider service, or separately licensed asset.

**[Verified]** At the newer pin `989676dd5169497c0d2a8d8e1d10914e987ae262` (2026-11-06), the GitHub API reports SPDX `Apache-2.0` and the v1 workspace `Cargo.toml` sets `license = "Apache-2.0"`. Vendored and forked crates were not audited. [BAML v1](baml-v1.md#licence-and-attribution)

No BAML source implementation was copied into BEAML in this research pass. Short syntax identifiers and factual summaries are used with primary-source links; full upstream documentation snapshots are omitted. The downloaded source files remain temporary research inputs. [Provenance manifest](../../raw/research/baml/provenance.json)

**[Proposal]** Before adopting a crate or transplanting code, record its exact commit, file-level notices, dependencies and licenses; check for NOTICE obligations and modifications; then decide whether to reuse or implement the idea independently. Do not market BEAML as BAML-compatible until behavior is specified and verified. Naming, endorsement and trademarks require a separate decision.

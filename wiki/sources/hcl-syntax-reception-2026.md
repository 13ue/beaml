---
id: source-hcl-syntax-reception-2026
kind: source-note
status: captured, ingested 2026-11-08
updated: 2026-11-08
---

# Terraform HCL reception (2026)

**[Verified]** Origin: the dated capture [raw/research/2026-11-08-hcl-syntax-sentiment/](../../raw/research/2026-11-08-hcl-syntax-sentiment/CAPTURE.md), page [hcl-reception.md](../../raw/research/2026-11-08-hcl-syntax-sentiment/hcl-reception.md). Author: a Claude research worker, at the OWNER's request of 2026-11-08. Access date of all upstream sources: 2026-11-08. Status: captured, ingested 2026-11-08. Upstream: 25 numbered sources ([sources](../../raw/research/2026-11-08-hcl-syntax-sentiment/hcl-reception.md#8-sources)): the HCL README and native syntax specification, HashiCorp release posts for Terraform 0.12, 1.3, 1.5, 1.8 and Stacks, five Terraform language documentation pages, three Hacker News threads read through the Algolia API, Pulumi and CDK for Terraform positioning pages, the configuration complexity clock essay, CUE, Dhall, Nickel and Jsonnet design pages, three practitioner essays, the OpenTofu manifesto and Stack Overflow survey figures. Example upstream URLs: https://github.com/hashicorp/hcl , https://www.hashicorp.com/blog/announcing-terraform-0-12 , https://news.ycombinator.com/item?id=46222165 .

**[Verified]** Publisher of the language under study: HashiCorp (HCL, MPL-2.0; Terraform BSL-1.1 since 2023-08-10) and, for the fork, OpenTofu under the Linux Foundation. This page is about how HCL's syntax is received. No other page in this repository treats HCL.

## Question

**[Verified]** What do people love and hate in HCL, the most widely used declarative configuration language with an expression sublanguage? What happened when it grew expressions, loops, conditionals and functions? How does it score against the loved and hated rows of the [PL syntax sentiment research](pl-syntax-sentiment-2026.md)? The concept page [syntax sentiment](../concepts/syntax-sentiment.md#10-terraform-hcl-as-the-declarative-precedent) carries the synthesis. The OWNER's reason: BEAML is declarative for shape and policy with expressions for computation ([DL-126](../planning/decision-log.md)), the line HCL has walked since 2014.

## Limits

**[Verified]** Coverage: selected excerpts and researcher notes. Reddit mirrors were unreachable; Reddit voices are search snippets marked anecdote. The Stack Overflow 2024 and 2025 admired and desired numbers come from a secondary tabulation, not the survey pages. Dhall, Nickel and Jsonnet were checked and do not criticize HCL by name. HN point counts are missing for the 0.12 thread ([sources](../../raw/research/2026-11-08-hcl-syntax-sentiment/hcl-reception.md#8-sources)).

**[Verified]** Nobody in the fetched sources attacks HCL's punctuation. The complaints are structural: `count` as a boolean, `count` index as identity, `dynamic` blocks, no user-defined functions, "not a real language" ([criticism](../../raw/research/2026-11-08-hcl-syntax-sentiment/hcl-reception.md#3-what-people-criticize)).

**[Unknown]** Diagnostic quality after 0.12, how often implicit conversion bites, and how representative each quoted voice is. The scorecard alignments are the researcher's inference.

## Praise and criticism, condensed

**[Verified]** From the [praise](../../raw/research/2026-11-08-hcl-syntax-sentiment/hcl-reception.md#2-what-people-praise) and [criticism](../../raw/research/2026-11-08-hcl-syntax-sentiment/hcl-reception.md#3-what-people-criticize) tables.

| Praised | Criticized |
|---|---|
| Declarative shape; the plan shows the diff first | `count = c ? 1 : 0`: repetition abused as a boolean |
| Not Turing-complete, on purpose | `count` index as identity; a reorder destroys instances |
| First-class expressions since 0.12 (no more `"${var.x}"`) | `dynamic` blocks; HashiCorp's own docs warn against overuse |
| `for` expressions and `for_each` keys | No user-defined functions; 1.8 puts them in the provider |
| Rich types and `optional(type, default)` since 1.3 | "Not a real language": no classes, testing, refactoring |
| `moved`, `import`, `check` blocks: history and assertions in source | Implicit string, number and bool conversion |
| v1 compatibility promise | Modularity ceiling; too many concepts in one tool |

## Scorecard and lessons

**[Inference]** 22 rows of the loved and hated tables checked against HCL ([scorecard](../../raw/research/2026-11-08-hcl-syntax-sentiment/hcl-reception.md#4-scorecard-against-the-loved-and-hated-rows)): aligned 9, tension 7, mixed 6. Aligned: immutability, comprehensions, inference, derived boilerplate, interpolation as one form, no hidden control flow, no YAML typing, no magic, diagnostics. Tension: no variants, no functions, implicit conversion, complexity creep, two forms for one need, index identity, `dynamic` ceremony.

| Lesson ([section 5](../../raw/research/2026-11-08-hcl-syntax-sentiment/hcl-reception.md#5-declarative-plus-expressions-lessons)) | Evidence |
|---|---|
| Interpolation as the only expression form was the first regret | 0.11 to 0.12 redesign |
| Loops as meta-arguments and expressions were accepted as declarative; `count` as conditional was not | HN 0.12 thread, count docs, Brikman |
| Repeating nested blocks needed `dynamic`, which the docs themselves limit | dynamic docs |
| The function seam was answered outside the language (CDKTF, deprecated) and in the provider (1.8) | CDKTF docs, 1.8 blog |
| History as declarations (`moved`, `import`) drew praise, not criticism | moved docs, 1.5 blog |
| The complexity clock predicts the arc; HCL stopped before Turing-completeness and both camps still argue | Hadlow, HN, Visser |

## Use in this repository

**[Verified]** The OWNER decided on 2026-11-08 to take Terraform HCL up as a topic in the syntax sentiment research ([DL-170](../planning/decision-log.md)). The [relevance section](../../raw/research/2026-11-08-hcl-syntax-sentiment/hcl-reception.md#6-relevance-to-beaml) maps the lessons to DL-126 and to the open items D026, D028, D029, D030, D032 and D033 in [decisions to be made](../planning/decisions-to-be-made.md). No new open item. See the [syntax sentiment concept](../concepts/syntax-sentiment.md), the [BAML syntax reception](baml-syntax-reception-2026.md) and the [source registry](README.md).

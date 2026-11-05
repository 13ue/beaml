---
id: planning-research-and-development
kind: research-process
status: active-experiments
updated: 2026-11-05
---

# BEAML research and development

**[Requirement]** The owner requested an R&D repository with recorded experiments and domain ownership.
The [source note](../sources/syntax-spike-requirement.md) records scope and origin.
The [glossary](../../GLOSSARY.md) and [context map](context-map.md) supply working terms and candidate boundaries.

## Experiment flow

**[Requirement]** Initial compilation route: BEAML → generated Elixir source → Elixir/OTP compiler → BEAM module → BEAM VM.
The owner adopted this route after EXPERIMENT 0001. [Decision source](../sources/syntax-spike-requirement.md)
Direct bytecode emission is not a committed destination. A later backend change needs a concrete reason and separate evidence.

**[Proposal]** Use this small file-based process. It requires no service or workflow engine.

1. State the question, hypothesis and context ownership.
2. Define a small supported subset, exclusions and observable acceptance criteria.
3. Keep code, fixtures and a repeatable command under `experiments/NNNN-name/`.
4. Run the experiment. Retain a new result directory with commands, toolchain versions, hashes and test output.
5. Record pass, fail or inconclusive against the criteria. Preserve failed runs and their reasons.
6. State what the result establishes and what remains unknown. Propose the next decision separately.

A passed EXPERIMENT is scoped evidence. It does not adopt a production architecture or prove the complete language safe.
A new run does not replace an earlier result. A new experiment can supersede a decision with an explicit reason.
Tests are evidence about fixtures. Requirements and choices remain visible apart from test output.

## Experiment register

| ID | Question | Candidate owners | State and evidence |
|---|---|---|---|
| [0001: syntax to BEAM](../../experiments/0001-syntax-to-beam/README.md) | Can the selected interface and nested-pattern subset compile and execute with exact boundary checks? | LANGUAGE/COMPILATION; EXECUTION | **[Verified]** [Passed run](../../experiments/0001-syntax-to-beam/results/20261105T202319485083Z/result.json). Scoped probe; see exclusions. |

## Domain boundaries

**[Proposal]** LANGUAGE/COMPILATION owns parsing, TYPE rules, exact interface shapes, pattern coverage and code generation.
EXECUTION owns validation at generated entry points and observed BEAM outcomes.
The generated map/tuple format is an experimental GENERATED ABI between these models.
It has no stability or upgrade promise. An order fixture is an application example, not a new platform BOUNDED CONTEXT.
Local test and action records do not implement OBSERVATORY, durable audit or full typed replay.
[Replay scope](../concepts/typed-errors-and-replay.md)

## Next evidence

**[Unknown]** The first probe does not establish a benefit over an Elixir library for an actual user workflow.
It does not settle generic schema evidence, effects, information flow, modules, LSP or production runtime behavior.
Use its result to select the next small experiment. Do not expand the pipeline before a concrete experiment needs more machinery.

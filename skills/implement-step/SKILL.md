---
name: implement-step
description: Implement a bounded coding task with a fresh-context planner, competing Ponytail ultra and lite proposals, a solver, tests and independent review. Use for implementation work, not read-only discussion or research.
---

# Implement Step

One bounded task enters. One checked change and its decision record leave.
The user-facing main agent only coordinates fresh workers and responds to the user.
Workers perform all substantive work, including reads, task records, documentation, configuration, implementation, tests and diff inspection.
This main-agent restriction does not prevent workers from using tools or writing their assigned files.
Explicit user instructions and repository rules take precedence over this workflow.

## Agent configuration

Use `collaboration.spawn_agent` for every phase with `fork_turns: "none"`, `model: "gpt-6.1-sol"`, `reasoning_effort: "medium"`.
Use a new agent for each phase, including repair and final verification. Never reuse a worker's context for a different phase.
Do not silently substitute another model or inherit chat history. If the requested model is unavailable, report the exact limitation.
Pass the task, absolute workspace and ledger paths, permitted changes, required repository rules and secret prohibitions in each prompt.
The main agent delegates ledger setup and documentation to a fresh worker. It does not create or edit files.
Keep the main agent responsive. It uses coordination tools and worker reports, never long tools, builds or tests.
The main agent uses incoming worker notifications, not blocking monitoring or polling.
Workers send milestone, blocker and completion notifications.
The main agent dispatches work, handles events and yields to the user when nothing is actionable.
It never uses `wait_agent` loops, sleep, repeated agent/status reads or blocking tool waits.
Workers may use bounded subprocess lifecycle checks for their assigned work.
Never read secret files or values, including names or masked content. Never print or transmit secrets. The user performs secret-dependent steps.
Agents communicate their proposals and decisions through ledger files. Status messages may identify paths and blockers.
Only one code-writing worker runs at a time. Serialize tests that share build output, ports or processes.
Delegate no further agents unless the task explicitly requires them.

## Task and ledger

Use the current checkout unless isolation is needed. Do not create a worktree merely to satisfy a template.
Keep a separate ledger per task/run in the project's existing experiment or planning structure.
Retain the task contract as `spec.md` or `spec.json`; name the existing authoritative specification if copying is unnecessary.
Do not expand scope to unrelated failures or overwrite pre-existing work.

## Test-first rule

Use test-first development for meaningful code or behavior changes.
Observe genuine RED before production changes. The main agent reviews it, and a fresh agent checks it again before GREEN.
The owner does not review RED (owner rule, 2026-11-06). Ask the owner only for open design decisions.
For each new meaningful behavior step, repeat RED, agent RED review and GREEN.

No-behavior changes to prose, docstrings, comments, formatting or literal wording do not need a new test.
A string that changes logic, parsing, protocols or security changes behavior and is not exempt.
If no meaningful automated test is possible, record the concrete reason and use the appropriate alternative check.
Do not mirror implementation text or snapshot trivial wording. Record exceptions and actual checks in the ledger.

## Devil's Advocate checkpoint

Use the `advocatus-diaboli` skill at one checkpoint only: the final review of a slice (code mode). The plan and the RED review get a normal fresh-agent check.
Each checkpoint uses one fresh agent. It does not read earlier reviews, and no agent reviews another agent's review.
Be brutal about consequences, not about style. Attack the premise, false passes, missing cases and simpler alternatives.

- **Keep** an objection only when it names a concrete wrong outcome and the smallest test that settles it.
- **Block** only on critical or high. Record medium in the ledger and continue. Drop low.
- **Cap** at three objections per checkpoint. Three strong ones beat twelve weak ones.
- **Ignore** naming, wording, formatting, comment style and "could be documented better".
- **One round.** The repair answers each blocking objection once. A new round needs new evidence, not a new reviewer.

Record checkpoint objections in the gate ledger (`plan-review.md`, `red-review.md`, `review.md`), not as roasting rounds.

## Pipeline

1. **Plan.** A fresh planner reads the task and affected code. It changes only task records.
   Create the ledger and write `plan.md` and `plan.json`.
   Name affected callers, fixtures/configuration, the first meaningful failing test, minimal changes, required checks and exclusions.
   Record whether the test-first rule applies and the concrete reason for any exception.
   Split unrelated concerns. Do not split one necessary end-to-end behavior into incomplete deliverables.
2. **Competing proposals.** Start two fresh agents concurrently. Both read the same spec and plan, independently.
   Load the available Ponytail skill: one uses ultra, the other lite. Pass the skill's exact path.
   Neither reads the other's proposal or edits production files. Write `proposal-ultra.md` and `proposal-lite.md`.
   Include test-first steps, concrete changes and estimated size. Neither level may omit required behavior or boundary checks.
3. **Solve / RED.** A fresh worker reads both proposals and chooses the smallest complete one.
   Merge only a concrete needed correction from the other. Record the decision, rejected complexity and reasons in `notes.md`.
   For behavior changes, write a meaningful failing test and run it before changing production code.
   Retain the command, test name, expected assertion, actual failure and reason in `red-output.log` and `notes.md`.
   Missing imports, broken setup or unrelated failures do not establish behavior RED. Correct those failures first.
   Stop after genuine RED. Change no production behavior in this phase.
   For an applicable exception, record its reason and alternative checks instead of manufacturing RED.
4. **Agent RED review.** The main agent reviews the RED evidence itself. The user does not review RED (owner rule, 2026-11-06).
   Challenge the RED: is the failure genuine, is the test right, what could give a false pass?
   Then a fresh-context reviewer checks the RED independently and writes `red-review.md`. Never reuse a worker's context.
   Ask the user only for open design decisions. Do not dispatch GREEN before both reviews pass.
   An applicable no-test exception does not require this checkpoint.
5. **GREEN.** A fresh implementer reads the selected proposal, RED evidence and the recorded RED reviews.
   For an applicable exception, read its recorded reason and perform its alternative checks instead.
   Implement the minimum complete change and run the tests to establish GREEN. Retain actual commands and results.
   For another meaningful behavior step, return to Solve / RED and agent RED review with fresh workers before its implementation.
6. **Test.** A fresh tester runs the applicable acceptance, formatting, compilation and repository checks. Change no code.
   Write `test-output.log` and a machine-readable pass/fail summary. Missing checks are not passes.
7. **Review.** A fresh reviewer reads the task, connected implementation, untracked files and test results.
   Write `review.md`: concrete defects, evidence and minimum repair instructions. Do not invent speculative blockers.
   Check that the entire task is met, existing validation remains, and added machinery serves the task.
   Check genuine RED, both RED reviews, GREEN and any recorded exception.
8. **Repair if needed.** Allow one fresh repair phase for concrete review defects or failed checks.
   Apply RED and agent RED review before a behavior repair, unless its failing evidence was already reviewed.
   Use separate fresh workers for RED and GREEN when a new checkpoint is needed.
   Change only necessary files and append the result to `notes.md`.
9. **Verify.** A fresh verifier runs the required checks after repair, or confirms unchanged passing evidence when no repair occurred.
   Write `final-test-output.log` and `result.json` with checks, unresolved defects, changed-file scope and actual outcome.
   An unresolved review defect prevents a success result even when tests pass.

## Completion

The fresh verifier inspects the final diff and ledger, including documentation and configuration changes.
Delegate any remaining documentation or record updates to a fresh worker before final verification.
The main agent reviews worker reports and reports changes, evidence, exclusions and remaining risk.
The main agent never reads the diff or ledger itself and never writes implementation, configuration or documentation.
Do not run an automatic second repair cycle or claim success on unresolved failures. Report the blocking evidence.
The main agent commits at the end of every phase, after its own check (owner rule, 2026-11-06). Workers do not commit.
Push, merge, publish or contact others only when separately authorized by the user's task.
The agent RED review implements the user's explicit test-first instruction. It grants no extra scope or external-action permission.

## Origin

Adapted from the owner's local Claude `implement-step` skill and `workflow.js`, read 2026-11-05.
The Codex adaptation uses native collaboration tools and the owner's requested GPT-6.1 Sol Medium model configuration.
It removes Formfix paths, Opus settings, job-bus assumptions, fixed test ports, mandatory merge commands and unrelated project checks.

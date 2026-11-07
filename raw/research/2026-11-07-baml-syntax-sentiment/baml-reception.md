---
title: "BAML syntax reception: how programmers receive BoundaryML's language, and the BAML/BEAML name proximity"
status: research capture, ingested 2026-11-07
date: 2026-11-07
access_date: 2026-11-07
scope: BAML (BoundaryML) syntax as received by programmers; BAML v0 (legacy DSL) and v1 (general-purpose language); the name proximity to BEAML. Not a technical precedent page; see wiki/sources/baml-v1.md for that.
---

# BAML syntax reception

Claim tags: **[Verified]** a cited source states it; **[Inference]** the researcher's reasoning from several sources; **[Unknown]** not established. Source numbers `[S1]` refer to section 8. "Fetched" means the page content was read on 2026-11-07; "search snippet only" means the claim rests on a search-result excerpt. BAML is BoundaryML's language. BEAML is this repository's language. They are different projects.

## 1. What BAML's syntax looks like

All snippets are verbatim from the cited page, trimmed to at most 8 lines. v0 is the "legacy DSL" per the docs banner [S1]; v1 is the general-purpose language at pin `989676dd` [S9].

v0 function with a Jinja prompt [S2]:

```baml
function ExtractEmail(text: string) -> string {
    client GPT4Turbo
    prompt #"
        Extract the email address from the following text:
        {{ text }}
        {{ ctx.output_format }}
    "#
}
```

v0 class, fields without a colon, attributes as `@` annotations [S3]:

```baml
class MyClass {
  property1 string @alias("name") @description("The name of the object")
  age int? @description("The age of the object")
}
```

v0 enum with value attributes [S4]:

```baml
enum MyEnum {
  Value1 @alias("complete_summary") @description("Answer in 2 sentences")
  Value2
  Value3 @skip
}
```

v0 test block with a Jinja assertion [S5]:

```baml
test TemplateTest {
  functions [Echo]
  args {
   input: EchoTestData()
  }
  @@assert( {{ this == "The number is 43" }} )
}
```

v0 reusable template with Jinja control flow [S6]:

```baml
template_string PrintMessages(messages: Message[]) #"
  {% for m in messages %}
    {{ _.role(m.role) }}
    {{ m.message }}
  {% endfor %}
"#
```

v1 class with colon fields [S9]:

```baml
class LineItem {
    name: string,
    amount: float,
    priority: Priority,
}
```

v1 client as a value, LLM function with a backtick prompt and `${}` holes [S9]:

```baml
client Fast = openai.ResponsesClient.new(model = "gpt-6-luna", api_key = env.OPENAI_API_KEY);
function Extract(raw: string) -> Invoice {
    client: Reliable
    prompt: `Extract the invoice. ${ctx.output_format()}\n${raw}`
}
```

v1 plain function with a body; the last expression is the value [S7]:

```baml
function format_summary(title: string, body: string) -> string {
  title + ": " + body
}
```

v1 typed errors: `throws`, `catch_all`, exhaustive arms [S8]:

```baml
function run_step(tool: string) -> string throws never {
    invoke_tool(tool) catch_all (e) {
        ToolUnavailable => `retry ${e.tool} in ${e.retry_after_ms} ms`,
        BadToolInput => `invalid tool input: ${e.message}`,
    }
}
```

v1 `match` with destructuring, `let` binding and a guard [S9]:

```baml
match (job) {
    Queued => "queued",
    Done { result: "" } => "done, empty",
    let d: Done => `done: ${d.result}`,
    Retrying { attempt: let n } if n >= MAX_ATTEMPTS => "giving up",
    Retrying { attempt: let n } => `retry ${n}`,
}
```

v1 test block as plain code [S9]:

```baml
test "post-process a literal Invoice - no model call" {
    let inv = Invoice { vendor: "Acme", status: "final", note: null,
        items: [LineItem { name: "srv", amount: 900.0, priority: Priority.High }] };
    assert.equal(high_total(inv), 900.0);
}
```

## 2. What people praise

| Feature | Example | Why | Evidence | Tag |
|---|---|---|---|---|
| Prompts as typed functions | `function ExtractEmail(text: string) -> string` | The prompt is findable, versioned and testable; the schema is the type | Gupta [S11], Rao [S20], Gutierrez [S21], Oladele [S24], Atlan [S25], Rost [S23] | [Verified] |
| TypeScript-like schema instead of JSON Schema | `class Resume { name string  skills string[] }` | Fewer tokens, easier to read for humans and models; 370 to 168 tokens in one example | Gutierrez [S21], Atlan [S25], HN laminarflow027 and vicentereig [S19], btbytes [S26] | [Verified] |
| Transparent prompt, no hidden rewriting | `{{ ctx.output_format }}` renders the schema where you see it | "The prompt mystery" is the docs' own complaint about frameworks | Why BAML [S1], Rao [S20], towardsai [S25] | [Verified] |
| Test blocks next to the function, playground in the editor | `test TemplateTest { functions [Echo] ... }` | Edit, run, see the prompt and parse result without restarting an app | Ragan [S22], Oladele [S24], Atlan [S25], Show HN [S14] | [Verified] |
| Jinja for prompt logic | `{% for m in messages %} {{ _.role(m.role) }}` | Popular and mature; agents already write it; static analysis and go-to-definition added | hellovai [S15], BAML docs on Jinja (search snippet) | [Verified] |
| Language-agnostic contracts | one `.baml` file, generated clients for many hosts | Same schema in Python, TypeScript, Go, Ruby; strong shapes across language boundaries | Rao [S20], Rost [S23], Lijin [S12] | [Verified] |
| v1: enums, `match`, exhaustiveness | `match (piece.kind) { ChessKind.Pawn => ... }` | "a new variant is a compile error"; the team's own quality guide steers agents to it | Townsend [S13] | [Verified] |
| v1: agents navigate it cheaply | fully-qualified names, no imports | Team reports about 30% fewer tokens for agents than TypeScript | aaronvg [S18] | [Verified] that the claim exists; [Unknown] independent measurement |

## 3. What people criticize

| Feature | Example | Why | Evidence | Tag |
|---|---|---|---|---|
| A new language at all ("external DSL") | the `.baml` file | "introduces complexity"; the same could be written in Python; frameworks need no new syntax | sbpayne [S17], mg [S15], Rost [S23]; Rao records the pushback [S20] | [Verified] |
| Cognitive load of new syntax | `function`, `class`, `client`, `prompt`, `@description`, `@@assert` | An adjustment period for people new to DSLs; documentation gaps when features combine | Rao [S20], Oladele [S24], Atlan [S25] | [Verified] |
| Build step and generated client | `baml_client` regenerated after each edit | Toolchain complexity; slower prototyping than inline Pydantic | Ragan [S22], Rost [S23] | [Verified] |
| Jinja inside strings | `{{ this == "..." }}`, `{% if content.type == 'text' %}` | Template logic is invisible to the type checker: false ambiguity warnings, `none` rendered for null, no editor comment shortcut, template strings not usable as test arguments | issues #1771, #2008, #2797, #1541, #2159 [S29] | [Verified] |
| Syntax churn between versions | `name string` to `name: string,`; `#"..."#` and `client<llm>` removed; `@@dynamic` removed; watch syntax changed | Frequent updates, breaking changes, two incompatible dialects under one name | SKILL.md [S9], PR #4328 [S28], PR #2630 and #4406 [S30], Oladele [S24], Atlan [S25] | [Verified] |
| Growth from DSL to general-purpose language | v1 stdlib with files, processes, HTTP server, crypto | Fear it gets "progressively worse for humans" when designed for agents | hdjrudni [S18]; wiki v1 page for the stdlib | [Verified] for the fear; [Unknown] how widespread |
| Unresolved arrow debate | `->` for all functions vs `:` and `=>` as in TypeScript | Two proposals, closed without a decision | BEP-008/009 [S27] | [Verified] |
| Acronym not explained | "BAML" | Docs and README did not say what it stands for (2025); third parties invent expansions | evanjrowley [S16], towardsai [S25] | [Verified] |
| Promotion bias | blog posts about parsing | "a little too much like a BAML funnel" | armcat, crystal_revenge [S19] | [Verified] that the view exists |

[Inference] The praise is about what the syntax makes visible (types, prompt, tests). The criticism is about the cost of a separate language (learning, build step, churn) and about logic hidden inside strings (Jinja). Nobody in the fetched sources criticizes a specific BAML keyword or punctuation choice; the complaints are structural. Reddit threads were not found by search [S38]; forum evidence is HN only and thin (the largest BAML-specific thread has 18 points).

## 4. Scorecard against the loved and hated rows

`L n` and `H n` refer to the [loved table](../2026-11-07-pl-syntax-sentiment/loved.md#1-ranked-table-top-celebrated-features) and the [hated table](../2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26) of the PL sentiment capture. "BAML status" is v1 unless marked v0. Alignment: **aligned** (BAML does what the row praises or avoids what it condemns), **tension** (BAML sits on the hated side or against a loved feature), **mixed** (v0 and v1 differ, or praise and criticism both apply). All alignments [Inference]; the status cells cite their source.

| Row | BAML status | Alignment | Note |
|---|---|---|---|
| L1 pattern matching, exhaustive | `match` with destructuring, guards, `let` [S9]; "new variant is a compile error" [S13] | aligned | v0 had none. Same position as BEAML, but BAML matches mid-body and BEAML only at clause heads. |
| L2 sum types | data-free enums; data variants as unions of classes; literal unions [S9, wiki v1] | mixed | No payload enum. BEAML's `Unknown(String)` has no direct BAML form. |
| L3 errors as values, `?`/`try` | `throws E`, `throw`, `catch_all` with arms; propagation inferred when `throws` is omitted [S8] | aligned | Typed and checked, but spelled as exceptions. See H11. |
| L4 null handling | `T?` is `T \| null`; `note: null` in a literal [S3, S9] | aligned | BAML has null and marks it in the type. BEAML has neither (D026). |
| L5 pipelines | no pipe operator; method chains `.flat_map(...)` [S13] | mixed | Chaining yes, `\|>` no. |
| L6 helpful compiler errors | Miette diagnostics with colour (PR #4159); E0098 "removed feature" errors with a pointer to the replacement [S28, S30] | aligned | Intent and tooling exist; quality not measured here. |
| L7 readability as a goal | thesis: agents write it, humans understand it [S11]; HN fear it gets worse for humans [S18] | mixed | The stated goal matches the row; the reception doubts it. |
| L8 expression orientation | body's last expression is the value; `if` is an expression [S7, wiki v1] | aligned | Same as BEAML. |
| L9 immutability by default | `let`, mutable class fields, `while` [wiki v1] | tension | Imperative core. BEAML has no assignment. |
| L10 closures | present [wiki v1] | aligned | BEAML gap (D030). |
| L14 type inference | `let` inferred; `throws` inferred [S8] | aligned | BEAML is on the explicit end. |
| L15 data classes, derived boilerplate | `class` is the schema, the prompt format and the parser [S1, S3] | aligned | The core selling point of v0. BEAML `type` derives decode and structs the same way. |
| L16 string interpolation | v0 Jinja `{{ }}`; v1 backtick `${}` with `if`/`for` tags [S2, S9] | aligned | BEAML rejects interpolation (D028). BAML's prompts are the reason it needs it. |
| L23 opinionated formatter | `baml fmt`, formatter rebuilt on a shared grammar (PR #4576) [S30] | aligned | Same as `beaml fmt`. |
| L24 decorators and annotations | v0 `@alias`, `@description`, `@skip`, `@@dynamic`; v1 removed `@@dynamic` [S3, S4, S28] | mixed | BEAML rejected the attribute spelling (0004 option A). |
| L22 small language, one way | v0 small DSL; v1 general-purpose with 14 stdlib packages [wiki v1] | tension | See H4. |
| H4 complexity creep | DSL became a Turing-complete language in three years [S18]; four syntax removals or changes in 2025 to 2026 [S9, S28, S30] | tension | The growth was user-driven per the team [S18]. BEAML has the same open question (D033). |
| H5 async coloring | `spawn`, `await`, `Future<T, E>` [wiki v1] | tension | BAML has `await`. BEAML has no concurrency form (D031). |
| H6 inconsistency within the language | `name string` (v0) vs `name: string,` (v1) under one name [S3, S9]; `->` vs `=>` debate open [S27] | tension | Inconsistency is across versions, not within one. |
| H8 magic and implicit behaviour | Jinja logic inside string literals; type narrowing by `{% if %}` not seen by the checker [S29] | tension | v1 moves to `${}` holes parsed by the host expression parser (wiki compilers/baml). |
| H10 boilerplate and ceremony | a build step and a generated client per host [S22, S23] | tension | The ceremony is outside the source text. |
| H11 checked exceptions, versionability | `throws` is inferred for bodies; explicit only at interface and native boundaries [S8, wiki canary] | aligned | BAML's answer to the ripple that D027 asks about: infer the list. |
| H23 breaking transitions | v0 labelled "legacy DSL", v1 "a separate language" [S1] | tension | Two dialects, one name. |

Counts over 23 rows: aligned 11, tension 8, mixed 4.

[Inference] Where BAML and BEAML agree (L1, L8, L15, L23, no `any`), the industry evidence is on their side. Where they differ, BAML took the loved side on L4, L10, L14, L16 and H11, and the hated side on L9, H4, H5 and H10. BEAML's open items D026 to D031 are exactly the rows where BAML already chose.

## 5. BAML v0 to v1: what changed in the syntax, and how it was received

Changes, all [Verified] against the cited source:

- Fields: `name string` (v0, [S3]) became `name: string,` (v1, [S9]).
- Prompts: `#"..."#` with Jinja `{{ }}` and `{% %}` (v0, [S2, S6]) became backtick strings with `${}` holes and `if`/`for` template tags; `#"` strings and `client<llm>` blocks "are removed" (v1, [S9]).
- Clients: a `client<llm> X { provider ... }` block (v0, [S1]) became a value, `client Fast = openai.ResponsesClient.new(...)` (v1, [S9]).
- Functions: signature plus prompt (v0) became functions with bodies, `throws`, `match`, closures, `spawn` and `await` (v1, [S7, S8, S9, wiki v1]).
- Tests: `test Name { functions [..] args {..} @@assert({{ }}) }` (v0, [S5]) became `test "name" { let ...; assert.equal(...) }` (v1, [S9]).
- Attributes: `@@dynamic` and `type_builder` were parsed and dropped, then removed with an E0098 diagnostic; `baml.reflect` replaces them (2026-08, [S28]).
- Watch syntax changed to a method-call form in a 39-comment pull request; `//#` header comments were restricted to expression positions in a 28-comment one [S30].
- Function and lambda arrows: BEP-008 (`->` everywhere) against BEP-009 (`:` and `=>` like TypeScript); the pull request closed 2026-08-11 without a decision [S27].

Reception, [Verified] that each voice exists, [Unknown] how representative:

- The v1 announcement thread on HN drew 8 points and 5 comments [S18]. One commenter expects a language built for agents to get "progressively worse for humans". The team answered that users asked for more than a DSL, and that agents spend about 30% fewer tokens navigating BAML than TypeScript.
- Reviewers in 2025 and 2026 name frequent updates and breaking changes as the main risk [S24, S25].
- The team's own 2026-11-05 post says agents wrote v1 code "noticeably worse than" their TypeScript or Rust until a skill taught idioms such as enums over strings and `match` over `if` chains [S13].
- v1 bridge downloads are about 2% of v0 downloads (wiki v1 page, 2026-11-06). Most users are still on v0 syntax.
- No fetched source compares the two syntaxes side by side or asks users which they prefer [Unknown].

## 6. Name proximity: BAML and BEAML

Observed facts:

- **[Verified]** BAML expands to "Basically A Made-up Language" in the README [S10]. A BoundaryML blog post also offers "Basic-Ass Machine Learning" [S11]. The team calls the name "tongue-in-cheek" [S16].
- **[Verified]** Third parties expand it differently: "Boundary AI Markup Language" [S25]. In 2025 a reader found no expansion in the docs or README [S16].
- **[Unknown]** Pronunciation. Neither the README [S10], the fetched docs pages [S1 to S8] nor the fetched blog posts [S11 to S13] state how BAML is spoken.
- **[Verified]** BAML collides with other meanings: Bank of America Merrill Lynch, a brand retired in 2019 (search snippet only, [S35]); Binary Application Markup Language (Wikipedia search result, [S36]); bamlanivimab and the R package bamlss appear in the HN search for "BAML" [S34]. Of the HN stories matched, about 35 are BoundaryML's BAML, 3 are the bank, about 12 other [S34].
- **[Verified]** No project named `beaml` was found: GitHub repository search `beaml in:name` returns 568 substring hits (beamlens, beamline, BeamletOptics.jl) and none named exactly `beaml` or `BEAML` [S32]; PyPI `/pypi/beaml/json`, the npm registry and the hex.pm API return 404 for `beaml` [S33].
- **[Verified]** Web searches for "BAML vs BEAML", "BEAML vs BAML" and "BEAML language" return no page about this repository's language or about a comparison [S37]. A search engine answers "BEAML" with BEAM (the Erlang VM) and BML results.
- **[Unknown]** Trademark status of "BAML" and "BEAML". No trademark register was searched.
- **[Verified]** Edit distance: BEAML is BAML with one inserted letter. BEAML also contains "BEAM", the name of the Erlang VM that BEAML targets.
- **[Verified]** Shared design space (from this repository's [BAML v1 source page](../../../wiki/sources/baml-v1.md#beaml-relevance)): typed LLM functions, exhaustive `match`, typed errors, telemetry recorded by default. Both are typed languages for agent software with a Rust toolchain.

[Inference] Search-engine collision risk runs in one direction today: a search for BEAML returns BEAM and BAML results, not the reverse, because BAML has about 9,500 GitHub stars and this repository has none public. A reader who hears "BEAML" next to "BAML" has one letter and a shared feature list to tell them apart. Whether that is a cost (confusion, "a BAML fork") or a benefit (positioning "BAML, but on the BEAM") is a design and positioning question, not a fact in the evidence.

## 7. Quotes

At most one verbatim quote per source, each under 15 words (14 or fewer), with URL. A line without quotation marks is a paraphrase, not a quote.

- "I have a distaste for external DSLs" — sbpayne, HN, https://news.ycombinator.com/item?id=47490365.
- "I expect it to get progressively worse for humans" — hdjrudni, HN, https://news.ycombinator.com/item?id=48927917.
- Paraphrase: the team reports about 30% fewer tokens for agents navigating BAML than TypeScript — aaronvg, HN, same thread as above.
- "none of those documentation sources told me what BAML stands for." — evanjrowley, HN, https://news.ycombinator.com/item?id=45822986.
- Paraphrase: the name is tongue-in-cheek, a joke about the ridiculous idea of building a DSL — aaronvg, HN, same thread as above.
- "we added a lot of static analysis" — hellovai, on Jinja, HN, https://news.ycombinator.com/item?id=40713952.
- Paraphrase: the same schema could be expressed in Python — mg, HN, same thread as above.
- "a little too much like a BAML funnel" — armcat, HN, https://news.ycombinator.com/item?id=46345333.
- "it might impose more of a cognitive load" — Prashanth Rao, https://thedataquarry.com/blog/baml-is-building-blocks-for-ai-engineers/.
- "adopting a compilation step into your build process" — Rob Ragan, https://starlog.is/articles/ai-dev-tools/boundaryml-baml/.
- "Zero setup friction—pip install and you're ready." — Rost on Instructor vs BAML, https://dev.to/rosgluk/baml-vs-instructor-structured-llm-outputs-2p2b.
- "You may face an initial adjustment period" — Oladele and Neurl Creators, https://neurlcreators.substack.com/p/1-tool-review-baml-next-level-prompt.
- "BAML doesn't have Jetbrains extension like VS Code" — Lorre Atlan, https://towardsai.com/p/machine-learning/the-prompting-language-every-ai-engineer-should-know-a-baml-deep-dive.
- Paraphrase: prompts as strings scattered through a codebase are unmaintainable (upstream spells it "unmaintable") — Vaibhav Gupta, https://boundaryml.com/blog/ai-agents-need-new-syntax.
- "String accepts typos. Use an enum or a literal union." — Avery Townsend, https://boundaryml.com/blog/teaching-agents-to-write-beautiful-baml.
- "Remove the name and body — that's your type" — BEP-008, https://github.com/BoundaryML/baml/pull/3231.
- "BAML massively improves the prompt engineering experience" — Sebastian Gutierrez, https://sebgnotes.substack.com/p/baml-bringing-software-engineering.
- Paraphrase: the expressiveness of English with the structure of code — BoundaryML, quoted on https://www.btbytes.com/BAML.

## 8. Sources

Access date for all: 2026-11-07. "Fetched" = page content read; "search snippet only" = seen only in a search result. Authors are cited as published; HN authors are user names.

- **S1** BoundaryML, "Why BAML?", BAML v0 docs (banner: "documents BAML v0, the legacy DSL"). https://docs.boundaryml.com/guide/introduction/why-baml . Fetched. Supports: argument chain from f-strings to BAML; `class Resume`, `client<llm>` snippets.
- **S2** BoundaryML, "function", BAML v0 reference. https://docs.boundaryml.com/ref/baml/function . Fetched. Supports: `ExtractEmail` snippet, `#"..."#`, `{{ ctx.output_format }}`.
- **S3** BoundaryML, "class", BAML v0 reference. https://docs.boundaryml.com/ref/baml/class . Fetched. Supports: `name Type` fields without colon, `@alias`, `@description`, `@@dynamic`.
- **S4** BoundaryML, "enum", BAML v0 reference. https://docs.boundaryml.com/ref/baml/enum . Fetched. Supports: `@alias`, `@description`, `@skip` on values.
- **S5** BoundaryML, "test", BAML v0 reference. https://docs.boundaryml.com/ref/baml/test . Fetched. Supports: `test` block with `functions`, `args`, `@@assert`.
- **S6** BoundaryML, "template_string", BAML v0 reference. https://docs.boundaryml.com/ref/baml/template-string . Fetched. Supports: Jinja `{% %}` and `{{ }}` in a reusable template.
- **S7** BoundaryML, BAML v1 language reference, "Functions". https://developer.boundaryml.com/baml/language/functions . Fetched. Supports: `function f(x: int) -> int { x }` form, colon parameters.
- **S8** BoundaryML, BAML v1 book, "Errors". https://developer.boundaryml.com/baml/book/errors . Fetched. Supports: `throw`, `throws never`, `catch_all` arms, inferred `throws`.
- **S9** BoundaryML, `skills/baml-core/SKILL.md` at commit `989676dd5169497c0d2a8d8e1d10914e987ae262`. https://github.com/BoundaryML/baml/blob/989676dd5169497c0d2a8d8e1d10914e987ae262/skills/baml-core/SKILL.md . Fetched (raw). Supports: v1 class, client value, LLM function, `match`, test snippets; `client<llm>` blocks and `#"` strings removed.
- **S10** BoundaryML, repository README, branch `canary`. https://github.com/BoundaryML/baml . Fetched (raw README). Supports: "Basically A Made-up Language"; tagline "the programming language for agents"; no pronunciation; no BAML code in the README.
- **S11** Vaibhav Gupta, "AI Agents Need a New Syntax", BoundaryML blog, 2025-01-24. https://boundaryml.com/blog/ai-agents-need-new-syntax . Fetched. Supports: JSX analogy, prompts as typed functions, "Basic-Ass Machine Learning", `ChatAgent` snippet.
- **S12** Sam Lijin, "Building a new programming language", BoundaryML blog, 2024-06-21. https://boundaryml.com/blog/building-a-new-programming-language . Fetched. Supports: Rust toolchain, Pest grammar, Jinja; syntax rationale deferred to a later post; no pushback discussed.
- **S13** Avery Townsend, "Teaching Agents to Write Maintainable Code", BoundaryML blog, 2026-11-05 (URL slug says "beautiful-baml"). https://boundaryml.com/blog/teaching-agents-to-write-beautiful-baml . Fetched. Supports: agents underused enums and `match`; code quality metrics in the toolchain; `match (piece.kind)` snippet.
- **S14** Hacker News, "Show HN: BAML - A new programming language to get structured data from LLMs", 2024-03-26, 18 points, 2 comments. https://news.ycombinator.com/item?id=39827354 . Fetched via the Algolia API. Supports: launch framing (type-safe, self-contained); one positive reply.
- **S15** Hacker News, "Every Way to Get Structured Output from LLMs", 2024-06-18, 169 points. https://news.ycombinator.com/item?id=40713952 . Fetched via the Algolia API. Supports: "Could be expressed in Python" objection; the team's three DSL reasons (see the whole prompt, codegen, static analysis on Jinja); DSL-vs-Python side thread.
- **S16** Hacker News, "Why BAML?", 2025-11-05, 4 points, 2 comments. https://news.ycombinator.com/item?id=45822986 . Fetched via the Algolia API. Supports: acronym not explained; "tongue-in-cheek".
- **S17** Hacker News, "If DSPy is so great, why isn't anyone using it?", 2026-03-23, 227 points. https://news.ycombinator.com/item?id=47490365 . Fetched via the Algolia API. Supports: distaste for external DSLs, "meh" on BAML; three users report BAML works well or is in production.
- **S18** Hacker News, "Baml: The Programming Language for Agents", 2026-07-15, 8 points, 5 comments. https://news.ycombinator.com/item?id=48927917 . Fetched via the Algolia API. Supports: "worse for humans" fear; three-year DSL to Turing-complete history; 30% token claim.
- **S19** Hacker News, Algolia comment search for "BAML", 100 hits read, stories 46345333 (2025-12-21), 46261884 (2025-12-19), 46635309 (2026-01-17) and others. https://hn.algolia.com/api/v1/search?query=BAML&tags=comment . Fetched. Supports: "BAML funnel", schema format token savings (85% vs JSON Schema, one commenter), "huge fan", production use.
- **S20** Prashanth Rao, "BAML is like building blocks for AI engineers", The Data Quarry, 2025-02-10. https://thedataquarry.com/blog/baml-is-building-blocks-for-ai-engineers/ . Fetched. Supports: cognitive-load pushback and the language-agnostic counter; no other criticism.
- **S21** Sebastian Gutierrez, "BAML: Bringing Software Engineering Rigor to LLM Development", Substack, 2025-01-31. https://sebgnotes.substack.com/p/baml-bringing-software-engineering . Fetched. Supports: type-safe DSL praise, token compression; no criticism.
- **S22** Rob Ragan, "BAML: The Type-Safe DSL That Treats LLM Prompts as Compiled Functions", starlog.is, 2026-05-08. https://starlog.is/articles/ai-dev-tools/boundaryml-baml/ . Fetched. Supports: fast feedback loop praise; compilation step and toolchain complexity; SAP latency; ecosystem skew to Python and TypeScript.
- **S23** Rost, "BAML vs Instructor: structured LLM outputs", dev.to, 2025-12-28. https://dev.to/rosgluk/baml-vs-instructor-structured-llm-outputs-2p2b . Fetched. Supports: separation of concerns and cross-language types for BAML; no build step and Pythonic for Instructor; "learning a new DSL".
- **S24** Stephen Fiyinfoluwa Oladele and Neurl Creators, "Tool review: BAML", Substack, 2025-02-25. https://neurlcreators.substack.com/p/1-tool-review-baml-next-level-prompt . Fetched. Supports: adjustment period for DSL newcomers; breaking changes risk; editor tooling praise.
- **S25** Lorre Atlan, "The Prompting Language Every AI Engineer Should Know: A BAML Deep Dive", Towards AI, 2025-11-24. https://towardsai.com/p/machine-learning/the-prompting-language-every-ai-engineer-should-know-a-baml-deep-dive . Fetched. Supports: expansion "Boundary AI Markup Language"; TypeScript-like schemas praise; no JetBrains preview, docs gaps, breaking changes.
- **S26** btbytes.com, "BAML" (personal notes page, author and date not shown). https://www.btbytes.com/BAML . Fetched. Supports: quotes BoundaryML's "expressiveness of English, structure of code" and the readability-for-LLMs claim.
- **S27** BoundaryML/baml pull request #3231, "BEP-008/009: Function and Lambda Syntax Design", opened 2026-03-10, closed 2026-08-11. https://github.com/BoundaryML/baml/pull/3231 . Fetched. Supports: `->` everywhere vs `:` and `=>`; arguments; no decision at close.
- **S28** BoundaryML/baml pull request #4328, "feat(lang): remove legacy type_builder/dynamic/@@dynamic syntax", antoniosarosi, 2026-08-06. https://github.com/BoundaryML/baml/pull/4328 . Fetched. Supports: inert legacy syntax removed; E0098 diagnostics; `baml.reflect` replacement.
- **S29** BoundaryML/baml issues found by the GitHub search API for "jinja": #1403, #1541, #1771, #1863, #2008, #2107, #2159, #2797 (2025-02 to 2025-12). https://api.github.com/search/issues?q=repo:BoundaryML/baml+jinja+is:issue . Fetched (API bodies, paraphrased). Supports: template strings not usable as test arguments; Jinja narrowing not seen by the checker; `none` rendered for null; no comment shortcut.
- **S30** BoundaryML/baml pull requests found by the GitHub search API for "syntax" in the title: #2630 (watch syntax, 39 comments), #4406 (`//#` comments, 28 comments), #4159 (Miette diagnostics), #4576 (grammar unification), #3346 (`-> void`), #2675 (drop language hints). https://api.github.com/search/issues?q=repo:BoundaryML/baml+syntax+in:title . Fetched (API listing only; diffs not read). Supports: syntax churn and diagnostics work in 2025 to 2026.
- **S31** manavisrani07, "BAML: The Structured-Output Power Tool...", Medium (HTTP 403 on fetch). https://medium.com/@manavisrani07/baml-the-structured-output-power-tool-your-llm-workflow-has-been-missing-f326046d019b . Search snippet only. Not used for any claim.
- **S32** GitHub repository search, `beaml in:name`. https://api.github.com/search/repositories?q=beaml+in:name . Fetched. Supports: 568 substring hits, none named exactly `beaml`.
- **S33** Package registries: https://pypi.org/pypi/beaml/json (404), https://registry.npmjs.org/beaml (404), https://hex.pm/api/packages/beaml (404). Fetched. Supports: no `beaml` package on PyPI, npm or Hex. The PyPI HTML page was bot-blocked; the JSON API answered.
- **S34** Hacker News, Algolia story search for "BAML", 50 hits read of 20,372 reported. https://hn.algolia.com/api/v1/search?query=BAML&tags=story . Fetched. Supports: about 35 BoundaryML, 3 Bank of America Merrill Lynch, about 12 other (bamlanivimab, bamlss).
- **S35** East & Partners, "BAML rebrands to 'Bank of America'" (2019); Euromoney, "BoA crab cake: catching an acronym crab". https://eastandpartners.com/news/baml-rebrands-to-bank-of-america/ . Search snippet only. Supports: BAML as the bank's brand 2009 to 2019.
- **S36** Wikipedia, "Binary Application Markup Language". https://en.wikipedia.org/wiki/Binary_Application_Markup_Language . Search result only. Supports: a second technical meaning of BAML.
- **S37** Web searches "BAML vs BEAML", "BEAML vs BAML", "BEAML language", 2026-11-07. No result about this repository's language or a comparison. Supports: [Unknown] public awareness of BEAML; search engines map "BEAML" to BEAM and BML.
- **S38** Web search for Reddit threads on BAML syntax, 2026-11-07. No Reddit thread appeared in the results; none fetched. Supports: the Reddit gap.

Not fetched, not cited: nicolaygerold.substack.com BAML issue (404); developer.boundaryml.com/baml landing and language index (fetched, no code on the page); BoundaryML blog index (fetched, lists only 2026 posts).

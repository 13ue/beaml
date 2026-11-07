---
title: "What drives programmers up the wall: hated syntax and language-level features"
status: temporary research, not ingested into wiki
date: 2026-11-07
access date for all sources: 2026-11-07
scope: syntax and language-level features across the landscape; libraries and ecosystems only where they leak into the language experience
---

# What drives programmers up the wall

Temporary research page. Not ingested into `wiki/`. Claims are tagged **[Verified]** (a cited source states it), **[Inference]** (aggregated or reasoned by the researcher), **[Unknown]** (not established). Sources are numbered `[S1]` to `[S43]`; see the list at the end. Where a source was only seen in a search snippet, the list says so.

## Method and limits

- 43 sources: 4 survey series (Stack Overflow 2023/2024/2025/2026, Go Developer Survey 2022/2024, State of Rust 2024 plus the 2026 Rust challenges report, State of JS 2024), classic essays and talks, official language documents, and practitioner threads (Hacker News, Slashdot, dev.to, perl.org, haskell.org lists). **[Verified]**
- The ranking in the table is the researcher's aggregation of breadth of sources, survey weight and recurrence. It is not a measured frequency. **[Inference]**
- Gaps: reddit threads (r/ProgrammingLanguages "worst design decisions", "dumbest feature", r/learnprogramming) and Lobste.rs were bot-blocked and could not be read; their content is only reflected through search snippets, marked as anecdotes. The Stack Overflow 2024 and 2025 "admired" pages were truncated on fetch; their numbers come from search snippets (Rust 83 % in 2024, Rust 72 % in 2025). The Stack Overflow "dreaded" wording was dropped after 2022; 2023 onward uses "admired" (users who want to keep using it), so "least admired" is the modern proxy for "most dreaded". **[Verified]** for the wording change, **[Inference]** for using it as a proxy.
- A note on one trap: a Dice article often cited for "most dreaded" (VB6 89.9 %, COBOL 84.1 %) is 2018 survey data, not 2024, despite how search engines present it [S43]. **[Verified]**

## Ranked table: the top 26

| # | Feature or trait | Canonical examples | Why people hate it | Evidence strength | Tag |
|---|---|---|---|---|---|
| 1 | Null / nil references everywhere | Java `NullPointerException`; Go `var p *T; p.x` panics; C `NULL`; JS `typeof null === 'object'` | Every reference is secretly optional, so the absence case is unchecked until runtime. Hoare called it his "billion-dollar mistake". Go users in 2024 still ask for a way to walk nested pointers without panics. | Strong: Hoare talk [S12], Go survey 2024 [S2], Zwinkau [S22], wtfjs [S26] | [Verified] |
| 2 | Implicit type coercion and loose equality | JS `[] + {}` is `"[object Object]"`, `[] == ![]` is `true`, `'3' - 1` is `2` but `'3' + 1` is `'31'`; PHP `"foo" == 0` and `"foo" == TRUE` but `TRUE != 0` | The language silently converts operands, so comparisons are non-transitive and bugs hide in plain sight. The "wat" talk made this the canonical language joke. | Strong: wat [S13], wtfjs (37.7 k stars) [S26], Eevee [S11], Slashdot [S40] | [Verified] |
| 3 | Repetitive error-handling boilerplate | Go `if err != nil { return nil, err }` after every call | Error handling verbosity was the top closed-form complaint in the Go survey 2024 H1 (13 %) and became the top challenge in 2022 once generics shipped; three Go-team proposals (`check`/`handle`, `try`, `?`) failed and the team stopped in June 2025. The HN thread drew 579 comments. | Strong: Go blog 2025 [S1], Go surveys [S2][S3], HN [S32], dev.to [S41] | [Verified] |
| 4 | Complexity creep / "too many features" | C++ with "about 150 cooks" and 43 major proposals in one mailing; Rust: 28 % of 2024 respondents fear it becomes "too complex"; Scala implicits | Each feature is reasonable alone; together they overwhelm teaching, tooling and ordinary programmers. Stroustrup warned WG21 the language "could crumble under the weight". | Strong: Vasa paper [S21], State of Rust 2024 [S4], Scala 3 docs [S25] | [Verified] |
| 5 | Async "function coloring" and async machinery | JS/C#/Python `async`/`await` split the codebase; Rust `Pin`, `BoxFuture`, `Arc<Mutex<_>>` across `.await` | Calling an async function from a sync one is impossible without infecting the caller; in Rust the interaction with lifetimes and traits makes API design "a minefield". Async complexity is a named productivity limiter in both Rust reports. | Strong: Nystrom [S18], boats [S17], hirrolot [S16], Rust surveys [S4][S5] | [Verified] |
| 6 | Ownership and the borrow checker learning curve | Rust `cannot borrow *x as mutable because it is also borrowed as immutable` | Beginners "basically all struggle" with it; 25 % of 2018 survey respondents who did not use Rust said it was too hard or intimidating (snippet). A 2023 usability paper calls the rules "repeatedly cited as a barrier to adopting Rust". | Strong: Rust challenges 2026 [S5], arXiv [S33], hirrolot [S16], 2018 survey (snippet) [S34] | [Verified] |
| 7 | Slow compilation blamed on the language | Rust (monomorphisation, LLVM); Scala "Hello World" at 4.4 s vs Java 0.1 s; C++ templates and headers | Slow compilation was the top productivity limiter in State of Rust 2024 and "recognised" again in 2026. Programmers blame the type system and generics design, not only the compiler. | Strong for Rust and Scala [S4][S5][S41]; C++ by analogy | [Verified] for Rust/Scala, [Inference] for C++ |
| 8 | Inconsistent naming and argument order | PHP `strpos` vs `str_rot13`, `array_filter(arr, fn)` vs `array_map(fn, arr)`, twelve sort functions; Delphi `AnsiContainsStr(haystack, needle)` vs `AnsiPos(needle, haystack)`; Python `'-'.join(list)` | Nothing can be remembered, everything must be looked up; the inconsistency is in the core, not in third-party code. | Medium: Eevee [S11], dev.to [S41] | [Verified] |
| 9 | Sentinel return values and wrong defaults | PHP `strpos` returns `0` at position zero and `false` when absent; PHP `json_decode` returns `null` for both invalid JSON and `null`; JS `[10, 9, 1].sort()` gives `[1, 10, 9]` | The common case works, the edge case silently returns something truthy or falsy that the caller misreads. | Medium: Eevee [S11], wtfjs [S26] | [Verified] |
| 10 | Boilerplate and ceremony (noun kingdom) | Java `new ServiceFactory().createService().execute()`, getters and setters, no free functions | Every verb must be wrapped in a class; simple actions become Factory and Manager objects. Still the most common Java complaint in practitioner threads. | Medium: Yegge [S23], dev.to [S41], snippets | [Verified] for the essay, [Inference] for "most common" |
| 11 | Checked exceptions and invisible exception control flow | Java `throws IOException, SQLException, ...`; C++/Java `throw` as hidden `goto` | Hejlsberg: adding an exception breaks every client (versionability) and large systems explode in declared exceptions (scalability). Spolsky: exceptions "are invisible in the source code". | Medium: Hejlsberg [S24], Spolsky [S19] | [Verified] |
| 12 | Undefined behaviour and "implementation specific" | C signed overflow lets the compiler turn `x + 1 > x` into `true`; null deref and out-of-bounds reads are UB | Programmers think C is a high-level assembler; the optimiser is allowed to delete their checks. Zwinkau lists unclear semantics as design mistake no. 2. | Medium: Lattner [S42], Zwinkau [S22] | [Verified] |
| 13 | C/C++ declaration syntax and prefix operators | `char *p` vs `*p = q`; `int (*f)(int)`; C++03 `vector<vector<int> >` needing a space | "Declaration mirrors use" blurs declaring and using; `>>` parsed as shift. Pascal's postfix `^` is cited as the fix nobody copied. | Medium: HN thread on the 1996 paper [S31], Zwinkau [S22], Slashdot [S40] | [Verified] |
| 14 | Significant whitespace | Python blocks by indentation | The 1996 "Seven Deadly Sins" paper called it "detrimental cleverness"; forum posts dislike invisible structure, copy-paste breakage and tabs vs spaces. The design FAQ defends it as "extremely elegant". | Medium: HN [S31], Python FAQ (defender) [S30], snippets (anecdote) | [Verified] for the critique and defence, [Inference] for how widespread |
| 15 | Lisp parentheses and prefix notation | `(defun f (x) (if (> x 0) (* x 2) (- x)))))` | No textual landmarks; closing-paren pile-ups; prefix arithmetic removes familiar precedence. "Oh! so many parentheses!" is the most common reason people stop. | Medium: CLiki [S37], Magne 2025 [S36], Wheeler (snippet) [S38] | [Verified] |
| 16 | Perl sigils, special variables and context | `$x`, `@x`, `%x`, `$x[0]` is an element of `@x`; `$_`, `$$`, `@_`; scalar vs list context | Looks like "line noise"; the sigil changes with context (dropped in Perl 6 / Raku); TIMTOWTDI makes other people's code hard to read. | Medium: Gardner [S35], Schwartz [S39], Slashdot [S40] | [Verified] |
| 17 | Bash word splitting, globbing and quoting | `for f in $(ls)`; `[ $x == foo ]` vs `[[ ... ]]`; unquoted `$var` | 65 documented pitfalls; the default behaviour of an unquoted variable is to split and glob, so the correct form is the verbose form. | Strong single source: Greg's Wiki [S20] | [Verified] |
| 18 | YAML implicit typing | `country: NO` becomes `false`; `version: 9.3` becomes a float; `time: 1:30` becomes `90` in YAML 1.1 | The "Norway problem": a config language guesses types from spelling. StrictYAML's answer is "everything is a string". | Medium single source: StrictYAML [S14]; Van Asseldonk essay blocked | [Verified] for Norway and versions, [Unknown] for the 1:30 case in this capture |
| 19 | Haskell `String = [Char]` and the records problem | `type String = [Char]` as a boxed linked list; `data P = P { name :: String }` clashes with any other `name` field | Three string types and conversions everywhere; record field selectors share one namespace, so the usual `a.b` needed a 2020 proposal (`OverloadedRecordDot`). | Medium: Allbery [S38], GHC proposal 0282 [S27] | [Verified] |
| 20 | Scala implicits (conversions, resolution, errors) | `implicit def intToStr(i: Int): String`; implicit parameters hidden in imports | "Most distinguished and most controversial feature": overused, one keyword for several concepts, inscrutable type errors, resolution depends on imports. Scala 3 replaced them with `given`/`using`. | Strong single authoritative source: Scala 3 docs [S25] | [Verified] |
| 21 | Missing sum types, enums and Option in Go | `const ( A = iota; B )` as pseudo-enum; `interface{}` plus type switch | Respondents: emulating closed enums "is a lot of faff"; "lack of enum support" is "easily the most annoying thing" in snippets. Go's simplicity is accused of relocating complexity to the user. | Medium: Go survey 2024 [S2], fasterthanlime [S28], snippets | [Verified] for the survey, [Inference] for ranking |
| 22 | No static typing in JavaScript | `function f(a, b) { return a + b }` | Static typing was the top "missing feature" in State of JS 2024 (5,403 mentions); 8,362 want it "as similar to TypeScript as possible". Typing is also a top-8 pain point. | Strong: State of JS 2024 [S6] | [Verified] |
| 23 | Breaking transitions in the language itself | Python 2 to 3 `str` vs `bytes`; `print` statement to function | Shaw: beginners cannot be taught Python 3 because of the strings/bytes split, and the migration took over a decade. Zwinkau lists bad Unicode support as design mistake no. 3. | Medium: Shaw [S29], Zwinkau [S22] | [Verified] |
| 24 | Assignment as an expression | C `if (a = b)`; Python's answer was 30 years of no assignment in expressions, then PEP 572 `:=` | Classic typo footgun. The walrus debate was so bitter that Guido resigned as BDFL the day after accepting it. | Medium: HN [S31], Slashdot [S40], Guido mail [S15] | [Verified] |
| 25 | Silent adjacent string concatenation | Python `["foo", "bar" "baz"]` yields two elements; same in C | A missing comma produces a shorter list with no error. | Weak: dev.to [S41] and snippets | [Verified] for the example, [Inference] for how widespread |
| 26 | Textual preprocessor and macros | C `#define MAX(a,b) ((a)>(b)?(a):(b))` | "A quick hack instead of a clean solution": macros do not know scope, types or syntax. | Weak: Zwinkau [S22] | [Verified] |

Honourable mentions seen in one thread each (all anecdotal, [Verified] that the source says it, [Unknown] how widespread): Lua 1-based indexing, PowerShell `-eq`, PHP's left-associative nested ternary, Java `Map.get(Object)` defeating generics, Elm's mandatory `in`, IDL dropping trailing dimensions of size 1 [S40][S41].

## Themes

### 1. Implicit coercion and footguns

JavaScript `==`, PHP `==`, YAML's bare `NO`, Bash's unquoted `$var` and C's undefined behaviour share one shape: the language does something helpful by default, and the helpful thing is wrong in an edge case nobody sees until production [S11][S13][S14][S20][S42]. The joke format ("wat", wtfjs, "the YAML document from hell") is itself evidence that these are the most memeable complaints **[Inference]**. Defenders say the rules are fully specified and learnable, that wtfjs exists to teach the spec, and that convenience in scripting is the point; StrictYAML and TypeScript show the pragmatic answer is a stricter dialect rather than a fix in place [S14][S6][S26].

### 2. Null and absence

Null is the one complaint with a designer's own confession attached [S12]. Modern languages answer with `Option`/`Maybe`, non-nullable references or sum types; Go users in 2024 are still asking for exactly that [S2]. The defence is practical: null is cheap, universal and easy to implement, which is precisely Hoare's reason for regretting it [S12]. Kotlin, Swift and Rust are rarely attacked on this point, which suggests the hate is about absence being unchecked, not about having a none value **[Inference]**.

### 3. Error handling noise versus invisible errors

Programmers hate both ends: Go's visible, repeated `if err != nil` [S1][S2][S3] and Java's invisible or over-declared exceptions [S19][S24]. Rust's `?` is the compromise most often held up; Go tried `check`/`handle`, `try` and `?` and could not reach consensus [S1]. Defenders of Go say the verbosity "fades into the background", that explicit errors are easier to debug in production, and that forced new syntax would split the community; several HN commenters report having "grown to love" it after years [S1][S32].

### 4. Boilerplate and ceremony

Java's noun kingdom [S23], getters and setters, Haskell's record-field prefixes [S27], Go's error lines [S3] and Elm's `let ... in` [S41] are all ceremony: text the programmer types that carries no decision. The complaint grows with codebase size and shrinks with IDE support; the Go team explicitly bets on editors hiding redundancy instead of changing syntax [S1]. Defenders say ceremony is explicitness, and that readers outnumber writers.

### 5. Complexity creep and too many ways

C++ [S21], Rust [S4][S5], Scala [S25] and Perl's TIMTOWTDI [S35][S40] draw the same objection: each addition is defensible, the sum is not. Stroustrup's Vasa paper is the committee-insider version; 28 % of Rust users name "too complex" as their top fear for the language [S4], and new features are a high priority for only about 29 % of them (snippet) [S4]. Defenders point out that Rust's complexity buys 82 % of companies reaching their goals [S4], and Stroustrup himself reads the Vasa story as "work on the foundation", not "stop adding".

### 6. Inconsistency within the language

PHP is the archetype: naming, argument order, return conventions and error reporting differ function by function [S11]; Delphi and Python have smaller versions [S41]; Go's standard library mixes interfaces and structs without a rule (snippet) [S31]. Inconsistency is hated more than any single bad rule because it defeats memory **[Inference]**. Defenders of PHP mostly concede the history and point to PHP 7/8 cleanup; the 2023 Stack Overflow data still puts PHP among the least admired languages [S7].

### 7. Whitespace and punctuation wars

Python indentation [S30][S31], Lisp parentheses [S36][S37], Perl sigils [S35][S39] and C-family braces and semicolons are the loudest and least consequential complaints: they are about reading, not about bugs **[Inference]**. Defenders in each camp make the same move, calling it unfamiliarity: Schwartz on Perl, the Python design FAQ, and Lisp advocates pointing to Paredit and rainbow parentheses [S30][S36][S39]. The counter-evidence is that Dylan dropped s-expressions to reach "normal" users (snippet) [S38].

### 8. Magic and implicit behaviour

Scala implicits [S25], exceptions as hidden control flow [S19], async coloring [S18], Perl's `$_` [S35] and optimisers acting on undefined behaviour [S42] all put behaviour outside the text being read. The common hatred is for not being able to answer "what does this line do" locally **[Inference]**. Defenders say implicit context is what makes type classes, DSLs and zero-cost abstractions possible, and Scala 3 kept the power while renaming and constraining it [S25].

## Hated then forgiven

- Rust borrow checker: beginners all struggle; experts "don't really complain about the borrow checker anymore" (2026 report, snippet) and the official challenges report says it improves with experience [S5][S34]. **[Verified]**
- gofmt: "Gofmt's style is no one's favorite, yet gofmt is everyone's favorite" [S30-bis]. **[Verified]**
- Go generics: lack of generics was the top Go complaint for years; after shipping, 43 % of free-text answers said "thank you" and only 6 % were negative [S3]. **[Verified]**
- Go error handling, for some: HN commenters who "hated it when first introduced" and now defend it [S32]; the Go team cites conference feedback that contradicts GitHub sentiment [S1]. **[Verified]** that these voices exist, **[Unknown]** what share they are.
- Python indentation: attacked in 1996 as "detrimental cleverness" [S31]; Python is now the most used (58 % in 2025, snippet [S9]) and most desired language (33.4 % in 2026 [S8]). Forgiveness **[Inference]** from adoption, not from a direct survey question.
- Static typing in JavaScript: hated as missing, then adopted via TypeScript (53 % admired in 2026 [S8], top wanted feature in State of JS [S6]). **[Inference]** that this is forgiveness rather than escape.
- Walrus operator `:=`: the fight cost Python its BDFL [S15]; the operator shipped in 3.8 and no source in this capture reports continued opposition. **[Unknown]** whether it is forgiven or merely tolerated.
- Lisp parentheses: still named as the top entry barrier [S37], yet Lisp sits at 55.4 % admired among its users in 2026 [S8]. **[Inference]**: hated by outsiders, accepted by insiders.
- Perl sigils: defended by insiders for forty years [S35][S39]; no survey evidence that outsiders came round. **[Unknown]**.

## Quotes

One quote per source, under 15 words each.

- "Simply because it was so easy to implement." Tony Hoare on null, InfoQ 2009. https://www.infoq.com/presentations/Null-References-The-Billion-Dollar-Mistake-Tony-Hoare/
- "the Go team will stop pursuing syntactic language changes for error handling" Robert Griesemer, Go blog 2025. https://go.dev/blog/error-syntax
- "Sum types/closed enums can be emulated but its a lot of faff." Go survey respondent, 2024. https://go.dev/blog/survey2024-h1-results
- "Virtually every feature in PHP is broken somehow." Eevee, 2012. https://eev.ee/blog/2012/04/09/php-a-fractal-of-bad-design/
- "Implicits are at the same time Scala's most distinguished and most controversial feature." Scala 3 reference. https://docs.scala-lang.org/scala3/reference/contextual/
- "We are on the path to something that could destroy C++." Bjarne Stroustrup, P0977, 2018. https://www.stroustrup.com/P0977-remember-the-vasa.pdf
- "Gofmt's style is no one's favorite, yet gofmt is everyone's favorite." Rob Pike, Go Proverbs, 2015. https://go-proverbs.github.io/
- "Using indentation for grouping is extremely elegant and contributes to clarity." Python design FAQ. https://docs.python.org/3/faq/design.html
- "I'm giving myself a permanent vacation from being BDFL" Guido van Rossum, 2018. https://mail.python.org/pipermail/python-committers/2018-July/005664.html
- "Designing interfaces in Rust is like walking through a minefield" hirrolot, 2022. https://hirrolot.github.io/posts/rust-is-hard-or-the-misery-of-mainstream-programming.html
- "Borrow checking remains a difficult part of the Rust language" Jack Huey, Rust blog 2026. https://blog.rust-lang.org/2026/03/20/rust-challenges
- "These rules come with a steep learning curve" Ferdowsi, arXiv 2023. https://arxiv.org/abs/2301.02308
- "Go has eliminated the distinction between synchronous and asynchronous code." Bob Nystrom, 2015. https://journal.stuffwithstuff.com/2015/02/01/what-color-is-your-function/
- "Classes are really the only modeling tool Java provides you." Steve Yegge, 2006. https://steve-yegge.blogspot.com/2006/03/execution-in-kingdom-of-nouns.html
- "The trouble begins when you start building big systems" Anders Hejlsberg, 2003. https://www.artima.com/articles/the-trouble-with-checked-exceptions
- "They are invisible in the source code." Joel Spolsky on exceptions, 2003. https://www.joelonsoftware.com/2003/10/13/13/
- "C is not a 'high level assembler'" Chris Lattner, 2011. https://blog.llvm.org/2011/05/what-every-c-programmer-should-know.html
- "Preprocessors like cpp and m4 are a quick hack" Andreas Zwinkau, 2010. https://beza1e1.tuxen.de/articles/proglang_mistakes.html
- "String as a boxed singly-linked list type is therefore a major problem." Brandon Allbery, 2012. https://mail.haskell.org/pipermail/haskell-prime/2012-March/003603.html
- "In almost every programming language we write a.b" GHC proposal 0282. https://github.com/ghc-proposals/ghc-proposals/blob/master/proposals/0282-record-dot-syntax.rst
- "it only tells me they haven't studied it" Randal Schwartz on "I can't read Perl", 2010. https://blogs.perl.org/users/randal_l_schwartz/2010/11/perls-readability.html
- "The sigil always tells you what you're going to get" Mark Gardner, 2021. https://dev.to/mjgardner/the-four-noisy-horsemen-of-perl-hate-o6p
- "It takes a lot of practice to be able to really read lisp" CLiki, Fear of Lisp. https://cliki.net/Fear%20of%20Lisp
- "Parentheses dominate visual space" Magne, 2025. https://dev.to/this-is-learning/could-parentheses-be-a-reason-lisp-is-hard-to-read-481l
- "Go constantly takes power away from its users" Amos Wenger, 2020. https://fasterthanli.me/articles/i-want-off-mr-golangs-wild-ride
- "I cannot teach Python 3 to total beginners" Zed Shaw, 2016. https://learnpythonthehardway.org/book/nopython3.html
- "Everything is fine I dream if err, if err dreams me." Anonymous HN commenter, 2025. https://news.ycombinator.com/item?id=44171677

## Sources

Access date for all: 2026-11-07. "Fetched" means the page content was read; "snippet" means only a search-result excerpt was seen.

1. [S1] https://go.dev/blog/error-syntax — Robert Griesemer, Go blog, 2025-06-03. Fetched. Supports: Go stops error-handling syntax work; three failed proposals; reasons; conference feedback vs GitHub.
2. [S2] https://go.dev/blog/survey2024-h1-results — Go team, 2024 (n = 6,224). Fetched. Supports: error-handling verbosity 13 %, learning Go 15 %, sum types and nil-walking requests.
3. [S3] https://go.dev/blog/survey2022-q2-results — Go team, 2022-09-08 (n = 5,752). Fetched. Supports: generics reception (43 % "thank you", 6 % negative), error handling becomes top challenge after generics.
4. [S4] https://blog.rust-lang.org/2025/02/13/2024-State-Of-Rust-Survey-results/ — Rust Survey Team, 2025-02-13 (n = 7,310). Fetched. Supports: "too complex" 28 % top worry, slow compilation top productivity limiter, async complexity, 82 % goals met. The 43 to 45 % figures for earlier cycles come from devclass snippets only.
5. [S5] https://blog.rust-lang.org/2026/03/20/rust-challenges — Jack Huey, Vision Doc group, 2026-03-20 (about 70 interviews). Fetched. Supports: compile times, borrow checking (beginners), async as universal challenges.
6. [S6] https://2024.stateofjs.com/en-US/usage/ — Devographics, 2024 (n = 10,599 for pain points). Fetched. Supports: static typing top missing feature (5,403), pain-point ranking.
7. [S7] https://survey.stackoverflow.co/2023/ — Stack Overflow, May 2023 (n = 87,585). Fetched. Supports: Rust over 80 % admired; MATLAB under 20 %; VB.Net, COBOL, Objective-C, PHP, VBA least admired.
8. [S8] https://survey.stackoverflow.co/2026/technology/data — Stack Overflow, 2026 (n = 14,099). Fetched. Supports: admired 2026: Rust 67.4 %, Lisp 55.4 %, TypeScript 53.0 %; least admired VBA 20.1 %, Objective-C 21.3 %, Groovy 21.9 %, MATLAB 24.4 %, VB.Net 25.5 %; Python most desired 33.4 %.
9. [S9] https://survey.stackoverflow.co/2025/technology/ — Stack Overflow, 2025 (n > 49,000). Snippet only (fetch truncated). Supports: Rust 72 %, Gleam 70 %, Elixir 66 %, Zig 64 % admired; Python used by 58 %.
10. [S10] https://survey.stackoverflow.co/2024/technology/ — Stack Overflow, 2024 (n = 65,437). Snippet only (fetch truncated). Supports: Rust 83 % admired.
11. [S11] https://eev.ee/blog/2012/04/09/php-a-fractal-of-bad-design/ — Eevee, 2012-04-09. Fetched. Supports: PHP inconsistency, `==`, `strpos`, `json_decode`, naming.
12. [S12] https://www.infoq.com/presentations/Null-References-The-Billion-Dollar-Mistake-Tony-Hoare/ — Tony Hoare, QCon London, 2009-08-25. Fetched. Supports: null introduced 1965, billion-dollar estimate.
13. [S13] https://www.destroyallsoftware.com/talks/wat — Gary Bernhardt, CodeMash 2012. Fetched (page describes the talk; examples are from the talk title and common knowledge of it). Supports: JS coercion as canonical joke.
14. [S14] https://hitchdev.com/strictyaml/why/implicit-typing-removed/ — Colm O'Connor, StrictYAML docs. Fetched. Supports: Norway problem, version numbers as floats, "Null" as none.
15. [S15] https://mail.python.org/pipermail/python-committers/2018-July/005664.html — Guido van Rossum, 2018-07-12. Fetched. Supports: resignation after PEP 572.
16. [S16] https://hirrolot.github.io/posts/rust-is-hard-or-the-misery-of-mainstream-programming.html — hirrolot, 2022-06-02. Fetched. Supports: async traits, lifetimes, closures, Pin pain.
17. [S17] https://without.boats/blog/why-async-rust/ — Saoirse (boats), 2023-10-15. Fetched. Supports: Pin as "unforced error", coloring, Arc/Mutex overhead, design constraints.
18. [S18] https://journal.stuffwithstuff.com/2015/02/01/what-color-is-your-function/ — Bob Nystrom, 2015-02-01. Fetched. Supports: function coloring critique; Go, Lua, Ruby avoid it.
19. [S19] https://www.joelonsoftware.com/2003/10/13/13/ — Joel Spolsky, 2003-10-13. Fetched. Supports: exceptions as invisible control flow.
20. [S20] https://mywiki.wooledge.org/BashPitfalls — Greg's Wiki, community maintained. Fetched. Supports: 65 pitfalls; word splitting, quoting, `[` vs `[[`.
21. [S21] https://www.stroustrup.com/P0977-remember-the-vasa.pdf — Bjarne Stroustrup, P0977r0, 2018-03-06. Fetched (PDF read directly). Supports: feature creep, "150 cooks", "could crumble under the weight".
22. [S22] https://beza1e1.tuxen.de/articles/proglang_mistakes.html — Andreas Zwinkau, 2010-08-15. Fetched. Supports: null, parser-unfriendly syntax, unclear semantics, Unicode, preprocessor.
23. [S23] https://steve-yegge.blogspot.com/2006/03/execution-in-kingdom-of-nouns.html — Steve Yegge, 2006-03-30. Fetched. Supports: Java noun-centric verbosity.
24. [S24] https://www.artima.com/articles/the-trouble-with-checked-exceptions — Anders Hejlsberg interview, Artima, 2003-08-18. Fetched. Supports: versionability and scalability problems.
25. [S25] https://docs.scala-lang.org/scala3/reference/contextual/ — Scala 3 reference (EPFL). Fetched. Supports: five problems with Scala 2 implicits.
26. [S26] https://github.com/denysdovhan/wtfjs — Denys Dovhan, ongoing, 37.7 k stars. Fetched. Supports: `[] == ![]`, `typeof null`, `'3' - 1`, `[10,9,1].sort()`, `null >= 0`.
27. [S27] https://github.com/ghc-proposals/ghc-proposals/blob/master/proposals/0282-record-dot-syntax.rst — Neil Mitchell, Shayne Fletcher, accepted 2020-05-03. Fetched. Supports: record field clashes, no namespacing, nested update.
28. [S28] https://fasterthanli.me/articles/i-want-off-mr-golangs-wild-ride — Amos Wenger, 2020-02-28 (updated 2022). Fetched. Supports: Go simplicity hides complexity, ignored errors, missing features.
29. [S29] https://learnpythonthehardway.org/book/nopython3.html — Zed Shaw, 2016-11-22. Fetched. Supports: str/bytes complaint, migration cost.
30. [S30] https://docs.python.org/3/faq/design.html — Python Software Foundation. Fetched. Supports: defence of indentation. [S30-bis] https://go-proverbs.github.io/ — Rob Pike, Gopherfest 2015. Fetched. Supports: gofmt proverb, "Errors are values".
31. [S31] https://news.ycombinator.com/item?id=28859449 — HN thread on "Seven Deadly Sins of Introductory Programming Language Design (1996)", 2021-10-14. Fetched. Supports: C declaration syntax, prefix pointers, assignment as expression, significant whitespace, syntactic synonyms, Go stdlib inconsistency.
32. [S32] https://news.ycombinator.com/item?id=44171677 — HN thread on the Go error-syntax post, 2025-06-03, 416 points, 579 comments. Fetched via the HN Algolia API (top-level comments). Supports: practitioner split, "grown to love", "13 % means 87 % did not".
33. [S33] https://arxiv.org/abs/2301.02308 — Kasra Ferdowsi, "The Usability of Advanced Type Systems: Rust as a Case Study", 2023-01-05. Fetched (abstract). Supports: ownership and lifetimes as adoption barrier.
34. [S34] https://www.infoworld.com/article/3324488/rust-language-is-too-hard-to-learn-and-use-says-user-survey.html — InfoWorld on the 2018 Rust survey. Snippet only. Supports: 25 % cite "too hard, intimidating"; experts stop complaining about the borrow checker (the latter sentence appeared in the search summary without a clear origin and is treated as anecdote).
35. [S35] https://dev.to/mjgardner/the-four-noisy-horsemen-of-perl-hate-o6p — Mark Gardner, 2021-07-20. Fetched. Supports: regex, sigils, dereferencing, special variables, with defences.
36. [S36] https://dev.to/this-is-learning/could-parentheses-be-a-reason-lisp-is-hard-to-read-481l — Magne, 2025-03-20. Fetched. Supports: parentheses critique and defenders' view.
37. [S37] https://cliki.net/Fear%20of%20Lisp — CLiki, community. Fetched. Supports: parentheses, CAR/CDR naming, "decode rather than read".
38. [S38] https://mail.haskell.org/pipermail/haskell-prime/2012-March/003603.html — Brandon Allbery, 2012-03-23. Fetched. Supports: String as linked list. Also in this slot: https://dwheeler.com/readable/readable-s-expressions — David Wheeler, snippet only, supports Dylan dropping s-expressions.
39. [S39] https://blogs.perl.org/users/randal_l_schwartz/2010/11/perls-readability.html — Randal L. Schwartz, 2010-11-29. Fetched. Supports: "line noise" defence as unfamiliarity. The "checksummed line noise" line from Learning Perl appeared in a snippet only.
40. [S40] https://developers.slashdot.org/story/14/09/05/160245/ask-slashdot-what-are-the-strangest-features-of-various-programming-languages — Slashdot, 2014-09-05, 729 comments. Fetched. Supports: `if (a = b)`, JS `+`, C++03 `>>`, PHP ternary, Lua indexing, Perl TIMTOWTDI, PowerShell `-eq`.
41. [S41] https://dev.to/mortoray/what-simple-things-annoy-you-about-your-favourite-programming-languages — edA-qa mort-ora-y and commenters, 2017-06-28. Fetched. Supports: Python join and string concatenation, Delphi argument order, Go `if err`, Java generics and getters, Scala compile time, Elm `in`.
42. [S42] https://blog.llvm.org/2011/05/what-every-c-programmer-should-know.html — Chris Lattner, 2011-05-13. Fetched. Supports: undefined behaviour examples and surprise.
43. [S43] https://www.dice.com/career-advice/tech-pros-dread-this-programming-language-the-most — Dice, 2018-03-15. Fetched. Supports only the caution that its "dreaded" numbers (VB6 89.9 %, COBOL 84.1 %) are 2018 data.

Not readable in this capture (bot-blocked or 403): reddit r/ProgrammingLanguages "worst design decisions" (2022) and "dumbest feature" (2021), r/computerscience "popular language you dislike" (2024), r/perl "write-only" (2023), Lobste.rs search, Ruud van Asseldonk "The YAML document from hell" (2023), TechRepublic SO summary. Their content appears only as search snippets and is marked anecdote where used.

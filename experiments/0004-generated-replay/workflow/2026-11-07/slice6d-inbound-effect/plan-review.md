# PLAN CHECK: slice 6d, inbound EFFECT (DL-128)

Fresh-context check, 2026-11-07, git HEAD c1af85a5. Normal check, not Devil's Advocate. One round.
Read: plan.md, plan.json, decisions.md; DL-101, DL-102, DL-126, DL-127, DL-128; D020; main.rs at HEAD (fallback text line 748, decode emit lines 3103 to 3171, encoder line 3387); README of `integrations/zed-beaml`.
By: Opus (PLAN CHECK, slice6d-inbound-effect) on every judgement in this file.

## Verdict

**BLOCK (two high objections).** The structure is sound. Repair two rules, then RED can start.
By: Opus (PLAN CHECK, slice6d-inbound-effect)

## Objections

### O1 · high · The param decode rule is not named; outside data passes with a wrong value or always fails

- **[Observed]** Probe with `erl` (OTP `json`): `json:encode(#{<<"a">> => nil})` gives `{"a":"nil"}`; an atom value `web` gives `"web"`; nested atom keys give String keys.
- **[Inference]** D6B-132 runs the decode on `:json.encode(params)`. A JS hook `pushEvent("place", {order_id: null})` reaches the host as `nil`. The round trip makes it the String `"nil"`. The decode accepts it, the ENTRY RECORD stores it, the flow runs. Wrong outcome, no reject.
- **[Inference]** LiveView form and `phx-value-*` params are Strings. An `Int` field gets `"500"`, the decode wants a JSON number, so every form submit with an `Int` field rejects with `decode`. The fixtures use no `Int` field, so N1 to N12 pass and hide it.
- **Plan repair must:** state the rule in D6B-132 and test it in N4. Smallest rule: a strict term check before the encode (maps with String keys, lists, binaries, integers, floats, `true`, `false` only; `nil`, other atoms, tuples and structs give `decode`, at every level), and no String-to-Int coercion in 6d (a `"500"` for an `Int` field gives `decode`). Add N4 cases: nested `nil`, nested atom value, `"qty" => "500"` on an `Int` field. Record the form-String limit for EXPERIMENT 0005 as an open question (coercion per `ui` transport, or an Int field in an entry input TYPE is a compile error).
- **Not a problem:** `_csrf_token` and `_target` are top-level String keys outside the declared keys. They go to `unknown_keys` (names only, no value). N8 covers `_csrf_token`. Uploads (`%Plug.Upload{}`) are structs and reject under the rule above.

By: Opus (PLAN CHECK, slice6d-inbound-effect)

### O2 · high · D6B-139 opens a DL-102 hole and is classed too low

- **[Verified]** D6B-130 allows constructor TYPES and enums in the fields of the input TYPE (the fixture `Amount` has a constructor, `Channel` has literals).
- **[Inference]** A later change to the `Amount` constructor or a lost `Channel` literal makes stored ENTRY RECORDS fail `Replay.entry` (a `Rejected`) or replay as `Unknown`. `--stored` reads no ENTRY RECORD, so the build does not block. DL-102 and DL-122 say: a stored record that fails a new rule, or loses its literal, blocks the build. The replay itself follows DL-102 (today's code on yesterday's params), so D6B-135 and D6B-137 are right; only the build check is missing.
- **[Inference]** Whether DL-102 covers a new record stream is a rule of the OWNER, not an Undo default. D6B-139 decides it silently.
- **Plan repair must:** raise D6B-139 to Migrate and put it to the OWNER as Q6D-4 (options below). Until the answer, keep the slice as planned but label D6B-139 an interim gap in the exclusions, with the N9 constructor case as its evidence.

By: Opus (PLAN CHECK, slice6d-inbound-effect)

### O3 · medium · One entry and one EFFECT per source do not carry the PROTOTYPE page

- **[Inference]** D6B-129 allows one ENTRY LINE; slice 1 allows one outbound EFFECT; the target must be that EFFECT's flow. A second page action (list orders, a `db` EFFECT under DL-127) cannot be declared in the same source. The plan records "a page with several events waits" but does not name it as a blocker of EXPERIMENT 0005.
- **[Inference]** D6B-136 is consistent: a pure flow from the same params gives the same result, so no record is needed. DL-128 scope ("REPLAY RUN of an inbound event") holds for the EFFECT source.
- **Note, no block:** name "several ENTRY LINES and several EFFECTS per source" as the first 0005 precondition in the exclusions.

By: Opus (PLAN CHECK, slice6d-inbound-effect)

## Other checks (no objection)

- **Check 1, entry as EFFECT.** D6B-128 keeps the inbound EFFECT of DL-128: declared, DL-101 decode, root span, typed failure. DL-126 lists "EFFECT signatures" and "entry points" as separate declarations, so a separate `Entry` node breaks no rule. A user sees: `effect` declares output, failure TYPE and path; `on` declares input TYPE and target, output and failure come from the fn; a reject is `Rejected`, not `<Failure>{reason: "decode"}`. Q6D-1 and Q6D-3 carry that difference to the OWNER. The glossary entry for ENTRY LINE should say "the declaration of an inbound EFFECT", so the DL-128 term stays linked.
- **Check 2, replay.** `Replay.entry` decodes the stored `value` with today's code, then runs the flow: the DL-102 replay rule. Only the build check is missing (O2).
- **Check 6, false pass.** **[Verified]** The fallback text at HEAD is unchanged (main.rs line 748, cli.rs line 208, slice5 line 42). N13 builds the compiler of the commit before the GREEN (`git archive`), so a shared emit change that moves bytes of an EFFECT module fails N13. Keep the `--stored` inputs of every source equal in both builds. N14 needs `--rebuild` (README line 52: without it a stale cached parser can pass); the plan has it.

By: Opus (PLAN CHECK, slice6d-inbound-effect)

## Q6D options as put to the OWNER

- **Q6D-1, form.** A `on ui "place" PlaceOrder -> place` (default, smallest, the DL-128 sketch). B `effect ui.place ... = ui.event("place") |> place`. C `entry ui.place PlaceOrder -> place`. Missing option D: `effect in ui "place" PlaceOrder -> place`, the `effect` keyword with a direction word, if "one keyword for both directions" matters.
- **Q6D-2, host call.** A `Orders.ui_place(params)` (default, smallest, errors at host build if the probe holds). B `Orders.entry("place", params)`. Real choice.
- **Q6D-3, reject form.** A `%Rejected{reason: ...}` (default, smallest, works without `!`). B the failure TYPE of the fn. C a plain tuple. Real choice.
- **Q6D-4 (new, from O2), stored ENTRY RECORDS.** A `--stored` also reads `entries.jsonl` and runs the field constructors and literals of the input TYPE (DL-102 covers entries). B no build check in 6d; the gap stays recorded until D020. Smallest safe default: B for the slice, with the gap named.

By: Opus (PLAN CHECK, slice6d-inbound-effect)

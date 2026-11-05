# HEEx analysis: syntax, semantic facts and safe source edits

Status: **[Verified]** pinned Phoenix mechanisms; **[Proposal]** BEAML adapter design and worked examples. No parser or refactor was executed. [Sources/pins/limits](../../sources/phoenix-heex-mechanisms.md).

## Choose a passive parsing path deliberately

**[Verified]** LiveView's official TagEngine composes parsing with code generation; internal parser node forms distinguish text, expressions, tag blocks/self-closing nodes and attributes with metadata. Parser/compiler modules are `@moduledoc false`. The parser also supports macro components and can call `module.transform`; its skip path exists but is not a long-term compatibility promise. Embedded-expression compilation invokes Elixir parsing and some name paths create atoms. [Parser definitions/execution branch](https://github.com/phoenixframework/phoenix_live_view/blob/d8252e1e21238e150e9e6b3d7285d4c060d28e6e/lib/phoenix_live_view/tag_engine/parser.ex#L1-L80); [Macro processing](https://github.com/phoenixframework/phoenix_live_view/blob/d8252e1e21238e150e9e6b3d7285d4c060d28e6e/lib/phoenix_live_view/tag_engine/parser.ex#L601-L700); [Expression/attribute compilation](https://github.com/phoenixframework/phoenix_live_view/blob/d8252e1e21238e150e9e6b3d7285d4c060d28e6e/lib/phoenix_live_view/tag_engine/compiler.ex).

**[Proposal]** Maintain a thin version-pinned frontend adapter: preserve input, invoke the supported official syntax path in a bounded helper, disable/decline macro execution for editor analysis, parse embedded expressions without evaluation, and convert only understood forms into frontend facts. Cap input/nesting/atom creation and discard the helper if its resource budget is exceeded. Syntax errors produce recoverable partial facts or explicit unavailable analysis; they cannot certify safety. A separate frontend is necessary; regex over rendered text cannot bind lexical variables/slots or preserve macro/source semantics.

## Worked structural facts

**[Proposal]** Given a declared `InvoiceCard` contract and this authored template:

```heex
<.invoice_card invoice={@invoice} compact={true}>
  <:actions :let={id}>
    <button phx-click="delete" phx-value-id={id}>Delete</button>
  </:actions>
</.invoice_card>
```

Extract a *schematic* fact graph, not an asserted exact Phoenix AST dump:

```text
component call -> resolved InvoiceCard symbol
  prop invoice -> assign-read invoice -> declared Invoice type
  prop compact -> literal Bool
  slot actions -> lexical binder id -> declared slot argument InvoiceId
  event literal delete -> InvoiceEditor event descriptor
  phx-value-id -> outbound DOM representation -> incoming untrusted string
```

The slot binder is scoped to its slot body, not a module variable or unrelated field also named `id`. A type-aware `Contract.field(@form,:amount)` yields a semantic field reference only if the call/module and form contract are recognized. Dynamic `apply`, computed event names and arbitrary map spreads retain unknown facts. Rendering a nominal ID does not prove the later browser payload is that ID; see [event decoding](typed-forms-and-events.md).

## Components, slots and assigns

**[Verified]** Phoenix records declarative attr/slot metadata and verification information; `__verify__` distinguishes known attrs from dynamic/root spreads, warns on missing/invalid static declarations and inspects slot metadata. The compiler constructs slot bodies and `:let` pattern clauses. [Declarative verifier](https://github.com/phoenixframework/phoenix_live_view/blob/d8252e1e21238e150e9e6b3d7285d4c060d28e6e/lib/phoenix_component/declarative.ex#L1150-L1265); [Slot compilation](https://github.com/phoenixframework/phoenix_live_view/blob/d8252e1e21238e150e9e6b3d7285d4c060d28e6e/lib/phoenix_live_view/tag_engine/compiler.ex#L813-L915).

**[Proposal]** Use a BEAML descriptor to add nominal/schema/refinement expectations beyond host literal checks. Keep required presence separate from nullability/defaults. Specify slot cardinality and yielded argument type; a `:let` pattern may bind only a projection or fail to match. A conditional slot is not always present. If `{attrs}` might supply a missing prop, report uncertain presence rather than definitely absent or proved present. Import metadata only with artifact/version identity; stale `__components__` data must not silently satisfy a new contract.

**[Verified]** Engine analysis recognizes forms such as `@name`, `assigns.name`, and certain literal access paths for change tracking; broad/dynamic assigns can disable precise tracking. Its internal “taint” terminology concerns change detection, not confidentiality. Component assign helpers preserve `__changed__` machinery. [Assign-path analysis](https://github.com/phoenixframework/phoenix_live_view/blob/d8252e1e21238e150e9e6b3d7285d4c060d28e6e/lib/phoenix_live_view/engine.ex#L1037-L1145); [Assign helpers](https://github.com/phoenixframework/phoenix_live_view/blob/d8252e1e21238e150e9e6b3d7285d4c060d28e6e/lib/phoenix_component.ex#L1418-L1479).

**[Proposal]** BEAML flow analysis should track recognized assign updates through control flow and meet branch facts conservatively. A required assign written on only one branch remains possibly missing. Unknown helper calls/macros can invalidate the local guarantee. Keep IFC labels and authorization facts as distinct dimensions; an assign being unchanged does not make its contents public. Generated `Contract.assign` must delegate appropriately to Phoenix tracking, not simply overwrite the socket map.

## Source coordinates need a real mapping layer

**[Verified]** The tokenizer increments columns while decoding UTF-8 codepoints and handles newline/indentation offsets. `sigil_H` forwards caller file/line-plus-one and sigil indentation into the engine. Elixir parsing/quoting has its own location retention behavior. [Tokenizer](https://github.com/phoenixframework/phoenix_live_view/blob/d8252e1e21238e150e9e6b3d7285d4c060d28e6e/lib/phoenix_live_view/tag_engine/tokenizer.ex); [Sigil macro](https://github.com/phoenixframework/phoenix_live_view/blob/d8252e1e21238e150e9e6b3d7285d4c060d28e6e/lib/phoenix_component.ex#L923-L939); [Compiler/LSP source-map context](../compiler-and-tooling.md).

**[Proposal]** Maintain authored byte ranges as canonical frontend locations plus a per-document index converting codepoints/bytes to negotiated LSP positions. `😀` occupies four UTF-8 bytes, one Unicode scalar and two UTF-16 units; a combining sequence can occupy multiple scalars but one displayed grapheme. A fixed column subtraction fails across these units. `.heex` is a direct file; `~H` additionally needs mapping through host source extraction, sigil delimiters, heredoc indentation, CRLF and escapes. If a synthetic wrapper is used for a parser, wrapper bytes/lines must map to no authored location and embedded slices must map back explicitly. Never apply generated diagnostic columns directly to user text.

## Rename is a transaction on semantic references

**[Proposal]** For `amount -> total`, bind declaration/field references in BEAML, recognized `Contract.field` literals and descriptor-backed HEEx references to the same semantic ID. Do not replace a prose string, a different component's `amount`, a browser's unrelated param name, or a dynamic expression because the text matches. Refuse a rename when a required dynamic reference cannot be resolved safely; report affected uncertainty.

Collect edits against each document's known version, check scope collisions and span/token expectations, ensure edits do not overlap, then submit one versioned workspace edit. Recompute after a stale buffer or contract fingerprint. A partial rename that leaves the generated ABI/event wire name inconsistent is not completion. Test Unicode/heredoc/slot shadowing/import alias/nested field/dynamic spread/contract edit cases and actual client rejection of stale edits. These are proposed acceptance cases, not a claim of tested safe rename.

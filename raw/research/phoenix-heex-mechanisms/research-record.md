# Phoenix/HEEx mechanism capture

Retrieved 2026-11-05. Publishers: Phoenix/Elixir contributors. Exact versions, paths and selected coverage: [provenance](provenance.json). LiveView v1.2.13 resolves to `d8252e1e21238e150e9e6b3d7285d4c060d28e6e`; Phoenix.HTML v4.3.0 to `8cfd3e37ff9ef0924812a78cf6c9d27cdbd4e726`. This capture contains researcher paraphrases, not upstream implementation copies. Status: source inspected, no running parser/form/LiveView experiment. Licenses/notices remain upstream; check before code reuse.

## Parser and coordinates

TagEngine composes an official parser and compiler. The parser exposes tag/tree/expression nodes with source metadata but is undocumented internally. It can run macro-component transforms; `skip_macro_components` controls a branch that bypasses these. The ordinary compile path should not be assumed to be passive syntax reading. The compiler parses embedded Elixir and creates atoms for some names. A safe editor adapter must explicitly choose non-executing, atom-bounded behavior and reject/mark unsupported syntax.

The tokenizer consumes UTF-8 codepoints while incrementing columns, handles CRLF/newline, and keeps an indentation-derived column offset. The `sigil_H` macro passes caller file/line plus one and sigil indentation into TagEngine. These are source-level behaviors, not evidence that a simple byte/UTF-16 offset subtraction is correct for every sigil/escape/wrapper. Tests must compare exact authored bytes, Elixir codepoint locations and negotiated LSP positions.

## Components and assigns

The declarative module registers attr/slot metadata and builds `__components__` plus verification callbacks. Its verification distinguishes root/dynamic attrs from statically absent required attrs; it does not assume arbitrary spread maps are known. The compiler handles slot names, slot bodies, `:let` pattern clauses and special attrs. Engine source recognizes paths such as `@name`, `assigns.name` and some access patterns for change tracking, and conservatively taints broad/dynamic usage. This internal taint is not security-label analysis. Assign helpers maintain framework tracking state; blindly replacing assigns maps can break rendering behavior.

## Forms and events

Client `extractMeta` gets `phx-value-*` attribute values using DOM getAttribute; ordinary values are strings, with optional explicit JS value metadata mixed separately. Form serialization uses FormData then URLSearchParams, excludes File entries from that form value path, and carries unused-field markers for presentation. Server event decoding has a separate query/form step; transport normalization must be tested before asserting preservation of duplicate keys or explicit null.

Phoenix.HTML's Map FormData implementation treats maps as parameter maps, warns on atom keys, preserves params and exposes data/errors/action/options through forms. Field lookup distinguishes a present parameter from fallback data. It is a presentation adapter, not a schema/type/authorization validator. LiveView's used-input markers hide premature error display; they cannot exempt a submitted field from authoritative validation.

## Proposed BEAML mechanisms

Compile a restricted template subset into stable semantic references and uncertainty, not runtime execution. Preserve mapping through `.heex` and `~H` extraction; reject unsafe dynamic rename. Define descriptor version/type/policy/error identity independently of private Phoenix metadata. Normalize untrusted maps with a documented missing/empty/null/optional policy, then validate before command execution. Work through encoded client/server fixtures because a map decoder cannot recover distinctions already collapsed by transport. None of these proposals was implemented or empirically verified in this capture.

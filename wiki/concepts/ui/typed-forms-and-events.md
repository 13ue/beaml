# Typed forms and events: the browser-to-command seam

Status: **[Verified]** framework transport/presentation mechanisms; **[Proposal]** BEAML normalization, descriptor and test design. [Primary source inventory](../../sources/phoenix-heex-mechanisms.md). No UI adapter is implemented.

## Transport representation is not a domain value

**[Verified]** In the inspected client, `extractMeta` reads `phx-value-*` through DOM attributes, normally yielding strings; explicit JavaScript value metadata can add other values. Form serialization uses FormData/URLSearchParams, handles submitter order and unused-input markers, and separates File objects from this form-value path. The server channel has its own event/form decoding. [Browser implementation](https://github.com/phoenixframework/phoenix_live_view/blob/d8252e1e21238e150e9e6b3d7285d4c060d28e6e/assets/js/phoenix_live_view/view.ts#L1861-L2000); [Server channel](https://github.com/phoenixframework/phoenix_live_view/blob/d8252e1e21238e150e9e6b3d7285d4c060d28e6e/lib/phoenix_live_view/channel.ex).

**[Inference]** A DOM `phx-value-id` rendered from an `InvoiceId` comes back as untrusted data. An attacker can forge event names, maps, arrays or nulls regardless of ordinary controls. A UI declaration, hidden field or disabled submit button cannot replace server authorization/decoding.

**[Verified]** Phoenix.HTML's Map `FormData` implementation treats input maps as parameter maps, warns on atom keys and exposes params/data/errors/action/options. Present params override fallback data in field lookup. LiveView's `_unused_*` markers support error-display decisions. Neither presentation feature establishes aggregate validity. [Map form adapter](https://github.com/phoenixframework/phoenix_html/blob/8cfd3e37ff9ef0924812a78cf6c9d27cdbd4e726/lib/phoenix_html/form_data.ex#L80-L194); [Used-input behavior](https://github.com/phoenixframework/phoenix_live_view/blob/d8252e1e21238e150e9e6b3d7285d4c060d28e6e/lib/phoenix_component.ex#L1693-L1765).

## Normalize without erasing distinctions

**[Requirement]** The spec separates raw, parsed and validated inputs and requires explicit missing/empty/null/optional semantics. [Spec pp.8–11 §§21–32](../../sources/engineering-spec-v0.5.md). **[Proposal]** Use the following decision matrix as a starting artifact, not an adopted universal coercion policy:

| Raw case | Preserve/parse fact | Required semantic decision / negative case |
|---|---|---|
| Key absent | Missing | Required input fails; optional omission/default must be specified. Never silently invent a validated value. |
| `""` | Present empty string | Valid for unconstrained string if allowed; invalid ID/number unless an explicit optional-empty rule applies. |
| `"null"` | Literal text | Never silently reinterpret as JSON null. |
| `nil`/JSON null | Explicit null, when transport allows it | Accept only a declared nullable case; distinct from absent and empty. |
| `"0"` | Parsed integer zero | Check range/refinement afterward; truthiness cannot reject a legitimate zero. |
| `" 12 "` | String with whitespace | Trimming is a field policy; define before numeric parse and preserve a safe error representation. |
| `"12.30"` | Exact decimal text | Decide scale/rounding/currency; do not parse through floating point accidentally. |
| Nested map/list | Shape already normalized by transport | Validate path/index/cardinality and reject incorrect scalar/container shape. |
| Repeated form keys/checkbox hidden input | Transport-specific multiplicity/order | Define/test actual encoded-client/server behavior; a map cannot recover duplicate distinctions already collapsed. |
| `_unused_*`, `_target`, submitter metadata | Presentation/transport information | Parse separately from domain fields; never let it bypass final required validation. |
| Unknown field/event | Unrecognized key/discriminant | Define explicit reject/ignore/version policy; never atomize arbitrary input names. |

**[Proposal]** Maintain a parsed draft with field-level outcomes during `change`, then run full authoritative validation on submit. Show only relevant touched errors if desired, but “not displayed” is not “passed.” Keep errors as typed codes/paths with safe public messages; raw secret/PII values must not leak through formatting, flash or logs.

## Versioned descriptors bridge the languages

**[Requirement]** The proposed ABI exposes typed descriptors, `decode_event/2`, `form/0`, `change/2`, `assign/2`, field references and explicit success/error returns; the example's extra helper export remains an open gap. [Spec source and ABI gap](../../planning/specification-gaps.md#ui-and-tooling-questions).

**[Proposal]** A descriptor should identify the contract, format/compiler ABI version, source/schema fingerprint, declared events, each field's shape/presence/nullability/refinement, component props/slots, public error schema and policy linkage. Omit payload values/secrets. Generated module metadata and a compiler-readable serialized artifact can serve different consumers; neither should depend on an undocumented Phoenix structure being stable forever. Define schema evolution/fingerprint invalidation, mixed-version requests and stale editor overlays before declaring a stable ABI.

```text
event "save" -> decode raw string-keyed payload with schema V
             -> Parsed<CreateInvoice.Input>
             -> validate fields + cross-field rules
             -> Validated<Input,V>
             -> authorize principal/purpose for this command
             -> execute domain transition
             -> contract-aware assign/error rendering
```

This is **[Proposal]** pseudocode. Authorization may need earlier checks as well; the important invariant is that no prohibited domain effect occurs before all required checks. Schema validation does not prove the principal may act, and successful rendering does not prove authorization for an external model request.

## Worked invalid-to-no-effects example

**[Proposal]** A save handler receives `%{"invoice" => %{"amount" => "-2", "id" => "forged"}}`. It must not call `execute` because a superficially map-shaped payload exists. Decode known keys without creating atoms; parse decimal/ID; reject nominal/refinement failures; create draft errors; preserve the user's permitted form values; assign/render the errors through Phoenix helpers. Domain effect count remains zero. Re-rendering error state must not accidentally trigger a duplicate model call, erase change tracking or disclose the rejected raw ID.

Contrast a valid value with an expired schema/principal: it may be structurally valid but still requires rejection/revalidation under the chosen policy. A fake externally constructed `Validated`-shaped struct is not evidence of trusted construction. Guard public APIs or use an explicitly scoped handle protocol as decided in [typed-language boundaries](../beam/typed-language-boundaries.md).

## Concrete end-to-end fixture seam

**[Proposal]** Test actual encoded DOM/form events, server normalization, generated decoder, domain-effect spy and rendered HEEx together. Include missing/empty/null, zero/decimal limits, nested fields/list variants, forged IDs, unknown events, stale descriptors, slot/assign errors, repeated-key/checkbox cases and errors followed by valid resubmit. Use no live provider initially. Assert exact diagnostic/error paths, safe output, zero effects for every rejected case and one expected effect for a valid command; test double submit/reconnect/cancel separately with operation identity. Add browser-side hints only after server behavior is established. No fixture or effect assertion has been executed yet.

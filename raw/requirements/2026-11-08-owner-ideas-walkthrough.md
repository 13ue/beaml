# OWNER ideas, 2026-11-08 (walk-through D037 and roadmap)

**Capture.** Spoken by the OWNER in the session of 2026-11-08, dictated, paraphrased into statements by Fable. Not a transcript. Each statement keeps the OWNER's intent; wording is the paraphraser's. Coverage: the ideas the OWNER raised beside the walk-through answers (answers themselves are in the decision log, DL-149 to DL-156). This capture is immutable; a later capture gets a new date.

## Meta rule: OWNER ideas carry the highest truth

- [Requirement] What the OWNER says about the far future, the roadmap and the shape of the language is the highest source of truth for this repository. It is captured every time, at the right places, prepared for the public repository (not in dictation text).
- [Requirement] The OWNER may contradict earlier statements. That is acceptable; the contradiction is recorded as a tension and untangled when the work reaches that point, not smoothed over at capture time.
- [Requirement] This is "creative capture of ideas": record, do not judge; label proposals as proposals.

## Redacted values in records (D039)

- [Requirement] The records that lead to the real state in the database hold REDACTED FIELDS in a form chosen by a setting with a safe default.
- [Requirement] Default: a hash, so "this value was entered here" can be verified without reading it.
- [Requirement] Explicit setting, never the default: encrypted with a server secret, readable in an emergency. The OWNER calls this the form that does not respect privacy.

## Visibility toward the host (D040)

- [Requirement] A BEAML module can keep something internal so it never leaves toward the host. Open whether this is declared on the TYPE, the field or the module; a very sensible default and an explicit opt-in to expose.

## Redacted fields with rules, lazy recheck, totality (D042, M3)

- [Requirement] When a rule over a redacted field tightens, the check cannot run at build time over absent values. The OWNER's idea: check lazily, the next time the value is entered or touched.
- [Requirement] The lazy path must hold end to end: database, BEAML core, LiveView at runtime, and the whole observability stack. The compiler says at build time, stack-wide, where the lazy case can fail later, under all cases. Totality is preserved.
- [Requirement] Work this out for simple data TYPES first and derive the complex ones later.
- [Requirement] The "old value fails on read" case must come back as a value with a mark, never a crash and never a silent skip (OWNER confirmed the direction, final form open: D042).
- [Statement] The OWNER leaned to "redact never skips a rule; DL-116 leaves the fate list", not yet signed (M3).

## The version rule (DL-155, signed)

- [Requirement] Only TYPES with constructors that have data in production get the hard border: a rule change with affected stored values is a new TYPE VERSION; records always carry the version; the complete answer is in the code. Enums the same way. Signed after three worked examples ("wird von mir so unterschrieben").

## Example rule for pictures (process)

- [Requirement] One example is one coherent unit (TYPE, constructor, migrate) before and after; several examples per point are welcome. If the complete unit gets too long, the example is too big: cut finer instead of showing fragments.

## Roadmap themes (D044 to D047)

- [Requirement] Unify Protocols and Behaviours into one simple, classic interface: a contract, declared once.
- [Requirement] Generics: type variables after the most accepted standards.
- [Requirement] Async compute in the widest sense: OTP from BEAML; Oban as the battle-proven job library.
- [Requirement] Explain how totality and let it crash fit together: totality refers to the data set and the real world that engineers otherwise hold in their heads ("in production the data looks like this; back then we did it that way for that reason"); the language carries that load in compiler and code.

## Process ideas

- [Requirement] Built defaults are presented explicitly and repeatedly until signed off (restated; DL-139 addition).
- [Requirement] A page of the decision site that the OWNER has answered never changes afterwards; new items go to an inbox; changes are logged.
- [Requirement] The decision site follows international UX best practices.

## Tensions to untangle later

- DL-140 C was rejected ("a typo fix must not cost a version") and DL-155 now forces a version on affected data; resolved by the data gate, recorded in DL-155. Kept here as the pattern for future tensions.
- D039 (hash of a redacted value) against the language team's candidate 8 (redacted stored as absent only): open.

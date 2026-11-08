# Totality and let it crash

**[Proposal]** Draft from the OWNER's words on 2026-11-08 (D047). Not a rule yet.

## Two words, two subjects

- **Let it crash** (the BEAM) is about the **running process**. A process that meets a fault it cannot handle stops; a supervisor restarts it in a known state. Nobody writes code for every runtime fault. Source: the BEAM/OTP design, see [BEAM runtime and interop](beam-runtime-and-interop.md).
- **Totality** (BEAML) is about the **data**: every value that was stored yesterday is handled by today's code under today's rules, or the build says where it is not. Every stored TYPE VERSION has a path to the current one, every lost literal has a `map`, every value that fails a new rule has a fate (DL-125, DL-155). Source: [Migrate fates](migrate-fates.md), [Vertical integration](vertical-integration.md).

## Why both hold

- Engineers carry in their heads what production data looks like and why it was written that way ("in 2024 we stored the currency empty because the provider sent none"). That knowledge is unwritten and leaves with the people. BEAML moves this load into the compiler and the code: the TYPE VERSIONS, the `migrate` blocks and the fate lines are that memory, checked on every build against the real rows (DL-151).
- Let it crash stays for what totality does not cover: a dropped connection, a full disk, a bug in the host. The generated Elixir does not catch those; the supervisor does. A typed reject (`Rejected`, `StoreError`) is not a crash: it is a total answer to a known case.
- The border: when a value reaches the runtime that the build has not accounted for (a row written past the build, a bad digest), that is today a runtime failure (DL-150 now blocks the build for not-decodable rows; the live read is the remaining gap, see the final review A2). Totality narrows that border; it never removes the supervisor.

## What this page does not claim

- That BEAML code never crashes. It claims that a crash is never the planned answer to a known data case.
- That totality is proven for all cases. It holds for the cases `--stored` checks (DL-101, DL-102, DL-122, DL-140, P4c) against the snapshot or, later, the live table.

## Open

- D042: lazy recheck of a rule over a REDACTED FIELD, end to end through the host and the observability stack.
- D046: how a crashed or retried job (Oban) is recorded without breaking totality over its attempts.

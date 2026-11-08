# OWNER ideas, 2026-11-08, third capture: PubSub, sockets, hard typing of OTP

**Capture.** Spoken by the OWNER on 2026-11-08, paraphrased by Fable. Not a transcript. Immutable.

- [Requirement] PubSub and sockets (Phoenix.PubSub, channels, LiveView sockets) are a topic of their own: they are EFFECTS too, and BEAML must say how it handles them.
- [Requirement] This belongs to the wider OTP theme (GenServer, supervision, D046) and is tackled with it.
- [Requirement] All of it is typed hard: messages on a topic, socket events and process messages carry BEAML TYPES, checked by the compiler, not free maps.
- [Statement] The OWNER expects this to be one of the most interesting parts ("richtig cool").

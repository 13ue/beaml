---
id: source-gleam-typed-otp
kind: source-note
status: captured, ingested 2026-11-08
updated: 2026-11-08
---

# Gleam typed OTP (gleam_erlang, gleam_otp)

**Origin.** Official Gleam package documentation on hexdocs, tagged package source on GitHub and the Gleam FAQ: [process](https://gleam-erlang.hexdocs.pm/gleam/erlang/process.html), [process source](https://github.com/gleam-lang/erlang/blob/51b0d4566508290cc82be64f9a92b69e96f4c8ce/src/gleam/erlang/process.gleam), [actor](https://gleam-otp.hexdocs.pm/gleam/otp/actor.html), [static_supervisor](https://gleam-otp.hexdocs.pm/gleam/otp/static_supervisor.html), [supervision](https://gleam-otp.hexdocs.pm/gleam/otp/supervision.html), [gleam_otp README](https://github.com/gleam-lang/otp/blob/main/README.md), [decode](https://gleam-stdlib.hexdocs.pm/gleam/dynamic/decode.html), [FAQ](https://gleam.run/frequently-asked-questions/). Third party: [Glyn](https://glyn.hexdocs.pm/). **Author/publisher.** The Gleam project (gleam-lang); Glyn by its own maintainers. **Version.** `gleam_erlang` v1.3.0 (tag `51b0d456…`), `gleam_otp` v1.3.0 (tag `4bd9c3e7…`), Glyn v2.0.3; stdlib and FAQ not version-pinned. **Access date.** 2026-11-08. **Raw path.** [raw/sources/2026-11-08-gleam-typed-otp.md](../../raw/sources/2026-11-08-gleam-typed-otp.md). **License.** Apache-2.0 for the gleam-lang repositories (GitHub metadata); tour text license unknown; Glyn MIT. **Status.** Captured for D046 and D049 ([OWNER capture](../../raw/requirements/2026-11-08-owner-ideas-gleam.md)). **Limits.** Selected excerpts; hexdocs pages were read through a summarising fetch tool, the `process` signatures directly in source. Nothing was compiled or run. Glyn read only from its docs page. Builds on the earlier backend and externals evidence in [typed BEAM languages](typed-beam-languages.md).

## Subject: a typed channel

**[Verified]** `pub opaque type Subject(message) { Subject(owner: Pid, tag: Dynamic)  NamedSubject(name: Name(message)) }`. `send(subject, message)` sends the plain tuple `{tag, message}` to the owner pid; a named subject sends `{name, message}` and panics when no process holds the name. [Source](https://github.com/gleam-lang/erlang/blob/51b0d4566508290cc82be64f9a92b69e96f4c8ce/src/gleam/erlang/process.gleam).

**[Verified]** "Each subject is \"owned\" by the process that created it"; only the owner can receive on it, and `receive(from, within) -> Result(message, Nil)` returns `Error(Nil)` on timeout. The docs compare a Subject to a channel and to a pub-sub topic. [process docs](https://gleam-erlang.hexdocs.pm/gleam/erlang/process.html).

**[Verified]** Request/reply is a typed Subject inside the message: `call(subject, waiting: timeout, sending: fn(Subject(reply)) -> message) -> reply`. Timers are typed too: `send_after(subject, delay, message)`. [Source](https://github.com/gleam-lang/erlang/blob/51b0d4566508290cc82be64f9a92b69e96f4c8ce/src/gleam/erlang/process.gleam).

## Selector: many sources, one payload TYPE

**[Verified]** `Selector(payload)` waits on several sources and maps each to one `payload` TYPE: `select` (a Subject of the payload TYPE), `select_map` (a Subject plus a mapping), `select_monitors`, `select_trapped_exits`, `select_record` (a raw tagged tuple, as `Dynamic`), `select_other` (catch-all, as `Dynamic`), plus `map_selector` and `merge_selector`. `select_record` "will not select messages sent via a subject", because each subject uses a unique tag. [process docs](https://gleam-erlang.hexdocs.pm/gleam/erlang/process.html).

## Actor: typed state and message

**[Verified]** `gleam/otp/actor` is a builder: `actor.new(state) |> actor.on_message(handler) |> actor.start` returns `Result(Started(data), StartError)` with `Started(pid, data)`; `data` is usually the actor's Subject. The handler is `fn(state, message) -> Next(state, message)`; `continue(state)`, `stop()`, `stop_abnormal(reason)`; `with_selector` swaps the selector. Messages are handled one at a time. The module calls this "a fully typed interface" compared with `gen_server`. [actor docs](https://gleam-otp.hexdocs.pm/gleam/otp/actor.html).

**[Verified]** The README states "Full type safety of actors and messages" as a goal, and that functions which cannot be typed safely are left out; not all OTP system messages are supported. [README](https://github.com/gleam-lang/otp/blob/main/README.md).

## Supervision

**[Verified]** `static_supervisor.new(OneForOne | OneForAll | RestForOne) |> add(child) |> restart_tolerance(intensity, period) |> start`. A child is `supervision.ChildSpecification(data)` with `start: fn() -> Result(actor.Started(data), actor.StartError)`. [static_supervisor](https://gleam-otp.hexdocs.pm/gleam/otp/static_supervisor.html), [supervision](https://gleam-otp.hexdocs.pm/gleam/otp/supervision.html).

**[Inference]** `add` returns a plain `Builder`, so the child's typed `data` does not come back through the supervisor; a restarted child has a new pid and new subjects. The documented route to a restarted process is a `Name`: the new process registers the same name and "transparently take-over" ([source](https://github.com/gleam-lang/erlang/blob/51b0d4566508290cc82be64f9a92b69e96f4c8ce/src/gleam/erlang/process.gleam)).

## Untyped messages

**[Verified]** Messages from Erlang or Elixir code that does not use subjects arrive only through `select_record` or `select_other`, as `Dynamic`. `gleam/dynamic/decode` turns `Dynamic` into a typed value or a list of `DecodeError(expected, found, path)`. [process docs](https://gleam-erlang.hexdocs.pm/gleam/erlang/process.html), [decode](https://gleam-stdlib.hexdocs.pm/gleam/dynamic/decode.html).

## What Gleam does not type

- **[Verified]** Names: `register(pid: Pid, name: Name(message))` takes any pid; names are atoms and must be created once at start, never dynamically. [Source](https://github.com/gleam-lang/erlang/blob/51b0d4566508290cc82be64f9a92b69e96f4c8ce/src/gleam/erlang/process.gleam). **[Inference]** The `message` parameter of a Name is a trusted claim, not checked against the process.
- **[Verified]** A Subject is only a pid plus a tag. An internal `unsafely_create_subject(owner, tag)` exists with the comment that nothing verifies the message. [Source](https://github.com/gleam-lang/erlang/blob/51b0d4566508290cc82be64f9a92b69e96f4c8ce/src/gleam/erlang/process.gleam). **[Inference]** Erlang code that knows the tag can send any term on a Subject; the receiver trusts it. This matches the ordinary-term limit in [typed-language boundaries](../concepts/beam/typed-language-boundaries.md#gleam-shows-ordinary-term-code-generation).
- **[Verified]** Hot code: Erlang reloading works, but "it is not possible to type check the upgrades themselves". [FAQ](https://gleam.run/frequently-asked-questions/). **[Inference]** Messages in flight across a code change carry no TYPE VERSION.
- **[Verified]** Typed message passing is a library, not part of the core language. [FAQ](https://gleam.run/frequently-asked-questions/).
- **[Unknown]** Distribution: whether a Subject sent to another node keeps any type evidence was not read; Glyn's use of decoders across nodes suggests not.

## PubSub

**[Verified]** No official gleam-lang PubSub package was found. The third-party Glyn v2.0.3 (MIT, on Erlang `syn`) gives `pubsub.new(scope, decoder, fallback)`, `subscribe` (a selector part) and `publish`; received terms are decoded with the given decoder. [Glyn](https://glyn.hexdocs.pm/). Search also lists `glubsub` and `simple_pubsub` (not read).

**[Unknown]** Phoenix.PubSub from Gleam: no package found. **[Inference]** It would go through an `@external(erlang, "Elixir.Phoenix.PubSub", …)` binding with trusted annotations ([externals guide](https://gleam.run/documentation/externals/)) and a decoder on receive.

## BEAML mapping

See [Prior art: Gleam](../concepts/beam/typed-language-boundaries.md#prior-art-gleam) for the mapping to D046 and D049.

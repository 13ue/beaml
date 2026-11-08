# Gleam typed OTP: selected excerpts and researcher notes (capture 2026-11-08)

**Capture.** Research worker (Opus) for the OWNER task under D046 and D049, accessed 2026-11-08. Immutable after capture; a later reading gets a new dated file.

**Coverage.** Selected short excerpts and signatures, plus researcher notes. Not the full documents. Hexdocs pages were read through a fetch tool that summarises; signatures and quoted lines marked "source" were read directly from the tagged source file. Quoted lines are short and attributed.

**License and attribution.** Publisher: the Gleam project (gleam-lang organisation). GitHub reports Apache-2.0 for `gleam-lang/otp`, `gleam-lang/erlang`, `gleam-lang/stdlib`, `gleam-lang/gleam` and `gleam-lang/website` (checked 2026-11-08 with `gh api repos/<repo>`). The hexdocs pages are generated from these repositories. `gleam-lang/language-tour` has no detected license (GitHub 404 on the license endpoint): **[Unknown]** license of the tour text. The FAQ page footer shows a copyright line, no license statement. Third-party package Glyn: MIT per its docs page. These licenses apply to the upstream material only.

## Pins

| Item | Version | Pin |
|---|---|---|
| `gleam_erlang` | v1.3.0 (hexdocs page) | tag `v1.3.0` = `51b0d4566508290cc82be64f9a92b69e96f4c8ce` |
| `gleam_otp` | v1.3.0 (hexdocs page) | tag `v1.3.0` = `4bd9c3e7963cc5d580a7f8e16526797a76cd9391` |
| `gleam_stdlib` `gleam/dynamic/decode` | version not captured from the page | newest GitHub tag listed: `v1.0.5` (not checked against hexdocs) |
| Gleam compiler | latest release `v1.19.2` (GitHub) | not read here |
| Glyn (third party) | v2.0.3 | not pinned |

## URLs read

- https://gleam-erlang.hexdocs.pm/gleam/erlang/process.html (redirect from https://hexdocs.pm/gleam_erlang/gleam/erlang/process.html)
- https://github.com/gleam-lang/erlang/blob/51b0d4566508290cc82be64f9a92b69e96f4c8ce/src/gleam/erlang/process.gleam (source, via `gh api`)
- https://gleam-otp.hexdocs.pm/gleam/otp/actor.html
- https://gleam-otp.hexdocs.pm/gleam/otp/static_supervisor.html
- https://gleam-otp.hexdocs.pm/gleam/otp/supervision.html
- https://github.com/gleam-lang/otp/blob/main/README.md (default branch read via `gh api` on 2026-11-08; equality with tag `v1.3.0` not checked)
- https://gleam-stdlib.hexdocs.pm/gleam/dynamic/decode.html
- https://gleam.run/frequently-asked-questions/
- https://glyn.hexdocs.pm/ (third party)
- Search result only, not read: packages `glubsub`, `simple_pubsub` on hex.pm.

## gleam_erlang `gleam/erlang/process` v1.3.0

Source, the Subject type:

```gleam
pub opaque type Subject(message) {
  Subject(owner: Pid, tag: Dynamic)
  NamedSubject(name: Name(message))
}
```

Source, `send` (body abridged):

```gleam
pub fn send(subject: Subject(message), message: message) -> Nil {
  case subject {
    Subject(pid, tag) -> raw_send(pid, #(tag, message))
    NamedSubject(name) -> {
      let assert Ok(pid) = named(name) as "Sending to unregistered name"
      raw_send(pid, #(name, message))
    }
  }
  Nil
}
```

Signatures (hexdocs and source agree):

```gleam
pub fn new_subject() -> Subject(message)
pub fn receive(from subject: Subject(message), within timeout: Int) -> Result(message, Nil)
pub fn receive_forever(from subject: Subject(message)) -> message
pub fn new_selector() -> Selector(payload)
pub fn select(selector: Selector(payload), for subject: Subject(payload)) -> Selector(payload)
pub fn select_map(selector: Selector(payload), for subject: Subject(message), mapping transform: fn(message) -> payload) -> Selector(payload)
pub fn select_record(selector: Selector(payload), tag tag: tag, fields arity: Int, mapping transform: fn(Dynamic) -> payload) -> Selector(payload)
pub fn select_other(selector: Selector(payload), mapping handler: fn(Dynamic) -> payload) -> Selector(payload)
pub fn map_selector(a: Selector(a), b: fn(a) -> b) -> Selector(b)
pub fn merge_selector(a: Selector(a), b: Selector(a)) -> Selector(a)
pub fn call(subject: Subject(message), waiting timeout: Int, sending make_request: fn(Subject(reply)) -> message) -> reply
pub fn new_name(prefix prefix: String) -> Name(message)
pub fn named_subject(name: Name(message)) -> Subject(message)
pub fn register(pid: Pid, name: Name(message)) -> Result(Nil, Nil)
pub fn spawn(running: fn() -> anything) -> Pid
pub fn monitor(pid: Pid) -> Monitor
pub fn send_after(subject: Subject(msg), delay: Int, message: msg) -> Timer
@internal pub fn unsafely_create_subject(owner: Pid, tag: Dynamic) -> Subject(message)
```

Short excerpts (doc comments):

- Subject: "Each subject is \"owned\" by the process that created it."
- Subject: similar to "the \"topic\" concept found in some pub-sub systems."
- receive: "Only the process that is owner of the `Subject` can receive a message using it."
- send: panics "when sending to a named subject if no process is currently registed under that name" (upstream spelling).
- Name: "Names are Erlang atoms internally, so never create them dynamically."
- select_record: "This will not select messages sent via a subject even if the message has the same tag in the first position."
- select_other: for "messages from other BEAM languages which do not use subjects or record format messages."
- unsafely_create_subject: "There's nothing here that verifies that the message the subject receives is expected".

Researcher notes:

- A Subject is a pid plus a unique tag; a message on the wire is the plain tuple `{Tag, Message}`. The static type exists only at compile time.
- `register(pid: Pid, name: Name(message))` accepts any `Pid`. Nothing checks that the process behind the pid handles `message`. Inference: the Name type parameter is trusted, as a foreign annotation is.
- The selector maps every source (subject, record tag, monitor, exit, catch-all) into one `payload` type, so the receiving code handles one closed type.
- `select_other` receives `Dynamic`; turning it into a typed value needs a decoder from `gleam/dynamic/decode`.
- No `select_record`/`select_other` path validates by itself; the `fn(Dynamic) -> payload` must do it.

## gleam_otp v1.3.0

`gleam/otp/actor` (hexdocs, partly summarised by the fetch tool):

- The actor offers "a fully typed interface", in contrast to `gen_server`.
- Builder: `actor.new(state)`, `actor.new_with_initialiser(timeout, initialise)`, `actor.on_message(builder, handler)`, `actor.named(builder, name)`, `actor.start(builder) -> Result(Started(return), StartError)`.
- `pub type Started(data) { Started(pid: process.Pid, data: data) }`.
- Handler returns opaque `Next(state, message)`: `actor.continue(state)`, `actor.stop()`, `actor.stop_abnormal(reason)`, `actor.with_selector(next, selector)` replaces the selector.
- "Actors handle messages sequentially".
- Module example: `Message(element)` with `Shutdown`, `Push(push: element)`, `Pop(reply_with: Subject(Result(element, Nil)))`; the reply channel is a typed Subject inside the message.

README (source):

- Goals include "Full type safety of actors and messages." and "Be compatible with Erlang's OTP actor framework."
- "Not all Erlang/OTP functionality is included in this library. Some is not possible to represent in a type safe way, so it is not included."
- System messages: "Actors do not yet support all OTP system messages".
- "The regular Erlang/OTP APIs can be used with and alongside this package".

`gleam/otp/static_supervisor`:

- "a supervisor where the number and types of the children are specified once".
- `new(strategy) -> Builder`, `add(builder, child: supervision.ChildSpecification(data)) -> Builder`, `restart_tolerance(builder, intensity, period)`, `auto_shutdown`, `start(builder) -> Result(actor.Started(Supervisor), actor.StartError)`; strategies `OneForOne`, `OneForAll`, `RestForOne`.

`gleam/otp/supervision`:

- `ChildSpecification(data)` holds `start: fn() -> Result(actor.Started(data), actor.StartError)`; `worker`, `supervisor`, `restart`, `significant`, `timeout`, `map_data`.
- Researcher note: `add` takes `ChildSpecification(data)` for any `data` and returns an untyped `Builder`; the started child's `data` (for example its Subject) is not returned through the supervisor. Inference: after a restart the child has a new pid and new subjects, so clients reach it through a `Name` (named subject).

## gleam_stdlib `gleam/dynamic/decode`

- The `Decoder` type is "a type-safe and composable way to convert dynamic data into some desired type".
- `run(data, decoder)` returns the value or a list of `DecodeError(expected, found, path)`; `field`, `string`, `int`, `success`, `failure`, `one_of`.

## Gleam FAQ (gleam.run, mutable, no version)

- Hot code: "it is not possible to type check the upgrades themselves as we have no way knowing the types of the already running code."
- "Type safe message passing is implemented in Gleam in libraries, rather than being part of the core language itself."

## Third party: Glyn v2.0.3 (MIT)

- "Type-safe PubSub and Registry for Gleam actors with distributed clustering support". Built on the Erlang `syn` library.
- `pubsub.new("orders", orders.event_decoder(), <fallback message>)`; `pubsub.subscribe` returns a selector part; `pubsub.publish(pubsub, group, message)`.
- Messages are sent as Erlang terms and decoded on receipt with the given decoder (fetch-tool summary; not read in source).

## Not found

- No official Gleam package for Phoenix.PubSub was found. Calling `Phoenix.PubSub` from Gleam would go through `@external(erlang, "Elixir.Phoenix.PubSub", ...)` (inference from the externals guide; not tried).
- The Gleam language tour has no OTP chapter that was read for this capture; only its externals page is cited elsewhere in this wiki.

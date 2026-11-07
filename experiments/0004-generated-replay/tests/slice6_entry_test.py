"""EXPERIMENT 0004 slice 6d: the ENTRY LINE, an inbound EFFECT (DL-128, DL-130, DL-131, DL-133, DL-134).

Ledger: workflow/2026-11-07/slice6d-inbound-effect/ (plan.md with "Plan repair", decisions.md, red-plan.md). The
OWNER answers DL-130 to DL-134 override the plan defaults; red-plan.md maps each plan N-test onto them.
Line form (DL-130): `effect ui.place PlaceOrder -> Payment ! PaymentError = ui.event("place") |> place`; the head TYPEs
equal the TYPEs of the target fn (drift rule). Host call (DL-131): `Orders.ui_place(params)`. Reject (DL-133):
`{:error, %Orders.Rejected{reason: "decode" | "constructor"}}`. Slice 6e (Q6E-1 C, Q6E-2 A): the module of an ENTRY
LINE source is named from the stem (orders -> Orders, echo -> Echo, count -> Count; a text source case.beaml -> Case). Stored ENTRY RECORDS (DL-134): `--stored S` also
reads `entries.jsonl` beside S and runs the field constructors and literals of the input TYPE (DL-102, DL-122, DL-124).
Fixtures: slice6/entry/ (orders, echo, count, stored/, bad/). Expected values come from the plan, the decision log and
red-plan.md, never from the new compiler. Guards pass before and after: H2, N13, the elixirc probe.
Runtime harness: the step 12 stubs (span stack, TCP payments stub) plus span kind, attributes and Capture kinds.
Run: python3 -B experiments/0004-generated-replay/tests/slice6_entry_test.py [-k NAME]
Scratch compiler: BEAML_SPIKE=<git archive HEAD build>/target/debug/beaml-spike (another worker writes main.rs).
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_tree import EXPERIMENT, REPO  # noqa: E402
import slice5_syntax_test as s5  # noqa: E402
import slice6_effect_reach_test as ser  # noqa: E402
import slice6_record_test as sr  # noqa: E402
import stored_types_test as st  # noqa: E402

FIX = EXPERIMENT / "slice6" / "entry"
ORDERS, ECHO, COUNT = FIX / "orders.beaml", FIX / "echo.beaml", FIX / "count.beaml"
BAD = FIX / "bad"
STORED = FIX / "stored" / "responses.jsonl"  # empty; entries.jsonl beside it: 3 accepted, 2 rejected at capture
ENTRIES = FIX / "stored" / "entries.jsonl"
EMPTY = ["--stored", str(EXPERIMENT / "stored" / "empty.jsonl")]  # no entries.jsonl beside it
BASE = "ce190054"  # N13: the multi-effect GREEN commit (RV3-14 rule)
ENTRY_LINE = 'effect ui.place PlaceOrder -> Payment ! PaymentError = ui.event("place") |> place\n'
TIMEOUT = 90  # step 13: every compiler run has a time limit
ex = sr.ex

GOOD = {"order_id": "order-1", "amount": {"value": "12.50", "currency": "EUR"}, "channel": "web"}
PLACE_FIELDS = [["order_id", "String"], ["amount", "Amount"], ["channel", "Channel"]]
PLACE_TYPE = {"name": "PlaceOrder", "version": 1, "fields": PLACE_FIELDS,
              "fingerprint": hashlib.sha256(json.dumps(sorted(PLACE_FIELDS), separators=(",", ":")).encode()).hexdigest()}
# D6B-135 keys, plus unknown_fields (red-plan R6D-05: DL-122 needs it to tell a kept value from a lost literal), plus
# outcome and reason (DL-138, R6D-13): "accepted" with reason null, or "rejected" with "decode" or "constructor".
ENTRY_KEYS = sorted(["version", "trace_id", "span_id", "artifact_id", "operation", "attempt", "value", "redacted",
                     "unknown_keys", "unknown_fields", "value_sha256", "type", "outcome", "reason"])
TOKEN = "csrf-token-value-6d"  # a host value outside the input TYPE; it must reach no record

# The drift rule (DL-130) and the subset checks (D6B-129, D6B-130, D6B-138), texts in red-plan.md R6D-07.
def drift(op, role, head, fn, target):
    return ("error: effect %s: the %s TYPE is %s in the head but %s in fn %s (DL-130)\n"
            "  help: write the input, output and failure TYPE of fn %s in the head of effect %s"
            % (op, role, head, fn, target, target, op))


def nested(kind, field):
    return ("error: effect ui.echo: the %s field %s below the top level of PlaceOrder is a slice 6d limit (DL-144)\n"
            "  help: move %s to the top level of PlaceOrder; slice 6d decodes enum and constructor fields at the top "
            "level only" % (kind, field, field))


BAD_CASES = {
    "drift_input": drift("ui.place", "input", "Order", "PlaceOrder", "place"),
    "drift_output": drift("ui.place", "output", "Order", "Payment", "place"),
    "drift_failure": drift("ui.place", "failure", "Declined", "PaymentError", "place"),
    "drift_failure_head_none": drift("ui.place", "failure", "none", "PaymentError", "place"),
    "drift_failure_fn_none": drift("ui.echo", "failure", "NoCurrency", "none", "echo"),
    "transport_route": ("error: effect ui.place: slice 6d supports the inbound transport ui.event only "
                        "(HTTP route entries come later)"),
    "constructor_target": "error: effect ui.amount: Amount is a constructor; an ENTRY LINE calls a fn (DL-120)",
    "two_params": "error: effect ui.echo: fn two must take one parameter",
    "not_flow": ("error: effect ui.place: fn checkout reaches payments.authorize but is not its flow; "
                 "slice 6d replays the flow only"),
    "name_taken": "duplicate name: ui_place",  # the outbound text of main.rs, e.g. `duplicate name: payments_authorize`
    "rejected_reserved": "error: effect ui.place: the TYPE name Rejected is reserved next to an ENTRY LINE (DL-133)",
    "input_constructor": "error: effect ui.keep: Amount has a constructor; slice 6d decodes a plain record (D6B-130)",
    "input_version_mark": ("error: effect ui.count: Count has a MIGRATE CHAIN or a VERSION MARK; slice 6d decodes the "
                           "newest TYPE only (D6B-130)"),
    # TEST O1 (DL-144): an enum or constructor field below the top level is a build error, not a run-time reject.
    "nested_enum": nested("enum", "Line.channel"),
    "nested_constructor": nested("constructor", "Line.amount"),
}

# DL-134 texts: the DL-102 and DL-122 texts of RESPONSE RECORDS with ENTRY RECORD (DL-124: never a stored value).
# DL-138 (O2, R6D-14): the DL-102 help names no TYPE VERSION, because D6B-130 bans a MIGRATE CHAIN on the input TYPE.
CTOR_BLOCK = ("error: TYPE PlaceOrder: 3 stored ENTRY RECORDS of operation ui.place fail the constructor of Amount for "
              "field amount with NoCurrency\n"
              "  record source: %s:1 (line 1)\n"
              "  help: declare the fate of these records in a MIGRATE STEP (DL-102); slice 6d has no MIGRATE STEP for an input "
              "TYPE (D6B-130), so restore the constructor rule of Amount" % ENTRIES)
LITERAL_BLOCK = ("error: TYPE PlaceOrder v1: 1 stored ENTRY RECORD of operation ui.place has a value of field channel "
                 "that is no ENUM LITERAL of Channel now (DL-122)\n"
                 "  record source: %s:2 (line 2)\n"
                 "  help: declare the fate in a MIGRATE STEP (DL-122); slice 6b has no MIGRATE STEP form for an enum field "
                 "(D6B-39), so restore the removed or changed ENUM LITERAL of Channel" % ENTRIES)
# DL-138: lines 4 and 5 of entries.jsonl are rejected at capture; --stored skips them and counts them.
COUNT_LINE = "5 entries, 3 checked, 2 rejected at capture"
# O3 (R6D-15): parity with a removed EFFECT (slice 4 E01; probe in red-output.md, RED repair).
NO_ENTRY_BLOCK = ("error: stored ENTRY RECORD of operation ui.place has no effect in the source\n"
                  "  record source: %s:1 (line 1)\n"
                  "  stored ENTRY RECORDS of operation ui.place: 5\n"
                  "  help: if the effect is deleted on purpose, declare: retire ui.place keep <n> days" % ENTRIES)
RETIRE_ENTRY = "retire ui.place keep 30 days\n"
APP = 'App = "app-channel"  '
# GREEN slice6d: the fixtures hold the DL-083 column alignment of the Amount clauses (N11), so the anchor has it too.
AMOUNT_EMPTY = 'fn Amount _,     ""       ->'
STRICTER = 'fn Amount _, "EUR" -> Amount ! NoCurrency = NoCurrency {}\n' + AMOUNT_EMPTY
STORED_WORDS = ("12.50", "EUR", "order-entry-", "app-channel", "phone", "00000000000000000000000000000001")

STUBS = r'''
defmodule ProbeSupport do
  def span(name, kind, input, _function, f) do
    stack = Process.get(:stack, [])
    log({:span, name, kind, input["order_id"], List.first(stack)})
    Process.put(:stack, [name | stack])

    try do
      f.()
    after
      Process.put(:stack, stack)
    end
  end

  def event(event, step), do: log({:event, event, step, List.first(Process.get(:stack, []))})
  def log(row), do: Process.put(:log, Process.get(:log, []) ++ [row])
  def config(:payments_port), do: :persistent_term.get(:payments_port)
  def config(_), do: nil
  def json(v), do: IO.iodata_to_binary(:json.encode(v))
  def increment, do: :ok
  def beam_hash(_), do: ""
end
defmodule ProbeSupport.Capture do
  def write(kind, record), do: Process.put(:captures, Process.get(:captures, []) ++ [{kind, record}])
end
defmodule OpenTelemetry.Tracer do
  def current_span_ctx, do: nil
end
defmodule OpenTelemetry.Span do
  def hex_trace_id(_), do: ""
  def hex_span_id(_), do: ""
end
defmodule :otel_span do
  def set_attribute(_, key, value), do: ProbeSupport.log({:attr, key, value, List.first(Process.get(:stack, []))})
end
defmodule :otel_propagator_text_map do
  def inject(carrier), do: carrier
end
'''
# Structs through struct/2 at run time: a missing module fails its case, not the whole script.
HELPERS = r'''
good = GOOD
run = fn f ->
  Process.put(:log, [])
  Process.put(:captures, [])
  r = f.()
  {r, Process.get(:log), Process.get(:captures)}
end
rt = fn term -> term |> :json.encode() |> IO.iodata_to_binary() |> :json.decode() end
entries = fn caps -> for {"entries", r} <- caps, do: rt.(r) end
responses = fn caps -> for {"responses", r} <- caps, do: rt.(r) end
rej = fn reason -> {:error, struct(Module.concat(mod, Rejected), reason: reason)} end
amount = fn -> struct(Module.concat(mod, Amount), value: "12.50", currency: "EUR") end
closed = fn f ->
  {:ok, l} = :gen_tcp.listen(0, [])
  {:ok, p} = :inet.port(l)
  :gen_tcp.close(l)
  old = :persistent_term.get(:payments_port)
  :persistent_term.put(:payments_port, p)
  try do
    f.()
  after
    :persistent_term.put(:payments_port, old)
  end
end
'''.replace("GOOD", ex(GOOD))

ROOT = '{:span, "orders.ui.place", :server, nil, nil}'
DECODE, CTOR = 'rej.("decode")', 'rej.("constructor")'
ECHO_OK = '{:ok, %%{"order_id" => "order-1", "amount" => amount.(), "channel" => {"Channel", "%s", [%s]}}}'

ECHO_CASES = {
    # N2: the DL-101 decode through the field constructor and the ENUM LITERAL.
    "N2_decode_through_the_constructor": "Echo.ui_echo(good) == %s" % (ECHO_OK % ("Web", "")),
    "N3_literal": 'Echo.ui_echo(Map.put(good, "channel", "app-channel")) == %s' % (ECHO_OK % ("App", "")),
    "N3_unknown_keeps_the_value": ('Echo.ui_echo(Map.put(good, "channel", "phone")) == %s'
                                   % (ECHO_OK % ("Unknown", '"phone"'))),
    "N4_extra_key_passes": 'Echo.ui_echo(Map.put(good, "_csrf_token", "x")) == %s' % (ECHO_OK % ("Web", "")),
    # N4, D6B-132, D6B-143: a typed reject, never a raise.
    "N4_constructor": 'Echo.ui_echo(put_in(good, ["amount", "currency"], "")) == %s' % CTOR,
    "N4_missing_key": 'Echo.ui_echo(Map.delete(good, "order_id")) == %s' % DECODE,
    "N4_wrong_shape": 'Echo.ui_echo(Map.put(good, "order_id", 7)) == %s' % DECODE,
    "N4_nil": "Echo.ui_echo(nil) == %s" % DECODE,
    "N4_list": "Echo.ui_echo([good]) == %s" % DECODE,
    "N4_atom_keys": ('Echo.ui_echo(%%{order_id: "order-1", amount: %%{"value" => "12.50", "currency" => "EUR"}, '
                     'channel: "web"}) == %s' % DECODE),
    "N4_tuple_value": 'Echo.ui_echo(Map.put(good, "order_id", {:a})) == %s' % DECODE,
    "N4_nested_nil": 'Echo.ui_echo(put_in(good, ["amount", "currency"], nil)) == %s' % DECODE,
    "N4_nested_atom_value": 'Echo.ui_echo(Map.put(good, "channel", :web)) == %s' % DECODE,
    "N4_nested_atom_key": ('Echo.ui_echo(Map.put(good, "amount", %%{value: "12.50", currency: "EUR"})) == %s'
                           % DECODE),
    "N4_struct_value": 'Echo.ui_echo(Map.put(good, "amount", amount.())) == %s' % DECODE,
    "N4_pid_ref_fun": ("Enum.map([self(), make_ref(), fn -> 1 end], &Echo.ui_echo/1) == [%s, %s, %s]"
                       % (DECODE, DECODE, DECODE)),
    # DL-133: one generated struct with the key reason only, also in a source without a failure TYPE.
    "DL133_rejected_shape": "Map.keys(struct(Echo.Rejected)) |> Enum.sort() == [:__struct__, :reason]",
    # N5 (D6B-133, D6B-134): a pure target gives the root span only; N8 (D6B-136): no record.
    "N5_echo_root_span_only": ('run.(fn -> Echo.ui_echo(good) end) |> elem(1) == '
                               '[{:span, "echo.ui.echo", :server, nil, nil}]'),
    "N8_echo_writes_no_record": "run.(fn -> Echo.ui_echo(good) end) |> elem(2) == []",
}
COUNT_CASES = {
    "N4_string_in_int_field": 'Count.ui_count(%%{"qty" => "500"}) == %s' % DECODE,  # D6B-144
    "N4_int_control": 'Count.ui_count(%{"qty" => 500}) == {:ok, %{"qty" => 500}}',
}
PAID = ex({"order_id": "order-1", "status": "authorized"})
CSRF = 'run.(fn -> Orders.ui_place(Map.put(good, "_csrf_token", %s)) end)' % ex(TOKEN)
ORDERS_CASES = {
    # N5: the root span is the parent of the prepared event and of the EFFECT span.
    "N5_root_span_and_children": ('run.(fn -> Orders.ui_place(good) end) |> Tuple.delete_at(2) == {{:ok, %s}, '
                                  '[%s, {:event, "payment_request_prepared", "to_order", "orders.ui.place"}, '
                                  '{:span, "orders.payments.authorize", :client, "order-1", "orders.ui.place"}]}'
                                  % (PAID, ROOT)),
    # N6: a reject stays inside the root span and sets reason there.
    "N6_reject_inside_the_root_span": ('run.(fn -> Orders.ui_place(nil) end) |> Tuple.delete_at(2) == '
                                       '{%s, [%s, {:attr, :reason, "decode", "orders.ui.place"}]}' % (DECODE, ROOT)),
    # N7: a domain failure passes as the failure TYPE of the fn, not as Rejected.
    "N7_domain_failure_passes": ('closed.(fn -> Orders.ui_place(good) end) == '
                                 '{:error, struct(Orders.PaymentError, reason: "transport")}'),
    # N8 (D6B-135): one ENTRY RECORD with the projection, before the RESPONSE RECORD.
    "N8_record_kinds": '%s |> elem(2) |> Enum.map(&elem(&1, 0)) == ["entries", "responses"]' % CSRF,
    "N8_entry_keys": "(%s |> elem(2) |> entries.() |> hd() |> Map.keys() |> Enum.sort()) == %s" % (CSRF, ex(ENTRY_KEYS)),
    "N8_entry_fields": ('(%s |> elem(2) |> entries.() |> hd() |> Map.take(%s)) == %s' % (
        CSRF, ex(["version", "operation", "attempt", "value", "redacted", "unknown_keys", "unknown_fields",
                  "value_sha256", "type", "outcome", "reason"]),
        ex({"version": 3, "operation": "ui.place", "attempt": 1, "value": GOOD, "redacted": [],
            "unknown_keys": ["_csrf_token"], "unknown_fields": [],
            "value_sha256": st.value_sha256(GOOD, ["_csrf_token"]), "type": PLACE_TYPE,
            "outcome": "accepted", "reason": None}))),
    "N8_no_token_in_any_record": ('not String.contains?(%s |> elem(2) |> Enum.map(&rt.(elem(&1, 1))) |> :json.encode() '
                                  '|> IO.iodata_to_binary(), %s)' % (CSRF, ex(TOKEN))),
    "N8_unknown_keys_root_attribute": ('Enum.member?(%s |> elem(1), {:attr, :unknown_keys, ["_csrf_token"], '
                                       '"orders.ui.place"})' % CSRF),
    "N8_kept_value_names_the_field": ('run.(fn -> Orders.ui_place(Map.put(good, "channel", "phone")) end) |> elem(2) '
                                      '|> entries.() |> hd() |> Map.get("unknown_fields") == ["channel"]'),
    # N9 (D6B-137): the REPLAY RUN from the ENTRY RECORD, through JSON as read from JSONL.
    "N9_replay_from_the_entry": ('(fn -> {_, _, caps} = run.(fn -> Orders.ui_place(good) end); '
                                 'Orders.Replay.entry(hd(entries.(caps)), responses.(caps)) end).() == {:ok, %s}'
                                 % PAID),
    "N9_changed_value_is_digest_mismatch": (
        '(fn -> {_, _, caps} = run.(fn -> Orders.ui_place(good) end); e = hd(entries.(caps)); '
        'Orders.Replay.entry(put_in(e, ["value", "order_id"], "order-2"), responses.(caps)) end).() '
        '== {:error, :body_digest_mismatch}'),
    "N9_other_operation_is_operation_mismatch": (
        '(fn -> {_, _, caps} = run.(fn -> Orders.ui_place(good) end); '
        'Orders.Replay.entry(Map.put(hd(entries.(caps)), "operation", "ui.other"), responses.(caps)) end).() '
        '== {:error, :operation_mismatch}'),
    "N9_constructor_reject_replays_as_reject": (
        '(fn -> {r, _, caps} = run.(fn -> Orders.ui_place(put_in(good, ["amount", "currency"], "")) end); '
        '{r, length(responses.(caps)), Orders.Replay.entry(hd(entries.(caps)), [])} end).() == {%s, 0, %s}'
        % (CTOR, CTOR)),
    # DL-138: a reject record names its capture outcome.
    "DL138_constructor_reject_outcome": (
        'run.(fn -> Orders.ui_place(put_in(good, ["amount", "currency"], "")) end) |> elem(2) |> entries.() |> hd() '
        '|> Map.take(["outcome", "reason"]) == %s' % ex({"outcome": "rejected", "reason": "constructor"})),
    # D6B-145: a term check reject writes value null; the REPLAY RUN gives the live outcome.
    "N9_nested_nil_record_holds_null_and_replays_as_decode": (
        '(fn -> {_, _, caps} = run.(fn -> Orders.ui_place(put_in(good, ["amount", "currency"], nil)) end); '
        'e = hd(entries.(caps)); {Map.take(e, ["value", "unknown_keys", "value_sha256", "outcome", "reason"]), '
        'Orders.Replay.entry(e, [])} end).() == {%s, %s}'
        % (ex({"value": None, "unknown_keys": [], "value_sha256": st.value_sha256(None), "outcome": "rejected",
               "reason": "decode"}), DECODE)),
}
HOST = '''defmodule Host do
  def handle_event("place", params, socket), do: {Orders.ui_place(params), socket}
end
'''
# Slice 6e (Q6E-1 C): without its ENTRY LINE the source is BeamlSpike, so the host sees "module Orders is not available";
# with it, "is undefined or private". The common prefix covers both.
UNDEFINED = "Orders.ui_place/1 is undefined"


class Slice6Entry(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        holder = tempfile.mkdtemp(prefix="beaml-0004-s6entry-")
        self.addCleanup(shutil.rmtree, holder)
        self.work = Path(holder)
        (self.work / "cwd").mkdir()

    def compile(self, source, extra=(), binary=None):
        """`source`: a Path or BEAML text. N12: events hold no path, no source text and no stored value."""
        if not isinstance(source, Path):
            path = self.work / "src" / "case.beaml"
            path.parent.mkdir(exist_ok=True)
            path.write_text(source)
            source = path
        result = subprocess.run([binary or st.compiler(), str(source), *extra], cwd=self.work / "cwd",
                                capture_output=True, text=True, timeout=TIMEOUT)
        log = self.work / "cwd" / ".beaml" / "actions.jsonl"
        if log.is_file():
            text = log.read_text()
            self.assertNotIn(str(source.parent), text, "action events must not record the source path")
            for word in ("fn ", "ui.event(") + STORED_WORDS:
                self.assertNotIn(word, text, "action events must not record source text or stored values")
        return result.returncode, result.stdout, result.stderr

    def built(self, source, extra=(), module="Orders"):
        code, stdout, stderr = self.compile(source, extra)
        self.assertEqual((0, True), (code, "defmodule %s do" % module in stdout),
                         "expected exit 0 and Elixir on stdout; stderr: " + stderr)
        return stdout, stderr

    def elixirc(self, stdout, *more):
        """Compile the generated module beside the stubs. Elixir 1.18.1 elixirc exits 0 on warnings (red-output.md)."""
        out = self.work / "beam"
        out.mkdir(exist_ok=True)
        (out / "generated.ex").write_text(stdout)
        (out / "stubs.ex").write_text(STUBS)
        files = [out / "stubs.ex", out / "generated.ex"]
        for name, text in more:
            (out / name).write_text(text)
            files.append(out / name)
        beam = subprocess.run(["elixirc", "--warnings-as-errors", "-o", str(out), *map(str, files)],
                              capture_output=True, text=True, timeout=120)
        return out, beam

    def runtime(self, source, cases, extra=(), module="Orders"):
        stdout, _ = self.built(source, extra, module)
        out, beam = self.elixirc(stdout)
        self.assertEqual(0, beam.returncode, "setup: elixirc failed:\n" + beam.stdout + beam.stderr)
        listed = ",\n".join('  {"%s", fn -> %s end, true}' % (name, check) for name, check in cases.items())
        (out / "checks.exs").write_text(ser.RUNTIME_HEAD + "mod = %s\n" % module + HELPERS + "\ncases = [\n" + listed + "\n]\n"
                                        + ser.RUNTIME_TAIL)
        run = subprocess.run(["elixir", "-pa", str(out), str(out / "checks.exs")], capture_output=True, text=True,
                             timeout=120)
        self.assertEqual(0, run.returncode, "setup: checks.exs did not run:\n" + run.stdout + run.stderr)
        results = dict(line.rsplit(" ", 1) for line in run.stdout.splitlines() if line.endswith((" PASS", " FAIL")))
        for name in cases:
            with self.subTest(name):
                self.assertEqual("PASS", results.get(name), run.stdout)

    # N1 (first RED): the ENTRY LINE parses and gives one host function per line (DL-130, DL-131).

    def test_n1_entry_line_gives_one_function(self):
        for source, extra, name, module in ((ORDERS, EMPTY, "ui_place", "Orders"), (ECHO, (), "ui_echo", "Echo"),
                                            (COUNT, (), "ui_count", "Count")):
            with self.subTest(source.name):
                stdout, stderr = self.built(source, extra, module)
                self.assertEqual((True, ""), ("  def %s(" % name in stdout, stderr))

    def test_n1b_event_name_is_free_text(self):
        # R6D-02: names come from the head; the UI EVENT String may hold a dash.
        self.built(ECHO.read_text().replace('ui.event("echo")', 'ui.event("echo-order")'), module="Case")

    def test_n1c_two_entry_lines_to_one_flow_build(self):
        # Slice 6e (D6B-197, D6B-207): the former D6B-147 reject compiles; each ENTRY LINE gives its function.
        stdout, _ = self.built(EXPERIMENT / "slice6" / "entry" / "two_entries.beaml", EMPTY, "TwoEntries")
        self.assertEqual((1, 1), (stdout.count("  def ui_place("), stdout.count("  def ui_again(")))

    # Runtime: decode, reject, root span, ENTRY RECORD, REPLAY RUN (N2 to N9, DL-133).

    def test_n2_to_n5_echo_runtime(self):
        self.runtime(ECHO, ECHO_CASES, module="Echo")

    def test_n4_count_runtime(self):
        self.runtime(COUNT, COUNT_CASES, module="Count")

    def test_n5_to_n9_orders_runtime(self):
        self.runtime(ORDERS, ORDERS_CASES, EMPTY)

    # DL-131: a removed ENTRY LINE is an undefined remote call in the host build.

    def test_h1_host_build_with_the_entry_has_no_warning(self):
        stdout, _ = self.built(ORDERS, EMPTY)
        _, beam = self.elixirc(stdout, ("host.ex", HOST))
        self.assertEqual((0, False), (beam.returncode, UNDEFINED in beam.stderr), beam.stderr)

    def test_h2_host_build_without_the_entry_warns(self):
        # Guard: the probe sees the removed function (DL-131). elixirc exits 0 here; the warning text decides.
        source = ORDERS.read_text()
        self.assertIn(ENTRY_LINE, source, "setup: the fixture lost its ENTRY LINE")
        stdout, _ = self.built(source.replace(ENTRY_LINE, ""), EMPTY, "BeamlSpike")
        _, beam = self.elixirc(stdout, ("host.ex", HOST))
        self.assertIn(UNDEFINED, beam.stderr)

    # N10 and the drift rule (DL-130): one source per reject case, exact text.

    def test_n10_rejects(self):
        self.assertEqual(sorted(BAD_CASES), sorted(p.stem for p in BAD.glob("*.beaml")), "setup: bad/ and the table differ")
        for name, message in BAD_CASES.items():
            with self.subTest(name):
                code, stdout, stderr = self.compile(BAD / ("%s.beaml" % name), EMPTY)
                self.assertEqual((1, "", message), (code, stdout, stderr.strip()),
                                 "expected exit 1, no stdout and the exact message")

    def test_o1_top_level_enum_and_constructor_and_nested_record_accept_a_good_event(self):
        # TEST O1 control: the nested limit leaves top-level enum and constructor fields and a nested plain record.
        source = ECHO.read_text().replace("type PlaceOrder { order_id: String", "type Line { note: String }\n"
                                          "type PlaceOrder { line: Line order_id: String")
        self.assertIn("line: Line", source, "setup: the echo fixture lost its PlaceOrder TYPE")
        self.runtime(source, {"O1_control_good_event": (
            'match?({:ok, %{"line" => %{"note" => "n"}, "amount" => %Case.Amount{}, '
            '"channel" => {"Channel", "Web", []}}}, Case.ui_echo(Map.put(good, "line", %{"note" => "n"})))')},
                     module="Case")

    # N11 (R6D-06): fmt treats the ENTRY LINE like an EFFECT line.

    def fmt(self, data):
        path = self.work / "fmt" / "case.beaml"
        path.parent.mkdir(exist_ok=True)
        path.write_text(data)
        result = subprocess.run([st.compiler(), "fmt", str(path)], cwd=self.work / "cwd", capture_output=True,
                                text=True, timeout=TIMEOUT)
        return result.returncode, path.read_text(), result.stderr

    def test_n11_fmt_keeps_the_fixtures(self):
        for source in (ORDERS, ECHO, COUNT):
            with self.subTest(source.name):
                code, after, stderr = self.fmt(source.read_text())
                self.assertEqual((0, source.read_text()), (code, after), stderr)

    def test_n11b_fmt_normalizes_the_head_like_an_effect_line(self):
        spaced = ENTRY_LINE.replace("PlaceOrder ->", "PlaceOrder   ->").replace("PaymentError =", "PaymentError    =")
        code, after, stderr = self.fmt(ORDERS.read_text().replace(ENTRY_LINE, spaced))
        self.assertEqual((0, ORDERS.read_text()), (code, after), stderr)

    # DL-134: --stored reads entries.jsonl beside the snapshot (DL-102, DL-122, DL-124).

    def blocked(self, source, extra=("--stored", str(STORED))):
        """Exit, stdout and stderr without the DL-138 count line: a block may print it, it need not."""
        code, stdout, stderr = self.compile(source, extra)
        return code, stdout, "\n".join(l for l in stderr.strip().splitlines() if COUNT_LINE not in l)

    def test_s1_stored_entry_records_build(self):
        # Line 3 holds a value kept as Unknown (unknown_fields): no lost literal, no note. DL-138 (O1): line 4 (a
        # constructor reject) and line 5 (value null) are skipped, not checked and no crash; one count line only.
        _, stderr = self.built(ORDERS, ["--stored", str(STORED)])
        lines = stderr.splitlines()
        self.assertEqual((1, True), (len(lines), COUNT_LINE in "".join(lines)), stderr)

    def test_s2_stricter_constructor_blocks(self):
        source = ORDERS.read_text().replace(AMOUNT_EMPTY, STRICTER)
        self.assertEqual((1, "", CTOR_BLOCK), self.blocked(source))

    def test_s3_removed_literal_blocks(self):
        source = ORDERS.read_text().replace(APP, "")
        self.assertEqual((1, "", LITERAL_BLOCK), self.blocked(source))

    def test_s3b_changed_literal_blocks(self):
        source = ORDERS.read_text().replace(APP, 'App = "app-ch2"  ')
        self.assertEqual((1, "", LITERAL_BLOCK), self.blocked(source))

    def test_s4_no_stored_value_in_output(self):
        # DL-124, DL-032: the block texts name no stored value (events: see compile()).
        for name, source in (("ctor", ORDERS.read_text().replace(AMOUNT_EMPTY, STRICTER)),
                             ("literal", ORDERS.read_text().replace(APP, ""))):
            with self.subTest(name):
                code, _, stderr = self.compile(source, ["--stored", str(STORED)])
                # The block itself must stand in stderr, so a parse error cannot pass this test.
                self.assertEqual((1, True, []), (code, "stored ENTRY RECORD" in stderr,
                                                 [w for w in STORED_WORDS if w in stderr]), stderr)

    # O3 (DL-138, R6D-15): a removed ENTRY LINE with stored ENTRY RECORDS behaves as a removed EFFECT (slice 4 E01, E02).

    def test_s5_removed_entry_line_with_stored_entries_blocks(self):
        source = ORDERS.read_text()
        self.assertIn(ENTRY_LINE, source, "setup: the fixture lost its ENTRY LINE")
        self.assertEqual((1, "", NO_ENTRY_BLOCK), self.blocked(source.replace(ENTRY_LINE, "")))

    def test_s5b_retire_line_frees_the_removed_entry_line(self):
        code, stdout, stderr = self.compile(ORDERS.read_text().replace(ENTRY_LINE, RETIRE_ENTRY),
                                            ["--stored", str(STORED)])
        self.assertEqual((0, True, False, False), (code, "defmodule BeamlSpike do" in stdout, "error" in stderr,
                                                   "DEAD LINE" in stderr), stderr)

    # N13 (guard): every tracked source without an ENTRY LINE keeps its bytes against the pre-6d compiler.

    def test_n13_sources_without_an_entry_keep_their_bytes(self):
        listed = subprocess.run(["git", "-C", str(REPO), "ls-files", "experiments/0001-syntax-to-beam/*.beaml",
                                 "experiments/0002-http-correlation/apps/*.beaml",
                                 "experiments/0004-generated-replay/slice*/*.beaml",
                                 "experiments/0004-generated-replay/drift/*.beaml",
                                 "experiments/0004-generated-replay/bad/*.beaml"],
                                capture_output=True, text=True, check=True).stdout.split()
        # GREEN slice6d: an ENTRY LINE is an `effect` line with `|>` after the call; `ui.event(` alone missed
        # bad/transport_route.beaml (http.route), which N10 needs to change its bytes.
        sources = [REPO / p for p in listed if not re.search(r"^effect .*\)\s*\|>", (REPO / p).read_text(), re.M)]
        self.assertGreater(len(sources), 100, "setup: too few tracked sources")
        base = s5.compiler_at(BASE)
        for path in sources:
            with self.subTest(str(path.relative_to(REPO))):
                self.assertEqual(self.compile(path, EMPTY, base), self.compile(path, EMPTY))


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)

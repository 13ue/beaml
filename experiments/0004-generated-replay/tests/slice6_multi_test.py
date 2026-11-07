"""EXPERIMENT 0004 slice 6e: several EFFECTS and ENTRY LINES per source, module named from the source (0005 P3, P5).

Ledger: workflow/2026-11-07/multi-effect-module/ (plan.md with "Plan repair", decisions.md D6B-197 to D6B-213,
red-plan.md maps N1 to N15 onto the tests). Defaults (DL-144, open): Q6E-1 C (the stem names the module of an ENTRY
LINE source: orders.beaml -> Orders; every other source stays BeamlSpike), Q6E-2 A (`Orders.Rejected`), Q6E-3 A
(`Replay.run(operation, a0, trace_id, records)` with two or more EFFECTS), Q6E-4 A (one EFFECT per flow).
Fixtures: slice6/multi/ (orders.beaml; no_hold/, no_hold_retired/, copy/ each with orders.beaml per D6B-210; bad/ per
D6B-211). The RECORD SNAPSHOTS of N7 to N9 are written by the test from the N4 records, not by hand.
Expected values come from the plan, the decision log and the slice 6d expected values, never from the new compiler.
Guards pass before and after: N13, N14 (stem error, BeamlSpike source).
Run: python3 -B experiments/0004-generated-replay/tests/slice6_multi_test.py [-k NAME]
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

FIX = EXPERIMENT / "slice6" / "multi"
MULTI = FIX / "orders.beaml"
NO_HOLD, NO_HOLD_RETIRED = FIX / "no_hold" / "orders.beaml", FIX / "no_hold_retired" / "orders.beaml"
COPY = FIX / "copy" / "orders.beaml"
BAD = FIX / "bad"
ENTRY_FIX = EXPERIMENT / "slice6" / "entry"
EMPTY = ["--stored", str(EXPERIMENT / "stored" / "empty.jsonl")]
# N13 (D6B-212): the P3 base. At RED this is HEAD 545dded0 (P2 not landed). After P2 GREEN it moves to the P2 pin
# commit (RV3-14); a pin sub-step in this step moves it to its GREEN hash.
BASE = "545dded0"
TIMEOUT = 90
ex = sr.ex

STOCK_LINE = 'effect stock.reserve Order      -> Hold ! StockError      = http.post("stock/reserve")\n'
HOLD_ENTRY = 'effect ui.hold PlaceOrder  -> Hold ! StockError      = ui.event("hold") |> hold\n'
PAY_LINE = 'effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize")\n'
PLACE_ENTRY = 'effect ui.place PlaceOrder -> Payment ! PaymentError = ui.event("place") |> place\n'
PLACE_FN = "\nfn place p: PlaceOrder -> Payment ! PaymentError =\n  p\n  |> to_order\n  |> payments.authorize\n"
# N9 W2 on Payment, not Hold: Hold.amount is a constructor field, and D6B-39 bans a MIGRATE CHAIN there (red-plan.md).
PAYMENT_TYPE = "type Payment { order_id: String status: String }\n"
MIGRATE_PAYMENT = "migrate Payment v1 -> v2 { drop note: String }\n"
GOOD = {"order_id": "order-1", "amount": {"value": "12.50", "currency": "EUR"}, "channel": "web"}
STORED_WORDS = ("12.50", "EUR", "order-1", "app-channel", "authorized")

# N10: one source per reject case, exact text (decisions.md Q6E-4 A, D6B-201, D6B-203).
BAD_CASES = {
    "two_effects_in_one_pipe": ("error: fn place calls the effects payments.authorize and audit.log; "
                                "slice 6e replays a flow with one effect"),
    "same_entry_operation": "duplicate name: ui_place",
    "enum": ("error: the source file name enum gives the module Enum, which the generated code calls; "
             "rename the file"),
}


def orphan(kind, op, source, line, count):
    """The slice 4 E01 orphan block (RESPONSE) and its slice 6d ENTRY parity (DL-138, R6D-15)."""
    return ("error: stored %s RECORD of operation %s has no effect in the source\n"
            "  record source: %s:%d (line %d)\n"
            "  stored %s RECORDS of operation %s: %d\n"
            "  help: if the effect is deleted on purpose, declare: retire %s keep <n> days"
            % (kind, op, source, line, line, kind, op, count, op))


# The slice 6d stubs with two changes: config/1 knows :stock_port, and the span context is the root span name, so
# that the two flows have two trace ids (N4). hex_trace_id gives the lower-case hex of that name, "" with no span.
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
  def config(:stock_port), do: :persistent_term.get(:stock_port)
  def config(_), do: nil
  def json(v), do: IO.iodata_to_binary(:json.encode(v))
  def increment, do: :ok
  def beam_hash(_), do: ""
end
defmodule ProbeSupport.Capture do
  def write(kind, record), do: Process.put(:captures, Process.get(:captures, []) ++ [{kind, record}])
end
defmodule OpenTelemetry.Tracer do
  def current_span_ctx, do: List.last(Process.get(:stack, []))
end
defmodule OpenTelemetry.Span do
  def hex_trace_id(nil), do: ""
  def hex_trace_id(root), do: :binary.encode_hex(root, :lowercase)
  def hex_span_id(nil), do: ""
  def hex_span_id(root), do: :binary.encode_hex(root, :lowercase)
end
defmodule :otel_span do
  def set_attribute(_, key, value), do: ProbeSupport.log({:attr, key, value, List.first(Process.get(:stack, []))})
end
defmodule :otel_propagator_text_map do
  def inject(carrier), do: carrier
end
'''
# Two TCP stubs (the step 12 stub twice), each with a request counter: index 1 payments, index 2 stock.
HEAD = r'''
counts = :counters.new(2, [])
stub = fn key, index, reply ->
  {:ok, listen} = :gen_tcp.listen(0, [:binary, active: false, reuseaddr: true])
  {:ok, port} = :inet.port(listen)
  :persistent_term.put(key, port)
  drain = fn drain, s -> case :gen_tcp.recv(s, 0, 2000) do {:ok, _} -> drain.(drain, s); _ -> :ok end end
  serve = fn serve ->
    {:ok, s} = :gen_tcp.accept(listen)
    {:ok, _} = :gen_tcp.recv(s, 0, 2000)
    :counters.add(counts, index, 1)
    :ok = :gen_tcp.send(s, "HTTP/1.1 200 OK\r\nContent-Length: #{byte_size(reply)}\r\nConnection: close\r\n\r\n" <> reply)
    :gen_tcp.shutdown(s, :write)
    drain.(drain, s)
    :gen_tcp.close(s)
    serve.(serve)
  end
  spawn(fn -> serve.(serve) end)
end
stub.(:payments_port, 1, ~s({"order_id":"order-1","status":"authorized"}))
stub.(:stock_port, 2, ~s({"order_id":"order-1","amount":{"value":"12.50","currency":"EUR"}}))
requests = fn f ->
  before = {:counters.get(counts, 1), :counters.get(counts, 2)}
  r = f.()
  {r, {:counters.get(counts, 1) - elem(before, 0), :counters.get(counts, 2) - elem(before, 1)}}
end
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
rej = fn reason -> {:error, struct(Orders.Rejected, reason: reason)} end
amount = fn -> struct(Orders.Amount, value: "12.50", currency: "EUR") end
paid = {:ok, %{"order_id" => "order-1", "status" => "authorized"}}
held = {:ok, %{"order_id" => "order-1", "amount" => amount.()}}
# The decoded PlaceOrder: the a0 of a flow REPLAY RUN (slice 6d ECHO_OK form).
decoded = %{"order_id" => "order-1", "amount" => amount.(), "channel" => {"Channel", "Web", []}}
# Both live flows, place first: their ENTRY and RESPONSE RECORDS through JSON, as read from JSONL.
live = fn ->
  {_, _, place_caps} = run.(fn -> Orders.ui_place(good) end)
  {_, _, hold_caps} = run.(fn -> Orders.ui_hold(good) end)
  caps = place_caps ++ hold_caps
  {entries.(caps), responses.(caps)}
end
'''.replace("GOOD", ex(GOOD))
TAIL_DUMP = r'''
{es, rs} = live.()
File.write!(System.get_env("DUMP_ENTRIES"), Enum.map(es, &(IO.iodata_to_binary(:json.encode(&1)) <> "\n")))
File.write!(System.get_env("DUMP_RESPONSES"), Enum.map(rs, &(IO.iodata_to_binary(:json.encode(&1)) <> "\n")))
'''

PLACE_LOG = ('[{:span, "orders.ui.place", :server, nil, nil}, '
             '{:event, "payment_request_prepared", "to_order", "orders.ui.place"}, '
             '{:span, "orders.payments.authorize", :client, "order-1", "orders.ui.place"}]')
HOLD_LOG = ('[{:span, "orders.ui.hold", :server, nil, nil}, '
            '{:event, "hold_request_prepared", "to_order", "orders.ui.hold"}, '
            '{:span, "orders.stock.reserve", :client, "order-1", "orders.ui.hold"}]')
BAD_HOLD = 'put_in(good, ["amount", "currency"], "")'
# Index 0 and 1 of the entries and responses lists are place and hold (live/0 order).
WITH = '(fn -> {[pe, he], [pr, hr]} = live.(); %s end).()'
RUNTIME_CASES = {
    # N3: two live flows, each with its own root span, prepared event, EFFECT span and stub request.
    "N3_place_value": "Orders.ui_place(good) == paid",
    "N3_hold_value": "Orders.ui_hold(good) == held",
    "N3_place_spans": "run.(fn -> Orders.ui_place(good) end) |> elem(1) == %s" % PLACE_LOG,
    "N3_hold_spans": "run.(fn -> Orders.ui_hold(good) end) |> elem(1) == %s" % HOLD_LOG,
    "N3_place_requests": "requests.(fn -> Orders.ui_place(good) end) |> elem(1) == {1, 0}",
    "N3_hold_requests": "requests.(fn -> Orders.ui_hold(good) end) |> elem(1) == {0, 1}",
    # N4: two ENTRY RECORDS and two RESPONSE RECORDS; each RESPONSE RECORD in the trace of its ENTRY RECORD.
    "N4_operations": ('(fn -> {es, rs} = live.(); {Enum.map(es, & &1["operation"]), Enum.map(rs, & &1["operation"])} '
                      'end).() == {["ui.place", "ui.hold"], ["payments.authorize", "stock.reserve"]}'),
    "N4_traces": WITH % ('pe["trace_id"] == pr["trace_id"] and he["trace_id"] == hr["trace_id"] and '
                         'pe["trace_id"] != he["trace_id"] and pe["trace_id"] != ""'),
    # N5 (Q6E-3 A, D6B-200): the REPLAY RUN picks the flow by operation; JSON records as read from JSONL.
    "N5_entry_place": WITH % "Orders.Replay.entry(pe, [pr, hr]) == paid",
    "N5_entry_hold": WITH % "Orders.Replay.entry(he, [pr, hr]) == held",
    "N5_run_stock_reserve": WITH % 'Orders.Replay.run("stock.reserve", decoded, hr["trace_id"], [pr, hr]) == held',
    "N5_run_payments_authorize": (WITH % 'Orders.Replay.run("payments.authorize", decoded, pr["trace_id"], [pr, hr]) '
                                  '== paid'),
    "N5_run_other_flow_on_the_hold_trace": (
        WITH % 'Orders.Replay.run("payments.authorize", decoded, hr["trace_id"], [pr, hr]) == {:error, :operation_mismatch}'),
    "N5_run_unknown_operation": (WITH % 'Orders.Replay.run("x.y", decoded, hr["trace_id"], [pr, hr]) == '
                                 '{:error, :operation_mismatch}'),
    "N5_entry_other_operation": (WITH % 'Orders.Replay.entry(Map.put(he, "operation", "ui.other"), [pr, hr]) == '
                                 '{:error, :operation_mismatch}'),
    "N5_entry_changed_value": (WITH % 'Orders.Replay.entry(put_in(he, ["value", "order_id"], "order-2"), [pr, hr]) == '
                               '{:error, :body_digest_mismatch}'),
    # N6: a reject per ENTRY LINE: Orders.Rejected (Q6E-2 A), no stock request, an ENTRY RECORD of ui.hold.
    "N6_hold_reject": ('(fn -> {{r, _, caps}, n} = requests.(fn -> run.(fn -> Orders.ui_hold(%s) end) end); '
                       '{r, n, Enum.map(entries.(caps), &Map.take(&1, ["operation", "outcome", "reason"])), '
                       'responses.(caps)} end).() == {rej.("constructor"), {0, 0}, '
                       '[%%{"operation" => "ui.hold", "outcome" => "rejected", "reason" => "constructor"}], []}'
                       % BAD_HOLD),
    "Q6E2_rejected_shape": "Map.keys(struct(Orders.Rejected)) |> Enum.sort() == [:__struct__, :reason]",
}


class Slice6Multi(unittest.TestCase):
    maxDiff = None
    _records = None  # (entries lines, responses lines) of the N4 live run, written once per process

    def setUp(self):
        holder = tempfile.mkdtemp(prefix="beaml-0004-s6multi-")
        self.addCleanup(shutil.rmtree, holder)
        self.work = Path(holder)
        (self.work / "cwd").mkdir()

    def compile(self, source, extra=(), binary=None, stem="orders"):
        """`source`: a Path or BEAML text (written as <stem>.beaml, D6B-210). N12: events hold no path, no source
        text and no stored value."""
        if not isinstance(source, Path):
            path = self.work / "src" / ("%s.beaml" % stem)
            path.parent.mkdir(exist_ok=True)
            path.write_text(source)
            source = path
        result = subprocess.run([binary or st.compiler(), str(source), *extra], cwd=self.work / "cwd",
                                capture_output=True, text=True, timeout=TIMEOUT)
        log = self.work / "cwd" / ".beaml" / "actions.jsonl"
        if log.is_file():
            text = log.read_text()
            self.assertNotIn(str(source.parent), text, "action events must not record the source path")
            for word in ("fn ", "ui.event(", "http.post(") + STORED_WORDS:
                self.assertNotIn(word, text, "action events must not record source text or stored values")
        return result.returncode, result.stdout, result.stderr

    def built(self, source, extra=EMPTY, module="Orders"):
        code, stdout, stderr = self.compile(source, extra)
        self.assertEqual((0, True), (code, "defmodule %s do" % module in stdout),
                         "expected exit 0 and defmodule %s on stdout; stderr: %s" % (module, stderr))
        return stdout, stderr

    def elixirc(self, stdout):
        """Compile the generated module beside the stubs. Elixir 1.18.1 elixirc exits 0 on warnings, so the
        warning text is checked too (slice 6d red-output.md)."""
        out = self.work / "beam"
        out.mkdir(exist_ok=True)
        (out / "generated.ex").write_text(stdout)
        (out / "stubs.ex").write_text(STUBS)
        beam = subprocess.run(["elixirc", "--warnings-as-errors", "-o", str(out), str(out / "stubs.ex"),
                               str(out / "generated.ex")], capture_output=True, text=True, timeout=120)
        return out, beam

    def compiled(self):
        stdout, _ = self.built(MULTI)
        out, beam = self.elixirc(stdout)
        self.assertEqual((0, False), (beam.returncode, "warning" in beam.stdout + beam.stderr),
                         "setup: elixirc failed or warned:\n" + beam.stdout + beam.stderr)
        return out

    def records(self):
        """The N4 records as JSONL lines: (entries, responses), each in live order (place, hold)."""
        if Slice6Multi._records is None:
            out = self.compiled()
            (out / "dump.exs").write_text(HEAD + TAIL_DUMP)
            dump = {"DUMP_ENTRIES": str(out / "e.jsonl"), "DUMP_RESPONSES": str(out / "r.jsonl")}
            done = subprocess.run(["elixir", "-pa", str(out), str(out / "dump.exs")], capture_output=True, text=True,
                                  timeout=120, env=dict(os.environ, **dump))
            self.assertEqual(0, done.returncode, "setup: dump.exs failed:\n" + done.stdout + done.stderr)
            Slice6Multi._records = (Path(dump["DUMP_ENTRIES"]).read_text().splitlines(),
                                    Path(dump["DUMP_RESPONSES"]).read_text().splitlines())
        return Slice6Multi._records

    def snapshot(self, name, responses, entries=None):
        """A RECORD SNAPSHOT directory: responses.jsonl, and entries.jsonl beside it when `entries` is given."""
        folder = self.work / "stored" / name
        folder.mkdir(parents=True)
        (folder / "responses.jsonl").write_text("".join(line + "\n" for line in responses))
        if entries is not None:
            (folder / "entries.jsonl").write_text("".join(line + "\n" for line in entries))
        return folder / "responses.jsonl"

    # N1 (first RED): two http EFFECTS and two ENTRY LINES build; every shared module stands once (D6B-197, D6B-198).

    def test_n1_two_effects_and_two_entry_lines_build(self):
        code, stdout, stderr = self.compile(MULTI, EMPTY)
        self.assertEqual((0, ""), (code, stderr.strip()), "expected exit 0 and no stderr")
        for line in ("defmodule Orders do", "defmodule Replay do", "defmodule Http do", "defmodule BeamlFailure do",
                     "defmodule Rejected do", "def ui_place(", "def ui_hold(", "def payments_authorize(",
                     "def stock_reserve("):
            with self.subTest(line):
                self.assertEqual(1, stdout.count(line))
        self.assertNotIn("BeamlSpike", stdout)

    # N2: the host build catches a duplicate def or module (D6B-198).

    def test_n2_output_compiles_without_warnings(self):
        stdout, _ = self.built(MULTI)
        _, beam = self.elixirc(stdout)
        self.assertEqual((0, False), (beam.returncode, "warning" in beam.stdout + beam.stderr),
                         beam.stdout + beam.stderr)

    # N3 to N6: the runtime of two flows, the records and the REPLAY RUN by operation.

    def test_n3_to_n6_runtime(self):
        out = self.compiled()
        listed = ",\n".join('  {"%s", fn -> %s end, true}' % (name, check) for name, check in RUNTIME_CASES.items())
        (out / "checks.exs").write_text(HEAD + "\ncases = [\n" + listed + "\n]\n" + ser.RUNTIME_TAIL)
        run = subprocess.run(["elixir", "-pa", str(out), str(out / "checks.exs")], capture_output=True, text=True,
                             timeout=120)
        self.assertEqual(0, run.returncode, "setup: checks.exs did not run:\n" + run.stdout + run.stderr)
        results = dict(line.rsplit(" ", 1) for line in run.stdout.splitlines() if line.endswith((" PASS", " FAIL")))
        for name in RUNTIME_CASES:
            with self.subTest(name):
                self.assertEqual("PASS", results.get(name), run.stdout)

    # N7 to N9 (D6B-206): --stored, DL-040 orphans and DEAD LINES per operation over one RECORD SNAPSHOT.

    def test_n7_stored_snapshot_with_two_operations_builds(self):
        entries, responses = self.records()
        stored = self.snapshot("n7", responses, entries)
        _, stderr = self.built(MULTI, ["--stored", str(stored)])
        self.assertIn("2 entries, 2 checked, 0 rejected at capture", stderr)

    def test_n8_orphan_block_per_operation(self):
        entries, responses = self.records()
        stored = self.snapshot("n7", responses, entries)
        with self.subTest("no_hold"):
            code, stdout, stderr = self.compile(NO_HOLD, ["--stored", str(stored)])
            self.assertEqual((1, ""), (code, stdout), stderr)
            self.assertIn(orphan("RESPONSE", "stock.reserve", stored, 2, 1), stderr)
            self.assertNotIn("operation payments.authorize has no effect", stderr)
        with self.subTest("two_blocks"):
            # Two stock.reserve records and one payments.authorize record; a source without both EFFECTS.
            pure = NO_HOLD.read_text()
            for part in (PAY_LINE, PLACE_ENTRY, PLACE_FN):
                self.assertIn(part, pure, "setup: no_hold changed")
                pure = pure.replace(part, "")
            two = self.snapshot("two", [responses[0], responses[1], responses[1]])
            code, stdout, stderr = self.compile(pure, ["--stored", str(two)])
            self.assertEqual((1, ""), (code, stdout), stderr)
            self.assertIn(orphan("RESPONSE", "payments.authorize", two, 1, 1), stderr)
            self.assertIn(orphan("RESPONSE", "stock.reserve", two, 2, 2), stderr)
        with self.subTest("retire_stock_only"):
            source = NO_HOLD.read_text().replace(PAY_LINE, "retire stock.reserve keep 30 days\n" + PAY_LINE)
            code, stdout, stderr = self.compile(source, ["--stored", str(stored)])
            self.assertEqual((1, ""), (code, stdout), stderr)
            self.assertIn(orphan("ENTRY", "ui.hold", stored.parent / "entries.jsonl", 2, 1), stderr)
            self.assertNotIn("stored RESPONSE RECORD of operation", stderr)
        with self.subTest("both_retired"):
            code, stdout, stderr = self.compile(NO_HOLD_RETIRED, ["--stored", str(stored)])
            self.assertEqual((0, True, False, False), (code, "defmodule Orders do" in stdout, "error" in stderr,
                                                       "DEAD LINE" in stderr), stderr)

    def test_n9_dead_line_per_operation(self):
        entries, responses = self.records()
        place_only = self.snapshot("place", [responses[0]], [entries[0]])
        with self.subTest("W1_per_retire_line"):
            code, stdout, stderr = self.compile(NO_HOLD_RETIRED, ["--stored", str(place_only)])
            warnings = [line for line in stderr.splitlines() if line.startswith("warning: DEAD LINE: ")]
            self.assertEqual((0, ["warning: DEAD LINE: retire stock.reserve keep 30 days",
                                  "warning: DEAD LINE: retire ui.hold keep 30 days"]), (code, warnings), stderr)
        hold_only = self.snapshot("hold", [responses[1]], [entries[1]])
        source = MULTI.read_text()
        self.assertIn(PAYMENT_TYPE, source, "setup: the fixture lost its Payment TYPE")
        source = source.replace(PAYMENT_TYPE, PAYMENT_TYPE + MIGRATE_PAYMENT)
        with self.subTest("W2_without_a_payment_record"):
            _, stderr = self.built(source, ["--stored", str(hold_only)])
            self.assertIn("warning: DEAD LINE: migrate Payment v1 -> v2", stderr)
        with self.subTest("no_W2_with_one_old_payment_record"):
            # One payments.authorize record at Payment v1 (with note) beside the hold records: the minimum over
            # operations keeps the step.
            old = json.loads(responses[0])
            fields = sorted([["note", "String"], ["order_id", "String"], ["status", "String"]])
            value = dict(old["value"], note="n")
            old.update(value=value, value_sha256=st.value_sha256(value, old["unknown_keys"], old["redacted"]),
                       type={"name": "Payment", "version": 1, "fields": fields, "fingerprint": hashlib.sha256(
                           json.dumps(fields, separators=(",", ":")).encode()).hexdigest()})
            mixed = self.snapshot("mixed", [responses[1], json.dumps(old)], [entries[1]])
            _, stderr = self.built(source, ["--stored", str(mixed)])
            self.assertNotIn("DEAD LINE", stderr)

    # N10: compile rejects, exact text.

    def test_n10_rejects(self):
        self.assertEqual(sorted(BAD_CASES), sorted(p.stem for p in BAD.glob("*.beaml")), "setup: bad/ and the table differ")
        for name, message in BAD_CASES.items():
            with self.subTest(name):
                code, stdout, stderr = self.compile(BAD / ("%s.beaml" % name), EMPTY)
                self.assertEqual((1, "", message), (code, stdout, stderr.strip()),
                                 "expected exit 1, no stdout and the exact message")

    # N11 (D6B-205): fmt aligns the two EFFECT lines and the two ENTRY LINES; the fixture is a fixed point.

    def fmt(self, data):
        path = self.work / "fmt" / "orders.beaml"
        path.parent.mkdir(exist_ok=True)
        path.write_text(data)
        result = subprocess.run([st.compiler(), "fmt", str(path)], cwd=self.work / "cwd", capture_output=True,
                                text=True, timeout=TIMEOUT)
        return result.returncode, path.read_text(), result.stderr

    def test_n11_fmt_keeps_the_fixture(self):
        code, after, stderr = self.fmt(MULTI.read_text())
        self.assertEqual((0, MULTI.read_text()), (code, after), stderr)

    def test_n11b_fmt_aligns_a_single_spaced_effect_line(self):
        text = MULTI.read_text()
        self.assertIn(STOCK_LINE, text, "setup: the fixture lost its stock.reserve line")
        single = " ".join(STOCK_LINE.split()) + "\n"
        code, after, stderr = self.fmt(text.replace(STOCK_LINE, single))
        self.assertEqual((0, text), (code, after), stderr)

    # N13 (guard, D6B-212): every tracked source without an ENTRY LINE keeps its bytes against the P3 base.

    def test_n13_sources_without_an_entry_keep_their_bytes(self):
        listed = subprocess.run(["git", "-C", str(REPO), "ls-files", "experiments/0001-syntax-to-beam/*.beaml",
                                 "experiments/0002-http-correlation/apps/*.beaml",
                                 "experiments/0004-generated-replay/slice*/*.beaml",
                                 "experiments/0004-generated-replay/drift/*.beaml",
                                 "experiments/0004-generated-replay/bad/*.beaml"],
                                capture_output=True, text=True, check=True).stdout.split()
        # The slice 6d G6D-01 filter: an ENTRY LINE is an `effect` line with `|>` after the call.
        sources = [REPO / p for p in listed if not re.search(r"^effect .*\)\s*\|>", (REPO / p).read_text(), re.M)]
        self.assertGreater(len(sources), 100, "setup: too few tracked sources")
        base = s5.compiler_at(BASE)
        for path in sources:
            with self.subTest(str(path.relative_to(REPO))):
                self.assertEqual(self.compile(path, EMPTY, base), self.compile(path, EMPTY))

    # N14 (Q6E-1 C): the module name of the existing ENTRY LINE fixtures and of a copy under the stem orders.

    def test_n14_entry_line_sources_take_the_stem(self):
        for source, extra, module in ((ENTRY_FIX / "orders.beaml", EMPTY, "Orders"), (ENTRY_FIX / "echo.beaml", (), "Echo"),
                                      (ENTRY_FIX / "count.beaml", (), "Count"), (COPY, EMPTY, "Orders")):
            with self.subTest(str(source.relative_to(EXPERIMENT))):
                stdout, _ = self.built(source, extra, module)
                self.assertNotIn("BeamlSpike", stdout)

    def test_n14b_source_without_entry_line_stays_beamlspike(self):
        # Guard: an EFFECT source without an ENTRY LINE (stem orders) keeps BeamlSpike (Q6E-1 C).
        stdout, _ = self.built(EXPERIMENT / "slice2" / "reuse" / "orders.beaml", EMPTY, "BeamlSpike")
        self.assertNotIn("defmodule Orders do", stdout)

    def test_n14c_non_identifier_stem_keeps_the_stem_error(self):
        # Guard: an ENTRY LINE source under a stem that is no lowercase identifier keeps the existing text.
        code, stdout, stderr = self.compile((ENTRY_FIX / "echo.beaml").read_text(), (), stem="order-flow")
        self.assertEqual((1, "", "a pipe or an effect needs a source file name that is a lowercase identifier "
                                 "(it names the spans)"), (code, stdout, stderr.strip()))

    # N15: one capital per `_` segment. Black box from here (main.rs belongs to the GREEN worker; the cargo unit
    # test `module_name_from_stem` of the plan is GREEN's to add).

    def test_n15_module_name_from_stem(self):
        echo = (ENTRY_FIX / "echo.beaml").read_text()
        for stem, module in (("order_flow", "OrderFlow"), ("v2_orders", "V2Orders")):
            with self.subTest(stem):
                code, stdout, stderr = self.compile(echo, (), stem=stem)
                self.assertEqual((0, True, False), (code, "defmodule %s do" % module in stdout,
                                                    "BeamlSpike" in stdout), stderr)


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)

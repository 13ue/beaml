"""EXPERIMENT 0004 slice 6b step 7: decode of ENUM LITERALS from outside data (DL-082 L, DL-065, DL-102, DL-103).

Plan step 7, D6B-35 to D6B-37, D6B-39; D6B-38 "count only" is superseded by DL-102. Ledger:
workflow/2026-11-07/slice6b-decode-literals/ (spec.md, notes.md). Fixture: slice6/decode/orders.beaml with the hand-built
RECORD SNAPSHOTS slice6/decode/stored*.jsonl.

Accept cases: the build with each snapshot, and runtime checks of the generated module. The runtime harness is
release-free: the module compiles with `elixirc --warnings-as-errors` beside stubs of ProbeSupport and OpenTelemetry; the
stub of `:otel_span.set_attribute/3` and of `ProbeSupport.Capture.write/2` keep their arguments in the process
dictionary. The live decode is `__beaml_result_payments_authorize/1`, the REPLAY RUN is `Replay.run/3` over the records
of a snapshot file. Reject cases assert the exact message (notes.md, S-decisions). Expected values come from the plan,
the decision log and notes.md, never from the new compiler.
Run: python3 -B experiments/0004-generated-replay/tests/slice6_decode_test.py [-k NAME]
"""
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_tree import EXPERIMENT  # noqa: E402
import slice6_failure_test as sf  # noqa: E402

DECODE = EXPERIMENT / "slice6" / "decode"
ORDERS = DECODE / "orders.beaml"
STORED = DECODE / "stored.jsonl"
RESOLVED = DECODE / "stored-resolved.jsonl"
FAIL = DECODE / "stored-fail.jsonl"
EMPTY = ["--stored", str(sf.EMPTY_STORED)]
b = sf.b

# Stubs for a release-free run (notes.md S8). Attributes and captured RESPONSE RECORDS go to the process dictionary.
STUBS = r'''
defmodule ProbeSupport do
  def span(_, _, _, _, f), do: f.()
  def event(_, _), do: :ok
  def config(_), do: nil
  def json(v), do: v
  def increment, do: :ok
  def beam_hash(_), do: ""
end
defmodule ProbeSupport.Capture do
  def write(_, record), do: Process.put(:capture, record)
end
defmodule OpenTelemetry.Tracer do
  def current_span_ctx, do: nil
end
defmodule OpenTelemetry.Span do
  def hex_trace_id(_), do: ""
  def hex_span_id(_), do: ""
end
defmodule :otel_span do
  def set_attribute(_, key, value), do: Process.put({:attr, key}, value)
end
defmodule :otel_propagator_text_map do
  def inject(carrier), do: carrier
end
'''
HELPERS = r'''
body = fn state -> :json.encode(%{"order_id" => "order-1", "state" => state}) |> IO.iodata_to_binary() end
live = fn state ->
  Process.delete({:attr, :unknown_fields})
  BeamlSpike.__beaml_attempt__(fn -> BeamlSpike.__beaml_result_payments_authorize(body.(state)) end)
end
records = fn file -> file |> File.read!() |> String.split("\n", trim: true) |> Enum.map(&:json.decode/1) end
replay = fn file, n ->
  Process.delete({:attr, :unknown_fields})
  BeamlSpike.Replay.run(%{"order_id" => "order-1"}, String.pad_leading(Integer.to_string(n, 16), 32, "0"), records.(file))
end
captured = fn state ->
  Process.delete(:capture)
  BeamlSpike.Replay.record(%{"order_id" => "order-1"}, 200, body.(state))
  Process.get(:capture)
end
attr = fn -> Process.get({:attr, :unknown_fields}) end
'''


def ok(state):
    return '{:ok, %%{"order_id" => "order-1", "state" => %s}}' % state


def v(name, args=""):
    return '{"PaymentState", "%s", [%s]}' % (name, args)


DECODE_ERROR = '{:error, %BeamlSpike.PaymentError{reason: "decode"}}'
LIVE_CASES = {
    # D6B-35: a literal gives its variant, another String the keep-value variant, a non-String the typed reject.
    "literal_ok_is_authorized": 'live.("ok") == %s and attr.() == nil' % ok(v("Authorized")),
    "literal_pending_is_pending": 'live.("pending") == %s' % ok(v("Pending")),
    "other_string_is_unknown": 'live.("refunded") == %s' % ok(v("Unknown", '"refunded"')),
    # D6B-37: a keep-value decode sets the span attribute unknown_fields (field names, no values).
    "unknown_sets_unknown_fields": 'live.("refunded") != nil and attr.() == ["state"]',
    "int_is_typed_reject_decode": 'live.(7) == %s' % DECODE_ERROR,
    "null_is_typed_reject_decode": 'live.(:null) == %s' % DECODE_ERROR,
    # notes.md S4 (open, Migrate): the RESPONSE RECORD keeps the names of the fields with a kept value.
    "record_keeps_unknown_fields": 'captured.("refunded").unknown_fields == ["state"]',
    "record_literal_has_no_unknown_fields": 'captured.("ok").unknown_fields == []',
}
REPLAY_CASES = {
    "replay_literal": 'replay.("%s", 1) == %s' % (RESOLVED, ok(v("Authorized"))),
    # DL-102: a REPLAY RUN of an old record uses the current mapping; the record was Unknown when it was written.
    "replay_resolved_uses_current_mapping": 'replay.("%s", 4) == %s' % (RESOLVED, ok(v("Pending"))),
    "replay_kept_value": ('replay.("%s", 3) == %s and attr.() == ["state"]'
                          % (RESOLVED, ok(v("Unknown", '"refunded"')))),
    "replay_not_a_string_is_decode": 'replay.("%s", 5) == %s' % (FAIL, DECODE_ERROR),
}

PS_LITERALS = 'enum PaymentState { Authorized = "ok"  Pending = "pending"  Unknown(String) }\n'
REST = ("type Order { order_id: String }\ntype PaymentError { reason: String }\n"
        'effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize")\n'
        "fn place order: Order -> Payment ! PaymentError = order |> payments.authorize\n")
NO_KEEP = ('enum PaymentState { Authorized = "ok"  Pending = "pending" }\n'
           "type Payment { order_id: String state: PaymentState }\n" + REST)
CHAIN = (PS_LITERALS + "type Payment v2 { order_id: String state: PaymentState }\n"
         "migrate Payment v1 -> v2 { rename status -> state }\n" + REST)
MARK = PS_LITERALS + "type Payment v3 { order_id: String state: PaymentState }\n" + REST
VERSIONED = ("error: effect payments.authorize: the enum field Payment.state cannot stand in a TYPE with a MIGRATE CHAIN "
             "or a VERSION MARK in slice 6b (D6B-39)\n"
             "  help: remove the MIGRATE CHAIN and the VERSION MARK of Payment, or make state a String field")


class Slice6Decode(unittest.TestCase):
    maxDiff = None
    setUp = sf.Slice6Failure.setUp
    compile = sf.Slice6Failure.compile
    assert_lines = sf.Slice6Failure.assert_lines

    def build(self, stored):
        code, stdout, stderr = self.compile(ORDERS, ["--stored", str(stored)])
        self.assertEqual((0, True), (code, "defmodule BeamlSpike do" in stdout),
                         "expected exit 0 and Elixir on stdout; stderr: " + stderr)
        return stdout, stderr

    def assert_rejected(self, source, message, extra=()):
        code, stdout, stderr = self.compile(source, list(extra))
        self.assertEqual((1, "", message), (code, stdout, stderr.strip()),
                         "expected exit 1, no stdout and the exact message")

    def run_runtime(self, cases):
        stdout, _ = self.build(STORED)
        out = self.work / "beam"
        out.mkdir()
        (out / "generated.ex").write_text(stdout)
        (out / "stubs.ex").write_text(STUBS)
        beam = subprocess.run(["elixirc", "--warnings-as-errors", "-o", str(out), str(out / "stubs.ex"),
                               str(out / "generated.ex")], capture_output=True, text=True)
        self.assertEqual(0, beam.returncode, "elixirc failed:\n" + beam.stdout + beam.stderr)
        listed = ",\n".join('  {"%s", fn -> %s end}' % item for item in cases.items())
        (out / "checks.exs").write_text(sf.RUNTIME_HEAD + HELPERS + "\ncases = [\n" + listed + "\n]\n" + sf.RUNTIME_TAIL)
        run = subprocess.run(["elixir", "-pa", str(out), str(out / "checks.exs")], capture_output=True, text=True)
        results = dict(line.rsplit(" ", 1) for line in run.stdout.splitlines() if line.endswith((" PASS", " FAIL")))
        for name in cases:
            with self.subTest(name):
                self.assertEqual("PASS", results.get(name), run.stdout + run.stderr)

    # Accept cases.

    def test_stored_values_all_resolve(self):
        # Every stored value maps to a variant; none was kept and is now resolved, so no report. Plan Elixir shape.
        stdout, stderr = self.build(STORED)
        self.assertEqual("", stderr)
        self.assert_lines(stdout, ["defp __beaml_literal_PaymentState(%s), do: {%s, %s, []}"
                                   % (b("ok"), b("PaymentState"), b("Authorized"))])

    def test_resolved_unknown_reports_the_count(self):
        # DL-103: a record kept as Unknown at write time that a literal maps now: a count, no block. notes.md S6.
        _, stderr = self.build(RESOLVED)
        self.assertEqual("note: TYPE Payment: 1 stored RESPONSE RECORD of operation payments.authorize kept a value "
                         "of field state that a literal of PaymentState maps now (DL-103)", stderr.strip())

    def test_runtime_live_decode(self):
        self.run_runtime(LIVE_CASES)

    def test_runtime_replay(self):
        self.run_runtime(REPLAY_CASES)

    # Reject cases.

    def test_stored_value_without_a_variant_blocks(self):
        # DL-102: counts, never values; the help line asks for a MIGRATE STEP. notes.md S5.
        self.assert_rejected(ORDERS, (
            "error: TYPE Payment: 2 stored RESPONSE RECORDS of operation payments.authorize have no variant of "
            "PaymentState for field state\n"
            "  record source: %s:2 (line 2)\n"
            "  help: declare the fate of these records in a MIGRATE STEP to a new TYPE VERSION of Payment (DL-102)"
        ) % FAIL, ["--stored", str(FAIL)])

    def test_output_enum_without_keep_value_variant(self):
        # D6B-36 (DL-065): an enum field in an EFFECT output needs a keep-value variant.
        self.assert_rejected(NO_KEEP, (
            "error: effect payments.authorize: the enum PaymentState of Payment.state has no keep-value variant "
            "(DL-065)\n  help: add the variant Unknown(String) to enum PaymentState"), EMPTY)

    def test_enum_output_field_with_a_chain(self):
        self.assert_rejected(CHAIN, VERSIONED, EMPTY)

    def test_enum_output_field_with_a_version_mark(self):
        self.assert_rejected(MARK, VERSIONED, EMPTY)


if __name__ == "__main__":
    unittest.main()

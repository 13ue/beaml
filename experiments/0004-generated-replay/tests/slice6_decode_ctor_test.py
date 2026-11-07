"""EXPERIMENT 0004 slice 6b step 8: decode of outside data through constructors (DL-084, DL-085, DL-099, DL-101, DL-102).

Plan step 8, D6B-48 to D6B-50; DL-101 lifts the interim reject D6B-19 for EFFECT output fields. Ledger:
workflow/2026-11-07/slice6b-decode-constructor/ (spec.md, notes.md). Fixture: slice6/decode-ctor/orders.beaml with the
hand-built RECORD SNAPSHOTS slice6/decode-ctor/stored*.jsonl.

The release-free runtime harness, the stubs and the shared forms (`unknown_fields`, the DL-102 block lines) come from
step 7 (tests/slice6_decode_test.py). Expected values come from the plan, the decision log and notes.md, never from the
new compiler. Reject cases assert the exact message.
Run: python3 -B experiments/0004-generated-replay/tests/slice6_decode_ctor_test.py [-k NAME]
"""
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_tree import EXPERIMENT  # noqa: E402
import slice6_failure_test as sf  # noqa: E402
import slice6_decode_test as sd  # noqa: E402

CTOR = EXPERIMENT / "slice6" / "decode-ctor"
ORDERS = CTOR / "orders.beaml"
STORED = CTOR / "stored.jsonl"
FAIL = CTOR / "stored-fail.jsonl"
NOMATCH = CTOR / "stored-nomatch.jsonl"
EMPTY = ["--stored", str(sf.EMPTY_STORED)]

HELPERS = r'''
eur = %{"value" => "12.50", "currency" => "EUR"}
st = fn status, reason -> %{"status" => status, "decline_reason" => reason} end
body = fn state, amount ->
  :json.encode(%{"order_id" => "order-1", "state" => state, "amount" => amount}) |> IO.iodata_to_binary()
end
live = fn state, amount ->
  Process.delete({:attr, :unknown_fields})
  Process.delete({:attr, :unknown_keys})
  BeamlSpike.__beaml_attempt__(fn -> BeamlSpike.__beaml_result_payments_authorize(body.(state, amount)) end)
end
records = fn file -> file |> File.read!() |> String.split("\n", trim: true) |> Enum.map(&:json.decode/1) end
replay = fn file, n ->
  BeamlSpike.Replay.run(%{"order_id" => "order-1"}, String.pad_leading(Integer.to_string(n, 16), 32, "0"), records.(file))
end
captured = fn state ->
  Process.delete(:capture)
  BeamlSpike.Replay.record(%{"order_id" => "order-1"}, 200, body.(state, eur))
  Process.get(:capture)
end
attr = fn key -> Process.get({:attr, key}) end
'''

EUR = '%{"value" => "12.50", "currency" => "EUR"}'


def ok(state, amount=EUR):
    return '{:ok, %%{"order_id" => "order-1", "state" => %s, "amount" => %s}}' % (state, amount)


def v(name, args=""):
    return '{"PaymentState", "%s", [%s]}' % (name, args)


def reject(reason):
    return '{:error, %%BeamlSpike.PaymentError{reason: "%s"}}' % reason


LIVE_CASES = {
    # D6B-48, DL-085: signature 1 matches when both keys are present with String values; first clause match wins.
    "two_keys_ok_is_authorized": ('live.(st.("ok", ""), eur) == %s and attr.(:unknown_fields) == nil'
                                  % ok(v("Authorized"))),
    "declined_via_pipe": 'live.(st.("declined", "card"), eur) == %s' % ok(v("Declined", '%{"text" => "card"}')),
    # DL-065, D6B-37 (step 7 form): the keep-value variant names the field in unknown_fields, never the value.
    "other_status_is_unknown": ('live.(st.("refunded", ""), eur) == %s and attr.(:unknown_fields) == ["state"]'
                                % ok(v("Unknown", '"refunded"'))),
    "record_keeps_unknown_fields": 'captured.(st.("refunded", "")).unknown_fields == ["state"]',
    # DL-099: a one-parameter signature reads a scalar field value directly.
    "scalar_uses_one_parameter_signature": 'live.("ok", eur) == %s' % ok(v("Authorized")),
    # D6B-48: no signature matches: a wrong TYPE, a missing key, a value that is neither an object nor a String.
    "wrong_type_matches_no_signature": 'live.(st.(7, ""), eur) == %s' % reject("decode"),
    "missing_key_matches_no_signature": 'live.(%%{"status" => "ok"}, eur) == %s' % reject("decode"),
    "int_matches_no_signature": 'live.(7, eur) == %s' % reject("decode"),
    # DL-101: the decode builds the inputs from the keys of the field value and calls the record constructor.
    "amount_constructor_accepts": 'live.("pending", eur) == %s' % ok(v("Pending")),
    # DL-101 open reason, notes.md S6 (proposal): a constructor failure is the typed reject `constructor`.
    "amount_constructor_failure_is_typed_reject": ('live.("ok", %%{"value" => "1", "currency" => ""}) == %s'
                                                   % reject("constructor")),
    "amount_missing_key_is_decode": 'live.("ok", %%{"value" => "1"}) == %s' % reject("decode"),
    # D6B-49: every parameter name of every signature is declared (code is a key name of signature 2).
    # notes.md S8 (proposal): a stray key inside a field value is FIELD.KEY.
    "stray_key_in_field_value": ('live.(Map.merge(st.("ok", ""), %%{"code" => "x", "extra" => "y"}), eur) == %s'
                                 ' and attr.(:unknown_keys) == ["state.extra"]' % ok(v("Authorized"))),
    "record_keeps_stray_key": ('captured.(Map.merge(st.("ok", ""), %{"extra" => "y"})).unknown_keys'
                               ' == ["state.extra"]'),
    # Slice 6b step 6a (D6B-54, DL-099): `value` takes the declared keys at every level; the stray key goes.
    "record_value_is_the_nested_projection": ('captured.(Map.merge(st.("ok", ""), %{"extra" => "y"})).value == '
                                              '%{"order_id" => "order-1", "state" => st.("ok", ""), "amount" => eur}'),
}
REPLAY_CASES = {
    "replay_declined": 'replay.("%s", 2) == %s' % (STORED, ok(v("Declined", '%{"text" => "card"}'))),
    "replay_scalar": 'replay.("%s", 3) == %s' % (STORED, ok(v("Pending"))),
}

# D6B-50 reject source: the last clause of signature 1 drops every input.
DROPS = ('type Order { order_id: String }\n'
         'enum PaymentState { Authorized  Pending  Unknown(String) }\n'
         'fn PaymentState status: String, decline_reason: String -> PaymentState\n'
         'fn PaymentState "ok", _ -> PaymentState = Authorized\n'
         'fn PaymentState _, _ -> PaymentState = Pending\n'
         'type Payment { order_id: String state: PaymentState }\n'
         'type PaymentError { reason: String }\n'
         'effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize")\n'
         'fn place order: Order -> Payment ! PaymentError = order |> payments.authorize\n')
# DL-085 between signatures (RED review objection 3): two object signatures share the key status.
SHARED = ('type Order { order_id: String }\n'
          'enum Pick { ByReason  ByCode  Unknown(String) }\n'
          'fn Pick status: String, decline_reason: String -> Pick\n'
          'fn Pick "ok", _ -> Pick = ByReason\n'
          'fn Pick other, _ -> Pick = Unknown(other)\n'
          'fn Pick status: String, code: String -> Pick\n'
          'fn Pick "ok", _ -> Pick = ByCode\n'
          'fn Pick other, _ -> Pick = Unknown(other)\n'
          'type Payment { order_id: String state: Pick }\n'
          'type PaymentError { reason: String }\n'
          'effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize")\n'
          'fn place order: Order -> Payment ! PaymentError = order |> payments.authorize\n')
SHARED_HELPERS = r'''
pick = fn state ->
  body = :json.encode(%{"order_id" => "order-1", "state" => state}) |> IO.iodata_to_binary()
  BeamlSpike.__beaml_attempt__(fn -> BeamlSpike.__beaml_result_payments_authorize(body) end)
end
'''
PICKED = '{:ok, %%{"order_id" => "order-1", "state" => {"Pick", "%s", []}}}'
SHARED_CASES = {
    # A value with the keys of both signatures: the first signature in source order wins (DL-085).
    "both_signatures_match_first_wins": ('pick.(%%{"status" => "ok", "decline_reason" => "", "code" => "x"}) == %s'
                                         % (PICKED % "ByReason")),
    # Signature 2 is reachable: its keys only.
    "second_signature_alone": 'pick.(%%{"status" => "ok", "code" => "x"}) == %s' % (PICKED % "ByCode"),
}
# D6B-40 (GREEN, notes.md G-text): an enum field in an EFFECT input TYPE, also nested. Today it compiles and
# :json.encode raises at call time.
INPUT_ENUM = ('type Order { order_id: String state: %s }\n'
              '%s'
              'type Payment { order_id: String }\n'
              'type PaymentError { reason: String }\n'
              'effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize")\n'
              'fn place order: Order -> Payment ! PaymentError = order |> payments.authorize\n')
LITERAL_ENUM = 'enum Kind { Card = "card"  Unknown(String) }\n'
CTOR_ENUM = ('type Meta { kind: Pick }\n'
             'enum Pick { ByCode  Unknown(String) }\n'
             'fn Pick code: String -> Pick\n'
             'fn Pick "x" -> Pick = ByCode\n'
             'fn Pick other -> Pick = Unknown(other)\n')


def input_enum_reject(place, enum):
    return ("error: effect payments.authorize: the enum field %s cannot stand in an EFFECT input in slice 6b (D6B-40)\n"
            "  help: send a String field, then map it to the enum %s after the EFFECT" % (place, enum))


HELP_MIGRATE = "  help: declare the fate of these records in a MIGRATE STEP to a new TYPE VERSION of Payment (DL-102)"


class Slice6DecodeCtor(unittest.TestCase):
    maxDiff = None
    setUp = sf.Slice6Failure.setUp
    compile = sf.Slice6Failure.compile
    assert_rejected = sd.Slice6Decode.assert_rejected

    def build(self, stored, source=ORDERS):
        # RED review objection 1: the step 8 fixture, not the step 7 ORDERS of slice6_decode_test.py.
        code, stdout, stderr = self.compile(source, ["--stored", str(stored)])
        self.assertEqual((0, True), (code, "defmodule BeamlSpike do" in stdout),
                         "expected exit 0 and Elixir on stdout; stderr: " + stderr)
        return stdout, stderr

    def run_runtime(self, cases, source=ORDERS, stored=STORED, helpers=HELPERS):
        stdout, _ = self.build(stored, source)
        out = self.work / "beam"
        out.mkdir()
        (out / "generated.ex").write_text(stdout)
        (out / "stubs.ex").write_text(sd.STUBS)
        beam = subprocess.run(["elixirc", "--warnings-as-errors", "-o", str(out), str(out / "stubs.ex"),
                               str(out / "generated.ex")], capture_output=True, text=True)
        self.assertEqual(0, beam.returncode, "elixirc failed:\n" + beam.stdout + beam.stderr)
        listed = ",\n".join('  {"%s", fn -> %s end}' % item for item in cases.items())
        (out / "checks.exs").write_text(sf.RUNTIME_HEAD + helpers + "\ncases = [\n" + listed + "\n]\n" + sf.RUNTIME_TAIL)
        run = subprocess.run(["elixir", "-pa", str(out), str(out / "checks.exs")], capture_output=True, text=True)
        results = dict(line.rsplit(" ", 1) for line in run.stdout.splitlines() if line.endswith((" PASS", " FAIL")))
        for name in cases:
            with self.subTest(name):
                self.assertEqual("PASS", results.get(name), run.stdout + run.stderr)

    # Accept cases.

    def test_stored_records_pass_the_constructors(self):
        # DL-102: every stored record passes the constructors. The kept value stays Unknown: no DL-103 note.
        _, stderr = self.build(STORED)
        self.assertEqual("", stderr)

    def test_runtime_live_decode(self):
        self.run_runtime(LIVE_CASES)

    def test_runtime_replay(self):
        self.run_runtime(REPLAY_CASES)

    def test_runtime_first_signature_wins(self):
        self.run_runtime(SHARED_CASES, SHARED, sf.EMPTY_STORED, SHARED_HELPERS)

    # Reject cases.

    def test_stored_record_fails_the_record_constructor(self):
        # DL-102: counts and the failure TYPE as the reason, never values. notes.md S9.
        self.assert_rejected(ORDERS, (
            "error: TYPE Payment: 2 stored RESPONSE RECORDS of operation payments.authorize fail the constructor of "
            "Amount for field amount with NoCurrency\n"
            "  record source: %s:2 (line 2)\n" + HELP_MIGRATE) % FAIL, ["--stored", str(FAIL)])

    def test_stored_record_matches_no_signature(self):
        # DL-102 over an enum constructor: no signature matches. notes.md S9.
        self.assert_rejected(ORDERS, (
            "error: TYPE Payment: 1 stored RESPONSE RECORD of operation payments.authorize matches no signature of "
            "PaymentState for field state\n"
            "  record source: %s:2 (line 2)\n" + HELP_MIGRATE) % NOMATCH, ["--stored", str(NOMATCH)])

    def test_last_clause_does_not_keep_the_value(self):
        # D6B-50 (DL-065). notes.md S10.
        self.assert_rejected(DROPS, (
            "error: effect payments.authorize: the last clause of signature 1 of constructor PaymentState (field "
            "Payment.state) keeps no String input in the keep-value variant Unknown (DL-065, D6B-50)\n"
            "  help: bind every input in the last clause and put one String input into Unknown, for example "
            "fn PaymentState other, _ -> PaymentState = Unknown(other)"), EMPTY)


    def test_enum_field_in_effect_input_is_rejected(self):
        # D6B-40: an ENUM LITERAL field and a constructor enum in a nested input TYPE.
        with self.subTest("literal"):
            self.assert_rejected(INPUT_ENUM % ("Kind", LITERAL_ENUM), input_enum_reject("Order.state", "Kind"), EMPTY)
        with self.subTest("constructor, nested"):
            self.assert_rejected(INPUT_ENUM % ("Meta", CTOR_ENUM), input_enum_reject("Meta.kind", "Pick"), EMPTY)

if __name__ == "__main__":
    unittest.main()

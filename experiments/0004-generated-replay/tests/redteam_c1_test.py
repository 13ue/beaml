"""EXPERIMENT 0004, RED TEAM 01 repair C1: an enum constructor with a failure TYPE under --stored.

Finding: workflow/2026-11-07/red-team-01/rt-correctness.md C1 (and R2-4). Contract: workflow/2026-11-07/red-team-01-repairs/
spec.md, decision D6B-187 (the DRIVER accepts the enum success tuple {"T", "Variant", [payload]} as `ok`).
The source is the red-team repro c2/en.beaml. Records come from one template; the digest comes from Python
(`stored_types_test.value_sha256`), never from the compiler. Expected text is the DL-102 block of step 8 (sdc.HELP_MIGRATE).
Run: python3 -B experiments/0004-generated-replay/tests/redteam_c1_test.py [-k NAME]
"""
import json
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import slice6_decode_ctor_test as sdc  # noqa: E402
import slice6_stored_elixir_test as ses  # noqa: E402
import stored_types_test as st  # noqa: E402

SOURCE = """type Order { order_id: String }
type Bad {}
enum PaymentState { Authorized  Unknown(String) }
fn PaymentState code: String -> PaymentState ! Bad
fn PaymentState "" -> PaymentState ! Bad = Bad {}
fn PaymentState "ok" -> PaymentState ! Bad = Authorized
fn PaymentState other -> PaymentState ! Bad = Unknown(other)
type Payment { order_id: String state: PaymentState }
type PaymentError { reason: String }
effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize")
fn place order: Order -> Payment ! PaymentError =
  order
  |> payments.authorize
"""
TEMPLATE = {"status": 200, "version": 2, "request": {"order_id": "order-1"}, "operation": "payments.authorize",
            "trace_id": "00000000000000000000000000000001", "unknown_keys": [], "artifact_id": "0" * 64, "attempt": 1,
            "client_span_id": "0000000000000001",
            "type": {"name": "Payment", "version": 1, "fields": [["order_id", "String"], ["state", "PaymentState"]],
                     "fingerprint": "de5ce8775a633272bc181cba11dda0b5b14609068977c0444f6eef5e61650c36"},
            "unknown_fields": [], "redacted": []}
FAILS = ("error: TYPE Payment: 1 stored RESPONSE RECORD of operation payments.authorize fails the constructor of "
         "PaymentState for field state with Bad\n"
         "  record source: %s:%d (line %d)\n" + sdc.HELP_MIGRATE)


def record(state):
    value = {"order_id": "order-1", "state": state}
    return dict(TEMPLATE, value=value, value_sha256=st.value_sha256(value))


class RedTeamC1(unittest.TestCase):
    maxDiff = None
    setUp = ses.Slice6StoredElixir.setUp
    compile = ses.Slice6StoredElixir.compile
    build = ses.Slice6StoredElixir.build
    events = ses.Slice6StoredElixir.events
    last_event = ses.Slice6StoredElixir.last_event

    def stored(self, *states):
        path = self.work / "stored.jsonl"
        path.write_text("".join(json.dumps(record(s)) + "\n" for s in states))
        return path

    def source(self):
        path = self.work / "src" / "en.beaml"
        path.parent.mkdir(exist_ok=True)
        path.write_text(SOURCE)
        return path

    # RED: a valid record passes the Elixir pass (D6B-187).

    def test_c1a_valid_record_builds(self):
        # Observed by the red team at 7ee5c89e and here at acf12d75: exit 1 with the run error.
        _, stderr = self.build(self.stored("ok"), self.source())
        self.assertEqual("", stderr)

    def test_c1b_valid_record_gives_an_ok_event(self):
        # D6B-107: one stored-elixir event, result ok, one call per record.
        self.build(self.stored("ok"), self.source())
        event = self.last_event()
        self.assertEqual(("ok", 1), (event.get("result"), event.get("calls")), event)

    def test_c1c_payload_variant_builds(self):
        # The success tuple has a payload: {"PaymentState", "Unknown", ["refunded"]}.
        _, stderr = self.build(self.stored("ok", "refunded"), self.source())
        self.assertEqual("", stderr)

    def test_c1d_mixed_records_give_the_dl102_block(self):
        # Today the run error hides the DL-102 block. Count 1, first failing record on line 2.
        stored = self.stored("ok", "", "refunded")
        code, stdout, stderr = self.compile(self.source(), ["--stored", str(stored)])
        self.assertEqual((1, "", FAILS % (stored, 2, 2)), (code, stdout, stderr.strip()))

    # Guards: pass before and after.

    def test_c1e_failing_record_alone_gives_the_dl102_block(self):
        stored = self.stored("")
        code, stdout, stderr = self.compile(self.source(), ["--stored", str(stored)])
        self.assertEqual((1, "", FAILS % (stored, 1, 1)), (code, stdout, stderr.strip()))

    def test_c1f_enum_success_is_a_tuple_not_a_struct(self):
        # Pins the value that the DRIVER must accept as ok (D6B-187): the generated constructor returns a tuple.
        code, module, stderr = self.compile(self.source(), ["--stored", str(ses.sf.EMPTY_STORED)])
        self.assertEqual(0, code, stderr)
        probe = ('Code.compile_string(IO.binread(:stdio, :eof))\n'
                 'IO.puts(inspect([BeamlSpike.new_PaymentState_1("ok"), BeamlSpike.new_PaymentState_1("refunded")]))')
        done = subprocess.run(["elixir", "-e", probe], input=module, capture_output=True, text=True, timeout=90,
                              cwd=self.work / "cwd")
        self.assertEqual('[ok: {"PaymentState", "Authorized", []}, ok: {"PaymentState", "Unknown", ["refunded"]}]',
                         done.stdout.strip().splitlines()[-1] if done.stdout.strip() else done.stderr)


if __name__ == "__main__":
    unittest.main()

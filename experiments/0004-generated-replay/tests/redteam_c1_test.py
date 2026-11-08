"""EXPERIMENT 0004, RED TEAM 01 repair C1: an enum constructor with a failure TYPE under --stored.

Finding: workflow/2026-11-07/red-team-01/rt-correctness.md C1 (and R2-4). Contract: workflow/2026-11-07/red-team-01-repairs/
spec.md, decision D6B-187 (the DRIVER accepts the enum success tuple {"T", "Variant", [payload]} as `ok`).
The source is the red-team repro c2/en.beaml. Records come from one template; the digest comes from Python
(`stored_types_test.value_sha256`), never from the compiler. Expected text is the DL-102 block of step 8 (sdc.HELP_MIGRATE).
Run: python3 -B experiments/0004-generated-replay/tests/redteam_c1_test.py [-k NAME]
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import slice6_decode_ctor_test as sdc  # noqa: E402
import slice6_stored_elixir_test as ses  # noqa: E402
import stored_types_test as st  # noqa: E402
from arm_tree import COMPILER_PATH, REPO  # noqa: E402

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
TEMPLATE = {"status": 200, "version": 3, "request": {"order_id": "order-1"}, "operation": "payments.authorize",
            "trace_id": "00000000000000000000000000000001", "unknown_keys": [], "artifact_id": "0" * 64, "attempt": 1,
            "span_id": "0000000000000001", "outcome": "accepted", "reason": None,
            "type": {"name": "Payment", "version": 1, "fields": [["order_id", "String"], ["state", "PaymentState"]],
                     "fingerprint": "de5ce8775a633272bc181cba11dda0b5b14609068977c0444f6eef5e61650c36"},
            "unknown_fields": [], "redacted": []}
FAILS = ("error: TYPE Payment: 1 stored RESPONSE RECORD of operation payments.authorize fails the constructor of "
         "PaymentState for field state with Bad\n"
         "  record source: %s:%d (line %d)\n" + sdc.HELP_ENUM_FAIL)


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


# RED review O1 (D6B-122 with D6B-187): the DRIVER text itself, fed a hand-made module. One call per run, because one
# raise ends the whole run. Success: exit 0 and exactly "ok". Wrong shape: non-zero exit and no "ok" line; the COMPILER
# maps a non-zero exit to the run error (D6B-121, U1, E8 cover that mapping).
DRIVER_MODULE = """defmodule BeamlSpike.Amount do defstruct [:v] end
defmodule BeamlSpike.Other do defstruct [:v] end
defmodule BeamlSpike do
  def struct_ok(_), do: {:ok, %BeamlSpike.Amount{}}
  def enum_ok(_), do: {:ok, {"PaymentState", "Authorized", []}}
  def enum_payload(_), do: {:ok, {"PaymentState", "Unknown", ["x"]}}
  def other_struct(_), do: {:ok, %BeamlSpike.Other{}}
  def bare_map(_), do: {:ok, %{}}
  def two_tuple(_), do: {:ok, {"PaymentState", "Authorized"}}
  def other_enum(_), do: {:ok, {"Other", "Authorized", []}}
  def atom_variant(_), do: {:ok, {"PaymentState", :Authorized, []}}
  def payload_not_list(_), do: {:ok, {"PaymentState", "Authorized", nil}}
  def bare_value(_), do: {"PaymentState", "Authorized", []}
end
"""
PASSES = {"struct_ok": "Amount", "enum_ok": "PaymentState", "enum_payload": "PaymentState"}
RAISES = {"other_struct": "Amount", "bare_map": "Amount", "two_tuple": "PaymentState", "other_enum": "PaymentState",
          "atom_variant": "PaymentState", "payload_not_list": "PaymentState", "bare_value": "PaymentState"}


def driver_text():
    """The DRIVER const of the main.rs that belongs to the binary under test (BEAML_SPIKE scratch tree, else the repo)."""
    spike = os.environ.get("BEAML_SPIKE")
    main = Path(spike).parents[2] / "src/main.rs" if spike else REPO / COMPILER_PATH / "src/main.rs"
    found = re.search(r'^const DRIVER: &str = r#"(.*?)"#;$', main.read_text(), re.S | re.M)
    return found.group(1) if found else None


class RedTeamC1Driver(unittest.TestCase):
    maxDiff = None

    def run_driver(self, fun, type_name):
        driver = driver_text()
        self.assertIsNotNone(driver, "no DRIVER const in main.rs")
        # D6B-204 (slice 6e): the DRIVER reads the module name from its input.
        stdin = json.dumps({"module": DRIVER_MODULE, "name": "BeamlSpike", "calls": [[fun, type_name, ["x"]]]})
        with tempfile.TemporaryDirectory(prefix="beaml-0004-c1drv-") as cwd:
            done = subprocess.run(["elixir", "-e", driver], input=stdin, capture_output=True, text=True,
                                  timeout=90, cwd=cwd)
        return done.returncode, done.stdout.split()

    def test_c1g_driver_accepts_success_shapes(self):
        # RED for enum_ok and enum_payload (D6B-187); struct_ok is a guard.
        for fun, type_name in PASSES.items():
            with self.subTest(fun):
                self.assertEqual((0, ["ok"]), self.run_driver(fun, type_name))

    def test_c1h_driver_raises_on_wrong_success_shapes(self):
        # Guards (D6B-122): each wrong shape raises today and must still raise after D6B-187.
        for fun, type_name in RAISES.items():
            with self.subTest(fun):
                code, lines = self.run_driver(fun, type_name)
                self.assertEqual((True, False), (code != 0, "ok" in lines), (code, lines))


if __name__ == "__main__":
    unittest.main()

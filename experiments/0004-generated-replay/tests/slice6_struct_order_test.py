"""EXPERIMENT 0004 slice 6b mini-step struct-order: a step 2 regression (commit c3e97430, D6B-07).

In a module with an EFFECT, the struct module of a record failure TYPE of a pure fn must come before its first use.
Ledger: workflow/2026-11-07/slice6b-struct-order/ (spec.md, notes.md). Probe: step 8 RED review, objection 2.
Guards: the EFFECT fixture outputs and the payments output stay byte-equal (the step 5 guard constants).
Run: python3 -B experiments/0004-generated-replay/tests/slice6_struct_order_test.py [-k NAME]
"""
import hashlib
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_tree import EXPERIMENT  # noqa: E402
import slice6_failure_test as sf  # noqa: E402
import slice6_decode_test as sd  # noqa: E402
import slice6_pipe_test as sp  # noqa: E402

# RED review step 8, objection 2: an EFFECT and a pure fn with a `! Bad` record failure.
PROBE = ('type Order { order_id: String }\n'
         'type Bad {}\n'
         'fn check "" -> String ! Bad = Bad {}\n'
         'fn check x: String -> String ! Bad = x\n'
         'type Payment { order_id: String }\n'
         'type PaymentError { reason: String }\n'
         'effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize")\n'
         'fn place order: Order -> Payment ! PaymentError = order |> payments.authorize\n')
EMPTY = ["--stored", str(sf.EMPTY_STORED)]


class Slice6StructOrder(unittest.TestCase):
    maxDiff = None
    setUp = sf.Slice6Failure.setUp
    compile = sf.Slice6Failure.compile

    def test_effect_module_with_pure_record_failure_compiles(self):
        # D6B-07: struct modules come before any use. Today: BeamlSpike.Bad.__struct__/1 is undefined.
        code, stdout, stderr = self.compile(PROBE, EMPTY)
        self.assertEqual((0, True), (code, "defmodule BeamlSpike do" in stdout), stderr)
        out = self.work / "beam"
        out.mkdir()
        (out / "generated.ex").write_text(stdout)
        (out / "stubs.ex").write_text(sd.STUBS)
        beam = subprocess.run(["elixirc", "--warnings-as-errors", "-o", str(out), str(out / "stubs.ex"),
                               str(out / "generated.ex")], capture_output=True, text=True)
        self.assertEqual(0, beam.returncode, "elixirc failed:\n" + beam.stdout + beam.stderr)

    # Guards: pass today.

    def test_effect_fixture_outputs_stay_byte_equal(self):
        for relative, digest in sp.EFFECT_OUTPUTS.items():
            with self.subTest(relative):
                code, stdout, stderr = self.compile(EXPERIMENT / relative, EMPTY)
                self.assertEqual((0, digest), (code, hashlib.sha256(stdout.encode()).hexdigest()), stderr)
        with self.subTest("payments.beaml"):
            code, stdout, stderr = self.compile(sp.PAYMENTS)
            self.assertEqual((0, sp.PAYMENTS_SNAPSHOT.read_text()), (code, stdout), stderr)


if __name__ == "__main__":
    unittest.main()

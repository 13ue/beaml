"""EXPERIMENT 0004 slice 6b step 13: the --stored check runs the generated Elixir constructor (DL-121, DL-122, DL-124).

Plan: workflow/2026-11-07/slice6b-stored-elixir/plan.md (contract, and the section "Plan repair", which holds where the
two differ), decisions D6B-102 to D6B-111 and D6B-119 to D6B-126. Fixtures: slice6/stored-elixir/ (D6B-110); the
DL-122 cases use slice6/decode/ with an inline text replace. Expected text comes from the plan and the decision log,
never from the new compiler. Reject cases assert the exact message. U1 (Rust unit test of the line parser) lives in
experiments/0001-syntax-to-beam/src/main.rs and belongs to GREEN (notes.md "Left for GREEN").
Run: python3 -B experiments/0004-generated-replay/tests/slice6_stored_elixir_test.py [-k NAME]
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_tree import EXPERIMENT  # noqa: E402
import slice6_decode_ctor_test as sdc  # noqa: E402
import slice6_decode_test as sd  # noqa: E402
import slice6_failure_test as sf  # noqa: E402
import stored_types_test as st  # noqa: E402

HERE = EXPERIMENT / "slice6" / "stored-elixir"
PIPE = HERE / "pipe.beaml"
NESTED = HERE / "nested.beaml"
REC = HERE / "rec.beaml"
ORDER = HERE / "order.beaml"
PIPE_FAIL = HERE / "pipe-fail.jsonl"
NESTED_FAIL = HERE / "nested-fail.jsonl"
REC_LOOP = HERE / "rec-loop.jsonl"
ORDER_STORED = HERE / "order.jsonl"
CTOR_STORED = sdc.STORED  # four records, each amount {"value": "12.50", "currency": "EUR"}
NOMATCH = sdc.NOMATCH

# Plan E1: the step 8 DL-102 block text, count 1, first record line.
CTOR_FAILS = ("error: TYPE Payment: 1 stored RESPONSE RECORD of operation payments.authorize fails the constructor of "
              "Amount for field amount with NoCurrency\n"
              "  record source: %s:1 (line 1)\n" + sdc.HELP_MIGRATE)
# Contract 5 (D6B-106): no pass without Elixir.
NO_ELIXIR = ("error: the --stored check runs the constructors over the stored values in Elixir (DL-121): elixir is not "
             "on PATH\n"
             "  help: install Elixir 1.18 with Erlang/OTP 27 and put elixir on PATH")
# Contract 5, repaired (D6B-119, D6B-121).
RUN_ERROR = ("error: the --stored check: the Elixir run of the generated constructors failed (%s)\n"
             "  help: compile the generated module with elixirc to see the error")
# Contract 2, repaired (D6B-124, DL-124): never the stored String.
LOST_LITERAL = ("error: TYPE Payment v1: 1 stored RESPONSE RECORD of operation payments.authorize has a value of field "
                "state that is no ENUM LITERAL of PaymentState now (DL-122)\n"
                "  record source: %s:2 (line 2)\n"
                "  help: declare the fate in a MIGRATE STEP (DL-122); slice 6b has no MIGRATE STEP form for an enum field "
                "(D6B-39), so restore the removed or changed ENUM LITERAL of PaymentState") % sd.STORED
RESOLVED_NOTE = ("note: TYPE Payment: 1 stored RESPONSE RECORD of operation payments.authorize kept a value of field "
                 "state that a literal of PaymentState maps now (DL-103)")
LITERAL = 'Pending = "pending"  '
EVENT_KEYS = {"ts", "source", "action", "target", "result", "ms", "calls"}

# E9 part b: the runtime decode (`__beaml_decode_T` of Payment through the live EFFECT result) of the two order.jsonl maps.
ORDER_CASES = {
    "signature_1_does_not_match_signature_2_fails": ('live.("ok", %%{"value" => "", "currency" => "EUR"}) == %s'
                                                     % sdc.reject("constructor")),
    "signature_1_matches_first": ('live.("ok", %%{"value" => "", "note" => "n", "currency" => "EUR"}) == %s'
                                  % sdc.ok(sdc.v("Authorized"), '%BeamlSpike.Amount{value: "", currency: "EUR"}')),
}


class Slice6StoredElixir(unittest.TestCase):
    maxDiff = None
    setUp = sf.Slice6Failure.setUp
    assert_rejected = sd.Slice6Decode.assert_rejected
    run_runtime = sdc.Slice6DecodeCtor.run_runtime

    def compile(self, source, extra=(), env=None):
        """sf.Slice6Failure.compile with an optional environment; also the same event checks."""
        if not isinstance(source, Path):
            path = self.work / "src" / "case.beaml"
            path.parent.mkdir(exist_ok=True)
            path.write_text(source)
            source = path
        binary = st.compiler()
        result = subprocess.run([binary, str(source), *extra], cwd=self.work / "cwd", capture_output=True, text=True,
                                env=env, timeout=90)
        log = self.work / "cwd" / ".beaml" / "actions.jsonl"
        if log.is_file():
            text = log.read_text()
            self.assertNotIn(str(source.parent), text, "action events must not record the source path")
            self.assertNotIn("fn ", text, "action events must not record source text")
        return result.returncode, result.stdout, result.stderr

    def build(self, stored, source=PIPE):
        code, stdout, stderr = self.compile(source, ["--stored", str(stored)])
        self.assertEqual((0, True), (code, "defmodule BeamlSpike do" in stdout),
                         "expected exit 0 and Elixir on stdout; stderr: " + stderr)
        return stdout, stderr

    def no_path(self):
        """D6B-126: an empty scratch directory as PATH holds no elixir on any host."""
        empty = self.work / "empty-path"
        empty.mkdir(exist_ok=True)
        return dict(os.environ, PATH=str(empty))

    def events(self):
        log = self.work / "cwd" / ".beaml" / "actions.jsonl"
        lines = log.read_text().splitlines() if log.is_file() else []
        return [e for e in map(json.loads, lines) if e.get("action") == "stored-elixir"]

    def last_event(self):
        events = self.events()
        self.assertTrue(events, "expected a stored-elixir event in .beaml/actions.jsonl")
        return events[-1]

    # RED: the Elixir pass decides (DL-121, contract 3 and 4).

    def test_e1_failure_in_a_pipe_step_blocks(self):
        # Review probe 6 (P11): the static body TYPE of the clause is Amount; the pipe step cur fails on "".
        self.assert_rejected(PIPE, CTOR_FAILS % PIPE_FAIL, ["--stored", str(PIPE_FAIL)])

    def test_e2_failure_in_a_nested_constructor_blocks(self):
        # The failure comes only from the nested constructor step Code on currency "".
        self.assert_rejected(NESTED, CTOR_FAILS % NESTED_FAIL, ["--stored", str(NESTED_FAIL)])

    def test_e3_passing_records_build(self):
        # Guard: passes before and after. A GREEN that blocks every record or forwards Elixir warnings fails here.
        _, stderr = self.build(CTOR_STORED)
        self.assertEqual("", stderr)

    def test_e3_passing_records_give_an_ok_event(self):
        # D6B-107: one stored-elixir event per Elixir run.
        self.build(CTOR_STORED)
        self.assertEqual("ok", self.last_event().get("result"))

    def test_e4_no_elixir_on_path_blocks(self):
        # D6B-106 (DL-121): no silent pass without the toolchain. Contract 7: result error, ms 0.
        code, stdout, stderr = self.compile(PIPE, ["--stored", str(PIPE_FAIL)], self.no_path())
        self.assertEqual((1, "", NO_ELIXIR), (code, stdout, stderr.strip()),
                         "expected exit 1, no stdout and the exact message")
        event = self.last_event()
        self.assertEqual(("error", 0), (event.get("result"), event.get("ms")))

    def test_e5_event_has_time_and_count_only(self):
        # D6B-107: Int ms, one Amount call per record of stored.jsonl, no other key. RED review O2: a real run
        # takes time, so ms > 0.
        self.build(CTOR_STORED)
        event = self.last_event()
        self.assertEqual((True, True, 4, set()),
                         (isinstance(event.get("ms"), int), event.get("ms", -1) > 0, event.get("calls"),
                          set(event) - EVENT_KEYS), event)

    def test_e6_static_error_needs_no_elixir(self):
        # Guard (D6B-105): the static pass ends the check before Elixir starts, also without elixir on PATH.
        code, stdout, stderr = self.compile(PIPE, ["--stored", str(NOMATCH)], self.no_path())
        self.assertEqual((1, "", (
            "error: TYPE Payment: 1 stored RESPONSE RECORD of operation payments.authorize matches no signature of "
            "PaymentState for field state\n"
            "  record source: %s:2 (line 2)\n" + sdc.HELP_MIGRATE) % NOMATCH), (code, stdout, stderr.strip()))
        self.assertEqual([], self.events())

    def test_e7_no_stored_value_in_output(self):
        # Guard (DL-032, D6B-106, D6B-124): stderr and events hold no record value and no trace_id.
        for source, stored in ((PIPE, PIPE_FAIL), (NESTED, NESTED_FAIL)):
            with self.subTest(stored.name):
                _, stdout, stderr = self.compile(source, ["--stored", str(stored)])
                log = self.work / "cwd" / ".beaml" / "actions.jsonl"
                events = log.read_text() if log.is_file() else ""
                trace_id = json.loads(stored.read_text())["trace_id"]
                for text in (stderr, events):
                    self.assertEqual([], [w for w in ("EUR", trace_id) if w in text], text)
        for name, source in (("removed", sd.ORDERS.read_text().replace(LITERAL, "")),
                             ("changed", sd.ORDERS.read_text().replace(LITERAL, 'Pending = "wait"  '))):
            with self.subTest(name):
                _, _, stderr = self.compile(source, ["--stored", str(sd.STORED)])
                self.assertEqual([], [w for w in ("pending", "wait") if w in stderr], stderr)

    def test_e8_endless_constructor_hits_the_time_limit(self):
        # D6B-119 (plan check O1): the run error, inside the limit plus a margin; no driver process stays.
        env = dict(os.environ, BEAML_STORED_ELIXIR_LIMIT_S="2")
        st.compiler()  # build outside the measured time
        # RED review O1: the marker is in the args of the running child, so the no-leftover check below sees it.
        during = []
        probe = threading.Timer(1, lambda: during.append(
            subprocess.run(["pgrep", "-f", "beaml-stored-check"], capture_output=True).returncode))
        start = time.monotonic()
        probe.start()
        code, stdout, stderr = self.compile(REC, ["--stored", str(REC_LOOP)], env)
        wall = time.monotonic() - start
        probe.join()
        self.assertEqual([0], during, "pgrep must find the driver while it runs")
        self.assertEqual((1, "", RUN_ERROR % "time limit 2 s"), (code, stdout, stderr.strip()),
                         "expected exit 1, no stdout and the exact message")
        self.assertLess(wall, 12)
        self.assertEqual("error", self.last_event().get("result"))
        time.sleep(1)
        left = subprocess.run(["pgrep", "-f", "beaml-stored-check"], capture_output=True, text=True)
        self.assertEqual(1, left.returncode, "a driver process still runs: " + left.stdout)

    def test_e9a_check_follows_the_signature_order(self):
        # D6B-125: line 1 matches only signature 2 (fails); line 2 matches signature 1 first (no failure TYPE).
        self.assert_rejected(ORDER, CTOR_FAILS % ORDER_STORED, ["--stored", str(ORDER_STORED)])

    def test_e9b_runtime_decode_follows_the_signature_order(self):
        # Guard: the generated cond of __beaml_from_T, which the check must mirror.
        self.run_runtime(ORDER_CASES, ORDER, sf.EMPTY_STORED, sdc.HELPERS)

    # DL-122 as narrowed by DL-124: a lost ENUM LITERAL blocks in the static pass (contract 2).

    def test_l1_removed_literal_blocks(self):
        self.assert_rejected(sd.ORDERS.read_text().replace(LITERAL, ""), LOST_LITERAL, ["--stored", str(sd.STORED)])

    def test_l1b_changed_literal_blocks(self):
        self.assert_rejected(sd.ORDERS.read_text().replace(LITERAL, 'Pending = "wait"  '), LOST_LITERAL,
                             ["--stored", str(sd.STORED)])

    def test_l2_current_literal_and_kept_value_build(self):
        # Guard: line 3 ("refunded", kept in unknown_fields) does not block. RED review O3: no constructor with a
        # failure TYPE gives zero calls, so Elixir does not start: no elixir on PATH, no event.
        code, stdout, stderr = self.compile(sd.ORDERS, ["--stored", str(sd.STORED)], self.no_path())
        self.assertEqual((0, True, ""), (code, "defmodule BeamlSpike do" in stdout, stderr))
        self.assertEqual([], self.events())

    def test_l3_resolved_note_stays(self):
        # Guard: the DL-103 note, no block.
        _, stderr = self.build(sd.RESOLVED, sd.ORDERS)
        self.assertEqual(RESOLVED_NOTE, stderr.strip())


if __name__ == "__main__":
    unittest.main()

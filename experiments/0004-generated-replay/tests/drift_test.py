"""EXPERIMENT 0004 slice 1 case (f): DRIFT runs only against the frozen LIB and records outcome classes.

Slice 6b step 6a (DL-110, DL-118, D6B-96): DRIFT has GEN rows only. The repair check is the GEN replay
of the repaired tree, not the 0003 copy `replay_run_test.py`.

DL-135 (M7 option A, D6B-189): the GEN classes are pinned (PIN). The DRIFT status is pass only for the pin,
a verified freeze and repaired_all true. A wanted class change moves PIN and run.DRIFT_PIN together.
Run: python3 -B experiments/0004-generated-replay/tests/drift_test.py
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_tree import ARMS, EXPERIMENT, HTTP_PATH, PAYMENTS_BEAML, REPLAY_PATH, REPO  # noqa: E402

DERIVATIVES = ("R", "N", "Q")
ARMS_NAMES = ("gen",)  # D6B-96: the LIB arm leaves DRIFT (DL-118)
OBSERVATIONS = ("build", "new_live", "pre_change")
# README "(f) DRIFT": outcome classes.
CLASSES = {"compile_error", "typed_reject", "correct_accept", "false_reject", "wrong_accept", "untyped_crash"}
LIB_MODULES = ("ReplayLib", "OrdersApi.ReplayDescriptor")
ACCEPT = {"correct_accept", "wrong_accept"}
REJECT = {"typed_reject", "false_reject"}
RESULTS_ROOT = EXPERIMENT / "results"
# DL-135, D6B-189: expected (build, new_live, pre_change) of the GEN row; 58 of 61 retained runs.
PIN = {"R": ("correct_accept", "false_reject", "typed_reject"),
       "N": ("correct_accept", "false_reject", "typed_reject"),
       "Q": ("correct_accept", "typed_reject", "typed_reject")}
# Review round 2, evidence per row of `run.py drift` (last stdout line {"run": <new dir in results/>, "drift": ...}):
#   row["evidence"] = {"build_output": <file>, "build_exit_code": <int>,
#                      "new_live_report": <live observed.json: {"reply": [code, body], ...}>,
#                      "pre_change_replay_report": <eval report.json: {"result": {"ok"|"error"|"raised": ...}}>}
# All files lie inside the run dir. With a failed build, both report paths may be absent.
# D6B-96 (slice 6b step 6a, DL-118), the repair evidence of a GEN row whose build passed:
#   row["repaired"] = {"exit_code": <int, eval exit>, "argv": <argv of the replay command>,
#                      "record": <RESPONSE RECORD (version 2) of one live call in the repaired tree>,
#                      "report": <eval report.json of the GEN runner over that record>}
#   The command is the eval of the Orders release of the repaired tree. No command of the row runs the
#   0003 copy replay_run_test.py. summary["repaired_all"] is true. drift, baseline and sites have no "lib".
#   RV6A-1 (option A): record["request"] has the fields of the drifted payments TYPE Order, record status
#   is 200, report result is {"ok": ...} and report host_validation is "ok", for each of R, N and Q.
REPLAY_0003_TEST = REPLAY_PATH + "/tests/replay_run_test.py"
ORDERS_RELEASE = HTTP_PATH + "/_build/prod/rel/orders/bin/orders"


def lib_hashes():
    found = {}
    root = ARMS / "lib" / "overlay"
    for path in sorted(root.rglob("*.ex")) if root.is_dir() else []:
        for name in LIB_MODULES:
            if ("defmodule %s do" % name) in path.read_text():
                found[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return found


class DriftFixtures(unittest.TestCase):
    """Guard, not RED: a derivative changes only BEAML declarations; the flow `place` stays."""

    def test_f_drift_fixtures_change_only_beaml_declarations(self):
        bases = {"orders.beaml": ARMS / "gen/orders.beaml", "payments.beaml": REPO / PAYMENTS_BEAML}
        for derivative in DERIVATIVES:
            for name, base in bases.items():
                old = base.read_text().splitlines()
                new = (EXPERIMENT / "drift" / derivative / name).read_text().splitlines()
                self.assertNotEqual(old, new, (derivative, name))
                changed = [line for line in new if line not in old]
                self.assertTrue(all(line.startswith(("type ", "effect ", "fn ")) for line in changed),
                                (derivative, name, changed))
                self.assertFalse(any(line.startswith("fn place") for line in changed), (derivative, name))
                flow = [line for line in old if line.startswith("  ")]
                self.assertEqual(flow, [line for line in new if line.startswith("  ")], (derivative, name))


class DriftRun(unittest.TestCase):
    """One `run.py drift` run for every case of this class (a run takes minutes)."""
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        cls.before = lib_hashes()
        results_before = set(RESULTS_ROOT.iterdir()) if RESULTS_ROOT.is_dir() else set()
        cls.done = subprocess.run([sys.executable, "-B", str(EXPERIMENT / "run.py"), "drift"], cwd=str(REPO),
                                  capture_output=True, text=True, timeout=7200)
        cls.after = lib_hashes()
        try:
            cls.summary = json.loads(cls.done.stdout.strip().splitlines()[-1])
        except (IndexError, ValueError):
            cls.summary = {}
        cls.run_dir = Path(cls.summary.get("run") or "/nonexistent").resolve()
        cls.new_dir = cls.run_dir not in {path.resolve() for path in results_before}

    def assert_run(self):
        self.assertEqual(0, self.done.returncode, self.done.stdout.strip()[-400:])
        self.assertTrue(self.run_dir.is_dir() and self.run_dir.parent == RESULTS_ROOT.resolve(),
                        "no run dir: %r" % self.run_dir)
        self.assertTrue(self.new_dir, "run dir is not new")

    def test_f_lib_is_frozen_before_drift(self):
        freeze = ARMS / "lib" / "freeze.json"
        self.assertTrue(freeze.is_file(), "no LIB freeze record")
        self.assertEqual(lib_hashes(), json.loads(freeze.read_text()).get("sha256"))
        self.assertEqual(set(LIB_MODULES), set(lib_hashes()))

    def test_f_drift_outcomes_recorded_per_arm_and_derivative(self):
        # Review round 2: a class string alone is not evidence. Each row names the files of this run
        # (EVIDENCE_CONTRACT), and the test re-derives the class families from them.
        self.assert_run()
        drift = self.summary["drift"]
        problems = []
        for derivative in DERIVATIVES:
            for arm in ARMS_NAMES:
                row = drift.get(derivative, {}).get(arm, {})
                where = "%s %s" % (derivative, arm)
                for observation in OBSERVATIONS:
                    if row.get(observation) not in CLASSES:
                        problems.append("%s %s: %r" % (where, observation, row.get(observation)))
                if not isinstance(row.get("manual_change_sites"), int):
                    problems.append("%s: no manual change site count" % where)
                problems.extend(evidence_problems(where, row, self.run_dir))
        self.assertEqual([], problems)
        self.assertEqual(self.before, self.after, "a DRIFT run changed the frozen LIB")

    def test_f_drift_classes_equal_the_pin(self):
        # DL-135: a crash, a build failure or another class change is a fail, not a recorded outcome.
        self.assert_run()
        rows = {d: tuple(((self.summary.get("drift", {}).get(d) or {}).get("gen") or {}).get(o)
                         for o in OBSERVATIONS) for d in DERIVATIVES}
        self.assertEqual(PIN, rows)
        self.assertEqual("pass", self.summary.get("status"))

    def test_f_drift_pin_matches_run_py(self):
        sys.path.insert(0, str(EXPERIMENT))
        import run
        self.assertEqual(PIN, run.DRIFT_PIN)

    def test_f_6a_drift_has_gen_rows_only(self):
        # D6B-96, DL-118: the LIB arm leaves DRIFT with DL-110. No LIB row, no LIB baseline, no LIB output.
        self.assert_run()
        problems = []
        # The stdout line has no "baseline"; drift.json in the run dir holds the full summary.
        saved = self.run_dir / "drift.json"
        full = json.loads(saved.read_text()) if saved.is_file() else {}
        for key in ("drift", "baseline", "sites"):
            nested = (self.summary if key != "baseline" else full).get(key) or {}
            arms = [set(nested.get(d) or {}) for d in DERIVATIVES] if key == "drift" else [set(nested)]
            if any(found != {"gen"} for found in arms):
                problems.append("%s arms: %r" % (key, arms))
        problems.extend("LIB output dir: %s" % path.relative_to(self.run_dir)
                        for path in [self.run_dir / "lib"] + [self.run_dir / d / "lib" for d in DERIVATIVES]
                        if path.exists())
        self.assertEqual([], problems)

    def test_f_6a_repair_check_is_the_gen_replay_of_the_repaired_tree(self):
        # D6B-96, DL-118: the repair check is the GEN replay of the repaired tree, never the 0003 copy.
        self.assert_run()
        problems = []
        for derivative in DERIVATIVES:
            row = (self.summary.get("drift", {}).get(derivative) or {}).get("gen") or {}
            if (row.get("evidence") or {}).get("build_exit_code") != 0:
                # RC6A-2: R, N and Q built in every earlier run; without a build D6B-96 has no evidence.
                problems.append("%s gen: build_exit_code %r" % (derivative, (row.get("evidence") or {}).get("build_exit_code")))
                continue
            problems.extend(repaired_problems(derivative, row, self.run_dir))
        if self.summary.get("repaired_all") is not True:
            problems.append("repaired_all: %r" % self.summary.get("repaired_all"))
        self.assertEqual([], problems)


def repaired_problems(derivative, row, run_dir):
    """D6B-96: check row["repaired"] and the command log of one GEN row."""
    where = "%s gen" % derivative
    problems = []
    log = run_dir / derivative / "gen" / "commands" / "commands.json"
    commands = json.loads(log.read_text()) if log.is_file() else []
    for command in commands:
        if any(str(arg).endswith(REPLAY_0003_TEST) for arg in command.get("argv", [])):
            problems.append("%s: command %r runs the 0003 copy %s" % (where, command.get("name"), REPLAY_0003_TEST))
    repaired = row.get("repaired") or {}
    code = repaired.get("exit_code")
    if not isinstance(code, int) or isinstance(code, bool) or code != 0:
        problems.append("%s: repaired.exit_code %r" % (where, code))
    argv = repaired.get("argv")
    if not (isinstance(argv, list) and len(argv) > 1 and str(argv[0]).endswith(ORDERS_RELEASE)
            and argv[1] == "eval"):
        problems.append("%s: repaired.argv is not the eval of the Orders release: %r" % (where, argv))
    # RC6A-1: the argv is a command of this row that exited 0.
    if not any(c.get("argv") == argv and c.get("exit_code") == 0 for c in commands):
        problems.append("%s: repaired.argv is no command of the row log with exit 0" % where)
    record_path = evidence_file(where, {"evidence": repaired}, "record", run_dir, problems)
    report_path = evidence_file(where, {"evidence": repaired}, "report", run_dir, problems)
    if record_path is None or report_path is None:
        return problems
    record = json.loads(record_path.read_text())
    if record.get("version") != 3:
        problems.append("%s: replayed record version %r" % (where, record.get("version")))
    report = json.loads(report_path.read_text())
    # RC6A-1: the eval ran, and the record comes from a new live call of this row (not baseline, not new_live).
    if report.get("eval_exit_code") != 0:
        problems.append("%s: report eval_exit_code %r" % (where, report.get("eval_exit_code")))
    row_dir = run_dir / derivative / "gen"
    traces = lambda path: [json.loads(l).get("trace_id") for l in path.read_text().splitlines() if l.strip()]  # noqa: E731
    baseline = run_dir / "gen" / "baseline" / "record.json"
    old = {json.loads(baseline.read_text()).get("trace_id")} if baseline.is_file() else set()
    live = row_dir / "new_live" / "orders" / "responses.jsonl"
    old |= set(traces(live)) if live.is_file() else set()
    written = {t for path in row_dir.rglob("responses.jsonl") for t in traces(path)}
    trace = record.get("trace_id")
    if not trace or trace in old or trace not in written:
        problems.append("%s: record trace_id %r is not new or not in a responses.jsonl of the row" % (where, trace))
    result = report.get("result") or {}
    # RV6A-1 (option A): the repair evidence must prove the repair. The repaired live call sends an order
    # that fits the drifted payments TYPE Order, gets status 200, and its GEN replay gives `ok` with host
    # validation `ok`. A 400 record that stops at `status_mismatch` runs no repaired line.
    fields = order_fields(derivative)
    request = record.get("request")
    if not isinstance(request, dict) or set(request) != fields:
        problems.append("%s: repaired request %r does not fit the drifted TYPE Order %r"
                        % (where, request, sorted(fields)))
    if record.get("status") != 200:
        problems.append("%s: repaired record status %r, not 200" % (where, record.get("status")))
    if "ok" not in result or result.get("error") == "status_mismatch":
        problems.append("%s: repaired replay result %r, not ok" % (where, result))
    if report.get("host_validation") != "ok":
        problems.append("%s: repaired host validation %r, not ok" % (where, report.get("host_validation")))
    return problems


def order_fields(derivative):
    """Field names of `type Order { ... }` in the drifted payments.beaml of one derivative."""
    for line in (EXPERIMENT / "drift" / derivative / "payments.beaml").read_text().splitlines():
        if line.startswith("type Order {"):
            return {part.split(":")[0].strip() for part in line.split("{", 1)[1].rstrip("} ").split(" ")
                    if part.endswith(":")}
    return set()


def evidence_file(where, row, key, run_dir, problems):
    """Return the parsed path of row["evidence"][key] if it is a file inside this run dir, else None."""
    value = (row.get("evidence") or {}).get(key)
    if not isinstance(value, str):
        problems.append("%s: no evidence path %s" % (where, key))
        return None
    path = Path(value).resolve()
    if not path.is_file():
        problems.append("%s: evidence %s is not a file: %s" % (where, key, value))
        return None
    if run_dir not in path.parents:
        problems.append("%s: evidence %s is outside this run dir: %s" % (where, key, value))
        return None
    return path


def evidence_problems(where, row, run_dir):
    """Re-derive the class family of each observation from the evidence files of one row."""
    problems = []
    evidence = row.get("evidence") or {}
    evidence_file(where, row, "build_output", run_dir, problems)
    exit_code = evidence.get("build_exit_code")
    if not isinstance(exit_code, int) or isinstance(exit_code, bool):
        problems.append("%s: no build exit code" % where)
        return problems
    if (exit_code != 0) != (row.get("build") == "compile_error"):
        problems.append("%s: build exit %d contradicts build class %r" % (where, exit_code, row.get("build")))
    if exit_code != 0:
        # No release, so no live call and no replay: both observations are the compile-time class.
        for observation in ("new_live", "pre_change"):
            if row.get(observation) != "compile_error":
                problems.append("%s: build failed but %s is %r" % (where, observation, row.get(observation)))
        return problems
    live = evidence_file(where, row, "new_live_report", run_dir, problems)
    if live is not None:
        reply = json.loads(live.read_text()).get("reply")
        code = reply[0] if isinstance(reply, list) and reply else None
        family = ACCEPT if code == 200 else REJECT | {"untyped_crash"}
        if row.get("new_live") not in family:
            problems.append("%s: new_live HTTP %r contradicts class %r" % (where, code, row.get("new_live")))
    replay = evidence_file(where, row, "pre_change_replay_report", run_dir, problems)
    if replay is not None:
        result = json.loads(replay.read_text()).get("result") or {}
        family = (ACCEPT if "ok" in result else REJECT if "error" in result
                  else {"untyped_crash"} if "raised" in result else set())
        if row.get("pre_change") not in family:
            problems.append("%s: pre_change result %r contradicts class %r" % (where, result, row.get("pre_change")))
    return problems

if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)

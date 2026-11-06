"""EXPERIMENT 0004 slice 1 arms harness: cases (b) strict compile, (c) live, (d) replay, (d2) TYPE mismatch, (e) LIB.

Each arm runs in a temporary tree with the repository layout (tests/arm_tree.py). The originals stay the control.
Case (d2) follows the owner decision of 2026-11-06 (tolerant decode with a hint, notes.md):
an unknown key is accepted and named in the RESPONSE RECORD (`unknown_keys`) and on the EFFECT span.
A missing or wrongly typed declared field gives `PaymentError{reason: "decode"}`, live (L3) and in a REPLAY RUN.
`Replay.run/3` returns only `{:ok, payment}` or `{:error, reason}` (D7 repair). A REPLAY RUN reports the
hint on its EFFECT span; the harness adds the spans of the eval VM to the replay report.
Run serially, loopback only: python3 -B experiments/0004-generated-replay/tests/arms_test.py [-k NAME]
"""
import atexit
import base64
import datetime
import hashlib
import http.server
import json
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arm_tree  # noqa: E402
from arm_tree import COMPILER_PATH, HTTP_PATH, REPLAY_PATH, REPO  # noqa: E402

sys.path.insert(0, str(REPO / HTTP_PATH))
from run import request, stop  # noqa: E402  (0002 helpers, as in the 0003 tests)
from query import event  # noqa: E402

EXPERIMENT = arm_tree.EXPERIMENT
ORDER = {"order_id": "order-1"}
PAYMENT = {"order_id": "order-1", "status": "authorized"}
VALID_BODY = b'{"order_id":"order-1","status":"authorized"}'
UNKNOWN_KEY_BODY = b'{"order_id":"order-1","status":"authorized","fraud_score":"low"}'
MISSING_KEY_BODY = b'{"order_id":"order-1"}'
WRONG_TYPE_BODY = b'{"order_id":"order-1","status":7}'
DECODE_ERROR = '%OrdersBeamlSpike.PaymentError{reason: "decode"}'
TRANSPORT_ERROR = '%OrdersBeamlSpike.PaymentError{reason: "transport"}'
EIGHT_CASES = ("replay_first_call", "replay_a1_noncanonical_body", "replay_missing_response",
               "replay_operation_mismatch", "replay_attempt_mismatch", "replay_body_digest_mismatch",
               "replay_status_mismatch", "replay_request_mismatch")
DEFAULT_STEPS = ["compiler-reference", "trace-lookup", "trace-lookup-repair", "response-capture", "replay-run"]
STAMP = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
RESULTS = EXPERIMENT / "results" / STAMP
CONTROL_BEFORE = arm_tree.control_hashes()
MIX = ["env", "MIX_ENV=prod", "mix"]

WATCHED = {
    "gen": ["{OrdersApi.Router, :call, 2}", "{OrdersBeamlSpike, :payments_authorize, 1}", "{:gen_tcp, :connect, 4}",
            "{OrdersBeamlSpike, :prepare, 1}", "{:json, :decode, 1}", "{OrdersBeamlSpike, :finish, 1}",
            "{ProbeSupport, :valid_payment!, 2}"],
    "lib": ["{OrdersApi.Router, :call, 2}", "{OrdersApi.PaymentHttp, :authorize, 2}", "{:gen_tcp, :connect, 4}",
            "{OrdersBeamlSpike, :prepare, 1}", "{:json, :decode, 1}", "{OrdersBeamlSpike, :finish, 1}",
            "{ProbeSupport, :valid_payment!, 2}"],
}
REPLAY_CALL = {
    "gen": "OrdersBeamlSpike.Replay.run(ProbeSupport.valid_order!(order), input[\"trace_id\"], input[\"responses\"])",
    "lib": "ReplayLib.run(OrdersApi.ReplayDescriptor.authorize(), ProbeSupport.valid_order!(order), "
           "input[\"trace_id\"], input[\"responses\"])",
}
PLACE_CALL = {"gen": "OrdersBeamlSpike.place(order)", "lib": "raise ArgumentError, \"no place in LIB\""}
# The 0003 eval harness with the arm runner. One return shape (D7 repair): `{:ok, payment}` or `{:error, reason}`.
# With "observe", the eval VM starts only OpenTelemetry and the capture writer, so the replay EFFECT span
# reaches PROBE_OUTPUT/spans.jsonl. The router and the Orders application do not start.
HARNESS = r'''
input = :json.decode(File.read!(System.fetch_env!("REPLAY_INPUT")))
:persistent_term.put(:probe_count, :atomics.new(1, []))
if input["observe"] == true do
  {:ok, _} = Application.ensure_all_started(:opentelemetry)
  {:ok, _} = ProbeSupport.Capture.start_link(nil)
end
watched = [%(watched)s]
unwatched = for {m, _, _} = mfa <- watched, Code.ensure_loaded?(m) == false or :erlang.trace_pattern(mfa, true, [:call_count]) != 1, do: inspect(mfa)
order = input["order"]
result =
  try do
    case input["mode"] do
      "place" -> %(place)s
      "replay" ->
        case %(replay)s do
          {:ok, p} -> {:ok, ProbeSupport.valid_payment!(p, order)}
          other -> other
        end
    end
  rescue
    error -> {:raised, inspect(error.__struct__)}
  end
if input["observe"] == true, do: :otel_tracer_provider.force_flush()
report = case result do
  {:ok, payment} -> %%{ok: payment}
  {:error, reason} when is_atom(reason) -> %%{error: Atom.to_string(reason)}
  {:error, reason} -> %%{error: inspect(reason)}
  {:raised, name} -> %%{raised: name}
  other -> %%{unexpected: inspect(other)}
end
calls = Map.new(watched, fn {m, f, a} = mfa ->
  count = case :erlang.trace_info(mfa, :call_count) do {:call_count, n} when is_integer(n) -> n; _ -> nil end
  {"#{inspect(m)}.#{f}/#{a}", count} end)
IO.puts("REPLAY " <> IO.iodata_to_binary(:json.encode(%%{
  result: report, transport: ProbeSupport.count(), calls: calls, unwatched: unwatched})))
'''


def utc():
    return datetime.datetime.now(datetime.timezone.utc)


def save(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, default=str) + "\n")


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()] if Path(path).exists() else []


def command(name, args, cwd, env=None, timeout=600):
    """Run one command, keep stdout and stderr in the results. Return (exit code, stdout)."""
    out_dir = RESULTS / "commands"
    out_dir.mkdir(parents=True, exist_ok=True)
    args = [str(arg) for arg in args]
    with (out_dir / (name + ".stdout")).open("wb") as out, (out_dir / (name + ".stderr")).open("wb") as err:
        code = subprocess.run(args, cwd=str(cwd), env=env, stdout=out, stderr=err, timeout=timeout).returncode
    with (RESULTS / "commands.jsonl").open("a") as log:
        log.write(json.dumps({"name": name, "argv": args, "cwd": str(cwd), "exit_code": code}) + "\n")
    return code, (out_dir / (name + ".stdout")).read_text(errors="replace")


def stderr_head(name):
    text = (RESULTS / "commands" / (name + ".stderr")).read_text(errors="replace").strip().splitlines()
    return text[0] if text else ""


_TREES, _BUILDS, _RUNS = {}, {}, {}


def tree(arm):
    """One temporary arm tree per process and arm."""
    if arm not in _TREES:
        holder = tempfile.TemporaryDirectory(prefix="beaml-0004-%s-" % arm)
        atexit.register(holder.cleanup)
        root = Path(holder.name)
        applied = arm_tree.build(arm, root)
        save(RESULTS / arm / "tree-applied.json", applied)
        _TREES[arm] = root
    return _TREES[arm]


def build(arm):
    """Generate both modules with the tree compiler, compile strict, build the Orders release. Cached."""
    if arm in _BUILDS:
        if isinstance(_BUILDS[arm], AssertionError):
            raise _BUILDS[arm]
        return _BUILDS[arm]
    root = tree(arm)
    http = root / HTTP_PATH
    try:
        code, _ = command(arm + "-deps", MIX + ["deps.get", "--offline"], http)
        assert code == 0, ("deps.get", code)
        for service in ("orders", "payments"):
            name = "%s-generate-%s" % (arm, service)
            code, generated = command(name, ["cargo", "run", "--offline", "--quiet", "--manifest-path",
                                             root / COMPILER_PATH / "Cargo.toml", "--",
                                             http / ("apps/%s_api/priv/%s.beaml" % (service, service))], root)
            assert code == 0, "%s: compiler exit %d: %s" % (name, code, stderr_head(name))
            assert generated.count("defmodule BeamlSpike do") == 1, name
            target = http / ("apps/%s_api/lib/generated.ex" % service)
            target.write_text(generated.replace("defmodule BeamlSpike do",
                                                "defmodule %sBeamlSpike do" % service.title()))
            shutil.copyfile(target, RESULTS / arm / ("%s.generated.ex" % service))
        code, _ = command(arm + "-compile-strict", MIX + ["compile", "--force", "--warnings-as-errors"], http)
        strict = code == 0
        code, _ = command(arm + "-release-orders", MIX + ["release", "orders", "--overwrite"], http)
        assert code == 0, "%s-release-orders: exit %d: %s" % (arm, code, stderr_head(arm + "-release-orders"))
        _BUILDS[arm] = {"http": http, "strict": strict, "bin": http / "_build/prod/rel/orders/bin/orders"}
    except AssertionError as error:
        _BUILDS[arm] = error
        raise
    return _BUILDS[arm]


def refused_port():
    with socket.socket() as closed:
        closed.bind(("127.0.0.1", 0))
        return closed.getsockname()[1]


def orders_env(out, payments_port):
    return dict(PATH="/usr/bin:/bin:/usr/sbin:/sbin", PROBE_SERVICE="orders", PROBE_OUTPUT=str(out),
                PROBE_PAYMENTS_PORT=str(payments_port), PROBE_DROP_CONTEXT="false",
                RELEASE_DISTRIBUTION="none", RELEASE_COOKIE="beaml_synthetic_loopback_test")


def live(arm, name, status, body):
    """One Orders call against the 0003 loopback stub (http.server, Content-Length framing)."""
    built = build(arm)
    out = RESULTS / arm / "live" / name
    out.mkdir(parents=True)
    for kind in ("spans", "logs"):
        (out / (kind + ".jsonl")).touch()
    sent = []

    class Stub(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            sent.append(self.rfile.read(int(self.headers["Content-Length"])))
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    stub = http.server.HTTPServer(("127.0.0.1", 0), Stub)
    threading.Thread(target=stub.serve_forever, daemon=True).start()
    process = None
    try:
        with (out / "process.log").open("wb") as log:
            process = subprocess.Popen([str(built["bin"]), "start"], env=orders_env(out, stub.server_address[1]),
                                       stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            deadline = time.monotonic() + 20
            while not (out / "ready.json").exists():
                assert process.poll() is None and time.monotonic() < deadline, ("orders_not_ready", name)
                time.sleep(.05)
            port = json.loads((out / "ready.json").read_text())["port"]
            reply = request(port, "/orders", ORDER)
            _, control = request(port)
    finally:
        if process is not None:
            stop(process)
        stub.shutdown()
        stub.server_close()
    observed = {"reply": list(reply), "transport": control["count"], "loss": control["capture"]["loss"],
                "sent": len(sent), "spans": rows(out / "spans.jsonl"), "records": rows(out / "responses.jsonl")}
    save(out / "observed.json", observed)
    return observed


def harness(arm, name, replay_input, payments_port=None):
    built = build(arm)
    out = RESULTS / arm / "eval" / name
    out.mkdir(parents=True)
    save(out / "input.json", dict(order=ORDER, **replay_input))
    script = HARNESS % {"watched": ", ".join(WATCHED[arm]), "replay": REPLAY_CALL[arm], "place": PLACE_CALL[arm]}
    env = dict(orders_env(out, payments_port or refused_port()), REPLAY_INPUT=str(out / "input.json"))
    code, text = command("%s-eval-%s" % (arm, name), [built["bin"], "eval", script], REPO, env=env, timeout=120)
    lines = [line[7:] for line in text.splitlines() if line.startswith("REPLAY ")]
    assert code == 0 and len(lines) == 1, ("eval_report", name, code, stderr_head("%s-eval-%s" % (arm, name)))
    report = json.loads(lines[0])
    if replay_input.get("observe"):
        # The replay report carries the spans of the eval VM (D7 repair: the hint is not in the return value).
        report["spans"] = rows(out / "spans.jsonl")
    save(out / "report.json", report)
    return report


def with_body(record, body):
    """A RESPONSE RECORD derivative with other body bytes and a recomputed length and SHA-256."""
    return dict(record, body_base64=base64.b64encode(body).decode(), body_length=len(body),
                body_sha256=hashlib.sha256(body).hexdigest())


def replay_counts(report, keys):
    calls = report["calls"]
    return dict({"result": report["result"], "transport": report["transport"]}, **{k: calls.get(k) for k in keys})


def run_0003(arm):
    """Run the unchanged 0003 runner in the arm tree once. Keep its result and the result dirs."""
    if arm not in _RUNS:
        root = tree(arm)
        code, stdout = command(arm + "-0003-run", [sys.executable, "-B", REPLAY_PATH + "/run.py"], root, timeout=3000)
        results = root / REPLAY_PATH / "results"
        if results.is_dir():
            shutil.copytree(results, RESULTS / arm / "0003-results")
        summary = json.loads(stdout.strip().splitlines()[-1]) if stdout.strip() else {}
        run_result = json.loads((Path(summary["run"]) / "result.json").read_text()) if summary.get("run") else {}
        replay = next((s for s in run_result.get("steps", []) if s["name"] == "replay-run"), {})
        replay_result = {}
        if replay.get("result_dir") and (Path(replay["result_dir"]) / "result.json").is_file():
            replay_result = json.loads((Path(replay["result_dir"]) / "result.json").read_text())
        _RUNS[arm] = {"exit_code": code, "result": run_result, "replay": replay_result}
        save(RESULTS / arm / "0003-run.json", _RUNS[arm])
    return _RUNS[arm]


def tree_text(arm, relative):
    path = tree(arm) / relative
    return path.read_text() if path.is_file() else None


def modules(arm):
    """Map of `defmodule` name to file text over the Orders and ProbeSupport apps of the tree."""
    found = {}
    for path in (tree(arm) / HTTP_PATH / "apps").glob("*/lib/**/*.ex"):
        text = path.read_text()
        for name in re.findall(r"^\s*defmodule ([\w.]+) do", text, re.M):
            found.setdefault(name, (path, text))
    return found


class Case(unittest.TestCase):
    """Posts one use-case event per test start and result (AGENTS.md, compiler action events)."""
    maxDiff = None

    def run(self, result=None):
        result = result or self.defaultTestResult()
        before = len(result.failures) + len(result.errors)
        event("start", self.id(), "running")
        super().run(result)
        event("pass" if len(result.failures) + len(result.errors) == before else "fail", self.id(), "done")
        return result


class GenStructure(Case):
    def test_c_gen_router_calls_only_place_and_host_replay_files_are_deleted(self):
        router = tree_text("gen", HTTP_PATH + "/apps/orders_api/lib/orders_api/router.ex") or ""
        problems = []
        called = sorted(set(re.findall(r"OrdersBeamlSpike\.(\w+!?)", router)))
        if called != ["place"]:
            problems.append("router calls OrdersBeamlSpike %s, expected only place" % called)
        for kept in ('"orders.request"', "ProbeSupport.valid_order!(", "ProbeSupport.valid_payment!("):
            if kept not in router:
                problems.append("router lost host code %s" % kept)
        for gone in ("payment_http.ex", "replay.ex"):
            if tree_text("gen", HTTP_PATH + "/apps/orders_api/lib/orders_api/" + gone) is not None:
                problems.append("%s is not deleted" % gone)
        left = sorted(n for n in modules("gen") if n in ("OrdersApi.PaymentHttp", "OrdersApi.Replay"))
        if left:
            problems.append("host transport or replay modules left: %s" % left)
        self.assertEqual([], problems)


class GenBuild(Case):
    def test_b_gen_module_compiles_with_warnings_as_errors(self):
        self.assertTrue(build("gen")["strict"], "mix compile --force --warnings-as-errors failed")


class GenRunner(Case):
    def require_gen_copies(self):
        text = tree_text("gen", REPLAY_PATH + "/tests/replay_run_test.py")
        self.assertIn("OrdersBeamlSpike.Replay.run(", text, "GEN copy of replay_run_test.py is not in the tree")

    def test_c_gen_0003_runner_passes_all_five_steps(self):
        self.require_gen_copies()
        outcome = run_0003("gen")
        steps = [(s["name"], s["status"]) for s in outcome["result"].get("steps", [])]
        self.assertEqual(([(n, "pass") for n in DEFAULT_STEPS], 0), (steps, outcome["exit_code"]))

    def test_d_gen_replay_matrix_eight_cases(self):
        self.require_gen_copies()
        assertions = run_0003("gen")["replay"].get("assertions", {})
        self.assertEqual(sorted(EIGHT_CASES + ("a1_record_bytes_equal_sent_bytes",)), sorted(assertions))
        for name, pair in assertions.items():
            self.assertEqual(pair["expected"], pair["actual"], name)


class GenTypeMismatch(Case):
    """Case (d2). Live cases L0, L1, L2 run first; the replay cases use their records."""
    REPLAY_KEYS = ("OrdersApi.Router.call/2", "OrdersBeamlSpike.payments_authorize/1", ":gen_tcp.connect/4",
                   ":json.decode/1", "OrdersBeamlSpike.finish/1", "ProbeSupport.valid_payment!/2")
    _live = {}

    @classmethod
    def observed(cls, name):
        bodies = {"L0": (200, VALID_BODY), "L1": (200, UNKNOWN_KEY_BODY), "L2": (503, VALID_BODY),
                  "L3": (200, MISSING_KEY_BODY)}
        if name not in cls._live:
            cls._live[name] = live("gen", name, *bodies[name])
        return cls._live[name]

    def spans(self, observed, span_name):
        return [s for s in observed["spans"] if s["name"] == span_name]

    def test_d2_L0_live_valid_body_baseline(self):
        seen = self.observed("L0")
        self.assertEqual({"reply": [200, PAYMENT], "transport": 1, "sent": 1, "records": 1, "finish": 1},
                         {"reply": seen["reply"], "transport": seen["transport"], "sent": seen["sent"],
                          "records": len(seen["records"]), "finish": len(self.spans(seen, "orders.finish"))})

    def test_d2_L1_live_unknown_key_accepted_with_hint(self):
        seen = self.observed("L1")
        client = self.spans(seen, "orders.payments.authorize")
        record = seen["records"][0] if len(seen["records"]) == 1 else {}
        self.assertEqual(
            {"reply": [200, PAYMENT], "transport": 1, "records": 1, "status": 200,
             "bytes": base64.b64encode(UNKNOWN_KEY_BODY).decode(), "record_hint": ["fraud_score"],
             "client": [("ok", True)], "finish": 1},
            {"reply": seen["reply"], "transport": seen["transport"], "records": len(seen["records"]),
             "status": record.get("status"), "bytes": record.get("body_base64"),
             "record_hint": record.get("unknown_keys"),
             "client": [(s["attributes"].get("outcome"), "fraud_score" in json.dumps(s["attributes"].get("unknown_keys")))
                        for s in client],
             "finish": len(self.spans(seen, "orders.finish"))})

    def test_d2_L2_live_status_503_rejected(self):
        seen = self.observed("L2")
        record = seen["records"][0] if len(seen["records"]) == 1 else {}
        self.assertEqual(
            {"reply": [502, {"error": "downstream_failure"}], "transport": 1, "records": 1, "status": 503,
             "bytes": base64.b64encode(VALID_BODY).decode(), "client": ["error"], "finish": 0},
            {"reply": seen["reply"], "transport": seen["transport"], "records": len(seen["records"]),
             "status": record.get("status"), "bytes": record.get("body_base64"),
             "client": [s["attributes"].get("outcome") for s in self.spans(seen, "orders.payments.authorize")],
             "finish": len(self.spans(seen, "orders.finish"))})

    def test_d2_L3_live_missing_key_is_typed_decode_error(self):
        # Owner decision: a response that does not match the TYPE gives a typed error, live too (review objection 2).
        seen = self.observed("L3")
        record = seen["records"][0] if len(seen["records"]) == 1 else {}
        self.assertEqual(
            {"reply": [502, {"error": "downstream_failure"}], "transport": 1, "records": 1, "status": 200,
             "bytes": base64.b64encode(MISSING_KEY_BODY).decode(), "client": [("error", "decode")], "finish": 0},
            {"reply": seen["reply"], "transport": seen["transport"], "records": len(seen["records"]),
             "status": record.get("status"), "bytes": record.get("body_base64"),
             "client": [(s["attributes"].get("outcome"), s["attributes"].get("reason"))
                        for s in self.spans(seen, "orders.payments.authorize")],
             "finish": len(self.spans(seen, "orders.finish"))})

    def replay_record(self, name, record, observe=False):
        replay_input = {"mode": "replay", "trace_id": record["trace_id"], "responses": [record]}
        if observe:
            replay_input["observe"] = True
        report = harness("gen", name, replay_input)
        counts = replay_counts(report, self.REPLAY_KEYS)
        if observe:
            counts["replay_hint"] = [s["attributes"].get("unknown_keys") for s in report.get("spans", [])
                                     if s["name"] == "orders.payments.authorize"]
        return counts

    def base_record(self, name):
        records = self.observed(name)["records"]
        self.assertEqual(1, len(records), "live %s gave no single RESPONSE RECORD" % name)
        return records[0]

    def decode_error(self):
        return {"result": {"error": DECODE_ERROR}, "transport": 0, "OrdersApi.Router.call/2": 0,
                "OrdersBeamlSpike.payments_authorize/1": 0, ":gen_tcp.connect/4": 0, ":json.decode/1": 1,
                "OrdersBeamlSpike.finish/1": 0, "ProbeSupport.valid_payment!/2": 0}

    def test_d2_R1_replay_missing_key_is_decode_error(self):
        record = with_body(self.base_record("L0"), MISSING_KEY_BODY)
        self.assertEqual(self.decode_error(), self.replay_record("R1", record))

    def test_d2_R2_replay_of_L1_record_gives_same_success_and_hint(self):
        # D7 repair: one return shape; the hint is read from the replay EFFECT span in the replay report.
        expected = {"result": {"ok": PAYMENT}, "transport": 0,
                    "OrdersApi.Router.call/2": 0, "OrdersBeamlSpike.payments_authorize/1": 0,
                    ":gen_tcp.connect/4": 0, ":json.decode/1": 1, "OrdersBeamlSpike.finish/1": 1,
                    "ProbeSupport.valid_payment!/2": 1, "replay_hint": [["fraud_score"]]}
        self.assertEqual(expected, self.replay_record("R2", self.base_record("L1"), observe=True))

    def test_d2_R3_replay_wrongly_typed_field_is_decode_error(self):
        record = with_body(self.base_record("L0"), WRONG_TYPE_BODY)
        self.assertEqual(self.decode_error(), self.replay_record("R3", record))

    def test_d2_P1_pipe_stops_after_failed_effect(self):
        report = harness("gen", "P1", {"mode": "place"})
        calls = report["calls"]
        self.assertEqual({"result": {"error": TRANSPORT_ERROR}, "prepare": 1, "finish": 0},
                         {"result": report["result"], "prepare": calls.get("OrdersBeamlSpike.prepare/1"),
                          "finish": calls.get("OrdersBeamlSpike.finish/1")})


class LibArm(Case):
    """Case (e). The LIB form is fixed by the README; R1, R2, L1, L2 are recorded, not asserted."""

    def test_e_lib_form_is_the_fixed_strongest_library(self):
        found, problems = modules("lib"), []
        lib = found.get("ReplayLib")
        descriptor = found.get("OrdersApi.ReplayDescriptor")
        if lib is None:
            problems.append("no ReplayLib module")
        else:
            if len(lib[1].splitlines()) > 60:
                problems.append("ReplayLib exceeds 60 lines")
            if "rescue" not in lib[1]:
                # Guard only. The typed result is asserted on LIB R1 before the freeze (review objection 3).
                problems.append("ReplayLib has no rescue")
        if descriptor is None:
            problems.append("no OrdersApi.ReplayDescriptor module")
        elif re.search(r"order_id|status|reference", descriptor[1]):
            problems.append("descriptor names a TYPE field")
        if "OrdersApi.Replay" in found:
            problems.append("replay.ex is not deleted")
        transport = tree_text("lib", HTTP_PATH + "/apps/orders_api/lib/orders_api/payment_http.ex") or ""
        if transport.count("ReplayLib.record(") != 1 or "defp capture" in transport:
            problems.append("payment_http.ex does not record through one ReplayLib.record call")
        router = HTTP_PATH + "/apps/orders_api/lib/orders_api/router.ex"
        if tree_text("lib", router) != (REPO / router).read_text():
            problems.append("LIB changed the router")
        self.assertEqual([], problems)

    def require_lib_copies(self):
        text = tree_text("lib", REPLAY_PATH + "/tests/replay_run_test.py")
        self.assertIn("ReplayLib.run(", text, "LIB copy of replay_run_test.py is not in the tree")

    def test_e_lib_arm_replays_matrix(self):
        self.require_lib_copies()
        outcome = run_0003("lib")
        steps = [(s["name"], s["status"]) for s in outcome["result"].get("steps", [])]
        self.assertEqual([(n, "pass") for n in DEFAULT_STEPS], steps)
        assertions = outcome["replay"].get("assertions", {})
        self.assertEqual(sorted(EIGHT_CASES + ("a1_record_bytes_equal_sent_bytes",)), sorted(assertions))
        for name, pair in assertions.items():
            self.assertEqual(pair["expected"], pair["actual"], name)

    def test_e_lib_type_mismatch_outcomes_recorded_then_frozen(self):
        self.assertIn("ReplayLib", modules("lib"), "no ReplayLib module in the LIB tree")
        outcomes = {}
        for name, status, body in (("L0", 200, VALID_BODY), ("L1", 200, UNKNOWN_KEY_BODY), ("L2", 503, VALID_BODY)):
            seen = live("lib", name, status, body)
            outcomes[name] = {"reply": seen["reply"], "records": len(seen["records"])}
            outcomes[name + "_record"] = seen["records"][0] if seen["records"] else None
        cases = {"R1": with_body(outcomes["L0_record"], MISSING_KEY_BODY) if outcomes["L0_record"] else None,
                 "R2": outcomes["L1_record"]}
        for name, record in cases.items():
            outcomes[name] = record and harness("lib", name, {"mode": "replay", "trace_id": record["trace_id"],
                                                               "responses": [record]})["result"]
        save(RESULTS / "lib" / "type-mismatch-outcomes.json", outcomes)
        # Fixed LIB form, not an outcome class (review objection 3): ReplayLib.run returns
        # {:error, %ReplayLib.Error{step: "decode" | "finish", reason: ...}}, never a raise, never an untyped tuple.
        typed = (outcomes["R1"] or {}).get("error", "")
        self.assertRegex(typed, r'^%ReplayLib\.Error\{(?=.*\bstep: "(decode|finish)")(?=.*\breason: )',
                         "LIB R1 is not a typed ReplayLib.Error: %r" % (outcomes["R1"],))
        freeze = EXPERIMENT / "arms/lib/freeze.json"
        self.assertTrue(freeze.is_file(), "no LIB freeze record")
        frozen = json.loads(freeze.read_text())
        found = modules("lib")
        actual = {name: hashlib.sha256(found[name][0].read_bytes()).hexdigest()
                  for name in ("ReplayLib", "OrdersApi.ReplayDescriptor")}
        self.assertEqual(actual, frozen.get("sha256"))


class ZzControlUnchanged(Case):
    """Runs last (name order). Arm runs do not change the originals (README, EXECUTION control)."""

    def test_control_originals_unchanged_by_arm_runs(self):
        self.assertEqual(CONTROL_BEFORE, arm_tree.control_hashes())


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    RESULTS.mkdir(parents=True, exist_ok=True)
    print(RESULTS, flush=True)
    unittest.main(verbosity=2)

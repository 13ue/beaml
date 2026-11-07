"""Repeatable command for EXPERIMENT 0004 slice 1 (README "Slice 1: acceptance cases in order").

Usage (from any cwd; loopback only; every step runs serially):
  python3 -B experiments/0004-generated-replay/run.py          all steps: compiler, LIB freeze, arms (GEN
                                                               cases), DRIFT (f), the slice 2-5 test files;
                                                               one result dir per run
  python3 -B experiments/0004-generated-replay/run.py drift    case (f) only: DRIFT R, N, Q (GEN rows)
  python3 -B experiments/0004-generated-replay/run.py freeze   write arms/lib/freeze.json once, else verify it
  python3 -B experiments/0004-generated-replay/run.py --list-steps

The last stdout line is one JSON object: {"run": <result dir>, "status": ...} (and "drift" for `drift`).
Arm trees are temporary copies with the repository layout (tests/arm_tree.py); the originals stay the control.
CLI actions go to <repo>/.beaml/actions.jsonl (append-only JSONL; logging never raises).

DRIFT (f), per derivative, GEN arm only since slice 6b step 6a (DL-110, DL-118; evidence D24 and D6B-96 in
tests/drift_test.py):
  1. build: regenerate both modules from the drifted BEAML and build both releases (no other change).
  2. new_live: one Orders call against the drifted Payments release through a loopback proxy that keeps
     the exchanged bytes, plus one eval probe of the arm flow that shows where a failure starts.
  3. pre_change: replay the RESPONSE RECORD of the undrifted arm (baseline) with the drifted arm runner.
  4. repair: apply arms/gen/repair/<derivative>.json, count the edited hunks, rebuild each release whose
     source the repair edits (probe_support.ex is in both), make one live call and replay its RESPONSE RECORD (D6B-96).
The classes come from these observations. The expected outcome comes from the bytes that the proxy saw
and from the drifted TYPE (never from a constant per derivative); see `classify_*`.
"""
import base64
import datetime
import difflib
import hashlib
import http.client
import http.server
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

EXPERIMENT = Path(__file__).resolve().parent
REPO = EXPERIMENT.parents[1]
sys.path.insert(0, str(EXPERIMENT / "tests"))
import arm_tree  # noqa: E402
from arm_tree import COMPILER_PATH, HTTP_PATH, REPLAY_PATH  # noqa: E402

try:
    sys.path.insert(0, str(Path.home() / ".claude-bus"))
    from cbus import post as _bus_post
except Exception:  # the job bus is optional
    _bus_post = None

TARGET = "experiment-0004"
JOB = "exp-0004-run"
TITLE = "Run the arms and the DRIFT of EXPERIMENT 0004 (slice 1)"
RESULTS = EXPERIMENT / "results"
ACTIONS = REPO / ".beaml" / "actions.jsonl"
ARMS = ("gen",)  # Slice 6b step 6a (DL-118, D6B-96): the LIB arm leaves DRIFT; the LIB freeze stays.
DERIVATIVES = ("R", "N", "Q")
LIB_MODULES = {"ReplayLib": "apps/orders_api/lib/replay_lib.ex",
               "OrdersApi.ReplayDescriptor": "apps/orders_api/lib/orders_api/replay_descriptor.ex"}
FREEZE = EXPERIMENT / "arms" / "lib" / "freeze.json"
# Slice 2 (README revision 6, C10): the GEN Orders source has an `effect`, so its build needs a RECORD
# SNAPSHOT. Slice 1 runs use the empty snapshot; each build records its SHA-256. LIB has no `effect`.
EMPTY_SNAPSHOT = EXPERIMENT / "stored" / "empty.jsonl"
ORDER = {"order_id": "order-1"}
MIX = ["env", "MIX_ENV=prod", "mix"]
TESTS = "experiments/0004-generated-replay/tests/"
STEPS = [
    ("compiler", ["cargo", "test", "--offline", "--manifest-path", COMPILER_PATH + "/Cargo.toml"]),
    # Slice 6b step 6a (DL-110, Q6B-10 option B): the overlay diff and the 0003 copy run leave the check list.
    ("lib-freeze", [sys.executable, "-B", "experiments/0004-generated-replay/run.py", "freeze"]),
    ("arms", [sys.executable, "-B", TESTS + "arms_test.py"]),
    ("drift", [sys.executable, "-B", "experiments/0004-generated-replay/run.py", "drift"]),
]
# Slices 2-5: one step per test file, serially, after the slice 1 steps (step name = file name without `_test.py`).
SLICE_TESTS = ("stored_types", "slice2_replay", "slice3_types", "slice3_replay", "slice4_retire", "slice4_replay",
               "slice5_syntax", "slice5_squash", "slice5_replay", "slice5_rewrite",
               # D6B-190 (DL-135, M7 option A): every slice 6 file and the DRIFT checks join the full run.
               "slice6_int", "slice6_failure", "slice6_constructor", "slice6_enum", "slice6_pipe", "slice6_decode",
               "slice6_decode_ctor", "slice6_fmt", "slice6_host_struct", "slice6_effect_reach", "slice6_record",
               "slice6_redacted", "slice6_redacted_failure", "slice6_stored_elixir", "slice6_struct_order",
               "slice6_entry", "slice6_multi", "slice6_db", "slice6_db_stored",
               "record_v3", "redteam_c1", "redteam_b3", "redteam_c3")
STEPS += [(name.replace("_", "-"), [sys.executable, "-B", TESTS + name + "_test.py"]) for name in SLICE_TESTS]
# Not "drift": that step name owns drift.stdout and the result.json summary.
STEPS.append(("drift-test", [sys.executable, "-B", TESTS + "drift_test.py"]))
# File classes of a repair hunk (README "Replay lines and manual change sites").
DOMAIN_FILES = (HTTP_PATH + "/apps/probe_support/lib/probe_support.ex",)
TEST_FILES = tuple([HTTP_PATH + "/query.py"] + [REPLAY_PATH + "/tests/" + n for n in arm_tree.TEST_NAMES])
# Eval probes. GEN: the generated flow. LIB: the 0002 live path the router runs (prepare, transport in its
# client span, finish). The span matters: without one, the CAPTURE reads no span context and raises, which
# the live router never sees (first DRIFT run, results/20261106T123902454745Z, LIB new_live probe).
FLOW = {"gen": "OrdersBeamlSpike.place(order)"}
RUNNER = {"gen": "OrdersBeamlSpike.Replay.run(ProbeSupport.valid_order!(order), input[\"trace_id\"], input[\"responses\"])"}
# One eval script for both probes. The runner result is reported without host validation; the host
# validation (`valid_payment!/2`, counted apart in the README) is reported next to it.
EVAL = r'''
input = :json.decode(File.read!(System.fetch_env!("PROBE_INPUT")))
:persistent_term.put(:probe_count, :atomics.new(1, []))
order = input["order"]
outcome =
  try do
    case input["mode"] do
      "flow" -> %(flow)s
      "replay" -> %(runner)s
    end
  rescue
    error -> {:raised, inspect(error.__struct__)}
  catch
    kind, _ -> {:raised, Atom.to_string(kind)}
  end
host = case outcome do
  {:ok, value} ->
    try do
      ProbeSupport.valid_payment!(value, order)
      "ok"
    rescue
      error -> inspect(error.__struct__)
    end
  _ -> nil
end
result = case outcome do
  {:ok, value} -> %%{ok: value}
  {:error, reason} when is_atom(reason) -> %%{error: Atom.to_string(reason)}
  {:error, reason} -> %%{error: inspect(reason)}
  {:raised, name} -> %%{raised: name}
  other -> %%{unexpected: inspect(other)}
end
IO.puts("PROBE " <> IO.iodata_to_binary(:json.encode(%%{result: result, host_validation: host,
  transport: ProbeSupport.count()})))
'''


def utc():
    return datetime.datetime.now(datetime.timezone.utc)


def save(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, default=str) + "\n")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def event(action, target, result, **state):
    """Append one CLI action event. Never raises."""
    try:
        ACTIONS.parent.mkdir(parents=True, exist_ok=True)
        with ACTIONS.open("a") as out:
            out.write(json.dumps(dict({"ts": utc().isoformat(), "source": "cli", "action": action,
                                       "target": target, "result": result}, **state)) + "\n")
    except Exception:
        pass


def bus(kind, **fields):
    """Post one job bus event. Never raises; no secrets in events."""
    try:
        if _bus_post is not None:
            _bus_post(JOB, kind=kind, title=TITLE, source="0004/run.py", **fields)
    except Exception:
        pass


def rows(path):
    path = Path(path)
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def stop(process):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)


def request(port, path="/control", body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request("http://127.0.0.1:%s%s" % (port, path), data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as response:
        return response.code, json.load(response)


# ---------------------------------------------------------------------------------------------- freeze

def lib_hashes():
    root = EXPERIMENT / "arms" / "lib" / "overlay" / HTTP_PATH
    return {name: digest(root / relative) for name, relative in LIB_MODULES.items() if (root / relative).is_file()}


def freeze():
    """Write the LIB freeze record once. Later calls only verify it: a LIB change after the freeze is a
    manual change site, never a new freeze (README "Freeze")."""
    hashes = lib_hashes()
    if set(hashes) != set(LIB_MODULES):
        return {"status": "fail", "reason": "LIB modules missing", "found": sorted(hashes)}
    if not FREEZE.is_file():
        save(FREEZE, {"sha256": hashes, "frozen_before": "GEN (d2) and DRIFT (f) judging", "ts": utc().isoformat()})
        return {"status": "pass", "action": "written", "sha256": hashes}
    frozen = json.loads(FREEZE.read_text()).get("sha256")
    return {"status": "pass" if frozen == hashes else "fail", "action": "verified", "sha256": hashes,
            "frozen": frozen}


# ---------------------------------------------------------------------------------------------- trees

class Commands:
    """Run commands in an arm tree; keep stdout and stderr of each under `out`."""

    def __init__(self, out):
        self.out = Path(out)
        self.out.mkdir(parents=True, exist_ok=True)
        self.log = []

    def run(self, name, args, cwd, env=None, timeout=900):
        args = [str(a) for a in args]
        with (self.out / (name + ".stdout")).open("wb") as out, (self.out / (name + ".stderr")).open("wb") as err:
            try:
                code = subprocess.run(args, cwd=str(cwd), env=env, stdout=out, stderr=err, timeout=timeout).returncode
            except subprocess.TimeoutExpired:
                err.write(b"runner: timeout\n")
                code = 124
        self.log.append({"name": name, "argv": args, "cwd": str(cwd), "exit_code": code})
        save(self.out / "commands.json", self.log)
        return code, (self.out / (name + ".stdout")).read_text(errors="replace")


def build_tree(arm, tree, out, orders_beaml=None, payments_beaml=None):
    """Write the arm tree, generate both modules with the tree compiler, build both releases.

    Return (exit code, build output path). The exit code is the first non-zero exit, else 0.
    """
    applied = arm_tree.build(arm, tree, orders_beaml=orders_beaml, payments_beaml=payments_beaml)
    save(out / "tree-applied.json", applied)
    commands = Commands(out / "commands")
    http = Path(tree) / HTTP_PATH
    output = out / "build_output.txt"
    exit_code = 0
    stored = EMPTY_SNAPSHOT if arm == "gen" else None
    save(out / "stored-snapshot.json", {"path": str(stored) if stored else None,
                                        "sha256": hashlib.sha256(stored.read_bytes()).hexdigest() if stored else None})
    with output.open("w") as text:
        def step(name, args, cwd):
            nonlocal exit_code
            code, stdout = commands.run(name, args, cwd)
            stderr = (commands.out / (name + ".stderr")).read_text(errors="replace")
            text.write("$ %s  (exit %d)\n%s%s\n" % (" ".join(str(a) for a in args), code,
                                                     stdout if not name.startswith("generate") else "",
                                                     stderr))
            if code and not exit_code:
                exit_code = code
            return code, stdout

        step("deps", MIX + ["deps.get", "--offline"], http)
        for service in ("orders", "payments"):
            if exit_code:
                break
            code, generated = step("generate-" + service,
                                   ["cargo", "run", "--offline", "--quiet", "--manifest-path",
                                    Path(tree) / COMPILER_PATH / "Cargo.toml", "--",
                                    http / ("apps/%s_api/priv/%s.beaml" % (service, service))]
                                   + (["--stored", stored] if service == "orders" and stored else []), tree)
            if code == 0:
                target = http / ("apps/%s_api/lib/generated.ex" % service)
                target.write_text(generated.replace("defmodule BeamlSpike do",
                                                    "defmodule %sBeamlSpike do" % service.title()))
                shutil.copyfile(target, out / ("%s.generated.ex" % service))
        if not exit_code:
            # Strict compile is recorded, not a class input: the class uses the release build.
            code, _ = commands.run("compile-strict", MIX + ["compile", "--force", "--warnings-as-errors"], http)
            text.write("$ mix compile --force --warnings-as-errors  (exit %d, recorded only)\n" % code)
            save(out / "strict-compile.json", {"exit_code": code})
        for service in ("orders", "payments"):
            if exit_code:
                break
            step("release-" + service, MIX + ["release", service, "--overwrite"], http)
    return exit_code, output, commands


def service_env(service, out, payments_port=0):
    return dict(PATH="/usr/bin:/bin:/usr/sbin:/sbin", PROBE_SERVICE=service, PROBE_OUTPUT=str(out),
                PROBE_PAYMENTS_PORT=str(payments_port), PROBE_DROP_CONTEXT="false",
                RELEASE_DISTRIBUTION="none", RELEASE_COOKIE="beaml_synthetic_loopback_test")


def start(tree, service, out, payments_port, holder):
    out.mkdir(parents=True, exist_ok=True)
    for kind in ("spans", "logs"):
        (out / (kind + ".jsonl")).touch()
    log = (out / "process.log").open("wb")
    holder.append(log)
    binary = Path(tree) / HTTP_PATH / "_build/prod/rel" / service / "bin" / service
    process = subprocess.Popen([str(binary), "start"], env=service_env(service, out, payments_port),
                               stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    holder.append(process)
    deadline = time.monotonic() + 30
    while not (out / "ready.json").exists():
        if process.poll() is not None or time.monotonic() > deadline:
            raise RuntimeError("service_not_ready:" + service)
        time.sleep(.05)
    return process, json.loads((out / "ready.json").read_text())["port"]


def proxy(target_port):
    """Loopback proxy in front of Payments. It keeps each exchange (request and response bytes)."""
    exchanges = []

    class Proxy(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers["Content-Length"]))
            headers = {k: v for k, v in self.headers.items() if k.lower() not in ("host", "connection")}
            connection = http.client.HTTPConnection("127.0.0.1", target_port, timeout=10)
            try:
                connection.request("POST", self.path, body=body, headers=headers)
                response = connection.getresponse()
                status, payload = response.status, response.read()
            finally:
                connection.close()
            exchanges.append({"path": self.path, "request": body.decode(errors="replace"), "status": status,
                              "body_base64": base64.b64encode(payload).decode()})
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Proxy)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, exchanges


def probe(tree, arm, name, out, probe_input, payments_port, commands):
    """One eval VM of the Orders release: the arm flow ("flow") or the arm runner ("replay")."""
    out.mkdir(parents=True, exist_ok=True)
    save(out / "input.json", dict(order=ORDER, **probe_input))
    script = EVAL % {"flow": FLOW[arm], "runner": RUNNER[arm]}
    env = dict(service_env("orders", out, payments_port), PROBE_INPUT=str(out / "input.json"))
    binary = Path(tree) / HTTP_PATH / "_build/prod/rel/orders/bin/orders"
    code, text = commands.run("eval-" + name, [binary, "eval", script], REPO, env=env, timeout=120)
    lines = [line[6:] for line in text.splitlines() if line.startswith("PROBE ")]
    report = json.loads(lines[0]) if code == 0 and len(lines) == 1 else {
        "result": {"raised": "eval_exit_%d" % code}, "host_validation": None, "transport": None}
    report["eval_exit_code"] = code
    save(out / "report.json", report)
    return out / "report.json", report


def live_call(tree, arm, out, commands, name="flow"):
    """Start Payments and Orders of the tree, one Orders call through the proxy, then one flow probe."""
    holder = []
    server, exchanges = None, []
    try:
        _, payments_port = start(tree, "payments", out / "payments", 0, holder)
        server, exchanges = proxy(payments_port)
        process, port = start(tree, "orders", out / "orders", server.server_address[1], holder)
        reply = request(port, "/orders", ORDER)
        _, control = request(port)
        stop(process)
        live_exchanges = list(exchanges)
        _, flow = probe(tree, arm, name, out / "flow", {"mode": "flow"}, server.server_address[1], commands)
    finally:
        for item in holder:
            if isinstance(item, subprocess.Popen):
                stop(item)
            else:
                item.close()
        if server is not None:
            server.shutdown()
            server.server_close()
    observed = {"reply": list(reply), "transport": control["count"], "loss": control["capture"]["loss"],
                "exchanges": live_exchanges, "records": rows(out / "orders/responses.jsonl"),
                "spans": rows(out / "orders/spans.jsonl"), "flow_probe": flow}
    save(out / "observed.json", observed)
    return out / "observed.json", observed


# ---------------------------------------------------------------------------------------------- classes

def payment_fields(orders_beaml):
    """Declared fields of the TYPE `Payment` in an orders BEAML file (the drifted TYPE)."""
    match = re.search(r"^type Payment(?: v[1-9][0-9]*)? \{([^}]*)\}", Path(orders_beaml).read_text(), re.M)
    return re.findall(r"(\w+)\s*:\s*String", match.group(1)) if match else []


def body_json(exchange_or_record):
    """The body of a proxy exchange or a LIB record (raw bytes), or the `value` of a GEN record (version 2, DL-105)."""
    if "value" in exchange_or_record:
        return exchange_or_record["value"]
    try:
        return json.loads(base64.b64decode(exchange_or_record["body_base64"]))
    except Exception:
        return None


def fits(value, fields):
    """True when every declared field is present with a String value (the README decode rule)."""
    return isinstance(value, dict) and all(isinstance(value.get(f), str) for f in fields)


def classify_live(observed, fields):
    """new_live. Expected: accept when Payments answered 200 with a body that fits the drifted TYPE."""
    exchange = observed["exchanges"][0] if observed["exchanges"] else None
    sent = body_json(exchange) if exchange else None
    expected_accept = bool(exchange) and exchange["status"] == 200 and fits(sent, fields)
    code, body = observed["reply"][0], observed["reply"][1]
    flow = observed["flow_probe"]["result"]
    if code == 200:
        right = expected_accept and body == {f: sent[f] for f in fields}
        return ("correct_accept" if right else "wrong_accept"), {"expected_accept": expected_accept,
                                                                  "cause": "accepted"}
    if "ok" in flow:
        cause = "host_validation " + str(observed["flow_probe"].get("host_validation"))
        typed = observed["flow_probe"].get("host_validation") not in (None, "ok")
    elif "error" in flow:
        cause, typed = "flow error " + flow["error"], True
    else:
        cause, typed = "flow raised " + str(flow.get("raised") or flow.get("unexpected")), False
    if not typed:
        return "untyped_crash", {"expected_accept": expected_accept, "cause": cause}
    return ("false_reject" if expected_accept else "typed_reject"), {"expected_accept": expected_accept,
                                                                      "cause": cause}


def classify_replay(report, old_record, new_request, fields):
    """pre_change. Expected: accept only when the old record still fits the drifted request and TYPE."""
    old_body = body_json(old_record)
    expected_accept = old_record["request"] == new_request and fits(old_body, fields)
    result = report["result"]
    if "ok" in result:
        right = expected_accept and result["ok"] == {f: old_body[f] for f in fields}
        return ("correct_accept" if right else "wrong_accept"), {"expected_accept": expected_accept}
    if "error" in result:
        return ("false_reject" if expected_accept else "typed_reject"), {"expected_accept": expected_accept}
    return "untyped_crash", {"expected_accept": expected_accept}


# ---------------------------------------------------------------------------------------------- repair

def lib_beaml(drifted):
    """The LIB arm has no `effect` and no `place`: its BEAML is the 0002 orders.beaml. A DRIFT changes the
    same TYPE and signature lines there. Keep each drifted line whose declaration exists in the LIB source,
    plus each new interface; drop the GEN-only lines (effect, failure TYPE, flow, comments).
    Slice 6b step 6a (DL-118): DRIFT no longer calls it. It stays because tests/slice5_rewrite_test.py A1 audits
    its `type ` line test."""
    def key(line):
        return " ".join(line.split()[:2])
    lib = (REPO / arm_tree.ORDERS_BEAML).read_text().splitlines()
    gen = (EXPERIMENT / "arms/gen/orders.beaml").read_text().splitlines()
    lib_keys, gen_keys = {key(l) for l in lib}, {key(l) for l in gen}
    kept = [line for line in Path(drifted).read_text().splitlines()
            if key(line) in lib_keys or (line.startswith("type ") and key(line) not in gen_keys)]
    return "\n".join(kept) + "\n"


def hunks(old, new):
    matcher = difflib.SequenceMatcher(a=old.splitlines(), b=new.splitlines(), autojunk=False)
    return sum(1 for tag, *_ in matcher.get_opcodes() if tag != "equal")


def repair(arm, derivative, tree, out):
    """Apply the repair spec; count hunks per class from the actual file diff. Return the counts."""
    spec_path = EXPERIMENT / "arms" / arm / "repair" / (derivative + ".json")
    spec = json.loads(spec_path.read_text()) if spec_path.is_file() else []
    counts = {"replay": 0, "domain": 0, "test": 0, "files": {}}
    before = {}
    for edit in spec:
        path = Path(tree) / edit["file"]
        before.setdefault(edit["file"], path.read_text())
        text = path.read_text()
        if text.count(edit["old"]) != 1:
            raise RuntimeError("repair %s %s: old text found %d times in %s"
                               % (arm, derivative, text.count(edit["old"]), edit["file"]))
        path.write_text(text.replace(edit["old"], edit["new"]))
    for relative, old in before.items():
        new = (Path(tree) / relative).read_text()
        n = hunks(old, new)
        kind = "domain" if relative in DOMAIN_FILES else "test" if relative in TEST_FILES else "replay"
        counts[kind] += n
        counts["files"][relative] = {"class": kind, "hunks": n}
        target = out / "repair" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("".join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                                       relative, relative)))
    save(out / "repair-counts.json", counts)
    return counts


def repair_releases(edited):
    """Releases whose source the repair edited (RV6A-1). A shared app (probe_support) is in every release."""
    apps = {rel[len(HTTP_PATH + "/apps/"):].split("/")[0] for rel in edited if rel.startswith(HTTP_PATH + "/apps/")}
    # ponytail: an app that is not <service>_api counts as shared by all releases; read mix.exs deps if that changes.
    return [s for s in ("orders", "payments") if s + "_api" in apps or apps - {"orders_api", "payments_api"}]


def repaired_replay(tree, arm, out, commands, edited):
    """D6B-96: rebuild each release the repair touched, make one live call, replay its RESPONSE RECORD."""
    http = Path(tree) / HTTP_PATH
    for service in repair_releases(edited):
        code, _ = commands.run("repair-release-" + service, MIX + ["release", service, "--overwrite"], http)
        if code != 0:
            return {"exit_code": code, "argv": commands.log[-1]["argv"]}
    _, observed = live_call(tree, arm, out / "live", commands, name="repaired-flow")
    if len(observed["records"]) != 1:
        return {"exit_code": None, "records": len(observed["records"])}
    record = observed["records"][0]
    save(out / "record.json", record)
    report_path, report = probe(tree, arm, "repaired-replay", out / "replay",
                                {"mode": "replay", "trace_id": record["trace_id"], "responses": [record]}, 0, commands)
    return {"exit_code": report["eval_exit_code"], "argv": commands.log[-1]["argv"],
            "record": str(out / "record.json"), "report": str(report_path)}


# ---------------------------------------------------------------------------------------------- drift

# D6B-189 (DL-135, M7 option A): the expected GEN classes per derivative (build, new_live, pre_change).
# 58 of 61 retained runs give these rows. A wanted class change moves this pin and drift_test.PIN together.
DRIFT_PIN = {"R": ("correct_accept", "false_reject", "typed_reject"),
             "N": ("correct_accept", "false_reject", "typed_reject"),
             "Q": ("correct_accept", "typed_reject", "typed_reject")}


def drift_status(summary):
    """pass only for a verified freeze, every repair replay green and every GEN row equal to DRIFT_PIN."""
    rows = {d: (summary.get("drift", {}).get(d) or {}).get("gen") or {} for d in DRIFT_PIN}
    ok = (summary.get("freeze", {}).get("status") == "pass" and summary.get("repaired_all") is True
          and all(tuple(rows[d].get(k) for k in ("build", "new_live", "pre_change")) == DRIFT_PIN[d]
                  for d in DRIFT_PIN))
    return "pass" if ok else "fail"


def drift():
    started = utc()
    run = RESULTS / started.strftime("%Y%m%dT%H%M%S%fZ")
    run.mkdir(parents=True)
    event("start", TARGET + "-drift", "running")
    bus("start", msg="DRIFT R, N, Q (GEN rows)", path=str(run))
    summary = {"run": str(run), "status": "fail", "freeze": freeze(), "drift": {}, "baseline": {}}
    if summary["freeze"]["status"] != "pass" or summary["freeze"]["action"] != "verified":
        # DRIFT runs only against a LIB that was frozen before (README "Freeze").
        summary["error"] = "LIB is not frozen before DRIFT"
        save(run / "drift.json", summary)
        event("finish", TARGET + "-drift", "fail")
        bus("error", msg="ERROR LIB: not frozen. Freeze LIB before DRIFT.")
        return summary
    total, done = len(ARMS) * (len(DERIVATIVES) + 1), 0
    with tempfile.TemporaryDirectory(prefix="beaml-0004-drift-") as scratch:
        scratch = Path(scratch)
        # Baseline per arm: the undrifted arm gives the pre-change RESPONSE RECORD.
        for arm in ARMS:
            out = run / arm / "baseline"
            tree = scratch / arm / "baseline"
            code, output, commands = build_tree(arm, tree, out)
            entry = {"build_exit_code": code, "build_output": str(output)}
            if code == 0:
                report, observed = live_call(tree, arm, out / "live", commands)
                entry.update(report=str(report), reply=observed["reply"], records=len(observed["records"]))
                if len(observed["records"]) == 1:
                    save(out / "record.json", observed["records"][0])
                    entry["record"] = str(out / "record.json")
            summary["baseline"][arm] = entry
            done += 1
            bus("progress", pct=100.0 * done / total, step="baseline %s" % arm)
            event("step", "baseline-" + arm, "pass" if entry.get("record") else "fail")
            shutil.rmtree(tree, ignore_errors=True)
        for derivative in DERIVATIVES:
            source = EXPERIMENT / "drift" / derivative
            for arm in ARMS:
                out = run / derivative / arm
                out.mkdir(parents=True)
                orders = source / "orders.beaml"
                shutil.copyfile(orders, out / "orders.applied.beaml")
                shutil.copyfile(source / "payments.beaml", out / "payments.applied.beaml")
                tree = scratch / derivative / arm
                code, output, commands = build_tree(arm, tree, out, orders_beaml=orders,
                                                    payments_beaml=source / "payments.beaml")
                row = {"evidence": {"build_output": str(output), "build_exit_code": code}, "notes": {}}
                fields = payment_fields(orders)
                if code != 0:
                    row.update(build="compile_error", new_live="compile_error", pre_change="compile_error")
                else:
                    row["build"] = "correct_accept"  # a consistent BEAML change builds: the build accepts it
                    report, observed = live_call(tree, arm, out / "new_live", commands)
                    row["evidence"]["new_live_report"] = str(report)
                    row["new_live"], row["notes"]["new_live"] = classify_live(observed, fields)
                    old = json.loads(Path(summary["baseline"][arm]["record"]).read_text())
                    new_request = (json.loads(observed["exchanges"][0]["request"]) if observed["exchanges"]
                                   else None)
                    replay_path, replay = probe(tree, arm, "pre-change", out / "pre_change",
                                                {"mode": "replay", "trace_id": old["trace_id"],
                                                 "responses": [old]}, 0, commands)
                    row["evidence"]["pre_change_replay_report"] = str(replay_path)
                    row["pre_change"], row["notes"]["pre_change"] = classify_replay(replay, old, new_request, fields)
                    row["notes"]["pre_change"]["host_validation"] = replay.get("host_validation")
                counts = repair(arm, derivative, tree, out)
                row["manual_change_sites"] = counts["replay"]
                row["domain_validation_sites"] = counts["domain"]
                row["test_expectation_sites"] = counts["test"]
                if code == 0:
                    # Repairs do not touch BEAML, but they change probe_support.ex: rebuild its releases (D6B-96).
                    row["repaired"] = repaired_replay(tree, arm, out / "repaired", commands, counts["files"])
                save(out / "row.json", row)
                summary["drift"].setdefault(derivative, {})[arm] = row
                done += 1
                bus("progress", pct=100.0 * done / total, step="DRIFT-%s %s" % (derivative, arm))
                event("step", "drift-%s-%s" % (derivative, arm), row["build"],
                      new_live=row["new_live"], pre_change=row["pre_change"],
                      sites=row["manual_change_sites"])
                shutil.rmtree(tree, ignore_errors=True)
    summary["sites"] = {arm: sum(summary["drift"][d][arm]["manual_change_sites"] for d in DERIVATIVES)
                        for arm in ARMS}
    summary["replay_lines"] = replay_lines()
    repaired = all(summary["drift"][d][a].get("repaired", {}).get("exit_code") == 0
                   for d in DERIVATIVES for a in ARMS if summary["drift"][d][a]["build"] != "compile_error")
    summary["repaired_all"] = repaired
    summary["status"] = drift_status(summary)
    save(run / "drift.json", summary)
    event("finish", TARGET + "-drift", summary["status"], repaired_all=repaired)
    bus("artifact", path=str(run))
    bus("done", msg="DRIFT: %s" % summary["status"], meta={"sites": summary["sites"], "repaired_all": repaired})
    return summary


def replay_lines():
    """Host lines that exist only for replay (README). Generated and compiler lines are not host lines."""
    lib_root = EXPERIMENT / "arms/lib/overlay" / HTTP_PATH
    counts = {"lib": {name: len((lib_root / rel).read_text().splitlines()) for name, rel in LIB_MODULES.items()}}
    transport = (lib_root / "apps/orders_api/lib/orders_api/payment_http.ex").read_text()
    counts["lib"]["ReplayLib.record call"] = transport.count("ReplayLib.record(")
    router = (EXPERIMENT / "arms/gen/overlay" / HTTP_PATH / "apps/orders_api/lib/orders_api/router.ex").read_text()
    counts["gen"] = {"router replay lines": len([l for l in router.splitlines() if "Replay" in l or "record" in l])}
    counts["compiler_main_rs_lines"] = len((REPO / COMPILER_PATH / "src/main.rs").read_text().splitlines())
    return counts


# ---------------------------------------------------------------------------------------------- all

def execute():
    started = utc()
    run = RESULTS / started.strftime("%Y%m%dT%H%M%S%fZ")
    run.mkdir(parents=True)
    result = {"command": [sys.executable] + sys.argv, "started_at": started.isoformat(), "steps": [],
              "status": "fail"}
    event("start", TARGET, "running")
    bus("start", msg="all steps", path=str(run))
    for index, (name, argv) in enumerate(STEPS):
        step = {"name": name, "command": argv, "exit_code": None, "status": "fail"}
        result["steps"].append(step)
        with (run / (name + ".stdout")).open("wb") as out, (run / (name + ".stderr")).open("wb") as err:
            try:
                step["exit_code"] = subprocess.run(argv, cwd=str(REPO), stdout=out, stderr=err).returncode
            except Exception as error:
                err.write(("runner: %s: %s\n" % (type(error).__name__, error)).encode())
        step["status"] = "pass" if step["exit_code"] == 0 else "fail"
        lines = (run / (name + ".stdout")).read_text(errors="replace").strip().splitlines()
        if name in ("drift", "lib-freeze") and lines:
            try:
                step["summary"] = json.loads(lines[-1])
            except ValueError:
                pass
        save(run / "result.json", result)
        event("step", name, step["status"])
        bus("progress", pct=100.0 * (index + 1) / len(STEPS), step=name)
    result["status"] = "pass" if all(s["status"] == "pass" for s in result["steps"]) else "fail"
    result["finished_at"] = utc().isoformat()
    save(run / "result.json", result)
    event("finish", TARGET, result["status"])
    bus("artifact", path=str(run))
    bus("done", msg="all steps: %s" % result["status"])
    return run, result


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    arguments = sys.argv[1:]
    if arguments == ["--list-steps"]:
        print(json.dumps({"steps": [{"name": n, "command": c} for n, c in STEPS]}))
        raise SystemExit(0)
    if arguments == ["freeze"]:
        outcome = freeze()
        event("freeze", TARGET, outcome["status"])
        print(json.dumps(outcome))
        raise SystemExit(0 if outcome["status"] == "pass" else 1)
    if arguments == ["drift"]:
        outcome = drift()
        print(json.dumps({"run": outcome["run"], "status": outcome["status"], "drift": outcome["drift"],
                          "sites": outcome.get("sites"), "repaired_all": outcome.get("repaired_all")}))
        raise SystemExit(0 if outcome["status"] == "pass" else 1)
    if arguments:
        print(json.dumps({"status": "usage", "arguments": arguments}))
        raise SystemExit(2)
    run, result = execute()
    print(json.dumps({"run": str(run), "status": result["status"]}))
    raise SystemExit(0 if result["status"] == "pass" else 1)

"""Independent TEST of gate 3 (CAPTURE and transport observer), EXPERIMENT 0003. Run from repo root."""
import base64, datetime, hashlib, json, re, shutil, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude-bus"))
try:
    from cbus import post
except Exception:
    def post(**_): pass

REPO = Path.cwd()
EXP = REPO / "experiments/0003-source-linked-replay"
HTTP = REPO / "experiments/0002-http-correlation"
LEDGER = EXP / "workflow/2026-11-05/capture"
CHANGED = "experiments/0002-http-correlation/apps/orders_api/lib/orders_api/payment_http.ex"
JOB = "beaml-0003-capture-test"
TESTS = {
    "response_capture_test.py": "da92ade2d614b83905f4f928988855bc5b92a585b17290c70964c61f801626fc",
    "trace_lookup_test.py": "6a7036195cc3025c252caa2cbe6ac4c9f13f78996752272249f0b5a6168b9ebe",
    "trace_lookup_repair_test.py": "5f83aa891c974c01179921ba2c27fd1b6b0f77c54a4de63ccf6641029b134804",
}
PAYMENT = {"order_id": "order-1", "status": "authorized"}
FIELDS = {"version", "trace_id", "client_span_id", "artifact_id", "operation", "attempt", "request", "status",
          "body_base64", "body_length", "body_sha256"}

now = datetime.datetime.now(datetime.timezone.utc)
out = EXP / "results" / now.strftime("%Y%m%dT%H%M%S%fZ")
out.mkdir(parents=True)
log_lines, checks, commands = [f"# Independent TEST of CAPTURE and transport observer, {now.isoformat()}"], {}, {}


def say(text):
    print(text, flush=True)
    log_lines.append(text)


def event(action, target, result):
    row = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(), "source": "cli", "action": action,
           "target": target, "result": result, "use_case": "0003-capture-independent-test"}
    try:
        (REPO / ".beaml").mkdir(exist_ok=True)
        with open(REPO / ".beaml/actions.jsonl", "a") as f:
            f.write(json.dumps(row) + "\n")
    except Exception:
        pass


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(name, cmd, cwd=REPO):
    commands[name] = {"command": [str(c) for c in cmd], "cwd": str(Path(cwd).relative_to(REPO)) or "."}
    say(f"$ (cwd {commands[name]['cwd']}) {' '.join(commands[name]['command'])}")
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    (out / f"{name}.stdout").write_text(p.stdout)
    (out / f"{name}.stderr").write_text(p.stderr)
    say(f"exit {p.returncode}")
    return p


def record(name, ok, **detail):
    checks[name] = {**detail, "pass": bool(ok)}
    say(f"CHECK {name}: {'pass' if ok else 'FAIL'}")
    event("pass" if ok else "fail", name, "ok" if ok else "check_failed")


def verify_output_hashes(run_dir):
    hashes = json.loads((run_dir / "output-hashes.json").read_text())
    bad = [p for p, h in hashes.items() if not (run_dir / p).is_file() or sha(run_dir / p) != h]
    return len(hashes), bad


post(job=JOB, kind="progress", pct=0, step="hashes", title="Test the CAPTURE and transport observer (EXPERIMENT 0003)")
event("start", "0003-capture-independent-test", "running")

# 1. Test hashes
actual = {name: sha(EXP / "tests" / name) for name in TESTS}
record("test_sha256_unchanged", actual == TESTS, expected=TESTS, actual=actual)

# 2. Capture test
post(job=JOB, kind="progress", pct=10, step="capture test")
p = run("capture", [sys.executable, "-B", "experiments/0003-source-linked-replay/tests/response_capture_test.py"])
capture_run = Path(p.stdout.splitlines()[0]) if p.stdout.strip() else None
record("response_capture_test", p.returncode == 0, exit_code=p.returncode,
       run=str(capture_run.relative_to(REPO)) if capture_run else None)

# 3. Lookup test
post(job=JOB, kind="progress", pct=35, step="lookup test")
p = run("lookup", [sys.executable, "-B", "experiments/0003-source-linked-replay/tests/trace_lookup_test.py"])
lookup_run = Path(p.stdout.splitlines()[0]) if p.stdout.strip() else None
record("trace_lookup_test", p.returncode == 0, exit_code=p.returncode,
       run=str(lookup_run.relative_to(REPO)) if lookup_run else None)

# 4. Repair test on the fresh lookup run (owner decision B)
post(job=JOB, kind="progress", pct=55, step="repair test")
src = str(lookup_run.relative_to(REPO)) if lookup_run else "MISSING"
p = run("repair", [sys.executable, "-B", "experiments/0003-source-linked-replay/tests/trace_lookup_repair_test.py",
                   "--source-run", src])
repair_run = Path(p.stdout.splitlines()[0]) if p.stdout.strip() and p.stdout.splitlines()[0].startswith("/") else None
record("trace_lookup_repair_test_fresh_source", p.returncode == 0, exit_code=p.returncode, source_run=src,
       run=str(repair_run.relative_to(REPO)) if repair_run else None)

# 5. 0002 unit tests: same discovery as earlier gates, plus the GREEN worker command for comparison
post(job=JOB, kind="progress", pct=65, step="0002 unit tests")
p = run("0002-unittest-discover", [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"], HTTP)
ran = re.search(r"Ran (\d+) test", p.stderr)
discover_names = re.findall(r"^(test_\w+) \((\S+)\)", p.stderr, re.M)
p6 = run("0002-test-query-only", [sys.executable, "-B", "tests/test_query.py"], HTTP)
ran6 = re.search(r"Ran (\d+) test", p6.stderr)
n, n6 = int(ran.group(1)) if ran else None, int(ran6.group(1)) if ran6 else None
by_module = {}
for _, cls in discover_names:
    by_module[cls.split(".")[0]] = by_module.get(cls.split(".")[0], 0) + 1
record("0002_unit_tests", p.returncode == 0 and n == 8, exit_code=p.returncode, ran=n, by_module=by_module,
       test_query_only={"exit_code": p6.returncode, "ran": n6},
       explanation="discover runs test_query.py (6) and test_runner.py (2); GREEN ran only test_query.py")

# 6. Format, warnings, whitespace
post(job=JOB, kind="progress", pct=75, step="format and warnings")
p = run("0002-format", ["mix", "format", "--check-formatted", "apps/orders_api/lib/orders_api/payment_http.ex"], HTTP)
record("elixir_format_changed_file", p.returncode == 0, exit_code=p.returncode)
warn = {}
for r in (capture_run, lookup_run, repair_run):
    if r:
        for f in sorted(r.rglob("*.std*")):
            if "warning" in f.read_text(errors="replace").lower():
                warn[str(f.relative_to(REPO))] = True
builds = sorted(str(f.relative_to(REPO)) for r in (capture_run, lookup_run) if r for f in r.glob("release-*.std*"))
record("release_builds_no_warnings", builds and not warn, release_logs=builds, files_with_warning=sorted(warn))
tracked = run("git-diff-check", ["git", "diff", "--check", "--", CHANGED])
untracked = subprocess.run(["git", "ls-files", "--error-unmatch", CHANGED], cwd=REPO, capture_output=True).returncode != 0
noindex = run("git-diff-check-no-index", ["git", "diff", "--no-index", "--check", "/dev/null", CHANGED])
record("git_diff_check_changed_file", tracked.returncode == 0 and not noindex.stdout.strip(),
       tracked_exit=tracked.returncode, file_untracked=untracked,
       no_index_exit=noindex.returncode, no_index_whitespace_errors=noindex.stdout.strip() or None,
       note="0002 is untracked; plain git diff --check sees no diff, so the file was also checked against /dev/null")

# 7. Retained response records
post(job=JOB, kind="progress", pct=85, step="response records")
rec = {"run": str(capture_run.relative_to(REPO)) if capture_run else None}
ok = False
try:
    result = json.loads((capture_run / "result.json").read_text())
    receipts = result["baseline"]["receipts"]
    manifest = json.loads((capture_run / "original/manifest.json").read_text())
    artifact = manifest["artifacts"]["orders"]["beam_hash"]
    spans = [json.loads(l) for l in (capture_run / "orders/spans.jsonl").read_text().splitlines()]
    clients = {s["trace_id"]: s["span_id"] for s in spans if s["name"] == "orders.payment_http"}
    live = [json.loads(l) for l in (capture_run / "orders/responses.jsonl").read_text().splitlines()]
    kept = [json.loads(l) for l in (capture_run / "original/orders.responses.jsonl").read_text().splitlines()]
    per = []
    for i, (r, receipt) in enumerate(zip(live, receipts)):
        raw = base64.b64decode(r["body_base64"], validate=True)
        per.append({
            "receipt": receipt["call"], "fields_exact": set(r) == FIELDS,
            "trace": r["trace_id"] == receipt["trace_id"],
            "client_span": r["client_span_id"] == clients.get(receipt["trace_id"]),
            "artifact": r["artifact_id"] == artifact,
            "operation_attempt_version": (r["operation"], r["attempt"], r["version"]) == ("payments.authorize", 1, 1),
            "request": r["request"] == {"order_id": "order-1"}, "status": r["status"] == 200,
            "length": r["body_length"] == len(raw) and 1 <= len(raw) <= 1024,
            "sha256": r["body_sha256"] == hashlib.sha256(raw).hexdigest(),
            "body_json_matches_receipt": json.loads(raw) == receipt["body"] == PAYMENT,
            "body_length_value": len(raw), "body_sha256_value": r["body_sha256"],
        })
    rec.update(records=len(live), receipts=len(receipts), retained_copy_equal=live == kept,
               distinct_client_spans=len({r["client_span_id"] for r in live}) == len(live), per_record=per,
               observer_control_records=len((capture_run / "observer-control/responses.jsonl").read_text().splitlines())
               if (capture_run / "observer-control/responses.jsonl").exists() else 0)
    ok = (len(live) == len(receipts) == 2 and live == kept and rec["distinct_client_spans"]
          and rec["observer_control_records"] == 0
          and all(all(v for k, v in x.items() if not k.endswith("_value") and k != "receipt") for x in per))
except Exception as e:
    rec["error"] = repr(e)
record("response_records_per_receipt", ok, **rec)

# Output hashes of the fresh runs
hs = {}
for r in (capture_run, lookup_run, repair_run):
    if r:
        count, bad = verify_output_hashes(r)
        hs[r.name] = {"files": count, "mismatch": bad}
record("result_output_hashes_verified", hs and all(not v["mismatch"] for v in hs.values()) and len(hs) == 3, runs=hs)

tool = {}
for name, cmd in {"python3": [sys.executable, "--version"], "elixir": ["elixir", "--short-version"],
                  "mix": ["mix", "--version"], "git": ["git", "--version"]}.items():
    q = subprocess.run(cmd, capture_output=True, text=True)
    tool[name] = (q.stdout + q.stderr).strip().splitlines()[-1]
status = "pass" if all(c["pass"] for c in checks.values()) else "fail"
summary = {
    "experiment": "0003-source-linked-replay", "phase": "response-capture-and-transport-observer-independent-test",
    "status": status, "runner": "fresh Claude Opus 5.5 subagent; owner chose this instead of GPT-6.1 Sol",
    "production_sha256": {CHANGED: sha(REPO / CHANGED)}, "toolchain": tool, "checks": checks,
    "out_of_scope": ["replay run", "invalid replay records", "malformed service parser crash"],
    "result_dir": str(out.relative_to(REPO)),
}
(out / "commands.json").write_text(json.dumps(commands, indent=2) + "\n")
(out / "toolchain.json").write_text(json.dumps(tool, indent=2) + "\n")
(out / "input-hashes.json").write_text(json.dumps({"tests": actual, "production": {CHANGED: sha(REPO / CHANGED)},
                                                   "tester": sha(__file__)}, indent=2) + "\n")
shutil.copyfile(__file__, out / "tester.py")
(out / "result.json").write_text(json.dumps(summary, indent=2) + "\n")
say(f"STATUS {status}")
(out / "test.log").write_text("\n".join(log_lines) + "\n")
(out / "output-hashes.json").write_text(json.dumps(
    {str(f.relative_to(out)): sha(f) for f in sorted(out.rglob("*")) if f.is_file()}, indent=2) + "\n")
(LEDGER / "test-result.json").write_text(json.dumps({**summary, "result_dir": "../../../results/" + out.name}, indent=2) + "\n")
(LEDGER / "test-output.log").write_text("\n".join(log_lines) + "\n")
event("pass" if status == "pass" else "fail", "0003-capture-independent-test", status)
for f in (out / "result.json", LEDGER / "test-result.json", LEDGER / "test-output.log"):
    post(job=JOB, kind="artifact", path=str(f))
post(job=JOB, kind="done", meta={"status": status}, msg=f"RUN capture test: {status}", title="Test the CAPTURE and transport observer (EXPERIMENT 0003)")
sys.exit(0 if status == "pass" else 1)

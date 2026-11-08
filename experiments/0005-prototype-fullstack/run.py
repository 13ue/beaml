"""Repeatable command for EXPERIMENT 0005 (PROTOTYPE: Postgres, BEAML, LiveView).

python3 -B run.py [run] | db-up | db-down | db-reset | smoke

`run` (the default) needs a database that is up (db-up). It never starts or stops it. Steps: the compiler
(BEAML_SPIKE or a cargo build of 0001), db-reset, stored + gen of app/beaml/orders.beaml (a live ROW SNAPSHOT by
`mix beaml.stored`, Q5-4 B, then the compiler with --stored), compile, the N-TESTS in mix test, then the phases n8,
n7_seed, gen order_v2, n7_read, and gen orders.beaml again. Every step runs and is recorded; one failed step fails the run.
The run also fails unless every N-TEST of EXPECTED passes (N9 blocked) and the order_v2 snapshot holds 2 rows, no DEAD LINE.

Every call writes results/<UTC>/ with commands, toolchain versions and result.json.
The database is a local pg_ctl cluster: trust auth, Unix socket only, no password (P5-01, P5-02, P5-22, P5-23).
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

EXPERIMENT = Path(__file__).resolve().parent
REPO = EXPERIMENT.parents[1]
APP = EXPERIMENT / "app"
PGDATA, PGSOCK = APP / ".pgdata", APP / ".pgsock"
DATABASES = ["proto_dev", "proto_test"]
ACTIONS = REPO / ".beaml" / "actions.jsonl"
GENERATED = APP / "lib" / "generated" / "orders.ex"
BEAML = APP / "beaml"
COMPILER = REPO / "experiments" / "0001-syntax-to-beam"
TITLES = {"run": "Run the N-TESTS of the PROTOTYPE (EXPERIMENT 0005)"}
TITLE = "Build the host scaffold of the PROTOTYPE (EXPERIMENT 0005)"

sys.path.insert(0, str(Path.home() / ".claude-bus"))
try:
    from cbus import post
except Exception:
    def post(*_, **__):
        pass


def utc():
    return datetime.datetime.now(datetime.timezone.utc)


def event(use_case, action, target, result):
    """One action event per step. Never values, never paths of inputs."""
    try:
        ACTIONS.parent.mkdir(parents=True, exist_ok=True)
        with ACTIONS.open("a") as out:
            out.write(json.dumps({"ts": utc().isoformat(), "source": "cli", "use_case": use_case,
                                  "action": action, "target": target, "result": result}) + "\n")
    except Exception:
        pass


def version(argv):
    try:
        out = subprocess.run(argv, capture_output=True, text=True, timeout=60)
        return (out.stdout + out.stderr).strip().splitlines()[-1]
    except Exception as error:
        return "unavailable: %s" % type(error).__name__


def toolchain():
    return {"python": platform.python_version(),
            "elixir": version(["elixir", "--version"]),
            "otp": version(["erl", "-noshell", "-eval",
                            "io:format(\"~s~n\", [erlang:system_info(otp_release)]), halt()."]),
            "pg_ctl": version(["pg_ctl", "--version"])}


def pg_running():
    return subprocess.run(["pg_ctl", "-D", str(PGDATA), "status"], capture_output=True).returncode == 0


def db_up():
    steps = []
    if not (PGDATA / "PG_VERSION").is_file():
        steps.append(("initdb", ["initdb", "-D", str(PGDATA), "-U", "proto", "--auth=trust"]))
    if not pg_running():
        PGSOCK.mkdir(exist_ok=True)
        opts = "-k %s -c listen_addresses='' -c unix_socket_permissions=0700" % PGSOCK
        steps.append(("pg-start", ["pg_ctl", "-D", str(PGDATA), "-o", opts, "-l", str(PGDATA / "log"),
                                   "-w", "start"]))
    return steps


def db_down():
    return [("pg-stop", ["pg_ctl", "-D", str(PGDATA), "-m", "fast", "-w", "stop"])] if pg_running() else []


def db_reset():
    return [("truncate-" + db, ["psql", "-h", str(PGSOCK), "-U", "proto", "-d", db, "-v", "ON_ERROR_STOP=1",
                                "-c", "TRUNCATE records RESTART IDENTITY"]) for db in DATABASES]


# compile first: ecto.create compiles too, and a second compile would hide every warning.
SMOKE = [("compile", ["mix", "compile", "--warnings-as-errors"]),
         ("ecto-create", ["mix", "ecto.create"]),
         ("ecto-migrate", ["mix", "ecto.migrate"]),
         ("test", ["mix", "test", "--warnings-as-errors"])]


def lazy_html_nif():
    """P5-24: record the NIF download, source URL and sha256 only."""
    cache = Path.home() / "Library" / "Caches" / "elixir_make"
    lock = (APP / "mix.lock").read_text()
    ver = lock.split('"lazy_html": {:hex, :lazy_html, "', 1)[1].split('"', 1)[0]
    found = []
    for path in sorted(cache.glob("lazy_html-nif-*-%s.tar.gz" % ver)):
        found.append({"file": path.name,
                      "source_url": "https://github.com/dashbitco/lazy_html/releases/download/v%s/%s" % (ver, path.name),
                      "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return found


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def source(variant):
    return BEAML / "orders.beaml" if variant is None else BEAML / "variants" / variant / "orders.beaml"


def phase(name):
    # --seed 0 keeps the definition order inside a phase file (N7 before N7b before N11).
    return ("test-" + name, ["mix", "test", "--warnings-as-errors", "--only", "phase:" + name, "--seed", "0"])


def main(command):
    if os.environ.get("DATABASE_URL") is not None:
        # P5-02: a set DATABASE_URL makes every step an OWNER step. Never read or print it.
        print("ERROR DATABASE: DATABASE_URL is set. The OWNER runs this step.", file=sys.stderr)
        return 2
    use_case = "exp0005-" + command
    started = utc()
    run = EXPERIMENT / "results" / started.strftime("%Y%m%dT%H%M%S%fZ")
    capture = run / "capture"
    capture.mkdir(parents=True)
    env = dict(os.environ, BEAML_CAPTURE_DIR=str(capture))
    result = {"command": [sys.executable] + sys.argv, "subcommand": command, "started_at": started.isoformat(),
              "finished_at": None, "toolchain": toolchain(), "steps": [], "status": "fail"}
    JOB = "exp0005-" + command
    post(JOB, "start", title=TITLES.get(command, TITLE), msg="RUN %s: started" % command)
    event(use_case, "start", command, "running")

    def execute(name, argv, cwd, stdout=None):
        step = {"name": name, "command": [str(a) for a in argv], "exit_code": None, "status": "fail"}
        result["steps"].append(step)
        with (stdout or run / (name + ".stdout")).open("wb") as out, (run / (name + ".stderr")).open("wb") as err:
            try:
                step["exit_code"] = subprocess.run([str(a) for a in argv], cwd=cwd, env=env, stdout=out,
                                                   stderr=err).returncode
            except Exception as error:
                err.write(("runner: %s\n" % type(error).__name__).encode())
        step["status"] = "pass" if step["exit_code"] == 0 else "fail"
        event(use_case, "step", name, step["status"])
        (run / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        return step["status"] == "pass"

    def gen(variant):
        """stored + gen: a live ROW SNAPSHOT, then the compiler. lib/generated/orders.ex changes only on exit 0."""
        label = variant or "orders"
        snap = run / ("stored-" + label)
        out = run / ("gen-" + label + ".ex")
        hashes = {"step": "gen-" + label, "source": str(source(variant).relative_to(EXPERIMENT)),
                  "source_sha256": sha256(source(variant)), "output_sha256": None, "written": False}
        result["hashes"].append(hashes)
        if not execute("stored-" + label, ["mix", "beaml.stored", snap], APP):
            execute("gen-" + label, ["false"], APP)  # recorded as failed: no snapshot, no build
            return False
        ok = execute("gen-" + label, [env["BEAML_SPIKE"], source(variant), "--stored", snap / "responses.jsonl"],
                     APP, stdout=out)
        if ok:
            GENERATED.parent.mkdir(exist_ok=True)
            GENERATED.write_bytes(out.read_bytes())
        hashes.update(output_sha256=sha256(out), written=ok)
        return ok

    def run_all():
        if not (pg_running() and PGSOCK.is_dir()):
            print("ERROR DATABASE: not reachable at app/.pgsock. Run run.py db-up.", file=sys.stderr)
            execute("database", ["false"], EXPERIMENT)
            return False
        result["hashes"] = []
        original = GENERATED.read_bytes() if GENERATED.is_file() else None
        if not os.environ.get("BEAML_SPIKE"):
            execute("cargo-build", ["cargo", "build", "-q"], COMPILER)
            env["BEAML_SPIKE"] = str(COMPILER / "target" / "debug" / "beaml-spike")
        env.update(BEAML_RUN_DIR=str(run), MIX_ENV="test")
        result["compiler"] = {"path": env["BEAML_SPIKE"], "sha256": sha256(Path(env["BEAML_SPIKE"]))}
        oks = []
        try:
            plan = [lambda: all(execute(n, a, EXPERIMENT) for n, a in db_reset()),
                    lambda: gen(None),
                    lambda: execute("compile", ["mix", "compile", "--force", "--warnings-as-errors"], APP),
                    lambda: execute("test", ["mix", "test", "--warnings-as-errors"], APP),
                    lambda: execute(*phase("n8"), APP),
                    lambda: execute(*phase("n7_seed"), APP),
                    lambda: gen("order_v2"),
                    lambda: execute("compile-order_v2", ["mix", "compile", "--force", "--warnings-as-errors"], APP),
                    lambda: execute(*phase("n7_read"), APP),
                    lambda: all(execute(n, a, EXPERIMENT) for n, a in db_reset())]
            for i, step in enumerate(plan, 1):
                post(JOB, "progress", pct=100.0 * (i - 1) / len(plan), step="step %d/%d" % (i, len(plan)),
                     msg="RUN run: running (STEP %d/%d)" % (i, len(plan)))
                oks.append(step())
        finally:
            # Leave the checked-in module of orders.beaml (Q5-5 A); restore the old bytes when that gen fails.
            if not gen(None):
                if original is None:
                    GENERATED.unlink(missing_ok=True)
                else:
                    GENERATED.write_bytes(original)
        result["use_cases"] = use_cases(run)
        result["acceptance"] = acceptance(run, result["use_cases"])
        counts = {}
        for c in result["use_cases"]:
            key = c["result"].split(":")[0]
            counts[key] = counts.get(key, 0) + 1
        result["use_case_counts"] = counts
        return all(oks) and result["steps"][-1]["status"] == "pass" and not result["acceptance"]

    try:
        if command == "run":
            ok = run_all()
        elif command == "smoke":
            plan = [(n, a, EXPERIMENT) for n, a in db_up()] + [(n, a, APP) for n, a in SMOKE]
            ok = True
            for i, (name, argv, cwd) in enumerate(plan, 1):
                post(JOB, "progress", pct=100.0 * (i - 1) / len(plan), step="%s %d/%d" % (name, i, len(plan)),
                     msg="RUN smoke: running (STEP %d/%d)" % (i, len(plan)))
                if not execute(name, argv, cwd):
                    ok = False
                    break
            result["lazy_html_nif"] = lazy_html_nif()
            # The smoke run owns the cluster lifecycle: stop it also after a failure.
            for name, argv in db_down():
                ok = execute(name, argv, EXPERIMENT) and ok
        else:
            steps = {"db-up": db_up, "db-down": db_down, "db-reset": db_reset}[command]()
            ok = all(execute(name, argv, EXPERIMENT) for name, argv in steps)
        result["status"] = "pass" if ok else "fail"
    except Exception as error:
        result["error"] = type(error).__name__
    finally:
        result["finished_at"] = utc().isoformat()
        (run / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        event(use_case, "finish", command, result["status"])
        post(JOB, "artifact", path=str(run), msg="RUN %s: result directory" % command)
        if result["status"] != "pass":
            post(JOB, "error", msg="ERROR RUN %s: a step failed. Read result.json." % command)
        post(JOB, "done", msg="RUN %s: %s" % (command, result["status"]),
             meta={"status": result["status"], "steps": len(result["steps"])})
    print(json.dumps({"run": str(run), "status": result["status"]}))
    return 0 if result["status"] == "pass" else 1


# RED repair O2: the acceptance set (plan.md "Acceptance"). Every pair must pass; only N9 is blocked.
BLOCKED = {"N9": "blocked: fate slice (D036)"}
EXPECTED = {("exp0005-" + u, "test " + t) for u, t in [
    ("N1", "N1 orders.beaml generates the module Orders and the host builds without a warning"),
    ("N2", "N2 a form submit writes one Order row through db.put"),
    ("N2c", "N2c the reason of the row is a JSON null"),
    ("N3", "N3 the submit writes one ENTRY RECORD and one db record with one trace"),
    ("N4", "N4 a constructor reject writes no row and no db record"),
    ("N4", "N4 an unknown channel is accepted and stored as its text"),
    ("N5", "N5 the list page shows both orders through db.list, newest first"),
    ("N6", "N6 an Unknown channel lists as its text"),
    ("N7", "N7 order_v2 builds against a live Order v1 row and a Note v1 row"),
    ("N7", "N7 the v1 Order row lists through the MIGRATE CHAIN with note empty and stays version 1"),
    ("N7", "N7 the v1 row lists through the MIGRATE CHAIN with tag empty and stays version 1"),
    ("N7b", "N7b a submit under v2 writes a version 2 row and the list shows v1 and v2"),
    ("N7b", "N7b a place submit under v2 writes a version 2 Order row and the list shows v1 and v2"),
    ("N8", "N8 a stricter Amount blocks the build against the live row and prints no stored value"),
    ("N8", "N8 control: the same live row builds under orders.beaml"),
    ("N8b", "N8b the stricter build passes after the row is deleted by SQL"),
    ("N8c", "N8c the snapshot holds exactly the live row ids of this instant"),
    ("N9", "N9 quarantine amount frees the stricter build and the list omits order-zero"),
    ("N10", "N10 a removed ui.place line stops the host build at Orders.ui_place/1"),
    ("N11", "N11 a TYPE change reached the table and the DDL did not move"),
    ("N12", "N12 the host writes one action event per action and no value"),
    ("N13", "N13 git holds no database dir, no env file and no secret literal in config or lib")]}


def acceptance(run, cases):
    """The use-case set and run.py's own pre-gen-order_v2 snapshot. Returns problems: counts and names, no values."""
    got = {(c["use_case"], c["test"]): c["result"] for c in cases}
    problems = ["missing: " + "; ".join(sorted(u for u, _ in EXPECTED - set(got)))] if EXPECTED - set(got) else []
    problems += ["unexpected: " + u for u, _ in sorted(set(got) - EXPECTED)]
    problems += ["%s: %s" % (u, r) for (u, t), r in sorted(got.items())
                 if (u, t) in EXPECTED and r != BLOCKED.get(u[len("exp0005-"):], "pass")]
    meta, err = run / "stored-order_v2" / "snapshot-meta.json", run / "gen-order_v2.stderr"
    try:
        if json.loads(meta.read_text())["row_count"] != 2:
            problems.append("stored-order_v2: row_count is not 2")
    except Exception as error:
        problems.append("stored-order_v2: no snapshot-meta (%s)" % type(error).__name__)
    if not err.is_file() or "DEAD LINE" in err.read_text():
        problems.append("gen-order_v2: no stderr or a DEAD LINE")
    return problems


def use_cases(run):
    """Last finish event per N-TEST use case and test: pass, fail: <kind> or blocked: <reason> (N9)."""
    finished = {}
    path = run / "use-cases.jsonl"
    for line in path.read_text().splitlines() if path.is_file() else []:
        e = json.loads(line)
        if e["action"] == "finish":
            finished[(e["use_case"], e["target"])] = e["result"]
    return [{"use_case": u, "test": t, "result": r} for (u, t), r in sorted(finished.items())]


if __name__ == "__main__":
    args = sys.argv[1:] or ["run"]
    if len(args) != 1 or args[0] not in ("run", "db-up", "db-down", "db-reset", "smoke"):
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(args[0]))

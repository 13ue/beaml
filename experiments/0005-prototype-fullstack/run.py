"""Repeatable command for EXPERIMENT 0005 (host scaffold).

python3 -B run.py db-up | db-down | db-reset | smoke

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
JOB = "scaffold-exp0005"
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
    post(JOB, "start", title=TITLE, msg="RUN %s: started" % command)
    event(use_case, "start", command, "running")

    def execute(name, argv, cwd):
        step = {"name": name, "command": argv, "exit_code": None, "status": "fail"}
        result["steps"].append(step)
        with (run / (name + ".stdout")).open("wb") as out, (run / (name + ".stderr")).open("wb") as err:
            try:
                step["exit_code"] = subprocess.run(argv, cwd=cwd, env=env, stdout=out, stderr=err).returncode
            except Exception as error:
                err.write(("runner: %s\n" % type(error).__name__).encode())
        step["status"] = "pass" if step["exit_code"] == 0 else "fail"
        event(use_case, "step", name, step["status"])
        (run / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        return step["status"] == "pass"

    try:
        if command == "smoke":
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


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("db-up", "db-down", "db-reset", "smoke"):
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))

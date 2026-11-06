"""Run the repair regressions against prebuilt production releases."""
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, HTTPServer
import io
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import run

PAYMENT = {"order_id": "order-1", "status": "authorized"}
FAILURE = (502, {"error": "downstream_failure"})


@contextmanager
def stub(respond):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            requests.append(self.path)
            status, headers, body = respond(len(requests))
            self.send_response(status)
            for name, value in headers.items():
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(json.dumps(body).encode())

        def log_message(self, *_args):
            pass

    with HTTPServer(("127.0.0.1", 0), Handler) as server:
        worker = threading.Thread(target=server.serve_forever)
        worker.start()
        try:
            yield server.server_port, requests
        finally:
            server.shutdown()
            worker.join()


@contextmanager
def orders(payments_port):
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory)
        binary = ROOT / "_build/prod/rel/orders/bin/orders"
        settings = dict(
            PATH="/usr/bin:/bin:/usr/sbin:/sbin",
            HOME=directory,
            PROBE_SERVICE="orders",
            PROBE_OUTPUT=directory,
            PROBE_PAYMENTS_PORT=str(payments_port),
            RELEASE_DISTRIBUTION="none",
        )
        with (output / "process.log").open("wb") as log:
            child = subprocess.Popen(
                [str(binary), "start"],
                env=settings,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            try:
                ready = output / "ready.json"
                deadline = time.monotonic() + 10
                while not ready.exists():
                    if child.poll() is not None or time.monotonic() > deadline:
                        raise RuntimeError("Orders release did not become ready")
                    time.sleep(0.05)
                yield json.loads(ready.read_text())["port"]
            finally:
                run.stop(child)


class TransportTest(unittest.TestCase):
    def test_retry_after_zero_sends_exactly_one_post(self):
        def respond(count):
            if count == 1:
                return 503, {"Retry-After": "0"}, {}
            return 200, {}, PAYMENT

        with stub(respond) as (port, requests), orders(port) as orders_port:
            run.event("step", self._testMethodName, "post_to_orders")
            result = run.request(orders_port, "/orders", {"order_id": "order-1"})
            self.assertEqual((result, requests), (FAILURE, ["/payments/authorize"]))

    def test_redirect_is_rejected_without_calling_sink(self):
        with stub(lambda _: (200, {}, PAYMENT)) as (sink_port, sink_requests):
            location = f"http://127.0.0.1:{sink_port}/redirect-target"
            with stub(lambda _: (307, {"Location": location}, {})) as (port, requests), orders(port) as orders_port:
                run.event("step", self._testMethodName, "post_to_orders")
                result = run.request(orders_port, "/orders", {"order_id": "order-1"})
                self.assertEqual((result, requests, sink_requests), (FAILURE, ["/payments/authorize"], []))


def runner_probe(wrong_edge=True, stop_after_build=False):
    """Exercise the CLI using existing releases and temporary capture evidence."""
    real_copy = shutil.copyfile
    real_popen = subprocess.Popen
    real_run = subprocess.run
    build_tools = {}
    mutated = False
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory) / "experiments" / ROOT.name
        root.mkdir(parents=True)
        compiler = ROOT.parent / "0001-syntax-to-beam/src/main.rs"
        compiler_copy = root.parent / "0001-syntax-to-beam/src/main.rs"
        compiler_copy.parent.mkdir(parents=True)
        real_copy(compiler, compiler_copy)
        sources = [ROOT / name for name in ("run.py", "query.py", "mix.exs", "mix.lock")]
        for pattern in ("apps/*/lib/generated.ex", "apps/*/priv/*.beaml"):
            sources.extend(ROOT.glob(pattern))
        for source in sources:
            destination = root / source.relative_to(ROOT)
            destination.parent.mkdir(parents=True, exist_ok=True)
            real_copy(source, destination)
        (root / "_build").symlink_to(ROOT / "_build", target_is_directory=True)

        def launch(args, **kwargs):
            settings = kwargs.get("env")
            if wrong_edge and settings and settings.get("PROBE_DROP_CONTEXT") == "true":
                kwargs["env"] = dict(settings, PROBE_DROP_CONTEXT="false")
            return real_popen(args, **kwargs)

        def copy(source, destination, **kwargs):
            nonlocal mutated
            result = real_copy(source, destination, **kwargs)
            path = Path(destination)
            if wrong_edge and path.parent.name == "context-drop" and path.name == "orders.spans.jsonl":
                lines = path.read_text().splitlines(keepends=True)
                for index, line in enumerate(lines):
                    row = json.loads(line)
                    if row["name"] == "orders.finish":
                        lines[index] = line.replace(row["trace_id"], "f" * 32, 1)
                        path.write_text("".join(lines))
                        mutated = True
                        break
            return result

        def command(args, **kwargs):
            if "stdout" not in kwargs:
                return real_run(args, **kwargs)
            output = kwargs["stdout"]
            name = Path(output.name).stem
            settings = kwargs.get("env")
            if Path(args[0]).name in {"elixir", "mix"}:
                path = os.environ.get("PATH") if settings is None else settings.get("PATH")
                build_tools[name] = shutil.which(args[0], path=path)
            if name.startswith("generate-"):
                service = name.removeprefix("generate-")
                generated = root / "apps" / (service + "_api") / "lib/generated.ex"
                output.write(generated.read_bytes().replace((service.title() + "BeamlSpike").encode(), b"BeamlSpike", 1))
            if stop_after_build and name == "python-tests":
                return subprocess.CompletedProcess(args, 1)
            return subprocess.CompletedProcess(args, 0)

        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(sys, "argv", [str(root / "run.py")]), redirect_stdout(stdout), redirect_stderr(stderr):
            with patch.object(subprocess, "run", command), patch.object(subprocess, "Popen", launch), patch.object(shutil, "copyfile", copy):
                try:
                    runpy.run_path(str(root / "run.py"), run_name="__main__")
                except SystemExit as error:
                    code = error.code
        reports = list(root.glob("results/*/result.json"))
        result = json.loads(reports[0].read_text()) if reports else {}
        diagnostic = " ".join((stdout.getvalue(), stderr.getvalue(), str(code))) if not result else ""
        return dict(exit_code=code, result=result, mutated=mutated, build_tools=build_tools, diagnostic=diagnostic)


class AcceptanceTest(unittest.TestCase):
    def test_h03_rejects_intact_payment_edge_with_detached_finish(self):
        run.event("step", self._testMethodName, "run_with_wrong_edge")
        probe = runner_probe()
        self.assertTrue(probe["mutated"], probe["result"].get("error"))
        cases = probe["result"]["cases"]
        self.assertEqual(cases["H03"]["status"], "fail", cases["H03"].get("details", {}).get("gaps"))

    def test_optimized_runner_keeps_acceptance_or_rejects_before_running(self):
        run.event("step", self._testMethodName, "run_optimized")
        child = subprocess.run([sys.executable, "-O", __file__, "--optimized-probe"], capture_output=True, text=True, timeout=60, check=True)
        probe = json.loads(child.stdout)
        if not probe["result"]:
            self.assertNotIn(probe["exit_code"], (0, None))
            self.assertEqual(probe["build_tools"], {})
            self.assertRegex(probe["diagnostic"].lower(), r"optim|\-o")
        else:
            cases = probe["result"]["cases"]
            self.assertEqual(cases["H03"]["status"], "fail", cases["H03"].get("details", {}).get("gaps"))


class ToolchainTest(unittest.TestCase):
    def test_build_uses_the_toolchain_selected_on_path(self):
        with tempfile.TemporaryDirectory() as directory:
            toolchain = Path(directory)
            for tool in ("elixir", "mix"):
                shim = toolchain / tool
                shim.write_text("#!/bin/sh\nexit 0\n")
                shim.chmod(0o755)
            run.event("step", self._testMethodName, "check_build_tool_selection")
            child = subprocess.run(
                [sys.executable, __file__, "--toolchain-probe"],
                env={"PATH": directory},
                capture_output=True, text=True, timeout=20, check=True,
            )
            actual = json.loads(child.stdout)["build_tools"]
            expected = {name: str(toolchain / "mix") for name in (
                "dependencies", "format-generated", "format", "release-orders", "release-payments", "compile-strict",
            )}
            expected["elixir-version"] = str(toolchain / "elixir")
            wrong_tool = [step for step, tool in expected.items() if actual.get(step) != tool]
            self.assertEqual(wrong_tool, [])


class RepairResult(unittest.TextTestResult):
    def startTest(self, test):
        super().startTest(test)
        run.event("start", test._testMethodName, "running")

    def addSuccess(self, test):
        super().addSuccess(test)
        run.event("pass", test._testMethodName, "pass")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        run.event("fail", test._testMethodName, "assertion_failed")

    def addError(self, test, err):
        super().addError(test, err)
        run.event("fail", test._testMethodName, "test_error")


if __name__ == "__main__":
    if sys.argv[1:] == ["--optimized-probe"]:
        print(json.dumps(runner_probe()))
    elif sys.argv[1:] == ["--toolchain-probe"]:
        print(json.dumps(runner_probe(wrong_edge=False, stop_after_build=True)))
    else:
        unittest.main(testRunner=unittest.TextTestRunner(resultclass=RepairResult))

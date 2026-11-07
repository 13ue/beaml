"""EXPERIMENT 0004, RED TEAM 01 repair B3: parallel COMPILER runs keep every action event a whole JSON line.

Finding: workflow/2026-11-07/red-team-01/rt-boundary.md B3 (and rt-correctness.md R2-6). Contract:
workflow/2026-11-07/red-team-01-repairs/spec.md, decision D6B-188 (one write per event, a full line with its newline,
on an O_APPEND file; no partial line). The COMPILER writes `.beaml/actions.jsonl` under its cwd, so a scratch cwd stands
for the repository root. WORKERS loops of RUNS builds each start at the same time against one log.
Run: python3 -B experiments/0004-generated-replay/tests/redteam_b3_test.py
"""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_tree import EXPERIMENT  # noqa: E402
import stored_types_test as st  # noqa: E402

SOURCE = EXPERIMENT / "slice6" / "host-struct" / "nonzero.beaml"
WORKERS = 40
RUNS = 50
KEYS = {"ts", "source", "action", "target", "result"}


class RedTeamB3(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        holder = tempfile.mkdtemp(prefix="beaml-0004-b3-")
        self.addCleanup(shutil.rmtree, holder)
        self.cwd = Path(holder)
        self.log = self.cwd / ".beaml" / "actions.jsonl"
        self.binary = st.compiler()

    def build(self):
        done = subprocess.run([self.binary, str(SOURCE)], cwd=self.cwd, capture_output=True, timeout=90)
        self.assertEqual(0, done.returncode, done.stderr[-300:])

    def test_b3_parallel_runs_write_whole_json_lines(self):
        self.build()
        per_run = len(self.log.read_text().splitlines())
        self.log.unlink()
        start = threading.Barrier(WORKERS)

        def loop(_):
            start.wait()
            for _ in range(RUNS):
                self.build()

        with ThreadPoolExecutor(WORKERS) as pool:
            list(pool.map(loop, range(WORKERS)))
        lines = self.log.read_text().splitlines()
        bad = 0
        for line in lines:
            try:
                event = json.loads(line)
            except ValueError:
                bad += 1
                continue
            if not (isinstance(event, dict) and KEYS <= set(event) and event["source"] == "cli"):
                bad += 1
        # Count only: a line is never printed (AGENTS.md, no source text or path in output).
        self.assertEqual((0, WORKERS * RUNS * per_run), (bad, len(lines)),
                         "(invalid lines, line count) of %d parallel runs" % (WORKERS * RUNS))


if __name__ == "__main__":
    unittest.main()

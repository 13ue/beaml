import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import run
from query import event

class RunnerTest(unittest.TestCase):
    def test_owned_child_stops(self):
        child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'],start_new_session=True)
        try: run.stop(child);self.assertIsNotNone(child.poll())
        finally:
            if child.poll() is None: child.kill();child.wait()

    def test_action_failure_does_not_raise(self):
        with patch('pathlib.Path.open',side_effect=OSError('synthetic unavailable')):
            self.assertIsNone(event('test','synthetic','pass'))

if __name__=='__main__':unittest.main()

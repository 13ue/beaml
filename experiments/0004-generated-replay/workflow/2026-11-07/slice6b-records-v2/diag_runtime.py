# Diagnostic only: run the runtime cases of steps 7 and 8 with --stored stored/empty.jsonl, so that the build step
# does not mask the runtime assertions. Not a test file.
import sys, unittest
sys.path.insert(0, "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests")
import slice6_decode_test as sd, slice6_decode_ctor_test as sc, slice6_failure_test as sf

class D(unittest.TestCase):
    setUp = sf.Slice6Failure.setUp
    compile = sf.Slice6Failure.compile
    run_runtime = sd.Slice6Decode.run_runtime
    def test_step7_live(self): self.run_runtime(sd.LIVE_CASES, stored=sf.EMPTY_STORED)
    def test_step7_replay(self): self.run_runtime(sd.REPLAY_CASES, stored=sf.EMPTY_STORED)
    def test_step7_no_value(self): self.run_runtime({"value_only_in_the_typed_field": sd.NO_VALUE}, stored=sf.EMPTY_STORED)
    def test_step8_live(self): self.run_runtime(sc.LIVE_CASES, source=sc.ORDERS, script=sc.HELPERS, stored=sf.EMPTY_STORED)
    def test_step8_replay(self): self.run_runtime(sc.REPLAY_CASES, source=sc.ORDERS, script=sc.HELPERS, stored=sf.EMPTY_STORED)
unittest.main()

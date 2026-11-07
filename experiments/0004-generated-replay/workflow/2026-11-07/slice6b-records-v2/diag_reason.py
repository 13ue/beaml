# Diagnostic only: the reason of the failing replay cases against the current compiler.
import sys, unittest
sys.path.insert(0, "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests")
import slice6_decode_test as sd, slice6_decode_ctor_test as sc, slice6_failure_test as sf
class D(unittest.TestCase):
    setUp = sf.Slice6Failure.setUp
    compile = sf.Slice6Failure.compile
    run_runtime = sd.Slice6Decode.run_runtime
    def test_reason(self):
        self.run_runtime({"step7_replay_is_digest_mismatch": 'replay.("%s", 1) == {:error, :body_digest_mismatch}' % sd.RESOLVED}, stored=sf.EMPTY_STORED)
    def test_reason8(self):
        self.run_runtime({"step8_replay_is_digest_mismatch": 'replay.("%s", 2) == {:error, :body_digest_mismatch}' % sc.STORED}, source=sc.ORDERS, script=sc.HELPERS, stored=sf.EMPTY_STORED)
unittest.main()

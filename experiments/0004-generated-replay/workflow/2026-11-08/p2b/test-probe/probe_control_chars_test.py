import json, subprocess, sys, unittest
sys.path.insert(0, "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests")
import slice6_db_stored_test as t
import hashlib
S = str(__import__('pathlib').Path(__file__).resolve().parent)
IDS = ["o-\x00-\x01-\x1f", "o-\x7f- - -\U0001F600", 'o-"-\\-\\u000b', "o-\x08\x0c\n\r\t-\x1a\x1b\x1c", "o-﻿-é-/"]
class Probe(t.Slice6DbStored):
    def test_probe(self):
        rows = [t.row(dict(t.WIRE1, order_id=i)) for i in IDS]
        inp = "\n".join(json.dumps(r) for r in rows)
        digests = subprocess.run(["elixir", S + "/digest.exs"], input=inp, capture_output=True, text=True, check=True).stdout.split()
        for r, d in zip(rows, digests):
            r["value_sha256"] = d
            print("elixir", d == t.st.value_sha256(r["value"]), file=sys.stderr)
        self.assert_built(t.ORDERS, [t.counted(len(rows), len(rows), 0)], rows=rows)
    def test_probe_lower_hex_blocks(self):
        r = t.row(dict(t.WIRE1, order_id="o-\x1a"))
        text = json.dumps({"redacted": r["redacted"], "unknown_keys": r["unknown_keys"], "value": r["value"]}, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        assert "\\u001a" in text
        r["value_sha256"] = hashlib.sha256(text.encode()).hexdigest()
        self.assert_digest_block([r], 1)
if __name__ == "__main__":
    unittest.main(argv=["x", "Probe"])

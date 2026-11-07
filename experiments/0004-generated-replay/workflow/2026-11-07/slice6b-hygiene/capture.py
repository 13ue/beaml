"""Slice 6b step 0 check: record the compiler output for fixed inputs, one JSON line per case.

Usage: python3 -B capture.py BINARY > LOG. Run it before and after the change; the two logs must be equal.
Cases: the three plan sources (compile; GEN with each stored snapshot), and `--remove-dead` (the difflib port, DL-067) on every slice4 and
slice5 fixture with every stored snapshot, with and without `--assume-complete`.
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
E4 = REPO / "experiments/0004-generated-replay"
STORED = "experiments/0004-generated-replay/stored/"
SOURCES = [["experiments/0001-syntax-to-beam/example.beaml"],
           ["experiments/0002-http-correlation/apps/payments_api/priv/payments.beaml"]] + \
    [["experiments/0004-generated-replay/arms/gen/orders.beaml", "--stored", STORED + name]
     for name in ("empty.jsonl", "v1.jsonl", "v1-v2.jsonl")]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main(binary):
    for argv in SOURCES:
        r = subprocess.run([binary] + argv, cwd=REPO, capture_output=True)
        print(json.dumps({"case": "compile " + " ".join(argv), "code": r.returncode, "stdout": digest(r.stdout),
                          "stderr": digest(r.stderr)}))
    fixtures = sorted(p for p in (E4 / "slice4").glob("*/orders.beaml")) + \
        sorted(p for p in (E4 / "slice5").glob("*/orders.beaml"))
    for fixture in fixtures:
        for stored in sorted((E4 / "stored").glob("*.jsonl")):
            for extra in ([], ["--assume-complete"]):
                work = Path(tempfile.mkdtemp(prefix="beaml-6b0-"))
                try:
                    (work / "src").mkdir()
                    shutil.copyfile(fixture, work / "src/orders.beaml")
                    shutil.copyfile(stored, work / "stored.jsonl")
                    r = subprocess.run([binary, "src/orders.beaml", "--stored", "stored.jsonl", "--remove-dead"]
                                       + extra, cwd=work, capture_output=True)
                    case = "remove-dead %s %s %s" % (fixture.relative_to(E4), stored.name, " ".join(extra))
                    print(json.dumps({"case": case.strip(), "code": r.returncode, "diff_bytes": len(r.stdout),
                                      "stdout": digest(r.stdout), "stderr": digest(r.stderr),
                                      "file": digest((work / "src/orders.beaml").read_bytes())}))
                finally:
                    shutil.rmtree(work)


if __name__ == "__main__":
    main(sys.argv[1])

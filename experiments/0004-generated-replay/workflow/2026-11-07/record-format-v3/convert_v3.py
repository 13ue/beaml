"""One-time rewrite of the tracked version 2 RECORD SNAPSHOT fixtures to RECORD FORMAT v3 (DL-143, QV3-5 A, RV3-08).

Per record: `version` 3; `client_span_id` or `server_span_id` becomes `span_id` (same place); `unknown_fields` `[]`
when absent; a RESPONSE RECORD gets `outcome`/`reason` from `status` only (RV3-12): 200 gives accepted/null, other
gives rejected/"status". An ENTRY RECORD keeps its `outcome`/`reason`. `value` and `value_sha256` stay; the digest is
recomputed with `stored_types_test.value_sha256` and must be equal. The input must be version 2 (assert).
Run from the repository root:
  python3 -B experiments/0004-generated-replay/workflow/2026-11-07/record-format-v3/convert_v3.py [--base COMMIT] [--out DIR]
--base reads each file at COMMIT (`git show`), --out writes under DIR instead of in place. GREEN runs it once, in place.
"""
import json
from pathlib import Path
import subprocess
import sys

EXPERIMENT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(EXPERIMENT / "tests"))
import stored_types_test as st  # noqa: E402

PREFIX = "experiments/0004-generated-replay/"
FILES = ["stored/v1.jsonl", "stored/v1-v2.jsonl",
         "slice6/decode/stored.jsonl", "slice6/decode/stored-fail.jsonl", "slice6/decode/stored-resolved.jsonl",
         "slice6/decode-ctor/stored.jsonl", "slice6/decode-ctor/stored-fail.jsonl",
         "slice6/decode-ctor/stored-nomatch.jsonl",
         "slice6/redacted/stored-unredacted.jsonl", "slice6/redacted/stored-request-unredacted.jsonl",
         "slice6/stored-elixir/order.jsonl", "slice6/stored-elixir/nested-fail.jsonl",
         "slice6/stored-elixir/pipe-fail.jsonl", "slice6/stored-elixir/rec-loop.jsonl",
         "slice6/entry/stored/entries.jsonl"]


def convert(record, entry):
    assert record.get("version") == 2, "input must be record version 2"
    span = "server_span_id" if entry else "client_span_id"
    out = {("span_id" if k == span else k): (3 if k == "version" else v) for k, v in record.items()}
    out.setdefault("unknown_fields", [])
    if not entry:
        out["outcome"], out["reason"] = ("accepted", None) if record["status"] == 200 else ("rejected", "status")
    assert st.value_sha256(out["value"], out["unknown_keys"], out["redacted"]) == out["value_sha256"], "digest"
    return out


def convert_text(text, entry):
    return "".join(json.dumps(convert(json.loads(line), entry), separators=(",", ":")) + "\n"
                   for line in text.splitlines() if line.strip())


def main(argv):
    base = argv[argv.index("--base") + 1] if "--base" in argv else None
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else EXPERIMENT
    for name in FILES:
        text = (subprocess.run(["git", "show", "%s:%s%s" % (base, PREFIX, name)], capture_output=True, text=True,
                               check=True, cwd=EXPERIMENT).stdout if base else (EXPERIMENT / name).read_text())
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(convert_text(text, name.endswith("entries.jsonl")))
        print("converted", name)


if __name__ == "__main__":
    main(sys.argv[1:])

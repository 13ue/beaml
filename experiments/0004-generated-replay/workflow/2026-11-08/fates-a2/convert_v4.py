"""One-time rewrite of the tracked RECORD FORMAT v3 fixtures to record format draft 4 (DL-168, fates-a2a, QA2-1 default).

Per record: `version` 3 becomes 4; `type.nested` is added. Every direct field whose TYPE is not String gets 1 (in these
fixtures each such TYPE is a constructor TYPE or an enum, and no fixture source has a VERSION MARK on it, plan.md
section 2). A LIST field `[E]` would get {"version": 1, "nested": ...} (plan.md "Repairs" O1); no fixture has one, so
the converter stops on it instead of guessing E's fields. Nothing else changes; the digest is checked, not recomputed.
The input must be version 3 (assert). Run from the repository root:
  python3 -B experiments/0004-generated-replay/workflow/2026-11-08/fates-a2/convert_v4.py [--check] [--out DIR]
--check converts in memory and prints the counts only; --out writes under DIR. GREEN runs it once, in place.
"""
import json
from pathlib import Path
import sys

EXPERIMENT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(EXPERIMENT / "tests"))
import stored_types_test as st  # noqa: E402

# The 26 tracked v3 fixtures at HEAD 6427262f (git ls-files ... | xargs grep -l '"version":3').
FILES = ["stored/v1.jsonl", "stored/v1-v2.jsonl",
         "slice6/db/stored/meta/rows.jsonl",
         "slice6/decode/stored.jsonl", "slice6/decode/stored-fail.jsonl", "slice6/decode/stored-resolved.jsonl",
         "slice6/decode-ctor/stored.jsonl", "slice6/decode-ctor/stored-fail.jsonl",
         "slice6/decode-ctor/stored-nomatch.jsonl",
         "slice6/entry/stored/entries.jsonl",
         "slice6/record-v3/order/entries.jsonl", "slice6/record-v3/order/responses.jsonl",
         "slice6/record-v3/stored-200-rejected-nopath.jsonl", "slice6/record-v3/stored-503-nopath.jsonl",
         "slice6/record-v3/stored-accepted-nopath.jsonl", "slice6/record-v3/stored-held-rejected.jsonl",
         "slice6/record-v3/stored-mixed-fail.jsonl", "slice6/record-v3/stored-mixed.jsonl",
         "slice6/record-v3/stored-w2-accepted.jsonl", "slice6/record-v3/stored-w2-rejected.jsonl",
         "slice6/redacted/stored-unredacted.jsonl", "slice6/redacted/stored-request-unredacted.jsonl",
         "slice6/stored-elixir/order.jsonl", "slice6/stored-elixir/nested-fail.jsonl",
         "slice6/stored-elixir/pipe-fail.jsonl", "slice6/stored-elixir/rec-loop.jsonl"]


def nested(fields):
    out = {}
    for name, ty in fields:
        assert not ty.startswith("["), "a LIST field: write its element nested by hand (plan Repairs O1)"
        if ty != "String":
            out[name] = 1
    return out


def convert(record):
    assert record.get("version") == 3, "input must be record version 3"
    assert st.value_sha256(record["value"], record["unknown_keys"], record["redacted"]) == record["value_sha256"], \
        "digest"
    out = dict(record, version=4)
    out["type"] = dict(record["type"], nested=nested(record["type"]["fields"]))
    return out


def convert_text(text):
    return "".join(json.dumps(convert(json.loads(line)), separators=(",", ":")) + "\n"
                   for line in text.splitlines() if line.strip())


def main(argv):
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else EXPERIMENT
    total = 0
    for name in FILES:
        text = convert_text((EXPERIMENT / name).read_text())
        total += text.count("\n")
        if "--check" not in argv:
            target = out / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        print("converted", name)
    print("files %d, records %d" % (len(FILES), total))


if __name__ == "__main__":
    main(sys.argv[1:])

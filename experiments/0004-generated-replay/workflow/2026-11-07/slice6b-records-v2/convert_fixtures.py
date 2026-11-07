"""One-off conversion of the stored fixtures to RESPONSE RECORD version 2 (D6B-69, slice 6b step 6a).

`value` = the decoded body under the fields of the record's own TYPE VERSION (top level). Nested values are kept as
they are: every nested key in these fixtures is a declared key (checked below). `redacted` = [] (no field is redacted
in 6a). `unknown_keys` keeps the record value. `value_sha256` per D6B-58. The body keys go (DL-105).
Run once from the repository root: python3 -B experiments/0004-generated-replay/workflow/2026-11-07/slice6b-records-v2/convert_fixtures.py
"""
import base64
import json
from pathlib import Path
import sys

EXPERIMENT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(EXPERIMENT / "tests"))
import stored_types_test as st  # noqa: E402

FILES = ["stored/v1.jsonl", "stored/v1-v2.jsonl", "slice6/decode/stored.jsonl", "slice6/decode/stored-fail.jsonl",
         "slice6/decode/stored-resolved.jsonl", "slice6/decode-ctor/stored.jsonl",
         "slice6/decode-ctor/stored-fail.jsonl", "slice6/decode-ctor/stored-nomatch.jsonl"]
NESTED = {"state": {"status", "decline_reason"}, "amount": {"value", "currency"}}

for name in FILES:
    path = EXPERIMENT / name
    out = []
    for line in path.read_text().splitlines():
        record = json.loads(line)
        assert record["version"] == 1, (name, "already converted")
        body = json.loads(base64.b64decode(record["body_base64"]))
        fields = [f for f, _ in record["type"]["fields"]]
        value = {f: body[f] for f in body if f in fields}
        assert value == body, (name, "an undeclared top-level key")
        for key, allowed in NESTED.items():
            assert not isinstance(value.get(key), dict) or set(value[key]) <= allowed, (name, key)
        converted = st.with_value(record, value, record["unknown_keys"])
        out.append(json.dumps(converted, separators=(",", ":"), ensure_ascii=False))
    path.write_text("\n".join(out) + "\n")
    print(name, len(out))

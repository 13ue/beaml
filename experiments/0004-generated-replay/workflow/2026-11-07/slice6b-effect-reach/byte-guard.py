"""Make slice6/effect-reach/byte-guard.json (E8 under DL-119, notes.md D6B-117). RED phase tool, not a test.

Compile every source with the pre-step compiler (BEAML_SPIKE, a scratch `git archive` build of the base commit) and
`--stored stored/empty.jsonl`. Remove every pure-step span with the D6B-114 form. Store the exit code and the
sha256 of the expected stdout. No step of an existing source reaches an EFFECT through a fn (plan-review scan), so
every `:internal` step span with a function name is a pure-step span.
Run: BEAML_SPIKE=<scratch binary> python3 -B <this file>
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

EXPERIMENT = Path(__file__).resolve().parents[3]
REPO = EXPERIMENT.parents[1]
CALL = r"__MODULE__\.\w+\(p\d+\)"
SPAN = r"ProbeSupport\.span\(<<[\d,]*>>, :internal, (?:p\d+|nil), <<[\d,]*>>, fn -> "
LHS = r"(\{:ok, p\d+\} <-|p\d+ =)"
EVENT_STEP = re.compile(r"^( *)(with )?%s %sresult = (%s); (ProbeSupport\.event\(<<[\d,]*>>, <<[\d,]*>>\)); result end\)(,| do)$"
                        % (LHS, SPAN, CALL))
PLAIN_STEP = re.compile(r"^( *)(with )?%s %s(%s) end\)(,| do)$" % (LHS, SPAN, CALL))


def expected(stdout):
    """D6B-114: a pure step is a plain call; the prepared event is its own `_ =` clause right after the step."""
    out = []
    for line in stdout.split("\n"):
        m = EVENT_STEP.match(line)
        if m:
            indent, with_, lhs, call, event, tail = m.groups()
            out.append("%s%s%s %s," % (indent, with_ or "", lhs, call))
            out.append("%s_ = %s%s" % (indent + ("     " if with_ else ""), event, tail))
            continue
        m = PLAIN_STEP.match(line)
        out.append("%s%s%s %s%s" % (m.group(1), m.group(2) or "", m.group(3), m.group(4), m.group(5)) if m else line)
    text = "\n".join(out)
    assert not re.search(SPAN, text), "a step span is left"
    return text


def sources():
    found = sorted(p for p in EXPERIMENT.rglob("*.beaml") if p.name != ".beaml"
                   and not p.relative_to(EXPERIMENT).parts[0] in ("results", "workflow")
                   and p.relative_to(EXPERIMENT).parts[:2] != ("slice6", "effect-reach"))
    return found + [REPO / "experiments/0002-http-correlation/apps/payments_api/priv/payments.beaml"]


def main():
    table = {}
    for path in sources():
        run = subprocess.run([os.environ["BEAML_SPIKE"], str(path), "--stored",
                              str(EXPERIMENT / "stored" / "empty.jsonl")], capture_output=True, text=True)
        text = expected(run.stdout) if run.returncode == 0 else run.stdout
        table[str(path.relative_to(REPO))] = {"code": run.returncode, "changed": text != run.stdout,
                                              "sha256": hashlib.sha256(text.encode()).hexdigest()}
    # O2 (RED review): only a pre-step-12 build gives 40 changed rows; a GREEN build gives 0 and must not write.
    assert sum(r["changed"] for r in table.values()) == 40, "BEAML_SPIKE is not a pre-step-12 build"
    target = EXPERIMENT / "slice6" / "effect-reach" / "byte-guard.json"
    target.write_text(json.dumps(table, indent=1, sort_keys=True) + "\n")
    print(sum(r["changed"] for r in table.values()), "of", len(table), "change")


if __name__ == "__main__":
    main()

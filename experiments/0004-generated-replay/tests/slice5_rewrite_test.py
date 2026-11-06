"""EXPERIMENT 0004 slice 5 rewrite audit A1 (README revision 9.1, "Rewrite audit").

Scope: every path of `git diff --name-status f29e3f12` (working tree against the base), except the new slice 5
files, the compiler and grammar sources (0001/src/, integrations/zed-beaml/), documentation (*.md), run
directories under results/ and action logs under .beaml/. For each modified path, every changed line is W1 to W4
applied to an old line of its block, or a row of slice5/rewrite-allowed.json. Every row is used exactly once per listed file. Completeness: no
`.beaml` file of the rewrite scope keeps an old form, and every W4 and allowed-row site holds its new text.
The rules are exact strings and regular expressions here; the compiler is not run.
Run: python3 -B experiments/0004-generated-replay/tests/slice5_rewrite_test.py [-k NAME]
"""
import difflib
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_tree import EXPERIMENT, REPO  # noqa: E402
import slice5_syntax_test as s5  # noqa: E402

BASE = s5.BASE
X = s5.EXPERIMENT_REL
ALLOWED = EXPERIMENT / "slice5" / "rewrite-allowed.json"
EXCLUDED_PREFIXES = (X + "/slice5/", X + "/tests/slice5_", "experiments/0001-syntax-to-beam/src/",
                     "integrations/zed-beaml/")

# W1: `interface` before one space and a TYPE name or a format placeholder.
W1 = re.compile(r"\binterface(?= (?:[A-Z]|%\(?[A-Za-z]|\{))")
# W2: `migrate <T> <a> -> <b>` with digits, %d, %s or {...}.
W2 = re.compile(r"(\bmigrate\s+\S+\s+)(\d+|%[ds]|\{[^}]*\})(\s*->\s*)(\d+|%[ds]|\{[^}]*\})")
# W3 and W4 (README, closed lists): file -> [(old, new)], replaced inside a line.
W3 = {
    X + "/tests/slice4_retire_test.py": [('"version %d or older" % a', '"v%d or older" % a'),
                                         ('"starts at version 3", "TYPE VERSION 1"', '"starts at v3", "TYPE VERSION v1"')],
    X + "/tests/slice3_types_test.py": [("must derive version %d", "must derive v%d"),
                                        ('"%s %s 2" % (NOT_IN, N.T)', '"%s %s v2" % (NOT_IN, N.T)'),
                                        ('"%s %s 2" % (STILL_IN, N.T)', '"%s %s v2" % (STILL_IN, N.T)'),
                                        ('"derived TYPE VERSION 2"', '"derived TYPE VERSION v2"'),
                                        ('"derived TYPE VERSION 1"', '"derived TYPE VERSION v1"')],
}
W4 = {
    X + "/run.py": [(r're.search(r"^interface Payment \{([^}]*)\}"', r're.search(r"^type Payment(?: v[1-9][0-9]*)? \{([^}]*)\}"'),
                    ('line.startswith("interface ")', 'line.startswith("type ")')],
    X + "/tests/drift_test.py": [('line.startswith(("interface ", "effect ", "fn "))',
                                  'line.startswith(("type ", "effect ", "fn "))')],
}


def git(*args):
    return subprocess.run(["git", "-C", str(REPO)] + list(args), capture_output=True, check=True).stdout


def excluded(path):
    return (path.startswith(EXCLUDED_PREFIXES) or path.endswith(".md")
            or re.search(r"(^|/)(results|\.beaml)/", path) is not None)


def changed_paths():
    """(status, path) of every path in `git diff --name-status BASE` that is in the audit scope."""
    rows = []
    for line in git("diff", "--name-status", "--no-renames", BASE).decode().splitlines():
        status, path = line.split("\t", 1)
        if not excluded(path):
            rows.append((status, path))
    return rows


def rewrite(path, line):
    """W1 to W4 applied to one old line of `path`."""
    for old, new in W3.get(path, []) + W4.get(path, []):
        line = line.replace(old, new)
    line = W1.sub("type", line)
    return W2.sub(r"\1v\2\3v\4", line)


def strip_end(line):
    return line[:-2] if line.endswith("\r\n") else line[:-1] if line.endswith("\n") else line


def leftover(path, old_text, new_text):
    """Changed-line blocks after W1 to W4: a list of (old lines left, new lines left), line ends stripped."""
    old_lines, new_lines = old_text.splitlines(keepends=True), new_text.splitlines(keepends=True)
    blocks = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        olds, news = list(old_lines[i1:i2]), list(new_lines[j1:j2])
        for old in list(olds):
            image = rewrite(path, old)
            if image != old and image in news:
                news.remove(image)
                olds.remove(old)
        blocks.append(([strip_end(o) for o in olds], [strip_end(n) for n in news]))
    return blocks


def load_rows():
    return json.loads(ALLOWED.read_text())


def apply_rows(path, blocks, rows):
    """Consume rows that list `path`. Return (unexplained old lines, unexplained new lines, use count per row)."""
    used = {}
    for olds, news in blocks:
        for index, row in enumerate(rows):
            if path not in row["files"]:
                continue
            while (row["old"] is None or row["old"] in olds) and (row["new"] is None or row["new"] in news) \
                    and not (row["old"] is None and row["new"] is None):
                if row["old"] is not None:
                    olds.remove(row["old"])
                if row["new"] is not None:
                    news.remove(row["new"])
                used[index] = used.get(index, 0) + 1
    return [o for olds, _ in blocks for o in olds], [n for _, news in blocks for n in news], used


class RewriteAudit(unittest.TestCase):
    maxDiff = None

    def test_A1_allowed_rows_are_well_formed(self):
        # Guard, not RED: every row has a reason, names base files, and its old line is in each base file.
        for index, row in enumerate(load_rows()):
            with self.subTest(row=index):
                self.assertTrue(row.get("reason") and row.get("files") and (row["old"] or row["new"]), row)
                for path in row["files"]:
                    base = git("show", "%s:%s" % (BASE, path)).decode()
                    if row["old"] is not None:
                        self.assertIn(row["old"], [strip_end(line) for line in base.splitlines(keepends=True)],
                                      "row %d: old line not in the base %s" % (index, path))

    def test_A1_no_deleted_or_new_path_in_scope(self):
        self.assertEqual([], [(s, p) for s, p in changed_paths() if s != "M"],
                         "A1: a deleted or new path outside the slice 5, compiler, grammar, doc and results scope")

    def test_A1_every_changed_line_is_a_rewrite_rule_or_an_allowed_row(self):
        rows = load_rows()
        used_total = {}
        for status, path in changed_paths():
            if status != "M":
                continue
            with self.subTest(path=path):
                old = git("show", "%s:%s" % (BASE, path)).decode()
                new = (REPO / path).read_text()
                olds, news, used = apply_rows(path, leftover(path, old, new), rows)
                for index, count in used.items():
                    used_total.setdefault(index, {})[path] = count
                self.assertEqual(([], []), (olds, news),
                                 "A1 %s: changed lines that are neither W1 to W4 nor an allowed row (old, new)" % path)
        wrong = {}
        for index, row in enumerate(rows):
            counts = used_total.get(index, {})
            bad = {path: counts.get(path, 0) for path in row["files"] if counts.get(path, 0) != 1}
            if bad:
                wrong[index] = {"old": row["old"], "new": row["new"], "uses": bad}
        self.assertEqual({}, wrong, "A1: every allowed row is used exactly once per listed file")

    def test_A1_the_rewrite_is_complete(self):
        stale = [path for path in s5.rewrite_sources()
                 if (REPO / path).is_file() and s5.OLD_FORM.search((REPO / path).read_text())]
        self.assertEqual([], stale, "A1: rewrite-scope sources with an interface declaration or a plain number")
        sites = [(path, new) for path, pairs in W4.items() for _, new in pairs]
        sites += [(path, row["new"]) for row in load_rows() if row["new"] is not None for path in row["files"]]
        missing = [(path, text) for path, text in sites if text not in (REPO / path).read_text()]
        self.assertEqual([], missing, "A1: W4 and allowed-row sites without their new text")


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)

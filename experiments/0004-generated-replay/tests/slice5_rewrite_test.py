"""EXPERIMENT 0004 slice 5 rewrite audit A1 (README revision 9.2, "Rewrite audit").

Scope: every path of `git diff --name-status` against its base (working tree against the base), except the new
slice 5 files, the compiler and grammar sources (0001/src/, integrations/zed-beaml/), documentation (*.md), run
directories under results/ and action logs under .beaml/. Base: test code (`.py`, `.rs`) against the slice 5 RED
commit (the first commit whose slice4_retire_test.py holds RED_MARKER), every other path against f29e3f12. The
`mod tests` block of 0001/src/main.rs is audited too, against 721e7eea (so U2 counts as base). For each modified
path, every changed line is W1 to W4 applied to an old line of its block, or a row of slice5/rewrite-allowed.json.
Every row is used exactly once per listed file. Completeness: no `.beaml` file of the rewrite scope and no test
code file (TEST_CODE) keeps an old form, except the closed list slice5/deliberate-old-forms.json, and every W4
and allowed-row site holds its new text. The rules are exact strings and regular expressions; no compiler runs.
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
DELIBERATE = EXPERIMENT / "slice5" / "deliberate-old-forms.json"
MAIN_RS = "experiments/0001-syntax-to-beam/src/main.rs"
MAIN_TESTS_BASE = "721e7eea"
# The slice 5 RED commit: the first commit whose slice4_retire_test.py holds this text (README revision 9.2).
RED_MARKER = "def test_E12b_empty_snapshot_gives_three_W2_warnings"
RED_MARKER_FILE = X + "/tests/slice4_retire_test.py"
EXCLUDED_PREFIXES = (X + "/slice5/", X + "/tests/slice5_", "experiments/0001-syntax-to-beam/src/",
                     "integrations/zed-beaml/")

# W1: `interface` before one space and a TYPE name or a format placeholder.
# Revision 9.2: also directly after a format placeholder such as `%(chain)s` (TEMPLATE of stored_types_test.py)
# and directly after the escape `\n` inside a string literal (RETIRED in the `mod tests` block of main.rs).
W1 = re.compile(r"(?:(?<![A-Za-z0-9_])|(?<=%s)|(?<=\)s)|(?<=\\n))interface(?= (?:[A-Z]|%\(?[A-Za-z]|\{))")
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


# Old forms in test code (revision 9.2): `interface` before a TYPE name or a placeholder, and a `migrate` line
# with a plain number or a number placeholder. No word boundary before `interface` (see W1).
OLD_CODE = re.compile(r"interface[ \t]+(?:[A-Z]|%|\{)"
                      r"|migrate[ \t]+(?:\w+|%\(?\w*\)?s|\{[^}]*\})[ \t]+(?:\d|%d|%s|%\(|\{)")


def red_base():
    """SHA of the slice 5 RED commit, or None while it is not committed."""
    out = git("log", "--format=%H", "--reverse", "-S" + RED_MARKER, "--", RED_MARKER_FILE).decode().split()
    return out[0] if out else None


def is_test_code(path):
    return path.endswith((".py", ".rs"))


def base_of(path):
    if path == MAIN_RS:
        return MAIN_TESTS_BASE
    if is_test_code(path):
        base = red_base()
        if base is None:
            raise AssertionError("A1: the slice 5 RED commit is missing (no commit adds %r to %s); commit the RED "
                                 "tests first" % (RED_MARKER, RED_MARKER_FILE))
        return base
    return BASE


def tests_block(text):
    """The `#[cfg(test)] mod tests` block of main.rs, to the end of the file."""
    at = text.find("#[cfg(test)]\nmod tests {")
    if at < 0:
        raise AssertionError("A1: main.rs has no `#[cfg(test)] mod tests {` block")
    return text[at:]


def base_text(path):
    text = git("show", "%s:%s" % (base_of(path), path)).decode()
    return tests_block(text) if path == MAIN_RS else text


# The slice 5 GREEN commit. The diff audit checks the rewrite as it was committed, so later work
# (overview page, new run.py steps) does not count as rewrite. The no-old-form check still reads the working tree.
REWRITE = "bdc79eccc352807ba11123a06b1b2c4f830ea7a8"


def rewrite_text(path):
    text = git("show", "%s:%s" % (REWRITE, path)).decode()
    return tests_block(text) if path == MAIN_RS else text


def work_text(path):
    # Bytes, then decode: read_text() would turn CRLF into LF (Q4-crlf, Q4s-crlf).
    text = (REPO / path).read_bytes().decode()
    return tests_block(text) if path == MAIN_RS else text


def test_code_paths():
    """TEST_CODE (revision 9.2): cli.rs, runtime_test.exs, the `mod tests` block of main.rs, every run.py, the
    Python tests of experiments 0003 and 0004, and every file of the arms overlays. Tracked files, no results/."""
    names = git("ls-files", "--", "experiments").decode().splitlines()
    picked = [MAIN_RS]
    for name in names:
        if "/results/" in name:
            continue
        if (name in ("experiments/0001-syntax-to-beam/tests/cli.rs",
                     "experiments/0001-syntax-to-beam/tests/runtime_test.exs")
                or re.fullmatch(r"experiments/[^/]+/run\.py", name)
                or re.fullmatch(r"experiments/000[34]-[^/]+/tests/[^/]+\.py", name)
                or re.fullmatch(X + r"/arms/[^/]+/overlay/.+", name)):
            picked.append(name)
    return picked


def excluded(path):
    return (path.startswith(EXCLUDED_PREFIXES) or path.endswith(".md")
            or re.search(r"(^|/)(results|\.beaml)/", path) is not None)


def changed_paths():
    """(status, path) of every audit-scope path that differs from its base: `git diff --name-status BASE` for
    every path, and against the RED commit for test code; plus main.rs when its `mod tests` block changed."""
    rows = {}
    for base, own in ((BASE, lambda p: not is_test_code(p)), (red_base(), is_test_code)):
        if base is None:
            continue
        for line in git("diff", "--name-status", "--no-renames", base, REWRITE).decode().splitlines():
            status, path = line.split("\t", 1)
            if not excluded(path) and (own(path) or path not in rows):
                rows[path] = status
    if base_text(MAIN_RS) != rewrite_text(MAIN_RS):
        rows[MAIN_RS] = "M"
    return sorted((status, path) for path, status in rows.items())


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
                    base = base_text(path)
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
                old, new = base_text(path), rewrite_text(path)
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

    def test_A1_test_code_keeps_no_old_form(self):
        # Revision 9.2: a negative test (`is_err`, exit 1) passes also when its inline source is never rewritten.
        deliberate = json.loads(DELIBERATE.read_text())
        found, stale = [], []
        lines = {}
        for path in test_code_paths():
            text = work_text(path)
            lines[path] = [line.strip() for line in text.splitlines()]
            for number, line in enumerate(text.splitlines(), 1):
                if OLD_CODE.search(line):
                    found.append((path, line.strip()))
        for row in deliberate:
            key = (row["file"], row["line"])
            if not row.get("reason") or lines.get(row["file"], []).count(row["line"]) != 1:
                stale.append(key)
            elif key in found:
                found.remove(key)
        self.assertEqual(([], []), (found, stale),
                         "A1: test code with an old form (interface, plain migrate numbers) that is not a listed "
                         "deliberate negative; listed rows that are not exactly one line of their file")


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)

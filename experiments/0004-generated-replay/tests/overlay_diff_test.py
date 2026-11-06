"""EXPERIMENT 0004 case (c), first check: each arm copy differs from its original only by the change table.

README "0003 lines that change in the arm copies" is the source of TABLE below. For each arm:
the line diff of each copy against its original equals arms/<arm>/assertion-changes.json,
and that file equals TABLE. No other line changes. Run: python3 -B tests/overlay_diff_test.py
"""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_tree import ARMS, COPIES, HTTP_PATH, REPLAY_PATH, REPO  # noqa: E402

QUERY = HTTP_PATH + "/query.py"
CAPTURE = REPLAY_PATH + "/tests/response_capture_test.py"
REPLAY = REPLAY_PATH + "/tests/replay_run_test.py"
TRANSPORT_OLD, TRANSPORT_NEW = "OrdersApi.PaymentHttp.authorize/2", "OrdersBeamlSpike.payments_authorize/1"

# (file, line) -> (text in the original line, texts in the copy line, count of the first copy text).
# The original text must not stay in the copy line.
TABLE = {
    "gen": {
        (QUERY, 12): ("'orders.payment_http'", ["'orders.payments.authorize'"], 1),
        (QUERY, 13): ("'orders.payment_http')", ["'orders.payments.authorize')"], 1),
        (CAPTURE, 175): ('"orders.payment_http"', ['"orders.payments.authorize"'], 1),
        (CAPTURE, 213): ('"orders.payment_http"', ['"orders.payments.authorize"'], 2),
        (REPLAY, 32): ('"%s"' % TRANSPORT_OLD, ['"%s"' % TRANSPORT_NEW], 1),
        (REPLAY, 48): ("{OrdersApi.PaymentHttp, :authorize, 2}", ["{OrdersBeamlSpike, :payments_authorize, 1}"], 1),
        (REPLAY, 56): ("OrdersApi.PaymentHttp.authorize(OrdersBeamlSpike.prepare(input[\"order\"]), [])",
                       ["OrdersBeamlSpike.payments_authorize(OrdersBeamlSpike.prepare(input[\"order\"]))"], 1),
        (REPLAY, 57): ("OrdersApi.Replay.run(input[\"order\"], input[\"trace_id\"], input[\"responses\"])",
                       ["OrdersBeamlSpike.Replay.run(ProbeSupport.valid_order!(", "ProbeSupport.valid_payment!(p, "],
                       1),
        (REPLAY, 292): ('{"raised": "MatchError"}', ["%OrdersBeamlSpike.PaymentError{reason: ", "transport"], 1),
        (REPLAY, 293): ('"%s"' % TRANSPORT_OLD, ['"%s"' % TRANSPORT_NEW], 1),
        (REPLAY, 301): ('"%s"' % TRANSPORT_OLD, ['"%s"' % TRANSPORT_NEW], 1),
    },
    "lib": {
        (REPLAY, 57): ("OrdersApi.Replay.run(input[\"order\"], input[\"trace_id\"], input[\"responses\"])",
                       ["ReplayLib.run(OrdersApi.ReplayDescriptor.authorize(), ProbeSupport.valid_order!(",
                        "ProbeSupport.valid_payment!(p, "], 1),
    },
}


def lines(path):
    return Path(path).read_text().split("\n")


class ChangeTableMatchesOriginals(unittest.TestCase):
    """Guard: the README line numbers point at the stated original text (plan commit)."""

    def test_table_rows_name_original_lines(self):
        for arm, rows in TABLE.items():
            for (relative, number), (old, _, _) in rows.items():
                self.assertIn(old, lines(REPO / relative)[number - 1], (arm, relative, number))


class OverlayCopiesEqualChangeTable(unittest.TestCase):
    maxDiff = None

    def check_arm(self, arm):
        problems = []
        changes_path = ARMS / arm / "assertion-changes.json"
        recorded = {}
        if not changes_path.is_file():
            problems.append("missing %s" % changes_path.relative_to(REPO))
        else:
            for row in json.loads(changes_path.read_text()):
                recorded[(row["file"], row["line"])] = row
            if set(recorded) != set(TABLE[arm]):
                problems.append("assertion-changes.json rows %s != table rows %s"
                                % (sorted(recorded), sorted(TABLE[arm])))
        for relative in COPIES:
            copy_path = ARMS / arm / "overlay" / relative
            if not copy_path.is_file():
                problems.append("missing copy %s" % copy_path.relative_to(REPO))
                continue
            original, copy = lines(REPO / relative), lines(copy_path)
            if len(original) != len(copy):
                problems.append("%s: %d lines, original %d" % (relative, len(copy), len(original)))
                continue
            changed = {i + 1 for i, (a, b) in enumerate(zip(original, copy)) if a != b}
            expected = {line for (path, line) in TABLE[arm] if path == relative}
            if changed != expected:
                problems.append("%s: changed lines %s, table %s" % (relative, sorted(changed), sorted(expected)))
            for number in sorted(changed & expected):
                old, news, count = TABLE[arm][(relative, number)]
                line = copy[number - 1]
                if old in line or line.count(news[0]) != count or not all(n in line for n in news[1:]):
                    problems.append("%s:%d copy line does not match the table: %r" % (relative, number, line))
                row = recorded.get((relative, number))
                if row is not None and (row.get("original"), row.get("copy")) != (original[number - 1], line):
                    problems.append("%s:%d assertion-changes.json text differs from the diff" % (relative, number))
                if row is not None and not row.get("reason"):
                    problems.append("%s:%d assertion-changes.json has no reason" % (relative, number))
        self.assertEqual([], problems)

    def test_overlay_copies_equal_change_table_gen(self):
        self.check_arm("gen")

    def test_overlay_copies_equal_change_table_lib(self):
        self.check_arm("lib")


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)

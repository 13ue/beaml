"""Repeatable command for EXPERIMENT 0004 slice 1.

RED stub (2026-11-06, implement-step Solve / RED): no subcommand is implemented yet.
GREEN adds the arm trees, the LIB freeze record and the DRIFT runner (plan.md, "New").
"""
import json
import sys

if __name__ == "__main__":
    print(json.dumps({"status": "not_implemented", "arguments": sys.argv[1:]}))
    raise SystemExit(2)

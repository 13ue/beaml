"""Test support for EXPERIMENT 0004: build one arm tree with the repository layout (README, Fixed inputs).

The tree holds the current compiler (0001), a copy of 0002 and the 0003 runner with its tests.
An arm adds its overlay, deletes its listed files and, for GEN, puts its BEAML source in place.
Arm layout (RED decision, notes.md):
  arms/<arm>/overlay/<repository path>   file copies that replace or add files in the tree
  arms/<arm>/delete.txt                  repository paths to delete in the tree, one per line
  arms/gen/orders.beaml                  the GEN source; it replaces 0002 apps/orders_api/priv/orders.beaml
The originals in the repository stay the control. This module never writes into the repository.
"""
import hashlib
from pathlib import Path
import shutil

EXPERIMENT = Path(__file__).resolve().parents[1]
REPO = EXPERIMENT.parents[1]
ARMS = EXPERIMENT / "arms"
COMPILER_PATH = "experiments/0001-syntax-to-beam"
HTTP_PATH = "experiments/0002-http-correlation"
REPLAY_PATH = "experiments/0003-source-linked-replay"
ORDERS_BEAML = HTTP_PATH + "/apps/orders_api/priv/orders.beaml"
PAYMENTS_BEAML = HTTP_PATH + "/apps/payments_api/priv/payments.beaml"
TEST_NAMES = ("replay_run_test.py", "response_capture_test.py", "run_test.py",
              "trace_lookup_repair_test.py", "trace_lookup_test.py")
# The files that each arm keeps as checked copies (README, 0003 lines that change in the arm copies).
COPIES = [HTTP_PATH + "/query.py"] + [REPLAY_PATH + "/tests/" + name for name in TEST_NAMES]
SKIP = {"_build", "deps", "target", "results", ".beaml", "__pycache__", "erl_crash.dump", "generated.ex"}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def control_files():
    """Repository files that an arm run must not change (README, EXECUTION control)."""
    files = [p for p in (REPO / HTTP_PATH).rglob("*")
             if p.is_file() and not SKIP.intersection(p.relative_to(REPO / HTTP_PATH).parts)]
    files += [REPO / REPLAY_PATH / "run.py"] + [REPO / REPLAY_PATH / "tests" / n for n in TEST_NAMES]
    files += [REPO / COMPILER_PATH / "src/main.rs"]
    return sorted(files)


def control_hashes():
    return {str(p.relative_to(REPO)): digest(p) for p in control_files()}


def _ignore(directory, names):
    return [name for name in names if name in SKIP]


def overlay_files(arm):
    root = ARMS / arm / "overlay"
    return sorted(p for p in root.rglob("*") if p.is_file()) if root.is_dir() else []


def deletions(arm):
    path = ARMS / arm / "delete.txt"
    if not path.is_file():
        return []
    return [line.strip() for line in path.read_text().splitlines() if line.strip() and not line.startswith("#")]


def build(arm, tree, orders_beaml=None, payments_beaml=None):
    """Write the arm tree under `tree`. Return the list of applied changes for the run record."""
    tree = Path(tree)
    applied = []
    shutil.copytree(REPO / COMPILER_PATH, tree / COMPILER_PATH, ignore=_ignore)
    shutil.copytree(REPO / HTTP_PATH, tree / HTTP_PATH, ignore=_ignore)
    (tree / REPLAY_PATH / "tests").mkdir(parents=True)
    shutil.copyfile(REPO / REPLAY_PATH / "run.py", tree / REPLAY_PATH / "run.py")
    for name in TEST_NAMES:
        shutil.copyfile(REPO / REPLAY_PATH / "tests" / name, tree / REPLAY_PATH / "tests" / name)
    for source in overlay_files(arm):
        relative = source.relative_to(ARMS / arm / "overlay")
        target = tree / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        applied.append(("overlay", str(relative)))
    for relative in deletions(arm):
        target = tree / relative
        if target.is_file():
            target.unlink()
            applied.append(("delete", relative))
    if orders_beaml is None and arm == "gen":
        orders_beaml = ARMS / "gen" / "orders.beaml"
    if orders_beaml is not None:
        shutil.copyfile(orders_beaml, tree / ORDERS_BEAML)
        applied.append(("beaml", ORDERS_BEAML))
    if payments_beaml is not None:
        shutil.copyfile(payments_beaml, tree / PAYMENTS_BEAML)
        applied.append(("beaml", PAYMENTS_BEAML))
    return applied

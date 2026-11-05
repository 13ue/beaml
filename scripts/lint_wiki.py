#!/usr/bin/env python3
"""Check local wiki structure and supplied-PDF provenance; never fetch the network."""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit


def prose(text):
    # shortcut: fenced blocks and inline links only, extend for reference links/HTML when used.
    return re.sub(r"^\s*(```|~~~).*?^\s*\1[^\n]*$", "", text, flags=re.M | re.S)


def anchors(text):
    found, counts = set(), {}
    for heading in re.findall(r"^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$", prose(text), re.M):
        heading = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", heading)
        slug = "".join(c for c in heading.lower() if c in " _-" or
                       unicodedata.category(c)[0] in "LN").replace(" ", "-")
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        found.add(f"{slug}-{count}" if count else slug)
    return found


def local_links(path, text):
    for match in re.finditer(r"\[[^]\n]*\]\((<[^>\n]+>|[^\s)]+)(?:\s+[^)]+)?\)", prose(text)):
        target = match.group(1).strip("<>")
        parts = urlsplit(target)
        if parts.scheme or parts.netloc:
            continue
        resolved = (path.parent / unquote(parts.path)).resolve() if parts.path else path
        yield resolved, unquote(parts.fragment), target


def check_markdown(root):
    files = sorted((root / "wiki").rglob("*.md")) + [root / "README.md", root / "AGENTS.md"]
    errors, outgoing, incoming = [], {}, set()
    texts = {}
    for path in files:
        if not path.resolve().is_relative_to(root):
            errors.append(f"{path.relative_to(root)}: maintained Markdown escapes repository")
        elif path.is_file():
            texts[path] = path.read_text()
    for path, text in texts.items():
        outgoing[path] = set()
        for target, fragment, original in local_links(path, text):
            if Path(unquote(urlsplit(original).path)).is_absolute() or not target.is_relative_to(root):
                errors.append(f"{path.relative_to(root)}: local link escapes repository {original}")
                continue
            outgoing[path].add(target)
            if target != path:
                incoming.add(target)
            label = str(path.relative_to(root))
            if not target.exists():
                errors.append(f"{label}: missing link target {original}")
            elif fragment and target.suffix == ".md" and fragment not in anchors(target.read_text()):
                errors.append(f"{label}: missing heading anchor {original}")
    index = root / "wiki/index.md"
    if index not in texts:
        errors.append("wiki/index.md: missing index")
    for path in texts:
        if path.is_relative_to(root / "wiki") and path.name not in {"index.md", "log.md"}:
            if path not in outgoing.get(index, set()):
                errors.append(f"{path.relative_to(root)}: absent from wiki/index.md")
            if path not in incoming:
                errors.append(f"{path.relative_to(root)}: no incoming local links")
        if path.parent == root / "wiki/sources":
            text = texts[path]
            requirements = {
                "status": r"(?i)status\s*:",
                "date": r"\b20\d{2}-\d{2}-\d{2}\b",
                "upstream URL or supplied-file origin": r"https?://|(?i:supplied|source_path|Downloads/)",
                "coverage/limits": r"(?i)coverage|limit|not |selected|unknown|scope|omitt|unavailable",
            }
            for field, pattern in requirements.items():
                if not re.search(pattern, text):
                    errors.append(f"{path.relative_to(root)}: missing source {field}")
            if not any(target.is_relative_to(root / "raw") for target in outgoing.get(path, set())):
                errors.append(f"{path.relative_to(root)}: missing raw evidence/provenance link")
    return errors, len(texts)


def check_specification(root):
    folder = root / "raw/specification"
    metadata = json.loads((folder / "provenance.json").read_text())
    pdf = folder / metadata["source_filename"]
    errors = []
    if hashlib.sha256(pdf.read_bytes()).hexdigest() != metadata["sha256"]:
        errors.append("specification: PDF SHA-256 differs from provenance")
    if pdf.stat().st_size != metadata["bytes"]:
        errors.append("specification: PDF byte count differs from provenance")
    saved = (folder / metadata["extraction"]["output"]).read_text()
    pieces = re.split(r"^===== PDF PAGE (\d+) =====\s*\n", saved, flags=re.M)
    page_numbers = [int(value) for value in pieces[1::2]]
    if page_numbers != list(range(1, metadata["pdf_pages"] + 1)):
        errors.append("specification: extraction page markers differ from provenance")
    missing = [tool for tool in ("pdfinfo", "pdftotext") if not shutil.which(tool)]
    if missing:
        return errors, "SKIPPED PDF text/page recount; unavailable: " + ", ".join(missing)
    info = subprocess.run(["pdfinfo", str(pdf)], check=True, capture_output=True, text=True, timeout=30)
    count = re.search(r"^Pages:\s+(\d+)", info.stdout, re.M)
    if not count or int(count.group(1)) != metadata["pdf_pages"]:
        errors.append("specification: pdfinfo page count differs from provenance")
    extraction = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], check=True,
                                capture_output=True, text=True, timeout=30).stdout
    fresh_pages = extraction.split("\f")
    if not fresh_pages[-1].strip():
        fresh_pages.pop()
    normalize = lambda value: " ".join(value.split())
    if [normalize(p) for p in fresh_pages] != [normalize(p) for p in pieces[2::2]]:
        errors.append("specification: saved per-page extraction differs from fresh pdftotext output")
    return errors, "PDF hash, bytes, page count and per-page text rechecked"


def self_test():
    assert anchors("# A & B\n# A & B\n## Über `code`\n") == {"a--b", "a--b-1", "über-code"}
    assert anchors("```md\n# Ignored\n```\n# Kept\n") == {"kept"}
    with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside_temp:
        root = Path(temp).resolve()
        outside = Path(outside_temp).resolve()
        (root / "wiki/sources").mkdir(parents=True)
        (root / "raw").mkdir()
        (root / "raw/evidence.txt").write_text("evidence")
        source = root / "wiki/sources/example.md"
        source.write_text("# Example\nStatus: selected, not runtime proof; 2026-11-05. "
                          "[Upstream](https://example.org) [raw](../../raw/evidence.txt)")
        (root / "wiki/index.md").write_text("# Index\n[Source](sources/example.md#example)")
        assert check_markdown(root)[0] == []
        (root / "wiki/index.md").write_text("[Broken](missing.md) [Source](sources/example.md#nope)")
        errors = check_markdown(root)[0]
        assert any("missing link target" in e for e in errors)
        assert any("missing heading anchor" in e for e in errors)
        (root / "wiki/index.md").write_text("# Index")
        assert any("absent from" in e for e in check_markdown(root)[0])
        source.write_text(source.read_text() + " [self](#example)")
        assert any("no incoming" in e for e in check_markdown(root)[0])
        source.write_text("# Example")
        assert any("missing source date" in e for e in check_markdown(root)[0])
        assert any("missing raw evidence" in e for e in check_markdown(root)[0])
        (outside / "secret.md").write_text("# Outside")
        (root / "raw/link.md").symlink_to(outside / "secret.md")
        for destination in [str(source), f"../../{outside.name}/secret.md#outside", "../raw/link.md#outside"]:
            (root / "wiki/index.md").write_text(f"[Escapes]({destination})")
            assert any("local link escapes" in e for e in check_markdown(root)[0])
        (root / "wiki/link.md").symlink_to(outside / "secret.md")
        assert any("maintained Markdown escapes" in e for e in check_markdown(root)[0])
    print("Self-test passed: headings, duplicate/Unicode anchors, fenced examples, broken links, "
          "index/orphans, metadata, absolute/traversal/symlink escapes")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    root = Path(__file__).resolve().parents[1]
    errors, count = check_markdown(root)
    pdf_errors, pdf_scope = check_specification(root)
    errors.extend(pdf_errors)
    for error in errors:
        print("ERROR:", error)
    print(f"Checked {count} maintained Markdown files; {len(errors)} error(s). {pdf_scope}.")
    print("Limits: inline Markdown links/headings only; original raw documents not linted; "
          "no external URL, semantic truth, security proof or runtime checks.")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())

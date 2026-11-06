"""Render BEAML files as a syntax-highlighted local HTML page with the project grammar.

Usage: python3 integrations/zed-beaml/preview.py [--chat] [file.beaml ...]
Writes integrations/zed-beaml/preview.html. With --chat, prints a compact HTML fragment for an inline chat widget.
Needs npx (Tree-sitter CLI 0.26.5).
"""
import html
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEFAULT = [
    "experiments/0002-http-correlation/apps/orders_api/priv/orders.beaml",
    "experiments/0002-http-correlation/apps/payments_api/priv/payments.beaml",
    "experiments/0001-syntax-to-beam/example.beaml",
]

CSS = """
:root{--bg:#f6f7f9;--surface:#fff;--fg:#1b2230;--muted:#6a7383;--line:#d9dde3;
--keyword:#7a3fc4;--type:#0f6e56;--function:#185fa5;--property:#a3412d;--string:#3b6d11;
--operator:#5f5e5a;--punct:#888780;--constructor:#854f0b;--comment:#8a8a8a;color-scheme:light}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
--bg:#12161c;--surface:#1a2029;--fg:#e4e8ee;--muted:#9aa4b2;--line:#2e3744;
--keyword:#c3a6ea;--type:#5dcaa5;--function:#85b7eb;--property:#f0997b;--string:#97c459;
--operator:#b4b2a9;--punct:#888780;--constructor:#ef9f27;--comment:#8a8a8a;color-scheme:dark}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 system-ui,-apple-system,sans-serif}
.wrap{max-width:960px;margin:0 auto;padding:32px 16px 64px;display:grid;gap:28px}
h1{font-size:26px;margin:0} h2{font-size:15px;margin:0 0 8px;font-family:ui-monospace,Menlo,monospace;color:var(--muted);font-weight:500}
.code{background:var(--surface);border:1px solid var(--line);border-radius:10px;overflow-x:auto;padding:12px 0}
table{border-collapse:collapse;font:13.5px/1.6 ui-monospace,"SF Mono",Menlo,monospace}
.line-number{user-select:none;text-align:right;color:var(--muted);padding:0 14px;opacity:.6}
.line{white-space:pre;padding-right:16px}
.keyword{color:var(--keyword);font-weight:600}.type{color:var(--type)}.function{color:var(--function)}
.property{color:var(--property)}.string,.string.escape{color:var(--string)}.operator{color:var(--operator)}
.punctuation{color:var(--punct)}.constructor{color:var(--constructor)}.comment{color:var(--comment);font-style:italic}
.note{color:var(--muted);font-size:13px}
"""


def highlight(path):
    out = subprocess.run(
        ["npx", "-y", "tree-sitter-cli@0.26.5", "highlight", "--html", "--css-classes", str(path)],
        cwd=HERE, capture_output=True, text=True, check=True,
    ).stdout
    return re.search(r"<table>.*</table>", out, re.S).group(0)


SHORT = {"keyword": "k", "type": "t", "function": "f", "property": "p", "string": "s", "string escape": "s",
         "operator": "o", "punctuation bracket": "b", "punctuation delimiter": "b", "constructor": "c", "comment": "m"}


def chat_fragment(files):
    out = []
    for f in files:
        lines = re.findall(r"<td class=line>(.*?)\n?</td></tr>", highlight(f), re.S)
        code = "\n".join(lines)
        code = re.sub(r"<span class='([^']+)'>", lambda m: f"<i class={SHORT.get(m.group(1), 'o')}>", code)
        out.append(f"<div class=h>{f.name} · {len(lines)} lines</div><pre>{code.replace('</span>', '</i>')}</pre>")
    return "".join(out)


def main(args):
    if args[:1] == ["--chat"]:
        print(chat_fragment([ROOT / f for f in (args[1:] or DEFAULT)]))
        return
    files = [ROOT / f for f in (args or DEFAULT)]
    parts = []
    for f in files:
        rel = f.relative_to(ROOT)
        lines = len(f.read_text().splitlines())
        parts.append(f'<section><h2>{html.escape(str(rel))} · {lines} lines</h2><div class="code">{highlight(f)}</div></section>')
    page = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>BEAML source</title><style>{CSS}</style></head><body><div class=\"wrap\">"
        "<h1>BEAML source</h1>"
        '<p class="note">Highlighted with the project Tree-sitter grammar (integrations/zed-beaml).</p>'
        + "".join(parts)
        + "</div></body></html>\n"
    )
    (HERE / "preview.html").write_text(page)
    print(HERE / "preview.html")


if __name__ == "__main__":
    main(sys.argv[1:])

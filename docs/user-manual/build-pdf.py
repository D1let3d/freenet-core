#!/usr/bin/env python3
"""Build the print-ready PDF of the Freenet User Manual.

Converts freenet-user-manual.md to styled HTML, then prints it to PDF with
headless Chromium (or Google Chrome). Run from anywhere:

    python3 docs/user-manual/build-pdf.py

Requires: `pip install markdown` and a Chromium/Chrome binary on PATH (or set
CHROMIUM env var to its path).

Output: docs/user-manual/Freenet-User-Manual.pdf
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import markdown
except ImportError:
    sys.exit("Missing dependency: run `pip install markdown` first.")

HERE = Path(__file__).resolve().parent
SRC = HERE / "freenet-user-manual.md"
HTML_OUT = HERE / "freenet-user-manual.html"
PDF_OUT = HERE / "Freenet-User-Manual.pdf"

CSS = """
@page { size: A4; margin: 20mm 18mm; }
:root {
  --ink: #1a2330; --muted: #5a6b7f; --accent: #0a6e5c; --accent2: #155799;
  --rule: #d7dee6; --codebg: #f4f6f8;
}
* { box-sizing: border-box; }
html { font-size: 10.5pt; }
body {
  font-family: "Source Serif 4", Georgia, "Times New Roman", serif;
  color: var(--ink); line-height: 1.55; margin: 0;
}
h1, h2, h3, h4, .cover-subtitle, th {
  font-family: "Inter", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
}
h1 { font-size: 1.9rem; color: var(--accent); border-bottom: 3px solid var(--accent);
     padding-bottom: .3rem; margin: 1.6rem 0 1rem; page-break-before: auto; }
h2 { font-size: 1.4rem; color: var(--accent2); margin: 1.5rem 0 .7rem;
     border-bottom: 1px solid var(--rule); padding-bottom: .2rem; }
h3 { font-size: 1.12rem; margin: 1.2rem 0 .5rem; }
h1, h2, h3 { page-break-after: avoid; }
p, li { orphans: 3; widows: 3; }
a { color: var(--accent2); text-decoration: none; }
code {
  font-family: "JetBrains Mono", "SF Mono", Consolas, Menlo, monospace;
  font-size: .88em; background: var(--codebg); padding: .08em .3em;
  border-radius: 3px;
}
pre {
  background: var(--codebg); border: 1px solid var(--rule); border-left: 4px solid var(--accent);
  padding: .7em .9em; border-radius: 4px; overflow-x: auto; page-break-inside: avoid;
}
pre code { background: none; padding: 0; font-size: .85rem; }
blockquote {
  margin: .9em 0; padding: .5em 1em; border-left: 4px solid var(--accent2);
  background: #f2f7fc; border-radius: 0 4px 4px 0; page-break-inside: avoid;
}
blockquote p { margin: .3em 0; }
table {
  border-collapse: collapse; width: 100%; margin: .8em 0; font-size: .92rem;
  page-break-inside: avoid;
}
th, td { border: 1px solid var(--rule); padding: .4em .6em; text-align: left; vertical-align: top; }
th { background: #eef3f7; }
tr:nth-child(even) td { background: #fafbfc; }
hr { border: none; border-top: 1px solid var(--rule); margin: 1.5em 0; }
.page-break { page-break-after: always; }

/* Cover */
.cover { text-align: center; padding-top: 28mm; page-break-after: always; }
.cover-logo { width: 42mm; margin-bottom: 10mm; }
.cover h1 { font-size: 2.6rem; border: none; color: var(--ink); }
.cover-subtitle { color: var(--muted); font-size: 1.15rem; max-width: 70%; margin: 1rem auto 3rem; }
.cover-meta { width: auto; margin: 0 auto; font-size: 1rem; }
.cover-meta td { border: none; border-bottom: 1px solid var(--rule); padding: .45em 1.2em; }
.cover-meta td:first-child { color: var(--muted); text-align: right; }

/* TOC */
.toc-page { page-break-after: always; }
.toc-page > h1 { color: var(--ink); }
.toc ul { list-style: none; padding-left: 1.1em; margin: .2em 0; }
.toc > ul { padding-left: 0; }
.toc a { color: var(--ink); }
.toc > ul > li { margin-top: .55em; font-weight: 600;
  font-family: "Inter", "Segoe UI", Arial, sans-serif; }
.toc > ul > li li { font-weight: 400; font-family: inherit; }

/* Badges for revision highlighting */
.badge {
  display: inline-block; font-family: "Inter", Arial, sans-serif; font-size: .68rem;
  font-weight: 700; letter-spacing: .05em; padding: .1em .5em; border-radius: 8px;
  vertical-align: middle; color: #fff;
}
.badge-new { background: var(--accent); }
.badge-upd { background: #b7791f; }

/* Growth chart */
.growth-chart { margin: 1em 0; }
.growth-row { display: flex; align-items: center; margin: .35em 0; }
.growth-label { width: 6em; font-family: "Inter", Arial, sans-serif; font-size: .85rem;
  color: var(--muted); flex-shrink: 0; }
.growth-bar {
  background: linear-gradient(90deg, var(--accent), var(--accent2));
  color: #fff; font-family: "Inter", Arial, sans-serif; font-size: .8rem;
  padding: .3em .8em; border-radius: 4px; white-space: nowrap;
}
.footer-note { color: var(--muted); font-size: .85rem; text-align: center; margin-top: 2em; }
"""

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Freenet User Manual</title>
<style>{css}</style>
</head>
<body>
{body}
</body>
</html>
"""

TOC_PAGE = """<div class="toc-page"><h1>Contents</h1><div class="toc">{toc}</div></div>"""


def find_chromium() -> str:
    for cand in (
        os.environ.get("CHROMIUM"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        "/opt/pw-browsers/chromium/chrome-linux/chrome",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ):
        if cand and Path(cand).exists():
            return cand
    sys.exit("No Chromium/Chrome found. Install one or set CHROMIUM=/path/to/chrome.")


def main() -> None:
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "toc", "attr_list", "md_in_html", "sane_lists"],
        extension_configs={"toc": {"toc_depth": "1-2", "permalink": False}},
    )
    body = md.convert(SRC.read_text(encoding="utf-8"))

    # Insert the TOC page right after the cover (first .page-break div).
    marker = '<div class="page-break"></div>'
    # The cover title is an h1 and would appear as a TOC entry wrapping
    # "About This Manual"; promote its children to the top level instead.
    toc = re.sub(
        r'<li>\s*<a href="#freenet-user-manual">[^<]*</a>\s*<ul>(.*?)</ul>\s*</li>',
        r"\1",
        md.toc,
        flags=re.S,
    )
    toc_html = TOC_PAGE.format(toc=toc)
    body = body.replace(marker, toc_html, 1)

    HTML_OUT.write_text(TEMPLATE.format(css=CSS, body=body), encoding="utf-8")
    print(f"wrote {HTML_OUT}")

    chromium = find_chromium()
    subprocess.run(
        [
            chromium,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--no-pdf-header-footer",
            f"--print-to-pdf={PDF_OUT}",
            HTML_OUT.as_uri(),
        ],
        check=True,
    )
    print(f"wrote {PDF_OUT}")


if __name__ == "__main__":
    main()

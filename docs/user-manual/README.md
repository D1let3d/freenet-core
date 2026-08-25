# Freenet User Manual

A complete, self-contained user manual for Freenet: installing, everyday use,
the operational self-check, troubleshooting, upgrading, secrets, tuning, and
first developer steps.

| File | Purpose |
|---|---|
| [`freenet-user-manual.md`](freenet-user-manual.md) | The manual source (single markdown file — readable as-is on GitHub). |
| [`Freenet-User-Manual.pdf`](Freenet-User-Manual.pdf) | Print-ready PDF, generated from the source. |
| [`build-pdf.py`](build-pdf.py) | Regenerates the PDF (`pip install markdown` + Chromium/Chrome required). |

## Updating the manual (the "living document" contract)

The manual is versioned independently of the software, with its revision and
the Freenet release it describes stamped on the cover. When you change it:

1. Edit `freenet-user-manual.md`.
2. Bump the **manual revision** and the **Freenet version** on the cover page.
3. Mark every added section with `<span class="badge badge-new">NEW</span>` and
   every changed section with `<span class="badge badge-upd">UPDATED</span>`
   next to its heading — and remove the previous revision's badges.
4. Add a row to **Appendix E** (revision history) and a bar to its growth
   chart, so readers get a visual record of how coverage has grown.
5. Rebuild the PDF: `python3 docs/user-manual/build-pdf.py` and commit it
   together with the source.

The generated intermediate `freenet-user-manual.html` is a build artifact and
is not committed.

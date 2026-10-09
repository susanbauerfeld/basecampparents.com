#!/usr/bin/env python3
"""Copy edits on top of the mirror: the book is out, authors named in the hero and share image."""
import os
import re
import sys

SITE = sys.argv[1] if len(sys.argv) > 1 else "."
# Each name stays on one line, so narrow screens wrap at the "&".
AUTHORS = (
    '<span style="white-space:nowrap">Susan Bauerfeld, PhD</span> &amp; '
    '<span style="white-space:nowrap">Chris Parrott, CPsychol</span>'
)
# Same image with the authors added under the subtitle (wp-content/uploads/2026/06/).
OLD_SHARE_IMAGE = "basecampparents.png"
NEW_SHARE_IMAGE = "basecampparents-authors.png"

HERO_PARAGRAPH = re.compile(
    r'(<p class="e-d852bdd-bcceb33 e-paragraph-base"[^>]*>Learn how to break free.*?</p>)', re.S
)
HERO_AUTHORS = (
    '\n\t\t\t\t\t<p class="e-d852bdd-bcceb33 e-paragraph-base hero-authors"'
    ' style="max-width:none;font-weight:600;color:var(--Green);margin-top:-16px">' + AUTHORS + "</p>"
)


def edit(text):
    text = text.replace(">PREORDER NOW ON<", ">ORDER NOW ON<")
    text = re.sub(r'(class="elementor-item elementor-item-anchor"[^>]*>)Pre-Order<', r"\1Order<", text)
    text = text.replace(OLD_SHARE_IMAGE, NEW_SHARE_IMAGE)
    if "hero-authors" not in text:
        text = HERO_PARAGRAPH.sub(lambda m: m.group(1) + HERO_AUTHORS, text, count=1)
    return text


changed = 0
for root, _, files in os.walk(SITE):
    if ".git" in root:
        continue
    for f in files:
        if not f.endswith(".html"):
            continue
        p = os.path.join(root, f)
        try:
            with open(p, encoding="utf-8") as fh:
                text = fh.read()
            new = edit(text)
            if new != text:
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(new)
                changed += 1
        except OSError as err:
            print(f"error: {p}: {err}", file=sys.stderr)

print(f"edited {changed} page(s)")

#!/usr/bin/env python3
"""Point share-preview images (og:image / twitter:image) at where the site is actually served.

Usage: share_urls.py <site-dir> <base-url>

The mirror's <meta> tags use absolute https://www.basecampparents.com/... URLs, which only
work once that domain points at this site. The deploy workflow passes the Pages URL
(github.io now, the custom domain once it's set), so link previews work either way.
Only images that exist in the site are rewritten.
"""
import os
import re
import sys

SITE, BASE = sys.argv[1], sys.argv[2].rstrip("/")
META = re.compile(
    r'(<meta (?:property|name)="(?:og:image|twitter:image)" content=")https?://(?:www\.)?basecampparents\.com/([^"]+)(")'
)

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

            def fix(m):
                exists = os.path.isfile(os.path.join(SITE, m.group(2)))
                return f"{m.group(1)}{BASE}/{m.group(2)}{m.group(3)}" if exists else m.group(0)

            new = META.sub(fix, text)
            if new != text:
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(new)
                changed += 1
        except OSError as err:
            print(f"error: {p}: {err}", file=sys.stderr)

print(f"share images now on {BASE} in {changed} page(s)")

#!/usr/bin/env python3
"""Turn the raw wget mirror into a self-contained static site."""
import hashlib
import os
import re
import shutil
import sys
from urllib.parse import quote, unquote

SRC = sys.argv[1]  # scratchpad dir containing the wget output
OUT = sys.argv[2]  # destination site root
HOST_DIR = "www.basecampparents.com"
EXTRA_DIRS = ["fonts.googleapis.com", "fonts.gstatic.com"]
TEXT_EXT = (".html", ".css", ".js", ".json", ".svg", ".xml")

if os.path.exists(OUT):
    shutil.rmtree(OUT)
shutil.copytree(os.path.join(SRC, HOST_DIR), OUT)
for d in EXTRA_DIRS:
    shutil.copytree(os.path.join(SRC, d), os.path.join(OUT, d))

# 1. Rename files whose names contain a query string.
renames = {}  # old basename -> new basename
for root, _, files in os.walk(OUT):
    for f in files:
        if "?" not in f:
            continue
        prefix, query = f.split("?", 1)
        stem, ext = os.path.splitext(prefix)
        for e in (".css", ".js"):
            if f.endswith(e):
                ext = e
        new = f"{stem}-{hashlib.sha1(query.encode()).hexdigest()[:8]}{ext}"
        os.rename(os.path.join(root, f), os.path.join(root, new))
        renames[f] = new


def encodings(name):
    forms = {name, name.replace("?", "%3F")}
    for safe in ("/:,=&+;", "/:,=&+;|", "/:,=+;", ""):
        forms.add(quote(name, safe=safe))
    forms |= {f.replace("&", "&amp;") for f in list(forms)}
    return sorted(forms, key=len, reverse=True)


rename_forms = [(enc, new) for old, new in renames.items() for enc in encodings(old)]

ABS = re.compile(r'(href|src|action)=(["\'])https?://(?:www\.)?basecampparents\.com(/[^"\']*)?\2')
ESCAPED_ABS = re.compile(r"https?:\\/\\/(?:www\.)?basecampparents\.com(?=\\/)")


def local_target(path):
    """Map a site URL path to an existing file under OUT, or None."""
    path = unquote(path.split("#")[0].split("?")[0]) or "/"
    full = os.path.join(OUT, path.lstrip("/"))
    if os.path.isdir(full):
        full = os.path.join(full, "index.html")
    return full if os.path.isfile(full) else None


for root, _, files in os.walk(OUT):
    for f in files:
        if not f.endswith(TEXT_EXT):
            continue
        p = os.path.join(root, f)
        with open(p, encoding="utf-8", errors="surrogateescape") as fh:
            text = orig = fh.read()

        # Fonts dirs moved one level deeper (inside the site root).
        if not any(os.path.relpath(p, OUT).startswith(d) for d in EXTRA_DIRS):
            text = re.sub(r"\.\./(fonts\.(?:googleapis|gstatic)\.com)", r"\1", text)

        for enc, new in rename_forms:
            text = text.replace(enc, new)

        # Absolute links to pages/assets we have locally -> relative links.
        def fix(m):
            attr, q, path = m.group(1), m.group(2), m.group(3) or "/"
            target = local_target(path)
            if not target or attr == "action":
                return m.group(0)
            rel = os.path.relpath(target, root)
            frag = "#" + path.split("#", 1)[1] if "#" in path else ""
            return f"{attr}={q}{rel}{frag}{q}"

        text = ABS.sub(fix, text)
        # JSON-escaped URLs in inline config (Elementor, Popup Maker, ...) -> root-relative.
        text = ESCAPED_ABS.sub("", text)

        if text != orig:
            with open(p, "w", encoding="utf-8", errors="surrogateescape") as fh:
                fh.write(text)

print(f"renamed {len(renames)} files")

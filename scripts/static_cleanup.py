#!/usr/bin/env python3
"""Strip WordPress leftovers that can't work on a static host, and make asset URLs page-relative.

- Removes the comment form (and "No Comments" link), the search popup, and the footer
  links to pages that 404 on the live site.
- Removes Gravity Forms / Akismet assets (no forms use them any more) and the head
  <link>s that point at the WordPress REST API / oEmbed endpoints.
- Rewrites the root-relative asset URLs in inline JSON config (Elementor's lazy-loaded
  bundles, etc.) to page-relative ones, so the site also works from a sub-path such as
  username.github.io/repo/.
- Restores absolute URLs in the Yoast JSON-LD, which postprocess.py made root-relative.
"""
import os
import re
import shutil
import sys

SITE = sys.argv[1] if len(sys.argv) > 1 else "."
ORIGIN = "https://www.basecampparents.com"
DEAD_PAGES = ("the-5-rs-explained/", "additional-resources/", "category/events/")
UNUSED_DIRS = ("wp-content/plugins/gravityforms", "wp-content/plugins/akismet")


def remove_element(text, start, tag):
    """Remove the <tag> element opening at `start`, including nested <tag>s."""
    depth = 0
    for m in re.compile(rf"<(/?){tag}\b[^>]*>", re.I).finditer(text, start):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            return text[:start] + text[m.end():]
    raise ValueError(f"unbalanced <{tag}> at {start}")


def remove_all(text, opening, tag):
    """Remove every element whose opening tag matches the `opening` regex."""
    while m := re.search(opening, text):
        text = remove_element(text, m.start(), tag)
    return text


def clean(text, depth):
    # Comment form and the "No Comments" link above it.
    text = remove_all(text, r'<section id="respond"', "section")
    text = re.sub(r'\s*<a href="[^"]*#comments" class="entry-comment-count">.*?</a>', "", text, flags=re.S)
    # Search popup (Popup Maker #150).
    text = remove_all(text, r'<div\s+id="pum-150"', "div")
    # Footer links to pages that don't exist.
    for page in DEAD_PAGES:
        text = re.sub(
            r'\s*<li class="elementor-icon-list-item[^"]*">\s*<a href="https?://(?:www\.)?basecampparents\.com/'
            + re.escape(page) + r'">.*?</li>',
            "", text, flags=re.S,
        )
    # Gravity Forms / Akismet assets.
    text = re.sub(r"\s*<link[^>]+plugins/(?:gravityforms|akismet)/[^>]*>", "", text)
    text = re.sub(r"\s*<script[^>]+plugins/(?:gravityforms|akismet)/[^>]*>\s*</script>", "", text)
    # REST API / oEmbed discovery links.
    text = re.sub(r'\s*<link[^>]+(?:rel="https://api\.w\.org/"|/wp-json/)[^>]*>', "", text)

    # Root-relative URLs: absolute in the JSON-LD, page-relative everywhere else.
    up = "..\\/" * depth

    def fix_script(m):
        body = m.group(0)
        if "application/ld+json" in body[: body.find(">")]:
            return re.sub(r'"\\/', '"' + ORIGIN.replace("/", "\\/") + "\\/", body)
        return re.sub(r'"\\/(wp-content|wp-includes)\\/', lambda s: f'"{up}{s.group(1)}\\/', body)

    return re.sub(r"<script\b[^>]*>.*?</script>", fix_script, text, flags=re.S)


changed = 0
for root, _, files in os.walk(SITE):
    if ".git" in root:
        continue
    for f in files:
        if not f.endswith(".html"):
            continue
        p = os.path.join(root, f)
        depth = os.path.relpath(p, SITE).count(os.sep)
        try:
            with open(p, encoding="utf-8") as fh:
                text = fh.read()
            new = clean(text, depth)
            if new != text:
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(new)
                changed += 1
        except (OSError, ValueError) as err:
            print(f"error: {p}: {err}", file=sys.stderr)

for d in UNUSED_DIRS:
    shutil.rmtree(os.path.join(SITE, d), ignore_errors=True)

print(f"cleaned {changed} page(s)")

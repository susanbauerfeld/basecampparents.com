#!/usr/bin/env python3
"""Replace the newsletter popup's Gravity Form with a button to the Constant Contact signup page."""
import os
import re
import sys

SITE = sys.argv[1] if len(sys.argv) > 1 else "."
URL = "https://lp.constantcontactpages.com/sl/M5GLFKQ/basecampparents"

# From the "Sign up here!" line through the end of Gravity Form 1 and its inline scripts.
SIGNUP = re.compile(
    r'<p style="text-align: center;"><strong>Sign up here!</strong></p>\s*'
    r"<p style=\"text-align: center;\">\s*<div class='gf_browser_unknown gform_wrapper' id='gform_wrapper_1'.*?"
    r"\[1, 1\]\) \} \); </script></p>",
    re.S,
)
BUTTON = (
    # Extra space between the heading and the button (collapses with the h2's margin).
    '<p style="text-align: center; margin-top: 44px;">'
    f'<a class="button" href="{URL}" target="_blank" rel="noopener">Sign up here!</a>'
    "</p>"
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
            new, n = SIGNUP.subn(BUTTON, text, count=1)
            if n:
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(new)
                changed += 1
        except OSError as err:
            print(f"error: {p}: {err}", file=sys.stderr)

print(f"patched {changed} page(s)")

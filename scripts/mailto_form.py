#!/usr/bin/env python3
"""Make the footer Elementor form open a mailto: link instead of posting to WordPress."""
import os
import re
import sys

SITE = sys.argv[1] if len(sys.argv) > 1 else "."
TO = "susan@susanbauerfeld.com,chris@YourSelfSeries.com"
MARKER = 'id="mailto-form"'

# Capture-phase listener on document runs before Elementor Pro's own submit
# handler on the form, so stopPropagation keeps it from posting to admin-ajax.
SCRIPT = """<script %s>
document.addEventListener("submit", function (e) {
  var f = e.target;
  if (!f.matches || !f.matches("form.elementor-form")) return;
  e.preventDefault();
  e.stopPropagation();
  var val = function (n) { var el = f.elements["form_fields[" + n + "]"]; return el ? el.value.trim() : ""; };
  var name = val("name"), email = val("email"), msg = val("message");
  var body = [msg, "", name, email].join("\\n").trim().replace(/\\n/g, "\\r\\n");
  var subject = "Website inquiry" + (name ? " from " + name : "");
  window.location.href = "mailto:%s?subject=" + encodeURIComponent(subject) +
    "&body=" + encodeURIComponent(body);
}, true);
</script>""" % (MARKER, TO)

FORM = re.compile(r'<form class="elementor-form".*?</form>', re.S)

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
            if MARKER in text or not FORM.search(text):
                continue
            text = FORM.sub(lambda m: m.group(0) + "\n" + SCRIPT, text, count=1)
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(text)
            changed += 1
        except OSError as err:
            print(f"error: {p}: {err}", file=sys.stderr)

print(f"patched {changed} page(s)")

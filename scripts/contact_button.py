#!/usr/bin/env python3
"""Replace the footer Elementor form with just its "GET IN TOUCH" button, as a mailto: link."""
import os
import re
import sys

SITE = sys.argv[1] if len(sys.argv) > 1 else "."
TO = "info@basecampparents.com"
MAILTO = f"mailto:{TO}?subject=Website%20inquiry"
MARKER = 'id="contact-button"'

# The form, plus the inline submit handler an earlier version of this site added after it.
FORM = re.compile(
    r'<form class="elementor-form".*?</form>(?:\s*<script id="mailto-form">.*?</script>)?', re.S
)
# Elementor styles the button via [type="submit"]; repeat those colours for the link.
BUTTON = f"""<style {MARKER}>
.elementor-element-265c644 a.elementor-button{{background-color:var(--e-global-color-23db457);color:#000;transition-duration:300ms}}
.elementor-element-265c644 a.elementor-button:hover{{background-color:#FFFBFB;color:var(--e-global-color-c684ca1)}}
</style>
<div class="elementor-form">
	<div class="elementor-form-fields-wrapper">
		<div class="elementor-field-group elementor-column elementor-field-type-submit elementor-col-100 e-form__buttons">
			<a class="elementor-button elementor-size-sm" href="{MAILTO}">
				<span class="elementor-button-content-wrapper"><span class="elementor-button-text">GET IN TOUCH</span></span>
			</a>
		</div>
	</div>
</div>"""

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
            if MARKER in text:
                continue
            new = FORM.sub(lambda m: BUTTON, text, count=1)
            # Home page copy pointed at the form.
            new = new.replace("fill out the form below", "get in touch below")
            if new != text:
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(new)
                changed += 1
        except OSError as err:
            print(f"error: {p}: {err}", file=sys.stderr)

print(f"patched {changed} page(s)")

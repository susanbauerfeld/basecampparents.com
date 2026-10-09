#!/usr/bin/env python3
"""Put a Constant Contact inline sign-up form in the newsletter popup.

Replaces the popup's Gravity Form (or the earlier "Sign up here!" button) with
"Sign up here!" plus Constant Contact's inline form, and adds their loader
script ("Universal Code") once per page. The form is drawn by their script into
the page itself, so the CSS below restyles it to look like the old popup form.
"""
import os
import re
import sys

SITE = sys.argv[1] if len(sys.argv) > 1 else "."
FORM_ID = "4e0c104f-e200-468c-85a1-c6d60840c197"
ACCOUNT_KEY = "f4154ea305bc06fef080a0e713139da5"  # public; part of Constant Contact's embed code
MARKER = 'id="ctct-signup-css"'

# From the "Sign up here!" line through the end of Gravity Form 1 and its inline scripts.
GRAVITY_FORM = re.compile(
    r'<p style="text-align: center;"><strong>Sign up here!</strong></p>\s*'
    r"<p style=\"text-align: center;\">\s*<div class='gf_browser_unknown gform_wrapper' id='gform_wrapper_1'.*?"
    r"\[1, 1\]\) \} \); </script></p>",
    re.S,
)
# The link-to-landing-page button an earlier version of this site used instead.
BUTTON = re.compile(r'<p style="text-align: center;[^"]*"><a class="button" href="https://lp\.constantcontactpages\.com/[^"]*"[^>]*>Sign up here!</a></p>')

FORM = (
    '<p style="text-align: center;"><strong>Sign up here!</strong></p>\n'
    f'<div class="ctct-inline-form" data-form-id="{FORM_ID}"></div>'
)
LOADER = f"""<style {MARKER}>
/* Match the old Gravity Forms popup: bare email box, small black "Signup" button. */
#pum-33 .ctct-form-defaults{{padding:0!important;background:transparent!important;border:0!important}}
#pum-33 form.ctct-form-custom{{display:flex;flex-direction:column;align-items:center;margin:0}}
#pum-33 .ctct-form-field{{order:1;width:416px;max-width:66vw;margin:36px 0 0!important}}
#pum-33 .ctct-form-label{{position:absolute!important;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}}
#pum-33 input.ctct-form-element{{box-sizing:border-box;height:37px!important;margin:0!important;padding:5px 4px!important;border:1px solid #ccc!important;border-radius:0!important;box-shadow:none!important;background:#fff!important;font:16px Cardo,Georgia,serif!important;color:#222!important}}
#pum-33 .ctct-form-errorMessage{{font:13px Cardo,Georgia,serif!important;text-align:center}}
#pum-33 .ctct-form-error{{order:2;margin:8px 0 0!important}}
#pum-33 button.ctct-form-button{{order:3;width:auto!important;height:42px;margin:32px 0 0!important;padding:10px 20px!important;border:0!important;border-radius:0!important;background:#000!important;color:#fff!important;font:16px Cardo,Georgia,serif!important;text-transform:none!important;letter-spacing:normal!important}}
#pum-33 #gdpr_text{{order:4;max-width:416px;margin:20px 0 0}}
#pum-33 .ctct-gdpr-text{{margin:0!important;font:11px/1.45 Cardo,Georgia,serif!important;color:#888!important;text-align:center!important}}
#pum-33 .ctct-gdpr-text a{{color:inherit!important}}
#pum-33 .g-recaptcha{{order:5}}
#pum-33 .ctct-form-footer{{margin:10px 0 0!important;text-align:center;line-height:0}}
#pum-33 .ctct-form-footer-img{{height:14px!important;width:auto!important}}
#pum-33 .ctct-form-success{{text-align:center}}
#pum-33 .ctct-form-success .ctct-form-header{{font:700 20px Cardo,Georgia,serif!important;color:#222!important}}
#pum-33 .ctct-form-success .ctct-form-text{{font:14px Cardo,Georgia,serif!important;color:#555!important}}
@media (max-width:600px){{
  #pum-33 button.ctct-form-button{{width:100%!important;height:52px}}
}}
</style>
<script> var _ctct_m = "{ACCOUNT_KEY}"; </script>
<script id="signupScript" src="https://static.ctctcdn.com/js/signup-form-widget/current/signup-form-widget.min.js" async defer></script>
"""

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
            new, n = GRAVITY_FORM.subn(lambda m: FORM, text, count=1)
            if not n:
                new, n = BUTTON.subn(lambda m: FORM, text, count=1)
            if n:
                new = new.replace("</body>", LOADER + "</body>", 1)
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(new)
                changed += 1
        except OSError as err:
            print(f"error: {p}: {err}", file=sys.stderr)

print(f"patched {changed} page(s)")

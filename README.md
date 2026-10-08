# base-camp-parents.com

Static mirror of https://www.basecampparents.com (WordPress/Elementor), made with the owner's permission.

## Serve locally

```sh
python3 -m http.server 8000
```

Then open http://localhost:8000. Deploy by pointing any static host at the repo root.
All asset URLs are page-relative, so it also works from a sub-path (e.g. a GitHub Pages project URL).
`.nojekyll` stops GitHub Pages from running Jekyll, which would drop `_`-prefixed dirs.

## Regenerate

```sh
wget --mirror --convert-links --adjust-extension --page-requisites --no-parent \
  --span-hosts --domains=www.basecampparents.com,basecampparents.com,fonts.googleapis.com,fonts.gstatic.com \
  --reject-regex '(wp-json|xmlrpc|/feed/|\?replytocom=|wp-login|/wp-admin/)' \
  -e robots=off -i urls.txt   # urls.txt = all <loc> entries from the Yoast sitemaps
# Also download every *.bundle.min.js named in the Elementor webpack runtimes
# (they are lazy-loaded and wget can't discover them).
python3 scripts/postprocess.py <wget-output-dir> <site-dir>
python3 scripts/mailto_form.py <site-dir>
python3 scripts/signup_button.py <site-dir>
python3 scripts/static_cleanup.py <site-dir>
# static_cleanup.py doesn't fetch the Elementor lightbox/dialog/swiper/share-link assets
# that load lazily on /gallery/; download them from the live site too.
rm -r <site-dir>/contact   # merged into the footer form; also repoint 'contact/index.html' links to 'index.html#contact'
```

`scripts/postprocess.py` flattens the Google Fonts dirs into the site, renames files with
query strings in their names, and rewrites absolute links to local relative ones.

## Known limitations

- The footer "Begin the Dialogue" form opens a `mailto:` to Susan and Chris (subject from the name,
  body = message + name + email) via `scripts/mailto_form.py`. Email is the only required field.
  Visitors without a mail client configured can't send it.
- The newsletter popup's Gravity Form is replaced by a "Sign up here!" button linking to the
  Constant Contact signup page (`scripts/signup_button.py`).
- `scripts/static_cleanup.py` removes what can't work statically: the comment form (there are no
  comments), the search popup, footer links to `/additional-resources/`, `/the-5-rs-explained/` and
  `/category/events/` (404 on the live site too), Gravity Forms / Akismet assets, and the REST API /
  oEmbed `<link>`s. It also makes inline-config asset URLs page-relative and the Yoast JSON-LD absolute.

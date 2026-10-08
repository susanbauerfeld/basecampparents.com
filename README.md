# base-camp-parents.com

Static mirror of https://www.basecampparents.com (WordPress/Elementor), made with the owner's permission.

## Serve locally

```sh
python3 -m http.server 8000
```

Then open http://localhost:8000. Deploy by pointing any static host at the repo root.
Inline Elementor/Popup Maker config uses root-relative URLs, so the site must be served from a domain root.

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
rm -r <site-dir>/contact   # merged into the footer form; also repoint 'contact/index.html' links to 'index.html#contact'
```

`scripts/postprocess.py` flattens the Google Fonts dirs into the site, renames files with
query strings in their names, and rewrites absolute links to local relative ones.

## Known limitations

- The footer "Begin the Dialogue" form opens a `mailto:` to Susan and Chris (subject from the name,
  body = message + name + email) via `scripts/mailto_form.py`. Email is the only required field.
  Visitors without a mail client configured can't send it.
- Other dynamic WordPress features don't work: the Gravity Forms newsletter popup, comment forms,
  search, and anything hitting `admin-ajax.php` / `wp-json`. The newsletter and comment forms still post
  to the live site.
- `/additional-resources/`, `/the-5-rs-explained/` and `/category/events/` are linked from the
  nav but 404 on the live site too; those links still point at the live domain.

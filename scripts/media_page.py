#!/usr/bin/env python3
"""The /media-appearances/ page: cards linking to TV, radio, podcast and press appearances.

Usage: media_page.py <site-dir>

To add an appearance, add it to the top of APPEARANCES (newest first) and rerun.
The list lives between <!-- media:start --> and <!-- media:end --> in the page. On the
first run (no page yet) the page is made from /book-talks-signings/ with its own title and
metadata. Every run also puts "Media Appearances" in the header menu of every page, right
after "Book Talks & Signings".
"""
import html
import os
import re
import sys

SITE = sys.argv[1] if len(sys.argv) > 1 else "."

# Newest first. "image" is a thumbnail in wp-content/uploads/media/ (the video's own still,
# e.g. from the page's og:image); without one the card shows the outlet's name instead.
APPEARANCES = [
    {
        "title": "Parenting Anxious Teens Podcast - November 10, 2026",
        "segment": "Is Worrying About Your Anxious Teen Making Their Anxiety Worse?",
        "outlet": "Parenting Anxious Teens · Podcast",
        "url": "https://podcasts.apple.com/us/podcast/125-is-worrying-about-your-anxious-teen-making-their/id1757142421?i=1000800988154",
        "image": "parenting-anxious-teens-125.jpg",
        "action": "Listen to the full episode",
    },
    {
        "title": "Beautifully Complex - October 29, 2026",
        "segment": "How Worrying Less Helps Children More",
        "outlet": "Beautifully Complex · Podcast",
        "url": "https://parentingadhdandautism.com/381/",
        "image": "beautifully-complex-381.jpg",
        "action": "Listen to the full episode",
    },
    {
        "title": "Bloom TV - October 22, 2026",
        "segment": "Worry Less to Help Your Kids More",
        "outlet": "WFLA · Bloom",
        "url": "https://www.wfla.com/video/worry-less-to-help-your-kids-more-bloom/12290446",
        "image": "bloom-tv-2026-10-22.jpg",
        "action": "Watch the segment",
    },
]

# Video clips shown on the page under their own heading, below the cards. "video" and
# "poster" are in wp-content/uploads/media/.
CLIPS = [
    {
        "heading": "Chris talks about the role of parents",
        "video": "parents-are-base-camp-leaders.mp4",
        "poster": "parents-are-base-camp-leaders.jpg",
        "source": "Beautifully Complex, episode 381",
        "url": "https://parentingadhdandautism.com/381/",
    },
]

# Audio clips, listed with their captions below the video clips. "audio" is an MP3 in
# wp-content/uploads/media/.
AUDIO = [
    {
        "caption": "Susan speaking about Gentle Parenting on KNX LA Radio News",
        "audio": "knx-gentle-parenting.mp3",
    },
    {
        "caption": "Susan speaking about parental overprotection on KNX LA Radio News",
        "audio": "knx-parental-overprotection.mp3",
    },
    {
        "caption": "Susan speaking about technology on KNX LA Radio News",
        "audio": "knx-technology.mp3",
    },
]

SLUG = "media-appearances"
TITLE = "Media Appearances"
DESCRIPTION = "Susan Bauerfeld and Chris Parrott on TV, radio, podcasts and in the press."
TEMPLATE = os.path.join("book-talks-signings", "index.html")
PAGE = os.path.join(SLUG, "index.html")
START, END = "<!-- media:start -->", "<!-- media:end -->"

CSS = """<style id="media-layout-css">
.media-layout{display:flex;justify-content:center;padding:0 16px 64px}
.media-layout > .e-con{width:100%;max-width:960px}
.media-list{display:flex;flex-wrap:wrap;justify-content:center;gap:32px;width:100%;margin:0;padding:0;list-style:none}
.media-item{flex:0 1 440px;min-width:0}
.media-card{display:flex;flex-direction:column;height:100%;background:#fff;border:1px solid #dfe9e9;color:inherit;text-decoration:none;transition:box-shadow .2s,transform .2s}
.media-card:hover,.media-card:focus-visible{box-shadow:0 10px 28px rgba(3,124,128,.16);transform:translateY(-2px)}
.media-thumb{position:relative;display:block;aspect-ratio:16/9;background:#C3DDDD;overflow:hidden}
.media-thumb img{display:block;width:100%;height:100%;object-fit:cover}
.media-thumb-text{display:flex;align-items:center;justify-content:center;height:100%;padding:16px;font-family:Cardo,Georgia,serif;font-size:28px;font-weight:700;color:var(--Green);text-align:center}
.media-play{position:absolute;left:16px;bottom:16px;width:52px;height:52px;border-radius:50%;background:var(--Green);box-shadow:0 2px 10px rgba(0,0,0,.25);transition:transform .2s}
.media-play::after{content:"";position:absolute;left:21px;top:16px;border-style:solid;border-width:10px 0 10px 16px;border-color:transparent transparent transparent #fff}
.media-card:hover .media-play{transform:scale(1.08)}
.media-body{display:flex;flex-direction:column;flex:1;padding:20px 22px 22px}
.media-outlet{margin:0 0 8px;font-family:Inter,sans-serif;font-size:12px;font-weight:600;letter-spacing:1.2px;text-transform:uppercase;color:var(--Green)}
.media-title{margin:0;font-family:Cardo,Georgia,serif;font-size:24px;font-weight:700;line-height:1.25;color:#222}
.media-segment{margin:6px 0 0;font-family:Cardo,Georgia,serif;font-size:18px;font-style:italic;line-height:1.4;color:#555}
.media-action{margin:auto 0 0;padding-top:16px;font-family:Inter,sans-serif;font-size:14px;font-weight:600;letter-spacing:.6px;text-transform:uppercase;color:var(--Green)}
.media-card:hover .media-action{text-decoration:underline}
.media-clip{margin:64px auto 0;max-width:400px;text-align:center}
.media-clip-heading{margin:0 0 20px;font-family:Cardo,Georgia,serif;font-size:32px;font-weight:700;line-height:1.2;color:#222}
.media-clip video{display:block;width:100%;aspect-ratio:9/16;background:#C3DDDD;border:1px solid #dfe9e9}
.media-clip-source{margin:12px 0 0;font-family:Inter,sans-serif;font-size:14px;color:#555}
.media-clip-source a{color:var(--Green);font-weight:600}
.media-audio-list{display:flex;flex-direction:column;gap:20px;margin:64px auto 0;max-width:640px}
.media-audio{margin:0;padding:20px 22px;background:#fff;border:1px solid #dfe9e9}
.media-audio figcaption{margin:0 0 12px;font-family:Cardo,Georgia,serif;font-size:20px;font-weight:700;line-height:1.3;color:#222}
.media-audio audio{display:block;width:100%}
</style>"""

NAV_ITEM = re.compile(r'<li class="[^"]*menu-item-10952[^"]*"><a [^>]*>.*?</li>')
BOOK_HREF = re.compile(r'href="[^"]*"')


def render_list():
    items = []
    for a in APPEARANCES:
        if a.get("image"):
            thumb = f'<img src="../wp-content/uploads/media/{html.escape(a["image"])}" alt="" loading="lazy"><span class="media-play"></span>'
        else:
            thumb = f'<span class="media-thumb-text">{html.escape(a["outlet"])}</span>'
        segment = f'\n\t\t<p class="media-segment">{html.escape(a["segment"])}</p>' if a.get("segment") else ""
        items.append(
            '<li class="media-item">\n'
            f'\t<a class="media-card" href="{html.escape(a["url"])}" target="_blank" rel="noopener">\n'
            f'\t\t<div class="media-thumb">{thumb}</div>\n'
            '\t\t<div class="media-body">\n'
            f'\t\t<p class="media-outlet">{html.escape(a["outlet"])}</p>\n'
            f'\t\t<h3 class="media-title">{html.escape(a["title"])}</h3>{segment}\n'
            f'\t\t<p class="media-action">{html.escape(a.get("action", "Open"))} &rarr;</p>\n'
            "\t\t</div>\n"
            "\t</a>\n"
            "</li>"
        )
    clips = []
    for c in CLIPS:
        clips.append(
            '<section class="media-clip">\n'
            f'\t<h2 class="media-clip-heading">{html.escape(c["heading"])}</h2>\n'
            f'\t<video controls playsinline preload="none" poster="../wp-content/uploads/media/{html.escape(c["poster"])}">'
            f'<source src="../wp-content/uploads/media/{html.escape(c["video"])}" type="video/mp4"></video>\n'
            f'\t<p class="media-clip-source">From <a href="{html.escape(c["url"])}" target="_blank" rel="noopener">{html.escape(c["source"])}</a></p>\n'
            "</section>"
        )
    audio = ""
    if AUDIO:
        audio = '<section class="media-audio-list">\n' + "".join(
            '\t<figure class="media-audio">\n'
            f'\t\t<figcaption>{html.escape(a["caption"])}</figcaption>\n'
            f'\t\t<audio controls preload="none" src="../wp-content/uploads/media/{html.escape(a["audio"])}"></audio>\n'
            "\t</figure>\n"
            for a in AUDIO
        ) + "</section>\n"
    return (
        f'{START}\n<ul class="media-list">\n' + "\n".join(items) + "\n</ul>\n"
        + "".join(c + "\n" for c in clips) + audio + END
    )


def make_page():
    with open(os.path.join(SITE, TEMPLATE), encoding="utf-8") as fh:
        text = fh.read()
    # Metadata: the Yoast tags all name the page and its URL.
    text = text.replace("book-talks-signings", SLUG)
    text = text.replace("Book Talks &amp; Signings |", f"{TITLE} |")
    text = text.replace("Book Talks & Signings |", f"{TITLE} |")
    text = text.replace('"name":"Book Talks &#038; Signings"', f'"name":"{TITLE}"')
    text = re.sub(r'(<meta property="og:description" content=")[^"]*', r"\g<1>" + DESCRIPTION, text)
    text = re.sub(r'\s*<meta property="article:modified_time"[^>]*>', "", text)
    text = re.sub(r'"datePublished":"[^"]*","dateModified":"[^"]*",', "", text)
    text = re.sub(r"\bpage-id-10931\b", "page-media-appearances", text)
    text = text.replace(
        '<h1 data-interaction-id="fbb1800" class="e-heading-base" data-e-type="widget" data-id="fbb1800">Book Talks &amp; Signings</h1>',
        f'<h1 data-interaction-id="fbb1800" class="e-heading-base" data-e-type="widget" data-id="fbb1800">{TITLE}</h1>',
    )
    # Body: the events layout (style, list, calendar) becomes the media list.
    body = re.compile(r'<style id="events-layout-css">.*?<!-- events:end -->\n</div>\n<aside class="events-calendar">.*?</aside>\n</div>', re.S)
    container = re.search(r'<div class="elementor-element elementor-element-abf32c2 [^>]*>', text).group(0)
    new_body = f'{CSS}\n<div class="media-layout">\n{container}\n{render_list()}\n</div>\n</div>'
    text, n = body.subn(lambda _: new_body, text, count=1)
    if n != 1:
        sys.exit(f"error: events layout not found in {TEMPLATE}")
    os.makedirs(os.path.join(SITE, SLUG), exist_ok=True)
    return text


def add_nav(text, page):
    """Insert the menu item after Book Talks & Signings; on the media page itself, mark it active."""
    if f'menu-item-{SLUG}"' in text or f"menu-item-{SLUG} " in text:
        return text
    href = os.path.relpath(os.path.join(SITE, PAGE), os.path.dirname(page)).replace(os.sep, "/")
    on_media = os.path.normpath(page) == os.path.normpath(os.path.join(SITE, PAGE))

    def add(m):
        book_li = m.group(0)
        tabindex = ' tabindex="-1"' if 'tabindex="-1"' in book_li else ""  # the dropdown copy
        li_class = f"menu-item menu-item-type-post_type menu-item-object-page menu-item-{SLUG}"
        a_attrs = 'class="elementor-item"'
        if on_media:
            # The page is a copy of Book Talks & Signings, whose item is marked current there.
            book_li = re.sub(r' (current-menu-item|page_item|page-item-10931|current_page_item|active)(?=[ "])', "", book_li)
            book_li = book_li.replace(' aria-current="page"', "").replace(" elementor-item-active", "")
            book_li = BOOK_HREF.sub('href="../book-talks-signings/index.html"', book_li, count=1)
            li_class += " current-menu-item"
            a_attrs = 'aria-current="page" class="elementor-item elementor-item-active"'
        return f'{book_li}\n<li class="{li_class}"><a href="{href}" {a_attrs}{tabindex}>{TITLE}</a></li>'

    return NAV_ITEM.sub(add, text)


page_path = os.path.join(SITE, PAGE)
if os.path.exists(page_path):
    with open(page_path, encoding="utf-8") as fh:
        text = fh.read()
    text = re.sub(re.escape(START) + ".*?" + re.escape(END), lambda _: render_list(), text, count=1, flags=re.S)
    text = re.sub(r'<style id="media-layout-css">.*?</style>', lambda _: CSS, text, count=1, flags=re.S)
else:
    text = make_page()
with open(page_path, "w", encoding="utf-8") as fh:
    fh.write(text)

changed = 0
for root, _, files in os.walk(SITE):
    if ".git" in root:
        continue
    for f in files:
        if not f.endswith(".html"):
            continue
        p = os.path.join(root, f)
        with open(p, encoding="utf-8") as fh:
            text = fh.read()
        new = add_nav(text, p)
        if new != text:
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(new)
            changed += 1

print(f"{len(APPEARANCES)} appearance(s); menu added to {changed} page(s)")

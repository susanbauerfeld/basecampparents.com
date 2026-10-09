#!/usr/bin/env python3
"""Render upcoming events from the public Google Calendar into /book-talks-signings/.

Usage: render_events.py <site-dir> [ics-file-or-url]

The event list lives between <!-- events:start --> and <!-- events:end --> in the page.
On the first run (no markers yet) it also lays the page out as the event list plus an
embedded Google Calendar, side by side on wide screens.

Each calendar event renders as a date block (month/day) beside:
    <title>
    <weekday> · <time>
    <location>
    <description>
The description is shown as written: bold/italic/underline, line breaks and links from
Google Calendar's editor are kept (everything else is stripped), and bare web addresses
become clickable.
"""
import datetime as dt
import html
import html.parser
import os
import re
import sys
import urllib.parse
import urllib.request
import zoneinfo

import icalendar
import recurring_ical_events

CALENDAR_ID = "c_1ed1b333b7aaa010c5326728c9a64d81ee32629f0b4288419b52cd95e7797b4f@group.calendar.google.com"
TZ = zoneinfo.ZoneInfo("America/New_York")
PAGE = os.path.join("book-talks-signings", "index.html")
HORIZON_DAYS = 365

ICS_URL = (
    "https://calendar.google.com/calendar/ical/"
    + urllib.parse.quote(CALENDAR_ID)
    + "/public/basic.ics"
)
EMBED_URL = "https://calendar.google.com/calendar/embed?" + urllib.parse.urlencode({
    "src": CALENDAR_ID,
    "ctz": "America/New_York",
    "mode": "MONTH",
    "showTitle": 0,
    "showPrint": 0,
    "showCalendars": 0,
    "showTz": 0,
    "bgcolor": "#ffffff",
})

START, END = "<!-- events:start -->", "<!-- events:end -->"
LIST_CONTAINER = re.compile(r'<div class="elementor-element elementor-element-abf32c2 ')
LAYOUT_CSS = """<style id="events-layout-css">
.events-layout{display:flex;flex-direction:column;align-items:center;gap:40px;padding:0 16px 48px}
.events-layout > .e-con{width:100%}
.events-calendar{width:100%;max-width:600px}
.events-calendar iframe{display:block;width:100%;height:520px;border:0}
.events-empty{font-style:italic}
.events-list{width:100%;margin:0;padding:0;list-style:none}
.event{display:flex;gap:20px;align-items:flex-start;padding:22px 0;border-top:1px solid #dfe9e9}
.event:first-child{border-top:0;padding-top:4px}
.event-date{flex:0 0 64px;padding:8px 0 10px;background:#C3DDDD;color:var(--Green);text-align:center;line-height:1}
.event-month{display:block;font-family:Inter,sans-serif;font-size:12px;font-weight:600;letter-spacing:1.2px;text-transform:uppercase}
.event-day{display:block;margin-top:4px;font-family:Cardo,Georgia,serif;font-size:30px;font-weight:700}
.event-body{min-width:0}
.event-title{margin:0 0 4px;font-family:Cardo,Georgia,serif;font-size:22px;font-weight:700;line-height:1.25;color:#222}
.event-meta{margin:0;font-size:16px;line-height:1.5;color:#555}
.event-desc{margin:8px 0 0;font-size:16px;line-height:1.5;color:#333;overflow-wrap:anywhere}
.event-desc a{color:var(--Green);text-decoration:underline}
@media (min-width:1024px){
  .events-layout{flex-direction:row;align-items:flex-start;justify-content:center;gap:56px}
  .events-layout > .e-con{flex:0 1 600px}
  .events-calendar{flex:0 1 640px;max-width:640px;position:sticky;top:24px}
  .events-calendar iframe{height:600px}
}
</style>"""


def remove_children(text, start):
    """Return (open_tag_end, close_tag_start) of the <div> opening at `start`."""
    open_end = text.index(">", start) + 1
    depth = 0
    for m in re.compile(r"<(/?)div\b[^>]*>", re.I).finditer(text, start):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            return open_end, m.start(), m.end()
    raise ValueError("unbalanced <div> in event list container")


def ensure_layout(text):
    if START in text:
        # Already laid out; refresh the stylesheet in case it changed.
        return re.sub(r'<style id="events-layout-css">.*?</style>', lambda _: LAYOUT_CSS, text, count=1, flags=re.S)
    m = LIST_CONTAINER.search(text)
    if not m:
        raise ValueError("event list container not found")
    open_end, close_start, close_end = remove_children(text, m.start())
    container = text[m.start():open_end] + f"\n{START}\n{END}\n" + text[close_start:close_end]
    calendar = (
        '<aside class="events-calendar">'
        f'<iframe src="{html.escape(EMBED_URL)}" title="Book talks &amp; signings calendar" loading="lazy"></iframe>'
        "</aside>"
    )
    layout = f'{LAYOUT_CSS}\n<div class="events-layout">\n{container}\n{calendar}\n</div>'
    return text[:m.start()] + layout + text[close_end:]


def as_datetime(value, end=False):
    """Calendar values are dates (all-day) or datetimes; return an aware datetime."""
    if isinstance(value, dt.datetime):
        return value.astimezone(TZ) if value.tzinfo else value.replace(tzinfo=TZ)
    return dt.datetime.combine(value, dt.time.min, TZ)


def clock(t):
    return f"{t.hour % 12 or 12}:{t.minute:02d}"


def when(start, end):
    """Return (first day, "Weekday · time" line) for an event."""
    if not isinstance(start, dt.datetime):  # all-day; DTEND is exclusive
        last = (end - dt.timedelta(days=1)) if end else start
        if last == start:
            return start, f"{start:%A}"
        return start, f"{start:%A, %B} {start.day} – {last:%A, %B} {last.day}"
    s = start.astimezone(TZ)
    if not end:
        return s, f"{s:%A} · {clock(s)} {'am' if s.hour < 12 else 'pm'}"
    e = end.astimezone(TZ)
    s_ampm, e_ampm = ("am" if s.hour < 12 else "pm"), ("am" if e.hour < 12 else "pm")
    if s_ampm == e_ampm:
        return s, f"{s:%A} · {clock(s)}–{clock(e)} {e_ampm}"
    return s, f"{s:%A} · {clock(s)} {s_ampm}–{clock(e)} {e_ampm}"


URL = re.compile(r"https?://[^\s<>\"]+")


def clean_url(url):
    """Unwrap Google's https://www.google.com/url?q=<real url> redirects."""
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc.endswith("google.com") and parsed.path == "/url":
        return urllib.parse.parse_qs(parsed.query).get("q", [url])[0]
    return url


def short(url):
    """Display form of a bare URL: no scheme or www., at most ~40 characters."""
    text = re.sub(r"^https?://(www\.)?", "", url).rstrip("/")
    return text if len(text) <= 40 else text[:38] + "\u2026"


def link(url, text=None):
    url = clean_url(url)
    label = html.escape(text) if text else html.escape(short(url))
    return f'<a href="{html.escape(url)}" target="_blank" rel="noopener">{label}</a>'


def linkify(text):
    """Escape plain text, turning web addresses into links (trailing punctuation stays outside)."""
    out, pos = [], 0
    for m in URL.finditer(text):
        url = m.group(0).rstrip(".,;:!?)")
        out.append(html.escape(text[pos:m.start()]))
        out.append(link(url))
        pos = m.start() + len(url)
    out.append(html.escape(text[pos:]))
    return "".join(out).replace("\n", "<br>")


class Description(html.parser.HTMLParser):
    """Keep a safe subset of the HTML Google Calendar stores in event descriptions."""

    INLINE = {"b": "strong", "strong": "strong", "i": "em", "em": "em", "u": "u"}
    BREAKS = {"p", "div", "li", "ul", "ol"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.href, self.anchor_text, self.skip = [], None, [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        elif tag == "a":
            href = dict(attrs).get("href") or ""
            self.href = href if re.match(r"https?://", href) else ""
            self.anchor_text = []
        elif tag == "br":
            self.out.append("<br>")
        elif tag in self.INLINE and self.href is None:
            self.out.append(f"<{self.INLINE[tag]}>")
        elif tag == "li":
            self.out.append("\u2022 ")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip = max(0, self.skip - 1)
        elif tag == "a" and self.href is not None:
            text = "".join(self.anchor_text).strip()
            if self.href:
                same = not text or URL.fullmatch(text) or text.rstrip("/") == self.href.rstrip("/")
                self.out.append(link(self.href, None if same else text))
            else:
                self.out.append(linkify(text))
            self.href = None
        elif tag in self.INLINE and self.href is None:
            self.out.append(f"</{self.INLINE[tag]}>")
        elif tag in self.BREAKS:
            self.out.append("<br>")

    def handle_data(self, data):
        if self.skip:
            return
        if self.href is not None:
            self.anchor_text.append(data)
        else:
            self.out.append(linkify(data))

    def render(self, source):
        self.feed(source)
        self.close()
        result = "".join(self.out)
        result = re.sub(r"(\s*<br>\s*){3,}", "<br><br>", result)
        return re.sub(r"^(\s*<br>)+|(<br>\s*)+$", "", result.strip())


def render_event(ev):
    start = ev.get("DTSTART").dt
    end = ev.get("DTEND").dt if ev.get("DTEND") else None
    title = str(ev.get("SUMMARY", "")).strip().rstrip(".")
    location = str(ev.get("LOCATION", "")).strip().rstrip(".")
    description = str(ev.get("DESCRIPTION", ""))
    day, time = when(start, end)
    lines = [f'<h3 class="event-title">{html.escape(title)}</h3>', f'<p class="event-meta">{html.escape(time)}']
    if location:
        lines[-1] += f"<br>{html.escape(location)}"
    lines[-1] += "</p>"
    desc = Description().render(description) if description.strip() else ""
    if desc:
        lines.append(f'<p class="event-desc">{desc}</p>')
    body = "\n\t\t".join(lines)
    return (
        '<li class="event">\n'
        f'\t<time class="event-date" datetime="{day:%Y-%m-%d}">'
        f'<span class="event-month">{day:%b}</span><span class="event-day">{day.day}</span></time>\n'
        f'\t<div class="event-body">\n\t\t{body}\n\t</div>\n'
        "</li>"
    )


def upcoming(calendar, now):
    events = recurring_ical_events.of(calendar).between(now - dt.timedelta(days=1), now + dt.timedelta(days=HORIZON_DAYS))
    keep = []
    for ev in events:
        if str(ev.get("STATUS", "")).upper() == "CANCELLED":
            continue
        start = ev.get("DTSTART").dt
        end = ev.get("DTEND").dt if ev.get("DTEND") else start
        if not isinstance(end, dt.datetime) and end == start:
            end = start + dt.timedelta(days=1)
        if as_datetime(end) > now:
            keep.append(ev)
    return sorted(keep, key=lambda ev: as_datetime(ev.get("DTSTART").dt))


def main():
    site = sys.argv[1] if len(sys.argv) > 1 else "."
    source = sys.argv[2] if len(sys.argv) > 2 else ICS_URL
    try:
        if re.match(r"https?://", source):
            with urllib.request.urlopen(source, timeout=30) as resp:
                raw = resp.read()
        else:
            with open(source, "rb") as fh:
                raw = fh.read()
        calendar = icalendar.Calendar.from_ical(raw)
    except Exception as err:  # fail the run so the last good deploy stays up
        print(f"error: couldn't load calendar from {source}: {err}", file=sys.stderr)
        sys.exit(1)

    events = upcoming(calendar, dt.datetime.now(TZ))
    if events:
        body = '<ul class="events-list">\n' + "\n".join(render_event(ev) for ev in events) + "\n</ul>"
    else:
        body = '<p class="e-paragraph-base events-empty">No upcoming events right now. Check back soon!</p>'

    path = os.path.join(site, PAGE)
    try:
        with open(path, encoding="utf-8") as fh:
            text = ensure_layout(fh.read())
        s, e = text.index(START) + len(START), text.index(END)
        text = text[:s] + "\n" + body + "\n" + text[e:]
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    except (OSError, ValueError) as err:
        print(f"error: {path}: {err}", file=sys.stderr)
        sys.exit(1)
    print(f"rendered {len(events)} upcoming event(s)")


if __name__ == "__main__":
    main()

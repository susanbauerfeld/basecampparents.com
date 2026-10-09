#!/usr/bin/env python3
"""Render upcoming events from the public Google Calendar into /book-talks-signings/.

Usage: render_events.py <site-dir> [ics-file-or-url]

The event list lives between <!-- events:start --> and <!-- events:end --> in the page.
On the first run (no markers yet) it also lays the page out as the event list plus an
embedded Google Calendar, side by side on wide screens.

Each calendar event renders as:
    <date and time>
    <title>. <location>.
    Click here to register.        (if the description contains a link)
The link text says "for more information" instead when the description mentions
"more information".
"""
import datetime as dt
import html
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
        return text
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
    if not isinstance(start, dt.datetime):  # all-day; DTEND is exclusive
        last = (end - dt.timedelta(days=1)) if end else start
        day = f"{start:%B} {start.day}"
        if last == start:
            return day
        if last.month == start.month:
            return f"{day}-{last.day}"
        return f"{day}-{last:%B} {last.day}"
    s = start.astimezone(TZ)
    day = f"{s:%B} {s.day}"
    if not end:
        return f"{day}, {clock(s)} {'am' if s.hour < 12 else 'pm'}"
    e = end.astimezone(TZ)
    s_ampm, e_ampm = ("am" if s.hour < 12 else "pm"), ("am" if e.hour < 12 else "pm")
    if s_ampm == e_ampm:
        return f"{day}, {clock(s)}-{clock(e)} {e_ampm}"
    return f"{day}, {clock(s)} {s_ampm}-{clock(e)} {e_ampm}"


def first_link(description):
    m = re.search(r'href="(https?://[^"]+)"', description) or re.search(r"https?://[^\s<>\"]+", description)
    if not m:
        return None
    url = html.unescape(m.group(1) if m.re.groups else m.group(0)).rstrip(".,)")
    # Google Calendar sometimes wraps links as https://www.google.com/url?q=<real url>&sa=...
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc.endswith("google.com") and parsed.path == "/url":
        url = urllib.parse.parse_qs(parsed.query).get("q", [url])[0]
    return url


def render_event(ev):
    start = ev.get("DTSTART").dt
    end = ev.get("DTEND").dt if ev.get("DTEND") else None
    title = str(ev.get("SUMMARY", "")).strip().rstrip(".")
    location = str(ev.get("LOCATION", "")).strip().rstrip(".")
    description = str(ev.get("DESCRIPTION", ""))
    text = ". ".join(html.escape(p) for p in (title, location) if p) + "."
    link = first_link(description)
    if link:
        purpose = "for more information" if re.search(r"(?i)more info", description) else "to register"
        text += (
            f'<br>Click <a href="{html.escape(link)}" target="_blank" rel="noopener">'
            f"<strong><u>here</u></strong></a> {purpose}."
        )
    return (
        '<div class="elementor-element e-con e-atomic-element e-div-block-base event">\n'
        f'\t<h4 class="e-heading-base">{html.escape(when(start, end))}</h4>\n'
        f'\t<p class="e-paragraph-base">{text}</p>\n'
        "</div>"
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
        body = "\n".join(render_event(ev) for ev in events)
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

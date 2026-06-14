"""
Secret Tel Aviv scraper
Primary: Tribe Events Calendar REST API  /wp-json/tribe/events/v1/events
Fallback: HTML scraping of category listing + detail pages
"""
import os, re, time, logging
from datetime import datetime, date
from typing import Optional
from dataclasses import dataclass, field

import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

BASE   = "https://www.secrettelaviv.com"
API    = f"{BASE}/wp-json/tribe/events/v1"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
    "Accept-Language": "en-US,en;q=0.9",
}

CATEGORY_MAP = {
    "parties":            ("music",    "dj-set"),
    "live-music":         ("music",    "live"),
    "music-festivals":    ("music",    "festival"),
    "culture-highlights": ("cultural", "general"),
    "exhibitions":        ("cultural", "exhibition"),
    "meetups":            ("cultural", "meetup"),
    "shopping":           ("market",   "crafts"),
    "food-events":        ("market",   "food"),
    "pride":              ("cultural", "pride"),
}

TICKET_DOMAINS = ["entrio.co.il","eventbrite.com","ticketmaster.co.il","tickets.co.il"]

@dataclass
class Event:
    source_id:    str
    title:        str
    description:  str
    category:     str
    subcategory:  str
    sta_category: str
    event_date:   Optional[date]
    start_time:   Optional[str]
    end_time:     Optional[str]
    venue_name:   Optional[str]
    venue_address:Optional[str]
    image_url:    Optional[str]
    ticket_url:   Optional[str]
    source_url:   str


session = requests.Session()
session.headers.update(HEADERS)

def _get(url, params=None, retries=3):
    for i in range(retries):
        try:
            r = session.get(url, params=params, timeout=15)
            r.raise_for_status()
            time.sleep(1.2)
            return r
        except Exception as e:
            log.warning(f"  attempt {i+1}: {e}")
            time.sleep(2 * (i+1))
    return None

def _parse_dt(s):
    if not s: return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try: return datetime.strptime(s[:19], fmt)
        except: pass
    return None

def _og(soup, prop):
    t = soup.find("meta", property=prop)
    return t["content"].strip() if t and t.get("content") else None

def _ticket_url(soup):
    for a in soup.find_all("a", href=True):
        if any(d in a["href"] for d in TICKET_DOMAINS):
            return a["href"]
    return None

def _venue_from_html(soup):
    v = soup.find(class_=re.compile(r"tribe-venue"))
    if v:
        lines = [l.strip() for l in v.get_text("\n").splitlines() if l.strip()]
        return (lines[0] if lines else None), (", ".join(lines[1:]) or None)
    h1 = soup.find("h1")
    if h1:
        m = re.search(r"@\s+(.+)$", h1.get_text(strip=True))
        if m: return m.group(1).strip(), None
    return None, None

def _dates_from_html(soup):
    times = [t for t in soup.find_all("time") if t.get("datetime")]
    parsed = []
    for t in times:
        dt = _parse_dt(t["datetime"].replace("Z",""))
        if dt: parsed.append(dt)
    if parsed: return parsed[0], (parsed[1] if len(parsed)>1 else None)

    txt = soup.get_text(" ")
    m = re.search(r"(\d{1,2}/\d{2}/\d{4})\s+[*_]?(\d{1,2}:\d{2}\s*[ap]m)", txt, re.I)
    if m:
        try:
            dt = datetime.strptime(f"{m.group(1)} {m.group(2).strip()}", "%d/%m/%Y %I:%M %p")
            return dt, None
        except: pass
    return None, None

# ── API path ────────────────────────────────────────────────────────────────

def _fetch_api(sta_cat, our_cat):
    cat, sub = our_cat
    events, page = [], 1
    today = date.today().isoformat()
    while True:
        r = _get(f"{API}/events", {"per_page":50,"page":page,"start_date":today,"categories":sta_cat})
        if not r: break
        try: data = r.json()
        except: break
        raw = data.get("events",[])
        if not raw: break
        for ev in raw:
            slug = ev.get("slug", str(ev.get("id","")))
            venue = ev.get("venue",{})
            sdt = _parse_dt(ev.get("start_date",""))
            edt = _parse_dt(ev.get("end_date",""))
            ticket = ev.get("website") or None
            if not ticket:
                soup2 = BeautifulSoup(ev.get("description",""), "html.parser")
                ticket = _ticket_url(soup2)
            events.append(Event(
                source_id    = str(ev.get("id", slug)),
                title        = ev.get("title","").strip(),
                description  = BeautifulSoup(ev.get("description",""),"html.parser").get_text(" ",strip=True)[:400],
                category     = cat, subcategory=sub, sta_category=sta_cat,
                event_date   = sdt.date() if sdt else None,
                start_time   = sdt.strftime("%H:%M") if sdt else None,
                end_time     = edt.strftime("%H:%M") if edt else None,
                venue_name   = venue.get("venue"),
                venue_address= ", ".join(filter(None,[venue.get("address"),venue.get("city")])) or None,
                image_url    = (ev.get("image") or {}).get("url"),
                ticket_url   = ticket,
                source_url   = ev.get("url", f"{BASE}/tickets/{slug}"),
            ))
        if page >= data.get("total_pages",1): break
        page += 1
    return events

# ── HTML path ───────────────────────────────────────────────────────────────

def _listing_links(soup):
    links = set()
    for a in soup.find_all("a", href=True):
        h = a["href"]
        if re.match(r"https://www\.secrettelaviv\.com/tickets/[^/]+/?$", h) and "/categories/" not in h:
            links.add(h.rstrip("/"))
    return list(links)

def _fetch_detail(url, sta_cat, our_cat):
    r = _get(url)
    if not r: return None
    soup = BeautifulSoup(r.text, "html.parser")
    cat, sub = our_cat
    title = _og(soup,"og:title") or ""
    title = re.sub(r"\s*\|\s*Secret Tel Aviv.*$","",title).strip()
    slug  = url.rstrip("/").rsplit("/",1)[-1]
    sdt, edt = _dates_from_html(soup)
    vname, vaddr = _venue_from_html(soup)
    if not title or not sdt: return None
    return Event(
        source_id=slug, title=title,
        description=(_og(soup,"og:description") or ""),
        category=cat, subcategory=sub, sta_category=sta_cat,
        event_date=sdt.date(), start_time=sdt.strftime("%H:%M"),
        end_time=edt.strftime("%H:%M") if edt else None,
        venue_name=vname, venue_address=vaddr,
        image_url=_og(soup,"og:image"),
        ticket_url=_ticket_url(soup),
        source_url=url,
    )

def _fetch_html(sta_cat, our_cat):
    r = _get(f"{BASE}/tickets/categories/{sta_cat}")
    if not r: return []
    soup = BeautifulSoup(r.text,"html.parser")
    links = _listing_links(soup)
    log.info(f"  HTML: {len(links)} links for {sta_cat}")
    events = []
    for link in links:
        ev = _fetch_detail(link, sta_cat, our_cat)
        if ev: events.append(ev)
    return events

# ── Public entry point ──────────────────────────────────────────────────────

def scrape(use_api=True):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if use_api:
        probe = _get(f"{API}/events", {"per_page":1})
        use_api = probe is not None
    log.info(f"API available: {use_api}")

    all_events, seen = [], set()
    for sta_cat, our_cat in CATEGORY_MAP.items():
        log.info(f"Category: {sta_cat}")
        evs = _fetch_api(sta_cat, our_cat) if use_api else _fetch_html(sta_cat, our_cat)
        for ev in evs:
            if ev.source_id not in seen:
                seen.add(ev.source_id)
                all_events.append(ev)
        log.info(f"  -> {len(evs)} events ({len(all_events)} total)")
    return all_events

if __name__ == "__main__":
    evs = scrape()
    print(f"\nTotal: {len(evs)}")
    for e in evs[:5]:
        print(f"  {e.event_date} {e.start_time} | {e.title[:50]} | {e.venue_name}")

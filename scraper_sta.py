"""
Secret Tel Aviv scraper
Strategy: parse the Events Manager table on /tickets (static HTML, no JS needed).
The listing page has date, time, title, and link for all upcoming events.
Detail pages are fetched for og:description and og:image only.
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
    price_min:    Optional[int] = None
    price_max:    Optional[int] = None


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

EXTERNAL_EVENT_DOMAINS = ["livenation.co.il","ticketmaster.co.il","eventim.co.il","leaan.co.il"]

def _ticket_url(soup):
    for a in soup.find_all("a", href=True):
        if any(d in a["href"] for d in TICKET_DOMAINS):
            return a["href"]
    return None

def _extract_prices_from_text(text: str):
    """Extract price_min, price_max from page text. Returns (None, None) if not found."""
    # Match ₪NN or NN₪ patterns
    shekel_prices = [int(float(m)) for m in re.findall(r"(\d+(?:\.\d+)?)\s*[₪]", text) if 10 <= int(float(m)) <= 2000]
    shekel_prices += [int(float(m)) for m in re.findall(r"[₪]\s*(\d+(?:\.\d+)?)", text) if 10 <= int(float(m)) <= 2000]
    # Match "ILS NN" or "NN ILS"
    ils_prices = [int(float(m)) for m in re.findall(r"(\d+)\s*ILS\b", text, re.I) if 10 <= int(float(m)) <= 2000]
    ils_prices += [int(float(m)) for m in re.findall(r"\bILS\s*(\d+)", text, re.I) if 10 <= int(float(m)) <= 2000]
    all_prices = sorted(set(shekel_prices + ils_prices))
    if not all_prices:
        return None, None
    return all_prices[0], (all_prices[-1] if len(all_prices) > 1 else None)

_SKIP_PRICE_DOMAINS = {"facebook.com", "instagram.com", "youtube.com", "t.me", "twitter.com"}

def _fetch_external_price(url: str):
    """Follow an external ticket URL (e.g. LiveNation) and try to extract price."""
    if any(d in url for d in _SKIP_PRICE_DOMAINS):
        return None, None
    try:
        r = _get(url)
        if not r: return None, None
        text = BeautifulSoup(r.text, "html.parser").get_text(" ")
        return _extract_prices_from_text(text)
    except Exception:
        return None, None

def _prices_from_soup(soup) -> tuple:
    """Extract prices from an STA detail page soup. Follows 'Original Event' external links."""
    # Try direct text extraction first
    text = soup.get_text(" ")
    pmin, pmax = _extract_prices_from_text(text)
    if pmin is not None:
        return pmin, pmax
    # Follow "Original Event" or external domain links
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text_lower = (a.get_text(strip=True) or "").lower()
        is_original = "original event" in text_lower or "לאירוע המקורי" in text_lower
        is_external = any(d in href for d in EXTERNAL_EVENT_DOMAINS + TICKET_DOMAINS)
        if (is_original or is_external) and href.startswith("http") and not any(d in href for d in _SKIP_PRICE_DOMAINS):
            pmin, pmax = _fetch_external_price(href)
            if pmin is not None:
                return pmin, pmax
    return None, None

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
            desc_soup = BeautifulSoup(ev.get("description",""), "html.parser")
            if not ticket:
                ticket = _ticket_url(desc_soup)
            # Try to extract price from description HTML first
            pmin, pmax = _prices_from_soup(desc_soup)
            # If no price in description, fetch the detail page
            if pmin is None:
                detail_url = ev.get("url", f"{BASE}/tickets/{slug}")
                detail_r = _get(detail_url)
                if detail_r:
                    detail_soup = BeautifulSoup(detail_r.text, "html.parser")
                    pmin, pmax = _prices_from_soup(detail_soup)
                    if not ticket:
                        ticket = _ticket_url(detail_soup)
            events.append(Event(
                source_id    = str(ev.get("id", slug)),
                title        = ev.get("title","").strip(),
                description  = desc_soup.get_text(" ",strip=True)[:400],
                category     = cat, subcategory=sub, sta_category=sta_cat,
                event_date   = sdt.date() if sdt else None,
                start_time   = sdt.strftime("%H:%M") if sdt else None,
                end_time     = edt.strftime("%H:%M") if edt else None,
                venue_name   = venue.get("venue"),
                venue_address= ", ".join(filter(None,[venue.get("address"),venue.get("city")])) or None,
                image_url    = (ev.get("image") or {}).get("url"),
                ticket_url   = ticket,
                source_url   = ev.get("url", f"{BASE}/tickets/{slug}"),
                price_min    = pmin,
                price_max    = pmax,
            ))
        if page >= data.get("total_pages",1): break
        page += 1
    return events

# ── Playwright path (STA pages are JS-rendered, requests gets no event data) ─

def _fetch_playwright(sta_cat, our_cat):
    """Scrape a STA category using Playwright to handle JS rendering."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log.warning("playwright not installed; skipping Playwright path for STA")
        return []

    cat, sub = our_cat
    events, seen = [], set()
    today_str = date.today().isoformat()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(
            user_agent=HEADERS["User-Agent"],
            locale="en-US",
        )
        page = ctx.new_page()
        detail = ctx.new_page()

        try:
            cat_url = f"{BASE}/tickets/categories/{sta_cat}"
            log.info(f"  Playwright: loading {cat_url}")
            page.goto(cat_url, timeout=25000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            # Collect event links from rendered DOM
            links = page.eval_on_selector_all(
                f"a[href*='/tickets/']",
                """els => [...new Set(els
                    .map(e => e.href)
                    .filter(h => /secrettelaviv\.com\/tickets\/[^/]+\/?$/.test(h) && !h.includes('/categories/'))
                )]"""
            )
            log.info(f"  Playwright: {len(links)} links for {sta_cat}")

            for url in links:
                slug = url.rstrip("/").rsplit("/", 1)[-1]
                if slug in seen: continue
                seen.add(slug)

                try:
                    detail.goto(url, timeout=20000, wait_until="domcontentloaded")
                    detail.wait_for_timeout(2000)

                    # Extract via page evaluate (works on JS-rendered content)
                    data = detail.evaluate("""() => {
                        const getText = sel => (document.querySelector(sel) || {}).innerText || '';
                        const getMeta = prop => {
                            const m = document.querySelector(`meta[property="${prop}"], meta[name="${prop}"]`);
                            return m ? m.content : '';
                        };
                        // Dates from <time> or tribe-events elements
                        const times = [...document.querySelectorAll('time[datetime], .tribe-events-start-datetime, .tribe-event-date-start, abbr.tribe-events-abbr')];
                        const datetimes = times.map(t => t.getAttribute('datetime') || t.getAttribute('title') || t.innerText).filter(Boolean);
                        // Venue
                        const venueEl = document.querySelector('.tribe-venue, [class*="venue"]');
                        const venueLines = venueEl ? venueEl.innerText.trim().split('\\n').filter(Boolean) : [];
                        return {
                            title: getMeta('og:title'),
                            description: getMeta('og:description'),
                            image: getMeta('og:image'),
                            datetimes,
                            venueName: venueLines[0] || '',
                            bodyText: document.body.innerText,
                        };
                    }""")

                    title = re.sub(r"\s*\|\s*Secret Tel Aviv.*$", "", data.get("title","")).strip()
                    if not title: continue

                    # Parse date/time from datetimes list or body text
                    sdt = edt = None
                    for dt_str in data.get("datetimes", []):
                        dt = _parse_dt(dt_str.replace("Z",""))
                        if dt:
                            if not sdt: sdt = dt
                            elif not edt: edt = dt

                    # Fallback: search body text for ISO date
                    if not sdt:
                        body = data.get("bodyText", "")
                        for m in re.finditer(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", body):
                            dt = _parse_dt(m.group(1))
                            if dt:
                                if not sdt: sdt = dt
                                elif not edt: edt = dt

                    if not sdt or sdt.date().isoformat() < today_str: continue

                    # Price from body text
                    body = data.get("bodyText","")
                    soup_body = BeautifulSoup(detail.content(), "html.parser")
                    pmin, pmax = _prices_from_soup(soup_body)

                    # Ticket URL
                    ticket = detail.evaluate("""() => {
                        const domains = ['entrio.co.il','eventbrite.com','ticketmaster.co.il','tickets.co.il'];
                        for (const a of document.querySelectorAll('a[href]')) {
                            if (domains.some(d => a.href.includes(d))) return a.href;
                        }
                        return null;
                    }""")

                    venue_name = data.get("venueName") or None
                    events.append(Event(
                        source_id=slug, title=title,
                        description=data.get("description","")[:400],
                        category=cat, subcategory=sub, sta_category=sta_cat,
                        event_date=sdt.date(),
                        start_time=sdt.strftime("%H:%M"),
                        end_time=edt.strftime("%H:%M") if edt else None,
                        venue_name=venue_name, venue_address=None,
                        image_url=data.get("image"),
                        ticket_url=ticket,
                        source_url=url,
                        price_min=pmin,
                        price_max=pmax,
                    ))
                    time.sleep(0.5)
                except Exception as e:
                    log.debug(f"  STA detail {url}: {e}")
        finally:
            detail.close()
            page.close()
            browser.close()

    log.info(f"  Playwright path: {len(events)} events for {sta_cat}")
    return events

# ── Listing-table scraper (primary path) ────────────────────────────────────

# Keyword → (category, subcategory) inference from title
_MUSIC_KW    = re.compile(r"\blive\b|concert|band|להקה|הופעה|מופע", re.I)
_DJ_KW       = re.compile(r"\bparty\b|dj\b|rave|techno|trance|house|electronic|מסיבה", re.I)
_STANDUP_KW  = re.compile(r"stand.?up|סטנד.?אפ|comedy|קומדי", re.I)
_FILM_KW     = re.compile(r"\bfilm\b|cinema|screening|הקרנה", re.I)
_MARKET_KW   = re.compile(r"market|fair|שוק|יריד", re.I)
_FOOD_KW     = re.compile(r"food|dinner|tasting|wine|אוכל|טעימות|יין", re.I)
_CULTURAL_KW = re.compile(r"tour|exhibit|lecture|talk|book|reading|workshop|סיור|תערוכה|הרצאה", re.I)

def _infer_sta_cat(title, desc=""):
    combined = f"{title} {desc}"
    if _STANDUP_KW.search(combined):   return "standup",  "standup"
    if _FILM_KW.search(combined):      return "cultural", "film"
    if _FOOD_KW.search(combined):      return "market",   "food"
    if _MARKET_KW.search(combined):    return "market",   "crafts"
    if _CULTURAL_KW.search(combined):  return "cultural", "general"
    if _DJ_KW.search(combined):        return "music",    "dj-set"
    if _MUSIC_KW.search(combined):     return "music",    "live"
    return "cultural", "general"

def _parse_sta_time(time_str):
    """Convert '6:00 pm' → '18:00'"""
    m = re.search(r"(\d{1,2}):(\d{2})\s*(am|pm)", time_str, re.I)
    if not m: return None
    hh, mm, ampm = int(m.group(1)), int(m.group(2)), m.group(3).lower()
    if ampm == "pm" and hh != 12: hh += 12
    if ampm == "am" and hh == 12: hh = 0
    return f"{hh:02d}:{mm:02d}"

def _scrape_listing_table():
    """Parse the Events Manager table on /tickets — one request, all events."""
    r = _get(f"{BASE}/tickets")
    if not r: return []
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table", class_="events-table")
    if not table:
        log.warning("STA: events-table not found on /tickets")
        return []

    rows = table.find_all("tr")[1:]  # skip header row
    log.info(f"STA: found {len(rows)} table rows")
    events, seen, today = [], set(), date.today()

    for row in rows:
        tds = row.find_all("td")
        if len(tds) < 3: continue

        date_td  = tds[1].get_text(separator=" ").strip()
        event_td = tds[2]
        price_td = tds[3].get_text(separator=" ").strip() if len(tds) > 3 else ""

        # Parse date
        m_date = re.search(r"(\d{1,2})/(\d{2})/(\d{4})", date_td)
        if not m_date: continue
        try:
            ev_date = date(int(m_date.group(3)), int(m_date.group(2)), int(m_date.group(1)))
        except ValueError:
            continue
        if ev_date < today: continue

        # Parse time
        start_time = _parse_sta_time(date_td)
        end_time   = None
        m_times = re.findall(r"\d{1,2}:\d{2}\s*(?:am|pm)", date_td, re.I)
        if len(m_times) >= 2:
            end_time = _parse_sta_time(m_times[1])

        # Title and URL
        link = event_td.find("a", href=True)
        if not link: continue
        title = link.get_text(strip=True)
        url   = link["href"]
        slug  = url.rstrip("/").rsplit("/", 1)[-1]
        if slug in seen: continue
        seen.add(slug)

        # Venue from "Title @ Venue" pattern
        venue_name = None
        m_at = re.search(r"@\s+(.+)$", title)
        if m_at:
            venue_name = m_at.group(1).strip()
            title = title[:m_at.start()].strip()

        # Fetch detail page for description, image, ticket URL, price.
        # Some STA pages redirect to external sites (Facebook etc.) — detect and skip.
        description, image_url, ticket_url = "", None, None
        pmin, pmax = _prices_from_soup(BeautifulSoup(price_td, "html.parser"))

        try:
            r2 = session.get(url, timeout=12, allow_redirects=True)
            # If we ended up on an external domain, use it as ticket_url and skip parse
            if BASE not in r2.url:
                ticket_url = r2.url
            elif r2.ok:
                s2 = BeautifulSoup(r2.text, "html.parser")
                description = (_og(s2, "og:description") or "")[:400]
                image_url   = _og(s2, "og:image")
                ticket_url  = _ticket_url(s2)
                if pmin is None:
                    pmin, pmax = _prices_from_soup(s2)
            time.sleep(0.4)
        except Exception as e:
            log.debug(f"STA detail {url}: {e}")

        category, subcategory = _infer_sta_cat(title, description)

        events.append(Event(
            source_id    = slug,
            title        = title,
            description  = description,
            category     = category,
            subcategory  = subcategory,
            sta_category = "",
            event_date   = ev_date,
            start_time   = start_time,
            end_time     = end_time,
            venue_name   = venue_name,
            venue_address= None,
            image_url    = image_url,
            ticket_url   = ticket_url,
            source_url   = url,
            price_min    = pmin,
            price_max    = pmax,
        ))
        time.sleep(0.4)

    log.info(f"STA: {len(events)} future events parsed from listing table")
    return events

# ── Public entry point ──────────────────────────────────────────────────────

def scrape(use_api=True):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    # Try API first (fast, structured); fall back to listing-table parser
    if use_api:
        probe = _get(f"{API}/events", {"per_page":1})
        use_api = probe is not None
    log.info(f"STA API available: {use_api}")

    if use_api:
        all_events, seen = [], set()
        for sta_cat, our_cat in CATEGORY_MAP.items():
            log.info(f"Category: {sta_cat}")
            evs = _fetch_api(sta_cat, our_cat)
            for ev in evs:
                if ev.source_id not in seen:
                    seen.add(ev.source_id)
                    all_events.append(ev)
            log.info(f"  -> {len(evs)} events ({len(all_events)} total)")
        return all_events
    else:
        return _scrape_listing_table()

if __name__ == "__main__":
    evs = scrape()
    print(f"\nTotal: {len(evs)}")
    for e in evs[:10]:
        print(f"  {e.event_date} {e.start_time} | {e.title[:50]:<50} | {e.venue_name}")

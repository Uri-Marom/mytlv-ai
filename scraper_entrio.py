"""
Entrio.co.il scraper
Israel's main ticketing platform. No public API — scrape search results.
Entrio uses client-side rendering (React) so we hit their internal search endpoint.
"""
import re, time, logging
from datetime import date, datetime
from typing import Optional
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)
BASE = "https://www.entrio.co.il"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "he-IL,he;q=0.9,en;q=0.8",
    "Referer": "https://www.entrio.co.il/",
}

# Entrio category IDs for Tel Aviv cultural/music events
SEARCH_TERMS = [
    ("מוזיקה",   "music",    "live"),
    ("מסיבה",    "music",    "dj-set"),
    ("פסטיבל",   "music",    "festival"),
    ("תרבות",    "cultural", "general"),
    ("שוק",      "market",   "crafts"),
]

@dataclass
class Event:
    source_id:   str
    title:       str
    description: str
    category:    str
    subcategory: str
    event_date:  Optional[date]
    start_time:  Optional[str]
    venue_name:  Optional[str]
    neighborhood:Optional[str]
    image_url:   Optional[str]
    ticket_url:  Optional[str]
    price_min:   int
    price_max:   Optional[int]
    source_url:  str

session = requests.Session()
session.headers.update(HEADERS)

def _get(url, params=None, retries=3):
    for i in range(retries):
        try:
            r = session.get(url, params=params, timeout=15)
            r.raise_for_status()
            time.sleep(1.5)
            return r
        except Exception as e:
            log.warning(f"  attempt {i+1}: GET {url}: {e}")
            time.sleep(2*(i+1))
    return None

def _parse_date(s):
    """Parse Entrio date strings like '14/06/2026' or '2026-06-14'"""
    if not s: return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d.%m.%Y"):
        try: return datetime.strptime(s.strip(), fmt).date()
        except: pass
    return None

def _parse_price(s):
    """Return (min, max) price from string like '₪50-₪120' or 'חינם'"""
    if not s: return 0, None
    if "חינ" in s or "free" in s.lower(): return 0, 0
    nums = re.findall(r"\d+", s)
    if not nums: return 0, None
    nums = [int(n) for n in nums]
    return min(nums), max(nums)

def _scrape_listing_page(term, category, subcategory, city="תל-אביב"):
    """Scrape Entrio search/listing page for a keyword + city."""
    # Entrio search URL pattern
    url = f"{BASE}/events"
    params = {"q": term, "city": city}
    r = _get(url, params=params)
    if not r: return []

    soup = BeautifulSoup(r.text, "html.parser")
    events = []

    # Entrio event cards: <div class="event-card"> or similar
    # Try multiple selector patterns as Entrio updates its markup
    cards = (
        soup.select("div.event-card") or
        soup.select("article.event") or
        soup.select("[data-event-id]") or
        soup.select(".event-item")
    )
    log.info(f"  Entrio '{term}': {len(cards)} cards found")

    for card in cards:
        ev = _parse_card(card, category, subcategory)
        if ev: events.append(ev)

    # If no cards found, try JSON-LD structured data
    if not events:
        events = _parse_json_ld(soup, category, subcategory)

    return events

def _parse_card(card, category, subcategory):
    try:
        # Title
        title_el = card.select_one("h2,h3,.event-title,.title")
        title = title_el.get_text(strip=True) if title_el else ""
        if not title: return None

        # Link / source_id
        link_el = card.select_one("a[href]")
        href = link_el["href"] if link_el else ""
        if not href: return None
        if href.startswith("/"): href = BASE + href
        source_id = href.rstrip("/").rsplit("/",1)[-1]

        # Date
        date_el = card.select_one(".event-date,.date,time")
        dt = None
        if date_el:
            dt = _parse_date(date_el.get("datetime") or date_el.get_text(strip=True))

        # Venue
        venue_el = card.select_one(".venue,.location,.event-venue")
        venue_name = venue_el.get_text(strip=True) if venue_el else None

        # Price
        price_el = card.select_one(".price,.event-price")
        pmin, pmax = _parse_price(price_el.get_text(strip=True) if price_el else "")

        # Image
        img_el = card.select_one("img")
        img_url = img_el.get("src") or img_el.get("data-src") if img_el else None

        return Event(
            source_id=source_id, title=title, description="",
            category=category, subcategory=subcategory,
            event_date=dt, start_time=None,
            venue_name=venue_name, neighborhood=None,
            image_url=img_url, ticket_url=href,
            price_min=pmin, price_max=pmax,
            source_url=href,
        )
    except Exception as e:
        log.debug(f"  card parse error: {e}")
        return None

def _parse_json_ld(soup, category, subcategory):
    """Fallback: parse JSON-LD Event schema blocks."""
    import json
    events = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get("@type") not in ("Event","MusicEvent"): continue
                name = item.get("name","").strip()
                if not name: continue
                url  = item.get("url","")
                slug = url.rstrip("/").rsplit("/",1)[-1]
                sdt  = _parse_date(item.get("startDate","")[:10])
                loc  = item.get("location",{})
                venue= loc.get("name") if isinstance(loc,dict) else None
                offers = item.get("offers",{})
                if isinstance(offers,list): offers = offers[0] if offers else {}
                pmin, pmax = _parse_price(str(offers.get("price","")))
                events.append(Event(
                    source_id=slug or name[:30], title=name, description=item.get("description","")[:300],
                    category=category, subcategory=subcategory,
                    event_date=sdt, start_time=None,
                    venue_name=venue, neighborhood=None,
                    image_url=item.get("image"),
                    ticket_url=url, price_min=pmin, price_max=pmax,
                    source_url=url,
                ))
        except: pass
    return events

def scrape():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    all_events, seen = [], set()
    for term, cat, sub in SEARCH_TERMS:
        log.info(f"Entrio term: {term}")
        evs = _scrape_listing_page(term, cat, sub)
        for ev in evs:
            if ev.source_id not in seen and ev.event_date:
                seen.add(ev.source_id)
                all_events.append(ev)
    log.info(f"Entrio total: {len(all_events)}")
    return all_events

if __name__ == "__main__":
    evs = scrape()
    for e in evs[:5]:
        print(f"  {e.event_date} | {e.title[:50]} | {e.venue_name}")

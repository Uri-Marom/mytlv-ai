"""
mytlv.ai — Event refresh pipeline (Secret Tel Aviv HTML scraper → Neon Postgres)
Usage:  source .env.local && python refresh_pipeline.py
Flags:  --dry-run   print events without writing to DB
        --since     ISO date to keep (default 2026-06-12)
"""
import os, re, sys, json, time, logging, argparse
from datetime import date, datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional

import requests
from bs4 import BeautifulSoup
import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
    "Accept-Language": "en-US,en;q=0.9",
}

CATEGORY_MAP = {
    "parties":            ("music",    "dj-set"),
    "live-music":         ("music",    "live"),
    "music-festivals":    ("music",    "festival"),
    "culture-highlights": ("cultural", "general"),
    "exhibitions":        ("cultural", "exhibition"),
    "food-events":        ("market",   "food"),
    "shopping":           ("market",   "crafts"),
}

TICKET_DOMAINS = ["entrio.co.il", "eventbrite.com", "ticketmaster.co.il", "tickets.co.il"]

BASE = "https://www.secrettelaviv.com"

# ── Data class ───────────────────────────────────────────────────────────────

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
    neighborhood: Optional[str]
    image_url:    Optional[str]
    ticket_url:   Optional[str]
    source_url:   str
    price_min:    int = 0
    price_max:    Optional[int] = None
    tags:         list = field(default_factory=list)

# ── HTTP helpers ─────────────────────────────────────────────────────────────

session = requests.Session()
session.headers.update(HEADERS)

def _get(url, retries=3, delay=1.0):
    for i in range(retries):
        try:
            r = session.get(url, timeout=15)
            r.raise_for_status()
            time.sleep(delay)
            return r
        except Exception as e:
            log.warning(f"  attempt {i+1}/{retries} {url}: {e}")
            time.sleep(2 * (i + 1))
    return None

# ── Parsers ──────────────────────────────────────────────────────────────────

MONTH_MAP = {
    "january":1,"february":2,"march":3,"april":4,"may":5,"june":6,
    "july":7,"august":8,"september":9,"october":10,"november":11,"december":12,
    "jan":1,"feb":2,"mar":3,"apr":4,"jun":6,"jul":7,"aug":8,
    "sep":9,"oct":10,"nov":11,"dec":12,
}

def _parse_date_text(text: str) -> Optional[date]:
    """Parse STA's date strings like 'Wed 29 July 2026' or '14/06/2026'."""
    text = text.strip()
    # numeric: 14/06/2026 or 2026-06-14
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except: pass
    # textual: "Wed 29 July 2026" or "29 July 2026"
    m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", text)
    if m:
        day, mon, yr = int(m.group(1)), m.group(2).lower(), int(m.group(3))
        if mon in MONTH_MAP:
            try:
                return date(yr, MONTH_MAP[mon], day)
            except: pass
    return None

def _parse_time_text(text: str) -> Optional[str]:
    """Parse '8:00 pm' or '21:00' → '21:00'."""
    m = re.search(r"(\d{1,2}):(\d{2})\s*(am|pm)?", text, re.I)
    if not m: return None
    h, mi = int(m.group(1)), int(m.group(2))
    ampm = (m.group(3) or "").lower()
    if ampm == "pm" and h != 12: h += 12
    if ampm == "am" and h == 12: h = 0
    return f"{h:02d}:{mi:02d}"

def _parse_price(text: str):
    if not text: return 0, None
    text = text.lower()
    if "free" in text or "חינ" in text: return 0, None
    nums = [int(n) for n in re.findall(r"\d+", text) if int(n) < 10000]
    if not nums: return 0, None
    return min(nums), (max(nums) if len(nums) > 1 else None)

def _og(soup, prop):
    t = soup.find("meta", property=prop)
    return t["content"].strip() if t and t.get("content") else None

def _ticket_url(soup):
    for a in soup.find_all("a", href=True):
        if any(d in a["href"] for d in TICKET_DOMAINS):
            return a["href"]
    return None

def _infer_neighborhood(venue_name: str) -> Optional[str]:
    """Best-effort neighborhood from known Tel Aviv venues."""
    if not venue_name: return None
    v = venue_name.lower()
    if any(x in v for x in ["port", "namal", "hangar"]): return "Tel Aviv Port"
    if any(x in v for x in ["florentin", "kuli alma", "alphabet"]): return "Florentin"
    if any(x in v for x in ["rothschild", "cinematheque", "habima", "suzanne"]): return "City Center"
    if any(x in v for x in ["jaffa", "yafo", "clock tower"]): return "Jaffa"
    if any(x in v for x in ["allenby", "levontin", "dixie"]): return "South TLV"
    if any(x in v for x in ["reading", "barby", "yarkon"]): return "North TLV"
    if any(x in v for x in ["dizengoff", "ibn gabirol"]): return "City Center"
    return None

def _infer_tags(title: str, category: str, subcategory: str, price_min: int) -> list:
    tags = []
    title_l = title.lower()
    if price_min == 0: tags.append("Free")
    if "pride" in title_l or "lgbtq" in title_l: tags.append("Pride")
    if "outdoor" in title_l or "park" in title_l: tags.append("Outdoor")
    if "festival" in title_l: tags.append("Festival")
    if "market" in title_l or "shuk" in title_l: tags.append("Market")
    if subcategory == "dj-set": tags.append("Electronic")
    if subcategory == "live": tags.append("Live Music")
    if subcategory == "exhibition": tags.append("Art")
    return tags

# ── Event detail scraper ─────────────────────────────────────────────────────

def scrape_detail(url: str, sta_category: str) -> Optional[Event]:
    r = _get(url, delay=0.8)
    if not r: return None
    soup = BeautifulSoup(r.text, "html.parser")

    # Title from OG or H1
    title = _og(soup, "og:title") or ""
    title = re.sub(r"\s*[|–—]\s*Secret Tel Aviv.*$", "", title).strip()
    if not title: return None

    # Venue: STA often puts it after @ in the title
    venue_name = None
    at_match = re.search(r"@\s+(.+?)(?:\s*[\|–]|$)", title)
    if at_match:
        venue_name = at_match.group(1).strip()
        title = title[:at_match.start()].strip()

    # Description
    description = _og(soup, "og:description") or ""
    description = description[:400]

    # Image
    image_url = _og(soup, "og:image")

    # Date + time from text nodes
    full_text = soup.get_text(" ")
    event_date, start_time, end_time = None, None, None

    # Look for date patterns in text
    date_patterns = re.finditer(
        r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\d{1,2}\s+[A-Za-z]+\s+\d{4}"
        r"|\d{1,2}\s+[A-Za-z]+\s+\d{4}"
        r"|\d{1,2}/\d{2}/\d{4}",
        full_text, re.I
    )
    for m in date_patterns:
        d = _parse_date_text(m.group())
        if d and d.year >= 2026:
            event_date = d
            break

    # Look for time patterns
    time_matches = re.findall(r"\d{1,2}:\d{2}\s*(?:am|pm)?", full_text, re.I)
    if time_matches:
        start_time = _parse_time_text(time_matches[0])
        end_time   = _parse_time_text(time_matches[1]) if len(time_matches) > 1 else None

    if not event_date: return None  # skip if we can't determine date

    # Price: look for ₪ or "free" near the page
    price_min, price_max = 0, None
    price_match = re.search(r"[₪\$]\s*(\d+)(?:\s*[-–]\s*[₪\$]?\s*(\d+))?", full_text)
    if price_match:
        price_min = int(price_match.group(1))
        price_max = int(price_match.group(2)) if price_match.group(2) else None
    elif re.search(r"\bfree\b|\bchinom\b|חינם", full_text, re.I):
        price_min, price_max = 0, None

    # Ticket URL
    ticket = _ticket_url(soup)

    # Category from the listing category
    cat, sub = CATEGORY_MAP.get(sta_category, ("cultural", "general"))

    slug = url.rstrip("/").rsplit("/", 1)[-1]
    neighborhood = _infer_neighborhood(venue_name)
    tags = _infer_tags(title, cat, sub, price_min)

    return Event(
        source_id=slug, title=title.strip(),
        description=description, category=cat, subcategory=sub,
        sta_category=sta_category, event_date=event_date,
        start_time=start_time, end_time=end_time,
        venue_name=venue_name, neighborhood=neighborhood,
        image_url=image_url, ticket_url=ticket, source_url=url,
        price_min=price_min, price_max=price_max, tags=tags,
    )

# ── Listing scraper ──────────────────────────────────────────────────────────

def get_event_links(sta_category: str) -> list[tuple[str, str]]:
    """Return [(url, category), ...] from a STA category listing page."""
    r = _get(f"{BASE}/tickets/categories/{sta_category}")
    if not r: return []
    soup = BeautifulSoup(r.text, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        h = a["href"]
        if re.match(r"https://www\.secrettelaviv\.com/tickets/[^/]+/?$", h) and "/categories/" not in h:
            links.add(h.rstrip("/"))
    log.info(f"  {sta_category}: {len(links)} links")
    return [(url, sta_category) for url in links]

# ── DB upsert ────────────────────────────────────────────────────────────────

def upsert_events(events: list[Event], conn):
    rows = [(
        "secret_tel_aviv", e.source_id, e.title, e.description,
        e.category, e.subcategory, e.sta_category,
        e.venue_name, e.neighborhood,
        str(e.event_date), e.start_time, e.end_time,
        e.price_min, e.price_max,
        e.image_url, e.ticket_url, e.source_url, e.tags,
    ) for e in events]

    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO events (
                source, source_id, title, description,
                category, subcategory, sta_category,
                venue_name, neighborhood,
                event_date, start_time, end_time,
                price_min, price_max,
                image_url, ticket_url, source_url, tags
            ) VALUES %s
            ON CONFLICT (source, source_id) DO UPDATE SET
                title        = EXCLUDED.title,
                description  = EXCLUDED.description,
                category     = EXCLUDED.category,
                subcategory  = EXCLUDED.subcategory,
                venue_name   = EXCLUDED.venue_name,
                neighborhood = EXCLUDED.neighborhood,
                event_date   = EXCLUDED.event_date,
                start_time   = EXCLUDED.start_time,
                end_time     = EXCLUDED.end_time,
                price_min    = EXCLUDED.price_min,
                price_max    = EXCLUDED.price_max,
                image_url    = EXCLUDED.image_url,
                ticket_url   = EXCLUDED.ticket_url,
                tags         = EXCLUDED.tags,
                updated_at   = NOW()
        """, rows)
    conn.commit()

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--since", default="2026-06-12", help="Keep events from this date forward")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()

    since = date.fromisoformat(args.since)
    log.info(f"Refreshing events since {since} (dry_run={args.dry_run})")

    # Step 1: collect all event links across categories
    log.info("Step 1: collecting event links...")
    all_links: list[tuple[str, str]] = []
    seen_urls: set[str] = set()
    for cat in CATEGORY_MAP:
        for url, sta_cat in get_event_links(cat):
            if url not in seen_urls:
                seen_urls.add(url)
                all_links.append((url, sta_cat))
    log.info(f"  Total unique links: {len(all_links)}")

    # Step 2: scrape each event detail page (parallel)
    log.info(f"Step 2: scraping {len(all_links)} event pages ({args.workers} workers)...")
    events: list[Event] = []
    errors = 0

    def fetch(url_cat):
        url, cat = url_cat
        try:
            return scrape_detail(url, cat)
        except Exception as e:
            log.warning(f"  error {url}: {e}")
            return None

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(fetch, lc): lc for lc in all_links}
        for i, fut in enumerate(as_completed(futures), 1):
            ev = fut.result()
            if ev:
                if ev.event_date >= since:
                    events.append(ev)
            else:
                errors += 1
            if i % 20 == 0:
                log.info(f"  {i}/{len(all_links)} done, {len(events)} valid so far")

    # Deduplicate by source_id (keep most-categorized)
    seen_ids: dict[str, Event] = {}
    for ev in events:
        if ev.source_id not in seen_ids:
            seen_ids[ev.source_id] = ev
    events = list(seen_ids.values())
    events.sort(key=lambda e: (e.event_date, e.start_time or ""))

    log.info(f"  {len(events)} valid events since {since} ({errors} errors/skipped)")
    for ev in events:
        log.info(f"  {ev.event_date} {ev.start_time or '?':5} | {ev.title[:45]:<45} | {ev.venue_name or '?'}")

    if args.dry_run:
        log.info("Dry run — not writing to DB")
        return

    # Step 3: write to Neon
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        sys.exit("DATABASE_URL not set — run: source .env.local && python refresh_pipeline.py")

    conn = psycopg2.connect(db_url)

    # Delete stale events from the same source that are before `since`
    with conn.cursor() as cur:
        cur.execute("DELETE FROM events WHERE source='secret_tel_aviv' AND event_date < %s", (str(since),))
        deleted = cur.rowcount
    conn.commit()
    log.info(f"Step 3: deleted {deleted} stale events before {since}")

    upsert_events(events, conn)
    conn.close()

    log.info(f"Done — {len(events)} events upserted into Neon")

if __name__ == "__main__":
    main()

"""
Entrio.co.il scraper (Playwright-based)
Israel's main ticketing platform. The site is geo-restricted to Israeli IPs;
running this from outside Israel will fail with DNS resolution errors.

Usage (from Israeli network):
  python scraper_entrio.py [--dry-run]
"""
import re, time, logging, argparse, sys, os
from datetime import date, datetime
from dataclasses import dataclass
from typing import Optional

log = logging.getLogger(__name__)

BASE = "https://www.entrio.co.il"

SEARCH_TERMS = [
    ("מוזיקה",  "music",    "live"),
    ("מסיבה",   "music",    "dj-set"),
    ("פסטיבל",  "music",    "festival"),
    ("תרבות",   "cultural", "general"),
    ("שוק",     "market",   "crafts"),
    ("אוכל",    "market",   "food"),
    ("תערוכה",  "cultural", "exhibition"),
]


@dataclass
class Event:
    source_id:    str
    title:        str
    description:  str
    category:     str
    subcategory:  str
    event_date:   Optional[date]
    start_time:   Optional[str]
    venue_name:   Optional[str]
    neighborhood: Optional[str]
    image_url:    Optional[str]
    ticket_url:   Optional[str]
    price_min:    int
    price_max:    Optional[int]
    source_url:   str


def _parse_date(s: str) -> Optional[date]:
    if not s: return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d.%m.%Y"):
        try: return datetime.strptime(s.strip()[:10], fmt).date()
        except: pass
    return None


def _parse_price(s: str):
    if not s: return 0, None
    if "חינ" in s or "free" in s.lower(): return 0, None
    nums = [int(n) for n in re.findall(r"\d+", s) if int(n) < 5000]
    if not nums: return 0, None
    return min(nums), (max(nums) if len(nums) > 1 else None)


def scrape():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log.error("playwright not installed: pip install playwright && playwright install chromium")
        return []

    all_events, seen = [], set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            locale="he-IL",
        )

        for term, category, subcategory in SEARCH_TERMS:
            page = ctx.new_page()
            try:
                url = f"{BASE}/events?q={term}"
                log.info(f"Entrio: searching '{term}' ({category}/{subcategory})")
                page.goto(url, timeout=20000, wait_until="domcontentloaded")
                time.sleep(3)

                cards = page.evaluate("""() => {
                    const results = [];
                    // Try common event card selectors
                    const selectors = ['.event-card', '.event-item', 'article[class*="event"]',
                                       '[data-event-id]', '.card'];
                    let found = [];
                    for (const sel of selectors) {
                        found = [...document.querySelectorAll(sel)];
                        if (found.length > 0) break;
                    }
                    // Fallback: JSON-LD structured data
                    if (found.length === 0) {
                        document.querySelectorAll('script[type="application/ld+json"]').forEach(s => {
                            try {
                                const d = JSON.parse(s.textContent);
                                const items = Array.isArray(d) ? d : [d];
                                items.filter(i => ['Event','MusicEvent'].includes(i['@type'])).forEach(ev => {
                                    results.push({
                                        title: ev.name || '',
                                        url: ev.url || '',
                                        date: (ev.startDate || '').slice(0, 10),
                                        time: (ev.startDate || '').slice(11, 16),
                                        venue: ((ev.location || {}).name || ''),
                                        price: String(((ev.offers || {}).price) || ''),
                                        img: ev.image || '',
                                        desc: ev.description || '',
                                    });
                                });
                            } catch {}
                        });
                        return results;
                    }
                    found.forEach(card => {
                        const a = card.querySelector('a[href]');
                        const titleEl = card.querySelector('h2,h3,h4,.title,.event-title,[class*="title"]');
                        const dateEl = card.querySelector('.date,time,[class*="date"]');
                        const venueEl = card.querySelector('.venue,.location,[class*="venue"]');
                        const priceEl = card.querySelector('.price,[class*="price"]');
                        const imgEl = card.querySelector('img');
                        results.push({
                            title: titleEl ? titleEl.innerText.trim() : '',
                            url: a ? a.href : '',
                            date: dateEl ? (dateEl.getAttribute('datetime') || dateEl.innerText.trim()) : '',
                            venue: venueEl ? venueEl.innerText.trim() : '',
                            price: priceEl ? priceEl.innerText.trim() : '',
                            img: imgEl ? (imgEl.src || imgEl.dataset.src || '') : '',
                            desc: '',
                        });
                    });
                    return results;
                }""")

                log.info(f"  → {len(cards)} cards")

                for c in cards:
                    title = (c.get("title") or "").strip()
                    if not title: continue
                    href = c.get("url") or ""
                    slug = href.rstrip("/").rsplit("/", 1)[-1] if href else title[:30]
                    key = f"entrio-{slug}"
                    if key in seen: continue
                    seen.add(key)

                    ev_date = _parse_date(c.get("date", ""))
                    venue = (c.get("venue") or "").strip()
                    pmin, pmax = _parse_price(c.get("price", ""))

                    all_events.append(Event(
                        source_id=slug,
                        title=title,
                        description=(c.get("desc") or "")[:300],
                        category=category,
                        subcategory=subcategory,
                        event_date=ev_date,
                        start_time=c.get("time") or None,
                        venue_name=venue or None,
                        neighborhood=None,
                        image_url=c.get("img") or None,
                        ticket_url=href or None,
                        price_min=pmin,
                        price_max=pmax,
                        source_url=href or url,
                    ))

            except Exception as e:
                log.warning(f"Entrio '{term}': {e}")
            finally:
                page.close()
            time.sleep(1.5)

        browser.close()

    log.info(f"Entrio total: {len(all_events)} events")
    return all_events


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    events = scrape()

    if args.dry_run:
        for e in events[:20]:
            print(f"  {e.event_date} | {e.title[:50]} | {e.venue_name}")
        print(f"Total: {len(events)}")
        sys.exit(0)

    import psycopg2
    from psycopg2.extras import execute_values

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        sys.exit("DATABASE_URL not set")

    conn = psycopg2.connect(db_url)
    rows = [(
        "entrio", e.source_id, e.title, e.description,
        e.category, e.subcategory, None,
        e.venue_name, e.neighborhood,
        str(e.event_date) if e.event_date else None,
        e.start_time, None, e.price_min, e.price_max,
        e.image_url, e.ticket_url, e.source_url, [],
        [e.category],
    ) for e in events if e.event_date]

    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO events (
                source, source_id, title, description,
                category, subcategory, sta_category,
                venue_name, neighborhood,
                event_date, start_time, end_time,
                price_min, price_max,
                image_url, ticket_url, source_url, tags, categories
            ) VALUES %s
            ON CONFLICT (source, source_id) DO UPDATE SET
                title=EXCLUDED.title, event_date=EXCLUDED.event_date,
                price_min=EXCLUDED.price_min, updated_at=NOW()
        """, rows)
    conn.commit()
    conn.close()
    print(f"Upserted {len(rows)} Entrio events")

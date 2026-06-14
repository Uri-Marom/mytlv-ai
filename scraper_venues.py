"""
mytlv.ai — Direct venue scraper
Scrapes Barby and Levontin 7 using Playwright (both are JS-rendered).
Hangar 11 uses plain requests.

Usage:
  source .env.local && python scraper_venues.py            # scrape + upsert
  python scraper_venues.py --dry-run                       # print only
  python scraper_venues.py --venue barby                   # single venue
"""
import os, re, sys, time, logging, argparse
from datetime import date, datetime
from dataclasses import dataclass, field
from typing import Optional
import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ── Venue config ─────────────────────────────────────────────────────────────

VENUES = {
    "barby": {
        "label":        "Barby",
        "url":          "https://www.barby.co.il",
        "events_url":   "https://www.barby.co.il",
        "neighborhood": "Jaffa Port",
        "category":     "music",
        "subcategory":  "live",
        "strategy":     "playwright",
    },
    "levontin7": {
        "label":        "Levontin 7",
        "url":          "https://levontin7.com",
        "events_url":   "https://levontin7.com/events/",
        "neighborhood": "Florentin",
        "category":     "music",
        "subcategory":  "live",
        "strategy":     "playwright",
    },
    "hangar11": {
        "label":        "Hangar 11",
        "url":          "https://hangar11.co.il",
        "events_url":   "https://hangar11.co.il/events/",
        "neighborhood": "Tel Aviv Port",
        "category":     "music",
        "subcategory":  "live",
        "strategy":     "html",
    },
    "beit_radical": {
        "label":        "Beit Radical",
        "url":          "https://radical.org.il",
        "events_url":   "https://radical.org.il/events/",
        "neighborhood": "Herzl Hill",
        "category":     "cultural",
        "subcategory":  "talk",
        "strategy":     "playwright",
    },
    "hameretz2": {
        "label":        "Hameretz 2",
        "url":          "https://hameretz2.org",
        "events_url":   "https://hameretz2.org",
        "neighborhood": "South TLV",
        "category":     "cultural",
        "subcategory":  "general",
        "strategy":     "playwright",
    },
}

# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class VenueEvent:
    source:      str
    source_id:   str
    title:       str
    venue_name:  str
    neighborhood: Optional[str]
    category:    str
    subcategory: str
    event_date:  Optional[date]
    start_time:  Optional[str]
    end_time:    Optional[str]
    image_url:   Optional[str]
    ticket_url:  Optional[str]
    source_url:  str
    price_min:   Optional[int] = None
    price_max:   Optional[int] = None
    description: str = ""
    tags:        list = field(default_factory=list)

# ── Helpers ───────────────────────────────────────────────────────────────────

HE_MONTHS = {"ינואר":1,"פברואר":2,"מרץ":3,"אפריל":4,"מאי":5,"יוני":6,
              "יולי":7,"אוגוסט":8,"ספטמבר":9,"אוקטובר":10,"נובמבר":11,"דצמבר":12}

def _slugify(s: str) -> str:
    s = re.sub(r"[^\w\s-]", "", s.lower())
    return re.sub(r"[\s_]+", "-", s.strip())[:60]

def _parse_price(text: str):
    """Returns (min, max). Returns (None, None) when price is unknown/unlisted."""
    if not text: return None, None
    if "חינ" in text or "free" in text.lower(): return 0, None
    nums = [int(n) for n in re.findall(r"\d+", text) if 5 < int(n) < 5000]
    if not nums: return None, None
    return min(nums), (max(nums) if len(set(nums)) > 1 else None)

def _derive_categories(category, subcategory):
    if category == "cultural" and subcategory == "exhibition": return ["art"]
    if category == "market" and subcategory == "food": return ["food"]
    return [category]

# ── Barby scraper ─────────────────────────────────────────────────────────────

def _scrape_barby(page, cfg) -> list[VenueEvent]:
    log.info("Barby: loading page...")
    page.goto(cfg["events_url"], timeout=30000, wait_until="domcontentloaded")
    time.sleep(6)  # wait for React hydration

    cards = page.evaluate("""() => {
        const results = [];
        document.querySelectorAll('.card-home').forEach(card => {
            const lines = (card.innerText || '').split('\\n').map(s => s.trim()).filter(Boolean);
            const imgEl = card.querySelector('img');
            results.push({
                lines,
                img: imgEl ? imgEl.src : null,
            });
        });
        return results;
    }""")

    log.info(f"Barby: found {len(cards)} cards")
    events = []

    for card in cards:
        lines = card.get("lines", [])
        if not lines: continue

        # Find the date line: "דלתות: HH:MM | DD/MM יום"
        date_line = next((l for l in lines if "דלתות" in l and "|" in l), None)
        if not date_line: continue

        # Parse date + time from "דלתות: 21:00 | 15/06 שני"
        m = re.search(r"דלתות:\s*(\d{1,2}:\d{2})\s*\|\s*(\d{1,2})/(\d{2})", date_line)
        if not m: continue
        start_time = m.group(1)
        day, month = int(m.group(2)), int(m.group(3))
        year = date.today().year
        # Handle year rollover
        if month < date.today().month - 1:
            year += 1
        try:
            ev_date = date(year, month, day)
        except ValueError:
            continue

        # Title: longest non-status line before the date line
        status_words = {"כרטיסים", "לרכישת", "בודדים", "אזלו", "מחיר", "דלתות"}
        title_candidates = []
        for l in lines:
            if l == date_line: break
            if not any(w in l for w in status_words) and len(l) > 2:
                title_candidates.append(l)
        if not title_candidates: continue
        title = title_candidates[0].strip()
        if not title: continue

        # Price (only available on Barby for the next show banner; None = unknown)
        price_line = next((l for l in lines if "מחיר" in l or "₪" in l), None)
        price_min, price_max = _parse_price(price_line or "")

        # Ticket availability
        sold_out = any("אזלו" in l for l in lines)
        ticket_url = cfg["url"] if not sold_out else None

        source_id = f"barby-{ev_date.isoformat()}-{_slugify(title)}"

        tags = ["Live Music"]
        if sold_out: tags.append("Sold Out")

        events.append(VenueEvent(
            source=f"venue_barby",
            source_id=source_id,
            title=title,
            venue_name=cfg["label"],
            neighborhood=cfg["neighborhood"],
            category=cfg["category"],
            subcategory=cfg["subcategory"],
            event_date=ev_date,
            start_time=start_time,
            end_time=None,
            image_url=card.get("img"),
            ticket_url=ticket_url,
            source_url=cfg["url"],
            price_min=price_min,
            price_max=price_max,
            tags=tags,
        ))

    log.info(f"Barby: {len(events)} events parsed")
    return events

# ── Levontin 7 scraper ────────────────────────────────────────────────────────

def _scrape_levontin7(page, cfg) -> list[VenueEvent]:
    log.info("Levontin 7: loading page...")
    page.goto(cfg["events_url"], timeout=30000, wait_until="domcontentloaded")
    time.sleep(4)

    # Get all event links with unix timestamps
    links = page.eval_on_selector_all(
        "a[href*='levontin7.com/events/'][href*='?sd=']",
        "els => els.map(e => ({href: e.href, text: e.innerText.trim()}))"
    )
    log.info(f"Levontin 7: found {len(links)} event links")

    events = []
    seen = set()

    for link in links:
        href = link.get("href", "")
        text = link.get("text", "").strip()
        if not href or not text: continue

        # Parse unix timestamp from ?sd=
        m_sd = re.search(r"[?&]sd=(\d+)", href)
        m_ed = re.search(r"[?&]ed=(\d+)", href)
        if not m_sd: continue

        sd = int(m_sd.group(1))
        ed = int(m_ed.group(1)) if m_ed else None

        dt_start = datetime.fromtimestamp(sd)
        dt_end   = datetime.fromtimestamp(ed) if ed else None

        ev_date   = dt_start.date()
        start_time = dt_start.strftime("%H:%M")
        end_time   = dt_end.strftime("%H:%M") if dt_end else None

        # Title: strip trailing time from link text e.g. " 20:00"
        title = re.sub(r"\s+\d{1,2}:\d{2}$", "", text).strip()
        if not title: continue

        # Slug from URL
        slug_m = re.search(r"/events/([^/?]+)", href)
        slug = slug_m.group(1) if slug_m else _slugify(title)
        # Use sd timestamp to distinguish same show on different dates
        source_id = f"{slug}-{sd}"
        if source_id in seen: continue
        seen.add(source_id)

        events.append(VenueEvent(
            source="venue_levontin7",
            source_id=source_id,
            title=title,
            venue_name=cfg["label"],
            neighborhood=cfg["neighborhood"],
            category=cfg["category"],
            subcategory=cfg["subcategory"],
            event_date=ev_date,
            start_time=start_time,
            end_time=end_time,
            image_url=None,
            ticket_url=href.split("?")[0],  # clean URL without timestamps
            source_url=href,
            price_min=0,
            tags=["Live Music"],
        ))

    log.info(f"Levontin 7: {len(events)} events parsed")
    return events

# ── Hangar 11 scraper (static HTML) ──────────────────────────────────────────

def _scrape_hangar11(cfg) -> list[VenueEvent]:
    import requests
    from bs4 import BeautifulSoup

    log.info("Hangar 11: fetching...")
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"}
    try:
        r = requests.get(cfg["events_url"], headers=headers, timeout=20)
        r.raise_for_status()
    except Exception as e:
        log.warning(f"Hangar 11 fetch failed: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    events = []

    # Tribe Events Calendar HTML pattern: .tribe-event-url or article.type-tribe_events
    for article in soup.select("article.type-tribe_events, .tribe_events_cat"):
        title_el = article.select_one(".tribe-events-list-event-title a, h2 a, h3 a")
        if not title_el: continue
        title = title_el.get_text(strip=True)
        url   = title_el.get("href", "")

        # Date
        date_el = article.select_one("abbr.tribe-events-abbr, time, .tribe-event-date-start")
        ev_date = None
        start_time = None
        if date_el:
            dt_str = date_el.get("title") or date_el.get("datetime") or date_el.get_text(strip=True)
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%B %d, %Y"):
                try:
                    ev_date = datetime.strptime(dt_str[:10], fmt[:len(dt_str)]).date()
                    break
                except: pass

        img_el = article.select_one("img")
        img_url = img_el.get("src") if img_el else None

        if not title or not ev_date: continue
        source_id = f"hangar11-{ev_date.isoformat()}-{_slugify(title)}"

        events.append(VenueEvent(
            source="venue_hangar11",
            source_id=source_id,
            title=title,
            venue_name=cfg["label"],
            neighborhood=cfg["neighborhood"],
            category=cfg["category"],
            subcategory=cfg["subcategory"],
            event_date=ev_date,
            start_time=start_time,
            end_time=None,
            image_url=img_url,
            ticket_url=url or cfg["url"],
            source_url=url or cfg["url"],
            tags=["Live Music"],
        ))

    log.info(f"Hangar 11: {len(events)} events parsed")
    return events

# ── Playwright runner ────────────────────────────────────────────────────────

def _scrape_hameretz2(page, cfg) -> list[VenueEvent]:
    log.info("Hameretz 2: loading page...")
    page.goto(cfg["events_url"], timeout=25000, wait_until="domcontentloaded")
    time.sleep(3)

    # DOM structure: [link][img?][date text DD.MM][title][description…][next link]
    # Walk the DOM in document order to collect (link, img, text_after) tuples.
    dom_items = page.evaluate("""() => {
        const out = [];
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT
        );
        let node;
        while (node = walker.nextNode()) {
            if (node.nodeType === 3) {
                const t = node.textContent.trim();
                if (t && t.length < 500 && !t.startsWith('//') && !t.includes('{')) {
                    out.push({type:'text', val:t});
                }
            } else if (node.nodeType === 1) {
                if (node.tagName === 'A' && (node.href||'').includes('tickets.hameretz2.org/event/'))
                    out.push({type:'link', href:node.href});
                else if (node.tagName === 'IMG' && node.src && node.src.includes('http'))
                    out.push({type:'img', src:node.src});
            }
        }
        return out;
    }""")

    # Group: each link starts a new event; collect text until the next link
    raw_groups = []
    current = None
    for item in dom_items:
        if item['type'] == 'link':
            if current: raw_groups.append(current)
            current = {'href': item['href'], 'texts': [], 'img': None}
        elif current is not None:
            if item['type'] == 'img' and not current['img']:
                current['img'] = item['src']
            elif item['type'] == 'text':
                current['texts'].append(item['val'])
    if current: raw_groups.append(current)

    items = [{'href': g['href'], 'lines': g['texts'][:8], 'img': g['img']}
             for g in raw_groups if g['texts']]

    log.info(f"Hameretz 2: found {len(items)} items")
    events = []
    seen = set()

    FILM_KEYWORDS = re.compile(
        r"סרט|קולנוע|film|screening|cinema|movie|🎬|🎞|director|הקרנה", re.I)
    STANDUP_KEYWORDS = re.compile(
        r"stand.?up|קומדי|ערסים|comedy|comedian|סטנד", re.I)
    CLASSICAL_KEYWORDS = re.compile(
        r"quartet|orchestra|symphon|classical|philharmon|רביעייה|תזמורת", re.I)

    def _fetch_ticket_details(ticket_page, href):
        """Fetch individual ticket page for start time, doors time, and price."""
        try:
            ticket_page.goto(href, timeout=12000, wait_until="domcontentloaded")
            time.sleep(1.5)
            txt = ticket_page.inner_text("body")
            lines = [l.strip() for l in txt.split('\n') if l.strip()]

            start_time, price_min, price_max = None, 0, None

            # Parse time: look for "לייב ב-HH:MM" or standalone HH:MM after "התחלה"
            show_m = re.search(r"לייב\s+ב.?(\d{1,2}:\d{2})", txt)
            if not show_m:
                # fallback: find "התחלה" then next HH:MM
                for i, l in enumerate(lines):
                    if "התחלה" in l:
                        for l2 in lines[i:i+3]:
                            m = re.search(r"\b(\d{1,2}:\d{2})\b", l2)
                            if m: show_m = m; break
                        break
            if show_m:
                t = show_m.group(1) if hasattr(show_m, 'group') else show_m
                h, mi = map(int, t.split(':'))
                start_time = f"{h:02d}:{mi:02d}"

            # Parse price: look for NN.00₪ or ₪NN patterns
            prices = [int(float(m)) for m in re.findall(r"(\d+)(?:\.\d+)?₪", txt) if 10 < int(float(m)) < 1000]
            if prices:
                price_min, price_max = min(prices), (max(prices) if len(prices) > 1 and max(prices) != min(prices) else None)

            return start_time, price_min, price_max
        except Exception as e:
            log.debug(f"  ticket page error {href}: {e}")
            return None, 0, None

    # Open a second tab for ticket detail pages
    ticket_page = page.context.new_page()

    for item in items:
        href = item.get("href", "")
        lines = item.get("lines", [])
        if not lines: continue

        # Extract ticket ID as source_id
        m_id = re.search(r"/event/(\d+)", href)
        source_id = m_id.group(1) if m_id else _slugify(lines[0] if lines else "")
        if source_id in seen: continue
        seen.add(source_id)

        # Date: look for DD.MM pattern
        ev_date, title, description = None, "", ""
        for i, line in enumerate(lines):
            m_date = re.search(r"(\d{1,2})\.(\d{2})", line)
            if m_date and not ev_date:
                day, month = int(m_date.group(1)), int(m_date.group(2))
                year = date.today().year
                if month < date.today().month - 1:
                    year += 1
                try:
                    ev_date = date(year, month, day)
                    for j in range(i + 1, min(i + 4, len(lines))):
                        if lines[j] and not re.search(r"^\d{1,2}\.\d{2}", lines[j]):
                            title = lines[j]
                            desc_parts = [l for l in lines[j+1:j+3] if l and len(l) > 5]
                            description = " ".join(desc_parts)[:300]
                            break
                except ValueError:
                    pass

        if not ev_date or not title: continue

        # Fetch ticket page for time + price
        start_time, price_min, price_max = _fetch_ticket_details(ticket_page, href)

        # Category inference from title + description
        combined = f"{title} {description}"
        if FILM_KEYWORDS.search(combined):
            category, subcategory = "cultural", "film"
        elif STANDUP_KEYWORDS.search(combined):
            category, subcategory = "standup", "standup"
        elif CLASSICAL_KEYWORDS.search(combined):
            category, subcategory = "music", "classical"
        else:
            category, subcategory = "music", "live"

        categories = _derive_categories(category, subcategory)

        events.append(VenueEvent(
            source="venue_hameretz2",
            source_id=source_id,
            title=title,
            venue_name=cfg["label"],
            neighborhood=cfg["neighborhood"],
            category=category,
            subcategory=subcategory,
            event_date=ev_date,
            start_time=start_time,
            end_time=None,
            image_url=item.get("img"),
            ticket_url=href,
            source_url=href,
            description=description,
            price_min=price_min,
            price_max=price_max,
            tags=[subcategory.title()] if subcategory not in ("general", "live") else ["Live Music"],
        ))

    ticket_page.close()
    log.info(f"Hameretz 2: {len(events)} events parsed")
    return events


# ── Playwright runner ────────────────────────────────────────────────────────

def _scrape_beit_radical(page, cfg) -> list[VenueEvent]:
    log.info("Beit Radical: loading events listing...")
    page.goto(cfg["events_url"], timeout=20000, wait_until="domcontentloaded")
    time.sleep(2)

    # Collect all unique event slugs
    links = page.eval_on_selector_all(
        "a[href*='/events/']",
        "els => [...new Set(els.map(e => e.href))].filter(h => h.split('/').filter(Boolean).length >= 4)"
    )
    log.info(f"Beit Radical: {len(links)} event links found")

    FILM_KW     = re.compile(r"סרט|הקרנה|film|cinema|🎬", re.I)
    STANDUP_KW  = re.compile(r"סטנד.?אפ|stand.?up|comedy|קומדי", re.I)
    CLASSICAL_KW= re.compile(r"קלאסי|orchestra|symphon|quartet", re.I)
    MUSIC_KW    = re.compile(r"מופע|הופעה|להקה|לייב|concert|live", re.I)

    events = []
    seen = set()
    detail_page = page.context.new_page()

    for href in links:
        slug = href.rstrip("/").rsplit("/", 1)[-1]
        if slug in seen or slug in ("events",): continue
        seen.add(slug)

        try:
            detail_page.goto(href, timeout=15000, wait_until="domcontentloaded")
            time.sleep(1)
            txt = detail_page.inner_text("body")
            lines = [l.strip() for l in txt.split('\n') if l.strip()]
            title = detail_page.title().replace(" - רדיקל","").replace(" | Radical","").strip()
            if not title: continue

            # Date: "ראשון, 14/06/2026" or "שני | 15.06 | 19:00"
            ev_date, start_time, end_time = None, None, None
            for l in lines:
                m = re.search(r"(\d{1,2})[./](\d{2})[./](\d{4})", l)
                if m:
                    d, mo, yr = int(m.group(1)), int(m.group(2)), int(m.group(3))
                    try: ev_date = date(yr, mo, d)
                    except ValueError: pass
                elif not ev_date:
                    m2 = re.search(r"(\d{1,2})\.(\d{2})\b", l)
                    if m2:
                        d, mo = int(m2.group(1)), int(m2.group(2))
                        yr = date.today().year
                        if mo < date.today().month - 1: yr += 1
                        try: ev_date = date(yr, mo, d)
                        except ValueError: pass
                if ev_date: break

            # Time: "התחלה: 20:00" or "| 19:00"
            for l in lines:
                m = re.search(r"(?:התחלה|לייב|Begin)[:\s]*(\d{1,2}:\d{2})", l)
                if m: start_time = m.group(1); break
                m2 = re.search(r"\|\s*(\d{1,2}:\d{2})\b", l)
                if m2: start_time = m2.group(1); break

            # Price
            price_min, price_max = None, None
            for l in lines:
                if "מחיר" in l or "₪" in l:
                    pm, px = _parse_price(l)
                    if pm is not None:
                        price_min, price_max = pm, px
                        break

            if not ev_date: continue

            # Category inference
            combined = f"{title} {' '.join(lines[:20])}"
            if STANDUP_KW.search(combined):
                category, subcategory = "standup", "standup"
            elif FILM_KW.search(combined):
                category, subcategory = "cultural", "film"
            elif CLASSICAL_KW.search(combined):
                category, subcategory = "music", "classical"
            elif MUSIC_KW.search(combined):
                category, subcategory = "music", "live"
            else:
                category, subcategory = "cultural", "talk"

            # Description: longest paragraph-like line
            desc = next((l for l in lines if len(l) > 80), "")[:400]

            events.append(VenueEvent(
                source="venue_beit_radical",
                source_id=slug,
                title=title,
                venue_name=cfg["label"],
                neighborhood=cfg["neighborhood"],
                category=category,
                subcategory=subcategory,
                event_date=ev_date,
                start_time=start_time,
                end_time=end_time,
                image_url=None,
                ticket_url=href,
                source_url=href,
                description=desc,
                price_min=price_min,
                price_max=price_max,
                tags=[],
            ))
            time.sleep(0.5)
        except Exception as e:
            log.debug(f"Beit Radical {href}: {e}")

    detail_page.close()
    log.info(f"Beit Radical: {len(events)} events parsed")
    return events


PW_SCRAPERS = {
    "barby":        _scrape_barby,
    "levontin7":    _scrape_levontin7,
    "hameretz2":    _scrape_hameretz2,
    "beit_radical": _scrape_beit_radical,
}

def scrape_playwright_venues(venue_ids) -> list[VenueEvent]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log.error("playwright not installed: pip install playwright && playwright install chromium")
        return []

    all_events = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ])
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            locale="he-IL",
        )
        for vid in venue_ids:
            if vid not in PW_SCRAPERS: continue
            cfg = VENUES[vid]
            page = ctx.new_page()
            try:
                events = PW_SCRAPERS[vid](page, cfg)
                all_events.extend(events)
            except Exception as e:
                log.error(f"{vid}: scrape error: {e}")
            finally:
                page.close()
        browser.close()
    return all_events

# ── DB upsert ────────────────────────────────────────────────────────────────

def upsert_venue_events(events: list[VenueEvent], conn):
    rows = [(
        e.source, e.source_id, e.title, e.description,
        e.category, e.subcategory,
        e.venue_name, e.neighborhood,
        str(e.event_date), e.start_time, e.end_time,
        e.price_min, e.price_max,
        e.image_url, e.ticket_url, e.source_url,
        e.tags,
        _derive_categories(e.category, e.subcategory),
    ) for e in events]

    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO events (
                source, source_id, title, description,
                category, subcategory,
                venue_name, neighborhood,
                event_date, start_time, end_time,
                price_min, price_max,
                image_url, ticket_url, source_url,
                tags, categories
            ) VALUES %s
            ON CONFLICT (source, source_id) DO UPDATE SET
                title        = EXCLUDED.title,
                venue_name   = EXCLUDED.venue_name,
                event_date   = EXCLUDED.event_date,
                start_time   = EXCLUDED.start_time,
                end_time     = EXCLUDED.end_time,
                price_min    = EXCLUDED.price_min,
                price_max    = EXCLUDED.price_max,
                image_url    = EXCLUDED.image_url,
                ticket_url   = EXCLUDED.ticket_url,
                tags         = EXCLUDED.tags,
                categories   = EXCLUDED.categories,
                updated_at   = NOW()
        """, rows)
    conn.commit()

# ── Main ─────────────────────────────────────────────────────────────────────

def scrape_all_venues(venue_filter=None) -> list[VenueEvent]:
    targets = [v for v in VENUES if venue_filter is None or v == venue_filter]
    all_events = []

    # Playwright venues
    pw_targets = [v for v in targets if VENUES[v]["strategy"] == "playwright"]
    if pw_targets:
        all_events.extend(scrape_playwright_venues(pw_targets))

    # HTML venues
    for vid in targets:
        if VENUES[vid]["strategy"] != "html": continue
        if vid == "hangar11":
            all_events.extend(_scrape_hangar11(VENUES[vid]))

    return all_events


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--venue", choices=list(VENUES.keys()), default=None)
    parser.add_argument("--since", default="2026-06-12")
    args = parser.parse_args()

    since = date.fromisoformat(args.since)
    events = scrape_all_venues(venue_filter=args.venue)
    events = [e for e in events if e.event_date and e.event_date >= since]
    events.sort(key=lambda e: (e.event_date, e.start_time or ""))

    log.info(f"Total venue events: {len(events)}")
    for e in events:
        log.info(f"  {e.source:15} {e.event_date} {e.start_time or '?':5} | {e.title[:50]}")

    if args.dry_run:
        log.info("Dry run — not writing to DB")
        return

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        sys.exit("DATABASE_URL not set")

    conn = psycopg2.connect(db_url)
    upsert_venue_events(events, conn)
    conn.close()
    log.info(f"Done — {len(events)} venue events upserted")


if __name__ == "__main__":
    main()

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
from datetime import date, datetime, timezone, timedelta

# Israel Daylight Time (UTC+3, Jun–Oct). Standard time is UTC+2.
_IDT = timezone(timedelta(hours=3))
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
    "ozen": {
        "label":        "Ozen Bar",
        "url":          "https://ozentelaviv.com",
        "events_url":   "https://ozentelaviv.com/",
        "neighborhood": "City Center",
        "category":     "music",
        "subcategory":  "live",
        "strategy":     "html",
    },
    "teder": {
        "label":        "Teder.fm",
        "url":          "https://www.teder.fm",
        "events_url":   "https://www.teder.fm/",
        "neighborhood": "Tel Aviv Port",
        "category":     "music",
        "subcategory":  "live",
        "strategy":     "html",
    },
    "tmuna": {
        "label":        "Tmuna Theater",
        "url":          "https://tmuna.co.il",
        "events_url":   "https://tmuna.co.il/",
        "neighborhood": "Jaffa",
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
            const linkEl = card.closest('a') || card.querySelector('a');
            results.push({
                lines,
                img: imgEl ? imgEl.src : null,
                href: linkEl ? linkEl.href : null,
            });
        });
        return results;
    }""")

    log.info(f"Barby: found {len(cards)} cards")
    events = []
    detail_page = page.context.new_page()

    def _fetch_barby_price(show_url):
        """Fetch price from a barby.co.il/show/NNNN page."""
        if not show_url or "/show/" not in show_url:
            return None, None
        try:
            detail_page.goto(show_url, timeout=12000, wait_until="domcontentloaded")
            time.sleep(1.5)
            txt = detail_page.inner_text("body")
            # Look for "NNN ₪" or "₪NNN" or "NNN ILS" patterns
            prices = []
            for m in re.findall(r"(\d{2,4})\s*[₪]", txt):
                n = int(m)
                if 10 <= n <= 2000: prices.append(n)
            for m in re.findall(r"[₪]\s*(\d{2,4})", txt):
                n = int(m)
                if 10 <= n <= 2000: prices.append(n)
            for m in re.findall(r"(\d{2,4})\s*ILS", txt, re.I):
                n = int(m)
                if 10 <= n <= 2000: prices.append(n)
            if not prices:
                return None, None
            prices = sorted(set(prices))
            return prices[0], (prices[-1] if len(prices) > 1 else None)
        except Exception as e:
            log.debug(f"Barby price fetch error {show_url}: {e}")
            return None, None

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

        # Ticket availability
        sold_out = any("אזלו" in l for l in lines)
        show_url = card.get("href") or cfg["url"]
        ticket_url = show_url if not sold_out else None

        # Fetch price from detail page; fallback to card text
        price_min, price_max = _fetch_barby_price(show_url)
        if price_min is None:
            price_line = next((l for l in lines if "מחיר" in l or "₪" in l), None)
            price_min, price_max = _parse_price(price_line or "")

        source_id = f"barby-{ev_date.isoformat()}-{_slugify(title)}"

        tags = ["Live Music"]
        if sold_out: tags.append("Sold Out")

        events.append(VenueEvent(
            source="venue_barby",
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
            source_url=show_url,
            price_min=price_min,
            price_max=price_max,
            tags=tags,
        ))

    detail_page.close()
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
    # Cache price by slug to avoid fetching the same slug twice (same show, different dates)
    slug_price_cache = {}
    detail_page = page.context.new_page()

    def _fetch_levontin_price(slug_url):
        """Visit a Levontin event page and extract ticket prices. Returns (min, max)."""
        if slug_url in slug_price_cache:
            return slug_price_cache[slug_url]
        try:
            detail_page.goto(slug_url, timeout=12000, wait_until="domcontentloaded")
            time.sleep(2.5)  # ticket widget needs time to render
            prices = detail_page.evaluate("""() => {
                // 1. Try .fat-event-fees / .fat-event-total-fees widget elements
                const feeEls = document.querySelectorAll('.fat-event-fees, .fat-event-total-fees, .fat-ticket-price, .fat-price');
                for (const el of feeEls) {
                    const txt = (el.innerText || '') + ' ' + (el.nextSibling?.textContent || '') + ' ' + (el.parentElement?.innerText || '');
                    const nums = [...txt.matchAll(/\\b(\\d{2,3})\\b/g)]
                        .map(m => parseInt(m[1], 10))
                        .filter(n => n >= 10 && n <= 500);
                    if (nums.length) return nums;
                }

                // 2. Look for ₪-adjacent numbers anywhere on page (most reliable)
                const shekelMatches = [];
                const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
                let node;
                while (node = walker.nextNode()) {
                    const t = node.textContent;
                    // Match "50₪", "₪50", "50 ₪", "מחיר: 50"
                    const m1 = t.match(/(\\d{2,3})\\s*[₪]/g);
                    const m2 = t.match(/[₪]\\s*(\\d{2,3})/g);
                    for (const m of [...(m1||[]), ...(m2||[])]) {
                        const n = parseInt(m.replace(/[^0-9]/g,''), 10);
                        if (n >= 10 && n <= 500) shekelMatches.push(n);
                    }
                    // Match price keyword context
                    if (/מחיר|כרטיס|כניסה|entrance|price/i.test(t)) {
                        const nums = [...t.matchAll(/\\b(\\d{2,3})\\b/g)]
                            .map(m => parseInt(m[1], 10))
                            .filter(n => n >= 10 && n <= 500);
                        shekelMatches.push(...nums);
                    }
                }
                if (shekelMatches.length) return [...new Set(shekelMatches)];

                return null;
            }""")
            result = (None, None)
            if prices and len(prices) > 0:
                unique = sorted(set(prices))
                result = (unique[0], unique[-1] if len(unique) > 1 else None)
            slug_price_cache[slug_url] = result
            return result
        except Exception as e:
            log.debug(f"Levontin price fetch error {slug_url}: {e}")
            slug_price_cache[slug_url] = (None, None)
            return (None, None)

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

        # Use Israel timezone explicitly so dates are correct regardless of server TZ
        dt_start = datetime.fromtimestamp(sd, tz=_IDT)
        dt_end   = datetime.fromtimestamp(ed, tz=_IDT) if ed else None

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

        # Fetch price from the detail page (cached per slug)
        slug_url = href.split("?")[0]
        price_min, price_max = _fetch_levontin_price(slug_url)

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
            ticket_url=slug_url,
            source_url=href,
            price_min=price_min,
            price_max=price_max,
            tags=["Live Music"],
        ))

    detail_page.close()
    log.info(f"Levontin 7: {len(events)} events parsed (price cache: {len(slug_price_cache)} slugs)")
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


# ── Ozen Bar scraper (static HTML) ──────────────────────────────────────────

_OZEN_CAT = {
    "הופעות":  ("music",    "live"),
    "סטנד-אפ": ("standup",  "standup"),
    "מסיבות":  ("music",    "dj-set"),
    "קולנוע":  ("cultural", "film"),
    "הרצאות":  ("cultural", "talk"),
    "תיאטרון": ("cultural", "theater"),
    "ג'אז":    ("music",    "jazz"),
}

def _scrape_ozen(cfg) -> list[VenueEvent]:
    import requests
    from bs4 import BeautifulSoup
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"}
    log.info("Ozen Bar: fetching listing...")
    try:
        r = requests.get(cfg["events_url"], headers=headers, timeout=20)
        r.raise_for_status()
    except Exception as e:
        log.warning(f"Ozen Bar fetch failed: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    items = soup.select(".event-item")
    log.info(f"Ozen Bar: {len(items)} event items found")
    events, seen = [], set()

    for item in items:
        a_el = item.find("a", href=True)
        href = a_el["href"] if a_el else cfg["url"]
        title_el = item.select_one("h3, h2, strong")
        if not title_el: continue
        title = title_el.get_text(strip=True)
        if not title: continue

        # Category
        cat_el = item.select_one(".categories, [class*='cat'], [class*='genre'], [class*='type']")
        cat_txt = cat_el.get_text(strip=True) if cat_el else ""
        category, subcategory = _OZEN_CAT.get(cat_txt, ("music", "live"))

        # Date: first td is "DD-MM-YYYY"
        tds = item.select("td")
        ev_date, start_time = None, None
        if tds:
            m_date = re.search(r"(\d{1,2})-(\d{2})-(\d{4})", tds[0].get_text())
            if m_date:
                try:
                    ev_date = date(int(m_date.group(3)), int(m_date.group(2)), int(m_date.group(1)))
                except ValueError:
                    pass
        if len(tds) > 1:
            m_time = re.search(r"(\d{1,2}:\d{2})", tds[1].get_text())
            if m_time: start_time = m_time.group(1)

        if not ev_date: continue
        if ev_date < date.today(): continue

        # Image from grid card (same events, parallel list)
        img_el = item.select_one("img")
        image_url = img_el.get("src") if img_el else None

        # Fetch detail page for price + ticket link
        price_min, price_max, ticket_url = None, None, href
        try:
            r2 = requests.get(href, headers=headers, timeout=12)
            soup2 = BeautifulSoup(r2.text, "html.parser")
            txt2 = soup2.get_text("\n")
            # Price: "מחיר: NN" or "NN ₪"
            prices = []
            for m in re.findall(r"מחיר[:\s]+(\d+)", txt2):
                n = int(m)
                if 10 <= n <= 1000: prices.append(n)
            for m in re.findall(r"(\d+)\s*[₪]", txt2):
                n = int(m)
                if 10 <= n <= 1000: prices.append(n)
            if prices:
                prices = sorted(set(prices))
                price_min, price_max = prices[0], (prices[-1] if len(prices) > 1 else None)
            # Ticket link (go-out.co or other)
            for a2 in soup2.find_all("a", href=True):
                if any(d in a2["href"] for d in ["go-out.co", "entrio", "eventbrite", "ticketmaster"]):
                    ticket_url = a2["href"]
                    break
        except Exception as e:
            log.debug(f"Ozen detail fetch error {href}: {e}")

        source_id = f"ozen-{ev_date.isoformat()}-{_slugify(title)}"
        if source_id in seen: continue
        seen.add(source_id)

        events.append(VenueEvent(
            source="venue_ozen",
            source_id=source_id,
            title=title,
            venue_name=cfg["label"],
            neighborhood=cfg["neighborhood"],
            category=category,
            subcategory=subcategory,
            event_date=ev_date,
            start_time=start_time,
            end_time=None,
            image_url=image_url,
            ticket_url=ticket_url,
            source_url=href,
            price_min=price_min,
            price_max=price_max,
            tags=[],
        ))
        time.sleep(0.5)

    log.info(f"Ozen Bar: {len(events)} events parsed")
    return events


# ── Teder.fm scraper (static HTML) ────────────────────────────────────────────

def _scrape_teder(cfg) -> list[VenueEvent]:
    import requests
    from bs4 import BeautifulSoup
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"}
    log.info("Teder.fm: fetching listing...")
    try:
        r = requests.get(cfg["events_url"], headers=headers, timeout=20)
        r.raise_for_status()
    except Exception as e:
        log.warning(f"Teder.fm fetch failed: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    # Find all /events/NNNN links and their enclosing blocks
    event_links = {}
    for a in soup.find_all("a", href=re.compile(r"/events/\d+")):
        eid = re.search(r"/events/(\d+)", a["href"]).group(1)
        if eid not in event_links:
            event_links[eid] = {"href": a["href"], "text": a.get_text(separator="|")}

    log.info(f"Teder.fm: {len(event_links)} event links found")
    events, today = [], date.today()

    for eid, info in event_links.items():
        # Fetch detail page (same data, cleaner format)
        try:
            r2 = requests.get(f"https://www.teder.fm/events/{eid}", headers=headers, timeout=12)
            soup2 = BeautifulSoup(r2.text, "html.parser")
            lines = [l.strip() for l in soup2.get_text("\n").splitlines() if l.strip()]
        except Exception as e:
            log.debug(f"Teder detail {eid} error: {e}")
            continue

        # Title: first heading or large text before date
        title = soup2.title.string.split("|")[0].strip() if soup2.title else ""
        title = re.sub(r"^\d+\.\d+\s*[•·]\s*!?", "", title).strip()  # strip "12.6 • "
        if not title: continue

        # Date: "DD.MM.YY" or "DD.MM.YYYY" in text lines
        ev_date, start_time, description = None, None, ""
        for line in lines:
            if not ev_date:
                m = re.search(r"(\d{1,2})\.(\d{2})\.(\d{2,4})", line)
                if m:
                    day, mon = int(m.group(1)), int(m.group(2))
                    yr_raw = m.group(3)
                    yr = int(yr_raw) if len(yr_raw) == 4 else 2000 + int(yr_raw)
                    try: ev_date = date(yr, mon, day)
                    except ValueError: pass
            if not start_time:
                m = re.search(r"^(\d{1,2}:\d{2})$", line)
                if m: start_time = m.group(1)
            if len(line) > 80 and not description:
                description = line[:400]

        if not ev_date or ev_date < today: continue

        source_id = f"teder-{eid}"
        events.append(VenueEvent(
            source="venue_teder",
            source_id=source_id,
            title=title,
            venue_name=cfg["label"],
            neighborhood=cfg["neighborhood"],
            category="music",
            subcategory="live",
            event_date=ev_date,
            start_time=start_time,
            end_time=None,
            image_url=None,
            ticket_url=f"https://www.teder.fm/events/{eid}",
            source_url=f"https://www.teder.fm/events/{eid}",
            description=description,
            tags=["Live Music"],
        ))
        time.sleep(0.4)

    log.info(f"Teder.fm: {len(events)} events parsed")
    return events


# ── Tmuna Theater scraper (Playwright, expired SSL) ──────────────────────────

def _scrape_tmuna(page, cfg) -> list[VenueEvent]:
    log.info("Tmuna: loading page...")
    try:
        page.goto(cfg["events_url"], timeout=25000, wait_until="domcontentloaded")
        time.sleep(2)
    except Exception as e:
        log.warning(f"Tmuna load error: {e}")
        return []

    # Extract all event-like links: look for patterns with dates
    links = page.eval_on_selector_all(
        "a[href]",
        "els => els.map(e => ({href: e.href, text: (e.innerText||'').trim()})).filter(x => x.text.length > 3 && x.href.includes('tmuna'))"
    )
    log.info(f"Tmuna: {len(links)} links found")

    # Identify event links by checking for date patterns in text or href
    event_links = []
    for lnk in links:
        href = lnk.get("href", "")
        text = lnk.get("text", "")
        # Look for event/show/performance URL patterns
        if re.search(r"/event|/show|/perf|\d{4}/\d{2}|/\d{5,}", href, re.I):
            event_links.append(lnk)

    log.info(f"Tmuna: {len(event_links)} event links after filter")
    events, seen, today = [], set(), date.today()
    detail_page = page.context.new_page()

    for lnk in event_links[:40]:  # cap at 40 to avoid excessive scraping
        href = lnk["href"]
        if href in seen: continue
        seen.add(href)
        try:
            detail_page.goto(href, timeout=15000, wait_until="domcontentloaded")
            time.sleep(1)
            txt = detail_page.inner_text("body")
            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            title = detail_page.title().split("|")[0].split("-")[0].strip()
            if not title or len(title) < 3: continue

            ev_date, start_time = None, None
            for line in lines:
                if not ev_date:
                    # DD.MM.YYYY or DD/MM/YYYY or written Hebrew date
                    m = re.search(r"(\d{1,2})[./](\d{2})[./](\d{4})", line)
                    if m:
                        try: ev_date = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
                        except ValueError: pass
                if not start_time:
                    m = re.search(r"\b(\d{1,2}:\d{2})\b", line)
                    if m: start_time = m.group(1)

            if not ev_date or ev_date < today: continue

            prices = [int(m) for m in re.findall(r"(\d{2,3})\s*[₪]", txt) if 10 <= int(m) <= 500]
            prices += [int(m) for m in re.findall(r"[₪]\s*(\d{2,3})", txt) if 10 <= int(m) <= 500]
            prices += [int(m) for m in re.findall(r"מחיר[:\s]+(\d+)", txt) if 10 <= int(m) <= 500]
            prices = sorted(set(prices))
            price_min = prices[0] if prices else None
            price_max = prices[-1] if len(prices) > 1 else None

            img_el = detail_page.query_selector("img[src*='tmuna'], .event-image img, article img, .wp-post-image")
            img_url = img_el.get_attribute("src") if img_el else None

            source_id = f"tmuna-{ev_date.isoformat()}-{_slugify(title)}"
            events.append(VenueEvent(
                source="venue_tmuna",
                source_id=source_id,
                title=title,
                venue_name=cfg["label"],
                neighborhood=cfg["neighborhood"],
                category="cultural",
                subcategory="theater",
                event_date=ev_date,
                start_time=start_time,
                end_time=None,
                image_url=img_url,
                ticket_url=href,
                source_url=href,
                price_min=price_min,
                price_max=price_max,
                tags=["Theater"],
            ))
            time.sleep(0.5)
        except Exception as e:
            log.debug(f"Tmuna {href}: {e}")

    detail_page.close()
    log.info(f"Tmuna: {len(events)} events parsed")
    return events


PW_SCRAPERS = {
    "barby":        _scrape_barby,
    "levontin7":    _scrape_levontin7,
    "hameretz2":    _scrape_hameretz2,
    "beit_radical": _scrape_beit_radical,
    "tmuna":        _scrape_tmuna,
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
            ignore_https_errors=True,  # needed for Tmuna (expired cert)
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
    _HTML_SCRAPERS = {
        "hangar11": _scrape_hangar11,
        "ozen":     _scrape_ozen,
        "teder":    _scrape_teder,
    }
    for vid in targets:
        if VENUES[vid]["strategy"] != "html": continue
        if vid in _HTML_SCRAPERS:
            all_events.extend(_HTML_SCRAPERS[vid](VENUES[vid]))

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

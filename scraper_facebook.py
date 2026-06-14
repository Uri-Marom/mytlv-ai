"""
mytlv.ai — Facebook Graph API scraper
Fetches events from a curated list of Tel Aviv venue/promoter Facebook Pages.

No user login needed — uses App Access Token (FB_APP_ID|FB_APP_SECRET).

Setup (one-time):
  1. Go to developers.facebook.com → Create App → Other → Consumer
  2. Copy App ID and App Secret from Settings → Basic
  3. Add to .env.local:  FB_APP_ID=...  FB_APP_SECRET=...

Usage:
  python scraper_facebook.py              # scrape all pages, print events
  python scraper_facebook.py --page kulialma   # single page dry-run
"""
import os, re, time, logging
from datetime import date, datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Optional

import requests

log = logging.getLogger(__name__)

GRAPH = "https://graph.facebook.com/v19.0"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; myTLV-bot/1.0)",
}

# ── Page registry ─────────────────────────────────────────────────────────────
# key: Facebook page slug or numeric ID
# value: (venue_name, neighborhood, default_category, default_subcategory)
# Category/subcategory are defaults; may be overridden by event description heuristics.

FB_PAGES = {
    # ── Clubs / Nightlife ────────────────────────────────────────────────────
    "kulialma":             ("Kuli Alma",         "Florentin",      "music",    "dj-set"),
    "theblocktelaviv":      ("The Block",          "Jaffa Port",     "music",    "dj-set"),
    "haoman17official":     ("Haoman 17",          "Tel Aviv",       "music",    "dj-set"),
    "duplex.tlv":           ("Duplex",             "City Center",    "music",    "dj-set"),
    "shalvatabeach":        ("Shalvata",           "Tel Aviv Port",  "music",    "dj-set"),
    "haezorclub":           ("HaEzor",             "Tel Aviv Port",  "music",    "dj-set"),
    "gagarintlv":           ("Gagarin Club",       "Florentin",      "music",    "dj-set"),
    "minusone.tlv":         ("Minus One",          "City Center",    "music",    "dj-set"),
    # ── Live music ───────────────────────────────────────────────────────────
    "barby.club":           ("Barby",              "Jaffa Port",     "music",    "live"),
    "levontin7":            ("Levontin 7",         "Florentin",      "music",    "live"),
    "hanangar11":           ("Hangar 11",          "Tel Aviv Port",  "music",    "live"),
    "ozentelaviv":          ("Ozen Bar",           "City Center",    "music",    "live"),
    "zappa.israel":         ("Zappa",              "Ramat HaHayal",  "music",    "live"),
    # ── Promoters / Collectives ──────────────────────────────────────────────
    "alphabettelaviv":      ("Alphabet",           "Tel Aviv",       "music",    "dj-set"),
    "mazkekatlv":           ("Mazkeka",            "Tel Aviv",       "music",    "dj-set"),
    "thetederstation":      ("Teder",              "Tel Aviv Port",  "music",    "live"),
    # ── Cultural ─────────────────────────────────────────────────────────────
    "tmunatheatre":         ("Tmuna Theater",      "Jaffa",          "cultural", "theater"),
    "beitradical":          ("Beit Radical",       "Herzl Hill",     "cultural", "talk"),
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _app_token():
    app_id     = os.environ.get("FB_APP_ID", "")
    app_secret = os.environ.get("FB_APP_SECRET", "")
    if not app_id or not app_secret:
        raise RuntimeError("FB_APP_ID and FB_APP_SECRET must be set in environment")
    return f"{app_id}|{app_secret}"

def _get(url, params=None, retries=3):
    for i in range(retries):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=15)
            if r.status_code == 429:
                log.warning("Rate limited — sleeping 30s")
                time.sleep(30)
                continue
            r.raise_for_status()
            time.sleep(0.5)
            return r
        except Exception as e:
            log.warning(f"  attempt {i+1}: {e}")
            time.sleep(2 * (i + 1))
    return None

def _parse_iso(s):
    if not s: return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s[:19], fmt[:len(s[:19])])
            return dt.replace(tzinfo=None)  # strip tz — we store Israel-local
        except: pass
    return None

# Price extraction (same logic as scraper_sta.py)
def _extract_prices(text):
    if not text: return None, None
    if re.search(r"חינ|free|חופשי", text, re.I): return 0, None
    prices = []
    for m in re.findall(r"(\d+)\s*[₪]", text):
        n = int(m)
        if 10 <= n <= 2000: prices.append(n)
    for m in re.findall(r"[₪]\s*(\d+)", text):
        n = int(m)
        if 10 <= n <= 2000: prices.append(n)
    for m in re.findall(r"(?:מחיר|כרטיס)[:\s]+(\d+)", text):
        n = int(m)
        if 10 <= n <= 2000: prices.append(n)
    if not prices: return None, None
    prices = sorted(set(prices))
    return prices[0], (prices[-1] if len(prices) > 1 else None)

# Category inference from event name + description
_MUSIC_KW   = re.compile(r"הופעה|לייב|קונצרט|concert|live|band|להקה|מופע", re.I)
_DJ_KW      = re.compile(r"מסיבה|party|dj\b|ריקוד|קלאב|club|techno|trance|house|electronic", re.I)
_STANDUP_KW = re.compile(r"סטנד.?אפ|stand.?up|קומדי|comedy", re.I)
_FILM_KW    = re.compile(r"סרט|הקרנה|film|cinema|screening", re.I)
_THEATER_KW = re.compile(r"תיאטרון|מחזה|theater|theatre", re.I)

def _infer_cat(text, default_cat, default_sub):
    if _STANDUP_KW.search(text): return "standup",  "standup"
    if _FILM_KW.search(text):    return "cultural", "film"
    if _THEATER_KW.search(text): return "cultural", "theater"
    if _DJ_KW.search(text):      return "music",    "dj-set"
    if _MUSIC_KW.search(text):   return "music",    "live"
    return default_cat, default_sub

# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class FBEvent:
    source_id:    str
    title:        str
    description:  str
    category:     str
    subcategory:  str
    event_date:   Optional[date]
    start_time:   Optional[str]
    end_time:     Optional[str]
    venue_name:   Optional[str]
    neighborhood: Optional[str]
    image_url:    Optional[str]
    ticket_url:   Optional[str]
    source_url:   str
    price_min:    Optional[int] = None
    price_max:    Optional[int] = None
    tags:         list = field(default_factory=list)

# ── Scraper ───────────────────────────────────────────────────────────────────

def _fetch_page_events(page_id, cfg, token, today_ts):
    venue_name, neighborhood, default_cat, default_sub = cfg
    events = []
    params = {
        "fields": "id,name,start_time,end_time,description,place,cover,ticket_uri",
        "since":  today_ts,
        "limit":  50,
        "access_token": token,
    }
    url = f"{GRAPH}/{page_id}/events"

    while url:
        r = _get(url, params=params)
        if not r: break
        try: data = r.json()
        except: break

        error = data.get("error")
        if error:
            log.warning(f"  {page_id}: API error — {error.get('message','')}")
            break

        for ev in data.get("data", []):
            sdt = _parse_iso(ev.get("start_time", ""))
            edt = _parse_iso(ev.get("end_time", ""))
            if not sdt: continue
            if sdt.date() < date.today(): continue

            desc = ev.get("description", "") or ""
            title = (ev.get("name") or "").strip()
            if not title: continue

            # Venue: prefer event's place, fall back to page default
            place = ev.get("place") or {}
            ev_venue = place.get("name") or venue_name
            ev_neighborhood = neighborhood  # FB doesn't give neighborhood

            cover = ev.get("cover") or {}
            image = cover.get("source") or None

            ticket_url = ev.get("ticket_uri") or None

            pmin, pmax = _extract_prices(desc)

            combined = f"{title} {desc}"
            category, subcategory = _infer_cat(combined, default_cat, default_sub)

            source_id = f"fb-{page_id}-{ev['id']}"
            source_url = f"https://www.facebook.com/events/{ev['id']}"

            events.append(FBEvent(
                source_id    = source_id,
                title        = title,
                description  = desc[:400],
                category     = category,
                subcategory  = subcategory,
                event_date   = sdt.date(),
                start_time   = sdt.strftime("%H:%M"),
                end_time     = edt.strftime("%H:%M") if edt else None,
                venue_name   = ev_venue,
                neighborhood = ev_neighborhood,
                image_url    = image,
                ticket_url   = ticket_url,
                source_url   = source_url,
                price_min    = pmin,
                price_max    = pmax,
                tags         = [],
            ))

        # Pagination
        paging = data.get("paging", {})
        next_url = paging.get("next")
        url = next_url
        params = None  # next_url already has all params encoded

    return events

def scrape(page_filter=None):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        token = _app_token()
    except RuntimeError as e:
        log.error(str(e))
        return []

    today_ts = int(datetime.now(timezone.utc).timestamp())
    all_events, seen = [], set()

    pages = {k: v for k, v in FB_PAGES.items() if page_filter is None or k == page_filter}

    for page_id, cfg in pages.items():
        log.info(f"Facebook: fetching {page_id} ({cfg[0]})...")
        evs = _fetch_page_events(page_id, cfg, token, today_ts)
        for ev in evs:
            if ev.source_id not in seen:
                seen.add(ev.source_id)
                all_events.append(ev)
        log.info(f"  → {len(evs)} events ({len(all_events)} total)")

    return all_events

# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--page", default=None, choices=list(FB_PAGES.keys()),
                        help="Scrape a single page (default: all)")
    args = parser.parse_args()

    evs = scrape(page_filter=args.page)
    print(f"\nTotal: {len(evs)} events")
    for e in sorted(evs, key=lambda x: (x.event_date or date.min, x.start_time or "")):
        price = f"₪{e.price_min}" if e.price_min else "?"
        print(f"  {e.event_date} {e.start_time or '?':5} | {e.title[:50]:<50} | {e.venue_name:<20} | {price}")

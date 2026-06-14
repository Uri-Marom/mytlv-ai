"""
Bandsintown scraper
Uses the public Bandsintown API v3 (no auth needed, app_id required).
Endpoint: GET https://rest.bandsintown.com/events/search
"""
import time, logging
from datetime import date, datetime, timedelta
from typing import Optional
from dataclasses import dataclass

import requests

log = logging.getLogger(__name__)

APP_ID   = "mytlv_ai"
API_BASE = "https://rest.bandsintown.com"

HEADERS = {"Accept": "application/json", "User-Agent": "mytlv-bot/1.0"}

# Map Bandsintown genres to our categories
GENRE_MAP = {
    "Electronic":   ("music", "dj-set"),
    "Rock":         ("music", "live"),
    "Pop":          ("music", "live"),
    "Jazz":         ("music", "live"),
    "Hip-Hop":      ("music", "live"),
    "Alternative":  ("music", "live"),
    "World Music":  ("music", "live"),
    "Classical":    ("cultural", "classical"),
    "R&B":          ("music", "live"),
    "Folk":         ("music", "live"),
    "Indie":        ("music", "live"),
    "Metal":        ("music", "live"),
}

@dataclass
class Event:
    source_id:   str
    title:       str
    artist_name: str
    category:    str
    subcategory: str
    event_date:  Optional[date]
    start_time:  Optional[str]
    venue_name:  Optional[str]
    venue_address:Optional[str]
    neighborhood: Optional[str]
    image_url:   Optional[str]
    ticket_url:  Optional[str]
    source_url:  str

session = requests.Session()
session.headers.update(HEADERS)

def _get(url, params=None, retries=3):
    for i in range(retries):
        try:
            r = session.get(url, params=params, timeout=15)
            if r.status_code == 429:
                time.sleep(10); continue
            r.raise_for_status()
            time.sleep(0.8)
            return r
        except Exception as e:
            log.warning(f"  attempt {i+1}: {e}")
            time.sleep(2*(i+1))
    return None

def _parse_dt(s):
    if not s: return None, None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.date(), dt.strftime("%H:%M")
    except:
        return None, None

def fetch_events_by_location(
    location="Tel Aviv, IL",
    radius_km=15,
    date_from: date = None,
    date_to:   date = None,
) -> list[Event]:
    """
    Search events near a location.
    BIT API: GET /events/search?location=&radius=&date=startDate,endDate&app_id=
    """
    if not date_from: date_from = date.today()
    if not date_to:   date_to   = date_from + timedelta(days=30)

    params = {
        "app_id":   APP_ID,
        "location": location,
        "radius":   radius_km,
        "date":     f"{date_from.isoformat()},{date_to.isoformat()}",
        "per_page": 100,
    }

    r = _get(f"{API_BASE}/events/search", params=params)
    if not r:
        log.warning("Bandsintown API unreachable")
        return []
    try:
        raw = r.json()
    except:
        log.warning("Bandsintown: non-JSON response")
        return []

    if not isinstance(raw, list):
        log.warning(f"Bandsintown unexpected response: {str(raw)[:200]}")
        return []

    events, seen = [], set()
    for ev in raw:
        eid = str(ev.get("id",""))
        if eid in seen: continue
        seen.add(eid)

        event_dt, start_time = _parse_dt(ev.get("datetime",""))

        venue = ev.get("venue", {})
        venue_name    = venue.get("name")
        venue_city    = venue.get("city","")
        venue_country = venue.get("country","")
        venue_addr    = venue.get("location") or f"{venue_city}, {venue_country}".strip(", ")

        # Only keep TLV-area events
        if "Tel Aviv" not in venue_city and "תל אביב" not in venue_city:
            if venue_country not in ("Israel","IL","ISR"):
                continue

        artist = ev.get("artist",{})
        artist_name = artist.get("name","")
        img_url     = artist.get("image_url") or artist.get("thumb_url")

        # Genre → category
        genres = artist.get("genres") or []
        cat, sub = "music", "live"
        for g in genres:
            if g in GENRE_MAP:
                cat, sub = GENRE_MAP[g]; break

        title = f"{artist_name}"
        offers = ev.get("offers",[])
        ticket_url = offers[0].get("url") if offers else ev.get("url")

        events.append(Event(
            source_id    = eid,
            title        = title,
            artist_name  = artist_name,
            category     = cat,
            subcategory  = sub,
            event_date   = event_dt,
            start_time   = start_time,
            venue_name   = venue_name,
            venue_address= venue_addr or None,
            neighborhood = None,
            image_url    = img_url,
            ticket_url   = ticket_url,
            source_url   = ev.get("url",""),
        ))

    log.info(f"Bandsintown: {len(events)} events in Tel Aviv area")
    return events

def scrape(date_from=None, date_to=None):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    today = date.today()
    df = date_from or today
    dt = date_to   or (today + timedelta(days=60))
    return fetch_events_by_location(date_from=df, date_to=dt)

if __name__ == "__main__":
    evs = scrape()
    for e in evs[:5]:
        print(f"  {e.event_date} {e.start_time} | {e.title} @ {e.venue_name}")

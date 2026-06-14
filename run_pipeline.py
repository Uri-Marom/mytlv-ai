"""
mytlv.ai — Main pipeline runner
Usage:
  python run_pipeline.py                  # live scrape + DB load
  python run_pipeline.py --seed-only      # load seed data only (no network)
  python run_pipeline.py --similarity     # recompute similarity scores
"""
import sys, os, logging, argparse
from datetime import date, datetime, timedelta
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ── SQLite for demo (swap to psycopg2 when DATABASE_URL is set) ────────────
import sqlite3

DB_PATH = os.environ.get("SQLITE_PATH", "/home/claude/mytlv/mytlv.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS venues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        neighborhood TEXT,
        address TEXT,
        lat REAL, lng REAL
    );
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        source_id TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        category TEXT,
        subcategory TEXT,
        sta_category TEXT,
        venue_id INTEGER REFERENCES venues(id),
        venue_name TEXT,
        neighborhood TEXT,
        event_date TEXT,
        start_time TEXT,
        end_time TEXT,
        price_min INTEGER DEFAULT 0,
        price_max INTEGER,
        image_url TEXT,
        ticket_url TEXT,
        source_url TEXT,
        tags TEXT,
        is_published INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        UNIQUE(source, source_id)
    );
    CREATE INDEX IF NOT EXISTS idx_events_date     ON events(event_date);
    CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);
    CREATE TABLE IF NOT EXISTS event_similarity (
        event_a_id INTEGER NOT NULL,
        event_b_id INTEGER NOT NULL,
        score_user_overlap REAL DEFAULT 0,
        score_venue        REAL DEFAULT 0,
        score_temporal     REAL DEFAULT 0,
        score_organizer    REAL DEFAULT 0,
        score_composite    REAL DEFAULT 0,
        overlap_user_count INTEGER DEFAULT 0,
        computed_at TEXT DEFAULT (datetime('now')),
        PRIMARY KEY (event_a_id, event_b_id)
    );
    CREATE INDEX IF NOT EXISTS idx_sim_a ON event_similarity(event_a_id, score_composite DESC);
    CREATE INDEX IF NOT EXISTS idx_sim_b ON event_similarity(event_b_id, score_composite DESC);
    """)
    conn.commit()
    log.info(f"DB initialised at {DB_PATH}")

def upsert_venue(conn, name, neighborhood=None, address=None):
    if not name: return None
    conn.execute("""
        INSERT INTO venues(name,neighborhood,address) VALUES(?,?,?)
        ON CONFLICT(name) DO UPDATE SET
            neighborhood=COALESCE(excluded.neighborhood,venues.neighborhood),
            address=COALESCE(excluded.address,venues.address)
    """, (name, neighborhood, address))
    conn.commit()
    row = conn.execute("SELECT id FROM venues WHERE name=?", (name,)).fetchone()
    return row[0] if row else None

def upsert_events(conn, events, source):
    n = 0
    for ev in events:
        edate = ev.get("event_date") if isinstance(ev, dict) else getattr(ev,"event_date",None)
        if not edate: continue
        if hasattr(edate,"isoformat"): edate = edate.isoformat()

        d = ev if isinstance(ev,dict) else ev.__dict__
        vid = upsert_venue(conn, d.get("venue_name"), d.get("neighborhood"), d.get("venue_address") or d.get("address"))
        tags = d.get("tags")
        if isinstance(tags, list): tags = ",".join(tags)

        conn.execute("""
            INSERT INTO events(source,source_id,title,description,category,subcategory,sta_category,
                venue_id,venue_name,neighborhood,event_date,start_time,end_time,
                price_min,price_max,image_url,ticket_url,source_url,tags)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(source,source_id) DO UPDATE SET
                title=excluded.title, description=excluded.description,
                category=excluded.category, subcategory=excluded.subcategory,
                event_date=excluded.event_date, start_time=excluded.start_time,
                end_time=excluded.end_time, price_min=excluded.price_min,
                price_max=excluded.price_max, image_url=excluded.image_url,
                ticket_url=excluded.ticket_url, updated_at=datetime('now')
        """, (
            source, d.get("source_id"), d.get("title"), d.get("description",""),
            d.get("category"), d.get("subcategory"), d.get("sta_category"),
            vid, d.get("venue_name"), d.get("neighborhood"),
            edate, d.get("start_time"), d.get("end_time"),
            d.get("price_min",0), d.get("price_max"),
            d.get("image_url"), d.get("ticket_url"), d.get("source_url"),
            tags,
        ))
        n += 1
    conn.commit()
    log.info(f"  Upserted {n} events from {source}")
    return n

# ── Similarity engine ──────────────────────────────────────────────────────

def compute_similarity(conn):
    """Compute pairwise similarity for all events and store results."""
    rows = conn.execute("""
        SELECT id,category,subcategory,venue_name,neighborhood,event_date,start_time
        FROM events WHERE is_published=1
    """).fetchall()

    if len(rows) < 2:
        log.warning("Not enough events to compute similarity")
        return

    # Synthetic user sets (deterministic, affinity-based) — replace with real data later
    import random
    def rng(seed):
        r = random.Random(seed)
        return r

    user_sets = {}
    for ev in rows:
        r = rng(ev["id"] * 7919)
        size = 60 + r.randint(0, 300)
        pool = set(r.randint(0, 3000) for _ in range(size))
        # Add shared users based on category/venue affinity
        for other in rows:
            if other["id"] == ev["id"]: continue
            affinity = (
                (0.35 if other["category"]    == ev["category"]    else 0) +
                (0.25 if other["subcategory"] == ev["subcategory"] else 0) +
                (0.15 if other["venue_name"]  == ev["venue_name"]  and ev["venue_name"] else 0) +
                (0.08 if other["neighborhood"]== ev["neighborhood"] and ev["neighborhood"] else 0)
            )
            if affinity > 0:
                r2 = rng(other["id"] * 6271)
                shared = int(affinity * 80)
                pool.update(r2.randint(0, 3000) for _ in range(shared))
        user_sets[ev["id"]] = pool

    # Pairwise Jaccard + secondary signals
    from itertools import combinations
    sim_rows = []
    for a, b in combinations(rows, 2):
        sa, sb = user_sets[a["id"]], user_sets[b["id"]]
        inter  = len(sa & sb)
        union  = len(sa | sb)
        jaccard = inter / union if union else 0

        v_score = (1.0 if a["venue_name"] and a["venue_name"] == b["venue_name"] else
                   0.5 if a["neighborhood"] and a["neighborhood"] == b["neighborhood"] else 0)
        try:
            ha = int((a["start_time"] or "00:00")[:2])
            hb = int((b["start_time"] or "00:00")[:2])
            t_score = 1.0 if abs(ha-hb) <= 2 else 0.5 if abs(ha-hb) <= 4 else 0
        except: t_score = 0
        o_score = (0.8 if a["subcategory"] == b["subcategory"] else
                   0.4 if a["category"]    == b["category"]    else 0)

        confidence = min(1.0, inter / 20)
        composite  = (0.60*jaccard + 0.20*v_score + 0.12*t_score + 0.08*o_score) * confidence

        if composite < 0.005: continue
        aid, bid = min(a["id"],b["id"]), max(a["id"],b["id"])
        sim_rows.append((aid,bid,round(jaccard,4),round(v_score,4),round(t_score,4),round(o_score,4),round(composite,4),inter))

    conn.execute("DELETE FROM event_similarity")
    conn.executemany("""
        INSERT OR REPLACE INTO event_similarity
        (event_a_id,event_b_id,score_user_overlap,score_venue,score_temporal,score_organizer,score_composite,overlap_user_count)
        VALUES(?,?,?,?,?,?,?,?)
    """, sim_rows)
    conn.commit()
    log.info(f"Similarity: {len(sim_rows)} pairs computed")

# ── Main ───────────────────────────────────────────────────────────────────

def run(seed_only=False, similarity_only=False):
    conn = get_conn()
    init_db(conn)

    if not similarity_only:
        if seed_only:
            from seed_data import STA_EVENTS
            log.info(f"Loading {len(STA_EVENTS)} seed events...")
            by_source = defaultdict(list)
            for ev in STA_EVENTS:
                by_source[ev["source"]].append(ev)   # pass dicts directly
            for src, evs in by_source.items():
                upsert_events(conn, evs, src)
        else:
            # Live scrape
            log.info("=== Scraping Secret Tel Aviv ===")
            try:
                sys.path.insert(0, "/home/claude/mytlv")
                from scraper_sta import scrape as sta_scrape
                sta_evs = sta_scrape()
                upsert_events(conn, sta_evs, "secret_tel_aviv")
            except Exception as e:
                log.error(f"STA scraper failed: {e}. Loading seed data instead.")
                from seed_data import STA_EVENTS
                by_source = defaultdict(list)
                for ev in STA_EVENTS:
                    by_source[ev["source"]].append(ev)
                for src, evs in by_source.items():
                    upsert_events(conn, evs, src)

            log.info("=== Scraping Entrio ===")
            try:
                from scraper_entrio import scrape as entrio_scrape
                entrio_evs = entrio_scrape()
                upsert_events(conn, entrio_evs, "entrio")
            except Exception as e:
                log.error(f"Entrio scraper failed: {e}")

            log.info("=== Scraping Bandsintown ===")
            try:
                from scraper_bandsintown import scrape as bit_scrape
                bit_evs = bit_scrape()
                upsert_events(conn, bit_evs, "bandsintown")
            except Exception as e:
                log.error(f"Bandsintown scraper failed: {e}")

            log.info("=== Scraping Facebook Pages ===")
            try:
                from scraper_facebook import scrape as fb_scrape
                fb_evs = fb_scrape()
                # Convert FBEvent dataclasses to dicts
                fb_dicts = [e.__dict__ for e in fb_evs]
                upsert_events(conn, fb_dicts, "facebook")
            except Exception as e:
                log.error(f"Facebook scraper failed: {e}")

            log.info("=== Scraping Venues (Barby, Levontin, Ozen, Teder, Tmuna, ...) ===")
            try:
                from scraper_venues import scrape_all_venues
                venue_evs = scrape_all_venues()
                # Convert VenueEvent dataclasses to dicts compatible with upsert_events
                venue_dicts = []
                for ve in venue_evs:
                    venue_dicts.append({
                        "source":      ve.source,
                        "source_id":   ve.source_id,
                        "title":       ve.title,
                        "description": ve.description,
                        "category":    ve.category,
                        "subcategory": ve.subcategory,
                        "sta_category": None,
                        "venue_name":  ve.venue_name,
                        "neighborhood": ve.neighborhood,
                        "event_date":  ve.event_date,
                        "start_time":  ve.start_time,
                        "end_time":    ve.end_time,
                        "price_min":   ve.price_min,
                        "price_max":   ve.price_max,
                        "image_url":   ve.image_url,
                        "ticket_url":  ve.ticket_url,
                        "source_url":  ve.source_url,
                        "tags":        ve.tags,
                    })
                by_source = defaultdict(list)
                for d in venue_dicts:
                    by_source[d["source"]].append(d)
                for src, evs in by_source.items():
                    upsert_events(conn, evs, src)
            except Exception as e:
                log.error(f"Venue scrapers failed: {e}", exc_info=True)

    log.info("=== Computing similarity ===")
    compute_similarity(conn)

    # Print summary
    total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    sim   = conn.execute("SELECT COUNT(*) FROM event_similarity").fetchone()[0]
    log.info(f"\n{'='*50}")
    log.info(f"  Events in DB : {total}")
    log.info(f"  Sim pairs    : {sim}")

    print("\n=== EVENTS THIS WEEKEND ===")
    rows = conn.execute("""
        SELECT title, event_date, start_time, venue_name, neighborhood, category, subcategory,
               price_min, price_max, source
        FROM events
        WHERE event_date BETWEEN '2026-06-14' AND '2026-06-21'
          AND is_published=1
        ORDER BY event_date, start_time
    """).fetchall()
    for r in rows:
        price = "Free" if r["price_min"]==0 else f"₪{r['price_min']}"
        if r["price_max"] and r["price_max"] != r["price_min"]:
            price += f"-{r['price_max']}"
        print(f"  {r['event_date']} {r['start_time'] or '??:??'} | {r['title'][:45]:<45} | {r['venue_name'] or '?':<25} | {price:<10} | [{r['source']}]")

    conn.close()

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--seed-only",      action="store_true")
    p.add_argument("--similarity",     action="store_true")
    args = p.parse_args()
    run(seed_only=args.seed_only, similarity_only=args.similarity)

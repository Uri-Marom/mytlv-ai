"""
Seed the Neon Postgres DB from seed_data.py.
Requires DATABASE_URL in environment (source .env.local first).
Usage: python seed_postgres.py
"""
import os, sys, json
import psycopg2
from psycopg2.extras import execute_values
from seed_data import STA_EVENTS

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    sys.exit("DATABASE_URL not set — run: source .env.local && python seed_postgres.py")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

rows = []
for e in STA_EVENTS:
    tags = e.get("tags") or []
    rows.append((
        e["source"], e["source_id"], e["title"],
        e.get("description", ""), e.get("category"), e.get("subcategory"),
        e.get("sta_category"), e.get("venue_name"), e.get("neighborhood"),
        str(e["event_date"]), e.get("start_time"), e.get("end_time"),
        e.get("price_min", 0), e.get("price_max"),
        e.get("image_url"), e.get("ticket_url"), e.get("source_url"),
        tags,
    ))

execute_values(cur, """
    INSERT INTO events (
        source, source_id, title, description, category, subcategory,
        sta_category, venue_name, neighborhood,
        event_date, start_time, end_time,
        price_min, price_max, image_url, ticket_url, source_url, tags
    ) VALUES %s
    ON CONFLICT (source, source_id) DO UPDATE SET
        title        = EXCLUDED.title,
        description  = EXCLUDED.description,
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
cur.execute("SELECT COUNT(*) FROM events")
print(f"Done — {cur.fetchone()[0]} events in DB")
cur.close()
conn.close()

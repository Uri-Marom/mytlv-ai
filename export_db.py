"""
Export events from SQLite → JSON for App.jsx DB constant.
Usage:
  python export_db.py                # prints JSON to stdout
  python export_db.py --update       # patches DB constant in src/App.jsx in-place
"""
import os, json, re, argparse, sqlite3
from datetime import date

DB_PATH = os.environ.get("SQLITE_PATH", "/Users/urimarom/Projects/tlv-events/mytlv.db")
APP_PATH = os.path.join(os.path.dirname(__file__), "src", "App.jsx")
TODAY = date.today().isoformat()

def get_events(conn):
    rows = conn.execute("""
        SELECT e.id, e.source, e.source_id, e.title, e.description,
               e.category, e.subcategory, e.sta_category,
               v.name AS venue_name, e.neighborhood,
               e.event_date, e.start_time, e.end_time,
               e.price_min, e.price_max,
               e.image_url, e.ticket_url, e.source_url,
               e.tags
        FROM events e
        LEFT JOIN venues v ON e.venue_id = v.id
        WHERE e.is_published = 1
          AND e.event_date >= ?
        ORDER BY e.event_date, e.start_time
    """, (TODAY,)).fetchall()
    return rows

def get_similarity(conn):
    rows = conn.execute("""
        SELECT event_a_id, event_b_id,
               score_user_overlap, score_venue, score_temporal, score_organizer, score_composite
        FROM event_similarity
        WHERE score_composite > 0.01
    """).fetchall()
    return rows

def row_to_dict(row):
    tags = row["tags"]
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    return {
        "id":           row["id"],
        "source":       row["source"],
        "title":        row["title"] or "",
        "description":  (row["description"] or "")[:300],
        "category":     row["category"] or "cultural",
        "subcategory":  row["subcategory"] or "",
        "sta_category": row["sta_category"] or "",
        "venue_name":   row["venue_name"] or "",
        "neighborhood": row["neighborhood"] or "",
        "event_date":   row["event_date"] or "",
        "start_time":   row["start_time"] or "",
        "end_time":     row["end_time"] or "",
        "price_min":    row["price_min"],
        "price_max":    row["price_max"],
        "image_url":    row["image_url"] or "",
        "ticket_url":   row["ticket_url"] or "",
        "source_url":   row["source_url"] or "",
        "tags":         tags or [],
    }

def sim_to_list(sim_rows):
    return [
        {
            "event_a_id": r[0], "event_b_id": r[1],
            "score_user_overlap": round(r[2], 4),
            "score_venue":        round(r[3], 4),
            "score_temporal":     round(r[4], 4),
            "score_organizer":    round(r[5], 4),
            "score_composite":    round(r[6], 4),
        }
        for r in sim_rows
    ]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", action="store_true", help="Patch App.jsx in-place")
    parser.add_argument("--db", default=DB_PATH)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    events   = [row_to_dict(r) for r in get_events(conn)]
    sim_rows = get_similarity(conn)
    sim_list = sim_to_list(sim_rows)
    conn.close()

    db_obj  = {"events": events, "similarity": sim_list}
    db_json = json.dumps(db_obj, ensure_ascii=False, separators=(",", ":"))

    n_ev, n_sim = len(events), len(sim_list)
    comment = f"// ── Live database ({n_ev} real events + {n_sim} similarity pairs) ──────────────────"

    print(f"Events: {n_ev}, similarity pairs: {n_sim}", flush=True)

    if args.update:
        with open(APP_PATH, "r", encoding="utf-8") as f:
            src = f.read()

        src = re.sub(
            r"// ── Live database[^\n]*\nconst DB = \{.*?\};",
            f"{comment}\nconst DB = {db_json};",
            src, flags=re.DOTALL, count=1
        )
        with open(APP_PATH, "w", encoding="utf-8") as f:
            f.write(src)
        print(f"Updated {APP_PATH}")
    else:
        print(db_json[:500], "...")

if __name__ == "__main__":
    main()

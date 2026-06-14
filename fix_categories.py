"""
Category corrections for mytlv.ai events.
Run: source .env.local && python fix_categories.py
"""
import os, psycopg2

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

fixes = [
    # ── Exhibitions hiding as cultural/general ─────────────────────────────
    # These have "Exhibition", "Fresh Paint", etc. in the title but subcategory=general
    ("UPDATE events SET subcategory='exhibition' WHERE id IN (34,76,115,29,128)",
     "Art exhibitions: Comunidad Judía, Future Legacy, Fresh Paint, House of Others, Illustrator Fair"),

    # ── Talks / lectures ──────────────────────────────────────────────────
    ("UPDATE events SET subcategory='talk' WHERE id = 63",
     "Tipsy Talks - Monet × Manet → cultural/talk"),

    ("UPDATE events SET subcategory='talk' WHERE id = 122",
     "Double book launch → cultural/talk"),

    ("UPDATE events SET subcategory='talk' WHERE title ILIKE '%what should we do%'",
     "'What should we do? The conflict version' → cultural/talk"),

    ("UPDATE events SET subcategory='talk' WHERE title ILIKE '%kan 11%beit ariela%'",
     "Kan 11 + Beit Ariela reading event → cultural/talk"),

    # ── Job fair and book launch wrongly in music ─────────────────────────
    ("UPDATE events SET category='cultural', subcategory='general' WHERE id = 50",
     "The Big Youth Job Fair 2026 → cultural/general (not music!)"),

    ("UPDATE events SET category='cultural', subcategory='talk' WHERE id = 36",
     "Indicord book launch → cultural/talk (not music)"),

    # ── Opera / concerts in cultural/general → music/live ─────────────────
    ("UPDATE events SET category='music', subcategory='live' WHERE id IN (123, 124)",
     "4Tress at the Opera + White Night Nabucco → music/live"),

    # ── Restaurant / food events in music/dj-set → market/food ────────────
    ("UPDATE events SET category='market', subcategory='food' WHERE id = 127",
     "12 Years of Cicchetti (restaurant anniversary) → market/food"),

    # ── Theater / musical ─────────────────────────────────────────────────
    ("UPDATE events SET subcategory='musical' WHERE id IN (111, 114)",
     "Pere – Original Musical → cultural/musical"),

    # ── Herzl Live = live art festival ─────────────────────────────────────
    ("UPDATE events SET subcategory='festival' WHERE id = 125",
     "Herzl Live - A festival of live art → cultural/festival"),
]

total = 0
for sql, desc in fixes:
    cur.execute(sql)
    n = cur.rowcount
    total += n
    print(f"  [{n:2d} row(s)] {desc}")

conn.commit()
conn.close()
print(f"\nDone — {total} rows updated")

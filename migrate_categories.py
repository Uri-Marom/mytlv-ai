"""
Migrate to multi-category support.
Run: source .env.local && python migrate_categories.py
"""
import os, psycopg2
conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

# ── Step 1: add column ─────────────────────────────────────────────────────
cur.execute("ALTER TABLE events ADD COLUMN IF NOT EXISTS categories TEXT[] DEFAULT '{}'")

# ── Step 2: base population from existing category/subcategory ─────────────
rules = [
    ("UPDATE events SET categories = ARRAY['music']    WHERE category = 'music'", "music → ['music']"),
    ("UPDATE events SET categories = ARRAY['art']      WHERE category = 'cultural' AND subcategory = 'exhibition'", "cultural/exhibition → ['art']"),
    ("UPDATE events SET categories = ARRAY['cultural'] WHERE category = 'cultural' AND subcategory != 'exhibition'", "cultural/* → ['cultural']"),
    ("UPDATE events SET categories = ARRAY['food']     WHERE category = 'market' AND subcategory = 'food'", "market/food → ['food']"),
    ("UPDATE events SET categories = ARRAY['market']   WHERE category = 'market' AND subcategory != 'food'", "market/* → ['market']"),
]

# ── Step 3: border case multi-category overrides ───────────────────────────
border_cases = [
    # "Live From the Storm" appears twice: cultural/exhibition (id=4) and music/dj-set (id=70)
    # The pop-up is an art/exhibition event WITH music. Keep both, give art+music categories.
    ("UPDATE events SET categories = ARRAY['art','music'] WHERE id IN (4, 70)",
     "Live From the Storm → ['art','music'] (pop-up exhibition + dj set)"),

    # Cheers! X MyYain Wine Festival – wine festival with sunset DJ
    ("UPDATE events SET categories = ARRAY['food','music'] WHERE id = 102",
     "Cheers! Wine Festival → ['food','music']"),

    # Jazz & Wine @ Baba Yaga
    ("UPDATE events SET categories = ARRAY['music','food'] WHERE title ILIKE '%jazz%wine%'",
     "Jazz & Wine → ['music','food']"),

    # Kobi Farhi book launch – Orphaned Land singer, almost certainly includes performance
    ("UPDATE events SET categories = ARRAY['cultural','music'] WHERE id = 44",
     "Kobi Farhi book launch → ['cultural','music']"),

    # Findings from the Present – discourse about an art collection at Liebling Haus
    ("UPDATE events SET categories = ARRAY['art','cultural'] WHERE id = 91",
     "Findings from the Present → ['art','cultural']"),

    # A restless night – Levontin 7 at the Tel Aviv Museum of Art
    ("UPDATE events SET categories = ARRAY['music','art'] WHERE title ILIKE '%restless night%levontin%'",
     "A restless night (Levontin @ Museum) → ['music','art']"),

    # Kabbalat Shabbat – singing ceremony, cultural + music
    ("UPDATE events SET categories = ARRAY['music','cultural'] WHERE title ILIKE '%kabbalat shabbat%'",
     "Kabbalat Shabbat → ['music','cultural']"),

    # Singing and Telling: 80 Years – commemoration with singing
    ("UPDATE events SET categories = ARRAY['music','cultural'] WHERE title ILIKE '%singing and telling%'",
     "Singing and Telling → ['music','cultural']"),

    # Psychedelic Hafla – party at Levontin 7, more dj/party than concert
    ("UPDATE events SET subcategory = 'dj-set' WHERE id = 67",
     "Psychedelic Hafla → subcategory dj-set (it's a party)"),

    # Shuk Olim – expat community market, market + cultural
    ("UPDATE events SET categories = ARRAY['market','cultural'] WHERE id = 120",
     "Shuk Olim → ['market','cultural']"),

    # Tipsy Talks - Monet X Manet – talk about art → art + cultural
    ("UPDATE events SET categories = ARRAY['cultural','art'] WHERE id = 63",
     "Tipsy Talks - Monet × Manet → ['cultural','art']"),
]

print("── Base population ─────────────────────────────────────────────")
for sql, desc in rules:
    cur.execute(sql); print(f"  [{cur.rowcount:3d}] {desc}")

print("\n── Border case multi-category overrides ────────────────────────")
for sql, desc in border_cases:
    cur.execute(sql); print(f"  [{cur.rowcount:3d}] {desc}")

# ── Step 4: verify ─────────────────────────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM events WHERE categories = '{}'")
empty = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM events WHERE array_length(categories,1) > 1")
multi = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM events")
total = cur.fetchone()[0]

conn.commit()
conn.close()
print(f"\n✓ {total} events total | {multi} multi-category | {empty} uncategorized")

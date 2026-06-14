import { neon } from "@neondatabase/serverless";

// ── Deduplication ────────────────────────────────────────────────────────────
// Key: event_date + normalised venue + start_time (catches cross-source dups
// like STA "Eviatar Banai" vs Barby "אביתר בנאי" at same venue/time).
// Also catches STA internal dups ("Off Grid @ Kuli Alma" vs "Off Grid").

function norm(s) {
  return (s || "").toLowerCase().replace(/\s+/g, " ").trim();
}

function dataScore(e) {
  return (e.image_url ? 2 : 0) +
         (e.ticket_url ? 1 : 0) +
         ((e.description || "").length > 80 ? 1 : 0) +
         (e.price_max ? 1 : 0);
}

function deduplicate(events) {
  // Priority: STA > venue scrapers > others (STA has richer metadata)
  const sourcePriority = s =>
    s === "secret_tel_aviv" ? 0 :
    s.startsWith("venue_") ? 1 : 2;

  const dominated = new Set();
  const groups = new Map();

  for (const e of events) {
    if (!e.venue_name || !e.start_time) continue;
    const key = `${e.event_date}|${norm(e.venue_name)}|${(e.start_time || "").slice(0, 5)}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(e);
  }

  for (const group of groups.values()) {
    if (group.length < 2) continue;
    // Pick winner: highest source priority, then highest data score
    group.sort((a, b) =>
      sourcePriority(a.source) - sourcePriority(b.source) ||
      dataScore(b) - dataScore(a)
    );
    for (let i = 1; i < group.length; i++) dominated.add(group[i].id);
  }

  return events.filter(e => !dominated.has(e.id));
}

// ── Handler ──────────────────────────────────────────────────────────────────

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Cache-Control", "s-maxage=300, stale-while-revalidate=60");

  const sql = neon(process.env.DATABASE_URL);

  const [rows, sourcesRaw] = await Promise.all([
    sql`
      SELECT
        id, source, title, description,
        category, subcategory, sta_category,
        venue_name, neighborhood,
        event_date::text AS event_date,
        start_time::text AS start_time,
        end_time::text   AS end_time,
        price_min, price_max,
        image_url, ticket_url, source_url,
        tags, categories
      FROM events
      WHERE is_published = true
      ORDER BY event_date, start_time
    `,
    sql`SELECT DISTINCT source FROM events WHERE is_published = true ORDER BY source`,
  ]);

  const events = deduplicate(rows);
  const sources = sourcesRaw.map(r => r.source);

  res.json({ events, sources });
}

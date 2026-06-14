import { neon } from "@neondatabase/serverless";

// ── Deduplication ────────────────────────────────────────────────────────────

function norm(s) {
  return (s || "").toLowerCase().replace(/\s+/g, " ").trim();
}

function dataScore(e) {
  return (e.image_url ? 2 : 0) +
         (e.ticket_url ? 1 : 0) +
         ((e.description || "").length > 80 ? 1 : 0) +
         (e.price_max ? 1 : 0);
}

function timeMins(t) {
  // "HH:MM:SS" or "HH:MM" → minutes since midnight
  if (!t) return null;
  const [h, m] = t.split(":").map(Number);
  return h * 60 + m;
}

function timeDiff(tA, tB) {
  // Absolute difference in minutes, wrapping midnight
  const a = timeMins(tA), b = timeMins(tB);
  if (a === null || b === null) return null;
  const d = Math.abs(a - b);
  return Math.min(d, 1440 - d); // handle midnight wrap
}

function deduplicate(events) {
  // STA has richer metadata (descriptions, images from their editorial team)
  const sourcePriority = s =>
    s === "secret_tel_aviv" ? 0 :
    s.startsWith("venue_") ? 1 : 2;

  const dominated = new Set();

  // Pass 1: exact date + venue + time match (same-source internal dups too)
  const exactGroups = new Map();
  for (const e of events) {
    if (!e.venue_name || !e.start_time) continue;
    const key = `${e.event_date}|${norm(e.venue_name)}|${(e.start_time).slice(0, 5)}`;
    if (!exactGroups.has(key)) exactGroups.set(key, []);
    exactGroups.get(key).push(e);
  }
  for (const group of exactGroups.values()) {
    if (group.length < 2) continue;
    group.sort((a, b) => sourcePriority(a.source) - sourcePriority(b.source) || dataScore(b) - dataScore(a));
    for (let i = 1; i < group.length; i++) dominated.add(group[i].id);
  }

  // Pass 2: cross-source fuzzy — same date + venue, times within 45 min (or one null).
  // Handles: Barby "doors 20:30" (STA) vs "show 21:00" (venue_barby),
  //          Hameretz2 null time (before fix) vs STA with time.
  // Groups by date + venue across different sources.
  const venueDay = new Map();
  for (const e of events) {
    if (!e.venue_name || dominated.has(e.id)) continue;
    const key = `${e.event_date}|${norm(e.venue_name)}`;
    if (!venueDay.has(key)) venueDay.set(key, []);
    venueDay.get(key).push(e);
  }

  for (const group of venueDay.values()) {
    if (group.length < 2) continue;
    // Only compare cross-source pairs
    for (let i = 0; i < group.length; i++) {
      if (dominated.has(group[i].id)) continue;
      for (let j = i + 1; j < group.length; j++) {
        if (dominated.has(group[j].id)) continue;
        const a = group[i], b = group[j];
        if (a.source === b.source) continue;

        const diff = timeDiff(a.start_time, b.start_time);
        // Match if: one has no time, OR times within 45 min
        const timeCompatible = diff === null || diff <= 45;
        if (!timeCompatible) continue;

        // Keep the better-quality event
        const aWins = sourcePriority(a.source) < sourcePriority(b.source) ||
          (sourcePriority(a.source) === sourcePriority(b.source) && dataScore(a) >= dataScore(b));
        dominated.add(aWins ? b.id : a.id);
      }
    }
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

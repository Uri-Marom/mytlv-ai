import { neon } from "@neondatabase/serverless";

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Cache-Control", "s-maxage=300, stale-while-revalidate=60");

  const sql = neon(process.env.DATABASE_URL);

  const rows = await sql`
    SELECT
      id, source, title, description,
      category, subcategory, sta_category,
      venue_name, neighborhood,
      event_date::text AS event_date,
      start_time::text AS start_time,
      end_time::text   AS end_time,
      price_min, price_max,
      image_url, ticket_url, source_url,
      tags
    FROM events
    WHERE is_published = true
      AND event_date >= CURRENT_DATE
    ORDER BY event_date, start_time
  `;

  res.json({ events: rows });
}

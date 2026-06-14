# myTLV.ai — Claude Code Project Guide

## Project overview

Tel Aviv events calendar app. The frontend is a self-contained React SPA with all event data embedded as a JS constant (`DB`). No backend or API is required at runtime.

## Directory structure

```
tlv-events/
├── src/
│   ├── App.jsx          # Entire React frontend (single component, ~1700 lines)
│   └── main.jsx         # Vite entry point
├── mytlv-app.jsx        # Source copy of the component (kept for reference)
├── index.html           # Vite HTML shell
├── vite.config.js       # Vite + React plugin config
├── package.json
│
├── run_pipeline.py      # Main pipeline runner — scrape + DB load + similarity
├── scraper_sta.py       # Secret Tel Aviv scraper
├── scraper_entrio.py    # Entrio scraper
├── scraper_bandsintown.py # Bandsintown scraper
├── seed_data.py         # 27 real TLV events seeded into SQLite
├── schema.sql           # Postgres schema (used when DATABASE_URL is set)
└── mytlv.db             # SQLite database with live event data
```

## Local development

```bash
npm install
npm run dev          # http://localhost:5173
npm run build        # production build → dist/
```

## Running the scrapers

The pipeline writes to SQLite by default. Set `SQLITE_PATH` to override the DB location.

```bash
# Full scrape + DB load
python run_pipeline.py

# Load seed data only (no network requests)
python run_pipeline.py --seed-only

# Recompute similarity scores only
python run_pipeline.py --similarity
```

To use Postgres instead of SQLite, set `DATABASE_URL` in the environment and run `schema.sql` once:

```bash
psql $DATABASE_URL -f schema.sql
DATABASE_URL=postgres://... python run_pipeline.py
```

## Updating the frontend with new events

1. Run `python run_pipeline.py` to refresh the SQLite DB.
2. Export the events as JSON and paste into the `DB` constant at the top of `src/App.jsx`.
3. Commit and redeploy (see below).

## Redeploying to Vercel

```bash
# Preview deploy
vercel

# Production deploy
vercel --prod
```

Live URL: **https://tlv-events.vercel.app**

The project is linked to Vercel via `.vercel/project.json` (not committed — add to `.gitignore` if needed).

## GitHub

Repository: https://github.com/Uri-Marom/mytlv-ai

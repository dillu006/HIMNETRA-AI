# Post-Deploy Checklist — Himalayan AI

Run through these in order after deploying via render.yaml.

## 1. Database
- [ ] Postgres created on Render, status "Available"
- [ ] Connected via dashboard's psql shell, ran: `CREATE EXTENSION postgis;`
- [ ] Ran `database/schema.sql` (creates tables + seeds 8 locations)
- [ ] Ran `database/migrations/002_location_signals.sql`
- [ ] Ran `python -m scripts.seed_demo_data` OR `ingest_real_data.py` at least once
      (via Render Shell tab, or locally with DATABASE_URL pointed at the
      Render DB's *external* connection string)

## 2. Backend
- [ ] Web service status "Live" in Render dashboard
- [ ] `OPENWEATHER_API_KEY` and `FIRMS_MAP_KEY` set in dashboard env vars
- [ ] Run: `python smoke_test.py https://<your-backend>.onrender.com`
      All 5 checks should print OK.
- [ ] Visit `https://<your-backend>.onrender.com/docs` — Swagger UI loads,
      you can manually try `/api/risk/all` from the browser

## 3. Scheduler (background ingestion)
- [ ] Check Render service logs for "Ingestion scheduler started" on boot
- [ ] Wait ~30 min (or your `WEATHER_FIRE_INTERVAL_MIN`), check logs for
      "Running scheduled data ingestion..."
- [ ] Remember: free-tier web services sleep after 15 min idle — if no
      one hits the API, the scheduler pauses too. Fine for testing;
      for real always-on ingestion, upgrade to the $7/mo Starter plan.

## 4. Frontend (PWA / static site)
- [ ] Static site status "Live"
- [ ] `VITE_API_BASE` env var updated to the real backend URL (not the
      placeholder in render.yaml)
- [ ] Open the site URL — location cards + map render with real data
- [ ] No red "Backend not reachable" banner

## 5. Mobile install
- [ ] Open the frontend URL on your phone browser
- [ ] Android: menu -> "Add to Home screen" / iOS: share -> "Add to Home Screen"
- [ ] Icon appears, opens full-screen, loads data over the deployed backend

## 6. Desktop app
- [ ] Locally: `VITE_API_BASE=https://<your-backend>.onrender.com npm run tauri build`
- [ ] Resulting installer (in `src-tauri/target/release/bundle/`) opens
      and shows live data pointed at the deployed backend, not localhost

## If something fails
`smoke_test.py`'s FAIL line tells you which layer broke:
- Root endpoint fails -> service isn't running, check Render logs
- Locations check fails -> schema.sql didn't run, or PostGIS extension missing
- Risk/all fails -> location_signals table is empty (seed/ingest script never ran)

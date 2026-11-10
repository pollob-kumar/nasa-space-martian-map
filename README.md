# RedNav-N399 — NASA Space Apps 2026 · Interplanetary Survival Guide: Martian Map

Layered NASA-data map + Marswalk route planner + helmet HUD, for one chosen Mars region (plus 5 Bangladesh-named craters as extra selectable regions).

```
backend/   FastAPI: regions, layers, sites, A* route planner, travel time      (owner: backend)
data/      pipeline: NASA/USGS rasters -> slope/hillshade/hazard PNG + JSON     (owners: data team)
frontend/  Next.js helmet HUD + layered map (theme from the original RedNav)    (owner: frontend)
docs/      project context, tasks per person, data sources, API spec
prompt.md  master prompt for an AI coding agent to finish the project
```

## Run it in 3 commands (works today with synthetic demo data)
```bash
pip install -r backend/requirements.txt -r data/requirements.txt
python data/scripts/run_all.py --full-demo   # writes demo_synthetic + jezero_delta + the 5 bd_* craters (ALL SYNTHETIC, labelled)
(cd backend && python -m uvicorn app.main:app --port 8000 --reload) &
(cd frontend && cp .env.example .env.local && npm install && npm run dev)   # http://localhost:3000
```
Real data: see `docs/DATA_SOURCES.md` then `python data/scripts/run_all.py --region jezero_delta`.

## Honesty rules (from the NASA brief)
No fake data shown as real · every layer shows source/resolution/date · missing data is shown as MISSING · thresholds are labelled assumptions · never say "safe", say "below the slope limit in the data used".

## What is in the app (details: docs/FEATURES.md)
Layers: surface imagery · elevation/slope · chemical index · geological features · rover observations · hazards · routes (every layer shows source, resolution, missing data).
Route planner: 3 strategies (balanced / gentlest slopes / shortest feasible), travel time, **oxygen budget with reserve + round trip**, radiation/space-weather safety context, routed detours to science near the route, **Route Analysis window** (5 questions from the NASA brief), plain-language context warnings.
Interface: astronaut intro -> helmet HUD with 3 priority levels (keys 1/2/3), live warnings (oxygen, point of no return, steep ground ahead, hazards, science of interest).
Regions: Jezero (main) + Bogra, Sripur, Teknaf, Ruhea, Satkania (Bangladesh-named craters, shown on a Mars overview chart).
**Data status: every raster, site, hazard, photo and number in `data/processed` is SYNTHETIC and labelled so until the data team drops real files in (docs/DATA_SOURCES.md).**

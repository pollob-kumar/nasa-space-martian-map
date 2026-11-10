from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import math
import numpy as np

from . import config
from .models import RouteRequest
from .store import get_region, list_region_ids
from .routing.astar import astar
from .routing.costmap import build_cost
from .routing.mission import summarize_path
from .routing.explain import build_explanation, direct_line_check, insights, routed_detours
from . import spaceweather

app = FastAPI(title="RedNav-N399 API", version="0.1.0",
              description="Layered Mars surface data + traversal route planning from NASA data (hackathon prototype).")
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])

LAYER_FILES = {"imagery": "imagery.png", "hillshade": "hillshade.png", "slope": "slope.png", "hazard": "hazard.png", "chemical": "chemical.png"}


def _region_or_404(rid: str):
    try:
        return get_region(rid)
    except KeyError:
        raise HTTPException(404, f"region '{rid}' has no processed data. Run: python data/scripts/run_all.py --region {rid}")


@app.get("/api/health")
def health():
    return {"ok": True, "regions_ready": list_region_ids()}


@app.get("/api/regions")
def regions():
    out = []
    for rid in list_region_ids():
        m = get_region(rid).meta
        out.append({"id": rid, "name": m["name"], "role": m.get("role", "primary"), "center": m["center"],
                    "synthetic": bool(m.get("synthetic")), "bangladesh": m.get("bangladesh"), "coord_status": m.get("coord_status")})
    return out


@app.get("/api/regions/{rid}")
def region_meta(rid: str):
    reg = _region_or_404(rid)
    m = dict(reg.meta)
    cell = reg.grid.cell_m
    warnings = list(m.get("warnings", []))
    if cell > 50:
        warnings.append(f"Elevation grid is {cell:.0f} m/pixel: slope is a coarse indicator; boulders and small hazards are NOT resolved.")
    m["warnings"] = warnings
    m["defaults"] = {"max_slope_deg": config.DEFAULT_MAX_SLOPE_DEG, "caution_slope_deg": config.DEFAULT_CAUTION_SLOPE_DEG,
                     "walk_speed_ms": config.DEFAULT_WALK_SPEED_MS, "load_factor": config.DEFAULT_LOAD_FACTOR,
                     "science_stop_min": config.DEFAULT_SCIENCE_STOP_MIN}
    m["suit_assumptions"] = {"o2_capacity_min": config.SUIT_O2_CAPACITY_MIN, "o2_reserve_pct": config.O2_RESERVE_PCT,
                             "o2_slope_factor_per_deg": config.O2_SLOPE_FACTOR_PER_DEG, "o2_load_weight": config.O2_LOAD_FACTOR_WEIGHT,
                             "o2_stop_factor": config.O2_SCIENCE_STOP_FACTOR}
    m["crs"] = {"coordinates": "planetocentric latitude, longitude degrees EAST (0-360)", "body_radius_m": config.MARS_RADIUS_M,
                "grid": "local equirectangular metre grid, row 0 = north edge; every layer shares this exact grid",
                "alignment": "All raster layers are produced on one grid (same width/height/cell), so they overlay pixel-for-pixel."}
    m["layer_urls"] = {k: f"/api/regions/{rid}/layers/{k}.png" for k, f in LAYER_FILES.items() if (reg.folder / f).exists()}
    m["stats"] = {"elev_min_m": float(np.nanmin(reg.dem)), "elev_max_m": float(np.nanmax(reg.dem)),
                  "slope_max_deg": float(np.nanmax(reg.slope)), "nodata_pct": round(float(np.isnan(reg.dem).mean() * 100), 2)}
    return m


@app.get("/api/regions/{rid}/sites")
def sites(rid: str):
    return _region_or_404(rid).sites


@app.get("/api/regions/{rid}/geology")
def geology(rid: str):
    return _region_or_404(rid).geology


@app.get("/api/space-weather")
def space_weather():
    return spaceweather.get_space_weather()


@app.get("/api/regions/{rid}/hazards")
def hazards(rid: str):
    return _region_or_404(rid).hazards


@app.get("/api/regions/{rid}/layers/{name}.png")
def layer_png(rid: str, name: str):
    reg = _region_or_404(rid)
    fn = LAYER_FILES.get(name)
    if not fn or not (reg.folder / fn).exists():
        raise HTTPException(404, f"layer '{name}' not available for {rid} (shown as MISSING in UI, never faked)")
    return FileResponse(reg.folder / fn, media_type="image/png")


@app.get("/api/regions/{rid}/media/{filename}")
def media(rid: str, filename: str):
    reg = _region_or_404(rid)
    p = (reg.folder / "media" / filename).resolve()
    if reg.folder.resolve() not in p.parents or not p.exists():
        raise HTTPException(404, "media not found")
    return FileResponse(p)


def _params(req: RouteRequest) -> dict:
    max_s = req.max_slope_deg or config.DEFAULT_MAX_SLOPE_DEG
    return {"max_slope_deg": max_s, "caution_slope_deg": min(req.caution_slope_deg or config.DEFAULT_CAUTION_SLOPE_DEG, max_s - 0.1),
            "walk_speed_ms": req.walk_speed_ms or config.DEFAULT_WALK_SPEED_MS,
            "load_factor": req.load_factor or config.DEFAULT_LOAD_FACTOR,
            "science_stop_min": req.science_stop_min if req.science_stop_min is not None else config.DEFAULT_SCIENCE_STOP_MIN}


def _cost(reg, req: RouteRequest, slope_weight: float):
    p = _params(req)
    extra = [o.model_dump() for o in req.obstacles]
    return build_cost(reg.slope, reg.hazard_mask(extra), max_slope=p["max_slope_deg"], caution_slope=p["caution_slope_deg"], slope_weight=slope_weight)


def _route_once(reg, start_rc, goal_rc, req: RouteRequest, slope_weight: float):
    p = _params(req)
    return astar(_cost(reg, req, slope_weight), start_rc, goal_rc), p["max_slope_deg"], p["caution_slope_deg"]


@app.post("/api/route")
def route(req: RouteRequest):
    reg = _region_or_404(req.region_id)
    g = reg.grid
    P = _params(req)
    # resolve targets
    targets = []
    for sid in req.via_site_ids:
        s = next((x for x in reg.sites if x["id"] == sid), None)
        if not s:
            raise HTTPException(400, f"unknown via site {sid}")
        targets.append(s)
    if req.goal_site_id:
        s = next((x for x in reg.sites if x["id"] == req.goal_site_id), None)
        if not s:
            raise HTTPException(400, f"unknown goal site {req.goal_site_id}")
        targets.append(s)
    elif req.goal:
        targets.append({"id": "custom", "name": "Custom goal", "lat": req.goal.lat, "lon": req.goal.lon, "pov_images": []})
    else:
        raise HTTPException(400, "give goal_site_id or goal")
    chain = [g.latlon_to_cell(req.start.lat, req.start.lon)] + [g.latlon_to_cell(t["lat"], t["lon"]) for t in targets]
    for rc in chain:
        if not g.inside(*rc):
            raise HTTPException(400, "start/goal outside this region's grid")

    results = []
    for label, w in (("balanced", 1.0), ("safest", 4.0), ("shortest_feasible", 0.0)):
        full, ok = [], True
        for a, b in zip(chain[:-1], chain[1:]):
            seg, max_s, cau_s = _route_once(reg, a, b, req, w)
            if seg is None:
                ok = False
                break
            full += seg if not full else seg[1:]
        if not ok:
            results.append({"strategy": label, "found": False})
            continue
        summ = summarize_path(full, reg.dem, reg.slope, g, walk_speed_ms=P["walk_speed_ms"], load_factor=P["load_factor"],
                              stop_min=P["science_stop_min"], caution_slope=cau_s, max_slope=max_s, stops=len(targets))
        summ.update({"strategy": label, "found": True})
        results.append(summ)

    # de-duplicate identical alternatives
    uniq, seen = [], set()
    for r in results:
        key = (r.get("distance_m"), r.get("max_slope_deg")) if r["found"] else ("x", r["strategy"])
        if key not in seen:
            seen.add(key)
            uniq.append(r)

    found = [r for r in uniq if r["found"]]
    primary = found[0] if found else None
    goal = targets[-1]
    obstacles = [o.model_dump() for o in req.obstacles]
    hz_mask = reg.hazard_mask(obstacles)

    # NASA 'make connections / apply context': combine slope + target + hazards + oxygen into advice
    direct = direct_line_check(reg, chain[0], chain[-1], hz_mask, P["max_slope_deg"], P["caution_slope_deg"])
    ins = insights(reg, goal, direct, primary, P["max_slope_deg"], P["caution_slope_deg"])

    nearby = []
    if primary:
        base_cost = _cost(reg, req, 1.0)
        skip = {t["id"] for t in targets}
        nearby = routed_detours(reg, primary, chain[0], chain[-1], base_cost, skip, P)
        meta_warn = reg.meta.get("warnings", [])
        for r in found:  # each route carries its own 5-question analysis for the 'Route analysis' window
            r["explanation"] = build_explanation(reg, r, uniq, goal, obstacles, max_slope=P["max_slope_deg"], caution_slope=P["caution_slope_deg"], region_warnings=meta_warn)
            r["explanation"]["insights"] = ins

    warnings = []
    if not found:
        warnings.append("No traversable route under the current slope limit / hazards. Raise the limit, remove obstacles or pick another goal. (We do not draw a line through unknown or blocked terrain.)")
    if reg.grid.cell_m > 50:
        warnings.append(f"DEM is {reg.grid.cell_m:.0f} m/px: 'below the slope limit' here only means below the limit in coarse data. It is not a guarantee of astronaut safety.")
    return {"region_id": req.region_id, "routes": uniq, "nearby_science": nearby, "insights": ins, "direct_line": direct,
            "warnings": warnings, "assumptions": P,
            "disclaimer": "Prototype decision-support. Thresholds are assumptions; not validated for crew safety."}

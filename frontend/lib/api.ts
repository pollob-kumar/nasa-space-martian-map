import type { GeologyFeature, SpaceWeather, Hazard, Obstacle, PlanOptions, RegionMeta, RegionSummary, RouteResponse, Site } from './missionTypes';

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

async function j<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  regions: () => j<RegionSummary[]>('/api/regions'),
  region: (id: string) => j<RegionMeta>(`/api/regions/${id}`),
  sites: (id: string) => j<Site[]>(`/api/regions/${id}/sites`),
  hazards: (id: string) => j<Hazard[]>(`/api/regions/${id}/hazards`),
  geology: (id: string) => j<GeologyFeature[]>(`/api/regions/${id}/geology`),
  spaceWeather: () => j<SpaceWeather>('/api/space-weather'),
  route: (body: {
    region_id: string;
    start: { lat: number; lon: number };
    goal_site_id: string;
    obstacles: Obstacle[];
  } & Partial<PlanOptions>) =>
    j<RouteResponse>('/api/route', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...body, obstacles: body.obstacles.map((o) => ({ ...o, name: o.name ?? 'user obstacle' })) }),
    }),
  assetUrl: (path: string) => (path.startsWith('http') ? path : `${API_BASE}${path}`),
};

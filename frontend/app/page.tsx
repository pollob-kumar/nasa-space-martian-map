"use client";

import { useEffect, useState } from "react";
import MarsHudLoader from "../components/MarsHudLoader";
import { api, API_BASE } from "../lib/api";
import type { RegionSummary } from "../lib/missionTypes";
import { MarsOverviewMap } from "../components/MarsOverviewMap";

const ROLE_LABEL: Record<string, string> = { primary: "MAIN REGION", bangladesh: "BANGLADESH-NAMED CRATER", demo: "SYNTHETIC DEMO" };

export default function Home() {
  const [regions, setRegions] = useState<RegionSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [picked, setPicked] = useState<string | null>(null);
  const [started, setStarted] = useState(false);

  useEffect(() => {
    api.regions().then((r0) => { const order: Record<string, number> = { primary: 0, bangladesh: 1 }; const r = [...r0].sort((a, b) => (order[a.role] ?? 2) - (order[b.role] ?? 2)); setRegions(r); setPicked(r.find((x) => x.role === "primary")?.id ?? r[0]?.id ?? null); }).catch((e) => setError(String(e.message ?? e)));
  }, []);

  if (started && picked) return <MarsHudLoader regionId={picked} />;

  return (
    <main className="relative flex h-screen w-full flex-col items-center overflow-y-auto bg-[#060408] text-white py-8">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[550px] h-[550px] bg-red-600/15 rounded-full blur-[130px] pointer-events-none" />
      <div className="absolute inset-0 opacity-15 pointer-events-none" style={{ backgroundImage: "linear-gradient(to right, #ffffff10 1px, transparent 1px), linear-gradient(to bottom, #ffffff10 1px, transparent 1px)", backgroundSize: "40px 40px" }} />

      <div className="relative z-10 flex flex-col items-center text-center px-6 max-w-3xl w-full my-auto">
        <div className="inline-flex items-center gap-2 px-3 py-1 mb-6 rounded-full border border-red-500/30 bg-red-950/40 text-red-400 font-mono text-xs tracking-widest uppercase">
          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          NASA Space Apps 2026 · Martian Map
        </div>
        <h1 className="text-5xl md:text-7xl font-black tracking-widest uppercase text-transparent bg-clip-text bg-gradient-to-b from-white via-slate-200 to-red-500 drop-shadow-[0_0_35px_rgba(239,68,68,0.5)]" style={{ fontFamily: "'Orbitron', sans-serif" }}>
          RedNav-N399
        </h1>
        <p className="mt-4 text-sm md:text-base text-slate-400 font-mono tracking-wider uppercase">Layered NASA-data map &amp; Marswalk route planner</p>
        <div className="w-32 h-[2px] bg-gradient-to-r from-transparent via-red-500 to-transparent my-6" />

        <section className="w-full text-left" aria-label="Choose a region">
          <h2 className="font-mono text-[11px] tracking-widest text-white/50 mb-2">1 · CHOOSE A REGION</h2>
          {!regions && !error && <div className="font-mono text-xs text-slate-400">Connecting to data server…</div>}
          {error && (
            <div className="rounded border border-red-500/40 bg-red-950/30 p-3 text-xs font-mono text-red-200 space-y-1">
              <div>Data server not reachable at {API_BASE}</div>
              <div className="text-red-300/70">Start it: <code>cd backend &amp;&amp; uvicorn app.main:app --port 8000</code> · then reload. ({error})</div>
            </div>
          )}
          {regions && regions.length === 0 && <div className="font-mono text-xs text-amber-200">No processed regions yet. Run: <code>python data/scripts/run_all.py --demo</code></div>}
          <div className="grid gap-2 sm:grid-cols-2">
            {regions?.map((r) => (
              <button key={r.id} onClick={() => setPicked(r.id)} className={`text-left rounded-lg border px-3 py-2.5 transition ${picked === r.id ? "border-red-400 bg-red-950/40" : "border-white/10 bg-slate-950/50 hover:border-white/30"}`}>
                <div className="text-[9px] font-mono tracking-widest text-red-300/80">{ROLE_LABEL[r.role] ?? r.role}</div>
                <div className="text-sm font-semibold">{r.name}</div>
              </button>
            ))}
          </div>
        </section>

        {regions && regions.length > 0 && (
          <section className="w-full text-left mt-5" aria-label="Where the regions are on Mars">
            <h2 className="font-mono text-[11px] tracking-widest text-white/50 mb-2">WHERE ON MARS · BANGLADESH-NAMED CRATERS</h2>
            <MarsOverviewMap regions={regions} activeId={picked} onPick={setPicked} />
          </section>
        )}

        <button onClick={() => setStarted(true)} disabled={!picked}
          className="mt-8 group relative px-10 py-4 font-mono text-sm tracking-widest uppercase font-bold text-white transition-all duration-300 rounded border border-red-500/60 bg-red-950/30 hover:bg-red-600 hover:text-black hover:shadow-[0_0_30px_rgba(239,68,68,0.7)] active:scale-95 disabled:opacity-40 cursor-pointer">
          START EXPEDITION <span className="inline-block transition-transform group-hover:translate-x-1">→</span>
        </button>
        <p className="mt-6 text-[10px] font-mono text-slate-500 tracking-wider max-w-lg">Prototype decision-support. Routes use the elevation data of the chosen region and team-set limits; not validated for crew safety.</p>
      </div>
    </main>
  );
}

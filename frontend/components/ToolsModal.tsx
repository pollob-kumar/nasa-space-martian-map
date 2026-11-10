import React from 'react';
import { X, Sun, Volume2, VolumeX } from 'lucide-react';
import { VisorTint } from '../types';
import { hudSound } from '../utils/soundEffects';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  visorTint: VisorTint;
  onChangeVisorTint: (tint: VisorTint) => void;
  soundEnabled: boolean;
  onToggleSound: () => void;
}

const TINTS: { id: VisorTint; label: string }[] = [
  { id: 'clear', label: 'Clear' },
  { id: 'gold-polar', label: 'Gold' },
  { id: 'thermal-lidar', label: 'Violet' },
  { id: 'night-nv', label: 'Night' },
];

export const ToolsModal: React.FC<Props> = ({ isOpen, onClose, visorTint, onChangeVisorTint, soundEnabled, onToggleSound }) => {
  if (!isOpen) return null;
  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm" role="dialog" aria-label="Display settings">
      <div className="w-[420px] max-w-[92vw] rounded-2xl border border-white/15 bg-slate-950/90 p-5 space-y-5 cursor-default">
        <div className="flex items-center justify-between">
          <h2 className="font-mono text-sm font-bold tracking-widest">DISPLAY SETTINGS</h2>
          <button onClick={onClose} className="p-1.5 rounded-full border border-white/15" aria-label="Close"><X className="w-4 h-4" /></button>
        </div>
        <div>
          <div className="flex items-center gap-2 text-[11px] font-mono text-white/55 mb-2"><Sun className="w-3.5 h-3.5" />VISOR TINT</div>
          <div className="grid grid-cols-4 gap-2">
            {TINTS.map((t) => (
              <button key={t.id} onClick={() => { hudSound.playClick(); onChangeVisorTint(t.id); }} className={`py-2 rounded border text-xs font-mono ${visorTint === t.id ? 'border-cyan-400 bg-cyan-500/20' : 'border-white/15'}`}>{t.label}</button>
            ))}
          </div>
        </div>
        <button onClick={onToggleSound} className="w-full flex items-center justify-between rounded border border-white/15 px-3 py-2 text-xs font-mono">
          <span className="flex items-center gap-2">{soundEnabled ? <Volume2 className="w-4 h-4 text-cyan-300" /> : <VolumeX className="w-4 h-4" />}Ambient sound</span>
          <span>{soundEnabled ? 'ON' : 'OFF'}</span>
        </button>
        <div className="text-[11px] text-white/50 leading-relaxed space-y-1">
          <p><b className="text-white/70">Keys:</b> Space = walk · Arrows/WASD = look · M = map · Esc = back to HUD</p>
          <p>The 3D ground behind the HUD is a generic visual texture. Terrain numbers (elevation, slope) come from the planner data, not from this picture.</p>
        </div>
      </div>
    </div>
  );
};

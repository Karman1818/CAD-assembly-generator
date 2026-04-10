'use client'

import React, { useState } from 'react';
import { UploadForm } from '@/components/upload/UploadForm';
import { MainScene } from '@/components/3d/MainScene';

export default function Home() {
  const [cadUrl, setModelUrl] = useState<string | null>(null);
  const [explosion, setExplosion] = useState(0);

  return (
    <main className="h-screen w-screen relative overflow-hidden">
      {/* 3D Background - always interactive */}
      <div className="absolute inset-0 z-0">
        <MainScene modelUrl={cadUrl} explosion={explosion} />
      </div>

      {/* UI Overlay - sits above 3D */}
      <div className="absolute inset-0 z-10 pointer-events-none flex flex-col items-center justify-center">
        {!cadUrl && (
          <div className="w-full px-4 pointer-events-auto">
            <UploadForm onModelReady={(url) => setModelUrl(url)} />
          </div>
        )}
        
        {cadUrl && (
          <div className="absolute top-10 left-10 flex flex-col gap-3 pointer-events-auto max-w-xs">
            
            <div className="p-5 bg-zinc-900/40 rounded-2xl border border-zinc-800/50 backdrop-blur-xl shadow-2xl flex flex-col gap-4">
              <div className="flex items-center justify-between pointer-events-auto">
                <div className="flex items-center gap-2 text-indigo-400 opacity-80">
                  <span className="flex w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                  <span className="text-xs tracking-wider uppercase font-semibold">Live Mode</span>
                </div>
                <button 
                  onClick={() => { setModelUrl(null); setExplosion(0); }}
                  className="px-3 py-1.5 bg-zinc-800/50 hover:bg-zinc-700/80 border border-zinc-700/50 rounded-lg text-xs font-medium text-zinc-300 hover:text-white transition-all shadow-sm"
                >
                  Close Model
                </button>
              </div>

              <div className="w-full h-px bg-zinc-800/60" />

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm text-zinc-200 font-medium tracking-wide">Assembly Parts Spacing</label>
                  <span className="text-xs text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded-md font-mono">{explosion.toFixed(2)}x</span>
                </div>
                <input 
                  type="range" min="0" max="1" step="0.01" value={explosion}
                  onChange={(e) => setExplosion(parseFloat(e.target.value))}
                  className="w-full h-2 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-blue-500 shadow-inner"
                />
              </div>

              <div className="p-3 bg-zinc-950/50 rounded-xl border border-zinc-800/30 text-xs text-zinc-400 font-light leading-relaxed">
                <span className="block text-zinc-300 font-medium mb-1">Controls</span>
                <span className="text-blue-400">Left Click</span> to rotate, <span className="text-blue-400">Right Click</span> to pan, and <span className="text-blue-400">Scroll</span> to zoom.
              </div>
            </div>

          </div>
        )}
      </div>
    </main>
  );
}

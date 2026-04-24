'use client'

import React, { useState } from 'react';
import { UploadForm } from '@/components/upload/UploadForm';
import { MainScene } from '@/components/3d/MainScene';
import { PartsList } from '@/components/3d/PartsList';
import { AssemblyInstructions } from '@/components/3d/AssemblyInstructions';
import { PrintableInstructions } from '@/components/3d/PrintableInstructions';
import { FileText, Wand2, Loader2 } from 'lucide-react';
import { API_BASE_URL, generateAssemblyInstructions } from '@/lib/api';

interface AssemblyPartRef {
  part_id: string;
  quantity_in_step: number;
  svgUrl?: string;
  type?: 'panel' | 'connector' | 'other';
  dimensions?: number[];
  label?: string;
}

interface AssemblyStep {
  step_number: number;
  title: string;
  description: string;
  parts_used: AssemblyPartRef[];
  sceneSvgUrl?: string;
  scenePngUrl?: string;
}

interface AssemblyData {
  title: string;
  steps: AssemblyStep[];
  pdfUrl?: string;
  overviewSvgUrl?: string;
  overviewPngUrl?: string;
  generationMode?: string;
  generationWarning?: string;
  parts_list?: Array<{
    id: string;
    label?: string;
    type: string;
    quantity: number;
    dimensions: number[];
    svgUrl?: string | null;
  }>;
}

export default function Home() {
  const [cadJobId, setCadJobId] = useState<string | null>(null);
  const [explosion, setExplosion] = useState(0);
  const [isGenerating, setIsGenerating] = useState(false);
  const [assemblyData, setAssemblyData] = useState<AssemblyData | null>(null);
  const [showInstructions, setShowInstructions] = useState(false);

  const modelUrl = cadJobId ? `${API_BASE_URL}/api/files/${cadJobId}.glb` : null;

  const handleGenerateInstructions = async () => {
    if (!cadJobId) return;
    setIsGenerating(true);
    try {
      const data = await generateAssemblyInstructions(cadJobId);
      setAssemblyData(data);
      setShowInstructions(true);
    } catch (e) {
      console.error(e);
      const message = e instanceof Error ? e.message : 'Nie udało się wygenerować instrukcji.';
      alert(`Błąd: ${message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownloadPdf = () => {
    if (!assemblyData?.pdfUrl) {
      window.print();
      return;
    }
    window.open(`${API_BASE_URL}${assemblyData.pdfUrl}`, '_blank', 'noopener,noreferrer');
  };

  return (
    <main className="h-screen w-screen relative overflow-hidden flex flex-col">
      {/* 3D Background - always interactive */}
      <div className="absolute inset-0 z-0">
        <MainScene modelUrl={modelUrl} explosion={explosion} />
      </div>

      {/* UI Overlay - sits above 3D */}
      <div className="relative z-10 flex items-center justify-center h-full pointer-events-none">
        
        {!cadJobId && (
          <div className="w-full px-4 pointer-events-auto">
            <UploadForm onModelReady={(jobId) => setCadJobId(jobId)} />
          </div>
        )}
        
        {cadJobId && (
          <div className="absolute top-10 left-10 flex flex-col gap-3 pointer-events-auto max-w-xs">
            
            <div className="p-5 bg-zinc-900/40 rounded-2xl border border-zinc-800/50 backdrop-blur-xl shadow-2xl flex flex-col gap-4">
              <div className="flex items-center justify-between pointer-events-auto">
                <div className="flex items-center gap-2 text-indigo-400 opacity-80">
                  <span className="flex w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                  <span className="text-xs tracking-wider uppercase font-semibold">Live Mode</span>
                </div>
                <button 
                  onClick={() => { setCadJobId(null); setExplosion(0); setAssemblyData(null); }}
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

              <div className="w-full h-px bg-zinc-800/60" />

              <div className="flex flex-col gap-2">
                <button 
                  onClick={handleGenerateInstructions}
                  disabled={isGenerating}
                  className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-zinc-800 disabled:text-zinc-500 rounded-xl text-white text-sm font-medium transition-all shadow-[0_0_20px_rgba(79,70,229,0.3)] flex items-center justify-center gap-2 group"
                >
                  {isGenerating ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Wand2 className="w-4 h-4 group-hover:rotate-12 transition-transform" />
                  )}
                  {isGenerating ? 'Generowanie...' : 'Generuj AI Instrukcję'}
                </button>

                {assemblyData && (
                  <button 
                    onClick={() => setShowInstructions(true)}
                    className="w-full py-3 bg-zinc-800 hover:bg-zinc-700 rounded-xl text-white text-sm font-medium transition-all border border-zinc-700/50 flex items-center justify-center gap-2"
                  >
                    <FileText className="w-4 h-4" />
                    Pokaż Instrukcję
                  </button>
                )}
              </div>

              <div className="p-3 bg-zinc-950/50 rounded-xl border border-zinc-800/30 text-xs text-zinc-400 font-light leading-relaxed">
                <span className="block text-zinc-300 font-medium mb-1">Controls</span>
                <span className="text-blue-400">Left Click</span> to rotate, <span className="text-blue-400">Right Click</span> to pan, and <span className="text-blue-400">Scroll</span> to zoom.
              </div>
            </div>

          </div>
        )}
        
        {cadJobId && (
          <PartsList jobId={cadJobId} />
        )}

        {showInstructions && assemblyData && (
          <AssemblyInstructions 
            data={assemblyData} 
            onClose={() => setShowInstructions(false)} 
            onDownloadPdf={handleDownloadPdf}
          />
        )}

        <PrintableInstructions data={assemblyData} />
      </div>
    </main>
  );
}

'use client'

import React from 'react';
import { API_BASE_URL } from '@/lib/api';

interface PartRef {
  part_id: string;
  quantity_in_step: number;
  svgUrl?: string;
}

interface AssemblyStep {
  step_number: number;
  title: string;
  description: string;
  parts_used: PartRef[];
  scenePngUrl?: string;
  sceneSvgUrl?: string;
}

interface AssemblyData {
  title: string;
  steps: AssemblyStep[];
  parts_list?: Array<{
    id: string;
    quantity: number;
    dimensions?: number[];
    svgUrl?: string | null;
  }>;
  overviewPngUrl?: string;
}

export function PrintableInstructions({ data }: { data: AssemblyData | null }) {
  if (!data) return null;

  return (
    <div className="hidden print:block print:bg-white min-h-screen text-black p-0 m-0">
      <style dangerouslySetInnerHTML={{ __html: `
        @media print {
          @page { size: A4; margin: 20mm; }
          body { background: white; }
          .no-print { display: none !important; }
        }
      `}} />

      {/* Cover Page */}
      <div className="h-[297mm] flex flex-col items-center justify-center border-b-2 border-black p-12 mb-12 page-break-after-always">
        <h1 className="text-6xl font-black uppercase tracking-tighter mb-4 text-center">{data.title}</h1>
        <div className="w-64 h-2 bg-black mb-12" />
        <div className="text-2xl font-light text-center mb-24 uppercase tracking-widest opacity-60">Instrukcja montażu IKEA Style</div>
        
        {/* Simple visual of the product - using the first part as a placeholder if no main visual exists */}
        <div className="w-full flex justify-center py-20">
           {data.overviewPngUrl ? (
            <img
              src={`${API_BASE_URL}${data.overviewPngUrl}`}
              alt="Assembly overview"
              className="max-h-[420px] object-contain"
            />
           ) : (
            <div className="text-zinc-300 transform scale-[3] opacity-5">
              CAD GENERATOR
            </div>
           )}
        </div>
        
        <div className="mt-auto text-sm font-mono uppercase tracking-widest text-zinc-500">
          Generated automatically from CAD metadata
        </div>
      </div>

      {/* BOM Page */}
      <div className="min-h-[297mm] p-12 border-b border-zinc-200 mb-12">
        <h2 className="text-3xl font-bold mb-10 uppercase">Wykaz części</h2>
        <div className="grid grid-cols-2 gap-8">
          {data.parts_list?.map((part, idx) => (
            <div key={idx} className="flex items-center gap-6 border-b border-zinc-100 pb-4">
               <div className="w-32 h-32 flex items-center justify-center border border-zinc-200 p-2">
                 {part.svgUrl && <img src={`${API_BASE_URL}${part.svgUrl}`} className="max-w-full max-h-full" alt="" />}
               </div>
               <div>
                 <div className="text-xs font-bold uppercase tracking-widest text-zinc-500">{part.id}</div>
                 <div className="text-3xl font-black">×{part.quantity}</div>
                 <div className="text-[10px] text-zinc-400 mt-2 font-mono">
                   {part.dimensions?.[0]?.toFixed(1)} x {part.dimensions?.[1]?.toFixed(1)} x {part.dimensions?.[2]?.toFixed(1)} mm
                 </div>
               </div>
            </div>
          ))}
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-0">
        {data.steps.map((step, idx) => (
          <div key={idx} className="min-h-[297mm] h-[297mm] p-12 flex flex-col border-b border-black/5 last:border-0 relative page-break-after-always">
            <div className="flex items-start justify-between border-b-2 border-black pb-6 mb-12">
               <div>
                  <h3 className="text-4xl font-black uppercase leading-none">{step.title}</h3>
                  <div className="text-zinc-500 text-sm font-medium mt-2">Krok {step.step_number} z {data.steps.length}</div>
               </div>
               <div className="text-6xl font-black bg-black text-white w-20 h-20 flex items-center justify-center">
                 {step.step_number}
               </div>
            </div>

            <div className="flex-1 flex flex-col">
              <div className="flex-1 flex items-center justify-center p-10">
                {step.scenePngUrl ? (
                  <img src={`${API_BASE_URL}${step.scenePngUrl}`} className="max-h-[720px] object-contain" alt="" />
                ) : (
                  <div className="grid grid-cols-2 gap-20 w-full max-w-2xl">
                    {step.parts_used.map((p, pidx) => (
                      <div key={pidx} className="flex flex-col items-center">
                        {p.svgUrl && <img src={`${API_BASE_URL}${p.svgUrl}`} className="max-h-[200px] object-contain" alt="" />}
                        <div className="mt-6 flex items-center gap-3">
                          <span className="text-xs font-bold bg-zinc-100 px-3 py-1 border border-zinc-300 uppercase">{p.part_id}</span>
                          <span className="text-2xl font-black">×{p.quantity_in_step}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="mt-auto pt-10 border-t-2 border-black/10">
                 <p className="text-2xl font-light leading-relaxed max-w-3xl">
                   {step.description}
                 </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

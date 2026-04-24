'use client'

import React, { useState } from 'react';
import { 
  X, 
  ChevronLeft, 
  ChevronRight, 
  BookOpen, 
  Download, 
  CheckCircle2,
  Package,
  Image as ImageIcon,
  AlertTriangle
} from 'lucide-react';
import { API_BASE_URL } from '@/lib/api';

interface PartRef {
  part_id: string;
  quantity_in_step: number;
  svgUrl?: string;
  type?: 'panel' | 'connector' | 'other';
  dimensions?: number[];
}

interface AssemblyStep {
  step_number: number;
  title: string;
  description: string;
  parts_used: PartRef[];
  sceneSvgUrl?: string;
  scenePngUrl?: string;
}

interface AssemblyData {
  title: string;
  steps: AssemblyStep[];
  pdfUrl?: string;
  overviewSvgUrl?: string;
  generationMode?: string;
  generationWarning?: string;
}

export function AssemblyInstructions({ 
  data, 
  onClose,
  onDownloadPdf
}: { 
  data: AssemblyData; 
  onClose: () => void;
  onDownloadPdf: () => void;
}) {
  const [currentStep, setCurrentStep] = useState(0);
  const steps = data.steps;
  const isLastStep = currentStep === steps.length - 1;

  const nextStep = () => {
    if (currentStep < steps.length - 1) setCurrentStep(currentStep + 1);
  };

  const prevStep = () => {
    if (currentStep > 0) setCurrentStep(currentStep - 1);
  };

  const step = steps[currentStep];

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-8 bg-black/60 backdrop-blur-sm animate-in fade-in duration-300 pointer-events-auto">
      <div className="bg-zinc-950 w-full max-w-5xl h-full max-h-[850px] rounded-[2.5rem] border border-zinc-800 shadow-2xl flex flex-col overflow-hidden relative pointer-events-auto">
        
        {/* Header */}
        <div className="p-6 md:p-8 border-b border-zinc-800 flex items-center justify-between bg-zinc-900/40 backdrop-blur-md">
          <div className="flex items-center gap-4">
            <div className="bg-indigo-500/10 p-3 rounded-2xl border border-indigo-500/20">
              <BookOpen className="w-6 h-6 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-xl md:text-2xl font-light tracking-tight text-white">{data.title}</h2>
              <p className="text-zinc-500 text-xs md:text-sm font-light">Krok {currentStep + 1} z {steps.length}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <button 
              onClick={onDownloadPdf}
              className="p-3 bg-zinc-800/50 hover:bg-zinc-700/80 border border-zinc-700/50 rounded-2xl text-zinc-300 hover:text-white transition-all shadow-sm flex items-center gap-2 px-5 group"
            >
              <Download className="w-4 h-4 group-hover:scale-110 transition-transform" />
              <span className="text-sm font-medium">Pobierz PDF</span>
            </button>
            <button 
              onClick={onClose}
              className="p-3 bg-zinc-800/50 hover:bg-zinc-700/80 border border-zinc-700/50 rounded-2xl text-zinc-300 hover:text-white transition-all shadow-sm"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {(data.generationMode || data.generationWarning) && (
          <div className="px-6 md:px-8 py-3 border-b border-zinc-900 bg-zinc-950/90 flex flex-wrap items-center gap-3 text-xs">
            {data.generationMode && (
              <span className="px-3 py-1 rounded-full border border-zinc-800 bg-zinc-900 text-zinc-300 uppercase tracking-widest">
                {data.generationMode === 'ai' ? 'AI planned' : 'Heuristic fallback'}
              </span>
            )}
            {data.generationWarning && (
              <span className="flex items-center gap-2 text-amber-300">
                <AlertTriangle className="w-4 h-4" />
                {data.generationWarning}
              </span>
            )}
          </div>
        )}

        {/* Content Section */}
        <div className="flex-1 overflow-y-auto flex flex-col md:flex-row p-6 md:p-10 gap-8 md:gap-12">
          
          {/* Main Drawing Area */}
          <div className="flex-[1.5] flex flex-col gap-6">
            <div className="bg-white rounded-[2rem] p-8 aspect-video flex items-center justify-center shadow-inner relative overflow-hidden group">
               <div className="absolute inset-0 bg-neutral-100/50 pointer-events-none" />
               <div className="relative w-full h-full flex items-center justify-center">
                 {step.sceneSvgUrl ? (
                  <img
                    src={`${API_BASE_URL}${step.sceneSvgUrl}`}
                    alt={`Assembly step ${step.step_number}`}
                    className="w-full h-full object-contain opacity-95"
                  />
                 ) : data.overviewSvgUrl ? (
                  <img
                    src={`${API_BASE_URL}${data.overviewSvgUrl}`}
                    alt="Assembly overview"
                    className="w-full h-full object-contain opacity-95"
                  />
                 ) : (
                  <div className="flex flex-col items-center gap-3 text-zinc-400">
                    <ImageIcon className="w-16 h-16" />
                    <span>No generated step illustration</span>
                  </div>
                 )}
               </div>
               
               {/* Step label */}
               <div className="absolute bottom-6 left-6 bg-zinc-900 text-white w-12 h-12 rounded-full flex items-center justify-center text-xl font-bold border-4 border-white shadow-xl">
                 {currentStep + 1}
               </div>
            </div>
            
            <div className="p-2">
              <h3 className="text-2xl font-light text-white mb-3 tracking-tight">{step.title}</h3>
              <p className="text-zinc-400 text-lg font-light leading-relaxed">
                {step.description}
              </p>
            </div>
          </div>

          {/* Sidebar: Parts used in this step */}
          <div className="flex-1 max-w-sm">
            <div className="bg-zinc-900/40 border border-zinc-800/60 rounded-3xl p-6 h-full backdrop-blur-md">
              <h4 className="text-zinc-300 font-medium mb-6 flex items-center gap-2 uppercase tracking-widest text-xs opacity-70">
                <Package className="w-4 h-4" />
                Części do tego kroku
              </h4>
              <div className="space-y-4">
                {step.parts_used.map((p, idx) => (
                  <div key={idx} className="bg-zinc-950/50 border border-zinc-800 rounded-2xl p-4 flex items-center gap-4 group hover:border-zinc-700 transition-colors">
                    <div className="bg-white p-2 rounded-xl w-16 h-16 flex items-center justify-center border border-zinc-800/20">
                      {p.svgUrl ? (
                        <img src={`${API_BASE_URL}${p.svgUrl}`} alt="" className="w-full h-full object-contain" />
                      ) : (
                        <Package className="w-6 h-6 text-zinc-300" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-zinc-400 text-[10px] font-bold uppercase tracking-widest">{p.part_id}</p>
                      <p className="text-white text-lg font-mono font-bold leading-none mt-1">×{p.quantity_in_step}</p>
                      {p.dimensions && (
                        <p className="text-zinc-500 text-xs mt-2 truncate">
                          {p.dimensions.map((value) => value.toFixed(1)).join(' × ')} mm
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Footer Navigation */}
        <div className="p-8 border-t border-zinc-900/50 bg-zinc-950 flex items-center justify-between">
          <button 
            onClick={prevStep}
            disabled={currentStep === 0}
            className={`flex items-center gap-2 px-6 py-4 rounded-2xl border transition-all ${
              currentStep === 0 
              ? 'border-zinc-900 text-zinc-600 opacity-50' 
              : 'border-zinc-800 text-zinc-300 hover:text-white hover:bg-zinc-900/50'
            }`}
          >
            <ChevronLeft className="w-5 h-5" />
            <span className="font-medium">Poprzedni</span>
          </button>

          <div className="hidden md:flex items-center gap-2">
            {steps.map((_, idx) => (
              <div 
                key={idx}
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  idx === currentStep ? 'w-8 bg-blue-500' : 'w-2 bg-zinc-800'
                }`}
              />
            ))}
          </div>

          {!isLastStep ? (
            <button 
              onClick={nextStep}
              className="flex items-center gap-2 px-10 py-4 bg-blue-600 hover:bg-blue-500 rounded-2xl text-white font-medium transition-all shadow-[0_0_20px_rgba(37,99,235,0.2)]"
            >
              <span>Następny</span>
              <ChevronRight className="w-5 h-5" />
            </button>
          ) : (
            <button 
              onClick={onClose}
              className="flex items-center gap-2 px-10 py-4 bg-green-600 hover:bg-green-500 rounded-2xl text-white font-medium transition-all shadow-[0_0_20px_rgba(22,163,74,0.2)]"
            >
              <span>Gotowe!</span>
              <CheckCircle2 className="w-5 h-5" />
            </button>
          )}
        </div>

      </div>
    </div>
  );
}

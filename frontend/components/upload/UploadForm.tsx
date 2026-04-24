'use client'

import React, { useState } from 'react';
import { uploadStepFile } from '@/lib/api';
import { ProgressBar } from './ProgressBar';
import { UploadCloud, FileType2 } from 'lucide-react';

export function UploadForm({ onModelReady }: { onModelReady: (jobId: string) => void }) {
  const [jobId, setJobId] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      const response = await uploadStepFile(file);
      setJobId(response.job_id);
    } catch (error) {
      console.error(error);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center p-10 bg-zinc-950/60 backdrop-blur-2xl text-white border border-zinc-800/80 rounded-[2rem] w-full max-w-2xl mx-auto shadow-[0_0_100px_rgba(59,130,246,0.1)] transition-all duration-500 ease-out border-b-zinc-800 border-r-zinc-800 border-t-zinc-700/50 border-l-zinc-700/50 relative overflow-hidden">
      
      {/* Decorative gradients */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-[100px] -z-10 pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-[100px] -z-10 pointer-events-none" />

      <div className="mb-8 flex items-center justify-center bg-zinc-900/50 p-4 rounded-3xl shadow-inner border border-zinc-800/50 mt-2">
         <FileType2 className="w-10 h-10 text-blue-400 opacity-80" />
      </div>

      <h2 className="text-3xl font-light mb-2 tracking-tight">Upload CAD Model</h2>
      <p className="text-zinc-400 mb-8 max-w-sm text-center text-sm font-light leading-relaxed">
        Upload a STEP file to generate high-fidelity technical blueprints and a 3D isometric view.
      </p>
      
      {!jobId && (
        <label className="group relative border-2 border-dashed border-zinc-700/80 hover:border-blue-500/60 hover:bg-zinc-900/40 transition-all duration-300 p-12 rounded-[1.5rem] text-center w-full max-w-md cursor-pointer flex flex-col items-center justify-center gap-4 hover:shadow-[0_0_30px_rgba(59,130,246,0.05)]">
          <input 
            type="file" 
            accept=".step,.stp" 
            onChange={handleFileChange}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            disabled={isUploading}
          />
          <div className="bg-zinc-800/50 p-4 rounded-full group-hover:scale-110 transition-transform duration-300 group-hover:bg-blue-500/20">
            <UploadCloud className="w-8 h-8 text-zinc-400 group-hover:text-blue-400 transition-colors" />
          </div>
          <div className="text-zinc-300 font-medium">
            {isUploading ? "Uploading & Handshaking..." : "Click or drag your .STEP file here"}
          </div>
          <div className="text-zinc-500 text-xs">Maximum file size: 50MB</div>
        </label>
      )}

      {jobId && (
        <div className="w-full mt-4 animation-fade-in">
          <ProgressBar jobId={jobId} onComplete={onModelReady} />
        </div>
      )}
    </div>
  );
}

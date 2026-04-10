'use client'

import React, { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';

export function ProgressBar({ jobId, onComplete }: { jobId: string, onComplete: (url: string) => void }) {
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('Initializing CAD Pipeline...');

  useEffect(() => {
    if (!jobId) return;

    const eventSource = new EventSource(`http://localhost:8000/api/step/progress/${jobId}/stream`);

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setProgress(data.progress);
      setMessage(data.message);

      if (data.status === 'completed') {
        eventSource.close();
        if (data.result_model_url) {
          // Add a short delay for animation completion to show "100%" smoothly
          setTimeout(() => {
             onComplete(`http://localhost:8000${data.result_model_url}`);
          }, 800);
        }
      } else if (data.status === 'error' || data.status === 'failed') {
        eventSource.close();
      }
    };

    return () => {
      eventSource.close();
    };
  }, [jobId, onComplete]);

  return (
    <div className="w-full max-w-md mx-auto p-6 bg-zinc-900/50 rounded-2xl shadow-inner border border-zinc-800/80 backdrop-blur-md">
      <div className="flex items-center justify-between text-sm text-zinc-300 mb-4 font-medium tracking-wide">
        <div className="flex items-center gap-3">
          <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
          <span className="animate-pulse">{message}</span>
        </div>
        <span className="text-blue-400 font-bold">{progress}%</span>
      </div>
      
      <div className="w-full bg-zinc-950/80 rounded-full h-2 shadow-inner overflow-hidden border border-zinc-800/60 p-[1px]">
        <div 
          className="bg-gradient-to-r from-blue-600 via-indigo-500 to-blue-400 h-full rounded-full transition-all duration-[800ms] ease-out shadow-[0_0_10px_rgba(59,130,246,0.8)]" 
          style={{ width: `${progress}%` }}
        ></div>
      </div>
    </div>
  );
}

'use client'

import React, { useEffect, useState, useRef } from 'react';
import { Layers, Wrench, Box, ChevronLeft, ChevronRight, ChevronDown, ChevronUp } from 'lucide-react';
import { API_BASE_URL } from '@/lib/api';

interface PartMetadata {
    id: string;
    label?: string;
    type: string;
    quantity: number;
    dimensions: number[];
    svgUrl: string | null;
}

export function PartsList({ jobId }: { jobId: string }) {
    const [parts, setParts] = useState<PartMetadata[]>([]);
    const [loading, setLoading] = useState(true);
    const [isOpen, setIsOpen] = useState(true);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!jobId) return;

        const fetchParts = async () => {
            try {
                await new Promise(r => setTimeout(r, 500));
                
                const response = await fetch(`${API_BASE_URL}/api/files/${jobId}_parts.json`);
                if (response.ok) {
                    const data = await response.json();
                    setParts(data);
                }
            } catch (err) {
                console.error("Failed to fetch parts metadata", err);
            } finally {
                setLoading(false);
            }
        };

        fetchParts();
    }, [jobId]);

    const getTypeDetails = (type: string) => {
        switch (type) {
            case 'panel': return { label: 'Panel', icon: Layers, color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/20' };
            case 'connector': return { label: 'Łącznik', icon: Wrench, color: 'text-sky-400', bg: 'bg-sky-500/10', border: 'border-sky-500/20' };
            default: return { label: 'Other', icon: Box, color: 'text-zinc-400', bg: 'bg-zinc-800/50', border: 'border-zinc-700/50' };
        }
    };

    const scroll = (direction: 'left' | 'right') => {
        if (scrollRef.current) {
            const scrollAmount = 300;
            scrollRef.current.scrollBy({ left: direction === 'left' ? -scrollAmount : scrollAmount, behavior: 'smooth' });
        }
    };

    if (loading) return null;
    if (parts.length === 0) return null;

    return (
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 w-full max-w-6xl pointer-events-auto px-8 z-20">
            <div className={`bg-zinc-950/70 backdrop-blur-2xl border border-zinc-800/80 rounded-[2rem] p-5 shadow-2xl overflow-hidden transition-all duration-500 ${isOpen ? '' : 'translate-y-2'}`}>
                <div className="flex items-center justify-between mb-2 px-2 cursor-pointer group" onClick={() => setIsOpen(!isOpen)}>
                    <h3 className="text-zinc-200 font-medium text-lg flex items-center gap-2 tracking-tight group-hover:text-white transition-colors">
                        <Box className="w-5 h-5 text-indigo-400" />
                        Zestawienie Części (BOM)
                    </h3>
                    <div className="flex items-center gap-4">
                        <div className="text-zinc-500 text-sm font-light bg-zinc-900/50 px-3 py-1 rounded-full border border-zinc-800 hidden sm:block">
                            {parts.length} unique parts ({parts.reduce((a, b) => a + b.quantity, 0)} total)
                        </div>
                        <button className="text-zinc-400 hover:text-white transition-colors bg-zinc-800/50 p-1.5 rounded-full border border-zinc-700/50">
                            {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
                        </button>
                    </div>
                </div>

                <div className={`transition-all duration-500 ease-in-out ${isOpen ? 'opacity-100 max-h-[300px] mt-4' : 'opacity-0 max-h-0 mt-0 pointer-events-none'}`}>
                   <div className="relative group/carousel">
                        <button onClick={() => scroll('left')} className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-4 z-10 p-2 bg-zinc-900/80 hover:bg-black/80 text-zinc-300 hover:text-white border border-zinc-700 rounded-full shadow-lg opacity-0 group-hover/carousel:opacity-100 transition-all group-hover/carousel:translate-x-0 backdrop-blur-md">
                            <ChevronLeft className="w-5 h-5" />
                        </button>

                        <div ref={scrollRef} className="flex overflow-x-auto pb-2 gap-4 snap-x hide-scrollbar scroll-smooth px-2">
                            {parts.map(part => {
                                const { label, icon: Icon, color, bg, border } = getTypeDetails(part.type);

                                return (
                                    <div key={part.id} className="min-w-[220px] flex-shrink-0 snap-start relative group">
                                        <div className={`h-40 rounded-[1.5rem] border border-zinc-800/60 bg-zinc-900/60 relative overflow-hidden flex items-center justify-center p-3 group-hover:border-zinc-600/80 group-hover:bg-zinc-800/60 transition-all duration-300`}>
                                            {part.svgUrl ? (
                                                <img src={`${API_BASE_URL}${part.svgUrl}`} alt={label} className="w-full h-full object-contain filter invert opacity-[0.85] group-hover:scale-110 transition-transform duration-500 ease-out" />
                                            ) : (
                                                <div className="text-xs text-zinc-600 border border-dashed border-zinc-700 w-full h-full rounded-xl flex items-center justify-center bg-zinc-950/30">
                                                No SVG render
                                                </div>
                                            )}
                                            
                                            <div className={`absolute top-3 left-3 px-2 py-1 rounded-lg flex items-center gap-1.5 backdrop-blur-md border ${bg} ${border} ${color}`}>
                                                <Icon className="w-3.5 h-3.5" />
                                                <span className="text-[10px] font-semibold tracking-wider uppercase">{label}</span>
                                            </div>
                                            
                                            <div className="absolute bottom-3 right-3 px-2.5 py-1 bg-zinc-950/80 backdrop-blur-md rounded-lg border border-zinc-800/80 shadow-lg group-hover:border-zinc-700/80 transition-colors">
                                                <span className="text-zinc-200 text-sm font-mono font-bold">×{part.quantity}</span>
                                            </div>
                                        </div>
                                        <div className="px-2 pt-3">
                                            <div className="text-zinc-200 text-sm font-medium truncate">{part.label || part.id}</div>
                                            <div className="text-zinc-500 text-xs font-mono truncate">
                                                {part.dimensions.map((value) => value.toFixed(1)).join(' × ')} mm
                                            </div>
                                        </div>
                                    </div>
                                )
                            })}
                        </div>

                        <button onClick={() => scroll('right')} className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-4 z-10 p-2 bg-zinc-900/80 hover:bg-black/80 text-zinc-300 hover:text-white border border-zinc-700 rounded-full shadow-lg opacity-0 group-hover/carousel:opacity-100 transition-all group-hover/carousel:translate-x-0 backdrop-blur-md">
                            <ChevronRight className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                <style dangerouslySetInnerHTML={{__html: `
                    .hide-scrollbar::-webkit-scrollbar { display: none; }
                    .hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
                `}} />
            </div>
        </div>
    );
}

'use client'

import React, { Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Stage } from '@react-three/drei'
import { ModelViewer } from './ModelViewer'

export function MainScene({ modelUrl, explosion = 0 }: { modelUrl: string | null, explosion?: number }) {
  if (!modelUrl) {
    return <div className="w-full h-full bg-zinc-950" />;
  }

  return (
    <div className="w-full h-full bg-zinc-950">
      <Canvas shadows camera={{ position: [-20, -40, 20], up: [0, 0, 1], fov: 45 }}>
        <color attach="background" args={['#09090b']} />
        
        <Suspense fallback={null}>
          <Stage environment="city" intensity={0.6} >
            <ModelViewer url={modelUrl} explosion={explosion} />
          </Stage>
        </Suspense>
        
        <OrbitControls makeDefault />
      </Canvas>
    </div>
  )
}

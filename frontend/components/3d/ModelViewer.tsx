import React, { useMemo, useRef } from 'react'
import { useGLTF } from '@react-three/drei'
import * as THREE from 'three'
import { useFrame } from '@react-three/fiber'

export function ModelViewer({ url, explosion = 0 }: { url: string, explosion?: number }) {
  const { scene } = useGLTF(url)
  const groupRef = useRef<THREE.Group>(null)

  const parts = useMemo(() => {
    const bbox = new THREE.Box3().setFromObject(scene)
    const size = new THREE.Vector3()
    bbox.getSize(size)
    const maxDim = Math.max(size.x, size.y, size.z)

    const assemblyCenter = new THREE.Vector3()
    bbox.getCenter(assemblyCenter)

    const meshList: THREE.Mesh[] = []
    
    scene.traverse((child) => {
      if ((child as THREE.Mesh).isMesh) {
        const mesh = child as THREE.Mesh
        mesh.castShadow = true
        mesh.receiveShadow = true
        
        if (!mesh.userData.originalPosition) {
          mesh.userData.originalPosition = mesh.position.clone()
          
          const partBox = new THREE.Box3().setFromObject(mesh)
          const partCenter = new THREE.Vector3()
          partBox.getCenter(partCenter)
          
          const direction = new THREE.Vector3().subVectors(partCenter, assemblyCenter).normalize()
          if (direction.lengthSq() === 0) direction.set(0, 1, 0)
          
          mesh.userData.direction = direction
          mesh.userData.maxDim = maxDim
        }
        meshList.push(mesh)
      }
    })
    return meshList
  }, [scene])

  useFrame(() => {
    parts.forEach((mesh) => {
      const orig = mesh.userData.originalPosition as THREE.Vector3
      const dir = mesh.userData.direction as THREE.Vector3
      const dim = mesh.userData.maxDim as number
      
      mesh.position.copy(orig).add(dir.clone().multiplyScalar(dim * explosion * 1.5))
    })
  })

  return <primitive object={scene} ref={groupRef} />
}

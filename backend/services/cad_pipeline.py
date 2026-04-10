import os
import asyncio
from backend.services.job_manager import job_manager

def process_step_file(job_id: str, file_path: str):
    async def run():
        try:
            await job_manager.update_job(job_id, "processing", 10, "Parsing STEP geometry")
            import cadquery as cq
            
            await job_manager.update_job(job_id, "processing", 30, "Reading components")
            # importStep is available, alternatively cq.Assembly().add() might be needed 
            # some versions of cadquery use cq.importers.importStep
            shape = cq.importers.importStep(file_path)
            asm = cq.Assembly()
            for solid in shape.solids().vals():
                asm.add(solid)
            
            await job_manager.update_job(job_id, "processing", 60, "Triangulating solids")
            out_file = os.path.join("backend", "storage", f"{job_id}.glb")
            asm.save(out_file, "GLTF")
            
            await job_manager.update_job(job_id, "completed", 100, "Done", f"/api/files/{job_id}.glb")

        except Exception as e:
            await job_manager.update_job(job_id, "failed", 0, str(e))

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(run())
        else:
            loop.run_until_complete(run())
    except RuntimeError:
        asyncio.run(run())

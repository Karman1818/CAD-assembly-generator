from fastapi import APIRouter, File, UploadFile, BackgroundTasks
from sse_starlette.sse import EventSourceResponse
from backend.services.job_manager import job_manager
from backend.services.cad_pipeline import process_step_file
import uuid
import os
import shutil

router = APIRouter()

@router.post("/upload")
async def upload_step(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.step', '.stp')):
        return {"error": "Invalid file type. Only .step or .stp are allowed."}

    job_id = str(uuid.uuid4())
    job_manager.create_job(job_id)

    # Save file
    file_path = os.path.join("backend", "storage", f"{job_id}.step")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Start background task
    background_tasks.add_task(process_step_file, job_id, file_path)

    return {"job_id": job_id}

@router.get("/progress/{job_id}/stream")
async def progress_stream(job_id: str):
    return EventSourceResponse(job_manager.stream_job_progress(job_id))

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from backend.services.assembly_ai import generate_assembly_instructions
import os
import json

router = APIRouter()

@router.post("/generate/{job_id}")
async def generate_instructions(job_id: str):
    """Trigger AI generation of assembly instructions for a processed CAD model."""
    parts_path = os.path.join("backend", "storage", f"{job_id}_parts.json")
    if not os.path.exists(parts_path):
        raise HTTPException(status_code=404, detail="Parts metadata not found. Upload and process a STEP file first.")
    
    try:
        instructions = await generate_assembly_instructions(job_id)
        return instructions
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")


@router.get("/instructions/{job_id}")
async def get_instructions(job_id: str):
    """Retrieve previously generated assembly instructions."""
    instructions_path = os.path.join("backend", "storage", f"{job_id}_instructions.json")
    if not os.path.exists(instructions_path):
        raise HTTPException(status_code=404, detail="Instructions not yet generated for this job.")
    
    with open(instructions_path, 'r', encoding='utf-8') as f:
        return json.load(f)


@router.get("/pdf/{job_id}")
async def get_instructions_pdf(job_id: str):
    pdf_path = os.path.join("backend", "storage", f"{job_id}_instructions.pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF has not been generated for this job yet.")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"{job_id}_instructions.pdf",
    )

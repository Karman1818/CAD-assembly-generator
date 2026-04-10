import asyncio
import json

class JobManager:
    def __init__(self):
        self.jobs = {}

    def create_job(self, job_id: str):
        self.jobs[job_id] = {
            "status": "processing",
            "progress": 0,
            "message": "Upload complete",
            "queue": asyncio.Queue()
        }

    async def update_job(self, job_id: str, status: str, progress: int, message: str, result_url: str = None):
        if job_id not in self.jobs:
            return
        
        job = self.jobs[job_id]
        job["status"] = status
        job["progress"] = progress
        job["message"] = message
        if result_url:
            job["result_model_url"] = result_url

        data = {
            "status": status,
            "progress": progress,
            "message": message
        }
        if result_url:
            data["result_model_url"] = result_url
            
        await job["queue"].put(data)

    async def stream_job_progress(self, job_id: str):
        if job_id not in self.jobs:
            yield {"data": json.dumps({"status": "error", "message": "Job not found"})}
            return
            
        job = self.jobs[job_id]
        
        # Initial yield
        yield {"data": json.dumps({"status": job["status"], "progress": job["progress"], "message": job["message"]})}
        
        while True:
            update = await job["queue"].get()
            yield {"data": json.dumps(update)}
            if update["status"] in ["completed", "failed", "error"]:
                break

job_manager = JobManager()

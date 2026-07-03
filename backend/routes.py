import os   # this is for the file path
import logging  # this is for logging the errors
import asyncio  # this is for running the style generation in the background
import json  # this is for parsing the json data

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from database import get_session
from models import Job, Thumbnail

from services.generator_services import process_job, STYLE_ORDER
from services.imagekit_service import upload_file, get_variants

# logger means we are creating a logger object that we can use to log messages in our code.
logger = logging.getLogger(__name__)

# this is the router object that we will use to define our API endpoints. The prefix means that all the endpoints defined in this router will have the prefix /api.
router = APIRouter(prefix="/api")

# this is the request model for creating a job.
class CreateJobRequest(BaseModel):
    prompt: str
    num_thumbnails: int
    headshot_url: str

# this is the response model for creating a job.
class CreateJobResponse(BaseModel):
    job_id: str

# this is the response model for getting a job.
class ThumbnailResponse(BaseModel):
    id: str
    style_name: str
    status: str
    imagekit_url: str | None = None
    error_message: str | None = None
    variants: dict | None = None

# this is the response model for getting a job.
class JobResponse(BaseModel):
    id: str
    prompt: str
    num_thumbnails: int
    headshot_url: str
    status: str
    thumbnails: list[ThumbnailResponse]

# this endpoint for uploading headshot
@router.post("/upload-headshot")
async def upload_headshot(file: UploadFile = File(...)):

    contents = await file.read()  # Read the file to ensure it's fully uploaded
    url = upload_file(
        file_bytes=contents,
        file_name=file.filename or "headshot.jpg",
        folder="headshots",
        content_type=file.content_type or "image/jpeg"
    )
    return {"url": url}

# this endpoint for creating a job
@router.post("/jobs", response_model=CreateJobResponse)
async def create_job(request: CreateJobRequest, session: Session = Depends(get_session)):
    if request.num_thumbnails < 1 or request.num_thumbnails > 3:
        raise HTTPException(status_code=400, detail="num_thumbnails must be between 1 and 3")
    
    # Create a new Job entry in the database
    job = Job(prompt=request.prompt, num_thumbnails=request.num_thumbnails, headshot_url=request.headshot_url)
    session.add(job)
    
    # Create Thumbnail entries for the job based on the requested number of thumbnails
    styles = STYLE_ORDER[:request.num_thumbnails]
    for style in styles:
        thumb = Thumbnail(job_id=job.id, style_name=style)
        session.add(thumb)

    session.commit()

    #  Start processing each thumbnail in the background
    for thumbnail in job.thumbnails:
        asyncio.create_task(process_job(thumbnail.id))
    return CreateJobResponse(job_id=job.id)


# this endpoint for getting a job
@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str, session: Session = Depends(get_session)):
    
    # Query the database for the job with the given job_id
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Query the database for all thumbnails associated with the job
    thumbnails = session.exec(select(Thumbnail).where(Thumbnail.job_id == job_id)).all()
    thumb_response = []
    for t in thumbnails:
        variants = get_variants(t.imagekit_url) if t.imagekit_url else None
        thumb_response.append(ThumbnailResponse(
            id=t.id,
            style_name=t.style_name,
            status=t.status,
            imagekit_url=t.imagekit_url,
            error_message=t.error_message,
            variants=variants
        ))

    return JobResponse(
        id=job.id,
        prompt=job.prompt,
        num_thumbnails=job.num_thumbnails,
        headshot_url=job.headshot_url,
        status=job.status,
        thumbnails=thumb_response
    )


# this endpoint for streaming the job status in real-time
@router.get("/jobs/{job_id}/stream")
async def stream_job(job_id: str):

    # This endpoint streams the status of the job in real-time
    async def event_generator():
        from database import engine
        sent_thumbnails = set()  # Keep track of thumbnails that have already been sent

        while True:
            with Session(engine) as session:
                job = session.get(Job, job_id)
                if not job:
                    yield f"event: error\ndata: {json.dumps({'error': 'Job not found'})}\n\n"
                    return
                # Check if all thumbnails have been processed
                thumbnails = session.exec(
                    select(Thumbnail).where(Thumbnail.job_id == job_id)
                ).all()

                # If all thumbnails are either uploaded or failed, we can stop the stream
                for t in thumbnails:
                    if t.id in sent_thumbnails:
                        continue  # Skip thumbnails that have already been sent
                    if t.status == "uploaded":
                        variants = get_variants(t.imagekit_url)
                        data = json.dumps({
                            "thumbnail_id": t.id,
                            "style_name": t.style_name,
                            "imagekit_url": t.imagekit_url,
                            "variants": variants
                        })
                        yield f"event: thumbnial ready\ndata: {data}\n\n"
                        sent_thumbnails.add(t.id)

                    elif t.status == "failed":
                        data = json.dumps({
                            "thumbnail_id": t.id,
                            "style_name": t.style_name,
                            "error": t.error_message
                        })
                        yield f"event: thumbnail failed\ndata: {data}\n\n"
                        sent_thumbnails.add(t.id)

                # If all thumbnails are either uploaded or failed, we can stop the stream
                all_done = all(t.status in ["uploaded", "failed"] for t in thumbnails)
                if all_done and len(sent_thumbnails) == len(thumbnails):

                    data = json.dumps({"job_id": job_id, "status": job.status})
                    yield f"events job completed\n data: {data}"
                    return
                
            await asyncio.sleep(1.5)

    
    # server sentiment events (SSE) is a standard that allows a server to push updates to the client over a single HTTP connection. The client can listen for these updates and handle them as they arrive. In this case, we are using SSE to stream the status of the job in real-time.
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no" }
        )
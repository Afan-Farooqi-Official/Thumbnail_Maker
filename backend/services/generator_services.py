import asyncio
from asyncio.log import logger
import logging

from click import prompt
from sqlmodel import Session, select
from database import engine
from models import Job, Thumbnail
from services.openai_service import generate_thumbnail
from services.imagekit_service import upload_file

logger = logging.getLogger(__name__)

STYLES = {
    "bold-dramatic": (
        "Bold and dramatic, with strong contrasts and intense colors, "
        "evoking a sense of power and intensity."
    ),
    "clean-minimal": (
        "Clean and minimal, with a focus on simplicity and clarity, "
        "using a limited color palette and negative space."
    ),
    "vibrant-energetic": (
        "Vibrant and energetic, with bright colors and dynamic compositions, "
        "conveying a sense of excitement and movement." 
    )
}

STYLE_ORDER = ["bold-dramatic", "clean-minimal", "vibrant-energetic"]

# this function will be called by the job queue to generate a single thumbnail
async def generate_single_thumbnail(thumbnail_id: str, prompt: str, headshot_url: str):

    # Update the thumbnail status to "generating" and retrieve the style
    with Session(engine) as session:
        thumb = session.get(Thumbnail, thumbnail_id)
        thumb.status = "generating"
        style_name = thumb.style
        session.add(thumb)
        session.commit()

    
    style_prompt = STYLES[style_name]
    try:
        image_byte = await generate_thumbnail(prompt, headshot_url, style_prompt)

        # session for retrieving the job_id associated with the thumbnail
        with Session(engine) as session:
            thumb = session.get(Thumbnail, thumbnail_id)
            job_id = thumb.job_id

        # this is where we upload the image to imagekit and get the url
        url = await upload_file(
            file_bytes=image_byte,
            file_name=f"{thumbnail_id}.png",
            folder_path=f"thumbnails/{job_id}/",
        )

        # session for updating the thumbnail with the imagekit url and status
        with Session(engine) as session:
            thumb = session.get(Thumbnail, thumbnail_id)
            thumb.imagekit_url = url
            thumb.status = "uploaded"
            session.add(thumb)
            session.commit()
        
        # log the successful generation and upload of the thumbnail
        logger.info(f"Thumbnail {thumbnail_id} generated and uploaded successfully.")   

    except Exception as e:
        logger.error(f"Error occurred while generating thumbnail {thumbnail_id}: {e}")

        # session for updating the thumbnail status to "failed" and storing the error message
        with Session(engine) as session:
            thumb = session.get(Thumbnail, thumbnail_id)
            thumb.status = "failed"
            thumb.error_message = str(e)[:500]  # Truncate the error message to 500 characters
            session.add(thumb)
            session.commit()

# this function will be called by the job queue to process a single job
async def process_job(job_id: str):

    # make job status to "processing"
    # find all thumbnails associated with the job
    # start one worker for each thumbnail
    # wait for all workers to finish
    # mark the job as "completed" if all thumbnails are generated successfully, otherwise mark it as "failed"

    with Session(engine) as session:
        job = session.get(Job, job_id)
        job.status = "processing"
        prompt = job.prompt
        headshot_url = job.headshot_url
        session.add(job)
        session.commit()

        # retrieve all thumbnails associated with the job
        thumbnails = session.exec(
            select(Thumbnail).where(Thumbnail.job_id == job_id)
        ).all()
        thumbnails_ids = [t.id for t in thumbnails]

        # create a list of tasks for generating thumbnails
        tasks = [
            generate_single_thumbnail(tid, prompt, headshot_url)
            for tid in thumbnails_ids
        ]

        # wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)

        # check if all thumbnails are generated successfully
        with Session(engine) as session:
            thumbnails = session.exec(
            select(Thumbnail).where(Thumbnail.job_id == job_id)
        ).all()
        all_failed = all(t.status == "failed" for t in thumbnails)
        job = session.get(Job, job_id)
        job.status = "failed" if all_failed else "completed"
        session.add(job)
        session.commit()
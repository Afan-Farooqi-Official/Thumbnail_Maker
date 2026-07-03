from datetime import datetime, timezone
from typing import Optional, List
from uuid import uuid4

from sqlmodel import Field, SQLModel, Relationship

# UUID generator function, use is as default_factory for UUID fields
def _uuid() -> str:
    return str(uuid4())

# utc means that the datetime is in Coordinated Universal Time (UTC) timezone. This function returns the current UTC time.
def _now () -> datetime:
    return datetime.now(timezone.utc)


# SQLModel class representing a Thumbnail entity in the database
class Thumbnail(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    job_id: str = Field(foreign_key="job.id")
    style_name: str = Field(default="")
    imagekit_url: Optional[str] = Field(default=None)
    status: str = Field(default="pending")
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=_now)

    # Relationship to the Job entity, allowing access to the associated Job object from a Thumbnail instance
    job: Optional["Job"] = Relationship(back_populates="thumbnails")


# SQLModel class representing a Job entity in the database
class Job(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    prompt: str
    num_thumbnails: int = Field(default=1, ge=1, le=3)
    headshot_url: Optional[str] = Field(default="")
    status: str = Field(default="pending")
    created_at: datetime = Field(default_factory=_now)
    
    # Relationship to the Thumbnail entity, allowing access to the associated Thumbnail objects from a Job instance
    thumbnails: List[Thumbnail] = Relationship(back_populates="job")
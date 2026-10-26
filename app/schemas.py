from typing import List, Optional

from pydantic import BaseModel, Field


class ScrapeRequest(BaseModel):
    url: str
    existing_urls: List[str] = []
    # Which concurrency strategy to process job URLs with.
    # One of: "gather", "wait", "as_completed", "semaphore", "queue"
    # See app/strategies/ — each value maps to a module of the same idea.
    strategy: str = "gather"


class JobInformation(BaseModel):
    job_title: Optional[str] = Field(None, description="Job title")
    company_name: Optional[str] = Field(None, description="Company name")
    location: Optional[str] = Field(None, description="Job location, as a single readable string")
    commitment: Optional[str] = Field(
        None, description="One of: 'full-time', 'part-time', 'contract', 'internship'"
    )
    seniority_level: Optional[str] = Field(
        None, description="One of: 'Entry Level', 'Mid Level', 'Senior Level'"
    )
    job_description: Optional[str] = Field(None, description="Plain-text job description, no HTML")
    apply_url: Optional[str] = Field(None, description="The URL of the job posting")

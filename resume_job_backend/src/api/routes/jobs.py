from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from src.core.db import db_query
from src.services.parsing_service import parse_job_text
from src.services.supabase_service import get_current_user_optional

router = APIRouter()


class JobCreateRequest(BaseModel):
    # PUBLIC_INTERFACE
    title: Optional[str] = Field(None, description="Optional job title")
    text: str = Field(..., description="Raw job description text")


class JobResponse(BaseModel):
    # PUBLIC_INTERFACE
    id: int = Field(..., description="Job ID")
    user_id: Optional[str] = Field(None, description="Supabase user ID if available")
    title: Optional[str] = Field(None, description="Job title")
    text: str = Field(..., description="Original job description text")
    parsed: dict = Field(..., description="Parsed job structure")


@router.post(
    "",
    summary="Create job description",
    description="Create and parse a job description record.",
    response_model=JobResponse,
)
async def create_job(req: JobCreateRequest, user=Depends(get_current_user_optional)):
    """
    PUBLIC_INTERFACE
    Create a job description and store parsed info.
    """
    parsed = parse_job_text(req.text)
    insert_sql = """
        INSERT INTO jobs (user_id, title, text, parsed)
        VALUES (%s, %s, %s, %s)
        RETURNING id, user_id, title, text, parsed
    """
    row = await db_query(insert_sql, (user["sub"] if user else None, req.title, req.text, parsed), fetch_one=True)
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "title": row["title"],
        "text": row["text"],
        "parsed": row["parsed"],
    }


@router.get(
    "/{job_id}",
    summary="Get job by id",
    description="Retrieve a job description and parsed structure.",
    response_model=JobResponse,
)
async def get_job(job_id: int, user=Depends(get_current_user_optional)):
    """
    PUBLIC_INTERFACE
    Get a job record by ID.
    """
    row = await db_query("SELECT id, user_id, title, text, parsed FROM jobs WHERE id = %s", (job_id,), fetch_one=True)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if user and row["user_id"] and row["user_id"] != user["sub"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "title": row["title"],
        "text": row["text"],
        "parsed": row["parsed"],
    }

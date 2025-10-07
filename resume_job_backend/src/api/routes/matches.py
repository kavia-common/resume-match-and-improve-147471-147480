from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from src.core.db import db_query
from src.services.matching_service import compute_match
from src.services.supabase_service import get_current_user_optional

router = APIRouter()


class MatchRequest(BaseModel):
    # PUBLIC_INTERFACE
    resume_id: int = Field(..., description="Resume ID to match")
    job_id: int = Field(..., description="Job ID to match against")


class MatchResponse(BaseModel):
    # PUBLIC_INTERFACE
    id: int = Field(..., description="Match ID")
    resume_id: int = Field(..., description="Resume ID")
    job_id: int = Field(..., description="Job ID")
    score: float = Field(..., description="Match score 0..1")
    explanation: dict = Field(..., description="Detailed scoring breakdown")


@router.post(
    "/match",
    summary="Compute match",
    description="Compute a match score between a resume and a job. Persists the result.",
    response_model=MatchResponse,
)
async def create_match(req: MatchRequest, user=Depends(get_current_user_optional)):
    """
    PUBLIC_INTERFACE
    Compute resume-job match score and store it.
    """
    resume = await db_query("SELECT id, user_id, parsed FROM resumes WHERE id = %s", (req.resume_id,), fetch_one=True)
    job = await db_query("SELECT id, user_id, parsed FROM jobs WHERE id = %s", (req.job_id,), fetch_one=True)
    if not resume or not job:
        raise HTTPException(status_code=404, detail="Resume or Job not found")
    if user:
        # ownership checks (soft)
        if resume["user_id"] and resume["user_id"] != user["sub"]:
            raise HTTPException(status_code=403, detail="Forbidden resume")
        if job["user_id"] and job["user_id"] != user["sub"]:
            raise HTTPException(status_code=403, detail="Forbidden job")

    score, explanation = compute_match(resume["parsed"], job["parsed"])
    row = await db_query(
        "INSERT INTO matches (resume_id, job_id, score, explanation) VALUES (%s, %s, %s, %s) RETURNING id",
        (req.resume_id, req.job_id, score, explanation),
        fetch_one=True,
    )
    return {"id": row["id"], "resume_id": req.resume_id, "job_id": req.job_id, "score": score, "explanation": explanation}


@router.get(
    "/matches",
    summary="List matches",
    description="List latest matches for the current user or globally if anonymous (limited).",
)
async def list_matches(limit: int = 25, user=Depends(get_current_user_optional)):
    """
    PUBLIC_INTERFACE
    List match results, newest first.
    """
    if user:
        sql = """
            SELECT m.id, m.resume_id, m.job_id, m.score, m.explanation, m.created_at
            FROM matches m
            JOIN resumes r ON r.id = m.resume_id
            WHERE r.user_id = %s
            ORDER BY m.created_at DESC
            LIMIT %s
        """
        rows = await db_query(sql, (user["sub"], limit))
    else:
        rows = await db_query(
            "SELECT id, resume_id, job_id, score, explanation, created_at FROM matches ORDER BY created_at DESC LIMIT %s",
            (limit,),
        )
    return {"items": rows}


@router.get(
    "/matches/{match_id}",
    summary="Get match by id",
    description="Retrieve a single match record.",
    response_model=MatchResponse,
)
async def get_match(match_id: int, user=Depends(get_current_user_optional)):
    """
    PUBLIC_INTERFACE
    Get a single match result.
    """
    row = await db_query("SELECT id, resume_id, job_id, score, explanation FROM matches WHERE id = %s", (match_id,), fetch_one=True)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    # ownership soft check if user is present
    if user:
        res = await db_query("SELECT user_id FROM resumes WHERE id = %s", (row["resume_id"],), fetch_one=True)
        if res and res["user_id"] and res["user_id"] != user["sub"]:
            raise HTTPException(status_code=403, detail="Forbidden")
    return {
        "id": row["id"],
        "resume_id": row["resume_id"],
        "job_id": row["job_id"],
        "score": row["score"],
        "explanation": row["explanation"],
    }

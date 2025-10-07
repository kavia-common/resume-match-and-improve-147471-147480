from typing import Optional, List
from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException
from fastapi import Body, status
from pydantic import BaseModel, Field
from src.core.db import db_query
from src.services.parsing_service import parse_resume_text, extract_text_from_file
from src.services.suggestions_service import generate_suggestions
from src.services.supabase_service import get_current_user_optional

router = APIRouter()


class ResumeCreateRequest(BaseModel):
    # PUBLIC_INTERFACE
    text: str = Field(..., description="Raw resume text content")
    title: Optional[str] = Field(None, description="Optional title for the resume")


class ResumeResponse(BaseModel):
    # PUBLIC_INTERFACE
    id: int = Field(..., description="Resume ID")
    user_id: Optional[str] = Field(None, description="Supabase user ID if available")
    title: Optional[str] = Field(None, description="Resume title")
    text: str = Field(..., description="Resume original text")
    parsed: dict = Field(..., description="Parsed structured data")


class SuggestionRequest(BaseModel):
    # PUBLIC_INTERFACE
    job_text: Optional[str] = Field(None, description="Optional job description text to tailor suggestions")


class SuggestionResponse(BaseModel):
    # PUBLIC_INTERFACE
    resume_id: int = Field(..., description="Resume ID")
    suggestions: List[dict] = Field(..., description="List of suggestion objects")


@router.post(
    "/upload",
    summary="Upload resume",
    description="Upload a resume as text or multipart file. Returns parsed structure and saved record.",
    response_model=ResumeResponse,
)
async def upload_resume(
    # Either multipart or json; support both
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    json_body: Optional[ResumeCreateRequest] = Body(None),
    user=Depends(get_current_user_optional),
):
    """
    PUBLIC_INTERFACE
    Upload a resume either as a multipart file or plain text (JSON or form-data).
    Returns the created resume with parsed fields.
    """
    raw_text = None
    title = None

    if json_body and json_body.text:
        raw_text = json_body.text
        title = json_body.title
    elif file is not None:
        try:
            raw_text = await extract_text_from_file(file)
            title = getattr(file, "filename", None)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")
    elif text:
        raw_text = text
    else:
        raise HTTPException(status_code=400, detail="Provide either 'file', 'text' form field, or JSON with 'text'.")

    parsed = parse_resume_text(raw_text)

    # Insert into database
    insert_sql = """
        INSERT INTO resumes (user_id, title, text, parsed)
        VALUES (%s, %s, %s, %s)
        RETURNING id, user_id, title, text, parsed
    """
    params = (user["sub"] if user else None, title, raw_text, parsed)
    row = await db_query(insert_sql, params, fetch_one=True)
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "title": row["title"],
        "text": row["text"],
        "parsed": row["parsed"],
    }


@router.get(
    "/{resume_id}",
    summary="Get resume by id",
    description="Retrieve resume details and parsed structure by id.",
    response_model=ResumeResponse,
)
async def get_resume(resume_id: int, user=Depends(get_current_user_optional)):
    """
    PUBLIC_INTERFACE
    Get a resume record by ID.
    """
    row = await db_query("SELECT id, user_id, title, text, parsed FROM resumes WHERE id = %s", (resume_id,), fetch_one=True)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    # Optional: enforce ownership if user present
    if user and row["user_id"] and row["user_id"] != user["sub"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "title": row["title"],
        "text": row["text"],
        "parsed": row["parsed"],
    }


@router.post(
    "/{resume_id}/suggestions",
    summary="Generate suggestions",
    description="Generate ATS-style improvement suggestions for a resume. Optionally tailored with job text.",
    response_model=SuggestionResponse,
)
async def create_suggestions(resume_id: int, req: SuggestionRequest, user=Depends(get_current_user_optional)):
    """
    PUBLIC_INTERFACE
    Generate improvement suggestions and persist them.
    """
    row = await db_query("SELECT id, user_id, text, parsed FROM resumes WHERE id = %s", (resume_id,), fetch_one=True)
    if not row:
        raise HTTPException(status_code=404, detail="Resume not found")
    if user and row["user_id"] and row["user_id"] != user["sub"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    suggestions = generate_suggestions(row["text"], row["parsed"], job_text=req.job_text if req else None)

    insert_sql = "INSERT INTO suggestions (resume_id, items) VALUES (%s, %s) RETURNING id"
    _ = await db_query(insert_sql, (resume_id, suggestions), fetch_one=True)

    return {"resume_id": resume_id, "suggestions": suggestions}


@router.get(
    "/{resume_id}/suggestions",
    summary="Get suggestions for resume",
    description="Return the latest suggestions for a resume.",
)
async def get_suggestions(resume_id: int, user=Depends(get_current_user_optional)):
    """
    PUBLIC_INTERFACE
    Retrieve suggestions stored for a resume.
    """
    row = await db_query("SELECT r.user_id FROM resumes r WHERE r.id = %s", (resume_id,), fetch_one=True)
    if not row:
        raise HTTPException(status_code=404, detail="Resume not found")
    if user and row["user_id"] and row["user_id"] != user["sub"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    sug = await db_query(
        "SELECT id, items, created_at FROM suggestions WHERE resume_id = %s ORDER BY created_at DESC LIMIT 1",
        (resume_id,),
        fetch_one=True,
    )
    if not sug:
        return {"resume_id": resume_id, "suggestions": []}
    return {"resume_id": resume_id, "suggestions": sug["items"], "id": sug["id"], "created_at": sug["created_at"]}

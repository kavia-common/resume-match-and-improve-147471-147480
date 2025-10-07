import re
from typing import Dict, List
from fastapi import UploadFile

# Basic text extraction from uploads
# PUBLIC_INTERFACE
async def extract_text_from_file(file: UploadFile) -> str:
    """Read file bytes and decode as UTF-8 fallback latin-1."""
    content = await file.read()
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("latin-1")


def _tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[A-Za-z0-9+#.\-]+", text.lower())
    return tokens


# PUBLIC_INTERFACE
def parse_resume_text(text: str) -> Dict:
    """Parse resume text into a minimal structure."""
    tokens = _tokenize(text)
    # naive email and phone extraction
    email = None
    m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    if m:
        email = m.group(0)
    phone = None
    p = re.search(r"(\+?\d[\d \-\(\)]{7,}\d)", text)
    if p:
        phone = p.group(1)

    # naive skills from token set
    skill_keywords = {"python", "java", "javascript", "react", "node", "sql", "postgres", "aws", "docker", "kubernetes"}
    skills = sorted(list(set(tokens) & skill_keywords))

    # experience years heuristic: count occurrences of years like 2018-2024 -> approximate 1 per range mention
    years_mentions = len(re.findall(r"(20\d{2}|19\d{2})", text))

    return {
        "contact": {"email": email, "phone": phone},
        "skills": skills,
        "summary_tokens": tokens[:200],
        "meta": {"year_mentions": years_mentions},
    }


# PUBLIC_INTERFACE
def parse_job_text(text: str) -> Dict:
    """Parse job description into structure similar to resume parse."""
    tokens = _tokenize(text)
    skill_keywords = {"python", "java", "javascript", "react", "node", "sql", "postgres", "aws", "docker", "kubernetes"}
    skills = sorted(list(set(tokens) & skill_keywords))
    return {"skills": skills, "summary_tokens": tokens[:200]}

from typing import Dict, Tuple, List


def _jaccard(a: List[str], b: List[str]) -> float:
    """Compute Jaccard similarity between two token lists."""
    sa, sb = set(a or []), set(b or [])
    if not sa or not sb:
        return 0.0
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / max(1, union)


# PUBLIC_INTERFACE
def compute_match(resume_parsed: Dict, job_parsed: Dict) -> Tuple[float, Dict]:
    """Compute a simple weighted match score with explanation.
    
    Args:
        resume_parsed: Parsed resume dict containing 'skills' and 'summary_tokens'
        job_parsed: Parsed job dict containing 'skills' and 'summary_tokens'
    Returns:
        Tuple of (score: float in 0..1, explanation: dict)
    """
    r_skills = list(resume_parsed.get("skills", []) or [])
    j_skills = list(job_parsed.get("skills", []) or [])
    r_tokens = list(resume_parsed.get("summary_tokens", []) or [])
    j_tokens = list(job_parsed.get("summary_tokens", []) or [])

    skill_overlap = _jaccard(r_skills, j_skills)
    token_overlap = _jaccard(r_tokens, j_tokens)

    # weights favor skills
    score = 0.7 * skill_overlap + 0.3 * token_overlap
    explanation = {
        "components": {
            "skill_overlap": round(float(skill_overlap), 4),
            "token_overlap": round(float(token_overlap), 4),
        },
        "weights": {"skills": 0.7, "tokens": 0.3},
        "details": {"resume_skills": r_skills, "job_skills": j_skills},
    }
    return round(float(score), 4), explanation

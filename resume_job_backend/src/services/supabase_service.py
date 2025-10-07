from typing import Optional, Dict, Any
import logging
from jose import jwt, JWTError

from fastapi import HTTPException, status, Header
from src.core.config import settings

logger = logging.getLogger("supabase_auth")


def _verify_bearer_token(token: str) -> Dict[str, Any]:
    """Verify JWT using Supabase JWT secret."""
    try:
        payload = jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"])
        return payload
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")


# PUBLIC_INTERFACE
def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency that verifies Authorization: Bearer <token> using Supabase JWT secret if configured.
    If no secret is set, returns None (anonymous) and logs a warning once.
    """
    if not settings.supabase_jwt_secret:
        if not getattr(get_current_user_optional, "_warned", False):
            logger.warning("SUPABASE_JWT_SECRET not set. Allowing anonymous requests for development.")
            setattr(get_current_user_optional, "_warned", True)
        return None

    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header")

    token = parts[1]
    user = _verify_bearer_token(token)
    return user

import os
from typing import List, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

# Load env vars from .env if present
load_dotenv()


class Settings(BaseModel):
    # PUBLIC_INTERFACE
    postgres_url: Optional[str] = None
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    postgres_db: Optional[str] = None
    postgres_port: Optional[str] = None
    # Allow specifying host when building DSN from parts (defaults to localhost if not provided)
    postgres_host: Optional[str] = None
    # List of allowed origins for CORS
    cors_origins: List[str] = []
    # Supabase configuration
    supabase_url: Optional[str] = None
    supabase_jwt_secret: Optional[str] = None
    supabase_service_role_key: Optional[str] = None
    # Storage bucket for resumes (Supabase)
    file_storage_bucket: Optional[str] = None
    # Defaults to 3001 per requirements
    backend_port: int = 3001

    # PUBLIC_INTERFACE
    def get_db_dsn(self) -> Optional[str]:
        """
        Return a postgres DSN URL. Prefer POSTGRES_URL; else build from parts if all provided.
        When building from parts, uses POSTGRES_HOST if provided, else 'localhost'.
        """
        if self.postgres_url:
            return self.postgres_url
        if all([self.postgres_user, self.postgres_password, self.postgres_db, self.postgres_port]):
            host = self.postgres_host or "localhost"
            return f"postgresql://{self.postgres_user}:{self.postgres_password}@{host}:{self.postgres_port}/{self.postgres_db}"
        return None


def _parse_cors_origins(val: Optional[str]) -> List[str]:
    """
    Parse a comma-separated list of origins into a list of strings.
    Empty/None returns an empty list.
    """
    if not val:
        return []
    # support comma-separated list
    return [o.strip() for o in val.split(",") if o.strip()]


# Build settings from environment variables.
# Note: Use CORS_ALLOWED_ORIGINS (CSV) per requirements.
settings = Settings(
    postgres_url=os.getenv("POSTGRES_URL"),
    postgres_user=os.getenv("POSTGRES_USER"),
    postgres_password=os.getenv("POSTGRES_PASSWORD"),
    postgres_db=os.getenv("POSTGRES_DB"),
    postgres_port=os.getenv("POSTGRES_PORT"),
    postgres_host=os.getenv("POSTGRES_HOST"),
    cors_origins=_parse_cors_origins(os.getenv("CORS_ALLOWED_ORIGINS")),
    supabase_url=os.getenv("SUPABASE_URL"),
    supabase_jwt_secret=os.getenv("SUPABASE_JWT_SECRET"),
    supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    file_storage_bucket=os.getenv("SUPABASE_BUCKET_RESUMES") or os.getenv("FILE_STORAGE"),
    # Default to 3001 when not specified
    backend_port=int(os.getenv("BACKEND_PORT", "3001")),
)

OPENAPI_TAGS = [
    {"name": "Health", "description": "Service health check"},
    {"name": "Resumes", "description": "Upload, view, and suggest improvements for resumes"},
    {"name": "Jobs", "description": "Create and view job descriptions"},
    {"name": "Matching", "description": "Compute and view resume-job match scores"},
    {"name": "Docs", "description": "Documentation related endpoints"},
]

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
    cors_origins: List[str] = []
    supabase_url: Optional[str] = None
    supabase_jwt_secret: Optional[str] = None
    supabase_service_role_key: Optional[str] = None
    file_storage_bucket: Optional[str] = None
    backend_port: int = 3001

    def get_db_dsn(self) -> Optional[str]:
        """
        PUBLIC_INTERFACE
        Return a postgres DSN URL. Prefer POSTGRES_URL; else build from parts if all provided.
        """
        if self.postgres_url:
            return self.postgres_url
        if all([self.postgres_user, self.postgres_password, self.postgres_db, self.postgres_port]):
            return f"postgresql://{self.postgres_user}:{self.postgres_password}@localhost:{self.postgres_port}/{self.postgres_db}"
        return None


def _parse_cors_origins(val: Optional[str]) -> List[str]:
    if not val:
        return []
    # support comma-separated list
    return [o.strip() for o in val.split(",") if o.strip()]


settings = Settings(
    postgres_url=os.getenv("POSTGRES_URL"),
    postgres_user=os.getenv("POSTGRES_USER"),
    postgres_password=os.getenv("POSTGRES_PASSWORD"),
    postgres_db=os.getenv("POSTGRES_DB"),
    postgres_port=os.getenv("POSTGRES_PORT"),
    cors_origins=_parse_cors_origins(os.getenv("CORS_ORIGINS")),
    supabase_url=os.getenv("SUPABASE_URL"),
    supabase_jwt_secret=os.getenv("SUPABASE_JWT_SECRET"),
    supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    file_storage_bucket=os.getenv("FILE_STORAGE"),
    backend_port=int(os.getenv("BACKEND_PORT", "3001")),
)

OPENAPI_TAGS = [
    {"name": "Health", "description": "Service health check"},
    {"name": "Resumes", "description": "Upload, view, and suggest improvements for resumes"},
    {"name": "Jobs", "description": "Create and view job descriptions"},
    {"name": "Matching", "description": "Compute and view resume-job match scores"},
    {"name": "Docs", "description": "Documentation related endpoints"},
]

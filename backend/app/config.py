"""Application configuration settings for Trust Gate."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DEMO_SAMPLES_DIR = DATA_DIR / "demo_samples"

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DEMO_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    APP_NAME: str = "Trust Gate API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # Database
    # Default to PostgreSQL, with auto-fallback to SQLite in database.py if unreachable
    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/trustgate",
        description="PostgreSQL or SQLite connection URL"
    )
    SQLITE_FALLBACK_URL: str = f"sqlite:///{BASE_DIR / 'trustgate.db'}"

    # AWS Textract credentials
    AWS_ACCESS_KEY_ID: str = Field(default="", description="AWS Access Key ID")
    AWS_SECRET_ACCESS_KEY: str = Field(default="", description="AWS Secret Access Key")
    AWS_REGION: str = Field(default="us-east-1", description="AWS Region")

    # LLM & AI Vision Providers (Groq + Gemini Multi-Provider with Auto-Failover)
    GROQ_API_KEY: str = Field(default=os.getenv("GROQ_API_KEY", ""), description="Groq API key for low-latency reasoning")
    GEMINI_API_KEY: str = Field(default=os.getenv("GEMINI_API_KEY", ""), description="Google Gemini API key for vision & LLM fallback")
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GEMINI_MODEL: str = "gemini-1.5-flash"
    OCR_PROVIDER: str = "AUTO"  # "GEMINI", "TEXTRACT", "DEV", "AUTO"

    # Security
    JWT_SECRET: str = Field(default="trustgate-secret-key-change-in-production-2026", description="JWT secret key")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60 * 24
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"

    # Hardware Configuration
    DEVICE_ID: str = "TG-001"
    SERIAL_PORT: str = "AUTO"  # AUTO detects or e.g. COM3
    SERIAL_BAUD_RATE: int = 115200
    GATE_OPEN_DURATION_MS: int = 5000
    LIVENESS_TIMEOUT_MS: int = 8000
    SERVO_ANGLE_LOCKED: int = 0
    SERVO_ANGLE_OPEN: int = 90

    # Verification Thresholds & Weights
    MINIMUM_AGE: int = 18
    STUDENT_REQUIRED: bool = True
    FACE_MATCH_THRESHOLD: float = 0.70
    FACE_INCONCLUSIVE_THRESHOLD: float = 0.50
    TAMPERING_RISK_THRESHOLD: float = 0.60
    LIVENESS_MIN_QUALITY: float = 0.65
    LIVENESS_MIN_DURATION_MS: int = 4000

    # Paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = DATA_DIR
    UPLOAD_DIR: Path = UPLOAD_DIR
    DEMO_SAMPLES_DIR: Path = DEMO_SAMPLES_DIR

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

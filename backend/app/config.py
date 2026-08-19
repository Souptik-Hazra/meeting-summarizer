import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

class Settings:
    PROJECT_NAME: str = "AI Meeting Intelligence & Summarization Platform"
    VERSION: str = "1.0.0"
    
    # Environment & CORS
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # AI Providers Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = "whisper-large-v3"
    
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # LLMOps & Prompt Versioning
    PROMPT_VERSION: str = "v1"
    
    # File Limits (e.g. 25MB max audio file size)
    MAX_FILE_SIZE_BYTES: int = 25 * 1024 * 1024
    ALLOWED_AUDIO_EXTENSIONS: set = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}

settings = Settings()

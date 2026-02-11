import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # API Settings
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    # Hugging Face Settings
    HF_API_KEY = os.getenv("HF_API_KEY", "")
    HF_MODEL = os.getenv("HF_MODEL", "gpt2")  # or use a better model
    
    # Document Processing
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10485760))  # 10MB
    SUPPORTED_FORMATS = ["pdf", "docx", "txt", "doc"]
    
    # Quiz Generation
    DEFAULT_QUESTION_COUNT = int(os.getenv("DEFAULT_QUESTION_COUNT", 10))
    MIN_QUESTION_COUNT = int(os.getenv("MIN_QUESTION_COUNT", 3))
    MAX_QUESTION_COUNT = int(os.getenv("MAX_QUESTION_COUNT", 50))

settings = Settings()
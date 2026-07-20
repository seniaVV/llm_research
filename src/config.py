import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "127.0.0.1"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DB", "agrometrics"),
    "user": os.getenv("POSTGRES_USER", "agrometrics"),
    "password": os.getenv("POSTGRES_PASSWORD", "agrometrics_dev_password"),
}

OLLAMA_BASE_URL = "http://127.0.0.1:11434"
MODEL_NAME = "qwen2.5:14b"

OPTIMAL_PARAMS = {
    "temperature": 0.5,
    "top_p": 0.85,
    "top_k": 30,
    "num_predict": 1024
}
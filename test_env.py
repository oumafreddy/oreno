# test_env.py
import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

print("Secret Key:", os.getenv("DJANGO_SECRET_KEY"))

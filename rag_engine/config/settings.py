import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq base URL
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
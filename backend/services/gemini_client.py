import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import google.generativeai as genai
import os
from dotenv import load_dotenv 

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found! Check your .env file.")

genai.configure(api_key=api_key)


def gemini_flash():
    return genai.GenerativeModel("gemini-2.5-flash")
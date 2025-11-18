import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_AI_KEY")

genai.configure(api_key=GEMINI_API_KEY)

models = genai.list_models()
for model in models:
    print(f"ID: {model.name}")
    print(f"Supports generateContent: {'generateContent' in model.supported_generation_methods}")
    print("-" * 40)
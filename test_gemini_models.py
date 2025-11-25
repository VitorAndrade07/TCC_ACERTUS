import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_AI_KEY = os.getenv("GEMINI_AI_KEY")

if GEMINI_AI_KEY:
    genai.configure(api_key=GEMINI_AI_KEY) # Sem client_options por enquanto para a lista
    
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            print(m.name)
else:
    print("GEMINI_AI_KEY não está configurada no .env")
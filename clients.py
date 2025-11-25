# clients.py
import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import HTTPException, Depends, APIRouter 

# Carrega as variáveis de ambiente
load_dotenv()
AI_KEY = os.getenv("AI_KEY")
AI_ENDPOINT = os.getenv("AI_ENDPOINT")
GEMINI_AI_KEY = os.getenv("GEMINI_AI_KEY")

# Variáveis globais para os clientes de IA
ai_client = None
gemini_model_instance = None

# Função de inicialização (chamada uma vez pelo FastAPI)
def initialize_clients():
    global ai_client
    global gemini_model_instance

    if AI_KEY and AI_ENDPOINT:
        try:
            credential = AzureKeyCredential(AI_KEY)
            ai_client = TextAnalyticsClient(endpoint=AI_ENDPOINT, credential=credential)
            print("Cliente Azure AI autenticado com sucesso (via clients.py).")
        except Exception as ex:
            print(f"ERRO na autenticação do cliente Azure AI (via clients.py): {ex}")
    else:
        print("Cliente Azure AI não inicializado devido à falta de chaves (via clients.py).")

    if GEMINI_AI_KEY:
        try: 
            genai.configure(api_key=GEMINI_AI_KEY)
            # AQUI ESTÁ A CORREÇÃO: Usar 'gemini-pro-latest'
            gemini_model_instance = genai.GenerativeModel('gemini-pro-latest') 
            print("Cliente Gemini AI inicializado e modelo carregado com sucesso (via clients.py).")
        except Exception as ex:
            print(f"ERRO na inicialização do cliente Gemini AI (via clients.py): {ex}")
    else:
        print("Cliente Gemini AI não inicializado devido à falta de chaves (via clients.py).")

# Funções de injeção de dependência
def get_azure_client():
    global ai_client
    if not ai_client:
        raise HTTPException(
            status_code=503, 
            detail="Serviço Azure AI Language não está disponível ou não foi autenticado."
        )
    yield ai_client

def get_gemini_model():
    global gemini_model_instance
    if not gemini_model_instance:
        raise HTTPException(
            status_code=503,
            detail="Modelo Gemini AI não está disponível ou não foi inicializado."
        )
    yield gemini_model_instance
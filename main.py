from fastapi import FastAPI, Depends, HTTPException
import os
import pandas as pd
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
from dotenv import load_dotenv
from typing import Dict, Any, List
# Importamos o router que deve conter a rota para os Estilos de Formatação
from routes.routes import router 

# Importação para o Gemini SDK
from google import genai
from google.genai import types
from google.genai.errors import APIError

# --- 1. CONFIGURAÇÃO INICIAL E VARIÁVEIS DE AMBIENTE ---
load_dotenv()
AI_KEY = os.getenv("AI_KEY")
AI_ENDPOINT = os.getenv("AI_ENDPOINT")
# NOVA: Variável para a chave do Gemini
GEMINI_KEY = os.getenv("GEMINI_AI_KEY") 

# Certifique-se de que as chaves estão presentes
if not AI_KEY or not AI_ENDPOINT:
    print("AVISO: Chaves 'AI_KEY' ou 'AI_ENDPOINT' não encontradas. O cliente Azure não será autenticado.")

# NOVA: Verifica a chave do Gemini
if not GEMINI_KEY:
    print("AVISO: Chave 'GEMINI_AI_KEY' não encontrada no .env. O cliente Gemini não será inicializado.")

# --- 2. INICIALIZAÇÃO DO APP E INCLUSÃO DE ROTAS ---
app = FastAPI(
    title="Minha API de TCC - ACERTUS",
    description="API para análise de feedback e processamento de texto utilizando Azure AI Language e Gemini.",
    version="1.0.0"
)

# Inclui o roteador existente
app.include_router(router) 

# NOVA: Importa o roteador do Gemini
from routes.gemini_routes import gemini_router
app.include_router(gemini_router)


ai_client = None
gemini_client = None # NOVA: Variável global para o cliente Gemini

# --- 3. EVENTO DE INICIALIZAÇÃO (SETUP DA AZURE AI E GEMINI) ---
@app.on_event("startup")
def startup_event():
    """
    Função executada na inicialização do servidor.
    Cria e autentica os clientes do Azure AI Language e do Gemini.
    """
    global ai_client
    if AI_KEY and AI_ENDPOINT:
        try:
            credential = AzureKeyCredential(AI_KEY)
            # Cria a instância do cliente Azure AI Language
            ai_client = TextAnalyticsClient(endpoint=AI_ENDPOINT, credential=credential)
            print("Cliente Azure AI autenticado com sucesso.")
        except Exception as ex:
            print(f"ERRO na autenticação do cliente Azure AI: {ex}")
    else:
        print("Cliente Azure AI não inicializado devido à falta de chaves.")
    
    # NOVA: Inicialização do cliente Gemini
    global gemini_client
    if GEMINI_KEY:
        try:
            # O cliente do Gemini é inicializado usando a chave que está na variável de ambiente
            gemini_client = genai.Client(api_key=GEMINI_KEY)
            print("Cliente Gemini API inicializado com sucesso.")
        except Exception as ex:
            print(f"ERRO na inicialização do cliente Gemini: {ex}")
    else:
        print("Cliente Gemini API não inicializado devido à falta de chaves.")


# --- 4. FUNÇÕES PARA INJEÇÃO DE DEPENDÊNCIA ---
def get_azure_client():
    """
    Função geradora usada pelo FastAPI Depends() para injetar
    o cliente autenticado do Azure AI nas rotas.
    """
    global ai_client
    if not ai_client:
        raise HTTPException(
            status_code=503, 
            detail="Serviço Azure AI Language não está disponível ou não foi autenticado."
        )
    yield ai_client

# NOVA: Função de dependência para o Gemini
def get_gemini_client():
    """
    Função geradora usada pelo FastAPI Depends() para injetar
    o cliente autenticado do Gemini nas rotas.
    """
    global gemini_client
    if not gemini_client:
        raise HTTPException(
            status_code=503, 
            detail="Serviço Gemini API não está disponível ou não foi autenticado."
        )
    yield gemini_client


# --- 5. ROTA DE SAUDAÇÃO E STATUS (CORRIGE O 404 NA RAIZ) ---

@app.get("/", tags=["Status"])
def read_root():
    """
    Rota de saudação. Verifica se a API está respondendo.
    """
    return {"message": "Bem-vindo à API do TCC Acertus. Acesse /docs para a documentação interativa."}

@app.get("/status", tags=["Status"])
def api_status():
    """
    Verifica o status da API, da conexão com o Azure AI e com o Gemini.
    """
    status = {
        "api_online": True,
        "azure_ai_client_ready": ai_client is not None,
        "gemini_client_ready": gemini_client is not None # NOVA: Status do Gemini
    }
    return status

# --- 6. ROTA LOCAL DE FEEDBACKS ---
# Mantida a rota de feedbacks para ser usada pela rota Gemini
@app.get("/feedbacks", tags=["Feedbacks"], response_model=List[Dict[str, str]])
def listar_feedbacks():
    """
    Lista todos os feedbacks lidos dos arquivos .txt na pasta ./feedbacks/
    """
    pasta_feedbacks = "./feedbacks/"
    feedbacks: List[Dict[str, str]] = []

    # Se a pasta não existir, retorna vazio
    if not os.path.exists(pasta_feedbacks):
        return []

    # Lê os arquivos da pasta
    for arquivo in os.listdir(pasta_feedbacks):
        if arquivo.endswith(".txt"):
            caminho = os.path.join(pasta_feedbacks, arquivo)
            try:
                # Usamos 'with open' para garantir que o arquivo seja fechado
                with open(caminho, "r", encoding="utf-8") as f:
                    texto = f.read().strip()
                feedbacks.append({"Arquivo": arquivo, "Feedback": texto})
            except Exception as e:
                print(f"Erro ao ler o arquivo {arquivo}: {e}")
                feedbacks.append({"Arquivo": arquivo, "Feedback": f"ERRO: Não foi possível ler o arquivo. {e}"})

    # Converte para DataFrame e depois para lista de dicionários
    df_feedbacks = pd.DataFrame(feedbacks)
    return df_feedbacks.to_dict(orient="records")
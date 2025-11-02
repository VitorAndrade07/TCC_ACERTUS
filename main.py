from fastapi import FastAPI
import os
import pandas as pd
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
from dotenv import load_dotenv
from routes.routes import router # Importa o router

# --- 1. CONFIGURAÇÃO DA APLICAÇÃO ---
app = FastAPI(title="Minha API de TCC")
app.include_router(router) # Inclui suas rotas


load_dotenv()
# As variáveis AI_KEY e AI_ENDPOINT devem ser definidas no seu arquivo .env
ai_key = os.getenv("AI_KEY")
ai_endpoint = os.getenv("AI_ENDPOINT")

# Variável global para armazenar o cliente do Azure AI
ai_client = None


@app.on_event("startup")
def startup_event():
    """
    Função executada na inicialização do servidor.
    Cria e autentica o cliente do Azure AI Language.
    """
    global ai_client
    try:
        credential = AzureKeyCredential(ai_key)
        # Cria a instância do cliente Azure AI Language
        ai_client = TextAnalyticsClient(endpoint=ai_endpoint, credential=credential)
        print("Cliente autenticado com sucesso.")
    except Exception as ex:
        # Se houver erro de credenciais, ele aparecerá aqui
        print("Erro na autenticação do cliente:", ex)


# --- 2. FUNÇÃO PARA INJEÇÃO DE DEPENDÊNCIA ---
def get_azure_client():
    """
    Função geradora usada pelo FastAPI Depends() para injetar
    o cliente autenticado do Azure AI nas rotas.
    """
    global ai_client
    yield ai_client


# --- 3. ROTA LOCAL DE FEEDBACKS ---
@app.get("/feedbacks")
def listar_feedbacks():
    """
    Lista todos os feedbacks lidos dos arquivos .txt na pasta ./feedbacks/
    """
    pasta_feedbacks = "./feedbacks/"
    feedbacks = []

    # Se a pasta não existir, retorna vazio
    if not os.path.exists(pasta_feedbacks):
        return []

    for arquivo in os.listdir(pasta_feedbacks):
        if arquivo.endswith(".txt"):
            caminho = os.path.join(pasta_feedbacks, arquivo)
            with open(caminho, "r", encoding="utf-8") as f:
                texto = f.read().strip()
                feedbacks.append({"Arquivo": arquivo, "Feedback": texto})
    
    # Converte para DataFrame e depois para lista de dicionários
    df_feedbacks = pd.DataFrame(feedbacks)
    return df_feedbacks.to_dict(orient="records")
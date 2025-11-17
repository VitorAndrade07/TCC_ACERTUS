from fastapi import FastAPI, Depends, HTTPException
import os
import pandas as pd
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
from dotenv import load_dotenv
from typing import Dict, Any, List
# Importamos o router que deve conter a rota para os Estilos de Formatação
from routes.routes import router 

# --- 1. CONFIGURAÇÃO INICIAL E VARIÁVEIS DE AMBIENTE ---
load_dotenv()
AI_KEY = os.getenv("AI_KEY")
AI_ENDPOINT = os.getenv("AI_ENDPOINT")

# Certifique-se de que as chaves estão presentes
if not AI_KEY or not AI_ENDPOINT:
    print("AVISO: Chaves 'AI_KEY' ou 'AI_ENDPOINT' não encontradas no .env. O cliente Azure não será autenticado.")
    # Usaremos None, e o status/startup_event irá reportar o erro.

# --- 2. INICIALIZAÇÃO DO APP E INCLUSÃO DE ROTAS ---
app = FastAPI(
    title="Minha API de TCC - ACERTUS",
    description="API para análise de feedback e processamento de texto utilizando Azure AI Language.",
    version="1.0.0"
)

# Inclui o roteador (onde deve estar a rota de Estilos de Formatação)
app.include_router(router) 

ai_client = None

# --- 3. EVENTO DE INICIALIZAÇÃO (SETUP DA AZURE AI) ---
@app.on_event("startup")
def startup_event():
    """
    Função executada na inicialização do servidor.
    Cria e autentica o cliente do Azure AI Language.
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


# --- 4. FUNÇÃO PARA INJEÇÃO DE DEPENDÊNCIA ---
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
    Verifica o status da API e da conexão com o Azure AI.
    """
    status = {
        "api_online": True,
        "azure_ai_client_ready": ai_client is not None
    }
    return status

# --- 6. ROTA LOCAL DE FEEDBACKS ---
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
    # Note: O uso de pandas para esta conversão simples não é ideal, 
    # mas mantive a sua lógica. Para performance, seria melhor retornar a lista 'feedbacks' diretamente.
    df_feedbacks = pd.DataFrame(feedbacks)
    return df_feedbacks.to_dict(orient="records")
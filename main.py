from fastapi import FastAPI, Depends, HTTPException
import os
import pandas as pd
from dotenv import load_dotenv
from typing import Dict, Any, List
import math # Importado para uso geral, pode ser útil em outras rotas ou aqui.

# Importamos o router que deve conter a rota para os Estilos de Formatação
from routes.routes import router 

# Importa as funções de injeção de dependência e a função de inicialização
from clients import initialize_clients, get_azure_client, get_gemini_model, ai_client, gemini_model_instance

# --- 1. CONFIGURAÇÃO INICIAL E VARIÁVEIS DE AMBIENTE ---
# As variáveis de ambiente serão carregadas em clients.py, então removemos daqui
load_dotenv() # Manter para garantir que outros módulos também carreguem se precisarem

# --- 2. INICIALIZAÇÃO DO APP E INCLUSÃO DE ROTAS ---
app = FastAPI(
    title="Minha API de TCC - ACERTUS",
    description="API para análise de feedback e processamento de texto utilizando Azure AI Language.",
    version="1.0.0"
)

# Inclui o roteador
app.include_router(router) 

# --- 3. EVENTO DE INICIALIZAÇÃO (SETUP DA AZURE AI E GEMINI) ---
@app.on_event("startup")
def startup_event():
    """
    Função executada na inicialização do servidor.
    Chama a função de inicialização dos clientes de IA.
    """
    initialize_clients() # Chama a função que agora está em clients.py

# --- As funções get_azure_client e get_gemini_model foram movidas para clients.py ---
# Então, removemos as definições delas daqui.

# --- 5. ROTA DE SAUDAÇÃO E STATUS ---

@app.get("/", tags=["Status"])
def read_root():
    """
    Rota de saudação. Verifica se a API está respondendo.
    """
    return {"message": "Bem-vindo à API do TCC Acertus. Acesse /docs para a documentação interativa."}

@app.get("/status", tags=["Status"])
def api_status():
    """
    Verifica o status da API e da conexão com o Azure AI e Gemini.
    """
    # Agora usamos as variáveis globais de clients.py
    status = {
        "api_online": True,
        "azure_ai_client_ready": ai_client is not None,
        "gemini_model_ready": gemini_model_instance is not None 
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
                with open(caminho, "r", encoding="utf-8") as f:
                    texto = f.read().strip()
                feedbacks.append({"Arquivo": arquivo, "Feedback": texto})
            except Exception as e:
                print(f"Erro ao ler o arquivo {arquivo}: {e}")
                feedbacks.append({"Arquivo": arquivo, "Feedback": f"ERRO: Não foi possível ler o arquivo. {e}"})

    df_feedbacks = pd.DataFrame(feedbacks)
    return df_feedbacks.to_dict(orient="records")
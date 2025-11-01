import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
from dotenv import load_dotenv

# Carrega .env uma segunda vez para garantir, caso o main.py não o tenha feito.
load_dotenv() 

# Credenciais lidas do .env
AI_KEY = os.getenv("AI_KEY")
AI_ENDPOINT = os.getenv("AI_ENDPOINT")

# Variável global para armazenar o cliente, evitando recriá-lo a cada requisição
# Inicializamos como None
ai_client = None

def get_text_analytics_client():
    """
    Cria ou retorna o cliente autenticado do Azure AI Language Service.
    A autenticação só ocorre na primeira vez que esta função é chamada.
    """
    global ai_client
    if ai_client is None:
        try:
            # A AUTENTICAÇÃO E CRIAÇÃO DO CLIENTE SÓ ACONTECE AQUI DENTRO DA FUNÇÃO
            credential = AzureKeyCredential(AI_KEY)
            ai_client = TextAnalyticsClient(endpoint=AI_ENDPOINT, credential=credential)
            print("Cliente Azure AI Language autenticado com sucesso.")
        except Exception as ex:
            # Em vez de imprimir e continuar, levantamos o erro para o FastAPI
            print(f"ERRO: Falha na autenticação do cliente Azure: {ex}")
            raise Exception("Falha ao inicializar o cliente Azure AI Language.")
    
    return ai_client


def analyze_sentiment(text: str):
    """
    Recebe um texto e envia para análise de sentimento.
    """
    # 1. Obtém o cliente (autentica se ainda não foi feito)
    client = get_text_analytics_client()

    # 2. Chama a API do Azure
    documents = [text]
    try:
        response = client.analyze_sentiment(documents=documents)[0]
    except Exception as e:
        # Se a chamada à API falhar, retornamos um erro claro.
        return {
            "error": "Falha na chamada da API de Sentimento do Azure.",
            "details": str(e)
        }

    # 3. Processa e retorna o resultado
    return {
        "sentimento_geral": response.sentiment.capitalize(),
        "pontuacoes_confianca": {
            "positivo": response.confidence_scores.positive,
            "negativo": response.confidence_scores.negative,
            "neutro": response.confidence_scores.neutral,
        },
        "detalhes_frase": [
            {
                "texto": sentence.text,
                "sentimento": sentence.sentiment.capitalize(),
                "positivo": sentence.confidence_scores.positive,
                "negativo": sentence.confidence_scores.negative,
                "neutro": sentence.confidence_scores.neutral,
            }
            for sentence in response.sentences
        ]
    }
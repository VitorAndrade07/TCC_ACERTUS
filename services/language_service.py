import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
from dotenv import load_dotenv

# Variável para armazenar o cliente, evitando recriá-lo a cada requisição
ai_client = None

def get_text_analytics_client():
    """
    Cria ou retorna o cliente autenticado do Azure AI Language Service.
    A autenticação só ocorre na primeira vez que esta função é chamada (lazy loading).
    """
    global ai_client
    if ai_client is None:
        load_dotenv()
        
        # Credenciais lidas do .env
        AI_KEY = os.getenv("AI_KEY")
        AI_ENDPOINT = os.getenv("AI_ENDPOINT")
        
        if not AI_KEY or not AI_ENDPOINT:
            raise Exception("Chaves AI_KEY ou AI_ENDPOINT não encontradas no .env.")
            
        try:
            # A AUTENTICAÇÃO E CRIAÇÃO DO CLIENTE SÓ ACONTECE AQUI
            credential = AzureKeyCredential(AI_KEY)
            ai_client = TextAnalyticsClient(endpoint=AI_ENDPOINT, credential=credential)
            # NÃO COLOCAMOS PRINT DE SUCESSO AQUI PARA NÃO ATRAPALHAR O UVICORN
        except Exception as ex:
            raise Exception(f"ERRO: Falha na autenticação do cliente Azure: {ex}")
    
    return ai_client


def analyze_sentiment(text: str):
    """
    Recebe um texto e envia para análise de sentimento.
    """
    client = get_text_analytics_client()

    documents = [text]
    try:
        response = client.analyze_sentiment(documents=documents)[0]
    except Exception as e:
        return {
            "error": "Falha na chamada da API de Sentimento do Azure.",
            "details": str(e)
        }

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

def extract_key_phrases(text: str):
    """
    Recebe um texto e extrai as frases-chave para resumo.
    """
    client = get_text_analytics_client()

    documents = [text]
    try:
        # A API de Frases-Chave é usada aqui
        response = client.extract_key_phrases(documents=documents)[0]
    except Exception as e:
        return {
            "error": "Falha na chamada da API de Extração de Frases-Chave do Azure.",
            "details": str(e)
        }
    
    # Retorna a lista de frases-chave
    return {"frases_chave": response.key_phrases}
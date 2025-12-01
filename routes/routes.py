# routes/routes.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

# Importa os serviços que você já tem
from services.language_service import extract_key_phrases 
# Importa as funções de injeção de dependência do NOVO arquivo clients.py
from clients import get_azure_client, get_gemini_model 

import google.generativeai as genai
import math # Para arredondamento das porcentagens
import asyncio
from concurrent.futures import ThreadPoolExecutor

router = APIRouter()

# Modelo Pydantic para requisições de texto, mantido para outras rotas se houver
class TextRequest(BaseModel):
    text: str

    class Config:
        schema_extra = {"example": {"text": "A equipe de suporte foi incrível, mas o produto travou duas vezes. Precisa melhorar!"}}


def run_in_executor(func, *args):
    """
    Função auxiliar para executar código síncrono (bloqueante)
    em um thread separado, tornando-o assíncrono para o FastAPI.
    """
    loop = asyncio.get_event_loop()
    # None usa o ThreadPoolExecutor padrão do FastAPI
    return loop.run_in_executor(None, func, *args)

# --- Rota para Análise de Sentimento (Azure AI Language) - OTIMIZADA PARA LISTA DE TEXTOS ---
@router.post("/analyze/sentiment", tags=["Analysis"])
def analyze_sentiment_batch(
    texts: List[str], # O Flask envia uma lista de strings
    ai_client = Depends(get_azure_client) # Injeta o cliente Azure AI de clients.py
) -> Dict[str, float]:
    """
    Realiza a análise de sentimento para uma lista de textos em lote e retorna as porcentagens
    de positivo, neutro e negativo.
    """
    if not texts:
        return {"positive": 0.0, "neutral": 0.0, "negative": 0.0}

    try:
        response = ai_client.analyze_sentiment(documents=texts, language="pt")

        positive_count = 0
        neutral_count = 0
        negative_count = 0
        total_analyzed = 0

        for doc in response:
            if not doc.is_error:
                total_analyzed += 1
                if doc.sentiment == "positive":
                    positive_count += 1
                elif doc.sentiment == "neutral":
                    neutral_count += 1
                elif doc.sentiment == "negative":
                    negative_count += 1

        if total_analyzed == 0:
            return {"positive": 0.0, "neutral": 0.0, "negative": 0.0}

        positive_percent = round((positive_count / total_analyzed) * 100, 1)
        neutral_percent = round((neutral_count / total_analyzed) * 100, 1)
        negative_percent = round((negative_count / total_analyzed) * 100, 1)

        return {
            "positive": positive_percent,
            "neutral": neutral_percent,
            "negative": negative_percent
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro na análise de sentimento do Azure: {str(e)}"
        )

# --- Rota para Geração de Resumo (Google Gemini) ---
@router.post("/generate/summary", tags=["Generation"])
def generate_summary_for_flask(
    texts: List[str], # O Flask envia uma lista de strings
    gemini_model: Any = Depends(get_gemini_model) # Injeta a instância do modelo Gemini de clients.py
) -> Dict[str, str]:
    """
    Gera um resumo consolidado a partir de uma lista de textos utilizando o Google Gemini.
    """
    if not texts:
        return {"summary_text": "Nenhum texto fornecido para resumo."}

    try:
        combined_text = "\n".join(texts)
        
        prompt = f"Consolide e resuma os seguintes feedbacks em português, mantendo as informações mais importantes e o tom geral. Se houver poucas respostas, apenas reformule-as brevemente. Não adicione saudações ou frases introdutórias, vá direto ao resumo:\n\n{combined_text}"

        response = gemini_model.generate_content(prompt)
        
        if response and response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            summary_text = response.candidates[0].content.parts[0].text
            return {"summary_text": summary_text}
        else:
            return {"summary_text": "Não foi possível gerar um resumo a partir dos feedbacks."}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro na geração do resumo do Gemini: {str(e)}"
        )

# --- Exemplo de Rota para Extração de Frases-Chave (se o Flask precisar dela) ---
@router.post("/extract/keyphrases", tags=["Analysis"])
async def extract_keyphrases_single_text(
    request: TextRequest,
    client = Depends(get_azure_client)
) -> Dict[str, List[str]]:
    """
    Extrai as frases e palavras-chave principais de um único texto.
    """
    if not request.text:
        return {"key_phrases": []}
    
    result = extract_key_phrases(client, request.text)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@router.post("/analyze/full", tags=["Analysis"])
async def analyze_full_batch(
    texts: List[str], 
    ai_client = Depends(get_azure_client), 
    gemini_model: Any = Depends(get_gemini_model)
) -> Dict[str, Any]:
    """
    Realiza a análise de Sentimento (Azure) e a Geração de Resumo (Gemini)
    SIMULTANEAMENTE para uma lista de textos.
    """
    if not texts:
        return {
            "sentiment": {"positive": 0.0, "neutral": 0.0, "negative": 0.0},
            "summary": {"summary_text": "Nenhum texto fornecido para análise."}
        }

    # 1. Empacota as chamadas síncronas para serem executadas em paralelo
    # Isso transforma suas funções síncronas em "tarefas" assíncronas
    
    # Chamada 1: Sentimento (Síncrona, rodando em thread paralelo)
    sentiment_task = run_in_executor(
        # Note que chamamos a função síncrona que JÁ EXISTE no seu arquivo:
        analyze_sentiment_batch, 
        texts, 
        ai_client
    )
    
    # Chamada 2: Resumo (Síncrona, rodando em thread paralelo)
    summary_task = run_in_executor(
        # Note que chamamos a função síncrona que JÁ EXISTE no seu arquivo:
        generate_summary_for_flask, 
        texts, 
        gemini_model
    )
    
    try:
        # 2. Roda as duas tarefas em paralelo e espera o resultado da mais lenta
        # O `await asyncio.gather(...)` é o comando que executa em paralelo.
        sentiment_result, summary_result = await asyncio.gather(sentiment_task, summary_task)
        
        return {
            "sentiment": sentiment_result,
            "summary": summary_result
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro durante a execução paralela das análises: {str(e)}"
        )
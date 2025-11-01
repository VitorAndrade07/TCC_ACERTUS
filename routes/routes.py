import os
from fastapi import APIRouter
from pydantic import BaseModel
from services.language_service import analyze_sentiment, extract_key_phrases

# Define o prefixo e as tags para todas as rotas neste arquivo
router = APIRouter(prefix="/api", tags=["Azure AI Language"])

# Define o modelo de dados de entrada
class TextRequest(BaseModel):
    text: str
    
    class Config:
        schema_extra = {"example": {"text": "A equipe de suporte foi incrível, mas o produto travou duas vezes. Precisa melhorar!"}}


@router.post("/sentiment")
def post_analyze_sentiment(request: TextRequest):
    """
    Analisa o sentimento de um texto (positivo, negativo, neutro).
    """
    result = analyze_sentiment(request.text)
    return result

@router.post("/keyphrases")
def post_extract_key_phrases(request: TextRequest):
    """
    Extrai as frases e termos mais importantes de um texto para gerar um resumo.
    """
    result = extract_key_phrases(request.text)
    return result
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from services.language_service import analyze_sentiment, extract_key_phrases
from services.azure_client import get_azure_client  # Importa do módulo separado
import google.generativeai as genai
from fastapi import HTTPException

router = APIRouter(prefix="/api", tags=["Azure AI Language"])

class TextRequest(BaseModel):
    text: str

    class Config:
        schema_extra = {"example": {"text": "A equipe de suporte foi incrível, mas o produto travou duas vezes. Precisa melhorar!"}}


@router.post("/sentiment")
def post_analyze_sentiment(
    request: TextRequest,
    client = Depends(get_azure_client)
):
    result = analyze_sentiment(client, request.text)
    return result


@router.post("/keyphrases")
def post_extract_key_phrases(
    request: TextRequest,
    client = Depends(get_azure_client)
):
    result = extract_key_phrases(client, request.text)
    return result

@router.post("/gemini/generate", tags=["Gemini"])
def gerar_conteudo(request: TextRequest):
    """
    Gera conteúdo com base em um prompt usando o modelo Gemini AI.
    """
    try:
        model = genai.GenerativeModel("models/gemini-pro-latest")
        response = model.generate_content(request.text)
        return {"prompt": request.text, "resposta": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar conteúdo com Gemini AI: {e}")
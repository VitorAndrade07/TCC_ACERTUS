def analyze_sentiment(client, text: str): # <--- AGORA RECEBE O CLIENTE
    """
    Analisa o sentimento (positivo, negativo, neutro) do texto.
    """
    try:
        response = client.analyze_sentiment(documents=[text])[0]
        return {
            "sentiment": response.sentiment,
            "positive": response.confidence_scores.positive,
            "neutral": response.confidence_scores.neutral,
            "negative": response.confidence_scores.negative
        }
    except Exception as e:
        return {"error": str(e)}

def extract_key_phrases(client, text: str): # <--- AGORA RECEBE O CLIENTE
    """
    Extrai as frases e palavras-chave principais do texto.
    """
    try:
        response = client.extract_key_phrases(documents=[text])[0]
        return {"key_phrases": response.key_phrases}
    except Exception as e:
        return {"error": str(e)}
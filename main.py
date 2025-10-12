import os
import pandas as pd
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
from dotenv import load_dotenv

# Obtendo as variáveis de ambiente principais e conectando ao serviço
load_dotenv()
ai_key = os.getenv("AI_KEY")
ai_endpoint = os.getenv("AI_ENDPOINT")

# Autenticação do cliente
try:       
    credential = AzureKeyCredential(ai_key)
    ai_client = TextAnalyticsClient(endpoint=ai_endpoint, credential=credential)
except Exception as ex:
    print("Erro na autenticação do cliente:", ex)
else:
    print("Cliente autenticado com sucesso.")

#carregando os dados
pasta_feedbacks = "./feedbacks/"

# Lista para armazenar feedbacks
feedbacks = []

# Percorrer todos os arquivos da pasta
for arquivo in os.listdir(pasta_feedbacks):
    if arquivo.endswith(".txt"): # considerando apenas arquivos de texto
        caminho = os.path.join(pasta_feedbacks, arquivo)
        with open(caminho, "r", encoding="utf-8") as f:
            texto = f.read().strip()
            feedbacks.append({"Arquivo": arquivo, "Feedback": texto})
# Criar DataFrame
df_feedbacks = pd.DataFrame(feedbacks)
df_feedbacks
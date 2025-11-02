from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
import os

def get_azure_client():
    endpoint = os.getenv("AI_ENDPOINT")
    key = os.getenv("AI_KEY")
    client = TextAnalyticsClient(endpoint=endpoint, credential=AzureKeyCredential(key))
    return client
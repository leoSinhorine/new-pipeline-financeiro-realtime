import os
import requests
from datetime import datetime
from google.cloud import bigquery
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET_ID = "raw_data"

# Moedas para buscar histórico de 30 dias
MOEDAS = ["USD", "EUR", "BTC"]

def carregar_historico_30_dias():
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        for moeda in MOEDAS:
            print(f"📡 Buscando histórico de 30 dias para {moeda}-BRL...")
            url = f"https://economia.awesomeapi.com.br/json/daily/{moeda}-BRL/30"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            dados_historicos = response.json()
            tabela_nome = f"{moeda.lower()}brl"
            table_ref = f"{PROJECT_ID}.{DATASET_ID}.raw_{tabela_nome}"
            
            registros = []
            for dados in dados_historicos:
                # Converte o timestamp UNIX da API para o formato ISO
                ts = datetime.fromtimestamp(int(dados['timestamp'])).isoformat()
                
                registro = {
                    "timestamp": ts,
                    "moeda": moeda,
                    "bid": float(dados['bid']),
                    "ask": float(dados['ask'])
                }
                registros.append(registro)
            
            # Configuração de carga no BigQuery
            job_config = bigquery.LoadJobConfig(
                schema=[
                    bigquery.SchemaField("timestamp", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("moeda", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("bid", "FLOAT", mode="REQUIRED"),
                    bigquery.SchemaField("ask", "FLOAT", mode="REQUIRED"),
                ],
                write_disposition="WRITE_APPEND", # Adiciona ao histórico atual
            )
            
            print(f"📥 Carregando {len(registros)} registros históricos de {moeda} no BigQuery...")
            load_job = client.load_table_from_json(registros, table_ref, job_config=job_config)
            load_job.result() # Aguarda a inserção no GCP
            print(f"✅ Histórico de {moeda} inserido com sucesso!")
            
    except Exception as e:
        print(f"❌ Erro ao processar carga histórica: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando Carga Única de Histórico (30 Dias)...")
    carregar_historico_30_dias()
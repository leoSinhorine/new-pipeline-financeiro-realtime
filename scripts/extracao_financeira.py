import os
from datetime import datetime
import pandas as pd
import pytz
import requests
from dotenv import load_timerenv  # Carrega variáveis do arquivo .env
from sqlalchemy import create_engine

# Carrega as configurações do arquivo .env local
load_dotenv()

# --- CONFIGURAÇÕES ---
URL_API = "https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL,BTC-BRL"

# Configuração segura do banco (Lendo das variáveis de ambiente)
USUARIO = os.getenv("DB_USER")
SENHA = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOST")
PORTA = os.getenv("DB_PORT")
BANCO = os.getenv("DB_NAME")

# Instanciação segura da engine de conexão do banco relacional de staging
engine = create_engine(
    f"postgresql://{USUARIO}:{SENHA}@{HOST}:{PORTA}/{BANCO}"
)

# Configuração do Timezone local de Brasília para logs e registros precisos
FUSO_BR = pytz.timezone("America/Sao_Paulo")


def extrair_dados_api():
    hora_atual = datetime.now(FUSO_BR).strftime("%H:%M:%S")
    print(f"📡 [{hora_atual}] Acessando API AwesomeAPI...")

    response = requests.get(URL_API)

    if response.status_code == 200:
        dados_json = response.json()
        lista_formatada = []

        # Percorrendo os pares de moedas retornados (USDBRL, EURBRL, BTCBRL)
        for par in dados_json.values():
            lista_formatada.append(
                {
                    "moeda": par["code"],
                    "valor_bid": float(par["bid"]),
                    "valor_ask": float(par["ask"]),
                    "data_consulta": datetime.now(
                        FUSO_BR
                    ),  # Garante data certa na nuvem
                }
            )

        return pd.DataFrame(lista_formatada)
    else:
        print("❌ Erro ao acessar a API.")
        return None


# --- EXECUÇÃO DO PIPELINE ---
try:
    df_moedas = extrair_dados_api()

    if df_moedas is not None:
        print(f"✅ Extração concluída: {len(df_moedas)} moedas encontradas.")

        # Carga no banco: Usamos 'append' para guardar o histórico incremental!
        print("📥 Salvando histórico no banco de dados...")
        df_moedas.to_sql(
            "cotacoes_moedas", engine, if_exists="append", index=False
        )

        print("🚀 Pipeline financeiro executado com sucesso!")
        print(df_moedas[["moeda", "valor_bid"]])

except Exception as e:
    print(f"❌ Erro no processo: {e}")
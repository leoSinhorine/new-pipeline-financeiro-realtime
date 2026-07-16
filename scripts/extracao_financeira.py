import requests
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

# --- CONFIGURAÇÕES ---
# API que traz Dólar, Euro e Bitcoin em tempo real
URL_API = "https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL,BTC-BRL"

# Configuração do banco (Ajuste sua senha aqui)
USUARIO = 'postgres'
SENHA = '2806'
HOST = 'localhost'
PORTA = '5432'
BANCO = 'dw_financeiro'

engine = create_engine(f'postgresql://{USUARIO}:{SENHA}@{HOST}:{PORTA}/{BANCO}')

def extrair_dados_api():
    print(f"📡 [{datetime.now().strftime('%H:%M:%S')}] Acessando API AwesomeAPI...")
    
    response = requests.get(URL_API)
    
    if response.status_code == 200:
        dados_json = response.json()
        
        lista_formatada = []
        
        # Percorrendo os pares de moedas retornados (USDBRL, EURBRL, BTCBRL)
        for par in dados_json.values():
            lista_formatada.append({
                "moeda": par['code'],
                "valor_bid": float(par['bid']),
                "valor_ask": float(par['ask']),
                "data_consulta": datetime.now()
            })
        
        return pd.DataFrame(lista_formatada)
    else:
        print("❌ Erro ao acessar a API.")
        return None

# --- EXECUÇÃO ---
try:
    df_moedas = extrair_dados_api()
    
    if df_moedas is not None:
        print(f"✅ Extração concluída: {len(df_moedas)} moedas encontradas.")
        
        # Carga no banco: Usamos 'append' para guardar o histórico!
        print("📥 Salvando histórico no banco de dados...")
        df_moedas.to_sql('cotacoes_moedas', engine, if_exists='append', index=False)
        
        print("🚀 Pipeline financeiro executado com sucesso!")
        print(df_moedas[['moeda', 'valor_bid']])
        
except Exception as e:
    print(f"❌ Erro no processo: {e}")
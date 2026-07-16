# 📡 Real-Time Financial Data Pipeline (USD, EUR, BTC)

Este projeto demonstra a construção de um pipeline de dados completo para monitorização de moedas em tempo real. O sistema extrai dados de uma API financeira, processa-os em Python e armazena-os num Data Warehouse PostgreSQL para visualização analítica.

## 🚀 Arquitetura do Projeto

1.  **Ingestão de Dados**: Script Python utilizando a biblioteca `requests` para consumir a API REST da AwesomeAPI.
2.  **Processamento**: Utilização do `Pandas` para limpeza e estruturação dos dados em formato tabular.
3.  **Armazenamento**: Persistência de dados num banco PostgreSQL utilizando `SQLAlchemy`. O pipeline utiliza a estratégia de carga incremental (`append`) para criar um histórico temporal (Time-Series).
4.  **Visualização**: Dashboard interativo no Power BI para análise de volatilidade e tendências de mercado.

## 🛠️ Tecnologias Utilizadas

* **Linguagem**: Python 3.x
* **Bibliotecas**: Pandas, SQLAlchemy, Requests
* **Base de Dados**: PostgreSQL
* **BI**: Power BI Desktop

## 📂 Estrutura de Pastas

```text
├── scripts/          # Código Python de extração e carga
├── sql/              # Scripts DDL para criação das tabelas
├── dashboard/        # Arquivo .pbix do Power BI
├── requirements.txt  # Dependências do projeto
└── README.md         # Documentação
# 📈 Monitor de Cotações Real-Time & Analytics (Modern Data Stack)

[![Streamlit App](/screenshots/Monitor%20de%20Cotações%20_%20Real-time%20·%20Streamlit%20-%20Brave%2016_07_2026%2013_36_31.png)
[![Database](/screenshots/Monitor%20de%20Cotações%20_%20Real-time%20·%20Streamlit%20-%20Brave%2016_07_2026%2013_35_55.png)


Uma plataforma analítica robusta de alta performance para monitoramento histórico e em tempo real de ativos globais (Dólar, Euro e Bitcoin). O ecossistema foi projetado de ponta a ponta seguindo as melhores práticas de **Engenharia de Dados** e **Engenharia de Software**, conectando um fluxo de ingestão dinâmico diretamente ao data warehouse em nuvem do Google, modelagem estatística avançada e uma interface rica e altamente responsiva.

---

## 🛠️ Arquitetura do Ecossistema (Modern Data Stack)

O fluxo de dados foi projetado para separar as responsabilidades de processamento em camadas independentes, garantindo escalabilidade e facilidade de manutenção:

[APIs Financeiras] ──(Python: Ingestão)──> [Google BigQuery] ──(dbt: Transformação)──> [OBT Analítica] ──> [Streamlit UI]


1. **Ingestão e Carga (EL):** Script em Python de alta frequência captura os dados brutos de APIs de mercado e descarrega de forma incremental diretamente no **Google BigQuery**.
2. **Data Lakehouse:** Armazenamento centralizado e serverless no **Google BigQuery** para queries distribuídas de baixa latência.
3. **Modelagem de Dados (T):** O **dbt (data build tool)** orquestra as transformações analíticas agregadas (cálculo de spreads, variações e médias móveis de 7 e 30 dias), gerando a tabela consolidada denormalizada no formato **OBT (One Big Table)**.
4. **Camada de Entrega (BI/App):** Aplicação interativa em **Streamlit** que consome a tabela OBT final de forma ultra performática.

---

## 📦 Estrutura do Repositório

```text
├── .github/                  # Configurações de CI/CD
├── finance_analytics/        # Diretório do projeto dbt
│   ├── analyses/
│   ├── macros/               # Lógicas SQL reutilizáveis
│   ├── models/
│   │   ├── marts/            # Tabelas de fatos, dimensões e a OBT final
│   │   └── staging/          # Views de saneamento dos dados brutos
│   └── dbt_project.yml       # Configuração global do dbt
├── screenshots/              # Prints de demonstração da interface
├── scripts/                  # Scripts de ingestão e carga de dados
│   ├── carga_historica.py    # Carga de dados passados
│   └── extracao_financeira.py# Script principal de ingestão (AwesomeAPI -> BigQuery)
├── .env.example              # Exemplo de variáveis de ambiente do projeto
├── .gitignore                # Exclusão segura de chaves privadas e configs locais
├── app.py                    # Aplicação principal do Dashboard (Streamlit)
├── README.md                 # Documentação técnica do projeto
└── requirements.txt          # Dependências do ambiente produtivo Linux
🛡️ Engenharia de Produção & Boas Práticas (Cloud & DevOps)
1. FinOps (Otimização de Custos em Nuvem)
Consultas diretas a Data Warehouses como o BigQuery são cobradas pelo volume de dados varridos. Para mitigar custos operacionais, a camada de front-end implementa uma estratégia rígida de caching de dados (@st.cache_data(ttl=600)). Os dados são guardados em memória no servidor do app e renovados automaticamente a cada 10 minutos. Isso faz com que interações repetidas de filtros e gráficos consumam cache local, reduzindo a zero o custo de processamento de queries na nuvem do Google.

2. SecOps (Segurança da Informação)
O caminho das chaves de conta de serviço do Google Cloud Platform (GCP) é isolado via variáveis de ambiente (.env). Em ambiente de produção, a conexão com o BigQuery é estabelecida de forma totalmente segura e assíncrona consumindo Secrets criptografados nativos do Streamlit Cloud (st.secrets). Nenhuma chave privada foi exposta no histórico do Git.

3. Sincronização Global de Timestamps
Para evitar dessincronizações entre o relógio físico do servidor de hospedagem (geralmente configurado no horário internacional UTC) e o usuário final, foi implementado o controle de timezone geográfico via biblioteca pytz (America/Sao_Paulo). Os registros de atualização do cache e logs do pipeline refletem milimetricamente o horário oficial de Brasília.

🎨 Engenharia de UI/UX & Responsividade
O painel foi desenhado para oferecer a usabilidade e o refino estético de grandes plataformas de investimentos do mercado:

Modo Escuro / Claro Dinâmico: O aplicativo possui uma folha de estilo customizada via CSS injetado que se adapta ao tema ativo do usuário. O tema escuro traz tons profundos e acentos em neon vibrante de acordo com o ativo selecionado (Verde para USD, Ciano para EUR, Âmbar para BTC), enquanto o tema claro traz uma paleta terrosa e pastéis de altíssimo contraste.

Componentes Responsivos Mobile: Para telas de smartphones menores que 991px, criamos uma folha de estilo responsiva avançada utilizando regras de @media no CSS. O menu lateral nativo de filtros é colapsado por padrão e acionado por um botão de hambúrguer flutuante neon e botão de voltar com tamanho de clique expandido para melhor acessibilidade ao toque.

Gráficos Interativos Inteligentes: Implementação de séries temporais financeiras ricas com Plotly, contendo anotações automáticas e flutuantes apontando os picos máximos e mínimos do período filtrado.

🚀 Como Executar o Projeto Localmente
1. Pré-requisitos
Certifique-se de ter o Python 3.12+ instalado na sua máquina local e uma conta ativa no Google Cloud Platform com acesso ao BigQuery.

2. Clonar o Repositório
Bash
git clone [https://github.com/leosinhorine/new-pipeline-financeiro-realtime.git](https://github.com/leosinhorine/new-pipeline-financeiro-realtime.git)
cd new-pipeline-financeiro-realtime
3. Configurar Variáveis de Ambiente
Crie um arquivo .env na raiz do projeto (use o .env.example como guia) e preencha com as credenciais do seu projeto no GCP:

Plaintext
GCP_PROJECT_ID=finance-analytics-engineering
GOOGLE_APPLICATION_CREDENTIALS=scripts/gcp_key.json
4. Instalar Dependências e Executar
Bash
# Instalar dependências necessárias
pip install -r requirements.txt

# Executar o script de ingestão (AwesomeAPI -> Google BigQuery)
python scripts/extracao_financeira.py

# Iniciar o painel interativo do Streamlit
streamlit run app.py
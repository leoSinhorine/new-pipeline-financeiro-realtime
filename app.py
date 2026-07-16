import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import plotly.graph_objects as go
from datetime import datetime


def hex_para_rgba(cor_hex, alpha=0.13):
    """Converte um hex '#rrggbb' para o formato 'rgba(r,g,b,a)' aceito pelo Plotly/CSS."""
    cor_hex = cor_hex.lstrip("#")
    r, g, b = int(cor_hex[0:2], 16), int(cor_hex[2:4], 16), int(cor_hex[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

# =========================================================================
# 1. CONFIGURAÇÃO BÁSICA DA PÁGINA
# =========================================================================
st.set_page_config(
    page_title="Monitor de Cotações | Real-time",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Metadados visuais por moeda (ícone e nome amigável — a cor vem do tema selecionado)
MOEDA_INFO = {
    "USD": {"icone": "💵", "nome": "Dólar Americano"},
    "EUR": {"icone": "💶", "nome": "Euro"},
    "BTC": {"icone": "₿",  "nome": "Bitcoin"},
}

# =========================================================================
# 2. SELEÇÃO DE TEMA (claro/escuro) — precisa vir antes do CSS
# =========================================================================
if "modo_escuro" not in st.session_state:
    st.session_state.modo_escuro = True

with st.sidebar:
    st.markdown("### 🎨 Aparência")
    st.session_state.modo_escuro = st.toggle(
        "🌙 Modo escuro",
        value=st.session_state.modo_escuro,
        help="Alterne entre o painel escuro e o painel claro",
    )
    st.markdown("---")

MODO_ESCURO = st.session_state.modo_escuro

if MODO_ESCURO:
    TEMA = dict(
        bg_gradient="radial-gradient(circle at 15% 0%, #131722 0%, #0b0e14 45%, #0a0c11 100%)",
        texto_primario="#f5f5f7",
        texto_secundario="#9ca3af",
        card_bg="linear-gradient(160deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02))",
        card_border="rgba(255,255,255,0.09)",
        card_border_hover="rgba(255,255,255,0.2)",
        card_shadow_hover="0 16px 34px rgba(0,0,0,0.4)",
        icon_bg="rgba(255,255,255,0.06)",
        sidebar_bg="linear-gradient(180deg, #0f1220 0%, #0a0c14 100%)",
        sidebar_border="rgba(255,255,255,0.06)",
        input_bg="rgba(255,255,255,0.05)",
        input_border="rgba(255,255,255,0.14)",
        df_border="rgba(255,255,255,0.09)",
        hr_color="rgba(255,255,255,0.09)",
        hero_bg="linear-gradient(135deg, rgba(139,92,246,0.22) 0%, rgba(56,189,248,0.14) 45%, rgba(52,211,153,0.12) 100%)",
        hero_border="rgba(255,255,255,0.09)",
        plotly_template="plotly_dark",
        grid_color="rgba(255,255,255,0.07)",
        plot_font_color="#e5e7eb",
        # --- Paleta de acento (neon sobre fundo escuro) ---
        cor_moeda={"USD": "#34d399", "EUR": "#38bdf8", "BTC": "#fbbf24"},
        cor_mm7="#f472b6",
        cor_mm30="#38bdf8",
        cor_badge_texto="#4ade80",
        cor_badge_bg="rgba(34,197,94,0.14)",
        cor_badge_borda="rgba(34,197,94,0.4)",
        cor_delta_up="#4ade80",
        cor_delta_down="#f87171",
        cor_var_pos="rgba(34,197,94,{a})",
        cor_var_neg="rgba(248,113,113,{a})",
        hover_bg="#161a26",
        glow_1="rgba(139,92,246,0.35)",
        glow_2="rgba(56,189,248,0.28)",
        mini_card_bg="linear-gradient(160deg, rgba(255,255,255,0.05), rgba(255,255,255,0.015))",
    )
else:
    TEMA = dict(
        bg_gradient="radial-gradient(circle at 15% 0%, #fdf6ec 0%, #f3ede0 45%, #ece3d3 100%)",
        texto_primario="#2b2013",
        texto_secundario="#7a6a52",
        card_bg="linear-gradient(160deg, rgba(255,255,255,0.96), rgba(255,250,240,0.8))",
        card_border="rgba(120,90,40,0.14)",
        card_border_hover="rgba(120,90,40,0.28)",
        card_shadow_hover="0 16px 34px rgba(120,90,40,0.18)",
        icon_bg="rgba(180,83,9,0.08)",
        sidebar_bg="linear-gradient(180deg, #fffaf2 0%, #f6ecd9 100%)",
        sidebar_border="rgba(120,90,40,0.14)",
        input_bg="rgba(255,255,255,0.7)",
        input_border="rgba(120,90,40,0.22)",
        df_border="rgba(120,90,40,0.16)",
        hr_color="rgba(120,90,40,0.16)",
        hero_bg="linear-gradient(135deg, rgba(180,83,9,0.15) 0%, rgba(190,24,93,0.10) 45%, rgba(21,128,61,0.11) 100%)",
        hero_border="rgba(120,90,40,0.16)",
        plotly_template="plotly_white",
        grid_color="rgba(120,90,40,0.14)",
        plot_font_color="#3f3320",
        # --- Paleta de acento (terrosa/quente sobre fundo claro) ---
        cor_moeda={"USD": "#0f766e", "EUR": "#7e22ce", "BTC": "#b45309"},
        cor_mm7="#be185d",
        cor_mm30="#1d4ed8",
        cor_badge_texto="#15803d",
        cor_badge_bg="rgba(21,128,61,0.12)",
        cor_badge_borda="rgba(21,128,61,0.4)",
        cor_delta_up="#15803d",
        cor_delta_down="#b91c1c",
        cor_var_pos="rgba(21,128,61,{a})",
        cor_var_neg="rgba(185,28,28,{a})",
        hover_bg="#fffaf2",
        glow_1="rgba(180,83,9,0.22)",
        glow_2="rgba(190,24,93,0.16)",
        mini_card_bg="linear-gradient(160deg, rgba(255,255,255,0.9), rgba(255,250,240,0.6))",
    )

COR_PADRAO = TEMA["cor_moeda"]["USD"]

# =========================================================================
# 3. CSS CUSTOMIZADO — TEMA, ANIMAÇÕES E COMPONENTES
# =========================================================================
st.markdown(f"""
<style>

    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    .stApp {{
        background: {TEMA["bg_gradient"]};
        transition: background 0.4s ease;
    }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}

    @keyframes fadeInUp {{
        from {{ opacity: 0; transform: translateY(14px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    .block-container {{
        animation: fadeInUp 0.6s ease-out;
        padding-top: 1.5rem;
        max-width: 1300px;
    }}

    p, span, label, .stMarkdown, .stCaption {{
        color: {TEMA["texto_primario"]};
    }}

    .st-emotion-cache-h2nzay {{
        flex-shrink: 0;
        margin-top: calc(0.15625rem);
        width: calc(2rem);
        height: 1rem;
        padding-left: 0.125rem;
        padding-right: 0.125rem;
        border-radius: 9999px;
        background-color: rgb(255 0 0 / 51%);
        display: flex;
        -webkit-box-align: center;
        align-items: center;
        transition: background-color 150ms;
    }}

    /* ---------- HERO / CABEÇALHO ---------- */
    .hero-wrap {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 1.2rem;
        padding: 1.9rem 2.3rem;
        border-radius: 24px;
        background: {TEMA["hero_bg"]};
        backdrop-filter: blur(16px);
        border: 1px solid {TEMA["hero_border"]};
        margin-bottom: 1.8rem;
        position: relative;
        overflow: hidden;
        transition: all 0.4s ease;
    }}
    .hero-wrap::before {{
        content: "";
        position: absolute;
        top: -55%; right: -8%;
        width: 340px; height: 340px;
        background: radial-gradient(circle, {TEMA["glow_1"]}, transparent 70%);
        border-radius: 50%;
        animation: pulseGlow 6s ease-in-out infinite;
    }}
    .hero-wrap::after {{
        content: "";
        position: absolute;
        bottom: -60%; left: 10%;
        width: 260px; height: 260px;
        background: radial-gradient(circle, {TEMA["glow_2"]}, transparent 72%);
        border-radius: 50%;
        animation: pulseGlow 7s ease-in-out infinite reverse;
    }}
    @keyframes pulseGlow {{
        0%, 100% {{ transform: scale(1); opacity: 0.65; }}
        50% {{ transform: scale(1.3); opacity: 1; }}
    }}
    .hero-left {{ position: relative; z-index: 1; }}
    .hero-eyebrow {{
        text-transform: uppercase;
        letter-spacing: 1.6px;
        font-size: 0.72rem;
        font-weight: 700;
        color: {TEMA["texto_secundario"]};
        margin-bottom: 0.35rem;
    }}
    .hero-title {{
        font-family: 'Sora', sans-serif;
        font-size: 2.05rem;
        font-weight: 800;
        color: {TEMA["texto_primario"]};
        margin: 0;
        letter-spacing: -0.6px;
    }}
    .hero-subtitle {{
        color: {TEMA["texto_secundario"]};
        font-size: 0.96rem;
        margin-top: 0.4rem;
    }}
    .hero-right {{
        position: relative;
        z-index: 1;
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 0.6rem;
    }}
    .hero-badge {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 7px 15px;
        border-radius: 999px;
        background: {TEMA["cor_badge_bg"]};
        border: 1px solid {TEMA["cor_badge_borda"]};
        color: {TEMA["cor_badge_texto"]};
        font-size: 0.8rem;
        font-weight: 700;
        box-shadow: 0 2px 10px {TEMA["cor_badge_bg"]};
    }}
    .pulse-dot {{
        width: 8px; height: 8px;
        border-radius: 50%;
        background: {TEMA["cor_badge_texto"]};
        animation: pulseDot 1.8s infinite;
    }}
    @keyframes pulseDot {{
        0%   {{ box-shadow: 0 0 0 0 {hex_para_rgba(TEMA["cor_badge_texto"], 0.55)}; }}
        70%  {{ box-shadow: 0 0 0 9px {hex_para_rgba(TEMA["cor_badge_texto"], 0)}; }}
        100% {{ box-shadow: 0 0 0 0 {hex_para_rgba(TEMA["cor_badge_texto"], 0)}; }}
    }}
    .hero-stats {{
        display: flex;
        gap: 1.4rem;
    }}
    .hero-stat {{
        text-align: right;
    }}
    .hero-stat-label {{
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: {TEMA["texto_secundario"]};
        font-weight: 700;
    }}
    .hero-stat-value {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.05rem;
        font-weight: 700;
        color: {TEMA["texto_primario"]};
    }}

    /* ---------- MINI CARDS (VISÃO GERAL MULTI-MOEDA) ---------- */
    .mini-card {{
        background: {TEMA["mini_card_bg"]};
        border: 1px solid {TEMA["card_border"]};
        border-radius: 18px;
        padding: 1rem 1.2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.8rem;
        transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
        cursor: default;
    }}
    .mini-card:hover {{
        transform: translateY(-4px);
        border-color: {TEMA["card_border_hover"]};
        box-shadow: {TEMA["card_shadow_hover"]};
    }}
    .mini-card.ativo {{
        border-color: {TEMA["cor_badge_borda"]};
        box-shadow: 0 0 0 1px {TEMA["cor_badge_borda"]} inset;
    }}
    .mini-card-left {{ display: flex; align-items: center; gap: 0.7rem; }}
    .mini-card-icon {{
        width: 40px; height: 40px;
        border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.3rem;
        background: {TEMA["icon_bg"]};
    }}
    .mini-card-nome {{
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: {TEMA["texto_secundario"]};
    }}
    .mini-card-valor {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.15rem;
        font-weight: 700;
        color: {TEMA["texto_primario"]};
    }}
    .mini-card-delta {{
        font-weight: 700;
        font-size: 0.85rem;
        font-family: 'JetBrains Mono', monospace;
        padding: 4px 9px;
        border-radius: 8px;
    }}

    /* ---------- CARDS DE KPI ---------- */
    .kpi-card {{
        background: {TEMA["card_bg"]};
        backdrop-filter: blur(10px);
        border: 1px solid {TEMA["card_border"]};
        border-radius: 20px;
        padding: 1.35rem 1.5rem;
        transition: transform 0.28s ease, box-shadow 0.28s ease, border-color 0.28s ease;
        height: 100%;
        animation: fadeInUp 0.7s ease-out;
    }}
    .kpi-card:hover {{
        transform: translateY(-7px) scale(1.01);
        box-shadow: {TEMA["card_shadow_hover"]};
        border-color: {TEMA["card_border_hover"]};
    }}
    .kpi-label {{
        color: {TEMA["texto_secundario"]};
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        margin-bottom: 0.5rem;
    }}
    .kpi-value {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.75rem;
        font-weight: 700;
        color: {TEMA["texto_primario"]};
        line-height: 1.2;
    }}
    .kpi-delta-up {{
        color: {TEMA["cor_delta_up"]};
        font-weight: 700;
        font-size: 0.85rem;
        margin-top: 0.3rem;
    }}
    .kpi-delta-down {{
        color: {TEMA["cor_delta_down"]};
        font-weight: 700;
        font-size: 0.85rem;
        margin-top: 0.3rem;
    }}
    .kpi-icon {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 38px;
        height: 38px;
        border-radius: 12px;
        background: {TEMA["icon_bg"]};
        font-size: 1.25rem;
        margin-bottom: 0.6rem;
    }}

    /* ---------- SEÇÕES ---------- */
    .section-title {{
        font-family: 'Sora', sans-serif;
        font-size: 1.2rem;
        font-weight: 700;
        color: {TEMA["texto_primario"]};
        margin: 0.4rem 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    .section-sub {{
        color: {TEMA["texto_secundario"]};
        font-size: 0.85rem;
        margin-top: -0.6rem;
        margin-bottom: 1rem;
    }}

    section[data-testid="stSidebar"] {{
        background: {TEMA["sidebar_bg"]};
        border-right: 1px solid {TEMA["sidebar_border"]};
    }}
    section[data-testid="stSidebar"] * {{
        color: {TEMA["texto_primario"]};
    }}

    div[data-testid="stDataFrame"] {{
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid {TEMA["df_border"]};
    }}

    button[data-baseweb="tab"] {{
        font-weight: 600;
        border-radius: 10px 10px 0 0 !important;
        color: {TEMA["texto_primario"]} !important;
    }}

    div[data-testid="stDownloadButton"] button {{
        border-radius: 12px;
        font-weight: 600;
        transition: transform 0.2s ease;
    }}
    div[data-testid="stDownloadButton"] button:hover {{
        transform: translateY(-2px);
    }}

    .stSelectbox [data-baseweb="select"],
    .stSelectbox [data-baseweb="select"] > div,
    .stSelectbox [data-baseweb="select"] div[role="button"],
    .stSelectbox [data-baseweb="select"] [data-testid="stMarkdownContainer"] p {{
        background-color: {TEMA["input_bg"]} !important;
        background: {TEMA["input_bg"]} !important;
        color: {TEMA["texto_primario"]} !important;
    }}
    .stSelectbox [data-baseweb="select"] > div {{
        border: 1px solid {TEMA["input_border"]} !important;
        border-radius: 12px !important;
    }}
    .stSelectbox div[data-baseweb="select"] [data-testid="stMarkdownContainer"] p,
    .stSelectbox div[data-baseweb="select"] div {{
        color: {TEMA["texto_primario"]} !important;
    }}
    div[data-baseweb="select"] svg {{
        fill: {TEMA["texto_secundario"]} !important;
    }}
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] *,
    ul[role="listbox"],
    ul[role="listbox"] *,
    div[role="listbox"],
    div[role="listbox"] * {{
        background-color: {"#0f1220" if MODO_ESCURO else "#fffaf2"} !important;
        color: {TEMA["texto_primario"]} !important;
    }}
    li[role="option"]:hover,
    li[data-baseweb="menu-item"]:hover {{
        background-color: {"rgba(255,255,255,0.08)" if MODO_ESCURO else "rgba(180,83,9,0.08)"} !important;
    }}

    div[data-testid="stCheckboxToggle"] div[role="switch"] {{
        background-color: {"rgba(255,255,255,0.12)" if MODO_ESCURO else "rgba(120,90,40,0.16)"} !important;
        border: 1px solid {TEMA["input_border"]} !important;
    }}
    div[data-testid="stCheckboxToggle"] div[role="switch"][aria-checked="true"] {{
        background-color: {TEMA["cor_badge_texto"]} !important;
    }}
    div[data-testid="stCheckboxToggle"] div[role="switch"] > div {{
        background-color: {TEMA["texto_primario"]} !important;
    }}

    /* ---------- SLIDER DE PERÍODO (OTIMIZADO COM ESTILO DINÂMICO COMPLETO) ---------- */
    div[data-baseweb="slider"] {{
        color: {TEMA["texto_primario"]} !important;
    }}
    
    .st-emotion-cache-e1adlt,
    div[data-baseweb="slider"] > div {{
        display: flex !important;
        flex-direction: row !important;
        align-items: stretch !important;
        width: 100% !important;
        height: 2.5rem !important;
        overflow: hidden !important;
        border-width: 1px !important;
        border-style: solid !important;
        border-color: {TEMA["input_border"]} !important;
        box-sizing: border-box !important;
        border-radius: 0.5rem !important;
        background-color: {"rgba(255,255,255,0.05)" if MODO_ESCURO else "#f1ddcf"} !important;
    }}

    .stButton > button, .stDownloadButton > button {{
        background: {TEMA["input_bg"]} !important;
        color: {TEMA["texto_primario"]} !important;
        border: 1px solid {TEMA["input_border"]} !important;
        border-radius: 10px !important;
    }}
    .stButton > button:hover {{
        border-color: {TEMA["cor_badge_borda"]} !important;
        color: {TEMA["cor_badge_texto"]} !important;
    }}

    /* ---------- TABELA HTML CUSTOMIZADA ---------- */
    .tabela-scroll {{
        max-height: 460px;
        overflow-y: auto;
        border-radius: 16px;
        border: 1px solid {TEMA["df_border"]};
    }}
    table.tabela-cotacoes {{
        width: 100%;
        border-collapse: collapse;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
    }}
    table.tabela-cotacoes thead th {{
        position: sticky;
        top: 0;
        background: {TEMA["sidebar_bg"]};
        color: {TEMA["texto_secundario"]};
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        text-transform: uppercase;
        font-size: 0.72rem;
        letter-spacing: 0.5px;
        text-align: right;
        padding: 12px 14px;
        border-bottom: 1px solid {TEMA["df_border"]};
        z-index: 1;
    }}
    table.tabela-cotacoes thead th:first-child {{ text-align: left; }}
    table.tabela-cotacoes td {{
        padding: 10px 14px;
        text-align: right;
        color: {TEMA["texto_primario"]};
        border-bottom: 1px solid {TEMA["hr_color"]};
        white-space: nowrap;
    }}
    table.tabela-cotacoes td.col-data {{
        text-align: left;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: {TEMA["texto_secundario"]};
    }}
    table.tabela-cotacoes tbody tr {{ transition: background 0.15s ease; }}
    table.tabela-cotacoes tbody tr:hover td {{ background: {TEMA["icon_bg"]}; }}

    hr {{ border-color: {TEMA["hr_color"]} !important; }}

    /* ---------- RODAPÉ ---------- */
    .rodape-final {{
        text-align: center;
        color: {TEMA["texto_secundario"]};
        font-size: 0.8rem;
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid {TEMA["hr_color"]};
    }}

    /* ---------- ASSINATURA DO AUTOR ---------- */
    .assinatura-autor {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-top: 0.5rem;
        font-size: 0.72rem;
        letter-spacing: 0.4px;
        color: {TEMA["texto_secundario"]};
        opacity: 0.75;
    }}
    .assinatura-autor .traco {{
        width: 14px;
        height: 1px;
        background: {TEMA["texto_secundario"]};
        opacity: 0.5;
        display: inline-block;
    }}
    .assinatura-autor .nome {{
        font-family: 'Sora', sans-serif;
        font-weight: 700;
        color: {TEMA["cor_badge_texto"]};
        opacity: 0.9;
    }}
    .assinatura-sidebar {{
        text-align: center;
        font-size: 0.68rem;
        color: {TEMA["texto_secundario"]};
        opacity: 0.6;
        letter-spacing: 0.4px;
        margin-top: 0.3rem;
    }}
    .assinatura-sidebar .nome {{
        color: {TEMA["cor_badge_texto"]};
        font-weight: 700;
        opacity: 0.85;
    }}
</style>
""", unsafe_allow_html=True)

# =========================================================================
# 4. CONEXÃO SEGURA COM O BIGQUERY (Streamlit Secrets)
# =========================================================================
@st.cache_resource(show_spinner=False)
def obter_cliente_bigquery():
    info_projeto = dict(st.secrets["gcp_service_account"])
    credentials = service_account.Credentials.from_service_account_info(info_projeto)
    return bigquery.Client(credentials=credentials, project=info_projeto["project_id"])


# =========================================================================
# 5. CARREGAMENTO DE DADOS COM CACHE (evita custos repetidos no GCP)
# =========================================================================
@st.cache_data(ttl=600, show_spinner=False)
def carregar_dados():
    client = obter_cliente_bigquery()
    query = """
        SELECT 
            data_referencia,
            codigo_moeda,
            nome_moeda,
            cotacao_compra,
            cotacao_venda,
            spread,
            media_movel_7_dias,
            media_movel_30_dias,
            variacao_diaria_pct
        FROM `finance-analytics-engineering.dbt_finance.obt_cotacoes_analitico`
        ORDER BY data_referencia DESC
    """
    df = client.query(query).to_dataframe()
    df['data_referencia'] = pd.to_datetime(df['data_referencia']).dt.date
    return df


def formatar_moeda(valor, casas=4):
    return f"R$ {valor:,.{casas}f}".replace(",", "§").replace(".", ",").replace("§", ".")


def kpi_card(icone, label, valor, delta=None, delta_positivo=None):
    delta_html = ""
    if delta is not None:
        seta = "▲" if delta_positivo else "▼"
        classe = "kpi-delta-up" if delta_positivo else "kpi-delta-down"
        delta_html = f'<div class="{classe}">{seta} {delta}</div>'
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">{icone}</div>
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{valor}</div>
            {delta_html}
        </div>
    """, unsafe_allow_html=True)


def mini_card_moeda(codigo, linha, ativo=False):
    """Card compacto de visão geral para cada moeda (usado no topo da página)."""
    info = MOEDA_INFO.get(codigo, {"icone": "💱", "nome": codigo})
    cor = TEMA["cor_moeda"].get(codigo, COR_PADRAO)
    variacao = linha['variacao_diaria_pct']
    subiu = variacao >= 0
    cor_delta = TEMA["cor_delta_up"] if subiu else TEMA["cor_delta_down"]
    bg_delta = hex_para_rgba(cor_delta, 0.14)
    seta = "▲" if subiu else "▼"
    classe_ativo = "ativo" if ativo else ""
    st.markdown(f"""
        <div class="mini-card {classe_ativo}">
            <div class="mini-card-left">
                <div class="mini-card-icon" style="background:{hex_para_rgba(cor, 0.16)};">{info['icone']}</div>
                <div>
                    <div class="mini-card-nome">{codigo} · {info['nome']}</div>
                    <div class="mini-card-valor">{formatar_moeda(linha['cotacao_compra'])}</div>
                </div>
            </div>
            <div class="mini-card-delta" style="color:{cor_delta}; background:{bg_delta};">
                {seta} {abs(variacao):.2f}%
            </div>
        </div>
    """, unsafe_allow_html=True)


# =========================================================================
# 6. APLICAÇÃO PRINCIPAL
# =========================================================================
try:
    with st.spinner("Carregando cotações mais recentes..."):
        df_raw = carregar_dados()

    # ---------------- SIDEBAR: FILTROS ----------------
    with st.sidebar:
        st.markdown("### ⚙️ Filtros")
        moedas_disponiveis = list(df_raw["codigo_moeda"].unique())
        moeda_selecionada = st.selectbox(
            "Selecione a moeda",
            moedas_disponiveis,
            format_func=lambda m: f"{MOEDA_INFO.get(m, {}).get('icone', '💱')}  {m}",
        )

        datas_disp = sorted(df_raw["data_referencia"].unique())

        st.markdown("**Atalhos de período**")
        col_a, col_b, col_c, col_d = st.columns(4)
        atalho = None
        if col_a.button("7d", use_container_width=True):
            atalho = 7
        if col_b.button("30d", use_container_width=True):
            atalho = 30
        if col_c.button("90d", use_container_width=True):
            atalho = 90
        if col_d.button("Tudo", use_container_width=True):
            atalho = None if len(datas_disp) <= 1 else -1

        if "periodo_ini" not in st.session_state:
            st.session_state.periodo_ini = datas_disp[0]
            st.session_state.periodo_fim = datas_disp[-1]

        if atalho == -1:
            st.session_state.periodo_ini = datas_disp[0]
            st.session_state.periodo_fim = datas_disp[-1]
        elif atalho is not None and len(datas_disp) > atalho:
            st.session_state.periodo_ini = datas_disp[-atalho]
            st.session_state.periodo_fim = datas_disp[-1]

        if len(datas_disp) > 1:
            data_ini, data_fim = st.select_slider(
                "Período de análise",
                options=datas_disp,
                value=(st.session_state.periodo_ini, st.session_state.periodo_fim),
            )
        else:
            data_ini = data_fim = datas_disp[0]

        st.markdown("---")
        st.caption(f"🕒 Última atualização dos dados em cache: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        st.caption("Cache renovado automaticamente a cada 10 minutos.")
        st.markdown("---")
        import pytz
        fuso_br = pytz.timezone('America/Sao_Paulo')
        hora_brasilia = datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M')
        st.caption(f"🕒 Última atualização dos dados em cache: {hora_brasilia}")
        st.caption("Cache renovado automaticamente a cada 10 minutos.")

    info_moeda = MOEDA_INFO.get(moeda_selecionada, {"icone": "💱", "nome": moeda_selecionada})
    meta_atual = {
        "icone": info_moeda["icone"],
        "nome": info_moeda["nome"],
        "cor": TEMA["cor_moeda"].get(moeda_selecionada, COR_PADRAO),
    }

    # ---------------- FILTRAGEM ----------------
    df_filtrado = df_raw[
        (df_raw["codigo_moeda"] == moeda_selecionada) &
        (df_raw["data_referencia"] >= data_ini) &
        (df_raw["data_referencia"] <= data_fim)
    ].sort_values("data_referencia")

    if not df_filtrado.empty:
        max_periodo = df_filtrado['cotacao_compra'].max()
        min_periodo = df_filtrado['cotacao_compra'].min()
        variacao_periodo = (
            (df_filtrado['cotacao_compra'].iloc[-1] / df_filtrado['cotacao_compra'].iloc[0]) - 1
        ) * 100 if len(df_filtrado) > 1 else 0.0
    else:
        max_periodo = min_periodo = variacao_periodo = 0.0

    # ---------------- HERO / CABEÇALHO ----------------
    sinal_periodo = "+" if variacao_periodo >= 0 else ""
    st.markdown(f"""
        <div class="hero-wrap">
            <div class="hero-left">
                <div class="hero-eyebrow">Pipeline ELT · BigQuery + dbt + Streamlit</div>
                <p class="hero-title">📈 Monitor de Cotações e Médias Móveis</p>
                <p class="hero-subtitle">Acompanhamento em tempo real de {meta_atual['nome']} com médias móveis de 7 e 30 dias</p>
                <div class="assinatura-autor"><span class="traco"></span> por <span class="nome">Leo Sinhorine</span></div>
            </div>
            <div class="hero-right">
                <div class="hero-badge"><span class="pulse-dot"></span> Dados ao vivo</div>
                <div class="hero-stats">
                    <div class="hero-stat">
                        <div class="hero-stat-label">Máxima período</div>
                        <div class="hero-stat-value">{formatar_moeda(max_periodo)}</div>
                    </div>
                    <div class="hero-stat">
                        <div class="hero-stat-label">Mínima período</div>
                        <div class="hero-stat-value">{formatar_moeda(min_periodo)}</div>
                    </div>
                    <div class="hero-stat">
                        <div class="hero-stat-label">Variação período</div>
                        <div class="hero-stat-value">{sinal_periodo}{variacao_periodo:.2f}%</div>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ---------------- VISÃO GERAL MULTI-MOEDA ----------------
    st.markdown('<p class="section-title">🌐 Visão Geral do Mercado</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-sub">Última cotação disponível para cada moeda monitorada</p>', unsafe_allow_html=True)
    ultimas_por_moeda = (
        df_raw.sort_values("data_referencia")
        .groupby("codigo_moeda")
        .tail(1)
        .set_index("codigo_moeda")
    )
    colunas_mercado = st.columns(len(moedas_disponiveis))
    for col, codigo in zip(colunas_mercado, moedas_disponiveis):
        with col:
            if codigo in ultimas_por_moeda.index:
                mini_card_moeda(codigo, ultimas_por_moeda.loc[codigo], ativo=(codigo == moeda_selecionada))

    st.markdown("<br>", unsafe_allow_html=True)

    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado para o período e moeda selecionados.")
    else:
        ultimo_registro = df_filtrado.iloc[-1]
        variacao = ultimo_registro['variacao_diaria_pct']
        subiu = variacao >= 0

        # ---------------- KPIs ----------------
        st.markdown(f'<p class="section-title">{meta_atual["icone"]} Indicadores — {moeda_selecionada}</p>', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            kpi_card(
                meta_atual["icone"],
                f"Cotação Atual · {moeda_selecionada}",
                formatar_moeda(ultimo_registro['cotacao_compra']),
                delta=f"{abs(variacao):.2f}% (24h)",
                delta_positivo=subiu,
            )
        with col2:
            kpi_card("📊", "Média Móvel (7 dias)", formatar_moeda(ultimo_registro['media_movel_7_dias']))
        with col3:
            kpi_card("📉", "Média Móvel (30 dias)", formatar_moeda(ultimo_registro['media_movel_30_dias']))
        with col4:
            kpi_card("🔀", "Spread Compra/Venda", formatar_moeda(ultimo_registro['spread']))

        st.markdown("<br>", unsafe_allow_html=True)

        aba_grafico, aba_tabela = st.tabs(["📈 Evolução & Tendências", "🗂️ Dados Detalhados (OBT)"])

        with aba_grafico:
            st.markdown(f'<p class="section-title">Histórico — {meta_atual["nome"]}</p>', unsafe_allow_html=True)

            fig = go.Figure()
            datas_x = df_filtrado['data_referencia'].astype(str)

            fig.add_trace(go.Scatter(
                x=datas_x,
                y=df_filtrado['cotacao_compra'],
                mode='lines+markers',
                name='Cotação Diária',
                line=dict(color=meta_atual["cor"], width=3, shape='spline'),
                marker=dict(size=8, symbol='circle'),
                fill='tozeroy',
                fillcolor=hex_para_rgba(meta_atual["cor"], 0.13),
            ))

            fig.add_trace(go.Scatter(
                x=datas_x,
                y=df_filtrado['media_movel_7_dias'],
                mode='lines+markers',
                name='Média Móvel (7d)',
                line=dict(color=TEMA["cor_mm7"], width=2, dash='dash'),
                marker=dict(size=6, symbol='x'),
            ))

            fig.add_trace(go.Scatter(
                x=datas_x,
                y=df_filtrado['media_movel_30_dias'],
                mode='lines+markers',
                name='Média Móvel (30d)',
                line=dict(color=TEMA["cor_mm30"], width=2, dash='dot'),
                marker=dict(size=6, symbol='diamond'),
            ))

            # --- Anotações de máxima e mínima do período (destaque visual) ---
            idx_max = df_filtrado['cotacao_compra'].idxmax()
            idx_min = df_filtrado['cotacao_compra'].idxmin()
            fig.add_annotation(
                x=str(df_filtrado.loc[idx_max, 'data_referencia']),
                y=df_filtrado.loc[idx_max, 'cotacao_compra'],
                text=f"Máx. {formatar_moeda(df_filtrado.loc[idx_max, 'cotacao_compra'])}",
                showarrow=True, arrowhead=2, arrowcolor=TEMA["cor_delta_up"],
                font=dict(color=TEMA["cor_delta_up"], size=11, family="Inter, sans-serif"),
                ay=-35, bgcolor=hex_para_rgba(TEMA["cor_delta_up"], 0.12), bordercolor=TEMA["cor_delta_up"], borderwidth=1,
            )
            fig.add_annotation(
                x=str(df_filtrado.loc[idx_min, 'data_referencia']),
                y=df_filtrado.loc[idx_min, 'cotacao_compra'],
                text=f"Mín. {formatar_moeda(df_filtrado.loc[idx_min, 'cotacao_compra'])}",
                showarrow=True, arrowhead=2, arrowcolor=TEMA["cor_delta_down"],
                font=dict(color=TEMA["cor_delta_down"], size=11, family="Inter, sans-serif"),
                ay=35, bgcolor=hex_para_rgba(TEMA["cor_delta_down"], 0.12), bordercolor=TEMA["cor_delta_down"], borderwidth=1,
            )

            # --- Destaque do último ponto (ponto "vivo") ---
            fig.add_trace(go.Scatter(
                x=[datas_x.iloc[-1]],
                y=[df_filtrado['cotacao_compra'].iloc[-1]],
                mode='markers',
                marker=dict(size=14, color=meta_atual["cor"], line=dict(width=2, color=TEMA["plot_font_color"])),
                showlegend=False,
                hoverinfo='skip',
            ))

            fig.update_layout(
                template=TEMA["plotly_template"],
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis_title=None,
                yaxis_title="Preço (R$)",
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(color=TEMA["plot_font_color"], size=12),
                ),
                margin=dict(l=10, r=10, t=40, b=10),
                height=480,
                hovermode="x unified",
                font=dict(family="Inter, sans-serif", color=TEMA["plot_font_color"]),
                xaxis=dict(
                    type='category',
                    showgrid=False,
                    tickfont=dict(color=TEMA["plot_font_color"]),
                    linecolor=TEMA["grid_color"],
                    rangeslider=dict(visible=False),
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor=TEMA["grid_color"],
                    tickfont=dict(color=TEMA["plot_font_color"]),
                    title=dict(font=dict(color=TEMA["plot_font_color"])),
                ),
                hoverlabel=dict(
                    bgcolor=TEMA["hover_bg"],
                    font=dict(color=TEMA["plot_font_color"]),
                ),
                transition=dict(duration=400, easing="cubic-in-out"),
            )

            st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

            # --- Mini gráfico de volatilidade (variação diária %) ---
            st.markdown('<p class="section-title" style="font-size:1rem;">⚡ Volatilidade Diária</p>', unsafe_allow_html=True)
            cores_barras = [
                TEMA["cor_delta_up"] if v >= 0 else TEMA["cor_delta_down"]
                for v in df_filtrado['variacao_diaria_pct']
            ]
            fig_vol = go.Figure(go.Bar(
                x=datas_x,
                y=df_filtrado['variacao_diaria_pct'],
                marker_color=cores_barras,
                marker_line_width=0,
                hovertemplate="%{x}<br>%{y:.2f}%<extra></extra>",
            ))
            fig_vol.update_layout(
                template=TEMA["plotly_template"],
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=180,
                margin=dict(l=10, r=10, t=10, b=10),
                showlegend=False,
                xaxis=dict(type='category', showgrid=False, tickfont=dict(color=TEMA["plot_font_color"], size=9)),
                yaxis=dict(showgrid=True, gridcolor=TEMA["grid_color"], tickfont=dict(color=TEMA["plot_font_color"]), title="%"),
                font=dict(family="Inter, sans-serif", color=TEMA["plot_font_color"]),
            )
            st.plotly_chart(fig_vol, use_container_width=True, config={"displaylogo": False})

        with aba_tabela:
            st.markdown('<p class="section-title">Tabela Consolidada (One Big Table)</p>', unsafe_allow_html=True)

            df_exibicao = df_filtrado[[
                'data_referencia', 'cotacao_compra', 'cotacao_venda',
                'spread', 'media_movel_7_dias', 'media_movel_30_dias', 'variacao_diaria_pct'
            ]].sort_values('data_referencia', ascending=False).rename(columns={
                'data_referencia': 'Data',
                'cotacao_compra': 'Compra (R$)',
                'cotacao_venda': 'Venda (R$)',
                'spread': 'Spread (R$)',
                'media_movel_7_dias': 'Média 7d (R$)',
                'media_movel_30_dias': 'Média 30d (R$)',
                'variacao_diaria_pct': 'Variação (%)',
            })

            def col_variacao_func(valor):
                intensidade = min(abs(valor) / 3, 1)
                alpha = 0.12 + 0.35 * intensidade
                if valor >= 0:
                    return TEMA["cor_var_pos"].format(a=alpha)
                return TEMA["cor_var_neg"].format(a=alpha)

            def renderizar_tabela_html(df):
                colunas = df.columns.tolist()
                linhas_html = []
                for _, linha in df.iterrows():
                    celulas = []
                    for col in colunas:
                        valor = linha[col]
                        if col == 'Data':
                            celulas.append(f'<td class="col-data">{valor}</td>')
                        elif col == 'Variação (%)':
                            bg = col_variacao_func(valor)
                            celulas.append(f'<td style="background:{bg}; font-weight:700;">{valor:+.2f}%</td>')
                        else:
                            celulas.append(f'<td>R$ {valor:.4f}</td>')
                    linhas_html.append(f"<tr>{''.join(celulas)}</tr>")

                cabecalho = "".join(f"<th>{c}</th>" for c in colunas)
                return f"""
                <div class="tabela-scroll">
                    <table class="tabela-cotacoes">
                        <thead><tr>{cabecalho}</tr></thead>
                        <tbody>{''.join(linhas_html)}</tbody>
                    </table>
                </div>
                """

            st.markdown(renderizar_tabela_html(df_exibicao), unsafe_allow_html=True)

            csv = df_exibicao.to_csv(index=False).encode('utf-8')
            st.download_button(
                "⬇️ Baixar dados em CSV",
                data=csv,
                file_name=f"cotacoes_{moeda_selecionada}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )

    # ---------------- RODAPÉ ----------------
    st.markdown(
        f"<div class='rodape-final'>Pipeline ELT · BigQuery + dbt + Streamlit &nbsp;•&nbsp; "
        f"Atualizado automaticamente a cada 10 minutos<br>"
        f"<span class='assinatura-autor' style='margin-top:0.6rem;'><span class='traco'></span> Desenvolvido por <span class='nome'>Leo Sinhorine</span><span class='traco'></span></span></div>",
        unsafe_allow_html=True,
    )

except Exception as e:
    st.error("⚠️ Erro ao carregar os dados do BigQuery. Verifique se o arquivo `.streamlit/secrets.toml` foi criado e preenchido corretamente.")
    with st.expander("Detalhes técnicos do erro"):
        st.exception(e)
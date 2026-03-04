"""
Sistema de Precificação Brivia 
=]
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, getcontext

# Configura precisão alta pra evitar aqueles erros chatos de ponto flutuante em cálculo financeiro
getcontext().prec = 20

# ==================== DATABASE & CONFIGURAÇÕES ====================

# Listas estáticas para preencher os selects. 
# Se isso crescer, ideal mover pra um banco ou arquivo de config separado.
TIPOS_CONTRATO = ["Fee Mensal (Recorrente)", "Projeto (Escopo Fechado)", "Sustentação", "Consultoria Estratégica"]
TIPOS_SERVICO = ["Tecnologia / Dev", "Design / UX", "Dados / Analytics", "Marketing / Growth", "Estratégia Digital"]

# Tabelas de comissão progressiva
COMISSAO_NB = [0, 5, 7, 10, 12, 15]
COMISSAO_PARCEIROS = [0, 5, 10, 15, 20, 25]
GROSS_MARGIN_ALVO = 45.0

# Base salarial hardcoded.
# Estrutura: Cargo -> Nível -> Régua (Mercado vs Brivia vs Mínima)
BASE_SALARIAL = {
    "Desenvolvedor Fullstack": {
        "1. Júnior": {"mercado": 4500, "minima": 3800, "brivia": 5000},
        "2. Pleno": {"mercado": 7500, "minima": 6500, "brivia": 8500},
        "3. Sênior": {"mercado": 11000, "minima": 9500, "brivia": 13000},
        "4. Líder": {"mercado": 14000, "minima": 12000, "brivia": 16000},
        "5. Head": {"mercado": 18000, "minima": 15000, "brivia": 22000}
    },
    "Desenvolvedor Frontend": {
        "1. Júnior": {"mercado": 4000, "minima": 3500, "brivia": 4500},
        "2. Pleno": {"mercado": 6500, "minima": 5500, "brivia": 7500},
        "3. Sênior": {"mercado": 10000, "minima": 8500, "brivia": 12000},
        "4. Líder": {"mercado": 13000, "minima": 11000, "brivia": 15000},
        "5. Head": {"mercado": 17000, "minima": 14000, "brivia": 20000}
    },
    "Desenvolvedor Backend": {
        "1. Júnior": {"mercado": 4500, "minima": 3800, "brivia": 5000},
        "2. Pleno": {"mercado": 7500, "minima": 6500, "brivia": 8500},
        "3. Sênior": {"mercado": 11500, "minima": 10000, "brivia": 13500},
        "4. Líder": {"mercado": 14500, "minima": 12500, "brivia": 17000},
        "5. Head": {"mercado": 19000, "minima": 16000, "brivia": 23000}
    },
    "Cientista de Dados": {
        "1. Júnior": {"mercado": 5500, "minima": 4500, "brivia": 6500},
        "2. Pleno": {"mercado": 9000, "minima": 7500, "brivia": 10500},
        "3. Sênior": {"mercado": 13500, "minima": 11500, "brivia": 16000},
        "4. Líder": {"mercado": 17000, "minima": 14500, "brivia": 20000},
        "5. Head": {"mercado": 22000, "minima": 18000, "brivia": 26000}
    },
    "Engenheiro de Dados": {
        "1. Júnior": {"mercado": 5000, "minima": 4200, "brivia": 5800},
        "2. Pleno": {"mercado": 8500, "minima": 7200, "brivia": 10000},
        "3. Sênior": {"mercado": 13000, "minima": 11000, "brivia": 15500},
        "4. Líder": {"mercado": 16500, "minima": 14000, "brivia": 19500},
        "5. Head": {"mercado": 21000, "minima": 17500, "brivia": 25000}
    },
    "UX Designer": {
        "1. Júnior": {"mercado": 4000, "minima": 3200, "brivia": 4500},
        "2. Pleno": {"mercado": 6500, "minima": 5500, "brivia": 7500},
        "3. Sênior": {"mercado": 9500, "minima": 8000, "brivia": 11000},
        "4. Líder": {"mercado": 12500, "minima": 10500, "brivia": 14500},
        "5. Head": {"mercado": 16000, "minima": 13500, "brivia": 19000}
    },
    "UI Designer": {
        "1. Júnior": {"mercado": 3800, "minima": 3000, "brivia": 4200},
        "2. Pleno": {"mercado": 6000, "minima": 5000, "brivia": 7000},
        "3. Sênior": {"mercado": 9000, "minima": 7500, "brivia": 10500},
        "4. Líder": {"mercado": 12000, "minima": 10000, "brivia": 14000},
        "5. Head": {"mercado": 15500, "minima": 13000, "brivia": 18000}
    },
    "Product Manager": {
        "1. Júnior": {"mercado": 5000, "minima": 4200, "brivia": 5800},
        "2. Pleno": {"mercado": 8500, "minima": 7200, "brivia": 10000},
        "3. Sênior": {"mercado": 13000, "minima": 11000, "brivia": 15000},
        "4. Líder": {"mercado": 17000, "minima": 14500, "brivia": 20000},
        "5. Head": {"mercado": 22000, "minima": 18500, "brivia": 26000}
    },
    "Tech Lead": {
        "3. Sênior": {"mercado": 14000, "minima": 12000, "brivia": 16500},
        "4. Líder": {"mercado": 18000, "minima": 15500, "brivia": 21000},
        "5. Head": {"mercado": 24000, "minima": 20000, "brivia": 28000}
    },
    "DevOps/SRE": {
        "1. Júnior": {"mercado": 5000, "minima": 4200, "brivia": 5800},
        "2. Pleno": {"mercado": 8500, "minima": 7200, "brivia": 10000},
        "3. Sênior": {"mercado": 13000, "minima": 11000, "brivia": 15500},
        "4. Líder": {"mercado": 17000, "minima": 14500, "brivia": 20000},
        "5. Head": {"mercado": 22000, "minima": 18500, "brivia": 26000}
    },
    "Analista de Marketing": {
        "1. Júnior": {"mercado": 3500, "minima": 2800, "brivia": 4000},
        "2. Pleno": {"mercado": 5500, "minima": 4500, "brivia": 6500},
        "3. Sênior": {"mercado": 8500, "minima": 7000, "brivia": 10000},
        "4. Líder": {"mercado": 12000, "minima": 10000, "brivia": 14000},
        "5. Head": {"mercado": 16000, "minima": 13500, "brivia": 19000}
    },
    "Scrum Master": {
        "2. Pleno": {"mercado": 7000, "minima": 5800, "brivia": 8200},
        "3. Sênior": {"mercado": 10500, "minima": 9000, "brivia": 12500},
        "4. Líder": {"mercado": 14000, "minima": 12000, "brivia": 16500},
        "5. Head": {"mercado": 18000, "minima": 15000, "brivia": 21000}
    }
}

# Mapeia o tipo de serviço pro nome "comercial" da squad
MAPEAMENTO_OFERTAS = {
    "Tecnologia / Dev": "Tech Squad",
    "Design / UX": "Design Studio",
    "Dados / Analytics": "Data Intelligence",
    "Marketing / Growth": "Growth Lab",
    "Estratégia Digital": "Strategy Hub"
}

# ==================== PAGE CONFIG ====================

# Configurações iniciais do Streamlit (título, layout wide)
st.set_page_config(
    page_title="Sistema de Precificação Brivia",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== CONSTANTES DE CÁLCULO ====================

# Cálculos de encargos trabalhistas (CLT)
PROV_13 = Decimal("100") / Decimal("12")
PROV_FERIAS = Decimal("11.1110833333333")

ENCARGOS_FPA = {
    "fgts_base": Decimal("8.00"),
    "fgts_s_13": PROV_13 * Decimal("0.08"),
    "fgts_s_ferias": PROV_FERIAS * Decimal("0.08"),
    "inss_gps_base": Decimal("26.30"),
    "inss_s_13": PROV_13 * Decimal("0.263"),
    "inss_s_ferias": PROV_FERIAS * Decimal("0.263"),
    "prov_13_salario": PROV_13,
    "prov_ferias": PROV_FERIAS,
    "aviso_previo": Decimal("1.32"),
    "auxilio_doenca": Decimal("0.55"),
    "desp_rescisao": Decimal("2.57")
}

# Fator multiplicador para transformar salário base em custo empresa
FATOR_ENCARGOS = Decimal("1") + (sum(ENCARGOS_FPA.values()) / Decimal("100"))
BENEFICIOS_MENSAIS = Decimal("1190") # VR/VA/Saúde médio
HORAS_MES = Decimal("170")
IMPOSTO_PADRAO_PCT = 14.25 # Imposto médio sobre NF

# ==================== CSS & VISUAL IDENTITY ====================

video_url = "https://cdn.prod.website-files.com/65c2dcb4330facd527e06bdd/66189f248c2e87b594826a44_Co%CC%81pia%20de%20BornBlackColor2-transcode.mp4"
logo_url = "https://cdn.prod.website-files.com/65c2dcb4330facd527e06bdd/6619a7597575e945de440959_brivia_group.svg"

# Paleta de cores da marca
COR_PRIMARIA = "#c58f3d"
COR_PRIMARIA_LIGHT = "#b86f55"
COR_SUCESSO = "#10b981"
COR_ALERTA = "#f59e0b"
COR_ERRO = "#ef4444"

# Injeção de CSS pesado pra sair do visual padrão do Streamlit
# Define fontes, scrollbars, cards translúcidos (glassmorphism) e background de vídeo
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');

    /* ===== RESET & GLOBAL ===== */
    .stApp {{
        background: linear-gradient(135deg, #0a0a0a 0%, #111111 50%, #0a0a0a 100%) !important;
        background-attachment: fixed;
    }}

    * {{
        font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif !important;
        scrollbar-width: thin;
        scrollbar-color: {COR_PRIMARIA} transparent;
    }}

    *::-webkit-scrollbar {{
        width: 6px;
        height: 6px;
    }}

    *::-webkit-scrollbar-track {{
        background: transparent;
    }}

    *::-webkit-scrollbar-thumb {{
        background: {COR_PRIMARIA};
        border-radius: 3px;
    }}

    /* ===== TYPOGRAPHY ===== */
    h1 {{
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        letter-spacing: -1px !important;
        margin-bottom: 0 !important;
    }}

    h2 {{
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        color: #ffffff !important;
        letter-spacing: -0.5px !important;
    }}

    h3 {{
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #ffffff !important;
        letter-spacing: 0 !important;
    }}

    p, span, label {{
        color: #d1d5db !important;
        font-weight: 400 !important;
    }}

    /* ===== VIDEO BACKGROUND ===== */
    #video-bg {{
        position: fixed;
        top: 0;
        right: 0;
        width: 70vw;
        height: 100vh;
        object-fit: cover;
        z-index: 0;
        opacity: 0.5;
        pointer-events: none;
        -webkit-mask-image: radial-gradient(ellipse 80% 100% at 100% 50%, black 0%, transparent 70%);
        mask-image: radial-gradient(ellipse 80% 100% at 100% 50%, black 0%, transparent 70%);
    }}

    .stMainBlockContainer {{
        position: relative;
        z-index: 1;
        background: transparent !important;
    }}

    /* ===== HEADER ===== */
    .header-premium {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 24px 0;
        margin-bottom: 32px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }}

    .header-left {{
        display: flex;
        align-items: center;
        gap: 20px;
    }}

    .logo-premium {{
        height: 38px;
        filter: brightness(0) invert(1);
        transition: all 0.3s ease;
    }}

    .logo-premium:hover {{
        filter: brightness(0) invert(1) drop-shadow(0 0 10px rgba(144, 81, 59, 0.5));
    }}

    .header-divider {{
        width: 1px;
        height: 30px;
        background: linear-gradient(to bottom, transparent, rgba(255,255,255,0.2), transparent);
    }}

    .header-title {{
        font-size: 1.4rem;
        font-weight: 600;
        color: #ffffff;
        letter-spacing: -0.5px;
    }}

    .header-badge {{
        background: linear-gradient(135deg, {COR_PRIMARIA}, {COR_PRIMARIA_LIGHT});
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.65rem;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: white;
    }}

    /* ===== TIMELINE/STEPPER ===== */
    .timeline-container {{
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 8px;
        padding: 20px 0;
        margin-bottom: 40px;
    }}

    .timeline-step {{
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 12px 24px;
        border-radius: 50px;
        font-size: 0.8rem;
        font-weight: 500;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: default;
        position: relative;
    }}

    .timeline-step.active {{
        background: linear-gradient(135deg, rgba(144, 81, 59, 0.3), rgba(144, 81, 59, 0.1));
        border: 1px solid {COR_PRIMARIA};
        color: #ffffff;
        box-shadow: 0 0 30px rgba(144, 81, 59, 0.3), inset 0 0 20px rgba(144, 81, 59, 0.1);
    }}

    .timeline-step.completed {{
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: {COR_SUCESSO};
    }}

    .timeline-step.pending {{
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.08);
        color: rgba(255, 255, 255, 0.3);
    }}

    .timeline-number {{
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
        font-weight: 700;
    }}

    .timeline-step.active .timeline-number {{
        background: {COR_PRIMARIA};
        color: white;
    }}

    .timeline-step.completed .timeline-number {{
        background: {COR_SUCESSO};
        color: white;
    }}

    .timeline-step.pending .timeline-number {{
        background: rgba(255, 255, 255, 0.1);
    }}

    .timeline-connector {{
        width: 40px;
        height: 2px;
        background: rgba(255, 255, 255, 0.1);
        position: relative;
    }}

    .timeline-connector.completed {{
        background: linear-gradient(90deg, {COR_SUCESSO}, {COR_PRIMARIA});
    }}

    /* ===== GLASS CARDS ===== */
    .glass-card {{
        background: rgba(17, 17, 17, 0.8);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 28px;
        margin-bottom: 24px;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }}

    .glass-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
    }}

    .glass-card:hover {{
        border-color: rgba(255, 255, 255, 0.1);
        transform: translateY(-2px);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
    }}

    .glass-card-header {{
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 24px;
        padding-bottom: 16px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }}

    .glass-card-icon {{
        width: 40px;
        height: 40px;
        border-radius: 10px;
        background: linear-gradient(135deg, {COR_PRIMARIA}33, {COR_PRIMARIA}11);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
    }}

    .glass-card-title {{
        font-size: 1rem;
        font-weight: 600;
        color: #ffffff;
        letter-spacing: -0.3px;
    }}

    /* ===== FORM INPUTS ===== */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {{
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        color: #ffffff !important;
        font-size: 0.9rem !important;
        padding: 12px 16px !important;
        transition: all 0.3s ease !important;
    }}

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: {COR_PRIMARIA} !important;
        box-shadow: 0 0 0 3px rgba(144, 81, 59, 0.15) !important;
        background: rgba(255, 255, 255, 0.05) !important;
    }}

    .stSelectbox > div > div {{
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
    }}

    .stSelectbox > div > div:hover {{
        border-color: rgba(255, 255, 255, 0.15) !important;
    }}

    .stSlider > div > div > div {{
        background: rgba(255, 255, 255, 0.1) !important;
    }}

    .stSlider > div > div > div > div {{
        background: linear-gradient(90deg, {COR_PRIMARIA}, {COR_PRIMARIA_LIGHT}) !important;
    }}

    /* ===== BUTTONS ===== */
    div.stButton > button {{
        width: 100%;
        background: transparent;
        border: 1px solid rgba(255, 255, 255, 0.12);
        color: #ffffff;
        border-radius: 10px;
        padding: 12px 24px;
        font-size: 0.85rem;
        font-weight: 500;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }}

    div.stButton > button::before {{
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        transition: left 0.5s ease;
    }}

    div.stButton > button:hover {{
        border-color: {COR_PRIMARIA};
        color: {COR_PRIMARIA};
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(144, 81, 59, 0.2);
    }}

    div.stButton > button:hover::before {{
        left: 100%;
    }}

    div.stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {COR_PRIMARIA}, #6b3a2a);
        border: none;
        color: white;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(144, 81, 59, 0.3);
    }}

    div.stButton > button[kind="primary"]:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 30px rgba(144, 81, 59, 0.5);
    }}

    /* Botão adicionar */
    .add-button {{
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(16, 185, 129, 0.05)) !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
        color: {COR_SUCESSO} !important;
    }}

    .add-button:hover {{
        border-color: {COR_SUCESSO} !important;
        box-shadow: 0 10px 30px rgba(16, 185, 129, 0.2) !important;
    }}

    /* ===== METRICS & KPIs ===== */
    .kpi-card {{
        background: rgba(17, 17, 17, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }}

    .kpi-card::after {{
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, transparent, {COR_PRIMARIA}, transparent);
        opacity: 0;
        transition: opacity 0.3s ease;
    }}

    .kpi-card:hover::after {{
        opacity: 1;
    }}

    .kpi-label {{
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: rgba(255, 255, 255, 0.5);
        margin-bottom: 8px;
    }}

    .kpi-value {{
        font-size: 2rem;
        font-weight: 700;
        color: #ffffff;
        font-family: 'JetBrains Mono', monospace !important;
        letter-spacing: -1px;
    }}

    .kpi-value.highlight {{
        background: linear-gradient(135deg, {COR_PRIMARIA}, {COR_PRIMARIA_LIGHT});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}

    .kpi-subtitle {{
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.4);
        margin-top: 4px;
    }}

    /* ===== TEAM TABLE ===== */
    .team-row {{
        display: flex;
        align-items: center;
        padding: 16px 20px;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 12px;
        margin-bottom: 8px;
        transition: all 0.3s ease;
    }}

    .team-row:hover {{
        background: rgba(255, 255, 255, 0.04);
        border-color: rgba(255, 255, 255, 0.08);
        transform: translateX(4px);
    }}

    .team-avatar {{
        width: 40px;
        height: 40px;
        border-radius: 10px;
        background: linear-gradient(135deg, {COR_PRIMARIA}44, {COR_PRIMARIA}22);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.9rem;
        color: {COR_PRIMARIA_LIGHT};
        margin-right: 16px;
    }}

    .team-info {{
        flex: 1;
    }}

    .team-name {{
        font-weight: 600;
        color: #ffffff;
        font-size: 0.9rem;
    }}

    .team-role {{
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.5);
    }}

    .team-value {{
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.9rem;
        color: {COR_SUCESSO};
        font-weight: 500;
    }}

    /* ===== ALERTS ===== */
    .alert-premium {{
        padding: 16px 20px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 24px;
        font-size: 0.85rem;
    }}

    .alert-info {{
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.2);
        color: #93c5fd;
    }}

    .alert-warning {{
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid rgba(245, 158, 11, 0.2);
        color: #fcd34d;
    }}

    .alert-success {{
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.2);
        color: #6ee7b7;
    }}

    /* ===== DIVIDERS ===== */
    .divider {{
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        margin: 32px 0;
    }}

    /* ===== RADIO & TOGGLE ===== */
    .stRadio > div {{
        gap: 16px !important;
    }}

    .stRadio > div > label {{
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        padding: 12px 20px !important;
        transition: all 0.3s ease !important;
    }}

    .stRadio > div > label:hover {{
        border-color: rgba(255, 255, 255, 0.15) !important;
        background: rgba(255, 255, 255, 0.05) !important;
    }}

    .stRadio > div > label[data-checked="true"] {{
        border-color: {COR_PRIMARIA} !important;
        background: rgba(144, 81, 59, 0.1) !important;
    }}

    /* ===== EXPANDER ===== */
    .streamlit-expanderHeader {{
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
    }}

    /* ===== HIDE STREAMLIT DEFAULTS ===== */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}

    .stDeployButton {{display: none;}}

    div[data-testid="stToolbar"] {{display: none;}}

    .stException {{
        background: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
        border-radius: 12px !important;
    }}
</style>

<video autoplay loop muted playsinline id="video-bg">
    <source src="{video_url}" type="video/mp4">
</video>

<div class="header-premium">
    <div class="header-left">
        <img src="{logo_url}" class="logo-premium">
        <div class="header-divider"></div>
        <span class="header-title">Sistema de Precificação</span>
    </div>

</div>
""", unsafe_allow_html=True)


# ==================== FUNÇÕES AUXILIARES ====================

def formatar_moeda(valor):
    """Formata valor em reais BR, trocando ponto por vírgula no final"""
    if isinstance(valor, Decimal):
        valor = float(valor)
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def formatar_moeda_curto(valor):
    """Abreviação pra caber em gráficos (R$ 1.5M, R$ 10K)"""
    if isinstance(valor, Decimal):
        valor = float(valor)
    if valor >= 1000000:
        return f"R$ {valor/1000000:.1f}M"
    elif valor >= 1000:
        return f"R$ {valor/1000:.1f}K"
    return f"R$ {valor:.0f}"


def calcular_custo_funcionario(salario_base, dedicacao_pct, meses):
    """
    Calcula o custo total de um CPF pra Brivia.
    Pega salário -> aplica encargos FPA + benefícios -> aplica % dedicação -> multiplica pelos meses.
    """
    sal = Decimal(str(salario_base))
    ded = Decimal(str(dedicacao_pct)) / Decimal("100")
    m = Decimal(str(meses))

    custo_mensal_cheio = (sal * FATOR_ENCARGOS) + BENEFICIOS_MENSAIS
    custo_mensal_dedicado = custo_mensal_cheio * ded
    custo_total = custo_mensal_dedicado * m

    return float(custo_mensal_cheio), float(custo_mensal_dedicado), float(custo_total)


def calcular_custo_hora(salario_base):
    """Custo hora simples baseado no divisor padrão de 170h"""
    sal = Decimal(str(salario_base))
    custo_mensal = (sal * FATOR_ENCARGOS) + BENEFICIOS_MENSAIS
    return float(custo_mensal / HORAS_MES)


def calcular_pricing_reverso(custo_total, gm_pct, imposto_pct, comissao_pct):
    """
    Markup Reverso (Target Price):
    Preço = Custo / (1 - Deduções)
    
    Se as deduções somarem 100%, dá divisão por zero, então trato ali no if.
    """
    deducoes = (gm_pct + imposto_pct + comissao_pct) / 100
    divisor = 1 - deducoes

    if divisor <= 0:
        return None, 0, 0, 0

    preco_venda = custo_total / divisor
    val_imposto = preco_venda * (imposto_pct / 100)
    val_comissao = preco_venda * (comissao_pct / 100)
    val_gm = preco_venda * (gm_pct / 100)

    return preco_venda, val_imposto, val_comissao, val_gm


# ==================== SESSION STATE ====================

def init_session():
    """Inicializa o estado da aplicação. É aqui que guardamos os dados enquanto o usuário troca de página (fase)."""
    if 'data' not in st.session_state:
        st.session_state.data = {
            'fase': 1,
            'cliente': '',
            'projeto': '',
            'descricao': '',
            'tipo_contrato': TIPOS_CONTRATO[0],
            'tipo_servico': TIPOS_SERVICO[0],
            'meses': 12,
            'imposto_pct': IMPOSTO_PADRAO_PCT,
            'comissao_nb': 0,
            'comissao_parceiros': 0,
            'gm_alvo': GROSS_MARGIN_ALVO,
            'regua_salarial': 'mercado',
            'equipe': [],
            'terceiros': [],
            'custos_extras': {
                'viagens': 0.0,
                'software': 0.0,
                'infraestrutura': 0.0,
                'outros': 0.0
            },
            'obs': ''
        }


# ==================== TIMELINE RENDER ====================

def render_timeline(fase_atual):
    """
    Barra de progresso visual no topo.
    Muda a classe CSS (active, completed) dependendo da fase atual.
    """
    steps = [
        ("1", "Estratégia"),
        ("2", "Equipe"),
        ("3", "Custos"),
        ("4", "Resultado")
    ]

    html = '<div class="timeline-container">'

    for i, (num, label) in enumerate(steps):
        fase_num = i + 1

        if fase_num == fase_atual:
            status = "active"
        elif fase_num < fase_atual:
            status = "completed"
        else:
            status = "pending"

        html += f'''
        <div class="timeline-step {status}">
            <div class="timeline-number">{num if status != "completed" else "&#10003;"}</div>
            <span>{label}</span>
        </div>
        '''

        if i < len(steps) - 1:
            connector_status = "completed" if fase_num < fase_atual else ""
            html += f'<div class="timeline-connector {connector_status}"></div>'

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# ==================== FASE 1: ESTRATÉGIA ====================

def fase_1_estrategia():
    """Fase 1: Coleta os dados macro do projeto (nome, escopo) e define as margens alvo."""
    
    col1, col2 = st.columns(2)

    with col1:
        st.session_state.data['cliente'] = st.text_input(
            "Nome do Cliente",
            value=st.session_state.data['cliente'],
            placeholder="Ex: Empresa ABC Ltda"
        )

        st.session_state.data['tipo_contrato'] = st.selectbox(
            "Modelo de Contrato",
            TIPOS_CONTRATO,
            index=TIPOS_CONTRATO.index(st.session_state.data['tipo_contrato'])
        )

        st.session_state.data['meses'] = st.number_input(
            "Duração do Contrato (meses)",
            min_value=1,
            max_value=60,
            value=st.session_state.data['meses']
        )

    with col2:
        st.session_state.data['projeto'] = st.text_input(
            "Nome do Projeto",
            value=st.session_state.data['projeto'],
            placeholder="Ex: Transformação Digital 2024"
        )

        st.session_state.data['tipo_servico'] = st.selectbox(
            "Vertical de Serviço",
            TIPOS_SERVICO,
            index=TIPOS_SERVICO.index(st.session_state.data['tipo_servico'])
        )

        st.session_state.data['imposto_pct'] = st.number_input(
            "Alíquota de Imposto (%)",
            min_value=0.0,
            max_value=30.0,
            value=st.session_state.data['imposto_pct'],
            step=0.5,
            help="Alíquota média de impostos sobre a nota fiscal"
        )

    st.session_state.data['descricao'] = st.text_area(
        "Descrição do Escopo",
        value=st.session_state.data['descricao'],
        placeholder="Descreva brevemente os serviços a serem prestados...",
        height=80
    )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.session_state.data['comissao_nb'] = st.selectbox(
            "Comissão New Business (%)",
            COMISSAO_NB,
            index=COMISSAO_NB.index(st.session_state.data['comissao_nb']),
            help="Comissão para novos negócios"
        )

    with col2:
        st.session_state.data['comissao_parceiros'] = st.selectbox(
            "Comissão Parceiros (%)",
            COMISSAO_PARCEIROS,
            index=COMISSAO_PARCEIROS.index(st.session_state.data['comissao_parceiros']),
            help="Comissão para parceiros indicadores"
        )

    with col3:
        st.session_state.data['gm_alvo'] = st.slider(
            "Meta de Gross Margin (%)",
            min_value=20.0,
            max_value=70.0,
            value=st.session_state.data['gm_alvo'],
            step=1.0
        )

    # Cálculo dinâmico das deduções pra avisar se o negócio tá inviável antes de prosseguir
    total_deducoes = (
        st.session_state.data['imposto_pct'] +
        st.session_state.data['comissao_nb'] +
        st.session_state.data['comissao_parceiros'] +
        st.session_state.data['gm_alvo']
    )

    st.markdown(f'''
    <div class="alert-premium alert-info">
        <span>&#9432;</span>
        <span>Total de deduções sobre receita: <strong>{total_deducoes:.1f}%</strong>
        (Imposto: {st.session_state.data['imposto_pct']}% +
        NB: {st.session_state.data['comissao_nb']}% +
        Parceiros: {st.session_state.data['comissao_parceiros']}% +
        GM: {st.session_state.data['gm_alvo']}%)</span>
    </div>
    ''', unsafe_allow_html=True)

    if total_deducoes >= 100:
        st.markdown(f'''
        <div class="alert-premium alert-warning">
            <span>&#9888;</span>
            <span>Atenção: As deduções somam {total_deducoes:.1f}%, o que torna o pricing inviável. Reduza as margens.</span>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Botões de navegação
    col1, col2, col3 = st.columns([2, 1, 2])

    with col2:
        # Só libera avançar se tiver dados básicos
        pode_avancar = (
            st.session_state.data['cliente'].strip() != '' and
            st.session_state.data['projeto'].strip() != '' and
            total_deducoes < 100
        )

        if pode_avancar:
            if st.button("Avançar para Equipe", type="primary", use_container_width=True):
                st.session_state.data['fase'] = 2
                st.rerun()
        else:
            st.button("Preencha Cliente e Projeto", disabled=True, use_container_width=True)


# ==================== FASE 2: EQUIPE ====================

def fase_2_equipe():
    """Fase 2: Montagem do Squad. Escolha de profissionais, nível e cálculo de custo."""
    
    meses = st.session_state.data['meses']

    # Escolha da faixa salarial base (Mercado costuma ser mais baixo, Brivia é nossa realidade)
    opcoes_regua = {
        "Média de Mercado": "mercado",
        "Faixa Mínima": "minima",
        "Média Brivia": "brivia"
    }

    regua_label = st.radio(
        "Selecione a régua salarial de referência:",
        list(opcoes_regua.keys()),
        horizontal=True,
        index=list(opcoes_regua.values()).index(st.session_state.data['regua_salarial'])
    )
    st.session_state.data['regua_salarial'] = opcoes_regua[regua_label]

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Card visual para adicionar profissional
    st.markdown(f'''
    <div class="glass-card">
        <div class="glass-card-header">
            <span class="glass-card-title">Squad Builder - {meses} meses de contrato</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns([2.5, 1.5, 1, 1])

    with col1:
        perfil = st.selectbox("Perfil Profissional", list(BASE_SALARIAL.keys()))
        niveis_disponiveis = list(BASE_SALARIAL[perfil].keys())

    with col2:
        nivel = st.selectbox("Senioridade", niveis_disponiveis)

    with col3:
        qtd = st.number_input("Qtd", min_value=1, max_value=20, value=1)

    with col4:
        dedicacao = st.number_input("Dedicação %", min_value=10, max_value=100, value=100, step=10)

    # Preview do custo em tempo real antes de adicionar
    regua_id = st.session_state.data['regua_salarial']
    salario_base = BASE_SALARIAL.get(perfil, {}).get(nivel, {}).get(regua_id, 0)
    custo_hora = calcular_custo_hora(salario_base) if salario_base > 0 else 0
    _, custo_dedicado, custo_total = calcular_custo_funcionario(salario_base, dedicacao, meses)
    custo_item = custo_total * qtd

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'''
        <div class="kpi-card">
            <div class="kpi-label">Salário Base</div>
            <div class="kpi-value">{formatar_moeda(salario_base)}</div>
        </div>
        ''', unsafe_allow_html=True)
    with col2:
        st.markdown(f'''
        <div class="kpi-card">
            <div class="kpi-label">Custo/Hora</div>
            <div class="kpi-value">{formatar_moeda(custo_hora)}</div>
        </div>
        ''', unsafe_allow_html=True)
    with col3:
        st.markdown(f'''
        <div class="kpi-card">
            <div class="kpi-label">Custo Mensal</div>
            <div class="kpi-value">{formatar_moeda(custo_dedicado)}</div>
        </div>
        ''', unsafe_allow_html=True)
    with col4:
        st.markdown(f'''
        <div class="kpi-card">
            <div class="kpi-label">Custo Total ({qtd}x)</div>
            <div class="kpi-value highlight">{formatar_moeda(custo_item)}</div>
        </div>
        ''', unsafe_allow_html=True)

    if st.button("+ Adicionar Profissional", use_container_width=True):
        st.session_state.data['equipe'].append({
            "perfil": perfil,
            "nivel": nivel,
            "qtd": qtd,
            "dedicacao": dedicacao,
            "salario_base": salario_base,
            "regua": regua_id
        })
        st.rerun()

    # Listagem da equipe já montada
    if st.session_state.data['equipe']:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        st.markdown('''
        <div class="glass-card">
            <div class="glass-card-header">
                <span class="glass-card-title">Equipe</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        total_equipe = 0
        total_headcount = 0

        for i, item in enumerate(st.session_state.data['equipe']):
            _, _, custo_tot = calcular_custo_funcionario(
                item['salario_base'],
                item['dedicacao'],
                meses
            )
            custo_item = custo_tot * item['qtd']
            total_equipe += custo_item
            total_headcount += item['qtd']

            # Pegar inicial do perfil pra fazer o avatar
            inicial = item['perfil'][0].upper()

            col1, col2 = st.columns([10, 1])

            with col1:
                st.markdown(f'''
                <div class="team-row">
                    <div class="team-avatar">{inicial}</div>
                    <div class="team-info">
                        <div class="team-name">{item['qtd']}x {item['perfil']}</div>
                        <div class="team-role">{item['nivel']} | {item['dedicacao']}% dedicação</div>
                    </div>
                    <div class="team-value">{formatar_moeda(custo_item)}</div>
                </div>
                ''', unsafe_allow_html=True)

            with col2:
                if st.button("X", key=f"del_equipe_{i}", help="Remover"):
                    st.session_state.data['equipe'].pop(i)
                    st.rerun()

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # Resumo da fase
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'''
            <div class="kpi-card">
                <div class="kpi-label">Total Headcount</div>
                <div class="kpi-value">{total_headcount}</div>
                <div class="kpi-subtitle">profissionais</div>
            </div>
            ''', unsafe_allow_html=True)
        with col2:
            st.markdown(f'''
            <div class="kpi-card">
                <div class="kpi-label">Custo Total Equipe</div>
                <div class="kpi-value highlight">{formatar_moeda(total_equipe)}</div>
                <div class="kpi-subtitle">{meses} meses</div>
            </div>
            ''', unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Voltar", use_container_width=True):
            st.session_state.data['fase'] = 1
            st.rerun()
    with col2:
        if st.button("Avançar para Custos", type="primary", use_container_width=True):
            st.session_state.data['fase'] = 3
            st.rerun()


# ==================== FASE 3: CUSTOS ====================

def fase_3_custos():
    """Fase 3: Adição de custos de terceiros (freelas) e custos operacionais extras."""
    
    meses = st.session_state.data['meses']

    # Seção de Terceiros
    st.markdown('''
    <div class="glass-card">
        <div class="glass-card-header">
            <span class="glass-card-title">Terceiros e Fornecedores</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([3, 2, 1])

    with col1:
        desc_terceiro = st.text_input(
            "Descrição",
            placeholder="Ex: Freelancer Design, Consultoria AWS, etc"
        )

    with col2:
        val_terceiro = st.number_input(
            "Valor Total (R$)",
            min_value=0.0,
            step=500.0,
            format="%.2f"
        )

    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("+ Add", use_container_width=True):
            if desc_terceiro and val_terceiro > 0:
                st.session_state.data['terceiros'].append({
                    'desc': desc_terceiro,
                    'valor': val_terceiro
                })
                st.rerun()

    # Listagem de terceiros adicionados
    if st.session_state.data['terceiros']:
        total_terceiros = 0
        for i, t in enumerate(st.session_state.data['terceiros']):
            total_terceiros += t['valor']
            col1, col2 = st.columns([10, 1])
            with col1:
                st.markdown(f'''
                <div class="team-row">
                    <div class="team-avatar">T</div>
                    <div class="team-info">
                        <div class="team-name">{t['desc']}</div>
                        <div class="team-role">Terceirizado</div>
                    </div>
                    <div class="team-value">{formatar_moeda(t['valor'])}</div>
                </div>
                ''', unsafe_allow_html=True)
            with col2:
                if st.button("X", key=f"del_terc_{i}"):
                    st.session_state.data['terceiros'].pop(i)
                    st.rerun()

        st.markdown(f'''
        <div class="alert-premium alert-info">
            <span>Total Terceiros: <strong>{formatar_moeda(total_terceiros)}</strong></span>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Custos Operacionais (OPEX)
    st.markdown('''
    <div class="glass-card">
        <div class="glass-card-header">
            <span class="glass-card-title">Custos Operacionais (valor mensal)</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.session_state.data['custos_extras']['viagens'] = st.number_input(
            "Viagens e Deslocamentos",
            min_value=0.0,
            value=st.session_state.data['custos_extras']['viagens'],
            step=100.0,
            help="Custo mensal estimado com viagens"
        )

        st.session_state.data['custos_extras']['software'] = st.number_input(
            "Software e Licenças",
            min_value=0.0,
            value=st.session_state.data['custos_extras']['software'],
            step=100.0,
            help="Custo mensal com ferramentas e licenças"
        )

    with col2:
        st.session_state.data['custos_extras']['infraestrutura'] = st.number_input(
            "Infraestrutura Cloud",
            min_value=0.0,
            value=st.session_state.data['custos_extras']['infraestrutura'],
            step=100.0,
            help="Custo mensal com servidores, cloud, etc"
        )

        st.session_state.data['custos_extras']['outros'] = st.number_input(
            "Outros Custos",
            min_value=0.0,
            value=st.session_state.data['custos_extras']['outros'],
            step=100.0,
            help="Outros custos operacionais mensais"
        )

    # Totalização do Opex
    extras_mensal = sum(st.session_state.data['custos_extras'].values())
    extras_total = extras_mensal * meses

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'''
        <div class="kpi-card">
            <div class="kpi-label">Opex Mensal</div>
            <div class="kpi-value">{formatar_moeda(extras_mensal)}</div>
        </div>
        ''', unsafe_allow_html=True)
    with col2:
        st.markdown(f'''
        <div class="kpi-card">
            <div class="kpi-label">Opex Total ({meses}m)</div>
            <div class="kpi-value highlight">{formatar_moeda(extras_total)}</div>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Campo livre para observações
    st.session_state.data['obs'] = st.text_area(
        "Observações Gerais",
        value=st.session_state.data['obs'],
        placeholder="Informações adicionais, premissas, riscos...",
        height=80
    )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Voltar", use_container_width=True):
            st.session_state.data['fase'] = 2
            st.rerun()
    with col2:
        if st.button("Calcular Pricing", type="primary", use_container_width=True):
            st.session_state.data['fase'] = 4
            st.rerun()


# ==================== FASE 4: RESULTADO/DASHBOARD ====================

def fase_4_dashboard():
    """Fase 4: Dashboard final. Consolida custos, aplica markup e gera gráficos."""
    
    meses = st.session_state.data['meses']

    # 1. Somatória de custos
    custo_equipe = 0
    for item in st.session_state.data['equipe']:
        _, _, tot = calcular_custo_funcionario(item['salario_base'], item['dedicacao'], meses)
        custo_equipe += (tot * item['qtd'])

    custo_terceiros = sum(t['valor'] for t in st.session_state.data['terceiros'])

    extras_mensal = sum(st.session_state.data['custos_extras'].values())
    custo_extras = extras_mensal * meses

    CUSTO_TOTAL = custo_equipe + custo_terceiros + custo_extras

    comissao_total = st.session_state.data['comissao_nb'] + st.session_state.data['comissao_parceiros']

    # 2. Aplicação do Markup Reverso
    preco_venda, v_imposto, v_comissao, v_gm = calcular_pricing_reverso(
        CUSTO_TOTAL,
        st.session_state.data['gm_alvo'],
        st.session_state.data['imposto_pct'],
        comissao_total
    )

    if preco_venda is None:
        st.markdown('''
        <div class="alert-premium alert-warning">
            <span>&#9888;</span>
            <span>Erro matemático: A soma das margens e impostos ultrapassa 100%. Reduza os custos ou ajuste as margens.</span>
        </div>
        ''', unsafe_allow_html=True)

        if st.button("Voltar e Ajustar", type="primary"):
            st.session_state.data['fase'] = 1
            st.rerun()
        return

    # Visualização dos KPIs principais
    st.markdown('''
    <div class="glass-card">
        <div class="glass-card-header">
            <span class="glass-card-title">Resultado da Precificação</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f'''
        <div class="kpi-card" style="border-left: 4px solid {COR_PRIMARIA};">
            <div class="kpi-label">Investimento Total</div>
            <div class="kpi-value highlight">{formatar_moeda(preco_venda)}</div>
            <div class="kpi-subtitle">Preço de Venda</div>
        </div>
        ''', unsafe_allow_html=True)

    with col2:
        st.markdown(f'''
        <div class="kpi-card">
            <div class="kpi-label">Fee Mensal</div>
            <div class="kpi-value">{formatar_moeda(preco_venda/meses)}</div>
            <div class="kpi-subtitle">{meses} parcelas</div>
        </div>
        ''', unsafe_allow_html=True)

    with col3:
        st.markdown(f'''
        <div class="kpi-card" style="border-left: 4px solid {COR_SUCESSO};">
            <div class="kpi-label">Margem Bruta</div>
            <div class="kpi-value" style="color: {COR_SUCESSO}">{formatar_moeda(v_gm)}</div>
            <div class="kpi-subtitle">{st.session_state.data['gm_alvo']:.0f}% do preço</div>
        </div>
        ''', unsafe_allow_html=True)

    with col4:
        markup = ((preco_venda / CUSTO_TOTAL) - 1) * 100
        st.markdown(f'''
        <div class="kpi-card">
            <div class="kpi-label">Markup</div>
            <div class="kpi-value">{markup:.1f}%</div>
            <div class="kpi-subtitle">Sobre custo</div>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Gráficos (Pizza e Tabela Detalhada)
    col1, col2 = st.columns([1, 1.5])

    with col1:
        st.markdown("##### Composição do Preço")

        fig = go.Figure(data=[go.Pie(
            labels=['Custo Base', 'Impostos', 'Comissões', 'Margem'],
            values=[CUSTO_TOTAL, v_imposto, v_comissao, v_gm],
            hole=0.65,
            marker_colors=['#374151', '#6b7280', '#9ca3af', COR_PRIMARIA],
            textinfo='percent',
            textfont_size=12,
            textfont_color='white'
        )])

        fig.update_layout(
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(color='white', size=10)
            ),
            margin=dict(t=20, b=60, l=20, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=300,
            annotations=[dict(
                text=f'<b>{formatar_moeda_curto(preco_venda)}</b>',
                x=0.5, y=0.5,
                font_size=18,
                font_color='white',
                showarrow=False
            )]
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("##### Detalhamento Financeiro")

        df_detalhe = pd.DataFrame({
            "Categoria": [
                "Equipe CLT",
                "Terceiros",
                "Opex/Viagens",
                "= CUSTO BASE",
                "Impostos",
                "Comissões",
                "= LUCRO BRUTO"
            ],
            "Valor": [
                formatar_moeda(custo_equipe),
                formatar_moeda(custo_terceiros),
                formatar_moeda(custo_extras),
                formatar_moeda(CUSTO_TOTAL),
                formatar_moeda(v_imposto),
                formatar_moeda(v_comissao),
                formatar_moeda(v_gm)
            ],
            "% Preço": [
                f"{(custo_equipe/preco_venda)*100:.1f}%",
                f"{(custo_terceiros/preco_venda)*100:.1f}%",
                f"{(custo_extras/preco_venda)*100:.1f}%",
                f"{(CUSTO_TOTAL/preco_venda)*100:.1f}%",
                f"{st.session_state.data['imposto_pct']:.1f}%",
                f"{comissao_total:.1f}%",
                f"{st.session_state.data['gm_alvo']:.1f}%"
            ]
        })

        st.dataframe(
            df_detalhe,
            hide_index=True,
            use_container_width=True,
            height=280
        )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Resumo descritivo final
    st.markdown('''
    <div class="glass-card">
        <div class="glass-card-header">
            <span class="glass-card-title">Resumo do Projeto</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        **Cliente:** {st.session_state.data['cliente']}
        **Projeto:** {st.session_state.data['projeto']}
        **Contrato:** {st.session_state.data['tipo_contrato']}
        """)

    with col2:
        st.markdown(f"""
        **Duração:** {meses} meses
        **Vertical:** {st.session_state.data['tipo_servico']}
        **Oferta:** {MAPEAMENTO_OFERTAS.get(st.session_state.data['tipo_servico'], '-')}
        """)

    with col3:
        total_hc = sum(item['qtd'] for item in st.session_state.data['equipe'])
        st.markdown(f"""
        **Headcount:** {total_hc} profissionais
        **Terceiros:** {len(st.session_state.data['terceiros'])}
        **GM Alvo:** {st.session_state.data['gm_alvo']:.0f}%
        """)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Ações Finais (Reiniciar, Editar, Exportar)
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Reiniciar Precificação", use_container_width=True):
            st.session_state.data = None
            st.rerun()

    with col2:
        if st.button("Voltar e Editar", use_container_width=True):
            st.session_state.data['fase'] = 1
            st.rerun()

    with col3:
        # Exportação para JSON
        export_data = {
            "metadata": {
                "versao": "3.0 PRO",
                "data_geracao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "sistema": "Brivia Pricing Pro"
            },
            "projeto": {
                "cliente": st.session_state.data['cliente'],
                "nome": st.session_state.data['projeto'],
                "descricao": st.session_state.data['descricao'],
                "tipo_contrato": st.session_state.data['tipo_contrato'],
                "tipo_servico": st.session_state.data['tipo_servico'],
                "duracao_meses": meses
            },
            "configuracao": {
                "imposto_pct": st.session_state.data['imposto_pct'],
                "comissao_nb_pct": st.session_state.data['comissao_nb'],
                "comissao_parceiros_pct": st.session_state.data['comissao_parceiros'],
                "gross_margin_alvo_pct": st.session_state.data['gm_alvo'],
                "regua_salarial": st.session_state.data['regua_salarial']
            },
            "equipe": st.session_state.data['equipe'],
            "terceiros": st.session_state.data['terceiros'],
            "custos_extras": st.session_state.data['custos_extras'],
            "resultado": {
                "custo_equipe": custo_equipe,
                "custo_terceiros": custo_terceiros,
                "custo_extras": custo_extras,
                "custo_total": CUSTO_TOTAL,
                "preco_venda": preco_venda,
                "preco_mensal": preco_venda / meses,
                "impostos": v_imposto,
                "comissoes": v_comissao,
                "margem_bruta": v_gm,
                "markup_pct": markup
            },
            "observacoes": st.session_state.data['obs']
        }

        json_str = json.dumps(export_data, indent=2, ensure_ascii=False, default=str)

        st.download_button(
            label="Exportar JSON",
            data=json_str,
            file_name=f"pricing_{st.session_state.data['cliente'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            type="primary",
            use_container_width=True
        )


# ==================== MAIN ====================

def main():
    """Roteador principal. Verifica qual fase está no state e renderiza a view correspondente."""
    init_session()
    render_timeline(st.session_state.data['fase'])

    if st.session_state.data['fase'] == 1:
        fase_1_estrategia()
    elif st.session_state.data['fase'] == 2:
        fase_2_equipe()
    elif st.session_state.data['fase'] == 3:
        fase_3_custos()
    elif st.session_state.data['fase'] == 4:
        fase_4_dashboard()


if __name__ == "__main__":
    main()
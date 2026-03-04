"""
Brivia Pricing PRO · v4.0
Multi-page · SQLite · Analytics · Excel Import
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sqlite3
import json
import random
import io
import os
from datetime import datetime, timedelta
from decimal import Decimal, getcontext
from pathlib import Path

try:
    import openpyxl
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    EXCEL_OK = True
except ImportError:
    EXCEL_OK = False

getcontext().prec = 20

# ==================== PAGE CONFIG ====================

st.set_page_config(
    page_title="Brivia Pricing PRO",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CONSTANTS ====================

DB_PATH = Path(__file__).parent / "brivia_pricing.db"
LOGO_URL = "https://cdn.prod.website-files.com/65c2dcb4330facd527e06bdd/6619a7597575e945de440959_brivia_group.svg"

TIPOS_CONTRATO = [
    "Fee Mensal (Recorrente)",
    "Projeto (Escopo Fechado)",
    "Sustentação",
    "Consultoria Estratégica"
]
TIPOS_SERVICO = [
    "Tecnologia / Dev",
    "Design / UX",
    "Dados / Analytics",
    "Marketing / Growth",
    "Estratégia Digital"
]
STATUS_LIST = ["Rascunho", "Em Análise", "Aprovada", "Rejeitada", "Em Execução", "Concluída", "Cancelada"]
STATUS_COLORS = {
    "Rascunho":     "#6b7280",
    "Em Análise":   "#3b82f6",
    "Aprovada":     "#10b981",
    "Rejeitada":    "#ef4444",
    "Em Execução":  "#f59e0b",
    "Concluída":    "#c58f3d",
    "Cancelada":    "#9ca3af",
}
MAPEAMENTO_OFERTAS = {
    "Tecnologia / Dev":   "Tech Squad",
    "Design / UX":        "Design Studio",
    "Dados / Analytics":  "Data Intelligence",
    "Marketing / Growth": "Growth Lab",
    "Estratégia Digital": "Strategy Hub",
}

COMISSAO_NB       = [0, 5, 7, 10, 12, 15]
COMISSAO_PARCEIROS = [0, 5, 10, 15, 20, 25]
GROSS_MARGIN_ALVO  = 45.0
IMPOSTO_PADRAO_PCT = 14.25
BENEFICIOS_MENSAIS = Decimal("1190")
HORAS_MES          = Decimal("170")

_P13 = Decimal("100") / Decimal("12")
_PFE = Decimal("11.1110833333333")
ENCARGOS_FPA = {
    "fgts_base":      Decimal("8.00"),
    "fgts_s_13":      _P13 * Decimal("0.08"),
    "fgts_s_ferias":  _PFE * Decimal("0.08"),
    "inss_base":      Decimal("26.30"),
    "inss_s_13":      _P13 * Decimal("0.263"),
    "inss_s_ferias":  _PFE * Decimal("0.263"),
    "prov_13":        _P13,
    "prov_ferias":    _PFE,
    "aviso_previo":   Decimal("1.32"),
    "aux_doenca":     Decimal("0.55"),
    "rescisao":       Decimal("2.57"),
}
FATOR_ENCARGOS = Decimal("1") + (sum(ENCARGOS_FPA.values()) / Decimal("100"))

BASE_SALARIAL = {
    "Desenvolvedor Fullstack": {
        "1. Júnior": {"mercado": 4500,  "minima": 3800,  "brivia": 5000},
        "2. Pleno":  {"mercado": 7500,  "minima": 6500,  "brivia": 8500},
        "3. Sênior": {"mercado": 11000, "minima": 9500,  "brivia": 13000},
        "4. Líder":  {"mercado": 14000, "minima": 12000, "brivia": 16000},
        "5. Head":   {"mercado": 18000, "minima": 15000, "brivia": 22000},
    },
    "Desenvolvedor Frontend": {
        "1. Júnior": {"mercado": 4000,  "minima": 3500,  "brivia": 4500},
        "2. Pleno":  {"mercado": 6500,  "minima": 5500,  "brivia": 7500},
        "3. Sênior": {"mercado": 10000, "minima": 8500,  "brivia": 12000},
        "4. Líder":  {"mercado": 13000, "minima": 11000, "brivia": 15000},
        "5. Head":   {"mercado": 17000, "minima": 14000, "brivia": 20000},
    },
    "Desenvolvedor Backend": {
        "1. Júnior": {"mercado": 4500,  "minima": 3800,  "brivia": 5000},
        "2. Pleno":  {"mercado": 7500,  "minima": 6500,  "brivia": 8500},
        "3. Sênior": {"mercado": 11500, "minima": 10000, "brivia": 13500},
        "4. Líder":  {"mercado": 14500, "minima": 12500, "brivia": 17000},
        "5. Head":   {"mercado": 19000, "minima": 16000, "brivia": 23000},
    },
    "Cientista de Dados": {
        "1. Júnior": {"mercado": 5500,  "minima": 4500,  "brivia": 6500},
        "2. Pleno":  {"mercado": 9000,  "minima": 7500,  "brivia": 10500},
        "3. Sênior": {"mercado": 13500, "minima": 11500, "brivia": 16000},
        "4. Líder":  {"mercado": 17000, "minima": 14500, "brivia": 20000},
        "5. Head":   {"mercado": 22000, "minima": 18000, "brivia": 26000},
    },
    "Engenheiro de Dados": {
        "1. Júnior": {"mercado": 5000,  "minima": 4200,  "brivia": 5800},
        "2. Pleno":  {"mercado": 8500,  "minima": 7200,  "brivia": 10000},
        "3. Sênior": {"mercado": 13000, "minima": 11000, "brivia": 15500},
        "4. Líder":  {"mercado": 16500, "minima": 14000, "brivia": 19500},
        "5. Head":   {"mercado": 21000, "minima": 17500, "brivia": 25000},
    },
    "UX Designer": {
        "1. Júnior": {"mercado": 4000,  "minima": 3200,  "brivia": 4500},
        "2. Pleno":  {"mercado": 6500,  "minima": 5500,  "brivia": 7500},
        "3. Sênior": {"mercado": 9500,  "minima": 8000,  "brivia": 11000},
        "4. Líder":  {"mercado": 12500, "minima": 10500, "brivia": 14500},
        "5. Head":   {"mercado": 16000, "minima": 13500, "brivia": 19000},
    },
    "UI Designer": {
        "1. Júnior": {"mercado": 3800,  "minima": 3000,  "brivia": 4200},
        "2. Pleno":  {"mercado": 6000,  "minima": 5000,  "brivia": 7000},
        "3. Sênior": {"mercado": 9000,  "minima": 7500,  "brivia": 10500},
        "4. Líder":  {"mercado": 12000, "minima": 10000, "brivia": 14000},
        "5. Head":   {"mercado": 15500, "minima": 13000, "brivia": 18000},
    },
    "Product Manager": {
        "1. Júnior": {"mercado": 5000,  "minima": 4200,  "brivia": 5800},
        "2. Pleno":  {"mercado": 8500,  "minima": 7200,  "brivia": 10000},
        "3. Sênior": {"mercado": 13000, "minima": 11000, "brivia": 15000},
        "4. Líder":  {"mercado": 17000, "minima": 14500, "brivia": 20000},
        "5. Head":   {"mercado": 22000, "minima": 18500, "brivia": 26000},
    },
    "Tech Lead": {
        "3. Sênior": {"mercado": 14000, "minima": 12000, "brivia": 16500},
        "4. Líder":  {"mercado": 18000, "minima": 15500, "brivia": 21000},
        "5. Head":   {"mercado": 24000, "minima": 20000, "brivia": 28000},
    },
    "DevOps/SRE": {
        "1. Júnior": {"mercado": 5000,  "minima": 4200,  "brivia": 5800},
        "2. Pleno":  {"mercado": 8500,  "minima": 7200,  "brivia": 10000},
        "3. Sênior": {"mercado": 13000, "minima": 11000, "brivia": 15500},
        "4. Líder":  {"mercado": 17000, "minima": 14500, "brivia": 20000},
        "5. Head":   {"mercado": 22000, "minima": 18500, "brivia": 26000},
    },
    "Analista de Marketing": {
        "1. Júnior": {"mercado": 3500,  "minima": 2800,  "brivia": 4000},
        "2. Pleno":  {"mercado": 5500,  "minima": 4500,  "brivia": 6500},
        "3. Sênior": {"mercado": 8500,  "minima": 7000,  "brivia": 10000},
        "4. Líder":  {"mercado": 12000, "minima": 10000, "brivia": 14000},
        "5. Head":   {"mercado": 16000, "minima": 13500, "brivia": 19000},
    },
    "Scrum Master": {
        "2. Pleno":  {"mercado": 7000,  "minima": 5800,  "brivia": 8200},
        "3. Sênior": {"mercado": 10500, "minima": 9000,  "brivia": 12500},
        "4. Líder":  {"mercado": 14000, "minima": 12000, "brivia": 16500},
        "5. Head":   {"mercado": 18000, "minima": 15000, "brivia": 21000},
    },
}

COR_PRIMARIA  = "#c58f3d"
COR_ACENTO    = "#3b82f6"
COR_SUCESSO   = "#10b981"
COR_ALERTA    = "#f59e0b"
COR_ERRO      = "#ef4444"

CHART_COLORS = [COR_PRIMARIA, COR_ACENTO, COR_SUCESSO, COR_ALERTA, "#8b5cf6", "#ec4899", "#06b6d4"]

# ==================== DATABASE LAYER ====================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS propostas (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at      TEXT    DEFAULT (datetime('now','localtime')),
                updated_at      TEXT    DEFAULT (datetime('now','localtime')),
                status          TEXT    DEFAULT 'Rascunho',
                cliente         TEXT    NOT NULL,
                segmento        TEXT,
                projeto         TEXT    NOT NULL,
                descricao       TEXT,
                tipo_contrato   TEXT,
                tipo_servico    TEXT,
                meses           INTEGER DEFAULT 12,
                imposto_pct     REAL    DEFAULT 14.25,
                comissao_nb     REAL    DEFAULT 0,
                comissao_parc   REAL    DEFAULT 0,
                gm_alvo         REAL    DEFAULT 45,
                regua_salarial  TEXT    DEFAULT 'mercado',
                custo_equipe    REAL    DEFAULT 0,
                custo_terceiros REAL    DEFAULT 0,
                custo_extras    REAL    DEFAULT 0,
                custo_total     REAL    DEFAULT 0,
                preco_venda     REAL    DEFAULT 0,
                fee_mensal      REAL    DEFAULT 0,
                v_impostos      REAL    DEFAULT 0,
                v_comissoes     REAL    DEFAULT 0,
                margem_bruta    REAL    DEFAULT 0,
                markup_pct      REAL    DEFAULT 0,
                headcount       INTEGER DEFAULT 0,
                responsavel     TEXT,
                obs             TEXT
            );

            CREATE TABLE IF NOT EXISTS proposta_equipe (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                proposta_id INTEGER NOT NULL,
                perfil      TEXT,
                nivel       TEXT,
                qtd         INTEGER DEFAULT 1,
                dedicacao   REAL    DEFAULT 100,
                salario_base REAL   DEFAULT 0,
                regua       TEXT,
                FOREIGN KEY (proposta_id) REFERENCES propostas(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS proposta_terceiros (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                proposta_id INTEGER NOT NULL,
                descricao   TEXT,
                valor       REAL DEFAULT 0,
                FOREIGN KEY (proposta_id) REFERENCES propostas(id) ON DELETE CASCADE
            );
        """)


def db_count():
    with get_db() as conn:
        return conn.execute("SELECT COUNT(*) FROM propostas").fetchone()[0]


def db_get_all(filtros=None):
    query = "SELECT * FROM propostas"
    params = []
    conds  = []
    if filtros:
        if filtros.get("status"):
            conds.append("status = ?"); params.append(filtros["status"])
        if filtros.get("tipo_servico"):
            conds.append("tipo_servico = ?"); params.append(filtros["tipo_servico"])
        if filtros.get("tipo_contrato"):
            conds.append("tipo_contrato = ?"); params.append(filtros["tipo_contrato"])
        if filtros.get("cliente"):
            conds.append("cliente LIKE ?"); params.append(f"%{filtros['cliente']}%")
    if conds:
        query += " WHERE " + " AND ".join(conds)
    query += " ORDER BY created_at DESC"
    with get_db() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


def db_get_one(pid):
    with get_db() as conn:
        p = conn.execute("SELECT * FROM propostas WHERE id=?", (pid,)).fetchone()
        eq = conn.execute("SELECT * FROM proposta_equipe WHERE proposta_id=?", (pid,)).fetchall()
        te = conn.execute("SELECT * FROM proposta_terceiros WHERE proposta_id=?", (pid,)).fetchall()
        if not p:
            return None, [], []
        return dict(p), [dict(e) for e in eq], [dict(t) for t in te]


def db_save(data, equipe, terceiros):
    with get_db() as conn:
        pid = data.get("id")
        fields = (
            data["status"], data["cliente"], data.get("segmento", ""),
            data["projeto"], data.get("descricao", ""),
            data["tipo_contrato"], data["tipo_servico"], data["meses"],
            data["imposto_pct"], data["comissao_nb"], data["comissao_parc"],
            data["gm_alvo"], data["regua_salarial"],
            data["custo_equipe"], data["custo_terceiros"], data["custo_extras"],
            data["custo_total"], data["preco_venda"], data["fee_mensal"],
            data["v_impostos"], data["v_comissoes"], data["margem_bruta"],
            data["markup_pct"], data["headcount"],
            data.get("responsavel", ""), data.get("obs", ""),
        )
        if pid:
            conn.execute("""
                UPDATE propostas SET
                    updated_at=datetime('now','localtime'), status=?, cliente=?, segmento=?,
                    projeto=?, descricao=?, tipo_contrato=?, tipo_servico=?, meses=?,
                    imposto_pct=?, comissao_nb=?, comissao_parc=?, gm_alvo=?, regua_salarial=?,
                    custo_equipe=?, custo_terceiros=?, custo_extras=?, custo_total=?,
                    preco_venda=?, fee_mensal=?, v_impostos=?, v_comissoes=?,
                    margem_bruta=?, markup_pct=?, headcount=?, responsavel=?, obs=?
                WHERE id=?
            """, (*fields, pid))
            conn.execute("DELETE FROM proposta_equipe WHERE proposta_id=?", (pid,))
            conn.execute("DELETE FROM proposta_terceiros WHERE proposta_id=?", (pid,))
        else:
            cur = conn.execute("""
                INSERT INTO propostas (
                    status, cliente, segmento, projeto, descricao,
                    tipo_contrato, tipo_servico, meses,
                    imposto_pct, comissao_nb, comissao_parc, gm_alvo, regua_salarial,
                    custo_equipe, custo_terceiros, custo_extras, custo_total,
                    preco_venda, fee_mensal, v_impostos, v_comissoes,
                    margem_bruta, markup_pct, headcount, responsavel, obs
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, fields)
            pid = cur.lastrowid

        for e in equipe:
            conn.execute(
                "INSERT INTO proposta_equipe (proposta_id,perfil,nivel,qtd,dedicacao,salario_base,regua) VALUES (?,?,?,?,?,?,?)",
                (pid, e["perfil"], e["nivel"], e["qtd"], e["dedicacao"], e["salario_base"], e["regua"]),
            )
        for t in terceiros:
            conn.execute(
                "INSERT INTO proposta_terceiros (proposta_id,descricao,valor) VALUES (?,?,?)",
                (pid, t["desc"], t["valor"]),
            )
        return pid


def db_delete(pid):
    with get_db() as conn:
        conn.execute("DELETE FROM propostas WHERE id=?", (pid,))


def db_update_status(pid, status):
    with get_db() as conn:
        conn.execute(
            "UPDATE propostas SET status=?, updated_at=datetime('now','localtime') WHERE id=?",
            (status, pid),
        )

# ==================== ARTIFICIAL DATA SEED ====================

_CLIENTES = [
    ("Itaú Unibanco", "Banco"), ("Nubank", "Fintech"),
    ("Magazine Luiza", "Varejo"), ("B3 - Bolsa de Valores", "Mercado de Capitais"),
    ("Ambev", "Bebidas/FMCG"), ("Petrobras", "Energia"),
    ("Grupo Globo", "Mídia"), ("Embraer", "Aeroespacial"),
    ("Santander Brasil", "Banco"), ("Vivo Telefônica", "Telecom"),
    ("Hapvida Intermédica", "Saúde"), ("Vale", "Mineração"),
    ("Cielo", "Meios de Pagamento"), ("XP Inc.", "Investimentos"),
    ("Mercado Livre", "E-commerce"), ("iFood", "Foodtech"),
    ("TOTVS", "ERP/Software"), ("Localiza Hertz", "Mobilidade"),
    ("Rede D'Or São Luiz", "Saúde"), ("Porto Seguro", "Seguros"),
]
_PROJETOS = {
    "Tecnologia / Dev": [
        "Plataforma Digital de Serviços", "Modernização de Core Bancário",
        "Squad Dedicado Full-Stack", "API Gateway e Microsserviços",
        "Aplicativo Mobile B2C", "Portal do Cliente 2.0",
        "Automação de Processos Críticos", "Migração para Cloud AWS",
        "Sistema de Onboarding Digital", "Plataforma de Pagamentos PIX",
    ],
    "Design / UX": [
        "Redesign de Experiência do Usuário", "Design System Corporativo",
        "Research & Discovery Sprint", "UX para App Mobile iOS/Android",
        "Identidade Visual Digital", "Auditoria de Acessibilidade UI",
    ],
    "Dados / Analytics": [
        "Data Lake Corporativo", "Dashboard Executivo BI",
        "Modelo Preditivo de Churn", "Data Governance Implementation",
        "Analytics em Tempo Real", "CDP - Customer Data Platform",
        "Engenharia de Features ML", "Data Mesh Architecture",
    ],
    "Marketing / Growth": [
        "Growth Hacking para Aquisição", "Performance Marketing Digital",
        "CRM e Automação de Marketing", "SEO e Estratégia de Conteúdo",
        "Retenção e Loyalty Program", "Social Commerce Strategy",
    ],
    "Estratégia Digital": [
        "Transformação Digital Corporativa", "Roadmap Tecnológico 2025-2027",
        "Assessment de Maturidade Digital", "Consultoria em Inovação Aberta",
        "Due Diligence Tecnológica", "OKRs e Gestão Ágil de Portfólio",
    ],
}
_RESPONSAVEIS = [
    "Ana Paula Ferreira", "Carlos Eduardo Lima", "Fernanda Souza",
    "Rafael Moreira", "Juliana Castro", "Bruno Alves",
    "Gabriela Nunes", "Thiago Ribeiro",
]
_PERFIS_POR_SERVICO = {
    "Tecnologia / Dev": [
        ("Desenvolvedor Fullstack", ["2. Pleno", "3. Sênior"]),
        ("Desenvolvedor Backend",   ["2. Pleno", "3. Sênior"]),
        ("Desenvolvedor Frontend",  ["2. Pleno", "3. Sênior"]),
        ("Tech Lead",               ["3. Sênior", "4. Líder"]),
        ("DevOps/SRE",              ["2. Pleno", "3. Sênior"]),
        ("Scrum Master",            ["2. Pleno", "3. Sênior"]),
    ],
    "Design / UX": [
        ("UX Designer",    ["2. Pleno", "3. Sênior"]),
        ("UI Designer",    ["2. Pleno", "3. Sênior"]),
        ("Product Manager",["2. Pleno", "3. Sênior"]),
    ],
    "Dados / Analytics": [
        ("Cientista de Dados", ["2. Pleno", "3. Sênior"]),
        ("Engenheiro de Dados",["2. Pleno", "3. Sênior"]),
        ("Desenvolvedor Backend",["2. Pleno", "3. Sênior"]),
    ],
    "Marketing / Growth": [
        ("Analista de Marketing", ["2. Pleno", "3. Sênior"]),
        ("UX Designer",           ["2. Pleno"]),
        ("Cientista de Dados",    ["2. Pleno"]),
    ],
    "Estratégia Digital": [
        ("Product Manager",    ["3. Sênior", "4. Líder"]),
        ("Cientista de Dados", ["3. Sênior"]),
        ("Tech Lead",          ["4. Líder"]),
    ],
}
_SERVICOS_TERC = [
    "Consultoria Cloud AWS", "Freelancer Design", "Parceiro QA",
    "Infra Azure", "Licença Figma Pro", "AWS Reserved Instances",
    "Consultoria Segurança", "Suporte Salesforce", "Auditoria Externa",
]


def _custo_item(salario, ded_pct, meses, qtd):
    s = Decimal(str(salario))
    d = Decimal(str(ded_pct)) / Decimal("100")
    return float((s * FATOR_ENCARGOS + BENEFICIOS_MENSAIS) * d * Decimal(str(meses)) * Decimal(str(qtd)))


def _preco_reverso(custo, gm, imp, com):
    div = 1 - (gm + imp + com) / 100
    if div <= 0:
        return custo * 2, 0, 0, 0
    p = custo / div
    return p, p * imp / 100, p * com / 100, p * gm / 100


def seed_data():
    if db_count() > 0:
        return
    random.seed(42)
    start = datetime(2024, 1, 15)
    end   = datetime(2026, 2, 28)
    span  = (end - start).days

    for _ in range(80):
        created = start + timedelta(days=random.randint(0, span))
        cliente, segmento  = random.choice(_CLIENTES)
        tipo_serv = random.choice(TIPOS_SERVICO)
        tipo_cont = random.choice(TIPOS_CONTRATO)
        projeto   = random.choice(_PROJETOS[tipo_serv])
        meses     = random.choice([3, 6, 9, 12, 12, 18, 24])
        imp       = random.choice([12.0, 13.5, 14.25, 15.0, 16.5])
        com_nb    = random.choice([0, 5, 7, 10])
        com_pa    = random.choice([0, 0, 5, 10])
        gm        = random.choice([35.0, 40.0, 45.0, 50.0])
        regua     = random.choice(["mercado", "mercado", "brivia", "minima"])
        resp      = random.choice(_RESPONSAVEIS)

        perfis_disp = _PERFIS_POR_SERVICO.get(tipo_serv, [])
        n = random.randint(2, min(5, len(perfis_disp)))
        selecionados = random.sample(perfis_disp, n)

        equipe = []
        custo_eq = 0
        headcount = 0
        for perfil, niveis in selecionados:
            nivel = random.choice(niveis)
            sal   = BASE_SALARIAL.get(perfil, {}).get(nivel, {}).get(regua, 8000)
            qtd   = random.choice([1, 1, 1, 2, 2, 3])
            ded   = random.choice([50, 75, 100, 100])
            custo_eq  += _custo_item(sal, ded, meses, qtd)
            headcount += qtd
            equipe.append({"perfil": perfil, "nivel": nivel, "qtd": qtd,
                           "dedicacao": ded, "salario_base": sal, "regua": regua})

        terc_list = []
        custo_te  = 0
        if random.random() > 0.65:
            for _ in range(random.randint(1, 2)):
                v = random.choice([5000, 8000, 12000, 15000, 20000, 30000])
                terc_list.append({"desc": random.choice(_SERVICOS_TERC), "valor": v})
                custo_te += v

        extras = {
            "viagens":      random.choice([0, 0, 500, 1000, 2000]),
            "software":     random.choice([0, 300, 500, 1000, 1500]),
            "infraestrutura": random.choice([0, 500, 1000, 2000, 3000]),
            "outros":       random.choice([0, 0, 300, 500]),
        }
        custo_ex    = sum(extras.values()) * meses
        custo_total = custo_eq + custo_te + custo_ex
        com_total   = com_nb + com_pa
        preco, v_imp, v_com, v_gm = _preco_reverso(custo_total, gm, imp, com_total)
        fee   = preco / meses
        mkp   = ((preco / custo_total) - 1) * 100 if custo_total else 0

        age_m = (datetime.now() - created).days / 30
        if age_m < 2:
            status = random.choices(["Rascunho", "Em Análise", "Aprovada"], weights=[20, 50, 30])[0]
        elif age_m < 6:
            status = random.choices(["Em Análise", "Aprovada", "Rejeitada", "Em Execução"], weights=[10, 30, 25, 35])[0]
        else:
            status = random.choices(["Aprovada", "Rejeitada", "Em Execução", "Concluída", "Cancelada"], weights=[10, 25, 20, 35, 10])[0]

        created_s = created.strftime("%Y-%m-%d %H:%M:%S")
        with get_db() as conn:
            cur = conn.execute("""
                INSERT INTO propostas (
                    created_at, updated_at, status, cliente, segmento, projeto, descricao,
                    tipo_contrato, tipo_servico, meses, imposto_pct, comissao_nb, comissao_parc,
                    gm_alvo, regua_salarial, custo_equipe, custo_terceiros, custo_extras,
                    custo_total, preco_venda, fee_mensal, v_impostos, v_comissoes,
                    margem_bruta, markup_pct, headcount, responsavel, obs
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                created_s, created_s, status, cliente, segmento,
                projeto, f"Proposta gerada artificialmente — {projeto}",
                tipo_cont, tipo_serv, meses, imp, com_nb, com_pa,
                gm, regua, custo_eq, custo_te, custo_ex,
                custo_total, preco, fee, v_imp, v_com, v_gm,
                mkp, headcount, resp, "",
            ))
            pid = cur.lastrowid
            for e in equipe:
                conn.execute(
                    "INSERT INTO proposta_equipe (proposta_id,perfil,nivel,qtd,dedicacao,salario_base,regua) VALUES (?,?,?,?,?,?,?)",
                    (pid, e["perfil"], e["nivel"], e["qtd"], e["dedicacao"], e["salario_base"], e["regua"]),
                )
            for t in terc_list:
                conn.execute(
                    "INSERT INTO proposta_terceiros (proposta_id,descricao,valor) VALUES (?,?,?)",
                    (pid, t["desc"], t["valor"]),
                )

# ==================== CSS ====================

def inject_css():
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── RESET ── */
*, *::before, *::after {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    box-sizing: border-box;
}}

.stApp {{
    background: #0d0d0d !important;
}}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {{
    background: #080808 !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
    width: 220px !important;
}}
section[data-testid="stSidebar"] > div {{
    padding: 0 !important;
}}

/* Sidebar buttons — nav items */
section[data-testid="stSidebar"] div.stButton > button {{
    width: 100% !important;
    background: transparent !important;
    border: none !important;
    color: rgba(255,255,255,0.45) !important;
    text-align: left !important;
    padding: 10px 20px !important;
    border-radius: 0 !important;
    font-size: 0.85rem !important;
    font-weight: 400 !important;
    letter-spacing: 0 !important;
    text-transform: none !important;
    transition: all 0.2s !important;
    box-shadow: none !important;
}}
section[data-testid="stSidebar"] div.stButton > button:hover {{
    background: rgba(255,255,255,0.04) !important;
    color: rgba(255,255,255,0.85) !important;
    transform: none !important;
    box-shadow: none !important;
}}

/* ── MAIN CONTENT ── */
.block-container {{
    padding: 2rem 2.5rem !important;
    max-width: 100% !important;
}}

/* ── TYPOGRAPHY ── */
h1 {{ font-size: 1.75rem !important; font-weight: 700 !important; color: #f9fafb !important; letter-spacing: -0.5px !important; margin-bottom: 4px !important; }}
h2 {{ font-size: 1.25rem !important; font-weight: 600 !important; color: #f9fafb !important; }}
h3 {{ font-size: 1rem !important;   font-weight: 600 !important; color: #f9fafb !important; }}
p, span, label, div {{ color: #9ca3af; }}

/* ── SCROLLBAR ── */
* {{ scrollbar-width: thin; scrollbar-color: #2d2d2d transparent; }}
*::-webkit-scrollbar {{ width: 5px; height: 5px; }}
*::-webkit-scrollbar-track {{ background: transparent; }}
*::-webkit-scrollbar-thumb {{ background: #2d2d2d; border-radius: 3px; }}

/* ── CARDS ── */
.pro-card {{
    background: #111111;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
}}
.pro-card:hover {{ border-color: rgba(255,255,255,0.1); }}
.pro-card-header {{
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 20px; padding-bottom: 16px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}}
.pro-card-title {{
    font-size: 0.9rem; font-weight: 600;
    color: #e5e7eb; letter-spacing: -0.2px;
}}
.card-accent-left {{
    border-left: 3px solid {COR_PRIMARIA};
}}

/* ── KPI CARDS ── */
.kpi-wrap {{
    background: #111111;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 20px 22px;
    position: relative;
    overflow: hidden;
}}
.kpi-wrap::after {{
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--kpi-color, {COR_PRIMARIA}), transparent);
    opacity: 0.6;
}}
.kpi-label {{
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: rgba(255,255,255,0.35);
    margin-bottom: 10px;
}}
.kpi-value {{
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.7rem;
    font-weight: 600;
    color: #f9fafb;
    letter-spacing: -1px;
    line-height: 1;
}}
.kpi-delta {{
    font-size: 0.72rem;
    margin-top: 8px;
    color: rgba(255,255,255,0.35);
}}
.kpi-delta.up   {{ color: {COR_SUCESSO}; }}
.kpi-delta.down {{ color: {COR_ERRO}; }}

/* ── STATUS BADGE ── */
.badge {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.3px;
}}

/* ── FORM INPUTS ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea {{
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: #f9fafb !important;
    font-size: 0.875rem !important;
}}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {{
    border-color: {COR_PRIMARIA} !important;
    box-shadow: 0 0 0 2px rgba(197,143,61,0.12) !important;
    background: rgba(255,255,255,0.05) !important;
}}
.stSelectbox > div > div,
.stMultiSelect > div > div {{
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
}}
.stSlider > div > div > div > div {{
    background: {COR_PRIMARIA} !important;
}}
.stRadio > div > label {{
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 8px !important;
    padding: 10px 16px !important;
    transition: all 0.2s !important;
}}
.stRadio > div > label:hover {{
    border-color: rgba(255,255,255,0.14) !important;
}}
.stRadio > div > label[data-checked="true"] {{
    border-color: {COR_PRIMARIA} !important;
    background: rgba(197,143,61,0.08) !important;
}}

/* ── MAIN CONTENT BUTTONS ── */
.block-container div.stButton > button {{
    background: transparent;
    border: 1px solid rgba(255,255,255,0.1);
    color: #e5e7eb;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 0.82rem;
    font-weight: 500;
    letter-spacing: 0.3px;
    text-transform: none;
    transition: all 0.2s;
}}
.block-container div.stButton > button:hover {{
    border-color: {COR_PRIMARIA};
    color: {COR_PRIMARIA};
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(197,143,61,0.15);
}}
.block-container div.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, {COR_PRIMARIA}, #a8793a);
    border: none;
    color: #ffffff;
    font-weight: 600;
    box-shadow: 0 2px 10px rgba(197,143,61,0.25);
}}
.block-container div.stButton > button[kind="primary"]:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(197,143,61,0.4);
    color: #ffffff !important;
}}

/* ── DATAFRAME ── */
.stDataFrame {{ border-radius: 10px; overflow: hidden; }}
[data-testid="stDataFrameResizable"] {{ background: #111111 !important; }}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {{
    background: rgba(255,255,255,0.02) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    gap: 4px !important;
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 7px !important;
    color: rgba(255,255,255,0.45) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
}}
.stTabs [aria-selected="true"] {{
    background: rgba(197,143,61,0.15) !important;
    color: {COR_PRIMARIA} !important;
}}

/* ── EXPANDER ── */
.streamlit-expanderHeader {{
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 8px !important;
    color: #e5e7eb !important;
}}

/* ── ALERTS ── */
.pro-alert {{
    padding: 12px 16px;
    border-radius: 8px;
    font-size: 0.82rem;
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
}}
.pro-alert.info    {{ background: rgba(59,130,246,0.08);  border: 1px solid rgba(59,130,246,0.2);  color: #93c5fd; }}
.pro-alert.success {{ background: rgba(16,185,129,0.08); border: 1px solid rgba(16,185,129,0.2); color: #6ee7b7; }}
.pro-alert.warning {{ background: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.2); color: #fcd34d; }}
.pro-alert.danger  {{ background: rgba(239,68,68,0.08);  border: 1px solid rgba(239,68,68,0.2);  color: #fca5a5; }}

/* ── DIVIDER ── */
.pro-divider {{
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
    margin: 28px 0;
}}

/* ── TEAM ROW ── */
.team-row {{
    display: flex;
    align-items: center;
    padding: 14px 18px;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.04);
    border-radius: 10px;
    margin-bottom: 6px;
    transition: all 0.2s;
    gap: 14px;
}}
.team-row:hover {{
    background: rgba(255,255,255,0.04);
    border-color: rgba(255,255,255,0.08);
}}
.team-avatar {{
    width: 36px; height: 36px;
    border-radius: 8px;
    background: linear-gradient(135deg, rgba(197,143,61,0.25), rgba(197,143,61,0.1));
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 0.85rem;
    color: {COR_PRIMARIA};
    flex-shrink: 0;
}}
.team-info {{ flex: 1; }}
.team-name {{ font-weight: 600; color: #e5e7eb; font-size: 0.85rem; }}
.team-sub  {{ font-size: 0.72rem; color: rgba(255,255,255,0.35); margin-top: 2px; }}
.team-cost {{
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem;
    color: {COR_SUCESSO};
    font-weight: 500;
}}

/* ── HIDE STREAMLIT DEFAULTS ── */
#MainMenu {{ visibility: hidden; }}
footer    {{ visibility: hidden; }}
header    {{ visibility: hidden; }}
.stDeployButton {{ display: none; }}
div[data-testid="stToolbar"] {{ display: none; }}

/* ── STEP INDICATOR ── */
.step-bar {{
    display: flex; align-items: center;
    gap: 0; margin-bottom: 36px;
    padding: 0;
}}
.step-item {{
    display: flex; align-items: center; gap: 10px;
    flex: 1;
    padding: 12px 20px;
    border-radius: 8px;
    font-size: 0.78rem;
    font-weight: 500;
    letter-spacing: 0.3px;
    text-transform: uppercase;
    transition: all 0.3s;
}}
.step-item.active {{
    background: rgba(197,143,61,0.12);
    border: 1px solid rgba(197,143,61,0.4);
    color: {COR_PRIMARIA};
}}
.step-item.done {{
    background: rgba(16,185,129,0.06);
    border: 1px solid rgba(16,185,129,0.2);
    color: {COR_SUCESSO};
}}
.step-item.pending {{
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.05);
    color: rgba(255,255,255,0.2);
}}
.step-num {{
    width: 22px; height: 22px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.68rem; font-weight: 700;
    flex-shrink: 0;
}}
.step-item.active  .step-num {{ background: {COR_PRIMARIA}; color: #fff; }}
.step-item.done    .step-num {{ background: {COR_SUCESSO};  color: #fff; }}
.step-item.pending .step-num {{ background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.25); }}
.step-connector {{
    width: 24px; height: 2px;
    background: rgba(255,255,255,0.06);
    flex-shrink: 0;
}}
.step-connector.done {{ background: {COR_SUCESSO}; }}
</style>
""", unsafe_allow_html=True)

# ==================== HELPERS ====================

def fmt(v):
    if isinstance(v, Decimal): v = float(v)
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_k(v):
    if isinstance(v, Decimal): v = float(v)
    if v >= 1_000_000: return f"R$ {v/1_000_000:.1f}M"
    if v >= 1_000:     return f"R$ {v/1_000:.1f}K"
    return f"R$ {v:.0f}"

def calc_custo(salario, ded_pct, meses, qtd=1):
    s = Decimal(str(salario))
    d = Decimal(str(ded_pct)) / Decimal("100")
    m = Decimal(str(meses))
    q = Decimal(str(qtd))
    mensal_cheio   = s * FATOR_ENCARGOS + BENEFICIOS_MENSAIS
    mensal_dedicado = mensal_cheio * d
    total = mensal_dedicado * m * q
    return float(mensal_cheio), float(mensal_dedicado), float(total)

def calc_hora(salario):
    s = Decimal(str(salario))
    return float((s * FATOR_ENCARGOS + BENEFICIOS_MENSAIS) / HORAS_MES)

def calc_preco(custo, gm, imp, com):
    div = 1 - (gm + imp + com) / 100
    if div <= 0: return None, 0, 0, 0
    p = custo / div
    return p, p * imp / 100, p * com / 100, p * gm / 100

def badge_html(status):
    cor = STATUS_COLORS.get(status, "#6b7280")
    return f'<span class="badge" style="background:rgba(0,0,0,0);border:1px solid {cor};color:{cor};">{status}</span>'

def chart_layout(**kwargs):
    base = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#6b7280", size=11),
        margin=dict(t=30, b=20, l=10, r=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#9ca3af", size=10)),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.06)", tickfont=dict(color="#6b7280")),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.06)", tickfont=dict(color="#6b7280")),
    )
    base.update(kwargs)
    return base

def kpi_card(label, value, delta=None, color=COR_PRIMARIA, mono=True):
    delta_html = ""
    if delta is not None:
        cls = "up" if delta >= 0 else "down"
        icon = "↑" if delta >= 0 else "↓"
        delta_html = f'<div class="kpi-delta {cls}">{icon} {abs(delta):.1f}%</div>'
    font_class = "font-family:'JetBrains Mono',monospace;" if mono else ""
    return f"""
<div class="kpi-wrap" style="--kpi-color:{color};">
  <div class="kpi-label">{label}</div>
  <div class="kpi-value" style="{font_class}">{value}</div>
  {delta_html}
</div>"""

def step_bar(atual):
    steps = [("1","Estratégia"),("2","Equipe"),("3","Custos"),("4","Revisão")]
    html  = '<div class="step-bar">'
    for i,(num,label) in enumerate(steps):
        n = i + 1
        cls = "active" if n == atual else ("done" if n < atual else "pending")
        icon = "✓" if cls == "done" else num
        html += f'<div class="step-item {cls}"><div class="step-num">{icon}</div><span>{label}</span></div>'
        if i < len(steps)-1:
            conn_cls = "done" if n < atual else ""
            html += f'<div class="step-connector {conn_cls}"></div>'
    html += '</div>'
    return html

def section_header(icon, title, subtitle=""):
    sub = f'<p style="color:rgba(255,255,255,0.35);font-size:0.82rem;margin:4px 0 0 0;">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
<div style="margin-bottom:28px;">
  <div style="display:flex;align-items:center;gap:10px;">
    <span style="font-size:1.3rem;">{icon}</span>
    <div>
      <h1 style="margin:0;">{title}</h1>
      {sub}
    </div>
  </div>
</div>""", unsafe_allow_html=True)

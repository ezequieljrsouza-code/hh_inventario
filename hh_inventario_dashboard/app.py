import io
import re
from collections import OrderedDict
import pandas as pd
import streamlit as st

# Configuração da página
st.set_page_config(page_title="HH Inventário", page_icon="📦", layout="wide")

# Paleta de Cores Premium
ORANGE = "#f59e0b"
DARK_TEXT = "#0f172a"
METRIC_LABEL = "#475569"
BORDER = "#e2e8f0"
BG_APP = "#f1f5f9"
WHITE = "#ffffff"

STATUS_ORDER = ["Verificados", "Pendente", "Deslocado"]

def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        /* ---------- TRECHO DE OCULTAR ELEMENTOS ---------- */
        header {{visibility: hidden;}}
        [data-testid="stToolbar"] {{display: none;}}
        [data-testid="stDecoration"] {{display: none;}}
        
        /* ---------- LIMPEZA E BASE ---------- */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        .stDeployButton {{display:none;}}
        
        .stApp {{ background: {BG_APP}; }}
        .block-container {{ padding-top: 1.5rem; max-width: 95%; }}

        /* ---------- TÍTULO HH INVENTÁRIO ---------- */
        .main-header {{
            text-align: center;
            padding: 10px 0 30px 0;
        }}
        .main-header-inner {{
            display: inline-block;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 60%, #1e3a5f 100%);
            padding: 18px 60px 16px 60px;
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(15, 23, 42, 0.35), 0 2px 8px rgba(245,158,11,0.15);
            border-top: 4px solid {ORANGE};
            position: relative;
            overflow: hidden;
        }}
        .main-header-inner::before {{
            content: '';
            position: absolute;
            top: -30px; left: -30px;
            width: 120px; height: 120px;
            background: radial-gradient(circle, rgba(245,158,11,0.18) 0%, transparent 70%);
            pointer-events: none;
        }}
        .main-header-inner::after {{
            content: '';
            position: absolute;
            bottom: -30px; right: -30px;
            width: 120px; height: 120px;
            background: radial-gradient(circle, rgba(245,158,11,0.12) 0%, transparent 70%);
            pointer-events: none;
        }}
        .main-header h1 {{
            font-size: 3.2rem;
            font-weight: 900;
            color: {WHITE};
            margin: 0;
            letter-spacing: -1px;
            text-shadow: 0 2px 12px rgba(0,0,0,0.3);
        }}
        .main-header h1 span.accent {{
            color: {ORANGE};
        }}
        .main-header .subtitle {{
            color: rgba(255,255,255,0.55);
            font-size: 0.85rem;
            font-weight: 600;
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-top: 4px;
        }}

        /* ---------- CONTAINER DE CARDS ---------- */
        .metric-row {{
            display: flex;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 32px;
        }}

        .modern-card {{
            background: {WHITE};
            flex: 1;
            padding: 22px 16px;
            border-radius: 16px;
            text-align: center;
            box-shadow: 0 4px 16px rgba(0,0,0,0.07);
            border: 1px solid {BORDER};
            position: relative;
            overflow: hidden;
        }}

        .card-accent {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 5px;
            background: {ORANGE};
        }}

        .m-label {{
            color: {METRIC_LABEL};
            font-size: 0.82rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}

        .m-value {{
            color: {DARK_TEXT};
            font-size: 2.8rem;
            font-weight: 900;
            line-height: 1;
        }}

        /* ---------- SEÇÕES E TABELAS ---------- */
        .section-header {{
            background: {ORANGE};
            color: white;
            padding: 11px 20px;
            border-radius: 12px 12px 0 0;
            font-weight: 800;
            font-size: 1.25rem;
            margin-top: 18px;
            box-shadow: 0 2px 6px rgba(245,158,11,0.2);
        }}

        .table-container {{
            background: {WHITE};
            border-radius: 0 0 12px 12px;
            padding: 5px;
            margin-bottom: 24px;
            border: 1px solid {BORDER};
            border-top: none;
            overflow: hidden;
        }}

        table.hh-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 1.3rem;
            font-weight: 700;
        }}

        table.hh-table th {{
            background: #f8fafc;
            color: {DARK_TEXT};
            border-bottom: 2px solid {BG_APP};
            padding: 14px 12px;
            font-weight: 900;
            font-size: 1.15rem;
            letter-spacing: 0.3px;
        }}

        table.hh-table td {{
            padding: 14px 12px;
            text-align: center;
            border-bottom: 1px solid {BG_APP};
            color: {DARK_TEXT};
            font-size: 1.3rem;
            font-weight: 700;
        }}

        table.hh-table td:first-child {{
            text-align: left;
            font-weight: 900;
            background: #fdfdfd;
            border-right: 2px solid {BG_APP};
        }}

        .total-cell {{
            background: #fffbeb !important;
            font-weight: 900 !important;
            color: {ORANGE} !important;
            border-left: 2px solid #fde68a !important;
        }}

        /* ---------- PRINT OPTIMIZATIONS ---------- */
        @media print {{
            .stApp, body {{ background: #ffffff !important; }}
            .block-container {{ padding-top: 0.5rem !important; max-width: 100% !important; }}
            .modern-card {{
                box-shadow: none !important;
                border: 2px solid {BORDER} !important;
                break-inside: avoid;
            }}
            .main-header-inner {{
                box-shadow: none !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            .section-header {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
                box-shadow: none !important;
            }}
            .table-container {{
                box-shadow: none !important;
                break-inside: avoid;
            }}
            table.hh-table th,
            table.hh-table td {{
                padding: 8px !important;
                font-size: 0.85rem !important;
            }}
            .m-value {{ font-size: 2rem !important; }}
            .metric-row {{ gap: 8px !important; margin-bottom: 16px !important; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).replace("\ufeff", "").strip().strip('"') for c in df.columns]
    rename_map = {}
    for col in df.columns:
        low = col.lower()
        if "pacote" in low: rename_map[col] = "Pacote"
        elif "data de escaneamento" in low: rename_map[col] = "Data de Escaneamento"
        elif "situa" in low: rename_map[col] = "Situação"
        elif "área" in low or "area" in low: rename_map[col] = "Área"
        elif "operador" in low: rename_map[col] = "Operador"
    df = df.rename(columns=rename_map)
    for col in ["Área", "Operador", "Pacote"]:
        if col not in df.columns: df[col] = pd.NA
    return df

def parse_hour(value) -> float:
    if pd.isna(value): return pd.NA
    text = str(value).strip().replace(".", ":")
    match = re.search(r"(\d{1,2}:\d{2}\s*[ap]m)", text, flags=re.I)
    if match: text = match.group(1)
    for fmt in ("%I:%M%p", "%I:%M %p", "%H:%M"):
        parsed = pd.to_datetime(text, format=fmt, errors="coerce")
        if not pd.isna(parsed): return int(parsed.hour)
    flexible = pd.to_datetime(text, errors="coerce")
    return int(flexible.hour) if not pd.isna(flexible) else pd.NA

def render_table(df: pd.DataFrame) -> None:
    if df.empty: return
    headers = list(df.columns)
    html = ["<div class='table-container'><table class='hh-table'><thead><tr>"]
    html.extend([f"<th>{h}</th>" for h in headers])
    html.append("</tr></thead><tbody>")
    for _, row in df.fillna("-").iterrows():
        html.append("<tr>")
        for idx, value in enumerate(row.tolist()):
            cls = "total-cell" if idx == len(headers) - 1 else ""
            html.append(f"<td class='{cls}'>{value}</td>")
        html.append("</tr>")
    html.append("</tbody></table></div>")
    st.markdown("".join(html), unsafe_allow_html=True)

def main():
    inject_css()
    
    # Upload no topo
    uploaded = st.file_uploader("📂 Base de Dados", type=["xlsx", "csv"])
    
    # Título do Painel — com fundo escuro e destaque laranja
    st.markdown('''
        <div class="main-header">
            <div class="main-header-inner">
                <h1><span class="accent">HH</span> Inventário</h1>
                <div class="subtitle">Analista: Ezequiel Miranda</div>
            </div>
        </div>
    ''', unsafe_allow_html=True)
    
    if not uploaded:
        st.info("Por favor, faça o upload da base de dados acima para iniciar.")
        st.stop()

    # Início da Área de Captura
    st.markdown('<div id="capture-area">', unsafe_allow_html=True)

    # Processamento
    df = pd.read_excel(uploaded) if uploaded.name.endswith('.xlsx') else pd.read_csv(uploaded)
    df = normalize_columns(df)
    df["Hora"] = df["Data de Escaneamento"].apply(parse_hour).astype("Int64")
    
    valid_hours = sorted([int(h) for h in df["Hora"].dropna().unique().tolist()])
    if not valid_hours: st.stop()
    base_h = min(valid_hours)
    hours = list(range(base_h, base_h + 8))
    hour_labels = [f"{idx+1}ª Hora ({h:02d}h)" for idx, h in enumerate(hours)]

    # Métricas
    v_total = len(df)
    v_verif = int((df['Situação'] == 'Verificados').sum())
    v_pend = int((df['Situação'] == 'Pendente').sum())
    v_desl = int((df['Situação'] == 'Deslocado').sum())
    
    # Cálculo da Acuracidade
    v_acu = (v_verif / v_total * 100) if v_total > 0 else 0.0

    st.markdown(f"""
    <div class="metric-row">
        <div class="modern-card"><div class="card-accent"></div><div class="m-label">Volume Total</div><div class="m-value">{v_total:,}</div></div>
        <div class="modern-card"><div class="card-accent" style="background:#22c55e"></div><div class="m-label">Verificados</div><div class="m-value">{v_verif:,}</div></div>
        <div class="modern-card"><div class="card-accent" style="background:#ef4444"></div><div class="m-label">Pendentes</div><div class="m-value">{v_pend:,}</div></div>
        <div class="modern-card"><div class="card-accent" style="background:#3b82f6"></div><div class="m-label">Deslocados</div><div class="m-value">{v_desl:,}</div></div>
        <div class="modern-card"><div class="card-accent" style="background:#8b5cf6"></div><div class="m-label">Acuracidade</div><div class="m-value">{v_acu:.1f}%</div></div>
    </div>
    """.replace(",", "."), unsafe_allow_html=True)

    # Zonas com borda esquerda
    if "Área" in df.columns:
        st.markdown("<div class='section-header'>Pendentes por Zona</div>", unsafe_allow_html=True)
        counts = df[df["Situação"]=="Pendente"]["Área"].value_counts().to_dict()
        zonas = ["Returns","Sorting","Problem Solving","Missort","Fraude","Damaged","Buffered","Dispatch","Containerized","Bulky returns"]
        
        cols = st.columns(5)
        for i, z in enumerate(zonas):
            val = counts.get(z, 0)
            with cols[i % 5]:
                st.markdown(f"""
                <div style="background:white; padding:16px; border-radius:12px; text-align:center; margin-bottom:12px; border: 1px solid {BORDER}; border-left: 5px solid {ORANGE};">
                    <div style="font-size:0.75rem; color:#64748b; font-weight:800; text-transform:uppercase; letter-spacing:0.5px;">{z}</div>
                    <div style="font-size:1.7rem; font-weight:900; color:{DARK_TEXT}">{val}</div>
                </div>
                """, unsafe_allow_html=True)

    # Tabelas
    st.markdown("<div class='section-header'>Resumo HH Por Status</div>", unsafe_allow_html=True)
    rows = []
    for s in STATUS_ORDER:
        row = OrderedDict({"QTD / Status": s})
        for h, lab in zip(hours, hour_labels): row[lab] = int(((df["Situação"]==s) & (df["Hora"]==h)).sum())
        row["TOTAL"] = int((df["Situação"]==s).sum())
        rows.append(row)
    render_table(pd.DataFrame(rows))

    for s, title in [("Verificados", "Verificados / Conferentes"), ("Deslocado", "Deslocados / Conferentes")]:
        subset = df[(df["Situação"] == s) & df["Operador"].notna()]
        ops = sorted(subset["Operador"].unique())
        op_rows = []
        for o in ops:
            r = OrderedDict({title: o})
            for h, lab in zip(hours, hour_labels): r[lab] = int(((subset["Operador"]==o) & (subset["Hora"]==h)).sum())
            r["TOTAL"] = int((subset["Operador"]==o).sum())
            op_rows.append(r)
        st.markdown(f"<div class='section-header'>{title}: {len(ops)}</div>", unsafe_allow_html=True)
        render_table(pd.DataFrame(op_rows))

    # Fim da Área de Captura
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()

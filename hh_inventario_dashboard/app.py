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
        /* ---------- LIMPEZA E BASE ---------- */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        .stDeployButton {{display:none;}}
        [data-testid="stToolbar"] {{display:none;}}
        [data-testid="stDecoration"] {{display:none;}}
        
        .stApp {{ background: {BG_APP}; }}
        .block-container {{ padding-top: 1.5rem; max-width: 95%; }}

        /* ---------- TÍTULO HH INVENTÁRIO ---------- */
        .main-header {{
            text-align: center;
            padding: 20px 0 40px 0;
        }}
        .main-header h1 {{
            font-size: 3.5rem;
            font-weight: 900;
            color: {DARK_TEXT};
            margin: 0;
            letter-spacing: -2px;
            background: linear-gradient(135deg, {DARK_TEXT} 0%, #334155 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        /* ---------- CONTAINER DE CARDS ---------- */
        .metric-row {{
            display: flex;
            justify-content: space-between;
            gap: 20px;
            margin-bottom: 40px;
        }}

        .modern-card {{
            background: {WHITE};
            flex: 1;
            padding: 25px 20px;
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.7);
            position: relative;
            overflow: hidden;
            transition: transform 0.3s ease;
        }}
        
        .modern-card:hover {{
            transform: translateY(-5px);
        }}

        /* Detalhe colorido no topo dos cards */
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
            font-size: 0.95rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 12px;
        }}

        .m-value {{
            color: {DARK_TEXT};
            font-size: 3.2rem;
            font-weight: 900;
            line-height: 1;
        }}

        /* ---------- SEÇÕES E TABELAS ---------- */
        .section-header {{
            background: {ORANGE};
            color: white;
            padding: 12px 20px;
            border-radius: 15px 15px 0 0;
            font-weight: 800;
            font-size: 1.4rem;
            margin-top: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}

        .table-container {{
            background: {WHITE};
            border-radius: 0 0 15px 15px;
            padding: 5px;
            margin-bottom: 30px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
            overflow: hidden;
        }}

        table.hh-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 1.25rem;
        }}

        table.hh-table th {{
            background: #fff;
            color: {DARK_TEXT};
            border-bottom: 2px solid {BG_APP};
            padding: 15px;
            font-weight: 800;
        }}

        table.hh-table td {{
            padding: 15px;
            text-align: center;
            border-bottom: 1px solid {BG_APP};
            color: {DARK_TEXT};
        }}

        table.hh-table td:first-child {{
            text-align: left;
            font-weight: 800;
            background: #fdfdfd;
            border-right: 2px solid {BG_APP};
        }}

        .total-cell {{
            background: #f8fafc !important;
            font-weight: 900 !important;
            color: {ORANGE} !important;
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
        elif "coment" in low: rename_map[col] = "Comentário"
    df = df.rename(columns=rename_map)
    for col in ["Área", "Operador", "Comentário", "Pacote"]:
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

def format_hour(hour_value: int) -> str:
    return f"{int(hour_value):02d}h"

def prepare_base_dataframe(file_bytes: bytes, uploaded_name: str) -> pd.DataFrame:
    if uploaded_name.lower().endswith(".csv"):
        df = pd.read_csv(io.BytesIO(file_bytes))
    else:
        excel = pd.ExcelFile(io.BytesIO(file_bytes))
        preferred = next((n for n in excel.sheet_names if "BASE" in n.upper()), excel.sheet_names[0])
        df = pd.read_excel(excel, sheet_name=preferred)
    df = normalize_columns(df)
    df["Situação"] = df["Situação"].astype(str).str.strip()
    df["Operador"] = df["Operador"].astype("string").str.strip()
    df["Hora"] = df["Data de Escaneamento"].apply(parse_hour).astype("Int64")
    return df

def render_table(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("Sem dados para exibir.")
        return
    headers = list(df.columns)
    html = ["<div class='table-wrap'><table class='hh-table'><thead><tr>"]
    html.extend([f"<th>{h}</th>" for h in headers])
    html.append("</tr></thead><tbody>")
    for _, row in df.fillna("").iterrows():
        html.append("<tr>")
        for idx, value in enumerate(row.tolist()):
            cls = "total-col" if idx == len(headers) - 1 else ""
            html.append(f"<td class='{cls}'>{value}</td>")
        html.append("</tr>")
    html.append("</tbody></table></div>")
    st.markdown("".join(html), unsafe_allow_html=True)

def main():
    inject_css()
    
    # Upload fora do design principal para não sujar o print
    uploaded = st.file_uploader("Upload da base", type=["xlsx", "csv"])
    if not uploaded:
        st.markdown('<div class="main-title">HH Inventário</div>', unsafe_allow_html=True)
        st.info("Aguardando arquivo para gerar o painel...")
        st.stop()

    df = prepare_base_dataframe(uploaded.getvalue(), uploaded.name)
    valid_hours = sorted([int(h) for h in df["Hora"].dropna().unique().tolist()])
    if not valid_hours: st.stop()
    
    base_h = min(valid_hours)
    hours = list(range(base_h, base_h + 8))
    hour_labels = [f"{idx+1}ª Hora ({format_hour(h)})" for idx, h in enumerate(hours)]

    # --- INÍCIO DO DESIGN VISUAL ---
    st.markdown('<div class="main-title">HH Inventário</div>', unsafe_allow_html=True)

    # Cards de Métricas Estilizados
    t_vol = len(df)
    t_ver = int((df['Situação'] == 'Verificados').sum())
    t_pen = int((df['Situação'] == 'Pendente').sum())
    t_des = int((df['Situação'] == 'Deslocado').sum())

    st.markdown(f"""
    <div class="metric-container">
        <div class="premium-card">
            <div class="metric-label">Volume Total</div>
            <div class="metric-value">{t_vol:,}</div>
        </div>
        <div class="premium-card">
            <div class="metric-label">Verificados</div>
            <div class="metric-value">{t_ver:,}</div>
        </div>
        <div class="premium-card">
            <div class="metric-label">Pendentes</div>
            <div class="metric-value">{t_pen:,}</div>
        </div>
        <div class="premium-card">
            <div class="premium-card-inner">
                <div class="metric-label">Deslocados</div>
                <div class="metric-value">{t_des:,}</div>
            </div>
        </div>
    </div>
    """.replace(",", "."), unsafe_allow_html=True)

    # Pendentes por Zona
    if "Área" in df.columns:
        st.markdown("<div class='section-title'>Pendentes Zona</div>", unsafe_allow_html=True)
        zonas = ["Returns","Sorting","Problem Solving","Missort","Fraude","Damaged","Buffered","Dispatch","Containerized","Bulky returns"]
        counts = df[df["Situação"]=="Pendente"]["Área"].value_counts().to_dict()
        cols = st.columns(5)
        for i, z in enumerate(zonas):
            val = counts.get(z, 0)
            with cols[i % 5]:
                st.markdown(f'<div style="background:white; border-left:6px solid {ORANGE}; padding:15px; border-radius:12px; text-align:center; box-shadow:0 2px 6px rgba(0,0,0,0.05); margin-bottom:10px;"><div style="font-size:0.85rem; color:{METRIC_LABEL}; font-weight:600;">{z}</div><div style="font-size:1.8rem; font-weight:800; color:{DARK_TEXT}">{val}</div></div>', unsafe_allow_html=True)

    # Tabelas HH
    st.markdown("<div class='section-title'>Resumo HH</div>", unsafe_allow_html=True)
    rows = []
    for s in STATUS_ORDER:
        row = OrderedDict({"QTD / Status": s})
        for h, lab in zip(hours, hour_labels): row[lab] = int(((df["Situação"]==s) & (df["Hora"]==h)).sum())
        row["TOTAL"] = int((df["Situação"]==s).sum())
        rows.append(row)
    render_table(pd.DataFrame(rows))

    # Operadores
    for s, title in [("Verificados", "Verificados / Conferentes"), ("Deslocado", "Deslocados / Conferentes")]:
        subset = df[(df["Situação"] == s) & df["Operador"].notna()]
        ops = sorted(subset["Operador"].unique())
        op_rows = []
        for o in ops:
            r = OrderedDict({title: o})
            for h, lab in zip(hours, hour_labels): r[lab] = int(((subset["Operador"]==o) & (subset["Hora"]==h)).sum())
            r["TOTAL"] = int((subset["Operador"]==o).sum())
            op_rows.append(r)
        st.markdown(f"<div class='section-title'>{title}: {len(ops)}</div>", unsafe_allow_html=True)
        render_table(pd.DataFrame(op_rows))

    st.download_button("Exportar CSV", df.to_csv(index=False).encode('utf-8'), "inventario.csv", "text/csv")

if __name__ == "__main__":
    main()

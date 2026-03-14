import io
import re
from collections import OrderedDict
import pandas as pd
import streamlit as st

# Configuração da página para ocupar toda a largura
st.set_page_config(page_title="HH Inventário", page_icon="📦", layout="wide")

# Paleta de Cores e Estilo
ORANGE = "#f59e0b"
DARK_TEXT = "#0f172a"
METRIC_LABEL = "#475569"
BG_APP = "#f1f5f9"
WHITE = "#ffffff"

STATUS_ORDER = ["Verificados", "Pendente", "Deslocado"]

def inject_css() -> None:
    """Injeta CSS para remover menus e estilizar cards e tabelas para print limpo."""
    st.markdown(
        f"""
        <style>
        /* ---------- REMOÇÃO DE ELEMENTOS DO STREAMLIT ---------- */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        .stDeployButton {{display:none;}}
        [data-testid="stToolbar"] {{display:none;}}
        [data-testid="stDecoration"] {{display:none;}}
        
        /* Oculta o botão 'Manage app' que aparece no Streamlit Cloud */
        button[title="Manage app"] {{ display: none !important; }}

        /* ---------- LAYOUT E FUNDO ---------- */
        .stApp {{ background: {BG_APP}; }}
        .block-container {{ padding-top: 1rem; padding-bottom: 1rem; max-width: 98%; }}

        /* ---------- DESIGN DO TÍTULO ---------- */
        .main-header {{
            text-align: center;
            padding: 10px 0 30px 0;
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

        /* ---------- CARDS DE MÉTRICAS (TOP) ---------- */
        .metric-row {{
            display: flex;
            justify-content: space-between;
            gap: 15px;
            margin-bottom: 30px;
        }}
        .modern-card {{
            background: {WHITE};
            flex: 1;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            border: 1px solid rgba(0,0,0,0.05);
            position: relative;
        }}
        .card-accent {{
            position: absolute; top: 0; left: 0; width: 100%; height: 4px; background: {ORANGE};
        }}
        .m-label {{ color: {METRIC_LABEL}; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }}
        .m-value {{ color: {DARK_TEXT}; font-size: 2.8rem; font-weight: 900; line-height: 1; }}

        /* ---------- ESTILO DAS SEÇÕES E TABELAS ---------- */
        .section-header {{
            background: {ORANGE};
            color: white;
            padding: 10px 15px;
            border-radius: 10px 10px 0 0;
            font-weight: 800;
            font-size: 1.2rem;
            margin-top: 20px;
        }}
        .table-container {{
            background: {WHITE};
            border-radius: 0 0 10px 10px;
            margin-bottom: 25px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.03);
            overflow: hidden;
        }}
        table.hh-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 1.1rem;
        }}
        table.hh-table th {{
            background: rgba(245, 158, 11, 0.1);
            color: {DARK_TEXT};
            padding: 12px;
            border: 1px solid #eee;
            font-weight: 800;
        }}
        table.hh-table td {{
            padding: 10px;
            text-align: center;
            border: 1px solid #eee;
            color: {DARK_TEXT};
        }}
        table.hh-table td:first-child {{
            text-align: left;
            font-weight: 800;
            background: #fafafa;
        }}
        .total-cell {{
            background: #f8fafc !important;
            font-weight: 900 !important;
            color: {ORANGE} !important;
        }}

        /* Esconder controles de upload no momento do print se desejar */
        @media print {{
            .stFileUploader {{ display: none; }}
            .stDownloadButton {{ display: none; }}
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

def parse_hour(value) -> int:
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
    
    # Área de Upload (discreta)
    with st.expander("📂 Carregar Base de Dados", expanded=True):
        uploaded = st.file_uploader("", type=["xlsx", "csv"])
    
    if not uploaded:
        st.markdown('<div class="main-header"><h1>HH Inventário</h1></div>', unsafe_allow_html=True)
        st.warning("Aguardando arquivo para gerar o painel...")
        st.stop()

    # Processamento dos Dados
    df = pd.read_excel(uploaded) if uploaded.name.endswith('.xlsx') else pd.read_csv(uploaded)
    df = normalize_columns(df)
    df["Hora"] = df["Data de Escaneamento"].apply(parse_hour).astype("Int64")
    
    valid_hours = sorted([int(h) for h in df["Hora"].dropna().unique().tolist()])
    if not valid_hours: 
        st.error("Erro ao processar as horas. Verifique a coluna 'Data de Escaneamento'.")
        st.stop()
        
    base_h = min(valid_hours)
    hours = list(range(base_h, base_h + 8))
    hour_labels = [f"{idx+1}ª Hora ({h:02d}h)" for idx, h in enumerate(hours)]

    # --- RENDERIZAÇÃO DO PAINEL ---
    st.markdown('<div class="main-header"><h1>HH Inventário</h1></div>', unsafe_allow_html=True)

    # Cards Principais
    st.markdown(f"""
    <div class="metric-row">
        <div class="modern-card"><div class="card-accent"></div><div class="m-label">Volume Total</div><div class="m-value">{len(df):,}</div></div>
        <div class="modern-card"><div class="card-accent" style="background:#22c55e"></div><div class="m-label">Verificados</div><div class="m-value">{int((df['Situação'] == 'Verificados').sum()):,}</div></div>
        <div class="modern-card"><div class="card-accent" style="background:#ef4444"></div><div class="m-label">Pendentes</div><div class="m-value">{int((df['Situação'] == 'Pendente').sum()):,}</div></div>
        <div class="modern-card"><div class="card-accent" style="background:#3b82f6"></div><div class="m-label">Deslocados</div><div class="m-value">{int((df['Situação'] == 'Deslocado').sum()):,}</div></div>
    </div>
    """.replace(",", "."), unsafe_allow_html=True)

    # Pendentes por Zona (Cards Menores)
    if "Área" in df.columns:
        st.markdown("<div class='section-header'>Pendentes Zona</div>", unsafe_allow_html=True)
        counts = df[df["Situação"]=="Pendente"]["Área"].value_counts().to_dict()
        zonas = ["Returns","Sorting","Problem Solving","Missort","Fraude","Damaged","Buffered","Dispatch","Containerized","Bulky returns"]
        cols = st.columns(5)
        for i, z in enumerate(zonas):
            val = counts.get(z, 0)
            with cols[i % 5]:
                st.markdown(f'<div style="background:white; padding:15px; border-radius:12px; text-align:center; box-shadow:0 2px 5px rgba(0,0,0,0.05); margin-bottom:10px; border:1px solid #eee;"><div style="font-size:0.75rem; color:#64748b; font-weight:800;">{z}</div><div style="font-size:1.6rem; font-weight:900; color:{DARK_TEXT}">{val}</div></div>', unsafe_allow_html=True)

    # Resumo Operacional
    st.markdown("<div class='section-header'>Resumo HH</div>", unsafe_allow_html=True)
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
        st.markdown(f"<div class='section-header'>{title}: {len(ops)}</div>", unsafe_allow_html=True)
        render_table(pd.DataFrame(op_rows))

if __name__ == "__main__":
    main()

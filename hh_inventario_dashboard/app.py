import io
import re
from collections import OrderedDict

import pandas as pd
import streamlit as st

# Configuração da página - FORÇANDO A BARRA LATERAL ABERTA
st.set_page_config(
    page_title="HH Inventário - Dark", 
    page_icon="📦", 
    layout="wide",
    initial_sidebar_state="expanded"  # Isso força o menu a iniciar aberto
)

# Paleta Dark Premium
ORANGE = "#f59e0b"
BG_BLACK = "#000000"
CARD_BG = "#1e1e1e"
TEXT_WHITE = "#ffffff"
TEXT_GRAY = "#a1a1aa"
BORDER_DARK = "#334155"

STATUS_ORDER = ["Verificados", "Pendente", "Deslocado"]

def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        /* ---------- TEMA DARK TOTAL ---------- */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        .stDeployButton {{display:none;}}
        [data-testid="stToolbar"] {{display:none;}}
        [data-testid="stDecoration"] {{display:none;}}
        
        .stApp {{ background: {BG_BLACK}; }}
        .block-container {{ padding-top: 1.5rem; max-width: 95%; }}

        /* Título com Gradiente */
        .main-header {{ text-align: center; padding: 20px 0 40px 0; }}
        .main-header h1 {{
            font-size: 3.5rem;
            font-weight: 900;
            color: {TEXT_WHITE};
            margin: 0;
            background: linear-gradient(135deg, {TEXT_WHITE} 0%, {ORANGE} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        /* ---------- CARDS PRINCIPAIS ---------- */
        .metric-row {{ display: flex; justify-content: space-between; gap: 20px; margin-bottom: 40px; }}
        .modern-card {{
            background: {CARD_BG};
            flex: 1;
            padding: 25px 20px;
            border-radius: 20px;
            text-align: center;
            border: 1px solid {BORDER_DARK};
            position: relative;
            overflow: hidden;
        }}
        .card-accent {{ position: absolute; top: 0; left: 0; width: 100%; height: 5px; background: {ORANGE}; }}
        .m-label {{ color: {TEXT_GRAY}; font-size: 0.95rem; font-weight: 700; text-transform: uppercase; margin-bottom: 12px; }}
        .m-value {{ color: {TEXT_WHITE}; font-size: 3.2rem; font-weight: 900; line-height: 1; }}

        /* ---------- CARDS DE ZONA (MODO DARK + BORDA LARANJA) ---------- */
        .zone-card {{
            background: {CARD_BG};
            padding: 22px 15px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 15px;
            border: 1px solid {BORDER_DARK};
            border-left: 8px solid {ORANGE} !important;
        }}
        .zone-label {{ font-size: 0.85rem; color: {TEXT_GRAY}; font-weight: 800; text-transform: uppercase; margin-bottom: 8px; }}
        .zone-value {{ font-size: 2rem; font-weight: 900; color: {TEXT_WHITE}; }}

        /* ---------- SEÇÕES E TABELAS DARK ---------- */
        .section-header {{
            background: {ORANGE};
            color: white;
            padding: 12px 20px;
            border-radius: 15px 15px 0 0;
            font-weight: 800;
            font-size: 1.4rem;
            margin-top: 20px;
        }}
        .table-container {{
            background: {CARD_BG};
            border-radius: 0 0 15px 15px;
            padding: 5px;
            margin-bottom: 30px;
            border: 1px solid {BORDER_DARK};
            overflow: hidden;
        }}
        table.hh-table {{ width: 100%; border-collapse: collapse; font-size: 1.25rem; color: {TEXT_WHITE}; }}
        table.hh-table th {{ background: #262626; color: {ORANGE}; padding: 15px; font-weight: 800; border-bottom: 1px solid {BORDER_DARK}; }}
        table.hh-table td {{ padding: 15px; text-align: center; border-bottom: 1px solid {BORDER_DARK}; }}
        table.hh-table td:first-child {{ text-align: left; font-weight: 800; background: #1a1a1a; color: {TEXT_WHITE}; }}
        
        .total-cell {{ background: #262626 !important; font-weight: 900 !important; color: {ORANGE} !important; }}

        /* Sidebar Dark */
        [data-testid="stSidebar"] {{ background-color: #0a0a0a; border-right: 1px solid {BORDER_DARK}; min-width: 300px !important; }}
        
        /* Botão de Instrução Central */
        .instruction-box {{
            background: #1e1e1e;
            padding: 40px;
            border-radius: 20px;
            border: 2px dashed {ORANGE};
            text-align: center;
            margin: 50px auto;
            max-width: 600px;
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
    
    # BARRA LATERAL (UPLOAD)
    with st.sidebar:
        st.markdown(f"<h1 style='color:{ORANGE};'>📁 CARREGAR</h1>", unsafe_allow_html=True)
        uploaded = st.file_uploader("Arraste seu XLSX ou CSV aqui", type=["xlsx", "csv"])
        st.markdown("---")
        st.markdown(f"**Usuário:** {st.session_state.get('user', 'Ezequiel Miranda')}")

    if not uploaded:
        st.markdown('<div class="main-header"><h1>HH Inventário</h1></div>', unsafe_allow_html=True)
        
        # AVISO CASO A SIDEBAR NÃO APAREÇA
        st.markdown(f"""
        <div class="instruction-box">
            <h2 style="color:{ORANGE};">⚠️ ONDE ESTÁ O UPLOAD?</h2>
            <p style="color:white; font-size:1.2rem;">
                Clique na <b>setinha ( > )</b> no canto superior esquerdo da tela para abrir o painel de upload lateral.
            </p>
            <div style="font-size: 4rem;">⬅️</div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # --- PROCESSAMENTO E RESTO DO CÓDIGO (IGUAL AO ANTERIOR) ---
    df = pd.read_excel(uploaded) if uploaded.name.endswith('.xlsx') else pd.read_csv(uploaded)
    df = normalize_columns(df)
    df["Hora"] = df["Data de Escaneamento"].apply(parse_hour).astype("Int64")
    
    valid_hours = sorted([int(h) for h in df["Hora"].dropna().unique().tolist()])
    if not valid_hours: st.stop()
    base_h = min(valid_hours)
    hours = list(range(base_h, base_h + 8))
    hour_labels = [f"{idx+1}ª Hora ({h:02d}h)" for idx, h in enumerate(hours)]

    st.markdown('<div class="main-header"><h1>HH Inventário</h1></div>', unsafe_allow_html=True)

    # Métricas Premium Dark
    st.markdown(f"""
    <div class="metric-row">
        <div class="modern-card"><div class="card-accent"></div><div class="m-label">Volume Total</div><div class="m-value">{len(df):,}</div></div>
        <div class="modern-card"><div class="card-accent" style="background:#22c55e"></div><div class="m-label">Verificados</div><div class="m-value">{int((df['Situação'] == 'Verificados').sum()):,}</div></div>
        <div class="modern-card"><div class="card-accent" style="background:#ef4444"></div><div class="m-label">Pendentes</div><div class="m-value">{int((df['Situação'] == 'Pendente').sum()):,}</div></div>
        <div class="modern-card"><div class="card-accent" style="background:#3b82f6"></div><div class="m-label">Deslocados</div><div class="m-value">{int((df['Situação'] == 'Deslocado').sum()):,}</div></div>
    </div>
    """.replace(",", "."), unsafe_allow_html=True)

    # Zonas com Borda Laranja de 8px
    if "Área" in df.columns:
        st.markdown("<div class='section-header'>Pendentes por Zona</div>", unsafe_allow_html=True)
        counts = df[df["Situação"]=="Pendente"]["Área"].value_counts().to_dict()
        zonas = ["Returns","Sorting","Problem Solving","Missort","Fraude","Damaged","Buffered","Dispatch","Containerized","Bulky returns"]
        
        cols = st.columns(5)
        for i, z in enumerate(zonas):
            val = counts.get(z, 0)
            with cols[i % 5]:
                st.markdown(f"""<div class="zone-card"><div class="zone-label">{z}</div><div class="zone-value">{val}</div></div>""", unsafe_allow_html=True)

    # Tabela Resumo
    st.markdown("<div class='section-header'>Resumo Operacional HH</div>", unsafe_allow_html=True)
    rows = []
    for s in STATUS_ORDER:
        row = OrderedDict({"QTD / Status": s})
        for h, lab in zip(hours, hour_labels): row[lab] = int(((df["Situação"]==s) & (df["Hora"]==h)).sum())
        row["TOTAL"] = int((df["Situação"]==s).sum())
        rows.append(row)
    render_table(pd.DataFrame(rows))

    # Conferentes
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

import io
import re
from collections import OrderedDict

import pandas as pd
import streamlit as st

st.set_page_config(page_title="HH Inventário", page_icon="📦", layout="wide")

ORANGE = "#f59e0b"
DARK = "#1f2937"
BORDER = "#d1d5db"
BG = "#f8fafc"
WHITE = "#ffffff"

STATUS_ORDER = ["Verificados", "Pendente", "Deslocado"]


# ---------- CARDS DE ZONA ----------
def render_zona_cards(df):

    zonas = [
        "Returns","Sorting","Problem Solving","Missort",
        "Fraude","Damaged","Buffered","Dispatch",
        "Containerized","Bulky returns"
    ]

    counts = df["Área"].value_counts().to_dict()

    st.markdown("<div class='section-title'>Pendentes Zona</div>", unsafe_allow_html=True)

    cols = st.columns(5)

    for i,z in enumerate(zonas):

        v = counts.get(z,0)

        cols[i % 5].markdown(f"""
        <div style="
        background:white;
        border-left:6px solid {ORANGE};
        padding:15px;
        border-radius:8px;
        text-align:center;
        box-shadow:0px 2px 6px rgba(0,0,0,0.08)">
        <div style="font-size:13px;color:#64748b">{z}</div>
        <div style="font-size:28px;font-weight:bold">{v}</div>
        </div>
        """, unsafe_allow_html=True)


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
            .stApp {{ background: {BG}; }}
            .block-container {{ padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1400px; }}

            .hero {{
                background: linear-gradient(135deg, {ORANGE} 0%, #fb923c 100%);
                color: white;
                padding: 1.25rem 1.5rem;
                border-radius: 16px;
                box-shadow: 0 10px 25px rgba(0,0,0,.08);
                margin-bottom: 1rem;
            }}

            .hero h1 {{ margin: 0; font-size: 2rem; }}
            .hero p {{ margin: .35rem 0 0 0; font-size: 1rem; }}

            .metric-card {{
                background: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 14px;
                padding: 1rem 1.15rem;
                box-shadow: 0 4px 16px rgba(15,23,42,.05);
            }}

            .section-title {{
                background: {ORANGE};
                color: white;
                padding: .65rem 1rem;
                border-radius: 12px 12px 0 0;
                font-weight: 700;
                border: 1px solid {BORDER};
                border-bottom: 0;
                margin-top: 1rem;
            }}

            .table-wrap {{
                background: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 0 0 12px 12px;
                overflow: hidden;
                margin-bottom: 1rem;
            }}

            table.hh-table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 0.95rem;
            }}

            table.hh-table th {{
                background: {ORANGE};
                color: white;
                border: 2px solid black;
                padding: .6rem;
                text-align: center;
            }}

            table.hh-table td {{
                border: 2px solid black;
                padding: .55rem;
                text-align: center;
                background:#e5e7eb;
            }}

            table.hh-table td:first-child {{
                text-align: left;
                font-weight: 700;
                background: #fde68a;
            }}

            table.hh-table td.total-col {{ font-weight: 700; }}

            .legend {{ color: #475569; font-size: .92rem; margin-top: -.25rem; margin-bottom: .75rem; }}

            .small-note {{ color: #64748b; font-size: .82rem; }}

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

        if "data de escaneamento" in low:
            rename_map[col] = "Data de Escaneamento"

        elif "situa" in low:
            rename_map[col] = "Situação"

        elif "área" in low or "area" in low:
            rename_map[col] = "Área"

        elif "operador" in low:
            rename_map[col] = "Operador"

    df = df.rename(columns=rename_map)

    return df


def parse_hour(value):

    if pd.isna(value):
        return pd.NA

    text = str(value)

    match = re.search(r'(\d{1,2}):(\d{2})', text)

    if match:
        return int(match.group(1))

    try:
        return pd.to_datetime(text).hour
    except:
        return pd.NA


def render_table(df: pd.DataFrame):

    if df.empty:
        st.info("Sem dados para exibir nesta seção.")
        return

    display_df = df.copy().fillna("")

    headers = list(display_df.columns)

    html = ["<div class='table-wrap'><table class='hh-table'><thead><tr>"]

    html.extend([f"<th>{h}</th>" for h in headers])

    html.append("</tr></thead><tbody>")

    for _, row in display_df.iterrows():

        html.append("<tr>")

        for idx, value in enumerate(row.tolist()):

            cls = "total-col" if idx == len(headers) - 1 else ""

            html.append(f"<td class='{cls}'>{value}</td>")

        html.append("</tr>")

    html.append("</tbody></table></div>")

    st.markdown("".join(html), unsafe_allow_html=True)


def main():

    inject_css()

    st.markdown("""
    <div class="hero">
        <h1>HH Inventário</h1>
        <p>Faça upload da BASE INICIAL INVENTÁRIO.</p>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload da base (.xlsx ou .csv)", type=["xlsx","csv"])

    if not uploaded:
        st.stop()

    df = pd.read_excel(uploaded)

    df = normalize_columns(df)

    df["Hora"] = df["Data de Escaneamento"].apply(parse_hour)

    # ---------- MÉTRICAS ----------
    total_registros = len(df)
    total_verificados = (df["Situação"]=="Verificados").sum()
    total_pendentes = (df["Situação"]=="Pendente").sum()
    total_deslocados = (df["Situação"]=="Deslocado").sum()

    c1,c2,c3,c4 = st.columns(4)

    c1.metric("Base", total_registros)
    c2.metric("Verificados", total_verificados)
    c3.metric("Pendentes", total_pendentes)
    c4.metric("Deslocados", total_deslocados)

    # ---------- CARDS DE ZONA ----------
    if "Área" in df.columns:
        render_zona_cards(df)

    # ---------- HH ----------
    base_hour = int(df["Hora"].dropna().min())

    hours = list(range(base_hour, base_hour + 8))

    rows = []

    for status in STATUS_ORDER:

        subset = df[df["Situação"] == status]

        r = {"QTD / Status": status}

        for h in hours:

            r[f"{h}h"] = (subset["Hora"] == h).sum()

        r["TOTAL"] = len(subset)

        rows.append(r)

    status_df = pd.DataFrame(rows)

    st.markdown("<div class='section-title'>HH Inventário</div>", unsafe_allow_html=True)

    render_table(status_df)


if __name__ == "__main__":
    main()
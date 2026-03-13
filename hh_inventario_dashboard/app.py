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


def inject_css() -> None:
    st.markdown(
        f"""
<style>

/* OCULTAR MENU STREAMLIT */

#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden;}}

.stDeployButton {{display:none;}}
[data-testid="stToolbar"] {{display:none;}}
[data-testid="stDecoration"] {{display:none;}}
[data-testid="stStatusWidget"] {{display:none;}}

/* LAYOUT */

.stApp {{ background: {BG}; }}
.block-container {{ padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1500px; }}

.hero {{
    background: linear-gradient(135deg, {ORANGE} 0%, #fb923c 100%);
    color: white;
    padding: 1.25rem 1.5rem;
    border-radius: 16px;
    box-shadow: 0 10px 25px rgba(0,0,0,.08);
    margin-bottom: 1rem;
}}

.hero h1 {{ margin: 0; font-size: 2rem; }}
.hero p {{ margin: .35rem 0 0 0; font-size: 1rem; opacity: 0.95; }}

/* METRIC CARDS */

.metric-card {{
    background: white;
    border-radius: 16px;
    padding: 20px;
    border-top: 6px solid {ORANGE};
    box-shadow: 0 8px 20px rgba(0,0,0,0.06);
}}

.metric-label {{
    font-size:16px;
    color:#64748b;
}}

.metric-value {{
    font-size:44px;
    font-weight:800;
    color:#1f2937;
}}

/* TABELAS */

.section-title {{
    background: {ORANGE};
    color: white;
    padding: .8rem 1rem;
    border-radius: 12px 12px 0 0;
    font-weight: 700;
    font-size:20px;
    border: 1px solid {BORDER};
    border-bottom: 0;
}}

.table-wrap {{
    background: {WHITE};
    border: 1px solid {BORDER};
    border-radius: 0 0 12px 12px;
    overflow: hidden;
}}

table.hh-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 18px;
}}

table.hh-table th {{
    background: {ORANGE};
    color: white;
    border: 1px solid {BORDER};
    padding: 12px;
    font-size:20px;
    font-weight:700;
}}

table.hh-table td {{
    border: 1px solid {BORDER};
    padding: 14px;
    text-align: center;
    color: {DARK};
    font-size:20px;
}}

table.hh-table td:first-child {{
    text-align: left;
    font-weight: 700;
    background: #fff7ed;
    font-size:20px;
}}

table.hh-table td.total-col {{
    font-weight:900;
    font-size:22px;
}}

.legend {{
    color: #475569;
    font-size: 18px;
    margin-top: 10px;
}}

</style>
""",
        unsafe_allow_html=True,
    )


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    df.columns = [str(c).replace("\ufeff", "").strip() for c in df.columns]

    rename_map = {}

    for col in df.columns:

        low = col.lower()

        if "data de escaneamento" in low:
            rename_map[col] = "Data de Escaneamento"

        elif "situa" in low:
            rename_map[col] = "Situação"

    df = df.rename(columns=rename_map)

    return df


def parse_hour(value):

    if pd.isna(value):
        return pd.NA

    try:
        return pd.to_datetime(value).hour
    except:
        return pd.NA

def format_hour(hour):
    return f"{int(hour):02d}h"


def build_hour_columns(hours):

    labels = []

    for idx, hour in enumerate(hours):

        labels.append(f"{idx+1}ª Hora ({format_hour(hour)})")

    return hours, labels


def prepare_base_dataframe(file_bytes, name):

    if name.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(file_bytes))

    else:
        df = pd.read_excel(io.BytesIO(file_bytes))

    df = normalize_columns(df)

    df["Hora"] = df["Data de Escaneamento"].apply(parse_hour).astype("Int64")

    return df


def summarize_by_status(df, hours, hour_labels):

    rows = []

    for status in STATUS_ORDER:

        subset = df[df["Situação"] == status]

        row = OrderedDict()

        row["QTD / Status"] = status

        for hour, label in zip(hours, hour_labels):

            row[label] = int((subset["Hora"] == hour).sum())

        row["TOTAL"] = len(subset)

        rows.append(row)

    return pd.DataFrame(rows)


def render_table(df):

    html = "<div class='table-wrap'><table class='hh-table'>"

    html += "<thead><tr>"

    for col in df.columns:
        html += f"<th>{col}</th>"

    html += "</tr></thead><tbody>"

    for _, row in df.iterrows():

        html += "<tr>"

        for i, v in enumerate(row):

            cls = "total-col" if i == len(row) - 1 else ""

            html += f"<td class='{cls}'>{v}</td>"

        html += "</tr>"

    html += "</tbody></table></div>"

    st.markdown(html, unsafe_allow_html=True)


def main():

    inject_css()

    st.markdown(
        """
<div class="hero">
<h1>HH Inventário</h1>
<p>Faça upload de um arquivo base e o painel é montado automaticamente</p>
</div>
""",
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader("Upload da base", type=["xlsx", "csv"])

    if not uploaded:
        st.stop()

    df = prepare_base_dataframe(uploaded.getvalue(), uploaded.name)

valid_hours = sorted(df["Hora"].dropna().unique())

if len(valid_hours) == 0:
    st.error("Não foi possível identificar horas válidas na coluna 'Data de Escaneamento'. Verifique o formato da data.")
    st.stop()

base_hour = min(valid_hours)

    hours = list(range(base_hour, base_hour + 8))

    hours, hour_labels = build_hour_columns(hours)

    total_registros = len(df)
    total_verificados = (df["Situação"] == "Verificados").sum()
    total_pendentes = (df["Situação"] == "Pendente").sum()
    total_deslocados = (df["Situação"] == "Deslocado").sum()

    c1, c2, c3, c4 = st.columns(4)

    metrics = [
        (c1, "Volume Total", total_registros),
        (c2, "Verificados", total_verificados),
        (c3, "Pendentes", total_pendentes),
        (c4, "Deslocados", total_deslocados),
    ]

    for container, label, value in metrics:

        container.markdown(
            f"""
<div class="metric-card">
<div class="metric-label">{label}</div>
<div class="metric-value">{value}</div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown(
        f"<div class='legend'>Janela horária: <strong>{format_hour(hours[0])}</strong> até <strong>{format_hour(hours[-1])}</strong></div>",
        unsafe_allow_html=True,
    )

    status_df = summarize_by_status(df, hours, hour_labels)

    st.markdown("<div class='section-title'>HH Inventário</div>", unsafe_allow_html=True)

    render_table(status_df)


if __name__ == "__main__":
    main()

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

# ---------- CSS ----------
def inject_css():
    st.markdown(f"""
    <style>

    .stApp {{ background:{BG}; }}

    .hero {{
        background:linear-gradient(135deg,{ORANGE},#fb923c);
        color:white;
        padding:1.2rem;
        border-radius:14px;
        margin-bottom:20px;
    }}

    .metric {{
        background:white;
        padding:15px;
        border-radius:10px;
        border:1px solid {BORDER};
        text-align:center;
        font-weight:700;
    }}

    .section {{
        background:{ORANGE};
        color:white;
        padding:8px;
        font-weight:700;
        border-radius:8px 8px 0 0;
        margin-top:20px;
    }}

    table.hh {{
        width:100%;
        border-collapse:collapse;
        font-size:14px;
    }}

    table.hh th {{
        background:{ORANGE};
        color:white;
        padding:6px;
        border:1px solid {BORDER};
    }}

    table.hh td {{
        border:1px solid {BORDER};
        padding:6px;
        text-align:center;
    }}

    table.hh td:first-child {{
        font-weight:bold;
        text-align:left;
        background:#fff7ed;
    }}

    /* Pendentes Zona */

    .pend-top {{
        display:grid;
        grid-template-columns:2fr 1fr;
        border:2px solid black;
        margin-bottom:10px;
    }}

    .pend-left {{
        background:{ORANGE};
        padding:25px;
        text-align:center;
        font-weight:bold;
        font-size:20px;
        border-right:2px solid black;
    }}

    .pend-right {{
        background:{ORANGE};
        padding:25px;
        text-align:center;
        font-weight:bold;
        font-size:20px;
    }}

    .pend-row {{
        display:grid;
        grid-template-columns:2fr 1fr;
    }}

    .pend-name {{
        background:{ORANGE};
        padding:8px;
        font-weight:bold;
        border-bottom:1px solid black;
    }}

    .pend-value {{
        background:#e5e7eb;
        padding:8px;
        text-align:right;
        border-bottom:1px solid black;
    }}

    </style>
    """, unsafe_allow_html=True)

# ---------- NORMALIZA COLUNAS ----------
def normalize_columns(df):
    rename = {}

    for c in df.columns:

        low = c.lower()

        if "data" in low:
            rename[c] = "Data de Escaneamento"

        if "situa" in low:
            rename[c] = "Situação"

        if "operador" in low:
            rename[c] = "Operador"

        if "area" in low or "área" in low:
            rename[c] = "Área"

    df = df.rename(columns=rename)

    for col in ["Operador","Área"]:
        if col not in df.columns:
            df[col] = ""

    return df

# ---------- HORA ----------
def parse_hour(v):

    try:

        v = str(v).split("|")[0]

        t = pd.to_datetime(v)

        return t.hour

    except:
        return None

# ---------- TABELA ----------
def render_table(df):

    html = "<table class='hh'>"

    html += "<tr>"
    for c in df.columns:
        html += f"<th>{c}</th>"
    html += "</tr>"

    for _,r in df.iterrows():

        html += "<tr>"

        for v in r:
            html += f"<td>{v}</td>"

        html += "</tr>"

    html += "</table>"

    st.markdown(html,unsafe_allow_html=True)

# ---------- PENDENTES ZONA ----------
def render_pendentes_zona(df):

    zonas = [
        "Returns",
        "Sorting",
        "Problem Solving",
        "Missort",
        "Fraude",
        "Damaged",
        "Buffered",
        "Dispatch",
        "Containerized",
        "Bulky returns"
    ]

    counts = df["Área"].value_counts().to_dict()

    html = """
    <div class='pend-top'>
    <div class='pend-left'>Pendentes<br>Zona</div>
    <div class='pend-right'>Total</div>
    </div>
    """

    for z in zonas:

        v = counts.get(z,0)

        html += f"""
        <div class='pend-row'>
        <div class='pend-name'>{z}</div>
        <div class='pend-value'>{v}</div>
        </div>
        """

    st.markdown(html,unsafe_allow_html=True)

# ---------- MAIN ----------
def main():

    inject_css()

    st.markdown("""
    <div class='hero'>
    <h2>HH Inventário</h2>
    Dashboard automático baseado na BASE INICIAL INVENTÁRIO
    </div>
    """,unsafe_allow_html=True)

    file = st.file_uploader("Upload da base inventário",type=["xlsx","csv"])

    if not file:
        st.stop()

    if file.name.endswith("csv"):

        df = pd.read_csv(file)

    else:

        excel = pd.ExcelFile(file)

        sheet = excel.sheet_names[0]

        df = pd.read_excel(excel,sheet)

    df = normalize_columns(df)

    df["Hora"] = df["Data de Escaneamento"].apply(parse_hour)

    total = len(df)

    ver = (df["Situação"]=="Verificados").sum()

    pen = (df["Situação"]=="Pendente").sum()

    des = (df["Situação"]=="Deslocado").sum()

    c1,c2,c3,c4 = st.columns(4)

    c1.metric("Base",total)

    c2.metric("Verificados",ver)

    c3.metric("Pendentes",pen)

    c4.metric("Deslocados",des)

    # ---------- PENDENTES ZONA ----------

    st.markdown("<div class='section'>Pendentes Zona</div>",unsafe_allow_html=True)

    render_pendentes_zona(df)

    # ---------- HH STATUS ----------

    st.markdown("<div class='section'>HH Inventário</div>",unsafe_allow_html=True)

    base = df["Hora"].min()

    hours = list(range(base,base+8))

    rows=[]

    for s in STATUS_ORDER:

        sub=df[df["Situação"]==s]

        r={"Status":s}

        for h in hours:

            r[f"{h}h"]=(sub["Hora"]==h).sum()

        r["Total"]=len(sub)

        rows.append(r)

    status_df=pd.DataFrame(rows)

    render_table(status_df)

    # ---------- OPERADORES ----------

    st.markdown("<div class='section'>Verificados por Operador</div>",unsafe_allow_html=True)

    ops=df[df["Situação"]=="Verificados"]["Operador"].dropna().unique()

    rows=[]

    for o in ops:

        sub=df[(df["Operador"]==o)&(df["Situação"]=="Verificados")]

        r={"Operador":o}

        for h in hours:

            r[f"{h}h"]=(sub["Hora"]==h).sum()

        r["Total"]=len(sub)

        rows.append(r)

    render_table(pd.DataFrame(rows))

if __name__ == "__main__":
    main()

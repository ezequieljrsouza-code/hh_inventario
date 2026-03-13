
import io
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="HH Inventário", page_icon="📦", layout="wide")

ORANGE = "#f59e0b"
BG = "#f8fafc"
BORDER = "#d1d5db"

STATUS_ORDER = ["Verificados", "Pendente", "Deslocado"]

# ---------- CSS ----------
st.markdown(f"""
<style>
.stApp {{ background:{BG}; }}

.hero {{
background:linear-gradient(135deg,{ORANGE},#fb923c);
color:white;
padding:1.3rem;
border-radius:14px;
margin-bottom:1rem;
}}

.metric-card {{
background:white;
border-radius:12px;
padding:1rem;
text-align:center;
border:1px solid {BORDER};
}}

.section-title {{
background:{ORANGE};
color:white;
padding:.6rem 1rem;
border-radius:8px;
margin-top:1rem;
font-weight:bold;
}}

table.hh-table {{
width:100%;
border-collapse:collapse;
font-size:0.95rem;
}}

table.hh-table th {{
background:{ORANGE};
color:white;
padding:.6rem;
border:1px solid {BORDER};
}}

table.hh-table td {{
border:1px solid {BORDER};
padding:.5rem;
text-align:center;
}}

table.hh-table td:first-child {{
text-align:left;
font-weight:bold;
background:#fff7ed;
}}
</style>
""", unsafe_allow_html=True)


# ---------- NORMALIZAR COLUNAS ----------
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
    return df


# ---------- TABELA HTML ----------
def render_table(df):
    html = "<table class='hh-table'>"
    html += "<tr>"
    for c in df.columns:
        html += f"<th>{c}</th>"
    html += "</tr>"

    for _, r in df.iterrows():
        html += "<tr>"
        for v in r:
            html += f"<td>{v}</td>"
        html += "</tr>"

    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)


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


# ---------- EXPORTAR IMAGEM ----------
def export_dashboard_image(df):

    fig, ax = plt.subplots(figsize=(12,3))
    ax.axis('off')

    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        loc='center'
    )

    table.auto_set_font_size(False)
    table.set_fontsize(10)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)

    st.download_button(
        "📸 Baixar imagem para WhatsApp",
        data=buf,
        file_name="hh_inventario.png",
        mime="image/png"
    )


# ---------- HEADER ----------
st.markdown("""
<div class='hero'>
<h1>HH Inventário</h1>
Dashboard automático baseado na BASE INICIAL INVENTÁRIO
</div>
""", unsafe_allow_html=True)


# ---------- UPLOAD ----------
file = st.file_uploader("Upload BASE INICIAL INVENTÁRIO", type=["xlsx","csv"])

if not file:
    st.stop()

if file.name.endswith("csv"):
    df = pd.read_csv(file)
else:
    df = pd.read_excel(file)

df = normalize_columns(df)

if "Data de Escaneamento" not in df.columns:
    st.error("Coluna 'Data de Escaneamento' não encontrada.")
    st.stop()

df["Hora"] = pd.to_datetime(df["Data de Escaneamento"], errors="coerce").dt.hour

if df["Hora"].dropna().empty:
    st.error("Não foi possível identificar horas válidas na coluna 'Data de Escaneamento'.")
    st.stop()

# ---------- MÉTRICAS ----------
total = len(df)
ver = (df["Situação"] == "Verificados").sum()
pen = (df["Situação"] == "Pendente").sum()
des = (df["Situação"] == "Deslocado").sum()

c1,c2,c3,c4 = st.columns(4)

c1.metric("Base", total)
c2.metric("Verificados", ver)
c3.metric("Pendentes", pen)
c4.metric("Deslocados", des)

# ---------- ZONAS ----------
if "Área" in df.columns:
    render_zona_cards(df)

# ---------- HH STATUS ----------
st.markdown("<div class='section-title'>HH Inventário</div>", unsafe_allow_html=True)

base_hour = int(df["Hora"].dropna().min())
hours = list(range(base_hour, base_hour + 8))

rows = []
for s in STATUS_ORDER:
    sub = df[df["Situação"] == s]
    r = {"QTD / Status": s}
    for h in hours:
        r[f"{h}h"] = (sub["Hora"] == h).sum()
    r["TOTAL"] = len(sub)
    rows.append(r)

status_df = pd.DataFrame(rows)

render_table(status_df)
export_dashboard_image(status_df)

# ---------- OPERADORES ----------
def summarize_operator(df, status, hours):
    sub = df[df["Situação"] == status]
    ops = sub["Operador"].dropna().unique()
    rows = []
    for o in ops:
        op = sub[sub["Operador"] == o]
        r = {"Operador": o}
        for h in hours:
            r[f"{h}h"] = (op["Hora"] == h).sum()
        r["TOTAL"] = len(op)
        rows.append(r)
    return pd.DataFrame(rows)

st.markdown("<div class='section-title'>Verificados / Conferentes</div>", unsafe_allow_html=True)
ver_df = summarize_operator(df,"Verificados",hours)
if not ver_df.empty:
    render_table(ver_df)

st.markdown("<div class='section-title'>Deslocados / Conferentes</div>", unsafe_allow_html=True)
des_df = summarize_operator(df,"Deslocado",hours)
if not des_df.empty:
    render_table(des_df)

# ---------- EXPORTAR BASE ----------
st.download_button(
    "Baixar base tratada",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="base_tratada.csv"
)

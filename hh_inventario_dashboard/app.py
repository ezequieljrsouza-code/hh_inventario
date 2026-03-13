import io
import re
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="HH Inventário", page_icon="📦", layout="wide")

ORANGE = "#f59e0b"
BG = "#f8fafc"

STATUS_ORDER = ["Verificados", "Pendente", "Deslocado"]

# ---------- CSS ----------
st.markdown(f"""
<style>

.stApp {{
background:{BG};
}}

.section-title {{
background:{ORANGE};
color:white;
padding:.6rem;
font-weight:bold;
margin-top:20px;
}}

table.hh-table {{
border-collapse:collapse;
width:100%;
}}

table.hh-table td {{
border:2px solid #000000;
padding:.55rem;
text-align:center;
background:#e5e7eb;
}}

table.hh-table td:first-child {{
background:#fde68a;
font-weight:bold;
text-align:left;
}}

table.hh-table th {{
background:#f59e0b;
color:white;
border:2px solid #000000;
padding:.55rem;
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


# ---------- RENDER TABELA ----------
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


# ---------- EXPORTAR PAINEL COMPLETO ----------
def export_dashboard_image(status_df, ver_df, des_df):

    fig, axs = plt.subplots(3,1, figsize=(16,10))

    tables = [
        ("HH Inventário", status_df),
        ("Verificados / Conferentes", ver_df),
        ("Deslocados / Conferentes", des_df)
    ]

    for ax, (title, df) in zip(axs, tables):

        ax.axis('off')

        table = ax.table(
            cellText=df.values,
            colLabels=df.columns,
            loc='center',
            cellLoc='center'
        )

        table.auto_set_font_size(False)
        table.set_fontsize(10)

        for (row,col), cell in table.get_celld().items():

            cell.set_edgecolor("black")
            cell.set_linewidth(2)

            if row == 0:
                cell.set_facecolor("#f59e0b")
                cell.get_text().set_color("white")

            elif col == 0:
                cell.set_facecolor("#fde68a")

            else:
                cell.set_facecolor("#e5e7eb")

        ax.set_title(title, fontsize=14, fontweight="bold")

    buf = io.BytesIO()

    plt.tight_layout()

    plt.savefig(buf, format="png", dpi=300)

    buf.seek(0)

    st.download_button(
        "📸 Baixar painel completo para WhatsApp",
        data=buf,
        file_name="hh_inventario_dashboard.png",
        mime="image/png"
    )


# ---------- HEADER ----------
st.title("HH Inventário")

st.write("Dashboard automático baseado na BASE INICIAL INVENTÁRIO")

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

# ---------- EXTRAIR HORA ----------
def extrair_hora(valor):

    if pd.isna(valor):
        return None

    texto = str(valor)

    match = re.search(r'(\\d{1,2}):(\\d{2})', texto)

    if match:
        return int(match.group(1))

    try:
        return pd.to_datetime(texto).hour
    except:
        return None


df["Hora"] = df["Data de Escaneamento"].apply(extrair_hora)

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


# ---------- BOTÃO WHATSAPP ----------
export_dashboard_image(status_df, ver_df, des_df)


# ---------- EXPORTAR BASE ----------
st.download_button(
    "Baixar base tratada",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="base_tratada.csv"
)
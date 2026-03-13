import pandas as pd
import streamlit as st
import plotly.express as px
from io import BytesIO

st.set_page_config(
    page_title="HH Inventário",
    page_icon="📦",
    layout="wide"
)

ORANGE = "#f59e0b"

# ---------------- CSS ----------------

st.markdown("""
<style>

.stApp {
background:#f3f4f6;
}

.hero {
background:linear-gradient(135deg,#f59e0b,#fb923c);
padding:22px;
border-radius:12px;
color:white;
margin-bottom:20px;
}

.card {
background:white;
padding:18px;
border-radius:10px;
box-shadow:0px 2px 8px rgba(0,0,0,0.08);
text-align:center;
}

.metric-title {
font-size:14px;
color:#64748b;
}

.metric-value {
font-size:30px;
font-weight:bold;
color:#1f2937;
}

.section {
background:#f59e0b;
color:white;
padding:8px;
font-weight:bold;
border-radius:6px;
margin-top:25px;
}

</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------

st.markdown("""
<div class='hero'>
<h1>HH Inventário</h1>
Dashboard automático baseado na BASE INICIAL INVENTÁRIO
</div>
""", unsafe_allow_html=True)

# ---------------- UPLOAD ----------------

file = st.file_uploader("Upload BASE INICIAL INVENTÁRIO", type=["xlsx","csv"])

if not file:
    st.stop()

# ---------------- LEITURA ----------------

if file.name.endswith(".csv"):
    df = pd.read_csv(file)
else:
    df = pd.read_excel(file)

df.columns = [c.strip() for c in df.columns]

df["Hora"] = pd.to_datetime(df["Data de Escaneamento"], errors="coerce").dt.hour

# ---------------- MÉTRICAS ----------------

total = len(df)
verificados = (df["Situação"]=="Verificados").sum()
pendentes = (df["Situação"]=="Pendente").sum()
deslocados = (df["Situação"]=="Deslocado").sum()

c1,c2,c3,c4 = st.columns(4)

with c1:
    st.markdown(f"<div class='card'><div class='metric-title'>Base</div><div class='metric-value'>{total}</div></div>",unsafe_allow_html=True)

with c2:
    st.markdown(f"<div class='card'><div class='metric-title'>Verificados</div><div class='metric-value'>{verificados}</div></div>",unsafe_allow_html=True)

with c3:
    st.markdown(f"<div class='card'><div class='metric-title'>Pendentes</div><div class='metric-value'>{pendentes}</div></div>",unsafe_allow_html=True)

with c4:
    st.markdown(f"<div class='card'><div class='metric-title'>Deslocados</div><div class='metric-value'>{deslocados}</div></div>",unsafe_allow_html=True)

# ---------------- PENDENTES ZONA ----------------

st.markdown("<div class='section'>Pendentes Zona</div>", unsafe_allow_html=True)

zonas = [
"Returns","Sorting","Problem Solving","Missort",
"Fraude","Damaged","Buffered","Dispatch",
"Containerized","Bulky returns"
]

counts = df["Área"].value_counts().to_dict()

cols = st.columns(5)

for i,z in enumerate(zonas):

    val = counts.get(z,0)

    with cols[i%5]:

        st.markdown(f"""
        <div style="
        background:white;
        border-left:6px solid #f59e0b;
        padding:15px;
        border-radius:8px;
        text-align:center;
        box-shadow:0px 2px 6px rgba(0,0,0,0.08)
        ">
        <div style="font-size:13px;color:#64748b">{z}</div>
        <div style="font-size:26px;font-weight:bold;color:#1f2937">{val}</div>
        </div>
        """, unsafe_allow_html=True)

# ---------------- PRODUTIVIDADE POR HORA ----------------

st.markdown("<div class='section'>Produtividade por Hora</div>", unsafe_allow_html=True)

prod = df.groupby("Hora").size().reset_index(name="Pacotes")

fig = px.bar(
    prod,
    x="Hora",
    y="Pacotes",
    color_discrete_sequence=[ORANGE]
)

fig.update_layout(
    height=400,
    plot_bgcolor="white",
    paper_bgcolor="white",
    font_color="#1f2937",
    xaxis_title="Hora",
    yaxis_title="Pacotes Processados"
)

st.plotly_chart(fig, use_container_width=True)

# ---------------- HH INVENTÁRIO ----------------

st.markdown("<div class='section'>HH Inventário</div>", unsafe_allow_html=True)

hh = df.groupby(["Situação","Hora"]).size().unstack(fill_value=0)

hh["Total"] = hh.sum(axis=1)

st.dataframe(hh,use_container_width=True)

# ---------------- RANKING OPERADORES ----------------

st.markdown("<div class='section'>Ranking de Operadores</div>", unsafe_allow_html=True)

ranking = (
    df.groupby("Operador")
    .size()
    .sort_values(ascending=False)
    .reset_index(name="Pacotes")
)

st.dataframe(ranking,use_container_width=True)

fig2 = px.bar(
    ranking.head(10),
    x="Operador",
    y="Pacotes",
    color_discrete_sequence=[ORANGE]
)

fig2.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    font_color="#1f2937"
)

st.plotly_chart(fig2, use_container_width=True)

# ---------------- EXPORTAÇÃO ----------------

st.markdown("<div class='section'>Exportar Dados</div>", unsafe_allow_html=True)

buffer = BytesIO()

with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    hh.to_excel(writer, sheet_name="HH Inventario")
    ranking.to_excel(writer, sheet_name="Ranking")

st.download_button(
    label="📥 Baixar Relatório Excel",
    data=buffer.getvalue(),
    file_name="hh_inventario_relatorio.xlsx"
)
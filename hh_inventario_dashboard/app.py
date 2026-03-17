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
        header {{visibility: hidden;}}
        [data-testid="stToolbar"] {{display: none;}}
        [data-testid="stDecoration"] {{display: none;}}
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        .stDeployButton {{display:none;}}
        
        .stApp {{ background: {BG_APP}; }}
        .block-container {{ padding-top: 1.5rem; max-width: 95%; }}

        .main-header {{ text-align: center; padding: 20px 0 40px 0; }}
        .main-header h1 {{
            font-size: 3.5rem;
            font-weight: 900;
            color: {DARK_TEXT};
            margin: 0;
            letter-spacing: -2px;
        }}

        .metric-row {{ display: flex; justify-content: space-between; gap: 20px; margin-bottom: 40px; }}
        .modern-card {{
            background: {WHITE};
            flex: 1;
            padding: 25px 20px;
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border: 1px solid {BORDER};
        }}

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
            background: {WHITE};
            border-radius: 0 0 15px 15px;
            padding: 5px;
            margin-bottom: 30px;
            border: 1px solid {BORDER};
        }}

        table.hh-table {{ width: 100%; border-collapse: collapse; font-size: 1.25rem; }}
        table.hh-table th {{ background: #fff; padding: 15px; border-bottom: 2px solid {BG_APP}; }}
        table.hh-table td {{ padding: 15px; text-align: center; border-bottom: 1px solid {BG_APP}; }}
        .total-cell {{ font-weight: 900 !important; color: {ORANGE} !important; }}
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
    uploaded = st.file_uploader("📂 Base de Dados", type=["xlsx", "csv"])
    st.markdown('<div class="main-header"><h1>HH Inventário</h1></div>', unsafe_allow_html=True)
    
    if not uploaded:
        st.info("Por favor, faça o upload da base de dados.")
        st.stop()

    # CONTAINER DE CAPTURA
    st.markdown('<div id="capture-area" style="padding: 10px; background-color: #f1f5f9;">', unsafe_allow_html=True)

    df = pd.read_excel(uploaded) if uploaded.name.endswith('.xlsx') else pd.read_csv(uploaded)
    df = normalize_columns(df)
    df["Hora"] = df["Data de Escaneamento"].apply(parse_hour).astype("Int64")
    
    valid_hours = sorted([int(h) for h in df["Hora"].dropna().unique().tolist()])
    if not valid_hours: st.stop()
    base_h = min(valid_hours)
    hours = list(range(base_h, base_h + 8))
    hour_labels = [f"{idx+1}ª Hora ({h:02d}h)" for idx, h in enumerate(hours)]

    v_total = len(df)
    v_verif = int((df['Situação'] == 'Verificados').sum())
    v_pend = int((df['Situação'] == 'Pendente').sum())
    v_acu = (v_verif / v_total * 100) if v_total > 0 else 0.0

    st.markdown(f"""
    <div class="metric-row">
        <div class="modern-card">Total: {v_total}</div>
        <div class="modern-card" style="border-top: 5px solid green;">Verificados: {v_verif}</div>
        <div class="modern-card" style="border-top: 5px solid red;">Pendentes: {v_pend}</div>
        <div class="modern-card" style="border-top: 5px solid {ORANGE};">Acuracidade: {v_acu:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='section-header'>Resumo Operacional HH</div>", unsafe_allow_html=True)
    rows = []
    for s in STATUS_ORDER:
        row = OrderedDict({"Status": s})
        for h, lab in zip(hours, hour_labels): row[lab] = int(((df["Situação"]==s) & (df["Hora"]==h)).sum())
        row["TOTAL"] = int((df["Situação"]==s).sum())
        rows.append(row)
    render_table(pd.DataFrame(rows))

    st.markdown('</div>', unsafe_allow_html=True)

    # SCRIPT DE CAPTURA ULTRA-ROBUSTO
    st.components.v1.html(
        f"""
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
        <button id="cap-btn" style="background:{ORANGE}; color:white; border:none; padding:12px 24px; border-radius:50px; font-weight:bold; cursor:pointer; position:fixed; bottom:20px; left:20px; z-index:10000; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">
            📸 Salvar Imagem HD
        </button>

        <script>
        document.getElementById('cap-btn').addEventListener('click', function() {{
            const area = window.parent.document.querySelector("#capture-area");
            
            window.parent.scrollTo(0,0);
            
            html2canvas(area, {{
                scale: 2,
                backgroundColor: "#f1f5f9",
                useCORS: true,
                allowTaint: true,
                logging: true,
                width: area.offsetWidth,
                height: area.offsetHeight,
                windowWidth: area.scrollWidth,
                windowHeight: area.scrollHeight
            }}).then(canvas => {{
                const link = document.createElement('a');
                link.download = 'HH_Inventario.png';
                link.href = canvas.toDataURL("image/png");
                link.click();
            }}).catch(err => alert("Erro ao gerar: " + err));
        }});
        </script>
        """,
        height=80,
    )

if __name__ == "__main__":
    main()

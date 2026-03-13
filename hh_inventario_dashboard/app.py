import io
import re
from collections import OrderedDict

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

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

        /* ---------- OCULTAR MENU STREAMLIT ---------- */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}

        .stDeployButton {{display:none;}}
        [data-testid="stToolbar"] {{display:none;}}
        [data-testid="stDecoration"] {{display:none;}}
        [data-testid="stStatusWidget"] {{display:none;}}

        /* ---------- CORREÇÃO HTML2CANVAS (ESPAÇOS EM BRANCO) ---------- */
        /* Força a renderização normal para evitar que palavras se juntem no print */
        * {{
            text-rendering: geometricPrecision !important;
            font-variant-ligatures: none !important;
            word-spacing: normal !important;
            letter-spacing: normal !important;
        }}

        /* ---------- LAYOUT ---------- */

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
        .hero p {{ margin: .35rem 0 0 0; font-size: 1rem; opacity: 0.95; }}

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
            margin-top: .5rem;
            font-size: 1.15rem;
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
            font-size: 1.15rem; 
        }}

        table.hh-table th {{
            background: {ORANGE};
            color: white;
            border: 1px solid {BORDER};
            padding: .8rem .6rem; 
            text-align: center;
            white-space: nowrap;
            font-size: 1.2rem; 
        }}

        table.hh-table td {{
            border: 1px solid {BORDER};
            padding: .7rem; 
            text-align: center;
            color: {DARK};
        }}

        table.hh-table td:first-child {{
            text-align: left;
            font-weight: 700;
            background: #fff7ed;
        }}

        table.hh-table td.total-col {{ font-weight: 700; font-size: 1.25rem; }}

        .legend {{ color: #475569; font-size: 1.05rem; margin-top: -.25rem; margin-bottom: .75rem; }}

        .small-note {{ color: #64748b; font-size: 0.95rem; font-weight: bold; }}

        .stFileUploader > div > div {{ background: {WHITE}; border-radius: 12px; }}

        </style>
        """,
        unsafe_allow_html=True,
    )


def render_capture_button():
    """Injeta um botão HTML/JS para tirar print da tela e baixar como imagem"""
    components.html(
        """
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
        <style>
        .btn-capture {
            background-color: #10b981;
            color: white;
            border: none;
            padding: 14px 24px;
            text-align: center;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            font-weight: bold;
            border-radius: 8px;
            cursor: pointer;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: 0.3s;
            width: 100%;
            font-family: sans-serif;
            margin-top: 10px;
        }
        .btn-capture:hover { background-color: #059669; }
        </style>
        <button class="btn-capture" onclick="capture()">
            📸 Capturar Painel como Imagem (WhatsApp)
        </button>
        <script>
        function capture() {
            var btn = document.querySelector('.btn-capture');
            var originalText = btn.innerHTML;
            btn.innerHTML = '⏳ Gerando imagem...';
            
            var target = window.parent.document.querySelector('.block-container');
            
            if(target) {
                html2canvas(target, {
                    scale: 2,
                    useCORS: true,
                    backgroundColor: '#f8fafc',
                    logging: false,
                    letterRendering: true, // Melhora a renderização de letras individuais
                    onclone: (clonedDoc) => {
                        // Força todos os elementos no clone a terem espaçamento de palavra normal
                        const all = clonedDoc.querySelectorAll('*');
                        all.forEach(el => {
                            el.style.wordSpacing = 'normal';
                            el.style.letterSpacing = 'normal';
                        });
                    }
                }).then(canvas => {
                    var link = document.createElement('a');
                    link.download = 'painel_inventario.png';
                    link.href = canvas.toDataURL('image/png');
                    link.click();
                    btn.innerHTML = originalText;
                }).catch(err => {
                    console.error('Erro na captura:', err);
                    btn.innerHTML = '❌ Erro ao capturar';
                    setTimeout(() => { btn.innerHTML = originalText; }, 3000);
                });
            } else {
                btn.innerHTML = '❌ Container não encontrado';
            }
        }
        </script>
        """,
        height=80
    )


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).replace("\ufeff", "").strip().strip('"') for c in df.columns]
    rename_map = {}
    for col in df.columns:
        low = col.lower()
        if "pacote" in low:
            rename_map[col] = "Pacote"
        elif "data de escaneamento" in low:
            rename_map[col] = "Data de Escaneamento"
        elif "situa" in low:
            rename_map[col] = "Situação"
        elif "área" in low or "area" in low:
            rename_map[col] = "Área"
        elif "operador" in low:
            rename_map[col] = "Operador"
        elif "coment" in low:
            rename_map[col] = "Comentário"
    df = df.rename(columns=rename_map)
    required = ["Data de Escaneamento", "Situação"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(missing)}")
    for optional in ["Área", "Operador", "Comentário", "Pacote"]:
        if optional not in df.columns:
            df[optional] = pd.NA
    return df


def parse_hour(value) -> float:
    if pd.isna(value):
        return pd.NA
    text = str(value).strip()
    if not text:
        return pd.NA
    time_part = text.split("|")[0].strip()
    time_part = time_part.replace(".", ":")
    match = re.search(r"(\d{{1,2}}:\d{{2}}\s*[ap]m)", time_part, flags=re.I)
    if match:
        time_part = match.group(1)
    for fmt in ("%I:%M%p", "%I:%M %p", "%H:%M"):
        parsed = pd.to_datetime(time_part, format=fmt, errors="coerce")
        if not pd.isna(parsed):
            return int(parsed.hour)
    flexible = pd.to_datetime(time_part, errors="coerce")
    if not pd.isna(flexible):
        return int(flexible.hour)
    return pd.NA


def format_hour(hour_value: int) -> str:
    return f"{int(hour_value):02d}h"


def build_hour_columns(hours: list[int]) -> tuple[list[int], list[str]]:
    labels = [f"{idx + 1}ª Hora ({format_hour(hour)})" for idx, hour in enumerate(hours)]
    return hours, labels


def prepare_base_dataframe(file_bytes: bytes, uploaded_name: str) -> pd.DataFrame:
    if uploaded_name.lower().endswith(".csv"):
        df = pd.read_csv(io.BytesIO(file_bytes))
    else:
        excel = pd.ExcelFile(io.BytesIO(file_bytes))
        preferred = None
        for name in excel.sheet_names:
            if name.strip().upper() == "BASE INICIAL INVENTÁRIO":
                preferred = name
                break
        preferred = preferred or excel.sheet_names[0]
        df = pd.read_excel(excel, sheet_name=preferred)
    df = normalize_columns(df)
    df["Situação"] = df["Situação"].astype(str).str.strip()
    df["Operador"] = df["Operador"].astype("string").str.strip()
    df["Hora"] = df["Data de Escaneamento"].apply(parse_hour).astype("Int64")
    return df


def summarize_by_status(df: pd.DataFrame, hours: list[int], hour_labels: list[str]) -> pd.DataFrame:
    rows = []
    for status in STATUS_ORDER:
        subset = df[df["Situação"] == status]
        row = OrderedDict()
        row["QTD / Status"] = status
        for hour, label in zip(hours, hour_labels):
            row[label] = int((subset["Hora"] == hour).sum())
        row["TOTAL"] = int(len(subset))
        rows.append(row)
    return pd.DataFrame(rows)


def summarize_by_operator(df: pd.DataFrame, status: str, title_prefix: str, hours: list[int], hour_labels: list[str]) -> tuple[str, pd.DataFrame]:
    subset = df[(df["Situação"] == status) & df["Operador"].notna() & (df["Operador"].str.len() > 0)]
    operators = list(dict.fromkeys(subset["Operador"].tolist()))
    rows = []
    for operator in operators:
        op_subset = subset[subset["Operador"] == operator]
        row = OrderedDict()
        
        # CORREÇÃO AQUI: Substitui espaços normais por espaços não quebráveis (HTML entity)
        # Isso impede que o html2canvas una as palavras.
        operator_safe = str(operator).replace(" ", "&nbsp;")
        row[title_prefix] = operator_safe
        
        for hour, label in zip(hours, hour_labels):
            row[label] = int((op_subset["Hora"] == hour).sum())
        row["TOTAL"] = int(len(op_subset))
        rows.append(row)
    title = f"{title_prefix}: {len(operators)}"
    return title, pd.DataFrame(rows)


def render_table(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("Sem dados para exibir nesta seção.")
        return
    display_df = df.copy()
    display_df = display_df.fillna("")
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


def main() -> None:
    inject_css()

    st.markdown(
        """
        <div class="hero">
            <h1>HH Inventário</h1>
            <p>Faça upload de um arquivo base e o painel é montado automaticamente com o mesmo racional da guia HH INVENTÁRIO.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Upload da base (.xlsx ou .csv)",
        type=["xlsx", "xls", "csv"],
        help="Preferencialmente um arquivo com a estrutura da guia BASE INICIAL INVENTÁRIO.",
    )

    with st.expander("Estrutura esperada do arquivo", expanded=not bool(uploaded)):
        st.markdown(
            """
            A aplicação espera, no mínimo, estas colunas:
            - **Data de Escaneamento**
            - **Situação**

            E também aproveita, quando existirem:
            - **Operador**
            - **Área**
            - **Comentário**
            - **Pacote**
            """
        )

    if not uploaded:
        st.stop()

    try:
        file_bytes = uploaded.getvalue()
        df = prepare_base_dataframe(file_bytes, uploaded.name)
    except Exception as exc:
        st.error(f"Não foi possível ler o arquivo: {exc}")
        st.stop()

    valid_hours = sorted([int(h) for h in df["Hora"].dropna().unique().tolist()])
    if not valid_hours:
        st.error("Não foi possível identificar nenhuma hora válida na coluna 'Data de Escaneamento'.")
        st.stop()

    base_hour = min(valid_hours)
    hours = list(range(base_hour, base_hour + 8))
    hours, hour_labels = build_hour_columns(hours)

    total_registros = len(df)
    total_verificados = int((df["Situação"] == "Verificados").sum())
    total_pendentes = int((df["Situação"] == "Pendente").sum())
    total_deslocados = int((df["Situação"] == "Deslocado").sum())

    c1, c2, c3, c4 = st.columns(4)
    metrics = [
        (c1, "Volume Total", f"{total_registros:,}".replace(",", ".")),
        (c2, "Verificados", f"{total_verificados:,}".replace(",", ".")),
        (c3, "Pendentes", f"{total_pendentes:,}".replace(",", ".")),
        (c4, "Deslocados", f"{total_deslocados:,}".replace(",", ".")),
    ]
    for container, label, value in metrics:
        # Tamanho da fonte dos cards de métricas ligeiramente aumentado
        container.markdown(
            f"<div class='metric-card'><div class='small-note'>{label}</div><div style='font-size:2.2rem;font-weight:800;color:{DARK}'>{value}</div></div>",
            unsafe_allow_html=True,
        )
        
    # ---------------- PENDENTES ZONA ----------------

    if "Área" in df.columns:

        st.markdown("<div class='section-title'>Pendentes Zona</div>", unsafe_allow_html=True)

        zonas = [
            "Returns","Sorting","Problem Solving","Missort",
            "Fraude","Damaged","Buffered","Dispatch",
            "Containerized","Bulky returns"
        ]

        counts = df[df["Situação"]=="Pendente"]["Área"].value_counts().to_dict()

        cols = st.columns(5)

        for i,z in enumerate(zonas):

            val = counts.get(z,0)

            with cols[i % 5]:
                # Fontes da zona aumentadas (13px -> 15px, 28px -> 32px)
                st.markdown(f"""
                <div style="
                background:white;
                border-left:6px solid {ORANGE};
                padding:15px;
                border-radius:10px;
                text-align:center;
                box-shadow:0px 2px 6px rgba(0,0,0,0.08)
                ">
                <div style="font-size:15px;color:#64748b">{z}</div>
                <div style="font-size:32px;font-weight:bold;color:{DARK}">{val}</div>
                </div>
                """, unsafe_allow_html=True)
                
    st.markdown(
        f"<div class='legend'>Janela horária usada no painel: <strong>{format_hour(hours[0])}</strong> até <strong>{format_hour(hours[-1])}</strong>.</div>",
        unsafe_allow_html=True,
    )

    status_df = summarize_by_status(df, hours, hour_labels)
    verif_title, verif_df = summarize_by_operator(df, "Verificados", "Verificados / Conferentes", hours, hour_labels)
    desloc_title, desloc_df = summarize_by_operator(df, "Deslocado", "Deslocados / Conferentes", hours, hour_labels)

    st.markdown("<div class='section-title'>HH Inventário</div>", unsafe_allow_html=True)
    render_table(status_df)

    st.markdown(f"<div class='section-title'>{verif_title}</div>", unsafe_allow_html=True)
    render_table(verif_df)

    st.markdown(f"<div class='section-title'>{desloc_title}</div>", unsafe_allow_html=True)
    render_table(desloc_df)

    # Botão de captura via JS e botão de download do CSV lado a lado
    col_capture, col_csv = st.columns([1, 1])
    
    with col_capture:
        render_capture_button()
        
    with col_csv:
        st.markdown("<br>", unsafe_allow_html=True) # Espaçamento para alinhar os botões
        st.download_button(
            "Baixar base tratada em CSV",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name="base_tratada_inventario.csv",
            mime="text/csv",
            use_container_width=True
        )

    with st.expander("Regra aplicada no cálculo", expanded=False):
        st.markdown(
            """
            - A coluna **Data de Escaneamento** é convertida para hora.
            - O painel usa a primeira hora encontrada na base como ponto de partida.
            - São exibidas **8 colunas horárias sequenciais**, no mesmo espírito da guia HH INVENTÁRIO.
            - A tabela principal agrupa por **Situação**.
            - As tabelas inferiores agrupam por **Operador**, separando **Verificados** e **Deslocado**.
            """
        )

if __name__ == "__main__":
    main()

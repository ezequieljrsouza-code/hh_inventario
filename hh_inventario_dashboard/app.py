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

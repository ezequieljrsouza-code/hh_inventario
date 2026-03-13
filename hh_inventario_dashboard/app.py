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
            border: 1px solid {BORDER};
            padding: .6rem .55rem;
            text-align: center;
            white-space: nowrap;
        }}

        table.hh-table td {{
            border: 1px solid {BORDER};
            padding: .55rem;
            text-align: center;
            color: {DARK};
        }}

        table.hh-table td:first-child {{
            text-align: left;
            font-weight: 700;
            background: #fff7ed;
        }}

        table.hh-table td.total-col {{ font-weight: 700; }}

        .legend {{ color: #475569; font-size: .92rem; margin-top: -.25rem; margin-bottom: .75rem; }}

        .small-note {{ color: #64748b; font-size: .82rem; }}

        .stFileUploader > div > div {{ background: {WHITE}; border-radius: 12px; }}

        </style>
        """,
        unsafe_allow_html=True,
    )
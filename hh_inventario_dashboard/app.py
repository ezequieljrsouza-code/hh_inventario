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

    data = []

    for z in zonas:
        data.append({
            "Pendentes Zona": z,
            "Total": counts.get(z, 0)
        })

    pend_df = pd.DataFrame(data)

    st.dataframe(
        pend_df,
        use_container_width=True,
        hide_index=True
    )
CORES_QUARTOS = {
    "Quarto com ventilador + Banheiro Compartilhado": "#2E86AB",
    "Quarto com Ar-condicionado + Banheiro Privativo": "#00A676",
    "Quarto Compartilhado Masculino": "#6C63FF",
    "Quarto Compartilhado Feminino": "#FF6B9A"

}

grafico_config = {
    "displayModeBar": False,
    "responsive": True
}

st.divider()

col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.subheader("🛏️ Reservas por quarto")

    reservas_por_quarto = (
        df_filtrado.groupby("Tipo")
        .size()
        .reset_index(name="Reservas")
        .sort_values("Reservas", ascending=True)
    )

    fig_reservas = px.bar(
        reservas_por_quarto,
        x="Reservas",
        y="Tipo",
        color="Tipo",
        text="Reservas",
        orientation="h",
        color_discrete_map=CORES_QUARTOS
    )

    fig_reservas.update_traces(
        textposition="outside",
        textfont_size=15,
        marker_line_width=0,
        hovertemplate="<b>%{y}</b><br>Reservas: %{x}<extra></extra>"
    )

    fig_reservas.update_layout(
        height=430,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Reservas",
        yaxis_title="",
        showlegend=False,
        margin=dict(l=10, r=50, t=20, b=20),
        font=dict(size=13)
    )

    fig_reservas.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.2)")
    fig_reservas.update_yaxes(showgrid=False)

    st.plotly_chart(fig_reservas, use_container_width=True, config=grafico_config)

with col_graf2:
    st.subheader("👥 Pessoas por quarto")

    pessoas_por_quarto = (
        df_filtrado.groupby("Tipo")["Pessoas"]
        .sum()
        .reset_index()
        .sort_values("Pessoas", ascending=True)
    )

    fig_pessoas = px.bar(
        pessoas_por_quarto,
        x="Pessoas",
        y="Tipo",
        color="Tipo",
        text="Pessoas",
        orientation="h",
        color_discrete_map=CORES_QUARTOS
    )

    fig_pessoas.update_traces(
        textposition="outside",
        textfont_size=15,
        marker_line_width=0,
        hovertemplate="<b>%{y}</b><br>Pessoas: %{x}<extra></extra>"
    )

    fig_pessoas.update_layout(
        height=430,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Pessoas",
        yaxis_title="",
        showlegend=False,
        margin=dict(l=10, r=50, t=20, b=20),
        font=dict(size=13)
    )

    fig_pessoas.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.2)")
    fig_pessoas.update_yaxes(showgrid=False)

    st.plotly_chart(fig_pessoas, use_container_width=True, config=grafico_config)

st.divider()

st.subheader("📅 Reservas por dia e quarto")

reservas_dia_quarto = (
    df_filtrado.groupby(["Check-in", "Tipo"])
    .size()
    .reset_index(name="Reservas")
)

fig_reservas_dia = px.bar(
    reservas_dia_quarto,
    x="Check-in",
    y="Reservas",
    color="Tipo",
    text="Reservas",
    barmode="stack",
    color_discrete_map=CORES_QUARTOS
)

fig_reservas_dia.update_traces(
    textposition="inside",
    textfont_size=13,
    marker_line_width=0,
    hovertemplate="<b>%{fullData.name}</b><br>Data: %{x|%d/%m/%Y}<br>Reservas: %{y}<extra></extra>"
)

fig_reservas_dia.update_layout(
    height=500,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis_title="Data",
    yaxis_title="Reservas",
    legend_title="Tipo de quarto",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5
    ),
    bargap=0.25,
    margin=dict(l=20, r=20, t=60, b=40),
    font=dict(size=13)
)

fig_reservas_dia.update_xaxes(
    tickformat="%d/%m",
    tickangle=-45,
    showgrid=False
)

fig_reservas_dia.update_yaxes(
    showgrid=True,
    gridcolor="rgba(128,128,128,0.2)"
)

st.plotly_chart(fig_reservas_dia, use_container_width=True, config=grafico_config)

st.subheader("👥 Pessoas por dia e quarto")

pessoas_dia_quarto = (
    df_filtrado.groupby(["Check-in", "Tipo"])["Pessoas"]
    .sum()
    .reset_index()
)

fig_pessoas_dia = px.bar(
    pessoas_dia_quarto,
    x="Check-in",
    y="Pessoas",
    color="Tipo",
    text="Pessoas",
    barmode="stack",
    color_discrete_map=CORES_QUARTOS
)

fig_pessoas_dia.update_traces(
    textposition="inside",
    textfont_size=13,
    marker_line_width=0,
    hovertemplate="<b>%{fullData.name}</b><br>Data: %{x|%d/%m/%Y}<br>Pessoas: %{y}<extra></extra>"
)

fig_pessoas_dia.update_layout(
    height=500,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis_title="Data",
    yaxis_title="Pessoas",
    legend_title="Tipo de quarto",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5
    ),
    bargap=0.25,
    margin=dict(l=20, r=20, t=60, b=40),
    font=dict(size=13)
)

fig_pessoas_dia.update_xaxes(
    tickformat="%d/%m",
    tickangle=-45,
    showgrid=False
)

fig_pessoas_dia.update_yaxes(
    showgrid=True,
    gridcolor="rgba(128,128,128,0.2)"
)

st.plotly_chart(fig_pessoas_dia, use_container_width=True, config=grafico_config)
    fig_reservas.update_traces(
        textposition="outside",
        textfont_size=15,
        marker_line_width=0,
        hovertemplate="<b>%{y}</b><br>Reservas: %{x}<extra></extra>"
    )

    fig_reservas.update_layout(
        height=430,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Reservas",
        yaxis_title="",
        showlegend=False,
        margin=dict(l=10, r=50, t=20, b=20),
        font=dict(size=13)
    )

    fig_reservas.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.2)")
    fig_reservas.update_yaxes(showgrid=False)

    st.plotly_chart(fig_reservas, use_container_width=True, config=grafico_config)

with col_graf2:
    st.subheader("👥 Pessoas por quarto")

    pessoas_por_quarto = (
        df_filtrado.groupby("Tipo")["Pessoas"]
        .sum()
        .reset_index()
        .sort_values("Pessoas", ascending=True)
    )

    fig_pessoas = px.bar(
        pessoas_por_quarto,
        x="Pessoas",
        y="Tipo",
        color="Tipo",
        text="Pessoas",
        orientation="h",
        color_discrete_map=CORES_QUARTOS
    )

    fig_pessoas.update_traces(
        textposition="outside",
        textfont_size=15,
        marker_line_width=0,
        hovertemplate="<b>%{y}</b><br>Pessoas: %{x}<extra></extra>"
    )

    fig_pessoas.update_layout(
        height=430,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Pessoas",
        yaxis_title="",
        showlegend=False,
        margin=dict(l=10, r=50, t=20, b=20),
        font=dict(size=13)
    )

    fig_pessoas.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.2)")
    fig_pessoas.update_yaxes(showgrid=False)

    st.plotly_chart(fig_pessoas, use_container_width=True, config=grafico_config)

st.divider()

st.subheader("📅 Reservas por dia e quarto")

reservas_dia_quarto = (
    df_filtrado.groupby(["Check-in", "Tipo"])
    .size()
    .reset_index(name="Reservas")
)

fig_reservas_dia = px.bar(
    reservas_dia_quarto,
    x="Check-in",
    y="Reservas",
    color="Tipo",
    text="Reservas",
    barmode="stack",
    color_discrete_map=CORES_QUARTOS
)

fig_reservas_dia.update_traces(
    textposition="inside",
    textfont_size=13,
    marker_line_width=0,
    hovertemplate="<b>%{fullData.name}</b><br>Data: %{x|%d/%m/%Y}<br>Reservas: %{y}<extra></extra>"
)

fig_reservas_dia.update_layout(
    height=500,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis_title="Data",
    yaxis_title="Reservas",
    legend_title="Tipo de quarto",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5
    ),
    bargap=0.25,
    margin=dict(l=20, r=20, t=60, b=40),
    font=dict(size=13)
)

fig_reservas_dia.update_xaxes(
    tickformat="%d/%m",
    tickangle=-45,
    showgrid=False
)

fig_reservas_dia.update_yaxes(
    showgrid=True,
    gridcolor="rgba(128,128,128,0.2)"
)

st.plotly_chart(fig_reservas_dia, use_container_width=True, config=grafico_config)

st.subheader("👥 Pessoas por dia e quarto")

pessoas_dia_quarto = (
    df_filtrado.groupby(["Check-in", "Tipo"])["Pessoas"]
    .sum()
    .reset_index()
)

fig_pessoas_dia = px.bar(
    pessoas_dia_quarto,
    x="Check-in",
    y="Pessoas",
    color="Tipo",
    text="Pessoas",
    barmode="stack",
    color_discrete_map=CORES_QUARTOS
)

fig_pessoas_dia.update_traces(
    textposition="inside",
    textfont_size=13,
    marker_line_width=0,
    hovertemplate="<b>%{fullData.name}</b><br>Data: %{x|%d/%m/%Y}<br>Pessoas: %{y}<extra></extra>"
)

fig_pessoas_dia.update_layout(
    height=500,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis_title="Data",
    yaxis_title="Pessoas",
    legend_title="Tipo de quarto",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5
    ),
    bargap=0.25,
    margin=dict(l=20, r=20, t=60, b=40),
    font=dict(size=13)
)

fig_pessoas_dia.update_xaxes(
    tickformat="%d/%m",
    tickangle=-45,
    showgrid=False
)

fig_pessoas_dia.update_yaxes(
    showgrid=True,
    gridcolor="rgba(128,128,128,0.2)"
)

st.plotly_chart(fig_pessoas_dia, use_container_width=True, config=grafico_config)

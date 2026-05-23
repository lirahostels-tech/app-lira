import streamlit as st
import pandas as pd
import gspread
import plotly.express as px
from google.oauth2.service_account import Credentials
from datetime import date
import re
import unicodedata

st.set_page_config(page_title="Lira Hostel", layout="wide")

SHEET_ID = "1IOD0Seqmwk9cqtuQeLxBJnYmWGa3Q9gqbrziV-Rd0_M"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

TIPOS_ACOMODACAO = [
    "Quarto com ventilador + Banheiro Compartilhado",
    "Quarto com Ar-condicionado + Banheiro Privativo",
    "Quarto Compartilhado Masculino",
    "Quarto Compartilhado Feminino",
    "Quarto Família",
]


def normalizar_texto(texto):
    texto = str(texto).strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.lower()


def tela_login():
    st.title("🔐 Login — Lira Hostel")

    usuario_correto = st.secrets["auth"]["usuario"]
    senha_correta = st.secrets["auth"]["senha"]

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar", use_container_width=True):
        if usuario == usuario_correto and senha == senha_correta:
            st.session_state["logado"] = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")


def conectar_planilha():
    creds = Credentials.from_service_account_info(
        st.secrets["google"],
        scopes=SCOPES
    )

    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    return sheet.sheet1


def padronizar_colunas(df):
    mapa = {}

    for col in df.columns:
        col_norm = normalizar_texto(col)

        if col_norm == "data":
            mapa[col] = "Data"
        elif col_norm == "tipo":
            mapa[col] = "Tipo"
        elif "hosp" in col_norm:
            mapa[col] = "Hóspede"
        elif "pessoa" in col_norm:
            mapa[col] = "Pessoas"
        elif "observ" in col_norm:
            mapa[col] = "Observações"

    return df.rename(columns=mapa)


def extrair_diarias(texto):
    if pd.isna(texto):
        return 1

    texto = str(texto).lower()
    busca = re.search(r"(\d+)\s*di[áa]ria", texto)

    if busca:
        return int(busca.group(1))

    return 1


def carregar_dados(worksheet):
    dados = worksheet.get_all_records()
    df = pd.DataFrame(dados)

    if df.empty:
        return df

    df = padronizar_colunas(df)

    colunas_obrigatorias = ["Data", "Tipo", "Hóspede", "Pessoas", "Observações"]

    for coluna in colunas_obrigatorias:
        if coluna not in df.columns:
            st.error(f"A coluna obrigatória '{coluna}' não foi encontrada na planilha.")
            st.stop()

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)
    df["Pessoas"] = pd.to_numeric(df["Pessoas"], errors="coerce").fillna(0).astype(int)
    df["Observações"] = df["Observações"].fillna("")

    df["Diárias"] = df["Observações"].apply(extrair_diarias)
    df["Check-in"] = df["Data"]
    df["Check-out"] = df["Data"] + pd.to_timedelta(df["Diárias"], unit="D")

    return df


def reorganizar_planilha_por_data(worksheet):
    dados = worksheet.get_all_records()
    df_temp = pd.DataFrame(dados)

    if df_temp.empty:
        return

    df_temp = padronizar_colunas(df_temp)

    df_temp["Data_Ordenacao"] = pd.to_datetime(
        df_temp["Data"],
        errors="coerce",
        dayfirst=True
    )

    df_temp = df_temp.sort_values(
        by=["Data_Ordenacao", "Tipo", "Hóspede"],
        ascending=True
    )

    df_temp["Data"] = df_temp["Data_Ordenacao"].dt.strftime("%d/%m/%Y")
    df_temp = df_temp.drop(columns=["Data_Ordenacao"])

    df_final = df_temp[["Data", "Tipo", "Hóspede", "Pessoas", "Observações"]]

    worksheet.clear()
    worksheet.append_row(["Data", "Tipo", "Hóspede", "Pessoas", "Observações"])
    worksheet.append_rows(df_final.values.tolist())


def montar_lista_reservas(df):
    df_edicao = df.copy()
    df_edicao["Linha"] = df_edicao.index + 2

    df_edicao["Reserva"] = (
        df_edicao["Linha"].astype(str)
        + " | "
        + df_edicao["Data"].dt.strftime("%d/%m/%Y")
        + " | "
        + df_edicao["Hóspede"].astype(str)
        + " | "
        + df_edicao["Tipo"].astype(str)
    )

    return df_edicao


if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    try:
        tela_login()
    except KeyError:
        st.error("Erro: o bloco [auth] não foi encontrado nos Secrets do Streamlit.")
    st.stop()


st.sidebar.title("🏨 Lira Hostel")

if st.sidebar.button("Sair", use_container_width=True):
    st.session_state["logado"] = False
    st.rerun()


try:
    worksheet = conectar_planilha()
    df = carregar_dados(worksheet)
except KeyError:
    st.error("Erro: o bloco [google] não foi encontrado nos Secrets do Streamlit.")
    st.stop()
except Exception as e:
    st.error(f"Erro ao conectar com a planilha: {e}")
    st.stop()


st.title("🏨 Dashboard de Ocupação — Lira Hostel")

aba_dashboard, aba_gerenciar = st.tabs([
    "📊 Dashboard",
    "📝 Gerenciar reservas"
])


with aba_gerenciar:
    aba_adicionar, aba_editar, aba_apagar = st.tabs([
        "➕ Adicionar",
        "✏️ Alterar",
        "🗑️ Apagar"
    ])

    with aba_adicionar:
        st.subheader("Adicionar nova reserva")

        with st.form("form_adicionar"):
            col1, col2 = st.columns(2)

            with col1:
                data_reserva = st.date_input("Data do Check-in", value=date.today())
                hospede = st.text_input("Nome do hóspede")
                pessoas = st.number_input("Quantidade de pessoas", min_value=1, step=1)

            with col2:
                tipo = st.selectbox("Tipo de acomodação", TIPOS_ACOMODACAO)
                diarias = st.number_input("Quantidade de diárias", min_value=1, step=1)
                origem = st.selectbox(
                    "Origem da reserva",
                    ["Booking", "WhatsApp", "Instagram", "Direto", "Outro"]
                )

            observacoes_extra = st.text_area("Observações extras")

            enviar = st.form_submit_button("Adicionar reserva", use_container_width=True)

            if enviar:
                if not hospede.strip():
                    st.error("Preencha o nome do hóspede.")
                else:
                    observacoes = f"{origem} | {diarias} Diárias"

                    if observacoes_extra.strip():
                        observacoes += f" | {observacoes_extra.strip()}"

                    nova_linha = [
                        data_reserva.strftime("%d/%m/%Y"),
                        tipo,
                        hospede.strip(),
                        int(pessoas),
                        observacoes
                    ]

                    worksheet.append_row(nova_linha)
                    reorganizar_planilha_por_data(worksheet)

                    st.success("Reserva adicionada e organizada por data com sucesso!")
                    st.rerun()

    if not df.empty:
        df_edicao = montar_lista_reservas(df)

        with aba_editar:
            st.subheader("Alterar reserva")

            reserva_selecionada = st.selectbox(
                "Selecione a reserva para alterar",
                df_edicao["Reserva"].tolist(),
                key="editar_reserva"
            )

            linha_planilha = int(reserva_selecionada.split(" | ")[0])
            reserva_atual = df_edicao[df_edicao["Linha"] == linha_planilha].iloc[0]

            with st.form("form_editar"):
                col1, col2 = st.columns(2)

                with col1:
                    nova_data = st.date_input(
                        "Nova data do Check-in",
                        value=reserva_atual["Data"].date()
                    )

                    novo_hospede = st.text_input(
                        "Nome do hóspede",
                        value=str(reserva_atual["Hóspede"])
                    )

                    novas_pessoas = st.number_input(
                        "Quantidade de pessoas",
                        min_value=1,
                        step=1,
                        value=int(reserva_atual["Pessoas"])
                    )

                with col2:
                    index_tipo = (
                        TIPOS_ACOMODACAO.index(reserva_atual["Tipo"])
                        if reserva_atual["Tipo"] in TIPOS_ACOMODACAO
                        else 0
                    )

                    novo_tipo = st.selectbox(
                        "Tipo de acomodação",
                        TIPOS_ACOMODACAO,
                        index=index_tipo
                    )

                    novas_diarias = st.number_input(
                        "Quantidade de diárias",
                        min_value=1,
                        step=1,
                        value=int(reserva_atual["Diárias"])
                    )

                nova_observacao = st.text_area(
                    "Observações",
                    value=str(reserva_atual["Observações"])
                )

                salvar = st.form_submit_button("Salvar alteração", use_container_width=True)

                if salvar:
                    if not novo_hospede.strip():
                        st.error("Preencha o nome do hóspede.")
                    else:
                        if not re.search(r"(\d+)\s*di[áa]ria", nova_observacao.lower()):
                            nova_observacao = f"{nova_observacao.strip()} | {novas_diarias} Diárias"

                        worksheet.update(
                            f"A{linha_planilha}:E{linha_planilha}",
                            [[
                                nova_data.strftime("%d/%m/%Y"),
                                novo_tipo,
                                novo_hospede.strip(),
                                int(novas_pessoas),
                                nova_observacao.strip()
                            ]]
                        )

                        reorganizar_planilha_por_data(worksheet)

                        st.success("Reserva alterada e reorganizada por data com sucesso!")
                        st.rerun()

        with aba_apagar:
            st.subheader("Apagar reserva")

            reserva_para_apagar = st.selectbox(
                "Selecione a reserva para apagar",
                df_edicao["Reserva"].tolist(),
                key="apagar_reserva"
            )

            linha_apagar = int(reserva_para_apagar.split(" | ")[0])

            st.warning("Essa ação irá apagar a reserva da planilha.")

            confirmar = st.checkbox("Confirmo que quero apagar esta reserva")

            if st.button("Apagar reserva", use_container_width=True):
                if confirmar:
                    worksheet.delete_rows(linha_apagar)
                    reorganizar_planilha_por_data(worksheet)

                    st.success("Reserva apagada com sucesso!")
                    st.rerun()
                else:
                    st.error("Marque a confirmação antes de apagar.")
    else:
        with aba_editar:
            st.warning("Não há reservas para alterar.")
        with aba_apagar:
            st.warning("Não há reservas para apagar.")


with aba_dashboard:
    if df.empty:
        st.warning("Ainda não existem reservas cadastradas.")
        st.stop()

    st.sidebar.subheader("🔎 Filtros do Dashboard")

    data_min = df["Check-in"].min().date()
    data_max = df["Check-in"].max().date()

    periodo = st.sidebar.date_input(
        "Filtrar por período",
        value=(data_min, data_max),
        min_value=data_min,
        max_value=data_max
    )

    tipos_disponiveis = sorted(df["Tipo"].dropna().unique())

    tipos_selecionados = st.sidebar.multiselect(
        "Filtrar por quarto",
        tipos_disponiveis,
        default=tipos_disponiveis
    )

    df_filtrado = df.copy()

    if len(periodo) == 2:
        data_inicio, data_fim = periodo

        df_filtrado = df_filtrado[
            (df_filtrado["Check-in"].dt.date >= data_inicio) &
            (df_filtrado["Check-in"].dt.date <= data_fim)
        ]

    df_filtrado = df_filtrado[
        df_filtrado["Tipo"].isin(tipos_selecionados)
    ]

    if df_filtrado.empty:
        st.warning("Nenhuma reserva encontrada para os filtros selecionados.")
        st.stop()

    total_reservas = len(df_filtrado)
    total_pessoas = int(df_filtrado["Pessoas"].sum())
    total_diarias = int(df_filtrado["Diárias"].sum())

    quarto_mais_demandado = (
        df_filtrado.groupby("Tipo")["Pessoas"]
        .sum()
        .sort_values(ascending=False)
        .index[0]
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total de Reservas", total_reservas)
    col2.metric("Total de Pessoas", total_pessoas)
    col3.metric("Total de Diárias", total_diarias)
    col4.metric("Quarto com Mais Demanda", quarto_mais_demandado)

    st.divider()

    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        st.subheader("🛏️ Reservas por quarto")

        reservas_por_quarto = (
            df_filtrado.groupby("Tipo")
            .size()
            .reset_index(name="Reservas")
            .sort_values("Reservas", ascending=False)
        )

        fig_reservas = px.bar(
            reservas_por_quarto,
            x="Tipo",
            y="Reservas",
            color="Tipo",
            text="Reservas"
        )

        fig_reservas.update_layout(
            xaxis_title="Quarto",
            yaxis_title="Reservas",
            showlegend=False
        )

        st.plotly_chart(fig_reservas, use_container_width=True)

    with col_graf2:
        st.subheader("👥 Pessoas por quarto")

        pessoas_por_quarto = (
            df_filtrado.groupby("Tipo")["Pessoas"]
            .sum()
            .reset_index()
            .sort_values("Pessoas", ascending=False)
        )

        fig_pessoas = px.bar(
            pessoas_por_quarto,
            x="Tipo",
            y="Pessoas",
            color="Tipo",
            text="Pessoas"
        )

        fig_pessoas.update_layout(
            xaxis_title="Quarto",
            yaxis_title="Pessoas",
            showlegend=False
        )

        st.plotly_chart(fig_pessoas, use_container_width=True)

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
        barmode="group"
    )

    fig_reservas_dia.update_layout(
        xaxis_title="Data",
        yaxis_title="Reservas",
        legend_title="Quarto"
    )

    st.plotly_chart(fig_reservas_dia, use_container_width=True)

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
        barmode="group"
    )

    fig_pessoas_dia.update_layout(
        xaxis_title="Data",
        yaxis_title="Pessoas",
        legend_title="Quarto"
    )

    st.plotly_chart(fig_pessoas_dia, use_container_width=True)

    st.divider()

    st.subheader("📋 Reservas filtradas")

    df_visual = df_filtrado.copy()
    df_visual["Data"] = df_visual["Data"].dt.strftime("%d/%m/%Y")
    df_visual["Check-in"] = df_visual["Check-in"].dt.strftime("%d/%m/%Y")
    df_visual["Check-out"] = df_visual["Check-out"].dt.strftime("%d/%m/%Y")

    st.dataframe(df_visual, use_container_width=True)

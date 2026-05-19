import streamlit as st
import pandas as pd
import gspread
import plotly.express as px
from google.oauth2.service_account import Credentials
from datetime import date
import re
import unicodedata

st.set_page_config(page_title="Lira Hostel", layout="wide")

USUARIO_CORRETO = st.secrets["auth"]["usuario"]
SENHA_CORRETA = st.secrets["auth"]["senha"]

SHEET_ID = "1IOD0Seqmwk9cqtuQeLxBJnYmWGa3Q9gqbrziV-Rd0_M"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

TIPOS_ACOMODACAO = [
    "Quarto com ventilador + Banheiro Compartilhado",
    "Quarto com Ar-condicionado + Banheiro Privativo",
    "Quarto Compartilhado",
    "Quarto Família",
    "Quarto Solteiro"
]


def normalizar_nome_coluna(nome):
    nome = str(nome).strip()
    nome = unicodedata.normalize("NFKD", nome)
    nome = "".join([c for c in nome if not unicodedata.combining(c)])
    return nome.lower()


def tela_login():
    st.title("🔐 Login — Lira Hostel")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar", use_container_width=True):
        if usuario == USUARIO_CORRETO and senha == SENHA_CORRETA:
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
        col_norm = normalizar_nome_coluna(col)

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

    df = df.rename(columns=mapa)
    return df


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

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)
    df["Pessoas"] = pd.to_numeric(df["Pessoas"], errors="coerce").fillna(0).astype(int)

    df["Diárias"] = df["Observações"].apply(extrair_diarias)
    df["Check-in"] = df["Data"]
    df["Check-out"] = df["Data"] + pd.to_timedelta(df["Diárias"], unit="D")

    return df


def reorganizar_planilha_por_data(worksheet):
    dados = worksheet.get_all_records()
    df = pd.DataFrame(dados)

    if df.empty:
        return

    df = padronizar_colunas(df)
    df["Data_temp"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)
    df = df.sort_values(by=["Data_temp", "Tipo", "Hóspede"])
    df = df.drop(columns=["Data_temp"])

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True).dt.strftime("%d/%m/%Y")

    worksheet.clear()
    worksheet.append_row(["Data", "Tipo", "Hóspede", "Pessoas", "Observações"])
    worksheet.append_rows(df[["Data", "Tipo", "Hóspede", "Pessoas", "Observações"]].values.tolist())


if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    tela_login()
    st.stop()


st.sidebar.title("Lira Hostel")

if st.sidebar.button("Sair", use_container_width=True):
    st.session_state["logado"] = False
    st.rerun()


st.title("🏨 Dashboard de Ocupação — Lira Hostel")

try:
    worksheet = conectar_planilha()
    df = carregar_dados(worksheet)
except KeyError:
    st.error("Erro: o bloco [google] não foi encontrado nos Secrets do Streamlit.")
    st.stop()
except Exception as e:
    st.error(f"Erro ao conectar com a planilha: {e}")
    st.stop()


aba_adicionar, aba_editar, aba_apagar = st.tabs([
    "➕ Adicionar reserva",
    "✏️ Alterar reserva",
    "🗑️ Apagar reserva"
])


with aba_adicionar:
    st.subheader("Adicionar nova reserva")

    with st.form("form_adicionar"):
        col1, col2 = st.columns(2)

        with col1:
            data = st.date_input("Data do Check-in", value=date.today())
            hospede = st.text_input("Nome do hóspede")
            pessoas = st.number_input("Quantidade de pessoas", min_value=1, step=1)

        with col2:
            tipo = st.selectbox("Tipo de acomodação", TIPOS_ACOMODACAO)
            diarias = st.number_input("Quantidade de diárias", min_value=1, step=1)
            origem = st.selectbox("Origem da reserva", ["Booking", "WhatsApp", "Instagram", "Direto", "Outro"])

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
                    data.strftime("%d/%m/%Y"),
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


st.divider()

if df.empty:
    st.warning("Ainda não existem reservas cadastradas.")
    st.stop()


total_reservas = len(df)
total_pessoas = int(df["Pessoas"].sum())
total_diarias = int(df["Diárias"].sum())

col1, col2, col3 = st.columns(3)

col1.metric("Total de Reservas", total_reservas)
col2.metric("Quantidade de Pessoas", total_pessoas)
col3.metric("Total de Diárias", total_diarias)

st.divider()


st.subheader("📊 Demanda por quarto em cada dia")

demanda_dia_tipo = (
    df.groupby(["Check-in", "Tipo"])
    .agg(
        Reservas=("Tipo", "count"),
        Pessoas=("Pessoas", "sum")
    )
    .reset_index()
)

fig_demanda = px.bar(
    demanda_dia_tipo,
    x="Check-in",
    y="Reservas",
    color="Tipo",
    barmode="group",
    text="Reservas",
    title="Reservas por quarto em cada dia"
)

fig_demanda.update_layout(
    xaxis_title="Data de Check-in",
    yaxis_title="Quantidade de reservas",
    legend_title="Tipo de quarto"
)

st.plotly_chart(fig_demanda, use_container_width=True)


st.subheader("👥 Quantidade de pessoas por tipo de quarto")

pessoas_tipo = (
    df.groupby("Tipo")["Pessoas"]
    .sum()
    .reset_index()
    .sort_values("Pessoas", ascending=False)
)

fig_pessoas = px.bar(
    pessoas_tipo,
    x="Tipo",
    y="Pessoas",
    color="Tipo",
    text="Pessoas",
    title="Demanda total por tipo de quarto"
)

fig_pessoas.update_layout(
    xaxis_title="Tipo de quarto",
    yaxis_title="Quantidade de pessoas",
    showlegend=False
)

st.plotly_chart(fig_pessoas, use_container_width=True)


st.divider()

st.subheader("📋 Reservas")

df_visual = df.copy()
df_visual["Data"] = df_visual["Data"].dt.strftime("%d/%m/%Y")
df_visual["Check-in"] = df_visual["Check-in"].dt.strftime("%d/%m/%Y")
df_visual["Check-out"] = df_visual["Check-out"].dt.strftime("%d/%m/%Y")

st.dataframe(df_visual, use_container_width=True)

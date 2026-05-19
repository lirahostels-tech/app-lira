import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import date
import re

st.set_page_config(page_title="Lira Hostel", layout="wide")

USUARIO_CORRETO = "admin"
SENHA_CORRETA = "1234"

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
    "Quarto Solteiro"
]


def tela_login():
    st.title("🔐 Login — Lira Hostel")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
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

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)
    df["Pessoas"] = pd.to_numeric(df["Pessoas"], errors="coerce").fillna(0)

    df["Diárias"] = df["Observações"].apply(extrair_diarias)
    df["Check-in"] = df["Data"]
    df["Check-out"] = df["Data"] + pd.to_timedelta(df["Diárias"], unit="D")

    return df


if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    tela_login()
    st.stop()


st.sidebar.title("Lira Hostel")

if st.sidebar.button("Sair"):
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


st.subheader("➕ Adicionar nova reserva")

with st.form("form_reserva"):
    data = st.date_input("Data do Check-in", value=date.today())

    tipo = st.selectbox("Tipo de acomodação", TIPOS_ACOMODACAO)

    hospede = st.text_input("Nome do hóspede")
    pessoas = st.number_input("Quantidade de pessoas", min_value=1, step=1)
    diarias = st.number_input("Quantidade de diárias", min_value=1, step=1)

    origem = st.selectbox(
        "Origem da reserva",
        ["Booking", "WhatsApp", "Instagram", "Direto", "Outro"]
    )

    observacoes_extra = st.text_area("Observações extras")

    enviar = st.form_submit_button("Adicionar reserva")

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

            st.success("Reserva adicionada com sucesso!")
            st.rerun()


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


reservas_por_data = df.groupby("Check-in").size().reset_index(name="Reservas")

st.subheader("📅 Quantidade de Reservas por Check-in")
st.bar_chart(
    reservas_por_data,
    x="Check-in",
    y="Reservas",
    use_container_width=True
)

ocupacao_por_tipo = df.groupby("Tipo")["Pessoas"].sum().reset_index()

st.subheader("🛏️ Ocupação por Tipo de Acomodação")
st.bar_chart(
    ocupacao_por_tipo,
    x="Tipo",
    y="Pessoas",
    use_container_width=True
)

st.divider()


st.subheader("📋 Reservas")

df_visual = df.copy()
df_visual["Data"] = df_visual["Data"].dt.strftime("%d/%m/%Y")
df_visual["Check-in"] = df_visual["Check-in"].dt.strftime("%d/%m/%Y")
df_visual["Check-out"] = df_visual["Check-out"].dt.strftime("%d/%m/%Y")

st.dataframe(df_visual, use_container_width=True)


st.divider()

st.subheader("✏️ Editar ou apagar reserva")

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

reserva_selecionada = st.selectbox(
    "Selecione a reserva",
    df_edicao["Reserva"].tolist()
)

linha_planilha = int(reserva_selecionada.split(" | ")[0])

reserva_atual = df_edicao[df_edicao["Linha"] == linha_planilha].iloc[0]

acao = st.radio(
    "O que deseja fazer?",
    ["Editar reserva", "Apagar reserva"],
    horizontal=True
)

if acao == "Editar reserva":
    with st.form("form_editar_reserva"):
        nova_data = st.date_input(
            "Nova data do Check-in",
            value=reserva_atual["Data"].date()
        )

        index_tipo = (
            TIPOS_ACOMODACAO.index(reserva_atual["Tipo"])
            if reserva_atual["Tipo"] in TIPOS_ACOMODACAO
            else 0
        )

        novo_tipo = st.selectbox(
            "Novo tipo de acomodação",
            TIPOS_ACOMODACAO,
            index=index_tipo
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

        salvar_edicao = st.form_submit_button("Salvar alterações")

        if salvar_edicao:
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

                st.success("Reserva editada com sucesso!")
                st.rerun()


if acao == "Apagar reserva":
    st.warning("Essa ação irá apagar a reserva da planilha.")

    confirmar = st.checkbox("Confirmo que quero apagar esta reserva")

    if st.button("Apagar reserva"):
        if confirmar:
            worksheet.delete_rows(linha_planilha)
            st.success("Reserva apagada com sucesso!")
            st.rerun()
        else:
            st.error("Marque a confirmação antes de apagar.")

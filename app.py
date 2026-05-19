import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import date
import re


USUARIO_CORRETO = "admin"
SENHA_CORRETA = "1234"

def tela_login():
    st.title("🔐 Login — Lira Hostel")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    entrar = st.button("Entrar")

    if entrar:
        if usuario == USUARIO_CORRETO and senha == SENHA_CORRETA:
            st.session_state["logado"] = True
            st.success("Login realizado com sucesso!")
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")

if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    tela_login()
    st.stop()

st.set_page_config(page_title="Lira Hostel", layout="wide")

st.title("🏨 Dashboard de Ocupação — Lira Hostel")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["google"],
    scopes=SCOPES
)

client = gspread.authorize(creds)

SHEET_ID = "1IOD0Seqmwk9cqtuQeLxBJnYmWGa3Q9gqbrziV-Rd0_M"

sheet = client.open_by_key(SHEET_ID)
worksheet = sheet.sheet1

dados = worksheet.get_all_records()
df = pd.DataFrame(dados)

# Tratamento dos dados
df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)
df["Pessoas"] = pd.to_numeric(df["Pessoas"], errors="coerce").fillna(0)

def extrair_diarias(texto):
    if pd.isna(texto):
        return 1

    texto = str(texto).lower()
    busca = re.search(r"(\d+)\s*di[áa]ria", texto)

    if busca:
        return int(busca.group(1))

    return 1

df["Diárias"] = df["Observações"].apply(extrair_diarias)
df["Check-in"] = df["Data"]
df["Check-out"] = df["Data"] + pd.to_timedelta(df["Diárias"], unit="D")

# Formulário para adicionar reserva
st.subheader("➕ Adicionar nova reserva")

with st.form("form_reserva"):
    data = st.date_input("Data do Check-in", value=date.today())

    tipo = st.selectbox(
        "Tipo de acomodação",
        [
            "Quarto com ventilador + Banheiro Compartilhado",
            "Quarto com Ar-condicionado + Banheiro Privativo",
            "Quarto Compartilhado",
            "Quarto Família",
            "Quarto Solteiro"
        ]
    )

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
        if not hospede:
            st.error("Preencha o nome do hóspede.")
        else:
            observacoes = f"{origem} | {diarias} Diárias"

            if observacoes_extra:
                observacoes += f" | {observacoes_extra}"

            nova_linha = [
                data.strftime("%d/%m/%Y"),
                tipo,
                hospede,
                int(pessoas),
                observacoes
            ]

            worksheet.append_row(nova_linha)

            st.success("Reserva adicionada com sucesso!")
            st.rerun()

st.divider()

# Métricas
total_reservas = len(df)
total_pessoas = int(df["Pessoas"].sum())
total_diarias = int(df["Diárias"].sum())

col1, col2, col3 = st.columns(3)

col1.metric("Total de Reservas", total_reservas)
col2.metric("Quantidade de Pessoas", total_pessoas)
col3.metric("Total de Diárias", total_diarias)

st.divider()

# Gráficos
reservas_por_data = df.groupby("Check-in").size().reset_index(name="Reservas")

st.subheader("📅 Quantidade de Reservas por Check-in")
st.bar_chart(reservas_por_data, x="Check-in", y="Reservas", use_container_width=True)

ocupacao_por_tipo = df.groupby("Tipo")["Pessoas"].sum().reset_index()

st.subheader("🛏️ Ocupação por Tipo de Acomodação")
st.bar_chart(ocupacao_por_tipo, x="Tipo", y="Pessoas", use_container_width=True)

st.divider()

# Tabela
st.subheader("📋 Reservas")

df_visual = df.copy()
df_visual["Data"] = df_visual["Data"].dt.strftime("%d/%m/%Y")
df_visual["Check-in"] = df_visual["Check-in"].dt.strftime("%d/%m/%Y")
df_visual["Check-out"] = df_visual["Check-out"].dt.strftime("%d/%m/%Y")

st.dataframe(df_visual, use_container_width=True)

# Botão de sair

st.sidebar.divider()

if st.sidebar.button("Sair"):
    st.session_state["logado"] = False
    st.rerun()
import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------
# CONFIGURAÇÃO
# -----------------------------------------------------------
st.set_page_config(layout="wide", page_title="Monitoramento Ergonômico")

st.title("🧍‍♂️ Monitoramento Ergonômico")

# -----------------------------------------------------------
# CARREGAR DADOS
# -----------------------------------------------------------
@st.cache_data(ttl=60)
def load_data():
    sheet_id = "1du_b9wsAlgvhrjyY0ts9x3Js_4FWDbWujRvi6PKMGEQ"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    return pd.read_csv(url)

df = load_data()

if df.empty:
    st.warning("Sem dados")
    st.stop()

# -----------------------------------------------------------
# IDENTIFICAR COLUNAS
# -----------------------------------------------------------
colunas = df.columns

col_setor = next((c for c in colunas if "setor" in c.lower()), None)
col_data = next((c for c in colunas if "data" in c.lower()), None)
col_dor_flag = next((c for c in colunas if "sentindo alguma dor" in c.lower()), None)
col_local_dor = next((c for c in colunas if "local da dor" in c.lower()), None)
col_lider = next((c for c in colunas if "liderança" in c.lower()), None)

# -----------------------------------------------------------
# LIMPEZA BASE
# -----------------------------------------------------------
df = df.copy()

# limpar textos
for col in [col_setor, col_dor_flag, col_local_dor, col_lider]:
    if col:
        df[col] = df[col].astype(str).str.strip()

# datas
if col_data:
    df[col_data] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce')
    df["MesAno"] = df[col_data].dt.to_period("M").astype(str)

# -----------------------------------------------------------
# FILTROS
# -----------------------------------------------------------
c1, c2, c3 = st.columns(3)

with c1:
    meses = sorted(df["MesAno"].dropna().unique(), reverse=True)
    mes_sel = st.selectbox("Mês", ["Todos"] + list(meses))

with c2:
    setores = sorted(df[col_setor].dropna().unique()) if col_setor else []
    setor_sel = st.selectbox("Setor", ["Todos"] + list(setores))

with c3:
    lideres = sorted(df[col_lider].dropna().unique()) if col_lider else []
    lider_sel = st.multiselect("Liderança", lideres)

# aplicar filtros
df_f = df.copy()

if mes_sel != "Todos":
    df_f = df_f[df_f["MesAno"] == mes_sel]

if setor_sel != "Todos" and col_setor:
    df_f = df_f[df_f[col_setor] == setor_sel]

if lider_sel and col_lider:
    df_f = df_f[df_f[col_lider].isin(lider_sel)]

# -----------------------------------------------------------
# 🔥 FILTRO PRINCIPAL (SÓ QUEM TEM DOR)
# -----------------------------------------------------------
df_f = df_f[df_f[col_dor_flag].str.lower() == "sim"]

if df_f.empty:
    st.warning("Nenhuma pessoa com dor encontrada")
    st.stop()

# -----------------------------------------------------------
# TRATAR LOCAL DA DOR
# -----------------------------------------------------------
df_dores = (
    df_f[col_local_dor]
    .dropna()
    .str.replace("\xa0", " ")
    .str.split(",")
    .explode()
    .str.strip()
)

# remover lixo
df_dores = df_dores[~df_dores.isin(["", "nan", "None"])]

# contagem real
df_contagem = df_dores.value_counts().reset_index()
df_contagem.columns = ["Parte do Corpo", "Quantidade"]

# -----------------------------------------------------------
# LAYOUT
# -----------------------------------------------------------
col1, col2 = st.columns([0.7, 0.3])

with col1:
    st.subheader("📊 Dores por Região do Corpo")

    fig = px.bar(
        df_contagem.sort_values("Quantidade"),
        x="Quantidade",
        y="Parte do Corpo",
        orientation="h",
        text="Quantidade"
    )

    fig.update_layout(height=500)

    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📋 Resumo")

    st.metric("Total com dor", len(df_f))

    st.dataframe(df_contagem, use_container_width=True)

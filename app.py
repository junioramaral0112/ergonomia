import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

st.title("🧍‍♂️ Monitoramento Ergonômico")

# -----------------------------------------------------------
# CONFIG
# -----------------------------------------------------------
GOOGLE_SHEET_CSV = "COLE_AQUI_O_LINK_CSV_DA_SUA_PLANILHA"

# -----------------------------------------------------------
# FUNÇÃO PARA CARREGAR DADOS
# -----------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(GOOGLE_SHEET_CSV)
    return df

df = load_data()

# -----------------------------------------------------------
# IDENTIFICAR COLUNAS
# -----------------------------------------------------------
col_dor = [c for c in df.columns if "dor" in c.lower() and "sentindo" in c.lower()][0]
col_local = [c for c in df.columns if "local" in c.lower()][0]
col_setor = [c for c in df.columns if "setor" in c.lower()][0]
col_data = [c for c in df.columns if "data" in c.lower()][0]
col_lider = [c for c in df.columns if "lider" in c.lower()][0]

# -----------------------------------------------------------
# LIMPEZA DE DADOS
# -----------------------------------------------------------
df[col_dor] = df[col_dor].astype(str).str.strip().str.lower()
df[col_local] = df[col_local].astype(str).str.strip()
df[col_setor] = df[col_setor].astype(str).str.strip()
df[col_lider] = df[col_lider].astype(str).str.strip()

# -----------------------------------------------------------
# PADRONIZAÇÃO DE SETORES (CORREÇÃO CRÍTICA)
# -----------------------------------------------------------
df[col_setor] = df[col_setor].str.lower().str.strip()

mapa_setores = {
    "laminação gdr": "laminação",
    "laminacao gdr": "laminação",
    "laminacao": "laminação",
    "laminação ": "laminação",
}

df[col_setor] = df[col_setor].replace(mapa_setores)

# manter padrão visual
df[col_setor] = df[col_setor].str.title()

# -----------------------------------------------------------
# FILTRAR APENAS "SIM"
# -----------------------------------------------------------
df_dor = df[df[col_dor] == "sim"].copy()

# -----------------------------------------------------------
# TRATAR DATAS
# -----------------------------------------------------------
df[col_data] = pd.to_datetime(df[col_data], errors="coerce")
df_dor[col_data] = pd.to_datetime(df_dor[col_data], errors="coerce")

# -----------------------------------------------------------
# FILTROS
# -----------------------------------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    meses = df[col_data].dt.to_period("M").dropna().astype(str).unique()
    mes_sel = st.selectbox("Selecione o Mês", sorted(meses))

with col2:
    setores = sorted(df[col_setor].dropna().unique())
    setor_sel = st.selectbox("Selecione o Setor", setores)

with col3:
    lideres = sorted(df[col_lider].dropna().unique())
    lider_sel = st.multiselect("Selecione o(s) Líder(es)", lideres)

# aplicar filtros (somente nos que responderam SIM)
df_filtrado = df_dor.copy()

df_filtrado = df_filtrado[
    df_filtrado[col_data].dt.to_period("M").astype(str) == mes_sel
]

df_filtrado = df_filtrado[df_filtrado[col_setor] == setor_sel]

if lider_sel:
    df_filtrado = df_filtrado[df_filtrado[col_lider].isin(lider_sel)]

# -----------------------------------------------------------
# EXPLODIR LOCAIS (caso tenha múltiplos: "Perna, Coluna")
# -----------------------------------------------------------
df_filtrado[col_local] = df_filtrado[col_local].str.split(",")

df_explodido = df_filtrado.explode(col_local)

df_explodido[col_local] = df_explodido[col_local].str.strip()

# remover vazios
df_explodido = df_explodido[df_explodido[col_local] != ""]

# -----------------------------------------------------------
# CONTAGEM REAL (APENAS "SIM")
# -----------------------------------------------------------
freq = df_explodido[col_local].value_counts().reset_index()
freq.columns = ["Parte do Corpo", "Qtd"]

# -----------------------------------------------------------
# DASHBOARD
# -----------------------------------------------------------
col_grafico, col_tabela = st.columns([2, 1])

with col_grafico:
    st.subheader("📊 Frequência de Dores por Região do Corpo")
    st.bar_chart(freq.set_index("Parte do Corpo"))

with col_tabela:
    st.subheader("📋 Frequência por Local")
    st.dataframe(freq, use_container_width=True)

# -----------------------------------------------------------
# DEBUG (OPCIONAL)
# -----------------------------------------------------------
with st.expander("🔍 Diagnóstico de Dados"):
    st.write("Setores encontrados:", df[col_setor].unique())
    st.write("Valores de dor:", df[col_dor].unique())
    st.write("Total de registros SIM:", len(df_dor))

import streamlit as st
import pandas as pd
import plotly.express as px

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(layout="wide")
st.title("📊 Monitoramento Ergonômico - Dashboard Inteligente")

# =====================================================
# CARREGAMENTO
# =====================================================
@st.cache_data
def load_data():
    df = pd.read_excel("dados.xlsx")

    # Padronizar colunas
    df.columns = df.columns.str.strip()

    return df

df = load_data()

# =====================================================
# LIMPEZA INTELIGENTE (NÍVEL EMPRESA)
# =====================================================
def normalizar_parte(parte):
    if pd.isna(parte):
        return "Não informado"

    parte = str(parte).strip().lower()

    mapa = {
        "mão": "Mãos",
        "maos": "Mãos",
        "mãos": "Mãos",
        "ombro": "Ombros",
        "ombros": "Ombros",
        "braço": "Braços",
        "braços": "Braços",
        "braco": "Braços",
        "cotovelo": "Cotovelo",
        "cotovelos": "Cotovelo",
        "antebraço": "Antebraço",
        "punho": "Punho",
        "coluna": "Coluna",
        "costas": "Costas",
    }

    for key in mapa:
        if key in parte:
            return mapa[key]

    return parte.capitalize()

df["Parte Limpa"] = df["Parte"].apply(normalizar_parte)

# =====================================================
# FILTROS
# =====================================================
col1, col2, col3 = st.columns(3)

with col1:
    meses = sorted(df["Mês"].dropna().unique())
    mes = st.selectbox("Selecione o Mês", meses)

with col2:
    setores = sorted(df["Setor"].dropna().unique())
    setor = st.selectbox("Selecione o Setor", setores)

with col3:
    liderancas = sorted(df["Liderança"].dropna().unique())
    lideranca = st.multiselect("Selecione a Liderança", liderancas)

# =====================================================
# FILTRAGEM
# =====================================================
df_filtrado = df[
    (df["Mês"] == mes) &
    (df["Setor"] == setor)
]

if lideranca:
    df_filtrado = df_filtrado[df_filtrado["Liderança"].isin(lideranca)]

# =====================================================
# KPI
# =====================================================
st.subheader("📌 Indicadores")

col1, col2, col3 = st.columns(3)

col1.metric("Total de Registros", len(df_filtrado))
col2.metric("Partes Afetadas", df_filtrado["Parte Limpa"].nunique())
col3.metric("Colaboradores", df_filtrado["Matrícula"].nunique())

# =====================================================
# GRÁFICO PRINCIPAL (SUBSTITUI O MAPA)
# =====================================================
st.subheader("📊 Frequência por Parte do Corpo")

freq = df_filtrado["Parte Limpa"].value_counts().reset_index()
freq.columns = ["Parte", "Qtd"]

fig = px.bar(
    freq,
    x="Qtd",
    y="Parte",
    orientation="h",
    text="Qtd"
)

fig.update_layout(
    height=500,
    yaxis=dict(categoryorder='total ascending')
)

st.plotly_chart(fig, use_container_width=True)

# =====================================================
# TENDÊNCIA (NÍVEL EMPRESA)
# =====================================================
st.subheader("📈 Tendência ao Longo do Tempo")

tendencia = df.groupby(["Mês", "Parte Limpa"]).size().reset_index(name="Qtd")

fig2 = px.line(
    tendencia,
    x="Mês",
    y="Qtd",
    color="Parte Limpa",
    markers=True
)

st.plotly_chart(fig2, use_container_width=True)

# =====================================================
# TABELA DETALHADA
# =====================================================
st.subheader("📋 Dados Detalhados")

st.dataframe(df_filtrado, use_container_width=True)

# =====================================================
# ALERTA INTELIGENTE
# =====================================================
st.subheader("🚨 Alertas")

top = freq.head(1)

if not top.empty:
    parte_top = top.iloc[0]["Parte"]
    qtd_top = top.iloc[0]["Qtd"]

    st.warning(f"Atenção: Maior incidência em **{parte_top} ({qtd_top} casos)**")

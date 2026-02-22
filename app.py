import streamlit as st
import pandas as pd
import os
import plotly.express as px

# =====================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================
st.set_page_config(layout="wide")
st.title("📊 Monitoramento Ergonômico - Dashboard Inteligente")

# =====================================================
# LOAD DE DADOS (ROBUSTO)
# =====================================================
@st.cache_data
def load_data():
    file_path = "dados.xlsx"

    # Tenta carregar automático
    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
        st.success("📁 Dados carregados automaticamente")
        return df

    # Upload manual
    uploaded_file = st.file_uploader("📤 Envie o arquivo Excel", type=["xlsx"])

    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        st.success("✅ Arquivo carregado com sucesso")
        return df

    st.warning("⚠️ Envie um arquivo para continuar.")
    st.stop()

df = load_data()

# =====================================================
# LIMPEZA DE DADOS (PADRÃO EMPRESA)
# =====================================================
df.columns = df.columns.str.strip()

# Padroniza nomes (ajuste conforme seu Excel)
colunas_necessarias = ["Data", "Setor", "Lideranca", "Parte do Corpo"]

for col in colunas_necessarias:
    if col not in df.columns:
        st.error(f"❌ Coluna obrigatória não encontrada: {col}")
        st.stop()

# Trata datas
df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

# Remove lixo
df = df.dropna(subset=["Data"])

# Cria coluna de mês
df["Mes"] = df["Data"].dt.to_period("M").astype(str)

# Remove valores vazios importantes
df["Setor"] = df["Setor"].fillna("Não informado").str.strip()
df["Lideranca"] = df["Lideranca"].fillna("Não informado").str.strip()
df["Parte do Corpo"] = df["Parte do Corpo"].fillna("Não informado").str.strip()

# =====================================================
# FILTROS (TOPO)
# =====================================================
col1, col2, col3 = st.columns(3)

with col1:
    meses = sorted(df["Mes"].dropna().unique(), reverse=True)
    mes_sel = st.selectbox("📅 Selecione o Mês", meses)

with col2:
    setores = sorted(df["Setor"].dropna().unique())
    setor_sel = st.selectbox("🏭 Selecione o Setor", setores)

with col3:
    lideres = sorted(df["Lideranca"].dropna().unique())
    lider_sel = st.multiselect("👔 Liderança", lideres)

# =====================================================
# FILTRAGEM
# =====================================================
df_filtrado = df[df["Mes"] == mes_sel]
df_filtrado = df_filtrado[df_filtrado["Setor"] == setor_sel]

if lider_sel:
    df_filtrado = df_filtrado[df_filtrado["Lideranca"].isin(lider_sel)]

# =====================================================
# KPIs (VISÃO EMPRESA)
# =====================================================
st.divider()

k1, k2, k3 = st.columns(3)

k1.metric("Total de Registros", len(df_filtrado))
k2.metric("Colaboradores Únicos", df_filtrado["Lideranca"].nunique())
k3.metric("Setor Atual", setor_sel)

# =====================================================
# GRÁFICOS PRINCIPAIS
# =====================================================
st.divider()

col1, col2 = st.columns(2)

# 🔹 Frequência por Parte do Corpo
with col1:
    freq = (
        df_filtrado["Parte do Corpo"]
        .value_counts()
        .reset_index()
    )
    freq.columns = ["Parte do Corpo", "Quantidade"]

    fig1 = px.bar(
        freq,
        x="Quantidade",
        y="Parte do Corpo",
        orientation="h",
        title="📊 Frequência por Parte do Corpo",
        text="Quantidade"
    )

    fig1.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig1, use_container_width=True)

# 🔹 Ocorrências por Liderança
with col2:
    lider = (
        df_filtrado["Lideranca"]
        .value_counts()
        .reset_index()
    )
    lider.columns = ["Liderança", "Quantidade"]

    fig2 = px.bar(
        lider,
        x="Liderança",
        y="Quantidade",
        title="👔 Ocorrências por Liderança",
        text="Quantidade"
    )

    st.plotly_chart(fig2, use_container_width=True)

# =====================================================
# EVOLUÇÃO TEMPORAL
# =====================================================
st.divider()

evolucao = (
    df_filtrado
    .groupby("Data")
    .size()
    .reset_index(name="Quantidade")
)

fig3 = px.line(
    evolucao,
    x="Data",
    y="Quantidade",
    title="📈 Evolução das Ocorrências"
)

st.plotly_chart(fig3, use_container_width=True)

# =====================================================
# TABELA DETALHADA
# =====================================================
st.divider()

st.subheader("📋 Dados Detalhados")

st.dataframe(
    df_filtrado.sort_values(by="Data", ascending=False),
    use_container_width=True
)

# =====================================================
# EXPORTAÇÃO
# =====================================================
st.download_button(
    "⬇️ Baixar Dados Filtrados",
    df_filtrado.to_csv(index=False),
    file_name="dados_filtrados.csv"
)

import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------
# CONFIGURAÇÃO DE PÁGINA
# -----------------------------------------------------------
st.set_page_config(
    layout="wide",
    page_title="Monitoramento Ergonômico",
    initial_sidebar_state="collapsed"
)

st.title("🧍‍♂️ Monitoramento Ergonômico")

st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        [data-testid="collapsedControl"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------
# CARREGAMENTO DOS DADOS
# -----------------------------------------------------------
@st.cache_data(ttl=60)
def load_data():
    try:
        sheet_id = "1du_b9wsAlgvhrjyY0ts9x3Js_4FWDbWujRvi6PKMGEQ"
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        return pd.DataFrame()

df_original = load_data()

if df_original.empty:
    st.warning("Aguardando carregamento dos dados...")
    st.stop()

# -----------------------------------------------------------
# IDENTIFICAÇÃO DINÂMICA DE COLUNAS
# -----------------------------------------------------------
colunas = df_original.columns.tolist()

coluna_setor = next(
    (c for c in colunas if "setor" in c.lower().replace(":", "").strip()),
    None
)

coluna_data = next(
    (c for c in colunas if "carimbo" in c.lower() or "data" in c.lower()),
    None
)

coluna_dor = next(
    (c for c in colunas if "local da dor" in c.lower() or "indique o local" in c.lower()),
    None
)

coluna_lider = next(
    (c for c in colunas if "liderança" in c.lower()),
    None
)

# -----------------------------------------------------------
# LIMPEZA DOS SETORES
# -----------------------------------------------------------
if coluna_setor:
    df_original[coluna_setor] = (
        df_original[coluna_setor]
        .astype(str)
        .str.replace("\xa0", " ", regex=False)
        .str.strip()
    )

    df_original[coluna_setor] = df_original[coluna_setor].replace(
        ['nan', 'None', '', 'NaN'],
        pd.NA
    )

    df_original = df_original.dropna(subset=[coluna_setor])

    df_original[coluna_setor] = df_original[coluna_setor].str.split(",")
    df_original = df_original.explode(coluna_setor)
    df_original[coluna_setor] = df_original[coluna_setor].str.strip()

# -----------------------------------------------------------
# DATA
# -----------------------------------------------------------
if coluna_data:
    df_original[coluna_data] = pd.to_datetime(
        df_original[coluna_data],
        dayfirst=True,
        errors='coerce'
    )

    df_original = df_original.dropna(subset=[coluna_data])
    df_original["MesAno"] = df_original[coluna_data].dt.to_period("M").astype(str)

# -----------------------------------------------------------
# FILTROS
# -----------------------------------------------------------
c1, c2, c3 = st.columns(3)

with c1:
    meses = sorted(df_original["MesAno"].unique(), reverse=True) if "MesAno" in df_original.columns else []
    mes_sel = st.selectbox("Selecione o Mês:", ["Todos os Meses"] + meses)

with c2:
    setores_lista = sorted(df_original[coluna_setor].dropna().unique()) if coluna_setor else []
    setor_sel = st.selectbox("Selecione o Setor:", ["Todos os Setores"] + list(setores_lista))

with c3:
    lideres = (
        df_original[coluna_lider]
        .astype(str)
        .replace(['nan', 'None', ''], pd.NA)
        .dropna()
        .unique()
    ) if coluna_lider else []

    lider_sel = st.multiselect("Selecione a(s) Liderança(s):", sorted(lideres))

# -----------------------------------------------------------
# FILTRAGEM
# -----------------------------------------------------------
df_f = df_original.copy()

if mes_sel != "Todos os Meses":
    df_f = df_f[df_f["MesAno"] == mes_sel]

if setor_sel != "Todos os Setores" and coluna_setor:
    df_f = df_f[df_f[coluna_setor] == setor_sel]

if lider_sel and coluna_lider:
    df_f = df_f[df_f[coluna_lider].astype(str).isin(lider_sel)]

if df_f.empty:
    st.info("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()

# -----------------------------------------------------------
# CONTAGEM DAS DORES
# -----------------------------------------------------------
if coluna_dor:
    df_dores = df_f[coluna_dor].astype(str).str.get_dummies(sep=",")
    df_dores.columns = df_dores.columns.str.strip()

    df_contagem = (
        df_dores.sum()
        .reset_index()
        .rename(columns={"index": "Parte", 0: "Qtd"})
    )
else:
    st.warning("Coluna de dor não encontrada.")
    st.stop()

# -----------------------------------------------------------
# LAYOUT COM GRÁFICO + TABELA
# -----------------------------------------------------------
col1, col2 = st.columns([0.6, 0.4])

with col1:
    df_plot = df_contagem[df_contagem["Qtd"] > 0].sort_values("Qtd", ascending=True)

    fig = px.bar(
        df_plot,
        x="Qtd",
        y="Parte",
        orientation="h",
        text="Qtd",
        title="📊 Frequência de Dores por Região do Corpo"
    )

    fig.update_layout(
        height=650,
        yaxis=dict(categoryorder='total ascending')
    )

    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 Frequência por Local")

    st.dataframe(
        df_contagem.sort_values("Qtd", ascending=False),
        hide_index=True,
        use_container_width=True
    )

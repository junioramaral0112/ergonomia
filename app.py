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

# Mapeamento exato baseado na sua estrutura
col_sentindo_dor = colunas[4]  # Coluna E: "Hoje, você está sentindo..."
col_local_dor = colunas[5]     # Coluna F: "Se SIM, indique o local..."

coluna_setor = next(
    (c for c in colunas if "setor" in c.lower().replace(":", "").strip()),
    None
)

coluna_data = next(
    (c for c in colunas if "carimbo" in c.lower() or "data" in c.lower()),
    None
)

coluna_lider = next(
    (c for c in colunas if "liderança" in c.lower()),
    None
)

# -----------------------------------------------------------
# LIMPEZA E NORMALIZAÇÃO DOS SETORES
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

    # Separa múltiplos setores em linhas diferentes (Ex: "Laminação, GDR" vira duas entradas)
    df_original[coluna_setor] = df_original[coluna_setor].str.split(",")
    df_original = df_original.explode(coluna_setor)
    df_original[coluna_setor] = df_original[coluna_setor].str.strip()

# -----------------------------------------------------------
# TRATAMENTO DE DATA
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
    if coluna_setor:
        setores_lista = sorted(df_original[coluna_setor].dropna().unique())
    else:
        setores_lista = []

    setor_sel = st.selectbox("Selecione o Setor:", ["Todos os Setores"] + list(setores_lista))

with c3:
    if coluna_lider:
        lideres = (
            df_original[coluna_lider]
            .astype(str)
            .replace(['nan', 'None', ''], pd.NA)
            .dropna()
            .unique()
        )
        lideres = sorted(lideres)
    else:
        lideres = []

    lider_sel = st.multiselect("Selecione a(s) Liderança(s):", lideres)

# -----------------------------------------------------------
# APLICAÇÃO DOS FILTROS
# -----------------------------------------------------------
df_f = df_original.copy()

if mes_sel != "Todos os Meses":
    df_f = df_f[df_f["MesAno"] == mes_sel]

if setor_sel != "Todos os Setores" and coluna_setor:
    df_f = df_f[df_f[coluna_setor] == setor_sel]

if lider_sel and coluna_lider:
    df_f = df_f[df_f[coluna_lider].astype(str).isin(lider_sel)]

# 🔥 REGRA DE SST: Filtrar apenas quem respondeu "Sim" para dor (Coluna E)
df_sim = df_f[df_f[col_sentindo_dor].astype(str).str.upper().str.contains("SIM")].copy()

# -----------------------------------------------------------
# CONTAGEM DAS DORES E GRÁFICO
# -----------------------------------------------------------
st.subheader(f"📊 Queixas por Região - {setor_sel}")

if df_sim.empty:
    st.info("Nenhum registro de 'Sim' para dor encontrado para os filtros selecionados.")
else:
    # Separa múltiplos locais de dor na mesma célula (Coluna F)
    df_locais = df_sim[col_local_dor].astype(str).str.split(',')
    df_locais = df_locais.explode().str.strip()
    df_contagem = df_locais.value_counts().reset_index()
    df_contagem.columns = ["Região", "Quantidade"]
    df_contagem = df_contagem[df_contagem["Região"].str.lower() != "nan"]

    col_chart, col_table = st.columns([0.7, 0.3])

    with col_chart:
        # Gráfico de barras horizontal (substituindo o mapa humano)
        fig = px.bar(
            df_contagem.sort_values("Quantidade", ascending=True),
            x="Quantidade",
            y="Região",
            orientation='h',
            text="Quantidade",
            color="Quantidade",
            color_continuous_scale="Reds"
        )
        fig.update_layout(height=500, margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.write("### Detalhamento")
        st.dataframe(df_contagem, hide_index=True, use_container_width=True)

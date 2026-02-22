import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image

# -----------------------------------------------------------
# CONFIGURAÇÃO
# -----------------------------------------------------------
st.set_page_config(layout="wide", page_title="Monitoramento Ergonômico", initial_sidebar_state="collapsed")
st.title("🧍‍♂️ Monitoramento Ergonômico - Dashboard Corporativo")

st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        [data-testid="collapsedControl"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------
# CARREGAMENTO
# -----------------------------------------------------------
@st.cache_data(ttl=60)
def load_data():
    sheet_id = "1du_b9wsAlgvhrjyY0ts9x3Js_4FWDbWujRvi6PKMGEQ"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    return pd.read_csv(url)

df_original = load_data()

if df_original.empty:
    st.stop()

# -----------------------------------------------------------
# IDENTIFICAÇÃO DE COLUNAS
# -----------------------------------------------------------
colunas = df_original.columns

coluna_setor = next((c for c in colunas if "setor" in c.lower()), None)
coluna_data = next((c for c in colunas if "data" in c.lower()), None)
coluna_dor = next((c for c in colunas if "local" in c.lower()), None)
coluna_lider = next((c for c in colunas if "lider" in c.lower()), None)

# -----------------------------------------------------------
# LIMPEZA DE DADOS
# -----------------------------------------------------------
df_original[coluna_setor] = (
    df_original[coluna_setor]
    .astype(str)
    .str.replace("\xa0", " ", regex=False)
    .str.strip()
)

df_original[coluna_setor] = df_original[coluna_setor].str.split(",")
df_original = df_original.explode(coluna_setor)
df_original[coluna_setor] = df_original[coluna_setor].str.strip()

df_original[coluna_data] = pd.to_datetime(df_original[coluna_data], dayfirst=True, errors='coerce')
df_original = df_original.dropna(subset=[coluna_data])
df_original["MesAno"] = df_original[coluna_data].dt.to_period("M").astype(str)

# -----------------------------------------------------------
# FILTROS
# -----------------------------------------------------------
c1, c2, c3 = st.columns(3)

with c1:
    meses = sorted(df_original["MesAno"].unique(), reverse=True)
    mes_sel = st.selectbox("Selecione o Mês:", ["Todos"] + meses)

with c2:
    setores = sorted(df_original[coluna_setor].dropna().unique())
    setor_sel = st.selectbox("Selecione o Setor:", ["Todos"] + list(setores))

with c3:
    lideres = sorted(df_original[coluna_lider].dropna().unique())
    lider_sel = st.multiselect("Liderança:", lideres)

df = df_original.copy()

if mes_sel != "Todos":
    df = df[df["MesAno"] == mes_sel]

if setor_sel != "Todos":
    df = df[df[coluna_setor] == setor_sel]

if lider_sel:
    df = df[df[coluna_lider].isin(lider_sel)]

if df.empty:
    st.warning("Sem dados para os filtros.")
    st.stop()

# -----------------------------------------------------------
# KPI
# -----------------------------------------------------------
k1, k2, k3 = st.columns(3)

k1.metric("Total de Registros", len(df))
k2.metric("Colaboradores com Dor", df[coluna_dor].notna().sum())
k3.metric("Setores Afetados", df[coluna_setor].nunique())

# -----------------------------------------------------------
# DORES
# -----------------------------------------------------------
df_dores = df[coluna_dor].dropna().str.get_dummies(sep=",")
df_dores.columns = df_dores.columns.str.strip()

df_contagem = df_dores.sum().reset_index()
df_contagem.columns = ["Parte", "Qtd"]

# -----------------------------------------------------------
# NORMALIZAÇÃO
# -----------------------------------------------------------
def normalizar(parte):
    p = str(parte).lower()

    if "mão" in p: return "Mãos"
    if "pé" in p or "tornozelo" in p: return "PÉS"
    if "joelho" in p or "perna" in p: return "Pernas / Joelho(s)"
    if "coluna" in p or "costas" in p: return "Coluna (Costas)"
    if "ombro" in p: return "Ombro(s)"
    return None

df_contagem["Parte"] = df_contagem["Parte"].apply(normalizar)
df_contagem = df_contagem.dropna()
df_contagem = df_contagem.groupby("Parte", as_index=False)["Qtd"].sum()

# -----------------------------------------------------------
# COORDENADAS
# -----------------------------------------------------------
coords = {
    "Mãos": [250, 350],
    "PÉS": [350, 85],
    "Pernas / Joelho(s)": [230, 310],
    "Coluna (Costas)": [744, 740],
    "Ombro(s)": [650, 785]
}

df_c = pd.DataFrame.from_dict(coords, orient="index", columns=["x", "y"]).reset_index()
df_c.columns = ["Parte", "x", "y"]

df_mapa = pd.merge(df_c, df_contagem, on="Parte")

# -----------------------------------------------------------
# LAYOUT PRINCIPAL
# -----------------------------------------------------------
col_map, col_side = st.columns([0.65, 0.35])

# MAPA
with col_map:
    img = Image.open("mapa_corporal.png")
    w, h = img.size

    fig = px.scatter(
        df_mapa,
        x="x",
        y="y",
        size="Qtd",
        color="Qtd",
        text="Qtd"
    )

    fig.add_layout_image(dict(
        source=img,
        xref="x", yref="y",
        x=0, y=h,
        sizex=w, sizey=h,
        sizing="stretch",
        layer="below"
    ))

    fig.update_xaxes(visible=False, range=[0, w])
    fig.update_yaxes(visible=False, range=[0, h])

    st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------
# LADO DIREITO
# -----------------------------------------------------------
with col_side:

    st.subheader("📊 Ranking de Dores")
    st.dataframe(df_contagem.sort_values("Qtd", ascending=False), use_container_width=True)

    st.subheader("🏭 Ranking por Setor")
    ranking_setor = df.groupby(coluna_setor).size().reset_index(name="Qtd")
    st.dataframe(ranking_setor.sort_values("Qtd", ascending=False), use_container_width=True)

# -----------------------------------------------------------
# TENDÊNCIA
# -----------------------------------------------------------
st.subheader("📈 Evolução Mensal")

df_trend = df_original.copy()
df_trend = df_trend[df_trend[coluna_dor].notna()]
trend = df_trend.groupby("MesAno").size().reset_index(name="Qtd")

fig2 = px.line(trend, x="MesAno", y="Qtd", markers=True)
st.plotly_chart(fig2, use_container_width=True)

import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image

# -----------------------------------------------------------
# CONFIGURAÇÃO DE PÁGINA
# -----------------------------------------------------------
st.set_page_config(layout="wide", page_title="Monitoramento Ergonômico", initial_sidebar_state="collapsed")
st.title("🧍‍♂️ Monitoramento Ergonômico")

# Esconde controles da barra lateral
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        [data-testid="collapsedControl"] {display: none;}
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_data():
    try:
        # Link da sua planilha pública
        sheet_id = "1du_b9wsAlgvhrjyY0ts9x3Js_4FWDbWujRvi6PKMGEQ"
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        return pd.DataFrame()

df_original = load_data()

if df_original.empty:
    st.warning("Aguardando dados da planilha...")
    st.stop()

# -----------------------------------------------------------
# IDENTIFICAÇÃO DINÂMICA DE COLUNAS
# -----------------------------------------------------------
colunas = df_original.columns.tolist()

# Busca flexível: encontra a coluna mesmo que tenha "Setor", "Setor:" ou "SETOR"
coluna_setor = next((c for c in colunas if "setor" in c.lower()), None)
coluna_data = next((c for c in colunas if "carimbo" in c.lower() or "data" in c.lower()), None)
coluna_dor = next((c for c in colunas if "local da dor" in c.lower() or "indique o local" in c.lower()), None)
coluna_lider = next((c for c in colunas if "liderança" in c.lower()), None)

# Limpeza da coluna Setor
if coluna_setor:
    df_original[coluna_setor] = df_original[coluna_setor].astype(str).replace(['nan', 'None', ''], 'Não Informado').str.strip()

if coluna_data:
    df_original[coluna_data] = pd.to_datetime(df_original[coluna_data], dayfirst=True, errors='coerce')
    df_original = df_original.dropna(subset=[coluna_data])
    df_original["MesAno"] = df_original[coluna_data].dt.to_period("M").astype(str)

# Interface de Filtros
c1, c2, c3 = st.columns(3)

with c1:
    meses = sorted(df_original["MesAno"].unique(), reverse=True) if "MesAno" in df_original.columns else []
    mes_sel = st.selectbox("Selecione o Mês:", ["Todos os Meses"] + meses)

with c2:
    # Garante que pegamos os nomes reais (Acabamento, GDR, etc) da coluna identificada
    if coluna_setor:
        setores_lista = sorted([s for s in df_original[coluna_setor].unique() if s and s.lower() != "nan" and s != "Não Informado"])
    else:
        setores_lista = []
    setor_sel = st.selectbox("Selecione o Setor:", ["Todos os Setores"] + setores_lista)

with c3:
    if coluna_lider:
        lideres_brutos = df_original[coluna_lider].astype(str).replace(['nan', 'None', ''], pd.NA).dropna().unique()
        lideres = sorted(list(lideres_brutos))
    else:
        lideres = []
    lider_sel = st.multiselect("Selecione a(s) Liderança(s):", lideres)

# Aplicação de Filtros
df_f = df_original.copy()
if mes_sel != "Todos os Meses": 
    df_f = df_f[df_f["MesAno"] == mes_sel]
if setor_sel != "Todos os Setores": 
    df_f = df_f[df_f[coluna_setor] == setor_sel]
if lider_sel: 
    df_f = df_f[df_f[coluna_lider].astype(str).isin(lider_sel)]

# -----------------------------------------------------------
# MAPA CORPORAL E GRÁFICOS
# -----------------------------------------------------------
if df_f.empty:
    st.info("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()

# Processamento da contagem de dores
df_dores = df_f[coluna_dor].str.get_dummies(sep=",")
df_dores.columns = df_dores.columns.str.strip()
df_contagem = df_dores.sum().reset_index().rename(columns={"index": "Parte", 0: "Qtd"})

# Coordenadas ajustadas para os nomes da sua planilha
coords = {
    "Braços / Mãos": [250, 350], 
    "Pernas / Joelho(s)": [230, 310], 
    "PÉS": [350, 85],
    "pé": [350, 85],
    "Coluna (Costas)": [744, 740], 
    "Ombro(s)": [650, 785],
    "Braços / Punho": [250, 350],
    "Mãos": [110, 510]
}

df_c = pd.DataFrame.from_dict(coords, orient="index", columns=["x", "y"]).reset_index().rename(columns={"index": "Parte"})
df_mapa = pd.merge(df_c, df_contagem, on="Parte", how="inner")

col_map, col_tab = st.columns([0.6, 0.4])

with col_map:
    try:
        img = Image.open("mapa_corporal.png")
        w, h = img.size
        
        fig = px.scatter(df_mapa[df_mapa["Qtd"] > 0], x="x", y="y", size="Qtd", color="Qtd",
                         color_continuous_scale="RdYlGn_r", text="Qtd", size_max=50)

        fig.update_traces(
            textfont=dict(size=14, family="Arial Black", color="black"),
            textposition='middle center'
        )

        fig.add_layout_image(dict(
            source=img, xref="x", yref="y", x=0, y=h, 
            sizex=w, sizey=h, sizing="stretch", layer="below"
        ))

        fig.update_xaxes(visible=False, range=[0, w], autorange=False)
        fig.update_yaxes(visible=False, range=[0, h], autorange=False)
        fig.update_layout(height=700, margin=dict(l=0, r=0, t=0, b=0), coloraxis_showscale=True)
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    except Exception as e:
        st.error(f"Erro ao carregar o mapa corporal: {e}")

with col_tab:
    st.subheader("📊 Frequência por Local")
    # Tabela detalhada
    st.dataframe(df_contagem.sort_values("Qtd", ascending=False), hide_index=True, use_container_width=True)

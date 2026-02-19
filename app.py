import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image

# -----------------------------------------------------------
# CONFIGURAÇÃO DE PÁGINA
# -----------------------------------------------------------
st.set_page_config(layout="wide", page_title="Monitoramento Ergonômico", initial_sidebar_state="collapsed")
st.title("🧍‍♂️ Monitoramento Ergonômico")

# Esconde controles da barra lateral para interface limpa
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        [data-testid="collapsedControl"] {display: none;}
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_data():
    try:
        # Link da sua planilha pública (formato CSV)
        sheet_id = "1du_b9wsAlgvhrjyY0ts9x3Js_4FWDbWujRvi6PKMGEQ"
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        return pd.DataFrame()

df_original = load_data()

if df_original.empty:
    st.warning("Aguardando carregamento dos dados da planilha...")
    st.stop()

# -----------------------------------------------------------
# PROCESSAMENTO DE COLUNAS E FILTROS
# -----------------------------------------------------------
colunas = df_original.columns.tolist()
coluna_Setor = next((c for c in colunas if "Setor" in c.lower()), None)
coluna_data = next((c for c in colunas if "carimbo" in c.lower() or "data" in c.lower()), None)
coluna_dor = next((c for c in colunas if "local da dor" in c.lower()), None)
coluna_lider = next((c for c in colunas if "liderança" in c.lower()), None)

# Tratamento de dados para evitar erros de tipo (TypeError)
if coluna_Setor:
    df_original[coluna_Setor] = df_original[coluna_Setor].astype(str).fillna("Não Informado").str.strip()

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
    Setores = sorted([s for s in df_original[coluna_Setor].unique() if s and s.lower() != "nan"]) if coluna_Setor else []
    Setor_sel = st.selectbox("Selecione o Setor:", ["Todos os Setores"] + Setores)

with c3:
    # Solução para o erro da linha 67: Garante que a lista de líderes seja apenas de strings e sem nulos
    if coluna_lider:
        lideres_brutos = df_original[coluna_lider].astype(str).replace(['nan', 'None', ''], pd.NA).dropna().unique()
        lideres = sorted(list(lideres_brutos))
    else:
        lideres = []
    lider_sel = st.multiselect("Selecione a(s) Liderança(s):", lideres)

# Aplicação dos Filtros
df_f = df_original.copy()
if mes_sel != "Todos os Meses": 
    df_f = df_f[df_f["MesAno"] == mes_sel]
if Setor_sel != "Todos os Setores": 
    df_f = df_f[df_f[coluna_Setor] == Setor_sel]
if lider_sel: 
    df_f = df_f[df_f[coluna_lider].astype(str).isin(lider_sel)]

# -----------------------------------------------------------
# MAPA CORPORAL E GRÁFICOS
# -----------------------------------------------------------
if df_f.empty:
    st.info("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()

# Contagem das queixas
df_dores = df_f[coluna_dor].str.get_dummies(sep=",")
df_dores.columns = df_dores.columns.str.strip()
df_contagem = df_dores.sum().reset_index().rename(columns={"index": "Parte", 0: "Qtd"})

# Coordenadas (X, Y) para os pontos no mapa
coords = {
    "Braços/Punho": [250, 350], "Mãos": [110, 510], "Antebraço/Punho": [415, 610],
    "Cotovelo": [300, 680], "Ombro(s)": [650, 785], "Coluna Cervical (Pescoço)": [744, 840],
    "Coluna Torácica(Costas)": [744, 740], "Coluna Lombar": [744, 570],
    "Joelho": [230, 310], "Tornezelo": [686, 130], "Pé": [350, 85],
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
        st.error(f"Erro ao carregar mapa_corporal.png: {e}")

with col_tab:
    st.subheader("📊 Frequência por Local")
    st.dataframe(df_contagem.sort_values("Qtd", ascending=False), hide_index=True, use_container_width=True)


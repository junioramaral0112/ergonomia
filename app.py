import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from PIL import Image
import unicodedata

# -----------------------------------------------------------
# CONFIGURAÇÃO DE PÁGINA (SEM BARRA LATERAL)
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
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        client = gspread.service_account(filename="credencial.json", scopes=scopes)
        spreadsheet = client.open("ergonomia")
        worksheet = spreadsheet.worksheet("Respostas ao formulário 1")
        values = worksheet.get_all_values()
        if not values: return pd.DataFrame()
        return pd.DataFrame(values[1:], columns=values[0])
    except Exception as e:
        st.error(f"Erro na conexão: {e}")
        return pd.DataFrame()

df_original = load_data()
if df_original.empty:
    st.stop()

# -----------------------------------------------------------
# PROCESSAMENTO DE COLUNAS E FILTROS
# -----------------------------------------------------------
colunas = df_original.columns.tolist()
coluna_setor = next((c for c in colunas if "setor" in c.lower()), None)
coluna_data = next((c for c in colunas if "carimbo" in c.lower() or "data" in c.lower()), None)
coluna_dor = next((c for c in colunas if "local da dor" in c.lower()), None)
coluna_lider = next((c for c in colunas if "liderança" in c.lower()), None)

if coluna_setor:
    df_original[coluna_setor] = df_original[coluna_setor].astype(str).str.strip()
    df_original = df_original[~df_original[coluna_setor].str.lower().isin(['nan', 'none', ''])]

df_original[coluna_data] = pd.to_datetime(df_original[coluna_data], dayfirst=True, errors='coerce')
df_original = df_original.dropna(subset=[coluna_data])
df_original["MesAno"] = df_original[coluna_data].dt.to_period("M").astype(str)

c1, c2, c3 = st.columns(3)
with c1:
    meses = sorted(df_original["MesAno"].unique(), reverse=True)
    mes_sel = st.selectbox("Selecione o Mês:", ["Todos os Meses"] + meses)

with c2:
    # Captura GDR, Laminação, Acabamento e outros automaticamente
    setores_unicos = sorted(list(set([s for s in df_original[coluna_setor].unique() if s])))
    setor_sel = st.selectbox("Selecione o Setor:", ["Todos os Setores"] + setores_unicos)

df_f = df_original.copy()
if mes_sel != "Todos os Meses": df_f = df_f[df_f["MesAno"] == mes_sel]
if setor_sel != "Todos os Setores": df_f = df_f[df_f[coluna_setor] == setor_sel]

with c3:
    lideres = sorted(df_f[coluna_lider].unique().tolist()) if coluna_lider else []
    lider_sel = st.multiselect("Selecione a(s) Liderança(s):", lideres)
    if lider_sel: df_f = df_f[df_f[coluna_lider].isin(lider_sel)]

# -----------------------------------------------------------
# MAPA E COORDENADAS (AJUSTADO PARA LAMINAÇÃO E GDR)
# -----------------------------------------------------------
if df_f.empty:
    st.info("Sem dados para esta combinação de filtros.")
    st.stop()

df_dores = df_f[coluna_dor].str.get_dummies(sep=",")
df_dores.columns = df_dores.columns.str.strip()
df_contagem = df_dores.sum().reset_index().rename(columns={"index": "Parte", 0: "Qtd"})

# DICIONÁRIO AMPLIADO: Mapeia variações de nomes para garantir que Laminação e GDR funcionem
coords = {
    "Braços/Punho": [250, 350], 
    "Mãos": [110, 510], 
    "Antebraço/Punho": [415, 610], 
    "Cotovelo": [300, 680], 
    "Ombro(s)": [650, 785], 
    "Coluna Cervical (Pescoço)": [744, 840], 
    "Coluna Torácica(Costas)": [744, 740], 
    "Coluna Lombar": [744, 570],
    "Joelho": [230, 310], 
    "Tornezelo": [686, 130], 
    "Pé": [350, 85],
}

df_c = pd.DataFrame.from_dict(coords, orient="index", columns=["x", "y"]).reset_index().rename(columns={"index": "Parte"})
df_mapa = pd.merge(df_c, df_contagem, on="Parte", how="inner")

col_map, col_tab = st.columns([0.6, 0.4])

with col_map:
    try:
        img = Image.open("mapa_corporal.png")
        w, h = img.size
        
        # Mapa de Calor reativado
        fig = px.scatter(df_mapa[df_mapa["Qtd"] > 0], x="x", y="y", size="Qtd", color="Qtd",
                         color_continuous_scale="RdYlGn_r", text="Qtd", size_max=50)

        fig.update_traces(
            textfont=dict(size=16, family="Arial Black", color="black"),
            textposition='middle center',
            text=df_mapa[df_mapa["Qtd"] > 0]["Qtd"].apply(lambda x: f"<b>{x}</b>")
        )

        fig.add_layout_image(dict(
            source=img, xref="x", yref="y", x=0, y=h, 
            sizex=w, sizey=h, sizing="stretch", layer="below"
        ))

        fig.update_xaxes(visible=False, range=[0, w], autorange=False)
        fig.update_yaxes(visible=False, range=[0, h], autorange=False)
        fig.update_layout(height=700, margin=dict(l=0, r=0, t=0, b=0), coloraxis_showscale=True)
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    except: st.error("Imagem mapa_corporal.png não encontrada.")

with col_tab:
    st.subheader("📊 Dados Detalhados")
    st.dataframe(df_contagem.sort_values("Qtd", ascending=False), hide_index=True, use_container_width=True)
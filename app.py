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

col_sentindo_dor = colunas[4]  # Coluna E
col_local_dor = colunas[5]     # Coluna F

coluna_setor = next((c for c in colunas if "setor" in c.lower().replace(":", "").strip()), None)
coluna_data = next((c for c in colunas if "carimbo" in c.lower() or "data" in c.lower()), None)
coluna_lider = next((c for c in colunas if "liderança" in c.lower()), None)

# -----------------------------------------------------------
# TRATAMENTO DE DATA (MELHORADO PARA PEGAR TODO O HISTÓRICO)
# -----------------------------------------------------------
if coluna_data:
    # Usamos errors='coerce' para não travar o código, mas sem deletar as linhas imediatamente
    df_original[coluna_data] = pd.to_datetime(df_original[coluna_data], dayfirst=True, errors='coerce')
    
    # Se ainda houver datas vazias, tentamos um formato secundário antes de desistir
    df_original["MesAno"] = df_original[coluna_data].dt.strftime('%Y-%m')
    
    # Remove apenas se for realmente impossível ler a data
    df_original = df_original.dropna(subset=["MesAno"])

# -----------------------------------------------------------
# LIMPEZA DOS SETORES
# -----------------------------------------------------------
if coluna_setor:
    df_original[coluna_setor] = df_original[coluna_setor].astype(str).str.strip()
    # Separa múltiplos setores (Ex: "Laminação, GDR")
    df_original[coluna_setor] = df_original[coluna_setor].str.split(",")
    df_original = df_original.explode(coluna_setor)
    df_original[coluna_setor] = df_original[coluna_setor].str.strip()

# -----------------------------------------------------------
# FILTROS
# -----------------------------------------------------------
c1, c2, c3 = st.columns(3)

with c1:
    # Pega todos os MesAno únicos, ordena do mais novo para o mais antigo
    meses_disponiveis = sorted(df_original["MesAno"].unique().tolist(), reverse=True)
    mes_sel = st.selectbox("Selecione o Mês:", ["Todos os Meses"] + meses_disponiveis)

with c2:
    setores_lista = sorted([s for s in df_original[coluna_setor].unique() if str(s).lower() != 'nan']) if coluna_setor else []
    setor_sel = st.selectbox("Selecione o Setor:", ["Todos os Setores"] + setores_lista)

with c3:
    if coluna_lider:
        lideres = sorted([l for l in df_original[coluna_lider].astype(str).unique() if l.lower() != 'nan'])
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

# 🔥 REGRA DE SST: Gráfico baseado apenas em quem respondeu "Sim"
df_sim = df_f[df_f[col_sentindo_dor].astype(str).str.upper().str.contains("SIM")].copy()

# -----------------------------------------------------------
# CONTAGEM E GRÁFICO
# -----------------------------------------------------------
st.subheader(f"📊 Queixas por Região - {setor_sel}")

if df_sim.empty:
    st.info("Nenhum registro de dor encontrado para os filtros selecionados.")
else:
    df_locais = df_sim[col_local_dor].astype(str).str.split(',')
    df_locais = df_locais.explode().str.strip()
    df_contagem = df_locais.value_counts().reset_index()
    df_contagem.columns = ["Região", "Quantidade"]
    df_contagem = df_contagem[df_contagem["Região"].str.lower() != "nan"]

    col_chart, col_table = st.columns([0.7, 0.3])

    with col_chart:
        fig = px.bar(
            df_contagem.sort_values("Quantidade", ascending=True),
            x="Quantidade", y="Região", orientation='h',
            text="Quantidade", color="Quantidade",
            color_continuous_scale="Reds"
        )
        fig.update_layout(height=500, margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.dataframe(df_contagem, hide_index=True, use_container_width=True)

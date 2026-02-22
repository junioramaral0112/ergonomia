import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------
# CONFIGURAÇÃO DE PÁGINA
# -----------------------------------------------------------
st.set_page_config(layout="wide", page_title="Monitoramento Ergonômico", initial_sidebar_state="collapsed")
st.title("🧍‍♂️ Monitoramento Ergonômico")

st.markdown("<style>[data-testid='stSidebarNav'] {display: none;} [data-testid='collapsedControl'] {display: none;}</style>", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_data():
    try:
        # Link da sua planilha pública conforme fornecido
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
# MAPEAMENTO POR POSIÇÃO (MAIS SEGURO QUE POR NOME)
# -----------------------------------------------------------
colunas = df_original.columns.tolist()
col_data = colunas[0]          # Carimbo de data/hora
col_setor = colunas[10]        # Coluna K (Setor:)
col_lider = colunas[7]         # Coluna H (Liderança)
col_sentindo_dor = colunas[4]  # Coluna E (Hoje, você está sentindo...)
col_local_dor = colunas[5]     # Coluna F (Se SIM, indique o local...)

# Criar base de processamento
df_base = df_original.copy()

# 1. Tratamento de Datas para 2026
df_base[col_data] = pd.to_datetime(df_base[col_data], dayfirst=True, errors='coerce')
df_base = df_base.dropna(subset=[col_data])
df_base["MesAno"] = df_base[col_data].dt.to_period("M").astype(str)

# -----------------------------------------------------------
# INTERFACE DE FILTROS (DADOS BRUTOS PARA NÃO SUMIR SETORES)
# -----------------------------------------------------------
c1, c2, c3 = st.columns(3)

with c1:
    meses = sorted(df_base["MesAno"].unique(), reverse=True)
    mes_sel = st.selectbox("Selecione o Mês:", ["Todos os Meses"] + meses)

with c2:
    # Separa setores que estão na mesma célula (ex: "Lâminaçao, GDR")
    setores_raw = df_base[col_setor].astype(str).str.split(',').explode().str.strip()
    setores_unicos = sorted([s for s in setores_raw.unique() if s and s.lower() != 'nan'])
    setor_sel = st.selectbox("Selecione o Setor:", ["Todos os Setores"] + setores_unicos)

with c3:
    lideres = sorted(df_base[col_lider].astype(str).dropna().unique().tolist())
    lider_sel = st.multiselect("Selecione a(s) Liderança(s):", lideres)

# -----------------------------------------------------------
# FILTRAGEM E REGRA DE NEGÓCIO ("SIM" NA COLUNA E)
# -----------------------------------------------------------
df_f = df_base.copy()

if mes_sel != "Todos os Meses":
    df_f = df_f[df_f["MesAno"] == mes_sel]

if setor_sel != "Todos os Setores":
    # Filtra o setor mesmo que ele esteja acompanhado de outro na célula
    df_f = df_f[df_f[col_setor].astype(str).str.contains(setor_sel, na=False)]

if lider_sel:
    df_f = df_f[df_f[col_lider].astype(str).isin(lider_sel)]

# APENAS RESPOSTAS "SIM" PARA O GRÁFICO
df_queixas = df_f[df_f[col_sentindo_dor].astype(str).str.upper().str.contains("SIM")].copy()

# -----------------------------------------------------------
# VISUALIZAÇÃO
# -----------------------------------------------------------
st.subheader(f"📊 Queixas por Região - {setor_sel}")

if df_queixas.empty:
    st.info("Nenhum registro de dor encontrado para os filtros selecionados.")
else:
    # Processa múltiplos locais de dor na coluna F
    df_locais = df_queixas[col_local_dor].astype(str).str.split(',').explode().str.strip()
    df_contagem = df_locais.value_counts().reset_index()
    df_contagem.columns = ["Região", "Quantidade"]
    df_contagem = df_contagem[df_contagem["Região"].str.lower() != "nan"]

    col_chart, col_table = st.columns([0.7, 0.3])
    with col_chart:
        fig = px.bar(df_contagem.sort_values("Quantidade", ascending=True), 
                     x="Quantidade", y="Região", orientation='h', 
                     text="Quantidade", color="Quantidade", color_continuous_scale="Reds")
        fig.update_layout(height=500, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)
    
    with col_table:
        st.dataframe(df_contagem, hide_index=True, use_container_width=True)

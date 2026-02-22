import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------
# CONFIGURAÇÃO DE PÁGINA
# -----------------------------------------------------------
st.set_page_config(layout="wide", page_title="Monitoramento Ergonômico", initial_sidebar_state="collapsed")
st.title("🧍‍♂️ Monitoramento Ergonômico")

# Estilo para esconder menus desnecessários
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        [data-testid="collapsedControl"] {display: none;}
    </style>
""", unsafe_allow_html=True)

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
# PROCESSAMENTO E REGRAS DE NEGÓCIO
# -----------------------------------------------------------
colunas = df_original.columns.tolist()

# Identificação das colunas (Baseado na estrutura da sua planilha)
col_sentindo_dor = colunas[4]  # Coluna E: "Hoje, você está sentindo alguma dor..."
col_local_dor = colunas[5]     # Coluna F: "Se SIM, indique o local da dor:"
col_lider = next((c for c in colunas if "liderança" in c.lower()), None)
col_setor = next((c for c in colunas if "setor" in c.lower()), None)
col_data = next((c for c in colunas if "carimbo" in c.lower() or "data" in c.lower() or "data" == c.lower()), None)

# 1. Limpeza de Setores: Trata "Lâminaçao, GDR" como entradas individuais
df_base = df_original.copy()
if col_setor:
    df_base[col_setor] = df_base[col_setor].astype(str).str.split(',')
    df_base = df_base.explode(col_setor)
    df_base[col_setor] = df_base[col_setor].str.strip()

# 2. Processamento de Datas
if col_data:
    df_base[col_data] = pd.to_datetime(df_base[col_data], dayfirst=True, errors='coerce')
    df_base = df_base.dropna(subset=[col_data])
    df_base["MesAno"] = df_base[col_data].dt.to_period("M").astype(str)

# -----------------------------------------------------------
# INTERFACE DE FILTROS (USA TODOS OS DADOS DISPONÍVEIS)
# -----------------------------------------------------------
c1, c2, c3 = st.columns(3)

with c1:
    meses = sorted(df_base["MesAno"].unique(), reverse=True) if "MesAno" in df_base.columns else []
    mes_sel = st.selectbox("Selecione o Mês:", ["Todos os Meses"] + meses)

with c2:
    setores_lista = sorted([s for s in df_base[col_setor].unique() if s and s.lower() != "nan"]) if col_setor else []
    setor_sel = st.selectbox("Selecione o Setor:", ["Todos os Setores"] + setores_lista)

with c3:
    lideres = sorted(df_base[col_lider].astype(str).replace(['nan', 'None'], pd.NA).dropna().unique().tolist()) if col_lider else []
    lider_sel = st.multiselect("Selecione a(s) Liderança(s):", lideres)

# Aplicar Filtros
df_f = df_base.copy()
if mes_sel != "Todos os Meses": df_f = df_f[df_f["MesAno"] == mes_sel]
if setor_sel != "Todos os Setores": df_f = df_f[df_f[col_setor] == setor_sel]
if lider_sel: df_f = df_f[df_f[col_lider].astype(str).isin(lider_sel)]

# -----------------------------------------------------------
# FILTRAGEM FINAL PARA O GRÁFICO (APENAS RESPOSTAS "SIM")
# -----------------------------------------------------------
# Agora filtramos para o gráfico apenas quem realmente está com dor
df_grafico = df_f[df_f[col_sentindo_dor].astype(str).str.upper().str.contains("SIM")].copy()

st.subheader("📊 Frequência de Queixas por Região Corporal")

if df_grafico.empty:
    st.info("Nenhum registro de dor encontrado para os filtros selecionados.")
else:
    # Processa os locais de dor (separa se houver múltiplos na mesma célula)
    df_locais = df_grafico[col_local_dor].astype(str).str.split(',')
    df_locais = df_locais.explode().str.strip()
    df_contagem = df_locais.value_counts().reset_index()
    df_contagem.columns = ["Região", "Quantidade"]
    df_contagem = df_contagem[df_contagem["Região"].str.lower() != "nan"]

    col_chart, col_table = st.columns([0.7, 0.3])

    with col_chart:
        fig = px.bar(
            df_contagem.sort_values("Quantidade", ascending=True),
            x="Quantidade",
            y="Região",
            orientation='h',
            text="Quantidade",
            color="Quantidade",
            color_continuous_scale="Reds"
        )
        fig.update_layout(height=500, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.write("### Detalhamento")
        st.dataframe(df_contagem, hide_index=True, use_container_width=True)

import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------
# CONFIGURAÇÃO DE PÁGINA
# -----------------------------------------------------------
st.set_page_config(layout="wide", page_title="Monitoramento Ergonômico", initial_sidebar_state="collapsed")
st.title("🧍‍♂️ Monitoramento Ergonômico")

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
# IDENTIFICAÇÃO DINÂMICA E FILTRAGEM DE REGRAS
# -----------------------------------------------------------
colunas = df_original.columns.tolist()

# Mapeamento exato baseado na sua planilha
col_sentindo_dor = colunas[4]  # Coluna E: "Hoje, você está sentindo alguma dor..."
col_local_dor = colunas[5]     # Coluna F: "Se SIM, indique o local da dor:"
col_lider = next((c for c in colunas if "liderança" in c.lower()), None)
col_setor = next((c for c in colunas if "setor" in c.lower()), None)
col_data = next((c for c in colunas if "carimbo" in c.lower() or "data" in c.lower() or "data" == c.lower()), None)

# REGRA DE OURO: Filtrar apenas quem respondeu "Sim" na Coluna E
df_sim = df_original[df_original[col_sentindo_dor].astype(str).str.upper().str.contains("SIM")].copy()

# Limpeza e separação de setores (Trata "Lâminaçao, GDR" como dois registros separados)
if col_setor:
    df_sim[col_setor] = df_sim[col_setor].astype(str).str.split(',')
    df_sim = df_sim.explode(col_setor)
    df_sim[col_setor] = df_sim[col_setor].str.strip()

if col_data:
    df_sim[col_data] = pd.to_datetime(df_sim[col_data], dayfirst=True, errors='coerce')
    df_sim = df_sim.dropna(subset=[col_data])
    df_sim["MesAno"] = df_sim[col_data].dt.to_period("M").astype(str)

# -----------------------------------------------------------
# INTERFACE DE FILTROS
# -----------------------------------------------------------
c1, c2, c3 = st.columns(3)

with c1:
    meses = sorted(df_sim["MesAno"].unique(), reverse=True) if "MesAno" in df_sim.columns else []
    mes_sel = st.selectbox("Selecione o Mês:", ["Todos os Meses"] + meses)

with c2:
    setores_lista = sorted([s for s in df_sim[col_setor].unique() if s and s.lower() != "nan"]) if col_setor else []
    setor_sel = st.selectbox("Selecione o Setor:", ["Todos os Setores"] + setores_lista)

with c3:
    lideres = sorted(df_sim[col_lider].astype(str).dropna().unique().tolist()) if col_lider else []
    lider_sel = st.multiselect("Selecione a(s) Liderança(s):", lideres)

# Aplicação dos Filtros
df_f = df_sim.copy()
if mes_sel != "Todos os Meses": df_f = df_f[df_f["MesAno"] == mes_sel]
if setor_sel != "Todos os Setores": df_f = df_f[df_f[col_setor] == setor_sel]
if lider_sel: df_f = df_f[df_f[col_lider].astype(str).isin(lider_sel)]

# -----------------------------------------------------------
# VISUALIZAÇÃO DOS DADOS (GRÁFICO DE BARRAS)
# -----------------------------------------------------------
st.subheader("📊 Frequência de Queixas por Região Corporal")

if df_f.empty:
    st.info("Nenhum registro de 'Sim' para dor encontrado com os filtros selecionados.")
else:
    # Separa múltiplos locais de dor na mesma célula (ex: "Mãos, Punho")
    df_locais = df_f[col_local_dor].astype(str).str.split(',')
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

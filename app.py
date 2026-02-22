import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------
# CONFIGURAÇÃO DE PÁGINA
# -----------------------------------------------------------
st.set_page_config(
    layout="wide",
    page_title="Gestão Ergonômica Inteligente",
    initial_sidebar_state="expanded"
)

# Estilização Personalizada
st.markdown("""
    <style>
        .main { background-color: #f8f9fa; }
        .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        footer { visibility: hidden; }
        .footer-text { text-align: center; color: #6c757d; padding: 20px; font-size: 14px; border-top: 1px solid #dee2e6; margin-top: 50px; }
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
        st.error(f"Erro na conexão: {e}")
        return pd.DataFrame()

df_original = load_data()

if df_original.empty:
    st.warning("Aguardando carregamento dos dados da planilha...")
    st.stop()

# -----------------------------------------------------------
# PROCESSAMENTO DE DADOS
# -----------------------------------------------------------
colunas = df_original.columns.tolist()
col_data = colunas[0]
col_sentindo_dor = colunas[4]
col_local_dor = colunas[5]
coluna_lider = next((c for c in colunas if "liderança" in c.lower()), colunas[7])
coluna_setor = next((c for c in colunas if "setor" in c.lower().replace(":", "").strip()), colunas[10])

# Tratamento de Data
df_original[col_data] = pd.to_datetime(df_original[col_data], dayfirst=True, errors='coerce')
df_original = df_original.dropna(subset=[col_data])
df_original["MesAno"] = df_original[col_data].dt.strftime('%Y-%m')

# Tratamento de Setores (Explosão para filtros individuais)
df_original[coluna_setor] = df_original[coluna_setor].astype(str).str.strip()
df_setores = df_original.copy()
df_setores[coluna_setor] = df_setores[coluna_setor].str.split(",")
df_setores = df_setores.explode(coluna_setor)
df_setores[coluna_setor] = df_setores[coluna_setor].str.strip()

# -----------------------------------------------------------
# FILTROS NA BARRA LATERAL (SIDEBAR)
# -----------------------------------------------------------
st.sidebar.header("🔍 Painel de Filtros")

meses = sorted(df_original["MesAno"].unique().tolist(), reverse=True)
mes_sel = st.sidebar.selectbox("Período de Análise:", ["Histórico Completo"] + meses)

setores_lista = sorted([s for s in df_setores[coluna_setor].unique() if str(s).lower() != 'nan' and s != 'Não Informado'])
setor_sel = st.sidebar.selectbox("Setor de Atuação:", ["Todos os Setores"] + setores_lista)

lideres = sorted([l for l in df_original[coluna_lider].astype(str).unique() if l.lower() != 'nan'])
lider_sel = st.sidebar.multiselect("Filtrar por Liderança:", lideres)

# Aplicação dos Filtros
df_f = df_setores.copy()
if mes_sel != "Histórico Completo":
    df_f = df_f[df_f["MesAno"] == mes_sel]
if setor_sel != "Todos os Setores":
    df_f = df_f[df_f[coluna_setor] == setor_sel]
if lider_sel:
    df_f = df_f[df_f[coluna_lider].astype(str).isin(lider_sel)]

# -----------------------------------------------------------
# KPIs - INDICADORES DE IMPACTO
# -----------------------------------------------------------
st.title("🧍‍♂️ Monitoramento Ergonômico")
st.markdown("---")

total_respostas = len(df_f)
df_dor_sim = df_f[df_f[col_sentindo_dor].astype(str).str.upper().str.contains("SIM")]
total_queixas = len(df_dor_sim)
percentual_dor = (total_queixas / total_respostas * 100) if total_respostas > 0 else 0

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Total de Avaliados", f"{total_respostas} colaboradores")
kpi2.metric("Casos com Desconforto", f"{total_queixas} queixas", delta_color="inverse")
kpi3.metric("Índice de Queixas (%)", f"{percentual_dor:.1f}%", delta_color="inverse")

st.markdown("---")

# -----------------------------------------------------------
# GRÁFICO E DETALHAMENTO
# -----------------------------------------------------------
if df_dor_sim.empty:
    st.info("Nenhum registro de queixa encontrado para os filtros selecionados.")
else:
    df_locais = df_dor_sim[col_local_dor].astype(str).str.split(',').explode().str.strip()
    df_contagem = df_locais.value_counts().reset_index()
    df_contagem.columns = ["Região Corporal", "Quantidade"]
    df_contagem = df_contagem[df_contagem["Região Corporal"].str.lower() != "nan"]

    col_chart, col_table = st.columns([0.6, 0.4])

    with col_chart:
        st.subheader("Análise por Região")
        fig = px.bar(
            df_contagem.sort_values("Quantidade", ascending=True),
            x="Quantidade", y="Região Corporal", orientation='h',
            text="Quantidade", color="Quantidade",
            color_continuous_scale="Reds", template="plotly_white"
        )
        fig.update_layout(height=600, showlegend=False, font=dict(size=14))
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.subheader("Tabela de Frequência")
        st.dataframe(df_contagem.sort_values("Quantidade", ascending=False), 
                     hide_index=True, use_container_width=True, height=565)

# -----------------------------------------------------------
# RODAPÉ DE DIREITOS AUTORAIS
# -----------------------------------------------------------
st.markdown(f"""
    <div class="footer-text">
        © 2026 Gestão Ergonômica Inteligente | Desenvolvido por <b>Dilceu Junior</b><br>
        Técnico em Segurança do Trabalho - Consultoria de SST
    </div>
""", unsafe_allow_html=True)

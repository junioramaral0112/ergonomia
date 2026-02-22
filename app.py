import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------
# CONFIGURAÇÃO DE PÁGINA
# -----------------------------------------------------------
st.set_page_config(
    layout="wide",
    page_title="Gestão Ergonômica Inteligente",
    initial_sidebar_state="collapsed" # Melhora a experiência inicial no celular
)

# Estilização CSS para Mobile e Desktop
st.markdown("""
    <style>
        /* Ajuste de margens para telas pequenas */
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        
        /* Card de métricas mais elegante */
        [data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #e6e9ef;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        /* Rodapé fixo e centralizado */
        .footer-text {
            text-align: center;
            color: #6c757d;
            padding: 20px;
            font-size: 13px;
            border-top: 1px solid #eee;
            margin-top: 30px;
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------
# CARREGAMENTO DOS DADOS (Otimizado)
# -----------------------------------------------------------
@st.cache_data(ttl=60)
def load_data():
    try:
        sheet_id = "1du_b9wsAlgvhrjyY0ts9x3Js_4FWDbWujRvi6PKMGEQ"
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return pd.DataFrame()

df_original = load_data()

if df_original.empty:
    st.stop()

# -----------------------------------------------------------
# MAPEAMENTO DINÂMICO
# -----------------------------------------------------------
colunas = df_original.columns.tolist()
col_data = colunas[0]
col_sentindo_dor = colunas[4] # Coluna E
col_local_dor = colunas[5]    # Coluna F
coluna_lider = colunas[7]     # Coluna H
coluna_setor = colunas[10]    # Coluna K

# Tratamento de Data (Histórico 2025-2026)
df_original[col_data] = pd.to_datetime(df_original[col_data], dayfirst=True, errors='coerce')
df_original = df_original.dropna(subset=[col_data])
df_original["MesAno"] = df_original[col_data].dt.strftime('%Y-%m')

# -----------------------------------------------------------
# SIDEBAR (FILTROS)
# -----------------------------------------------------------
st.sidebar.header("⚙️ Configurações")

# Filtro de Mês
meses = sorted(df_original["MesAno"].unique().tolist(), reverse=True)
mes_sel = st.sidebar.selectbox("Mês de Referência:", ["Todos os Meses"] + meses)

# Filtro de Setor (Tratando múltiplos setores)
df_setores = df_original.copy()
df_setores[coluna_setor] = df_setores[coluna_setor].astype(str).str.split(',')
df_setores = df_setores.explode(coluna_setor).str.strip()
lista_setores = sorted([s for s in df_setores[coluna_setor].unique() if s != 'nan'])
setor_sel = st.sidebar.selectbox("Setor:", ["Todos os Setores"] + lista_setores)

# Filtro de Liderança
lideres = sorted([l for l in df_original[coluna_lider].astype(str).unique() if l != 'nan'])
lider_sel = st.sidebar.multiselect("Liderança:", lideres)

# Aplicação dos Filtros
df_f = df_setores.copy()
if mes_sel != "Todos os Meses": df_f = df_f[df_f["MesAno"] == mes_sel]
if setor_sel != "Todos os Setores": df_f = df_f[df_f[coluna_setor] == setor_sel]
if lider_sel: df_f = df_f[df_f[coluna_lider].astype(str).isin(lider_sel)]

# -----------------------------------------------------------
# CONTEÚDO PRINCIPAL (LAYOUT RESPONSIVO)
# -----------------------------------------------------------
st.title("🧍‍♂️ Ergonomia Inteligente")
st.caption(f"Visualizando: {setor_sel} | {mes_sel}")

# KPIs em colunas que se empilham no celular
k1, k2 = st.columns(2)
total_resp = len(df_f)
df_sim = df_f[df_f[col_sentindo_dor].astype(str).str.upper().str.contains("SIM")]
total_dor = len(df_sim)
taxa = (total_dor / total_resp * 100) if total_resp > 0 else 0

k1.metric("Avaliações", total_resp)
k2.metric("Índice de Queixas", f"{taxa:.1f}%")

st.markdown("---")

if df_sim.empty:
    st.info("Nenhuma queixa registrada para este filtro.")
else:
    # Processamento para o gráfico
    df_locais = df_sim[col_local_dor].astype(str).str.split(',').explode().str.strip()
    df_contagem = df_locais.value_counts().reset_index()
    df_contagem.columns = ["Região", "Qtd"]
    df_contagem = df_contagem[df_contagem["Região"].str.lower() != "nan"]

    # No celular, o gráfico ocupa a largura total primeiro, depois vem a tabela
    st.subheader("Regiões Críticas")
    fig = px.bar(
        df_contagem.sort_values("Qtd", ascending=True),
        x="Qtd", y="Região", orientation='h',
        text="Qtd", color="Qtd",
        color_continuous_scale="Reds", template="plotly_white"
    )
    fig.update_layout(height=450, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with st.expander("Ver Tabela Detalhada"):
        st.dataframe(df_contagem.sort_values("Qtd", ascending=False), hide_index=True, use_container_width=True)

# -----------------------------------------------------------
# RODAPÉ
# -----------------------------------------------------------
st.markdown(f"""
    <div class="footer-text">
        © 2026 Gestão Ergonômica | <b>Dilceu Junior</b><br>
    </div>
""", unsafe_allow_html=True)

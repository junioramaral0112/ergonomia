import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURAÇÃO DE PÁGINA (Otimizado para Celular)
st.set_page_config(
    layout="wide", 
    page_title="Gestão Ergonômica",
    initial_sidebar_state="collapsed"
)

# Estilo Visual Profissional
st.markdown("""
    <style>
        .stMetric { background-color: #ffffff; border: 1px solid #eee; padding: 10px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .footer { text-align: center; color: #666; font-size: 12px; margin-top: 50px; border-top: 1px solid #eee; padding: 20px; }
        .main { background-color: #f9f9f9; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_data():
    try:
        sheet_id = "1du_b9wsAlgvhrjyY0ts9x3Js_4FWDbWujRvi6PKMGEQ"
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(url)
        # Limpeza básica de nomes de colunas
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

df_raw = load_data()

if df_raw.empty:
    st.error("Erro ao carregar os dados da planilha. Verifique a conexão.")
    st.stop()

# --- MAPEAMENTO SEGURO POR POSIÇÃO ---
df_base = df_raw.copy()
c_data = df_base.columns[0]   # Carimbo de data/hora
c_dor = df_base.columns[4]    # Sentindo dor? (Coluna E)
c_local = df_base.columns[5]  # Local da dor (Coluna F)
c_lider = df_base.columns[7]  # Liderança (Coluna H)
c_setor = df_base.columns[10] # Setor (Coluna K)

# Tratamento de Data (Garante 2025 e 2026)
df_base[c_data] = pd.to_datetime(df_base[c_data], dayfirst=True, errors='coerce')
df_base = df_base.dropna(subset=[c_data])
df_base["MesAno"] = df_base[c_data].dt.strftime('%Y-%m')

# --- FILTROS NA SIDEBAR (GANHA ESPAÇO NO CELULAR) ---
st.sidebar.header("🔍 Painel de Filtros")

# Filtro Meses
meses = sorted(df_base["MesAno"].unique().tolist(), reverse=True)
mes_sel = st.sidebar.selectbox("Selecione o Mês:", ["Todos"] + meses)

# Filtro Setores (Tratando células com múltiplos setores)
df_base[c_setor] = df_base[c_setor].astype(str).str.strip().replace(['nan', 'None'], 'Geral')
lista_setores = sorted(list(set([x.strip() for s in df_base[c_setor].unique() for x in str(s).split(',') if x not in ['Geral', 'nan']])))
setor_sel = st.sidebar.selectbox("Selecione o Setor:", ["Todos"] + lista_setores)

# Filtro de Liderança ( Douglas, Flavio, Leonel, etc.)
lideres_lista = sorted([str(l).strip() for l in df_base[c_lider].unique() if str(l).lower() != 'nan' and str(l).strip() != ''])
lider_sel = st.sidebar.multiselect("Filtrar Liderança:", lideres_lista)

# --- APLICAÇÃO DOS FILTROS ---
df_f = df_base.copy()
if mes_sel != "Todos": 
    df_f = df_f[df_f["MesAno"] == mes_sel]
if setor_sel != "Todos": 
    df_f = df_f[df_f[c_setor].str.contains(setor_sel, na=False)]
if lider_sel:
    df_f = df_f[df_f[c_lider].astype(str).str.strip().isin(lider_sel)]

# --- DASHBOARD PRINCIPAL ---
st.title("🧍‍♂️ Monitoramento Ergonômico")
st.caption(f"Análise: {setor_sel} | {mes_sel}")

# KPIs Responsivos
k1, k2 = st.columns(2)
total_avaliados = len(df_f)
df_sim = df_f[df_f[c_dor].astype(str).str.upper().str.contains("SIM")].copy()
total_queixas = len(df_sim)
taxa_incidencia = (total_queixas / total_avaliados * 100) if total_avaliados > 0 else 0

k1.metric("Total de Avaliados", f"{total_avaliados}")
k2.metric("Índice de Queixas", f"{taxa_incidencia:.1f}%")

st.markdown("---")

if not df_sim.empty:
    # Processamento para o Gráfico de Regiões
    df_locais = df_sim[c_local].astype(str).str.split(',').explode().str.strip()
    df_contagem = df_locais.value_counts().reset_index()
    df_contagem.columns = ["Região", "Quantidade"]
    # Limpeza de nulos no gráfico
    df_contagem = df_contagem[df_contagem["Região"].astype(str).str.lower() != "nan"]

    st.subheader("Mapa de Queixas por Região")
    
    fig = px.bar(
        df_contagem.sort_values("Quantidade", ascending=True), 
        x="Quantidade", y="Região", orientation='h', text="Quantidade",
        color="Quantidade", color_continuous_scale="Reds",
        template="plotly_white"
    )
    
    fig.update_layout(
        height=550, 
        margin=dict(l=0, r=20, t=10, b=10), 
        showlegend=False,
        font=dict(size=13)
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with st.expander("📊 Ver Dados Detalhados"):
        st.dataframe(df_contagem.sort_values("Quantidade", ascending=False), hide_index=True, use_container_width=True)
else:
    st.info("Nenhum registro de desconforto encontrado para os filtros aplicados.")

# RODAPÉ
st.markdown(f'<div class="footer">© 2026 Gestão Ergonômica Inteligente | Desenvolvido por <b>Dilceu Junior</b><br>Técnico em Segurança do Trabalho</div>', unsafe_allow_html=True)

import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# 1. CONFIGURAÇÃO DE PÁGINA (Layout Mobile-First)
st.set_page_config(
    layout="wide", 
    page_title="Gestão Ergonômica Inteligente",
    initial_sidebar_state="collapsed"
)

# Configuração da IA com sua chave
genai.configure(api_key="AIzaSyCJ72jm7JfJKINgV9SjEALYdTwEGlM3FMU")
model = genai.GenerativeModel('gemini-1.5-flash')

def obter_sugestao_ia(setor, regiao, qtd):
    prompt = f"Como técnico de SST, sugira 3 melhorias ergonômicas (NR-17) para o setor {setor} com {qtd} queixas em {regiao}. Seja curto e prático."
    try:
        return model.generate_content(prompt).text
    except:
        return "Sugestões automáticas temporariamente indisponíveis."

# Estilo para Celular e Cards
st.markdown("""
    <style>
        .stMetric { background-color: #ffffff; border: 1px solid #eee; padding: 10px; border-radius: 10px; }
        .ia-card { background-color: #f0f7ff; border-left: 5px solid #007bff; padding: 15px; border-radius: 8px; margin: 10px 0; }
        .footer { text-align: center; color: #666; font-size: 12px; margin-top: 50px; border-top: 1px solid #eee; padding: 20px; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_data():
    try:
        sheet_id = "1du_b9wsAlgvhrjyY0ts9x3Js_4FWDbWujRvi6PKMGEQ"
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

df_raw = load_data()
if df_raw.empty: st.stop()

# --- MAPEAMENTO SEGURO (Baseado na imagem 10 da planilha) ---
df_base = df_raw.copy()
c_data = df_base.columns[0]   # Carimbo de data/hora
c_dor = df_base.columns[4]    # Hoje, você está sentindo... (Coluna E)
c_local = df_base.columns[5]  # Se SIM, indique o local... (Coluna F)
c_setor = df_base.columns[10] # Setor: (Coluna K)

# Tratamento de Data (Garante histórico 2025/2026)
df_base[c_data] = pd.to_datetime(df_base[c_data], dayfirst=True, errors='coerce')
df_base = df_base.dropna(subset=[c_data])
df_base["MesAno"] = df_base[c_data].dt.strftime('%Y-%m')

# --- FILTROS (SIDEBAR PARA CELULAR) ---
st.sidebar.header("🔍 Filtros")
meses = sorted(df_base["MesAno"].unique().tolist(), reverse=True)
mes_sel = st.sidebar.selectbox("Período:", ["Todos"] + meses)

# Limpeza de Setores (Evita erro da imagem 11)
df_base[c_setor] = df_base[c_setor].astype(str).str.strip().replace(['nan', 'None'], 'Geral')
lista_setores = sorted(list(set([x.strip() for s in df_base[c_setor].unique() for x in str(s).split(',') if x != 'Geral'])))
setor_sel = st.sidebar.selectbox("Setor:", ["Todos"] + lista_setores)

# --- APLICAÇÃO DE FILTROS ---
df_f = df_base.copy()
if mes_sel != "Todos": df_f = df_f[df_f["MesAno"] == mes_sel]
if setor_sel != "Todos": df_f = df_f[df_f[c_setor].str.contains(setor_sel, na=False)]

# --- LAYOUT PRINCIPAL ---
st.title("🧍‍♂️ Ergonomia Inteligente")

# KPIs Responsivos
k1, k2 = st.columns(2)
total = len(df_f)
df_sim = df_f[df_f[c_dor].astype(str).str.upper().str.contains("SIM")].copy()
taxa = (len(df_sim) / total * 100) if total > 0 else 0
k1.metric("Avaliações", total)
k2.metric("Índice de Queixas", f"{taxa:.1f}%")

st.markdown("---")

if not df_sim.empty:
    # Dados para Gráfico e IA
    df_locais = df_sim[c_local].astype(str).str.split(',').explode().str.strip()
    df_contagem = df_locais.value_counts().reset_index()
    df_contagem.columns = ["Região", "Qtd"]
    df_contagem = df_contagem[df_contagem["Região"].lower() != "nan"]
    
    regiao_topo = df_contagem.iloc[0]["Região"]
    qtd_topo = df_contagem.iloc[0]["Qtd"]

    # IA (Apenas se houver queixas)
    with st.expander("🤖 Ver Análise da IA", expanded=True):
        st.markdown(f"**Cenário:** {setor_sel} - {regiao_topo}")
        st.write(obter_sugestao_ia(setor_sel, regiao_topo, qtd_topo))

    # Gráfico (Ajusta automático no celular)
    fig = px.bar(df_contagem.sort_values("Qtd", ascending=True), 
                 x="Qtd", y="Região", orientation='h', text="Qtd",
                 color="Qtd", color_continuous_scale="Reds")
    fig.update_layout(height=450, margin=dict(l=0, r=10, t=10, b=10), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Nenhum registro encontrado.")

# RODAPÉ
st.markdown(f'<div class="footer">© 2026 Gestão Ergonômica | Desenvolvido por <b>Dilceu Junior</b></div>', unsafe_allow_html=True)

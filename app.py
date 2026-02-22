import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# 1. CONFIGURAÇÃO DE PÁGINA (Layout Responsivo)
st.set_page_config(layout="wide", page_title="Ergonomia Inteligente", initial_sidebar_state="collapsed")

# 2. CONFIGURAÇÃO DA IA (Chave direta e Modelo Corrigido)
API_KEY = "AIzaSyCJ72jm7JfJKINgV9SjEALYdTwEGlM3FMU"
genai.configure(api_key=API_KEY)

def obter_sugestao_ia(setor, regiao, qtd):
    try:
        # Nome do modelo corrigido para evitar Error 404
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Como perito em SST (NR-17), analise: Setor {setor}, {qtd} queixas na região corporal {regiao}. Dê 3 recomendações técnicas curtas."
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"IA em manutenção rápida. (Tente novamente em instantes)"

# Estilo para Celular
st.markdown("""<style>.stMetric {background-color: #ffffff; border: 1px solid #eee; padding: 10px; border-radius: 10px;}
.ia-card {background-color: #f0f7ff; border-left: 5px solid #007bff; padding: 15px; border-radius: 8px; margin: 10px 0; font-size: 14px;}</style>""", unsafe_allow_html=True)

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

# --- MAPEAMENTO SEGURO POR POSIÇÃO ---
df_base = df_raw.copy()
c_data = df_base.columns[0]   # Coluna A
c_dor = df_base.columns[4]    # Coluna E
c_local = df_base.columns[5]  # Coluna F
c_lider = df_base.columns[7]  # Coluna H
c_setor = df_base.columns[10] # Coluna K

# Tratamento de Data (Garante 2025 e 2026)
df_base[c_data] = pd.to_datetime(df_base[c_data], dayfirst=True, errors='coerce')
df_base = df_base.dropna(subset=[c_data])
df_base["MesAno"] = df_base[c_data].dt.strftime('%Y-%m')

# --- FILTROS (SIDEBAR PARA GANHAR ESPAÇO NO CELULAR) ---
st.sidebar.header("🔍 Filtros")
meses = sorted(df_base["MesAno"].unique().tolist(), reverse=True)
mes_sel = st.sidebar.selectbox("Mês:", ["Todos"] + meses)

# Limpeza e separação de setores (Ex: GDR, Laminação)
df_base[c_setor] = df_base[c_setor].astype(str).str.strip().replace(['nan', 'None'], 'Geral')
lista_setores = sorted(list(set([x.strip() for s in df_base[c_setor].unique() for x in str(s).split(',') if x != 'Geral' and x != 'nan'])))
setor_sel = st.sidebar.selectbox("Setor:", ["Todos"] + lista_setores)

# FILTRO LIDERANÇA (Douglas, Flavio, etc)
lideres_lista = sorted([str(l).strip() for l in df_base[c_lider].unique() if str(l).lower() != 'nan' and str(l).strip() != ''])
lider_sel = st.sidebar.multiselect("Liderança:", lideres_lista)

# --- APLICAÇÃO DOS FILTROS ---
df_f = df_base.copy()
if mes_sel != "Todos": df_f = df_f[df_f["MesAno"] == mes_sel]
if setor_sel != "Todos": df_f = df_f[df_f[c_setor].str.contains(setor_sel, na=False)]
if lider_sel: df_f = df_f[df_f[c_lider].astype(str).str.strip().isin(lider_sel)]

# --- LAYOUT PRINCIPAL ---
st.title("🧍‍♂️ Ergonomia Inteligente")

# KPIs responsivos
k1, k2 = st.columns(2)
total = len(df_f)
df_sim = df_f[df_f[c_dor].astype(str).str.upper().str.contains("SIM")].copy()
taxa = (len(df_sim) / total * 100) if total > 0 else 0
k1.metric("Amostragem", total)
k2.metric("Índice de Queixas", f"{taxa:.1f}%")

st.markdown("---")

if not df_sim.empty:
    # Contagem de Regiões
    df_locais = df_sim[c_local].astype(str).str.split(',').explode().str.strip()
    df_contagem = df_locais.value_counts().reset_index()
    df_contagem.columns = ["Região", "Qtd"]
    df_contagem = df_contagem[df_contagem["Região"].astype(str).str.lower() != "nan"]
    
    if not df_contagem.empty:
        reg_topo = df_contagem.iloc[0]["Região"]
        qtd_topo = df_contagem.iloc[0]["Qtd"]

        # Bloco da IA Dinâmica (Corrigido)
        st.subheader("🤖 Sugestão Técnica da IA")
        with st.spinner("IA analisando..."):
            texto_ia = obter_sugestao_ia(setor_sel, reg_topo, qtd_topo)
            st.markdown(f'<div class="ia-card">{texto_ia}</div>', unsafe_allow_html=True)

        # Gráfico responsivo
        fig = px.bar(df_contagem.sort_values("Qtd", ascending=True), 
                     x="Qtd", y="Região", orientation='h', text="Qtd",
                     color="Qtd", color_continuous_scale="Reds")
        fig.update_layout(height=450, margin=dict(l=0, r=10, t=10, b=10), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Nenhum registro de queixa encontrado para os filtros atuais.")

# RODAPÉ
st.markdown(f'<div style="text-align:center; color:#666; font-size:12px; margin-top:50px; border-top:1px solid #eee; padding:20px;">© 2026 Gestão Ergonômica | Desenvolvido por <b>Dilceu Junior</b></div>', unsafe_allow_html=True)

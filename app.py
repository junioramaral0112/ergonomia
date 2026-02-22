import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# 1. CONFIGURAÇÃO DE PÁGINA
st.set_page_config(
    layout="wide", 
    page_title="Gestão Ergonômica Inteligente",
    initial_sidebar_state="collapsed"
)

# Configuração da IA (Sua chave direta)
genai.configure(api_key="AIzaSyCJ72jm7JfJKINgV9SjEALYdTwEGlM3FMU")
model = genai.GenerativeModel('gemini-1.5-flash')

def obter_sugestao_ia(setor, regiao, qtd):
    # Prompt mais robusto
    prompt = f"""
    Como especialista em SST e Ergonomia (NR-17), analise:
    No setor {setor}, há {qtd} queixas na região {regiao}.
    Dê 3 recomendações técnicas curtas e profissionais.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # Se der erro, mostra o motivo para podermos diagnosticar
        return f"IA indisponível no momento. (Log: {str(e)[:50]}...)"

# Estilo
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

# --- MAPEAMENTO SEGURO ---
df_base = df_raw.copy()
c_data = df_base.columns[0]   # Coluna A
c_dor = df_base.columns[4]    # Coluna E
c_local = df_base.columns[5]  # Coluna F
c_lider = df_base.columns[7]  # Coluna H (Liderança)
c_setor = df_base.columns[10] # Coluna K

# Tratamento de Data
df_base[c_data] = pd.to_datetime(df_base[c_data], dayfirst=True, errors='coerce')
df_base = df_base.dropna(subset=[c_data])
df_base["MesAno"] = df_base[c_data].dt.strftime('%Y-%m')

# --- FILTROS NA SIDEBAR ---
st.sidebar.header("🔍 Filtros")

# Filtro Meses
meses = sorted(df_base["MesAno"].unique().tolist(), reverse=True)
mes_sel = st.sidebar.selectbox("Período:", ["Todos"] + meses)

# Filtro Setores
df_base[c_setor] = df_base[c_setor].astype(str).str.strip().replace(['nan', 'None'], 'Geral')
lista_setores = sorted(list(set([x.strip() for s in df_base[c_setor].unique() for x in str(s).split(',') if x != 'Geral'])))
setor_sel = st.sidebar.selectbox("Setor:", ["Todos"] + lista_setores)

# NOVO: Filtro de Liderança Restaurado
lideres_lista = sorted([str(l) for l in df_base[c_lider].unique() if str(l).lower() != 'nan'])
lider_sel = st.sidebar.multiselect("Liderança:", lideres_lista)

# --- APLICAÇÃO DE FILTROS ---
df_f = df_base.copy()
if mes_sel != "Todos": 
    df_f = df_f[df_f["MesAno"] == mes_sel]
if setor_sel != "Todos": 
    df_f = df_f[df_f[c_setor].str.contains(setor_sel, na=False)]
if lider_sel:
    df_f = df_f[df_f[c_lider].astype(str).isin(lider_sel)]

# --- LAYOUT ---
st.title("🧍‍♂️ Ergonomia Inteligente")

k1, k2 = st.columns(2)
total = len(df_f)
df_sim = df_f[df_f[c_dor].astype(str).str.upper().str.contains("SIM")].copy()
taxa = (len(df_sim) / total * 100) if total > 0 else 0
k1.metric("Avaliações", total)
k2.metric("Índice de Queixas", f"{taxa:.1f}%")

st.markdown("---")

if not df_sim.empty:
    df_locais = df_sim[c_local].astype(str).str.split(',').explode().str.strip()
    df_contagem = df_locais.value_counts().reset_index()
    df_contagem.columns = ["Região", "Qtd"]
    df_contagem = df_contagem[df_contagem["Região"].astype(str).str.lower() != "nan"]
    
    if not df_contagem.empty:
        reg_topo = df_contagem.iloc[0]["Região"]
        qtd_topo = df_contagem.iloc[0]["Qtd"]

        # IA Dinâmica
        st.subheader("🤖 Sugestão Técnica da IA")
        with st.container():
            st.markdown(f'<div class="ia-card">{obter_sugestao_ia(setor_sel, reg_topo, qtd_topo)}</div>', unsafe_allow_html=True)

        # Gráfico
        fig = px.bar(df_contagem.sort_values("Qtd", ascending=True), 
                     x="Qtd", y="Região", orientation='h', text="Qtd",
                     color="Qtd", color_continuous_scale="Reds")
        fig.update_layout(height=450, margin=dict(l=0, r=10, t=10, b=10), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Nenhum registro encontrado para estes filtros.")

st.markdown(f'<div class="footer">© 2026 Gestão Ergonômica | Desenvolvido por <b>Dilceu Junior</b></div>', unsafe_allow_html=True)

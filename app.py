import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI

# 1. CONFIGURAÇÃO DE PÁGINA (Layout Mobile-First)
st.set_page_config(
    layout="wide", 
    page_title="Gestão Ergonômica Inteligente",
    initial_sidebar_state="collapsed"
)

# 2. CONFIGURAÇÃO DA IA (OPENAI)
# Se estiver no Streamlit Cloud, use st.secrets["OPENAI_API_KEY"] para mais segurança
client = OpenAI(api_key="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")

def obter_sugestao_chatgpt(setor, regiao, qtd):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um perito em Ergonomia e SST (NR-17)."},
                {"role": "user", "content": f"No setor {setor}, houve {qtd} queixas na região corporal {regiao}. Forneça 3 recomendações técnicas práticas e curtas baseadas na NR-17."}
            ],
            max_tokens=200
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"IA temporariamente indisponível. (Log: {str(e)[:40]}...)"

# Estilização Profissional
st.markdown("""
    <style>
        .stMetric { background-color: #ffffff; border: 1px solid #eee; padding: 10px; border-radius: 10px; }
        .ia-card { background-color: #f0fff4; border-left: 5px solid #28a745; padding: 15px; border-radius: 8px; margin: 10px 0; font-family: sans-serif; }
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
c_data, c_dor, c_local, c_lider, c_setor = df_base.columns[0], df_base.columns[4], df_base.columns[5], df_base.columns[7], df_base.columns[10]

# Tratamento de Data (Garante 2025 e 2026)
df_base[c_data] = pd.to_datetime(df_base[c_data], dayfirst=True, errors='coerce')
df_base = df_base.dropna(subset=[c_data])
df_base["MesAno"] = df_base[c_data].dt.strftime('%Y-%m')

# --- FILTROS (SIDEBAR) ---
st.sidebar.header("🔍 Filtros")

mes_sel = st.sidebar.selectbox("Mês:", ["Todos"] + sorted(df_base["MesAno"].unique().tolist(), reverse=True))

df_base[c_setor] = df_base[c_setor].astype(str).str.strip().replace(['nan', 'None'], 'Geral')
lista_setores = sorted(list(set([x.strip() for s in df_base[c_setor].unique() for x in str(s).split(',') if x not in ['Geral', 'nan']])))
setor_sel = st.sidebar.selectbox("Setor:", ["Todos"] + lista_setores)

# Filtro de Liderança (Douglas, Flavio, etc.)
lideres_lista = sorted([str(l).strip() for l in df_base[c_lider].unique() if str(l).lower() != 'nan' and str(l).strip() != ''])
lider_sel = st.sidebar.multiselect("Liderança:", lideres_lista)

# Aplicação dos Filtros
df_f = df_base.copy()
if mes_sel != "Todos": df_f = df_f[df_f["MesAno"] == mes_sel]
if setor_sel != "Todos": df_f = df_f[df_f[c_setor].str.contains(setor_sel, na=False)]
if lider_sel: df_f = df_f[df_f[c_lider].astype(str).str.strip().isin(lider_sel)]

# --- DASHBOARD ---
st.title("🧍‍♂️ Ergonomia Inteligente")

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
    
    # Bloco da IA (ChatGPT)
    st.subheader("🤖 Recomendação Técnica (IA)")
    reg_topo = df_contagem.iloc[0]["Região"]
    qtd_topo = df_contagem.iloc[0]["Qtd"]
    
    with st.spinner("ChatGPT analisando dados..."):
        sugestao = obter_sugestao_chatgpt(setor_sel, reg_topo, qtd_topo)
        st.markdown(f'<div class="ia-card">{sugestao}</div>', unsafe_allow_html=True)

    # Gráfico responsivo
    fig = px.bar(df_contagem.sort_values("Qtd", ascending=True), 
                 x="Qtd", y="Região", orientation='h', text="Qtd", color="Qtd", 
                 color_continuous_scale="Reds")
    fig.update_layout(height=450, margin=dict(l=0, r=10, t=10, b=10), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Nenhum registro crítico encontrado.")

st.markdown(f'<div class="footer">© 2026 Gestão Ergonômica | Desenvolvido por <b>Dilceu Junior</b></div>', unsafe_allow_html=True)

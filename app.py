import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# -----------------------------------------------------------
# CONFIGURAÇÃO DE PÁGINA & IA
# -----------------------------------------------------------
st.set_page_config(
    layout="wide", 
    page_title="Gestão Ergonômica Inteligente",
    initial_sidebar_state="collapsed"
)

# Configuração Segura da API (Tenta pegar do Streamlit Secrets ou usa a sua direta)
api_key = st.secrets.get("GEMINI_API_KEY", "AIzaSyCJ72jm7JfJKINgV9SjEALYdTwEGlM3FMU")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# Função para gerar recomendações técnicas dinâmicas
def obter_sugestao_ia(setor, regiao, qtd):
    prompt = f"""
    Como especialista em Ergonomia e SST (foco na NR-17), analise este cenário:
    No setor '{setor}', identificamos '{qtd}' queixas de dor/desconforto na região '{regiao}'.
    Forneça 3 sugestões técnicas práticas e imediatas para o Técnico de Segurança do Trabalho atuar neste local.
    Use linguagem profissional, cite a NR-17 se pertinente e seja conciso.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"IA temporariamente indisponível: {e}"

# Estilo CSS para o Bloco da IA e Layout
st.markdown("""
    <style>
        .stMetric { background-color: #ffffff; border: 1px solid #eee; padding: 15px; border-radius: 10px; }
        .ia-card {
            background-color: #f0f7ff;
            border-left: 6px solid #007bff;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 25px;
            font-family: 'Segoe UI', sans-serif;
        }
        .footer-text { text-align: center; color: #6c757d; font-size: 13px; margin-top: 50px; border-top: 1px solid #eee; padding-top: 20px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------
# CARREGAMENTO E MAPEAMENTO (COLUNA A - HISTÓRICO COMPLETO)
# -----------------------------------------------------------
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

# Mapeamento Seguro
df_base = df_raw.copy()
c_data_hora = df_base.columns[0]
c_sentindo_dor = df_base.columns[4]
c_local_dor = df_base.columns[5]
c_lider = df_base.columns[7]
c_setor = df_base.columns[10]

# Tratamento de Data (Garante 2025 e 2026 da Coluna A)
df_base[c_data_hora] = pd.to_datetime(df_base[c_data_hora], dayfirst=True, errors='coerce')
df_base = df_base.dropna(subset=[c_data_hora])
df_base["MesAno"] = df_base[c_data_hora].dt.strftime('%Y-%m')

# -----------------------------------------------------------
# SIDEBAR & FILTROS
# -----------------------------------------------------------
st.sidebar.header("🔍 Painel de Controle")

lista_meses = sorted(df_base["MesAno"].unique().tolist(), reverse=True)
mes_sel = st.sidebar.selectbox("Filtrar Mês:", ["Todos os Meses"] + lista_meses)

df_base[c_setor] = df_base[c_setor].astype(str).str.strip().replace(['nan', 'None'], 'Não Informado')
lista_setores = sorted(list(set([x.strip() for s in df_base[c_setor].unique() for x in str(s).split(',') if x != 'Não Informado'])))
setor_sel = st.sidebar.selectbox("Filtrar Setor:", ["Todos os Setores"] + lista_setores)

# -----------------------------------------------------------
# APLICAÇÃO DOS FILTROS
# -----------------------------------------------------------
df_f = df_base.copy()
if mes_sel != "Todos os Meses": df_f = df_f[df_f["MesAno"] == mes_sel]
if setor_sel != "Todos os Setores": df_f = df_f[df_f[c_setor].str.contains(setor_sel, na=False)]

# -----------------------------------------------------------
# DASHBOARD PRINCIPAL
# -----------------------------------------------------------
st.title("🧍‍♂️ Monitoramento Ergonômico Inteligente")
st.caption(f"Dados atualizados de 2025 e 2026 | Setor: {setor_sel}")

# KPIs
total_resp = len(df_f)
df_sim = df_f[df_f[c_sentindo_dor].astype(str).str.upper().str.contains("SIM")].copy()
total_dor = len(df_sim)
taxa = (total_dor / total_resp * 100) if total_resp > 0 else 0

k1, k2, k3 = st.columns(3)
k1.metric("Total Avaliados", total_resp)
k2.metric("Queixas de Dor", total_dor)
k3.metric("Índice Crítico", f"{taxa:.1f}%")

st.markdown("---")

if not df_sim.empty:
    # Identifica região crítica
    df_locais = df_sim[c_local_dor].astype(str).str.split(',').explode().str.strip()
    df_contagem = df_locais.value_counts().reset_index()
    df_contagem.columns = ["Região", "Qtd"]
    regiao_topo = df_contagem.iloc[0]["Região"]
    qtd_topo = df_contagem.iloc[0]["Qtd"]

    # --- BLOCO DE IA DINÂMICA ---
    with st.spinner("IA analisando dados técnicos..."):
        sugestao_tecnica = obter_sugestao_ia(setor_sel, regiao_topo, qtd_topo)
    
    st.markdown(f"""
        <div class="ia-card">
            <h4 style="margin-top:0;">🤖 Recomendação Estratégica da IA</h4>
            {sugestao_tecnica}
        </div>
    """, unsafe_allow_html=True)

    # Gráfico
    fig = px.bar(df_contagem.sort_values("Qtd", ascending=True), 
                 x="Qtd", y="Região", orientation='h', text="Qtd", 
                 color="Qtd", color_continuous_scale="Reds", template="plotly_white")
    fig.update_layout(height=450, margin=dict(l=0, r=10, t=10, b=10), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Nenhuma queixa de dor encontrada para o filtro selecionado.")

# RODAPÉ
st.markdown(f"""
    <div class="footer-text">
        © 2026 Gestão Ergonômica Inteligente | Desenvolvido por <b>Dilceu Junior</b><br>
        Técnico em Segurança do Trabalho
    </div>
""", unsafe_allow_html=True)

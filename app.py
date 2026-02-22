import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURAÇÃO DE PÁGINA (Layout Responsivo)
st.set_page_config(
    layout="wide",
    page_title="Gestão Ergonômica Inteligente",
    initial_sidebar_state="collapsed"
)

# Estilo para melhorar visual no celular
st.markdown("""
    <style>
        .stMetric {
            background-color: #ffffff;
            border: 1px solid #eee;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .footer-text {
            text-align: center;
            color: #6c757d;
            padding: 20px;
            font-size: 13px;
            margin-top: 30px;
            border-top: 1px solid #eee;
        }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_data():
    try:
        sheet_id = "1du_b9wsAlgvhrjyY0ts9x3Js_4FWDbWujRvi6PKMGEQ"
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(url)
        # Limpa espaços nos nomes das colunas
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

df_raw = load_data()

if df_raw.empty:
    st.stop()

# --- PROCESSAMENTO SEGURO (Evita o AttributeError) ---
df_base = df_raw.copy()

# Mapeamento por posição (mais seguro)
c_data_hora = df_base.columns[0]
c_sentindo_dor = df_base.columns[4]  # Coluna E
c_local_dor = df_base.columns[5]     # Coluna F
c_lider = df_base.columns[7]         # Coluna H
c_setor = df_base.columns[10]        # Coluna K

# Tratamento de Data (Garante 2025 e 2026)
df_base[c_data_hora] = pd.to_datetime(df_base[c_data_hora], dayfirst=True, errors='coerce')
df_base = df_base.dropna(subset=[c_data_hora])
df_base["MesAno"] = df_base[c_data_hora].dt.strftime('%Y-%m')

# --- INTERFACE DE FILTROS (SIDEBAR para ganhar espaço no celular) ---
st.sidebar.header("🔍 Filtros")

meses = sorted(df_base["MesAno"].unique().tolist(), reverse=True)
mes_sel = st.sidebar.selectbox("Selecione o Mês:", ["Todos os Meses"] + meses)

# Tratamento de Setores (Separa Laminação e GDR corretamente)
df_base[c_setor] = df_base[c_setor].astype(str).str.strip().replace(['nan', 'None'], 'Não Informado')
lista_setores_unica = []
for s in df_base[c_setor].unique():
    if s != "Não Informado":
        lista_setores_unica.extend([x.strip() for x in s.split(',')])
lista_setores_unica = sorted(list(set(lista_setores_unica)))

setor_sel = st.sidebar.selectbox("Selecione o Setor:", ["Todos os Setores"] + lista_setores_unica)

lideres = sorted([str(l) for l in df_base[c_lider].unique() if str(l).lower() != 'nan'])
lider_sel = st.sidebar.multiselect("Liderança:", lideres)

# --- FILTRAGEM ---
df_f = df_base.copy()

if mes_sel != "Todos os Meses":
    df_f = df_f[df_f["MesAno"] == mes_sel]

if setor_sel != "Todos os Setores":
    # Filtro flexível para encontrar o setor mesmo se estiver em lista (ex: "Laminação, GDR")
    df_f = df_f[df_f[c_setor].str.contains(setor_sel, na=False)]

if lider_sel:
    df_f = df_f[df_f[c_lider].astype(str).isin(lider_sel)]

# --- DASHBOARD PRINCIPAL ---
st.title("🧍‍♂️ Ergonomia Inteligente")

# KPIs que se ajustam ao celular
k1, k2 = st.columns(2)
total_resp = len(df_f)
df_sim = df_f[df_f[c_sentindo_dor].astype(str).str.upper().str.contains("SIM")].copy()
total_dor = len(df_sim)
taxa = (total_dor / total_resp * 100) if total_resp > 0 else 0

k1.metric("Total Avaliados", total_resp)
k2.metric("Taxa de Queixas", f"{taxa:.1f}%")

st.markdown("---")

if df_sim.empty:
    st.info("Nenhum registro de dor encontrado para estes filtros.")
else:
    # Contagem das dores
    df_locais = df_sim[c_local_dor].astype(str).str.split(',').explode().str.strip()
    df_contagem = df_locais.value_counts().reset_index()
    df_contagem.columns = ["Região", "Qtd"]
    df_contagem = df_contagem[df_contagem["Região"].str.lower() != "nan"]

    # Gráfico responsivo
    st.subheader(f"Regiões Críticas - {setor_sel}")
    fig = px.bar(
        df_contagem.sort_values("Qtd", ascending=True),
        x="Qtd", y="Região", orientation='h',
        text="Qtd", color="Qtd",
        color_continuous_scale="Reds", template="plotly_white"
    )
    fig.update_layout(height=500, margin=dict(l=0, r=10, t=10, b=10), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Ver Detalhamento em Tabela"):
        st.dataframe(df_contagem, hide_index=True, use_container_width=True)

# RODAPÉ
st.markdown(f"""
    <div class="footer-text">
        © 2026 Gestão Ergonômica | <b>Dilceu Junior</b><br>
        Consultoria em Segurança do Trabalho
    </div>
""", unsafe_allow_html=True)

import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------
# CONFIGURAÇÃO DE PÁGINA
# -----------------------------------------------------------
st.set_page_config(layout="wide", page_title="Monitoramento Ergonômico", initial_sidebar_state="collapsed")
st.title("🧍‍♂️ Monitoramento Ergonômico")

# Esconde menus nativos do Streamlit
st.markdown("<style>[data-testid='stSidebarNav'] {display: none;} [data-testid='collapsedControl'] {display: none;}</style>", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_data():
    try:
        # Link da planilha pública
        sheet_id = "1du_b9wsAlgvhrjyY0ts9x3Js_4FWDbWujRvi6PKMGEQ"
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(url)
        # Limpa espaços em branco nos nomes das colunas
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        return pd.DataFrame()

df_bruto = load_data()

if df_bruto.empty:
    st.warning("Aguardando carregamento dos dados...")
    st.stop()

# -----------------------------------------------------------
# MAPEAMENTO POR POSIÇÃO (GARANTE ESTABILIDADE)
# -----------------------------------------------------------
# Conforme a estrutura da sua planilha:
# 0: Carimbo | 2: Setor | 3: Liderança | 4: Resposta Sim/Não | 5: Local da Dor
cols = df_bruto.columns.tolist()
c_data = cols[0]
c_setor = cols[10] if len(cols) > 10 else cols[2] # Tenta coluna K ou C conforme prints
c_lider = cols[7] if len(cols) > 7 else cols[3]   # Tenta coluna H ou D
c_sentindo_dor = cols[4]
c_local_dor = cols[5]

# Criar DataFrame de trabalho
df = df_bruto.copy()

# 1. Tratamento de Datas (Pega 2025 e 2026)
df[c_data] = pd.to_datetime(df[c_data], dayfirst=True, errors='coerce')
df['MesAno'] = df[c_data].dt.strftime('%Y-%m').fillna("Data Inválida")

# 2. Tratamento de Setores (Separa Lâminaçao, GDR)
df[c_setor] = df[c_setor].astype(str).replace(['nan', 'None'], 'Não Informado').str.strip()
df_exp = df.copy()
df_exp[c_setor] = df_exp[c_setor].str.split(',')
df_exp = df_exp.explode(c_setor)
df_exp[c_setor] = df_exp[c_setor].str.strip()

# -----------------------------------------------------------
# INTERFACE DE FILTROS (DADOS COMPLETOS)
# -----------------------------------------------------------
col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    # Mostra todos os meses de 2025 e 2026
    lista_meses = sorted([m for m in df['MesAno'].unique() if m != "Data Inválida"], reverse=True)
    mes_sel = st.selectbox("Selecione o Mês:", ["Todos os Meses"] + lista_meses)

with col_f2:
    # Mostra todos os setores individualmente
    lista_setores = sorted([s for s in df_exp[c_setor].unique() if s != "Não Informado"])
    setor_sel = st.selectbox("Selecione o Setor:", ["Todos os Setores"] + lista_setores)

with col_f3:
    # Mostra todas as lideranças
    lista_lideres = sorted([l for l in df[c_lider].astype(str).unique() if l.lower() != 'nan'])
    lider_sel = st.multiselect("Selecione a(s) Liderança(s):", lista_lideres)

# -----------------------------------------------------------
# FILTRAGEM FINAL E REGRA DE NEGÓCIO
# -----------------------------------------------------------
df_f = df_exp.copy()

if mes_sel != "Todos os Meses":
    df_f = df_f[df_f['MesAno'] == mes_sel]

if setor_sel != "Todos os Setores":
    df_f = df_f[df_f[c_setor] == setor_sel]

if lider_sel:
    df_f = df_f[df_f[c_lider].astype(str).isin(lider_sel)]

# REGRA: O gráfico só contabiliza se a resposta na coluna E for "Sim"
df_grafico = df_f[df_f[c_sentindo_dor].astype(str).str.upper().str.contains("SIM")].copy()

# -----------------------------------------------------------
# VISUALIZAÇÃO (GRÁFICO DE BARRAS)
# -----------------------------------------------------------
st.subheader(f"📊 Queixas por Região - {setor_sel}")

if df_grafico.empty:
    st.info("Nenhum registro de dor encontrado para os filtros selecionados.")
else:
    # Contabiliza locais da coluna F
    df_locais = df_grafico[c_local_dor].astype(str).str.split(',').explode().str.strip()
    df_contagem = df_locais.value_counts().reset_index()
    df_contagem.columns = ["Região Corporal", "Quantidade"]
    df_contagem = df_contagem[df_contagem["Região Corporal"].str.lower() != "nan"]

    c_chart, c_table = st.columns([0.7, 0.3])
    
    with c_chart:
        fig = px.bar(
            df_contagem.sort_values("Quantidade", ascending=True), 
            x="Quantidade", y="Região Corporal", orientation='h',
            text="Quantidade", color="Quantidade", color_continuous_scale="Reds"
        )
        fig.update_layout(height=500, margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with c_table:
        st.dataframe(df_contagem, hide_index=True, use_container_width=True)

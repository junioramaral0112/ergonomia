import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuração Inicial
st.set_page_config(layout="wide", page_title="Monitoramento Ergonômico", initial_sidebar_state="collapsed")
st.title("🧍‍♂️ Monitoramento Ergonômico")

@st.cache_data(ttl=60)
def load_data():
    try:
        sheet_id = "1du_b9wsAlgvhrjyY0ts9x3Js_4FWDbWujRvi6PKMGEQ"
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        return pd.DataFrame()

df_original = load_data()

if df_original.empty:
    st.warning("Aguardando carregamento dos dados...")
    st.stop()

# -----------------------------------------------------------
# MAPEAMENTO POR POSIÇÃO (BASEADO NO SEU PRINT DA PLANILHA)
# -----------------------------------------------------------
# Coluna 0 (A): Carimbo de data/hora
# Coluna 4 (E): Hoje, você está sentindo alguma dor...
# Coluna 5 (F): Se SIM, indique o local da dor:
# Coluna 7 (H): Liderança
# Coluna 10 (K): Setor:
# -----------------------------------------------------------
df_base = df_original.copy()

# Tratamento de Datas (Garante que Fevereiro 2026 e 2025 apareçam)
df_base.iloc[:, 0] = pd.to_datetime(df_base.iloc[:, 0], dayfirst=True, errors='coerce')
df_base = df_base.dropna(subset=[df_base.columns[0]])
df_base["MesAno"] = df_base.iloc[:, 0].dt.strftime('%Y-%m')

# Tratamento de Setores (Separa Laminação e GDR)
col_setor_nome = df_base.columns[10]
df_base[col_setor_nome] = df_base.iloc[:, 10].astype(str).str.strip().replace(['nan', 'None'], 'Não Informado')

# -----------------------------------------------------------
# INTERFACE DE FILTROS (USA O DF_BASE ANTES DO FILTRO "SIM")
# -----------------------------------------------------------
c1, c2, c3 = st.columns(3)

with c1:
    # Pega todos os meses antes de filtrar quem sentiu dor
    lista_meses = sorted(df_base["MesAno"].unique().tolist(), reverse=True)
    mes_sel = st.selectbox("Selecione o Mês:", ["Todos os Meses"] + lista_meses)

with c2:
    # Pega todos os setores antes de filtrar quem sentiu dor
    # Faz o split para separar "Lâminaçao, GDR"
    todos_setores = []
    for s in df_base.iloc[:, 10].unique():
        if s and s != "Não Informado":
            todos_setores.extend([p.strip() for p in str(s).split(',')])
    setores_lista = sorted(list(set(todos_setores)))
    setor_sel = st.selectbox("Selecione o Setor:", ["Todos os Setores"] + setores_lista)

with c3:
    col_lider_nome = df_base.columns[7]
    lideres = sorted([l for l in df_base.iloc[:, 7].astype(str).unique() if l.lower() != 'nan'])
    lider_sel = st.multiselect("Selecione a(s) Liderança(s):", lideres)

# -----------------------------------------------------------
# APLICAÇÃO DOS FILTROS
# -----------------------------------------------------------
df_f = df_base.copy()

if mes_sel != "Todos os Meses":
    df_f = df_f[df_f["MesAno"] == mes_sel]

if setor_sel != "Todos os Setores":
    # Filtra o setor mesmo que esteja em uma célula com outros (ex: "Lâminaçao, GDR")
    df_f = df_f[df_f.iloc[:, 10].astype(str).str.contains(setor_sel, na=False)]

if lider_sel:
    df_f = df_f[df_f.iloc[:, 7].astype(str).isin(lider_sel)]

# -----------------------------------------------------------
# GRÁFICO (REGRAS: APENAS RESPOSTAS "SIM" NA COLUNA E)
# -----------------------------------------------------------
st.subheader(f"📊 Queixas por Região - {setor_sel}")

# Filtra apenas quem marcou "Sim" na coluna 4 (Coluna E)
df_grafico = df_f[df_f.iloc[:, 4].astype(str).str.upper().str.contains("SIM")].copy()

if df_grafico.empty:
    st.info("Nenhum registro de dor encontrado para estes filtros.")
else:
    # Processa os locais da coluna 5 (Coluna F)
    df_locais = df_grafico.iloc[:, 5].astype(str).str.split(',')
    df_locais = df_locais.explode().str.strip()
    df_contagem = df_locais.value_counts().reset_index()
    df_contagem.columns = ["Região", "Quantidade"]
    df_contagem = df_contagem[df_contagem["Região"].str.lower() != "nan"]

    col_chart, col_table = st.columns([0.7, 0.3])
    with col_chart:
        fig = px.bar(df_contagem.sort_values("Quantidade", ascending=True), 
                     x="Quantidade", y="Região", orientation='h', 
                     text="Quantidade", color="Quantidade", color_continuous_scale="Reds")
        fig.update_layout(height=500, margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with col_table:
        st.dataframe(df_contagem, hide_index=True, use_container_width=True)

import streamlit as st
import pandas as pd
import time
import sys
import os

# Adjust so Python finds the 'processing' folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from processing.data_handler import DataProcessor

# Page configuration
st.set_page_config(
    page_title="Bombeiros - 2ª CIA Passos",
    page_icon="🚒",
    layout="wide",
)

# Custom CSS for Fire Department branding
st.markdown("""
    <style>
    .stButton>button { width: 100%; background-color: #d32f2f; color: white; border-radius: 5px; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

def main():
    # Initialize Data Processor
    processor = DataProcessor()

    # Header
    st.title("🚒 Gestão de Ocorrências - 2ª CIA Passos")
    st.divider()

    # Sidebar
    st.sidebar.header("📍 Localidade")
    st.sidebar.info("Unidade: 2ª CIA - PASSOS")
    
    # Navigation Tabs (Variable names in English, Labels in Portuguese)
    extraction_tab, processing_tab, dashboard_tab = st.tabs([
        "📥 Extração (CAD)", 
        "⚙️ Processamento (Medalhão)", 
        "📊 Visualização"
    ])

    # --- TAB 1: EXTRACTION ---
    with extraction_tab:
        st.subheader("Extração de Dados do Sistema CAD")
        st.write("Acione o script para realizar o download automático do CSV no sistema JAVA.")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("Iniciar Extração"):
                with st.status("Executando automação...", expanded=True) as status:
                    st.write("Acessando sistema CAD...")
                    time.sleep(1.5)
                    st.write("Baixando dados brutos...")
                    time.sleep(1.0)
                    status.update(label="Download concluído!", state="complete")
                st.success("Arquivo CSV disponível na pasta '01_bronze'.")

    # --- TAB 2: PROCESSING ---
    with processing_tab:
        st.subheader("Pipeline de Dados (Arquitetura Medalhão)")
        st.info("Este módulo transforma os dados brutos (2018-2026) em tabelas prontas para análise.")
        
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        metric_col1.metric("Camada Bronze", "Dados Brutos")
        metric_col2.metric("Camada Prata", "Dados Limpos")
        metric_col3.metric("Camada Ouro", "Dados Consolidados")

        st.divider()

        # Action 1: Consolidate Historical Data (The folders 2018, 2019...)
        st.write("### 📂 Processamento Histórico")
        if st.button("Unificar Histórico (2018 - 2026)"):
            try:
                with st.spinner("Lendo subpastas e consolidando arquivos..."):
                    df_master = processor.consolidate_historical_data()
                st.success(f"Sucesso! {len(df_master)} registros unificados em 'master_historic_silver.csv'.")
                st.dataframe(df_master.head(20), width="stretch")
            except Exception as e:
                st.error(f"Erro ao consolidar histórico: {e}")

        st.divider()

        # Action 2: Process a single file (Incremental) (ONLY TESTING)
        st.write("### 📄 Processamento Individual")
        if st.button("Rodar Processamento Individual (Bronze -> Silver)"):
            try:
                filename = "master_historic_silver.csv" 
                with st.spinner("Limpando dados..."):
                    df_silver = processor.process_bronze_to_silver(filename)
                st.success("Arquivo individual processado.")
                st.dataframe(df_silver.head(10), width="stretch")
            except FileNotFoundError:
                st.error("Arquivo 'master_historic_silver.csv' não encontrado.")
            except Exception as e:
                st.error(f"Erro inesperado: {e}")

    # --- TAB 3: DASHBOARD ---
    with dashboard_tab:
        st.subheader("Indicadores de Ocorrências")
        st.write("Gráficos baseados nos dados processados.")
        
        # Placeholder chart
        chart_data = pd.DataFrame({
            "Mês": ["Jan", "Fev", "Mar", "Abr"],
            "Ocorrências": [45, 32, 58, 41]
        })
        st.area_chart(chart_data.set_index("Mês"), color="#d32f2f")

if __name__ == "__main__":
    main()
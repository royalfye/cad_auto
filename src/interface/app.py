import os
import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st

# --- PATH CONFIGURATION ---
current_dir = Path(__file__).resolve().parent  # cad-auto/src/interface
src_root = current_dir.parent                 # cad-auto/src
project_root = src_root.parent                # cad-auto

if str(src_root) not in sys.path:
    sys.path.append(str(src_root))

BRONZE_DIR = project_root / "data" / "01_bronze"
SILVER_DIR = project_root / "data" / "02_silver"

# Importamos a CLASSE agora, seguindo a boa prática de encapsulamento
from bot.cad_bot import CADAutomationBot
from processing.data_handler import DataProcessor

# --- UI CONSTANTS ---
FIRE_DEPT_RED = "#d32f2f"

def apply_custom_styles():
    """Applies Fire Department branding via CSS."""
    st.markdown(f"""
        <style>
        .stButton>button {{ 
            width: 100%; 
            background-color: {FIRE_DEPT_RED}; 
            color: white; 
            border-radius: 5px; 
        }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 24px; }}
        .stTabs [data-baseweb="tab"] {{ 
            height: 50px; 
            white-space: pre-wrap; 
            font-weight: bold; 
        }}
        </style>
        """, unsafe_allow_html=True)

def main():
    # Initialization
    st.set_page_config(
        page_title="Bombeiros - 2ª CIA Passos",
        page_icon="🚒",
        layout="wide",
    )
    apply_custom_styles()
    
    # Instanciamos os objetos necessários
    processor = DataProcessor()
    bot = CADAutomationBot()

    # Sidebar & Header
    st.title("🚒 Gestão de Ocorrências - 2ª CIA Passos")
    st.sidebar.header("📍 Localidade")
    st.sidebar.info("Unidade: 2ª CIA - PASSOS")
    st.divider()

    # Tabs definition
    extraction_tab, processing_tab, dashboard_tab = st.tabs([
        "📥 Extração (CAD)", 
        "⚙️ Processamento (Medalhão)", 
        "📊 Visualização"
    ])

# --- TAB 1: EXTRACTION ---
    with extraction_tab:
        st.subheader("Extração Automatizada")
        
        if st.button("Iniciar Extração"):
            # Criamos o arquivo de destino aqui (única info que a interface gera)
            timestamp = int(time.time())
            bronze_file_path = BRONZE_DIR / f"raw_export_{timestamp}.csv"

            with st.status("Executando automação CAD...", expanded=True) as status:
                # Chamamos o mestre: o bot assume o controle
                success = bot.run_full_extraction_flow(bronze_file_path, status)
                
                if success:
                    status.update(label="Extração Completa!", state="complete")
                    st.success(f"Dados salvos com sucesso: {bronze_file_path.name}")
                else:
                    status.update(label="Falha na Extração", state="error")
                    st.error("Ocorreu um erro durante o processo. Verifique os logs.")

    # --- TAB 2: PROCESSING ---
    with processing_tab:
        st.subheader("Pipeline de Dados")
        
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("Bronze", "Dados Brutos")
        m_col2.metric("Silver", "Dados Limpos")
        m_col3.metric("Gold", "Consolidados")
        st.divider()

        st.write("### 📂 Consolidação Histórica")
        if st.button("Unificar Histórico (2018 - 2026)"):
            try:
                with st.spinner("Processando pastas..."):
                    df_master = processor.consolidate_historical_data()
                st.success(f"Unificação concluída: {len(df_master)} registros.")
                st.dataframe(df_master.head(20), use_container_width=True)
            except Exception as e:
                st.error(f"Erro na consolidação: {e}")

        st.divider()
        st.write("### 🔍 Inspeção da Camada Silver")
        master_silver = processor.silver_path / "master_historic_silver.csv"
        
        if master_silver.exists():
            if st.button("Visualizar Dados Consolidados"):
                df_view = pd.read_csv(master_silver)
                st.write(f"Total: {df_view.shape[0]} linhas.")
                st.dataframe(df_view, use_container_width=True)
        else:
            st.warning("Arquivo 'master_historic_silver.csv' não encontrado.")

    # --- TAB 3: DASHBOARD ---
    with dashboard_tab:
        st.subheader("Indicadores")
        chart_data = pd.DataFrame({
            "Mês": ["Jan", "Fev", "Mar", "Abr"],
            "Ocorrências": [45, 32, 58, 41]
        }).set_index("Mês")
        st.area_chart(chart_data, color=FIRE_DEPT_RED)

if __name__ == "__main__":
    main()
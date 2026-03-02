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
        st.subheader("Extração Automatizada de Ocorrências")
        st.info("Selecione o tipo de extração desejada. Certifique-se de que o CAD está aberto.")

        col_hist, col_act = st.columns(2)

        with col_hist:
            st.write("### 📜 Dados Históricos")
            st.caption("Extrai chamadas classificadas dos últimos 3 meses.")
            if st.button("🚀 Sincronizar Histórico", key="btn_hist"):
                with st.status("Executando extração histórica...", expanded=True) as status:
                    # Passamos a raiz da bronze
                    success = bot.run_full_extraction_flow(processor.bronze_path, status)
                    if success:
                        status.update(label="Histórico Sincronizado!", state="complete")
                        st.success("Dados salvos em bronze/historical/")
                    else:
                        status.update(label="Falha no Processo", state="error")

        with col_act:
            st.write("### 🚨 Chamadas Ativas")
            st.caption("Extrai as ocorrências em andamento (Tempo Real).")
            if st.button("🔴 Monitorar Ativas", key="btn_active"):
                with st.status("Capturando chamadas em aberto...", expanded=True) as status:
                    success = bot.run_active_extraction_flow(processor.bronze_path, status)
                    if success:
                        status.update(label="Ativas Capturadas!", state="complete")
                        st.success("Dados salvos em bronze/active/")
                    else:
                        status.update(label="Falha na Captura", state="error")
# --- TAB 2: PROCESSING ---
    with processing_tab:
        st.subheader("Pipeline de Dados")
        
        # Métricas dinâmicas (Exemplo de como deixar sênior)
        m_col1, m_col2, m_col3 = st.columns(3)
        
        # Contagem de arquivos na bronze
        bronze_files_count = len(list(BRONZE_DIR.glob("*.csv")))
        m_col1.metric("Arquivos na Bronze", bronze_files_count)
        m_col2.metric("Camada Silver", "Standardized")
        m_col3.metric("Camada Gold", "Ready")
        
        st.divider()

        st.write("### 📂 Gerenciamento do Histórico")
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("Force Re-sync (Bronze -> Silver)"):
                with st.spinner("Reprocessando todo o histórico..."):
                    df_master = processor.consolidate_historical_data()
                    st.success(f"Sincronização concluída: {len(df_master)} registros.")

        st.divider()
        st.write("### 🔍 Inspeção da Camada Silver")
        
        # Em vez de ler o CSV aqui, usamos o processor
        master_silver_path = SILVER_DIR / "master_historic_silver.csv"
        
        if master_silver_path.exists():
            if st.button("Visualizar Tabela Master"):
                # O ideal é criar um método processor.load_silver_data() no futuro
                df_view = pd.read_csv(master_silver_path)
                st.write(f"Exibindo {df_view.shape[0]} registros únicos.")
                st.dataframe(df_view, width='stretch') # Corrigido para 'stretch'
        else:
            st.warning("A base unificada ainda não foi gerada. Inicie uma extração ou force a sincronização.")

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
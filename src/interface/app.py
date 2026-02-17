import os
import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st

# --- PATH CONFIGURATION ---
current_dir = Path(__file__).resolve().parent
src_root = current_dir.parent
if str(src_root) not in sys.path:
    sys.path.append(str(src_root))

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
            with st.status("Preparando ambiente...", expanded=True) as status:
                # Ação 1: Fechar Excel
                st.write("Encerrando processos do Excel...")
                count = bot.close_excel_processes()
                msg = f"Encerradas {count} instâncias." if count > 0 else "Nenhuma instância aberta."
                st.write(msg)
                
                # Ação 2: Focar Janela do CAD
                st.write("Localizando janela do sistema CAD...")
                time.sleep(1)
                
                if bot.focus_cad_window():
                    st.write("✅ Janela do CAD localizada e focada.")
                    status.update(label="Ambiente Pronto!", state="complete")
                    st.success("O sistema está pronto. Proceda com a extração manual ou automática no CAD.")
                else:
                    status.update(label="Erro na Localização", state="error")
                    st.error("Certifique-se de que o CAD está aberto com o título correto.")

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
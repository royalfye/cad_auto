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
            with st.status("Preparando ambiente...", expanded=True) as status:
                
                # Action 1: Terminate Excel processes
                st.write("Encerrando processos do Excel...")
                count = bot.close_excel_processes()
                msg = f"Encerradas {count} instâncias." if count > 0 else "Nenhuma instância aberta."
                st.write(msg)
                
                # Action 2: Focus and Prepare CAD Window
                st.write("Localizando e focando janela do sistema CAD...")
                time.sleep(1)
                
                if not bot.focus_cad_window():
                    status.update(label="Erro na Localização", state="error")
                    st.error("Certifique-se de que o CAD está aberto com o título correto.")
                    st.stop() # Stops Streamlit execution here if failed

                st.write("✅ Janela do CAD localizada.")
                
                # Action 3: Step 01 - Verify Call Filter
                st.write("Verificando Filtro de Chamadas...")
                if not bot.check_passos_filter():
                    status.update(label="Ação Manual Requerida", state="error")
                    st.error("Filtro incorreto! Selecione 'PASSOS' no CAD e tente novamente.")
                    st.stop()

                st.write("✅ Filtro 'PASSOS' confirmado.")
                
                # Action 4: Step 02 - Click Calls Module
                st.write("Acessando módulo de chamadas...")
                if not bot.click_calls_button():
                    status.update(label="Erro na Navegação", state="error")
                    st.error("Não foi possível encontrar o botão de chamadas (02).")
                    st.stop()

                st.write("✅ Módulo de chamadas aberto.")
                time.sleep(1.5) # Wait for Java UI rendering
                
                # Action 5: Step 03 - Open Search Tool
                st.write("Abrindo ferramenta de pesquisa...")
                if not bot.click_search_button():
                    status.update(label="Erro na Pesquisa", state="error")
                    st.error("Não foi possível encontrar o botão de pesquisa (03).")
                    st.stop()

                st.write("✅ Janela de pesquisa aberta.")
                time.sleep(1)
                
                # Action 6: Step 04 - Select Classified Occurrences
                st.write("Selecionando ocorrências classificadas...")
                if not bot.click_classified_button():
                    status.update(label="Erro no Filtro", state="error")
                    st.error("Não foi possível localizar o botão de classificadas (04).")
                    st.stop()

                # Action 7: Step 05 - Select Last 24 Hours
                st.write("Selecionando filtro de últimas 24 horas...")
                if not bot.click_last_24h_button():
                    status.update(label="Erro no Filtro", state="error")
                    st.error("Não foi possível localizar o botão de 24h (05).")
                    st.stop()
                
                time.sleep(0.5) # Brief pause for UI feedback

                # Action 8: Step 06 - Select Last 3 Months
                st.write("Selecionando filtro de últimos 3 meses...")
                if not bot.click_last_3_months_button():
                    status.update(label="Erro no Filtro", state="error")
                    st.error("Não foi possível localizar o botão de 3 meses (06).")
                    st.stop()

                # Action 9: Steps 07 & 08 - City Filtering
                st.write("Filtrando ocorrências da cidade de Passos...")
                if not bot.filter_by_city_name("passos"):
                    status.update(label="Erro no Filtro de Cidade", state="error")
                    st.error("Falha ao digitar ou confirmar a cidade (07/08).")
                    st.stop()
                
                # Action 10: Step 09 - Exporting Data
                st.write("Solicitando exportação de dados...")
                time.sleep(1) # Wait for Java to process the list before export is available
                
                if not bot.click_export_button():
                    status.update(label="Erro na Exportação", state="error")
                    st.error("Não foi possível encontrar o botão de exportar (09).")
                    st.stop()

                st.write("Detectando planilha aberta e salvando na Bronze...")
                
                bronze_file_path = BRONZE_DIR / f"raw_export_{int(time.time())}.csv"

                if bot.save_excel_export(bronze_file_path):
                    st.write(f"✅ Arquivo salvo em: {bronze_file_path.name}")
                    status.update(label="Extração Completa!", state="complete")
                    st.success(f"Dados exportados com sucesso para a camada Bronze!")
                else:
                    status.update(label="Erro no Salvamento", state="error")
                    st.error("O Excel abriu, mas não conseguimos salvar o arquivo via código.")
                    st.stop()

                # Success State
                st.write("✅ Comando de exportação enviado.")
                status.update(label="Exportação Iniciada!", state="complete")
                st.success("O bot acionou a exportação. Aguardando janela de salvamento...")

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
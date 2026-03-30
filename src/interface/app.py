#1 - Imports
import os
import sys
import time
from pathlib import Path
import logging 
from datetime import datetime 

# Configuração básica para o logging aparecer no terminal com data e hora
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_AUTOSCREENSCALEFACTOR"] = "1"

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import webbrowser
import pandas as pd
from pynput import mouse, keyboard # Instale com: pip install pynput
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QProgressBar, QTableView, QTextEdit,
    QMessageBox
)
from PySide6.QtCore import Qt, QTimer

from src.bot.cad_bot import CADAutomationBot
from src.bot.history_bot import HistoryBot
from src.processing.data_handler import DataProcessor
from src.processing.services import (
    converter_dataframe_para_objetos, 
    generate_activity_report
)
from src.interface.styles import STYLE_SHEET, apply_light_theme
from src.interface.workers import AutomationWorker
from src.interface.sidebar import SideBar
from src.interface.table_model import OcorrenciaTableModel
from src.interface.components.active_table import ActiveCallsTable
from src.interface.components.summary_card import SummaryCard
from src.interface.components.header import HeaderSection
from src.processing.services import obter_nome_grupo_whatsapp
from src.bot.whatsapp_bot import WhatsAppBot
from src.bot.sentinel_worker import SentinelWorker

#2 - Class
class FireApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # 1. Inicialização de instâncias (Lógica de Negócio)
        self.processor = DataProcessor()
        self.bot = CADAutomationBot()
        
        # 2. Configurações da Janela Principal
        self._configure_window()
        
        # 3. Construção da Interface
        self._setup_ui()
        
        # 4. Inicialização de Modelos (Dados vazios para começar)
        self.model = None

        self.carregar_chamadas_ativas()

        self.header.play_toggled.connect(self.gerenciar_sentinela)
        self.sentinela_ativa = False

    def _configure_window(self):
        """Configurações básicas da janela principal."""
        self.setWindowTitle("Bombeiros - 2ª CIA Passos")
        self.resize(1200, 800)
        self.setStyleSheet(STYLE_SHEET)

    def _setup_ui(self):
        """Orquestra a montagem de todos os componentes visuais."""
        # Widget Central e Layout Principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.layout_geral = QHBoxLayout(main_widget)
        self.layout_geral.setContentsMargins(0, 0, 0, 0)
        self.layout_geral.setSpacing(0)

        # Inicializa Componentes
        self._create_sidebar()
        self._create_main_content_area()
        
        # Montagem Final
        self.layout_geral.addWidget(self.sidebar)
        self.layout_geral.addWidget(self.content_area)

    def _create_sidebar(self):
        """Cria e configura a barra lateral."""
        self.sidebar = SideBar(switch_page_callback=lambda: None)
        self.sidebar.btn_extracao.hide()
        self.sidebar.btn_process.hide()

    def _create_main_content_area(self):
        """Cria a área onde as tabelas e botões de ação ficam."""
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(20)

        # Adiciona a página de processamento
        self.monitor_page = self.create_processing_page() # Este método vamos refatorar no próximo passo
        self.content_layout.addWidget(self.monitor_page)

    def switch_page_dummy(self, index):
        """Função vazia apenas para evitar erros na Sidebar."""
        pass

    def gerenciar_sentinela(self, ativo):
        self.sentinela_ativa = ativo
        if ativo:
            self._update_status("🛰️ Sentinela Ativado: Monitorando CAD...")
            # Limpa qualquer thread resíduo antes de começar
            self.parar_loop_monitoramento()
            self.iniciar_loop_monitoramento()
        else:
            self.sentinela_ativa = False
            self.parar_loop_monitoramento()
            self._update_status("⚪ Sentinela Desativado.")

    def iniciar_loop_monitoramento(self):
        """Inicia o sentinela com trava de segurança para não duplicar."""
        # Se o botão foi desmarcado manualmente, não faz nada
        if not self.sentinela_ativa:
            return

        # Traz o CAD para frente
        if self.bot.focar_janela_cad():
            # Aguarda o Windows terminar de desenhar a janela
            QTimer.singleShot(1500, self._disparar_thread_sentinela)
        else:
            self._update_status("❌ CAD não encontrado. Tentando em 5s...")
            # Se não achou o CAD, tenta de novo em 5 segundos, mas só se ainda estiver ativo
            if self.sentinela_ativa:
                QTimer.singleShot(5000, self.iniciar_loop_monitoramento)

    def _disparar_thread_sentinela(self):
        if not self.sentinela_ativa: return
        
        # Cria a thread
        self.sentinel_thread = SentinelWorker()
        self.sentinel_thread.new_occurrence_detected.connect(self._reagir_a_nova_ocorrencia)
        self.sentinel_thread.finished_by_user.connect(self._on_sentinel_stopped)
        self.sentinel_thread.start()

    def parar_loop_monitoramento(self):
        """Para a thread de forma agressiva e limpa a memória."""
        if hasattr(self, 'sentinel_thread') and self.sentinel_thread:
            if self.sentinel_thread.isRunning():
                self.sentinel_thread.is_running = False
                self.sentinel_thread.quit()
                self.sentinel_thread.wait(2000) # Espera até 2 segundos
            self.sentinel_thread = None # Deleta a thread da memória

    def _on_sentinel_stopped(self, reason):
        """Callback para quando o sentinela para via hardware (mouse/ESC)."""
        self.sentinela_ativa = False
        # Força o botão do Header a voltar para o estado de "Play"
        self.header.is_monitoring = False
        self.header._toggle_state()
        self._update_status(f"⚪ Sentinela parado por: {reason}")

    

    def create_processing_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Instancia o novo componente
        self.header = HeaderSection()
        
        # CONEXÃO DOS BOTÕES (O "pulo do gato")
        # Como os botões agora estão dentro de 'self.header', acessamos assim:
        self.header.btn_history.clicked.connect(self.iniciar_busca_historico)
        self.header.btn_copy.clicked.connect(self.copiar_ocorrencia_selecionada)
        self.header.btn_send.clicked.connect(self.disparar_whatsapp_automático) 
        self.header.btn_sync.clicked.connect(self.run_active_sync)

        self.status_section = self._create_status_section()
        self.table_ativas = ActiveCallsTable()
        self.summary_card = SummaryCard()

        # Adição ao layout
        layout.addWidget(self.header) # Adiciona o componente direto como Widget
        layout.addWidget(self.status_section)
        layout.addWidget(self.table_ativas, 1)
        layout.addWidget(self.summary_card)

        return page

    def _create_status_section(self):
        """Cria a barra de progresso e mensagens de status."""
        self.status_frame = QFrame()
        self.status_frame.setObjectName("Card")
        self.status_frame.setVisible(False)
        
        layout = QVBoxLayout(self.status_frame)
        self.status_msg = QLabel("Pronto...")
        self.progress_bar = QProgressBar()
        
        layout.addWidget(self.status_msg)
        layout.addWidget(self.progress_bar)
        
        return self.status_frame

    def run_active_sync(self):
        """Inicia a sincronização de chamadas ativas com proteção contra erros."""
        try:
            self._start_automation_task(
                self.bot.run_active_extraction_flow, 
                self.processor.bronze_path
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro de Sincronização", f"Falha ao iniciar robô: {e}")

    def iniciar_busca_historico(self):
        """Gatilha o robô para buscar o histórico de todas as ocorrências marcadas."""
        if not self.model:
            return

        # 1. Filtramos todas as ocorrências que o usuário marcou com o "X"
        selecionadas = [oc for oc in self.model.ocorrencias if oc.selecionado]

        if not selecionadas:
            QMessageBox.warning(self, "Aviso", "Marque as caixas de seleção das ocorrências que deseja atualizar!")
            return

        # 2. Criamos uma função recursiva ou em loop para processar a fila
        self._processar_fila_historico(selecionadas)

    def _processar_fila_historico(self, fila):
        """Processa uma lista de ocorrências, uma por uma."""
        if not fila:
            self._update_status("✅ Todas as atualizações concluídas!")
            QMessageBox.information(self, "Sucesso", "Todas as ocorrências selecionadas foram atualizadas.")
            return

        # Pega a primeira ocorrência da fila
        ocorrencia_atual = fila.pop(0)
        call_id = ocorrencia_atual.id_chamada

        self._update_status(f"🤖 [{len(fila)+1} restantes] Buscando histórico: {call_id}")
        
        # Disparamos o Worker para esta ocorrência específica
        self.h_bot = HistoryBot()
        self.worker = AutomationWorker(self.h_bot.capturar_historico_por_id, call_id)
        
        # Quando ESTE terminar, ele chama automaticamente o próximo da fila
        self.worker.finished.connect(
            lambda success, result: self._on_batch_history_finished(success, result, ocorrencia_atual, fila)
        )
        self.worker.start()

    def _on_batch_history_finished(self, success, result, occurrence, fila):
        """Trata o resultado de uma ocorrência e pula para a próxima."""
        if success:
            occurrence.historico = result
            # Desmarca a caixa após processar com sucesso (opcional, melhora a UX)
            occurrence.selecionado = False 
            self.model.layoutChanged.emit()
        
        # Independente de sucesso ou erro nesta, tenta a próxima da fila
        self._processar_fila_historico(fila)

    def copiar_ocorrencia_selecionada(self):
        """Copia as ocorrências marcadas inserindo a Ala selecionada na Sidebar."""
        if not self.model:
            return

        # 1. Pegamos a Ala que está selecionada no ComboBox da Sidebar
        # O .currentText() pega exatamente o que o usuário está vendo (ex: "4ª ALA")
        ala_selecionada = self.sidebar.combo_ala.currentText()

        # 2. Filtramos as ocorrências marcadas com o "X"
        selecionadas = [oc for oc in self.model.ocorrencias if oc.selecionado]

        if not selecionadas:
            QMessageBox.warning(self, "Aviso", "Marque pelo menos uma ocorrência!")
            return

        try:
            # 3. Geramos o texto passando a ala_selecionada como argumento
            # Agora o método formatar_para_whatsapp(equipe=...) recebe o valor correto
            lista_textos = [
                oc.formatar_para_whatsapp(equipe=ala_selecionada) 
                for oc in selecionadas
            ]
            
            texto_final = "\n\n---\n\n".join(lista_textos)
            
            QApplication.clipboard().setText(texto_final)
            
            # Feedback visual
            self.header.btn_copy.setText(f"✅ {len(selecionadas)} Copiadas!")
            QTimer.singleShot(2000, lambda: self.header.btn_copy.setText("📋 Copiar para WhatsApp"))
            
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível copiar: {e}")

    # --- DATA & UI UPDATES (Atualização da Interface) ---

    def disparar_whatsapp_automático(self):
        selecionadas = [oc for oc in self.model.ocorrencias if oc.selecionado]
        if not selecionadas: return

        ala_sel = self.sidebar.combo_ala.currentText()
        # A função que você criou no services.py
        grupo_destino = obter_nome_grupo_whatsapp(ala_sel) 

        self.status_frame.setVisible(True)
        self._update_status(f"🚀 Disparando para {grupo_destino}...")

        # Instancia o bot do zap
        ws_bot = WhatsAppBot()
        
        for oc in selecionadas:
            texto = oc.formatar_para_whatsapp(equipe=ala_sel)
            # Chama o robô para digitar e enviar
            ws_bot.enviar_para_grupo(grupo_destino, texto)
            time.sleep(1) # Pausa entre múltiplos disparos

        self._update_status("✅ Disparos concluídos!")

    def carregar_chamadas_ativas(self):
        """Atualiza a tabela com os dados locais ou recém-sincronizados."""
        try:
            df = self.processor.process_latest_active_call()
            
            if df is not None and not df.empty:
                # 1. Prepara os dados
                lista_objetos = converter_dataframe_para_objetos(df)
                self.model = OcorrenciaTableModel(lista_objetos)
                
                # 2. Distribui para os componentes
                report_text = generate_activity_report(df)
                self.summary_card.update_text(report_text)
                self.table_ativas.update_data(self.model)
                
                # --- O PULO DO GATO ---
                # Antes de conectar, tentamos desconectar conexões antigas para não duplicar
                try:
                    self.table_ativas.clicked.disconnect()
                except Exception:
                    # Se não houver conexão para desconectar, ele apenas segue
                    pass
                
                # Agora conectamos o clique ao novo modelo carregado
                self.table_ativas.clicked.connect(self._toggle_row_checkbox)
                # ----------------------

                self._update_status("📂 Dados atualizados com sucesso.")
            else:
                self._update_status("ℹ️ Nenhuma planilha encontrada. Sincronize com o CAD.")
                
        except Exception as e:
            self._update_status(f"❌ Erro ao carregar dados: {e}")

    def _update_status(self, message):
        """Método auxiliar para atualizar a barra de status."""
        self.status_frame.setVisible(True)
        self.status_msg.setText(message)

    def _start_automation_task(self, func, *args):
        """Orquestrador genérico para tarefas do robô."""
        self._update_status("🤖 Bot em ação...")
        self.progress_bar.setRange(0, 0)
        self.worker = AutomationWorker(func, *args)
        self.worker.finished.connect(self._on_automation_finished)
        self.worker.start()

    def _reagir_a_nova_ocorrencia(self):
        """Bloqueia o sentinela temporariamente para o robô trabalhar em paz."""
        if not self.sentinela_ativa:
            return

        # 1. Pausa o 'olho' do sentinela para ele não detectar os próprios cliques do robô
        self.sentinel_thread.is_running = False 
        
        self._update_status("🚨 Nova ocorrência! Iniciando extração...")
        
        # 2. Roda a sincronização (que já foca a janela e extrai)
        # Usamos o QTimer para dar 1 segundo de respiro para o sistema
        QTimer.singleShot(1000, self.run_active_sync)

    def _ocorrencia_ja_disparada(self, call_id):
        """Verifica se o ID da chamada já consta no arquivo de log."""
        log_path = Path(ROOT_DIR) / "data" / "disparados.log"
        if not log_path.exists():
            return False
        with open(log_path, "r") as f:
            ids_enviados = f.read().splitlines()
        return str(call_id) in ids_enviados

    def _registrar_disparo(self, call_id):
        """Salva o ID da chamada no arquivo de log para evitar duplicidade."""
        log_path = Path(ROOT_DIR) / "data" / "disparados.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a") as f:
            f.write(f"{call_id}\n")

    def _on_automation_finished(self, success, message):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        
        if success:
            self._update_status("✅ Dados sincronizados!")
            self.carregar_chamadas_ativas()
            
            # SE o sentinela estiver ativo, buscamos a cronologicamente mais recente
            if self.sentinela_ativa and self.model and self.model.ocorrencias:
                try:
                    # 1. Ordenamos usando 'horario' (que é onde o seu services.py guardou o created_at)
                    ocorrencias_ordenadas = sorted(
                        self.model.ocorrencias, 
                        key=lambda x: datetime.strptime(x.horario, "%d/%m/%Y %H:%M:%S"), 
                        reverse=True
                    )
                    
                    ultima_oc = ocorrencias_ordenadas[0] 
                    call_id = ultima_oc.id_chamada

                    # 2. Verificamos se já foi disparada (Memória do Log)
                    if not self._ocorrencia_ja_disparada(call_id):
                        # Marca visualmente na tabela
                        ultima_oc.selecionado = True
                        self.model.layoutChanged.emit()
                        
                        # Registra o ID no log para não repetir e dispara
                        self._registrar_disparo(call_id)
                        self._update_status(f"🚀 Nova ocorrência detectada: {call_id}")
                        
                        # Disparo automático para o WhatsApp
                        QTimer.singleShot(1000, self.disparar_whatsapp_automático)
                    else:
                        self._update_status(f"ℹ️ Sem novidades. Última ID ({call_id}) já enviada.")

                except Exception as e:
                    logging.error(f"Erro ao processar datas para disparo: {e}")
                    self._update_status("❌ Erro ao identificar ocorrência mais recente.")

            # Reinício do sentinela com tempo de respiro para o usuário
            if self.sentinela_ativa:
                self.parar_loop_monitoramento()
                QTimer.singleShot(10000, self.iniciar_loop_monitoramento)
        else:
            self._update_status(f"❌ Erro: {message}")
            if self.sentinela_ativa:
                QTimer.singleShot(5000, self.iniciar_loop_monitoramento)

    def _on_history_finished(self, success, result, occurrence):
        """Trata o retorno da busca de histórico (OCR)."""
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        if success:
            occurrence.historico = result
            self._update_status("✅ Histórico capturado!")
            self.model.layoutChanged.emit()
            QMessageBox.information(self, "Sucesso", f"Relato extraído:\n\n{result}")
        else:
            self._update_status(f"❌ Falha no OCR: {result}")
    
    def _toggle_row_checkbox(self, index):
        """Inverte o checkbox quando qualquer parte da linha é clicada."""
        # Se o usuário clicar exatamente na coluna 0 (a da caixa), 
        # o PySide já trata o clique sozinho. Só agimos se for nas outras colunas.
        if index.column() == 0:
            return

        # Pegamos o modelo
        model = self.model
        if not model: return

        # Pegamos o índice exato da coluna 0 para a linha clicada
        check_index = model.index(index.row(), 0)
        
        # Pegamos o estado atual
        ocorrencia = model.ocorrencias[index.row()]
        novo_estado = not ocorrencia.selecionado
        
        # Atualizamos via setData (que emite o sinal de mudança visual)
        model.setData(check_index, Qt.Checked if novo_estado else Qt.Unchecked, Qt.CheckStateRole)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_light_theme(app)
    window = FireApp()
    window.show()
    sys.exit(app.exec())
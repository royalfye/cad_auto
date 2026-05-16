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

from src.bot.cad_bot import CADAutomationBot
from src.processing.data_handler import DataProcessor
from src.processing.services import (
    converter_dataframe_para_objetos, 
    generate_activity_report,
    obter_nome_grupo_whatsapp
)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMessageBox, QStackedWidget
)
from PySide6.QtCore import Qt, QTimer

from src.interface.styles import STYLE_SHEET, apply_light_theme
from src.interface.workers import AutomationWorker
from src.interface.sidebar import SideBar
from src.interface.table_model import OcorrenciaTableModel
from src.interface.pages.active_calls_page import ActiveCallsPage
from src.processing.log_service import ocorrencia_ja_disparada, registrar_disparo
from src.interface.pages.process_page import ProcessPage
from src.bot.sentinel_worker import SentinelWorker
from src.bot.history_bot import HistoryBot
from src.bot.whatsapp_bot import WhatsAppBot

#2 - Class
class FireApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # 1. Inicialização de instâncias (Lógica de Negócio)
        self.processor = DataProcessor()
        self.bot = CADAutomationBot()
        self.model = None
        self.sentinela_ativa = False
        self.sentinel_thread = None
        
        # 2. Configurações da Janela Principal
        self._configure_window()
        
        # 3. Construção da Interface
        self._setup_ui()
        
        # 4. Inicialização de Modelos (Dados vazios para começar)
        self._connect_signals()
        self.carregar_chamadas_ativas()

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

        # Inicializa Componentes (A ORDEM FOI INVERTIDA AQUI)
        self._create_main_content_area() # PRIMEIRO criamos o baralho
        self._create_sidebar()           # DEPOIS criamos a Sidebar e conectamos ao baralho
        
        # Montagem Final
        self.layout_geral.addWidget(self.sidebar)
        self.layout_geral.addWidget(self.content_area)

    def _create_sidebar(self):
        # O callback diz à Sidebar: "Quando um botão for clicado, mude o índice do meu baralho"
        self.sidebar = SideBar(switch_page_callback=self.page_manager.setCurrentIndex)
        self.layout_geral.addWidget(self.sidebar)

    def _create_main_content_area(self):
        """Cria a área onde as tabelas e botões de ação ficam."""
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(20)

        self.page_manager = QStackedWidget()
        self.content_layout.addWidget(self.page_manager)
        self.monitor_page = ActiveCallsPage()
        
        self.page_manager.addWidget(self.monitor_page)

        self.process_page = ProcessPage()
        self.page_manager.addWidget(self.process_page)

    def _connect_signals(self):
        """Connects page controls to application actions via Signals."""
        self.monitor_page.solicitou_historico.connect(self.iniciar_busca_historico)
        self.monitor_page.solicitou_copia.connect(self.copiar_ocorrencia_selecionada)
        self.monitor_page.solicitou_disparo.connect(self.disparar_whatsapp_automático)
        self.monitor_page.solicitou_sincronizacao.connect(self.run_active_sync)
        self.monitor_page.solicitou_sentinela.connect(self.gerenciar_sentinela)

    def switch_page_dummy(self, index):
        """Função vazia apenas para evitar erros na Sidebar."""
        pass

    def gerenciar_sentinela(self, ativo):
        """Ponto de entrada único para ligar/desligar."""
        self.sentinela_ativa = ativo
        if ativo:
            # Antes de ligar, garante que está tudo limpo
            self.parar_loop_monitoramento()
            # Pequeno delay para garantir a limpeza da memória
            QTimer.singleShot(500, self.iniciar_loop_monitoramento)
        else:
            self.parar_loop_monitoramento()
            self._update_status("⚪ Sentinela Desativado manualmente.")

    def iniciar_loop_monitoramento(self):
        """Inicia a thread com verificação de existência."""
        if not self.sentinela_ativa:
            return

        # VERIFICAÇÃO CRÍTICA: Se já existe uma thread rodando, não faz nada
        if hasattr(self, 'sentinel_thread') and self.sentinel_thread is not None:
            if self.sentinel_thread.isRunning():
                logging.info("🛰️ Sentinela já está em execução. Ignorando novo início.")
                return

        if self.bot.focar_janela_cad():
            self._update_status("🛰️ Sentinela: Calibrando visão...")
            QTimer.singleShot(1500, self._disparar_thread_sentinela)
        else:
            self._update_status("⚠️ CAD não encontrado. Tentando em 10s...")
            if self.sentinela_ativa:
                QTimer.singleShot(10000, self.iniciar_loop_monitoramento)

    def _disparar_thread_sentinela(self):
        """Criação física da thread."""
        if not self.sentinela_ativa: return
        
        self._update_status("🛰️ Sentinela: Monitorando tabela...")

        self.sentinel_thread = SentinelWorker()
        self.sentinel_thread.new_occurrence_detected.connect(self._reagir_a_nova_ocorrencia)
        self.sentinel_thread.finished_by_user.connect(self._on_sentinel_stopped)
        self.sentinel_thread.start()

    def parar_loop_monitoramento(self):
        """Finalização agressiva para evitar loops infinitos."""
        if hasattr(self, 'sentinel_thread') and self.sentinel_thread:
            # 1. Avisa a thread para parar o loop interno dela
            self.sentinel_thread.is_running = False
            # 2. Desconecta os sinais para evitar que ela tente rodar o _on_sentinel_stopped
            try:
                self.sentinel_thread.new_occurrence_detected.disconnect()
                self.sentinel_thread.finished_by_user.disconnect()
            except:
                pass
            # 3. Mata a thread
            self.sentinel_thread.quit()
            self.sentinel_thread.wait(1000) 
            self.sentinel_thread = None
            logging.info("🛰️ Thread do Sentinela destruída com sucesso.")

    def _on_sentinel_stopped(self, reason):
        """Callback para quando o sentinela para via hardware (mouse/ESC)."""
        self.sentinela_ativa = False
        self.monitor_page.atualizar_estado_sentinela(False, emitir_sinal=False)
        self._update_status(f"⚪ Sentinela parado por: {reason}")

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
            lista_textos = [
                oc.formatar_para_whatsapp(equipe=ala_selecionada) 
                for oc in selecionadas
            ]
            texto_final = "\n\n---\n\n".join(lista_textos)
            QApplication.clipboard().setText(texto_final)
            
            # SUBSTITUA AS DUAS LINHAS DO FEEDBACK VISUAL POR ESTA:
            self.monitor_page.exibir_feedback_copia(len(selecionadas))
            
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível copiar: {e}")

    # --- DATA & UI UPDATES (Atualização da Interface) ---

    def disparar_whatsapp_automático(self):
        selecionadas = [oc for oc in self.model.ocorrencias if oc.selecionado]
        if not selecionadas: return

        ala_sel = self.sidebar.combo_ala.currentText()
        # A função que você criou no services.py
        grupo_destino = obter_nome_grupo_whatsapp(ala_sel) 

        # A LINHA QUE DAVA ERRO FOI APAGADA AQUI!
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
                # 1. Prepara os dados (A lógica de negócio continua igual)
                lista_objetos = converter_dataframe_para_objetos(df)
                self.model = OcorrenciaTableModel(lista_objetos)
                
                # 2. Distribui para os componentes (AQUI MUDA!)
                report_text = generate_activity_report(df)
                
                # Em vez de self.summary_card.update_text(...), usamos a nova porta:
                self.monitor_page.atualizar_resumo(report_text)
                
                # A página recebe o modelo e atualiza a tabela
                self.monitor_page.table_ativas.update_data(self.model)
                
                # --- O PULO DO GATO AGORA FICA RESUMIDO A UMA LINHA ---
                # Aquele bloco inteiro de try/except foi movido para dentro desta função abaixo:
                self.monitor_page.associar_tabela_clique(self._toggle_row_checkbox)
                # ------------------------------------------------------

                self._update_status("📂 Dados atualizados com sucesso.")
            else:
                self._update_status("ℹ️ Nenhuma planilha encontrada. Sincronize com o CAD.")
                
        except Exception as e:
            self._update_status(f"❌ Erro ao carregar dados: {e}")

    def _update_status(self, message):
        """Método auxiliar para atualizar a barra de status."""
        self.monitor_page.exibir_status(message)

    def _start_automation_task(self, func, *args):
        """Orquestrador genérico para tarefas do robô."""
        self._update_status("🤖 Bot em ação...")
        self.monitor_page.configurar_progresso(0, 0)
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

    def _on_automation_finished(self, success, message):
        
        self.monitor_page.configurar_progresso(0, 100, 100)
        
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
                    if not ocorrencia_ja_disparada(call_id):
                        # Marca visualmente na tabela
                        ultima_oc.selecionado = True
                        self.model.layoutChanged.emit()
                        
                        # Registra o ID no log para não repetir e dispara
                        registrar_disparo(call_id)
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
            # 1. Primeiro, garantimos que qualquer resíduo da thread anterior sumiu
                self.parar_loop_monitoramento()
                
                # 2. Damos um tempo de respiro maior (10s) para o Windows estabilizar o foco
                # e para que você consiga clicar em "Parar" se quiser, sem o bot te atropelar.
                logging.info("🛰️ Agendando reinício do Sentinela em 10 segundos...")
                QTimer.singleShot(10000, self.iniciar_loop_monitoramento)

        else:
            # Caso a automação principal tenha falhado (success = False)
            self._update_status(f"❌ Erro na extração: {message}")
            
            if self.sentinela_ativa:
                self.parar_loop_monitoramento()
                # Em caso de erro, esperamos um pouco menos para tentar de novo
                QTimer.singleShot(5000, self.iniciar_loop_monitoramento)

    def _on_history_finished(self, success, result, occurrence):
        """Trata o retorno da busca de histórico (OCR)."""
        
        # AGORA USAMOS A PORTA CORRETA PARA A BARRA DE PROGRESSO:
        self.monitor_page.configurar_progresso(0, 100, 100)
        
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

# Comentario de teste 3: robos carregados sob demanda pelo Codex.

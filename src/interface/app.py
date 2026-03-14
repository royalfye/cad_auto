import os  # Primeiro importamos a biblioteca
import sys
from pathlib import Path

# 1. Configurações de Ambiente (Agora o 'os' já existe para o Python)
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_AUTOSCREENSCALEFACTOR"] = "1"

# 1.1 Ambiente e Caminhos

ROOT_DIR = Path(__file__).resolve().parent.parent.parent 
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# 2. Terceiros
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QTabWidget, QFrame, QProgressBar, 
    QHeaderView, QGraphicsDropShadowEffect, QTableView, QTextEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, QTimer 

# 3. Seus Módulos - PADRONIZE TUDO COM 'src.'
from src.processing.services import converter_dataframe_para_objetos, generate_activity_report
from src.bot.cad_bot import CADAutomationBot
from src.processing.data_handler import DataProcessor
from src.interface.styles import STYLE_SHEET, apply_light_theme 
from src.interface.workers import AutomationWorker 
from src.interface.sidebar import SideBar
from src.processing.services import converter_dataframe_para_objetos
from src.interface.table_model import OcorrenciaTableModel

class FireApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.processor = DataProcessor()
        self.bot = CADAutomationBot()
        
        self.setWindowTitle("Bombeiros - 2ª CIA Passos")
        self.resize(1200, 800)
        self.setStyleSheet(STYLE_SHEET)

        # Layout Principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.layout_geral = QHBoxLayout(main_widget)
        self.layout_geral.setContentsMargins(0, 0, 0, 0)
        self.layout_geral.setSpacing(0)

        # Peças da Interface
        self.sidebar = SideBar(switch_page_callback=self.switch_page_dummy)
        # Esconde os botões de navegação que não fazem mais sentido
        self.sidebar.btn_extracao.hide()
        self.sidebar.btn_process.hide()
        
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(20)

        # Montagem Direta (Sem abas)
        self.layout_geral.addWidget(self.sidebar)
        
        # Criamos direto a página de processamento (que agora é a única)
        self.monitor_page = self.create_processing_page()
        self.content_layout.addWidget(self.monitor_page)
        
        self.layout_geral.addWidget(self.content_area)

    def switch_page_dummy(self, index):
        """Função vazia apenas para evitar erros na Sidebar."""
        pass

    def create_processing_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. CABEÇALHO
        header = QHBoxLayout()
        header_title = QLabel("Monitoramento: Chamadas Ativas")
        header_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2d4157;")
        
        # --- PASSO A: CRIAR OS BOTÕES (Fabricação) ---
        # Definimos o que eles são ANTES de usá-los
        self.btn_history = QPushButton("🔍 Buscar Histórico")
        self.btn_history.setObjectName("ActionBtn")
        self.btn_history.setFixedWidth(180)
        self.btn_history.clicked.connect(self.iniciar_busca_historico)

        self.btn_copy = QPushButton("📋 Copiar para WhatsApp")
        self.btn_copy.setObjectName("ActionBtn")
        self.btn_copy.setStyleSheet("background-color: #25D366; color: white;")
        self.btn_copy.setFixedWidth(220)
        self.btn_copy.clicked.connect(self.copiar_ocorrencia_selecionada)

        self.btn_sync = QPushButton("🔄 Sincronizar CAD")
        self.btn_sync.setObjectName("ActionBtn")
        self.btn_sync.setFixedWidth(150)
        self.btn_sync.clicked.connect(self.run_active_sync)

        # --- PASSO B: ADICIONAR AO LAYOUT (Montagem) ---
        header.addWidget(header_title)
        header.addStretch()
        header.addWidget(self.btn_history) # Agora o Python já sabe quem ele é!
        header.addWidget(self.btn_copy)
        header.addWidget(self.btn_sync)
        layout.addLayout(header)

        # 2. BARRA DE STATUS
        self.status_frame = QFrame()
        self.status_frame.setObjectName("Card")
        self.status_frame.setVisible(False)
        st_layout = QVBoxLayout(self.status_frame)
        self.status_msg = QLabel("Pronto...")
        self.progress_bar = QProgressBar()
        st_layout.addWidget(self.status_msg)
        st_layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_frame)

        # 3. TABELA (O peso '1' faz ela ocupar o centro)
        self.table_ativas = QTableView() 
        self.table_ativas.setAlternatingRowColors(True)
        self.table_ativas.setSelectionBehavior(QTableView.SelectRows)
        h_header = self.table_ativas.horizontalHeader()
        h_header.setStretchLastSection(True)
        layout.addWidget(self.table_ativas, 1) 

        # 4. CARD DE RELATÓRIO (Agora abaixo da tabela)
        # Primeiro criamos o Frame
        self.summary_card = QFrame()
        self.summary_card.setObjectName("SummaryCard")
        self.summary_card.setFixedHeight(200)
        
        # Depois o Layout para o Frame
        report_layout = QVBoxLayout(self.summary_card)
        
        lbl_preview = QLabel("📋 Pré-visualização para WhatsApp:")
        lbl_preview.setStyleSheet("font-size: 11px; font-weight: bold; color: #6a8296;")
        
        self.txt_preview = QTextEdit()
        self.txt_preview.setReadOnly(True)
        self.txt_preview.setStyleSheet("background-color: #f8fafc; font-family: 'Consolas';")

        self.btn_copy_report = QPushButton("📋 Copiar Relatório Completo")
        self.btn_copy_report.setObjectName("SecondaryBtn")
        self.btn_copy_report.clicked.connect(self.copy_summary_to_clipboard)

        report_layout.addWidget(lbl_preview)
        report_layout.addWidget(self.txt_preview)
        report_layout.addWidget(self.btn_copy_report)
        
        layout.addWidget(self.summary_card)

        return page
    
    # --- LÓGICA DE DADOS E AUTOMAÇÃO ---
    def carregar_chamadas_ativas(self):
        df = self.processor.process_latest_active_call()
        if df is not None:
            # 1. Atualiza a tabela (O que já funcionava)
            lista_objetos = converter_dataframe_para_objetos(df)
            self.model = OcorrenciaTableModel(lista_objetos)
            self.table_ativas.setModel(self.model)
            
            # 2. Atualiza o Dashboard e o Preview (O ajuste está aqui)
            # Em vez de procurar 'lbl_report_text', chamamos o método que criamos
            self.update_summary_dashboard(df)
            
            self.table_ativas.resizeColumnsToContents()
            self.table_ativas.setColumnWidth(0, 50)

    def copiar_ocorrencia_selecionada(self):
        index = self.table_ativas.currentIndex()
        if not index.isValid():
            # Opcional: mostrar mensagem que nada foi selecionado
            return

        # Pegamos o objeto diretamente do modelo
        ocorrencia = self.model.ocorrencias[index.row()]
        texto = ocorrencia.formatar_para_whatsapp()
        
        # Clipboard do sistema
        QApplication.clipboard().setText(texto)
        
        # Dica de UX: Você pode mudar temporariamente o texto do botão
        self.btn_copy.setText("✅ Copiado!")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self.btn_copy.setText("📋 Copiar para WhatsApp"))
    
        # Adicione estes métodos à classe FireApp:

    def update_summary_dashboard(self, df):
        """Atualiza apenas o campo de texto do relatório."""
        if df is not None and not df.empty:
            # Importamos a lógica de texto que gera o relatório formatado
            from src.processing.services import generate_activity_report
            
            # Geramos o texto (que já inclui o TOTAL lá dentro, lembra?)
            report_text = generate_activity_report(df)
            
            # Inserimos o texto no campo de pré-visualização abaixo da tabela
            self.txt_preview.setText(report_text)
        else:
            # Caso o DataFrame esteja vazio, limpamos o campo
            self.txt_preview.clear()
            self.txt_preview.setPlaceholderText("Nenhum dado encontrado para gerar o relatório.")

    def copy_summary_to_clipboard(self):
        """Copia o conteúdo que já está visível no preview."""
        text_to_copy = self.txt_preview.toPlainText()
        
        if text_to_copy:
            QApplication.clipboard().setText(text_to_copy)
            
            # Feedback visual no botão
            self.btn_copy_report.setText("✅ Relatório Copiado!")
            QTimer.singleShot(2000, lambda: self.btn_copy_report.setText("📋 Copiar para WhatsApp"))

    def iniciar_busca_historico(self):
        """Gatilha o robô para buscar o relato no CAD."""
        index = self.table_ativas.currentIndex()
        if not index.isValid():
            self.status_frame.setVisible(True)
            self.status_msg.setText("⚠️ Selecione uma linha na tabela primeiro!")
            return
        from src.bot.history_bot import HistoryBot
        # Pegamos o objeto Ocorrencia da linha selecionada
        ocorrencia = self.model.ocorrencias[index.row()]
        call_id = ocorrencia.id_chamada

        # 1. Mostra feedback visual
        self.status_frame.setVisible(True)
        self.status_msg.setText(f"🤖 Indo buscar histórico do ID: {call_id}")
        self.progress_bar.setRange(0, 0) # Efeito de 'carregando' infinito

        # 2. Prepara o robô
        self.h_bot = HistoryBot()
        
        # 3. Dispara via Worker (passando a função e o ID)
        self.worker = AutomationWorker(self.h_bot.capturar_historico_por_id, call_id)
        
        # Conecta o sinal de status para as mensagens do bot aparecerem na tela (opcional mas recomendado)
        if hasattr(self.worker, 'status'):
            self.worker.status.connect(lambda msg: self.status_msg.setText(msg))
        
        # Conecta o fim do processo
        self.worker.finished.connect(lambda success, result: self.on_history_finished(success, result, ocorrencia))
        self.worker.start()

    def exibir_relatorio_pop_up(self):
        """Pega os dados atuais e exibe o resumo em um pop-up."""
        from PySide6.QtWidgets import QMessageBox
        
        # 1. Tentamos processar o arquivo mais recente para garantir dados novos
        df = self.processor.process_latest_active_call()
        
        if df is not None:
            # 2. Chamamos a lógica que criamos no services.py
            texto_relatorio = generate_activity_report(df)
            
            # 3. Exibimos na tela
            msg = QMessageBox(self)
            msg.setWindowTitle("Resumo do Serviço")
            msg.setText(texto_relatorio)
            msg.setIcon(QMessageBox.Information)
            msg.exec()
        else:
            QMessageBox.warning(self, "Aviso", "Não há dados disponíveis para gerar o relatório.")

    def on_history_finished(self, success, result, ocorrencia):
        """Processa o resultado do OCR e atualiza a interface."""
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        
        if success:
            # 'result' aqui é o texto que o OCR extraiu da tabela!
            ocorrencia.historico = result
            self.status_msg.setText("✅ Histórico capturado com sucesso!")
            
            # Notifica a tabela que o dado mudou (isso atualiza o texto se você tiver uma coluna de histórico)
            self.model.layoutChanged.emit()
            
            # Mostra o que foi capturado em um pop-up simples para conferência
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Histórico Capturado", f"Relato extraído:\n\n{result}")
        else:
            self.status_msg.setText(f"❌ Falha no OCR: {result}")



    def run_historical_sync(self):
    # Remova o 'None' do final
        self.start_automation(self.bot.run_full_extraction_flow, self.processor.bronze_path)

    def run_active_sync(self):
    # Remova o 'None' do final
        self.start_automation(self.bot.run_active_extraction_flow, self.processor.bronze_path)

    def start_automation(self, func, *args):
        self.status_frame.setVisible(True)
        self.status_msg.setText("🤖 Bot em ação...")
        self.worker = AutomationWorker(func, *args)
        self.worker.finished.connect(self.on_automation_finished)
        self.worker.start()

    def on_automation_finished(self, success, message):
        """Ao terminar a extração do CAD, atualiza a tabela na mesma tela."""
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        
        if success:
            self.status_msg.setText("✅ Dados do CAD sincronizados!")
            # 1. Recarrega os dados do CSV para a tabela
            self.carregar_chamadas_ativas()
            # 2. NÃO use mais self.switch_page(1), pois já estamos na página certa!
        else:
            self.status_msg.setText(f"❌ Erro na sincronização: {message}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_light_theme(app)
    window = FireApp()
    window.show()
    sys.exit(app.exec())
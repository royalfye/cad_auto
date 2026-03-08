import os  # Primeiro importamos a biblioteca
import sys
from pathlib import Path

# 1. Configurações de Ambiente (Agora o 'os' já existe para o Python)
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_AUTOSCREENSCALEFACTOR"] = "1"

# 1. Ambiente e Caminhos

ROOT_DIR = Path(__file__).resolve().parent.parent.parent 
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# 2. Terceiros
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QTabWidget, QFrame, QProgressBar, 
    QHeaderView, QGraphicsDropShadowEffect, QTableView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

# 3. Seus Módulos - PADRONIZE TUDO COM 'src.'
from src.bot.cad_bot import CADAutomationBot
from src.processing.data_handler import DataProcessor
from src.interface.styles import STYLE_SHEET
from src.interface.workers import AutomationWorker 
from src.interface.sidebar import SideBar
from src.processing.services import converter_dataframe_para_objetos
from src.interface.table_model import OcorrenciaTableModel
from src.bot.history_bot import HistoryBot

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
        self.sidebar = SideBar(switch_page_callback=self.switch_page)
        
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(20)

        self.pages = QTabWidget()
        self.pages.tabBar().hide()
        self.setup_pages() 

        # Montagem
        self.layout_geral.addWidget(self.sidebar)
        self.content_layout.addWidget(self.pages)
        self.layout_geral.addWidget(self.content_area)

    # --- LÓGICA DE NAVEGAÇÃO ---
    def switch_page(self, index):
        self.pages.setCurrentIndex(index)
        # Atualiza o visual dos botões que estão LÁ na sidebar
        self.sidebar.btn_extracao.setChecked(index == 0)
        self.sidebar.btn_process.setChecked(index == 1)

    # --- CRIAÇÃO DAS PÁGINAS ---
    def setup_pages(self):
        self.pages.addTab(self.create_extraction_page(), "Extração")
        self.pages.addTab(self.create_processing_page(), "Processamento")

    def create_extraction_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        header = QLabel("Módulos de Extração")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #2d4157;")
        layout.addWidget(header)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        # Usando a função interna por enquanto (vamos mover depois)
        hist_card = self.create_modern_card(
            "📜 Histórico de Dados", 
            "Captura ocorrências finalizadas dos últimos 90 dias.", 
            "Sincronizar Histórico", 
            self.run_historical_sync
        )
        active_card = self.create_modern_card(
            "🚨 Ocorrências Ativas", 
            "Captura chamadas em andamento no tempo real.", 
            "Monitorar Ativas", 
            self.run_active_sync
        )

        cards_layout.addWidget(hist_card)
        cards_layout.addWidget(active_card)
        layout.addLayout(cards_layout)

        # Feedback de Status
        self.status_frame = QFrame()
        self.status_frame.setObjectName("Card")
        self.status_frame.setVisible(False)
        st_layout = QVBoxLayout(self.status_frame)
        
        self.status_msg = QLabel("Pronto para iniciar...")
        self.status_msg.setStyleSheet("font-weight: bold; color: #2d4157;")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        
        st_layout.addWidget(self.status_msg)
        st_layout.addWidget(self.progress_bar)
        
        layout.addSpacing(20)
        layout.addWidget(self.status_frame)
        layout.addStretch()
        return page

    def create_modern_card(self, title, desc, btn_txt, callback):
        frame = QFrame()
        frame.setObjectName("Card")
        frame.setMinimumHeight(220)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30))
        frame.setGraphicsEffect(shadow)

        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(25, 25, 25, 25)
        
        t = QLabel(title)
        t.setObjectName("CardTitle")
        d = QLabel(desc)
        d.setWordWrap(True)
        d.setStyleSheet("color: #6a8296; font-size: 13px;")

        btn = QPushButton(btn_txt)
        btn.setObjectName("ActionBtn")
        btn.clicked.connect(callback)

        vbox.addWidget(t)
        vbox.addWidget(d)
        vbox.addStretch()
        vbox.addWidget(btn)
        return frame

    def create_processing_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        header = QHBoxLayout()
        header_title = QLabel("Monitoramento: Chamadas Ativas")
        header_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2d4157;")
        
        # --- BOTÃO COPIAR ---
        self.btn_copy = QPushButton("📋 Copiar para WhatsApp")
        self.btn_copy.setObjectName("ActionBtn")
        self.btn_copy.setStyleSheet("background-color: #25D366; color: white;") # Verde WhatsApp
        self.btn_copy.clicked.connect(self.copiar_ocorrencia_selecionada)
        self.btn_copy.setFixedWidth(220)

        # --- BOTÃO EXTRAIR HISTÓRICO (Novo!) ---
        self.btn_history = QPushButton("🔍 Buscar Histórico")
        self.btn_history.setObjectName("ActionBtn")
        self.btn_history.setStyleSheet("background-color: #2d4157; color: white;")
        self.btn_history.setFixedWidth(180)
        self.btn_history.clicked.connect(self.iniciar_busca_historico)

        btn_view = QPushButton("🔄 Atualizar")
        btn_view.setObjectName("ActionBtn")
        btn_view.clicked.connect(self.carregar_chamadas_ativas)
        btn_view.setFixedWidth(120)

        

        header.addWidget(header_title)
        header.addStretch()
        header.addWidget(self.btn_history) # Novo botão aqui
        header.addWidget(self.btn_copy) # Adicionamos o novo botão
        header.addWidget(btn_view)
        
        layout.addLayout(header)

        self.table_ativas = QTableView() 
        self.table_ativas.setAlternatingRowColors(True)
        self.table_ativas.setSelectionBehavior(QTableView.SelectRows)
        self.table_ativas.verticalHeader().setVisible(False)
        
        # O Estilo agora vem automático do STYLE_SHEET!
        
        h_header = self.table_ativas.horizontalHeader()
        h_header.setSectionResizeMode(QHeaderView.Interactive)
        h_header.setStretchLastSection(True)

        layout.addWidget(self.table_ativas)
        return page

    # --- LÓGICA DE DADOS E AUTOMAÇÃO ---
    def carregar_chamadas_ativas(self):
        df = self.processor.process_latest_active_call()
        if df is not None:
            # Degrau 2: Converte os dados
            lista_objetos = converter_dataframe_para_objetos(df)
            
            # Degrau 3: Usa o novo Model focado em Objetos
            self.model = OcorrenciaTableModel(lista_objetos)
            self.table_ativas.setModel(self.model)
            
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

    def iniciar_busca_historico(self):
        """Gatilha o robô para buscar o relato no CAD."""
        index = self.table_ativas.currentIndex()
        if not index.isValid():
            self.status_frame.setVisible(True)
            self.status_msg.setText("⚠️ Selecione uma linha na tabela primeiro!")
            return

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
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        if success:
            self.status_msg.setText("✅ Sucesso!")
            self.carregar_chamadas_ativas()
            self.switch_page(1)
        else:
            self.status_msg.setText(f"❌ Erro: {message}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FireApp()
    window.show()
    sys.exit(app.exec())
# 1. Bibliotecas padrão do sistema (Standard Library)
import sys
from pathlib import Path

# 2. Bibliotecas de terceiros (Third-party)
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QTabWidget, QFrame, QProgressBar, 
    QTableWidget, QTableWidgetItem, QHeaderView, QSpacerItem, 
    QSizePolicy, QGraphicsDropShadowEffect, QTableView
)
from PySide6.QtCore import Qt, QThread, Signal, QSize, QAbstractTableModel
from PySide6.QtGui import QIcon, QFont, QColor

# 3. Configuração de Caminhos (Hack necessário para módulos locais)
current_dir = Path(__file__).resolve().parent
src_root = current_dir.parent
if str(src_root) not in sys.path:
    sys.path.append(str(src_root))

# 4. Módulos do seu projeto (Local imports)
from bot.cad_bot import CADAutomationBot
from processing.data_handler import DataProcessor
from interface.styles import STYLE_SHEET

class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)
        return None

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        return None

# --- ESTILIZAÇÃO QSS MODERNA ---


class AutomationWorker(QThread):
    finished = Signal(bool, str)
    def __init__(self, bot_function, *args):
        super().__init__()
        self.bot_function = bot_function
        self.args = args

    def run(self):
        try:
            success = self.bot_function(*self.args)
            self.finished.emit(success, "Processo concluído com sucesso!")
        except Exception as e:
            self.finished.emit(False, str(e))

class FireApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.processor = DataProcessor()
        self.bot = CADAutomationBot()
        
        self.setWindowTitle("Bombeiros - 2ª CIA Passos")
        self.resize(1200, 800)
        self.setStyleSheet(STYLE_SHEET)
        
        # Layout Principal (Horizontal: Sidebar + Content)
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.layout_geral = QHBoxLayout(main_widget)
        self.layout_geral.setContentsMargins(0, 0, 0, 0)
        self.layout_geral.setSpacing(0)

        self.setup_sidebar()
        
        # Área de Conteúdo (Vertical: Header + MainContent)
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(20)
        
        # Stacked Widget para simular as abas
        self.pages = QTabWidget()
        self.pages.tabBar().hide() # Esconde as abas originais do Qt
        
        self.setup_pages()
        
        self.content_layout.addWidget(self.pages)
        self.layout_geral.addWidget(self.content_area)

    def apply_stylesheet(self):
        """Lê o arquivo .qss e aplica na janela principal."""
        if self.qss_path.exists():
            with open(self.qss_path, "r", encoding="utf-8") as f:
                style = f.read()
                self.setStyleSheet(style)
        else:
            print(f"⚠️ Alerta: Arquivo de estilo não encontrado em {self.qss_path}")

    def carregar_chamadas_ativas(self):
        df = self.processor.process_latest_active_call()
        
        if df is not None:
            # Cria o model com os dados novos
            self.model = PandasModel(df)
            # Aplica o model na tabela da interface
            self.table_ativas.setModel(self.model)
            # Ajusta a largura das colunas automaticamente
            self.table_ativas.resizeColumnsToContents()
        else:
            print("Aviso: Nenhum dado disponível para exibição.")

    def setup_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("SideBar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header da Sidebar (Branding)
        brand_frame = QFrame()
        brand_layout = QVBoxLayout(brand_frame)
        brand_layout.setContentsMargins(20, 40, 20, 40)
        
        title = QLabel("🚒 GESTÃO\nCAD PASSOS")
        title.setObjectName("MainTitle")
        title.setWordWrap(True)
        brand_layout.addWidget(title)
        
        layout.addWidget(brand_frame)

        # Botões de Navegação
        self.btn_extracao = QPushButton("  📥 Extração (CAD)")
        self.btn_extracao.setObjectName("NavBtn")
        self.btn_extracao.setCheckable(True)
        self.btn_extracao.setChecked(True)
        self.btn_extracao.clicked.connect(lambda: self.switch_page(0))

        self.btn_process = QPushButton("  ⚙️ Processamento")
        self.btn_process.setObjectName("NavBtn")
        self.btn_process.setCheckable(True)
        self.btn_process.clicked.connect(lambda: self.switch_page(1))

        layout.addWidget(self.btn_extracao)
        layout.addWidget(self.btn_process)
        layout.addStretch()

        # Rodapé Sidebar
        status_lbl = QLabel("V 1.2.0 | Ativo")
        status_lbl.setStyleSheet("color: #6a8296; padding: 20px; font-size: 11px;")
        layout.addWidget(status_lbl)

        self.layout_geral.addWidget(sidebar)

    def setup_pages(self):
        self.pages.addTab(self.create_extraction_page(), "Extração")
        self.pages.addTab(self.create_processing_page(), "Processamento")

    def create_extraction_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        info_header = QLabel("Módulos de Extração")
        info_header.setStyleSheet("font-size: 24px; font-weight: bold; color: #2d4157;")
        layout.addWidget(info_header)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        # Card 1: Histórico
        hist_card = self.create_modern_card(
            "📜 Histórico de Dados", 
            "Captura ocorrências finalizadas dos últimos 90 dias para base silver.", 
            "Sincronizar Histórico", 
            self.run_historical_sync
        )
        
        # Card 2: Ativas
        active_card = self.create_modern_card(
            "🚨 Ocorrências Ativas", 
            "Captura chamadas em andamento no tempo real para o monitoramento.", 
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
        
        # Efeito de Sombra (Moderno)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 30))
        frame.setGraphicsEffect(shadow)

        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(25, 25, 25, 25)

        t = QLabel(title)
        t.setObjectName("CardTitle")
        
        d = QLabel(desc)
        d.setWordWrap(True)
        d.setStyleSheet("color: #6a8296; font-size: 13px; line-height: 18px;")

        btn = QPushButton(btn_txt)
        btn.setObjectName("ActionBtn")
        btn.setCursor(Qt.PointingHandCursor)
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
        header_title = QLabel("Monitoramento: Chamadas Ativas (Silver)") # Ajuste no título
        header_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2d4157;")
        
        btn_view = QPushButton("🔄 Atualizar Tabela")
        btn_view.setObjectName("ActionBtn")
        btn_view.clicked.connect(self.carregar_chamadas_ativas) # Conectado ao seu novo método
        btn_view.setFixedWidth(180)

        header.addWidget(header_title)
        header.addStretch()
        header.addWidget(btn_view)
        
        layout.addLayout(header)
        layout.addSpacing(10)

        # TROCA: Saída QTableWidget, Entrada QTableView
        self.table_ativas = QTableView() 
        self.table_ativas.setAlternatingRowColors(True)
        self.table_ativas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_ativas)
        
        return page

    def switch_page(self, index):
        self.pages.setCurrentIndex(index)
        self.btn_extracao.setChecked(index == 0)
        self.btn_process.setChecked(index == 1)

    # --- LÓGICA DE EXECUÇÃO (MANTIDA) ---
    def run_historical_sync(self):
        self.start_automation(self.bot.run_full_extraction_flow, self.processor.bronze_path, None)

    def run_active_sync(self):
        self.start_automation(self.bot.run_active_extraction_flow, self.processor.bronze_path, None)

    def start_automation(self, func, *args):
        self.status_frame.setVisible(True)
        self.status_msg.setText("🤖 Bot em ação: Executando no CAD...")
        self.status_msg.setStyleSheet("color: #f77965; font-weight: bold;")
        
        self.worker = AutomationWorker(func, *args)
        self.worker.finished.connect(self.on_automation_finished)
        self.worker.start()

    def on_automation_finished(self, success, message):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        
        if success:
            self.status_msg.setText(f"✅ Extração Concluída! Processando dados...")
            self.status_msg.setStyleSheet("color: #27ae60; font-weight: bold;")
            

            self.carregar_chamadas_ativas() 
            
            self.switch_page(1) 
        else:
            self.status_msg.setText(f"❌ Falha: {message}")
            self.status_msg.setStyleSheet("color: #e74c3c; font-weight: bold;")

    def load_silver_data(self):
        path = self.processor.silver_path / "master_historic_silver.csv"
        if path.exists():
            df = pd.read_csv(path).head(100)
            self.table.setColumnCount(len(df.columns))
            self.table.setRowCount(len(df.index))
            self.table.setHorizontalHeaderLabels(df.columns)
            for i in range(len(df.index)):
                for j in range(len(df.columns)):
                    self.table.setItem(i, j, QTableWidgetItem(str(df.iloc[i, j])))
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FireApp()
    window.show()
    sys.exit(app.exec())
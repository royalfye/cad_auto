from PySide6.QtCore import Signal, QTimer
from PySide6.QtWidgets import QLabel, QFrame, QProgressBar, QVBoxLayout, QWidget

from src.interface.components.active_table import ActiveCallsTable
from src.interface.components.header import HeaderSection
from src.interface.components.summary_card import SummaryCard

class ActiveCallsPage(QWidget):
    """Page responsible only for the active calls UI composition."""

    # --- 1. SINAIS (O "RÁDIO" PARA AVISAR O APP.PY) ---
    solicitou_historico = Signal()
    solicitou_copia = Signal()
    solicitou_disparo = Signal()
    solicitou_sincronizacao = Signal()
    solicitou_sentinela = Signal(bool) # Passa True/False avisando se ligou ou desligou

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._conectar_sinais_internos()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.header = HeaderSection()
        self.status_frame = self._create_status_section()
        self.table_ativas = ActiveCallsTable()
        self.summary_card = SummaryCard()

        layout.addWidget(self.header)
        layout.addWidget(self.status_frame)
        layout.addWidget(self.table_ativas, 1)
        layout.addWidget(self.summary_card)
        
    def _conectar_sinais_internos(self):
        """Conecta os cliques físicos da tela aos sinais de 'Rádio'."""
        self.header.btn_history.clicked.connect(self.solicitou_historico.emit)
        self.header.btn_copy.clicked.connect(self.solicitou_copia.emit)
        self.header.btn_send.clicked.connect(self.solicitou_disparo.emit)
        self.header.btn_sync.clicked.connect(self.solicitou_sincronizacao.emit)
        self.header.play_toggled.connect(self.solicitou_sentinela.emit)

    def _create_status_section(self):
        frame = QFrame()
        frame.setObjectName("Card")
        frame.setVisible(False)

        layout = QVBoxLayout(frame)
        self.status_msg = QLabel("Pronto...")
        self.progress_bar = QProgressBar()

        layout.addWidget(self.status_msg)
        layout.addWidget(self.progress_bar)

        return frame
    
    # --- 2. MÉTODOS PÚBLICOS DE ATUALIZAÇÃO (PORTAS DE ENTRADA) ---
    
    def exibir_status(self, mensagem: str, visivel: bool = True):
        self.status_frame.setVisible(visivel)
        self.status_msg.setText(mensagem)

    def configurar_progresso(self, minimo: int, maximo: int, valor: int = 0):
        self.progress_bar.setRange(minimo, maximo)
        self.progress_bar.setValue(valor)

    def atualizar_resumo(self, texto: str):
        self.summary_card.update_text(texto)
        
    def associar_tabela_clique(self, callback):
        try:
            self.table_ativas.clicked.disconnect()
        except Exception:
            pass
        self.table_ativas.clicked.connect(callback)
        
    def atualizar_estado_sentinela(self, ativo: bool, emitir_sinal: bool = False):
        """Atualiza visualmente o botão do sentinela pelo HeaderSection."""
        self.header.set_monitoring_state(ativo, emit_signal=emitir_sinal)
        
    def exibir_feedback_copia(self, quantidade: int):
        """Muda o texto do botão temporariamente para dar feedback visual."""
        self.header.btn_copy.setText(f"✅ {quantidade} Copiadas!")
        QTimer.singleShot(2000, lambda: self.header.btn_copy.setText("📋 Copiar para WhatsApp"))
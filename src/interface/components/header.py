from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal

class HeaderSection(QWidget):
    """Componente que agrupa o título e os botões de ação superiores."""
    
    # Sinal para avisar o App que o estado do Sentinela mudou (True=Rodando, False=Parado)
    play_toggled = Signal(bool) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_monitoring = False # Estado inicial: desligado
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Título
        title = QLabel("Monitoramento: Chamadas Ativas")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2d4157;")
        
        # 2. Botão Histórico
        self.btn_history = QPushButton("🔍 Buscar Histórico")
        self.btn_history.setObjectName("ActionBtn")
        self.btn_history.setFixedWidth(160)

        # 3. Botão Copiar
        self.btn_copy = QPushButton("📋 Copiar")
        self.btn_copy.setObjectName("ActionBtn")
        self.btn_copy.setFixedWidth(120)

        # 4. Botão Disparar (WhatsApp)
        self.btn_send = QPushButton("🚀 Disparar WhatsApp")
        self.btn_send.setObjectName("ActionBtn")
        self.btn_send.setStyleSheet("background-color: #128C7E; color: white;") 
        self.btn_send.setFixedWidth(200)

        # 5. Botão Sentinela (O que deu o erro)
        self.btn_sentinel = QPushButton("▶️ Iniciar Sentinela")
        self.btn_sentinel.setObjectName("ActionBtn")
        self.btn_sentinel.setFixedWidth(200)
        self.btn_sentinel.setStyleSheet("background-color: #4b5263; color: white;")
        
        # Conexão que estava falhando:
        self.btn_sentinel.clicked.connect(self._toggle_state)

        # 6. Botão Sincronizar
        self.btn_sync = QPushButton("🔄 Sincronizar")
        self.btn_sync.setObjectName("ActionBtn")
        self.btn_sync.setFixedWidth(130)

        # Montagem do Layout
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self.btn_history)
        layout.addWidget(self.btn_copy)
        layout.addWidget(self.btn_send)
        layout.addWidget(self.btn_sentinel) # Sentinela adicionado
        layout.addWidget(self.btn_sync)

    def _toggle_state(self):
        """Alterna visualmente e logicamente entre Play e Stop."""
        self.set_monitoring_state(not self.is_monitoring)

    def set_monitoring_state(self, is_monitoring: bool, emit_signal: bool = True):
        """Define o estado visual do sentinela sem depender de alternância."""
        self.is_monitoring = is_monitoring

        if self.is_monitoring:
            self.btn_sentinel.setText("⏹️ Parar Sentinela")
            # Vermelho para indicar perigo/parada
            self.btn_sentinel.setStyleSheet("background-color: #d9534f; color: white;") 
        else:
            self.btn_sentinel.setText("▶️ Iniciar Sentinela")
            # Cinza azulado para indicar prontidão
            self.btn_sentinel.setStyleSheet("background-color: #4b5263; color: white;")
            
        if emit_signal:
            self.play_toggled.emit(self.is_monitoring)

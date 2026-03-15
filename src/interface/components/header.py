from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton

class HeaderSection(QWidget):
    """Componente que agrupa o título e os botões de ação superiores."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Título
        title = QLabel("Monitoramento: Chamadas Ativas")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2d4157;")
        
        # Botões
        self.btn_history = QPushButton("🔍 Buscar Histórico")
        self.btn_history.setObjectName("ActionBtn")
        self.btn_history.setFixedWidth(180)

        self.btn_copy = QPushButton("📋 Copiar para WhatsApp")
        self.btn_copy.setObjectName("ActionBtn")
        self.btn_copy.setStyleSheet("background-color: #25D366; color: white;")
        self.btn_copy.setFixedWidth(220)

        self.btn_sync = QPushButton("🔄 Sincronizar CAD")
        self.btn_sync.setObjectName("ActionBtn")
        self.btn_sync.setFixedWidth(150)

        # Montagem
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self.btn_history)
        layout.addWidget(self.btn_copy)
        layout.addWidget(self.btn_sync)
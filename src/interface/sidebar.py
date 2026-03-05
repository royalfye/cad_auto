from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt

class SideBar(QFrame):
    def __init__(self, parent=None, switch_page_callback=None):
        super().__init__(parent)
        self.setObjectName("SideBar")
        self.switch_page = switch_page_callback
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header (Branding)
        brand_frame = QFrame()
        brand_layout = QVBoxLayout(brand_frame)
        brand_layout.setContentsMargins(20, 40, 20, 40)
        
        title = QLabel("🚒 GESTÃO\nCAD PASSOS")
        title.setObjectName("MainTitle")
        title.setWordWrap(True)
        brand_layout.addWidget(title)
        layout.addWidget(brand_frame)

        # Botões de Navegação
        self.btn_extracao = self._create_nav_btn("  📥 Extração (CAD)", 0)
        self.btn_process = self._create_nav_btn("  ⚙️ Processamento", 1)
        
        self.btn_extracao.setChecked(True)

        layout.addWidget(self.btn_extracao)
        layout.addWidget(self.btn_process)
        layout.addStretch()

        # Rodapé
        status_lbl = QLabel("V 1.2.0 | Ativo")
        status_lbl.setStyleSheet("color: #6a8296; padding: 20px; font-size: 11px;")
        layout.addWidget(status_lbl)

    def _create_nav_btn(self, text, index):
        btn = QPushButton(text)
        btn.setObjectName("NavBtn")
        btn.setCheckable(True)
        # Quando clica, avisa a janela principal para mudar de página
        btn.clicked.connect(lambda: self.switch_page(index))
        return btn
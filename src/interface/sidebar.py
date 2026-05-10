from datetime import datetime
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QComboBox
from PySide6.QtCore import Qt

# Importante: certifique-se que o caminho do import está correto para o seu projeto
from src.processing.services import calcular_ala_atual

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

        # 1. Header (Branding)
        brand_frame = QFrame()
        brand_layout = QVBoxLayout(brand_frame)
        brand_layout.setContentsMargins(20, 40, 20, 40)
        
        title = QLabel("🚒 GESTÃO\nCAD PASSOS")
        title.setObjectName("MainTitle")
        title.setWordWrap(True)
        brand_layout.addWidget(title)
        layout.addWidget(brand_frame)

        # 2. Configurações de Plantão (Seletor de Ala)
        self._create_shift_selector(layout)

        # 3. Botões de Navegação
        # Aqui é onde o erro acontecia; agora o método existe abaixo
        self.btn_extracao = self._create_nav_btn("   📥 Extração (CAD)", 0)
        self.btn_process = self._create_nav_btn("   ⚙️ Processamento", 1)
        
        self.btn_extracao.setChecked(True)

        layout.addWidget(self.btn_extracao)
        layout.addWidget(self.btn_process)
        layout.addStretch()

        # 4. Rodapé
        status_lbl = QLabel("V 1.2.0 | Ativo")
        status_lbl.setStyleSheet("color: #6a8296; padding: 20px; font-size: 11px;")
        layout.addWidget(status_lbl) # Adicione esta linha que faltava

    def _create_shift_selector(self, parent_layout):
        """Cria a seção de seleção da Ala delegando o visual para o QSS."""
        container = QFrame()
        container.setObjectName("AlaContainer")
        
        v_layout = QVBoxLayout(container)
        v_layout.setContentsMargins(10, 10, 10, 10)
        
        label = QLabel("ALA DE PLANTÃO")
        label.setObjectName("AlaLabel")
        
        self.combo_ala = QComboBox()
        self.combo_ala.setObjectName("AlaSelector")
        self.combo_ala.addItems(["1ª ALA", "2ª ALA", "3ª ALA", "4ª ALA"])
        
        # Lógica matemática de plantão
        ala_inicial = calcular_ala_atual(datetime.now())
        self.combo_ala.setCurrentIndex(ala_inicial - 1)
        
        v_layout.addWidget(label)
        v_layout.addWidget(self.combo_ala)
        parent_layout.addWidget(container)

    def _create_nav_btn(self, text, index):
        """Método auxiliar para criar os botões de navegação lateral."""
        btn = QPushButton(text)
        btn.setObjectName("NavBtn")
        btn.setCheckable(True)
        # Conecta o clique para mudar a página no sistema
        btn.clicked.connect(lambda: self.switch_page(index))
        return btn
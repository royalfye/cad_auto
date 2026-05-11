from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class ProcessPage(QWidget):
    def __init__(self):
        super().__init__()
        
        # Cria um layout simples
        layout = QVBoxLayout(self)
        
        # Cria um título grande no meio da tela
        titulo = QLabel("⚙️ Página de Processamento e Histórico")
        titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: #333333;")
        titulo.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(titulo)
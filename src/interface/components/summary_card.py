from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QTextEdit, QPushButton, QApplication
from PySide6.QtCore import QTimer

class SummaryCard(QFrame):
    """Componente especializado para o preview e cópia do relatório."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._configure_ui()

    def _configure_ui(self):
        self.setObjectName("SummaryCard")
        self.setFixedHeight(200)
        
        layout = QVBoxLayout(self)
        
        lbl_preview = QLabel("📋 Pré-visualização para WhatsApp:")
        lbl_preview.setStyleSheet("font-size: 11px; font-weight: bold; color: #6a8296;")
        
        self.txt_preview = QTextEdit()
        self.txt_preview.setReadOnly(True)
        self.txt_preview.setStyleSheet("background-color: #f8fafc; font-family: 'Consolas';")

        self.btn_copy_report = QPushButton("📋 Copiar Relatório Completo")
        self.btn_copy_report.setObjectName("SecondaryBtn")
        self.btn_copy_report.clicked.connect(self._copy_to_clipboard)

        layout.addWidget(lbl_preview)
        layout.addWidget(self.txt_preview)
        layout.addWidget(self.btn_copy_report)

    def update_text(self, text):
        """Atualiza o conteúdo do preview ou limpa se estiver vazio."""
        if text:
            self.txt_preview.setText(text)
        else:
            self.txt_preview.clear()
            self.txt_preview.setPlaceholderText("Nenhum dado encontrado para gerar o relatório.")

    def _copy_to_clipboard(self):
        """Lógica interna de cópia com feedback visual."""
        text = self.txt_preview.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.btn_copy_report.setText("✅ Relatório Copiado!")
            QTimer.singleShot(2000, lambda: self.btn_copy_report.setText("📋 Copiar Relatório Completo"))
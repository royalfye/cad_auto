from PySide6.QtWidgets import QLabel, QFrame, QProgressBar, QVBoxLayout, QWidget

from src.interface.components.active_table import ActiveCallsTable
from src.interface.components.header import HeaderSection
from src.interface.components.summary_card import SummaryCard


class ActiveCallsPage(QWidget):
    """Page responsible only for the active calls UI composition."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

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

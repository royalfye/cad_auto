from PySide6.QtCore import Qt, QAbstractTableModel
from PySide6.QtGui import QColor, QFont

STATUS_COLORS = {
    'Atribuída ao órgão': "#2ecc71",
    'No local':           "#e74c3c",
    'Em controle':        "#D1D5DB",
    'Terminada':          "#2c3e50",
    'À caminho':          "#3498db",
    'Despachada':         "#f1c40f",
    'Em retorno':         "#e67e22"
}

class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
            
        row = index.row()
        col = index.column()
        col_name = self._data.columns[col]
        
        # Pega o valor da célula atual
        cell_value = self._data.iloc[row, col]

        # 1. TEXTO
        if role == Qt.DisplayRole:
            return str(cell_value)

        # 2. COR DA FONTE (Indicador de Status)
        if role == Qt.ForegroundRole:
            if col_name == 'status_indicator':
                # Buscamos o valor da coluna 'status' na mesma linha
                status_value = self._data.iloc[row]['status'] if 'status' in self._data.columns else ""
                color_hex = STATUS_COLORS.get(status_value, "#e74c3c")
                return QColor(color_hex)
            return QColor("#212529")

        # 3. ESTILO DA FONTE
        if role == Qt.FontRole and col_name == 'status_indicator':
            font = QFont()
            font.setPointSize(14)
            font.setBold(True)
            return font

        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            label = self._data.columns[section]
            return "ST" if label == 'status_indicator' else str(label).upper()
        return None
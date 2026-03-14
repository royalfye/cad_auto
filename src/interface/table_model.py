from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
# Importante: Importar o modelo que criamos no Degrau 1
from src.processing.models import Ocorrencia 

class OcorrenciaTableModel(QAbstractTableModel):
    def __init__(self, ocorrencias=None):
        super().__init__()
        # Lista de objetos Ocorrencia
        self.ocorrencias = ocorrencias or []
        self.headers = ["ST", "ID", "Horário", "Natureza", "Endereço", "Status"]

    def rowCount(self, parent=QModelIndex()):
        return len(self.ocorrencias)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.ocorrencias)):
            return None
        
        ocorrencia = self.ocorrencias[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            # Mapeia as colunas para os atributos do objeto Ocorrencia
            mapping = {
                0: ocorrencia.status_icone,
                1: ocorrencia.id_chamada,
                2: ocorrencia.horario,
                3: ocorrencia.natureza,
                4: ocorrencia.endereco,
                5: ocorrencia.status
            }
            return mapping.get(col)
        
        if role == Qt.TextAlignmentRole:
            if col in [0, 1, 5]: return Qt.AlignCenter
            
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
# Importante: Importar o modelo que criamos no Degrau 1
from src.processing.models import Ocorrencia 

class OcorrenciaTableModel(QAbstractTableModel):
    def __init__(self, ocorrencias=None):
        super().__init__()
        # Lista de objetos Ocorrencia
        self.ocorrencias = ocorrencias or []
        self.headers = ["Sel", "ST", "ID", "Horário", "Natureza", "Endereço", "Status"]

    def rowCount(self, parent=QModelIndex()):
        return len(self.ocorrencias)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.ocorrencias)):
            return None

        ocorrencia = self.ocorrencias[index.row()]
        col = index.column()

        # NOVIDADE: O CheckStateRole controla o quadradinho de marcação
        if role == Qt.CheckStateRole and col == 0:
            return Qt.Checked if ocorrencia.selecionado else Qt.Unchecked

        if role == Qt.DisplayRole:
            if col == 0: return None
            mapping = {
                1: ocorrencia.status_icone,
                2: ocorrencia.id_chamada,
                3: ocorrencia.horario,
                4: ocorrencia.natureza,
                5: ocorrencia.endereco,
                6: ocorrencia.status
            }
            return mapping.get(col)
        
        if role == Qt.TextAlignmentRole:
            if col in [0, 1, 5]: return Qt.AlignCenter
            
        return None
    
    def flags(self, index):
        """Define as permissões de cada célula."""
        if not index.isValid():
            return Qt.NoItemFlags

        # Pegamos as permissões padrão (ex: selecionar a linha)
        default_flags = super().flags(index)

        # Se for a coluna 0 (a do Checkbox), damos permissão de 'Checkable'
        if index.column() == 0:
            return default_flags | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled
        
        return default_flags

    def setData(self, index, value, role=Qt.EditRole):
        """Este método é chamado pelo PySide6 quando você clica na caixinha."""
        if role == Qt.CheckStateRole and index.column() == 0:
            # 1. Localiza a ocorrência na lista
            ocorrencia = self.ocorrencias[index.row()]
            
            # 2. Atualiza o valor no nosso objeto (True se marcado, False se desmarcado)
            ocorrencia.selecionado = (value == Qt.Checked)
            
            # 3. Importante: Avisa a interface que o dado mudou para ela se "repintar"
            self.dataChanged.emit(index, index, [Qt.CheckStateRole])
            return True
            
        return False
    
    def selecionar_todas(self, estado: bool):
        """Marca ou desmarca todas as ocorrências da lista."""
        if not self.ocorrencias:
            return

        # Começamos a sinalizar a mudança
        self.layoutAboutToBeChanged.emit()
        
        for oc in self.ocorrencias:
            oc.selecionado = estado
            
        # Finalizamos a sinalização para a tabela atualizar o visual
        self.layoutChanged.emit()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self.headers[section]
            
            if role == Qt.ToolTipRole and section == 0:
                return "Clique aqui para selecionar/desmarcar todas as chamadas"
        
        return None
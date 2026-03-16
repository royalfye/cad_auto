from PySide6.QtWidgets import QTableView, QHeaderView

class ActiveCallsTable(QTableView):
    """Componente especializado para a tabela de chamadas ativas."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._configure_style()

    def _configure_style(self):
        """Define o comportamento visual da tabela."""
        self.setAlternatingRowColors(True)
        
        # IMPORTANTE: Mudamos para permitir que o clique chegue à célula individual
        self.setSelectionBehavior(QTableView.SelectItems) 
        self.setSelectionMode(QTableView.SingleSelection)
        
        # UX: Faz com que o utilizador sinta que a tabela é interativa
        self.setEditTriggers(QTableView.AllEditTriggers) 
        
        h_header = self.horizontalHeader()
        h_header.setStretchLastSection(True)
        
    def update_data(self, model):
        """Atualiza o modelo de dados e ajusta as colunas."""
        self.setModel(model)
        self.resizeColumnsToContents()
        self.setColumnWidth(0, 50) # ID geralmente é pequeno
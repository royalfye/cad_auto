from PySide6.QtWidgets import QTableView, QHeaderView

class ActiveCallsTable(QTableView):
    """Componente especializado para a tabela de chamadas ativas."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._configure_style()

    def _configure_style(self):
        """Define o comportamento visual da tabela."""
        self.setAlternatingRowColors(True)
        
        # IMPORTANTE: Use SelectItems para não bloquear o clique na célula da caixa
        self.setSelectionBehavior(QTableView.SelectItems) 
        self.setSelectionMode(QTableView.SingleSelection)
        
        # Permite que o clique ative a edição (o check) imediatamente
        self.setEditTriggers(QTableView.AllEditTriggers) 
        
        h_header = self.horizontalHeader()
        h_header.setStretchLastSection(True)
        h_header.sectionClicked.connect(self._on_header_clicked)
        
    def _on_header_clicked(self, logical_index):
        """Lógica para selecionar tudo ao clicar no topo da coluna 0."""
        # Se o clique foi na coluna 0 (onde está o nosso Checkbox)
        if logical_index == 0:
            model = self.model()
            if not model or not model.ocorrencias:
                return

            # Lógica de alternância (Toggle): 
            # Se a primeira ocorrência já estiver selecionada, a intenção é desmarcar todas.
            # Caso contrário, selecionamos todas.
            novo_estado = not model.ocorrencias[0].selecionado
            model.selecionar_todas(novo_estado)

    def update_data(self, model):
        """Atualiza o modelo de dados e ajusta as colunas."""
        self.setModel(model)
        self.resizeColumnsToContents()
        self.setColumnWidth(0, 50) # Coluna do Checkbox/Sel
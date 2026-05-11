from pathlib import Path
import pandas as pd
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QMessageBox, QTabWidget)
from PySide6.QtCore import Qt

class ProcessPage(QWidget):
    def __init__(self):
        super().__init__()
        self.csv_path = Path(__file__).resolve().parent.parent.parent.parent / "data" / "02_silver" / "vehicle_calls.csv"
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # --- 1. Barra de Ferramentas ---
        toolbar_layout = QHBoxLayout()
        self.btn_carregar = QPushButton("🔄 Carregar Viaturas")
        self.btn_salvar = QPushButton("💾 Exportar Planilhas")
        self.btn_salvar.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        
        toolbar_layout.addWidget(self.btn_carregar)
        toolbar_layout.addStretch() 
        toolbar_layout.addWidget(self.btn_salvar)
        layout.addLayout(toolbar_layout)

        # --- 2. O Pulo do Gato: Sistema de Abas ---
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # --- 3. Conexões ---
        self.btn_carregar.clicked.connect(self.carregar_dados)
        self.btn_salvar.clicked.connect(self.exportar_excel)

    def carregar_dados(self):
        if not self.csv_path.exists():
            QMessageBox.warning(self, "Aviso", "Arquivo CSV não encontrado.")
            return

        try:
            df = pd.read_csv(self.csv_path).fillna("")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao ler o arquivo: {e}")
            return

        # Limpa as abas caso o usuário clique em "Carregar" mais de uma vez
        self.tabs.clear()

        # Evita erro caso alguma linha não tenha o nome da viatura preenchido
        df['Recurso'] = df['Recurso'].replace("", "SEM VIATURA")

        # Agrupa os dados usando Pandas (mágica da engenharia de dados aqui!)
        grupos_viaturas = df.groupby('Recurso')

        # Para cada viatura encontrada, criamos uma tabela nova
        for recurso, df_grupo in grupos_viaturas:
            tabela = QTableWidget()
            tabela.setAlternatingRowColors(True)
            tabela.setStyleSheet("alternate-background-color: #f0f0f0; background-color: #ffffff; color: black;")
            
            tabela.setColumnCount(len(df_grupo.columns))
            tabela.setHorizontalHeaderLabels(df_grupo.columns)
            tabela.setRowCount(len(df_grupo))

            # Preenche a tabela específica desta viatura
            for row_idx, (index, row_data) in enumerate(df_grupo.iterrows()):
                for col_idx, col_name in enumerate(df_grupo.columns):
                    valor = str(row_data[col_name])
                    item = QTableWidgetItem(valor)
                    item.setTextAlignment(Qt.AlignCenter)
                    tabela.setItem(row_idx, col_idx, item)

            header = tabela.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeToContents)
            header.setStretchLastSection(True)

            # Adiciona a tabela como uma nova aba com o nome do recurso
            self.tabs.addTab(tabela, f"🚒 {recurso}")

        QMessageBox.information(self, "Sucesso", "Viaturas organizadas em abas com sucesso!")

    def exportar_excel(self):
        """Exporta cada aba da interface como uma planilha separada no Excel."""
        if self.tabs.count() == 0:
            QMessageBox.warning(self, "Erro", "A tabela está vazia. Carregue os dados primeiro.")
            return

        output_dir = self.csv_path.parent.parent / "03_gold"
        output_dir.mkdir(parents=True, exist_ok=True)
        excel_path = output_dir / "controle_viaturas_final.xlsx"

        try:
            # O ExcelWriter do Pandas permite salvar várias abas no mesmo arquivo
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                
                # Percorre todas as abas que criamos na tela
                for index_aba in range(self.tabs.count()):
                    
                    # Pega o nome da aba e remove o emoji para o Excel não reclamar
                    nome_aba = self.tabs.tabText(index_aba).replace("🚒 ", "")
                    
                    # Pega a tabela que está dentro desta aba
                    tabela = self.tabs.widget(index_aba)
                    
                    rows = tabela.rowCount()
                    cols = tabela.columnCount()
                    headers = [tabela.horizontalHeaderItem(i).text() for i in range(cols)]
                    
                    # Varre a tabela capturando o que você digitou/editou
                    data = []
                    for row in range(rows):
                        row_data = []
                        for col in range(cols):
                            item = tabela.item(row, col)
                            row_data.append(item.text() if item else "")
                        data.append(row_data)

                    # Salva esta aba específica dentro do arquivo Excel
                    df_editado = pd.DataFrame(data, columns=headers)
                    df_editado.to_excel(writer, sheet_name=nome_aba, index=False)

            QMessageBox.information(self, "Sucesso", f"Excel gerado com sucesso!\nSalvo em: {excel_path}")
            
            import os
            os.startfile(output_dir)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar o arquivo:\n{str(e)}")
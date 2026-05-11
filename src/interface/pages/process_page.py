from pathlib import Path
import pandas as pd
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QMessageBox, QTabWidget, 
                               QLabel, QLineEdit, QComboBox)
from PySide6.QtCore import Qt

class ProcessPage(QWidget):
    def __init__(self):
        super().__init__()
        self.csv_path = Path(__file__).resolve().parent.parent.parent.parent / "data" / "02_silver" / "vehicle_calls.csv"
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # --- Barra Superior Geral ---
        toolbar_layout = QHBoxLayout()
        self.btn_carregar = QPushButton("🔄 Carregar Viaturas")
        self.btn_salvar = QPushButton("💾 Exportar Planilhas")
        self.btn_salvar.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        
        toolbar_layout.addWidget(self.btn_carregar)
        toolbar_layout.addStretch() 
        toolbar_layout.addWidget(self.btn_salvar)
        layout.addLayout(toolbar_layout)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

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

        self.tabs.clear()
        df['Recurso'] = df['Recurso'].replace("", "SEM VIATURA")
        grupos_viaturas = df.groupby('Recurso')

        for recurso, df_grupo in grupos_viaturas:
            # --- Container da Aba ---
            aba_widget = QWidget()
            aba_layout = QVBoxLayout(aba_widget)

            # --- Painel de Estimativa de KM (Barra superior da aba) ---
            km_panel = QHBoxLayout()
            
            lbl_inicial = QLabel("KM Inicial:")
            input_inicial = QLineEdit()
            input_inicial.setPlaceholderText("Ex: 5963")
            input_inicial.setFixedWidth(80)

            lbl_final = QLabel("KM Final:")
            input_final = QLineEdit()
            input_final.setPlaceholderText("Ex: 6011")
            input_final.setFixedWidth(80)

            btn_estimar = QPushButton("⚡ Estimar KM")
            btn_estimar.setStyleSheet("background-color: #f39c12; color: white;")
            
            km_panel.addWidget(lbl_inicial)
            km_panel.addWidget(input_inicial)
            km_panel.addWidget(lbl_final)
            km_panel.addWidget(input_final)
            km_panel.addWidget(btn_estimar)
            km_panel.addStretch()
            
            aba_layout.addLayout(km_panel)

            # --- Tabela ---
            tabela = QTableWidget()
            tabela.setAlternatingRowColors(True)
            tabela.setColumnCount(len(df_grupo.columns))
            tabela.setHorizontalHeaderLabels(df_grupo.columns)
            tabela.setRowCount(len(df_grupo))

            # Antes do loop, carregamos a lista de nomes formatados
            lista_militares = self.carregar_efetivo()

            for row_idx, (index, row_data) in enumerate(df_grupo.iterrows()):
                for col_idx, col_name in enumerate(df_grupo.columns):
                    
                    if col_name == "Motorista":
                        # Criamos o seletor (ComboBox)
                        combo = QComboBox()
                        combo.addItems(lista_militares)
                        
                        # Se já houver um motorista no CSV (raro na primeira carga), tentamos selecionar
                        valor_atual = str(row_data[col_name])
                        combo.setCurrentText(valor_atual)
                        
                        # Colocamos o seletor dentro da célula da tabela
                        tabela.setCellWidget(row_idx, col_idx, combo)
                    else:
                        item = QTableWidgetItem(str(row_data[col_name]))
                        item.setTextAlignment(Qt.AlignCenter)
                        tabela.setItem(row_idx, col_idx, item)
                        
            tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            tabela.horizontalHeader().setStretchLastSection(True)
            aba_layout.addWidget(tabela)

            # --- Lógica do Botão Estimar ---
            # Usamos uma função lambda para passar os dados específicos desta aba
            btn_estimar.clicked.connect(lambda ch=None, t=tabela, i=input_inicial, f=input_final: 
                                        self.estimar_quilometragem(t, i, f))

            self.tabs.addTab(aba_widget, f"🚒 {recurso}")

    def estimar_quilometragem(self, tabela, input_ini, input_fim):
        """Calcula e distribui a quilometragem nas linhas da tabela."""
        try:
            km_ini = int(input_ini.text())
            km_fim = int(input_fim.text())
        except ValueError:
            QMessageBox.warning(self, "Erro", "Por favor, insira apenas números inteiros nos campos de KM.")
            return

        if km_fim <= km_ini:
            QMessageBox.warning(self, "Erro", "O KM Final deve ser maior que o Inicial.")
            return

        total_linhas = tabela.rowCount()
        km_total = km_fim - km_ini
        
        # Cálculo da base e do resto (para distribuir os arredondamentos)
        km_por_chamada = km_total // total_linhas
        resto = km_total % total_linhas

        km_atual = km_ini

        # Precisamos descobrir quais colunas são "Km Saída" e "Km Chegada"
        col_saida = -1
        col_chegada = -1
        for c in range(tabela.columnCount()):
            header = tabela.horizontalHeaderItem(c).text()
            if "Km Saída" in header: col_saida = c
            if "Km Chegada" in header: col_chegada = c

        if col_saida == -1 or col_chegada == -1:
            QMessageBox.warning(self, "Erro", "Colunas de KM não encontradas na tabela.")
            return

        # Preenchimento das linhas
        for row in range(total_linhas):
            # Distribuímos o "resto" nas primeiras linhas para fechar a conta exata
            incremento = km_por_chamada + (1 if row < resto else 0)
            proximo_km = km_atual + incremento
            
            tabela.setItem(row, col_saida, QTableWidgetItem(str(km_atual)))
            tabela.setItem(row, col_chegada, QTableWidgetItem(str(proximo_km)))
            
            # Centralizar o texto novo
            tabela.item(row, col_saida).setTextAlignment(Qt.AlignCenter)
            tabela.item(row, col_chegada).setTextAlignment(Qt.AlignCenter)
            
            km_atual = proximo_km

        QMessageBox.information(self, "Sucesso", f"KM estimado com base em {km_total}km percorridos.")

    def exportar_excel(self):
        # A lógica de exportar precisa de um pequeno ajuste para achar a tabela dentro do widget da aba
        if self.tabs.count() == 0: return

        output_dir = self.csv_path.parent.parent / "03_gold"
        output_dir.mkdir(parents=True, exist_ok=True)
        excel_path = output_dir / "controle_viaturas_final.xlsx"

        try:
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                for i in range(self.tabs.count()):
                    nome_aba = self.tabs.tabText(i).replace("🚒 ", "")
                    # Agora a tabela não é mais o widget principal, ela está DENTRO do layout do widget
                    aba_widget = self.tabs.widget(i)
                    tabela = aba_widget.findChild(QTableWidget)
                    
                    rows = tabela.rowCount()
                    cols = tabela.columnCount()
                    headers = [tabela.horizontalHeaderItem(c).text() for c in range(cols)]
                    
                    data = []
                    # --- A MÁGICA DA TRADUÇÃO ACONTECE NESTE BLOCO ---
                    for r in range(rows):
                        row_data = []
                        for c in range(cols):
                            header_nome = headers[c] # Nome da coluna que estamos lendo agora
                            
                            if header_nome == "Motorista":
                                # Pega o menu suspenso (ComboBox) da célula
                                combo = tabela.cellWidget(r, c)
                                nome_guerra = combo.currentText() if combo else ""
                                
                                # Traduz usando o dicionário que criamos no carregar_efetivo()
                                nome_final = getattr(self, 'mapa_motoristas', {}).get(nome_guerra, nome_guerra)
                                row_data.append(nome_final)
                            else:
                                # Se for as outras colunas (KM, endereço, etc), lê o texto normalmente
                                item = tabela.item(r, c)
                                row_data.append(item.text() if item else "")
                                
                        data.append(row_data)
                    # -------------------------------------------------
                    
                    pd.DataFrame(data, columns=headers).to_excel(writer, sheet_name=nome_aba, index=False)
            
            QMessageBox.information(self, "Sucesso", "Planilha exportada!")
            import os
            os.startfile(output_dir)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro: {e}")


    def carregar_efetivo(self):
        """Lê o arquivo de pessoal e cria uma lista para o menu de seleção."""
        
        # 1. Ajustamos o caminho para a pasta correta e o formato .xlsx
        caminho_pessoal = Path(__file__).resolve().parent.parent.parent.parent / "data" / "02_silver" / "personal_info.xlsx"

        self.mapa_placas = {
            "ABT00816": "HMH3919",
            "ASL07161": "TEH7B61",
            "UR04360": "QXW4D60",
            "VOB00480": "SYZ0E80"
            # Você pode adicionar as outras viaturas da 2ª CIA aqui depois
        }
        
        self.mapa_motoristas = {} # Dicionário para traduzir Nome de Guerra -> Nome Completo
        lista_formatada = [""] # Começa com uma opção vazia

        try:
            # 2. Mudamos de read_csv para read_excel
            df_pessoal = pd.read_excel(caminho_pessoal)
            
            for _, row in df_pessoal.iterrows():
                # Criamos o nome que o militar reconhece: "2 SGT RENATO"
                identidade_militar = f"{row['Rank']} {row['War Name']}"
                nome_completo = row['Name']
                
                self.mapa_motoristas[identidade_militar] = nome_completo
                lista_formatada.append(identidade_militar)
                
            return sorted(lista_formatada)
        except Exception as e:
            print(f"Erro ao carregar efetivo: {e}")
            return [""]
from pathlib import Path
import pandas as pd
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QMessageBox, QTabWidget, 
                               QLabel, QLineEdit, QComboBox, QStyledItemDelegate)

from PySide6.QtCore import Qt

class MotoristaDelegate(QStyledItemDelegate):
    def __init__(self, mapa_motoristas, parent=None):
        super().__init__(parent)
        self.mapa_motoristas = mapa_motoristas
        # Cria a lista de opções ordenada: ["", "1 SGT ANDERSON", "2 SGT RENATO", ...]
        self.lista_opcoes = [""] + sorted(self.mapa_motoristas.keys())

    def createEditor(self, parent, option, index):
        # Quando o usuário der duplo-clique, criamos o ComboBox
        combo = QComboBox(parent)
        combo.addItems(self.lista_opcoes)
        return combo

    def setEditorData(self, editor, index):
        # Lê o "Nome Completo" que está na célula atualmente
        nome_completo_atual = index.model().data(index, Qt.EditRole)
        
        # Faz o caminho reverso: acha o "Nome de Guerra" para mostrar no ComboBox
        nome_guerra = ""
        for guerra, completo in self.mapa_motoristas.items():
            if completo == nome_completo_atual:
                nome_guerra = guerra
                break
        
        editor.setCurrentText(nome_guerra)

    def setModelData(self, editor, model, index):
        # Pega o "Nome de Guerra" que o usuário escolheu no menu
        nome_guerra_escolhido = editor.currentText()
        
        # Traduz para o "Nome Completo"
        nome_completo = self.mapa_motoristas.get(nome_guerra_escolhido, "")
        
        # Salva o "Nome Completo" direto no texto da tabela
        model.setData(index, nome_completo, Qt.EditRole)

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
        self.btn_siad = QPushButton("🤖 Gerar Arquivos SIAD")
        self.btn_salvar.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        self.btn_siad.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;") # Cor roxa para diferenciar
        
        toolbar_layout.addWidget(self.btn_carregar)
        toolbar_layout.addStretch() 
        toolbar_layout.addWidget(self.btn_salvar)
        toolbar_layout.addWidget(self.btn_siad)
        layout.addLayout(toolbar_layout)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.btn_carregar.clicked.connect(self.carregar_dados)
        self.btn_salvar.clicked.connect(self.exportar_excel)
        self.btn_siad.clicked.connect(self.gerar_csv_siad)

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

        # Carrega o efetivo UMA VEZ antes de montar as abas para não pesar o programa
        self.carregar_efetivo()

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

            # --- A MÁGICA DO DELEGATE ENTRA AQUI ---
            # Identificamos qual é o número da coluna "Motorista"
            if "Motorista" in df_grupo.columns:
                idx_motorista = list(df_grupo.columns).index("Motorista")
                
                # Criamos a nossa máscara mágica (Delegate) e aplicamos SÓ nessa coluna
                delegate = MotoristaDelegate(self.mapa_motoristas, tabela)
                tabela.setItemDelegateForColumn(idx_motorista, delegate)
            # ----------------------------------------

            # Preenchimento SUPER SIMPLES: tudo entra como texto puro na tabela
            for row_idx, (index, row_data) in enumerate(df_grupo.iterrows()):
                for col_idx, col_name in enumerate(df_grupo.columns):
                    valor = str(row_data[col_name])
                    item = QTableWidgetItem(valor)
                    item.setTextAlignment(Qt.AlignCenter)
                    tabela.setItem(row_idx, col_idx, item)

            tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            tabela.horizontalHeader().setStretchLastSection(True)
            aba_layout.addWidget(tabela)

            # --- Lógica do Botão Estimar ---
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
        """Exporta cada aba da interface como uma planilha separada no Excel."""
        if self.tabs.count() == 0: 
            return

        # Define o caminho de salvamento
        output_dir = self.csv_path.parent.parent / "03_gold"
        output_dir.mkdir(parents=True, exist_ok=True)
        excel_path = output_dir / "controle_viaturas_final.xlsx"

        try:
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                for i in range(self.tabs.count()):
                    nome_aba = self.tabs.tabText(i).replace("🚒 ", "")
                    
                    # Encontra a tabela dentro da aba
                    aba_widget = self.tabs.widget(i)
                    tabela = aba_widget.findChild(QTableWidget)
                    
                    rows = tabela.rowCount()
                    cols = tabela.columnCount()
                    headers = [tabela.horizontalHeaderItem(c).text() for c in range(cols)]
                    
                    # --- AQUI ESTÁ O BLOCO SIMPLIFICADO ---
                    # Lê o texto de cada célula da tabela diretamente
                    data = []
                    for r in range(rows):
                        row_data = []
                        for c in range(cols):
                            item = tabela.item(r, c)
                            row_data.append(item.text() if item else "")
                        data.append(row_data)
                    # --------------------------------------
                    
                    # Salva no arquivo Excel
                    pd.DataFrame(data, columns=headers).to_excel(writer, sheet_name=nome_aba, index=False)
            
            QMessageBox.information(self, "Sucesso", "Planilha exportada com sucesso!")
            
            # Abre a pasta para o usuário ver o arquivo
            import os
            os.startfile(output_dir)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar o arquivo:\n{str(e)}")


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

        self.mapa_placas = {
            "ABT00816": "HMH3919",
            "ASL07161": "TEH7B61",
            "UR04360": "QXW4D60",
            "VOB00480": "SYZ0E80"
            # Conforme descobrir as outras, é só adicionar aqui!
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
        
    def gerar_csv_siad(self):
        """Gera arquivos CSV simplificados e separados por viatura para o UI.Vision."""
        if self.tabs.count() == 0:
            QMessageBox.warning(self, "Erro", "Carregue os dados primeiro.")
            return

        # Cria uma nova pasta específica para os robôs
        output_dir = self.csv_path.parent.parent / "04_siad_macros"
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            for i in range(self.tabs.count()):
                nome_viatura = self.tabs.tabText(i).replace("🚒 ", "")
                # Traduz o nome da viatura para a placa. Se não achar, avisa no arquivo.
                placa = getattr(self, 'mapa_placas', {}).get(nome_viatura, "PLACA_NAO_CADASTRADA")
                
                aba_widget = self.tabs.widget(i)
                tabela = aba_widget.findChild(QTableWidget)
                
                rows = tabela.rowCount()
                headers = [tabela.horizontalHeaderItem(c).text() for c in range(tabela.columnCount())]
                
                # Encontra onde estão as colunas que nos interessam
                idx_saida = headers.index("Saída") if "Saída" in headers else -1
                idx_km_saida = headers.index("Km Saída") if "Km Saída" in headers else -1
                idx_km_cheg = headers.index("Km Chegada") if "Km Chegada" in headers else -1
                idx_motorista = headers.index("Motorista") if "Motorista" in headers else -1

                dados_siad = []
                
                for r in range(rows):
                    # 1. Tratar Data e Hora
                    saida_raw = tabela.item(r, idx_saida).text() if idx_saida != -1 and tabela.item(r, idx_saida) else ""
                    data_atendimento = ""
                    hora_atendimento = ""
                    
                    if " " in saida_raw:
                        partes = saida_raw.split(" ")
                        data_atendimento = partes[0]       # Extrai só "10/05/2026"
                        hora_atendimento = partes[1][:5]   # Extrai só "10:03" (corta os segundos)

                    # 2. Pegar Quilometragens
                    km_ini = tabela.item(r, idx_km_saida).text() if idx_km_saida != -1 and tabela.item(r, idx_km_saida) else ""
                    km_fim = tabela.item(r, idx_km_cheg).text() if idx_km_cheg != -1 and tabela.item(r, idx_km_cheg) else ""
                    
                    # 3. Pegar Nome Completo do Motorista
                    combo = tabela.cellWidget(r, idx_motorista) if idx_motorista != -1 else None
                    nome_guerra = combo.currentText() if combo else ""
                    nome_completo = getattr(self, 'mapa_motoristas', {}).get(nome_guerra, nome_guerra)

                    # 4. Monta a linha pronta para o robô ler
                    linha = {
                        "PLACA": placa,
                        "DATA": data_atendimento,
                        "HORA": hora_atendimento,
                        "KM_INICIAL": km_ini,
                        "KM_FINAL": km_fim,
                        "MOTORISTA": nome_completo
                    }
                    dados_siad.append(linha)
                
                # Salva o arquivo apenas desta viatura!
                if dados_siad:
                    df_siad = pd.DataFrame(dados_siad)
                    caminho_csv = output_dir / f"SIAD_{nome_viatura}.csv"
                    # Salvamos sem os cabeçalhos (index=False, header=False) para o robô ler a partir da linha 1
                    df_siad.to_csv(caminho_csv, index=False, header=False, encoding='utf-8')
            
            QMessageBox.information(self, "Sucesso", f"Arquivos CSV para o UI.Vision gerados com sucesso na pasta:\\n{output_dir}")
            import os
            os.startfile(output_dir)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar arquivos do SIAD:\\n{str(e)}")
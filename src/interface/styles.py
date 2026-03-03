STYLE_SHEET = """
QMainWindow { 
    background-color: #f3f3f9; 
}

/* Sidebar / Barra Lateral */
#SideBar { 
    background-color: #2d4157; 
    min-width: 250px; 
    max-width: 250px;
    border-right: 1px solid #d0d0d0;
}

/* Títulos */
QLabel#MainTitle { 
    font-size: 20px; 
    font-weight: bold; 
    color: #f77965; 
    padding: 10px;
}

QLabel#SubTitle { 
    font-size: 13px; 
    color: #8fa3b2; 
    padding-left: 10px;
}

/* Cards Flutuantes */
QFrame#Card { 
    background-color: #ffffff; 
    border-radius: 12px; 
    border: none;
}

QLabel#CardTitle { 
    font-size: 16px; 
    font-weight: bold; 
    color: #2d4157; 
}

/* Botões de Navegação (Sidebar) */
QPushButton#NavBtn {
    background-color: transparent;
    color: #ffffff;
    text-align: left;
    padding: 15px;
    border: none;
    font-size: 14px;
    border-radius: 0px;
}
QPushButton#NavBtn:hover {
    background-color: #3e5670;
    border-left: 4px solid #f77965;
}
QPushButton#NavBtn:checked {
    background-color: #3e5670;
    border-left: 4px solid #f77965;
    font-weight: bold;
}

/* Botão de Ação Coral */
QPushButton#ActionBtn {
    background-color: #f77965;
    color: white;
    border-radius: 8px;
    padding: 12px;
    font-weight: bold;
    font-size: 13px;
    border: none;
}
QPushButton#ActionBtn:hover {
    background-color: #e66854;
}
QPushButton#ActionBtn:pressed {
    background-color: #d45b49;
}

/* Tabelas */
QTableWidget {
    background-color: #ffffff;
    gridline-color: #f0f0f0;
    border-radius: 8px;
    border: 1px solid #e0e0e0;
}
QHeaderView::section {
    background-color: #2d4157;
    color: white;
    padding: 6px;
    border: none;
}

/* Barra de Progresso */
QProgressBar {
    background-color: #e0e0e0;
    color: white;
    border-radius: 5px;
    text-align: center;
    height: 10px;
}
QProgressBar::chunk {
    background-color: #f77965;
    border-radius: 5px;
}
"""
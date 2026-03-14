# Automação e Dashboard - Gestão de Chamadas (CBMMG)

Este projeto possui a finalidade de automatizar alguma funções do CAD e implementar algumas melhorias para o dia a dia.
O CAD é um sistema chamado "legado", pois possui uma arquitetura em linguagem de programação mais antiga, comuns em aplicações do serviço público.


## 🛠️ Tecnologias e Bibliotecas
* **Python 3.12+**: Linguagem base.
* **PySide6**: Interface do usuário.
* **Pandas**: Processamento e transformação dos arquivos em .csv.
* **PyAutoGUI & PyGetWindow**: Automação RPA baseada em visão computacional.
* **Psutil**: Gerenciamento de processos do sistema (limpeza de ambiente).

## 🚀 Como Executar
1. **Ambiente Virtual**: `python -m venv .venv`
2. **Ativação**: `.\.venv\Scripts\Activate.ps1`
3. **Dependências**: `pip install -r requirements`
4. **Execução**: `py src/interface/app.py`

## 🤖 A Interface
O bot utiliza um fluxo de decisão em cascata para garantir estabilidade:
1. **Sincronizar CAD**: O software irá alterar automaticamente para a janela já aberta do CAD e fará a extração da tabela das chamadas ativas, aplicando os filtros para isolar apenas as chamadas de 'Passos'.
2. **Buscar Histórico**: Realiza a extração do histórico da ocorrência. Com a linha da chamada em questão já pré-selecionada, o software altera automaticamente para a janela já aberta do CAD e faz a extração do histórico.
3. **Copiar para WhatsApp**: Formata a chamada para envio de mensagem via WhatsApp, sintetizando os dados e criando o link do google maps.

## 🏗️ Estrutura do Projeto

<details>
  <summary>Clique para expandir a árvore de diretórios</summary>

```text
cad_auto/
├── assets/
│   ├── images/
│   │   └── cad_targets/
│   │       ├── 01_filter_passos_active.png
│   │       ├── 02_chamadas_button.png
│   │       ├── 03_pesquisa_button.png
│   │       ├── 04_classificadas_button.png
│   │       ├── 05_ultimas_24_button.png
│   │       ├── 06_ultimos_3_button.png
│   │       ├── 07_filtro_passos.button.png
│   │       ├── 08_passos_button.png
│   │       ├── 09_exportar_button.png
│   │       ├── 10_ativas_button.png
│   │       ├── 11_call_number_ref.png
│   │       ├── 12_historico_button_01.png
│   │       ├── 12_historico_button_02.png
│   │       ├── 13_pencil_button.png
│   │       └── 14_tabela_header.png
│   └── styles.qss
├── data/
├── src/
│   ├── bot/
│   │   ├── cad_bot.py
│   │   └── history_bot.py
│   ├── interface/
│   │   ├── app.py
│   │   ├── models.py
│   │   ├── sidebar.py
│   │   ├── styles.py
│   │   ├── table_model.py
│   │   └── workers.py
│   ├── processing/
│   │   ├── data_handler.py
│   │   ├── models.py
│   │   └── services.py
│   ├── utils/
│   │   └── tree_viewer.py
│   └── __init__.py
├── README.md
└── requirements.txt
```

## 🤖 Como funciona
O software possui 3 principais pastas:
1. **assets**: Onde contém os arquivos de imagem utilizados para reconhecimento da automação.
2. **data**: Onde estão armazenados os dados extraídos do CAD.
3. **src**: Onde está presente o frontend e backend da aplicação.

## Source
Na pasta 'src' contém 4 principais pastas:
1. **bot**: Pasta onde contém os arquivos de automação para extração das chamadas e dos históricos, 'cad_bot.py' e 'history_bot.py'
2. **interface**: Onde está armazenando o frontend do projeto, onde chama as demais funções de automação e exibe as informações para o usuário.
3. **processing**: Pasta onde ocorre o processamento dos dados extraídos da automação. Aplicando filtros, deleções e aprimorando para apresentar da melhor forma possível ao usuário.
4. **utils**: Ferramentas para melhorar o código.
# Automação e Dashboard - Gestão de Chamadas (CBMMG)

Este projeto automatiza a extração de dados do sistema **CAD (Java)** e processa as informações utilizando a **Arquitetura Medalhão** para exibição em um dashboard interativo. O sistema é focado na otimização da análise de ocorrências da **2ª CIA Passos**.



## 🛠️ Tecnologias e Bibliotecas
* **Python 3.12+**: Linguagem base.
* **Streamlit**: Interface do usuário e orquestração do pipeline.
* **Pandas**: Processamento e transformação de grandes volumes de dados (ETL).
* **PyAutoGUI & PyGetWindow**: Automação RPA baseada em visão computacional.
* **OpenCV (opencv-python)**: Suporte para reconhecimento de imagem com alta precisão.
* **Psutil**: Gerenciamento de processos do sistema (limpeza de ambiente).

## 🚀 Como Executar
1. **Ambiente Virtual**: `python -m venv .venv`
2. **Ativação**: `.\.venv\Scripts\Activate.ps1`
3. **Dependências**: `pip install streamlit pandas pyautogui opencv-python psutil pygetwindow`
4. **Execução**: `streamlit run src/interface/app.py`

## 📁 Fluxo de Dados (Arquitetura Medalhão)
* **01_Bronze**: Dados brutos extraídos diretamente do CAD (formato CSV).
    * *Encoding*: `latin1` | *Separator*: `;`
* **02_Silver**: Dados unificados, limpos e tipados.
    * *Output*: `master_historic_silver.csv` | *Encoding*: `utf-8-sig`.
* **03_Gold**: Métricas prontas para consumo (KPIs de tempo de resposta e volumetria).

## 🤖 Módulos de Automação (RPA)
O bot utiliza um fluxo de decisão em cascata para garantir estabilidade:
1. **Ambiente**: Encerra processos do Excel para evitar travas de arquivos.
2. **Foco**: Localiza a janela do CAD e utiliza o *Alt-key precedence* para forçar o foco (bypass de Foreground Lock).
3. **Validação**: Verifica via visão computacional se o filtro de chamadas está corretamente em "PASSOS".
4. **Navegação**: Executa cliques sequenciais (passos 01 a 09) e inserção de texto para exportação de dados.

## 🏗️ Estrutura do Projeto

<details>
  <summary>Clique para expandir a árvore de diretórios</summary>

```text
cad-auto/
│
├── assets/
│   └── images/
│       └── cad_targets/     # Prints de referência (01_... a 09_...)
│
├── data/                    # Armazenamento local (Ignorado pelo Git)
│   ├── 01_bronze/           # Histórico bruto (2018-2026)
│       └── active/     
│       └── historical/     
│   ├── 02_silver/           # Base unificada
│   └── 03_gold/             # Agregações de indicadores
│
├── src/                     # Código-fonte (Padrão Inglês)
│   ├── bot/                 # cad_bot.py (RPA Sênior)
│   ├── processing/          # data_handler.py (Engenharia de Dados)
│   └── interface/           # app.py (Interface Streamlit)
│
├── requirements.txt         # Dependências do projeto
└── README.md                # Documentação
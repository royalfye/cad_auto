# Automação e Dashboard - Gestão de Chamadas (CBMMG)

Este projeto automatiza a extração de dados do sistema **CAD (Java)** e processa as informações para exibição em um dashboard interativo. O objetivo é agilizar a análise de ocorrências atendidas na área da **2ª CIA Passos**.

## 🛠️ Tecnologias Utilizadas
* **Python 3.12+**
* **Streamlit**: Interface do usuário e Hub de controle.
* **Pandas**: Motor de transformação de dados (ETL).
* **Pathlib**: Gerenciamento de caminhos de arquivos (Windows friendly).

## 🚀 Como Executar
1. Crie o ambiente virtual: `python -m venv .venv`
2. Ative o ambiente: `.\.venv\Scripts\Activate.ps1`
3. Instale as dependências: `pip install streamlit pandas`
4. Execute o dashboard: `streamlit run src/interface/app.py`
5. Botão "Iniciar Extração": apenas visual por enquanto, sem funcionalidade

## 📁 Fluxo de Dados (Medalhão)
* **01_Bronze**: Dados brutos extraídos do CAD. Organizados em subpastas por ano (ex: `2018/`, `2019/`). Codificação original: `latin1` com separador `;`.
* **02_Silver**: Dados unificados e limpos. Arquivo mestre `master_historic_silver.csv` gerado com codificação `utf-8-sig`.
* **03_Gold**: (Em desenvolvimento) Tabelas agregadas por tipo de ocorrência e tempo de resposta.

## 🏗️ Estrutura do Projeto

<details>
  <summary>Clique para expandir a árvore de diretórios</summary>

```text
cad-auto/
│
├── data/                  # Armazenamento local de dados
│   ├── 01_bronze/         # Histórico bruto (2018-2026)
│   ├── 02_silver/         # Base unificada e limpa
│   └── 03_gold/           # Métricas prontas para o Dashboard
│
├── src/                   # Código-fonte (Padrão Inglês)
│   ├── bot/               # Scripts de automação RPA
│   ├── processing/        # Lógica de negócio e limpeza (data_handler.py)
│   └── interface/         # Hub visual em Streamlit (app.py)
│
├── requirements.txt       # Dependências principais
└── README.md              # Documentação do projeto
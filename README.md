# Beach-chopp

# 🍺 Beach Chopp - Sistema de Gestão Cloud (AC1)

Sistema de gerenciamento de vendas e logística para a **Beach Chopp**, desenvolvido para a disciplina de Projeto de Software do curso de ADS (Impacta). O foco desta primeira entrega (AC1) é a integração das três camadas de desenvolvimento com persistência de dados em nuvem.

## 🚀 Funcionalidades (AC1)
- **Cadastro de Vendas:** Formulário intuitivo para registro de novos pedidos.
- **Persistência em Nuvem:** Integração via API com Google Sheets (Database-as-a-Service).
- **Dashboard de Performance:** Visualização em tempo real de KPIs de vendas e volume por tipo de produto.
- **Arquitetura Escalável:** Separação clara entre interface, lógica de negócio e camada de dados.

## 🏗️ Arquitetura do Projeto
O projeto segue o modelo de 3 camadas solicitado:

1.  **Front-end:** Desenvolvido em [Streamlit](https://streamlit.io/), proporcionando uma interface web responsiva e dinâmica.
2.  **Back-end:** Lógica de processamento em **Python**, utilizando **Pandas** para manipulação de dados e **GSheets Connection** para comunicação via API.
3.  **Banco de Dados (DB):** **Google Sheets API**, garantindo armazenamento seguro e acessível em nuvem.

## 🛠️ Tecnologias Utilizadas
- [Python 3.13+](https://www.python.org/)
- [Streamlit](https://streamlit.io/)
- [Pandas](https://pandas.pydata.org/)
- [Plotly Express](https://plotly.com/python/)
- [Streamlit GSheets Connection](https://github.com/streamlit/gsheets-connection)

## 📋 Pré-requisitos
Para rodar o projeto localmente, você precisará instalar as dependências listadas no arquivo `requirements.txt`:

```bash
pip install -r requirements.txt

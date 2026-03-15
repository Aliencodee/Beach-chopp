import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Beach Chopp - Sistema Cloud", layout="wide")

# --- CONEXÃO COM GOOGLE SHEETS ---
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/10PWbmWEY0caMjCBKdXkWTbYiQUH9qY5vjNnteOp2QCc/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        # ttl=0 garante dados frescos da nuvem
        df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
        
        if df.empty:
            return pd.DataFrame(columns=["Data Registro", "Cliente", "Tipo", "Qtd", "Entrega", "Status"])
        
        # 1. FORÇAMOS A DATA A SER TEXTO PARA NÃO APARECER 'NONE' NO SITE
        df['Data Registro'] = df['Data Registro'].astype(str)
        
        # 2. CRIAMOS UMA COLUNA TEMPORÁRIA SÓ PARA O GRÁFICO (Sem estragar a principal)
        df['Data_Grafico'] = pd.to_datetime(df['Data Registro'], dayfirst=True, errors='coerce')
        
        return df
    except:
        return pd.DataFrame(columns=["Data Registro", "Cliente", "Tipo", "Qtd", "Entrega", "Status"])

# Carregamento inicial
df_db = carregar_dados()

st.title("🍺 Beach Chopp - Gestão em Tempo Real (Cloud)")

# --- ABAS ---
tab_cadastro, tab_dashboard = st.tabs(["📝 Novo Cadastro", "📊 Dashboard de Performance"])

# ---------------------------------------------------------
# ABA 1: NOVO CADASTRO
# ---------------------------------------------------------
with tab_cadastro:
    st.subheader("Registrar Venda na Nuvem")
    
    with st.form("form_registro", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            cliente = st.text_input("Nome do Cliente")
        with col2:
            tipo = st.selectbox("Tipo de Chopp", ["Pilsen", "Vinho", "IPA", "Black"])
        with col3:
            qtd = st.number_input("Barris", min_value=1, step=1)
            
        data_ent = st.date_input("Data de Entrega", datetime.now())
        
        btn_salvar = st.form_submit_button("Salvar no Google Sheets")

        if btn_salvar:
            if cliente:
                # 1. Buscamos a versão real antes de salvar (Garante que não apague o histórico)
                df_atual_nuvem = carregar_dados()
                
                # 2. Removemos a coluna do gráfico para não salvar lixo na planilha
                if 'Data_Grafico' in df_atual_nuvem.columns:
                    df_atual_nuvem = df_atual_nuvem.drop(columns=['Data_Grafico'])
                
                # 3. Criamos o novo registro como texto puro
                novo_item = {
                    "Data Registro": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "Cliente": cliente,
                    "Tipo": tipo,
                    "Qtd": qtd,
                    "Entrega": data_ent.strftime("%d/%m/%Y"),
                    "Status": "Pendente"
                }
                
                # 4. Concatenamos e limpamos linhas vazias que o Sheets costuma gerar
                df_para_atualizar = pd.concat([df_atual_nuvem, pd.DataFrame([novo_item])], ignore_index=True)
                df_para_atualizar = df_para_atualizar.dropna(subset=['Cliente'])
                
                # 5. Enviamos a lista completa atualizada
                conn.update(spreadsheet=URL_PLANILHA, data=df_para_atualizar)
                
                st.success(f"Pedido de {cliente} enviado com sucesso!")
                st.rerun() 
            else:
                st.error("Por favor, informe o nome do cliente.")

    st.markdown("---")
    st.subheader("📋 Registros Sincronizados")
    # Exibimos apenas as colunas originais
    cols_exibicao = ["Data Registro", "Cliente", "Tipo", "Qtd", "Entrega", "Status"]
    st.dataframe(df_db[cols_exibicao].sort_index(ascending=False), use_container_width=True)

# ---------------------------------------------------------
# ABA 2: DASHBOARD
# ---------------------------------------------------------
with tab_dashboard:
    if df_db.empty:
        st.info("Aguardando dados da nuvem...")
    else:
        st.subheader("Filtros Rápidos")
        tipos_disponiveis = df_db["Tipo"].unique()
        selecionados = st.multiselect("Filtrar por Tipo", tipos_disponiveis, default=tipos_disponiveis)
        
        df_filtrado = df_db[df_db["Tipo"].isin(selecionados)]

        m1, m2, m3 = st.columns(3)
        m1.metric("Total de Barris", int(df_filtrado["Qtd"].sum()))
        m2.metric("Total de Pedidos", len(df_filtrado))
        m3.metric("Clientes Únicos", df_filtrado["Cliente"].nunique())

        c1, c2 = st.columns(2)
        with c1:
            fig_bar = px.bar(df_filtrado.groupby("Tipo")["Qtd"].sum().reset_index(), 
                             x="Tipo", y="Qtd", title="Volume por Tipo", template="plotly_dark")
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with c2:
            # Usamos a coluna Data_Grafico que foi tratada para ser uma data real
            fig_line = px.line(df_filtrado.sort_values("Data_Grafico"), 
                               x="Data_Grafico", y="Qtd", title="Vendas no Tempo", template="plotly_dark")
            st.plotly_chart(fig_line, use_container_width=True)
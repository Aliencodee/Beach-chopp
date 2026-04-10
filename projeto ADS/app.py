import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
from fpdf import FPDF
import io

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Beach Chopp - Sistema Cloud", layout="wide")

# --- AUTENTICAÇÃO DE USUÁRIO ---
USUARIOS = {
    "admin": "chopp123",
    "vendedor": "beach2024"
}

def login():
    st.title("🍺 Beach Chopp - Acesso Restrito")
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Login")
        usuario = st.text_input("Usuário", placeholder="Digite seu usuário")
        senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
        btn_login = st.button("Entrar", use_container_width=True)

        if btn_login:
            if usuario in USUARIOS and USUARIOS[usuario] == senha:
                st.session_state["autenticado"] = True
                st.session_state["usuario_logado"] = usuario
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    login()
    st.stop()

# --- CONEXÃO COM GOOGLE SHEETS ---
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/10PWbmWEY0caMjCBKdXkWTbYiQUH9qY5vjNnteOp2QCc/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
        if df.empty:
            return pd.DataFrame(columns=["Data Registro", "Cliente", "Tipo", "Qtd", "Entrega", "Status"])
        df['Data Registro'] = df['Data Registro'].astype(str)
        df['Data_Grafico'] = pd.to_datetime(df['Data Registro'], dayfirst=True, errors='coerce')
        return df
    except:
        return pd.DataFrame(columns=["Data Registro", "Cliente", "Tipo", "Qtd", "Entrega", "Status"])

# Carregamento inicial
df_db = carregar_dados()

# --- HEADER COM LOGOUT ---
col_titulo, col_usuario = st.columns([4, 1])
with col_titulo:
    st.title("🍺 Beach Chopp - Gestão em Tempo Real (Cloud)")
with col_usuario:
    st.markdown(f"<br>👤 **{st.session_state['usuario_logado']}**", unsafe_allow_html=True)
    if st.button("Sair", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = ""
        st.rerun()

# --- ABAS ---
tab_cadastro, tab_status, tab_dashboard = st.tabs([
    "📝 Novo Cadastro",
    "🔄 Gerenciar Status",
    "📊 Dashboard de Performance"
])

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
                df_atual_nuvem = carregar_dados()
                if 'Data_Grafico' in df_atual_nuvem.columns:
                    df_atual_nuvem = df_atual_nuvem.drop(columns=['Data_Grafico'])

                novo_item = {
                    "Data Registro": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "Cliente": cliente,
                    "Tipo": tipo,
                    "Qtd": qtd,
                    "Entrega": data_ent.strftime("%d/%m/%Y"),
                    "Status": "Pendente"
                }

                df_para_atualizar = pd.concat([df_atual_nuvem, pd.DataFrame([novo_item])], ignore_index=True)
                df_para_atualizar = df_para_atualizar.dropna(subset=['Cliente'])
                conn.update(spreadsheet=URL_PLANILHA, data=df_para_atualizar)
                st.success(f"Pedido de {cliente} enviado com sucesso!")
                st.rerun()
            else:
                st.error("Por favor, informe o nome do cliente.")

    st.markdown("---")
    st.subheader("📋 Registros Sincronizados")

    # --- FILTROS DE BUSCA ---
    with st.expander("🔍 Filtros de Busca", expanded=False):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filtro_cliente = st.text_input("Buscar por Cliente", placeholder="Nome do cliente...")
        with col_f2:
            filtro_data_inicio = st.date_input("Data Inicial", value=None, key="fi")
        with col_f3:
            filtro_data_fim = st.date_input("Data Final", value=None, key="ff")

    cols_exibicao = ["Data Registro", "Cliente", "Tipo", "Qtd", "Entrega", "Status"]
    df_exibicao = df_db[cols_exibicao].copy()

    # Aplica filtro de cliente
    if filtro_cliente:
        df_exibicao = df_exibicao[df_exibicao["Cliente"].str.contains(filtro_cliente, case=False, na=False)]

    # Aplica filtro de data (usando Data_Grafico do df_db)
    if filtro_data_inicio or filtro_data_fim:
        datas = df_db['Data_Grafico']
        mask = pd.Series([True] * len(df_db), index=df_db.index)
        if filtro_data_inicio:
            mask = mask & (datas >= pd.Timestamp(filtro_data_inicio))
        if filtro_data_fim:
            mask = mask & (datas <= pd.Timestamp(filtro_data_fim))
        df_exibicao = df_exibicao[mask]

    st.dataframe(df_exibicao.sort_index(ascending=False), use_container_width=True)

    # --- EXPORTAÇÃO PDF ---
    st.markdown("---")
    st.subheader("📄 Exportar Relatório")

    col_exp1, col_exp2 = st.columns([2, 1])
    with col_exp1:
        data_pdf = st.date_input("Exportar pedidos do dia", datetime.now(), key="data_pdf")
    with col_exp2:
        st.markdown("<br>", unsafe_allow_html=True)
        btn_pdf = st.button("📥 Gerar PDF do Dia", use_container_width=True)

    if btn_pdf:
        data_str = data_pdf.strftime("%d/%m/%Y")
        df_dia = df_db[df_db["Entrega"] == data_str][cols_exibicao]

        if df_dia.empty:
            st.warning(f"Nenhum pedido encontrado para {data_str}.")
        else:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, f"Beach Chopp - Pedidos do Dia {data_str}", ln=True, align="C")
            pdf.ln(5)

            pdf.set_font("Arial", "B", 10)
            headers = ["Data Reg.", "Cliente", "Tipo", "Qtd", "Entrega", "Status"]
            widths = [38, 40, 22, 15, 28, 27]
            for h, w in zip(headers, widths):
                pdf.cell(w, 8, h, border=1)
            pdf.ln()

            pdf.set_font("Arial", "", 9)
            for _, row in df_dia.iterrows():
                valores = [
                    str(row["Data Registro"])[:16],
                    str(row["Cliente"]),
                    str(row["Tipo"]),
                    str(row["Qtd"]),
                    str(row["Entrega"]),
                    str(row["Status"])
                ]
                for val, w in zip(valores, widths):
                    pdf.cell(w, 7, val[:18], border=1)
                pdf.ln()

            pdf.ln(5)
            pdf.set_font("Arial", "B", 10)
            pdf.cell(0, 8, f"Total de Barris: {int(df_dia['Qtd'].sum())}  |  Total de Pedidos: {len(df_dia)}", ln=True)

            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            st.download_button(
                label="⬇️ Baixar PDF",
                data=pdf_bytes,
                file_name=f"beachchopp_{data_pdf.strftime('%d%m%Y')}.pdf",
                mime="application/pdf"
            )

# ---------------------------------------------------------
# ABA 2: GERENCIAR STATUS
# ---------------------------------------------------------
with tab_status:
    st.subheader("🔄 Alterar Status dos Pedidos")
    st.markdown("Marque os pedidos como **Entregue** abaixo:")

    df_status = carregar_dados()
    cols_s = ["Data Registro", "Cliente", "Tipo", "Qtd", "Entrega", "Status"]

    pendentes = df_status[df_status["Status"] == "Pendente"].copy()

    if pendentes.empty:
        st.success("✅ Nenhum pedido pendente no momento!")
    else:
        st.markdown(f"**{len(pendentes)} pedido(s) pendente(s):**")
        indices_para_entregar = []

        for idx, row in pendentes.iterrows():
            col_check, col_info = st.columns([1, 6])
            with col_check:
                marcar = st.checkbox("", key=f"status_{idx}")
            with col_info:
                st.markdown(
                    f"**{row['Cliente']}** | {row['Tipo']} | {row['Qtd']} barril(s) | Entrega: {row['Entrega']}"
                )
            if marcar:
                indices_para_entregar.append(idx)

        if indices_para_entregar:
            if st.button(f"✅ Confirmar Entrega de {len(indices_para_entregar)} pedido(s)", type="primary"):
                df_atualizar = carregar_dados()
                if 'Data_Grafico' in df_atualizar.columns:
                    df_atualizar = df_atualizar.drop(columns=['Data_Grafico'])
                df_atualizar.loc[indices_para_entregar, "Status"] = "Entregue"
                df_atualizar = df_atualizar.dropna(subset=['Cliente'])
                conn.update(spreadsheet=URL_PLANILHA, data=df_atualizar)
                st.success("Status atualizado com sucesso!")
                st.rerun()

    st.markdown("---")
    st.subheader("📦 Todos os Pedidos")
    st.dataframe(df_status[cols_s].sort_index(ascending=False), use_container_width=True)

# ---------------------------------------------------------
# ABA 3: DASHBOARD
# ---------------------------------------------------------
with tab_dashboard:
    if df_db.empty:
        st.info("Aguardando dados da nuvem...")
    else:
        st.subheader("Filtros Rápidos")
        tipos_disponiveis = df_db["Tipo"].unique()
        selecionados = st.multiselect("Filtrar por Tipo", tipos_disponiveis, default=tipos_disponiveis)

        df_filtrado = df_db[df_db["Tipo"].isin(selecionados)]

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total de Barris", int(df_filtrado["Qtd"].sum()))
        m2.metric("Total de Pedidos", len(df_filtrado))
        m3.metric("Clientes Únicos", df_filtrado["Cliente"].nunique())
        pendentes_count = len(df_filtrado[df_filtrado["Status"] == "Pendente"])
        m4.metric("Pedidos Pendentes", pendentes_count)

        c1, c2 = st.columns(2)
        with c1:
            fig_bar = px.bar(
                df_filtrado.groupby("Tipo")["Qtd"].sum().reset_index(),
                x="Tipo", y="Qtd", title="Volume por Tipo", template="plotly_dark"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with c2:
            fig_line = px.line(
                df_filtrado.sort_values("Data_Grafico"),
                x="Data_Grafico", y="Qtd", title="Vendas no Tempo", template="plotly_dark"
            )
            st.plotly_chart(fig_line, use_container_width=True)

        c3, c4 = st.columns(2)
        with c3:
            status_count = df_filtrado["Status"].value_counts().reset_index()
            status_count.columns = ["Status", "Quantidade"]
            fig_status = px.pie(
                status_count, values="Quantidade", names="Status",
                title="Pedidos por Status", template="plotly_dark",
                color_discrete_map={"Pendente": "#f59e0b", "Entregue": "#10b981"}
            )
            st.plotly_chart(fig_status, use_container_width=True)

        with c4:
            top_clientes = df_filtrado.groupby("Cliente")["Qtd"].sum().nlargest(10).reset_index()
            fig_clientes = px.bar(
                top_clientes, x="Qtd", y="Cliente", orientation="h",
                title="Top 10 Clientes", template="plotly_dark"
            )
            st.plotly_chart(fig_clientes, use_container_width=True)

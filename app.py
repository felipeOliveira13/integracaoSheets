import streamlit as st
import gspread
import pandas as pd
import altair as alt

# --- VARIÁVEIS DE CONFIGURAÇÃO ---
SHEET_ID = "1fa4HLFfjIFKHjHBuxW_ymHkahVPzeoB_XlHNJMaNCg8"
SHEET_NAME = "Chevrolet Preços"

# --- FUNÇÕES DE CARREGAMENTO DE DADOS ---

@st.cache_data(ttl=600)
def load_data_from_sheet():
    """Carrega os dados da planilha do Google Sheets."""
    try:
        # Puxa as credenciais do Google Sheets do secrets.toml
        credentials = st.secrets["gcp_service_account"]
        gc = gspread.service_account_from_dict(credentials)
        
        # Abre a planilha e a aba específica
        spreadsheet = gc.open_by_key(SHEET_ID)
        worksheet = spreadsheet.worksheet(SHEET_NAME)
        
        # Converte os registros em um DataFrame Pandas
        df = pd.DataFrame(worksheet.get_all_records())
        
        # Limpeza e conversão de dados: Ano
        df['Ano'] = pd.to_numeric(df['Ano'], errors='coerce').fillna(0).astype(int)
        
        # Limpeza e conversão de dados: Preço (para gráficos e cálculos)
        df['Preço Numérico'] = pd.to_numeric(
            df['Preço (R$)'].astype(str).str.replace(r'[R$.,]', '', regex=True), 
            errors='coerce'
        )
        
        return df
    
    except KeyError:
        st.error("❌ Erro de Configuração: O segredo 'gcp_service_account' não foi encontrado no secrets.toml.")
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"❌ Erro ao acessar o Google Sheets: {e}")
        st.warning("Verifique se o email de serviço foi adicionado como 'Leitor' na planilha.")
        return pd.DataFrame()

# --- LAYOUT PRINCIPAL DO APLICATIVO ---

def main_app():
    st.set_page_config(layout="wide", page_title="Tabela de Preços Chevrolet")
    st.title("🚗 Tabela de Preços Chevrolet (Dados do Google Sheets)")
    
    st.caption("Dados carregados diretamente da planilha, sem autenticação.")

    # Carrega os dados (função protegida por cache)
    df = load_data_from_sheet()

    if not df.empty:
        st.subheader(f"Dados da Aba: {SHEET_NAME} (Total de linhas: {len(df)})")
        
        # --- FILTROS DE DADOS ---
        st.markdown("### Filtros de Dados")
        col_model, col_year = st.columns(2)

        with col_model:
            selected_models = st.multiselect(
                "Selecione o(s) Modelo(s) de Carro:",
                options=df['Modelo'].unique(),
                default=df['Modelo'].unique()
            )
        
        with col_year:
            selected_years = st.multiselect(
                "Selecione o(s) Ano(s) de Fabricação:",
                options=df['Ano'].unique(),
                default=df['Ano'].unique()
            )
        
        # Aplica o filtro
        df_filtered = df[
            (df['Modelo'].isin(selected_models)) &
            (df['Ano'].isin(selected_years))
        ]

        if df_filtered.empty:
            st.warning("O filtro retornou zero resultados. Ajuste a seleção.")
        else:
            # --- TABELA DE DADOS ---
            st.dataframe(df_filtered[['Modelo', 'Ano', 'Preço (R$)']])
            
            # --- GRÁFICO ---
            st.subheader("Gráfico de Preços por Ano")
            
            # Agrupa por ano e calcula a média do preço
            df_plot = df_filtered.groupby('Ano')['Preço Numérico'].mean().reset_index()
            df_plot.columns = ['Ano', 'Preço Médio (R$)']

            # Cria o gráfico Altair
            chart = alt.Chart(df_plot).mark_line(point=True).encode(
                x=alt.X('Ano:O', title='Ano de Fabricação'), # 'O' for Ordinal
                y=alt.Y('Preço Médio (R$)', title='Preço Médio (R$)', axis=alt.Axis(format='$,.0f')),
                tooltip=['Ano', alt.Tooltip('Preço Médio (R$)', format='$,.0f')]
            ).properties(
                title='Preço Médio dos Carros Selecionados por Ano'
            ).interactive() # Permite zoom e pan

            st.altair_chart(chart, use_container_width=True)

    # Botão de recarga para forçar a busca de novos dados
    st.button("Recarregar Dados", on_click=load_data_from_sheet.clear)

if __name__ == "__main__":
    main_app()
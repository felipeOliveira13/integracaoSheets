import streamlit as st
import gspread
import pandas as pd

# --- CONSTANTES GERAIS ---
ROW_HEIGHT = 35 
HEADER_HEIGHT = 35


# 1. FUNÇÃO DE INJEÇÃO DE CSS (NOVO TEMA NEUTRO)
def inject_custom_css():
    st.markdown(
        """
        <style>
        /* 1. TEMA NEUTRO: Fundo da Página (Light Gray) e Cor do Texto */
        .stApp {
            background-color: #F0F2F6; /* Cinza Claro (Padrão Streamlit Light) */
            color: #333333; /* Cor do texto principal */
        }
        
        /* 2. Título Principal (Cor Sóbria e Centralizada) */
        h1 {
            text-align: center;
            color: #2E4053; /* Azul Marinho Profundo para forte contraste */
        }
        
        /* 3. Subtítulos (Headers) e Outros Textos */
        h2, h3 {
            color: #333333;
        }

        /* 4. Centraliza e define cor do texto secundário (caption) */
        div[data-testid="stCaptionContainer"] {
            text-align: center;
            color: #555555; 
        }

        /* 5. Garante que o texto do botão não quebre (mantido) */
        div.stButton > button:first-child {
            white-space: nowrap; 
        }

        /* 6. Outros ajustes de padding */
        .block-container {
            padding-top: 2rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
inject_custom_css()
# --- FIM DO CSS ---


# --- DADOS DA PLANILHA ---
SHEET_ID = "1fa4HLFfjIFKHjHBuxW_ymHkahVPzeoB_XlHNJMaNCg8"
SHEET_NAME = "Chevrolet Preços"

st.title("🚗 Tabela de Preços Chevrolet (Google Sheets)")
st.caption("Dados carregados diretamente do Google Sheets usando st.secrets.")


# Função de carregamento com cache (mantida sem alteração)
@st.cache_data(ttl=600)  
def load_data_from_sheet():
    try:
        credentials = st.secrets["gcp_service_account"]
        gc = gspread.service_account_from_dict(credentials)
        spreadsheet = gc.open_by_key(SHEET_ID)
        worksheet = spreadsheet.worksheet(SHEET_NAME)
        df = pd.DataFrame(worksheet.get_all_records())
        df['Ano'] = pd.to_numeric(df['Ano'], errors='coerce').fillna(0).astype(int)
        return df
    
    except KeyError:
        st.error("❌ Erro de Configuração: O segredo 'gcp_service_account' não foi encontrado.")
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"❌ Erro ao acessar o Google Sheets: {e}")
        st.warning("Verifique se o email de serviço foi adicionado como 'Leitor' na planilha.")
        return pd.DataFrame()


# --- EXECUÇÃO DO APLICATIVO ---
df = load_data_from_sheet()

if not df.empty:
    
    # =============================================================
    # SEÇÃO DE FILTROS INTERATIVOS
    # =============================================================
    st.markdown("---")
    st.subheader("Filtros de Dados")
    
    filter_col1, filter_col2 = st.columns(2)
    
    with filter_col1:
        all_models = sorted(df['Modelo'].unique())
        selected_models = st.multiselect(
            "Selecione o(s) Modelo(s) de Carro:",
            options=all_models,
            default=all_models
        )

    with filter_col2:
        all_years = sorted(df['Ano'].unique())
        selected_years = st.multiselect(
            "Selecione o(s) Ano(s) de Fabricação:",
            options=all_years,
            default=all_years
        )

    df_filtered = df[
        (df['Modelo'].isin(selected_models)) &
        (df['Ano'].isin(selected_years))
    ]
    
    
    # =============================================================
    # SEÇÃO DE MÉTRICAS (KPIs)
    # =============================================================
    if not df_filtered.empty:
        total_carros = len(df_filtered)
        # O .mean() e .max() exigem que a coluna de preço seja numérica (float/int)
        try:
            prices = pd.to_numeric(df_filtered['Preço (R$)'].astype(str).str.replace(r'[R$.,]', '', regex=True), errors='coerce')
            preco_medio = prices.mean()
            preco_max = prices.max()
        except Exception:
             preco_medio = 0
             preco_max = 0
             
        
        st.markdown("## Resumo das Métricas")
        
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        
        with metric_col1:
            st.metric(
                label="🚗 Total de Carros Filtrados", 
                value=f"{total_carros} Unidades"
            )
            
        with metric_col2:
            st.metric(
                label="💰 Preço Médio (R$)", 
                value=f"R$ {preco_medio:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".") if preco_medio > 0 else "N/A" # Formato BRL
            )
            
        with metric_col3:
            st.metric(
                label="🔝 Preço Máximo (R$)", 
                value=f"R$ {preco_max:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".") if preco_max > 0 else "N/A" # Formato BRL
            )
            
        st.markdown("---") 
    
    # =============================================================
    # EXIBIÇÃO DA TABELA (DATAFRAME)
    # =============================================================

    st.subheader(f"Dados da Aba: {SHEET_NAME} (Linhas exibidas: {len(df_filtered)})")
    
    calculated_height = (len(df_filtered) * ROW_HEIGHT) + HEADER_HEIGHT

    st.dataframe(df_filtered, 
                 use_container_width=True, 
                 hide_index=True, 
                 height=calculated_height) 
    
    # Botão de Recarregar
    st.markdown("---") 
    col_left, col_center, col_right = st.columns([3, 4, 3])
    
    with col_center:
        if st.button(
            "🔄 Recarregar Dados", 
            help="Clique para buscar a versão mais recente dos dados da planilha."
        ):
            load_data_from_sheet.clear()
            st.rerun() 
            
else:
    st.warning("Não foi possível carregar os dados ou o filtro retornou zero resultados.")
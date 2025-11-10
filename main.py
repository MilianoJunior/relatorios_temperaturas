# importar bibliotecas
import streamlit as st

# Configuração da página DEVE ser a primeira chamada do Streamlit
ug = 'UG-01'
usina = 'CGH-FAE'

st.set_page_config(page_title=f'Relatório de Temperaturas {usina}', page_icon=':thermometer:', layout='centered')

# Imports que usam Streamlit devem vir DEPOIS do set_page_config
import plotly.express as px
from libs.styles import styles
import plotly.graph_objects as go
from datetime import datetime
import time
import pandas as pd
import os
import glob
from libs.temperaturas import relatorio_temperaturas
from libs.rendimento import relatorio_rendimento
from libs.configs import leituras

# Aplicar estilos CSS
st.markdown(styles, unsafe_allow_html=True)

def registrar_atualizacao(usina, ug, periodo, num_registros, arquivo_csv):
    """Registra a última atualização em um arquivo JSON"""
    import json
    arquivo_registro = 'assets/historico_atualizacoes.json'
    
    # Criar diretório se não existir
    if not os.path.exists('assets'):
        os.makedirs('assets')
    
    # Ler registros existentes
    if os.path.exists(arquivo_registro):
        with open(arquivo_registro, 'r', encoding='utf-8') as f:
            historico = json.load(f)
    else:
        historico = []
    
    # Adicionar novo registro
    novo_registro = {
        'usina': usina,
        'ug': ug,
        'periodo': periodo,
        'data_atualizacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'num_registros': num_registros,
        'arquivo_csv': arquivo_csv
    }
    
    historico.insert(0, novo_registro)  # Adiciona no início da lista
    
    # Manter apenas os últimos 50 registros
    historico = historico[:50]
    
    # Salvar arquivo
    with open(arquivo_registro, 'w', encoding='utf-8') as f:
        json.dump(historico, f, indent=2, ensure_ascii=False)

def obter_historico_atualizacoes():
    """Retorna o histórico de atualizações"""
    import json
    arquivo_registro = 'assets/historico_atualizacoes.json'
    
    if os.path.exists(arquivo_registro):
        with open(arquivo_registro, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def encontrar_csv_mais_recente(usina, ug):
    """Tenta encontrar o arquivo CSV mais recente para uma usina/ug"""
    # Mapear nome da usina para o padrão do diretório
    mapeamento_diretorios = {
        'CGH-HOPPEN': 'hoppen',
        'CGH-FAE': 'fae',
        'CGH-APARECIDA': 'aparecida',
        'CGH-PICADAS_ALTAS': 'picadas_altas',
        'PCH-PEDRAS': 'pedras'
    }
    
    # Mapear UG para o padrão do arquivo
    ug_num = ug.lower().replace('-', '')  # UG-01 -> ug01
    
    diretorio = mapeamento_diretorios.get(usina)
    if not diretorio:
        return None
    
    # Buscar arquivos CSV no padrório
    padrao = f'assets/{diretorio}/*_{ug_num}_*.csv'
    arquivos = glob.glob(padrao)
    
    if arquivos:
        # Retornar o arquivo mais recente
        arquivos.sort(reverse=True)
        return arquivos[0]
    
    return None

def carregar_dados_do_csv(arquivo_csv):
    """Carrega dados diretamente de um arquivo CSV existente"""
    if os.path.exists(arquivo_csv):
        df = pd.read_csv(arquivo_csv)
        print(f'CSV carregado do histórico: {arquivo_csv}', len(df))
        # Processar DataFrame
        if 'id' in df.columns:
            df = df.drop(columns=['id'])
        df['data_hora'] = pd.to_datetime(df['data_hora'])
        return df
    else:
        st.error(f"Arquivo CSV não encontrado: {arquivo_csv}")
        return None

def carregar_dados(usina, ug, periodo_dias=None):
    # Incluir hora e minuto no nome do arquivo
    data_hora_atual = datetime.now().strftime('%Y-%m-%d_%H-%M')
    data_atual = datetime.now().strftime('%Y-%m-%d')
    
    # Calcular data inicial baseada no período
    if periodo_dias is None:
        # Todo o período
        condicao_data = ""
    else:
        data_inicial = (datetime.now() - pd.Timedelta(days=periodo_dias)).strftime('%Y-%m-%d')
        condicao_data = f" AND data_hora >= '{data_inicial}'"
    
    # colunas = ['data_hora']
    usinas = {
        'CGH-HOPPEN':{
            'UG-01': {'csv': f'assets/hoppen/hoppen_ug01_{data_hora_atual}.csv', 'nome': 'UG-01','mysql': f'select * from cgh_hoppen_ug01 where data_hora <= "{data_atual}"{condicao_data}'},
            'UG-02': {'csv': f'assets/hoppen/hoppen_ug02_{data_hora_atual}.csv', 'nome': 'UG-02','mysql': f'select * from cgh_hoppen_ug02 where data_hora <= "{data_atual}"{condicao_data}'},
        },
        'CGH-FAE':{
            'UG-01': {'csv': f'assets/fae/fae_ug01_{data_hora_atual}.csv', 'nome': 'UG-01','mysql': f'select * from cgh_fae where data_hora <= "{data_atual}"{condicao_data}'},
            'UG-02': {'csv': f'assets/fae/fae_ug02_{data_hora_atual}.csv', 'nome': 'UG-02','mysql': f'select * from cgh_fae where data_hora <= "{data_atual}"{condicao_data}'},
        },
        'CGH-APARECIDA':{
            'UG-01': {'csv': f'assets/aparecida/aparecida_ug01_{data_hora_atual}.csv', 'nome': 'UG-01','mysql': f'select * from cgh_aparecida where data_hora <= "{data_atual}"{condicao_data}'},
        },
        'CGH-PICADAS-ALTAS':{
            'UG-01': {'csv': f'assets/picadas_altas/picadas_altas_ug01_{data_hora_atual}.csv', 'nome': 'UG-01','mysql': f'select * from cgh_picadas_altas where data_hora <= "{data_atual}"{condicao_data}'},
            'UG-02': {'csv': f'assets/picadas_altas/picadas_altas_ug02_{data_hora_atual}.csv', 'nome': 'UG-02','mysql': f'select * from cgh_picadas_altas where data_hora <= "{data_atual}"{condicao_data}'},
        },
        'PCH-PEDRAS':{
            'UG-01': {'csv': f'assets/pedras/pedras_ug01_{data_hora_atual}.csv', 'nome': 'UG-01','mysql': f'select * from pch_pedras_ug01 where data_hora <= "{data_atual}"{condicao_data}'},
            'UG-02': {'csv': f'assets/pedras/pedras_ug02_{data_hora_atual}.csv', 'nome': 'UG-02','mysql': f'select * from pch_pedras_ug02 where data_hora <= "{data_atual}"{condicao_data}'},
        },
    }
    def verificar_csv(csv):
        if os.path.exists(csv):
            return True
        return False

    def salvar_csv(df, usina):
        name_csv = usinas[usina][ug]['csv']
        print(f'Quantidade de dados: {len(df)}')
        DF = 5
        # DS = 3  # experimente 2, 3 ou 5
        df = df.iloc[::DF].copy()
        print(f'Depois de reduzir a quantidade de dados: {len(df)}')
        
        # Criar diretório se não existir
        csv_dir = os.path.dirname(name_csv)
        if not os.path.exists(csv_dir):
            os.makedirs(csv_dir)
        
        df.to_csv(name_csv, index=False)

    def consultar_mysql(usina):
        csv_path = usinas[usina][ug]['csv']
        
        if verificar_csv(csv_path):
            df = pd.read_csv(csv_path)
            print('Arquivo CSV encontrado', len(df))
            df = df.dropna()
            # remover a coluna 'id'
            df = df.drop(columns=['id'])

            # converter a coluna 'data_hora' para datetime
            df['data_hora'] = pd.to_datetime(df['data_hora'])
            return df, csv_path
        try:
            from libs.db import Database
            db = Database()
            print(usinas[usina][ug]['mysql'])
            print('Consultando MySQL')
            # Usar fetch_data em vez de execute_query para consultas SELECT
            data = db.fetch_data(usinas[usina][ug]['mysql'])
            df = pd.DataFrame(data)
            salvar_csv(df, usina)
            
            # Processar DataFrame após consulta MySQL
            df = df.dropna()
            df = df.drop(columns=['id'])
            df['data_hora'] = pd.to_datetime(df['data_hora'])
            return df, csv_path
        finally:
            db.close()

    return consultar_mysql(usina)


def renomear_colunas_picadas_altas(df):
    names_temp = {
        "ug01_p_ativa":"ug01 Potência Ativa",
        "ug01_temp_oleo_uhlm":"ug01 Óleo Reservatório - U.H.L.M*",
        "ug01_temp_1":"ug01 enrolamento fase A",
        "ug01_temp_2":"ug01 enrolamento fase B",
        "ug01_temp_3":"ug01 enrolamento fase C",
        "ug01_temp_4":"ug01 nucleo do estator",
        "ug01_temp_5":"ug01 CS-U1",
        "ug01_temp_6":"ug01 Mancal Combinado Radial L.A",
        "ug01_temp_7":"ug01 Mancal Combinado Escora L.A",
        "ug01_temp_8":"ug01 Mancal Combinado Contra Escora L.A",
        "ug01_temp_9":"ug01 Mancal Guia L.N.A.",
        "ug02_p_ativa":"ug02 Potência Ativa",
        "ug02_temp_oleo_uhlm":"ug02 Óleo Reservatório - U.H.L.M*",
        "ug02_temp_1":"ug02 enrolamento fase A",
        "ug02_temp_2":"ug02 enrolamento fase B",
        "ug02_temp_3":"ug02 enrolamento fase C",
        "ug02_temp_4":"ug02 nucleo do estator",
        "ug02_temp_5":"ug02 CS-U1",
        "ug02_temp_6":"ug02 Mancal Combinado Radial L.A",
        "ug02_temp_7":"ug02 Mancal Combinado Escora L.A",
        "ug02_temp_8":"ug02 Mancal Combinado Contra Escora L.A",
        "ug02_temp_9":"ug02 Mancal Guia L.N.A.",
        "temp_ambiente":"Temperatura Ambiente",
    }
    df = df.rename(columns=names_temp)
    colunas_disponiveis = [col for col in df.columns if col not in ['id', 'data_hora']]
    return df, colunas_disponiveis


# Chamar a função principal
if __name__ == "__main__":
    usinas = ['CGH-HOPPEN', 'CGH-FAE', 'CGH-APARECIDA', 'CGH-PICADAS-ALTAS', 'PCH-PEDRAS']
    
    # Inicializar session_state
    if 'registro_selecionado_idx' not in st.session_state:
        st.session_state.registro_selecionado_idx = None
    if 'colunas_selecionadas' not in st.session_state:
        st.session_state.colunas_selecionadas = []
    
    # === CARD 1: Seleção de usina e atualização de dados ===
    st.markdown("### 🏭 Atualização de Dados")
    with st.container():
        cols = st.columns(3)
        
        with cols[0]:
            usina_selecionada = st.selectbox('Selecione a Usina', usinas)
        
        with cols[1]:
            unidade_geradora = st.selectbox('Selecione a Unidade Geradora', ['UG-01', 'UG-02'])
        
        with cols[2]:
            selecione_periodo = st.selectbox('Selecione o Período', 
                                            ['Últimos 7 dias', 'Últimos 30 dias', 'Últimos 90 dias', 
                                             'Últimos 180 dias', 'Último ano', 'Todo o período'])
        
        btn_atualizar = st.button('🔄 Atualizar Dados', use_container_width=True)
        
        if btn_atualizar:
            # Mapear seleção do período para número de dias
            periodos = {
                'Últimos 7 dias': 7,
                'Últimos 30 dias': 30,
                'Últimos 90 dias': 90,
                'Últimos 180 dias': 180,
                'Último ano': 365,
                'Todo o período': None
            }
            
            periodo_dias = periodos[selecione_periodo]
            
            # Carregar dados da usina selecionada
            with st.spinner('Carregando dados...'):
                df, csv_path = carregar_dados(usina_selecionada, unidade_geradora, periodo_dias)
            
            # Registrar atualização com o caminho do CSV
            registrar_atualizacao(usina_selecionada, unidade_geradora, selecione_periodo, len(df), csv_path)
            
            st.success(f'✅ Dados carregados com sucesso! Total de {len(df):,} registros.')
            st.info(f'📁 Arquivo salvo: {csv_path}')
            st.rerun()
    
    st.markdown("---")
    
    # === CARD 2: Histórico de atualizações com seleção única ===
    st.markdown("### 📋 Histórico de Atualizações")
    
    # Obter histórico
    historico = obter_historico_atualizacoes()
    
    if historico:
        # Criar DataFrame para exibição
        df_historico = pd.DataFrame(historico)
        
        # Formatar para exibição
        st.markdown("**Selecione um registro para gerar o relatório:**")
        
        # Usar radio button para seleção única
        opcoes = []
        for idx, row in df_historico.head(10).iterrows():
            opcao = f"**{row['usina']}** - {row['ug']} | {row['periodo']} | {row['data_atualizacao']} | {row['num_registros']:,} registros"
            opcoes.append(opcao)
        
        if opcoes:
            registro_selecionado_idx = st.radio(
                "Registros disponíveis:",
                range(len(opcoes)),
                format_func=lambda x: opcoes[x],
                key='radio_registros'
            )
            
            # Atualizar session_state com o índice selecionado
            st.session_state.registro_selecionado_idx = registro_selecionado_idx
            
            # Obter o registro selecionado
            registro_selecionado = df_historico.iloc[registro_selecionado_idx]
            
            st.markdown("---")
            
            # === CARD 3: Seleção de colunas ===
            st.markdown("### 📊 Seleção de Colunas para o Relatório")
            
            # Verificar se o registro tem o campo arquivo_csv válido
            # Checar se existe, não é None, não é string vazia e não é NaN (float)
            arquivo_csv_valido = (
                'arquivo_csv' in registro_selecionado and 
                pd.notna(registro_selecionado['arquivo_csv']) and 
                registro_selecionado['arquivo_csv'] and
                isinstance(registro_selecionado['arquivo_csv'], str)
            )
            
            # Se não tiver arquivo_csv válido, tentar encontrar automaticamente
            arquivo_csv = None
            if arquivo_csv_valido:
                arquivo_csv = registro_selecionado['arquivo_csv']
            else:
                # Tentar encontrar CSV automaticamente
                arquivo_csv = encontrar_csv_mais_recente(registro_selecionado['usina'], registro_selecionado['ug'])
                if arquivo_csv:
                    st.info(f"📂 Arquivo CSV encontrado automaticamente: {os.path.basename(arquivo_csv)}")
            
            if not arquivo_csv:
                st.warning("⚠️ Nenhum arquivo CSV encontrado para este registro. Por favor, faça uma nova atualização dos dados.")
            else:
                
                if os.path.exists(arquivo_csv):
                    df_temp = pd.read_csv(arquivo_csv, nrows=1)
                    colunas_disponiveis = [col for col in df_temp.columns if col not in ['id', 'data_hora']]

                    st.write(registro_selecionado['usina'])

                    if 'CGH-PICADAS-ALTAS' in registro_selecionado['usina']:
                        df_temp, colunas_disponiveis = renomear_colunas_picadas_altas(df_temp)

                    
                    
                    # Filtrar colunas de temperatura por padrão
                    colunas_temp_default = [col for col in colunas_disponiveis 
                                           if any(palavra in col.lower() for palavra in ['temp', 'enrol', 'nucleo', 'mancal'])]

                    potencia_name = [col for col in df_temp.columns if 'ativa' in col.lower()]
                    
                    st.markdown(f"**Usina:** {registro_selecionado['usina']} | **UG:** {registro_selecionado['ug']}")
                    st.markdown(f"**Total de colunas disponíveis:** {len(colunas_disponiveis)}")
                    
                    # Multiselect para escolher colunas
                    colunas_selecionadas = st.multiselect(
                        "Selecione as colunas que deseja incluir no relatório:",
                        options=colunas_disponiveis,
                        default=colunas_temp_default if colunas_temp_default else colunas_disponiveis[:10],
                        key='multiselect_colunas'
                    )

                    # Selecionar a potência ativa
                    potencia_ativa = st.selectbox('Selecione a potência ativa', potencia_name)
                    
                    # Atualizar session_state
                    st.session_state.colunas_selecionadas = colunas_selecionadas
                    
                    if colunas_selecionadas:
                        st.info(f"✅ {len(colunas_selecionadas)} colunas selecionadas")
                    else:
                        st.warning("⚠️ Selecione pelo menos uma coluna para gerar o relatório")
                else:
                    st.error(f"❌ Arquivo CSV não encontrado: {arquivo_csv}")
            
            st.markdown("---")
            st.markdown("### 📄 Geração de Relatório")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                btn_gerar = st.button('📊 Gerar Relatório', 
                                     use_container_width=True,
                                     disabled=(len(st.session_state.colunas_selecionadas) == 0),
                                     key='btn_gerar_relatorio')
            
            if btn_gerar:
                # Buscar arquivo CSV (do registro ou tentando encontrar automaticamente)
                arquivo_csv_valido_btn = (
                    'arquivo_csv' in registro_selecionado and 
                    pd.notna(registro_selecionado['arquivo_csv']) and 
                    registro_selecionado['arquivo_csv'] and
                    isinstance(registro_selecionado['arquivo_csv'], str)
                )
                
                arquivo_csv_btn = None
                if arquivo_csv_valido_btn:
                    arquivo_csv_btn = registro_selecionado['arquivo_csv']
                else:
                    arquivo_csv_btn = encontrar_csv_mais_recente(registro_selecionado['usina'], registro_selecionado['ug'])
                
                if len(st.session_state.colunas_selecionadas) == 0:
                    st.error("❌ Selecione pelo menos uma coluna para gerar o relatório")
                elif not arquivo_csv_btn:
                    st.error("❌ Nenhum arquivo CSV encontrado. Faça uma nova atualização dos dados.")
                else:
                    with st.spinner('📂 Carregando dados do arquivo...'):
                        df = carregar_dados_do_csv(arquivo_csv_btn)

                    if 'CGH-PICADAS-ALTAS' in registro_selecionado['usina']:
                        df, colunas_disponiveis = renomear_colunas_picadas_altas(df)

                    if df is not None:
                        st.success(f"✅ Dados carregados! Total de {len(df):,} registros")
                        colunas_para_relatorio = ['data_hora'] + st.session_state.colunas_selecionadas
                        df_filtrado = df[colunas_para_relatorio + [potencia_ativa]]
                        
                        # Gerar relatório
                        with st.spinner('📊 Gerando relatório...'):
                            st.markdown("---")
                            st.markdown("## 📈 Relatório Gerado")
                            st.markdown(f"**Usina:** {registro_selecionado['usina']} | **UG:** {registro_selecionado['ug']}")
                            st.markdown(f"**Período:** {registro_selecionado['periodo']} | **Colunas:** {len(st.session_state.colunas_selecionadas)}")
                            st.markdown("""<div style="page-break-after: always;"></div>""", unsafe_allow_html=True)
                            relatorio_temperaturas(registro_selecionado['usina'], registro_selecionado['ug'], df_filtrado, potencia_ativa)
                            
                    else:
                        st.error("❌ Erro ao carregar dados do histórico")
    else:
        st.info("ℹ️ Nenhuma atualização registrada ainda. Use o formulário acima para atualizar os dados.")


# importar bibliotecas
import streamlit as st
import plotly.express as px
from libs.styles import styles
import plotly.graph_objects as go
from datetime import datetime
import time
import pandas as pd
import os
import re
from difflib import get_close_matches
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from libs.trips import valores


def obter_setpoints_temperaturas(usina, ug):
    usina_ = usina.replace('-',' ').upper()
    print(usina_)
    valores_usina = valores.get(usina_, {})
    # print(valores_usina)
    valores_ug = valores_usina.get(ug, {})
    print(valores_ug)
    return valores_ug

def mapear_nome_coluna_para_sensor(nome_coluna, variaveis_disponiveis):
    """
    Mapeia o nome da coluna do banco de dados para o nome do sensor físico.
    
    Args:
        nome_coluna: Nome da coluna do banco (ex: 'ug01_enrol_faseA', 'ug01_temp_oleo_UHRV')
        variaveis_disponiveis: Dicionário com os nomes dos sensores disponíveis
        
    Returns:
        Nome do sensor físico ou None se não encontrar
    """
    # Remover prefixos comuns (ug01_, ug02_, temp_, etc)
    nome_limpo = re.sub(r'^(ug\d{2}_|temp_)', '', nome_coluna, flags=re.IGNORECASE)
    
    # Dicionário de padrões específicos (ordem importa - mais específicos primeiro!)
    padroes = {
        # Enrolamentos e Fases - mais específicos primeiro
        r'enrol[_\s]*fase[_\s]*a': ['Enrolamento Fase A', 'Fase A'],
        r'enrol[_\s]*fase[_\s]*b': ['Enrolamento Fase B', 'Fase B'],
        r'enrol[_\s]*fase[_\s]*c': ['Enrolamento Fase C', 'Fase C'],
        r'enrol[_\s]*[_\s]*a\b': ['Enrolamento Fase A', 'Fase A'],  # enrol_A
        r'enrol[_\s]*[_\s]*b\b': ['Enrolamento Fase B', 'Fase B'],  # enrol_B
        r'enrol[_\s]*[_\s]*c\b': ['Enrolamento Fase C', 'Fase C'],  # enrol_C
        
        # Óleos - todas as variações possíveis
        r'(oleo[_\s]*uhrv|uhrv[_\s]*(temp[_\s]*)?oleo|temp[_\s]*oleo[_\s]*uhrv)': 'Óleo U.H.R.V.',
        r'(oleo[_\s]*uhlm|uhlm[_\s]*(temp[_\s]*)?oleo|temp[_\s]*oleo[_\s]*uhlm)': 'Óleo U.H.L.M.',
        
        # Núcleo Estator - variações
        r'nucleo[_\s]*estator[_\s]*0?1': ['Núcleo Estator 1', 'Núcleo Estator'],
        r'nucleo[_\s]*estator[_\s]*0?2': ['Núcleo Estator 2', 'Núcleo Estator'],
        r'nucleo[_\s]*estator[_\s]*0?3': ['Núcleo Estator 3', 'Núcleo Estator'],
        r'nucleo[_\s]*estator': 'Núcleo Estator',
        
        # Mancais APARECIDA - padrões muito específicos primeiro
        r'manc[_\s]*(al)?[_\s]*casq[_\s]*comb': 'Mancal Comb. Casq.',
        r'manc[_\s]*(al)?[_\s]*casq[_\s]*(esc|escora)': 'Mancal Comb. Esc.',
        r'manc[_\s]*(al)?[_\s]*(cont|contra)[_\s]*(esc|escora)': 'Mancal Comb. Contra Esc.',
        r'manc[_\s]*(al)?[_\s]*casq[_\s]*guia': 'Mancal Guia Casq. Turb.',
        r'casq[_\s]*rad[_\s]*comb': 'Mancal Radial Guia',
        
        # Mancais genéricos - L.N.A. e L.A. devem vir ANTES dos genéricos
        r'manc[_\s]*(al)?[_\s]*lna[_\s]*guia': 'Mancal L.N.A. Guia',
        r'manc[_\s]*(al)?[_\s]*la[_\s]*guia': 'Mancal L.A. Guia',
        r'manc[_\s]*(al)?[_\s]*lna[_\s]*(esc|escora)': 'Mancal L.N.A. Escora',
        r'manc[_\s]*(al)?[_\s]*la[_\s]*(esc|escora)': 'Mancal L.A. Escora',
        r'mancal[_\s]*guia': 'Mancal Guia',
        r'mancal[_\s]*combinado': 'Mancal Combinado',
        r'mancal[_\s]*escora': 'Mancal Escora',
        r'manc[_\s]*rad[_\s]*guia': 'Mancal Radial Guia',
        
        # Tiristores
        r'tiristor[_\s]*0?1': 'Tiristor 1',
        r'tiristor[_\s]*0?2': 'Tiristor 2',
        r'tiristor[_\s]*0?3': 'Tiristor 3',
        
        # Crowbar
        r'crowbar[_\s]*0?1': 'Resistor Crowbar 01',
        r'crowbar[_\s]*0?2': 'Resistor Crowbar D02',
        
        # Transformador
        r'transf[_\s]*excita': 'Transformador de Excitação',
        
        # CSS
        r'cssu?\d*': 'CSS-U1',
        
        # Gaxeteiros
        r'(gaxeteiro|gaxet)[_\s]*0?1': 'Gaxeteiro 01',
        r'(gaxeteiro|gaxet)[_\s]*0?2': 'Gaxeteiro 02',
        r'(gaxeteiro|gaxet)[_\s]*0?3': 'Gaxeteiro 03',
        
        # Bucha Radial
        r'bucha[_\s]*(radial|rad)[_\s]*0?1': 'Bucha Radial O1',
        r'bucha[_\s]*(radial|rad)[_\s]*0?2': 'Bucha Radial O2',
    }
    
    # Tentar match com padrões específicos
    for padrao, nomes_sensores in padroes.items():
        if re.search(padrao, nome_limpo, re.IGNORECASE):
            # nomes_sensores pode ser uma string ou uma lista de strings
            if isinstance(nomes_sensores, str):
                nomes_sensores = [nomes_sensores]
            
            # Tentar cada opção de nome
            for nome_sensor in nomes_sensores:
                # Verificar se esse nome existe nas variáveis disponíveis
                if nome_sensor in variaveis_disponiveis:
                    return nome_sensor
                # Tentar variações do nome
                for var_nome in variaveis_disponiveis.keys():
                    if nome_sensor.lower() in var_nome.lower() or var_nome.lower() in nome_sensor.lower():
                        return var_nome
    
    # Se não encontrou com regex, tentar match fuzzy
    # Normalizar nome_limpo para comparação
    nome_para_busca = nome_limpo.replace('_', ' ').title()
    
    # Buscar matches próximos
    matches = get_close_matches(nome_para_busca, variaveis_disponiveis.keys(), n=1, cutoff=0.6)
    if matches:
        return matches[0]
    
    # Última tentativa: buscar substring
    nome_lower = nome_limpo.lower()
    for var_nome in variaveis_disponiveis.keys():
        var_lower = var_nome.lower()
        # Remover caracteres especiais para comparação
        var_limpo = re.sub(r'[^\w\s]', '', var_lower)
        nome_limpo_comp = re.sub(r'[^\w\s]', '', nome_lower)
        
        if nome_limpo_comp in var_limpo or var_limpo in nome_limpo_comp:
            return var_nome
    
    return None

def relatorio_temperaturas(usina, ug, df, potencia_name):
    
    data_atual = datetime.now().strftime('%Y-%m-%d')
    data_inicio = df['data_hora'].min().strftime('%Y-%m-%d')
    data_fim = df['data_hora'].max().strftime('%Y-%m-%d')
    print(data_inicio, data_fim)
    # filtrar os dados para os ultimos 60 dias
    df['data_hora'] = pd.to_datetime(df['data_hora'])

    # Obter os setpoints de temperaturas da usina
    variaveis = obter_setpoints_temperaturas(usina, ug)
    
    # Criar dicionário de mapeamento usando a função de regex
    # Mapear cada coluna do DataFrame para o nome do sensor físico
    mapeamento_colunas = {}
    colunas_nao_mapeadas = []
    
    print(f"\n{'='*60}")
    print(f"MAPEAMENTO DE COLUNAS - {usina} - {ug}")
    print(f"{'='*60}")
    
    for coluna in df.columns:
        if coluna == 'data_hora':
            continue
        nome_sensor = mapear_nome_coluna_para_sensor(coluna, variaveis)
        if nome_sensor:
            mapeamento_colunas[coluna] = nome_sensor
            print(f"✅ {coluna:30} → {nome_sensor}")
        else:
            # Se não encontrou mapeamento, manter o nome original mas formatado
            nome_formatado = coluna.replace('_', ' ').title()
            mapeamento_colunas[coluna] = nome_formatado
            colunas_nao_mapeadas.append(coluna)
            print(f"⚠️  {coluna:30} → {nome_formatado} (SEM SETPOINTS)")
    
    if colunas_nao_mapeadas:
        print(f"\n{'='*60}")
        print(f"⚠️  ATENÇÃO: {len(colunas_nao_mapeadas)} coluna(s) não mapeada(s)")
        print(f"As seguintes colunas receberão alarme=0 e trip=0:")
        for col in colunas_nao_mapeadas:
            print(f"   - {col}")
        print(f"{'='*60}\n")
    
    # Não filtramos mais as colunas - elas já vêm filtradas do main.py
    # Apenas garantimos que data_hora esteja em formato datetime


    # CSS para quebras de página em PDF
    st.markdown("""

    """, unsafe_allow_html=True)

    # Cabeçalho com logos alinhados
    cols = st.columns([1, 2, 1])
    with cols[0]:
        st.markdown('<div class="header-col">', unsafe_allow_html=True)
        st.image('assets/imgs/logo_novo.png', width=250)
        st.markdown('</div>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f"""
        <div class="header-title-col">
            <h3 style="margin: 0; color: #000; line-height: 1.0;">{usina}</h3>
            <p style="margin: 5px 0 0 0; color: #666; font-size: 0.9em;">Relatório de Temperaturas</p>
        </div>
        """, unsafe_allow_html=True)
    with cols[2]:
        st.markdown('<div class="header-col">', unsafe_allow_html=True)
        st.image('assets/imgs/IA.png', width=80)
        st.markdown('</div>', unsafe_allow_html=True)

    # Linha separadora
    st.markdown('<hr style="border: 2px solid #007bff; margin: 20px 0;">', unsafe_allow_html=True)

    # st.write(df.columns)

    # Seção de introdução formatada
    st.markdown("""
    <div class="intro-section">
    <h4>📄 Relatório de Temperaturas {}</h4>

    <p>Este relatório foi gerado em <strong>{}</strong>, contendo dados coletados a cada 1 minuto durante o período de <strong>{}</strong> a <strong>{}</strong>.</p>

    <p>O presente documento apresenta uma análise detalhada das temperaturas dos componentes críticos da unidade geradora, incluindo:</p>

    <ul>
    <li><strong>Vedações de Eixo</strong> - Temperaturas das vedações (L.A. e L.N.A.)</li>
    <li><strong>Mancais</strong> - Temperaturas dos mancais radiais e de escora</li>
    <li><strong>Óleo</strong> - Temperaturas do óleo</li>
    </ul>

    <p>As análises incluem estatísticas descritivas completas (média, desvio padrão, valores mínimo e máximo, mediana e quartis) para cada variável monitorada.</p>
    </div>
    """.format(usina + ' ' + ug, datetime.now().strftime('%d/%m/%Y às %H:%M:%S'), 
            pd.to_datetime(df['data_hora'].min()).strftime('%d/%m/%Y %H:%M'), 
            pd.to_datetime(df['data_hora'].max()).strftime('%d/%m/%Y %H:%M')), unsafe_allow_html=True)

    # Seção de metodologia
    st.markdown("""
    <div class="intro-section">
    <h4>🔬 Metodologia de Análise</h4>

    <p><strong>Taxa de Variação:</strong> Calculada para intervalos de 5 minutos utilizando a diferença entre médias móveis consecutivas, permitindo identificar tendências de curto prazo nos dados.</p>

    <p><strong>Análise de Tendências:</strong> Baseada na comparação entre valores atuais e médias históricas.</p>

    <p><strong>Limites Operacionais:</strong> Cada variável possui limites de alarme e trip predefinidos, representados graficamente para facilitar a identificação de condições críticas.</p>
    </div>
    """, unsafe_allow_html=True)
    # Adicionar quebra de página antes das análises
    st.markdown('<div class="page-break"></div>', unsafe_allow_html=True)
    # Seção de fórmulas
    st.markdown("""
    <div class="formula-section">
    <h4>📊 Fórmulas Utilizadas</h4>

    <ul>
    <li><strong>Tendência Absoluta:</strong> Tendência = Temperatura Atual - Média Histórica</li>
    <li><strong>Taxa de Variação:</strong> Diferença entre médias móveis de 5 minutos consecutivos</li>
    <li><strong>Correlação:</strong> Coeficiente de Pearson entre variáveis (0 = sem correlação, 1 = correlação perfeita)</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    # Renomear as colunas usando o mapeamento criado
    df = df.rename(columns=mapeamento_colunas)
    
    # Limpar dados inválidos
    # df = df.dropna()  # Removido para não perder dados válidos

    def criar_grafico_temperatura(df, coluna, titulo, variaveis):

        
        # --- REDUÇÃO DE DADOS PARA MELHOR PERFORMANCE ---
        df_plot = df[['data_hora', coluna]].copy()
        
        # Se tiver mais de 5000 pontos, reduzir
        if len(df_plot) > 5000:
            step = len(df_plot) // 5000
            df_plot = df_plot.iloc[::step]
        
        # Criar gráfico com matplotlib (mais estável e leve)
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # Plotar linha de temperatura
        ax.plot(df_plot['data_hora'], df_plot[coluna], color='blue', linewidth=1)
        
        # Adicionar linhas de alarme e trip apenas se não forem 0
        if variaveis['alarme'] > 0 or variaveis['trip'] > 0:
            if variaveis['alarme'] > 0:
                ax.axhline(y=variaveis['alarme'], color='orange', linestyle='--', linewidth=2, label='Alarme')
            if variaveis['trip'] > 0:
                ax.axhline(y=variaveis['trip'], color='red', linestyle='--', linewidth=2, label='Trip')
        
        # Configurar título e labels
        ax.set_title(titulo, fontsize=12)
        ax.set_xlabel('Data', fontsize=10)
        ax.set_ylabel('Temperatura (°C)', fontsize=10)
        
        # Configurar eixo Y
        if variaveis['trip'] > 0:
            ax.set_ylim([0, variaveis['trip'] + 5])
        else:
            # Se trip for 0, usar os dados para definir escala
            max_val = df_plot[coluna].max()
            ax.set_ylim([0, max_val * 1.1])
        
        # Formatar eixo X para mostrar datas
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45)
        
        # Grid
        ax.grid(True, alpha=0.3)
        
        # Legenda - posicionada no canto superior esquerdo para não cobrir os dados
        # Só mostra legenda se houver linhas de alarme/trip
        if variaveis['alarme'] > 0 or variaveis['trip'] > 0:
            ax.legend(loc='upper left', bbox_to_anchor=(0, 1), framealpha=0.9)
        
        # Ajustar layout
        plt.tight_layout()
        
        # Exibir no Streamlit
        st.pyplot(fig)
        plt.close()
    
    # Iterar sobre todas as colunas (exceto data_hora)
    for coluna in df.columns:
        # Pular a coluna data_hora
        if coluna == 'data_hora':
            continue
            
        with st.container():
            # Buscar os setpoints da coluna nas variáveis da usina
            setpoints_coluna = variaveis.get(coluna)
            
            # Se não encontrou setpoints, usar valores 0 (coluna não mapeada)
            setpoints_automaticos = False
            if not setpoints_coluna:
                # Colunas não mapeadas recebem alarme e trip = 0
                setpoints_coluna = {
                    "alarme": 0.0,
                    "trip": 0.0
                }
                setpoints_automaticos = True
            
            # Sempre gerar gráfico e estatísticas para cada coluna selecionada
            if True:  # Sempre True agora que garantimos ter setpoints
                # Adicionar quebra de página antes de cada nova seção (exceto a primeira)
                if coluna != list(df.columns)[0]:
                    st.markdown('<div class="page-break"></div>', unsafe_allow_html=True)
                
                # Container que não deve quebrar internamente
                st.markdown('<div class="no-break">', unsafe_allow_html=True)
                
                # Cabeçalho da seção
                st.markdown(f'<h4 style="color: #3c3c3c; border-bottom: 1px solid #3c3c3c; padding-bottom: 10px;">Análise de Temperatura - {coluna}</h4>', unsafe_allow_html=True)
                
                criar_grafico_temperatura(df, coluna, f'{coluna} - {usina.upper()}', setpoints_coluna)
                
                # Seção de estatísticas em duas colunas
                cols = st.columns(2)
                with cols[0]:
                    st.markdown(f'<h5 style="color: #3c3c3c; border-bottom: 1px solid #3c3c3c; padding-bottom: 10px;">Variáveis Descritivas</h4>', unsafe_allow_html=True)
                    st.dataframe(df[coluna].describe())
                with cols[1]:
                    # taxa_atual = df_taxa[coluna].mean()
                    tedencia_atual = df[coluna].iloc[-1] - df[coluna].mean()
                    desvio_padrao_max = df[coluna].std()
                    st.markdown(f'<h5 style="color: #3c3c3c; border-bottom: 1px solid #3c3c3c; padding-bottom: 10px;">Taxa de Variação</h4>', unsafe_allow_html=True)
                    percentual_tendencia = (tedencia_atual / desvio_padrao_max) * 100 if desvio_padrao_max != 0 else 0
                    if tedencia_atual > 0:
                        st.markdown(f'<p><strong>Tendência atual:</strong> <span style="color: #dc3545;">{tedencia_atual:.2f}°C acima da média </span></p>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<p><strong>Tendência atual:</strong> <span style="color: #28a745;">{tedencia_atual:.2f}°C abaixo da média</span></p>', unsafe_allow_html=True)
                    
                    # st.markdown(f'<p><strong>Taxa de variação:</strong> {round(taxa_atual, 4)}°C</p>', unsafe_allow_html=True)
                    st.markdown(f'<p><strong>Desvio padrão:</strong> {round(desvio_padrao_max, 4)}°C</p>', unsafe_allow_html=True)
                    st.markdown(f'<p><strong>Média:</strong> {round(df[coluna].mean(), 2)}°C</p>', unsafe_allow_html=True)
                    
                    # Adicionar informações sobre limites
                    st.markdown(f'<p><strong>Limite de Alarme:</strong> {setpoints_coluna["alarme"]:.2f}°C</p>', unsafe_allow_html=True)
                    st.markdown(f'<p><strong>Limite de Trip:</strong> {setpoints_coluna["trip"]:.2f}°C</p>', unsafe_allow_html=True)
                    
                    # Informar se os setpoints foram criados automaticamente (valor 0)
                    if setpoints_automaticos:
                        st.markdown('<p style="color: #dc3545; font-size: 0.85em;">⚠️ Sensor não mapeado - limites indefinidos (0)</p>', unsafe_allow_html=True)
                
                # Fechar container no-break
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Adicionar quebra de página após cada seção
                st.markdown('<div class="page-break-after"></div>', unsafe_allow_html=True)

    # Adicionar quebra de página antes da seção de correlação
    st.markdown('<div class="page-break"></div>', unsafe_allow_html=True)

    # Seção de correlação entre variáveis
    st.markdown("""
    <div class="intro-section">
    <h3>🔗 Análise de Correlação entre Variáveis</h3>

    <p>A matriz de correlação abaixo mostra a relação entre todas as variáveis de temperatura monitoradas. Valores próximos a 1 indicam correlação positiva forte, valores próximos a -1 indicam correlação negativa forte, e valores próximos a 0 indicam baixa correlação.</p>
    </div>
    """, unsafe_allow_html=True)

    # Calcular e exibir matriz de correlação (excluindo a coluna data_hora)
    df_numeric = df.select_dtypes(include=['float64', 'int64'])
    correlation_matrix = df_numeric.corr()

    # Criar heatmap de correlação com Plotly
    fig_corr = px.imshow(
        correlation_matrix,
        text_auto='.2f',
        aspect="auto",
        color_continuous_scale="RdBu_r",
        title="Matriz de Correlação - Variáveis de Temperatura",
        labels=dict(x="Variáveis", y="Variáveis", color="Correlação")
    )

    # Configurar layout do gráfico
    fig_corr.update_layout(
        width=800,
        height=600,
        title_x=0.5,
        title_font_size=16,
        font=dict(size=10)
    )

    # Configurar eixo X (rotacionar labels para melhor visualização)
    fig_corr.update_xaxes(
        tickangle=45
    )

    st.plotly_chart(fig_corr, use_container_width=True)

    # Adicionar tabela resumida das correlações mais significativas
    st.markdown('<h5 style="color: #007bff;">📊 Correlações Mais Significativas (>0.7)</h5>', unsafe_allow_html=True)

    # Encontrar correlações mais significativas
    high_corr = []
    for i in range(len(correlation_matrix.columns)):
        for j in range(i+1, len(correlation_matrix.columns)):
            corr_value = correlation_matrix.iloc[i, j]
            if abs(corr_value) > 0.7:
                high_corr.append({
                    'Variável 1': correlation_matrix.columns[i],
                    'Variável 2': correlation_matrix.columns[j],
                    'Correlação': corr_value
                })

    if high_corr:
        high_corr_df = pd.DataFrame(high_corr).sort_values('Correlação', ascending=False)
        st.dataframe(high_corr_df.round(3))
    else:
        st.write("Nenhuma correlação forte (>0.7) encontrada entre as variáveis.")

    # Adicionar interpretação das correlações mais significativas
    st.markdown("""
    <div class="formula-section">
    <h4>📈 Interpretação das Correlações</h4>

    <ul>
    <li><strong>Correlação > 0.7:</strong> Correlação positiva forte - as variáveis tendem a aumentar juntas</li>
    <li><strong>Correlação entre 0.3 e 0.7:</strong> Correlação positiva moderada</li>
    <li><strong>Correlação entre -0.3 e 0.3:</strong> Baixa correlação</li>
    <li><strong>Correlação entre -0.7 e -0.3:</strong> Correlação negativa moderada</li>
    <li><strong>Correlação < -0.7:</strong> Correlação negativa forte - quando uma aumenta, a outra diminui</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    # Rodapé do relatório
    st.markdown("""
    <div style="margin-top: 3rem; padding: 2rem; background-color: #f8f9fa; border-radius: 10px; border-top: 3px solid #007bff;">
    <h3 style="color: #007bff; text-align: center;">📋 Relatório Concluído</h3>

    <p style="text-align: center; margin-bottom: 1rem;"><strong>Este relatório foi gerado automaticamente pelo sistema de monitoramento da{}</strong></p>

    <div style="display: flex; justify-content: space-between; font-size: 0.9em; color: #666;">
    <div>
    <p><strong>Data de Geração:</strong> {}</p>
    <p><strong>Período Analisado:</strong> {} a {}</p>
    </div>
    <div>
    <p><strong>Total de Variáveis:</strong> {}</p>
    <p><strong>Total de Registros:</strong> {:,}</p>
    </div>
    </div>

    <p style="text-align: center; margin-top: 2rem; font-size: 0.8em; color: #999;">
    ⚠️ Este documento contém informações técnicas críticas para a operação da unidade geradora. 
    Mantenha-o em local seguro e consulte a equipe técnica em caso de dúvidas.
    </p>
    </div>
    """.format(usina, 
            datetime.now().strftime('%d/%m/%Y às %H:%M:%S'),
            pd.to_datetime(df['data_hora'].min()).strftime('%d/%m/%Y %H:%M'),
            pd.to_datetime(df['data_hora'].max()).strftime('%d/%m/%Y %H:%M'),
            len([col for col in df.columns if col != 'data_hora']),
            len(df)), unsafe_allow_html=True)

# Aplicar estilos CSS
st.markdown(styles, unsafe_allow_html=True)
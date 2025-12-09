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

#----------------------------------------------------------------------------------
# Funções para processar os dados de temperatura
#    1. obter_setpoints_temperaturas: Obtém os setpoints de temperatura para a usina e unidade geradora
#    2. mapear_nome_coluna_para_sensor: Mapeia o nome da coluna do banco de dados para o nome do sensor físico
#    3. processar_dados_temperaturas: Processa os dados de temperatura para a usina e unidade geradora
#----------------------------------------------------------------------------------

def obter_setpoints_temperaturas(usina, ug):
    usina_ = usina.replace('-',' ').upper()
    valores_usina = valores.get(usina_, {})
    valores_ug = valores_usina.get(ug, {})
    return valores_ug

def mapear_nome_coluna_para_sensor(nome_coluna, variaveis_disponiveis):
    nome_limpo = re.sub(r'^(ug\d{2}_|temp_)', '', nome_coluna, flags=re.IGNORECASE)
    
    padroes = {
        r'enrol[_\s]*fase[_\s]*a': ['Enrolamento Fase A', 'Fase A'],
        r'enrol[_\s]*fase[_\s]*b': ['Enrolamento Fase B', 'Fase B'],
        r'enrol[_\s]*fase[_\s]*c': ['Enrolamento Fase C', 'Fase C'],
        r'enrol[_\s]*[_\s]*a\b': ['Enrolamento Fase A', 'Fase A'],
        r'enrol[_\s]*[_\s]*b\b': ['Enrolamento Fase B', 'Fase B'],
        r'enrol[_\s]*[_\s]*c\b': ['Enrolamento Fase C', 'Fase C'],
        r'(oleo[_\s]*uhrv|uhrv[_\s]*(temp[_\s]*)?oleo|temp[_\s]*oleo[_\s]*uhrv)': 'Óleo U.H.R.V.',
        r'(oleo[_\s]*uhlm|uhlm[_\s]*(temp[_\s]*)?oleo|temp[_\s]*oleo[_\s]*uhlm)': 'Óleo U.H.L.M.',
        r'nucleo[_\s]*estator[_\s]*0?1': ['Núcleo Estator 1', 'Núcleo Estator'],
        r'nucleo[_\s]*estator[_\s]*0?2': ['Núcleo Estator 2', 'Núcleo Estator'],
        r'nucleo[_\s]*estator[_\s]*0?3': ['Núcleo Estator 3', 'Núcleo Estator'],
        r'nucleo[_\s]*estator': 'Núcleo Estator',
        r'manc[_\s]*(al)?[_\s]*casq[_\s]*comb': 'Mancal Comb. Casq.',
        r'manc[_\s]*(al)?[_\s]*casq[_\s]*(esc|escora)': 'Mancal Comb. Esc.',
        r'manc[_\s]*(al)?[_\s]*(cont|contra)[_\s]*(esc|escora)': 'Mancal Comb. Contra Esc.',
        r'manc[_\s]*(al)?[_\s]*casq[_\s]*guia': 'Mancal Guia Casq. Turb.',
        r'casq[_\s]*rad[_\s]*comb': 'Mancal Radial Guia',
        r'manc[_\s]*(al)?[_\s]*lna[_\s]*guia': 'Mancal L.N.A. Guia',
        r'manc[_\s]*(al)?[_\s]*la[_\s]*guia': 'Mancal L.A. Guia',
        r'manc[_\s]*(al)?[_\s]*lna[_\s]*(esc|escora)': 'Mancal L.N.A. Escora',
        r'manc[_\s]*(al)?[_\s]*la[_\s]*(esc|escora)': 'Mancal L.A. Escora',
        r'mancal[_\s]*guia': 'Mancal Guia',
        r'mancal[_\s]*combinado': 'Mancal Combinado',
        r'mancal[_\s]*escora': 'Mancal Escora',
        r'manc[_\s]*rad[_\s]*guia': 'Mancal Radial Guia',
        r'tiristor[_\s]*0?1': 'Tiristor 1',
        r'tiristor[_\s]*0?2': 'Tiristor 2',
        r'tiristor[_\s]*0?3': 'Tiristor 3',
        r'crowbar[_\s]*0?1': 'Resistor Crowbar 01',
        r'crowbar[_\s]*0?2': 'Resistor Crowbar D02',
        r'transf[_\s]*excita': 'Transformador de Excitação',
        r'cssu?\d*': 'CSS-U1',
        r'(gaxeteiro|gaxet)[_\s]*0?1': 'Gaxeteiro 01',
        r'(gaxeteiro|gaxet)[_\s]*0?2': 'Gaxeteiro 02',
        r'(gaxeteiro|gaxet)[_\s]*0?3': 'Gaxeteiro 03',
        r'bucha[_\s]*(radial|rad)[_\s]*0?1': 'Bucha Radial O1',
        r'bucha[_\s]*(radial|rad)[_\s]*0?2': 'Bucha Radial O2',
        r'temp_vedacao_eixo_lna': 'Vedação Eixo L.N.A.',
        r'temp_vedacao_eixo_la': 'Vedação Eixo L.A.',
    }
    # print(f"nome_limpo: {nome_limpo}")
    if nome_limpo == 'vedacao_eixo_lna':
        return 'Vedação Eixo L.N.A.'
    if nome_limpo == 'vedacao_eixo_la':
        return 'Vedação Eixo L.A.'
    if nome_limpo == 'manc_rad_comb_lna':
        return 'Mancal Rad. Comb. L.N.A.'
    if nome_limpo == 'manc_rad_comb_la':
        return 'Mancal Rad. Comb. L.A.'
    
    for padrao, nomes_sensores in padroes.items():
        
        
        if re.search(padrao, nome_limpo, re.IGNORECASE):
            if isinstance(nomes_sensores, str):
                nomes_sensores = [nomes_sensores]
            
            for nome_sensor in nomes_sensores:
                if nome_sensor in variaveis_disponiveis:
                    return nome_sensor
                for var_nome in variaveis_disponiveis.keys():
                    if nome_sensor.lower() in var_nome.lower() or var_nome.lower() in nome_sensor.lower():
                        return var_nome
    
    nome_para_busca = nome_limpo.replace('_', ' ').title()
    
    matches = get_close_matches(nome_para_busca, variaveis_disponiveis.keys(), n=1, cutoff=0.6)
    if matches:
        return matches[0]
    
    nome_lower = nome_limpo.lower()
    for var_nome in variaveis_disponiveis.keys():
        var_lower = var_nome.lower()
        var_limpo = re.sub(r'[^\w\s]', '', var_lower)
        nome_limpo_comp = re.sub(r'[^\w\s]', '', nome_lower)
        
        if nome_limpo_comp in var_limpo or var_limpo in nome_limpo_comp:
            return var_nome
    
    return None

# Função finalizada
def processar_dados_temperaturas(usina, ug, df, potencia_name):

    mapeamento_colunas = {}
    nomes_finais_usados = set()

    variaveis = obter_setpoints_temperaturas(usina, ug)
    print(f"\n MAPEAMENTO DE COLUNAS - {usina} - {ug} \n")
    for coluna in df.columns:
        if coluna == 'data_hora' or coluna == potencia_name:
            continue
        
        nome_sensor = mapear_nome_coluna_para_sensor(coluna, variaveis)
        
        if nome_sensor:
            nome_final = nome_sensor
            if nome_final in nomes_finais_usados:
                partes_coluna = coluna.split('_')
                sufixo = partes_coluna[-1].upper() if len(partes_coluna) > 1 else "2"
                nome_final = f"{nome_sensor} ({sufixo})"
                
                # Garante que o novo nome com sufixo também seja único
                contador = 2
                while nome_final in nomes_finais_usados:
                    nome_final = f"{nome_sensor} ({sufixo}-{contador})"
                    contador += 1
                    
                print(f"⚠️  {coluna:30} → {nome_final} (DUPLICATA)")
            else:
                print(f"✅ {coluna:30} → {nome_final}")

            nomes_finais_usados.add(nome_final)
            mapeamento_colunas[coluna] = nome_final
        else:
            nome_formatado = coluna.replace('_', ' ').title()
            if nome_formatado in nomes_finais_usados:
                 partes_coluna = coluna.split('_')
                 sufixo = partes_coluna[-1].upper() if len(partes_coluna) > 1 else "2"
                 nome_formatado = f"{nome_formatado} ({sufixo})"
                 print(f"⚠️  {coluna:30} → {nome_formatado} (DUPLICATA SEM SETPOINTS)")
            else:
                print(f"⚠️  {coluna:30} → {nome_formatado} (SEM SETPOINTS)")

            nomes_finais_usados.add(nome_formatado)
            mapeamento_colunas[coluna] = nome_formatado

    df = df.rename(columns=mapeamento_colunas)

    return df, mapeamento_colunas, variaveis

#----------------------------------------------------------------------------------
# Funções que criam os componentes do relatório de temperatura
#    1. cabecalho: implementa o logo da empresa, nome da usina e logo da IA
#    2. secao_introducao: implementa a descrição das variáveis monitoradas e o período de coleta dos dados
#    3. grafico_temperatura: gera um gráfico de temperatura para uma variável
#    4. grafico_temperatura_potencia: gera um gráfico de temperatura vs potência para uma variável
#    5. rodape: implementa o rodapé do relatório
#----------------------------------------------------------------------------------

def cabecalho(usina, ug, df):
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
        </div>""", unsafe_allow_html=True)
    with cols[2]:
        st.markdown('<div class="header-col">', unsafe_allow_html=True)
        st.image('assets/imgs/IA.png', width=80)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<hr style="border: 2px solid #007bff; margin: 20px 0;">', unsafe_allow_html=True)

def secao_introducao(usina, ug, df):
    st.markdown(f"""
    <div class="intro-section">
        <h5>📄 Relatório de Temperaturas {usina + ' ' + ug}</h5>
        <p>Este relatório foi gerado em <strong>{datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</strong>, contendo dados coletados a cada 1 minuto durante o período de <strong>{pd.to_datetime(df['data_hora'].min()).strftime('%d/%m/%Y %H:%M')}</strong> a <strong>{pd.to_datetime(df['data_hora'].max()).strftime('%d/%m/%Y %H:%M')}</strong>.</p>
        <p>O presente documento apresenta uma análise detalhada das temperaturas dos componentes críticos da unidade geradora, incluindo:</p>
        <ul>
            <li><strong>Vedações de Eixo</strong> - Temperaturas das vedações (L.A. e L.N.A.)</li>
            <li><strong>Mancais</strong> - Temperaturas dos mancais radiais e de escora</li>
            <li><strong>Óleo</strong> - Temperaturas do óleo</li>
        </ul>
        <p>As análises incluem estatísticas descritivas completas (média, desvio padrão, valores mínimo e máximo, mediana e quartis) para cada variável monitorada.</p>
    </div>
    """,unsafe_allow_html=True)


def grafico_temperatura(df, col_temp, col_pot, titulo, variaveis):
    """
    df: DataFrame com 'data_hora', col_temp e col_pot
    col_temp: nome da coluna de temperatura
    col_pot: nome da coluna de potência ativa
    variaveis: dict com {'alarme': float, 'trip': float}
    """
    # --- base limpa + downsampling leve para grandes volumes ---
    cols = ["data_hora", col_temp, col_pot]
    d = df[cols].copy()
    # salvar o dataframe original em um arquivo csv
    # df.to_csv('assets/df_original.csv', index=False)
    # d["data_hora"] = pd.to_datetime(d["data_hora"], errors="coerce")
    # d[col_temp] = pd.to_numeric(d[col_temp], errors="coerce")
    # d[col_pot] = pd.to_numeric(d[col_pot], errors="coerce")
    # calcular a media movel de 20 minutos para a col_pot
    d['pot_media'] = d[col_pot].rolling(window=20).mean()
    # remover valores igual a zero da coluna de potência
    # d = d[d['pot_media'] <= 20]
    # d = d.dropna(subset=["data_hora"])

    # --- criar subplots: 2 linhas, eixo X compartilhado ---
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,  # Compartilha eixo X
        vertical_spacing=0.05,  # Espaço entre gráficos
        row_heights=[0.7, 0.3],  # Temperatura maior, potência menor
        subplot_titles=(titulo, None)  # Título só no primeiro
    )

    # --- Linha de Temperatura ---
    fig.add_trace(
        go.Scatter(
            x=d["data_hora"], 
            y=d[col_temp],
            mode="lines",
            name="Temperatura",
            line=dict(color="#F54927", width=1.5),
            hovertemplate="<b>%{x}</b><br>Temp: %{y:.1f}°C<extra></extra>"
        ),
        row=1, col=1
    )

    # # --- Linha de Tendência (Média Móvel) ---
    # fig.add_trace(
    #     go.Scatter(
    #         x=d["data_hora"], 
    #         y=d[col_temp].rolling(window=60).mean(),
    #         mode="lines",
    #         name="Tendência",
    #         line=dict(color="#3c3c3c", width=2, dash="dash"),
    #         hovertemplate="<b>%{x}</b><br>Tendência: %{y:.1f}°C<extra></extra>"
    #     ),
    #     row=1, col=1
    # )

    # --- Linhas de Alarme/Trip ---
    if variaveis.get("alarme", 0) > 0:
        fig.add_hline(
            y=variaveis["alarme"], 
            line_dash="dash", 
            line_width=2,
            line_color="orange", 
            annotation_text="Alarme",
            annotation_position="top left",
            row=1, col=1
        )
    if variaveis.get("trip", 0) > 0:
        fig.add_hline(
            y=variaveis["trip"], 
            line_dash="dash", 
            line_width=2,
            line_color="red", 
            annotation_text="Trip",
            annotation_position="top left",
            row=1, col=1
        )

    # --- Área de Potência ---
    fig.add_trace(
        go.Scatter(
            x=d["data_hora"], 
            y=d['pot_media'],
            mode="lines",
            name="Potência",
            fill="tozeroy",
            line=dict(color="royalblue", width=1.5),
            hovertemplate="<b>%{x}</b><br>Potência: %{y:.0f} kW<extra></extra>"
        ),
        row=2, col=1
    )

    # --- Layout ---
    fig.update_layout(
        template="plotly_white",
        height=650,
        margin=dict(l=60, r=20, t=60, b=60),
        hovermode="x unified",
        showlegend=False
    )

    # --- Eixos ---
    # Temperatura (row 1)
    fig.update_yaxes(title_text="Temperatura (°C)", row=1, col=1)
    
    # Potência (row 2)
    fig.update_yaxes(title_text="Potência (kW)", row=2, col=1)
    fig.update_xaxes(title_text="Data", row=2, col=1)  # Label "Data" só no eixo inferior

    # --- render no Streamlit ---
    st.plotly_chart(fig, use_container_width=True)

def _card_metrica(titulo, valor, unidade="°C", cor="#3c3c3c", subtexto=None):
    """Card compacto estilo mobile (8px padding)"""
    subtexto_html = f'<span style="font-size: 0.75em; font-weight: normal; color: #666;"> {subtexto}</span>' if subtexto else ''
    
    return f"""
    <div style="background: white; padding: 8px 12px; border-radius: 6px; margin-top: 6px; border: 1px solid #e0e0e0;">
        <p style="margin: 0 0 4px 0; font-size: 0.8em; color: #999;">{titulo}</p>
        <p style="margin: 0; font-size: 1.4em; font-weight: bold; color: {cor}; line-height: 1.2;">
            {valor:.2f}{unidade}{subtexto_html}
        </p>
    </div>
    """

def _card_header(icone, titulo):
    """Header compacto estilo mobile (12px padding)"""
    return f"""
    <div style="background: #f8f9fa; padding: 10px 12px; border-radius: 6px; border-left: 3px solid #3c3c3c; margin-bottom: 6px;">
        <h6 style="margin: 0; color: #3c3c3c; font-size: 0.9em; font-weight: 600;">{icone} {titulo}</h6>
    </div>
    """

def _tabela_estatisticas(media, std, minimo, maximo):
    """Tabela ultra-compacta estilo mobile"""
    stats = [
        ("Média", media),
        ("Desvio Padrão", std),
        ("Mínima", minimo),
        ("Máxima", maximo)
    ]
    
    linhas = "".join([
        f'<tr><td style="color: #666;  padding: 3px 3px 3px 3px; font-size: 0.85em;">{label}</td>'
        f'<td style="text-align: right; font-weight: 600; color: #3c3c3c; font-size: 0.9em;">{val:.2f}°C</td></tr>'
        for label, val in stats
    ])
    
    return f"""
        <table style="width: 100%; margin: 3px 3px 3px 3px; border-spacing: 0; border-radius: 6px; border: 1px solid #e0e0e0;">{linhas}</table>
    """

def _card_limites(alarme, trip):
    """Card de limites compacto estilo mobile"""
    if alarme <= 0 and trip <= 0:
        return """
        <div style="background: #fff3cd; padding: 10px 12px; border-radius: 6px; margin-top: 6px; border-left: 3px solid #ffc107;">
            <p style="margin: 0; font-size: 0.8em; color: #856404; line-height: 1.4;">
                ⚠️ Sensor não mapeado<br><span style="font-size: 0.85em;">Limites indefinidos</span>
            </p>
        </div>
        """
    
    return f"""
    <div style="background: white; padding: 10px 12px; border-radius: 6px; margin-top: 6px; border: 1px solid #e0e0e0;">
        <div style="margin-bottom: 8px;">
            <p style="margin: 0 0 2px 0; font-size: 0.8em; color: #999;">Alarme</p>
            <p style="margin: 0; font-size: 1.3em; font-weight: bold; color: #ff9800; line-height: 1;">{alarme:.2f}°C</p>
        </div>
        <div style="border-top: 1px solid #f0f0f0; padding-top: 8px;">
            <p style="margin: 0 0 2px 0; font-size: 0.8em; color: #999;">Trip</p>
            <p style="margin: 0; font-size: 1.3em; font-weight: bold; color: #dc3545; line-height: 1;">{trip:.2f}°C</p>
        </div>
    </div>
    """

def renderizar_estatisticas(df, coluna, setpoints_coluna):
    """Renderização compacta estilo mobile app"""
    # Calcular métricas
    temp_atual = df[coluna].iloc[-1]
    temp_media = df[coluna].mean()
    temp_std = df[coluna].std()
    temp_min = df[coluna].min()
    temp_max = df[coluna].max()
    tendencia = temp_atual - temp_media
    
    cor_tend = "#dc3545" if tendencia > 0 else "#28a745"
    texto_tend = "acima" if tendencia > 0 else "abaixo"
    
    # Container compacto
    st.markdown('<div style="margin: 12px 0;">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1.2, 1, 1], gap="small")
    
    with col1:
        st.markdown(_card_header("📊", "Situação Atual"), unsafe_allow_html=True)
        st.markdown(_card_metrica("Tendência", abs(tendencia), cor=cor_tend, subtexto=f"{texto_tend} da média"), unsafe_allow_html=True)
        st.markdown(_card_metrica("Temperatura Atual", temp_atual), unsafe_allow_html=True)
    
    with col2:
        st.markdown(_card_header("📈", "Estatísticas"), unsafe_allow_html=True)
        st.markdown(_tabela_estatisticas(temp_media, temp_std, temp_min, temp_max), unsafe_allow_html=True)
    
    with col3:
        st.markdown(_card_header("⚠️", "Limites"), unsafe_allow_html=True)
        st.markdown(_card_limites(setpoints_coluna["alarme"], setpoints_coluna["trip"]), unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


def rodape(usina, df):
    st.markdown(f"""
    <div style="margin-top: 3rem; padding: 2rem; background-color: #f8f9fa; border-radius: 10px; border-top: 3px solid #007bff;">
        <h3 style="color: #007bff; text-align: center;">📋 Relatório Concluído</h3>
        <p style="text-align: center; margin-bottom: 1rem;"><strong>Este relatório foi gerado automaticamente pelo sistema de monitoramento da {usina}</strong></p>
        <div style="display: flex; justify-content: space-between; font-size: 0.9em; color: #666; margin-bottom: 1rem;">
            <div>
                <p><strong>Data de Geração:</strong> {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</p>
                <p><strong>Período Analisado:</strong> {pd.to_datetime(df['data_hora'].min()).strftime('%d/%m/%Y %H:%M')} a {pd.to_datetime(df['data_hora'].max()).strftime('%d/%m/%Y %H:%M')}</p>
            </div>
            <div>
                <p><strong>Total de Variáveis:</strong> {len([col for col in df.columns if col != 'data_hora'])}</p>
                <p><strong>Total de Registros:</strong> {len(df):,}</p>
            </div>
        </div>
        <div style="text-align: center; margin-top: 2rem; font-size: 0.8em; color: #999;">
            <p style="margin: 0;">
                ⚠️ Este documento contém informações técnicas críticas para a operação da unidade geradora.
                Mantenha-o em local seguro e consulte a equipe técnica em caso de dúvidas.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

#----------------------------------------------------------------------------------
# Funções auxiliares que compoem o layout do relatório
#    1. analises_colunas: compoem os componentes em um layout e quebra de página para geração de um PDF
#    2. relatorio_temperaturas: função principal que executa o fluxo da aplicação
#----------------------------------------------------------------------------------

def analises_colunas(df, variaveis, potencia_name, usina):
    for coluna in df.columns:
        if coluna == 'data_hora' or coluna == potencia_name:
            continue

        with st.container():
            setpoints_coluna = variaveis.get(coluna)

            setpoints_automaticos = False
            if not setpoints_coluna:
                setpoints_coluna = {"alarme": 0.0, "trip": 0.0}
                setpoints_automaticos = True

            if coluna != list(df.columns)[1]:
                st.markdown('<div class="page-break"></div>', unsafe_allow_html=True)

            st.markdown('<div class="no-break">', unsafe_allow_html=True)

            st.markdown(f'<h5 style="color: #3c3c3c; border-bottom: 1px solid #3c3c3c; padding-bottom: 10px;">Temperatura - {coluna}</h5>', unsafe_allow_html=True)

            grafico_temperatura(df, coluna, potencia_name, f'', setpoints_coluna)

            # st.markdown(f'<h5 style="color: #3c3c3c; margin-top: 20px; padding-bottom: 10px;">📊 Relação Temperatura vs Potência Ativa</h5>', unsafe_allow_html=True)
            # grafico_temperatura_potencia(df, coluna, potencia_name, f'{coluna} vs Potência Ativa - {usina.upper()}', setpoints_coluna)
            renderizar_estatisticas(df, coluna, setpoints_coluna)

            st.markdown('<div class="page-break-after"></div>', unsafe_allow_html=True)



def relatorio_temperaturas(usina, ug, df, potencia_name):

    df, mapeamento_colunas, variaveis = processar_dados_temperaturas(usina, ug, df, potencia_name)
    cabecalho(usina, ug, df)
    secao_introducao(usina, ug, df)
    st.markdown('<div class="page-break"></div>', unsafe_allow_html=True)
    analises_colunas(df, variaveis, potencia_name, usina)
    rodape(usina, df)
    # st.markdown(styles, unsafe_allow_html=True)
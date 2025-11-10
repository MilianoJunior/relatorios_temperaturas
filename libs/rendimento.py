

from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
# import streamlit as st

def relatorio_rendimento(usina, df, st):
    st.title(f'Relatório de Rendimento {usina}')
    # renomear as colunas
    df = df.rename(columns={
        'nivel_montante_grade': 'Nível de Água Montante',
        'nivel_jusante_grade': 'Nível de Água',
    })
    # plotar o gráfico de nivel de água

    fig = px.line(df, x=df.index, y='nivel_montante_grade', title='Nível de Água')
    st.plotly_chart(fig)
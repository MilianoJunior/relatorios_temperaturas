styles = '''
<style>
@media print {
    .page-break {
        page-break-before: always;
    }
    .page-break-after {
        page-break-after: always;
    }
    .no-break {
        page-break-inside: avoid;
    }
    
    /* Melhorias para impressão */
    body {
        font-size: 12pt;
        line-height: 1.4;
    }
    
    /* Melhorar parágrafos */
    p {
        margin-bottom: 1em;
        text-align: justify;
    }
    
    /* Melhorar listas */
    ul, ol {
        margin-bottom: 1em;
        padding-left: 2em;
    }
    
    li {
        margin-bottom: 0.5em;
    }
    
    /* Melhorar cabeçalhos */
    h1, h2, h3, h4, h5, h6 {
        page-break-after: avoid;
        margin-top: 1.5em;
        margin-bottom: 0.5em;
    }
    
    /* Melhorar tabelas */
    .dataframe {
        font-size: 10pt;
        border-collapse: collapse;
        margin: 1em 0;
    }
    
    .dataframe th, .dataframe td {
        border: 1px solid #ddd;
        padding: 4px;
    }
    
    /* Melhorar gráficos */
    .js-plotly-plot {
        page-break-inside: avoid;
        margin: 1em 0;
    }
}

/* Estilos para tela */
.intro-section {
    background-color: #f8f9fa;
    padding: 2rem;
    border-radius: 10px;
    margin-bottom: 2rem;
    border-left: 4px solid #007bff;
}

.intro-section h3 {
    color: #007bff;
    margin-bottom: 1rem;
}

.intro-section p {
    margin-bottom: 1rem;
    line-height: 1.6;
}

.intro-section ul {
    margin-bottom: 1rem;
    padding-left: 2rem;
}

.intro-section li {
    margin-bottom: 0.5rem;
}

.formula-section {
    background-color: #fff3cd;
    padding: 1.5rem;
    border-radius: 8px;
    margin: 1rem 0;
    border-left: 4px solid #ffc107;
}

.formula-section h4 {
    color: #856404;
    margin-bottom: 1rem;
}

.formula-section ul {
    margin-bottom: 0;
}

/* Estilos para o cabeçalho */
.header-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 0;
    border-bottom: 2px solid #007bff;
    margin-bottom: 2rem;
}

.header-logo {
    display: flex;
    align-items: center;
}

.header-title {
    text-align: center;
    flex-grow: 1;
    margin: 0 2rem;
}

.header-ai-logo {
    display: flex;
    align-items: center;
    justify-content: flex-end;
}

/* Estilos específicos para o cabeçalho Streamlit */
.header-col {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 20px;
}

.header-title-col {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    height: 50%;
}
</style>'''
import pandas as pd
import json
import time
import httpx 
from libs.configs import leituras
import copy
import random
import asyncio
# from datetime import datetime
from collections import defaultdict
from datetime import datetime
import traceback

# histórico compartilhado entre chamadas, como no seu código original
historico = defaultdict(dict)      # chave = "usina key - Enrolamento Fase A",   valor = { "12:20": 42.6, ... }


async def list_modbus_connections(config):
    """Lista todas as conexões Modbus ativas via API."""
    async with httpx.AsyncClient(verify=False, timeout=httpx.Timeout(5.0)) as client:
        try:
            response = await client.get(f"http://{config['ip']}:{config['port']}/listConnections")
            connections_data = response.json()
            if connections_data.get('status') != 'success':
                await close_modbus_connections(config)
                raise Exception(f"[ERRO API] {connections_data.get('message')}")
            return connections_data.get('data'), time.time()
        except Exception as e:
            await close_modbus_connections(config)
            raise Exception(f"[ERRO] {e}")
        
async def close_modbus_connections(config):
    """Fecha todas as conexões Modbus ativas via API."""
    async with httpx.AsyncClient(verify=False, timeout=httpx.Timeout(5.0)) as client:
        try:
            response = await client.post(f"http://{config['ip']}:{config['port']}/closeConnections")
            connections_data = response.json()
            if connections_data.get('status') != 'success':
                raise Exception(f"[ERRO API] {connections_data.get('message')}")
            return True
        except Exception as e:
            raise Exception(f"[ERRO] {e}")
        
def verify_all_connections():
    ''' Verifica se todas as conexões estão funcionando '''
    ips = {'APARECIDA':'100.110.212.125', 'FAE':'100.106.33.66','PICADAS':'100.79.241.13','PEDRAS':'100.93.237.40','HOPPEN':'100.73.37.105'}
    for key, value in ips.items():
        print(f"Verificando conexão: {key}")
        config = {'ip': value, 'port': 8010}
        data, timestamp = asyncio.run(list_modbus_connections(config))
        if len(data['active_connections']) != 0:
            asyncio.run(close_modbus_connections(config))
            print(f"Conexão {key} fechada")
        print(data)
        print(timestamp)
        print('-' * 50)
        time.sleep(5)

async def json_to_dataframe(json_data):
    data = dict(json_data)
    valores = {}
    for valor in data.values():
        for key, value in valor.items():
            valores[key] = value
    df = pd.DataFrame([valores])
    return df

def normalize_registers(registers_data):
    """
    Converte formato antigo (agrupado por tipo) para o formato da nova API.
    
    Formato antigo (opção 1 - agrupado simples):
        {"REAL": {"Nivel montante": 13353}, "INT": {"Potencia": 13407}}
    
    Formato antigo (opção 2 - agrupado com lista):
        {"REAL": {"Nivel montante": [13353, {"offset": -1}]}}
    
    Formato novo (API):
        {"Nivel montante": [13353, "REAL", {"offset": -1}], "Potencia": [13407, "INT", {"offset": -1}]}
    """
    if not isinstance(registers_data, dict):
        return registers_data
    
    # Verificar se precisa normalizar (tem chaves de tipo REAL, INT, BOOLEAN)
    has_type_keys = any(k in registers_data for k in ['REAL', 'INT', 'BOOLEAN'])
    
    # Se não tem chaves de tipo, já está no formato novo
    if not has_type_keys:
        return registers_data
    
    # Converter formato antigo para novo
    normalized = {}
    for tipo, registros in registers_data.items():
        if tipo in ['REAL', 'INT', 'BOOLEAN'] and isinstance(registros, dict):
            for nome, config in registros.items():
                # Caso 1: valor é uma lista completa [endereço, tipo, {opções}]
                if isinstance(config, list) and len(config) >= 3:
                    normalized[nome] = config
                
                # Caso 2: valor é uma lista [endereço, {opções}] sem o tipo
                elif isinstance(config, list) and len(config) == 2:
                    endereco, opcoes = config
                    if isinstance(opcoes, dict):
                        normalized[nome] = [endereco, tipo, opcoes]
                    else:
                        normalized[nome] = [endereco, tipo, {"offset": -1}]
                
                # Caso 3: valor é apenas o endereço (int)
                elif isinstance(config, int):
                    normalized[nome] = [config, tipo, {"offset": -1}]
                
                # Caso 4: valor é uma lista [endereço] sem opções
                elif isinstance(config, list) and len(config) == 1:
                    normalized[nome] = [config[0], tipo, {"offset": -1}]
                
                # Caso 5: outras estruturas, tenta extrair o endereço
                else:
                    # Tenta usar o valor diretamente
                    try:
                        endereco = int(config)
                        normalized[nome] = [endereco, tipo, {"offset": -1}]
                    except (ValueError, TypeError):
                        # Se não conseguir converter, mantém como está
                        print(f"⚠️  Aviso: formato não reconhecido para {nome}: {config}")
                        normalized[nome] = config
        else:
            # Se não é um tipo conhecido, ignora (não adiciona ao resultado)
            pass
    
    return normalized if normalized else registers_data

def generate_data(body):
    import random
    registers = body['registers'].copy()
    # Gerar valores None para todos os registros
    result = {}
    for key in registers.keys():
        result[key] = None
    return result

def validate_data(data):
    if isinstance(data, pd.DataFrame):
        return True
    return False

async def get_data(config, data):
    '''
    Lê dados do CLP via API Modbus TCP.
    
    Args:
        config: dict {ip: str, port: int, tipo: str}
        data: dict {conexao: dict, leituras: dict, temperaturas: dict, etc.}
    
    Returns:
        tuple: (dados_lidos, tempo_decorrido)
    '''
    inicio = time.time()
    
    # Normalizar registros do formato antigo para o novo
    registers_raw = data.get(config['tipo'], {})
    registers_normalized = normalize_registers(registers_raw)
    
    # Adicionar timeout à conexão se não estiver presente
    conexao = data['conexao'].copy()
    if 'timeout' not in conexao:
        conexao['timeout'] = 10.0
    
    body = {
        "conexao": conexao,
        "registers": registers_normalized
    }
    
    # Mapear tipo para rota da API
    tipo = config['tipo'] if config['tipo'] != 'temperaturas' else 'leituras'
    
    # Definindo timeout de 3 segundos para a requisição HTTP
    timeout = httpx.Timeout(3.0)
    url = f"http://{config['ip']}:{config['port']}/readCLP/{tipo}"
    
    async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
        try:
            response = await client.post(url, json=body)
            leituras_data = response.json()
            fim = time.time() - inicio
            
            if leituras_data.get('status') == 'success':
                return leituras_data.get('data', {}), fim
            else:
                return generate_data(body), fim
                
        except (httpx.TimeoutException, Exception) as e:
            # Log detalhado do erro (classe, mensagem, URL e chaves solicitadas)
            err_cls = e.__class__.__name__
            err_msg = str(e) if str(e) else repr(e)
            req_keys = list(body.get('registers', {}).keys())
            print(f"Erro na leitura: {err_cls}: {err_msg} | url={url} | tipo={tipo} | registers={req_keys}")
            fim = time.time() - inicio
            gerar_dados = generate_data(body)
            return gerar_dados, fim
        
def safe_float(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return float('-inf')

async def fetch_all_clp_data(select_type):
    usinas = leituras.keys()
    tasks = []
    clp_info = []
    for usina in usinas:
        config = {
            'ip': leituras[usina]['ip'],
            'port': leituras[usina]['port'],
            'table': leituras[usina]['table'],
            'tipo': select_type
        }
        data = leituras[usina]['CLPS']
        for key, value in data.items():
            tasks.append(get_data(config, value))
            clp_info.append((usina, key))
    results = await _gather_data(tasks)
    return clp_info, results

def enrich_clp_data(clp_info, results):
    """
    Processa dados recebidos da API e enriquece com metadados.
    
    A API retorna um dicionário simples: {"Potência Ativa": 1812, "Nivel montante": 404.12, ...}
    """
    response = []
    for (usina, key), (leitura, tempo) in zip(clp_info, results):
        # Verificar se a regra 'potência máxima' existe
        regras = leituras[usina]['CLPS'][key].get('regras', {})
        if not regras:
            regras = leituras[usina]['CLPS'][key].get('caracteristicas', {})
        potencia_maxima = regras.get('potência máxima', 0)
        
        # A nova API retorna diretamente {nome_variavel: valor}
        if isinstance(leitura, dict):
            for nome_var, valor in leitura.items():
                response.append({
                    'title': f'{usina} {key}',
                    'key': nome_var,
                    'value': valor,
                    'tipo': 'kW' if 'Potência' in nome_var or 'Potencia' in nome_var else '',
                    'potencia_maxima': potencia_maxima,
                    'tempo': tempo
                })
    
    return response

def filter_and_sort(data, key_name):
    filtered = [line for line in data if line['key'] == key_name]
    sorted_data = sorted(
        filtered,
        key=lambda x: (x['value'] is None, safe_float(x['value'])),
        reverse=True
    )
    return sorted_data

async def get_current_values(select_type):
    """
    Busca e organiza os valores atuais de todos os CLPs de todas as usinas.
    """
    clp_info, results = await fetch_all_clp_data(select_type)
    response = enrich_clp_data(clp_info, results)
    potencias = filter_and_sort(response, 'Potência Ativa')
    # temperaturas = filter_and_sort(response, 'Temperatura')
    return response

async def _gather_data(tasks):
    return await asyncio.gather(*tasks) 

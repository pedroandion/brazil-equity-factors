"""Functions that collect data from the Comdinheiro API. A licensed account is required."""
import json
import os
from datetime import date

import numpy as np
import pandas as pd
import requests

# Credentials are read from the environment and are never stored in the code
credentials = "username={0}&password={1}".format(os.environ.get('COMDINHEIRO_USERNAME', ''), os.environ.get('COMDINHEIRO_PASSWORD', ''))


# The stock screener function returns all companies that meet the pre-selected criteria on the requested date

def get_index_composition(dt: date, index) -> pd.DataFrame:    
    # url and payload for the request
    url = "https://www.comdinheiro.com.br/Clientes/API/EndPoint001.php"

    querystring = {"code":"import_data"}

    payload = credentials + "&URL=ComposicaoIndices001.php%3F%26data_analise%3D{0}%26indice%3D{1}%26nome_portfolio%3D%26tipo_portfolio%3Dquantidade%26overwrite%3D0%26design%3D2%26obs_portfolio%3D%26num_casas%3D0%26salvar_dados%3Dnenhum%26sufixo%3D%26nome_serie%3D%26filtro_avancado%3D&format=json3".format(dt.strftime('%d%m%Y'), index)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = requests.request("POST", url, data=payload, headers=headers, params=querystring)

    # Converts the api response to json
    data = json.loads(response.text)
    # Goes through the json keys until reaching the table with the companies' information
    data = data['tables']['tab0']

    # Converts the json to a dataframe, with the lin0 key used as index
    index_comp = pd.DataFrame(data).set_index('lin0')

    # Replaces empty values with NaN and removes the rows containing NaN, also transposes the dataframe
    index_comp = index_comp.replace('', np.nan).dropna().T

    # Converts the vendor's weight column to float and divides by 100 to get a percentage
    index_comp['Participação'] = pd.to_numeric(index_comp['Participação'].str.replace(',','.')) / 100

    # Resets the index
    index_comp = index_comp.reset_index(drop = True)

    # Adds the date to the dataframe
    index_comp['Date'] = dt

    # Renames the vendor's column to English
    index_comp = index_comp.rename(columns = {'Participação': 'Weight'})

    return index_comp

def get_sectors(tickers_str):
    url = "https://www.comdinheiro.com.br/Clientes/API/EndPoint001.php"

    querystring = {"code":"import_data"}

    payload = credentials + "&URL=ComparaEmpresas001.php%3F%26data_d%3D31129999%26data_a%3D21%2F06%2F2024%26trailing%3D12%26conv%3DMIXED%26c_c%3Dconsolidado%2520preferencialmente%26moeda%3DMOEDA_ORIGINAL%26m_m%3D1000000000%26n_c%3D2%26f_v%3D0%26papeis%3D{}%26indic%3DSETOR%26enviar_email%3D0%26enviar_email_log%3D0%26transpor%3D0%26op01%3Dtabela%26oculta_cabecalho_sup%3D0%26relat_alias_automatico%3Dcmd_alias_01%26script%3D&format=json3".format(tickers_str)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = requests.request("POST", url, data=payload, headers=headers, params=querystring)

    data = json.loads(response.text)

    data = data['tables']['tab0']

    sectors = pd.DataFrame(data).set_index('lin0').T.reset_index(drop = True).rename(columns = {'Setor': 'Sector'})

    return sectors

def filter_indexes_comp(indexes: pd.DataFrame, tickers_str: str) -> pd.DataFrame:
    '''Adds the sector and the ticker without the exchange code to the composition of the indices.'''

    # Creates a dataframe with the companies' sectors
    sectors = get_sectors(tickers_str)

    # Standardizes the date format
    indexes['Date'] = pd.to_datetime(indexes['Date'], format = '%Y-%m-%d')

    # Adds the sector to the dataframe
    indexes = pd.merge(indexes, sectors, left_on = 'Ticker', right_on = 'Empresas', how = 'left').drop('Empresas', axis = 1)

    # Adds the column with the stock's Ticker without the exchange code
    indexes['Company'] = indexes['Ticker'].str[0:4]

    return indexes

def get_benchmarks(dt_start, dt_end)-> pd.DataFrame:
    '''The API does not return the dataframe starting at dt_start, the previous day must be passed to get the dataframe from dt_start onwards.
    Data for d0 may come empty, so it is also recommended to use d-1 as the end date to make sure the data is complete.'''
    
    # Url and payload for the request
    url = "https://www.comdinheiro.com.br/Clientes/API/EndPoint001.php"

    querystring = {"code":"import_data"}

    payload = credentials + "&URL=HistoricoCotacao002.php%3F%26x%3DCDI%2BSELIC%2BANBIMA_IMAB%2BANBIMA_IMAB5%2BANBIMA_IRFM%2BPTAXV%2BIBOV%2BIBRX%2BMLCX%2BSMLL%2BIFIX%2BBOVA11%2BIVVB11%2BGOLD11%26data_ini%3D{0}%26data_fim%3D{1}%26pagina%3D1%26d%3DMOEDA_ORIGINAL%26g%3D0%26m%3D0%26info_desejada%3Dretorno%26retorno%3Ddiscreto%26tipo_data%3Ddu_br%26tipo_ajuste%3Dtodosajustes%26num_casas%3D2%26enviar_email%3D0%26ordem_legenda%3D1%26cabecalho_excel%3Dmodo1%26classes_ativos%3Dz1ci99jj7473%26ordem_data%3D1%26rent_acum%3Drent_acum%26minY%3D%26maxY%3D%26deltaY%3D%26preco_nd_ant%3D0%26base_num_indice%3D100%26flag_num_indice%3D0%26eixo_x%3DData%26startX%3D0%26max_list_size%3D20%26line_width%3D2%26titulo_grafico%3D%26legenda_eixoy%3D%26tipo_grafico%3Dline%26script%3D%26tooltip%3Dunica&format=json3".format(dt_start.strftime('%d%m%Y'), dt_end.strftime('%d%m%Y'))
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = requests.request("POST", url, data=payload, headers=headers, params=querystring)

    # Converts the api response to json
    data = json.loads(response.text)
    # Goes through the json keys until reaching the table with the companies' information
    data = data['tables']['tab1']

    # Converts the json to a dataframe
    benchmarks = pd.DataFrame(data).set_index('lin0').T
    benchmarks = benchmarks.reset_index(drop = True)

    benchmarks = benchmarks.drop(0).reset_index(drop = True)

    # Converts null values to np.nan
    benchmarks = benchmarks.replace('nd', np.nan)
    benchmarks = benchmarks.replace(',', '.', regex = True)

    # Converts the Data column from text to date and the values from str to float
    benchmarks['Data'] = pd.to_datetime(benchmarks['Data'], format = 'mixed', dayfirst = True)
    benchmarks[benchmarks.columns[1:]] = benchmarks[benchmarks.columns[1:]].astype(float)
    benchmarks = benchmarks.set_index('Data').rename_axis('Date')

    return benchmarks

def get_prices(tickers_str, dt_start, dt_end):
    '''The API does not return the dataframe starting at dt_start, the previous day must be passed to get the dataframe from dt_start onwards.
    Data for d0 may come empty, so it is also recommended to use d-1 as the end date to make sure the data is complete.'''
    
    # Url and payload for the request
    url = "https://www.comdinheiro.com.br/Clientes/API/EndPoint001.php"

    querystring = {"code":"import_data"}

    payload = credentials + "&URL=HistoricoCotacao002.php%3F%26x%3D{0}%26data_ini%3D{1}%26data_fim%3D{2}%26pagina%3D1%26d%3DMOEDA_ORIGINAL%26g%3D0%26m%3D0%26info_desejada%3Dpreco%26retorno%3Ddiscreto%26tipo_data%3Ddu_br%26tipo_ajuste%3Dtodosajustes%26num_casas%3D4%26enviar_email%3D0%26ordem_legenda%3D1%26cabecalho_excel%3Dmodo1%26classes_ativos%3Dhio94mrrlk3j%26ordem_data%3D0%26rent_acum%3Drent_acum%26minY%3D%26maxY%3D%26deltaY%3D%26preco_nd_ant%3D0%26base_num_indice%3D100%26flag_num_indice%3D0%26eixo_x%3DData%26startX%3D0%26max_list_size%3D20%26line_width%3D2%26titulo_grafico%3D%26legenda_eixoy%3D%26tipo_grafico%3Dline%26script%3D%26tooltip%3Dunica&format=json3".format(tickers_str, dt_start.strftime('%d%m%Y'), dt_end.strftime('%d%m%Y'))
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = requests.request("POST", url, data=payload, headers=headers, params=querystring)

    # Converts the api response to json
    data = json.loads(response.text)
    # Goes through the json keys until reaching the table with the companies' information
    data = data['tables']['tab1']

    # Converts the json to a dataframe
    prices_df = pd.DataFrame(data).T
    prices_df = prices_df.reset_index(drop = True)

    # Makes the first row of the dataframe the header
    prices_df.columns = prices_df.iloc[0]
    prices_df = prices_df.drop(0)

    # Converts null values to np.nan
    prices_df = prices_df.replace('nd', np.nan)
    prices_df = prices_df.replace(',', '.', regex = True)

    # Converts the Data column from text to date and the values from str to float
    prices_df['Data'] = pd.to_datetime(prices_df['Data'], dayfirst = True, format='mixed')
    prices_df[prices_df.columns[1:]] = prices_df[prices_df.columns[1:]].astype(float)
    prices_df = prices_df.set_index('Data').rename_axis('Date')

    return prices_df

def get_market_value(tickers_str, dt_start, dt_end):
    # Url and payload for the request
    url = "https://www.comdinheiro.com.br/Clientes/API/EndPoint001.php"

    querystring = {"code":"import_data"}

    payload = credentials + "&URL=HistoricoIndicadoresFundamentalistas001.php%3F%26data_ini%3D{1}%26data_fim%3D{2}%26trailing%3D12%26conv%3DMIXED%26moeda%3DMOEDA_ORIGINAL%26c_c%3Dconsolidado%26m_m%3D1000%26n_c%3D2%26f_v%3D0%26papel%3D{0}%26indic%3DMARKET_VALUE%26periodicidade%3Ddu%26graf_tab%3Dtabela%26desloc_data_analise%3D1%26flag_transpor%3D0%26c_d%3Dc%26enviar_email%3D0%26enviar_email_log%3D0%26cabecalho_excel%3Dmodo2%26relat_alias_automatico%3Dcmd_alias_01&format=json3".format(tickers_str, dt_start.strftime('%d%m%Y'), dt_end.strftime('%d%m%Y'))
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = requests.request("POST", url, data=payload, headers=headers, params=querystring)

    # Converts the api response to json
    data = json.loads(response.text)
    # Goes through the json keys until reaching the table with the companies' information
    data = data['tables']['tab0']

    # Converts the json to a dataframe
    market_value = pd.DataFrame(data).set_index('lin0').T.reset_index(drop = True)
    
    # Converts null values to np.nan
    market_value = market_value.replace(',', '.', regex=True).replace('', np.nan, regex=True)

    # Converts the Data column from text to date and the values from str to float
    market_value.loc[:, ~market_value.columns.str.contains('Data')] = market_value.loc[:, ~market_value.columns.str.contains('Data')].astype(float)
    market_value['Data'] = pd.to_datetime(market_value['Data'], dayfirst = True, format = 'mixed')
    market_value = market_value.set_index('Data').rename_axis('Date')

    return market_value

def get_volume(tickers_str, dt_start, dt_end):
    # Url and payload for the request
    url = "https://www.comdinheiro.com.br/Clientes/API/EndPoint001.php"

    querystring = {"code":"import_data"}

    payload = credentials + "&URL=HistoricoIndicadoresFundamentalistas001.php%3F%26data_ini%3D{1}%26data_fim%3D{2}%26trailing%3D12%26conv%3DMIXED%26moeda%3DMOEDA_ORIGINAL%26c_c%3Dconsolidado%26m_m%3D1000%26n_c%3D2%26f_v%3D0%26papel%3D{0}%26indic%3DVOLUME_DIA%26periodicidade%3Ddu%26graf_tab%3Dtabela%26desloc_data_analise%3D1%26flag_transpor%3D0%26c_d%3Dc%26enviar_email%3D0%26enviar_email_log%3D0%26cabecalho_excel%3Dmodo2%26relat_alias_automatico%3Dcmd_alias_01&format=json3".format(tickers_str, dt_start.strftime('%d%m%Y'), dt_end.strftime('%d%m%Y'))
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = requests.request("POST", url, data=payload, headers=headers, params=querystring)

    # Converts the api response to json
    data = json.loads(response.text)
    # Goes through the json keys until reaching the table with the companies' information
    data = data['tables']['tab0']

    # Converts the json to a dataframe
    volume = pd.DataFrame(data).set_index('lin0').T.reset_index(drop = True)
    
    # Converts null values to np.nan
    volume = volume.replace(',', '.', regex=True).replace('', np.nan, regex=True)

    # Converts the Data column from text to date and the values from str to float
    volume.loc[:, ~volume.columns.str.contains('Data')] = volume.loc[:, ~volume.columns.str.contains('Data')].astype(float)
    volume['Data'] = pd.to_datetime(volume['Data'], dayfirst = True, format = 'mixed')
    volume = volume.set_index('Data').rename_axis('Date')

    return volume

def get_financial_statements(dt_analysis, dt_ref, tickers_str):

    # Url and payload for the request
    url = "https://www.comdinheiro.com.br/Clientes/API/EndPoint001.php"

    querystring = {"code":"import_data"}

    payload = credentials + f"&URL=StockScreenerFull.php%3F%26relat%3D%26data_analise%3D{dt_analysis.day:02d}%2F{dt_analysis.month:02d}%2F{dt_analysis.year}%26data_dem%3D{dt_ref.day:02d}%2F{dt_ref.month:02d}%2F{dt_ref.year}%26variaveis%3DTICKER%2BDATA_DEMONSTRACAO%2BDATA_PUBLICACAO%2BAT%2BAC%2BDISPONIBILIDADES%2BCONTAS_A_RECEBER%2BESTOQUES%2BTRIB_RECUPERAR%2BOUTROS_AC%2BANC%2BRLP%2BINVESTIMENTOS%2BIMOBILIZADO%2BINTANGIVEL%2BPC%2BFORNECEDORES_CP%2BEMP_FIN_CP%2BOBR_SOCIAIS_TRAB%2BDIVIDENDOS_E_JUROS_A_PAGAR%2BOBR_FISCAIS%2BPNC%2BFORNECEDORES_LP%2BEMP_FIN_LP%2BPL%2BRL%2BLUB%2BEBIT%2BEBITDA%2BRESULTADO_ANTES_TRIB%2BLL%2BDEPRE_AMOR%2BFCO%2BFCI%2BFCF%2BDFC_VARIACAO_CAIXA_EQUIVALENTES%26segmento%3Dtodos%26setor%3Dtodos%26filtro%3Dticker%2Blike%2B{tickers_str.replace('%2B', '%7C')}%26demonstracao%3Dconsolidado%2520preferencialmente%26convencao%3DMIXED%26acumular%3D3%26valores_em%3D1000%26num_casas%3D0%26salve%3D%26salve_obs%3D%26opcao_salvar%3Dnenhum%26opcao_portfolio%3Dquantidade%26opcao_serie%3Dcash%26indicador_pesos_portfolio%3D%26data_analise_portfolio%3D14%2F04%2F2025%26var_control%3D0%26overwrite%3D0%26setor_bov%3Dtodos%26subsetor_bov%3Dtodos%26subsubsetor_bov%3Dtodos%26group_by%3D%26relat_alias_automatico%3Dcmd_alias_01%26primeira_coluna_ticker%3D0%26periodos%3D0%26periodicidade%3Danual_02%26formato_data%3D1%26tipo_on_pn%3Dtodos%26tipo_listagem%3Dlistada_em_bolsa%26casos_especiais_01%3D%26casos_especiais_02%3D%26pais_origem%3DBR%26exchange%3DB3%26limit_01%3D%26order_by%3DTICKER%26moeda%3DMOEDA_ORIGINAL%26nome_serie%3D%26republicacoes%3D1%26linppag%3D50&format=json3"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = requests.request("POST", url, data=payload, headers=headers, params=querystring)

    # Converts the api response to json
    data = json.loads(response.text)

    # Converts the json to a dataframe
    df = pd.DataFrame(data['tables']['tab0']).T

    # Makes the first row of the dataframe the header, removes it and resets the index
    df.columns = df.iloc[0]
    df = df.drop(df.index[0])

    # Removes unnecessary text from the header
    df.columns = df.columns.str.replace('\n Milhares\n', '')
    df.columns = df.columns.str.replace('\n3 meses', '')

    # Null values come as [] and are converted to np.nan
    df = df.map(lambda x: np.nan if isinstance(x, list) and not x else x)
    df = df.replace([''], np.nan)

    # Replaces commas with dots to convert the values to float
    # Replaces the date 31/12/9999 with np.nan
    df = df.replace(',', '.', regex=True).replace('31/12/9999', np.nan).replace('9999-12-31', np.nan)

    # Converts numeric values to float and dates to datetime.date
    for col in [col for col in df.columns if 'DATA' not in col and 'Data' not in col]:
        if col == 'TICKER':
            pass
        else:
            df[col] = df[col].astype(float)
    for col in [col for col in df.columns if 'DATA' in col or 'Data' in col]:
        df[col] = pd.to_datetime(df[col], dayfirst=True, format = 'mixed').dt.date

    return df

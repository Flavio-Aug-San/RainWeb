import streamlit as st
import pandas as pd
import geopandas as gpd
import requests
import numpy as np
from datetime import datetime, timedelta
import leafmap.foliumap as leafmap
import folium
import glob
import calendar
from io import StringIO
import matplotlib.pyplot as plt
from folium.plugins import MarkerCluster

# URLs e caminhos de arquivos
shp_mg_url = 'https://github.com/giuliano-macedo/geodata-br-states/raw/main/geojson/br_states/br_mg.json'
csv_file_path = 'input;/filtered_data.csv'
dadosoff = 'input;/estacoes_suldeminas.csv'

# Login e senha do CEMADEN (previamente fornecidos)
login = 'augustoflaviobob@gmail.com'
senha = 'Flaviobr123!'

# Carregar os dados do shapefile de Minas Gerais
mg_gdf = gpd.read_file(shp_mg_url)

# Estações Selecionadas do Sul de Minas Gerais
codigo_estacao = ['314790701A','310710901A','312870901A','315180001A','316930702A','314780801A','315250101A','313240401A','313360001A','311410501A','311360201A','313300601A']

# Lê o arquivo XLS em um DataFrame
dfoff = pd.read_csv(dadosoff,delimiter =';')

# Carregar os dados das estações
df1 = pd.read_csv(csv_file_path)
gdf = gpd.GeoDataFrame(df1, geometry=gpd.points_from_xy(df1['longitude'], df1['latitude']))

# Realizar o filtro espacial: apenas estações dentro de Minas Gerais
gdf_mg = gpd.sjoin(gdf, mg_gdf, predicate='within')

# Recuperação do token
#token_url = 'http://sgaa.cemaden.gov.br/SGAA/rest/controle-token/tokens'
#login_payload = {'email': login, 'password': senha}
#response = requests.post(token_url, json=login_payload)
#content = response.json()
#token = content['token']

# sigla do estado do Brasil
sigla_estado = 'MG'

# Criar as variáveis de data inicial e final
data_final = pd.to_datetime("01/02/2024", format="%d/%m/%Y")
data_inicial = pd.to_datetime("29/02/2024", format="%d/%m/%Y")
# Data de hoje
#agora = datetime.now()

# Dia, mês e ano de hoje
#dia_atual = agora.day
#mes_atual = agora.month
#ano_atual = agora.year

# Calcula o mês e ano anteriores para a data inicial
#if mes_atual == 1:
   # mes_anterior = 12
   # ano_anterior = ano_atual - 1
#else:
  #  mes_anterior = mes_atual - 1
  #  ano_anterior = ano_atual
  #  mes_pos = mes_atual + 1

# Formata as datas
#diai = '01'
#data_inicial = f'{ano_atual}{mes_anterior:02d}{diai}'
#data_final = f'{ano_atual}{mes_atual:02d}{dia_atual:02d}'
#data_inicial = pd.to_datetime(data_inicial)
#data_final = pd.to_datetime(data_final)

# Converter a coluna 'datahora' para datetime, ignorando milissegundos
dfoff['datahora'] = pd.to_datetime(dfoff['datahora'], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')

# Definir 'datahora' como índice
dfoff.set_index('datahora', inplace=True)

#def baixar_dados_estacoes(codigo_estacao, data_inicial, data_final, sigla_estado):
    # Lista para armazenar os dados de todas as estações
    #dados_estacoes = {}

    #for codigo in codigo_estacao:
        # Lista para armazenar os dados de cada mês de uma estação
        #dados_completos = []

        #for ano_mes_dia in pd.date_range(data_inicial, data_final, freq='M'):
            #ano_mes = ano_mes_dia.strftime('%Y%m')  # Formato '202401'

            # URL e parâmetros da requisição
            #sws_url = 'http://sws.cemaden.gov.br/PED/rest/pcds/dados_pcd'
            #params = dict(
                #rede=11, uf=sigla_estado, inicio=ano_mes, fim=ano_mes, codigo=codigo
            #)

            # Requisição dos dados
            #r = requests.get(sws_url, params=params, headers={'token': token})
            #dados = r.text

            # Remover a linha de comentário e converter para DataFrame
            #linhas = dados.split("\n")
            #dados_filtrados = "\n".join(linhas[1:])  # Remove a primeira linha (comentário)

            #df = pd.read_csv(StringIO(dados_filtrados), sep=";")

            # Armazena os dados no acumulado
            #dados_completos.append(df)

        # Combina os dados de todos os meses para a estação
        #if dados_completos:
            #dados_estacoes[codigo] = pd.concat(dados_completos)

    #return dados_estacoes

# Função para exibir gráficos de precipitação
def mostrar_graficos(codigo_estacao, data_inicial):
    # Garantir que data_inicial é um objeto datetime
    if not isinstance(data_inicial, datetime):
        data_inicial = pd.to_datetime(data_inicial)

    # Filtrar o DataFrame dfoff para a estação selecionada
    dados_estacao = dfoff[dfoff['codEstacao'] == codigo_estacao]

    # Verificar se há dados para a estação
    if dados_estacao.empty:
        st.error(f"Estação {codigo_estacao} não encontrada ou sem dados.")
        return

    # Garantir que a coluna 'datahora' é datetime e está como índice
    if not isinstance(dados_estacao.index, pd.DatetimeIndex):
        dados_estacao['datahora'] = pd.to_datetime(dados_estacao['datahora'], errors='coerce')
        dados_estacao.set_index('datahora', inplace=True)

    # ======================== Cálculos de Precipitação ========================
    inicio_dia_atual = data_inicial.replace(hour=0, minute=0, second=0, microsecond=0)
    inicio_24h = data_inicial - timedelta(hours=24)
    inicio_48h = data_inicial - timedelta(hours=48)

    soma_dia_atual = dados_estacao.loc[dados_estacao.index >= inicio_dia_atual, 'valorMedida'].sum()
    soma_24h = dados_estacao.loc[dados_estacao.index >= inicio_24h, 'valorMedida'].sum()
    soma_48h = dados_estacao.loc[dados_estacao.index >= inicio_48h, 'valorMedida'].sum()

    # ======================== Gráfico de Barras ========================
    # Preparar os dados para o gráfico
    horas = ['Dia Atual', 'Últimas 24 Horas', 'Últimas 48 Horas']
    chuva_valores = [soma_dia_atual, soma_24h, soma_48h]

    # Criar o gráfico de barras
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(horas, chuva_valores, color=['blue', 'orange', 'green'])
    ax.set_ylabel('Precipitação (mm)')
    ax.set_title(f'Precipitação - Estação {codigo_estacao}')

    # ======================== Gráfico de Curva Mensal ========================
    # Plotar a curva de precipitação ao longo do mês
    fig_mensal, ax_mensal = plt.subplots(figsize=(20, 10))
    ax_mensal.plot(dados_estacao.index, dados_estacao['valorMedida'], marker='o', linestyle='-', color='blue')
    ax_mensal.set_title(f'Curva Mensal de Precipitação - Estação {codigo_estacao}')
    ax_mensal.set_ylabel('Precipitação (mm)')
    ax_mensal.set_xlabel('Data')
    ax_mensal.grid(True)

    # ======================== Exibir os Gráficos ========================
    col1, col2 = st.columns(2)  # Dividir a tela em duas colunas

    with col1:
        st.pyplot(fig)  # Exibe o gráfico de barras na primeira coluna

    with col2:
        st.pyplot(fig_mensal)  # Exibe o gráfico da curva mensal na segunda coluna
    
m = leafmap.Map(center=[-21, -45],zoom_start = 8,draw_control=False, measure_control=False, fullscreen_control=False, attribution_control=True)

# Defina o layout da página como largo
st.set_page_config(layout="wide")

# Baixar dados da estação
#dados1 = baixar_dados_estacoes(codigo_estacao, data_inicial, data_final, sigla_estado)

# Remover chave se o valor for vazio (DataFrame vazio)
#for codigo in list(dados1.keys()):
    #valor = dados1[codigo]

    #if isinstance(valor, pd.DataFrame) and valor.empty:
       # del dados1[codigo]  # Remove a chave se for um DataFrame vazio
#dados2 = {}
#for codigo in dados1.keys():
 # df = dados1[codigo][dados1[codigo]['sensor'] != 'intensidade_precipitacao']
 # df['datahora'] = pd.to_datetime(df['datahora'])
 # df = df.set_index('datahora')
 # dados2[codigo] = df

# Criação do dicionário para armazenar os resultados
#somas_por_estacao = {}

# Data/hora atual para referência
#agora = datetime.now()

# Iterar sobre os dataframes em dados2
#for codigo_estacao, df in dados2.items():
#    # Garantir que o index esteja no formato datetime
#    df.index = pd.to_datetime(df.index)
    
    # Filtrar os dados para o dia atual, últimas 24 horas e últimas 48 horas
#    inicio_dia_atual = agora.replace(hour=0, minute=0, second=0, microsecond=0)
#    inicio_24h = agora - timedelta(hours=24)
#    inicio_48h = agora - timedelta(hours=48)
    
#    soma_dia_atual = df.loc[df.index >= inicio_dia_atual, 'valor'].sum()
#    soma_24h = df.loc[df.index >= inicio_24h, 'valor'].sum()
#    soma_48h = df.loc[df.index >= inicio_48h, 'valor'].sum()
    
    # Armazenar os resultados em somas_por_estacao
#    somas_por_estacao[codigo_estacao] = {
#        "dia_atual": soma_dia_atual,
#        "ultimas_24h": soma_24h,
#        "ultimas_48h": soma_48h
   # }

# Criar uma lista para armazenar os resultados
resultados_precipitacao = []

# Iterar por cada estação
for estacao, grupo in dfoff.groupby('codEstacao'):
    grupo = grupo.sort_index()  # Garantir que os dados estão ordenados por data e hora
    
    # Calcular somas para cada momento no DataFrame
    for timestamp in grupo.index:
        ultima_hora = grupo.loc[(grupo.index > timestamp - timedelta(hours=1)) & (grupo.index <= timestamp), 'valorMedida'].sum()
        ultimas_24h = grupo.loc[(grupo.index > timestamp - timedelta(hours=24)) & (grupo.index <= timestamp), 'valorMedida'].sum()
        ultimas_48h = grupo.loc[(grupo.index > timestamp - timedelta(hours=48)) & (grupo.index <= timestamp), 'valorMedida'].sum()

        # Armazenar os resultados em uma lista
        resultados_precipitacao.append({
            "codEstacao": estacao,
            "timestamp": timestamp,
            "ultima_hora": ultima_hora,
            "ultimas_24h": ultimas_24h,
            "ultimas_48h": ultimas_48h
        })

# Transformar os resultados em um DataFrame
df_resultados = pd.DataFrame(resultados_precipitacao)

# Adicionar marcadores das estações meteorológicas
for i, row in gdf_mg.iterrows():
    # Filtrar os dados para a estação atual
    dados_estacao = dfoff[dfoff['codEstacao'] == row['codEstacao']]

    # Calcular as somas dinâmicas para a data_inicial
    if not dados_estacao.empty:
        inicio_ultima_hora = data_inicial - timedelta(hours=1)
        inicio_24h = data_inicial - timedelta(hours=24)
        inicio_48h = data_inicial - timedelta(hours=48)

        # Filtrar os dados para os períodos correspondentes
        soma_ultima_hora = dados_estacao.loc[dados_estacao.index >= inicio_ultima_hora, 'valorMedida'].sum()
        soma_24h = dados_estacao.loc[dados_estacao.index >= inicio_24h, 'valorMedida'].sum()
        soma_48h = dados_estacao.loc[dados_estacao.index >= inicio_48h, 'valorMedida'].sum()

        # Criar o popup com HTML para melhor formatação
        popup_text = f"""
        <b>Município:</b> {row['municipio']} <br>
        <b>Código:</b> {row['codEstacao']} <br>
        <b>Última Hora:</b> {soma_ultima_hora:.2f} mm <br>
        <b>Últimas 24 Horas:</b> {soma_24h:.2f} mm <br>
        <b>Últimas 48 Horas:</b> {soma_48h:.2f} mm <br>
        """
    else:
        popup_text = f"<b>{row['municipio']} (Código: {row['codEstacao']})</b> - Sem Dados de Precipitação"

    # Adicionar marcador com valor
    folium.RegularPolygonMarker(
        location=[row['latitude'], row['longitude']],
        color='black',
        opacity=1,
        weight=1,
        fillColor='green',
        fillOpacity=1,
        numberOfSides=4,
        rotation=45,
        radius=8,
        popup=folium.Popup(popup_text, max_width=300)  # Usando HTML no popup
    ).add_to(m)

# Adicionar camada do município em Minas Gerais
m.add_gdf(
    mg_gdf, 
    layer_name="Minas Gerais", 
    style={"color": "black", "weight": 1, "fillOpacity": 0, "interactive": False},
    info_mode=None
)

st.sidebar.header("Filtros de Seleção")
modo_selecao = st.sidebar.radio("Selecionar Estação por:", ('Código'))

# Seleção da estação
if modo_selecao == 'Código':
    estacao_selecionada = st.sidebar.selectbox("Selecione a Estação", gdf_mg['codEstacao'].unique())
    # Certifique-se de que o código da estação é extraído corretamente
    codigo_estacao = gdf_mg[gdf_mg['codEstacao'] == estacao_selecionada]['codEstacao'].values[0]

# Adicionar um controle para "Recarregar Dados" quando a data for alterada
tipo_busca = st.sidebar.radio("Tipo de Busca:", ('Diária'))

if tipo_busca == 'Diária':
    data_inicial = st.sidebar.date_input("Data", value=data_inicial)
else:
    ano_selecionado = st.sidebar.selectbox("Selecione o Ano", range(2020, datetime.now().year + 1))
    mes_selecionado = st.sidebar.selectbox("Selecione o Mês", range(1, 13))
    data_inicial = datetime(ano_selecionado, mes_selecionado, 1)
    data_final = datetime(ano_selecionado, mes_selecionado + 1, 1) - timedelta(days=1) if mes_selecionado != 12 else datetime(ano_selecionado, 12, 31)

# Adicionar um controle de flag para verificar se os dados precisam ser recarregados
data_inicial_str = data_inicial.strftime('%Y%m%d')
data_final_str = data_final.strftime('%Y%m%d')

# Verificar se os dados já estão carregados
#if 'dados_baixados' not in st.session_state or st.session_state.data_inicial != data_inicial_str or st.session_state.data_final != data_final_str:
    # Se os dados não estão carregados ou a data foi alterada, atualize os dados
    #st.session_state.dados_baixados = baixar_dados_estacoes(codigo_estacao, data_inicial, data_final, sigla_estado)
    #st.session_state.data_inicial = data_inicial_str
    #st.session_state.data_final = data_final_str

# Exibir os dados baixados
#dados_baixados = st.session_state.dados_baixados

#if dados_baixados:
    #st.subheader(f"Dados da Estação: {estacao_selecionada} (Código: {codigo_estacao})")
    #st.write(dados_baixados)
#else:
    #st.warning("Nenhum dado encontrado para o período selecionado.")

if st.sidebar.button("Baixar Dados"):
    data_inicial_str = data_inicial.strftime('%Y%m%d')
    data_final_str = data_final.strftime('%Y%m%d')
    dados_baixados = dados['codEstacao']
    if not dados_estacao.empty:
        st.subheader(f"Dados da Estação: {estacao_selecionada} (Código: {codigo_estacao})")
        st.write(dados_baixados)
    else:
        st.warning("Nenhum dado encontrado para o período selecionado.")

# Checkbox na barra lateral para alternar exibição do gráfico
mostrar = st.sidebar.checkbox("Gráfico de Precipitação")

# Exibir ou ocultar o gráfico conforme o estado do checkbox
if mostrar:
    # Exibir o gráfico para a estação selecionada
    mostrar_graficos(estacao_selecionada, data_inicial)
# Mostrar o mapa em Streamlit
m.to_streamlit(width=1300,height=775)
#st.write(somas_por_estacao)
#st.write(dados2)

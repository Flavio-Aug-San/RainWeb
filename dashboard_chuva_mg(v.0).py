import streamlit as st
import pandas as pd
import geopandas as gpd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import requests
from io import StringIO
import folium
from folium.plugins import MarkerCluster
import leafmap.foliumap as leafmap

# Login e senha do CEMADEN (previamente fornecidos)
login = 'augustoflaviobob@gmail.com'
senha = 'Flaviobr123!'

# Recuperação do token
token_url = 'http://sgaa.cemaden.gov.br/SGAA/rest/controle-token/tokens'
login_payload = {'email': login, 'password': senha}
response = requests.post(token_url, json=login_payload)
content = response.json()
token = content['token']

# sigla do estado do Brasil
sigla_estado = 'MG'

# Configuração inicial
st.set_page_config(layout="wide")
st.sidebar.header("Filtros de Seleção")

# URLs e variáveis fixas
shp_mg_url = 'https://github.com/giuliano-macedo/geodata-br-states/raw/main/geojson/br_states/br_mg.json'
csv_file_path = 'input;/filtered_data.csv'

# Inicializar session state
if "dados2" not in st.session_state:
    st.session_state.dados2 = {}
if "somas_por_estacao" not in st.session_state:
    st.session_state.somas_por_estacao = {}
if "range_dados" not in st.session_state:
    st.session_state.range_dados = {"inicio": None, "fim": None}

# Função para baixar os dados
def baixar_dados_estacoes(codigo_estacao, data_inicial, data_final, token, sigla_estado):
    dados_estacoes = {}
    for codigo in codigo_estacao:
        dados_completos = []
        for ano_mes_dia in pd.date_range(data_inicial, data_final, freq='M'):
            ano_mes = ano_mes_dia.strftime('%Y%m')
            sws_url = 'http://sws.cemaden.gov.br/PED/rest/pcds/dados_pcd'
            params = {"rede": 11, "uf": sigla_estado, "inicio": ano_mes, "fim": ano_mes, "codigo": codigo}
            r = requests.get(sws_url, params=params, headers={'token': token})
            dados = r.text.split("\n")[1:]
            df = pd.read_csv(StringIO("\n".join(dados)), sep=";")
            dados_completos.append(df)
        if dados_completos:
            dados_estacoes[codigo] = pd.concat(dados_completos)
    return dados_estacoes

# Função para calcular as somas
def calcular_somas(dados2):
    somas = {}
    agora = datetime.now()
    for codigo, df in dados2.items():
        df.index = pd.to_datetime(df.index)
        inicio_dia = agora.replace(hour=0, minute=0, second=0, microsecond=0)
        inicio_24h = agora - timedelta(hours=24)
        inicio_48h = agora - timedelta(hours=48)
        somas[codigo] = {
            "dia_atual": df.loc[df.index >= inicio_dia, 'valor'].sum(),
            "ultimas_24h": df.loc[df.index >= inicio_24h, 'valor'].sum(),
            "ultimas_48h": df.loc[df.index >= inicio_48h, 'valor'].sum(),
        }
    return somas

# Função para exibir gráficos
def mostrar_graficos(codigo_estacao, data_selecionada):
    if codigo_estacao not in st.session_state.somas_por_estacao:
        st.error(f"Estação {codigo_estacao} não encontrada.")
        return
    soma_dia = st.session_state.somas_por_estacao[codigo_estacao]["dia_atual"]
    soma_24h = st.session_state.somas_por_estacao[codigo_estacao]["ultimas_24h"]
    soma_48h = st.session_state.somas_por_estacao[codigo_estacao]["ultimas_48h"]
    horas = ['Dia Atual', '24 Horas', '48 Horas']
    valores = [soma_dia, soma_24h, soma_48h]
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.bar(horas, valores, color=['blue', 'orange', 'green'])
    ax.set_ylabel('Precipitação (mm)')
    ax.set_title(f'Estação {codigo_estacao} - Data: {data_selecionada.strftime("%d/%m/%Y")}')
    st.pyplot(fig)

# Carregar shapefile e CSV
mg_gdf = gpd.read_file(shp_mg_url)
df1 = pd.read_csv(csv_file_path)
gdf = gpd.GeoDataFrame(df1, geometry=gpd.points_from_xy(df1['longitude'], df1['latitude']))
gdf_mg = gpd.sjoin(gdf, mg_gdf, predicate='within')

# Seleção de estação
modo_selecao = st.sidebar.radio("Selecionar Estação por:", ('Código'))
if modo_selecao == 'Código':
    estacao_selecionada = st.sidebar.selectbox("Selecione a Estação", gdf_mg['codEstacao'].unique())
    codigo_estacao = estacao_selecionada

# Input para seleção de data
data_selecionada = st.sidebar.date_input("Data de Referência", value=datetime.now())

# Atualizar dados se a data estiver fora do intervalo
if st.sidebar.button("Atualizar Dados") or (
    st.session_state.range_dados["inicio"] is None
    or data_selecionada < st.session_state.range_dados["inicio"]
    or data_selecionada > st.session_state.range_dados["fim"]
):
    data_inicial = data_selecionada - timedelta(days=30)
    data_final = data_selecionada + timedelta(days=1)
    novos_dados = baixar_dados_estacoes([codigo_estacao], data_inicial, data_final, token, "MG")
    st.session_state.dados2.update(novos_dados)
    st.session_state.somas_por_estacao = calcular_somas(st.session_state.dados2)
    st.session_state.range_dados["inicio"] = data_inicial
    st.session_state.range_dados["fim"] = data_final

# Mostrar gráfico se checkbox estiver ativo
if st.sidebar.checkbox("Mostrar Gráfico"):
    mostrar_graficos(codigo_estacao, data_selecionada)

# Mostrar mapa
m = leafmap.Map(center=[-21, -45], zoom_start=8)
m.to_streamlit(width=1300, height=775)

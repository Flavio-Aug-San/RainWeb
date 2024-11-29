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

# Simulação de dados (soma de chuva em mm) - substitua por seus dados reais
chuva_ultima_hora = np.random.uniform(0, 5)  # Exemplo de valor entre 0 e 5mm
chuva_ultimas_24_horas = np.random.uniform(5, 50)  # Exemplo de valor entre 5 e 50mm
chuva_ultimas_48_horas = np.random.uniform(20, 100)  # Exemplo de valor entre 20 e 100mm

# URLs e caminhos de arquivos
shp_mg_url = 'https://github.com/giuliano-macedo/geodata-br-states/raw/main/geojson/br_states/br_mg.json'
csv_file_path = 'input;/estcaos_filtradas(1).csv'

# Login e senha do CEMADEN (previamente fornecidos)
login = 'augustoflaviobob@gmail.com'
senha = 'Flaviobr123!'

# Carregar os dados do shapefile de Minas Gerais
mg_gdf = gpd.read_file(shp_mg_url)

# Estações Selecionadas do Sul de Minas Gerais
#codigo_estacao = ['314790701A','310710901A','312870901A','315180001A','316930701A','314780801A','315250101A','313240401A','313360001A','311410501A','316230201A','313300601A']
codigo_estacao = '313240401A'

# Carregar os dados das estações
df1 = pd.read_csv(csv_file_path)
gdf = gpd.GeoDataFrame(df1, geometry=gpd.points_from_xy(df1['longitude'], df1['latitude']))

# Realizar o filtro espacial: apenas estações dentro de Minas Gerais
gdf_mg = gpd.sjoin(gdf, mg_gdf, predicate='within')

# Recuperação do token
token_url = 'http://sgaa.cemaden.gov.br/SGAA/rest/controle-token/tokens'
login_payload = {'email': login, 'password': senha}
response = requests.post(token_url, json=login_payload)
content = response.json()
token = content['token']

# sigla do estado do Brasil
sigla_estado = 'MG'

# período dos dados
anoi, mesi = '2024', '11'
anof, mesf = '2024', '11'

diai = '01'
diaf = str(calendar.monthrange(int(anof), int(mesf))[1])
data_inicial, data_final = f'{anoi}{mesi}{diai}', f'{anof}{mesf}{diaf}'
data_inicial = pd.to_datetime(data_inicial)

estacao_selecionada =  gdf_mg['codEstacao'].unique()

for ano_mes_dia in pd.date_range(data_inicial, data_final, freq='1M'):

    ano_mes = ano_mes_dia.strftime('%Y%m') #'202401'

    sws_url = 'http://sws.cemaden.gov.br/PED/rest/pcds/dados_pcd'
    params = dict(rede=11, uf=sigla_estado, inicio=ano_mes, fim=ano_mes, codigo=codigo_estacao) #data = '202404' e #codigo = '431490201A'
    r = requests.get(sws_url, params=params, headers={'token': token})
    dados = r.text
    # Remover a linha de comentário
    linhas = dados.split("\n")
    dados_filtrados = "\n".join(linhas[1:])  # Remove a primeira linha (comentário)

    # Transformar em DataFrame
    df = pd.read_csv(StringIO(dados_filtrados), sep=";")

    # seleciona o acumulado de chuva
    df = df[ df['sensor'] == 'chuva' ]

    # insere a coluna data como DateTime no DataFrame
    df['datahora'] = pd.to_datetime(df['datahora'])

    # seta a coluna data com o index do dataframe
    df.set_index('datahora', inplace=True)

    df2 = df['valor'].resample('H').sum()
    
    dfuma = df2[-1]
    
    # Filtra e soma os valores das últimas 24 horas
    soma_ultimas_24h = df2.iloc[-24:].sum()

    # Filtra e soma os valores das últimas 48 horas
    soma_ultimas_48h = df2.iloc[-48:].sum()

# Função para exibir gráficos de precipitação
def mostrar_graficos():
    horas = ['Última Hora', '24 Horas', '48 Horas']
    chuva_valores = [dfuma, soma_ultimas_24h, soma_ultimas_48h]

    fig, ax = plt.subplots()
    ax.bar(horas, chuva_valores, color=['blue', 'orange', 'green'])
    ax.set_ylabel('Precipitação (mm)')
    ax.set_title('Precipitação nas últimas horas')

    st.pyplot(fig)
# Função para exibir o pop-up no canto inferior direito
def exibir_popup(chuva_ultima_hora, chuva_ultimas_24_horas, chuva_ultimas_48_horas):
    st.markdown("""
    <style>
        .popup {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 250px;
            background-color: rgba(255, 255, 255, 0.8);
            color: black;
            padding: 10px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            font-family: Arial, sans-serif;
        }
    </style>
    """, unsafe_allow_html=True)

    # Conteúdo do popup
    st.markdown(f"""
    <div class="popup">
        <h4>Informações de Chuva</h4>
        <p>Chuva na última hora: {dfuma} mm</p>
        <p>Chuva nas últimas 24 horas: {soma_ultimas_24h} mm</p>
        <p>Chuva nas últimas 48 horas: {soma_ultimas_48h} mm</p>
    </div>
    """, unsafe_allow_html=True)
    
m = leafmap.Map(center=[-21, -45],zoom_start = 8,draw_control=False, measure_control=False, fullscreen_control=False, attribution_control=True)

# Defina o layout da página como largo
st.set_page_config(layout="wide")

# Adicionar marcadores das estações meteorológicas
for i, row in gdf_mg.iterrows():
    # Baixar dados da estação
    #dados_estacao= df

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
        popup=f"{row['municipio']} (Código: {row['codEstacao']})"
    ).add_to(m)

m.add_gdf(
    mg_gdf, 
    layer_name="Minas Gerais", 
    style={"color": "black", "weight": 1, "fillOpacity": 0, "interactive": False},
    info_mode=None
)

st.sidebar.header("Filtros de Seleção")
modo_selecao = st.sidebar.radio("Selecionar Estação por:", ('Código'))

if modo_selecao == 'Código':
    estacao_selecionada = st.sidebar.selectbox("Selecione a Estação", gdf_mg['codEstacao'].unique())
    codigo_estacao = gdf_mg[gdf_mg['codEstacao'] == estacao_selecionada]['codEstacao'].values[0]

sigla_estado = 'MG'
tipo_busca = st.sidebar.radio("Tipo de Busca:", ('Diária', 'Mensal'))

if tipo_busca == 'Diária':
    data_inicial = st.sidebar.date_input("Data", value=data_inicial)
else:
    ano_selecionado = st.sidebar.selectbox("Selecione o Ano", range(2020, datetime.now().year + 1))
    mes_selecionado = st.sidebar.selectbox("Selecione o Mês", range(1, 13))
    data_inicial = datetime(ano_selecionado, mes_selecionado, 1)
    data_final = datetime(ano_selecionado, mes_selecionado + 1, 1) - timedelta(days=1) if mes_selecionado != 12 else datetime(ano_selecionado, 12, 31)

if st.sidebar.button("Baixar Dados"):
    data_inicial_str = data_inicial.strftime('%Y%m%d')
    data_final_str = data_final.strftime('%Y%m%d')
    #dados_estacao= df

    if not dados_estacao.empty:
        st.subheader(f"Dados da Estação: {estacao_selecionada} (Código: {codigo_estacao})")
        st.write(dados_estacao)
    else:
        st.warning("Nenhum dado encontrado para o período selecionado.")

# Checkbox na barra lateral para alternar exibição do gráfico
mostrar = st.sidebar.checkbox("Gráfico de Precipitação")

# Exibir ou ocultar o gráfico conforme o estado do checkbox
if mostrar:
    mostrar_graficos()
st.dataframe(df)

# Mostrar o mapa em Streamlit
m.to_streamlit(width=1300,height=775)
# Chamando a função para exibir o popup
exibir_popup(chuva_ultima_hora, chuva_ultimas_24_horas, chuva_ultimas_48_horas)

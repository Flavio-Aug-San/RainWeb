import streamlit as st
import pandas as pd
import geopandas as gpd
import requests
from datetime import datetime, timedelta
import leafmap.foliumap as leafmap
import folium
import glob
from folium.plugins import MarkerCluster

# URLs e caminhos de arquivos
shp_mg_url = 'https://github.com/giuliano-macedo/geodata-br-states/raw/main/geojson/br_states/br_mg.json'
csv_file_path = 'input;/estcaos_filtradas(1).csv'

# Login e senha do CEMADEN (previamente fornecidos)
login = 'augustoflaviobob@gmail.com'
senha = 'Flaviobr123!'

# Carregar os dados do shapefile de Minas Gerais
mg_gdf = gpd.read_file(shp_mg_url)

# Estações Selecionadas do Sul de Minas Gerais
codigo_estacao = ['314790701A','310710901A','312870901A','315180001A','316930701A','314780801A','315250101A','313240401A','313360001A','311410501A','316230201A','313300601A']

# Carregar os dados das estações
df = pd.read_csv(csv_file_path)
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['longitude'], df['latitude']))

# Realizar o filtro espacial: apenas estações dentro de Minas Gerais
gdf_mg = gpd.sjoin(gdf, mg_gdf, predicate='within')

# Recuperação do token
token_url = 'http://sgaa.cemaden.gov.br/SGAA/rest/controle-token/tokens'
login_payload = {'email': login, 'password': senha}
response = requests.post(token_url, json=login_payload)
content = response.json()
token = content['token']

# Função para baixar os dados do último mês e retornar a soma
def baixar_dados_estacao(codigo_estacao, sigla_estado, data_inicial, data_final, login, senha):
    dfs = []
    for ano_mes_dia in pd.date_range(data_inicial, data_final, freq='1M'):
        ano_mes = ano_mes_dia.strftime('%Y%m')
        sws_url = 'http://sws.cemaden.gov.br/PED/rest/pcds/df_pcd'
        params = dict(rede=11, uf=sigla_estado, inicio=ano_mes, fim=ano_mes, codigo=codigo_estacao)
        r = requests.get(sws_url, params=params, headers={'token': token})
        df_mes = pd.read_csv(pd.compat.StringIO(r.text))
        dfs.append(df_mes)
            
    files = sorted(glob.glob(f'/content/estacao_CEMADEN_{sigla_estado}_{codigo_estacao}*.csv'))

    # leitura dos arquivos
    dfs = pd.DataFrame()
    for file in files:
    
        # leitura da tabela
        df0 = pd.read_csv(file, delimiter=';', skiprows=1)
    
        # junta a tabela que foi lida com a anterior
        dfs = pd.concat([dfs, df0], ignore_index=True)

    # seleciona o acumulado de vhuva
    df = dfs[ dfs['sensor'] == 'chuva' ]
    
    soma_selecionada = df['valor'].sum()

# Função principal do dashboard
def main():
    hoje = datetime.now()
    data_inicial = hoje.replace(day=1)
    data_final = hoje

    st.set_page_config(layout="wide")

    st.markdown(
        """
        <style>
            .main .block-container {
                padding: 0;
                margin: 0;
            }
            iframe {
                height: 100vh !important;
                width: 100vw !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    m = leafmap.Map(center=[-21.5, -45.75], zoom=7, draw_control=False, measure_control=False, fullscreen_control=False, attribution_control=False)

    # Adicionar marcadores das estações meteorológicas
    for i, row in gdf_mg.iterrows():
        # Baixar dados da estação
        codigo_estacao = row['codEstacao']
        dados_estacao= baixar_dados_estacao(codigo_estacao, 'MG', data_inicial, data_final, login, senha)

        # Definir cor com base no valor
        #if soma_selecionada <= 10:
            #cor = 'green'
        #elif 10 <soma_selecionada <= 30:
           # cor = 'yellow'
       # else:
         #   cor = 'red'
        # Adicionar marcador com valor
        folium.RegularPolygonMarker(
            location=[row['latitude'], row['longitude']],
            color='black',
            opacity=1,
            weight=2,
            fillColor='green',
            fillOpacity=1,
            numberOfSides=2,
            rotation=45,
            radius=10,
            popup=f"{row['municipio']} (Código: {row['codEstacao']})<br>Soma do último mês:{soma_selecionada}"
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
        dados_estacao= baixar_dados_estacao(codigo_estacao, sigla_estado, data_inicial, data_final, login, senha)

        if not dados_estacao.empty:
            st.subheader(f"Dados da Estação: {estacao_selecionada} (Código: {codigo_estacao})")
            st.write(dados_estacao)
        else:
            st.warning("Nenhum dado encontrado para o período selecionado.")

    m.to_streamlit()

if __name__ == "__main__":
    main()

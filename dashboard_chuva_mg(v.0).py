import streamlit as st
import pandas as pd
import geopandas as gpd
import requests
from datetime import datetime, timedelta
import leafmap.foliumap as leafmap

# URLs e caminhos de arquivos
shp_mg_url = 'https://github.com/giuliano-macedo/geodata-br-states/raw/main/geojson/br_states/br_mg.json'
csv_file_path = 'input;/lista_das_estacoes_CEMADEN_13maio2024.csv'

# Login e senha do CEMADEN (previamente fornecidos)
login = 'augustoflaviobob@gmail.com'
senha = 'Flaviobr123!'

# Carregar os dados do shapefile de Minas Gerais
mg_gdf = gpd.read_file(shp_mg_url)

# Carregar os dados das estações
df = pd.read_csv(csv_file_path)
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['Longitude'], df['Latitude']))

# Realizar o filtro espacial: apenas estações dentro de Minas Gerais
gdf_mg = gpd.sjoin(gdf, mg_gdf, predicate='within')

# Função para baixar os dados da estação
def baixar_dados_estacao(codigo_estacao, sigla_estado, data_inicial, data_final, login, senha):
    # Recuperação do token
    token_url = 'http://sgaa.cemaden.gov.br/SGAA/rest/controle-token/tokens'
    login_payload = {'email': login, 'password': senha}
    response = requests.post(token_url, json=login_payload)
    content = response.json()
    token = content['token']

    # Lista para armazenar os dados
    dfs = []

    # Loop para baixar os dados mês a mês
    for ano_mes_dia in pd.date_range(data_inicial, data_final, freq='1M'):
        ano_mes = ano_mes_dia.strftime('%Y%m')
        sws_url = 'http://sws.cemaden.gov.br/PED/rest/pcds/df_pcd'
        params = dict(rede=11, uf=sigla_estado, inicio=ano_mes, fim=ano_mes, codigo=codigo_estacao)
        r = requests.get(sws_url, params=params, headers={'token': token})
        
        # Se há dados, adiciona ao DataFrame
        if r.text:
            df_mes = pd.read_csv(pd.compat.StringIO(r.text))
            dfs.append(df_mes)

    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        return pd.DataFrame()

# Função principal do dashboard
def main():
        # Defina o layout da página como largo
        st.set_page_config(layout="wide")
        
        # CSS customizado para tornar o mapa tela cheia
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
        
        # Mapa interativo usando Leafmap
        m = leafmap.Map(center=[-18.5122, -44.5550], zoom=7,draw_control=False, measure_control=False, fullscreen_control=False, attribution_control=True)
        
        # Sidebar para seleção de estação e datas
        st.sidebar.header("Filtros de Seleção")
        
        # Opções de seleção: Nome ou Código
        modo_selecao = st.sidebar.radio("Selecionar Estação por:", ('Nome'))
        
        if modo_selecao == 'Nome':
            estacao_selecionada = st.sidebar.selectbox("Selecione a Estação", gdf_mg['Nome'].unique())
            codigo_estacao = gdf_mg[gdf_mg['Nome'] == estacao_selecionada]['Código'].values[0]

        # Recupera as coordenadas da estação selecionada
        latitude_estacao = gdf_mg[gdf_mg['Nome'] == estacao_selecionada]['Latitude'].values[0]
        longitude_estacao = gdf_mg[gdf_mg['Nome'] == estacao_selecionada]['Longitude'].values[0]
    
        sigla_estado = 'MG'
        
        # Escolha entre busca diária ou mensal
        tipo_busca = st.sidebar.radio("Tipo de Busca:", ('Diária', 'Mensal'))
        
        if tipo_busca == 'Diária':
            # Seleção de datas para busca diária
            data_inicial = st.sidebar.date_input("Data Inicial", value=datetime(2023, 1, 1))
            data_final = st.sidebar.date_input("Data Final", value=datetime(2023, 12, 31))
        else:
            # Seleção de mês para busca mensal
            ano_selecionado = st.sidebar.selectbox("Selecione o Ano", range(2020, datetime.now().year + 1))
            mes_selecionado = st.sidebar.selectbox("Selecione o Mês", range(1, 13))
            
            # Definindo a data inicial e final com base no mês e ano selecionados
            data_inicial = datetime(ano_selecionado, mes_selecionado, 1)
            data_final = datetime(ano_selecionado, mes_selecionado + 1, 1) - timedelta(days=1) if mes_selecionado != 12 else datetime(ano_selecionado, 12, 31)
        
        if st.sidebar.button("Baixar Dados"):
            # Converter datas para o formato necessário
            data_inicial_str = data_inicial.strftime('%Y%m%d')
            data_final_str = data_final.strftime('%Y%m%d')
            # Baixar os dados da estação
            dados_estacao = baixar_dados_estacao(codigo_estacao, sigla_estado, data_inicial_str, data_final_str, login, senha)
        
            if not dados_estacao.empty:
                st.subheader(f"Dados da Estação: {estacao_selecionada} (Código: {codigo_estacao})")
                st.write(dados_estacao)
        else:
            st.warning("Nenhum dado encontrado para o período selecionado.")
            
        for i, row in gdf_mg.iterrows():
            m.add_marker(location=[row['Latitude'], row['Longitude']],popup=f"{row['Nome']} (Código: {row['Código']})")
        m.to_streamlit()

if __name__ == "__main__":
    main()

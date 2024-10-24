import streamlit as st
import pandas as pd
import geopandas as gpd
import requests
import numpy as np
from datetime import datetime, timedelta
import leafmap.foliumap as leafmap
import folium
import glob
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

# Seleção da estação
estacao_selecionada = st.selectbox("Selecione a Estação", list(df['codEstacao'].keys()))

# Obter os valores de precipitação da estação selecionada
dados_chuva = df['valorMedida']
chuva_ultima_hora = dados_chuva[0]
chuva_24h = dados_chuva[0]
chuva_48h = dados_chuva[0]

# Estado para controlar exibição do gráfico
mostrar_grafico = st.session_state.get('mostrar_grafico', False)

# Função para exibir gráficos de precipitação
def mostrar_graficos():
    st.markdown(f"### Gráfico de Precipitação - {estacao_selecionada}")
    horas = ['Última Hora', '24 Horas', '48 Horas']
    chuva_valores = [chuva_ultima_hora, chuva_24h, chuva_48h]
    
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
        <p>Chuva na última hora: {chuva_ultima_hora} mm</p>
        <p>Chuva nas últimas 24 horas: {chuva_ultimas_24_horas} mm</p>
        <p>Chuva nas últimas 48 horas: {chuva_ultimas_48_horas} mm</p>
    </div>
    """, unsafe_allow_html=True)

# Função para baixar os dados do último mês e retornar a soma
def baixar_dados_estacao(codigo_estacao, sigla_estado, data_inicial, data_final, login, senha):
    dfs = []
    for estacao in codigo_estacao: 
        for ano_mes_dia in pd.date_range(data_inicial, data_final, freq='1M'):
            ano_mes = ano_mes_dia.strftime('%Y%m')
            sws_url = 'http://sws.cemaden.gov.br/PED/rest/pcds/df_pcd'
            params = dict(rede=11, uf=sigla_estado, inicio=ano_mes, fim=ano_mes, codigo=codigo_estacao)
            r = requests.get(sws_url, params=params, headers={'token': token})
            df_mes = pd.read_csv(pd.compat.StringIO(r.text))
            df.append(df_mes)
                
        files = sorted(glob.glob(f'/content/estacao_CEMADEN_{sigla_estado}_{codigo_estacao}*.csv'))
    
        # leitura dos arquivos
        df = pd.DataFrame()
        for file in files:
        
            # leitura da tabela
            df0 = pd.read_csv(file, delimiter=';', skiprows=1)
        
            # junta a tabela que foi lida com a anterior
            df = pd.concat([df, df0], ignore_index=True)
    
        # insere a coluna data como DateTime no DataFrame
        #df['datahora'] = pd.to_datetime(df['datahora'])
        
        # seta a coluna data com o index do dataframe
        #df.set_index('datahora', inplace=True)
    
        # seleciona o acumulado de vhuva
        #dfs = df[df['sensor'] == 'chuva']
        
    #soma_selecionada = df['valor'].sum()

# Função principal do dashboard
def main():
    hoje = datetime.now()
    data_inicial = hoje.replace(day=1)
    data_final = hoje

    m = leafmap.Map(center=[-21.5, -45.75],zoom=20,draw_control=False, measure_control=False, fullscreen_control=False, attribution_control=True)

    # Adicionar marcadores das estações meteorológicas
    for i, row in gdf_mg.iterrows():
        # Baixar dados da estação
        codigo_estacao = row['codEstacao']
        dados_estacao= baixar_dados_estacao(codigo_estacao, 'MG', data_inicial, data_final, login, senha)
        
        # Adicionar marcador com valor
        folium.RegularPolygonMarker(
            location=[row['latitude'], row['longitude']],
            color='black',
            opacity=1,
            weight=2,
            fillColor='green',
            fillOpacity=1,
            numberOfSides=4,
            rotation=45,
            radius=10,
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
        dados_estacao= baixar_dados_estacao(codigo_estacao, sigla_estado, data_inicial, data_final, login, senha)

        if not dados_estacao.empty:
            st.subheader(f"Dados da Estação: {estacao_selecionada} (Código: {codigo_estacao})")
            st.write(dados_estacao)
        else:
            st.warning("Nenhum dado encontrado para o período selecionado.")
    # Botões para exibir e fechar gráficos
    if not mostrar_grafico:
        if st.button("Mostrar Gráfico"):
            st.session_state['mostrar_grafico'] = True
    else:
        st.markdown(f"### Gráfico de Precipitação - {estacao_selecionada}")
        mostrar_graficos()
        
    m.to_streamlit()
    # Chamando a função para exibir o popup
    exibir_popup(chuva_ultima_hora, chuva_ultimas_24_horas, chuva_ultimas_48_horas)
    
    if st.button("Fechar Gráfico"):
        st.session_state['mostrar_grafico'] = False
        
if __name__ == "__main__":
    main()

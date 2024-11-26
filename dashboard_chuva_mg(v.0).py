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
import requests
from bs4 import BeautifulSoup

# Simulação de dados (soma de chuva em mm) - substitua por seus dados reais
chuva_ultima_hora = np.random.uniform(0, 5)  # Exemplo de valor entre 0 e 5mm
chuva_ultimas_24_horas = np.random.uniform(5, 50)  # Exemplo de valor entre 5 e 50mm
chuva_ultimas_48_horas = np.random.uniform(20, 100)  # Exemplo de valor entre 20 e 100mm

# Pegar o dia atual: Obtém a data e hora atual
agora = datetime.now()

# Extrai o dia, mês e ano
dia = agora.day
mes = agora.month
ano = agora.year

# Formatar mês e dia para dois dígitos
mes_formatado = f'{mes:02d}'
dia_formatado = f'{dia:02d}'

# Concatenar ano, mês e dia
data_formatada = f'{ano}{mes_formatado}{dia_formatado}'

# URLs e caminhos de arquivos
shp_mg_url = 'https://github.com/giuliano-macedo/geodata-br-states/raw/main/geojson/br_states/br_mg.json'
#csv_file_path = 'input;/estcaos_filtradas(1).csv'

# Login e senha do CEMADEN (previamente fornecidos)
#login = 'augustoflaviobob@gmail.com'
#senha = 'Flaviobr123!'

# Carregar os dados do shapefile de Minas Gerais
mg_gdf = gpd.read_file(shp_mg_url)

# Estações Selecionadas do Sul de Minas Gerais
# codigo_estacao = ['314790701A','310710901A','312870901A','315180001A','316930701A','314780801A','315250101A','313240401A','313360001A','311410501A','316230201A','313300601A']
estacoes = ['IVARGE10','ICACON2','IAGUAN2','IPOOSD2','IVARGI20','IBOCAI17','IITAJUB5','ISOSEB22','IEXTRE1','ISOLOU3','ISOGON8','IITAMO7']
muni = ['Vargem Bonita','Caconde','Iguanil','Poços de Caldas','Varginha','Bocaina de Minas','Itajubá','São Sebastião da Bela Vista','Extrema','São Lourenço','São Gonçalo do Sapucaí','Itamonte']
lat = [-20.55,-21.53,-20.98,-21.79,-21.55,-22.26,-22.41,-22.18,-22.78,-22.11,-21.96,-22.23]
lon = [-46.30,-46.65,-45.37,-46.57,-45.45,-44.45,-45.45,-45.81,-46.28,-45.06,-45.50,-44.85]

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

# Obter os valores de precipitação da estação selecionada
dados_chuva = df['valorMedida']
chuva_ultima_hora = dados_chuva[0]
chuva_24h = dados_chuva[0]
chuva_48h = dados_chuva[0]

estacao_selecionada =  gdf_mg['codEstacao'].unique()

# Função para exibir gráficos de precipitação
def mostrar_graficos():
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

def processar_estacoes(estacoes, ano, mes, dia):
    resultados = {}
    
    for estacao in estacoes:
        try:
            print(f"Processando estação: {estacao}")
            
            # URL formatada
            url = f'https://www.wunderground.com/dashboard/pws/{estacao}/table/{ano}-{mes}-{dia}/{ano}-{mes}-{dia}/daily'
            
            # Requisição HTTP
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Encontrar a tabela
            table = soup.find('table', class_='history-table desktop-table')

            if not table:
                print(f"Nenhuma tabela encontrada para a estação {estacao}.")
                continue

            # Processar as linhas da tabela
            rows = table.find_all('tr')
            data = []

            # Extrair cabeçalhos
            headers = [header.text.strip() for header in rows[0].find_all('th')]
            data.append(headers)

            # Extrair dados
            for row in rows[1:]:
                cols = row.find_all('td')
                cols = [col.text.strip() for col in cols]
                data.append(cols)

            # Converter para DataFrame do pandas
            df = pd.DataFrame(data[1:], columns=data[0])

            # Remover as colunas indesejadas
            colunas_para_remover = ['Dew Point', 'Wind', 'Speed', 'Gust', 'Pressure', 'Precip. Accum.', 'UV', 'Solar']
            df = df.drop(columns=[col for col in colunas_para_remover if col in df.columns])

            # Remover a linha que contém valores None em todas as colunas
            df = df.dropna(how='all')

            # Processar colunas
            if 'Time' in df.columns:
                df['Time'] = pd.to_datetime(df['Time'], format='%I:%M %p').dt.strftime('%H:%M')

            if 'Temperature' in df.columns:
                df['Temperature'] = df['Temperature'].str.replace('°F', '').astype(float)
                df['Temperature'] = (df['Temperature'] - 32) * 5.0 / 9.0

            if 'Humidity' in df.columns:
                df['Humidity'] = df['Humidity'].str.replace('%', '').astype(float)

            if 'Precip. Rate.' in df.columns:
                df['Precip. Rate.'] = df['Precip. Rate.'].str.replace(' in', '').astype(float)
                # Conversão de polegadas para mm
                df['Precip. Rate.'] = df['Precip. Rate.'] * 25.4

            # Criar coluna 'Date' e 'DateTime'
            dia_formatado = f'{dia:02d}'
            df['Date'] = f'{ano}-{mes:02d}-{dia_formatado}'
            df['DateTime'] = df['Date'] + ' ' + df['Time']

            df = df.drop(columns=['Date', 'Time'], errors='ignore')
            df = df.set_index('DateTime', drop=True)
            df.index = pd.to_datetime(df.index)

            # Agrupar por hora e calcular médias
            df = df.resample('H').mean()

            # Remover colunas de Temperatura e Umidade
            df = df.drop(columns=['Temperature', 'Humidity'], errors='ignore')

            # Formatar resultados com duas casas decimais
            df = df.round(2)

            # Salvar no dicionário de resultados
            resultados[estacao] = df
        except Exception as e:
            print(f"Erro ao processar a estação {estacao}: {e}")

    return resultados

m = leafmap.Map(center=[-21, -45],zoom_start = 8,draw_control=False, measure_control=False, fullscreen_control=False, attribution_control=True)

# Defina o layout da página como largo
st.set_page_config(layout="wide")

hoje = datetime.now()
data_inicial = hoje.replace(day=1)
data_final = hoje
    
# Adicionar marcadores das estações meteorológicas
for i, row in gdf_mg.iterrows():
    # Baixar dados da estação
    dados_estacao= processar_estacoes(estacoes, ano, mes, dia)
    
    # Adicionar marcadores para cada estação
    for i in range(len(estacoes)):
        folium.RegularPolygonMarker(
            location=[lat[i], lon[i]],
            color='black',
            opacity=1,
            weight=1,
            fillColor='green',
            fillOpacity=1,
            numberOfSides=4,
            rotation=45,
            radius=8,
            popup=f"{muni[i]} (Código: {estacoes[i]})"
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
    estacao_selecionada = st.sidebar.selectbox("Selecione a Estação", dados_estacao['estacoes'].unique())
    codigo_estacao = dados_estacao[dados_estacao['estacoes'] == estacao_selecionada]['estacoes'].values[0]

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
    dados_estacao= processar_estacoes(estacoes, ano, mes, dia)

    if not dados_estacao.empty:
        st.subheader(f"Dados da Estação: {estacao_selecionada} (Código: {estacoes})")
        st.write(estacoes)
    else:
        st.warning("Nenhum dado encontrado para o período selecionado.")
    
# Checkbox na barra lateral para alternar exibição do gráfico
mostrar = st.sidebar.checkbox("Gráfico de Precipitação")

# Exibir ou ocultar o gráfico conforme o estado do checkbox
if mostrar:
    mostrar_graficos()
    
# Mostrar o mapa em Streamlit
m.to_streamlit(width=1300,height=775)
# Chamando a função para exibir o popup
exibir_popup(chuva_ultima_hora, chuva_ultimas_24_horas, chuva_ultimas_48_horas)

import streamlit as st
import pandas as pd
import geopandas as gpd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import requests
from io import StringIO
import folium
import leafmap.foliumap as leafmap
from folium.plugins import MarkerCluster

# Configuração inicial da página
st.set_page_config(layout="wide")
st.sidebar.header("Filtros de Seleção")

# URLs e caminhos de arquivos
shp_mg_url = 'https://github.com/giuliano-macedo/geodata-br-states/raw/main/geojson/br_states/br_mg.json'
csv_file_path = 'input/filtered_data.csv'  # Corrigido o caminho do arquivo

# Login e senha do CEMADEN (previamente fornecidos)
login = 'augustoflaviobob@gmail.com'
senha = 'Flaviobr123!'

# Inicializar session state
if "dados2" not in st.session_state:
    st.session_state.dados2 = {}
if "somas_por_estacao" not in st.session_state:
    st.session_state.somas_por_estacao = {}
if "range_dados" not in st.session_state:
    st.session_state.range_dados = {"inicio": None, "fim": None}
if "token" not in st.session_state:
    # Recuperação do token
    token_url = 'http://sgaa.cemaden.gov.br/SGAA/rest/controle-token/tokens'
    login_payload = {'email': login, 'password': senha}
    response = requests.post(token_url, json=login_payload)
    if response.status_code == 200:
        content = response.json()
        st.session_state.token = content.get('token')
    else:
        st.error("Erro ao recuperar token. Verifique as credenciais e tente novamente.")
        st.stop()

# Função para baixar os dados
def baixar_dados_estacoes(codigo_estacao, data_inicial, data_final, token, sigla_estado):
    dados_estacoes = {}
    for codigo in codigo_estacao:
        dados_completos = []
        # Baixar dados mês a mês para evitar sobrecarga
        for ano_mes_dia in pd.date_range(data_inicial, data_final, freq='MS'):  # 'MS' para início do mês
            ano_mes = ano_mes_dia.strftime('%Y%m')  # Formato '202401'
            sws_url = 'http://sws.cemaden.gov.br/PED/rest/pcds/dados_pcd'
            params = {"rede": 11, "uf": sigla_estado, "inicio": ano_mes, "fim": ano_mes, "codigo": codigo}
            r = requests.get(sws_url, params=params, headers={'token': token})
            if r.status_code == 200:
                dados = r.text.split("\n")[1:]  # Remove a primeira linha (comentário)
                if dados:
                    try:
                        df = pd.read_csv(StringIO("\n".join(dados)), sep=";")
                        if not df.empty:
                            dados_completos.append(df)
                    except Exception as e:
                        st.warning(f"Erro ao ler dados para a estação {codigo} no período {ano_mes}: {e}")
            else:
                st.warning(f"Erro na requisição para a estação {codigo} no período {ano_mes}: {r.status_code}")
        if dados_completos:
            dados_estacoes[codigo] = pd.concat(dados_completos, ignore_index=True)
    return dados_estacoes

# Função para calcular as somas
def calcular_somas(dados2):
    somas = {}
    agora = datetime.now()
    for codigo, df in dados2.items():
        df = df.copy()
        if 'datahora' in df.columns:
            df['datahora'] = pd.to_datetime(df['datahora'])
            df.set_index('datahora', inplace=True)
        else:
            st.warning(f"Datahora não encontrada no DataFrame da estação {codigo}.")
            continue
        # Filtrar os dados para o dia atual, últimas 24 horas e últimas 48 horas
        inicio_dia_atual = agora.replace(hour=0, minute=0, second=0, microsecond=0)
        inicio_24h = agora - timedelta(hours=24)
        inicio_48h = agora - timedelta(hours=48)
        
        soma_dia_atual = df.loc[df.index >= inicio_dia_atual, 'valor'].sum()
        soma_24h = df.loc[df.index >= inicio_24h, 'valor'].sum()
        soma_48h = df.loc[df.index >= inicio_48h, 'valor'].sum()
        
        # Armazenar os resultados
        somas[codigo] = {
            "dia_atual": soma_dia_atual,
            "ultimas_24h": soma_24h,
            "ultimas_48h": soma_48h
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
@st.cache_data
def carregar_dados():
    mg_gdf = gpd.read_file(shp_mg_url)
    df1 = pd.read_csv(csv_file_path)
    gdf = gpd.GeoDataFrame(df1, geometry=gpd.points_from_xy(df1['longitude'], df1['latitude']))
    gdf_mg = gpd.sjoin(gdf, mg_gdf, predicate='within')
    return mg_gdf, gdf_mg

mg_gdf, gdf_mg = carregar_dados()

# Seleção de estação
modo_selecao = st.sidebar.radio("Selecionar Estação por:", ('Código'))
if modo_selecao == 'Código':
    estacao_selecionada = st.sidebar.selectbox("Selecione a Estação", gdf_mg['codEstacao'].unique())
    codigo_estacao = estacao_selecionada

# Input para seleção de data
data_selecionada = st.sidebar.date_input("Data de Referência", value=datetime.now().date())

# Inicial download on first run if 'dados2' is vazio
if not st.session_state.dados2:
    # Definir um intervalo padrão, por exemplo, últimos 30 dias
    data_final_default = datetime.now()
    data_inicial_default = data_final_default - timedelta(days=30)
    token = st.session_state.token
    dados_baixados = baixar_dados_estacoes([codigo_estacao], data_inicial_default, data_final_default, token, "MG")
    if dados_baixados:
        st.session_state.dados2 = dados_baixados
        st.session_state.somas_por_estacao = calcular_somas(dados_baixados)
        st.session_state.range_dados = {
            "inicio": data_inicial_default.date(),
            "fim": data_final_default.date()
        }
    else:
        st.warning("Nenhum dado foi baixado na inicialização.")

# Função para atualizar dados com base na data selecionada
def atualizar_dados_selecionados():
    data_min = st.session_state.range_dados["inicio"]
    data_max = st.session_state.range_dados["fim"]
    # Converter data_selecionada para datetime
    data_selecionada_dt = datetime.combine(data_selecionada, datetime.min.time())
    if (data_selecionada < data_min) or (data_selecionada > data_max):
        st.info("A data selecionada está fora do intervalo atual. Baixando novos dados...")
        # Definir novos intervalos para incluir a data selecionada
        # Aqui, baixar 30 dias antes e 1 dia depois da data selecionada
        nova_data_inicial = data_selecionada_dt - timedelta(days=30)
        nova_data_final = data_selecionada_dt + timedelta(days=1)
        token = st.session_state.token
        novos_dados = baixar_dados_estacoes([codigo_estacao], nova_data_inicial, nova_data_final, token, "MG")
        if novos_dados:
            # Atualizar dados2 com novos dados, evitando duplicações
            for codigo, df in novos_dados.items():
                if codigo in st.session_state.dados2:
                    # Concatenar e remover duplicatas
                    combined_df = pd.concat([st.session_state.dados2[codigo], df], ignore_index=True)
                    combined_df.drop_duplicates(subset='datahora', inplace=True)
                    st.session_state.dados2[codigo] = combined_df
                else:
                    st.session_state.dados2[codigo] = df
            # Recalcular somas
            st.session_state.somas_por_estacao = calcular_somas(st.session_state.dados2)
            # Atualizar range_dados
            new_inicio = min(nova_data_inicial.date(), st.session_state.range_dados["inicio"])
            new_fim = max(nova_data_final.date(), st.session_state.range_dados["fim"])
            st.session_state.range_dados["inicio"] = new_inicio
            st.session_state.range_dados["fim"] = new_fim
            st.success("Dados atualizados com sucesso.")
        else:
            st.warning("Nenhum dado foi baixado para a data selecionada.")

# Botão para atualizar dados
if st.sidebar.button("Atualizar Dados"):
    atualizar_dados_selecionados()

# Verificar se a data selecionada está fora do range e atualizar se necessário
data_min = st.session_state.range_dados["inicio"]
data_max = st.session_state.range_dados["fim"]
data_selecionada_dt = datetime.combine(data_selecionada, datetime.min.time())
if (data_selecionada < data_min) or (data_selecionada > data_max):
    atualizar_dados_selecionados()

# Checkbox na barra lateral para alternar exibição do gráfico
mostrar = st.sidebar.checkbox("Mostrar Gráfico de Precipitação")

# Exibir gráfico se checkbox estiver ativo
if mostrar:
    mostrar_graficos(codigo_estacao, data_selecionada_dt)

# Criar o mapa com marcadores
m = leafmap.Map(center=[-21, -45], zoom_start=8, draw_control=False, measure_control=False, fullscreen_control=False, attribution_control=True)

# Adicionar marcadores das estações meteorológicas
for i, row in gdf_mg.iterrows():    
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

# Adicionar shapefile no mapa
m.add_gdf(
    mg_gdf, 
    layer_name="Minas Gerais", 
    style={"color": "black", "weight": 1, "fillOpacity": 0, "interactive": False},
    info_mode=None
)

# Exibir o mapa no Streamlit
m.to_streamlit(width=1300, height=775)

# Mostrar o conteúdo dos dicionários
st.write("Dados armazenados no dicionário `dados2`:", st.session_state.dados2 if st.session_state.dados2 else "Dicionário vazio")
st.write("Somas por estação:", st.session_state.somas_por_estacao if st.session_state.somas_por_estacao else "Dicionário vazio")
st.write("Intervalo de dados carregados:", st.session_state.range_dados)

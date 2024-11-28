# -*- coding: utf-8 -*-
"""04_download_via_API_estacoes_CEMADEN.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/github/evmpython/estacoes_meteorologicas/blob/main/04_download_via_API_estacoes_CEMADEN.ipynb

**DOWNLOAD DOS DADOS DAS ESTAÇÕES METEOROLÓGICAS DO `CEMADEN`**

---
- Para processar esse código será necessário solicitar ao CEMADEN via e-mail (ped@cemaden.gov.br) o login e senha.

- O acesso é realizado via Plataforma de Entrega de Dados (PED): http://ped.cemaden.gov.br/

- Informações sobre as estações: http://ped.cemaden.gov.br/ConsultarRedeEstacoes

---


- Código realizado por: Enrique V. Mattos -- 13/05/2024 - enrique@unifei.edu.br.

---

#**Estações do CEMADEN disponíveis**
"""

# baixa a lista das estações
!wget -c https://raw.githubusercontent.com/evmpython/estacoes_meteorologicas/main/input/lista_das_estacoes_CEMADEN_13maio2024.csv

# leitura do planilha
import pandas as pd
df_estacoes = pd.read_csv('/content/lista_das_estacoes_CEMADEN_13maio2024.csv')
df_estacoes.drop('Unnamed: 0', axis=1, inplace=True)
df_estacoes.rename(columns={'Código': 'codigo', 'Nome': 'nome', 'Latitude': 'lat', 'Longitude': 'lon'}, inplace=True)
df_estacoes.head(2)

print('Quantidade de estações do CEMADEN=', f'{df_estacoes.shape[0]} estações')

"""# **Download dos dados**
Para realizar o download dos dados deverá ser informado:

- LOGIN e SENHA passado pelo CEMADEN

![image.png](data:image/png;base64,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)

- Código da estação
- Sigla do Estado da Federação que pertence a estação
- Ano e Mês inicial e final

![image.png](data:image/png;base64,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)

- 1) Indicar o `Estado` e `código` da estação. Para isto você deverá acessar a [página](http://www2.cemaden.gov.br/mapainterativo/#) do CEMADEN e clicar em *Estações* localizado na parte superior da página e depois em *Pluviometros Automáticos*, como mostrado na figura abaixo. Basta passar o Mouse sobre a estação e anotar o código.

- 2) Indicar o `Ano` e `Mês` inicial e final.

"""

#====================================================================#
#                 Importa bibliotecas
#====================================================================#
import pandas as pd
import requests
import glob
import calendar
import os
import warnings
warnings.filterwarnings("ignore")

# remove arquivos anteriores
!rm /content/estacao_CEMADEN_*.csv

#====================================================================#
#                 Informar LOGIN e SENHA
#====================================================================#
# LOGIN passado pelo CEMADEN
login = ' '

# SENHA passado pelo CEMADEN
senha = ' '

#====================================================================#
#                 Define o período e estação
#====================================================================#
# código da estação
codigo_estacao = '432026301A'

# sigla do estado do Brasil
sigla_estado = 'RS'

# período dos dados
anoi, mesi = '2024', '02'
anof, mesf = '2024', '05'

diai = '01'
diaf = str(calendar.monthrange(int(anof), int(mesf))[1])
data_inicial, data_final = f'{anoi}{mesi}{diai}', f'{anof}{mesf}{diaf}'

#====================================================================#
#           Recuperação do token usando Python
#====================================================================#
token_url = 'http://sgaa.cemaden.gov.br/SGAA/rest/controle-token/tokens'

login = {'email': login, 'password': senha}
response = requests.post(token_url, json=login)
content = response.json()
token = content['token']

#====================================================================#
#               Download dos arquivos por mês
#====================================================================#
for ano_mes_dia in pd.date_range(data_inicial, data_final, freq='1M'):

    #------------------------------------------#
    #          Extrai o ano e mês
    #------------------------------------------#
    ano_mes = ano_mes_dia.strftime('%Y%m') #'202401'

    #------------------------------------------#
    #    Requisição de dados usando Python
    #------------------------------------------#
    sws_url = 'http://sws.cemaden.gov.br/PED/rest/pcds/dados_pcd'
    params = dict(rede=11, uf=sigla_estado, inicio=ano_mes, fim=ano_mes, codigo=codigo_estacao) #data = '202404' e #codigo = '431490201A'
    r = requests.get(sws_url, params=params, headers={'token': token})
    dados = r.text

    #------------------------------------------#
    #           Escrita do arquivo
    #------------------------------------------#
    with open(f'/content/estacao_CEMADEN_{sigla_estado}_{codigo_estacao}_{ano_mes}.csv','w') as arquivo:
        for dado in dados:
            arquivo.write(str(dado))

#====================================================================#
#               Junta num arquivo CSV
#====================================================================#
# lista os arquivos
files = sorted(glob.glob(f'/content/estacao_CEMADEN_{sigla_estado}_{codigo_estacao}*.csv'))

# leitura dos arquivos
df = pd.DataFrame()
for file in files:

    # leitura da tabela
    df0 = pd.read_csv(file, delimiter=';', skiprows=1)

    # junta a tabela que foi lida com a anterior
    df = pd.concat([df, df0], ignore_index=True)

# salva arquivo
df.to_csv(f'/content/merge_estacao_CEMADEN_{sigla_estado}_{codigo_estacao}_{data_inicial}_to_{data_final}.csv')

# seleciona o acumulado de vhuva
df = df[ df['sensor'] == 'chuva' ]

# insere a coluna data como DateTime no DataFrame
df['datahora'] = pd.to_datetime(df['datahora'])

# seta a coluna data com o index do dataframe
df.set_index('datahora', inplace=True)

# mostra os dados
df
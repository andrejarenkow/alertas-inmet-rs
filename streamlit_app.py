# Importação de bibliotecas
import pandas as pd
import geopandas as gpd
import plotly.express as px
import streamlit as st
import plotly.graph_objects as go
import requests
import folium
from streamlit_folium import st_folium, folium_static

# Configurações da página
st.set_page_config(
    page_title="Alertas INMET - RS",
    page_icon=":warning:",
    #layout="wide",
    initial_sidebar_state='collapsed'
)
col1, col2, col3 = st.columns([1,4,1])

col1.image('https://github.com/andrejarenkow/csv/blob/master/logo_cevs%20(2).png?raw=true', width=100)
col2.title('Alertas INMET - RS')
col3.image('https://github.com/andrejarenkow/csv/blob/master/logo_estado%20(3)%20(1).png?raw=true', width=150)


# Importação dos dados
municipios_crs = pd.read_csv('https://raw.githubusercontent.com/andrejarenkow/csv/master/Munic%C3%ADpios%20RS%20IBGE6%20Popula%C3%A7%C3%A3o%20CRS%20Regional%20-%20P%C3%A1gina1.csv')


# Dados INMET
def obter_dados_api(url):
    try:
        resposta = requests.get(url)
        resposta.raise_for_status()  # Verifica se houve algum erro na requisição
        return resposta.json()  # Retorna os dados no formato JSON
    except requests.exceptions.RequestException as e:
        print("Erro ao obter os dados da API:", e)

url='https://apiprevmet3.inmet.gov.br/avisos/ativos'
dados = obter_dados_api(url)

#criar lista vazia
lista_avisos_rs = []

# procura rs na lista de estados de cada aviso
for aviso in dados['hoje']:
  if 'Rio Grande do Sul' in  aviso['estados']:
    lista_avisos_rs.append(aviso)

lista_avisos_rs

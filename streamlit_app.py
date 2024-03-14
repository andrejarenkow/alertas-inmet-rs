# Importação de bibliotecas
import pandas as pd
import geopandas as gpd
import plotly.express as px
import streamlit as st
import plotly.graph_objects as go
import requests
import folium
from streamlit_folium import st_folium, folium_static
import requests
import json
import geojson
from datetime import datetime

# Configurações da página
st.set_page_config(
    page_title="Alertas INMET - RS",
    page_icon=":warning:",
    layout="wide",
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

# Link para acesso a todos os avisos ativos
url='https://apiprevmet3.inmet.gov.br/avisos/ativos'
dados = obter_dados_api(url)

#criar lista vazia
lista_avisos_rs = []

# procura rs na lista de estados de cada aviso
for aviso in dados['hoje']:
  if 'Rio Grande do Sul' in  aviso['estados']:
    lista_avisos_rs.append(aviso)

# Função para formatar a data corretamente
def formatar_data(data_a_ser_formatada):

  # Converter para objeto datetime
  data_obj = datetime.strptime(data_a_ser_formatada, "%Y-%m-%dT%H:%M:%S.%fZ")

  # Formatar para o formato desejado
  data_formatada = data_obj.strftime("%d/%m/%Y")

  return data_formatada

#Função para adicionar a CRS no aviso
def crs_no_aviso(aviso):

  lista_municipios = aviso['geocodes'].split(',')
  valores_comecando_com_43 = [int(valor[:6]) for valor in lista_municipios if valor.startswith('43')]
  lista_crs = sorted(municipios_crs[municipios_crs['IBGE6'].isin(valores_comecando_com_43)]['CRS'].unique())
  aviso['crs'] = ','.join(str(item) for item in lista_crs)
  aviso['data_inicio_formatado'] = formatar_data(lista_avisos_rs[0]['data_inicio'])
  aviso['data_fim_formatado'] = formatar_data(lista_avisos_rs[0]['data_fim'])

  return aviso

# Cria lista vazia para armazenar as features
lista_features = []

# Percorre a lista de avisos para criar as features
for aviso in lista_avisos_rs:
  crs_no_aviso(aviso)
  feature = geojson.Feature(geometry=json.loads(aviso['poligono']), properties=aviso)
  lista_features.append(feature)

# Cria um FeatureCollection com os objetos Feature
feature_collection = geojson.FeatureCollection(lista_features)

# Converte para string JSON
geojson_str = geojson.dumps(feature_collection, sort_keys=True)

# Mapa
# Criar um objeto de mapa
mapa = folium.Map(location=[-29.481856994459644, -52.763236352888136], zoom_start=6)

# Criar popup
popup = folium.GeoJsonPopup(fields=["descricao", 'severidade', 'data_inicio_formatado', 'data_fim_formatado', 'crs'],
                            aliases=['Tipo de alerta', 'Grau de severidade', 'Data de início', 'Data de fim', 'CRS afetadas'],
                            style="""
                                      background-color: #F0EFEF;
                                      border: 2px solid black;
                                      border-radius: 3px;
                                      box-shadow: 3px;
                                  """
                            )

# Adicionar o GeoJSON ao mapa
folium.GeoJson(geojson_str,
               style_function=lambda feature: {
                "fillColor": feature["properties"]["aviso_cor"],
                "color": "black",
                "weight": 1,
               'fillOpacity':0.4},
               highlight_function=lambda feature: {
                "fillColor": feature["properties"]["aviso_cor"],
                "color": "black",
                "weight": 3,
               'fillOpacity':0.6
                },
               popup=popup
                 ).add_to(mapa)

coluna_mapa, coluna_descricao = st.columns(2)
with coluna_mapa:
    # Exibindo o Mapa
    st_data = st_folium(mapa, width=725)

with coluna_descricao:
    try:
        propriedades = st_data['last_active_drawing']['properties']
        crs = propriedades['crs']
        data_hora_inicio = f" {propriedades['data_inicio_formatado']} - {propriedades['hora_inicio']} "
        data_hora_fim = f"{propriedades['data_fim_formatado']} - {propriedades['hora_fim']}"
        descricao = propriedades['descricao']
        instrucoes = propriedades['instrucoes']
        riscos = propriedades['riscos']
        severidade = propriedades['severidade']
        texto = f"""
        VIGIDESASTRES - PROGRAMA NACIONAL DE VIGILÂNCIA EM SAÚDE DOS RISCOS ASSOCIADOS AOS DESASTRES

Prezados(as), 
 
INMET publica aviso alertando sobre {riscos}. O cenário possibilita a ocorrência de eventos como, alagamentos, enxurradas, movimento de massa e outros desastres associados.  
 
**Aviso de:** {descricao}

**Grau de severidade:** {severidade} 

**Início:** {data_hora_inicio} 

**Fim:** {data_hora_fim} 

**CRS Afetadas:** {crs}

Alertas disponíveis no link: https://alertas2.inmet.gov.br/46712
 
**Recomendações:**  
{instrucoes}

**Encaminhamentos:** Realizado contato com o ponto focal do Estado para ciência do risco.
Na ocorrência do evento, solicitamos maiores informações sobre os impactos e estamos à disposição para apoiar na gestão da emergência.
        """
        st.markdown(texto)

    except:
        st.write('Clique em algum aviso para ver as informações')
    
    

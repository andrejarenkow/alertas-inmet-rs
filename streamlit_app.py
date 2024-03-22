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
import urllib.parse
import urllib.request
import re
import contextily as ctx
import matplotlib.pyplot as plt
import base64

# Configurações da página
st.set_page_config(
    page_title="Alertas INMET - RS",
    page_icon=":warning:",
    layout="wide",
    initial_sidebar_state='collapsed'
)
col1, col2, col3 = st.columns([1,1,4])

col1.image('https://github.com/andrejarenkow/csv/blob/master/logo_cevs%20(2).png?raw=true', width=100)
col2.image('https://github.com/andrejarenkow/csv/blob/master/logo_estado%20(3)%20(1).png?raw=true', width=200)
col3.title('Vigidesastres RS - Alertas INMET')

# Importação dos dados
municipios_crs = pd.read_csv('https://raw.githubusercontent.com/andrejarenkow/csv/master/Munic%C3%ADpios%20RS%20IBGE6%20Popula%C3%A7%C3%A3o%20CRS%20Regional%20-%20P%C3%A1gina1.csv')

# Geodataframe CRS
geojson_crs = gpd.read_file('https://raw.githubusercontent.com/andrejarenkow/geodata/main/RS_por_CRS/RS_por_CRS.json')

# Importação shape CRS
with urllib.request.urlopen("https://raw.githubusercontent.com/andrejarenkow/geodata/main/RS_por_CRS/RS_por_CRS.json") as url:
  rs_municipios = json.loads(url.read().decode())

# Seleção tempo avisos
tempo = st.radio('Selecione o período desejado', options=['hoje', 'futuro'])

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
for aviso in dados[tempo]:
  if 'Rio Grande do Sul' in  aviso['estados']:
    lista_avisos_rs.append(aviso)

if len(lista_avisos_rs)==0:
    st.subheader('Nenhum alerta para o Rio Grande do Sul')

else:
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
      aviso['crs'] = ', '.join(str(item) for item in lista_crs)
      aviso['riscos'] = '. '.join(str(item) for item in aviso['riscos'])
      aviso['instrucoes'] = '. '.join(str(item) for item in aviso['instrucoes'])
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
    mapa = folium.Map(location=[-30.510000000000, -53.8000000000], zoom_start=6)
    
    # Adicionando as CRS
    folium.GeoJson(rs_municipios,
                   style_function=lambda feature: {
                    "fillColor": 'black',
                    "color": "grey",
                    "weight": 0.8,
                   'fillOpacity':0},
                   ).add_to(mapa)
    
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
                   'fillOpacity':0.3},
                   highlight_function=lambda feature: {
                    "fillColor": feature["properties"]["aviso_cor"],
                    "color": "black",
                    "weight": 3,
                   'fillOpacity':0.6
                    },
                   popup=popup,
                   popup_keep_highlighted=True
                     ).add_to(mapa)
    
    coluna_mapa, coluna_descricao = st.columns(2)
    with coluna_mapa:
        # Exibindo o Mapa
        st_data = st_folium(mapa, width=500, height=450)
    
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
    
            #Geração da imagem que vai pelo whatsapp
            gdf = gpd.read_file(propriedades['poligono'])
                    
            # Crie uma figura e um eixo para o mapa
            fig, ax = plt.subplots(figsize=(10, 10))
            
            # Ajuste os limites do eixo x e y para os limites desejados
            ax.set_xlim(-58, -49)
            ax.set_ylim(-34.5, -26.5)
            
            # Plote o GeoDataFrame no mapa com o fundo do OpenStreetMap
            gdf.plot(ax=ax, facecolor='none', edgecolor=propriedades['aviso_cor'], linewidth=1.0, hatch='////')
            # Plote o segundo GeoDataFrame filtrado no mesmo mapa
            geojson_crs.plot(ax=ax, facecolor='none', edgecolor='grey', linewidth=1.0)
            ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, crs=gdf.crs.to_string())
            
            # Adicione títulos, legendas, etc., conforme necessário
            plt.title(f'Alerta de {descricao}, de {data_hora_inicio} até {data_hora_fim}.')
            plt.xlabel('Longitude')
            plt.ylabel('Latitude')
            
            # Salve a figura como uma imagem PNG
            imagem_path = 'Alerta.png'
            plt.savefig(imagem_path, dpi=100)
    
            # Codificar a imagem em base64 para anexar ao texto
            #with open(imagem_path, "rb") as image_file:
            #    encoded_string = base64.b64encode(image_file.read()).decode()
    
            
            texto = f"""
         *VIGIDESASTRES RS - PROGRAMA NACIONAL DE VIGILÂNCIA EM SAÚDE DOS RISCOS ASSOCIADOS AOS DESASTRES*
         
    Prezados(as), 
                 
    INMET publica aviso alertando sobre {riscos}   
                 
    *Aviso de:* {descricao}
                
    *Grau de severidade:* {severidade} 
                
    *Início:* {data_hora_inicio} 
                
    *Fim:* {data_hora_fim} 
                
    *CRS Afetadas:* {crs}
                           
    *Recomendações:*  {instrucoes}
               
    *Encaminhamentos:* Realizado contato com o ponto focal do Estado para ciência do risco.
    Na ocorrência do evento, solicitamos maiores informações sobre os impactos e estamos à disposição para apoiar na gestão da emergência.
    
    Fonte: https://alertas2.inmet.gov.br/
            """
            st.markdown(texto)
            
    
                  
            # Codificar o texto do link
            texto_codificado = urllib.parse.quote(texto)
    
            # Gerar o link para o WhatsApp
            link_whatsapp = f"https://wa.me/?text={texto_codificado}"
            
            # HTML para o botão de compartilhamento do WhatsApp
            html_button = f'<a href="{link_whatsapp}" target="_blank"><img src="https://cdn-icons-png.flaticon.com/512/3670/3670051.png" width="50" height="50"></a>'
    
            # Exibir o botão no Streamlit
            st.markdown(html_button, unsafe_allow_html=True)
            st.image(imagem_path)
            
            
        except:
            st.write('Clique na área de interesse e aguarde para obter informações sobre alertas.')

import streamlit as st
import pandas as pd
import psycopg2 as sql
from funciones.funciones import *

st.set_page_config(page_title="Datos Cliente", page_icon="📝")

# Set the background image
background()

# set sidebar
sidebar()

# text format
text1 = "<{h} style='text-align: left; color: #000058;'>{txt}</{h}>"
text2 = '<span style="color:#000058">**{txt}:** {value}</span>'
text3 = '<span style="color:#000058">{txt}</span>'

# main screen
col1, col2 = st.columns(2)
with col1:
  formato(string=text1, h='h1', txt="Vicepresidencia de Estrategia y Administración🔎")
  formato(string=text1, h='h3', txt='Control de Gestión')
  
with col2:
  st.image('static/banplus2.png',use_column_width = True)
  
col1, col2, col3 = st.columns(3)

with col1:
  formato(string=text1, h='h4', txt='Nombre Cliente:')
  
with col2:
  if 'razon_soc' in st.session_state:
    formato(string=text1, h='h4', txt=st.session_state['razon_soc'])
  else:
    formato(string=text1, h='h4', txt='➖')

with col3:
  if 'RIF' in st.session_state:
    formato(string=text1, h='h4', txt='#️⃣RIF: {rif}'.format(rif=st.session_state['RIF']))
  else:
    formato(string=text1, h='h4', txt='#️⃣RIF:➖')
    
# data base connection
@st.cache_resource
def init_connection():
  db="vikua"
  db_host="172.16.201.11" #10.212.134.9
  db_user="usr_vikua_db"
  db_pass="Vikua2024"
  return sql.connect(host=db_host, database=db, user=db_user, password=db_pass)
conn = init_connection()

# validacion de rif para realizar la consulta
if 'RIF' in st.session_state:
  # datos a mostrar
  campos=['Región','Gerente Ejecutivo','Oficina',
          'Grupo Económico','Telefono','Mail','Mail Accionista']
        
  # resultados de consulta de datos del cliente
  dato_empresa = client_info(st.session_state['RIF'], conn)
  if 'mail' in st.session_state:
    dato_empresa['Mail'] = st.session_state['mail']

  # resultados datos de marcaje
  formato(string=text1, h='h4', txt='📝Datos de Marcaje y Contacto')
  with st.container(border=True):
    for k in campos:
      value = dato_empresa.get(k, 'N/A')
      formato(string=text2, txt=k, value=value)

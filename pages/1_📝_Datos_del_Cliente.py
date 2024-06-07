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
conn = st.connection("postgresql", type="sql")

# validacion de rif para realizar la consulta
if 'RIF' in st.session_state:
  # datos a mostrar
  campos=['Región','Gerente Ejecutivo','Oficina',
          'Grupo Económico','Telefono','Mail','Mail Accionista']
        
  # consulta de datos
  # diccionario para almacenar los resultados de datos de marcaje y contacto
  result = {}

  query1 = '''
      select
        trim(ci_rif) as RIF,
        región as Región,
        gerente_ejecutivo as Gerente_Ejecutivo,
        oficina as Oficina,
        grupoeconómico as Grupo_Económico
      from
        region
      where
        ci_rif = cast({rif} AS TEXT)'''

  query1 = query1.format(rif = st.session_state['RIF'])
  df_contact = conn.query(query1, ttl="10m")
  
  if not df_contact.empty:
    for item in df_contact:
      field = item.replace('_', ' ')
      field = field.title()
      value = df_contact.drop_duplicates().loc[df_contact.index[0], item]
      try:
        value = value.lower()
        value = value.title()
      except:
        value = 'N/A'
      if field not in result:
        result[field] = value
        
  query2 = '''
  select
      trim(table1.c020mail) as mail_accionista,
      concat(cast(table1.c020area AS TEXT), cast(trim(table1.c020telm) AS TEXT)) as telefono
    from
      dcclf020 table1
    where
      trim(table1.c000ndoc) in (
        select
          trim(table2.c011ndoc)
        from
          dcclf011 table2
        where
          trim(table2.c000ndoc) = cast({rif} AS TEXT)
          )'''

  query2 = query2.format(rif = st.session_state['RIF'])
  df_contact2 = conn.query(query2, ttl='10m')
  
  if not df_contact2.empty:
    for item in df_contact2:
      field = item.replace('_', ' ')
      field = field.title()
      value = list(df_contact2[item].drop_duplicates())
      try:
        value = [i.lower() for i in value]
        value = [i.title() for i in value]
        value = ', '.join(value)
      except:
        value = 'N/A'
      if field not in result:
        result[field] = value
        
  if 'mail' in st.session_state:
    result['Mail'] = st.session_state['mail']

  # resultados datos de marcaje
  formato(string=text1, h='h4', txt='📝Datos de Marcaje y Contacto')
  with st.container(border=True):
    for k in campos:
      value = result.get(k, 'N/A')
      formato(string=text2, txt=k, value=value)

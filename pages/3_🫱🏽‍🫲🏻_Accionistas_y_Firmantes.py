import streamlit as st
import psycopg2 as sql
import pandas as pd
import numpy as np
from funciones.funciones import *

st.set_page_config(page_title="Accionistas y Firmantes", page_icon="👨‍💼")

# Set the background image
background()

# format
text1 = "<{h} style='text-align: left; color: #000058;'>{txt}</{h}>"
text2 = '<span style="color:#000058">**{txt}** {value}</span>'
text3 = '<span style="color:#000058">{txt}</span>'

# set sidebar
sidebar()

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

# condicion para realizar consulta
if 'RIF' in st.session_state:
  query='''
  CREATE TEMPORARY TABLE temp_table as
    select
        distinct trim(c000ndoc) as rif,
        trim(c011ndoc) as cedula,
        case when c011pacc > 0 THEN 1 ELSE 0 END as Acci,
        c011pacc as prop_acci
      from
        dcclf011
      where
        trim(c000ndoc) = cast({RIF} AS TEXT) '''
  query = query.format(RIF=st.session_state['RIF'])
  cur = conn.cursor()
  cur.execute(query)
  
  query='''
  select
      distinct table1.rif,
      table1.cedula,
      concat(
        trim(table2.c020nom1),' ',trim(table2.c020nom4)
        ) as nombre,
      case when trim(table3.c036ndfi) IS NULL THEN 0 ELSE 1 END as fir,
      table1.acci,
      table1.prop_acci
    from
      temp_table table1
    left join
      dcclf020 table2 on table1.cedula = trim(table2.c000ndoc)
    left join
      dcclf036 table3 on table1.cedula = trim(table3.c036ndfi)'''
      
  base_firm = pd.read_sql(query, conn)
  cur.execute("DROP TABLE temp_table")
  
  # mostramos resultado de consulta de firmantes de la empresa
  if not base_firm.empty:
    formato(string=text1, h='h4', txt='🖋️ Firmantes de la Empresa')
    with st.container(border=True):
      col1, col2, col3, col4 = st.columns(4)
      with col1:
        formato(string=text1, h='h4', txt='Nombre')
        for name in base_firm['nombre'].to_list():
          formato(string=text2, txt = name.strip().title())
      with col2:
        formato(string=text1, h='h4', txt='Cedula')
        for ci in base_firm['cedula'].to_list():
          formato(string=text2, txt = ci)
      with col3:
        formato(string=text1, h='h4', txt='Firmante')
        for n in base_firm['fir'].to_list():
          if bool(n):
            formato(string=text2, txt = 'Si')
          else:
            formato(string=text2, txt = 'No')
      with col4:
        formato(string=text1, h='h4', txt='% Acciones')
        for acc in base_firm['prop_acci'].to_list():
          if acc > 0:
            formato(string=text2, txt=str(acc)+'%')
          else:
            formato(string=text2, txt=str(acc))
  else:
    formato(string=text1, h='h4', txt='Sin información para #️⃣RIF: {}'.format(st.session_state['RIF']))

# consulta de cliente para saber si firma en alguna empresa
st.write('\n')
st.write('\n')

col1, col2 = st.columns(2)
with col1:
  formato(string=text1, h='h3', txt='Consulta de Cliente')
formato(string=text3, txt='Para consultar empresas asociadas al cliente ingrese numero de cedula')

with st.container(border=True):
  col1, col2 = st.columns(2)
  formato(string=text1, h='h4', txt='Cliente a Consultar ⬇️')
  
  col1, col2, col3 = st.columns(3)
  with col1:
    CI = st.text_input('')
    CI.strip()
  
  # condicion para guardar la cedula en la sesion y realizar consulta
  if CI:
    if len(CI) > 0 and CI.isnumeric():
      st.session_state['CI'] = CI
    else:
      formato(string=text1, h='h4', txt='⛔ Numero de Cedula: {CI} invalido, Ingrese solo numero'.format(CI=CI))
  
  if 'CI' in st.session_state:
    query='''
    select
        distinct trim(table1.c000ndoc) as rif,
        trim(table1.c011ndoc) as ci,
        concat(
        trim(table4.c020nom1),' ', trim(table4.c020nom4)
        ) as nombre_cliente,
        trim(table2.c010rsoc) as nombre_empresa,
        case when trim(table3.c036ndfi) IS NULL THEN 0 ELSE 1 END as fir,
        case when table1.c011pacc > 0 THEN 1 ELSE 0 END as acc,
        table1.c011pacc as porcen_acc
      from
        dcclf011 table1
      left join
        dcclf010 table2 on trim(table1.c000ndoc) = trim(table2.c000ndoc)
      left join
        dcclf036 table3 on trim(table1.c011ndoc) = trim(table3.c036ndfi)
      left join
        dcclf020 table4 on  trim(table1.c011ndoc) = trim(table4.c000ndoc)
      where
        trim(table1.c011ndoc) = cast({CI} AS TEXT)'''
        
    query = query.format(CI=st.session_state['CI'])
    base_firm_client = pd.read_sql(query, conn)
    
    if not base_firm_client.empty:
      try:
        nombre = base_firm_client['nombre_cliente'].iloc[0]
        nombre = nombre.title()
      except:
        nombre='Desconocido'
      formato(string=text1, h='h4', txt='Cliente: '+nombre)
      
      # mostramos los resultados
      df = base_firm_client[['nombre_empresa', 'rif', 'fir', 'porcen_acc']]
      df['nombre_empresa'] = df['nombre_empresa'].str.title()
      df['fir'] = df['fir'].transform(lambda x: 'Si' if x == 1 else 'No')
      df['porcen_acc'] = df['porcen_acc'].transform(lambda x: str(x)+'%' if x>0 else str(x))
      st.dataframe(
        df,
        column_config={'nombre_empresa': 'Empresa','rif':'RIF','fir':'Firmante','porcen_acc': '% Acciones'})

import streamlit as st
import psycopg2 as sql
import pandas as pd
import numpy as np
import sqlalchemy
from funciones.funciones import *

# comando para correr app in terminal -> streamlit run 📌_Inicio.py

st.set_page_config(
  page_title="Dashboard Banplus",
  page_icon="💳",
)

# Set the background image
background()

# format
text1 = "<{h} style='text-align: left; color: #000058;'>{txt}</{h}>"
text2 = '<span style="color:#000058">**{txt}** {value}</span>'
text3 = '<span style="color:#000058">{txt}</span>'

# set sidebar
sidebar()
reset = st.sidebar.button("⏹️Reset", type="primary")

# main sreen
col1, col2 = st.columns(2)
with col1:
  formato(string=text1, h='h1', txt="Vicepresidencia de Estrategia y Administración🔎")
  formato(string=text1, h='h3', txt='Control de Gestión')
  formato(string=text1, h='h4', txt='Ingrese un RIF ⬇️')

with col2:
  st.image('static/banplus2.png',use_column_width = True)
  
col1, col2, col3 = st.columns(3)
with col1:
  RIF = st.text_input('')
  RIF.strip()
  
# data base connection
conn = st.connection("postgresql", type="sql")

# condicion para guardar el rif en la sesion para demas consultas en otros modulos
if RIF:
  if len(RIF) > 0 and RIF.isnumeric():
    st.session_state['RIF'] = RIF
  else:
    formato(string=text1, h='h4', txt='⛔ Numero de RIF: {} invalido, Ingrese solo numero '.format(RIF))
    for key in st.session_state.keys():
      del st.session_state[key]  

if reset:
  for key in st.session_state.keys():
    del st.session_state[key]

# condicion para realizar consultas correspondientes
if 'RIF' in st.session_state:
  # razon social y email del cliente
  query = '''
  select
      distinct trim(c010rsoc) as razon_soc,
      trim(c010mail) as mail
    from
      dcclf010
    join (
      values (cast({txt} AS TEXT))
    ) t(id) on t.id = trim(c000ndoc)'''
  query = query.format(txt = st.session_state['RIF'])
  info_cli = conn.query(query, ttl="10m")
  col1, col2 = st.columns(2)
  
  # obtenemos el nombre o razon social y lo guardamos como variable en la sesion
  try:
    razon_soc = info_cli.loc[0,'razon_soc'].title()
    st.session_state['razon_soc'] = razon_soc
    with col1:
      formato(string=text1, h='h4', txt=razon_soc)
    with col2:
      n_rif='#️⃣RIF: {rif}'.format(rif=st.session_state['RIF'])
      formato(string=text1, h='h4', txt=n_rif)
  except:
    if 'razon_soc' in st.session_state:
      del st.session_state['razon_soc']
    with col1:
      formato(string=text1, h='h4', txt='Sin información de nombre del cliente')
    with col2:
      formato(string=text1, h='h4', txt='#️⃣RIF: {rif}'.format(rif=st.session_state['RIF']))
  
  # obtenemos el mail y lo guardamos como variable en la sesion
  try:
    mail = info_cli.loc[0,'mail'].title()
    st.session_state['mail'] = mail
  except:
    if 'mail' in st.session_state:
      del st.session_state['mail']
  
  # obtenemos el codigo cliente
  try:
    query = '''
      select
        trim(c001cli) as cod_cliente
      from
        dcclf006
      join(
        values (cast({txt} AS TEXT))
        ) t(id) on t.id = trim(c006ndoc)'''
    query = query.format(txt = st.session_state['RIF'])
    cod_cli = conn.query(query, ttl="10m")
    st.session_state['cod_cli'] = cod_cli.iloc[0,0]
    # cuentas del cliente
    query = '''
    select
        g300uuid as key,
        trim(g300prod) as cod_producto
      from
        dgscf300
      join (
        values (cast({txt} AS TEXT))
      ) t(id) on t.id = trim(g300cli)'''
    query = query.format(txt = st.session_state['cod_cli'])
    
    cuentas_cli = conn.query(query, ttl="10m")
    
    # tabla de codigos producto
    cod_prod = conn.query('select cod_producto, cuenta from cod_productos;', ttl="10m")
    
    # obtenemos los productos del cliente (cuenta bs, cuenta m1, cuenta divisa plus)
    cuentas_cli = cuentas_cli.merge(cod_prod, how='left', on='cod_producto')
    
    cuentas_cli = cuentas_cli.query("cuenta != 'otro'").dropna()
    
    with st.container(border=True):
      col1, col2, col3 = st.columns(3)
      with col1:
        formato(string=text1, h='h4', txt='Productos')
      with col2:
        formato(string=text1, h='h4', txt='Status')
      with col3:
        formato(string=text1, h='h4', txt='Leyenda')
        formato(string=text3, txt='Tiene Producto 🟢')
        formato(string=text3, txt="No Tiene Producto ➖")
    
      type_cuenta = ('cuenta_bs', 'cuenta_m1', 'divisa_plus')
      for cuenta in type_cuenta:
        if cuenta in list(cuentas_cli['cuenta']):
          with col1:
            formato(string=text2, txt = cuenta.replace('_', ' ').title())
          with col2:
            st.write("🟢")
        else:
          with col1:
            formato(string=text2, txt = cuenta.replace('_', ' ').title())
          with col2:
            st.write("➖")
    
    # guardamos los productos del cliente en la sesion
    st.session_state['cuentas_cli'] = cuentas_cli
    # Consultas productos y servicios: proveedores, pago nomina, pos, intervencion
    # oferta, demanda, bolpriaven, seniat, encargos de confianza
    
    # extraemos el monto total de la operacion (pago nomina, seniat, intervencion, ...)
    # del cliente que se esta consultando
    query='''
    select
        cod_producto,
        monto_total
      from
        monto_ser
      join (
        values (cast({cod_cli} AS TEXT))
      ) t(id) on t.id = cod_cliente'''
      
    query = query.format(cod_cli = st.session_state['cod_cli'])
    client_prod = conn.query(query,ttl="10m")
    
    # tabla catalogo
    base_catalogo = conn.query('select * from catalogo',ttl="10m")
    base_catalogo = base_catalogo.rename(columns={"Producto.Negocio": "ProductoNegocio"})
    
    # de la tabla catalogo filtro codigos de productos de interes
    prod_neg = ['Nomina', 'Bolpriaven']
    prod = ['Pago Proveedores', 'Encargo de Confianza', 'Seniat']
    key_words = ['Intervencion','oferta','demanda']
    tesoreria = base_catalogo.loc[(base_catalogo['ProductoNegocio'] == 'Tesoreria'), ['Producto']]
    prod += [item for key in key_words for item in list(tesoreria['Producto']) if key in item]
    query = "ProductoNegocio in {prod_neg} or Producto in {prod}".format(prod_neg=prod_neg, prod=prod)
    df_prod = base_catalogo.query(query)[['Concatenado','ProductoNegocio', 'Producto']]
    # campo donde se identifica tipo de operacion
    df_prod['clase'] = np.where(df_prod['ProductoNegocio'].isin(prod_neg), df_prod['ProductoNegocio'],
                                np.where(df_prod['Producto'].isin(prod[0:3]), df_prod['Producto'], 
                                          np.where(df_prod['Producto'].str.contains('oferta'), 'Oferta',
                                                    np.where(df_prod['Producto'].str.contains('demanda'), 'Demanda',
                                                              'Intervencion') ) ) )
                                                              
    client_prod = client_prod.merge(df_prod, how='left', left_on='cod_producto', right_on='Concatenado')
    client_prod = client_prod.dropna()
    client_prod = client_prod.groupby('clase').sum('monto_total')
    # guardamos el uso de servivios del cliente en la sesion
    st.session_state['client_prod'] = client_prod    
    
    with st.container(border=True):
      col1, col2, col3 = st.columns(3)
      with col1:
        formato(string=text1, h='h4', txt='Servicios')
      with col2:
        formato(string=text1, h='h4', txt='Status')
      with col3:
        formato(string=text1, h='h4', txt='Leyenda')
        formato(string=text3, txt='Hizo uso del servicio 🟢')
        formato(string=text3, txt="No hizo uso del servicio ➖")
    
      services = sorted(df_prod['clase'].unique())
      for service in services:
        if client_prod.filter(regex = service, axis = 0).empty:
          with col1:
            formato(string=text2, txt = service)
          with col2:
            st.write("➖") 
        else:
          with col1:
            formato(string=text2, txt = service)
          with col2:
            st.write("🟢")  
    # consultamos region y la guardamos en la sesion
    query = '''
        select
          región as region
        from
          region
        where
          ci_rif = cast({rif} AS TEXT)'''
    query = query.format(rif = st.session_state['RIF'])
    region = conn.query(query,ttl="10m")
    st.session_state['region'] = region.iloc[0,0]
  except:
    formato(string=text1, h='h4', txt='Sin información de Productos/Servicios #️⃣RIF: {}'.format(st.session_state['RIF']))
    for var in ['cod_cli','cuentas_cli','client_prod','region']:
      if var in st.session_state:
        del st.session_state[var]

else:
  formato(string=text1, h = 'h5', txt='Nota: RIF de prueba para consultar: 402137826 246644108 298101105 298643986')

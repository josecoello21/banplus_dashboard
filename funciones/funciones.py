import streamlit as st
import pandas as pd

# set background image
def background():
  background_image = """
  <style>
    [data-testid="stAppViewContainer"] > .main {
    background-image: url("https://www.solidbackgrounds.com/images/3840x2160/3840x2160-pastel-blue-solid-color-background.jpg");
    background-size: 100vw 100vh;  # This sets the size to cover 100% of the viewport width and height
    background-position: left;  
    background-repeat: no-repeat;
    }
  </style>"""
  st.markdown(background_image, unsafe_allow_html=True)
  
# set sidebar
def sidebar():
  st.sidebar.success('## Seleccione una opción️ ⬆️')
  st.sidebar.image('static/banplus1.png', caption='Dashboard Banplus Banco Universal')

# format
def formato(string, h='h1', txt='', value=''):
  return st.markdown(string.format(h=h, txt=txt, value=value), unsafe_allow_html=True)

# function to get key id client
def cod_cliente(rif = '', conn=None):
  query = '''
  select
    trim(c001cli) as cod_cliente
  from
    dcclf006
  join(
    values (cast({txt} AS TEXT))
  ) t(id) on t.id = trim(c006ndoc)'''
  
  # cur object using DB connection
  cur = conn.cursor()
  query = query.format(txt = rif)
  cur.execute(query)
  cod_cliente = cur.fetchall()
  return cod_cliente[0][0]


# function for info client module
def client_info(rif, conn):
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

  query1 = query1.format(rif = rif)
  df_contact = pd.read_sql(query1, conn)

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

  query2 = query2.format(rif = rif)
  df_contact2 = pd.read_sql(query2, conn)

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

  return result
  


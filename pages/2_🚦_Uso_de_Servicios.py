import streamlit as st
import pandas as pd
import datetime
import psycopg2 as sql
from funciones.funciones import *

# streamlit run 📌_Inicio.py

st.set_page_config(page_title="Productos y Servicios", page_icon="🚦")

# Set the background image
background()

# set sidebar
sidebar()

# text format
text1 = "<{h} style='text-align: left; color: #000058;'>{txt}</{h}>"
text2 = '<span style="color:#000058">**{txt}** {value}</span>'
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
    
col1, col2, col3 = st.columns(3)
with col1:
  formato(string=text1, h='h4', txt='Región:')
if 'region' in st.session_state:
  with col2:
    formato(string=text1, h='h4', txt = st.session_state['region'].title())
else:
  with col2:
    formato(string=text1, h='h4', txt='➖')

# data base connection
@st.cache_resource
def init_connection():
  db="vikua"
  db_host="172.16.201.11" #10.212.134.9
  db_user="usr_vikua_db"
  db_pass="Vikua2024"
  return sql.connect(host=db_host, database=db, user=db_user, password=db_pass)
conn = init_connection()

# configuracion de valores para construir slider user input fecha
fecha = datetime.datetime.now()
mes = fecha.month
year = fecha.year

if mes == 1:
  meses = list(range(1,13))
  years = [year-1]*12
else:
  meses = list(range(mes,13))+list(range(1,mes))
  years = [year-1]*len(range(mes,13)) + [year]*len(range(1,mes))
  
start = datetime.datetime(years[0],meses[0],1)
end = datetime.datetime(years[-1],meses[-1],1)
rango = (datetime.datetime(years[-3],meses[-3],1), datetime.datetime(years[-1],meses[-1],1))

# condicion para realizar la consulta de cuentas (el rif ingresado debe tener asociada cuentas con el banco)
if 'cuentas_cli' in st.session_state:
  # slider user input date
  col1, col2 = st.columns(2)
  with col1:
    st.write('\n')
    st.write('\n')
    st.write('\n')
    formato(string=text1, h='h5', txt='📅Rango fecha a consultar')
    time = st.slider('',start, end, rango, format="YYYY/MM/DD")

  # rango seleccionado
  mes_ini = time[0].month
  mes_fin = time[1].month
  
  if mes_ini<=mes_fin:
    select_month = meses[meses.index(mes_ini):(meses.index(mes_fin)+1)]
  else:
    select_month = meses[meses.index(mes_ini):(meses.index(12)+1)] + meses[meses.index(1):(meses.index(mes_fin)+1)]
  
  # meses a seleccionar en la consulta a la tabla dvcvf003
  my_function = lambda x: 'v003dp0{x} as saldo_0{x}'.format(x=str(x)) if x<10 else 'v003dp{x} as saldo_{x}'.format(x=str(x))
  saldo_fields = list(map(my_function , select_month))
  saldo_fields = ', '.join(saldo_fields)
  key = list(st.session_state['cuentas_cli']['key'])
  key = map(lambda x: "('{x}')".format(x = x), key)
  key = ', '.join(key)
  # consulta de saldos del cliente en sus cuentas con el banco
  query = '''
  select
      v001uuid as key,
      {saldo_fields}
    from
      dvcvf003
    join (
      values {txt}
    ) t(id) on t.id = v001uuid'''
    
  query = query.format(saldo_fields=saldo_fields, txt=key)
  saldos = pd.read_sql(query, conn)
  cuentas_cli = st.session_state['cuentas_cli'].merge(saldos, how='left', on='key')
  
  var_saldo = saldo_fields.split(' ')
  var_saldo = list(filter(lambda x: 'saldo' in x, var_saldo))
  var_saldo = [i.replace(',','') for i in var_saldo]
  
  cuentas_cli = cuentas_cli.groupby('cuenta').sum(var_saldo)
  cuentas_cli = cuentas_cli.reset_index()
  cuentas_cli = cuentas_cli.melt(id_vars='cuenta', var_name='mes', value_name='saldo')
  cuentas_cli = cuentas_cli.groupby('cuenta')['saldo'].mean()
  cuentas_cli = cuentas_cli.reset_index()
  
  # consulta de saldos en la region asociada al cliente para comparacion
  var_saldo2 = ', '.join(var_saldo)
  query = '''
  select
      region,
      cuenta,
      {saldos}
    from
      saldos_region
    where
      region = cast('{region}' AS TEXT)'''
  query=query.format(saldos=var_saldo2, region=st.session_state['region'])
  saldos_region=pd.read_sql(query, conn)
  saldos_region=saldos_region[['cuenta']+var_saldo].melt(id_vars='cuenta', var_name='mes', value_name='saldo')
  saldos_region=saldos_region.groupby('cuenta').mean('saldo')
  saldos_region=saldos_region.reset_index()
  
  # consulta del producto POS para anexar el resultado
  try:
    # consulta de facturacion POS cliente
    mes = list(map(lambda x: str(int(x[-2:])), var_saldo))
    mes = list(map(lambda x: "'{x}'".format(x=x), mes))
    mes = ', '.join(mes)
    query='''
    select
        substring(rif, 3, 20) as rif,
        mes,
        region,
        avg(cast(mto_trs AS NUMERIC)) as monto_tx
      from
        pos
      where
        substring(rif, 3, 20) = cast({rif} AS TEXT) and mes in ({mes})
      group by
        substring(rif, 3, 20), mes, region'''.format(rif=st.session_state['RIF'], mes=mes)
        
    pos_client = pd.read_sql(query, conn)
    pos_client = pos_client.groupby('region')['monto_tx'].mean()
    pos_client = pos_client.reset_index()
    
    if not pos_client.empty:
      cuentas_cli.loc[len(cuentas_cli.index)] = ['p o s', pos_client.iloc[0,1]]
    
    # facturacion POS region
    query='''
    select
        mes,
        region,
        avg(cast(mto_trs AS NUMERIC)) as monto_tx
      from
        pos
      where
        region = cast('{region}' AS TEXT) and mes in ({mes})
      group by
        mes, region'''.format(region=st.session_state['region'], mes=mes)
    
    pos_region = pd.read_sql(query, conn)
    pos_region = pos_region.groupby('region')['monto_tx'].mean()
    pos_region = pos_region.reset_index()
    
    if pos_region.empty:
      saldos_region.loc[len(saldos_region.index)] = ['p o s', 0]
    else:
      saldos_region.loc[len(saldos_region.index)] = ['p o s', pos_region.iloc[0,1]]
  
  except:
    pass
  
  # comparacion saldos cliente vs saldos promedio region
  def semaforo(df_cli, df_reg, column, col_saldo):
    color = {}
    for var in df_reg[column].to_list():
      try:
        if df_cli.loc[(df_cli[column] == var),col_saldo].iloc[0] >= df_reg.loc[(df_reg[column] == var),col_saldo].iloc[0]:
          color[var] = 'green'
        elif df_cli.loc[(df_cli[column] == var),col_saldo].iloc[0] < 1:
          color[var] = 'red'
        else:
          color[var] = 'yellow'
      except:
        color[var] = 'grey'
    return color
  
  resultado = semaforo(cuentas_cli, saldos_region, 'cuenta', 'saldo')
  
  # orden a mostrar
  green, yellow, red, grey = [],[],[],[]
  for k,v in resultado.items():
    if v=='green':
      green.append(k)
    elif v=='yellow':
      yellow.append(k)
    elif v=='red':
      red.append(k)
    else:
      grey.append(k)
  green.sort()
  yellow.sort()
  red.sort()
  grey.sort()
  order_product = green+yellow+red+grey
    
  with st.container(border=True):
    col1, col2, col3 = st.columns(3)
    with col1:
      formato(string=text1, h='h4', txt='Productos')
    with col2:
      formato(string=text1, h='h4', txt='Saldo Cliente')
    with col3:
      formato(string=text1, h='h4', txt='Saldo Región')
    
    for k in order_product:
      key = k.replace('_', ' ').title()
      with col1:
        if resultado[k]=='green':
          formato(string=text2, txt = key+' {color}'.format(color='🟢'))
        elif resultado[k]=='yellow':
          formato(string=text2, txt = key+' {color}'.format(color='🟡'))
        elif resultado[k]=='red':
          formato(string=text2, txt = key+' {color}'.format(color='🔴'))
        else:
          formato(string=text2, txt = key+' {color}'.format(color='➖'))
      with col2:
        try:
          value = cuentas_cli.loc[(cuentas_cli['cuenta'] == k), 'saldo'].iloc[0]
          value = int(round(value,0))
          value = f"{value:,d}"
          formato(string=text2, txt=value)
        except:
          formato(string=text2, txt='')
      with col3:
        try:
          value = saldos_region.loc[(saldos_region['cuenta'] == k), 'saldo'].iloc[0]
          value = int(round(value,0))
          value = f"{value:,d}"
          formato(string=text2, txt=value)
        except:
          formato(string=text2, txt='N/A')
    
    # leyenda
    formato(string=text1, h='h4', txt='Leyenda')
    col1, col2 = st.columns(2)
    with col1:
      formato(string=text3, txt='Saldo Cliente >= Saldo Región 🟢')
      formato(string=text3, txt='Saldo Cliente = 0 🔴')
    with col2:  
      formato(string=text3, txt='Saldo Cliente < Saldo Región 🟡')
      formato(string=text3, txt='No Tiene Producto ➖')
    
    
# condicion para realizar la consulta de servicios (el codigo de cliente debe aparecer en la tabla transacciones)
if 'client_prod' in st.session_state:
  # tabla comparativo por region para elaboracion del semaforo
  query='''
  select *
      from tabla_uso'''
  tabla_uso = pd.read_sql(query, conn)
  tabla_uso = tabla_uso.fillna(0)
  try:
    # filtramos por la region del cliente
    tabla_uso = tabla_uso.loc[(tabla_uso['region'] == st.session_state['region'])]
    tabla_uso = tabla_uso.loc[:, tabla_uso.columns!='region']
    tabla_uso = tabla_uso.melt(var_name='clase', value_name='monto_total')
    client_prod = st.session_state['client_prod']
    client_prod = client_prod.reset_index()
    
    # comparativo de montos de servicios cliente vs la region
    resultado = semaforo(client_prod, tabla_uso, 'clase', 'monto_total')
    
    # orden a mostrar
    green, yellow, red, grey = [],[],[],[]
    for k,v in resultado.items():
      if v=='green':
        green.append(k)
      elif v=='yellow':
        yellow.append(k)
      elif v=='red':
        red.append(k)
      else:
        grey.append(k)
    green.sort()
    yellow.sort()
    red.sort()
    grey.sort()
    order_service = green+yellow+red+grey  
    
    # mostrar resultados en el front
    with st.container(border=True):
      col1, col2, col3 = st.columns(3)
      with col1:
        formato(string=text1, h='h4', txt='Servicios')
      with col2:
        formato(string=text1, h='h4', txt='Monto Cliente')
      with col3:
        formato(string=text1, h='h4', txt='Monto Región')
      
      for k in order_service:
        with col1:
          if resultado[k]=='green':
            formato(string=text2, txt = k+' {color}'.format(color='🟢'))
          elif resultado[k]=='yellow':
            formato(string=text2, txt = k+' {color}'.format(color='🟡'))
          elif resultado[k]=='red':
            formato(string=text2, txt = k+' {color}'.format(color='🔴'))
          else:
            formato(string=text2, txt = k+' {color}'.format(color='➖'))
        with col2:
          try:
            value = client_prod.loc[(client_prod['clase'] == k), 'monto_total'].iloc[0]
            value = int(round(value,0))
            value = f"{value:,d}"
            formato(string=text2, txt=value)
          except:
            formato(string=text2, txt='')
        with col3:
          value = tabla_uso.loc[(tabla_uso['clase'] == k), 'monto_total'].iloc[0]
          value = int(round(value,0))
          value = f"{value:,d}"
          formato(string=text2, txt=value)
      # leyenda
      formato(string=text1, h='h4', txt='Leyenda')
      col1, col2 = st.columns(2)
      with col1:
        formato(string=text3, txt='Monto Cliente >= Monto Región 🟢')
        formato(string=text3, txt='Monto Cliente = 0 🔴')
      with col2:  
        formato(string=text3, txt='Monto Cliente < Monto Región 🟡')
        formato(string=text3, txt='Sin uso de Servicio ➖')  
  except:
    with st.container(border=True):
      formato(string=text2, txt='Región del cliente no coincide con ninguna región en la tabla')

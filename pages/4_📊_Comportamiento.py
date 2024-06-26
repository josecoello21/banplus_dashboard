import streamlit as st
import calendar
import datetime
import numpy as np
import pandas as pd
# pip install plotly==5.22.0
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from funciones.funciones import *

st.set_page_config(page_title="Datos Cliente", page_icon="📊", layout="wide")

# margin top
st.markdown("<style> div[class^='block-container'] { padding-top: 2rem; } </style>", 
            unsafe_allow_html=True)

# set footer
footer = """<style>.footer {
  position: fixed; left: 0.2; bottom: 0; width: 100%; height: 5%;
  background:linear-gradient(to right, #69be28, #bed600);
  float:left;}
  .size{
    width:6vw;
    height:5vh;
    float: left;
    margin-top: 1px;
    margin-bottom: 1px;
    margin-left: 20px;}
  </style>
  <div class='footer'><p><img class='size' src="https://storage.googleapis.com/vikua-styles/banplus-styles/logo_banplus_blanco.png"/></p>
  </div>
"""
st.markdown(footer, unsafe_allow_html=True)

# set sidebar
sidebar()

# text format
text1 = "<{h} style='text-align: left; color: #00204E;'>{txt}</{h}>"
text2 = '<span style="color:#00204E">**{txt}:** {value}</span>'
text3 = '<span style="color:#00204E">{txt}</span>'

# main screen
col1, col2 = st.columns(2)
with col1:
  st.image('https://storage.googleapis.com/vikua-styles/banplus-styles/banplus2.png')
with col2:
  header = """
  <style>.img{
    float: right;
  }
  </style>
  <p><img class = 'img' src='https://storage.googleapis.com/vikua-styles/banplus-styles/header.jpg'></p>"""
  st.markdown(header, unsafe_allow_html=True)
  
st.title("Tablero de Control de Gestión")
  
col1, col2, col3 = st.columns(3)

with col1:
  formato(string=text1, h='h4', txt='Uso de Productos y Servicios')
  
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

# condicion para realizar graficos de saldos promedios
if 'cuentas_cli' in st.session_state:
  # hidden footer
  hide_footer_style = """
  <style>
  .footer {
  display: none;
  }
  </style>
  """
  st.markdown(hide_footer_style, unsafe_allow_html=True)
  
  # configuracion de valores para consulta de saldos
  fecha = datetime.datetime.now()
  mes = fecha.month
  year = fecha.year

  if mes == 1:
    meses = list(range(1,13))
    years = [year-1]*12
  else:
    meses = list(range(mes,13))+list(range(1,mes))
    years = [year-1]*len(range(mes,13)) + [year]*len(range(1,mes))
    
  # meses a seleccionar en la consulta a la tabla dvcvf003
  my_function = lambda x: 'v003dp0{x} as saldo_0{x}'.format(x=str(x)) if x<10 else 'v003dp{x} as saldo_{x}'.format(x=str(x))
  saldo_fields = list(map(my_function , meses))
  saldo_fields = ', '.join(saldo_fields)
  key = list(st.session_state['cuentas_cli']['key'])
  key = list(map(lambda x: "('{x}')".format(x = x), key))
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
  saldos = conn.query(query, ttl='10m')
  cuentas_cli = st.session_state['cuentas_cli'].merge(saldos, how='left', on='key')
  
  var_saldo = saldo_fields.split(' ')
  var_saldo = list(filter(lambda x: 'saldo' in x, var_saldo))
  var_saldo = [i.replace(',','') for i in var_saldo]
  
  cuentas_cli = cuentas_cli.groupby('cuenta')[var_saldo].sum()
  cuentas_cli = cuentas_cli.reset_index()
  cuentas_cli = cuentas_cli.melt(id_vars='cuenta', var_name='mes', value_name='saldo')
  
  # seleccion de periodos en que se desea mostrar las graficas
  col1, col2, col3, col4 = st.columns(4)
  with col1:
    st.write('\n')
    period = st.selectbox(r"$\textsf{\large Periodo de tiempo a consultar}$",
    ("Mensual","Trimestral","Cuatrimestral","Semestral"), placeholder="Mensual")
  
  # configuracion de graficas
  if period:
    if period == 'Mensual':
      col = meses
    elif period == 'Trimestral':
      col = [4,3,2,1]*3
      col.sort(reverse=True)
    elif period == 'Cuatrimestral':
      col = [3,2,1]*4
      col.sort(reverse=True)
    else:
      col = [1,2]*6
      col.sort(reverse=True)
      period='Semestral'
    # almacenamos los datos para de cada una de las cuentas para las graficas en un diccionario  
    dic_cuenta = {}
    n_cuenta = cuentas_cli['cuenta'].unique()
    for cuenta in n_cuenta:
      df = cuentas_cli.loc[(cuentas_cli['cuenta'] == cuenta), ]
      new_cols = {'mes':meses, 'period':col, 'year':years}
      df = df.assign(**new_cols)
      if period == 'Mensual':
        df['meses'] = df.groupby('period')['mes'].transform(
        lambda x: '{Mes}'.format(Mes=calendar.month_abbr[list(x)[0]])
        ) + df.year.astype(str)
        df = df.groupby(['period', 'meses'])['saldo'].mean()
        df = df.reset_index()
        df = df.set_index('period')
        df = df.loc[col]
        df['saldo'] = df['saldo'].round(0)
        dic_cuenta[cuenta] = df
      else:
        df['meses'] = df.groupby('period')['mes'].transform(
        lambda x: '{Min}-{Max}'.format(Min=calendar.month_abbr[list(x)[0]],Max=calendar.month_abbr[list(x)[-1]])
        )
        df = df.groupby(['period', 'meses'])['saldo'].mean()
        df = df.reset_index()
        df = df.set_index('period')
        col2 = [col.index(i) for i in np.unique(col)]
        col2.reverse()
        col2 = np.array(col)[[col2]]
        df = df.loc[list(col2[0])]
        df['saldo'] = df['saldo'].round(0)
        dic_cuenta[cuenta] = df
  #plots
  col1, col2 = st.columns(2)
  height=350
  with col1:
    try:
      title='Saldo Promedio {period} Cuenta Bs'.format(period=period)
      fig = px.bar(dic_cuenta['cuenta_bs'], x='meses', y='saldo', text_auto='.2s')
      fig.update_traces(marker_color='rgb(0,152,219)')
      fig.update_layout(title_text=title, title_x=0.5, title_xanchor='center', 
                        title_font_style='italic', title_font_weight='bold',
                        xaxis_title="Meses", yaxis_title="Saldo promedio en Bs",
                        height=height)
      st.plotly_chart(fig)
    except:
      title='No posee Cuenta Bs'
      df2 = pd.DataFrame({'meses': df.meses.to_list(), 'saldo': 0}, index = df.index)
      fig = px.bar(df2, x='meses', y='saldo', text_auto='.2s')
      fig.update_traces(marker_color='rgb(0,152,219)')
      fig.update_layout(title_text=title, title_x=0.5, title_xanchor='center', 
                        title_font_style='italic', title_font_weight='bold',
                        xaxis_title="Meses", yaxis_title="Saldo promedio en Bs",
                        height=height)
      st.plotly_chart(fig)
  with col2:
    try:
      if set(['divisa_plus', 'cuenta_m1']).issubset(set(n_cuenta)):
        # para grafica en divisas unimos cuenta m1 y cuenta divisas plus en una sola grafica
        divisas = {'meses': df['meses'].to_list(),
                   'Cuenta M1': dic_cuenta['cuenta_m1']['saldo'].to_list(),
                   'Divisa Plus': dic_cuenta['divisa_plus']['saldo'].to_list()}
        div_df = pd.DataFrame(data=divisas)
        div_df = div_df.melt(id_vars='meses', var_name='cuenta', value_name='saldo')
        title = 'Saldo Promedio {period} en Divisas'.format(period=period)
        fig = px.bar(div_df, x="meses", y="saldo", color="cuenta", text_auto='.2s', 
                     color_discrete_sequence=['rgb(105,190,40)', 'rgb(0,152,219)'])
        fig.update_layout(title_text=title, title_x=0.5, title_xanchor='center', 
                          title_font_style='italic', title_font_weight='bold', 
                          legend_title_font_weight='bold', 
                          legend_title_side='top right', xaxis_title="Meses", 
                          yaxis_title="Saldo prom. Divisas", height=height)
        st.plotly_chart(fig)
      elif 'cuenta_m1' in dic_cuenta:
        title='Saldo Promedio {period} Cuenta M1'.format(period=period)
        fig = px.bar(dic_cuenta['cuenta_m1'], x='meses', y='saldo', text_auto='.2s', title=title)
        fig.update_traces(marker_color='rgb(105,190,40)')
        fig.update_layout(title_text=title, title_x=0.5, title_xanchor='center', 
                          title_font_style='italic', title_font_weight='bold',
                          xaxis_title="Meses", yaxis_title="Saldo prom. Divisas",height=height)
        st.plotly_chart(fig)
      elif 'divisa_plus' in dic_cuenta:
        title='Saldo Promedio {period} Divisa Plus'.format(period=period)
        fig = px.bar(dic_cuenta['divisa_plus'], x='meses', y='saldo', text_auto='.2s', title=title)
        fig.update_traces(marker_color='rgb(105,190,40)')
        fig.update_layout(title_text=title, title_x=0.5, title_xanchor='center', 
                          title_font_style='italic', title_font_weight='bold',
                          xaxis_title="Meses", yaxis_title="Saldo prom. Divisas",height=height)
        st.plotly_chart(fig)
    except:
      title='No posee Cuenta en Divisas'
      df2 = pd.DataFrame({'meses': df.meses.to_list(), 'saldo': 0}, index = df.index)
      fig = px.bar(df2, x='meses', y='saldo', text_auto='.2s')
      fig.update_traces(marker_color='rgb(105,190,40)')
      fig.update_layout(title_text=title, title_x=0.5, title_xanchor='center', 
                        title_font_style='italic', title_font_weight='bold',
                        xaxis_title="Meses", yaxis_title="Saldo prom. Divisas",height=height)
      st.plotly_chart(fig)
      
# condicion para realizar graficos de facturacion POS
if 'POS' in st.session_state:
  pos_client = st.session_state['POS']
  m = ",".join(map(lambda x: "'{x}'".format(x=x), meses))
  pos_client = pos_client.query('mes in ({meses})'.format(meses=m))
  # informacion de total puntos de venta y cuantos estan en uso
  info_pos = pos_client[['numpos', 'cant_trs']].groupby('numpos')['cant_trs'].sum().reset_index()
  info_pos['total_pos'] = len(info_pos.numpos.unique())
  info_pos['pos_activo'] = np.sum(info_pos.cant_trs.apply(lambda x: x!=0))
  #pos_client = pos_client[['mes','monto_tx']].groupby('mes')['monto_tx'].mean()
  pos_client = pos_client.groupby('mes')[['cant_trs','monto_tx']].sum()
  idx = pos_client.index.to_list()
  # dt_ls = pos_client.to_list()
  dt_ls = pos_client.monto_tx.to_list()
  df_can = pos_client.cant_trs.to_list()
  for i in range(1,13):
    if not str(i) in idx:
      idx.append(str(i))
      dt_ls.append(0)
      df_can.append(0)
  # pos_client = pd.DataFrame(dt_ls, df_can, index = idx)
  pos_client = pd.DataFrame({'monto_tx':dt_ls, 'cant_trs':df_can}, index = idx)
  pos_client = pos_client.loc[map(lambda x: str(x), meses)].reset_index()
  new_cols = {'mes':meses, 'period':col, 'year':years}
  pos_client = pos_client.assign(**new_cols)
  # pos_client = pos_client.rename(columns={0:'monto_tx'})
  if period == 'Mensual':
    pos_client['meses'] = pos_client.groupby('period')['mes'].transform(
    lambda x: '{Mes}'.format(Mes=calendar.month_abbr[list(x)[0]])
    ) + pos_client.year.astype(str)
    # pos_client = pos_client.groupby(['period', 'meses'])['monto_tx'].mean()
    pos_client = pos_client.groupby(['period', 'meses'])[['monto_tx','cant_trs']].sum()
    pos_client = pos_client.reset_index()
    pos_client = pos_client.set_index('period')
    pos_client = pos_client.loc[col]
    pos_client['monto_tx'] = pos_client['monto_tx'].round(0)
  else:
    pos_client['meses'] = pos_client.groupby('period')['mes'].transform(
    lambda x: '{Min}-{Max}'.format(Min=calendar.month_abbr[list(x)[0]],Max=calendar.month_abbr[list(x)[-1]])
    )
    # pos_client = pos_client.groupby(['period', 'meses'])['monto_tx'].mean()
    pos_client = pos_client.groupby(['period', 'meses'])[['monto_tx','cant_trs']].sum()
    pos_client = pos_client.reset_index()
    pos_client = pos_client.set_index('period')
    col2 = [col.index(i) for i in np.unique(col)]
    col2.reverse()
    col2 = np.array(col)[[col2]]
    pos_client = pos_client.loc[list(col2[0])]
    pos_client['monto_tx'] = pos_client['monto_tx'].round(0)
  # plot POS
  height=420
  try:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=pos_client.meses, y=pos_client.cant_trs, name="Nro de Transacciones", mode="lines+markers+text", 
                  line=dict(color="#00204e"), text=[f'{int(i):,}'for i in pos_client.cant_trs.to_list()], 
                  textfont=dict(color="#00204e"), marker=dict(symbol="arrow-bar-down"),
                  textposition="top right"),secondary_y=True)
    fig.add_trace(go.Bar(x=pos_client.meses, y=pos_client.monto_tx, name="Monto en Bs", text = [f'Bs {round(i,0):,}' for i in pos_client.monto_tx.to_list()], 
                  marker_color='#0098db'),secondary_y=False)
    fig.update_xaxes(title_text="Mes", type='category')
    title='Facturación Total {period} POS'.format(period=period)
    fig.update_layout(title_text=title, title_x=0.5, title_xanchor='center', 
                      title_font_weight='bold',
                      xaxis_title="Meses", yaxis_title="Facturación Total Bs",
                      height=height)
    st.plotly_chart(fig)
    # title='Facturación Promedio {period} POS'.format(period=period)
    # fig = px.bar(pos_client, x='meses', y='monto_tx', text_auto='.2s')
    # fig.update_traces(marker_color='rgb(0,38,78)')
    # fig.update_layout(title_text=title, title_x=0.5, title_xanchor='center', 
    #                   title_font_style='italic', title_font_weight='bold',
    #                   xaxis_title="Meses", yaxis_title="Facturación promedio Bs",
    #                   height=height)
    # st.plotly_chart(fig)
    # formato(string=text2, txt = 'Total POS', value=info_pos.iloc[0,2])
    # formato(string=text2, txt = 'POS en uso', value=info_pos.iloc[0,3])
  except:
    title='Sin registro de Facturación POS'
    df2 = pd.DataFrame({'meses': df.meses.to_list(), 'monto_tx': 0}, index = df.index)
    fig = px.bar(df2, x='meses', y='monto_tx', text_auto='.2s')
    fig.update_traces(marker_color='rgb(0,38,78)')
    fig.update_layout(title_text=title, title_x=0.5, title_xanchor='center', 
                      title_font_style='italic', title_font_weight='bold',
                      xaxis_title="Meses", yaxis_title="Facturación promedio Bs",height=height)
    st.plotly_chart(fig)
    formato(string=text2, txt = 'Total POS', value=info_pos.iloc[0,2])
    formato(string=text2, txt = 'POS en uso', value=info_pos.iloc[0,3])
    
if 'client_prod' in st.session_state:
  height=350
  df_dep_ret = st.session_state['client_prod'].loc[(st.session_state['client_prod'].clase.str.contains('Depositos ')) | (st.session_state['client_prod'].clase.str.contains('Retiro '))]
  df_dep_ret['fecha2'] = pd.to_datetime(df_dep_ret.fecha, format="%Y/%m/%d") - datetime.timedelta(days=1)
  df_dep_ret['Días'] = df_dep_ret.fecha2.apply(lambda x: calendar.day_name[x.weekday()])
  df_dep_ret['Moneda'] = np.where(df_dep_ret.clase.str.contains('Divisas'), 'Divisas', 'Bs')
  df_dep_ret_plot = df_dep_ret.loc[(df_dep_ret['Días'].isin(['Monday','Tuesday','Wednesday','Thursday','Friday']))]
  #plot
  fig = px.histogram(df_dep_ret_plot, x = 'Días', y='monto_total', color='clase', barmode='group', facet_col='Moneda',
                     category_orders={"Días": ['Monday','Tuesday','Wednesday','Thursday','Friday'],
                                      "Moneda":['Bs', 'Divisas']},
                     color_discrete_sequence=['rgb(105,190,40)', 'rgb(0,152,219)'], text_auto='.2s')
  fig.update_xaxes(labelalias=dict(Monday='Lunes', Tuesday='Martes', Wednesday='Miercoles', Thursday='Jueves', Friday='Viernes'))
  fig.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))
  fig.update_layout(title_text='Comp. Semanal Distribución de Depósitos y Retiros en Bs y Divisas', 
                   title_x=0.5, title_xanchor='center',title_font_weight='bold',height=height)
  st.plotly_chart(fig)
  
  # with st.container(border=True):
  #   formato(string=text1, h='h3', txt='Saldo Promedio (Cuenta Bs, Cuenta M1 y Divisa Plus)')
  #   col1, col2 = st.columns(2)
  #   with col1:
  #     try:
  #       title='Saldo Promedio {period} Cuenta Bs'.format(period=period)
  #       fig = px.bar(dic_cuenta['cuenta_bs'], x='meses', y='saldo', text_auto='.2s')
  #       fig.update_traces(marker_color='red')
  #       fig.update_layout(title_text=title, title_x=0.5, title_xanchor='center', 
  #                         title_font_style='italic', title_font_weight='bold',
  #                         xaxis_title="Meses", yaxis_title="Saldo promedio en Bs")
  #       st.plotly_chart(fig)
  #     except:
  #       formato(string=text1, h='h4', txt='No posee Cuenta en Bs')
  #   with col2:
  #     try:
  #       if set(['divisa_plus', 'cuenta_m1']).issubset(set(n_cuenta)):
  #         # para grafica en divisas unimos cuenta m1 y cuenta divisas plus en una sola grafica
  #         divisas = {'meses': df['meses'].to_list(),
  #                    'Cuenta M1': dic_cuenta['cuenta_m1']['saldo'].to_list(),
  #                    'Divisa Plus': dic_cuenta['divisa_plus']['saldo'].to_list()}
  #         div_df = pd.DataFrame(data=divisas)
  #         div_df = div_df.melt(id_vars='meses', var_name='cuenta', value_name='saldo')
  #         title = 'Saldo Promedio {period} en dolares'.format(period=period)
  #         fig = px.bar(div_df, x="meses", y="saldo", color="cuenta", text_auto='.2s', 
  #                      color_discrete_sequence=['rgb(0, 200, 0)', 'rgb(0, 0, 200)'])
  #         fig.update_layout(title_text=title, title_x=0.5, title_xanchor='center', 
  #                           title_font_style='italic', title_font_weight='bold', 
  #                           legend_title_font_weight='bold', 
  #                           legend_title_side='top right', xaxis_title="Meses", yaxis_title="Saldo Promedio en $")
  #         st.plotly_chart(fig)
  #       elif 'cuenta_m1' in dic_cuenta:
  #         title='Saldo Promedio {period} Cuenta M1'.format(period=period)
  #         fig = px.bar(dic_cuenta['cuenta_m1'], x='meses', y='saldo', text_auto='.2s', title=title)
  #         fig.update_traces(marker_color='green')
  #         fig.update_layout(title_text=title, title_x=0.5, title_xanchor='center', 
  #                           title_font_style='italic', title_font_weight='bold',
  #                           xaxis_title="Meses", yaxis_title="Saldo promedio en $")
  #         st.plotly_chart(fig)
  #       elif 'divisa_plus' in dic_cuenta:
  #         title='Saldo Promedio {period} Divisa Plus'.format(period=period)
  #         fig = px.bar(dic_cuenta['divisa_plus'], x='meses', y='saldo', text_auto='.2s', title=title)
  #         fig.update_traces(marker_color='green')
  #         fig.update_layout(title_text=title, title_x=0.5, title_xanchor='center', 
  #                           title_font_style='italic', title_font_weight='bold',
  #                           xaxis_title="Meses", yaxis_title="Saldo promedio en $")
  #         st.plotly_chart(fig)
  #     except:
  #       formato(string=text1, h='h4', txt='No posee Cuenta en $')
        

      
      # # comprobamos si el cliente tiene cuenta m1 y divisa+
      # formato(string=text1, h='h3', txt='Saldo Promedio (Cuenta Bs, Cuenta M1 y Divisa Plus)')
      # if set(['divisa_plus', 'cuenta_m1']).issubset(set(n_cuenta)):
      #   # si cliente tiene cuenta bs realizamos grafica en bs
      #   if 'cuenta_bs' in dic_cuenta:
      #     title='Saldo Promedio {period} Cuenta Bs'.format(period=period)
      #     fig = px.bar(dic_cuenta['cuenta_bs'], x='meses', y='saldo', text_auto='.2s')
      #     fig.update_traces(marker_color='rgb(255,0,0)')
      #     fig.update_layout(title_text=title, title_x=0.5, title_xanchor='center', 
      #                       title_font_style='italic', title_font_weight='bold',
      #                       xaxis_title="Meses", yaxis_title="Saldo promedio en Bs")
      #     st.plotly_chart(fig)
      #   
      #   # para grafica en divisas unimos cuenta m1 y cuenta divisas plus en una sola grafica
      #   divisas = {'meses': df['meses'].to_list(),
      #              'Cuenta M1': dic_cuenta['cuenta_m1']['saldo'].to_list(),
      #              'Divisa Plus': dic_cuenta['divisa_plus']['saldo'].to_list()}
      #   div_df = pd.DataFrame(data=divisas)
      #   div_df = div_df.melt(id_vars='meses', var_name='cuenta', value_name='saldo')
      #   title = 'Saldo Promedio {period} en dolares'.format(period=period)
      #   fig2 = px.bar(div_df, x="meses", y="saldo", color="cuenta", text_auto='.2s', title=title)
      #   fig2.update_layout(title_text=title, title_x=0.5, title_xanchor='center', 
      #                     title_font_style='italic', title_font_weight='bold', 
      #                     legend_title={'cuenta': 'Cuenta'}, legend_title_font_weight='bold', 
      #                     legend_title_side='top right', xaxis_title="Meses", yaxis_title="Saldo promedio en $")
      #   st.plotly_chart(fig2)
      # else:
      #   if 'cuenta_bs' in dic_cuenta:
      #     title='Saldo Promedio {period} Cuenta Bs'.format(period=period)
      #     fig = px.bar(dic_cuenta['cuenta_bs'], x='meses', y='saldo', text_auto='.2s', title=title)
      #     fig.update_traces(marker_color='rgb(255,0,0)')
      #     fig.update_layout(title_text=title, title_x=0.5, title_xanchor='center', 
      #                       title_font_style='italic', title_font_weight='bold',
      #                       xaxis_title="Meses", yaxis_title="Saldo promedio en Bs")
      #     st.plotly_chart(fig)
      #   if 'cuenta_m1' in dic_cuenta:
      #     title='Saldo Promedio {period} Cuenta M1'.format(period=period)
      #     fig = px.bar(dic_cuenta['cuenta_m1'], x='meses', y='saldo', text_auto='.2s', title=title)
      #     fig.update_traces(marker_color='green')
      #     fig.update_layout(title_text=title, title_x=0.5, title_xanchor='center', 
      #                       title_font_style='italic', title_font_weight='bold',
      #                       xaxis_title="Meses", yaxis_title="Saldo promedio en $")
      #     st.plotly_chart(fig)
      #   if 'divisa_plus' in dic_cuenta:
      #     title='Saldo Promedio {period} Divisa Plus'.format(period=period)
      #     fig = px.bar(dic_cuenta['divisa_plus'], x='meses', y='saldo', text_auto='.2s', title=title)
      #     fig.update_traces(marker_color='green')
      #     fig.update_layout(title_text=title, title_x=0.5, title_xanchor='center', 
      #                       title_font_style='italic', title_font_weight='bold',
      #                       xaxis_title="Meses", yaxis_title="Saldo promedio en $")
      #     st.plotly_chart(fig)

# condicion para realizar graficos de facturacion POS
# if 'POS' in st.session_state:
#   pos_client = st.session_state['POS']
#   m = ",".join(map(lambda x: "'{x}'".format(x=x), meses))
#   pos_client = pos_client.query('mes in ({meses})'.format(meses=m))
#   # informacion de total puntos de venta y cuantos estan en uso
#   info_pos = pos_client[['numpos', 'cant_trs']].groupby('numpos')['cant_trs'].sum().reset_index()
#   info_pos['total_pos'] = len(info_pos.numpos.unique())
#   info_pos['pos_activo'] = np.sum(info_pos.cant_trs.apply(lambda x: x!=0))
#   
#   pos_client=pos_client[['mes','numpos','monto_tx']].groupby(['mes','numpos'])['monto_tx'].mean()
#   pos_client=pos_client.reset_index()
#   pos_client['numpos']=pos_client.numpos.apply(lambda x: 'POS#{x}'.format(x = x))
#   pos_client=pos_client.pivot_table(values='monto_tx', index='mes', columns='numpos')
#   pos_client=pos_client.fillna(0)
#   pos_client=pos_client.loc[map(lambda x: str(x), meses)].reset_index()
#   pos_client = pos_client.assign(**new_cols)
#   
#   if period == 'Mensual':
#     pos_client['meses'] = pos_client.groupby('period')['mes'].transform(
#     lambda x: '{Mes}'.format(Mes=calendar.month_abbr[list(x)[0]])
#     ) + pos_client.year.astype(str)
#     pos_client=pos_client.melt(id_vars=['mes','meses','period', 'year'], var_name='POS', value_name='monto_tx')
#     pos_client = pos_client.groupby(['meses','period','POS'])['monto_tx'].mean()
#     pos_client = pos_client.reset_index()
#     pos_client = pos_client.set_index('period')
#     pos_client = pos_client.loc[col]
#     pos_client['monto_tx'] = pos_client['monto_tx'].round(0)
#   else:
#     pos_client['meses'] = pos_client.groupby('period')['mes'].transform(
#     lambda x: '{Min}-{Max}'.format(Min=calendar.month_abbr[list(x)[0]],Max=calendar.month_abbr[list(x)[-1]])
#     )
#     pos_client=pos_client.melt(id_vars=['mes','meses','period', 'year'], var_name='POS', value_name='monto_tx')
#     pos_client = pos_client.groupby(['meses','period','POS'])['monto_tx'].mean()
#     pos_client = pos_client.reset_index()
#     pos_client = pos_client.set_index('period')
#     col2 = [col.index(i) for i in np.unique(col)]
#     col2.reverse()
#     col2 = np.array(col)[[col2]]
#     pos_client = pos_client.loc[list(col2[0])]
#     pos_client['monto_tx'] = pos_client['monto_tx'].round(0)
#   
#   # plot POS
#   with st.container(border=True):
#     formato(string=text1, h='h3', txt='Punto de Venta (P O S)')
#     col1, col2, col3, col4 = st.columns(4)
#     with col1:
#       formato(string=text2, txt = 'Total POS', value=info_pos.iloc[0,2])
#     with col2:
#       formato(string=text2, txt = 'POS en uso', value=info_pos.iloc[0,3])
#     
#     col1,col2 = st.columns(2)
#     with col1:
#       title='Facturación POS Promedio {period}'.format(period=period)
#       fig = px.bar(pos_client, x="meses", y="monto_tx", color="POS", text_auto='.2s', 
#                    color_discrete_sequence=px.colors.colorbrewer.Accent())
#       #fig.update_traces(marker_color=px.colors.colorbrewer.Accent)
#       fig.update_layout(title_text=title, title_x=0.5, title_xanchor='center', 
#                             title_font_style='italic', title_font_weight='bold', 
#                             legend_title_font_weight='bold', 
#                             legend_title_side='top right', xaxis_title="Meses", yaxis_title="Monto promedio en Bs")
#       st.plotly_chart(fig)
  
  
  # pos_client = pos_client[['mes','monto_tx']].groupby('mes')['monto_tx'].mean()
  # pos_client = pos_client.loc[map(lambda x: str(x), meses)].reset_index()
  # pos_client = pos_client.assign(**new_cols)
  # if period == 'Mensual':
  #   pos_client['meses'] = pos_client.groupby('period')['mes'].transform(
  #   lambda x: '{Mes}'.format(Mes=calendar.month_abbr[list(x)[0]])
  #   ) + pos_client.year.astype(str)
  #   pos_client = pos_client.groupby(['period', 'meses'])['monto_tx'].mean()
  #   pos_client = pos_client.reset_index()
  #   pos_client = pos_client.set_index('period')
  #   pos_client = pos_client.loc[col]
  #   pos_client['monto_tx'] = pos_client['monto_tx'].round(0)
  # else:
  #   pos_client['meses'] = pos_client.groupby('period')['mes'].transform(
  #   lambda x: '{Min}-{Max}'.format(Min=calendar.month_abbr[list(x)[0]],Max=calendar.month_abbr[list(x)[-1]])
  #   )
  #   pos_client = pos_client.groupby(['period', 'meses'])['monto_tx'].mean()
  #   pos_client = pos_client.reset_index()
  #   pos_client = pos_client.set_index('period')
  #   col2 = [col.index(i) for i in np.unique(col)]
  #   col2.reverse()
  #   col2 = np.array(col)[[col2]]
  #   pos_client = pos_client.loc[list(col2[0])]
  #   pos_client['monto_tx'] = pos_client['monto_tx'].round(0)
  #   
  # # plot POS
  # with st.container(border=True):
  #   formato(string=text1, h='h3', txt='Punto de Venta (P O S)')
  #   col1, col2, col3, col4 = st.columns(4)
  #   with col1:
  #     formato(string=text2, txt = 'Total POS', value=info_pos.iloc[0,2])
  #   with col2:
  #     formato(string=text2, txt = 'POS en uso', value=info_pos.iloc[0,3])
  #   
  #   title='Facturación POS Promedio {period}'.format(period=period)
  #   fig = px.bar(pos_client, x='meses', y='monto_tx', text_auto='.2s')
  #   fig.update_traces(marker_color='rgb(0,0,255)')
  #   fig.update_layout(title_text=title, title_x=0.5, title_xanchor='center', 
  #                           title_font_style='italic', title_font_weight='bold',
  #                           xaxis_title="Meses", yaxis_title="Monto promedio en Bs")
  #   st.plotly_chart(fig)
#st.write(st.session_state) 
  
  
  
  
  
  
  

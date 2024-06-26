import streamlit as st
from streamlit_extras.app_logo import add_logo

# set footer
def footer():
  # Set footer
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
  return st.markdown(footer, unsafe_allow_html=True)
  
# set sidebar
def sidebar():
  add_logo("https://storage.googleapis.com/vikua-styles/banplus-styles/logo_vikua_es_dark.png", height=172)
  st.sidebar.success('### Seleccione una opción️ ⬆️')
  st.markdown("<style> div[class^='css-1544g2n'] { padding-top: 1.5rem; } </style> ", unsafe_allow_html=True)
  #st.logo('static/banplus1.png', icon_image='static/banplus2.png')

# format
def formato(string, h='h1', txt='', value=''):
  return st.markdown(string.format(h=h, txt=txt, value=value), unsafe_allow_html=True)

import streamlit as st

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

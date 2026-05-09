import streamlit as st
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Norte Imagen - Registro", layout="centered")

# Estilo personalizado (Burgundy)
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .stButton>button { background-color: #800020; color: white; border-radius: 5px; }
    h1 { color: #800020; }
    </style>
    """, unsafe_allow_globals=True)

st.title("🏥 Registro de Paciente - Norte Imagen")

# 1. CARGA DEL ARCHIVO CSV 
# Forzamos el separador a ';' para que la ',' de la fila 57 se tome como texto.
try:
    # Probamos primero con punto y coma (común en Excel regional)
    df = pd.read_csv('listado_prestaciones.csv', sep=';', engine='python')
    
    # Si por alguna razón el punto y coma no separa nada (solo hay 1 columna), 
    # intentamos con la coma estándar
    if df.shape[1] < 2:
        df = pd.read_csv('listado_prestaciones.csv', sep=',', engine='python')

    # Limpieza de espacios en los nombres de columnas
    df.columns = df.columns.str.strip()

    if 'Especialidad' in df.columns and 'Prestación' in df.columns:
        
        with st.form("formulario_paciente"):
            col1, col2 = st.columns(2)
            with col1:
                rut = st.text_input("RUT del Paciente")
                nombre = st.text_input("Nombre Completo")
            with col2:
                fecha = st.date_input("Fecha", datetime.now())
                email = st.text_input("Email de contacto")

            st.divider()

            # Selección de especialidad
            especialidades = df['Especialidad'].dropna().unique()
            esp_seleccionada = st.selectbox("Seleccione Especialidad", especialidades)

            # Filtrar prestaciones
            lista_prestaciones = df[df['Especialidad'] == esp_seleccionada]['Prestación'].tolist()
            prestacion_final = st.selectbox("Seleccione el Examen/Prestación", lista_prestaciones)

            comentarios = st.text_area("Observaciones adicionales")

            enviado = st.form_submit_button("Generar Ficha")

            if enviado:
                if not rut or not nombre:
                    st.error("Por favor, complete los datos obligatorios.")
                else:
                    st.success(f"Ficha de {nombre} lista para procesar.")
    else:
        st.error(f"Columnas detectadas: {list(df.columns)}. Se necesitan 'Especialidad' y 'Prestación'.")

except Exception as e:
    st.error(f"Error al leer el archivo: {e}")
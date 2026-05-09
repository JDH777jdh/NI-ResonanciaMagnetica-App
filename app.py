import streamlit as st
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Norte Imagen - Registro", layout="centered")

# Estilo personalizado compatible
st.markdown("""
    <style>
    .stApp { background-color: #f5f5f5; }
    .stButton>button { background-color: #800020; color: white; border-radius: 5px; }
    h1 { color: #800020; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏥 Registro de Paciente - Norte Imagen")

# CARGA DEL ARCHIVO CSV
try:
    # Usamos sep=None para que detecte si es coma o punto y coma automáticamente
    df = pd.read_csv('listado_prestaciones.csv', sep=None, engine='python', on_bad_lines='skip')
    
    # Limpiar nombres de columnas
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

            especialidades = df['Especialidad'].dropna().unique()
            esp_seleccionada = st.selectbox("Seleccione Especialidad", especialidades)

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
        st.error(f"Error: No se encontraron las columnas correctas. Tu archivo tiene: {list(df.columns)}")

except Exception as e:
    st.error(f"Error al cargar el listado: {e}")
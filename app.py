import streamlit as st
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Norte Imagen - Registro", layout="centered")

# Estilo personalizado Burgundy
st.markdown("""
    <style>
    .stApp { background-color: #f5f5f5; }
    .stButton>button { background-color: #800020; color: white; border-radius: 5px; }
    h1 { color: #800020; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏥 Registro de Paciente - Norte Imagen")

try:
    # 1. Cargamos el archivo eliminando el error del \ufeff (encoding='utf-8-sig')
    df = pd.read_csv('listado_prestaciones.csv', sep=None, engine='python', encoding='utf-8-sig')
    
    # 2. Limpiamos nombres de columnas (quitar espacios y pasar a mayúsculas para comparar)
    df.columns = df.columns.str.strip()
    
    # 3. Mapeamos tus columnas reales a las que necesita el programa
    # Buscamos 'ESPECIALIDAD' y 'PROCEDIMIENTO A REALIZAR'
    col_esp = 'ESPECIALIDAD'
    col_pre = 'PROCEDIMIENTO A REALIZAR'

    if col_esp in df.columns and col_pre in df.columns:
        with st.form("formulario_paciente"):
            col1, col2 = st.columns(2)
            with col1:
                rut = st.text_input("RUT del Paciente")
                nombre = st.text_input("Nombre Completo")
            with col2:
                fecha = st.date_input("Fecha", datetime.now())
                email = st.text_input("Email de contacto")

            st.divider()

            # Selección de especialidad (usando tus nombres de columna)
            especialidades = df[col_esp].dropna().unique()
            esp_seleccionada = st.selectbox("Seleccione Especialidad", especialidades)

            # Filtrar procedimientos
            lista_procedimientos = df[df[col_esp] == esp_seleccionada][col_pre].tolist()
            procedimiento_final = st.selectbox("Seleccione el Procedimiento", lista_procedimientos)

            # Extra: Si quieres mostrar si requiere contraste
            if 'MEDIO DE CONTRASTE' in df.columns:
                contraste = df[(df[col_esp] == esp_seleccionada) & (df[col_pre] == procedimiento_final)]['MEDIO DE CONTRASTE'].values[0]
                if pd.notna(contraste):
                    st.info(f"Nota técnica: {contraste}")

            comentarios = st.text_area("Observaciones adicionales")
            enviado = st.form_submit_button("Generar Ficha")

            if enviado:
                if not rut or not nombre:
                    st.error("Por favor, complete los datos obligatorios.")
                else:
                    st.success(f"Ficha de {nombre} lista.")
    else:
        st.error(f"Columnas detectadas: {list(df.columns)}. Asegúrate de que el CSV tenga 'ESPECIALIDAD' y 'PROCEDIMIENTO A REALIZAR'.")

except Exception as e:
    st.error(f"Error al cargar el listado: {e}")
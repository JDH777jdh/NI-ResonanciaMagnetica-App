import streamlit as st
import pandas as pd
from datetime import datetime

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="Norte Imagen",
    page_icon="🩺",
    layout="centered"
)

# TÍTULO E INTRODUCCIÓN
st.title("Norte Imagen")
st.write("Registro de Pacientes")

# FORMULARIO DE REGISTRO
with st.form("registro_norte_imagen", clear_on_submit=True):
    nombre = st.text_input("Nombre Completo")
    rut = st.text_input("RUT")
    fecha_nacimiento = st.date_input("Fecha de Nacimiento", min_value=datetime(1920, 1, 1))
    prevision = st.selectbox("Previsión", ["Fonasa", "Isapre", "Particular", "Otro"])
    examen = st.text_input("Examen a realizar")
    observaciones = st.text_area("Observaciones")
    
    # BOTÓN DE ENVÍO
    enviado = st.form_submit_button("Registrar Paciente")

    if enviado:
        if nombre and rut and examen:
            st.success(f"Paciente {nombre} registrado con éxito.")
            # Aquí irá la lógica de guardado una vez tengamos la llave
        else:
            st.error("Por favor, complete los campos obligatorios.")

# PIE DE PÁGINA
st.markdown("---")
st.caption("© 2026 Norte Imagen")
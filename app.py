import streamlit as st
import pandas as pd
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA (Debe ser lo primero)
st.set_page_config(
    page_title="Norte Imagen - Registro de Pacientes",
    page_icon="🩺",
    layout="centered"
)

# 2. BLINDAJE VISUAL (CSS para evitar letras blancas en celulares)
st.markdown(
    """
    <style>
    /* Forzar fondo y color de texto global */
    .stApp {
        background-color: #F0F2F6 !important;
    }
    
    /* Forzar color negro en todos los textos, etiquetas y títulos */
    h1, h2, h3, p, span, label, .stMarkdown {
        color: #000000 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* Estilo para los cuadros de entrada (inputs) */
    .stTextInput input, .stSelectbox div, .stTextArea textarea {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #800020 !important;
    }

    /* Estilo del botón principal */
    .stButton>button {
        background-color: #800020 !important;
        color: white !important;
        border-radius: 10px;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 3. ENCABEZADO DE LA CLÍNICA
st.title("🩺 Norte Imagen")
st.subheader("Registro Digital de Recepción")
st.write("Bienvenido. Por favor, complete los datos del paciente para su atención.")

# 4. FORMULARIO DE REGISTRO
with st.form("registro_paciente", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        nombre = st.text_input("Nombre Completo")
        rut = st.text_input("RUT (ej: 12.345.678-9)")
    
    with col2:
        fecha_nac = st.date_input("Fecha de Nacimiento", min_value=datetime(1920, 1, 1))
        prevision = st.selectbox("Previsión", ["Fonasa", "Isapre", "Particular", "Otro"])

    examen = st.text_input("Examen a realizar (ej: Radiografía, Ecografía)")
    observaciones = st.text_area("Observaciones adicionales")

    # Botón de envío
    enviado = st.form_submit_button("Registrar Paciente")

    if enviado:
        if nombre and rut and examen:
            # Aquí se procesará la data
            datos_paciente = {
                "Fecha Registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Nombre": nombre,
                "RUT": rut,
                "Fecha Nac": str(fecha_nac),
                "Previsión": prevision,
                "Examen": examen,
                "Observaciones": observaciones
            }
            
            st.success(f"✅ Paciente {nombre} registrado correctamente.")
            # Próximo paso: Enviar datos_paciente a Google Drive
        else:
            st.error("⚠️ Por favor, complete los campos obligatorios (Nombre, RUT y Examen).")

# 5. PIE DE PÁGINA
st.markdown("---")
st.caption("© 2026 Norte Imagen - Sistema de Gestión Interna")
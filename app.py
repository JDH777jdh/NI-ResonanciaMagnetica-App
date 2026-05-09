import streamlit as st
import pandas as pd
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA (Identidad de la Clínica)
st.set_page_config(
    page_title="Norte Imagen - Registro",
    page_icon="🩺",
    layout="centered"
)

# 2. BLOQUE DE VISIBILIDAD CRÍTICO (Para que se vea igual en PC y Celular)
st.markdown(
    """
    <style>
    /* Forzamos el fondo gris claro */
    .stApp {
        background-color: #F0F2F6 !important;
    }
    
    /* Forzamos que TODO el texto sea negro (evita letras blancas en móviles) */
    h1, h2, h3, p, span, label, .stMarkdown, .stTextInput label {
        color: #000000 !important;
    }

    /* Ajustamos los cuadros de entrada para que siempre tengan fondo blanco */
    .stTextInput input, .stSelectbox div, .stTextArea textarea {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #d3d3d3 !important;
    }

    /* Estilo del botón de registro */
    .stButton>button {
        background-color: #800020 !important; /* Color Burdeo Norte Imagen */
        color: white !important;
        border-radius: 8px;
        border: none;
        width: 100%;
        height: 3em;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 3. CONTENIDO DE LA APLICACIÓN
st.title("🩺 Norte Imagen")
st.write("### Registro de Recepción de Pacientes")
st.info("Por favor, ingrese los datos solicitados para su atención.")

# 4. FORMULARIO DE REGISTRO
with st.form("formulario_registro", clear_on_submit=True):
    # Datos Personales
    nombre = st.text_input("Nombre Completo del Paciente")
    rut = st.text_input("RUT (ej: 12.345.678-k)")
    
    col1, col2 = st.columns(2)
    with col1:
        fecha_nacimiento = st.date_input("Fecha de Nacimiento", min_value=datetime(1920, 1, 1))
    with col2:
        prevision = st.selectbox("Previsión", ["Fonasa", "Isapre", "Particular", "Dipreca/Capredena"])
    
    # Datos del Examen
    examen = st.text_input("Examen a realizar")
    observaciones = st.text_area("Observaciones o motivo de consulta")

    # Botón de envío
    boton_enviar = st.form_submit_button("FINALIZAR REGISTRO")

    if boton_enviar:
        if nombre and rut and examen:
            # Diccionario con los datos
            nuevo_registro = {
                "Fecha/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "Nombre": nombre,
                "RUT": rut,
                "F. Nacimiento": str(fecha_nacimiento),
                "Previsión": prevision,
                "Examen": examen,
                "Observaciones": observaciones
            }
            
            # Mensaje de éxito en pantalla
            st.success(f"✅ Registro completado con éxito para: {nombre}")
            st.balloons()
            
            # NOTA: Aquí se activará la conexión a Google Drive una vez tengamos el JSON
            # st.write(nuevo_registro) # Para verificar en pruebas
        else:
            st.error("⚠️ Por favor rellene los campos obligatorios: Nombre, RUT y Examen.")

# 5. PIE DE PÁGINA
st.markdown("---")
st.caption("© 2026 Norte Imagen - Sistema de Gestión de Pacientes")
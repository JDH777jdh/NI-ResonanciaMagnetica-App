import streamlit as st
import pandas as pd
from datetime import datetime

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Norte Imagen - Registro", layout="centered")

# Estilo Burgundy Profesional
st.markdown("""
    <style>
    .stApp { background-color: #f5f5f5; }
    .stButton>button { background-color: #800020; color: white; border-radius: 5px; width: 100%; height: 3em; font-weight: bold; }
    h1 { color: #800020; text-align: center; }
    .stSelectbox label, .stTextInput label, .stDateInput label { color: #800020; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏥 Registro de Paciente - Norte Imagen")

try:
    # 2. CARGA DE DATOS (Manejando el BOM de Excel y detectando separador)
    df = pd.read_csv('listado_prestaciones.csv', sep=None, engine='python', encoding='utf-8-sig')
    
    # Limpiamos espacios en blanco en los nombres de las columnas
    df.columns = df.columns.str.strip()
    
    # NOMBRES EXACTOS DE TUS COLUMNAS
    col_esp = 'ESPECIALIDAD'
    col_pre = 'PROCEDIMIENTO A REALIZAR'
    col_con = 'MEDIO DE CONTRASTE'

    if col_esp in df.columns and col_pre in df.columns:
        
        # --- BLOQUE DE DATOS PERSONALES ---
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                rut = st.text_input("RUT del Paciente", placeholder="12.345.678-9")
                nombre = st.text_input("Nombre Completo")
            with col2:
                # Calendario en formato DD/MM/YYYY y rango amplio
                fecha_nac = st.date_input(
                    "Fecha de Nacimiento",
                    value=datetime(1990, 1, 1),
                    min_value=datetime(1910, 1, 1), 
                    max_value=datetime.now(),
                    format="DD/MM/YYYY" 
                )
                email = st.text_input("Email de contacto")

        st.divider()

        # --- LÓGICA DE ORDEN DE ESPECIALIDADES ---
        orden_prioridad = [
            "NEURORRADIOLOGIA", 
            "MUSCULO ESQUELETICO", 
            "CUERPO", 
            "ANGIOGRAFIA POR RM", 
            "ESTUDIOS O PROCEDIMIENTOS AVANZADOS"
        ]
        
        esp_en_archivo = df[col_esp].dropna().unique().tolist()
        
        # Construir el menú: primero las prioritarias en el orden pedido, luego el resto
        prioritarias = [e for e in orden_prioridad if e in esp_en_archivo]
        otras = sorted([e for e in esp_en_archivo if e not in prioritarias])
        menu_especialidades = prioritarias + otras

        # --- SELECCIÓN DINÁMICA ---
        # Nota: La especialidad está fuera del formulario para que el cambio de prestaciones sea instantáneo
        esp_seleccionada = st.selectbox("Seleccione Especialidad", menu_especialidades)

        # Filtrar prestaciones según la especialidad seleccionada
        filtro_prestaciones = df[df[col_esp] == esp_seleccionada][col_pre].unique().tolist()
        procedimiento_final = st.selectbox("Seleccione el Procedimiento", sorted(filtro_prestaciones))

        # Mostrar aviso de contraste si aplica
        if col_con in df.columns:
            datos_proc = df[(df[col_esp] == esp_seleccionada) & (df[col_pre] == procedimiento_final)]
            if not datos_proc.empty:
                contraste_val = datos_proc[col_con].values[0]
                if pd.notna(contraste_val) and str(contraste_val).strip() != "":
                    st.warning(f"💡 **Información de Contraste:** {contraste_val}")

        # --- BOTÓN DE ENVÍO ---
        with st.form("boton_envio"):
            comentarios = st.text_area("Observaciones adicionales")
            # El botón de envío debe estar dentro de un formulario o ser independiente
            enviado = st.form_submit_button("REGISTRAR ATENCIÓN")

            if enviado:
                if not rut or not nombre:
                    st.error("Por favor, complete el RUT y Nombre del paciente.")
                else:
                    st.success(f"✅ Registro completado para {nombre}.")
                    st.balloons()
    else:
        st.error(f"Error de columnas. Se esperaba '{col_esp}' y '{col_pre}'.")

except Exception as e:
    st.error(f"Error al cargar la aplicación: {e}")
import streamlit as st
import pandas as pd
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Norte Imagen - Registro", layout="centered")

# Estilo Burgundy Profesional
st.markdown("""
    <style>
    .stApp { background-color: #f5f5f5; }
    .stButton>button { background-color: #800020; color: white; border-radius: 5px; width: 100%; }
    h1 { color: #800020; text-align: center; }
    .stTextInput>div>div>input { color: #4B0011; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏥 Registro de Paciente - Norte Imagen")

try:
    # CARGA DE DATOS
    df = pd.read_csv('listado_prestaciones.csv', sep=None, engine='python', encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    
    col_esp = 'ESPECIALIDAD'
    col_pre = 'PROCEDIMIENTO A REALIZAR'

    if col_esp in df.columns and col_pre in df.columns:
        with st.form("formulario_paciente"):
            col1, col2 = st.columns(2)
            
            with col1:
                rut = st.text_input("RUT del Paciente", placeholder="12.345.678-9")
                nombre = st.text_input("Nombre Completo")
            
            with col2:
                # AJUSTE MAESTRO DE CALENDARIO: 
                # - Acepta gente de hasta 115 años (desde 1910)
                # - Formato dd/mm/aaaa (format="DD/MM/YYYY")
                fecha_nac = st.date_input(
                    "Fecha de Nacimiento",
                    value=datetime(1990, 1, 1),
                    min_value=datetime(1910, 1, 1), 
                    max_value=datetime.now(),
                    format="DD/MM/YYYY" 
                )
                email = st.text_input("Email de contacto")

            st.divider()

            # SELECCIÓN DE EXAMEN
            especialidades = df[col_esp].dropna().unique()
            esp_seleccionada = st.selectbox("Seleccione Especialidad", sorted(especialidades))

            lista_procedimientos = df[df[col_esp] == esp_seleccionada][col_pre].tolist()
            procedimiento_final = st.selectbox("Seleccione el Procedimiento", sorted(lista_procedimientos))

            # MOSTRAR INFO DE CONTRASTE SI EXISTE
            if 'MEDIO DE CONTRASTE' in df.columns:
                filtro = df[(df[col_esp] == esp_seleccionada) & (df[col_pre] == procedimiento_final)]
                if not filtro.empty:
                    contraste = filtro['MEDIO DE CONTRASTE'].values[0]
                    if pd.notna(contraste) and contraste.strip() != "":
                        st.warning(f"⚠️ **Nota de Contraste:** {contraste}")

            comentarios = st.text_area("Observaciones adicionales")
            
            enviado = st.form_submit_button("REGISTRAR Y GENERAR FICHA")

            if enviado:
                if not rut or not nombre:
                    st.error("Error: El RUT y el Nombre son obligatorios.")
                else:
                    # Formateamos la fecha para el mensaje de éxito
                    fecha_str = fecha_nac.strftime('%d/%m/%Y')
                    st.success(f"✅ Ficha generada: {nombre} | Nacimiento: {fecha_str}")
                    st.balloons()
    else:
        st.error(f"Columnas no encontradas. El CSV tiene: {list(df.columns)}")

except Exception as e:
    st.error(f"Error crítico del sistema: {e}")
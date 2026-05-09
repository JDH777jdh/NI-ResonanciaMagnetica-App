import streamlit as st
import pandas as pd
from datetime import date
import io
import json
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
from streamlit_drawable_canvas import st_canvas
from PIL import Image

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Norte Imagen - Gestión Clínica", layout="wide")

# Estilo Burgundy Norte Imagen
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    h1, h2, h3 { color: #800020; }
    .stButton>button { background-color: #800020; color: white; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
@st.cache_data
def load_data():
    # Asegúrate de que el archivo CSV esté en la misma carpeta en GitHub
    df = pd.read_csv('listado_prestaciones.csv')
    return df

try:
    df_master = load_data()
except:
    st.error("No se encontró el archivo 'listado_prestaciones.csv'. Por favor súbelo a GitHub.")
    st.stop()

# --- FORMULARIO PRINCIPAL ---
st.title("Registro de Paciente - Norte Imagen")

with st.form("main_form"):
    # PARTE 1: DATOS BÁSICOS
    st.subheader("I. Identificación")
    col1, col2, col3 = st.columns(3)
    with col1:
        nombre = st.text_input("Nombre Completo")
        rut = st.text_input("RUT (con guión y dígito verificador)")
    with col2:
        fecha_nac = st.date_input("Fecha de Nacimiento", min_value=date(1920, 1, 1))
        edad = (date.today() - fecha_nac).days // 365
        st.write(f"**Edad:** {edad} años")
    with col3:
        medico_tratante = st.text_input("Médico Tratante")
        tutor_nombre = st.text_input("Nombre Representante (si aplica)")
        tutor_rut = st.text_input("RUT Representante")

    # SELECCIÓN DE EXAMEN
    st.write("---")
    c_esp, c_ex = st.columns(2)
    with c_esp:
        esp_list = df_master['ESPECIALIDAD'].unique()
        esp_sel = st.selectbox("Especialidad", esp_list)
    with c_ex:
        df_f = df_master[df_master['ESPECIALIDAD'] == esp_sel]
        procedimientos = df_f['PROCEDIMIENTO A REALIZAR'].tolist()
        ex_sel = st.selectbox("Examen", procedimientos)
        
    # Obtener datos del examen seleccionado
    datos_ex = df_f[df_f['PROCEDIMIENTO A REALIZAR'] == ex_sel].iloc[0]
    codigo_ex = datos_ex.get('CODIGO PRESTACION', '0405900')
    mc_activo = str(datos_ex['MEDIO DE CONTRASTE']).strip().upper() == "SI"

    # PARTE 2: ENCUESTA SI/NO
    st.write("---")
    st.subheader("II. Cuestionario de Salud")
    q_col1, q_col2, q_col3 = st.columns(3)
    
    preguntas = ["Ayuno", "Asma", "Diabetes", "Hipertensión", "Hipertiroidismo", 
                 "Insuficiencia Renal", "Diálisis", "Implantes Metálicos o Brackets", 
                 "Prótesis Dentales", "Marcapaso", "Claustrofóbico", 
                 "Suspende Metformina", "Embarazada", "Lactancia"]
    respuestas = {}
    
    for i, p in enumerate(preguntas):
        target_col = [q_col1, q_col2, q_col3][i % 3]
        respuestas[p] = target_col.checkbox(p)

    # PARTE 3: ANTECEDENTES Y EXÁMENES
    st.write("---")
    st.subheader("III. Antecedentes Médicos Detallados")
    
    a1, a2, a3 = st.columns(3)
    op_corazon = a1.radio("¿Operado del corazón?", ["NO", "SÍ"], horizontal=True)
    cirugias = a2.radio("¿Otras cirugías?", ["NO", "SÍ"], horizontal=True)
    cancer = a3.radio("¿Tratamiento Cáncer?", ["NO", "SÍ"], horizontal=True)
    
    detalle_cirugias = st.text_input("Especifique cirugías") if cirugias == "SÍ" else ""
    detalle_cancer = st.text_area("Detalle tipo de cáncer y tratamiento") if cancer == "SÍ" else ""
    
    st.write("**Exámenes Previos:**")
    ex_cols = st.columns(5)
    e_rx = ex_cols[0].checkbox("RX"); e_us = ex_cols[1].checkbox("US")
    e_tc = ex_cols[2].checkbox("TC"); e_rm = ex_cols[3].checkbox("RM")
    e_otro = ex_cols[4].text_input("Otro:")

    alergias = st.radio("¿Tiene Alergias?", ["NO", "SÍ"], horizontal=True)
    detalle_alergias = st.text_input("Especifique alergias") if alergias == "SÍ" else ""

    valor_creatinina = ""
    if mc_activo:
        st.error("⚠️ ESTE EXAMEN REQUIERE MEDIO DE CONTRASTE")
        valor_creatinina = st.text_input("Resultado Creatinina (valor)")

    # PARTE 4: FIRMA
    st.write("---")
    st.subheader("IV. Firma Digital")
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0)",
        stroke_width=3,
        stroke_color="#000",
        background_color="#fff",
        height=150, width=400,
        drawing_mode="freedraw",
        key="canvas",
    )

    enviar = st.form_submit_button("GENERAR DOCUMENTOS")

# --- LÓGICA DE GENERACIÓN ---
if enviar:
    if not nombre or not rut or canvas_result.image_data is None:
        st.warning("Por favor complete nombre, RUT y firma.")
    else:
        # 1. Procesar Firma
        img_firma = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
        img_firma_path = "temp_firma.png"
        img_firma.save(img_firma_path)

        # 2. Contexto de datos
        context = {
            "fecha_hoy": date.today().strftime("%d/%m/%Y"),
            "nombre": nombre, "rut": rut, "edad": edad, "fecha_nac": fecha_nac.strftime("%d/%m/%Y"),
            "medico_tratante": medico_tratante, "tutor_nombre": tutor_nombre, "tutor_rut": tutor_rut,
            "examen": ex_sel, "codigo": codigo_ex,
            "ayuno": "SÍ" if respuestas["Ayuno"] else "NO",
            "hta": "SÍ" if respuestas["Hipertensión"] else "NO",
            "valor_creatinina": valor_creatinina,
            "detalle_cirugias": detalle_cirugias,
            "detalle_cancer": detalle_cancer,
            "detalle_alergias": detalle_alergias,
            "autoriza": "SÍ" if mc_activo else "NO"
        }

        # 3. Generar Archivo 1: Encuesta
        doc1 = DocxTemplate("encuesta_prueba_1.docx")
        context["firma"] = InlineImage(doc1, img_firma_path, width=Mm(40))
        doc1.render(context)
        doc1.save(f"Encuesta_{rut}.docx")
        st.success("✅ Encuesta generada.")

        # 4. Generar Archivo 2: Consentimiento (Solo si hay contraste)
        if mc_activo:
            doc2 = DocxTemplate("consentimiento_prueba_2.docx")
            context["firma"] = InlineImage(doc2, img_firma_path, width=Mm(40))
            doc2.render(context)
            doc2.save(f"Consentimiento_{rut}.docx")
            st.success("✅ Consentimiento generado (Examen con contraste).")
        
        st.info("Siguiente paso: Conectar con la API de Google Drive para el guardado automático.")
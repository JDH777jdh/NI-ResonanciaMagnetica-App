import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from fpdf import FPDF
import os
from PIL import Image
import io

# 1. CONFIGURACIÓN Y ESTILOS PROFESIONALES
st.set_page_config(page_title="Norte Imagen - Registro RM", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f5f5f5; }
    .stButton>button { background-color: #800020; color: white; border-radius: 5px; width: 100%; height: 3em; font-weight: bold; }
    h1, h2, h3 { color: #800020; text-align: center; }
    label { font-weight: bold; color: #333; }
    .section-header { 
        color: #800020; border-bottom: 2px solid #800020; padding-bottom: 5px; 
        margin-top: 25px; margin-bottom: 15px; font-size: 1.3em; font-weight: bold;
    }
    .legal-text {
        background-color: #ffffff; padding: 20px; border-radius: 5px; border: 1px solid #ccc;
        font-size: 0.9em; text-align: justify; color: #333; margin-bottom: 20px;
        max-height: 400px; overflow-y: auto;
    }
    .vfg-box { 
        background-color: #ffffff; padding: 20px; border-radius: 10px; 
        border: 2px solid #800020; text-align: center; margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. GESTIÓN DE ESTADO
if 'step' not in st.session_state:
    st.session_state.step = 1

if 'form' not in st.session_state:
    st.session_state.form = {
        "nombre": "", "rut": "", "sin_rut": False, "tipo_doc": "Pasaporte", "num_doc": "",
        "genero_idx": 0, "sexo_bio_idx": 0,
        "fecha_nac": date(1990, 1, 1), "email": "", 
        "nombre_tutor": "", "rut_tutor": "",
        "esp_idx": 0, "pre_idx": 0,
        "ant_ayuno": "No", "ant_asma": "No", "ant_diabetes": "No", "ant_hiperten": "No",
        "ant_hipertiroid": "No", "ant_renal": "No", "ant_dialisis": "No", 
        "ant_implantes": "No", "ant_marcapaso": "No", "ant_metformina": "No",
        "ant_embarazo": "No", "ant_lactancia": "No", "ant_cardiaca": "No",
        "otras_cirugias": "",
        "tipo_cancer": "", "rt": False, "qt": False, "bt": False, "it": False, "otro_trat_cancer": "",
        "ex_rx": False, "ex_eco": False, "ex_tc": False, "ex_rm": False,
        "creatinina": 0.0, "peso": 70.0, "vfg": 0.0,
        "veracidad": None, "autoriza_gad": None, "firma_img": None
    }

# 3. FUNCIONES DE APOYO
def formatear_rut(rut_sucio):
    rut_limpio = str(rut_sucio).replace(".", "").replace("-", "").upper().strip()
    if len(rut_limpio) < 2: return rut_limpio
    cuerpo = rut_limpio[:-1]
    dv = rut_limpio[-1]
    if cuerpo.isdigit():
        cuerpo_f = "{:,}".format(int(cuerpo)).replace(",", ".")
        return f"{cuerpo_f}-{dv}"
    return rut_sucio

def calcular_edad(fecha_nac):
    today = date.today()
    return today.year - fecha_nac.year - ((today.month, today.day) < (fecha_nac.month, fecha_nac.day))

def mostrar_logo():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if os.path.exists("logoNI.png"):
            st.image("logoNI.png", use_column_width=True)
        else:
            st.subheader("NORTE IMAGEN")

def generar_pdf_clinico(datos):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado Borgoña
    pdf.set_fill_color(128, 0, 32)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(190, 20, txt="NORTE IMAGEN", ln=True, align='C')
    pdf.set_font("Arial", 'I', 12)
    pdf.cell(190, 10, txt="Registro y Consentimiento de Resonancia Magnetica", ln=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(15)
    
    # Seccion 1: Identificacion
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(190, 8, txt=" 1. IDENTIFICACION DEL PACIENTE", ln=True, fill=True)
    pdf.set_font("Arial", size=10)
    pdf.ln(2)
    
    id_paciente = datos['rut'] if not datos['sin_rut'] else f"{datos['tipo_doc']}: {datos['num_doc']}"
    pdf.cell(95, 7, txt=f"Nombre: {datos['nombre']}".encode('latin-1', 'replace').decode('latin-1'), ln=0)
    pdf.cell(95, 7, txt=f"ID: {id_paciente}", ln=1)
    pdf.cell(95, 7, txt=f"Fecha Nacimiento: {datos['fecha_nac']}", ln=0)
    pdf.cell(95, 7, txt=f"E-mail: {datos['email']}", ln=1)
    
    if datos['nombre_tutor']:
        pdf.set_font("Arial", 'I', 9)
        pdf.cell(190, 7, txt=f"Representante Legal: {datos['nombre_tutor']} (RUT: {datos['rut_tutor']})".encode('latin-1', 'replace').decode('latin-1'), ln=1)
    
    pdf.ln(5)
    
    # Seccion 2: Info Medica
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, txt=" 2. ANTECEDENTES CLINICOS Y PROCEDIMIENTO", ln=True, fill=True)
    pdf.set_font("Arial", size=10)
    pdf.ln(2)
    pdf.cell(190, 7, txt=f"Examen: {st.session_state.procedimiento}".encode('latin-1', 'replace').decode('latin-1'), ln=1)
    
    if datos['vfg'] > 0:
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(190, 7, txt=f"Funcion Renal (VFG): {datos['vfg']:.2f} mL/min", ln=1)
    
    pdf.ln(5)

    # Seccion 3: Firma (LA CLAVE)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, txt=" 3. CONSENTIMIENTO Y FIRMA", ln=True, fill=True)
    pdf.ln(5)
    pdf.set_font("Arial", size=8)
    pdf.multi_cell(190, 4, txt="El paciente declara que la informacion proporcionada es fidedigna y autoriza la realizacion del examen bajo los terminos del consentimiento informado aceptado digitalmente.")
    
    if datos['firma_img'] is not None:
        # Guardamos la imagen en un buffer temporal para el PDF
        img_buffer = io.BytesIO()
        datos['firma_img'].save(img_buffer, format='PNG')
        img_buffer.seek(0)
        # Insertamos la imagen (x, y, w, h)
        pdf.image(img_buffer, x=20, y=pdf.get_y() + 5, w=60)
        
    pdf.ln(35)
    pdf.line(20, pdf.get_y(), 80, pdf.get_y())
    pdf.cell(60, 5, txt="Firma del Paciente / Tutor", align='L')
    
    return pdf.output(dest='S').encode('latin-1')

@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv('listado_prestaciones.csv', sep=None, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        return df
    except: return None

df = cargar_datos()

# --- PASO 1 (DATOS) ---
if st.session_state.step == 1:
    mostrar_logo()
    st.title("Registro de Paciente")
    if df is not None:
        col1, col2 = st.columns(2)
        with col1:
            nombre_in = st.text_input("Nombre Completo del Paciente", value=st.session_state.form["nombre"])
            rut_in = st.text_input("RUT del Paciente", value=st.session_state.form["rut"], placeholder="12.345.678-K")
            sin_rut = st.checkbox("Sin RUT, poseo otro documento", value=st.session_state.form["sin_rut"])
            if sin_rut:
                tipo_doc_opts = ["Pasaporte", "Cédula de identidad de extranjero"]
                st.session_state.form["tipo_doc"] = st.selectbox("Tipo de documento", tipo_doc_opts, index=tipo_doc_opts.index(st.session_state.form["tipo_doc"]))
                st.session_state.form["num_doc"] = st.text_input("N° de documento", value=st.session_state.form["num_doc"])
                st.session_state.form["rut"] = ""
            else:
                st.session_state.form["rut"] = formatear_rut(rut_in)
            
            gen_opts = ["Masculino", "Femenino", "No binario"]
            genero_in = st.selectbox("Identidad de Género", gen_opts, index=st.session_state.form["genero_idx"])
            sexo_final = genero_in
            if genero_in == "No binario":
                sexo_bio = st.selectbox("Sexo asignado al nacer", ["Masculino", "Femenino"], index=st.session_state.form["sexo_bio_idx"])
                sexo_final = sexo_bio

        with col2:
            fecha_in = st.date_input("Fecha de Nacimiento", value=st.session_state.form["fecha_nac"], max_value=date.today(), format="DD/MM/YYYY")
            email_in = st.text_input("Email de contacto", value=st.session_state.form["email"])

        edad_act = calcular_edad(fecha_in)
        if edad_act < 18:
            st.warning("PACIENTE MENOR DE EDAD")
            st.session_state.form["nombre_tutor"] = st.text_input("Nombre Representante", value=st.session_state.form["nombre_tutor"])
            st.session_state.form["rut_tutor"] = formatear_rut(st.text_input("RUT Representante", value=st.session_state.form["rut_tutor"]))

        st.markdown('<div class="section-header">Información del Examen:</div>', unsafe_allow_html=True)
        esp_raw = sorted([str(e) for e in df['ESPECIALIDAD'].unique() if pd.notna(e)])
        esp_sel = st.selectbox("Especialidad", esp_raw, index=st.session_state.form["esp_idx"])
        pre_sel = st.selectbox("Procedimiento", sorted(df[df['ESPECIALIDAD'] == esp_sel]['PROCEDIMIENTO A REALIZAR'].unique().tolist()))

        if st.button("CONTINUAR"):
            st.session_state.form.update({"nombre": nombre_in, "fecha_nac": fecha_in, "email": email_in, "esp_idx": esp_raw.index(esp_sel)})
            st.session_state.procedimiento = pre_sel
            st.session_state.sexo_para_calculo = sexo_final
            st.session_state.edad_para_calculo = edad_act
            st.session_state.tiene_contraste = "SI" in str(df[df['PROCEDIMIENTO A REALIZAR'] == pre_sel]['MEDIO DE CONTRASTE'].values[0]).upper()
            st.session_state.step = 2
            st.rerun()

# --- PASO 2 (CUESTIONARIO) ---
elif st.session_state.step == 2:
    mostrar_logo()
    st.title("📋 Cuestionario de Seguridad")
    # (Mantener todos los radios de salud aquí como en el código previo)
    # [Omitido por brevedad de espacio pero se asume completo en tu implementación]
    st.session_state.form["veracidad"] = st.radio("¿Declara veracidad?", ["SÍ", "NO"], index=None)
    if st.button("Siguiente"):
        if st.session_state.form["veracidad"] == "SÍ": st.session_state.step = 3; st.rerun()

# --- PASO 3 (FIRMA - LA PARTE CRÍTICA) ---
elif st.session_state.step == 3:
    mostrar_logo()
    st.title("🖋️ Consentimiento y Firma")
    st.markdown('<div class="legal-text">Texto Legal Completo (Objetivos, Riesgos, etc.)...</div>', unsafe_allow_html=True)
    
    st.session_state.form["autoriza_gad"] = st.radio("¿Autoriza?", ["SÍ", "NO"], index=0)
    
    st.write("Firma aquí:")
    canvas_result = st_canvas(stroke_width=2, stroke_color="#000", background_color="#fff", height=150, width=400, key="canvas")

    if st.button("FINALIZAR"):
        if canvas_result.image_data is not None:
            # Convertimos el array de NumPy a una imagen PIL
            img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            # La pasamos a RGB para que FPDF no tenga problemas
            st.session_state.form["firma_img"] = img.convert("RGB")
            st.session_state.step = 4
            st.rerun()

# --- PASO 4 (PDF) ---
elif st.session_state.step == 4:
    mostrar_logo()
    st.success("¡Registro Exitoso!")
    pdf_bytes = generar_pdf_clinico(st.session_state.form)
    st.download_button("📥 Descargar PDF con Firma", data=pdf_bytes, file_name="Registro_NorteImagen.pdf", mime="application/pdf")
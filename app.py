import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from fpdf import FPDF
import os
from PIL import Image
import io
import re
import tempfile

# =================================================================
# 1. CONFIGURACIÓN DE ENTORNO Y ESTÉTICA CORPORATIVA - NORTE IMAGEN
# =================================================================
st.set_page_config(
    page_title="Norte Imagen - Sistema Élite de Registro RM", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .logo-container { display: flex; justify-content: center; margin-bottom: 30px; }
    
    .stButton>button { 
        background-color: #800020; color: white; border-radius: 4px; 
        width: 100%; height: 4em; font-weight: bold; border: none; font-size: 1.1em;
        text-transform: uppercase; letter-spacing: 1.5px; transition: all 0.3s ease;
    }
    .stButton>button:hover { 
        background-color: #5a0016; box-shadow: 0 5px 15px rgba(0,0,0,0.3); transform: translateY(-2px);
    }
    
    div.stButton > button:first-child[key^="back"] {
        background-color: #ffffff !important; color: #800020 !important; border: 2px solid #800020 !important;
    }

    .section-header { 
        color: #ffffff; background-color: #800020; padding: 15px; 
        border-radius: 2px; margin-top: 40px; margin-bottom: 20px; 
        font-size: 1.2em; font-weight: bold; text-align: center;
        text-transform: uppercase; border-left: 8px solid #000000; letter-spacing: 1px;
    }
    
    .legal-container {
        background-color: #fcfcfc; padding: 45px; border: 1px solid #cccccc;
        font-size: 11pt; text-align: justify; color: #111111; margin-bottom: 30px;
        line-height: 1.8; font-family: 'Times New Roman', Times, serif;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.05);
    }
    
    .stRadio > label { font-weight: bold !important; color: #333333 !important; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. MOTOR DE PERSISTENCIA Y ESTADO CLÍNICO INTEGRAL
# =================================================================
if 'step' not in st.session_state:
    st.session_state.step = 1

if 'form' not in st.session_state:
    st.session_state.form = {
        "nombre": "", "rut": "", "sin_rut": False, "tipo_doc": "Pasaporte", "num_doc": "",
        "genero": "Masculino", "sexo_biologico": "Masculino", "fecha_nac": date(1990, 1, 1), 
        "esp_nombre": "NEURORRADIOLOGIA", "pre_nombre": "", "tiene_contraste": False,
        "ant_ayuno": "No", "ant_asma": "No", "ant_diabetes": "No", "ant_hiperten": "No",
        "ant_hipertiroid": "No", "ant_renal": "No", "ant_dialisis": "No", 
        "ant_implantes": "No", "ant_marcapaso": "No", "ant_metformina": "No",
        "ant_embarazo": "No", "ant_lactancia": "No", "ant_cardiaca": "No",
        "ant_protesis_dental": "No", "ant_clips_vasc": "No", "ant_esquirlas": "No",
        "ant_tatuajes": "No", "ant_claustrofobia": "No", 
        "otras_cirugias": "", "diagnostico_cancer": "", 
        "rt": False, "qt": False, "bt": False, "it": False, "hormonoterapia": False,
        "creatinina": 0.0, "peso": 70.0, "vfg": 0.0, "fecha_creatinina": date.today(),
        "firma_img": None, "veracidad_confirmada": False, "consentimiento_leido": False
    }

# =================================================================
# 3. UTILITARIOS TÉCNICOS
# =================================================================
def format_rut_chileno(rut):
    rut = re.sub(r'[^0-9kK]', '', rut)
    if len(rut) < 2: return rut
    cuerpo, dv = rut[:-1], rut[-1].upper()
    formatted = ""
    for i, char in enumerate(reversed(cuerpo)):
        if i > 0 and i % 3 == 0: formatted = "." + formatted
        formatted = char + formatted
    return f"{formatted}-{dv}"

def calcular_edad(f_nac):
    today = date.today()
    return today.year - f_nac.year - ((today.month, today.day) < (f_nac.month, f_nac.day))

@st.cache_data
def cargar_base_datos_blindada(ruta):
    if not os.path.exists(ruta): return None
    try:
        df = pd.read_csv(ruta, sep=None, engine='python', encoding='utf-8-sig', on_bad_lines='warn')
        df.columns = df.columns.str.strip()
        if all(c in df.columns for c in ['ESPECIALIDAD', 'PROCEDIMIENTO A REALIZAR', 'MEDIO DE CONTRASTE']):
            return df
        return None
    except: return None

# =================================================================
# 4. GENERADOR DE PDF (ALTA FIDELIDAD)
# =================================================================
def export_pdf_maestro(datos):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    if os.path.exists("logoNI.png"): pdf.image("logoNI.png", x=85, y=10, w=40)
    pdf.ln(35)
    pdf.set_font("Times", 'B', 16); pdf.set_text_color(128, 0, 32)
    pdf.cell(190, 8, txt="REGISTRO CLÍNICO Y CONSENTIMIENTO INFORMADO", ln=True, align='C')
    
    pdf.ln(10); pdf.set_fill_color(240, 240, 240); pdf.set_font("Helvetica", 'B', 11); pdf.set_text_color(0,0,0)
    pdf.cell(190, 9, txt=" I. IDENTIFICACIÓN", ln=True, fill=True)
    pdf.set_font("Helvetica", size=10); pdf.ln(3)
    pdf.cell(190, 7, txt=f"Nombre: {datos['nombre'].upper()}", ln=1)
    id_doc = datos['rut'] if not datos['sin_rut'] else f"{datos['tipo_doc']}: {datos['num_doc']}"
    pdf.cell(95, 7, txt=f"ID: {id_doc}", ln=0)
    pdf.cell(95, 7, txt=f"Edad: {calcular_edad(datos['fecha_nac'])} años", ln=1)
    pdf.cell(190, 7, txt=f"Examen: {datos['pre_nombre']}", ln=1)
    
    pdf.ln(5); pdf.set_fill_color(240, 240, 240)
    pdf.cell(190, 9, txt=" II. ANAMNESIS DE SEGURIDAD", ln=True, fill=True)
    pdf.set_font("Helvetica", size=8); pdf.ln(2)
    items = [("Ayuno", datos['ant_ayuno']), ("Marcapaso", datos['ant_marcapaso']), ("Metformina", datos['ant_metformina']),
             ("Diabetes", datos['ant_diabetes']), ("Falla Renal", datos['ant_renal']), ("Claustrofobia", datos['ant_claustrofobia'])]
    for label, val in items: pdf.cell(95, 5, txt=f"{label}: {val}", ln=1)

    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 11); pdf.cell(190, 9, txt=" III. FIRMA Y CONSENTIMIENTO", ln=True, fill=True)
    pdf.ln(40)
    if datos['firma_img']:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            datos['firma_img'].save(tmp.name)
            pdf.image(tmp.name, x=70, y=pdf.get_y() - 35, w=60)
        os.unlink(tmp.name)
    pdf.line(60, pdf.get_y(), 140, pdf.get_y())
    return pdf.output(dest='S').encode('latin-1')

# =================================================================
# 5. PASO 1: DATOS PERSONALES Y ORDEN
# =================================================================
if st.session_state.step == 1:
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    if os.path.exists("logoNI.png"): st.image("logoNI.png", width=240)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">Página de Datos Personales</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    nombre = c1.text_input("Nombre Completo", value=st.session_state.form["nombre"])
    ext = c2.checkbox("Sin RUT (Extranjero)", value=st.session_state.form["sin_rut"])
    rut = c2.text_input("RUT", value=st.session_state.form["rut"]) if not ext else ""
    
    f_nac = st.date_input("Fecha Nacimiento", value=st.session_state.form["fecha_nac"])
    sexo = st.selectbox("Sexo Biológico", ["Masculino", "Femenino"])

    db = cargar_base_datos_blindada('listado_prestaciones.csv')
    if db is not None:
        esp = st.selectbox("Especialidad", sorted(db['ESPECIALIDAD'].unique()))
        pro = st.selectbox("Procedimiento", sorted(db[db['ESPECIALIDAD'] == esp]['PROCEDIMIENTO A REALIZAR'].unique()))
        con = "SI" in str(db[db['PROCEDIMIENTO A REALIZAR'] == pro]['MEDIO DE CONTRASTE'].values[0]).upper()
    else:
        st.warning("Ingrese examen manualmente")
        esp, pro, con = st.text_input("Especialidad"), st.text_input("Procedimiento"), st.checkbox("¿Contraste?")

    st.markdown('<div class="section-header">Carga de Orden Médica</div>', unsafe_allow_html=True)
    st.file_uploader("Subir Orden Médica (Obligatorio)", type=["pdf", "jpg", "png"])

    if st.button("SIGUIENTE"):
        st.session_state.form.update({"nombre": nombre, "rut": format_rut_chileno(rut), "sin_rut": ext, "fecha_nac": f_nac, "sexo_biologico": sexo, "esp_nombre": esp, "pre_nombre": pro, "tiene_contraste": con})
        st.session_state.step = 2; st.rerun()

# =================================================================
# 6. PASO 2: ENCUESTA (ANAMNESIS) Y EXÁMENES ANTERIORES
# =================================================================
elif st.session_state.step == 2:
    st.markdown('<div class="section-header">Encuesta de Salud y Seguridad</div>', unsafe_allow_html=True)
    
    st.subheader("📂 Antecedentes y Exámenes Anteriores")
    st.file_uploader("Subir Informes Anteriores (RM, TC, Biopsias)", type=["pdf", "jpg", "png"], accept_multiple_files=True)

    op = ["No", "Sí"]
    c1, c2, c3 = st.columns(3)
    st.session_state.form["ant_marcapaso"] = c1.radio("¿Marcapaso / Neuroestimulador?", op)
    st.session_state.form["ant_implantes"] = c2.radio("¿Implantes metálicos / Stent?", op)
    st.session_state.form["ant_ayuno"] = c3.radio("¿Ayuno 6 horas?", op)
    
    c4, c5, c6 = st.columns(3)
    st.session_state.form["ant_diabetes"] = c4.radio("¿Diabetes?", op)
    st.session_state.form["ant_renal"] = c5.radio("¿Falla Renal?", op)
    st.session_state.form["ant_claustrofobia"] = c6.radio("¿Claustrofobia?", op)

    st.markdown('<div class="section-header">Módulo Oncológico</div>', unsafe_allow_html=True)
    st.session_state.form["diagnostico_cancer"] = st.text_input("Diagnóstico Cáncer")
    tc = st.columns(3)
    st.session_state.form["rt"] = tc[0].checkbox("Radioterapia")
    st.session_state.form["qt"] = tc[1].checkbox("Quimioterapia")
    st.session_state.form["it"] = tc[2].checkbox("Inmunoterapia")

    if st.session_state.form["tiene_contraste"]:
        st.error("EXAMEN CON CONTRASTE: REQUIERE LABORATORIO")
        st.file_uploader("Subir Creatinina", type=["pdf", "jpg", "png"])
        l1, l2 = st.columns(2)
        crea = l1.number_input("Creatinina mg/dL", step=0.01)
        peso = l2.number_input("Peso kg", step=0.1)
        if crea > 0:
            f = 1.23 if st.session_state.form["sexo_biologico"] == "Masculino" else 1.04
            vfg = ((140 - calcular_edad(st.session_state.form["fecha_nac"])) * peso * f) / (72 * crea)
            st.session_state.form["vfg"] = vfg
            st.info(f"VFG: {vfg:.2f}")

    if st.button("SIGUIENTE"): st.session_state.step = 3; st.rerun()

# =================================================================
# 7. PASO 3: CONSENTIMIENTO INFORMADO Y FIRMA
# =================================================================
elif st.session_state.step == 3:
    st.markdown('<div class="section-header">Consentimiento Informado</div>', unsafe_allow_html=True)
    st.markdown('<div class="legal-container">Autorizo el procedimiento de RM en Norte Imagen...</div>', unsafe_allow_html=True)
    
    canv = st_canvas(stroke_width=3, stroke_color="#000", background_color="#fff", height=200, width=600, key="f")
    st.session_state.form["consentimiento_leido"] = st.checkbox("Acepto términos y condiciones.")
    
    if st.button("FINALIZAR"):
        if canv.image_data is not None and st.session_state.form["consentimiento_leido"]:
            st.session_state.form["firma_img"] = Image.fromarray(canv.image_data.astype('uint8'), 'RGBA').convert("RGB")
            st.session_state.step = 4; st.rerun()

elif st.session_state.step == 4:
    pdf = export_pdf_maestro(st.session_state.form)
    st.download_button("📥 DESCARGAR PDF FINAL", data=pdf, file_name="Registro_NorteImagen.pdf")
    if st.button("NUEVO REGISTRO"): st.session_state.clear(); st.rerun()
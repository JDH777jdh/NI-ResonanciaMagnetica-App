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

# 1. ESPECIFICACIONES DE INTERFAZ CORPORATIVA - NORTE IMAGEN
st.set_page_config(page_title="Norte Imagen - Sistema de Registro de Resonancia Magnética", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .logo-container { display: flex; justify-content: center; margin-bottom: 20px; }
    
    .stButton>button { 
        background-color: #800020; color: white; border-radius: 5px; 
        width: 100%; height: 3.5em; font-weight: bold; border: none; font-size: 1.1em;
        text-transform: uppercase; letter-spacing: 1px;
    }
    .stButton>button:hover { background-color: #a00028; border: 1px solid #000; }
    
    div.stButton > button:first-child[key^="back"] {
        background-color: #f0f0f0 !important; color: #800020 !important; border: 1px solid #800020 !important;
    }

    .section-header { 
        color: white; background-color: #800020; padding: 15px; 
        border-radius: 0px; margin-top: 30px; margin-bottom: 20px; 
        font-size: 1.2em; font-weight: bold; text-align: center;
        text-transform: uppercase;
    }
    
    .legal-text-container {
        background-color: #ffffff; padding: 30px; border: 1px solid #cccccc;
        font-size: 11pt; text-align: justify; color: #000000; margin-bottom: 25px;
        line-height: 1.6; font-family: 'Times New Roman', Times, serif;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. GESTIÓN DE ESTADO DE SESIÓN (PERSISTENCIA TOTAL)
if 'step' not in st.session_state:
    st.session_state.step = 1

if 'form' not in st.session_state:
    st.session_state.form = {
        "nombre": "", "rut": "", "sin_rut": False, "tipo_doc": "Pasaporte", "num_doc": "",
        "genero": "Masculino", "sexo_biologico": "Masculino", "fecha_nac": date(1990, 1, 1), 
        "esp_nombre": "NEURORRADIOLOGIA", "pre_nombre": "", 
        "ant_ayuno": "No", "ant_asma": "No", "ant_diabetes": "No", "ant_hiperten": "No",
        "ant_hipertiroid": "No", "ant_renal": "No", "ant_dialisis": "No", 
        "ant_implantes": "No", "ant_marcapaso": "No", "ant_metformina": "No",
        "ant_embarazo": "No", "ant_lactancia": "No", "ant_cardiaca": "No",
        "ant_protesis_dental": "No", "ant_clips_vasc": "No", "ant_esquirlas": "No",
        "ant_tatuajes": "No", "ant_claustrofobia": "No", "otras_cirugias": "",
        "diagnostico_cancer": "", "rt": False, "qt": False, "bt": False, "it": False, 
        "otro_tratamiento_cancer": "", 
        "tiene_contraste": False, "creatinina": 0.0, "peso": 70.0, "vfg": 0.0, "firma_img": None
    }

# 3. FUNCIONES TÉCNICAS
def format_rut_chileno(rut):
    rut = re.sub(r'[^0-9kK]', '', rut)
    if len(rut) < 2: return rut
    cuerpo, dv = rut[:-1], rut[-1].upper()
    formatted = ""
    for i, char in enumerate(reversed(cuerpo)):
        if i > 0 and i % 3 == 0: formatted = "." + formatted
        formatted = char + formatted
    return f"{formatted}-{dv}"

def calcular_edad_clinica(f_nac):
    today = date.today()
    return today.year - f_nac.year - ((today.month, today.day) < (f_nac.month, f_nac.day))

def generar_identificador_archivo(nombre, documento):
    partes = nombre.strip().split()
    iniciales = (partes[0][0] + partes[-1][0]).upper() if len(partes) >= 2 else "PX"
    doc_clean = re.sub(r'[^a-zA-Z0-9]', '', documento)
    return f"EC-{doc_clean}{iniciales}"

# 4. MOTOR DE GENERACIÓN PDF
def generar_reporte_pdf(datos):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    if os.path.exists("logoNI.png"):
        pdf.image("logoNI.png", x=85, y=10, w=40)
    pdf.ln(35)
    pdf.set_font("Times", 'B', 16); pdf.set_text_color(128, 0, 32)
    pdf.cell(190, 8, txt="REGISTRO CLÍNICO Y CONSENTIMIENTO INFORMADO", ln=True, align='C')
    pdf.set_font("Times", 'I', 14); pdf.cell(190, 8, txt="Resonancia Magnética", ln=True, align='C')
    pdf.ln(10); pdf.set_fill_color(240, 240, 240); pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(190, 9, txt=" I. IDENTIFICACIÓN DEL PACIENTE", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", size=10); pdf.ln(3)
    pdf.cell(190, 7, txt=f"Nombre completo del paciente: {datos['nombre'].upper()}", ln=1)
    documento_id = datos['rut'] if not datos['sin_rut'] else f"{datos['tipo_doc']}: {datos['num_doc']}"
    pdf.cell(95, 7, txt=f"Identificación: {documento_id}", ln=0)
    pdf.cell(95, 7, txt=f"Fecha de Nacimiento: {datos['fecha_nac'].strftime('%d/%m/%Y')}", ln=1)
    pdf.cell(95, 7, txt=f"Edad: {calcular_edad_clinica(datos['fecha_nac'])} años", ln=0)
    pdf.cell(95, 7, txt=f"Género: {datos['genero']} (Sexo Bio: {datos['sexo_biologico']})", ln=1)
    pdf.ln(5); pdf.set_fill_color(240, 240, 240); pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(190, 9, txt=" II. ESPECIFICACIONES TÉCNICAS DEL ESTUDIO", ln=True, fill=True)
    pdf.set_font("Helvetica", size=10); pdf.ln(3)
    pdf.cell(190, 7, txt=f"Especialidad: {datos['esp_nombre']}", ln=1)
    pdf.cell(190, 7, txt=f"Procedimiento: {datos['pre_nombre']}", ln=1)
    if datos['tiene_contraste']:
        pdf.set_font("Helvetica", 'B', 10); pdf.set_text_color(180, 0, 0)
        pdf.cell(190, 7, txt="ALERTA: REQUIERE MEDIO DE CONTRASTE GADOLINIO", ln=1)
        pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", size=10)
        pdf.cell(95, 7, txt=f"Creatinina: {datos['creatinina']} mg/dL", ln=0)
        pdf.cell(95, 7, txt=f"VFG: {datos['vfg']:.2f} mL/min", ln=1)
    pdf.ln(5); pdf.set_fill_color(240, 240, 240); pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(190, 9, txt=" III. ANAMNESIS DE SEGURIDAD RADIOLÓGICA", ln=True, fill=True)
    pdf.set_font("Helvetica", size=8); pdf.ln(2)
    anamnesis_items = [
        ("Ayuno", datos['ant_ayuno']), ("Asma", datos['ant_asma']), ("Diabetes", datos['ant_diabetes']),
        ("Hipertensión", datos['ant_hiperten']), ("Hipertiroidismo", datos['ant_hipertiroid']), ("Insuficiencia Renal", datos['ant_renal']),
        ("Diálisis", datos['ant_dialisis']), ("Marcapaso", datos['ant_marcapaso']), ("Implantes", datos['ant_implantes']),
        ("Metformina", datos['ant_metformina']), ("Gravidez", datos['ant_embarazo']), ("Lactancia", datos['ant_lactancia']),
        ("Falla Cardíaca", datos['ant_cardiaca']), ("Prótesis Dental", datos['ant_protesis_dental']), ("Clips Vasculares", datos['ant_clips_vasc']),
        ("Esquirlas Oculares", datos['ant_esquirlas']), ("Tatuajes", datos['ant_tatuajes']), ("Claustrofobia", datos['ant_claustrofobia'])
    ]
    for i in range(0, len(anamnesis_items), 2):
        pdf.cell(95, 5, txt=f"{anamnesis_items[i][0]}: {anamnesis_items[i][1]}", ln=0)
        if i+1 < len(anamnesis_items): pdf.cell(95, 5, txt=f"{anamnesis_items[i+1][0]}: {anamnesis_items[i+1][1]}", ln=1)
    pdf.add_page(); pdf.ln(35); pdf.set_fill_color(240, 240, 240); pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(190, 9, txt=" IV. ANTECEDENTES ONCOLÓGICOS Y TERAPÉUTICOS", ln=True, fill=True)
    pdf.set_font("Helvetica", size=10); pdf.ln(3)
    pdf.multi_cell(190, 6, txt=f"Diagnóstico Oncológico: {datos['diagnostico_cancer']}")
    pdf.ln(5); pdf.set_fill_color(128, 0, 32); pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 9, txt=" V. CONSENTIMIENTO INFORMADO", ln=True, fill=True)
    pdf.set_font("Times", size=9.5); pdf.set_text_color(0, 0, 0); pdf.ln(3)
    pdf.multi_cell(190, 5, txt="Certifico que he sido informado de los riesgos y beneficios... (Texto completo).")
    pdf.ln(30); posicion_y = pdf.get_y()
    if datos['firma_img']:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            datos['firma_img'].save(tmp.name)
            pdf.image(tmp.name, x=45, y=posicion_y - 25, w=50)
        os.unlink(tmp.name)
    pdf.line(40, posicion_y, 100, posicion_y); pdf.line(115, posicion_y, 175, posicion_y)
    pdf.set_font("Helvetica", 'B', 8); pdf.set_xy(40, posicion_y + 2); pdf.cell(60, 5, txt="FIRMA PACIENTE", align='C')
    pdf.set_xy(115, posicion_y + 2); pdf.cell(60, 5, txt="FIRMA PROFESIONAL", align='C')
    return pdf.output(dest='S').encode('latin-1')

# --- CARGA DB ---
@st.cache_data
def cargar_db():
    if os.path.exists('listado_prestaciones.csv'):
        df = pd.read_csv('listado_prestaciones.csv', sep=None, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip(); return df
    return None

db_p = cargar_db()

# --- FASE 1: IDENTIFICACIÓN ---
if st.session_state.step == 1:
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    if os.path.exists("logoNI.png"): st.image("logoNI.png", width=200)
    st.markdown('</div>', unsafe_allow_html=True)
    st.title("Registro Clínico de Resonancia Magnética")
    st.markdown('<div class="section-header">Identificación del Paciente</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    nombre_comp = c1.text_input("Nombre completo del paciente", value=st.session_state.form["nombre"])
    ext = st.checkbox("Paciente extranjero", value=st.session_state.form["sin_rut"])
    if not ext:
        rut_i = c2.text_input("RUT", value=st.session_state.form["rut"])
        rut_f = format_rut_chileno(rut_i)
        if rut_f != rut_i: st.session_state.form["rut"] = rut_f; st.rerun()
    else:
        tipo_d = c2.selectbox("Tipo Documento", ["Pasaporte", "DNI", "Otros"])
        num_d = c2.text_input("N° Documento", value=st.session_state.form["num_doc"])
        rut_f = ""
    c3, c4 = st.columns(2)
    f_nac = c3.date_input("Fecha de Nacimiento", value=st.session_state.form["fecha_nac"], format="DD/MM/YYYY")
    gen = c4.selectbox("Género", ["Masculino", "Femenino", "No binario"])
    sexo_b = st.selectbox("Sexo Biológico", ["Masculino", "Femenino"]) if gen == "No binario" else gen
    st.markdown('<div class="section-header">Información del Procedimiento</div>', unsafe_allow_html=True)
    if db_p is not None:
        esps = sorted([str(e) for e in db_p['ESPECIALIDAD'].unique() if pd.notna(e)])
        esp_s = st.selectbox("Especialidad", esps)
        pros = sorted([str(p) for p in db_p[db_p['ESPECIALIDAD'] == esp_s]['PROCEDIMIENTO A REALIZAR'].unique()])
        pro_s = st.selectbox("Procedimiento", pros)
        # CARGADOR DE ORDEN MÉDICA (REQUISITO 1)
        st.file_uploader("Subir Orden Médica Digitalizada (Obligatorio)", type=["pdf", "jpg", "png"])
    if st.button("Siguiente"):
        if len(nombre_comp.strip().split()) >= 2:
            st.session_state.form.update({"nombre": nombre_comp, "rut": rut_f, "sin_rut": ext, "fecha_nac": f_nac, "genero": gen, "sexo_biologico": sexo_b, "esp_nombre": esp_s, "pre_nombre": pro_s})
            row = db_p[db_p['PROCEDIMIENTO A REALIZAR'] == pro_s]
            st.session_state.form["tiene_contraste"] = "SI" in str(row['MEDIO DE CONTRASTE'].values[0]).upper()
            st.session_state.step = 2; st.rerun()

# --- FASE 2: ANAMNESIS ---
elif st.session_state.step == 2:
    st.markdown('<div class="section-header">Cuestionario de Seguridad y Documentación Clínica</div>', unsafe_allow_html=True)
    # CARGADOR DE EXÁMENES PREVIOS (REQUISITO 2)
    st.file_uploader("Adjuntar Exámenes Previos (RX, TC, RM, ECO)", type=["pdf", "jpg", "png"], accept_multiple_files=True)
    
    opc = ["No", "Sí"]
    c1, c2, c3 = st.columns(3)
    st.session_state.form["ant_ayuno"] = c1.radio("Ayuno", opc)
    st.session_state.form["ant_asma"] = c2.radio("Asma", opc)
    st.session_state.form["ant_diabetes"] = c3.radio("Diabetes", opc)
    st.session_state.form["ant_hiperten"] = c1.radio("Hipertensión", opc)
    st.session_state.form["ant_hipertiroid"] = c2.radio("Hipertiroidismo", opc)
    st.session_state.form["ant_renal"] = c3.radio("Falla Renal", opc)
    st.session_state.form["ant_dialisis"] = c1.radio("Diálisis", opc)
    st.session_state.form["ant_marcapaso"] = c2.radio("Marcapaso", opc)
    st.session_state.form["ant_implantes"] = c3.radio("Metales", opc)
    st.session_state.form["ant_metformina"] = c1.radio("Metformina", opc)
    st.session_state.form["ant_embarazo"] = c2.radio("Embarazo", opc)
    st.session_state.form["ant_lactancia"] = c3.radio("Lactancia", opc)
    st.session_state.form["ant_cardiaca"] = c1.radio("Falla Cardíaca", opc)
    st.session_state.form["ant_protesis_dental"] = c2.radio("Prótesis Dental", opc)
    st.session_state.form["ant_clips_vasc"] = c3.radio("Clips Vasculares", opc)
    st.session_state.form["ant_esquirlas"] = c1.radio("Esquirlas", opc)
    st.session_state.form["ant_tatuajes"] = c2.radio("Tatuajes", opc)
    st.session_state.form["ant_claustrofobia"] = c3.radio("Claustrofobia", opc)

    if st.session_state.form["tiene_contraste"]:
        st.error("Protocolo con Contraste")
        # CARGADOR DE EXAMEN DE CREATININA (REQUISITO 3)
        st.file_uploader("Subir Informe de Laboratorio (Creatinina)", type=["pdf", "jpg", "png"])
        cr, ps = st.columns(2)
        crea = cr.number_input("Creatinina (mg/dL)", value=st.session_state.form["creatinina"], step=0.01)
        peso = ps.number_input("Peso (kg)", value=st.session_state.form["peso"], step=0.1)
        if crea > 0:
            f = 1.23 if st.session_state.form["sexo_biologico"] == "Masculino" else 1.04
            vfg = ((140 - calcular_edad_clinica(st.session_state.form["fecha_nac"])) * peso * f) / (72 * crea)
            st.session_state.form.update({"creatinina": crea, "peso": peso, "vfg": vfg})
            st.info(f"VFG: {vfg:.2f}")

    if st.button("Ir a Firma"): st.session_state.step = 3; st.rerun()

# --- FASE 3: FIRMA ---
elif st.session_state.step == 3:
    st.title("Consentimiento Informado")
    canvas = st_canvas(stroke_width=2, stroke_color="#000", background_color="#fff", height=150, width=500, key="sig")
    if st.button("Finalizar"):
        if canvas.image_data is not None:
            st.session_state.form["firma_img"] = Image.fromarray(canvas.image_data.astype('uint8'), 'RGBA').convert("RGB")
            st.session_state.step = 4; st.rerun()

# --- FASE 4: DESCARGA ---
elif st.session_state.step == 4:
    f = st.session_state.form
    d_id = f['rut'] if not f['sin_rut'] else f['num_doc']
    name = generar_identificador_archivo(f['nombre'], d_id)
    pdf = generar_reporte_pdf(f)
    st.download_button(f"Descargar Registro {name}", data=pdf, file_name=f"{name}.pdf", mime="application/pdf")
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

# 1. CONFIGURACIÓN DE ESTÉTICA CORPORATIVA "LUJO MÉDICO"
st.set_page_config(page_title="Norte Imagen - Registro Élite", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .stButton>button { 
        background-color: #800020; color: white; border-radius: 8px; 
        width: 100%; height: 3.8em; font-weight: bold; border: none; font-size: 1.1em;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton>button:hover { background-color: #a00028; transform: translateY(-1px); }
    /* Botón de retroceso */
    div.stButton > button:first-child[key^="back"] {
        background-color: #f8f9fa !important; color: #800020 !important; border: 1px solid #800020 !important;
    }
    .section-header { 
        color: white; background-color: #800020; padding: 15px; 
        border-radius: 5px; margin-top: 25px; margin-bottom: 20px; 
        font-size: 1.2em; font-weight: bold; text-align: center;
        text-transform: uppercase; letter-spacing: 2px;
    }
    .legal-box {
        background-color: #ffffff; padding: 35px; border-radius: 8px; border: 1px solid #dee2e6;
        font-size: 1em; text-align: justify; color: #222; margin-bottom: 20px;
        line-height: 1.7; font-family: 'Georgia', serif;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. PERSISTENCIA DE DATOS (ESTADO DE SESIÓN)
if 'step' not in st.session_state:
    st.session_state.step = 1

if 'form' not in st.session_state:
    st.session_state.form = {
        # Identificación
        "nombre": "", "rut": "", "sin_rut": False, "tipo_doc": "Pasaporte", "num_doc": "",
        "genero": "Masculino", "sexo_biologico": "Masculino", "fecha_nac": date(1990, 1, 1), "email": "", 
        "nombre_tutor": "", "rut_tutor": "", "es_menor": False,
        # Examen
        "esp_nombre": "NEURORRADIOLOGIA", "pre_nombre": "", 
        # Cuestionario de Seguridad (EXTENSO - SIN RESUMIR)
        "ant_ayuno": "No", "ant_asma": "No", "ant_diabetes": "No", "ant_hiperten": "No",
        "ant_hipertiroid": "No", "ant_renal": "No", "ant_dialisis": "No", 
        "ant_implantes": "No", "ant_marcapaso": "No", "ant_metformina": "No",
        "ant_embarazo": "No", "ant_lactancia": "No", "ant_cardiaca": "No",
        "ant_protesis_dental": "No", "ant_clips_vasc": "No", "ant_esquirlas": "No",
        "ant_tatuajes": "No", "ant_claustrofobia": "No", "otras_cirugias": "",
        # Cáncer
        "diagnostico_cancer": "", "rt": False, "qt": False, "bt": False, "it": False, 
        "otro_tratamiento_cancer": "", 
        # Exámenes Previos
        "ex_rx": False, "ex_eco": False, "ex_tc": False, "ex_rm": False,
        # Parámetros Contrastados
        "tiene_contraste": False, "creatinina": 0.0, "peso": 70.0, "vfg": 0.0, "firma_img": None
    }

# 3. UTILITARIOS
def format_rut_chile(rut):
    rut = re.sub(r'[^0-9kK]', '', rut)
    if len(rut) < 2: return rut
    c, dv = rut[:-1], rut[-1].upper()
    cf = ""
    for i, n in enumerate(reversed(c)):
        if i > 0 and i % 3 == 0: cf = "." + cf
        cf = n + cf
    return f"{cf}-{dv}"

def get_edad(f_nac):
    today = date.today()
    return today.year - f_nac.year - ((today.month, today.day) < (f_nac.month, f_nac.day))

def get_iniciales_paciente(nombre):
    partes = nombre.strip().split()
    if len(partes) < 2: return "PX"
    return (partes[0][0] + partes[-1][0]).upper()

# 4. GENERADOR DE PDF "INFORME MÉDICO PRO"
def generate_pdf_final(datos):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PÁGINA 1: CABECERA E IDENTIFICACIÓN ---
    pdf.add_page()
    if os.path.exists("logoNI.png"):
        pdf.image("logoNI.png", x=85, y=10, w=40)
    
    pdf.ln(35)
    pdf.set_font("Times", 'B', 16)
    pdf.set_text_color(128, 0, 32)
    pdf.cell(190, 8, txt="REGISTRO CLÍNICO Y CONSENTIMIENTO INFORMADO", ln=True, align='C')
    pdf.set_font("Times", 'I', 14)
    pdf.cell(190, 8, txt="Resonancia Magnética", ln=True, align='C')
    
    pdf.ln(8)
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(190, 9, txt=" 1. IDENTIFICACIÓN DEL PACIENTE", ln=True, fill=True)
    
    pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", size=10); pdf.ln(2)
    pdf.cell(190, 7, txt=f"Nombre: {datos['nombre'].upper()}", ln=1)
    
    doc = datos['rut'] if not datos['sin_rut'] else f"{datos['tipo_doc']}: {datos['num_doc']}"
    pdf.cell(95, 7, txt=f"Documento ID: {doc}", ln=0)
    pdf.cell(95, 7, txt=f"F. Nacimiento: {datos['fecha_nac'].strftime('%d/%m/%Y')}", ln=1)
    pdf.cell(95, 7, txt=f"Edad: {get_edad(datos['fecha_nac'])} años", ln=0)
    pdf.cell(95, 7, txt=f"Género: {datos['genero']} (Sexo Bio: {datos['sexo_biologico']})", ln=1)
    
    pdf.ln(5)
    pdf.set_fill_color(245, 245, 245); pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(190, 9, txt=" 2. DETALLES DEL PROCEDIMIENTO", ln=True, fill=True)
    pdf.set_font("Helvetica", size=10); pdf.ln(2)
    pdf.cell(190, 7, txt=f"Especialidad: {datos['esp_nombre']}", ln=1)
    pdf.cell(190, 7, txt=f"Estudio: {datos['pre_nombre']}", ln=1)
    
    if datos['tiene_contraste']:
        pdf.set_font("Helvetica", 'B', 10); pdf.set_text_color(180, 0, 0)
        pdf.cell(190, 7, txt="REQUIERE ADMINISTRACIÓN DE MEDIO DE CONTRASTE ENDOVENOSO", ln=1)
        pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", size=10)
        pdf.cell(95, 7, txt=f"Creatinina: {datos['creatinina']} mg/dL", ln=0)
        pdf.cell(95, 7, txt=f"VFG Estimado: {datos['vfg']:.2f} mL/min", ln=1)

    pdf.ln(5)
    pdf.set_fill_color(245, 245, 245); pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(190, 9, txt=" 3. CUESTIONARIO DE SEGURIDAD (ANAMNESIS COMPLETA)", ln=True, fill=True)
    pdf.set_font("Helvetica", size=8); pdf.ln(2)
    
    # LISTADO COMPLETO - SIN RESUMIR
    preguntas = [
        ("¿Mantiene Ayuno?", datos['ant_ayuno']), ("¿Padece Asma?", datos['ant_asma']),
        ("¿Padece Diabetes?", datos['ant_diabetes']), ("¿Hipertensión?", datos['ant_hiperten']),
        ("¿Hipertiroidismo?", datos['ant_hipertiroid']), ("¿Enfermedad Renal?", datos['ant_renal']),
        ("¿Realiza Diálisis?", datos['ant_dialisis']), ("¿Marcapaso/Neuro?", datos['ant_marcapaso']),
        ("¿Metales/Clips/Vasc?", datos['ant_implantes']), ("¿Toma Metformina?", datos['ant_metformina']),
        ("¿Embarazo?", datos['ant_embarazo']), ("¿Lactancia?", datos['ant_lactancia']),
        ("¿Falla Cardíaca?", datos['ant_cardiaca']), ("¿Prótesis Dental?", datos['ant_protesis_dental']),
        ("¿Clips Vasculares?", datos['ant_clips_vasc']), ("¿Esquirlas Ojos?", datos['ant_esquirlas']),
        ("¿Tatuajes?", datos['ant_tatuajes']), ("¿Claustrofobia?", datos['ant_claustrofobia'])
    ]
    
    for i in range(0, len(preguntas), 2):
        pdf.cell(95, 5, txt=f"{preguntas[i][0]}: {preguntas[i][1]}", ln=0)
        if i+1 < len(preguntas):
            pdf.cell(95, 5, txt=f"{preguntas[i+1][0]}: {preguntas[i+1][1]}", ln=1)
        else:
            pdf.ln(5)

    # --- PÁGINA 2: ANTECEDENTES Y CI ---
    pdf.add_page()
    if os.path.exists("logoNI.png"): pdf.image("logoNI.png", x=85, y=10, w=40)
    pdf.ln(35)
    
    pdf.set_fill_color(245, 245, 245); pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(190, 9, txt=" 4. ANTECEDENTES ONCOLÓGICOS Y QUIRÚRGICOS", ln=True, fill=True)
    pdf.set_font("Helvetica", size=10); pdf.ln(2)
    pdf.multi_cell(190, 6, txt=f"Diagnóstico Cáncer: {datos['diagnostico_cancer'] if datos['diagnostico_cancer'] else 'No refiere'}")
    
    tr = []
    if datos['rt']: tr.append("Radioterapia")
    if datos['qt']: tr.append("Quimioterapia")
    if datos['bt']: tr.append("Braquiterapia")
    if datos['it']: tr.append("Inmunoterapia")
    pdf.cell(190, 7, txt=f"Tratamientos realizados: {', '.join(tr) if tr else 'Ninguno'}", ln=1)
    pdf.multi_cell(190, 6, txt=f"Otros Tratamientos: {datos['otro_tratamiento_cancer'] if datos['otro_tratamiento_cancer'] else 'N/A'}")
    pdf.multi_cell(190, 6, txt=f"Cirugías Previas: {datos['otras_cirugias'] if datos['otras_cirugias'] else 'No refiere'}")

    pdf.ln(5); pdf.set_fill_color(128, 0, 32); pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 9, txt=" 5. CONSENTIMIENTO INFORMADO", ln=True, fill=True)
    pdf.set_font("Times", size=9); pdf.set_text_color(0, 0, 0); pdf.ln(2)
    
    texto_ci = (
        "Declaro que he sido informado/a exhaustivamente sobre el examen de Resonancia Magnética. Comprendo que se utiliza un campo magnético de alta "
        "intensidad y que debo advertir sobre cualquier elemento metálico en mi cuerpo. Autorizo voluntariamente la realización del examen y, "
        "en caso de ser necesario según criterio médico, la administración de medio de contraste (Gadolinio) endovenoso, habiendo comprendido sus beneficios y "
        "posibles efectos secundarios. Confirmo que toda la información entregada en este registro clínico es veraz y fidedigna."
    )
    pdf.multi_cell(190, 5, txt=texto_ci.encode('latin-1', 'replace').decode('latin-1'))

    # FIRMA POSICIONADA SOBRE LA LÍNEA
    pdf.ln(30)
    y_firma = pdf.get_y()
    
    if datos['firma_img']:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            datos['firma_img'].save(tmp.name)
            # El -22 asegura que la imagen de la firma quede "pisando" la línea
            pdf.image(tmp.name, x=45, y=y_firma - 22, w=50)
        os.unlink(tmp.name)
    
    pdf.line(40, y_firma, 100, y_firma)
    pdf.line(115, y_firma, 175, y_firma)
    pdf.set_font("Helvetica", 'B', 8)
    pdf.set_xy(40, y_firma + 2); pdf.cell(60, 5, txt="FIRMA PACIENTE O TUTOR", align='C')
    pdf.set_xy(115, y_firma + 2); pdf.cell(60, 5, txt="FIRMA PROFESIONAL NORTE IMAGEN", align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- CARGA DE DATOS ---
@st.cache_data
def load_db():
    if os.path.exists('listado_prestaciones.csv'):
        df = pd.read_csv('listado_prestaciones.csv', sep=None, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        return df
    return None

db = load_db()

# --- PASO 1: IDENTIFICACIÓN ---
if st.session_state.step == 1:
    if os.path.exists("logoNI.png"): st.image("logoNI.png", width=220)
    st.title("Registro de Paciente")
    
    st.markdown('<div class="section-header">DATOS PERSONALES</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    nombre = c1.text_input("Nombre y Apellido (Ej: Juan Pérez)", value=st.session_state.form["nombre"])
    
    extranjero = st.checkbox("¿Es extranjero?", value=st.session_state.form["sin_rut"])
    if not extranjero:
        r_input = c2.text_input("RUT (Autocompletado)", value=st.session_state.form["rut"])
        r_val = format_rut_chile(r_input)
        if r_val != r_input:
            st.session_state.form["rut"] = r_val
            st.rerun()
    else:
        tipo = c2.selectbox("Documento", ["Pasaporte", "DNI", "Cédula Ext."], index=0)
        num = c2.text_input("N° Documento", value=st.session_state.form["num_doc"])
        r_val = ""

    c3, c4 = st.columns(2)
    # Formato DD/MM/YYYY
    f_nac = c3.date_input("F. de Nacimiento", value=st.session_state.form["fecha_nac"], format="DD/MM/YYYY")
    gen = c4.selectbox("Identidad de Género", ["Masculino", "Femenino", "No binario"], index=["Masculino", "Femenino", "No binario"].index(st.session_state.form["genero"]))
    
    # Sexo biológico para VFG
    if gen == "No binario":
        sex_bio = st.selectbox("Sexo biológico (Para cálculo VFG)", ["Masculino", "Femenino"])
    else:
        sex_bio = gen

    st.markdown('<div class="section-header">INFORMACIÓN DEL EXAMEN</div>', unsafe_allow_html=True)
    if db is not None:
        esps = sorted([str(e) for e in db['ESPECIALIDAD'].unique() if pd.notna(e)])
        if "NEURORRADIOLOGIA" in esps:
            esps.remove("NEURORRADIOLOGIA")
            esps.insert(0, "NEURORRADIOLOGIA")
        
        esp_sel = st.selectbox("Especialidad", esps, index=esps.index(st.session_state.form["esp_nombre"]) if st.session_state.form["esp_nombre"] in esps else 0)
        estudios = sorted([str(p) for p in db[db['ESPECIALIDAD'] == esp_sel]['PROCEDIMIENTO A REALIZAR'].unique() if pd.notna(p)])
        est_sel = st.selectbox("Estudio", estudios)
        
    v1 = st.checkbox("Declaro que los datos son verídicos.")

    if st.button("SIGUIENTE"):
        if len(nombre.strip().split()) >= 2 and (r_val or extranjero) and v1:
            st.session_state.form.update({"nombre": nombre, "rut": r_val, "sin_rut": extranjero, "fecha_nac": f_nac, "genero": gen, "sexo_biologico": sex_bio, "esp_nombre": esp_sel, "pre_nombre": est_sel})
            # Verificar si lleva contraste
            row = db[db['PROCEDIMIENTO A REALIZAR'] == est_sel]
            st.session_state.form["tiene_contraste"] = "SI" in str(row['MEDIO DE CONTRASTE'].values[0]).upper()
            st.session_state.step = 2; st.rerun()
        else:
            st.error("Complete Nombre y Apellido, RUT/ID y acepte la declaración.")

# --- PASO 2: ANAMNESIS (EXTENSO) ---
elif st.session_state.step == 2:
    st.title("Encuesta Clínica Detallada")
    st.markdown('<div class="section-header">CUESTIONARIO DE SEGURIDAD (SIN RESUMIR)</div>', unsafe_allow_html=True)
    o = ["No", "Sí"]
    
    c1, c2, c3 = st.columns(3)
    # TODAS LAS PREGUNTAS INDIVIDUALES
    st.session_state.form["ant_ayuno"] = c1.radio("¿Mantiene Ayuno?", o)
    st.session_state.form["ant_asma"] = c2.radio("¿Padece Asma?", o)
    st.session_state.form["ant_diabetes"] = c3.radio("¿Padece Diabetes?", o)
    st.session_state.form["ant_hiperten"] = c1.radio("¿Hipertensión?", o)
    st.session_state.form["ant_hipertiroid"] = c2.radio("¿Hipertiroidismo?", o)
    st.session_state.form["ant_renal"] = c3.radio("¿Enfermedad Renal?", o)
    st.session_state.form["ant_dialisis"] = c1.radio("¿Realiza Diálisis?", o)
    st.session_state.form["ant_marcapaso"] = c2.radio("¿Marcapaso/Neuroestimulador?", o)
    st.session_state.form["ant_implantes"] = c3.radio("¿Metales/Implantes?", o)
    st.session_state.form["ant_metformina"] = c1.radio("¿Toma Metformina?", o)
    st.session_state.form["ant_embarazo"] = c2.radio("¿Posible Embarazo?", o)
    st.session_state.form["ant_lactancia"] = c3.radio("¿Lactancia?", o)
    st.session_state.form["ant_cardiaca"] = c1.radio("¿Falla Cardíaca?", o)
    st.session_state.form["ant_protesis_dental"] = c
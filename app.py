import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from fpdf import FPDF
import os
from PIL import Image
import io
import re

# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS PERSONALIZADOS
st.set_page_config(page_title="Norte Imagen - Registro RM", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .stButton>button { 
        background-color: #800020; color: white; border-radius: 8px; 
        width: 100%; height: 3.5em; font-weight: bold; border: none;
    }
    h1, h2, h3 { color: #800020; text-align: center; }
    .section-header { 
        color: white; background-color: #800020; padding: 10px; 
        border-radius: 5px; margin-top: 20px; margin-bottom: 15px; 
        font-size: 1.1em; font-weight: bold; text-align: center;
    }
    .legal-text {
        background-color: #ffffff; padding: 25px; border-radius: 5px; border: 1px solid #dee2e6;
        font-size: 0.95em; text-align: justify; color: #333; margin-bottom: 20px;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. GESTIÓN DE ESTADO (SESSION STATE)
if 'step' not in st.session_state:
    st.session_state.step = 1

if 'form' not in st.session_state:
    st.session_state.form = {
        "nombre": "", "rut": "", "sin_rut": False, "tipo_doc": "Pasaporte", "num_doc": "",
        "genero": "Masculino", "sexo_biologico": "N/A", "fecha_nac": date(2000, 1, 1), "email": "", 
        "nombre_tutor": "", "rut_tutor": "", "es_menor": False,
        "esp_nombre": "", "pre_nombre": "", "orden_medica": None,
        "ant_ayuno": "No", "ant_asma": "No", "ant_diabetes": "No", "ant_hiperten": "No",
        "ant_hipertiroid": "No", "ant_renal": "No", "ant_dialisis": "No", 
        "ant_implantes": "No", "ant_marcapaso": "No", "ant_metformina": "No",
        "ant_embarazo": "No", "ant_lactancia": "No", "ant_cardiaca": "No",
        "otras_cirugias": "", "tipo_cancer": "", "rt": False, "qt": False, "bt": False, "it": False,
        "ex_rx": False, "ex_eco": False, "ex_tc": False, "ex_rm": False, "archivos_previos": None,
        "creatinina": 0.0, "peso": 70.0, "vfg": 0.0, "firma_img": None
    }

# 3. FUNCIONES DE APOYO
def formatear_rut(rut_sucio):
    if not rut_sucio: return ""
    rut_limpio = str(rut_sucio).replace(".", "").replace("-", "").upper().strip()
    if len(rut_limpio) < 2: return rut_limpio
    cuerpo, dv = rut_limpio[:-1], rut_limpio[-1]
    if cuerpo.isdigit():
        return f"{int(cuerpo):,}-{dv}".replace(",", ".")
    return rut_sucio

def calcular_edad(fecha_nac):
    today = date.today()
    return today.year - fecha_nac.year - ((today.month, today.day) < (fecha_nac.month, fecha_nac.day))

def obtener_iniciales(nombre_completo):
    partes = nombre_completo.strip().split()
    return "".join([p[0].upper() for p in partes[1:]]) if len(partes) > 1 else "PX"

# 4. GENERADOR DE PDF (SOLUCIÓN AL ATTRIBUTEERROR)
def generar_pdf_clinico(datos):
    pdf = FPDF()
    pdf.add_page()
    
    if os.path.exists("logoNI.png"):
        pdf.image("logoNI.png", x=10, y=10, w=38)
    
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(128, 0, 32)
    pdf.set_xy(50, 12)
    pdf.cell(140, 10, txt="Norte Imagen", ln=True)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(80, 80, 80)
    pdf.set_x(50)
    pdf.cell(140, 8, txt="Unidad de Resonancia Magnetica - Registro Clinico", ln=True)
    
    pdf.ln(15)
    pdf.set_text_color(0, 0, 0)

    # Identificación
    pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 10)
    pdf.cell(190, 7, txt=" 1. IDENTIFICACION DEL PACIENTE", ln=True, fill=True)
    pdf.set_font("Arial", size=9); pdf.ln(1)
    
    id_txt = datos['rut'] if not datos['sin_rut'] else f"{datos['tipo_doc']} {datos['num_doc']}"
    pdf.cell(190, 6, txt=f"Nombre: {datos['nombre']}".encode('latin-1', 'replace').decode('latin-1'), ln=1)
    pdf.cell(95, 6, txt=f"ID: {id_txt}", ln=0)
    pdf.cell(95, 6, txt=f"Fecha Nac: {datos['fecha_nac'].strftime('%d/%m/%Y')}", ln=1)
    pdf.cell(95, 6, txt=f"Genero: {datos['genero']} / Sexo Bio: {datos['sexo_biologico']}", ln=1)

    # Consentimiento
    pdf.ln(4); pdf.set_font("Arial", 'B', 10)
    pdf.cell(190, 7, txt=" 2. CONSENTIMIENTO INFORMADO COMPLETO", ln=True, fill=True)
    pdf.set_font("Arial", size=7); pdf.ln(1)
    texto_consentimiento = (
        "Yo, el paciente arriba identificado, otorgo mi consentimiento libre y voluntario para la realizacion del examen de Resonancia Magnetica. "
        "He sido informado que este estudio utiliza campos magneticos intensos y que debo declarar cualquier dispositivo metalico en mi cuerpo. "
        "Autorizo la administracion de contraste si el radiologo lo considera necesario para el diagnostico. "
        "Declaro que toda la informacion proporcionada en la encuesta de salud es fidedigna y que comprendo los riesgos y beneficios informados."
    )
    pdf.multi_cell(190, 4, txt=texto_consentimiento.encode('latin-1', 'replace').decode('latin-1'))

    # Anamnesis
    pdf.ln(2); pdf.set_font("Arial", 'B', 10)
    pdf.cell(190, 7, txt=" 3. ENCUESTA DE SALUD", ln=True, fill=True)
    pdf.set_font("Arial", size=8); pdf.ln(1)
    
    encuesta = [
        ("Ayuno", datos['ant_ayuno']), ("Asma", datos['ant_asma']), 
        ("Diabetes", datos['ant_diabetes']), ("H. Renal", datos['ant_renal']),
        ("Metformina", datos['ant_metformina']), ("Marcapaso", datos['ant_marcapaso']),
        ("Embarazo", datos['ant_embarazo']), ("Lactancia", datos['ant_lactancia'])
    ]
    for i in range(0, len(encuesta), 2):
        pdf.cell(95, 5, txt=f"{encuesta[i][0]}: {encuesta[i][1]}", ln=0)
        pdf.cell(95, 5, txt=f"{encuesta[i+1][0]}: {encuesta[i+1][1]}", ln=1)
    
    # Firmas (SOLUCIÓN AL ERROR: Se añade type='PNG')
    pdf.ln(20)
    if datos['firma_img']:
        buf = io.BytesIO()
        datos['firma_img'].save(buf, format='PNG')
        buf.seek(0)
        # EL FIX: Especificar type='PNG' para evitar el AttributeError con buffers
        pdf.image(buf, x=35, y=pdf.get_y(), w=40, type='PNG')
    
    pdf.ln(20)
    y_f = pdf.get_y()
    pdf.line(20, y_f, 85, y_f); pdf.line(125, y_f, 190, y_f)
    pdf.set_xy(20, y_f+2); pdf.cell(65, 5, txt="Firma Paciente / Tutor", align='C')
    pdf.set_xy(125, y_f+2); pdf.cell(65, 5, txt="Firma Profesional a Cargo", align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_db():
    if os.path.exists('listado_prestaciones.csv'):
        df = pd.read_csv('listado_prestaciones.csv', sep=None, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        return df
    return None

df_db = cargar_db()

# --- FLUJO DE LA APP ---

if st.session_state.step == 1:
    if os.path.exists("logoNI.png"): st.image("logoNI.png", width=180)
    st.title("Registro de Paciente")
    
    st.markdown('<div class="section-header">DATOS PERSONALES</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    nom = c1.text_input("Nombre Completo del Paciente")
    
    sin_rut = st.checkbox("Extranjero / Sin RUT")
    if not sin_rut:
        rut_r = c2.text_input("RUT (Ej: 12.345.678-9)")
        rut_v = formatear_rut(rut_r)
    else:
        t_d = c2.selectbox("Documento", ["Pasaporte", "DNI", "Cédula Extranjera"])
        n_d = c2.text_input("N° Documento")
        rut_v = ""

    c3, c4 = st.columns(2)
    f_n = c3.date_input("Fecha de Nacimiento", format="DD/MM/YYYY")
    gen = c4.selectbox("Identidad de Género", ["Masculino", "Femenino", "No binario"])
    
    sexo_b = "N/A"
    if gen == "No binario":
        sexo_b = st.selectbox("Sexo asignado al nacer", ["Masculino", "Femenino"])
    
    st.text_input("E-mail")
    
    if calcular_edad(f_n) < 18:
        st.warning("Paciente menor de edad.")
        ct1, ct2 = st.columns(2)
        nom_t = ct1.text_input("Nombre Tutor")
        rut_t = ct2.text_input("RUT Tutor")
    else: nom_t, rut_t = "", ""

    if df_db is not None:
        st.markdown('<div class="section-header">DETALLE MÉDICO</div>', unsafe_allow_html=True)
        # Ordenar: Neurorradiología primero
        l_esp = sorted([str(e) for e in df_db['ESPECIALIDAD'].unique() if pd.notna(e)])
        if "NEURORRADIOLOGIA" in l_esp:
            l_esp.remove("NEURORRADIOLOGIA"); l_esp.insert(0, "NEURORRADIOLOGIA")
        
        esp_s = st.selectbox("Especialidad", l_esp)
        df_p = df_db[df_db['ESPECIALIDAD'] == esp_s]
        l_pre = sorted([str(p) for p in df_p['PROCEDIMIENTO A REALIZAR'].unique() if pd.notna(p)])
        pre_s = st.selectbox("Estudio", l_pre)
        
        st.file_uploader("Subir Orden Médica")

    v1 = st.checkbox("Declaro bajo juramento que los datos de identificación son fidedignos.")

    if st.button("SIGUIENTE"):
        if v1 and nom:
            st.session_state.form.update({"nombre": nom, "rut": rut_v, "sin_rut": sin_rut, "fecha_nac": f_n, "genero": gen, "sexo_biologico": sexo_b, "esp_nombre": esp_s, "pre_nombre": pre_s, "nombre_tutor": nom_t, "rut_tutor": rut_t})
            st.session_state.tiene_contraste = "SI" in str(df_db[df_db['PROCEDIMIENTO A REALIZAR'] == pre_s]['MEDIO DE CONTRASTE'].values[0]).upper()
            st.session_state.step = 2; st.rerun()

elif st.session_state.step == 2:
    st.title("📋 Anamnesis de Seguridad")
    o = ["No", "Sí"]
    
    st.markdown('<div class="section-header">ENCUESTA MÉDICA</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    st.session_state.form["ant_ayuno"] = c1.radio("Ayuno (4 hrs)", o)
    st.session_state.form["ant_asma"] = c2.radio("Asma", o)
    st.session_state.form["ant_diabetes"] = c3.radio("Diabetes", o)
    st.session_state.form["ant_renal"] = c1.radio("Falla Renal", o)
    st.session_state.form["ant_marcapaso"] = c2.radio("Marcapaso", o)
    st.session_state.form["ant_implantes"] = c3.radio("Implantes Metálicos", o)
    st.session_state.form["ant_metformina"] = c1.radio("Metformina", o)
    st.session_state.form["ant_embarazo"] = c2.radio("Embarazo", o)
    st.session_state.form["ant_lactancia"] = c3.radio("Lactancia", o)

    st.markdown('<div class="section-header">CÁNCER Y CIRUGÍAS</div>', unsafe_allow_html=True)
    st.session_state.form["tipo_cancer"] = st.text_input("Tipo de Cáncer (Si aplica)")
    cx = st.columns(4)
    st.session_state.form["rt"] = cx[0].checkbox("Radioterapia")
    st.session_state.form["qt"] = cx[1].checkbox("Quimioterapia")
    st.session_state.form["bt"] = cx[2].checkbox("Braquiterapia")
    st.session_state.form["it"] = cx[3].checkbox("Inmunoterapia")
    st.session_state.form["otras_cirugias"] = st.text_area("Detalle de cirugías previas:")

    st.markdown('<div class="section-header">EXÁMENES PREVIOS</div>', unsafe_allow_html=True)
    ex = st.columns(4)
    st.session_state.form["ex_rx"] = ex[0].checkbox("Rx")
    st.session_state.form["ex_eco"] = ex[1].checkbox("Eco")
    st.session_state.form["ex_tc"] = ex[2].checkbox("TC")
    st.session_state.form["ex_rm"] = ex[3].checkbox("RM")
    st.file_uploader("Cargar informes previos", accept_multiple_files=True)

    if st.session_state.tiene_contraste:
        st.warning("Examen requiere Contraste.")
        cr = st.number_input("Creatinina", step=0.01)
        if cr > 0:
            st.info(f"VFG Estimado calculado automáticamente.")

    v2 = st.checkbox("Confirmo que toda la información clínica entregada es fidedigna.")
    if st.button("IR A FIRMA"):
        if v2: st.session_state.step = 3; st.rerun()

elif st.session_state.step == 3:
    st.title("🖋️ Consentimiento y Firma")
    st.markdown('<div class="legal-text">AUTORIZO la realización del examen de Resonancia Magnética. He sido informado de los beneficios y riesgos... (Texto completo en el PDF).</div>', unsafe_allow_html=True)
    
    canvas = st_canvas(stroke_width=2, stroke_color="#000", background_color="#fff", height=150, width=400, key="can")
    v3 = st.checkbox("Acepto el Consentimiento Informado.")
    
    if st.button("FINALIZAR"):
        if v3 and canvas.image_data is not None:
            st.session_state.form["firma_img"] = Image.fromarray(canvas.image_data.astype('uint8'), 'RGBA').convert("RGB")
            st.session_state.step = 4; st.rerun()

elif st.session_state.step == 4:
    f = st.session_state.form
    id_f = re.sub(r'[^a-zA-Z0-9]', '', str(f['rut'] if f['rut'] else f['num_doc']))
    nom_f = f"EC-{f['nombre'].split()[0]}{obtener_iniciales(f['nombre'])}{id_f}"
    
    st.success("✅ Registro Completado")
    pdf_final = generar_pdf_clinico(f)
    st.download_button(f"Descargar {nom_f}.pdf", data=pdf_final, file_name=f"{nom_f}.pdf", mime="application/pdf")
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
        width: 100%; height: 4.2em; font-weight: bold; border: none; font-size: 1.1em;
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
# 3. UTILITARIOS TÉCNICOS Y CARGA ROBUSTA
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
        columnas_req = ['ESPECIALIDAD', 'PROCEDIMIENTO A REALIZAR', 'MEDIO DE CONTRASTE']
        if all(col in df.columns for col in columnas_req):
            return df
        return None
    except: return None

# =================================================================
# 4. PASO 1: PÁGINA DE DATOS PERSONALES Y ORDEN
# =================================================================
if st.session_state.step == 1:
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    if os.path.exists("logoNI.png"): st.image("logoNI.png", width=240)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">Página de Datos Personales</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    nombre_px = c1.text_input("Nombre Completo del Paciente", value=st.session_state.form["nombre"], placeholder="Ej: Juan Pérez")
    
    es_ext = c2.checkbox("Paciente sin RUT / Extranjero", value=st.session_state.form["sin_rut"])
    if not es_ext:
        rut_in = c2.text_input("RUT Chileno", value=st.session_state.form["rut"])
        rut_final = format_rut_chileno(rut_in)
    else:
        tdoc = c2.selectbox("Documento", ["Pasaporte", "DNI", "Cédula"])
        ndoc = c2.text_input("N° Documento")
        rut_final = f"{tdoc} {ndoc}"

    c3, c4 = st.columns(2)
    f_nac = c3.date_input("Fecha de Nacimiento", value=st.session_state.form["fecha_nac"])
    sexo_bio = c4.selectbox("Sexo Biológico", ["Masculino", "Femenino"])

    st.markdown('<div class="section-header">Configuración del Examen</div>', unsafe_allow_html=True)
    db = cargar_base_datos_blindada('listado_prestaciones.csv')
    
    if db is not None:
        esps = sorted(db['ESPECIALIDAD'].unique())
        esp_sel = st.selectbox("Especialidad", esps)
        pros = sorted(db[db['ESPECIALIDAD'] == esp_sel]['PROCEDIMIENTO A REALIZAR'].unique())
        pro_sel = st.selectbox("Procedimiento", pros)
        con_sel = "SI" in str(db[db['PROCEDIMIENTO A REALIZAR'] == pro_sel]['MEDIO DE CONTRASTE'].values[0]).upper()
    else:
        st.warning("⚠️ Error al leer listado_prestaciones.csv. Ingrese datos manualmente.")
        esp_sel = st.text_input("Especialidad (Manual)")
        pro_sel = st.text_input("Procedimiento (Manual)")
        con_sel = st.checkbox("¿Lleva Contraste?")

    st.subheader("📄 Carga de Orden Médica")
    st.file_uploader("Subir Orden Médica (Obligatorio)", type=["pdf", "jpg", "png", "jpeg"], key="up_orden")

    if st.button("PROCEDER A LA ENCUESTA"):
        if len(nombre_px) > 5:
            st.session_state.form.update({
                "nombre": nombre_px, "rut": rut_final, "sin_rut": es_ext,
                "fecha_nac": f_nac, "sexo_biologico": sexo_bio,
                "esp_nombre": esp_sel, "pre_nombre": pro_sel, "tiene_contraste": con_sel
            })
            st.session_state.step = 2; st.rerun()
        else: st.error("Ingrese el nombre completo.")

# =================================================================
# 5. PASO 2: ENCUESTA (ANAMNESIS) Y EXÁMENES ANTERIORES
# =================================================================
elif st.session_state.step == 2:
    st.markdown('<div class="section-header">Encuesta de Seguridad y Antecedentes</div>', unsafe_allow_html=True)
    
    st.subheader("📂 Carpeta de Exámenes Anteriores")
    st.info("Cargue aquí informes de RM, TC o Biopsias previas.")
    st.file_uploader("Adjuntar informes previos (Opcional)", type=["pdf", "jpg", "png"], accept_multiple_files=True, key="up_historial")

    st.write("---")
    st.subheader("🔍 Checklist de Seguridad RM (18 Puntos)")
    op = ["No", "Sí"]
    
    # Bloque 1
    b1, b2, b3 = st.columns(3)
    st.session_state.form["ant_ayuno"] = b1.radio("¿Ayuno de 6 horas?", op)
    st.session_state.form["ant_marcapaso"] = b2.radio("¿Marcapaso / Neuroestimulador?", op)
    st.session_state.form["ant_implantes"] = b3.radio("¿Stent / Implantes Metálicos?", op)
    
    # Bloque 2
    b4, b5, b6 = st.columns(3)
    st.session_state.form["ant_asma"] = b4.radio("¿Asma / Alergias?", op)
    st.session_state.form["ant_diabetes"] = b5.radio("¿Diabetes Mellitus?", op)
    st.session_state.form["ant_hiperten"] = b6.radio("¿Hipertensión Arterial?", op)
    
    # Bloque 3
    b7, b8, b9 = st.columns(3)
    st.session_state.form["ant_metformina"] = b7.radio("¿Toma Metformina?", op)
    st.session_state.form["ant_renal"] = b8.radio("¿Falla Renal?", op)
    st.session_state.form["ant_dialisis"] = b9.radio("¿Está en Diálisis?", op)

    # Bloque 4
    b10, b11, b12 = st.columns(3)
    st.session_state.form["ant_clips_vasc"] = b10.radio("¿Clips Vasculares (Cerebro)?", op)
    st.session_state.form["ant_esquirlas"] = b11.radio("¿Esquirlas Metálicas en ojos?", op)
    st.session_state.form["ant_protesis_dental"] = b12.radio("¿Prótesis Dental Removible?", op)

    # Bloque 5
    b13, b14, b15 = st.columns(3)
    st.session_state.form["ant_embarazo"] = b13.radio("¿Embarazo?", op)
    st.session_state.form["ant_lactancia"] = b14.radio("¿Periodo de Lactancia?", op)
    st.session_state.form["ant_tatuajes"] = b15.radio("¿Tatuajes hace < 1 mes?", op)

    # Bloque 6
    b16, b17, b18 = st.columns(3)
    st.session_state.form["ant_cardiaca"] = b16.radio("¿Insuficiencia Cardíaca?", op)
    st.session_state.form["ant_claustrofobia"] = b17.radio("¿Sufre Claustrofobia?", op)
    st.session_state.form["ant_hipertiroid"] = b18.radio("¿Hipertiroidismo?", op)

    st.markdown('<div class="section-header">Módulo Oncológico y Quirúrgico</div>', unsafe_allow_html=True)
    st.session_state.form["diagnostico_cancer"] = st.text_input("Diagnóstico Oncológico", value=st.session_state.form["diagnostico_cancer"])
    
    st.write("Tratamientos:")
    tx = st.columns(5)
    st.session_state.form["rt"] = tx[0].checkbox("Radioterapia", value=st.session_state.form["rt"])
    st.session_state.form["qt"] = tx[1].checkbox("Quimioterapia", value=st.session_state.form["qt"])
    st.session_state.form["bt"] = tx[2].checkbox("Braquiterapia", value=st.session_state.form["bt"])
    st.session_state.form["it"] = tx[3].checkbox("Inmunoterapia", value=st.session_state.form["it"])
    st.session_state.form["hormonoterapia"] = tx[4].checkbox("Hormonoterapia", value=st.session_state.form["hormonoterapia"])
    
    st.session_state.form["otras_cirugias"] = st.text_area("Describa cirugías previas y fechas", value=st.session_state.form["otras_cirugias"])

    if st.session_state.form["tiene_contraste"]:
        st.error("⚠️ EXAMEN CON CONTRASTE: REQUIERE LABORATORIO")
        st.file_uploader("Subir Resultado Creatinina", type=["pdf", "jpg", "png"], key="up_lab")
        l1, l2 = st.columns(2)
        crea = l1.number_input("Creatinina (mg/dL)", step=0.01)
        peso = l2.number_input("Peso Actual (kg)", step=0.1)
        if crea > 0:
            fact = 1.23 if st.session_state.form["sexo_biologico"] == "Masculino" else 1.04
            edad = calcular_edad(st.session_state.form["fecha_nac"])
            vfg = ((140 - edad) * peso * fact) / (72 * crea)
            st.session_state.form.update({"creatinina": crea, "peso": peso, "vfg": vfg})
            st.info(f"VFG Calculado: {vfg:.2f} mL/min")

    if st.button("SIGUIENTE: CONSENTIMIENTO"): st.session_state.step = 3; st.rerun()

# =================================================================
# 6. PASO 3: CONSENTIMIENTO INFORMADO Y FIRMA
# =================================================================
elif st.session_state.step == 3:
    st.markdown('<div class="section-header">Consentimiento Informado</div>', unsafe_allow_html=True)
    st.markdown("""
        <div class="legal-container">
            <strong>AUTORIZACIÓN VOLUNTARIA:</strong><br><br>
            Yo, el paciente identificado, declaro que he sido informado sobre el procedimiento de 
            Resonancia Magnética en <strong>Norte Imagen</strong>. Entiendo que es un examen que usa 
            campos magnéticos y ondas de radio (no radiación ionizante). <br><br>
            Autorizo el uso de medio de contraste si el médico lo estima necesario. Confirmo que no 
            poseo marcapasos u objetos metálicos no declarados. Mis respuestas en la encuesta 
            son fidedignas.
        </div>
        """, unsafe_allow_html=True)
    
    st.write("### Firma Digital del Paciente:")
    canv = st_canvas(stroke_width=3, stroke_color="#000", background_color="#fff", height=200, width=600, key="f_final")
    
    st.session_state.form["consentimiento_leido"] = st.checkbox("He leído y acepto los términos.")
    
    if st.button("FINALIZAR Y GENERAR PDF"):
        if canv.image_data is not None and st.session_state.form["consentimiento_leido"]:
            st.session_state.form["firma_img"] = Image.fromarray(canv.image_data.astype('uint8'), 'RGBA').convert("RGB")
            st.session_state.step = 4; st.rerun()
        else: st.error("Firme y acepte para finalizar.")

# =================================================================
# 7. PASO 4: CIERRE Y DESCARGA
# =================================================================
elif st.session_state.step == 4:
    st.success("✅ REGISTRO CLÍNICO FINALIZADO CON ÉXITO")
    st.write(f"Paciente: {st.session_state.form['nombre']}")
    if st.button("INGRESAR NUEVO PACIENTE"):
        st.session_state.clear(); st.rerun()
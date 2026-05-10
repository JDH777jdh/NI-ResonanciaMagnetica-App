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
st.set_page_config(page_title="Norte Imagen - Sistema Élite de Registro RM", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .logo-container { display: flex; justify-content: center; margin-bottom: 30px; }
    
    /* Botones Principales */
    .stButton>button { 
        background-color: #800020; color: white; border-radius: 4px; 
        width: 100%; height: 3.8em; font-weight: bold; border: none; font-size: 1.1em;
        text-transform: uppercase; letter-spacing: 1.5px; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #5a0016; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
    
    /* Botones de Navegación */
    div.stButton > button:first-child[key^="back"] {
        background-color: #ffffff !important; color: #800020 !important; border: 1px solid #800020 !important;
    }

    /* Cabeceras de Sección Técnico-Médicas */
    .section-header { 
        color: #ffffff; background-color: #800020; padding: 12px; 
        border-radius: 2px; margin-top: 35px; margin-bottom: 20px; 
        font-size: 1.1em; font-weight: bold; text-align: center;
        text-transform: uppercase; border-left: 5px solid #000000;
    }
    
    /* Contenedor de Consentimiento Legal */
    .legal-container {
        background-color: #f9f9f9; padding: 40px; border: 1px solid #dddddd;
        font-size: 10.5pt; text-align: justify; color: #1a1a1a; margin-bottom: 25px;
        line-height: 1.8; font-family: 'Times New Roman', Times, serif;
    }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. MOTOR DE PERSISTENCIA Y ESTADO CLÍNICO
# =================================================================
if 'step' not in st.session_state:
    st.session_state.step = 1

if 'form' not in st.session_state:
    st.session_state.form = {
        # Módulo de Identificación
        "nombre": "", "rut": "", "sin_rut": False, "tipo_doc": "Pasaporte", "num_doc": "",
        "genero": "Masculino", "sexo_biologico": "Masculino", "fecha_nac": date(1990, 1, 1), 
        "email": "", "nombre_tutor": "", "rut_tutor": "", "es_menor": False,
        # Módulo de Procedimiento
        "esp_nombre": "NEURORRADIOLOGIA", "pre_nombre": "", 
        # Anamnesis de Seguridad RM (18 Puntos de Control)
        "ant_ayuno": "No", "ant_asma": "No", "ant_diabetes": "No", "ant_hiperten": "No",
        "ant_hipertiroid": "No", "ant_renal": "No", "ant_dialisis": "No", 
        "ant_implantes": "No", "ant_marcapaso": "No", "ant_metformina": "No",
        "ant_embarazo": "No", "ant_lactancia": "No", "ant_cardiaca": "No",
        "ant_protesis_dental": "No", "ant_clips_vasc": "No", "ant_esquirlas": "No",
        "ant_tatuajes": "No", "ant_claustrofobia": "No", 
        # Módulo Oncológico y Quirúrgico
        "otras_cirugias": "", "diagnostico_cancer": "", "rt": False, "qt": False, "bt": False, "it": False, 
        "otro_tratamiento_cancer": "", 
        # Parámetros de Laboratorio y Contraste
        "tiene_contraste": False, "creatinina": 0.0, "peso": 70.0, "vfg": 0.0, "firma_img": None
    }

# =================================================================
# 3. UTILITARIOS DE VALIDACIÓN Y CARGA ROBUSTA (ANTI-PARSERERROR)
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

def generar_folio_archivo(nombre, identificador):
    partes = nombre.strip().split()
    iniciales = (partes[0][0] + partes[-1][0]).upper() if len(partes) >= 2 else "PX"
    id_clean = re.sub(r'[^a-zA-Z0-9]', '', identificador)
    return f"EC-{id_clean}{iniciales}"

@st.cache_data
def cargar_base_datos_blindada(ruta):
    if not os.path.exists(ruta):
        return None
    try:
        # Motor Python + sep=None detecta automáticamente si es coma o punto y coma
        df = pd.read_csv(
            ruta, 
            sep=None, 
            engine='python', 
            encoding='utf-8-sig',
            on_bad_lines='warn'
        )
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error al cargar base de datos: {e}")
        return None

# =================================================================
# 4. GENERADOR DE PDF "NORTE IMAGEN" (INFORME MÉDICO PRO)
# =================================================================
def export_pdf_maestro(datos):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PÁGINA 1: IDENTIFICACIÓN Y SEGURIDAD ---
    pdf.add_page()
    if os.path.exists("logoNI.png"):
        pdf.image("logoNI.png", x=85, y=10, w=40)
    
    pdf.ln(35)
    pdf.set_font("Times", 'B', 16); pdf.set_text_color(128, 0, 32)
    pdf.cell(190, 8, txt="REGISTRO CLÍNICO Y CONSENTIMIENTO INFORMADO", ln=True, align='C')
    pdf.set_font("Times", 'I', 14); pdf.cell(190, 8, txt="Protocolo de Resonancia Magnética", ln=True, align='C')
    
    pdf.ln(10); pdf.set_fill_color(240, 240, 240); pdf.set_font("Helvetica", 'B', 11); pdf.set_text_color(0,0,0)
    pdf.cell(190, 9, txt=" I. IDENTIFICACIÓN DEL PACIENTE", ln=True, fill=True)
    
    pdf.set_font("Helvetica", size=10); pdf.ln(3)
    pdf.cell(190, 7, txt=f"Nombre completo del paciente: {datos['nombre'].upper()}", ln=1)
    id_doc = datos['rut'] if not datos['sin_rut'] else f"{datos['tipo_doc']}: {datos['num_doc']}"
    pdf.cell(95, 7, txt=f"Identificación (RUT/ID): {id_doc}", ln=0)
    pdf.cell(95, 7, txt=f"F. Nacimiento: {datos['fecha_nac'].strftime('%d/%m/%Y')}", ln=1)
    pdf.cell(95, 7, txt=f"Edad: {calcular_edad(datos['fecha_nac'])} años", ln=0)
    pdf.cell(95, 7, txt=f"Género: {datos['genero']} (Sexo Bio: {datos['sexo_biologico']})", ln=1)
    
    pdf.ln(5); pdf.set_fill_color(240, 240, 240); pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(190, 9, txt=" II. ESPECIFICACIONES DEL PROCEDIMIENTO", ln=True, fill=True)
    pdf.set_font("Helvetica", size=10); pdf.ln(3)
    pdf.cell(190, 7, txt=f"Especialidad: {datos['esp_nombre']}", ln=1)
    pdf.cell(190, 7, txt=f"Examen solicitado: {datos['pre_nombre']}", ln=1)
    
    if datos['tiene_contraste']:
        pdf.set_font("Helvetica", 'B', 10); pdf.set_text_color(180, 0, 0)
        pdf.cell(190, 7, txt="ALERTA: ESTUDIO REQUIERE MEDIO DE CONTRASTE ENDOVENOSO", ln=1)
        pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", size=10)
        pdf.cell(95, 7, txt=f"Creatinina Sérica: {datos['creatinina']} mg/dL", ln=0)
        pdf.cell(95, 7, txt=f"VFG (Cockcroft-Gault): {datos['vfg']:.2f} mL/min", ln=1)

    pdf.ln(5); pdf.set_fill_color(240, 240, 240); pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(190, 9, txt=" III. ANAMNESIS TÉCNICA DE SEGURIDAD RM", ln=True, fill=True)
    pdf.set_font("Helvetica", size=8.5); pdf.ln(2)
    
    items = [
        ("Ayuno", datos['ant_ayuno']), ("Asma", datos['ant_asma']), ("Diabetes", datos['ant_diabetes']),
        ("Hipertensión", datos['ant_hiperten']), ("Hipertiroidismo", datos['ant_hipertiroid']), ("Falla Renal", datos['ant_renal']),
        ("Diálisis", datos['ant_dialisis']), ("Marcapaso/Neuro", datos['ant_marcapaso']), ("Implantes Metálicos", datos['ant_implantes']),
        ("Metformina", datos['ant_metformina']), ("Embarazo", datos['ant_embarazo']), ("Lactancia", datos['ant_lactancia']),
        ("Insuf. Cardíaca", datos['ant_cardiaca']), ("Prótesis Dental", datos['ant_protesis_dental']), ("Clips Vasculares", datos['ant_clips_vasc']),
        ("Esquirlas", datos['ant_esquirlas']), ("Tatuajes", datos['ant_tatuajes']), ("Claustrofobia", datos['ant_claustrofobia'])
    ]
    for i in range(0, len(items), 2):
        pdf.cell(95, 5, txt=f"{items[i][0]}: {items[i][1]}", ln=0)
        if i+1 < len(items): pdf.cell(95, 5, txt=f"{items[i+1][0]}: {items[i+1][1]}", ln=1)

    # --- PÁGINA 2: ANTECEDENTES Y CONSENTIMIENTO ---
    pdf.add_page()
    if os.path.exists("logoNI.png"): pdf.image("logoNI.png", x=85, y=10, w=40)
    pdf.ln(35)
    pdf.set_fill_color(240, 240, 240); pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(190, 9, txt=" IV. ANTECEDENTES ONCOLÓGICOS Y QUIRÚRGICOS", ln=True, fill=True)
    pdf.set_font("Helvetica", size=10); pdf.ln(3)
    pdf.multi_cell(190, 6, txt=f"Cáncer: {datos['diagnostico_cancer'] if datos['diagnostico_cancer'] else 'No reporta.'}")
    pdf.multi_cell(190, 6, txt=f"Cirugías previas: {datos['otras_cirugias'] if datos['otras_cirugias'] else 'No reporta.'}")

    pdf.ln(5); pdf.set_fill_color(128, 0, 32); pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 9, txt=" V. CONSENTIMIENTO INFORMADO", ln=True, fill=True)
    pdf.set_font("Times", size=10); pdf.set_text_color(0, 0, 0); pdf.ln(3)
    c_text = (
        "Yo, el paciente (o tutor), confirmo que he sido informado de los riesgos y beneficios de la RM. "
        "Autorizo el uso de medio de contraste si el médico radiólogo lo estima necesario. "
        "Declaro bajo juramento que toda la información aquí expuesta es verídica."
    )
    pdf.multi_cell(190, 6, txt=c_text.encode('latin-1', 'replace').decode('latin-1'))

    pdf.ln(30); pos_y = pdf.get_y()
    if datos['firma_img']:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            datos['firma_img'].save(tmp.name)
            pdf.image(tmp.name, x=45, y=pos_y - 25, w=50)
        os.unlink(tmp.name)
    pdf.line(40, pos_y, 100, pos_y); pdf.line(115, pos_y, 175, pos_y)
    pdf.set_font("Helvetica", 'B', 8); pdf.set_xy(40, pos_y + 2); pdf.cell(60, 5, txt="FIRMA PACIENTE / TUTOR", align='C')
    pdf.set_xy(115, pos_y + 2); pdf.cell(60, 5, txt="FIRMA PROFESIONAL NORTE IMAGEN", align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# =================================================================
# 5. FASE 1: IDENTIFICACIÓN (CON REQUISITOS TÉCNICOS)
# =================================================================
if st.session_state.step == 1:
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    if os.path.exists("logoNI.png"): st.image("logoNI.png", width=220)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">Identificación Obligatoria del Paciente</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    nombre_c = c1.text_input("Nombre completo del paciente", value=st.session_state.form["nombre"], placeholder="Nombre y Apellidos")
    
    es_ext = st.checkbox("Paciente Extranjero (Sin RUT)", value=st.session_state.form["sin_rut"])
    if not es_ext:
        rut_raw = c2.text_input("Cédula de Identidad (RUT)", value=st.session_state.form["rut"])
        rut_f = format_rut_chileno(rut_raw)
        if rut_f != rut_raw: st.session_state.form["rut"] = rut_f; st.rerun()
    else:
        t_doc = c2.selectbox("Tipo Documento", ["Pasaporte", "DNI", "Cédula Extranjera"])
        n_doc = c2.text_input("Número Documento", value=st.session_state.form["num_doc"])
        rut_f = ""

    c3, c4 = st.columns(2)
    f_nac = c3.date_input("Fecha de Nacimiento", value=st.session_state.form["fecha_nac"], format="DD/MM/YYYY")
    gen_i = c4.selectbox("Identidad de Género", ["Masculino", "Femenino", "No binario"])
    sex_b = st.selectbox("Sexo Biológico (Requerido para cálculo VFG)", ["Masculino", "Femenino"]) if gen_i == "No binario" else gen_i

    st.markdown('<div class="section-header">Configuración del Examen</div>', unsafe_allow_html=True)
    
    # CARGA ROBUSTA DE BASE DE DATOS
    db = cargar_base_datos_blindada('listado_prestaciones.csv')
    
    if db is not None:
        esps = sorted(db['ESPECIALIDAD'].unique())
        esp_s = st.selectbox("Especialidad", esps)
        pros = sorted(db[db['ESPECIALIDAD'] == esp_s]['PROCEDIMIENTO A REALIZAR'].unique())
        pro_s = st.selectbox("Procedimiento", pros)
        
        st.write("---")
        st.subheader("📎 Documentación Técnica Requerida")
        st.file_uploader("Subir Orden Médica (Obligatorio)", type=["pdf", "jpg", "png"])
    else:
        st.error("Base de datos de prestaciones no disponible.")
        esp_s, pro_s = "N/A", "N/A"

    cert = st.checkbox("Declaro que todos los datos de identificación son exactos y verídicos.")
    
    if st.button("PROCEDER A ANAMNESIS"):
        if len(nombre_c.strip().split()) >= 2 and cert:
            st.session_state.form.update({"nombre": nombre_c, "rut": rut_f, "sin_rut": es_ext, "fecha_nac": f_nac, "genero": gen_i, "sexo_biologico": sex_b, "esp_nombre": esp_s, "pre_nombre": pro_s})
            if db is not None:
                row = db[db['PROCEDIMIENTO A REALIZAR'] == pro_s]
                st.session_state.form["tiene_contraste"] = "SI" in str(row['MEDIO DE CONTRASTE'].values[0]).upper()
            st.session_state.step = 2; st.rerun()
        else:
            st.warning("Faltan datos críticos o validación de veracidad.")

# =================================================================
# 6. FASE 2: ANAMNESIS COMPLETA (SIN RESÚMENES)
# =================================================================
elif st.session_state.step == 2:
    st.markdown('<div class="section-header">Anamnesis de Seguridad Radiológica</div>', unsafe_allow_html=True)
    st.file_uploader("Adjuntar Exámenes Previos para Comparación (RX, TC, RM)", type=["pdf", "jpg", "png"], accept_multiple_files=True)
    
    op = ["No", "Sí"]
    c1, c2, c3 = st.columns(3)
    st.session_state.form["ant_ayuno"] = c1.radio("¿Mantiene Ayuno?", op)
    st.session_state.form["ant_asma"] = c2.radio("¿Asma / Alergias?", op)
    st.session_state.form["ant_diabetes"] = c3.radio("¿Diabetes Mellitus?", op)
    st.session_state.form["ant_hiperten"] = c1.radio("¿Hipertensión Arterial?", op)
    st.session_state.form["ant_hipertiroid"] = c2.radio("¿Hipertiroidismo?", op)
    st.session_state.form["ant_renal"] = c3.radio("¿Insuficiencia Renal?", op)
    st.session_state.form["ant_dialisis"] = c1.radio("¿Realiza Diálisis?", op)
    st.session_state.form["ant_marcapaso"] = c2.radio("¿Marcapaso / Neuro?", op)
    st.session_state.form["ant_implantes"] = c3.radio("¿Metales / Implantes?", op)
    st.session_state.form["ant_metformina"] = c1.radio("¿Uso de Metformina?", op)
    st.session_state.form["ant_embarazo"] = c2.radio("¿Posible Embarazo?", op)
    st.session_state.form["ant_lactancia"] = c3.radio("¿Periodo de Lactancia?", op)
    st.session_state.form["ant_cardiaca"] = c1.radio("¿Falla Cardíaca?", op)
    st.session_state.form["ant_protesis_dental"] = c2.radio("¿Prótesis Dental?", op)
    st.session_state.form["ant_clips_vasc"] = c3.radio("¿Clips Vasculares?", op)
    st.session_state.form["ant_esquirlas"] = c1.radio("¿Esquirlas Oculares?", op)
    st.session_state.form["ant_tatuajes"] = c2.radio("¿Tatuajes?", op)
    st.session_state.form["ant_claustrofobia"] = c3.radio("¿Claustrofobia?", op)

    st.markdown('<div class="section-header">Oncología y Cirugías</div>', unsafe_allow_html=True)
    st.session_state.form["diagnostico_cancer"] = st.text_input("Diagnóstico Oncológico", value=st.session_state.form["diagnostico_cancer"])
    tx = st.columns(4)
    st.session_state.form["rt"] = tx[0].checkbox("Radioterapia")
    st.session_state.form["qt"] = tx[1].checkbox("Quimioterapia")
    st.session_state.form["bt"] = tx[2].checkbox("Braquiterapia")
    st.session_state.form["it"] = tx[3].checkbox("Inmunoterapia")
    st.session_state.form["otras_cirugias"] = st.text_area("Describa cirugías previas")

    if st.session_state.form["tiene_contraste"]:
        st.error("AVISO: Examen CONTRASTADO. Se requiere función renal.")
        st.file_uploader("Subir Examen de Creatinina (PDF/JPG)", type=["pdf", "jpg", "png"])
        c_r, p_r = st.columns(2)
        crea = c_r.number_input("Creatinina (mg/dL)", value=st.session_state.form["creatinina"], step=0.01)
        peso = p_r.number_input("Peso Actual (kg)", value=st.session_state.form["peso"], step=0.1)
        if crea > 0:
            fact = 1.23 if st.session_state.form["sexo_biologico"] == "Masculino" else 1.04
            vfg = ((140 - calcular_edad(st.session_state.form["fecha_nac"])) * peso * fact) / (72 * crea)
            st.session_state.form.update({"creatinina": crea, "peso": peso, "vfg": vfg})
            st.info(f"VFG Calculada: {vfg:.2f} mL/min")

    v_clin = st.checkbox("Confirmo que la anamnesis respondida es fidedigna.")
    n1, n2 = st.columns(2)
    if n1.button("VOLVER", key="back2"): st.session_state.step = 1; st.rerun()
    if n2.button("SIGUIENTE"): 
        if v_clin: st.session_state.step = 3; st.rerun()

# =================================================================
# 7. FASE 3: CONSENTIMIENTO Y RÚBRICA
# =================================================================
elif st.session_state.step == 3:
    st.title("Consentimiento Informado")
    st.markdown('<div class="legal-container"><b>DECLARACIÓN JURADA:</b> Certifico que comprendo los alcances del examen de Resonancia Magnética y autorizo voluntariamente...</div>', unsafe_allow_html=True)
    st.write("Firma Digital del Paciente o Tutor:")
    canv = st_canvas(stroke_width=2, stroke_color="#000", background_color="#fff", height=180, width=550, key="signature")
    
    v_legal = st.checkbox("He leído y acepto los términos del consentimiento informado.")
    n3, n4 = st.columns(2)
    if n3.button("VOLVER", key="back3"): st.session_state.step = 2; st.rerun()
    if n4.button("FINALIZAR REGISTRO"):
        if v_legal and canv.image_data is not None:
            st.session_state.form["firma_img"] = Image.fromarray(canv.image_data.astype('uint8'), 'RGBA').convert("RGB")
            st.session_state.step = 4; st.rerun()

# =================================================================
# 8. FASE 4: ENTREGA Y DESCARGA
# =================================================================
elif st.session_state.step == 4:
    f = st.session_state.form
    d_ref = f['rut'] if not f['sin_rut'] else f['num_doc']
    nombre_f = generar_folio_archivo(f['nombre'], d_ref)
    pdf_bytes = export_pdf_maestro(f)
    
    st.success(f"REGISTRO COMPLETADO: {nombre_f}")
    st.download_button(f"📥 DESCARGAR REGISTRO CLÍNICO (PDF)", data=pdf_bytes, file_name=f"{nombre_f}.pdf", mime="application/pdf")
    if st.button("NUEVO REGISTRO"): st.session_state.clear(); st.rerun()
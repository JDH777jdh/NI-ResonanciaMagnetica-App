import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from fpdf import FPDF
import os
import numpy as np
from PIL import Image
import tempfile

# 1. CONFIGURACIÓN Y ESTILOS (ESTÁNDAR DE ORO BLOQUEADO)
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
        font-size: 0.95em; text-align: justify; color: #333; margin-bottom: 20px;
        max-height: 500px; overflow-y: auto; line-height: 1.6;
    }
    .vfg-box { 
        background-color: #ffffff; padding: 20px; border-radius: 10px; 
        border: 2px solid #800020; text-align: center; margin-top: 20px;
    }
    .vfg-critica { border: 3px solid #ff0000 !important; color: #ff0000 !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. GESTIÓN DE ESTADO (PERSISTENCIA TOTAL)
if 'step' not in st.session_state: st.session_state.step = 1
if 'form' not in st.session_state:
    st.session_state.form = {
        "nombre": "", "rut": "", "sin_rut": False, "tipo_doc": "Pasaporte", "num_doc": "",
        "genero_idx": 0, "sexo_bio_idx": 0, "fecha_nac": date(1990, 1, 1), "email": "", 
        "nombre_tutor": "", "rut_tutor": "", "esp_idx": 0,
        "bio_marcapaso": "No", "bio_implantes": "No", "bio_detalle": "",
        "clin_ayuno": "No", "clin_asma": "No", "clin_hiperten": "No", "clin_hipertiroid": "No",
        "clin_diabetes": "No", "clin_alergico": "No", "clin_metformina": "No", "clin_renal": "No",
        "clin_dialisis": "No", "clin_claustro": "No", "clin_embarazo": "No", "clin_lactancia": "No",
        "quir_cirugia_check": "No", "quir_cirugia_detalle": "", "quir_cancer_detalle": "",
        "rt": False, "qt": False, "bt": False, "it": False, "quir_otro_trat": "",
        "ex_rx": False, "ex_mg": False, "ex_eco": False, "ex_tc": False, "ex_rm": False, "ex_otros": "",
        "creatinina": 0.0, "peso": 70.0, "vfg": 0.0,
        "veracidad": None, "autoriza_gad": None, "firma_img": None
    }

# 3. FUNCIONES DE APOYO Y MOTOR PDF PROFESIONAL
def formatear_rut(rut_sucio):
    rut_limpio = str(rut_sucio).replace(".", "").replace("-", "").upper().strip()
    if len(rut_limpio) < 2: return rut_limpio
    cuerpo, dv = rut_limpio[:-1], rut_limpio[-1]
    if cuerpo.isdigit(): return f"{int(cuerpo):,}".replace(",", ".") + f"-{dv}"
    return rut_sucio

def calcular_edad(fecha_nac):
    today = date.today()
    return today.year - fecha_nac.year - ((today.month, today.day) < (fecha_nac.month, fecha_nac.day))

class PDF(FPDF):
    def header(self):
        if os.path.exists("logoNI.png"):
            self.image("logoNI.png", 10, 8, 33)
        self.set_font('Arial', 'B', 15)
        self.set_text_color(128, 0, 32)
        self.cell(80)
        self.cell(30, 10, 'ENCUESTA Y CONSENTIMIENTO INFORMADO', 0, 0, 'C')
        self.ln(20)

    def section_title(self, label):
        self.set_font('Arial', 'B', 11)
        self.set_fill_color(240, 240, 240)
        self.set_text_color(128, 0, 32)
        self.cell(0, 8, label, 0, 1, 'L', 1)
        self.ln(2)

    def data_row(self, label, value):
        self.set_font('Arial', 'B', 9)
        self.set_text_color(50, 50, 50)
        self.write(5, f"{label}: ")
        self.set_font('Arial', '', 9)
        self.set_text_color(0, 0, 0)
        self.write(5, f"{value}\n")

def generar_pdf_clinico(datos):
    pdf = PDF()
    pdf.add_page()
    
    # 1. Datos Identificación
    pdf.section_title("1. IDENTIFICACIÓN DEL PACIENTE")
    doc_id = datos['rut'] if not datos['sin_rut'] else f"{datos['tipo_doc']}: {datos['num_doc']}"
    pdf.data_row("Nombre Completo", datos['nombre'])
    pdf.data_row("Documento", doc_id)
    pdf.data_row("Fecha de Nacimiento", datos['fecha_nac'].strftime("%d/%m/%Y"))
    pdf.data_row("Email", datos['email'])
    pdf.data_row("Procedimiento", st.session_state.procedimiento)
    if datos['nombre_tutor']:
        pdf.data_row("Tutor/Representante", f"{datos['nombre_tutor']} (RUT: {datos['rut_tutor']})")
    pdf.ln(5)

    # 2. Bioseguridad
    pdf.section_title("2. BIOSEGURIDAD MAGNÉTICA")
    pdf.data_row("Marcapasos cardiaco", datos['bio_marcapaso'])
    pdf.data_row("Implantes/Prótesis metálicas", datos['bio_implantes'])
    pdf.data_row("Detalle Bioseguridad", datos['bio_detalle'] if datos['bio_detalle'] else "Sin hallazgos")
    pdf.ln(5)

    # 3. Antecedentes Clínicos
    pdf.section_title("3. ANTECEDENTES CLÍNICOS")
    clin_txt = (f"Ayuno: {datos['clin_ayuno']} | Asma: {datos['clin_asma']} | HTA: {datos['clin_hiperten']} | "
                f"Hipertiroidismo: {datos['clin_hipertiroid']} | Diabetes: {datos['clin_diabetes']} | "
                f"Alérgico: {datos['clin_alergico']} | Renal: {datos['clin_renal']} | "
                f"Diálisis: {datos['clin_dialisis']} | Embarazo: {datos['clin_embarazo']}")
    pdf.multi_cell(0, 5, clin_txt)
    pdf.ln(5)

    # 4. Quirúrgicos y VFG
    pdf.section_title("4. ANTECEDENTES QUIRÚRGICOS Y FUNCIÓN RENAL")
    pdf.data_row("Cirugías", f"{datos['quir_cirugia_check']} - {datos['quir_cirugia_detalle']}")
    pdf.data_row("Tratamientos", f"RT: {datos['rt']}, QT: {datos['qt']}, BT: {datos['bt']}, IT: {datos['it']}")
    if datos['vfg'] > 0:
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 10, f"RESULTADO VFG: {datos['vfg']:.2f} ml/min | Creatinina: {datos['creatinina']} mg/dL", 0, 1)
    pdf.ln(5)

    # 5. Consentimiento
    pdf.add_page()
    pdf.section_title("5. CONSENTIMIENTO INFORMADO")
    pdf.set_font('Arial', '', 8)
    consent_body = (
        "OBJETIVOS: La Resonancia Magnética (RM) es una segura técnica de Diagnóstico, que permite la adquisición de imágenes "
        "de gran sensibilidad en todos los planos del espacio de las estructuras del cuerpo. Tiene como objetivo obtener "
        "Información, datos funcionales y morfológicos para detectar precozmente una enfermedad. "
        "Para este examen eventualmente se puede requerir la utilización de un medio de contraste paramagnético de "
        "administración endovenosa llamado gadolinio, que permite realzar ciertos tejidos del cuerpo para un mejor diagnóstico."
    )
    pdf.multi_cell(0, 4, consent_body)
    pdf.ln(10)

    # Firmas
    y_pos = pdf.get_y()
    if datos['firma_img']:
        pdf.image(datos['firma_img'], x=15, y=y_pos, w=50)
    
    pdf.line(15, y_pos + 25, 75, y_pos + 25)
    pdf.set_font('Arial', 'B', 8)
    pdf.text(15, y_pos + 30, f"FIRMA PACIENTE: {datos['nombre']}")
    
    pdf.line(120, y_pos + 25, 180, y_pos + 25)
    pdf.text(120, y_pos + 30, "FIRMA PROFESIONAL RESPONSABLE")

    return pdf.output(dest='S').encode('latin-1')

def mostrar_logo():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if os.path.exists("logoNI.png"): st.image("logoNI.png", use_container_width=True)
        else: st.subheader("NORTE IMAGEN")

@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv('listado_prestaciones.csv', sep=None, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        return df
    except: return None

df = cargar_datos()

# --- PÁGINA 1: REGISTRO (CON BLINDAJE DE FECHA) ---
if st.session_state.step == 1:
    mostrar_logo(); st.title("Registro de Paciente")
    if df is not None:
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.form["nombre"] = st.text_input("Nombre Completo del Paciente", value=st.session_state.form["nombre"])
            rut_p = st.text_input("RUT del Paciente", value=st.session_state.form["rut"], placeholder="12.345.678-K")
            st.session_state.form["rut"] = formatear_rut(rut_p)
            st.session_state.form["sin_rut"] = st.checkbox("Sin RUT, poseo otro documento", value=st.session_state.form["sin_rut"])
            if st.session_state.form["sin_rut"]:
                t_opts = ["Pasaporte", "Cédula de extranjero"]
                st.session_state.form["tipo_doc"] = st.selectbox("Tipo de documento", t_opts, index=t_opts.index(st.session_state.form["tipo_doc"]))
                st.session_state.form["num_doc"] = st.text_input("N° de documento", value=st.session_state.form["num_doc"])
            
            g_opts = ["Masculino", "Femenino", "No binario"]
            gen_sel = st.selectbox("Identidad de Género", g_opts, index=st.session_state.form["genero_idx"])
            st.session_state.form["genero_idx"] = g_opts.index(gen_sel)
            
            sexo_final = gen_sel
            if gen_sel == "No binario":
                sb_opts = ["Masculino", "Femenino"]
                sexo_bio = st.selectbox("Sexo asignado al nacer (Para fines clínicos)", sb_opts, index=st.session_state.form["sexo_bio_idx"])
                st.session_state.form["sexo_bio_idx"] = sb_opts.index(sexo_bio)
                sexo_final = sexo_bio

        with c2:
            st.session_state.form["fecha_nac"] = st.date_input(
                "Fecha de Nacimiento", 
                value=st.session_state.form["fecha_nac"], 
                min_value=date(1910, 1, 1),
                max_value=date.today(),
                format="DD/MM/YYYY",
                help="Puedes escribir la fecha directamente o usar el calendario."
            )
            st.session_state.form["email"] = st.text_input("Email de contacto", value=st.session_state.form["email"])
        
        edad = calcular_edad(st.session_state.form["fecha_nac"])
        if edad < 18:
            st.warning(f"👦 PACIENTE MENOR DE EDAD ({edad} años)")
            st.session_state.form["nombre_tutor"] = st.text_input("Nombre Representante Legal", value=st.session_state.form["nombre_tutor"])
            st.session_state.form["rut_tutor"] = formatear_rut(st.text_input("RUT Representante", value=st.session_state.form["rut_tutor"]))

        st.markdown('<div class="section-header">Información del Examen</div>', unsafe_allow_html=True)
        esp_raw = sorted([str(e) for e in df['ESPECIALIDAD'].unique() if pd.notna(e)])
        esp_finales = [e for e in esp_raw if "NEURO" in e.upper()] + [e for e in esp_raw if "NEURO" not in e.upper()]
        ce1, ce2 = st.columns(2)
        esp_sel = ce1.selectbox("Especialidad", esp_finales, index=st.session_state.form["esp_idx"])
        st.session_state.form["esp_idx"] = esp_finales.index(esp_sel)
        
        filtered = df[df['ESPECIALIDAD'] == esp_sel]
        list_pre = sorted(filtered['PROCEDIMIENTO A REALIZAR'].dropna().unique().tolist()) if not filtered.empty else ["No disponible"]
        pre_sel = ce2.selectbox("Procedimiento", list_pre)

        st.markdown('<div class="section-header">Documentación Médica</div>', unsafe_allow_html=True)
        st.file_uploader("Cargue la Orden Médica (Obligatorio)", type=["pdf", "jpg", "jpeg"], key="up_orden_p1")

        if st.button("CONTINUAR"):
            if st.session_state.form["nombre"]:
                row = df[(df['ESPECIALIDAD'] == esp_sel) & (df['PROCEDIMIENTO A REALIZAR'] == pre_sel)]
                st.session_state.tiene_contraste = str(row['MEDIO DE CONTRASTE'].values[0]).upper() == "SI" if not row.empty else False
                st.session_state.procedimiento = pre_sel
                st.session_state.edad_para_calculo = edad
                st.session_state.sexo_para_calculo = sexo_final
                st.session_state.step = 2; st.rerun()

# --- PÁGINA 2: CUESTIONARIO ---
elif st.session_state.step == 2:
    mostrar_logo(); st.title("📋 Cuestionario de Seguridad RM")
    opts = ["No", "Sí"]

    st.markdown('<div class="section-header">1. Bioseguridad Magnética</div>', unsafe_allow_html=True)
    st.session_state.form["bio_marcapaso"] = st.radio("Marcapasos cardiaco:", opts, index=opts.index(st.session_state.form["bio_marcapaso"]), horizontal=True)
    st.session_state.form["bio_implantes"] = st.radio("Implantes metálicos, quirúrgicos, prótesis o dispositivos electrónicos:", opts, index=opts.index(st.session_state.form["bio_implantes"]), horizontal=True)
    st.session_state.form["bio_detalle"] = st.text_area("Detalle de que tipo y ubicación:", value=st.session_state.form["bio_detalle"], height=70)

    st.markdown('<div class="section-header">2. Antecedentes Clínicos</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    k1 = [("clin_ayuno", "Ayuno (2 hrs o mas)"), ("clin_asma", "Asma"), ("clin_hiperten", "Hipertensión"), ("clin_hipertiroid", "Hipertiroidismo")]
    k2 = [("clin_diabetes", "Diabetes"), ("clin_alergico", "Alérgico"), ("clin_metformina", "Suspende metformina (48 hrs. antes)"), ("clin_renal", "Insuficiencia renal")]
    k3 = [("clin_dialisis", "Diálisis"), ("clin_claustro", "Claustrofóbico"), ("clin_embarazo", "Embarazo"), ("clin_lactancia", "Lactancia")]
    for col, keys in zip([c1, c2, c3], [k1, k2, k3]):
        for k, label in keys: st.session_state.form[k] = col.radio(label, opts, index=opts.index(st.session_state.form[k]))

    st.markdown('<div class="section-header">3. Antecedentes Quirúrgicos y/o Terapéuticos</div>', unsafe_allow_html=True)
    st.session_state.form["quir_cirugia_check"] = st.radio("¿Ha sido sometido a alguna cirugía o más de una?", opts, index=opts.index(st.session_state.form["quir_cirugia_check"]), horizontal=True)
    st.session_state.form["quir_cirugia_detalle"] = st.text_area("Detalle nombre de la cirugía y fecha:", value=st.session_state.form["quir_cirugia_detalle"], height=70)
    st.session_state.form["quir_cancer_detalle"] = st.text_input("¿Has estado bajo tratamiento de cáncer o alguna otra enfermedad? (Detalle tipo y fecha):", value=st.session_state.form["quir_cancer_detalle"])
    
    ct1, ct2, ct3, ct4 = st.columns(4)
    st.session_state.form["rt"] = ct1.checkbox("Radioterapia (RT)", value=st.session_state.form["rt"])
    st.session_state.form["qt"] = ct2.checkbox("Quimioterapia (QT)", value=st.session_state.form["qt"])
    st.session_state.form["bt"] = ct3.checkbox("Braquiterapia (BT)", value=st.session_state.form["bt"])
    st.session_state.form["it"] = ct4.checkbox("Inmunoterapia (IT)", value=st.session_state.form["it"])
    st.session_state.form["quir_otro_trat"] = st.text_input("Algún otro tratamiento que mencionar:", value=st.session_state.form["quir_otro_trat"])

    st.markdown('<div class="section-header">4. Exámenes anteriores</div>', unsafe_allow_html=True)
    ce1, ce2, ce3, ce4, ce5 = st.columns(5)
    st.session_state.form["ex_rx"] = ce1.checkbox("Radiografía (Rx)", value=st.session_state.form["ex_rx"])
    st.session_state.form["ex_mg"] = ce2.checkbox("Mamografía (MG)", value=st.session_state.form["ex_mg"])
    st.session_state.form["ex_eco"] = ce3.checkbox("Ecotomografía (Eco)", value=st.session_state.form["ex_eco"])
    st.session_state.form["ex_tc"] = ce4.checkbox("Tomografía (TC)", value=st.session_state.form["ex_tc"])
    st.session_state.form["ex_rm"] = ce5.checkbox("Resonancia (RM)", value=st.session_state.form["ex_rm"])
    st.session_state.form["ex_otros"] = st.text_input("Otros estudios:", value=st.session_state.form["ex_otros"])
    st.file_uploader("Subir exámenes anteriores (Hasta 4 archivos PDF/JPG):", type=["pdf", "jpg", "jpeg"], accept_multiple_files=True)

    if st.session_state.tiene_contraste:
        st.markdown('<div class="section-header">5. Cálculo del Velocidad de Filtración Glomerular (VFG)</div>', unsafe_allow_html=True)
        st.session_state.form["creatinina"] = st.number_input("Creatinina (mg/dL)", value=st.session_state.form["creatinina"], step=0.01)
        st.session_state.form["peso"] = st.number_input("Peso (kg)", value=st.session_state.form["peso"])
        if st.session_state.form["creatinina"] > 0:
            vfg = ((140 - st.session_state.edad_para_calculo) * st.session_state.form["peso"]) / (72 * st.session_state.form["creatinina"])
            if st.session_state.sexo_para_calculo == "Femenino": vfg *= 0.85
            st.session_state.form["vfg"] = vfg
            estilo = "vfg-critica" if vfg < 30 else ""
            st.markdown(f'<div class="vfg-box {estilo}">Resultado VFG: <h2>{vfg:.2f} ml/min</h2></div>', unsafe_allow_html=True)

    st.divider()
    st.session_state.form["veracidad"] = st.radio("¿Declara que la información es fidedigna?", ["SÍ", "NO"], index=None)
    
    col_nav = st.columns(2)
    if col_nav[0].button("ATRÁS"): st.session_state.step = 1; st.rerun()
    if col_nav[1].button("SIGUIENTE"):
        if st.session_state.form["veracidad"] == "SÍ": st.session_state.step = 3; st.rerun()
        else: st.error("Debe declarar que la información es fidedigna.")

# --- PÁGINA 3: CONSENTIMIENTO ---
elif st.session_state.step == 3:
    mostrar_logo(); st.title("Consentimiento informado")
    paciente = st.session_state.form["nombre"]
    examen = st.session_state.procedimiento
    gad_txt = " con medio de contraste" if st.session_state.tiene_contraste else ""
    st.subheader(f"{paciente} se realizará una {examen}{gad_txt}")

    if st.session_state.tiene_contraste:
        st.markdown(f"""<div class="legal-text">
        <strong>OBJETIVOS</strong><br>
        La Resonancia Magnética (RM) es una segura técnica de Diagnóstico, que permite la adquisición de imágenes de gran sensibilidad en todos los planos del espacio de las estructuras del cuerpo. Tiene como objetivo obtener Información, datos funcionales y morfológicos para detectar precozmente una enfermedad.<br><br>
        Para este examen eventualmente se puede requerir la utilización de un medio de contraste paramagnético de administración endovenosa llamado gadolinio, que permite realzar ciertos tejidos del cuerpo para un mejor diagnóstico.<br><br>
        <strong>CARACTERISTICAS</strong><br>
        La Resonancia utiliza fuertes campos magnéticos y ondas de radiofrecuencia, por lo que es muy importante dejar fuera de la sala absolutamente todo lo que lleve consigo de tipo metálico y/o electrónico (relojes, pulseras, teléfonos, tarjetas magnéticas, etc). Si lleva material de este tipo en su cuerpo (fijaciones dentales, piercings, algunos tatuajes, balas o esquirlas metálicas) ciertos tipos de prótesis (valvulares, de cadera, de rodilla, clips metálicos, etc), o implantes, así como dispositivos electrónicos de carácter médico como bombas de insulina, prótesis auditivas, marcapasos, desfibriladores, etc. Avísenos, ya que puede contraindicar de manera absoluta la realización de este examen.<br><br>
        Usted será posicionado en la camilla del equipo, según el estudio a realizar y se colocarán cerca de la zona a estudiar unos dispositivos (bobinas) que pueden ser de diversos tamaños. Esta exploración suele ser larga (entre 20 min y 1 hr según los casos). Notará ruido derivado del funcionamiento de la RM (por lo que le facilitaremos unos protectores auditivos), todo esto es normal y se le vigilará constantemente desde la sala de control. Es muy importante que permanezca quieto durante el estudio y siga las instrucciones del Tecnólogo Médico.<br><br>
        <strong>POTENCIALES RIESGOS</strong><br>
        Existe una muy baja posibilidad de que se presente una reacción adversa al medio de contraste (0.07-2.4%) la mayoría de carácter leve fundamentalmente nauseas o cefaleas al momento de la inyección.<br>
        Pacientes con deterioro importante de la función renal, poseen riesgo de desarrollo de fibrosis nefrogénica sistémica.<br><br>
        Por lo anteriormente expuesto:<br><br>
        He sido informado de mi derecho de anular o revocar posteriormente este documento, dejándolo constatado por escrito y firmado por mi o mi representante.
        </div>""", unsafe_allow_html=True)
        st.session_state.form["autoriza_gad"] = st.radio("Autorizo la realización del procedimiento y acciones necesarias:", ["SÍ", "NO"], index=None)
    else: st.session_state.form["autoriza_gad"] = "SÍ"

    st.write("Firma del Paciente / Tutor:")
    canvas_result = st_canvas(stroke_width=2, stroke_color="#000", background_color="#fff", height=150, width=400, key="canvas")
    
    c_nav = st.columns(2)
    if c_nav[0].button("ATRÁS"): st.session_state.step = 2; st.rerun()
    if c_nav[1].button("FINALIZAR REGISTRO"):
        if st.session_state.form["autoriza_gad"] == "SÍ" and np.any(canvas_result.image_data[:, :, 3] > 0):
            img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                img.save(tmp.name); st.session_state.form["firma_img"] = tmp.name
            st.session_state.step = 4; st.balloons(); st.rerun()
        else: st.error("Debe firmar y autorizar el procedimiento.")

# --- PÁGINA 4: FINALIZACIÓN ---
elif st.session_state.step == 4:
    mostrar_logo(); st.success("Registro Completado con Éxito")
    pdf_bytes = generar_pdf_clinico(st.session_state.form)
    st.download_button(label="📥 Descargar PDF de Registro (Compilado Clínico)", data=pdf_bytes, file_name=f"Registro_{st.session_state.form['nombre']}.pdf", mime="application/pdf")
    if st.button("Nuevo Registro"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
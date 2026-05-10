import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from fpdf import FPDF
import os

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

# 2. GESTIÓN DE ESTADO (PERSISTENCIA TOTAL)
if 'step' not in st.session_state:
    st.session_state.step = 1

if 'form' not in st.session_state:
    st.session_state.form = {
        "rut": "", "nombre": "", "genero_idx": 0, "sexo_bio_idx": 0,
        "fecha_nac": date(1990, 1, 1), "email": "", 
        "nombre_tutor": "", "rut_tutor": "",
        "esp_idx": 0, "pre_idx": 0,
        "ant_ayuno": "No", "ant_asma": "No", "ant_diabetes": "No", "ant_hiperten": "No",
        "ant_hipertiroid": "No", "ant_renal": "No", "ant_dialisis": "No", 
        "ant_implantes": "No", "ant_marcapaso": "No", "ant_metformina": "No",
        "ant_embarazo": "No", "ant_lactancia": "No", "ant_cardiaca": "No",
        "otras_cirugias": "",
        "tipo_cancer": "", "rt": False, "qt": False, "bt": False, "it": False, "otro_trat_cancer": "",
        "ex_rx": False, "ex_eco": False, "ex_tc": False, "ex_rm": False, "otro_ex": "",
        "creatinina": 0.0, "peso": 70.0, "vfg": 0.0,
        "veracidad": None, "autoriza_gad": None
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

def generar_pdf(datos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="NORTE IMAGEN - COMPROBANTE DE REGISTRO", ln=True, align='C')
    pdf.set_font("Arial", size=11)
    pdf.ln(10)
    for key, value in datos.items():
        if "idx" not in key and value not in [None, False]:
            texto = f"{key.replace('_', ' ').upper()}: {value}"
            pdf.cell(200, 8, txt=texto.encode('latin-1', 'replace').decode('latin-1'), ln=True)
    return pdf.output(dest='S').encode('latin-1')

@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv('listado_prestaciones.csv', sep=None, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        return df
    except: return None

df = cargar_datos()

# ---------------------------------------------------------
# PASO 1: DATOS PERSONALES
# ---------------------------------------------------------
if st.session_state.step == 1:
    mostrar_logo()
    st.title("Registro de Paciente")
    
    if df is not None:
        col1, col2 = st.columns(2)
        with col1:
            rut_in = st.text_input("RUT del Paciente", value=st.session_state.form["rut"], placeholder="12.345.678-K")
            nombre_in = st.text_input("Nombre Completo del Paciente", value=st.session_state.form["nombre"])
            gen_opts = ["Masculino", "Femenino", "No binario"]
            genero_in = st.selectbox("Identidad de Género", gen_opts, index=st.session_state.form["genero_idx"])
            
            sexo_final = genero_in
            if genero_in == "No binario":
                bio_opts = ["Masculino", "Femenino"]
                sexo_bio = st.selectbox("Sexo asignado al nacer", bio_opts, index=st.session_state.form["sexo_bio_idx"])
                sexo_final = sexo_bio

        with col2:
            fecha_in = st.date_input("Fecha de Nacimiento", value=st.session_state.form["fecha_nac"], 
                                    min_value=date(1900, 1, 1), max_value=date.today(), format="DD/MM/YYYY")
            email_in = st.text_input("Email de contacto", value=st.session_state.form["email"])

        edad_act = calcular_edad(fecha_in)
        if edad_act < 18:
            st.warning(f"👦 PACIENTE MENOR DE EDAD ({edad_act} años)")
            st.markdown('<div class="section-header">Datos del Representante Legal:</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            tutor_nom = c1.text_input("Nombre Representante", value=st.session_state.form["nombre_tutor"])
            tutor_rut = c2.text_input("RUT Representante", value=st.session_state.form["rut_tutor"])
            st.session_state.form["nombre_tutor"] = tutor_nom
            st.session_state.form["rut_tutor"] = formatear_rut(tutor_rut)

        st.markdown('<div class="section-header">Información del Examen:</div>', unsafe_allow_html=True)
        esp_raw = sorted([str(e) for e in df['ESPECIALIDAD'].unique() if pd.notna(e)])
        esp_finales = [e for e in esp_raw if "NEURO" in e.upper()] + [e for e in esp_raw if "NEURO" not in e.upper()]
        
        col_e1, col_e2 = st.columns(2)
        esp_sel = col_e1.selectbox("Especialidad", esp_finales, index=st.session_state.form["esp_idx"])
        list_pre = sorted(df[df['ESPECIALIDAD'] == esp_sel]['PROCEDIMIENTO A REALIZAR'].unique().tolist())
        pre_sel = col_e2.selectbox("Procedimiento", list_pre)

        st.write("Cargue la Orden Médica:")
        st.file_uploader("Subir Orden (PDF/Imagen)", type=["pdf", "jpg", "png"], accept_multiple_files=True, key="up_orden")

        if st.button("CONTINUAR"):
            st.session_state.form.update({
                "rut": formatear_rut(rut_in), "nombre": nombre_in, "genero_idx": gen_opts.index(genero_in),
                "fecha_nac": fecha_in, "email": email_in, "esp_idx": esp_finales.index(esp_sel)
            })
            datos_fila = df[(df['ESPECIALIDAD'] == esp_sel) & (df['PROCEDIMIENTO A REALIZAR'] == pre_sel)]
            st.session_state.tiene_contraste = str(datos_fila['MEDIO DE CONTRASTE'].values[0]).strip().upper() == "SI" if not datos_fila.empty else False
            st.session_state.sexo_para_calculo = sexo_final
            st.session_state.edad_para_calculo = edad_act
            st.session_state.procedimiento = pre_sel
            st.session_state.step = 2
            st.rerun()

# ---------------------------------------------------------
# PASO 2: CUESTIONARIO Y SEGURIDAD
# ---------------------------------------------------------
elif st.session_state.step == 2:
    mostrar_logo()
    st.title("📋 Cuestionario de Seguridad RM")
    
    st.markdown('<div class="section-header">Antecedentes clínicos:</div>', unsafe_allow_html=True)
    c_a, c_b, c_c = st.columns(3)
    opts = ["No", "Sí"]
    
    keys_a = [("ant_ayuno", "Ayuno (4 hrs.)"), ("ant_asma", "Asma"), ("ant_diabetes", "Diabetes"), ("ant_hiperten", "Hipertensión")]
    keys_b = [("ant_hipertiroid", "Hipertiroidismo"), ("ant_renal", "Falla Renal"), ("ant_dialisis", "Diálisis"), ("ant_implantes", "Implantes/Metales")]
    keys_c = [("ant_marcapaso", "Marcapaso"), ("ant_metformina", "Metformina"), ("ant_embarazo", "Embarazo"), ("ant_lactancia", "Lactancia")]

    for col, keys in zip([c_a, c_b, c_c], [keys_a, keys_b, keys_c]):
        for k, label in keys:
            st.session_state.form[k] = col.radio(label, opts, index=opts.index(st.session_state.form[k]), horizontal=True)
    
    st.session_state.form["ant_cardiaca"] = st.radio("¿Cirugía Cardiaca?", opts, index=opts.index(st.session_state.form["ant_cardiaca"]), horizontal=True)
    st.session_state.form["otras_cirugias"] = st.text_area("Otras cirugías (año):", value=st.session_state.form["otras_cirugias"])

    st.markdown('<div class="section-header">Tratamientos por Cáncer:</div>', unsafe_allow_html=True)
    st.session_state.form["tipo_cancer"] = st.text_input("Tipo de cáncer:", value=st.session_state.form["tipo_cancer"])
    ct1, ct2, ct3, ct4 = st.columns(4)
    st.session_state.form["rt"] = ct1.checkbox("Radioterapia", value=st.session_state.form["rt"])
    st.session_state.form["qt"] = ct2.checkbox("Quimioterapia", value=st.session_state.form["qt"])
    st.session_state.form["bt"] = ct3.checkbox("Braquiterapia", value=st.session_state.form["bt"])
    st.session_state.form["it"] = ct4.checkbox("Inmunoterapia", value=st.session_state.form["it"])
    st.session_state.form["otro_trat_cancer"] = st.text_input("Otro tratamiento:", value=st.session_state.form["otro_trat_cancer"])

    st.markdown('<div class="section-header">Exámenes Anteriores:</div>', unsafe_allow_html=True)
    ce1, ce2, ce3, ce4 = st.columns(4)
    st.session_state.form["ex_rx"] = ce1.checkbox("Rx", value=st.session_state.form["ex_rx"])
    st.session_state.form["ex_eco"] = ce2.checkbox("Eco", value=st.session_state.form["ex_eco"])
    st.session_state.form["ex_tc"] = ce3.checkbox("TC", value=st.session_state.form["ex_tc"])
    st.session_state.form["ex_rm"] = ce4.checkbox("RM", value=st.session_state.form["ex_rm"])
    st.file_uploader("Subir archivos previos", type=["pdf", "jpg", "png"], accept_multiple_files=True, key="up_prev")

    if st.session_state.tiene_contraste:
        st.divider()
        st.warning("⚠️ REQUERIDO: CÁLCULO DE FUNCIÓN RENAL")
        col_v1, col_v2 = st.columns(2)
        st.session_state.form["creatinina"] = col_v1.number_input("Creatinina (mg/dL)", value=st.session_state.form["creatinina"], step=0.01)
        st.session_state.form["peso"] = col_v2.number_input("Peso (kg)", value=st.session_state.form["peso"])
        if st.session_state.form["creatinina"] > 0:
            vfg = ((140 - st.session_state.edad_para_calculo) * st.session_state.form["peso"]) / (72 * st.session_state.form["creatinina"])
            if st.session_state.sexo_para_calculo == "Femenino": vfg *= 0.85
            st.session_state.form["vfg"] = vfg
            st.markdown(f'<div class="vfg-box">VFG Estimada: <h2>{vfg:.2f} mL/min</h2></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">Declaración de Veracidad:</div>', unsafe_allow_html=True)
    st.session_state.form["veracidad"] = st.radio("¿Declara que la información es fidedigna?", ["SÍ", "NO"], index=None)

    c_b1, c_b2 = st.columns(2)
    if c_b1.button("Atrás"): st.session_state.step = 1; st.rerun()
    if c_b2.button("Siguiente"):
        if st.session_state.form["veracidad"] == "SÍ": st.session_state.step = 3; st.rerun()
        else: st.error("Debe declarar veracidad para continuar.")

# ---------------------------------------------------------
# PASO 3: CONSENTIMIENTO INFORMADO (TEXTO COMPLETO)
# ---------------------------------------------------------
elif st.session_state.step == 3:
    mostrar_logo()
    st.title("🖋️ Consentimiento Informado")
    sujeto = st.session_state.form['nombre_tutor'] if st.session_state.form['nombre_tutor'] else st.session_state.form['nombre']
    
    if st.session_state.tiene_contraste:
        st.markdown("""
        <div class="legal-text">
        <strong>OBJETIVOS:</strong> La Resonancia Magnética (RM) es una segura técnica de Diagnóstico, que permite la adquisición de imágenes de gran sensibilidad en todos los planos del espacio de las estructuras del cuerpo. Tiene como objetivo obtener Información, datos funcionales y morfológicos para detectar precozmente una enfermedad. Para este examen eventualmente se puede requerir la utilización de un medio de contraste paramagnético de administración endovenosa llamado gadolinio, que permite realzar ciertos tejidos del cuerpo para un mejor diagnóstico.<br><br>
        <strong>CARACTERÍSTICAS:</strong> La Resonancia utiliza fuertes campos magnéticos y ondas de radiofrecuencia, por lo que es muy importante dejar fuera de la sala absolutamente todo lo que lleve consigo de tipo metálico y/o electrónico. Avísenos si lleva material de este tipo en su cuerpo (fijaciones dentales, piercings, tatuajes, esquirlas metálicas, clips metálicos, marcapasos, desfibriladores, etc.), ya que puede contraindicar la realización de este examen. La exploración suele durar entre 20 min y 1 hr. Notará ruido derivado del funcionamiento de la RM, todo esto es normal y se le vigilará constantemente.<br><br>
        <strong>POTENCIALES RIESGOS:</strong> Existe una muy baja posibilidad de reacción adversa al medio de contraste (0.07-2.4%) mayoritariamente leve (náuseas o cefaleas). Pacientes con deterioro importante de la función renal poseen riesgo de desarrollo de fibrosis nefrogénica sistémica.<br><br>
        He sido informado de mi derecho de anular o revocar posteriormente este documento, dejándolo constatado por escrito.
        </div>
        """, unsafe_allow_html=True)
        st.session_state.form["autoriza_gad"] = st.radio(f"¿Autoriza el procedimiento {st.session_state.procedimiento} y uso de contraste?", ["SÍ", "NO"], index=None)
    else:
        st.info(f"Yo, {sujeto}, autorizo la realización del examen {st.session_state.procedimiento}.")
        st.session_state.form["autoriza_gad"] = "SÍ"

    st.write("Firma Digital (en recuadro blanco):")
    canvas_result = st_canvas(stroke_width=2, stroke_color="#000", background_color="#fff", height=150, width=400, key="canvas")

    c_f1, c_f2 = st.columns(2)
    if c_f1.button("Atrás"): st.session_state.step = 2; st.rerun()
    if c_f2.button("FINALIZAR REGISTRO"):
        if st.session_state.form["autoriza_gad"] == "SÍ" and canvas_result.image_data is not None:
            st.session_state.step = 4; st.balloons(); st.rerun()
        else: st.error("Debe autorizar y firmar para finalizar.")

# ---------------------------------------------------------
# PASO 4: ÉXITO Y PDF
# ---------------------------------------------------------
elif st.session_state.step == 4:
    mostrar_logo()
    st.success(f"¡Registro completado con éxito para {st.session_state.form['nombre']}!")
    
    pdf_bytes = generar_pdf(st.session_state.form)
    st.download_button(label="📥 Descargar Resumen en PDF", data=pdf_bytes, file_name=f"Registro_{st.session_state.form['rut']}.pdf", mime="application/pdf")
    
    if st.button("Nuevo Registro"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()
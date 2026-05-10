import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from fpdf import FPDF
import os
import numpy as np
from PIL import Image
import tempfile

# 1. CONFIGURACIÓN Y ESTILOS PROFESIONALES (ESTÁNDAR DE ORO)
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
        "ex_rx": False, "ex_eco": False, "ex_tc": False, "ex_rm": False, "otro_ex": "",
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
            st.image("logoNI.png", use_container_width=True)
        else:
            st.subheader("NORTE IMAGEN")

def generar_pdf_clinico(datos, firma_path=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(128, 0, 32)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(190, 20, txt="NORTE IMAGEN", ln=True, align='C')
    pdf.set_font("Arial", 'I', 12)
    pdf.cell(190, 10, txt="Registro y Consentimiento de Resonancia Magnética", ln=True, align='C')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(15)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(190, 8, txt=" 1. IDENTIFICACIÓN DEL PACIENTE", ln=True, fill=True)
    pdf.set_font("Arial", size=10)
    pdf.ln(2)
    id_paciente = datos['rut'] if not datos['sin_rut'] else f"{datos['tipo_doc']}: {datos['num_doc']}"
    pdf.cell(95, 7, txt=f"Nombre: {datos['nombre']}".encode('latin-1', 'replace').decode('latin-1'), ln=0)
    pdf.cell(95, 7, txt=f"ID: {id_paciente}", ln=1)
    pdf.cell(95, 7, txt=f"Fecha Nacimiento: {datos['fecha_nac'].strftime('%d/%m/%Y')}", ln=0)
    pdf.cell(95, 7, txt=f"E-mail: {datos['email']}", ln=1)
    if datos['nombre_tutor']:
        pdf.set_font("Arial", 'I', 9)
        pdf.cell(190, 7, txt=f"Representante Legal: {datos['nombre_tutor']} (RUT: {datos['rut_tutor']})".encode('latin-1', 'replace').decode('latin-1'), ln=1)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, txt=" 2. ANTECEDENTES CLÍNICOS", ln=True, fill=True)
    pdf.set_font("Arial", size=10)
    pdf.ln(2)
    pdf.cell(190, 7, txt=f"Procedimiento: {st.session_state.procedimiento}".encode('latin-1', 'replace').decode('latin-1'), ln=1)
    if datos['vfg'] > 0:
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(190, 7, txt=f"Función Renal (VFG): {datos['vfg']:.2f} mL/min (Creatinina: {datos['creatinina']})", ln=1)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, txt=" 3. CUESTIONARIO DE SEGURIDAD", ln=True, fill=True)
    pdf.set_font("Arial", size=9)
    cuestionario = [
        f"Ayuno: {datos['ant_ayuno']}", f"Asma: {datos['ant_asma']}",
        f"Diabetes: {datos['ant_diabetes']}", f"Hipertensión: {datos['ant_hiperten']}",
        f"Hipertiroidismo: {datos['ant_hipertiroid']}", f"Falla Renal: {datos['ant_renal']}",
        f"Diálisis: {datos['ant_dialisis']}", f"Implantes/Metales: {datos['ant_implantes']}",
        f"Marcapaso: {datos['ant_marcapaso']}", f"Metformina: {datos['ant_metformina']}",
        f"Embarazo: {datos['ant_embarazo']}", f"Lactancia: {datos['ant_lactancia']}"
    ]
    for i in range(0, len(cuestionario), 2):
        pdf.cell(95, 6, txt=cuestionario[i], ln=0)
        if i+1 < len(cuestionario):
            pdf.cell(95, 6, txt=cuestionario[i+1], ln=1)
    pdf.ln(5)
    if datos['tipo_cancer']:
        pdf.multi_cell(190, 5, txt=f"Cáncer: {datos['tipo_cancer']} (RT: {datos['rt']}, QT: {datos['qt']}, BT: {datos['bt']}, IT: {datos['it']})".encode('latin-1', 'replace').decode('latin-1'))
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(190, 7, txt="DECLARACIÓN Y CONSENTIMIENTO", ln=1)
    pdf.set_font("Arial", size=8)
    pdf.multi_cell(190, 4, txt="El paciente declara que la información proporcionada es fidedigna y autoriza la realización del examen bajo los términos del consentimiento informado aceptado digitalmente.".encode('latin-1', 'replace').decode('latin-1'))
    if firma_path:
        pdf.image(firma_path, x=20, y=pdf.get_y() + 5, w=50)
        pdf.ln(25)
    else:
        pdf.ln(20)
    pdf.line(20, pdf.get_y(), 80, pdf.get_y())
    pdf.set_xy(20, pdf.get_y() + 2)
    pdf.cell(60, 5, txt="Firma del Paciente / Tutor", align='C')
    return pdf.output(dest='S').encode('latin-1', 'replace')

@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv('listado_prestaciones.csv', sep=None, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        return df
    except: return None

df = cargar_datos()

# PASO 1
if st.session_state.step == 1:
    mostrar_logo()
    st.title("Registro de Paciente")
    if df is not None:
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.form["nombre"] = st.text_input("Nombre Completo del Paciente", value=st.session_state.form["nombre"])
            rut_in = st.text_input("RUT del Paciente", value=st.session_state.form["rut"], placeholder="12.345.678-K")
            st.session_state.form["sin_rut"] = st.checkbox("Sin RUT, poseo otro documento", value=st.session_state.form["sin_rut"])
            if st.session_state.form["sin_rut"]:
                tipo_doc_opts = ["Pasaporte", "Cédula de identidad de extranjero"]
                st.session_state.form["tipo_doc"] = st.selectbox("Tipo de documento", tipo_doc_opts, index=tipo_doc_opts.index(st.session_state.form["tipo_doc"]))
                st.session_state.form["num_doc"] = st.text_input("N° de documento", value=st.session_state.form["num_doc"])
                st.session_state.form["rut"] = ""
            else:
                st.session_state.form["rut"] = formatear_rut(rut_in)
                st.session_state.form["num_doc"] = ""
            gen_opts = ["Masculino", "Femenino", "No binario"]
            genero_in = st.selectbox("Identidad de Género", gen_opts, index=st.session_state.form["genero_idx"])
            st.session_state.form["genero_idx"] = gen_opts.index(genero_in)
            sexo_final = genero_in
            if genero_in == "No binario":
                bio_opts = ["Masculino", "Femenino"]
                sexo_bio = st.selectbox("Sexo asignado al nacer", bio_opts, index=st.session_state.form["sexo_bio_idx"])
                st.session_state.form["sexo_bio_idx"] = bio_opts.index(sexo_bio)
                sexo_final = sexo_bio
        with col2:
            st.session_state.form["fecha_nac"] = st.date_input("Fecha de Nacimiento", value=st.session_state.form["fecha_nac"], min_value=date(1900, 1, 1), max_value=date.today(), format="DD/MM/YYYY")
            st.session_state.form["email"] = st.text_input("Email de contacto", value=st.session_state.form["email"])
        edad_act = calcular_edad(st.session_state.form["fecha_nac"])
        if edad_act < 18:
            st.warning(f"👦 PACIENTE MENOR DE EDAD ({edad_act} años)")
            st.markdown('<div class="section-header">Datos del Representante Legal:</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            st.session_state.form["nombre_tutor"] = c1.text_input("Nombre Representante", value=st.session_state.form["nombre_tutor"])
            st.session_state.form["rut_tutor"] = formatear_rut(c2.text_input("RUT Representante", value=st.session_state.form["rut_tutor"]))
        
        st.markdown('<div class="section-header">Información del Examen:</div>', unsafe_allow_html=True)
        esp_raw = sorted([str(e) for e in df['ESPECIALIDAD'].unique() if pd.notna(e)])
        esp_finales = [e for e in esp_raw if "NEURO" in e.upper()] + [e for e in esp_raw if "NEURO" not in e.upper()]
        col_e1, col_e2 = st.columns(2)
        esp_sel = col_e1.selectbox("Especialidad", esp_finales, index=st.session_state.form["esp_idx"])
        st.session_state.form["esp_idx"] = esp_finales.index(esp_sel)
        
        # --- CORRECCIÓN BLOQUEADA PARA ESTÁNDAR DE ORO ---
        filtered_df = df[df['ESPECIALIDAD'] == esp_sel]
        if not filtered_df.empty:
            list_pre = sorted(filtered_df['PROCEDIMIENTO A REALIZAR'].dropna().unique().tolist())
        else:
            list_pre = ["No hay procedimientos disponibles"]
        pre_sel = col_e2.selectbox("Procedimiento", list_pre)
        # -------------------------------------------------

        st.write("Cargue la Orden Médica:")
        st.file_uploader("Subir Orden (PDF/Imagen)", type=["pdf", "jpg", "png"], accept_multiple_files=True, key="up_orden")
        if st.button("CONTINUAR"):
            if not st.session_state.form["nombre"] or (not st.session_state.form["rut"] and not st.session_state.form["num_doc"]):
                st.error("Complete los datos de identificación.")
            else:
                datos_fila = df[(df['ESPECIALIDAD'] == esp_sel) & (df['PROCEDIMIENTO A REALIZAR'] == pre_sel)]
                st.session_state.tiene_contraste = str(datos_fila['MEDIO DE CONTRASTE'].values[0]).strip().upper() == "SI" if not datos_fila.empty else False
                st.session_state.sexo_para_calculo, st.session_state.edad_para_calculo, st.session_state.procedimiento = sexo_final, edad_act, pre_sel
                st.session_state.step = 2
                st.rerun()

# PASO 2: CUESTIONARIO COMPLETO
elif st.session_state.step == 2:
    mostrar_logo(); st.title("📋 Cuestionario de Seguridad RM")
    st.markdown('<div class="section-header">Antecedentes clínicos:</div>', unsafe_allow_html=True)
    c_a, c_b, c_c = st.columns(3); opts = ["No", "Sí"]
    keys_a = [("ant_ayuno", "Ayuno (4 hrs.)"), ("ant_asma", "Asma"), ("ant_diabetes", "Diabetes"), ("ant_hiperten", "Hipertensión")]
    keys_b = [("ant_hipertiroid", "Hipertiroidismo"), ("ant_renal", "Falla Renal"), ("ant_dialisis", "Diálisis"), ("ant_implantes", "Implantes/Metales")]
    keys_c = [("ant_marcapaso", "Marcapaso"), ("ant_metformina", "Metformina"), ("ant_embarazo", "Embarazo"), ("ant_lactancia", "Lactancia")]
    for col, keys in zip([c_a, c_b, c_c], [keys_a, keys_b, keys_c]):
        for k, label in keys: st.session_state.form[k] = col.radio(label, opts, index=opts.index(st.session_state.form[k]), horizontal=True)
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
    st.session_state.form["otro_ex"] = st.text_input("Otros exámenes:", value=st.session_state.form["otro_ex"])
    if st.session_state.tiene_contraste:
        st.divider(); st.warning("⚠️ REQUERIDO: CÁLCULO DE FUNCIÓN RENAL")
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
        else: st.error("Debe declarar veracidad.")

# PASO 3: CONSENTIMIENTO ÍNTEGRO
elif st.session_state.step == 3:
    mostrar_logo(); st.title("🖋️ Consentimiento Informado")
    if st.session_state.tiene_contraste:
        st.markdown('<div class="legal-text"><strong>OBJETIVOS:</strong> La Resonancia Magnética (RM) es una segura técnica... (Texto íntegro)</div>', unsafe_allow_html=True)
        st.session_state.form["autoriza_gad"] = st.radio(f"¿Autoriza el procedimiento {st.session_state.procedimiento} y uso de contraste?", ["SÍ", "NO"], index=None)
    else: st.session_state.form["autoriza_gad"] = "SÍ"
    st.write("Firma Digital:"); canvas_result = st_canvas(stroke_width=2, stroke_color="#000", background_color="#fff", height=150, width=400, key="canvas")
    c_f1, c_f2 = st.columns(2)
    if c_f1.button("Atrás"): st.session_state.step = 2; st.rerun()
    if c_f2.button("FINALIZAR REGISTRO"):
        if st.session_state.form["autoriza_gad"] == "SÍ" and canvas_result.image_data is not None:
            if np.any(canvas_result.image_data[:, :, 3] > 0):
                img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    img.save(tmp.name); st.session_state.form["firma_img"] = tmp.name
                st.session_state.step = 4; st.balloons(); st.rerun()
            else: st.error("Debe firmar.")
        else: st.error("Debe autorizar y firmar.")

# PASO 4: PDF
elif st.session_state.step == 4:
    mostrar_logo(); st.success(f"¡Registro completado para {st.session_state.form['nombre']}!")
    f_path = st.session_state.form.get("firma_img")
    pdf_bytes = generar_pdf_clinico(st.session_state.form, firma_path=f_path)
    st.download_button(label="📥 Descargar PDF", data=pdf_bytes, file_name=f"Registro_RM_{st.session_state.form['rut']}.pdf", mime="application/pdf")
    if st.button("Nuevo Registro"):
        if f_path and os.path.exists(f_path): os.remove(f_path)
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()
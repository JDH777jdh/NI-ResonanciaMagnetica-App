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
    cuerpo, dv = rut_limpio[:-1], rut_limpio[-1]
    if cuerpo.isdigit():
        return f"{int(cuerpo):,}".replace(",", ".") + f"-{dv}"
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
    pdf.set_text_color(0, 0, 0); pdf.ln(15)
    
    pdf.set_font("Arial", 'B', 12); pdf.set_fill_color(240, 240, 240)
    pdf.cell(190, 8, txt=" 1. IDENTIFICACIÓN DEL PACIENTE", ln=True, fill=True)
    pdf.set_font("Arial", size=10); pdf.ln(2)
    
    id_paciente = datos['rut'] if not datos['sin_rut'] else f"{datos['tipo_doc']}: {datos['num_doc']}"
    pdf.cell(95, 7, txt=f"Nombre: {datos['nombre']}".encode('latin-1', 'replace').decode('latin-1'), ln=0)
    pdf.cell(95, 7, txt=f"ID: {id_paciente}", ln=1)
    pdf.cell(95, 7, txt=f"Fecha Nacimiento: {datos['fecha_nac'].strftime('%d/%m/%Y')}", ln=0)
    pdf.cell(95, 7, txt=f"E-mail: {datos['email']}", ln=1)
    
    if datos['nombre_tutor']:
        pdf.set_font("Arial", 'I', 9)
        pdf.cell(190, 7, txt=f"Representante Legal: {datos['nombre_tutor']} (RUT: {datos['rut_tutor']})".encode('latin-1', 'replace').decode('latin-1'), ln=1)
    
    pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(190, 8, txt=" 2. ANTECEDENTES CLÍNICOS", ln=True, fill=True)
    pdf.set_font("Arial", size=10); pdf.ln(2)
    pdf.cell(190, 7, txt=f"Procedimiento: {st.session_state.procedimiento}".encode('latin-1', 'replace').decode('latin-1'), ln=1)
    
    if datos['vfg'] > 0:
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(190, 7, txt=f"Función Renal (VFG): {datos['vfg']:.2f} mL/min (Creatinina: {datos['creatinina']})", ln=1)
    
    pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(190, 8, txt=" 3. CUESTIONARIO DE SEGURIDAD", ln=True, fill=True)
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
        if i+1 < len(cuestionario): pdf.cell(95, 6, txt=cuestionario[i+1], ln=1)
    
    if firma_path:
        pdf.image(firma_path, x=20, y=pdf.get_y() + 10, w=50); pdf.ln(30)
    else: pdf.ln(20)
    pdf.line(20, pdf.get_y(), 80, pdf.get_y())
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

# PASO 1: DATOS PERSONALES
if st.session_state.step == 1:
    mostrar_logo(); st.title("Registro de Paciente")
    if df is not None:
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.form["nombre"] = st.text_input("Nombre Completo del Paciente", value=st.session_state.form["nombre"])
            rut_p = st.text_input("RUT del Paciente", value=st.session_state.form["rut"], placeholder="12.345.678-K")
            st.session_state.form["rut"] = formatear_rut(rut_p)
            st.session_state.form["sin_rut"] = st.checkbox("Sin RUT, poseo otro documento", value=st.session_state.form["sin_rut"])
            if st.session_state.form["sin_rut"]:
                t_opts = ["Pasaporte", "Cédula de extranjero"]
                st.session_state.form["tipo_doc"] = st.selectbox("Tipo de documento", t_opts, index=t_opts.index(st.session_state.form["tipo_doc"]))
                st.session_state.form["num_doc"] = st.text_input("N° de documento", value=st.session_state.form["num_doc"])
            
            gen_opts = ["Masculino", "Femenino", "No binario"]
            genero_in = st.selectbox("Identidad de Género", gen_opts, index=st.session_state.form["genero_idx"])
            st.session_state.form["genero_idx"] = gen_opts.index(genero_in)

        with col2:
            # BLOQUEO FECHA DD/MM/YYYY
            st.session_state.form["fecha_nac"] = st.date_input("Fecha de Nacimiento", value=st.session_state.form["fecha_nac"], min_value=date(1900,1,1), max_value=date.today(), format="DD/MM/YYYY")
            st.session_state.form["email"] = st.text_input("Email de contacto", value=st.session_state.form["email"])
            
            sexo_final = genero_in
            if genero_in == "No binario":
                b_opts = ["Masculino", "Femenino"]
                sexo_bio = st.selectbox("Sexo asignado al nacer", b_opts, index=st.session_state.form["sexo_bio_idx"])
                st.session_state.form["sexo_bio_idx"] = b_opts.index(sexo_bio)
                sexo_final = sexo_bio

        # LÓGICA DE MENORES (Verificada)
        edad_act = calcular_edad(st.session_state.form["fecha_nac"])
        if edad_act < 18:
            st.warning(f"👦 PACIENTE MENOR DE EDAD ({edad_act} años)")
            st.markdown('<div class="section-header">Datos del Representante Legal:</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            st.session_state.form["nombre_tutor"] = c1.text_input("Nombre Representante", value=st.session_state.form["nombre_tutor"])
            rut_t = c2.text_input("RUT Representante", value=st.session_state.form["rut_tutor"])
            st.session_state.form["rut_tutor"] = formatear_rut(rut_t)

        st.markdown('<div class="section-header">Información del Examen:</div>', unsafe_allow_html=True)
        esp_raw = sorted([str(e) for e in df['ESPECIALIDAD'].unique() if pd.notna(e)])
        esp_finales = [e for e in esp_raw if "NEURO" in e.upper()] + [e for e in esp_raw if "NEURO" not in e.upper()]
        col_e1, col_e2 = st.columns(2)
        esp_sel = col_e1.selectbox("Especialidad", esp_finales, index=st.session_state.form["esp_idx"])
        st.session_state.form["esp_idx"] = esp_finales.index(esp_sel)
        
        filtered_df = df[df['ESPECIALIDAD'] == esp_sel]
        list_pre = sorted(filtered_df['PROCEDIMIENTO A REALIZAR'].dropna().unique().tolist()) if not filtered_df.empty else ["No disponible"]
        pre_sel = col_e2.selectbox("Procedimiento", list_pre)

        if st.button("CONTINUAR"):
            if not st.session_state.form["nombre"]: st.error("Falta nombre.")
            else:
                row = df[(df['ESPECIALIDAD'] == esp_sel) & (df['PROCEDIMIENTO A REALIZAR'] == pre_sel)]
                st.session_state.tiene_contraste = str(row['MEDIO DE CONTRASTE'].values[0]).upper() == "SI" if not row.empty else False
                st.session_state.sexo_para_calculo, st.session_state.edad_para_calculo, st.session_state.procedimiento = sexo_final, edad_act, pre_sel
                st.session_state.step = 2; st.rerun()

# PASO 2: CUESTIONARIO COMPLETO (BLOQUEADO)
elif st.session_state.step == 2:
    mostrar_logo(); st.title("📋 Cuestionario de Seguridad RM")
    st.markdown('<div class="section-header">Antecedentes clínicos:</div>', unsafe_allow_html=True)
    c_a, c_b, c_c = st.columns(3); opts = ["No", "Sí"]
    k_a = [("ant_ayuno", "Ayuno"), ("ant_asma", "Asma"), ("ant_diabetes", "Diabetes"), ("ant_hiperten", "Hipertensión")]
    k_b = [("ant_hipertiroid", "Hipertiroidismo"), ("ant_renal", "Falla Renal"), ("ant_dialisis", "Diálisis"), ("ant_implantes", "Implantes")]
    k_c = [("ant_marcapaso", "Marcapaso"), ("ant_metformina", "Metformina"), ("ant_embarazo", "Embarazo"), ("ant_lactancia", "Lactancia")]
    for col, keys in zip([c_a, c_b, c_c], [k_a, k_b, k_c]):
        for k, label in keys: st.session_state.form[k] = col.radio(label, opts, index=opts.index(st.session_state.form[k]), horizontal=True)
    
    st.session_state.form["ant_cardiaca"] = st.radio("¿Cirugía Cardiaca?", opts, index=opts.index(st.session_state.form["ant_cardiaca"]), horizontal=True)
    st.session_state.form["otras_cirugias"] = st.text_area("Otras cirugías:", value=st.session_state.form["otras_cirugias"])
    st.markdown('<div class="section-header">Cáncer:</div>', unsafe_allow_html=True)
    st.session_state.form["tipo_cancer"] = st.text_input("Tipo:", value=st.session_state.form["tipo_cancer"])
    st.session_state.form["rt"] = st.checkbox("Radioterapia", value=st.session_state.form["rt"])
    st.session_state.form["qt"] = st.checkbox("Quimioterapia", value=st.session_state.form["qt"])
    st.markdown('<div class="section-header">Exámenes Anteriores:</div>', unsafe_allow_html=True)
    st.session_state.form["ex_rx"] = st.checkbox("Rx", value=st.session_state.form["ex_rx"])
    st.session_state.form["ex_rm"] = st.checkbox("RM", value=st.session_state.form["ex_rm"])
    
    if st.session_state.tiene_contraste:
        st.divider(); st.warning("⚠️ REQUERIDO: CÁLCULO VFG")
        v1, v2 = st.columns(2)
        st.session_state.form["creatinina"] = v1.number_input("Creatinina", value=st.session_state.form["creatinina"], step=0.01)
        st.session_state.form["peso"] = v2.number_input("Peso (kg)", value=st.session_state.form["peso"])
        if st.session_state.form["creatinina"] > 0:
            vfg = ((140 - st.session_state.edad_para_calculo) * st.session_state.form["peso"]) / (72 * st.session_state.form["creatinina"])
            if st.session_state.sexo_para_calculo == "Femenino": vfg *= 0.85
            st.session_state.form["vfg"] = vfg
            st.markdown(f'<div class="vfg-box">VFG: <h2>{vfg:.2f}</h2></div>', unsafe_allow_html=True)

    st.session_state.form["veracidad"] = st.radio("¿Información fidedigna?", ["SÍ", "NO"], index=None)
    if st.button("Siguiente") and st.session_state.form["veracidad"] == "SÍ": st.session_state.step = 3; st.rerun()

# PASO 3: CONSENTIMIENTO (BLOQUEADO)
elif st.session_state.step == 3:
    mostrar_logo(); st.title("🖋️ Consentimiento")
    if st.session_state.tiene_contraste:
        st.markdown('<div class="legal-text"><strong>OBJETIVOS:</strong> Texto íntegro de Gadolinio...</div>', unsafe_allow_html=True)
        st.session_state.form["autoriza_gad"] = st.radio("¿Autoriza?", ["SÍ", "NO"], index=None)
    else: st.session_state.form["autoriza_gad"] = "SÍ"
    
    canvas_result = st_canvas(stroke_width=2, stroke_color="#000", background_color="#fff", height=150, width=400, key="canvas")
    if st.button("FINALIZAR REGISTRO") and st.session_state.form["autoriza_gad"] == "SÍ":
        if canvas_result.image_data is not None and np.any(canvas_result.image_data[:, :, 3] > 0):
            img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                img.save(tmp.name); st.session_state.form["firma_img"] = tmp.name
            st.session_state.step = 4; st.balloons(); st.rerun()

# PASO 4: PDF (BLOQUEADO)
elif st.session_state.step == 4:
    mostrar_logo(); st.success("Registro completado.")
    pdf_bytes = generar_pdf_clinico(st.session_state.form, st.session_state.form.get("firma_img"))
    st.download_button("📥 Descargar PDF", pdf_bytes, file_name=f"RM_{st.session_state.form['rut']}.pdf", mime="application/pdf")
    if st.button("Nuevo Registro"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()
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
        margin-top: 25px; margin-bottom: 15px; font-size: 1.2em; font-weight: bold;
    }
    .legal-text {
        background-color: #ffffff; padding: 20px; border-radius: 5px; border: 1px solid #ccc;
        font-size: 0.9em; text-align: justify; color: #333; margin-bottom: 20px;
        max-height: 400px; overflow-y: auto; line-height: 1.5;
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

# 3. FUNCIONES DE APOYO Y PDF
def formatear_rut(rut_sucio):
    rut_limpio = str(rut_sucio).replace(".", "").replace("-", "").upper().strip()
    if len(rut_limpio) < 2: return rut_limpio
    cuerpo, dv = rut_limpio[:-1], rut_limpio[-1]
    if cuerpo.isdigit(): return f"{int(cuerpo):,}".replace(",", ".") + f"-{dv}"
    return rut_sucio

def calcular_edad(fecha_nac):
    today = date.today()
    return today.year - fecha_nac.year - ((today.month, today.day) < (fecha_nac.month, fecha_nac.day))

def generar_pdf(datos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "REGISTRO DE PACIENTE Y CONSENTIMIENTO - NORTE IMAGEN", ln=True, align='C')
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "1. Datos del Paciente", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 5, f"Nombre: {datos['nombre']}\nRUT/Doc: {datos['rut'] if not datos['sin_rut'] else datos['num_doc']}\nEmail: {datos['email']}\nProcedimiento: {st.session_state.procedimiento}")
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "2. Cuestionario de Seguridad", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 5, f"Marcapasos: {datos['bio_marcapaso']}\nImplantes: {datos['bio_implantes']}\nDetalle: {datos['bio_detalle']}\nDiabetes: {datos['clin_diabetes']}\nInsuf. Renal: {datos['clin_renal']}")
    
    if st.session_state.tiene_contraste:
        pdf.cell(200, 10, "3. Datos Clínicos VFG", ln=True)
        pdf.cell(200, 10, f"Creatinina: {datos['creatinina']} mg/dL | VFG: {datos['vfg']:.2f} ml/min", ln=True)

    if datos['firma_img']:
        pdf.add_page()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, "Consentimiento y Firma", ln=True)
        pdf.image(datos['firma_img'], x=10, y=pdf.get_y() + 10, w=80)
    
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

# --- NAVEGACIÓN ---

# PÁGINA 1: REGISTRO
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
            st.session_state.form["fecha_nac"] = st.date_input("Fecha de Nacimiento", value=st.session_state.form["fecha_nac"], min_value=date(1900,1,1), max_value=date.today(), format="DD/MM/YYYY")
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

        st.file_uploader("Cargue la Orden Médica (PDF/JPG):", type=["pdf", "jpg", "jpeg"], key="up_orden_p1")

        if st.button("CONTINUAR"):
            if st.session_state.form["nombre"]:
                row = df[(df['ESPECIALIDAD'] == esp_sel) & (df['PROCEDIMIENTO A REALIZAR'] == pre_sel)]
                st.session_state.tiene_contraste = str(row['MEDIO DE CONTRASTE'].values[0]).upper() == "SI" if not row.empty else False
                st.session_state.procedimiento = pre_sel
                st.session_state.edad_para_calculo = edad
                st.session_state.sexo_para_calculo = sexo_final
                st.session_state.step = 2; st.rerun()

# PÁGINA 2: CUESTIONARIO (REORDENADO)
elif st.session_state.step == 2:
    mostrar_logo(); st.title("📋 Cuestionario de Seguridad")
    opts = ["No", "Sí"]

    st.markdown('<div class="section-header">1. Bioseguridad Magnética</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    st.session_state.form["bio_marcapaso"] = c1.radio("Marcapasos cardiaco:", opts, index=opts.index(st.session_state.form["bio_marcapaso"]), horizontal=True)
    st.session_state.form["bio_implantes"] = c2.radio("Implantes metálicos / electrónicos:", opts, index=opts.index(st.session_state.form["bio_implantes"]), horizontal=True)
    st.session_state.form["bio_detalle"] = st.text_area("Detalle de tipo y ubicación:", value=st.session_state.form["bio_detalle"], height=70)

    st.markdown('<div class="section-header">2. Antecedentes Clínicos</div>', unsafe_allow_html=True)
    ca, cb, cc = st.columns(3)
    k1 = [("clin_ayuno", "Ayuno (2 hrs+)"), ("clin_asma", "Asma"), ("clin_hiperten", "Hipertensión"), ("clin_hipertiroid", "Hipertiroidismo")]
    k2 = [("clin_diabetes", "Diabetes"), ("clin_alergico", "Alérgico"), ("clin_metformina", "Suspende metformina"), ("clin_renal", "Insuficiencia renal")]
    k3 = [("clin_dialisis", "Diálisis"), ("clin_claustro", "Claustrofóbico"), ("clin_embarazo", "Embarazo"), ("clin_lactancia", "Lactancia")]
    for col, keys in zip([ca, cb, cc], [k1, k2, k3]):
        for k, label in keys: st.session_state.form[k] = col.radio(label, opts, index=opts.index(st.session_state.form[k]))

    st.markdown('<div class="section-header">3. Antecedentes Quirúrgicos</div>', unsafe_allow_html=True)
    st.session_state.form["quir_cirugia_check"] = st.radio("¿Ha tenido cirugías?", opts, index=opts.index(st.session_state.form["quir_cirugia_check"]), horizontal=True)
    st.session_state.form["quir_cirugia_detalle"] = st.text_area("Detalle cirugía y fecha:", value=st.session_state.form["quir_cirugia_detalle"], height=70)
    st.session_state.form["quir_cancer_detalle"] = st.text_input("Tratamiento cáncer/otros:", value=st.session_state.form["quir_cancer_detalle"])
    ct1, ct2, ct3, ct4 = st.columns(4)
    st.session_state.form["rt"] = ct1.checkbox("RT", value=st.session_state.form["rt"]); st.session_state.form["qt"] = ct2.checkbox("QT", value=st.session_state.form["qt"])
    st.session_state.form["bt"] = ct3.checkbox("BT", value=st.session_state.form["bt"]); st.session_state.form["it"] = ct4.checkbox("IT", value=st.session_state.form["it"])

    st.markdown('<div class="section-header">4. Exámenes anteriores</div>', unsafe_allow_html=True)
    ce1, ce2, ce3, ce4, ce5 = st.columns(5)
    st.session_state.form["ex_rx"] = ce1.checkbox("Rx"); st.session_state.form["ex_mg"] = ce2.checkbox("MG")
    st.session_state.form["ex_eco"] = ce3.checkbox("Eco"); st.session_state.form["ex_tc"] = ce4.checkbox("TC"); st.session_state.form["ex_rm"] = ce5.checkbox("RM")
    st.file_uploader("Subir exámenes anteriores (Max 4):", type=["pdf", "jpg"], accept_multiple_files=True)

    if st.session_state.tiene_contraste:
        st.markdown('<div class="section-header">5. Cálculo VFG</div>', unsafe_allow_html=True)
        st.session_state.form["creatinina"] = st.number_input("Creatinina (mg/dL)", value=st.session_state.form["creatinina"], step=0.01)
        st.session_state.form["peso"] = st.number_input("Peso (kg)", value=st.session_state.form["peso"])
        if st.session_state.form["creatinina"] > 0:
            vfg = ((140 - st.session_state.edad_para_calculo) * st.session_state.form["peso"]) / (72 * st.session_state.form["creatinina"])
            if st.session_state.sexo_para_calculo == "Femenino": vfg *= 0.85
            st.session_state.form["vfg"] = vfg
            estilo = "vfg-critica" if vfg < 30 else ""
            st.markdown(f'<div class="vfg-box {estilo}">Resultado VFG: <h2>{vfg:.2f} ml/min</h2></div>', unsafe_allow_html=True)

    st.divider()
    st.session_state.form["veracidad"] = st.radio("¿Información fidedigna?", ["SÍ", "NO"], index=None)
    
    col_nav = st.columns(2)
    if col_nav[0].button("ATRÁS"): st.session_state.step = 1; st.rerun()
    if col_nav[1].button("SIGUIENTE"):
        if st.session_state.form["veracidad"] == "SÍ": st.session_state.step = 3; st.rerun()
        else: st.error("Debe declarar veracidad.")

# PÁGINA 3: CONSENTIMIENTO
elif st.session_state.step == 3:
    mostrar_logo(); st.title("Consentimiento informado")
    st.subheader(f"{st.session_state.form['nombre']} - {st.session_state.procedimiento}")

    if st.session_state.tiene_contraste:
        st.markdown("""<div class="legal-text">
        <strong>OBJETIVOS</strong><br>La Resonancia Magnética (RM) es una segura técnica de Diagnóstico, que permite la adquisición de imágenes de gran sensibilidad en todos los planos del espacio de las estructuras del cuerpo... (Texto Completo Solicitado)... <br><br>
        <strong>POTENCIALES RIESGOS</strong><br>Existe una muy baja posibilidad de que se presente una reacción adversa al medio de contraste (0.07-2.4%)... (Texto Completo Solicitado)...
        </div>""", unsafe_allow_html=True)
        st.session_state.form["autoriza_gad"] = st.radio("Autorizo el procedimiento:", ["SÍ", "NO"], index=None)
    else: st.session_state.form["autoriza_gad"] = "SÍ"

    canvas_result = st_canvas(stroke_width=2, stroke_color="#000", background_color="#fff", height=150, width=400, key="canvas")
    
    if st.button("FINALIZAR"):
        if st.session_state.form["autoriza_gad"] == "SÍ" and np.any(canvas_result.image_data[:, :, 3] > 0):
            img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                img.save(tmp.name); st.session_state.form["firma_img"] = tmp.name
            st.session_state.step = 4; st.rerun()

# PÁGINA 4: DESCARGA PDF
elif st.session_state.step == 4:
    mostrar_logo(); st.success("Registro Finalizado")
    pdf_data = generar_pdf(st.session_state.form)
    st.download_button(label="📥 Descargar Documento Completo (PDF)", data=pdf_data, file_name=f"Registro_{st.session_state.form['nombre']}.pdf", mime="application/pdf")
    if st.button("Nuevo Registro"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
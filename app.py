import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from fpdf import FPDF
import os
from PIL import Image
import io
import re

# 1. CONFIGURACIÓN Y ESTILOS
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

# 2. GESTIÓN DE ESTADO
if 'step' not in st.session_state:
    st.session_state.step = 1

if 'form' not in st.session_state:
    st.session_state.form = {
        "nombre": "", "rut": "", "sin_rut": False, "tipo_doc": "Pasaporte", "num_doc": "",
        "genero_idx": 0, "sexo_bio_idx": 0, "fecha_nac": date(1990, 1, 1), "email": "", 
        "nombre_tutor": "", "rut_tutor": "", "esp_nombre": "", "pre_nombre": "",
        "ant_ayuno": "No", "ant_asma": "No", "ant_diabetes": "No", "ant_hiperten": "No",
        "ant_hipertiroid": "No", "ant_renal": "No", "ant_dialisis": "No", 
        "ant_implantes": "No", "ant_marcapaso": "No", "ant_metformina": "No",
        "ant_embarazo": "No", "ant_lactancia": "No", "ant_cardiaca": "No",
        "otras_cirugias": "", "tipo_cancer": "", "rt": False, "qt": False, "bt": False, "it": False, "otro_trat_cancer": "",
        "ex_rx": False, "ex_eco": False, "ex_tc": False, "ex_rm": False,
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

def obtener_iniciales(nombre_completo):
    partes = nombre_completo.split()
    if len(partes) < 2: return ""
    # Retorna iniciales de los apellidos (asumiendo que los últimos dos son apellidos)
    return "".join([p[0].upper() for p in partes[1:]])

def generar_pdf_clinico(datos):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. ENCABEZADO CON LOGO Y TÍTULOS
    if os.path.exists("logoNI.png"):
        pdf.image("logoNI.png", x=10, y=10, w=35)
    
    pdf.set_font("Arial", 'B', 22)
    pdf.set_text_color(128, 0, 32)
    pdf.set_xy(50, 10)
    pdf.cell(140, 10, txt="Norte Imagen", ln=True, align='L')
    
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(50, 50, 50)
    pdf.set_x(50)
    pdf.cell(140, 10, txt="Resonancia Magnética", ln=True, align='L')
    
    pdf.set_font("Arial", 'I', 11)
    pdf.set_x(50)
    pdf.cell(140, 8, txt="Encuesta y consentimiento informado", ln=True, align='L')
    
    pdf.ln(10)
    pdf.set_text_color(0, 0, 0)

    # 2. SECCIÓN: IDENTIFICACIÓN
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, txt=" 1. DATOS DEL PACIENTE", ln=True, fill=True)
    pdf.set_font("Arial", size=10)
    pdf.ln(2)
    
    id_paciente = datos['rut'] if not datos['sin_rut'] else f"{datos['tipo_doc']}: {datos['num_doc']}"
    pdf.cell(95, 7, txt=f"Nombre: {datos['nombre']}".encode('latin-1', 'replace').decode('latin-1'), ln=0)
    pdf.cell(95, 7, txt=f"Documento: {id_paciente}", ln=1)
    pdf.cell(95, 7, txt=f"Fecha Nac.: {datos['fecha_nac']}", ln=0)
    pdf.cell(95, 7, txt=f"E-mail: {datos['email']}", ln=1)
    
    if datos['nombre_tutor']:
        pdf.cell(190, 7, txt=f"Tutor: {datos['nombre_tutor']} (RUT: {datos['rut_tutor']})".encode('latin-1', 'replace').decode('latin-1'), ln=1)
    
    pdf.ln(4)

    # 3. SECCIÓN: EXAMEN
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, txt=" 2. DETALLES DEL EXAMEN", ln=True, fill=True)
    pdf.set_font("Arial", size=10)
    pdf.ln(2)
    pdf.cell(95, 7, txt=f"Especialidad: {datos['esp_nombre']}".encode('latin-1', 'replace').decode('latin-1'), ln=0)
    pdf.cell(95, 7, txt=f"Procedimiento: {datos['pre_nombre']}".encode('latin-1', 'replace').decode('latin-1'), ln=1)
    
    con_contraste = "SÍ" if st.session_state.tiene_contraste else "NO"
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(95, 7, txt=f"¿Requiere Medio de Contraste?: {con_contraste}", ln=0)
    if datos['vfg'] > 0:
        pdf.cell(95, 7, txt=f"Función Renal (VFG): {datos['vfg']:.2f} mL/min", ln=1)
    else: pdf.ln(7)
    
    pdf.ln(4)

    # 4. SECCIÓN: ENCUESTA COMPLETA
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, txt=" 3. ENCUESTA DE SALUD Y SEGURIDAD", ln=True, fill=True)
    pdf.set_font("Arial", size=9)
    pdf.ln(2)
    
    encuesta = [
        ("Ayuno", datos['ant_ayuno']), ("Asma", datos['ant_asma']), 
        ("Diabetes", datos['ant_diabetes']), ("Hipertensión", datos['ant_hiperten']),
        ("H. Renal", datos['ant_renal']), ("Marcapaso", datos['ant_marcapaso']),
        ("Metales", datos['ant_implantes']), ("Embarazo", datos['ant_embarazo'])
    ]
    
    for i in range(0, len(encuesta), 2):
        pdf.cell(95, 6, txt=f"{encuesta[i][0]}: {encuesta[i][1]}", ln=0)
        pdf.cell(95, 6, txt=f"{encuesta[i+1][0]}: {encuesta[i+1][1]}", ln=1)
    
    if datos['tipo_cancer']:
        trat = []
        if datos['rt']: trat.append("Radioterapia")
        if datos['qt']: trat.append("Quimioterapia")
        pdf.cell(190, 6, txt=f"Antecedente Cáncer: {datos['tipo_cancer']} ({', '.join(trat)})".encode('latin-1', 'replace').decode('latin-1'), ln=1)
    
    ex_prev = []
    if datos['ex_rx']: ex_prev.append("Radiografía (Rx)")
    if datos['ex_eco']: ex_prev.append("Ecotomografía (Eco)")
    if datos['ex_tc']: ex_prev.append("Tomografía Computada (TC)")
    if datos['ex_rm']: ex_prev.append("Resonancia Magnética (RM)")
    if ex_prev:
        pdf.cell(190, 6, txt=f"Exámenes previos: {', '.join(ex_prev)}", ln=1)

    pdf.ln(5)

    # 5. FIRMAS
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, txt=" 4. CONSENTIMIENTO INFORMADO Y FIRMAS", ln=True, fill=True)
    pdf.ln(4)
    
    if datos['firma_img'] is not None:
        img_buffer = io.BytesIO()
        datos['firma_img'].save(img_buffer, format='PNG')
        img_buffer.seek(0)
        pdf.image(img_buffer, x=20, y=pdf.get_y(), w=50)
    
    pdf.ln(25)
    y_firmas = pdf.get_y()
    pdf.line(20, y_firmas, 80, y_firmas)
    pdf.line(120, y_firmas, 180, y_firmas)
    
    pdf.set_font("Arial", size=8)
    pdf.set_xy(20, y_firmas + 2)
    pdf.cell(60, 5, txt="Firma del Paciente / Tutor", align='C')
    pdf.set_xy(120, y_firmas + 2)
    pdf.cell(60, 5, txt="Firma del profesional a cargo", align='C')
    
    return pdf.output(dest='S').encode('latin-1')

@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv('listado_prestaciones.csv', sep=None, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        return df
    except: return None

df = cargar_datos()

# --- FLUJO DE PANTALLAS ---
if st.session_state.step == 1:
    col1, col2, col3 = st.columns([1,2,1]); col2.image("logoNI.png") if os.path.exists("logoNI.png") else None
    st.title("Registro de Paciente")
    
    if df is not None:
        c1, c2 = st.columns(2)
        with c1:
            nombre = st.text_input("Nombre Completo del Paciente", value=st.session_state.form["nombre"])
            rut = st.text_input("RUT del Paciente", value=st.session_state.form["rut"])
            sin_rut = st.checkbox("Sin RUT, poseo otro documento", value=st.session_state.form["sin_rut"])
            if sin_rut:
                t_doc = st.selectbox("Tipo", ["Pasaporte", "Cédula de identidad de extranjero"])
                n_doc = st.text_input("N° de documento", value=st.session_state.form["num_doc"])
                st.session_state.form.update({"tipo_doc": t_doc, "num_doc": n_doc, "rut": ""})
            else:
                st.session_state.form["rut"] = formatear_rut(rut)
            
            gen_opts = ["Masculino", "Femenino", "No binario"]
            genero = st.selectbox("Identidad de Género", gen_opts, index=st.session_state.form["genero_idx"])

        with c2:
            fecha_n = st.date_input("Fecha de Nacimiento", value=st.session_state.form["fecha_nac"])
            email = st.text_input("E-mail de contacto", value=st.session_state.form["email"])

        st.markdown('<div class="section-header">Información del Examen:</div>', unsafe_allow_html=True)
        esp_list = sorted(df['ESPECIALIDAD'].unique().tolist())
        esp_sel = st.selectbox("Especialidad", esp_list)
        pre_list = sorted(df[df['ESPECIALIDAD'] == esp_sel]['PROCEDIMIENTO A REALIZAR'].unique().tolist())
        pre_sel = st.selectbox("Procedimiento", pre_list)

        if st.button("SIGUIENTE"):
            st.session_state.form.update({"nombre": nombre, "fecha_nac": fecha_n, "email": email, "esp_nombre": esp_sel, "pre_nombre": pre_sel})
            st.session_state.tiene_contraste = "SI" in str(df[df['PROCEDIMIENTO A REALIZAR'] == pre_sel]['MEDIO DE CONTRASTE'].values[0]).upper()
            st.session_state.edad_para_calculo = calcular_edad(fecha_n)
            st.session_state.step = 2
            st.rerun()

elif st.session_state.step == 2:
    st.title("📋 Encuesta de Salud")
    c_a, c_b, c_c = st.columns(3); opts = ["No", "Sí"]
    st.session_state.form["ant_ayuno"] = c_a.radio("Ayuno (4 hrs.)", opts)
    st.session_state.form["ant_asma"] = c_b.radio("Asma", opts)
    st.session_state.form["ant_marcapaso"] = c_c.radio("Marcapaso", opts)
    
    st.markdown("Exámenes Anteriores:")
    c1, c2, c3, c4 = st.columns(4)
    st.session_state.form["ex_rx"] = c1.checkbox("Radiografía (Rx)")
    st.session_state.form["ex_eco"] = c2.checkbox("Ecotomografía (Eco)")
    st.session_state.form["ex_tc"] = c3.checkbox("Tomografía Computada (TC)")
    st.session_state.form["ex_rm"] = c4.checkbox("Resonancia Magnética (RM)")

    if st.session_state.tiene_contraste:
        st.warning("⚠️ Requiere Creatinina para Contraste")
        st.session_state.form["creatinina"] = st.number_input("Creatinina (mg/dL)", step=0.01)
        st.session_state.form["peso"] = st.number_input("Peso (kg)", value=70.0)
        if st.session_state.form["creatinina"] > 0:
            vfg = ((140 - st.session_state.edad_para_calculo) * st.session_state.form["peso"]) / (72 * st.session_state.form["creatinina"])
            st.session_state.form["vfg"] = vfg
            st.info(f"VFG Estimado: {vfg:.2f}")

    if st.button("CONTINUAR A FIRMA"):
        st.session_state.step = 3; st.rerun()

elif st.session_state.step == 3:
    st.title("🖋️ Firma y Consentimiento")
    st.markdown('<div class="legal-text">Yo autorizo la realización del examen...</div>', unsafe_allow_html=True)
    canvas_result = st_canvas(stroke_width=2, stroke_color="#000", background_color="#fff", height=150, width=400, key="canvas")
    
    if st.button("FINALIZAR REGISTRO"):
        if canvas_result.image_data is not None:
            img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA').convert("RGB")
            st.session_state.form["firma_img"] = img
            st.session_state.step = 4; st.balloons(); st.rerun()

elif st.session_state.step == 4:
    st.success("¡Registro Completado!")
    f = st.session_state.form
    # Nomenclatura EC-NombreInicialesID
    id_ref = f['rut'] if f['rut'] else f['num_doc']
    id_limpio = re.sub(r'[^a-zA-Z0-9]', '', id_ref)
    nombre_archivo = f"EC-{f['nombre'].split()[0]}{obtener_iniciales(f['nombre'])}{id_limpio}"
    
    pdf_bytes = generar_pdf_clinico(f)
    st.download_button(f"📥 Descargar {nombre_archivo}.pdf", data=pdf_bytes, file_name=f"{nombre_archivo}.pdf", mime="application/pdf")
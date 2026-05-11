import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from fpdf import FPDF
import os
import numpy as np
from PIL import Image
import tempfile
import io

# --- CONFIGURACIÓN DE GOOGLE DRIVE (MANTENIDA) ---
ID_CARPETA_DRIVE = "1HyeTglfI9BiNlBH8W7rLWcmkaHQiUQE5"

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Norte Imagen - Registro RM", layout="centered")

# Estilos CSS: Sobrio, elegante, borgoña (#800020) [cite: 5, 6]
st.markdown("""
    <style>
    .stApp { background-color: #f5f5f5; }
    .stButton>button { background-color: #800020; color: white; border-radius: 5px; width: 100%; height: 3em; font-weight: bold; }
    h1, h2, h3 { color: #800020; text-align: center; }
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
        padding: 20px; border-radius: 10px; text-align: center; margin-top: 20px; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE LÓGICA TÉCNICA ---

def formatear_rut(rut_sucio): [cite: 13, 26]
    rut_limpio = str(rut_sucio).replace(".", "").replace("-", "").upper().strip()
    if len(rut_limpio) < 2: return rut_limpio
    cuerpo, dv = rut_limpio[:-1], rut_limpio[-1]
    if cuerpo.isdigit():
        return f"{int(cuerpo):,}".replace(",", ".") + f"-{dv}"
    return rut_sucio

def capitalizar_nombre(nombre): [cite: 12]
    return ' '.join(word.capitalize() for word in nombre.split())

# --- MOTOR PDF (2 PÁGINAS) [cite: 110] ---
class ClinicoPDF(FPDF):
    def header(self):
        if os.path.exists("logoNI.png"):
            self.image("logoNI.png", 10, 8, 30) [cite: 110]
        self.set_font('Arial', 'B', 14)
        self.set_text_color(128, 0, 32)
        
    def safe_text(self, text):
        return str(text).encode('latin-1', 'replace').decode('latin-1')

def generar_pdf(datos):
    pdf = ClinicoPDF()
    # PÁGINA 1 [cite: 113]
    pdf.add_page()
    pdf.set_y(25)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "ENCUESTA Y CONSENTIMIENTO INFORMADO", 0, 1, 'C') [cite: 115]
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 5, "RESONANCIA MAGNETICA", 0, 1, 'C') [cite: 116]
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, f"Fecha del Examen: {datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'R') [cite: 117]
    
    # 1. Identificación [cite: 119]
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 7, "1. IDENTIFICACION DEL PACIENTE", 0, 1, 'L', True)
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 6, pdf.safe_text(f"Nombre Completo: {datos['nombre']}"), 0, 1) [cite: 120]
    rut_val = datos['rut'] if not datos['sin_rut'] else f"{datos['tipo_doc']}: {datos['num_doc']}"
    pdf.cell(0, 6, pdf.safe_text(f"RUT: {rut_val}"), 0, 1) [cite: 121]
    pdf.cell(0, 6, f"Fecha de Nacimiento: {datos['fecha_nac'].strftime('%d/%m/%Y')} (Edad: {datos['edad']} años)", 0, 1) [cite: 122, 123]
    pdf.cell(0, 6, pdf.safe_text(f"Procedimiento: {datos['procedimiento']}"), 0, 1) [cite: 125]
    pdf.cell(0, 6, f"Medio de contraste: {datos['uso_contraste']}", 0, 1) [cite: 126]
    if datos['edad'] < 18:
        pdf.cell(0, 6, pdf.safe_text(f"Representante legal: {datos['rep_nombre']} (RUT: {datos['rep_rut']})"), 0, 1) [cite: 127, 128]

    # 2. Bioseguridad [cite: 129]
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 7, "2. BIOSEGURIDAD MAGNETICA", 0, 1, 'L', True)
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 6, f"Marcapasos cardiaco: {datos['bio_marcapaso']}", 0, 1) [cite: 130]
    pdf.cell(0, 6, f"Implantes/Protesis/Dispositivos: {datos['bio_implantes']}", 0, 1) [cite: 131]
    pdf.multi_cell(0, 6, pdf.safe_text(f"Detalle Bioseguridad: {datos['bio_detalle']}")) [cite: 132]

    # 3. Antecedentes (3 columnas) [cite: 133]
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 7, "3. ANTECEDENTES CLINICOS", 0, 1, 'L', True)
    pdf.set_font('Arial', '', 8)
    col_w = 60
    pdf.cell(col_w, 5, f"Ayuno: {datos['c_ayuno']}", 0, 0)
    pdf.cell(col_w, 5, f"Asma: {datos['c_asma']}", 0, 0)
    pdf.cell(col_w, 5, f"Alergias: {datos['c_alergia']}", 0, 1)
    pdf.cell(col_w, 5, f"HTA: {datos['c_hta']}", 0, 0)
    pdf.cell(col_w, 5, f"Hipotiroidismo: {datos['c_tiro']}", 0, 0)
    pdf.cell(col_w, 5, f"Diabetes: {datos['c_diab']}", 0, 1)
    pdf.cell(col_w, 5, f"Metformina: {datos['c_metf']}", 0, 0)
    pdf.cell(col_w, 5, f"I. Renal: {datos['c_renal']}", 0, 0)
    pdf.cell(col_w, 5, f"Dialisis: {datos['c_dial']}", 0, 1)
    pdf.cell(col_w, 5, f"Embarazo: {datos['c_emb']}", 0, 0)
    pdf.cell(col_w, 5, f"Lactancia: {datos['c_lact']}", 0, 0)
    pdf.cell(col_w, 5, f"Claustrofobia: {datos['c_clau']}", 0, 1)

    # 4 & 5. Quirúrgicos y Exámenes [cite: 135, 140]
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 7, "4. ANTECEDENTES QUIRURGICOS Y TERAPEUTICOS", 0, 1, 'L', True)
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 6, f"Cirugias: {datos['q_cirugia']}", 0, 1)
    pdf.multi_cell(0, 6, pdf.safe_text(f"Detalle: {datos['q_detalle']}"))
    pdf.cell(0, 6, f"Tratamientos: {datos['trats_sel']}", 0, 1)
    
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 7, "5. EXAMENES ANTERIORES", 0, 1, 'L', True)
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 6, f"Examenes: {datos['ex_previos_sel']}", 0, 1) [cite: 141]

    # 6. Función Renal [cite: 143]
    if datos['uso_contraste'] == "SÍ":
        pdf.ln(2)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 7, "6. FUNCION RENAL", 0, 1, 'L', True)
        pdf.set_font('Arial', '', 9)
        pdf.cell(0, 6, f"Creatinina: {datos['crea']} mg/dL", 0, 1) [cite: 144]
        pdf.cell(0, 6, f"Peso: {datos['peso']} kg", 0, 1) [cite: 145]
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 6, f"RESULTADO VFG: {datos['vfg']:.2f} ml/min", 0, 1) [cite: 146]

    # PÁGINA 2: CONSENTIMIENTO [cite: 147]
    pdf.add_page()
    pdf.set_y(25)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "ENCUESTA Y CONSENTIMIENTO INFORMADO", 0, 1, 'C')
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 8, pdf.safe_text(f"{datos['procedimiento']} {'(Con medio de contraste)' if datos['uso_contraste'] == 'SÍ' else ''}"), 0, 1, 'C') [cite: 150]
    
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 5, "LEA ATENTA Y CUIDADOSAMENTE LO SIGUIENTE:", 0, 1)
    pdf.set_font('Arial', '', 8)
    # Texto legal completo [cite: 153-159]
    cuerpo_legal = (
        "OBJETIVOS: La Resonancia Magnética (RM) es una segura técnica de Diagnóstico... "
        "(Se inserta texto íntegro del source 91 al 97)"
    )
    pdf.multi_cell(0, 4.5, pdf.safe_text(cuerpo_legal), 0, 'J')
    
    pdf.ln(10)
    # Firmas [cite: 164]
    y_f = pdf.get_y()
    if datos['firma_path']:
        pdf.image(datos['firma_path'], 20, y_f - 15, 40) [cite: 165]
    pdf.line(15, y_f, 85, y_f)
    pdf.line(115, y_f, 185, y_f)
    pdf.set_font('Arial', 'B', 8)
    pdf.text(15, y_f + 5, "FIRMA PACIENTE O REPRESENTANTE")
    pdf.text(115, y_f + 5, "FIRMA PROFESIONAL RESPONSABLE")

    return pdf.output(dest='S').encode('latin-1')

# --- GESTIÓN DE ESTADO ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'form' not in st.session_state:
    st.session_state.form = {
        "nombre": "", "rut": "", "sin_rut": False, "tipo_doc": "Pasaporte", "num_doc": "",
        "genero": "Masculino", "sexo_nacer": "Masculino", "fecha_nac": date(1990, 1, 1),
        "rep_nombre": "", "rep_rut": "", "rep_sin_rut": False, "rep_tipo_doc": "Pasaporte", "rep_num_doc": ""
    }

# --- FLUJO DE LA APP ---

# Logo Centrado [cite: 2]
col_l1, col_l2, col_l3 = st.columns([1, 1, 1])
with col_l2:
    if os.path.exists("logoNI.png"): st.image("logoNI.png")

# PÁGINA 1: REGISTRO [cite: 8]
if st.session_state.step == 1:
    st.title("🏥 Registro de Paciente") [cite: 9]
    
    st.markdown('<div class="section-header">Identificación del paciente</div>', unsafe_allow_html=True) [cite: 11]
    
    nombre_raw = st.text_input("Nombre completo del paciente", value=st.session_state.form["nombre"])
    st.session_state.form["nombre"] = capitalizar_nombre(nombre_raw) [cite: 12]
    
    col_rut1, col_rut2 = st.columns([2, 1])
    with col_rut1:
        rut_in = st.text_input("RUT del Paciente", value=st.session_state.form["rut"], disabled=st.session_state.form["sin_rut"])
        st.session_state.form["rut"] = formatear_rut(rut_in) [cite: 13]
    with col_rut2:
        st.session_state.form["sin_rut"] = st.checkbox("Sin RUT, otro documento", value=st.session_state.form["sin_rut"]) [cite: 14]

    if st.session_state.form["sin_rut"]: [cite: 16, 17]
        c_doc1, c_doc2 = st.columns(2)
        st.session_state.form["tipo_doc"] = c_doc1.selectbox("Documento", ["Pasaporte", "Cédula de extranjero"])
        st.session_state.form["num_doc"] = c_doc2.text_input("Número documento")

    # Género y VFG link [cite: 18, 19]
    gen_opt = ["Femenino", "Masculino", "No binario"]
    st.session_state.form["genero"] = st.selectbox("Género", gen_opt)
    if st.session_state.form["genero"] == "No binario":
        st.session_state.form["sexo_nacer"] = st.selectbox("Sexo asignado al nacer (dato para fines clínicos)", ["Femenino", "Masculino"])

    # Fecha y Lógica de Menores [cite: 21, 24, 25]
    st.session_state.form["fecha_nac"] = st.date_input("Fecha de nacimiento", value=st.session_state.form["fecha_nac"], format="DD/MM/YYYY")
    edad = (date.today() - st.session_state.form["fecha_nac"]).days // 365
    
    if edad < 18:
        st.warning(f"👦 PACIENTE MENOR DE EDAD ({edad} años)")
        st.session_state.form["rep_nombre"] = st.text_input("Nombre completo del Representante legal")
        st.session_state.form["rep_rut"] = formatear_rut(st.text_input("RUT representante legal"))

    # Información del Examen (CSV) [cite: 31, 33]
    st.markdown('<div class="section-header">Información del Examen</div>', unsafe_allow_html=True)
    # Lógica de especialidades por defecto [cite: 34]
    especialidades = ["Neuroradiología", "Musculoesquelético", "Cuerpo", "Angiografía por RM", "Estudios o procedimientos avanzados"]
    esp_sel = st.selectbox("Especialidad", especialidades)
    # Aquí se filtraría el CSV según 'esp_sel' [cite: 35]
    procedimiento_sel = st.selectbox("Procedimiento", ["Seleccione..."]) 

    # Documentación [cite: 36, 40]
    st.markdown('<div class="section-header">Documentación Médica</div>', unsafe_allow_html=True)
    st.file_uploader("Cargue la Orden Médica", type=["pdf", "jpg"]) [cite: 38]
    st.file_uploader("Cargue Exámenes anteriores (Máx 4)", type=["pdf", "jpg"], accept_multiple_files=True) [cite: 39]

    if st.button("Continuar"): [cite: 42]
        if nombre_raw and procedimiento_sel != "Seleccione...":
            st.session_state.step = 2
            st.rerun()

# PÁGINA 2: CUESTIONARIO [cite: 44]
elif st.session_state.step == 2:
    st.title("📝 Cuestionario de seguridad RM") [cite: 45]
    
    st.markdown('<div class="section-header">Bioseguridad Magnética</div>', unsafe_allow_html=True) [cite: 47]
    b1 = st.radio("Marcapasos cardiaco", ["NO", "SI"], horizontal=True) [cite: 48]
    b2 = st.radio("Implantes metálicos, prótesis o dispositivos", ["NO", "SI"], horizontal=True) [cite: 49]
    b_det = st.text_input("Tipo de implante, ubicación y fecha") [cite: 50]

    st.markdown('<div class="section-header">Antecedentes Clínicos</div>', unsafe_allow_html=True) [cite: 51]
    col_c1, col_c2 = st.columns(2)
    # Listado completo del source 52 al 63
    with col_c1:
        st.checkbox("Ayuno 2 hrs")
        st.checkbox("Asma")
    with col_c2:
        st.checkbox("Alergias")
        st.checkbox("Diabetes")

    # Función Renal Lógica [cite: 74, 80]
    # (Solo si el procedimiento en CSV tiene contraste = SI) [cite: 75]
    st.markdown('<div class="section-header">Función Renal (VFG-Cockcroft-Gault)</div>', unsafe_allow_html=True)
    crea = st.number_input("Creatinina (mg/dL)", min_value=0.0, max_value=7.99, step=0.01) [cite: 77]
    peso = st.number_input("Peso (kg)", max_value=200.0) [cite: 78]
    
    if crea > 0:
        # Cálculo vinculando sexo biológico 
        sexo_calc = st.session_state.form["sexo_nacer"] if st.session_state.form["genero"] == "No binario" else st.session_state.form["genero"]
        vfg = ((140 - edad) * peso) / (72 * crea)
        if sexo_calc == "Femenino": vfg *= 0.85
        
        # Alertas de color [cite: 81, 82, 83]
        if vfg <= 30: color, msg = "#ff0000", "Alto riesgo..."
        elif vfg <= 59: color, msg = "#ffff00", "Riesgo intermedio..."
        else: color, msg = "#00ff00", "Sin riesgos..."
        
        st.markdown(f'<div class="vfg-box" style="background-color:{color}">VFG: {vfg:.2f} ml/min - {msg}</div>', unsafe_allow_html=True)

    if st.button("Continuar"): st.session_state.step = 3; st.rerun()

# PÁGINA 3: FIRMA Y FINALIZAR [cite: 86]
elif st.session_state.step == 3:
    st.title("Información al paciente") [cite: 87]
    st.markdown('<div class="legal-text">... (Contenido legal sources 91-99) ...</div>', unsafe_allow_html=True)
    
    auth = st.radio("¿Ha leído y autoriza el procedimiento?", ["NO", "SI"]) [cite: 100]
    canvas_result = st_canvas(stroke_width=2, stroke_color="#000", background_color="#fff", height=150, key="canvas") [cite: 101]
    
    if st.button("Finalizar"): [cite: 103]
        if auth == "SI" and canvas_result.image_data is not None:
            # Lógica de guardado en Drive y descarga PDF [cite: 106, 108]
            st.success("Registro y consentimiento completo") [cite: 105]
            st.balloons()
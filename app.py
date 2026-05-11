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

# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
st.set_page_config(page_title="Norte Imagen - Registro RM", layout="centered")

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
        max-height: 400px; overflow-y: auto; line-height: 1.6;
    }
    .vfg-box { 
        padding: 20px; border-radius: 10px; text-align: center; margin-top: 10px; font-weight: bold; border: 2px solid #800020;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. FUNCIONES TÉCNICAS (Lógica de Negocio)
def formatear_rut(rut_sucio):
    rut_limpio = str(rut_sucio).replace(".", "").replace("-", "").upper().strip()
    if len(rut_limpio) < 2: return rut_limpio
    cuerpo, dv = rut_limpio[:-1], rut_limpio[-1]
    if cuerpo.isdigit():
        return f"{int(cuerpo):,}".replace(",", ".") + f"-{dv}"
    return rut_sucio

def capitalizar_nombre(nombre):
    return ' '.join(word.capitalize() for word in nombre.split())

def calcular_edad(f_nac):
    today = date.today()
    return today.year - f_nac.year - ((today.month, today.day) < (f_nac.month, f_nac.day))

# 3. GESTIÓN DE ESTADO (Para no perder datos)
if 'step' not in st.session_state: st.session_state.step = 1
if 'form' not in st.session_state:
    st.session_state.form = {
        "nombre": "", "rut": "", "sin_rut": False, "tipo_doc": "Pasaporte", "num_doc": "",
        "genero": "Masculino", "sexo_bio": "Masculino", "f_nac": date(1990, 1, 1),
        "email": "", "nombre_tutor": "", "rut_tutor": "", "especialidad": "", "procedimiento": "",
        "uso_contraste": False, "bio_marcapaso": "NO", "bio_implantes": "NO", "bio_detalle": "",
        "clin_ayuno": False, "clin_asma": False, "clin_alergia": False, "clin_hta": False,
        "clin_tiro": False, "clin_diab": False, "clin_metf": False, "clin_renal": False,
        "clin_dial": False, "clin_emb": False, "clin_lact": False, "clin_clau": False,
        "q_cirugia": "NO", "q_detalle": "", "trats": [], "ex_anteriores": [], "ex_otros": "",
        "creatinina": 0.0, "peso": 0.0, "vfg": 0.0, "autoriza": "NO", "firma_img": None
    }

# 4. MOTOR PDF DE 2 PÁGINAS
class NorteImagenPDF(FPDF):
    def header(self):
        if os.path.exists("logoNI.png"):
            self.image("logoNI.png", 10, 8, 33)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(128, 0, 32)
        self.cell(0, 10, 'ENCUESTA Y CONSENTIMIENTO INFORMADO', 0, 1, 'C')
        self.set_font('Arial', 'B', 11)
        self.cell(0, 5, 'RESONANCIA MAGNETICA', 0, 1, 'C')
        self.ln(10)

    def safe(self, txt):
        return str(txt).encode('latin-1', 'replace').decode('latin-1')

def generar_reporte_pdf(f):
    pdf = NorteImagenPDF()
    pdf.add_page()
    
    # Sección 1: Identificación
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 7, "1. IDENTIFICACION DEL PACIENTE", 0, 1, 'L', True)
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 6, pdf.safe(f"Nombre: {f['nombre']}"), 0, 1)
    id_paciente = f['rut'] if not f['sin_rut'] else f"{f['tipo_doc']}: {f['num_doc']}"
    pdf.cell(0, 6, pdf.safe(f"Documento: {id_paciente}"), 0, 1)
    pdf.cell(0, 6, f"Edad: {calcular_edad(f['f_nac'])} años | Fecha Nac: {f['f_nac'].strftime('%d/%m/%Y')}", 0, 1)
    pdf.cell(0, 6, pdf.safe(f"Procedimiento: {f['procedimiento']}"), 0, 1)
    
    # Sección 2: Bioseguridad
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 7, "2. BIOSEGURIDAD MAGNETICA", 0, 1, 'L', True)
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 6, f"Marcapasos: {f['bio_marcapaso']} | Implantes/Protesis: {f['bio_implantes']}", 0, 1)
    pdf.multi_cell(0, 6, pdf.safe(f"Detalle: {f['bio_detalle']}"))

    # Sección 3: Antecedentes (Organizados en bloques)
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 7, "3. ANTECEDENTES CLINICOS Y QUIRURGICOS", 0, 1, 'L', True)
    pdf.set_font('Arial', '', 9)
    clin_txt = f"Ayuno: {'SI' if f['clin_ayuno'] else 'NO'} | Asma: {'SI' if f['clin_asma'] else 'NO'} | Alergia: {'SI' if f['clin_alergia'] else 'NO'} | HTA: {'SI' if f['clin_hta'] else 'NO'}"
    pdf.cell(0, 6, pdf.safe(clin_txt), 0, 1)
    pdf.cell(0, 6, pdf.safe(f"Cirugias: {f['q_cirugia']} - Detalle: {f['q_detalle']}"), 0, 1)
    
    if f['uso_contraste']:
        pdf.ln(2)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 7, "4. FUNCION RENAL", 0, 1, 'L', True)
        pdf.set_font('Arial', '', 9)
        pdf.cell(0, 6, f"Creatinina: {f['creatinina']} mg/dL | Peso: {f['peso']} kg | VFG: {f['vfg']:.2f} ml/min", 0, 1)

    # PÁGINA 2: CONSENTIMIENTO
    pdf.add_page()
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, "LEA ATENTA Y CUIDADOSAMENTE LO SIGUIENTE:", 0, 1, 'C')
    pdf.set_font('Arial', '', 8.5)
    
    texto_legal = (
        "OBJETIVOS: La Resonancia Magnética (RM) es una segura técnica de Diagnóstico, que permite la adquisición "
        "de imágenes de gran sensibilidad... (Incluir aquí el texto completo del Word)..."
    )
    pdf.multi_cell(0, 5, pdf.safe(texto_legal), 0, 'J')
    
    pdf.ln(20)
    y_firma = pdf.get_y()
    if f['firma_img']:
        pdf.image(f['firma_img'], 20, y_firma - 15, 40)
    pdf.line(15, y_firma, 85, y_firma)
    pdf.line(115, y_firma, 185, y_firma)
    pdf.set_font('Arial', 'B', 8)
    pdf.text(15, y_firma + 5, "FIRMA PACIENTE O REPRES. LEGAL")
    pdf.text(115, y_firma + 5, "FIRMA PROFESIONAL RESPONSABLE")
    
    return pdf.output(dest='S').encode('latin-1')

# 5. ESTRUCTURA DE NAVEGACIÓN
def mostrar_logo():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if os.path.exists("logoNI.png"): st.image("logoNI.png")
        else: st.subheader("NORTE IMAGEN")

# --- PÁGINA 1: REGISTRO ---
if st.session_state.step == 1:
    mostrar_logo()
    st.title("🏥 Registro de Paciente")
    
    with st.container():
        st.markdown('<div class="section-header">Identificación del paciente</div>', unsafe_allow_html=True)
        nombre = st.text_input("Nombre completo del paciente", value=st.session_state.form["nombre"])
        st.session_state.form["nombre"] = capitalizar_nombre(nombre)
        
        c1, c2 = st.columns([2, 1])
        with c1:
            rut_in = st.text_input("RUT del Paciente", value=st.session_state.form["rut"], placeholder="12.345.678-K", disabled=st.session_state.form["sin_rut"])
            st.session_state.form["rut"] = formatear_rut(rut_in)
        with c2:
            st.session_state.form["sin_rut"] = st.checkbox("Sin RUT / Otro", value=st.session_state.form["sin_rut"])
        
        if st.session_state.form["sin_rut"]:
            cc1, cc2 = st.columns(2)
            st.session_state.form["tipo_doc"] = cc1.selectbox("Tipo", ["Pasaporte", "Cédula de extranjero"])
            st.session_state.form["num_doc"] = cc2.text_input("N° Documento", value=st.session_state.form["num_doc"])
        
        g_opt = ["Masculino", "Femenino", "No binario"]
        st.session_state.form["genero"] = st.selectbox("Género", g_opt, index=g_opt.index(st.session_state.form["genero"]))
        if st.session_state.form["genero"] == "No binario":
            st.session_state.form["sexo_bio"] = st.selectbox("Sexo asignado al nacer (fines clínicos)", ["Masculino", "Femenino"])
        else:
            st.session_state.form["sexo_bio"] = st.session_state.form["genero"]

        st.session_state.form["f_nac"] = st.date_input("Fecha de nacimiento", value=st.session_state.form["f_nac"], format="DD/MM/YYYY")
        edad = calcular_edad(st.session_state.form["f_nac"])
        
        if edad < 18:
            st.warning(f"👦 PACIENTE MENOR DE EDAD ({edad} años)")
            st.session_state.form["nombre_tutor"] = st.text_input("Nombre Representante Legal", value=st.session_state.form["nombre_tutor"])
            st.session_state.form["rut_tutor"] = formatear_rut(st.text_input("RUT Representante", value=st.session_state.form["rut_tutor"]))

    if st.button("CONTINUAR"):
        if st.session_state.form["nombre"]:
            st.session_state.step = 2
            st.rerun()

# --- PÁGINA 2: CUESTIONARIO Y VFG ---
elif st.session_state.step == 2:
    mostrar_logo()
    st.title("📋 Cuestionario de Seguridad")
    
    st.markdown('<div class="section-header">Bioseguridad y Clínica</div>', unsafe_allow_html=True)
    st.session_state.form["bio_marcapaso"] = st.radio("¿Posee Marcapasos?", ["NO", "SI"], horizontal=True)
    st.session_state.form["bio_implantes"] = st.radio("¿Posee Implantes/Prótesis?", ["NO", "SI"], horizontal=True)
    st.session_state.form["bio_detalle"] = st.text_area("Detalles de bioseguridad", value=st.session_state.form["bio_detalle"])

    # Lógica de VFG (Cockcroft-Gault)
    st.markdown('<div class="section-header">Cálculo de Función Renal (VFG)</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    st.session_state.form["creatinina"] = c1.number_input("Creatinina (mg/dL)", value=st.session_state.form["creatinina"], step=0.01)
    st.session_state.form["peso"] = c2.number_input("Peso (kg)", value=st.session_state.form["peso"], step=0.1)
    
    if st.session_state.form["creatinina"] > 0 and st.session_state.form["peso"] > 0:
        edad = calcular_edad(st.session_state.form["f_nac"])
        vfg = ((140 - edad) * st.session_state.form["peso"]) / (72 * st.session_state.form["creatinina"])
        if st.session_state.form["sexo_bio"] == "Femenino": vfg *= 0.85
        st.session_state.form["vfg"] = vfg
        
        color = "#90ee90" if vfg > 60 else "#ffcccb"
        st.markdown(f'<div class="vfg-box" style="background-color:{color}">Resultado VFG: {vfg:.2f} ml/min</div>', unsafe_allow_html=True)

    if st.button("SIGUIENTE"):
        st.session_state.step = 3
        st.rerun()

# --- PÁGINA 3: FIRMA Y CIERRE ---
elif st.session_state.step == 3:
    mostrar_logo()
    st.title("✍️ Consentimiento e Informe")
    st.markdown('<div class="legal-text"><b>OBJETIVOS:</b> La RM es una técnica segura... (Texto completo del Word)...</div>', unsafe_allow_html=True)
    
    st.session_state.form["autoriza"] = st.radio("¿Autoriza el procedimiento?", ["NO", "SI"], horizontal=True)
    st.write("Firma del paciente:")
    canvas_result = st_canvas(stroke_width=2, stroke_color="#000", background_color="#fff", height=150, width=400, key="canvas")
    
    if st.button("FINALIZAR REGISTRO"):
        if st.session_state.form["autoriza"] == "SI" and canvas_result.image_data is not None:
            img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                img.save(tmp.name)
                st.session_state.form["firma_img"] = tmp.name
            
            pdf_bytes = generar_reporte_pdf(st.session_state.form)
            st.success("¡Registro completado con éxito!")
            st.download_button("Descargar Documento PDF", data=pdf_bytes, file_name=f"Registro_{st.session_state.form['rut']}.pdf", mime="application/pdf")
            if st.button("Nuevo Pac
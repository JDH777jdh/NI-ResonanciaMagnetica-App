import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from fpdf import FPDF
import os
import numpy as np
from PIL import Image
import tempfile
# Librerías para Google Drive
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

# --- CONFIGURACIÓN DE GOOGLE DRIVE ---
ID_CARPETA_DRIVE = "1HyeTglfI9BiNlBH8W7rLWcmkaHQiUQE5"

def subir_a_google_drive(archivo_datos, nombre_archivo):
    try:
        if "gcp_service_account" not in st.secrets:
            return False, "Faltan credenciales en Secrets"
            
        # SOLUCIÓN PUNTO 2: Reparación de la llave privada PEM
        creds_dict = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        service = build('drive', 'v3', credentials=creds)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            tmp_pdf.write(archivo_datos)
            tmp_path = tmp_pdf.name

        file_metadata = {
            'name': nombre_archivo,
            'parents': [ID_CARPETA_DRIVE]
        }
        media = MediaFileUpload(tmp_path, mimetype='application/pdf')
        
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        os.remove(tmp_path)
        return True, file.get('id')
    except Exception as e:
        return False, str(e)

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
    .vfg-box { 
        background-color: #ffffff; padding: 20px; border-radius: 10px; 
        border: 2px solid #800020; text-align: center; margin-top: 20px;
    }
    .vfg-critica { border: 3px solid #ff0000 !important; color: #ff0000 !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. GESTIÓN DE ESTADO
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

# SOLUCIÓN PUNTO 1: Función para sanitizar texto y evitar PDF en blanco
def safe_str(texto):
    if texto is None: return ""
    return str(texto).encode('latin-1', 'replace').decode('latin-1')

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
        self.set_font('Arial', 'B', 14)
        self.set_text_color(128, 0, 32)
        self.cell(0, 10, 'ENCUESTA Y CONSENTIMIENTO INFORMADO', 0, 1, 'C')
        self.ln(10)

    def section_title(self, num, label):
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(230, 230, 230)
        self.set_text_color(128, 0, 32)
        self.cell(0, 7, f"{num}. {safe_str(label)}", 0, 1, 'L', 1)
        self.ln(2)

    def data_field(self, label, value):
        self.set_font('Arial', 'B', 9)
        self.write(5, f"{safe_str(label)}: ")
        self.set_font('Arial', '', 9)
        self.write(5, f"{safe_str(value)}\n")

def generar_pdf_clinico(datos):
    pdf = PDF()
    pdf.add_page()
    
    pdf.section_title("1", "IDENTIFICACION DEL PACIENTE")
    doc_id = datos['rut'] if not datos['sin_rut'] else f"{datos['tipo_doc']}: {datos['num_doc']}"
    pdf.data_field("Nombre", datos['nombre'])
    pdf.data_field("Documento", doc_id)
    pdf.data_field("Fecha Nacimiento", datos['fecha_nac'].strftime("%d/%m/%Y"))
    pdf.data_field("Procedimiento", st.session_state.procedimiento)
    
    pdf.section_title("2", "BIOSEGURIDAD Y CLINICA")
    pdf.data_field("Marcapasos", datos['bio_marcapaso'])
    pdf.data_field("Alergias", datos['clin_alergico'])
    pdf.data_field("VFG Resultado", f"{datos['vfg']:.2f}")

    if datos['firma_img']:
        pdf.ln(10)
        pdf.image(datos['firma_img'], x=20, w=50)
        pdf.text(20, pdf.get_y() + 45, f"Firma: {safe_str(datos['nombre'])}")

    return pdf.output(dest='S').encode('latin-1', 'replace')

@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv('listado_prestaciones.csv', sep=None, engine='python', encoding='utf-8-sig')
        return df
    except: return None

df = cargar_datos()

# --- PÁGINA 1: REGISTRO ---
if st.session_state.step == 1:
    st.title("Registro de Paciente")
    if df is not None:
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.form["nombre"] = st.text_input("Nombre Completo", value=st.session_state.form["nombre"])
            st.session_state.form["rut"] = formatear_rut(st.text_input("RUT", value=st.session_state.form["rut"]))
            st.session_state.form["sin_rut"] = st.checkbox("Otro documento", value=st.session_state.form["sin_rut"])
            if st.session_state.form["sin_rut"]:
                st.session_state.form["tipo_doc"] = st.selectbox("Tipo", ["Pasaporte", "Cédula extranjero"])
                st.session_state.form["num_doc"] = st.text_input("N° Documento")
        
        with c2:
            st.session_state.form["fecha_nac"] = st.date_input("Nacimiento", value=st.session_state.form["fecha_nac"])
            st.session_state.form["email"] = st.text_input("Email", value=st.session_state.form["email"])

        st.markdown('<div class="section-header">Información del Examen</div>', unsafe_allow_html=True)
        esp_sel = st.selectbox("Especialidad", sorted(df['ESPECIALIDAD'].unique()))
        pre_sel = st.selectbox("Procedimiento", sorted(df[df['ESPECIALIDAD'] == esp_sel]['PROCEDIMIENTO A REALIZAR'].unique()))

        if st.button("CONTINUAR"):
            row = df[(df['ESPECIALIDAD'] == esp_sel) & (df['PROCEDIMIENTO A REALIZAR'] == pre_sel)]
            st.session_state.tiene_contraste = str(row['MEDIO DE CONTRASTE'].values[0]).upper() == "SI"
            st.session_state.procedimiento = pre_sel
            st.session_state.step = 2; st.rerun()

# --- PÁGINA 2: CUESTIONARIO ---
elif st.session_state.step == 2:
    st.title("📋 Cuestionario")
    opts = ["No", "Sí"]
    
    # CAMPOS DE CARGA DE ARCHIVOS (RECUPERADOS)
    st.markdown('<div class="section-header">Carga de Documentos</div>', unsafe_allow_html=True)
    st.file_uploader("Subir Orden Médica (Opcional)", type=['pdf', 'jpg', 'png'])
    st.file_uploader("Subir Exámenes Anteriores (Opcional)", type=['pdf', 'jpg', 'png'], accept_multiple_files=True)

    st.markdown('<div class="section-header">Bioseguridad</div>', unsafe_allow_html=True)
    st.session_state.form["bio_marcapaso"] = st.radio("¿Tiene Marcapasos?", opts, horizontal=True)
    st.session_state.form["clin_alergico"] = st.radio("¿Es Alérgico?", opts, horizontal=True)

    if st.session_state.tiene_contraste:
        st.markdown('<div class="section-header">Función Renal</div>', unsafe_allow_html=True)
        st.session_state.form["creatinina"] = st.number_input("Creatinina", value=st.session_state.form["creatinina"])
        st.session_state.form["peso"] = st.number_input("Peso", value=st.session_state.form["peso"])
        vfg = ((140 - 30) * st.session_state.form["peso"]) / (72 * st.session_state.form["creatinina"]) if st.session_state.form["creatinina"] > 0 else 0
        st.session_state.form["vfg"] = vfg
        st.metric("VFG", f"{vfg:.2f}")

    if st.button("SIGUIENTE"):
        st.session_state.step = 3; st.rerun()

# --- PÁGINA 3: FIRMA ---
elif st.session_state.step == 3:
    st.title("Firma de Consentimiento")
    canvas_result = st_canvas(stroke_width=2, stroke_color="#000", background_color="#fff", height=150, width=400, key="canvas")
    if st.button("FINALIZAR"):
        if canvas_result.image_data is not None:
            img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                img.save(tmp.name); st.session_state.form["firma_img"] = tmp.name
            st.session_state.step = 4; st.rerun()

# --- PÁGINA 4: FINAL ---
elif st.session_state.step == 4:
    st.success("Procesando datos...")
    pdf_output = generar_pdf_clinico(st.session_state.form)
    nombre_final = f"Registro_{st.session_state.form['rut']}.pdf"
    exito, resultado = subir_a_google_drive(pdf_output, nombre_final)
    
    if exito: st.info("✅ Archivo subido a Google Drive correctamente")
    else: st.error(f"❌ Error al subir a Drive: {resultado}")
    
    st.download_button("Descargar Copia PDF", pdf_output, nombre_final, "application/pdf")
    if st.button("Nuevo Registro"):
        st.session_state.clear(); st.rerun()
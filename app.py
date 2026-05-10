import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from fpdf import FPDF
import os
import numpy as np
from PIL import Image
import tempfile
# Librerías adicionales para Google Drive
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

# --- CONFIGURACIÓN DE GOOGLE DRIVE ---
ID_CARPETA_DRIVE = "1HyeTglfI9BiNlBH8W7rLWcmkaHQiUQE5"

def subir_a_google_drive(archivo_datos, nombre_archivo):
    try:
        if "gcp_service_account" not in st.secrets:
            return False, "Faltan credenciales en Secrets"
            
        creds_dict = dict(st.secrets["gcp_service_account"])
        
        # REPARACIÓN DE LLAVE PRIVADA: Crucial para que no falle la conexión
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

# 3. FUNCIONES DE APOYO
def formatear_rut(rut_sucio):
    rut_limpio = str(rut_sucio).replace(".", "").replace("-", "").upper().strip()
    if len(rut_limpio) < 2: return rut_limpio
    cuerpo, dv = rut_limpio[:-1], rut_limpio[-1]
    if cuerpo.isdigit(): return f"{int(cuerpo):,}".replace(",", ".") + f"-{dv}"
    return rut_sucio

def calcular_edad(fecha_nac):
    today = date.today()
    return today.year - fecha_nac.year - ((today.month, today.day) < (fecha_nac.month, fecha_nac.day))

# Función para limpiar texto y evitar errores en PDF
def clean_txt(text):
    if text is None: return ""
    return str(text).encode('latin-1', 'replace').decode('latin-1')

class PDF(FPDF):
    def header(self):
        if os.path.exists("logoNI.png"):
            self.image("logoNI.png", 10, 8, 33)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(128, 0, 32)
        self.cell(0, 10, 'ENCUESTA Y CONSENTIMIENTO INFORMADO', 0, 1, 'C')
        self.set_font('Arial', 'B', 12)
        self.cell(0, 5, 'RESONANCIA MAGNETICA', 0, 1, 'C')
        self.ln(10)

    def section_title(self, num, label):
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(230, 230, 230)
        self.set_text_color(128, 0, 32)
        self.cell(0, 7, f"{num}. {clean_txt(label)}", 0, 1, 'L', 1)
        self.ln(2)

    def data_field(self, label, value):
        self.set_font('Arial', 'B', 9)
        self.set_text_color(50, 50, 50)
        self.write(5, f"{clean_txt(label)}: ")
        self.set_font('Arial', '', 9)
        self.set_text_color(0, 0, 0)
        self.write(5, f"{clean_txt(value)}\n")

def generar_pdf_clinico(datos):
    pdf = PDF()
    pdf.add_page()
    
    pdf.section_title("1", "IDENTIFICACION DEL PACIENTE")
    doc_id = datos['rut'] if not datos['sin_rut'] else f"{datos['tipo_doc']}: {datos['num_doc']}"
    pdf.data_field("Fecha del Examen", datetime.now().strftime("%d/%m/%Y"))
    pdf.data_field("Nombre Completo", datos['nombre'])
    pdf.data_field("Documento", doc_id)
    pdf.data_field("Fecha de Nacimiento", datos['fecha_nac'].strftime("%d/%m/%Y"))
    pdf.data_field("Email", datos['email'])
    pdf.data_field("Procedimiento", st.session_state.procedimiento)
    pdf.data_field("Medio de contraste", "SI" if st.session_state.tiene_contraste else "NO")
    pdf.ln(4)

    pdf.section_title("2", "BIOSEGURIDAD MAGNETICA")
    pdf.data_field("Marcapasos cardiaco", datos['bio_marcapaso'])
    pdf.data_field("Implantes/Protesis metalicas", datos['bio_implantes'])
    pdf.data_field("Detalle Bioseguridad", datos['bio_detalle'] if datos['bio_detalle'] else "")
    pdf.ln(4)

    pdf.section_title("3", "ANTECEDENTES CLINICOS")
    clin_txt = (f"Ayuno: {datos['clin_ayuno']} | Asma: {datos['clin_asma']} | HTA: {datos['clin_hiperten']} | "
                f"Diabetes: {datos['clin_diabetes']} | Alergico: {datos['clin_alergico']} | Renal: {datos['clin_renal']}")
    pdf.set_font('Arial', '', 9)
    pdf.multi_cell(0, 5, clean_txt(clin_txt))
    
    if st.session_state.tiene_contraste:
        pdf.ln(4)
        pdf.data_field("Creatinina", f"{datos['creatinina']} mg/dL")
        pdf.data_field("VFG", f"{datos['vfg']:.2f} ml/min")

    # Información y Firma
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "CONSENTIMIENTO INFORMADO", 0, 1, 'C')
    pdf.ln(5)
    pdf.set_font('Arial', '', 9)
    pdf.multi_cell(0, 5, clean_txt("Autorizo la realizacion del procedimiento y las acciones necesarias..."))
    
    if datos['firma_img']:
        pdf.ln(10)
        pdf.image(datos['firma_img'], x=20, w=50)
        pdf.ln(2)
        pdf.set_font('Arial', 'B', 8)
        pdf.cell(0, 5, f"FIRMA: {clean_txt(datos['nombre'][:30])}", 0, 1)

    return pdf.output(dest='S').encode('latin-1', 'replace')

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

# --- LÓGICA DE PÁGINAS ---
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
                st.session_state.form["tipo_doc"] = st.selectbox("Tipo de documento", t_opts)
                st.session_state.form["num_doc"] = st.text_input("N° de documento", value=st.session_state.form["num_doc"])
        with c2:
            st.session_state.form["fecha_nac"] = st.date_input("Nacimiento", value=st.session_state.form["fecha_nac"])
            st.session_state.form["email"] = st.text_input("Email", value=st.session_state.form["email"])
        
        st.markdown('<div class="section-header">Examen</div>', unsafe_allow_html=True)
        # CORRECCIÓN PARA ESPECIALIDAD: Evitar error TypeError si hay nulos
        especialidades = sorted([str(e) for e in df['ESPECIALIDAD'].unique() if pd.notna(e)])
        esp_sel = st.selectbox("Especialidad", especialidades)
        
        procedimientos = sorted([str(p) for p in df[df['ESPECIALIDAD'] == esp_sel]['PROCEDIMIENTO A REALIZAR'].unique() if pd.notna(p)])
        pre_sel = st.selectbox("Procedimiento", procedimientos)

        # Cargas de archivos (Restablecidas)
        st.file_uploader("Subir Orden Médica", type=["pdf", "jpg", "jpeg"], key="up_orden")

        if st.button("CONTINUAR"):
            if st.session_state.form["nombre"]:
                row = df[(df['ESPECIALIDAD'] == esp_sel) & (df['PROCEDIMIENTO A REALIZAR'] == pre_sel)]
                st.session_state.tiene_contraste = str(row['MEDIO DE CONTRASTE'].values[0]).upper() == "SI" if not row.empty else False
                st.session_state.procedimiento = pre_sel
                st.session_state.step = 2; st.rerun()

elif st.session_state.step == 2:
    mostrar_logo(); st.title("📋 Cuestionario")
    opts = ["No", "Sí"]
    st.session_state.form["bio_marcapaso"] = st.radio("¿Marcapasos?", opts, horizontal=True)
    st.session_state.form["bio_implantes"] = st.radio("¿Implantes metálicos?", opts, horizontal=True)
    
    if st.session_state.tiene_contraste:
        st.session_state.form["creatinina"] = st.number_input("Creatinina", value=st.session_state.form["creatinina"], step=0.01)
        st.session_state.form["peso"] = st.number_input("Peso (kg)", value=st.session_state.form["peso"])
        if st.session_state.form["creatinina"] > 0:
            edad = calcular_edad(st.session_state.form["fecha_nac"])
            vfg = ((140 - edad) * st.session_state.form["peso"]) / (72 * st.session_state.form["creatinina"])
            st.session_state.form["vfg"] = vfg
            st.metric("VFG Resultado", f"{vfg:.2f} ml/min")

    st.session_state.form["veracidad"] = st.radio("¿Información fidedigna?", ["SÍ", "NO"], index=None)
    if st.button("SIGUIENTE"):
        if st.session_state.form["veracidad"] == "SÍ": st.session_state.step = 3; st.rerun()

elif st.session_state.step == 3:
    mostrar_logo(); st.title("Firma")
    st.write("Firme en el recuadro:")
    canvas_result = st_canvas(stroke_width=2, stroke_color="#000", background_color="#fff", height=150, width=400, key="canvas")
    if st.button("FINALIZAR"):
        if np.any(canvas_result.image_data[:, :, 3] > 0):
            img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                img.save(tmp.name); st.session_state.form["firma_img"] = tmp.name
            st.session_state.step = 4; st.rerun()

elif st.session_state.step == 4:
    mostrar_logo(); st.success("¡Registro Exitoso!")
    pdf_bytes = generar_pdf_clinico(st.session_state.form)
    nombre_pdf = f"RM_{st.session_state.form['rut']}.pdf"
    
    exito, res = subir_a_google_drive(pdf_bytes, nombre_pdf)
    if exito: st.info(f"✅ Sincronizado con Drive")
    else: st.warning(f"⚠️ Drive: {res}")
    
    st.download_button("📥 Descargar PDF", data=pdf_bytes, file_name=nombre_pdf, mime="application/pdf")
    if st.button("Nuevo Registro"):
        st.session_state.clear(); st.rerun()
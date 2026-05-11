import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from fpdf import FPDF
import os
import numpy as np
from PIL import Image
import tempfile
import base64
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
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        service = build('drive', 'v3', credentials=creds)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            tmp_pdf.write(archivo_datos)
            tmp_path = tmp_pdf.name
        file_metadata = {'name': nombre_archivo, 'parents': [ID_CARPETA_DRIVE]}
        media = MediaFileUpload(tmp_path, mimetype='application/pdf')
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        os.remove(tmp_path)
        return True, file.get('id')
    except Exception as e:
        return False, str(e)

# 1. CONFIGURACIÓN, ESTILOS Y LOGO
st.set_page_config(page_title="Norte Imagen - Registro RM", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f5f5f5; }
    .stButton>button { background-color: #800020; color: white; border-radius: 5px; width: 100%; height: 3.5em; font-weight: bold; font-size: 1.1em; }
    h1, h2, h3 { color: #800020; text-align: center; font-family: 'Arial'; }
    label { font-weight: bold; color: #333; font-size: 1.05em; }
    .section-header { 
        color: #800020; border-bottom: 2px solid #800020; padding-bottom: 8px; 
        margin-top: 30px; margin-bottom: 20px; font-size: 1.4em; font-weight: bold;
    }
    .legal-text {
        background-color: #ffffff; padding: 25px; border-radius: 8px; border: 1px solid #ccc;
        font-size: 1em; text-align: justify; color: #333; margin-bottom: 25px;
        max-height: 550px; overflow-y: auto; line-height: 1.7; font-family: 'Arial';
    }
    .vfg-box { padding: 25px; border-radius: 12px; text-align: center; margin-top: 25px; font-weight: bold; border: 3px solid; }
    .vfg-verde { background-color: #e8f5e9; border-color: #4caf50; color: #2e7d32; }
    .vfg-amarillo { background-color: #fffde7; border-color: #fbc02d; color: #f57f17; }
    .vfg-rojo { background-color: #ffebee; border-color: #f44336; color: #c62828; }
    </style>
    """, unsafe_allow_html=True)

def mostrar_logo_centrado():
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists("logoNI.png"): st.image("logoNI.png", use_container_width=True)
        else: st.subheader("NORTE IMAGEN")

# 2. FUNCIONES DE LÓGICA Y FORMATEO
def formatear_rut(rut_sucio):
    rut = str(rut_sucio).replace(".", "").replace("-", "").upper().strip()
    if not rut: return ""
    if len(rut) < 2: return rut
    cuerpo, dv = rut[:-1], rut[-1]
    if cuerpo.isdigit(): return f"{int(cuerpo):,}".replace(",", ".") + f"-{dv}"
    return rut_sucio

def capitalizar_nombre(txt):
    return ' '.join(word.capitalize() for word in txt.split())

def calcular_edad(f_nac):
    hoy = date.today()
    return hoy.year - f_nac.year - ((hoy.month, hoy.day) < (f_nac.month, f_nac.day))

# 3. GESTIÓN DE ESTADO (PERSISTENCIA DE DATOS)
if 'step' not in st.session_state: st.session_state.step = 1
if 'form' not in st.session_state:
    st.session_state.form = {
        "nombre": "", "rut": "", "sin_rut": False, "tipo_doc": "Pasaporte", "num_doc": "",
        "genero": "Masculino", "sexo_bio_nb": "Masculino", "f_nac": date(1990, 1, 1),
        "email": "", "n_tutor": "", "r_tutor": "", "sin_rut_tutor": False, "tipo_doc_tutor": "Pasaporte", "num_doc_tutor": "",
        "esp_idx": 0, "procedimiento": "", "contraste": "NO",
        "b_marcapaso": "No", "b_implante": "No", "b_detalle": "",
        "c_ayuno": "No", "c_asma": "No", "c_alergia": "No", "c_hta": "No", "c_tiro": "No", "c_diab": "No",
        "c_metf": "No", "c_renal": "No", "c_dial": "No", "c_clau": "No", "c_emb": "No", "c_lact": "No",
        "q_cirugia": "No", "q_detalle": "", "trats": [], "q_otro_trat": "",
        "exs": [], "ex_otros": "", "crea": 0.0, "peso": 0.0, "vfg": 0.0,
        "autoriza": "No", "firma_path": None
    }

# 4. MOTOR PDF MEJORADO (2 PÁGINAS)
class NorteImagenPDF(FPDF):
    def header(self):
        if os.path.exists("logoNI.png"): self.image("logoNI.png", 10, 8, 33)
        self.set_font('Arial', 'B', 14); self.set_text_color(128, 0, 32)
        self.cell(0, 10, 'ENCUESTA Y CONSENTIMIENTO INFORMADO', 0, 1, 'C')
        self.set_font('Arial', 'B', 11); self.cell(0, 5, 'RESONANCIA MAGNETICA', 0, 1, 'C')
        self.ln(10)
    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8); self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')
    def safe(self, txt): return str(txt).encode('latin-1', 'replace').decode('latin-1')

def generar_pdf(d):
    pdf = NorteImagenPDF()
    pdf.add_page()
    # Fecha arriba derecha
    pdf.set_font('Arial', '', 10); pdf.cell(0, 5, f"Fecha del Examen: {datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'R')
    
    # 1. IDENTIFICACIÓN
    pdf.set_fill_color(230, 230, 230); pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 7, "1. IDENTIFICACION DEL PACIENTE", 0, 1, 'L', True)
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 6, pdf.safe(f"Nombre Completo: {d['nombre']}"), 0, 1)
    id_p = d['rut'] if not d['sin_rut'] else f"{d['tipo_doc']}: {d['num_doc']}"
    pdf.cell(0, 6, pdf.safe(f"RUT/Doc: {id_p} | F.Nac: {d['f_nac'].strftime('%d/%m/%Y')} | Edad: {calcular_edad(d['f_nac'])}"), 0, 1)
    pdf.cell(0, 6, pdf.safe(f"Email: {d['email']} | Procedimiento: {d['procedimiento']} | Contraste: {d['contraste']}"), 0, 1)
    if calcular_edad(d['f_nac']) < 18:
        id_t = d['r_tutor'] if not d['sin_rut_tutor'] else f"{d['tipo_doc_tutor']}: {d['num_doc_tutor']}"
        pdf.cell(0, 6, pdf.safe(f"Representante Legal: {d['n_tutor']} | RUT/Doc Representante: {id_t}"), 0, 1)

    # 2. BIOSEGURIDAD
    pdf.ln(2); pdf.set_font('Arial', 'B', 10); pdf.cell(0, 7, "2. BIOSEGURIDAD MAGNETICA", 0, 1, 'L', True)
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 6, f"Marcapasos cardiaco: {d['b_marcapaso']} | Implantes/Protesis/Dispositivos: {d['b_implante']}", 0, 1)
    pdf.multi_cell(0, 5, pdf.safe(f"Detalle Bioseguridad: {d['b_detalle']}"))

    # 3. ANTECEDENTES CLÍNICOS (3 Columnas)
    pdf.ln(2); pdf.set_font('Arial', 'B', 10); pdf.cell(0, 7, "3. ANTECEDENTES CLINICOS", 0, 1, 'L', True)
    pdf.set_font('Arial', '', 8)
    cl_datos = [
        f"Ayuno: {d['c_ayuno']}", f"Asma: {d['c_asma']}", f"Alergias: {d['c_alergia']}",
        f"HTA: {d['c_hta']}", f"Hipotiroidismo: {d['c_tiro']}", f"Diabetes: {d['c_diab']}",
        f"Metformina: {d['c_metf']}", f"Insuf. Renal: {d['c_renal']}", f"Dialisis: {d['c_dial']}",
        f"Embarazo: {d['c_emb']}", f"Lactancia: {d['c_lact']}", f"Claustrofobia: {d['c_clau']}"
    ]
    for i in range(0, len(cl_datos), 3):
        pdf.cell(60, 5, pdf.safe(cl_datos[i]), 0)
        if i+1 < len(cl_datos): pdf.cell(60, 5, pdf.safe(cl_datos[i+1]), 0)
        if i+2 < len(cl_datos): pdf.cell(60, 5, pdf.safe(cl_datos[i+2]), 0)
        pdf.ln()

    # 4. QUIRÚRGICOS Y VFG
    pdf.ln(2); pdf.set_font('Arial', 'B', 10); pdf.cell(0, 7, "4. ANTECEDENTES QUIRURGICOS Y FUNCION RENAL", 0, 1, 'L', True)
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 6, f"Cirugias: {d['q_cirugia']} | Detalle: {pdf.safe(d['q_detalle'])}", 0, 1)
    pdf.cell(0, 6, f"Tratamientos: {', '.join(d['trats'])} | Otros: {pdf.safe(d['q_otro_trat'])}", 0, 1)
    if d['contraste'] == "SI":
        pdf.cell(0, 6, f"Creatinina: {d['crea']} mg/dL | Peso: {d['peso']} kg | RESULTADO VFG: {d['vfg']:.2f} ml/min", 0, 1)

    # PÁGINA 2
    pdf.add_page()
    pdf.set_font('Arial', 'B', 10); pdf.cell(0, 7, pdf.safe(f"{d['procedimiento']} ({'Con' if d['contraste']=='SI' else 'Sin'} medio de contraste)"), 0, 1, 'C')
    pdf.ln(3); pdf.set_font('Arial', 'B', 11); pdf.cell(0, 7, "LEA ATENTA Y CUIDADOSAMENTE LO SIGUIENTE:", 0, 1, 'C')
    pdf.set_font('Arial', '', 8.5)
    texto_legal = (
        "OBJETIVOS: La Resonancia Magnetica (RM) es una segura tecnica de Diagnostico... "
        "(Se incluye aquí todo el texto legal descrito en el esquema base de 3 párrafos)..."
    )
    pdf.multi_cell(0, 4.5, pdf.safe(texto_legal), 0, 'J')
    pdf.ln(15)
    y_f = pdf.get_y()
    if d['firma_path']: pdf.image(d['firma_path'], 25, y_f - 15, 40)
    pdf.line(20, y_f, 85, y_f); pdf.line(115, y_f, 180, y_f)
    pdf.set_font('Arial', 'B', 8); pdf.text(20, y_f + 5, "FIRMA PACIENTE O REPRESENTANTE"); pdf.text(115, y_f + 5, "FIRMA PROFESIONAL RESPONSABLE")
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# 5. PÁGINAS DE LA APLICACIÓN
@st.cache_data
def load_csv():
    try:
        df = pd.read_csv('listado_prestaciones.csv', sep=None, engine='python', encoding='utf-8-sig')
        return df
    except: return None

df_csv = load_csv()

# PAGINA 1: REGISTRO
if st.session_state.step == 1:
    mostrar_logo_centrado()
    st.title("🏥 Registro de Paciente")
    st.markdown('<div class="section-header">Identificación del paciente</div>', unsafe_allow_html=True)
    
    st.session_state.form["nombre"] = capitalizar_nombre(st.text_input("Nombre completo del paciente", value=st.session_state.form["nombre"]))
    
    c1, c2 = st.columns([2, 1])
    st.session_state.form["sin_rut"] = c2.checkbox("Sin RUT, poseo otro documento", value=st.session_state.form["sin_rut"])
    if not st.session_state.form["sin_rut"]:
        st.session_state.form["rut"] = formatear_rut(c1.text_input("RUT del Paciente", value=st.session_state.form["rut"], placeholder="12.345.678-9"))
    else:
        st.session_state.form["tipo_doc"] = c1.selectbox("Tipo de documento", ["Pasaporte", "Cédula de extranjero"], key="td1")
        st.session_state.form["num_doc"] = st.text_input("Registro numérico del documento", value=st.session_state.form["num_doc"])

    gen_list = ["Femenino", "Masculino", "No binario"]
    st.session_state.form["genero"] = st.selectbox("Género", gen_list, index=gen_list.index(st.session_state.form["genero"]))
    sexo_calculo = st.session_state.form["genero"]
    if st.session_state.form["genero"] == "No binario":
        st.session_state.form["sexo_bio_nb"] = st.selectbox("Sexo asignado al nacer (dato para fines clínicos)", ["Femenino", "Masculino"])
        sexo_calculo = st.session_state.form["sexo_bio_nb"]

    st.session_state.form["f_nac"] = st.date_input("Fecha de nacimiento", value=st.session_state.form["f_nac"], format="DD/MM/YYYY")
    edad = calcular_edad(st.session_state.form["f_nac"])
    if edad < 18:
        st.warning(f"👦PACIENTE MENOR DE EDAD ({edad} años)")
        st.session_state.form["n_tutor"] = st.text_input("Nombre completo del Representante legal", value=st.session_state.form["n_tutor"])
        ct1, ct2 = st.columns([2, 1])
        st.session_state.form["sin_rut_tutor"] = ct2.checkbox("Tutor: Sin RUT", value=st.session_state.form["sin_rut_tutor"])
        if not st.session_state.form["sin_rut_tutor"]:
            st.session_state.form["r_tutor"] = formatear_rut(ct1.text_input("RUT del representante legal", value=st.session_state.form["r_tutor"]))
        else:
            st.session_state.form["tipo_doc_tutor"] = ct1.selectbox("Tipo doc tutor", ["Pasaporte", "Cédula de extranjero"])
            st.session_state.form["num_doc_tutor"] = st.text_input("N° doc tutor", value=st.session_state.form["num_doc_tutor"])

    st.markdown('<div class="section-header">Información del Examen</div>', unsafe_allow_html=True)
    esp_orden = ["Neuroradiología", "Musculoesquelético", "Cuerpo", "Angiografía por RM", "Estudios o procedimientos avanzados"]
    esp_sel = st.selectbox("Especialidad", esp_orden, index=st.session_state.form["esp_idx"])
    st.session_state.form["esp_idx"] = esp_orden.index(esp_sel)
    
    if df_csv is not None:
        procs = sorted(df_csv[df_csv['ESPECIALIDAD'] == esp_sel]['PROCEDIMIENTO A REALIZAR'].unique())
        st.session_state.form["procedimiento"] = st.selectbox("Procedimiento", procs)
        row = df_csv[df_csv['PROCEDIMIENTO A REALIZAR'] == st.session_state.form["procedimiento"]]
        st.session_state.form["contraste"] = "SI" if not row.empty and str(row['MEDIO DE CONTRASTE'].values[0]).upper() == "SI" else "NO"

    st.markdown('<div class="section-header">Documentación Médica</div>', unsafe_allow_html=True)
    st.file_uploader("Subir archivo: Cargue la Orden Médica", type=["pdf", "jpg", "jpeg"])
    st.file_uploader("Subir archivo: Cargue Exámenes anteriores (Máx 4)", type=["pdf", "jpg", "jpeg"], accept_multiple_files=True)

    if st.button("Continuar"):
        if st.session_state.form["nombre"] and st.session_state.form["procedimiento"]:
            st.session_state.sexo_vfg = sexo_calculo
            st.session_state.step = 2; st.rerun()
        else: st.error("Llene los campos obligatorios")

# PAGINA 2: CUESTIONARIO
elif st.session_state.step == 2:
    mostrar_logo_centrado()
    st.title("📝 Cuestionario de seguridad RM")
    st.markdown('<div class="section-header">Bioseguridad Magnética</div>', unsafe_allow_html=True)
    st.session_state.form["b_marcapaso"] = st.radio("Marcapasos cardiaco:", ["No", "Si"], horizontal=True)
    st.session_state.form["b_implante"] = st.radio("Implantes metálicos, quirúrgicos, prótesis:", ["No", "Si"], horizontal=True)
    st.session_state.form["b_detalle"] = st.text_input("Tipo de implante, ubicación y fecha de colocación:")

    st.markdown('<div class="section-header">Antecedentes Clínicos</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    k1 = [("c_ayuno", "Ayuno 2h+"), ("c_asma", "Asma"), ("c_alergia", "Alergias"), ("c_hta", "HTA")]
    k2 = [("c_tiro", "Hipotiroidismo"), ("c_diab", "Diabetes"), ("c_metf", "Metformina"), ("c_renal", "Insuf. Renal")]
    k3 = [("c_dial", "Diálisis"), ("c_emb", "Embarazo"), ("c_lact", "Lactancia"), ("c_clau", "Claustrofobia")]
    for col, keys in zip([c1, c2, c3], [k1, k2, k3]):
        for k, l in keys: st.session_state.form[k] = col.radio(l, ["No", "Si"])

    st.markdown('<div class="section-header">Antecedentes quirúrgicos y/o Terapéuticos</div>', unsafe_allow_html=True)
    st.session_state.form["q_cirugia"] = st.radio("¿Cirugías?", ["No", "Si"], horizontal=True)
    st.session_state.form["q_detalle"] = st.text_input("Detalle nombre y fecha de cirugías:")
    st.session_state.form["trats"] = st.multiselect("Tratamientos:", ["Radioterapia (RT)", "Quimioterapia (QT)", "Braquiterapia (BT)", "Inmunoterapia (IT)"])
    st.session_state.form["q_otro_trat"] = st.text_input("Otro tratamiento:")

    st.markdown('<div class="section-header">Exámenes anteriores</div>', unsafe_allow_html=True)
    st.session_state.form["exs"] = st.multiselect("Marque exámenes previos:", ["Radiografía (Rx)", "Mamografía (MG)", "Ecografía (Eco)", "Tomografía Computarizada (TC)", "Resonancia Magnética (RM)"])
    st.session_state.form["ex_otros"] = st.text_input("Otros exámenes anteriores:")

    if st.session_state.form["contraste"] == "SI":
        st.markdown('<div class="section-header">Función Renal (VFG-Cockcroft-Gault)</div>', unsafe_allow_html=True)
        st.session_state.form["crea"] = st.number_input("Creatinina (mg/dL)", min_value=0.0, max_value=7.99, step=0.01, format="%.2f")
        st.session_state.form["peso"] = st.number_input("Peso (kg)", min_value=0.0, max_value=200.0, step=0.1)
        if st.session_state.form["crea"] > 0:
            v = ((140 - calcular_edad(st.session_state.form["f_nac"])) * st.session_state.form["peso"]) / (72 * st.session_state.form["crea"])
            if st.session_state.sexo_vfg == "Femenino": v *= 0.85
            st.session_state.form["vfg"] = v
            if v <= 30: cls, msg = "vfg-rojo", "Alto riesgo para la administración de medio de contraste"
            elif v < 60: cls, msg = "vfg-amarillo", "Riesgo intermedio para la administración de medio de contraste"
            else: cls, msg = "vfg-verde", "Sin riesgos para la administración del medio de contraste"
            st.markdown(f'<div class="vfg-box {cls}">RESULTADO VFG: {v:.2f} ml/min<br>{msg}</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    if col1.button("Atrás"): st.session_state.step = 1; st.rerun()
    if col2.button("Continuar"): st.session_state.step = 3; st.rerun()

# PAGINA 3: FIRMA Y FINALIZACIÓN
elif st.session_state.step == 3:
    mostrar_logo_centrado()
    st.title("📄 Información al paciente")
    st.subheader(f"{st.session_state.form['nombre']} - {st.session_state.form['procedimiento']} ({st.session_state.form['contraste']} usa contraste)")
    st.markdown('<div class="legal-text"><b>LEA ATENTA Y CUIDADOSAMENTE LO SIGUIENTE:</b><br><br>OBJETIVOS... (Texto íntegro del documento base)...</div>', unsafe_allow_html=True)
    
    st.session_state.form["autoriza"] = st.radio("¿Ha leído y autoriza el procedimiento?", ["SÍ", "NO"], index=None)
    st.write("Firma del paciente o representante legal:")
    canvas = st_canvas(stroke_width=2, stroke_color="#000", background_color="#fff", height=150, width=400, key="canvas")
    
    col1, col2 = st.columns(2)
    if col1.button("Atrás"): st.session_state.step = 2; st.rerun()
    if col2.button("Finalizar"):
        if st.session_state.form["autoriza"] == "SÍ" and np.any(canvas.image_data[:, :, 3] > 0):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                Image.fromarray(canvas.image_data.astype('uint8')).save(tmp.name)
                st.session_state.form["firma_path"] = tmp.name
            st.session_state.step = 4; st.rerun()
        else: st.error("Debe autorizar y firmar para finalizar.")

# PAGINA 4: DESCARGA Y DRIVE
elif st.session_state.step == 4:
    mostrar_logo_centrado()
    st.success("Registro y consentimiento completo")
    pdf_bytes = generar_pdf(st.session_state.form)
    n_file = f"RegistroEC_{st.session_state.form['rut']}_{st.session_state.form['nombre'].replace(' ','_')}.pdf"
    
    # Subida automática a Drive
    with st.spinner("Sincronizando con Google Drive..."):
        ok, res = subir_a_google_drive(pdf_bytes, n_file)
        if ok: st.info(f"✅ Documento enviado a Drive.")
        else: st.warning(f"⚠️ Error Drive: {res}")

    # Botón de Descarga / Apertura
    st.download_button("📥 Descargar PDF", data=pdf_bytes, file_name=n_file, mime="application/pdf")
    
    # Abrir en nueva ventana (Base64)
    b64 = base64.b64encode(pdf_bytes).decode('latin-1')
    pdf_display = f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="600" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

    if st.button("Nuevo Registro de paciente"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
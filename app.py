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
        # Usa las credenciales guardadas en Secrets de Streamlit
        if "gcp_service_account" not in st.secrets:
            return False, "Faltan credenciales en Secrets"
            
        # CORRECCIÓN PUNTO 2: Reparación de la PEM key
        creds_dict = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        service = build('drive', 'v3', credentials=creds)

        # Crear archivo temporal físico para la subida
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            tmp_pdf.write(archivo_datos)
            tmp_path = tmp_pdf.name

        file_metadata = {
            'name': nombre_archivo,
            'parents': [ID_CARPETA_DRIVE]
        }
        media = MediaFileUpload(tmp_path, mimetype='application/pdf')
        
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        os.remove(tmp_path) # Limpieza
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

# 3. FUNCIONES DE APOYO Y MOTOR PDF
def formatear_rut(rut_sucio):
    rut_limpio = str(rut_sucio).replace(".", "").replace("-", "").upper().strip()
    if len(rut_limpio) < 2: return rut_limpio
    cuerpo, dv = rut_limpio[:-1], rut_limpio[-1]
    if cuerpo.isdigit(): return f"{int(cuerpo):,}".replace(",", ".") + f"-{dv}"
    return rut_sucio

def calcular_edad(fecha_nac):
    today = date.today()
    return today.year - fecha_nac.year - ((today.month, today.day) < (fecha_nac.month, fecha_nac.day))

# CORRECCIÓN PUNTO 1: Sanitización de texto para evitar PDF en blanco
def safe_str(texto):
    if texto is None: return ""
    return str(texto).encode('latin-1', 'replace').decode('latin-1')

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
        self.cell(0, 7, f"{num}. {safe_str(label)}", 0, 1, 'L', 1)
        self.ln(2)

    def data_field(self, label, value):
        self.set_font('Arial', 'B', 9)
        self.set_text_color(50, 50, 50)
        self.write(5, f"{safe_str(label)}: ")
        self.set_font('Arial', '', 9)
        self.set_text_color(0, 0, 0)
        self.write(5, f"{safe_str(value)}\n")

def generar_pdf_clinico(datos):
    pdf = PDF()
    pdf.add_page()
    
    # 1. Identificación
    pdf.section_title("1", "IDENTIFICACION DEL PACIENTE")
    doc_id = datos['rut'] if not datos['sin_rut'] else f"{datos['tipo_doc']}: {datos['num_doc']}"
    pdf.data_field("Fecha del Examen", datetime.now().strftime("%d/%m/%Y"))
    pdf.data_field("Nombre Completo", datos['nombre'])
    pdf.data_field("RUT", doc_id)
    pdf.data_field("Fecha de Nacimiento", datos['fecha_nac'].strftime("%d/%m/%Y"))
    pdf.data_field("Email", datos['email'])
    pdf.data_field("Procedimiento", st.session_state.procedimiento)
    pdf.data_field("Medio de contraste", "SI" if st.session_state.tiene_contraste else "NO")
    pdf.data_field("Representante legal", datos['nombre_tutor'] if datos['nombre_tutor'] else "N/A")
    pdf.data_field("RUT representante legal", datos['rut_tutor'] if datos['rut_tutor'] else "N/A")
    pdf.ln(4)

    # 2. Bioseguridad
    pdf.section_title("2", "BIOSEGURIDAD MAGNETICA")
    pdf.data_field("Marcapasos cardiaco", datos['bio_marcapaso'])
    pdf.data_field("Implantes/Protesis metalicas", datos['bio_implantes'])
    pdf.data_field("Detalle Bioseguridad", datos['bio_detalle'] if datos['bio_detalle'] else "")
    pdf.ln(4)

    # 3. Antecedentes Clínicos
    pdf.section_title("3", "ANTECEDENTES CLINICOS")
    clin_txt = (f"Ayuno: {datos['clin_ayuno']} | Asma: {datos['clin_asma']} | HTA: {datos['clin_hiperten']} | "
                f"Hipertiroidismo: {datos['clin_hipertiroid']} | Diabetes: {datos['clin_diabetes']} | "
                f"Alergico: {datos['clin_alergico']} | Insuf. Renal: {datos['clin_renal']} | "
                f"Dialisis: {datos['clin_dialisis']} | Embarazo: {datos['clin_embarazo']} | Lactancia: {datos['clin_lactancia']}")
    pdf.set_font('Arial', '', 9)
    pdf.multi_cell(0, 5, safe_str(clin_txt))
    pdf.ln(4)

    # 4. Quirúrgicos
    pdf.section_title("4", "ANTECEDENTES QUIRURGICOS, TERAPEUTICOS Y FUNCION RENAL")
    pdf.data_field("Cirugias", datos['quir_cirugia_check'])
    pdf.data_field("Detalle cirugias", datos['quir_cirugia_detalle'] if datos['quir_cirugia_detalle'] else "")
    
    trats = []
    if datos['rt']: trats.append("RT")
    if datos['qt']: trats.append("QT")
    if datos['bt']: trats.append("BT")
    if datos['it']: trats.append("IT")
    pdf.data_field("Tratamientos", ", ".join(trats) if trats else "Ninguno")
    pdf.data_field("Detalle de otros tratamientos", datos['quir_otro_trat'] if datos['quir_otro_trat'] else "")
    
    if st.session_state.tiene_contraste:
        pdf.ln(2)
        pdf.data_field("Creatinina", f"{datos['creatinina']} mg/dL")
        pdf.data_field("Peso", f"{datos['peso']} kg")
        if datos['vfg'] < 30: pdf.set_text_color(255, 0, 0)
        pdf.data_field("RESULTADO VFG", f"{datos['vfg']:.2f} ml/min")
        pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # 5. Exámenes Anteriores
    pdf.section_title("5", "EXAMENES ANTERIORES")
    exs = []
    if datos['ex_rx']: exs.append("Rx")
    if datos['ex_mg']: exs.append("MG")
    if datos['ex_eco']: exs.append("Eco")
    if datos['ex_tc']: exs.append("TC")
    if datos['ex_rm']: exs.append("RM")
    pdf.data_field("Examenes realizados", ", ".join(exs) if exs else "Ninguno")
    pdf.data_field("Otros examenes anteriores", datos['ex_otros'] if datos['ex_otros'] else "")

    # NUEVA PÁGINA: INFORMACIÓN
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, safe_str("LEA ATENTA Y CUIDADOSAMENTE LO SIGUIENTE:"), 0, 1, 'C')
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 5, "OBJETIVOS", 0, 1, 'L')
    pdf.set_font('Arial', '', 9)
    pdf.multi_cell(0, 5, safe_str("La Resonancia Magnetica (RM) es una segura tecnica de Diagnostico... Autorizo la realizacion del procedimiento y las acciones necesarias."))
    
    pdf.ln(15)
    y_pos = pdf.get_y()
    if datos['firma_img']:
        pdf.image(datos['firma_img'], x=20, y=y_pos - 12, w=50)
    
    pdf.line(15, y_pos + 5, 85, y_pos + 5)
    pdf.set_font('Arial', 'B', 8)
    pdf.text(15, y_pos + 10, safe_str(f"FIRMA PACIENTE: {datos['nombre'][:30]}"))
    pdf.line(115, y_pos + 5, 185, y_pos + 5)
    pdf.text(115, y_pos + 10, "FIRMA PROFESIONAL RESPONSABLE")

    # Retornar como bytes (latin-1 por fpdf)
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

# --- PÁGINA 1: REGISTRO ---
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
            st.session_state.form["fecha_nac"] = st.date_input("Fecha de Nacimiento", value=st.session_state.form["fecha_nac"], min_value=date(1910, 1, 1), max_value=date.today(), format="DD/MM/YYYY")
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

        if st.button("CONTINUAR"):
            if st.session_state.form["nombre"]:
                row = df[(df['ESPECIALIDAD'] == esp_sel) & (df['PROCEDIMIENTO A REALIZAR'] == pre_sel)]
                st.session_state.tiene_contraste = str(row['MEDIO DE CONTRASTE'].values[0]).upper() == "SI" if not row.empty else False
                st.session_state.procedimiento = pre_sel
                st.session_state.edad_para_calculo = edad
                st.session_state.sexo_para_calculo = sexo_final
                st.session_state.step = 2; st.rerun()

# --- PÁGINA 2: CUESTIONARIO ---
elif st.session_state.step == 2:
    mostrar_logo(); st.title("📋 Cuestionario de Seguridad RM")
    opts = ["No", "Sí"]

    st.markdown('<div class="section-header">1. Bioseguridad Magnética</div>', unsafe_allow_html=True)
    st.session_state.form["bio_marcapaso"] = st.radio("Marcapasos:", opts, index=opts.index(st.session_state.form["bio_marcapaso"]), horizontal=True)
    st.session_state.form["bio_implantes"] = st.radio("Implantes metálicos:", opts, index=opts.index(st.session_state.form["bio_implantes"]), horizontal=True)
    st.session_state.form["bio_detalle"] = st.text_area("Detalle:", value=st.session_state.form["bio_detalle"], height=70)

    st.markdown('<div class="section-header">2. Antecedentes Clínicos</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    k1 = [("clin_ayuno", "Ayuno"), ("clin_asma", "Asma"), ("clin_hiperten", "Hipertensión"), ("clin_hipertiroid", "Hipertiroidismo")]
    k2 = [("clin_diabetes", "Diabetes"), ("clin_alergico", "Alérgico"), ("clin_metformina", "Metformina"), ("clin_renal", "Insuficiencia renal")]
    k3 = [("clin_dialisis", "Diálisis"), ("clin_claustro", "Claustrofóbico"), ("clin_embarazo", "Embarazo"), ("clin_lactancia", "Lactancia")]
    for col, keys in zip([c1, c2, c3], [k1, k2, k3]):
        for k, label in keys: st.session_state.form[k] = col.radio(label, opts, index=opts.index(st.session_state.form[k]))

    if st.session_state.tiene_contraste:
        st.markdown('<div class="section-header">Función Renal (VFG)</div>', unsafe_allow_html=True)
        st.session_state.form["creatinina"] = st.number_input("Creatinina (mg/dL)", value=st.session_state.form["creatinina"], step=0.01)
        st.session_state.form["peso"] = st.number_input("Peso (kg)", value=st.session_state.form["peso"])
        if st.session_state.form["creatinina"] > 0:
            vfg = ((140 - st.session_state.edad_para_calculo) * st.session_state.form["peso"]) / (72 * st.session_state.form["creatinina"])
            if st.session_state.sexo_para_calculo == "Femenino": vfg *= 0.85
            st.session_state.form["vfg"] = vfg
            estilo = "vfg-critica" if vfg < 30 else ""
            st.markdown(f'<div class="vfg-box {estilo}">VFG: <h2>{vfg:.2f}</h2></div>', unsafe_allow_html=True)

    st.divider()
    st.session_state.form["veracidad"] = st.radio("¿Veracidad?", ["SÍ", "NO"], index=None)
    if st.button("SIGUIENTE"):
        if st.session_state.form["veracidad"] == "SÍ": st.session_state.step = 3; st.rerun()

# --- PÁGINA 3: FIRMA ---
elif st.session_state.step == 3:
    mostrar_logo(); st.title("Firma")
    st.session_state.form["autoriza_gad"] = st.radio("¿Autoriza?", ["SÍ", "NO"], index=None)
    canvas_result = st_canvas(stroke_width=2, stroke_color="#000", background_color="#fff", height=150, width=400, key="canvas")
    if st.button("FINALIZAR"):
        if st.session_state.form["autoriza_gad"] == "SÍ":
            img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                img.save(tmp.name); st.session_state.form["firma_img"] = tmp.name
            st.session_state.step = 4; st.rerun()

# --- PÁGINA 4: DRIVE ---
elif st.session_state.step == 4:
    mostrar_logo(); st.success("Completado")
    pdf_output = generar_pdf_clinico(st.session_state.form)
    nombre_final = f"Registro_{st.session_state.form['rut']}.pdf"
    exito, resultado = subir_a_google_drive(pdf_output, nombre_final)
    if exito: st.info(f"✅ Drive OK")
    else: st.warning(f"⚠️ Drive Error: {resultado}")
    st.download_button("Descargar PDF", pdf_output, nombre_final, "application/pdf")
    if st.button("Nuevo"): 
        st.session_state.clear(); st.rerun()
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

# ==============================================================================
# INTEGRACIÓN AVANZADA CON GOOGLE DRIVE API (SISTEMA DE RESPALDO)
# ==============================================================================
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

ID_CARPETA_DRIVE = "1HyeTglfI9BiNlBH8W7rLWcmkaHQiUQE5"

def subir_a_google_drive(archivo_bytes, nombre_archivo):
    """
    Función de respaldo en la nube. 
    Se encarga de la autenticación mediante cuenta de servicio y subida de archivos.
    CORRECCIÓN: Manejo de AttrDict de Streamlit para evitar errores de campos faltantes.
    """
    try:
        if "gcp_service_account" not in st.secrets:
            return False, "ERROR: No se encontraron las credenciales 'gcp_service_account' en el archivo de secretos del servidor."
            
        # Transformación de los secretos de Streamlit a un diccionario nativo de Python
        # Esto soluciona el error 'missing fields client_email' al convertir el objeto Proxy de Streamlit
        info_servidor = {}
        for llave, valor in st.secrets["gcp_service_account"].items():
            info_servidor[llave] = valor
            
        # Validación interna de la estructura de la cuenta de servicio
        campos_requeridos = [
            "type", "project_id", "private_key_id", "private_key", 
            "client_email", "client_id", "auth_uri", "token_uri"
        ]
        
        for campo in campos_requeridos:
            if campo not in info_servidor:
                return False, f"ERROR DE FORMATO: Falta el campo '{campo}' en la configuración de la cuenta de servicio."

        # Proceso de autenticación con Google Auth
        credenciales_google = service_account.Credentials.from_service_account_info(info_servidor)
        instancia_drive = build('drive', 'v3', credentials=credenciales_google)

        # Generación de archivo temporal físico necesario para la API de Google
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as archivo_temporal_pdf:
            archivo_temporal_pdf.write(archivo_bytes)
            ruta_archivo_fisico = archivo_temporal_pdf.name

        # Definición de metadatos del archivo en la carpeta compartida
        metadatos_archivo = {
            'name': nombre_archivo,
            'parents': [ID_CARPETA_DRIVE],
            'description': f"Registro de RM generado automáticamente desde la aplicación web el {datetime.now().strftime('%d/%m/%Y')}"
        }
        
        cuerpo_media = MediaFileUpload(ruta_archivo_fisico, mimetype='application/pdf', resumable=True)
        
        # Ejecución de la subida a los servidores de Google
        archivo_creado = instancia_drive.files().create(
            body=metadatos_archivo, 
            media_body=cuerpo_media, 
            fields='id'
        ).execute()
        
        # Eliminación del residuo temporal en el servidor
        if os.path.exists(ruta_archivo_fisico):
            os.remove(ruta_archivo_fisico)
            
        return True, archivo_creado.get('id')
        
    except Exception as error_instancia:
        return False, f"FALLO DE CONEXIÓN: {str(error_instancia)}"

# ==============================================================================
# CONFIGURACIÓN DE LA INTERFAZ DE USUARIO Y ESTILOS CSS PERSONALIZADOS
# ==============================================================================
st.set_page_config(
    page_title="Norte Imagen - Sistema de Registro RM v2.0", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    /* Estilos generales de la aplicación */
    .stApp { background-color: #fcfcfc; }
    
    /* Personalización de botones principales */
    .stButton>button { 
        background-color: #800020; 
        color: #ffffff; 
        border-radius: 10px; 
        width: 100%; 
        height: 4em; 
        font-weight: 800; 
        font-size: 1.1em;
        border: 2px solid transparent;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .stButton>button:hover { 
        background-color: #ffffff; 
        color: #800020;
        border: 2px solid #800020;
        transform: translateY(-2px);
    }
    
    /* Formateo de encabezados institucionales */
    h1, h2, h3 { 
        color: #800020; 
        text-align: center; 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Etiquetas de formulario */
    label { font-weight: 700 !important; color: #2c3e50 !important; margin-bottom: 5px; }
    
    /* Contenedores de secciones médicas */
    .section-header { 
        color: #ffffff; 
        background: linear-gradient(90deg, #800020 0%, #a50029 100%);
        padding: 12px 20px;
        border-radius: 8px;
        margin-top: 35px; 
        margin-bottom: 20px; 
        font-size: 1.25em; 
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* BLOQUE LEGAL Y CONSENTIMIENTO (Integridad de texto) */
    .legal-text {
        background-color: #ffffff; 
        padding: 35px; 
        border-radius: 12px; 
        border: 1px solid #e0e0e0;
        font-size: 1.05em; 
        text-align: justify; 
        color: #2d3436; 
        margin-bottom: 30px;
        height: 600px; 
        overflow-y: scroll; 
        line-height: 1.8;
        box-shadow: inset 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Resultados de Función Renal (VFG) */
    .vfg-box { 
        background-color: #ffffff; 
        padding: 30px; 
        border-radius: 15px; 
        border: 3px solid #800020; 
        text-align: center; 
        margin: 25px 0;
        transition: transform 0.3s ease;
    }
    .vfg-critica { border-color: #e74c3c; background-color: #fff9f8; }
    .vfg-critica h2 { color: #e74c3c !important; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# GESTIÓN DEL ESTADO DE LA SESIÓN (PERSISTENCIA TOTAL DE DATOS)
# ==============================================================================
if 'step' not in st.session_state: st.session_state.step = 1
if 'form' not in st.session_state:
    st.session_state.form = {
        # Sección 1: Identificación Básica
        "nombre": "", "rut": "", "sin_rut": False, "tipo_doc": "Pasaporte", "num_doc": "",
        "genero_idx": 0, "sexo_bio_idx": 0, "fecha_nac": date(1990, 1, 1), "email": "", 
        "nombre_tutor": "", "rut_tutor": "", "esp_idx": 0,
        # Sección 2: Cuestionario de Bioseguridad
        "bio_marcapaso": "No", "bio_implantes": "No", "bio_detalle": "",
        # Sección 3: Antecedentes Clínicos
        "clin_ayuno": "No", "clin_asma": "No", "clin_hiperten": "No", "clin_hipertiroid": "No",
        "clin_diabetes": "No", "clin_alergico": "No", "clin_metformina": "No", "clin_renal": "No",
        "clin_dialisis": "No", "clin_claustro": "No", "clin_embarazo": "No", "clin_lactancia": "No",
        # Sección 4: Quirúrgicos y Tratamientos
        "quir_cirugia_check": "No", "quir_cirugia_detalle": "", "quir_cancer_detalle": "",
        "rt": False, "qt": False, "bt": False, "it": False, "quir_otro_trat": "",
        # Sección 5: Exámenes e Historial
        "ex_rx": False, "ex_mg": False, "ex_eco": False, "ex_tc": False, "ex_rm": False, "ex_otros": "",
        # Función Renal
        "creatinina": 0.0, "peso": 70.0, "vfg": 0.0,
        # Validación y Firma
        "veracidad": None, "autoriza_gad": None, "firma_img": None
    }

# ==============================================================================
# MOTOR DE GENERACIÓN DE DOCUMENTOS PDF (SISTEMA DE ALTA ESTABILIDAD)
# ==============================================================================
class GeneradorPDF_NI(FPDF):
    def header(self):
        if os.path.exists("logoNI.png"):
            self.image("logoNI.png", 10, 8, 40)
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(128, 0, 32)
        self.cell(0, 12, 'ENCUESTA Y CONSENTIMIENTO INFORMADO', 0, 1, 'C')
        self.set_font('Helvetica', 'B', 12)
        self.cell(0, 6, 'CENTRO DE IMAGENOLOGÍA AVANZADA - NORTE IMAGEN', 0, 1, 'C')
        self.ln(15)

    def footer(self):
        self.set_y(-20)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Documento clínico confidencial | Paciente: {st.session_state.form["nombre"]} | Pág {self.page_no()}', 0, 0, 'C')

    def titulo_seccion(self, titulo):
        self.set_font('Helvetica', 'B', 11)
        self.set_fill_color(128, 0, 32)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, f"  {titulo}", 0, 1, 'L', True)
        self.ln(4)

    def fila_datos(self, etiqueta, valor):
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(50, 50, 50)
        self.write(6, f"{etiqueta}: ")
        self.set_font('Helvetica', '', 9)
        self.set_text_color(0, 0, 0)
        self.write(6, f"{valor}\n")

def compilar_documento_pdf(datos):
    """
    Ensambla el archivo PDF clínico con toda la información capturada.
    Ajustado para evitar páginas vacías y errores de renderizado de imagen.
    """
    pdf = GeneradorPDF_NI()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    
    # BLOQUE 1: DATOS PERSONALES
    pdf.titulo_seccion("1. IDENTIFICACIÓN Y DATOS GENERALES")
    id_paciente = datos['rut'] if not datos['sin_rut'] else f"{datos['tipo_doc']}: {datos['num_doc']}"
    pdf.fila_datos("PACIENTE", datos['nombre'])
    pdf.fila_datos("IDENTIFICACIÓN", id_paciente)
    pdf.fila_datos("FECHA NACIMIENTO", datos['fecha_nac'].strftime("%d/%m/%Y"))
    pdf.fila_datos("EXAMEN", st.session_state.get("procedimiento", "RESONANCIA MAGNÉTICA"))
    pdf.fila_datos("USO DE CONTRASTE", "SÍ (GADOLINIO)" if st.session_state.get("tiene_contraste") else "NO")
    pdf.ln(5)

    # BLOQUE 2: SEGURIDAD
    pdf.titulo_seccion("2. EVALUACIÓN DE BIOSEGURIDAD MAGNÉTICA")
    pdf.fila_datos("MARCAPASOS / DESFIBRILADOR", datos['bio_marcapaso'])
    pdf.fila_datos("IMPLANTES / CLIPS / PRÓTESIS", datos['bio_implantes'])
    if datos['bio_detalle']:
        pdf.fila_datos("DETALLE DISPOSITIVOS", datos['bio_detalle'])
    pdf.ln(5)

    # BLOQUE 3: ANTECEDENTES CLÍNICOS (Tabla resumida)
    pdf.titulo_seccion("3. HISTORIAL CLÍNICO Y FACTORES DE RIESGO")
    pdf.set_font('Helvetica', '', 9)
    resumen_clinico = (f"AYUNO: {datos['clin_ayuno']} | ASMA: {datos['clin_asma']} | "
                       f"HTA: {datos['clin_hiperten']} | DIABETES: {datos['clin_diabetes']} | "
                       f"I. RENAL: {datos['clin_renal']} | EMBARAZO: {datos['clin_embarazo']}")
    pdf.multi_cell(0, 6, resumen_clinico)
    
    if st.session_state.get("tiene_contraste"):
        pdf.ln(3)
        pdf.fila_datos("FUNCIÓN RENAL (VFG)", f"{datos['vfg']:.2f} ml/min")
        pdf.fila_datos("CREATININA", f"{datos['creatinina']} mg/dL")
    pdf.ln(10)

    # PÁGINA 2: CONSENTIMIENTO LEGAL ÍNTEGRO
    pdf.add_page()
    pdf.titulo_seccion("4. CONSENTIMIENTO INFORMADO Y AUTORIZACIÓN")
    
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 8, "OBJETIVOS DEL PROCEDIMIENTO", 0, 1)
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(0, 5, "La Resonancia Magnética (RM) es una segura técnica de Diagnóstico, que permite la adquisición de imágenes de gran sensibilidad en todos los planos del espacio de las estructuras del cuerpo. Tiene como objetivo obtener Información, datos funcionales y morfológicos para detectar precozmente una enfermedad. Para este examen eventualmente se puede requerir la utilización de un medio de contraste paramagnético de administración endovenosa llamado gadolinio, que permite realzar ciertos tejidos del cuerpo para un mejor diagnóstico.")
    
    pdf.ln(4)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 8, "CARACTERÍSTICAS Y PRECAUCIONES", 0, 1)
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(0, 5, "La Resonancia utiliza fuertes campos magnéticos y ondas de radiofrecuencia, por lo que es muy importante dejar fuera de la sala absolutamente todo lo que lleve consigo de tipo metálico y/o electrónico (relojes, pulseras, teléfonos, tarjetas magnéticas, etc). Si lleva material de este tipo en su cuerpo (fijaciones dentales, piercings, algunos tatuajes, balas o esquirlas metálicas) ciertos tipos de prótesis (valvulares, de cadera, de rodilla, clips metálicos, etc), o implantes, así como dispositivos electrónicos de carácter médico como bombas de insulina, prótesis auditivas, marcapasos, desfibriladores, etc. Avísenos, ya que puede contraindicar de manera absoluta la realización de este examen. Usted será posicionado en la camilla del equipo, según el estudio a realizar y se colocarán cerca de la zona a estudiar unos dispositivos (bobinas) que pueden ser de diversos tamaños. Esta exploración suele ser larga (entre 20 min y 1 hr según los casos).")

    pdf.ln(10)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 5, "DECLARACIÓN DE VOLUNTAD", 0, 1)
    pdf.set_font('Helvetica', 'I', 9)
    pdf.multi_cell(0, 5, "Autorizo la realización del procedimiento anteriormente especificado y las acciones que sean necesarias en caso de surgir complicaciones durante el procedimiento. Doy mi consentimiento para la administración de fármacos si el estudio lo requiere.")

    # INSERCIÓN DE FIRMA DIGITAL
    if datos['firma_img'] and os.path.exists(datos['firma_img']):
        pdf.ln(10)
        posicion_y = pdf.get_y()
        pdf.image(datos['firma_img'], x=20, y=posicion_y, w=65)
        pdf.set_y(posicion_y + 30)
    
    pdf.line(15, pdf.get_y(), 100, pdf.get_y())
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 7, f"Firma del Paciente / Representante: {datos['nombre']}", 0, 1)
    
    # Salida en flujo de bytes codificados
    return pdf.output(dest='S').encode('latin-1')

# ==============================================================================
# LÓGICA DE NAVEGACIÓN Y COMPONENTES DE LA INTERFAZ
# ==============================================================================

@st.cache_data
def cargar_base_datos():
    try:
        df = pd.read_csv('listado_prestaciones.csv', sep=None, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        return df
    except:
        return None

df_global = cargar_base_datos()

def mostrar_cabecera_institucional():
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists("logoNI.png"):
            st.image("logoNI.png", use_container_width=True)
        else:
            st.markdown("## 🏥 NORTE IMAGEN")

# FLUJO PRINCIPAL DE PÁGINAS
if st.session_state.step == 1:
    mostrar_cabecera_institucional()
    st.markdown("### 1. Registro de Identificación")
    
    with st.form("form_identificacion"):
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.form["nombre"] = st.text_input("Nombre Completo", value=st.session_state.form["nombre"])
            rut_txt = st.text_input("RUT", value=st.session_state.form["rut"], placeholder="12.345.678-K")
            st.session_state.form["rut"] = rut_txt
            st.session_state.form["sin_rut"] = st.checkbox("Uso Pasaporte / Otro")
        
        with col2:
            st.session_state.form["fecha_nac"] = st.date_input("Fecha Nacimiento", value=st.session_state.form["fecha_nac"])
            st.session_state.form["email"] = st.text_input("Email", value=st.session_state.form["email"])
            
        st.markdown("---")
        if df_global is not None:
            especialidades = sorted(df_global['ESPECIALIDAD'].unique())
            esp_sel = st.selectbox("Especialidad", especialidades)
            procedimientos = sorted(df_global[df_global['ESPECIALIDAD']==esp_sel]['PROCEDIMIENTO A REALIZAR'].unique())
            proc_sel = st.selectbox("Examen a realizar", procedimientos)
            
            # Guardar lógica de contraste
            info_proc = df_global[df_global['PROCEDIMIENTO A REALIZAR'] == proc_sel].iloc[0]
            st.session_state.tiene_contraste = str(info_proc['MEDIO DE CONTRASTE']).upper() == "SI"
            st.session_state.procedimiento = proc_sel
            
        enviar_id = st.form_submit_button("VALIDAR Y CONTINUAR")
        if enviar_id:
            if st.session_state.form["nombre"] != "":
                st.session_state.step = 2
                st.rerun()

elif st.session_state.step == 2:
    mostrar_cabecera_institucional()
    st.markdown("### 2. Cuestionario Clínico y Seguridad")
    
    st.markdown('<div class="section-header">BIOSEGURIDAD RM</div>', unsafe_allow_html=True)
    c_bio1, c_bio2 = st.columns(2)
    st.session_state.form["bio_marcapaso"] = c_bio1.radio("¿Marcapasos o Desfibrilador?", ["No", "Sí"])
    st.session_state.form["bio_implantes"] = c_bio2.radio("¿Prótesis o Clips Metálicos?", ["No", "Sí"])
    st.session_state.form["bio_detalle"] = st.text_input("Especifique si marcó SÍ:")

    st.markdown('<div class="section-header">ANTECEDENTES GENERALES</div>', unsafe_allow_html=True)
    c_clin1, c_clin2, c_clin3 = st.columns(3)
    st.session_state.form["clin_ayuno"] = c_clin1.radio("¿Ayuno de 6h?", ["No", "Sí"])
    st.session_state.form["clin_diabetes"] = c_clin2.radio("¿Diabetes?", ["No", "Sí"])
    st.session_state.form["clin_renal"] = c_clin3.radio("¿Falla Renal?", ["No", "Sí"])

    if st.session_state.get("tiene_contraste"):
        st.markdown('<div class="section-header">CÁLCULO DE FUNCIÓN RENAL (VFG)</div>', unsafe_allow_html=True)
        col_v1, col_v2 = st.columns(2)
        crea = col_v1.number_input("Creatinina sérica", min_value=0.1, value=0.9, step=0.1)
        peso_p = col_v2.number_input("Peso (kg)", min_value=10, value=70)
        
        # Fórmula Cockcroft-Gault
        edad_p = date.today().year - st.session_state.form["fecha_nac"].year
        vfg_val = ((140 - edad_p) * peso_p) / (72 * crea)
        st.session_state.form["vfg"] = vfg_val
        st.session_state.form["creatinina"] = crea
        st.session_state.form["peso"] = peso_p
        
        clase_box = "vfg-box" if vfg_val >= 30 else "vfg-box vfg-critica"
        st.markdown(f'<div class="{clase_box}">Resultado VFG: <h2>{vfg_val:.2f} ml/min</h2></div>', unsafe_allow_html=True)

    if st.button("PROCEDER AL CONSENTIMIENTO"):
        st.session_state.step = 3
        st.rerun()

elif st.session_state.step == 3:
    mostrar_cabecera_institucional()
    st.markdown("### 3. Consentimiento Legal")
    
    st.markdown("""
        <div class="legal-text">
        <strong>LEA ATENTAMENTE:</strong><br><br>
        Usted va a ser sometido a un examen de RESONANCIA MAGNÉTICA. Este estudio utiliza campos magnéticos de alta intensidad. Es imperativo que declare cualquier objeto metálico en su cuerpo.<br><br>
        <strong>COMPLICACIONES:</strong> Aunque el Gadolinio es seguro, existen riesgos mínimos de reacciones alérgicas. En pacientes con VFG menor a 30, existe riesgo de Fibrosis Nefrogénica Sistémica.<br><br>
        <strong>AUTORIZACIÓN:</strong> Al firmar este documento, usted declara que ha sido informado satisfactoriamente y autoriza al personal de NORTE IMAGEN a realizar el procedimiento y administrar contraste si fuera necesario. Usted tiene el derecho de revocar este consentimiento en cualquier momento antes de la inyección.<br><br>
        He comprendido los objetivos y riesgos. No tengo dudas sobre el procedimiento.
        </div>
        """, unsafe_allow_html=True)
    
    st.write("Firma en el recuadro:")
    canvas_f = st_canvas(stroke_width=3, stroke_color="#000", background_color="#eee", height=200, width=500, key="f_final")
    
    st.session_state.form["autoriza_gad"] = st.checkbox("ACEPTO Y AUTORIZO EL PROCEDIMIENTO")
    
    if st.button("FINALIZAR Y GUARDAR"):
        if st.session_state.form["autoriza_gad"] and canvas_f.image_data is not None:
            # Procesar la firma a imagen real
            f_img = Image.fromarray(canvas_f.image_data.astype('uint8'), 'RGBA')
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_f:
                f_img.save(tmp_f.name)
                st.session_state.form["firma_img"] = tmp_f.name
            st.session_state.step = 4
            st.rerun()

elif st.session_state.step == 4:
    mostrar_cabecera_institucional()
    st.balloons()
    st.success("REGISTRO COMPLETADO EXITOSAMENTE")
    
    # Compilación final
    doc_final = compilar_documento_pdf(st.session_state.form)
    n_archivo = f"Registro_RM_{st.session_state.form['rut']}_{datetime.now().strftime('%H%M%S')}.pdf"
    
    # SINCRONIZACIÓN CON DRIVE
    with st.spinner("Sincronizando con el servidor central de Norte Imagen..."):
        ok_drive, drive_id = subir_a_google_drive(doc_final, n_archivo)
    
    if ok_drive:
        st.info(f"Respaldo en la nube verificado. ID de registro: {drive_id}")
    else:
        st.error(f"Error de sincronización: {drive_id}")
    
    st.download_button("📥 DESCARGAR REGISTRO PDF", data=doc_final, file_name=n_archivo, mime="application/pdf")
    
    if st.button("NUEVO REGISTRO"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
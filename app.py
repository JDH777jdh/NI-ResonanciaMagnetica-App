# =====================================================================
# 1. LIBRERÍAS (Nativas, Gráficas, Drive y Firebase)
# =====================================================================
import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from fpdf import FPDF
import os
import numpy as np
import pytz
import tempfile
from PIL import Image
import re  # <--- OBLIGATORIO: Para limpiar la llave privada bajo Python 3.14

# Conectores OAuth2 para Google Drive (Módulo de respaldo de PDFs)
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Conectores para la Base de Datos Médica
import firebase_admin
from firebase_admin import credentials, firestore, storage

# =====================================================================
# 2. CONFIGURACIÓN DE PÁGINA (Regla estricta: Primer comando 'st' ejecutable)
# =====================================================================
st.set_page_config(page_title="Encuesta de Consentimiento Informado - RM", layout="centered")
<a class="btn-opcion op-tel" href="#">
        📞 A. Fernández
    </a>
    ...
</div> ```

Al faltar las etiquetas `<div class="menu-flotante">` y `<div class="opciones-contacto">`, todo el CSS corporativo que diseñamos pierde su punto de anclaje, provocando que los botones se vuelvan invisibles o queden flotando de forma caótica en el fondo de la página.

---

### 3. Solución Definitiva (El código correcto)

Para solucionar todo de una vez, abre tu archivo `app.py` y ve al **final absoluto del archivo** (abajo de todo). Pega este bloque único que contiene la estructura HTML corregida de forma estricta junto con sus estilos optimizados:

```python
# =====================================================================
# 🛟 BLOQUE FINAL: MENÚ FLOTANTE DE SOPORTE INSTITUCIONAL (NORTE IMAGEN)
# =====================================================================
st.markdown(
    """
    <style>
    /* Contenedor principal fijo en la esquina inferior derecha */
    .menu-flotante {
        position: fixed;
        bottom: 30px;
        right: 30px;
        z-index: 999999;
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 12px;
        font-family: 'Helvetica Neue', Arial, sans-serif;
    }

    /* Contenedor de las opciones ocultas por defecto */
    .opciones-contacto {
        display: flex;
        flex-direction: column;
        gap: 8px;
        opacity: 0;
        transform: translateY(20px);
        pointer-events: none;
        transition: all 0.3s ease-in-out;
    }

    /* Mostrar opciones al pasar el cursor (Hover) sobre el contenedor principal */
    .menu-flotante:hover .opciones-contacto {
        opacity: 1;
        transform: translateY(0);
        pointer-events: auto;
    }

    /* Estilo elegante y traslúcido para las opciones (Color Burdeos Corporativo con transparencia) */
    .btn-opcion {
        background-color: rgba(128, 0, 32, 0.85) !important;
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        color: #ffffff !important;
        text-decoration: none !important;
        padding: 10px 20px;
        border-radius: 30px;
        font-size: 14px;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        transition: background-color 0.2s, transform 0.2s;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        white-space: nowrap;
    }

    .btn-opcion:hover {
        background-color: rgba(128, 0, 32, 1.0) !important;
        transform: scale(1.03);
    }

    /* Botón principal visible "💬 Soporte" */
    .btn-principal {
        background-color: #800020 !important;
        color: #ffffff !important;
        border-radius: 50px;
        padding: 14px 26px;
        font-size: 16px;
        font-weight: bold;
        box-shadow: 0 6px 16px rgba(128, 0, 32, 0.35);
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 10px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: transform 0.2s, background-color 0.2s;
    }

    .btn-principal:hover {
        transform: scale(1.04);
        background-color: #940d2f !important;
    }
    </style>

    <div class="menu-flotante">
        <div class="opciones-contacto">
            <a class="btn-opcion" href="mailto:resonancia@cdnorteimagen.cl?subject=Consulta%20Registro%20RM" target="_blank">
                ✉️ resonancia@cdnorteimagen.cl
            </a>
            
            <a class="btn-opcion" href="javascript:void(0);" style="cursor: default; opacity: 0.85;">
                📞 A. Fernández
            </a>
            
            <a class="btn-opcion" href="tel:+56572466423" target="_blank">
                📞 Bilbao: +56 57 246 6423
            </a>
            
            <a class="btn-opcion" href="https://wa.me/56572466423" target="_blank">
                📱 WhatsApp Institucional
            </a>
        </div>
        
        <div class="btn-principal" title="¿Dudas o consultas acerca de tu Resonancia Magnética? Despliega las opciones">
            💬 Soporte
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
# =====================================================================
# 3. VARIABLES DE ENTORNO Y TIEMPO (Zonas Horarias y Secrets)
# =====================================================================
tz_chile = pytz.timezone('America/Santiago')
fecha_chile = datetime.now(tz_chile) 
fecha_str = fecha_chile.strftime("%d/%m/%Y")

CLIENT_ID = st.secrets["google_oauth"]["client_id"]
CLIENT_SECRET = st.secrets["google_oauth"]["client_secret"]
REDIRECT_URI = st.secrets["google_oauth"]["redirect_uri"]
ID_CARPETA_DRIVE = st.secrets["drive"]["folder_id"]
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# =====================================================================
# 4. INICIALIZACIÓN SEGURA DE FIREBASE ADMIN SDK (Código anti-caídas)
# =====================================================================
firebase_inicializado = False
if "firma_guardada" not in st.session_state:
    st.session_state["firma_guardada"] = None

try:
    # Intenta obtener la app si ya existe
    firebase_admin.get_app()
    firebase_inicializado = True
    url_bucket = st.secrets["firebase"].get("bucket_url", "firmas-encuestaconsentimiento.firebasestorage.app")
except ValueError:
    # Si no existe, inicializa
    try:
        cred_dict = dict(st.secrets["firebase"])
        url_bucket = cred_dict.get("bucket_url", "firmas-encuestaconsentimiento.firebasestorage.app")
        if "bucket_url" in cred_dict:
            del cred_dict["bucket_url"]

        if "private_key" in cred_dict and isinstance(cred_dict["private_key"], str):
            import re
            raw_key = cred_dict["private_key"]
            b64_content = re.sub(r'-----.*?PRIVATE KEY-----', '', raw_key)
            b64_content = re.sub(r'\s+', '', b64_content)
            chunks = [b64_content[i:i+64] for i in range(0, len(b64_content), 64)]
            llave_limpia = "-----BEGIN PRIVATE KEY-----\n" + "\n".join(chunks) + "\n-----END PRIVATE KEY-----\n"
            
            cred_dict["private_key"] = llave_limpia
            
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {
            'storageBucket': url_bucket
        })
        firebase_inicializado = True
    except Exception as e:
        st.error(f"🚨 Error crítico al inicializar Firebase en App Pacientes: {e}")
        st.stop()

# Conectores globales finales listos para ser usados por tus funciones inferiores
if firebase_inicializado:
    db = firestore.client()
    bucket = storage.bucket(url_bucket) if url_bucket else storage.bucket()


import streamlit as st

# Inyectar CSS para que las opciones del selectbox muestren el texto completo
st.markdown(
    """
    <style>
    /* 1. Fuerza a que la lista desplegable (abierta) use todo el ancho necesario en celulares */
    div[data-baseweb="popover"] {
        max-width: 95vw !important; /* Permite que el cuadro use hasta el 95% del ancho de la pantalla del celular */
    }
    
    div[data-baseweb="popover"] ul li {
        white-space: normal !important;   /* Permite saltos de línea */
        word-break: break-word !important; /* Rompe palabras largas si es necesario */
        line-height: 1.4 !important;      /* Un poquito más de espacio entre líneas para el dedo */
        padding-top: 12px !important;     /* Más cómodo de tocar en pantallas táctiles */
        padding-bottom: 12px !important;
    }
    
    /* 2. Hace que el texto ya seleccionado (menú cerrado) se vea completo en varias líneas */
    div[data-baseweb="select"] > div {
        white-space: normal !important;
        overflow: visible !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Norte Imagen - Registro Clínico")

# --- LÓGICA DE CONEXIÓN CON DRIVE ---
if 'credentials' not in st.session_state:
    st.session_state.credentials = None

# 1. Función para manejar el flujo de regreso de Google
query_params = st.query_params
if "code" in query_params and st.session_state.credentials is None:
    flow = Flow.from_client_config(
        {"web": {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token"}},
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    flow.fetch_token(code=query_params["code"])
    st.session_state.credentials = flow.credentials
    st.success("✅ Conectado exitosamente a la cuenta de Norte Imagen")

# 2. Función modificada para subir archivos usando TUS 15GB
def subir_a_google_drive(archivo_datos, nombre_archivo):
    if not st.session_state.credentials:
        return False, "No has iniciado sesión en Google Drive"
    
    tmp_path = None
    try:
        service = build('drive', 'v3', credentials=st.session_state.credentials)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(archivo_datos)
            tmp_path = tmp_file.name

        media = MediaFileUpload(tmp_path, mimetype='application/pdf', resumable=True)

        file_metadata = {
            'name': nombre_archivo,
            'parents': [ID_CARPETA_DRIVE]
        }

        # Aquí Google ya sabe que ERES TÚ, por lo tanto usa tus 15GB
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
            
        return True, file.get('id')

    except Exception as e:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        return False, str(e)

# --- INTERFAZ Y FORMULARIO ---
if st.session_state.credentials is None:
    st.info("⚠️ Para guardar los archivos en el almacenamiento de 15GB, debes autorizar la conexión.")
    flow = Flow.from_client_config(
        {"web": {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token"}},
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(prompt='consent')
    st.link_button("🔑 Conectar con Google Drive de Norte Imagen", auth_url)

else:
    # AQUÍ VA TODO EL RESTO DE TU CÓDIGO (Canvas, Formulario, FPDF, etc.)
    st.write(f"Fecha de registro: {fecha_str}")
    
    # Ejemplo de cómo llamarías a la función ahora:
    with st.form("mi_formulario"):
        nombre_paciente = st.text_input("Nombre Paciente")
        archivo_subido = st.file_uploader("Examen PDF")
        enviar = st.form_submit_button("Guardar en Drive")
        
        if enviar and archivo_subido:
            exito, resultado = subir_a_google_drive(archivo_subido.getvalue(), f"Examen_{nombre_paciente}.pdf")
            if exito:
                st.success(f"Guardado con ID: {resultado}")
            else:
                st.error(f"Error: {resultado}")

# 1. CONFIGURACIÓN Y ESTILOS
st.set_page_config(page_title="Norte Imagen - Registro RM", layout="centered")

st.markdown("""
    <style>
    /* Estilos Base Originales */
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

    /* Inyección Global: Cajas de Texto y Selectores */
    div[data-baseweb="input"] > div, 
    div[data-baseweb="textarea"] > div,
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1px solid #b3b3b3 !important;
        border-radius: 6px !important;
        box-shadow: inset 0px 1px 3px rgba(0, 0, 0, 0.05) !important;
    }

    /* Efecto al hacer click (Focus) corporativo */
    div[data-baseweb="input"] > div:focus-within, 
    div[data-baseweb="textarea"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-within {
        border: 2px solid #800020 !important;
        box-shadow: 0px 0px 5px rgba(128, 0, 32, 0.2) !important;
    }

    /* Inyección Global: Tags de Multiselect Azules */
    span[data-baseweb="tag"] {
        background-color: #0056b3 !important;
        border-radius: 4px !important;
        border: none !important;
    }
    span[data-baseweb="tag"] span {
        color: #ffffff !important;
        font-weight: bold;
    }
    span[data-baseweb="tag"] svg {
        fill: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. GESTIÓN DE ESTADO
if 'step' not in st.session_state: st.session_state.step = 1
if 'form' not in st.session_state:
    st.session_state.form = {
        "nombre": "", "rut": "", "sin_rut": False, "tipo_doc": "Pasaporte", "num_doc": "",
        "telefono": "", # <- NUEVO: Teléfono
        "genero_idx": 0, "sexo_bio_idx": 0, "fecha_nac": date(1990, 1, 1), "email": "", 
        "nombre_tutor": "", "rut_tutor": "", 
        "parentesco_tutor": "", "sin_rut_tutor": False, "tipo_doc_tutor": "Pasaporte", "num_doc_tutor": "", # <- NUEVO: Datos de Tutor
        "esp_idx": 0,
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

from streamlit_javascript import st_javascript

def obtener_ip_cliente():
    # Este código se ejecuta en el navegador del paciente
    url_consulta = "https://api.ipify.org?format=json"
    script_js = f'fetch("{url_consulta}").then(response => response.json()).then(data => data.ip)'
    
    ip_cliente = st_javascript(script_js)
    
    # Manejo de valor nulo mientras carga el JS
    if ip_cliente is None or ip_cliente == 0:
        return "Cargando..."
    return ip_cliente

# Sanitización de texto para PDF
def safe_text(txt):
    return str(txt).encode('latin-1', 'replace').decode('latin-1')

class PDF(FPDF):
    def header(self):
        if os.path.exists("logoNI.png"):
            self.image("logoNI.png", 10, 8, 45)
        
        # Título en dos líneas - NEGRITA activada ('B')
        self.set_font('Arial', 'B', 12)
        self.set_text_color(128, 0, 32) # Color corporativo
        
        # Línea 1
        self.cell(0, 7, 'ENCUESTA DE RIESGOS ASOCIADOS Y', 0, 1, 'R')
        # Línea 2
        self.cell(0, 7, 'CONSENTIMIENTO INFORMADO', 0, 1, 'R')
        
        # Subtítulo - NEGRITA activada ('B') y tamaño mayor (16)
        self.set_font('Arial', 'B', 16)
        self.cell(0, 8, 'RESONANCIA MAGNETICA', 0, 1, 'R')
        
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 7)
        self.set_text_color(150, 150, 150)

        ahora_pie = datetime.now(tz_chile).strftime("%d/%m/%Y %H:%M:%S")
        nombre = st.session_state.form.get('nombre', '')
        iniciales = "".join([p[0].upper() for p in nombre.split() if p])

        rut_p = st.session_state.form.get('rut', 'S/R')

        # USAR LA IP GUARDADA EN EL FORMULARIO
        ip_cliente = st.session_state.form.get("ip_dispositivo", "No detectada")

        id_registro = f"{rut_p}-{iniciales} (IP:{ip_cliente})"
        texto = f"Certificado Digital Norte Imagen - RM: {ahora_pie} - ID Registro: {id_registro} - ORIGINAL PRE-ADMISIÓN."

        self.cell(0, 10, safe_text(texto), 0, 0, 'L')
        self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}}", 0, 0, 'R')

    def section_title(self, num, label):
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(230, 230, 230)
        self.set_text_color(128, 0, 32)
        self.cell(0, 7, f"{num}. {safe_text(label)}", 0, 1, 'L', 1)
        self.ln(2)

    def data_field(self, label, value):
        self.set_font('Arial', 'B', 9)
        self.set_text_color(50, 50, 50)
        self.write(5, f"{safe_text(label)}: ")
        self.set_font('Arial', '', 9)
        self.set_text_color(0, 0, 0)
        self.write(5, f"{safe_text(value)}\n")

def generar_pdf_clinico(datos):
    pdf = PDF()
    pdf.alias_nb_pages()
    ahora_cierre = datetime.now(tz_chile)
    sello_digital = ahora_cierre.strftime("%d/%m/%Y %H:%M:%S")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=12)

    # --- PÁGINA 1: ENCABEZADO Y FECHA ---
    fecha_chile = datetime.now(tz_chile) 
    fecha_str = fecha_chile.strftime("%d/%m/%Y")
    
    # Tamaño sutil para la fecha superior
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 5, f"Fecha de examen: {fecha_str}", 0, 1, 'R') 
    pdf.ln(2)

    # 1. IDENTIFICACION DEL PACIENTE
    pdf.section_title("1", "IDENTIFICACION DEL PACIENTE")
    pdf.set_text_color(0, 0, 0)
    
    margen_izquierdo = 10
    ancho_disponible = pdf.w - 20
    w_col = (ancho_disponible - 10) / 2
    x_col2 = margen_izquierdo + w_col + 10

    # Lógica Blindada del RUT / Documento (Paciente)
    es_extranjero = datos.get('sin_rut', False)
    if es_extranjero in [True, "true", "True", "1"]:
        tipo = datos.get('tipo_doc', 'Documento')
        num = datos.get('num_doc', 'S/N')
        paciente_rut = f"{tipo}: {num}"
    else:
        paciente_rut = str(datos.get('rut', 'S/R'))

    # Extracción de variables limpias
    paciente_nombre = datos.get('nombre', 'Sin Registro')
    paciente_edad = f"{calcular_edad(datos['fecha_nac'])} años"
    fecha_nacimiento_val = datos['fecha_nac'].strftime('%d/%m/%Y')
    email_val = datos.get('email', 'S/E')
    is_contraste = st.session_state.get('tiene_contraste', False)

    # --- RENDERIZADO AL ESTILO ADMIN.PY ---
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(32, 5, "Nombre Completo: ", 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, safe_text(paciente_nombre), 0, 1)

    y_fila2 = pdf.get_y()
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(32, 5, "Documento / RUT: ", 0, 0)
    pdf.set_font('Arial', '', 9)
    pdf.cell(w_col - 32, 5, safe_text(paciente_rut), 0, 0)
    
    pdf.set_xy(x_col2, y_fila2)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(12, 5, "Edad: ", 0, 0)
    pdf.set_font('Arial', '', 9)
    pdf.cell(w_col - 12, 5, safe_text(paciente_edad), 0, 1)

    y_fila3 = pdf.get_y()
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(35, 5, "Fecha Nacimiento: ", 0, 0)
    pdf.set_font('Arial', '', 9)
    pdf.cell(w_col - 35, 5, safe_text(fecha_nacimiento_val), 0, 0)
    
    pdf.set_xy(x_col2, y_fila3)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(12, 5, "Email: ", 0, 0)
    pdf.set_font('Arial', '', 9)
    pdf.cell(w_col - 12, 5, safe_text(email_val), 0, 1)

    pdf.set_font('Arial', 'B', 9)
    pdf.cell(35, 5, "Medio de contraste: ", 0, 0)
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 5, 'SI' if is_contraste else 'NO', 0, 1)

    # Procedimiento en paralelo
    procedimiento_val = st.session_state.get('procedimiento', 'No especificado')
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(28, 5, safe_text("Procedimiento(s): "), 0, 0, 'L')
    pdf.set_font('Arial', '', 9)
    pdf.multi_cell(0, 5, safe_text(procedimiento_val), 0, 'L')
    pdf.ln(2)

    # Lógica Blindada del Tutor Legal
    rep_nombre = datos.get('nombre_tutor', '')
    if rep_nombre or calcular_edad(datos['fecha_nac']) < 18:
        pdf.ln(1)
        y_tutor = pdf.get_y()
        
        # Extracción segura RUT Tutor
        if datos.get('sin_rut_tutor'):
            rep_rut = f"{datos.get('tipo_doc_tutor', 'Doc')}: {datos.get('num_doc_tutor', 'S/R')}"
        else:
            rep_rut = datos.get('rut_tutor', 'S/R')

        pdf.set_font('Arial', 'B', 9)
        pdf.cell(28, 5, "Representante: ", 0, 0)
        pdf.set_font('Arial', '', 9)
        pdf.cell(w_col - 28, 5, safe_text(rep_nombre if rep_nombre else 'N/A'), 0, 0)
        
        pdf.set_xy(x_col2, y_tutor)
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(22, 5, "Parentesco: ", 0, 0)
        pdf.set_font('Arial', '', 9)
        pdf.cell(w_col - 22, 5, safe_text(datos.get('parentesco_tutor', 'N/A')), 0, 1)

        pdf.set_font('Arial', 'B', 9)
        pdf.cell(35, 5, "Doc. Representante: ", 0, 0)
        pdf.set_font('Arial', '', 9)
        pdf.cell(w_col - 35, 5, safe_text(rep_rut), 0, 1)



    # 2. BIOSEGURIDAD MAGNETICA
    pdf.section_title("2", "BIOSEGURIDAD MAGNETICA")
    pdf.set_font('Arial', '', 9) # Tamaño base para seguridad
    pdf.data_field("Marcapasos cardiaco", datos['bio_marcapaso'])
    pdf.data_field("Implantes metálicos, quirúrgicos, prótesis o dispositivo electrónicos", datos['bio_implantes'])
    
    # Detalle en tamaño 8 si es muy largo, para que no salte de página
    pdf.set_font('Arial', 'I', 8)
    pdf.data_field("Detalle Bioseguridad", datos['bio_detalle'] if datos['bio_detalle'] else "Sin observaciones")
    pdf.ln(2)

    # 3. ANTECEDENTES CLINICOS (Distribución en 4 Columnas)
    pdf.section_title("3", "ANTECEDENTES CLINICOS")
    pdf.set_text_color(0, 0, 0)
    
    clinicos = [
        ("Ayuno 2hrs+", datos['clin_ayuno']), ("Asma", datos['clin_asma']), ("Alergias", datos['clin_alergico']),
        ("Hipertensión", datos['clin_hiperten']), ("Hipotiroidismo", datos['clin_hipertiroid']), ("Diabetes", datos['clin_diabetes']),
        ("Metformina 48h", datos['clin_metformina']), ("Insuf. Renal", datos['clin_renal']), ("Diálisis", datos['clin_dialisis']),
        ("Embarazo", datos['clin_embarazo']), ("Lactancia", datos['clin_lactancia']), ("Claustrofobia", datos['clin_claustro'])
    ]

    col_width = pdf.w / 4.2 
    for i in range(0, len(clinicos), 4):
        linea = clinicos[i:i+4]
        for item, valor in linea:
            pdf.set_font('Arial', '', 8) # Fuente compacta para la grilla
            texto_col = f"{item}: {valor}"
            pdf.cell(col_width, 4.5, safe_text(texto_col), 0, 0)
        pdf.ln(4.5) 

    pdf.ln(2)

    # 4. ANTECEDENTES QUIRURGICOS Y TERAPEUTICOS
    pdf.section_title("4", "ANTECEDENTES QUIRURGICOS Y TERAPEUTICOS")
    pdf.set_font('Arial', '', 9)
    pdf.data_field("Cirugías", datos['quir_cirugia_check'])
    
    pdf.set_font('Arial', '', 8) # Detalle técnico más pequeño
    pdf.data_field("Detalle cirugías", datos['quir_cirugia_detalle'] if datos['quir_cirugia_detalle'] else "N/A")
    
    trats = [k for k, v in {"RT": datos['rt'], "QT": datos['qt'], "BT": datos['bt'], "IT": datos['it']}.items() if v]
    pdf.set_font('Arial', '', 9)
    pdf.data_field("Tratamientos", ", ".join(trats) if trats else "Ninguno")
    pdf.data_field("Detalle de otros tratamientos", datos['quir_otro_trat'] if datos['quir_otro_trat'] else "N/A")
    pdf.ln(2)

    # 5. EXAMENES ANTERIORES
    pdf.section_title("5", "EXAMENES ANTERIORES")
    ex_list = [k for k, v in {"Rx": datos['ex_rx'], "MG": datos['ex_mg'], "Eco": datos['ex_eco'], "TC": datos['ex_tc'], "RM": datos['ex_rm']}.items() if v]
    pdf.set_font('Arial', '', 9)
    pdf.data_field("Exámenes", ", ".join(ex_list) if ex_list else "Ninguno")
    pdf.data_field("Otros exámenes anteriores", datos['ex_otros'] if datos['ex_otros'] else "N/A")
    pdf.ln(2)

   # 6. FUNCION RENAL
    pdf.section_title("6", "EVALUACIÓN DE LA FUNCION RENAL")
    pdf.set_font('Arial', '', 9)
    
    # Validamos si el examen actual configurado requiere medio de contraste
    if st.session_state.get('tiene_contraste', False):
        crea = datos.get('creatinina')
        creatinina_val = f"{crea} mg/dL" if (crea and crea > 0) else "__________ mg/dL"
        pdf.data_field("Creatinina", creatinina_val)

        peso_real = datos.get('peso')
        peso_texto = f"{peso_real} kg" if (peso_real and peso_real > 0) else "__________ kg"
        pdf.data_field("Peso", peso_texto)

        vfg_real = datos.get('vfg')
        if vfg_real and vfg_real > 0 and peso_texto != "__________ kg":
            # Determinar color y mensaje de riesgo basado en tu lógica de la APP
            if vfg_real <= 30:
                pdf.set_text_color(255, 0, 0) # Rojo
                msg_riesgo = "ALTO RIESGO para la administración de medio de contraste"
            elif 31 <= vfg_real <= 59:
                pdf.set_text_color(184, 134, 11) # Dorado oscuro (se lee mejor en PDF que el amarillo)
                msg_riesgo = "RIESGO INTERMEDIO para la administración de medio de contraste"
            else:
                pdf.set_text_color(34, 139, 34) # Verde bosque
                msg_riesgo = "SIN RIESGOS para la administración de medio de contraste"

            # Escribimos el resultado con su mensaje al lado
            pdf.set_font('Arial', 'B', 9)
            pdf.write(5, f"V.F.G: {vfg_real:.2f} ml/min")
            pdf.set_font('Arial', 'B', 8) # Fuente un poco más pequeña para la nota
            pdf.write(5, f"  ({msg_riesgo})")
            
            # Volver a color negro para el resto del documento
            pdf.set_text_color(0, 0, 0)
            pdf.ln(5)
        else:
            pdf.data_field("RESULTADO VFG", "__________ ml/min (Cálculo manual)")
    else:
        # ESCENARIO SIN CONTRASTE: Fuerza de manera segura las líneas en blanco en el PDF
        pdf.data_field("Creatinina", "__________ mg/dL")
        pdf.data_field("Peso", "__________ kg")
        pdf.data_field("RESULTADO VFG", "__________ ml/min (Cálculo manual)")

    pdf.ln(2)

    # 7. REGISTRO DE ADMINISTRACIÓN DE MEDIO DE CONTRASTE
    pdf.section_title("7", "REGISTRO DE ADMINISTRACION DE CONTRASTE")
    pdf.set_text_color(0, 0, 0)
    
    w_col = (pdf.w - 30) / 2
    pdf.set_font('Arial', 'B', 9) 
    pdf.set_fill_color(245, 245, 245)
    
    # Encabezados
    pdf.cell(w_col, 6, safe_text(" Acceso venoso:"), 0, 0, 'L', fill=True)
    pdf.cell(10, 6, "", 0, 0) 
    pdf.cell(w_col, 6, safe_text(" Sitio de punción:"), 0, 1, 'L', fill=True)
    
    # Fila 1: Acceso y Sitio
    pdf.set_font('Arial', '', 9)
    pdf.ln(1)
    
    # Columna Izquierda: Bránula y Mariposa (distribuidos en w_col)
    opciones_acceso = "[     ] Branula: ____ G  [     ] Mariposa: ____ G"
    pdf.cell(w_col, 8, safe_text(opciones_acceso), 0, 0, 'L') 
    
    pdf.cell(10, 8, "", 0, 0) # Espacio central
    
    # Columna Derecha: Sitio de punción (línea ajustada al ancho w_col)
    pdf.cell(w_col, 8, safe_text("________________________________"), 0, 1, 'L')
    
    pdf.ln(1)
    
    # Encabezados de Contraste
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(w_col, 6, safe_text(" Medio de contraste (Intravenoso):"), 0, 0, 'L', fill=True)
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(w_col, 6, safe_text(" Cantidad administrada:"), 0, 1, 'L', fill=True)
    
    pdf.ln(1)
    pdf.set_font('Arial', '', 9)
    
    # Guardamos la posición para manejar las dos columnas en paralelo
    pos_y_bloque = pdf.get_y()
    
    # Columna Izquierda: Opciones de fármaco
    pdf.cell(w_col, 4, safe_text("[     ] Acido gadoterico (Clariscan)"), 0, 1)
    pdf.cell(w_col, 4, safe_text("[     ] Gadopiclenol (Elucirem)"), 0, 1)
    pdf.cell(w_col, 4, safe_text("[     ] Acido gadoxetico (Primovist)"), 0, 1)
    
    # Columna Derecha: Cantidad (Volvemos arriba a la derecha)
    # Usamos el ancho w_col para que la línea no se desplace
    pdf.set_xy(pdf.get_x() + w_col + 10, pos_y_bloque)
    pdf.cell(w_col, 7, safe_text("___________ ml."), 0, 1, 'L')
    
    pdf.ln(4)

    # --- PÁGINA 2 ---
    pdf.add_page()
    

  # Apartado dinámico: Procedimiento + Contraste
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0, 0, 0)
    
    texto_procedimiento = f"Procedimiento: {st.session_state.procedimiento}"
    
    if st.session_state.tiene_contraste:
        texto_procedimiento += " con uso de medio de contraste."
        pdf.multi_cell(0, 7, safe_text(texto_procedimiento), 0, 'L')
    else:
        # Escenario B: Examen simple con pregunta y cuadro a la derecha
        pdf.multi_cell(0, 7, safe_text(texto_procedimiento), 0, 'L')
        
        pdf.ln(1)
        pdf.set_font('Arial', '', 9)
        
        # 1. Escribimos la pregunta primero (sin salto de línea)
        pregunta = "¿Se aplicó medio de contraste adicionalmente?"
        ancho_texto = pdf.get_string_width(pregunta) + 2 # Calculamos cuánto mide el texto
        pdf.cell(ancho_texto, 7, safe_text(pregunta), 0, 0, 'L')
        
        # 2. Obtenemos la posición justo donde terminó el texto
        pos_x = pdf.get_x()
        pos_y = pdf.get_y()
        
        # 3. Dibujamos el rectángulo (un poco más grande: 5x5 mm)
        # Lo subimos un poco (pos_y + 1) para que alinee bien con la altura de la fuente
        pdf.rect(pos_x + 2, pos_y + 1, 5, 5) 
        
        # 4. Hacemos el salto de línea manual para que lo siguiente no se encime
        pdf.ln(8)
    
    pdf.ln(3)
    


    # Título de Advertencia
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, "LEA ATENTA Y CUIDADOSAMENTE LO SIGUIENTE:", 0, 1, 'L')
    pdf.ln(2)

    # Secciones de Información
    sections = {
        "OBJETIVOS": (
            "La Resonancia Magnética (RM) es una segura técnica de Diagnóstico, que permite la adquisición "
            "de imágenes de gran sensibilidad en todos los planos del espacio de las estructuras del cuerpo. "
            "Tiene como objetivo obtener Información, datos funcionales y morfológicos para detectar precozmente una enfermedad.\n\n"
            "Para este examen eventualmente se puede requerir la utilización de un medio de contraste paramagnético "
            "de administración endovenosa llamado gadolinio, que permite realzar ciertos tejidos del cuerpo para un mejor diagnóstico."
        ),
        "CARACTERISTICAS": (
            "La Resonancia utiliza fuertes campos magnéticos y ondas de radiofrecuencia, por lo que es muy importante "
            "dejar fuera de la sala absolutamente todo lo que lleve consigo de tipo metálico y/o electrónico (relojes, pulseras, "
            "teléfonos, tarjetas magnéticas, etc). Si lleva material de este tipo en su cuerpo (fijaciones dentales, piercings, "
            "algunos tatuajes, balas o esquirlas metálicas) ciertos tipos de prótesis (valvulares, de cadera, de rodilla, "
            "clips metálicos, etc), o implantes, así como dispositivos electrónicos de carácter médico como bombas de insulina, "
            "prótesis auditivas, marcapasos, desfibriladores, etc. Avísenos, ya que puede contraindicar de manera absoluta la realización de este examen.\n\n"
            "Usted será posicionado en la camilla del equipo, según el estudio a realizar y se colocarán cerca de la zona a estudiar "
            "unos dispositivos (bobinas) que pueden ser de diversos tamaños. Esta exploración suele ser larga (entre 20 min y 1 hr según los casos). "
            "Notará ruido derivado del funcionamiento de la RM (por lo que le facilitaremos unos protectores auditivos), todo esto es normal "
            "y se le vigilará constantemente desde la sala de control.\n\n"
            "Es muy importante que permanezca quieto durante el estudio y siga las instrucciones del Tecnólogo Médico."
        ),
        "POTENCIALES RIESGOS": (
            "Existe una muy baja posibilidad de que se presente una reacción adversa al medio de contraste (0.07-2.4%) "
            "la mayoría de carácter leve fundamentalmente nauseas o cefaleas al momento de la inyección.\n\n"
            "Pacientes con deterioro importante de la función renal, poseen riesgo de desarrollo de fibrosis nefrogénica sistémica."
        )
    }

    for tit, cont in sections.items():
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(128, 0, 32)
        pdf.cell(0, 6, safe_text(tit), 0, 1, 'L')
        pdf.set_font('Arial', '', 9)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 5, safe_text(cont))
        pdf.ln(3)

    # Declaración de consentimiento
    pdf.set_font('Arial', '', 9)
    
    # Usamos triple comilla para evitar problemas de paréntesis de cierre
    consentimiento_texto = """He sido informado de mi derecho de anular o revocar posteriormente este documento, dejándolo constatado por escrito y firmado por mi o mi representante.

Autorizo la realización del procedimiento anteriormente especificado y las acciones que sean necesarias en caso de surgir complicaciones durante el procedimiento. Además, doy consentimiento para que se administren medicamentos y/o infusiones que se requieran para la realización de este."""
    
    pdf.multi_cell(0, 5, safe_text(consentimiento_texto))
    
    # --- SECCIÓN DE FIRMAS ---
    pdf.ln(5)
    y_pos_firmas = pdf.get_y()
    
    # Rutas para el PDF
    ruta_p_local = datos.get('firma_img')
    
    # 1. ESTAMPAMOS LAS IMÁGENES PNG (Si existen)
    if ruta_p_local and os.path.exists(ruta_p_local):
        pdf.image(ruta_p_local, 35, y_pos_firmas, 45, 12)
    
    # 2. ESCRIBIMOS LOS NOMBRES SOBRE LAS LÍNEAS
    pdf.set_y(y_pos_firmas + 8)
    pdf.set_font('Arial', '', 8)
    nombre_paciente_pdf = datos.get('nombre', 'Paciente').strip()
    
    pdf.cell(95, 4, safe_text(nombre_paciente_pdf), 0, 0, 'C')
    pdf.cell(95, 4, "VALIDACIÓN DEL T.M. PENDIENTE", 0, 1, 'C')
    
    # 3. LÍNEAS DE FIRMA
    pdf.cell(95, 4, "________________________________________", 0, 0, 'C')
    pdf.cell(95, 4, "________________________________________", 0, 1, 'C')
    
    # 4. ETIQUETAS (NEGRITA)
    pdf.set_font('Arial', 'B', 8)
    pdf.cell(95, 4, safe_text("FIRMA PACIENTE O REPRESENTANTE LEGAL"), 0, 0, 'C')
    pdf.cell(95, 4, safe_text("FIRMA PROFESIONAL A CARGO"), 0, 1, 'C')
    
    # 5. DETALLES (R.L y Títulos)
    pdf.set_font('Arial', '', 8)
    nombre_tutor_pdf = datos.get('nombre_tutor', '').strip()
    
    # Columna Paciente: Tutor Legal si existe
    if nombre_tutor_pdf:
        parentesco_t_pdf = datos.get('parentesco_tutor', '').strip()
        texto_tutor = f"R.L: {nombre_tutor_pdf} ({parentesco_t_pdf})" if parentesco_t_pdf else f"R.L: {nombre_tutor_pdf}"
        pdf.cell(95, 4, safe_text(texto_tutor), 0, 0, 'C')
    else:
        pdf.cell(95, 4, "", 0, 0, 'C')
    
    # Columna Profesional: Título
    pdf.cell(95, 4, safe_text("Tecnólogo Médico en Imagenología"), 0, 1, 'C')
    
    # Segunda línea de detalles (Documentos/RUT)
    if nombre_tutor_pdf and datos.get('sin_rut_tutor'):
        texto_doc_rl = f"{datos.get('tipo_doc_tutor', 'Doc')} R.L: {datos.get('num_doc_tutor', '')}"
        pdf.cell(95, 4, safe_text(texto_doc_rl), 0, 0, 'C')
    elif nombre_tutor_pdf:
        pdf.cell(95, 4, f"R.R.L: {datos.get('rut_tutor', '')}", 0, 0, 'C')
    else:
        pdf.cell(95, 4, "", 0, 0, 'C')
        
    pdf.cell(95, 4, safe_text("Esp. Resonancia Magnética"), 0, 1, 'C')
    
    # 6. REGISTRO SIS
    pdf.cell(95, 4, "", 0, 0, 'C')
    pdf.cell(95, 4, "Registro SIS: PENDIENTE", 0, 1, 'C')
    
    pdf.ln(4)

    # --- AGREGAR ESTA LÍNEA DE CÓDIGO (LA PIEZA FALTANTE) ---
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

from streamlit_javascript import st_javascript

def obtener_ip():
    """Captura la IP real del dispositivo del paciente usando JavaScript."""
    try:
        # Intentamos vía JavaScript (Navegador del Paciente)
        url_consulta = "https://api.ipify.org?format=json"
        script_js = f'fetch("{url_consulta}").then(response => response.json()).then(data => data.ip)'
        ip_js = st_javascript(script_js)
        
        if ip_js and ip_js != 0:
            return ip_js
    except:
        pass

    # Respaldo vía Python (Servidor)
    import requests
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=2)
        return response.json()['ip']
    except:
        return "0.0.0.0"

# --- PÁGINA 1: REGISTRO ---
if st.session_state.step == 1:
    # 1. CAPTURA DE IP
    # Intentamos capturar la IP. st_javascript devolverá None o 0 al principio.
    ip_detectada = obtener_ip() 
    
    # Solo guardamos si realmente obtuvimos una IP válida
    if ip_detectada and ip_detectada not in ["Cargando...", "0.0.0.0", 0]:
        st.session_state.form["ip_dispositivo"] = ip_detectada
    else:
        # Valor por defecto temporal para que no falle el PDF si el paciente es muy rápido
        if "ip_dispositivo" not in st.session_state.form:
            st.session_state.form["ip_dispositivo"] = "Buscando IP..."
    
    # 2. INTERFAZ VISUAL
    mostrar_logo()
    st.title("Registro de Paciente")
    
    if df is not None:
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.form["nombre"] = st.text_input("Nombre Completo del Paciente", value=st.session_state.form["nombre"])
            
            # --- LÓGICA CONDICIONAL DE RUT PACIENTE (IDs ORIGINALES) ---
            st.session_state.form["sin_rut"] = st.checkbox("Sin RUT, poseo otro documento", value=st.session_state.form["sin_rut"])
            
            if st.session_state.form["sin_rut"]:
                t_opts = ["Pasaporte", "Cédula de extranjero"]
                idx_doc = t_opts.index(st.session_state.form["tipo_doc"]) if st.session_state.form["tipo_doc"] in t_opts else 0
                st.session_state.form["tipo_doc"] = st.selectbox("Tipo de documento", t_opts, index=idx_doc)
                st.session_state.form["num_doc"] = st.text_input("N° de documento", value=st.session_state.form["num_doc"])
                st.session_state.form["rut"] = ""  # Limpieza interna para evitar datos cruzados
            else:
                rut_p = st.text_input("RUT del Paciente", value=st.session_state.form["rut"], placeholder="12.345.678-K")
                st.session_state.form["rut"] = formatear_rut(rut_p)
                st.session_state.form["num_doc"] = ""
            
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
            st.session_state.form["telefono"] = st.text_input("Teléfono móvil", value=st.session_state.form["telefono"], placeholder="+56 9 1234 5678")
        
        edad = calcular_edad(st.session_state.form["fecha_nac"])
        if edad < 18:
            st.warning(f"👦 PACIENTE MENOR DE EDAD ({edad} años)")
            st.session_state.form["nombre_tutor"] = st.text_input("Nombre Representante Legal", value=st.session_state.form["nombre_tutor"])
            st.session_state.form["parentesco_tutor"] = st.text_input("Parentesco (ej. Madre, Padre, Abuelo)", value=st.session_state.form["parentesco_tutor"])
            
            # --- LÓGICA CONDICIONAL DE IDENTIFICACIÓN TUTOR ---
            st.session_state.form["sin_rut_tutor"] = st.checkbox("Representante no posee RUT", value=st.session_state.form["sin_rut_tutor"])
            
            if st.session_state.form["sin_rut_tutor"]:
                t_opts_tutor = ["Pasaporte", "Cédula de extranjero"]
                idx_doc_tutor = t_opts_tutor.index(st.session_state.form["tipo_doc_tutor"]) if st.session_state.form["tipo_doc_tutor"] in t_opts_tutor else 0
                st.session_state.form["tipo_doc_tutor"] = st.selectbox("Tipo de doc. Representante", t_opts_tutor, index=idx_doc_tutor)
                st.session_state.form["num_doc_tutor"] = st.text_input("N° documento Representante", value=st.session_state.form["num_doc_tutor"])
                st.session_state.form["rut_tutor"] = ""  # Limpia el RUT para evitar datos cruzados
            else:
                rut_tutor_input = st.text_input("RUT Representante", value=st.session_state.form["rut_tutor"], placeholder="12.345.678-K")
                st.session_state.form["rut_tutor"] = formatear_rut(rut_tutor_input)
                st.session_state.form["tipo_doc_tutor"] = "Pasaporte"
                st.session_state.form["num_doc_tutor"] = ""

        st.markdown('<div class="section-header">Información del Examen</div>', unsafe_allow_html=True)
        
        

        # 1. Recuperamos tus dos columnas originales
        ce1, ce2 = st.columns(2)
        
        esp_raw = sorted([str(e) for e in df['ESPECIALIDAD'].unique() if pd.notna(e)])
        esp_sel = ce1.selectbox("Especialidad", esp_raw, index=st.session_state.form["esp_idx"])
        st.session_state.form["esp_idx"] = esp_raw.index(esp_sel)
        
        # Filtramos
        filtered = df[df['ESPECIALIDAD'] == esp_sel]
        list_pre = sorted(filtered['PROCEDIMIENTO A REALIZAR'].dropna().unique().tolist())
        
        # FIX BUG DOBLE CLICK: Usamos un callback nativo
        if "proc_cache" not in st.session_state:
            st.session_state.proc_cache = []

        # Opciones visibles: los de la especialidad actual + los ya seleccionados para no dar error
        opciones_visibles = sorted(list(set(list_pre + st.session_state.proc_cache)))

        def sync_proc():
            # Esta función se ejecuta EXACTAMENTE en el momento que el usuario hace click
            st.session_state.proc_cache = st.session_state.widget_proc

        pre_sel = ce2.multiselect(
            "Procedimiento(s) a realizar", 
            options=opciones_visibles,
            default=st.session_state.proc_cache,
            key="widget_proc",
            on_change=sync_proc
        )
        
        # Guardamos la selección actual para que no se borre al cambiar de especialidad
        st.session_state.acumulados = pre_sel

        st.markdown('<div class="section-header">Documentación Médica</div>', unsafe_allow_html=True)
        st.file_uploader("Cargue la Orden Médica (Obligatorio)", type=["pdf", "jpg", "jpeg"], key="up_orden_p1")
        st.file_uploader("Cargue Exámenes Anteriores (Máximo 4 archivos)", type=["pdf", "jpg", "jpeg"], accept_multiple_files=True, key="up_anteriores_p1")

        if st.button("CONTINUAR"):
            if st.session_state.form["nombre"] and pre_sel:
                # Buscamos en todo el DataFrame si alguno de los exámenes seleccionados requiere contraste
                rows = df[df['PROCEDIMIENTO A REALIZAR'].isin(pre_sel)]
                st.session_state.tiene_contraste = any(str(val).upper() == "SI" for val in rows['MEDIO DE CONTRASTE'].values)
                
                # Unimos los procedimientos con coma para el motor del PDF
                st.session_state.procedimiento = ", ".join(pre_sel)
                
                st.session_state.edad_para_calculo = edad
                st.session_state.sexo_para_calculo = sexo_final
                
                # Limpiamos la variable temporal de acumulación antes de avanzar de página
                del st.session_state.acumulados
                
                st.session_state.step = 2
                st.rerun()
            elif not pre_sel:
                st.error("Por favor, seleccione al menos un procedimiento.")

# --- PÁGINA 2: CUESTIONARIO ---
elif st.session_state.step == 2:
    mostrar_logo(); st.title("📋 Cuestionario de Seguridad RM")
    opts = ["No", "Sí"]

    st.markdown('<div class="section-header">1. Bioseguridad Magnética</div>', unsafe_allow_html=True)
    st.session_state.form["bio_marcapaso"] = st.radio("Marcapasos cardiaco:", opts, index=opts.index(st.session_state.form["bio_marcapaso"]), horizontal=True)
    st.session_state.form["bio_implantes"] = st.radio("Implantes metálicos, quirúrgicos, prótesis o dispositivos electrónicos:", opts, index=opts.index(st.session_state.form["bio_implantes"]), horizontal=True)
    st.session_state.form["bio_detalle"] = st.text_area("Detalle de que tipo y ubicación:", value=st.session_state.form["bio_detalle"], height=70)

    st.markdown('<div class="section-header">2. Antecedentes Clínicos</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    k1 = [("clin_ayuno", "Ayuno (2 hrs o mas)"), ("clin_asma", "Asma"), ("clin_hiperten", "Hipertensión"), ("clin_hipertiroid", "Hipertiroidismo")]
    k2 = [("clin_diabetes", "Diabetes"), ("clin_alergico", "Alérgico"), ("clin_metformina", "Suspende metformina (48 hrs. antes)"), ("clin_renal", "Insuficiencia renal")]
    k3 = [("clin_dialisis", "Diálisis"), ("clin_claustro", "Claustrofóbico"), ("clin_embarazo", "Embarazo"), ("clin_lactancia", "Lactancia")]
    for col, keys in zip([c1, c2, c3], [k1, k2, k3]):
        for k, label in keys: st.session_state.form[k] = col.radio(label, opts, index=opts.index(st.session_state.form[k]))

    st.markdown('<div class="section-header">3. Antecedentes Quirúrgicos y/o Terapéuticos</div>', unsafe_allow_html=True)
    st.session_state.form["quir_cirugia_check"] = st.radio("¿Ha sido sometido a alguna cirugía o más de una?", opts, index=opts.index(st.session_state.form["quir_cirugia_check"]), horizontal=True)
    st.session_state.form["quir_cirugia_detalle"] = st.text_area("Detalle nombre de la cirugía y fecha:", value=st.session_state.form["quir_cirugia_detalle"], height=70)
    
    ct1, ct2, ct3, ct4 = st.columns(4)
    st.session_state.form["rt"] = ct1.checkbox("Radioterapia (RT)", value=st.session_state.form["rt"])
    st.session_state.form["qt"] = ct2.checkbox("Quimioterapia (QT)", value=st.session_state.form["qt"])
    st.session_state.form["bt"] = ct3.checkbox("Braquiterapia (BT)", value=st.session_state.form["bt"])
    st.session_state.form["it"] = ct4.checkbox("Inmunoterapia (IT)", value=st.session_state.form["it"])
    st.session_state.form["quir_otro_trat"] = st.text_input("Algún otro tratamiento que mencionar:", value=st.session_state.form["quir_otro_trat"])

    st.markdown('<div class="section-header">4. Exámenes anteriores</div>', unsafe_allow_html=True)
    ce1, ce2, ce3, ce4, ce5 = st.columns(5)
    st.session_state.form["ex_rx"] = ce1.checkbox("Radiografía (Rx)", value=st.session_state.form["ex_rx"])
    st.session_state.form["ex_mg"] = ce2.checkbox("Mamografía (MG)", value=st.session_state.form["ex_mg"])
    st.session_state.form["ex_eco"] = ce3.checkbox("Ecotomografía (Eco)", value=st.session_state.form["ex_eco"])
    st.session_state.form["ex_tc"] = ce4.checkbox("Tomografía (TC)", value=st.session_state.form["ex_tc"])
    st.session_state.form["ex_rm"] = ce5.checkbox("Resonancia (RM)", value=st.session_state.form["ex_rm"])
    st.session_state.form["ex_otros"] = st.text_input("Otros estudios:", value=st.session_state.form["ex_otros"])

    if st.session_state.tiene_contraste:
        st.markdown('<div class="section-header">5. Función Renal (VFG según Fórmula de Cockcroft-Gault)</div>', unsafe_allow_html=True)
        st.session_state.form["creatinina"] = st.number_input("Creatinina (mg/dL)", value=st.session_state.form["creatinina"], step=0.01)
        st.session_state.form["peso"] = st.number_input("Peso (kg)", value=st.session_state.form["peso"])
    
    if st.session_state.form["creatinina"] > 0:
        # Cálculo de VFG (Fórmula de Cockcroft-Gault)
        vfg = ((140 - st.session_state.edad_para_calculo) * st.session_state.form["peso"]) / (72 * st.session_state.form["creatinina"])
        if st.session_state.sexo_para_calculo == "Femenino": 
            vfg *= 0.85
        
        st.session_state.form["vfg"] = vfg

        # --- LÓGICA DE COLORES Y MENSAJES ---
        if vfg <= 30:
            estilo = "vfg-critica"  # Asegúrate que esta clase en tu CSS tenga background rojo
            mensaje = "🔴 Alto riesgo para la administración de medio de contraste"
            color_texto = "#FF0000" # Rojo
        elif 31 <= vfg <= 59:
            estilo = "vfg-intermedia" # Deberás crear esta clase o usar estilos inline
            mensaje = "⚠️ Riesgo intermedio para la administración de medio de contraste"
            color_texto = "#FFCC00" # Amarillo/Dorado
        else:
            estilo = "vfg-normal" # Deberás crear esta clase
            mensaje = "✅ Sin riesgos para la administración del medio de contraste"
            color_texto = "#28A745" # Verde

        # Renderizado en la App
        # Usamos un div con estilo dinámico para el borde/fondo y el mensaje abajo
        st.markdown(f'''
            <div class="vfg-box {estilo}" style="border-left: 10px solid {color_texto}; padding: 15px; border-radius: 5px;">
                <p style="margin:0; color: {color_texto}; font-weight: bold;">{mensaje}</p>
                <small>Resultado VFG:</small>
                <h2 style="margin:0;">{vfg:.2f} ml/min</h2>
            </div>
        ''', unsafe_allow_html=True)

    st.write("")
    col_nav = st.columns(2)
    if col_nav[0].button("ATRÁS"): st.session_state.step = 1; st.rerun()
    if col_nav[1].button("SIGUIENTE"):
        st.session_state.step = 3; st.rerun()

# --- PÁGINA 3: INFORMACIÓN Y FIRMA ---
elif st.session_state.step == 3:
    mostrar_logo(); st.title("Información al Paciente")
    st.markdown('<div class="section-header">LEA ATENTA Y CUIDADOSAMENTE LO SIGUIENTE:</div>', unsafe_allow_html=True)
    st.markdown("""
        <div class="legal-text">
        <strong>OBJETIVOS</strong><br>
        La Resonancia Magnética (RM) es una segura técnica de Diagnóstico, que permite la adquisición de imágenes de gran sensibilidad en todos los planos del espacio de las estructuras del cuerpo. Tiene como objetivo obtener Información, datos funcionales y morfológicos para detectar precozmente una enfermedad.<br>
        Para este examen eventualmente se puede requerir la utilización de un medio de contraste paramagnético de administración endovenosa llamado gadolinio, que permite realzar ciertos tejidos del cuerpo para un mejor diagnóstico.<br><br>
        <strong>CARACTERISTICAS</strong><br>
        La Resonancia utiliza fuertes campos magnéticos y ondas de radiofrecuencia, por lo que es muy importante dejar fuera de la sala absolutamente todo lo que lleve consigo de tipo metálico y/o electrónico (relojes, pulseras, teléfonos, tarjetas magnéticas, etc). Si lleva material de este tipo en su cuerpo (fijaciones dentales, piercings, algunos tatuajes, balas o esquirlas metálicas) ciertos tipos de prótesis (valvulares, de cadera, de rodilla, clips metálicos, etc), o implantes, así como dispositivos electrónicos de carácter médico como bombas de insulina, prótesis auditivas, marcapasos, desfibriladores, etc. Avísenos, ya que puede contraindicar de manera absoluta la realización de este examen.<br>
        Usted será posicionado en la camilla del equipo, según el estudio a realizar y se colocarán cerca de la zona a estudiar unos dispositivos (bobinas) que pueden ser de diversos tamaños. Esta exploración suele ser larga (entre 20 min y 1 hr según los casos). Notará ruido derivado del funcionamiento de la RM (por lo que le facilitaremos unos protectores auditivos), todo esto es normal y se le vigilará constantemente desde la sala de control.<br>
        Es muy importante que permanezca quieto durante el estudio y siga las instrucciones del Tecnólogo Médico.<br><br>
        <strong>POTENCIALES RIESGOS</strong><br>
        Existe una muy baja posibilidad de que se presente una reacción adversa al medio de contraste (0.07-2.4%) la mayoría de carácter leve fundamentalmente nauseas o cefaleas al momento de la inyección.<br>
        Pacientes con deterioro importante de la función renal, poseen riesgo de desarrollo de fibrosis nefrogénica sistémica.<br><hr>
        He sido informado de mi derecho de anular o revocar posteriormente este documento, dejándolo constatado por escrito y firmado por mi o mi representante.<br><br>
        Autorizo la realización del procedimiento anteriormente especificado y las acciones que sean necesarias en caso de surgir complicaciones durante el procedimiento. Además, doy consentimiento para que se administren medicamentos y/o infusiones que se requieran para la realización de este.
        </div>
        """, unsafe_allow_html=True)

    st.session_state.form["autoriza_gad"] = st.radio("¿Ha leído y autoriza el procedimiento?", ["SÍ", "NO"], index=None)
    st.write("Firma del Paciente / Tutor:")
    canvas_result = st_canvas(stroke_width=4, stroke_color="#000", background_color="#fff", height=150, width=400, key="canvas")
# 2. CAPTURA INMEDIATA: Guardamos los trazos en la sesión si el usuario dibujó algo
    if canvas_result is not None and canvas_result.image_data is not None:
        st.session_state["firma_guardada"] = canvas_result.image_data

    c_nav = st.columns(2)
    
    if c_nav[0].button("ATRÁS", key="btn_atras_final"): 
        st.session_state.step = 2
        st.rerun()
        
    if c_nav[1].button("FINALIZAR REGISTRO", key="btn_finalizar_final"):
        # 1. Validar la respuesta de la radio primero
        if not st.session_state.form["autoriza_gad"]:
            st.error("🚨 Por favor, responda si lee y autoriza el procedimiento antes de finalizar.")
            st.stop()
            
        # 2. Validar que la firma tenga trazos (usando la sesión segura)
        if st.session_state.form["autoriza_gad"] == "SÍ" and np.any(st.session_state["firma_guardada"][:, :, 3] > 0):
            # Convertimos la firma de la sesión en imagen temporal
            img = Image.fromarray(st.session_state["firma_guardada"].astype('uint8'), 'RGBA')
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                img.save(tmp.name)
                st.session_state.form["firma_img"] = tmp.name
            
            # Avanzamos de forma limpia al paso de guardado/éxito
            st.session_state.step = 4
            st.balloons()
            st.rerun()
        else: 
            st.error("🚨 Debe firmar en el recuadro y autorizar con 'SÍ' para poder finalizar el registro.")

# --- PÁGINA 4: FINALIZACIÓN ---
elif st.session_state.step == 4:
    mostrar_logo()
    st.success("🎉 ¡Registro Completado con Éxito!")
    
    # 1. GENERACIÓN DEL PDF EN LA MEMORIA DE FORMA INMEDIATA (CERO ESPERAS)
    pdf_bytes = generar_pdf_clinico(st.session_state.form)
    nombre_final = f"Registro_{st.session_state.form['nombre']}_{st.session_state.form['rut']}_{datetime.now().strftime('%m_%Y')}.pdf"
    
    # 2. SE ENTREGA EL BOTÓN DE DESCARGA AL PACIENTE AL INSTANTE
    st.download_button(
        label="📥 Descargar Copia PDF de Inmediato", 
        data=pdf_bytes, 
        file_name=nombre_final, 
        mime="application/pdf",
        use_container_width=True
    )
    
    st.divider()
    st.info("⏳ Sincronizando copia digital con los servidores de Resonancia Magnética... Puedes descargar tu archivo mientras tanto.")
    
# =============================================================================
    # 🚀 IMPLEMENTACIÓN DE VINCULACIÓN MAESTRA CON FIRESTORE Y STORAGE (Sincronizado)
    # =============================================================================
    ruta_firma_storage_final = ""

    # CAMBIO AQUÍ: Ahora validamos leyendo desde st.session_state en lugar de locals()
    if st.session_state.get("firma_guardada") is not None:
        try:
            # Convertir los datos del canvas guardados en la sesión a una imagen PNG limpia
            img_data = st.session_state["firma_guardada"]
            img_paciente = Image.fromarray(img_data.astype('uint8'), 'RGBA')
            
            # Guardar temporalmente en el contenedor de Streamlit
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_firma:
                img_paciente.save(tmp_firma.name)
                ruta_firma_local = tmp_firma.name

            # Estructurar una ruta interna limpia para el almacenamiento en el Bucket
            rut_limpio = str(st.session_state.form.get('rut', 'sin_rut')).replace(".", "").replace("-", "")
            timestamp_str = datetime.now(tz_chile).strftime('%Y%m%d_%H%M%S')
            nombre_blob_storage = f"firmas_pacientes/{rut_limpio}_{timestamp_str}.png"
            
            # Conectar al bucket de Firebase Storage y subir el archivo de la firma
            url_bucket = st.secrets["firebase"].get("bucket_url", "firmas-encuestaconsentimiento.firebasestorage.app")
            bucket = storage.bucket(url_bucket)
            
            blob_paciente = bucket.blob(nombre_blob_storage)
            blob_paciente.upload_from_filename(ruta_firma_local, content_type='image/png')
            
            # Guardamos la ruta interna para que admin.py la lea sin problemas
            ruta_firma_storage_final = nombre_blob_storage
            
            # Limpieza del archivo temporal local para no saturar el servidor
            try:
                os.unlink(ruta_firma_local)
            except:
                pass
                
        except Exception as e_storage:
            print(f"Error crítico al subir firma a Storage: {e_storage}")
            st.error("🚨 Hubo un problema al procesar su firma digital en los servidores. Por favor intente firmar nuevamente.")

    # 2. CONSTRUCCIÓN DE LA FICHA CLÍNICA CON LLAVES ESTRICTAS EN MINÚSCULAS
    if ruta_firma_storage_final:
        try:
            # Capturamos de forma segura las variables de st.session_state.form de tu app.py
            datos_formulario = st.session_state.form 
            
            # Obtener el VFG calculado de forma segura
            try:
                vfg_calculada = float(datos_formulario.get('vfg', 0.0))
            except:
                vfg_calculada = 0.0

            # Calculamos la edad con tu función ya existente
            edad_paciente = "N/A"
            if "fecha_nac" in datos_formulario:
                try:
                    edad_paciente = str(calcular_edad(datos_formulario["fecha_nac"]))
                except:
                    pass

            # Mapeo exacto alineado con los requerimientos de la app profesional (admin.py)
            # =====================================================================
            # 🩹 CORRECCIÓN NIVEL DIOS V2: SANITIZAR FECHA PARA FIRESTORE
            # =====================================================================
            # 1. Clonamos el formulario base con sus respuestas clínicas crudas
            payload_firestore = st.session_state.form.copy()
            
            # 2. Inyectamos y sobrescribimos con los datos validados y formateados
            payload_firestore.update({
                "rut": str(datos_formulario.get('rut', '')).strip(),
                "nombre": str(datos_formulario.get('nombre', '')).upper().strip(),
                "edad": edad_paciente,
                "telefono": str(datos_formulario.get('telefono', '')),
                "creatinina": float(datos_formulario.get('creatinina', 0.0)),
                "peso": float(datos_formulario.get('peso', 0.0)),
                "vfg": vfg_calculada,
                
                # 🔥 SOLUCIÓN CRÍTICA: Convertimos el objeto date a String de texto legible para Firestore
                "fecha_nac": st.session_state.form["fecha_nac"].strftime("%d/%m/%Y") if hasattr(st.session_state.form["fecha_nac"], "strftime") else str(st.session_state.form["fecha_nac"]),
                
                # --- INYECCIÓN PASO B: IDENTIFICACIÓN ALTERNATIVA PACIENTE ---
                "sin_rut": st.session_state.form.get("sin_rut", False),
                "tipo_doc": str(st.session_state.form.get("tipo_doc", "Pasaporte")),
                "num_doc": str(st.session_state.form.get("num_doc", "")).strip().upper(),
                
                # --- INYECCIÓN PASO C: IDENTIFICACIÓN Y LOGICA TUTOR MENOR DE EDAD ---
                "nombre_tutor": str(st.session_state.form.get("nombre_tutor", "")).upper().strip(),
                "parentesco_tutor": str(st.session_state.form.get("parentesco_tutor", "")).strip(),
                "sin_rut_tutor": st.session_state.form.get("sin_rut_tutor", False),
                "tipo_doc_tutor": str(st.session_state.form.get("tipo_doc_tutor", "Pasaporte")),
                "num_doc_tutor": str(st.session_state.form.get("num_doc_tutor", "")).strip().upper(),
                "rut_tutor": str(st.session_state.form.get("rut_tutor", "")).strip(),

                # Datos del examen que estaban sueltos en st.session_state
                "tiene_contraste": st.session_state.get("tiene_contraste", False),
                "procedimiento": str(st.session_state.get("procedimiento", "No especificado")),
                "ip_dispositivo": str(datos_formulario.get("ip_dispositivo", "IP No detectada")),
                
                # Triaje clínico mapeado a respuestas binarias estrictas "Sí" / "No"
                "alergias": "Sí" if datos_formulario.get('clin_alergico') in [True, "Sí", "si", "SI"] else "No",
                "alergias_detalles": str(datos_formulario.get('alergias_detalle', '')),
                "asma": "Sí" if datos_formulario.get('clin_asma') in [True, "Sí", "si", "SI"] else "No",
                "diabetes": "Sí" if datos_formulario.get('clin_diabetes') in [True, "Sí", "si", "SI"] else "No",
                "metformina": "Sí" if datos_formulario.get('clin_metformina') in [True, "Sí", "si", "SI"] else "No",
                "insuf_renal": "Sí" if datos_formulario.get('clin_renal') in [True, "Sí", "si", "SI"] else "No",
                "embarazo": "Sí" if datos_formulario.get('clin_embarazo') in [True, "Sí", "si", "SI"] else "No",
                
                # --- ATRIBUTOS DE CONTROL DE FLUJO SÍNCRONO ---
                "estado_validacion": "PENDIENTE",
                "encuesta_validada": False,
                "firma_img": ruta_firma_storage_final,
                "fecha_creacion": datetime.now(tz_chile).strftime("%d/%m/%Y %H:%M:%S"),
                "pdf_name": nombre_final
            })
            # =====================================================================
            
            # 3. ESCRITURA EN LA BASE DE DATOS DE FIRESTORE
            # Usamos un ID único estructurado igual que antes para mantener consistencia
            id_documento = f"{payload_firestore['rut']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 🚀 INYECCIÓN DE SEGURIDAD (Asegurando la IP en el paquete)
            # Extraemos la IP directamente desde el formulario donde sabemos que está guardada
            ip_final = str(datos_formulario.get("ip_dispositivo", "IP No detectada"))
            
            # Inyectamos la variable al diccionario que SÍ se envía a Firestore
            payload_firestore["ip_paciente"] = ip_final

            db = firestore.client()
            db.collection("encuestas").document(id_documento).set(payload_firestore)
            
            st.caption("🔹 Registro clínico y firma electrónica respaldados en Firestore con éxito.")
            
        except Exception as e_firestore:
            st.error(f"🚨 Error al guardar la ficha clínica en Firestore: {e_firestore}")
    else:
        st.error("🚨 Registro detenido: La firma digital en el recuadro es obligatoria para validar legalmente este consentimiento.")
        st.stop()

    # 4. CIRCUITO 2 ASÍNCRONO: BACKEND GOOGLE DRIVE Y ARCHIVOS ADJUNTOS
    try:
        exito, resultado = subir_a_google_drive(pdf_bytes, nombre_final)
        
        # Subir Orden Médica si existe
        if st.session_state.get("up_orden_p1"):
            orden = st.session_state["up_orden_p1"]
            subir_a_google_drive(orden.getvalue(), f"ORDEN_{st.session_state.form['rut']}_{orden.name}")
            
        # Subir Exámenes Anteriores si existen
        if st.session_state.get("up_anteriores_p1"):
            for i, exam in enumerate(st.session_state["up_anteriores_p1"]):
                subir_a_google_drive(exam.getvalue(), f"EXAM_{i}_{st.session_state.form['rut']}_{exam.name}")
        
        if exito: 
            st.caption("🔹 Archivos médicos respaldados en Google Drive.")
    except Exception as e_drive:
        print(f"Error silencioso en segundo plano con módulo Drive: {e_drive}")

    # Lanzar efectos visuales festivos para el paciente
    st.balloons()
    
    st.divider()
    # Botón para reiniciar el formulario para el siguiente paciente del hospital
    if st.button("🔄 Iniciar Nuevo Registro", use_container_width=True):
        for k in list(st.session_state.keys()): 
            del st.session_state[k]
        st.rerun()


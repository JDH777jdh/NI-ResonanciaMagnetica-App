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
DICCIONARIO_ANATOMICO = {
    # --- FEMENINOS ---
    "RODILLA": {"genero": "F", "plural": "RODILLAS"},
    "PIERNA": {"genero": "F", "plural": "PIERNAS"},
    "MANO": {"genero": "F", "plural": "MANOS"},
    "MUÑECA": {"genero": "F", "plural": "MUÑECAS"},
    "MAMA": {"genero": "F", "plural": "MAMAS"},
    "ORBITA": {"genero": "F", "plural": "ORBITAS"},
    "CADERA": {"genero": "F", "plural": "CADERAS"},
    
    # Excepciones plurales femeninas
    "EXTREMIDAD INFERIOR": {"genero": "F", "plural": "EXTREMIDADES INFERIORES"},
    "EXTREMIDAD SUPERIOR": {"genero": "F", "plural": "EXTREMIDADES SUPERIORES"},

    # --- MASCULINOS ---
    "HOMBRO": {"genero": "M", "plural": "HOMBROS"},
    "CODO": {"genero": "M", "plural": "CODOS"},
    "BRAZO": {"genero": "M", "plural": "BRAZOS"},
    "ANTEBRAZO": {"genero": "M", "plural": "ANTEBRAZOS"},
    "MUSLO": {"genero": "M", "plural": "MUSLOS"},
    "TOBILLO": {"genero": "M", "plural": "TOBILLOS"},
    "OÍDO": {"genero": "M", "plural": "OÍDOS"},
    "GLÚTEO": {"genero": "M", "plural": "GLÚTEOS"},
    
    # Excepciones plurales masculinas
    "PIÉ": {"genero": "M", "plural": "PIES"},
    "ANTEPIÉ O MEDIOPIÉ": {"genero": "M", "plural": "ANTEPIÉS O MEDIOPIÉS"},
    "DEDO (S) DE LA MANO": {"genero": "M", "plural": "DEDOS DE LAS MANOS"},
    "ORTEJO (S) DEL PIÉ": {"genero": "M", "plural": "ORTEJOS DE LOS PIES"}
}

def construir_nombre_especifico(nombre_base, lateralidad):
    """
    Toma un examen (ej: 'RM DE HOMBRO') y la lateralidad ('Derecha', 'Izquierda', 'Ambas')
    y retorna el nombre aplicando las reglas gramaticales chilenas y clínicas correctas.
    """
    if lateralidad not in ["Derecha", "Izquierda", "Ambas"]:
        return nombre_base
        
    # Buscamos qué palabra clave del diccionario está contenida en el examen base
    palabra_encontrada = None
    for clave in DICCIONARIO_ANATOMICO.keys():
        if clave in nombre_base:
            palabra_encontrada = clave
            break
            
    # Si no coincide con ninguna estructura anatómica del diccionario, añadimos la lateralidad al final
    if not palabra_encontrada:
        return f"{nombre_base} {lateralidad.upper()}"
        
    info = DICCIONARIO_ANATOMICO[palabra_encontrada]
    genero = info["genero"]
    plural = info["plural"]
    
    if lateralidad == "Ambas":
        # Caso especial: "RM DE HOMBRO" -> "RM DE AMBOS HOMBROS"
        sufijo_ambos = "AMBOS" if genero == "M" else "AMBAS"
        # Reemplazamos la palabra en singular por la versión en plural
        nuevo_nombre = nombre_base.replace(palabra_encontrada, plural)
        # Inyectamos el "AMBOS / AMBAS" justo antes del sustantivo pluralizado
        nuevo_nombre = nuevo_nombre.replace(f"DE {plural}", f"DE {sufijo_ambos} {plural}")
        return nuevo_nombre
    else:
        # Casos: "Derecha" o "Izquierda"
        # Adecuamos el sufijo según el género ("DERECHO" / "DERECHA")
        sufijo_lado = lateralidad.upper() if genero == "F" else lateralidad.upper().replace("A", "O")
        # Si termina en "OÍDO", cambia a "OÍDO DERECHO", etc.
        return f"{nombre_base} {sufijo_lado}"

# =====================================================================
# 2. CONFIGURACIÓN DE PÁGINA Y MENÚ FLOTANTE PROFESIONAL
# =====================================================================
st.set_page_config(page_title="Encuesta de Consentimiento Informado - RM", layout="centered")

st.markdown(
    """
    <style>
    /* 1. ANIMACIÓN DESTELLANTE (GLOW) - Tonos blancos y verdes suaves */
    @keyframes pulse-glow {
        0% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.6); }
        70% { box-shadow: 0 0 0 12px rgba(255, 255, 255, 0.4); } /* Fina transición a blanco translúcido */
        100% { box-shadow: 0 0 0 0 rgba(255, 255, 255, 0); }
    }

    /* 2. CONTENEDOR PRINCIPAL - POSICIÓN ELEVADA (80px) */
    .menu-flotante {
        position: fixed !important;
        bottom: 45px !important;
        right: 1px !important;
        z-index: 999999 !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: flex-end !important;
        gap: 10px !important;
    }

    /* 3. LISTA DE CONTACTOS */
    .opciones-contacto {
        display: none !important;
        flex-direction: column !important;
        gap: 8px !important;
        margin-bottom: 5px !important;
    }

    .menu-flotante:hover .opciones-contacto,
    .menu-flotante:focus-within .opciones-contacto {
        display: flex !important;
    }

    /* ESTILO PESTAÑAS (COLORES Y TRANSPARENCIA) */
    .btn-opcion {
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
        text-decoration: none !important;
        color: #333 !important; /* Texto oscuro para contrastar con fondos claros */
        font-size: 13px !important;
        font-weight: 600 !important;
        padding: 10px 15px !important;
        border-radius: 12px !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(255,255,255,0.6) !important;
        white-space: nowrap !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }
    
    /* Colores individuales de las pestañas (Llevados hacia la escala de blancos/grises/verdes claros) */
    .color-email { background-color: rgba(255, 255, 255, 0.85) !important; } /* Blanco puro */
    .color-info { background-color: rgba(233, 246, 234, 0.85) !important; } /* Verde muy suave (casi blanco) */
    .color-telefono { background-color: rgba(211, 237, 212, 0.85) !important; } /* Verde menta pálido */
    .color-whatsapp { background-color: rgba(165, 214, 167, 0.85) !important; color: #155724 !important; } /* Verde pastel intenso */

    /* 4. BOTÓN PRINCIPAL: ESCALA DE VERDE A BLANCO */
    .btn-principal {
        /* AQUÍ ESTÁ EL DEGRADADO: Empieza en verde corporativo y termina en blanco */
        background: linear-gradient(135deg, rgba(40, 167, 69, 0.8) 0%, rgba(255, 255, 255, 0.95) 100%) !important;
        
        /* Como el lado derecho es blanco, el texto debe ser verde oscuro o negro para leerse */
        color: #004d00 !important; 
        
        border-radius: 50px !important;
        padding: 14px 26px !important;
        font-weight: bold !important;
        cursor: pointer !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
        animation: pulse-glow 2s infinite !important;
        backdrop-filter: blur(5px) !important;
        
        /* Borde sutil para enmarcar el blanco */
        border: 1px solid rgba(40, 167, 69, 0.4) !important; 
        
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
    }
    </style>

    <div class="menu-flotante" tabindex="0">
        <div class="opciones-contacto">
            <a class="btn-opcion color-telefono" href="tel:+56572466423" target="_blank">
                📞 Francisco Bilbao: +56 57 246 6423
            </a>
            <a class="btn-opcion color-telefono" href="tel:+56572466425" target="_blank">
                📞 Arturo Fernández: +56 57 246 6425
            </a>
            <a class="btn-opcion color-whatsapp" href="javascript:void(0);" style="cursor: default;">
                📱 WhatsApp (Próximamente)
            </a>
            <a class="btn-opcion color-email" href="mailto:resonancia@cdnorteimagen.cl?subject=Consulta%20Registro%20RM" target="_blank">
                ✉️ resonancia.iquique@cdnorteimagen.cl
            </a>
        </div>
        <div class="btn-principal" title="Soporte Norte Imagen">
            💬 ¿Necesitas ayuda?
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
        background-color: #78909c !important;
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

# =====================================================================
# 2. GESTIÓN DE ESTADO
# =====================================================================
if 'step' not in st.session_state: st.session_state.step = 1

# 📷 LÍNEA AGREGADA DEL PASO 2 (PUNTO 1):
if 'mostrar_camara' not in st.session_state: st.session_state.mostrar_camara = False
if 'mostrar_camara_tutor' not in st.session_state: st.session_state.mostrar_camara_tutor = False

if 'form' not in st.session_state:
    st.session_state.form = {
        "condiciones": [],           # Lista vacía para el multiselect
        "condicion_detalle": "",
        "procedencia": "Ambulatorio",
        "unidad_procedencia": "",
        "quir_cirugia_check": "No",
        "quir_cirugia_detalle": "",
        "quir_cancer_check": "No",
        "quir_cancer_detalle": "",
        "rt": False,
        "qt": False,
        "bt": False,
        "it": False,
        "quir_otro_trat": "",
        "has_examenes_previos": "No",
        "ex_rx": False,
        "ex_mg": False,
        "ex_eco": False,
        "ex_tc": False,
        "ex_rm": False,
        "ex_otros": "",
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

# 📷 --- INICIO FUNCIONES NUEVAS AGREGADAS (PASO 2) --- 📷
def limpiar_datos_ocr(texto_bruto, tipo="nombre"):
    # PROTECCIÓN: Si el texto es None o está vacío, devolvemos cadena vacía y salimos
    if texto_bruto is None or texto_bruto == "":
        return ""

    # 1. Eliminar ruidos comunes (OCR artifacts)
    sucio = ["eE", "p ", " /", " / ", "  ", ";", ":"]
    limpio = str(texto_bruto) # Nos aseguramos que sea string
    for s in sucio:
        limpio = limpio.replace(s, "")
    
    # 2. Si es fecha, convertimos el mes
    if tipo == "fecha":
        meses = {"ENE":"01", "FEB":"02", "MAR":"03", "ABR":"04", "MAY":"05", "JUN":"06", 
                 "JUL":"07", "AGO":"08", "SEP":"09", "OCT":"10", "NOV":"11", "DIC":"12"}
        for mes_texto, mes_num in meses.items():
            if mes_texto in limpio.upper():
                limpio = limpio.upper().replace(mes_texto, mes_num).replace(" ", "/")
    
    return limpio.strip()

def procesar_cedula_inteligente(image_file):
    import pytesseract
    import cv2
    import numpy as np
    import re
    
    try:
        # 1. Leer imagen
        file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if img is None: return None, None, None, None
        
        # 2. Conversión Gris y MEJORA DE RESOLUCIÓN PARA CÁMARA
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Agrandamos la imagen al doble: Esto ayuda enormemente al OCR a leer fotos de cámara web
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        
        # 3. Configuración explícita
        custom_config = r'--oem 3 --psm 6 -l spa' 
        texto_extraido = pytesseract.image_to_string(gray, config=custom_config)
        
        # --- Lógica de extracción MEJORADA (Regex) ---
        
        # 1. Extracción RUT
        rut_match = re.search(r'(\d{1,2}(?:\.?\d{3}){2}\s*[-_]?\s*[\dkK])', texto_extraido)
        rut = rut_match.group(0) if rut_match else ""
        
        # 2. Extracción Sexo
        sexo = ""
        if re.search(r'\b(F|FEMENINO)\b', texto_extraido, re.IGNORECASE): sexo = "Femenino"
        elif re.search(r'\b(M|MASCULINO)\b', texto_extraido, re.IGNORECASE): sexo = "Masculino"
            
        # 3. Extracción Fecha de Nacimiento INTELIGENTE (Responde a tu duda 4)
        # Busca la palabra "NACIMIENTO" e ignora las fechas de emisión/vencimiento que están más abajo
        fecha_match = re.search(r'NACIMIENTO[^\d]{0,50}(\d{2}\s?(?:ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)\s?\d{4}|\d{2}[-/.]\d{2}[-/.]\d{4})', texto_extraido, re.IGNORECASE)
        
        # Plan B: Si la foto está muy cortada y no lee "NACIMIENTO", atrapa la primera fecha que vea
        if not fecha_match:
            fecha_match = re.search(r'(\d{2}\s?(?:ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)\s?\d{4}|\d{2}[-/.]\d{2}[-/.]\d{4})', texto_extraido, re.IGNORECASE)
        
        # Usamos group(1) porque queremos atrapar la fecha exacta
        fecha_nacimiento = fecha_match.group(1) if fecha_match else ""
        
        # 4. Extracción Apellidos (Buscamos desde APELLIDOS hasta encontrar NOMBRES)
        apellidos_match = re.search(r"APELLIDOS[\s\n]+(.*?)\s+NOMBRES", texto_extraido, re.IGNORECASE | re.DOTALL)
        apellidos_raw = apellidos_match.group(1).strip() if apellidos_match else ""
        
        # 5. Extracción Nombres (Buscamos desde NOMBRES hasta encontrar NACIONALIDAD o SEXO)
        nombres_match = re.search(r"NOMBRES[\s\n]+(.*?)\s+(NACIONALIDAD|SEXO)", texto_extraido, re.IGNORECASE | re.DOTALL)
        nombres_raw = nombres_match.group(1).strip() if nombres_match else ""
        
        nombre_completo = f"{nombres_raw} {apellidos_raw}".strip()
            
        # --- LIMPIEZA FINAL SEGURA ---
        rut_limpio = limpiar_datos_ocr(rut, "rut")
        nombre_limpio = limpiar_datos_ocr(nombre_completo, "nombre")
        fecha_limpia = limpiar_datos_ocr(fecha_nacimiento, "fecha")
        sexo_limpio = limpiar_datos_ocr(sexo, "sexo")
        
        return rut_limpio, nombre_limpio, fecha_limpia, sexo_limpio

    except Exception as e:
        print(f"ERROR CRÍTICO EN OCR: {e}")
        return None, None, None, None
# 📷 --- FIN FUNCIONES NUEVAS --- 📷

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

    # --- NUEVO: IMPRESIÓN DE PROCEDENCIA CON UNIDAD ---
    procedencia_base = datos.get('procedencia', 'AMBULATORIO').upper()
    unidad_val = datos.get('unidad_procedencia', '').strip().upper()
    
    if procedencia_base == 'HOSPITALIZADO' and unidad_val:
        texto_procedencia = f"PROCEDENCIA: {procedencia_base} (UNIDAD: {unidad_val})"
    else:
        texto_procedencia = f"PROCEDENCIA: {procedencia_base}"
        
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 5, safe_text(texto_procedencia), 0, 1, 'L') 
    pdf.ln(1)

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

    # -----------------------------------------------------------------
    # 3. ANTECEDENTES CLINICOS (Incluye condiciones especiales)
    # -----------------------------------------------------------------
    pdf.section_title("3", "ANTECEDENTES CLINICOS")
    pdf.set_text_color(0, 0, 0)
    
    # 1. Grilla de checkboxes (4 columnas)
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
            pdf.set_font('Arial', '', 8)
            texto_col = f"{item}: {valor}"
            pdf.cell(col_width, 4.5, safe_text(texto_col), 0, 0)
        pdf.ln(4.5) 

    # --- AQUÍ LA INYECCIÓN DEL DETALLE DE ALERGIA ---
    # Obtenemos el detalle desde el diccionario de datos
    detalle_alergia = datos.get('alergias_detalles', '').strip()
    
    # Solo imprimimos si el paciente marcó "Sí" en alergias y hay texto escrito
    if str(datos.get('clin_alergico', '')).upper() == "SÍ" and detalle_alergia:
        pdf.ln(2) # Pequeño espacio para separar de la grilla
        pdf.set_font('Arial', 'BI', 8) # Negrita + Cursiva para resaltar
        pdf.cell(0, 5, f"DETALLE ALERGIAS: {detalle_alergia}", ln=True, border='B')
        pdf.ln(2)
    else:
        pdf.ln(1) # Espacio normal si no hay alergias

    # 2. Integración de Condiciones y Discapacidades (Sección antes separada)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 5, "CONDICIONES O REQUERIMIENTOS ESPECIALES:", 0, 1)
    
    conds = datos.get("condiciones", [])
    detalle = datos.get("condicion_detalle", "") # Usando la clave que definimos antes
    
    pdf.set_font('Arial', '', 9)
    
    if conds or detalle:
        # Imprimir las selecciones
        if conds:
            pdf.multi_cell(0, 5, f" {', '.join(conds)}")
        
        # Imprimir el detalle si existe
        if detalle:
            pdf.set_font('Arial', 'I', 8) # Itálica para resaltar el detalle
            pdf.multi_cell(0, 5, f"Detalle: {detalle}")
    else:
        pdf.cell(0, 5, "Ninguna condición declarada.", 0, 1)

    pdf.ln(2)

    # 4. ANTECEDENTES QUIRURGICOS Y TERAPEUTICOS
    # -----------------------------------------------------------------
    # SECCIÓN 4: ANTECEDENTES QUIRÚRGICOS Y TERAPÉUTICOS (Refinado)
    # -----------------------------------------------------------------
    pdf.section_title("4", "ANTECEDENTES QUIRÚRGICOS Y TERAPÉUTICOS")
    pdf.set_font('Arial', '', 9)
    
    # 1. Cirugías
    pdf.data_field("Cirugías", datos.get('quir_cirugia_check', 'No'))
    pdf.set_font('Arial', '', 8)
    pdf.data_field("Detalle cirugías", datos.get('quir_cirugia_detalle') if datos.get('quir_cirugia_detalle') else "N/A")
    
    # 2. Cáncer
    pdf.set_font('Arial', '', 9)
    pdf.data_field("¿Cursa o ha cursado cáncer?", datos.get('quir_cancer_check', 'No'))
    
    # Solo mostramos detalle de cáncer y tratamientos SI el paciente marcó que SÍ
    if datos.get('quir_cancer_check') == 'Sí':
        pdf.set_font('Arial', '', 8)
        pdf.data_field("Detalle cáncer/etapa", datos.get('quir_cancer_detalle') if datos.get('quir_cancer_detalle') else "N/A")
        
        # 3. Tratamientos (Solo visibles si hay antecedentes de cáncer)
        trats = [k for k, v in {"RT": datos.get('rt'), "QT": datos.get('qt'), "BT": datos.get('bt'), "IT": datos.get('it')}.items() if v]
        pdf.set_font('Arial', '', 9)
        pdf.data_field("Tratamientos", ", ".join(trats) if trats else "Ninguno declarado")
        
        # Detalle tratamientos
        if datos.get('quir_otro_trat'):
            pdf.set_font('Arial', '', 8)
            pdf.data_field("Detalle otros tratamientos", datos.get('quir_otro_trat'))
            
    pdf.ln(2)

    # 5. EXAMENES ANTERIORES
    pdf.section_title("5", "EXAMENES ANTERIORES")
    pdf.set_font('Arial', '', 9)
    
    # Verificamos si el paciente indicó tener exámenes previos
    if datos.get('has_examenes_previos') == 'Sí':
        # Lista los seleccionados
        ex_list = [k for k, v in {
            "Rx": datos.get('ex_rx'), 
            "MG": datos.get('ex_mg'), 
            "Eco": datos.get('ex_eco'), 
            "TC": datos.get('ex_tc'), 
            "RM": datos.get('ex_rm')
        }.items() if v]
        
        pdf.data_field("Exámenes", ", ".join(ex_list) if ex_list else "Ninguno seleccionado")
        
        # Detalle de otros
        valor_otros = datos.get('ex_otros')
        pdf.data_field("Otros exámenes", valor_otros if valor_otros else "N/A")
        
    else:
        # Si marcó que no tiene, simplemente mostramos esta fila
        pdf.data_field("Exámenes", "No refiere exámenes anteriores")
        
    pdf.ln(2)

   # 6. FUNCION RENAL
    pdf.section_title("6", "EVALUACIÓN DE LA FUNCION RENAL")
    pdf.set_font('Arial', '', 9)
    
    # Validamos si el examen actual configurado requiere medio de contraste
    if st.session_state.get('tiene_contraste', False):
        crea = datos.get('creatinina', 0.0)
        creatinina_val = f"{crea} mg/dL" if crea > 0 else "__________ mg/dL"
        pdf.data_field("Creatinina", creatinina_val)

        # --- EXTRACCIÓN DE EDAD PARA EL PDF ---
        from datetime import date
        fecha_nac_pdf = datos.get('fecha_nac')
        hoy = date.today()
        edad_dias = (hoy - fecha_nac_pdf).days
        edad_meses = edad_dias / 30.4
        edad_anos = edad_dias / 365.25

        es_pediatrico = edad_anos < 18
        vfg_real = datos.get('vfg', 0.0)

        # --- BIFURCACIÓN: MOSTRAR TALLA O PESO ---
        if es_pediatrico:
            talla_real = datos.get('talla', 0.0)
            talla_texto = f"{talla_real} cm" if talla_real > 0 else "__________ cm"
            pdf.data_field("Talla (Pediátrico)", talla_texto)
        else:
            peso_real = datos.get('peso', 0.0)
            peso_texto = f"{peso_real} kg" if peso_real > 0 else "__________ kg"
            pdf.data_field("Peso (Adulto)", peso_texto)

        # --- RENDERIZADO DEL RESULTADO Y ALERTA ---
        if vfg_real > 0:
            msg_riesgo = ""
            r, g, b = 0, 0, 0 # Variables para el color RGB

            # A) Alertas para Lactantes (< 2 años)
            if es_pediatrico and edad_anos < 2:
                if edad_meses <= 0.25: min_n, max_n = 15, 30
                elif edad_meses <= 1: min_n, max_n = 30, 50
                elif edad_meses <= 2: min_n, max_n = 40, 65
                elif edad_meses <= 4: min_n, max_n = 55, 85
                elif edad_meses <= 12: min_n, max_n = 70, 110
                else: min_n, max_n = 85, 125

                if vfg_real < (min_n * 0.7):
                    msg_riesgo, r, g, b = "ALTO RIESGO: VFG Crítica", 255, 0, 0
                elif vfg_real < min_n:
                    msg_riesgo, r, g, b = "RIESGO INTERMEDIO: Retraso maduración", 184, 134, 11
                elif vfg_real <= max_n:
                    msg_riesgo, r, g, b = "SIN RIESGO: VFG Adecuada", 34, 139, 34
                else:
                    msg_riesgo, r, g, b = "REVISAR: Posible hiperfiltración", 0, 123, 255
            
            # B) Alertas para Mayores de 2 años y Adultos
            else:
                if vfg_real <= 30.0:
                    msg_riesgo, r, g, b = "ALTO RIESGO para medio de contraste", 255, 0, 0
                elif vfg_real <= 59.0:
                    msg_riesgo, r, g, b = "RIESGO INTERMEDIO para medio de contraste", 184, 134, 11
                else:
                    msg_riesgo, r, g, b = "SIN RIESGOS para medio de contraste", 34, 139, 34

            # Escribimos el resultado base en negro
            pdf.set_font('Arial', 'B', 9)
            pdf.write(5, f"V.F.G: {vfg_real:.2f} ml/min")
            
            # Escribimos la alerta con su color clínico correspondiente
            pdf.set_font('Arial', 'B', 8)
            pdf.set_text_color(r, g, b)
            pdf.write(5, f"  ({msg_riesgo})\n")
            
            # Volver a color negro para el resto del documento
            pdf.set_text_color(0, 0, 0)
            pdf.ln(2)
        else:
            pdf.data_field("RESULTADO VFG", "__________ ml/min (Cálculo manual)")
    else:
        # ESCENARIO SIN CONTRASTE
        pdf.data_field("Creatinina", "__________ mg/dL")
        pdf.data_field("Peso / Talla", "__________")
        pdf.data_field("RESULTADO VFG", "__________ ml/min (Sin contraste)")

    pdf.ln(2)

    # -----------------------------------------------------------------
    # 6. REGISTRO DE ADMINISTRACIÓN FARMACOLÓGICA Y EVALUACIÓN DE LA FUNCIÓN RENAL
    # -----------------------------------------------------------------
    pdf.section_title("6", "REGISTRO DE ADMINISTRACION FARMACOLOGICA Y EVALUACION DE LA FUNCION RENAL")
    pdf.set_font('Arial', '', 9)
    
    # --- A. EVALUACIÓN FUNCIÓN RENAL ---
    if st.session_state.get('tiene_contraste', False):
        crea = datos.get('creatinina', 0.0)
        pdf.data_field("Creatinina", f"{crea} mg/dL" if crea > 0 else "__________ mg/dL")

        fecha_nac_pdf = datos.get('fecha_nac')
        hoy = date.today()
        edad_anos = (hoy - fecha_nac_pdf).days / 365.25
        es_pediatrico = edad_anos < 18
        vfg_real = datos.get('vfg', 0.0)

        if es_pediatrico:
            talla_real = datos.get('talla', 0.0)
            pdf.data_field("Talla (Pediátrico)", f"{talla_real} cm" if talla_real > 0 else "__________ cm")
        else:
            peso_real = datos.get('peso', 0.0)
            pdf.data_field("Peso (Adulto)", f"{peso_real} kg" if peso_real > 0 else "__________ kg")

        if vfg_real > 0:
            # Determinación de color de alerta (Lógica simplificada para visualización)
            r, g, b = 0, 0, 0
            if es_pediatrico and edad_anos < 2:
                if vfg_real < 30: msg_riesgo, r, g, b = "ALTO RIESGO: VFG Crítica", 255, 0, 0
                elif vfg_real < 50: msg_riesgo, r, g, b = "RIESGO INTERMEDIO", 184, 134, 11
                else: msg_riesgo, r, g, b = "SIN RIESGO: Adecuada", 34, 139, 34
            else:
                if vfg_real <= 30.0: msg_riesgo, r, g, b = "ALTO RIESGO para contraste", 255, 0, 0
                elif vfg_real <= 59.0: msg_riesgo, r, g, b = "RIESGO INTERMEDIO para contraste", 184, 134, 11
                else: msg_riesgo, r, g, b = "SIN RIESGO para contraste", 34, 139, 34

            pdf.set_font('Arial', 'B', 9)
            pdf.write(5, f"V.F.G Estimada: {vfg_real:.2f} ml/min")
            pdf.set_font('Arial', 'B', 8)
            pdf.set_text_color(r, g, b)
            pdf.write(5, f"  ({msg_riesgo})\n")
            pdf.set_text_color(0, 0, 0)
        else:
            pdf.data_field("RESULTADO VFG", "__________ ml/min (Cálculo manual pendiente)")
    else:
        pdf.data_field("Creatinina", "__________ mg/dL")
        pdf.data_field("Peso / Talla", "__________")
        pdf.data_field("RESULTADO VFG", "__________ ml/min (Estudio Basal)")

    # --- B. DETALLES DE ADMINISTRACIÓN Y ACCESO (PLANTILLA VACÍA PARA TM) ---
    pdf.ln(3) 
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 6, "DETALLES DE ADMINISTRACION Y ACCESO", ln=True, border='B')
    pdf.set_font('Arial', '', 9)
    pdf.ln(2)
    
    # Renderizado en dos columnas estilo formulario en blanco
    w_col = (pdf.w - 30) / 2
    pdf.cell(w_col, 6, safe_text("Acceso Vascular: _______________________"), 0, 0, 'L')
    pdf.cell(10, 6, "", 0, 0) 
    pdf.cell(w_col, 6, safe_text("Sitio de Punción: _______________________"), 0, 1, 'L')
    pdf.ln(2)
    
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 5, "Farmacos / Insumos a Administrar (Uso exclusivo TM):", ln=True)
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 6, safe_text("• ___________________________________ | Dosis: _______ ml | Vía: _______"), ln=True)
    pdf.cell(0, 6, safe_text("• ___________________________________ | Dosis: _______ ml | Vía: _______"), ln=True)
    pdf.cell(0, 6, safe_text("• ___________________________________ | Dosis: _______ ml | Vía: _______"), ln=True)
    pdf.ln(2)

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

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    
    # -----------------------------------------------------------------
    # 1. NUEVO CAMPO: PROCEDENCIA (Distribuido lateralmente)
    # -----------------------------------------------------------------
    col_proc1, col_proc2 = st.columns(2)
    
    with col_proc1:
        # Usamos el radio horizontal que ya maneja la exclusión mutua perfectamente
        opciones_proc = ["Ambulatorio", "Hospitalizado"]
        idx_proc = opciones_proc.index(st.session_state.form.get("procedencia", "Ambulatorio"))
        
        st.session_state.form["procedencia"] = st.radio(
            "**Procedencia del Paciente:**", 
            opciones_proc, 
            index=idx_proc, 
            horizontal=True
        )
        
    with col_proc2:
        # --- LÓGICA MAGNÉTICA DE UNIDAD HOSPITALARIA ---
        if st.session_state.form["procedencia"] == "Hospitalizado":
            st.session_state.form["unidad_procedencia"] = st.text_input(
                "**Unidad y cama (Ej. UCI - C2; Medicina Varones - C10):**",
                value=st.session_state.form.get("unidad_procedencia", ""),
                key="txt_unidad_proc"
            )
        else:
            st.session_state.form["unidad_procedencia"] = "" # Limpiamos la memoria si es ambulatorio

    st.markdown("---") # Línea divisoria visual

    if df is not None:
        # =====================================================================
        # RENDERS DE CAMPOS TRADICIONALES Y MÓDULO OCR DUAL AVANZADO
        # =====================================================================
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.form["nombre"] = st.text_input("Nombre Completo del Paciente", value=st.session_state.form["nombre"])
            
            # --- LÓGICA CONDICIONAL DE RUT PACIENTE ---
            st.session_state.form["sin_rut"] = st.checkbox("Sin RUT, poseo otro documento", value=st.session_state.form["sin_rut"])
            
            if st.session_state.form["sin_rut"]:
                t_opts = ["Pasaporte", "Cédula de extranjero"]
                idx_doc = t_opts.index(st.session_state.form["tipo_doc"]) if st.session_state.form["tipo_doc"] in t_opts else 0
                st.session_state.form["tipo_doc"] = st.selectbox("Tipo de documento", t_opts, index=idx_doc)
                st.session_state.form["num_doc"] = st.text_input("N° de documento", value=st.session_state.form["num_doc"])
                st.session_state.form["rut"] = ""  
            else:
                # 📷 --- NUEVA ESTÉTICA DE BOTÓN DISCRETO --- 📷
                col_inputs, col_btn = st.columns([5, 1], vertical_alignment="bottom")
                with col_inputs:
                    rut_p = st.text_input("RUT del Paciente", value=st.session_state.form["rut"], placeholder="12.345.678-K")
                    st.session_state.form["rut"] = formatear_rut(rut_p)
                    st.session_state.form["num_doc"] = ""
                with col_btn:
                    # 🎨 CSS para agrandar SOLO la cámara sin inflar el tamaño del botón
                    st.markdown("""
                        <style>
                        /* Apuntamos al botón usando exactamente el texto de tu parámetro 'help' */
                        button[title="Escanea tu carnet de identidad"] p {
                            font-size: 32px !important; /* Hace el emoji de la cámara mucho más grande */
                            line-height: 1 !important;  /* Evita que el botón crezca a lo alto */
                            margin: 0 !important;
                            padding: 0 !important;
                        }
                        </style>
                    """, unsafe_allow_html=True)
                    
                    # Botón pequeño solo con icono y burbuja de ayuda
                    if st.button("📷", help="Escanea tu carnet de identidad", key="btn_disparar_cam", use_container_width=True):
                        st.session_state.mostrar_camara = True
                        st.rerun()

            # --- Lógica Asíncrona: Cámara y Plan B ---
            if not st.session_state.form["sin_rut"] and st.session_state.mostrar_camara:
                st.markdown("---")
                st.info("💡 **Enfoque la cédula completa.** Evite que los focos de luz reflejen directamente en el plástico.")
                
                opcion_carga = st.radio("Método de escaneo:", ["📷 Usar Cámara", "📁 Subir Foto (Galería)"], horizontal=True)
                
                foto_capturada = None
                if opcion_carga == "📷 Usar Cámara":
                    # Al quitar las columnas, permitimos que el navegador use el 100% 
                    # del espacio y Safari debería mostrar los controles nativos.
                    foto_capturada = st.camera_input("Tome la foto de su cédula", key="lector_cam_webrtc")

                    # Burbuja de ayuda integrada para el Tutor (mismo formato profesional)
                    with st.expander("ℹ️ ¿Problemas con la cámara?"):
                        st.markdown("""
                        Si no logras ver el botón para girar la cámara en tu iPad:
                        1. Toca el botón **'AA'** en la barra de direcciones de Safari.
                        2. Asegúrate de seleccionar **'Sitio web para móviles'**.
                        3. Si persiste, utiliza la opción **'📁 Subir Foto'**; esto abrirá la cámara nativa de tu dispositivo donde podrás elegir la cámara trasera fácilmente.
                        """)
                else:
                    foto_capturada = st.file_uploader("Seleccione la foto frontal de su cédula", type=["jpg", "png", "jpeg"])

                # --- LÓGICA DE PROCESAMIENTO AUTOMÁTICO (CORREGIDA) ---
                # ¡OJO! La sangría ahora está correcta, dentro del bloque principal
                if foto_capturada is not None:
                    c_cam1, c_cam2 = st.columns(2)
                    
                    with c_cam1:
                        # Protegemos con el session_state para que analice solo una vez por foto
                        if st.session_state.get("archivo_procesado") != foto_capturada.name:
                            with st.spinner("⚡ Analizando documento de forma segura..."):
                                import time
                                from datetime import datetime
                                
                                # Llamamos a la función UNA SOLA VEZ y extraemos los 4 valores
                                rut, nombre, fecha, sexo = procesar_cedula_inteligente(foto_capturada)
                                
                                if rut or sexo or nombre:
                                    # Inyectamos directamente al diccionario del formulario
                                    if rut: 
                                        st.session_state.form["rut"] = rut
                                    if nombre: 
                                        st.session_state.form["nombre"] = nombre
                                    if sexo: 
                                        st.session_state.form["genero_biologico"] = sexo
                                    if fecha:
                                        try:
                                            # Convertimos el string a objeto date para el calendario
                                            parsed_date = datetime.strptime(fecha, "%d/%m/%Y").date()
                                            
                                            # 🛡️ BLINDAJE MILIMÉTRICO: Evitar que el OCR asigne una fecha futura (ej. vencimiento)
                                            from datetime import date
                                            if date(1910, 1, 1) <= parsed_date <= date.today():
                                                st.session_state.form["fecha_nac"] = parsed_date
                                        except:
                                            pass
                                    
                                    # Marcamos como procesado y apagamos la cámara para romper el bucle
                                    st.session_state.archivo_procesado = foto_capturada.name
                                    st.session_state.mostrar_camara = False
                                    
                                    st.success("✅ Datos extraídos correctamente. Cerrando escáner...")
                                    time.sleep(1.5)
                                    st.rerun()
                                else:
                                    st.error("❌ No logramos extraer los datos. Intente con mejor iluminación o ciérrelo e ingrese los datos manualmente arriba.")
                                    # Lo marcamos procesado igual para no entrar en bucle de error
                                    st.session_state.archivo_procesado = foto_capturada.name
                    
                    with c_cam2:
                        if st.button("❌ Cerrar Escáner", key="btn_close_cam", use_container_width=True):
                            st.session_state.mostrar_camara = False
                            st.rerun()
                st.markdown("---")
            # 📷 --- FIN NUEVA LÓGICA --- 📷
            
            # --- MANEJO DE IDENTIDAD DE GÉNERO E INCLUSIÓN ---
            g_opts = ["Masculino", "Femenino", "No binario"]
            gen_sel = st.selectbox("Identidad de Género", g_opts, index=st.session_state.form["genero_idx"])
            st.session_state.form["genero_idx"] = g_opts.index(gen_sel)
            sexo_final = gen_sel
            
            if gen_sel == "No binario":
                sb_opts = ["Masculino", "Femenino"]
                
                # INTELIGENCIA DE TRASPASO
                ocr_sexo_detectado = st.session_state.form.get("genero_biologico")
                if ocr_sexo_detectado in sb_opts:
                    idx_default_bio = sb_opts.index(ocr_sexo_detectado)
                else:
                    idx_default_bio = st.session_state.form["sexo_bio_idx"]
                
                sexo_bio = st.selectbox("Sexo asignado al nacer (Para fines clínicos)", sb_opts, index=idx_default_bio)
                st.session_state.form["sexo_bio_idx"] = sb_opts.index(sexo_bio)
                st.session_state.form["genero_biologico"] = sexo_bio  
                sexo_final = sexo_bio

        with c2:
            st.session_state.form["fecha_nac"] = st.date_input("Fecha de Nacimiento", value=st.session_state.form["fecha_nac"], min_value=date(1910, 1, 1), max_value=date.today(), format="DD/MM/YYYY")
            st.session_state.form["email"] = st.text_input("Email de contacto", value=st.session_state.form["email"])
            st.session_state.form["telefono"] = st.text_input("Teléfono móvil", value=st.session_state.form["telefono"], placeholder="+56 9 1234 5678")
        
        # --- SECCIÓN MENOR DE EDAD Y TUTOR LEGAL ---
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
                st.session_state.form["rut_tutor"] = ""  
            else:
                # 📷 --- BOTÓN DISCRETO TUTOR --- 📷
                col_inp_tutor, col_btn_tutor = st.columns([5, 1], vertical_alignment="bottom")
                with col_inp_tutor:
                    rut_tutor_input = st.text_input("RUT Representante", value=st.session_state.form["rut_tutor"], placeholder="12.345.678-K")
                    st.session_state.form["rut_tutor"] = formatear_rut(rut_tutor_input)
                    st.session_state.form["tipo_doc_tutor"] = "Pasaporte"
                    st.session_state.form["num_doc_tutor"] = ""
                with col_btn_tutor:
                    if st.button("📷", help="Escanea el carnet del representante", key="btn_cam_tutor", use_container_width=True):
                        st.session_state.mostrar_camara_tutor = True
                        st.rerun()

            # Lógica Asíncrona Tutor
            if not st.session_state.form["sin_rut_tutor"] and st.session_state.get("mostrar_camara_tutor", False):
                st.markdown("---")
                st.info("💡 **Enfoque la cédula completa del representante.** Evite reflejos de luz.")
                
                # Agregamos la misma consistencia para elegir entre cámara o galería
                opcion_carga_tutor = st.radio("Método de escaneo (Tutor):", ["📷 Usar Cámara", "📁 Subir Foto (Galería)"], horizontal=True, key="radio_tutor")
                
                if opcion_carga_tutor == "📷 Usar Cámara":
                    # Mantenemos el componente libre (sin columnas) para que Safari en iPad
                    # detecte que tiene espacio suficiente para renderizar todos los controles.
                    foto_tutor = st.camera_input("Tome la foto de su cédula (Tutor)", key="cam_webrtc_tut")
                    
                    # Burbuja de ayuda integrada para el Tutor (mismo formato profesional)
                    with st.expander("ℹ️ ¿Problemas con la cámara del tutor?"):
                        st.markdown("""
                        Si no logras ver el botón para girar la cámara en tu iPad:
                        1. Toca el botón **'AA'** en la barra de direcciones de Safari.
                        2. Asegúrate de seleccionar **'Sitio web para móviles'**.
                        3. Si persiste, utiliza la opción **'📁 Subir Foto'**; esto abrirá la cámara nativa de tu dispositivo donde podrás elegir la cámara trasera fácilmente.
                        """)
                else:
                    foto_tutor = st.file_uploader("Seleccione la foto frontal de su cédula", type=["jpg", "png", "jpeg"], key="up_webrtc_tut")
                
                # Aplicamos la misma protección de bucle que en el paciente principal
                if foto_tutor is not None:
                    c_cam_t1, c_cam_t2 = st.columns(2)
                    with c_cam_t1:
                        # Evitar bucle infinito verificando si ya procesamos esta imagen
                        if st.session_state.get("archivo_procesado_tutor") != foto_tutor.name:
                            with st.spinner("⚡ Procesando OCR de forma segura..."):
                                import time
                                
                                # ¡CORRECCIÓN! Desempaquetamos los 4 valores (aunque solo usemos 2)
                                rut_tutor, nombre_tutor, fecha_tutor, sexo_tutor = procesar_cedula_inteligente(foto_tutor)
                                
                                if rut_tutor or nombre_tutor:
                                    if rut_tutor:
                                        st.session_state.form["rut_tutor"] = rut_tutor
                                        st.success(f"✅ RUT detectado: {rut_tutor}")
                                    if nombre_tutor:
                                        # Aprovechamos de auto-rellenar también el nombre del tutor
                                        st.session_state.form["nombre_tutor"] = nombre_tutor
                                        st.success(f"✅ Nombre detectado: {nombre_tutor}")
                                    
                                    # Marcamos como procesado y cerramos la cámara
                                    st.session_state.archivo_procesado_tutor = foto_tutor.name
                                    st.session_state.mostrar_camara_tutor = False
                                    
                                    time.sleep(1.5)
                                    st.rerun()
                                else:
                                    st.error("❌ No se detectaron datos. Intente con mejor iluminación o ingréselos manualmente.")
                                    # Lo marcamos procesado igual para no entrar en bucle de error
                                    st.session_state.archivo_procesado_tutor = foto_tutor.name
                    
                    with c_cam_t2:
                        if st.button("❌ Cerrar Escáner", key="btn_close_tut", use_container_width=True):
                            st.session_state.mostrar_camara_tutor = False
                            st.rerun()
                st.markdown("---")

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

        # =====================================================================
        # SUMA ADITIVA: CONTROL TOGGLE NATIVO Y REEMPLAZO SWAP EN TIEMPO REAL
        # =====================================================================
        if pre_sel:
            if "lateralidades_finales" not in st.session_state:
                st.session_state.lateralidades_finales = {}
            if "nombres_transformados" not in st.session_state:
                st.session_state.nombres_transformados = {}

            for examen in pre_sel:
                fila_csv = df[df['PROCEDIMIENTO A REALIZAR'] == examen]
                if not fila_csv.empty and fila_csv.iloc[0].get('REQUIERE_LATERALIDAD', 'NO') == 'SI':
                    
                    # Generación de claves únicas sanitizadas por examen
                    clave_limpia = examen.replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')
                    key_ambas = f"chk_ambas_{clave_limpia}"
                    key_toggle = f"tgl_lado_{clave_limpia}"
                    
                    # 1. EVALUACIÓN PREVIA PARA EL EFECTO SWAP (SALE UNO, ENTRA OTRO)
                    es_bilateral = st.session_state.get(key_ambas, False)
                    toggle_activo = st.session_state.get(key_toggle, False)
                    
                    # Mapeo lógico del toggle: False = Derecha / True = Izquierda
                    lado_activo = "Izquierda" if toggle_activo else "Derecha"
                    lat_actual = "Ambas" if es_bilateral else lado_activo
                    
                    # Calculamos el nombre modificado gramaticalmente
                    nombre_final_calculado = construir_nombre_especifico(examen, lat_actual)
                    
                    # Guardamos en tus estructuras globales de sesión para Firebase y PDF
                    st.session_state.lateralidades_finales[examen] = lat_actual
                    st.session_state.nombres_transformados[examen] = nombre_final_calculado
                    
                    # DESPLIEGUE CON EFECTO SWAP (Letra compacta a 0.9rem como pediste)
                    st.markdown(
                        f"<p style='font-size: 0.9rem; margin-bottom: 2px;'><b>PROCEDIMIENTO:</b> {nombre_final_calculado}</p>", 
                        unsafe_allow_html=True
                    )
                    
                    # 2. DISTRIBUCIÓN HORIZONTAL CON TOGGLE Y CHECKBOX ALINEADOS
                    c_txt1, c_tgl, c_txt2, c_divisor, c_chk = st.columns([0.6, 0.6, 0.7, 0.2, 2.5])
                    
                    with c_txt1:
                        # Opacidad reducida si el componente completo está bloqueado por marcar "Ambos"
                        color_txt1 = "#999" if es_bilateral else "#333"
                        st.markdown(f"<p style='margin-top: 4px; font-size: 0.85rem; text-align: right; color: {color_txt1};'>DERECHA</p>", unsafe_allow_html=True)
                        
                    with c_tgl:
                        # Renderizamos el Toggle sin label para una perfecta alineación lateral
                        st.toggle(
                            label="Lado Examen",
                            key=key_toggle,
                            disabled=es_bilateral,
                            label_visibility="collapsed"
                        )
                        
                    with c_txt2:
                        color_txt2 = "#999" if es_bilateral else "#333"
                        st.markdown(f"<p style='margin-top: 4px; font-size: 0.85rem; text-align: left; color: {color_txt2};'>IZQUIERDA</p>", unsafe_allow_html=True)
                        
                    with c_divisor:
                        st.markdown("<p style='margin-top: 2px; color: #ccc; font-size: 1.1rem; text-align: center;'>|</p>", unsafe_allow_html=True)
                        
                    with c_chk:
                        st.checkbox(
                            "AMBOS (AS)", 
                            key=key_ambas
                        )
                        
                    st.markdown("<div style='border-bottom: 1px dashed #e0e0e0; margin: 10px 0;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">Documentación Médica</div>', unsafe_allow_html=True)
        st.file_uploader("Cargue la Orden Médica (Obligatorio)", type=["pdf", "jpg", "jpeg"], key="up_orden_p1")
        

        if st.button("CONTINUAR"):
            if st.session_state.form["nombre"] and pre_sel:
                
                # =====================================================================
                # 🚀 NUEVO: SALVAR ARCHIVOS EN MEMORIA ANTES DE CAMBIAR DE PÁGINA
                # =====================================================================
                # 1. Orden Médica
                if st.session_state.get("up_orden_p1") is not None:
                    st.session_state["orden_persistente"] = {
                        "name": st.session_state["up_orden_p1"].name,
                        "bytes": st.session_state["up_orden_p1"].getvalue()
                    }
                else:
                    st.session_state["orden_persistente"] = None
                
                # 2. Exámenes Anteriores (Es una lista, iteramos con un for)
                if st.session_state.get("up_anteriores_p1") is not None:
                    st.session_state["examenes_persistentes"] = []
                    for archivo_exam in st.session_state["up_anteriores_p1"]:
                        st.session_state["examenes_persistentes"].append({
                            "name": archivo_exam.name,
                            "bytes": archivo_exam.getvalue()
                        })
                else:
                    st.session_state["examenes_persistentes"] = []
                # =====================================================================

                # Buscamos en todo el DataFrame si alguno de los exámenes seleccionados requiere contraste
                rows = df[df['PROCEDIMIENTO A REALIZAR'].isin(pre_sel)]
                st.session_state.tiene_contraste = any(str(val).upper() == "SI" for val in rows['MEDIO DE CONTRASTE'].values)
                
                # Unimos los procedimientos con coma para el motor del PDF
                # Extracción con lógica de lateralidad aplicada
                nombres_finales = []
                for ex in pre_sel:
                    if "nombres_transformados" in st.session_state and ex in st.session_state.nombres_transformados:
                        nombres_finales.append(st.session_state.nombres_transformados[ex])
                    else:
                        nombres_finales.append(ex)
                
                st.session_state.procedimiento = ", ".join(nombres_finales)
                
                st.session_state.edad_para_calculo = edad
                st.session_state.sexo_para_calculo = sexo_final
                
                # Limpiamos la variable temporal de acumulación antes de avanzar de página
                del st.session_state.acumulados
                
                st.session_state.step = 2
                st.rerun()
            elif not pre_sel:
                st.error("Por favor, seleccione al menos un procedimiento.")

elif st.session_state.step == 2:
    mostrar_logo(); st.title("📋 Cuestionario de Seguridad RM")
    opts = ["No", "Sí"]

    st.markdown('<div class="section-header">1. Bioseguridad Magnética</div>', unsafe_allow_html=True)

    # 1. Marcapasos cardiaco
    # Convertimos el radio a booleano para el toggle
    is_marcapaso = st.session_state.form.get("bio_marcapaso") == "Sí"
    bio_marcapaso_toggle = st.toggle("Marcapasos cardiaco", value=is_marcapaso)
    st.session_state.form["bio_marcapaso"] = "Sí" if bio_marcapaso_toggle else "No"

    # 2. Implantes metálicos
    is_implante = st.session_state.form.get("bio_implantes") == "Sí"
    bio_implante_toggle = st.toggle("Implantes metálicos, quirúrgicos, prótesis o dispositivos electrónicos", value=is_implante)
    st.session_state.form["bio_implantes"] = "Sí" if bio_implante_toggle else "No"

    # 3. Detalle (Solo aparece si alguna de las dos opciones anteriores es "Sí")
    # Si cualquiera de los dos toggles está activo, mostramos el cuadro de detalle
    if st.session_state.form["bio_marcapaso"] == "Sí" or st.session_state.form["bio_implantes"] == "Sí":
        st.session_state.form["bio_detalle"] = st.text_area(
            "Detalle de qué tipo y ubicación:", 
            value=st.session_state.form.get("bio_detalle", ""), 
            height=70
        )
    else:
        # Si el paciente apaga los toggles, limpiamos el detalle automáticamente
        st.session_state.form["bio_detalle"] = ""

    st.markdown('<div class="section-header">2. Antecedentes Clínicos</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    k1 = [("clin_ayuno", "Ayuno (2 hrs o mas)"), ("clin_asma", "Asma"), ("clin_hiperten", "Hipertensión"), ("clin_hipertiroid", "Hipertiroidismo")]
    k2 = [("clin_diabetes", "Diabetes"), ("clin_alergico", "Alérgico"), ("clin_metformina", "Suspende metformina (48 hrs. antes)"), ("clin_renal", "Insuficiencia renal")]
    k3 = [("clin_dialisis", "Diálisis"), ("clin_claustro", "Claustrofóbico"), ("clin_embarazo", "Embarazo"), ("clin_lactancia", "Lactancia")]
    
    for col, keys in zip([c1, c2, c3], [k1, k2, k3]):
        for k, label in keys:
            # 1. Leemos y pasamos a booleano
            valor_actual_bool = (st.session_state.form.get(k) == "Sí")
            # 2. Renderizamos el Toggle
            resultado_toggle = col.toggle(label, value=valor_actual_bool, key=k)
            # 3. Guardamos como "Sí" o "No"
            st.session_state.form[k] = "Sí" if resultado_toggle else "No"

            # 🚀 INYECCIÓN LÓGICA DE ALERGIAS (Se renderiza dentro de la columna 2)
            if k == "clin_alergico":
                if st.session_state.form["clin_alergico"] == "Sí":
                    st.session_state.form["alergias_detalle"] = col.text_input(
                        "⚠️ Especifique alergias (Fármacos/Alimentos):", 
                        value=st.session_state.form.get("alergias_detalle", "")
                    )
                else:
                    st.session_state.form["alergias_detalle"] = "" # Limpieza si apaga el toggle

    # -----------------------------------------------------------------
    # NUEVA INTEGRACIÓN: CONDICIONES ESPECIALES (Dentro de Sección 2)
    # -----------------------------------------------------------------
    st.markdown("<br>", unsafe_allow_html=True) # Espacio visual
    st.markdown("**¿Posee alguna condición o requerimiento especial?**")
    
    # Toggle Maestro para activar la sección
    toggle_condicion = st.toggle("Sí, deseo indicar una condición especial", key="toggle_cond")
    
    if toggle_condicion:
        opciones_condicion = [
            "Discapacidad física o movilidad reducida (ej.: uso de silla de ruedas, amputaciones, secuelas motoras)",
            "Condición del neurodesarrollo o neurodivergencia (ej.: TEA, TDAH, dislexia)",
            "Discapacidad intelectual o cognitiva",
            "Discapacidad sensorial (ej.: visual, auditiva)",
            "Otra"
        ]
        
        # Multiselect
        st.session_state.form["condiciones"] = st.multiselect(
            "Seleccione todas las que correspondan:", 
            opciones_condicion, 
            default=st.session_state.form.get("condiciones", [])
        )
        
        # Cuadro de detalle (Siempre disponible si el toggle está activo)
        st.session_state.form["condicion_detalle"] = st.text_input(
            "Detalle de la condición o requerimiento:", 
            value=st.session_state.form.get("condicion_detalle", "")
        )
    else:
        # Limpiamos los datos si el paciente apaga el toggle
        st.session_state.form["condiciones"] = []
        st.session_state.form["condicion_detalle"] = ""

    st.markdown('<div class="section-header">3. Antecedentes Quirúrgicos y/o Terapéuticos</div>', unsafe_allow_html=True)

    # 1. Convertimos el valor actual de la base de datos a booleano para el toggle
    is_cirugia = st.session_state.form.get("quir_cirugia_check") == "Sí"
    
    # 2. Renderizamos el toggle
    cirugia_toggle = st.toggle("¿Ha sido sometido a alguna cirugía o más de una?", value=is_cirugia)
    
    # 3. Actualizamos el estado con el valor esperado por tu backend ("Sí"/"No")
    st.session_state.form["quir_cirugia_check"] = "Sí" if cirugia_toggle else "No"

    # 4. Detalle (Solo aparece si el toggle está activo)
    if st.session_state.form["quir_cirugia_check"] == "Sí":
        st.session_state.form["quir_cirugia_detalle"] = st.text_area(
            "Detalle nombre de la cirugía y fecha:", 
            value=st.session_state.form.get("quir_cirugia_detalle", ""), 
            height=70
        )
    else:
        # Limpiamos el detalle si el usuario desactiva la opción
        st.session_state.form["quir_cirugia_detalle"] = ""

    # -----------------------------------------------------------------
    # 4. PREGUNTA DE CÁNCER (Con lógica de Switchbox)
    # -----------------------------------------------------------------
    # Convertimos a booleano
    is_cancer = st.session_state.form.get("quir_cancer_check") == "Sí"
    
    # Renderizamos el toggle
    cancer_toggle = st.toggle("¿Usted cursa o ha cursado alguna enfermedad de cáncer?", value=is_cancer)
    
    # Actualizamos el estado con el valor estándar
    st.session_state.form["quir_cancer_check"] = "Sí" if cancer_toggle else "No"

    # -----------------------------------------------------------------
    # LÓGICA INTEGRADA: CÁNCER Y TRATAMIENTOS
    # -----------------------------------------------------------------
    
    # 1. Pregunta principal de Cáncer
    # (Suponiendo que el toggle ya definió st.session_state.form["quir_cancer_check"])
    
    if st.session_state.form["quir_cancer_check"] == "Sí":
        # A. Detalle del cáncer
        st.session_state.form["quir_cancer_detalle"] = st.text_area(
            "Detalle tipo de cáncer y etapa:", 
            value=st.session_state.form.get("quir_cancer_detalle", ""), 
            height=70
        )
        
        # B. Pregunta de tratamientos (Aparece solo si es Sí)
        st.markdown("**¿Has tenido que realizarte alguno de estos tratamientos?**")
        
        ct1, ct2, ct3, ct4 = st.columns(4)
        st.session_state.form["rt"] = ct1.checkbox("Radioterapia (RT)", value=st.session_state.form.get("rt", False))
        st.session_state.form["qt"] = ct2.checkbox("Quimioterapia (QT)", value=st.session_state.form.get("qt", False))
        st.session_state.form["bt"] = ct3.checkbox("Braquiterapia (BT)", value=st.session_state.form.get("bt", False))
        st.session_state.form["it"] = ct4.checkbox("Inmunoterapia (IT)", value=st.session_state.form.get("it", False))
        
        st.session_state.form["quir_otro_trat"] = st.text_input(
            "Algún otro tratamiento que mencionar:", 
            value=st.session_state.form.get("quir_otro_trat", "")
        )
        
    else:
        # C. LIMPIEZA AUTOMÁTICA (Si no hay cáncer, borramos todo rastro de tratamientos)
        st.session_state.form["quir_cancer_detalle"] = ""
        st.session_state.form["rt"] = False
        st.session_state.form["qt"] = False
        st.session_state.form["bt"] = False
        st.session_state.form["it"] = False
        st.session_state.form["quir_otro_trat"] = ""

    st.markdown('<div class="section-header">4. Exámenes anteriores</div>', unsafe_allow_html=True)

    is_previos = st.session_state.form.get("has_examenes_previos") == "Sí"
    toggle_previos = st.toggle("¿Tiene exámenes anteriores relacionados a la Resonancia Magnética que se va a realizar hoy?", value=is_previos)
    st.session_state.form["has_examenes_previos"] = "Sí" if toggle_previos else "No"

    if st.session_state.form["has_examenes_previos"] == "Sí":
        st.markdown("*Seleccione los que tiene, ya sea en formato digital o físico.*")
        
        ce1, ce2, ce3, ce4, ce5 = st.columns(5)
        st.session_state.form["ex_rx"] = ce1.checkbox("Radiografía (Rx)", value=st.session_state.form.get("ex_rx", False))
        st.session_state.form["ex_mg"] = ce2.checkbox("Mamografía (MG)", value=st.session_state.form.get("ex_mg", False))
        st.session_state.form["ex_eco"] = ce3.checkbox("Ecotomografía (Eco)", value=st.session_state.form.get("ex_eco", False))
        st.session_state.form["ex_tc"] = ce4.checkbox("Tomografía Computarizada (TC)", value=st.session_state.form.get("ex_tc", False))
        st.session_state.form["ex_rm"] = ce5.checkbox("Resonancia Magnética (RM)", value=st.session_state.form.get("ex_rm", False))
        st.session_state.form["ex_otros"] = st.text_input("Otros estudios:", value=st.session_state.form.get("ex_otros", ""))
        
        # =====================================================================
        # 📂 NUEVA SECCIÓN DE CARGA DE EXÁMENES (ARCHIVOS Y LINKS)
        # =====================================================================
        st.markdown("---")
        st.markdown("**A. Archivos Ligeros (Informes en PDF o Fotos)**")
        st.file_uploader("Adjunte sus informes (Máx. 4)", type=["pdf", "jpg", "jpeg"], accept_multiple_files=True, key="up_anteriores_p2")
        
        st.markdown("**B. Archivos Pesados (Links a Portales Externos o DICOM)**")
        st.info("💡 Si su examen está en la nube (ej. Integramédica, RedSalud, etc.), pegue los datos de acceso aquí para no saturar su dispositivo.")
        
        col_l1, col_p1 = st.columns([3, 1])
        st.session_state.form["link_exam_1"] = col_l1.text_input("🔗 Link de visualización 1:", value=st.session_state.form.get("link_exam_1", ""), placeholder="https://...")
        st.session_state.form["pin_exam_1"] = col_p1.text_input("🔑 PIN / Clave 1:", value=st.session_state.form.get("pin_exam_1", ""), placeholder="Ej: 1234")

        col_l2, col_p2 = st.columns([3, 1])
        st.session_state.form["link_exam_2"] = col_l2.text_input("🔗 Link de visualización 2 (Opcional):", value=st.session_state.form.get("link_exam_2", ""))
        st.session_state.form["pin_exam_2"] = col_p2.text_input("🔑 PIN / Clave 2:", value=st.session_state.form.get("pin_exam_2", ""))
        # =====================================================================

    else:
        st.session_state.form["ex_rx"] = False
        st.session_state.form["ex_mg"] = False
        st.session_state.form["ex_eco"] = False
        st.session_state.form["ex_tc"] = False
        st.session_state.form["ex_rm"] = False
        st.session_state.form["ex_otros"] = ""
        st.session_state.form["link_exam_1"] = ""
        st.session_state.form["pin_exam_1"] = ""
        st.session_state.form["link_exam_2"] = ""
        st.session_state.form["pin_exam_2"] = ""
        # =====================================================================


    if st.session_state.tiene_contraste:
        # 1. Título dinámico según la edad
        if st.session_state.edad_para_calculo < 18:
            titulo_vfg = "5. Función Renal (VFG Pediátrica / Maduración)"
        else:
            titulo_vfg = "5. Función Renal (VFG Adulto según Ecuación Cockcroft-Gault)"
            
        st.markdown(f'<div class="section-header">{titulo_vfg}</div>', unsafe_allow_html=True)
        
        # 2. Pedimos la Creatinina (común para todos)
        st.session_state.form["creatinina"] = st.number_input("Creatinina (mg/dL)", value=float(st.session_state.form.get("creatinina", 0.0)), step=0.01)
        
        vfg = 0.0
        mensaje = ""
        color_texto = ""
        estilo = ""
        
        # ---------------------------------------------------------
        # 3. EXTRACCIÓN MILIMÉTRICA DE EDAD (Días, Meses, Años)
        # Usamos el objeto fecha_nac que ya existe en el form
        # ---------------------------------------------------------
        from datetime import date
        fecha_nac_vfg = st.session_state.form["fecha_nac"]
        hoy = date.today()
        edad_dias = (hoy - fecha_nac_vfg).days
        edad_meses = edad_dias / 30.4
        edad_anos = edad_dias / 365.25

        # =========================================================
        # 4. BIFURCACIÓN Y CÁLCULO CLÍNICO AVANZADO (Motor admin.py)
        # =========================================================
        if edad_anos < 18:
            st.warning("👶 Paciente pediátrico/lactante detectado. Se solicitará talla en centímetros.")
            st.session_state.form["talla"] = st.number_input("Talla (cm)", value=float(st.session_state.form.get("talla", 0.0)), step=0.5)
            st.session_state.form["peso"] = 0.0 # Bloqueamos peso en BD para pediatría
            
            creatinina_val = st.session_state.form["creatinina"]
            talla_val = st.session_state.form["talla"]
            
            if creatinina_val > 0 and talla_val > 0:
                # A) LACTANTES (< 2 años) - Schwartz Clásica (Maduración)
                if edad_anos < 2:
                    if edad_dias <= 28:
                        k = 0.33 if edad_dias < 7 else 0.45
                    else:
                        k = 0.45 if edad_meses <= 12 else 0.55
                        
                    vfg = (k * talla_val) / creatinina_val
                    
                    # Sistema de Alertas Estricto para Maduración Neonatal
                    if edad_meses <= 0.25: min_n, max_n = 15, 30
                    elif edad_meses <= 1: min_n, max_n = 30, 50
                    elif edad_meses <= 2: min_n, max_n = 40, 65
                    elif edad_meses <= 4: min_n, max_n = 55, 85
                    elif edad_meses <= 12: min_n, max_n = 70, 110
                    else: min_n, max_n = 85, 125
                    
                    if vfg < (min_n * 0.7):
                        estilo, mensaje, color_texto = "vfg-critica", "🔴 ALTO RIESGO: VFG Crítica para etapa de maduración", "#FF0000"
                    elif vfg < min_n:
                        estilo, mensaje, color_texto = "vfg-intermedia", "⚠️ RIESGO INTERMEDIO: Retraso en maduración renal", "#FFCC00"
                    elif vfg <= max_n:
                        estilo, mensaje, color_texto = "vfg-normal", "✅ SIN RIESGO: VFG Adecuada para la edad", "#28A745"
                    else:
                        estilo, mensaje, color_texto = "vfg-normal", "🔵 REVISAR: Posible hiperfiltración", "#007BFF"

                # B) PEDIÁTRICOS MAYORES (2 a 17 años) - Schwartz Bedside 2009
                else:
                    vfg = (0.413 * talla_val) / creatinina_val
                    
                    if vfg <= 30.0:
                        estilo, mensaje, color_texto = "vfg-critica", "🔴 Alto riesgo para administración de medio de contraste", "#FF0000"
                    elif vfg <= 59.0:
                        estilo, mensaje, color_texto = "vfg-intermedia", "⚠️ Riesgo intermedio para administración de medio de contraste", "#FFCC00"
                    else:
                        estilo, mensaje, color_texto = "vfg-normal", "✅ Sin riesgos para administración de medio de contraste", "#28A745"
                        
                st.session_state.form["vfg"] = vfg

        else:
            # C) ADULTOS (>= 18 años) - Cockcroft-Gault
            st.session_state.form["peso"] = st.number_input("Peso (kg)", value=float(st.session_state.form.get("peso", 0.0)), step=0.1)
            st.session_state.form["talla"] = 0.0 # Bloqueamos talla en BD para adultos
            
            creatinina_val = st.session_state.form["creatinina"]
            peso_val = st.session_state.form["peso"]
            
            if creatinina_val > 0 and peso_val > 0:
                es_mujer = st.session_state.sexo_para_calculo in ['Femenino', 'No binario (Bio: Femenino)']
                factor = 0.85 if es_mujer else 1.0
                vfg = (((140 - int(edad_anos)) * peso_val) / (72 * creatinina_val)) * factor
                st.session_state.form["vfg"] = vfg
                
                if vfg <= 30.0:
                    estilo, mensaje, color_texto = "vfg-critica", "🔴 Alto riesgo para administración de medio de contraste", "#FF0000"
                elif vfg <= 59.0:
                    estilo, mensaje, color_texto = "vfg-intermedia", "⚠️ Riesgo intermedio para administración de medio de contraste", "#FFCC00"
                else:
                    estilo, mensaje, color_texto = "vfg-normal", "✅ Sin riesgos para administración de medio de contraste", "#28A745"

        # =========================================================
        # 5. RENDERIZADO VISUAL DEL PACIENTE (Triaje Real)
        # =========================================================
        if vfg > 0:
            st.markdown(f'''
                <div class="vfg-box {estilo}" style="border-left: 10px solid {color_texto}; padding: 15px; border-radius: 5px;">
                    <p style="margin:0; color: {color_texto}; font-weight: bold;">{mensaje}</p>
                    <small>Resultado VFG Estimada:</small>
                    <h2 style="margin:0;">{vfg:.2f} ml/min</h2>
                </div>
            ''', unsafe_allow_html=True)

    st.write("")
    col_nav = st.columns(2)
    if col_nav[0].button("ATRÁS"): st.session_state.step = 1; st.rerun()
    if col_nav[1].button("SIGUIENTE"):
        # =====================================================================
        # 🚀 INTERCEPTAR ARCHIVOS DE EXÁMENES ANTES DE CAMBIAR DE PÁGINA
        # =====================================================================
        if st.session_state.get("up_anteriores_p2") is not None:
            st.session_state["examenes_persistentes"] = []
            for archivo_exam in st.session_state["up_anteriores_p2"]:
                st.session_state["examenes_persistentes"].append({
                    "name": archivo_exam.name,
                    "bytes": archivo_exam.getvalue()
                })
        else:
            st.session_state["examenes_persistentes"] = []
            
        st.session_state.step = 3
        st.rerun()

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
    
    # =====================================================================
    # ✅ NUEVO: CHECKBOX DE VERACIDAD LEGAL (SIN EMOJI)
    # =====================================================================

    # 1. Inyección de estilo (Ajustado para buscar el texto sin emoji)
    st.markdown("""
        <style>
        /* El selector :has() busca el texto específico sin el emoji */
        div[data-testid="stCheckbox"]:has(label[title*="Verifico que todos los datos ingresados"]) div[role="checkbox"][aria-checked="true"] {
            background-color: #28a745 !important;
            border-color: #28a745 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # 2. Checkbox (Texto limpio, sin el ✅)
    st.markdown("<br>", unsafe_allow_html=True)
    st.session_state.form["veracidad"] = st.checkbox(
        "**Verifico que todos los datos ingresados son fidedignos y corresponden a mi estado de salud actual.**", 
        value=st.session_state.form.get("veracidad", False),
        key="chk_veracidad_legal"
    )
    st.markdown("<br>", unsafe_allow_html=True)

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
        # 1. Validar la respuesta del selector de autorización primero
        if not st.session_state.form.get("autoriza_gad"):
            st.error("🚨 Por favor, responda si lee y autoriza el procedimiento antes de finalizar.")
            st.stop()
            
        # 2. Validar casilla de veracidad obligatoria (Declaración fidedigna)
        if not st.session_state.form.get("veracidad"):
            st.error("🚨 Es obligatorio confirmar que los datos ingresados son fidedignos marcando la casilla de verificación.")
            st.stop()
            
        # 3. Validar que la firma tenga trazos físicos reales (analizando el canal alfa > 0)
        firma_valida = False
        if st.session_state.get("firma_guardada") is not None:
            # np.any verifica si hay algún píxel dibujado que no sea transparente
            if np.any(st.session_state["firma_guardada"][:, :, 3] > 0):
                firma_valida = True

        # Ejecutar la transición de almacenamiento si todo es correcto legalmente
        if st.session_state.form["autoriza_gad"] == "SÍ" and firma_valida:
            # Convertimos la firma de la sesión en imagen con formato RGBA
            img = Image.fromarray(st.session_state["firma_guardada"].astype('uint8'), 'RGBA')
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                img.save(tmp.name)
                st.session_state.form["firma_img"] = tmp.name
            
            # Avanzamos de forma limpia al paso de guardado/éxito (Página 4)
            st.session_state.step = 4
            st.balloons()
            st.rerun()
        else: 
            st.error("🚨 Debe verificar haber llenado todos los campos obligatorios, también dibujar su firma manualmente en el recuadro y autorizar con 'SÍ' para poder finalizar el registro.")

# --- PÁGINA 4: FINALIZACIÓN ---
elif st.session_state.step == 4:
    mostrar_logo()
    st.success("🎉 ¡Registro Completado con Éxito!")
    
    # =====================================================================
    # 📄 GENERACIÓN DE ID UNIVERSAL (RUT O PASAPORTE) Y NOMENCLATURA
    # =====================================================================
    # Lógica de extracción de ID limpia sin romper si el paciente es extranjero
    id_paciente_file = st.session_state.form.get('rut') if not st.session_state.form.get('sin_rut') else st.session_state.form.get('num_doc')
    if not id_paciente_file: 
        id_paciente_file = "SIN_ID"
    
    # Sanitización de caracteres para nombres de archivos e indexación en base de datos
    id_paciente_limpio = str(id_paciente_file).replace(".", "").replace("-", "").strip()

    # 1. GENERACIÓN DEL PDF EN LA MEMORIA DE FORMA INMEDIATA (CERO ESPERAS)
    try:
        # =====================================================================
        # 🧠 INYECCIÓN INTELIGENTE DE GÉNERO ANTES DE COMPILAR EL PDF
        # =====================================================================
        idx_gen_p4 = str(st.session_state.form.get('genero_idx', '0'))
        idx_bio_p4 = str(st.session_state.form.get('sexo_bio_idx', '0'))
        ocr_bio_p4 = str(st.session_state.form.get('genero_biologico', '')).strip().capitalize()
        
        if idx_gen_p4 == "1":
            sexo_formateado = "Femenino"
        elif idx_gen_p4 == "2" or str(st.session_state.form.get('sexo')) == "No binario":
            # Si es No Binario, rescatamos el sexo biológico (vía OCR o vía selectbox de respaldo)
            if ocr_bio_p4 in ["Masculino", "Femenino"]:
                sexo_bio_str = ocr_bio_p4
            else:
                sexo_bio_str = "Femenino" if idx_bio_p4 == "1" else "Masculino"
            
            sexo_formateado = f"No binario (Bio: {sexo_bio_str})"
        else:
            sexo_formateado = "Masculino"

        # Inyectamos el string definitivo en el formulario para que lo lea 'generar_pdf_clinico'
        st.session_state.form["sexo_pdf_format"] = sexo_formateado
        # Como resguardo, si tu función usa la llave 'sexo' o 'genero', las actualizamos también:
        st.session_state.form["sexo"] = sexo_formateado
        st.session_state.form["genero"] = sexo_formateado
        # =====================================================================

        # Compilación nativa del documento en memoria
        pdf_bytes = generar_pdf_clinico(st.session_state.form)
        st.session_state.pdf_bytes_data = pdf_bytes  # Guardamos en estado para persistencia
    except Exception as e_pdf:
        st.error(f"Error crítico al compilar el PDF: {e_pdf}")
        st.stop()

    # Definición original restaurada
    nombre_final = f"Registro_{st.session_state.form['nombre']}_{id_paciente_limpio}_{datetime.now().strftime('%m_%Y')}.pdf"
    st.session_state.pdf_filename = nombre_final
    
    st.divider()
    st.info("⏳ Sincronizando copia digital con los servidores de Resonancia Magnética... Puedes descargar tu archivo mientras tanto.")
    
# =============================================================================
    # 🚀 IMPLEMENTACIÓN DE VINCULACIÓN MAESTRA CON FIRESTORE Y STORAGE (Sincronizado)
    # =============================================================================
    
    # 🛡️ INICIO CANDADO ANTI-DUPLICACIÓN 🛡️
    # Verificamos si la variable existe, si no, la creamos en False
    if "registro_guardado_db" not in st.session_state:
        st.session_state.registro_guardado_db = False

    # Todo el bloque de guardado se ejecuta SOLO si el candado está abierto (False)
    if not st.session_state.registro_guardado_db:
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
                
                # =====================================================================
                # 🚀 PASO 1 (CORREGIDO): SUBIDA DE ORDEN MÉDICA A FIREBASE STORAGE
                # =====================================================================
                rut_paciente = str(datos_formulario.get('rut', 'sin_rut')).replace(".", "").replace("-", "")
                timestamp_archivos = datetime.now(tz_chile).strftime('%Y%m%d_%H%M%S')
                
                ruta_orden_firebase_final = ""
                if st.session_state.get("orden_persistente") is not None:
                    try:
                        archivo_orden = st.session_state["orden_persistente"]
                        nombre_original = archivo_orden["name"]
                        _, ext = os.path.splitext(nombre_original)
                        ext = ext.lower() if ext else ".pdf"
                        
                        ruta_orden_firebase_final = f"ordenes_medicas/{rut_paciente}_{timestamp_archivos}_orden{ext}"
                        blob_orden = bucket.blob(ruta_orden_firebase_final)
                        ct = 'application/pdf' if ext == '.pdf' else f'image/{ext.replace(".", "")}'
                        blob_orden.upload_from_string(archivo_orden["bytes"], content_type=ct)
                    except Exception as e_orden:
                        print(f"Error al subir orden: {e_orden}")
                        
                # =====================================================================
                # 🚀 PASO 1.5: SUBIDA DE EXÁMENES ANTERIORES A FIREBASE STORAGE
                # =====================================================================
                rutas_examenes_firebase = [] # Lista para guardar todas las rutas
                if st.session_state.get("examenes_persistentes"):
                    for idx, archivo_exam in enumerate(st.session_state["examenes_persistentes"]):
                        try:
                            nombre_orig = archivo_exam["name"]
                            _, ext = os.path.splitext(nombre_orig)
                            ext = ext.lower() if ext else ".pdf"
                            
                            ruta_exam = f"examenes_anteriores/{rut_paciente}_{timestamp_archivos}_exam{idx+1}{ext}"
                            blob_exam = bucket.blob(ruta_exam)
                            ct = 'application/pdf' if ext == '.pdf' else f'image/{ext.replace(".", "")}'
                            blob_exam.upload_from_string(archivo_exam["bytes"], content_type=ct)
                            
                            rutas_examenes_firebase.append(ruta_exam)
                        except Exception as e_exam:
                            print(f"Error al subir examen {idx+1}: {e_exam}")
                # =====================================================================

                # 1. Clonamos el formulario base con sus respuestas clínicas crudas
                payload_firestore = st.session_state.form.copy()
                
                # 2. Inyectamos y sobrescribimos con los datos validados y formateados
                payload_firestore.update({
                    "rt": "Sí" if st.session_state.form.get("rt", False) else "No",
                    "qt": "Sí" if st.session_state.form.get("qt", False) else "No",
                    "bt": "Sí" if st.session_state.form.get("bt", False) else "No",
                    "it": "Sí" if st.session_state.form.get("it", False) else "No",
                    "url_orden_firebase": ruta_orden_firebase_final, 
                    "url_examenes_firebase": rutas_examenes_firebase, # <--- AQUI SE GUARDAN LOS EXAMENES EN LA BD
                    "link_exam_1": str(st.session_state.form.get("link_exam_1", "")),
                    "pin_exam_1": str(st.session_state.form.get("pin_exam_1", "")),
                    "link_exam_2": str(st.session_state.form.get("link_exam_2", "")),
                    "pin_exam_2": str(st.session_state.form.get("pin_exam_2", "")),
                    "url_orden_firebase": ruta_orden_firebase_final, # <--- AQUI SE GUARDA LA RUTA EN LA BD
                    "has_examenes_previos": st.session_state.form.get("has_examenes_previos", "No"),
                    "ex_rx": st.session_state.form.get("ex_rx", False),
                    "ex_mg": st.session_state.form.get("ex_mg", False),
                    "ex_eco": st.session_state.form.get("ex_eco", False),
                    "ex_tc": st.session_state.form.get("ex_tc", False),
                    "ex_rm": st.session_state.form.get("ex_rm", False),
                    "ex_otros": str(st.session_state.form.get("ex_otros", "")),
                    "procedencia": str(datos_formulario.get('procedencia', 'Ambulatorio')), # <--- NUEVO
                    "unidad_procedencia": str(datos_formulario.get('unidad_procedencia', '')).strip().upper(), # <--- NUEVO
                    "bio_marcapaso": st.session_state.form.get('bio_marcapaso', 'No'),
                    "bio_implantes": st.session_state.form.get('bio_implantes', 'No'),
                    "quir_cirugia_check": st.session_state.form.get('quir_cirugia_check', 'No'),
                    "quir_cirugia_detalle": str(st.session_state.form.get('quir_cirugia_detalle', '')),
                    "quir_cancer_check": st.session_state.form.get('quir_cancer_check', 'No'),
                    "quir_cancer_detalle": str(st.session_state.form.get('quir_cancer_detalle', '')),
                    "rut": str(datos_formulario.get('rut', '')).strip(),
                    "nombre": str(datos_formulario.get('nombre', '')).upper().strip(),
                    "edad": edad_paciente,
                    "telefono": str(datos_formulario.get('telefono', '')),
                    "creatinina": float(datos_formulario.get('creatinina', 0.0)),
                    "peso": float(datos_formulario.get('peso', 0.0)),
                    "talla": float(datos_formulario.get('talla', 0.0)),
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
        
        # 🔒 CERRAMOS EL CANDADO PARA QUE NO SE REPITA AL DESCARGAR EL PDF
        st.session_state.registro_guardado_db = True

    # ---- FUERA DEL CANDADO (SIEMPRE SE MUESTRA EL BOTÓN) ----
    st.divider()
    # Botón para reiniciar el formulario para el siguiente paciente del hospital
    if st.button("🔄 Iniciar Nuevo Registro", use_container_width=True):
        for k in list(st.session_state.keys()): 
            del st.session_state[k]
        st.rerun()

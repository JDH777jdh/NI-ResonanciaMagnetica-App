# =============================================================================
# COPYRIGHT (c) 2026 [JONATHAN HAROLD ENRIQUE DÍAZ HUAMÁN]. 
# ARQUITECTURA V2: SPA, HL7 FHIR, AES-256 Y AISLAMIENTO UUID.
# =============================================================================

import streamlit as st
import uuid
import json
import base64
import os
from datetime import datetime, date
import pytz

# Dependencias Criptográficas y de Base de Datos (BLOQUE 2)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import firebase_admin
from firebase_admin import credentials, firestore, storage
import pandas as pd
import pytesseract
import cv2
import numpy as np
import re
import requests
import smtplib
from email.message import EmailMessage
import random

# =====================================================================
# 1. CONFIGURACIÓN MAESTRA DE PÁGINA (Debe ser la línea 1 ejecutable)
# =====================================================================
dir_actual = os.path.dirname(__file__)
ruta_logo = os.path.join(dir_actual, "logoNI_pg.png")

st.set_page_config(
    page_title="Norte Imagen - Registro RM",
    page_icon=ruta_logo if os.path.exists(ruta_logo) else "🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =====================================================================
# 2. INYECCIÓN DE CSS GLOBAL (DRY - Don't Repeat Yourself)
# =====================================================================
def inyectar_css_corporativo():
    """Centraliza todo el estilo para evitar inyecciones múltiples en el código."""
    fondo_dinamico = "#ffffff" if st.session_state.get("step", 0) == 0 else "#f5f5f5"
    
    st.markdown(f"""
        <style>
        /* Reseteo de Tema Claro Forzado */
        html, body, [class*="css"], .stApp, .stMarkdown, p, span, div, label, li {{ color: #333333 !important; }}
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{ background-color: {fondo_dinamico} !important; }}
        
        /* Botones Corporativos */
        .stButton>button {{ 
            background-color: #800020 !important; 
            color: #ffffff !important; 
            border-radius: 8px; 
            width: 100%; 
            height: 3em; 
            font-weight: bold; 
            transition: all 0.3s ease;
        }}
        .stButton>button:hover {{ box-shadow: 0px 4px 12px rgba(128, 0, 32, 0.4) !important; transform: translateY(-2px); }}
        .stButton > button * {{ color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; }}
        
        /* Tipografía Clínica */
        h1 {{ color: #000000 !important; text-align: center; }}
        h2, h3, .section-header {{ color: #800020 !important; border-bottom: 2px solid #800020 !important; margin-top: 25px; margin-bottom: 15px; font-weight: bold; }}
        
        /* Cajas de Alerta VFG */
        .vfg-box {{ background-color: #ffffff !important; padding: 20px; border-radius: 10px; border: 2px solid #800020 !important; text-align: center; margin-top: 20px; }}
        
        /* Ajuste de Tabs (Pestañas) */
        .stTabs [data-baseweb="tab-list"] {{ gap: 20px; }}
        .stTabs [data-baseweb="tab"] {{
            height: 50px;
            white-space: pre-wrap;
            background-color: #F8F9FA;
            border-radius: 4px 4px 0px 0px;
            padding: 10px 20px;
            color: #333333;
        }}
        .stTabs [aria-selected="true"] {{ background-color: #800020 !important; color: #FFFFFF !important; font-weight: bold; }}
        
        /* Forzar color oscuro en inputs */
        input, select, textarea {{ color: #333333 !important; }}
        </style>
    """, unsafe_allow_html=True)

# =====================================================================
# 3. GESTOR DE ESTADO AISLADO (ANTI-CRUCE DE PACIENTES)
# =====================================================================
def inicializar_sesion_segura():
    """Crea un contenedor hermético para cada paciente conectado."""
    if "paciente_uuid" not in st.session_state:
        st.session_state.paciente_uuid = str(uuid.uuid4())
    
    if "step" not in st.session_state:
        st.session_state.step = 0
        
    if "form" not in st.session_state:
        st.session_state.form = {
            "rut_titular": "", "nombre_titular": "", "fecha_nac": None, "genero_biologico": "",
            "requiere_tutor": False, "rut_tutor": "", "nombre_tutor": "",
            "recursos_hl7": [], "tiene_contraste": False, "nombres_transformados": {},
            "peso": 0.0, "talla": 0.0, "creatinina": 0.0, "fecha_creatinina": None
        }
    if "fes_codigo_generado" not in st.session_state:
        st.session_state.fes_codigo_generado = None
    if "fes_validado" not in st.session_state:
        st.session_state.fes_validado = False

# Ejecución inmediata
inyectar_css_corporativo()
inicializar_sesion_segura()

# =====================================================================
# 4. CONEXIÓN SINGLETON A FIREBASE (Escalabilidad Concurrente) - CORREGIDO
# =====================================================================
@st.cache_resource
def inicializar_firebase():
    """Abre UNA SOLA conexión global hiper-rápida para todos los pacientes."""
    try:
        # Verifica si ya existe para evitar errores de doble inicialización
        return firebase_admin.get_app()
    except ValueError:
        try:
            # Intentar obtener credenciales. Si fallan, atrapamos el error.
            cred_dict = dict(st.secrets["firebase"])
            url_bucket = cred_dict.pop("bucket_url", "firmas-encuestaconsentimiento.firebasestorage.app")
            
            # Limpieza segura de la llave privada
            if "private_key" in cred_dict:
                cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
                
            cred = credentials.Certificate(cred_dict)
            return firebase_admin.initialize_app(cred, {'storageBucket': url_bucket})
        except (KeyError, FileNotFoundError):
            # En lugar de romperse, mostrará un mensaje amigable y permitirá que la UI siga cargando
            st.error("⚠️ Atención: Credenciales de Firebase no configuradas en st.secrets.")
            return None
        except Exception as e:
            st.error(f"🚨 Error inesperado conectando a Firebase: {e}")
            return None

# Inicializamos la base de datos (incluso si falla, las variables quedarán en None pero la App no se caerá)
app_firebase = inicializar_firebase()
db = firestore.client() if app_firebase else None
bucket = storage.bucket() if app_firebase else None

# =====================================================================
# 5. MOTOR CRIPTOGRÁFICO AES-256 (Grado Militar)
# =====================================================================
class GestorCriptografico:
    def __init__(self):
        try:
            key_hex = st.secrets["aes"]["master_key"]
        except:
            key_hex = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
            
        self.key = bytes.fromhex(key_hex)
        self.aesgcm = AESGCM(self.key)

    def encriptar(self, datos_dict: dict) -> str:
        nonce = os.urandom(12)
        datos_bytes = json.dumps(datos_dict, default=str).encode('utf-8')
        texto_cifrado = self.aesgcm.encrypt(nonce, datos_bytes, None)
        return base64.b64encode(nonce + texto_cifrado).decode('utf-8')

    def desencriptar(self, cadena_encriptada: str) -> dict:
        datos_crudos = base64.b64decode(cadena_encriptada)
        nonce, texto_cifrado = datos_crudos[:12], datos_crudos[12:]
        datos_descifrados = self.aesgcm.decrypt(nonce, texto_cifrado, None)
        return json.loads(datos_descifrados.decode('utf-8'))

# =====================================================================
# 3.1 MOTOR HL7 FHIR Y CATÁLOGO FONASA MLE
# =====================================================================
@st.cache_data
def cargar_catalogo_hl7(ruta_csv='listado_prestaciones.csv'):
    try:
        df = pd.read_csv(ruta_csv, sep=';', encoding='utf-8-sig', dtype=str)
        df.columns = df.columns.str.strip()
        
        catalogo = {}
        for _, row in df.iterrows():
            nombre = str(row.get('PROCEDIMIENTO A REALIZAR', '')).strip()
            if nombre and nombre != 'nan':
                catalogo[nombre] = {
                    "especialidad": str(row.get('ESPECIALIDAD', '')).strip(),
                    "codigo_fonasa": str(row.get('CODIGO PRESTACION', 'S/C')).strip(),
                    "contraste": str(row.get('MEDIO DE CONTRASTE', 'NO')).strip().upper() == 'SI',
                    "lateralidad": str(row.get('REQUIERE_LATERALIDAD', 'NO')).strip().upper() == 'SI'
                }
        return df, catalogo
    except Exception as e:
        return None, {}

def generar_service_request_hl7(procedimiento_base, lateralidad, catalogo):
    info = catalogo.get(procedimiento_base, {})
    codigo_fonasa = info.get("codigo_fonasa", "S/C")
    
    fhir_payload = {
        "resourceType": "ServiceRequest",
        "status": "active",
        "intent": "order",
        "code": {
            "coding": [{"system": "http://minsal.cl/fonasa/mle", "code": codigo_fonasa, "display": procedimiento_base}],
            "text": f"{procedimiento_base} - LAT: {lateralidad}"
        },
        "bodySite": [{"coding": [{"system": "http://snomed.info/sct", "display": lateralidad}]}]
    }
    return fhir_payload

def generar_bundle_fhir_completo(form_data: dict, id_documento: str) -> dict:
    """Empaqueta toda la Ficha Clínica en un Bundle HL7 FHIR R4."""
    
    # 1. Recurso Paciente
    paciente = {
        "resourceType": "Patient",
        "identifier": [{"system": "http://registrocivil.cl/rut", "value": form_data.get("rut_titular", "")}],
        "name": [{"text": form_data.get("nombre_titular", "")}],
        "gender": form_data.get("genero_biologico", "unknown"),
        "birthDate": str(form_data.get("fecha_nac", ""))
    }

    # 2. Observaciones Clínicas (VFG)
    observaciones = []
    if form_data.get("tiene_contraste"):
        observaciones.append({
            "resourceType": "Observation",
            "status": "final",
            "code": {"coding": [{"system": "http://loinc.org", "code": "33914-3", "display": "Estimated GFR"}]},
            "valueQuantity": {"value": form_data.get("vfg", 0.0), "unit": "mL/min/1.73m2"}
        })
        
    # 3. Respuestas del Triaje (Bioseguridad y Antecedentes)
    cuestionario = {
        "resourceType": "QuestionnaireResponse",
        "status": "completed",
        "item": []
    }
    
    for key, value in form_data.get("cuestionario", {}).items():
        if isinstance(value, bool):
            respuesta = {"valueBoolean": value}
        else:
            respuesta = {"valueString": str(value)}
        cuestionario["item"].append({"linkId": key, "answer": [respuesta]})

    # 4. ServiceRequests (Exámenes FONASA MLE)
    service_requests = form_data.get("recursos_hl7", [])

    return {
        "resourceType": "Bundle",
        "type": "document",
        "timestamp": datetime.now(pytz.utc).isoformat(),
        "entry": [{"resource": paciente}, {"resource": cuestionario}] + [{"resource": obs} for obs in observaciones] + [{"resource": sr} for sr in service_requests]
    }

# =====================================================================
# 3.2 LÓGICA GRAMATICAL Y ANATÓMICA
# =====================================================================
DICCIONARIO_ANATOMICO = {
    "RODILLA": {"genero": "F", "plural": "RODILLAS"}, "PIERNA": {"genero": "F", "plural": "PIERNAS"},
    "MANO": {"genero": "F", "plural": "MANOS"}, "MUÑECA": {"genero": "F", "plural": "MUÑECAS"},
    "MAMA": {"genero": "F", "plural": "MAMAS"}, "ORBITA": {"genero": "F", "plural": "ORBITAS"},
    "CADERA": {"genero": "F", "plural": "CADERAS"}, "EXTREMIDAD INFERIOR": {"genero": "F", "plural": "EXTREMIDADES INFERIORES"},
    "EXTREMIDAD SUPERIOR": {"genero": "F", "plural": "EXTREMIDADES SUPERIORES"},
    "HOMBRO": {"genero": "M", "plural": "HOMBROS"}, "CODO": {"genero": "M", "plural": "CODOS"},
    "BRAZO": {"genero": "M", "plural": "BRAZOS"}, "ANTEBRAZO": {"genero": "M", "plural": "ANTEBRAZOS"},
    "MUSLO": {"genero": "M", "plural": "MUSLOS"}, "TOBILLO": {"genero": "M", "plural": "TOBILLOS"},
    "OÍDO": {"genero": "M", "plural": "OÍDOS"}, "GLÚTEO": {"genero": "M", "plural": "GLÚTEOS"},
    "PIÉ": {"genero": "M", "plural": "PIES"}, "ANTEPIÉ O MEDIOPIÉ": {"genero": "M", "plural": "ANTEPIÉS O MEDIOPIÉS"},
    "DEDO (S) DE LA MANO": {"genero": "M", "plural": "DEDOS DE LAS MANOS"},
    "ORTEJO (S) DEL PIÉ": {"genero": "M", "plural": "ORTEJOS DE LOS PIES"}
}

def construir_nombre_especifico(nombre_base, lateralidad):
    if lateralidad not in ["Derecha", "Izquierda", "Ambas"]: return nombre_base
    palabra_encontrada = next((clave for clave in DICCIONARIO_ANATOMICO.keys() if clave in nombre_base), None)
    if not palabra_encontrada: return f"{nombre_base} {lateralidad.upper()}"
    info = DICCIONARIO_ANATOMICO[palabra_encontrada]
    
    if lateralidad == "Ambas":
        sufijo_ambos = "AMBOS" if info["genero"] == "M" else "AMBAS"
        nuevo_nombre = nombre_base.replace(palabra_encontrada, info["plural"])
        return nuevo_nombre.replace(f"DE {info['plural']}", f"DE {sufijo_ambos} {info['plural']}")
    else:
        sufijo_lado = lateralidad.upper() if info["genero"] == "F" else lateralidad.upper().replace("A", "O")
        return f"{nombre_base} {sufijo_lado}"

# =====================================================================
# 3.3 MOTOR OCR AVANZADO (Cédula de Identidad)
# =====================================================================
def limpiar_datos_ocr(texto_bruto, tipo="nombre"):
    if not texto_bruto: return ""
    limpio = str(texto_bruto)
    for s in ["eE", "p ", " /", " / ", "  ", ";", ":"]: limpio = limpio.replace(s, "")
    if tipo == "fecha":
        meses = {"ENE":"01", "FEB":"02", "MAR":"03", "ABR":"04", "MAY":"05", "JUN":"06", "JUL":"07", "AGO":"08", "SEP":"09", "OCT":"10", "NOV":"11", "DIC":"12"}
        for mes_texto, mes_num in meses.items():
            if mes_texto in limpio.upper(): limpio = limpio.upper().replace(mes_texto, mes_num).replace(" ", "/")
    return limpio.strip()

def procesar_cedula_inteligente(image_file):
    try:
        file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if img is None: return None, None, None, None
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        texto_extraido = pytesseract.image_to_string(gray, config=r'--oem 3 --psm 6 -l spa')
        
        rut_match = re.search(r'(\d{1,2}(?:\.?\d{3}){2}\s*[-_]?\s*[\dkK])', texto_extraido)
        rut = rut_match.group(0) if rut_match else ""
        
        sexo = "Femenino" if re.search(r'\b(F|FEMENINO)\b', texto_extraido, re.IGNORECASE) else ("Masculino" if re.search(r'\b(M|MASCULINO)\b', texto_extraido, re.IGNORECASE) else "")
            
        fecha_match = re.search(r'NACIMIENTO[^\d]{0,50}(\d{2}\s?(?:ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)\s?\d{4}|\d{2}[-/.]\d{2}[-/.]\d{4})', texto_extraido, re.IGNORECASE)
        if not fecha_match: fecha_match = re.search(r'(\d{2}\s?(?:ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)\s?\d{4}|\d{2}[-/.]\d{2}[-/.]\d{4})', texto_extraido, re.IGNORECASE)
        fecha_nacimiento = fecha_match.group(1) if fecha_match else ""
        
        apellidos_match = re.search(r"APELLIDOS[\s\n]+(.*?)\s+NOMBRES", texto_extraido, re.IGNORECASE | re.DOTALL)
        nombres_match = re.search(r"NOMBRES[\s\n]+(.*?)\s+(NACIONALIDAD|SEXO)", texto_extraido, re.IGNORECASE | re.DOTALL)
        
        nombre_completo = f"{nombres_match.group(1).strip() if nombres_match else ''} {apellidos_match.group(1).strip() if apellidos_match else ''}".strip()
        return limpiar_datos_ocr(rut, "rut"), limpiar_datos_ocr(nombre_completo, "nombre"), limpiar_datos_ocr(fecha_nacimiento, "fecha"), limpiar_datos_ocr(sexo, "sexo")
    except:
        return None, None, None, None

# =====================================================================
# 3.4 MOTOR FES (Firma Electrónica Simple)
# =====================================================================
def despachar_codigo_fes(metodo, destino, codigo):
    try:
        if metodo == "Email":
            correo_emisor = st.secrets.get("email", {}).get("sender_email")
            password_app = st.secrets.get("email", {}).get("app_password")
            if not correo_emisor or not password_app: return False

            msg = EmailMessage()
            msg.set_content(f"Estimado(a) paciente,\n\nSu código FES es: {codigo}\n\nNorte Imagen.")
            msg['Subject'] = '🔑 Código de Validación FES - Norte Imagen'
            msg['From'] = f"Norte Imagen <{correo_emisor}>"
            msg['To'] = destino

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(correo_emisor, password_app)
                smtp.send_message(msg)
            return True

        elif metodo == "WhatsApp":
            token_meta = st.secrets.get("whatsapp", {}).get("token")
            id_telefono = st.secrets.get("whatsapp", {}).get("phone_id")
            if not token_meta or not id_telefono: return False
            
            destino_limpio = "".join(filter(str.isdigit, str(destino)))
            url = f"https://graph.facebook.com/v19.0/{id_telefono}/messages"
            payload = {
                "messaging_product": "whatsapp", "to": destino_limpio, "type": "template",
                "template": {"name": "codigo_fes_norte_imagen", "language": {"code": "es"}, "components": [{"type": "body", "parameters": [{"type": "text", "text": str(codigo)}]}]}
            }
            response = requests.post(url, headers={"Authorization": f"Bearer {token_meta}", "Content-Type": "application/json"}, json=payload)
            return response.status_code == 200

    except:
        return False

# =====================================================================
# 3.5 MOTOR CLÍNICO: CÁLCULO DE VFG
# =====================================================================
def calcular_vfg_clinica(fecha_nac, sexo, peso, talla, creatinina):
    if creatinina <= 0: return 0.0, "Faltan datos de creatinina", "#333333", ""
    
    hoy = date.today()
    edad_dias = (hoy - fecha_nac).days
    edad_meses = edad_dias / 30.4
    edad_anos = edad_dias / 365.25

    if edad_anos < 18:
        if talla <= 0: return 0.0, "Requiere talla", "#333333", ""
        if edad_anos < 2:
            if edad_dias <= 28: k = 0.33 if edad_dias < 7 else 0.45
            else: k = 0.45 if edad_meses <= 12 else 0.55
                
            vfg = (k * talla) / creatinina
            
            if edad_meses <= 0.25: min_n, max_n = 15, 30
            elif edad_meses <= 1: min_n, max_n = 30, 50
            elif edad_meses <= 2: min_n, max_n = 40, 65
            elif edad_meses <= 4: min_n, max_n = 55, 85
            elif edad_meses <= 12: min_n, max_n = 70, 110
            else: min_n, max_n = 85, 125
            
            if vfg < (min_n * 0.7): return vfg, "🔴 ALTO RIESGO: VFG Crítica", "#FF0000", "vfg-critica"
            elif vfg < min_n: return vfg, "⚠️ RIESGO INTERMEDIO: Retraso", "#FFCC00", "vfg-intermedia"
            elif vfg <= max_n: return vfg, "✅ SIN RIESGO: VFG Adecuada", "#28A745", "vfg-normal"
            else: return vfg, "🔵 REVISAR: Posible hiperfiltración", "#007BFF", "vfg-normal"
        else:
            vfg = (0.413 * talla) / creatinina
            if vfg <= 30.0: return vfg, "🔴 Alto riesgo para administración de medio de contraste", "#FF0000", "vfg-critica"
            elif vfg <= 59.0: return vfg, "⚠️ Riesgo intermedio para administración de medio de contraste", "#FFCC00", "vfg-intermedia"
            else: return vfg, "✅ Sin riesgos para administración de medio de contraste", "#28A745", "vfg-normal"
    else:
        if peso <= 0: return 0.0, "Requiere peso", "#333333", ""
        factor = 0.85 if sexo in ['Femenino', 'No binario (Bio: Femenino)'] else 1.0
        vfg = (((140 - int(edad_anos)) * peso) / (72 * creatinina)) * factor
        
        if vfg <= 30.0: return vfg, "🔴 Alto riesgo para administración de medio de contraste", "#FF0000", "vfg-critica"
        elif vfg <= 59.0: return vfg, "⚠️ Riesgo intermedio para administración de medio de contraste", "#FFCC00", "vfg-intermedia"
        else: return vfg, "✅ Sin riesgos para administración de medio de contraste", "#28A745", "vfg-normal"

from streamlit_javascript import st_javascript

def obtener_ip_cliente():
    """Captura la IP real del dispositivo para trazabilidad legal FES."""
    try:
        ip_js = st_javascript('fetch("https://api.ipify.org?format=json").then(r => r.json()).then(d => d.ip)')
        if ip_js and ip_js != 0: return ip_js
    except: pass
    return "IP No detectada"
    
# =====================================================================
# VISTAS (FRAGMENTOS UI)
# =====================================================================
@st.fragment
def vista_escaner_cedula(tipo_paciente="TITULAR"):
    prefix = "titular" if tipo_paciente == "TITULAR" else "tutor"
    col_inputs, col_btn = st.columns([5, 1], vertical_alignment="bottom")
    with col_inputs:
        rut_input = st.text_input(f"RUT {tipo_paciente.capitalize()}", value=st.session_state.form.get(f"rut_{prefix}", ""), key=f"input_rut_{prefix}")
        st.session_state.form[f"rut_{prefix}"] = rut_input
        
    with col_btn:
        st.markdown("""<style>button[title*="Escanear cédula"] p {font-size: 32px !important; line-height: 1 !important; margin: 0 !important; padding: 0 !important;}</style>""", unsafe_allow_html=True)
        if st.button("📷", key=f"btn_cam_{prefix}", help=f"Escanear cédula de {tipo_paciente}", use_container_width=True):
            st.session_state[f"mostrar_camara_{prefix}"] = not st.session_state.get(f"mostrar_camara_{prefix}", False)

    if st.session_state.get(f"mostrar_camara_{prefix}", False):
        st.info("💡 Enfoque la cédula completa. Evite reflejos de luz.")
        opcion_carga = st.radio(f"Método de escaneo ({tipo_paciente}):", ["📷 Usar Cámara", "📁 Subir Foto (Galería)"], horizontal=True, key=f"radio_carga_{prefix}")
        
        foto_capturada = st.camera_input("Tomar foto", key=f"camara_{prefix}") if opcion_carga == "📷 Usar Cámara" else st.file_uploader("Seleccione la foto", type=["jpg", "png", "jpeg"], key=f"up_{prefix}")
        
        if foto_capturada:
            with st.spinner("Analizando con Visión Artificial..."):
                rut, nombre, fecha, sexo = procesar_cedula_inteligente(foto_capturada)
                if rut or nombre:
                    st.success("✅ ¡Datos extraídos con éxito!")
                    if rut: st.session_state.form[f"rut_{prefix}"] = rut
                    if nombre: st.session_state.form[f"nombre_{prefix}"] = nombre
                    if fecha and tipo_paciente == "TITULAR":
                        try: st.session_state.form["fecha_nac"] = datetime.strptime(fecha, "%d/%m/%Y").date()
                        except: pass
                    if sexo and tipo_paciente == "TITULAR": st.session_state.form["genero_biologico"] = sexo
                    
                    st.session_state[f"mostrar_camara_{prefix}"] = False
                    st.rerun()
                else:
                    st.error("❌ No se detectó texto claro. Intente nuevamente.")

@st.fragment
def vista_seleccion_procedimiento():
    df, catalogo = cargar_catalogo_hl7()
    if df is None:
        st.error("Error: No se encontró el catálogo de prestaciones.")
        return

    st.markdown('<div class="section-header">Información del Examen</div>', unsafe_allow_html=True)
    esp_raw = sorted(list(set([info["especialidad"] for info in catalogo.values()])))
    esp_sel = st.selectbox("Especialidad", esp_raw, key="sel_especialidad")
    proc_disponibles = [proc for proc, info in catalogo.items() if info["especialidad"] == esp_sel]
    
    if "proc_cache" not in st.session_state: st.session_state.proc_cache = []
    def sync_proc(): st.session_state.proc_cache = st.session_state.sel_procedimientos

    pre_sel = st.multiselect("Procedimiento(s) a realizar", options=sorted(list(set(proc_disponibles + st.session_state.proc_cache))), default=st.session_state.proc_cache, key="sel_procedimientos", on_change=sync_proc)
    
    if pre_sel:
        st.session_state.form["recursos_hl7"] = []
        st.session_state.form["tiene_contraste"] = False
        st.session_state.form["nombres_transformados"] = {}
        
        for examen in pre_sel:
            info_examen = catalogo.get(examen, {"contraste": False, "lateralidad": False, "codigo_fonasa": "S/C"})
            if info_examen["contraste"]: st.session_state.form["tiene_contraste"] = True
            lat_actual = "No aplica"
            
            if info_examen["lateralidad"]:
                clave_limpia = examen.replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')
                c_txt1, c_tgl, c_txt2, c_divisor, c_chk = st.columns([0.6, 0.6, 0.7, 0.2, 2.5])
                es_bilateral = st.session_state.get(f"chk_ambas_{clave_limpia}", False)
                with c_chk: es_bilateral = st.checkbox("AMBOS (AS)", key=f"chk_ambas_{clave_limpia}")
                with c_tgl: lado_izq = st.toggle("Lado Examen", key=f"tgl_lat_{clave_limpia}", disabled=es_bilateral, label_visibility="collapsed")
                with c_txt1: st.markdown(f"<p style='margin-top: 4px; font-size: 0.85rem; text-align: right; color: {'#999' if es_bilateral else '#333'};'>DERECHA</p>", unsafe_allow_html=True)
                with c_txt2: st.markdown(f"<p style='margin-top: 4px; font-size: 0.85rem; text-align: left; color: {'#999' if es_bilateral else '#333'};'>IZQUIERDA</p>", unsafe_allow_html=True)
                with c_divisor: st.markdown("<p style='margin-top: 2px; color: #ccc; font-size: 1.1rem; text-align: center;'>|</p>", unsafe_allow_html=True)
                lat_actual = "Ambas" if es_bilateral else ("Izquierda" if lado_izq else "Derecha")
                st.markdown("<div style='border-bottom: 1px dashed #e0e0e0; margin: 10px 0;'></div>", unsafe_allow_html=True)
            
            nombre_final = construir_nombre_especifico(examen, lat_actual)
            st.session_state.form["nombres_transformados"][examen] = nombre_final
            st.markdown(f"<p style='font-size: 0.9rem; margin-bottom: 2px; color: #333333;'><b>PROCEDIMIENTO:</b> {nombre_final}</p>", unsafe_allow_html=True)
            st.session_state.form["recursos_hl7"].append(generar_service_request_hl7(examen, lat_actual, catalogo))
            st.caption(f"🧬 Mapeado a HL7 - Código FONASA: {info_examen['codigo_fonasa']}")

@st.fragment
def vista_modulo_fes():
    st.markdown('<div class="section-header">Firma Electrónica Simple (FES)</div>', unsafe_allow_html=True)
    st.info("ℹ️ Para validar su identidad y firmar el consentimiento, enviaremos un código temporal.")
    
    col_metodo, col_contacto = st.columns([1, 2])
    with col_metodo: metodo_fes = st.selectbox("Canal de envío", ["WhatsApp", "Email"], key="sel_metodo_fes")
    with col_contacto: contacto = st.text_input("Ingrese número (+569...) o Correo Electrónico", key="txt_contacto_fes")
        
    if st.button("📲 Generar y Enviar Código", use_container_width=True):
        if not contacto:
            st.error("Debe ingresar un contacto válido.")
            return
            
        codigo_seguridad = str(random.randint(100000, 999999))
        st.session_state.fes_codigo_generado = codigo_seguridad
        
        exito = despachar_codigo_fes(metodo_fes, contacto, codigo_seguridad)
        if exito: st.success(f"Código enviado exitosamente vía {metodo_fes}.")
        else: st.warning(f"⚠️ Entorno de prueba (Credenciales email/WP no config). Tu código FES de prueba es: {codigo_seguridad}")
            
    if st.session_state.get("fes_codigo_generado"):
        st.markdown("---")
        codigo_ingresado = st.text_input("🔑 Ingrese el código de 6 dígitos recibido:", max_chars=6)
        if st.button("✅ Validar Identidad y Firmar", type="primary", use_container_width=True):
            if codigo_ingresado == st.session_state.fes_codigo_generado:
                st.session_state.fes_validado = True
                st.success("🎉 ¡Identidad validada exitosamente! Procedimiento autorizado.")
            else: st.error("❌ Código incorrecto. Intente nuevamente.")

@st.fragment
def vista_cuestionario_clinico():
    if "cuestionario" not in st.session_state.form:
        st.session_state.form["cuestionario"] = {}
    riesgos = st.session_state.form["cuestionario"]

    st.markdown('<div class="section-header">1. Bioseguridad Magnética</div>', unsafe_allow_html=True)
    riesgos["marcapasos"] = st.toggle("Marcapasos cardiaco", value=riesgos.get("marcapasos", False))
    riesgos["implantes"] = st.toggle("Implantes metálicos, quirúrgicos, prótesis o dispositivos electrónicos", value=riesgos.get("implantes", False))
    if riesgos["marcapasos"] or riesgos["implantes"]:
        riesgos["detalle_implantes"] = st.text_area("Detalle (Tipo y Ubicación):", value=riesgos.get("detalle_implantes", ""))

    st.markdown('<div class="section-header">2. Antecedentes Clínicos</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    riesgos["ayuno"] = c1.toggle("Ayuno (2 hrs o mas)", value=riesgos.get("ayuno", False))
    riesgos["asma"] = c1.toggle("Asma", value=riesgos.get("asma", False))
    riesgos["alergico"] = c2.toggle("Alergias severas", value=riesgos.get("alergico", False))
    if riesgos["alergico"]: riesgos["detalle_alergias"] = c2.text_input("⚠️ Especifique alergias:", value=riesgos.get("detalle_alergias", ""))
    riesgos["renal"] = c2.toggle("Insuficiencia renal", value=riesgos.get("renal", False))
    riesgos["embarazo"] = c3.toggle("Embarazo", value=riesgos.get("embarazo", False))

    st.markdown('<div class="section-header">3. Antecedentes Quirúrgicos y Oncológicos</div>', unsafe_allow_html=True)
    riesgos["cirugia"] = st.toggle("¿Ha sido sometido a alguna cirugía?", value=riesgos.get("cirugia", False))
    if riesgos["cirugia"]: riesgos["cirugia_detalle"] = st.text_input("Detalle y fecha:", value=riesgos.get("cirugia_detalle", ""))
    
    riesgos["cancer"] = st.toggle("¿Cursa o ha cursado cáncer?", value=riesgos.get("cancer", False))
    if riesgos["cancer"]:
        riesgos["cancer_detalle"] = st.text_input("Tipo de cáncer y etapa:", value=riesgos.get("cancer_detalle", ""))
        ct1, ct2, ct3, ct4 = st.columns(4)
        riesgos["rt"] = ct1.checkbox("Radioterapia (RT)", value=riesgos.get("rt", False))
        riesgos["qt"] = ct2.checkbox("Quimioterapia (QT)", value=riesgos.get("qt", False))

    st.markdown('<div class="section-header">4. Exámenes Anteriores y Respaldos</div>', unsafe_allow_html=True)
    riesgos["tiene_examenes"] = st.toggle("¿Tiene exámenes anteriores relacionados?", value=riesgos.get("tiene_examenes", False))
    if riesgos["tiene_examenes"]:
        st.file_uploader("Adjunte informes (PDF/JPG)", type=["pdf", "jpg", "jpeg"], accept_multiple_files=True, key="up_anteriores_ui")
        col_l1, col_p1 = st.columns([3, 1])
        riesgos["link_exam_1"] = col_l1.text_input("🔗 Link Portal/DICOM:", value=riesgos.get("link_exam_1", ""))
        riesgos["pin_exam_1"] = col_p1.text_input("🔑 PIN / Clave:", value=riesgos.get("pin_exam_1", ""))

from streamlit_drawable_canvas import st_canvas

@st.fragment
def vista_consentimiento_y_firma():
    st.markdown('<div class="section-header">Declaración Legal y Consentimiento</div>', unsafe_allow_html=True)
    st.info("Al firmar este documento, usted autoriza el procedimiento y el procesamiento de sus datos bajo el estándar clínico HL7 FHIR.")
    
    st.session_state.form["autoriza_gad"] = st.radio("¿Ha leído y autoriza el procedimiento?", ["SÍ", "NO"], index=None)
    st.session_state.form["veracidad"] = st.checkbox("**Verifico que todos los datos ingresados son fidedignos y corresponden a mi estado de salud actual.**", value=st.session_state.form.get("veracidad", False))
    
    st.markdown("---")
    col_firma, col_fes = st.columns([1, 1.2])
    
    with col_firma:
        st.markdown("**Firma Manuscrita:**")
        canvas_result = st_canvas(stroke_width=3, stroke_color="#000", background_color="#f5f5f5", height=150, width=350, key="canvas_firma")
        if canvas_result is not None and canvas_result.image_data is not None:
            # Validación para asegurar que el usuario realmente dibujó algo
            import numpy as np
            if np.any(canvas_result.image_data[:, :, 3] > 0):
                st.session_state.form["firma_trazada"] = True
            else:
                st.session_state.form["firma_trazada"] = False
            
    with col_fes:
        vista_modulo_fes()
        
# =====================================================================
# 5.4 MAIN LOOP
# =====================================================================
def main():
    st.markdown("<h1 style='text-align: center; color: #800020;'>🏥 Admisión y Consentimiento Clínico</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Plataforma Integral Norte Imagen</p>", unsafe_allow_html=True)
    
    tab_paciente, tab_examenes, tab_clinica, tab_firma, tab_resumen = st.tabs(["👤 1. Paciente", "🩻 2. Exámenes", "⚕️ 3. Clínica", "✍️ 4. Firma (FES)", "📄 5. Resumen JSON"])
    
    with tab_paciente:
        st.markdown('<div class="section-header">Identificación del Paciente Titular</div>', unsafe_allow_html=True)
        vista_escaner_cedula("TITULAR")
        
        col_nac, col_gen = st.columns(2)
        with col_nac: st.session_state.form["fecha_nac"] = st.date_input("Fecha de Nacimiento", value=st.session_state.form.get("fecha_nac", None), min_value=date(1900, 1, 1), max_value=date.today())
        with col_gen:
            opciones_gen = ["", "Femenino", "Masculino", "No binario (Bio: Femenino)", "No binario (Bio: Masculino)"]
            # Usar .get() previene el KeyError si el usuario tiene una sesión antigua guardada
            genero_actual = st.session_state.form.get("genero_biologico", "")
            indice_seguro = opciones_gen.index(genero_actual) if genero_actual in opciones_gen else 0
            
            st.session_state.form["genero_biologico"] = st.selectbox("Género Biológico", opciones_gen, index=indice_seguro)
            
        st.markdown("---")
        st.session_state.form["requiere_tutor"] = st.checkbox("🙋♂️ El paciente es menor de edad o requiere tutor legal")
        if st.session_state.form["requiere_tutor"]:
            st.markdown('<div class="section-header">Identificación del Tutor Legal</div>', unsafe_allow_html=True)
            vista_escaner_cedula("TUTOR")

    with tab_examenes: vista_seleccion_procedimiento()

    with tab_clinica:
        vista_cuestionario_clinico()
        
        st.markdown('<div class="section-header">5. Evaluación de Función Renal (Contraste)</div>', unsafe_allow_html=True)
        if st.session_state.form.get("tiene_contraste", False):
            st.warning("⚠️ Requiere **Medio de Contraste**. Complete los datos antropométricos.")
            c_peso, c_talla, c_crea, c_fecha = st.columns(4)
            with c_peso: st.session_state.form["peso"] = st.number_input("Peso (kg)", min_value=0.0, max_value=300.0, step=0.1)
            with c_talla: st.session_state.form["talla"] = st.number_input("Talla (cm)", min_value=0.0, max_value=250.0, step=1.0)
            with c_crea: st.session_state.form["creatinina"] = st.number_input("Creatinina (mg/dL)", min_value=0.0, max_value=20.0, step=0.01)
            with c_fecha: st.session_state.form["fecha_creatinina"] = st.date_input("Fecha Examen Creatinina")
                
            if st.session_state.form.get("fecha_nac") and st.session_state.form.get("genero_biologico") and st.session_state.form["creatinina"] > 0:
                vfg, mensaje_riesgo, color_hex, _ = calcular_vfg_clinica(st.session_state.form["fecha_nac"], st.session_state.form["genero_biologico"], st.session_state.form["peso"], st.session_state.form["talla"], st.session_state.form["creatinina"])
                st.session_state.form["vfg"] = vfg # Guardamos en estado
                st.markdown(f"<div class='vfg-box' style='border: 2px solid {color_hex}; color: {color_hex};'><b>VFG: {vfg:.2f} mL/min</b><br>{mensaje_riesgo}</div>", unsafe_allow_html=True)
        else:
            st.success("✅ Los procedimientos seleccionados NO requieren Medio de Contraste.")

    with tab_firma: 
        vista_consentimiento_y_firma()

    with tab_resumen:
        st.markdown('<div class="section-header">Empaquetado de Datos y Envío</div>', unsafe_allow_html=True)
        
        if not st.session_state.form.get("firma_trazada", False):
            st.error("✍️ Debe realizar la firma manuscrita en el recuadro de la pestaña anterior.")
        elif not st.session_state.get("fes_validado", False): 
            st.error("🔒 Complete la Validación FES (Código SMS/Email) en la pestaña anterior.")
        elif not st.session_state.form.get("veracidad", False):
            st.error("⚖️ Debe confirmar la veracidad de los datos en la pestaña anterior.")
        else:
            # Generamos el ID Único del Documento
            rut_limpio = str(st.session_state.form.get('rut_titular', 'SIN_RUT')).replace(".", "").replace("-", "")
            id_doc = f"DOC_{rut_limpio}_{datetime.now().strftime('%Y%m%d%H%M')}"
            
            # Compilamos el HL7 FHIR
            bundle_final = generar_bundle_fhir_completo(st.session_state.form, id_doc)
            
            # Inyectamos Metadatos de Auditoría
            bundle_final["meta"] = {
                "security": [{"code": "AES-256-GCM"}],
                "client_ip": obtener_ip_cliente(),
                "fes_signature_hash": st.session_state.fes_codigo_generado
            }

            st.success("✅ Paquete estructurado exitosamente bajo estándar HL7 FHIR R4.")
            with st.expander("Ver JSON Generado (Listo para Interoperabilidad)", expanded=True): 
                st.json(bundle_final)
                
            if st.button("🚀 Encriptar (AES-256) y Enviar a Central (HIS/RIS)", type="primary", use_container_width=True):
                with st.spinner("Encriptando y transmitiendo..."):
                    try:
                        # 1. Encriptación
                        gestor_crypto = GestorCriptografico()
                        datos_encriptados = gestor_crypto.encriptar(bundle_final)
                        
                        # 2. Guardado en Firebase Firestore
                        if db is not None:
                            db.collection("admisiones_fhir").document(id_doc).set({
                                "paciente_rut": rut_limpio,
                                "timestamp": datetime.now(pytz.utc).isoformat(),
                                "payload_encriptado_aes": datos_encriptados
                            })
                            st.balloons()
                            st.success(f"¡Transmisión Segura Completada! ID: {id_doc}")
                        else:
                            st.error("Error: Conexión a Firebase no disponible.")
                    except Exception as e:
                        st.error(f"Error en el proceso de encriptación/envío: {e}")
if __name__ == "__main__":
    main()

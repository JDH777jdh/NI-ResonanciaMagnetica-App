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

# ── DEPENDENCIAS ADICIONALES (Integración app_v2) ──────────────────────────
from fpdf import FPDF
from PIL import Image
import pyotp
import hashlib
import time
import tempfile

# Conectores OAuth2 para Google Drive (módulo de respaldo PDF - kill-switch)
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

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

    if "abrir_modal" not in st.session_state:
        st.session_state.abrir_modal = False

    if "registro_guardado_db" not in st.session_state:
        st.session_state.registro_guardado_db = False

    # Cámaras OCR
    if 'mostrar_camara' not in st.session_state:
        st.session_state.mostrar_camara = False
    if 'mostrar_camara_tutor' not in st.session_state:
        st.session_state.mostrar_camara_tutor = False

    if "form" not in st.session_state:
        st.session_state.form = {
            # ── Identificación Paciente ──────────────────────────────────
            "rut_titular": "", "nombre_titular": "",
            "nombre": "", "rut": "", "sin_rut": False,
            "tipo_doc": "Pasaporte", "num_doc": "",
            "telefono": "", "email": "",
            "fecha_nac": date(1990, 1, 1),
            "genero_biologico": "",
            "genero_idx": 0, "sexo_bio_idx": 0,

            # ── Tutor Legal ──────────────────────────────────────────────
            "requiere_tutor": False,
            "es_autovalente": True,
            "rut_tutor": "", "nombre_tutor": "",
            "parentesco_tutor": "",
            "sin_rut_tutor": False,
            "tipo_doc_tutor": "Pasaporte", "num_doc_tutor": "",

            # ── Procedencia y Agenda ─────────────────────────────────────
            "procedencia": "Ambulatorio",
            "unidad_procedencia": "",
            "fecha_examen": date.today(),

            # ── Examen HL7 FHIR ──────────────────────────────────────────
            "recursos_hl7": [],
            "tiene_contraste": False,
            "nombres_transformados": {},
            "esp_idx": 0,

            # ── Bioseguridad Magnética ───────────────────────────────────
            "bio_marcapaso": "No", "bio_implantes": "No", "bio_detalle": "",

            # ── Antecedentes Clínicos ────────────────────────────────────
            "clin_ayuno": "No", "clin_asma": "No",
            "clin_hiperten": "No", "clin_hipertiroid": "No",
            "clin_diabetes": "No", "clin_alergico": "No",
            "clin_metformina": "No", "clin_renal": "No",
            "clin_dialisis": "No", "clin_claustro": "No",
            "clin_embarazo": "No", "clin_lactancia": "No",
            "alergias_detalle": "",
            "condiciones": [], "condicion_detalle": "",

            # ── Antecedentes Quirúrgicos ─────────────────────────────────
            "quir_cirugia_check": "No", "quir_cirugia_detalle": "",
            "quir_cancer_check": "No", "quir_cancer_detalle": "",
            "rt": False, "qt": False, "bt": False, "it": False,
            "quir_otro_trat": "",

            # ── Exámenes Anteriores ───────────────────────────────────────
            "has_examenes_previos": "No",
            "ex_rx": False, "ex_mg": False, "ex_eco": False,
            "ex_tc": False, "ex_rm": False, "ex_otros": "",
            "link_exam_1": "", "pin_exam_1": "",
            "link_exam_2": "", "pin_exam_2": "",

            # ── Función Renal ────────────────────────────────────────────
            "peso": 0.0, "talla": 0.0,
            "creatinina": 0.0, "fecha_creatinina": None,
            "vfg": 0.0,

            # ── FES / OTP Criptográfico (Ley 19.799) ─────────────────────
            "otp_secret": pyotp.random_base32(),
            "otp_enviado": False,
            "otp_metodo": "Email",
            "otp_verificado": False,
            "otp_timestamp": 0.0,
            "hash_documento": "",
            "traza_auditoria": "",

            # ── Consentimiento ────────────────────────────────────────────
            "veracidad": False,
            "autoriza_gad": None,
            "firma_img": None,

            # ── Metadata Clínica ──────────────────────────────────────────
            "ip_dispositivo": "Buscando IP...",
        }

    # Variables de sesión paralelas (no dentro de "form")
    if "tiene_contraste" not in st.session_state:
        st.session_state.tiene_contraste = False
    if "procedimiento" not in st.session_state:
        st.session_state.procedimiento = ""
    if "edad_para_calculo" not in st.session_state:
        st.session_state.edad_para_calculo = 0
    if "sexo_para_calculo" not in st.session_state:
        st.session_state.sexo_para_calculo = ""
    if "firma_guardada" not in st.session_state:
        st.session_state.firma_guardada = None
    if "pdf_bytes_data" not in st.session_state:
        st.session_state.pdf_bytes_data = None
    if "proc_cache" not in st.session_state:
        st.session_state.proc_cache = []
        
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
# MOTOR PDF INSTITUCIONAL (Encapsulado — futuro reemplazo por motor central)
# =====================================================================
tz_chile = pytz.timezone('America/Santiago')

class PDF(FPDF):
    """
    Clase PDF institucional Norte Imagen.
    NOTA ARQUITECTURAL: Este motor es candidato a ser extraído como
    microservicio/módulo independiente (motor_pdf_institucional.py).
    La interfaz pública es: generar_pdf_clinico(datos: dict) -> bytes
    """
    def header(self):
        if os.path.exists("logoNI.png"):
            self.image("logoNI.png", 11, 11, 30)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(128, 0, 32)
        self.cell(0, 7, 'ENCUESTA DE RIESGOS ASOCIADOS Y', 0, 1, 'R')
        self.cell(0, 7, 'CONSENTIMIENTO INFORMADO', 0, 1, 'R')
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
        ip_cliente = st.session_state.form.get("ip_dispositivo", "No detectada")
        id_registro = f"{rut_p}-{iniciales} (IP:{ip_cliente})"
        texto = (f"Certificado Digital Norte Imagen - RM: {ahora_pie} "
                 f"- ID Registro: {id_registro} - ORIGINAL PRE-ADMISIÓN.")
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


def generar_pdf_clinico(datos: dict) -> bytes:
    """
    Motor PDF clínico Norte Imagen.
    
    INTERFAZ ESTABLE: Esta función es el punto de integración con el
    futuro motor PDF institucional. Los parámetros y el tipo de retorno
    NO deben cambiar al migrar al motor central.
    
    Args:
        datos: dict con todos los campos del formulario clínico
    Returns:
        bytes: PDF compilado listo para descarga o almacenamiento
    """
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=12)

    # ── Encabezado de fecha y procedencia ──────────────────────────────────
    fecha_str = datetime.now(tz_chile).strftime("%d/%m/%Y")
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 5, f"Fecha de examen: {fecha_str}", 0, 1, 'R')

    procedencia_base = datos.get('procedencia', 'AMBULATORIO').upper()
    unidad_val = datos.get('unidad_procedencia', '').strip().upper()
    if procedencia_base == 'HOSPITALIZADO' and unidad_val:
        texto_procedencia = f"PROCEDENCIA: {procedencia_base} (UNIDAD: {unidad_val})"
    else:
        texto_procedencia = f"PROCEDENCIA: {procedencia_base}"
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 5, safe_text(texto_procedencia), 0, 1, 'L')
    pdf.ln(1)

    # ── SECCIÓN 1: Identificación del Paciente ──────────────────────────────
    pdf.section_title("1", "IDENTIFICACION DEL PACIENTE")
    pdf.set_text_color(0, 0, 0)

    margen_izquierdo = 10
    ancho_disponible = pdf.w - 20
    w_col = (ancho_disponible - 10) / 2
    x_col2 = margen_izquierdo + w_col + 10

    es_extranjero = datos.get('sin_rut', False)
    if es_extranjero in [True, "true", "True", "1"]:
        paciente_rut = f"{datos.get('tipo_doc', 'Documento')}: {datos.get('num_doc', 'S/N')}"
    else:
        paciente_rut = str(datos.get('rut', 'S/R'))

    paciente_nombre = datos.get('nombre', 'Sin Registro')
    paciente_edad = obtener_edad_visual_pdf(datos.get('fecha_nac'))
    fecha_nac_val = datos['fecha_nac'].strftime('%d/%m/%Y') if hasattr(
        datos.get('fecha_nac'), 'strftime') else str(datos.get('fecha_nac', ''))
    email_val = datos.get('email', 'S/E')
    is_contraste = st.session_state.get('tiene_contraste', False)
    procedimiento_val = st.session_state.get('procedimiento', 'No especificado')

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
    pdf.cell(w_col - 35, 5, safe_text(fecha_nac_val), 0, 0)
    pdf.set_xy(x_col2, y_fila3)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(12, 5, "Email: ", 0, 0)
    pdf.set_font('Arial', '', 9)
    pdf.cell(w_col - 12, 5, safe_text(email_val), 0, 1)

    pdf.set_font('Arial', 'B', 9)
    pdf.cell(35, 5, "Medio de contraste: ", 0, 0)
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 5, 'SI' if is_contraste else 'NO', 0, 1)

    pdf.set_font('Arial', 'B', 9)
    pdf.cell(28, 5, safe_text("Procedimiento(s): "), 0, 0, 'L')
    pdf.set_font('Arial', '', 9)
    pdf.multi_cell(0, 5, safe_text(procedimiento_val), 0, 'L')
    pdf.ln(2)

    # ── Tutor Legal ────────────────────────────────────────────────────────
    rep_nombre = datos.get('nombre_tutor', '')
    fecha_nac_obj = datos.get('fecha_nac')
    edad_num = calcular_edad(fecha_nac_obj) if fecha_nac_obj else 99

    if rep_nombre or edad_num < 18:
        pdf.ln(1)
        y_tutor = pdf.get_y()
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

    # ── SECCIÓN 2: Bioseguridad ────────────────────────────────────────────
    pdf.section_title("2", "BIOSEGURIDAD MAGNETICA")
    pdf.set_font('Arial', '', 9)
    pdf.data_field("Marcapasos cardiaco", datos.get('bio_marcapaso', 'No'))
    pdf.data_field("Implantes metálicos, quirúrgicos, prótesis o dispositivos electrónicos",
                   datos.get('bio_implantes', 'No'))
    pdf.set_font('Arial', 'I', 8)
    pdf.data_field("Detalle Bioseguridad",
                   datos.get('bio_detalle') or "Sin observaciones")
    pdf.ln(2)

    # ── SECCIÓN 3: Antecedentes Clínicos ───────────────────────────────────
    pdf.section_title("3", "ANTECEDENTES CLINICOS")
    pdf.set_text_color(0, 0, 0)
    clinicos = [
        ("Ayuno 2hrs+", datos.get('clin_ayuno')),
        ("Asma", datos.get('clin_asma')),
        ("Alergias", datos.get('clin_alergico')),
        ("Hipertensión", datos.get('clin_hiperten')),
        ("Hipotiroidismo", datos.get('clin_hipertiroid')),
        ("Diabetes", datos.get('clin_diabetes')),
        ("Metformina 48h", datos.get('clin_metformina')),
        ("Insuf. Renal", datos.get('clin_renal')),
        ("Diálisis", datos.get('clin_dialisis')),
        ("Embarazo", datos.get('clin_embarazo')),
        ("Lactancia", datos.get('clin_lactancia')),
        ("Claustrofobia", datos.get('clin_claustro'))
    ]
    col_width = pdf.w / 4.2
    for i in range(0, len(clinicos), 4):
        linea = clinicos[i:i+4]
        for item, valor in linea:
            pdf.set_font('Arial', '', 8)
            pdf.cell(col_width, 4.5, safe_text(f"{item}: {valor}"), 0, 0)
        pdf.ln(4.5)

    detalle_alergia = datos.get('alergias_detalles', datos.get('alergias_detalle', '')).strip()
    if str(datos.get('clin_alergico', '')).upper() in ["SÍ", "SI"] and detalle_alergia:
        pdf.ln(2)
        pdf.set_font('Arial', 'BI', 8)
        pdf.cell(0, 5, f"DETALLE ALERGIAS: {detalle_alergia}", ln=True, border='B')
        pdf.ln(2)
    else:
        pdf.ln(1)

    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 5, "CONDICIONES O REQUERIMIENTOS ESPECIALES:", 0, 1)
    conds = datos.get("condiciones", [])
    detalle_cond = datos.get("condicion_detalle", "")
    pdf.set_font('Arial', '', 9)
    if conds or detalle_cond:
        if conds:
            pdf.multi_cell(0, 5, f" {', '.join(conds)}")
        if detalle_cond:
            pdf.set_font('Arial', 'I', 8)
            pdf.multi_cell(0, 5, f"Detalle: {detalle_cond}")
    else:
        pdf.cell(0, 5, "Ninguna condición declarada.", 0, 1)
    pdf.ln(2)

    # ── SECCIÓN 4: Antecedentes Quirúrgicos ───────────────────────────────
    pdf.section_title("4", "ANTECEDENTES QUIRURGICOS Y TERAPEUTICOS")
    pdf.set_font('Arial', '', 9)
    pdf.data_field("Cirugías", datos.get('quir_cirugia_check', 'No'))
    pdf.set_font('Arial', '', 8)
    pdf.data_field("Detalle cirugías",
                   datos.get('quir_cirugia_detalle') or "N/A")
    pdf.set_font('Arial', '', 9)
    pdf.data_field("¿Cursa o ha cursado cáncer?", datos.get('quir_cancer_check', 'No'))
    if datos.get('quir_cancer_check') == 'Sí':
        pdf.set_font('Arial', '', 8)
        pdf.data_field("Detalle cáncer/etapa",
                       datos.get('quir_cancer_detalle') or "N/A")
        trats = [k for k, v in {
            "RT": datos.get('rt'), "QT": datos.get('qt'),
            "BT": datos.get('bt'), "IT": datos.get('it')
        }.items() if v in [True, "Sí"]]
        pdf.set_font('Arial', '', 9)
        pdf.data_field("Tratamientos", ", ".join(trats) if trats else "Ninguno declarado")
        if datos.get('quir_otro_trat'):
            pdf.set_font('Arial', '', 8)
            pdf.data_field("Otros tratamientos", datos.get('quir_otro_trat'))
    pdf.ln(2)

    # ── SECCIÓN 5: Exámenes Anteriores ────────────────────────────────────
    pdf.section_title("5", "EXAMENES ANTERIORES")
    pdf.set_font('Arial', '', 9)
    if datos.get('has_examenes_previos') == 'Sí':
        ex_list = [k for k, v in {
            "Rx": datos.get('ex_rx'), "MG": datos.get('ex_mg'),
            "Eco": datos.get('ex_eco'), "TC": datos.get('ex_tc'),
            "RM": datos.get('ex_rm')
        }.items() if v in [True, "Sí"]]
        pdf.data_field("Exámenes", ", ".join(ex_list) if ex_list else "Ninguno seleccionado")
        pdf.data_field("Otros exámenes", datos.get('ex_otros') or "N/A")
    else:
        pdf.data_field("Exámenes", "No refiere exámenes anteriores")
    pdf.ln(2)

    # ── SECCIÓN 6: Registro Farmacológico y VFG ────────────────────────────
    pdf.section_title("6", "REGISTRO DE ADMINISTRACION FARMACOLOGICA Y EVALUACION FUNCION RENAL")
    pdf.set_font('Arial', '', 9)

    if st.session_state.get('tiene_contraste', False):
        crea = datos.get('creatinina', 0.0)
        creatinina_val_pdf = f"{crea} mg/dL" if crea > 0 else "Sin registro"

        fecha_nac_pdf = datos.get('fecha_nac')
        hoy_pdf = date.today()
        edad_dias_pdf = (hoy_pdf - fecha_nac_pdf).days if fecha_nac_pdf else 0
        edad_meses_pdf = edad_dias_pdf / 30.4
        edad_anos_pdf = edad_dias_pdf / 365.25
        es_pediatrico = edad_anos_pdf < 18
        vfg_real = datos.get('vfg', 0.0)

        if es_pediatrico:
            talla_real = datos.get('talla', 0.0)
            etiqueta_antropo = "Talla (Pediátrico)"
            valor_antropo = f"{talla_real} cm" if talla_real > 0 else "Sin registro"
        else:
            peso_real = datos.get('peso', 0.0)
            etiqueta_antropo = "Peso (Adulto)"
            valor_antropo = f"{peso_real} kg" if peso_real > 0 else "Sin registro"

        pdf.set_fill_color(245, 245, 245)
        pdf.cell(95, 7, safe_text(f" Creatinina: {creatinina_val_pdf}"), 0, 0, 'L', True)
        pdf.cell(95, 7, safe_text(f" {etiqueta_antropo}: {valor_antropo}"), 0, 1, 'L', True)
        pdf.ln(1)

        if vfg_real > 0:
            msg_riesgo, r, g, b = "", 0, 0, 0
            if es_pediatrico and edad_anos_pdf < 2:
                if edad_meses_pdf <= 0.25: min_n, max_n = 15, 30
                elif edad_meses_pdf <= 1:  min_n, max_n = 30, 50
                elif edad_meses_pdf <= 2:  min_n, max_n = 40, 65
                elif edad_meses_pdf <= 4:  min_n, max_n = 55, 85
                elif edad_meses_pdf <= 12: min_n, max_n = 70, 110
                else:                      min_n, max_n = 85, 125
                if vfg_real < (min_n * 0.7):
                    msg_riesgo, r, g, b = "ALTO RIESGO: VFG Crítica", 255, 0, 0
                elif vfg_real < min_n:
                    msg_riesgo, r, g, b = "RIESGO INTERMEDIO: Retraso maduración", 184, 134, 11
                elif vfg_real <= max_n:
                    msg_riesgo, r, g, b = "SIN RIESGO: VFG Adecuada", 34, 139, 34
                else:
                    msg_riesgo, r, g, b = "REVISAR: Posible hiperfiltración", 0, 123, 255
            else:
                if vfg_real <= 30.0:
                    msg_riesgo, r, g, b = "ALTO RIESGO para medio de contraste", 255, 0, 0
                elif vfg_real <= 59.0:
                    msg_riesgo, r, g, b = "RIESGO INTERMEDIO para medio de contraste", 184, 134, 11
                else:
                    msg_riesgo, r, g, b = "SIN RIESGOS para medio de contraste", 34, 139, 34

            pdf.set_font('Arial', 'B', 9)
            pdf.cell(35, 6, safe_text(f" V.F.G: {vfg_real:.2f} ml/min"), 0, 0, 'L')
            pdf.set_font('Arial', 'B', 8)
            pdf.set_text_color(r, g, b)
            pdf.cell(155, 6, safe_text(f"({msg_riesgo})"), 0, 1, 'L')
            pdf.set_text_color(0, 0, 0)
            pdf.ln(2)

        # Tabla de fármacos
        pdf.ln(3)
        pdf.set_font('Arial', 'B', 9)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(190, 6, safe_text("DETALLE DE ADMINISTRACIÓN, FÁRMACOS Y ACCESO"), 0, 1, 'C', True)
        pdf.ln(1)
        pdf.set_font('Arial', '', 9)
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(95, 7, safe_text(" Acceso Vascular: "), 0, 0, 'L', True)
        pdf.cell(95, 7, safe_text(" Sitio de Punción: "), 0, 1, 'L', True)
        pdf.ln(2)
        w1, w2, w3 = 80, 40, 70
        pdf.set_font('Arial', 'B', 8)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(w1, 7, safe_text("Medio de contraste u otros medicamentos"), 0, 0, 'C', True)
        pdf.cell(w2, 7, safe_text("Cantidad (ml)"), 0, 0, 'C', True)
        pdf.cell(w3, 7, safe_text("Vía de administración"), 0, 1, 'C', True)
        pdf.set_font('Arial', '', 8)
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(w1, 7, safe_text(" Medio de contraste / Ac. Gadoxético"), 0, 0, 'L', True)
        pdf.cell(w2, 7, "", 0, 0, 'C', True)
        pdf.cell(w3, 7, "", 0, 1, 'C', True)
        pdf.set_fill_color(252, 252, 252)
        pdf.cell(w1, 7, safe_text(" Suero fisiológico (NaCl 0,9%)"), 0, 0, 'L', True)
        pdf.cell(w2, 7, "", 0, 0, 'C', True)
        pdf.cell(w3, 7, "", 0, 1, 'C', True)
        pdf.ln(2)
    else:
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(190, 7, safe_text(" Creatinina: Sin registro"), 0, 1, 'L', True)
        pdf.cell(190, 7, safe_text(" Peso / Talla: Sin registro"), 0, 1, 'L', True)
        pdf.cell(190, 7, safe_text(" RESULTADO VFG: Sin contraste"), 0, 1, 'L', True)

    # ── PÁGINA 2: Información al Paciente ──────────────────────────────────
    pdf.add_page()

    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0, 0, 0)
    texto_proc = f"Procedimiento: {st.session_state.get('procedimiento', 'No especificado')}"
    if st.session_state.get('tiene_contraste'):
        texto_proc += " con uso de medio de contraste."
        pdf.multi_cell(0, 7, safe_text(texto_proc), 0, 'L')
    else:
        pdf.multi_cell(0, 7, safe_text(texto_proc), 0, 'L')
        pdf.ln(1)
        pdf.set_font('Arial', '', 9)
        pregunta = "¿Se aplicó medio de contraste adicionalmente?"
        ancho_txt = pdf.get_string_width(pregunta) + 2
        pdf.cell(ancho_txt, 7, safe_text(pregunta), 0, 0, 'L')
        pos_x, pos_y = pdf.get_x(), pdf.get_y()
        pdf.rect(pos_x + 2, pos_y + 1, 5, 5)
        pdf.ln(8)
    pdf.ln(3)

    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, "LEA ATENTA Y CUIDADOSAMENTE LO SIGUIENTE:", 0, 1, 'L')
    pdf.ln(2)

    sections_pdf = {
        "OBJETIVOS": (
            "La Resonancia Magnética (RM) es una segura técnica de Diagnóstico, que permite la "
            "adquisición de imágenes de gran sensibilidad en todos los planos del espacio de las "
            "estructuras del cuerpo. Tiene como objetivo obtener Información, datos funcionales y "
            "morfológicos para detectar precozmente una enfermedad.\n\n"
            "Para este examen eventualmente se puede requerir la utilización de un medio de "
            "contraste paramagnético de administración endovenosa llamado gadolinio, que permite "
            "realzar ciertos tejidos del cuerpo para un mejor diagnóstico."
        ),
        "CARACTERISTICAS": (
            "La Resonancia utiliza fuertes campos magnéticos y ondas de radiofrecuencia, por lo "
            "que es muy importante dejar fuera de la sala absolutamente todo lo que lleve consigo "
            "de tipo metálico y/o electrónico (relojes, pulseras, teléfonos, tarjetas magnéticas, "
            "etc). Si lleva material de este tipo en su cuerpo (fijaciones dentales, piercings, "
            "algunos tatuajes, balas o esquirlas metálicas) ciertos tipos de prótesis (valvulares, "
            "de cadera, de rodilla, clips metálicos, etc), o implantes, así como dispositivos "
            "electrónicos de carácter médico como bombas de insulina, prótesis auditivas, "
            "marcapasos, desfibriladores, etc. Avísenos, ya que puede contraindicar de manera "
            "absoluta la realización de este examen.\n\n"
            "Usted será posicionado en la camilla del equipo, según el estudio a realizar y se "
            "colocarán cerca de la zona a estudiar unos dispositivos (bobinas) que pueden ser de "
            "diversos tamaños. Esta exploración suele ser larga (entre 20 min y 1 hr según los "
            "casos). Notará ruido derivado del funcionamiento de la RM (por lo que le facilitaremos "
            "unos protectores auditivos), todo esto es normal y se le vigilará constantemente desde "
            "la sala de control.\n\nEs muy importante que permanezca quieto durante el estudio y "
            "siga las instrucciones del Tecnólogo Médico."
        ),
        "POTENCIALES RIESGOS": (
            "Existe una muy baja posibilidad de que se presente una reacción adversa al medio de "
            "contraste (0.07-2.4%) la mayoría de carácter leve fundamentalmente nauseas o cefaleas "
            "al momento de la inyección.\n\nPacientes con deterioro importante de la función renal, "
            "poseen riesgo de desarrollo de fibrosis nefrogénica sistémica."
        )
    }
    for tit, cont in sections_pdf.items():
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(128, 0, 32)
        pdf.cell(0, 6, safe_text(tit), 0, 1, 'L')
        pdf.set_font('Arial', '', 9)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 5, safe_text(cont))
        pdf.ln(3)

    consentimiento_texto = (
        "He sido informado de mi derecho de anular o revocar posteriormente este documento, "
        "dejándolo constatado por escrito y firmado por mi o mi representante.\n\n"
        "Autorizo la realización del procedimiento anteriormente especificado y las acciones que "
        "sean necesarias en caso de surgir complicaciones durante el procedimiento. Además, doy "
        "consentimiento para que se administren medicamentos y/o infusiones que se requieran para "
        "la realización de este."
    )
    pdf.set_font('Arial', '', 9)
    pdf.multi_cell(0, 5, safe_text(consentimiento_texto))

    # ── Sección de Firmas ─────────────────────────────────────────────────
    pdf.ln(5)
    y_pos_firmas = pdf.get_y()
    ancho_caja_izq, inicio_caja_izq = 65, 20
    ancho_caja_der, inicio_caja_der = 65, 125
    firma_w, firma_h = 45, 12
    sello_size = 28
    x_firma_img = inicio_caja_izq + (ancho_caja_izq - firma_w) / 2
    x_sello_img = inicio_caja_der + (ancho_caja_der - sello_size) / 2

    ruta_p_local = datos.get('firma_img')
    if ruta_p_local and os.path.exists(ruta_p_local):
        pdf.image(ruta_p_local, x=x_firma_img, y=y_pos_firmas, w=firma_w, h=firma_h)
    if os.path.exists("sello_norte_imagen.png"):
        pdf.image("sello_norte_imagen.png", x=x_sello_img, y=y_pos_firmas - 2,
                  w=sello_size, h=sello_size)

    data_y_textos = y_pos_firmas + sello_size + 2
    nombre_tutor_pdf = datos.get('nombre_tutor', '').strip().upper()
    nombre_paciente_pdf = datos.get('nombre', 'PACIENTE').strip().upper()
    hash_full = datos.get('hash_documento', '')
    hash_short = (f"{hash_full[:8]}-{hash_full[8:16]}".upper()
                  if hash_full else "PENDIENTE DE GENERACIÓN")

    if nombre_tutor_pdf:
        validador_pac = nombre_tutor_pdf
        cargo_pac = datos.get('parentesco_tutor', 'REPRESENTANTE LEGAL').strip().upper()
        if datos.get('sin_rut_tutor'):
            doc_pac = f"{datos.get('tipo_doc_tutor', 'DOC').upper()}: {datos.get('num_doc_tutor', '')}"
        else:
            doc_pac = f"RUT: {datos.get('rut_tutor', 'S/R')}"
    else:
        validador_pac = nombre_paciente_pdf
        cargo_pac = "PACIENTE TITULAR"
        if datos.get('sin_rut'):
            doc_pac = f"{datos.get('tipo_doc', 'DOC').upper()}: {datos.get('num_doc', '')}"
        else:
            doc_pac = f"RUT: {datos.get('rut', 'S/R')}"

    pdf.set_text_color(60, 60, 60)
    pdf.set_y(data_y_textos)
    pdf.set_font('Arial', 'B', 6)
    pdf.set_x(inicio_caja_izq)
    pdf.cell(ancho_caja_izq, 3.5, safe_text(f"VALIDADO POR: {validador_pac}"), 0, 0, 'C')
    pdf.set_x(inicio_caja_der)
    pdf.cell(ancho_caja_der, 3.5, "VALIDADO POR: PENDIENTE", 0, 1, 'C')
    pdf.set_font('Arial', '', 5.5)
    pdf.set_x(inicio_caja_izq)
    pdf.cell(ancho_caja_izq, 2.5, safe_text(cargo_pac), 0, 0, 'C')
    pdf.set_x(inicio_caja_der)
    pdf.cell(ancho_caja_der, 2.5, "TECNÓLOGO MÉDICO EN IMAGENOLOGÍA", 0, 1, 'C')
    pdf.set_x(inicio_caja_izq)
    pdf.cell(ancho_caja_izq, 2.5, safe_text(doc_pac), 0, 0, 'C')
    pdf.set_x(inicio_caja_der)
    pdf.cell(ancho_caja_der, 2.5, "ESPECIALIDAD RESONANCIA MAGNÉTICA", 0, 1, 'C')
    pdf.set_x(inicio_caja_izq)
    pdf.cell(ancho_caja_izq, 2.5, "", 0, 0, 'C')
    pdf.set_x(inicio_caja_der)
    pdf.cell(ancho_caja_der, 2.5, "REG. SIS: PENDIENTE", 0, 1, 'C')
    pdf.ln(1)
    pdf.set_font('Arial', 'I', 4.5)
    pdf.set_x(inicio_caja_izq)
    pdf.cell(ancho_caja_izq, 2.5, safe_text(f"HUELLA SHA-256: {hash_short}"), 0, 0, 'C')
    pdf.set_x(inicio_caja_der)
    pdf.cell(ancho_caja_der, 2.5, "HUELLA SHA-256: PENDIENTE", 0, 1, 'C')
    pdf.set_text_color(0, 0, 0)

    # ── Compilación binaria segura ─────────────────────────────────────────
    try:
        return bytes(pdf.output())
    except Exception:
        salida_cruda = pdf.output(dest='S')
        if isinstance(salida_cruda, str):
            return salida_cruda.encode('latin-1')
        elif isinstance(salida_cruda, bytearray):
            return bytes(salida_cruda)
        return salida_cruda

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
@st.fragment
def vista_cuestionario_clinico():
    """
    Cuestionario HL7 FHIR QuestionnaireResponse.
    Cubre bioseguridad, antecedentes clínicos, quirúrgicos y exámenes previos.
    """
    if "cuestionario" not in st.session_state.form:
        st.session_state.form["cuestionario"] = {}

    # ── SECCIÓN 1: Bioseguridad Magnética ───────────────────────────────────
    st.markdown('<div class="section-header">1. Bioseguridad Magnética</div>',
                unsafe_allow_html=True)

    is_marcapaso = st.session_state.form.get("bio_marcapaso") == "Sí"
    bio_marcapaso_toggle = st.toggle("Marcapasos cardiaco", value=is_marcapaso)
    st.session_state.form["bio_marcapaso"] = "Sí" if bio_marcapaso_toggle else "No"

    is_implante = st.session_state.form.get("bio_implantes") == "Sí"
    bio_implante_toggle = st.toggle(
        "Implantes metálicos, quirúrgicos, prótesis o dispositivos electrónicos",
        value=is_implante
    )
    st.session_state.form["bio_implantes"] = "Sí" if bio_implante_toggle else "No"

    if (st.session_state.form["bio_marcapaso"] == "Sí"
            or st.session_state.form["bio_implantes"] == "Sí"):
        st.session_state.form["bio_detalle"] = st.text_area(
            "Detalle (Tipo y Ubicación):",
            value=st.session_state.form.get("bio_detalle", ""),
            height=70
        )
    else:
        st.session_state.form["bio_detalle"] = ""

    # ── SECCIÓN 2: Antecedentes Clínicos ────────────────────────────────────
    st.markdown('<div class="section-header">2. Antecedentes Clínicos</div>',
                unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    k1 = [("clin_ayuno", "Ayuno (2 hrs o más)"), ("clin_asma", "Asma"),
          ("clin_hiperten", "Hipertensión"), ("clin_hipertiroid", "Hipertiroidismo")]
    k2 = [("clin_diabetes", "Diabetes"), ("clin_alergico", "Alergias severas"),
          ("clin_metformina", "Suspende Metformina (48h antes)"),
          ("clin_renal", "Insuficiencia Renal")]
    k3 = [("clin_dialisis", "Diálisis"), ("clin_claustro", "Claustrofóbico"),
          ("clin_embarazo", "Embarazo"), ("clin_lactancia", "Lactancia")]

    for col, keys in zip([c1, c2, c3], [k1, k2, k3]):
        for k, label in keys:
            valor_bool = (st.session_state.form.get(k) == "Sí")
            resultado = col.toggle(label, value=valor_bool, key=f"toggle_{k}")
            st.session_state.form[k] = "Sí" if resultado else "No"

            if k == "clin_alergico" and st.session_state.form["clin_alergico"] == "Sí":
                st.session_state.form["alergias_detalle"] = col.text_input(
                    "⚠️ Especifique alergias (Fármacos/Alimentos):",
                    value=st.session_state.form.get("alergias_detalle", ""),
                    key="txt_alergias"
                )
            elif k == "clin_alergico":
                st.session_state.form["alergias_detalle"] = ""

    # ── Condiciones Especiales ──────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**¿Posee alguna condición o requerimiento especial?**")
    toggle_condicion = st.toggle("Sí, deseo indicar una condición especial",
                                  key="toggle_cond")
    if toggle_condicion:
        opciones_condicion = [
            "Discapacidad física o movilidad reducida (ej.: silla de ruedas, amputaciones)",
            "Condición del neurodesarrollo o neurodivergencia (ej.: TEA, TDAH)",
            "Discapacidad intelectual o cognitiva",
            "Discapacidad sensorial (ej.: visual, auditiva)",
            "Otra"
        ]
        st.session_state.form["condiciones"] = st.multiselect(
            "Seleccione todas las que correspondan:",
            opciones_condicion,
            default=st.session_state.form.get("condiciones", [])
        )
        st.session_state.form["condicion_detalle"] = st.text_input(
            "Detalle de la condición o requerimiento:",
            value=st.session_state.form.get("condicion_detalle", "")
        )
    else:
        st.session_state.form["condiciones"] = []
        st.session_state.form["condicion_detalle"] = ""

    # ── SECCIÓN 3: Antecedentes Quirúrgicos y Oncológicos ──────────────────
    st.markdown('<div class="section-header">3. Antecedentes Quirúrgicos y Oncológicos</div>',
                unsafe_allow_html=True)
    is_cirugia = st.session_state.form.get("quir_cirugia_check") == "Sí"
    cirugia_toggle = st.toggle("¿Ha sido sometido a alguna cirugía?", value=is_cirugia)
    st.session_state.form["quir_cirugia_check"] = "Sí" if cirugia_toggle else "No"
    if st.session_state.form["quir_cirugia_check"] == "Sí":
        st.session_state.form["quir_cirugia_detalle"] = st.text_area(
            "Detalle nombre de la cirugía y fecha:",
            value=st.session_state.form.get("quir_cirugia_detalle", ""),
            height=70
        )
    else:
        st.session_state.form["quir_cirugia_detalle"] = ""

    is_cancer = st.session_state.form.get("quir_cancer_check") == "Sí"
    cancer_toggle = st.toggle("¿Cursa o ha cursado cáncer?", value=is_cancer)
    st.session_state.form["quir_cancer_check"] = "Sí" if cancer_toggle else "No"

    if st.session_state.form["quir_cancer_check"] == "Sí":
        st.session_state.form["quir_cancer_detalle"] = st.text_area(
            "Tipo de cáncer y etapa:",
            value=st.session_state.form.get("quir_cancer_detalle", ""),
            height=70
        )
        st.markdown("**¿Has tenido alguno de estos tratamientos?**")
        ct1, ct2, ct3, ct4 = st.columns(4)
        st.session_state.form["rt"] = ct1.checkbox("Radioterapia (RT)",
                                                     value=st.session_state.form.get("rt", False))
        st.session_state.form["qt"] = ct2.checkbox("Quimioterapia (QT)",
                                                     value=st.session_state.form.get("qt", False))
        st.session_state.form["bt"] = ct3.checkbox("Braquiterapia (BT)",
                                                     value=st.session_state.form.get("bt", False))
        st.session_state.form["it"] = ct4.checkbox("Inmunoterapia (IT)",
                                                     value=st.session_state.form.get("it", False))
        st.session_state.form["quir_otro_trat"] = st.text_input(
            "Algún otro tratamiento:",
            value=st.session_state.form.get("quir_otro_trat", "")
        )

    # ── SECCIÓN 4: Exámenes Anteriores ─────────────────────────────────────
    st.markdown('<div class="section-header">4. Exámenes Anteriores y Respaldos</div>',
                unsafe_allow_html=True)
    is_exam_prev = st.session_state.form.get("has_examenes_previos") == "Sí"
    exam_prev_toggle = st.toggle("¿Tiene exámenes anteriores relacionados?",
                                  value=is_exam_prev, key="tgl_exam_prev")
    st.session_state.form["has_examenes_previos"] = "Sí" if exam_prev_toggle else "No"

    if st.session_state.form["has_examenes_previos"] == "Sí":
        cols_ex = st.columns(5)
        st.session_state.form["ex_rx"] = cols_ex[0].checkbox("Rx",
            value=st.session_state.form.get("ex_rx", False))
        st.session_state.form["ex_mg"] = cols_ex[1].checkbox("MG",
            value=st.session_state.form.get("ex_mg", False))
        st.session_state.form["ex_eco"] = cols_ex[2].checkbox("Eco",
            value=st.session_state.form.get("ex_eco", False))
        st.session_state.form["ex_tc"] = cols_ex[3].checkbox("TC",
            value=st.session_state.form.get("ex_tc", False))
        st.session_state.form["ex_rm"] = cols_ex[4].checkbox("RM",
            value=st.session_state.form.get("ex_rm", False))
        st.session_state.form["ex_otros"] = st.text_input("Otros:",
            value=st.session_state.form.get("ex_otros", ""))

        st.markdown("**A. Archivos (PDF / Fotos)**")
        st.file_uploader("Adjunte informes (Máx. 4)", type=["pdf", "jpg", "jpeg"],
                          accept_multiple_files=True, key="up_anteriores_ui")

        st.markdown("**B. Links a Portales Externos o DICOM**")
        col_l1, col_p1 = st.columns([3, 1])
        st.session_state.form["link_exam_1"] = col_l1.text_input(
            "🔗 Link visualización 1:",
            value=st.session_state.form.get("link_exam_1", ""),
            placeholder="https://..."
        )
        st.session_state.form["pin_exam_1"] = col_p1.text_input(
            "🔑 PIN / Clave 1:",
            value=st.session_state.form.get("pin_exam_1", ""),
            placeholder="Ej: 1234"
        )
        col_l2, col_p2 = st.columns([3, 1])
        st.session_state.form["link_exam_2"] = col_l2.text_input(
            "🔗 Link visualización 2 (Opcional):",
            value=st.session_state.form.get("link_exam_2", "")
        )
        st.session_state.form["pin_exam_2"] = col_p2.text_input(
            "🔑 PIN / Clave 2:",
            value=st.session_state.form.get("pin_exam_2", "")
        )
    else:
        for k in ["ex_rx", "ex_mg", "ex_eco", "ex_tc", "ex_rm"]:
            st.session_state.form[k] = False
        for k in ["ex_otros", "link_exam_1", "pin_exam_1", "link_exam_2", "pin_exam_2"]:
            st.session_state.form[k] = ""

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
# MODAL DE CONSENTIMIENTO INICIAL (Ley 19.799 / HL7 FHIR Consent)
# =====================================================================
@st.dialog("Aviso Legal y Consentimiento (FES / HL7 FHIR)")
def modal_consentimiento():
    st.markdown(
        "Para autorizar su resonancia magnética, utilizaremos un sistema de "
        "**Firma Electrónica Simple (FES)**. Al firmar en la pantalla, el sistema "
        "capturará de forma encriptada su identidad junto con la fecha y hora exacta "
        "del procedimiento."
    )
    st.markdown(
        "Sus respuestas de seguridad, imágenes y este consentimiento se guardarán en "
        "su Ficha Clínica Electrónica, protegidos bajo la **Ley chilena de Protección "
        "de Datos Personales**. Adicionalmente, esta información se estructurará bajo "
        "el estándar internacional **HL7 FHIR**, lo que permite que, si usted lo "
        "solicita, sus datos médicos puedan ser transmitidos de forma segura e "
        "interoperable a otros centros de salud para la continuidad de su atención."
    )
    st.markdown(
        "**¿Comprende cómo se procesará su firma y está de acuerdo con el registro "
        "e interoperabilidad segura de sus datos?**"
    )
    c1, c2 = st.columns(2)
    if c1.button("Sí, comprendo y acepto", type="primary", use_container_width=True):
        st.session_state.abrir_modal = False
        st.session_state.step = 1
        st.rerun()
    if c2.button("Cancelar", use_container_width=True):
        st.session_state.abrir_modal = False
        st.rerun()

# =====================================================================
# 5.4 MAIN LOOP (ENRUTADOR SPA)
# =====================================================================
def main():
    # ── 1. RENDERIZADO CONDICIONAL: PASO 0 (BARRERA LEGAL Y VIDEO) ──
    if st.session_state.step == 0:
        try:
            with open("video_bienvenida.mp4", "rb") as video_file:
                video_bytes = video_file.read()
            video_base64 = base64.b64encode(video_bytes).decode("utf-8")
            video_data_url = f"data:video/mp4;base64,{video_base64}"
        except Exception:
            video_data_url = ""

        st.markdown(f"""
            <style>
            .stApp {{ overflow: hidden !important; background-color: black !important; }}
            #video-fondo {{
                position: fixed !important; top: 50% !important; left: 50% !important;
                width: 100vw !important; height: 100vh !important;
                transform: translate(-50%, -50%) !important; object-fit: cover !important; z-index: 0 !important;
            }}
            div[data-testid="stButton"] {{
                position: fixed !important; top: 0 !important; left: 0 !important;
                width: 100vw !important; height: 100vh !important; opacity: 0 !important; z-index: 10 !important;
            }}
            div[data-testid="stButton"] button {{ width: 100vw !important; height: 100vh !important; cursor: pointer !important; }}
            </style>
            <video id="video-fondo" autoplay loop muted playsinline><source src="{video_data_url}" type="video/mp4"></video>
        """, unsafe_allow_html=True)

        # Botón invisible gigante que atrapa el primer clic
        if st.button(" ", key="btn_invisible_start"):
            st.session_state.abrir_modal = True
            st.rerun()

        if st.session_state.abrir_modal:
            modal_consentimiento()

    # ── 2. RENDERIZADO CONDICIONAL: PASO 1 EN ADELANTE (LA APLICACIÓN) ──
    else:
        # Menú flotante corporativo (Visible en toda la app)
        st.markdown("""
            <style>
            .stApp { overflow: auto !important; }
            @keyframes pulse-glow { 0% { box-shadow: 0 0 0 0 rgba(40,167,69,0.6); } 70% { box-shadow: 0 0 0 12px rgba(255,255,255,0.4); } 100% { box-shadow: 0 0 0 0 rgba(255,255,255,0); } }
            .menu-flotante { position: fixed !important; bottom: 45px !important; right: 1px !important; z-index: 999999 !important; display: flex !important; flex-direction: column !important; align-items: flex-end !important; gap: 10px !important; }
            .opciones-contacto { display: none !important; flex-direction: column !important; gap: 8px !important; margin-bottom: 5px !important; }
            .menu-flotante:hover .opciones-contacto, .menu-flotante:focus-within .opciones-contacto { display: flex !important; }
            .btn-opcion { display: flex !important; align-items: center !important; gap: 10px !important; text-decoration: none !important; color: #333 !important; font-size: 13px !important; font-weight: 600 !important; padding: 10px 15px !important; border-radius: 12px !important; backdrop-filter: blur(8px) !important; border: 1px solid rgba(255,255,255,0.6) !important; white-space: nowrap !important; box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important; }
            .color-telefono { background-color: rgba(211, 237, 212, 0.85) !important; }
            .color-whatsapp { background-color: rgba(165, 214, 167, 0.85) !important; color: #155724 !important; }
            .color-email { background-color: rgba(255, 255, 255, 0.85) !important; }
            .btn-principal { background: linear-gradient(135deg, rgba(40,167,69,0.8) 0%, rgba(255,255,255,0.95) 100%) !important; color: #004d00 !important; border-radius: 50px !important; padding: 14px 26px !important; font-weight: bold !important; cursor: pointer !important; box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important; animation: pulse-glow 2s infinite !important; backdrop-filter: blur(5px) !important; border: 1px solid rgba(40,167,69,0.4) !important; display: flex !important; align-items: center !important; gap: 10px !important; }
            </style>
            <div class="menu-flotante" tabindex="0">
                <div class="opciones-contacto">
                    <a class="btn-opcion color-telefono" href="tel:+56572466423" target="_blank">📞 F. Bilbao: +56 57 246 6423</a>
                    <a class="btn-opcion color-telefono" href="tel:+56572466425" target="_blank">📞 A. Fernández: +56 57 246 6425</a>
                    <a class="btn-opcion color-email" href="mailto:resonancia@cdnorteimagen.cl" target="_blank">✉️ resonancia@cdnorteimagen.cl</a>
                </div>
                <div class="btn-principal" title="Soporte Norte Imagen">💬 ¿Necesitas ayuda?</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<h1 style='text-align: center; color: #800020;'>🏥 Admisión y Consentimiento Clínico</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666;'>Plataforma Integral Norte Imagen</p>", unsafe_allow_html=True)
        
        tab_paciente, tab_examenes, tab_clinica, tab_firma, tab_resumen = st.tabs(["👤 1. Paciente", "🩻 2. Exámenes", "⚕️ 3. Clínica", "✍️ 4. Firma (FES)", "📄 5. Resumen y Envío"])
    
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
        
        # Validaciones estrictas MINSAL
        if not st.session_state.form.get("firma_trazada", False):
            st.error("✍️ Debe realizar la firma manuscrita en el recuadro de la pestaña anterior.")
        elif not st.session_state.get("fes_validado", False): 
            st.error("🔒 Complete la Validación FES (Código SMS/Email) en la pestaña anterior.")
        elif not st.session_state.form.get("veracidad", False):
            st.error("⚖️ Debe confirmar la veracidad de los datos en la pestaña anterior.")
        else:
            # 1. Identificadores únicos
            rut_limpio = str(st.session_state.form.get('rut_titular', 'SIN_RUT')).replace(".", "").replace("-", "")
            timestamp_actual = datetime.now(pytz.timezone('America/Santiago')).strftime('%Y%m%d%H%M')
            id_doc = f"DOC_{rut_limpio}_{timestamp_actual}"
            
            st.info("✅ Todo listo. Presione el botón para compilar su ficha, encriptarla y enviarla a la central.")

            if st.button("🚀 Encriptar, Enviar y Generar PDF", type="primary", use_container_width=True):
                with st.spinner("Procesando datos bajo estándar HL7 FHIR y cifrado AES-256..."):
                    try:
                        # ── 1. GENERACIÓN DEL PDF CLÍNICO HUMANO ──
                        # Necesitamos generar el PDF primero para que el paciente lo pueda descargar
                        pdf_bytes = generar_pdf_clinico(st.session_state.form)
                        nombre_pdf_final = f"Consentimiento_RM_{rut_limpio}.pdf"

                        # ── 2. SUBIDA DE ARCHIVOS A FIREBASE STORAGE (FIRMA Y PDF) ──
                        url_firma = ""
                        url_pdf = ""
                        if bucket is not None:
                            # Subir PDF
                            blob_pdf = bucket.blob(f"fichas_clinicas/{timestamp_actual}/{nombre_pdf_final}")
                            blob_pdf.upload_from_string(pdf_bytes, content_type='application/pdf')
                            url_pdf = f"fichas_clinicas/{timestamp_actual}/{nombre_pdf_final}"
                        
                        # ── 3. ESTRUCTURACIÓN HL7 FHIR ──
                        bundle_final = generar_bundle_fhir_completo(st.session_state.form, id_doc)
                        
                        # Inyectamos Metadatos de Auditoría y URLs del Storage al Bundle
                        bundle_final["meta"] = {
                            "security": [{"code": "AES-256-GCM"}],
                            "client_ip": obtener_ip_cliente(),
                            "fes_signature_hash": st.session_state.get("fes_codigo_generado", ""),
                            "storage_references": {
                                "pdf_document": url_pdf,
                                "firma_manuscrita": url_firma
                            }
                        }

                        # ── 4. ENCRIPTACIÓN AES-256 ──
                        gestor_crypto = GestorCriptografico()
                        datos_encriptados = gestor_crypto.encriptar(bundle_final)
                        
                        # ── 5. GUARDADO EN FIRESTORE (LA BÓVEDA) ──
                        if db is not None:
                            db.collection("admisiones_fhir").document(id_doc).set({
                                "paciente_rut": rut_limpio,
                                "timestamp": datetime.now(pytz.utc).isoformat(),
                                "payload_encriptado_aes": datos_encriptados
                            })
                            
                            st.session_state.registro_guardado_db = True
                            st.balloons()
                            st.success(f"¡Transmisión Segura Completada! ID de Registro: {id_doc}")
                            
                            # Mostramos el botón de descarga del PDF sin recargar la página (Magia SPA)
                            st.download_button(
                                label="📥 Descargar Copia del Consentimiento (PDF)", 
                                data=pdf_bytes, 
                                file_name=nombre_pdf_final, 
                                mime="application/pdf",
                                width="stretch"
                            )
                        else:
                            st.error("Error: Conexión a Base de Datos no disponible. Avise al tecnólogo.")
                            
                    except Exception as e:
                        st.error(f"Error en el proceso de encriptación/envío: {e}")

    if __name__ == "__main__":
        main()

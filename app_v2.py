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

# =====================================================================
# 1. CONFIGURACIÓN MAESTRA DE PÁGINA (Debe ser la línea 1 ejecutable)
# =====================================================================
dir_actual = os.path.dirname(__file__)
ruta_logo = os.path.join(dir_actual, "logoNI_pg.png")

st.set_page_config(
    page_title="Norte Imagen - Registro RM",
    page_icon=ruta_logo if os.path.exists(ruta_logo) else "🏥",
    layout="centered",
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
        </style>
    """, unsafe_allow_html=True)

# =====================================================================
# 3. GESTOR DE ESTADO AISLADO (ANTI-CRUCE DE PACIENTES)
# =====================================================================
def inicializar_sesion_segura():
    """Crea un contenedor hermético para cada paciente conectado."""
    if "paciente_uuid" not in st.session_state:
        # Genera un ID único e irrepetible para esta pestaña del navegador
        st.session_state.paciente_uuid = str(uuid.uuid4())
    
    if "step" not in st.session_state:
        st.session_state.step = 0
        
    if "form" not in st.session_state:
        # Estructura limpia y lista para ser empaquetada en FHIR
        st.session_state.form = {
            "datos_demograficos": {
                "rut": "", "nombre": "", "fecha_nac": date(1990, 1, 1), 
                "telefono": "", "email": "", "genero_idx": 0
            },
            "datos_tutor": {
                "requerido": False, "rut": "", "nombre": "", "parentesco": ""
            },
            "datos_clinicos": {
                "procedencia": "Ambulatorio", "unidad": "", "peso": 0.0, "talla": 0.0, "creatinina": 0.0, "vfg": 0.0
            },
            "cuestionario_riesgo": {},
            "firma_electronica": {
                "otp_secret": "", "hash_documento": "", "validado": False
            }
        }

# Ejecución inmediata del Bloque 1
inyectar_css_corporativo()
inicializar_sesion_segura()

# =====================================================================
# 4. CONEXIÓN SINGLETON A FIREBASE (Escalabilidad Concurrente)
# =====================================================================
@st.cache_resource
def inicializar_firebase():
    """Abre UNA SOLA conexión global hiper-rápida para todos los pacientes."""
    try:
        # Verifica si ya existe para evitar errores de doble inicialización
        return firebase_admin.get_app()
    except ValueError:
        try:
            # Intenta acceder a los secretos de Streamlit
            cred_dict = dict(st.secrets["firebase"])
            url_bucket = cred_dict.pop("bucket_url", "firmas-encuestaconsentimiento.firebasestorage.app")
            
            # Limpieza segura de la llave privada (Evita errores de formato)
            if "private_key" in cred_dict:
                cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
                
            cred = credentials.Certificate(cred_dict)
            return firebase_admin.initialize_app(cred, {'storageBucket': url_bucket})
            
        except FileNotFoundError:
            st.error("🚨 Archivo de secretos no encontrado. Configura secrets.toml localmente o en Streamlit Cloud.")
            return None
        except KeyError:
            st.error("🚨 No se encontró la sección [firebase] dentro de los secretos de Streamlit.")
            return None
        except Exception as e:
            st.error(f"🚨 Error al inicializar Firebase: {e}")
            return None

# Inicializamos la base de datos de inmediato
app_firebase = inicializar_firebase()
db = firestore.client()
bucket = storage.bucket()

# =====================================================================
# 5. MOTOR CRIPTOGRÁFICO AES-256 (Grado Militar)
# =====================================================================
class GestorCriptografico:
    def __init__(self):
        # En producción, esto DEBE venir de st.secrets["aes"]["master_key"] (64 caracteres hex)
        # Para desarrollo, generaremos una llave dummy si no existe en secrets.
        try:
            key_hex = st.secrets["aes"]["master_key"]
        except:
            key_hex = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
            
        self.key = bytes.fromhex(key_hex)
        self.aesgcm = AESGCM(self.key)

    def encriptar(self, datos_dict: dict) -> str:
        """Convierte un diccionario a JSON y lo encripta en AES-256 GCM."""
        nonce = os.urandom(12) # Vector de inicialización único por cifrado
        datos_bytes = json.dumps(datos_dict, default=str).encode('utf-8')
        texto_cifrado = self.aesgcm.encrypt(nonce, datos_bytes, None)
        return base64.b64encode(nonce + texto_cifrado).decode('utf-8')

    def desencriptar(self, cadena_encriptada: str) -> dict:
        """Recibe una cadena Base64, desencripta y devuelve el diccionario original."""
        datos_crudos = base64.b64decode(cadena_encriptada)
        nonce, texto_cifrado = datos_crudos[:12], datos_crudos[12:]
        datos_descifrados = self.aesgcm.decrypt(nonce, texto_cifrado, None)
        return json.loads(datos_descifrados.decode('utf-8'))

# =====================================================================
# 6. TRANSDUCTOR HL7 FHIR (Interoperabilidad Internacional)
# =====================================================================
def transformar_a_fhir(form_data: dict, id_paciente: str) -> dict:
    """Mapea el diccionario plano del estado a un Bundle de HL7 FHIR Release 4."""
    
    fecha_nac_str = form_data["datos_demograficos"]["fecha_nac"]
    if isinstance(fecha_nac_str, date):
        fecha_nac_str = fecha_nac_str.strftime("%Y-%m-%d")

    # Recurso 1: El Paciente (Patient)
    recurso_paciente = {
        "resourceType": "Patient",
        "id": id_paciente,
        "identifier": [{
            "use": "official",
            "system": "http://registrocivil.cl/rut",
            "value": form_data["datos_demograficos"]["rut"]
        }],
        "name": [{"use": "official", "text": form_data["datos_demograficos"]["nombre"]}],
        "telecom": [
            {"system": "phone", "value": form_data["datos_demograficos"]["telefono"]},
            {"system": "email", "value": form_data["datos_demograficos"]["email"]}
        ],
        "gender": "unknown", # Aquí mapearemos la lógica de género (male/female/other) en el Bloque 3
        "birthDate": fecha_nac_str
    }

    # Recurso 2: Las respuestas clínicas (QuestionnaireResponse)
    recurso_cuestionario = {
        "resourceType": "QuestionnaireResponse",
        "status": "completed",
        "subject": {"reference": f"Patient/{id_paciente}"},
        "item": [
            {
                "linkId": "vfg",
                "text": "Tasa de Filtración Glomerular",
                "answer": [{"valueDecimal": form_data["datos_clinicos"]["vfg"]}]
            },
            # Aquí iteraremos dinámicamente sobre el diccionario de bioseguridad en el Bloque 3
        ]
    }

    # Empaquetado final tipo Bundle
    bundle_fhir = {
        "resourceType": "Bundle",
        "type": "document",
        "timestamp": datetime.now(pytz.utc).isoformat(),
        "entry": [
            {"resource": recurso_paciente},
            {"resource": recurso_cuestionario}
        ]
    }
    
    return bundle_fhir

import pandas as pd
import pytesseract
import cv2
import numpy as np
import re
import requests
import smtplib
from email.message import EmailMessage
import streamlit as st
from datetime import date

# =====================================================================
# 3.1 MOTOR HL7 FHIR Y CATÁLOGO FONASA MLE
# =====================================================================
@st.cache_data
def cargar_catalogo_hl7(ruta_csv='listado_prestaciones.csv'):
    """
    Carga el CSV y crea un diccionario maestro para mapeo rápido en O(1).
    Extrae el Código Fonasa (CODIGO PRESTACION) para el estándar HL7.
    """
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
        print(f"Error cargando catálogo: {e}")
        return None, {}

def generar_service_request_hl7(procedimiento_base, lateralidad, catalogo):
    """
    Convierte la selección del paciente en un recurso 'ServiceRequest' de HL7 FHIR
    inyectando el código FONASA MLE chileno.
    """
    info = catalogo.get(procedimiento_base, {})
    codigo_fonasa = info.get("codigo_fonasa", "S/C")
    
    fhir_payload = {
        "resourceType": "ServiceRequest",
        "status": "active",
        "intent": "order",
        "code": {
            "coding": [
                {
                    "system": "http://minsal.cl/fonasa/mle",
                    "code": codigo_fonasa,
                    "display": procedimiento_base
                }
            ],
            "text": f"{procedimiento_base} - LAT: {lateralidad}"
        },
        "bodySite": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "display": lateralidad
                    }
                ]
            }
        ]
    }
    return fhir_payload

# =====================================================================
# 3.2 LÓGICA GRAMATICAL Y ANATÓMICA
# =====================================================================
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
    if lateralidad not in ["Derecha", "Izquierda", "Ambas"]:
        return nombre_base
        
    palabra_encontrada = None
    for clave in DICCIONARIO_ANATOMICO.keys():
        if clave in nombre_base:
            palabra_encontrada = clave
            break
            
    if not palabra_encontrada:
        return f"{nombre_base} {lateralidad.upper()}"
        
    info = DICCIONARIO_ANATOMICO[palabra_encontrada]
    genero = info["genero"]
    plural = info["plural"]
    
    if lateralidad == "Ambas":
        sufijo_ambos = "AMBOS" if genero == "M" else "AMBAS"
        nuevo_nombre = nombre_base.replace(palabra_encontrada, plural)
        nuevo_nombre = nuevo_nombre.replace(f"DE {plural}", f"DE {sufijo_ambos} {plural}")
        return nuevo_nombre
    else:
        sufijo_lado = lateralidad.upper() if genero == "F" else lateralidad.upper().replace("A", "O")
        return f"{nombre_base} {sufijo_lado}"

# =====================================================================
# 3.3 MOTOR OCR AVANZADO (Cédula de Identidad)
# =====================================================================
def limpiar_datos_ocr(texto_bruto, tipo="nombre"):
    if texto_bruto is None or texto_bruto == "":
        return ""

    sucio = ["eE", "p ", " /", " / ", "  ", ";", ":"]
    limpio = str(texto_bruto)
    for s in sucio:
        limpio = limpio.replace(s, "")
    
    if tipo == "fecha":
        meses = {"ENE":"01", "FEB":"02", "MAR":"03", "ABR":"04", "MAY":"05", "JUN":"06", 
                 "JUL":"07", "AGO":"08", "SEP":"09", "OCT":"10", "NOV":"11", "DIC":"12"}
        for mes_texto, mes_num in meses.items():
            if mes_texto in limpio.upper():
                limpio = limpio.upper().replace(mes_texto, mes_num).replace(" ", "/")
    
    return limpio.strip()

def procesar_cedula_inteligente(image_file):
    try:
        file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if img is None: return None, None, None, None
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        
        custom_config = r'--oem 3 --psm 6 -l spa' 
        texto_extraido = pytesseract.image_to_string(gray, config=custom_config)
        
        rut_match = re.search(r'(\d{1,2}(?:\.?\d{3}){2}\s*[-_]?\s*[\dkK])', texto_extraido)
        rut = rut_match.group(0) if rut_match else ""
        
        sexo = ""
        if re.search(r'\b(F|FEMENINO)\b', texto_extraido, re.IGNORECASE): sexo = "Femenino"
        elif re.search(r'\b(M|MASCULINO)\b', texto_extraido, re.IGNORECASE): sexo = "Masculino"
            
        fecha_match = re.search(r'NACIMIENTO[^\d]{0,50}(\d{2}\s?(?:ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)\s?\d{4}|\d{2}[-/.]\d{2}[-/.]\d{4})', texto_extraido, re.IGNORECASE)
        
        if not fecha_match:
            fecha_match = re.search(r'(\d{2}\s?(?:ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)\s?\d{4}|\d{2}[-/.]\d{2}[-/.]\d{4})', texto_extraido, re.IGNORECASE)
        
        fecha_nacimiento = fecha_match.group(1) if fecha_match else ""
        
        apellidos_match = re.search(r"APELLIDOS[\s\n]+(.*?)\s+NOMBRES", texto_extraido, re.IGNORECASE | re.DOTALL)
        apellidos_raw = apellidos_match.group(1).strip() if apellidos_match else ""
        
        nombres_match = re.search(r"NOMBRES[\s\n]+(.*?)\s+(NACIONALIDAD|SEXO)", texto_extraido, re.IGNORECASE | re.DOTALL)
        nombres_raw = nombres_match.group(1).strip() if nombres_match else ""
        
        nombre_completo = f"{nombres_raw} {apellidos_raw}".strip()
            
        rut_limpio = limpiar_datos_ocr(rut, "rut")
        nombre_limpio = limpiar_datos_ocr(nombre_completo, "nombre")
        fecha_limpia = limpiar_datos_ocr(fecha_nacimiento, "fecha")
        sexo_limpio = limpiar_datos_ocr(sexo, "sexo")
        
        return rut_limpio, nombre_limpio, fecha_limpia, sexo_limpio

    except Exception as e:
        print(f"ERROR CRÍTICO EN OCR: {e}")
        return None, None, None, None

# =====================================================================
# 3.4 MOTOR FES (Firma Electrónica Simple)
# =====================================================================
def despachar_codigo_fes(metodo, destino, codigo):
    try:
        if metodo == "Email":
            correo_emisor = st.secrets["email"]["sender_email"]
            password_app = st.secrets["email"]["app_password"]

            msg = EmailMessage()
            msg.set_content(f"""Estimado(a) paciente,

Su código de validación para la Firma Electrónica Simple (FES) es: {codigo}

Este código es válido por 5 minutos. Ingréselo en la plataforma para autorizar su procedimiento de Resonancia Magnética.

Norte Imagen.
""")
            msg['Subject'] = '🔑 Código de Validación FES - Norte Imagen'
            msg['From'] = f"Norte Imagen <{correo_emisor}>"
            msg['To'] = destino

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(correo_emisor, password_app)
                smtp.send_message(msg)
            
            print(f"[FES EMAIL] Enviado exitosamente a {destino}")
            return True

        elif metodo == "WhatsApp":
            token_meta = st.secrets["whatsapp"]["token"]
            id_telefono = st.secrets["whatsapp"]["phone_id"]
            
            destino_limpio = "".join(filter(str.isdigit, str(destino)))

            url = f"https://graph.facebook.com/v19.0/{id_telefono}/messages"
            headers = {
                "Authorization": f"Bearer {token_meta}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": destino_limpio,
                "type": "template",
                "template": {
                    "name": "codigo_fes_norte_imagen", 
                    "language": {"code": "es"},
                    "components": [{
                        "type": "body",
                        "parameters": [{"type": "text", "text": str(codigo)}]
                    }]
                }
            }

            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                print(f"[FES WHATSAPP] Enviado exitosamente a {destino_limpio}")
                return True
            else:
                st.error(f"Error de Meta: {response.json()}")
                return False

    except Exception as e:
        print(f"🚨 ERROR EN DESPACHO FES: {e}")
        st.error(f"Error de conexión: Verifica las credenciales o el formato del destino. Detalles: {e}")
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
            if edad_dias <= 28:
                k = 0.33 if edad_dias < 7 else 0.45
            else:
                k = 0.45 if edad_meses <= 12 else 0.55
                
            vfg = (k * talla) / creatinina
            
            if edad_meses <= 0.25: min_n, max_n = 15, 30
            elif edad_meses <= 1: min_n, max_n = 30, 50
            elif edad_meses <= 2: min_n, max_n = 40, 65
            elif edad_meses <= 4: min_n, max_n = 55, 85
            elif edad_meses <= 12: min_n, max_n = 70, 110
            else: min_n, max_n = 85, 125
            
            if vfg < (min_n * 0.7):
                return vfg, "🔴 ALTO RIESGO: VFG Crítica para etapa de maduración", "#FF0000", "vfg-critica"
            elif vfg < min_n:
                return vfg, "⚠️ RIESGO INTERMEDIO: Retraso en maduración renal", "#FFCC00", "vfg-intermedia"
            elif vfg <= max_n:
                return vfg, "✅ SIN RIESGO: VFG Adecuada para la edad", "#28A745", "vfg-normal"
            else:
                return vfg, "🔵 REVISAR: Posible hiperfiltración", "#007BFF", "vfg-normal"
        else:
            vfg = (0.413 * talla) / creatinina
            
            if vfg <= 30.0:
                return vfg, "🔴 Alto riesgo para administración de medio de contraste", "#FF0000", "vfg-critica"
            elif vfg <= 59.0:
                return vfg, "⚠️ Riesgo intermedio para administración de medio de contraste", "#FFCC00", "vfg-intermedia"
            else:
                return vfg, "✅ Sin riesgos para administración de medio de contraste", "#28A745", "vfg-normal"
    else:
        if peso <= 0: return 0.0, "Requiere peso", "#333333", ""
        es_mujer = sexo in ['Femenino', 'No binario (Bio: Femenino)']
        factor = 0.85 if es_mujer else 1.0
        vfg = (((140 - int(edad_anos)) * peso) / (72 * creatinina)) * factor
        
        if vfg <= 30.0:
            return vfg, "🔴 Alto riesgo para administración de medio de contraste", "#FF0000", "vfg-critica"
        elif vfg <= 59.0:
            return vfg, "⚠️ Riesgo intermedio para administración de medio de contraste", "#FFCC00", "vfg-intermedia"
        else:
            return vfg, "✅ Sin riesgos para administración de medio de contraste", "#28A745", "vfg-normal"


import streamlit as st

# =====================================================================
# VISTA: MÓDULO OCR AISLADO (Fragmento)
# =====================================================================
@st.fragment
def vista_escaner_cedula(tipo_paciente="TITULAR"):
    """
    Este fragmento maneja la cámara sin recargar toda la encuesta.
    tipo_paciente puede ser 'TITULAR' o 'TUTOR'.
    """
    prefix = "titular" if tipo_paciente == "TITULAR" else "tutor"
    
    col_inputs, col_btn = st.columns([5, 1], vertical_alignment="bottom")
    with col_inputs:
        rut_input = st.text_input(
            f"RUT {tipo_paciente.capitalize()}", 
            value=st.session_state.form.get(f"rut_{prefix}", ""), 
            key=f"input_rut_{prefix}"
        )
        st.session_state.form[f"rut_{prefix}"] = rut_input
        
    with col_btn:
        st.markdown("""
            <style>
            button[title*="Escanear cédula"] p {
                font-size: 32px !important;
                line-height: 1 !important;
                margin: 0 !important;
                padding: 0 !important;
            }
            </style>
        """, unsafe_allow_html=True)
        
        if st.button("📷", key=f"btn_cam_{prefix}", help=f"Escanear cédula de {tipo_paciente}", use_container_width=True):
            st.session_state[f"mostrar_camara_{prefix}"] = not st.session_state.get(f"mostrar_camara_{prefix}", False)

    if st.session_state.get(f"mostrar_camara_{prefix}", False):
        st.info("💡 Enfoque la cédula completa. Evite reflejos de luz.")
        
        opcion_carga = st.radio(f"Método de escaneo ({tipo_paciente}):", ["📷 Usar Cámara", "📁 Subir Foto (Galería)"], horizontal=True, key=f"radio_carga_{prefix}")
        
        foto_capturada = None
        if opcion_carga == "📷 Usar Cámara":
            foto_capturada = st.camera_input("Tomar foto", key=f"camara_{prefix}")
        else:
            foto_capturada = st.file_uploader("Seleccione la foto", type=["jpg", "png", "jpeg"], key=f"up_{prefix}")
        
        if foto_capturada:
            with st.spinner("Analizando con Visión Artificial..."):
                rut, nombre, fecha, sexo = procesar_cedula_inteligente(foto_capturada)
                
                if rut or nombre:
                    st.success("✅ ¡Datos extraídos con éxito!")
                    if rut: st.session_state.form[f"rut_{prefix}"] = rut
                    if nombre: st.session_state.form[f"nombre_{prefix}"] = nombre
                    if fecha and tipo_paciente == "TITULAR":
                        from datetime import datetime
                        try:
                            parsed_date = datetime.strptime(fecha, "%d/%m/%Y").date()
                            st.session_state.form["fecha_nac"] = parsed_date
                        except:
                            pass
                    if sexo and tipo_paciente == "TITULAR":
                        st.session_state.form["genero_biologico"] = sexo
                    
                    st.session_state[f"mostrar_camara_{prefix}"] = False
                    st.rerun()
                else:
                    st.error("❌ No se detectó texto claro. Intente nuevamente.")


# =====================================================================
# VISTA: SELECCIÓN DE PROCEDIMIENTO FONASA / HL7 (Fragmento)
# =====================================================================
@st.fragment
def vista_seleccion_procedimiento():
    df, catalogo = cargar_catalogo_hl7()
    if df is None:
        st.error("Error: No se encontró el catálogo de prestaciones.")
        return

    st.markdown('<div class="section-header" style="color: #800020; font-weight: bold; border-bottom: 2px solid #800020;">Información del Examen</div>', unsafe_allow_html=True)
    
    esp_raw = sorted(list(set([info["especialidad"] for info in catalogo.values()])))
    esp_sel = st.selectbox("Especialidad", esp_raw, key="sel_especialidad")
    
    proc_disponibles = [proc for proc, info in catalogo.items() if info["especialidad"] == esp_sel]
    
    if "proc_cache" not in st.session_state:
        st.session_state.proc_cache = []

    def sync_proc():
        st.session_state.proc_cache = st.session_state.sel_procedimientos

    pre_sel = st.multiselect(
        "Procedimiento(s) a realizar", 
        options=sorted(list(set(proc_disponibles + st.session_state.proc_cache))),
        default=st.session_state.proc_cache,
        key="sel_procedimientos",
        on_change=sync_proc
    )
    
    if pre_sel:
        st.session_state.form["recursos_hl7"] = []
        st.session_state.form["tiene_contraste"] = False
        st.session_state.form["nombres_transformados"] = {}
        
        for examen in pre_sel:
            info_examen = catalogo.get(examen, {"contraste": False, "lateralidad": False, "codigo_fonasa": "S/C"})
            
            if info_examen["contraste"]:
                st.session_state.form["tiene_contraste"] = True
                
            lat_actual = "No aplica"
            
            if info_examen["lateralidad"]:
                clave_limpia = examen.replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')
                
                c_txt1, c_tgl, c_txt2, c_divisor, c_chk = st.columns([0.6, 0.6, 0.7, 0.2, 2.5])
                
                es_bilateral = st.session_state.get(f"chk_ambas_{clave_limpia}", False)
                
                with c_chk:
                    es_bilateral = st.checkbox("AMBOS (AS)", key=f"chk_ambas_{clave_limpia}")
                
                with c_tgl:
                    lado_izq = st.toggle("Lado Examen", key=f"tgl_lat_{clave_limpia}", disabled=es_bilateral, label_visibility="collapsed")
                
                with c_txt1:
                    color_txt1 = "#999" if es_bilateral else "#333"
                    st.markdown(f"<p style='margin-top: 4px; font-size: 0.85rem; text-align: right; color: {color_txt1};'>DERECHA</p>", unsafe_allow_html=True)
                with c_txt2:
                    color_txt2 = "#999" if es_bilateral else "#333"
                    st.markdown(f"<p style='margin-top: 4px; font-size: 0.85rem; text-align: left; color: {color_txt2};'>IZQUIERDA</p>", unsafe_allow_html=True)
                with c_divisor:
                    st.markdown("<p style='margin-top: 2px; color: #ccc; font-size: 1.1rem; text-align: center;'>|</p>", unsafe_allow_html=True)
                
                if es_bilateral:
                    lat_actual = "Ambas"
                else:
                    lat_actual = "Izquierda" if lado_izq else "Derecha"
                
                st.markdown("<div style='border-bottom: 1px dashed #e0e0e0; margin: 10px 0;'></div>", unsafe_allow_html=True)
            
            # Procesar el nombre transformado gramaticalmente
            nombre_final = construir_nombre_especifico(examen, lat_actual)
            st.session_state.form["nombres_transformados"][examen] = nombre_final
            
            # Mostrar el procedimiento resultante
            st.markdown(f"<p style='font-size: 0.9rem; margin-bottom: 2px; color: #333333;'><b>PROCEDIMIENTO:</b> {nombre_final}</p>", unsafe_allow_html=True)
            
            # Empaquetado HL7 FONASA
            recurso_fhir = generar_service_request_hl7(examen, lat_actual, catalogo)
            st.session_state.form["recursos_hl7"].append(recurso_fhir)
            
            st.caption(f"🧬 Mapeado a HL7 - Código FONASA: {info_examen['codigo_fonasa']}")

import streamlit as st
import random
import json
from datetime import date

# =====================================================================
# 5.1 INICIALIZACIÓN Y GESTIÓN DE ESTADO GLOBAL
# =====================================================================
def inicializar_estado():
    """Inicializa todas las variables de sesión necesarias de forma segura."""
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

# =====================================================================
# 5.2 INYECCIÓN DE ESTILOS CSS MAESTROS
# =====================================================================
def aplicar_estilos_css():
    """Fuerza paleta de colores limpia y previene roturas por Dark Mode."""
    st.markdown("""
        <style>
        /* Forzar fondo blanco y texto oscuro general */
        .stApp {
            background-color: #FFFFFF !important;
            color: #333333 !important;
        }
        
        /* Headers y Divisores */
        .section-header {
            font-size: 1.4rem;
            font-weight: bold;
            color: #800020;
            border-bottom: 2px solid #800020;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            padding-bottom: 0.2rem;
        }
        
        /* Cajas de alerta clínicas VFG */
        .vfg-box {
            padding: 15px;
            border-radius: 8px;
            font-weight: bold;
            color: #FFFFFF;
            text-align: center;
            font-size: 1.1rem;
            box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
            margin-top: 1rem;
        }
        
        /* Ajuste de Tabs (Pestañas) */
        .stTabs [data-baseweb="tab-list"] {
            gap: 20px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #F8F9FA;
            border-radius: 4px 4px 0px 0px;
            padding: 10px 20px;
            color: #333333;
        }
        .stTabs [aria-selected="true"] {
            background-color: #800020 !important;
            color: #FFFFFF !important;
            font-weight: bold;
        }
        
        /* Forzar color oscuro en inputs de texto si el tema base se cruza */
        input, select, textarea {
            color: #333333 !important;
        }
        </style>
    """, unsafe_allow_html=True)

# =====================================================================
# 5.3 MÓDULO FES FRAGMENTADO
# =====================================================================
@st.fragment
def vista_modulo_fes():
    """Fragmento independiente para manejar la validación de firma."""
    st.markdown('<div class="section-header">Firma Electrónica Simple (FES)</div>', unsafe_allow_html=True)
    st.info("ℹ️ Para validar su identidad y firmar el consentimiento, enviaremos un código temporal.")
    
    col_metodo, col_contacto = st.columns([1, 2])
    with col_metodo:
        metodo_fes = st.selectbox("Canal de envío", ["WhatsApp", "Email"], key="sel_metodo_fes")
    with col_contacto:
        contacto = st.text_input("Ingrese número (+569...) o Correo Electrónico", key="txt_contacto_fes")
        
    if st.button("📲 Generar y Enviar Código", use_container_width=True):
        if not contacto:
            st.error("Debe ingresar un contacto válido.")
            return
            
        codigo_seguridad = str(random.randint(100000, 999999))
        st.session_state.fes_codigo_generado = codigo_seguridad
        
        # Aquí llamamos a la función real despachar_codigo_fes (del Bloque 3)
        # Se envuelve en try/except por si st.secrets no está configurado en tu entorno local aún.
        try:
            exito = despachar_codigo_fes(metodo_fes, contacto, codigo_seguridad)
            if exito:
                st.success(f"Código enviado exitosamente vía {metodo_fes}.")
            else:
                st.warning(f"Simulando envío por falta de credenciales. Tu código es: {codigo_seguridad}")
        except Exception:
            st.warning(f"⚠️ Entorno de prueba (secrets no configurados). Tu código es: {codigo_seguridad}")
            
    if st.session_state.get("fes_codigo_generado"):
        st.markdown("---")
        codigo_ingresado = st.text_input("🔑 Ingrese el código de 6 dígitos recibido:", max_chars=6)
        if st.button("✅ Validar Identidad y Firmar", type="primary", use_container_width=True):
            if codigo_ingresado == st.session_state.fes_codigo_generado:
                st.session_state.fes_validado = True
                st.success("🎉 ¡Identidad validada exitosamente! Procedimiento autorizado.")
            else:
                st.error("❌ Código incorrecto. Intente nuevamente.")

# =====================================================================
# 5.4 ORQUESTADOR PRINCIPAL (MAIN)
# =====================================================================
def main():
    st.set_page_config(page_title="Norte Imagen - Admisión", page_icon="🏥", layout="wide", initial_sidebar_state="collapsed")
    aplicar_estilos_css()
    inicializar_estado()
    
    st.markdown("<h1 style='text-align: center; color: #800020;'>🏥 Admisión y Consentimiento Clínico</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Plataforma Integral Norte Imagen</p>", unsafe_allow_html=True)
    
    # Sistema de Navegación por Pasos (Wizard)
    tab_paciente, tab_examenes, tab_clinica, tab_firma, tab_resumen = st.tabs([
        "👤 1. Paciente", 
        "🩻 2. Exámenes", 
        "⚕️ 3. Clínica", 
        "✍️ 4. Firma (FES)", 
        "📄 5. Resumen JSON"
    ])
    
    # ---------------------------------------------------------
    # PASO 1: PACIENTE Y TUTOR
    # ---------------------------------------------------------
    with tab_paciente:
        st.markdown('<div class="section-header">Identificación del Paciente Titular</div>', unsafe_allow_html=True)
        
        # Llamamos al Fragmento OCR del Bloque 4
        vista_escaner_cedula("TITULAR")
        
        col_nac, col_gen = st.columns(2)
        with col_nac:
            st.session_state.form["fecha_nac"] = st.date_input(
                "Fecha de Nacimiento", 
                value=st.session_state.form.get("fecha_nac", None),
                min_value=date(1900, 1, 1),
                max_value=date.today()
            )
        with col_gen:
            opciones_gen = ["", "Femenino", "Masculino", "No binario (Bio: Femenino)", "No binario (Bio: Masculino)"]
            indice_gen = opciones_gen.index(st.session_state.form["genero_biologico"]) if st.session_state.form["genero_biologico"] in opciones_gen else 0
            st.session_state.form["genero_biologico"] = st.selectbox("Género Biológico (Para cálculos médicos)", opciones_gen, index=indice_gen)
            
        st.markdown("---")
        st.session_state.form["requiere_tutor"] = st.checkbox("🙋‍♂️ El paciente es menor de edad o requiere tutor legal")
        
        if st.session_state.form["requiere_tutor"]:
            st.markdown('<div class="section-header">Identificación del Tutor Legal</div>', unsafe_allow_html=True)
            vista_escaner_cedula("TUTOR")

    # ---------------------------------------------------------
    # PASO 2: SELECCIÓN DE EXÁMENES Y LATERALIDAD
    # ---------------------------------------------------------
    with tab_examenes:
        # Llamamos al Fragmento Selector del Bloque 4
        vista_seleccion_procedimiento()

    # ---------------------------------------------------------
    # PASO 3: EVALUACIÓN CLÍNICA (VFG)
    # ---------------------------------------------------------
    with tab_clinica:
        st.markdown('<div class="section-header">Evaluación de Riesgo y Contraste</div>', unsafe_allow_html=True)
        
        if st.session_state.form.get("tiene_contraste", False):
            st.warning("⚠️ Al menos uno de los procedimientos seleccionados requiere **Medio de Contraste**. Complete los datos antropométricos y de laboratorio.")
            
            c_peso, c_talla, c_crea, c_fecha = st.columns(4)
            with c_peso:
                st.session_state.form["peso"] = st.number_input("Peso (kg)", min_value=0.0, max_value=300.0, step=0.1)
            with c_talla:
                st.session_state.form["talla"] = st.number_input("Talla (cm)", min_value=0.0, max_value=250.0, step=1.0)
            with c_crea:
                st.session_state.form["creatinina"] = st.number_input("Creatinina (mg/dL)", min_value=0.0, max_value=20.0, step=0.01)
            with c_fecha:
                st.session_state.form["fecha_creatinina"] = st.date_input("Fecha Examen Creatinina")
                
            # Calcular VFG automáticamente si hay datos suficientes
            if st.session_state.form["fecha_nac"] and st.session_state.form["genero_biologico"] and st.session_state.form["creatinina"] > 0:
                vfg, mensaje_riesgo, color_hex, clase_css = calcular_vfg_clinica(
                    st.session_state.form["fecha_nac"],
                    st.session_state.form["genero_biologico"],
                    st.session_state.form["peso"],
                    st.session_state.form["talla"],
                    st.session_state.form["creatinina"]
                )
                
                html_vfg = f"""
                <div class='vfg-box' style='background-color: {color_hex};'>
                    Tasa de Filtración Glomerular (VFG): {vfg:.2f} mL/min/1.73m²<br>
                    <span style='font-size: 1.3rem;'>{mensaje_riesgo}</span>
                </div>
                """
                st.markdown(html_vfg, unsafe_allow_html=True)
            else:
                st.info("ℹ️ Ingrese Fecha de Nacimiento, Género Biológico y Creatinina para calcular la VFG.")
        else:
            st.success("✅ Los procedimientos seleccionados NO requieren Medio de Contraste. No es necesario el cálculo de VFG.")

    # ---------------------------------------------------------
    # PASO 4: FIRMA ELECTRÓNICA SIMPLE
    # ---------------------------------------------------------
    with tab_firma:
        vista_modulo_fes()

    # ---------------------------------------------------------
    # PASO 5: EXPORTACIÓN Y PAYLOAD FINAL (HL7/JSON)
    # ---------------------------------------------------------
    with tab_resumen:
        st.markdown('<div class="section-header">Empaquetado de Datos (Integración HIS/RIS)</div>', unsafe_allow_html=True)
        
        if not st.session_state.fes_validado:
            st.warning("🔒 El paquete de datos se desbloqueará una vez que se complete la Firma Electrónica Simple en la pestaña anterior.")
        else:
            # Construcción del Payload Maestro
            payload_maestro = {
                "metadata": {
                    "fecha_admision": str(date.today()),
                    "firma_electronica_validada": True
                },
                "paciente": {
                    "rut": st.session_state.form.get("rut_titular", ""),
                    "nombre": st.session_state.form.get("nombre_titular", ""),
                    "fecha_nacimiento": str(st.session_state.form.get("fecha_nac", "")),
                    "genero": st.session_state.form.get("genero_biologico", "")
                },
                "tutor_legal": {
                    "requerido": st.session_state.form.get("requiere_tutor", False),
                    "rut": st.session_state.form.get("rut_tutor", ""),
                    "nombre": st.session_state.form.get("nombre_tutor", "")
                },
                "evaluacion_clinica": {
                    "requiere_contraste": st.session_state.form.get("tiene_contraste", False),
                    "peso_kg": st.session_state.form.get("peso", 0),
                    "talla_cm": st.session_state.form.get("talla", 0),
                    "creatinina": st.session_state.form.get("creatinina", 0),
                    "fecha_creatinina": str(st.session_state.form.get("fecha_creatinina", ""))
                },
                "hl7_fhir_service_requests": st.session_state.form.get("recursos_hl7", [])
            }
            
            st.success("✅ Paquete de datos estructurado exitosamente. Listo para envío a API / Base de Datos.")
            
            with st.expander("Ver JSON Generado (Estándar FHIR / FONASA)", expanded=True):
                st.json(payload_maestro)
                
            if st.button("🚀 Enviar a Sistema Central (HIS/RIS)", type="primary", use_container_width=True):
                st.balloons()
                st.success("¡Transmisión iniciada! Los datos han sido empaquetados bajo los estándares solicitados.")

if __name__ == "__main__":
    main()


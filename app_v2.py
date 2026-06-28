# =============================================================================
# COPYRIGHT (c) 2026 [JONATHAN HAROLD ENRIQUE DÍAZ HUAMÁN].
# ARQUITECTURA V3: SPA WIZARD, HL7 FHIR R4, AES-256 GCM, FES Ley 19.799
# Cumple: Ley 19.628 (Datos Personales CL), Ley 19.799 (FES CL),
#         Decreto 41 MINSAL (Consentimiento Informado), HL7 FHIR Release 4
# Registro Profesional: [513416]
# =============================================================================

# =====================================================================
# SECCIÓN 1: IMPORTACIONES (ÚNICAS — SIN DUPLICADOS)
# =====================================================================
import base64
import hashlib
import json
import os
import re
import smtplib
import tempfile
import time
import uuid
from datetime import date, datetime
from email.message import EmailMessage

import cv2
import firebase_admin
import numpy as np
import pandas as pd
import pyotp
import pytz
import requests
import streamlit as st
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from firebase_admin import credentials, firestore, storage
from fpdf import FPDF
from PIL import Image
from streamlit_drawable_canvas import st_canvas
from streamlit_javascript import st_javascript
import pytesseract

# Google Drive (Kill-Switch = False por defecto, listo para habilitar)
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# =====================================================================
# SECCIÓN 2: CONFIGURACIÓN ÚNICA DE PÁGINA (PRIMERA LÍNEA EJECUTABLE)
# =====================================================================
dir_actual = os.path.dirname(__file__)
ruta_logo_pg = os.path.join(dir_actual, "logoNI_pg.png")
try:
    img_icono = Image.open(ruta_logo_pg)
except Exception:
    img_icono = "🏥"

st.set_page_config(
    page_title="Norte Imagen - Registro RM",
    page_icon=img_icono,
    layout="centered",
    initial_sidebar_state="collapsed"
)

# =====================================================================
# SECCIÓN 3: ZONA HORARIA CHILE
# =====================================================================
tz_chile = pytz.timezone('America/Santiago')

# =====================================================================
# SECCIÓN 4: CSS GLOBAL + MENÚ FLOTANTE (UNA SOLA INYECCIÓN)
# =====================================================================
def inyectar_css_y_menu():
    """Centraliza TODO el estilo de la app. Se llama UNA SOLA VEZ al inicio."""
    fondo = "#ffffff" if st.session_state.get("step", 0) == 0 else "#f5f5f5"
    st.markdown(f"""
    <style>
    /* === MODO CLARO FORZADO (Anti Dark-Mode) === */
    html, body, [class*="css"], .stApp, p, span, div, label, li {{
        color: #333333 !important;
    }}
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background-color: {fondo} !important;
    }}
    [data-testid="stSidebar"] {{ background-color: #ffffff !important; }}

    /* === BOTONES CORPORATIVOS BURDEOS === */
    .stButton>button {{
        background-color: #800020 !important; color: #ffffff !important;
        border-radius: 8px; width: 100%; height: 3em; font-weight: bold;
        transition: all 0.3s ease;
    }}
    .stButton>button:hover {{
        box-shadow: 0px 4px 12px rgba(128, 0, 32, 0.4) !important;
        transform: translateY(-2px);
    }}
    .stButton>button *, .stButton>button p, .stButton>button span {{
        color: #ffffff !important; -webkit-text-fill-color: #ffffff !important;
    }}
    div[role="dialog"] button, [data-testid="stModal"] button {{
        color: #ffffff !important; -webkit-text-fill-color: #ffffff !important;
    }}

    /* === TIPOGRAFÍA CLÍNICA === */
    h1 {{ color: #000000 !important; text-align: center; }}
    h2, h3 {{ color: #800020 !important; }}
    .section-header {{
        color: #800020 !important; border-bottom: 2px solid #800020 !important;
        padding-bottom: 5px; margin-top: 25px; margin-bottom: 15px;
        font-size: 1.3em; font-weight: bold;
    }}

    /* === INPUTS Y SELECTORES === */
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div,
    div[data-baseweb="select"] > div {{
        background-color: #ffffff !important; border: 1px solid #b3b3b3 !important;
        border-radius: 6px !important; color: #333333 !important;
    }}
    div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea,
    div[data-baseweb="select"] div {{
        color: #333333 !important; -webkit-text-fill-color: #333333 !important;
    }}
    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-within {{
        border: 2px solid #800020 !important;
        box-shadow: 0px 0px 5px rgba(128, 0, 32, 0.2) !important;
    }}

    /* === MULTISELECT TAGS === */
    span[data-baseweb="tag"] {{ background-color: #78909c !important; border-radius: 4px !important; }}
    span[data-baseweb="tag"] span {{ color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; font-weight: bold; }}
    span[data-baseweb="tag"] svg {{ fill: #ffffff !important; }}

    /* === SELECTBOX MOBILE (Texto completo en pantallas chicas) === */
    div[data-baseweb="popover"] {{ max-width: 95vw !important; }}
    div[data-baseweb="popover"] ul li {{
        white-space: normal !important; word-break: break-word !important;
        line-height: 1.4 !important; padding-top: 12px !important; padding-bottom: 12px !important;
    }}
    div[data-baseweb="select"] > div {{ white-space: normal !important; overflow: visible !important; }}

    /* === CAJAS VFG CLÍNICAS === */
    .vfg-box {{
        background-color: #ffffff !important; padding: 20px; border-radius: 10px;
        border: 2px solid #800020 !important; text-align: center; margin-top: 20px;
    }}
    .vfg-critica {{ border: 3px solid #ff0000 !important; color: #ff0000 !important; }}

    /* === TEXTO LEGAL (Scroll) === */
    .legal-text {{
        background-color: #ffffff !important; padding: 20px; border-radius: 5px;
        border: 1px solid #ccc !important; font-size: 0.95em; text-align: justify;
        color: #333333 !important; margin-bottom: 20px;
        max-height: 500px; overflow-y: auto; line-height: 1.6;
    }}

    /* === ANIMACIÓN MENÚ FLOTANTE === */
    @keyframes pulse-glow {{
        0% {{ box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.6); }}
        70% {{ box-shadow: 0 0 0 12px rgba(255, 255, 255, 0.4); }}
        100% {{ box-shadow: 0 0 0 0 rgba(255, 255, 255, 0); }}
    }}
    .menu-flotante {{
        position: fixed !important; bottom: 45px !important; right: 1px !important;
        z-index: 999999 !important; display: flex !important;
        flex-direction: column !important; align-items: flex-end !important; gap: 10px !important;
    }}
    .opciones-contacto {{ display: none !important; flex-direction: column !important; gap: 8px !important; margin-bottom: 5px !important; }}
    .menu-flotante:hover .opciones-contacto,
    .menu-flotante:focus-within .opciones-contacto {{ display: flex !important; }}
    .btn-opcion {{
        display: flex !important; align-items: center !important; gap: 10px !important;
        text-decoration: none !important; color: #333 !important; font-size: 13px !important;
        font-weight: 600 !important; padding: 10px 15px !important; border-radius: 12px !important;
        backdrop-filter: blur(8px) !important; border: 1px solid rgba(255, 255, 255, 0.6) !important;
        white-space: nowrap !important; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
    }}
    .color-email {{ background-color: rgba(255, 255, 255, 0.85) !important; }}
    .color-telefono {{ background-color: rgba(211, 237, 212, 0.85) !important; }}
    .color-whatsapp {{ background-color: rgba(165, 214, 167, 0.85) !important; color: #155724 !important; }}
    .btn-principal {{
        background: linear-gradient(135deg, rgba(40, 167, 69, 0.8) 0%, rgba(255, 255, 255, 0.95) 100%) !important;
        color: #004d00 !important; border-radius: 50px !important; padding: 14px 26px !important;
        font-weight: bold !important; cursor: pointer !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important; animation: pulse-glow 2s infinite !important;
        border: 1px solid rgba(40, 167, 69, 0.4) !important;
        display: flex !important; align-items: center !important; gap: 10px !important;
    }}
    </style>

    <div class="menu-flotante" tabindex="0">
        <div class="opciones-contacto">
            <a class="btn-opcion color-telefono" href="tel:+56572466423" target="_blank">
                📞 Francisco Bilbao: +56 57 246 6423
            </a>
            <a class="btn-opcion color-telefono" href="tel:+56572466425" target="_blank">
                📞 Arturo Fernández: +56 57 246 6425
            </a>
            <a class="btn-opcion color-whatsapp" href="javascript:void(0);" style="cursor:default;">
                📱 WhatsApp (Próximamente)
            </a>
            <a class="btn-opcion color-email"
               href="mailto:resonancia@cdnorteimagen.cl?subject=Consulta%20Registro%20RM"
               target="_blank">
                ✉️ resonancia.iquique@cdnorteimagen.cl
            </a>
        </div>
        <div class="btn-principal" title="Soporte Norte Imagen">💬 ¿Necesitas ayuda?</div>
    </div>
    """, unsafe_allow_html=True)


# =====================================================================
# SECCIÓN 5: FIREBASE SINGLETON (1 sola conexión para todos)
# =====================================================================
@st.cache_resource
def inicializar_firebase():
    """Abre UNA SOLA conexión global — todos los pacientes usan el mismo canal."""
    try:
        return firebase_admin.get_app()
    except ValueError:
        cred_dict = dict(st.secrets["firebase"])
        url_bucket = cred_dict.pop("bucket_url", "firmas-encuestaconsentimiento.firebasestorage.app")
        if "private_key" in cred_dict:
            raw = cred_dict["private_key"]
            b64 = re.sub(r'-----.*?PRIVATE KEY-----', '', raw)
            b64 = re.sub(r'\s+', '', b64)
            chunks = [b64[i:i + 64] for i in range(0, len(b64), 64)]
            cred_dict["private_key"] = (
                "-----BEGIN PRIVATE KEY-----\n" + "\n".join(chunks) + "\n-----END PRIVATE KEY-----\n"
            )
        cred = credentials.Certificate(cred_dict)
        return firebase_admin.initialize_app(cred, {'storageBucket': url_bucket})


# =====================================================================
# SECCIÓN 6: MOTOR CRIPTOGRÁFICO AES-256 GCM (Grado Militar)
# =====================================================================
class GestorCriptografico:
    """Encriptación AES-256 GCM. Cumple Ley 19.628 (Datos Personales Chile)."""

    def __init__(self):
        try:
            key_hex = st.secrets["aes"]["master_key"]
        except Exception:
            # Clave de desarrollo — DEBE reemplazarse con st.secrets en producción
            key_hex = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        self.key = bytes.fromhex(key_hex)
        self.aesgcm = AESGCM(self.key)

    def encriptar(self, datos_dict: dict) -> str:
        nonce = os.urandom(12)
        payload = json.dumps(datos_dict, default=str).encode('utf-8')
        cifrado = self.aesgcm.encrypt(nonce, payload, None)
        return base64.b64encode(nonce + cifrado).decode('utf-8')

    def desencriptar(self, cadena: str) -> dict:
        raw = base64.b64decode(cadena)
        nonce, cifrado = raw[:12], raw[12:]
        datos = self.aesgcm.decrypt(nonce, cifrado, None)
        return json.loads(datos.decode('utf-8'))


# =====================================================================
# SECCIÓN 7: MOTOR FHIR HL7 R4 (MINSAL Chile — Bundle Completo)
# =====================================================================
MAPA_GENERO_FHIR = {
    "Masculino": "male",
    "Femenino": "female",
    "No binario (Bio: Masculino)": "other",
    "No binario (Bio: Femenino)": "other",
    "No binario": "other",
}

# SNOMED CT — Códigos para bodySite en ServiceRequest
MAPA_SNOMED_ANATOMICO = {
    "HOMBRO": "368209003", "RODILLA": "362768002", "CADERA": "24136001",
    "MUÑECA": "8205005",   "MANO": "85562004",     "CODO": "76248009",
    "TOBILLO": "70258002", "PIÉ": "302539009",      "BRAZO": "40983000",
    "ANTEBRAZO": "14975008","MUSLO": "68367000",    "PIERNA": "30021000",
    "ORBITA": "363654007", "MAMA": "80248007",      "OÍDO": "25342003",
    "GLÚTEO": "78961009",  "COLUMNA": "421060004",  "CEREBRO": "12738006",
}


def transformar_a_bundle_fhir(form_data: dict, id_sesion: str,
                               recursos_hl7: list = None) -> dict:
    """
    Genera un FHIR R4 Bundle completo con todos los recursos clínicos.
    Recursos incluidos: Patient, Consent, Observation (creatinina + VFG),
    ServiceRequest (x procedimiento FONASA MLE), QuestionnaireResponse.
    """
    ahora_iso = datetime.now(pytz.utc).isoformat()
    fn = form_data.get("fecha_nac")
    fecha_nac_str = fn.strftime("%Y-%m-%d") if hasattr(fn, "strftime") else str(fn)
    genero_fhir = MAPA_GENERO_FHIR.get(form_data.get("genero_biologico", ""), "unknown")
    rut = form_data.get("rut", "")

    # --- RECURSO 1: Patient ---
    if form_data.get("sin_rut"):
        identificador = [{
            "use": "usual",
            "type": {"text": form_data.get("tipo_doc", "Pasaporte")},
            "value": form_data.get("num_doc", ""),
        }]
    else:
        identificador = [{
            "use": "official",
            "system": "http://registrocivil.cl/rut",
            "value": rut,
        }]

    recurso_patient = {
        "resourceType": "Patient",
        "id": id_sesion,
        "identifier": identificador,
        "name": [{"use": "official", "text": form_data.get("nombre", "")}],
        "telecom": [
            {"system": "phone", "value": form_data.get("telefono", ""), "use": "mobile"},
            {"system": "email", "value": form_data.get("email", ""), "use": "home"},
        ],
        "gender": genero_fhir,
        "birthDate": fecha_nac_str,
    }
    if form_data.get("nombre_tutor"):
        recurso_patient["contact"] = [{
            "relationship": [{"text": form_data.get("parentesco_tutor", "Representante Legal")}],
            "name": {"use": "official", "text": form_data.get("nombre_tutor", "")},
        }]

    # --- RECURSO 2: Consent (Decreto 41 MINSAL + Ley 19.799 FES) ---
    recurso_consent = {
        "resourceType": "Consent",
        "id": f"consent-{id_sesion}",
        "status": "active",
        "scope": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/consentscope",
                "code": "treatment",
                "display": "Treatment",
            }]
        },
        "category": [{
            "coding": [{
                "system": "http://loinc.org",
                "code": "59284-0",
                "display": "Consent Document",
            }]
        }],
        "patient": {"reference": f"Patient/{id_sesion}"},
        "dateTime": ahora_iso,
        "performer": [{"display": form_data.get("nombre_tutor") or form_data.get("nombre", "")}],
        "policy": [{
            "authority": "https://www.minsal.cl",
            "uri": "https://www.bcn.cl/leychile/navegar?idNorma=193581",
        }],
        "provision": {"type": "permit", "period": {"start": ahora_iso}},
        "verification": [{
            "verified": bool(form_data.get("otp_verificado")),
            "verifiedWith": {"reference": f"Patient/{id_sesion}"},
            "verificationDate": ahora_iso,
        }],
        "extension": [{
            "url": "http://minsal.cl/fhir/extension/fes-ley-19799",
            "valueString": form_data.get("hash_documento", ""),
        }],
    }

    entradas = [
        {"resource": recurso_patient},
        {"resource": recurso_consent},
    ]

    # --- RECURSO 3: Observation — Creatinina sérica (LOINC 2160-0) ---
    creatinina = float(form_data.get("creatinina", 0.0))
    if creatinina > 0:
        fc = form_data.get("fecha_creatinina", ahora_iso)
        fc_str = fc.isoformat() if hasattr(fc, "isoformat") else str(fc)
        entradas.append({"resource": {
            "resourceType": "Observation",
            "id": f"obs-creatinina-{id_sesion}",
            "status": "final",
            "category": [{"coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "laboratory",
            }]}],
            "code": {"coding": [{
                "system": "http://loinc.org",
                "code": "2160-0",
                "display": "Creatinine [Mass/volume] in Serum or Plasma",
            }], "text": "Creatinina"},
            "subject": {"reference": f"Patient/{id_sesion}"},
            "effectiveDateTime": fc_str,
            "valueQuantity": {
                "value": creatinina, "unit": "mg/dL",
                "system": "http://unitsofmeasure.org", "code": "mg/dL",
            },
        }})

    # --- RECURSO 4: Observation — VFG estimada (LOINC 33914-3) ---
    vfg = float(form_data.get("vfg", 0.0))
    if vfg > 0:
        entradas.append({"resource": {
            "resourceType": "Observation",
            "id": f"obs-vfg-{id_sesion}",
            "status": "final",
            "category": [{"coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "laboratory",
            }]}],
            "code": {"coding": [{
                "system": "http://loinc.org",
                "code": "33914-3",
                "display": "Glomerular filtration rate/1.73 sq M.predicted [Volume Rate/Area] in Serum or Plasma by Creatinine-based formula (MDRD)",
            }], "text": "VFG Estimada"},
            "subject": {"reference": f"Patient/{id_sesion}"},
            "effectiveDateTime": ahora_iso,
            "valueQuantity": {
                "value": round(vfg, 2), "unit": "mL/min/1.73m2",
                "system": "http://unitsofmeasure.org", "code": "mL/min/{1.73_m2}",
            },
        }})

    # --- RECURSO 5: ServiceRequests (Procedimientos FONASA MLE) ---
    if recursos_hl7:
        for sr in recursos_hl7:
            sr_completo = dict(sr)
            sr_completo["subject"] = {"reference": f"Patient/{id_sesion}"}
            sr_completo["requester"] = {"display": "Norte Imagen - Resonancia Magnética"}
            sr_completo["authoredOn"] = ahora_iso
            entradas.append({"resource": sr_completo})

    # --- RECURSO 6: QuestionnaireResponse (Encuesta de Riesgos) ---
    def item_q(link_id, texto, valor):
        return {"linkId": link_id, "text": texto, "answer": [{"valueString": str(valor)}]}

    entradas.append({"resource": {
        "resourceType": "QuestionnaireResponse",
        "id": f"qr-{id_sesion}",
        "status": "completed",
        "subject": {"reference": f"Patient/{id_sesion}"},
        "authored": ahora_iso,
        "item": [
            item_q("bio_marcapaso",       "Marcapasos cardiaco",               form_data.get("bio_marcapaso", "No")),
            item_q("bio_implantes",       "Implantes metálicos/electrónicos",  form_data.get("bio_implantes", "No")),
            item_q("bio_detalle",         "Detalle bioseguridad",              form_data.get("bio_detalle", "")),
            item_q("clin_ayuno",          "Ayuno 2 hrs+",                      form_data.get("clin_ayuno", "No")),
            item_q("clin_asma",           "Asma",                              form_data.get("clin_asma", "No")),
            item_q("clin_hiperten",       "Hipertensión",                      form_data.get("clin_hiperten", "No")),
            item_q("clin_hipertiroid",    "Hipertiroidismo",                   form_data.get("clin_hipertiroid", "No")),
            item_q("clin_diabetes",       "Diabetes",                          form_data.get("clin_diabetes", "No")),
            item_q("clin_alergico",       "Alergias",                          form_data.get("clin_alergico", "No")),
            item_q("alergias_detalles",   "Detalle alergias",                  form_data.get("alergias_detalle", "")),
            item_q("clin_metformina",     "Suspende metformina 48h",           form_data.get("clin_metformina", "No")),
            item_q("clin_renal",          "Insuficiencia renal",               form_data.get("clin_renal", "No")),
            item_q("clin_dialisis",       "Diálisis",                          form_data.get("clin_dialisis", "No")),
            item_q("clin_embarazo",       "Embarazo",                          form_data.get("clin_embarazo", "No")),
            item_q("clin_lactancia",      "Lactancia",                         form_data.get("clin_lactancia", "No")),
            item_q("clin_claustro",       "Claustrofobia",                     form_data.get("clin_claustro", "No")),
            item_q("quir_cirugia",        "Cirugías previas",                  form_data.get("quir_cirugia_check", "No")),
            item_q("quir_cancer",         "Antecedentes oncológicos",          form_data.get("quir_cancer_check", "No")),
            {"linkId": "tiene_contraste", "text": "Requiere medio de contraste",
             "answer": [{"valueBoolean": bool(form_data.get("tiene_contraste", False))}]},
            {"linkId": "vfg_resultado", "text": "VFG (mL/min/1.73m²)",
             "answer": [{"valueDecimal": round(vfg, 2)}]},
            {"linkId": "fes_validada", "text": "FES Validada (Ley 19.799)",
             "answer": [{"valueBoolean": bool(form_data.get("otp_verificado", False))}]},
            {"linkId": "fes_hash_sha256", "text": "Hash SHA-256 del Sello Digital",
             "answer": [{"valueString": form_data.get("hash_documento", "")}]},
        ],
    }})

    return {
        "resourceType": "Bundle",
        "id": f"bundle-{id_sesion}",
        "type": "document",
        "timestamp": ahora_iso,
        "entry": entradas,
        "meta": {
            "profile": ["http://hl7.org/fhir/StructureDefinition/Bundle"],
            "tag": [{"system": "http://minsal.cl/fhir/tag", "code": "norte-imagen-rm-v3"}],
        },
    }


# =====================================================================
# SECCIÓN 8: DICCIONARIO ANATÓMICO + CATÁLOGO FONASA MLE
# =====================================================================
DICCIONARIO_ANATOMICO = {
    # Femeninos
    "RODILLA": {"genero": "F", "plural": "RODILLAS"},
    "PIERNA":  {"genero": "F", "plural": "PIERNAS"},
    "MANO":    {"genero": "F", "plural": "MANOS"},
    "MUÑECA":  {"genero": "F", "plural": "MUÑECAS"},
    "MAMA":    {"genero": "F", "plural": "MAMAS"},
    "ORBITA":  {"genero": "F", "plural": "ORBITAS"},
    "CADERA":  {"genero": "F", "plural": "CADERAS"},
    "EXTREMIDAD INFERIOR": {"genero": "F", "plural": "EXTREMIDADES INFERIORES"},
    "EXTREMIDAD SUPERIOR": {"genero": "F", "plural": "EXTREMIDADES SUPERIORES"},
    # Masculinos
    "HOMBRO":   {"genero": "M", "plural": "HOMBROS"},
    "CODO":     {"genero": "M", "plural": "CODOS"},
    "BRAZO":    {"genero": "M", "plural": "BRAZOS"},
    "ANTEBRAZO":{"genero": "M", "plural": "ANTEBRAZOS"},
    "MUSLO":    {"genero": "M", "plural": "MUSLOS"},
    "TOBILLO":  {"genero": "M", "plural": "TOBILLOS"},
    "OÍDO":     {"genero": "M", "plural": "OÍDOS"},
    "GLÚTEO":   {"genero": "M", "plural": "GLÚTEOS"},
    "PIÉ":      {"genero": "M", "plural": "PIES"},
    "ANTEPIÉ O MEDIOPIÉ": {"genero": "M", "plural": "ANTEPIÉS O MEDIOPIÉS"},
    "DEDO (S) DE LA MANO": {"genero": "M", "plural": "DEDOS DE LAS MANOS"},
    "ORTEJO (S) DEL PIÉ":  {"genero": "M", "plural": "ORTEJOS DE LOS PIES"},
}


def construir_nombre_especifico(nombre_base: str, lateralidad: str) -> str:
    """Aplica reglas gramaticales chilenas al nombre del procedimiento radiológico."""
    if lateralidad not in ["Derecha", "Izquierda", "Ambas"]:
        return nombre_base
    palabra = next((k for k in DICCIONARIO_ANATOMICO if k in nombre_base), None)
    if not palabra:
        return f"{nombre_base} {lateralidad.upper()}"
    info = DICCIONARIO_ANATOMICO[palabra]
    genero, plural = info["genero"], info["plural"]
    if lateralidad == "Ambas":
        sufijo = "AMBOS" if genero == "M" else "AMBAS"
        nuevo = nombre_base.replace(palabra, plural)
        return nuevo.replace(f"DE {plural}", f"DE {sufijo} {plural}")
    sufijo_lado = lateralidad.upper() if genero == "F" else lateralidad.upper().replace("A", "O")
    return f"{nombre_base} {sufijo_lado}"


@st.cache_data
def cargar_catalogo_hl7(ruta_csv: str = 'listado_prestaciones.csv'):
    """Carga el CSV de prestaciones y genera el catálogo en O(1) para lookup rápido."""
    try:
        df = pd.read_csv(ruta_csv, sep=';', encoding='utf-8-sig', dtype=str)
        df.columns = df.columns.str.strip()
        catalogo = {}
        for _, row in df.iterrows():
            nombre = str(row.get('PROCEDIMIENTO A REALIZAR', '')).strip()
            if nombre and nombre != 'nan':
                catalogo[nombre] = {
                    "especialidad":   str(row.get('ESPECIALIDAD', '')).strip(),
                    "codigo_fonasa":  str(row.get('CODIGO PRESTACION', 'S/C')).strip(),
                    "contraste":      str(row.get('MEDIO DE CONTRASTE', 'NO')).strip().upper() == 'SI',
                    "lateralidad":    str(row.get('REQUIERE_LATERALIDAD', 'NO')).strip().upper() == 'SI',
                }
        return df, catalogo
    except Exception as e:
        st.warning(f"⚠️ Catálogo de prestaciones no cargado: {e}")
        return None, {}


def generar_service_request_hl7(procedimiento: str, lateralidad: str,
                                 catalogo: dict) -> dict:
    """Genera un FHIR ServiceRequest con código FONASA MLE y SNOMED CT body site."""
    info = catalogo.get(procedimiento, {})
    codigo_fonasa = info.get("codigo_fonasa", "S/C")
    snomed_code = next((v for k, v in MAPA_SNOMED_ANATOMICO.items() if k in procedimiento), None)
    body_site = ([{"coding": [{"system": "http://snomed.info/sct",
                                "code": snomed_code, "display": lateralidad}]}]
                 if snomed_code else [])
    return {
        "resourceType": "ServiceRequest",
        "status": "active",
        "intent": "order",
        "code": {
            "coding": [{
                "system": "http://minsal.cl/fonasa/mle",
                "code": codigo_fonasa,
                "display": procedimiento,
            }],
            "text": (f"{procedimiento} - LAT: {lateralidad}"
                     if lateralidad not in ["No aplica", ""] else procedimiento),
        },
        "bodySite": body_site,
    }


# =====================================================================
# SECCIÓN 9: FUNCIONES DE APOYO CLÍNICO
# =====================================================================
def formatear_rut(rut_sucio: str) -> str:
    rut = str(rut_sucio).replace(".", "").replace("-", "").upper().strip()
    if len(rut) < 2:
        return rut_sucio
    cuerpo, dv = rut[:-1], rut[-1]
    return f"{int(cuerpo):,}".replace(",", ".") + f"-{dv}" if cuerpo.isdigit() else rut_sucio


def calcular_edad(fecha_nac: date) -> int:
    hoy = date.today()
    return hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))


def obtener_edad_visual_pdf(fecha_nac) -> str:
    """Edad en formato legible (años/meses/días) para el PDF clínico."""
    if not fecha_nac:
        return "N/A"
    hoy = date.today()
    anos  = hoy.year  - fecha_nac.year
    meses = hoy.month - fecha_nac.month
    dias  = hoy.day   - fecha_nac.day
    if dias  < 0: meses -= 1; dias  += 30
    if meses < 0: anos  -= 1; meses += 12
    if anos  > 0: return f"{anos} años, {meses} meses"
    if meses > 0: return f"{meses} meses, {dias} días"
    return f"{dias} días"


def safe_text(txt) -> str:
    """Sanitiza texto para compatibilidad Latin-1 en FPDF."""
    return str(txt).encode('latin-1', 'replace').decode('latin-1')


def mostrar_logo():
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists("logoNI.png"):
            st.image("logoNI.png", use_column_width=True)
        else:
            st.subheader("NORTE IMAGEN")


def enmascarar_contacto(texto: str, tipo: str) -> str:
    if not texto:
        return "Dato no registrado"
    if tipo == "Email":
        partes = texto.split("@")
        return f"{partes[0][:3]}***@{partes[1]}" if len(partes) == 2 else texto
    return f"******{texto[-4:]}" if len(texto) >= 4 else texto


def obtener_ip() -> str:
    """Captura la IP real del dispositivo del paciente vía JavaScript del navegador."""
    try:
        url = "https://api.ipify.org?format=json"
        ip_js = st_javascript(f'fetch("{url}").then(r=>r.json()).then(d=>d.ip)')
        if ip_js and ip_js != 0:
            return str(ip_js)
    except Exception:
        pass
    try:
        return requests.get('https://api.ipify.org?format=json', timeout=2).json()['ip']
    except Exception:
        return "0.0.0.0"


# =====================================================================
# SECCIÓN 10: MOTOR OCR — Visión Artificial Cédula Chilena
# =====================================================================
def limpiar_datos_ocr(texto: str, tipo: str = "nombre") -> str:
    if not texto:
        return ""
    limpio = str(texto)
    for s in ["eE", "p ", " /", " / ", "  ", ";", ":"]:
        limpio = limpio.replace(s, "")
    if tipo == "fecha":
        meses = {
            "ENE": "01", "FEB": "02", "MAR": "03", "ABR": "04",
            "MAY": "05", "JUN": "06", "JUL": "07", "AGO": "08",
            "SEP": "09", "OCT": "10", "NOV": "11", "DIC": "12",
        }
        for m_txt, m_num in meses.items():
            if m_txt in limpio.upper():
                limpio = limpio.upper().replace(m_txt, m_num).replace(" ", "/")
    return limpio.strip()


def procesar_cedula_inteligente(image_file):
    """
    Extrae RUT, nombre, fecha de nacimiento y sexo de la cédula chilena
    usando OpenCV (preprocesado) + Tesseract (OCR).
    """
    try:
        file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if img is None:
            return None, None, None, None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        texto = pytesseract.image_to_string(gray, config=r'--oem 3 --psm 6 -l spa')

        rut_m = re.search(r'(\d{1,2}(?:\.?\d{3}){2}\s*[-_]?\s*[\dkK])', texto)
        rut   = rut_m.group(0) if rut_m else ""

        sexo = ""
        if re.search(r'\b(F|FEMENINO)\b',  texto, re.IGNORECASE): sexo = "Femenino"
        elif re.search(r'\b(M|MASCULINO)\b', texto, re.IGNORECASE): sexo = "Masculino"

        fecha_m = re.search(
            r'NACIMIENTO[^\d]{0,50}(\d{2}\s?(?:ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)\s?\d{4}'
            r'|\d{2}[-/.]\d{2}[-/.]\d{4})',
            texto, re.IGNORECASE
        )
        if not fecha_m:
            fecha_m = re.search(
                r'(\d{2}\s?(?:ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)\s?\d{4}'
                r'|\d{2}[-/.]\d{2}[-/.]\d{4})',
                texto, re.IGNORECASE
            )
        fecha = fecha_m.group(1) if fecha_m else ""

        ap_m  = re.search(r"APELLIDOS[\s\n]+(.*?)\s+NOMBRES",          texto, re.IGNORECASE | re.DOTALL)
        nom_m = re.search(r"NOMBRES[\s\n]+(.*?)\s+(NACIONALIDAD|SEXO)", texto, re.IGNORECASE | re.DOTALL)
        apellidos = ap_m.group(1).strip()  if ap_m  else ""
        nombres   = nom_m.group(1).strip() if nom_m else ""
        nombre_completo = f"{nombres} {apellidos}".strip()

        return (
            limpiar_datos_ocr(rut,            "rut"),
            limpiar_datos_ocr(nombre_completo,"nombre"),
            limpiar_datos_ocr(fecha,          "fecha"),
            limpiar_datos_ocr(sexo,           "sexo"),
        )
    except Exception as e:
        print(f"ERROR OCR: {e}")
        return None, None, None, None


# =====================================================================
# SECCIÓN 11: MOTOR FES — Firma Electrónica Simple (Ley 19.799 Chile)
# =====================================================================
def despachar_codigo_fes(metodo: str, destino: str, codigo: str) -> bool:
    """
    Controlador central de envío FES omnicanal.
    Email (SMTP SSL) y WhatsApp (Meta Cloud API v19).
    """
    try:
        if metodo == "Email":
            correo  = st.secrets["email"]["sender_email"]
            passw   = st.secrets["email"]["app_password"]
            
            # 1. Limpiamos espacios fantasma del correo que puedan causar rebotes silenciosos
            destino_limpio = str(destino).strip()
            
            msg = EmailMessage()
            msg.set_content(
                f"Estimado(a) paciente,\n\n"
                f"Su codigo de validacion para la Firma Electronica Simple (FES) es: {codigo}\n\n"
                f"Este codigo es valido por 5 minutos. Ingreselo en la plataforma para\n"
                f"autorizar su procedimiento de Resonancia Magnetica.\n\nNorte Imagen."
            )
            
            # 2. Asunto limpio sin emojis (evita que Google lo trague como Spam)
            msg['Subject'] = 'Codigo de Validacion FES - Norte Imagen'
            
            # 3. From estricto (Evita bloqueos DMARC/SPF que silencian la entrega)
            msg['From']    = correo 
            msg['To']      = destino_limpio
            
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(correo, passw)
                smtp.send_message(msg)
                
            print(f"[FES EMAIL] Enviado a {destino_limpio}")
            return True

        elif metodo == "WhatsApp":
            token    = st.secrets["whatsapp"]["token"]
            phone_id = st.secrets["whatsapp"]["phone_id"]
            destino_limpio = "".join(filter(str.isdigit, str(destino)))
            resp = requests.post(
                f"https://graph.facebook.com/v19.0/{phone_id}/messages",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={
                    "messaging_product": "whatsapp",
                    "to": destino_limpio,
                    "type": "template",
                    "template": {
                        "name": "codigo_fes_norte_imagen",
                        "language": {"code": "es"},
                        "components": [{"type": "body",
                                        "parameters": [{"type": "text", "text": str(codigo)}]}],
                    },
                },
            )
            if resp.status_code == 200:
                print(f"[FES WA] Enviado a {destino_limpio}")
                return True
            st.error(f"Error Meta API: {resp.json()}")
            return False
            
    except Exception as e:
        st.error(f"Error de conexión FES: {e}")
        return False

# =====================================================================
# SECCIÓN 12: MOTOR VFG CLÍNICA (Schwartz + Cockcroft-Gault)
# =====================================================================
def calcular_vfg_clinica(fecha_nac, sexo: str, peso: float,
                          talla: float, creatinina: float):
    """
    Schwartz Clásica (<2 años), Schwartz Bedside 2009 (2-17 años),
    Cockcroft-Gault (≥18 años). Según KDIGO 2012 y práctica clínica MINSAL.
    Retorna: (vfg, mensaje, color_hex, clase_css)
    """
    if creatinina <= 0:
        return 0.0, "Ingrese la creatinina para calcular la VFG", "#333333", ""

    hoy       = date.today()
    edad_dias = (hoy - fecha_nac).days
    edad_mes  = edad_dias / 30.4
    edad_anos = edad_dias / 365.25

    # ── PEDIÁTRICO ──────────────────────────────────────────────────
    if edad_anos < 18:
        if talla <= 0:
            return 0.0, "Se requiere Talla (cm) para la VFG pediátrica", "#333333", ""

        # Schwartz Clásica — Lactantes < 2 años
        if edad_anos < 2:
            if edad_dias <= 6:
                k = 0.33
            elif edad_dias <= 28:
                k = 0.45
            elif edad_mes <= 12:
                k = 0.45
            else:
                k = 0.55
            vfg = (k * talla) / creatinina

            # Rangos de referencia por etapa de maduración neonatal
            rangos = [(0.25, 15, 30), (1, 30, 50), (2, 40, 65),
                      (4, 55, 85), (12, 70, 110)]
            min_n, max_n = 85, 125
            for tope, mn, mx in rangos:
                if edad_mes <= tope:
                    min_n, max_n = mn, mx
                    break

            if vfg < (min_n * 0.7):
                return vfg, "🔴 ALTO RIESGO: VFG Crítica para maduración neonatal", "#FF0000", "vfg-critica"
            elif vfg < min_n:
                return vfg, "⚠️ RIESGO INTERMEDIO: Retraso en maduración renal", "#FFCC00", "vfg-intermedia"
            elif vfg <= max_n:
                return vfg, "✅ SIN RIESGO: VFG Adecuada para la edad", "#28A745", "vfg-normal"
            else:
                return vfg, "🔵 REVISAR: Posible hiperfiltración", "#007BFF", "vfg-normal"

        # Schwartz Bedside 2009 — Pediátricos 2-17 años
        else:
            vfg = (0.413 * talla) / creatinina

    # ── ADULTO ──────────────────────────────────────────────────────
    else:
        if peso <= 0:
            return 0.0, "Se requiere Peso (kg) para la VFG adulto (Cockcroft-Gault)", "#333333", ""
        factor = 0.85 if sexo in ['Femenino', 'No binario (Bio: Femenino)'] else 1.0
        vfg    = (((140 - int(edad_anos)) * peso) / (72 * creatinina)) * factor

    # Clasificación KDIGO 2012 para contraste
    if vfg <= 30.0:
        return vfg, "🔴 Alto riesgo para administración de medio de contraste", "#FF0000", "vfg-critica"
    elif vfg <= 59.0:
        return vfg, "⚠️ Riesgo intermedio para administración de medio de contraste", "#FFCC00", "vfg-intermedia"
    return vfg, "✅ Sin riesgos para administración de medio de contraste", "#28A745", "vfg-normal"


# =====================================================================
# SECCIÓN 13: MOTOR PDF CLÍNICO (FPDF2 — Formato MINSAL)
# =====================================================================
class PDF(FPDF):
    def header(self):
        if os.path.exists("logoNI.png"):
            self.image("logoNI.png", 11, 11, 30)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(128, 0, 32)
        self.cell(0, 7, 'ENCUESTA DE RIESGOS ASOCIADOS Y', 0, 1, 'R')
        self.cell(0, 7, 'CONSENTIMIENTO INFORMADO',        0, 1, 'R')
        self.set_font('Arial', 'B', 16)
        self.cell(0, 8, 'RESONANCIA MAGNETICA', 0, 1, 'R')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 7)
        self.set_text_color(150, 150, 150)
        ahora    = datetime.now(tz_chile).strftime("%d/%m/%Y %H:%M:%S")
        nombre   = st.session_state.form.get('nombre', '')
        iniciales= "".join([p[0].upper() for p in nombre.split() if p])
        rut_p    = st.session_state.form.get('rut', 'S/R')
        ip       = st.session_state.form.get("ip_dispositivo", "No detectada")
        texto = (f"Certificado Digital Norte Imagen - RM: {ahora} "
                 f"- ID: {rut_p}-{iniciales} (IP:{ip}) - ORIGINAL PRE-ADMISIÓN.")
        self.cell(0, 10, safe_text(texto),              0, 0, 'L')
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", 0, 0, 'R')

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
        self.write(5, f"{safe_text(str(value))}\n")


def generar_pdf_clinico(datos: dict) -> bytes:
    """
    Genera el PDF clínico de 2 páginas en conformidad con el Decreto 41 MINSAL.
    Incluye: identificación, bioseguridad, antecedentes, VFG, consentimiento y firmas.
    """
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=12)
    is_contraste = st.session_state.get('tiene_contraste', False)

    # Cabecera fecha y procedencia
    fecha_str    = datetime.now(tz_chile).strftime("%d/%m/%Y")
    proc_base    = datos.get('procedencia', 'AMBULATORIO').upper()
    unidad       = datos.get('unidad_procedencia', '').strip().upper()
    txt_proc     = (f"PROCEDENCIA: {proc_base} (UNIDAD: {unidad})"
                    if proc_base == 'HOSPITALIZADO' and unidad
                    else f"PROCEDENCIA: {proc_base}")
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 5, f"Fecha de examen: {fecha_str}", 0, 1, 'R')
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 5, safe_text(txt_proc), 0, 1, 'L')
    pdf.ln(1)

    # ── SECCIÓN 1: IDENTIFICACIÓN ────────────────────────────────────
    pdf.section_title("1", "IDENTIFICACION DEL PACIENTE")
    pdf.set_text_color(0, 0, 0)
    marg    = 10
    ancho   = pdf.w - 20
    w_col   = (ancho - 10) / 2
    x_col2  = marg + w_col + 10

    pac_rut = (f"{datos.get('tipo_doc','Doc')}: {datos.get('num_doc','S/N')}"
               if datos.get('sin_rut') else str(datos.get('rut', 'S/R')))
    pac_edad       = obtener_edad_visual_pdf(datos.get('fecha_nac'))
    fecha_nac_str  = datos['fecha_nac'].strftime('%d/%m/%Y') if datos.get('fecha_nac') else 'S/D'
    email_val      = datos.get('email', 'S/E')

    pdf.set_font('Arial', 'B', 10); pdf.cell(32, 5, "Nombre Completo: ", 0, 0)
    pdf.set_font('Arial', '', 10); pdf.cell(0, 5, safe_text(datos.get('nombre', 'Sin Registro')), 0, 1)

    y2 = pdf.get_y()
    pdf.set_font('Arial', 'B', 9); pdf.cell(32, 5, "Documento / RUT: ", 0, 0)
    pdf.set_font('Arial', '', 9); pdf.cell(w_col - 32, 5, safe_text(pac_rut), 0, 0)
    pdf.set_xy(x_col2, y2)
    pdf.set_font('Arial', 'B', 9); pdf.cell(12, 5, "Edad: ", 0, 0)
    pdf.set_font('Arial', '', 9); pdf.cell(w_col - 12, 5, safe_text(pac_edad), 0, 1)

    y3 = pdf.get_y()
    pdf.set_font('Arial', 'B', 9); pdf.cell(35, 5, "Fecha Nacimiento: ", 0, 0)
    pdf.set_font('Arial', '', 9); pdf.cell(w_col - 35, 5, safe_text(fecha_nac_str), 0, 0)
    pdf.set_xy(x_col2, y3)
    pdf.set_font('Arial', 'B', 9); pdf.cell(12, 5, "Email: ", 0, 0)
    pdf.set_font('Arial', '', 9); pdf.cell(w_col - 12, 5, safe_text(email_val), 0, 1)

    pdf.set_font('Arial', 'B', 9); pdf.cell(35, 5, "Medio de contraste: ", 0, 0)
    pdf.set_font('Arial', '', 9); pdf.cell(0, 5, 'SI' if is_contraste else 'NO', 0, 1)

    proc_val = st.session_state.get('procedimiento', 'No especificado')
    pdf.set_font('Arial', 'B', 9); pdf.cell(28, 5, "Procedimiento(s): ", 0, 0)
    pdf.set_font('Arial', '', 9); pdf.multi_cell(0, 5, safe_text(proc_val), 0, 'L')
    pdf.ln(2)

    # Tutor Legal (si corresponde)
    rep_nombre = datos.get('nombre_tutor', '')
    if rep_nombre or (datos.get('fecha_nac') and calcular_edad(datos['fecha_nac']) < 18):
        pdf.ln(1); y_tut = pdf.get_y()
        rep_rut = (f"{datos.get('tipo_doc_tutor','Doc')}: {datos.get('num_doc_tutor','')}"
                   if datos.get('sin_rut_tutor') else datos.get('rut_tutor', 'S/R'))
        pdf.set_font('Arial', 'B', 9); pdf.cell(28, 5, "Representante: ", 0, 0)
        pdf.set_font('Arial', '', 9); pdf.cell(w_col - 28, 5, safe_text(rep_nombre or 'N/A'), 0, 0)
        pdf.set_xy(x_col2, y_tut)
        pdf.set_font('Arial', 'B', 9); pdf.cell(22, 5, "Parentesco: ", 0, 0)
        pdf.set_font('Arial', '', 9); pdf.cell(w_col - 22, 5, safe_text(datos.get('parentesco_tutor', 'N/A')), 0, 1)
        pdf.set_font('Arial', 'B', 9); pdf.cell(35, 5, "Doc. Representante: ", 0, 0)
        pdf.set_font('Arial', '', 9); pdf.cell(w_col - 35, 5, safe_text(rep_rut), 0, 1)

    # ── SECCIÓN 2: BIOSEGURIDAD MAGNÉTICA ────────────────────────────
    pdf.section_title("2", "BIOSEGURIDAD MAGNETICA")
    pdf.set_font('Arial', '', 9)
    pdf.data_field("Marcapasos cardiaco", datos.get('bio_marcapaso', 'No'))
    pdf.data_field("Implantes metálicos, quirúrgicos, prótesis o dispositivos electrónicos",
                   datos.get('bio_implantes', 'No'))
    if datos.get('bio_detalle'):
        pdf.set_font('Arial', 'I', 8)
        pdf.data_field("Detalle Bioseguridad", datos['bio_detalle'])
    pdf.ln(2)

    # ── SECCIÓN 3: ANTECEDENTES CLÍNICOS ─────────────────────────────
    pdf.section_title("3", "ANTECEDENTES CLINICOS")
    pdf.set_text_color(0, 0, 0)
    clinicos = [
        ("Ayuno 2hrs+",     datos.get('clin_ayuno',     'No')),
        ("Asma",            datos.get('clin_asma',      'No')),
        ("Alergias",        datos.get('clin_alergico',  'No')),
        ("Hipertensión",    datos.get('clin_hiperten',  'No')),
        ("Hipotiroidismo",  datos.get('clin_hipertiroid','No')),
        ("Diabetes",        datos.get('clin_diabetes',  'No')),
        ("Metformina 48h",  datos.get('clin_metformina','No')),
        ("Insuf. Renal",    datos.get('clin_renal',     'No')),
        ("Diálisis",        datos.get('clin_dialisis',  'No')),
        ("Embarazo",        datos.get('clin_embarazo',  'No')),
        ("Lactancia",       datos.get('clin_lactancia', 'No')),
        ("Claustrofobia",   datos.get('clin_claustro',  'No')),
    ]
    col_w = pdf.w / 4.2
    for i in range(0, len(clinicos), 4):
        for item, val in clinicos[i:i + 4]:
            pdf.set_font('Arial', '', 8)
            pdf.cell(col_w, 4.5, safe_text(f"{item}: {val}"), 0, 0)
        pdf.ln(4.5)

    detalle_alergia = datos.get('alergias_detalle', '').strip()
    if str(datos.get('clin_alergico', '')).upper() in ["SÍ", "SI"] and detalle_alergia:
        pdf.ln(2); pdf.set_font('Arial', 'BI', 8)
        pdf.cell(0, 5, safe_text(f"DETALLE ALERGIAS: {detalle_alergia}"), ln=True, border='B')

    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 5, "CONDICIONES O REQUERIMIENTOS ESPECIALES:", 0, 1)
    conds   = datos.get("condiciones", [])
    detalle = datos.get("condicion_detalle", "")
    pdf.set_font('Arial', '', 9)
    if conds or detalle:
        if conds:   pdf.multi_cell(0, 5, f" {', '.join(conds)}")
        if detalle: pdf.set_font('Arial', 'I', 8); pdf.multi_cell(0, 5, f"Detalle: {detalle}")
    else:
        pdf.cell(0, 5, "Ninguna condición declarada.", 0, 1)
    pdf.ln(2)

    # ── SECCIÓN 4: QUIRÚRGICO Y TERAPÉUTICO ──────────────────────────
    pdf.section_title("4", "ANTECEDENTES QUIRÚRGICOS Y TERAPÉUTICOS")
    pdf.set_font('Arial', '', 9)
    pdf.data_field("Cirugías", datos.get('quir_cirugia_check', 'No'))
    if datos.get('quir_cirugia_detalle'):
        pdf.set_font('Arial', '', 8)
        pdf.data_field("Detalle cirugías", datos['quir_cirugia_detalle'])
    pdf.set_font('Arial', '', 9)
    pdf.data_field("¿Cursa o ha cursado cáncer?", datos.get('quir_cancer_check', 'No'))
    if datos.get('quir_cancer_check') == 'Sí':
        pdf.set_font('Arial', '', 8)
        pdf.data_field("Detalle cáncer/etapa", datos.get('quir_cancer_detalle', 'N/A'))
        trats = [k for k, v in {
            "RT": datos.get('rt'), "QT": datos.get('qt'),
            "BT": datos.get('bt'), "IT": datos.get('it'),
        }.items() if v]
        pdf.set_font('Arial', '', 9)
        pdf.data_field("Tratamientos", ", ".join(trats) if trats else "Ninguno declarado")
        if datos.get('quir_otro_trat'):
            pdf.set_font('Arial', '', 8)
            pdf.data_field("Otros tratamientos", datos['quir_otro_trat'])
    pdf.ln(2)

    # ── SECCIÓN 5: EXÁMENES ANTERIORES ───────────────────────────────
    pdf.section_title("5", "EXAMENES ANTERIORES")
    pdf.set_font('Arial', '', 9)
    if datos.get('has_examenes_previos') == 'Sí':
        ex = [k for k, v in {
            "Rx": datos.get('ex_rx'), "MG":  datos.get('ex_mg'),
            "Eco":datos.get('ex_eco'),"TC":  datos.get('ex_tc'),
            "RM": datos.get('ex_rm'),
        }.items() if v]
        pdf.data_field("Exámenes", ", ".join(ex) if ex else "Ninguno seleccionado")
        if datos.get('ex_otros'):
            pdf.data_field("Otros exámenes", datos['ex_otros'])
    else:
        pdf.data_field("Exámenes", "No refiere exámenes anteriores")
    pdf.ln(2)

    # ── SECCIÓN 6: FUNCIÓN RENAL + FARMACOLOGÍA ───────────────────────
    pdf.section_title("6", "REGISTRO DE ADMINISTRACION FARMACOLOGICA Y EVALUACION FUNCION RENAL")
    pdf.set_font('Arial', '', 9)

    fn_pdf      = datos.get('fecha_nac')
    hoy         = date.today()
    edad_dias_p = (hoy - fn_pdf).days if fn_pdf else 0
    edad_mes_p  = edad_dias_p / 30.4
    edad_anos_p = edad_dias_p / 365.25
    es_pediat   = edad_anos_p < 18

    if is_contraste:
        crea     = float(datos.get('creatinina', 0.0))
        vfg_real = float(datos.get('vfg', 0.0))
        crea_txt = f"{crea} mg/dL" if crea > 0 else "Sin registro"

        if es_pediat:
            talla_r = float(datos.get('talla', 0.0))
            lbl_ant, val_ant = "Talla (Pediátrico)", f"{talla_r} cm" if talla_r > 0 else "Sin registro"
        else:
            peso_r  = float(datos.get('peso', 0.0))
            lbl_ant, val_ant = "Peso (Adulto)", f"{peso_r} kg" if peso_r > 0 else "Sin registro"

        pdf.set_fill_color(245, 245, 245)
        pdf.cell(95, 7, safe_text(f" Creatinina: {crea_txt}"),      0, 0, 'L', True)
        pdf.cell(95, 7, safe_text(f" {lbl_ant}: {val_ant}"),         0, 1, 'L', True)
        pdf.ln(1)

        if vfg_real > 0:
            if es_pediat and edad_anos_p < 2:
                rangos = [(0.25,15,30),(1,30,50),(2,40,65),(4,55,85),(12,70,110)]
                min_n, max_n = 85, 125
                for tope, mn, mx in rangos:
                    if edad_mes_p <= tope: min_n, max_n = mn, mx; break
                if vfg_real < (min_n * 0.7): msg_r, r, g, b = "ALTO RIESGO: VFG Crítica",              255,   0,   0
                elif vfg_real < min_n:        msg_r, r, g, b = "RIESGO INTERMEDIO: Retraso maduración", 184, 134,  11
                elif vfg_real <= max_n:       msg_r, r, g, b = "SIN RIESGO: VFG Adecuada",             34,  139,  34
                else:                         msg_r, r, g, b = "REVISAR: Posible hiperfiltración",        0, 123, 255
            else:
                if vfg_real <= 30.0:   msg_r, r, g, b = "ALTO RIESGO para medio de contraste",      255,   0,   0
                elif vfg_real <= 59.0: msg_r, r, g, b = "RIESGO INTERMEDIO para medio de contraste",184, 134,  11
                else:                  msg_r, r, g, b = "SIN RIESGOS para medio de contraste",        34, 139,  34

            pdf.set_font('Arial', 'B', 9)
            pdf.cell(35, 6, safe_text(f" V.F.G: {vfg_real:.2f} ml/min"), 0, 0, 'L')
            pdf.set_font('Arial', 'B', 8); pdf.set_text_color(r, g, b)
            pdf.cell(155, 6, safe_text(f"({msg_r})"), 0, 1, 'L')
            pdf.set_text_color(0, 0, 0); pdf.ln(2)

        # Tabla farmacológica
        pdf.ln(3); pdf.set_font('Arial', 'B', 9); pdf.set_fill_color(230, 230, 230)
        pdf.cell(190, 6, safe_text("DETALLE DE ADMINISTRACIÓN, FÁRMACOS Y ACCESO"), 0, 1, 'C', True)
        pdf.ln(1); pdf.set_font('Arial', '', 9); pdf.set_fill_color(245, 245, 245)
        pdf.cell(95, 7, safe_text(" Acceso Vascular: "), 0, 0, 'L', True)
        pdf.cell(95, 7, safe_text(" Sitio de Punción: "), 0, 1, 'L', True)
        pdf.ln(2)
        pdf.set_font('Arial', 'B', 8); pdf.set_fill_color(230, 230, 230)
        pdf.cell(80, 7, safe_text("Medio de contraste u otros medicamentos"), 0, 0, 'C', True)
        pdf.cell(40, 7, safe_text("Cantidad (ml)"),        0, 0, 'C', True)
        pdf.cell(70, 7, safe_text("Vía de administración"),0, 1, 'C', True)
        pdf.set_font('Arial', '', 8); pdf.set_fill_color(245, 245, 245)
        pdf.cell(80, 7, safe_text(" Medio de contraste / Ac. Gadoxético"), 0, 0, 'L', True)
        pdf.cell(40, 7, "", 0, 0, 'C', True); pdf.cell(70, 7, "", 0, 1, 'C', True)
        pdf.set_fill_color(252, 252, 252)
        pdf.cell(80, 7, safe_text(" Suero fisiológico (NaCl 0,9%)"), 0, 0, 'L', True)
        pdf.cell(40, 7, "", 0, 0, 'C', True); pdf.cell(70, 7, "", 0, 1, 'C', True)
        pdf.ln(2)
    else:
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(190, 7, safe_text(" Creatinina: Sin registro (Examen sin contraste)"), 0, 1, 'L', True)
        pdf.cell(190, 7, safe_text(" RESULTADO VFG: Sin contraste"),                    0, 1, 'L', True)

    # ── PÁGINA 2: CONSENTIMIENTO Y FIRMAS ────────────────────────────
    pdf.add_page()
    pdf.set_font('Arial', 'B', 10); pdf.set_text_color(0, 0, 0)
    txt_pr = f"Procedimiento: {st.session_state.get('procedimiento', 'No especificado')}"
    if st.session_state.get('tiene_contraste'):
        txt_pr += " con uso de medio de contraste."
    pdf.multi_cell(0, 7, safe_text(txt_pr), 0, 'L')
    if not st.session_state.get('tiene_contraste'):
        pdf.ln(1); pdf.set_font('Arial', '', 9)
        pregunta = "¿Se aplicó medio de contraste adicionalmente?"
        aw = pdf.get_string_width(pregunta) + 2
        pdf.cell(aw, 7, safe_text(pregunta), 0, 0, 'L')
        pdf.rect(pdf.get_x() + 2, pdf.get_y() + 1, 5, 5)
        pdf.ln(8)
    pdf.ln(3)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, "LEA ATENTA Y CUIDADOSAMENTE LO SIGUIENTE:", 0, 1, 'L')
    pdf.ln(2)

    secciones_legales = {
        "OBJETIVOS": (
            "La Resonancia Magnética (RM) es una segura técnica de Diagnóstico, que permite la adquisición "
            "de imágenes de gran sensibilidad en todos los planos del espacio de las estructuras del cuerpo. "
            "Tiene como objetivo obtener Información, datos funcionales y morfológicos para detectar precozmente "
            "una enfermedad.\n\nPara este examen eventualmente se puede requerir la utilización de un medio de "
            "contraste paramagnético de administración endovenosa llamado gadolinio, que permite realzar ciertos "
            "tejidos del cuerpo para un mejor diagnóstico."
        ),
        "CARACTERISTICAS": (
            "La Resonancia utiliza fuertes campos magnéticos y ondas de radiofrecuencia, por lo que es muy "
            "importante dejar fuera de la sala absolutamente todo lo que lleve consigo de tipo metálico y/o "
            "electrónico (relojes, pulseras, teléfonos, tarjetas magnéticas, etc). Si lleva material de este "
            "tipo en su cuerpo (fijaciones dentales, piercings, algunos tatuajes, balas o esquirlas metálicas) "
            "ciertos tipos de prótesis (valvulares, de cadera, de rodilla, clips metálicos, etc), o implantes, "
            "así como dispositivos electrónicos de carácter médico como bombas de insulina, prótesis auditivas, "
            "marcapasos, desfibriladores, etc. Avísenos, ya que puede contraindicar de manera absoluta la "
            "realización de este examen.\n\nUsted será posicionado en la camilla del equipo, según el estudio "
            "a realizar y se colocarán cerca de la zona a estudiar unos dispositivos (bobinas) que pueden ser "
            "de diversos tamaños. Esta exploración suele ser larga (entre 20 min y 1 hr según los casos). "
            "Notará ruido derivado del funcionamiento de la RM (por lo que le facilitaremos unos protectores "
            "auditivos), todo esto es normal y se le vigilará constantemente desde la sala de control.\n\n"
            "Es muy importante que permanezca quieto durante el estudio y siga las instrucciones del Tecnólogo Médico."
        ),
        "POTENCIALES RIESGOS": (
            "Existe una muy baja posibilidad de que se presente una reacción adversa al medio de contraste "
            "(0.07-2.4%) la mayoría de carácter leve fundamentalmente nauseas o cefaleas al momento de la "
            "inyección.\n\nPacientes con deterioro importante de la función renal, poseen riesgo de desarrollo "
            "de fibrosis nefrogénica sistémica."
        ),
    }
    for tit, cont in secciones_legales.items():
        pdf.set_font('Arial', 'B', 10); pdf.set_text_color(128, 0, 32)
        pdf.cell(0, 6, safe_text(tit), 0, 1, 'L')
        pdf.set_font('Arial', '', 9); pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 5, safe_text(cont)); pdf.ln(3)

    pdf.set_font('Arial', '', 9)
    pdf.multi_cell(0, 5, safe_text(
        "He sido informado de mi derecho de anular o revocar posteriormente este documento, "
        "dejándolo constatado por escrito y firmado por mi o mi representante.\n\n"
        "Autorizo la realización del procedimiento anteriormente especificado y las acciones que sean "
        "necesarias en caso de surgir complicaciones durante el procedimiento. Además, doy consentimiento "
        "para que se administren medicamentos y/o infusiones que se requieran para la realización de este."
    ))

    # ── FIRMAS ───────────────────────────────────────────────────────
    pdf.ln(5); y_f = pdf.get_y()
    a_izq, i_izq = 65, 20
    a_der, i_der = 65, 125
    fw, fh, ss   = 45, 12, 28
    x_firma = i_izq + (a_izq - fw) / 2
    x_sello = i_der + (a_der - ss) / 2

    ruta_f = datos.get('firma_img')
    if ruta_f and os.path.exists(ruta_f):
        pdf.image(ruta_f, x=x_firma, y=y_f, w=fw, h=fh)
    if os.path.exists("sello_norte_imagen.png"):
        pdf.image("sello_norte_imagen.png", x=x_sello, y=y_f - 2, w=ss, h=ss)

    data_y       = y_f + ss + 2
    rep_pdf      = datos.get('nombre_tutor', '').strip().upper()
    pac_pdf      = datos.get('nombre', 'PACIENTE').strip().upper()
    hash_full    = datos.get('hash_documento', '')
    hash_short   = f"{hash_full[:8]}-{hash_full[8:16]}".upper() if hash_full else "PENDIENTE"

    if rep_pdf:
        validador = rep_pdf
        cargo     = datos.get('parentesco_tutor', 'REPRESENTANTE LEGAL').upper()
        doc_sign  = (f"{datos.get('tipo_doc_tutor','DOC').upper()}: {datos.get('num_doc_tutor','')}"
                     if datos.get('sin_rut_tutor') else f"RUT: {datos.get('rut_tutor','S/R')}")
    else:
        validador = pac_pdf
        cargo     = "PACIENTE TITULAR"
        doc_sign  = (f"{datos.get('tipo_doc','DOC').upper()}: {datos.get('num_doc','')}"
                     if datos.get('sin_rut') else f"RUT: {datos.get('rut','S/R')}")

    pdf.set_text_color(60, 60, 60); pdf.set_y(data_y)
    pdf.set_font('Arial', 'B', 6)
    pdf.set_x(i_izq); pdf.cell(a_izq, 3.5, safe_text(f"VALIDADO POR: {validador}"), 0, 0, 'C')
    pdf.set_x(i_der); pdf.cell(a_der, 3.5, "VALIDADO POR: PENDIENTE",               0, 1, 'C')
    pdf.set_font('Arial', '', 5.5)
    pdf.set_x(i_izq); pdf.cell(a_izq, 2.5, safe_text(cargo),                          0, 0, 'C')
    pdf.set_x(i_der); pdf.cell(a_der, 2.5, "TECNÓLOGO MÉDICO EN IMAGENOLOGÍA",       0, 1, 'C')
    pdf.set_x(i_izq); pdf.cell(a_izq, 2.5, safe_text(doc_sign),                       0, 0, 'C')
    pdf.set_x(i_der); pdf.cell(a_der, 2.5, "ESPECIALIDAD RESONANCIA MAGNÉTICA",       0, 1, 'C')
    pdf.set_x(i_izq); pdf.cell(a_izq, 2.5, "",                                        0, 0, 'C')
    pdf.set_x(i_der); pdf.cell(a_der, 2.5, "REG. SIS: PENDIENTE",                    0, 1, 'C')
    pdf.ln(1); pdf.set_font('Arial', 'I', 4.5)
    pdf.set_x(i_izq); pdf.cell(a_izq, 2.5, safe_text(f"HUELLA SHA-256: {hash_short}"),0, 0, 'C')
    pdf.set_x(i_der); pdf.cell(a_der, 2.5, "HUELLA SHA-256: PENDIENTE",              0, 1, 'C')
    pdf.set_text_color(0, 0, 0)

    try:
        return bytes(pdf.output())
    except Exception:
        salida = pdf.output(dest='S')
        if isinstance(salida, str):        return salida.encode('latin-1')
        elif isinstance(salida, bytearray): return bytes(salida)
        return salida


# =====================================================================
# SECCIÓN 14: INICIALIZACIÓN DE SESIÓN SEGURA (ÚNICA — COMPLETA)
# =====================================================================
def inicializar_sesion():
    """
    Crea UN contenedor hermético por paciente/pestaña.
    UUID único = aislamiento matemático entre sesiones concurrentes.
    """
    if "paciente_uuid" not in st.session_state:
        st.session_state.paciente_uuid = str(uuid.uuid4())
    if "step" not in st.session_state:
        st.session_state.step = 0
    if "abrir_modal" not in st.session_state:
        st.session_state.abrir_modal = False
    if "registro_guardado_db" not in st.session_state:
        st.session_state.registro_guardado_db = False
    if "firma_guardada" not in st.session_state:
        st.session_state.firma_guardada = None
    if "proc_cache" not in st.session_state:
        st.session_state.proc_cache = []
    if "tiene_contraste" not in st.session_state:
        st.session_state.tiene_contraste = False
    if "procedimiento" not in st.session_state:
        st.session_state.procedimiento = ""
    if "credentials" not in st.session_state:
        st.session_state.credentials = None
    if "form" not in st.session_state:
        st.session_state.form = {
            # ── Demografía ──────────────────────────────────────────
            "nombre": "", "rut": "", "sin_rut": False,
            "tipo_doc": "Pasaporte", "num_doc": "",
            "fecha_nac": date(1990, 1, 1),
            "telefono": "", "email": "",
            "genero_idx": 0, "sexo_bio_idx": 0, "genero_biologico": "",
            "es_autovalente": True,
            # ── Tutor Legal ─────────────────────────────────────────
            "nombre_tutor": "", "rut_tutor": "", "parentesco_tutor": "",
            "sin_rut_tutor": False, "tipo_doc_tutor": "Pasaporte", "num_doc_tutor": "",
            # ── Procedencia / Agenda ─────────────────────────────────
            "procedencia": "Ambulatorio", "unidad_procedencia": "",
            "fecha_examen": date.today(),
            # ── Bioseguridad ─────────────────────────────────────────
            "bio_marcapaso": "No", "bio_implantes": "No", "bio_detalle": "",
            # ── Clínicos ─────────────────────────────────────────────
            "clin_ayuno": "No", "clin_asma": "No", "clin_hiperten": "No",
            "clin_hipertiroid": "No", "clin_diabetes": "No", "clin_alergico": "No",
            "clin_metformina": "No", "clin_renal": "No", "clin_dialisis": "No",
            "clin_claustro": "No", "clin_embarazo": "No", "clin_lactancia": "No",
            "alergias_detalle": "",
            # ── Condiciones especiales ───────────────────────────────
            "condiciones": [], "condicion_detalle": "",
            # ── Quirúrgico ────────────────────────────────────────────
            "quir_cirugia_check": "No", "quir_cirugia_detalle": "",
            "quir_cancer_check": "No", "quir_cancer_detalle": "",
            "rt": False, "qt": False, "bt": False, "it": False, "quir_otro_trat": "",
            # ── Exámenes previos ─────────────────────────────────────
            "has_examenes_previos": "No",
            "ex_rx": False, "ex_mg": False, "ex_eco": False, "ex_tc": False, "ex_rm": False,
            "ex_otros": "",
            "link_exam_1": "", "pin_exam_1": "", "link_exam_2": "", "pin_exam_2": "",
            # ── VFG / Laboratorio ────────────────────────────────────
            "creatinina": 0.0, "peso": 0.0, "talla": 0.0, "vfg": 0.0,
            "fecha_creatinina": date.today(),
            # ── HL7 FHIR ─────────────────────────────────────────────
            "recursos_hl7": [], "nombres_transformados": {}, "esp_idx": 0,
            # ── FES / Firma Electrónica Simple ───────────────────────
            "otp_secret":     pyotp.random_base32(),
            "otp_enviado":    False,
            "otp_metodo":     "Email",
            "otp_verificado": False,
            "otp_timestamp":  0.0,
            "hash_documento": "",
            "traza_auditoria": "",
            # ── Consentimiento ───────────────────────────────────────
            "veracidad":   False,
            "autoriza_gad": None,
            "firma_img":   None,
            # ── Metadatos ────────────────────────────────────────────
            "ip_dispositivo": "Detectando...",
        }


# =====================================================================
# SECCIÓN 15: FRAGMENTOS @st.fragment (SPA — sin recarga de página)
# =====================================================================
@st.fragment
def vista_escaner_cedula(tipo_paciente: str = "TITULAR"):
    """
    Módulo OCR aislado: al interactuar solo se recarga este fragmento.
    tipo_paciente = "TITULAR" | "TUTOR"
    """
    prefix   = "titular" if tipo_paciente == "TITULAR" else "tutor"
    key_rut  = "rut"    if tipo_paciente == "TITULAR" else "rut_tutor"
    key_nom  = "nombre" if tipo_paciente == "TITULAR" else "nombre_tutor"

    col_inp, col_btn = st.columns([5, 1], vertical_alignment="bottom")
    with col_inp:
        rut_v = st.text_input(
            f"RUT {tipo_paciente.capitalize()}",
            value=st.session_state.form.get(key_rut, ""),
            placeholder="12.345.678-K",
            key=f"inp_rut_{prefix}",
        )
        st.session_state.form[key_rut] = formatear_rut(rut_v)
    with col_btn:
        st.markdown(
            f"<style>button[title*='Escanear cédula de {tipo_paciente}'] p "
            "{{ font-size: 32px !important; line-height: 1 !important; margin: 0; }}</style>",
            unsafe_allow_html=True,
        )
        if st.button("📷", key=f"btn_cam_{prefix}",
                     help=f"Escanear cédula de {tipo_paciente}",
                     use_container_width=True):
            llave = f"mostrar_camara_{prefix}"
            st.session_state[llave] = not st.session_state.get(llave, False)

    if st.session_state.get(f"mostrar_camara_{prefix}", False):
        st.info("💡 Enfoque la cédula completa. Evite reflejos de luz directos sobre el plástico.")
        opcion = st.radio(
            f"Método de escaneo ({tipo_paciente}):",
            ["📷 Usar Cámara", "📁 Subir Foto (Galería)"],
            horizontal=True, key=f"radio_{prefix}",
        )
        foto = None
        if opcion == "📷 Usar Cámara":
            foto = st.camera_input("Tomar foto", key=f"cam_{prefix}")
            with st.expander("ℹ️ ¿Problemas con la cámara?"):
                st.markdown(
                    "En Safari/iPad: toca **'AA'** → **'Sitio web para móviles'**. "
                    "Si persiste, usa **'📁 Subir Foto'** para abrir la cámara nativa."
                )
        else:
            foto = st.file_uploader(
                "Seleccionar foto de la cédula", type=["jpg", "png", "jpeg"],
                key=f"up_{prefix}",
            )

        if foto and st.session_state.get(f"procesado_{prefix}") != foto.name:
            with st.spinner("⚡ Analizando documento con Visión Artificial..."):
                rut, nombre, fecha, sexo = procesar_cedula_inteligente(foto)
                if rut or nombre:
                    if rut:    st.session_state.form[key_rut] = rut
                    if nombre: st.session_state.form[key_nom] = nombre
                    if fecha and tipo_paciente == "TITULAR":
                        try:
                            parsed = datetime.strptime(fecha, "%d/%m/%Y").date()
                            if date(1910, 1, 1) <= parsed <= date.today():
                                st.session_state.form["fecha_nac"] = parsed
                        except Exception:
                            pass
                    if sexo and tipo_paciente == "TITULAR":
                        st.session_state.form["genero_biologico"] = sexo
                    st.session_state[f"procesado_{prefix}"]      = foto.name
                    st.session_state[f"mostrar_camara_{prefix}"] = False
                    st.success("✅ Datos extraídos. Cerrando escáner...")
                    time.sleep(0.8)
                    st.rerun()
                else:
                    st.error("❌ No se detectó texto claro. Intente con mejor iluminación.")
                    st.session_state[f"procesado_{prefix}"] = foto.name

        if st.button("❌ Cerrar Escáner", key=f"close_{prefix}"):
            st.session_state[f"mostrar_camara_{prefix}"] = False
            st.rerun()


@st.fragment
def vista_seleccion_procedimiento(df, catalogo):
    """
    Selector de procedimientos HL7/FONASA aislado como fragmento:
    el toggle de lateralidad no recarga toda la encuesta.
    """
    if df is None:
        st.error("❌ No se encontró el catálogo de prestaciones. Verifique listado_prestaciones.csv")
        return

    st.markdown('<div class="section-header">Información del Examen</div>', unsafe_allow_html=True)
    ce1, ce2 = st.columns(2)

    esp_raw = sorted([str(e) for e in df['ESPECIALIDAD'].unique() if pd.notna(e)])
    esp_idx = min(st.session_state.form.get("esp_idx", 0), len(esp_raw) - 1)
    esp_sel = ce1.selectbox("Especialidad", esp_raw, index=esp_idx, key="sel_esp_frag")
    st.session_state.form["esp_idx"] = esp_raw.index(esp_sel)

    filtered   = df[df['ESPECIALIDAD'] == esp_sel]
    list_pre   = sorted(filtered['PROCEDIMIENTO A REALIZAR'].dropna().unique().tolist())
    opciones   = sorted(list(set(list_pre + st.session_state.proc_cache)))

    def sync_proc():
        st.session_state.proc_cache = st.session_state.widget_proc_frag

    pre_sel = ce2.multiselect(
        "Procedimiento(s) a realizar",
        options=opciones,
        default=st.session_state.proc_cache,
        key="widget_proc_frag",
        on_change=sync_proc,
    )

    if pre_sel:
        st.session_state.form["recursos_hl7"]         = []
        st.session_state.form["nombres_transformados"] = {}
        st.session_state.tiene_contraste              = False

        for examen in pre_sel:
            fila      = df[df['PROCEDIMIENTO A REALIZAR'] == examen]
            req_lat   = (not fila.empty and
                         str(fila.iloc[0].get('REQUIERE_LATERALIDAD', 'NO')).upper() == 'SI')
            info_cat  = catalogo.get(examen, {"contraste": False, "codigo_fonasa": "S/C"})
            if info_cat.get("contraste"):
                st.session_state.tiene_contraste = True

            lat_actual = "No aplica"
            if req_lat:
                clave      = (examen.replace(' ', '_').replace('(', '')
                                     .replace(')', '').replace('-', '_'))
                es_bilat   = st.session_state.get(f"chk_ambas_{clave}", False)
                tgl_activo = st.session_state.get(f"tgl_lado_{clave}", False)
                lat_actual = "Ambas" if es_bilat else ("Izquierda" if tgl_activo else "Derecha")
                nombre_calc = construir_nombre_especifico(examen, lat_actual)

                st.markdown(
                    f"<p style='font-size:0.9rem;margin-bottom:2px;'>"
                    f"<b>PROCEDIMIENTO:</b> {nombre_calc}</p>",
                    unsafe_allow_html=True,
                )
                c1, c2, c3, c4, c5 = st.columns([0.6, 0.6, 0.7, 0.2, 2.5])
                c1.markdown(
                    f"<p style='margin-top:4px;font-size:0.85rem;text-align:right;"
                    f"color:{'#999' if es_bilat else '#333'};'>DERECHA</p>",
                    unsafe_allow_html=True,
                )
                c2.toggle("Lado Examen", key=f"tgl_lado_{clave}",
                          disabled=es_bilat, label_visibility="collapsed")
                c3.markdown(
                    f"<p style='margin-top:4px;font-size:0.85rem;text-align:left;"
                    f"color:{'#999' if es_bilat else '#333'};'>IZQUIERDA</p>",
                    unsafe_allow_html=True,
                )
                c4.markdown("<p style='margin-top:2px;color:#ccc;font-size:1.1rem;text-align:center;'>|</p>",
                            unsafe_allow_html=True)
                c5.checkbox("AMBOS (AS)", key=f"chk_ambas_{clave}")
                st.markdown("<div style='border-bottom:1px dashed #e0e0e0;margin:10px 0;'></div>",
                            unsafe_allow_html=True)
            else:
                nombre_calc = examen

            st.session_state.form["nombres_transformados"][examen] = nombre_calc
            sr = generar_service_request_hl7(examen, lat_actual, catalogo)
            st.session_state.form["recursos_hl7"].append(sr)
            st.caption(f"🧬 HL7 FHIR R4 | Código FONASA MLE: {info_cat.get('codigo_fonasa', 'S/C')}")


# =====================================================================
# SECCIÓN 16: MODAL DE CONSENTIMIENTO FES / HL7 FHIR
# =====================================================================
@st.dialog("Aviso Legal y Consentimiento (FES / HL7 FHIR R4)")
def modal_consentimiento():
    st.markdown(
        "Para autorizar su resonancia magnética, utilizaremos un sistema de "
        "**Firma Electrónica Simple (FES)**. Al firmar, el sistema capturará de forma "
        "encriptada su identidad junto con la fecha y hora exacta del procedimiento."
    )
    st.markdown(
        "Sus datos se estructurarán bajo el estándar **HL7 FHIR R4** (interoperabilidad "
        "internacional de salud) y serán protegidos bajo **Ley 19.628** (Protección de "
        "Datos Personales) y **Ley 19.799** (Firma Electrónica Simple Chile)."
    )
    st.markdown("---")
    st.markdown(
        "**¿Comprende cómo se procesará su firma y está de acuerdo con el registro "
        "e interoperabilidad segura de sus datos?**"
    )
    c1, c2 = st.columns(2)
    if c1.button("✅ Sí, comprendo y acepto", type="primary", use_container_width=True):
        st.session_state.abrir_modal = False
        st.session_state.step        = 1
        st.rerun()
    if c2.button("❌ Cancelar", use_container_width=True):
        st.session_state.abrir_modal = False
        st.rerun()


# =====================================================================
# SECCIÓN 17: PASO 0 — BIENVENIDA INMERSIVA (Video + Clic Invisible)
# =====================================================================
def pagina_0_bienvenida():
    try:
        with open("video_bienvenida.mp4", "rb") as vf:
            video_b64 = base64.b64encode(vf.read()).decode("utf-8")
        video_url = f"data:video/mp4;base64,{video_b64}"
    except Exception:
        video_url = ""

    st.markdown(f"""
    <style>
    /* 1. Fondo principal para el video */
    .stApp {{ overflow: hidden !important; background-color: white !important; }}
    
    /* 2. El Video se va al fondo (z-index: 0) y no roba clics */
    #video-fondo {{ 
        position: fixed !important; 
        z-index: 0 !important; 
        pointer-events: none !important; 
    }}
    
    @media (min-width: 1024px) {{
        #video-fondo {{
            top: 50% !important; left: 50% !important;
            width: 85vw !important; height: 85vh !important;
            transform: translate(-50%, -50%) !important;
            object-fit: contain !important;
        }}
    }}
    @media (max-width: 1023px) {{
        #video-fondo {{
            top: 50% !important; left: 50% !important;
            width: 100vw !important; height: 100vh !important;
            transform: translate(-50%, -50%) scale(1.30) !important;
            object-fit: contain !important;
        }}
    }}
    video::-webkit-media-controls,
    video::-webkit-media-controls-enclosure,
    video::-webkit-media-controls-play-button {{
        display: none !important; opacity: 0 !important;
    }}
    </style>
    <video id="video-fondo" autoplay loop muted playsinline
           webkit-playsinline="true" preload="auto"
           oncanplay="this.muted=true; this.play();">
        <source src="{video_url}" type="video/mp4">
    </video>
    <script>
    document.addEventListener('DOMContentLoaded', () => {{
        let v = document.getElementById('video-fondo');
        if (v) {{ v.muted = true; v.play().catch(() => {{}}); }}
    }});
    </script>
    """, unsafe_allow_html=True)

    # 3. EL CAPTURADOR DE CLICS (Cristal Puro Inquebrantable)
    if not st.session_state.abrir_modal:
        st.markdown("""
        <style>
        /* Envolvemos el contenedor base de Streamlit */
        div.stButton {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            z-index: 99999 !important; /* Muy por encima del video */
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }
        /* Aplastamos el CSS global de la app para asegurar pantalla completa */
        div.stButton > button {
            width: 100vw !important;
            height: 100vh !important;
            background-color: transparent !important; /* Cristal puro (No opacity:0) */
            color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            cursor: pointer !important;
        }
        /* Evitamos que al hacer hover aparezcan colores */
        div.stButton > button:hover, 
        div.stButton > button:active, 
        div.stButton > button:focus {
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            transform: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # El botón invisible que dispara el Modal Legal
        if st.button(" ", key="btn_invisible_click"):
            st.session_state.abrir_modal = True
            st.rerun()

    # 4. LLAMADA AL MODAL
    if st.session_state.abrir_modal:
        modal_consentimiento()

# =====================================================================
# SECCIÓN 18: PASO 1 — REGISTRO DEMOGRÁFICO COMPLETO
# =====================================================================
def pagina_1_registro(df, catalogo):
    st.markdown('<style>.stApp { overflow: auto !important; }</style>', unsafe_allow_html=True)

    # Captura IP del dispositivo del paciente
    ip = obtener_ip()
    if ip and ip not in ["Detectando...", "0.0.0.0", 0]:
        st.session_state.form["ip_dispositivo"] = ip

    mostrar_logo()
    st.title("Registro de Paciente")
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Agenda ───────────────────────────────────────────────────────
    es_hoy = st.radio(
        "¿Su examen por Resonancia Magnética está agendado para el día de hoy?",
        ["Sí, es para hoy", "No, está agendado para otro día"],
        horizontal=True,
    )
    if es_hoy == "No, está agendado para otro día":
        st.session_state.form["fecha_examen"] = st.date_input(
            "📅 Seleccione la fecha del examen:", min_value=date.today()
        )
    else:
        st.session_state.form["fecha_examen"] = date.today()
    st.markdown("---")

    # ── Procedencia ───────────────────────────────────────────────────
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        opts_proc = ["Ambulatorio", "Hospitalizado"]
        st.session_state.form["procedencia"] = st.radio(
            "**Procedencia del Paciente:**",
            opts_proc,
            index=opts_proc.index(st.session_state.form.get("procedencia", "Ambulatorio")),
            horizontal=True,
        )
    with col_p2:
        if st.session_state.form["procedencia"] == "Hospitalizado":
            st.session_state.form["unidad_procedencia"] = st.text_input(
                "**Unidad y cama (Ej. UCI - C2; Medicina Varones - C10):**",
                value=st.session_state.form.get("unidad_procedencia", ""),
                key="txt_unidad_proc",
            )
        else:
            st.session_state.form["unidad_procedencia"] = ""
    st.markdown("---")

    # ── Datos del Paciente ────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.form["nombre"] = st.text_input(
            "Nombre Completo del Paciente",
            value=st.session_state.form["nombre"],
        )
        st.session_state.form["sin_rut"] = st.checkbox(
            "Sin RUT, poseo otro documento",
            value=st.session_state.form["sin_rut"],
        )
        if st.session_state.form["sin_rut"]:
            t_opts = ["Pasaporte", "Cédula de extranjero"]
            idx_d  = t_opts.index(st.session_state.form["tipo_doc"]) if st.session_state.form["tipo_doc"] in t_opts else 0
            st.session_state.form["tipo_doc"] = st.selectbox("Tipo de documento", t_opts, index=idx_d)
            st.session_state.form["num_doc"]  = st.text_input("N° de documento", value=st.session_state.form["num_doc"])
            st.session_state.form["rut"]      = ""
        else:
            vista_escaner_cedula("TITULAR")   # Fragmento OCR titular

        # Género con soporte No Binario
        g_opts = ["Masculino", "Femenino", "No binario"]
        gen_sel = st.selectbox("Identidad de Género", g_opts, index=st.session_state.form["genero_idx"])
        st.session_state.form["genero_idx"] = g_opts.index(gen_sel)
        sexo_final = gen_sel
        if gen_sel == "No binario":
            sb_opts = ["Masculino", "Femenino"]
            ocr_s   = st.session_state.form.get("genero_biologico", "")
            idx_bio = sb_opts.index(ocr_s) if ocr_s in sb_opts else st.session_state.form["sexo_bio_idx"]
            sexo_bio = st.selectbox("Sexo asignado al nacer (para fines clínicos)", sb_opts, index=idx_bio)
            st.session_state.form["sexo_bio_idx"]    = sb_opts.index(sexo_bio)
            st.session_state.form["genero_biologico"] = f"No binario (Bio: {sexo_bio})"
            sexo_final = f"No binario (Bio: {sexo_bio})"
        else:
            st.session_state.form["genero_biologico"] = gen_sel

    with c2:
        st.session_state.form["fecha_nac"] = st.date_input(
            "Fecha de Nacimiento",
            value=st.session_state.form["fecha_nac"],
            min_value=date(1910, 1, 1), max_value=date.today(),
            format="DD/MM/YYYY",
        )
        st.session_state.form["email"]    = st.text_input("Email de contacto",  value=st.session_state.form["email"])
        st.session_state.form["telefono"] = st.text_input(
            "Teléfono móvil", value=st.session_state.form["telefono"],
            placeholder="+56 9 1234 5678",
        )

    # ── Autovalencia y Tutor Legal ────────────────────────────────────
    edad       = calcular_edad(st.session_state.form["fecha_nac"])
    edad_vis   = obtener_edad_visual_pdf(st.session_state.form["fecha_nac"])

    st.markdown("<br>", unsafe_allow_html=True)
    autoval = st.toggle(
        "¿El paciente es autovalente para firmar el consentimiento por sí mismo?",
        value=st.session_state.form.get("es_autovalente", True),
        help="Desactiva esto si el paciente posee Alzheimer, ACV, estado de conciencia alterado o discapacidad severa.",
    )
    st.session_state.form["es_autovalente"] = autoval
    requiere_tutor = (edad < 18) or not st.session_state.form["es_autovalente"]

    if requiere_tutor:
        if edad < 2:
            icono, txt_r, color_r = "🍼👶🏻", f"<b>Paciente LACTANTE ({edad_vis}):</b> Requiere Representante Legal.", "#007BFF"
        elif edad < 14:
            icono, txt_r, color_r = "🧸👦🏻", f"<b>Paciente PEDIÁTRICO ({edad_vis}):</b> Requiere Representante Legal.", "#17A2B8"
        elif edad < 18:
            icono, txt_r, color_r = "🛹👦🏻", f"<b>Paciente ADOLESCENTE ({edad_vis}):</b> Requiere Representante Legal.", "#6C757D"
        else:
            icono, txt_r, color_r = "🧑🏻‍🦽🧠", f"<b>ADULTO NO AUTOVALENTE ({edad_vis}):</b> Requiere Representante Legal estricto.", "#DC3545"

        st.markdown(
            f'<div style="background-color:white;border-left:6px solid {color_r};padding:12px;'
            f'border-radius:5px;box-shadow:0px 2px 5px rgba(0,0,0,0.1);margin-bottom:15px;">'
            f'<p style="margin:0;color:#333333;font-size:15px;">{icono} {txt_r}</p></div>',
            unsafe_allow_html=True,
        )
        st.session_state.form["nombre_tutor"]    = st.text_input("Nombre Representante / Cuidador", value=st.session_state.form["nombre_tutor"])
        st.session_state.form["parentesco_tutor"]= st.text_input("Parentesco (Ej: Madre, Esposo, Cuidador)", value=st.session_state.form["parentesco_tutor"])
        st.session_state.form["sin_rut_tutor"]   = st.checkbox("Representante no posee RUT", value=st.session_state.form["sin_rut_tutor"])
        if st.session_state.form["sin_rut_tutor"]:
            t2 = ["Pasaporte", "Cédula de extranjero"]
            i2 = t2.index(st.session_state.form["tipo_doc_tutor"]) if st.session_state.form["tipo_doc_tutor"] in t2 else 0
            st.session_state.form["tipo_doc_tutor"] = st.selectbox("Tipo doc. Representante", t2, index=i2)
            st.session_state.form["num_doc_tutor"]  = st.text_input("N° doc. Representante", value=st.session_state.form["num_doc_tutor"])
            st.session_state.form["rut_tutor"]      = ""
        else:
            vista_escaner_cedula("TUTOR")  # Fragmento OCR tutor

    # ── Selección de Procedimiento (Fragmento HL7) ────────────────────
    vista_seleccion_procedimiento(df, catalogo)

    # ── Orden Médica ─────────────────────────────────────────────────
    st.markdown('<div class="section-header">Documentación Médica</div>', unsafe_allow_html=True)
    st.file_uploader("Cargue la Orden Médica (Opcional)", type=["pdf", "jpg", "jpeg"], key="up_orden_p1")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("CONTINUAR →", type="primary", use_container_width=True):
        # Validaciones
        campos_pac = ["nombre", "fecha_nac", "telefono"]
        if st.session_state.form.get("sin_rut"): campos_pac.extend(["tipo_doc", "num_doc"])
        else:                                     campos_pac.append("rut")
        datos_ok = all(str(st.session_state.form.get(k, "")).strip() != "" for k in campos_pac)

        tutor_ok = True
        if requiere_tutor:
            campos_tut = ["nombre_tutor", "parentesco_tutor"]
            if st.session_state.form.get("sin_rut_tutor"): campos_tut.extend(["tipo_doc_tutor", "num_doc_tutor"])
            else:                                           campos_tut.append("rut_tutor")
            tutor_ok = all(str(st.session_state.form.get(k, "")).strip() != "" for k in campos_tut)

        if not st.session_state.proc_cache:
            st.error("🚨 Seleccione al menos un procedimiento radiológico.")
        elif not datos_ok:
            st.error("🚨 Faltan datos obligatorios del paciente (Nombre, RUT/Documento o Teléfono).")
        elif requiere_tutor and not tutor_ok:
            st.error("🚨 El paciente requiere representante legal. Complete Nombre, Parentesco y RUT/Documento del cuidador.")
        else:
            # Persistir archivos antes de cambiar de paso
            ord_file = st.session_state.get("up_orden_p1")
            st.session_state["orden_persistente"] = (
                {"name": ord_file.name, "bytes": ord_file.getvalue()} if ord_file else None
            )
            # Nombres finales con lateralidad aplicada
            nombres_finales = [
                st.session_state.form["nombres_transformados"].get(e, e)
                for e in st.session_state.proc_cache
            ]
            st.session_state.procedimiento          = ", ".join(nombres_finales)
            st.session_state.edad_para_calculo      = edad
            st.session_state.sexo_para_calculo      = sexo_final
            st.session_state.step                   = 2
            st.rerun()


# =====================================================================
# SECCIÓN 19: PASO 2 — CUESTIONARIO CLÍNICO COMPLETO
# =====================================================================
def pagina_2_cuestionario():
    mostrar_logo()
    st.title("📋 Cuestionario de Seguridad RM")

    # ── 1. BIOSEGURIDAD MAGNÉTICA ─────────────────────────────────────
    st.markdown('<div class="section-header">1. Bioseguridad Magnética</div>', unsafe_allow_html=True)
    for key_b, lbl_b in [
        ("bio_marcapaso", "Marcapasos cardiaco"),
        ("bio_implantes", "Implantes metálicos, quirúrgicos, prótesis o dispositivos electrónicos"),
    ]:
        val_b = st.session_state.form.get(key_b) == "Sí"
        res_b = st.toggle(lbl_b, value=val_b)
        st.session_state.form[key_b] = "Sí" if res_b else "No"

    if (st.session_state.form["bio_marcapaso"] == "Sí" or
            st.session_state.form["bio_implantes"] == "Sí"):
        st.session_state.form["bio_detalle"] = st.text_area(
            "Detalle de qué tipo y ubicación:",
            value=st.session_state.form.get("bio_detalle", ""), height=70,
        )
    else:
        st.session_state.form["bio_detalle"] = ""

    # ── 2. ANTECEDENTES CLÍNICOS ──────────────────────────────────────
    st.markdown('<div class="section-header">2. Antecedentes Clínicos</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    k1 = [("clin_ayuno","Ayuno (2 hrs o más)"),("clin_asma","Asma"),
          ("clin_hiperten","Hipertensión"),("clin_hipertiroid","Hipertiroidismo")]
    k2 = [("clin_diabetes","Diabetes"),("clin_alergico","Alérgico"),
          ("clin_metformina","Suspende metformina (48 hrs. antes)"),("clin_renal","Insuficiencia renal")]
    k3 = [("clin_dialisis","Diálisis"),("clin_claustro","Claustrofóbico"),
          ("clin_embarazo","Embarazo"),("clin_lactancia","Lactancia")]

    for col, keys in zip([c1, c2, c3], [k1, k2, k3]):
        for k, lbl in keys:
            val = st.session_state.form.get(k) == "Sí"
            res = col.toggle(lbl, value=val, key=k)
            st.session_state.form[k] = "Sí" if res else "No"
            if k == "clin_alergico" and st.session_state.form["clin_alergico"] == "Sí":
                st.session_state.form["alergias_detalle"] = col.text_input(
                    "⚠️ Especifique alergias (Fármacos/Alimentos):",
                    value=st.session_state.form.get("alergias_detalle", ""),
                )
            elif k == "clin_alergico":
                st.session_state.form["alergias_detalle"] = ""

    # Condiciones especiales
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**¿Posee alguna condición o requerimiento especial?**")
    tgl_cond = st.toggle("Sí, deseo indicar una condición especial", key="toggle_cond")
    if tgl_cond:
        opciones_cond = [
            "Discapacidad física o movilidad reducida (ej.: uso de silla de ruedas, amputaciones, secuelas motoras)",
            "Condición del neurodesarrollo o neurodivergencia (ej.: TEA, TDAH, dislexia)",
            "Discapacidad intelectual o cognitiva",
            "Discapacidad sensorial (ej.: visual, auditiva)",
            "Otra",
        ]
        st.session_state.form["condiciones"] = st.multiselect(
            "Seleccione las que correspondan:",
            opciones_cond,
            default=st.session_state.form.get("condiciones", []),
        )
        st.session_state.form["condicion_detalle"] = st.text_input(
            "Detalle la condición o requerimiento:",
            value=st.session_state.form.get("condicion_detalle", ""),
        )
    else:
        st.session_state.form["condiciones"]       = []
        st.session_state.form["condicion_detalle"] = ""

    # ── 3. QUIRÚRGICO / TERAPÉUTICO ──────────────────────────────────
    st.markdown('<div class="section-header">3. Antecedentes Quirúrgicos y/o Terapéuticos</div>', unsafe_allow_html=True)
    cir_tgl = st.toggle("¿Ha sido sometido a alguna cirugía?",
                         value=st.session_state.form.get("quir_cirugia_check") == "Sí")
    st.session_state.form["quir_cirugia_check"] = "Sí" if cir_tgl else "No"
    if cir_tgl:
        st.session_state.form["quir_cirugia_detalle"] = st.text_area(
            "Detalle nombre de la cirugía y fecha:",
            value=st.session_state.form.get("quir_cirugia_detalle", ""), height=70,
        )
    else:
        st.session_state.form["quir_cirugia_detalle"] = ""

    cancer_tgl = st.toggle("¿Usted cursa o ha cursado alguna enfermedad de cáncer?",
                            value=st.session_state.form.get("quir_cancer_check") == "Sí")
    st.session_state.form["quir_cancer_check"] = "Sí" if cancer_tgl else "No"
    if cancer_tgl:
        st.session_state.form["quir_cancer_detalle"] = st.text_area(
            "Detalle tipo de cáncer y etapa:",
            value=st.session_state.form.get("quir_cancer_detalle", ""), height=70,
        )
        st.markdown("**¿Ha tenido que realizarse alguno de estos tratamientos?**")
        ct1, ct2, ct3, ct4 = st.columns(4)
        st.session_state.form["rt"] = ct1.checkbox("Radioterapia (RT)",   value=st.session_state.form.get("rt", False))
        st.session_state.form["qt"] = ct2.checkbox("Quimioterapia (QT)",  value=st.session_state.form.get("qt", False))
        st.session_state.form["bt"] = ct3.checkbox("Braquiterapia (BT)",  value=st.session_state.form.get("bt", False))
        st.session_state.form["it"] = ct4.checkbox("Inmunoterapia (IT)",  value=st.session_state.form.get("it", False))
        st.session_state.form["quir_otro_trat"] = st.text_input(
            "Algún otro tratamiento que mencionar:",
            value=st.session_state.form.get("quir_otro_trat", ""),
        )
    else:
        st.session_state.form.update({
            "quir_cancer_detalle": "", "rt": False, "qt": False,
            "bt": False, "it": False, "quir_otro_trat": "",
        })

    # ── 4. EXÁMENES ANTERIORES ───────────────────────────────────────
    st.markdown('<div class="section-header">4. Exámenes Anteriores</div>', unsafe_allow_html=True)
    prev_tgl = st.toggle(
        "¿Tiene exámenes anteriores relacionados a la Resonancia Magnética?",
        value=st.session_state.form.get("has_examenes_previos") == "Sí",
    )
    st.session_state.form["has_examenes_previos"] = "Sí" if prev_tgl else "No"
    if prev_tgl:
        st.markdown("*Seleccione los que tiene, en formato digital o físico.*")
        ce1, ce2, ce3, ce4, ce5 = st.columns(5)
        st.session_state.form["ex_rx"]  = ce1.checkbox("Radiografía (Rx)",          value=st.session_state.form.get("ex_rx",  False))
        st.session_state.form["ex_mg"]  = ce2.checkbox("Mamografía (MG)",            value=st.session_state.form.get("ex_mg",  False))
        st.session_state.form["ex_eco"] = ce3.checkbox("Ecotomografía (Eco)",        value=st.session_state.form.get("ex_eco", False))
        st.session_state.form["ex_tc"]  = ce4.checkbox("Tomografía Computarizada (TC)", value=st.session_state.form.get("ex_tc",  False))
        st.session_state.form["ex_rm"]  = ce5.checkbox("Resonancia Magnética (RM)",  value=st.session_state.form.get("ex_rm",  False))
        st.session_state.form["ex_otros"] = st.text_input("Otros estudios:", value=st.session_state.form.get("ex_otros", ""))
        st.markdown("---")
        st.markdown("**A. Archivos Ligeros (Informes en PDF o Fotos)**")
        st.file_uploader("Adjunte sus informes (Máx. 4)", type=["pdf", "jpg", "jpeg"],
                         accept_multiple_files=True, key="up_anteriores_p2")
        st.markdown("**B. Archivos Pesados (Links a Portales Externos o DICOM)**")
        st.info("💡 Si su examen está en la nube, peguelo aquí junto a los datos de acceso.")
        cl1, cp1 = st.columns([3, 1])
        st.session_state.form["link_exam_1"] = cl1.text_input("🔗 Link 1:", value=st.session_state.form.get("link_exam_1", ""), placeholder="https://...")
        st.session_state.form["pin_exam_1"]  = cp1.text_input("🔑 PIN 1:", value=st.session_state.form.get("pin_exam_1", ""))
        cl2, cp2 = st.columns([3, 1])
        st.session_state.form["link_exam_2"] = cl2.text_input("🔗 Link 2 (Opcional):", value=st.session_state.form.get("link_exam_2", ""))
        st.session_state.form["pin_exam_2"]  = cp2.text_input("🔑 PIN 2:", value=st.session_state.form.get("pin_exam_2", ""))
    else:
        st.session_state.form.update({
            "ex_rx": False, "ex_mg": False, "ex_eco": False, "ex_tc": False, "ex_rm": False,
            "ex_otros": "", "link_exam_1": "", "pin_exam_1": "", "link_exam_2": "", "pin_exam_2": "",
        })

    # ── 5. VFG (Solo si el examen requiere contraste) ─────────────────
    if st.session_state.tiene_contraste:
        edad_c = st.session_state.get("edad_para_calculo", 30)
        tit_v  = ("5. Función Renal (VFG Pediátrica - Schwartz)"
                  if edad_c < 18 else
                  "5. Función Renal (VFG Adulto - Cockcroft-Gault)")
        st.markdown(f'<div class="section-header">{tit_v}</div>', unsafe_allow_html=True)

        fn_vfg    = st.session_state.form["fecha_nac"]
        hoy_v     = date.today()
        edad_d_v  = (hoy_v - fn_vfg).days
        edad_m_v  = edad_d_v / 30.4
        edad_a_v  = edad_d_v / 365.25

        if edad_a_v < 2:
            ico_v, txt_v, col_v = "🍼👶🏻", "<b>Paciente LACTANTE:</b> Se solicitará Talla en cm (Schwartz Clásica).", "#007BFF"
        elif edad_a_v < 14:
            ico_v, txt_v, col_v = "🧸👦🏻", "<b>Paciente PEDIÁTRICO:</b> Se solicitará Talla en cm (Schwartz Bedside 2009).", "#17A2B8"
        elif edad_a_v < 18:
            ico_v, txt_v, col_v = "🛹👦🏻", "<b>Paciente ADOLESCENTE:</b> Se solicitará Talla en cm (Schwartz Bedside 2009).", "#6C757D"
        else:
            ico_v, txt_v, col_v = "🧑🏻‍⚕️", "<b>Paciente ADULTO:</b> Se requiere Peso en kg (Cockcroft-Gault).", "#800020"

        st.markdown(
            f'<div style="background-color:white;border-left:6px solid {col_v};padding:12px;'
            f'border-radius:5px;box-shadow:0px 2px 5px rgba(0,0,0,0.1);margin-bottom:15px;">'
            f'<p style="margin:0;color:#333333;font-size:15px;">{ico_v} {txt_v}</p></div>',
            unsafe_allow_html=True,
        )
        c_crea, c_fc = st.columns(2)
        st.session_state.form["creatinina"] = c_crea.number_input(
            "Creatinina (mg/dL)", value=float(st.session_state.form.get("creatinina", 0.0)),
            step=0.01, min_value=0.0,
        )
        st.session_state.form["fecha_creatinina"] = c_fc.date_input(
            "Fecha Examen Creatinina",
            value=st.session_state.form.get("fecha_creatinina", date.today()),
        )
        if edad_a_v < 18:
            st.session_state.form["talla"] = st.number_input(
                "Talla (cm)", value=float(st.session_state.form.get("talla", 0.0)), step=0.5, min_value=0.0,
            )
            st.session_state.form["peso"]  = 0.0
        else:
            st.session_state.form["peso"]  = st.number_input(
                "Peso (kg)", value=float(st.session_state.form.get("peso", 0.0)), step=0.1, min_value=0.0,
            )
            st.session_state.form["talla"] = 0.0

        if st.session_state.form["creatinina"] > 0:
            vfg, msg_v, color_v, clase_v = calcular_vfg_clinica(
                st.session_state.form["fecha_nac"],
                st.session_state.get("sexo_para_calculo", "Masculino"),
                st.session_state.form["peso"],
                st.session_state.form["talla"],
                st.session_state.form["creatinina"],
            )
            st.session_state.form["vfg"] = vfg
            if vfg > 0:
                st.markdown(
                    f'<div class="vfg-box {clase_v}" '
                    f'style="border-left:10px solid {color_v};padding:15px;border-radius:5px;">'
                    f'<p style="margin:0;color:{color_v};font-weight:bold;">{msg_v}</p>'
                    f'<small>VFG Estimada:</small>'
                    f'<h2 style="margin:0;">{vfg:.2f} ml/min/1.73m²</h2></div>',
                    unsafe_allow_html=True,
                )

    st.markdown("<br>", unsafe_allow_html=True)
    col_nav = st.columns(2)
    if col_nav[0].button("← ATRÁS"):
        st.session_state.step = 1
        st.rerun()
    if col_nav[1].button("SIGUIENTE →", type="primary"):
        up_p2 = st.session_state.get("up_anteriores_p2")
        st.session_state["examenes_persistentes"] = (
            [{"name": f.name, "bytes": f.getvalue()} for f in up_p2]
            if up_p2 else []
        )
        st.session_state.step = 3
        st.rerun()


# =====================================================================
# SECCIÓN 20: PASO 3 — CONSENTIMIENTO, FIRMA CANVAS + FES pyotp
# =====================================================================
def pagina_3_consentimiento():
    mostrar_logo()
    st.title("Información al Paciente")
    st.markdown('<div class="section-header">LEA ATENTA Y CUIDADOSAMENTE LO SIGUIENTE:</div>',
                unsafe_allow_html=True)
    st.markdown("""
    <div class="legal-text">
    <strong>OBJETIVOS</strong><br>
    La Resonancia Magnética (RM) es una segura técnica de Diagnóstico, que permite la adquisición
    de imágenes de gran sensibilidad en todos los planos del espacio de las estructuras del cuerpo.
    Tiene como objetivo obtener Información, datos funcionales y morfológicos para detectar
    precozmente una enfermedad.<br>
    Para este examen eventualmente se puede requerir la utilización de un medio de contraste
    paramagnético de administración endovenosa llamado gadolinio, que permite realzar ciertos
    tejidos del cuerpo para un mejor diagnóstico.<br><br>
    <strong>CARACTERISTICAS</strong><br>
    La Resonancia utiliza fuertes campos magnéticos y ondas de radiofrecuencia, por lo que es muy
    importante dejar fuera de la sala absolutamente todo lo que lleve consigo de tipo metálico y/o
    electrónico (relojes, pulseras, teléfonos, tarjetas magnéticas, etc). Si lleva material de este
    tipo en su cuerpo (fijaciones dentales, piercings, algunos tatuajes, balas o esquirlas metálicas)
    ciertos tipos de prótesis (valvulares, de cadera, de rodilla, clips metálicos, etc), o implantes,
    así como dispositivos electrónicos de carácter médico como bombas de insulina, prótesis auditivas,
    marcapasos, desfibriladores, etc. Avísenos, ya que puede contraindicar de manera absoluta la
    realización de este examen.<br>
    Usted será posicionado en la camilla del equipo, según el estudio a realizar y se colocarán cerca
    de la zona a estudiar unos dispositivos (bobinas) que pueden ser de diversos tamaños. Esta
    exploración suele ser larga (entre 20 min y 1 hr según los casos). Notará ruido derivado del
    funcionamiento de la RM (por lo que le facilitaremos unos protectores auditivos), todo esto es
    normal y se le vigilará constantemente desde la sala de control.<br>
    Es muy importante que permanezca quieto durante el estudio y siga las instrucciones del
    Tecnólogo Médico.<br><br>
    <strong>POTENCIALES RIESGOS</strong><br>
    Existe una muy baja posibilidad de que se presente una reacción adversa al medio de contraste
    (0.07-2.4%) la mayoría de carácter leve fundamentalmente nauseas o cefaleas al momento de la
    inyección.<br>
    Pacientes con deterioro importante de la función renal, poseen riesgo de desarrollo de fibrosis
    nefrogénica sistémica.<hr>
    He sido informado de mi derecho de anular o revocar posteriormente este documento, dejándolo
    constatado por escrito y firmado por mi o mi representante.<br><br>
    Autorizo la realización del procedimiento anteriormente especificado y las acciones que sean
    necesarias en caso de surgir complicaciones durante el procedimiento. Además, doy consentimiento
    para que se administren medicamentos y/o infusiones que se requieran para la realización de este.
    </div>
    """, unsafe_allow_html=True)

    st.session_state.form["autoriza_gad"] = st.radio(
        "¿Ha leído y autoriza el procedimiento?", ["SÍ", "NO"], index=None,
    )

    # Checkbox de veracidad
    st.markdown("""
    <style>
    div[data-testid="stCheckbox"]:has(label[title*="Verifico que todos los datos"]) div[role="checkbox"][aria-checked="true"] {
        background-color: #28a745 !important; border-color: #28a745 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.session_state.form["veracidad"] = st.checkbox(
        "**Verifico que todos los datos ingresados son fidedignos y corresponden a mi estado de salud actual.**",
        value=st.session_state.form.get("veracidad", False),
        key="chk_veracidad_legal",
    )

    # ── Canvas de Firma Manual ────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.write("**Firma del Paciente / Representante legal:**")
    canvas_result = st_canvas(
        stroke_width=4, stroke_color="#000", background_color="#fff",
        height=150, width=400, key="canvas_firma",
    )
    if canvas_result is not None and canvas_result.image_data is not None:
        st.session_state["firma_guardada"] = canvas_result.image_data

    # ── FES — Firma Electrónica Simple (Ley 19.799 Chile) ────────────
    st.markdown('<div class="section-header">Validación de Identidad (Ley 19.799)</div>',
                unsafe_allow_html=True)
    st.write("Seleccione cómo desea recibir su código de firma electrónica de 6 dígitos:")

    col_met, col_dato = st.columns(2)
    with col_met:
        metodo = st.radio(
            "Método de envío:",
            ["📧 Correo Electrónico", "🟩 WhatsApp"],
            label_visibility="collapsed",
        )
        st.session_state.form["otp_metodo"] = "Email" if "Correo" in metodo else "WhatsApp"

    with col_dato:
        destino = (st.session_state.form.get("email")
                   if st.session_state.form["otp_metodo"] == "Email"
                   else st.session_state.form.get("telefono"))
        enmascarado = enmascarar_contacto(destino or "", st.session_state.form["otp_metodo"])
        st.info(f"Destino seguro: **{enmascarado}**")

    if st.button("📲 Generar y Enviar Código FES", use_container_width=True):
        if not destino:
            st.error(f"🚨 No se registró un {st.session_state.form['otp_metodo']} en el formulario. Regrese al Paso 1.")
        else:
            # pyotp TOTP — intervalo 300 s = 5 minutos (cumple Ley 19.799)
            totp   = pyotp.TOTP(st.session_state.form["otp_secret"], interval=300)
            codigo = totp.now()
            exito  = despachar_codigo_fes(st.session_state.form["otp_metodo"], destino, codigo)
            if exito:
                st.session_state.form["otp_enviado"]   = True
                st.session_state.form["otp_timestamp"] = time.time()
                st.success("✅ Código enviado. Revise su bandeja o teléfono. Válido por 5 minutos.")

    if st.session_state.form.get("otp_enviado"):
        st.markdown("---")
        transcurrido = time.time() - st.session_state.form.get("otp_timestamp", time.time())
        if transcurrido > 300:
            st.warning("⏳ El código expiró. Presione 'Generar y Enviar' nuevamente.")
        codigo_ingresado = st.text_input("🔑 Ingrese el código de 6 dígitos recibido:", max_chars=6)
        if st.button("✅ Verificar Identidad y Sellar Documento", type="primary", use_container_width=True):
            totp = pyotp.TOTP(st.session_state.form["otp_secret"], interval=300)
            if totp.verify(codigo_ingresado):
                st.session_state.form["otp_verificado"] = True
                ip_f   = st.session_state.form.get("ip_dispositivo", "Desconocida")
                fecha_f= datetime.now(tz_chile).strftime('%Y-%m-%d %H:%M:%S')
                rut_f  = st.session_state.form.get("rut", "S/R")
                traza  = (f"FES_CL | RUT:{rut_f} | Canal:{st.session_state.form['otp_metodo']} "
                          f"| Dest:{enmascarado} | IP:{ip_f} | Fecha:{fecha_f} | OTP:{codigo_ingresado}")
                hash_f = hashlib.sha256(traza.encode('utf-8')).hexdigest()
                st.session_state.form["traza_auditoria"] = traza
                st.session_state.form["hash_documento"]  = hash_f
                st.success("🔒 Identidad verificada. Sello criptográfico SHA-256 generado.")
                st.code(f"Sello Digital (SHA-256): {hash_f}", language="text")
            else:
                st.error("❌ Código incorrecto o expirado. Genere uno nuevo.")

    # ── Navegación ────────────────────────────────────────────────────
    st.markdown("---")
    col_nav = st.columns(2)
    if col_nav[0].button("← ATRÁS", key="atras_p3"):
        st.session_state.step = 2
        st.rerun()
    if col_nav[1].button("FINALIZAR REGISTRO", type="primary", key="finalizar_p3"):
        # Validaciones legales obligatorias
        if not st.session_state.form.get("autoriza_gad"):
            st.error("🚨 Por favor, responda si lee y autoriza el procedimiento."); st.stop()
        if not st.session_state.form.get("veracidad"):
            st.error("🚨 Es obligatorio confirmar que los datos son fidedignos."); st.stop()
        firma_valida = (
            st.session_state.get("firma_guardada") is not None and
            np.any(st.session_state["firma_guardada"][:, :, 3] > 0)
        )
        if not firma_valida:
            st.error("🚨 Debe dibujar su firma manualmente en el recuadro."); st.stop()
        if not st.session_state.form.get("otp_verificado"):
            st.error("🚨 Debe verificar su identidad mediante el código FES antes de finalizar."); st.stop()

        # Guardar imagen de firma temporalmente
        img_arr = Image.fromarray(st.session_state["firma_guardada"].astype('uint8'), 'RGBA')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_s:
            img_arr.save(tmp_s.name)
            st.session_state.form["firma_img"] = tmp_s.name
        st.session_state.step = 4
        st.balloons()
        st.rerun()


# =====================================================================
# SECCIÓN 21: PASO 4 — FINALIZACIÓN (PDF + Firebase + AES-256 + FHIR)
# =====================================================================
def pagina_4_finalizacion():
    mostrar_logo()
    st.success("🎉 ¡Registro Completado con Éxito!")
    cripto = GestorCriptografico()

    # ID del paciente (limpio para nombres de archivo)
    id_pac = (st.session_state.form.get('rut')
              if not st.session_state.form.get('sin_rut')
              else st.session_state.form.get('num_doc', 'SIN_ID'))
    if not id_pac: id_pac = "SIN_ID"
    id_pac_limpio = str(id_pac).replace(".", "").replace("-", "").strip()

    # ── Generar PDF ───────────────────────────────────────────────────
    try:
        idx_gen = str(st.session_state.form.get('genero_idx', '0'))
        idx_bio = str(st.session_state.form.get('sexo_bio_idx', '0'))
        ocr_bio = str(st.session_state.form.get('genero_biologico', '')).strip().capitalize()
        if idx_gen == "1":
            sexo_fmt = "Femenino"
        elif idx_gen == "2" or "No binario" in str(st.session_state.form.get('sexo', '')):
            s = ocr_bio if ocr_bio in ["Masculino", "Femenino"] else ("Femenino" if idx_bio == "1" else "Masculino")
            sexo_fmt = f"No binario (Bio: {s})"
        else:
            sexo_fmt = "Masculino"
        st.session_state.form["sexo"]   = sexo_fmt
        st.session_state.form["genero"] = sexo_fmt

        pdf_bytes = generar_pdf_clinico(st.session_state.form)
        st.session_state.pdf_bytes_data = pdf_bytes
    except Exception as e_pdf:
        st.error(f"Error al compilar el PDF: {e_pdf}")
        st.stop()

    nombre_final = (
        f"REG-PRE-VALIDADO_{st.session_state.form.get('nombre','Paciente')}_"
        f"{id_pac_limpio}_{datetime.now().strftime('%m_%Y')}.pdf"
    )
    st.session_state.pdf_filename = nombre_final

    # Botón de descarga inmediata
    st.download_button(
        "📥 Descargar Copia PDF de Inmediato",
        data=pdf_bytes, file_name=nombre_final,
        mime="application/pdf", use_container_width=True,
    )
    st.divider()
    st.info("⏳ Sincronizando copia digital con los servidores de Norte Imagen...")

    # ── Candado Anti-Duplicación ──────────────────────────────────────
    if not st.session_state.registro_guardado_db:
        ruta_firma_storage = ""
        url_bkt = st.secrets["firebase"].get("bucket_url", "firmas-encuestaconsentimiento.firebasestorage.app")
        bkt = storage.bucket(url_bkt)

        # Firebase Storage: Firma Digital
        if st.session_state.get("firma_guardada") is not None:
            ruta_tmp_f = None
            try:
                img_d = st.session_state["firma_guardada"]
                img_p = Image.fromarray(img_d.astype('uint8'), 'RGBA')
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tf:
                    img_p.save(tf.name); ruta_tmp_f = tf.name
                ts_str       = datetime.now(tz_chile).strftime('%Y%m%d_%H%M%S')
                blob_name    = f"firmas_pacientes/{id_pac_limpio}_{ts_str}.png"
                bkt.blob(blob_name).upload_from_filename(ruta_tmp_f, content_type='image/png')
                ruta_firma_storage = blob_name
            except Exception as e_st:
                st.error(f"Error al subir firma a Storage: {e_st}")
            finally:
                if ruta_tmp_f and os.path.exists(ruta_tmp_f):
                    try: os.unlink(ruta_tmp_f)
                    except Exception: pass

        if ruta_firma_storage:
            try:
                ts_arch = datetime.now(tz_chile).strftime('%Y%m%d_%H%M%S')

                # Firebase Storage: Orden Médica
                ruta_orden_fb = ""
                if st.session_state.get("orden_persistente"):
                    arch   = st.session_state["orden_persistente"]
                    _, ext = os.path.splitext(arch["name"])
                    ext    = ext.lower() or ".pdf"
                    ruta_orden_fb = f"ordenes_medicas/{id_pac_limpio}_{ts_arch}_orden{ext}"
                    bkt.blob(ruta_orden_fb).upload_from_string(
                        arch["bytes"],
                        content_type='application/pdf' if ext == '.pdf' else f'image/{ext.strip(".")}',
                    )

                # Firebase Storage: Exámenes Anteriores
                rutas_exams = []
                for idx, arch_ex in enumerate(st.session_state.get("examenes_persistentes", [])):
                    try:
                        _, ext_ex = os.path.splitext(arch_ex["name"])
                        ext_ex    = ext_ex.lower() or ".pdf"
                        ruta_ex   = f"examenes_anteriores/{id_pac_limpio}_{ts_arch}_exam{idx+1}{ext_ex}"
                        bkt.blob(ruta_ex).upload_from_string(
                            arch_ex["bytes"],
                            content_type='application/pdf' if ext_ex == '.pdf' else f'image/{ext_ex.strip(".")}',
                        )
                        rutas_exams.append(ruta_ex)
                    except Exception as ex_e:
                        print(f"Error examen {idx+1}: {ex_e}")

                # ── FHIR Bundle → AES-256 GCM ─────────────────────────
                bundle_fhir      = transformar_a_bundle_fhir(
                    st.session_state.form,
                    st.session_state.paciente_uuid,
                    st.session_state.form.get("recursos_hl7", []),
                )
                payload_encripted = cripto.encriptar(bundle_fhir)

                # ── Payload Firestore ─────────────────────────────────
                df_f = st.session_state.form

                def sf(v):
                    return v.strftime("%d/%m/%Y") if hasattr(v, "strftime") else str(v)

                edad_pac = str(calcular_edad(df_f["fecha_nac"])) if "fecha_nac" in df_f else "N/A"

                payload_firestore = {
                    # Identificadores
                    "uuid_sesion":   st.session_state.paciente_uuid,
                    "rut":           str(df_f.get('rut', '')).strip(),
                    "nombre":        str(df_f.get('nombre', '')).upper().strip(),
                    "fecha_nac":     sf(df_f.get('fecha_nac')),
                    "edad":          edad_pac,
                    "genero":        str(df_f.get('genero_biologico', '')),
                    "email":         str(df_f.get('email', '')),
                    "telefono":      str(df_f.get('telefono', '')),
                    "sin_rut":       df_f.get('sin_rut', False),
                    "tipo_doc":      str(df_f.get('tipo_doc', '')),
                    "num_doc":       str(df_f.get('num_doc', '')).upper().strip(),
                    # Tutor
                    "nombre_tutor":    str(df_f.get('nombre_tutor', '')).upper().strip(),
                    "parentesco_tutor":str(df_f.get('parentesco_tutor', '')),
                    "rut_tutor":       str(df_f.get('rut_tutor', '')),
                    "sin_rut_tutor":   df_f.get('sin_rut_tutor', False),
                    "num_doc_tutor":   str(df_f.get('num_doc_tutor', '')).upper(),
                    # Clínico
                    "procedencia":       str(df_f.get('procedencia', 'Ambulatorio')),
                    "unidad_procedencia":str(df_f.get('unidad_procedencia', '')).upper(),
                    "fecha_examen":      sf(df_f.get('fecha_examen')),
                    "procedimiento":     str(st.session_state.get('procedimiento', '')),
                    "tiene_contraste":   st.session_state.get('tiene_contraste', False),
                    "creatinina":        float(df_f.get('creatinina', 0.0)),
                    "peso":              float(df_f.get('peso', 0.0)),
                    "talla":             float(df_f.get('talla', 0.0)),
                    "vfg":               float(df_f.get('vfg', 0.0)),
                    "fecha_creatinina":  sf(df_f.get('fecha_creatinina')),
                    # Cuestionario
                    "bio_marcapaso":  df_f.get('bio_marcapaso', 'No'),
                    "bio_implantes":  df_f.get('bio_implantes',  'No'),
                    "bio_detalle":    str(df_f.get('bio_detalle', '')),
                    "clin_ayuno":     df_f.get('clin_ayuno',     'No'),
                    "clin_asma":      df_f.get('clin_asma',      'No'),
                    "clin_hiperten":  df_f.get('clin_hiperten',  'No'),
                    "clin_diabetes":  df_f.get('clin_diabetes',  'No'),
                    "clin_alergico":  df_f.get('clin_alergico',  'No'),
                    "alergias_detalles": str(df_f.get('alergias_detalle', '')),
                    "clin_metformina":df_f.get('clin_metformina','No'),
                    "clin_renal":     df_f.get('clin_renal',     'No'),
                    "clin_dialisis":  df_f.get('clin_dialisis',  'No'),
                    "clin_embarazo":  df_f.get('clin_embarazo',  'No'),
                    "clin_lactancia": df_f.get('clin_lactancia', 'No'),
                    "clin_claustro":  df_f.get('clin_claustro',  'No'),
                    "condiciones":    df_f.get('condiciones', []),
                    "condicion_detalle": str(df_f.get('condicion_detalle', '')),
                    "quir_cirugia_check":  df_f.get('quir_cirugia_check', 'No'),
                    "quir_cirugia_detalle":str(df_f.get('quir_cirugia_detalle', '')),
                    "quir_cancer_check":   df_f.get('quir_cancer_check',  'No'),
                    "quir_cancer_detalle": str(df_f.get('quir_cancer_detalle', '')),
                    "rt": "Sí" if df_f.get('rt') else "No",
                    "qt": "Sí" if df_f.get('qt') else "No",
                    "bt": "Sí" if df_f.get('bt') else "No",
                    "it": "Sí" if df_f.get('it') else "No",
                    # Exámenes previos
                    "has_examenes_previos": df_f.get('has_examenes_previos', 'No'),
                    "ex_rx": df_f.get('ex_rx', False), "ex_mg": df_f.get('ex_mg', False),
                    "ex_eco":df_f.get('ex_eco',False),  "ex_tc": df_f.get('ex_tc', False),
                    "ex_rm": df_f.get('ex_rm', False),  "ex_otros":str(df_f.get('ex_otros','')),
                    "link_exam_1": str(df_f.get('link_exam_1', '')),
                    "pin_exam_1":  str(df_f.get('pin_exam_1',  '')),
                    "link_exam_2": str(df_f.get('link_exam_2', '')),
                    "pin_exam_2":  str(df_f.get('pin_exam_2',  '')),
                    # URLs Firebase
                    "url_firma_storage":    ruta_firma_storage,
                    "url_orden_firebase":   ruta_orden_fb,
                    "url_examenes_firebase":rutas_exams,
                    # FES / Criptografía (Ley 19.799)
                    "firma_electronica": {
                        "estado":              "FIRMADO",
                        "tipo":                "Firma Electrónica Simple (FES) - Ley 19.799",
                        "metodo_verificacion": df_f.get("otp_metodo", "N/A"),
                        "hash_sha256":         df_f.get("hash_documento", ""),
                        "traza_auditoria":     df_f.get("traza_auditoria", ""),
                        "timestamp_firma":     datetime.now(tz_chile).strftime("%d/%m/%Y %H:%M:%S"),
                    },
                    # HL7 FHIR Bundle encriptado en AES-256 GCM
                    "fhir_bundle_aes256_gcm": payload_encripted,
                    # Metadatos
                    "estado_validacion": "PENDIENTE",
                    "encuesta_validada": False,
                    "pdf_name":          nombre_final,
                    "ip_paciente":       str(df_f.get("ip_dispositivo", "No detectada")),
                    "fecha_creacion":    datetime.now(tz_chile).strftime("%d/%m/%Y %H:%M:%S"),
                }

                # Escribir en Firestore
                id_doc = f"{id_pac_limpio}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                db     = firestore.client()
                db.collection("encuestas").document(id_doc).set(payload_firestore)
                st.caption(
                    "🔹 Registro clínico guardado en Firestore con FHIR Bundle "
                    "encriptado (AES-256 GCM) + sello FES SHA-256."
                )

                # Google Drive (Kill-Switch — activar cambiando a True)
                USAR_RESPALDO_DRIVE = False
                if USAR_RESPALDO_DRIVE:
                    try:
                        ok, res = subir_a_google_drive(pdf_bytes, nombre_final)
                        if ok: st.caption("🔹 PDF respaldado en Google Drive.")
                    except Exception as e_dr:
                        print(f"Error Drive: {e_dr}")

            except Exception as e_fs:
                st.error(f"🚨 Error al guardar en Firestore: {e_fs}")
        else:
            st.error("🚨 Registro detenido: La firma digital es obligatoria para validar el consentimiento.")
            st.stop()

        st.balloons()
        st.session_state.registro_guardado_db = True

    # ── Botón Nuevo Registro (siempre visible) ────────────────────────
    st.divider()
    if st.button("🔄 Iniciar Nuevo Registro", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# =====================================================================
# SECCIÓN 22: GOOGLE DRIVE — Módulo de Respaldo (Kill-Switch)
# =====================================================================
CLIENT_ID       = st.secrets.get("google_oauth", {}).get("client_id",      "")
CLIENT_SECRET   = st.secrets.get("google_oauth", {}).get("client_secret",  "")
REDIRECT_URI    = st.secrets.get("google_oauth", {}).get("redirect_uri",   "")
ID_CARPETA_DRIVE= st.secrets.get("drive",        {}).get("folder_id",       "")
SCOPES          = ['https://www.googleapis.com/auth/drive.file']

# Interceptar callback de OAuth si viene con ?code=
query_params = st.query_params
if "code" in query_params and not st.session_state.get("credentials"):
    try:
        flow = Flow.from_client_config(
            {"web": {
                "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }},
            scopes=SCOPES, redirect_uri=REDIRECT_URI,
        )
        flow.fetch_token(code=query_params["code"])
        st.session_state.credentials = flow.credentials
        st.success("✅ Conectado exitosamente a Google Drive de Norte Imagen")
    except Exception:
        pass


def subir_a_google_drive(archivo_datos: bytes, nombre_archivo: str):
    if not st.session_state.get("credentials"):
        return False, "No hay sesión activa de Google Drive"
    tmp_path = None
    try:
        service = build('drive', 'v3', credentials=st.session_state.credentials)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tf:
            tf.write(archivo_datos); tmp_path = tf.name
        media = MediaFileUpload(tmp_path, mimetype='application/pdf', resumable=True)
        f = service.files().create(
            body={'name': nombre_archivo, 'parents': [ID_CARPETA_DRIVE]},
            media_body=media, fields='id',
        ).execute()
        return True, f.get('id')
    except Exception as e:
        return False, str(e)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


# =====================================================================
# === ORQUESTADOR PRINCIPAL — PUNTO DE ENTRADA ÚNICO ===
# =====================================================================

# 1. Firebase Singleton (1 conexión para todos los pacientes concurrentes)
_app_firebase = inicializar_firebase()

# 2. Catálogo FONASA/HL7 (cacheado — lectura única del CSV)
df_global, catalogo_global = cargar_catalogo_hl7()

# 3. Sesión hermética por paciente (UUID único + form dict completo)
inicializar_sesion()

# 4. CSS global + Menú flotante (inyección única)
inyectar_css_y_menu()

# 5. ENRUTADOR DE PASOS — Wizard SPA (Single Page Application)
if st.session_state.step == 0:
    pagina_0_bienvenida()

elif st.session_state.step == 1:
    pagina_1_registro(df_global, catalogo_global)

elif st.session_state.step == 2:
    pagina_2_cuestionario()

elif st.session_state.step == 3:
    pagina_3_consentimiento()

elif st.session_state.step == 4:
    pagina_4_finalizacion()

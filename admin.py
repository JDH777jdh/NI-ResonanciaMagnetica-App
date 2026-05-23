# =====================================================================
# 1. PRIMERO: TODAS LAS IMPORTACIONES DE LIBRERÍAS
# =====================================================================
import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import firebase_admin
from firebase_admin import credentials, firestore, storage
import tempfile
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import pytz
import json
import re
import time

# =====================================================================
# MOTOR CLÍNICO UNIVERSAL VFG (Integración Segura)
# =====================================================================
from datetime import date, datetime

def calcular_vfg_universal(fecha_nacimiento, sexo_bio, creatinina, talla_cm, peso_kg):
    """Calcula la VFG y blinda el error de fechas de Firestore."""
    if creatinina <= 0:
        return 0.0, "Parámetros incompletos"

    hoy = date.today()
    # Blindaje del Punto Ciego: Parseo estricto de fecha
    if isinstance(fecha_nacimiento, str):
        try:
            fecha_nac_real = datetime.strptime(fecha_nacimiento[:10], '%d/%m/%Y').date()
        except ValueError:
            try:
                fecha_nac_real = datetime.strptime(fecha_nacimiento[:10], '%Y-%m-%d').date()
            except ValueError:
                fecha_nac_real = hoy
    elif isinstance(fecha_nacimiento, datetime):
        fecha_nac_real = fecha_nacimiento.date()
    else:
        fecha_nac_real = fecha_nacimiento

    edad_dias = (hoy - fecha_nac_real).days
    edad_meses = edad_dias / 30.4
    edad_anos = edad_dias / 365.25

    vfg = 0.0
    formula_usada = ""

    # 1. LACTANTES (< 2 años) - Schwartz Clásica
    if edad_anos < 2:
        formula_usada = "Schwartz Clásica (Maduración)"
        if edad_dias <= 28:
            k = 0.33 if edad_dias < 7 else 0.45
        else:
            k = 0.45 if edad_meses <= 12 else 0.55
        if talla_cm > 0:
            vfg = (k * talla_cm) / creatinina

    # 2. PEDIÁTRICOS (2 a 17 años) - Schwartz Bedside 2009
    elif edad_anos < 18:
        formula_usada = "Schwartz Bedside 2009"
        if talla_cm > 0:
            vfg = (0.413 * talla_cm) / creatinina

    # 3. ADULTOS (>= 18 años) - Cockcroft-Gault (Peso Activo)
    else:
        formula_usada = "Cockcroft-Gault"
        if peso_kg > 0:
            es_mujer = str(sexo_bio).lower() in ['femenino', 'f', 'mujer', 'fem']
            factor = 0.85 if es_mujer else 1.0
            vfg = (((140 - int(edad_anos)) * peso_kg) / (72 * creatinina)) * factor

    return round(vfg, 2), formula_usada


def obtener_alerta_vfg(vfg_valor, fecha_nacimiento):
    """Evalúa el riesgo clínico y retorna (Mensaje, Color_HEX_Web, Color_RGB_PDF)"""
    if vfg_valor <= 0:
        return "Cálculo pendiente", "#888888", (136, 136, 136)

    hoy = date.today()
    if isinstance(fecha_nacimiento, str):
        try:
            fecha_nac_real = datetime.strptime(fecha_nacimiento[:10], '%d/%m/%Y').date()
        except:
            fecha_nac_real = hoy
    elif isinstance(fecha_nacimiento, datetime):
        fecha_nac_real = fecha_nacimiento.date()
    else:
        fecha_nac_real = fecha_nacimiento

    edad_dias = (hoy - fecha_nac_real).days
    edad_meses = edad_dias / 30.4
    edad_anos = edad_dias / 365.25

    # 1. LACTANTES (< 2 AÑOS)
    if edad_anos < 2:
        if edad_meses <= 0.25: min_norm, max_norm = 15, 30
        elif edad_meses <= 1: min_norm, max_norm = 30, 50
        elif edad_meses <= 2: min_norm, max_norm = 40, 65
        elif edad_meses <= 4: min_norm, max_norm = 55, 85
        elif edad_meses <= 12: min_norm, max_norm = 70, 110
        else: min_norm, max_norm = 85, 125

        if vfg_valor < (min_norm * 0.7):
            return "ALTO RIESGO: VFG Crítica", "#FF0000", (255, 0, 0)
        elif vfg_valor < min_norm:
            return "RIESGO INTERMEDIO: Retraso maduración", "#FFCC00", (184, 134, 11)
        elif vfg_valor <= max_norm:
            return "SIN RIESGO: VFG Adecuada", "#28A745", (34, 139, 34)
        else:
            return "REVISAR: Hiperfiltración", "#007BFF", (0, 123, 255)

    # 2. MAYORES Y ADULTOS (>= 2 AÑOS)
    else:
        if vfg_valor <= 30.0:
            return "ALTO RIESGO para la administración de medio de contraste", "#FF0000", (255, 0, 0)
        elif vfg_valor <= 59.0:
            return "RIESGO INTERMEDIO para la administración de medio de contraste", "#FFCC00", (184, 134, 11)
        else:
            return "SIN RIESGO para la administración de medio de contraste", "#28A745", (34, 139, 34)

def validacion_str(valor):
    """Función auxiliar para normalizar valores en PDF."""
    if valor is None: return "N/A"
    if isinstance(valor, bool): return "Sí" if valor else "No"
    return str(valor)

def calcular_edad_exacta(fecha_nacimiento):
    """Calcula la edad exacta en años, meses o días de forma segura."""
    if not fecha_nacimiento or fecha_nacimiento == 'N/A':
        return "N/A"
        
    hoy = date.today()
    
    # 1. Parseo estricto de la fecha (blindado contra formatos raros)
    if isinstance(fecha_nacimiento, str):
        try:
            fecha_nac_real = datetime.strptime(fecha_nacimiento[:10], '%d/%m/%Y').date()
        except ValueError:
            try:
                fecha_nac_real = datetime.strptime(fecha_nacimiento[:10], '%Y-%m-%d').date()
            except ValueError:
                return "N/A"
    elif hasattr(fecha_nacimiento, 'date'):
        fecha_nac_real = fecha_nacimiento.date()
    else:
        fecha_nac_real = fecha_nacimiento
        
    if not isinstance(fecha_nac_real, date):
        return "N/A"
        
    # 2. Cálculo matemático exacto
    diferencia = relativedelta(hoy, fecha_nac_real)
    
    # 3. Formateo inteligente para el PDF
    if diferencia.years > 0:
        return f"{diferencia.years} años"
    elif diferencia.months > 0:
        return f"{diferencia.months} meses"
    else:
        return f"{max(0, diferencia.days)} días"

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Panel de Validación Técnica - RM", layout="wide")
# Definición de Zona Horaria Chilena para el Panel Profesional
tz_chile = pytz.timezone('America/Santiago')

# --- 1. INICIALIZACIÓN SEGURA DE ESTADO ---
if "selector_refresh_key" not in st.session_state:
    st.session_state.selector_refresh_key = 0
if 'paciente_seleccionado' not in st.session_state:
    st.session_state.paciente_seleccionado = None
if 'doc_completo' not in st.session_state:
    st.session_state.doc_completo = {}

# === INICIALIZACIÓN SEGURA DE FIREBASE ADMIN SDK ===
firebase_inicializado = False

try:
    # Intenta obtener la app si ya existe (Evita el error de doble conexión)
    firebase_admin.get_app()
    firebase_inicializado = True
    url_bucket = st.secrets["firebase"].get("bucket_url", "firmas-encuestaconsentimiento.firebasestorage.app")
except ValueError:
    # Si no existe, entonces la inicializa por primera vez
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
        st.error(f"🚨 Error crítico al inicializar Firebase en Panel TM: {e}")
        st.stop()

# --- CONECTORES GLOBALES FINALES ---
if firebase_inicializado:
    db = firestore.client()
    bucket = storage.bucket(url_bucket) if url_bucket else storage.bucket()

# --- HEADER DEL PANEL ---

# --- LOGO CENTRADO AL INICIO ---
try:
    col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
    with col_logo2:
        st.image("logoNI.png", width=220)
except Exception:
    pass  # Silencioso si no encuentra el logo para no romper la pantalla

st.title("🏥 Servicio de Resonancia Magnética")
st.subheader("👨‍⚕️ Panel de Control y Validación de Seguridad (Tecnólogo Médico)")
st.divider()

# =============================================================================
# --- SISTEMA DE AUTENTICACIÓN INDIVIDUALIZADO (Cero Suplantación) ---
# =============================================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "current_user" not in st.session_state:
    st.session_state.current_user = None

if not st.session_state.authenticated or st.session_state.current_user is None:
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.warning("🔒 **Acceso Restringido.**\n\nIngrese sus credenciales de Tecnólogo Médico.")
    col1, col2 = st.columns([1, 2])
    with col1:
        pin_ingresado = st.text_input("Ingrese su Clave Personal (PIN):", type="password")
        if st.button("Ingresar al Sistema"):
            usuarios = st.secrets.get("usuarios_rm", {})
            if pin_ingresado in usuarios:
                st.session_state.authenticated = True
                st.session_state.current_user = usuarios[pin_ingresado]
                st.success(f"🔓 Bienvenido(a), TM {st.session_state.current_user['nombre']}")
                st.rerun()
            else:
                st.error("🔑 Clave incorrecta o profesional no autorizado.")
    st.stop()

# --- BOTÓN PARA CERRAR SESIÓN EN BARRA LATERAL ---
st.sidebar.markdown(f"**Usuario:**\nTM {st.session_state.current_user['nombre']}")

# Texto extendido en dos líneas para una visualización elegante
st.sidebar.markdown(
    f"**Registro de Prestadores Individuales de la**\n"
    f"**Superintendencia de Salud:**\n"
    f"{st.session_state.current_user['sis']}"
)

st.sidebar.markdown("### ⚙️ Estado: Operativo 🟢")

# Espacio divisorio y sección del Portal de Pacientes
st.sidebar.markdown("---")
st.sidebar.markdown("### 📱 Portal Pacientes\n*Encuesta y Consentimiento*")

# Carga segura del QR desde la raíz de tu repositorio de GitHub
try:
    st.sidebar.image("QRPacientes.png", caption="Escanee para acceder al formulario", use_container_width=True)
except Exception:
    # Plan de contingencia por si la imagen se encuentra en una subcarpeta
    try:
        st.sidebar.image("images/QRPacientes.png", caption="Escanee para acceder al formulario", use_container_width=True)
    except Exception as e:
        st.sidebar.error("⚠️ Archivo 'QRPacientes.png' no detectado en el repositorio.")

# --- ACCESOS DIRECTOS INSTITUCIONALES ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔗 Enlaces Clínicos")

# st.link_button crea un botón elegante que abre el link en una pestaña nueva
st.sidebar.link_button(
    "🖥️🩻 Ingresar a RIS/PACS (Francisco Bilbao)", 
    "https://risnimag1.irad.cl/RISWEB/Timeout.aspx", # Reemplaza con tu link real
    use_container_width=True
)

st.sidebar.link_button(
    "🖥️🩻 Ingresar a RIS/PACS (Arturo Fernández)", 
    "https://risnimag2.irad.cl/RISWEB/Timeout.aspx", # Reemplaza con tu link real
    use_container_width=True
)

st.sidebar.link_button(
    "📋📊 Portal de Resultados Paciente", 
    "https://risnimag1.irad.cl/PPAC/", # Reemplaza con tu link real
    use_container_width=True
)

# Botón de cierre de sesión al final
if st.sidebar.button("🔒 Cerrar Sesión", use_container_width=True):
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.rerun()


# =============================================================================
# ⏱️ MOTOR DE BANDEJA DE ENTRADA AUTO-ASÍNCRONA (Cada 60 Segundos)
# =============================================================================
@st.fragment(run_every=60)
def filtrar_y_sincronizar_pacientes():
    # 1. UI de Cabecera
    col_tit, col_btn = st.columns([3, 1])

    with col_tit:
        st.markdown("### 📥 Bandeja de Entrada: Pacientes en espera de validación")

    with col_btn:
        if st.button("🔄 Actualizar", use_container_width=True, key="btn_manual_refresh"):
            st.rerun()
            
        if st.button("🧹 Limpiar Bandeja", use_container_width=True, help="Elimina pacientes ya validados", key="btn_limpiar_lista"):
            # AQUÍ ESTÁ EL CÓDIGO REAL (Así Python ya no ve un 'if' vacío)
            st.session_state.paciente_seleccionado = None
            st.session_state.doc_completo = {}
            # Borrar de Firestore los ya validados
            validados = db.collection("encuestas").where("estado_validacion", "==", "VALIDADO").stream()
            for doc in validados:
                db.collection("encuestas").document(doc.id).delete()
            st.rerun()
            
    # Usamos la zona horaria definida globalmente (tz_chile)
    hora_sincro = datetime.now(tz_chile).strftime('%H:%M:%S')
    st.caption(f"✨ Conectado a Firebase Firestore • Último auto-refresco: **{hora_sincro}**")

    # 2. Consulta a Firebase
    try:
        docs_ref = db.collection("encuestas").where("estado_validacion", "==", "PENDIENTE").stream()
        
        listado_pacientes = []
        for doc in docs_ref:
            data = doc.to_dict()
            
            # --- Procesamiento Seguro de Fecha ---
            fecha_raw = data.get("fecha") or data.get("fecha_examen") or data.get("Fecha")
            
            if fecha_raw:
                # Si es un objeto Timestamp de Firebase o datetime de Python
                if hasattr(fecha_raw, 'astimezone'):
                    fecha_dt = fecha_raw.astimezone(tz_chile)
                    fecha_str = fecha_dt.strftime('%d/%m/%y')
                else:
                    # Si viene como texto (ej: "2026-05-20"), lo convertimos a formato corto
                    try:
                        fecha_str = datetime.strptime(str(fecha_raw)[:10], '%Y-%m-%d').strftime('%d/%m/%y')
                    except:
                        fecha_str = str(fecha_raw)
            else:
                # RESPALDO ABSOLUTO: Si el campo no existe, usa la fecha de creación del documento
                fecha_str = doc.create_time.astimezone(tz_chile).strftime('%d/%m/%y')
            
            # Agregamos los paréntesis solicitados al formato (dd/mm/aa)
            fecha_final = f"({fecha_str})"
            
            listado_pacientes.append({
                "Fecha de examen": fecha_final,
                "Nombre del paciente": data.get("nombre", "Sin Nombre"),
                "RUT paciente": data.get("rut", "S/R"),
                "Procedimiento": data.get("procedimiento", "No especificado"),
                "ID_Documento": doc.id
            })
            
    except Exception as e:
        st.error(f"🚨 Error de conexión: {e}")
        listado_pacientes = []

    # 3. Control de flujo: Si no hay pacientes, nos detenemos aquí
    if not listado_pacientes:
        st.info("✅ No hay pacientes pendientes de validación.")
        st.session_state.paciente_seleccionado = None
        st.session_state.doc_completo = {}
        st.stop()  # IMPORTANTE: Detiene la ejecución aquí mismo y evita errores abajo

    # 4. Procesamiento de datos (Solo se ejecuta si hay pacientes)
    df_pacientes = pd.DataFrame(listado_pacientes)
    options_list = list(df_pacientes["ID_Documento"])

    # Selector de pacientes
    paciente_seleccionado = st.selectbox(
        "🔎 Seleccione el paciente para revisar antecedentes:",
        options=options_list,
        format_func=lambda x: f"📅 {df_pacientes[df_pacientes['ID_Documento']==x]['Fecha de examen'].values[0]} | 👤 {df_pacientes[df_pacientes['ID_Documento']==x]['Nombre del paciente'].values[0]} | 🔹 RUT: {df_pacientes[df_pacientes['ID_Documento']==x]['RUT paciente'].values[0]} | 🔍 {df_pacientes[df_pacientes['ID_Documento']==x]['Procedimiento'].values[0]}",
        key="selector_pacientes_dinamico"
    )

    # 5. Actualizar sesión al cambiar el selector
    if paciente_seleccionado != st.session_state.get('paciente_seleccionado'):
        st.session_state.paciente_seleccionado = paciente_seleccionado
        doc_data = db.collection("encuestas").document(paciente_seleccionado).get().to_dict()
        st.session_state.doc_completo = doc_data if doc_data else {}
        st.rerun() # Recargamos para que el contenido se actualice

    # 6. RENDERIZADO: Mostrar la ficha del paciente seleccionado
    datos_doc = st.session_state.get('doc_completo') or {}
    
    

# --- LLAMADO ---
filtrar_y_sincronizar_pacientes()

# =============================================================================
# --- DESPLIEGUE DEL FORMULARIO CLÍNICO ACTIVO ---
# =============================================================================
# El formulario completo se despliega de manera segura acoplándose al motor asíncrono

if st.session_state.get("doc_completo") is not None:
    paciente_seleccionado = st.session_state.paciente_seleccionado
    doc_completo = st.session_state.doc_completo
    
    st.divider()

    # =========================================================================
    # 🩹 MICRO-CIRUGÍA 1 REPARADA: EXTRACCIÓN INTELIGENTE Y OMNIDIRECCIONAL
    # =========================================================================
    datos_doc = doc_completo
    	
    # Detectar automáticamente si los datos vienen planos o anidados en un sub-mapa 'form'
    form_interno = datos_doc.get('form', datos_doc.get('encuesta', datos_doc))
    if not isinstance(form_interno, dict):
        form_interno = datos_doc

    # 👤 Demográficos Básicos
    paciente_nombre = datos_doc.get('nombre', form_interno.get('nombre', 'No registrado'))
    paciente_rut = datos_doc.get('rut', form_interno.get('rut', 'No registrado'))
    paciente_fnac = datos_doc.get('fecha_nac', datos_doc.get('fecha_nacimiento', form_interno.get('fecha_nac', 'N/A')))
    
    if hasattr(paciente_fnac, 'strftime'):
        paciente_fnac = paciente_fnac.strftime('%d/%m/%Y')
        
    try:
        edad_int = int(datos_doc.get('edad', form_interno.get('edad', 0)))
        paciente_edad = f"{edad_int} años"
    except:
        edad_int = 0
        paciente_edad = str(datos_doc.get('edad', form_interno.get('edad', 'N/A')))

    # 👨‍👦 Datos del Tutor
    if edad_int < 18:
        tutor_nombre = datos_doc.get('nombre_tutor', form_interno.get('nombre_tutor', 'No registrado'))
        tutor_rut = datos_doc.get('rut_tutor', form_interno.get('rut_tutor', 'No registrado'))
        datos_doc['tutor_nombre'] = tutor_nombre # INYECCIÓN
        datos_doc['tutor_rut'] = tutor_rut       # INYECCIÓN
    else:
        tutor_nombre = None
        tutor_rut = None

    # 🧲 Bioseguridad Real
    marcapasos = form_interno.get('marcapaso', form_interno.get('bio_marcapaso', datos_doc.get('marcapaso', 'No')))
    implantes = form_interno.get('implantes', form_interno.get('bio_implantes', datos_doc.get('implantes', 'No')))
    det_bio = form_interno.get('bio_detalle', form_interno.get('detalle_bioseguridad', datos_doc.get('bio_detalle', ''))).strip()

    nota_marcapaso = ""
    nota_implante = ""

    if str(marcapasos).strip().upper() in ["SI", "SÍ"]:
        nota_marcapaso = "Se deberá evaluar compatibilidad si es que no está contraindicado para su examen."
    if str(implantes).strip().upper() in ["SI", "SÍ"]:
        nota_implante = "Se deberá evaluar su compatibilidad con la zona de estudio."
    
    datos_doc['nota_marcapaso'] = nota_marcapaso # INYECCIÓN
    datos_doc['nota_implante'] = nota_implante   # INYECCIÓN

    # 🚨 Triaje de Riesgos Clínicos
    clin_alergico = form_interno.get('alergico', form_interno.get('clin_alergico', 'No'))
    clin_dialisis = form_interno.get('dialisis', form_interno.get('clin_dialisis', 'No'))
    clin_renal = form_interno.get('renal', form_interno.get('clin_renal', 'No'))
    clin_embarazo = form_interno.get('embarazo', form_interno.get('clin_embarazo', 'No'))
    clin_claustro = form_interno.get('claustrofobia', form_interno.get('clin_claustro', 'No'))
    clin_lactancia = form_interno.get('lactancia', form_interno.get('clin_lactancia', 'No'))

    # Inicializar notas vacías
    nota_alergico = nota_dialisis = nota_renal = nota_embarazo = nota_claustro = nota_lactancia = ""

    if str(clin_alergico).strip().upper() in ["SI", "SÍ"]: nota_alergico = "Evaluar su relación al medio de contraste y necesidad de premedicación."
    if str(clin_dialisis).strip().upper() in ["SI", "SÍ"]: nota_dialisis = "No se debe inyectar medio de contraste basado en Gadolinio."
    if str(clin_renal).strip().upper() in ["SI", "SÍ"]: nota_renal = "Se debe considerar la VFG para la administración de medio de contraste."
    if str(clin_embarazo).strip().upper() in ["SI", "SÍ"]: nota_embarazo = "Precaución, paciente de alto cuidado."
    if str(clin_claustro).strip().upper() in ["SI", "SÍ"]: nota_claustro = "Puede requerir atención personalizada."
    if str(clin_lactancia).strip().upper() in ["SI", "SÍ"]: nota_lactancia = "Consultar si junto leche materna o cuenta con alguna adicional."
    # INYECCIÓN AL DICCIONARIO
    datos_doc.update({
        'nota_alergico': nota_alergico,
        'nota_dialisis': nota_dialisis,
        'nota_renal': nota_renal,
        'nota_embarazo': nota_embarazo,
        'nota_claustro': nota_claustro,
        'nota_lactancia': nota_lactancia
    })
    
    # 🧪 Parámetros Métricos y resto de variables...
    # Extracción y tipado forzado a float para evitar errores en el cálculo
    creatinina_val = form_interno.get('creatinina', datos_doc.get('creatinina', 'N/A'))
    peso_val = form_interno.get('peso', datos_doc.get('peso', 'N/A'))
    talla_val = form_interno.get('talla', datos_doc.get('talla', 0.0))
    
    # Variables de cálculo (seguras)
    talla_profesional = float(talla_val) if str(talla_val).replace('.','',1).isdigit() else 0.0
    peso_profesional = float(peso_val) if str(peso_val).replace('.','',1).isdigit() else 0.0
    creatinina_profesional = float(creatinina_val) if str(creatinina_val).replace('.','',1).isdigit() else 0.0
    
    # Resto de variables visuales
    vfg_valor = form_interno.get('vfg', datos_doc.get('vfg', 0.0))
    is_contraste_visual = datos_doc.get('tiene_contraste', form_interno.get('tiene_contraste', False)) in [True, "Sí", "SI", "si", "Si"]
    procedimiento_val_visual = datos_doc.get('procedimiento', form_interno.get('procedimiento', 'No especificado'))
    ip_cliente = datos_doc.get('ip_dispositivo', datos_doc.get('ip', form_interno.get('ip_dispositivo', form_interno.get('ip', 'No detectada'))))


st.title("🏥 Panel de Validación Profesional")


st.divider()

# --- 1. PREPARACIÓN DE DATOS (Soluciona el NameError) ---
# Intentamos obtener el documento de la sesión. Si no existe, usamos un dict vacío.
datos_doc = st.session_state.get('doc_completo', {})
# --- FUNCIÓN DE TRADUCCIÓN CLÍNICA NIVEL DIOS ---
def evaluar_si_no(valor):
    """Convierte respuestas 'Sí'/'No' de Firebase a booleanos reales (True/False)"""
    if isinstance(valor, bool):
        return valor
    return str(valor).strip().upper() in ["SI", "SÍ", "TRUE", "1", "YES"]


# =====================================================================
# 🟢 RENDERIZADO EN 2 COLUMNAS CON DISTRIBUCIÓN ESPECÍFICA (DATOS REALES)
# =====================================================================
# Extraemos el diccionario real del estado de la sesión
datos_doc = st.session_state.get('doc_completo', {})

with sub_c2:
                        # Alternancia dinámica si el paciente no posee RUT
                        if datos_doc.get('sin_rut'):
                            tipo_id_paciente = datos_doc.get('tipo_doc', 'Pasaporte')
                            id_paciente = datos_doc.get('num_doc', 'N/A')
                            st.write(f"**Documento ({tipo_id_paciente}):**\n{id_paciente}")
                        else:
                            st.write(f"**RUT:**\n{datos_doc.get('rut', 'N/A')}")
                            
                        st.write(f"**Teléfono:**\n{datos_doc.get('telefono', 'N/A')}")
                        st.write("** **\n** **")

                    # =====================================================================
                    # 📁 [NUEVO] VISOR DE DOCUMENTACIÓN MÉDICA DESDE GOOGLE DRIVE
                    # =====================================================================
                    st.markdown("📂 **Documentos Adjuntos (Google Drive)**")
                    
                    # Recuperamos los enlaces que app.py guardó en Firestore
                    url_orden = datos_doc.get("url_orden_drive")
                    urls_examenes = datos_doc.get("urls_examenes_drive", [])

                    col_docs1, col_docs2 = st.columns(2)
                    
                    with col_docs1:
                        if url_orden:
                            st.link_button("📄 Ver Orden Médica", url_orden, use_container_width=True)
                        else:
                            st.caption("⚠️ Sin Orden Médica en Drive")

                    with col_docs2:
                        if urls_examenes:
                            # Si hay múltiples exámenes, los mostramos en un menú desplegable limpio
                            with st.popover("🔍 Ver Exámenes Anteriores", use_container_width=True):
                                for idx, url_ex in enumerate(urls_examenes):
                                    st.link_button(f"📊 Examen Anterior {idx + 1}", url_ex, use_container_width=True)
                        else:
                            st.caption("ℹ️ Sin exámenes anteriores")

                    st.markdown("<br>", unsafe_allow_html=True)

                    # =====================================================================
                    # 🗑️ BOTÓN DE ACCIÓN RÁPIDA: ELIMINAR PACIENTE DE LA BANDEJA
                    # =====================================================================
                    if st.button("🗑️ Eliminar Paciente de la Bandeja", use_container_width=True, key="btn_eliminar_paciente_ficha"):
                        if paciente_seleccionado:
                            db.collection("encuestas").document(paciente_seleccionado).delete()
                            st.session_state.paciente_seleccionado = None
                            st.session_state.doc_completo = {}
                            st.toast("🔥 Paciente eliminado de la lista", icon="🗑️")
                            import time
                            time.sleep(0.5)
                            st.rerun()

                    # --- PROCEDIMIENTO ASIGNADO (Antes del Representante Legal) ---

        # --- PROCEDIMIENTO ASIGNADO (Antes del Representante Legal) ---
        st.markdown("---") 
        nombre_procedimiento = datos_doc.get('procedimiento', 'No especificado')
        st.markdown(f"**🔍 Examen / Procedimiento:**\n{nombre_procedimiento.upper()}")

        # Control Seguro para Menores de Edad
        try:
            edad_paciente = int(datos_doc.get('edad', 0))
        except (ValueError, TypeError):
            edad_paciente = 0
            
        if 0 < edad_paciente < 18:
            st.warning("⚠️ **Paciente Menor de Edad - Representante Legal:**")
            
            # Creamos un sub-bloque de columnas para alinear los datos del tutor perfectamente abajo
            sub_rep1, sub_rep2 = st.columns(2)
            with sub_rep1:
                nombre_t = datos_doc.get('nombre_tutor', datos_doc.get('rep_legal_nombre', 'No registrado'))
                parentesco_t = datos_doc.get('parentesco_tutor', '')
                texto_tutor = f"{nombre_t} ({parentesco_t})" if parentesco_t else nombre_t
                st.write(f"**Nombre:**\n{texto_tutor}")
            with sub_rep2:
                # Alternancia dinámica si el tutor no posee RUT
                if datos_doc.get('sin_rut_tutor'):
                    tipo_id_tutor = datos_doc.get('tipo_doc_tutor', 'Pasaporte')
                    id_tutor = datos_doc.get('num_doc_tutor', 'N/A')
                    st.write(f"**Documento ({tipo_id_tutor}):**\n{id_tutor}")
                else:
                    st.write(f"**RUT:**\n{datos_doc.get('rut_tutor', datos_doc.get('rep_legal_rut', 'N/A'))}")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- B. BIOSEGURIDAD MAGNÉTICA ---
        with st.expander("🧲 2. BIOSEGURIDAD MAGNÉTICA", expanded=True):
            
            # 1. Marcapasos cardíaco (Visualización)
            tiene_marcapaso = evaluar_si_no(datos_doc.get('bio_marcapaso'))
            st.write(f"**Marcapasos cardíaco:** {'🔴 SÍ' if tiene_marcapaso else '✅ NO'}")
            if tiene_marcapaso and datos_doc.get('nota_marcapaso'):
                st.warning(datos_doc.get('nota_marcapaso'))

            # 2. Implantes / Prótesis (Visualización)
            tiene_implantes = evaluar_si_no(datos_doc.get('bio_implantes'))
            st.write(f"**Implantes / Prótesis / Dispositivos:** {'🔴 SÍ' if tiene_implantes else '✅ NO'}")
            if tiene_implantes and datos_doc.get('nota_implante'):
                st.warning(datos_doc.get('nota_implante'))

            # 3. Clasificación de Bioseguridad (NUEVA LÓGICA DE SELECCIÓN)
            if tiene_implantes:
                st.markdown("---")
                st.subheader("📋 Clasificación Técnica de Seguridad")
                
                # Asumimos que extraes los implantes de una lista o campo en datos_doc
                # Si es una cadena, puedes separarla por comas:
                lista_implantes = [imp.strip() for imp in datos_doc.get('nota_implante', '').split(',')] if datos_doc.get('nota_implante') else ["Implante no especificado"]

                for implante in lista_implantes:
                    st.markdown(f"**Evaluación para:** `{implante}`")
                    
                    key_estado = f"clasificacion_{implante}_{datos_doc.get('rut', 'default')}"
                    if key_estado not in st.session_state:
                        st.session_state[key_estado] = None

                    cols = st.columns(3, vertical_alignment="bottom") # <--- AÑADIR vertical_alignment
                    opciones = [
                        ("MR SAFE", "MRSAFE.png", "🟢"),
                        ("MR CONDITIONAL", "MRCONDITIONAL.png", "🟡"),
                        ("MR UNSAFE", "MRUNSAFE.png", "🔴")
                    ]

                    for i, (nombre, archivo, color) in enumerate(opciones):
                        with cols[i]:
                            try:
                                # AÑADIR use_container_width=True a la imagen
                                st.image(archivo, use_container_width=True) 
                            except:
                                st.warning("Img no encontrada")
                            
                            btn_key = f"btn_{nombre}_{implante}"
                            if st.button(f"{nombre}", key=btn_key, use_container_width=True):
                                st.session_state[key_estado] = nombre

                    # Indicador visual de selección (Lógica de Semáforo)
                    clasificacion_actual = st.session_state.get(key_estado, None)
                    
                    if clasificacion_actual:
                        if clasificacion_actual == "MR SAFE":
                            st.success(f"✅ Clasificación asignada: **{clasificacion_actual}**")
                            st.info("💡 **Instrucción:** Verifica que el elemento, implante o dispositivo tenga el sello de compatibilidad de MR SAFE.")
                        elif clasificacion_actual == "MR CONDITIONAL":
                            st.warning(f"⚠️ Clasificación asignada: **{clasificacion_actual}**")
                            st.info("💡 **Instrucción:** Revisa las especificaciones del fabricante y ajusta los parámetros (SAR, B1+rms, Gradientes) para su examinación en Resonancia Magnética.")
                        elif clasificacion_actual == "MR UNSAFE":
                            st.error(f"❌ Clasificación asignada: **{clasificacion_actual}**")
                            st.error("🚨 **ALERTA CRÍTICA:** Estos elementos o dispositivos no deben entrar por ningún motivo a la sala de Resonancia Magnética.")
                    else:
                        st.info(f"⚠️ Pendiente de clasificar")

            # 4. Detalle de Bioseguridad (Nota general)
            st.markdown("---")
            st.write("**Detalle Bioseguridad (Observaciones):**")
            st.info(datos_doc.get('bio_detalle') if datos_doc.get('bio_detalle') else "Sin observaciones")

     # --- C. ANTECEDENTES CLÍNICOS (TABLA DE RIESGOS VINCULADA) ---
        with st.expander("📋 3. ANTECEDENTES CLÍNICOS", expanded=True):
            data_riesgos = {
            "Antecedente Clínico": [
                "Ayuno 2hrs+", "Asma", "Alergias", "Hipertensión", 
                "Hipotiroidismo", "Diabetes", "Metformina 48h", 
                "Insuficiencia Renal", "Diálisis", "Embarazo", 
                "Lactancia", "Claustrofobia", "Enfermedad Oncológica (Cáncer)"
            ],
            "Estado": [
                "✅ SÍ" if evaluar_si_no(datos_doc.get('clin_ayuno')) else "🔴 NO",
                "🔴 SÍ" if evaluar_si_no(datos_doc.get('clin_asma')) else "✅ NO",
                "🔴 SÍ" if evaluar_si_no(datos_doc.get('clin_alergico')) else "✅ NO",
                "🔴 SÍ" if evaluar_si_no(datos_doc.get('clin_hiperten')) else "✅ NO",
                "🔴 SÍ" if evaluar_si_no(datos_doc.get('clin_hipertiroid')) else "✅ NO",
                "🔴 SÍ" if evaluar_si_no(datos_doc.get('clin_diabetes')) else "✅ NO",
                "🔴 SÍ" if evaluar_si_no(datos_doc.get('clin_metformina')) else "✅ NO",
                "🚨 SÍ" if evaluar_si_no(datos_doc.get('clin_renal')) else "✅ NO",
                "🚨 SÍ" if evaluar_si_no(datos_doc.get('clin_dialisis')) else "✅ NO",
                "🚨 SÍ" if evaluar_si_no(datos_doc.get('clin_embarazo')) else "✅ NO",
                "🔴 SÍ" if evaluar_si_no(datos_doc.get('clin_lactancia')) else "✅ NO",
                "🔴 SÍ" if evaluar_si_no(datos_doc.get('clin_claustro')) else "✅ NO",
                "🔴 SÍ" if (evaluar_si_no(datos_doc.get('quir_cancer')) or evaluar_si_no(datos_doc.get('clin_cancer'))) else "✅ NO"
            ],
            "Recomendación / Alerta": [
                "", # Ayuno
                "", # Asma
                datos_doc.get('nota_alergico', '') if evaluar_si_no(datos_doc.get('clin_alergico')) else "",
                "", # Hipertensión
                "", # Hipotiroidismo
                "", # Diabetes
                "", # Metformina
                datos_doc.get('nota_renal', '') if evaluar_si_no(datos_doc.get('clin_renal')) else "",
                datos_doc.get('nota_dialisis', '') if evaluar_si_no(datos_doc.get('clin_dialisis')) else "",
                datos_doc.get('nota_embarazo', '') if evaluar_si_no(datos_doc.get('clin_embarazo')) else "",
                datos_doc.get('nota_lactancia', '') if evaluar_si_no(datos_doc.get('clin_lactancia')) else "",
                datos_doc.get('nota_claustro', '') if evaluar_si_no(datos_doc.get('clin_claustro')) else "",
                datos_doc.get('nota_cancer', '') if (evaluar_si_no(datos_doc.get('quir_cancer')) or evaluar_si_no(datos_doc.get('clin_cancer'))) else ""
            ]
        }
        st.table(pd.DataFrame(data_riesgos))

        # --- VISUALIZACIÓN DE CONDICIONES ESPECIALES Y COMENTARIOS DEL PACIENTE ---
        condiciones_list = datos_doc.get("condiciones", [])
        otra_condicion_txt = datos_doc.get("otra_condicion", "").strip()
        comentario_condicion_txt = datos_doc.get("comentario_condicion", "").strip()

        if (condiciones_list and "Ninguna de las anteriores" not in condiciones_list) or otra_condicion_txt or comentario_condicion_txt:
            st.markdown("---")
            st.markdown("⚠️ **Condiciones Especiales o Comentarios del Paciente:**")
            
            if condiciones_list and "Ninguna de las anteriores" not in condiciones_list:
                st.write(f"**Categorías seleccionadas:** {', '.join(condiciones_list)}")
            
            if otra_condicion_txt:
                st.info(f"**Detalle de Condición Especial:** {otra_condicion_txt}")
                
            if comentario_condicion_txt:
                st.info(f"**Texto / Comentario Adicional:** {comentario_condicion_txt}")

    # =============================================================================
    # COLUMNA 2: EVALUACIÓN DE FUNCIÓN RENAL, CIRUGÍAS Y TRATAMIENTOS, EXÁMENES ANT.
    # =============================================================================
    with c2:
                # --- B. ANTECEDENTES QUIRÚRGICOS Y TERAPÉUTICOS ---
                with st.expander("🏥 4. ANTECEDENTES QUIRÚRGICOS Y TERAPÉUTICOS", expanded=True):
                    # Inyectamos evaluar_si_no() aquí para traducir el texto "Sí" o "No"
                    st.write(f"**Cirugías:** {'🔴 SÍ' if evaluar_si_no(datos_doc.get('quir_cirugia_check')) else '✅ NO'}")
                    st.write("**Detalle Cirugías:**")
                    st.caption(datos_doc.get('quir_cirugia_detalle') if datos_doc.get('quir_cirugia_detalle') else "N/A")
                    
                    # --- INCORPORACIÓN DE PREGUNTA ONCOLÓGICA ---
                    st.write(f"**Enfermedad Oncológica (Cáncer):** {'🔴 SÍ' if (evaluar_si_no(datos_doc.get('quir_cancer')) or evaluar_si_no(datos_doc.get('clin_cancer'))) else '✅ NO'}")
                    
                    trats_activos = []
                    if datos_doc.get('quir_rt') or datos_doc.get('rt'): trats_activos.append("RT")
                    if datos_doc.get('quir_qt') or datos_doc.get('qt'): trats_activos.append("QT")
                    if datos_doc.get('quir_bt') or datos_doc.get('bt'): trats_activos.append("BT")
                    if datos_doc.get('quir_it') or datos_doc.get('it'): trats_activos.append("IT")
                    
                    st.write(f"**Tratamientos:** {', '.join(trats_activos) if trats_activos else 'Ninguno'}")
                    st.write("**Otros Tratamientos:**")
                    st.caption(datos_doc.get('quir_otro_trat') if datos_doc.get('quir_otro_trat') else "N/A")

                # --- C. EXÁMENES ANTERIORES ---
                with st.expander("📂 5. EXÁMENES ANTERIORES", expanded=True):
                    ex_activos = []
                    if datos_doc.get('ex_rx'): ex_activos.append("Rx")
                    if datos_doc.get('ex_mg'): ex_activos.append("MG")
                    if datos_doc.get('ex_eco'): ex_activos.append("Eco")
                    if datos_doc.get('ex_tc'): ex_activos.append("TC")
                    if datos_doc.get('ex_rm'): ex_activos.append("RM")
                    
                    st.write(f"**Exámenes Realizados:** {', '.join(ex_activos) if ex_activos else 'Ninguno'}")
                    st.write("**Otros Exámenes Anteriores:**")
                    st.caption(datos_doc.get('ex_otros') if datos_doc.get('ex_otros') else "N/A")

                # --- C. EXÁMENES ANTERIORES ---
                with st.expander("📂 5. EXÁMENES ANTERIORES", expanded=True):
                    ex_activos = []
                    if datos_doc.get('ex_rx'): ex_activos.append("Rx")
                    if datos_doc.get('ex_mg'): ex_activos.append("MG")
                    if datos_doc.get('ex_eco'): ex_activos.append("Eco")
                    if datos_doc.get('ex_tc'): ex_activos.append("TC")
                    if datos_doc.get('ex_rm'): ex_activos.append("RM")
                    
                    st.write(f"**Exámenes Realizados:** {', '.join(ex_activos) if ex_activos else 'Ninguno'}")
                    st.write("**Otros Exámenes Anteriores:**")
                    st.caption(datos_doc.get('ex_otros') if datos_doc.get('ex_otros') else "N/A")

            # --- A. EVALUACIÓN DE LA FUNCIÓN RENAL (EDICIÓN EN TIEMPO REAL) ---
                with st.expander("🧪 6. EVALUACIÓN DE LA FUNCIÓN RENAL", expanded=True):
                    es_estudio_basal = not datos_doc.get('tiene_contraste', False)
                    
                    # Recuperación segura de variables
                    try: creatinina_base = float(datos_doc.get('creatinina', 0.0))
                    except: creatinina_base = 0.0
                    try: peso_base = float(datos_doc.get('peso', 0.0))
                    except: peso_base = 0.0
                    try: talla_base = float(datos_doc.get('talla', 0.0))
                    except: talla_base = 0.0

                    if es_estudio_basal and peso_base == 70.0: peso_base = 0.0

                    st.markdown("<span style='font-size: 13px; color: #666;'><b>Ajuste de Parámetros Clínicos:</b></span>", unsafe_allow_html=True)
                    col_p, col_c, col_t = st.columns(3)

                    # Determinación estricta de edad para bloqueos
                    fecha_nac = datos_doc.get('fecha_nac', datos_doc.get('fecha_nacimiento', datetime.today().date()))
                    if isinstance(fecha_nac, str):
                        try: edad_calc = (date.today() - datetime.strptime(fecha_nac[:10], '%d/%m/%Y').date()).days / 365.25
                        except: edad_calc = 18
                    else:
                        edad_calc = (date.today() - fecha_nac).days / 365.25
                        
                    es_pediatrico = (edad_calc < 18)

                    with col_p:
                        peso_profesional = st.number_input(
                            "Peso (kg):",
                            min_value=0.0, max_value=250.0, value=peso_base, step=1.0,
                            disabled=es_pediatrico, # Bloqueado en niños, editable en adultos
                            help="Visible pero bloqueado en pacientes pediátricos." if es_pediatrico else "Obligatorio para adultos."
                        )
                    with col_c:
                        creatinina_profesional = st.number_input(
                            "Creatinina (mg/dL):",
                            min_value=0.0, max_value=15.0, value=creatinina_base, step=0.01
                        )
                    with col_t:
                        talla_profesional = st.number_input(
                            "Talla (cm):",
                            min_value=0.0, max_value=250.0, value=talla_base, step=1.0,
                            disabled=not es_pediatrico, # Bloqueado en adultos, editable en niños
                            help="Bloqueado en adultos." if not es_pediatrico else "Obligatorio para pediatría y lactantes."
                        )

                    # Recálculo Dinámico Universal
                    sexo_bio_paciente = datos_doc.get('genero_biologico', datos_doc.get('sexo', 'M'))
                    vfg_dinamico, formula_dinamica = calcular_vfg_universal(
                        fecha_nac, sexo_bio_paciente, creatinina_profesional, talla_profesional, peso_profesional
                    )

                    mensaje_alerta, color_hex, color_rgb_pdf = obtener_alerta_vfg(vfg_dinamico, fecha_nac)
                    flecha = "▼" if "RIESGO" in mensaje_alerta and "SIN" not in mensaje_alerta else "▲"

                    # Renderizado HTML Visual
                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; margin-top: 10px; border-top: 1px solid #eee;">
                        <div style="text-align: center;">
                            <span style="font-size: 11px; color: #666;">Fórmula Aplicada</span><br>
                            <span style="font-size: 14px; font-weight: bold;">{formula_dinamica}</span>
                        </div>
                        <div style="text-align: center;">
                            <span style="font-size: 11px; color: #666;">VFG</span><br>
                            <span style="font-size: 16px; font-weight: bold; color: {color_hex};">{flecha} {vfg_dinamico:.2f} <span style="font-size: 10px;">ml/min</span></span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"<div style='text-align: center; color: {color_hex}; font-weight: bold; margin-top: 5px;'>{mensaje_alerta}</div>", unsafe_allow_html=True)

                    # Almacenamiento estricto para el PDF final
                    st.session_state.pdf_peso = peso_profesional
                    st.session_state.pdf_creatinina = creatinina_profesional
                    st.session_state.pdf_talla = talla_profesional
                    st.session_state.pdf_vfg = vfg_dinamico
                    st.session_state.pdf_formula = formula_dinamica
                    st.session_state.pdf_mensaje = mensaje_alerta
                    st.session_state.pdf_color_rgb = color_rgb_pdf
                    st.session_state.pdf_es_pediatrico = es_pediatrico

                    # --- NUEVO BLOQUE: TABLA DE REFERENCIA VFG ---
                    st.markdown("---")
                    st.markdown("<span style='font-size: 13px; color: #666;'><b>📊 Referencia de Riesgo (Adultos y Niños > 2 años)</b></span>", unsafe_allow_html=True)
                    tabla_vfg_erc = pd.DataFrame({
                        "Estadio ERC": ["Normal / Alto", "Ligero descenso", "Moderado a grave", "Grave", "Fallo Renal"],
                        "VFG (ml/min/1.73m²)": ["≥ 90", "60 - 89", "30 - 59", "15 - 29", "< 15"],
                        "Riesgo Contraste": ["Sin Riesgo", "Precaución / Bajo", "Riesgo Intermedio", "Alto Riesgo", "Contraindicado"]
                    })
                    st.table(tabla_vfg_erc)

                    st.markdown("<span style='font-size: 13px; color: #666;'><b>👶 Referencia de Maduración Renal (Lactantes < 2 años)</b></span>", unsafe_allow_html=True)
                    tabla_vfg_ped = pd.DataFrame({
                        "Edad del Lactante": ["1 semana", "2 a 4 semanas", "1 a 2 meses", "3 a 4 meses", "5 a 12 meses", "1 a 2 años"],
                        "VFG Esperada (ml/min)": ["15 - 30", "30 - 50", "40 - 65", "55 - 85", "70 - 110", "85 - 125"],
                        "Alerta Clínica": ["Alto Riesgo si < 10.5", "Alto Riesgo si < 21", "Alto Riesgo si < 28", "Alto Riesgo si < 38", "Alto Riesgo si < 49", "Alto Riesgo si < 59"]
                    })
                    st.table(tabla_vfg_ped)

                

                # --- SECCIÓN 7: REGISTRO DE ADMINISTRACIÓN DE CONTRASTE ---
                with st.expander("💉 7. REGISTRO DE ADMINISTRACIÓN DE CONTRASTE", expanded=True):
                    col_acc, col_sit = st.columns(2)
                with col_acc:
                    acceso_venoso = st.selectbox("Acceso Venoso", ["Bránula", "Mariposa", "PICC (Catéter central periférico)", "CVC (Catéter venoso central)", "No requiere"])
                with col_sit:
                    sitio_puncion = st.text_input("Sitio de punción (Ej. Pliegue antebrazo derecho):")

                st.markdown("**💊 Medios de Contraste y Fármacos Administrados:**")
                
                lista_medios_disponibles = [
                    "Ac. Gadotérico (Clariscan)", "Gadopiclenol (Elucirem)", 
                    "Ac. Gadoxético (Primovist)", "Gel de ultrasonido", 
                    "Contraste neutro (H2O)", "Suero fisiológico (NaCl 0,9%)", "Otro (Especificar)"
                ]
                medios_seleccionados = st.multiselect("Seleccione uno o más medios/fármacos:", lista_medios_disponibles)
                
                # Diccionario para guardar las vías y cantidades de cada contraste seleccionado
                if "datos_contraste" not in st.session_state:
                    st.session_state.datos_contraste = {}

                if medios_seleccionados:
                    for medio in medios_seleccionados:
                        # Cuadro estilo tabla para cada contraste
                        st.markdown(f"<div style='padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 5px;'><b>{medio}</b>", unsafe_allow_html=True)
                        cc1, cc2 = st.columns(2)
                        with cc1:
                            via = st.selectbox(f"Vía de administración", ["Endovenosa", "Oral", "Rectal", "Intraarticular", "No aplica"], key=f"via_{medio}")
                        with cc2:
                            cant = st.number_input(f"Cantidad administrada (ml/cc)", min_value=0.0, step=0.5, key=f"cant_{medio}")
                        
                        st.session_state.datos_contraste[medio] = {"via": via, "cantidad": cant}
                        st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.info("No se han seleccionado medios de contraste.")
                
                otros_meds = st.text_input("Otros medicamentos adicionales (Observaciones):")

    # 3. FIRMA DIGITAL
    st.markdown("#### ✍️ Firma Digital del Paciente")
    try:
        ruta_firma = doc_completo.get("firma_img")
        if ruta_firma:
            blob = bucket.blob(ruta_firma)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                blob.download_to_filename(tmp.name)
                st.image(Image.open(tmp.name), width=300)
        else:
            st.caption("No se capturó firma.")
    except Exception as e:
        st.error(f"Error cargando firma: {e}")

    # --- BLOQUE DE DOBLE FIRMA SEGURA ---
    st.divider()
    st.markdown("### ✍️ Validación del Profesional (Doble Firma)")

    # Formulario de validación técnica
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        profesional_nombre = st.text_input(
            "Nombre del Tecnólogo Médico / Profesional:", 
            value=st.session_state.current_user['nombre'], 
            disabled=True,
            key="tm_nom"
        )
        profesional_registro = st.text_input(
            "N° Registro Superintendencia de Salud (SIS):", 
            value=st.session_state.current_user['sis'], 
            disabled=True,
            key="tm_sis"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.warning("⚠️ Al presionar 'Aprobar Encuesta', usted certifica bajo su firma que ha evaluado la tasa de filtración glomerular (VFG) y los factores de riesgo del paciente para la ejecución segura del examen.")

    with col_f2:
        st.markdown("##### Firma Digital del Profesional:")
        canvas_profesional = st_canvas(
            fill_color="rgba(255, 255, 255, 0)",
            stroke_width=4,
            stroke_color="#000000",
            background_color="#ffffff",
            height=150,
            width=400,
            drawing_mode="freedraw",
            key="canvas_tm"
        )

    # --- BOTÓN DE CIERRE DE CIRCUITO CLÍNICO ---
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Inicializar variables de estado en la sesión para persistencia del PDF
    if "pdf_ready" not in st.session_state:
        st.session_state.pdf_ready = False
    if "pdf_bytes_data" not in st.session_state:
        st.session_state.pdf_bytes_data = None
    if "pdf_filename" not in st.session_state:
        st.session_state.pdf_filename = ""
    if "paciente_nombre_val" not in st.session_state:
        st.session_state.paciente_nombre_val = ""

    if st.button("🚀 APROBAR ENCUESTA Y GUARDAR VALIDACIÓN", use_container_width=True):
        if canvas_profesional is not None and canvas_profesional.json_data is not None and len(canvas_profesional.json_data["objects"]) > 0:
            with st.spinner("Estampando firma del profesional y consolidando documento..."):
                try:
                    # =====================================================================
                    # 1. PROCESAR LA FIRMA DEL PROFESIONAL (TM)
                    # =====================================================================
                    img_data_tm = canvas_profesional.image_data
                    img_tm_pil = Image.fromarray(img_data_tm.astype('uint8'), 'RGBA')
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_tm:
                        img_tm_pil.save(tmp_tm.name)
                        ruta_firma_tm_local = tmp_tm.name

                    # =====================================================================
                    # 2. SUBIR FIRMA DEL TM A STORAGE
                    # =====================================================================
                    nombre_archivo_tm_storage = f"firmas_profesionales/TM_{profesional_registro}_{datetime.now(tz_chile).strftime('%Y%m%d_%H%M%S')}.png"
                    blob_tm = bucket.blob(nombre_archivo_tm_storage)
                    blob_tm.upload_from_filename(ruta_firma_tm_local, content_type='image/png')

                    # =====================================================================
                    # 3. ACTUALIZAR FIRESTORE (CIERRE DE ESTADO CLINICO)
                    # =====================================================================
                    fecha_validacion_str = datetime.now(tz_chile).strftime("%d/%m/%Y %H:%M:%S")
                    id_documento_paciente = paciente_seleccionado.id if hasattr(paciente_seleccionado, 'id') else str(paciente_seleccionado)
                    
                    db.collection("encuestas").document(id_documento_paciente).update({
                        "profesional_nombre": profesional_nombre,
                        "profesional_registro": profesional_registro,
                        "fecha_validacion": fecha_validacion_str,
                        "estado_validacion": "VALIDADO",
                        "encuesta_validada": True,
                        "firma_profesional_img": nombre_archivo_tm_storage
                    })
                    
                    # =====================================================================
                    # 📄 4. PREPARACIÓN E INYECCIÓN DE VARIABLES AL MOTOR PDF
                    # =====================================================================
                    st.info("🔄 Compilando formato institucional Norte Imagen...")

                    import io
                    import os
                    from fpdf import FPDF

                    # Extraemos con llaves e índices sanitizados para el reporte PDF
                    paciente_nombre = datos_doc.get('nombre', 'Paciente No Identificado')

                    # --- NUEVA LÓGICA BLINDADA: Identificación Paciente ---
                    es_extranjero = datos_doc.get('sin_rut', False)
                    if es_extranjero in [True, "true", "True", "1"]:
                        paciente_rut = f"{datos_doc.get('tipo_doc', 'Documento')}: {datos_doc.get('num_doc', 'S/N')}"
                    else:
                        paciente_rut = str(datos_doc.get('rut', datos_doc.get('run', 'S/R')))
                    # -------------------------------------------------------

                    fecha_nacimiento_val = datos_doc.get('fecha_nac', datos_doc.get('fecha_nacimiento', 'N/A'))
                    if hasattr(fecha_nacimiento_val, 'strftime'):
                        fecha_nacimiento_val = fecha_nacimiento_val.strftime('%d/%m/%Y')
                    email_val = datos_doc.get('email', 'N/A')
                    procedimiento_val = datos_doc.get('procedimiento', 'RM General')

                    # =====================================================================
                    # 🏳️‍🌈 IDENTIDAD DE GÉNERO INCLUSIVA Y SEXO REGISTRAL (REEMPLAZO)
                    # =====================================================================
                    idx_gen_admin = str(datos_doc.get('genero_idx', '0'))
                    idx_bio_admin = str(datos_doc.get('sexo_bio_idx', '0'))
                    ocr_bio_admin = str(datos_doc.get('genero_biologico', '')).strip().capitalize()

                    if idx_gen_admin == "1" or idx_gen_admin in ["Femenino", "F", "Mujer"]:
                        genero = "Femenino"
                    elif idx_gen_admin == "2" or idx_gen_admin in ["No binario", "Nobinario"] or str(datos_doc.get('sexo')) == "No binario":
                        # Rescate inteligente de sexo biológico por OCR o por respaldo de índice
                        if ocr_bio_admin in ["Masculino", "Femenino"]:
                            sexo_bio_str = ocr_bio_admin
                        else:
                            sexo_bio_str = "Femenino" if idx_bio_admin == "1" else "Masculino"
                        
                        # Cadena unificada de coincidencia perfecta
                        genero = f"No binario (Bio: {sexo_bio_str})"
                    else:
                        genero = "Masculino"
                    # =====================================================================

                    # Sincronización estricta del indicador de contraste
                    is_contraste = datos_doc.get('tiene_contraste', False) in [True, "Sí", "SI", "si", "Si"]
                    
                    # --- NUEVA LÓGICA BLINDADA: Identificación Tutor Legal ---
                    rep_nombre = datos_doc.get('nombre_tutor', '')
                    if datos_doc.get('sin_rut_tutor'):
                        rep_rut = f"{datos_doc.get('tipo_doc_tutor', 'Doc')}: {datos_doc.get('num_doc_tutor', 'S/R')}"
                    else:
                        rep_rut = datos_doc.get('rut_tutor', 'S/R')
                    # ---------------------------------------------------------

                    ip_cliente = datos_doc.get('ip_dispositivo', 'No detectada')
                    ruta_firma_paciente_storage = datos_doc.get('firma_img', '')

                    # Descarga segura de la firma del paciente (Tótem)
                    ruta_p_local = None
                    if ruta_firma_paciente_storage:
                        try:
                            blob_firma_p = bucket.blob(ruta_firma_paciente_storage)
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img_p:
                                blob_firma_p.download_to_filename(tmp_img_p.name)
                                ruta_p_local = tmp_img_p.name
                        except Exception as e_firma:
                            print(f"Error descargando firma paciente: {e_firma}")

                    st.session_state.paciente_nombre_val = paciente_nombre

                    # Funciones auxiliares internas de codificación FPDF
                    def safe_text(txt):
                        if txt is None: return "N/A"
                        return str(txt).encode('latin-1', 'replace').decode('latin-1')

                    def parse_bool_clinico(val):
                        if isinstance(val, bool): return "Sí" if val else "No"
                        if str(val).strip().upper() in ['SI', 'SÍ', 'TRUE', '1', 'YES']: return "Sí"
                        return "No"

                    # --- DECLARACIÓN DEL COMPILADOR INSTITUCIONAL CORREGIDO ---
                    class PDF_Institucional(FPDF):
                        def __init__(self, p_nombre, p_rut, p_ip, f_val):
                            super().__init__()
                            self.p_nombre = p_nombre
                            self.p_rut = p_rut
                            self.p_ip = p_ip
                            self.f_val = f_val

                        def header(self):
                            if os.path.exists("logoNI.png"):
                                self.image("logoNI.png", 10, 8, 45)
                            self.set_font('Arial', 'B', 12)
                            self.set_text_color(128, 0, 32)
                            self.cell(0, 7, safe_text('ENCUESTA DE RIESGOS ASOCIADOS Y'), 0, 1, 'R')
                            self.cell(0, 7, safe_text('CONSENTIMIENTO INFORMADO'), 0, 1, 'R')
                            self.set_font('Arial', 'B', 16)
                            self.cell(0, 8, safe_text('RESONANCIA MAGNETICA'), 0, 1, 'R')
                            self.ln(10)

                        def footer(self):
                            self.set_y(-15)
                            self.set_font('Arial', 'I', 7)
                            self.set_text_color(150, 150, 150)
                            
                            iniciales = "".join([p[0].upper() for p in self.p_nombre.split() if p])
                            
                            ip_final = getattr(self, 'p_ip', 'IP No detectada')
                            
                            # 🔑 Si la IP no viene asignada, la buscamos dentro del diccionario datos_doc
                            if ip_final == "IP No detectada" and hasattr(self, 'datos_doc'):
                                ip_final = self.datos_doc.get('ip_paciente', 'IP No detectada')
                            
                            id_registro = f"{self.p_rut}-{iniciales} (IP:{ip_final})"
                            texto_pie = f"Certificado Digital Norte Imagen - RM: {self.f_val} - ID Registro: {id_registro} - VALIDADO TM."

                            self.cell(0, 10, safe_text(texto_pie), 0, 0, 'L')
                            self.cell(0, 10, safe_text(f"Página {self.page_no()}/{{nb}}"), 0, 0, 'R')

                        def section_title(self, num, title):
                            self.set_font('Arial', 'B', 10)
                            # 🔘 ACTIVAMOS EL FONDO GRIS: Seteamos gris claro para el sombreado de la barra
                            self.set_fill_color(240, 240, 240)
                            # 🔥 TONO BURDEO: Seteamos color burdeo (128, 0, 32) para las letras del título
                            self.set_text_color(128, 0, 32)
                            # 🟢 RENDERIZADO: Dibujamos la barra con ancho total (0), alto 6, y fill=True para que pinte el fondo gris
                            self.cell(0, 6, safe_text(f" {num}. {title}"), ln=True, fill=True)
                            self.ln(1.5)
                            # 🧼 RESTABLECER CONTEXTO: Volvemos a negro absoluto y fondo blanco para el contenido de las subsecciones
                            self.set_text_color(0, 0, 0)
                            self.set_fill_color(255, 255, 255)

                        # SOLUCIÓN CRÍTICA: Aquí agregamos formalmente 'h=5' con un valor por defecto
                        def data_field(self, label, value, h=5):
                            self.set_font('Arial', 'B', 9)
                            self.set_text_color(50, 50, 50)
                            self.write(h, f"{safe_text(label)}: ")
                            self.set_font('Arial', '', 9)
                            self.set_text_color(0, 0, 0)
                            self.write(h, f"{safe_text(value)}\n")

                   # --- INSTANCIACIÓN DEL MOTOR DE REPORTES ---
                    # 🔥 REPARACIÓN PASO 3: Búsqueda de IP en cascada (¡Agregada la llave exacta de app.py al principio!)
                    ip_cliente = datos_doc.get('ip_paciente', 
                                 datos_doc.get('ip_dispositivo', 
                                 datos_doc.get('ip', 
                                 form_interno.get('ip_dispositivo', 
                                 form_interno.get('ip', 'IP No detectada')))))

                    fecha_validacion_str = datetime.now(tz_chile).strftime("%d/%m/%Y %H:%M:%S")
                    paciente_nombre = datos_doc.get('nombre', 'Paciente')
                    paciente_rut = datos_doc.get('rut', 'N/A')

                    # 1. Instanciamos el motor pasando la IP correcta
                    pdf = PDF_Institucional(paciente_nombre, paciente_rut, ip_cliente, fecha_validacion_str)
                    
                    # 🚀 INYECCIÓN QUIRÚRGICA: Forzamos los atributos exactos que lee tu 'def footer'
                    pdf.p_nombre = paciente_nombre
                    pdf.p_rut = paciente_rut
                    pdf.f_val = fecha_validacion_str
                    pdf.p_ip = ip_cliente
                    pdf.datos_doc = datos_doc  # Respaldo completo del diccionario
                    
                    # 2. Inicialización de páginas
                    pdf.alias_nb_pages()
                    pdf.add_page()
                    pdf.set_auto_page_break(auto=True, margin=12)

                    # --- ENCABEZADO FECHA Y PROCEDENCIA ---
                    pdf.set_font('Arial', 'B', 9)
                    # 🟢 Añadimos safe_text para blindar la celda contra fallos de encoding
                    pdf.cell(0, 5, safe_text(f"Fecha de examen: {fecha_validacion_str.split()[0]}"), 0, 1, 'R')
                    procedencia_val = datos_doc.get('procedencia', 'AMBULATORIO').upper()
                                                  pdf.set_font('Arial', 'B', 10)
                                                  pdf.cell(0, 5, safe_text(f"Procedencia: {procedencia_val}"), 0, 1, 'L') 
                    pdf.ln(2)

                    # --- SECCIÓN 1: IDENTIFICACIÓN DEL PACIENTE ---
                    pdf.section_title("1", "IDENTIFICACION DEL PACIENTE")
                    
                    margen_izquierdo = 10
                    ancho_disponible = pdf.w - 20
                    w_col = (ancho_disponible - 10) / 2
                    x_col2 = margen_izquierdo + w_col + 10

                    pdf.set_font('Arial', 'B', 10)
                    pdf.cell(32, 5, "Nombre Completo: ", 0, 0)
                    pdf.set_font('Arial', '', 10)
                    pdf.cell(0, 5, safe_text(paciente_nombre), 0, 1)

                    y_fila2 = pdf.get_y()
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(32, 5, "Documento / RUT: ", 0, 0)
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(w_col - 32, 5, safe_text(paciente_rut), 0, 0)
                    
                    # --- REEMPLAZO DE EDAD EXACTA ---
                    edad_formateada = calcular_edad_exacta(datos_doc['fecha_nac'])
                    
                    pdf.set_xy(x_col2, y_fila2)
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(12, 5, "Edad: ", 0, 0)
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(w_col - 12, 5, safe_text(edad_formateada), 0, 1)

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

                    # --- LINEA DE PROCEDIMIENTO EN PARALELO ---
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(28, 5, safe_text("Procedimiento(s): "), 0, 0, 'L')
                    
                    pdf.set_font('Arial', '', 9)
                    # Escribe inmediatamente al lado; si es muy largo, saltará de línea de forma natural
                    pdf.multi_cell(0, 5, safe_text(procedimiento_val), 0, 'L')
                    pdf.ln(2)

                    # Manejo seguro e inclusión de Representante Legal / Tutor
                    if rep_nombre or edad_int < 18:
                        pdf.ln(1)
                        y_tutor = pdf.get_y()
                        pdf.set_font('Arial', 'B', 9)
                        pdf.cell(28, 5, "Representante: ", 0, 0)
                        pdf.set_font('Arial', '', 9)
                        pdf.cell(w_col - 28, 5, safe_text(rep_nombre if rep_nombre else 'N/A'), 0, 0)
                        
                        pdf.set_xy(x_col2, y_tutor)
                        pdf.set_font('Arial', 'B', 9)
                        pdf.cell(22, 5, "Parentesco: ", 0, 0)
                        pdf.set_font('Arial', '', 9)
                        pdf.cell(w_col - 22, 5, safe_text(datos_doc.get('parentesco_tutor', 'N/A')), 0, 1)

                        pdf.set_font('Arial', 'B', 9)
                        pdf.cell(35, 5, "Doc. Representante: ", 0, 0)
                        pdf.set_font('Arial', '', 9)
                        pdf.cell(w_col - 35, 5, safe_text(rep_rut if rep_rut else 'N/A'), 0, 1)

                    # --- SECCIÓN 2: BIOSEGURIDAD (SINCRONIZACIÓN EXACТА DE NOMBRE DE LLAVES) ---
                    pdf.section_title("2", "BIOSEGURIDAD MAGNETICA")
                    pdf.set_font('Arial', '', 9)
                    pdf.data_field("Marcapasos cardiaco", parse_bool_clinico(datos_doc.get('bio_marcapaso', 'No')), h=5)
                    pdf.data_field("Implantes metálicos, quirúrgicos, prótesis o dispositivo electrónicos", parse_bool_clinico(datos_doc.get('bio_implantes', 'No')), h=5)
                    
                    pdf.set_font('Arial', 'I', 8)
                    pdf.data_field("Detalle Bioseguridad", det_bio if det_bio else "Sin observaciones", h=4.5)
                    
                    pdf.ln(2)

                    # --- SECCIÓN 3: ANTECEDENTES CLÍNICOS (SISTEMA DE GRILLA CORREGIDO CON PREFIJOS CLIN_) ---
                    pdf.section_title("3", "ANTECEDENTES CLINICOS")
                    
                    clinicos = [
                        ("Ayuno 2hrs+", parse_bool_clinico(datos_doc.get('clin_ayuno', 'No'))), 
                        ("Asma", parse_bool_clinico(datos_doc.get('clin_asma', 'No'))), 
                        ("Alergias", parse_bool_clinico(datos_doc.get('clin_alergico', 'No'))),
                        ("Hipertensión", parse_bool_clinico(datos_doc.get('clin_hiperten', 'No'))), 
                        ("Hipotiroidismo", parse_bool_clinico(datos_doc.get('clin_hipertiroid', 'No'))), 
                        ("Diabetes", parse_bool_clinico(datos_doc.get('clin_diabetes', 'No'))),
                        ("Metformina 48h", parse_bool_clinico(datos_doc.get('clin_metformina', 'No'))), 
                        ("Insuf. Renal", parse_bool_clinico(datos_doc.get('clin_renal', 'No'))), 
                        ("Diálisis", parse_bool_clinico(datos_doc.get('clin_dialisis', 'No'))),
                        ("Embarazo", parse_bool_clinico(datos_doc.get('clin_embarazo', 'No'))), 
                        ("Lactancia", parse_bool_clinico(datos_doc.get('clin_lactancia', 'No'))), 
                        ("Claustrofobia", parse_bool_clinico(datos_doc.get('clin_claustro', 'No')))
                    ]

                    w_col_fija = ancho_disponible / 4

                    for i in range(0, len(clinicos), 4):
                        linea = clinicos[i:i+4]
                        y_fila_actual = pdf.get_y()

                        for idx_col, (item, valor) in enumerate(linea):
                            # Filtro clínico de género para evitar incongruencias visuales en el PDF institucional
                            if genero == "Masculino" and item in ["Embarazo", "Lactancia"]:
                                valor = "N/A"
                            
                            x_exacto = margen_izquierdo + (idx_col * w_col_fija)
                            pdf.set_xy(x_exacto, y_fila_actual)
                            
                            pdf.set_font('Arial', '', 8)
                            texto_col = f"{item}: {valor}"
                            pdf.cell(w_col_fija - 2, 4.5, safe_text(texto_col), 0, 0)
                        
                        pdf.set_x(margen_izquierdo)
                        pdf.ln(4.5) 
                        
                    pdf.ln(2)

                    # --- SECCIÓN 4: ANTECEDENTES QUIRÚRGICOS ---
                    pdf.section_title("4", "ANTECEDENTES QUIRURGICOS Y TERAPEUTICOS")
                    pdf.set_font('Arial', '', 9)
                    pdf.data_field("Cirugías", parse_bool_clinico(datos_doc.get('quir_cirugia_check', 'No')), h=5)
                    
                    pdf.set_font('Arial', 'I', 8)
                    det_cir = datos_doc.get('quir_cirugia_detalle', '')
                    pdf.data_field("Detalle cirugías", det_cir if det_cir else "N/A", h=4.5)
                    
                    trats_dict = {"RT": datos_doc.get('rt', False), "QT": datos_doc.get('qt', False), "BT": datos_doc.get('bt', False), "IT": datos_doc.get('it', False)}
                    trats = [k for k, v in trats_dict.items() if v in [True, "Sí", "SI", "si", 1, "true", "Si"]]
                    
                    pdf.set_font('Arial', '', 9)
                    pdf.data_field("Tratamientos", ", ".join(trats) if trats else "Ninguno", h=5)
                    
                    pdf.set_font('Arial', 'I', 8)
                    otr_trat = datos_doc.get('quir_otro_trat', '')
                    pdf.data_field("Detalle de otros tratamientos", otr_trat if otr_trat else "N/A", h=4.5)
                    
                    pdf.ln(2)

                    # --- SECCIÓN 5: EXÁMENES ANTERIORES ---
                    pdf.section_title("5", "EXAMENES ANTERIORES")
                    ex_dict = {"Rx": datos_doc.get('ex_rx', False), "MG": datos_doc.get('ex_mg', False), "Eco": datos_doc.get('ex_eco', False), "TC": datos_doc.get('ex_tc', False), "RM": datos_doc.get('ex_rm', False)}
                    ex_list = [k for k, v in ex_dict.items() if v in [True, "Sí", "SI", "si", 1, "true", "Si"]]
                    
                    pdf.set_font('Arial', '', 9)
                    pdf.data_field("Exámenes", ", ".join(ex_list) if ex_list else "Ninguno", h=5)
                    
                    pdf.set_font('Arial', 'I', 8)
                    ex_otr = datos_doc.get('ex_otros', '')
                    pdf.data_field("Otros exámenes anteriores", ex_otr if ex_otr else "N/A", h=4.5)
                    
                    pdf.ln(2)

                    # --- SECCIÓN 6: FUNCIÓN RENAL INTEGRADA CON CONTRASTE ---
                    pdf.section_title("6", "EVALUACIÓN DE LA FUNCION RENAL")
                    pdf.set_font('Arial', '', 9)
                    
                    try: crea_float = float(st.session_state.get('pdf_creatinina', 0.0))
                    except: crea_float = 0.0
                    try: peso_float = float(st.session_state.get('pdf_peso', 0.0))
                    except: peso_float = 0.0
                    try: talla_float = float(st.session_state.get('pdf_talla', 0.0))
                    except: talla_float = 0.0
                    try: vfg_float = float(st.session_state.get('pdf_vfg', 0.0))
                    except: vfg_float = 0.0

                    es_pediatrico = st.session_state.get('pdf_es_pediatrico', False)
                    
                    pdf.data_field("Creatinina", f"{crea_float:.2f} mg/dL" if crea_float > 0 else "__________ mg/dL", h=5)

                    if es_pediatrico:
                        pdf.data_field("Talla (Pediátrico)", f"{talla_float:.1f} cm" if talla_float > 0 else "__________ cm", h=5)
                    else:
                        pdf.data_field("Peso (Adulto)", f"{peso_float:.1f} kg" if peso_float > 0 else "__________ kg", h=5)
                    
                    if vfg_float > 0:
                        formula_pdf = st.session_state.get('pdf_formula', 'Fórmula no especificada')
                        msg_riesgo = st.session_state.get('pdf_mensaje', '')
                        r, g, b = st.session_state.get('pdf_color_rgb', (0,0,0))

                        if not is_contraste:
                            msg_riesgo += " (Calculado preventivamente en basal)"

                        pdf.set_font('Arial', 'B', 9)
                        pdf.set_text_color(50, 50, 50) 
                        pdf.write(5, safe_text(f"V.F.G ({formula_pdf}): "))
                        
                        pdf.set_font('Arial', 'B', 9)
                        pdf.set_text_color(r, g, b)
                        pdf.write(5, safe_text(f"{vfg_float:.2f} ml/min ({msg_riesgo})\n"))
                        pdf.set_text_color(0, 0, 0)
                    else:
                        if is_contraste:
                            pdf.data_field("RESULTADO VFG", "__________ ml/min (Cálculo manual)", h=5)
                        else:
                            pdf.data_field("RESULTADO VFG", "__________ ml/min (Sin Contraste)", h=5)
                            
                    pdf.ln(2)

                    # --- SECCIÓN 7: REGISTRO DE ADMINISTRACIÓN EN BLANCO PARA ENFERMERÍA ---
                    pdf.section_title("7", "REGISTRO DE ADMINISTRACION DE MEDIO DE CONTRASTE Y OTROS")
                    
                    w_col_7 = (ancho_disponible - 10) / 2
                    x_col7_derecha = margen_izquierdo + w_col_7 + 10

                    y_cabecera1 = pdf.get_y()
                    pdf.set_font('Arial', 'B', 9) 
                    pdf.set_fill_color(245, 245, 245)
                    pdf.cell(w_col_7, 6, safe_text(" Acceso venoso:"), 0, 0, 'L', fill=True)
                    
                    pdf.set_xy(x_col7_derecha, y_cabecera1)
                    pdf.cell(w_col_7, 6, safe_text(" Sitio de punción:"), 0, 1, 'L', fill=True)
                    pdf.ln(1)
                    
                    y_inputs1 = pdf.get_y()
                    pdf.set_font('Arial', '', 9)
                    opciones_acceso = "[      ] Branula: ________ G  [      ] Mariposa: ________ G"
                    pdf.cell(w_col_7, 8, safe_text(opciones_acceso), 0, 0, 'L') 
                    
                    pdf.set_xy(x_col7_derecha, y_inputs1)
                    pdf.cell(w_col_7, 8, safe_text("______________________________________________"), 0, 1, 'L')
                    pdf.ln(1)
                    
                    y_cabecera2 = pdf.get_y()
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(w_col_7, 6, safe_text(" Medio de contraste (Intravenoso):"), 0, 0, 'L', fill=True)
                    
                    pdf.set_xy(x_col7_derecha, y_cabecera2)
                    pdf.cell(w_col_7, 6, safe_text(" Cantidad administrada:"), 0, 1, 'L', fill=True)
                    pdf.ln(1)
                    
                    pdf.set_font('Arial', '', 9)
                    pos_y_bloque = pdf.get_y()
                    pdf.cell(w_col_7, 4.5, safe_text("[     ] Ácido gadotérico (Clariscan)"), 0, 1, 'L')
                    pdf.cell(w_col_7, 4.5, safe_text("[     ] Gadopiclenol (Elucirem)"), 0, 1, 'L')
                    pdf.cell(w_col_7, 4.5, safe_text("[     ] Ácido gadoxético (Primovist)"), 0, 1, 'L')
                    
                    pdf.set_xy(x_col7_derecha, pos_y_bloque + 4.5)
                    pdf.cell(w_col_7, 5, safe_text("_____________________ ml."), 0, 1, 'L')
                    
                    pdf.set_x(margen_izquierdo)
                    pdf.ln(4)

                  # =====================================================================
                    # 📄 PÁGINA 2: TEXTO LEGAL DE CONSENTIMIENTO INFORMADO
                    # =====================================================================
                    pdf.add_page()
                    pdf.set_font('Arial', 'B', 10)

                    texto_procedimiento_p2 = f"Procedimiento: {procedimiento_val}"

                    if is_contraste:
                        # Caso con contraste
                        texto_procedimiento_p2 += " con uso de medio de contraste."
                        pdf.multi_cell(0, 6, safe_text(texto_procedimiento_p2), 0, 'L')
                        pdf.ln(2)
                    else:
                        # Caso sin contraste: agregamos el texto correspondiente
                        texto_procedimiento_p2 += " sin medio de contraste."
                        pdf.multi_cell(0, 6, safe_text(texto_procedimiento_p2), 0, 'L')
                        
                        # Agregamos la pregunta y el recuadro dinámico debajo
                        pdf.ln(1)
                        pdf.set_font('Arial', '', 9)
                        
                        # 1. Escribimos la pregunta primero (sin salto de línea)
                        pregunta = "¿Se aplicó medio de contraste adicionalmente?"
                        ancho_texto = pdf.get_string_width(pregunta) + 2 # Calculamos cuánto mide el texto
                        pdf.cell(ancho_texto, 6, safe_text(pregunta), 0, 0, 'L')
                        
                        # 2. Obtenemos la posición justo donde terminó el texto
                        pos_x = pdf.get_x()
                        pos_y = pdf.get_y()
                        
                        # 3. Dibujamos el rectángulo (5x5 mm)
                        # Lo subimos un poco (pos_y + 1) para que alinee bien con la fuente
                        pdf.rect(pos_x + 2, pos_y + 1, 5, 5) 
                        
                        # 4. Hacemos el salto de línea manual para que el resto del documento no se encime
                        pdf.ln(8)
                        
                        # Devolvemos la fuente a su formato original (negrita) si los siguientes títulos lo requieren
                        pdf.set_font('Arial', 'B', 10)

                    pdf.set_font('Arial', 'B', 10)
                    pdf.set_text_color(128, 0, 32)
                    pdf.cell(0, 6, safe_text("LEA ATENTA Y CUIDADOSAMENTE LO SIGUIENTE:"), 0, 1, 'L')
                    pdf.ln(1)

                    sections = {
                        "OBJETIVOS": (
                            "La Resonancia Magnética (RM) es una segura técnica de Diagnóstico, que permite la adquisición "
                            "de imágenes de gran sensibilidad en todos los planos del espacio de las estructuras del cuerpo. "
                            "Tiene como objetivo obtener información, datos funcionales y morfológicos para detectar precozmente una enfermedad.\n\n"
                            "Para este examen eventualmente se puede requerir la utilización de un medio de contraste paramagnético "
                            "de administración endovenosa llamado gadolinio, que permite realzar ciertos tejidos del cuerpo para un mejor diagnóstico."
                        ),
                        "CARACTERÍSTICAS": (
                            "La Resonancia utiliza fuertes campos magnéticos y ondas de radiofrecuencia, por lo que es muy importante "
                            "dejar fuera de la sala absolutamente todo lo que lleve consigo de tipo metálico y/o electrónico (relojes, pulseras, "
                            "teléfonos, tarjetas magnéticas, etc). Si lleva material de este tipo en su cuerpo (fijaciones dentales, piercings, "
                            "algunos tatuajes, balas o esquirlas metálicas), ciertos tipos de prótesis (valvulares, de cadera, de rodilla, "
                            "clips metálicos, etc), o implantes, así como dispositivos electrónicos de carácter médico como bombas de insulina, "
                            "prótesis auditivas, marcapasos, desfibriladores, etc., avísenos, ya que puede contraindicar de manera absoluta la realización de este examen.\n\n"
                            "Usted será posicionado en la camilla del equipo, según el estudio a realizar y se colocarán cerca de la zona a estudiar "
                            "unos dispositivos (bobinas) que pueden ser de diversos tamaños. Esta exploración suele ser larga (entre 20 min y 1 hr según los casos). "
                            "Notará ruido derivado del funcionamiento de la RM (por lo que le facilitaremos unos protectores auditivos), todo esto es normal "
                            "y se le vigilará constantemente desde la sala de control.\n\n"
                            "Es muy importante que permanezca quieto durante el estudio y siga las instrucciones del Tecnólogo Médico."
                        ),
                        "POTENCIALES RIESGOS": (
                            "Existe una muy baja posibilidad de que se presente una reacción adversa al medio de contraste (0.07-2.4%), "
                            "la mayoría de carácter leve, fundamentalmente náuseas o cefaleas al momento de la inyección.\n\n"
                            "Pacientes con deterioro importante de la función renal poseen riesgo de desarrollo de fibrosis nefrogénica sistémica."
                        )
                    }

                    for tit, cont in sections.items():
                        pdf.set_font('Arial', 'B', 9)
                        pdf.set_text_color(128, 0, 32)
                        pdf.cell(0, 5, safe_text(tit), 0, 1, 'L')
                        pdf.set_font('Arial', '', 8.5)
                        pdf.set_text_color(0, 0, 0)
                        pdf.multi_cell(0, 4.2, safe_text(cont))
                        pdf.ln(2)

                    pdf.set_font('Arial', '', 8.5)
                    consentimiento_texto = (
                        "He sido informado de mi derecho de anular o revocar posteriormente este documento, "
                        "dejándolo constatado por escrito y firmado por mí o mi representante.\n\n"
                        "Autorizo la realización del procedimiento anteriormente especificado y las acciones que sean necesarias "
                        "en caso de surgir complicaciones durante el procedimiento. Además, doy consentimiento para que se administren "
                        "medicamentos y/o infusiones que se requieran para la realización de este."
                    )
                    pdf.multi_cell(0, 4.2, safe_text(consentimiento_texto))
                    pdf.ln(3)
                    
                    texto_declaracion = "Certifico que toda la información provista en esta encuesta es fidedigna y corresponde a mi estado de salud actual."
                    pdf.multi_cell(0, 4, safe_text(texto_declaracion), 0, 'J')
                    pdf.ln(12)
                    
                    # =====================================================================
                    # ✒️ SECCIÓN DE FIRMAS BALANCEADAS Y CENTRADAS
                    # =====================================================================
                    pdf.ln(5)
                    y_pos_firmas = pdf.get_y()
                    
                    # 1. ESTAMPAMOS LAS IMÁGENES PNG PRIMERO (Para que queden de fondo)
                    # --- COLUMNA 1: CENTRADO DE FIRMA PACIENTE / TUTOR ---
                    if ruta_p_local and os.path.exists(ruta_p_local):
                        # Columna de 95mm: margen inicial 10mm + (95mm - 45mm de imagen)/2 = 35mm
                        pdf.image(ruta_p_local, 35, y_pos_firmas, 45, 12)
                    
                    # --- COLUMNA 2: CENTRADO DE FIRMA PROFESIONAL A CARGO ---
                    if 'ruta_firma_tm_local' in locals() and os.path.exists(ruta_firma_tm_local):
                        # Segunda columna: margen inicial 10mm + 95mm + (95mm - 45mm)/2 = 130mm
                        pdf.image(ruta_firma_tm_local, 130, y_pos_firmas, 45, 12)
                    
                    # 2. ESCRIBIMOS LOS NOMBRES SOBRE LAS IMÁGENES
                    # Bajamos 8mm para que el texto quede flotando sobre la firma PNG
                    pdf.set_y(y_pos_firmas + 8)
                    
                    # CAMBIO: Subimos la fuente a 10
                    pdf.set_font('Arial', '', 10) 
                    
                    # CAMBIO: Aplicamos .title() a las variables de nombre
                    nombre_paciente_pdf = datos_doc.get('nombre', 'Paciente').strip().title()
                    profesional_nombre_pdf = profesional_nombre.strip().title()
                    
                    pdf.cell(95, 4, safe_text(nombre_paciente_pdf), 0, 0, 'C')
                    pdf.cell(95, 4, safe_text(profesional_nombre_pdf), 0, 1, 'C')
                    
                    # 3. DIBUJAMOS LAS LÍNEAS DE FIRMA JUSTO DEBAJO DE LOS NOMBRES
                    pdf.cell(95, 4, "________________________________________", 0, 0, 'C')
                    pdf.cell(95, 4, "________________________________________", 0, 1, 'C')
                    
                    # 4. ETIQUETAS INSTITUCIONALES DE FIRMA (NEGRITA)
                    pdf.set_font('Arial', 'B', 8)
                    pdf.cell(95, 4, safe_text("FIRMA PACIENTE O REPRESENTANTE LEGAL"), 0, 0, 'C')
                    pdf.cell(95, 4, safe_text("FIRMA PROFESIONAL A CARGO"), 0, 1, 'C')
                    
                    # 5. ANTECEDENTES R.L Y TÍTULOS PROFESIONALES
                    pdf.set_font('Arial', '', 8)
                    nombre_tutor_pdf = datos_doc.get('nombre_tutor', '').strip()
                    rut_tutor_pdf = datos_doc.get('rut_tutor', '').strip()
                    
                    if nombre_tutor_pdf:
                        # Recuperamos el parentesco para mayor precisión legal en la firma
                        parentesco_t_pdf = datos_doc.get('parentesco_tutor', '').strip()
                        texto_nombre_rl = f"R.L: {nombre_tutor_pdf} ({parentesco_t_pdf})" if parentesco_t_pdf else f"R.L: {nombre_tutor_pdf}"
                        pdf.cell(95, 4, safe_text(texto_nombre_rl), 0, 0, 'C')
                    else:
                        pdf.cell(95, 4, "", 0, 0, 'C')
                        
                    pdf.cell(95, 4, safe_text("Tecnólogo Médico en Imagenología"), 0, 1, 'C')
                    
                    if nombre_tutor_pdf:
                        # Alternancia dinámica del documento para la zona de firmas
                        if datos_doc.get('sin_rut_tutor'):
                            tipo_id_tutor_pdf = datos_doc.get('tipo_doc_tutor', 'Doc').strip()
                            id_tutor_pdf = datos_doc.get('num_doc_tutor', '').strip()
                            texto_doc_rl = f"{tipo_id_tutor_pdf} R.L: {id_tutor_pdf}"
                        else:
                            texto_doc_rl = f"R.R.L: {rut_tutor_pdf}"
                            
                        pdf.cell(95, 4, safe_text(texto_doc_rl), 0, 0, 'C')
                    else:
                        pdf.cell(95, 4, "", 0, 0, 'C')
                        
                    pdf.cell(95, 4, safe_text("Esp. Resonancia Magnética"), 0, 1, 'C')
                    
                    # 6. REGISTRO SIS DINÁMICO
                    pdf.cell(95, 4, "", 0, 0, 'C')
                    pdf.cell(95, 4, safe_text(f"Registro SIS: {profesional_registro}"), 0, 1, 'C') # Variable dinámica real
                    
                    pdf.ln(4)

                    # =====================================================================
                    # 💾 COMPILACIÓN BINARIA ESTÁNDAR Y ASIGNACIÓN DE NOMBRE OFICIAL
                    # =====================================================================
                    try:
                        raw_data = pdf.output(dest='S')
                    except TypeError:
                        raw_data = pdf.output()

                    if isinstance(raw_data, str):
                        pdf_bytes_final = raw_data.encode('latin-1', errors='replace')
                    elif isinstance(raw_data, bytearray):
                        pdf_bytes_final = bytes(raw_data)
                    else:
                        pdf_bytes_final = raw_data

                    st.session_state.pdf_bytes_data = pdf_bytes_final
        
                    # Nomenclatura oficial de archivo solicitada para auditorías chilenas
                    meses_chile = ['', 'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
                    mes_actual = meses_chile[datetime.now(tz_chile).month]
                    año_actual = datetime.now(tz_chile).strftime('%Y')
                    
                    rut_limpio_pdf = str(paciente_rut).replace('.', '').upper()
                    st.session_state.pdf_filename = f"REG-VALIDADO_{paciente_nombre.replace(' ', '-').upper()}_{rut_limpio_pdf}_{mes_actual}_{año_actual}.pdf"
                    st.session_state.pdf_ready = True
                    
                    st.success(f"🎉 ¡Circuito Clínico Cerrado! Paciente {paciente_nombre} validado correctamente bajo la firma de {profesional_nombre}.")
                    st.balloons()
                        
                except Exception as ex_admin:
                    st.error(f"🚨 Error operativo al cerrar protocolo o compilar PDF institucional: {ex_admin}")
                finally:
                    # Limpieza quirúrgica de archivos temporales de firmas en el contenedor para evitar sobrepeso
                    try:
                        if 'ruta_firma_tm_local' in locals() and os.path.exists(ruta_firma_tm_local):
                            os.unlink(ruta_firma_tm_local)
                        if 'ruta_p_local' in locals() and ruta_p_local and os.path.exists(ruta_p_local):
                            os.unlink(ruta_p_local)
                    except:
                        pass
        else:
            st.error("🚨 Firma incompleta. Debe dibujar su firma digital en el recuadro para visar el procedimiento.")

    # =====================================================================
    # 📥 RENDERIZADO DEL BOTÓN DE DESCARGA (INMUNE A REFRESH)
    # =====================================================================
    if st.session_state.pdf_ready and st.session_state.pdf_bytes_data is not None:
        st.markdown("---")
        st.markdown("### 📥 Descarga de Documento Oficial")
        
        nombre_paciente_pdf = st.session_state.get('doc_completo', {}).get('nombre', 'Paciente')
        st.write(f"El consentimiento institucional de **{nombre_paciente_pdf}** ha sido visado con ambas firmas.")
        
        st.download_button(
            label="📄 DESCARGAR PDF INSTITUCIONAL FIRMADO",
            data=st.session_state.pdf_bytes_data,
            file_name=st.session_state.pdf_filename,
            mime="application/pdf",
            key="btn_descarga_pdf_final",
            use_container_width=True
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🧼 LIMPIAR BANDEJA Y CONTINUAR", use_container_width=True):
            # 1. Limpiamos solo las variables activas (DEBE ESTAR INDENTADO)
            st.session_state.paciente_seleccionado = None
            st.session_state.doc_completo = None
            st.session_state.pdf_ready = False
            st.session_state.pdf_bytes_data = None
            st.rerun() # O st.experimental_rerun()
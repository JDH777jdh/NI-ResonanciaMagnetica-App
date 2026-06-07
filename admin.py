# =============================================================================
# COPYRIGHT (c) 2026 [JONATHAN HAROLD ENRIQUE DÍAZ HUAMÁN]. TODOS LOS DERECHOS RESERVADOS.
# 
# Este software es propiedad intelectual exclusiva del autor, Tecnólogo Médico.
# La arquitectura, lógica clínica y módulos de gestión son propiedad del autor.
# Su uso, distribución o modificación está estrictamente limitado a los 
# términos de licenciamiento otorgados. Queda prohibida la ingeniería inversa, 
# copia o uso no autorDETAizado por terceros fuera de los entornos licenciados.
# 
# Autor: [JONATHAN HAROLD ENRIQUE DÍAZ HUAMÁN]
# Registro Profesional: [513416]
# =====================================================================
# 1. PRIMERO: TODAS LAS IMPORTACIONES DE LIBRERÍAS
# =====================================================================
import streamlit as st
import os  # <--- ¡AGREGA ESTA LÍNEA AQUÍ!*15
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
from werkzeug.security import generate_password_hash, check_password_hash # <--- ¡NUEVA LÍNEA AGREGADA

# =====================================================================
# MOTOR CLÍNICO UNIVERSAL VFG (Integración Segura)
# =====================================================================
from datetime import date, datetime

# =============================================================================
# DEFINICIÓN GLOBAL DE FUNCIONES DE SEGURIDAD Y ROLES
# =============================================================================
def obtener_rol_actual():
    return st.session_state.get('user_role', 'visualizador')

def es_owner():
    return obtener_rol_actual() == 'owner'

def es_coordinador_o_master():
    return obtener_rol_actual() in ['tm_coordinador', 'owner']

def puede_editar_y_firmar():
    # TMs, Coordinador y Owner tienen el control clínico
    return obtener_rol_actual() in ['tm', 'tm_coordinador', 'owner']

def es_solo_lectura():
    # TENS, Secretarias y Calidad no pueden modificar clínica
    return obtener_rol_actual() in ['tens', 'secretaria', 'calidad']

def puede_trazabilidad():
    # Basado en la regla: Calidad tiene acceso exclusivo. (Añadimos Owner por jerarquía absoluta).
    return obtener_rol_actual() in ['calidad', 'owner']
# =============================================================================

def mostrar_archivo_interactivo(blob, nombre_archivo):
    """Renderiza botón de 'Abrir en nueva pestaña' y botón de descarga."""
    try:
        bytes_archivo = blob.download_as_bytes()
        ext = os.path.splitext(nombre_archivo)[1].lower().replace(".", "")
        mime = "application/pdf" if ext == "pdf" else f"image/{ext}"
        
        # Convertir a base64
        b64_data = base64.b64encode(bytes_archivo).decode()
        data_url = f"data:{mime};base64,{b64_data}"
        
        # 1. Botón para abrir en nueva pestaña
        st.markdown(f'''
            <a href="{data_url}" target="_blank" style="text-decoration:none;">
                <div style="text-align:center; padding:10px; background-color: #e1f5fe; border-radius:5px; border:1px solid #b3e5fc; cursor:pointer; margin-bottom:5px;">
                    👁️ <b>Abrir {nombre_archivo}</b> (Nueva pestaña)
                </div>
            </a>
        ''', unsafe_allow_html=True)
        
        # 2. Botón de descarga de respaldo
        st.download_button(
            label=f"⬇️ Descargar original",
            data=bytes_archivo,
            file_name=nombre_archivo,
            mime=mime,
            key=f"btn_descarga_{nombre_archivo}_{int(time.time())}",
            width='stretch'
        )
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        
def normalizar_procedimiento_definitivo(texto_crudo, tiene_contraste_actual):
    """
    Limpia cualquier etiqueta previa de contraste y fuerza la nomenclatura oficial.
    Esta es la única fuente de verdad.
    """
    # Lista de términos a erradicar para evitar duplicados clínicos
    patron_limpieza = r'(?i)\s*[\(\-]?\s*\b(con medio de contraste|sin medio de contraste|con contraste|sin contraste|c/gd|c/c|s/c|c/contraste)\b\s*[\(\)\-]?\s*'
    
    # 1. Limpiar y estandarizar a mayúsculas
    nombre_base = re.sub(patron_limpieza, '', str(texto_crudo)).strip().upper()
    nombre_base = re.sub(r'\s+', ' ', nombre_base).strip(' ,')
    
    # 2. Inyectar el estado real (priorizando el input del TM)
    sufijo = "CON CONTRASTE" if tiene_contraste_actual else "SIN CONTRASTE"
    
    return f"{nombre_base} {sufijo}"
    
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

def calcular_edad_visual_completa(fecha_nacimiento):
    """
    Calcula la edad exacta en años, meses y días.
    USO EXCLUSIVO VISUAL: Interfaz de usuario (UI) y renderizado PDF.
    No interfiere con VFG ni alertas clínicas.
    """
    if not fecha_nacimiento or fecha_nacimiento == 'N/A':
        return "N/A"
        
    hoy = date.today()
    
    # 1. Parseo estricto
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
    
    # 3. Formateo acumulativo y gramatical (Ej: 30 años, 2 meses y 5 días)
    partes = []
    if diferencia.years > 0:
        partes.append(f"{diferencia.years} años")
    if diferencia.months > 0:
        partes.append(f"{diferencia.months} meses")
    if diferencia.days > 0:
        partes.append(f"{diferencia.days} días")
        
    if not partes:
        return "0 días"
        
    if len(partes) > 1:
        return ", ".join(partes[:-1]) + " y " + partes[-1]
    else:
        return partes[0]

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

# --- INICIALIZACIÓN SEGURA DE ESTADO ---
if "selector_refresh_key" not in st.session_state:
    st.session_state.selector_refresh_key = 0
if 'paciente_seleccionado' not in st.session_state:
    st.session_state.paciente_seleccionado = None
if 'doc_completo' not in st.session_state:
    st.session_state.doc_completo = {}

# 🚀 INYECCIÓN PASO 3: Control de navegación entre pantallas
if "vista_actual" not in st.session_state:
    st.session_state.vista_actual = "principal"

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
st.subheader("👨🏻‍⚕️👩🏻‍⚕️ Panel de Control y Validación de Seguridad (Tecnólogo Médico)")
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
    st.warning("🔒 **Acceso Restringido.**\n\nIngrese sus credenciales Institucionales.")
    col1, col2 = st.columns([1, 2])
    with col1:
        # 1. Agregado placeholder y autocomplete="username" para reconocimiento del navegador
        email_ingresado = st.text_input(
            "Correo Electrónico (ID):", 
            placeholder="usuario@cdnorteimagen.cl", 
            autocomplete="username"
        ).strip().lower()
        
        # 2. Agregado autocomplete="current-password" para que el navegador guarde la clave
        pin_ingresado = st.text_input(
            "Ingrese su Clave Personal (PIN):", 
            type="password", 
            autocomplete="current-password"
        )
        
        if st.button("Ingresar al Sistema", use_container_width=True):
            # 3. Lógica: Autodetectar dominio si no está presente
            email_busqueda = email_ingresado
            if email_busqueda and "@" not in email_busqueda:
                email_busqueda += "@cdnorteimagen.cl"
                
            if email_busqueda and pin_ingresado:
                try:
                    # Búsqueda directa en Firebase usando el email ajustado
                    doc_user = db.collection("usuarios").document(email_busqueda).get()
                    
                    if doc_user.exists:
                        user_data = doc_user.to_dict()
                        
                        # 1. Verificar si está activo
                        if not user_data.get("activo", True):
                            st.error("🔴 Cuenta suspendida. Contacte al TM Coordinador.")
                        else:
                            # 2. Verificar contraseña (encriptada o texto plano para transición)
                            hash_guardado = user_data.get("password_hash", "")
                            pin_plano_guardado = user_data.get("pin_plano", "")
                            
                            acceso_concedido = False
                            if hash_guardado and check_password_hash(hash_guardado, pin_ingresado):
                                acceso_concedido = True
                            elif pin_plano_guardado and pin_ingresado == pin_plano_guardado:
                                acceso_concedido = True # Plan de transición por si los inyectas en texto plano primero
                            
                            if acceso_concedido:
                                st.session_state.authenticated = True
                                st.session_state.current_user = user_data
                                st.session_state.user_role = user_data.get('rol', 'visualizador') 
                                st.success(f"🔓 Bienvenido(a), {user_data['nombre']}")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("🔑 Clave incorrecta.")
                    else:
                        st.error("👤 Usuario no encontrado en los registros.")
                except Exception as e:
                    st.error(f"Error de conexión con el servidor: {e}")
            else:
                st.warning("Debe ingresar correo y clave.")
        st.stop()
        
from streamlit_option_menu import option_menu
import time

# --- BARRA LATERAL DINÁMICA CON ROLES NOMINALES ---
st.sidebar.markdown(f"### 🛡️ Credenciales Activas")
st.sidebar.markdown(f"**Operador:**\n{st.session_state.current_user['nombre']}")
st.sidebar.markdown(f"**Rol Asignado:**\n`{st.session_state.current_user['rol'].upper()}`")
st.sidebar.markdown(f"**Identificación Profesional:**\n{st.session_state.current_user.get('sis', 'N/A')}")

st.sidebar.markdown("### ⚙️ Estado: Operativo 🟢")
st.sidebar.markdown("---")

# --- PORTAL DE PACIENTES EN EXPANDER ---
with st.sidebar.expander("📱 Portal Pacientes (Encuesta/Consentimiento)"):
    # Carga segura del QR desde la raíz de tu repositorio de GitHub
    try:
        st.image("QRPacientes.png", caption="Escanee para acceder al formulario", use_container_width=True)
    except Exception:
        # Plan de contingencia por si la imagen se encuentra en una subcarpeta
        try:
            st.image("images/QRPacientes.png", caption="Escanee para acceder al formulario", use_container_width=True)
        except Exception:
            st.error("⚠️ Archivo 'QRPacientes.png' no detectado.")

# --- ACCESOS DIRECTOS INSTITUCIONALES EN EXPANDER ---
with st.sidebar.expander("🔗 Enlaces Clínicos RIS/PACS"):
    st.link_button("🖥️🩻 RIS/PACS Bilbao", "https://risnimag1.irad.cl/RISWEB/Timeout.aspx", use_container_width=True)
    st.link_button("🖥️🩻 RIS/PACS Fernández", "https://risnimag2.irad.cl/RISWEB/Timeout.aspx", use_container_width=True)
    st.link_button("📋📊 Portal Resultados", "https://risnimag1.irad.cl/PPAC/", use_container_width=True)

st.sidebar.markdown("---")

# =============================================================================
# INICIO DE NAVEGACIÓN PROFESIONAL (OPTION MENU)
# =============================================================================
if "modo_vista" not in st.session_state:
    st.session_state.modo_vista = "bandeja"

if "vista_actual" not in st.session_state:
    st.session_state.vista_actual = "principal"

# 1. Construir las opciones del menú dinámicamente según los permisos del usuario
opciones_menu = ["Panel Principal"]
iconos_menu = ["house"]

if not es_solo_lectura() or obtener_rol_actual() in ['tens', 'secretaria']:
    opciones_menu.extend(["Motor de Rescate", "Emisión Certificados"])
    iconos_menu.extend(["ambulance", "file-earmark-medical"])

if puede_trazabilidad():
    opciones_menu.append("Ver Trazabilidad")
    iconos_menu.append("search")

# 2. Mapear la vista actual (del session_state) para mantener iluminada la opción correcta
vistas_map = {
    "principal": "Panel Principal",
    "rescate": "Motor de Rescate",
    "certificados": "Emisión Certificados",
    "trazabilidad": "Ver Trazabilidad"
}
vista_actual_nombre = vistas_map.get(st.session_state.vista_actual, "Panel Principal")
default_idx = opciones_menu.index(vista_actual_nombre) if vista_actual_nombre in opciones_menu else 0

# 3. Renderizar el Option Menu
with st.sidebar:
    seleccion_vista = option_menu(
        menu_title="Herramientas Clínicas",
        options=opciones_menu,
        icons=iconos_menu,
        menu_icon="cast",
        default_index=default_idx,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#4F8BF9", "font-size": "18px"}, 
            "nav-link": {"font-size": "14px", "text-align": "left", "margin":"0px", "--hover-color": "#2c3e50"},
            "nav-link-selected": {"background-color": "#1F618D", "color": "white"},
        }
    )

# 4. Lógica de Ruteo Automática al hacer clic en el menú
if seleccion_vista == "Panel Principal" and st.session_state.vista_actual != "principal":
    st.session_state.vista_actual = "principal"
    st.session_state.doc_completo = {} 
    st.session_state.paciente_seleccionado = None
    st.rerun()

elif seleccion_vista == "Motor de Rescate" and st.session_state.vista_actual != "rescate":
    st.session_state.vista_actual = "rescate"
    st.session_state.doc_completo = {} 
    st.session_state.paciente_seleccionado = None 
    st.rerun()

elif seleccion_vista == "Emisión Certificados" and st.session_state.vista_actual != "certificados":
    st.session_state.vista_actual = "certificados"
    st.session_state.doc_completo = {} 
    st.session_state.paciente_seleccionado = None
    st.rerun()

elif seleccion_vista == "Ver Trazabilidad":
    st.sidebar.info("Módulo de trazabilidad en desarrollo.")

# =============================================================================
# PANEL DE GESTIÓN DE USUARIOS (ACCESIBLE EXCLUSIVAMENTE POR COORDINADOR Y DUEÑO)
# =============================================================================
if es_coordinador_o_master():
    st.sidebar.markdown("---")
    st.sidebar.markdown("👑 **CONTROLADOR JERÁRQUICO ACTIVO**")
    
    expander_gestion = st.sidebar.expander("🛠️ GESTIÓN DE PERSONAL INSTITUCIONAL", expanded=False)
    with expander_gestion:
        opcion_admin = st.radio("Seleccione Operación:", ["Listar y Modificar Estados", "Crear Nuevo Usuario / Cambiar PIN"], key="radio_admin_key")
        
        if opcion_admin == "Listar y Modificar Estados":
            try:
                usuarios_db = db.collection("usuarios").stream()
                for u_doc in usuarios_db:
                    u_data = u_doc.to_dict()
                    
                    # REGLA: El TM Coordinador NO puede ver al Owner
                    if u_data.get('rol') == 'owner' and not es_owner():
                        continue 
                        
                    col_u1, col_u2 = st.columns([2, 1])
                    estado_emoticon = "🟢 Activo" if u_data.get("activo", True) else "🔴 Suspendido"
                    col_u1.markdown(f"**{u_data['nombre']}**\n`{u_data.get('rol', 'S/R')}` - {estado_emoticon}")
                    
                    if col_u2.button("Invertir", key=f"btn_toggle_{u_doc.id}"):
                        db.collection("usuarios").document(u_doc.id).update({"activo": not u_data.get("activo", True)})
                        st.toast(f"Estado de {u_data['nombre']} modificado.")
                        time.sleep(0.4)
                        st.rerun()
                    st.markdown("---")
            except Exception as e:
                st.error(f"Error al leer usuarios: {e}")
                
        elif opcion_admin == "Crear Nuevo Usuario / Cambiar PIN":
            nuevo_nombre = st.text_input("Nombre Completo:", key="n_nom")
            nuevo_email = st.text_input("Correo Electrónico (ID):", key="n_em")
            nuevo_sis = st.text_input("Registro SIS / Cargo:", key="n_sis")
            
            roles_disponibles = ["tm", "tens", "secretaria", "calidad", "tm_coordinador"]
            if es_owner(): roles_disponibles.append("owner") # Solo el dueño puede crear otro dueño
            
            nuevo_rol = st.selectbox("Rol Asignado:", roles_disponibles, key="n_rol")
            nuevo_pin = st.text_input("Nueva Clave / PIN:", type="password", key="n_pin")
            
            if st.button("Inyectar Profesional en Producción", use_container_width=True):
                if nuevo_email and nuevo_pin and nuevo_nombre:
                    hash_creacion = generate_password_hash(nuevo_pin, method="pbkdf2:sha256", salt_length=16)
                    doc_nuevo = {
                        "nombre": nuevo_nombre, "email": nuevo_email.strip().lower(),
                        "sis": nuevo_sis, "rol": nuevo_rol, "password_hash": hash_creacion, "activo": True
                    }
                    db.collection("usuarios").document(nuevo_email.strip().lower()).set(doc_nuevo)
                    st.toast(f"✅ Profesional {nuevo_nombre} registrado de forma conforme.")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Campos obligatorios incompletos.")

st.sidebar.divider()
if st.sidebar.button("🔒 Cerrar Sesión", use_container_width=True):
    # Esto elimina absolutamente todas las variables almacenadas en la sesión
    st.session_state.clear()
    st.rerun()
# =============================================================================
# 🆘 MOTOR DE RESCATE LEGAL Y LIMPIEZA DE BD (TTL 48 HORAS)
# =============================================================================
def modulo_rescate_enmiendas():
    st.markdown("### 🆘 Módulo de Rescate y Enmienda Clínica")
    st.warning("⚠️ **ATENCIÓN:** Está accediendo a registros ya validados. Cualquier modificación realizada aquí constituirá una enmienda legal bajo la Ley 20.584 y quedará registrada en el Adendum del documento final.")
    
    hoy = datetime.now(tz_chile)
    
    try:
        # Obtenemos TODOS los validados
        docs_validados = db.collection("encuestas").where("estado_validacion", "==", "VALIDADO").stream()
        listado_rescate = []
        
        for doc in docs_validados:
            data = doc.to_dict()
            fecha_val_str = data.get("fecha_validacion")
            
            # 1. Lógica de Limpieza (TTL 2 días)
            if fecha_val_str:
                try:
                    fecha_val = datetime.strptime(fecha_val_str, "%d/%m/%Y %H:%M:%S").astimezone(tz_chile)
                    # Si pasaron más de 48 horas (2 días), lo eliminamos de la BD para no saturar
                    if (hoy - fecha_val).days >= 2:
                        db.collection("encuestas").document(doc.id).delete()
                        continue # Saltamos este paciente, ya no se muestra
                except Exception:
                    pass # Si falla el parseo, lo mostramos igual por seguridad
            
            # 2. Si sobrevivió a la limpieza, lo listamos
            listado_rescate.append({
                "Etiqueta": f"✅ VAL: {fecha_val_str}",
                "Nombre del paciente": data.get("nombre", "Sin Nombre"),
                "RUT paciente": data.get("rut", "S/R"),
                "Procedimiento": data.get("procedimiento", "No especificado"),
                "ID_Documento": doc.id
            })
            
        if not listado_rescate:
            st.info("No hay pacientes validados dentro de las últimas 48 horas disponibles para rescate.")
            return

        df_rescate = pd.DataFrame(listado_rescate)
        
        # Selector idéntico al de la bandeja, pero rojo para indicar que es rescate
        paciente_rescate = st.selectbox(
            "🔎 Seleccione el paciente a enmendar:",
            options=list(df_rescate["ID_Documento"]),
            format_func=lambda x: f"{df_rescate[df_rescate['ID_Documento']==x]['Etiqueta'].values[0]} | 👤 {df_rescate[df_rescate['ID_Documento']==x]['Nombre del paciente'].values[0]} | 🔹 RUT: {df_rescate[df_rescate['ID_Documento']==x]['RUT paciente'].values[0]}",
            key="selector_rescate"
        )
        
        if paciente_rescate != st.session_state.get('paciente_seleccionado'):
            st.session_state.paciente_seleccionado = paciente_rescate
            doc_data = db.collection("encuestas").document(paciente_rescate).get().to_dict()
            
            # 💡 MARCA DE AGUA VIRTUAL: Le indicamos al sistema que estamos en modo enmienda
            doc_data['es_enmienda'] = True 
            
            st.session_state.doc_completo = doc_data if doc_data else {}
            st.rerun()

    except Exception as e:
        st.error(f"Error cargando módulo de rescate: {e}")

# =============================================================================
# 🚦 PASO 3: ENRUTADOR SOBERANO DE VISTAS (PANTALLA PRINCIPAL VS RESCATE)
# =============================================================================

if st.session_state.vista_actual == "principal":

    # 🚨 PUENTE DE SEGURIDAD: Si venimos de un rescate exitoso, congelamos la bandeja general
    if st.session_state.get("modo_enmienda_activo", False):
        
        # 🛡️ EXTRACCIÓN SEGURA (Evita el AttributeError)
        raw_doc = st.session_state.get('doc_completo')
        # Si raw_doc es None o no es un diccionario, forzamos un dict vacío
        datos_seguros = raw_doc if isinstance(raw_doc, dict) else {}
        nombre_paciente = datos_seguros.get('nombre', 'Sin Nombre')

        st.markdown(
            f'''
            <div style="background-color: #fff3cd; padding: 15px; border-left: 6px solid #ffc107; border-radius: 4px; margin-bottom: 20px;">
                <h4 style="margin: 0; color: #856404;">⚠️ CONTROL ASIGNADO POR MOTOR DE RESCATE</h4>
                <p style="margin: 5px 0 0 0; color: #856404; font-size: 14px;">
                    Estás editando la ficha validada de: <strong>{nombre_paciente}</strong> (Modo Enmienda Activo).
                </p>
            </div>
            ''', 
            unsafe_allow_html=True
        )
        
        # Botón de escape 
        if st.button("❌ Cancelar Enmienda y Volver a la Lista de Trabajo General", use_container_width=True):
            st.session_state.modo_enmienda_activo = False
            # IMPORTANTE: Asignamos {} (diccionario vacío) en lugar de None
            st.session_state.doc_completo = {} 
            st.session_state.paciente_seleccionado = None
            st.rerun()
            
    else:
        # =============================================================================
        # ⏱️ MOTOR DE BANDEJA DE ENTRADA AUTO-ASÍNCRONA (Cada 60 Segundos)
        # =============================================================================
        @st.fragment(run_every=60)
        def filtrar_y_sincronizar_pacientes():
            # 1. UI de Cabecera
            st.markdown("### 📥 Bandeja de Entrada: Pacientes en espera de validación")
            
            hora_sincro = datetime.now(tz_chile).strftime('%H:%M:%S')
            st.caption(f"✨ Conectado a Firebase Firestore • Último auto-refresco: **{hora_sincro}**")
        
            # 2. Consulta a Firebase
            try:
                docs_ref = db.collection("encuestas").where("estado_validacion", "==", "PENDIENTE").stream()
                
                listado_pacientes = []
                for doc in docs_ref:
                    data = doc.to_dict()
                    fecha_raw = data.get("fecha_examen") or data.get("fecha") or data.get("Fecha")
                    
                    if fecha_raw:
                        if hasattr(fecha_raw, 'astimezone'):
                            fecha_str = fecha_raw.astimezone(tz_chile).strftime('%d/%m/%Y')
                        else:
                            try:
                                fecha_str = datetime.strptime(str(fecha_raw)[:10], '%Y-%m-%d').strftime('%d/%m/%Y')
                            except:
                                fecha_str = str(fecha_raw).strip()
                    else:
                        fecha_str = "Sin Fecha"
        
                    hoy_str = datetime.now(tz_chile).strftime('%d/%m/%Y')
                    
                    if fecha_str == hoy_str:
                        etiqueta_temporal = "🟢 [HOY EN SALA]"
                    elif fecha_str == "Sin Fecha":
                        etiqueta_temporal = "⚪ [FECHA NO ESPECIFICADA]"
                    else:
                        if len(fecha_str) >= 10 and fecha_str[2] == '/' and fecha_str[5] == '/':
                            fecha_corta = fecha_str[:6] + fecha_str[-2:]
                        else:
                            fecha_corta = fecha_str
                        etiqueta_temporal = f"🗓️ [AGENDADO: {fecha_corta}]"
                    
                    listado_pacientes.append({
                        "Etiqueta": etiqueta_temporal,
                        "Nombre del paciente": data.get("nombre", "Sin Nombre"),
                        "RUT paciente": data.get("rut", "S/R"),
                        "Procedimiento": data.get("procedimiento", "No especificado"),
                        "ID_Documento": doc.id
                    })
                    
            except Exception as e:
                st.error(f"🚨 Error de conexión: {e}")
                listado_pacientes = []
                
            # 3. Control de flujo: ESCENARIO VACÍO (Sin pacientes pendientes)
            if not listado_pacientes:
                st.info("✅ No hay pacientes pendientes de validación.")
                st.session_state.paciente_seleccionado = None
                st.session_state.doc_completo = {}
                
                col_vacia1, col_vacia2 = st.columns(2)
                with col_vacia1:
                    if st.button("🔄 Actualizar Bandeja", use_container_width=True):
                        st.rerun()
                with col_vacia2:
                    if st.button("🧹 Limpiar Historial", help="Elimina el historial oculto de pacientes YA validados", use_container_width=True):
                        validados = db.collection("encuestas").where("estado_validacion", "==", "VALIDADO").stream()
                        for doc in validados:
                            db.collection("encuestas").document(doc.id).delete()
                        st.rerun()
                        
                st.stop()  
        
            # 4. Procesamiento de datos y BOTONERA APILADA (Con pacientes)
            df_pacientes = pd.DataFrame(listado_pacientes)
            options_list = list(df_pacientes["ID_Documento"])
        
            col_selector, col_botones = st.columns([3, 1])
        
            with col_selector:
                paciente_seleccionado = st.selectbox(
                    "🔎 Seleccione el paciente para revisar antecedentes:",
                    options=options_list,
                    format_func=lambda x: f"{df_pacientes[df_pacientes['ID_Documento']==x]['Etiqueta'].values[0]} | 👤 {df_pacientes[df_pacientes['ID_Documento']==x]['Nombre del paciente'].values[0]} | 🔹 RUT: {df_pacientes[df_pacientes['ID_Documento']==x]['RUT paciente'].values[0]} | 🔍 {df_pacientes[df_pacientes['ID_Documento']==x]['Procedimiento'].values[0]}",
                    key="selector_pacientes_dinamico"
                )
        
            with col_botones:
                if st.button("🔄 Actualizar", help="Actualizar la bandeja manualmente", use_container_width=True):
                    st.rerun()
                    
                if st.button("🗑️ Eliminar", help="Borra forzosamente al paciente actual de la bandeja", use_container_width=True):
                    if paciente_seleccionado:
                        db.collection("encuestas").document(paciente_seleccionado).delete()
                        st.session_state.paciente_seleccionado = None
                        st.session_state.doc_completo = {}
                        st.rerun()
                        
                if st.button("🧹 Limpiar", help="Elimina el historial oculto de pacientes YA validados", use_container_width=True):
                    validados = db.collection("encuestas").where("estado_validacion", "==", "VALIDADO").stream()
                    for doc in validados:
                        db.collection("encuestas").document(doc.id).delete()
                    st.rerun()
        
            # 5. Actualizar sesión al cambiar el selector
            if paciente_seleccionado != st.session_state.get('paciente_seleccionado'):
                st.session_state.paciente_seleccionado = paciente_seleccionado
                doc_data = db.collection("encuestas").document(paciente_seleccionado).get().to_dict()
                st.session_state.doc_completo = doc_data if doc_data else {}
                st.rerun()
        
        # --- LLAMADO AL FLUJO NORMAL ---
        filtrar_y_sincronizar_pacientes()
        # 🛡️ [AQUÍ VA EL GUARDIA DE SEGURIDAD]
        if "ultimo_paciente_procesado" not in st.session_state:
            st.session_state.ultimo_paciente_procesado = None
        
        # Si el paciente en sesión cambió, limpiamos la memoria ANTES de pintar el resto de la interfaz
        if st.session_state.ultimo_paciente_procesado != st.session_state.get('paciente_seleccionado'):
            st.session_state.registro_insumos_final = {}
            st.session_state.registro_acceso_vascular = {}
            st.session_state.insumos_sesion = []
            st.session_state.ultimo_paciente_procesado = st.session_state.get('paciente_seleccionado')
        if st.session_state.get("doc_completo") is not None:
            paciente_seleccionado = st.session_state.paciente_seleccionado
            doc_completo = st.session_state.doc_completo
        
    st.divider()

elif st.session_state.vista_actual == "rescate":
    # =============================================================================
    # 🧠 INTERFAZ DEL MOTOR DE RESCATE (SÓLO LISTA Y REDIRIGE A LA PRINCIPAL)
    # =============================================================================
    st.title("🚑 Historial de Pacientes Validados")
    st.markdown("---")
    st.caption("Visualizando pacientes validados en las últimas 48 horas.")

    ahora = datetime.now(tz_chile)
    listado_validados = []
    
    try:
        docs_ref = db.collection("encuestas").where("estado_validacion", "==", "VALIDADO").stream()
        for doc in docs_ref:
            data = doc.to_dict()
            fecha_raw = data.get("fecha_examen") or data.get("fecha") or data.get("Fecha")
            
            es_reciente = False
            if fecha_raw:
                try:
                    if hasattr(fecha_raw, 'to_datetime'):
                        dt_exam = fecha_raw.to_datetime().astimezone(tz_chile)
                    else:
                        dt_exam = tz_chile.localize(datetime.strptime(str(fecha_raw)[:10], '%Y-%m-%d'))
                    
                    if (ahora - dt_exam).days <= 2:
                        es_reciente = True
                except:
                    es_reciente = True 
            else:
                es_reciente = True
                
            if es_reciente:
                listado_validados.append({
                    "id": doc.id,
                    "nombre": data.get("nombre", "Sin Nombre"),
                    "rut": data.get("rut", "S/R"),
                    "procedimiento": data.get("procedimiento", "No especificado"),
                    "datos_completos": data
                })
    except Exception as e:
        st.error(f"🚨 Error de conexión: {e}")

    if not listado_validados:
        st.success("✅ No existen registros validados dentro del umbral de las últimas 48 horas.")
    else:
        df_validados = pd.DataFrame(listado_validados)
        paciente_id_rescate = st.selectbox(
            "🔎 Seleccione el examen validado que requiere rectificación:",
            options=list(df_validados["id"]),
            format_func=lambda x: f"👤 {df_validados[df_validados['id']==x]['nombre'].values[0]} | 🔹 RUT: {df_validados[df_validados['id']==x]['rut'].values[0]} | 🔍 {df_validados[df_validados['id']==x]['procedimiento'].values[0]}"
        )

        if paciente_id_rescate:
            registro_sel = next(item for item in listado_validados if item["id"] == paciente_id_rescate)
            
            st.markdown("### 📋 Acción Requerida")
            st.info(f"Ha seleccionado al paciente **{registro_sel['nombre']}**. Para realizar modificaciones o enmiendas, debe reabrir la ficha clínica.")
            
            # 🔥 AQUÍ ESTÁ LA MODIFICACIÓN CRÍTICA DEL BOTÓN: Activamos la bandera de enmienda activa
            if st.button("✏️ REABRIR FICHA EN LA PANTALLA PRINCIPAL (MODO ENMIENDA)", use_container_width=True, key=f"btn_rescate_{paciente_id_rescate}"):
                datos_paciente = registro_sel["datos_completos"]
                datos_paciente["es_enmienda"] = True
                
                st.session_state.doc_completo = datos_paciente
                st.session_state.paciente_seleccionado = paciente_id_rescate
                st.session_state.modo_enmienda_activo = True  # <-- ESTA ES LA LLAVE MAESTRA
                st.session_state.vista_actual = "principal"
                st.rerun()    

# =============================================================================
# 📄 MÓDULO DE EMISIÓN DE CERTIFICADOS INSTITUCIONALES (NORTE IMAGEN)
# =============================================================================
elif st.session_state.vista_actual == "certificados":
    # 1. Definimos la clase PDF AQUÍ ADENTRO para no romper la estructura de Python
    from fpdf import FPDF
    import tempfile
    import os
    
    # 1. CLASE PDF CON DISEÑO ABSOLUTO NORTE IMAGEN (CERTIFICADOS)
    class PDF_Certificado(FPDF):
        def __init__(self, tipo_documento, rut_paciente):
            super().__init__()
            self.tipo_documento = tipo_documento
            self.rut_paciente = rut_paciente
            
            # Autogeneración de metadatos de seguridad (Fecha y UUID)
            from datetime import datetime
            import pytz
            import uuid
            tz_chile = pytz.timezone('America/Santiago')
            self.fecha_emision = datetime.now(tz_chile).strftime("%d/%m/%Y %H:%M")
            self.id_verificacion = str(uuid.uuid4().hex)[:10].upper()

        def clean_txt(self, texto):
            """Limpia caracteres para que FPDF no explote con acentos"""
            return str(texto).encode('latin-1', 'replace').decode('latin-1')

        def header(self):
            # Logo Institucional a la izquierda
            if os.path.exists("logoNI.png"):
                self.image("logoNI.png", 10, 8, 45)
            
            # Encabezado 100% Alineado a la Derecha
            self.set_font('Arial', 'B', 14)
            self.set_text_color(128, 0, 32) # Burdeo Norte Imagen
            self.cell(0, 6, self.clean_txt(self.tipo_documento), 0, 1, 'R')
            
            self.set_font('Arial', 'B', 12)
            self.cell(0, 6, 'DOCUMENTO INSTITUCIONAL', 0, 1, 'R')
            
            self.set_font('Arial', 'B', 14)
            self.cell(0, 7, 'RESONANCIA MAGNETICA', 0, 1, 'R')
            
            # Fecha dinámica inyectada bajo el bloque derecho
            self.set_font('Arial', 'B', 9)
            self.set_text_color(100, 100, 100) # Gris elegante
            self.cell(0, 5, self.clean_txt(f'Fecha de certificado: {self.fecha_emision}'), 0, 1, 'R')
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 7)
            self.set_text_color(150, 150, 150)
            
            texto_pie = f"Certificado Digital Norte Imagen - RM: {self.fecha_emision} - Paciente RUT: {self.rut_paciente} - VALIDADO TM."
            self.cell(0, 10, self.clean_txt(texto_pie), 0, 0, 'L')
            
            # Sello de veracidad inyectado junto a la numeración
            self.cell(0, 10, f"Pag. {self.page_no()}/{{nb}} | ID VERIFICACION: {self.id_verificacion}", 0, 0, 'R')

    # Función interna para centrar la firma
    def estampar_firma_tm(pdf_obj, datos_db):
        ruta_firma_storage = datos_db.get("firma_profesional_img")
        prof_nombre = datos_db.get("profesional_nombre", "Profesional a cargo").title()
        prof_sis = datos_db.get("profesional_registro", "S/R")
        
        pdf_obj.ln(15)
        y_firma = pdf_obj.get_y()
        
        # Intentar descargar la firma desde Firebase
        ruta_firma_local = None
        if ruta_firma_storage:
            try:
                blob_firma = bucket.blob(ruta_firma_storage)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                    blob_firma.download_to_filename(tmp_img.name)
                    ruta_firma_local = tmp_img.name
                
                # Insertar imagen centrada (A4 width = 210. Image width = 45. Center X = 82.5)
                pdf_obj.image(ruta_firma_local, 82.5, y_firma, 45, 12)
            except Exception as e:
                print(f"Error descargando firma TM: {e}")

        # Textos de la firma superpuestos/debajo de la imagen
        pdf_obj.set_y(y_firma + 8)
        pdf_obj.set_font('Arial', '', 10)
        pdf_obj.set_text_color(0, 0, 0)
        pdf_obj.cell(0, 4, prof_nombre, 0, 1, 'C')
        pdf_obj.cell(0, 4, "________________________________________", 0, 1, 'C')
        
        pdf_obj.set_font('Arial', 'B', 8)
        pdf_obj.cell(0, 4, "FIRMA PROFESIONAL A CARGO", 0, 1, 'C')
        pdf_obj.set_font('Arial', '', 8)
        pdf_obj.cell(0, 4, "Tecnologo Medico en Imagenologia", 0, 1, 'C')
        pdf_obj.cell(0, 4, "Esp. Resonancia Magnetica", 0, 1, 'C')
        pdf_obj.cell(0, 4, f"Registro SIS: {prof_sis}", 0, 1, 'C')
        
        # Limpieza del archivo temporal
        if ruta_firma_local and os.path.exists(ruta_firma_local):
            try: os.unlink(ruta_firma_local)
            except: pass

    # 2. RENDERIZADO DE LA PANTALLA UI
    st.title("📄 Emisión de Certificados y Sugerencias")
    st.markdown("---")
    st.caption("Visualizando pacientes con atención registrada en las últimas 48 horas.")

    ahora = datetime.now(tz_chile)
    listado_cert = []
    
    try:
        docs_ref_cert = db.collection("encuestas").where("estado_validacion", "==", "VALIDADO").stream()
        for doc in docs_ref_cert:
            data = doc.to_dict()
            fecha_raw = data.get("fecha_validacion")
            if fecha_raw:
                try:
                    dt_val = datetime.strptime(fecha_raw, "%d/%m/%Y %H:%M:%S").astimezone(tz_chile)
                    if (ahora - dt_val).days <= 2:
                        listado_cert.append({
                            "id": doc.id,
                            "nombre": data.get("nombre", "Sin Nombre"),
                            "rut": data.get("rut", "S/R"),
                            "procedimiento": data.get("procedimiento", "No especificado"),
                            "datos_completos": data
                        })
                except Exception:
                    pass
    except Exception as e:
        st.error(f"🚨 Error conectando a la base de datos: {e}")

    if not listado_cert:
        st.info("No hay pacientes validados dentro de las últimas 48 horas para emitir certificados.")
    else:
        df_cert = pd.DataFrame(listado_cert)
        paciente_id_cert = st.selectbox(
            "🔎 Seleccione el paciente para emitir documento:",
            options=list(df_cert["id"]),
            format_func=lambda x: f"👤 {df_cert[df_cert['id']==x]['nombre'].values[0]} | 🔹 RUT: {df_cert[df_cert['id']==x]['rut'].values[0]} | 🔍 {df_cert[df_cert['id']==x]['procedimiento'].values[0]}",
            key="selector_modulo_certificados"
        )

        if paciente_id_cert:
            registro_sel = next(item for item in listado_cert if item["id"] == paciente_id_cert)
            datos_completos_db = registro_sel["datos_completos"]
            
            st.markdown(f"### Opciones para: **{registro_sel['nombre']}**")
            
            tab1, tab2, tab3, tab4 = st.tabs([
                "🏥 1. Certificado de Atención", 
                "👨🏻‍⚕️ 2. Sugerencia al Derivador", 
                "🕰️ 3. Reingreso Histórico",
                "📝 4. Documentos por Firmar"
            ])
            
            # ---------------------------------------------------------
            # PESTAÑA 1: ATENCIÓN
            # ---------------------------------------------------------
            with tab1:
                st.markdown("#### 🏥 Datos del Certificado de Asistencia")
                
                # --- NUEVOS CAMPOS: DESTINATARIO ("DIRIGIDO A") ---
                st.markdown("##### 👤 Dirigido a (Opcional):")
                col_d1, col_d2, col_d3 = st.columns(3)
                dest_nombre = col_d1.text_input("Nombre del médico derivador (ej. Juan Pérez)", key=f"dest_nom_{paciente_id_cert}")
                dest_cargo = col_d2.text_input("Cargo (ej. Médico Tratante)", key=f"dest_car_{paciente_id_cert}")
                dest_empresa = col_d3.text_input("Institución (ej. Hospital Regional)", key=f"dest_emp_{paciente_id_cert}")
                
                st.markdown("##### 🕒 Horarios de Atención:")
                col_h1, col_h2 = st.columns(2)
                hora_llegada = col_h1.time_input("Hora de Llegada (Cita)", value=None, key=f"hllegada_{paciente_id_cert}")
                hora_salida = col_h2.time_input("Hora de Término (Salida)", value=None, key=f"hsalida_{paciente_id_cert}")
                
                incluir_acompanante = st.checkbox("Incluir constancia de acompañante", key=f"chk_acomp_{paciente_id_cert}")
                nombre_acompanante = ""
                parentesco_acompanante = ""
                if incluir_acompanante:
                    col_a1, col_a2 = st.columns(2)
                    nombre_acompanante = col_a1.text_input("Nombre completo del acompañante:", key=f"txt_acomp_{paciente_id_cert}")
                    parentesco_acompanante = col_a2.text_input("Parentesco:", key=f"txt_par_{paciente_id_cert}")
                    
                st.markdown("<br>", unsafe_allow_html=True)
                
                if puede_editar_y_firmar():
                    # -------------------------------------------------------------
                    # VISTA TM / COORDINADOR: Genera y firma directo
                    # -------------------------------------------------------------
                    if st.button("📄 GENERAR CERTIFICADO Y FIRMAR", use_container_width=True, type="primary", key=f"btn_cert_{paciente_id_cert}"):
                        if hora_llegada and hora_salida:
                            # >>> AQUÍ VA TODO TU CÓDIGO ORIGINAL QUE COMPILA EL PDF Y LE PEGA LA FIRMA DEL TM (estampar_firma_tm)
                            pass # Mantén tu código original de compilación de PDF aquí
                        else:
                            st.warning("⚠️ Es obligatorio ingresar la hora de llegada y de salida.")
                else:
                    # -------------------------------------------------------------
                    # VISTA SECRETARIA / TENS: Genera PDF Blanco o Envía a Bandeja
                    # -------------------------------------------------------------
                    st.info("Su perfil requiere autorización del profesional para la validez legal de este documento.")
                    col_sec1, col_sec2 = st.columns(2)
                    
                    if col_sec1.button("📄 DESCARGAR SIN FIRMA (Borrador)", use_container_width=True, key=f"btn_sec_nofirma_{paciente_id_cert}"):
                         if hora_llegada and hora_salida:
                             # >>> AQUÍ PEGARIAS LA MISMA COMPILACIÓN DEL PDF PERO BORRANDO LA LÍNEA: estampar_firma_tm(pdf, datos_completos_db)
                             pass 
                         else:
                             st.warning("⚠️ Es obligatorio ingresar la hora de llegada y de salida.")
                             
                    # Selección de TM para envío a firma
                    tms_disponibles = []
                    try:
                        usuarios_activos = db.collection("usuarios").where("activo", "==", True).stream()
                        for u in usuarios_activos:
                            u_data = u.to_dict()
                            if u_data.get('rol') in ['tm', 'tm_coordinador', 'owner']:
                                tms_disponibles.append(u_data['nombre'])
                    except: pass
                    
                    tm_destinatario = col_sec2.selectbox("Seleccionar Profesional Revisor:", tms_disponibles, key=f"sel_tm_{paciente_id_cert}")
                    
                    if col_sec2.button("📬 ENVIAR A FIRMA DIGITAL", use_container_width=True, key=f"btn_sec_enviar_{paciente_id_cert}"):
                        if hora_llegada and hora_salida and tm_destinatario:
                            # Guardamos la estructura del certificado pendiente en Firestore
                            doc_pendiente = {
                                "tipo_doc": "Certificado de Atención",
                                "paciente_id": paciente_id_cert,
                                "paciente_nombre": registro_sel['nombre'],
                                "paciente_rut": registro_sel['rut'],
                                "destinatario_medico": dest_nombre,
                                "hora_llegada": hora_llegada.strftime('%H:%M'),
                                "hora_salida": hora_salida.strftime('%H:%M'),
                                "acompanante": nombre_acompanante if incluir_acompanante else "",
                                "tm_asignado": tm_destinatario,
                                "solicitante": st.session_state.current_user['nombre'],
                                "estado": "Pendiente de Firma",
                                "timestamp": datetime.now(tz_chile).strftime("%d/%m/%Y %H:%M:%S")
                            }
                            db.collection("certificados_pendientes").add(doc_pendiente)
                            st.success(f"✅ Solicitud enviada a la bandeja de {tm_destinatario}.")
                        else:
                            st.warning("Faltan horas de registro o TM asignado.")
                            pdf.add_page()
                            
                            # TÍTULO CENTRADO DE INICIO DE HOJA
                            pdf.set_font('Arial', 'B', 12)
                            pdf.set_text_color(0, 0, 0)
                            pdf.cell(0, 8, "CERTIFICADO DE ASISTENCIA", 0, 1, 'C')
                            pdf.ln(5)
                            
                            # ESTRUCTURA "ESTIMADO SR..."
                            if dest_nombre:
                                pdf.set_font('Arial', '', 11)
                                txt_cargo = f", {dest_cargo}" if dest_cargo else ""
                                txt_empresa = f" perteneciente a {dest_empresa}" if dest_empresa else ""
                                saludo = f"Estimado Dr(a). {dest_nombre}{txt_cargo}{txt_empresa}:"
                                pdf.multi_cell(0, 6, pdf.clean_txt(saludo))
                                pdf.ln(5)
                            
                            # CUERPO CLÍNICO EXACTO
                            pdf.set_font('Arial', '', 11)
                            fecha_hoy_cuerpo = datetime.now(tz_chile).strftime("%d/%m/%Y")
                            
                            texto_principal = f"Se extiende el presente documento para dejar constancia y certificar de que el paciente {registro_sel['nombre']}, con número de RUT {registro_sel['rut']}, asistió a nuestro centro diagnóstico para realizarse un estudio de {registro_sel['procedimiento']} el día {fecha_hoy_cuerpo}."
                            pdf.multi_cell(0, 6, pdf.clean_txt(texto_principal))
                            pdf.ln(5)
                            
                            # Grilla de horas elegante
                            pdf.set_font('Arial', 'B', 11)
                            pdf.cell(60, 8, "Hora de llegada a la unidad:", 0, 0)
                            pdf.set_font('Arial', '', 11)
                            pdf.cell(0, 8, hora_llegada.strftime('%H:%M'), 0, 1)
                            
                            pdf.set_font('Arial', 'B', 11)
                            pdf.cell(60, 8, "Hora de salida de la unidad:", 0, 0)
                            pdf.set_font('Arial', '', 11)
                            pdf.cell(0, 8, hora_salida.strftime('%H:%M'), 0, 1)
                            
                            if incluir_acompanante and nombre_acompanante:
                                pdf.ln(5)
                                txt_par = f" ({parentesco_acompanante})" if parentesco_acompanante else ""
                                texto_acomp = f"Se deja constancia formal que el paciente asistió en compañía de su familiar o tutor: {nombre_acompanante}{txt_par}."
                                pdf.multi_cell(0, 6, pdf.clean_txt(texto_acomp))
                            
                            # Estampar la firma del TM desde Firebase (Centrada intacta)
                            estampar_firma_tm(pdf, datos_completos_db)
                            
                            try:
                                pdf_bytes = pdf.output(dest='S').encode('latin1')
                            except AttributeError:
                                pdf_bytes = bytes(pdf.output())
                                
                            st.session_state[f'pdf_atencion_bytes_{paciente_id_cert}'] = pdf_bytes
                    else:
                        st.warning("⚠️ Es obligatorio ingresar la hora de llegada y de salida.")
                
                if f'pdf_atencion_bytes_{paciente_id_cert}' in st.session_state:
                    st.success("✅ Certificado validado y generado exitosamente.")
                    st.download_button(
                        label="⬇️ DESCARGAR CERTIFICADO OFICIAL (PDF)",
                        data=st.session_state[f'pdf_atencion_bytes_{paciente_id_cert}'],
                        file_name=f"Certificado_Atencion_{registro_sel['rut']}.pdf",
                        mime="application/pdf",
                        key=f"dl_cert_{paciente_id_cert}"
                    )

            # ---------------------------------------------------------
            # PESTAÑA 2: SUGERENCIA AL DERIVADOR
            # ---------------------------------------------------------
            with tab2:
                st.markdown("#### 👨🏻‍⚕️ Informe de Sugerencia Clínica")
                st.warning("Utilice este módulo si el paciente no pudo realizarse el estudio o si sugiere una modificación en la orden médica.")
                
                # --- NUEVOS CAMPOS: DESTINATARIO ("DIRIGIDO A") ---
                st.markdown("##### 👤 Dirigido a (Opcional):")
                col_sd1, col_sd2, col_sd3 = st.columns(3)
                dest_nombre_sug = col_sd1.text_input("Nombre del médico derivador (ej. Juan Pérez)", key=f"sug_nom_{paciente_id_cert}")
                dest_cargo_sug = col_sd2.text_input("Cargo (ej. Médico jefe de neurocirugía ó traumatólogo infantil)", key=f"sug_car_{paciente_id_cert}")
                dest_empresa_sug = col_sd3.text_input("Institución (ej. Hospital Regional o Clínica...)", key=f"sug_emp_{paciente_id_cert}")
                
                st.markdown("##### 🩺 Detalles Clínicos:")
                motivo_principal = st.selectbox(
                    "Motivo Clínico:",
                    [
                        "Seleccione un motivo...", 
                        "Claustrofobia Severa", 
                        "Funcion Renal Alterada (VFG Baja)", 
                        "Incompatibilidad de Implante (Bioseguridad)", 
                        "Paciente no coopera / Movimiento constante",
                        "Incapacidad para contener la respiracion",
                        "Otro motivo"
                    ],
                    key=f"motivo_sug_{paciente_id_cert}"
                )
                
                texto_sugerencia = st.text_area(
                    "Detalle de la sugerencia para el Médico Derivador:", 
                    placeholder="Ej: Estimado doctor Juan Pérez, debido a cuadro de claustrofobia durante la realización...",
                    height=150,
                    key=f"texto_sug_{paciente_id_cert}"
                )
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                if st.button("📄 GENERAR INFORME DE SUGERENCIA", use_container_width=True, type="primary", key=f"btn_sug_{paciente_id_cert}"):
                    if motivo_principal != "Seleccione un motivo..." and texto_sugerencia.strip():
                        with st.spinner("Compilando formato institucional y rescatando firma..."):
                            pdf = PDF_Certificado('SUGERENCIA AL DERIVADOR', registro_sel['rut'])
                            pdf.alias_nb_pages()
                            pdf.add_page()
                            
                            # TÍTULO CENTRADO DE INICIO DE HOJA
                            pdf.set_font('Arial', 'B', 12)
                            pdf.set_text_color(0, 0, 0)
                            pdf.cell(0, 8, "SUGERENCIA AL DERIVADOR", 0, 1, 'C')
                            pdf.ln(5)
                            
                            # ESTRUCTURA "ESTIMADO SR..."
                            if dest_nombre_sug:
                                pdf.set_font('Arial', '', 11)
                                txt_cargo = f", {dest_cargo_sug}" if dest_cargo_sug else ""
                                txt_empresa = f" perteneciente a {dest_empresa_sug}" if dest_empresa_sug else ""
                                saludo = f"Estimado Sr(a). {dest_nombre_sug}{txt_cargo}{txt_empresa}:"
                                pdf.multi_cell(0, 6, pdf.clean_txt(saludo))
                                pdf.ln(5)

                                # 2. Inyección del nuevo texto fijo
                                pdf.set_font('Arial', '', 11) # Aseguramos mantener el mismo estilo
                                texto_cert = "Se emite el presente certificado asociado a:"
                                pdf.multi_cell(0, 6, pdf.clean_txt(texto_cert))
                                
                                # 3. Espacio final antes de que comience tu renderizado de datos
                                pdf.ln(10)
                            
                            # Cuerpo original
                            pdf.set_font('Arial', 'B', 11)
                            pdf.cell(30, 6, "Paciente:", 0, 0)
                            pdf.set_font('Arial', '', 11)
                            pdf.cell(0, 6, pdf.clean_txt(registro_sel['nombre']), 0, 1)
                            
                            pdf.set_font('Arial', 'B', 11)
                            pdf.cell(30, 6, "RUT:", 0, 0)
                            pdf.set_font('Arial', '', 11)
                            pdf.cell(0, 6, pdf.clean_txt(registro_sel['rut']), 0, 1)
                            
                            pdf.set_font('Arial', 'B', 11)
                            pdf.cell(30, 6, "Examen:", 0, 0)
                            pdf.set_font('Arial', '', 11)
                            pdf.multi_cell(0, 6, pdf.clean_txt(registro_sel['procedimiento']))
                            pdf.ln(5)
                            
                            pdf.set_fill_color(240, 240, 240)
                            pdf.set_font('Arial', 'B', 11)
                            pdf.cell(0, 8, pdf.clean_txt(f" Motivo clinico: {motivo_principal}"), 0, 1, fill=True)
                            pdf.ln(4)
                            
                            pdf.set_font('Arial', 'B', 11)
                            pdf.cell(0, 6, "Antecedentes y sugerencia del profesional:", 0, 1)
                            pdf.set_font('Arial', '', 11)
                            pdf.multi_cell(0, 6, pdf.clean_txt(texto_sugerencia))
                            pdf.ln(5)
                            
                            # Estampar la firma del TM desde Firebase (Centrada intacta)
                            estampar_firma_tm(pdf, datos_completos_db)
                            
                            try:
                                pdf_bytes = pdf.output(dest='S').encode('latin1')
                            except AttributeError:
                                pdf_bytes = bytes(pdf.output())
                                
                            st.session_state[f'pdf_sugerencia_bytes_{paciente_id_cert}'] = pdf_bytes
                    else:
                        st.warning("⚠️ Debe seleccionar un motivo y redactar la sugerencia.")
                
                if f'pdf_sugerencia_bytes_{paciente_id_cert}' in st.session_state:
                    st.success("✅ Informe validado y generado exitosamente.")
                    st.download_button(
                        label="⬇️ DESCARGAR INFORME OFICIAL (PDF)",
                        data=st.session_state[f'pdf_sugerencia_bytes_{paciente_id_cert}'],
                        file_name=f"Sugerencia_Clinica_{registro_sel['rut']}.pdf",
                        mime="application/pdf",
                        key=f"dl_sug_{paciente_id_cert}"
                    )
                    
                    
            with tab3:
                st.markdown("<br>", unsafe_allow_html=True)
                st.info("🛠️ **Módulo en Desarrollo.** Esta sección permitirá cargar y adjuntar consentimientos PDF antiguos firmados en papel, exclusivamente para pacientes de historial.")

            # ---------------------------------------------------------
            # PESTAÑA 4: DOCUMENTOS POR FIRMAR
            # ---------------------------------------------------------
            with tab4:
                st.markdown("#### 📝 Bandeja de Documentos por Firmar")
                
                if puede_editar_y_firmar():
                    st.info(f"Mostrando documentos asignados a: **{st.session_state.current_user['nombre']}**")
                    try:
                        docs_pendientes = db.collection("certificados_pendientes").where("tm_asignado", "==", st.session_state.current_user['nombre']).where("estado", "==", "Pendiente de Firma").stream()
                        
                        hay_pendientes = False
                        for doc_p in docs_pendientes:
                            hay_pendientes = True
                            d_p = doc_p.to_dict()
                            
                            with st.container():
                                st.markdown(f"**Paciente:** {d_p['paciente_nombre']} | **Documento:** {d_p['tipo_doc']} | **Solicitado por:** {d_p['solicitante']}")
                                col_p1, col_p2, col_p3 = st.columns(3)
                                
                                if col_p1.button("🔍 Firmar y Aprobar", key=f"apr_{doc_p.id}"):
                                    # Al aprobar, cambiamos estado y se compilaría el PDF final
                                    db.collection("certificados_pendientes").document(doc_p.id).update({"estado": "Firmado"})
                                    st.success("✅ Documento firmado digitalmente.")
                                    st.rerun()
                                    
                                if col_p2.button("✏️ Modificar", key=f"mod_{doc_p.id}"):
                                    st.warning("Utilice el generador normal para recrear y sobreescribir este documento.")
                                    
                                if col_p3.button("🔄 Devolver a Solicitante", key=f"dev_{doc_p.id}"):
                                    db.collection("certificados_pendientes").document(doc_p.id).update({"estado": "Devuelto para corrección"})
                                    st.error("Documento devuelto.")
                                    st.rerun()
                                st.divider()
                                
                        if not hay_pendientes:
                            st.success("Bandeja limpia. No hay documentos pendientes de firma.")
                            
                    except Exception as e:
                        st.error(f"Error consultando bandeja: {e}")
                else:
                    st.info("Aquí podrá ver el estado de los documentos que usted ha enviado a firma.")
                    try:
                        mis_solicitudes = db.collection("certificados_pendientes").where("solicitante", "==", st.session_state.current_user['nombre']).stream()
                        for doc_s in mis_solicitudes:
                            d_s = doc_s.to_dict()
                            estado_color = "🟢" if d_s['estado'] == "Firmado" else "🟡" if d_s['estado'] == "Pendiente de Firma" else "🔴"
                            st.write(f"{estado_color} **{d_s['paciente_nombre']}** - {d_s['tipo_doc']} - TM Asignado: {d_s['tm_asignado']} - Estado: {d_s['estado']}")
                    except: pass
                
# =========================================================================
# 🛑 CORTAFUEGOS DE RUTAS (SOLUCIÓN ULTRAMEGA PRO)
# =========================================================================
# Si no estamos en la vista principal, detenemos la ejecución aquí para
# evitar que el panel de validación se filtre en otras pestañas.
if st.session_state.get("vista_actual", "principal") != "principal":
    st.stop()

# =========================================================================
# 🛑 BARRERA DE SEGURIDAD ABSOLUTA (ÚNICA Y DEFINITIVA)
# =========================================================================
st.divider()

# 1. Recuperación segura desde el estado de la sesión
doc_completo = st.session_state.get('doc_completo', {})
paciente_seleccionado = st.session_state.get('paciente_seleccionado')

# 2. Si no hay un documento cargado en memoria, detenemos la ejecución aquí.
if not doc_completo:
    st.stop() # Adiós NameErrors. Todo se detiene de forma segura.

# 3. Asignación segura y Extracción Inteligente
datos_doc = doc_completo
form_interno = datos_doc.get('form', datos_doc.get('encuesta', datos_doc))
if not isinstance(form_interno, dict):
    form_interno = datos_doc

# 4. Declaración forzosa de variables clínicas para evitar errores en PDF y UI
det_bio = form_interno.get('detalle_bioseguridad', form_interno.get('det_bio', 'Sin observaciones'))

try:
    edad_raw = form_interno.get('edad', form_interno.get('Edad', datos_doc.get('edad', 0)))
    edad_int = int(float(str(edad_raw).strip()))
except:
    edad_int = 0

# Variables clínicas (Forzamos booleano para que el PDF no falle al evaluar)
es_embarazo = bool(form_interno.get('embarazo', False))
es_lactancia = bool(form_interno.get('lactancia', False))
es_claustrofobia = bool(form_interno.get('claustrofobia', False))

# Rol para los botones de aprobación
es_admin_role = st.session_state.get('user_role') == 'admin'

# =========================================================================
# A partir de aquí, el resto de tu lógica de generación de PDF es segura.
# =========================================================================

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
    datos_doc['tutor_nombre'] = tutor_nombre
    datos_doc['tutor_rut'] = tutor_rut
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

datos_doc['nota_marcapaso'] = nota_marcapaso
datos_doc['nota_implante'] = nota_implante

# 🚨 Triaje de Riesgos Clínicos
clin_alergico = form_interno.get('alergico', form_interno.get('clin_alergico', 'No'))
detalle_alergia_fb = form_interno.get('alergias_detalles', '').strip()

if str(clin_alergico).strip().upper() in ["SI", "SÍ"]: 
    if detalle_alergia_fb:
        nota_alergico = f"⚠️ ALERGIAS: {detalle_alergia_fb}. Evaluar premedicación."
    else:
        nota_alergico = "Evaluar su relación al medio de contraste y necesidad de premedicación."
else:
    nota_alergico = ""

clin_dialisis = form_interno.get('dialisis', form_interno.get('clin_dialisis', 'No'))
clin_renal = form_interno.get('renal', form_interno.get('clin_renal', 'No'))
clin_embarazo = form_interno.get('embarazo', form_interno.get('clin_embarazo', 'No'))
clin_claustro = form_interno.get('claustrofobia', form_interno.get('clin_claustro', 'No'))
clin_lactancia = form_interno.get('lactancia', form_interno.get('clin_lactancia', 'No'))

nota_dialisis = "No se debe inyectar medio de contraste basado en Gadolinio." if str(clin_dialisis).strip().upper() in ["SI", "SÍ"] else ""
nota_renal = "Se debe considerar la VFG para la administración de medio de contraste." if str(clin_renal).strip().upper() in ["SI", "SÍ"] else ""
nota_embarazo = "Precaución, paciente de alto cuidado." if str(clin_embarazo).strip().upper() in ["SI", "SÍ"] else ""
nota_claustro = "Puede requerir atención personalizada." if str(clin_claustro).strip().upper() in ["SI", "SÍ"] else ""
nota_lactancia = "Consultar si junto leche materna o cuenta con alguna adicional." if str(clin_lactancia).strip().upper() in ["SI", "SÍ"] else ""

datos_doc.update({
    'nota_alergico': nota_alergico,
    'nota_dialisis': nota_dialisis,
    'nota_renal': nota_renal,
    'nota_embarazo': nota_embarazo,
    'nota_claustro': nota_claustro,
    'nota_lactancia': nota_lactancia
})

# 🧪 Parámetros Métricos
creatinina_val = form_interno.get('creatinina', datos_doc.get('creatinina', 'N/A'))
peso_val = form_interno.get('peso', datos_doc.get('peso', 'N/A'))
talla_val = form_interno.get('talla', datos_doc.get('talla', 0.0))

# Variables de cálculo (seguras)
talla_profesional = float(talla_val) if str(talla_val).replace('.','',1).isdigit() else 0.0
peso_profesional = float(peso_val) if str(peso_val).replace('.','',1).isdigit() else 0.0
creatinina_profesional = float(creatinina_val) if str(creatinina_val).replace('.','',1).isdigit() else 0.0

vfg_valor = form_interno.get('vfg', datos_doc.get('vfg', 0.0))
is_contraste_visual = datos_doc.get('tiene_contraste', form_interno.get('tiene_contraste', False)) in [True, "Sí", "SI", "si", "Si"]
procedimiento_val_visual = datos_doc.get('procedimiento', form_interno.get('procedimiento', 'No especificado'))
ip_cliente = datos_doc.get('ip_dispositivo', datos_doc.get('ip', form_interno.get('ip_dispositivo', form_interno.get('ip', 'No detectada'))))

st.title("🏥 Panel de Validación Profesional")

st.divider()
# =====================================================================
# 🚨 ALERTA VISUAL Y REGISTRO LEGAL: DETECCIÓN DE MODO ENMIENDA
# =====================================================================
if datos_doc.get("es_enmienda"):
    st.markdown(f'''
        <div style="background-color: #ffe6e6; border-left: 6px solid #FF0000; padding: 16px; border-radius: 5px; margin-bottom: 15px;">
            <h3 style="margin: 0 0 5px 0; color: #FF0000;">🛑 MODO ENMIENDA LEY 20.584 ACTIVO</h3>
            <p style="margin: 0; color: #333333; font-size: 15px;">
                Usted ha reabierto la ficha de un paciente ya validado. Todas las modificaciones realizadas aquí y la nueva firma anularán el documento anterior.
            </p>
        </div>
    ''', unsafe_allow_html=True)
    
    # 🧠 CAPTURA FALTANTE: La justificación que viajará al PDF y Firebase
    justificacion = st.text_area(
        "📝 Justificación Clínica Obligatoria para la Enmienda:", 
        value=datos_doc.get('adendum_texto', ''), 
        help="Este motivo se imprimirá legalmente en la cabecera roja y el pie de página del PDF definitivo."
    )
    datos_doc['adendum_texto'] = justificacion
    
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
# 🟢 RENDERIZADO EN 2 COLUMNAS (CORREGIDO Y REORGANIZADO)
# =====================================================================
c1, c2 = st.columns(2)

with c1:
    with st.expander("👤 1. FICHA CLÍNICA: DATOS DEL PACIENTE", expanded=True):
        
        # --- A. INFORMACIÓN CLÍNICA PRINCIPAL ---
        nombre_procedimiento = datos_doc.get('procedimiento', 'No especificado')
        st.info(f"**EXAMEN A REALIZAR:** {nombre_procedimiento.upper()}")
        
        # --- B. DATOS PERSONALES (Columnas) ---
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Nombre:** {datos_doc.get('nombre', 'N/A')}")
            
            # --- NUEVA LÍNEA: PROCEDENCIA ---
            procedencia_pac = datos_doc.get('procedencia', 'Ambulatorio')
            unidad_pac = datos_doc.get('unidad_procedencia', '')
            if procedencia_pac.upper() == 'HOSPITALIZADO' and unidad_pac:
                st.write(f"**Procedencia:** {procedencia_pac} ({unidad_pac})")
            else:
                st.write(f"**Procedencia:** {procedencia_pac}")
            st.write(f"**Teléfono:** {datos_doc.get('telefono', 'N/A')}")
            st.write(f"**Email:** {datos_doc.get('email', 'N/A')}")
            
            # --- CÁLCULO DE EDAD CORREGIDO Y SEGURO ---
        fecha_nac = datos_doc.get('fecha_nac') 
        # --- CÁLCULO DE EDAD CORREGIDO Y SEGURO (MÉTODO VISUAL) ---
        fecha_nac = datos_doc.get('fecha_nac') 
        edad_str = calcular_edad_visual_completa(fecha_nac) # Llama a la nueva función visual
        st.write(f"**Edad:** {edad_str}") # IMPRESIÓN ÚNICA

        with col2:
            # Lógica de identificación (RUT vs Pasaporte)
            if datos_doc.get('sin_rut'):
                st.write(f"**Documento ({datos_doc.get('tipo_doc', 'Pasaporte')}):** {datos_doc.get('num_doc', 'N/A')}")
            else:
                st.write(f"**RUT:** {datos_doc.get('rut', 'N/A')}")
            
            # Muestra el género formateado exacto que preparó app.py para el PDF institucional
            genero_visual = datos_doc.get('sexo', datos_doc.get('genero', 'N/A'))
            st.write(f"**Identidad / Sexo Registrado:** {genero_visual}")

        # --- C. REPRESENTANTE LEGAL (Tutor) ---
        # Determinamos si es menor usando la función universal de edad para evitar quiebres
        from datetime import date
        es_menor_de_edad = False
        if fecha_nac:
            try:
                # Si viene de Firestore como Timestamp
                if hasattr(fecha_nac, 'to_datetime'):
                    fecha_date = fecha_nac.to_datetime().date()
                elif isinstance(fecha_nac, str):
                    fecha_date = datetime.strptime(fecha_nac[:10].strip(), '%Y-%m-%d').date()
                else:
                    fecha_date = fecha_nac.date() if hasattr(fecha_nac, 'date') else fecha_nac
                
                # Evaluación estricta de minoría de edad (< 18 años)
                if (date.today() - fecha_date).days / 365.25 < 18:
                    es_menor_de_edad = True
            except:
                # Si falla por cualquier motivo, verificamos la llave antigua como respaldo
                try: es_menor_de_edad = int(datos_doc.get('edad', 18)) < 18
                except: es_menor_de_edad = False

        if es_menor_de_edad:
            st.markdown("---")
            
            # 1. Extracción previa de las variables de datos_doc
            nombre_t = datos_doc.get('nombre_tutor', datos_doc.get('rep_legal_nombre', 'No registrado'))
            parentesco_t = datos_doc.get('parentesco_tutor', '')
            
            if datos_doc.get('sin_rut_tutor'):
                documento_tutor = f"<b>Doc ({datos_doc.get('tipo_doc_tutor', 'Pasaporte')}):</b> {datos_doc.get('num_doc_tutor', 'N/A')}"
            else:
                documento_tutor = f"<b>RUT Tutor:</b> {datos_doc.get('rut_tutor', datos_doc.get('rep_legal_rut', 'N/A'))}"
            
            # 2. Renderizado del Cuadro Blanco Clínico Integrado
            st.markdown(f'''
                <div style="background-color: white; border-left: 6px solid #17A2B8; padding: 16px; border-radius: 5px; box-shadow: 0px 2px 5px rgba(0,0,0,0.08); margin-bottom: 15px;">
                    <p style="margin: 0 0 12px 0; color: #17A2B8; font-weight: bold; font-size: 16px;">
                        ⚠️ Datos del Representante Legal
                    </p>
                    <div style="display: flex; flex-wrap: wrap; gap: 20px; color: #333333; font-size: 15px;">
                        <div style="flex: 1; min-width: 250px;">
                            <b>Nombre:</b> {nombre_t} <span style="color: #6C757D;">({parentesco_t})</span>
                        </div>
                        <div style="flex: 1; min-width: 250px;">
                            {documento_tutor}
                        </div>
                    </div>
                </div>
            ''', unsafe_allow_html=True)

        # =====================================================================
        # 📂 ORDEN MÉDICA (VERSION PRO: CACHÉ EN RAM ACTIVADO)
        # =====================================================================
        st.markdown("---")
        st.markdown("**📄 Orden Médica**")
        
        # 1. Definimos una clave única basada en el paciente
        id_paciente_actual = paciente_seleccionado # Asumiendo que esta variable existe
        
        if "orden_memoria" not in st.session_state:
            st.session_state.orden_memoria = {"id": None, "bytes": None, "ext": None}

        ruta_orden_fb = datos_doc.get("url_orden_firebase", "")
        
        if ruta_orden_fb:
            try:
                # 2. Lógica: Si el paciente cambió, descargamos; si es el mismo, usamos lo que ya tenemos
                if st.session_state.orden_memoria["id"] != id_paciente_actual:
                    blob_orden = bucket.blob(ruta_orden_fb)
                    st.session_state.orden_memoria["bytes"] = blob_orden.download_as_bytes()
                    st.session_state.orden_memoria["ext"] = os.path.splitext(ruta_orden_fb)[1].lower()
                    st.session_state.orden_memoria["id"] = id_paciente_actual
                
                # 3. Renderizado desde la RAM (Instantáneo)
                ext = st.session_state.orden_memoria["ext"]
                if ext in ['.jpg', '.jpeg', '.png']:
                    st.image(st.session_state.orden_memoria["bytes"], caption="Orden Médica (Caché en RAM)", use_container_width=True)
                else:
                    st.download_button(
                        label="⬇️ Descargar Orden Médica (PDF)",
                        data=st.session_state.orden_memoria["bytes"],
                        file_name=f"Orden_Medica_{datos_doc.get('rut', 'Paciente')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
            except Exception as e:
                st.error("⚠️ Error al procesar la Orden Médica desde la memoria.")
        else:
            st.caption("ℹ️ Sin Orden Médica en el servidor de Firebase.")

        # Lógica de Respaldo: Google Drive (Se mantiene igual)
        url_orden_drive = datos_doc.get("url_orden_drive")
        if url_orden_drive:
            st.link_button("🔗 Ver Respaldo en Drive", url_orden_drive, use_container_width=True)
        # =====================================================================
            
    # --- B. BIOSEGURIDAD MAGNÉTICA ---
    with st.expander("🧲 2. BIOSEGURIDAD MAGNÉTICA", expanded=True):
        tiene_marcapaso = evaluar_si_no(datos_doc.get('bio_marcapaso'))
        st.write(f"**Marcapasos cardíaco:** {'🔴 SÍ' if tiene_marcapaso else '✅ NO'}")
        if tiene_marcapaso and datos_doc.get('nota_marcapaso'):
            st.warning(datos_doc.get('nota_marcapaso'))

        tiene_implantes = evaluar_si_no(datos_doc.get('bio_implantes'))
        st.write(f"**Implantes / Prótesis / Dispositivos:** {'🔴 SÍ' if tiene_implantes else '✅ NO'}")
        if tiene_implantes and datos_doc.get('nota_implante'):
            st.warning(datos_doc.get('nota_implante'))

        if tiene_implantes:
            st.markdown("---")
            st.subheader("📋 Clasificación Técnica de Seguridad")
            lista_implantes = [imp.strip() for imp in datos_doc.get('nota_implante', '').split(',')] if datos_doc.get('nota_implante') else ["Implante no especificado"]
            for implante in lista_implantes:
                st.markdown(f"**Evaluación para:** `{implante}`")
                key_estado = f"clasificacion_{implante}_{datos_doc.get('rut', 'default')}"
                if key_estado not in st.session_state:
                    st.session_state[key_estado] = None
                cols = st.columns(3, vertical_alignment="bottom")
                opciones = [("MR SAFE", "MRSAFE.png", "🟢"), ("MR CONDITIONAL", "MRCONDITIONAL.png", "🟡"), ("MR UNSAFE", "MRUNSAFE.png", "🔴")]
                for i, (nombre, archivo, color) in enumerate(opciones):
                    with cols[i]:
                        try:
                            st.image(archivo, use_container_width=True) 
                        except:
                            st.warning("Img no encontrada")
                        btn_key = f"btn_{nombre}_{implante}"
                        if st.button(f"{nombre}", key=btn_key, use_container_width=True):
                            st.session_state[key_estado] = nombre
                clasificacion_actual = st.session_state.get(key_estado, None)
                if clasificacion_actual:
                    if clasificacion_actual == "MR SAFE":
                        st.success(f"✅ Clasificación asignada: **{clasificacion_actual}**")
                    elif clasificacion_actual == "MR CONDITIONAL":
                        st.warning(f"⚠️ Clasificación asignada: **{clasificacion_actual}**")
                    elif clasificacion_actual == "MR UNSAFE":
                        st.error(f"❌ Clasificación asignada: **{clasificacion_actual}**")
                else:
                    st.info(f"⚠️ Pendiente de clasificar")

        st.markdown("---")
        st.write("**Detalle Bioseguridad (Observaciones):**")
        st.info(datos_doc.get('bio_detalle') if datos_doc.get('bio_detalle') else "Sin observaciones")

    # --- C. ANTECEDENTES CLÍNICOS ---
    with st.expander("📋 3. ANTECEDENTES CLÍNICOS", expanded=True):
        # 1. PARCHE DE ALERGIAS: Rescatar el detalle textual exacto
        tiene_alergia = evaluar_si_no(datos_doc.get('clin_alergico'))
        detalle_alergia_texto = datos_doc.get('alergias_detalles', '').strip()
        
        if tiene_alergia:
            if detalle_alergia_texto:
                alerta_alergias_final = f"⚠️ ESPECÍFICO: {detalle_alergia_texto}. Evaluar premedicación."
            else:
                alerta_alergias_final = "Evaluar su relación al medio de contraste y necesidad de premedicación."
        else:
            alerta_alergias_final = ""

        # 2. PARCHE CÁNCER: Detectar el check directo de app.py
        tiene_cancer_check = datos_doc.get('quir_cancer_check', 'No') == "Sí"
        nota_cancer_paciente = datos_doc.get('quir_cancer_detalle', '') if tiene_cancer_check else ""

        data_riesgos = {
            "Antecedente Clínico": ["Ayuno 2hrs+", "Asma", "Alergias", "Hipertensión", "Hipotiroidismo", "Diabetes", "Metformina 48h", "Insuficiencia Renal", "Diálisis", "Embarazo", "Lactancia", "Claustrofobia", "Enfermedad Oncológica (Cáncer)"],
            "Estado": [
                "✅ SÍ" if evaluar_si_no(datos_doc.get('clin_ayuno')) else "🔴 NO",
                "🔴 SÍ" if evaluar_si_no(datos_doc.get('clin_asma')) else "✅ NO",
                "🔴 SÍ" if tiene_alergia else "✅ NO",
                "🔴 SÍ" if evaluar_si_no(datos_doc.get('clin_hiperten')) else "✅ NO",
                "🔴 SÍ" if evaluar_si_no(datos_doc.get('clin_hipertiroid')) else "✅ NO",
                "🔴 SÍ" if evaluar_si_no(datos_doc.get('clin_diabetes')) else "✅ NO",
                "🔴 SÍ" if evaluar_si_no(datos_doc.get('clin_metformina')) else "✅ NO",
                "🚨 SÍ" if evaluar_si_no(datos_doc.get('clin_renal')) else "✅ NO",
                "🚨 SÍ" if evaluar_si_no(datos_doc.get('clin_dialisis')) else "✅ NO",
                "🚨 SÍ" if evaluar_si_no(datos_doc.get('clin_embarazo')) else "✅ NO",
                "🔴 SÍ" if evaluar_si_no(datos_doc.get('clin_lactancia')) else "✅ NO",
                "🔴 SÍ" if evaluar_si_no(datos_doc.get('clin_claustro')) else "✅ NO",
                "🔴 SÍ" if tiene_cancer_check else "✅ NO"
            ],
            "Recomendación / Alerta": [
                "", "", alerta_alergias_final, "", "", "", "",
                datos_doc.get('nota_renal', '') if evaluar_si_no(datos_doc.get('clin_renal')) else "",
                datos_doc.get('nota_dialisis', '') if evaluar_si_no(datos_doc.get('clin_dialisis')) else "",
                datos_doc.get('nota_embarazo', '') if evaluar_si_no(datos_doc.get('clin_embarazo')) else "",
                datos_doc.get('nota_lactancia', '') if evaluar_si_no(datos_doc.get('clin_lactancia')) else "",
                datos_doc.get('nota_claustro', '') if evaluar_si_no(datos_doc.get('clin_claustro')) else "",
                nota_cancer_paciente
            ]
        }
        st.table(pd.DataFrame(data_riesgos))

        condiciones_list = datos_doc.get("condiciones", [])
        detalle_condicion_txt = datos_doc.get("condicion_detalle", "").strip()

        if condiciones_list or detalle_condicion_txt:
            st.markdown("---")
            st.markdown("⚠️ **Condiciones Especiales o Requerimientos:**")
            if condiciones_list:
                st.write(f"**Categorías:** {', '.join(condiciones_list)}")
            if detalle_condicion_txt:
                st.info(f"**Detalle:** {detalle_condicion_txt}")
with c2:
    # 🟢 BLOQUE DE ANTECEDENTES (c2)
    with st.expander("🏥 4. ANTECEDENTES QUIRÚRGICOS Y TERAPÉUTICOS", expanded=True):
        st.write(f"**Cirugías:** {'🔴 SÍ' if evaluar_si_no(datos_doc.get('quir_cirugia_check')) else '✅ NO'}")
        st.write("**Detalle Cirugías:**")
        st.caption(datos_doc.get('quir_cirugia_detalle') if datos_doc.get('quir_cirugia_detalle') else "N/A")
        
        # Sincronizado exacto con el check de app.py
        tiene_cancer = datos_doc.get('quir_cancer_check', 'No') == "Sí"
        st.write(f"**Enfermedad Oncológica (Cáncer):** {'🔴 SÍ' if tiene_cancer else '✅ NO'}")
        
        if tiene_cancer:
            st.write("**Detalle Cáncer/Etapa:**")
            st.caption(datos_doc.get('quir_cancer_detalle') if datos_doc.get('quir_cancer_detalle') else "N/A")
        
        # 👇 PARCHE ONCOLÓGICO: Evaluación estricta de la cadena "Sí"
        trats_activos = []
        if datos_doc.get('rt') == "Sí": trats_activos.append("RT")
        if datos_doc.get('qt') == "Sí": trats_activos.append("QT")
        if datos_doc.get('bt') == "Sí": trats_activos.append("BT")
        if datos_doc.get('it') == "Sí": trats_activos.append("IT")
        
        st.write(f"**Tratamientos:** {', '.join(trats_activos) if trats_activos else 'Ninguno'}")
        st.write("**Otros Tratamientos:**")
        st.caption(datos_doc.get('quir_otro_trat') if datos_doc.get('quir_otro_trat') else "N/A")
        
    with st.expander("📂 5. EXÁMENES ANTERIORES", expanded=True):
        ex_activos = []
        if datos_doc.get('ex_rx'): ex_activos.append("Rx")
        if datos_doc.get('ex_mg'): ex_activos.append("MG")
        if datos_doc.get('ex_eco'): ex_activos.append("Eco")
        if datos_doc.get('ex_tc'): ex_activos.append("TC")
        if datos_doc.get('ex_rm'): ex_activos.append("RM")
    
        st.write(f"**Tipos Declarados:** {', '.join(ex_activos) if ex_activos else 'Ninguno'}")
        if datos_doc.get('ex_otros'):
            st.caption(f"**Otros:** {datos_doc.get('ex_otros')}")

        st.markdown("---")

        # =====================================================================
        # 🌐 A. ENLACES EXTERNOS (NUBE / DICOM)
        # =====================================================================
        link1 = datos_doc.get("link_exam_1", "").strip()
        link2 = datos_doc.get("link_exam_2", "").strip()
        
        if link1 or link2:
            st.markdown("**🌐 Accesos a Portales Externos:**")
            if link1:
                pin1 = datos_doc.get("pin_exam_1", "Sin clave")
                st.info(f"**Link 1:** [{link1}]({link1})  |  **Clave/PIN:** `{pin1}`")
            if link2:
                pin2 = datos_doc.get("pin_exam_2", "Sin clave")
                st.info(f"**Link 2:** [{link2}]({link2})  |  **Clave/PIN:** `{pin2}`")
        else:
            st.caption("ℹ️ Sin links externos declarados.")

        # =====================================================================
        # 📂 B. ARCHIVOS ADJUNTOS (CACHÉ EN RAM MULTI-ARCHIVO)
        # =====================================================================
        st.markdown("---")
        st.markdown("**📂 Documentos Adjuntos (Informes):**")
        
        # 1. Caché para múltiples archivos
        id_paciente_actual = paciente_seleccionado
        if "examenes_cache" not in st.session_state: st.session_state.examenes_cache = []
        if "id_examenes_cache" not in st.session_state: st.session_state.id_examenes_cache = None

        rutas_examenes_fb = datos_doc.get("url_examenes_firebase", [])
        if rutas_examenes_fb:
            try:
                # 2. Descarga única de toda la lista
                if st.session_state.id_examenes_cache != id_paciente_actual or not st.session_state.examenes_cache:
                    st.session_state.examenes_cache = [] # Limpiamos caché anterior
                    for ruta in rutas_examenes_fb:
                        blob_exam = bucket.blob(ruta)
                        # Guardamos los bytes y la extensión en un diccionario dentro de la lista
                        st.session_state.examenes_cache.append({
                            "bytes": blob_exam.download_as_bytes(),
                            "ext": os.path.splitext(ruta)[1].lower()
                        })
                    st.session_state.id_examenes_cache = id_paciente_actual

                # 3. Renderizado instantáneo
                for i, archivo in enumerate(st.session_state.examenes_cache):
                    if archivo["ext"] in ['.jpg', '.jpeg', '.png']:
                        st.image(archivo["bytes"], caption=f"Examen Adjunto #{i+1}", use_container_width=True)
                    else:
                        st.download_button(
                            label=f"⬇️ Descargar Informe #{i+1} (PDF)",
                            data=archivo["bytes"],
                            file_name=f"Informe_{i+1}_{datos_doc.get('rut', 'Paciente')}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            key=f"btn_descarga_exam_{i}_{id_paciente_actual}"
                        )
            except Exception as e:
                st.error("⚠️ Error al cargar los informes en memoria.")
        else:
            st.caption("ℹ️ El paciente no adjuntó archivos físicos.")
            
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
                disabled=es_pediatrico or not puede_editar_y_firmar(),
                key=f"peso_input_{paciente_seleccionado}", # <--- LLAVE ÚNICA AÑADIDA
                help="Visible pero bloqueado en pacientes pediátricos o modo solo lectura."
            )
        with col_c:
            creatinina_profesional = st.number_input(
                "Creatinina (mg/dL):",
                min_value=0.0, max_value=15.0, value=creatinina_base, step=0.01,
                key=f"crea_input_{paciente_seleccionado}", # <--- LLAVE ÚNICA AÑADIDA
                disabled=not puede_editar_y_firmar()
            )
        with col_t:
            talla_profesional = st.number_input(
                "Talla (cm):",
                min_value=0.0, max_value=250.0, value=talla_base, step=1.0,
                key=f"talla_input_{paciente_seleccionado}", # <--- LLAVE ÚNICA AÑADIDA
                disabled=not es_pediatrico or not puede_editar_y_firmar(),
                help="Bloqueado en adultos o modo solo lectura."
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

# =====================================================================
# 1. ESTILOS CSS PARA CENTRAR CAMPOS (TÍTULOS A LA IZQUIERDA)
# =====================================================================
st.markdown("""
    <style>
    /* Centra el texto digitado dentro de los cuadros de texto (Cantidad) */
    div[data-testid="stTextInput"] input {
        text-align: center !important;
    }
    /* Centra la opción seleccionada dentro de los selectores (Vías e Insumos) */
    div[data-testid="stSelectbox"] div[data-testid="stMarkdownContainer"] p {
        text-align: center !important;
        width: 100%;
    }
    /* Centra el texto estático de los insumos fijos alineándolos en su contenedor */
    .centrar-verticalmente {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 2.5rem;
        font-weight: bold;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)


# =====================================================================
# 1. ESTILOS CSS PARA CENTRAR CAMPOS (TÍTULOS A LA IZQUIERDA)
# =====================================================================
st.markdown("""
    <style>
    /* Centra el texto digitado dentro de los cuadros de texto (Cantidad) */
    div[data-testid="stTextInput"] input {
        text-align: center !important;
    }
    /* Centra la opción seleccionada dentro de los selectores (Vías e Insumos) */
    div[data-testid="stSelectbox"] div[data-testid="stMarkdownContainer"] p {
        text-align: center !important;
        width: 100%;
    }
    /* Centra el texto estático de los insumos fijos alineándolos en su contenedor */
    .centrar-verticalmente {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 2.5rem;
        font-weight: bold;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 0. FUNCIONES DE UTILIDAD (Limpieza de Estado)
# =====================================================================
def limpiar_estado_administracion():
    """Limpia todo el estado de insumos para evitar contaminación cruzada."""
    st.session_state.insumos_sesion = []
    st.session_state.registro_insumos_final = {}
    st.session_state.registro_acceso_vascular = {}
    st.session_state.toggle_admin_activo = False
    st.session_state.contexto_insumos = None
# =====================================================================
# 2. CATÁLOGO MAESTRO DE INSUMOS (IDs Únicos para PDF y Firestore)
# =====================================================================
MASTER_INSUMOS = {
    "INS_001": {"nombre": "Ac. Gadotérico (Clariscan)", "via": "Endovenosa"},
    "INS_002": {"nombre": "Suero fisiológico (NaCl 0,9%)", "via": "Endovenosa"},
    "INS_003": {"nombre": "Furosemida", "via": "Endovenosa"},
    "INS_004": {"nombre": "Butilbromuro de escopolamina (Buscapina)", "via": "Endovenosa"},
    "INS_005": {"nombre": "Suero Manitol 15%", "via": "Oral"},
    "INS_006": {"nombre": "Agua (H2O)", "via": "Oral"},
    "INS_007": {"nombre": "Gel Intracavitario", "via": "Rectal"},  # Unificado
    "INS_009": {"nombre": "Ac. Gadoxético (Primovist)", "via": "Endovenosa"},
    "INS_010": {"nombre": "Gadopiclenol (Elucirem)", "via": "Endovenosa"},
    "INS_011": {"nombre": "Clorfenamina Maleato", "via": "Endovenosa"},
    "INS_012": {"nombre": "Betametasona", "via": "Endovenosa"},
    "INS_013": {"nombre": "Regadenosón", "via": "Endovenosa"},
    "INS_014": {"nombre": "Dobutamina", "via": "Endovenosa"}
}

# Callback optimizado para eliminar insumos de la sesión de inmediato sin lag
def eliminar_insumo_callback(insumo_id):
    if insumo_id in st.session_state.get('insumos_sesion', []):
        st.session_state.insumos_sesion.remove(insumo_id)
    if insumo_id in st.session_state.get('registro_insumos_final', {}):
        del st.session_state.registro_insumos_final[insumo_id]


# =====================================================================
# 3. SECCIÓN 7: REGISTRO DE ADMINISTRACIÓN DINÁMICO
# =====================================================================
requiere_contraste = datos_doc.get('tiene_contraste', False)
with st.expander("💉 7. REGISTRO DE ADMINISTRACIÓN CLÍNICA", expanded=True):
    
    # 1. Obtenemos el contexto actual (LÓGICA DE IDENTIDAD BLINDADA)
    es_extranjero = datos_doc.get('sin_rut', False)
    if es_extranjero in [True, "true", "True", "1"]:
        id_paciente_actual = str(datos_doc.get('num_doc', 'SIN_IDENTIFICACION')).strip()
    else:
        id_paciente_actual = str(datos_doc.get('rut', 'SIN_RUT')).strip()
    
    procedimientos_str = str(datos_doc.get('procedimiento', '')).upper()
    contexto_actual = f"{id_paciente_actual}_{procedimientos_str}"
    
    # 2. DISPARADOR: Si el contexto cambió, LLAMAMOS a la función de limpieza y calculamos activación
    if st.session_state.get('contexto_insumos') != contexto_actual:
        limpiar_estado_administracion() # <--- Asegúrate que esta función también borre la llave 'insumos_restaurados_enmienda'
        st.session_state.contexto_insumos = contexto_actual
        # Eliminamos el candado al cambiar de paciente para que pueda rescatar el nuevo
        if 'insumos_restaurados_enmienda' in st.session_state:
            del st.session_state.insumos_restaurados_enmienda
        
        # 🧠 MEMORIA DE RESCATE: ¿El paciente ya trae fármacos validados?
        farmacos_previos = datos_doc.get('contraste_administrado', {})
        
        if datos_doc.get("es_enmienda") and farmacos_previos:
            # 🔐 APLICAMOS EL CANDADO: Solo entra aquí una vez por paciente
            if "insumos_restaurados_enmienda" not in st.session_state:
                # Restaurar insumos y dosis
                st.session_state.insumos_sesion = list(farmacos_previos.keys())
                st.session_state.registro_insumos_final = farmacos_previos.copy()
                st.session_state.toggle_admin_activo = True
                
                # Restauramos el acceso venoso y sitio guardado
                acc_previo = datos_doc.get('acceso_venoso', 'No registrado')
                partes_acc = acc_previo.split(" ")
                tipo_prev = partes_acc[0] if len(partes_acc) > 0 else acc_previo
                cal_prev = partes_acc[1] if len(partes_acc) > 1 else "N/A"
                
                if "Aguja" in acc_previo:
                    tipo_prev = "Aguja Ultra Fina"
                    cal_prev = partes_acc[-1] if len(partes_acc) > 0 else "N/A"
                    
                st.session_state.registro_acceso_vascular = {
                    "dispositivo": tipo_prev,
                    "calibre": cal_prev,
                    "sitio": datos_doc.get('sitio_puncion', 'No registrado'),
                    "resumen_acceso": acc_previo
                }
                
                # CERRAMOS EL CANDADO
                st.session_state.insumos_restaurados_enmienda = True
        
        else:
            # Lógica estándar de sugerencia de insumos (si no es enmienda)
            requiere_contraste = datos_doc.get('tiene_contraste', False)
            insumos_sugeridos = set()
            
            if requiere_contraste:
                if "HEPATO" in procedimientos_str:
                    insumos_sugeridos.update(["INS_009", "INS_002"])
                else:
                    insumos_sugeridos.update(["INS_001", "INS_002"])
            
            if "CARDIO" in procedimientos_str:
                insumos_sugeridos.update(["INS_001", "INS_002", "INS_013", "INS_014"])
            if "URO" in procedimientos_str:
                insumos_sugeridos.update(["INS_001", "INS_002", "INS_003", "INS_004"])
            if "ENTERO" in procedimientos_str:
                insumos_sugeridos.update(["INS_001", "INS_002", "INS_005", "INS_006", "INS_004"])
            if "DEFECO" in procedimientos_str:
                insumos_sugeridos.update(["INS_001", "INS_002", "INS_007", "INS_004"])
                
            st.session_state.insumos_sesion = list(insumos_sugeridos)
            st.session_state.paciente_activo_insumos = id_paciente_actual
                    
            # 🧠 DETERMINACIÓN FIABLE DE ACTIVACIÓN EN TIEMPO REAL:
            # Evaluamos si cumple con criterio de contraste o pertenece a un procedimiento especial
            es_procedimiento_especial = any(x in procedimientos_str for x in ["CARDIO", "URO", "ENTERO", "DEFECO", "HEPATO"])
            st.session_state.toggle_admin_activo = bool(requiere_contraste or es_procedimiento_especial)

    st.markdown("<span style='font-size: 13px; color: #666;'><b>Control de Sesión:</b></span>", unsafe_allow_html=True)
    
    # Inicialización de seguridad en caso de que no exista la llave en el primer renderizado absoluto
    if "toggle_admin_activo" not in st.session_state:
        es_procedimiento_especial = any(x in procedimientos_str for x in ["CARDIO", "URO", "ENTERO", "DEFECO", "HEPATO"])
        st.session_state.toggle_admin_activo = bool(requiere_contraste or es_procedimiento_especial)

    # 🎛️ EL INTERRUPTOR MAESTRO REACTIVO
    activar_admin = st.toggle(
        "Habilitar registro de administración (Medios de Contraste y/o Fármacos)", 
        key="toggle_admin_activo",
        disabled=not puede_editar_y_firmar(), # <--- AQUI
        help="Solo profesionales Clínicos (TM) pueden editar esta sección, endender en caso de que se requiera administrar  medio de contraste."
    )
    
    if activar_admin:
        st.info("✅ **Modo Administración Activo.** Registre los parámetros utilizados en la sesión.")
        
        # --- A. ACCESO VASCULAR ---
        st.markdown("**1. Dispositivo de Acceso Venoso Principal**")
        
        # 🧠 RESCATE INTELIGENTE DE VALORES DE ACCESO VASCULAR (UI)
        datos_acc_memoria = st.session_state.get('registro_acceso_vascular', {})
        tipo_default = datos_acc_memoria.get('dispositivo', 'Bránula')
        calibre_default = datos_acc_memoria.get('calibre', '20G')
        sitio_default = datos_acc_memoria.get('sitio', 'Pliegue antebrazo')
        
        lista_tipos = ["Bránula", "Mariposa", "PICC", "CVC", "Aguja Ultra Fina"]
        try: idx_tipo = lista_tipos.index(tipo_default)
        except: idx_tipo = 0
        
        c_acc1, c_acc2, c_acc3 = st.columns([1.5, 1, 2])
        tipo_acc = c_acc1.selectbox("Dispositivo", lista_tipos, index=idx_tipo, key="acc_tipo")
        
        # Lógica de calibres (G vs French)
        if tipo_acc == "Mariposa":
            opciones_calibre = ["21G", "23G"]
        elif tipo_acc == "Bránula":
            opciones_calibre = ["18G", "20G", "22G", "24G"]
        elif tipo_acc in ["PICC", "CVC"]:
            opciones_calibre = ["4 FR", "5 FR", "6 FR", "7 FR"]
        elif tipo_acc == "Aguja Ultra Fina":
            opciones_calibre = ["31G", "32G", "33G"]
        else:
            opciones_calibre = ["N/A"]
            
        try: idx_cal = opciones_calibre.index(calibre_default)
        except: idx_cal = 0
            
        cal_acc = c_acc2.selectbox("Calibre", opciones_calibre, index=idx_cal, key="acc_calibre")
        sitio_acc = c_acc3.text_input("Sitio de punción", value=sitio_default if tipo_acc != "No aplica" else "N/A", key="acc_sitio")
        
        disp_principal_str = f"{tipo_acc} {cal_acc}" if cal_acc != "N/A" else tipo_acc
        st.session_state.registro_acceso_vascular = {
            "dispositivo": tipo_acc,
            "calibre": cal_acc,
            "sitio": sitio_acc,
            "resumen_acceso": disp_principal_str
        }
        
        if 'registro_insumos_final' not in st.session_state:
            st.session_state.registro_insumos_final = {}

        # --- DINÁMICA DE CONTRASTE (DETECTA CUALQUIER CONTRASTE ACTIVO: 001 O 009) ---
        contrastes_validos = ["INS_001", "INS_009"]
        id_contraste_activo = next((i for i in st.session_state.insumos_sesion if i in contrastes_validos), None)

        if id_contraste_activo:
            datos_contraste = MASTER_INSUMOS[id_contraste_activo]
            st.markdown("<br>", unsafe_allow_html=True)
            c_cm1, c_cm2, c_cm3, c_cm4, c_cm5 = st.columns([2.5, 1.5, 1.5, 0.8, 0.5])
            with c_cm1:
                st.markdown(f"<div class='centrar-verticalmente'>{datos_contraste['nombre']}</div>", unsafe_allow_html=True)
            with c_cm2:
                # 🧠 Rescate Vía MC
                via_memoria_mc = st.session_state.registro_insumos_final.get(id_contraste_activo, {}).get("via", "Endovenosa")
                opc_via_mc = ["Endovenosa"]
                try: idx_via_mc = opc_via_mc.index(via_memoria_mc)
                except: idx_via_mc = 0
                via_sel_cm = st.selectbox("Vía MC", opc_via_mc, index=idx_via_mc, key=f"via_{id_contraste_activo}", label_visibility="collapsed")
            with c_cm3:
                st.markdown(f"<div class='centrar-verticalmente'>{disp_principal_str}</div>", unsafe_allow_html=True)
            with c_cm4:
                # 🧠 RESCATE INTELIGENTE DE DOSIS CONTRASTE (ML)
                datos_insumo_cm = st.session_state.registro_insumos_final.get(id_contraste_activo, {})
                # 💡 FIX: Retrocompatibilidad. Busca 'dosis', si no existe, rescata 'cantidad' (registros antiguos).
                dosis_memoria_cm = str(datos_insumo_cm.get("dosis", datos_insumo_cm.get("cantidad", "0.0")))
                
                dosis_raw_cm = st.text_input("Dosis MC", value=dosis_memoria_cm, key=f"dosis_raw_{id_contraste_activo}", label_visibility="collapsed")
                try: dosis_sel_cm = float(dosis_raw_cm)
                except ValueError: dosis_sel_cm = 0.0
            with c_cm5:
                st.write("") # Espacio vacío
            
            st.session_state.registro_insumos_final[id_contraste_activo] = {
                "id": id_contraste_activo, "nombre": datos_contraste['nombre'], "via": via_sel_cm, "insumo_administracion": disp_principal_str, "dosis": dosis_sel_cm
            }

        st.markdown("---")

        # --- B. LISTADO DINÁMICO DE INSUMOS ---
        st.markdown("**2. Otros medios de contraste y medicamentos**")
        
        hc1, hc2, hc3, hc4, hc5 = st.columns([2.5, 1.5, 1.5, 0.8, 0.5])
        hc1.caption("Insumo / Fármaco")
        hc2.caption("Vía")
        hc3.caption("Insumo Adm.")
        hc4.caption("ml")
        hc5.caption("")

        for insumo_id in list(st.session_state.insumos_sesion):
            # Saltar el contraste principal (ya renderizado arriba)
            if insumo_id in contrastes_validos:
                continue
                
            datos_maestros = MASTER_INSUMOS[insumo_id]
            nombre_insumo = datos_maestros['nombre']
            via_maestra = datos_maestros['via']
            es_gel = insumo_id == "INS_007"
            
            c1, c2, c3, c4, c5 = st.columns([2.5, 1.5, 1.5, 0.8, 0.5])
            
            with c1:
                st.markdown(f"<div class='centrar-verticalmente'>{nombre_insumo}</div>", unsafe_allow_html=True)
            
            with c2:
                opciones_via = ["Rectal", "Vaginal", "Ambas vías"] if es_gel else (["Endovenosa"] if insumo_id == "INS_002" else [via_maestra])
                # 🧠 Rescatar Vía Seleccionada de Memoria
                via_mem = st.session_state.registro_insumos_final.get(insumo_id, {}).get("via", opciones_via[0])
                try: idx_via = opciones_via.index(via_mem)
                except: idx_via = 0
                via_sel = st.selectbox("V", opciones_via, index=idx_via, key=f"via_{insumo_id}", label_visibility="collapsed")
            
            with c3:
                if via_sel == "Oral":
                    st.markdown("<div class='centrar-verticalmente'>Botella Plástica / Vaso</div>", unsafe_allow_html=True)
                    insumo_admin_str = "Botella Plástica / Vaso"
                elif es_gel:
                    sonda_mem = st.session_state.registro_insumos_final.get(insumo_id, {}).get("insumo_administracion", "Sonda FR10")
                    sondas_opc = ["Sonda FR10", "Sonda FR12", "Sonda FR14"]
                    try: idx_sonda = sondas_opc.index(sonda_mem)
                    except: idx_sonda = 0
                    sonda_sel = st.selectbox("Sonda Tipo", sondas_opc, index=idx_sonda, key=f"sonda_{insumo_id}", label_visibility="collapsed")
                    insumo_admin_str = sonda_sel
                elif via_sel == "Endovenosa":
                    st.markdown(f"<div class='centrar-verticalmente'>{disp_principal_str}</div>", unsafe_allow_html=True)
                    insumo_admin_str = disp_principal_str
                else:
                    st.markdown("<div class='centrar-verticalmente'>No aplica</div>", unsafe_allow_html=True)
                    insumo_admin_str = "No aplica"
            
            with c4:
                # 🧠 RESCATE INTELIGENTE DE DOSIS OTROS INSUMOS (ML)
                val_defecto = "10.0" if es_gel else "0.0"
                datos_otro_insumo = st.session_state.registro_insumos_final.get(insumo_id, {})
                # 💡 FIX: Retrocompatibilidad con la llave antigua 'cantidad'
                val_memoria = str(datos_otro_insumo.get("dosis", datos_otro_insumo.get("cantidad", val_defecto)))
                
                dosis_raw = st.text_input("D", value=val_memoria, key=f"dosis_raw_{insumo_id}", label_visibility="collapsed")
                try: dosis_sel = float(dosis_raw)
                except ValueError: dosis_sel = 0.0

            with c5:
                if st.button("🗑️", key=f"del_{insumo_id}"):
                    eliminar_insumo_callback(insumo_id)
                    st.rerun()

            st.session_state.registro_insumos_final[insumo_id] = {
                "id": insumo_id, "nombre": nombre_insumo, "via": via_sel, "insumo_administracion": insumo_admin_str, "dosis": dosis_sel
            }

        # --- C. EXCEPCIONES Y ADICIONALES ---
        with st.expander("➕ Administrar fármaco o insumo adicional"):
            insumos_disponibles = {k: v['nombre'] for k, v in MASTER_INSUMOS.items() if k not in st.session_state.insumos_sesion}
            
            if insumos_disponibles:
                # 🛡️ SOLUCIÓN: st.form aísla los widgets y evita el colapso de recargas automáticas
                with st.form(key=f"form_adicionales_{paciente_seleccionado}", border=False):
                    col_ex1, col_ex2 = st.columns([3, 1], vertical_alignment="bottom")
                    
                    nuevos_ids = col_ex1.multiselect(
                        "Seleccione las sustancias:", 
                        list(insumos_disponibles.keys()), 
                        format_func=lambda x: insumos_disponibles[x]
                    )
                    
                    # form_submit_button atrapa la acción de forma segura
                    submit_add = col_ex2.form_submit_button("Añadir Selección", use_container_width=True)
                    
                    if submit_add and nuevos_ids:
                        # 1. Inyectamos a la memoria principal asegurando que no haya duplicados
                        for nid in nuevos_ids:
                            if nid not in st.session_state.insumos_sesion:
                                st.session_state.insumos_sesion.append(nid)
                        
                        # 2. Rerun limpio. Las opciones elegidas ya no estarán en 'insumos_disponibles',
                        # por lo que Streamlit limpiará el multiselect automáticamente al recargar.
                        st.rerun()
            else:
                st.caption("Todos los insumos del catálogo ya están en la lista.")
                
    else:
        st.warning("El registro de contraste y fármacos está desactivado.")
        
        # ELIMINADO: Ya no borramos la memoria aquí.
        # La limpieza debe ocurrir solo si seleccionas un paciente diferente, 
        # no porque el panel esté oculto.
        
        if requiere_contraste:
            motivo_suspension = st.text_area("⚠️ Justifique la **no administración** de contraste:", 
                                            placeholder="Ej: Paciente refiere alergia severa...", 
                                            key="motivo_suspension_contraste")
        
    # =====================================================================
# 3. FIRMA DIGITAL
# =====================================================================
st.markdown("---")
st.markdown("#### ✍🏼 Firma Digital del Paciente")

# 1. Identificador único
id_paciente_actual = paciente_seleccionado

# 2. Creamos los espacios en la memoria si no existen
if "firma_paciente_cache" not in st.session_state:
    st.session_state.firma_paciente_cache = None
if "id_firma_cache" not in st.session_state:
    st.session_state.id_firma_cache = None

try:
    ruta_firma = doc_completo.get("firma_img")
    if ruta_firma:
        # Lógica de carga de firma
        if st.session_state.id_firma_cache != id_paciente_actual or st.session_state.firma_paciente_cache is None:
            blob = bucket.blob(ruta_firma)
            st.session_state.firma_paciente_cache = blob.download_as_bytes()
            st.session_state.id_firma_cache = id_paciente_actual 
        
        st.markdown('''
            <div style="display: flex; justify-content: center; align-items: center; margin: 15px 0; padding: 20px; background: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px;">
        ''', unsafe_allow_html=True)
        st.image(st.session_state.firma_paciente_cache, width=350)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("⚠️ No se capturó firma digital para este paciente.")
except Exception as e:
    st.error(f"Error cargando firma: {e}")

# --- BLOQUE DE DOBLE FIRMA SEGURA ---
st.divider()
st.markdown("### ✍🏼 Validación del Profesional (Doble Firma)")

if not puede_editar_y_firmar():
    st.warning("🔒 **Modo Solo Lectura:** Su perfil no cuenta con permisos clínicos para modificar o firmar la ficha técnica de este paciente.")
else:
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
        st.warning("⚠️ Al presionar 'Aprobar Encuesta', usted certifica bajo su firma que ha evaluado la tasa de filtración glomerular (VFG) y los factores de riesgo del paciente.")
    
    with col_f2:
        st.markdown("##### Firma Digital del Profesional:")
        col_esp1, col_canvas, col_esp2 = st.columns([1, 4, 1])
        
        with col_canvas:
            st.markdown('''
                <style>
                .canvas-container {
                    background: white;
                    border: 2px solid #ddd;
                    border-radius: 10px;
                    padding: 10px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    display: flex;
                    justify-content: center;
                }
                </style>
                <div class="canvas-container">
            ''', unsafe_allow_html=True)
            
            canvas_profesional = st_canvas(
                fill_color="rgba(255, 255, 255, 0)",
                stroke_width=4,
                stroke_color="#000000",
                background_color="#ffffff",
                height=200, 
                width=500,
                drawing_mode="freedraw",
                key="canvas_tm_unico" 
            )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
# --- BOTÓN DE CIERRE DE CIRCUITO CLÍNICO ---
    st.markdown("<br>", unsafe_allow_html=True)

        # AÑADIMOS EL KEY ÚNICO AL BOTÓN PARA EVITAR CONFLICTOS ENTRE PACIENTES
    if st.button("🚀 APROBAR ENCUESTA Y GUARDAR VALIDACIÓN", use_container_width=True, key=f"btn_final_{paciente_seleccionado}"):
        
        if canvas_profesional is not None and canvas_profesional.json_data is not None and len(canvas_profesional.json_data["objects"]) > 0:
            
            # 👇 TODO EL CÓDIGO AHORA VIVE ESTRICTAMENTE DENTRO DE ESTE IF (DENTRO DEL BOTÓN)
            with st.spinner("Estampando firma del profesional y consolidando documento..."):
                try:
                    # =====================================================================
                    # 1. PROCESAR LA FIRMA DEL PROFESIONAL (TM) Y SUBIR A FIRESTORE
                    # =====================================================================
                    img_data_tm = canvas_profesional.image_data
                    img_tm_pil = Image.fromarray(img_data_tm.astype('uint8'), 'RGBA')
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_tm:
                        img_tm_pil.save(tmp_tm.name)
                        ruta_firma_tm_local = tmp_tm.name
        
                    # SUBIR FIRMA DEL TM A STORAGE
                    nombre_archivo_tm_storage = f"firmas_profesionales/TM_{profesional_registro}_{datetime.now(tz_chile).strftime('%Y%m%d_%H%M%S')}.png"
                    blob_tm = bucket.blob(nombre_archivo_tm_storage)
                    blob_tm.upload_from_filename(ruta_firma_tm_local, content_type='image/png')
        
                    # ACTUALIZAR FIRESTORE Y MEMORIA LOCAL
                    fecha_validacion_str = datetime.now(tz_chile).strftime("%d/%m/%Y %H:%M:%S")
                    id_documento_paciente = paciente_seleccionado.id if hasattr(paciente_seleccionado, 'id') else str(paciente_seleccionado)
                    
                    datos_acceso = st.session_state.get('registro_acceso_vascular', {})
                    acceso_venoso = datos_acceso.get('resumen_acceso', 'No registrado')
                    sitio_puncion = datos_acceso.get('sitio', 'No registrado')
                    datos_contraste = st.session_state.get('registro_insumos_final', {})
                    
                    activar_admin = st.session_state.get('toggle_admin_activo', False)
                    gadolinios_ids = ["INS_001", "INS_009", "INS_010"]
                    
                    if activar_admin and datos_contraste:
                        tiene_contraste_real = any(ins in gadolinios_ids for ins in datos_contraste.keys())
                    else:
                        tiene_contraste_real = False

                    proc_base_raw = str(datos_doc.get('procedimiento', 'PROCEDIMIENTO NO ESPECIFICADO'))
                    patron_limpieza = r'(?i)\s*[\(\-]?\s*\b(con medio de contraste|sin medio de contraste|con contraste|sin contraste|c/gd|c/c|s/c|c/contraste)\b\s*[\(\)\-]?\s*'
                    nombre_base = re.sub(patron_limpieza, '', proc_base_raw).strip().upper()
                    nombre_base = re.sub(r'\s+', ' ', nombre_base).strip(' ,')

                    if tiene_contraste_real:
                        if "," in nombre_base:
                            procedimiento_oficial = f"{nombre_base} C/Gd"
                        else:
                            procedimiento_oficial = f"{nombre_base} CON CONTRASTE"
                    else:
                        procedimiento_oficial = f"{nombre_base} SIN CONTRASTE"
                        
                    datos_doc.update({
                        'acceso_venoso': acceso_venoso,
                        'sitio_puncion': sitio_puncion,
                        'contraste_administrado': datos_contraste,
                        'procedimiento': procedimiento_oficial,
                        'tiene_contraste': tiene_contraste_real,
                        'adendum_autor': profesional_nombre
                    })
                    
                    db.collection("encuestas").document(id_documento_paciente).update({
                        "profesional_nombre": profesional_nombre,
                        "profesional_registro": profesional_registro,
                        "fecha_validacion": fecha_validacion_str,
                        "estado_validacion": "VALIDADO",
                        "encuesta_validada": True,
                        "firma_profesional_img": nombre_archivo_tm_storage,
                        "procedimiento": procedimiento_oficial,
                        "tiene_contraste": tiene_contraste_real,
                        "acceso_venoso": acceso_venoso,
                        "sitio_puncion": sitio_puncion,
                        "adendum_texto": datos_doc.get('adendum_texto', ''),
                        "adendum_fecha": fecha_validacion_str if datos_doc.get('es_enmienda') else None,
                        "adendum_autor": profesional_nombre if datos_doc.get('es_enmienda') else None
                    })
                    
                    # =====================================================================
                    # 📄 2. PREPARACIÓN E INYECCIÓN DE VARIABLES AL MOTOR PDF
                    # =====================================================================
                    st.info("🔄 Compilando formato institucional Norte Imagen...")

                    import io
                    import os
                    from fpdf import FPDF

                    paciente_nombre = datos_doc.get('nombre', 'Paciente No Identificado')

                    es_extranjero = datos_doc.get('sin_rut', False)
                    if es_extranjero in [True, "true", "True", "1"]:
                        paciente_rut = f"{datos_doc.get('tipo_doc', 'Documento')}: {datos_doc.get('num_doc', 'S/N')}"
                    else:
                        paciente_rut = str(datos_doc.get('rut', datos_doc.get('run', 'S/R')))

                    fecha_nacimiento_val = datos_doc.get('fecha_nac', datos_doc.get('fecha_nacimiento', 'N/A'))
                    if hasattr(fecha_nacimiento_val, 'strftime'):
                        fecha_nacimiento_val = fecha_nacimiento_val.strftime('%d/%m/%Y')
                    email_val = datos_doc.get('email', 'N/A')
                    procedimiento_val = datos_doc.get('procedimiento', 'RM General')

                    idx_gen_admin = str(datos_doc.get('genero_idx', '0'))
                    idx_bio_admin = str(datos_doc.get('sexo_bio_idx', '0'))
                    ocr_bio_admin = str(datos_doc.get('genero_biologico', '')).strip().capitalize()

                    if idx_gen_admin == "1" or idx_gen_admin in ["Femenino", "F", "Mujer"]:
                        genero = "Femenino"
                    elif idx_gen_admin == "2" or idx_gen_admin in ["No binario", "Nobinario"] or str(datos_doc.get('sexo')) == "No binario":
                        if ocr_bio_admin in ["Masculino", "Femenino"]:
                            sexo_bio_str = ocr_bio_admin
                        else:
                            sexo_bio_str = "Femenino" if idx_bio_admin == "1" else "Masculino"
                        genero = f"No binario (Bio: {sexo_bio_str})"
                    else:
                        genero = "Masculino"

                    is_contraste = datos_doc.get('tiene_contraste', False) in [True, "Sí", "SI", "si", "Si"]
                    
                    rep_nombre = datos_doc.get('nombre_tutor', '')
                    if datos_doc.get('sin_rut_tutor'):
                        rep_rut = f"{datos_doc.get('tipo_doc_tutor', 'Doc')}: {datos_doc.get('num_doc_tutor', 'S/R')}"
                    else:
                        rep_rut = datos_doc.get('rut_tutor', 'S/R')

                    ip_cliente = datos_doc.get('ip_dispositivo', 'No detectada')
                    ruta_firma_paciente_storage = datos_doc.get('firma_img', '')

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

                    def safe_text(txt):
                        if txt is None: return "N/A"
                        return str(txt).encode('latin-1', 'replace').decode('latin-1')

                    def parse_bool_clinico(val):
                        if isinstance(val, bool): return "Sí" if val else "No"
                        if str(val).strip().upper() in ['SI', 'SÍ', 'TRUE', '1', 'YES']: return "Sí"
                        return "No"

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
                            
                            if hasattr(self, 'datos_doc') and self.datos_doc.get('adendum_texto'):
                                self.set_font('Arial', 'B', 9) 
                                self.set_text_color(255, 0, 0) 
                                self.cell(0, 5, safe_text('DOCUMENTO RECTIFICADO / ADENDUM CLÍNICO'), 0, 1, 'R')

                            self.set_font('Arial', 'B', 12)
                            self.set_text_color(128, 0, 32)
                            self.cell(0, 7, safe_text('ENCUESTA DE RIESGOS ASOCIADOS Y'), 0, 1, 'R')
                            self.cell(0, 7, safe_text('CONSENTIMIENTO INFORMADO'), 0, 1, 'R')
                                
                            self.set_font('Arial', 'B', 16)
                            self.set_text_color(128, 0, 32)
                            self.cell(0, 8, safe_text('RESONANCIA MAGNETICA'), 0, 1, 'R')
                            self.ln(10)

                        def footer(self):
                            es_adendum = hasattr(self, 'datos_doc') and self.datos_doc.get('adendum_texto')
                            altura_adicional = 15 if es_adendum else 0 
                            
                            self.set_y(-15 - altura_adicional) 
                            
                            if es_adendum:
                                self.set_font('Arial', 'B', 7)
                                self.set_text_color(255, 0, 0) 
                                
                                motivo_enmienda = self.datos_doc.get('adendum_texto', 'Rectificación.').replace('\n', ' ')
                                autor_enmienda = self.datos_doc.get('adendum_autor', 'Profesional a cargo')
                                
                                self.cell(0, 3, safe_text(f"ADENDUM LEY 20.584: Este documento fue reabierto y rectificado por {autor_enmienda}."), 0, 1, 'L')
                                self.cell(0, 3, safe_text(f"Motivo: {motivo_enmienda}"), 0, 1, 'L')
                                self.ln(2) 
                            
                            self.set_font('Arial', 'I', 7)
                            self.set_text_color(150, 150, 150)
                            
                            iniciales = "".join([p[0].upper() for p in self.p_nombre.split() if p])
                            ip_final = getattr(self, 'p_ip', 'IP No detectada')
                            if ip_final == "IP No detectada" and hasattr(self, 'datos_doc'):
                                ip_final = self.datos_doc.get('ip_paciente', 'IP No detectada')
                            
                            id_registro = f"{self.p_rut}-{iniciales} (IP:{ip_final})"
                            estado_val = "REVALIDADO TM" if es_adendum else "VALIDADO TM"
                            texto_pie = f"Certificado Digital Norte Imagen - RM: {self.f_val} - ID Registro: {id_registro} - {estado_val}."
                            
                            self.cell(0, 10, safe_text(texto_pie), 0, 0, 'L')
                            self.cell(0, 10, safe_text(f"Página {self.page_no()}/{{nb}}"), 0, 0, 'R')

                        def section_title(self, num, title):
                            self.set_font('Arial', 'B', 10)
                            self.set_fill_color(240, 240, 240)
                            self.set_text_color(128, 0, 32)
                            self.cell(0, 6, safe_text(f" {num}. {title}"), ln=True, fill=True)
                            self.ln(1.5)
                            self.set_text_color(0, 0, 0)
                            self.set_fill_color(255, 255, 255)

                        def data_field(self, label, value, h=5):
                            self.set_font('Arial', 'B', 9)
                            self.set_text_color(50, 50, 50)
                            self.write(h, f"{safe_text(label)}: ")
                            self.set_font('Arial', '', 9)
                            self.set_text_color(0, 0, 0)
                            self.write(h, f"{safe_text(value)}\n")

                    ip_cliente = datos_doc.get('ip_paciente', 
                                 datos_doc.get('ip_dispositivo', 
                                 datos_doc.get('ip', 
                                 form_interno.get('ip_dispositivo', 
                                 form_interno.get('ip', 'IP No detectada')))))

                    fecha_validacion_str = datetime.now(tz_chile).strftime("%d/%m/%Y %H:%M:%S")
                    paciente_nombre = datos_doc.get('nombre', 'Paciente')
                    paciente_rut = datos_doc.get('rut', 'N/A')

                    pdf = PDF_Institucional(paciente_nombre, paciente_rut, ip_cliente, fecha_validacion_str)
                    
                    pdf.p_nombre = paciente_nombre
                    pdf.p_rut = paciente_rut
                    pdf.f_val = fecha_validacion_str
                    pdf.p_ip = ip_cliente
                    pdf.datos_doc = datos_doc  
                    
                    pdf.alias_nb_pages()
                    pdf.add_page()
                    pdf.set_auto_page_break(auto=True, margin=12)

                    pdf.set_font('Arial', 'B', 9)
                    
                    fecha_top = fecha_validacion_str.split()[0] if 'fecha_validacion_str' in locals() else datetime.now().strftime("%d/%m/%Y")
                    pdf.cell(0, 5, safe_text(f"Fecha de examen: {fecha_top}"), 0, 1, 'R')
                    
                    procedencia_base = datos_doc.get('procedencia', 'AMBULATORIO').upper()
                    unidad_val = datos_doc.get('unidad_procedencia', '').strip().upper()
                    
                    if procedencia_base == 'HOSPITALIZADO' and unidad_val:
                        texto_procedencia = f"Procedencia: {procedencia_base} (Unidad: {unidad_val})"
                    else:
                        texto_procedencia = f"Procedencia: {procedencia_base}"
                    
                    pdf.set_font('Arial', 'B', 10)
                    pdf.cell(0, 5, safe_text(texto_procedencia), 0, 1, 'L') 
                    pdf.ln(2)

                    pdf.section_title("1", "IDENTIFICACION DEL PACIENTE")
                    
                    margen_izquierdo = 10
                    ancho_disponible = pdf.w - 20 
                    w_col = (ancho_disponible - 10) / 2
                    x_col2 = margen_izquierdo + w_col + 10 
                    c_label = (245, 245, 245)
                    c_valor = (252, 252, 252)
                    h = 4.7 
                    
                    edad_formateada = calcular_edad_visual_completa(datos_doc.get('fecha_nac', ''))
                    edad_int = int(datos_doc.get('edad_int', 0)) if str(datos_doc.get('edad_int', '0')).isdigit() else 0
                    
                    pdf.set_fill_color(*c_label)
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(30, h, safe_text(" Nombre:"), 0, 0, 'L', fill=True)
                    pdf.set_fill_color(*c_valor)
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(ancho_disponible - 30, h, safe_text(f" {paciente_nombre}"), 0, 1, 'L', fill=True)
                    pdf.ln(0.5)
                    
                    pdf.set_fill_color(*c_label)
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(30, h, safe_text(" RUT/Doc:"), 0, 0, 'L', fill=True)
                    pdf.set_fill_color(*c_valor)
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(w_col - 30, h, safe_text(f" {paciente_rut}"), 0, 0, 'L', fill=True)
                    
                    pdf.set_x(x_col2)
                    pdf.set_fill_color(*c_label)
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(30, h, safe_text(" Email:"), 0, 0, 'L', fill=True)
                    pdf.set_fill_color(*c_valor)
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(w_col - 30, h, safe_text(f" {email_val}"), 0, 1, 'L', fill=True)
                    
                    pdf.set_fill_color(*c_label)
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(30, h, safe_text(" F. Nac:"), 0, 0, 'L', fill=True)
                    pdf.set_fill_color(*c_valor)
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(w_col - 30, h, safe_text(f" {fecha_nacimiento_val}"), 0, 0, 'L', fill=True)
                    
                    pdf.set_x(x_col2)
                    pdf.set_fill_color(*c_label)
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(30, h, safe_text(" Edad:"), 0, 0, 'L', fill=True)
                    pdf.set_fill_color(*c_valor)
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(w_col - 30, h, safe_text(f" {edad_formateada}"), 0, 1, 'L', fill=True)
                    pdf.ln(0.5)
                    
                    pdf.set_fill_color(*c_label)
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(40, h, safe_text(" Procedimiento:"), 0, 0, 'L', fill=True)
                    pdf.set_fill_color(*c_valor)
                    pdf.set_font('Arial', '', 9)
                    pdf.multi_cell(ancho_disponible - 40, h, safe_text(str(datos_doc.get('procedimiento', 'ERROR'))), 0, 'L', fill=True)
                    pdf.ln(0.5)
                    
                    if rep_nombre or edad_int < 18:
                        pdf.set_fill_color(*c_label)
                        pdf.set_font('Arial', 'B', 9)
                        pdf.cell(30, h, safe_text(" Representante:"), 0, 0, 'L', fill=True)
                        pdf.set_fill_color(*c_valor)
                        pdf.set_font('Arial', '', 9)
                        pdf.cell(w_col - 30, h, safe_text(f" {rep_nombre if rep_nombre else 'N/A'}"), 0, 0, 'L', fill=True)
                        
                        pdf.set_x(x_col2)
                        pdf.set_fill_color(*c_label)
                        pdf.set_font('Arial', 'B', 9)
                        pdf.cell(30, h, safe_text(" Parentesco:"), 0, 0, 'L', fill=True)
                        pdf.set_fill_color(*c_valor)
                        pdf.set_font('Arial', '', 9)
                        pdf.cell(w_col - 30, h, safe_text(f" {datos_doc.get('parentesco_tutor', 'N/A')}"), 0, 1, 'L', fill=True)
                    
                        if datos_doc.get('sin_rut_tutor'):
                            rep_rut_final = f"{datos_doc.get('tipo_doc_tutor', 'Doc')}: {datos_doc.get('num_doc_tutor', 'S/N')}"
                        else:
                            rep_rut_final = datos_doc.get('rut_tutor', 'S/R')
                    
                        pdf.set_fill_color(*c_label)
                        pdf.set_font('Arial', 'B', 9)
                        pdf.cell(40, h, safe_text(" Doc. Representante:"), 0, 0, 'L', fill=True)
                        pdf.set_fill_color(*c_valor)
                        pdf.set_font('Arial', '', 9)
                        pdf.cell(ancho_disponible - 40, h, safe_text(f" {rep_rut_final}"), 0, 1, 'L', fill=True)
                    pdf.ln(2)    
                    
                    pdf.section_title("2", "BIOSEGURIDAD MAGNETICA")
                    pdf.set_font('Arial', '', 9)
                    
                    val_marcapaso = parse_bool_clinico(datos_doc.get('bio_marcapaso', 'No'))
                    val_implantes = parse_bool_clinico(datos_doc.get('bio_implantes', 'No'))
                    det_bio = det_bio if det_bio else "Sin observaciones"
                    
                    pdf.set_fill_color(245, 245, 245) 
                    pdf.set_font('Arial', 'B', 9)
                    
                    pdf.cell(40, 6, safe_text(" Marcapasos cardiaco:"), 0, 0, 'L', fill=True)
                    pdf.set_fill_color(252, 252, 252) 
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(50, 6, safe_text(f" {val_marcapaso}"), 0, 0, 'L', fill=True)
                    
                    pdf.set_fill_color(245, 245, 245)
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(50, 6, safe_text(" Implantes/Prótesis:"), 0, 0, 'L', fill=True)
                    pdf.set_fill_color(252, 252, 252)
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(40, 6, safe_text(f" {val_implantes}"), 0, 1, 'L', fill=True) 
                    
                    pdf.set_fill_color(245, 245, 245)
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(35, 6, safe_text(" Detalle Bioseguridad:"), 0, 0, 'L', fill=True)
                    
                    pdf.set_fill_color(252, 252, 252)
                    pdf.set_font('Arial', 'I', 9)
                    pdf.multi_cell(145, 6, safe_text(det_bio), 0, 'L', fill=True)
                    
                    pdf.ln(2)

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
                    
                    h = 4.5 
                    w_col = ancho_disponible / 4 
                    
                    y_grilla_start = pdf.get_y()
                    
                    for i in range(0, len(clinicos), 4):
                        fila = clinicos[i:i+4]
                        
                        for idx, (label, valor) in enumerate(fila):
                            if genero == "Masculino" and label in ["Embarazo", "Lactancia"]:
                                valor = "N/A"
                            
                            pdf.set_x(margen_izquierdo + (idx * w_col))
                            
                            pdf.set_font('Arial', 'B', 8)
                            pdf.set_fill_color(245, 245, 245)
                            pdf.cell(30, h, safe_text(f" {label}"), 0, 0, 'L', fill=True)
                            
                            pdf.set_font('Arial', '', 8)
                            pdf.set_fill_color(252, 252, 252)
                            pdf.cell(15, h, safe_text(f"{valor}"), 0, 0, 'C', fill=True)
                            
                        pdf.ln(h) 
                    
                    pdf.ln(2) 
                        
                    detalle_alergia = datos_doc.get('alergias_detalles', '').strip()
                    if parse_bool_clinico(datos_doc.get('clin_alergico', 'No')) == "Sí" and detalle_alergia:
                        pdf.ln(1) 
                        pdf.set_font('Arial', 'B', 9)
                        pdf.set_fill_color(245, 245, 245)
                        pdf.cell(40, h, safe_text(" Alergias:"), 0, 0, 'L', fill=True)
                        
                        pdf.set_font('Arial', 'I', 9)
                        pdf.set_fill_color(252, 252, 252)
                        pdf.cell(140, h, safe_text(f" {detalle_alergia}"), 0, 1, 'L', fill=True)
                    
                    condiciones_list = datos_doc.get("condiciones", [])
                    detalle_cond = datos_doc.get("condicion_detalle", "").strip()
                    
                    if condiciones_list or detalle_cond:
                        pdf.ln(1)
                        
                        texto_categorias = ', '.join(condiciones_list) if condiciones_list else "Sin especificar"
                        
                        pdf.set_font('Arial', 'B', 9)
                        pdf.set_fill_color(245, 245, 245)
                        pdf.cell(40, h, safe_text(" Condición:"), 0, 0, 'L', fill=True)
                        
                        pdf.set_font('Arial', '', 9)
                        pdf.set_fill_color(252, 252, 252)
                        pdf.cell(140, h, safe_text(f" {texto_categorias}"), 0, 1, 'L', fill=True)
                    
                        if detalle_cond:
                            pdf.set_font('Arial', 'B', 9)
                            pdf.set_fill_color(245, 245, 245)
                            pdf.cell(30, h, safe_text(" Detalle:"), 0, 0, 'L', fill=True)
                            
                            pdf.set_font('Arial', 'I', 9)
                            pdf.set_fill_color(252, 252, 252)
                            pdf.multi_cell(150, h, safe_text(f" {detalle_cond}"), 0, 'L', fill=True)
                    
                    pdf.ln(2)
                    
                    pdf.section_title("4", "ANTECEDENTES QUIRURGICOS Y TERAPEUTICOS")
                    pdf.set_font('Arial', '', 9)
                    
                    pdf.set_fill_color(245, 245, 245) 
                    pdf.set_text_color(0, 0, 0)
                    
                    val_cirugia = parse_bool_clinico(datos_doc.get('quir_cirugia_check', 'No'))
                    det_cir = datos_doc.get('quir_cirugia_detalle', '')
                    det_cir = det_cir if det_cir else "N/A"
                    
                    pdf.set_font('Arial', 'B', 9)
                    pdf.set_fill_color(245, 245, 245)
                    pdf.cell(20, 6, safe_text(" Cirugías:"), 0, 0, 'L', fill=True) 
                    
                    pdf.set_font('Arial', '', 9)
                    pdf.set_fill_color(252, 252, 252)
                    pdf.cell(25, 6, safe_text(f" {val_cirugia}"), 0, 0, 'L', fill=True) 
                    
                    pdf.set_font('Arial', 'I', 8)
                    pdf.set_fill_color(252, 252, 252)
                    pdf.multi_cell(135, 6, safe_text(f" Detalle: {det_cir}"), 0, 'L', fill=True)
                    
                    trats_dict = {"RT": datos_doc.get('rt', False), "QT": datos_doc.get('qt', False), "BT": datos_doc.get('bt', False), "IT": datos_doc.get('it', False)}
                    trats = [k for k, v in trats_dict.items() if v in [True, "Sí", "SI", "si", 1, "true", "Si"]]
                    val_trats = ", ".join(trats) if trats else "Ninguno"
                    otr_trat = datos_doc.get('quir_otro_trat', '')
                    det_otr_trat = otr_trat if otr_trat else "N/A"
                    
                    pdf.ln(1) 
                    
                    pdf.set_font('Arial', 'B', 9)
                    pdf.set_fill_color(245, 245, 245)
                    pdf.cell(25, 6, safe_text(" Tratamientos:"), 0, 0, 'L', fill=True) 
                    
                    pdf.set_font('Arial', '', 8) 
                    pdf.set_fill_color(252, 252, 252)
                    pdf.cell(20, 6, safe_text(f" {val_trats}"), 0, 0, 'L', fill=True) 
                    
                    pdf.set_font('Arial', 'I', 8)
                    pdf.set_fill_color(252, 252, 252)
                    pdf.multi_cell(135, 6, safe_text(f" Detalle: {det_otr_trat}"), 0, 'L', fill=True)
                    
                    pdf.ln(2)

                    pdf.section_title("5", "EXAMENES ANTERIORES")
                    ex_dict = {"Rx": datos_doc.get('ex_rx', False), "MG": datos_doc.get('ex_mg', False), "Eco": datos_doc.get('ex_eco', False), "TC": datos_doc.get('ex_tc', False), "RM": datos_doc.get('ex_rm', False)}
                    ex_list = [k for k, v in ex_dict.items() if v in [True, "Sí", "SI", "si", 1, "true", "Si"]]
                    
                    pdf.set_font('Arial', '', 9)
                    pdf.data_field("Exámenes", ", ".join(ex_list) if ex_list else "Ninguno", h=5)
                    
                    pdf.set_font('Arial', 'I', 8)
                    ex_otr = datos_doc.get('ex_otros', '')
                    pdf.data_field("Otros exámenes anteriores", ex_otr if ex_otr else "N/A", h=4.5)
                    
                    pdf.ln(2)

                    pdf.section_title("6", "REGISTRO DE ADMINISTRACION FARMACOLOGICA Y EVALUACION DE LA FUNCION RENAL")
                    
                    crea_float = float(st.session_state.get('pdf_creatinina', 0.0))
                    peso_float = float(st.session_state.get('pdf_peso', 0.0))
                    talla_float = float(st.session_state.get('pdf_talla', 0.0))
                    vfg_float = float(st.session_state.get('pdf_vfg', 0.0))
                    es_pediatrico = st.session_state.get('pdf_es_pediatrico', False)

                    crea_text = f"{crea_float:.2f} mg/dL" if crea_float > 0 else "__________ mg/dL"
                    if es_pediatrico:
                        peso_talla_lbl = "Talla (Pediátrico):"
                        peso_talla_val = f"{talla_float:.1f} cm" if talla_float > 0 else "__________ cm"
                    else:
                        peso_talla_lbl = "Peso (Adulto):"
                        peso_talla_val = f"{peso_float:.1f} kg" if peso_float > 0 else "__________ kg"

                    pdf.set_font('Arial', 'B', 9)
                    pdf.set_text_color(0, 0, 0)
                    
                    pdf.set_fill_color(245, 245, 245)
                    pdf.cell(25, 6, " Creatinina:", 0, 0, 'L', fill=True)
                    
                    pdf.set_font('Arial', '', 9)
                    pdf.set_fill_color(252, 252, 252)
                    pdf.cell(65, 6, safe_text(f" {crea_text}"), 0, 0, 'L', fill=True)

                    pdf.set_font('Arial', 'B', 9)
                    pdf.set_fill_color(245, 245, 245)
                    pdf.cell(35, 6, safe_text(f" {peso_talla_lbl}"), 0, 0, 'L', fill=True)
                    
                    pdf.set_font('Arial', '', 9)
                    pdf.set_fill_color(252, 252, 252)
                    pdf.cell(55, 6, safe_text(f" {peso_talla_val}"), 0, 1, 'L', fill=True)

                    formula_pdf = st.session_state.get('pdf_formula', 'Fórmula no especificada')
                    msg_riesgo = st.session_state.get('pdf_mensaje', '')
                    r, g, b = st.session_state.get('pdf_color_rgb', (0,0,0))
                    is_contraste = locals().get('is_contraste', False)

                    if vfg_float > 0:
                        if not is_contraste: 
                            msg_riesgo += " (Cálculo basal)"
                        
                        label_vfg = f" V.F.G ({formula_pdf}):"
                        
                        pdf.set_font('Arial', 'B', 9)
                        w_label = pdf.get_string_width(label_vfg) + 4
                        
                        pdf.set_fill_color(245, 245, 245)
                        pdf.set_text_color(0, 0, 0)
                        pdf.cell(w_label, 6, safe_text(label_vfg), 0, 0, 'L', fill=True)
                        
                        w_resto = 180 - w_label 
                        pdf.set_fill_color(252, 252, 252)
                        x_val = pdf.get_x()
                        y_val = pdf.get_y()
                        
                        pdf.cell(w_resto, 6, "", 0, 0, 'L', fill=True)
                        
                        pdf.set_xy(x_val, y_val)
                        pdf.set_text_color(r, g, b)
                        pdf.cell(w_resto, 6, safe_text(f" {vfg_float:.2f} ml/min ({msg_riesgo})"), 0, 1, 'L')
                        
                        pdf.set_text_color(0, 0, 0) 
                    else:
                        pdf.set_font('Arial', 'B', 9)
                        pdf.set_fill_color(245, 245, 245)
                        pdf.cell(35, 6, " RESULTADO VFG:", 0, 0, 'L', fill=True)
                        
                        pdf.set_font('Arial', '', 9)
                        pdf.set_fill_color(252, 252, 252)
                        pdf.cell(145, 6, " __________ ml/min", 0, 1, 'L', fill=True)

                    pdf.ln(1)

                    pdf.set_font('Arial', 'B', 9)
                    pdf.set_text_color(0, 0, 0) 
                    pdf.cell(180, 6, safe_text("DETALLE DE ADMINISTRACIÓN"), 0, 1, 'L')
                    
                    datos_acceso_vivo = st.session_state.get('registro_acceso_vascular', {})
                    acceso_v = datos_acceso_vivo.get('resumen_acceso', datos_doc.get('acceso_venoso', 'No registrado'))
                    sitio_v = datos_acceso_vivo.get('sitio', datos_doc.get('sitio_puncion', 'No registrado'))

                    pdf.set_font('Arial', 'B', 9)
                    pdf.set_fill_color(245, 245, 245)
                    pdf.cell(30, 6, safe_text(" Acceso vascular:"), 0, 0, 'L', fill=True)
                    
                    pdf.set_font('Arial', '', 9)
                    pdf.set_fill_color(252, 252, 252)
                    pdf.cell(60, 6, safe_text(f" {acceso_v}"), 0, 0, 'L', fill=True)

                    pdf.set_font('Arial', 'B', 9)
                    pdf.set_fill_color(245, 245, 245)
                    pdf.cell(32, 6, safe_text(" Sitio de punción:"), 0, 0, 'L', fill=True)
                    
                    pdf.set_font('Arial', '', 9)
                    pdf.set_fill_color(252, 252, 252)
                    pdf.cell(58, 6, safe_text(f" {sitio_v}"), 0, 1, 'L', fill=True)

                    pdf.ln(2)
        
                    def formatear_cantidad_clinica(valor):
                        try:
                            val_float = float(valor)
                            if val_float.is_integer():
                                return str(int(val_float))
                            return f"{val_float}".replace('.', ',')
                        except:
                            return str(valor)
        
                    pdf.set_fill_color(235, 235, 235) 
                    pdf.set_text_color(0, 0, 0)
                    pdf.set_font('Arial', 'B', 8.5)
                    
                    pdf.cell(95, 6, safe_text(" Medio de contraste u otros medicamentos"), 0, 0, 'L', True)
                    pdf.cell(35, 6, safe_text("Cantidad (ml)"), 0, 0, 'C', True)
                    pdf.cell(50, 6, safe_text("Vía de administración"), 0, 1, 'C', True)
        
                    datos_farmacos = datos_doc.get('contraste_administrado', {})
                    
                    if datos_farmacos and isinstance(datos_farmacos, dict):
                        for idx, item in datos_farmacos.items():
                            nombre_f = item.get('nombre', 'No especificado')
                            cantidad_f = formatear_cantidad_clinica(item.get('dosis', '0'))
                            via_f = item.get('via', 'No especificado')
                            
                            pdf.set_fill_color(245, 245, 245)
                            pdf.set_font('Arial', 'B', 8.5)
                            pdf.cell(95, 6, safe_text(f" {nombre_f}"), 0, 0, 'L', True)
                            
                            pdf.set_fill_color(252, 252, 252)
                            pdf.set_font('Arial', '', 8.5)
                            pdf.cell(35, 6, safe_text(cantidad_f), 0, 0, 'C', True)
                            pdf.cell(50, 6, safe_text(via_f), 0, 1, 'C', True)
                    else:
                        pdf.set_fill_color(248, 248, 248)
                        pdf.set_font('Arial', 'I', 8.5)
                        pdf.cell(180, 6, safe_text(" No se registraron administraciones farmacológicas en este procedimiento."), 0, 1, 'L', True)
                            
                    pdf.ln(2) 
                    
                    pdf.add_page()
                    pdf.set_font('Arial', 'B', 10)

                    texto_procedimiento_p2 = f"Procedimiento: {datos_doc.get('procedimiento', 'PROCEDIMIENTO')}."
                    
                    pdf.set_font('Arial', 'B', 9)
                    pdf.multi_cell(0, 6, safe_text(texto_procedimiento_p2), 0, 'L')
                    pdf.ln(2) 

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
                    
                    pdf.ln(5)
                    y_pos_firmas = pdf.get_y()
                    
                    if ruta_p_local and os.path.exists(ruta_p_local):
                        pdf.image(ruta_p_local, 35, y_pos_firmas, 45, 12)
                    
                    if 'ruta_firma_tm_local' in locals() and os.path.exists(ruta_firma_tm_local):
                        pdf.image(ruta_firma_tm_local, 130, y_pos_firmas, 45, 12)
                    
                    pdf.set_y(y_pos_firmas + 8)
                    
                    pdf.set_font('Arial', '', 10) 
                    
                    nombre_paciente_pdf = datos_doc.get('nombre', 'Paciente').strip().title()
                    profesional_nombre_pdf = profesional_nombre.strip().title()
                    
                    pdf.cell(95, 4, safe_text(nombre_paciente_pdf), 0, 0, 'C')
                    pdf.cell(95, 4, safe_text(profesional_nombre_pdf), 0, 1, 'C')
                    
                    pdf.cell(95, 4, "________________________________________", 0, 0, 'C')
                    pdf.cell(95, 4, "________________________________________", 0, 1, 'C')
                    
                    pdf.set_font('Arial', 'B', 8)
                    pdf.cell(95, 4, safe_text("FIRMA PACIENTE O REPRESENTANTE LEGAL"), 0, 0, 'C')
                    pdf.cell(95, 4, safe_text("FIRMA PROFESIONAL A CARGO"), 0, 1, 'C')
                    
                    pdf.set_font('Arial', '', 8)
                    nombre_tutor_pdf = datos_doc.get('nombre_tutor', '').strip()
                    rut_tutor_pdf = datos_doc.get('rut_tutor', '').strip()
                    
                    if nombre_tutor_pdf:
                        parentesco_t_pdf = datos_doc.get('parentesco_tutor', '').strip()
                        texto_nombre_rl = f"R.L: {nombre_tutor_pdf} ({parentesco_t_pdf})" if parentesco_t_pdf else f"R.L: {nombre_tutor_pdf}"
                        pdf.cell(95, 4, safe_text(texto_nombre_rl), 0, 0, 'C')
                    else:
                        pdf.cell(95, 4, "", 0, 0, 'C')
                        
                    pdf.cell(95, 4, safe_text("TECNÓLOGO MÉDICO EN IMAGENOLOGÍA"), 0, 1, 'C')
                    
                    if nombre_tutor_pdf:
                        if datos_doc.get('sin_rut_tutor'):
                            tipo_id_tutor_pdf = datos_doc.get('tipo_doc_tutor', 'Doc').strip()
                            id_tutor_pdf = datos_doc.get('num_doc_tutor', '').strip()
                            texto_doc_rl = f"{tipo_id_tutor_pdf} R.L: {id_tutor_pdf}"
                        else:
                            texto_doc_rl = f"R.R.L: {rut_tutor_pdf}"
                            
                        pdf.cell(95, 4, safe_text(texto_doc_rl), 0, 0, 'C')
                    else:
                        pdf.cell(95, 4, "", 0, 0, 'C')
                        
                    pdf.cell(95, 4, safe_text("ESP. RESONANCIA MAGNÉTICA"), 0, 1, 'C')
                    
                    pdf.cell(95, 4, "", 0, 0, 'C')
                    pdf.cell(95, 4, safe_text(f"REGISTRO SIS: {profesional_registro}"), 0, 1, 'C') 
                    
                    pdf.ln(4)

                    # =====================================================================
                    # 💾 3. COMPILACIÓN BINARIA ESTÁNDAR Y ASIGNACIÓN DE NOMBRE OFICIAL
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
                    # Limpieza quirúrgica de archivos temporales de firmas
                    try:
                        if 'ruta_firma_tm_local' in locals() and os.path.exists(ruta_firma_tm_local):
                            os.unlink(ruta_firma_tm_local)
                        if 'ruta_p_local' in locals() and ruta_p_local and os.path.exists(ruta_p_local):
                            os.unlink(ruta_p_local)
                    except:
                        pass
                        
        else:
            # El error ahora salta SOLO si presionas el botón y el canvas está vacío
            st.error("🚨 Firma incompleta. Debe dibujar su firma digital en el recuadro para visar el procedimiento.")

    # =====================================================================
# 📥 RENDERIZADO DEL BOTÓN DE DESCARGA (INMUNE A REFRESH)
# =====================================================================

# Verificamos que las variables existan antes de intentar renderizar
if st.session_state.get('pdf_ready', False) and st.session_state.get('pdf_bytes_data') is not None:
    st.markdown("---")
    st.markdown("### 📥 Descarga de Documento Oficial")
    
    # Manejo seguro del nombre del archivo por si no se definió
    nombre_archivo = st.session_state.get('pdf_filename', 'consentimiento_firmado.pdf')
    nombre_paciente_pdf = st.session_state.get('doc_completo', {}).get('nombre', 'Paciente')
    
    st.write(f"El consentimiento institucional de **{nombre_paciente_pdf}** ha sido visado con ambas firmas.")
    
    st.download_button(
        label="📄 DESCARGAR PDF INSTITUCIONAL FIRMADO",
        data=st.session_state.pdf_bytes_data,
        file_name=nombre_archivo,
        mime="application/pdf",
        key="btn_descarga_pdf_final",
        use_container_width=True
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🧼 LIMPIAR BANDEJA"):
        st.session_state.doc_completo = {} 
        st.session_state.modo_enmienda_activo = False
        st.session_state.paciente_seleccionado = None
        # BORRADO TOTAL PARA PROTECCIÓN DEL BOTÓN DESCARGA
        st.session_state.pdf_ready = False
        st.session_state.pdf_bytes_data = None
        st.rerun()

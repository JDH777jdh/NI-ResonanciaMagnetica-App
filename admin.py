# =====================================================================
# 1. PRIMERO: TODAS LAS IMPORTACIONES DE LIBRERÍAS
# =====================================================================
import streamlit as st
import pandas as pd
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore, storage
import tempfile
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import pytz
import json
import re
import time

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
st.sidebar.markdown(f"**Registro SIS:**\n{st.session_state.current_user['sis']}")
if st.sidebar.button("🔒 Cerrar Sesión"):
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
        st.markdown("### 📥 Bandeja de Entrada: Pacientes en Sala de Espera")
    with col_btn:
        if st.button("🔄 Actualizar", use_container_width=True, key="btn_manual_refresh"):
            st.rerun()
            
    # Usamos la zona horaria definida globalmente (tz_chile)
    hora_sincro = datetime.now(tz_chile).strftime('%H:%M:%S')
    st.caption(f"✨ Conectado a Firebase Firestore • Último auto-refresco: **{hora_sincro}**")

    # 2. Consulta a Firebase
    try:
        docs_ref = db.collection("encuestas").where("estado_validacion", "==", "PENDIENTE").stream()
        listado_pacientes = [{"ID_Documento": doc.id, "RUT": doc.to_dict().get("rut", "S/R"), "Nombre": doc.to_dict().get("nombre", "Sin Nombre")} for doc in docs_ref]
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
        format_func=lambda x: f"🔹 RUT: {df_pacientes[df_pacientes['ID_Documento']==x]['RUT'].values[0]} | {df_pacientes[df_pacientes['ID_Documento']==x]['Nombre'].values[0]}",
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

    # Inicializar notas vacías
    nota_alergico = nota_dialisis = nota_renal = nota_embarazo = nota_claustro = ""

    if str(clin_alergico).strip().upper() in ["SI", "SÍ"]: nota_alergico = "Evaluar su relación al medio de contraste y necesidad de premedicación."
    if str(clin_dialisis).strip().upper() in ["SI", "SÍ"]: nota_dialisis = "No se debe inyectar medio de contraste basado en Gadolinio."
    if str(clin_renal).strip().upper() in ["SI", "SÍ"]: nota_renal = "Se debe considerar la VFG para la administración de medio de contraste."
    if str(clin_embarazo).strip().upper() in ["SI", "SÍ"]: nota_embarazo = "Precaución, paciente de alto cuidado."
    if str(clin_claustro).strip().upper() in ["SI", "SÍ"]: nota_claustro = "Puede requerir atención personalizada."
    
    # INYECCIÓN AL DICCIONARIO
    datos_doc.update({
        'nota_alergico': nota_alergico,
        'nota_dialisis': nota_dialisis,
        'nota_renal': nota_renal,
        'nota_embarazo': nota_embarazo,
        'nota_claustro': nota_claustro
    })
    
    # 🧪 Parámetros Métricos y resto de variables...
    creatinina_val = form_interno.get('creatinina', datos_doc.get('creatinina', 'N/A'))
    peso_val = form_interno.get('peso', datos_doc.get('peso', 'N/A'))
    vfg_valor = form_interno.get('vfg', datos_doc.get('vfg', 0.0))
    is_contraste_visual = datos_doc.get('tiene_contraste', form_interno.get('tiene_contraste', False)) in [True, "Sí", "SI", "si", "Si"]
    procedimiento_val_visual = datos_doc.get('procedimiento', form_interno.get('procedimiento', 'No especificado'))
    ip_cliente = datos_doc.get('ip_dispositivo', datos_doc.get('ip', form_interno.get('ip_dispositivo', form_interno.get('ip', 'No detectada'))))
    
    # 🔥 IMPORTANTE: Guardamos el objeto enriquecido
    st.session_state.doc_completo = datos_doc


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

# --- 2. LOGO CORREGIDO ---
try:
    st.image("logoNI.png", width=200)
except Exception:
    st.warning("No se pudo cargar 'logoNI.png'. Verifica que esté en la raíz del repositorio.")

# =====================================================================
# 🟢 RENDERIZADO EN 2 COLUMNAS CON DISTRIBUCIÓN ESPECÍFICA (DATOS REALES)
# =====================================================================
# Extraemos el diccionario real del estado de la sesión
datos_doc = st.session_state.get('doc_completo', {})

if datos_doc:
    st.divider()
    c1, c2 = st.columns([1, 1])

    # =============================================================================
    # COLUMNA 1: FICHA DE ATENCIÓN CLÍNICA, BIOSEGURIDAD Y ANTECEDENTES CLÍNICOS
    # =============================================================================
    with c1:
        # --- A. FICHA DE ATENCIÓN CLÍNICA ---
        st.markdown("#### 👤 Ficha de Atención Clínica")
        sub_c1, sub_c2 = st.columns(2)
        with sub_c1:
            st.write(f"**Nombre:**\n{datos_doc.get('nombre', 'N/A')}")
            st.write(f"**Edad:**\n{datos_doc.get('edad', 'N/A')} años")
        with sub_c2:
            st.write(f"**RUT:**\n{datos_doc.get('rut', 'N/A')}")
            st.write(f"**Teléfono:**\n{datos_doc.get('telefono', 'N/A')}")

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
                st.write(f"**Nombre:**\n{datos_doc.get('nombre_tutor', datos_doc.get('rep_legal_nombre', 'No registrado'))}")
            with sub_rep2:
                st.write(f"**RUT:**\n{datos_doc.get('rut_tutor', datos_doc.get('rep_legal_rut', 'N/A'))}")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- B. BIOSEGURIDAD MAGNÉTICA ---
        with st.expander("🧲 2. BIOSEGURIDAD MAGNÉTICA", expanded=True):
            # 1. Marcapasos cardíaco
            tiene_marcapaso = evaluar_si_no(datos_doc.get('bio_marcapaso'))
            st.write(f"**Marcapasos cardíaco:** {'🔴 SÍ' if tiene_marcapaso else '✅ NO'}")
            if tiene_marcapaso and datos_doc.get('nota_marcapaso'):
                st.warning(datos_doc.get('nota_marcapaso'))

            # 2. Implantes / Prótesis
            tiene_implantes = evaluar_si_no(datos_doc.get('bio_implantes'))
            st.write(f"**Implantes / Prótesis / Dispositivos:** {'🔴 SÍ' if tiene_implantes else '✅ NO'}")
            if tiene_implantes and datos_doc.get('nota_implante'):
                st.warning(datos_doc.get('nota_implante'))

            # 3. Detalle de Bioseguridad
            st.write("**Detalle Bioseguridad:**")
            st.info(datos_doc.get('bio_detalle') if datos_doc.get('bio_detalle') else "Sin observaciones")

        # --- C. ANTECEDENTES CLÍNICOS (TABLA DE RIESGOS VINCULADA) ---
        with st.expander("📋 3. ANTECEDENTES CLÍNICOS", expanded=True):
            data_riesgos = {
                "Antecedente Clínico": [
                    "Ayuno 2hrs+", "Asma", "Alergias", "Hipertensión", 
                    "Hipotiroidismo", "Diabetes", "Metformina 48h", 
                    "Insuficiencia Renal", "Diálisis", "Embarazo", 
                    "Lactancia", "Claustrofobia"
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
                    "🔴 SÍ" if evaluar_si_no(datos_doc.get('clin_claustro')) else "✅ NO"
                ],
                "Recomendación / Alerta": [
                    "", "", datos_doc.get('nota_alergico', '') if evaluar_si_no(datos_doc.get('clin_alergico')) else "",
                    "", "", "", "",
                    datos_doc.get('nota_renal', '') if evaluar_si_no(datos_doc.get('clin_renal')) else "",
                    datos_doc.get('nota_dialisis', '') if evaluar_si_no(datos_doc.get('clin_dialisis')) else "",
                    datos_doc.get('nota_embarazo', '') if evaluar_si_no(datos_doc.get('clin_embarazo')) else "",
                    "", datos_doc.get('nota_claustro', '') if evaluar_si_no(datos_doc.get('clin_claustro')) else ""
                ]
            }
            st.table(pd.DataFrame(data_riesgos))

    # =============================================================================
    # COLUMNA 2: EVALUACIÓN DE FUNCIÓN RENAL, CIRUGÍAS Y TRATAMIENTOS, EXÁMENES ANT.
    # =============================================================================
    with c2:
        # --- A. EVALUACIÓN DE LA FUNCIÓN RENAL (EDICIÓN EN TIEMPO REAL) ---
        with st.expander("🧪 6. EVALUACIÓN DE LA FUNCIÓN RENAL", expanded=True):
            
            # 1. Extracción segura de la base de datos e inicialización
            es_estudio_basal = not datos_doc.get('tiene_contraste', False)
            
            try:
                creatinina_base = float(datos_doc.get('creatinina', 0.0))
                peso_base = float(datos_doc.get('peso', 0.0))
            except (ValueError, TypeError):
                creatinina_base, peso_base = 0.0, 0.0

            # Si es sin contraste y el sistema arrojó el 70 por defecto, lo forzamos a 0.0
            if es_estudio_basal and peso_base == 70.0:
                peso_base = 0.0

            # 2. Celdas de edición interactiva para el profesional
            st.markdown("<span style='font-size: 13px; color: #666;'><b>Ajuste de Parámetros Clínicos:</b></span>", unsafe_allow_html=True)
            col_p, col_c = st.columns(2)
            
            with col_p:
                peso_profesional = st.number_input(
                    "Peso (kg):",
                    min_value=0.0, max_value=250.0, value=peso_base, step=1.0,
                    help="Deje en 0.0 para estudios basales (mostrará 00 kg en el PDF final)."
                )

            with col_c:
                creatinina_profesional = st.number_input(
                    "Creatinina (mg/dL):",
                    min_value=0.0, max_value=15.0, value=creatinina_base, step=0.01,
                    help="Deje en 0.0 si no aplica medición de función renal."
                )

            # 3. Cálculo automatizado de VFG en tiempo real con las variables recién editadas
            vfg_dinamico = 0.0
            if peso_profesional > 0 and creatinina_profesional > 0:
                edad_paciente = int(datos_doc.get('edad_num', 17))
                sexo_paciente = datos_doc.get('sexo', 'Masculino')
                factor_sexo = 0.85 if "Fem" in str(sexo_paciente) or datos_doc.get('es_mujer', False) else 1.0
                
                try:
                    vfg_dinamico = ((140 - edad_paciente) * peso_profesional) / (72 * creatinina_profesional) * factor_sexo
                except ZeroDivisionError:
                    vfg_dinamico = 0.0

            # 4. Determinación de estado clínico (Aplicado al VFG dinámico)
            if peso_profesional == 0 or creatinina_profesional == 0:
                riesgo_estado = "Parámetros Incompletos / Estudio Basal"
                color_indicador = "#888" # Gris
                flecha = ""
            elif vfg_dinamico <= 30.0:
                riesgo_estado = "Alto Riesgo"
                color_indicador = "#FF4B4B" # Rojo
                flecha = "▼"
            elif vfg_dinamico <= 59.0:
                riesgo_estado = "Riesgo Intermedio"
                color_indicador = "#FFA500" # Naranja
                flecha = "▼"
            else:
                riesgo_estado = "Sin Riesgo"
                color_indicador = "#00D26A" # Verde
                flecha = "▲"

            # 5. Renderizado visual HTML (Usando las variables conectadas al st.number_input)
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; margin-top: 10px; border-top: 1px solid #eee;">
                <div style="text-align: center;">
                    <span style="font-size: 11px; color: #666;">Creat.</span><br>
                    <span style="font-size: 16px; font-weight: bold;">{creatinina_profesional:.2f} <span style="font-size: 10px;">mg/dL</span></span>
                </div>
                <div style="text-align: center;">
                    <span style="font-size: 11px; color: #666;">Peso</span><br>
                    <span style="font-size: 16px; font-weight: bold;">{peso_profesional:.1f} <span style="font-size: 10px;">Kg</span></span>
                </div>
                <div style="text-align: center;">
                    <span style="font-size: 11px; color: #666;">VFG</span><br>
                    <span style="font-size: 16px; font-weight: bold; color: {color_indicador};">{flecha} {vfg_dinamico:.2f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"<div style='text-align: center; color: {color_indicador}; font-weight: bold; margin-top: 5px;'>{riesgo_estado}</div>", unsafe_allow_html=True)

            # 6. Almacenamos el resultado final en el estado para que el constructor del PDF lo lea
            st.session_state.pdf_peso = peso_profesional
            st.session_state.pdf_creatinina = creatinina_profesional
            st.session_state.pdf_vfg = vfg_dinamico

       # --- B. ANTECEDENTES QUIRÚRGICOS Y TERAPÉUTICOS ---
        with st.expander("🏥 4. ANTECEDENTES QUIRÚRGICOS Y TERAPÉUTICOS", expanded=True):
            # Inyectamos evaluar_si_no() aquí para traducir el texto "Sí" o "No"
            st.write(f"**Cirugías:** {'🔴 SÍ' if evaluar_si_no(datos_doc.get('quir_cirugia_check')) else '✅ NO'}")
            st.write("**Detalle Cirugías:**")
            st.caption(datos_doc.get('quir_cirugia_detalle') if datos_doc.get('quir_cirugia_detalle') else "N/A")
            
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

    # 3. FIRMA DIGITAL
    st.markdown("#### ✍️ Firma Digital")
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
            stroke_width=3,
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
                    paciente_rut = datos_doc.get('rut', datos_doc.get('run', 'S/R'))
                    fecha_nacimiento_val = datos_doc.get('fecha_nac', datos_doc.get('fecha_nacimiento', 'N/A'))
                    if hasattr(fecha_nacimiento_val, 'strftime'):
                        fecha_nacimiento_val = fecha_nacimiento_val.strftime('%d/%m/%Y')
                    email_val = datos_doc.get('email', 'N/A')
                    procedimiento_val = datos_doc.get('procedimiento', 'RM General')

                    genero = str(datos_doc.get('genero_idx', datos_doc.get('sexo', 'No especificado'))).strip().capitalize()
                    if genero in ["0", "Masculino", "M", "Hombre", "Masculina"]: genero = "Masculino"
                    elif genero in ["1", "Femenino", "F", "Mujer"]: genero = "Femenino"
                    elif genero == "2": genero = "No binario"

                    # Sincronización estricta del indicador de contraste
                    is_contraste = datos_doc.get('tiene_contraste', False) in [True, "Sí", "SI", "si", "Si"]
                    
                    rep_nombre = datos_doc.get('nombre_tutor', '')
                    rep_rut = datos_doc.get('rut_tutor', '')

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
                                 datos_doc.get('form_interno', {}).get('ip_dispositivo', 
                                 datos_doc.get('form_interno', {}).get('ip', 'IP No detectada')))))
                    
                    fecha_validacion_str = datetime.now(tz_chile).strftime("%d/%m/%Y %H:%M:%S")
                    paciente_nombre = datos_doc.get('nombre', 'Paciente')
                    paciente_rut = datos_doc.get('rut', 'N/A')

                    # 1. Instanciamos el motor pasando la IP correcta
                    pdf = PDF_Institucional(paciente_nombre, paciente_rut, ip_cliente, fecha_validacion_str)
                    
                    # 🚀 INYECCIÓN QUIRÚRGICA: Forzamos los atributos exactos que lee tu 'def footer'
                    pdf.p_nombre = paciente_nombre
                    pdf.p_rut = paciente_rut
                    pdf.f_val = datos_doc.get('fecha', datetime.now(tz_chile).strftime("%d/%m/%Y")) # Fecha del examen base
                    pdf.p_ip = ip_cliente
                    pdf.datos_doc = datos_doc  # Respaldo completo del diccionario
                    
                    # 2. Inicialización de páginas
                    pdf.alias_nb_pages()
                    pdf.add_page()
                    pdf.set_auto_page_break(auto=True, margin=12)

                    # --- ENCABEZADO FECHA ---
                    pdf.set_font('Arial', 'B', 9)
                    # 🟢 Añadimos safe_text para blindar la celda contra fallos de encoding
                    pdf.cell(0, 5, safe_text(f"Fecha de examen: {fecha_validacion_str.split()[0]}"), 0, 1, 'R') 
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
                    pdf.cell(18, 5, "RUT: ", 0, 0)
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(w_col - 18, 5, safe_text(paciente_rut), 0, 0)
                    
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
                        pdf.cell(35, 5, "RUT Representante: ", 0, 0)
                        pdf.set_font('Arial', '', 9)
                        pdf.cell(w_col - 35, 5, safe_text(rep_rut if rep_rut else 'N/A'), 0, 1)

                    pdf.ln(4)

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
                    
                    # 🚀 EXTRACCIÓN CENTRALIZADA Y SEGURA: Castigo estricto a flotante para evitar caídas por strings o None
                    try:
                        crea_float = float(st.session_state.get('pdf_creatinina', 0.0))
                    except (ValueError, TypeError):
                        crea_float = 0.0

                    try:
                        peso_float = float(st.session_state.get('pdf_peso', 0.0))
                    except (ValueError, TypeError):
                        peso_float = 0.0

                    try:
                        vfg_float = float(st.session_state.get('pdf_vfg', 0.0))
                    except (ValueError, TypeError):
                        vfg_float = 0.0
                    
                    if is_contraste:
                        creatinina_val_pdf = f"{crea_float:.2f} mg/dL" if crea_float > 0 else "__________ mg/dL"
                        pdf.data_field("Creatinina", creatinina_val_pdf, h=5)

                        peso_texto = f"{peso_float:.1f} kg" if peso_float > 0 else "__________ kg"
                        pdf.data_field("Peso", peso_texto, h=5)
                        
                        # 🔍 SOLUCIÓN DE TRANSMISIÓN: Evaluamos el VFG de manera independiente. Si el valor existe, se estampa.
                        if vfg_float > 0:
                            if vfg_float <= 30.0:
                                r, g, b = 255, 0, 0 # Rojo Crítico
                                msg_riesgo = "ALTO RIESGO para la administración de medio de contraste"
                            elif vfg_float <= 59.0:
                                r, g, b = 184, 134, 11 # Amarillo / Oro Oscuro (Legible en papel)
                                msg_riesgo = "RIESGO INTERMEDIO para la administración de medio de contraste"
                            else:
                                r, g, b = 34, 139, 34 # Verde Clínico
                                msg_riesgo = "SIN RIESGOS para la administración de medio de contraste"

                            # 🔥 SOLUCIÓN COLOR: Escribimos el campo saltándonos data_field para que respectete el color clínico
                            pdf.set_font('Arial', 'B', 9)
                            pdf.set_text_color(50, 50, 50) # Gris para la etiqueta V.F.G
                            pdf.write(5, safe_text("V.F.G: "))
                            
                            pdf.set_font('Arial', 'B', 9)
                            pdf.set_text_color(r, g, b)    # Inyecta Rojo, Amarillo o Verde según corresponda
                            pdf.write(5, safe_text(f"{vfg_float:.2f} ml/min  ({msg_riesgo})\n"))
                            
                            pdf.set_text_color(0, 0, 0)    # Volver a negro estándar inmediatamente
                        else:
                            pdf.data_field("RESULTADO VFG", "__________ ml/min (Cálculo manual)", h=5)
                    else:
                        # Si es un estudio basal pero el profesional igual registró datos, los mostramos limpios
                        txt_crea_b = f"{crea_float:.2f} mg/dL" if crea_float > 0 else "__________ mg/dL"
                        txt_peso_b = f"{peso_float:.1f} kg" if peso_float > 0 else "__________ kg"
                        
                        pdf.data_field("Creatinina", txt_crea_b, h=5)
                        pdf.data_field("Peso", txt_peso_b, h=5)
                        pdf.data_field("RESULTADO VFG", "__________ ml/min", h=5)
                        
                    pdf.ln(2)

                    # --- SECCIÓN 7: REGISTRO DE ADMINISTRACIÓN EN BLANCO PARA ENFERMERÍA ---
                    pdf.section_title("7", "REGISTRO DE ADMINISTRACION DE CONTRASTE")
                    
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
                    opciones_acceso = "[     ] Branula: ____ G  [     ] Mariposa: ____ G"
                    pdf.cell(w_col_7, 8, safe_text(opciones_acceso), 0, 0, 'L') 
                    
                    pdf.set_xy(x_col7_derecha, y_inputs1)
                    pdf.cell(w_col_7, 8, safe_text("________________________________"), 0, 1, 'L')
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
                    pdf.cell(w_col_7, 5, safe_text("___________ ml."), 0, 1, 'L')
                    
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
                    pdf.set_font('Arial', '', 8)
                    nombre_paciente_pdf = datos_doc.get('nombre', 'Paciente').strip()
                    
                    pdf.cell(95, 4, safe_text(nombre_paciente_pdf), 0, 0, 'C')
                    pdf.cell(95, 4, safe_text(profesional_nombre), 0, 1, 'C') # Variable dinámica real
                    
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
                        pdf.cell(95, 4, safe_text(f"R.L: {nombre_tutor_pdf}"), 0, 0, 'C')
                    else:
                        pdf.cell(95, 4, "", 0, 0, 'C')
                        
                    pdf.cell(95, 4, safe_text("Tecnólogo Médico en Imagenología"), 0, 1, 'C')
                    
                    if nombre_tutor_pdf:
                        pdf.cell(95, 4, safe_text(f"R.R.L: {rut_tutor_pdf}"), 0, 0, 'C')
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
            # 1. Limpiamos solo las variables activas
            st.session_state.paciente_seleccionado = None
            st.session_state.doc_completo = None
            st.session_state.pdf_ready = False
            st.session_state.pdf_bytes_data = None
            
            # 2. Retraso táctico para evitar leer la caché vieja de Firestore
            time.sleep(0.5) 
            
            # 3. Reiniciamos la interfaz
            st.rerun()
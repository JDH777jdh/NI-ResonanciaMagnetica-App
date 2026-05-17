import streamlit as st
import pandas as pd
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore, storage
import tempfile
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import pytz

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Panel de Validación Técnica - RM", layout="wide")

# --- CONFIGURACIÓN DE ZONA HORARIA ---
tz_chile = pytz.timezone('America/Santiago')

# === INICIALIZACIÓN SEGURA DE FIREBASE ADMIN SDK ===
if not firebase_admin._apps:
    try:
        fb_credentials = {
            "type": st.secrets["firebase"]["type"],
            "project_id": st.secrets["firebase"]["project_id"],
            "private_key_id": st.secrets["firebase"]["private_key_id"],
            "private_key": st.secrets["firebase"]["private_key"].replace("\\n", "\n"),
            "client_email": st.secrets["firebase"]["client_email"],
            "client_id": st.secrets["firebase"]["client_id"],
            "auth_uri": st.secrets["firebase"]["auth_uri"],
            "token_uri": st.secrets["firebase"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"],
            "universe_domain": st.secrets["firebase"]["universe_domain"]
        }
        cred = credentials.Certificate(fb_credentials)
        firebase_admin.initialize_app(cred, {
            'storageBucket': st.secrets["firebase"]["bucket_url"]
        })
    except Exception as e:
        st.error(f"🚨 Error de conexión con la infraestructura central: {e}")

db = firestore.client()
bucket = storage.bucket()

# --- HEADER DEL PANEL ---
st.title("🏥 Servicio de Resonancia Magnética")
st.subheader("👨‍⚕️ Panel de Control y Validación de Seguridad (Tecnólogo Médico)")
st.divider()

# =============================================================================
# --- SISTEMA DE AUTENTICACIÓN INDIVIDUALIZADO (Cero Suplantación) ---
# =============================================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.current_user = None

if not st.session_state.authenticated:
    st.warning("🔒 Acceso Restringido. Ingrese sus credenciales de Tecnólogo Médico.")
    col1, col2 = st.columns([1, 2])
    with col1:
        pin_ingresado = st.text_input("Ingrese su Clave Personal (PIN):", type="password")
        if st.button("Ingresar al Sistema"):
            # Buscar el PIN dentro de la lista de secrets del hospital
            usuarios = st.secrets.get("usuarios_rm", {})
            if pin_ingresado in usuarios:
                st.session_state.authenticated = True
                # Guardamos los datos reales del profesional en la sesión
                st.session_state.current_user = usuarios[pin_ingresado]
                st.success(f"🔓 Bienvenido(a), TM {st.session_state.current_user['nombre']}")
                st.rerun()
            else:
                st.error("🔑 Clave incorrecta o profesional no autorizado.")
    st.stop()

# --- BOTÓN PARA CERRAR SESIÓN ---
st.sidebar.markdown(f"**Usuario:**\nTM {st.session_state.current_user['nombre']}")
st.sidebar.markdown(f"**Registro SIS:**\n{st.session_state.current_user['sis']}")
if st.sidebar.button("🔒 Cerrar Sesión"):
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.rerun()

# =============================================================================
# --- LOGICA CORE: LEER ENCUESTAS PENDIENTES ---
# =============================================================================
st.markdown("### 📥 Bandeja de Entrada: Pacientes en Sala de Espera")

# Traer los documentos desde Firestore
docs_ref = db.collection("encuestas_pendientes").where("estado_validacion", "==", "PENDIENTE AUDITORIA").stream()

listado_pacientes = []
for doc in docs_ref:
    data = doc.to_dict()
    listado_pacientes.append({
        "ID_Documento": doc.id,
        "RUT": data.get("rut", "S/R"),
        "Nombre": data.get("nombre", "Sin Nombre"),
        "Edad": data.get("edad", "N/A"),
        "VFG": data.get("vfg", 0.0),
        "Alergias": data.get("alergias", "No")
    })

if not listado_pacientes:
    st.info("🟢 No hay encuestas pendientes por revisar. Sala de espera despejada.")
else:
    df_pacientes = pd.DataFrame(listado_pacientes)
    
    # Selector visual para escoger a qué paciente auditar
    paciente_seleccionado = st.selectbox(
        "🔎 Seleccione el paciente para revisar antecedentes y autorizar examen:",
        options=df_pacientes["ID_Documento"],
        format_func=lambda x: f"🔹 RUT: {df_pacientes[df_pacientes['ID_Documento']==x]['RUT'].values[0]} | {df_pacientes[df_pacientes['ID_Documento']==x]['Nombre'].values[0]}"
    )
    
    # Recuperar la información completa del paciente seleccionado
    doc_completo = db.collection("encuestas_pendientes").document(paciente_seleccionado).get().to_dict()
    
    st.divider()
    
    # Desplegar la ficha clínica del paciente en dos columnas organizadas
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("#### 👤 Datos Demográficos")
        st.write(f"**Nombre:** {doc_completo.get('nombre')}")
        st.write(f"**RUT:** {doc_completo.get('rut')}")
        st.write(f"**Edad:** {doc_completo.get('edad')} años")
        st.write(f"**Teléfono:** {doc_completo.get('telefono')}")
        
        st.markdown("#### 🧪 Parámetros Clínicos Críticos")
        st.write(f"**Creatinina:** {doc_completo.get('creatinina')} mg/dL")
        st.write(f"**Peso:** {doc_completo.get('peso')} Kg")
        vfg_valor = doc_completo.get('vfg', 0.0)
        if vfg_valor < 30.0:
            st.error(f"⚠️ **VFG:** {vfg_valor} mL/min/1.73m² (🚨 CONTRAINDICACIÓN CRÍTICA)")
        elif vfg_valor < 60.0:
            st.warning(f"⚠️ **VFG:** {vfg_valor} mL/min/1.73m² (Riesgo Moderado)")
        else:
            st.success(f"✅ **VFG:** {vfg_valor} mL/min/1.73m² (Función Renal Normal)")

    with c2:
        st.markdown("#### 🚨 Triaje de Factores de Riesgo")
        st.write(f"**¿Alergias?:** {doc_completo.get('alergias')} ({doc_completo.get('alergias_detalles','')})")
        st.write(f"**¿Asma?:** {doc_completo.get('asma')}")
        st.write(f"**¿Diabetes?:** {doc_completo.get('diabetes')} | **Toma Metformina:** {doc_completo.get('metformina')}")
        st.write(f"**¿Insuficiencia Renal?:** {doc_completo.get('insuf_renal')}")
        st.write(f"**¿Embarazo?:** {doc_completo.get('embarazo')}")
        
        # Mostrar visualmente la firma que el paciente dibujó en la tablet
        st.markdown("#### ✍️ Firma Digital del Paciente")
        try:
            ruta_firma_storage = doc_completo.get("firma_img")
            blob_firma = bucket.blob(ruta_firma_storage)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                blob_firma.download_to_filename(tmp_img.name)
                imagen_firma = Image.open(tmp_img.name)
                st.image(imagen_firma, width=300, caption="Firma capturada desde el Tótem")
        except Exception as ef:
            st.caption(f"No se pudo cargar la vista previa de la firma: {ef}")

    # --- BLOQUE DE DOBLE FIRMA SEGURA ---
    st.divider()
    st.markdown("### ✍️ Validación del Profesional (Doble Firma)")

    # Formulario de validación técnica
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        # Los datos se cargan automáticamente según el PIN y están bloqueados (disabled=True)
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
        
        st.markdown("<br>", unsafe_html=True)
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
    st.markdown("<br>", unsafe_html=True)
    
    if st.button("🚀 APROBAR ENCUESTA Y GUARDAR VALIDACIÓN", use_container_width=True):
        if canvas_profesional.image_data is not None:
            with st.spinner("Estampando firma del profesional y asegurando registro..."):
                try:
                    # 1. Procesar la firma del profesional en formato imagen
                    img_data_tm = canvas_profesional.image_data
                    img_tm = Image.fromarray(img_data_tm.astype('uint8'), 'RGBA')
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_tm:
                        img_tm.save(tmp_tm.name)
                        ruta_firma_tm_local = tmp_tm.name

                    # 2. Subir la firma del TM a Firebase Storage para registro de auditoría
                    nombre_archivo_tm_storage = f"firmas_profesionales/TM_{profesional_registro}_{datetime.now(tz_chile).strftime('%Y%m%d_%H%M%S')}.png"
                    blob_tm = bucket.blob(nombre_archivo_tm_storage)
                    blob_tm.upload_from_filename(ruta_firma_tm_local, content_type='image/png')

                    # 3. Actualizar el documento en Firestore (Cambiando el estado a VALIDADO)
                    fecha_validacion_str = datetime.now(tz_chile).strftime("%d/%m/%Y %H:%M:%S")
                    
                    db.collection("encuestas_pendientes").document(paciente_seleccionado).update({
                        "profesional_nombre": profesional_nombre,
                        "profesional_registro": profesional_registro,
                        "fecha_validacion": fecha_validacion_str,
                        "estado_validacion": "VALIDADO",
                        "encuesta_validada": True,
                        "firma_profesional_img": nombre_archivo_tm_storage
                    })
                    
                    st.success(f"✅ Paciente {doc_completo.get('nombre')} visado con éxito por TM {profesional_nombre}.")
                    st.balloons()
                    
                    # Forzar recarga de la bandeja para limpiar la sala de espera
                    st.rerun()

                except Exception as ex_admin:
                    st.error(f"🚨 Error operativo al cerrar el protocolo: {ex_admin}")
        else:
            st.error("🚨 Firma incompleta. Debe dibujar su firma digital en el recuadro para visar el procedimiento.")
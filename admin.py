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
        # 1. Copiamos los secretos para no alterar el st.secrets original
        cred_dict = dict(st.secrets["firebase"])
        
        # 2. Extraemos el bucket de forma segura para que NO contamine la credencial de Google
        url_bucket = cred_dict.get("bucket_url", "")
        
        # 3. Removemos 'bucket_url' del diccionario de autenticación si es que viene dentro de él
        if "bucket_url" in cred_dict:
            del cred_dict["bucket_url"]

        # Limpieza estándar de saltos de línea si vienen como texto explícito
        if "private_key" in cred_dict and isinstance(cred_dict["private_key"], str):
            cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
            
        cred = credentials.Certificate(cred_dict)

        # Inicialización con el bucket correspondiente para almacenamiento de firmas
        firebase_admin.initialize_app(cred, {
            'storageBucket': url_bucket if url_bucket else st.secrets["firebase"].get("bucket_url", "")
        })
    except Exception as e:
        st.error(f"🚨 Error crítico al inicializar Firebase Admin: {e}")

# ESTAS DOS LÍNEAS DEBEN QUEDAR AHÍ, JUSTO AFUERA DEL BLOQUE TRY-EXCEPT:
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
docs_ref = db.collection("encuestas").where("estado_validacion", "==", "PENDIENTE").stream()

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
    
    # =====================================================================
    # 🛠️ SOLUCIÓN PASO 1: Unificar colección exacta a "encuestas"
    # =====================================================================
    doc_completo = db.collection("encuestas").document(paciente_seleccionado).get().to_dict()
    
    if doc_completo is None:
        doc_completo = {}
        
    st.divider()
    
    # Desplegar la ficha clínica del paciente en dos columnas organizadas
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("#### 👤 Datos Demográficos")
        # 🛠️ SOLUCIÓN PASO 3: .get() seguro con llaves controladas en minúscula
        st.write(f"**Nombre:** {doc_completo.get('nombre', 'No registrado')}")
        st.write(f"**RUT:** {doc_completo.get('rut', 'No registrado')}")
        st.write(f"**Edad:** {doc_completo.get('edad', 'N/A')} años")
        st.write(f"**Teléfono:** {doc_completo.get('telefono', 'No registrado')}")
        
        st.markdown("#### 🧪 Parámetros Clínicos Críticos")
        st.write(f"**Creatinina:** {doc_completo.get('creatinina', 'N/A')} mg/dL")
        st.write(f"**Peso:** {doc_completo.get('peso', 'N/A')} Kg")
        
        vfg_valor = doc_completo.get('vfg', 0.0)
        try:
            vfg_valor = float(vfg_valor)
        except:
            vfg_valor = 0.0
            
        if vfg_valor < 30.0:
            st.error(f"⚠️ **VFG:** {vfg_valor} mL/min/1.73m² (🚨 CONTRAINDICACIÓN CRÍTICA)")
        elif vfg_valor < 60.0:
            st.warning(f"⚠️ **VFG:** {vfg_valor} mL/min/1.73m² (Riesgo Moderado)")
        else:
            st.success(f"✅ **VFG:** {vfg_valor} mL/min/1.73m² (Función Renal Normal)")

    with c2:
        st.markdown("#### 🚨 Triaje de Factores de Riesgo")
        st.write(f"**¿Alergias?:** {doc_completo.get('alergias', 'No')} ({doc_completo.get('alergias_detalles','')})")
        st.write(f"**¿Asma?:** {doc_completo.get('asma', 'No')}")
        st.write(f"**¿Diabetes?:** {doc_completo.get('diabetes', 'No')} | **Toma Metformina:** {doc_completo.get('metformina', 'No')}")
        st.write(f"**¿Insuficiencia Renal?:** {doc_completo.get('insuf_renal', 'No')}")
        st.write(f"**¿Embarazo?:** {doc_completo.get('embarazo', 'No')}")
        
        # Mostrar visualmente la firma que el paciente dibujó en la tablet
        st.markdown("#### ✍️ Firma Digital del Paciente")
        try:
            ruta_firma_storage = doc_completo.get("firma_img")
            if ruta_firma_storage:
                blob_firma = bucket.blob(ruta_firma_storage)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                    blob_firma.download_to_filename(tmp_img.name)
                    imagen_firma = Image.open(tmp_img.name)
                    st.image(imagen_firma, width=300, caption="Firma capturada desde el Tótem")
            else:
                st.caption("No hay ruta de firma de paciente guardada en Firestore para este registro.")
        except Exception as ef:
            st.caption(f"No se pudo cargar la vista previa de la firma: {ef}")

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

                    # 2. Subir la firma del TM a Firebase Storage
                    nombre_archivo_tm_storage = f"firmas_profesionales/TM_{profesional_registro}_{datetime.now(tz_chile).strftime('%Y%m%d_%H%M%S')}.png"
                    blob_tm = bucket.blob(nombre_archivo_tm_storage)
                    blob_tm.upload_from_filename(ruta_firma_tm_local, content_type='image/png')

                    # 3. Actualizar el documento en Firestore
                    fecha_validacion_str = datetime.now(tz_chile).strftime("%d/%m/%Y %H:%M:%S")
                    
                    db.collection("encuestas").document(paciente_seleccionado).update({
                        "profesional_nombre": profesional_nombre,
                        "profesional_registro": profesional_registro,
                        "fecha_validacion": fecha_validacion_str,
                        "estado_validacion": "VALIDADO",
                        "encuesta_validada": True,
                        "firma_profesional_img": nombre_archivo_tm_storage
                    })
                    
                    try:
                        import os
                        os.unlink(ruta_firma_tm_local)
                    except:
                        pass

                    # =====================================================================
                    # 🛠️ SOLUCIÓN PASO 2: Se corrige la variable inexistente a doc_completo
                    # =====================================================================
                    st.success(f"✅ Paciente {doc_completo.get('nombre', 'Seleccionado')} visado con éxito por TM {profesional_nombre}.")
                    st.balloons()
                    
                    # Forzar recarga de la bandeja para limpiar la sala de espera
                    st.rerun()

                except Exception as ex_admin:
                    st.error(f"🚨 Error operativo al cerrar el protocolo: {ex_admin}")
        else:
            st.error("🚨 Firma incompleta. Debe dibujar su firma digital en el recuadro para visar el procedimiento.")
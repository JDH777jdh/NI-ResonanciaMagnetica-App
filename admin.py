import streamlit as st
import pandas as pd
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore, storage
import tempfile
from PIL import Image

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Panel de Validación Técnica - RM", layout="wide")

# --- ESTILOS INSTITUCIONALES (Color Vino/Bordeaux Hospitalario) ---
st.markdown(
    """
    <style>
    .main { background-color: #f8f9fa; }
    h1, h2, h3 { color: #800020; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    div[st-decorator="true"] { background-color: #800020; }
    .stButton>button {
        background-color: #800020; color: white; border-radius: 6px;
        border: none; padding: 0.5rem 1rem; font-weight: bold;
    }
    .stButton>button:hover { background-color: #a31d3d; color: white; }
    </style>
    """,
    unsafe_html=True
)

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

# --- SISTEMA DE AUTENTICACIÓN INTEGRADO ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.warning("🔒 Acceso Restringido. Personal Médico Autorizado.")
    col1, col2 = st.columns([1, 2])
    with col1:
        password = st.text_input("Ingrese Clave Institucional:", type="password")
        if st.button("Ingresar al Sistema"):
            # Puedes cambiar esta clave por la que gustes en tu producción
            if password == "rm_hospital_2026":
                st.session_state.authenticated = True
                st.success("Acceso concedido.")
                st.rerun()
            else:
                st.error("🔑 Credencial incorrecta. Intente nuevamente.")
    st.stop()

# =============================================================================
# --- LOGICA CORE: LEER ENCUESTAS PENDIENTES ---
# =============================================================================
st.markdown("### 📥 Bandeja de Entrada: Pacientes en Sala de Espera")

# Traer los documentos desde Firestore
docs_ref = db.collection("encuestas_pendientes").where("estado_validacion", "==", "PENDIENTE").stream()

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

    st.info("💡 *Este es el esqueleto base conectado. En el siguiente paso agregaremos la doble firma del Tecnólogo y el botón para mover el PDF final consolidado a Google Drive.*")
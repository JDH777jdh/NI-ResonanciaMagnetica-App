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
if "selector_refresh_key" not in st.session_state:
    st.session_state.selector_refresh_key = 0
if "id_seleccionado_anterior" not in st.session_state:
    st.session_state.id_seleccionado_anterior = None

@st.fragment(run_every=60)
def filtrar_y_sincronizar_pacientes():
    col_tit, col_btn = st.columns([3, 1])
    with col_tit:
        st.markdown("### 📥 Bandeja de Entrada: Pacientes en Sala de Espera")
    with col_btn:
        if st.button("🔄 Actualizar Lista", use_container_width=True, key="btn_manual_refresh"):
            st.rerun()
            
    hora_sincro = datetime.now(tz_chile).strftime('%H:%M:%S')
    st.caption(f"✨ Conectado a Firebase Firestore • Último auto-refresco: **{hora_sincro}**")

    try:
        docs_ref = db.collection("encuestas").where("estado_validacion", "==", "PENDIENTE").stream()
        listado_pacientes = []
        for doc in docs_ref:
            data = doc.to_dict()
            listado_pacientes.append({
                "ID_Documento": doc.id,
                "RUT": data.get("rut", "S/R"),
                "Nombre": data.get("nombre", "Sin Nombre")
            })
    except Exception as e:
        st.error(f"🚨 Error de conexión con el servidor de datos: {e}")
        listado_pacientes = []

    if not listado_pacientes:
        st.info("🟢 No hay encuestas pendientes por revisar. Sala de espera despejada.")
        st.session_state.paciente_seleccionado = None
        st.session_state.doc_completo = None
        return

    df_pacientes = pd.DataFrame(listado_pacientes)
    options_list = list(df_pacientes["ID_Documento"])

    key_dinamica = f"selector_pacientes_async_k_{st.session_state.selector_refresh_key}"

    def al_cambiar_paciente():
        st.session_state.id_seleccionado_anterior = st.session_state[key_dinamica]
        st.rerun()

    idx_actual = 0
    if st.session_state.id_seleccionado_anterior in options_list:
        idx_actual = options_list.index(st.session_state.id_seleccionado_anterior)
    else:
        st.session_state.id_seleccionado_anterior = options_list[0]

    paciente_seleccionado = st.selectbox(
        "🔎 Seleccione el paciente para revisar antecedentes y autorizar examen:",
        options=options_list,
        index=idx_actual,
        format_func=lambda x: f"🔹 RUT: {df_pacientes[df_pacientes['ID_Documento']==x]['RUT'].values[0]} | {df_pacientes[df_pacientes['ID_Documento']==x]['Nombre'].values[0]}",
        key=key_dinamica,
        on_change=al_cambiar_paciente
    )

    st.session_state.paciente_seleccionado = st.session_state.id_seleccionado_anterior
    doc_completo = db.collection("encuestas").document(st.session_state.id_seleccionado_anterior).get().to_dict()
    st.session_state.doc_completo = doc_completo if doc_completo else {}

filtrar_y_sincronizar_pacientes()


# =============================================================================
# --- DESPLIEGUE DEL FORMULARIO CLÍNICO ACTIVO ---
# =============================================================================
# El formulario completo se despliega de manera segura acoplándose al motor asíncrono

if st.session_state.get("doc_completo") is not None:
    paciente_seleccionado = st.session_state.paciente_seleccionado
    doc_completo = st.session_state.doc_completo
    
    st.divider()
    
    # Desplegar la ficha clínica del paciente en dos columnas organizadas
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("#### 👤 Datos Demográficos")
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
                    # 1. Procesar la firma del profesional (TM)
                    img_data_tm = canvas_profesional.image_data
                    img_tm_pil = Image.fromarray(img_data_tm.astype('uint8'), 'RGBA')
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_tm:
                        img_tm_pil.save(tmp_tm.name)
                        ruta_firma_tm_local = tmp_tm.name

                    # 2. Subir firma del TM a Storage
                    nombre_archivo_tm_storage = f"firmas_profesionales/TM_{profesional_registro}_{datetime.now(tz_chile).strftime('%Y%m%d_%H%M%S')}.png"
                    blob_tm = bucket.blob(nombre_archivo_tm_storage)
                    blob_tm.upload_from_filename(ruta_firma_tm_local, content_type='image/png')

                    # 3. Actualizar Firestore
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
                    # 📄 GENERACIÓN DEL PDF: DISEÑO EXACTO NORTE IMAGEN (CLON DE APP.PY)
                    # =====================================================================
                    st.info("🔄 Compilando formato institucional Norte Imagen...")
                    
                    import io
                    import os
                    from fpdf import FPDF
                    
                    datos_doc = doc_completo
                    paciente_nombre = datos_doc.get('nombre', 'Paciente No Identificado')
                    paciente_rut = datos_doc.get('rut', datos_doc.get('run', 'S/R'))
                    paciente_edad = str(datos_doc.get('edad', 'N/A'))
                    ip_cliente = datos_doc.get('ip_dispositivo', 'No detectada')
                    ruta_firma_paciente_storage = datos_doc.get('firma_img', '')

                    st.session_state.paciente_nombre_val = paciente_nombre

                    def safe_text(txt):
                        return str(txt).encode('latin-1', 'replace').decode('latin-1')

                    # 1. CLASE FPDF CON ESTILOS CORPORATIVOS
                    class PDF_Institucional(FPDF):
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
                            iniciales = "".join([p[0].upper() for p in paciente_nombre.split() if p])
                            id_registro = f"{paciente_rut}-{iniciales} (IP:{ip_cliente})"
                            texto_pie = f"Certificado Digital Norte Imagen - RM: {fecha_validacion_str} - ID: {id_registro} - VALIDADO TM."
                            self.cell(0, 10, safe_text(texto_pie), 0, 0, 'L')
                            self.cell(0, 10, safe_text(f"Página {self.page_no()}/{{nb}}"), 0, 0, 'R')

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

                    # 2. INICIALIZACIÓN DEL DOCUMENTO
                    pdf = PDF_Institucional()
                    pdf.alias_nb_pages()
                    pdf.add_page()
                    pdf.set_auto_page_break(auto=True, margin=12)

                    fecha_str = datetime.now(tz_chile).strftime("%d/%m/%Y")
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(0, 5, safe_text(f"Fecha de examen: {fecha_str}"), 0, 1, 'R') 
                    pdf.ln(2)

                    # --- SECCIÓN 1: IDENTIFICACION DEL PACIENTE ---
                    pdf.section_title("1", "IDENTIFICACION DEL PACIENTE")
                    pdf.set_text_color(0, 0, 0)
                    w_col = (pdf.w - 25) / 2

                    pdf.set_font('Arial', 'B', 10)
                    pdf.cell(32, 5, safe_text("Nombre Completo: "), 0, 0)
                    pdf.set_font('Arial', '', 10)
                    pdf.cell(0, 5, safe_text(paciente_nombre), 0, 1)

                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(18, 5, "RUT: ", 0, 0)
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(w_col - 18, 5, safe_text(paciente_rut), 0, 0)
                    
                    pdf.set_x(pdf.get_x() + 5)
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(12, 5, "Edad: ", 0, 0)
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(w_col - 12, 5, safe_text(f"{paciente_edad} años"), 0, 1)

                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(35, 5, "Fecha Nacimiento: ", 0, 0)
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(w_col - 35, 5, safe_text(datos_doc.get('fecha_nac', 'N/A')), 0, 0)
                    
                    pdf.set_x(pdf.get_x() + 5)
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(12, 5, "Email: ", 0, 0)
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(w_col - 12, 5, safe_text(datos_doc.get('email', 'N/A')), 0, 1)

                    pdf.set_font('Arial', 'B', 9)
                    pdf.write(5, "Procedimiento(s): ")
                    pdf.set_font('Arial', '', 9)
                    pdf.multi_cell(0, 5, safe_text(datos_doc.get('procedimiento', 'RM General')), 0, 'L')
                    pdf.ln(4)

                    # --- SECCIÓN 2: BIOSEGURIDAD ---
                    pdf.section_title("2", "BIOSEGURIDAD MAGNETICA")
                    pdf.set_font('Arial', '', 9)
                    pdf.data_field("Marcapasos cardiaco", datos_doc.get('bio_marcapaso', 'No'))
                    pdf.data_field("Implantes metálicos/quirúrgicos", datos_doc.get('bio_implantes', 'No'))
                    pdf.set_font('Arial', 'I', 8)
                    pdf.data_field("Detalle Bioseguridad", datos_doc.get('bio_detalle', 'Sin observaciones'))
                    pdf.ln(2)

                    # --- SECCIÓN 3: CLINICOS (Grilla a 4 columnas) ---
                    pdf.section_title("3", "ANTECEDENTES CLINICOS")
                    pdf.set_text_color(0, 0, 0)
                    
                    clinicos = [
                        ("Ayuno 2hrs+", datos_doc.get('clin_ayuno', 'No')), ("Asma", datos_doc.get('asma', 'No')), ("Alergias", datos_doc.get('alergias', 'No')),
                        ("Hipertensión", datos_doc.get('clin_hiperten', 'No')), ("Hipotiroidismo", datos_doc.get('clin_hipertiroid', 'No')), ("Diabetes", datos_doc.get('diabetes', 'No')),
                        ("Metformina 48h", datos_doc.get('metformina', 'No')), ("Insuf. Renal", datos_doc.get('insuf_renal', 'No')), ("Diálisis", datos_doc.get('clin_dialisis', 'No')),
                        ("Embarazo", datos_doc.get('embarazo', 'No')), ("Lactancia", datos_doc.get('clin_lactancia', 'No')), ("Claustrofobia", datos_doc.get('clin_claustro', 'No'))
                    ]

                    col_width = pdf.w / 4.2 
                    for i in range(0, len(clinicos), 4):
                        linea = clinicos[i:i+4]
                        for item, valor in linea:
                            pdf.set_font('Arial', '', 8)
                            pdf.cell(col_width, 4.5, safe_text(f"{item}: {valor}"), 0, 0)
                        pdf.ln(4.5) 
                    pdf.ln(2)

                    # --- SECCIÓN 4 Y 5: QUIRÚRGICOS Y EXÁMENES ---
                    pdf.section_title("4", "ANTECEDENTES QUIRURGICOS Y TERAPEUTICOS")
                    pdf.set_font('Arial', '', 9)
                    pdf.data_field("Cirugías", datos_doc.get('quir_cirugia_check', 'No'))
                    pdf.set_font('Arial', '', 8)
                    pdf.data_field("Detalle", datos_doc.get('quir_cirugia_detalle', 'N/A'))
                    pdf.data_field("Tratamientos Adicionales", datos_doc.get('quir_otro_trat', 'Ninguno'))
                    pdf.ln(2)

                    pdf.section_title("5", "EXAMENES ANTERIORES")
                    pdf.set_font('Arial', '', 9)
                    pdf.data_field("Exámenes previos", datos_doc.get('ex_otros', 'Ninguno documentado'))
                    pdf.ln(2)

                    # --- SECCIÓN 6: FUNCION RENAL ---
                    pdf.section_title("6", "EVALUACION DE LA FUNCION RENAL")
                    pdf.set_font('Arial', '', 9)
                    
                    crea = datos_doc.get('creatinina', 0.0)
                    peso = datos_doc.get('peso', 0.0)
                    vfg_real = datos_doc.get('vfg', 0.0)

                    pdf.data_field("Creatinina", f"{crea} mg/dL" if str(crea) != 'N/A' else "__________ mg/dL")
                    pdf.data_field("Peso", f"{peso} kg" if str(peso) != 'N/A' else "__________ kg")

                    try:
                        vfg_real = float(vfg_real)
                    except:
                        vfg_real = 0.0

                    if vfg_real > 0:
                        if vfg_real <= 30:
                            pdf.set_text_color(255, 0, 0) 
                            msg_riesgo = "ALTO RIESGO"
                        elif 31 <= vfg_real <= 59:
                            pdf.set_text_color(184, 134, 11) 
                            msg_riesgo = "RIESGO INTERMEDIO"
                        else:
                            pdf.set_text_color(34, 139, 34) 
                            msg_riesgo = "SIN RIESGOS"

                        pdf.set_font('Arial', 'B', 9)
                        pdf.write(5, safe_text(f"V.F.G: {vfg_real:.2f} ml/min"))
                        pdf.set_font('Arial', 'B', 8)
                        pdf.write(5, safe_text(f"  ({msg_riesgo})"))
                        pdf.set_text_color(0, 0, 0)
                        pdf.ln(5)
                    else:
                        pdf.data_field("RESULTADO VFG", "__________ ml/min (Cálculo manual)")
                    pdf.ln(2)

                    # --- SECCIÓN 7: CONTRASTE (Grilla para rellenar) ---
                    pdf.section_title("7", "REGISTRO DE ADMINISTRACION DE CONTRASTE")
                    pdf.set_text_color(0, 0, 0)
                    
                    w_col_ct = (pdf.w - 30) / 2
                    pdf.set_font('Arial', 'B', 9) 
                    pdf.set_fill_color(245, 245, 245)
                    
                    pdf.cell(w_col_ct, 6, safe_text(" Acceso venoso:"), 0, 0, 'L', fill=True)
                    pdf.cell(10, 6, "", 0, 0) 
                    pdf.cell(w_col_ct, 6, safe_text(" Sitio de punción:"), 0, 1, 'L', fill=True)
                    
                    pdf.set_font('Arial', '', 9)
                    pdf.ln(1)
                    pdf.cell(w_col_ct, 8, safe_text("[     ] Branula: ____ G  [     ] Mariposa: ____ G"), 0, 0, 'L') 
                    pdf.cell(10, 8, "", 0, 0) 
                    pdf.cell(w_col_ct, 8, safe_text("________________________________"), 0, 1, 'L')
                    pdf.ln(1)
                    
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(w_col_ct, 6, safe_text(" Medio de contraste (Intravenoso):"), 0, 0, 'L', fill=True)
                    pdf.cell(10, 6, "", 0, 0)
                    pdf.cell(w_col_ct, 6, safe_text(" Cantidad administrada:"), 0, 1, 'L', fill=True)
                    
                    pdf.ln(1)
                    pdf.set_font('Arial', '', 9)
                    pos_y_bloque = pdf.get_y()
                    pdf.cell(w_col_ct, 4, safe_text("[     ] Acido gadoterico (Clariscan)"), 0, 1)
                    pdf.cell(w_col_ct, 4, safe_text("[     ] Gadopiclenol (Elucirem)"), 0, 1)
                    pdf.cell(w_col_ct, 4, safe_text("[     ] Acido gadoxetico (Primovist)"), 0, 1)
                    
                    pdf.set_xy(pdf.get_x() + w_col_ct + 10, pos_y_bloque)
                    pdf.cell(w_col_ct, 7, safe_text("___________ ml."), 0, 1, 'L')
                    pdf.ln(4)

                    # --- PÁGINA 2: LEGAL Y DOBLE FIRMA ---
                    pdf.add_page()
                    pdf.set_font('Arial', 'B', 10)
                    pdf.multi_cell(0, 7, safe_text(f"Procedimiento: {datos_doc.get('procedimiento', 'RM General')}"), 0, 'L')
                    pdf.ln(3)

                    pdf.set_font('Arial', 'B', 11)
                    pdf.cell(0, 10, safe_text("LEA ATENTA Y CUIDADOSAMENTE LO SIGUIENTE:"), 0, 1, 'L')
                    pdf.ln(2)

                    sections = {
                        "OBJETIVOS": "La Resonancia Magnética (RM) es una segura técnica de Diagnóstico, que permite la adquisición de imágenes de gran sensibilidad en todos los planos del espacio de las estructuras del cuerpo. Tiene como objetivo obtener Información, datos funcionales y morfológicos para detectar precozmente una enfermedad.\n\nPara este examen eventualmente se puede requerir la utilización de un medio de contraste paramagnético de administración endovenosa llamado gadolinio, que permite realzar ciertos tejidos del cuerpo para un mejor diagnóstico.",
                        "CARACTERISTICAS": "La Resonancia utiliza fuertes campos magnéticos y ondas de radiofrecuencia, por lo que es muy importante dejar fuera de la sala absolutamente todo lo que lleve consigo de tipo metálico y/o electrónico. Si lleva material de este tipo en su cuerpo, implantes, así como dispositivos electrónicos de carácter médico, avísenos, ya que puede contraindicar de manera absoluta la realización de este examen.\n\nUsted será posicionado en la camilla del equipo, según el estudio a realizar y se colocarán cerca de la zona a estudiar unos dispositivos. Notará ruido derivado del funcionamiento de la RM, todo esto es normal y se le vigilará constantemente desde la sala de control.\n\nEs muy importante que permanezca quieto durante el estudio y siga las instrucciones del Tecnólogo Médico.",
                        "POTENCIALES RIESGOS": "Existe una muy baja posibilidad de que se presente una reacción adversa al medio de contraste (0.07-2.4%) la mayoría de carácter leve fundamentalmente nauseas o cefaleas al momento de la inyección.\n\nPacientes con deterioro importante de la función renal, poseen riesgo de desarrollo de fibrosis nefrogénica sistémica."
                    }

                    for tit, cont in sections.items():
                        pdf.set_font('Arial', 'B', 10)
                        pdf.set_text_color(128, 0, 32)
                        pdf.cell(0, 6, safe_text(tit), 0, 1, 'L')
                        pdf.set_font('Arial', '', 9)
                        pdf.set_text_color(0, 0, 0)
                        pdf.multi_cell(0, 5, safe_text(cont))
                        pdf.ln(3)

                    pdf.set_font('Arial', '', 9)
                    consentimiento_texto = "He sido informado de mi derecho de anular o revocar posteriormente este documento, dejándolo constatado por escrito y firmado por mi o mi representante.\n\nAutorizo la realización del procedimiento anteriormente especificado y las acciones que sean necesarias en caso de surgir complicaciones durante el procedimiento. Además, doy consentimiento para que se administren medicamentos y/o infusiones que se requieran para la realización de este."
                    pdf.multi_cell(0, 5, safe_text(consentimiento_texto))
                    
                    # --- ESTAMPADO DE FIRMAS INTEGRADAS ---
                    pdf.ln(20)
                    pos_firmas_y = pdf.get_y()
                    ruta_p_local = None

                    # 1. Recuperar firma del Paciente desde Firebase Storage
                    if ruta_firma_paciente_storage:
                        try:
                            blob_paciente = bucket.blob(ruta_firma_paciente_storage)
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_p_img:
                                blob_paciente.download_to_filename(tmp_p_img.name)
                                ruta_p_local = tmp_p_img.name
                            pdf.image(ruta_p_local, x=20, y=pos_firmas_y - 15, w=45)
                        except Exception:
                            pdf.set_xy(20, pos_firmas_y - 5)
                            pdf.set_font('Arial', 'I', 8)
                            pdf.cell(45, 5, safe_text("[Firma respaldada en BD]"), 0, 0, 'C')

                    # 2. Estampar firma del TM (Tecnólogo)
                    if os.path.exists(ruta_firma_tm_local):
                        pdf.image(ruta_firma_tm_local, x=130, y=pos_firmas_y - 15, w=45)

                    # Líneas horizontales debajo de las firmas (Paciente a la izq / TM a la der)
                    pdf.set_draw_color(0, 0, 0)
                    pdf.line(15, pos_firmas_y, 80, pos_firmas_y)
                    pdf.line(125, pos_firmas_y, 190, pos_firmas_y)

                    # --- FILA 1: Títulos de las Columnas ---
                    pdf.set_font('Arial', 'B', 8)
                    pdf.set_xy(15, pos_firmas_y + 2)
                    pdf.cell(65, 4, safe_text("FIRMA PACIENTE O REPRESENTANTE LEGAL"), 0, 0, 'C')
                    
                    pdf.set_xy(125, pos_firmas_y + 2)
                    pdf.cell(65, 4, safe_text("FIRMA PROFESIONAL RESPONSABLE"), 0, 1, 'C')

                    # --- FILA 2: Datos de Identificación / Nombre ---
                    # Guardamos la posición Y actual para que ambas columnas bajen simétricamente
                    siguiente_y = pdf.get_y()
                    
                    # Renglón Paciente (Izquierda)
                    pdf.set_font('Arial', '', 8)
                    pdf.set_xy(15, siguiente_y)
                    pdf.cell(65, 4, safe_text(f"RUN: {paciente_rut}"), 0, 0, 'C')
                    
                    # Renglón TM (Derecha)
                    pdf.set_xy(125, siguiente_y)
                    pdf.cell(65, 4, safe_text(profesional_nombre), 0, 1, 'C')

                    # --- FILA 3: Cargo (Línea 1) ---
                    pdf.set_x(125)
                    pdf.cell(65, 4, safe_text("Tecnólogo Médico"), 0, 1, 'C')

                    # --- FILA 4: Cargo (Línea 2) ---
                    pdf.set_x(125)
                    pdf.cell(65, 4, safe_text("Esp. Resonancia Magnética"), 0, 1, 'C')

                    # --- FILA 5: Registro SIS ---
                    pdf.set_x(125)
                    pdf.cell(65, 4, safe_text(f"(Reg: {profesional_registro})"), 0, 1, 'C')

                    # Almacenar en la sesión de Streamlit para el botón de descarga
                    st.session_state.pdf_bytes_data = pdf.output(dest='S').encode('latin-1', 'replace')
                    st.session_state.pdf_filename = f"REG-VALIDADO_{paciente_nombre.replace(' ', '-').upper()}_{paciente_rut}_{['', 'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE'][datetime.now(tz_chile).month]}_{datetime.now(tz_chile).strftime('%Y')}.pdf"

                    st.session_state.pdf_ready = True
                    
                    st.success(f"🎉 ¡Circuito Clínico Cerrado! Paciente {paciente_nombre} validado correctamente.")
                    st.balloons()
                        
                except Exception as ex_admin:
                    st.error(f"🚨 Error operativo al cerrar protocolo o compilar PDF institucional: {ex_admin}")
                finally:
                    # Limpieza de imágenes temporales para mantener la memoria sana
                    try:
                        import os
                        if 'ruta_firma_tm_local' in locals() and os.path.exists(ruta_firma_tm_local):
                            os.unlink(ruta_firma_tm_local)
                        if 'ruta_p_local' in locals() and ruta_p_local and os.path.exists(ruta_p_local):
                            os.unlink(ruta_p_local)
                    except:
                        pass
        else:
            st.error("🚨 Firma incompleta. Debe dibujar su firma digital en el recuadro para visar el procedimiento.")

    # =====================================================================
    # 🔥 RENDEREADO SEGURO DE DESCARGA (EXTERNO AL IF PRINCIPAL)
    # =====================================================================
    if st.session_state.pdf_ready and st.session_state.pdf_bytes_data is not None:
        st.markdown("---")
        st.markdown("### 📥 Descarga de Documento Oficial")
        
        # Recuperamos el nombre directamente del documento en sesión para que sea 100% inmune a NameError
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
            # Forzamos la destrucción de la caché del selector de pacientes
            st.session_state.selector_refresh_key += 1  
            st.session_state.id_seleccionado_anterior = None
            st.session_state.paciente_seleccionado = None
            st.session_state.doc_completo = None
            
            # Reset de PDFs
            st.session_state.pdf_ready = False
            st.session_state.pdf_bytes_data = None
            st.rerun()
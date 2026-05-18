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
                    # 3. ACTUALIZAR FIRESTORE
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
                    # 📄 4. GENERACIÓN DEL PDF: DISEÑO EXACTO NORTE IMAGEN (VERSIÓN OPTIMIZADA)
                    # =====================================================================
                    st.info("🔄 Compilando formato institucional Norte Imagen...")

                    import io
                    import os
                    from fpdf import FPDF

                    datos_doc = doc_completo
                    
                    # --- EXTRACCIÓN SEGURA DE VARIABLES ---
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

                    try:
                        edad_int = int(datos_doc.get('edad', 0))
                        paciente_edad = f"{edad_int} años"
                    except:
                        edad_int = 0
                        paciente_edad = str(datos_doc.get('edad', 'N/A'))

                    req_contraste = str(datos_doc.get('req_contraste', datos_doc.get('contraste', 'No')))
                    is_contraste = req_contraste.upper() in ['SI', 'SÍ', 'TRUE', '1', 'YES']
                    
                    rep_nombre = datos_doc.get('nombre_tutor', datos_doc.get('representante_nombre', ''))
                    rep_rut = datos_doc.get('rut_tutor', datos_doc.get('representante_rut', ''))

                    ip_cliente = datos_doc.get('ip_dispositivo', datos_doc.get('ip_paciente', 'No detectada'))
                    ruta_firma_paciente_storage = datos_doc.get('firma_img', '')

                    # --- DESCARGA DE FIRMA DEL PACIENTE PARA INCRUSTAR EN PDF ---
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
                            id_registro = f"{self.p_rut}-{iniciales} (IP:{self.p_ip})"
                            texto_pie = f"Certificado Digital Norte Imagen - RM: {self.f_val} - ID Registro: {id_registro} - VALIDADO TM."
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

                    pdf = PDF_Institucional(paciente_nombre, paciente_rut, ip_cliente, fecha_validacion_str)
                    pdf.alias_nb_pages()
                    pdf.add_page()
                    pdf.set_auto_page_break(auto=True, margin=12)

                    # --- ENCABEZADO FECHA ---
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(0, 5, f"Fecha de examen: {fecha_validacion_str.split()[0]}", 0, 1, 'R') 
                    pdf.ln(2)

                   # --- SECCIÓN 1: IDENTIFICACION DEL PACIENTE ---
                    pdf.section_title("1", "IDENTIFICACION DEL PACIENTE")
                    pdf.set_text_color(0, 0, 0)
                    
                    # Cálculo exacto de columnas simétricas independientes
                    margen_izquierdo = 10
                    ancho_disponible = pdf.w - 20 # 190mm típicamente en A4
                    w_col = (ancho_disponible - 10) / 2 # Mitad exacta dejando un espacio central de 10mm
                    x_col2 = margen_izquierdo + w_col + 10 # Posición X fija para la columna 2

                    # Fila 1: Nombre del Paciente
                    pdf.set_font('Arial', 'B', 10)
                    pdf.cell(32, 5, "Nombre Completo: ", 0, 0)
                    pdf.set_font('Arial', '', 10)
                    pdf.cell(0, 5, safe_text(paciente_nombre), 0, 1)

                    # Guardamos la posición Y para la grilla en paralelo
                    y_fila2 = pdf.get_y()

                    # Fila 2 - Columna 1: RUT
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(18, 5, "RUT: ", 0, 0)
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(w_col - 18, 5, safe_text(paciente_rut), 0, 0)
                    
                    # Fila 2 - Columna 2: Edad (Forzada a su coordenada X fija)
                    pdf.set_xy(x_col2, y_fila2)
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(12, 5, "Edad: ", 0, 0)
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(w_col - 12, 5, safe_text(paciente_edad), 0, 1) # Salto de línea limpio

                    # Guardamos la nueva posición Y para la siguiente fila en paralelo
                    y_fila3 = pdf.get_y()

                    # Fila 3 - Columna 1: Fecha Nacimiento
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(35, 5, "Fecha Nacimiento: ", 0, 0)
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(w_col - 35, 5, safe_text(fecha_nacimiento_val), 0, 0)
                    
                    # Fila 3 - Columna 2: Email (Forzado a su coordenada X fija)
                    pdf.set_xy(x_col2, y_fila3)
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(12, 5, "Email: ", 0, 0)
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(w_col - 12, 5, safe_text(email_val), 0, 1) # Salto de línea limpio

                    # Fila 4: Medio de Contraste
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(35, 5, "Medio de contraste: ", 0, 0)
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(0, 5, 'SI' if is_contraste else 'NO', 0, 1)

                    # Fila 5: Procedimientos (Usa multi_cell de forma segura al final de la estructura)
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(35, 5, "Procedimiento(s): ", 0, 1) # Cambiado a cell para dar un salto limpio
                    pdf.set_font('Arial', '', 9)
                    pdf.multi_cell(0, 5, safe_text(procedimiento_val), 0, 'L')

                    # Fila 6: Datos del Tutor / Representante (Si aplica)
                    if rep_nombre or edad_int < 18:
                        pdf.ln(1)
                        y_tutor = pdf.get_y()
                        
                        # Columna 1: Nombre Representante
                        pdf.set_font('Arial', 'B', 9)
                        pdf.cell(28, 5, "Representante: ", 0, 0)
                        pdf.set_font('Arial', '', 9)
                        pdf.cell(w_col - 28, 5, safe_text(rep_nombre if rep_nombre else 'N/A'), 0, 0)
                        
                        # Columna 2: RUT Representante
                        pdf.set_xy(x_col2, y_tutor)
                        pdf.set_font('Arial', 'B', 9)
                        pdf.cell(35, 5, "RUT Representante: ", 0, 0)
                        pdf.set_font('Arial', '', 9)
                        pdf.cell(w_col - 35, 5, safe_text(rep_rut if rep_rut else 'N/A'), 0, 1)

                    pdf.ln(4)

                    # --- SECCIÓN 2: BIOSEGURIDAD ---
                    pdf.section_title("2", "BIOSEGURIDAD MAGNETICA")
                    
                    # Usamos una altura de celda fija (h=5) para mantener la simetría horizontal
                    pdf.set_font('Arial', '', 9)
                    pdf.data_field("Marcapasos cardiaco", parse_bool_clinico(datos_doc.get('bio_marcapaso', 'No')), h=5)
                    
                    # Al usar la función optimizada con multi_cell, esta línea larga se ajustará de forma segura si es necesario
                    pdf.data_field("Implantes metálicos, quirúrgicos, prótesis o dispositivo electrónicos", parse_bool_clinico(datos_doc.get('bio_implantes', datos_doc.get('bio_metal', 'No'))), h=5)
                    
                    # El detalle lo manejamos en cursiva (I) y tamaño 8 por si el paciente escribió un texto muy extenso
                    pdf.set_font('Arial', 'I', 8)
                    det_bio = datos_doc.get('bio_detalle', '')
                    pdf.data_field("Detalle Bioseguridad", det_bio if det_bio else "Sin observaciones", h=4.5)
                    
                    pdf.ln(2)

                    # --- SECCIÓN 3: ANTECEDENTES CLINICOS ---
                    pdf.section_title("3", "ANTECEDENTES CLINICOS")
                    pdf.set_text_color(0, 0, 0)
                    
                    clinicos = [
                        ("Ayuno 2hrs+", parse_bool_clinico(datos_doc.get('clin_ayuno', 'No'))), 
                        ("Asma", parse_bool_clinico(datos_doc.get('asma', datos_doc.get('clin_asma', 'No')))), 
                        ("Alergias", parse_bool_clinico(datos_doc.get('alergias', datos_doc.get('clin_alergico', 'No')))),
                        ("Hipertensión", parse_bool_clinico(datos_doc.get('clin_hiperten', 'No'))), 
                        ("Hipotiroidismo", parse_bool_clinico(datos_doc.get('clin_hipertiroid', 'No'))), 
                        ("Diabetes", parse_bool_clinico(datos_doc.get('diabetes', datos_doc.get('clin_diabetes', 'No')))),
                        ("Metformina 48h", parse_bool_clinico(datos_doc.get('metformina', datos_doc.get('clin_metformina', 'No')))), 
                        ("Insuf. Renal", parse_bool_clinico(datos_doc.get('insuf_renal', datos_doc.get('clin_renal', 'No')))), 
                        ("Diálisis", parse_bool_clinico(datos_doc.get('clin_dialisis', 'No'))),
                        ("Embarazo", parse_bool_clinico(datos_doc.get('embarazo', datos_doc.get('clin_embarazo', 'No')))), 
                        ("Lactancia", parse_bool_clinico(datos_doc.get('clin_lactancia', 'No'))), 
                        ("Claustrofobia", parse_bool_clinico(datos_doc.get('clin_claustro', 'No')))
                    ]

                    # Cálculo matemático estricto de las 4 columnas
                    margen_izquierdo = 10
                    ancho_disponible = pdf.w - 20 # Generalmente 190mm en A4
                    w_col_fija = ancho_disponible / 4 # 47.5mm exactos para cada columna

                    # Procesamos en grupos de 4 elementos por fila
                    for i in range(0, len(clinicos), 4):
                        linea = clinicos[i:i+4]
                        y_fila_actual = pdf.get_y() # Fijamos la altura horizontal de la fila

                        for idx_col, (item, valor) in enumerate(linea):
                            # Si es masculino, aplicamos la regla biológica
                            if genero == "Masculino" and item in ["Embarazo", "Lactancia"]:
                                valor = "N/A"
                            
                            # Calculamos la coordenada X exacta de la columna (0, 1, 2 o 3)
                            x_exacto = margen_izquierdo + (idx_col * w_col_fija)
                            pdf.set_xy(x_exacto, y_fila_actual)
                            
                            # Imprimimos de manera segura
                            pdf.set_font('Arial', '', 8)
                            texto_col = f"{item}: {valor}"
                            pdf.cell(w_col_fija - 2, 4.5, safe_text(texto_col), 0, 0)
                        
                        # Al terminar las 4 columnas de la fila, ejecutamos un salto de línea controlado
                        pdf.set_x(margen_izquierdo)
                        pdf.ln(4.5) 
                        
                    pdf.ln(2)

                    # --- SECCIÓN 4: ANTECEDENTES QUIRURGICOS Y TERAPEUTICOS ---
                    pdf.section_title("4", "ANTECEDENTES QUIRURGICOS Y TERAPEUTICOS")
                    
                    # Campo simple de Sí/No para Cirugías
                    pdf.set_font('Arial', '', 9)
                    pdf.data_field("Cirugías", parse_bool_clinico(datos_doc.get('quir_cirugia_check', 'No')), h=5)
                    
                    # Detalle de cirugías en tamaño 8 (Usa multi_cell internamente de forma segura si el texto es largo)
                    pdf.set_font('Arial', 'I', 8)
                    det_cir = datos_doc.get('quir_cirugia_detalle', '')
                    pdf.data_field("Detalle cirugías", det_cir if det_cir else "N/A", h=4.5)
                    
                    # Procesamiento y renderizado de Tratamientos (RT, QT, BT, IT)
                    trats_dict = {"RT": datos_doc.get('rt', False), "QT": datos_doc.get('qt', False), "BT": datos_doc.get('bt', False), "IT": datos_doc.get('it', False)}
                    trats = [k for k, v in trats_dict.items() if v in [True, "Sí", "SI", "si", 1, "true", "Si"]]
                    
                    pdf.set_font('Arial', '', 9)
                    pdf.data_field("Tratamientos", ", ".join(trats) if trats else "Ninguno", h=5)
                    
                    # Detalle de otros tratamientos en tamaño 8 con tipografía cursiva (I) de protección
                    pdf.set_font('Arial', 'I', 8)
                    otr_trat = datos_doc.get('quir_otro_trat', '')
                    pdf.data_field("Detalle de otros tratamientos", otr_trat if otr_trat else "N/A", h=4.5)
                    
                    pdf.ln(2)

                    # --- SECCIÓN 5: EXAMENES ANTERIORES ---
                    pdf.section_title("5", "EXAMENES ANTERIORES")
                    
                    # Procesamiento de checkboxes de exámenes (Rx, MG, Eco, TC, RM)
                    ex_dict = {"Rx": datos_doc.get('ex_rx', False), "MG": datos_doc.get('ex_mg', False), "Eco": datos_doc.get('ex_eco', False), "TC": datos_doc.get('ex_tc', False), "RM": datos_doc.get('ex_rm', False)}
                    ex_list = [k for k, v in ex_dict.items() if v in [True, "Sí", "SI", "si", 1, "true", "Si"]]
                    
                    # Imprime de forma segura la lista consolidada
                    pdf.set_font('Arial', '', 9)
                    pdf.data_field("Exámenes", ", ".join(ex_list) if ex_list else "Ninguno", h=5)
                    
                    # Detalle de otros exámenes en tamaño 8 y estilo cursiva (I) inmune a textos largos
                    pdf.set_font('Arial', 'I', 8)
                    ex_otr = datos_doc.get('ex_otros', '')
                    pdf.data_field("Otros exámenes anteriores", ex_otr if ex_otr else "N/A", h=4.5)
                    
                    pdf.ln(2)

                    # --- SECCIÓN 6: FUNCION RENAL ---
                    pdf.section_title("6", "EVALUACIÓN DE LA FUNCION RENAL")
                    pdf.set_font('Arial', '', 9)
                    
                    if is_contraste:
                        crea = datos_doc.get('creatinina')
                        try: crea_float = float(crea)
                        except: crea_float = 0.0
                        creatinina_val = f"{crea_float} mg/dL" if crea_float > 0 else "__________ mg/dL"
                        pdf.data_field("Creatinina", creatinina_val, h=5)

                        peso_real = datos_doc.get('peso')
                        try: peso_float = float(peso_real)
                        except: peso_float = 0.0
                        peso_texto = f"{peso_float} kg" if peso_float > 0 else "__________ kg"
                        pdf.data_field("Peso", peso_texto, h=5)

                        vfg_real = datos_doc.get('vfg')
                        try: vfg_float = float(vfg_real)
                        except: vfg_float = 0.0
                        
                        if vfg_float > 0 and peso_texto != "__________ kg":
                            if vfg_float <= 30:
                                pdf.set_text_color(255, 0, 0)
                                msg_riesgo = "ALTO RIESGO para la administración de medio de contraste"
                            elif 31 <= vfg_float <= 59:
                                pdf.set_text_color(184, 134, 11)
                                msg_riesgo = "RIESGO INTERMEDIO para la administración de medio de contraste"
                            else:
                                pdf.set_text_color(34, 139, 34)
                                msg_riesgo = "SIN RIESGOS para la administración de medio de contraste"

                            # Renderizado seguro: Consolidamos el valor y la alerta en una sola llamada limpia
                            # El texto de riesgo cambia de color de manera segura y controlada
                            valor_vfg_completo = f"{vfg_float:.2f} ml/min  ({msg_riesgo})"
                            pdf.data_field("V.F.G", valor_vfg_completo, h=5)
                            pdf.set_text_color(0, 0, 0) # Restablecemos inmediatamente a negro
                        else:
                            pdf.data_field("RESULTADO VFG", "__________ ml/min (Cálculo manual)", h=5)
                    else:
                        # Si el estudio no requiere contraste, dejamos los campos limpios y estandarizados
                        pdf.data_field("Creatinina", "__________ mg/dL", h=5)
                        pdf.data_field("Peso", "__________ kg", h=5)
                        pdf.data_field("RESULTADO VFG", "__________ ml/min (Cálculo manual)", h=5)
                        
                    pdf.ln(2)

                    # --- SECCIÓN 7: REGISTRO DE ADMINISTRACION DE CONTRASTE ---
                    pdf.section_title("7", "REGISTRO DE ADMINISTRACION DE CONTRASTE")
                    pdf.set_text_color(0, 0, 0)
                    
                    # Definición matemática estricta de las dos columnas
                    margen_izquierdo = 10
                    ancho_disponible = pdf.w - 20 # 190mm típicamente en A4
                    w_col_7 = (ancho_disponible - 10) / 2 # Mitad exacta con espacio central de 10mm
                    x_col7_derecha = margen_izquierdo + w_col_7 + 10 # Coordenada X fija para columna 2

                    # --- FILA 1: Encabezados (Acceso venoso / Sitio punción) ---
                    y_cabecera1 = pdf.get_y()
                    pdf.set_font('Arial', 'B', 9) 
                    pdf.set_fill_color(245, 245, 245)
                    
                    pdf.cell(w_col_7, 6, safe_text(" Acceso venoso:"), 0, 0, 'L', fill=True)
                    
                    pdf.set_xy(x_col7_derecha, y_cabecera1)
                    pdf.cell(w_col_7, 6, safe_text(" Sitio de punción:"), 0, 1, 'L', fill=True)
                    pdf.ln(1)
                    
                    # --- FILA 2: Inputs manuales (Branula/Mariposa / Línea de llenado) ---
                    y_inputs1 = pdf.get_y()
                    pdf.set_font('Arial', '', 9)
                    
                    opciones_acceso = "[     ] Branula: ____ G  [     ] Mariposa: ____ G"
                    pdf.cell(w_col_7, 8, safe_text(opciones_acceso), 0, 0, 'L') 
                    
                    pdf.set_xy(x_col7_derecha, y_inputs1)
                    pdf.cell(w_col_7, 8, safe_text("________________________________"), 0, 1, 'L')
                    pdf.ln(1)
                    
                    # --- FILA 3: Encabezados (Medio de Contraste / Cantidad) ---
                    y_cabecera2 = pdf.get_y()
                    pdf.set_font('Arial', 'B', 9)
                    
                    pdf.cell(w_col_7, 6, safe_text(" Medio de contraste (Intravenoso):"), 0, 0, 'L', fill=True)
                    
                    pdf.set_xy(x_col7_derecha, y_cabecera2)
                    pdf.cell(w_col_7, 6, safe_text(" Cantidad administrada:"), 0, 1, 'L', fill=True)
                    pdf.ln(1)
                    
                    # --- FILA 4: Opciones de fármacos vs Volumen ml (Grilla paralela rígida) ---
                    pdf.set_font('Arial', '', 9)
                    pos_y_bloque = pdf.get_y()
                    
                    # Columna Izquierda: Listado de medios de contraste institucionales
                    pdf.cell(w_col_7, 4.5, safe_text("[     ] Ácido gadotérico (Clariscan)"), 0, 1, 'L')
                    pdf.cell(w_col_7, 4.5, safe_text("[     ] Gadopiclenol (Elucirem)"), 0, 1, 'L')
                    pdf.cell(w_col_7, 4.5, safe_text("[     ] Ácido gadoxético (Primovist)"), 0, 1, 'L')
                    
                    # Columna Derecha: Posicionamiento absoluto forzado e inmune a las líneas de la izquierda
                    pdf.set_xy(x_col7_derecha, pos_y_bloque + 4.5) # Centrado verticalmente respecto a las 3 opciones
                    pdf.cell(w_col_7, 5, safe_text("___________ ml."), 0, 1, 'L')
                    
                    # Devolvemos el cursor al inicio del margen izquierdo y avanzamos de forma limpia
                    pdf.set_x(margen_izquierdo)
                    pdf.ln(4)

                   # =====================================================================
                    # --- PÁGINA 2: CONSENTIMIENTO Y FIRMAS (IDÉNTICO CON VISACIÓN TM) ---
                    # =====================================================================
                    pdf.add_page()

                    pdf.set_font('Arial', 'B', 10)
                    pdf.set_text_color(0, 0, 0)
                    
                    texto_procedimiento_p2 = f"Procedimiento: {procedimiento_val}"
                    if is_contraste:
                        texto_procedimiento_p2 += " con uso de medio de contraste."
                        pdf.multi_cell(0, 6, safe_text(texto_procedimiento_p2), 0, 'L')
                    else:
                        pdf.multi_cell(0, 6, safe_text(texto_procedimiento_p2), 0, 'L')
                        pdf.ln(1)
                        pdf.set_font('Arial', '', 9)
                        pregunta = "¿Se aplicó medio de contraste adicionalmente?"
                        
                        # Dibujamos la pregunta de forma controlada
                        pdf.cell(75, 5, safe_text(pregunta), 0, 0, 'L')
                        
                        # Coordenadas fijas milimétricas para dibujar el checkbox cuadrado
                        pos_x_check = pdf.get_x()
                        pos_y_check = pdf.get_y()
                        pdf.rect(pos_x_check + 2, pos_y_check, 4, 4) # Caja de 4x4mm simétrica
                        
                        # Forzamos el retorno seguro al margen izquierdo
                        pdf.set_x(10)
                        pdf.ln(6)
                    
                    pdf.ln(1)

                    pdf.set_font('Arial', 'B', 10)
                    pdf.set_text_color(128, 0, 32) # Color corporativo burdeos
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

                    # Renderizado compacto de los textos legales
                    for tit, cont in sections.items():
                        pdf.set_font('Arial', 'B', 9)
                        pdf.set_text_color(128, 0, 32)
                        pdf.cell(0, 5, safe_text(tit), 0, 1, 'L')
                        pdf.set_font('Arial', '', 8.5) # Reducimos ligeramente a 8.5 para asegurar espacio de firmas
                        pdf.set_text_color(0, 0, 0)
                        pdf.multi_cell(0, 4.2, safe_text(cont))
                        pdf.ln(2)

                    # Bloque final de autorización por parte del paciente
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
                    
                    # --- SECCIÓN DE FIRMAS Y VISACIÓN TM ---
                    pdf.ln(4)
                    
                    # Integración de la declaración del TM justo antes de la tabla de firmas
                    pdf.set_font('Arial', 'I', 8)
                    pdf.set_text_color(50, 50, 50)
                    texto_declaracion = (
                        "DECLARACIÓN DE VISACIÓN: El profesional abajo firmante certifica que ha examinado el cuestionario de seguridad del paciente, "
                        "verificando las condiciones y parámetros para la ejecución segura del examen, dando por cerrado formalmente el circuito clínico."
                    )
                    pdf.multi_cell(0, 4, safe_text(texto_declaracion), 0, 'J')
                    pdf.ln(12) # Espacio seguro para que las firmas no toquen el texto legal
                    
                    pdf.set_text_color(0, 0, 0)
                    
                    # --- ESTRUCTURACIÓN GEOMÉTRICA DE FIRMAS ---
                    # Fijamos el eje horizontal base común para ambas firmas basándonos en la posición actual del cursor
                    y_base_firmas = pdf.get_y() + 12 
                    
                    # Coordenadas X fijas e independientes para simetría bilateral perfecta
                    x_paciente = 15
                    x_profesional = 115
                    ancho_linea = 70 # Largo de la línea de firma (15 a 85 y 115 a 185)

                    # 1. RENDERIZADO GRÁFICO (Imágenes y Líneas)
                    # Firma Paciente (Izquierda)
                    if ruta_p_local and os.path.exists(ruta_p_local):
                        pdf.image(ruta_p_local, x=x_paciente + 12, y=y_base_firmas - 14, w=45)
                    pdf.line(x_paciente, y_base_firmas, x_paciente + ancho_linea, y_base_firmas)
                    
                    # Firma Profesional (Derecha)
                    if 'ruta_firma_tm_local' in locals() and os.path.exists(ruta_firma_tm_local):
                        pdf.image(ruta_firma_tm_local, x=x_profesional + 12, y=y_base_firmas - 14, w=45)
                    pdf.line(x_profesional, y_base_firmas, x_profesional + ancho_linea, y_base_firmas)

                    # 2. RENDERIZADO DE TEXTOS (Mediante celdas controladas de manera paralela)
                    # Línea 1: Títulos en Negrita
                    pdf.set_xy(x_paciente, y_base_firmas + 2)
                    pdf.set_font('Arial', 'B', 8)
                    pdf.cell(ancho_linea, 4, safe_text("FIRMA PACIENTE O REPRESENTANTE LEGAL"), 0, 0, 'L')
                    
                    pdf.set_xy(x_profesional, y_base_firmas + 2)
                    pdf.cell(ancho_linea, 4, safe_text("FIRMA PROFESIONAL RESPONSABLE"), 0, 1, 'L')
                    
                    # Línea 2: Nombres del Paciente y Tecnólogo Médico
                    nombre_firmante = rep_nombre if rep_nombre else paciente_nombre
                    pdf.set_xy(x_paciente, y_base_firmas + 6)
                    pdf.set_font('Arial', '', 8)
                    pdf.cell(ancho_linea, 4, f" {safe_text(nombre_firmante[:40])}", 0, 0, 'L')
                    
                    pdf.set_xy(x_profesional, y_base_firmas + 6)
                    pdf.cell(ancho_linea, 4, f" TM {safe_text(profesional_nombre)}", 0, 1, 'L')
                    
                    # Línea 3: Registro SIS del Profesional
                    pdf.set_xy(x_profesional, y_base_firmas + 10)
                    pdf.cell(ancho_linea, 4, f" Reg. SIS: {safe_text(profesional_registro)}", 0, 1, 'L')
                    
                    pdf.ln(2)

                    # =====================================================================
                    # 📦 EXPORTACIÓN BINARIA DEL PDF
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
        
                    # =====================================================================
                    # 📑 ASIGNACIÓN DE NOMBRE DINÁMICO
                    # =====================================================================
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
    # 📥 6. RENDERIZADO DEL BOTÓN DE DESCARGA (INMUNE A REFRESH)
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
            st.session_state.selector_refresh_key += 1  
            st.session_state.id_seleccionado_anterior = None
            st.session_state.paciente_seleccionado = None
            st.session_state.doc_completo = None
            st.session_state.pdf_ready = False
            st.session_state.pdf_bytes_data = None
            st.rerun()
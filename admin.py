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
    
    if st.button("🚀 APROBAR ENCUESTA Y GUARDAR VALIDACIÓN", use_container_width=True):
        # Validación matemática estricta: Verifica que el canvas no esté vacío (al menos un trazo realizado)
        if canvas_profesional is not None and canvas_profesional.json_data is not None and len(canvas_profesional.json_data["objects"]) > 0:
            with st.spinner("Estampando firma del profesional y asegurando registro..."):
                try:
                    # 1. Procesar la firma del profesional en formato imagen
                    img_data_tm = canvas_profesional.image_data
                    img_tm_pil = Image.fromarray(img_data_tm.astype('uint8'), 'RGBA')
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_tm:
                        img_tm_pil.save(tmp_tm.name)
                        ruta_firma_tm_local = tmp_tm.name

                    # 2. Subir la firma del TM a Firebase Storage
                    nombre_archivo_tm_storage = f"firmas_profesionales/TM_{profesional_registro}_{datetime.now(tz_chile).strftime('%Y%m%d_%H%M%S')}.png"
                    blob_tm = bucket.blob(nombre_archivo_tm_storage)
                    blob_tm.upload_from_filename(ruta_firma_tm_local, content_type='image/png')

                    # 3. Actualizar el documento en Firestore
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
                    # 📄 GENERACIÓN DEL PDF CON CLASE FPDF INSTITUTIONAL (NORTE IMAGEN)
                    # =====================================================================
                    st.info("🔄 Compilando respuestas médicas bajo formato institucional FPDF...")
                    
                    import io
                    import requests
                    from fpdf import FPDF
                    
                    # Recuperar datos del paciente desde el documento actual
                    datos_doc = doc.to_dict()
                    paciente_nombre = datos_doc.get('nombre', 'Paciente No Identificado')
                    paciente_rut = datos_doc.get('rut', datos_doc.get('run', 'N/A'))
                    paciente_edad = datos_doc.get('edad', 'N/A')
                    url_firma_paciente = datos_doc.get('firma_url', '')
                    ip_cliente = datos_doc.get('ip_dispositivo', 'No detectada')

                    # Función interna de sanitización de texto para evitar problemas con caracteres latinos
                    def safe_text(txt):
                        return str(txt).encode('latin-1', 'replace').decode('latin-1')

                    # Definición de la clase FPDF replicando el diseño de app.py
                    class PDF_Institucional(FPDF):
                        def header(self):
                            if os.path.exists("logoNI.png"):
                                self.image("logoNI.png", 10, 8, 45)
                            self.set_font('Arial', 'B', 12)
                            self.set_text_color(128, 0, 32) # Burdeos Corporativo
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
                            texto_pie = f"Certificado Digital Norte Imagen - RM: {fecha_validacion_str} - ID: {id_registro} - VALIDADO POR TM."
                            self.cell(0, 10, safe_text(texto_pie), 0, 0, 'L')
                            self.cell(0, 10, safe_text(f"Página {self.page_no()}/{{nb}}"), 0, 0, 'R')

                        def section_title(self, num, label):
                            self.set_font('Arial', 'B', 10)
                            self.set_fill_color(230, 230, 230)
                            self.set_text_color(128, 0, 32)
                            self.cell(0, 7, f"{num}. {safe_text(label)}", 0, 1, 'L', 1)
                            self.ln(2)

                    # Inicializar PDF
                    pdf = PDF_Institucional()
                    pdf.alias_nb_pages()
                    pdf.add_page()
                    pdf.set_auto_page_break(auto=True, margin=20)

                    # Sección 1: Datos Demográficos
                    pdf.section_title("1", "DATOS IDENTIFICATORIOS DEL PACIENTE")
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(35, 6, safe_text("Nombre Completo:"), 0, 0)
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(0, 6, safe_text(paciente_nombre), 0, 1)
                    
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(35, 6, safe_text("RUN / RUT:"), 0, 0)
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(55, 6, safe_text(paciente_rut), 0, 0)
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(15, 6, safe_text("Edad:"), 0, 0)
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(0, 6, safe_text(f"{paciente_edad} años"), 0, 1)
                    pdf.ln(5)

                    # Sección 2: Cuestionario Clínico (Dinámico)
                    pdf.section_title("2", "ANAMNESIS Y EVALUACION DE SEGURIDAD RM")
                    pdf.set_font('Arial', '', 9)

                    exclusiones = ['nombre', 'rut', 'run', 'edad', 'firma_url', 'estado', 'estado_validacion', 'fecha', 'timestamp', 'tecnologo_validador', 'fecha_validacion', 'firma_profesional_img', 'profesional_nombre', 'profesional_registro', 'encuesta_validada', 'ip_dispositivo']
                    
                    for clave, valor in datos_doc.items():
                        if clave not in exclusiones and not clave.startswith('firma'):
                            pregunta_limpia = clave.replace('_', ' ').capitalize()
                            if valor is True: resp_limpia = "SI"
                            elif valor is False: resp_limpia = "NO"
                            else: resp_limpia = str(valor)

                            # Evitar desbordamiento de línea en preguntas largas usando MultiCell
                            pdf.set_font('Arial', 'B', 9)
                            pdf.set_text_color(50, 50, 50)
                            pos_y_inicial = pdf.get_y()
                            pdf.multi_cell(150, 5, safe_text(f"- {pregunta_limpia}:"), 0, 'L')
                            pos_y_final = pdf.get_y()
                            
                            # Colocar la respuesta alineada a la derecha en la misma altura
                            pdf.set_viewport_side = True
                            pdf.set_xy(165, pos_y_inicial)
                            pdf.set_font('Arial', 'B', 9)
                            if resp_limpia == "SI":
                                pdf.set_text_color(128, 0, 32) # Destacar respuestas afirmativas en riesgo
                            else:
                                pdf.set_text_color(0, 0, 0)
                            pdf.cell(25, 5, safe_text(resp_limpia), 0, 1, 'R')
                            pdf.set_text_color(0, 0, 0)
                            
                            # Asegurar que el puntero baje correctamente después de MultiCell
                            if pdf.get_y() < pos_y_final:
                                pdf.set_y(pos_y_final)
                            pdf.ln(1)

                    pdf.ln(5)

                    # Sección 3: Bloque de Firmas Estructuradas
                    pdf.section_title("3", "RECONOCIMIENTO, CONSENTIMIENTO Y VALIDACION CLINICA")
                    pos_firmas_y = pdf.get_y() + 5

                    # Descargar y estampar firma del Paciente
                    if url_firma_paciente:
                        try:
                            res_paciente = requests.get(url_firma_paciente, timeout=10)
                            if res_paciente.status_code == 200:
                                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_p_img:
                                    tmp_p_img.write(res_paciente.content)
                                    ruta_p_local = tmp_p_img.name
                                pdf.image(ruta_p_local, x=25, y=pos_firmas_y, w=50, h=20)
                                os.unlink(ruta_p_local)
                        except Exception as e_p_firm:
                            pdf.set_xy(25, pos_firmas_y + 8)
                            pdf.set_font('Arial', 'I', 8)
                            pdf.cell(50, 5, safe_text("[Firma Firmada Digitalmente]"), 0, 0, 'C')

                    # Estampar firma recién dibujada del TM
                    if os.path.exists(ruta_firma_tm_local):
                        pdf.image(ruta_firma_tm_local, x=125, y=pos_firmas_y, w=50, h=20)

                    # Dibujar líneas de base e información de firmas
                    pdf.set_y(pos_firmas_y + 22)
                    pdf.set_draw_color(150, 150, 150)
                    pdf.line(20, pos_firmas_y + 21, 80, pos_firmas_y + 21)
                    pdf.line(120, pos_firmas_y + 21, 180, pos_firmas_y + 21)

                    pdf.set_font('Arial', 'B', 8)
                    pdf.set_xy(15, pos_firmas_y + 22)
                    pdf.cell(70, 4, safe_text("Firma del Paciente / Tutor"), 0, 0, 'C')
                    pdf.set_xy(115, pos_firmas_y + 22)
                    pdf.cell(70, 4, safe_text(f"Visado Electrónicamente por TM"), 0, 1, 'C')

                    pdf.set_font('Arial', '', 8)
                    pdf.set_xy(15, pdf.get_y())
                    pdf.cell(70, 4, safe_text(f"RUN: {paciente_rut}"), 0, 0, 'C')
                    pdf.set_xy(115, pdf.get_y())
                    pdf.cell(70, 4, safe_text(f"{profesional_nombre} (Reg: {profesional_registro})"), 0, 1, 'C')

                    # Compilar PDF en bytes
                    pdf_output_bytes = pdf.output(dest='S').encode('latin-1')

                    # =====================================================================
                    # 🔥 INTERFAZ INTERACTIVA: DESCARGA Y CONTROL DE PANTALLA
                    # =====================================================================
                    st.success(f"🎉 ¡Circuito Clínico Cerrado! Paciente {paciente_nombre} validado correctamente.")
                    st.balloons()
                    
                    nombre_archivo_pdf = f"Consentimiento_{paciente_rut}_{datetime.now(tz_chile).strftime('%Y%m%d')}.pdf"
                    
                    st.markdown("---")
                    st.markdown("### 📥 Descarga de Documento Oficial")
                    st.write("El consentimiento ha sido visado con ambas firmas electrónicas de Norte Imagen. Descárguelo antes de limpiar la bandeja de entrada.")
                    
                    st.download_button(
                        label="📄 DESCARGAR PDF CONSENTIMIENTO FINAL (CON AMBAS FIRMAS)",
                        data=pdf_output_bytes,
                        file_name=nombre_archivo_pdf,
                        mime="application/pdf",
                        key="btn_descarga_pdf_final",
                        use_container_width=True
                    )
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🧼 LIMPIAR BANDEJA Y CONTINUAR CON SIGUIENTE PACIENTE", use_container_width=True):
                        st.rerun()
                        
                except Exception as ex_admin:
                    st.error(f"🚨 Error operativo al cerrar el protocolo o compilar PDF: {ex_admin}")
                finally:
                    try:
                        import os
                        if os.path.exists(ruta_firma_tm_local):
                            os.unlink(ruta_firma_tm_local)
                    except:
                        pass
        else:
            st.error("🚨 Firma incompleta. Debe dibujar su firma digital en el recuadro para visar el procedimiento.")
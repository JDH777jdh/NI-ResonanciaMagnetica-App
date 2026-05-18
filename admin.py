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
                    # 📄 GENERACIÓN DEL PDF CONSOLIDADO EN TIEMPO REAL (AMBAS FIRMAS)
                    # =====================================================================
                    st.info("🔄 Compilando respuestas médicas y estampando firmas en el PDF...")
                    
                    import io
                    import requests
                    from reportlab.lib.pagesizes import letter
                    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
                    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                    from reportlab.lib import colors
                    
                    # Recuperar datos clave del paciente
                    datos_doc = doc.to_dict()
                    paciente_nombre = datos_doc.get('nombre', 'Paciente No Identificado')
                    paciente_rut = datos_doc.get('rut', datos_doc.get('run', 'N/A'))
                    paciente_edad = datos_doc.get('edad', 'N/A')
                    url_firma_paciente = datos_doc.get('firma_url', '') # Asegúrate de que este campo guarda la URL pública en tu BD
                    
                    # Configurar buffer en memoria para el PDF
                    pdf_buffer = io.BytesIO()
                    doc_pdf = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
                    story = []
                    
                    # Estilos del Documento Hospitalario
                    styles = getSampleStyleSheet()
                    style_titulo = ParagraphStyle('Titulo', parent=styles['Heading1'], fontSize=16, leading=20, alignment=1, textColor=colors.HexColor("#1A365D"))
                    style_sub_titulo = ParagraphStyle('SubTitulo', parent=styles['Heading3'], fontSize=11, leading=14, alignment=1, textColor=colors.HexColor("#4A5568"))
                    style_header_seccion = ParagraphStyle('HeaderSec', parent=styles['Heading2'], fontSize=12, leading=16, textColor=colors.white)
                    style_texto = ParagraphStyle('Texto', parent=styles['Normal'], fontSize=10, leading=14)
                    style_pregunta = ParagraphStyle('Pregunta', parent=styles['Normal'], fontSize=9, leading=12, fontWeight='Bold')
                    
                    # Encabezado Institucional
                    story.append(Paragraph("<b>DOCUMENTO DE CONSENTIMIENTO INFORMADO</b>", style_titulo))
                    story.append(Paragraph("SERVICIO DE RESONANCIA MAGNÉTICA — UNIDAD DE IMAGENOLOGÍA", style_sub_titulo))
                    story.append(Spacer(1, 15))
                    
                    # Ficha del Paciente
                    info_paciente = [
                        [Paragraph(f"<b>Paciente:</b> {paciente_nombre}", style_texto), Paragraph(f"<b>RUN/RUT:</b> {paciente_rut}", style_texto)],
                        [Paragraph(f"<b>Edad:</b> {paciente_edad} años", style_texto), Paragraph(f"<b>Fecha Visación:</b> {datetime.now(tz_chile).strftime('%d/%m/%Y %H:%M')}", style_texto)]
                    ]
                    t_paciente = Table(info_paciente, colWidths=[270, 270])
                    t_paciente.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")),
                        ('PADDING', (0,0), (-1,-1), 6),
                        ('LINEBELOW', (0,-1), (-1,-1), 1, colors.HexColor("#E2E8F0")),
                    ]))
                    story.append(t_paciente)
                    story.append(Spacer(1, 15))
                    
                    # Bloque de Cuestionario Clínico
                    story.append(Table([[Paragraph("<b>ANAMNESIS Y SEGURIDAD EN RESONANCIA MAGNÉTICA</b>", style_header_seccion)]], colWidths=[540], style=[('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2B6CB0")), ('PADDING', (0,0), (-1,-1), 5)]))
                    story.append(Spacer(1, 5))
                    
                    # Mapear dinámicamente preguntas de la encuesta
                    exclusiones = ['nombre', 'rut', 'run', 'edad', 'firma_url', 'estado', 'estado_validacion', 'fecha', 'timestamp', 'tecnologo_validador', 'fecha_validacion']
                    tabla_respuestas = []
                    
                    for clave, valor in datos_doc.items():
                        if clave not in exclusiones and not clave.startswith('firma'):
                            pregunta_limpia = clave.replace('_', ' ').capitalize()
                            if valor is True: resp_limpia = "SÍ"
                            elif valor is False: resp_limpia = "NO"
                            else: resp_limpia = str(valor)
                            
                            tabla_respuestas.append([Paragraph(pregunta_limpia, style_pregunta), Paragraph(resp_limpia, style_texto)])
                    
                    if tabla_respuestas:
                        t_encuesta = Table(tabla_respuestas, colWidths=[420, 120])
                        t_encuesta.setStyle(TableStyle([
                            ('PADDING', (0,0), (-1,-1), 4),
                            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
                            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                        ]))
                        story.append(t_encuesta)
                    else:
                        story.append(Paragraph("No se registraron respuestas médicas estructuradas en el formulario.", style_texto))
                    
                    story.append(Spacer(1, 20))
                    
                    # 4. TRATAMIENTO DE IMÁGENES DE FIRMAS
                    img_paciente = None
                    img_tm = None
                    
                    # Descargar firma del Paciente desde Firebase Storage
                    if url_firma_paciente:
                        try:
                            respuesta_img = requests.get(url_firma_paciente, timeout=10)
                            if respuesta_img.status_code == 200:
                                bytes_firma_paciente = io.BytesIO(respuesta_img.content)
                                img_paciente = RLImage(bytes_firma_paciente, width=160, height=70)
                        except Exception as e_img:
                            st.warning(f"⚠️ No se pudo cargar la imagen de la firma del paciente: {e_img}")
                    
                    if not img_paciente:
                        img_paciente = Paragraph("<font color='gray'>[Firma digitalizada en registro]</font>", style_texto)
                        
                    # Cargar firma del TM local recién dibujada
                    try:
                        img_tm = RLImage(ruta_firma_tm_local, width=160, height=70)
                    except Exception as e_img_tm:
                        img_tm = Paragraph("<font color='red'>[Firma TM no procesada]</font>", style_texto)
                    
                    # Dibujar Cuadro de Firmas lado a lado
                    bloque_firmas = [
                        [img_paciente, img_tm],
                        [Paragraph(f"<b>Firma del Paciente</b><br/>RUN: {paciente_rut}", style_texto),
                         Paragraph(f"<b>Visado por TM:</b> {profesional_nombre}<br/>Registro Clínico: {profesional_registro}", style_texto)]
                    ]
                    t_firmas = Table(bloque_firmas, colWidths=[270, 270])
                    t_firmas.setStyle(TableStyle([
                        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                        ('LINEABOVE', (0,1), (-1,1), 0.5, colors.HexColor("#718096")),
                        ('PADDING', (0,0), (-1,-1), 10),
                    ]))
                    story.append(t_firmas)
                    
                    # Construir el archivo PDF final en memoria
                    doc_pdf.build(story)
                    pdf_data = pdf_buffer.getvalue()
                    
                    # =====================================================================
                    # 🔥 INTERFAZ INTERACTIVA: DESCARGA Y CIERRE CLÍNICO
                    # =====================================================================
                    st.success(f"🎉 ¡Circuito Clínico Cerrado! Paciente {paciente_nombre} validado correctamente.")
                    st.balloons()
                    
                    nombre_archivo_pdf = f"Consentimiento_{paciente_rut}_{datetime.now(tz_chile).strftime('%Y%m%d')}.pdf"
                    
                    # Mostrar contenedor de descarga sin reiniciar la app automáticamente
                    st.markdown("---")
                    st.markdown("### 📥 Descarga de Documento Oficial")
                    st.write("El consentimiento ha sido visado con ambas firmas electrónicas. Descárguelo antes de limpiar la bandeja.")
                    
                    st.download_button(
                        label="📄 DESCARGAR PDF CONSENTIMIENTO FINAL",
                        data=pdf_data,
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
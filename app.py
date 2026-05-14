import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from fpdf import FPDF
import os
import numpy as np
import pytz
import tempfile
from PIL import Image

# Nuevas librerías para el sistema de 15GB (OAuth2)
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- CONFIGURACIÓN DE ZONA HORARIA ---
tz_chile = pytz.timezone('America/Santiago')
fecha_chile = datetime.now(tz_chile) 
fecha_str = fecha_chile.strftime("%d/%m/%Y")

# --- CONFIGURACIÓN DESDE SECRETS (NUEVO SISTEMA) ---
# Estos nombres deben coincidir EXACTO con lo que pusiste en Streamlit Secrets
CLIENT_ID = st.secrets["google_oauth"]["client_id"]
CLIENT_SECRET = st.secrets["google_oauth"]["client_secret"]
REDIRECT_URI = st.secrets["google_oauth"]["redirect_uri"]
ID_CARPETA_DRIVE = st.secrets["drive"]["folder_id"]
SCOPES = ['https://www.googleapis.com/auth/drive.file']

st.title("Norte Imagen - Registro Clínico")

# --- LÓGICA DE CONEXIÓN CON DRIVE ---
if 'credentials' not in st.session_state:
    query_params = st.query_params
    
    if "code" in query_params:
        # 1. Crear el flujo
        flow = Flow.from_client_config(
            {"web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }},
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        
        try:
            # 2. Canjear el código por el token
            flow.fetch_token(code=query_params["code"])
            st.session_state.credentials = flow.credentials
            
            # 3. ¡CRUCIAL! Limpiar el código de la URL para que no se use dos veces
            st.query_params.clear() 
            st.rerun()
            
        except Exception as e:
            st.error(f"Error al validar el código: {e}")
            st.button("Reintentar conexión", on_click=lambda: st.query_params.clear())
    else:
        # Si no hay credenciales ni código en la URL, mostrar el botón
        flow = Flow.from_client_config(
            {"web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }},
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
        st.link_button("🔑 Conectar con Google Drive (Norte Imagen)", auth_url)
        st.stop()

# --- INTERFAZ Y FORMULARIO ---
if st.session_state.credentials is None:
    st.info("⚠️ Para guardar los archivos en el almacenamiento de 15GB, debes autorizar la conexión.")
    flow = Flow.from_client_config(
        {"web": {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token"}},
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(prompt='consent')
    st.link_button("🔑 Conectar con Google Drive de Norte Imagen", auth_url)

else:
    # AQUÍ VA TODO EL RESTO DE TU CÓDIGO (Canvas, Formulario, FPDF, etc.)
    st.write(f"Fecha de registro: {fecha_str}")
    
    # Ejemplo de cómo llamarías a la función ahora:
    with st.form("mi_formulario"):
        nombre_paciente = st.text_input("Nombre Paciente")
        archivo_subido = st.file_uploader("Examen PDF")
        enviar = st.form_submit_button("Guardar en Drive")
        
        if enviar and archivo_subido:
            exito, resultado = subir_a_google_drive(archivo_subido.getvalue(), f"Examen_{nombre_paciente}.pdf")
            if exito:
                st.success(f"Guardado con ID: {resultado}")
            else:
                st.error(f"Error: {resultado}")

# 1. CONFIGURACIÓN Y ESTILOS
st.set_page_config(page_title="Norte Imagen - Registro RM", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f5f5f5; }
    .stButton>button { background-color: #800020; color: white; border-radius: 5px; width: 100%; height: 3em; font-weight: bold; }
    h1, h2, h3 { color: #800020; text-align: center; }
    label { font-weight: bold; color: #333; }
    .section-header { 
        color: #800020; border-bottom: 2px solid #800020; padding-bottom: 5px; 
        margin-top: 25px; margin-bottom: 15px; font-size: 1.3em; font-weight: bold;
    }
    .legal-text {
        background-color: #ffffff; padding: 20px; border-radius: 5px; border: 1px solid #ccc;
        font-size: 0.95em; text-align: justify; color: #333; margin-bottom: 20px;
        max-height: 500px; overflow-y: auto; line-height: 1.6;
    }
    .vfg-box { 
        background-color: #ffffff; padding: 20px; border-radius: 10px; 
        border: 2px solid #800020; text-align: center; margin-top: 20px;
    }
    .vfg-critica { border: 3px solid #ff0000 !important; color: #ff0000 !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. GESTIÓN DE ESTADO
if 'step' not in st.session_state: st.session_state.step = 1
if 'form' not in st.session_state:
    st.session_state.form = {
        "nombre": "", "rut": "", "sin_rut": False, "tipo_doc": "Pasaporte", "num_doc": "",
        "genero_idx": 0, "sexo_bio_idx": 0, "fecha_nac": date(1990, 1, 1), "email": "", 
        "nombre_tutor": "", "rut_tutor": "", "esp_idx": 0,
        "bio_marcapaso": "No", "bio_implantes": "No", "bio_detalle": "",
        "clin_ayuno": "No", "clin_asma": "No", "clin_hiperten": "No", "clin_hipertiroid": "No",
        "clin_diabetes": "No", "clin_alergico": "No", "clin_metformina": "No", "clin_renal": "No",
        "clin_dialisis": "No", "clin_claustro": "No", "clin_embarazo": "No", "clin_lactancia": "No",
        "quir_cirugia_check": "No", "quir_cirugia_detalle": "", "quir_cancer_detalle": "",
        "rt": False, "qt": False, "bt": False, "it": False, "quir_otro_trat": "",
        "ex_rx": False, "ex_mg": False, "ex_eco": False, "ex_tc": False, "ex_rm": False, "ex_otros": "",
        "creatinina": 0.0, "peso": 70.0, "vfg": 0.0,
        "veracidad": None, "autoriza_gad": None, "firma_img": None
    }

# 3. FUNCIONES DE APOYO Y MOTOR PDF
def formatear_rut(rut_sucio):
    rut_limpio = str(rut_sucio).replace(".", "").replace("-", "").upper().strip()
    if len(rut_limpio) < 2: return rut_limpio
    cuerpo, dv = rut_limpio[:-1], rut_limpio[-1]
    if cuerpo.isdigit(): return f"{int(cuerpo):,}".replace(",", ".") + f"-{dv}"
    return rut_sucio

def calcular_edad(fecha_nac):
    today = date.today()
    return today.year - fecha_nac.year - ((today.month, today.day) < (fecha_nac.month, fecha_nac.day))

from streamlit_javascript import st_javascript

def obtener_ip_cliente():
    # Este código se ejecuta en el navegador del paciente
    url_consulta = "https://api.ipify.org?format=json"
    script_js = f'fetch("{url_consulta}").then(response => response.json()).then(data => data.ip)'
    
    ip_cliente = st_javascript(script_js)
    
    # Manejo de valor nulo mientras carga el JS
    if ip_cliente is None or ip_cliente == 0:
        return "Cargando..."
    return ip_cliente

# Sanitización de texto para PDF
def safe_text(txt):
    return str(txt).encode('latin-1', 'replace').decode('latin-1')

class PDF(FPDF):
    def header(self):
        if os.path.exists("logoNI.png"):
            self.image("logoNI.png", 10, 8, 45)
        
        # Título en dos líneas - NEGRITA activada ('B')
        self.set_font('Arial', 'B', 12)
        self.set_text_color(128, 0, 32) # Color corporativo
        
        # Línea 1
        self.cell(0, 7, 'ENCUESTA DE RIESGOS ASOCIADOS Y', 0, 1, 'R')
        # Línea 2
        self.cell(0, 7, 'CONSENTIMIENTO INFORMADO', 0, 1, 'R')
        
        # Subtítulo - NEGRITA activada ('B') y tamaño mayor (16)
        self.set_font('Arial', 'B', 16)
        self.cell(0, 8, 'RESONANCIA MAGNETICA', 0, 1, 'R')
        
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 7)
        self.set_text_color(150, 150, 150)

        ahora_pie = datetime.now(tz_chile).strftime("%d/%m/%Y %H:%M:%S")
        nombre = st.session_state.form.get('nombre', '')
        iniciales = "".join([p[0].upper() for p in nombre.split() if p])

        rut_p = st.session_state.form.get('rut', 'S/R')

        # USAR LA IP GUARDADA EN EL FORMULARIO
        ip_cliente = st.session_state.form.get("ip_dispositivo", "No detectada")

        id_registro = f"{rut_p}-{iniciales} (IP:{ip_cliente})"
        texto = f"Certificado Digital Norte Imagen - Resonancia Magnética: {ahora_pie} - ID Registro: {id_registro} - Original."

        self.cell(0, 10, safe_text(texto), 0, 0, 'L')
        self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}}", 0, 0, 'R')

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

def generar_pdf_clinico(datos):
    pdf = PDF()
    pdf.alias_nb_pages()
    ahora_cierre = datetime.now(tz_chile)
    sello_digital = ahora_cierre.strftime("%d/%m/%Y %H:%M:%S")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=12)
    

    
    # --- PÁGINA 1: ENCABEZADO Y FECHA ---
    fecha_chile = datetime.now(tz_chile) 
    fecha_str = fecha_chile.strftime("%d/%m/%Y")
    
    # Tamaño sutil para la fecha superior
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 5, f"Fecha de examen: {fecha_str}", 0, 1, 'R') 
    pdf.ln(2)

    # 1. IDENTIFICACION DEL PACIENTE
    # El método section_title ya maneja su propio tamaño (10), lo mantenemos por consistencia
    pdf.section_title("1", "IDENTIFICACION DEL PACIENTE")
    
    doc_id = datos['rut'] if not datos['sin_rut'] else f"{datos['tipo_doc']}: {datos['num_doc']}"
     
    w_col = (pdf.w - 25) / 2

    # --- FILA 1: Nombre (Fuente ligeramente más grande para destacar al paciente) ---
    edad_calculada = calcular_edad(datos['fecha_nac'])
    pdf.set_font('Arial', 'B', 10)
    pdf.data_field("Nombre Completo", datos['nombre'])
    
    # --- FILA 2 a 5: Datos Personales (Tamaño estándar 9 para optimizar espacio) ---
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(w_col, 7, safe_text(f"RUT: {doc_id}"), 0, 0)
    pdf.set_x(pdf.get_x() + 5)
    pdf.cell(w_col, 7, safe_text(f"Edad: {edad_calculada} años"), 0, 1)

    pdf.cell(w_col, 7, safe_text(f"Fecha Nacimiento: {datos['fecha_nac'].strftime('%d/%m/%Y')}"), 0, 0)
    pdf.set_x(pdf.get_x() + 5)
    pdf.cell(w_col, 7, safe_text(f"Email: {datos['email']}"), 0, 1)

    pdf.cell(w_col, 7, safe_text(f"Procedimiento: {st.session_state.procedimiento}"), 0, 0)
    pdf.set_x(pdf.get_x() + 5)
    pdf.cell(w_col, 7, safe_text(f"Medio de contraste: {'SI' if st.session_state.tiene_contraste else 'NO'}"), 0, 1)

    if datos['nombre_tutor']:
        pdf.cell(w_col, 7, safe_text(f"Representante: {datos['nombre_tutor']}"), 0, 0)
        pdf.set_x(pdf.get_x() + 5)
        pdf.cell(w_col, 7, safe_text(f"RUT Representante: {datos['rut_tutor']}"), 0, 1)

    pdf.ln(2) # Reducido de 4 a 2 para ganar aire

    # 2. BIOSEGURIDAD MAGNETICA
    pdf.section_title("2", "BIOSEGURIDAD MAGNETICA")
    pdf.set_font('Arial', '', 9) # Tamaño base para seguridad
    pdf.data_field("Marcapasos cardiaco", datos['bio_marcapaso'])
    pdf.data_field("Implantes metálicos, quirúrgicos, prótesis o dispositivo electrónicos", datos['bio_implantes'])
    
    # Detalle en tamaño 8 si es muy largo, para que no salte de página
    pdf.set_font('Arial', 'I', 8)
    pdf.data_field("Detalle Bioseguridad", datos['bio_detalle'] if datos['bio_detalle'] else "Sin observaciones")
    pdf.ln(2)

    # 3. ANTECEDENTES CLINICOS (Distribución en 4 Columnas)
    pdf.section_title("3", "ANTECEDENTES CLINICOS")
    
    clinicos = [
        ("Ayuno 2hrs+", datos['clin_ayuno']), ("Asma", datos['clin_asma']), ("Alergias", datos['clin_alergico']),
        ("Hipertensión", datos['clin_hiperten']), ("Hipotiroidismo", datos['clin_hipertiroid']), ("Diabetes", datos['clin_diabetes']),
        ("Metformina 48h", datos['clin_metformina']), ("Insuf. Renal", datos['clin_renal']), ("Diálisis", datos['clin_dialisis']),
        ("Embarazo", datos['clin_embarazo']), ("Lactancia", datos['clin_lactancia']), ("Claustrofobia", datos['clin_claustro'])
    ]

    col_width = pdf.w / 4.2 
    for i in range(0, len(clinicos), 4):
        linea = clinicos[i:i+4]
        for item, valor in linea:
            pdf.set_font('Arial', '', 8) # Fuente compacta para la grilla
            texto_col = f"{item}: {valor}"
            pdf.cell(col_width, 4.5, safe_text(texto_col), 0, 0)
        pdf.ln(4.5) 

    pdf.ln(2)

    # 4. ANTECEDENTES QUIRURGICOS Y TERAPEUTICOS
    pdf.section_title("4", "ANTECEDENTES QUIRURGICOS Y TERAPEUTICOS")
    pdf.set_font('Arial', '', 9)
    pdf.data_field("Cirugías", datos['quir_cirugia_check'])
    
    pdf.set_font('Arial', '', 8) # Detalle técnico más pequeño
    pdf.data_field("Detalle cirugías", datos['quir_cirugia_detalle'] if datos['quir_cirugia_detalle'] else "N/A")
    
    trats = [k for k, v in {"RT": datos['rt'], "QT": datos['qt'], "BT": datos['bt'], "IT": datos['it']}.items() if v]
    pdf.set_font('Arial', '', 9)
    pdf.data_field("Tratamientos", ", ".join(trats) if trats else "Ninguno")
    pdf.data_field("Detalle de otros tratamientos", datos['quir_otro_trat'] if datos['quir_otro_trat'] else "N/A")
    pdf.ln(2)

    # 5. EXAMENES ANTERIORES
    pdf.section_title("5", "EXAMENES ANTERIORES")
    ex_list = [k for k, v in {"Rx": datos['ex_rx'], "MG": datos['ex_mg'], "Eco": datos['ex_eco'], "TC": datos['ex_tc'], "RM": datos['ex_rm']}.items() if v]
    pdf.set_font('Arial', '', 9)
    pdf.data_field("Exámenes", ", ".join(ex_list) if ex_list else "Ninguno")
    pdf.data_field("Otros exámenes anteriores", datos['ex_otros'] if datos['ex_otros'] else "N/A")
    pdf.ln(2)

   # 6. FUNCION RENAL
    pdf.section_title("6", "EVALUACIÓN DE LA FUNCION RENAL")
    pdf.set_font('Arial', '', 9)
    
    crea = datos.get('creatinina')
    creatinina_val = f"{crea} mg/dL" if (crea and crea > 0) else "__________ mg/dL"
    pdf.data_field("Creatinina", creatinina_val)

    peso_real = datos.get('peso')
    peso_texto = f"{peso_real} kg" if (peso_real and peso_real > 0) else "__________ kg"
    pdf.data_field("Peso", peso_texto)

    vfg_real = datos.get('vfg')
    if vfg_real and vfg_real > 0 and peso_texto != "__________ kg":
        # Determinar color y mensaje de riesgo basado en tu lógica de la APP
        if vfg_real <= 30:
            pdf.set_text_color(255, 0, 0) # Rojo
            msg_riesgo = "ALTO RIESGO para contraste"
        elif 31 <= vfg_real <= 59:
            pdf.set_text_color(184, 134, 11) # Dorado oscuro (se lee mejor en PDF que el amarillo)
            msg_riesgo = "RIESGO INTERMEDIO para contraste"
        else:
            pdf.set_text_color(34, 139, 34) # Verde bosque
            msg_riesgo = "SIN RIESGOS para contraste"

        # Escribimos el resultado con su mensaje al lado
        pdf.set_font('Arial', 'B', 9)
        pdf.write(5, f"V.F.G: {vfg_real:.2f} ml/min")
        pdf.set_font('Arial', 'B', 8) # Fuente un poco más pequeña para la nota
        pdf.write(5, f"  ({msg_riesgo})")
        
        # Volver a color negro para el resto del documento
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)
    else:
        pdf.data_field("RESULTADO VFG", "__________ ml/min (Cálculo manual)")

    pdf.ln(2)

    # 7. REGISTRO DE ADMINISTRACIÓN DE MEDIO DE CONTRASTE
    pdf.section_title("7", "REGISTRO DE ADMINISTRACION DE CONTRASTE")
    
    w_col = (pdf.w - 30) / 2
    pdf.set_font('Arial', 'B', 9) 
    pdf.set_fill_color(245, 245, 245)
    
    # Encabezados
    pdf.cell(w_col, 6, safe_text(" Acceso venoso:"), 0, 0, 'L', fill=True)
    pdf.cell(10, 6, "", 0, 0) 
    pdf.cell(w_col, 6, safe_text(" Sitio de punción:"), 0, 1, 'L', fill=True)
    
    # Fila 1: Acceso y Sitio
    pdf.set_font('Arial', '', 9)
    pdf.ln(1)
    
    # Columna Izquierda: Bránula y Mariposa (distribuidos en w_col)
    opciones_acceso = "[     ] Branula: ____ G  [     ] Mariposa: ____ G"
    pdf.cell(w_col, 8, safe_text(opciones_acceso), 0, 0, 'L') 
    
    pdf.cell(10, 8, "", 0, 0) # Espacio central
    
    # Columna Derecha: Sitio de punción (línea ajustada al ancho w_col)
    pdf.cell(w_col, 8, safe_text("________________________________"), 0, 1, 'L')
    
    pdf.ln(1)
    
    # Encabezados de Contraste
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(w_col, 6, safe_text(" Medio de contraste (Intravenoso):"), 0, 0, 'L', fill=True)
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(w_col, 6, safe_text(" Cantidad administrada:"), 0, 1, 'L', fill=True)
    
    pdf.ln(1)
    pdf.set_font('Arial', '', 9)
    
    # Guardamos la posición para manejar las dos columnas en paralelo
    pos_y_bloque = pdf.get_y()
    
    # Columna Izquierda: Opciones de fármaco
    pdf.cell(w_col, 4, safe_text("[     ] Acido gadoterico (Clariscan)"), 0, 1)
    pdf.cell(w_col, 4, safe_text("[     ] Gadopiclenol (Elucirem)"), 0, 1)
    pdf.cell(w_col, 4, safe_text("[     ] Acido gadoxetico (Primovist)"), 0, 1)
    
    # Columna Derecha: Cantidad (Volvemos arriba a la derecha)
    # Usamos el ancho w_col para que la línea no se desplace
    pdf.set_xy(pdf.get_x() + w_col + 10, pos_y_bloque)
    pdf.cell(w_col, 7, safe_text("___________ ml."), 0, 1, 'L')
    
    pdf.ln(4)

    # --- PÁGINA 2 ---
    pdf.add_page()
    

  # Apartado dinámico: Procedimiento + Contraste
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0, 0, 0)
    
    texto_procedimiento = f"Procedimiento: {st.session_state.procedimiento}"
    
    if st.session_state.tiene_contraste:
        texto_procedimiento += " con uso de medio de contraste."
        pdf.multi_cell(0, 7, safe_text(texto_procedimiento), 0, 'L')
    else:
        # Escenario B: Examen simple con pregunta y cuadro a la derecha
        pdf.multi_cell(0, 7, safe_text(texto_procedimiento), 0, 'L')
        
        pdf.ln(1)
        pdf.set_font('Arial', '', 9)
        
        # 1. Escribimos la pregunta primero (sin salto de línea)
        pregunta = "¿Se aplicó medio de contraste adicionalmente?"
        ancho_texto = pdf.get_string_width(pregunta) + 2 # Calculamos cuánto mide el texto
        pdf.cell(ancho_texto, 7, safe_text(pregunta), 0, 0, 'L')
        
        # 2. Obtenemos la posición justo donde terminó el texto
        pos_x = pdf.get_x()
        pos_y = pdf.get_y()
        
        # 3. Dibujamos el rectángulo (un poco más grande: 5x5 mm)
        # Lo subimos un poco (pos_y + 1) para que alinee bien con la altura de la fuente
        pdf.rect(pos_x + 2, pos_y + 1, 5, 5) 
        
        # 4. Hacemos el salto de línea manual para que lo siguiente no se encime
        pdf.ln(8)
    
    pdf.ln(3)
    


    # Título de Advertencia
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, "LEA ATENTA Y CUIDADOSAMENTE LO SIGUIENTE:", 0, 1, 'L')
    pdf.ln(2)

    # Secciones de Información
    sections = {
        "OBJETIVOS": (
            "La Resonancia Magnética (RM) es una segura técnica de Diagnóstico, que permite la adquisición "
            "de imágenes de gran sensibilidad en todos los planos del espacio de las estructuras del cuerpo. "
            "Tiene como objetivo obtener Información, datos funcionales y morfológicos para detectar precozmente una enfermedad.\n\n"
            "Para este examen eventualmente se puede requerir la utilización de un medio de contraste paramagnético "
            "de administración endovenosa llamado gadolinio, que permite realzar ciertos tejidos del cuerpo para un mejor diagnóstico."
        ),
        "CARACTERISTICAS": (
            "La Resonancia utiliza fuertes campos magnéticos y ondas de radiofrecuencia, por lo que es muy importante "
            "dejar fuera de la sala absolutamente todo lo que lleve consigo de tipo metálico y/o electrónico (relojes, pulseras, "
            "teléfonos, tarjetas magnéticas, etc). Si lleva material de este tipo en su cuerpo (fijaciones dentales, piercings, "
            "algunos tatuajes, balas o esquirlas metálicas) ciertos tipos de prótesis (valvulares, de cadera, de rodilla, "
            "clips metálicos, etc), o implantes, así como dispositivos electrónicos de carácter médico como bombas de insulina, "
            "prótesis auditivas, marcapasos, desfibriladores, etc. Avísenos, ya que puede contraindicar de manera absoluta la realización de este examen.\n\n"
            "Usted será posicionado en la camilla del equipo, según el estudio a realizar y se colocarán cerca de la zona a estudiar "
            "unos dispositivos (bobinas) que pueden ser de diversos tamaños. Esta exploración suele ser larga (entre 20 min y 1 hr según los casos). "
            "Notará ruido derivado del funcionamiento de la RM (por lo que le facilitaremos unos protectores auditivos), todo esto es normal "
            "y se le vigilará constantemente desde la sala de control.\n\n"
            "Es muy importante que permanezca quieto durante el estudio y siga las instrucciones del Tecnólogo Médico."
        ),
        "POTENCIALES RIESGOS": (
            "Existe una muy baja posibilidad de que se presente una reacción adversa al medio de contraste (0.07-2.4%) "
            "la mayoría de carácter leve fundamentalmente nauseas o cefaleas al momento de la inyección.\n\n"
            "Pacientes con deterioro importante de la función renal, poseen riesgo de desarrollo de fibrosis nefrogénica sistémica."
        )
    }

    for tit, cont in sections.items():
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(128, 0, 32)
        pdf.cell(0, 6, safe_text(tit), 0, 1, 'L')
        pdf.set_font('Arial', '', 9)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 5, safe_text(cont))
        pdf.ln(3)

    # Declaración de consentimiento
    pdf.set_font('Arial', '', 9)
    consentimiento_texto = (
        "He sido informado de mi derecho de anular o revocar posteriormente este documento, "
        "dejándolo constatado por escrito y firmado por mi o mi representante.\n\n"
        "Autorizo la realización del procedimiento anteriormente especificado y las acciones que sean necesarias "
        "en caso de surgir complicaciones durante el procedimiento. Además, doy consentimiento para que se administren "
        "medicamentos y/o infusiones que se requieran para la realización de este."
    )
    pdf.multi_cell(0, 5, safe_text(consentimiento_texto))
    
    # --- SECCIÓN DE FIRMAS ---
    pdf.ln(20)
    y_firma = pdf.get_y()
    
    if datos.get('firma_img'):
        pdf.image(datos['firma_img'], x=20, y=y_firma - 15, w=45)
    
    pdf.line(15, y_firma, 85, y_firma)
    pdf.set_font('Arial', 'B', 8)
    nombre_firmante = datos['nombre_tutor'] if datos['nombre_tutor'] else datos['nombre']
    pdf.text(15, y_firma + 5, "FIRMA PACIENTE O REPRESENTANTE LEGAL")
    pdf.set_font('Arial', '', 8)
    pdf.text(15, y_firma + 9, f" {safe_text(nombre_firmante[:40])}")
    
    pdf.line(115, y_firma, 185, y_firma)
    pdf.set_font('Arial', 'B', 8)
    pdf.text(115, y_firma + 5, "FIRMA PROFESIONAL RESPONSABLE")

    return pdf.output(dest='S').encode('latin-1', 'replace')

def mostrar_logo():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if os.path.exists("logoNI.png"): st.image("logoNI.png", use_container_width=True)
        else: st.subheader("NORTE IMAGEN")

@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv('listado_prestaciones.csv', sep=None, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        return df
    except: return None

df = cargar_datos()

from streamlit_javascript import st_javascript

def obtener_ip():
    """Captura la IP real del dispositivo del paciente usando JavaScript."""
    try:
        # Intentamos vía JavaScript (Navegador del Paciente)
        url_consulta = "https://api.ipify.org?format=json"
        script_js = f'fetch("{url_consulta}").then(response => response.json()).then(data => data.ip)'
        ip_js = st_javascript(script_js)
        
        if ip_js and ip_js != 0:
            return ip_js
    except:
        pass

    # Respaldo vía Python (Servidor)
    import requests
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=2)
        return response.json()['ip']
    except:
        return "0.0.0.0"

# --- PÁGINA 1: REGISTRO ---
if st.session_state.step == 1:
    # 1. CAPTURA DE IP
    # Intentamos capturar la IP. st_javascript devolverá None o 0 al principio.
    ip_detectada = obtener_ip() 
    
    # Solo guardamos si realmente obtuvimos una IP válida
    if ip_detectada and ip_detectada not in ["Cargando...", "0.0.0.0", 0]:
        st.session_state.form["ip_dispositivo"] = ip_detectada
    else:
        # Valor por defecto temporal para que no falle el PDF si el paciente es muy rápido
        if "ip_dispositivo" not in st.session_state.form:
            st.session_state.form["ip_dispositivo"] = "Buscando IP..."
    
    # 2. INTERFAZ VISUAL
    mostrar_logo()
    st.title("Registro de Paciente")
    
    if df is not None:
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.form["nombre"] = st.text_input("Nombre Completo del Paciente", value=st.session_state.form["nombre"])
            rut_p = st.text_input("RUT del Paciente", value=st.session_state.form["rut"], placeholder="12.345.678-K")
            st.session_state.form["rut"] = formatear_rut(rut_p)
            st.session_state.form["sin_rut"] = st.checkbox("Sin RUT, poseo otro documento", value=st.session_state.form["sin_rut"])
            if st.session_state.form["sin_rut"]:
                t_opts = ["Pasaporte", "Cédula de extranjero"]
                idx_doc = t_opts.index(st.session_state.form["tipo_doc"]) if st.session_state.form["tipo_doc"] in t_opts else 0
                st.session_state.form["tipo_doc"] = st.selectbox("Tipo de documento", t_opts, index=idx_doc)
                st.session_state.form["num_doc"] = st.text_input("N° de documento", value=st.session_state.form["num_doc"])
            
            g_opts = ["Masculino", "Femenino", "No binario"]
            gen_sel = st.selectbox("Identidad de Género", g_opts, index=st.session_state.form["genero_idx"])
            st.session_state.form["genero_idx"] = g_opts.index(gen_sel)
            sexo_final = gen_sel
            if gen_sel == "No binario":
                sb_opts = ["Masculino", "Femenino"]
                sexo_bio = st.selectbox("Sexo asignado al nacer (Para fines clínicos)", sb_opts, index=st.session_state.form["sexo_bio_idx"])
                st.session_state.form["sexo_bio_idx"] = sb_opts.index(sexo_bio)
                sexo_final = sexo_bio

        with c2:
            st.session_state.form["fecha_nac"] = st.date_input("Fecha de Nacimiento", value=st.session_state.form["fecha_nac"], min_value=date(1910, 1, 1), max_value=date.today(), format="DD/MM/YYYY")
            st.session_state.form["email"] = st.text_input("Email de contacto", value=st.session_state.form["email"])
        
        edad = calcular_edad(st.session_state.form["fecha_nac"])
        if edad < 18:
            st.warning(f"👦 PACIENTE MENOR DE EDAD ({edad} años)")
            st.session_state.form["nombre_tutor"] = st.text_input("Nombre Representante Legal", value=st.session_state.form["nombre_tutor"])
            st.session_state.form["rut_tutor"] = formatear_rut(st.text_input("RUT Representante", value=st.session_state.form["rut_tutor"]))

        st.markdown('<div class="section-header">Información del Examen</div>', unsafe_allow_html=True)
        esp_raw = sorted([str(e) for e in df['ESPECIALIDAD'].unique() if pd.notna(e)])
        ce1, ce2 = st.columns(2)
        esp_sel = ce1.selectbox("Especialidad", esp_raw, index=st.session_state.form["esp_idx"])
        st.session_state.form["esp_idx"] = esp_raw.index(esp_sel)
        
        filtered = df[df['ESPECIALIDAD'] == esp_sel]
        list_pre = sorted(filtered['PROCEDIMIENTO A REALIZAR'].dropna().unique().tolist())
        pre_sel = ce2.selectbox("Procedimiento", list_pre)

        st.markdown('<div class="section-header">Documentación Médica</div>', unsafe_allow_html=True)
        st.file_uploader("Cargue la Orden Médica (Obligatorio)", type=["pdf", "jpg", "jpeg"], key="up_orden_p1")
        st.file_uploader("Cargue Exámenes Anteriores (Máximo 4 archivos)", type=["pdf", "jpg", "jpeg"], accept_multiple_files=True, key="up_anteriores_p1")

        if st.button("CONTINUAR"):
            if st.session_state.form["nombre"]:
                row = df[(df['ESPECIALIDAD'] == esp_sel) & (df['PROCEDIMIENTO A REALIZAR'] == pre_sel)]
                st.session_state.tiene_contraste = str(row['MEDIO DE CONTRASTE'].values[0]).upper() == "SI" if not row.empty else False
                st.session_state.procedimiento = pre_sel
                st.session_state.edad_para_calculo = edad
                st.session_state.sexo_para_calculo = sexo_final
                st.session_state.step = 2; st.rerun()

# --- PÁGINA 2: CUESTIONARIO ---
elif st.session_state.step == 2:
    mostrar_logo(); st.title("📋 Cuestionario de Seguridad RM")
    opts = ["No", "Sí"]

    st.markdown('<div class="section-header">1. Bioseguridad Magnética</div>', unsafe_allow_html=True)
    st.session_state.form["bio_marcapaso"] = st.radio("Marcapasos cardiaco:", opts, index=opts.index(st.session_state.form["bio_marcapaso"]), horizontal=True)
    st.session_state.form["bio_implantes"] = st.radio("Implantes metálicos, quirúrgicos, prótesis o dispositivos electrónicos:", opts, index=opts.index(st.session_state.form["bio_implantes"]), horizontal=True)
    st.session_state.form["bio_detalle"] = st.text_area("Detalle de que tipo y ubicación:", value=st.session_state.form["bio_detalle"], height=70)

    st.markdown('<div class="section-header">2. Antecedentes Clínicos</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    k1 = [("clin_ayuno", "Ayuno (2 hrs o mas)"), ("clin_asma", "Asma"), ("clin_hiperten", "Hipertensión"), ("clin_hipertiroid", "Hipertiroidismo")]
    k2 = [("clin_diabetes", "Diabetes"), ("clin_alergico", "Alérgico"), ("clin_metformina", "Suspende metformina (48 hrs. antes)"), ("clin_renal", "Insuficiencia renal")]
    k3 = [("clin_dialisis", "Diálisis"), ("clin_claustro", "Claustrofóbico"), ("clin_embarazo", "Embarazo"), ("clin_lactancia", "Lactancia")]
    for col, keys in zip([c1, c2, c3], [k1, k2, k3]):
        for k, label in keys: st.session_state.form[k] = col.radio(label, opts, index=opts.index(st.session_state.form[k]))

    st.markdown('<div class="section-header">3. Antecedentes Quirúrgicos y/o Terapéuticos</div>', unsafe_allow_html=True)
    st.session_state.form["quir_cirugia_check"] = st.radio("¿Ha sido sometido a alguna cirugía o más de una?", opts, index=opts.index(st.session_state.form["quir_cirugia_check"]), horizontal=True)
    st.session_state.form["quir_cirugia_detalle"] = st.text_area("Detalle nombre de la cirugía y fecha:", value=st.session_state.form["quir_cirugia_detalle"], height=70)
    
    ct1, ct2, ct3, ct4 = st.columns(4)
    st.session_state.form["rt"] = ct1.checkbox("Radioterapia (RT)", value=st.session_state.form["rt"])
    st.session_state.form["qt"] = ct2.checkbox("Quimioterapia (QT)", value=st.session_state.form["qt"])
    st.session_state.form["bt"] = ct3.checkbox("Braquiterapia (BT)", value=st.session_state.form["bt"])
    st.session_state.form["it"] = ct4.checkbox("Inmunoterapia (IT)", value=st.session_state.form["it"])
    st.session_state.form["quir_otro_trat"] = st.text_input("Algún otro tratamiento que mencionar:", value=st.session_state.form["quir_otro_trat"])

    st.markdown('<div class="section-header">4. Exámenes anteriores</div>', unsafe_allow_html=True)
    ce1, ce2, ce3, ce4, ce5 = st.columns(5)
    st.session_state.form["ex_rx"] = ce1.checkbox("Radiografía (Rx)", value=st.session_state.form["ex_rx"])
    st.session_state.form["ex_mg"] = ce2.checkbox("Mamografía (MG)", value=st.session_state.form["ex_mg"])
    st.session_state.form["ex_eco"] = ce3.checkbox("Ecotomografía (Eco)", value=st.session_state.form["ex_eco"])
    st.session_state.form["ex_tc"] = ce4.checkbox("Tomografía (TC)", value=st.session_state.form["ex_tc"])
    st.session_state.form["ex_rm"] = ce5.checkbox("Resonancia (RM)", value=st.session_state.form["ex_rm"])
    st.session_state.form["ex_otros"] = st.text_input("Otros estudios:", value=st.session_state.form["ex_otros"])

    if st.session_state.tiene_contraste:
        st.markdown('<div class="section-header">5. Función Renal (VFG según Fórmula de Cockcroft-Gault)</div>', unsafe_allow_html=True)
        st.session_state.form["creatinina"] = st.number_input("Creatinina (mg/dL)", value=st.session_state.form["creatinina"], step=0.01)
        st.session_state.form["peso"] = st.number_input("Peso (kg)", value=st.session_state.form["peso"])
    
    if st.session_state.form["creatinina"] > 0:
        # Cálculo de VFG (Fórmula de Cockcroft-Gault)
        vfg = ((140 - st.session_state.edad_para_calculo) * st.session_state.form["peso"]) / (72 * st.session_state.form["creatinina"])
        if st.session_state.sexo_para_calculo == "Femenino": 
            vfg *= 0.85
        
        st.session_state.form["vfg"] = vfg

        # --- LÓGICA DE COLORES Y MENSAJES ---
        if vfg <= 30:
            estilo = "vfg-critica"  # Asegúrate que esta clase en tu CSS tenga background rojo
            mensaje = "🔴 Alto riesgo para la administración de medio de contraste"
            color_texto = "#FF0000" # Rojo
        elif 31 <= vfg <= 59:
            estilo = "vfg-intermedia" # Deberás crear esta clase o usar estilos inline
            mensaje = "⚠️ Riesgo intermedio para la administración de medio de contraste"
            color_texto = "#FFCC00" # Amarillo/Dorado
        else:
            estilo = "vfg-normal" # Deberás crear esta clase
            mensaje = "✅ Sin riesgos para la administración del medio de contraste"
            color_texto = "#28A745" # Verde

        # Renderizado en la App
        # Usamos un div con estilo dinámico para el borde/fondo y el mensaje abajo
        st.markdown(f'''
            <div class="vfg-box {estilo}" style="border-left: 10px solid {color_texto}; padding: 15px; border-radius: 5px;">
                <p style="margin:0; color: {color_texto}; font-weight: bold;">{mensaje}</p>
                <small>Resultado VFG:</small>
                <h2 style="margin:0;">{vfg:.2f} ml/min</h2>
            </div>
        ''', unsafe_allow_html=True)

    st.write("")
    col_nav = st.columns(2)
    if col_nav[0].button("ATRÁS"): st.session_state.step = 1; st.rerun()
    if col_nav[1].button("SIGUIENTE"):
        st.session_state.step = 3; st.rerun()

# --- PÁGINA 3: INFORMACIÓN Y FIRMA ---
elif st.session_state.step == 3:
    mostrar_logo(); st.title("Información al Paciente")
    st.markdown('<div class="section-header">LEA ATENTA Y CUIDADOSAMENTE LO SIGUIENTE:</div>', unsafe_allow_html=True)
    st.markdown("""
        <div class="legal-text">
        <strong>OBJETIVOS</strong><br>
        La Resonancia Magnética (RM) es una segura técnica de Diagnóstico, que permite la adquisición de imágenes de gran sensibilidad en todos los planos del espacio de las estructuras del cuerpo. Tiene como objetivo obtener Información, datos funcionales y morfológicos para detectar precozmente una enfermedad.<br>
        Para este examen eventualmente se puede requerir la utilización de un medio de contraste paramagnético de administración endovenosa llamado gadolinio, que permite realzar ciertos tejidos del cuerpo para un mejor diagnóstico.<br><br>
        <strong>CARACTERISTICAS</strong><br>
        La Resonancia utiliza fuertes campos magnéticos y ondas de radiofrecuencia, por lo que es muy importante dejar fuera de la sala absolutamente todo lo que lleve consigo de tipo metálico y/o electrónico (relojes, pulseras, teléfonos, tarjetas magnéticas, etc). Si lleva material de este tipo en su cuerpo (fijaciones dentales, piercings, algunos tatuajes, balas o esquirlas metálicas) ciertos tipos de prótesis (valvulares, de cadera, de rodilla, clips metálicos, etc), o implantes, así como dispositivos electrónicos de carácter médico como bombas de insulina, prótesis auditivas, marcapasos, desfibriladores, etc. Avísenos, ya que puede contraindicar de manera absoluta la realización de este examen.<br>
        Usted será posicionado en la camilla del equipo, según el estudio a realizar y se colocarán cerca de la zona a estudiar unos dispositivos (bobinas) que pueden ser de diversos tamaños. Esta exploración suele ser larga (entre 20 min y 1 hr según los casos). Notará ruido derivado del funcionamiento de la RM (por lo que le facilitaremos unos protectores auditivos), todo esto es normal y se le vigilará constantemente desde la sala de control.<br>
        Es muy importante que permanezca quieto durante el estudio y siga las instrucciones del Tecnólogo Médico.<br><br>
        <strong>POTENCIALES RIESGOS</strong><br>
        Existe una muy baja posibilidad de que se presente una reacción adversa al medio de contraste (0.07-2.4%) la mayoría de carácter leve fundamentalmente nauseas o cefaleas al momento de la inyección.<br>
        Pacientes con deterioro importante de la función renal, poseen riesgo de desarrollo de fibrosis nefrogénica sistémica.<br><hr>
        He sido informado de mi derecho de anular o revocar posteriormente este documento, dejándolo constatado por escrito y firmado por mi o mi representante.<br><br>
        Autorizo la realización del procedimiento anteriormente especificado y las acciones que sean necesarias en caso de surgir complicaciones durante el procedimiento. Además, doy consentimiento para que se administren medicamentos y/o infusiones que se requieran para la realización de este.
        </div>
        """, unsafe_allow_html=True)

    st.session_state.form["autoriza_gad"] = st.radio("¿Ha leído y autoriza el procedimiento?", ["SÍ", "NO"], index=None)
    st.write("Firma del Paciente / Tutor:")
    canvas_result = st_canvas(stroke_width=2, stroke_color="#000", background_color="#fff", height=150, width=400, key="canvas")
    
    c_nav = st.columns(2)
    if c_nav[0].button("ATRÁS"): st.session_state.step = 2; st.rerun()
    if c_nav[1].button("FINALIZAR REGISTRO"):
        if st.session_state.form["autoriza_gad"] == "SÍ" and np.any(canvas_result.image_data[:, :, 3] > 0):
            img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                img.save(tmp.name); st.session_state.form["firma_img"] = tmp.name
            st.session_state.step = 4; st.balloons(); st.rerun()
        else: st.error("Debe firmar y autorizar para finalizar.")

# --- PÁGINA 4: FINALIZACIÓN ---
elif st.session_state.step == 4:
    mostrar_logo(); st.success("Registro Completado")
    pdf_bytes = generar_pdf_clinico(st.session_state.form)
    nombre_final = f"Registro_{st.session_state.form['rut']}_{datetime.now().strftime('%H%M%S')}.pdf"
    
    with st.spinner("Sincronizando con Google Drive..."):
        exito, resultado = subir_a_google_drive(pdf_bytes, nombre_final)
        if st.session_state.get("up_orden_p1"):
            orden = st.session_state["up_orden_p1"]
            subir_a_google_drive(orden.getvalue(), f"ORDEN_{st.session_state.form['rut']}_{orden.name}")
        if st.session_state.get("up_anteriores_p1"):
            for i, exam in enumerate(st.session_state["up_anteriores_p1"]):
                subir_a_google_drive(exam.getvalue(), f"EXAM_{i}_{st.session_state.form['rut']}_{exam.name}")
        if exito: st.info(f"✅ Sincronizado (ID: {resultado})")
        else: st.warning(f"⚠️ Error Drive: {resultado}")

    st.download_button("📥 Descargar Copia PDF", data=pdf_bytes, file_name=nombre_final, mime="application/pdf")
    if st.button("Nuevo Registro"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
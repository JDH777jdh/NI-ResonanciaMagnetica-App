import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from fpdf import FPDF
import os
from PIL import Image
import io
import re

# 1. CONFIGURACIÓN Y ESTILO VISUAL NORTE IMAGEN
st.set_page_config(page_title="Norte Imagen - Registro RM", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .stButton>button { 
        background-color: #800020; color: white; border-radius: 8px; 
        width: 100%; height: 3.5em; font-weight: bold; border: none;
    }
    .stButton>button:hover { background-color: #a00028; color: white; }
    h1, h2, h3 { color: #800020; text-align: center; font-family: 'Helvetica', sans-serif; }
    .section-header { 
        color: white; background-color: #800020; padding: 10px; 
        border-radius: 5px; margin-top: 20px; margin-bottom: 15px; 
        font-size: 1.1em; font-weight: bold; text-align: center;
    }
    .legal-text {
        background-color: #ffffff; padding: 20px; border-radius: 5px; border: 1px solid #dee2e6;
        font-size: 0.85em; text-align: justify; color: #444; margin-bottom: 20px;
        max-height: 300px; overflow-y: auto; line-height: 1.4;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. PERSISTENCIA DE DATOS (SESSION STATE)
if 'step' not in st.session_state:
    st.session_state.step = 1

if 'form' not in st.session_state:
    st.session_state.form = {
        "nombre": "", "rut": "", "sin_rut": False, "tipo_doc": "Pasaporte", "num_doc": "",
        "genero": "Masculino", "fecha_nac": date(2000, 1, 1), "email": "", 
        "nombre_tutor": "", "rut_tutor": "", "es_menor": False,
        "esp_nombre": "", "pre_nombre": "",
        "ant_ayuno": "No", "ant_asma": "No", "ant_diabetes": "No", "ant_hiperten": "No",
        "ant_hipertiroid": "No", "ant_renal": "No", "ant_dialisis": "No", 
        "ant_implantes": "No", "ant_marcapaso": "No", "ant_metformina": "No",
        "ant_embarazo": "No", "ant_lactancia": "No", "ant_cardiaca": "No",
        "otras_cirugias": "", "tipo_cancer": "", "rt": False, "qt": False, "bt": False, "it": False,
        "ex_rx": False, "ex_eco": False, "ex_tc": False, "ex_rm": False,
        "creatinina": 0.0, "peso": 70.0, "vfg": 0.0, "firma_img": None
    }

# 3. LÓGICA DE NEGOCIO Y FORMATOS
def formatear_rut(rut_sucio):
    if not rut_sucio: return ""
    rut_limpio = str(rut_sucio).replace(".", "").replace("-", "").upper().strip()
    if len(rut_limpio) < 2: return rut_limpio
    cuerpo, dv = rut_limpio[:-1], rut_limpio[-1]
    if cuerpo.isdigit():
        return f"{int(cuerpo):,}-{dv}".replace(",", ".")
    return rut_sucio

def calcular_edad(fecha_nac):
    today = date.today()
    return today.year - fecha_nac.year - ((today.month, today.day) < (fecha_nac.month, fecha_nac.day))

def obtener_iniciales(nombre_completo):
    partes = nombre_completo.strip().split()
    if len(partes) < 2: return "PX"
    # Toma la inicial de los apellidos (del segundo elemento en adelante)
    return "".join([p[0].upper() for p in partes[1:]])

# 4. GENERADOR DE PDF PROFESIONAL
def generar_pdf_clinico(datos):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado Corporativo
    if os.path.exists("logoNI.png"):
        pdf.image("logoNI.png", x=10, y=10, w=38)
    
    pdf.set_font("Arial", 'B', 22)
    pdf.set_text_color(128, 0, 32)
    pdf.set_xy(55, 12)
    pdf.cell(140, 10, txt="Norte Imagen", ln=True)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(80, 80, 80)
    pdf.set_x(55)
    pdf.cell(140, 8, txt="Unidad de Resonancia Magnetica", ln=True)
    
    pdf.set_font("Arial", 'I', 10)
    pdf.set_x(55)
    pdf.cell(140, 6, txt="Consentimiento Informado y Anamnesis Proyectada", ln=True)
    
    pdf.ln(15)
    pdf.set_text_color(0, 0, 0)

    # Bloque 1: Datos del Paciente
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, txt=" 1. IDENTIFICACION DEL PACIENTE", ln=True, fill=True)
    pdf.set_font("Arial", size=10)
    pdf.ln(2)
    
    id_pac = datos['rut'] if not datos['sin_rut'] else f"{datos['tipo_doc']} {datos['num_doc']}"
    pdf.cell(110, 7, txt=f"Nombre: {datos['nombre']}".encode('latin-1', 'replace').decode('latin-1'), ln=0)
    pdf.cell(80, 7, txt=f"RUT/ID: {id_pac}", ln=1)
    
    f_nac_fmt = datos['fecha_nac'].strftime("%d/%m/%Y")
    pdf.cell(110, 7, txt=f"Fecha de Nacimiento: {f_nac_fmt}", ln=0)
    pdf.cell(80, 7, txt=f"Genero: {datos['genero']}", ln=1)
    pdf.cell(190, 7, txt=f"Email: {datos['email']}", ln=1)
    
    if datos['es_menor']:
        pdf.set_font("Arial", 'B', 10)
        pdf.set_text_color(128, 0, 32)
        pdf.cell(190, 7, txt=f"REPRESENTANTE LEGAL: {datos['nombre_tutor']} (RUT: {datos['rut_tutor']})".encode('latin-1', 'replace').decode('latin-1'), ln=1)
        pdf.set_text_color(0, 0, 0)
    
    # Bloque 2: Examen
    pdf.ln(4)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, txt=" 2. DETALLES DEL PROCEDIMIENTO", ln=True, fill=True)
    pdf.set_font("Arial", size=10)
    pdf.ln(2)
    pdf.cell(190, 7, txt=f"Especialidad: {datos['esp_nombre']}".encode('latin-1', 'replace').decode('latin-1'), ln=1)
    pdf.cell(190, 7, txt=f"Estudio: {datos['pre_nombre']}".encode('latin-1', 'replace').decode('latin-1'), ln=1)
    
    if datos['vfg'] > 0:
        pdf.cell(190, 7, txt=f"Funcion Renal: Creatinina {datos['creatinina']} / VFG: {datos['vfg']:.2f} mL/min", ln=1)

    # Bloque 3: Encuesta Completa (Sin Resúmenes)
    pdf.ln(4)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, txt=" 3. ANAMNESIS Y SEGURIDAD (ENCUESTA)", ln=True, fill=True)
    pdf.set_font("Arial", size=8.5)
    pdf.ln(2)
    
    items = [
        ("Ayuno (4 hrs)", datos['ant_ayuno']), ("Asma", datos['ant_asma']),
        ("Diabetes", datos['ant_diabetes']), ("Hipertension", datos['ant_hiperten']),
        ("Falla Renal", datos['ant_renal']), ("Dialisis", datos['ant_dialisis']),
        ("Marcapaso", datos['ant_marcapaso']), ("Implantes Metalicos", datos['ant_implantes']),
        ("Metformina", datos['ant_metformina']), ("Embarazo", datos['ant_embarazo']),
        ("Lactancia", datos['ant_lactancia']), ("Cardiopatia", datos['ant_cardiaca'])
    ]
    
    for i in range(0, len(items), 2):
        pdf.cell(95, 6, txt=f"{items[i][0]}: {items[i][1]}", ln=0)
        pdf.cell(95, 6, txt=f"{items[i+1][0]}: {items[i+1][1]}", ln=1)

    if datos['otras_cirugias']:
        pdf.multi_cell(190, 5, txt=f"Cirugias/Otros: {datos['otras_cirugias']}".encode('latin-1', 'replace').decode('latin-1'))

    # Bloque 4: Firmas
    pdf.ln(15)
    if datos['firma_img']:
        buf = io.BytesIO()
        datos['firma_img'].save(buf, format='PNG')
        buf.seek(0)
        pdf.image(buf, x=35, y=pdf.get_y(), w=40)
    
    pdf.ln(25)
    y_linea = pdf.get_y()
    pdf.line(20, y_linea, 85, y_linea)
    pdf.line(125, y_linea, 190, y_linea)
    pdf.set_font("Arial", 'B', 8)
    pdf.set_xy(20, y_linea + 2)
    pdf.cell(65, 5, txt="FIRMA PACIENTE O TUTOR", align='C')
    pdf.set_xy(125, y_linea + 2)
    pdf.cell(65, 5, txt="FIRMA PROFESIONAL NORTE IMAGEN", align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_prestaciones():
    if os.path.exists('listado_prestaciones.csv'):
        df = pd.read_csv('listado_prestaciones.csv', sep=None, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        return df
    return None

df_db = cargar_prestaciones()

# --- NAVEGACIÓN ---

# PASO 1: DATOS PERSONALES Y FILTROS MÉDICOS
if st.session_state.step == 1:
    if os.path.exists("logoNI.png"): st.image("logoNI.png", width=200)
    st.title("Registro de Paciente")
    
    st.markdown('<div class="section-header">INFORMACIÓN PERSONAL</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    nombre = col1.text_input("Nombre Completo", value=st.session_state.form["nombre"])
    
    sin_rut = st.checkbox("Soy extranjero / No poseo RUT chileno", value=st.session_state.form["sin_rut"])
    if not sin_rut:
        rut_raw = col2.text_input("RUT (ej: 12.345.678-9)", value=st.session_state.form["rut"])
        rut_val = formatear_rut(rut_raw)
    else:
        t_doc = col2.selectbox("Tipo Documento", ["Pasaporte", "DNI", "Otro"])
        n_doc = col2.text_input("Numero de Documento")
        rut_val = ""

    c3, c4 = st.columns(2)
    f_nac = c3.date_input("Fecha de Nacimiento", value=st.session_state.form["fecha_nac"], format="DD/MM/YYYY")
    genero = c4.selectbox("Identidad de Genero", ["Masculino", "Femenino", "No Binario", "Transgenero", "Prefiero no decir"])
    email = st.text_input("E-mail de contacto", value=st.session_state.form["email"])

    # LÓGICA DE MINORÍA DE EDAD
    edad_actual = calcular_edad(f_nac)
    es_menor = edad_actual < 18
    nombre_tutor, rut_tutor = "", ""
    
    if es_menor:
        st.error(f"⚠️ El paciente es menor de edad ({edad_actual} años). Se requiere la firma de un Tutor Legal.")
        ct1, ct2 = st.columns(2)
        nombre_tutor = ct1.text_input("Nombre Completo del Tutor")
        rut_tutor = ct2.text_input("RUT del Tutor")

    # SECCIÓN DE ESPECIALIDADES
    if df_db is not None:
        st.markdown('<div class="section-header">ESPECIALIDAD Y EXAMEN</div>', unsafe_allow_html=True)
        # Ordenar: NEURORRADIOLOGIA primero
        lista_esp = sorted([str(e) for e in df_db['ESPECIALIDAD'].unique() if pd.notna(e)])
        if "NEURORRADIOLOGIA" in lista_esp:
            lista_esp.remove("NEURORRADIOLOGIA")
            lista_esp.insert(0, "NEURORRADIOLOGIA")
        
        esp_sel = st.selectbox("Seleccione Especialidad", lista_esp)
        
        # Filtro de procedimientos basado en especialidad
        df_proc = df_db[df_db['ESPECIALIDAD'] == esp_sel]
        lista_proc = sorted(df_proc['PROCEDIMIENTO A REALIZAR'].unique().tolist())
        pre_sel = st.selectbox("Seleccione el Estudio", lista_proc)

    if st.button("CONTINUAR A ENCUESTA"):
        if not nombre or (not sin_rut and not rut_raw):
            st.warning("Por favor complete los campos obligatorios.")
        else:
            st.session_state.form.update({
                "nombre": nombre, "rut": rut_val, "sin_rut": sin_rut, "fecha_nac": f_nac,
                "genero": genero, "email": email, "es_menor": es_menor,
                "nombre_tutor": nombre_tutor, "rut_tutor": formatear_rut(rut_tutor),
                "esp_nombre": esp_sel, "pre_nombre": pre_sel
            })
            # Verificar contraste
            row = df_db[df_db['PROCEDIMIENTO A REALIZAR'] == pre_sel]
            st.session_state.tiene_contraste = "SI" in str(row['MEDIO DE CONTRASTE'].values[0]).upper()
            st.session_state.step = 2
            st.rerun()

# PASO 2: ENCUESTA MÉDICA DETALLADA
elif st.session_state.step == 2:
    st.title("📋 Anamnesis de Seguridad")
    st.info("Responda con total honestidad. Esta información es vital para su seguridad dentro del resonador.")
    
    opts = ["No", "Sí"]
    
    st.markdown('<div class="section-header">CUESTIONARIO DE SALUD</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    st.session_state.form["ant_ayuno"] = c1.radio("Ayuno (4 horas)", opts)
    st.session_state.form["ant_asma"] = c2.radio("Asma", opts)
    st.session_state.form["ant_diabetes"] = c3.radio("Diabetes", opts)
    
    st.session_state.form["ant_hiperten"] = c1.radio("Hipertensión", opts)
    st.session_state.form["ant_renal"] = c2.radio("Enfermedad Renal", opts)
    st.session_state.form["ant_marcapaso"] = c3.radio("Marcapaso / Prótesis", opts)
    
    st.session_state.form["ant_metformina"] = c1.radio("Toma Metformina", opts)
    st.session_state.form["ant_embarazo"] = c2.radio("¿Está Embarazada?", opts)
    st.session_state.form["ant_lactancia"] = c3.radio("¿Está Lactando?", opts)

    st.session_state.form["otras_cirugias"] = st.text_area("Describa cirugías previas o implantes dentales/auditivos:")

    st.markdown('<div class="section-header">ESTUDIOS PREVIOS</div>', unsafe_allow_html=True)
    cx = st.columns(4)
    st.session_state.form["ex_rx"] = cx[0].checkbox("Rx")
    st.session_state.form["ex_eco"] = cx[1].checkbox("Eco")
    st.session_state.form["ex_tc"] = cx[2].checkbox("TC (Scanner)")
    st.session_state.form["ex_rm"] = cx[3].checkbox("RM")

    if st.session_state.tiene_contraste:
        st.warning("🧪 Este examen requiere contraste endovenoso.")
        st.session_state.form["creatinina"] = st.number_input("Valor Creatinina (mg/dL)", step=0.01)
        st.session_state.form["peso"] = st.number_input("Peso (Kg)", value=70.0)
        if st.session_state.form["creatinina"] > 0:
            edad = calcular_edad(st.session_state.form["fecha_nac"])
            vfg = ((140 - edad) * st.session_state.form["peso"]) / (72 * st.session_state.form["creatinina"])
            st.session_state.form["vfg"] = vfg
            st.success(f"VFG Calculado: {vfg:.2f} mL/min")

    if st.button("IR A CONSENTIMIENTO Y FIRMA"):
        st.session_state.step = 3; st.rerun()

# PASO 3: FIRMA Y CONSENTIMIENTO
elif st.session_state.step == 3:
    st.title("🖋️ Consentimiento Legal")
    
    st.markdown("""
    <div class="legal-text">
    <b>AUTORIZACIÓN:</b> Por la presente, autorizo al equipo de <b>Norte Imagen</b> a realizar el examen de Resonancia Magnética prescrito. 
    Comprendo que este examen utiliza campos magnéticos potentes y ondas de radio. Declaro no portar marcapasos ni elementos ferromagnéticos 
    no informados. Asimismo, autorizo la administración de contraste si el protocolo médico lo requiere, conociendo los posibles 
    riesgos de reacciones alérgicas. Declaro que toda la información entregada en la anamnesis es verídica.
    </div>
    """, unsafe_allow_html=True)
    
    st.write("Firme a continuación (use el mouse o pantalla táctil):")
    canvas_result = st_canvas(stroke_width=3, stroke_color="#000", background_color="#fff", height=200, width=500, key="canvas")
    
    if st.button("FINALIZAR REGISTRO"):
        if canvas_result.image_data is not None:
            st.session_state.form["firma_img"] = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA').convert("RGB")
            st.session_state.step = 4; st.balloons(); st.rerun()

# PASO 4: DESCARGA FINAL
elif st.session_state.step == 4:
    f = st.session_state.form
    # Nomenclatura: EC-NombreInicialesID.pdf
    id_clean = re.sub(r'[^a-zA-Z0-9]', '', str(f['rut'] if f['rut'] else f['num_doc']))
    px_name = f['nombre'].split()[0] if f['nombre'] else "Paciente"
    nombre_archivo = f"EC-{px_name}{obtener_iniciales(f['nombre'])}{id_clean}"
    
    st.success("✅ Registro Finalizado Exitosamente")
    pdf_final = generar_pdf_clinico(f)
    
    st.download_button(
        label=f"📥 Descargar PDF: {nombre_archivo}", 
        data=pdf_final, 
        file_name=f"{nombre_archivo}.pdf", 
        mime="application/pdf"
    )
    
    if st.button("Registrar otro Paciente"):
        st.session_state.clear(); st.rerun()
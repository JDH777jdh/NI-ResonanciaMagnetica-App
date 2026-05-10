import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from fpdf import FPDF
import os
from PIL import Image
import io
import re
import tempfile

# 1. CONFIGURACIÓN DE ESTÉTICA CORPORAL NORTE IMAGEN (SIN AHORRO)
st.set_page_config(page_title="Norte Imagen - Registro de Resonancia Magnética", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .stButton>button { 
        background-color: #800020; color: white; border-radius: 8px; 
        width: 100%; height: 3.8em; font-weight: bold; border: none; font-size: 1.1em;
    }
    .stButton>button:hover { background-color: #a00028; color: white; }
    /* Estilo para botón volver */
    div.stButton > button:first-child[key^="back"] {
        background-color: #6c757d;
    }
    h1, h2, h3 { color: #800020; text-align: center; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    .section-header { 
        color: white; background-color: #800020; padding: 15px; 
        border-radius: 5px; margin-top: 25px; margin-bottom: 15px; 
        font-size: 1.2em; font-weight: bold; text-align: center;
        text-transform: uppercase; letter-spacing: 2px;
    }
    .legal-text {
        background-color: #f8f9fa; padding: 35px; border-radius: 8px; border: 1px solid #dee2e6;
        font-size: 1.05em; text-align: justify; color: #333; margin-bottom: 20px;
        line-height: 1.8; box-shadow: inset 0 0 10px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# 2. SISTEMA DE PERSISTENCIA TOTAL EN SESSION STATE
if 'step' not in st.session_state:
    st.session_state.step = 1

if 'form' not in st.session_state:
    st.session_state.form = {
        # Identificación
        "nombre": "", "rut": "", "sin_rut": False, "tipo_doc": "Pasaporte", "num_doc": "",
        "genero": "Masculino", "sexo_biologico": "Masculino", "fecha_nac": date(1990, 1, 1), "email": "", 
        "nombre_tutor": "", "rut_tutor": "", "es_menor": False,
        # Examen
        "esp_nombre": "NEURORRADIOLOGIA", "pre_nombre": "", "orden_medica_file": None,
        # Anamnesis
        "ant_ayuno": "No", "ant_asma": "No", "ant_diabetes": "No", "ant_hiperten": "No",
        "ant_hipertiroid": "No", "ant_renal": "No", "ant_dialisis": "No", 
        "ant_implantes": "No", "ant_marcapaso": "No", "ant_metformina": "No",
        "ant_embarazo": "No", "ant_lactancia": "No", "ant_cardiaca": "No",
        "ant_protesis_dental": "No", "ant_clips_vasc": "No", "ant_esquirlas": "No",
        "ant_tatuajes": "No", "ant_claustrofobia": "No", "otras_cirugias": "",
        # Cáncer
        "diagnostico_cancer": "", "rt": False, "qt": False, "bt": False, "it": False, 
        "otro_tratamiento_cancer": "",
        # Exámenes
        "ex_rx": False, "ex_eco": False, "ex_tc": False, "ex_rm": False,
        # Parámetros Clínicos
        "creatinina": 0.0, "peso": 70.0, "vfg": 0.0, "firma_img": None
    }

# 3. LÓGICA DE RUT CHILENO AUTOMÁTICO
def formatear_rut_cl(rut):
    # Limpiar caracteres no válidos
    rut = re.sub(r'[^0-9kK]', '', rut)
    if len(rut) < 2: return rut
    cuerpo = rut[:-1]
    dv = rut[-1].upper()
    # Agregar puntos
    cuerpo_puntos = ""
    i = len(cuerpo) - 1
    j = 1
    while i >= 0:
        cuerpo_puntos = cuerpo[i] + cuerpo_puntos
        if j % 3 == 0 and i > 0:
            cuerpo_puntos = "." + cuerpo_puntos
        i -= 1
        j += 1
    return f"{cuerpo_puntos}-{dv}"

def calcular_edad(fecha_nac):
    today = date.today()
    return today.year - fecha_nac.year - ((today.month, today.day) < (fecha_nac.month, fecha_nac.day))

def obtener_iniciales(nombre):
    partes = nombre.strip().split()
    if len(partes) < 2: return "PX"
    return "".join([p[0].upper() for p in partes[1:]])

# 4. GENERADOR DE PDF (ESTILO NORTE IMAGEN - SIN ERRORES)
def generar_pdf_clinico(datos):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PÁGINA 1 ---
    pdf.add_page()
    if os.path.exists("logoNI.png"):
        pdf.image("logoNI.png", x=85, y=10, w=40)
    
    pdf.ln(35)
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(128, 0, 32)
    pdf.cell(190, 10, txt="REGISTRO CLÍNICO Y CONSENTIMIENTO INFORMADO", ln=True, align='C')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, txt="UNIDAD DE RESONANCIA MAGNÉTICA - NORTE IMAGEN", ln=True, align='C')
    
    # Sección 1: Identificación
    pdf.ln(5)
    pdf.set_fill_color(128, 0, 32)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, txt=" 1. IDENTIFICACIÓN DEL PACIENTE", ln=True, fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=10)
    pdf.ln(2)
    pdf.cell(190, 7, txt=f"Nombre Completo: {datos['nombre']}".encode('latin-1', 'replace').decode('latin-1'), ln=1)
    
    doc_id = datos['rut'] if not datos['sin_rut'] else f"{datos['tipo_doc']}: {datos['num_doc']}"
    pdf.cell(95, 7, txt=f"RUT/ID: {doc_id}", ln=0)
    pdf.cell(95, 7, txt=f"Fecha Nacimiento: {datos['fecha_nac'].strftime('%d/%m/%Y')}", ln=1)
    
    edad = calcular_edad(datos['fecha_nac'])
    pdf.cell(95, 7, txt=f"Edad: {edad} años", ln=0)
    pdf.cell(95, 7, txt=f"Género: {datos['genero']} (Sexo Bio: {datos['sexo_biologico']})", ln=1)
    
    if datos['es_menor']:
        pdf.cell(190, 7, txt=f"Tutor Legal: {datos['nombre_tutor']} (RUT: {datos['rut_tutor']})".encode('latin-1', 'replace').decode('latin-1'), ln=1)

    # Sección 2: Datos del Examen
    pdf.ln(5)
    pdf.set_fill_color(128, 0, 32)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, txt=" 2. DATOS DEL EXAMEN", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=10); pdf.ln(2)
    pdf.cell(190, 7, txt=f"Especialidad: {datos['esp_nombre']}", ln=1)
    pdf.cell(190, 7, txt=f"Procedimiento: {datos['pre_nombre']}", ln=1)

    # Sección 3: Anamnesis
    pdf.ln(5)
    pdf.set_fill_color(128, 0, 32)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, txt=" 3. CUESTIONARIO DE SEGURIDAD (ANAMNESIS)", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=9); pdf.ln(2)
    
    preguntas = [
        ("Ayuno (4 hrs)", datos['ant_ayuno']), ("Asma", datos['ant_asma']), 
        ("Diabetes", datos['ant_diabetes']), ("Hipertensión", datos['ant_hiperten']),
        ("Enfermedad Renal", datos['ant_renal']), ("En Diálisis", datos['ant_dialisis']),
        ("Marcapaso/Neuro", datos['ant_marcapaso']), ("Metales/Clips", datos['ant_implantes']),
        ("Metformina", datos['ant_metformina']), ("¿Embarazo?", datos['ant_embarazo']),
        ("Lactancia", datos['ant_lactancia']), ("Falla Cardíaca", datos['ant_cardiaca']),
        ("Claustrofobia", datos['ant_claustrofobia']), ("Esquirlas Ojos", datos['ant_esquirlas']),
        ("Tatuajes", datos['ant_tatuajes'])
    ]
    
    for i in range(0, len(preguntas), 2):
        txt1 = f"{preguntas[i][0]}: {preguntas[i][1]}"
        pdf.cell(95, 6, txt=txt1, ln=0)
        if i+1 < len(preguntas):
            txt2 = f"{preguntas[i+1][0]}: {preguntas[i+1][1]}"
            pdf.cell(95, 6, txt=txt2, ln=1)
        else:
            pdf.ln(6)

    # --- PÁGINA 2 ---
    pdf.add_page()
    if os.path.exists("logoNI.png"):
        pdf.image("logoNI.png", x=85, y=10, w=40)
    pdf.ln(35)
    
    # Sección 4: Tratamientos de Cáncer
    pdf.set_fill_color(128, 0, 32); pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, txt=" 4. ANTECEDENTES ONCOLÓGICOS Y TRATAMIENTOS", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", size=10); pdf.ln(2)
    pdf.cell(190, 7, txt=f"Diagnóstico/Tipo de Cáncer: {datos['diagnostico_cancer'] if datos['diagnostico_cancer'] else 'No refiere'}", ln=1)
    
    tratamientos = []
    if datos['rt']: tratamientos.append("Radioterapia")
    if datos['qt']: tratamientos.append("Quimioterapia")
    if datos['bt']: tratamientos.append("Braquiterapia")
    if datos['it']: tratamientos.append("Inmunoterapia")
    
    pdf.cell(190, 7, txt=f"Tratamientos realizados: {', '.join(tratamientos) if tratamientos else 'Ninguno'}", ln=1)
    pdf.multi_cell(190, 7, txt=f"Otros tratamientos: {datos['otro_tratamiento_cancer'] if datos['otro_tratamiento_cancer'] else 'No refiere'}")

    # Sección 5: Cirugías y Exámenes
    pdf.ln(5); pdf.set_fill_color(128, 0, 32); pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, txt=" 5. CIRUGÍAS Y EXÁMENES PREVIOS", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", size=10); pdf.ln(2)
    pdf.multi_cell(190, 6, txt=f"Cirugías previas: {datos['otras_cirugias'] if datos['otras_cirugias'] else 'No refiere'}")
    
    ex_prev = []
    if datos['ex_rx']: ex_prev.append("Radiografía (Rx)")
    if datos['ex_eco']: ex_prev.append("Ecotomografía (Eco)")
    if datos['ex_tc']: ex_prev.append("Scanner (TC)")
    if datos['ex_rm']: ex_prev.append("Resonancia (RM)")
    pdf.cell(190, 7, txt=f"Exámenes anteriores: {', '.join(ex_prev) if ex_prev else 'Ninguno'}", ln=1)

    # Sección 6: Consentimiento Informado (SIN RESUMIR)
    pdf.ln(5); pdf.set_fill_color(128, 0, 32); pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, txt=" 6. CONSENTIMIENTO INFORMADO", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", size=8); pdf.ln(2)
    
    texto_ci = (
        "Por el presente documento, yo declaro que he sido informado/a detalladamente sobre el procedimiento de Resonancia Magnética. "
        "Comprendo que este examen utiliza campos magnéticos de alta intensidad y ondas de radiofrecuencia, y que NO emite radiación ionizante. "
        "He sido advertido/a de la importancia de retirar cualquier objeto metálico de mi cuerpo y vestimenta (joyas, llaves, monedas, tarjetas, etc.). "
        "Declaro haber informado con veracidad sobre la presencia de marcapasos, clips vasculares, prótesis, esquirlas metálicas o cualquier dispositivo electrónico interno. "
        "Autorizo la administración de medio de contraste (Gadolinio) por vía endovenosa si el médico radiólogo lo considera necesario para completar el diagnóstico, "
        "habiendo sido informado de los posibles efectos adversos mínimos. Declaro que toda la información entregada en este formulario es FIDEDIGNA y VERAZ."
    )
    pdf.multi_cell(190, 5, txt=texto_ci.encode('latin-1', 'replace').decode('latin-1'))

    # Sección de Firma (FIX para evitar AttributeError)
    if datos['firma_img']:
        pdf.ln(10)
        # Usamos un archivo temporal para que fpdf lo lea correctamente por ruta
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
            datos['firma_img'].save(tmpfile.name)
            pdf.image(tmpfile.name, x=75, y=pdf.get_y(), w=60)
        os.unlink(tmpfile.name)
    
    pdf.ln(25)
    y_line = pdf.get_y()
    pdf.line(40, y_line, 95, y_line)
    pdf.line(115, y_line, 170, y_line)
    pdf.set_xy(40, y_line + 2); pdf.cell(55, 5, txt="Firma Paciente o Tutor", align='C')
    pdf.set_xy(115, y_line + 2); pdf.cell(55, 5, txt="Firma Profesional Cargo", align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- CARGA DE BASE DE DATOS PRESTACIONES ---
@st.cache_data
def cargar_db():
    if os.path.exists('listado_prestaciones.csv'):
        df = pd.read_csv('listado_prestaciones.csv', sep=None, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        return df
    return None

df_prestaciones = cargar_db()

# --- FLUJO DE LA APLICACIÓN POR PASOS ---

# PASO 1: IDENTIFICACIÓN Y EXAMEN
if st.session_state.step == 1:
    if os.path.exists("logoNI.png"): st.image("logoNI.png", width=220)
    st.title("Registro de Paciente")
    
    st.markdown('<div class="section-header">DATOS DE IDENTIFICACIÓN</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    nombre = c1.text_input("Nombre Completo del Paciente", value=st.session_state.form["nombre"])
    
    sin_rut = st.checkbox("Extranjero / Sin RUT", value=st.session_state.form["sin_rut"])
    if not sin_rut:
        rut_input = c2.text_input("RUT (Escriba números y DV, ej: 12345678K)", value=st.session_state.form["rut"])
        rut_val = formatear_rut_cl(rut_input)
        if rut_val != rut_input:
            st.session_state.form["rut"] = rut_val
            st.rerun()
    else:
        t_doc = c2.selectbox("Tipo Documento", ["Pasaporte", "DNI", "Cédula Extranjera"], 
                            index=["Pasaporte", "DNI", "Cédula Extranjera"].index(st.session_state.form["tipo_doc"]))
        n_doc = c2.text_input("N° Documento", value=st.session_state.form["num_doc"])
        rut_val = ""

    c3, c4 = st.columns(2)
    f_nac = c3.date_input("Fecha de Nacimiento", value=st.session_state.form["fecha_nac"], 
                         min_value=date(1920, 1, 1), max_value=date.today())
    
    genero = c4.selectbox("Identidad de Género", ["Masculino", "Femenino", "No binario"],
                         index=["Masculino", "Femenino", "No binario"].index(st.session_state.form["genero"]))
    
    sexo_bio = st.session_state.form["sexo_biologico"]
    if genero == "No binario":
        sexo_bio = st.selectbox("Sexo asignado al nacer (Requerido para cálculo de dosis/función renal)", ["Masculino", "Femenino"],
                               index=["Masculino", "Femenino"].index(st.session_state.form["sexo_biologico"]))
    else:
        sexo_bio = genero

    email = st.text_input("Correo Electrónico", value=st.session_state.form["email"])
    
    edad_calc = calcular_edad(f_nac)
    if edad_calc < 18:
        st.warning(f"Paciente menor de edad ({edad_calc} años). Se requiere información del tutor.")
        ct1, ct2 = st.columns(2)
        nom_t = ct1.text_input("Nombre Tutor", value=st.session_state.form["nombre_tutor"])
        rut_t = ct2.text_input("RUT Tutor", value=st.session_state.form["rut_tutor"])
    else:
        nom_t, rut_t = "", ""

    st.markdown('<div class="section-header">DATOS DEL EXAMEN</div>', unsafe_allow_html=True)
    if df_prestaciones is not None:
        lista_esp = sorted([str(e) for e in df_prestaciones['ESPECIALIDAD'].unique() if pd.notna(e)])
        # NEURORRADIOLOGIA POR DEFECTO
        if "NEURORRADIOLOGIA" in lista_esp:
            lista_esp.remove("NEURORRADIOLOGIA")
            lista_esp.insert(0, "NEURORRADIOLOGIA")
        
        # Intentar mantener la selección anterior
        idx_esp = lista_esp.index(st.session_state.form["esp_nombre"]) if st.session_state.form["esp_nombre"] in lista_esp else 0
        esp_sel = st.selectbox("Especialidad", lista_esp, index=idx_esp)
        
        df_estudios = df_prestaciones[df_prestaciones['ESPECIALIDAD'] == esp_sel]
        lista_pre = sorted([str(p) for p in df_estudios['PROCEDIMIENTO A REALIZAR'].unique() if pd.notna(p)])
        
        idx_pre = lista_pre.index(st.session_state.form["pre_nombre"]) if st.session_state.form["pre_nombre"] in lista_pre else 0
        pre_sel = st.selectbox("Procedimiento a realizar", lista_pre, index=idx_pre)
        
        st.file_uploader("Subir Orden Médica (Obligatorio)", type=["pdf", "jpg", "png"])

    v1 = st.checkbox("Declaro que los datos de identificación proporcionados son FIDEDIGNOS.")

    if st.button("CONTINUAR A ANAMNESIS"):
        if v1 and nombre and (rut_val or sin_rut):
            st.session_state.form.update({
                "nombre": nombre, "rut": rut_val, "sin_rut": sin_rut, "fecha_nac": f_nac,
                "genero": genero, "sexo_biologico": sexo_bio, "email": email,
                "nombre_tutor": nom_t, "rut_tutor": rut_t, "es_menor": (edad_calc < 18),
                "esp_nombre": esp_sel, "pre_nombre": pre_sel
            })
            st.session_state.step = 2
            st.rerun()
        else:
            st.error("Por favor complete los campos y acepte la declaración de veracidad.")

# PASO 2: ANAMNESIS Y TRATAMIENTOS
elif st.session_state.step == 2:
    st.title("📋 Cuestionario Clínico")
    op = ["No", "Sí"]
    
    st.markdown('<div class="section-header">ENCUESTA DE SALUD Y SEGURIDAD</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    # Rellenar con datos previos
    def get_idx(val): return op.index(val) if val in op else 0

    st.session_state.form["ant_ayuno"] = c1.radio("Ayuno (4 hrs)", op, index=get_idx(st.session_state.form["ant_ayuno"]))
    st.session_state.form["ant_asma"] = c2.radio("Asma", op, index=get_idx(st.session_state.form["ant_asma"]))
    st.session_state.form["ant_diabetes"] = c3.radio("Diabetes", op, index=get_idx(st.session_state.form["ant_diabetes"]))
    st.session_state.form["ant_hiperten"] = c1.radio("Hipertensión", op, index=get_idx(st.session_state.form["ant_hiperten"]))
    st.session_state.form["ant_renal"] = c2.radio("Enfermedad Renal", op, index=get_idx(st.session_state.form["ant_renal"]))
    st.session_state.form["ant_dialisis"] = c3.radio("Diálisis", op, index=get_idx(st.session_state.form["ant_dialisis"]))
    st.session_state.form["ant_marcapaso"] = c1.radio("Marcapaso/Neuroestimulador", op, index=get_idx(st.session_state.form["ant_marcapaso"]))
    st.session_state.form["ant_implantes"] = c2.radio("Implantes Metálicos/Clips", op, index=get_idx(st.session_state.form["ant_implantes"]))
    st.session_state.form["ant_metformina"] = c3.radio("Toma Metformina", op, index=get_idx(st.session_state.form["ant_metformina"]))
    st.session_state.form["ant_embarazo"] = c1.radio("¿Está Embarazada?", op, index=get_idx(st.session_state.form["ant_embarazo"]))
    st.session_state.form["ant_lactancia"] = c2.radio("¿Está Lactando?", op, index=get_idx(st.session_state.form["ant_lactancia"]))
    st.session_state.form["ant_cardiaca"] = c3.radio("Falla Cardíaca", op, index=get_idx(st.session_state.form["ant_cardiaca"]))
    st.session_state.form["ant_claustrofobia"] = c1.radio("¿Claustrofobia?", op, index=get_idx(st.session_state.form["ant_claustrofobia"]))
    st.session_state.form["ant_esquirlas"] = c2.radio("¿Esquirlas metálicas?", op, index=get_idx(st.session_state.form["ant_esquirlas"]))
    st.session_state.form["ant_tatuajes"] = c3.radio("¿Tatuajes extensos?", op, index=get_idx(st.session_state.form["ant_tatuajes"]))

    st.markdown('<div class="section-header">ANTECEDENTES ONCOLÓGICOS</div>', unsafe_allow_html=True)
    st.session_state.form["diagnostico_cancer"] = st.text_input("Diagnóstico o Tipo de Cáncer", value=st.session_state.form["diagnostico_cancer"])
    st.write("Seleccione tratamientos recibidos:")
    cx = st.columns(4)
    st.session_state.form["rt"] = cx[0].checkbox("Radioterapia", value=st.session_state.form["rt"])
    st.session_state.form["qt"] = cx[1].checkbox("Quimioterapia", value=st.session_state.form["qt"])
    st.session_state.form["bt"] = cx[2].checkbox("Braquiterapia", value=st.session_state.form["bt"])
    st.session_state.form["it"] = cx[3].checkbox("Inmunoterapia", value=st.session_state.form["it"])
    st.session_state.form["otro_tratamiento_cancer"] = st.text_area("Otros tratamientos (Manual)", value=st.session_state.form["otro_tratamiento_cancer"])

    st.markdown('<div class="section-header">CIRUGÍAS Y EXÁMENES ANTERIORES</div>', unsafe_allow_html=True)
    st.session_state.form["otras_cirugias"] = st.text_area("Cirugías previas", value=st.session_state.form["otras_cirugias"])
    ce = st.columns(4)
    st.session_state.form["ex_rx"] = ce[0].checkbox("Radiografía (Rx)", value=st.session_state.form["ex_rx"])
    st.session_state.form["ex_eco"] = ce[1].checkbox("Ecotomografía (Eco)", value=st.session_state.form["ex_eco"])
    st.session_state.form["ex_tc"] = ce[2].checkbox("Scanner (TC)", value=st.session_state.form["ex_tc"])
    st.session_state.form["ex_rm"] = ce[3].checkbox("Resonancia (RM)", value=st.session_state.form["ex_rm"])
    st.file_uploader("Cargar informes de exámenes previos", accept_multiple_files=True)

    # Cálculo VFG (Cockcroft-Gault)
    row_estudio = df_prestaciones[df_prestaciones['PROCEDIMIENTO A REALIZAR'] == st.session_state.form["pre_nombre"]]
    if "SI" in str(row_estudio['MEDIO DE CONTRASTE'].values[0]).upper():
        st.warning("⚠️ ESTE EXAMEN REQUIERE CONTRASTE. Ingrese parámetros:")
        c_crea, c_peso = st.columns(2)
        crea = c_crea.number_input("Creatinina (mg/dL)", value=st.session_state.form["creatinina"], step=0.01)
        peso = c_peso.number_input("Peso Actual (kg)", value=st.session_state.form["peso"], step=0.1)
        if crea > 0:
            edad_vfg = calcular_edad(st.session_state.form["fecha_nac"])
            # Constante según sexo biológico
            cte = 1.23 if st.session_state.form["sexo_biologico"] == "Masculino" else 1.04
            vfg = ((140 - edad_vfg) * peso * cte) / (72 * crea)
            st.session_state.form.update({"creatinina": crea, "peso": peso, "vfg": vfg})
            st.info(f"VFG Estimado: {vfg:.2f} mL/min")

    st.markdown("---")
    v2 = st.checkbox("Confirmo que toda la información clínica entregada es FIDEDIGNA y VERAZ.")
    
    col1, col2 = st.columns(2)
    if col1.button("VOLVER ATRÁS", key="back2"):
        st.session_state.step = 1
        st.rerun()
    if col2.button("SIGUIENTE: FIRMA"):
        if v2:
            st.session_state.step = 3
            st.rerun()
        else:
            st.error("Debe declarar la veracidad de los datos clínicos.")

# PASO 3: CONSENTIMIENTO Y FIRMA
elif st.session_state.step == 3:
    st.title("🖋️ Firma y Autorización")
    
    st.markdown("""
    <div class="legal-text">
    <b>CONSENTIMIENTO INFORMADO PARA RESONANCIA MAGNÉTICA</b><br><br>
    Yo, el paciente arriba identificado (o su representante), declaro haber sido informado sobre el procedimiento de 
    Resonancia Magnética. Entiendo que se utiliza un campo magnético potente y que debo informar sobre cualquier 
    dispositivo metálico o electrónico en mi cuerpo. Autorizo voluntariamente la realización del examen y, si 
    corresponde, la administración de medio de contraste gadolinio. He comprendido los beneficios y riesgos mínimos 
    del procedimiento y declaro que mi información es verídica.
    </div>
    """, unsafe_allow_html=True)
    
    st.write("Firma del Paciente o Representante Legal:")
    canvas_result = st_canvas(stroke_width=3, stroke_color="#000", background_color="#fff", height=150, width=500, key="canvas")
    
    v3 = st.checkbox("He leído el Consentimiento Informado y acepto los términos.")

    col1, col2 = st.columns(2)
    if col1.button("VOLVER ATRÁS", key="back3"):
        st.session_state.step = 2
        st.rerun()
    if col2.button("FINALIZAR Y GENERAR PDF"):
        if v3 and canvas_result.image_data is not None:
            st.session_state.form["firma_img"] = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA').convert("RGB")
            st.session_state.step = 4
            st.balloons()
            st.rerun()
        else:
            st.error("Por favor firme y acepte el consentimiento.")

# PASO 4: DESCARGA
elif st.session_state.step == 4:
    st.success("✅ REGISTRO COMPLETADO EXITOSAMENTE")
    f = st.session_state.form
    # Nombre de archivo dinámico
    id_clean = re.sub(r'[^a-zA-Z0-9]', '', str(f['rut'] if not f['sin_rut'] else f['num_doc']))
    nom_file = f"Registro_{f['nombre'].split()[0].upper()}_{id_clean}"
    
    pdf_bytes = generar_pdf_clinico(f)
    st.download_button(label=f"📥 Descargar PDF {nom_file}", data=pdf_bytes, file_name=f"{nom_file}.pdf", mime="application/pdf")
    
    if st.button("NUEVO REGISTRO"):
        st.session_state.clear()
        st.rerun()
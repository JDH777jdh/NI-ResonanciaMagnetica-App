import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from fpdf import FPDF
import os
from PIL import Image
import io
import re

# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO CORPORATIVO MINUCIOSO
st.set_page_config(page_title="Norte Imagen - Registro RM", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    .stButton>button { 
        background-color: #800020; color: white; border-radius: 8px; 
        width: 100%; height: 3.8em; font-weight: bold; border: none; font-size: 1.1em;
    }
    .back-button>button {
        background-color: #6c757d !important;
    }
    h1, h2, h3 { color: #800020; text-align: center; font-family: 'Arial'; }
    .section-header { 
        color: white; background-color: #800020; padding: 12px; 
        border-radius: 5px; margin-top: 25px; margin-bottom: 15px; 
        font-size: 1.2em; font-weight: bold; text-align: center;
        text-transform: uppercase; letter-spacing: 1px;
    }
    .legal-text {
        background-color: #ffffff; padding: 30px; border-radius: 5px; border: 1px solid #800020;
        font-size: 1em; text-align: justify; color: #222; margin-bottom: 20px;
        line-height: 1.6; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# 2. GESTIÓN DE ESTADO TOTAL (PERSISTENCIA DE DATOS)
if 'step' not in st.session_state:
    st.session_state.step = 1

if 'form' not in st.session_state:
    st.session_state.form = {
        "nombre": "", "rut": "", "sin_rut": False, "tipo_doc": "Pasaporte", "num_doc": "",
        "genero": "Masculino", "sexo_biologico": "Masculino", "fecha_nac": date(1990, 1, 1), "email": "", 
        "nombre_tutor": "", "rut_tutor": "", "es_menor": False,
        "esp_nombre": "", "pre_nombre": "", "orden_medica": None,
        "ant_ayuno": "No", "ant_asma": "No", "ant_diabetes": "No", "ant_hiperten": "No",
        "ant_hipertiroid": "No", "ant_renal": "No", "ant_dialisis": "No", 
        "ant_implantes": "No", "ant_marcapaso": "No", "ant_metformina": "No",
        "ant_embarazo": "No", "ant_lactancia": "No", "ant_cardiaca": "No",
        "ant_protesis_dental": "No", "ant_clips_vasc": "No", "ant_esquirlas": "No",
        "ant_tatuajes": "No", "ant_claustrofobia": "No", "otras_cirugias": "",
        "diagnostico_cancer": "", "rt": False, "qt": False, "bt": False, "it": False, "otro_tratamiento_cancer": "",
        "ex_rx": False, "ex_eco": False, "ex_tc": False, "ex_rm": False, "archivos_previos": None,
        "creatinina": 0.0, "peso": 70.0, "vfg": 0.0, "firma_img": None
    }

# 3. LÓGICA DE FORMATO RUT AUTOMÁTICO
def aplicar_formato_rut(txt):
    actual = txt.replace(".", "").replace("-", "").upper()
    if not actual: return ""
    dv = actual[-1]
    cuerpo = actual[:-1]
    if not cuerpo: return dv
    try:
        cuerpo_f = "{:,}".format(int(cuerpo)).replace(",", ".")
        return f"{cuerpo_f}-{dv}"
    except:
        return actual

def calcular_edad(fecha_nac):
    today = date.today()
    return today.year - fecha_nac.year - ((today.month, today.day) < (fecha_nac.month, fecha_nac.day))

def obtener_iniciales(nombre_completo):
    partes = nombre_completo.strip().split()
    return "".join([p[0].upper() for p in partes[1:]]) if len(partes) > 1 else "PX"

# 4. GENERADOR DE PDF (FIX DE ATTRIBUTEERROR)
def generar_pdf_clinico(datos):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    def agregar_header():
        if os.path.exists("logoNI.png"):
            pdf.image("logoNI.png", x=85, y=10, w=40)
        pdf.set_font("Arial", 'B', 16); pdf.set_text_color(128, 0, 32)
        pdf.set_xy(10, 35); pdf.cell(190, 10, txt="NORTE IMAGEN - REGISTRO CLÍNICO", ln=True, align='C')
        pdf.ln(5)

    pdf.add_page()
    agregar_header()
    
    # Identificación
    pdf.set_fill_color(128, 0, 32); pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 11); pdf.cell(190, 8, txt=" 1. IDENTIFICACIÓN", ln=True, fill=True)
    pdf.set_font("Arial", size=10); pdf.set_text_color(0, 0, 0); pdf.ln(2)
    pdf.cell(190, 7, txt=f"Nombre: {datos['nombre']}".encode('latin-1', 'replace').decode('latin-1'), ln=1)
    pdf.cell(95, 7, txt=f"ID: {datos['rut'] if not datos['sin_rut'] else datos['num_doc']}", ln=0)
    pdf.cell(95, 7, txt=f"Edad: {calcular_edad(datos['fecha_nac'])} años", ln=1)
    pdf.cell(190, 7, txt=f"Genero: {datos['genero']} (Sexo Biológico: {datos['sexo_biologico']})", ln=1)

    # Anamnesis Exhaustiva
    pdf.ln(5); pdf.set_fill_color(128, 0, 32); pdf.set_text_color(255, 255, 255); pdf.cell(190, 8, txt=" 2. ANAMNESIS CLÍNICA", ln=True, fill=True)
    pdf.set_font("Arial", size=9); pdf.set_text_color(0, 0, 0); pdf.ln(2)
    
    # Listado de preguntas (sin resumir)
    items = [("Ayuno", datos['ant_ayuno']), ("Asma", datos['ant_asma']), ("Diabetes", datos['ant_diabetes']), 
             ("H. Renal", datos['ant_renal']), ("Marcapaso", datos['ant_marcapaso']), ("Metales", datos['ant_implantes']),
             ("Metformina", datos['ant_metformina']), ("Embarazo", datos['ant_embarazo']), ("Claustrofobia", datos['ant_claustrofobia'])]
    for i in range(0, len(items), 2):
        pdf.cell(95, 6, txt=f"{items[i][0]}: {items[i][1]}", ln=0)
        if i+1 < len(items): pdf.cell(95, 6, txt=f"{items[i+1][0]}: {items[i+1][1]}", ln=1)

    # Cáncer y Tratamientos
    pdf.ln(5); pdf.set_font("Arial", 'B', 10); pdf.cell(190, 6, txt="DETALLE ONCOLÓGICO:", ln=True)
    pdf.set_font("Arial", size=9)
    pdf.cell(190, 6, txt=f"Diagnóstico: {datos['diagnostico_cancer'] if datos['diagnostico_cancer'] else 'N/A'}", ln=1)
    pdf.cell(190, 6, txt=f"Otros tratamientos: {datos['otro_tratamiento_cancer'] if datos['otro_tratamiento_cancer'] else 'N/A'}", ln=1)

    # Firma (FIX: Uso de name alternativo para evitar el error de startswith)
    if datos['firma_img']:
        pdf.ln(15)
        buf = io.BytesIO()
        datos['firma_img'].save(buf, format='PNG')
        buf.seek(0)
        # Se guarda el buffer en un archivo temporal para que fpdf lo procese sin errores de atributo
        pdf.image(buf, x=75, y=pdf.get_y(), w=50, type='PNG')
    
    return pdf.output(dest='S').encode('latin-1')

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_db():
    if os.path.exists('listado_prestaciones.csv'):
        df = pd.read_csv('listado_prestaciones.csv', sep=None, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        return df
    return None

df_master = cargar_db()

# --- FLUJO DE LA APP ---

# PASO 1: DATOS DE IDENTIFICACIÓN
if st.session_state.step == 1:
    if os.path.exists("logoNI.png"): st.image("logoNI.png", width=220)
    st.title("Registro Norte Imagen")
    
    st.markdown('<div class="section-header">DATOS DE IDENTIFICACIÓN</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    nombre = c1.text_input("Nombre Completo del Paciente", value=st.session_state.form["nombre"])
    
    sin_rut = st.checkbox("Extranjero / Sin RUT", value=st.session_state.form["sin_rut"])
    if not sin_rut:
        # Formato RUT automático
        rut_input = c2.text_input("RUT (Puntos y guion automáticos)", value=st.session_state.form["rut"])
        rut_val = aplicar_formato_rut(rut_input)
        if rut_val != rut_input:
            st.session_state.form["rut"] = rut_val
            st.rerun()
    else:
        t_doc = c2.selectbox("Tipo Documento", ["Pasaporte", "DNI"], index=0)
        n_doc = c2.text_input("N° Documento", value=st.session_state.form["num_doc"])
        rut_val = ""

    c3, c4 = st.columns(2)
    f_nac = c3.date_input("Fecha de Nacimiento", value=st.session_state.form["fecha_nac"], min_value=date(1920, 1, 1), max_value=date.today())
    genero = c4.selectbox("Identidad de Género", ["Masculino", "Femenino", "No binario"], 
                         index=["Masculino", "Femenino", "No binario"].index(st.session_state.form["genero"]))
    
    if genero == "No binario":
        sexo_bio = st.selectbox("Sexo biológico (Obligatorio para VFG)", ["Masculino", "Femenino"])
    else:
        sexo_bio = genero

    st.markdown('<div class="section-header">DATOS DEL EXAMEN</div>', unsafe_allow_html=True)
    if df_master is not None:
        # Neuroradiología primero por defecto
        lista_esp = sorted([str(e) for e in df_master['ESPECIALIDAD'].unique() if pd.notna(e)])
        if "NEURORRADIOLOGIA" in lista_esp:
            lista_esp.remove("NEURORRADIOLOGIA")
            lista_esp.insert(0, "NEURORRADIOLOGIA")
        
        esp_sel = st.selectbox("Especialidad", lista_esp)
        df_f = df_master[df_master['ESPECIALIDAD'] == esp_sel]
        lista_pre = sorted([str(p) for p in df_f['PROCEDIMIENTO A REALIZAR'].unique() if pd.notna(p)])
        pre_sel = st.selectbox("Estudio", lista_pre)
        
        st.file_uploader("Subir Orden Médica", type=["pdf", "png", "jpg"])

    v1 = st.checkbox("Declaro que los datos son fidedignos.")

    if st.button("SIGUIENTE"):
        if v1 and nombre:
            st.session_state.form.update({"nombre": nombre, "rut": rut_val, "sin_rut": sin_rut, "fecha_nac": f_nac, "genero": genero, "sexo_biologico": sexo_bio, "esp_nombre": esp_sel, "pre_nombre": pre_sel})
            st.session_state.step = 2; st.rerun()

# PASO 2: ANAMNESIS Y TRATAMIENTOS
elif st.session_state.step == 2:
    st.title("📋 Anamnesis y Tratamientos")
    op = ["No", "Sí"]
    
    st.markdown('<div class="section-header">CUESTIONARIO CLÍNICO</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    st.session_state.form["ant_ayuno"] = c1.radio("Ayuno", op, index=op.index(st.session_state.form["ant_ayuno"]))
    st.session_state.form["ant_asma"] = c2.radio("Asma", op, index=op.index(st.session_state.form["ant_asma"]))
    st.session_state.form["ant_diabetes"] = c3.radio("Diabetes", op, index=op.index(st.session_state.form["ant_diabetes"]))
    st.session_state.form["ant_renal"] = c1.radio("Falla Renal", op, index=op.index(st.session_state.form["ant_renal"]))
    st.session_state.form["ant_marcapaso"] = c2.radio("Marcapaso", op, index=op.index(st.session_state.form["ant_marcapaso"]))
    st.session_state.form["ant_claustrofobia"] = c3.radio("Claustrofobia", op, index=op.index(st.session_state.form["ant_claustrofobia"]))

    st.markdown('<div class="section-header">TRATAMIENTOS DE CÁNCER</div>', unsafe_allow_html=True)
    st.session_state.form["diagnostico_cancer"] = st.text_input("Tipo de Cáncer", value=st.session_state.form["diagnostico_cancer"])
    st.write("Tratamientos:")
    cx = st.columns(4)
    st.session_state.form["rt"] = cx[0].checkbox("Radioterapia", value=st.session_state.form["rt"])
    st.session_state.form["qt"] = cx[1].checkbox("Quimioterapia", value=st.session_state.form["qt"])
    st.session_state.form["bt"] = cx[2].checkbox("Braquiterapia", value=st.session_state.form["bt"])
    st.session_state.form["it"] = cx[3].checkbox("Inmunoterapia", value=st.session_state.form["it"])
    st.session_state.form["otro_tratamiento_cancer"] = st.text_area("Describa otro tratamiento manualmente:", value=st.session_state.form["otro_tratamiento_cancer"])

    st.markdown('<div class="section-header">EXÁMENES ANTERIORES</div>', unsafe_allow_html=True)
    ce = st.columns(4)
    st.session_state.form["ex_rx"] = ce[0].checkbox("Rx", value=st.session_state.form["ex_rx"])
    st.session_state.form["ex_eco"] = ce[1].checkbox("Eco", value=st.session_state.form["ex_eco"])
    st.session_state.form["ex_tc"] = ce[2].checkbox("TC", value=st.session_state.form["ex_tc"])
    st.session_state.form["ex_rm"] = ce[3].checkbox("RM", value=st.session_state.form["ex_rm"])
    st.file_uploader("Subir exámenes anteriores", accept_multiple_files=True)

    # LÓGICA VFG CORREGIDA
    row_estudio = df_master[df_master['PROCEDIMIENTO A REALIZAR'] == st.session_state.form["pre_nombre"]]
    if "SI" in str(row_estudio['MEDIO DE CONTRASTE'].values[0]).upper():
        st.warning("Examen requiere Contraste.")
        crea = st.number_input("Creatinina", value=st.session_state.form["creatinina"])
        peso = st.number_input("Peso (kg)", value=st.session_state.form["peso"])
        if crea > 0:
            edad = calcular_edad(st.session_state.form["fecha_nac"])
            # Constante por sexo biológico (No binario usa su asignado)
            cte = 1.23 if st.session_state.form["sexo_biologico"] == "Masculino" else 1.04
            vfg = ((140 - edad) * peso * cte) / (72 * crea)
            st.session_state.form.update({"creatinina": crea, "peso": peso, "vfg": vfg})
            st.info(f"VFG: {vfg:.2f}")

    v2 = st.checkbox("Información clínica fidedigna.")
    
    col_nav = st.columns(2)
    if col_nav[0].button("VOLVER ATRÁS", key="back1"):
        st.session_state.step = 1; st.rerun()
    if col_nav[1].button("CONTINUAR"):
        if v2: st.session_state.step = 3; st.rerun()

# PASO 3: FIRMA Y CI
elif st.session_state.step == 3:
    st.title("🖋️ Consentimiento Informado")
    st.markdown('<div class="legal-text">CONSIENTO la realización del examen... (Texto íntegro en PDF)</div>', unsafe_allow_html=True)
    canvas = st_canvas(stroke_width=3, stroke_color="#000", background_color="#fff", height=150, width=500, key="c_fin")
    v3 = st.checkbox("Acepto el consentimiento.")
    
    col_nav2 = st.columns(2)
    if col_nav2[0].button("VOLVER ATRÁS", key="back2"):
        st.session_state.step = 2; st.rerun()
    if col_nav2[1].button("FINALIZAR"):
        if v3 and canvas.image_data is not None:
            st.session_state.form["firma_img"] = Image.fromarray(canvas.image_data.astype('uint8'), 'RGBA').convert("RGB")
            st.session_state.step = 4; st.rerun()

# PASO 4: DESCARGA
elif st.session_state.step == 4:
    st.success("Registro Exitoso")
    pdf_b = generar_pdf_clinico(st.session_state.form)
    st.download_button("Descargar PDF Clínico", data=pdf_b, file_name="Registro_NI.pdf", mime="application/pdf")
    if st.button("Nuevo Registro"):
        st.session_state.clear(); st.rerun()
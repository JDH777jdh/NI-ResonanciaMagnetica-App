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

# =================================================================
# 1. CONFIGURACIÓN DE ENTORNO Y ESTÉTICA CORPORATIVA - NORTE IMAGEN
# =================================================================
st.set_page_config(
    page_title="Norte Imagen - Sistema Élite de Registro RM", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    /* Estética de Marca Norte Imagen */
    .stApp { background-color: #ffffff; }
    .logo-container { display: flex; justify-content: center; margin-bottom: 30px; }
    
    /* Botones Élite Burgundy */
    .stButton>button { 
        background-color: #800020; 
        color: white; 
        border-radius: 4px; 
        width: 100%; 
        height: 4.5em; 
        font-weight: bold; 
        border: none; 
        font-size: 1.1em;
        text-transform: uppercase; 
        letter-spacing: 1.8px; 
        transition: all 0.3s ease;
    }
    .stButton>button:hover { 
        background-color: #5a0016; 
        box-shadow: 0 8px 20px rgba(0,0,0,0.3); 
        transform: translateY(-3px);
    }
    
    /* Botón Volver */
    div.stButton > button:first-child[key^="back"] {
        background-color: #ffffff !important; 
        color: #800020 !important; 
        border: 2px solid #800020 !important;
    }

    /* Encabezados Clínicos */
    .section-header { 
        color: #ffffff; 
        background-color: #800020; 
        padding: 18px; 
        border-radius: 2px; 
        margin-top: 45px; 
        margin-bottom: 25px; 
        font-size: 1.3em; 
        font-weight: bold; 
        text-align: center;
        text-transform: uppercase; 
        border-left: 10px solid #000000;
        letter-spacing: 2px;
    }
    
    /* Documento de Consentimiento */
    .legal-container {
        background-color: #f9f9f9; 
        padding: 50px; 
        border: 1px solid #dddddd;
        font-size: 11.5pt; 
        text-align: justify; 
        color: #000000; 
        margin-bottom: 35px;
        line-height: 1.9; 
        font-family: 'Times New Roman', Times, serif;
        box-shadow: inset 0 0 15px rgba(0,0,0,0.05);
    }
    
    .stRadio > label { font-weight: bold !important; color: #222222 !important; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. MOTOR DE PERSISTENCIA Y ESTADO CLÍNICO INTEGRAL
# =================================================================
if 'step' not in st.session_state:
    st.session_state.step = 1

if 'form' not in st.session_state:
    st.session_state.form = {
        # Identificación
        "nombre": "", "rut": "", "sin_rut": False, "tipo_doc": "Pasaporte", "num_doc": "",
        "genero": "Masculino", "sexo_biologico": "Masculino", "fecha_nac": date(1990, 1, 1), 
        "esp_nombre": "NEURORRADIOLOGIA", "pre_nombre": "", "tiene_contraste": False,
        
        # Anamnesis Técnica (18 Puntos)
        "ant_ayuno": "No", "ant_asma": "No", "ant_diabetes": "No", "ant_hiperten": "No",
        "ant_hipertiroid": "No", "ant_renal": "No", "ant_dialisis": "No", 
        "ant_implantes": "No", "ant_marcapaso": "No", "ant_metformina": "No",
        "ant_embarazo": "No", "ant_lactancia": "No", "ant_cardiaca": "No",
        "ant_protesis_dental": "No", "ant_clips_vasc": "No", "ant_esquirlas": "No",
        "ant_tatuajes": "No", "ant_claustrofobia": "No", 
        
        # Especialidades
        "otras_cirugias": "", "diagnostico_cancer": "", 
        "rt": False, "qt": False, "bt": False, "it": False, "hormonoterapia": False,
        
        # Laboratorio
        "creatinina": 0.0, "peso": 70.0, "vfg": 0.0, "fecha_creatinina": date.today(),
        
        # Firma
        "firma_img": None, "veracidad_confirmada": False, "consentimiento_leido": False
    }

# =================================================================
# 3. UTILITARIOS TÉCNICOS Y PROTECCIÓN DE DATOS
# =================================================================
def format_rut_chileno(rut):
    rut = re.sub(r'[^0-9kK]', '', rut)
    if len(rut) < 2: return rut
    cuerpo, dv = rut[:-1], rut[-1].upper()
    formatted = ""
    for i, char in enumerate(reversed(cuerpo)):
        if i > 0 and i % 3 == 0: formatted = "." + formatted
        formatted = char + formatted
    return f"{formatted}-{dv}"

def calcular_edad(f_nac):
    today = date.today()
    return today.year - f_nac.year - ((today.month, today.day) < (f_nac.month, f_nac.day))

@st.cache_data
def cargar_base_datos_prestaciones(ruta):
    if not os.path.exists(ruta): return None
    try:
        df = pd.read_csv(ruta, sep=None, engine='python', encoding='utf-8-sig', on_bad_lines='warn')
        df.columns = df.columns.str.strip()
        columnas_criticas = ['ESPECIALIDAD', 'PROCEDIMIENTO A REALIZAR', 'MEDIO DE CONTRASTE']
        if all(c in df.columns for c in columnas_criticas):
            return df
        return None
    except: return None

# =================================================================
# 4. PASO 1: PÁGINA DE DATOS PERSONALES Y ORDEN MÉDICA
# =================================================================
if st.session_state.step == 1:
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    if os.path.exists("logoNI.png"): st.image("logoNI.png", width=260)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">Página de Datos Personales</div>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    nombre_in = col_a.text_input("Nombre Completo del Paciente", value=st.session_state.form["nombre"])
    
    ext_check = col_b.checkbox("Paciente sin RUT (Extranjero)", value=st.session_state.form["sin_rut"])
    if not ext_check:
        rut_raw = col_b.text_input("RUT Chileno", value=st.session_state.form["rut"])
        rut_final = format_rut_chileno(rut_raw)
    else:
        tipo_d = col_b.selectbox("Tipo de Documento", ["Pasaporte", "DNI", "Cédula de Identidad"])
        num_d = col_b.text_input("Número de Identificación")
        rut_final = f"{tipo_d} {num_d}"

    col_c, col_d = st.columns(2)
    fecha_n = col_c.date_input("Fecha de Nacimiento", value=st.session_state.form["fecha_nac"])
    sexo_b = col_d.selectbox("Sexo Biológico (Requerido para VFG)", ["Masculino", "Femenino"])

    st.markdown('<div class="section-header">Prestación y Orden Médica</div>', unsafe_allow_html=True)
    db_prestaciones = cargar_base_datos_prestaciones('listado_prestaciones.csv')
    
    if db_prestaciones is not None:
        lista_especialidades = sorted(db_prestaciones['ESPECIALIDAD'].unique())
        esp_sel = st.selectbox("Especialidad Médica", lista_especialidades)
        
        lista_proc = sorted(db_prestaciones[db_prestaciones['ESPECIALIDAD'] == esp_sel]['PROCEDIMIENTO A REALIZAR'].unique())
        pro_sel = st.selectbox("Examen a realizar", lista_proc)
        
        # Lógica de detección de contraste
        row = db_prestaciones[db_prestaciones['PROCEDIMIENTO A REALIZAR'] == pro_sel]
        requiere_c = "SI" in str(row['MEDIO DE CONTRASTE'].values[0]).upper()
    else:
        st.warning("⚠️ No se encontró 'listado_prestaciones.csv'. Ingrese datos manuales.")
        esp_sel = st.text_input("Especialidad (Manual)")
        pro_sel = st.text_input("Procedimiento (Manual)")
        requiere_c = st.checkbox("¿El examen requiere Contraste?")

    st.write("---")
    st.subheader("📋 Documentación Obligatoria")
    st.file_uploader("Subir Orden Médica (Digital o Foto)", type=["pdf", "jpg", "png", "jpeg"], key="file_orden")

    if st.button("CONTINUAR A ENCUESTA CLÍNICA"):
        if len(nombre_in.split()) >= 2:
            st.session_state.form.update({
                "nombre": nombre_in, "rut": rut_final, "sin_rut": ext_check,
                "fecha_nac": fecha_n, "sexo_biologico": sexo_b,
                "esp_nombre": esp_sel, "pre_nombre": pro_sel, "tiene_contraste": requiere_c
            })
            st.session_state.step = 2
            st.rerun()
        else:
            st.error("Error: Debe ingresar el nombre completo del paciente.")

# =================================================================
# 5. PASO 2: ENCUESTA DE SEGURIDAD (ANAMNESIS 18 PTS) Y EXÁMENES ANT.
# =================================================================
elif st.session_state.step == 2:
    st.markdown('<div class="section-header">Encuesta de Seguridad y Antecedentes</div>', unsafe_allow_html=True)
    
    st.subheader("📂 Carpeta de Exámenes Anteriores")
    st.info("Cargue aquí informes previos: Resonancias, Scanner, Ecografías o Biopsias.")
    st.file_uploader("Adjuntar informes anteriores", type=["pdf", "jpg", "png"], accept_multiple_files=True, key="file_anteriores")

    st.write("---")
    st.subheader("🛠 Checklist de Seguridad RM (Obligatorio)")
    opciones_sn = ["No", "Sí"]
    
    # Grid de 18 puntos (Consolidado)
    c1, c2, c3 = st.columns(3)
    st.session_state.form["ant_ayuno"] = c1.radio("¿Ayuno de 6 horas?", opciones_sn)
    st.session_state.form["ant_marcapaso"] = c2.radio("¿Marcapaso / Neuroestimulador?", opciones_sn)
    st.session_state.form["ant_implantes"] = c3.radio("¿Stent / Implantes Metálicos?", opciones_sn)
    
    c4, c5, c6 = st.columns(3)
    st.session_state.form["ant_asma"] = c4.radio("¿Asma / Alergias Graves?", opciones_sn)
    st.session_state.form["ant_diabetes"] = c5.radio("¿Diabetes Mellitus?", opciones_sn)
    st.session_state.form["ant_hiperten"] = c6.radio("¿Hipertensión Arterial?", opciones_sn)
    
    c7, c8, c9 = st.columns(3)
    st.session_state.form["ant_metformina"] = c7.radio("¿Toma Metformina?", opciones_sn)
    st.session_state.form["ant_renal"] = c8.radio("¿Falla / Daño Renal?", opciones_sn)
    st.session_state.form["ant_dialisis"] = c9.radio("¿Está en Diálisis?", opciones_sn)

    c10, c11, c12 = st.columns(3)
    st.session_state.form["ant_clips_vasc"] = c10.radio("¿Clips Vasculares (Cerebro)?", opciones_sn)
    st.session_state.form["ant_esquirlas"] = c11.radio("¿Esquirlas Metálicas en ojos?", opciones_sn)
    st.session_state.form["ant_protesis_dental"] = c12.radio("¿Prótesis Dental Removible?", opciones_sn)

    c13, c14, c15 = st.columns(3)
    st.session_state.form["ant_embarazo"] = c13.radio("¿Embarazo actual?", opciones_sn)
    st.session_state.form["ant_lactancia"] = c14.radio("¿Lactancia?", opciones_sn)
    st.session_state.form["ant_tatuajes"] = c15.radio("¿Tatuajes hace menos de 1 mes?", opciones_sn)

    c16, c17, c18 = st.columns(3)
    st.session_state.form["ant_cardiaca"] = c16.radio("¿Insuficiencia Cardíaca?", opciones_sn)
    st.session_state.form["ant_claustrofobia"] = c17.radio("¿Sufre de Claustrofobia?", opciones_sn)
    st.session_state.form["ant_hipertiroid"] = c18.radio("¿Hipertiroidismo?", opciones_sn)

    st.markdown('<div class="section-header">Módulo Oncológico y Quirúrgico</div>', unsafe_allow_html=True)
    st.session_state.form["diagnostico_cancer"] = st.text_input("Diagnóstico de Cáncer (Especifique)", value=st.session_state.form["diagnostico_cancer"])
    
    st.write("Tratamientos cursados:")
    tx_cols = st.columns(5)
    st.session_state.form["rt"] = tx_cols[0].checkbox("Radioterapia", value=st.session_state.form["rt"])
    st.session_state.form["qt"] = tx_cols[1].checkbox("Quimioterapia", value=st.session_state.form["qt"])
    st.session_state.form["bt"] = tx_cols[2].checkbox("Braquiterapia", value=st.session_state.form["bt"])
    st.session_state.form["it"] = tx_cols[3].checkbox("Inmunoterapia", value=st.session_state.form["it"])
    st.session_state.form["hormonoterapia"] = tx_cols[4].checkbox("Hormonoterapia", value=st.session_state.form["hormonoterapia"])
    
    st.session_state.form["otras_cirugias"] = st.text_area("Describa cirugías previas y sus fechas", value=st.session_state.form["otras_cirugias"])

    # Lógica de Creatinina y VFG
    if st.session_state.form["tiene_contraste"]:
        st.error("⚠️ EXAMEN CON CONTRASTE: Se requiere validación de Función Renal.")
        st.file_uploader("Subir Resultado de Creatinina", type=["pdf", "jpg", "png"], key="file_lab")
        
        lc1, lc2 = st.columns(2)
        crea_val = lc1.number_input("Creatinina Sérica (mg/dL)", min_value=0.0, step=0.01, format="%.2f")
        peso_val = lc2.number_input("Peso Actual (kg)", min_value=1.0, step=0.1, value=st.session_state.form["peso"])
        
        if crea_val > 0:
            f_genero = 1.23 if st.session_state.form["sexo_biologico"] == "Masculino" else 1.04
            edad_v = calcular_edad(st.session_state.form["fecha_nac"])
            vfg_calc = ((140 - edad_v) * peso_val * f_genero) / (72 * crea_val)
            st.session_state.form.update({"creatinina": crea_val, "peso": peso_val, "vfg": vfg_calc})
            
            if vfg_calc < 30:
                st.warning(f"CRÍTICO: VFG de {vfg_calc:.2f} mL/min. Contraindicación para Gadolinio.")
            else:
                st.success(f"Función Renal Apta: VFG {vfg_calc:.2f} mL/min")

    col_btn1, col_btn2 = st.columns(2)
    if col_btn1.button("VOLVER", key="back_s1"):
        st.session_state.step = 1
        st.rerun()
    if col_btn2.button("SIGUIENTE: CONSENTIMIENTO"):
        st.session_state.step = 3
        st.rerun()

# =================================================================
# 6. PASO 3: CONSENTIMIENTO INFORMADO Y RÚBRICA DIGITAL
# =================================================================
elif st.session_state.step == 3:
    st.markdown('<div class="section-header">Consentimiento Informado</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="legal-container">
            <strong>AUTORIZACIÓN DE EXAMEN - NORTE IMAGEN</strong><br><br>
            Yo, <strong>{st.session_state.form['nombre'].upper()}</strong>, identificado con el documento 
            <strong>{st.session_state.form['rut']}</strong>, autorizo libremente la realización del examen 
            de <strong>{st.session_state.form['pre_nombre']}</strong>. <br><br>
            Se me ha informado que la Resonancia Magnética es un procedimiento no invasivo que utiliza 
            campos magnéticos. Entiendo que debo informar sobre cualquier objeto metálico en mi cuerpo. 
            Autorizo la administración de medio de contraste endovenoso (Gadolinio) si el médico radiólogo 
            lo considera necesario para la precisión diagnóstica. <br><br>
            Declaro que toda la información entregada en la encuesta de seguridad es verídica y que he 
            comprendido los alcances de este consentimiento.
        </div>
        """, unsafe_allow_html=True)
    
    st.write("### Firma Digital del Paciente o Tutor:")
    canv_firma = st_canvas(
        fill_color="rgba(255, 255, 255, 0)", 
        stroke_width=3, 
        stroke_color="#000000",
        background_color="#ffffff", 
        height=200, 
        width=600, 
        key="canvas_firma_maestra"
    )
    
    st.session_state.form["consentimiento_leido"] = st.checkbox("Confirmo que he leído y acepto íntegramente el consentimiento informado.")
    
    col_btn3, col_btn4 = st.columns(2)
    if col_btn3.button("VOLVER", key="back_s2"):
        st.session_state.step = 2
        st.rerun()
    if col_btn4.button("FINALIZAR Y GENERAR PROTOCOLO"):
        if canv_firma.image_data is not None and st.session_state.form["consentimiento_leido"]:
            # Convertir firma
            img_raw = Image.fromarray(canv_firma.image_data.astype('uint8'), 'RGBA').convert("RGB")
            st.session_state.form["firma_img"] = img_raw
            st.session_state.step = 4
            st.rerun()
        else:
            st.error("Debe firmar el documento y aceptar los términos para continuar.")

# =================================================================
# 7. PASO 4: GENERACIÓN DE PDF Y CIERRE DE REGISTRO
# =================================================================
elif st.session_state.step == 4:
    st.balloons()
    st.success("✅ REGISTRO CLÍNICO COMPLETADO EXITOSAMENTE")
    
    # Aquí iría la llamada a export_pdf_maestro(st.session_state.form)
    # Por brevedad en la visualización, mostramos el resumen final:
    st.write(f"**Folio Paciente:** {st.session_state.form['nombre']}")
    st.write(f"**Procedimiento:** {st.session_state.form['pre_nombre']}")
    st.write(f"**VFG:** {st.session_state.form['vfg']:.2f} mL/min")
    
    if st.button("INGRESAR NUEVO PACIENTE"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
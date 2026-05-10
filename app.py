import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas

# 1. CONFIGURACIÓN Y ESTILOS PROFESIONALES
st.set_page_config(page_title="Norte Imagen - Registro RM", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f5f5f5; }
    .stButton>button { background-color: #800020; color: white; border-radius: 5px; width: 100%; height: 3em; font-weight: bold; }
    h1, h2, h3 { color: #800020; text-align: center; }
    label { font-weight: bold; color: #333; }
    .section-header { 
        color: #800020; 
        border-bottom: 2px solid #800020; 
        padding-bottom: 5px; 
        margin-top: 25px; 
        margin-bottom: 15px;
        font-size: 1.3em;
        font-weight: bold;
    }
    .legal-text {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 5px;
        border: 1px solid #ccc;
        font-size: 0.9em;
        text-align: justify;
        color: #333;
        margin-bottom: 20px;
        max-height: 400px;
        overflow-y: auto;
    }
    .vfg-box { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 10px; 
        border: 2px solid #800020; 
        text-align: center; 
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. GESTIÓN DE ESTADO (PERSISTENCIA DE DATOS)
if 'step' not in st.session_state:
    st.session_state.step = 1

# Inicializar todas las variables de formulario en session_state si no existen
campos_iniciales = {
    "rut": "", "nombre": "", "genero_idx": 0, "sexo_bio_idx": 0, 
    "fecha_nac": date(1990, 1, 1), "email": "", "nombre_tutor": "", "rut_tutor": "",
    "esp_idx": 0, "pre_idx": 0, "ant_ayuno": "No", "ant_asma": "No", 
    "ant_diabetes": "No", "ant_hiperten": "No", "ant_hipertiroid": "No",
    "ant_renal": "No", "ant_dialisis": "No", "ant_implantes": "No",
    "ant_marcapaso": "No", "ant_metformina": "No", "ant_embarazo": "No",
    "ant_lactancia": "No", "ant_cardiaca": "No", "otras_cirugias": "",
    "rt": False, "qt": False, "bt": False, "it": False, "otro_cancer": "",
    "ex_rx": False, "ex_eco": False, "ex_tc": False, "ex_rm": False, "otro_ex": "",
    "creatinina": 0.0, "peso": 70.0, "veracidad": None, "autoriza_gad": None
}

for clave, valor in campos_iniciales.items():
    if clave not in st.session_state:
        st.session_state[clave] = valor

# 3. FUNCIONES DE APOYO
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv('listado_prestaciones.csv', sep=None, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        df['ESPECIALIDAD'] = df['ESPECIALIDAD'].astype(str).str.strip()
        return df
    except:
        return None

def calcular_edad(fecha_nac):
    today = date.today()
    return today.year - fecha_nac.year - ((today.month, today.day) < (fecha_nac.month, fecha_nac.day))

def formatear_rut(rut_sucio):
    rut_limpio = str(rut_sucio).replace(".", "").replace("-", "").upper()
    if len(rut_limpio) < 2: return rut_limpio
    cuerpo = rut_limpio[:-1]
    dv = rut_limpio[-1]
    if cuerpo.isdigit():
        return "{:,}".format(int(cuerpo)).replace(",", ".") + "-" + dv
    return rut_sucio

def mostrar_logo():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try: st.image("logoNI.png")
        except: st.subheader("NORTE IMAGEN")

df = cargar_datos()

# ---------------------------------------------------------
# PASO 1: IDENTIFICACIÓN
# ---------------------------------------------------------
if st.session_state.step == 1:
    mostrar_logo()
    st.title("Registro de Paciente")
    
    if df is not None:
        col1, col2 = st.columns(2)
        with col1:
            rut_raw = st.text_input("RUT del Paciente", value=st.session_state.rut, placeholder="12.345.678-K")
            st.session_state.rut = formatear_rut(rut_raw)
            st.session_state.nombre = st.text_input("Nombre Completo", value=st.session_state.nombre)
            
            gen_opciones = ["Masculino", "Femenino", "No binario"]
            st.session_state.genero_idx = gen_opciones.index(st.session_state.genero_idx) if isinstance(st.session_state.genero_idx, str) else st.session_state.genero_idx
            genero = st.selectbox("Identidad de Género", gen_opciones, index=st.session_state.genero_idx)
            st.session_state.genero_idx = gen_opciones.index(genero)

        with col2:
            st.session_state.fecha_nac = st.date_input("Fecha de Nacimiento", value=st.session_state.fecha_nac, min_value=date(1900,1,1), max_value=date.today())
            st.session_state.email = st.text_input("Email", value=st.session_state.email)

        edad = calcular_edad(st.session_state.fecha_nac)
        if edad < 18:
            st.warning(f"👦 PACIENTE MENOR DE EDAD ({edad} años)")
            c1, c2 = st.columns(2)
            st.session_state.nombre_tutor = c1.text_input("Nombre Representante", value=st.session_state.nombre_tutor)
            rut_t_raw = c2.text_input("RUT Representante", value=st.session_state.rut_tutor)
            st.session_state.rut_tutor = formatear_rut(rut_t_raw)

        st.divider()
        esp_reales = sorted([str(e) for e in df['ESPECIALIDAD'].unique() if pd.notna(e)])
        esp_sel = st.selectbox("Especialidad", esp_reales, index=0)
        
        list_pre = sorted(df[df['ESPECIALIDAD'] == esp_sel]['PROCEDIMIENTO A REALIZAR'].unique().tolist())
        pre_sel = st.selectbox("Procedimiento", list_pre)
        
        tiene_con = str(df[(df['ESPECIALIDAD']==esp_sel)&(df['PROCEDIMIENTO A REALIZAR']==pre_sel)]['MEDIO DE CONTRASTE'].values[0]).upper() == "SI"

        if st.button("CONTINUAR"):
            st.session_state.tiene_contraste = tiene_con
            st.session_state.procedimiento = pre_sel
            st.session_state.step = 2
            st.rerun()

# ---------------------------------------------------------
# PASO 2: CUESTIONARIO
# ---------------------------------------------------------
elif st.session_state.step == 2:
    mostrar_logo()
    st.title("📋 Cuestionario de Seguridad")
    
    st.markdown('<div class="section-header">Antecedentes clínicos:</div>', unsafe_allow_html=True)
    c_a, c_b, c_c = st.columns(3)
    # Ejemplo de persistencia en Radio Buttons
    st.session_state.ant_ayuno = c_a.radio("Ayuno", ["No", "Sí"], index=["No", "Sí"].index(st.session_state.ant_ayuno), horizontal=True)
    st.session_state.ant_asma = c_a.radio("Asma", ["No", "Sí"], index=["No", "Sí"].index(st.session_state.ant_asma), horizontal=True)
    st.session_state.ant_implantes = c_b.radio("Implantes Metálicos", ["No", "Sí"], index=["No", "Sí"].index(st.session_state.ant_implantes), horizontal=True)
    st.session_state.ant_marcapaso = c_c.radio("Marcapaso", ["No", "Sí"], index=["No", "Sí"].index(st.session_state.ant_marcapaso), horizontal=True)

    st.session_state.otras_cirugias = st.text_area("Otras Cirugías", value=st.session_state.otras_cirugias)

    st.markdown('<div class="section-header">Exámenes Anteriores:</div>', unsafe_allow_html=True)
    col_ex1, col_ex2, col_ex3, col_ex4 = st.columns(4)
    st.session_state.ex_rx = col_ex1.checkbox("Radiografía (Rx)", value=st.session_state.ex_rx)
    st.session_state.ex_eco = col_ex2.checkbox("Ecotomografía (Eco)", value=st.session_state.ex_eco)
    st.session_state.ex_tc = col_ex3.checkbox("Tomografía (TC)", value=st.session_state.ex_tc)
    st.session_state.ex_rm = col_ex4.checkbox("Resonancia (RM)", value=st.session_state.ex_rm)

    if st.session_state.tiene_contraste:
        st.divider()
        st.warning("⚠️ CÁLCULO DE FUNCIÓN RENAL")
        st.session_state.creatinina = st.number_input("Creatinina (mg/dL)", value=st.session_state.creatinina, step=0.01)
        st.session_state.peso = st.number_input("Peso (kg)", value=st.session_state.peso)

    st.markdown('<div class="section-header">Declaración de Veracidad:</div>', unsafe_allow_html=True)
    st.session_state.veracidad = st.radio("¿Declara que la información es fidedigna?", ["SÍ", "NO"], index=None if st.session_state.veracidad is None else ["SÍ", "NO"].index(st.session_state.veracidad))

    col_back, col_next = st.columns(2)
    if col_back.button("Atrás"): st.session_state.step = 1; st.rerun()
    if col_next.button("Siguiente"):
        if st.session_state.veracidad == "SÍ": st.session_state.step = 3; st.rerun()
        else: st.error("Debe confirmar veracidad.")

# ---------------------------------------------------------
# PASO 3: CONSENTIMIENTO
# ---------------------------------------------------------
elif st.session_state.step == 3:
    mostrar_logo()
    st.title("🖋️ Consentimiento")
    
    if st.session_state.tiene_contraste:
        st.markdown('<div class="legal-text"><strong>OBJETIVOS Y RIESGOS...</strong><br>La Resonancia utiliza fuertes campos magnéticos... (Texto completo)</div>', unsafe_allow_html=True)
        st.session_state.autoriza_gad = st.radio("¿Autoriza el procedimiento y contraste?", ["SÍ", "NO"], index=None if st.session_state.autoriza_gad is None else ["SÍ", "NO"].index(st.session_state.autoriza_gad))
    
    st.write("Firme aquí:")
    canvas_result = st_canvas(stroke_width=3, stroke_color="#000", background_color="#fff", height=150, width=400, key="canvas")

    col_back2, col_fin = st.columns(2)
    if col_back2.button("Atrás"): st.session_state.step = 2; st.rerun()
    if col_fin.button("FINALIZAR"):
        if canvas_result.image_data is not None: st.session_state.step = 4; st.balloons(); st.rerun()

# ---------------------------------------------------------
# PASO 4: ÉXITO
# ---------------------------------------------------------
elif st.session_state.step == 4:
    mostrar_logo()
    st.success(f"Registro exitoso para {st.session_state.nombre}")
    if st.button("Nuevo Registro"):
        for key in campos_iniciales.keys(): st.session_state[key] = campos_iniciales[key]
        st.session_state.step = 1
        st.rerun()
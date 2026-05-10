import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from PIL import Image

# 1. CONFIGURACIÓN Y ESTILOS PROFESIONALES (NORTE IMAGEN)
st.set_page_config(page_title="Norte Imagen - Registro RM", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f5f5f5; }
    .stButton>button { background-color: #800020; color: white; border-radius: 5px; width: 100%; height: 3em; font-weight: bold; }
    h1, h2, h3 { color: #800020; text-align: center; }
    label { font-weight: bold; color: #333; }
    .stWarning { border-left: 5px solid #800020; border-radius: 10px; background-color: #fff4f4; }
    .section-header { 
        color: #800020; 
        border-bottom: 2px solid #800020; 
        padding-bottom: 5px; 
        margin-top: 25px; 
        margin-bottom: 15px;
        font-size: 1.3em;
        font-weight: bold;
    }
    .vfg-box { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 10px; 
        border: 2px solid #800020; 
        text-align: center; 
        margin-top: 20px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    .stCheckbox { margin-bottom: -10px; }
    </style>
    """, unsafe_allow_html=True)

# Manejo de estados
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'step_data' not in st.session_state:
    st.session_state.step_data = {}

# 2. FUNCIONES DE APOYO
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv('listado_prestaciones.csv', sep=None, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        df['ESPECIALIDAD'] = df['ESPECIALIDAD'].astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"Error al leer CSV: {e}")
        return None

df = cargar_datos()

def calcular_edad(fecha_nac):
    today = date.today()
    return today.year - fecha_nac.year - ((today.month, today.day) < (fecha_nac.month, fecha_nac.day))

def formatear_rut(rut_sucio):
    if not rut_sucio: return ""
    rut_limpio = str(rut_sucio).replace(".", "").replace("-", "").upper()
    if len(rut_limpio) < 2: return rut_limpio
    cuerpo = rut_limpio[:-1]
    dv = rut_limpio[-1]
    if cuerpo.isdigit():
        cuerpo_formateado = "{:,}".format(int(cuerpo)).replace(",", ".")
        return f"{cuerpo_formateado}-{dv}"
    return rut_sucio

# ---------------------------------------------------------
# PASO 1: IDENTIFICACIÓN
# ---------------------------------------------------------
if st.session_state.step == 1:
    col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
    with col_logo2:
        try:
            st.image("logoNI.png")
        except:
            st.subheader("NORTE IMAGEN")
    
    st.title("Registro de Paciente")
    
    if df is not None:
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                rut_input = st.text_input("RUT del Paciente", placeholder="12.345.678-K")
                rut = formatear_rut(rut_input)
                nombre = st.text_input("Nombre Completo del Paciente")
                
                genero_opciones = ["Masculino", "Femenino", "No binario"]
                genero_identidad = st.selectbox("Identidad de Género", genero_opciones)
                
                sexo_biologico = genero_identidad
                if genero_identidad == "No binario":
                    sexo_biologico = st.selectbox("Sexo asignado al nacer", ["Masculino", "Femenino"])

            with col2:
                fecha_nac = st.date_input("Fecha de Nacimiento", value=datetime(1990, 1, 1), format="DD/MM/YYYY")
                email = st.text_input("Email de contacto")

        edad = calcular_edad(fecha_nac)
        es_menor = edad < 18
        nombre_tutor, rut_tutor = "", ""
        
        if es_menor:
            st.warning("👦 PACIENTE MENOR DE EDAD")
            ct1, ct2 = st.columns(2)
            with ct1: nombre_tutor = st.text_input("Nombre del Representante Legal")
            with ct2: 
                rut_tutor_input = st.text_input("RUT del Representante Legal")
                rut_tutor = formatear_rut(rut_tutor_input)

        st.divider()

        esp_reales = sorted([str(e) for e in df['ESPECIALIDAD'].unique() if pd.notna(e) and str(e).lower() not in ["nan", "otros"]])
        neuro = next((e for e in esp_reales if "NEURO" in e.upper()), None)
        menu_final = [neuro] + [e for e in esp_reales if e != neuro] if neuro else esp_reales

        esp_sel = st.selectbox("Seleccione Especialidad", options=menu_final)
        list_pre = df[df['ESPECIALIDAD'] == esp_sel]['PROCEDIMIENTO A REALIZAR'].unique().tolist()
        pre_sel = st.selectbox("Seleccione el Procedimiento", sorted([str(p) for p in list_pre]))
        
        datos_fila = df[(df['ESPECIALIDAD'] == esp_sel) & (df['PROCEDIMIENTO A REALIZAR'] == pre_sel)]
        tiene_contraste = str(datos_fila['MEDIO DE CONTRASTE'].values[0]).strip().upper() == "SI" if not datos_fila.empty else False

        if st.button("CONTINUAR AL CUESTIONARIO"):
            if rut and nombre:
                st.session_state.step_data.update({
                    "rut": rut, "nombre": nombre, "edad": edad, "sexo_biologico": sexo_biologico,
                    "es_menor": es_menor, "nombre_tutor": nombre_tutor, "rut_tutor": rut_tutor,
                    "procedimiento": pre_sel, "tiene_contraste": tiene_contraste
                })
                st.session_state.step = 2
                st.rerun()

# ---------------------------------------------------------
# PASO 2: CUESTIONARIO DE SEGURIDAD
# ---------------------------------------------------------
elif st.session_state.step == 2:
    st.title("📋 Cuestionario de Seguridad RM")
    
    # 1. ANTECEDENTES CLÍNICOS
    st.markdown('<div class="section-header">Antecedentes clínicos:</div>', unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        ant_ayuno = st.radio("Ayuno (4 hrs.)", ["No", "Sí"], horizontal=True)
        ant_asma = st.radio("Asma", ["No", "Sí"], horizontal=True)
        ant_diabetes = st.radio("Diabetes", ["No", "Sí"], horizontal=True)
        ant_hiperten = st.radio("Hipertensión", ["No", "Sí"], horizontal=True)
    with col_b:
        ant_hipertiroid = st.radio("Hipertiroidismo", ["No", "Sí"], horizontal=True)
        ant_renal = st.radio("Insuficiencia Renal", ["No", "Sí"], horizontal=True)
        ant_dialisis = st.radio("Diálisis", ["No", "Sí"], horizontal=True)
        ant_implantes = st.radio("Implantes/Braquets", ["No", "Sí"], horizontal=True)
    with col_c:
        ant_marcapaso = st.radio("Marcapaso", ["No", "Sí"], horizontal=True)
        ant_metformina = st.radio("Metformina (48h)", ["No", "Sí"], horizontal=True)
        ant_embarazo = st.radio("Embarazo", ["No", "Sí"], horizontal=True)
        ant_lactancia = st.radio("Lactancia", ["No", "Sí"], horizontal=True)
    
    ant_cardiaca = st.radio("¿Cirugía cardiaca?", ["No", "Sí"], horizontal=True)

    # 2. OTRAS CIRUGÍAS
    st.markdown('<div class="section-header">Otras Cirugías:</div>', unsafe_allow_html=True)
    otras_cirugias = st.text_area("¿Alguna otra cirugía? Detalle cuál o cuáles y en qué año:", placeholder="Ej: Vesícula (2018)...")

    # 3. TRATAMIENTOS CÁNCER
    st.markdown('<div class="section-header">Tratamientos Oncológicos:</div>', unsafe_allow_html=True)
    st.write("Seleccione todos los que correspondan:")
    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
    rt = col_t1.checkbox("Radioterapia (RT)")
    qt = col_t2.checkbox("Quimioterapia (QT)")
    bt = col_t3.checkbox("Braquiterapia (BT)")
    it = col_t4.checkbox("Inmunoterapia (IT)")
    
    lista_tratamientos = []
    if rt: lista_tratamientos.append("RT")
    if qt: lista_tratamientos.append("QT")
    if bt: lista_tratamientos.append("BT")
    if it: lista_tratamientos.append("IT")
    
    otro_trat_cancer = st.text_input("Otro tratamiento oncológico:", placeholder="Escriba aquí...")

    # 4. EXÁMENES ANTERIORES (FORMATO UNIFICADO)
    st.markdown('<div class="section-header">Exámenes Anteriores:</div>', unsafe_allow_html=True)
    st.write("Seleccione los exámenes previos que posea:")
    col_ex1, col_ex2, col_ex3, col_ex4 = st.columns(4)
    ex_rx = col_ex1.checkbox("Radiografía (Rx)")
    ex_eco = col_ex2.checkbox("Ecotomografía (Eco)")
    ex_tc = col_ex3.checkbox("Tomografía Computarizada (TC)")
    ex_rm = col_ex4.checkbox("Resonancia Magnética (RM)")
    
    lista_examenes = []
    if ex_rx: lista_examenes.append("Radiografía (Rx)")
    if ex_eco: lista_examenes.append("Ecotomografía (Eco)")
    if ex_tc: lista_examenes.append("Tomografía Computarizada (TC)")
    if ex_rm: lista_examenes.append("Resonancia Magnética (RM)")

    otro_examen = st.text_input("Otro examen anterior:", placeholder="Escriba aquí...")
    
    st.write("**Subir archivos de exámenes (Puede seleccionar varios JPG, JPEG o PDF):**")
    archivos_examenes = st.file_uploader("Arrastre o seleccione archivos", type=['jpg', 'jpeg', 'pdf'], accept_multiple_files=True)

    # 5. VFG
    creatinina, peso, vfg = 0.0, 0.0, 0.0
    if st.session_state.step_data["tiene_contraste"]:
        st.divider()
        st.warning("⚠️ CÁLCULO DE FUNCIÓN RENAL")
        col_v1, col_v2 = st.columns(2)
        with col_v1: creatinina = st.number_input("Creatinina (mg/dL):", min_value=0.00, max_value=7.99, step=0.01, format="%.2f")
        with col_v2: peso = st.number_input("Peso Actual (kg):", min_value=1.0, max_value=250.0, step=0.1, value=70.0)
        
        if creatinina > 0:
            vfg = ((140 - st.session_state.step_data["edad"]) * peso) / (72 * creatinina)
            if st.session_state.step_data["sexo_biologico"] == "Femenino": vfg *= 0.85
            st.markdown(f'<div class="vfg-box"><p>VFG Estimada:</p><h2>{vfg:.2f} mL/min</h2></div>', unsafe_allow_html=True)

    # 6. DECLARACIÓN DE VERACIDAD (BLOQUEO)
    st.markdown('<div class="section-header">Declaración de Veracidad:</div>', unsafe_allow_html=True)
    confirmacion_datos = st.radio(
        "¿Declara que la información clínica proporcionada es fidedigna y no ha ocultado ni un antecedente importante de salud?",
        ["Seleccione una opción", "SÍ", "NO"],
        index=0,
        help="Este campo es obligatorio para continuar."
    )

    st.divider()
    col_prev, col_next = st.columns(2)
    
    if col_prev.button("Atrás"): 
        st.session_state.step = 1
        st.rerun()

    if col_next.button("Siguiente: Consentimiento"):
        if confirmacion_datos == "SÍ":
            st.session_state.step_data.update({
                "antecedentes": {"Ayuno": ant_ayuno, "Asma": ant_asma, "VFG": vfg},
                "tratamientos_onc": lista_tratamientos,
                "examenes_prev": lista_examenes,
                "creatinina": creatinina, "peso": peso, "vfg": vfg
            })
            st.session_state.step = 3
            st.rerun()
        elif confirmacion_datos == "NO":
            st.error("No puede continuar si la información no es fidedigna.")
        else:
            st.warning("Debe confirmar la veracidad de la información para avanzar.")

# ---------------------------------------------------------
# PASO 3: FIRMA
# ---------------------------------------------------------
elif st.session_state.step == 3:
    st.title("🖋️ Consentimiento Informado")
    sujeto = st.session_state.step_data['nombre_tutor'] if st.session_state.step_data['es_menor'] else st.session_state.step_data['nombre']
    id_sujeto = st.session_state.step_data['rut_tutor'] if st.session_state.step_data['es_menor'] else st.session_state.step_data['rut']
    st.markdown(f"Yo, **{sujeto}**, RUT **{id_sujeto}**, autorizo el examen **{st.session_state.step_data['procedimiento']}** en **Norte Imagen**.")
    
    canvas_result = st_canvas(stroke_width=3, stroke_color="#000000", background_color="#ffffff", height=150, width=400, key="canvas")
    
    col_v2, col_f = st.columns(2)
    if col_v2.button("Atrás"): st.session_state.step = 2; st.rerun()
    if col_f.button("FINALIZAR REGISTRO"):
        if canvas_result.image_data is not None:
            st.session_state.step = 4
            st.balloons()
        else: st.warning("Firme para continuar.")

# ---------------------------------------------------------
# PASO 4: ÉXITO
# ---------------------------------------------------------
elif st.session_state.step == 4:
    st.title("✅ Registro Exitoso")
    st.success(f"Ficha de {st.session_state.step_data['nombre']} enviada a revisión.")
    if st.button("Nuevo Paciente"):
        st.session_state.step = 1
        st.rerun()
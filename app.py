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
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# Manejo de estados de navegación
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'step_data' not in st.session_state:
    st.session_state.step_data = {}

# 2. FUNCIONES DE APOYO CORREGIDAS
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
    """Cálculo de edad blindado contra errores de tipo de dato"""
    if fecha_nac is None:
        return 0
    try:
        # Aseguramos que sea un objeto date
        if isinstance(fecha_nac, datetime):
            fecha_nac = fecha_nac.date()
        today = date.today()
        return today.year - fecha_nac.year - ((today.month, today.day) < (fecha_nac.month, fecha_nac.day))
    except AttributeError:
        return 0

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

def mostrar_logo():
    col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
    with col_logo2:
        try:
            st.image("logoNI.png")
        except:
            st.subheader("NORTE IMAGEN")

# ---------------------------------------------------------
# PASO 1: IDENTIFICACIÓN
# ---------------------------------------------------------
if st.session_state.step == 1:
    mostrar_logo()
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
                fecha_nac = st.date_input("Fecha de Nacimiento", value=date(1990, 1, 1), format="DD/MM/YYYY")
                email = st.text_input("Email de contacto")

        # El error ocurría aquí; ahora calcular_edad es más segura
        edad_pasciente = calcular_edad(fecha_nac)
        es_menor = edad_pasciente < 18
        nombre_tutor, rut_tutor = "", ""
        
        if es_menor:
            st.warning(f"👦 PACIENTE MENOR DE EDAD ({edad_pasciente} años)")
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
                    "rut": rut, "nombre": nombre, "edad": edad_pasciente, "sexo_biologico": sexo_biologico,
                    "es_menor": es_menor, "nombre_tutor": nombre_tutor, "rut_tutor": rut_tutor,
                    "procedimiento": pre_sel, "tiene_contraste": tiene_contraste
                })
                st.session_state.step = 2
                st.rerun()

# ---------------------------------------------------------
# PASO 2: CUESTIONARIO DE SEGURIDAD
# ---------------------------------------------------------
elif st.session_state.step == 2:
    mostrar_logo()
    st.title("📋 Cuestionario de Seguridad RM")
    
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

    st.markdown('<div class="section-header">Otras Cirugías:</div>', unsafe_allow_html=True)
    otras_cirugias = st.text_area("¿Alguna otra cirugía? Detalle cuál o cuáles y en qué año:")

    st.markdown('<div class="section-header">Tratamientos Oncológicos:</div>', unsafe_allow_html=True)
    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
    rt = col_t1.checkbox("Radioterapia (RT)")
    qt = col_t2.checkbox("Quimioterapia (QT)")
    bt = col_t3.checkbox("Braquiterapia (BT)")
    it = col_t4.checkbox("Inmunoterapia (IT)")

    st.markdown('<div class="section-header">Exámenes Anteriores:</div>', unsafe_allow_html=True)
    col_ex1, col_ex2, col_ex3, col_ex4 = st.columns(4)
    ex_rx = col_ex1.checkbox("Radiografía (Rx)")
    ex_eco = col_ex2.checkbox("Ecotomografía (Eco)")
    ex_tc = col_ex3.checkbox("Tomografía Computarizada (TC)")
    ex_rm = col_ex4.checkbox("Resonancia Magnética (RM)")
    
    archivos_examenes = st.file_uploader("Subir archivos de exámenes (JPG o PDF)", type=['jpg', 'jpeg', 'pdf'], accept_multiple_files=True)

    vfg = 0.0
    if st.session_state.step_data["tiene_contraste"]:
        st.divider()
        st.warning("⚠️ CÁLCULO DE FUNCIÓN RENAL")
        col_v1, col_v2 = st.columns(2)
        with col_v1: creatinina = st.number_input("Creatinina (mg/dL):", min_value=0.00, step=0.01)
        with col_v2: peso = st.number_input("Peso Actual (kg):", min_value=1.0, value=70.0)
        if creatinina > 0:
            vfg = ((140 - st.session_state.step_data["edad"]) * peso) / (72 * creatinina)
            if st.session_state.step_data["sexo_biologico"] == "Femenino": vfg *= 0.85
            st.markdown(f'<div class="vfg-box"><p>VFG Estimada:</p><h2>{vfg:.2f} mL/min</h2></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">Declaración de Veracidad:</div>', unsafe_allow_html=True)
    confirmacion_datos = st.radio(
        "¿Declara que la información clínica proporcionada es fidedigna y no ha ocultado ni un antecedente importante de salud?",
        ["SÍ", "NO"], index=None
    )

    st.divider()
    col_prev, col_next = st.columns(2)
    if col_prev.button("Atrás"): st.session_state.step = 1; st.rerun()
    if col_next.button("Siguiente: Consentimiento"):
        if confirmacion_datos == "SÍ":
            st.session_state.step_data.update({"vfg": vfg})
            st.session_state.step = 3
            st.rerun()
        elif confirmacion_datos == "NO":
            st.error("No puede continuar si la información no es fidedigna.")

# ---------------------------------------------------------
# PASO 3: CONSENTIMIENTO INFORMADO
# ---------------------------------------------------------
elif st.session_state.step == 3:
    mostrar_logo()
    st.title("🖋️ Consentimiento Informado")
    sujeto = st.session_state.step_data['nombre_tutor'] if st.session_state.step_data['es_menor'] else st.session_state.step_data['nombre']
    id_sujeto = st.session_state.step_data['rut_tutor'] if st.session_state.step_data['es_menor'] else st.session_state.step_data['rut']
    
    if st.session_state.step_data["tiene_contraste"]:
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
        Pacientes con deterioro importante de la función renal, poseen riesgo de desarrollo de fibrosis nefrogénica sistémica.<br><br>
        <strong>Por lo anteriormente expuesto:</strong><br>
        He sido informado de mi derecho de anular o revocar posteriormente este documento, dejándolo constatado por escrito y firmado por mi o mi representante.
        </div>
        """, unsafe_allow_html=True)
        
        autoriza_gadolinio = st.radio(
            f"¿Autorizo la realización del procedimiento ({st.session_state.step_data['procedimiento']}) anteriormente especificado y las acciones que sean necesarias en caso de surgir complicaciones? Además, doy consentimiento para que se administren medicamentos y/o infusiones que se requieran.",
            ["SÍ", "NO"], index=None
        )
    else:
        st.info(f"Yo, **{sujeto}**, RUT **{id_sujeto}**, autorizo la realización del examen **{st.session_state.step_data['procedimiento']}** en la clínica **Norte Imagen**.")
        autoriza_gadolinio = "SÍ"

    st.write("Firme en el recuadro blanco:")
    canvas_result = st_canvas(stroke_width=3, stroke_color="#000000", background_color="#ffffff", height=150, width=400, key="canvas")
    
    col_v2, col_f = st.columns(2)
    if col_v2.button("Atrás"): st.session_state.step = 2; st.rerun()
    if col_f.button("FINALIZAR REGISTRO"):
        if autoriza_gadolinio == "SÍ" and canvas_result.image_data is not None:
            st.session_state.step = 4
            st.balloons()
        elif autoriza_gadolinio == "NO":
            st.error("No se puede proceder sin la autorización.")
        else:
            st.warning("Debe autorizar y firmar.")

# ---------------------------------------------------------
# PASO 4: ÉXITO
# ---------------------------------------------------------
elif st.session_state.step == 4:
    mostrar_logo()
    st.title("✅ Registro Completado")
    st.success(f"La ficha de {st.session_state.step_data['nombre']} ha sido generada correctamente.")
    if st.button("Registrar nuevo paciente"):
        st.session_state.step = 1
        st.rerun()
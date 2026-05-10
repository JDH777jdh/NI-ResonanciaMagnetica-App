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
        color: #800020; border-bottom: 2px solid #800020; padding-bottom: 5px; 
        margin-top: 25px; margin-bottom: 15px; font-size: 1.3em; font-weight: bold;
    }
    .legal-text {
        background-color: #ffffff; padding: 20px; border-radius: 5px; border: 1px solid #ccc;
        font-size: 0.9em; text-align: justify; color: #333; margin-bottom: 20px;
        max-height: 400px; overflow-y: auto;
    }
    .vfg-box { 
        background-color: #ffffff; padding: 20px; border-radius: 10px; 
        border: 2px solid #800020; text-align: center; margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. GESTIÓN DE ESTADO (PERSISTENCIA TOTAL E ÍNTEGRA)
if 'step' not in st.session_state:
    st.session_state.step = 1

if 'form' not in st.session_state:
    st.session_state.form = {
        "rut": "", "nombre": "", "genero_idx": 0, "sexo_bio_idx": 0,
        "fecha_nac": date(1990, 1, 1), "email": "", 
        "nombre_tutor": "", "rut_tutor": "",
        "esp_idx": 0, "pre_idx": 0,
        # Cuestionario Completo
        "ant_ayuno": "No", "ant_asma": "No", "ant_diabetes": "No", "ant_hiperten": "No",
        "ant_hipertiroid": "No", "ant_renal": "No", "ant_dialisis": "No", 
        "ant_implantes": "No", "ant_marcapaso": "No", "ant_metformina": "No",
        "ant_embarazo": "No", "ant_lactancia": "No", "ant_cardiaca": "No",
        "otras_cirugias": "",
        "rt": False, "qt": False, "bt": False, "it": False, "otro_cancer": "",
        "ex_rx": False, "ex_eco": False, "ex_tc": False, "ex_rm": False, "otro_ex": "",
        "creatinina": 0.0, "peso": 70.0, "veracidad": None, "autoriza_gad": None
    }

# 3. FUNCIONES DE APOYO
def formatear_rut(rut_sucio):
    rut_limpio = str(rut_sucio).replace(".", "").replace("-", "").upper().strip()
    if len(rut_limpio) < 2: return rut_limpio
    cuerpo = rut_limpio[:-1]
    dv = rut_limpio[-1]
    if cuerpo.isdigit():
        cuerpo_f = "{:,}".format(int(cuerpo)).replace(",", ".")
        return f"{cuerpo_f}-{dv}"
    return rut_sucio

def calcular_edad(fecha_nac):
    today = date.today()
    return today.year - fecha_nac.year - ((today.month, today.day) < (fecha_nac.month, fecha_nac.day))

def mostrar_logo():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try: st.image("logoNI.png")
        except: st.subheader("NORTE IMAGEN")

@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv('listado_prestaciones.csv', sep=None, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        return df
    except: return None

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
            rut_input = st.text_input("RUT del Paciente", value=st.session_state.form["rut"], placeholder="12.345.678-K")
            st.session_state.form["rut"] = formatear_rut(rut_input)
            st.session_state.form["nombre"] = st.text_input("Nombre Completo del Paciente", value=st.session_state.form["nombre"])
            
            gen_opciones = ["Masculino", "Femenino", "No binario"]
            genero = st.selectbox("Identidad de Género", gen_opciones, index=st.session_state.form["genero_idx"])
            st.session_state.form["genero_idx"] = gen_opciones.index(genero)

            sexo_final = genero
            if genero == "No binario":
                bio_opciones = ["Masculino", "Femenino"]
                sexo_bio = st.selectbox("Sexo asignado al nacer (fines médicos)", bio_opciones, index=st.session_state.form["sexo_bio_idx"])
                st.session_state.form["sexo_bio_idx"] = bio_opciones.index(sexo_bio)
                sexo_final = sexo_bio

        with col2:
            st.session_state.form["fecha_nac"] = st.date_input(
                "Fecha de Nacimiento", 
                value=st.session_state.form["fecha_nac"], 
                min_value=date(1900,1,1), max_value=date.today(),
                format="DD/MM/YYYY"
            )
            st.session_state.form["email"] = st.text_input("Email de contacto", value=st.session_state.form["email"])

        edad = calcular_edad(st.session_state.form["fecha_nac"])
        if edad < 18:
            st.warning(f"👦 PACIENTE MENOR DE EDAD ({edad} años)")
            c1, c2 = st.columns(2)
            st.session_state.form["nombre_tutor"] = c1.text_input("Nombre Representante Legal", value=st.session_state.form["nombre_tutor"])
            rut_t_input = c2.text_input("RUT Representante Legal", value=st.session_state.form["rut_tutor"])
            st.session_state.form["rut_tutor"] = formatear_rut(rut_t_input)

        st.divider()
        
        # PRIORIDAD NEURORADIOLOGÍA
        esp_raw = sorted([str(e) for e in df['ESPECIALIDAD'].unique() if pd.notna(e)])
        neuro_list = [e for e in esp_raw if "NEURO" in e.upper()]
        otros_list = [e for e in esp_raw if "NEURO" not in e.upper()]
        esp_finales = neuro_list + otros_list
        
        esp_sel = st.selectbox("Especialidad", esp_finales, index=st.session_state.form["esp_idx"])
        st.session_state.form["esp_idx"] = esp_finales.index(esp_sel)
        
        list_pre = sorted(df[df['ESPECIALIDAD'] == esp_sel]['PROCEDIMIENTO A REALIZAR'].unique().tolist())
        if st.session_state.form["pre_idx"] >= len(list_pre): st.session_state.form["pre_idx"] = 0
        pre_sel = st.selectbox("Procedimiento", list_pre, index=st.session_state.form["pre_idx"])
        st.session_state.form["pre_idx"] = list_pre.index(pre_sel)
        
        datos_fila = df[(df['ESPECIALIDAD'] == esp_sel) & (df['PROCEDIMIENTO A REALIZAR'] == pre_sel)]
        tiene_con = str(datos_fila['MEDIO DE CONTRASTE'].values[0]).strip().upper() == "SI" if not datos_fila.empty else False

        if st.button("CONTINUAR"):
            st.session_state.tiene_contraste = tiene_con
            st.session_state.sexo_para_calculo = sexo_final
            st.session_state.edad_para_calculo = edad
            st.session_state.procedimiento = pre_sel
            st.session_state.step = 2
            st.rerun()

# ---------------------------------------------------------
# PASO 2: CUESTIONARIO DE SEGURIDAD RM
# ---------------------------------------------------------
elif st.session_state.step == 2:
    mostrar_logo()
    st.title("📋 Cuestionario de Seguridad RM")
    
    st.markdown('<div class="section-header">Antecedentes clínicos:</div>', unsafe_allow_html=True)
    c_a, c_b, c_c = st.columns(3)
    opts = ["No", "Sí"]
    
    st.session_state.form["ant_ayuno"] = c_a.radio("Ayuno (4 hrs.)", opts, index=opts.index(st.session_state.form["ant_ayuno"]), horizontal=True)
    st.session_state.form["ant_asma"] = c_a.radio("Asma", opts, index=opts.index(st.session_state.form["ant_asma"]), horizontal=True)
    st.session_state.form["ant_diabetes"] = c_a.radio("Diabetes", opts, index=opts.index(st.session_state.form["ant_diabetes"]), horizontal=True)
    st.session_state.form["ant_hiperten"] = c_a.radio("Hipertensión", opts, index=opts.index(st.session_state.form["ant_hiperten"]), horizontal=True)
    
    st.session_state.form["ant_hipertiroid"] = c_b.radio("Hipertiroidismo", opts, index=opts.index(st.session_state.form["ant_hipertiroid"]), horizontal=True)
    st.session_state.form["ant_renal"] = c_b.radio("Insuficiencia Renal", opts, index=opts.index(st.session_state.form["ant_renal"]), horizontal=True)
    st.session_state.form["ant_dialisis"] = c_b.radio("Diálisis", opts, index=opts.index(st.session_state.form["ant_dialisis"]), horizontal=True)
    st.session_state.form["ant_implantes"] = c_b.radio("Implantes Metálicos o Braquets", opts, index=opts.index(st.session_state.form["ant_implantes"]), horizontal=True)
    
    st.session_state.form["ant_marcapaso"] = c_c.radio("Marcapaso", opts, index=opts.index(st.session_state.form["ant_marcapaso"]), horizontal=True)
    st.session_state.form["ant_metformina"] = c_c.radio("Suspende Metformina (48 hrs.)", opts, index=opts.index(st.session_state.form["ant_metformina"]), horizontal=True)
    st.session_state.form["ant_embarazo"] = c_c.radio("Embarazo", opts, index=opts.index(st.session_state.form["ant_embarazo"]), horizontal=True)
    st.session_state.form["ant_lactancia"] = c_c.radio("Lactancia", opts, index=opts.index(st.session_state.form["ant_lactancia"]), horizontal=True)
    
    st.session_state.form["ant_cardiaca"] = st.radio("¿Cirugía Cardiaca?", opts, index=opts.index(st.session_state.form["ant_cardiaca"]), horizontal=True)
    st.session_state.form["otras_cirugias"] = st.text_area("¿Alguna otra cirugía? Detalle cuál y en qué año:", value=st.session_state.form["otras_cirugias"])

    st.markdown('<div class="section-header">Tratamientos por Cáncer:</div>', unsafe_allow_html=True)
    ct1, ct2, ct3, ct4 = st.columns(4)
    st.session_state.form["rt"] = ct1.checkbox("Radioterapia (RT)", value=st.session_state.form["rt"])
    st.session_state.form["qt"] = ct2.checkbox("Quimioterapia (QT)", value=st.session_state.form["qt"])
    st.session_state.form["bt"] = ct3.checkbox("Braquiterapia (BT)", value=st.session_state.form["bt"])
    st.session_state.form["it"] = ct4.checkbox("Inmunoterapia (IT)", value=st.session_state.form["it"])
    st.session_state.form["otro_cancer"] = st.text_input("Otro tratamiento oncológico:", value=st.session_state.form["otro_cancer"])

    st.markdown('<div class="section-header">Exámenes Anteriores:</div>', unsafe_allow_html=True)
    ce1, ce2, ce3, ce4 = st.columns(4)
    st.session_state.form["ex_rx"] = ce1.checkbox("Radiografía (Rx)", value=st.session_state.form["ex_rx"])
    st.session_state.form["ex_eco"] = ce2.checkbox("Ecotomografía (Eco)", value=st.session_state.form["ex_eco"])
    st.session_state.form["ex_tc"] = ce3.checkbox("Tomografía Computarizada (TC)", value=st.session_state.form["ex_tc"])
    st.session_state.form["ex_rm"] = ce4.checkbox("Resonancia Magnética (RM)", value=st.session_state.form["ex_rm"])
    st.session_state.form["otro_ex"] = st.text_input("Otro examen anterior:", value=st.session_state.form["otro_ex"])

    if st.session_state.tiene_contraste:
        st.divider()
        st.warning("⚠️ CÁLCULO DE FUNCIÓN RENAL REQUERIDO")
        st.session_state.form["creatinina"] = st.number_input("Creatinina (mg/dL)", value=st.session_state.form["creatinina"], step=0.01, format="%.2f")
        st.session_state.form["peso"] = st.number_input("Peso Actual (kg)", value=st.session_state.form["peso"])
        if st.session_state.form["creatinina"] > 0:
            vfg = ((140 - st.session_state.edad_para_calculo) * st.session_state.form["peso"]) / (72 * st.session_state.form["creatinina"])
            if st.session_state.sexo_para_calculo == "Femenino": vfg *= 0.85
            st.markdown(f'<div class="vfg-box"><p>VFG Estimada:</p><h2>{vfg:.2f} mL/min</h2></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">Declaración de Veracidad:</div>', unsafe_allow_html=True)
    v_opts = ["SÍ", "NO"]
    idx_v = v_opts.index(st.session_state.form["veracidad"]) if st.session_state.form["veracidad"] in v_opts else None
    st.session_state.form["veracidad"] = st.radio("¿Declara que la información clínica proporcionada es fidedigna y no ha ocultado antecedentes de salud?", v_opts, index=idx_v)

    col_back, col_next = st.columns(2)
    if col_back.button("Atrás"): st.session_state.step = 1; st.rerun()
    if col_next.button("Siguiente"):
        if st.session_state.form["veracidad"] == "SÍ": 
            st.session_state.step = 3; st.rerun()
        else: 
            st.error("No puede continuar si la información no es fidedigna.")

# ---------------------------------------------------------
# PASO 3: CONSENTIMIENTO INFORMADO
# ---------------------------------------------------------
elif st.session_state.step == 3:
    mostrar_logo()
    st.title("🖋️ Consentimiento Informado")
    
    sujeto = st.session_state.form['nombre_tutor'] if st.session_state.form['nombre_tutor'] else st.session_state.form['nombre']
    id_sujeto = st.session_state.form['rut_tutor'] if st.session_state.form['rut_tutor'] else st.session_state.form['rut']

    if st.session_state.tiene_contraste:
        st.markdown("""
        <div class="legal-text">
        <strong>OBJETIVOS</strong><br>
        La Resonancia Magnética (RM) es una segura técnica de Diagnóstico, que permite la adquisición de imágenes de gran sensibilidad en todos los planos del espacio de las estructuras del cuerpo. Tiene como objetivo obtener Información, datos funcionales y morfológicos para detectar precozmente una enfermedad.<br>
        Para este examen eventualmente se puede requerir la utilización de un medio de contraste paramagnético de administración endovenosa llamado gadolinio, que permite realzar ciertos tejidos del cuerpo para un mejor diagnóstico.<br><br>
        <strong>CARACTERÍSTICAS</strong><br>
        La Resonancia utiliza fuertes campos magnéticos y ondas de radiofrecuencia, por lo que es muy importante dejar fuera de la sala absolutamente todo lo que lleve consigo de tipo metálico y/o electrónico (relojes, pulseras, teléfonos, tarjetas magnéticas, etc). Si lleva material de este tipo en su cuerpo (fijaciones dentales, piercings, algunos tatuajes, balas o esquirlas metálicas) ciertos tipos de prótesis (valvulares, de cadera, de rodilla, clips metálicos, etc), o implantes, así como dispositivos electrónicos de carácter médico como bombas de insulina, prótesis auditivas, marcapasos, desfibriladores, etc. Avísenos, ya que puede contraindicar de manera absoluta la realización de este examen.<br>
        Usted será posicionado en la camilla del equipo, según el estudio a realizar y se colocarán cerca de la zona a estudiar unos dispositivos (bobinas) que pueden ser de diversos tamaños. Esta exploración suele ser larga (entre 20 min y 1 hr según los casos). Notará ruido derivado del funcionamiento de la RM (por lo que le facilitaremos unos protectores auditivos), todo esto es normal y se le vigilará constantemente desde la sala de control.<br>
        Es muy importante que permanezca quieto durante el estudio y siga las instrucciones del Tecnólogo Médico.<br><br>
        <strong>POTENCIALES RIESGOS</strong><br>
        Existe una muy baja posibilidad de que se presente una reacción adversa al medio de contraste (0.07-2.4%) la mayoría de carácter leve fundamentalmente náuseas o cefaleas al momento de la inyección.<br>
        Pacientes con deterioro importante de la función renal, poseen riesgo de desarrollo de fibrosis nefrogénica sistémica.<br><br>
        <strong>Por lo anteriormente expuesto:</strong><br>
        He sido informado de mi derecho de anular o revocar posteriormente este documento, dejándolo constatado por escrito y firmado por mí o mi representante.
        </div>
        """, unsafe_allow_html=True)
        
        c_opts = ["SÍ", "NO"]
        idx_c = c_opts.index(st.session_state.form["autoriza_gad"]) if st.session_state.form["autoriza_gad"] in c_opts else None
        st.session_state.form["autoriza_gad"] = st.radio(
            f"¿Autoriza la realización del procedimiento {st.session_state.procedimiento} y el uso de medio de contraste?", 
            c_opts, index=idx_c
        )
    else:
        st.info(f"Yo, **{sujeto}**, RUT **{id_sujeto}**, autorizo la realización del examen **{st.session_state.procedimiento}** en Norte Imagen.")
        st.session_state.form["autoriza_gad"] = "SÍ"

    st.write("Firme en el recuadro:")
    canvas_result = st_canvas(stroke_width=3, stroke_color="#000", background_color="#fff", height=150, width=400, key="canvas")

    col_back2, col_fin = st.columns(2)
    if col_back2.button("Atrás"): st.session_state.step = 2; st.rerun()
    if col_fin.button("FINALIZAR REGISTRO"):
        if st.session_state.form["autoriza_gad"] == "SÍ" and canvas_result.image_data is not None:
            st.session_state.step = 4; st.balloons(); st.rerun()
        elif st.session_state.form["autoriza_gad"] == "NO":
            st.error("No se puede proceder sin la autorización de los términos.")
        else:
            st.warning("Debe autorizar y firmar para completar el registro.")

# ---------------------------------------------------------
# PASO 4: ÉXITO
# ---------------------------------------------------------
elif st.session_state.step == 4:
    mostrar_logo()
    st.success(f"¡Registro completado con éxito para {st.session_state.form['nombre']}!")
    if st.button("Registrar nuevo paciente"):
        st.session_state.clear(); st.rerun()
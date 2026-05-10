import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas

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
        font-size: 0.9em; text-align: justify; color: #333; margin-bottom: 20px;
        max-height: 400px; overflow-y: auto;
    }
    .vfg-box { 
        background-color: #ffffff; padding: 20px; border-radius: 10px; 
        border: 2px solid #800020; text-align: center; margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. GESTIÓN DE ESTADO (PERSISTENCIA TOTAL)
if 'step' not in st.session_state:
    st.session_state.step = 1

if 'form' not in st.session_state:
    st.session_state.form = {
        "rut": "", "nombre": "", "genero_idx": 0, "sexo_bio_idx": 0,
        "fecha_nac": date(1990, 1, 1), "email": "", 
        "nombre_tutor": "", "rut_tutor": "",
        "esp_idx": 0, "pre_idx": 0, "ant_ayuno": "No", "ant_asma": "No",
        "ant_implantes": "No", "ant_marcapaso": "No", "otras_cirugias": "",
        "ex_rx": False, "ex_eco": False, "ex_tc": False, "ex_rm": False,
        "creatinina": 0.0, "peso": 70.0, "veracidad": None, "autoriza_gad": None
    }

# 3. FUNCIONES CRÍTICAS
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
            rut_input = st.text_input("RUT del Paciente", value=st.session_state.form["rut"])
            st.session_state.form["rut"] = formatear_rut(rut_input)
            st.session_state.form["nombre"] = st.text_input("Nombre Completo", value=st.session_state.form["nombre"])
            
            gen_opciones = ["Masculino", "Femenino", "No binario"]
            genero = st.selectbox("Identidad de Género", gen_opciones, index=st.session_state.form["genero_idx"])
            st.session_state.form["genero_idx"] = gen_opciones.index(genero)

            # LÓGICA SEXO NO BINARIO / ASIGNADO AL NACER
            sexo_final = genero
            if genero == "No binario":
                bio_opciones = ["Masculino", "Femenino"]
                sexo_bio = st.selectbox("Sexo asignado al nacer (para fines médicos)", bio_opciones, index=st.session_state.form["sexo_bio_idx"])
                st.session_state.form["sexo_bio_idx"] = bio_opciones.index(sexo_bio)
                sexo_final = sexo_bio

        with col2:
            st.session_state.form["fecha_nac"] = st.date_input(
                "Fecha de Nacimiento", 
                value=st.session_state.form["fecha_nac"], 
                min_value=date(1900,1,1), 
                max_value=date.today(),
                format="DD/MM/YYYY"
            )
            st.session_state.form["email"] = st.text_input("Email de contacto", value=st.session_state.form["email"])

        edad = calcular_edad(st.session_state.form["fecha_nac"])
        if edad < 18:
            st.warning(f"👦 PACIENTE MENOR DE EDAD ({edad} años)")
            c1, c2 = st.columns(2)
            st.session_state.form["nombre_tutor"] = c1.text_input("Nombre del Representante Legal", value=st.session_state.form["nombre_tutor"])
            rut_t_input = c2.text_input("RUT del Representante Legal", value=st.session_state.form["rut_tutor"])
            st.session_state.form["rut_tutor"] = formatear_rut(rut_t_input)

        st.divider()
        
        # PRIORIDAD NEURO (POSICIÓN 0)
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

        if st.button("CONTINUAR AL CUESTIONARIO"):
            st.session_state.tiene_contraste = tiene_con
            st.session_state.sexo_para_calculo = sexo_final
            st.session_state.edad_para_calculo = edad
            st.session_state.procedimiento = pre_sel
            st.session_state.step = 2
            st.rerun()

# ---------------------------------------------------------
# PASO 2: CUESTIONARIO
# ---------------------------------------------------------
elif st.session_state.step == 2:
    mostrar_logo()
    st.title("📋 Cuestionario de Seguridad RM")
    
    st.markdown('<div class="section-header">Antecedentes clínicos:</div>', unsafe_allow_html=True)
    c_a, c_b, c_c = st.columns(3)
    
    opts = ["No", "Sí"]
    st.session_state.form["ant_ayuno"] = c_a.radio("Ayuno (4 hrs.)", opts, index=opts.index(st.session_state.form["ant_ayuno"]), horizontal=True)
    st.session_state.form["ant_asma"] = c_a.radio("Asma", opts, index=opts.index(st.session_state.form["ant_asma"]), horizontal=True)
    st.session_state.form["ant_implantes"] = c_b.radio("Implantes/Braquets", opts, index=opts.index(st.session_state.form["ant_implantes"]), horizontal=True)
    st.session_state.form["ant_marcapaso"] = c_c.radio("Marcapaso", opts, index=opts.index(st.session_state.form["ant_marcapaso"]), horizontal=True)

    st.session_state.form["otras_cirugias"] = st.text_area("Otras Cirugías (detalle año):", value=st.session_state.form["otras_cirugias"])

    st.markdown('<div class="section-header">Exámenes Anteriores:</div>', unsafe_allow_html=True)
    col_ex1, col_ex2, col_ex3, col_ex4 = st.columns(4)
    st.session_state.form["ex_rx"] = col_ex1.checkbox("Radiografía (Rx)", value=st.session_state.form["ex_rx"])
    st.session_state.form["ex_eco"] = col_ex2.checkbox("Ecotomografía (Eco)", value=st.session_state.form["ex_eco"])
    st.session_state.form["ex_tc"] = col_ex3.checkbox("Tomografía (TC)", value=st.session_state.form["ex_tc"])
    st.session_state.form["ex_rm"] = col_ex4.checkbox("Resonancia (RM)", value=st.session_state.form["ex_rm"])

    if st.session_state.tiene_contraste:
        st.divider()
        st.warning("⚠️ CÁLCULO DE FUNCIÓN RENAL")
        st.session_state.form["creatinina"] = st.number_input("Creatinina (mg/dL)", value=st.session_state.form["creatinina"], step=0.01, format="%.2f")
        st.session_state.form["peso"] = st.number_input("Peso Actual (kg)", value=st.session_state.form["peso"])
        
        if st.session_state.form["creatinina"] > 0:
            vfg = ((140 - st.session_state.edad_para_calculo) * st.session_state.form["peso"]) / (72 * st.session_state.form["creatinina"])
            if st.session_state.sexo_para_calculo == "Femenino": vfg *= 0.85
            st.markdown(f'<div class="vfg-box"><p>VFG Estimada:</p><h2>{vfg:.2f} mL/min</h2></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">Declaración de Veracidad:</div>', unsafe_allow_html=True)
    v_opts = ["SÍ", "NO"]
    idx_v = v_opts.index(st.session_state.form["veracidad"]) if st.session_state.form["veracidad"] in v_opts else None
    st.session_state.form["veracidad"] = st.radio("¿Declara que la información es fidedigna?", v_opts, index=idx_v)

    col_back, col_next = st.columns(2)
    if col_back.button("Atrás"): 
        st.session_state.step = 1
        st.rerun()
    if col_next.button("Siguiente: Consentimiento"):
        if st.session_state.form["veracidad"] == "SÍ": 
            st.session_state.step = 3
            st.rerun()
        else: st.error("Debe declarar veracidad para continuar.")

# ---------------------------------------------------------
# PASO 3: CONSENTIMIENTO
# ---------------------------------------------------------
elif st.session_state.step == 3:
    mostrar_logo()
    st.title("🖋️ Consentimiento Informado")
    
    sujeto = st.session_state.form['nombre_tutor'] if st.session_state.form['rut_tutor'] else st.session_state.form['nombre']
    id_sujeto = st.session_state.form['rut_tutor'] if st.session_state.form['rut_tutor'] else st.session_state.form['rut']

    if st.session_state.tiene_contraste:
        st.markdown(f"""<div class="legal-text">
        <strong>OBJETIVOS</strong><br>La Resonancia Magnética (RM) es una segura técnica de Diagnóstico...<br><br>
        <strong>POTENCIALES RIESGOS</strong><br>Existe una muy baja posibilidad de reacción adversa (0.07-2.4%)...
        </div>""", unsafe_allow_html=True)
        
        c_opts = ["SÍ", "NO"]
        idx_c = c_opts.index(st.session_state.form["autoriza_gad"]) if st.session_state.form["autoriza_gad"] in c_opts else None
        st.session_state.form["autoriza_gad"] = st.radio(f"¿Autoriza el procedimiento {st.session_state.procedimiento} y uso de contraste?", c_opts, index=idx_c)
    else:
        st.info(f"Yo, **{sujeto}**, RUT **{id_sujeto}**, autorizo la realización del examen **{st.session_state.procedimiento}** en Norte Imagen.")
        st.session_state.form["autoriza_gad"] = "SÍ"

    st.write("Firme en el recuadro blanco:")
    canvas_result = st_canvas(stroke_width=3, stroke_color="#000", background_color="#fff", height=150, width=400, key="canvas")

    col_back2, col_fin = st.columns(2)
    if col_back2.button("Atrás"): 
        st.session_state.step = 2
        st.rerun()
    if col_fin.button("FINALIZAR REGISTRO"):
        if st.session_state.form["autoriza_gad"] == "SÍ" and canvas_result.image_data is not None:
            st.session_state.step = 4
            st.balloons()
            st.rerun()
        else:
            st.warning("Debe autorizar los términos y firmar para completar el registro.")

# ---------------------------------------------------------
# PASO 4: ÉXITO
# ---------------------------------------------------------
elif st.session_state.step == 4:
    mostrar_logo()
    st.success(f"¡Registro completado con éxito para {st.session_state.form['nombre']}!")
    if st.button("Registrar nuevo paciente"):
        st.session_state.clear()
        st.rerun()
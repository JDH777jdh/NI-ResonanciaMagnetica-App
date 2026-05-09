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

# Manejo de estados de navegación y datos
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'step_data' not in st.session_state:
    st.session_state.step_data = {}

# 2. FUNCIONES DE APOYO Y CARGA DE DATOS
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
# PASO 1: IDENTIFICACIÓN Y DATOS CLÍNICOS BÁSICOS
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
                if rut_input and rut != rut_input:
                    st.caption(f"RUT validado: {rut}")
                
                nombre = st.text_input("Nombre Completo del Paciente")
                
                # Gestión de Género e Identidad
                genero_opciones = ["Masculino", "Femenino", "No binario"]
                genero_identidad = st.selectbox("Identidad de Género", genero_opciones)
                
                sexo_biologico = genero_identidad
                if genero_identidad == "No binario":
                    sexo_biologico = st.selectbox(
                        "Sexo asignado al nacer", 
                        ["Masculino", "Femenino"],
                        help="Dato clínico estrictamente necesario para el cálculo de la función renal."
                    )

            with col2:
                fecha_nac = st.date_input("Fecha de Nacimiento", value=datetime(1990, 1, 1),
                                        min_value=datetime(1910, 1, 1), max_value=datetime.now(),
                                        format="DD/MM/YYYY")
                email = st.text_input("Email de contacto")

        edad = calcular_edad(fecha_nac)
        es_menor = edad < 18
        nombre_tutor, rut_tutor = "", ""
        
        if es_menor:
            st.warning("👦 PACIENTE MENOR DE EDAD: Ingrese datos del Representante Legal.")
            ct1, ct2 = st.columns(2)
            with ct1: 
                nombre_tutor = st.text_input("Nombre del Representante Legal")
            with ct2: 
                rut_tutor_input = st.text_input("RUT del Representante Legal", placeholder="12.345.678-K")
                rut_tutor = formatear_rut(rut_tutor_input)
                if rut_tutor_input and rut_tutor != rut_tutor_input:
                    st.caption(f"RUT Representante: {rut_tutor}")

        st.divider()

        # Selección de Examen con Prioridad Neurorradiología
        esp_reales = sorted([str(e) for e in df['ESPECIALIDAD'].unique() 
                            if pd.notna(e) and str(e).lower() not in ["nan", "otros", "otro", "none"]])
        
        neuro = next((e for e in esp_reales if "NEURO" in e.upper()), None)
        menu_final = [neuro] + [e for e in esp_reales if e != neuro] if neuro else esp_reales

        esp_sel = st.selectbox("Seleccione Especialidad", options=menu_final)
        list_pre = df[df['ESPECIALIDAD'] == esp_sel]['PROCEDIMIENTO A REALIZAR'].unique().tolist()
        list_pre_limpia = sorted([str(p) for p in list_pre if pd.notna(p)])
        pre_sel = st.selectbox("Seleccione el Procedimiento", list_pre_limpia)
        
        datos_fila = df[(df['ESPECIALIDAD'] == esp_sel) & (df['PROCEDIMIENTO A REALIZAR'] == pre_sel)]
        info_con = datos_fila['MEDIO DE CONTRASTE'].values[0] if not datos_fila.empty else ""
        tiene_contraste = str(info_con).strip().upper() == "SI"

        if st.button("CONTINUAR AL CUESTIONARIO"):
            if rut and nombre and (not es_menor or (nombre_tutor and rut_tutor)):
                st.session_state.step_data.update({
                    "rut": rut, "nombre": nombre, "edad": edad, "sexo_biologico": sexo_biologico,
                    "es_menor": es_menor, "nombre_tutor": nombre_tutor, "rut_tutor": rut_tutor,
                    "procedimiento": pre_sel, "tiene_contraste": tiene_contraste, "info_contraste": info_con
                })
                st.session_state.step = 2
                st.rerun()
            else:
                st.error("Por favor complete los campos obligatorios.")

# ---------------------------------------------------------
# PASO 2: CUESTIONARIO Y CÁLCULO VFG AUTOMÁTICO
# ---------------------------------------------------------
elif st.session_state.step == 2:
    st.title("📋 Cuestionario de Seguridad RM")
    with st.container():
        st.info("Responda cuidadosamente para garantizar la seguridad del procedimiento.")
        q1 = st.radio("1. ¿Posee marcapasos, desfibrilador o neuroestimulador?", ["No", "Sí"])
        q2 = st.radio("2. ¿Posee clips vasculares, stents o válvulas cardíacas?", ["No", "Sí"])
        q3 = st.radio("3. ¿Tiene esquirlas metálicas en los ojos o cuerpo?", ["No", "Sí"])
        q4 = st.radio("4. ¿Ha tenido cirugías recientes (últimos 2 meses)?", ["No", "Sí"])
        
        creatinina = 0.0
        peso = 0.0
        vfg = 0.0
        
        if st.session_state.step_data["tiene_contraste"]:
            st.warning(f"⚠️ EXAMEN CON CONTRASTE: {st.session_state.step_data['info_contraste']}")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                creatinina = st.number_input("Creatinina (mg/dL):", min_value=0.00, max_value=7.99, step=0.01, format="%.2f")
            with col_c2:
                peso = st.number_input("Peso Actual (kg):", min_value=1.0, max_value=250.0, step=0.1, value=70.0)
            
            if creatinina > 0:
                # Fórmula Cockcroft-Gault
                vfg = ((140 - st.session_state.step_data["edad"]) * peso) / (72 * creatinina)
                if st.session_state.step_data["sexo_biologico"] == "Femenino":
                    vfg *= 0.85
                
                st.markdown(f"""
                <div class="vfg-box">
                    <p style="margin:0; font-size: 1em; color: #333; font-weight: bold;">Función Renal Estimada (Cockcroft-Gault)</p>
                    <h2 style="margin:0; color: #800020; font-size: 2.2em;">{vfg:.2f} <span style="font-size: 0.5em;">mL/min</span></h2>
                </div>
                """, unsafe_allow_html=True)

            q5 = st.radio("5. ¿Es alérgico al contraste (Gadolinio) o sufre de asma?", ["No", "Sí"])

    col_v, col_s = st.columns(2)
    if col_v.button("Atrás"): st.session_state.step = 1; st.rerun()
    if col_s.button("Ir al Consentimiento"):
        st.session_state.step_data.update({"q1": q1, "q2": q2, "q3": q3, "q4": q4, "vfg": vfg})
        st.session_state.step = 3
        st.rerun()

# ---------------------------------------------------------
# PASO 3: CONSENTIMIENTO Y FIRMA
# ---------------------------------------------------------
elif st.session_state.step == 3:
    st.title("🖋️ Consentimiento Informado")
    sujeto = st.session_state.step_data['nombre_tutor'] if st.session_state.step_data['es_menor'] else st.session_state.step_data['nombre']
    id_sujeto = st.session_state.step_data['rut_tutor'] if st.session_state.step_data['es_menor'] else st.session_state.step_data['rut']
    parentesco = " (en representación legal del paciente)" if st.session_state.step_data['es_menor'] else ""
    
    st.markdown(f"Yo, **{sujeto}**, RUT **{id_sujeto}**{parentesco}, autorizo la realización del examen **{st.session_state.step_data['procedimiento']}** en la clínica **Norte Imagen**.")
    
    st.write("Firme en el recuadro blanco:")
    canvas_result = st_canvas(stroke_width=3, stroke_color="#000000", background_color="#ffffff", height=150, width=400, key="canvas")
    
    col_v2, col_f = st.columns(2)
    if col_v2.button("Atrás"): st.session_state.step = 2; st.rerun()
    if col_f.button("FINALIZAR Y REGISTRAR"):
        if canvas_result.image_data is not None:
            st.session_state.step = 4
            st.balloons()
        else:
            st.warning("Debe firmar para completar el registro.")

# ---------------------------------------------------------
# PASO 4: ÉXITO
# ---------------------------------------------------------
elif st.session_state.step == 4:
    st.title("✅ Registro Completado")
    st.success(f"La ficha de {st.session_state.step_data['nombre']} ha sido generada correctamente.")
    if st.button("Registrar nuevo paciente"):
        st.session_state.step = 1
        st.rerun()
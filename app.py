import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from PIL import Image

# 1. CONFIGURACIÓN Y ESTILOS PROFESIONALES
st.set_page_config(page_title="Norte Imagen - Registro RM", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f5f5f5; }
    .stButton>button { background-color: #800020; color: white; border-radius: 5px; width: 100%; height: 3em; font-weight: bold; }
    h1, h2, h3 { color: #800020; text-align: center; }
    label { font-weight: bold; color: #333; }
    .stWarning { border-left: 5px solid #800020; }
    </style>
    """, unsafe_allow_html=True)

if 'step' not in st.session_state:
    st.session_state.step = 1
if 'step_data' not in st.session_state:
    st.session_state.step_data = {}

# 2. CARGA Y LIMPIEZA DE DATOS
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv('listado_prestaciones.csv', sep=None, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        # Mantenemos la conversión a texto, pero no forzamos el "OTRO" si queremos borrarlo luego
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
# PASO 1: IDENTIFICACIÓN Y SELECCIÓN DE EXAMEN
# ---------------------------------------------------------
if st.session_state.step == 1:
    col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
    with col_logo2:
        st.image("logoNI.png")
    st.title("Registro de Paciente")
    
    if df is not None:
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                rut_input = st.text_input("RUT del Paciente", placeholder="12.345.678-K")
                rut = formatear_rut(rut_input)
                if rut_input and rut != rut_input:
                    st.caption(f"RUT detectado: {rut}")
                nombre = st.text_input("Nombre Completo del Paciente")
            with col2:
                fecha_nac = st.date_input("Fecha de Nacimiento", value=datetime(1990, 1, 1),
                                        min_value=datetime(1910, 1, 1), max_value=datetime.now(),
                                        format="DD/MM/YYYY")
                email = st.text_input("Email de contacto")

        es_menor = calcular_edad(fecha_nac) < 18
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

        # --- LÓGICA DE PRIORIDAD SIN "OTROS" ---
        # Filtramos para excluir cualquier valor nulo o que diga "nan" u "Otros"
        esp_reales = sorted([str(e) for e in df['ESPECIALIDAD'].unique() 
                            if pd.notna(e) and str(e).lower() not in ["nan", "otros", "otro", "none"]])
        
        neuro = next((e for e in esp_reales if "NEURO" in e.upper()), None)
        musculo = next((e for e in esp_reales if "MUSCULO" in e.upper() or "ESQUELETICO" in e.upper()), None)
        cuerpo = next((e for e in esp_reales if "CUERPO" in e.upper()), None)
        angio = next((e for e in esp_reales if "ANGIO" in e.upper()), None)

        menu_final = []
        for item in [neuro, musculo, cuerpo, angio]:
            if item and item not in menu_final:
                menu_final.append(item)
        
        for e in esp_reales:
            if e not in menu_final:
                menu_final.append(e)

        esp_sel = st.selectbox("Seleccione Especialidad", options=menu_final, index=0)
        
        list_pre = df[df['ESPECIALIDAD'] == esp_sel]['PROCEDIMIENTO A REALIZAR'].unique().tolist()
        # También limpiamos nulos en los procedimientos por seguridad
        list_pre_limpia = sorted([str(p) for p in list_pre if pd.notna(p) and str(p).lower() != "nan"])
        pre_sel = st.selectbox("Seleccione el Procedimiento", list_pre_limpia)
        
        datos_fila = df[(df['ESPECIALIDAD'] == esp_sel) & (df['PROCEDIMIENTO A REALIZAR'] == pre_sel)]
        info_con = datos_fila['MEDIO DE CONTRASTE'].values[0] if not datos_fila.empty else ""
        tiene_contraste = pd.notna(info_con) and str(info_con).strip() != ""

        if st.button("CONTINUAR AL CUESTIONARIO"):
            if rut and nombre and (not es_menor or (nombre_tutor and rut_tutor)):
                st.session_state.step_data.update({
                    "rut": rut, "nombre": nombre, "fecha_nac": fecha_nac, "es_menor": es_menor,
                    "nombre_tutor": nombre_tutor, "rut_tutor": rut_tutor, "email": email,
                    "especialidad": esp_sel, "procedimiento": pre_sel,
                    "tiene_contraste": tiene_contraste, "info_contraste": info_con
                })
                st.session_state.step = 2
                st.rerun()
            else:
                st.error("Por favor complete los campos obligatorios.")

# PASOS 2, 3 Y 4 (Sin cambios adicionales)
elif st.session_state.step == 2:
    st.title("📋 Cuestionario de Seguridad RM")
    with st.container():
        st.info("Responda cuidadosamente para garantizar la seguridad del procedimiento.")
        q1 = st.radio("1. ¿Posee marcapasos, desfibrilador o neuroestimulador?", ["No", "Sí"])
        q2 = st.radio("2. ¿Posee clips vasculares, stents o válvulas cardíacas?", ["No", "Sí"])
        q3 = st.radio("3. ¿Tiene esquirlas metálicas en los ojos o cuerpo?", ["No", "Sí"])
        q4 = st.radio("4. ¿Ha tenido cirugías recientes (últimos 2 meses)?", ["No", "Sí"])
        creatinina = ""
        if st.session_state.step_data["tiene_contraste"]:
            st.warning(f"⚠️ EXAMEN CON CONTRASTE: {st.session_state.step_data['info_contraste']}")
            creatinina = st.text_input("Indique valor de Creatinina (si lo tiene):")
            q5 = st.radio("5. ¿Es alérgico al contraste (Gadolinio) o sufre de asma?", ["No", "Sí"])
    col_v, col_s = st.columns(2)
    if col_v.button("Atrás"): st.session_state.step = 1; st.rerun()
    if col_s.button("Ir al Consentimiento"):
        st.session_state.step_data.update({"q1": q1, "q2": q2, "q3": q3, "q4": q4, "creatinina": creatinina})
        st.session_state.step = 3
        st.rerun()

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
        else: st.warning("Debe firmar para completar el registro.")

elif st.session_state.step == 4:
    st.title("✅ Registro Completado")
    st.success(f"La ficha de {st.session_state.step_data['nombre']} ha sido generada correctamente.")
    if st.button("Registrar nuevo paciente"):
        st.session_state.step = 1
        st.rerun()
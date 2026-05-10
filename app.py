import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from fpdf import FPDF
import os
from PIL import Image
import io
import re

# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO CORPORATIVO
st.set_page_config(page_title="Norte Imagen - Registro RM", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    .stButton>button { 
        background-color: #800020; color: white; border-radius: 8px; 
        width: 100%; height: 3.8em; font-weight: bold; border: none; font-size: 1.1em;
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

# 2. INICIALIZACIÓN DE ESTADO TOTAL (SIN AHORRO)
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
        "diagnostico_cancer": "", "rt": False, "qt": False, "bt": False, "it": False,
        "ex_rx": False, "ex_eco": False, "ex_tc": False, "ex_rm": False, "archivos_previos": None,
        "creatinina": 0.0, "peso": 70.0, "vfg": 0.0, "firma_img": None
    }

# 3. FUNCIONES DE FORMATO Y LÓGICA CLÍNICA
def formatear_rut(rut_sucio):
    if not rut_sucio: return ""
    rut_limpio = str(rut_sucio).replace(".", "").replace("-", "").upper().strip()
    if len(rut_limpio) < 2: return rut_limpio
    cuerpo, dv = rut_limpio[:-1], rut_limpio[-1]
    if cuerpo.isdigit():
        return f"{int(cuerpo):,}-{dv}".replace(",", ".")
    return rut_sucio

def calcular_edad(fecha_nac):
    today = date.today()
    return today.year - fecha_nac.year - ((today.month, today.day) < (fecha_nac.month, fecha_nac.day))

def obtener_iniciales(nombre_completo):
    partes = nombre_completo.strip().split()
    return "".join([p[0].upper() for p in partes[1:]]) if len(partes) > 1 else "PX"

# 4. GENERADOR DE PDF MULTIPÁGINA DETALLADO
def generar_pdf_clinico(datos):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    def agregar_header():
        if os.path.exists("logoNI.png"):
            # Logo centrado
            pdf.image("logoNI.png", x=85, y=10, w=40)
        pdf.set_font("Arial", 'B', 16); pdf.set_text_color(128, 0, 32)
        pdf.set_xy(10, 35); pdf.cell(190, 10, txt="NORTE IMAGEN - REGISTRO CLÍNICO OFICIAL", ln=True, align='C')
        pdf.set_font("Arial", 'B', 10); pdf.set_text_color(100, 100, 100)
        pdf.cell(190, 5, txt="UNIDAD DE RESONANCIA MAGNÉTICA", ln=True, align='C')
        pdf.ln(5)

    pdf.add_page()
    agregar_header()
    
    # 1. Identificación
    pdf.set_fill_color(128, 0, 32); pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 11); pdf.cell(190, 8, txt=" 1. IDENTIFICACIÓN DEL PACIENTE", ln=True, fill=True)
    pdf.set_font("Arial", size=10); pdf.set_text_color(0, 0, 0); pdf.ln(2)
    
    id_pac = datos['rut'] if not datos['sin_rut'] else f"{datos['tipo_doc']} {datos['num_doc']}"
    pdf.cell(100, 7, txt=f"Nombre: {datos['nombre']}".encode('latin-1', 'replace').decode('latin-1'), ln=0)
    pdf.cell(90, 7, txt=f"RUT/ID: {id_pac}", ln=1)
    
    f_nac_str = datos['fecha_nac'].strftime("%d/%m/%Y")
    pdf.cell(100, 7, txt=f"Fecha Nacimiento: {f_nac_str} (Edad: {calcular_edad(datos['fecha_nac'])} años)", ln=0)
    pdf.cell(90, 7, txt=f"Género: {datos['genero']} (Sexo Bio: {datos['sexo_biologico']})", ln=1)
    
    if datos['es_menor']:
        pdf.set_font("Arial", 'B', 10); pdf.set_text_color(128, 0, 32)
        pdf.cell(190, 7, txt=f"REPRESENTANTE LEGAL: {datos['nombre_tutor']} (RUT: {datos['rut_tutor']})".encode('latin-1', 'replace').decode('latin-1'), ln=1)
        pdf.set_font("Arial", size=10); pdf.set_text_color(0, 0, 0)

    # 2. Datos del Examen
    pdf.ln(5); pdf.set_fill_color(128, 0, 32); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, txt=" 2. DATOS DEL EXAMEN", ln=True, fill=True)
    pdf.set_font("Arial", size=10); pdf.set_text_color(0, 0, 0); pdf.ln(2)
    pdf.cell(190, 7, txt=f"Especialidad: {datos['esp_nombre']}".encode('latin-1', 'replace').decode('latin-1'), ln=1)
    pdf.cell(190, 7, txt=f"Estudio Programado: {datos['pre_nombre']}".encode('latin-1', 'replace').decode('latin-1'), ln=1)

    # 3. Anamnesis Exhaustiva
    pdf.ln(5); pdf.set_fill_color(128, 0, 32); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, txt=" 3. ANAMNESIS DE SEGURIDAD (CUESTIONARIO)", ln=True, fill=True)
    pdf.set_font("Arial", size=9); pdf.set_text_color(0, 0, 0); pdf.ln(2)
    
    q = [
        ("Ayuno (4 hrs)", datos['ant_ayuno']), ("Asma", datos['ant_asma']), 
        ("Diabetes", datos['ant_diabetes']), ("Hipertensión", datos['ant_hiperten']),
        ("Falla Renal", datos['ant_renal']), ("Diálisis", datos['ant_dialisis']),
        ("Marcapaso/Neuro", datos['ant_marcapaso']), ("Metales/Clips", datos['ant_implantes']),
        ("Metformina", datos['ant_metformina']), ("¿Embarazo?", datos['ant_embarazo']),
        ("Lactancia", datos['ant_lactancia']), ("E. Cardíaca", datos['ant_cardiaca']),
        ("Tatuajes", datos['ant_tatuajes']), ("Claustrofobia", datos['ant_claustrofobia'])
    ]
    for i in range(0, len(q)-1, 2):
        pdf.cell(95, 6, txt=f"{q[i][0]}: {q[i][1]}", ln=0)
        pdf.cell(95, 6, txt=f"{q[i+1][0]}: {q[i+1][1]}", ln=1)

    # 4. Tratamientos Cáncer y Cirugías
    pdf.ln(5); pdf.set_font("Arial", 'B', 10); pdf.cell(190, 6, txt="TRATAMIENTOS DE CÁNCER:", ln=True)
    pdf.set_font("Arial", size=9)
    pdf.cell(190, 6, txt=f"Diagnóstico/Tipo: {datos['diagnostico_cancer'] if datos['diagnostico_cancer'] else 'Ninguno'}", ln=1)
    trats = []
    if datos['rt']: trats.append("Radioterapia")
    if datos['qt']: trats.append("Quimioterapia")
    if datos['bt']: trats.append("Braquiterapia")
    if datos['it']: trats.append("Inmunoterapia")
    pdf.cell(190, 6, txt=f"Tratamientos aplicados: {', '.join(trats) if trats else 'Sin tratamientos'}", ln=1)
    
    pdf.ln(2); pdf.set_font("Arial", 'B', 10); pdf.cell(190, 6, txt="HISTORIAL QUIRÚRGICO:", ln=True)
    pdf.set_font("Arial", size=9)
    pdf.multi_cell(190, 5, txt=f"{datos['otras_cirugias'] if datos['otras_cirugias'] else 'Sin cirugías previas'}")

    # 5. Consentimiento Informado (SIN RESUMIR)
    pdf.add_page(); agregar_header()
    pdf.set_fill_color(128, 0, 32); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, txt=" 4. CONSENTIMIENTO INFORMADO", ln=True, fill=True)
    pdf.set_font("Arial", size=8.5); pdf.set_text_color(0, 0, 0); pdf.ln(2)
    
    cons_text = (
        "1. He sido informado que la Resonancia Magnetica es un examen diagnostico que utiliza un campo magnetico potente y ondas de radiofrecuencia.\n"
        "2. Comprendo que no utiliza radiacion ionizante (Rayos X), pero que existen riesgos asociados a la presencia de metales o dispositivos electronicos.\n"
        "3. Declaro NO portar marcapasos, desfibriladores cardiacos, clips de aneurisma cerebral metalicos, implantes cocleares o esquirlas metalicas en ojos.\n"
        "4. En caso de requerir Medio de Contraste (Gadolinio), autorizo su administracion endovenosa y entiendo que existe un riesgo minimo de reaccion alergica.\n"
        "5. Declaro que he comprendido las instrucciones de seguridad y que toda la informacion proporcionada en este formulario es verdadera y fidedigna.\n"
        "6. Autorizo al equipo de NORTE IMAGEN a realizar el examen y procedimientos necesarios para la obtencion de imagenes diagnosticas de calidad."
    )
    pdf.multi_cell(190, 5, txt=cons_text.encode('latin-1', 'replace').decode('latin-1'))

    # Firmas
    pdf.ln(20)
    if datos['firma_img']:
        buf = io.BytesIO(); datos['firma_img'].save(buf, format='PNG'); buf.seek(0)
        pdf.image(buf, x=75, y=pdf.get_y(), w=60, type='PNG')
    
    pdf.ln(30); y_line = pdf.get_y()
    pdf.line(40, y_line, 100, y_line); pdf.line(120, y_line, 180, y_line)
    pdf.set_font("Arial", 'B', 8)
    pdf.set_xy(40, y_line + 2); pdf.cell(60, 5, txt="FIRMA PACIENTE O TUTOR", align='C')
    pdf.set_xy(120, y_line + 2); pdf.cell(60, 5, txt="FIRMA PROFESIONAL NORTE IMAGEN", align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- CARGA DE BASE DE DATOS ---
@st.cache_data
def cargar_prestaciones():
    if os.path.exists('listado_prestaciones.csv'):
        df = pd.read_csv('listado_prestaciones.csv', sep=None, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        return df
    return None

df_master = cargar_prestaciones()

# --- PASO 1: DATOS DE IDENTIFICACIÓN Y EXAMEN ---
if st.session_state.step == 1:
    if os.path.exists("logoNI.png"): st.image("logoNI.png", width=220)
    st.title("Registro Norte Imagen")
    
    st.markdown('<div class="section-header">DATOS DE IDENTIFICACIÓN</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    nombre = c1.text_input("Nombre Completo del Paciente")
    
    sin_rut = st.checkbox("Extranjero o Sin RUT Chileno")
    if not sin_rut:
        rut_raw = c2.text_input("RUT (Ej: 12.345.678-9)")
        rut_val = formatear_rut(rut_raw)
    else:
        t_doc = c2.selectbox("Tipo Documento", ["Pasaporte", "DNI", "Cédula Extranjera"])
        n_doc = c2.text_input("N° Documento Identidad")
        rut_val = ""

    c3, c4 = st.columns(2)
    # FIX: Error de rango de fechas resuelto (min_value y max_value)
    f_nac = c3.date_input("Fecha de Nacimiento", 
                         value=st.session_state.form["fecha_nac"], 
                         min_value=date(1920, 1, 1), 
                         max_value=date.today(),
                         format="DD/MM/YYYY")
    
    genero = c4.selectbox("Identidad de Género", ["Masculino", "Femenino", "No binario"])
    
    sexo_bio = "N/A"
    if genero == "No binario":
        sexo_bio = st.selectbox("Sexo asignado al nacer (Para protocolos de seguridad)", ["Masculino", "Femenino"])
    else:
        sexo_bio = genero

    email = st.text_input("Correo Electrónico de Contacto")
    
    # Lógica de Tutor
    edad_p = calcular_edad(f_nac)
    if edad_p < 18:
        st.warning(f"Paciente Menor de Edad ({edad_p} años). Ingrese datos del Representante.")
        ct1, ct2 = st.columns(2)
        nom_t = ct1.text_input("Nombre Completo del Representante")
        rut_t = ct2.text_input("RUT del Representante")
    else: nom_t, rut_t = "", ""

    # SECCIÓN: DATOS DEL EXAMEN (Nombre cambiado como pediste)
    if df_master is not None:
        st.markdown('<div class="section-header">DATOS DEL EXAMEN</div>', unsafe_allow_html=True)
        # ORDENAR: NEURORRADIOLOGIA PRIMERO
        lista_esp = sorted([str(e) for e in df_master['ESPECIALIDAD'].unique() if pd.notna(e)])
        if "NEURORRADIOLOGIA" in lista_esp:
            lista_esp.remove("NEURORRADIOLOGIA")
            lista_esp.insert(0, "NEURORRADIOLOGIA")
        
        esp_sel = st.selectbox("Especialidad Médica", lista_esp)
        
        # Filtrado de estudios (PROCEDIMIENTOS Y ESTUDIOS AVANZADOS)
        df_f = df_master[df_master['ESPECIALIDAD'] == esp_sel]
        lista_pre = sorted([str(p) for p in df_f['PROCEDIMIENTO A REALIZAR'].unique() if pd.notna(p)])
        pre_sel = st.selectbox("Procedimiento / Estudio", lista_pre)
        
        st.markdown("**Carga de Orden Médica:**")
        orden_up = st.file_uploader("Subir imagen o PDF de la orden médica", type=["pdf", "png", "jpg", "jpeg"])

    st.markdown("---")
    veracidad1 = st.checkbox("Declaro que todos los datos de identificación y del examen son verídicos y fidedignos.")

    if st.button("CONTINUAR A ENCUESTA CLÍNICA"):
        if veracidad1 and nombre and (rut_val or sin_rut):
            st.session_state.form.update({
                "nombre": nombre, "rut": rut_val, "sin_rut": sin_rut, "fecha_nac": f_nac,
                "genero": genero, "sexo_biologico": sexo_bio, "email": email,
                "es_menor": (edad_p < 18), "nombre_tutor": nom_t, "rut_tutor": formatear_rut(rut_t),
                "esp_nombre": esp_sel, "pre_nombre": pre_sel
            })
            # Lógica de contraste
            row = df_master[df_master['PROCEDIMIENTO A REALIZAR'] == pre_sel]
            st.session_state.tiene_contraste = "SI" in str(row['MEDIO DE CONTRASTE'].values[0]).upper()
            st.session_state.step = 2; st.rerun()
        else:
            st.error("Por favor, complete los datos obligatorios y acepte la declaración de veracidad.")

# --- PASO 2: ANAMNESIS, CÁNCER Y CIRUGÍAS (SIN AHORRO) ---
elif st.session_state.step == 2:
    st.title("📋 Anamnesis Exhaustiva de Seguridad")
    op = ["No", "Sí"]
    
    st.markdown('<div class="section-header">CUESTIONARIO DE SALUD GENERAL</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    st.session_state.form["ant_ayuno"] = c1.radio("¿Cumple Ayuno (4 hrs)?", op)
    st.session_state.form["ant_asma"] = c2.radio("¿Padece de Asma?", op)
    st.session_state.form["ant_diabetes"] = c3.radio("¿Padece de Diabetes?", op)
    st.session_state.form["ant_hiperten"] = c1.radio("¿Es Hipertenso/a?", op)
    st.session_state.form["ant_renal"] = c2.radio("¿Enfermedad Renal?", op)
    st.session_state.form["ant_dialisis"] = c3.radio("¿Está en Diálisis?", op)
    st.session_state.form["ant_marcapaso"] = c1.radio("¿Usa Marcapaso?", op)
    st.session_state.form["ant_implantes"] = c2.radio("¿Clips/Implantes?", op)
    st.session_state.form["ant_metformina"] = c3.radio("¿Usa Metformina?", op)
    st.session_state.form["ant_embarazo"] = c1.radio("¿Está Embarazada?", op)
    st.session_state.form["ant_lactancia"] = c2.radio("¿Está Lactando?", op)
    st.session_state.form["ant_cardiaca"] = c3.radio("¿Falla Cardíaca?", op)
    st.session_state.form["ant_claustrofobia"] = c1.radio("¿Sufre Claustrofobia?", op)
    st.session_state.form["ant_esquirlas"] = c2.radio("¿Esquirlas en ojos?", op)
    st.session_state.form["ant_tatuajes"] = c3.radio("¿Tatuajes extensos?", op)

    # SECCIÓN TRATAMIENTOS DE CÁNCER (SEPARADO)
    st.markdown('<div class="section-header">TRATAMIENTOS DE CÁNCER</div>', unsafe_allow_html=True)
    st.session_state.form["diagnostico_cancer"] = st.text_input("Escriba su Diagnóstico o Tipo de Cáncer (Si aplica):")
    st.write("Seleccione tratamientos recibidos:")
    cx = st.columns(4)
    st.session_state.form["rt"] = cx[0].checkbox("Radioterapia")
    st.session_state.form["qt"] = cx[1].checkbox("Quimioterapia")
    st.session_state.form["bt"] = cx[2].checkbox("Braquiterapia")
    st.session_state.form["it"] = cx[3].checkbox("Inmunoterapia")

    # SECCIÓN CIRUGÍAS Y EXÁMENES ANTERIORES
    st.markdown('<div class="section-header">CIRUGÍAS Y EXÁMENES PREVIOS</div>', unsafe_allow_html=True)
    st.session_state.form["otras_cirugias"] = st.text_area("Describa cirugías previas y fechas:")
    st.write("Indique si posee exámenes anteriores del área a estudiar:")
    ce = st.columns(4)
    st.session_state.form["ex_rx"] = ce[0].checkbox("Radiografía (Rx)")
    st.session_state.form["ex_eco"] = ce[1].checkbox("Ecotomografía (Eco)")
    st.session_state.form["ex_tc"] = ce[2].checkbox("Escáner (TC)")
    st.session_state.form["ex_rm"] = ce[3].checkbox("Resonancia (RM)")
    
    st.markdown("**Carga de Informes Anteriores:**")
    st.file_uploader("Subir archivos de exámenes anteriores", accept_multiple_files=True)

    if st.session_state.tiene_contraste:
        st.warning("⚠️ EXAMEN CON CONTRASTE: Se requiere función renal.")
        crea = st.number_input("Valor Creatinina plasmática", step=0.01)
        peso = st.number_input("Peso Actual del Paciente (Kg)", value=70.0)
        st.session_state.form["creatinina"] = crea
        st.session_state.form["peso"] = peso
        
        # CÁLCULO DE VFG (Fórmula Cockcroft-Gault)
        if crea > 0:
            edad_vfg = calcular_edad(st.session_state.form["fecha_nac"])
            cte = 1.23 if st.session_state.form["sexo_biologico"] == "Masculino" else 1.04
            vfg = ((140 - edad_vfg) * peso * cte) / (72 * crea)
            st.session_state.form["vfg"] = vfg
            st.success(f"VFG Estimado: {vfg:.2f} mL/min")

    st.markdown("---")
    veracidad2 = st.checkbox("Confirmo que toda la información clínica y anamnesis entregada es fidedigna.")

    if st.button("CONTINUAR A CONSENTIMIENTO"):
        if veracidad2: st.session_state.step = 3; st.rerun()
        else: st.error("Debe declarar la veracidad de la información clínica para continuar.")

# --- PASO 3: CONSENTIMIENTO Y FIRMA ---
elif st.session_state.step == 3:
    st.title("🖋️ Consentimiento Informado")
    
    st.markdown("""
    <div class="legal-text">
    <b>AUTORIZACIÓN VOLUNTARIA PARA EXAMEN DE RM</b><br><br>
    Por la presente, yo (o en representación del paciente), autorizo a <b>Norte Imagen</b> a realizar el estudio de Resonancia Magnética. 
    He sido informado que este examen utiliza campos magnéticos intensos y radiofrecuencia. Declaro que he retirado todo objeto 
    metálico de mi vestimenta y cuerpo. <br><br>
    Entiendo que en caso de requerir gadolinio, este será administrado por personal capacitado. Declaro no tener contraindicaciones 
    no informadas en la encuesta anterior. Entiendo que puedo detener el examen en cualquier momento si me siento incómodo. <br><br>
    Toda la información entregada es veraz y asumo la responsabilidad de la omisión de datos relevantes.
    </div>
    """, unsafe_allow_html=True)
    
    st.write("Firme dentro del cuadro blanco:")
    canvas_final = st_canvas(stroke_width=3, stroke_color="#000", background_color="#fff", height=180, width=500, key="c_fin")
    
    veracidad3 = st.checkbox("He leído el consentimiento informado y acepto voluntariamente el procedimiento.")

    if st.button("FINALIZAR REGISTRO"):
        if veracidad3 and canvas_final.image_data is not None:
            st.session_state.form["firma_img"] = Image.fromarray(canvas_final.image_data.astype('uint8'), 'RGBA').convert("RGB")
            st.session_state.step = 4; st.balloons(); st.rerun()
        else: st.error("Debe firmar y aceptar el consentimiento para finalizar.")

# --- PASO 4: DESCARGA ---
elif st.session_state.step == 4:
    f = st.session_state.form
    id_f = re.sub(r'[^a-zA-Z0-9]', '', str(f['rut'] if f['rut'] else f['num_doc']))
    nom_f = f"EC-{f['nombre'].split()[0].upper()}{obtener_iniciales(f['nombre'])}{id_f}"
    
    st.success(f"✅ REGISTRO EXITOSO: {nom_f}")
    pdf_out = generar_pdf_clinico(f)
    
    st.download_button(label=f"📥 DESCARGAR {nom_f}.pdf", data=pdf_out, file_name=f"{nom_f}.pdf", mime="application/pdf")
    
    if st.button("Realizar Nuevo Registro"):
        st.session_state.clear(); st.rerun()
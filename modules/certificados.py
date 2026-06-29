# modules/certificados.py — EMISIÓN DE CERTIFICADOS
import tempfile, os, io
from datetime import datetime, timedelta
import pytz, streamlit as st
import pandas as pd
from norte_imagen_core import (
    PDFNorteImagen, FHIRBuilder,
    generar_id_documento, validar_pin,
)

tz_chile = pytz.timezone("America/Santiago")
_HORAS   = 48

TIPOS_CERT = {
    "ASISTENCIA": "Certificado de Asistencia",
    "SUGERENCIA": "Sugerencia Clínica al Derivador",
    "HISTORICO":  "Certificado de Asistencia Histórico",
}


def render(db, bucket, usuario: dict):
    tab1, tab2, tab3, tab4 = st.tabs([
        "📬 Bandeja Pendientes",
        "📄 Emitir Certificado",
        "🕐 Reingreso Histórico",
        "📊 Historial por Mes",
    ])
    with tab1: _bandeja_pendientes(db, bucket, usuario)
    with tab2: _emitir_certificado(db, bucket, usuario)
    with tab3: _reingreso_historico(db, bucket, usuario)
    with tab4: _historial_mes(db)


# ── TAB 1: BANDEJA ────────────────────────────────────────────────
@st.fragment(run_every=30)
def _bandeja_pendientes(db, bucket, usuario: dict):
    rol = usuario.get("rol","")
    st.markdown(
        "<div style='font-size:12px;color:#64748b;margin-bottom:10px'>"
        "Certificados solicitados por Secretaría esperando validación del TM. "
        "Ventana de emisión: 48 horas desde la validación del examen.</div>",
        unsafe_allow_html=True,
    )
    try:
        docs = (db.collection("certificados_pendientes")
                  .where("estado","==","PENDIENTE_TM")
                  .order_by("fecha_solicitud", direction="DESCENDING")
                  .limit(30).get())
    except Exception as e:
        st.error(f"Error: {e}"); return

    st.session_state["badge_certs"] = len(docs)
    if not docs:
        st.info("✅ Sin certificados pendientes de validación.")
        return

    ahora = datetime.now(tz_chile)
    for doc in docs:
        d      = doc.to_dict()
        nombre = d.get("nombre_paciente","S/N")
        tipo   = TIPOS_CERT.get(d.get("tipo_cert",""), d.get("tipo_cert",""))
        sol_by = d.get("solicitado_por","S/D")
        f_sol  = d.get("fecha_solicitud","")
        enc_id = d.get("encuesta_id","")

        try:
            fv = datetime.strptime(d.get("fecha_validacion",""),"%d/%m/%Y %H:%M:%S")
            fv = tz_chile.localize(fv)
            horas_rest = _HORAS - (ahora - fv).total_seconds()/3600
            dentro_48  = horas_rest > 0
        except Exception:
            horas_rest, dentro_48 = 0, False

        with st.container():
            c_info, c_accion = st.columns([3,1])
            with c_info:
                st.markdown(
                    f"<div style='font-weight:700;font-size:12px'>{nombre}</div>"
                    f"<div style='font-size:10px;color:#64748b'>"
                    f"{tipo} · Solicitado por: {sol_by} · {f_sol}</div>"
                    f"<div style='font-size:10px;color:{'#16a34a' if dentro_48 else '#dc2626'}'>"
                    f"{'✅ Dentro de 48h' if dentro_48 else '⛔ Fuera de 48h'}"
                    f"</div>", unsafe_allow_html=True,
                )
            with c_accion:
                if dentro_48 and rol in ("tm","tm_coordinador","calidad"):
                    if st.button("✏️ Emitir", key=f"em_{doc.id}",
                                 use_container_width=True):
                        st.session_state["cert_pendiente_id"]  = doc.id
                        st.session_state["cert_pendiente_data"] = d
                        st.rerun()
            st.divider()

    # Emitir desde bandeja (si seleccionado)
    if st.session_state.get("cert_pendiente_id"):
        _panel_emision_rapida(db, bucket, usuario,
                              st.session_state.cert_pendiente_id,
                              st.session_state.cert_pendiente_data)


def _panel_emision_rapida(db, bucket, usuario, cert_id, d):
    st.markdown("---")
    st.subheader("Emitir certificado seleccionado")
    enc_id = d.get("encuesta_id","")
    tipo   = d.get("tipo_cert","ASISTENCIA")

    try:
        enc_doc = db.collection("encuestas").document(enc_id).get().to_dict() or {}
    except Exception:
        enc_doc = {}

    _formulario_cert(db, bucket, usuario, enc_doc, tipo,
                     cert_pendiente_id=cert_id)


# ── TAB 2: EMITIR ──────────────────────────────────────────────────
def _emitir_certificado(db, bucket, usuario: dict):
    rol = usuario.get("rol","")
    if rol not in ("tm","tm_coordinador","calidad","secretaria"):
        st.warning("Sin permisos para emitir certificados.")
        return

    tipo_sel = st.selectbox(
        "Tipo de certificado:",
        list(TIPOS_CERT.keys()),
        format_func=lambda x: TIPOS_CERT[x],
        key="tipo_cert_directo",
    )
    rut_busq = st.text_input("RUT del paciente:", key="rut_busq_cert",
                             placeholder="12.345.678-9")

    enc_doc = {}
    if rut_busq and st.button("🔍 Buscar paciente validado", key="buscar_cert"):
        try:
            docs = (db.collection("encuestas")
                      .where("rut","==",rut_busq.strip())
                      .where("encuesta_validada","==",True)
                      .order_by("fecha_validacion",direction="DESCENDING")
                      .limit(1).get())
            if docs:
                enc_doc = docs[0].to_dict()
                st.session_state["cert_enc_encontrado"] = enc_doc
                st.success(f"✅ Paciente encontrado: {enc_doc.get('nombre','')}")
            else:
                st.warning("Paciente no encontrado o no validado.")
                return
        except Exception as e:
            st.error(f"Error: {e}"); return

    enc_doc = st.session_state.get("cert_enc_encontrado", enc_doc)
    if enc_doc:
        _formulario_cert(db, bucket, usuario, enc_doc, tipo_sel)


def _formulario_cert(db, bucket, usuario, enc_doc, tipo,
                     cert_pendiente_id=None):
    nombre  = enc_doc.get("nombre","")
    rut     = enc_doc.get("rut","") or enc_doc.get("num_doc","")
    proc    = enc_doc.get("procedimiento","")
    f_valid = enc_doc.get("fecha_validacion","")

    st.markdown(
        f"<div style='background:#f0fdf4;border:1px solid #bbf7d0;"
        f"border-radius:7px;padding:9px 12px;font-size:11px;margin-bottom:10px'>"
        f"<strong>{nombre}</strong> · RUT: {rut} · {proc} · Validado: {f_valid}"
        f"</div>", unsafe_allow_html=True,
    )

    # Campos específicos por tipo
    h_llegada, h_salida, texto_libre = "", "", ""
    if tipo in ("ASISTENCIA","HISTORICO"):
        c1, c2 = st.columns(2)
        h_llegada = c1.text_input("Hora llegada:", key="cert_llegada",
                                  placeholder="09:30")
        h_salida  = c2.text_input("Hora salida:", key="cert_salida",
                                  placeholder="11:05")
    if tipo == "SUGERENCIA":
        texto_libre = st.text_area(
            "Texto de la sugerencia clínica:",
            height=100, key="cert_sugerencia",
            placeholder="Se sugiere control de…",
        )

    obs = st.text_area("Observaciones (opcional):",
                       height=70, key="cert_obs", value="")

    st.markdown("---")
    pin_c = st.text_input("PIN de autorización:", type="password",
                          key="pin_cert", label_visibility="visible")

    if st.button("🖨️ GENERAR PDF Y FIRMAR", type="primary",
                 use_container_width=True):
        if tipo in ("ASISTENCIA","HISTORICO") and not all([h_llegada, h_salida]):
            st.error("Ingrese horarios de llegada y salida."); return
        if tipo == "SUGERENCIA" and not texto_libre.strip():
            st.error("Escriba el texto de la sugerencia clínica."); return
        if not validar_pin(pin_c, usuario.get("hash","")):
            st.error("❌ PIN incorrecto."); return

        _generar_y_guardar_cert(db, bucket, usuario, enc_doc, tipo,
                                h_llegada, h_salida, texto_libre, obs,
                                cert_pendiente_id)


def _generar_y_guardar_cert(db, bucket, usuario, enc_doc, tipo,
                             h_llegada, h_salida, texto_libre, obs,
                             cert_pendiente_id):
    ahora_str = datetime.now(tz_chile).strftime("%d/%m/%Y %H:%M:%S")
    _, id_v, nombre_pdf = generar_id_documento(
        tipo, db, enc_doc.get("nombre",""), enc_doc.get("rut",""),
    )
    rut = enc_doc.get("rut","") or enc_doc.get("num_doc","")

    pdf = PDFNorteImagen(tipo, config={
        "id_verificacion": id_v,
        "rut_paciente":    rut,
        "nombre_paciente": enc_doc.get("nombre",""),
    })
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=12)

    pdf.section_title("1","DATOS DEL PACIENTE")
    pdf.data_field_2col([
        ("Nombre",    enc_doc.get("nombre","")),
        ("RUT/Doc",   rut),
        ("Edad",      enc_doc.get("edad","")),
        ("Examen",    enc_doc.get("procedimiento","")),
    ])

    if tipo in ("ASISTENCIA","HISTORICO"):
        pdf.section_title("2","REGISTRO DE ASISTENCIA")
        pdf.tabla_horarios(h_llegada, h_salida)

    if tipo == "SUGERENCIA":
        pdf.section_title("2","SUGERENCIA CLÍNICA")
        pdf.cuerpo(texto_libre)

    if obs.strip():
        pdf.section_title("3","OBSERVACIONES")
        pdf.cuerpo(obs)

    huella = pdf.estampar_sello_digital(
        usuario.get("nombre",""), usuario.get("sis",""),
        usuario.get("rol","tm"), ahora_str,
    )
    pdf_bytes = pdf.compilar()

    # Guardar en Firestore + Storage
    ahora_iso = datetime.now(tz_chile).isoformat()
    doc_ref   = FHIRBuilder.bundle(
        tipo, id_v,
        [FHIRBuilder.patient(enc_doc, enc_doc.get("uuid_sesion","x"))],
        ahora_iso,
    )
    try:
        db.collection("certificados_emitidos").add({
            "tipo":             tipo,
            "id_verificacion":  id_v,
            "nombre_paciente":  enc_doc.get("nombre",""),
            "rut_paciente":     rut,
            "encuesta_id":      enc_doc.get("uuid_sesion",""),
            "emitido_por":      usuario.get("nombre",""),
            "sis":              usuario.get("sis",""),
            "rol":              usuario.get("rol",""),
            "fecha_emision":    ahora_str,
            "huella_sha256":    huella,
            "fhir_doc_ref":     doc_ref,
            "hora_llegada":     h_llegada,
            "hora_salida":      h_salida,
        })
        if cert_pendiente_id:
            db.collection("certificados_pendientes").document(
                cert_pendiente_id
            ).update({"estado":"EMITIDO","fecha_emision":ahora_str})

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tp:
            tp.write(pdf_bytes)
            bucket.blob(f"certificados/{nombre_pdf}").upload_from_filename(
                tp.name, content_type="application/pdf",
            )
        os.unlink(tp.name)

        if "cert_enc_encontrado" in st.session_state:
            del st.session_state["cert_enc_encontrado"]
        if "cert_pendiente_id" in st.session_state:
            del st.session_state["cert_pendiente_id"]
        st.session_state["badge_certs"] = max(
            0, st.session_state.get("badge_certs",0)-1
        )
        st.success(f"✅ {TIPOS_CERT.get(tipo,tipo)} generado correctamente.")
    except Exception as e:
        st.error(f"Error al guardar: {e}"); return

    st.download_button("📥 Descargar PDF",
                       data=pdf_bytes, file_name=nombre_pdf,
                       mime="application/pdf", use_container_width=True)


# ── TAB 3: REINGRESO HISTÓRICO ────────────────────────────────────
def _reingreso_historico(db, bucket, usuario: dict):
    st.markdown(
        "<div style='background:#fffbeb;border:1px solid #fde68a;"
        "border-radius:7px;padding:9px 12px;font-size:11px;color:#92400e;"
        "margin-bottom:12px'>"
        "⚠️ Reingreso fuera de la ventana de 48h. Solo para Certificado de Asistencia "
        "Histórico. Requiere justificación y registro en trazabilidad.</div>",
        unsafe_allow_html=True,
    )
    rut  = st.text_input("RUT del paciente:", key="rut_historico")
    just = st.text_area("Justificación del reingreso:", height=70,
                        key="just_historico")
    pin  = st.text_input("PIN:", type="password", key="pin_historico")

    enc_doc = {}
    if rut and st.button("🔍 Buscar en historial", key="buscar_hist"):
        try:
            docs = (db.collection("encuestas")
                      .where("rut","==",rut.strip())
                      .where("encuesta_validada","==",True)
                      .order_by("fecha_validacion",direction="DESCENDING")
                      .limit(5).get())
            if docs:
                enc_doc = docs[0].to_dict()
                st.session_state["hist_enc"] = enc_doc
                st.success(f"✅ {enc_doc.get('nombre','')} — "
                           f"Validado: {enc_doc.get('fecha_validacion','')}")
            else:
                st.warning("Paciente no encontrado.")
        except Exception as e:
            st.error(f"Error: {e}")

    enc_doc = st.session_state.get("hist_enc", enc_doc)
    if enc_doc and st.button("📄 GENERAR CERTIFICADO HISTÓRICO",
                              type="primary", use_container_width=True):
        if not just.strip():
            st.error("Ingrese la justificación del reingreso."); return
        if not validar_pin(pin, usuario.get("hash","")):
            st.error("❌ PIN incorrecto."); return
        _generar_y_guardar_cert(db, bucket, usuario, enc_doc,
                                "HISTORICO", "", "", just, "", None)
        if "hist_enc" in st.session_state:
            del st.session_state["hist_enc"]


# ── TAB 4: HISTORIAL POR MES ──────────────────────────────────────
def _historial_mes(db):
    import calendar
    ahora = datetime.now(tz_chile)
    meses = [(datetime(ahora.year, m, 1).strftime("%B %Y"), m, ahora.year)
             for m in range(ahora.month, 0, -1)]
    for m_prev in range(1, 4):
        anio = ahora.year - 1 if ahora.month - m_prev <= 0 else ahora.year
        mes  = (ahora.month - m_prev) % 12 or 12
        meses.append((datetime(anio, mes, 1).strftime("%B %Y"), mes, anio))

    mes_sel = st.selectbox("Período:", [m[0] for m in meses], key="mes_hist_cert")
    _, mes_n, anio_n = next(m for m in meses if m[0] == mes_sel)

    f_ini = datetime(anio_n, mes_n, 1, tzinfo=tz_chile)
    f_fin = datetime(anio_n, mes_n,
                     calendar.monthrange(anio_n, mes_n)[1],
                     23, 59, 59, tzinfo=tz_chile)

    try:
        docs = (db.collection("certificados_emitidos")
                  .order_by("fecha_emision", direction="DESCENDING")
                  .limit(200).get())
    except Exception as e:
        st.error(f"Error: {e}"); return

    filas = []
    for doc in docs:
        d = doc.to_dict()
        try:
            fe = datetime.strptime(d.get("fecha_emision",""),"%d/%m/%Y %H:%M:%S")
            fe = tz_chile.localize(fe)
            if f_ini <= fe <= f_fin:
                filas.append({
                    "Fecha/Hora":  d.get("fecha_emision",""),
                    "Paciente":    d.get("nombre_paciente",""),
                    "RUT":         d.get("rut_paciente",""),
                    "Tipo":        TIPOS_CERT.get(d.get("tipo",""), d.get("tipo","")),
                    "Profesional": d.get("emitido_por",""),
                    "ID Verif.":   d.get("id_verificacion",""),
                })
        except Exception:
            pass

    st.markdown(
        f"<div style='font-size:12px;color:#475569;margin-bottom:8px'>"
        f"<strong>{len(filas)}</strong> certificados emitidos en {mes_sel}</div>",
        unsafe_allow_html=True,
    )

    if filas:
        df = pd.DataFrame(filas)
        st.dataframe(df, use_container_width=True, hide_index=True,
                     height=280)

        # Descargar como CSV
        csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            f"⬇️ Descargar historial {mes_sel} (.csv)",
            data=csv_bytes,
            file_name=f"certificados_{mes_n:02d}_{anio_n}.csv",
            mime="text/csv", use_container_width=True,
        )
    else:
        st.info(f"Sin certificados emitidos en {mes_sel}.")

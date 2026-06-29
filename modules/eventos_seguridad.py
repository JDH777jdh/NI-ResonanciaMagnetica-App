# modules/eventos_seguridad.py — EVENTOS DE SEGURIDAD GCL 2.3 MINSAL
import tempfile, os, calendar
from datetime import datetime
import pytz, streamlit as st
import pandas as pd
from norte_imagen_core import (
    PDFNorteImagen, FHIRBuilder, generar_id_documento, validar_pin,
)

tz_chile = pytz.timezone("America/Santiago")

_TIPOS = ["Incidente Clínico","Cuasi-incidente","Evento Adverso",
          "No conformidad de proceso","Queja / Reclamo","Otro"]
_AREAS = ["Sala RM 1","Sala RM 2","Recepción / Admisión",
          "Bodega / Insumos","Farmacología","Administración","Otro"]
_GRAVEDADES = ["Leve","Moderado","Grave","Catastrófico"]
_ESTADOS_FILTRO = ["Todos","PENDIENTE_VALIDACION","VALIDADO","CERRADO"]


def render(db, bucket, usuario: dict):
    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ Registrar Evento",
        "✅ Validar Evento",
        "📋 Historial GCL 2.3",
        "📊 Consolidado Mensual",
    ])
    with tab1: _registrar_evento(db, usuario)
    with tab2: _validar_evento(db, bucket, usuario)
    with tab3: _historial_eventos(db)
    with tab4: _consolidado_mensual(db, bucket, usuario)


# ── TAB 1: REGISTRAR ──────────────────────────────────────────────
def _registrar_evento(db, usuario: dict):
    st.markdown(
        "<div style='font-size:12px;color:#64748b;margin-bottom:10px'>"
        "Registre cualquier incidente, cuasi-incidente o no conformidad "
        "detectado durante la atención. Se generará folio GCL 2.3 automáticamente."
        "</div>", unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    tipo      = c1.selectbox("Tipo de evento:", _TIPOS, key="ev_tipo")
    area      = c2.selectbox("Área involucrada:", _AREAS, key="ev_area")
    gravedad  = c1.selectbox("Gravedad:", _GRAVEDADES, key="ev_grav")
    fecha_ev  = c2.date_input("Fecha del evento:", key="ev_fecha")

    descripcion = st.text_area(
        "Descripción objetiva del evento:",
        height=100, key="ev_desc",
        placeholder="Describa los hechos de forma objetiva, sin juicios de valor…",
    )
    causa = st.text_area(
        "Causa raíz probable (si se conoce):",
        height=70, key="ev_causa",
        placeholder="Ej: Falla en protocolo de verificación de implantes…",
    )
    medidas = st.text_area(
        "Medidas inmediatas tomadas:",
        height=70, key="ev_medidas",
        placeholder="Ej: Se suspendió el examen, se notificó al coordinador…",
    )

    # Paciente involucrado (opcional)
    st.markdown("**Paciente involucrado (si aplica):**")
    c3, c4 = st.columns(2)
    pac_nombre = c3.text_input("Nombre paciente:", key="ev_pac_nom")
    pac_rut    = c4.text_input("RUT paciente:", key="ev_pac_rut")

    st.markdown("---")
    pin = st.text_input("PIN de autorización:", type="password", key="pin_ev_reg")

    col_a, col_b = st.columns(2)
    if col_a.button("📝 REGISTRAR Y GENERAR FOLIO GCL",
                    type="primary", use_container_width=True):
        if not descripcion.strip():
            st.error("La descripción del evento es obligatoria."); return
        if not validar_pin(pin, usuario.get("hash","")):
            st.error("❌ PIN incorrecto."); return
        _guardar_evento(db, usuario, tipo, area, gravedad,
                        str(fecha_ev), descripcion, causa,
                        medidas, pac_nombre, pac_rut)

    if col_b.button("🔄 Limpiar formulario", use_container_width=True):
        for k in ["ev_desc","ev_causa","ev_medidas","ev_pac_nom","ev_pac_rut"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()


def _guardar_evento(db, usuario, tipo, area, gravedad,
                    fecha_ev, descripcion, causa, medidas,
                    pac_nombre, pac_rut):
    ahora_str = datetime.now(tz_chile).strftime("%d/%m/%Y %H:%M:%S")
    ahora_iso = datetime.now(tz_chile).isoformat()
    _, id_v, _ = generar_id_documento("INCIDENTE", db)

    # AdverseEvent + AuditEvent FHIR
    adverse = FHIRBuilder.adverse_event(
        tipo, gravedad, descripcion,
        usuario.get("nombre",""),
        pac_rut or "anonimo",
        ahora_iso,
    )
    audit = FHIRBuilder.audit_event(
        "EVENTO_REGISTRADO",
        usuario.get("nombre",""), usuario.get("sis",""),
        pac_rut or "anonimo", ahora_iso,
        f"Folio: {id_v} | Tipo: {tipo} | Área: {area}",
    )
    try:
        db.collection("eventos_seguridad").document(id_v).set({
            "folio":            id_v,
            "tipo":             tipo,
            "area":             area,
            "gravedad":         gravedad,
            "fecha_evento":     fecha_ev,
            "descripcion":      descripcion,
            "causa_raiz":       causa,
            "medidas_inmediatas": medidas,
            "paciente_nombre":  pac_nombre,
            "paciente_rut":     pac_rut,
            "registrado_por":   usuario.get("nombre",""),
            "sis_registrador":  usuario.get("sis",""),
            "rol_registrador":  usuario.get("rol",""),
            "fecha_registro":   ahora_str,
            "estado":           "PENDIENTE_VALIDACION",
            "fhir_adverse":     adverse,
            "fhir_audit":       audit,
        })
        db.collection("trazabilidad").add({
            "modulo":       "eventos_seguridad",
            "accion":       "EVENTO_REGISTRADO",
            "profesional":  usuario.get("nombre",""),
            "sis":          usuario.get("sis",""),
            "rol":          usuario.get("rol",""),
            "rut_paciente": pac_rut,
            "detalle":      f"Folio GCL: {id_v} | Tipo: {tipo} | Gravedad: {gravedad}",
            "timestamp":    ahora_iso,
        })
        st.session_state["badge_eventos"] = (
            st.session_state.get("badge_eventos",0) + 1
        )
        st.success(
            f"✅ Evento registrado · Folio GCL: **{id_v}**\n\n"
            f"Notifique al coordinador o encargado de calidad."
        )
    except Exception as e:
        st.error(f"Error al guardar: {e}")


# ── TAB 2: VALIDAR ────────────────────────────────────────────────
def _validar_evento(db, bucket, usuario: dict):
    rol = usuario.get("rol","")
    if rol not in ("tm_coordinador","radiologo_coordinador",
                   "medico_coordinador","calidad","owner"):
        st.warning("Solo coordinadores y calidad pueden validar eventos."); return

    try:
        docs = (db.collection("eventos_seguridad")
                  .where("estado","==","PENDIENTE_VALIDACION")
                  .order_by("fecha_registro", direction="DESCENDING")
                  .limit(30).get())
    except Exception as e:
        st.error(f"Error: {e}"); return

    st.session_state["badge_eventos"] = len(docs)

    if not docs:
        st.info("✅ Sin eventos pendientes de validación.")
        return

    opts = {doc.id: f"{doc.id} — {doc.to_dict().get('tipo','')} "
                    f"({doc.to_dict().get('gravedad','')})" for doc in docs}
    sel  = st.selectbox("Evento a validar:", list(opts.keys()),
                         format_func=lambda x: opts[x], key="ev_sel_val")
    ev   = next(d.to_dict() for d in docs if d.id == sel)

    # Detalle del evento
    _card_evento(ev)

    analisis  = st.text_area("Análisis de causa raíz (validación):",
                              height=90, key="ev_analisis")
    acciones  = st.text_area("Plan de mejora / acciones correctivas:",
                              height=90, key="ev_acciones")
    cierre    = st.selectbox("Estado tras validación:",
                              ["VALIDADO","CERRADO"], key="ev_cierre")
    pin_val   = st.text_input("PIN:", type="password", key="pin_ev_val")

    if st.button("✅ VALIDAR EVENTO Y GENERAR PDF",
                 type="primary", use_container_width=True):
        if not analisis.strip():
            st.error("Ingrese el análisis de causa raíz."); return
        if not validar_pin(pin_val, usuario.get("hash","")):
            st.error("❌ PIN incorrecto."); return
        _procesar_validacion_evento(db, bucket, usuario, sel, ev,
                                    analisis, acciones, cierre)


def _card_evento(ev: dict):
    color  = {"Leve":"#16a34a","Moderado":"#d97706",
               "Grave":"#dc2626","Catastrófico":"#7f1d1d"}.get(
                   ev.get("gravedad","Leve"),"#374151")
    st.markdown(
        f"<div style='background:#f8fafc;border:1px solid #e2e8f0;"
        f"border-left:4px solid {color};border-radius:7px;"
        f"padding:10px 12px;font-size:11px;margin-bottom:10px'>"
        f"<strong>Folio:</strong> {ev.get('folio','')} &nbsp;·&nbsp; "
        f"<strong>Tipo:</strong> {ev.get('tipo','')} &nbsp;·&nbsp; "
        f"<span style='color:{color};font-weight:700'>{ev.get('gravedad','')}</span><br>"
        f"<strong>Área:</strong> {ev.get('area','')} &nbsp;·&nbsp; "
        f"<strong>Fecha evento:</strong> {ev.get('fecha_evento','')} &nbsp;·&nbsp; "
        f"<strong>Registrado:</strong> {ev.get('registrado_por','')} — "
        f"{ev.get('fecha_registro','')}<br>"
        f"<strong>Descripción:</strong> {ev.get('descripcion','')}<br>"
        f"{'<strong>Causa probable:</strong> '+ev.get('causa_raiz','') if ev.get('causa_raiz') else ''}"
        f"</div>", unsafe_allow_html=True,
    )


def _procesar_validacion_evento(db, bucket, usuario, ev_id, ev,
                                analisis, acciones, cierre):
    ahora_str = datetime.now(tz_chile).strftime("%d/%m/%Y %H:%M:%S")
    ahora_iso = datetime.now(tz_chile).isoformat()
    folio     = ev.get("folio", ev_id)

    # PDF del reporte
    pdf = PDFNorteImagen("INCIDENTE", config={
        "id_verificacion": folio,
        "folio": folio,
    })
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=12)

    pdf.section_title_dark(f"REPORTE DE EVENTO DE SEGURIDAD — Folio: {folio}")
    pdf.data_field_2col([
        ("Tipo",     ev.get("tipo","")),
        ("Gravedad", ev.get("gravedad","")),
        ("Área",     ev.get("area","")),
        ("Fecha",    ev.get("fecha_evento","")),
    ])
    pdf.section_title("1","DESCRIPCIÓN DEL EVENTO")
    pdf.cuerpo(ev.get("descripcion",""))
    if ev.get("causa_raiz"):
        pdf.section_title("2","CAUSA RAÍZ PROBABLE")
        pdf.cuerpo(ev.get("causa_raiz",""))
    if ev.get("medidas_inmediatas"):
        pdf.section_title("3","MEDIDAS INMEDIATAS TOMADAS")
        pdf.cuerpo(ev.get("medidas_inmediatas",""))
    pdf.section_title("4","ANÁLISIS DE VALIDACIÓN")
    pdf.cuerpo(analisis)
    if acciones.strip():
        pdf.section_title("5","PLAN DE MEJORA / ACCIONES CORRECTIVAS")
        pdf.cuerpo(acciones)
    if ev.get("paciente_nombre"):
        pdf.section_title("6","PACIENTE INVOLUCRADO")
        pdf.data_field("Nombre", ev["paciente_nombre"])
        pdf.data_field("RUT",    ev.get("paciente_rut",""))

    huella = pdf.estampar_sello_digital(
        usuario.get("nombre",""), usuario.get("sis",""),
        usuario.get("rol","calidad"), ahora_str,
    )
    pdf_bytes = pdf.compilar()
    nombre_pdf = f"EV-SEG-{folio}-{ahora_str[:10].replace('/','')}.pdf"

    audit = FHIRBuilder.audit_event(
        "VALIDACION_EVENTO", usuario.get("nombre",""),
        usuario.get("sis",""), ev.get("paciente_rut","anonimo"),
        ahora_iso, f"Folio {folio} validado — Estado: {cierre}",
    )
    try:
        db.collection("eventos_seguridad").document(ev_id).update({
            "estado":              cierre,
            "analisis_validacion": analisis,
            "plan_mejora":         acciones,
            "validado_por":        usuario.get("nombre",""),
            "sis_validador":       usuario.get("sis",""),
            "fecha_validacion":    ahora_str,
            "huella_sha256":       huella,
            "fhir_audit_val":      audit,
        })
        db.collection("trazabilidad").add({
            "modulo":       "eventos_seguridad",
            "accion":       "VALIDACION_EVENTO",
            "profesional":  usuario.get("nombre",""),
            "sis":          usuario.get("sis",""),
            "rol":          usuario.get("rol",""),
            "rut_paciente": ev.get("paciente_rut",""),
            "detalle":      f"Folio {folio} — Estado: {cierre}",
            "timestamp":    ahora_iso,
        })
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tp:
            tp.write(pdf_bytes)
            bucket.blob(f"eventos/{nombre_pdf}").upload_from_filename(
                tp.name, content_type="application/pdf",
            )
        os.unlink(tp.name)
        st.session_state["badge_eventos"] = max(
            0, st.session_state.get("badge_eventos",0)-1
        )
        st.success(f"✅ Evento validado · Estado: {cierre}")
    except Exception as e:
        st.error(f"Error: {e}"); return

    st.download_button("📥 Descargar Reporte PDF",
                       data=pdf_bytes, file_name=nombre_pdf,
                       mime="application/pdf", use_container_width=True)


# ── TAB 3: HISTORIAL ──────────────────────────────────────────────
def _historial_eventos(db):
    c1, c2 = st.columns(2)
    filtro  = c1.text_input("🔍 Buscar:", key="filt_ev_hist",
                             placeholder="Folio, tipo, área…",
                             label_visibility="collapsed")
    estado  = c2.selectbox("Estado:", _ESTADOS_FILTRO, key="ev_est_filt")

    try:
        query = db.collection("eventos_seguridad").order_by(
            "fecha_registro", direction="DESCENDING"
        ).limit(150)
        if estado != "Todos":
            query = db.collection("eventos_seguridad").where(
                "estado","==",estado
            ).order_by("fecha_registro",direction="DESCENDING").limit(150)
        docs = query.get()
    except Exception as e:
        st.error(f"Error: {e}"); return

    filas = []
    for doc in docs:
        d = doc.to_dict()
        if filtro and filtro.lower() not in " ".join([
            d.get("folio",""), d.get("tipo",""), d.get("area",""),
            d.get("descripcion","")
        ]).lower():
            continue
        grav   = d.get("gravedad","")
        emoji  = {"Leve":"🟢","Moderado":"🟡","Grave":"🔴",
                  "Catastrófico":"⛔"}.get(grav,"⚪")
        filas.append({
            "Folio":     d.get("folio",""),
            "Tipo":      d.get("tipo",""),
            "Área":      d.get("area",""),
            "Gravedad":  f"{emoji} {grav}",
            "Estado":    d.get("estado",""),
            "Fecha":     d.get("fecha_evento",""),
            "Registrado":d.get("registrado_por",""),
        })

    st.markdown(
        f"<div style='font-size:11px;color:#475569;margin-bottom:6px'>"
        f"<strong>{len(filas)}</strong> eventos encontrados</div>",
        unsafe_allow_html=True,
    )
    if filas:
        df = pd.DataFrame(filas)
        st.dataframe(df, use_container_width=True, hide_index=True, height=350)
        st.download_button("⬇️ Exportar CSV",
                           data=df.to_csv(index=False).encode("utf-8-sig"),
                           file_name="historial_eventos_gcl.csv",
                           mime="text/csv", use_container_width=True)
    else:
        st.info("Sin eventos para los filtros seleccionados.")


# ── TAB 4: CONSOLIDADO MENSUAL ────────────────────────────────────
def _consolidado_mensual(db, bucket, usuario: dict):
    rol = usuario.get("rol","")
    if rol not in ("tm_coordinador","radiologo_coordinador",
                   "medico_coordinador","calidad","owner"):
        st.warning("Solo coordinadores y calidad pueden generar el consolidado."); return

    ahora   = datetime.now(tz_chile)
    periodo = st.text_input("Período:", value=ahora.strftime("%B %Y"),
                             key="periodo_ev")
    pin     = st.text_input("PIN:", type="password", key="pin_cons_ev")

    if st.button("📊 GENERAR CONSOLIDADO GCL 2.3",
                 type="primary", use_container_width=True):
        if not validar_pin(pin, usuario.get("hash","")):
            st.error("❌ PIN incorrecto."); return
        try:
            docs  = (db.collection("eventos_seguridad")
                       .order_by("fecha_registro",direction="DESCENDING")
                       .limit(300).get())
            filas = []
            resumen = {t: 0 for t in _TIPOS}
            for doc in docs:
                d = doc.to_dict()
                tipo_ev = d.get("tipo","Otro")
                resumen[tipo_ev] = resumen.get(tipo_ev,0) + 1
                filas.append([
                    d.get("folio",""), d.get("tipo",""),
                    d.get("area",""), d.get("gravedad",""),
                    d.get("estado",""), d.get("fecha_evento",""),
                    d.get("registrado_por",""),
                ])
        except Exception as e:
            st.error(f"Error: {e}"); return

        ahora_str = ahora.strftime("%d/%m/%Y %H:%M:%S")
        _, id_v, nombre_pdf = generar_id_documento("REPORTE_GCL", db)

        pdf = PDFNorteImagen("REPORTE_GCL", config={
            "id_verificacion": id_v,
            "periodo": periodo,
        })
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.section_title_dark(f"CONSOLIDADO GCL 2.3 — {periodo}")

        # Resumen por tipo
        pdf.section_title("1","RESUMEN POR TIPO DE EVENTO")
        for tipo_r, count in resumen.items():
            if count > 0:
                pdf.data_field(tipo_r, str(count))

        # Detalle
        pdf.section_title("2","DETALLE DE EVENTOS")
        pdf.tabla(
            ["Folio","Tipo","Área","Gravedad","Estado","Fecha","Registrador"],
            filas, anchos=[22,32,24,18,22,18,24],
        )
        pdf.estampar_sello_digital(
            usuario.get("nombre",""), usuario.get("sis",""),
            usuario.get("rol","calidad"), ahora_str,
        )
        pdf_bytes = pdf.compilar()
        st.download_button("⬇️ Descargar Consolidado PDF",
                           data=pdf_bytes, file_name=nombre_pdf,
                           mime="application/pdf", use_container_width=True)

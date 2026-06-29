# modules/farmacos.py — GESTIÓN MÉDICA DE FÁRMACOS
import tempfile, os
from datetime import datetime
import pytz, streamlit as st
import pandas as pd
from norte_imagen_core import (
    PDFNorteImagen, FHIRBuilder, generar_id_documento, validar_pin,
)

tz_chile = pytz.timezone("America/Santiago")


def render(db, bucket, usuario: dict):
    tab1, tab2, tab3, tab4 = st.tabs([
        "🩺 Triaje TM/TENS",
        "👨‍⚕️ Validar y Emitir Receta",
        "📋 Historial Recetas",
        "📊 Balance Mensual",
    ])
    with tab1: _triaje(db, usuario)
    with tab2: _validar_receta(db, bucket, usuario)
    with tab3: _historial(db)
    with tab4: _balance_mensual(db, bucket, usuario)


def _triaje(db, usuario: dict):
    rol = usuario.get("rol","")
    if rol not in ("tm","tm_coordinador","tens","calidad","owner"):
        st.warning("Sin permisos para triaje."); return

    st.markdown(
        "<div style='font-size:12px;color:#64748b;margin-bottom:10px'>"
        "Seleccione al paciente validado, complete el triaje farmacológico "
        "y envíe al médico para prescripción.</div>", unsafe_allow_html=True,
    )
    rut_busq = st.text_input("RUT del paciente:", key="rut_farm",
                              placeholder="12.345.678-9")
    enc_doc  = {}
    if rut_busq and st.button("🔍 Buscar", key="buscar_farm"):
        try:
            docs = (db.collection("encuestas")
                      .where("rut","==",rut_busq.strip())
                      .where("encuesta_validada","==",True)
                      .order_by("fecha_validacion",direction="DESCENDING")
                      .limit(1).get())
            if docs:
                enc_doc = docs[0].to_dict()
                st.session_state["farm_enc"] = enc_doc
                st.success(f"✅ {enc_doc.get('nombre','')}")
            else:
                st.warning("Paciente no encontrado o no validado.")
        except Exception as e:
            st.error(f"Error: {e}")

    enc_doc = st.session_state.get("farm_enc", enc_doc)
    if not enc_doc:
        return

    # Datos del paciente
    vfg   = float(enc_doc.get("vfg",0))
    crea  = float(enc_doc.get("creatinina",0))
    st.markdown(
        f"<div style='background:#f8fafc;border:1px solid #e2e8f0;"
        f"border-radius:7px;padding:9px 12px;font-size:11px;margin-bottom:10px'>"
        f"<strong>{enc_doc.get('nombre','')}</strong> · RUT: "
        f"{enc_doc.get('rut','S/D')} · "
        f"VFG: <strong style='color:{'#dc2626' if vfg<=30 else '#d97706' if vfg<=59 else '#16a34a'}'>"
        f"{vfg:.1f} ml/min</strong> · Creatinina: {crea} mg/dL"
        f"</div>", unsafe_allow_html=True,
    )

    # CIE-10 / CIE-11
    cie10 = st.text_input("Código CIE-10:", key="farm_cie10",
                           placeholder="Ej: M23.2")
    cie10_desc = st.text_input("Descripción CIE-10:", key="farm_cie10d",
                                placeholder="Ej: Lesión meniscal rodilla")
    cie11 = st.text_input("Código CIE-11 (opcional):", key="farm_cie11",
                           placeholder="Ej: FB83")

    # Fármaco
    st.markdown("**Fármaco / Insumo a administrar:**")
    c1,c2,c3 = st.columns([2,1,1])
    farmaco   = c1.text_input("Nombre:", key="farm_nom")
    dosis     = c2.text_input("Dosis:", key="farm_dos")
    via       = c3.text_input("Vía:", key="farm_via")
    obs_farm  = st.text_area("Observaciones del triaje:", height=70,
                              key="farm_obs")

    if vfg > 0 and vfg <= 59:
        st.markdown(
            "<div style='background:#fffbeb;border:1px solid #fde68a;"
            "border-radius:6px;padding:8px;font-size:11px;color:#92400e;margin:6px 0'>"
            "⚠️ VFG reducida — Verifique ajuste de dosis en insuficiencia renal "
            "antes de enviar al médico.</div>", unsafe_allow_html=True,
        )

    pin = st.text_input("PIN TM/TENS:", type="password", key="pin_triaje")
    if st.button("📤 ENVIAR A MÉDICO PARA VALIDAR",
                 type="primary", use_container_width=True):
        if not all([farmaco, dosis, cie10, cie10_desc]):
            st.error("Complete fármaco, dosis y diagnóstico CIE-10."); return
        if not validar_pin(pin, usuario.get("hash","")):
            st.error("❌ PIN incorrecto."); return
        ahora = datetime.now(tz_chile).strftime("%d/%m/%Y %H:%M:%S")
        try:
            db.collection("triajes_farmacos").add({
                "encuesta_id":  enc_doc.get("uuid_sesion",""),
                "nombre":       enc_doc.get("nombre",""),
                "rut":          enc_doc.get("rut",""),
                "vfg":          vfg,
                "creatinina":   crea,
                "cie10":        cie10, "cie10_desc": cie10_desc, "cie11": cie11,
                "farmaco":      farmaco, "dosis": dosis, "via": via,
                "observaciones":obs_farm,
                "tm":           usuario.get("nombre",""),
                "sis_tm":       usuario.get("sis",""),
                "estado":       "PENDIENTE_MEDICO",
                "fecha":        ahora,
            })
            if "farm_enc" in st.session_state:
                del st.session_state["farm_enc"]
            st.success(f"✅ Triaje enviado al médico radiólogo.")
            st.session_state["badge_farmacos"] = (
                st.session_state.get("badge_farmacos",0) + 1
            )
        except Exception as e:
            st.error(f"Error: {e}")


def _validar_receta(db, bucket, usuario: dict):
    rol = usuario.get("rol","")
    if rol not in ("radiologo","radiologo_coordinador","medico_coordinador","owner"):
        st.warning("Solo médicos radiólogos pueden emitir recetas."); return

    try:
        docs = (db.collection("triajes_farmacos")
                  .where("estado","==","PENDIENTE_MEDICO")
                  .order_by("fecha", direction="DESCENDING")
                  .limit(20).get())
    except Exception as e:
        st.error(f"Error: {e}"); return

    st.session_state["badge_farmacos"] = len(docs)

    if not docs:
        st.info("✅ Sin triajes pendientes de validación médica.")
        return

    opts = {doc.id: f"{doc.to_dict().get('nombre','')} — "
                    f"{doc.to_dict().get('farmaco','')}"
            for doc in docs}
    sel  = st.selectbox("Triaje a validar:", list(opts.keys()),
                         format_func=lambda x: opts[x], key="sel_triaje")

    sel_doc = next(d.to_dict() for d in docs if d.id == sel)
    vfg     = float(sel_doc.get("vfg",0))

    st.markdown(
        f"<div style='background:#f0fdf4;border:1px solid #bbf7d0;"
        f"border-radius:7px;padding:9px 12px;font-size:11px;margin-bottom:10px'>"
        f"<strong>{sel_doc.get('nombre','')}</strong> · RUT: {sel_doc.get('rut','S/D')}<br>"
        f"CIE-10: {sel_doc.get('cie10','')} — {sel_doc.get('cie10_desc','')}<br>"
        f"Fármaco: <strong>{sel_doc.get('farmaco','')} {sel_doc.get('dosis','')}"
        f" · Vía: {sel_doc.get('via','')}</strong><br>"
        f"VFG: {vfg:.1f} ml/min · Creatinina: {sel_doc.get('creatinina',0)} mg/dL<br>"
        f"Triaje por: {sel_doc.get('tm','')} · {sel_doc.get('fecha','')}"
        f"</div>", unsafe_allow_html=True,
    )

    indicaciones = st.text_area("Indicaciones médicas adicionales:",
                                 height=80, key="indicaciones_med")
    pin_med = st.text_input("PIN Médico:", type="password", key="pin_medico")

    if st.button("💊 VALIDAR Y EMITIR RECETA", type="primary",
                 use_container_width=True):
        if not validar_pin(pin_med, usuario.get("hash","")):
            st.error("❌ PIN incorrecto."); return
        _emitir_receta(db, bucket, usuario, sel, sel_doc, indicaciones)


def _emitir_receta(db, bucket, usuario, triaje_id, td, indicaciones):
    ahora_str = datetime.now(tz_chile).strftime("%d/%m/%Y %H:%M:%S")
    _, id_v, nombre_pdf = generar_id_documento("RECETA", db,
                                               td.get("nombre",""),
                                               td.get("rut",""))
    pdf = PDFNorteImagen("RECETA", config={
        "id_verificacion": id_v,
        "rut_paciente":    td.get("rut",""),
        "nombre_paciente": td.get("nombre",""),
    })
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.section_title("1","DATOS DEL PACIENTE")
    pdf.data_field_2col([
        ("Nombre",    td.get("nombre","")),
        ("RUT/Doc",   td.get("rut","")),
        ("VFG",       f"{td.get('vfg',0):.1f} ml/min"),
        ("Creatinina",f"{td.get('creatinina',0)} mg/dL"),
    ])
    pdf.section_title("2","DIAGNÓSTICO")
    pdf.data_field("CIE-10", f"{td.get('cie10','')} — {td.get('cie10_desc','')}")
    if td.get("cie11"):
        pdf.data_field("CIE-11", td["cie11"])
    pdf.section_title("3","PRESCRIPCIÓN")
    pdf.data_field("Fármaco",     td.get("farmaco",""))
    pdf.data_field("Dosis",       td.get("dosis",""))
    pdf.data_field("Vía",         td.get("via",""))
    if indicaciones.strip():
        pdf.data_field("Indicaciones adicionales", indicaciones)
    pdf.section_title("4","TRIAJE TM")
    pdf.data_field("Evaluado por", f"{td.get('tm','')} · SIS {td.get('sis_tm','')}")
    pdf.data_field("Observaciones", td.get("observaciones",""))

    # MedicationRequest FHIR
    mr = {
        "resourceType": "MedicationRequest",
        "id": f"mr-{id_v}",
        "status": "active",
        "intent": "order",
        "medicationCodeableConcept": {"text": td.get("farmaco","")},
        "subject": {"display": td.get("nombre","")},
        "dosageInstruction": [{
            "text": f"{td.get('dosis','')} — Vía: {td.get('via','')}",
            "route": {"text": td.get("via","")},
        }],
        "reasonCode": [{"coding": [{"system":"http://hl7.org/fhir/sid/icd-10",
                                     "code": td.get("cie10",""),
                                     "display": td.get("cie10_desc","")}]}],
    }
    huella = pdf.estampar_sello_digital(
        usuario.get("nombre",""), usuario.get("sis",""),
        usuario.get("rol","radiologo"), ahora_str,
    )
    pdf_bytes = pdf.compilar()
    try:
        db.collection("triajes_farmacos").document(triaje_id).update({
            "estado": "RECETA_EMITIDA",
        })
        db.collection("recetas_emitidas").add({
            "triaje_id":      triaje_id,
            "id_verificacion":id_v,
            "nombre":         td.get("nombre",""),
            "rut":            td.get("rut",""),
            "farmaco":        td.get("farmaco",""),
            "dosis":          td.get("dosis",""),
            "indicaciones":   indicaciones,
            "medico":         usuario.get("nombre",""),
            "sis_medico":     usuario.get("sis",""),
            "fecha":          ahora_str,
            "huella_sha256":  huella,
            "fhir_medication":mr,
        })
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tp:
            tp.write(pdf_bytes)
            bucket.blob(f"recetas/{nombre_pdf}").upload_from_filename(
                tp.name, content_type="application/pdf",
            )
        os.unlink(tp.name)
        st.session_state["badge_farmacos"] = max(
            0, st.session_state.get("badge_farmacos",0)-1
        )
        st.success(f"✅ Receta emitida · Folio: {id_v}")
    except Exception as e:
        st.error(f"Error: {e}"); return

    st.download_button("📥 Descargar Receta PDF",
                       data=pdf_bytes, file_name=nombre_pdf,
                       mime="application/pdf", use_container_width=True)


def _historial(db):
    filtro = st.text_input("🔍", placeholder="Buscar…", key="filt_rec",
                            label_visibility="collapsed")
    try:
        docs = (db.collection("recetas_emitidas")
                  .order_by("fecha", direction="DESCENDING")
                  .limit(100).get())
    except Exception as e:
        st.error(f"Error: {e}"); return

    filas = []
    for doc in docs:
        d = doc.to_dict()
        if filtro and filtro.lower() not in d.get("nombre","").lower():
            continue
        filas.append({"Fecha":d.get("fecha",""),"Paciente":d.get("nombre",""),
                      "RUT":d.get("rut",""),"Fármaco":d.get("farmaco",""),
                      "Folio":d.get("id_verificacion",""),"Médico":d.get("medico","")})
    if filas:
        st.dataframe(pd.DataFrame(filas), use_container_width=True,
                     hide_index=True, height=350)
    else:
        st.info("Sin recetas registradas.")


def _balance_mensual(db, bucket, usuario: dict):
    ahora  = datetime.now(tz_chile)
    periodo = st.text_input("Período:", value=ahora.strftime("%B %Y"),
                             key="periodo_rec")
    pin = st.text_input("PIN:", type="password", key="pin_bal_rec")

    if st.button("📊 GENERAR BALANCE PDF", type="primary", use_container_width=True):
        if not validar_pin(pin, usuario.get("hash","")): 
            st.error("❌ PIN incorrecto."); return
        try:
            docs  = (db.collection("recetas_emitidas")
                       .order_by("fecha",direction="DESCENDING").limit(200).get())
            filas = [[d.to_dict().get("fecha",""),d.to_dict().get("nombre",""),
                      d.to_dict().get("farmaco",""),d.to_dict().get("dosis",""),
                      d.to_dict().get("medico",""),d.to_dict().get("id_verificacion","")]
                     for d in docs]
        except Exception as e:
            st.error(f"Error: {e}"); return

        ahora_str = ahora.strftime("%d/%m/%Y %H:%M:%S")
        _, id_v, nombre_pdf = generar_id_documento("REPORTE_RECETAS", db)
        pdf = PDFNorteImagen("REPORTE_RECETAS", config={
            "id_verificacion": id_v, "periodo": periodo,
        })
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.section_title_dark(f"BALANCE MENSUAL DE PRESCRIPCIONES — {periodo}")
        pdf.tabla(
            ["Fecha","Paciente","Fármaco","Dosis","Médico","Folio"],
            filas, anchos=[30,38,30,20,30,22],
        )
        pdf.estampar_sello_digital(
            usuario.get("nombre",""), usuario.get("sis",""),
            usuario.get("rol","tm"), ahora_str,
        )
        pdf_bytes = pdf.compilar()
        st.download_button("⬇️ Descargar Balance PDF",
                           data=pdf_bytes, file_name=nombre_pdf,
                           mime="application/pdf", use_container_width=True)

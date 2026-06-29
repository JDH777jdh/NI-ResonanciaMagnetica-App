# modules/motor_rescate.py — MOTOR DE RESCATE (Adendum / Enmiendas 48h)
import tempfile, os
from datetime import datetime, timedelta, timezone
import pytz, streamlit as st
from norte_imagen_core import (
    PDFNorteImagen, GestorCriptografico, FHIRBuilder,
    generar_id_documento, validar_pin, calcular_edad, edad_visual,
)

tz_chile = pytz.timezone("America/Santiago")
_cripto  = GestorCriptografico()
_HORAS   = 48

MOTIVOS = [
    "Corrección de datos demográficos",
    "Actualización VFG post-laboratorio",
    "Corrección de procedimiento radiológico",
    "Corrección de lateralidad",
    "Corrección de antecedentes clínicos",
    "Modificación de datos del representante legal",
    "Corrección de datos de contacto",
    "Otro motivo (especificar)",
]


def render(db, bucket, usuario: dict):
    _init_state()
    col_lista, col_form = st.columns([1, 2.2], gap="medium")
    with col_lista:
        _bandeja_rescate(db)
    with col_form:
        if st.session_state.get("rescate_id"):
            _formulario_adendum(db, bucket, usuario)
        else:
            st.markdown(
                "<div style='text-align:center;padding:60px 20px;color:#94a3b8'>"
                "<div style='font-size:36px'>💓</div>"
                "<div style='font-size:14px;font-weight:600;margin-top:10px'>"
                "Seleccione un paciente validado</div>"
                "<div style='font-size:11px;margin-top:4px'>"
                f"Ventana de enmienda activa: {_HORAS} horas post-validación</div>"
                "</div>", unsafe_allow_html=True,
            )


def _init_state():
    for k, v in [("rescate_id", None), ("rescate_doc", None),
                  ("adendum_aprobado", False)]:
        if k not in st.session_state:
            st.session_state[k] = v


@st.fragment(run_every=60)
def _bandeja_rescate(db):
    st.markdown(
        "<div style='font-size:11px;font-weight:700;color:#475569;"
        "margin-bottom:8px;text-transform:uppercase;letter-spacing:.5px'>"
        "Validados — Últimas 48 hrs</div>", unsafe_allow_html=True,
    )
    filtro = st.text_input("🔍", placeholder="Buscar…",
                           key="filtro_rescate", label_visibility="collapsed")
    try:
        docs = (db.collection("encuestas")
                  .where("encuesta_validada", "==", True)
                  .order_by("fecha_validacion", direction="DESCENDING")
                  .limit(40).get())
    except Exception as e:
        st.error(f"Error: {e}"); return

    ahora = datetime.now(tz_chile)
    activos = []
    for doc in docs:
        d = doc.to_dict()
        try:
            fv = datetime.strptime(d.get("fecha_validacion",""), "%d/%m/%Y %H:%M:%S")
            fv = tz_chile.localize(fv)
            if (ahora - fv).total_seconds() / 3600 <= _HORAS:
                activos.append((doc.id, d, fv))
        except Exception:
            pass

    st.session_state["badge_rescate"] = len(activos)

    if filtro:
        fl = filtro.lower()
        activos = [(i,d,f) for i,d,f in activos
                   if fl in d.get("nombre","").lower()
                   or fl in d.get("rut","").lower()]
    if not activos:
        st.markdown(
            "<div style='text-align:center;color:#94a3b8;padding:20px;font-size:11px'>"
            "Sin pacientes en ventana de enmienda</div>", unsafe_allow_html=True,
        )
        return

    for doc_id, d, fv in activos:
        horas_rest = _HORAS - (ahora - fv).total_seconds() / 3600
        mins = int((horas_rest % 1) * 60)
        tiene_adendum = d.get("tiene_adendum", False)
        color_borde   = "#d97706" if tiene_adendum else "#16a34a"
        activo_sel    = st.session_state.rescate_id == doc_id

        st.markdown(
            f"<div style='border:{'2px solid #800020' if activo_sel else f'1px solid {color_borde}'};"
            f"border-left:4px solid {color_borde};"
            f"background:{'#fdf2f4' if activo_sel else '#fff'};"
            f"border-radius:8px;padding:9px 12px;margin-bottom:6px'>"
            f"<div style='font-weight:700;font-size:12px;color:#1e293b'>"
            f"{d.get('nombre','S/N')}</div>"
            f"<div style='font-size:10px;color:#64748b'>"
            f"{d.get('rut','S/D')} · {d.get('procedimiento','S/P')}</div>"
            f"<div style='display:flex;justify-content:space-between;margin-top:5px'>"
            f"<span style='font-size:10px;color:#f59e0b;font-weight:700'>"
            f"⏱ {int(horas_rest)}h {mins}m restantes</span>"
            f"{'<span style=\"font-size:9px;background:#fef3c7;color:#92400e;'
               'padding:2px 6px;border-radius:8px\">Con adendum</span>'
               if tiene_adendum else ''}"
            f"</div></div>", unsafe_allow_html=True,
        )
        if st.button("Seleccionar", key=f"resc_{doc_id}", use_container_width=True):
            st.session_state.rescate_id  = doc_id
            st.session_state.rescate_doc = d
            st.session_state.adendum_aprobado = False
            st.rerun()


def _formulario_adendum(db, bucket, usuario: dict):
    d       = st.session_state.rescate_doc or {}
    nombre  = d.get("nombre", "Paciente")
    rut     = d.get("rut") or d.get("num_doc", "S/D")

    st.markdown(
        f"<div style='font-size:15px;font-weight:800;color:#1e293b'>"
        f"✏️ Adendum — {nombre}</div>"
        f"<div style='font-size:11px;color:#64748b;margin-bottom:10px'>"
        f"RUT: {rut} · Validado por: {d.get('validado_por','S/D')}"
        f" · {d.get('fecha_validacion','')}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div style='background:#fef2f2;border:1px solid #fecaca;"
        "border-radius:7px;padding:9px 12px;font-size:11px;color:#991b1b;margin-bottom:10px'>"
        "🔴 <strong>Ley 20.584 — Derechos del Paciente:</strong> El adendum queda "
        "registrado como enmienda oficial. El hash SHA-256 del documento original "
        "se preserva y el nuevo sello se adjunta al FHIR Bundle.</div>",
        unsafe_allow_html=True,
    )

    # Datos originales (expandible)
    with st.expander("📋 Ver datos originales del paciente", expanded=False):
        c1, c2 = st.columns(2)
        for lbl, val in [("Nombre", d.get("nombre","")),
                         ("Procedimiento", d.get("procedimiento","")),
                         ("VFG", f"{d.get('vfg',0):.2f} ml/min"),
                         ("Contraste", "Sí" if d.get("tiene_contraste") else "No")]:
            c1.caption(f"**{lbl}:** {val}")

    st.markdown("---")

    motivo = st.selectbox("Motivo de la enmienda:", MOTIVOS, key="adendum_motivo")
    otro   = ""
    if "Otro" in motivo:
        otro = st.text_input("Especifique:", key="adendum_otro")

    campo  = st.selectbox(
        "Campo a rectificar:",
        ["Nombre del paciente","RUT / Documento","Fecha de nacimiento",
         "Procedimiento","VFG / Creatinina","Datos del representante","Otro"],
        key="adendum_campo",
    )
    val_orig  = st.text_input("Valor original (incorrecto):", key="adendum_orig")
    val_nuevo = st.text_input("Valor corregido:", key="adendum_nuevo")
    texto_ad  = st.text_area(
        "Descripción completa de la enmienda:",
        height=90, key="adendum_texto",
        placeholder="Describa objetivamente la corrección realizada…",
    )

    st.markdown("---")
    st.markdown(
        "<div style='font-size:11px;font-weight:600;color:#374151;margin-bottom:4px'>"
        f"PIN de autorización — {usuario.get('nombre','')} · "
        f"SIS {usuario.get('sis','')}</div>",
        unsafe_allow_html=True,
    )
    pin_ad = st.text_input("PIN:", type="password", key="pin_adendum",
                           label_visibility="collapsed",
                           placeholder="Ingrese su PIN de 6 dígitos")

    if st.button("💾 SELLAR ADENDUM Y ACTUALIZAR DOCUMENTO",
                 type="primary", use_container_width=True):
        _procesar_adendum(db, bucket, usuario, d,
                          motivo, otro, campo,
                          val_orig, val_nuevo, texto_ad, pin_ad)

    if st.session_state.adendum_aprobado:
        st.success("✅ Adendum sellado y registrado correctamente.")


def _procesar_adendum(db, bucket, usuario, d,
                      motivo, otro, campo, val_orig, val_nuevo,
                      texto_ad, pin_ad):
    if not all([texto_ad.strip(), val_nuevo.strip(), pin_ad]):
        st.error("🚨 Complete todos los campos y su PIN."); return
    if not validar_pin(pin_ad, usuario.get("hash","")):
        st.error("❌ PIN incorrecto."); return

    ahora_str = datetime.now(tz_chile).strftime("%d/%m/%Y %H:%M:%S")
    ahora_iso = datetime.now(tz_chile).isoformat()
    _, id_adnd, nombre_pdf = generar_id_documento(
        "ADENDUM", db, d.get("nombre",""), d.get("rut",""),
    )
    hash_orig = d.get("huella_sha256_tm", d.get("firma_electronica",{}).get("hash_sha256",""))

    # PDF Adendum
    pdf = PDFNorteImagen("ADENDUM", config={
        "id_verificacion": id_adnd,
        "rut_paciente":    d.get("rut") or d.get("num_doc",""),
        "ip_paciente":     d.get("ip_paciente",""),
        "nombre_paciente": d.get("nombre",""),
        "hash_original":   hash_orig,
    })
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.section_title("1", "IDENTIFICACIÓN")
    pdf.data_field("Paciente",   d.get("nombre",""))
    pdf.data_field("RUT/Doc",    d.get("rut") or d.get("num_doc",""))
    pdf.section_title("2", "DETALLE DE LA ENMIENDA")
    pdf.data_field("Motivo",          f"{motivo}{' — '+otro if otro else ''}")
    pdf.data_field("Campo rectificado", campo)
    pdf.data_field("Valor original",   val_orig)
    pdf.data_field("Valor corregido",  val_nuevo)
    pdf.data_field("Descripción",      texto_ad)
    pdf.data_field("Hash doc. original", hash_orig[:32]+"…" if len(hash_orig)>32 else hash_orig)
    huella_ad = pdf.estampar_sello_digital(
        usuario.get("nombre",""), usuario.get("sis",""),
        usuario.get("rol","tm"), ahora_str,
    )
    pdf_bytes = pdf.compilar()

    # AuditEvent FHIR
    audit = FHIRBuilder.audit_event(
        "ADENDUM_DOCUMENTO", usuario.get("nombre",""),
        usuario.get("sis",""), st.session_state.rescate_id,
        ahora_iso, f"Adendum {id_adnd} | Campo: {campo} | Motivo: {motivo}",
    )

    try:
        db.collection("encuestas").document(st.session_state.rescate_id).update({
            "tiene_adendum":       True,
            "adendum": {
                "id":              id_adnd,
                "motivo":          f"{motivo}{' — '+otro if otro else ''}",
                "campo":           campo,
                "valor_original":  val_orig,
                "valor_corregido": val_nuevo,
                "descripcion":     texto_ad,
                "autor":           usuario.get("nombre",""),
                "sis":             usuario.get("sis",""),
                "fecha":           ahora_str,
                "huella_sha256":   huella_ad,
                "hash_original_preservado": hash_orig,
                "audit_fhir":      audit,
            },
        })
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tp:
            tp.write(pdf_bytes)
            bucket.blob(f"adendum/{nombre_pdf}").upload_from_filename(
                tp.name, content_type="application/pdf",
            )
        os.unlink(tp.name)
        st.session_state.adendum_aprobado = True
        st.session_state["badge_rescate"] = max(
            0, st.session_state.get("badge_rescate",0)-1
        )
    except Exception as e:
        st.error(f"Error al guardar: {e}"); return

    st.download_button("📥 Descargar PDF Adendum",
                       data=pdf_bytes, file_name=nombre_pdf,
                       mime="application/pdf", use_container_width=True)

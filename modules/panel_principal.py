# =============================================================================
# modules/panel_principal.py
# MÓDULO 1 — PANEL PRINCIPAL
# =============================================================================
# Responsabilidad:
#   · Bandeja de pacientes pre-validados (appv3 → Firestore)
#   · Desencriptación AES-256 del FHIR Bundle de cada paciente
#   · 7 subsecciones clínicas de revisión
#   · Firma digital del profesional (PIN + sello SHA-256)
#   · Generación de AuditEvent FHIR por cada acción
# =============================================================================

import os
import tempfile
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pytz
import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas

from norte_imagen_core import (
    FHIRBuilder,
    GestorCriptografico,
    PDFNorteImagen,
    _cargo_a_texto,
    calcular_edad,
    edad_visual,
    generar_id_documento,
    validar_pin,
)

tz_chile = pytz.timezone("America/Santiago")
_cripto  = GestorCriptografico()

# Umbral: pacientes de las últimas N horas
_HORAS_BANDEJA = 72


# =============================================================================
# PUNTO DE ENTRADA DEL MÓDULO
# =============================================================================
def render(db, bucket, usuario: dict):
    """Función principal llamada por admin_main.py."""
    _init_panel_state()
    _actualizar_badges(db)

    col_lista, col_detalle = st.columns([1, 2.2], gap="medium")

    with col_lista:
        _bandeja_pacientes(db)

    with col_detalle:
        pac_id = st.session_state.get("paciente_id")
        if pac_id:
            _panel_detalle(db, bucket, usuario)
        else:
            _placeholder_seleccion()


# =============================================================================
# ESTADO LOCAL DEL MÓDULO
# =============================================================================
def _init_panel_state():
    defaults = {
        "paciente_id":    None,
        "doc_completo":   None,
        "fhir_bundle":    None,
        "sec_expandidas": {
            "identificacion": True,
            "bioseguridad":   False,
            "clinicos":       False,
            "condiciones":    False,
            "quirurgico":     False,
            "examenes":       False,
            "vfg":            False,
        },
        "firma_canvas":   None,
        "pin_ingresado":  "",
        "doc_aprobado":   False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# =============================================================================
# SECCIÓN A — BANDEJA DE PACIENTES
# =============================================================================
@st.fragment(run_every=60)
def _bandeja_pacientes(db):
    """
    Lista de pacientes pendientes de validación.
    Auto-refresco cada 60 segundos sin recargar toda la página.
    """
    st.markdown(
        "<div style='font-size:11px;font-weight:700;color:#475569;"
        "margin-bottom:8px;text-transform:uppercase;letter-spacing:.5px'>"
        "Pacientes en espera</div>",
        unsafe_allow_html=True,
    )

    # Filtro
    filtro = st.text_input("🔍", placeholder="Buscar nombre o RUT…",
                           key="filtro_bandeja", label_visibility="collapsed")

    # Cargar desde Firestore (últimas N horas, no validados aún)
    desde = datetime.now(timezone.utc) - timedelta(hours=_HORAS_BANDEJA)
    try:
        docs = (db.collection("encuestas")
                  .where("encuesta_validada", "==", False)
                  .order_by("fecha_creacion", direction="DESCENDING")
                  .limit(50)
                  .get())
    except Exception as e:
        st.error(f"Error al cargar bandeja: {e}")
        return

    pacientes = [d for d in docs]
    if filtro:
        filtro_l = filtro.lower()
        pacientes = [d for d in pacientes
                     if filtro_l in d.to_dict().get("nombre", "").lower()
                     or filtro_l in d.to_dict().get("rut", "").lower()]

    st.session_state["badge_panel"] = len(pacientes)

    if not pacientes:
        st.markdown(
            "<div style='text-align:center;color:#94a3b8;padding:30px 0;font-size:12px'>"
            "✅ Sin pacientes pendientes</div>",
            unsafe_allow_html=True,
        )
        return

    for doc in pacientes:
        d    = doc.to_dict()
        _tarjeta_paciente(doc.id, d)


def _tarjeta_paciente(doc_id: str, d: dict):
    """Tarjeta clickeable por paciente."""
    nombre     = d.get("nombre", "Sin nombre")
    rut        = d.get("rut") or d.get("num_doc", "S/D")
    proc       = d.get("procedimiento", "S/P")
    contraste  = d.get("tiene_contraste", False)
    vfg        = float(d.get("vfg", 0))
    f_creacion = d.get("fecha_creacion", "")
    activo     = st.session_state.paciente_id == doc_id

    # Indicador de riesgo VFG
    if contraste and 0 < vfg <= 30:
        riesgo_html = "<span class='tag tag-red'>🔴 VFG crítica</span>"
    elif contraste and 0 < vfg <= 59:
        riesgo_html = "<span class='tag tag-amber'>⚠️ VFG intermedia</span>"
    elif contraste:
        riesgo_html = "<span class='tag tag-green'>✅ VFG OK</span>"
    else:
        riesgo_html = "<span class='tag tag-gray'>Sin contraste</span>"

    # Edad
    fn = d.get("fecha_nac")
    try:
        if isinstance(fn, str):
            fn_d = datetime.strptime(fn, "%d/%m/%Y").date()
        else:
            fn_d = fn
        edad_txt = f"{calcular_edad(fn_d)} años"
    except Exception:
        edad_txt = "S/D"

    borde = "border:2px solid #800020" if activo else "border:1px solid #e2e8f0"
    bg    = "background:#fdf2f4" if activo else "background:#fff"

    st.markdown(f"""
    <div style="{borde};{bg};border-radius:8px;padding:10px 12px;
                 margin-bottom:6px;cursor:pointer">
      <div style="display:flex;justify-content:space-between;align-items:flex-start">
        <div style="font-weight:700;font-size:12px;color:#1e293b">{nombre}</div>
        <div style="font-size:10px;color:#64748b">{f_creacion[:16] if f_creacion else ''}</div>
      </div>
      <div style="font-size:10px;color:#64748b;margin:2px 0">
        RUT {rut} · {edad_txt}
      </div>
      <div style="font-size:10px;color:#475569;margin:2px 0">{proc}</div>
      <div style="margin-top:5px">{riesgo_html}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Seleccionar", key=f"sel_{doc_id}",
                 use_container_width=True):
        st.session_state.paciente_id   = doc_id
        st.session_state.doc_completo  = d
        st.session_state.fhir_bundle   = _desencriptar_fhir(d)
        st.session_state.doc_aprobado  = False
        st.session_state.firma_canvas  = None
        # Registrar apertura en auditoría
        _rerun_con_refresco()


def _desencriptar_fhir(d: dict) -> dict | None:
    """Desencripta el FHIR Bundle AES-256 recibido de appv3."""
    payload_enc = d.get("fhir_bundle_aes256_gcm", "")
    if not payload_enc:
        return None
    return _cripto.desencriptar_seguro(payload_enc)


def _rerun_con_refresco():
    st.rerun()


# =============================================================================
# SECCIÓN B — PLACEHOLDER SIN SELECCIÓN
# =============================================================================
def _placeholder_seleccion():
    st.markdown(
        "<div style='text-align:center;padding:60px 20px;color:#94a3b8'>"
        "<div style='font-size:40px;margin-bottom:12px'>👈</div>"
        "<div style='font-size:14px;font-weight:600'>Seleccione un paciente</div>"
        "<div style='font-size:12px;margin-top:4px'>"
        "de la bandeja para revisar su ficha clínica</div>"
        "</div>",
        unsafe_allow_html=True,
    )


# =============================================================================
# SECCIÓN C — PANEL DE DETALLE CLÍNICO (7 subsecciones)
# =============================================================================
def _panel_detalle(db, bucket, usuario: dict):
    d    = st.session_state.doc_completo or {}
    fhir = st.session_state.fhir_bundle  or {}

    nombre = d.get("nombre", "Paciente")
    rut    = d.get("rut") or d.get("num_doc", "S/D")

    # Cabecera del paciente
    c_nom, c_rut, c_proc = st.columns([2.5, 1.2, 2])
    c_nom.markdown(
        f"<div style='font-size:16px;font-weight:800;color:#1e293b'>{nombre}</div>"
        f"<div style='font-size:11px;color:#64748b'>RUT / Doc: {rut}</div>",
        unsafe_allow_html=True,
    )
    c_rut.markdown(
        f"<span class='tag tag-{'blue' if d.get('tiene_contraste') else 'gray'}'>"
        f"{'Con contraste' if d.get('tiene_contraste') else 'Sin contraste'}</span>",
        unsafe_allow_html=True,
    )
    c_proc.markdown(
        f"<div style='font-size:11px;color:#475569;padding-top:4px'>"
        f"📋 {d.get('procedimiento','S/P')}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<hr style='border:none;border-top:1px solid #e2e8f0;margin:8px 0'>",
        unsafe_allow_html=True,
    )

    # ── 7 Subsecciones ────────────────────────────────────────────
    _subsec_identificacion(d, fhir)
    _subsec_bioseguridad(d)
    _subsec_clinicos(d)
    _subsec_condiciones(d)
    _subsec_quirurgico(d)
    _subsec_examenes(d, bucket)
    _subsec_vfg(d)

    # ── Firma Digital ─────────────────────────────────────────────
    _bloque_firma_digital(db, bucket, usuario, d, fhir)


# ── Componente reutilizable de subsección ─────────────────────────
def _subsec(titulo: str, key: str, emoji: str):
    """Devuelve True si la subsección está expandida."""
    expandido = st.session_state.sec_expandidas.get(key, False)
    icono_flecha = "▲" if expandido else "▼"
    st.markdown(
        f"<div style='background:#f8fafc;border:1px solid #e2e8f0;"
        f"border-radius:7px;padding:8px 12px;margin-bottom:4px;"
        f"display:flex;justify-content:space-between;align-items:center'>"
        f"<span style='font-weight:700;font-size:12px;color:#374151'>"
        f"{emoji} {titulo}</span>"
        f"<span style='color:#94a3b8;font-size:11px'>{icono_flecha}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
    if st.button(f"Toggle {titulo}", key=f"tgl_{key}", use_container_width=True):
    # 2. La acción va abajo, con 4 espacios más de sangría hacia la derecha
    st.session_state.sec_expandidas[key] = not expandido
    st.rerun()
    return expandido


def _campo(col, label: str, value, estado: str = "normal"):
    """Campo visual dentro de una subsección."""
    color_val = {
        "ok":     "#16a34a",
        "danger": "#dc2626",
        "warn":   "#d97706",
        "normal": "#1e293b",
    }.get(estado, "#1e293b")
    col.markdown(
        f"<div style='background:#f8fafc;border-radius:5px;padding:5px 8px;"
        f"margin-bottom:5px'>"
        f"<div style='font-size:9px;color:#94a3b8;text-transform:uppercase;"
        f"letter-spacing:.4px'>{label}</div>"
        f"<div style='font-size:11px;font-weight:600;color:{color_val};margin-top:1px'>"
        f"{value}</div></div>",
        unsafe_allow_html=True,
    )


# ── 1. IDENTIFICACIÓN ─────────────────────────────────────────────
def _subsec_identificacion(d: dict, fhir: dict):
    if not _subsec("1. IDENTIFICACIÓN DEL PACIENTE", "identificacion", "🪪"):
        return

    fn_raw = d.get("fecha_nac", "")
    try:
        if isinstance(fn_raw, str):
            fn_d = datetime.strptime(fn_raw, "%d/%m/%Y").date()
        else:
            fn_d = fn_raw
        edad_txt = edad_visual(fn_d)
    except Exception:
        edad_txt = "S/D"

    fes = d.get("firma_electronica", {})
    hash_doc = fes.get("hash_sha256", "")
    hash_corto = f"{hash_doc[:8]}…{hash_doc[-8:]}" if len(hash_doc) > 16 else hash_doc

    c1, c2 = st.columns(2)
    _campo(c1, "Nombre completo", d.get("nombre", "S/D"))
    _campo(c2, "RUT / Documento",
           d.get("rut") or f"{d.get('tipo_doc','')} {d.get('num_doc','')}")
    _campo(c1, "Fecha de nacimiento", fn_raw)
    _campo(c2, "Edad", edad_txt)
    _campo(c1, "Email", d.get("email", "S/D"))
    _campo(c2, "Teléfono", d.get("telefono", "S/D"))
    _campo(c1, "Procedencia",
           f"{d.get('procedencia','S/D')} "
           f"{'· ' + d.get('unidad_procedencia','') if d.get('unidad_procedencia') else ''}")
    _campo(c2, "IP Dispositivo Paciente",
           d.get("ip_paciente", "No registrada"),
           "normal")
    _campo(c1, "FES Verificado",
           "✅ SHA-256 válido" if fes.get("estado") == "FIRMADO" else "⚠️ Pendiente",
           "ok" if fes.get("estado") == "FIRMADO" else "warn")
    _campo(c2, "Huella SHA-256", hash_corto if hash_corto else "S/D")

    # Tutor (si aplica)
    if d.get("nombre_tutor"):
        st.markdown(
            "<div style='background:#eff6ff;border:1px solid #bfdbfe;"
            "border-radius:6px;padding:8px 10px;margin-top:6px;"
            "font-size:11px;color:#1e40af'>"
            f"👨‍👦 <strong>Representante Legal:</strong> "
            f"{d['nombre_tutor']} — {d.get('parentesco_tutor','S/D')}"
            f" | Doc: {d.get('rut_tutor') or d.get('num_doc_tutor','S/D')}"
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Firma del paciente (imagen desde Firebase)
    ruta_firma = d.get("url_firma_storage", "")
    if ruta_firma:
        try:
            blob = bucket.blob(ruta_firma)
            tmp  = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            blob.download_to_filename(tmp.name)
            st.markdown(
                "<div style='font-size:11px;font-weight:600;color:#374151;"
                "margin-bottom:4px'>Firma Digital del Paciente / Representante:</div>",
                unsafe_allow_html=True,
            )
            st.image(tmp.name, width=220)
            os.unlink(tmp.name)
        except Exception:
            st.caption("⚠️ Firma no disponible temporalmente.")


# ── 2. BIOSEGURIDAD ────────────────────────────────────────────────
def _subsec_bioseguridad(d: dict):
    if not _subsec("2. BIOSEGURIDAD MAGNÉTICA", "bioseguridad", "🧲"):
        return

    marc = d.get("bio_marcapaso",  "No")
    impl = d.get("bio_implantes",  "No")
    det  = d.get("bio_detalle",    "")
    c1, c2 = st.columns(2)
    _campo(c1, "Marcapasos cardiaco", marc,
           "danger" if marc == "Sí" else "ok")
    _campo(c2, "Implantes / prótesis / dispositivos electrónicos",
           impl, "danger" if impl == "Sí" else "ok")
    if det:
        st.markdown(
            f"<div style='background:#fef2f2;border:1px solid #fecaca;"
            f"border-radius:6px;padding:8px;font-size:11px;color:#991b1b;margin-top:4px'>"
            f"⚠️ <strong>Detalle:</strong> {det}</div>",
            unsafe_allow_html=True,
        )
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


# ── 3. ANTECEDENTES CLÍNICOS ───────────────────────────────────────
def _subsec_clinicos(d: dict):
    if not _subsec("3. ANTECEDENTES CLÍNICOS", "clinicos", "🩺"):
        return

    campos_clinicos = [
        ("Ayuno ≥ 2 hrs",      "clin_ayuno"),
        ("Asma",               "clin_asma"),
        ("Hipertensión",       "clin_hiperten"),
        ("Hipertiroidismo",    "clin_hipertiroid"),
        ("Diabetes",           "clin_diabetes"),
        ("Alergias",           "clin_alergico"),
        ("Metformina 48h",     "clin_metformina"),
        ("Insuf. Renal",       "clin_renal"),
        ("Diálisis",           "clin_dialisis"),
        ("Embarazo",           "clin_embarazo"),
        ("Lactancia",          "clin_lactancia"),
        ("Claustrofobia",      "clin_claustro"),
    ]
    cols = st.columns(3)
    for i, (label, key) in enumerate(campos_clinicos):
        val = d.get(key, "No")
        _campo(cols[i % 3], label, val,
               "danger" if val == "Sí" else "ok")

    alergias = d.get("alergias_detalles", "").strip()
    if alergias:
        st.markdown(
            f"<div style='background:#fef2f2;border:1px solid #fecaca;"
            f"border-radius:6px;padding:8px;font-size:11px;color:#991b1b;margin-top:4px'>"
            f"⚠️ <strong>Alergias declaradas:</strong> {alergias}</div>",
            unsafe_allow_html=True,
        )
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


# ── 4. CONDICIONES ESPECIALES ─────────────────────────────────────
def _subsec_condiciones(d: dict):
    if not _subsec("4. CONDICIONES O REQUERIMIENTOS ESPECIALES",
                   "condiciones", "♿"):
        return

    conds   = d.get("condiciones", [])
    detalle = d.get("condicion_detalle", "")
    if conds or detalle:
        if conds:
            for c in conds:
                st.markdown(
                    f"<div style='background:#eff6ff;border-left:3px solid #2563eb;"
                    f"padding:5px 10px;font-size:11px;color:#1e40af;margin-bottom:4px'>"
                    f"• {c}</div>",
                    unsafe_allow_html=True,
                )
        if detalle:
            st.caption(f"Detalle adicional: {detalle}")
    else:
        st.markdown(
            "<div style='color:#64748b;font-size:11px;padding:6px 0'>"
            "Sin condiciones especiales declaradas.</div>",
            unsafe_allow_html=True,
        )
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


# ── 5. ANTECEDENTES QUIRÚRGICOS ───────────────────────────────────
def _subsec_quirurgico(d: dict):
    if not _subsec("5. ANTECEDENTES QUIRÚRGICOS Y TERAPÉUTICOS",
                   "quirurgico", "🔪"):
        return

    cir  = d.get("quir_cirugia_check", "No")
    can  = d.get("quir_cancer_check",  "No")
    c1, c2 = st.columns(2)
    _campo(c1, "Cirugías previas", cir,
           "warn" if cir == "Sí" else "ok")
    _campo(c2, "Antecedente oncológico", can,
           "danger" if can == "Sí" else "ok")

    if cir == "Sí" and d.get("quir_cirugia_detalle"):
        st.caption(f"Detalle: {d['quir_cirugia_detalle']}")
    if can == "Sí":
        trats = [k for k in ["rt","qt","bt","it"]
                 if d.get(k) in ("Sí", True)]
        st.markdown(
            f"<div style='font-size:11px;color:#991b1b;margin-top:4px'>"
            f"Tratamientos: {', '.join(trats).upper() if trats else 'No especificados'} "
            f"| {d.get('quir_cancer_detalle','')}</div>",
            unsafe_allow_html=True,
        )
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


# ── 6. EXÁMENES ANTERIORES ────────────────────────────────────────
def _subsec_examenes(d: dict, bucket):
    if not _subsec("6. EXÁMENES ANTERIORES", "examenes", "📁"):
        return

    has = d.get("has_examenes_previos", "No")
    if has != "Sí":
        st.markdown(
            "<div style='color:#64748b;font-size:11px;padding:6px 0'>"
            "Paciente no refiere exámenes anteriores.</div>",
            unsafe_allow_html=True,
        )
    else:
        tipos = [k.upper() for k in ["ex_rx","ex_mg","ex_eco","ex_tc","ex_rm"]
                 if d.get(k)]
        if tipos:
            st.markdown(
                "<div style='font-size:11px;color:#374151;margin-bottom:6px'>"
                f"Tipos declarados: <strong>{'  ·  '.join(tipos)}</strong></div>",
                unsafe_allow_html=True,
            )
        otros = d.get("ex_otros", "").strip()
        if otros:
            st.caption(f"Otros: {otros}")

        # Links externos
        for i in ["1","2"]:
            link = d.get(f"link_exam_{i}", "").strip()
            pin  = d.get(f"pin_exam_{i}", "").strip()
            if link:
                st.markdown(
                    f"<a href='{link}' target='_blank' "
                    f"style='font-size:11px;color:#2563eb'>🔗 Link {i}</a>"
                    f"{'  |  PIN: ' + pin if pin else ''}",
                    unsafe_allow_html=True,
                )

        # Archivos en Firebase Storage
        rutas = d.get("url_examenes_firebase", [])
        if rutas:
            st.markdown(
                "<div style='font-size:11px;font-weight:600;color:#374151;"
                "margin-top:6px;margin-bottom:4px'>Archivos adjuntos:</div>",
                unsafe_allow_html=True,
            )
            for ruta in rutas:
                nombre_arch = os.path.basename(ruta)
                try:
                    blob = bucket.blob(ruta)
                    url  = blob.generate_signed_url(expiration=300)
                    st.markdown(
                        f"<a href='{url}' target='_blank' "
                        f"style='font-size:11px;color:#2563eb;display:block;"
                        f"margin-bottom:3px'>📎 {nombre_arch}</a>",
                        unsafe_allow_html=True,
                    )
                except Exception:
                    st.caption(f"📎 {nombre_arch} (no disponible)")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


# ── 7. VFG Y ADMINISTRACIÓN FARMACOLÓGICA ─────────────────────────
def _subsec_vfg(d: dict):
    if not _subsec("7. VFG Y ADMINISTRACIÓN FARMACOLÓGICA", "vfg", "🧪"):
        return

    contraste = d.get("tiene_contraste", False)

    if not contraste:
        st.markdown(
            "<div style='background:#f0fdf4;border:1px solid #bbf7d0;"
            "border-radius:7px;padding:10px;font-size:11px;color:#166534'>"
            "✅ Examen sin medio de contraste. No se requiere evaluación de VFG.</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        return

    crea   = float(d.get("creatinina", 0))
    vfg    = float(d.get("vfg", 0))
    peso   = float(d.get("peso", 0))
    talla  = float(d.get("talla", 0))
    f_crea = d.get("fecha_creatinina", "Sin fecha")

    c1, c2, c3 = st.columns(3)
    _campo(c1, "Creatinina (mg/dL)",
           f"{crea} mg/dL" if crea > 0 else "Sin registro",
           "danger" if crea > 1.5 else "ok" if crea > 0 else "warn")
    _campo(c2,
           "Peso (kg)" if peso > 0 else "Talla (cm)",
           f"{peso} kg" if peso > 0 else (f"{talla} cm" if talla > 0 else "S/D"))
    _campo(c3, "Fecha examen Creatinina", str(f_crea))

    # Caja VFG coloreada
    if vfg <= 0:
        clase, color, msg = "vfg-warn", "#d97706", "VFG no calculada"
    elif vfg <= 30:
        clase, color, msg = "vfg-danger", "#dc2626", "🔴 ALTO RIESGO"
    elif vfg <= 59:
        clase, color, msg = "vfg-warn", "#d97706", "⚠️ RIESGO INTERMEDIO"
    else:
        clase, color, msg = "vfg-ok", "#16a34a", "✅ SIN RIESGO"

    st.markdown(
        f"<div class='{clase}' style='margin-top:8px;padding:14px'>"
        f"<div style='font-size:11px;color:#64748b'>VFG Estimada</div>"
        f"<div style='font-size:28px;font-weight:800;color:{color}'>"
        f"{vfg:.2f}</div>"
        f"<div style='font-size:11px;color:#64748b'>ml/min/1.73m²</div>"
        f"<div style='font-size:12px;font-weight:700;color:{color};margin-top:4px'>"
        f"{msg}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Recomendación ESUR 2023
    if 0 < vfg <= 30:
        st.markdown(
            "<div style='background:#fef2f2;border:1px solid #fecaca;"
            "border-radius:6px;padding:8px 10px;font-size:11px;color:#991b1b;margin-top:6px'>"
            "⛔ <strong>ESUR 2023:</strong> VFG ≤30 ml/min. "
            "Contraindicado el uso de GBCA de baja estabilidad. "
            "Evaluar con radiólogo antes de proceder.</div>",
            unsafe_allow_html=True,
        )
    elif 30 < vfg <= 59:
        st.markdown(
            "<div style='background:#fffbeb;border:1px solid #fde68a;"
            "border-radius:6px;padding:8px 10px;font-size:11px;color:#92400e;margin-top:6px'>"
            "⚠️ <strong>ESUR 2023:</strong> VFG 30–60 ml/min. "
            "Usar GBCA macrocíclico a dosis estándar (0.1 mmol/kg). "
            "Hidratación pre-examen recomendada.</div>",
            unsafe_allow_html=True,
        )

    # Tabla administración farmacológica
    st.markdown(
        "<div style='font-size:11px;font-weight:700;color:#374151;"
        "margin:10px 0 4px'>Registro de Administración (completar post-examen):</div>",
        unsafe_allow_html=True,
    )
    ca1, ca2, ca3 = st.columns(3)
    ca1.text_input("Acceso Vascular", key="farm_acceso",
                   placeholder="Ej: Vía periférica")
    ca2.text_input("Sitio de Punción", key="farm_sitio",
                   placeholder="Ej: Fosa antecubital D")
    ca3.text_input("Cantidad Contraste (ml)", key="farm_cantidad",
                   placeholder="Ej: 15 ml")
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


# =============================================================================
# SECCIÓN D — FIRMA DIGITAL DEL PROFESIONAL
# =============================================================================
def _bloque_firma_digital(db, bucket, usuario: dict, d: dict, fhir: dict):
    nombre_prof = usuario.get("nombre", "")
    sis_prof    = usuario.get("sis", "")
    rol_prof    = usuario.get("rol", "tm")
    hash_usr    = usuario.get("hash", "")

    st.markdown(
        "<div style='background:#fff;border:1px solid #e2e8f0;border-radius:10px;"
        "padding:14px 16px;margin-top:8px'>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div style='font-size:13px;font-weight:700;color:#1e293b;margin-bottom:8px'>"
        "✍️ Firma Digital del Profesional</div>",
        unsafe_allow_html=True,
    )

    # Canvas de firma
    st.markdown(
        "<div style='font-size:11px;color:#64748b;margin-bottom:4px'>"
        "Firme en el recuadro con el cursor o dedo:</div>",
        unsafe_allow_html=True,
    )
    canvas_res = st_canvas(
        stroke_width=3, stroke_color="#000",
        background_color="#fff",
        height=100, width=380,
        key="canvas_firma_tm",
    )
    if canvas_res and canvas_res.image_data is not None:
        st.session_state.firma_canvas = canvas_res.image_data

    firma_valida = (
        st.session_state.firma_canvas is not None
        and np.any(st.session_state.firma_canvas[:, :, 3] > 0)
    )

    # Alerta legal
    st.markdown(
        "<div style='background:#fef2f2;border:1px solid #fecaca;"
        "border-radius:6px;padding:8px 10px;font-size:11px;color:#991b1b;margin:8px 0'>"
        "⚠️ Al ingresar su PIN certifica bajo Sello Criptográfico SHA-256 que revisó "
        "todos los antecedentes clínicos del paciente y validó los riesgos asociados "
        "al procedimiento.</div>",
        unsafe_allow_html=True,
    )

    # PIN + Botón
    st.markdown(
        f"<div style='font-size:11px;font-weight:600;color:#374151;margin-bottom:3px'>"
        f"{nombre_prof} · SIS {sis_prof} · "
        f"<span style='color:#800020'>{_cargo_a_texto(rol_prof)}</span></div>",
        unsafe_allow_html=True,
    )
    pin_col, btn_col = st.columns([2, 1])
    pin_input = pin_col.text_input(
        "PIN profesional", type="password",
        placeholder="Ingrese su PIN de 6 dígitos",
        key="pin_firma_tm",
        label_visibility="collapsed",
    )

    if btn_col.button("🔒 APROBAR Y SELLAR", type="primary",
                      use_container_width=True):
        _procesar_firma(db, bucket, usuario, d, fhir,
                        pin_input, firma_valida,
                        hash_usr, nombre_prof, sis_prof, rol_prof)

    if st.session_state.doc_aprobado:
        st.success("✅ Documento sellado y guardado correctamente.")

    st.markdown("</div>", unsafe_allow_html=True)


def _procesar_firma(db, bucket, usuario, d, fhir,
                    pin_input, firma_valida,
                    hash_usr, nombre_prof, sis_prof, rol_prof):
    """Valida PIN, sella el documento y lo persiste."""
    if not firma_valida:
        st.error("🚨 Debe dibujar su firma en el recuadro.")
        return
    if not pin_input:
        st.error("🚨 Ingrese su PIN.")
        return
    if not validar_pin(pin_input, hash_usr):
        st.error("❌ PIN incorrecto.")
        _log_accion(db, usuario, "FIRMA_FALLIDA", d.get("rut",""))
        return

    # Guardar firma TM en Storage
    try:
        img_arr  = Image.fromarray(
            st.session_state.firma_canvas.astype("uint8"), "RGBA"
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            img_arr.save(tmp.name)
            ts_str   = datetime.now(tz_chile).strftime("%Y%m%d_%H%M%S")
            rut_lmp  = str(d.get("rut","SR")).replace(".","").replace("-","")
            blob_n   = f"firmas_tm/{rut_lmp}_{sis_prof}_{ts_str}.png"
            bucket.blob(blob_n).upload_from_filename(
                tmp.name, content_type="image/png"
            )
        os.unlink(tmp.name)
    except Exception as e:
        st.warning(f"Firma guardada localmente. Storage: {e}")
        blob_n = ""

    # Generar PDF validado
    ahora_str = datetime.now(tz_chile).strftime("%d/%m/%Y %H:%M:%S")
    _, id_verif, nombre_pdf = generar_id_documento(
        "CONSENTIMIENTO", db,
        nombre_pac=d.get("nombre",""),
        rut_pac=d.get("rut",""),
    )

    pdf = PDFNorteImagen("CONSENTIMIENTO", config={
        "id_verificacion": id_verif,
        "rut_paciente":    d.get("rut") or d.get("num_doc",""),
        "ip_paciente":     d.get("ip_paciente",""),
        "nombre_paciente": d.get("nombre",""),
    })
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=12)

    # Secciones resumidas en el PDF validado
    pdf.section_title("1", "IDENTIFICACIÓN")
    pdf.data_field("Nombre",     d.get("nombre",""))
    pdf.data_field("RUT/Doc",    d.get("rut") or d.get("num_doc",""))
    pdf.data_field("Procedimiento", d.get("procedimiento",""))
    pdf.data_field("Contraste",  "SÍ" if d.get("tiene_contraste") else "NO")

    if float(d.get("vfg",0)) > 0:
        pdf.section_title("7", "VFG")
        pdf.data_field("Creatinina", f"{d.get('creatinina',0)} mg/dL")
        pdf.data_field("VFG Estimada", f"{d.get('vfg',0):.2f} ml/min/1.73m2")

    huella = pdf.estampar_sello_digital(nombre_prof, sis_prof, rol_prof, ahora_str)
    pdf_bytes = pdf.compilar()

    # AuditEvent FHIR
    ahora_iso = datetime.now(tz_chile).isoformat()
    audit_ev  = FHIRBuilder.audit_event(
        accion="VALIDACION_DOCUMENTO",
        profesional=nombre_prof, sis=sis_prof,
        paciente_id=st.session_state.paciente_id,
        ahora_iso=ahora_iso,
        detalle=f"Documento {id_verif} validado con sello SHA-256: {huella}",
    )

    # Actualizar Firestore
    try:
        db.collection("encuestas").document(st.session_state.paciente_id).update({
            "encuesta_validada":    True,
            "fecha_validacion":     ahora_str,
            "validado_por":         nombre_prof,
            "sis_validador":        sis_prof,
            "rol_validador":        rol_prof,
            "url_firma_tm":         blob_n,
            "id_verificacion_tm":   id_verif,
            "huella_sha256_tm":     huella,
            "pdf_validado_nombre":  nombre_pdf,
            "audit_validacion":     audit_ev,
            "administracion_farm": {
                "acceso":   st.session_state.get("farm_acceso",""),
                "sitio":    st.session_state.get("farm_sitio",""),
                "cantidad": st.session_state.get("farm_cantidad",""),
            },
        })
        # Subir PDF validado a Storage
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tp:
            tp.write(pdf_bytes)
            bucket.blob(f"pdfs_validados/{nombre_pdf}").upload_from_filename(
                tp.name, content_type="application/pdf"
            )
        os.unlink(tp.name)
        _log_accion(db, usuario, "DOCUMENTO_VALIDADO",
                    d.get("rut",""), f"ID: {id_verif}")
        st.session_state.doc_aprobado = True
        st.session_state["badge_panel"] = max(
            0, st.session_state.get("badge_panel",0) - 1
        )
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return

    # Descarga inmediata
    st.download_button(
        "📥 Descargar PDF Validado",
        data=pdf_bytes,
        file_name=nombre_pdf,
        mime="application/pdf",
        use_container_width=True,
    )


# =============================================================================
# UTILIDADES INTERNAS
# =============================================================================
def _actualizar_badges(db):
    try:
        n = (db.collection("encuestas")
               .where("encuesta_validada", "==", False)
               .get())
        st.session_state["badge_panel"] = len(n)
    except Exception:
        pass


def _log_accion(db, usuario: dict, accion: str,
                rut: str, detalle: str = ""):
    try:
        db.collection("trazabilidad").add({
            "modulo":      "panel_principal",
            "accion":      accion,
            "profesional": usuario.get("nombre",""),
            "sis":         usuario.get("sis",""),
            "rol":         usuario.get("rol",""),
            "rut_paciente":rut,
            "detalle":     detalle,
            "timestamp":   datetime.now(tz_chile).isoformat(),
        })
    except Exception:
        pass

# =============================================================================
# modules/panel_principal.py — v2 CORREGIDA
# Fixes: VFG interactiva, query Firestore correcta, PDF igual a admin(96)
# =============================================================================
import os, tempfile
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pytz
import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas
from google.cloud.firestore_v1.base_query import FieldFilter

from norte_imagen_core import (
    FHIRBuilder, GestorCriptografico, PDFNorteImagen,
    _cargo_a_texto, calcular_edad, edad_visual,
    generar_id_documento, validar_pin,
)

tz_chile = pytz.timezone("America/Santiago")
_cripto  = GestorCriptografico()
_HORAS_BANDEJA = 72


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================
def render(db, bucket, usuario: dict):
    _init_panel_state()
    _actualizar_badges(db)
    col_lista, col_detalle = st.columns([1, 2.2], gap="medium")
    with col_lista:
        _bandeja_pacientes(db)
    with col_detalle:
        if st.session_state.get("paciente_id"):
            _panel_detalle(db, bucket, usuario)
        else:
            st.markdown(
                "<div style='text-align:center;padding:60px 20px;color:#94a3b8'>"
                "<div style='font-size:40px;margin-bottom:12px'>👈</div>"
                "<div style='font-size:14px;font-weight:600'>Seleccione un paciente</div>"
                "<div style='font-size:12px;margin-top:4px;color:#cbd5e1'>"
                "de la bandeja para revisar su ficha clínica</div></div>",
                unsafe_allow_html=True,
            )


def _init_panel_state():
    for k, v in {
        "paciente_id": None, "doc_completo": None, "fhir_bundle": None,
        "sec_expandidas": {
            "identificacion": True, "bioseguridad": False, "clinicos": False,
            "condiciones": False, "quirurgico": False, "examenes": False, "vfg": False,
        },
        "firma_canvas": None, "doc_aprobado": False,
        # VFG interactiva — valores editables por el TM
        "vfg_crea_tm": 0.0, "vfg_peso_tm": 0.0, "vfg_talla_tm": 0.0,
        "vfg_contraste_tm": False, "vfg_calculada_tm": 0.0,
        "vfg_msg_tm": "", "vfg_color_tm": "#888888",
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v


# =============================================================================
# VFG UNIVERSAL (portada del motor de admin96)
# =============================================================================
def _calcular_vfg_universal(fecha_nac_raw, sexo_bio, creatinina, talla_cm, peso_kg):
    """Motor VFG idéntico al de admin(96). Soporta strings y dates."""
    if creatinina <= 0:
        return 0.0, "Parámetros incompletos"
    hoy = date.today()
    # Parseo robusto de fecha
    if isinstance(fecha_nac_raw, str):
        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                fecha_nac = datetime.strptime(fecha_nac_raw[:10], fmt).date(); break
            except ValueError:
                continue
        else:
            fecha_nac = hoy
    elif isinstance(fecha_nac_raw, datetime):
        fecha_nac = fecha_nac_raw.date()
    elif isinstance(fecha_nac_raw, date):
        fecha_nac = fecha_nac_raw
    else:
        fecha_nac = hoy

    edad_dias  = (hoy - fecha_nac).days
    edad_meses = edad_dias / 30.4
    edad_anos  = edad_dias / 365.25

    if edad_anos < 2:
        formula = "Schwartz Clásica"
        k = 0.33 if edad_dias < 7 else (0.45 if edad_dias <= 28 else
            (0.45 if edad_meses <= 12 else 0.55))
        vfg = (k * talla_cm) / creatinina if talla_cm > 0 else 0.0
    elif edad_anos < 18:
        formula = "Schwartz Bedside 2009"
        vfg = (0.413 * talla_cm) / creatinina if talla_cm > 0 else 0.0
    else:
        formula = "Cockcroft-Gault"
        if peso_kg > 0:
            es_mujer = str(sexo_bio).lower() in ["femenino","f","fem","mujer"]
            vfg = (((140 - int(edad_anos)) * peso_kg) / (72 * creatinina)) * (0.85 if es_mujer else 1.0)
        else:
            vfg = 0.0
    return round(vfg, 2), formula


def _alerta_vfg(vfg, fecha_nac_raw):
    """Misma lógica de alertas que admin(96) — pediatría y adultos."""
    if vfg <= 0:
        return "Cálculo pendiente", "#888888"
    hoy = date.today()
    if isinstance(fecha_nac_raw, str):
        try: fn = datetime.strptime(fecha_nac_raw[:10], "%d/%m/%Y").date()
        except: fn = hoy
    elif isinstance(fecha_nac_raw, datetime): fn = fecha_nac_raw.date()
    elif isinstance(fecha_nac_raw, date): fn = fecha_nac_raw
    else: fn = hoy

    edad_anos  = (hoy - fn).days / 365.25
    edad_meses = (hoy - fn).days / 30.4

    if edad_anos < 2:
        if edad_meses <= 0.25: mn, mx = 15, 30
        elif edad_meses <= 1:  mn, mx = 30, 50
        elif edad_meses <= 2:  mn, mx = 40, 65
        elif edad_meses <= 4:  mn, mx = 55, 85
        elif edad_meses <= 12: mn, mx = 70, 110
        else:                  mn, mx = 85, 125
        if vfg < mn * 0.7:  return "🔴 ALTO RIESGO: VFG Crítica para maduración neonatal", "#FF0000"
        if vfg < mn:        return "⚠️ RIESGO INTERMEDIO: Retraso en maduración renal", "#FFCC00"
        if vfg <= mx:       return "✅ SIN RIESGO: VFG Adecuada para la edad", "#28A745"
        return "🔵 REVISAR: Posible hiperfiltración", "#007BFF"
    else:
        if vfg <= 30:  return "🔴 ALTO RIESGO para la administración de medio de contraste", "#FF0000"
        if vfg <= 59:  return "⚠️ RIESGO INTERMEDIO para la administración de medio de contraste", "#FFCC00"
        return "✅ SIN RIESGO para la administración de medio de contraste", "#28A745"


# =============================================================================
# BANDEJA DE PACIENTES — usa estado_validacion == "PENDIENTE" (igual a admin96)
# =============================================================================
@st.fragment(run_every=60)
def _bandeja_pacientes(db):
    hora = datetime.now(tz_chile).strftime("%H:%M:%S")
    st.markdown(
        f"<div style='font-size:11px;font-weight:700;color:#475569;margin-bottom:4px;"
        f"text-transform:uppercase;letter-spacing:.5px'>Pacientes en espera</div>"
        f"<div style='font-size:9px;color:#94a3b8;margin-bottom:8px'>"
        f"✨ Auto-refresco · {hora}</div>",
        unsafe_allow_html=True,
    )
    filtro = st.text_input("🔍", placeholder="Buscar nombre o RUT…",
                           key="filtro_bandeja", label_visibility="collapsed")

    # ── QUERY CORREGIDA: estado_validacion == "PENDIENTE" (como admin96) ──
    try:
        docs = list(db.collection("encuestas")
                      .where(filter=FieldFilter("estado_validacion", "==", "PENDIENTE"))
                      .stream())
    except Exception:
        # Fallback: encuesta_validada == False
        try:
            docs = list(db.collection("encuestas")
                          .where("encuesta_validada", "==", False)
                          .order_by("fecha_creacion", direction="DESCENDING")
                          .limit(50).get())
        except Exception as e:
            st.error(f"Error bandeja: {e}"); return

    st.session_state["badge_panel"] = len(docs)

    # Ordenar por fecha
    ahora = datetime.now(tz_chile)
    lista = []
    for doc in docs:
        d = doc.to_dict()
        f_raw = d.get("fecha_examen") or d.get("fecha") or d.get("Fecha") or ""
        try:
            if hasattr(f_raw, "astimezone"):
                f_str = f_raw.astimezone(tz_chile).strftime("%d/%m/%Y")
            else:
                f_str = datetime.strptime(str(f_raw)[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            f_str = str(f_raw)[:10] if f_raw else "Sin fecha"
        hoy_str = ahora.strftime("%d/%m/%Y")
        if f_str == hoy_str: etiq = "🟢 HOY"
        elif not f_str or f_str == "Sin fecha": etiq = "⚪"
        else: etiq = f"🗓️ {f_str}"
        lista.append((doc.id, d, etiq))

    if filtro:
        fl = filtro.lower()
        lista = [(i,d,e) for i,d,e in lista
                 if fl in d.get("nombre","").lower() or fl in d.get("rut","").lower()]

    if not lista:
        st.info("✅ Sin pacientes pendientes")
        if st.button("🔄 Actualizar", key="btn_upd_vacia", use_container_width=True):
            st.rerun()
        return

    col_upd, col_del, col_clean = st.columns(3)
    if col_upd.button("🔄", key="btn_upd", use_container_width=True, help="Actualizar"):
        st.rerun()
    if col_del.button("🗑️", key="btn_del", use_container_width=True, help="Eliminar seleccionado"):
        if st.session_state.get("paciente_id"):
            db.collection("encuestas").document(st.session_state.paciente_id).delete()
            for k in ["paciente_id","doc_completo","fhir_bundle"]:
                st.session_state[k] = None
            st.rerun()
    if col_clean.button("🧹", key="btn_cln", use_container_width=True, help="Limpiar validados"):
        try:
            for doc in db.collection("encuestas").where(
                filter=FieldFilter("estado_validacion","==","VALIDADO")).stream():
                db.collection("encuestas").document(doc.id).delete()
            st.rerun()
        except Exception: pass

    for doc_id, d, etiq in lista:
        activo  = st.session_state.paciente_id == doc_id
        vfg     = float(d.get("vfg", 0))
        cte     = d.get("tiene_contraste", False)
        if cte and vfg > 0 and vfg <= 30:   riesgo = "🔴 VFG crítica"
        elif cte and vfg > 0 and vfg <= 59: riesgo = "⚠️ VFG intermedia"
        elif cte:                            riesgo = "✅ VFG OK"
        else:                                riesgo = "Sin contraste"

        st.markdown(
            f"<div style='border:{'2px solid #800020' if activo else '1px solid #e2e8f0'};"
            f"border-left:{'4px solid #800020' if activo else '3px solid #94a3b8'};"
            f"background:{'#fdf2f4' if activo else '#fff'};"
            f"border-radius:8px;padding:9px 12px;margin-bottom:4px'>"
            f"<div style='font-size:9px;color:#64748b'>{etiq}</div>"
            f"<div style='font-weight:700;font-size:12px;color:#1e293b'>"
            f"{d.get('nombre','Sin nombre')}</div>"
            f"<div style='font-size:10px;color:#64748b'>"
            f"{d.get('rut','S/D')} · {d.get('procedimiento','S/P')[:35]}</div>"
            f"<div style='font-size:10px;color:#64748b;margin-top:3px'>{riesgo}</div>"
            f"</div>", unsafe_allow_html=True,
        )
        if st.button("Seleccionar →", key=f"sel_{doc_id}", use_container_width=True):
            st.session_state.paciente_id  = doc_id
            st.session_state.doc_completo = d
            st.session_state.fhir_bundle  = _cripto.desencriptar_seguro(
                d.get("fhir_bundle_aes256_gcm","")
            )
            st.session_state.doc_aprobado = False
            st.session_state.firma_canvas = None
            # Cargar VFG desde Firestore como punto de partida
            st.session_state.vfg_crea_tm     = float(d.get("creatinina", 0.0))
            st.session_state.vfg_peso_tm     = float(d.get("peso", 0.0))
            st.session_state.vfg_talla_tm    = float(d.get("talla", 0.0))
            st.session_state.vfg_contraste_tm= bool(d.get("tiene_contraste", False))
            st.session_state.vfg_calculada_tm= float(d.get("vfg", 0.0))
            msg, col = _alerta_vfg(float(d.get("vfg",0)), d.get("fecha_nac"))
            st.session_state.vfg_msg_tm   = msg
            st.session_state.vfg_color_tm = col
            st.rerun()


# =============================================================================
# PANEL DE DETALLE
# =============================================================================
def _panel_detalle(db, bucket, usuario: dict):
    d = st.session_state.doc_completo or {}
    nombre = d.get("nombre", "Paciente")
    rut    = d.get("rut") or d.get("num_doc","S/D")
    proc   = d.get("procedimiento","S/P")

    c_nom, c_tag = st.columns([3, 1])
    c_nom.markdown(
        f"<div style='font-size:16px;font-weight:800;color:#1e293b'>{nombre}</div>"
        f"<div style='font-size:11px;color:#64748b'>RUT/Doc: {rut}</div>",
        unsafe_allow_html=True,
    )
    c_tag.markdown(
        f"<div style='padding-top:8px'>"
        f"<span style='background:{'#dbeafe' if d.get('tiene_contraste') else '#f1f5f9'};"
        f"color:{'#1e40af' if d.get('tiene_contraste') else '#475569'};"
        f"font-size:10px;font-weight:600;padding:3px 8px;border-radius:8px'>"
        f"{'💉 Con contraste' if d.get('tiene_contraste') else 'Sin contraste'}</span></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='font-size:11px;color:#475569;margin-top:3px;margin-bottom:10px'>"
        f"📋 {proc}</div>"
        f"<hr style='border:none;border-top:1px solid #e2e8f0;margin:0 0 8px'>",
        unsafe_allow_html=True,
    )

    _subsec_identificacion(d, bucket)
    _subsec_bioseguridad(d)
    _subsec_clinicos(d)
    _subsec_condiciones(d)
    _subsec_quirurgico(d)
    _subsec_examenes(d, bucket)
    _subsec_vfg(d, db)          # ← VFG interactiva
    _bloque_firma(db, bucket, usuario, d)


# ── COMPONENTE TOGGLE ──────────────────────────────────────────────
def _subsec(titulo, key, emoji):
    exp = st.session_state.sec_expandidas.get(key, False)
    flecha = "▲" if exp else "▼"
    st.markdown(
        f"<div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:7px;"
        f"padding:8px 12px;margin-bottom:3px;display:flex;"
        f"justify-content:space-between;align-items:center'>"
        f"<span style='font-weight:700;font-size:12px;color:#374151'>"
        f"{emoji} {titulo}</span>"
        f"<span style='color:#94a3b8;font-size:11px'>{flecha}</span></div>",
        unsafe_allow_html=True,
    )
    if st.button(f"·{titulo}", key=f"tgl_{key}", label_visibility="collapsed",
                 use_container_width=True):
        st.session_state.sec_expandidas[key] = not exp
        st.rerun()
    return exp


def _campo(col, label, value, estado="normal"):
    c = {"ok":"#16a34a","danger":"#dc2626","warn":"#d97706","normal":"#1e293b"}.get(estado,"#1e293b")
    col.markdown(
        f"<div style='background:#f8fafc;border-radius:5px;padding:5px 8px;margin-bottom:5px'>"
        f"<div style='font-size:9px;color:#94a3b8;text-transform:uppercase;letter-spacing:.4px'>"
        f"{label}</div>"
        f"<div style='font-size:11px;font-weight:600;color:{c};margin-top:1px'>"
        f"{value}</div></div>", unsafe_allow_html=True,
    )


# ── 1. IDENTIFICACIÓN ─────────────────────────────────────────────
def _subsec_identificacion(d, bucket):
    if not _subsec("1. IDENTIFICACIÓN DEL PACIENTE","identificacion","🪪"): return
    fn   = d.get("fecha_nac","")
    try:
        fd = datetime.strptime(str(fn)[:10], "%d/%m/%Y").date()
        ev = edad_visual(fd)
    except Exception:
        ev = "S/D"
    fes = d.get("firma_electronica",{})
    hsh = fes.get("hash_sha256","")

    c1,c2 = st.columns(2)
    _campo(c1,"Nombre completo", d.get("nombre","S/D"))
    _campo(c2,"RUT / Documento", d.get("rut") or f"{d.get('tipo_doc','')} {d.get('num_doc','')}")
    _campo(c1,"Fecha nacimiento", fn)
    _campo(c2,"Edad", ev)
    _campo(c1,"Email", d.get("email","S/D"))
    _campo(c2,"Teléfono", d.get("telefono","S/D"))
    _campo(c1,"Procedencia", f"{d.get('procedencia','S/D')} {d.get('unidad_procedencia','')}")
    _campo(c2,"IP Dispositivo Paciente", d.get("ip_paciente","No registrada"))
    _campo(c1,"FES",
           "✅ Verificado" if fes.get("estado")=="FIRMADO" else "⚠️ Pendiente",
           "ok" if fes.get("estado")=="FIRMADO" else "warn")
    _campo(c2,"SHA-256", f"{hsh[:8]}…{hsh[-8:]}" if len(hsh)>16 else hsh or "S/D")
    if d.get("nombre_tutor"):
        st.markdown(
            f"<div style='background:#eff6ff;border:1px solid #bfdbfe;border-radius:6px;"
            f"padding:8px;font-size:11px;color:#1e40af;margin-top:4px'>"
            f"👨‍👦 <strong>Representante:</strong> {d['nombre_tutor']} — "
            f"{d.get('parentesco_tutor','')} · "
            f"{d.get('rut_tutor') or d.get('num_doc_tutor','S/D')}</div>",
            unsafe_allow_html=True,
        )
    ruta_f = d.get("url_firma_storage","")
    if ruta_f:
        try:
            blob = bucket.blob(ruta_f)
            tmp  = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            blob.download_to_filename(tmp.name)
            st.markdown("<div style='font-size:11px;font-weight:600;color:#374151;margin:6px 0 3px'>"
                        "Firma del Paciente / Representante:</div>", unsafe_allow_html=True)
            st.image(tmp.name, width=220)
            os.unlink(tmp.name)
        except Exception:
            st.caption("⚠️ Firma no disponible temporalmente")
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


# ── 2. BIOSEGURIDAD ────────────────────────────────────────────────
def _subsec_bioseguridad(d):
    if not _subsec("2. BIOSEGURIDAD MAGNÉTICA","bioseguridad","🧲"): return
    c1,c2 = st.columns(2)
    m = d.get("bio_marcapaso","No"); i = d.get("bio_implantes","No")
    _campo(c1,"Marcapasos cardiaco", m, "danger" if m=="Sí" else "ok")
    _campo(c2,"Implantes / Prótesis / Dispositivos", i, "danger" if i=="Sí" else "ok")
    if d.get("bio_detalle"):
        st.markdown(
            f"<div style='background:#fef2f2;border:1px solid #fecaca;border-radius:6px;"
            f"padding:7px;font-size:11px;color:#991b1b;margin-top:3px'>"
            f"⚠️ {d['bio_detalle']}</div>", unsafe_allow_html=True,
        )
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


# ── 3. ANTECEDENTES CLÍNICOS ───────────────────────────────────────
def _subsec_clinicos(d):
    if not _subsec("3. ANTECEDENTES CLÍNICOS","clinicos","🩺"): return
    keys = [
        ("Ayuno ≥2h","clin_ayuno"),("Asma","clin_asma"),
        ("Hipertensión","clin_hiperten"),("Hipertiroidismo","clin_hipertiroid"),
        ("Diabetes","clin_diabetes"),("Alergias","clin_alergico"),
        ("Metformina 48h","clin_metformina"),("Insuf. Renal","clin_renal"),
        ("Diálisis","clin_dialisis"),("Embarazo","clin_embarazo"),
        ("Lactancia","clin_lactancia"),("Claustrofobia","clin_claustro"),
    ]
    cols = st.columns(3)
    for idx,(label,key) in enumerate(keys):
        v = d.get(key,"No")
        _campo(cols[idx%3], label, v, "danger" if v=="Sí" else "ok")
    al = d.get("alergias_detalles","").strip()
    if al:
        st.markdown(
            f"<div style='background:#fef2f2;border:1px solid #fecaca;border-radius:6px;"
            f"padding:7px;font-size:11px;color:#991b1b;margin-top:4px'>"
            f"⚠️ <strong>Alergias:</strong> {al}</div>", unsafe_allow_html=True,
        )
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


# ── 4. CONDICIONES ESPECIALES ─────────────────────────────────────
def _subsec_condiciones(d):
    if not _subsec("4. CONDICIONES ESPECIALES","condiciones","♿"): return
    conds = d.get("condiciones",[])
    det   = d.get("condicion_detalle","")
    if conds:
        for c in conds:
            st.markdown(
                f"<div style='background:#eff6ff;border-left:3px solid #2563eb;"
                f"padding:5px 10px;font-size:11px;color:#1e40af;margin-bottom:3px'>"
                f"• {c}</div>", unsafe_allow_html=True,
            )
    if det: st.caption(f"Detalle: {det}")
    if not conds and not det:
        st.markdown("<div style='color:#64748b;font-size:11px;padding:5px 0'>"
                    "Sin condiciones declaradas</div>", unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


# ── 5. QUIRÚRGICO ─────────────────────────────────────────────────
def _subsec_quirurgico(d):
    if not _subsec("5. ANTECEDENTES QUIRÚRGICOS","quirurgico","🔪"): return
    c1,c2 = st.columns(2)
    cir = d.get("quir_cirugia_check","No")
    can = d.get("quir_cancer_check","No")
    _campo(c1,"Cirugías previas", cir, "warn" if cir=="Sí" else "ok")
    _campo(c2,"Antecedente oncológico", can, "danger" if can=="Sí" else "ok")
    if cir=="Sí" and d.get("quir_cirugia_detalle"):
        st.caption(f"Detalle: {d['quir_cirugia_detalle']}")
    if can=="Sí":
        trats = [k for k in ["rt","qt","bt","it"] if d.get(k) in ("Sí",True)]
        st.markdown(
            f"<div style='font-size:11px;color:#991b1b;margin-top:3px'>"
            f"Tratamientos: {', '.join(trats).upper() if trats else 'No especificados'} "
            f"| {d.get('quir_cancer_detalle','')}</div>", unsafe_allow_html=True,
        )
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


# ── 6. EXÁMENES ANTERIORES ────────────────────────────────────────
def _subsec_examenes(d, bucket):
    if not _subsec("6. EXÁMENES ANTERIORES","examenes","📁"): return
    if d.get("has_examenes_previos") != "Sí":
        st.markdown("<div style='color:#64748b;font-size:11px;padding:5px 0'>"
                    "No refiere exámenes anteriores</div>", unsafe_allow_html=True)
    else:
        tipos = [k.upper().replace("ex_","") for k in
                 ["ex_rx","ex_mg","ex_eco","ex_tc","ex_rm"] if d.get(k)]
        if tipos:
            st.markdown(f"<div style='font-size:11px;color:#374151;margin-bottom:5px'>"
                        f"Tipos: <strong>{'  ·  '.join(tipos)}</strong></div>",
                        unsafe_allow_html=True)
        for i in ["1","2"]:
            link = d.get(f"link_exam_{i}","").strip()
            pin  = d.get(f"pin_exam_{i}","").strip()
            if link:
                st.markdown(
                    f"<a href='{link}' target='_blank' style='font-size:11px;color:#2563eb'>"
                    f"🔗 Link {i}</a>"
                    f"{'  |  PIN: '+pin if pin else ''}",
                    unsafe_allow_html=True,
                )
        for ruta in d.get("url_examenes_firebase",[]):
            try:
                url = bucket.blob(ruta).generate_signed_url(expiration=300)
                st.markdown(
                    f"<a href='{url}' target='_blank' style='font-size:11px;color:#2563eb;"
                    f"display:block;margin-bottom:2px'>"
                    f"📎 {os.path.basename(ruta)}</a>", unsafe_allow_html=True,
                )
            except Exception:
                st.caption(f"📎 {os.path.basename(ruta)}")
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


# ── 7. VFG INTERACTIVA (igual a admin96 — editable por el TM) ─────
def _subsec_vfg(d: dict, db):
    if not _subsec("7. VFG Y ADMINISTRACIÓN FARMACOLÓGICA","vfg","🧪"): return

    fn_raw   = d.get("fecha_nac","")
    sexo_bio = d.get("genero_biologico") or d.get("genero","Masculino")

    # Toggle contraste (TM puede corregirlo)
    tiene_contraste = st.toggle(
        "💉 Con Contraste",
        value=st.session_state.vfg_contraste_tm,
        key="tgl_contraste_vfg",
    )
    st.session_state.vfg_contraste_tm = tiene_contraste

    if not tiene_contraste:
        st.markdown(
            "<div style='background:#f0fdf4;border:1px solid #bbf7d0;border-radius:7px;"
            "padding:10px;font-size:11px;color:#166534;margin-bottom:8px'>"
            "✅ Examen sin medio de contraste. VFG no requerida.</div>",
            unsafe_allow_html=True,
        )
        _tabla_farm_vacia()
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        return

    # Detectar si es pediátrico para mostrar talla o peso
    hoy = date.today()
    try:
        for fmt in ("%d/%m/%Y","%Y-%m-%d"):
            try: fn_d = datetime.strptime(str(fn_raw)[:10], fmt).date(); break
            except: continue
        else: fn_d = hoy
    except Exception: fn_d = hoy
    edad_anos = (hoy - fn_d).days / 365.25
    es_ped    = edad_anos < 18

    if edad_anos < 2:   label_et = "🍼 Lactante"
    elif edad_anos < 14: label_et = "🧸 Pediátrico"
    elif edad_anos < 18: label_et = "🛹 Adolescente"
    else:                label_et = "🧑🏻‍⚕️ Adulto"

    st.markdown(
        f"<div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:7px;"
        f"padding:7px 12px;font-size:11px;color:#374151;margin-bottom:8px'>"
        f"{label_et} · {sexo_bio} · {'Schwartz' if es_ped else 'Cockcroft-Gault'}</div>",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    st.session_state.vfg_crea_tm = c1.number_input(
        "Creatinina (mg/dL)",
        value=st.session_state.vfg_crea_tm,
        step=0.01, min_value=0.0, key="inp_crea_vfg",
    )
    if es_ped:
        st.session_state.vfg_talla_tm = c2.number_input(
            "Talla (cm)",
            value=st.session_state.vfg_talla_tm,
            step=0.5, min_value=0.0, key="inp_talla_vfg",
        )
        peso_val = 0.0
    else:
        st.session_state.vfg_peso_tm = c2.number_input(
            "Peso (kg)",
            value=st.session_state.vfg_peso_tm,
            step=0.1, min_value=0.0, key="inp_peso_vfg",
        )
        peso_val = st.session_state.vfg_peso_tm

    f_crea = c3.date_input("Fecha Creatinina",
                            value=date.today(), key="fecha_crea_vfg")

    # Botón recalcular
    if st.button("⚡ CALCULAR / ACTUALIZAR VFG", use_container_width=True, key="btn_calc_vfg"):
        crea  = st.session_state.vfg_crea_tm
        talla = st.session_state.vfg_talla_tm if es_ped else 0.0
        peso  = st.session_state.vfg_peso_tm  if not es_ped else 0.0

        if crea <= 0:
            st.error("Ingrese la creatinina sérica."); return
        if es_ped and talla <= 0:
            st.error("Ingrese la talla en cm para el cálculo pediátrico."); return
        if not es_ped and peso <= 0:
            st.error("Ingrese el peso en kg."); return

        vfg, formula = _calcular_vfg_universal(fn_raw, sexo_bio, crea, talla, peso)
        msg, col     = _alerta_vfg(vfg, fn_raw)
        st.session_state.vfg_calculada_tm = vfg
        st.session_state.vfg_msg_tm       = msg
        st.session_state.vfg_color_tm     = col

        # Actualizar en Firestore para que el PDF tome el valor nuevo
        try:
            db.collection("encuestas").document(
                st.session_state.paciente_id
            ).update({
                "vfg":             vfg,
                "creatinina":      crea,
                "peso":            peso,
                "talla":           talla,
                "tiene_contraste": tiene_contraste,
                "fecha_creatinina":str(f_crea),
                "formula_vfg":     formula,
            })
            # Actualizar caché local
            st.session_state.doc_completo["vfg"]           = vfg
            st.session_state.doc_completo["creatinina"]    = crea
            st.session_state.doc_completo["tiene_contraste"]= tiene_contraste
        except Exception as e:
            st.warning(f"VFG calculada pero no guardada: {e}")
        st.rerun()

    # Mostrar resultado VFG
    vfg   = st.session_state.vfg_calculada_tm
    msg   = st.session_state.vfg_msg_tm
    color = st.session_state.vfg_color_tm

    if vfg > 0:
        if vfg <= 30:   bg, borde = "#fef2f2","#dc2626"
        elif vfg <= 59: bg, borde = "#fffbeb","#d97706"
        else:           bg, borde = "#f0fdf4","#16a34a"
        st.markdown(
            f"<div style='background:{bg};border:2px solid {borde};border-radius:9px;"
            f"padding:14px;text-align:center;margin:8px 0'>"
            f"<div style='font-size:11px;color:#64748b'>VFG Estimada</div>"
            f"<div style='font-size:30px;font-weight:800;color:{color}'>{vfg:.2f}</div>"
            f"<div style='font-size:11px;color:#64748b'>ml/min/1.73m²</div>"
            f"<div style='font-size:12px;font-weight:700;color:{color};margin-top:5px'>"
            f"{msg}</div></div>",
            unsafe_allow_html=True,
        )
        # Recomendación ESUR 2023
        if 0 < vfg <= 30:
            st.markdown(
                "<div style='background:#fef2f2;border:1px solid #fecaca;border-radius:6px;"
                "padding:8px;font-size:11px;color:#991b1b;margin-top:5px'>"
                "⛔ <strong>ESUR 2023:</strong> VFG ≤30 ml/min. Contraindicado GBCA de baja "
                "estabilidad. Evaluar con radiólogo antes de proceder.</div>",
                unsafe_allow_html=True,
            )
        elif 30 < vfg <= 59:
            st.markdown(
                "<div style='background:#fffbeb;border:1px solid #fde68a;border-radius:6px;"
                "padding:8px;font-size:11px;color:#92400e;margin-top:5px'>"
                "⚠️ <strong>ESUR 2023:</strong> VFG 30-60 ml/min. GBCA macrocíclico a "
                "0.1 mmol/kg. Hidratación pre-examen recomendada.</div>",
                unsafe_allow_html=True,
            )

    # Tabla de administración farmacológica
    st.markdown(
        "<div style='font-size:11px;font-weight:700;color:#374151;margin:10px 0 5px'>"
        "Registro de Administración Farmacológica:</div>",
        unsafe_allow_html=True,
    )
    _tabla_farm(d)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


def _tabla_farm(d: dict):
    fa1, fa2, fa3 = st.columns(3)
    fa1.text_input("Acceso Vascular", key="farm_acceso_tm",
                   placeholder="Ej: Vía periférica")
    fa2.text_input("Sitio de Punción", key="farm_sitio_tm",
                   placeholder="Ej: Fosa antecubital D")
    fa3.text_input("Cantidad Contraste (ml)", key="farm_cantidad_tm",
                   placeholder="Ej: 15")
    st.caption("Los datos de administración quedarán registrados en el PDF al aprobar.")


def _tabla_farm_vacia():
    st.markdown(
        "<div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:7px;"
        "padding:9px 12px;font-size:11px;color:#94a3b8'>Tabla farmacológica "
        "no requerida (sin contraste)</div>",
        unsafe_allow_html=True,
    )


# =============================================================================
# FIRMA DIGITAL DEL PROFESIONAL
# =============================================================================
def _bloque_firma(db, bucket, usuario: dict, d: dict, fhir: dict = None):
    nombre_prof = usuario.get("nombre","")
    sis_prof    = usuario.get("sis","")
    rol_prof    = usuario.get("rol","tm")

    st.markdown(
        "<div style='background:#fff;border:1px solid #e2e8f0;border-radius:10px;"
        "padding:14px 16px;margin-top:10px'>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div style='font-size:13px;font-weight:700;color:#1e293b;margin-bottom:8px'>"
        "✍️ Firma Digital del Profesional</div>",
        unsafe_allow_html=True,
    )
    canvas_res = st_canvas(
        stroke_width=3, stroke_color="#000", background_color="#fff",
        height=100, width=380, key="canvas_firma_tm",
    )
    if canvas_res and canvas_res.image_data is not None:
        st.session_state.firma_canvas = canvas_res.image_data

    firma_valida = (
        st.session_state.firma_canvas is not None
        and np.any(st.session_state.firma_canvas[:,:,3] > 0)
    )
    st.markdown(
        "<div style='background:#fef2f2;border:1px solid #fecaca;border-radius:6px;"
        "padding:8px;font-size:11px;color:#991b1b;margin:8px 0'>"
        "⚠️ Al ingresar su PIN certifica bajo Sello Criptográfico SHA-256 que revisó "
        "todos los antecedentes y validó los riesgos del procedimiento.</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='font-size:11px;font-weight:600;color:#374151;margin-bottom:3px'>"
        f"{nombre_prof} · SIS {sis_prof} · "
        f"<span style='color:#800020'>{_cargo_a_texto(rol_prof)}</span></div>",
        unsafe_allow_html=True,
    )
    pin_col, btn_col = st.columns([2,1])
    pin_input = pin_col.text_input(
        "PIN", type="password", placeholder="PIN de 6 dígitos",
        key="pin_firma_tm", label_visibility="collapsed",
    )
    if btn_col.button("🔒 APROBAR Y SELLAR", type="primary", use_container_width=True):
        _procesar_firma(db, bucket, usuario, d, pin_input, firma_valida)
    if st.session_state.doc_aprobado:
        st.success("✅ Documento sellado y guardado correctamente.")
    st.markdown("</div>", unsafe_allow_html=True)


def _procesar_firma(db, bucket, usuario, d, pin_input, firma_valida):
    if not firma_valida:
        st.error("🚨 Dibuje su firma en el recuadro."); return
    if not pin_input:
        st.error("🚨 Ingrese su PIN."); return
    if not validar_pin(pin_input, usuario.get("hash","")):
        st.error("❌ PIN incorrecto.")
        _log(db, usuario, "FIRMA_FALLIDA", d.get("rut","")); return

    nombre_prof = usuario.get("nombre","")
    sis_prof    = usuario.get("sis","")
    rol_prof    = usuario.get("rol","tm")
    ahora_str   = datetime.now(tz_chile).strftime("%d/%m/%Y %H:%M:%S")

    # Guardar firma TM en Storage
    blob_n = ""
    try:
        img = Image.fromarray(st.session_state.firma_canvas.astype("uint8"),"RGBA")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            img.save(tmp.name)
            rut_lmp = str(d.get("rut","SR")).replace(".","").replace("-","")
            blob_n  = f"firmas_tm/{rut_lmp}_{sis_prof}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            bucket.blob(blob_n).upload_from_filename(tmp.name, content_type="image/png")
        os.unlink(tmp.name)
    except Exception as e:
        st.warning(f"Firma guardada localmente. Storage: {e}")

    # Generar PDF validado (diseño idéntico a admin96)
    _, id_verif, nombre_pdf = generar_id_documento(
        "CONSENTIMIENTO", db, d.get("nombre",""), d.get("rut",""),
    )
    rut_pac = d.get("rut") or d.get("num_doc","")

    pdf = PDFNorteImagen("CONSENTIMIENTO", config={
        "id_verificacion": id_verif,
        "rut_paciente":    rut_pac,
        "ip_paciente":     d.get("ip_paciente",""),
        "nombre_paciente": d.get("nombre",""),
    })
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=12)

    pdf.section_title("1","IDENTIFICACIÓN DEL PACIENTE")
    pdf.data_field_2col([
        ("Nombre",     d.get("nombre","")),
        ("RUT/Doc",    rut_pac),
        ("Edad",       d.get("edad","S/D")),
        ("Procedencia",d.get("procedencia","S/D")),
    ])
    pdf.data_field("Procedimiento", d.get("procedimiento","S/P"))
    contraste = st.session_state.vfg_contraste_tm
    pdf.data_field("Medio de contraste", "SÍ" if contraste else "NO")

    if contraste and st.session_state.vfg_calculada_tm > 0:
        pdf.section_title("7","VFG Y ADMINISTRACIÓN FARMACOLÓGICA")
        vfg = st.session_state.vfg_calculada_tm
        pdf.data_field("Creatinina", f"{st.session_state.vfg_crea_tm} mg/dL")
        pdf.data_field("VFG Estimada", f"{vfg:.2f} ml/min/1.73m²")
        msg, _ = _alerta_vfg(vfg, d.get("fecha_nac",""))
        pdf.data_field("Riesgo", msg)
        # Tabla farmacológica
        acceso   = st.session_state.get("farm_acceso_tm","")
        sitio    = st.session_state.get("farm_sitio_tm","")
        cantidad = st.session_state.get("farm_cantidad_tm","")
        if acceso or sitio:
            pdf.data_field("Acceso Vascular", acceso)
            pdf.data_field("Sitio de Punción", sitio)
            pdf.data_field("Cantidad Contraste (ml)", cantidad)

    huella    = pdf.estampar_sello_digital(nombre_prof, sis_prof, rol_prof, ahora_str)
    pdf_bytes = pdf.compilar()

    # AuditEvent FHIR
    ahora_iso = datetime.now(tz_chile).isoformat()
    audit     = FHIRBuilder.audit_event(
        "VALIDACION_DOCUMENTO", nombre_prof, sis_prof,
        st.session_state.paciente_id, ahora_iso,
        f"Documento {id_verif} | SHA-256: {huella}",
    )

    try:
        db.collection("encuestas").document(st.session_state.paciente_id).update({
            "encuesta_validada":  True,
            "estado_validacion":  "VALIDADO",
            "fecha_validacion":   ahora_str,
            "validado_por":       nombre_prof,
            "sis_validador":      sis_prof,
            "rol_validador":      rol_prof,
            "url_firma_tm":       blob_n,
            "id_verificacion_tm": id_verif,
            "huella_sha256_tm":   huella,
            "pdf_validado_nombre":nombre_pdf,
            "audit_validacion":   audit,
            "tiene_contraste":    contraste,
            "administracion_farm":{
                "acceso":   st.session_state.get("farm_acceso_tm",""),
                "sitio":    st.session_state.get("farm_sitio_tm",""),
                "cantidad": st.session_state.get("farm_cantidad_tm",""),
            },
        })
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tp:
            tp.write(pdf_bytes)
            bucket.blob(f"pdfs_validados/{nombre_pdf}").upload_from_filename(
                tp.name, content_type="application/pdf",
            )
        os.unlink(tp.name)
        _log(db, usuario, "DOCUMENTO_VALIDADO", d.get("rut",""), f"ID: {id_verif}")
        st.session_state.doc_aprobado = True
        st.session_state["badge_panel"] = max(0,
            st.session_state.get("badge_panel",0)-1)
    except Exception as e:
        st.error(f"Error al guardar: {e}"); return

    st.download_button("📥 Descargar PDF Validado",
                       data=pdf_bytes, file_name=nombre_pdf,
                       mime="application/pdf", use_container_width=True)


# =============================================================================
# UTILIDADES
# =============================================================================
def _actualizar_badges(db):
    try:
        n = sum(1 for _ in db.collection("encuestas").where(
            filter=FieldFilter("estado_validacion","==","PENDIENTE")).stream())
        st.session_state["badge_panel"] = n
    except Exception:
        pass


def _log(db, usuario, accion, rut="", detalle=""):
    try:
        db.collection("trazabilidad").add({
            "modulo": "panel_principal", "accion": accion,
            "profesional": usuario.get("nombre",""), "sis": usuario.get("sis",""),
            "rol": usuario.get("rol",""), "rut_paciente": rut,
            "detalle": detalle, "timestamp": datetime.now(tz_chile).isoformat(),
        })
    except Exception:
        pass

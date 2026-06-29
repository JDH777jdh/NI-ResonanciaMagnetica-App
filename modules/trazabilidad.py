# modules/trazabilidad.py — TRAZABILIDAD (AuditEvent FHIR por módulo)
from datetime import datetime
import pytz, streamlit as st
import pandas as pd

tz_chile = pytz.timezone("America/Santiago")

_MODULOS = {
    "panel_principal":   ("🏠","Panel Principal"),
    "motor_rescate":     ("💓","Motor de Rescate"),
    "certificados":      ("📄","Certificados"),
    "insumos":           ("📦","Insumos"),
    "farmacos":          ("💊","Fármacos"),
    "eventos_seguridad": ("🛡️","Eventos de Seguridad"),
}

_ACCIONES = [
    "Todas","VALIDACION_DOCUMENTO","APERTURA_FICHA","DESCARGA_PDF",
    "ADENDUM_DOCUMENTO","RECETA_EMITIDA","EMISION_CERTIFICADO",
    "AJUSTE_STOCK","ALTA_INSUMO","EVENTO_REGISTRADO","LOGIN_FALLIDO",
]


def render(db, bucket, usuario: dict):
    rol = usuario.get("rol","")
    if rol not in ("tm_coordinador","radiologo_coordinador",
                   "medico_coordinador","calidad","owner"):
        st.warning("⛔ Acceso restringido a Coordinadores y Calidad."); return

    # Tabs por módulo
    tabs = st.tabs(["🔍 Global"] + [f"{v[0]} {v[1]}"
                    for v in _MODULOS.values()])
    with tabs[0]:
        _log_global(db, usuario)
    for i, (mod_id, (ico, label)) in enumerate(_MODULOS.items(), 1):
        with tabs[i]:
            _log_modulo(db, mod_id, label, usuario)


def _filtros(key_pfx: str, modulo_fijo: str = None):
    """Barra de filtros reutilizable."""
    c1, c2, c3, c4 = st.columns([2,1.5,1.5,1])
    busq    = c1.text_input("🔍 Buscar:", key=f"{key_pfx}_busq",
                             placeholder="RUT, nombre, profesional…",
                             label_visibility="collapsed")
    periodo = c2.selectbox("Período:", ["Hoy","Últimas 48h","Esta semana",
                                        "Este mes","Todos"],
                            key=f"{key_pfx}_per")
    accion  = c3.selectbox("Acción:", _ACCIONES if not modulo_fijo else ["Todas"] + [
                                a for a in _ACCIONES
                                if a != "Todas"],
                            key=f"{key_pfx}_ac")
    exportar = c4.button("⬇️ CSV", key=f"{key_pfx}_exp")
    return busq, periodo, accion, exportar


def _query_trazabilidad(db, modulo: str = None,
                         accion: str = None, limite: int = 200):
    try:
        q = db.collection("trazabilidad").order_by(
            "timestamp", direction="DESCENDING"
        ).limit(limite)
        return q.get()
    except Exception as e:
        st.error(f"Error al cargar trazabilidad: {e}")
        return []


def _filtrar_por_periodo(docs, periodo: str):
    ahora = datetime.now(tz_chile)
    deltas = {
        "Hoy":         1,  "Últimas 48h":  2,
        "Esta semana": 7,  "Este mes":    31,
        "Todos":       99999,
    }
    dias = deltas.get(periodo, 99999)
    resultado = []
    for doc in docs:
        d = doc.to_dict()
        try:
            ts = datetime.fromisoformat(d.get("timestamp",""))
            if not ts.tzinfo:
                ts = tz_chile.localize(ts)
            if (ahora - ts).days <= dias:
                resultado.append(d)
        except Exception:
            resultado.append(d)
    return resultado


def _log_global(db, usuario: dict):
    busq, periodo, accion, exportar = _filtros("global")
    docs = _query_trazabilidad(db, limite=300)
    filas = _procesar_docs(docs, busq, periodo, accion, None)
    _mostrar_tabla(filas, exportar, "trazabilidad_global.csv")


def _log_modulo(db, mod_id: str, label: str, usuario: dict):
    busq, periodo, accion, exportar = _filtros(mod_id, mod_id)
    docs = _query_trazabilidad(db, limite=200)
    filas = _procesar_docs(docs, busq, periodo, accion, mod_id)
    st.markdown(
        f"<div style='font-size:11px;color:#475569;margin-bottom:6px'>"
        f"Mostrando eventos del módulo <strong>{label}</strong></div>",
        unsafe_allow_html=True,
    )
    _mostrar_tabla(filas, exportar, f"trazabilidad_{mod_id}.csv")


def _procesar_docs(docs, busq, periodo, accion, modulo_fijo):
    filas = []
    ahora = datetime.now(tz_chile)
    deltas = {"Hoy":1,"Últimas 48h":2,"Esta semana":7,"Este mes":31,"Todos":99999}
    dias   = deltas.get(periodo, 99999)

    for doc in docs:
        d = doc.to_dict()
        try:
            ts  = datetime.fromisoformat(d.get("timestamp",""))
            if not ts.tzinfo: ts = tz_chile.localize(ts)
            if (ahora - ts).days > dias: continue
        except Exception:
            pass
        if modulo_fijo and d.get("modulo","") != modulo_fijo:
            continue
        if accion and accion != "Todas" and d.get("accion","") != accion:
            continue
        txt = " ".join([d.get("profesional",""), d.get("rut_paciente",""),
                        d.get("detalle","")]).lower()
        if busq and busq.lower() not in txt:
            continue
        filas.append({
            "Fecha/Hora":  d.get("timestamp","")[:16],
            "Módulo":      _MODULOS.get(d.get("modulo",""),("","S/M"))[1],
            "Profesional": d.get("profesional",""),
            "SIS":         d.get("sis",""),
            "Acción":      d.get("accion",""),
            "Paciente":    d.get("rut_paciente",""),
            "Detalle":     (d.get("detalle","")[:60]+"…"
                           if len(d.get("detalle",""))>60
                           else d.get("detalle","")),
        })
    return filas


def _mostrar_tabla(filas: list, exportar: bool, nombre_csv: str):
    if not filas:
        st.info("Sin eventos para los filtros seleccionados.")
        return
    st.markdown(
        f"<div style='font-size:11px;color:#64748b;margin-bottom:4px'>"
        f"<strong>{len(filas)}</strong> registros</div>",
        unsafe_allow_html=True,
    )
    df = pd.DataFrame(filas)
    st.dataframe(df, use_container_width=True, hide_index=True, height=380)
    if exportar:
        st.download_button("⬇️ Descargar CSV",
                           data=df.to_csv(index=False).encode("utf-8-sig"),
                           file_name=nombre_csv, mime="text/csv",
                           use_container_width=True)

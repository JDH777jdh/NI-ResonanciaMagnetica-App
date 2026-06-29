# =============================================================================
# admin_main.py — ORQUESTADOR PRINCIPAL Norte Imagen Admin v3
# =============================================================================
# Responsabilidad única: autenticación + sidebar + enrutamiento a módulos.
# NO contiene lógica clínica. Cada módulo vive en modules/<nombre>.py
#
# Módulos disponibles (cada uno en su propio archivo):
#   modules/panel_principal.py   → Bandeja validación + 7 subsecciones clínicas
#   modules/motor_rescate.py     → Adendum / enmiendas 48h
#   modules/certificados.py      → Certificados + sugerencias + historial
#   modules/insumos.py           → Bodega central
#   modules/farmacos.py          → Triaje + receta médica + historial
#   modules/trazabilidad.py      → AuditEvent FHIR por sección
#   modules/eventos_seguridad.py → GCL 2.3 MINSAL
# =============================================================================

import importlib
import os
from datetime import datetime

import firebase_admin
import pytz
import streamlit as st
from firebase_admin import credentials, firestore, storage

# Motor compartido
from norte_imagen_core import (
    GestorCriptografico,
    _cargo_a_texto,
    validar_pin,
)

tz_chile = pytz.timezone("America/Santiago")

# =============================================================================
# SECCIÓN 1 — CONFIGURACIÓN ÚNICA DE PÁGINA
# =============================================================================
from PIL import Image as _PIL_Image

_logo_path = os.path.join(os.path.dirname(__file__), "assets", "logoNI_pg.png")
try:
    _icono = _PIL_Image.open(_logo_path)
except Exception:
    _icono = "🏥"

st.set_page_config(
    page_title="Norte Imagen — Panel Clínico",
    page_icon=_icono,
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# SECCIÓN 2 — CSS GLOBAL EMPRESA (inyección única)
# =============================================================================
def _inyectar_css():
    st.markdown("""
    <style>
    /* ── RESET MODO CLARO ─────────────────────────── */
    html,body,[class*="css"],.stApp,p,span,div,label,li{color:#1e293b !important}
    .stApp,[data-testid="stAppViewContainer"],[data-testid="stHeader"]{
        background-color:#f8fafc !important}
    [data-testid="stSidebar"]{
        background-color:#0f172a !important;
        border-right:1px solid rgba(255,255,255,0.06) !important}
    [data-testid="stSidebar"] *{color:#94a3b8 !important}
    [data-testid="stSidebarContent"]{padding:0 !important}

    /* ── TIPOGRAFÍA ───────────────────────────────── */
    h1{font-size:1.4rem !important;font-weight:800 !important;color:#1e293b !important}
    h2,h3{color:#800020 !important;font-weight:700 !important}
    .section-header{
        color:#800020 !important;border-bottom:2px solid #800020 !important;
        padding-bottom:5px;margin:20px 0 12px;font-size:1.1em;font-weight:700}

    /* ── BOTONES ──────────────────────────────────── */
    .stButton>button{
        background-color:#800020 !important;color:#ffffff !important;
        border-radius:8px;font-weight:700;transition:all .25s;border:none}
    .stButton>button:hover{
        background-color:#600018 !important;
        box-shadow:0 4px 12px rgba(128,0,32,0.35) !important;
        transform:translateY(-1px)}
    .stButton>button *{color:#ffffff !important;-webkit-text-fill-color:#fff !important}

    /* Botón outline secundario */
    [data-testid="baseButton-secondary"]>button{
        background-color:transparent !important;
        border:1px solid #800020 !important;
        color:#800020 !important}

    /* ── INPUTS ───────────────────────────────────── */
    div[data-baseweb="input"]>div,
    div[data-baseweb="textarea"]>div,
    div[data-baseweb="select"]>div{
        background-color:#ffffff !important;
        border:1px solid #cbd5e1 !important;border-radius:7px !important}
    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea{
        color:#1e293b !important;-webkit-text-fill-color:#1e293b !important}
    div[data-baseweb="input"]>div:focus-within{
        border-color:#800020 !important;
        box-shadow:0 0 0 3px rgba(128,0,32,0.15) !important}

    /* ── TARJETAS ─────────────────────────────────── */
    .ni-card{
        background:#ffffff;border:1px solid #e2e8f0;
        border-radius:10px;padding:14px 16px;margin-bottom:10px}
    .ni-card-danger{border-left:4px solid #dc2626}
    .ni-card-warn{border-left:4px solid #d97706}
    .ni-card-ok{border-left:4px solid #16a34a}
    .ni-card-info{border-left:4px solid #2563eb}

    /* ── TAGS / BADGES ────────────────────────────── */
    .tag{display:inline-flex;align-items:center;gap:4px;
         font-size:10px;font-weight:600;padding:2px 8px;
         border-radius:12px;border:1px solid}
    .tag-red{background:#fef2f2;color:#991b1b !important;border-color:#fecaca}
    .tag-green{background:#f0fdf4;color:#166534 !important;border-color:#bbf7d0}
    .tag-amber{background:#fffbeb;color:#92400e !important;border-color:#fde68a}
    .tag-blue{background:#eff6ff;color:#1e40af !important;border-color:#bfdbfe}
    .tag-purple{background:#faf5ff;color:#6b21a8 !important;border-color:#e9d5ff}
    .tag-gray{background:#f1f5f9;color:#475569 !important;border-color:#cbd5e1}

    /* ── VFG ─────────────────────────────────────── */
    .vfg-ok{background:#f0fdf4;border:2px solid #16a34a;
            border-radius:8px;padding:10px;text-align:center}
    .vfg-warn{background:#fffbeb;border:2px solid #d97706;
              border-radius:8px;padding:10px;text-align:center}
    .vfg-danger{background:#fef2f2;border:2px solid #dc2626;
                border-radius:8px;padding:10px;text-align:center}

    /* ── MULTISELECT ─────────────────────────────── */
    span[data-baseweb="tag"]{background-color:#78909c !important;border-radius:4px !important}
    span[data-baseweb="tag"] span{
        color:#ffffff !important;-webkit-text-fill-color:#fff !important;font-weight:600}
    span[data-baseweb="tag"] svg{fill:#ffffff !important}

    /* ── TABS ────────────────────────────────────── */
    .stTabs [data-baseweb="tab"]{
        color:#64748b !important;font-weight:500;
        padding:7px 18px;border-radius:6px 6px 0 0}
    .stTabs [aria-selected="true"]{
        color:#800020 !important;font-weight:700 !important;
        background:rgba(128,0,32,0.08) !important}

    /* ── SCROLLBAR ───────────────────────────────── */
    ::-webkit-scrollbar{width:5px;height:5px}
    ::-webkit-scrollbar-track{background:#f1f5f9}
    ::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:4px}
    ::-webkit-scrollbar-thumb:hover{background:#94a3b8}

    /* ── SIDEBAR STREAMLIT NATIVO ─────────────────── */
    section[data-testid="stSidebar"] .stButton>button{
        background-color:rgba(255,255,255,0.06) !important;
        color:#e2e8f0 !important;border:1px solid rgba(255,255,255,0.1) !important;
        text-align:left;justify-content:flex-start;width:100%;
        border-radius:7px;font-size:12px;font-weight:500;margin-bottom:2px}
    section[data-testid="stSidebar"] .stButton>button:hover{
        background-color:rgba(128,0,32,0.25) !important;
        color:#fff !important;transform:none}
    section[data-testid="stSidebar"] .stButton>button.activo{
        background:linear-gradient(90deg,rgba(128,0,32,0.5),
                                         rgba(128,0,32,0.2)) !important;
        border-left:3px solid #800020 !important;color:#fff !important}

    /* ── HIDE STREAMLIT DEFAULTS ─────────────────── */
    #MainMenu,footer,[data-testid="stToolbar"]{display:none !important}
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# SECCIÓN 3 — FIREBASE SINGLETON
# =============================================================================
@st.cache_resource
def _init_firebase():
    try:
        return firebase_admin.get_app()
    except ValueError:
        cred_dict = dict(st.secrets["firebase"])
        bucket_url = cred_dict.pop("bucket_url",
                                   "firmas-encuestaconsentimiento.firebasestorage.app")
        if "private_key" in cred_dict:
            raw  = cred_dict["private_key"]
            b64  = __import__("re").sub(r'-----.*?PRIVATE KEY-----', '', raw)
            b64  = __import__("re").sub(r'\s+', '', b64)
            chunks = [b64[i:i+64] for i in range(0, len(b64), 64)]
            cred_dict["private_key"] = (
                "-----BEGIN PRIVATE KEY-----\n"
                + "\n".join(chunks)
                + "\n-----END PRIVATE KEY-----\n"
            )
        cred = credentials.Certificate(cred_dict)
        return firebase_admin.initialize_app(cred, {"storageBucket": bucket_url})


# =============================================================================
# SECCIÓN 4 — MAPA DE MÓDULOS Y PERMISOS
# =============================================================================
# Estructura: id → {label, icono, archivo_modulo, roles_permitidos, badge_key}
# badge_key: clave en st.session_state con conteo para el badge numérico
# roles_permitidos: lista de roles con acceso. "owner" siempre tiene acceso a todo.

MODULOS = [
    {
        "id":      "panel_principal",
        "label":   "Panel Principal",
        "icono":   "🏠",
        "modulo":  "modules.panel_principal",
        "roles":   ["tm", "tm_coordinador", "tens", "radiologo",
                    "radiologo_coordinador", "calidad"],
        "badge":   "badge_panel",
    },
    {
        "id":      "motor_rescate",
        "label":   "Motor de Rescate",
        "icono":   "💓",
        "modulo":  "modules.motor_rescate",
        "roles":   ["tm", "tm_coordinador", "radiologo",
                    "radiologo_coordinador", "calidad"],
        "badge":   "badge_rescate",
    },
    {
        "id":      "certificados",
        "label":   "Emisión Certificados",
        "icono":   "📄",
        "modulo":  "modules.certificados",
        "roles":   ["tm", "tm_coordinador", "secretaria", "calidad"],
        "badge":   "badge_certs",
    },
    {
        "id":      "insumos",
        "label":   "Gestión de Insumos",
        "icono":   "📦",
        "modulo":  "modules.insumos",
        "roles":   ["tm", "tm_coordinador", "tens", "calidad", "secretaria"],
        "badge":   None,
    },
    {
        "id":      "farmacos",
        "label":   "Gestión Médica Fármacos",
        "icono":   "💊",
        "modulo":  "modules.farmacos",
        "roles":   ["tm", "tm_coordinador", "tens",
                    "radiologo", "radiologo_coordinador", "calidad"],
        "badge":   "badge_farmacos",
    },
    {
        "id":      "trazabilidad",
        "label":   "Trazabilidad",
        "icono":   "🔍",
        "modulo":  "modules.trazabilidad",
        "roles":   ["tm_coordinador", "radiologo_coordinador", "calidad"],
        "badge":   None,
    },
    {
        "id":      "eventos_seguridad",
        "label":   "Eventos de Seguridad",
        "icono":   "🛡️",
        "modulo":  "modules.eventos_seguridad",
        "roles":   ["tm", "tm_coordinador", "radiologo",
                    "radiologo_coordinador", "calidad", "tens"],
        "badge":   "badge_eventos",
    },
]

# Orden visual de los roles en el sidebar
_LABEL_ROL = {
    "owner":                 "Dirección Técnica",   # invisible para todos
    "tm":                    "Tecnólogo Médico",
    "tm_coordinador":        "TM Coordinador",
    "radiologo":             "Médico Radiólogo",
    "radiologo_coordinador": "Radiólogo Coordinador",
    "secretaria":            "Secretaria",
    "tens":                  "TENS",
    "calidad":               "Encargada de Calidad",
}


# =============================================================================
# SECCIÓN 5 — SESIÓN GLOBAL
# =============================================================================
def _init_session():
    defaults = {
        "autenticado":    False,
        "usuario":        {},
        "vista_actual":   "panel_principal",
        # Badges (se actualizan en cada módulo)
        "badge_panel":    0,
        "badge_rescate":  0,
        "badge_certs":    0,
        "badge_farmacos": 0,
        "badge_eventos":  0,
        # Caché de paciente seleccionado
        "paciente_id":    None,
        "doc_completo":   None,
        "fhir_bundle":    None,   # FHIR desencriptado del paciente actual
        # Caché de módulos importados dinámicamente
        "_modulos_cache": {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# =============================================================================
# SECCIÓN 6 — AUTENTICACIÓN
# =============================================================================
def _pantalla_login(db):
    """Login institucional. Renderiza en la vista centrada."""
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Logo
        for ruta_l in ["assets/logoNI.png", "logoNI.png"]:
            if os.path.exists(ruta_l):
                st.image(ruta_l, use_column_width=True)
                break
        else:
            st.markdown(
                "<h2 style='text-align:center;color:#800020'>NORTE IMAGEN</h2>",
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<h3 style='text-align:center;color:#1e293b'>Panel Clínico Admin</h3>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align:center;color:#64748b;font-size:13px'>"
            "Sistema de Gestión Clínica RM — Norte Imagen v3.0</p>",
            unsafe_allow_html=True,
        )
        st.markdown("---")

        usuario_input = st.text_input("Usuario", placeholder="usuario@norteimagn.cl",
                                      key="login_user")
        pin_input     = st.text_input("PIN", type="password",
                                      placeholder="••••••", key="login_pin")

        if st.button("Ingresar al Sistema", use_container_width=True):
            if not usuario_input or not pin_input:
                st.error("Ingrese usuario y PIN.")
                return

            try:
                # Buscar usuario en Firestore
                docs = (db.collection("usuarios")
                          .where("usuario", "==", usuario_input.strip().lower())
                          .limit(1)
                          .get())
                if not docs:
                    st.error("Usuario no encontrado.")
                    return

                doc_usr = docs[0].to_dict()
                hash_almacenado = doc_usr.get("password_hash", "")

                if not validar_pin(pin_input, hash_almacenado):
                    st.error("PIN incorrecto.")
                    _registrar_intento_fallido(db, usuario_input)
                    return

                if not doc_usr.get("activo", True):
                    st.error("Cuenta desactivada. Contacte a administración.")
                    return

                # Login exitoso
                st.session_state.autenticado = True
                st.session_state.usuario = {
                    "id":       docs[0].id,
                    "nombre":   doc_usr.get("nombre", ""),
                    "usuario":  doc_usr.get("usuario", ""),
                    "rol":      doc_usr.get("rol", "tm"),
                    "sis":      doc_usr.get("registro_sis", ""),
                    "hash":     hash_almacenado,
                }
                st.rerun()

            except Exception as e:
                st.error(f"Error de conexión: {e}")

        st.markdown(
            "<p style='text-align:center;color:#94a3b8;font-size:11px;margin-top:16px'>"
            "© 2026 Norte Imagen — Todos los derechos reservados</p>",
            unsafe_allow_html=True,
        )


def _registrar_intento_fallido(db, usuario: str):
    """Registra intento fallido en Firestore para auditoría."""
    try:
        db.collection("auditoria_acceso").add({
            "usuario":  usuario,
            "evento":   "LOGIN_FALLIDO",
            "timestamp": datetime.now(tz_chile).isoformat(),
        })
    except Exception:
        pass


# =============================================================================
# SECCIÓN 7 — SIDEBAR ENTERPRISE
# =============================================================================
def _renderizar_sidebar(usuario: dict, db):
    """
    Sidebar con:
      - Avatar de iniciales + nombre + rol + SIS
      - Navegación con badges numéricos
      - Links rápidos
      - Botón cerrar sesión
    El rol 'owner' tiene acceso a TODOS los módulos pero
    su label aparece como "Director Técnico" (nunca "owner").
    """
    with st.sidebar:
        # ── Logo ─────────────────────────────────────────────
        st.markdown("""
        <div style="padding:14px 16px 10px;border-bottom:1px solid rgba(255,255,255,0.07)">
          <div style="color:#fff;font-size:14px;font-weight:800;letter-spacing:.3px">
            🏥 Norte Imagen
          </div>
          <div style="color:#475569;font-size:10px;margin-top:2px">
            Sistema Clínico RM v3.0
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Tarjeta de usuario ────────────────────────────────
        nombre  = usuario.get("nombre", "")
        rol     = usuario.get("rol", "tm")
        sis     = usuario.get("sis", "")
        iniciales = "".join(p[0].upper() for p in nombre.split() if p)[:2]
        # Owner: mostrar como rol clínico, no "owner"
        label_rol = _LABEL_ROL.get(rol, rol.replace("_", " ").title())

        st.markdown(f"""
        <div style="margin:10px 10px 0;background:rgba(255,255,255,0.05);
             border:1px solid rgba(255,255,255,0.08);border-radius:10px;
             padding:10px 12px;display:flex;align-items:center;gap:10px">
          <div style="width:36px;height:36px;border-radius:50%;flex-shrink:0;
               background:linear-gradient(135deg,#800020,#c0002a);
               display:flex;align-items:center;justify-content:center;
               color:#fff;font-weight:800;font-size:13px">{iniciales}</div>
          <div style="overflow:hidden">
            <div style="color:#e2e8f0;font-size:12px;font-weight:600;
                 white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
              {nombre}
            </div>
            <div style="color:#64748b;font-size:10px">{label_rol}</div>
            {"<div style='color:#475569;font-size:10px'>SIS: "+sis+"</div>" if sis else ""}
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(
            "<div style='color:#475569;font-size:10px;font-weight:600;"
            "letter-spacing:.8px;text-transform:uppercase;"
            "padding:14px 14px 4px'>Herramientas Clínicas</div>",
            unsafe_allow_html=True,
        )

        # ── Navegación ─────────────────────────────────────────
        vista_actual = st.session_state.vista_actual
        for mod in MODULOS:
            # Filtro de acceso
            if rol != "owner" and rol not in mod["roles"]:
                continue

            badge_n = int(st.session_state.get(mod["badge"] or "_", 0))
            badge_txt = f"  [{badge_n}]" if badge_n > 0 else ""
            label_btn = f"{mod['icono']}  {mod['label']}{badge_txt}"
            activo    = vista_actual == mod["id"]

            if st.button(
                label_btn,
                key=f"nav_{mod['id']}",
                use_container_width=True,
                type="primary" if activo else "secondary",
            ):
                st.session_state.vista_actual = mod["id"]
                # Limpiar paciente al cambiar de módulo
                st.session_state.paciente_id  = None
                st.session_state.doc_completo  = None
                st.session_state.fhir_bundle   = None
                st.rerun()

        # ── Links rápidos ──────────────────────────────────────
        st.markdown(
            "<div style='height:1px;background:rgba(255,255,255,0.07);"
            "margin:10px 14px'></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='color:#475569;font-size:10px;font-weight:600;"
            "letter-spacing:.8px;text-transform:uppercase;"
            "padding:4px 14px 4px'>Accesos Rápidos</div>",
            unsafe_allow_html=True,
        )
        for label, url in [
            ("📱  Portal Pacientes", "https://cdnorteimagen.cl"),
            ("🔗  RIS / PACS",       "https://ris.cdnorteimagen.cl"),
            ("📋  Normativa MINSAL", "https://www.minsal.cl/normativa"),
        ]:
            st.markdown(
                f"<a href='{url}' target='_blank' "
                f"style='display:block;color:#475569;font-size:11px;"
                f"padding:4px 14px;text-decoration:none;"
                f"transition:color .15s'>{label}</a>",
                unsafe_allow_html=True,
            )

        # ── Cerrar sesión ──────────────────────────────────────
        st.markdown(
            "<div style='height:1px;background:rgba(255,255,255,0.07);"
            "margin:10px 14px 6px'></div>",
            unsafe_allow_html=True,
        )
        if st.button("🔒  Cerrar Sesión",
                     key="btn_logout", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


# =============================================================================
# SECCIÓN 8 — BARRA SUPERIOR (breadcrumb + reloj + acción rápida)
# =============================================================================
def _barra_superior(mod_info: dict):
    label  = mod_info.get("label", "")
    icono  = mod_info.get("icono", "")
    ahora  = datetime.now(tz_chile).strftime("%d/%m/%Y  %H:%M")

    col_bread, col_mid, col_right = st.columns([4, 2, 1.5])
    with col_bread:
        st.markdown(
            f"<div style='font-size:11px;color:#94a3b8;margin-bottom:2px'>"
            f"Sistema &nbsp;/&nbsp; <span style='color:#1e293b;font-weight:600'>"
            f"{label}</span></div>"
            f"<h2 style='margin:0;font-size:17px;color:#1e293b'>"
            f"{icono}&nbsp; {label}</h2>",
            unsafe_allow_html=True,
        )
    with col_mid:
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:8px;margin-top:14px'>"
            f"<span style='width:8px;height:8px;border-radius:50%;"
            f"background:#16a34a;display:inline-block'></span>"
            f"<span style='font-size:11px;color:#16a34a'>Operativo</span>"
            f"&nbsp;&nbsp;"
            f"<span style='font-size:11px;color:#64748b'>{ahora}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_right:
        st.markdown("<div style='margin-top:10px'>", unsafe_allow_html=True)
        if st.button("⟳  Actualizar", key="btn_refresh_top",
                     use_container_width=True):
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        "<hr style='border:none;border-top:1px solid #e2e8f0;margin:8px 0 16px'>",
        unsafe_allow_html=True,
    )


# =============================================================================
# SECCIÓN 9 — ENRUTADOR DINÁMICO DE MÓDULOS
# =============================================================================
def _cargar_modulo(mod_id: str):
    """
    Importa dinámicamente modules/<mod_id>.py y llama a render().
    Cachea el módulo importado para no re-importar en cada rerun.
    """
    cache = st.session_state._modulos_cache
    if mod_id not in cache:
        try:
            cache[mod_id] = importlib.import_module(f"modules.{mod_id}")
        except ModuleNotFoundError:
            st.warning(
                f"⚙️ Módulo **{mod_id}** aún no implementado. "
                f"Crea `modules/{mod_id}.py` con una función `render(db, bucket, usuario)`."
            )
            return

    mod = cache[mod_id]
    if not hasattr(mod, "render"):
        st.error(f"El módulo `modules/{mod_id}.py` no expone la función `render()`.")
        return

    db     = firestore.client()
    bucket = storage.bucket()
    mod.render(db=db, bucket=bucket, usuario=st.session_state.usuario)


# =============================================================================
# SECCIÓN 10 — PUNTO DE ENTRADA
# =============================================================================
def main():
    _inyectar_css()
    _init_session()
    _init_firebase()
    db = firestore.client()

    # ── Sin autenticar: mostrar login ─────────────────────────────
    if not st.session_state.autenticado:
        _pantalla_login(db)
        return

    usuario = st.session_state.usuario
    rol     = usuario.get("rol", "")

    # ── Sidebar ───────────────────────────────────────────────────
    _renderizar_sidebar(usuario, db)

    # ── Verificar acceso al módulo actual ─────────────────────────
    vista = st.session_state.vista_actual
    mod_info = next((m for m in MODULOS if m["id"] == vista), None)

    if not mod_info:
        st.session_state.vista_actual = "panel_principal"
        st.rerun()
        return

    if rol != "owner" and rol not in mod_info["roles"]:
        st.warning("⛔ No tienes permisos para acceder a este módulo.")
        st.session_state.vista_actual = "panel_principal"
        st.rerun()
        return

    # ── Barra superior ────────────────────────────────────────────
    _barra_superior(mod_info)

    # ── Renderizar módulo ─────────────────────────────────────────
    _cargar_modulo(vista)


if __name__ == "__main__":
    main()

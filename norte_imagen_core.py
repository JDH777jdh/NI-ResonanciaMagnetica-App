# =============================================================================
# norte_imagen_core.py
# MOTOR COMPARTIDO — Norte Imagen Sistema Clínico v3
# Importado por: admin_main.py, appv3.py y todos los módulos
# =============================================================================
# Contiene:
#   · PDFNorteImagen     → Motor PDF institucional unificado (reemplaza 7 clases)
#   · GestorCriptografico → AES-256 GCM bidireccional
#   · FHIRBuilder        → Constructor de recursos HL7 FHIR R4
#   · SelloDigital       → QR + SHA-256 (reemplaza 2 funciones estampar_sello)
#   · validar_pin        → Única función de validación PIN (solo hash)
#   · generar_id_doc     → Correlativo atómico Firestore
#   · Utilidades clínicas compartidas
# =============================================================================

import base64
import hashlib
import json
import os
import re
import tempfile
from datetime import date, datetime
from typing import Optional

import pyotp
import pytz
import qrcode
import streamlit as st
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fpdf import FPDF
from werkzeug.security import check_password_hash

tz_chile = pytz.timezone("America/Santiago")

# =============================================================================
# SECCIÓN 1 — CATÁLOGO DE TIPOS DE DOCUMENTO
# Cada tipo tiene: título header, subtítulo, sufijo SHA-256, prefijo ID
# =============================================================================
CATALOGO_DOCS = {
    # ── Consentimientos ──────────────────────────────────────────────
    "CONSENTIMIENTO": {
        "titulo":   "ENCUESTA DE RIESGOS ASOCIADOS Y CONSENTIMIENTO INFORMADO",
        "subtitulo":"ENCUESTA PRE-PROCEDIMIENTO",
        "sha_sfx":  "CONSENTIMIENTO_INFORMADO_FES_LEY19799",
        "id_pfx":   ("REG-PRE",  "CONSI"),
        "ip_footer": True,
        "adendum":  False,
    },
    "ADENDUM": {
        "titulo":   "ADENDUM DE CONSENTIMIENTO INFORMADO",
        "subtitulo":"ENMIENDA OFICIAL — Ley 20.584",
        "sha_sfx":  "ADENDUM_CONSENTIMIENTO_LEY20584",
        "id_pfx":   ("ADENDUM",  "ADND"),
        "ip_footer": True,
        "adendum":  True,
    },
    # ── Certificados ─────────────────────────────────────────────────
    "ASISTENCIA": {
        "titulo":   "CERTIFICADO DE ASISTENCIA",
        "subtitulo":"DOCUMENTO INSTITUCIONAL",
        "sha_sfx":  "CERTIFICADO_ASISTENCIA_INSTITUCIONAL",
        "id_pfx":   ("C-ASIST",  "CDARM"),
        "ip_footer": False,
        "adendum":  False,
    },
    "HISTORICO": {
        "titulo":   "CERTIFICADO DE ASISTENCIA HISTÓRICO",
        "subtitulo":"REINGRESO DOCUMENTAL",
        "sha_sfx":  "CERTIFICADO_HISTORICO_INSTITUCIONAL",
        "id_pfx":   ("C-HIST",   "CDAHRM"),
        "ip_footer": False,
        "adendum":  False,
    },
    "SUGERENCIA": {
        "titulo":   "SUGERENCIA CLÍNICA AL DERIVADOR",
        "subtitulo":"INFORME DE HALLAZGOS PRELIMINARES",
        "sha_sfx":  "SUGERENCIA_DERIVADOR_INSTITUCIONAL",
        "id_pfx":   ("C-SUGER",  "CDSRM"),
        "ip_footer": False,
        "adendum":  False,
    },
    # ── Farmacología ─────────────────────────────────────────────────
    "RECETA": {
        "titulo":   "RECETA MÉDICA ELECTRÓNICA",
        "subtitulo":"PRESCRIPCIÓN MÉDICA ELECTRÓNICA",
        "sha_sfx":  "RECETA_MEDICA_ELECTRONICA_NORTE_IMAGEN",
        "id_pfx":   ("R-MED",    "RMED"),
        "ip_footer": False,
        "adendum":  False,
    },
    "REPORTE_RECETAS": {
        "titulo":   "REGISTRO MENSUAL DE PRESCRIPCIONES",
        "subtitulo":"CONSOLIDADO FARMACOLÓGICO",
        "sha_sfx":  "REPORTE_MENSUAL_RECETAS",
        "id_pfx":   ("RPT-REC",  "RPTREC"),
        "ip_footer": False,
        "adendum":  False,
    },
    # ── Calidad y Seguridad ───────────────────────────────────────────
    "INCIDENTE": {
        "titulo":   "REPORTE OFICIAL DE INCIDENTE",
        "subtitulo":"DEPARTAMENTO DE CALIDAD Y SEGURIDAD",
        "sha_sfx":  "REPORTE_SEGURIDAD_MINSAL_GCL23",
        "id_pfx":   ("EV-SEG",   "EVSEG"),
        "ip_footer": False,
        "adendum":  False,
    },
    "REPORTE_GCL": {
        "titulo":   "CONSOLIDADO ESTADÍSTICO GCL 2.3",
        "subtitulo":"INDICADORES DE SEGURIDAD MINSAL",
        "sha_sfx":  "CONSOLIDADO_GCL_MINSAL",
        "id_pfx":   ("RPT-GCL",  "RPTGCL"),
        "ip_footer": False,
        "adendum":  False,
    },
    # ── Insumos ───────────────────────────────────────────────────────
    "INSUMOS": {
        "titulo":   "INFORME DE MOVIMIENTO DE INSUMOS",
        "subtitulo":"BODEGA CENTRAL — CONTROL DE STOCK",
        "sha_sfx":  "INFORME_INSUMOS_BODEGA",
        "id_pfx":   ("INS",      "INSBOD"),
        "ip_footer": False,
        "adendum":  False,
    },
}


# =============================================================================
# SECCIÓN 2 — PDFNorteImagen (Motor PDF Unificado)
# Reemplaza: PDF_Certificado, PDF_Receta_Professional, PDF_Recetas_Institucional,
#            PDF_Balance_Avanzado, PDF_Incidente_Institucional,
#            PDF_Mensual_Institucional, PDF_Institucional
# =============================================================================
class PDFNorteImagen(FPDF):
    """
    Motor PDF institucional único de Norte Imagen.

    Uso:
        pdf = PDFNorteImagen("ASISTENCIA", config={
            "id_verificacion": "CDARM000042",
            "rut_paciente":    "12.345.678-9",
            "ip_paciente":     "186.10.42.1",   # Solo para CONSENTIMIENTO/ADENDUM
            "periodo":         "Junio 2026",    # Para reportes mensuales
            "hash_original":   "A3F2...",       # Solo para ADENDUM
        })
        pdf.add_page()
        pdf.section_title("1", "IDENTIFICACIÓN DEL PACIENTE")
        pdf.data_field("Nombre", "Juan Torres")
        huella = pdf.estampar_sello_digital("Carlos Molina", "84231-7", "tm")
        raw = pdf.compilar()
    """

    def __init__(self, tipo_doc: str, config: dict = None):
        super().__init__()
        tipo_doc = tipo_doc.upper()
        if tipo_doc not in CATALOGO_DOCS:
            raise ValueError(f"tipo_doc '{tipo_doc}' no está en CATALOGO_DOCS.")

        self.tipo_doc   = tipo_doc
        self.meta       = CATALOGO_DOCS[tipo_doc]
        self.cfg        = config or {}

        # Atributos del documento
        self.id_verificacion = self.cfg.get("id_verificacion", "PENDIENTE")
        self.rut_paciente    = self.cfg.get("rut_paciente", "S/R")
        self.ip_paciente     = self.cfg.get("ip_paciente", "")
        self.periodo         = self.cfg.get("periodo", "")
        self.hash_original   = self.cfg.get("hash_original", "")
        self.nombre_paciente = self.cfg.get("nombre_paciente", "")

        self._ahora = datetime.now(tz_chile)

    # ── UTILIDADES ────────────────────────────────────────────────────
    def c(self, txt) -> str:
        """Sanitiza texto para Latin-1 (FPDF). Fuente única de verdad."""
        if txt is None:
            return ""
        return (str(txt)
                .replace("á","a").replace("é","e").replace("í","i")
                .replace("ó","o").replace("ú","u").replace("ü","u")
                .replace("Á","A").replace("É","E").replace("Í","I")
                .replace("Ó","O").replace("Ú","U")
                .replace("ñ","n").replace("Ñ","N")
                .encode("latin-1", "replace").decode("latin-1"))

    def _set_burdeos(self): self.set_text_color(128, 0, 32)
    def _set_negro(self):   self.set_text_color(0, 0, 0)
    def _set_gris(self):    self.set_text_color(110, 110, 110)
    def _set_blanco(self):  self.set_text_color(255, 255, 255)
    def _set_rojo(self):    self.set_text_color(185, 28, 28)

    # ── HEADER ADAPTATIVO ─────────────────────────────────────────────
    def header(self):
        # Logo (izquierda)
        for ruta in ["logoNI.png", "assets/logoNI.png",
                     os.path.join(os.path.dirname(__file__), "assets", "logoNI.png")]:
            if os.path.exists(ruta):
                self.image(ruta, 11, 11, 30)
                break

        # Banner rojo adendum (SOLO para ADENDUM)
        if self.meta["adendum"]:
            self.set_fill_color(185, 28, 28)
            self._set_blanco()
            self.set_font("Arial", "B", 8)
            self.set_xy(0, 0)
            self.cell(0, 8,
                self.c("  DOCUMENTO RECTIFICADO / ADENDUM — Ley 20.584"),
                0, 1, "L", fill=True)
            self._set_negro()
            self.ln(2)

        # Bloque de títulos (derecha)
        self.set_font("Arial", "B", 11)
        self._set_burdeos()
        # Título principal (puede ser 1 o 2 líneas según longitud)
        titulo = self.meta["titulo"]
        if len(titulo) > 42:
            mitad = titulo.find(" ", len(titulo)//2)
            self.cell(0, 6, self.c(titulo[:mitad]), 0, 1, "R")
            self.cell(0, 6, self.c(titulo[mitad+1:]), 0, 1, "R")
        else:
            self.cell(0, 7, self.c(titulo), 0, 1, "R")

        # Subtítulo
        self.set_font("Arial", "B", 9)
        subtitulo = self.meta["subtitulo"]
        if self.periodo:
            subtitulo += f" — {self.periodo}"
        self.cell(0, 5, self.c(subtitulo), 0, 1, "R")

        # Servicio (siempre)
        self.set_font("Arial", "B", 15)
        self.cell(0, 7, "RESONANCIA MAGNETICA", 0, 1, "R")

        # Fecha/hora emisión
        self.set_font("Arial", "B", 8)
        self._set_gris()
        self.cell(0, 5,
            self.c(f"Emitido: {self._ahora.strftime('%d/%m/%Y')} "
                   f"{self._ahora.strftime('%H:%M')} hrs"),
            0, 1, "R")
        self._set_negro()
        self.ln(8)

    # ── FOOTER ADAPTATIVO ─────────────────────────────────────────────
    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 6.5)
        self._set_gris()
        ts = self._ahora.strftime("%d/%m/%Y %H:%M:%S")

        # Texto izquierdo: varía por tipo
        if self.meta["ip_footer"] and self.ip_paciente:
            # CONSENTIMIENTO y ADENDUM incluyen IP del paciente
            txt_izq = (f"Certificado Digital Norte Imagen RM | "
                       f"RUT Pac.: {self.rut_paciente} | "
                       f"IP Dispositivo Paciente: {self.ip_paciente} | "
                       f"{ts}")
            if self.meta["adendum"]:
                txt_izq += " | ADENDUM OFICIAL"
            else:
                txt_izq += " | ORIGINAL PRE-ADMISION"
        elif self.tipo_doc in ("RECETA", "REPORTE_RECETAS"):
            txt_izq = (f"Receta Medica Electronica Norte Imagen RM | "
                       f"RUT Pac.: {self.rut_paciente} | "
                       f"Folio: {self.id_verificacion} | {ts}")
        elif self.tipo_doc in ("INCIDENTE", "REPORTE_GCL"):
            txt_izq = (f"Reporte Institucional Norte Imagen RM | "
                       f"Folio GCL: {self.id_verificacion} | "
                       f"Descarga: {ts}")
        elif self.tipo_doc == "INSUMOS":
            txt_izq = (f"Informe Bodega Norte Imagen RM | "
                       f"Periodo: {self.periodo} | {ts}")
        else:
            # Certificados sin IP
            txt_izq = (f"Documento Institucional Norte Imagen RM | "
                       f"RUT Pac.: {self.rut_paciente} | "
                       f"Validado TM | {ts}")

        # Texto derecho: siempre pagina + ID verificacion
        txt_der = f"Pag. {self.page_no()}/{{nb}} | ID: {self.id_verificacion}"

        self.cell(140, 10, self.c(txt_izq), 0, 0, "L")
        self.cell(0, 10, self.c(txt_der), 0, 0, "R")

    # ── COMPONENTES ───────────────────────────────────────────────────
    def section_title(self, num: str, label: str):
        """Barra gris con número y texto burdeos."""
        self.set_font("Arial", "B", 10)
        self.set_fill_color(230, 230, 230)
        self._set_burdeos()
        self.cell(0, 7, self.c(f"{num}. {label}"), 0, 1, "L", fill=True)
        self._set_negro()
        self.ln(2)

    def section_title_dark(self, label: str):
        """Barra burdeos con texto blanco (reportes y eventos)."""
        self.set_font("Arial", "B", 10)
        self.set_fill_color(128, 0, 32)
        self._set_blanco()
        self.cell(0, 7.5, self.c(f"  {label}"), 0, 1, "L", fill=True)
        self._set_negro()
        self.ln(2)

    def data_field(self, label: str, value, ancho_label: float = 40):
        """Campo label: valor en línea."""
        self.set_font("Arial", "B", 9)
        self.set_text_color(60, 60, 60)
        self.write(5, self.c(f"{label}: "))
        self.set_font("Arial", "", 9)
        self._set_negro()
        self.write(5, self.c(str(value)) + "\n")

    def data_field_2col(self, items: list):
        """
        Pares (label, valor) en 2 columnas.
        items = [(label1, val1), (label2, val2), ...]
        """
        w = (self.w - 20) / 2
        for i in range(0, len(items), 2):
            y0 = self.get_y()
            # Columna izquierda
            self.set_font("Arial", "B", 8.5)
            self.set_text_color(60, 60, 60)
            self.set_x(10)
            self.cell(w, 5.5, self.c(f"{items[i][0]}: "), 0, 0)
            self.set_font("Arial", "", 8.5)
            self._set_negro()
            self.cell(w - 10, 5.5, self.c(str(items[i][1])), 0, 0)
            # Columna derecha (si existe)
            if i + 1 < len(items):
                self.set_xy(10 + w + 5, y0)
                self.set_font("Arial", "B", 8.5)
                self.set_text_color(60, 60, 60)
                self.cell(w, 5.5, self.c(f"{items[i+1][0]}: "), 0, 0)
                self.set_font("Arial", "", 8.5)
                self._set_negro()
                self.cell(w - 10, 5.5, self.c(str(items[i+1][1])), 0, 0)
            self.ln(5.5)

    def tabla(self, encabezados: list, filas: list, anchos: list = None):
        """
        Tabla genérica con encabezado gris, filas alternadas.
        encabezados: ['Col A', 'Col B']
        filas:       [['val1', 'val2'], ...]
        anchos:      [80, 60, ...] — si None, distribuye uniformemente
        """
        n   = len(encabezados)
        ws  = anchos if anchos else [(self.w - 20) / n] * n
        self.set_draw_color(255, 255, 255)
        self.set_line_width(0.5)

        # Encabezado
        self.set_fill_color(220, 220, 220)
        self.set_font("Arial", "B", 8)
        self._set_burdeos()
        for i, h in enumerate(encabezados):
            self.cell(ws[i], 7, self.c(f"  {h}"), 1, 0, "L", fill=True)
        self.ln()

        # Filas
        self.set_font("Arial", "", 8)
        self._set_negro()
        for r_idx, row in enumerate(filas):
            fill = r_idx % 2 == 0
            self.set_fill_color(248, 248, 248)
            for i, cel in enumerate(row):
                self.cell(ws[i], 6.5, self.c(f"  {cel}"), 1, 0, "L", fill=fill)
            self.ln()

        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.2)
        self.ln(3)

    def tabla_horarios(self, llegada: str, salida: str):
        """Tabla de 2 columnas para horarios de atención."""
        self.tabla(
            ["HORA DE INGRESO REGISTRADA", "HORA DE SALIDA REGISTRADA"],
            [[llegada, salida]],
            anchos=[(self.w - 20) / 2, (self.w - 20) / 2],
        )

    def cuerpo(self, texto: str, negrita: bool = False):
        """Párrafo de texto corrido 9pt."""
        self.set_font("Arial", "B" if negrita else "", 9)
        self._set_negro()
        self.multi_cell(0, 5.5, self.c(texto))
        self.ln(3)

    def alerta(self, texto: str, tipo: str = "warn"):
        """
        Caja de alerta coloreada.
        tipo: 'warn' | 'danger' | 'ok' | 'info'
        """
        colores = {
            "warn":   ((255, 251, 235), (217, 119, 6)),
            "danger": ((254, 242, 242), (185, 28, 28)),
            "ok":     ((240, 253, 244), (22, 163, 74)),
            "info":   ((239, 246, 255), (30, 64, 175)),
        }
        bg, txt = colores.get(tipo, colores["info"])
        self.set_fill_color(*bg)
        self.set_text_color(*txt)
        self.set_font("Arial", "B", 8.5)
        self.multi_cell(0, 6, self.c(f"  {texto}"), 0, "L", fill=True)
        self._set_negro()
        self.ln(3)

    # ── SELLO DIGITAL ─────────────────────────────────────────────────
    def estampar_sello_digital(
        self,
        nombre_prof: str,
        sis_prof:    str,
        rol:         str,
        fecha_firma: str = None,
    ) -> str:
        """
        Genera QR + SHA-256 + imagen de sello y los estampa en el PDF.
        Reemplaza estampar_sello_criptografico_medico() y estampar_sello_criptografico().
        Devuelve la huella corta (para guardar en Firestore + footer).
        """
        if fecha_firma is None:
            fecha_firma = self._ahora.strftime("%d/%m/%Y %H:%M:%S")

        # SHA-256
        semilla = (f"{self.id_verificacion}|{sis_prof}|"
                   f"{fecha_firma}|{self.meta['sha_sfx']}")
        hash_full   = hashlib.sha256(semilla.encode()).hexdigest().upper()
        huella_corta = f"{hash_full[:8]}-{hash_full[-8:]}"

        # QR
        qr_payload = (
            f"NORTE IMAGEN — DOCUMENTO AUTENTICADO\n"
            f"Tipo: {self.meta['titulo']}\n"
            f"ID: {self.id_verificacion}\n"
            f"Huella: {huella_corta}\n"
            f"Validar: https://cdnorteimagen.cl/validar?id={huella_corta}"
        )
        qr_img  = qrcode.make(qr_payload)
        tmp_qr  = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        qr_img.save(tmp_qr.name)
        tmp_qr.close()

        # Layout centrado
        self.ln(10)
        y0      = self.get_y()
        qr_sz   = 20
        sello_sz= 28
        gap     = 5
        bloque  = qr_sz + gap + sello_sz
        x_base  = (210 - bloque) / 2

        # QR centrado verticalmente respecto al sello
        if os.path.exists(tmp_qr.name):
            self.image(tmp_qr.name,
                       x=x_base,
                       y=y0 + (sello_sz - qr_sz) / 2,
                       w=qr_sz, h=qr_sz)
        try:
            os.unlink(tmp_qr.name)
        except Exception:
            pass

        # Sello PNG
        for ruta_s in ["sello_norte_imagen.png",
                        "assets/sello_norte_imagen.png",
                        os.path.join(os.path.dirname(__file__),
                                     "assets", "sello_norte_imagen.png")]:
            if os.path.exists(ruta_s):
                self.image(ruta_s, x=x_base + qr_sz + gap,
                           y=y0, w=sello_sz, h=sello_sz)
                break

        # Datos del profesional
        self.set_y(y0 + sello_sz + 3)
        self.set_text_color(60, 60, 60)
        cargo = _cargo_a_texto(rol)

        for fuente, tam, txt in [
            ("B", 6.5, f"VALIDADO POR: {nombre_prof.upper()}"),
            ("",  5.5, cargo),
            ("",  5.5, "ESPECIALIDAD RESONANCIA MAGNETICA"),
            ("",  5.5, f"REG. SIS: {sis_prof}"),
            ("",  5.5, f"FECHA Y HORA DE FIRMA: {fecha_firma}"),
        ]:
            self.set_font("Arial", fuente, tam)
            self.set_x(x_base)
            self.cell(bloque, 3, self.c(txt), 0, 1, "C")

        self.set_font("Arial", "I", 4.8)
        self.set_x(x_base)
        self.cell(bloque, 3,
                  self.c(f"HUELLA SHA-256: {huella_corta}"),
                  0, 1, "C")
        self._set_negro()
        return huella_corta

    # ── COMPILACIÓN ───────────────────────────────────────────────────
    def compilar(self) -> bytes:
        """Genera y retorna los bytes del PDF. Compatible con FPDF y FPDF2."""
        try:
            return bytes(self.output())
        except TypeError:
            salida = self.output(dest="S")
            if isinstance(salida, str):
                return salida.encode("latin-1")
            return bytes(salida)


# =============================================================================
# SECCIÓN 3 — GESTOR CRIPTOGRÁFICO AES-256 GCM
# Bidireccional: appv3 encripta → admin desencripta
# =============================================================================
class GestorCriptografico:
    """
    Encriptación/desencriptación AES-256 GCM.
    Cumple Ley 19.628 (Datos Personales Chile).
    La misma clase en appv3.py y admin para interoperabilidad.
    """

    def __init__(self):
        try:
            key_hex = st.secrets["aes"]["master_key"]
        except Exception:
            # Clave de desarrollo — reemplazar con st.secrets en producción
            key_hex = ("0123456789abcdef" * 4)
        self._aesgcm = AESGCM(bytes.fromhex(key_hex))

    def encriptar(self, datos: dict) -> str:
        nonce   = os.urandom(12)
        payload = json.dumps(datos, default=str).encode("utf-8")
        cifrado = self._aesgcm.encrypt(nonce, payload, None)
        return base64.b64encode(nonce + cifrado).decode("utf-8")

    def desencriptar(self, cadena: str) -> dict:
        raw    = base64.b64decode(cadena)
        datos  = self._aesgcm.decrypt(raw[:12], raw[12:], None)
        return json.loads(datos.decode("utf-8"))

    def desencriptar_seguro(self, cadena: str) -> Optional[dict]:
        """Versión segura que nunca lanza excepción (para UI del admin)."""
        try:
            return self.desencriptar(cadena)
        except Exception:
            return None


# =============================================================================
# SECCIÓN 4 — FHIR BUILDER HL7 R4
# =============================================================================
_MAPA_GENERO_FHIR = {
    "Masculino": "male", "Femenino": "female",
    "No binario (Bio: Masculino)": "other",
    "No binario (Bio: Femenino)":  "other",
    "No binario": "other",
}

_MAPA_SNOMED = {
    "HOMBRO": "368209003", "RODILLA":  "362768002", "CADERA":   "24136001",
    "MUNECA": "8205005",   "MANO":     "85562004",  "CODO":     "76248009",
    "TOBILLO":"70258002",  "PIE":      "302539009", "BRAZO":    "40983000",
    "ANTEBRAZO":"14975008","MUSLO":    "68367000",  "PIERNA":   "30021000",
    "ORBITA": "363654007", "MAMA":     "80248007",  "OIDO":     "25342003",
    "GLUTEO": "78961009",  "COLUMNA":  "421060004", "CEREBRO":  "12738006",
}


class FHIRBuilder:
    """Constructor de recursos HL7 FHIR R4 para Norte Imagen."""

    @staticmethod
    def patient(form: dict, id_sesion: str) -> dict:
        genero = _MAPA_GENERO_FHIR.get(form.get("genero_biologico", ""), "unknown")
        fn     = form.get("fecha_nac")
        fnac   = fn.strftime("%Y-%m-%d") if hasattr(fn, "strftime") else str(fn)
        ident  = ([{"use": "usual",
                    "type": {"text": form.get("tipo_doc", "Pasaporte")},
                    "value": form.get("num_doc", "")}]
                  if form.get("sin_rut") else
                  [{"use": "official",
                    "system": "http://registrocivil.cl/rut",
                    "value": form.get("rut", "")}])
        r = {"resourceType": "Patient", "id": id_sesion,
             "identifier": ident,
             "name": [{"use": "official", "text": form.get("nombre", "")}],
             "telecom": [
                 {"system": "phone", "value": form.get("telefono", ""), "use": "mobile"},
                 {"system": "email", "value": form.get("email", ""),    "use": "home"},
             ],
             "gender": genero, "birthDate": fnac}
        if form.get("nombre_tutor"):
            r["contact"] = [{"relationship": [{"text": form.get("parentesco_tutor","")}],
                             "name": {"text": form.get("nombre_tutor", "")}}]
        return r

    @staticmethod
    def consent(form: dict, id_sesion: str, ahora_iso: str) -> dict:
        return {
            "resourceType": "Consent", "id": f"consent-{id_sesion}",
            "status": "active",
            "scope": {"coding": [{"system":"http://terminology.hl7.org/CodeSystem/consentscope",
                                   "code":"treatment"}]},
            "category": [{"coding": [{"system":"http://loinc.org",
                                       "code":"59284-0","display":"Consent Document"}]}],
            "patient":   {"reference": f"Patient/{id_sesion}"},
            "dateTime":  ahora_iso,
            "performer": [{"display": form.get("nombre_tutor") or form.get("nombre","")}],
            "policy":    [{"authority":"https://www.minsal.cl",
                           "uri":"https://www.bcn.cl/leychile/navegar?idNorma=193581"}],
            "provision": {"type":"permit","period":{"start":ahora_iso}},
            "verification": [{"verified": bool(form.get("otp_verificado")),
                               "verifiedWith":{"reference":f"Patient/{id_sesion}"},
                               "verificationDate":ahora_iso}],
            "extension": [{"url":"http://minsal.cl/fhir/extension/fes-ley-19799",
                           "valueString":form.get("hash_documento","")}],
        }

    @staticmethod
    def observation_creatinina(form: dict, id_sesion: str) -> Optional[dict]:
        crea = float(form.get("creatinina", 0))
        if crea <= 0:
            return None
        fc  = form.get("fecha_creatinina")
        fcs = fc.isoformat() if hasattr(fc, "isoformat") else str(fc)
        return {
            "resourceType": "Observation", "id": f"obs-crea-{id_sesion}",
            "status": "final",
            "category": [{"coding":[{"system":"http://terminology.hl7.org/CodeSystem/observation-category",
                                      "code":"laboratory"}]}],
            "code":{"coding":[{"system":"http://loinc.org","code":"2160-0",
                               "display":"Creatinine [Mass/volume] in Serum or Plasma"}]},
            "subject":{"reference":f"Patient/{id_sesion}"},
            "effectiveDateTime": fcs,
            "valueQuantity":{"value":crea,"unit":"mg/dL",
                             "system":"http://unitsofmeasure.org","code":"mg/dL"},
        }

    @staticmethod
    def observation_vfg(form: dict, id_sesion: str, ahora_iso: str) -> Optional[dict]:
        vfg = float(form.get("vfg", 0))
        if vfg <= 0:
            return None
        return {
            "resourceType": "Observation", "id": f"obs-vfg-{id_sesion}",
            "status": "final",
            "category":[{"coding":[{"system":"http://terminology.hl7.org/CodeSystem/observation-category",
                                     "code":"laboratory"}]}],
            "code":{"coding":[{"system":"http://loinc.org","code":"33914-3","display":"eGFR"}]},
            "subject":{"reference":f"Patient/{id_sesion}"},
            "effectiveDateTime":ahora_iso,
            "valueQuantity":{"value":round(vfg,2),"unit":"mL/min/1.73m2",
                             "system":"http://unitsofmeasure.org","code":"mL/min/{1.73_m2}"},
        }

    @staticmethod
    def audit_event(accion: str, profesional: str, sis: str,
                    paciente_id: str, ahora_iso: str,
                    detalle: str = "") -> dict:
        """AuditEvent FHIR para trazabilidad de acciones del profesional."""
        return {
            "resourceType": "AuditEvent",
            "type":   {"system":"http://dicom.nema.org/resources/ontology/DCM","code":"110110"},
            "action": "C" if "CREA" in accion.upper() else
                      "R" if "LECTUR" in accion.upper() else
                      "U" if "MODIF" in accion.upper() or "ADENDUM" in accion.upper() else "E",
            "recorded": ahora_iso,
            "outcome":  "0",
            "agent":  [{"who":{"display":f"{profesional} | SIS:{sis}"},
                        "requestor": True}],
            "source": [{"site":"Norte Imagen RM",
                        "observer":{"display":"Sistema Admin Norte Imagen v3"}}],
            "entity": [{"what":{"reference":f"Patient/{paciente_id}"},
                        "description": detalle}],
        }

    @staticmethod
    def adverse_event(tipo: str, gravedad: str, descripcion: str,
                      profesional: str, paciente_id: str,
                      ahora_iso: str) -> dict:
        """AdverseEvent FHIR para eventos de seguridad GCL 2.3 MINSAL."""
        _grav = {"Leve":"mild","Moderado":"moderate","Grave":"severe"}.get(gravedad,"mild")
        return {
            "resourceType": "AdverseEvent",
            "status": "completed",
            "actuality": "potential" if "cuasi" in tipo.lower() else "actual",
            "category":[{"coding":[{"system":"http://terminology.hl7.org/CodeSystem/adverse-event-category",
                                     "code":"clinical-trial"}]}],
            "event":{"coding":[{"system":"http://snomed.info/sct","display":tipo}]},
            "subject":{"reference":f"Patient/{paciente_id}"},
            "date":ahora_iso,
            "severity":{"coding":[{"system":"http://terminology.hl7.org/CodeSystem/adverse-event-severity",
                                    "code":_grav,"display":gravedad}]},
            "description": descripcion,
            "recorder":{"display":profesional},
        }

    @staticmethod
    def bundle(tipo: str, id_sesion: str, entradas: list,
               ahora_iso: str) -> dict:
        return {
            "resourceType": "Bundle",
            "id": f"bundle-{id_sesion}",
            "type": "document",
            "timestamp": ahora_iso,
            "entry": [{"resource": r} for r in entradas if r],
            "meta": {
                "tag": [{"system":"http://minsal.cl/fhir/tag",
                         "code":f"norte-imagen-{tipo.lower()}"}]
            },
        }


# =============================================================================
# SECCIÓN 5 — CORRELATIVO ATÓMICO + ID DE DOCUMENTO
# =============================================================================
def generar_id_documento(tipo_doc: str, db_client,
                         nombre_pac: str = "", rut_pac: str = "") -> tuple:
    """
    Genera correlativo atómico (inmune a colisiones) + ID verificación + nombre archivo.
    Retorna: (correlativo_str, id_verificacion, nombre_archivo)
    """
    tipo_doc = tipo_doc.upper()
    if tipo_doc not in CATALOGO_DOCS:
        raise ValueError(f"tipo_doc '{tipo_doc}' no reconocido.")

    pfx_arch, pfx_id = CATALOGO_DOCS[tipo_doc]["id_pfx"]

    try:
        from firebase_admin import firestore as _fs
        ref = db_client.collection("configuracion").document("contadores_documentos")
        ref.set({tipo_doc: _fs.Increment(1)}, merge=True)
        n = int(ref.get().to_dict().get(tipo_doc, 1))
    except Exception:
        import time as _t
        n = int(str(int(_t.time()))[-5:])

    correlativo     = str(n).zfill(6)
    id_verif        = f"{pfx_id}{correlativo}"
    nom             = str(nombre_pac).replace(" ", "_").upper()[:20]
    rut             = str(rut_pac).replace(".", "").replace("-", "").upper()[:10]
    nombre_archivo  = f"{pfx_arch}-{nom}_{rut}_{correlativo}.pdf"

    return correlativo, id_verif, nombre_archivo


# =============================================================================
# SECCIÓN 6 — VALIDACIÓN DE PIN (ÚNICA — SIN pin_plano, SIN fallback)
# =============================================================================
def validar_pin(pin_ingresado: str, hash_almacenado: str) -> bool:
    """
    Única función de validación de PIN en todo el sistema.
    Usa solo check_password_hash (werkzeug/pbkdf2:sha256).
    NO hay fallback a pin_plano, pin, password ni password_directa.
    Si el hash no existe → False.
    """
    if not pin_ingresado or not hash_almacenado:
        return False
    try:
        return check_password_hash(hash_almacenado, pin_ingresado)
    except Exception:
        return False


# =============================================================================
# SECCIÓN 7 — UTILIDADES CLÍNICAS COMPARTIDAS
# =============================================================================
def calcular_edad(fecha_nac: date) -> int:
    hoy = date.today()
    return (hoy.year - fecha_nac.year
            - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day)))


def edad_visual(fecha_nac: date) -> str:
    hoy   = date.today()
    a     = hoy.year  - fecha_nac.year
    m     = hoy.month - fecha_nac.month
    d     = hoy.day   - fecha_nac.day
    if d < 0: m -= 1; d += 30
    if m < 0: a -= 1; m += 12
    if a > 0: return f"{a} años, {m} meses"
    if m > 0: return f"{m} meses, {d} dias"
    return f"{d} dias"


def formatear_rut(rut: str) -> str:
    r = str(rut).replace(".", "").replace("-", "").upper().strip()
    if len(r) < 2:
        return rut
    cuerpo, dv = r[:-1], r[-1]
    return (f"{int(cuerpo):,}".replace(",", ".") + f"-{dv}"
            if cuerpo.isdigit() else rut)


def generar_otp_secret() -> str:
    return pyotp.random_base32()


def verificar_otp(secret: str, codigo: str, intervalo: int = 300) -> bool:
    try:
        return pyotp.TOTP(secret, interval=intervalo).verify(codigo)
    except Exception:
        return False


def otp_actual(secret: str, intervalo: int = 300) -> str:
    return pyotp.TOTP(secret, interval=intervalo).now()


def enmascarar(texto: str, tipo: str = "email") -> str:
    if not texto:
        return "Sin dato"
    if tipo == "email":
        p = texto.split("@")
        return f"{p[0][:3]}***@{p[1]}" if len(p) == 2 else texto
    return f"******{texto[-4:]}" if len(texto) >= 4 else texto


# =============================================================================
# AUXILIAR PRIVADO
# =============================================================================
def _cargo_a_texto(rol: str) -> str:
    return {
        "tm":                    "TECNOLOGO MEDICO",
        "tm_coordinador":        "TECNOLOGO MEDICO COORDINADOR",
        "calidad":               "ENCARGADA DE CALIDAD Y SEGURIDAD",
        "owner":                 "DIRECCION TECNICA",
        "tens":                  "TENS",
        "secretaria":            "SECRETARIA",
        "radiologo":             "MEDICO RADIOLOGO",
        "radiologo_coordinador": "MEDICO RADIOLOGO COORDINADOR",
        "medico_coordinador":    "MEDICO RADIOLOGO COORDINADOR",
    }.get(str(rol).lower().strip(), str(rol).upper())

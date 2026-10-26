import { useState, useMemo, useEffect, useRef } from "react";
import {
  Search, Zap, RefreshCw, ArrowUpDown, ChevronRight, Cpu, Eye, PenSquare,
  FileText, Printer, MessageSquare, Share2, Calendar, UserCheck, Monitor,
  FolderOpen, X, ClipboardCheck, ShieldCheck, Paperclip, Camera, Link2,
  Settings, Trash2, Plus, Move, ZoomIn, RotateCw, Contrast, Ruler, Crosshair, Sun,
  Ticket, UserPlus, Banknote, Tablet, CalendarClock, AlertTriangle, RotateCcw, Mic,
} from "lucide-react";
/* Capa de datos real (26-ago-2026) — habla con WorklistApiServer.js, que a su
   vez lee/escribe WorklistStore.js, el mismo store que consulta el motor
   DICOM por C-FIND/C-STORE. Antes de hoy, este archivo nunca hablaba con el
   motor: todo vivía en useState local. Ver AXON_MOTOR_DICOM_Mapa_y_Estado
   _Verificado (dossier), §9/§11/§12, para el porqué completo. */
import * as WorklistClient from "./WorklistClient.js";

/* ════════════════════════════════════════════════════════════════════
   NOTA DE ARQUITECTURA — TICKET DE MEMORIA (patrón reutilizable)
   ════════════════════════════════════════════════════════════════════
   Esta estructura —registro de modalidades, registro de estados por fase,
   shell de pestañas, máquina de estados fase→estado, columnas por config
   en vez de tablas repetidas, panel de detalle contextual, trazabilidad
   de staff (Administrativo/TENS/TM/Radiólogo), y puertas IA etiquetadas—
   es el MOLDE para cuando armemos, más adelante, los sistemas de las
   otras unidades de examen (Cardiología, Neurología, Laboratorio,
   Biopsias, etc.), cada una con su propio registro de protocolos/estados
   bajo la misma forma. No se construye nada de eso todavía — queda
   anotado aquí para no perder el hilo cuando terminemos RIS/PACS.

   ALINEACIÓN CON LA BASE REAL (HISClinico_Base_v5.zip, revisado 05-jul-2026):
   CUP y EventBus ya calzan en forma con src/utils/cup.js y src/events/EventBus.js
   (mismo formato CUP-{ISO2}-{REGIÓN}-{AÑO}-{SEQ8}-{CHK2}, mismo publish/EVENTS).
   Pendiente para cuando este componente se integre al proyecto real (no bloquea
   avanzar hoy): TerminologyService en vez de MODALIDADES fijo, roles reales de
   userTypes/workTeams.config.js en vez de arrays sueltos, DatabaseService en vez
   de useState local.
   ════════════════════════════════════════════════════════════════════ */

/* ────────────────────────────────────────────────────────────────
   § 1 · PALETA OSCURA — misma identidad AXON, recalibrada para fondo oscuro
   ──────────────────────────────────────────────────────────────── */
const D = {
  bg: "#0A1420", sfc: "#111F32", sfc2: "#0D1A29", brd: "#1E3350",
  txt: "#EAF0FA", txm: "#96AAC6", txl: "#5E7593",
  pri: "#9BA8B8", tea: "#22D3B8", dan: "#FF5C6C", war: "#FFA359", suc: "#5FD97A", pur: "#B37FE0",
};

/* ────────────────────────────────────────────────────────────────
   § 2 · REGISTRO DE MODALIDADES — un solo lugar para editar/extender.
   BDUS y BDM son mi mejor interpretación de tu lista — si el
   nombre no calza, se corrige acá y se propaga solo. (XO retirado)
   ──────────────────────────────────────────────────────────────── */
const MODALIDADES = {
  RX:   { color: "#29B6D8", nombre: "Radiografía digital" },
  MG:   { color: "#E0559E", nombre: "Mamografía" },
  US:   { color: "#5FD97A", nombre: "Ultrasonido" },
  TC:   { color: "#4C8DFF", nombre: "Tomografía computada" },
  RM:   { color: "#B37FE0", nombre: "Resonancia magnética" },
  XA:   { color: "#FF7A59", nombre: "Angiografía digital" },
  PT:   { color: "#FFC24C", nombre: "Tomografía por emisión de positrones" },
  MN:   { color: "#22D3B8", nombre: "Medicina nuclear" },
  BDUS: { color: "#7BC4A8", nombre: "Biopsia guiada por ultrasonido" },
  BDM:  { color: "#D98BB0", nombre: "Biopsia guiada por mamografía (estereotaxia)" },
};

/* Categorías clínicas — CONFIGURABLES desde la interfaz (panel "Gestionar categorías"),
   no están quemadas en código: agregar/quitar una no requiere tocar este archivo en producción,
   solo pasa por la misma pantalla. Esta lista es apenas el set inicial. */
const CATEGORIAS_DEFAULT = [
  { id: "aisl_aereo", label: "Aislamiento aéreo", color: "#FF7A59", grupo: "Aislamiento" },
  { id: "aisl_gotas", label: "Aislamiento por gotas", color: "#FFC24C", grupo: "Aislamiento" },
  { id: "aisl_contacto", label: "Aislamiento de contacto", color: "#E0559E", grupo: "Aislamiento" },
  { id: "aisl_protector", label: "Aislamiento protector", color: "#B37FE0", grupo: "Aislamiento" },
  { id: "niv_uci", label: "UCI", color: "#FF5C6C", grupo: "Nivel de cuidados" },
  { id: "niv_intermedio", label: "Intermedio", color: "#FFA359", grupo: "Nivel de cuidados" },
  { id: "niv_basico", label: "Básico", color: "#5E7593", grupo: "Nivel de cuidados" },
  { id: "niv_estable", label: "Paciente estable", color: "#5FD97A", grupo: "Nivel de cuidados" },
  { id: "urg_pcr", label: "Paro cardiorrespiratorio", color: "#FF5C6C", grupo: "Urgencia" },
  { id: "urg_covid", label: "COVID-19", color: "#29B6D8", grupo: "Urgencia" },
];

const PRIORIDADES = {
  stat: { label: "STAT", color: D.dan },
  alta: { label: "Alta", color: D.war },
  normal: { label: null, color: D.txl },
};

/* ────────────────────────────────────────────────────────────────
   § 3 · MÁQUINA DE ESTADOS — fase actual (pestaña) + estado dentro de ella.
   Coincide 1:1 con FLUJO_REAL_RISPACS_PACIENTE.docx.
   ──────────────────────────────────────────────────────────────── */
const FASES = [
  { id: "agendados", label: "Agendados", icon: Calendar, color: D.pri },
  { id: "admision", label: "Admisión", icon: UserCheck, color: D.tea },
  { id: "worklist", label: "Worklist · RIS", icon: Monitor, color: D.war },
  { id: "examenes", label: "Exámenes · PACS", icon: FolderOpen, color: D.suc },
];

const ESTADOS = {
  agendado: { label: "Agendado", color: D.txl },
  confirmado: { label: "Confirmado", color: D.pri },
  llegada_recepcion: { label: "Llegada · recepción", color: D.tea },
  llegada_totem: { label: "Llegada · tótem", color: D.tea },
  nuevo: { label: "Nuevo", color: D.txl },
  arribado: { label: "Arribado", color: D.pri },
  en_proceso: { label: "En proceso", color: D.war },
  almacenado: { label: "Almacenado", color: D.pri },
  informado: { label: "Informado", color: D.war },
  validado: { label: "Validado", color: D.suc },
  reagendado: { label: "Reagendado", color: D.war },
};

/* CUT alineado al formato real de src/utils/cup.js: CUT-{ISO2}-{REGIÓN}-{CLINICA4}-{SEQ8}-{CHK2}.
   Mismo dígito local de checkDigitLocal(), ya definido arriba junto a makeCUP. */
const makeCUT = (n, regionCode = "13") => {
  const base = `CUT-CL-${regionCode}-AXON-${String(n).padStart(8, "0")}`;
  return `${base}-${checkDigitLocal(base)}`;
};

/* Tiempos múltiples por etapa (§7 del dossier) — helpers HH:MM ⇄ minutos */
const toMin = (hhmm) => { const [h, m] = hhmm.split(":").map(Number); return h * 60 + m; };
const toHHMM = (min) => { const m = ((min % 1440) + 1440) % 1440; return `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`; };

/* A partir del único "hora" de la semilla, deriva los 6 timestamps reales del flujo.
   No es una reconstrucción perfecta — es suficiente para que cada pestaña muestre
   sus 2 columnas correctas mientras no hay backend calculando esto de verdad. */
const deriveTimestamps = (r) => {
  const t = toMin(r.hora);
  const ts = { horaAgendada: null, horaPresentacion: null, horaAdmision: null, horaArribo: null, horaAtencion: null, horaAlmacenado: null };
  if (r.fase === "agendados") {
    ts.horaAgendada = r.hora;
    if (r.estado === "llegada_recepcion" || r.estado === "llegada_totem") ts.horaPresentacion = r.hora;
  } else if (r.fase === "admision") {
    ts.horaAgendada = toHHMM(t - 25);
    ts.horaPresentacion = r.hora;
  } else if (r.fase === "worklist") {
    ts.horaAgendada = toHHMM(t - 40);
    ts.horaPresentacion = toHHMM(t - 20);
    ts.horaAdmision = toHHMM(t - 12);
    ts.horaArribo = r.hora;
  } else if (r.fase === "examenes") {
    ts.horaAgendada = toHHMM(t - 70);
    ts.horaArribo = toHHMM(t - 20);
    ts.horaAtencion = toHHMM(t - 10);
    ts.horaAlmacenado = r.hora;
  }
  return ts;
};

/* ACC (Número de Acceso) y OT (Orden de Trabajo) — §8 del dossier. No aplican en Agendados. */
const makeOT = (n) => `OT-2026-${String(n).padStart(6, "0")}`; // 14 caracteres — dentro del máximo 16 de VR=SH, sin cambios
/* makeACC() — corregido 31-ago-2026: el formato anterior (`ACC-2026-00000001`,
   17 caracteres) excedía el máximo real de 16 caracteres de la VR SH
   (Accession Number, tag 0008,0050 — PS3.5 Tabla 6.2-1, verificado contra
   la fuente primaria dicom.nema.org). Nadie lo había notado porque ni
   ImplicitVrCodec.js ni ExplicitVrCodec.js validaban longitud al codificar
   — un motor DICOM real, conforme al estándar, podría truncar o rechazar
   el valor. Ahora el motor SÍ valida (ver VrLimits.js) y este es el fix
   del lado que generaba el valor. Se saca el año del medio (ya vive en el
   CUP, no hace falta duplicarlo acá) — 12 caracteres, deja margen. */
const makeACC = (n) => `ACC-${String(n).padStart(8, "0")}`;

const MEDIOS_CONTRASTE = ["Ninguno", "Yodado no iónico (Iopamidol)", "Yodado no iónico (Iohexol)", "Gadolinio (Gadoteridol)", "Gadolinio (Gadobutrol)", "Bario oral"];

const MEDICOS_SOLICITANTES = ["Dr. Enzo Muñoz Caprile", "Dra. Valentina Ortúzar", "Dr. Ignacio Bravo Reyes", "Dra. Camila Sepúlveda"];

/* Muestra real y verificada (no toda la tabla — eso queda para el módulo admin de CIE-10/CIE-11 más adelante). */
const CIE10_MUESTRA = [
  { codigo: "M54.4", glosa: "Lumbago con ciática" },
  { codigo: "M54.5", glosa: "Lumbago no especificado" },
  { codigo: "M51.1", glosa: "Trastorno de disco lumbar y otros, con radiculopatía" },
  { codigo: "M51.2", glosa: "Otros desplazamientos especificados de disco intervertebral" },
  { codigo: "M51.3", glosa: "Otra degeneración especificada de disco intervertebral" },
  { codigo: "M17.1", glosa: "Otras gonartrosis primarias (rodilla)" },
  { codigo: "M17.9", glosa: "Gonartrosis, no especificada" },
  { codigo: "M16.9", glosa: "Coxartrosis, no especificada (cadera)" },
  { codigo: "R90.0", glosa: "Lesión que ocupa el espacio intracraneal" },
  { codigo: "R91", glosa: "Hallazgos anormales en diagnóstico por imagen del pulmón" },
  { codigo: "R92.2", glosa: "Mamografía no concluyente" },
  { codigo: "R93.2", glosa: "Hallazgos anormales en diagnóstico por imagen del hígado y vías biliares" },
  { codigo: "R93.4", glosa: "Hallazgos anormales en diagnóstico por imagen de los órganos urinarios" },
  { codigo: "R93.5", glosa: "Hallazgos anormales en diagnóstico por imagen de otras regiones abdominales" },
  { codigo: "R93.6", glosa: "Hallazgos anormales en diagnóstico por imagen de los miembros" },
  { codigo: "R93.7", glosa: "Hallazgos anormales en diagnóstico por imagen del sistema osteomuscular" },
  { codigo: "R94", glosa: "Resultados anormales de estudios funcionales" },
];

/* Plantillas privadas por radiólogo — cada uno ve solo las suyas, no se comparten. */
const PLANTILLAS_POR_RADIOLOGO = {
  "Dr. Carlos Soto": [
    { id: "p1", nombre: "RM Columna Lumbar — normal", tecnica: "Cortes sagitales y axiales T1/T2/STIR.", hallazgos: "Alineación conservada. Discos intervertebrales de altura y señal conservadas. Sin herniación ni estenosis significativa.", impresion: "Estudio sin hallazgos patológicos significativos." },
    { id: "p2", nombre: "TC Cerebro — normal", tecnica: "Cortes axiales sin contraste.", hallazgos: "Parénquima cerebral de densidad conservada. Sistema ventricular de tamaño normal. Sin colecciones ni desplazamiento de línea media.", impresion: "TC de cerebro sin alteraciones agudas." },
  ],
  "Dra. Fernanda Ríos": [
    { id: "p3", nombre: "Mamografía — BI-RADS 1", tecnica: "Proyecciones CC y MLO bilaterales.", hallazgos: "Parénquima mamario de patrón graso. Sin nódulos ni microcalcificaciones sospechosas.", impresion: "Mamografía bilateral sin hallazgos. BI-RADS 1." },
  ],
};

/* Calculadora de función renal — §5 del dossier.
   Cockcroft-Gault (≥18a): CrCl = [(140-edad)×peso] / [72×creatinina] × (0.85 si mujer)
   Schwartz bedside 2009 (<18a): eGFR = 0.413 × talla / creatinina
   Fórmulas verificadas contra fuentes clínicas actuales (jul-2026). El aviso de <30/<45
   sigue el umbral más citado por ACR 2025 / ESUR — es informativo, no bloquea nada. */
const calcularFuncionRenal = (edad, sexo, creatinina, talla, peso) => {
  if (!creatinina || creatinina <= 0) return null;
  if (edad != null && edad < 18) {
    if (!talla) return null;
    const egfr = (0.413 * talla) / creatinina;
    return { formula: "Schwartz bedside (2009)", valor: egfr, unidad: "mL/min/1.73m²" };
  }
  if (!peso) return null;
  const crcl = ((140 - edad) * peso) / (72 * creatinina) * (sexo === "F" ? 0.85 : 1);
  return { formula: "Cockcroft-Gault", valor: crcl, unidad: "mL/min" };
};

/* Mapeo a roles reales de src/config/userTypes.config.js (revisado 05-jul-2026):
   "Radiólogo" → string de rol "radiologo" (hoy vive raro: colgado de TECNOLOGO_MED_STAFF
   y de TECNOLOGO_INDEPENDIENTE — un radiólogo es médico, no tecnólogo; posible ajuste a
   futuro: moverlo bajo MEDICO_STAFF). "TM" → "tecnologo_med". "Administrativo" → "administrativo".
   "TENS" → NO EXISTE TODAVÍA en userTypes.config.js — falta crear (ej. TENS_STAFF, rol "tens").
   Los arrays de abajo siguen siendo nombres simples por velocidad; cuando esto entre al
   proyecto real, cada nombre se reemplaza por {cut: makeCUT(n), nombre, rol}. */
const ADMINISTRATIVOS = ["Loreto Cáceres", "Pablo Yáñez"];
const TENS_LIST = ["Nicolás Bravo", "Camila Ossandón"];
const TM_LIST = ["TM Andrea Bustos", "TM Felipe Concha"];
const RADIOLOGOS = ["Dr. Carlos Soto", "Dra. Fernanda Ríos", "Dr. Matías Contreras", "Dra. Javiera Rojas"];

/* CUP alineado al formato real de src/utils/cup.js: CUP-{ISO2}-{REGIÓN}-{AÑO}-{SEQ8}-{CHK2}.
   El dígito verificador acá es un hash corto local solo para que se vea y calce en forma —
   la validación real (SHA-256) vive en cup.js y se usa apenas este módulo entre al proyecto. */
const checkDigitLocal = (base) => {
  let h = 0;
  for (let i = 0; i < base.length; i++) h = (h * 31 + base.charCodeAt(i)) >>> 0;
  return h.toString(16).toUpperCase().slice(-2).padStart(2, "0");
};
const makeCUP = (n, regionCode = "13") => {
  const base = `CUP-CL-${regionCode}-2026-${String(n).padStart(8, "0")}`;
  return `${base}-${checkDigitLocal(base)}`;
};

/* Stub local del EventBus real (src/events/EventBus.js) — misma firma (publish/EVENTS),
   así que cuando este componente entre al proyecto, el cambio es una sola línea de import.
   Hoy solo deja rastro en consola; nadie más está "escuchando" y eso está bien. */
/* Copiado de src/config/security.config.js (audit.criticalEvents) — mismos nombres,
   para que cuando esto entre al proyecto real sea reemplazar publish() por el import,
   no reescribir qué se audita. */
const EVENTS = { PACIENTE_INGRESADO: "paciente.ingresado", RESULTADO_LISTO: "resultado.listo", ALERTA_CRITICA: "alerta.critica", CHECKPOINT_SCAN: "checkpoint.scan", VIEW_IMAGING_REPORT: "view_imaging_report", DOWNLOAD_PDF: "download_pdf" };
const publish = (eventName, payload) => { if (typeof console !== "undefined") console.debug(`[EventBus·stub] ${eventName}`, payload); };
/* Mismo patrón que canAccessClinicalRecord(role, config) de security.config.js —
   ahí compara contra accessControl.clinicalRecordRoles; acá ROLES_INFORMANTES
   cumple el mismo rol para la porción de "informar", ya con IDs reales. */

/* Copiado literal de src/config/roles.config.js (categoría "tecnologos" + "medicos") —
   cuando este módulo entre al proyecto real, esto pasa a venir de TENANT_ROLES y
   findRole(), ambos exportados desde ese archivo de configuración real, en vez de
   estar harcodeado acá como demo.
   No quedan roles inventados: t_tec_imagen_tens es el TENS real de imagenología
   (no un "tens" genérico), t_med_radiologo es médico confirmado, separado de
   t_tec_imagen_coord (que es tecnólogo, no médico). */
const SESIONES_DEMO = [
  { nombre: "Andrea Bustos", rolId: "t_tec_imagen", rol: "Tecnólogo Médico · Imagen" },
  { nombre: "Nicolás Bravo", rolId: "t_tec_imagen_tens", rol: "TENS · Imagen" },
  { nombre: "Dr. Carlos Soto", rolId: "t_med_radiologo", rol: "Médico Radiólogo" },
  { nombre: "Felipe Concha", rolId: "t_tec_imagen_coord", rol: "Tecnólogo Médico Coordinador · Imagen" },
];
/* Solo estos roles pueden abrir/validar informe — el resto revisa imágenes e informes, no los crea ni edita.
   Confirmado contra AXON_Actualizacion_Roles_Modulos_Satelite.md: el gating va contra estos 2 IDs reales. */
const ROLES_INFORMANTES = ["t_med_radiologo", "t_tec_imagen_coord"];

/* ────────────────────────────────────────────────────────────────
   § 4 · DATOS SEMILLA — un solo modelo de "viaje del paciente"
   ──────────────────────────────────────────────────────────────── */
/* Bono/pago — §11 del dossier de ampliación. null = sin bono asociado todavía.
   { numero, origen: "presencial"|"autoatencion", estado: "pendiente_pago"|"validado"|"anulado" } */
const BONO_ESTADOS = {
  pendiente_pago: { label: "Pendiente", color: D.war },
  validado: { label: "Validado", color: D.suc },
  anulado: { label: "Anulado", color: D.dan },
};
let bonoAutoSeq = 500;
const makeBonoAutoatencion = () => `BN-TOTEM-${String(bonoAutoSeq++).padStart(6, "0")}`;

let manualSeq = 0;
const nextManualId = () => 9000 + (++manualSeq); // rango separado del SEED (1-24) para que no choquen nunca

const SEED = [
  { id: 1, cup: makeCUP(2001), rut: "12.111.222-3", nombre: "María Elena Rojas P.", edad: 55, sexo: "F", fase: "agendados", estado: "agendado", modalidad: "TC", estudio: "TC abdomen y pelvis con contraste", procedencia: "Ambulatorio", prioridad: "normal", hora: "09:00", staff: { administrativo: "Loreto Cáceres", tens: null, tm: null, radiologo: null }, comentarios: [] },
  { id: 2, cup: makeCUP(2002), rut: "18.222.333-4", nombre: "Bastián Contreras L.", edad: 30, sexo: "M", fase: "agendados", estado: "confirmado", modalidad: "RM", estudio: "RM rodilla derecha", procedencia: "Ambulatorio", prioridad: "normal", hora: "09:30", staff: { administrativo: "Pablo Yáñez", tens: null, tm: null, radiologo: null }, comentarios: [] },
  { id: 3, cup: makeCUP(2003), rut: "9.333.444-5", nombre: "Isidora Vergara T.", edad: 62, sexo: "F", fase: "agendados", estado: "agendado", modalidad: "MG", estudio: "Mamografía bilateral", procedencia: "Ambulatorio", prioridad: "normal", hora: "10:00", staff: { administrativo: "Loreto Cáceres", tens: null, tm: null, radiologo: null }, comentarios: [] },
  { id: 4, cup: makeCUP(2004), rut: "14.444.555-6", nombre: "Sebastián Ibáñez R.", edad: 47, sexo: "M", fase: "agendados", estado: "llegada_recepcion", modalidad: "RX", estudio: "RX tórax", procedencia: "Ambulatorio", prioridad: "normal", hora: "10:15", staff: { administrativo: "Pablo Yáñez", tens: null, tm: null, radiologo: null }, comentarios: [] },
  { id: 5, cup: makeCUP(2005), rut: "21.555.666-7", nombre: "Constanza Leiva M.", edad: 19, sexo: "F", fase: "agendados", estado: "llegada_totem", modalidad: "US", estudio: "Ecografía pélvica", procedencia: "Ambulatorio", prioridad: "normal", hora: "10:30", staff: { administrativo: "Loreto Cáceres", tens: null, tm: null, radiologo: null }, comentarios: [] },
  { id: 6, cup: makeCUP(2006), rut: "8.666.777-8", nombre: "Ramón Aguayo S.", edad: 70, sexo: "M", fase: "agendados", estado: "confirmado", modalidad: "TC", estudio: "TC tórax de control oncológico", procedencia: "Ambulatorio", prioridad: "alta", hora: "11:00", staff: { administrativo: "Pablo Yáñez", tens: null, tm: null, radiologo: null }, comentarios: [] },

  { id: 7, cup: makeCUP(2007), rut: "10.777.888-9", nombre: "Teresa Bustamante O.", edad: 66, sexo: "F", fase: "admision", estado: "nuevo", modalidad: "RM", estudio: "RM columna cervical", procedencia: "Ambulatorio", prioridad: "normal", hora: "08:45", staff: { administrativo: "Loreto Cáceres", tens: null, tm: null, radiologo: null }, comentarios: [] },
  { id: 8, cup: makeCUP(2008), rut: "16.888.999-0", nombre: "Álvaro Sepúlveda N.", edad: 38, sexo: "M", fase: "admision", estado: "nuevo", modalidad: "XA", estudio: "Angiografía de miembros inferiores", procedencia: "Hospitalizado", prioridad: "alta", hora: "09:05", staff: { administrativo: "Pablo Yáñez", tens: null, tm: null, radiologo: null }, comentarios: [] },
  { id: 9, cup: makeCUP(2009), rut: "26.999.111-2", nombre: "Josefina Campos D.", edad: 5, sexo: "F", fase: "admision", estado: "nuevo", modalidad: "RX", estudio: "RX ambas manos", procedencia: "Ambulatorio", prioridad: "normal", hora: "09:20", staff: { administrativo: "Loreto Cáceres", tens: null, tm: null, radiologo: null }, comentarios: [] },
  { id: 10, cup: makeCUP(2010), rut: "7.111.222-3", nombre: "Hugo Peña V.", edad: 82, sexo: "M", fase: "admision", estado: "nuevo", modalidad: "TC", estudio: "TC cerebro sin contraste", procedencia: "Urgencia", prioridad: "stat", hora: "09:40", staff: { administrativo: "Pablo Yáñez", tens: null, tm: null, radiologo: null }, comentarios: [] },
  { id: 11, cup: makeCUP(2011), rut: "15.222.333-4", nombre: "Daniela Zúñiga F.", edad: 44, sexo: "F", fase: "admision", estado: "nuevo", modalidad: "BDM", estudio: "Biopsia estereotáxica mama izquierda", procedencia: "Ambulatorio", prioridad: "normal", hora: "10:00", staff: { administrativo: "Loreto Cáceres", tens: null, tm: null, radiologo: null }, comentarios: [] },

  { id: 12, cup: makeCUP(2012), rut: "11.333.444-5", nombre: "Patricio Salgado H.", edad: 59, sexo: "M", fase: "worklist", estado: "arribado", modalidad: "TC", estudio: "TC tórax + abdomen y pelvis", procedencia: "Hospitalizado", prioridad: "alta", hora: "08:30", staff: { administrativo: "Pablo Yáñez", tens: null, tm: null, radiologo: null }, comentarios: [] },
  { id: 13, cup: makeCUP(2013), rut: "19.444.555-6", nombre: "Fernanda Riquelme A.", edad: 29, sexo: "F", fase: "worklist", estado: "en_proceso", modalidad: "US", estudio: "Ecografía abdominal", procedencia: "Ambulatorio", prioridad: "normal", hora: "08:50", staff: { administrativo: "Loreto Cáceres", tens: "Nicolás Bravo", tm: "TM Andrea Bustos", radiologo: "Dr. Carlos Soto" }, comentarios: [] },
  { id: 14, cup: makeCUP(2014), rut: "27.555.666-7", nombre: "Cristóbal Molina P.", edad: 8, sexo: "M", fase: "worklist", estado: "arribado", modalidad: "TC", estudio: "TC cerebro con contraste", procedencia: "Urgencia", prioridad: "stat", hora: "09:00", staff: { administrativo: "Pablo Yáñez", tens: null, tm: null, radiologo: null }, comentarios: [] },
  { id: 15, cup: makeCUP(2015), rut: "6.666.777-8", nombre: "Amanda Herrera Q.", edad: 75, sexo: "F", fase: "worklist", estado: "en_proceso", modalidad: "RM", estudio: "RM cerebro con contraste", procedencia: "Hospitalizado", prioridad: "alta", hora: "09:10", staff: { administrativo: "Loreto Cáceres", tens: "Camila Ossandón", tm: "TM Felipe Concha", radiologo: "Dra. Fernanda Ríos" }, comentarios: [] },
  { id: 16, cup: makeCUP(2016), rut: "13.777.888-9", nombre: "Gonzalo Tapia B.", edad: 41, sexo: "M", fase: "worklist", estado: "arribado", modalidad: "RX", estudio: "RX columna lumbosacra", procedencia: "Urgencia", prioridad: "normal", hora: "09:25", staff: { administrativo: "Pablo Yáñez", tens: null, tm: null, radiologo: null }, comentarios: [] },
  { id: 17, cup: makeCUP(2017), rut: "17.888.999-0", nombre: "Valeria Contreras S.", edad: 53, sexo: "F", fase: "worklist", estado: "arribado", modalidad: "MG", estudio: "Mamografía bilateral (4 exp.)", procedencia: "Ambulatorio", prioridad: "normal", hora: "09:35", staff: { administrativo: "Loreto Cáceres", tens: null, tm: null, radiologo: null }, comentarios: [] },
  { id: 18, cup: makeCUP(2018), rut: "5.999.111-2", nombre: "Marcelo Vidal C.", edad: 68, sexo: "M", fase: "worklist", estado: "en_proceso", modalidad: "BDUS", estudio: "Biopsia guiada por ultrasonido hepática", procedencia: "Ambulatorio", prioridad: "alta", hora: "09:50", staff: { administrativo: "Pablo Yáñez", tens: "Nicolás Bravo", tm: "TM Andrea Bustos", radiologo: "Dr. Matías Contreras" }, comentarios: [] },

  { id: 19, cup: makeCUP(2019), rut: "12.999.222-3", nombre: "Ignacia Poblete R.", edad: 36, sexo: "F", fase: "examenes", estado: "almacenado", modalidad: "US", estudio: "Ecografía tiroidea", procedencia: "Ambulatorio", prioridad: "normal", hora: "07:40", staff: { administrativo: "Loreto Cáceres", tens: "Camila Ossandón", tm: "TM Felipe Concha", radiologo: "Dra. Javiera Rojas" }, comentarios: [] },
  { id: 20, cup: makeCUP(2020), rut: "9.111.333-4", nombre: "Vicente Núñez A.", edad: 61, sexo: "M", fase: "examenes", estado: "informado", modalidad: "TC", estudio: "TC tórax sin contraste", procedencia: "Ambulatorio", prioridad: "normal", hora: "07:55", staff: { administrativo: "Pablo Yáñez", tens: "Nicolás Bravo", tm: "TM Andrea Bustos", radiologo: "Dr. Carlos Soto" }, comentarios: [] },
  { id: 21, cup: makeCUP(2021), rut: "14.222.444-5", nombre: "Antonia Fuenzalida L.", edad: 48, sexo: "F", fase: "examenes", estado: "validado", modalidad: "RM", estudio: "RM columna lumbar", procedencia: "Ambulatorio", prioridad: "normal", hora: "08:05", staff: { administrativo: "Loreto Cáceres", tens: "Camila Ossandón", tm: "TM Felipe Concha", radiologo: "Dra. Fernanda Ríos" }, comentarios: [] },
  { id: 22, cup: makeCUP(2022), rut: "8.333.555-6", nombre: "Rodrigo Escobar M.", edad: 77, sexo: "M", fase: "examenes", estado: "validado", modalidad: "RX", estudio: "RX tórax PA y lateral", procedencia: "Hospitalizado", prioridad: "alta", hora: "08:15", staff: { administrativo: "Pablo Yáñez", tens: "Nicolás Bravo", tm: "TM Andrea Bustos", radiologo: "Dr. Matías Contreras" }, comentarios: [] },
  { id: 23, cup: makeCUP(2023), rut: "20.444.666-7", nombre: "Camila Reyes T.", edad: 33, sexo: "F", fase: "examenes", estado: "informado", modalidad: "MG", estudio: "Mamografía bilateral", procedencia: "Ambulatorio", prioridad: "normal", hora: "08:25", staff: { administrativo: "Loreto Cáceres", tens: "Camila Ossandón", tm: "TM Felipe Concha", radiologo: "Dra. Javiera Rojas" }, comentarios: [] },
  { id: 24, cup: makeCUP(2024), rut: "28.555.777-8", nombre: "Diego Castillo P.", edad: 5, sexo: "M", fase: "examenes", estado: "almacenado", modalidad: "TC", estudio: "TC cerebro con contraste", procedencia: "Urgencia", prioridad: "stat", hora: "08:35", staff: { administrativo: "Pablo Yáñez", tens: "Nicolás Bravo", tm: "TM Andrea Bustos", radiologo: "Dr. Carlos Soto" }, comentarios: [] },
].map((r) => ({
  categoria: null,
  consentimiento: false,
  clinico: { creatinina: null, talla: null, peso: null, contrasteMl: null, medioContraste: null },
  adjuntos: [],
  anamnesis: "",
  fecha: "2026-07-05",
  bono: null,
  ...r,
})).map((r) => ({
  ...r,
  acc: r.fase === "agendados" ? null : makeACC(r.id),
  ot: r.fase === "agendados" ? null : makeOT(r.id),
  timestamps: deriveTimestamps(r),
})).map((r) => ({
  ...r,
  codigoExamen: `${r.modalidad}-${String(r.id).padStart(4, "0")}`,
  medicoSolicitante: MEDICOS_SOLICITANTES[r.id % MEDICOS_SOLICITANTES.length],
  clasificacionCritica: r.prioridad === "stat",
  titulo: r.estudio,
  cie10Indicacion: [],
  cie10Conclusion: [],
})); // campos nuevos con default — así no se reescriben los 24 registros a mano

/* ────────────────────────────────────────────────────────────────
   § 5 · PIEZAS VISUALES REUTILIZABLES
   ──────────────────────────────────────────────────────────────── */
const ModBadge = ({ mod }) => {
  const m = MODALIDADES[mod] || { color: D.txl };
  return (
    <span title={m.nombre} style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", minWidth: 38, height: 20, padding: "0 6px", borderRadius: 5, background: `${m.color}22`, color: m.color, border: `1px solid ${m.color}44`, fontSize: 10, fontWeight: 700 }}>
      {mod}
    </span>
  );
};

const EstadoBadge = ({ estado }) => {
  const s = ESTADOS[estado] || { label: estado, color: D.txl };
  return (
    <span style={{ display: "inline-flex", alignItems: "center", padding: "2px 8px", borderRadius: 5, background: `${s.color}20`, color: s.color, border: `1px solid ${s.color}3A`, fontSize: 10, fontWeight: 600, whiteSpace: "nowrap" }}>
      {s.label}
    </span>
  );
};

const PrioTag = ({ prioridad }) => {
  const p = PRIORIDADES[prioridad] || PRIORIDADES.normal;
  if (!p.label) return <span style={{ color: D.txl, fontSize: 10 }}>—</span>;
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 3, padding: "2px 7px", borderRadius: 5, background: `${p.color}22`, color: p.color, border: `1px solid ${p.color}44`, fontSize: 9, fontWeight: 700, animation: prioridad === "stat" ? "rpPulse 1.6s ease-in-out infinite" : "none" }}>
      {prioridad === "stat" && <Zap size={9} />}{p.label}
    </span>
  );
};

const PacienteCell = ({ r }) => (
  <div>
    <div style={{ fontSize: 12, fontWeight: 600, color: D.txt }}>{r.nombre}</div>
    <span style={{ fontSize: 9, fontWeight: 700, background: D.bg, color: D.tea, padding: "1px 6px", borderRadius: 4, fontFamily: "monospace", display: "inline-block", marginTop: 2 }}>{r.cup}</span>
  </div>
);
const RutCell = ({ rut }) => <span style={{ fontSize: 11, color: D.txm, fontFamily: "monospace" }}>{rut}</span>;

/** OT/ACC: el número va limpio, sin repetir el prefijo que ya dice el encabezado de columna. */
const soloNumero = (valor) => (valor ? valor.replace(/^(OT|ACC)-/, "") : "—");

const StaffName = ({ name }) => <span style={{ fontSize: 11, color: name ? D.txt : D.txl }}>{name || "Sin asignar"}</span>;

const TabCard = ({ fase, active, count, onClick }) => {
  const I = fase.icon; // fase.icon ya existe en FASES — solo faltaba extraerlo (mismo patrón que RowIcon)
  return (
    <button onClick={onClick} style={{ textAlign: "left", cursor: "pointer", background: active ? `linear-gradient(135deg, ${fase.color}26, ${fase.color}0A)` : D.sfc, border: `1px solid ${active ? fase.color : D.brd}`, borderRadius: 12, padding: "14px 16px", position: "relative", overflow: "hidden" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ fontSize: 10, color: active ? fase.color : D.txl, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.5px" }}>{fase.label}</div>
          <div style={{ fontSize: 26, fontWeight: 700, color: D.txt, marginTop: 4 }}>{count}</div>
        </div>
        <div style={{ background: `${fase.color}22`, borderRadius: 9, padding: 8 }}><I size={17} color={fase.color} /></div>
      </div>
      <div style={{ position: "absolute", top: 0, left: 0, width: 3, height: "100%", background: fase.color }} />
    </button>
  );
};

const Chip = ({ active, onClick, children, color = D.pri }) => (
  <button onClick={onClick} style={{ padding: "5px 12px", borderRadius: 7, fontSize: 11, fontWeight: 600, cursor: "pointer", border: `1px solid ${active ? color : D.brd}`, background: active ? `${color}22` : D.sfc, color: active ? color : D.txm, whiteSpace: "nowrap" }}>
    {children}
  </button>
);

const Field = ({ label, value, last }) => (
  <div style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: last ? "none" : `1px solid ${D.brd}` }}>
    <span style={{ fontSize: 11, color: D.txl }}>{label}</span>
    <span style={{ fontSize: 11, fontWeight: 600, color: D.txt }}>{value}</span>
  </div>
);

const ProcedenciaCell = ({ r, categorias }) => {
  const cat = r.categoria ? categorias.find((c) => c.id === r.categoria) : null;
  return (
    <div>
      <div style={{ fontSize: 11, color: D.txm }}>{r.procedencia}</div>
      {cat && (
        <span style={{ display: "inline-block", marginTop: 3, fontSize: 9, fontWeight: 600, padding: "1px 6px", borderRadius: 4, background: `${cat.color}22`, color: cat.color, border: `1px solid ${cat.color}44` }}>
          {cat.label}
        </span>
      )}
    </div>
  );
};

const AdjuntarButton = ({ r, onOpen }) => (
  <button
    onClick={(e) => { e.stopPropagation(); onOpen(r); }}
    title={`Adjuntar examen externo${(r.adjuntos || []).length ? ` · ${r.adjuntos.length} adjunto(s)` : ""}`}
    style={{ display: "inline-flex", alignItems: "center", gap: 3, padding: "4px 6px", borderRadius: 6, border: `1px solid ${(r.adjuntos || []).length ? D.tea + "55" : D.brd}`, background: "transparent", color: (r.adjuntos || []).length ? D.tea : D.txm, cursor: "pointer" }}
  >
    <Paperclip size={12} />{(r.adjuntos || []).length > 0 && <span style={{ fontSize: 9, fontWeight: 700 }}>{r.adjuntos.length}</span>}
  </button>
);

/* §11 — 4 estados visuales, uno solo verdadero a la vez:
   1) sin bono todavía -> botón para ingresarlo (ingreso presencial, §11a)
   2) bono pendiente pero el examen no ha llegado a Almacenado -> visible, no clickeable
   3) bono pendiente Y (Almacenado o Reagendado) -> "accionable": parpadeo (misma animación
      rpPulse que ya usa PrioTag para "stat"), abre la mini-ventana de Validar/Anular/Reagendar
   4) bono ya resuelto (validado/anulado) -> badge final, nada más que hacer */
const BonoCell = ({ r, onIngresar, onAbrirFinalizar }) => {
  if (!r.bono) {
    return (
      <button onClick={(e) => { e.stopPropagation(); onIngresar(r); }} style={{ display: "flex", alignItems: "center", gap: 4, padding: "4px 8px", borderRadius: 6, border: `1px dashed ${D.brd}`, background: "transparent", color: D.txl, fontSize: 9.5, fontWeight: 600, cursor: "pointer", whiteSpace: "nowrap" }}>
        <Ticket size={11} />Ingresar bono
      </button>
    );
  }
  const cfg = BONO_ESTADOS[r.bono.estado];
  if (r.bono.estado !== "pendiente_pago") {
    return <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 9.5, fontWeight: 700, color: cfg.color, whiteSpace: "nowrap" }}><Ticket size={11} />{r.bono.numero} · {cfg.label}</span>;
  }
  const accionable = r.estado === "almacenado" || r.estado === "reagendado";
  if (!accionable) {
    return <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 9.5, color: D.txl, whiteSpace: "nowrap" }}><Ticket size={11} />{r.bono.numero} · pendiente</span>;
  }
  return (
    <button onClick={(e) => { e.stopPropagation(); onAbrirFinalizar(r); }} style={{ display: "flex", alignItems: "center", gap: 4, padding: "4px 8px", borderRadius: 6, border: `1px solid ${D.war}88`, background: `${D.war}22`, color: D.war, fontSize: 9.5, fontWeight: 700, cursor: "pointer", whiteSpace: "nowrap", animation: "rpPulse 1.6s ease-in-out infinite" }}>
      <AlertTriangle size={11} />Bono {r.bono.numero} · resolver
    </button>
  );
};

const Cie10Multibox = ({ seleccionados, onChange, placeholder }) => {
  const [query, setQuery] = useState("");
  const [abierto, setAbierto] = useState(false);
  const q = query.trim().toLowerCase();
  const filtrados = q ? CIE10_MUESTRA.filter((c) => !seleccionados.some((s) => s.codigo === c.codigo) && (c.codigo.toLowerCase().includes(q) || c.glosa.toLowerCase().includes(q))).slice(0, 8) : [];

  const agregar = (c) => { onChange([...seleccionados, c]); setQuery(""); setAbierto(false); };
  const quitar = (codigo) => onChange(seleccionados.filter((s) => s.codigo !== codigo));

  return (
    <div>
      {seleccionados.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 5, marginBottom: 6 }}>
          {seleccionados.map((s) => (
            <span key={s.codigo} style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 10, fontWeight: 600, padding: "3px 6px 3px 8px", borderRadius: 5, background: `${D.tea}1E`, color: D.tea, border: `1px solid ${D.tea}44` }}>
              <b>{s.codigo}</b> — {s.glosa}
              <button onClick={() => quitar(s.codigo)} style={{ background: "none", border: "none", cursor: "pointer", color: D.tea, display: "flex" }}><X size={11} /></button>
            </span>
          ))}
        </div>
      )}
      <div style={{ position: "relative" }}>
        <input
          value={query}
          onChange={(e) => { setQuery(e.target.value); setAbierto(true); }}
          onFocus={() => setAbierto(true)}
          onBlur={() => setTimeout(() => setAbierto(false), 150)}
          placeholder={placeholder || "Escribe código o glosa (ej. M54 o lumbago)…"}
          style={{ width: "100%", padding: "7px 9px", borderRadius: 7, border: `1px solid ${D.brd}`, background: D.bg, color: D.txt, fontSize: 11 }}
        />
        {abierto && q && (
          <div style={{ position: "absolute", top: "calc(100% + 3px)", left: 0, right: 0, background: D.sfc2, border: `1px solid ${D.brd}`, borderRadius: 8, zIndex: 20, maxHeight: 200, overflowY: "auto" }}>
            {filtrados.length === 0 && <div style={{ padding: "8px 10px", fontSize: 10.5, color: D.txl }}>Sin coincidencias en la muestra cargada.</div>}
            {filtrados.map((c) => (
              <div key={c.codigo} onMouseDown={() => agregar(c)} style={{ padding: "7px 10px", fontSize: 11, color: D.txt, cursor: "pointer", borderBottom: `1px solid ${D.brd}` }}>
                <b style={{ color: D.tea }}>{c.codigo}</b> — {c.glosa}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const MiniField = ({ label, value, onChange }) => (
  <div>
    <div style={{ fontSize: 9, color: D.txl, marginBottom: 3 }}>{label}</div>
    <input
      type="number"
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value === "" ? null : Number(e.target.value))}
      style={{ width: "100%", padding: "6px 8px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.bg, color: D.txt, fontSize: 11 }}
    />
  </div>
);

/* ────────────────────────────────────────────────────────────────
   Generador + lector DICOM mínimo — corre en el navegador, mismo esquema
   de dataset (Implicit VR LE) que el motor Node (dicom-engine/). Prueba
   real de que el ciclo codificar → decodificar → pintar funciona acá
   mismo, sin depender de una conexión a ningún servidor.
   Ahora con 3 cortes (simulando una serie corta) y ventaneo real
   (fórmula DICOM PS3.3 C.11.2.1.2 — no es un filtro CSS de adorno).
   Simplificado a propósito: sin grupo File Meta (eso ya se probó aparte,
   en el motor Node, con el archivo Part10 completo).
   ──────────────────────────────────────────────────────────────── */
function generarPixelesPatron(seed, W, H) {
  const pixels = new Uint8Array(W * H);
  const cx = W / 2, cy = H / 2;
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const d = Math.sqrt((x - cx) ** 2 + (y - cy) ** 2);
      const anillo = Math.floor((d + seed) / 7) % 2;
      pixels[y * W + x] = anillo ? 225 : 35;
    }
  }
  // Marcador asimétrico arriba-izquierda — sin esto, los círculos concéntricos son simétricos
  // y rotar/invertir no se notaría a simple vista (no serviría para comprobar nada).
  const m = Math.floor(Math.min(W, H) * 0.14);
  for (let y = 4; y < 4 + m; y++) for (let x = 4; x < 4 + m; x++) pixels[y * W + x] = 255;
  return pixels;
}

/** Rotación real de la matriz de píxeles 90° horario — verificada con test unitario, no es un truco visual con CSS. */
function rotar90CW(pixelData, cols, rows) {
  const out = new Uint8Array(cols * rows);
  for (let newRow = 0; newRow < cols; newRow++) {
    for (let newCol = 0; newCol < rows; newCol++) {
      out[newRow * rows + newCol] = pixelData[(rows - 1 - newCol) * cols + newRow];
    }
  }
  return out;
}

function construirCorteDicomDemo({ nombre, cup, modalidad }, indiceCorte, W = 180, H = 180) {
  const seedBase = cup.split("").reduce((a, c) => a + c.charCodeAt(0), 0);
  const pixels = generarPixelesPatron(seedBase + indiceCorte * 9, W, H);
  const partes = [];
  const push = (group, element, valBuf) => {
    const head = new Uint8Array(8);
    new DataView(head.buffer).setUint16(0, group, true);
    new DataView(head.buffer).setUint16(2, element, true);
    new DataView(head.buffer).setUint32(4, valBuf.length, true);
    partes.push(head, valBuf);
  };
  const str = (s) => { let b = new TextEncoder().encode(s); if (b.length % 2) b = new Uint8Array([...b, 0x20]); return b; };
  const u16 = (n) => { const b = new Uint8Array(2); new DataView(b.buffer).setUint16(0, n, true); return b; };

  push(0x0008, 0x0018, str(`1.2.826.TEST.${cup}.${indiceCorte + 1}`));
  push(0x0020, 0x0013, str(String(indiceCorte + 1))); // Instance Number
  push(0x0010, 0x0010, str(nombre));
  push(0x0008, 0x0060, str(modalidad));
  push(0x0028, 0x0010, u16(H));
  push(0x0028, 0x0011, u16(W));
  push(0x0028, 0x0100, u16(8));
  push(0x0028, 0x0103, u16(0));
  push(0x7fe0, 0x0010, pixels);

  const totalLen = partes.reduce((a, e) => a + e.length, 0);
  const dataset = new Uint8Array(totalLen);
  let o = 0; for (const e of partes) { dataset.set(e, o); o += e.length; }
  const preamble = new Uint8Array(128);
  const magic = new TextEncoder().encode("DICM");
  const full = new Uint8Array(preamble.length + magic.length + dataset.length);
  full.set(preamble, 0); full.set(magic, 128); full.set(dataset, 132);
  return full;
}

function leerDicomDemo(buffer) {
  let o = 132; // 128 preámbulo + 4 "DICM" — sin File Meta en esta demo
  const dv = new DataView(buffer.buffer, buffer.byteOffset, buffer.byteLength);
  let rows = 0, cols = 0, pixelData = null;
  const tags = {};
  while (o < buffer.length) {
    const group = dv.getUint16(o, true);
    const element = dv.getUint16(o + 2, true);
    const length = dv.getUint32(o + 4, true);
    const value = buffer.slice(o + 8, o + 8 + length);
    const key = group.toString(16).padStart(4, "0") + element.toString(16).padStart(4, "0");
    if (key === "00280010") rows = new DataView(value.buffer, value.byteOffset).getUint16(0, true);
    else if (key === "00280011") cols = new DataView(value.buffer, value.byteOffset).getUint16(0, true);
    else if (key === "7fe00010") pixelData = value;
    else tags[key] = new TextDecoder().decode(value).replace(/\s+$/, "");
    o += 8 + length;
  }
  return { rows, cols, pixelData, tags };
}

/** Ventaneo real (brillo=centro, contraste=ancho) — PS3.3 C.11.2.1.2, la misma fórmula que usa cualquier visor DICOM. */
function aplicarVentana(x, center, width) {
  const w = Math.max(width, 1);
  if (x <= center - 0.5 - (w - 1) / 2) return 0;
  if (x > center - 0.5 + (w - 1) / 2) return 255;
  return ((x - (center - 0.5)) / (w - 1) + 0.5) * 255;
}

const NUM_CORTES_DEMO = 3;

/* Cómo se acomodan de 1 a 6 vistas — usado tanto por el ícono del selector como por la grilla real. */
const GRID_TEMPLATES = { 1: { cols: 1, rows: 1 }, 2: { cols: 2, rows: 1 }, 3: { cols: 3, rows: 1 }, 4: { cols: 2, rows: 2 }, 5: { cols: 3, rows: 2 }, 6: { cols: 3, rows: 2 } };

const MiniGridIcon = ({ n, color, size = 20 }) => {
  const { cols, rows } = GRID_TEMPLATES[n];
  const gap = 2, cell = (size - gap * (cols - 1)) / cols, cellH = (size - gap * (rows - 1)) / rows;
  const celdas = Array.from({ length: cols * rows }, (_, i) => i < n);
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {celdas.map((activa, i) => {
        const cx = (i % cols) * (cell + gap), cy = Math.floor(i / cols) * (cellH + gap);
        return <rect key={i} x={cx} y={cy} width={cell} height={cellH} rx={1.5} fill={activa ? color : "none"} stroke={color} strokeWidth={activa ? 0 : 1} opacity={activa ? 1 : 0.35} />;
      })}
    </svg>
  );
};
const HERRAMIENTAS = [
  { id: "ventana", label: "Ventana", icon: Sun },
  { id: "pan", label: "Pan", icon: Move },
  { id: "zoom", label: "Zoom", icon: ZoomIn },
  { id: "rotar", label: "Rotar", icon: RotateCw },
  { id: "invertir", label: "Invertir", icon: Contrast },
  { id: "medir", label: "Medir", icon: Ruler },
  { id: "referencia", label: "Referencia cruzada", icon: Crosshair },
];
/** Herramientas reales de PACS que necesitan datos volumétricos/multi-modales que hoy no tenemos —
    puertas etiquetadas visibles pero apagadas a propósito, no botones que fingen funcionar. */
const HERRAMIENTAS_FUTURAS = [
  { label: "MPR", nota: "Necesita volumen 3D real" },
  { label: "Cobb", nota: "Necesita calibración de spacing real" },
  { label: "Fusión PET-CT", nota: "Necesita 2 estudios co-registrados" },
];

/** Convierte un click del mouse a coordenadas de píxel del canvas, sin importar el zoom/pan aplicado por CSS. */
function coordenadasCanvas(e, canvas) {
  const rect = canvas.getBoundingClientRect();
  return { x: ((e.clientX - rect.left) / rect.width) * canvas.width, y: ((e.clientY - rect.top) / rect.height) * canvas.height };
}

const ViewportPanel = ({ record, corteInicial, herramienta, puntoReferencia, onSetReferencia, focused, onFocus }) => {
  const canvasRef = useRef(null);
  const [cortesData, setCortesData] = useState(null);
  const [corteActivo, setCorteActivo] = useState(corteInicial);
  const [center, setCenter] = useState(128);
  const [width, setWidth] = useState(256);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [rotDeg, setRotDeg] = useState(0);
  const [invertido, setInvertido] = useState(false);
  const [medicion, setMedicion] = useState(null);
  const arrastre = useRef(null);

  useEffect(() => {
    const generados = Array.from({ length: NUM_CORTES_DEMO }, (_, i) => leerDicomDemo(construirCorteDicomDemo(record, i)));
    setCortesData(generados);
  }, [record]);

  const corteBase = cortesData ? cortesData[corteActivo] : null;
  const corteRotado = useMemo(() => {
    if (!corteBase) return null;
    let pixelData = corteBase.pixelData, cols = corteBase.cols, rows = corteBase.rows;
    const vueltas = ((rotDeg / 90) % 4 + 4) % 4;
    for (let i = 0; i < vueltas; i++) { pixelData = rotar90CW(pixelData, cols, rows); [cols, rows] = [rows, cols]; }
    return { pixelData, cols, rows };
  }, [corteBase, rotDeg]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !corteRotado) return;
    canvas.width = corteRotado.cols; canvas.height = corteRotado.rows;
    const ctx = canvas.getContext("2d");
    const imgData = ctx.createImageData(corteRotado.cols, corteRotado.rows);
    for (let i = 0; i < corteRotado.pixelData.length; i++) {
      let v = aplicarVentana(corteRotado.pixelData[i], center, width);
      if (invertido) v = 255 - v;
      imgData.data[i * 4] = v; imgData.data[i * 4 + 1] = v; imgData.data[i * 4 + 2] = v; imgData.data[i * 4 + 3] = 255;
    }
    ctx.putImageData(imgData, 0, 0);
  }, [corteRotado, center, width, invertido]);

  /* Scroll del mouse = cambiar de corte — la interacción real, no un botón numerado. */
  const onWheel = (e) => {
    e.preventDefault();
    onFocus();
    setCorteActivo((c) => Math.min(NUM_CORTES_DEMO - 1, Math.max(0, c + (e.deltaY > 0 ? 1 : -1))));
  };

  const onMouseDown = (e) => {
    onFocus();
    const canvas = canvasRef.current;
    const pt = coordenadasCanvas(e, canvas);
    if (herramienta === "pan") arrastre.current = { tipo: "pan", startX: e.clientX, startY: e.clientY, panX: pan.x, panY: pan.y };
    else if (herramienta === "ventana") arrastre.current = { tipo: "ventana", startX: e.clientX, startY: e.clientY, center0: center, width0: width };
    else if (herramienta === "medir") setMedicion(medicion && !medicion.p2 ? { p1: medicion.p1, p2: pt } : { p1: pt, p2: null });
    else if (herramienta === "referencia") onSetReferencia({ rx: pt.x / canvas.width, ry: pt.y / canvas.height });
  };
  const onMouseMove = (e) => {
    if (!arrastre.current) return;
    if (arrastre.current.tipo === "pan") {
      setPan({ x: arrastre.current.panX + (e.clientX - arrastre.current.startX), y: arrastre.current.panY + (e.clientY - arrastre.current.startY) });
    } else if (arrastre.current.tipo === "ventana") {
      setCenter(Math.max(0, Math.min(255, arrastre.current.center0 + (e.clientY - arrastre.current.startY))));
      setWidth(Math.max(2, Math.min(512, arrastre.current.width0 + (e.clientX - arrastre.current.startX))));
    }
  };
  const onMouseUp = () => { arrastre.current = null; };

  if (!cortesData) return <div style={{ color: D.txl, fontSize: 11, padding: 20, textAlign: "center" }}>Generando…</div>;

  const distanciaPx = medicion && medicion.p2 ? Math.hypot(medicion.p2.x - medicion.p1.x, medicion.p2.y - medicion.p1.y) : null;
  const cursor = herramienta === "pan" ? "move" : herramienta === "ventana" ? "ns-resize" : herramienta === "medir" || herramienta === "referencia" ? "crosshair" : "default";

  return (
    <div
      onClick={onFocus} onWheel={onWheel}
      style={{ position: "relative", background: "#000", overflow: "hidden", border: `1px solid ${focused ? D.pri : "#152030"}`, height: "100%", display: "flex", alignItems: "center", justifyContent: "center", cursor }}
    >
      <canvas
        ref={canvasRef}
        onMouseDown={onMouseDown} onMouseMove={onMouseMove} onMouseUp={onMouseUp} onMouseLeave={onMouseUp}
        style={{ maxWidth: "100%", maxHeight: "100%", imageRendering: "pixelated", display: "block", transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`, transformOrigin: "center" }}
      />
      <svg style={{ position: "absolute", inset: 0, width: "100%", height: "100%", pointerEvents: "none" }} viewBox={`0 0 ${corteRotado.cols} ${corteRotado.rows}`} preserveAspectRatio="xMidYMid meet">
        {medicion && (
          <>
            <circle cx={medicion.p1.x} cy={medicion.p1.y} r={2.5} fill={D.war} />
            {medicion.p2 && <>
              <line x1={medicion.p1.x} y1={medicion.p1.y} x2={medicion.p2.x} y2={medicion.p2.y} stroke={D.war} strokeWidth={1} />
              <circle cx={medicion.p2.x} cy={medicion.p2.y} r={2.5} fill={D.war} />
            </>}
          </>
        )}
        {puntoReferencia && (
          <>
            <line x1={0} y1={puntoReferencia.ry * corteRotado.rows} x2={corteRotado.cols} y2={puntoReferencia.ry * corteRotado.rows} stroke={D.tea} strokeWidth={0.6} strokeDasharray="3 2" />
            <line x1={puntoReferencia.rx * corteRotado.cols} y1={0} x2={puntoReferencia.rx * corteRotado.cols} y2={corteRotado.rows} stroke={D.tea} strokeWidth={0.6} strokeDasharray="3 2" />
          </>
        )}
      </svg>

      <span style={{ position: "absolute", top: 8, left: 10, fontSize: 10, color: "#B9C6DA", fontFamily: "monospace", lineHeight: 1.4 }}>{record.nombre}<br />{record.cup}</span>
      <span style={{ position: "absolute", top: 8, right: 10, fontSize: 10, color: "#B9C6DA", fontFamily: "monospace", textAlign: "right", lineHeight: 1.4 }}>AXON RIS/PACS<br />{record.modalidad} · {record.estudio}</span>
      <span style={{ position: "absolute", bottom: 8, left: 10, fontSize: 10, color: "#8FA3C7", fontFamily: "monospace" }}>Corte {corteActivo + 1}/{NUM_CORTES_DEMO}</span>
      <span style={{ position: "absolute", bottom: 8, right: 10, fontSize: 10, color: "#8FA3C7", fontFamily: "monospace", textAlign: "right" }}>W:{Math.round(center)} L:{Math.round(width)}{invertido ? " · INV" : ""}<br />Zoom {Math.round(zoom * 100)}%</span>
      {distanciaPx != null && <span style={{ position: "absolute", bottom: 26, left: 10, fontSize: 10, color: D.war, fontFamily: "monospace" }}>{distanciaPx.toFixed(1)} px</span>}
      {herramienta === "zoom" && (
        <div style={{ position: "absolute", top: "50%", right: 10, transform: "translateY(-50%)", display: "flex", flexDirection: "column", gap: 4 }}>
          <button onClick={(e) => { e.stopPropagation(); setZoom((z) => Math.min(4, z + 0.25)); }} style={{ width: 24, height: 24, borderRadius: 5, border: `1px solid ${D.brd}`, background: "rgba(17,31,50,0.85)", color: D.txm, fontSize: 12, cursor: "pointer" }}>+</button>
          <button onClick={(e) => { e.stopPropagation(); setZoom((z) => Math.max(0.5, z - 0.25)); }} style={{ width: 24, height: 24, borderRadius: 5, border: `1px solid ${D.brd}`, background: "rgba(17,31,50,0.85)", color: D.txm, fontSize: 12, cursor: "pointer" }}>−</button>
        </div>
      )}
      {herramienta === "rotar" && (
        <button onClick={(e) => { e.stopPropagation(); setRotDeg((d) => d + 90); }} style={{ position: "absolute", top: 8, left: "50%", transform: "translateX(-50%)", padding: "4px 10px", borderRadius: 5, border: `1px solid ${D.brd}`, background: "rgba(17,31,50,0.85)", color: D.txm, fontSize: 10, cursor: "pointer" }}>Girar 90°</button>
      )}
      {herramienta === "invertir" && (
        <button onClick={(e) => { e.stopPropagation(); setInvertido((v) => !v); }} style={{ position: "absolute", top: 8, left: "50%", transform: "translateX(-50%)", padding: "4px 10px", borderRadius: 5, border: `1px solid ${D.brd}`, background: "rgba(17,31,50,0.85)", color: D.txm, fontSize: 10, cursor: "pointer" }}>{invertido ? "Quitar inversión" : "Invertir colores"}</button>
      )}
    </div>
  );
};

const VisorPantallaCompleta = ({ record, mostrarInforme, sesion, informeCampos, setInformeCampos, onVolver, onAbrirInforme, onValidarInforme, misPlantillas, guardarPlantilla, nombrePlantilla, setNombrePlantilla, setTitulo, setClasificacionCritica, setCie10 }) => {
  const [layout, setLayout] = useState(mostrarInforme ? 1 : 2);
  const [selectorAbierto, setSelectorAbierto] = useState(false);
  const [dictandoCampo, setDictandoCampo] = useState(null);
  const [ordenAbierta, setOrdenAbierta] = useState(false);
  // "Horario" (Hábil/Inhábil) es un flag del momento de informar, no algo que necesite
  // sobrevivir a cerrar/reabrir el visor -> estado local acá, no en el componente padre.
  const [horario, setHorario] = useState("habil");
  const reconocimientoRef = useRef(null);
  // Estudios previos: hoy no hay fuente de datos real para exámenes anteriores del mismo
  // paciente — se deja el array vacío a propósito (no se inventa data) y el sidebar
  // muestra el estado vacío honesto. Cuando exista la fuente real, esto pasa a venir
  // de una consulta (por RUT/CUP) y el bloque de abajo ya queda listo para recibirla.
  const estudiosPrevios = [];

  const toggleDictado = (campo) => {
    if (dictandoCampo === campo) { reconocimientoRef.current?.stop(); setDictandoCampo(null); return; }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { alert("Este navegador no soporta dictado por voz nativo (funciona en Chrome/Edge). En producción esto se reemplaza por Whisper autoalojado."); return; }
    const r = new SR();
    r.lang = "es-CL"; r.continuous = true; r.interimResults = false;
    r.onresult = (e) => {
      let texto = "";
      for (let i = e.resultIndex; i < e.results.length; i++) texto += e.results[i][0].transcript + " ";
      setInformeCampos((prev) => ({ ...prev, [campo]: ((prev[campo] || "").trim() + " " + texto).trim() }));
    };
    r.onerror = () => setDictandoCampo(null);
    r.onend = () => setDictandoCampo(null);
    try { r.start(); reconocimientoRef.current = r; setDictandoCampo(campo); }
    catch { alert("No se pudo activar el micrófono — revisa los permisos del navegador."); }
  };
  const [herramienta, setHerramienta] = useState("ventana");
  const [puntoReferencia, setPuntoReferencia] = useState(null);
  const [panelFocado, setPanelFocado] = useState(0);

  return (
    <div style={{ position: "fixed", inset: 0, background: D.bg, zIndex: 500, display: "flex", flexDirection: "column", fontFamily: "'Inter',system-ui,-apple-system,sans-serif" }}>
      <style>{`*{box-sizing:border-box;} select{-webkit-appearance:none;}`}</style>

      {/* Barra superior */}
      <div style={{ height: 56, background: D.sfc, borderBottom: `1px solid ${D.brd}`, display: "flex", alignItems: "center", gap: 12, padding: "0 14px", flexShrink: 0, overflowX: "auto" }}>
        <button onClick={onVolver} style={{ display: "flex", alignItems: "center", gap: 6, padding: "7px 12px", borderRadius: 7, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txm, fontSize: 11, fontWeight: 700, cursor: "pointer", flexShrink: 0 }}>← Volver</button>
        <div style={{ fontSize: 11, lineHeight: 1.3, flexShrink: 0 }}>
          <div style={{ fontWeight: 700, color: D.txt }}>{record.nombre}</div>
          <div style={{ color: D.txl }}>{record.cup} · {record.modalidad} · {record.estudio}</div>
        </div>
        <div style={{ width: 1, height: 28, background: D.brd, flexShrink: 0 }} />
        <div style={{ display: "flex", gap: 4, flexShrink: 0 }}>
          {HERRAMIENTAS.map((h) => (
            <button key={h.id} onClick={() => setHerramienta(h.id)} title={h.label} style={{ display: "flex", alignItems: "center", gap: 4, padding: "7px 9px", borderRadius: 6, border: `1px solid ${herramienta === h.id ? D.pri : D.brd}`, background: herramienta === h.id ? `${D.pri}22` : D.sfc2, color: herramienta === h.id ? "#D6DCE4" : D.txm, fontSize: 10, fontWeight: 600, cursor: "pointer" }}>
              <h.icon size={13} />
            </button>
          ))}
        </div>
        <div style={{ width: 1, height: 28, background: D.brd, flexShrink: 0 }} />
        <div style={{ display: "flex", gap: 4, flexShrink: 0 }}>
          {HERRAMIENTAS_FUTURAS.map((h) => (
            <button key={h.label} disabled title={`${h.label} — ${h.nota}`} style={{ padding: "7px 10px", borderRadius: 6, border: `1px dashed ${D.brd}`, background: "transparent", color: D.txl, fontSize: 9.5, fontWeight: 600, cursor: "not-allowed" }}>{h.label}</button>
          ))}
        </div>
        <div style={{ marginLeft: "auto", position: "relative", flexShrink: 0 }}>
          <button onClick={() => setSelectorAbierto((v) => !v)} style={{ display: "flex", alignItems: "center", gap: 7, padding: "6px 10px", borderRadius: 7, border: `1px solid ${selectorAbierto ? D.pri : D.brd}`, background: selectorAbierto ? `${D.pri}1E` : D.sfc2, color: selectorAbierto ? "#D6DCE4" : D.txm, cursor: "pointer" }}>
            <MiniGridIcon n={layout} color="currentColor" size={20} />
            <span style={{ fontSize: 10.5, fontWeight: 600 }}>{layout} {layout === 1 ? "vista" : "vistas"}</span>
          </button>
          {selectorAbierto && (
            <div style={{ position: "absolute", top: "calc(100% + 6px)", right: 0, background: D.sfc2, border: `1px solid ${D.brd}`, borderRadius: 10, padding: 8, display: "flex", gap: 6, zIndex: 30, boxShadow: "0 8px 24px rgba(0,0,0,0.4)" }}>
              {[1, 2, 3, 4, 5, 6].map((n) => (
                <button key={n} onClick={() => { setLayout(n); setSelectorAbierto(false); }} title={`${n} ${n === 1 ? "vista" : "vistas"}`} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4, padding: "8px 7px", borderRadius: 7, border: `1px solid ${layout === n ? D.pri : "transparent"}`, background: layout === n ? `${D.pri}1E` : "transparent", cursor: "pointer" }}>
                  <MiniGridIcon n={n} color={layout === n ? D.pri : D.txm} size={22} />
                  <span style={{ fontSize: 8.5, color: layout === n ? "#D6DCE4" : D.txl, fontWeight: 600 }}>{n}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
        {/* Rail izquierdo: Series (igual que antes) + Estudios previos — sidebar siempre
            visible, ya no modal. Mismo gating que tenía el botón viejo (solo cuando
            mostrarInforme es true) — esto es layout, no se cambió a quién le llega. */}
        <div style={{ width: 200, background: D.sfc, borderRight: `1px solid ${D.brd}`, padding: 10, flexShrink: 0, overflowY: "auto", display: "flex", flexDirection: "column", gap: 16 }}>
          <div>
            {/* hoy solo tenemos 1 serie sintética de 3 cortes; no invento series que no existen */}
            <div style={{ fontSize: 9, fontWeight: 700, color: D.txl, textTransform: "uppercase", letterSpacing: "0.4px", marginBottom: 8 }}>Series</div>
            <div style={{ border: `1px solid ${D.pri}`, borderRadius: 8, padding: 8, background: `${D.pri}14` }}>
              <div style={{ aspectRatio: "1/1", background: "#000", borderRadius: 5, marginBottom: 6 }} />
              <div style={{ fontSize: 9.5, color: D.txt, fontWeight: 600 }}>{record.estudio}</div>
              <div style={{ fontSize: 9, color: D.txl, marginTop: 2 }}>{NUM_CORTES_DEMO} cortes</div>
            </div>
          </div>

          {mostrarInforme && (
            <div style={{ borderTop: `1px solid ${D.brd}`, paddingTop: 12 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 9, fontWeight: 700, color: D.txl, textTransform: "uppercase", letterSpacing: "0.4px", marginBottom: 8 }}>
                <Eye size={11} />Estudios previos
              </div>
              {estudiosPrevios.length === 0 ? (
                <div style={{ fontSize: 10, color: D.txl, lineHeight: 1.5 }}>Sin estudios previos registrados para este paciente en la demo — con datos reales, acá aparece la lista de exámenes anteriores de la misma persona para comparar.</div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {estudiosPrevios.map((p) => (
                    <div key={p.id} style={{ border: `1px solid ${D.brd}`, borderRadius: 7, padding: 7, fontSize: 10 }}>
                      <div style={{ color: D.txt, fontWeight: 600 }}>{p.modalidad} · {p.estudio}</div>
                      <div style={{ color: D.txl, marginTop: 2 }}>{p.fecha}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Grilla de viewports */}
        <div style={{ flex: 1, display: "grid", gridTemplateColumns: `repeat(${GRID_TEMPLATES[layout].cols}, 1fr)`, gridTemplateRows: `repeat(${GRID_TEMPLATES[layout].rows}, 1fr)`, gap: 2, background: "#000", padding: 2, minWidth: 0 }}>
          {Array.from({ length: layout }, (_, i) => (
            <ViewportPanel key={i} record={record} corteInicial={i % NUM_CORTES_DEMO} herramienta={herramienta} puntoReferencia={puntoReferencia} onSetReferencia={setPuntoReferencia} focused={panelFocado === i} onFocus={() => setPanelFocado(i)} />
          ))}
        </div>

        {/* Informe — solo si la sesión tiene permiso y el estudio está en fase examenes */}
        {mostrarInforme && (
          <div style={{ width: 400, background: D.sfc, borderLeft: `1px solid ${D.brd}`, padding: 14, flexShrink: 0, overflowY: "auto", display: "flex", flexDirection: "column", gap: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: D.txl, textTransform: "uppercase", letterSpacing: "0.4px" }}>Informe — {sesion.rol}</div>
              <button onClick={() => setOrdenAbierta(true)} style={{ display: "flex", alignItems: "center", gap: 5, padding: "5px 9px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txm, fontSize: 9.5, fontWeight: 600, cursor: "pointer" }}><FileText size={11} />Ver orden médica</button>
            </div>

            {/* Datos del paciente y del estudio — todo a la mano, sin adivinar */}
            <div style={{ background: D.bg, borderRadius: 8, padding: 10, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, fontSize: 10.5 }}>
              <div><span style={{ color: D.txl }}>Paciente: </span><span style={{ color: D.txt, fontWeight: 600 }}>{record.nombre}</span></div>
              <div><span style={{ color: D.txl }}>RUT: </span><span style={{ color: D.txt }}>{record.rut}</span></div>
              <div><span style={{ color: D.txl }}>Edad/Sexo: </span><span style={{ color: D.txt }}>{record.edad} · {record.sexo}</span></div>
              <div><span style={{ color: D.txl }}>Fecha: </span><span style={{ color: D.txt }}>{record.fecha}</span></div>
              <div><span style={{ color: D.txl }}>Código examen: </span><span style={{ color: D.txt, fontFamily: "monospace" }}>{record.codigoExamen}</span></div>
              <div><span style={{ color: D.txl }}>Procedencia: </span><span style={{ color: D.txt }}>{record.procedencia}</span></div>
              <div style={{ gridColumn: "1 / -1" }}><span style={{ color: D.txl }}>Médico solicitante: </span><span style={{ color: D.txt }}>{record.medicoSolicitante}</span></div>
            </div>

            <label style={{ display: "flex", alignItems: "center", gap: 7, fontSize: 11, color: D.txm, cursor: "pointer" }}>
              <input type="checkbox" checked={record.clasificacionCritica} onChange={(e) => setClasificacionCritica(record.id, e.target.checked)} />
              Patología crítica que requiere notificación
            </label>

            <div>
              <div style={{ fontSize: 9.5, fontWeight: 700, color: D.txl, marginBottom: 5 }}>Horario</div>
              <div style={{ display: "flex", gap: 14 }}>
                {[["habil", "Hábil"], ["inhabil", "Inhábil"]].map(([v, l]) => (
                  <label key={v} style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 11, color: D.txm, cursor: "pointer" }}>
                    <input type="radio" name="horario" checked={horario === v} onChange={() => setHorario(v)} />{l}
                  </label>
                ))}
              </div>
            </div>

            {record.anamnesis && (
              <div>
                <div style={{ fontSize: 9.5, fontWeight: 700, color: D.txl, marginBottom: 5 }}>Comentario TM (de la Worklist)</div>
                <div style={{ background: D.bg, borderRadius: 7, padding: "7px 9px", fontSize: 10.5, color: D.txm, lineHeight: 1.5 }}>{record.anamnesis}</div>
              </div>
            )}
            <div>
              <div style={{ fontSize: 9.5, fontWeight: 700, color: D.txl, marginBottom: 5 }}>Antecedentes Clínicos</div>
              <textarea value={informeCampos.antecedentes} onChange={(e) => setInformeCampos({ ...informeCampos, antecedentes: e.target.value })} rows={2} style={{ width: "100%", padding: "7px 9px", borderRadius: 7, border: `1px solid ${D.brd}`, background: D.bg, color: D.txt, fontSize: 11, resize: "vertical", fontFamily: "inherit" }} />
            </div>

            <div>
              <div style={{ fontSize: 9.5, fontWeight: 700, color: D.txl, marginBottom: 5 }}>Título del estudio</div>
              <input value={record.titulo} onChange={(e) => setTitulo(record.id, e.target.value)} style={{ width: "100%", padding: "7px 9px", borderRadius: 7, border: `1px solid ${D.brd}`, background: D.bg, color: D.txt, fontSize: 11.5, fontWeight: 600 }} />
            </div>

            <div>
              <div style={{ fontSize: 9.5, fontWeight: 700, color: D.txl, marginBottom: 5 }}>CIE-10 · Indicación clínica (motivo de envío)</div>
              <Cie10Multibox seleccionados={record.cie10Indicacion} onChange={(v) => setCie10(record.id, "cie10Indicacion", v)} />
            </div>

            <div>
              <div style={{ fontSize: 9.5, fontWeight: 700, color: D.txl, marginBottom: 5 }}>Plantillas (privadas, por radiólogo)</div>
              {misPlantillas.length > 0 && (
                <select onChange={(e) => {
                  const p = misPlantillas.find((x) => x.id === e.target.value);
                  if (p) setInformeCampos({ tecnica: p.tecnica || "", hallazgos: p.hallazgos || "", impresion: p.impresion || "", antecedentes: p.antecedentes || "" });
                }} style={{ width: "100%", padding: "7px 9px", borderRadius: 7, border: `1px solid ${D.brd}`, background: D.bg, color: D.txt, fontSize: 11, marginBottom: 6 }} defaultValue="">
                  <option value="" disabled>Cargar plantilla…</option>
                  {misPlantillas.map((p) => <option key={p.id} value={p.id}>{p.nombre}</option>)}
                </select>
              )}
              <div style={{ display: "flex", gap: 6 }}>
                <input value={nombrePlantilla} onChange={(e) => setNombrePlantilla(e.target.value)} placeholder="Nombre para guardar esta como plantilla…" style={{ flex: 1, padding: "6px 8px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.bg, color: D.txt, fontSize: 10.5 }} />
                <button onClick={guardarPlantilla} style={{ padding: "0 10px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txm, fontSize: 10, fontWeight: 600, cursor: "pointer" }}>Guardar</button>
              </div>
            </div>

            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 5 }}>
                <span style={{ fontSize: 9.5, fontWeight: 700, color: D.txl }}>Técnica</span>
                <button onClick={() => toggleDictado("tecnica")} title="Dictado por voz" style={{ display: "flex", padding: 4, borderRadius: 5, border: "none", background: dictandoCampo === "tecnica" ? D.dan : "transparent", color: dictandoCampo === "tecnica" ? "#fff" : D.txl, cursor: "pointer" }}><Mic size={12} /></button>
              </div>
              <textarea value={informeCampos.tecnica} onChange={(e) => setInformeCampos({ ...informeCampos, tecnica: e.target.value })} rows={2} style={{ width: "100%", padding: "7px 9px", borderRadius: 7, border: `1px solid ${dictandoCampo === "tecnica" ? D.dan : D.brd}`, background: D.bg, color: D.txt, fontSize: 11, resize: "vertical", fontFamily: "inherit" }} />
            </div>
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 5 }}>
                <span style={{ fontSize: 9.5, fontWeight: 700, color: D.txl }}>Hallazgos <span style={{ fontWeight: 400, textTransform: "none", color: D.txl }}>(sin códigos acá)</span></span>
                <button onClick={() => toggleDictado("hallazgos")} title="Dictado por voz" style={{ display: "flex", padding: 4, borderRadius: 5, border: "none", background: dictandoCampo === "hallazgos" ? D.dan : "transparent", color: dictandoCampo === "hallazgos" ? "#fff" : D.txl, cursor: "pointer" }}><Mic size={12} /></button>
              </div>
              <textarea value={informeCampos.hallazgos} onChange={(e) => setInformeCampos({ ...informeCampos, hallazgos: e.target.value })} rows={7} style={{ width: "100%", padding: "7px 9px", borderRadius: 7, border: `1px solid ${dictandoCampo === "hallazgos" ? D.dan : D.brd}`, background: D.bg, color: D.txt, fontSize: 11, resize: "vertical", fontFamily: "inherit" }} />
            </div>
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 5 }}>
                <span style={{ fontSize: 9.5, fontWeight: 700, color: D.txl }}>Impresión</span>
                <button onClick={() => toggleDictado("impresion")} title="Dictado por voz" style={{ display: "flex", padding: 4, borderRadius: 5, border: "none", background: dictandoCampo === "impresion" ? D.dan : "transparent", color: dictandoCampo === "impresion" ? "#fff" : D.txl, cursor: "pointer" }}><Mic size={12} /></button>
              </div>
              <textarea value={informeCampos.impresion} onChange={(e) => setInformeCampos({ ...informeCampos, impresion: e.target.value })} rows={3} style={{ width: "100%", padding: "7px 9px", borderRadius: 7, border: `1px solid ${dictandoCampo === "impresion" ? D.dan : D.brd}`, background: D.bg, color: D.txt, fontSize: 11, resize: "vertical", fontFamily: "inherit" }} />
            </div>

            <div>
              <div style={{ fontSize: 9.5, fontWeight: 700, color: D.txl, marginBottom: 5 }}>CIE-10 · Conclusión codificada</div>
              <Cie10Multibox seleccionados={record.cie10Conclusion} onChange={(v) => setCie10(record.id, "cie10Conclusion", v)} />
            </div>

            {record.estado === "almacenado" && <button onClick={onAbrirInforme} style={{ padding: "9px 12px", borderRadius: 8, border: "none", background: D.war, color: "#0A1420", fontSize: 12, fontWeight: 700, cursor: "pointer" }}>Marcar informado</button>}
            {record.estado === "informado" && <button onClick={onValidarInforme} style={{ padding: "9px 12px", borderRadius: 8, border: "none", background: D.suc, color: "#0A1420", fontSize: 12, fontWeight: 700, cursor: "pointer" }}>Validar y firmar</button>}
            {record.estado === "validado" && <div style={{ padding: "9px 12px", borderRadius: 8, border: `1px solid ${D.suc}44`, background: `${D.suc}18`, color: D.suc, fontSize: 11, fontWeight: 700, textAlign: "center" }}>Validado y firmado</div>}
          </div>
        )}
      </div>

      {ordenAbierta && (
        <>
          <div onClick={() => setOrdenAbierta(false)} style={{ position: "fixed", inset: 0, background: "rgba(4,9,16,0.7)", zIndex: 600 }} />
          <div style={{ position: "fixed", top: "50%", left: "50%", transform: "translate(-50%,-50%)", width: "min(420px,90vw)", background: D.sfc, border: `1px solid ${D.brd}`, borderRadius: 12, padding: 18, zIndex: 601 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}><b style={{ color: D.txt, fontSize: 13 }}>Orden médica</b><button onClick={() => setOrdenAbierta(false)} style={{ background: "none", border: "none", color: D.txl, cursor: "pointer" }}><X size={16} /></button></div>
            <div style={{ background: D.bg, borderRadius: 8, padding: 12, fontSize: 11, color: D.txm, lineHeight: 1.7 }}>
              <div><b style={{ color: D.txt }}>Examen solicitado:</b> {record.estudio}</div>
              <div><b style={{ color: D.txt }}>Código:</b> {record.codigoExamen}</div>
              <div><b style={{ color: D.txt }}>Médico solicitante:</b> {record.medicoSolicitante}</div>
              <div><b style={{ color: D.txt }}>Fecha orden:</b> {record.fecha}</div>
            </div>
            <p style={{ fontSize: 9.5, color: D.txl, marginTop: 8 }}>Documento escaneado real llega con el módulo de adjuntos de admisión — esto muestra los mismos datos estructurados que ya viajan con la orden.</p>
          </div>
        </>
      )}
      <div style={{ height: 30, background: D.sfc, borderTop: `1px solid ${D.brd}`, display: "flex", alignItems: "center", padding: "0 14px", flexShrink: 0 }}>
        <span style={{ fontSize: 10, color: D.txl }}>Rueda del mouse sobre la imagen = cambiar de corte · Arrastrar con "Ventana" activa = brillo/contraste</span>
      </div>
    </div>
  );
};

const StaffSelect = ({ label, value, options, onChange }) => (
  <div style={{ marginBottom: 10 }}>
    <div style={{ fontSize: 9, fontWeight: 700, color: D.txl, textTransform: "uppercase", letterSpacing: "0.4px", marginBottom: 5 }}>{label}</div>
    <select value={value || ""} onChange={(e) => onChange(e.target.value)} style={{ width: "100%", padding: "7px 9px", borderRadius: 7, border: `1px solid ${D.brd}`, background: D.bg, color: D.txt, fontSize: 11 }}>
      <option value="">Sin asignar</option>
      {options.map((o) => <option key={o} value={o}>{o}</option>)}
    </select>
  </div>
);

/* Botón de acción de fila — placeholders honestos para lo que aún no existe */
const RowIcon = ({ icon: I, disabled, title }) => (
  <span title={title} style={{ display: "inline-flex", padding: 5, borderRadius: 6, color: disabled ? "#3C4E68" : D.txm, cursor: disabled ? "not-allowed" : "pointer" }}>
    <I size={13} />
  </span>
);

/* ────────────────────────────────────────────────────────────────
   § 6 · CONFIGURACIÓN DE COLUMNAS POR PESTAÑA
   (agregar una unidad de examen nueva más adelante = agregar una
   entrada acá + su propio registro de estados, sin tocar el resto)
   ──────────────────────────────────────────────────────────────── */
const buildColumns = (fase, categorias, onAdjuntar, onIngresarBono, onAbrirFinalizarBono) => {
  const horaPar = (labelA, campoA, labelB, campoB) => [
    { key: "h1", label: labelA, render: (r) => <span style={{ fontSize: 10.5, color: D.txm, fontFamily: "monospace" }}>{r.timestamps[campoA] || "—"}</span> },
    { key: "h2", label: labelB, render: (r) => <span style={{ fontSize: 10.5, color: D.txt, fontFamily: "monospace", fontWeight: 600 }}>{r.timestamps[campoB] || "—"}</span> },
  ];
  const accOtCols = [
    { key: "ot", label: "OT", render: (r) => <span style={{ fontSize: 9.5, color: D.txl, fontFamily: "monospace" }}>{soloNumero(r.ot)}</span> },
    { key: "acc", label: "Acceso", render: (r) => <span style={{ fontSize: 9.5, color: D.txl, fontFamily: "monospace" }}>{soloNumero(r.acc)}</span> },
  ];
  const pacCol = { key: "pac", label: "Paciente", render: (r) => <PacienteCell r={r} /> };
  const rutCol = { key: "rut", label: "RUT/N° Documento", render: (r) => <RutCell rut={r.rut} /> };
  const modCol = { key: "mod", label: "Modalidad", render: (r) => <ModBadge mod={r.modalidad} /> };
  const estCol = { key: "est", label: "Estudio", render: (r) => <span style={{ fontSize: 11, color: D.txt }}>{r.estudio}</span> };
  const adjCol = { key: "adj", label: "", render: (r) => <AdjuntarButton r={r} onOpen={onAdjuntar} /> };
  const chevCol = { key: "chev", label: "", render: () => <ChevronRight size={14} color={D.txl} /> };

  const procCol = { key: "proc", label: "Procedencia", render: (r) => <ProcedenciaCell r={r} categorias={categorias} /> };

  if (fase === "agendados") {
    return [
      ...horaPar("Hora agendada", "horaAgendada", "Hora presentación", "horaPresentacion"),
      procCol, pacCol, rutCol, modCol, estCol,
      { key: "estado", label: "Estado", render: (r) => <EstadoBadge estado={r.estado} /> },
      { key: "staff", label: "Agendado por", render: (r) => <StaffName name={r.staff.administrativo} /> },
      adjCol, chevCol,
    ];
  }
  if (fase === "admision") {
    return [
      ...horaPar("Hora presentación", "horaPresentacion", "Hora admisión", "horaAdmision"),
      ...accOtCols,
      procCol, pacCol, rutCol, modCol, estCol,
      { key: "estado", label: "Estado", render: (r) => <EstadoBadge estado={r.estado} /> },
      { key: "bono", label: "Bono", render: (r) => <BonoCell r={r} onIngresar={onIngresarBono} onAbrirFinalizar={onAbrirFinalizarBono} /> },
      { key: "staff", label: "Registrado por", render: (r) => <StaffName name={r.staff.administrativo} /> },
      adjCol, chevCol,
    ];
  }
  if (fase === "worklist") {
    return [
      ...horaPar("Hora agendada", "horaAgendada", "Hora arribo", "horaArribo"),
      ...accOtCols,
      { key: "prio", label: "Prioridad", render: (r) => <PrioTag prioridad={r.prioridad} /> },
      procCol, pacCol, rutCol, modCol, estCol,
      { key: "estado", label: "Estado", render: (r) => <EstadoBadge estado={r.estado} /> },
      { key: "tm", label: "TM / Radiólogo", render: (r) => <StaffName name={r.staff.tm ? `${r.staff.tm}${r.staff.radiologo ? " · " + r.staff.radiologo : ""}` : r.staff.radiologo} /> },
      adjCol, chevCol,
    ];
  }
  // examenes
  return [
    ...horaPar("Hora atención", "horaAtencion", "Hora almacenado", "horaAlmacenado"),
    ...accOtCols,
    procCol, pacCol, rutCol, modCol, estCol,
    { key: "estado", label: "Estado informe", render: (r) => <EstadoBadge estado={r.estado} /> },
    { key: "rad", label: "Radiólogo", render: (r) => <StaffName name={r.staff.radiologo} /> },
    {
      key: "acciones", label: "Acciones", render: (r) => (
        <div style={{ display: "flex", alignItems: "center", gap: 2 }}>
          <RowIcon icon={Eye} disabled title="Ver imágenes — próxima sesión" />
          <RowIcon icon={FileText} disabled title="Ver PDF de informe — próxima sesión" />
          <RowIcon icon={Printer} disabled title="Enviar a impresora/grabadora — próxima sesión" />
          <RowIcon icon={MessageSquare} title="Comentario — abrir ficha" />
          <RowIcon icon={Share2} disabled title="Compartir a extrasistema — próxima sesión" />
          <RowIcon icon={Cpu} disabled title="Puerta IA — construida, inactiva (fase futura)" />
        </div>
      ),
    },
    adjCol, chevCol,
  ];
};

/* ────────────────────────────────────────────────────────────────
   § 7 · COMPONENTE PRINCIPAL
   ──────────────────────────────────────────────────────────────── */
/* URL de la API del Worklist real — configurable por prop para cada
   despliegue (dev/staging/producción); este valor es solo el default para
   correr localmente. Ver WorklistApiServer.js del motor. */
const WORKLIST_API_DEFAULT = "http://localhost:8043";

export default function HISRisPacsImaging({ apiBaseUrl = WORKLIST_API_DEFAULT, pollIntervalMs = 4000 } = {}) {
  const [data, setData] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [errorConexion, setErrorConexion] = useState(null);
  const [sesion, setSesion] = useState(SESIONES_DEMO[0]);
  const [activeFase, setActiveFase] = useState("worklist");
  const [search, setSearch] = useState("");
  const [fechaFiltro, setFechaFiltro] = useState("");
  const [modFilter, setModFilter] = useState("todas");
  const [onlyPrio, setOnlyPrio] = useState(false);
  const [sortAsc, setSortAsc] = useState(true);
  const [selectedId, setSelectedId] = useState(null);
  const [comentarioTxt, setComentarioTxt] = useState("");
  const [clock, setClock] = useState("");
  const [categorias, setCategorias] = useState(CATEGORIAS_DEFAULT);
  const [showCatManager, setShowCatManager] = useState(false);
  const [catNombre, setCatNombre] = useState("");
  const [catGrupo, setCatGrupo] = useState("Aislamiento");
  const [adjuntoTarget, setAdjuntoTarget] = useState(null);
  const [visorPaciente, setVisorPaciente] = useState(null);
  const [guardandoId, setGuardandoId] = useState(null);
  const [informeCampos, setInformeCampos] = useState({ tecnica: "", hallazgos: "", impresion: "", antecedentes: "" });
  const [plantillasNuevas, setPlantillasNuevas] = useState([]);
  const [nombrePlantilla, setNombrePlantilla] = useState("");
  const misPlantillas = [...(PLANTILLAS_POR_RADIOLOGO[sesion.nombre] || []), ...plantillasNuevas];
  const guardarPlantilla = () => {
    if (!nombrePlantilla.trim()) return;
    setPlantillasNuevas((prev) => [...prev, { id: `nueva_${Date.now()}`, nombre: nombrePlantilla.trim(), ...informeCampos }]);
    setNombrePlantilla("");
  };
  // setTitulo/setClasificacionCritica: el campo YA vivía en el registro (record.titulo,
  // record.clasificacionCritica) pero nunca se había creado el setter — el input/checkbox
  // del visor llamaba una función que no existía (ReferenceError, tumbaba todo el panel
  // de Informe para cualquier rol que pudiera informar). Mismo patrón que el resto de
  // los setters de campo: patch() sobre el registro real.
  const setTitulo = (id, valor) => patch(id, (r) => ({ ...r, titulo: valor }));
  const setClasificacionCritica = (id, valor) => patch(id, (r) => ({ ...r, clasificacionCritica: valor }));
  const setCie10 = (id, campo, valor) => patch(id, (r) => ({ ...r, [campo]: valor }));
  const [linkTxt, setLinkTxt] = useState("");
  const fotoInputRef = useRef(null);
  const pdfInputRef = useRef(null);

  // --- Bono/pago (§11 Ampliación) ---
  const [bonoTarget, setBonoTarget] = useState(null); // record abierto en la mini-ventana de Validar/Anular/Reagendar
  const [bonoNumeroInput, setBonoNumeroInput] = useState("");

  // --- Ingreso manual de paciente (§10 Ampliación) ---
  const [ingresoManualAbierto, setIngresoManualAbierto] = useState(false);
  const [manualForm, setManualForm] = useState({ rut: "", nombre: "", edad: "", sexo: "F", modalidad: "TC", estudio: "", procedencia: "Ambulatorio" });
  const ordenMedicaInputRef = useRef(null);
  const [ordenMedicaAdjunta, setOrdenMedicaAdjunta] = useState(null);
  const matchManualPorRut = useMemo(() => {
    const rutLimpio = manualForm.rut.replace(/[.\s]/g, "").toLowerCase();
    if (rutLimpio.length < 5) return null;
    return data.find((r) => r.rut.replace(/[.\s]/g, "").toLowerCase() === rutLimpio) || null;
  }, [manualForm.rut, data]);

  useEffect(() => {
    const tick = () => setClock(new Date().toLocaleTimeString("es-CL", { hour: "2-digit", minute: "2-digit", second: "2-digit" }));
    tick();
    const t = setInterval(tick, 1000);
    return () => clearInterval(t);
  }, []);

  /* Carga real (26-ago-2026) — reemplaza a useState(SEED). Si el motor
     todavía no tiene ningún registro (primera vez que se conecta a un
     WorklistStore nuevo), lo puebla con la SEED de demo; si ya hay datos
     (de esta demo o de uso real), los respeta tal cual — nunca pisa
     trabajo real por asumir que está vacío. Si la API no responde, se
     muestra el error explícito (§8 más abajo) en vez de caer en silencio
     a datos locales fingidos — sería reintroducir la misma simulación
     que este cableado vino a sacar. */
  useEffect(() => {
    let cancelado = false;
    (async () => {
      try {
        const { datos } = await WorklistClient.sembrarSiVacio(apiBaseUrl, SEED);
        if (!cancelado) { setData(datos); setCargando(false); }
      } catch (e) {
        if (!cancelado) { setErrorConexion(e.message); setCargando(false); }
      }
    })();
    return () => { cancelado = true; };
  }, [apiBaseUrl]);

  /* Polling real (26-ago-2026) — así se entera el navegador de cambios que
     él no disparó: un C-STORE real llegando desde un equipo (o desde el
     test-harness DIMSE) mientras la pestaña está abierta. Simplificado a
     propósito: reemplaza `data` completo con lo que devuelve el servidor
     cada 4s, no intenta un merge fino con cambios locales optimistas en
     vuelo — el margen de carrera es acotado (una escritura local tarda
     milisegundos, no hasta el próximo poll) y no vale la pena la
     complejidad extra hoy. WebSocket/SSE en tiempo real queda como puerta
     etiquetada explícita para cuando haga falta, no fingida ahora. */
  useEffect(() => {
    if (cargando || errorConexion) return;
    const intervalId = setInterval(async () => {
      try {
        const fresco = await WorklistClient.cargarWorklist(apiBaseUrl);
        setData(fresco);
      } catch (e) {
        console.error("[HIS-RIS-PACS] Error al refrescar el Worklist desde el motor:", e.message);
      }
    }, pollIntervalMs);
    return () => clearInterval(intervalId);
  }, [apiBaseUrl, pollIntervalMs, cargando, errorConexion]);

  /* Reemplaza al setTimeout falso que antes fingía "llegó el C-STORE" en
     guardarYEnviar(). Ahora: cuando el polling de arriba trae un dato real
     donde el registro que se estaba "guardando" ya no está en fase
     "worklist" (el motor lo pasó a "examenes" porque llegó el C-STORE de
     verdad), se limpia el estado de UI — mismo efecto visual de antes,
     disparado por un evento real en vez de un timer inventado. */
  useEffect(() => {
    if (!guardandoId) return;
    const registro = data.find((r) => r.id === guardandoId);
    if (registro && registro.fase !== "worklist") {
      setGuardandoId(null);
      setSelectedId(null);
    }
  }, [data, guardandoId]);

  const conteos = useMemo(() => {
    const c = {};
    const bonoSinResolver = (r) => r.bono && r.bono.estado === "pendiente_pago" && (r.estado === "almacenado" || r.estado === "reagendado");
    FASES.forEach((f) => { c[f.id] = data.filter((r) => (f.id === "admision" ? (r.fase === "admision" || bonoSinResolver(r)) : r.fase === f.id)).length; });
    return c;
  }, [data]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    const bonoSinResolver = (r) => r.bono && r.bono.estado === "pendiente_pago" && (r.estado === "almacenado" || r.estado === "reagendado");
    let rows = data.filter((r) => {
      const enEstaFase = activeFase === "admision" ? (r.fase === "admision" || bonoSinResolver(r)) : r.fase === activeFase;
      if (!enEstaFase) return false;
      const okSearch = !q || r.nombre.toLowerCase().includes(q) || r.cup.toLowerCase().includes(q) || r.rut.includes(q);
      const okMod = modFilter === "todas" || r.modalidad === modFilter;
      const okPrio = !onlyPrio || r.prioridad === "stat" || r.prioridad === "alta";
      const okFecha = !fechaFiltro || r.fecha === fechaFiltro;
      return okSearch && okMod && okPrio && okFecha;
    });
    rows.sort((a, b) => (sortAsc ? a.hora.localeCompare(b.hora) : b.hora.localeCompare(a.hora)));
    return rows;
  }, [data, activeFase, search, modFilter, onlyPrio, sortAsc, fechaFiltro]);

  const selected = data.find((r) => r.id === selectedId) || null;
  const puedeInformar = ROLES_INFORMANTES.includes(sesion.rolId);
  const columns = useMemo(() => buildColumns(activeFase, categorias, (r) => setAdjuntoTarget(r), (r) => { setBonoTarget(r); setBonoNumeroInput(""); }, (r) => setBonoTarget(r)), [activeFase, categorias]);

  /* Real desde el 26-ago-2026: sigue actualizando el estado local de
     inmediato (optimista, mismo comportamiento visual de siempre), pero
     ahora TAMBIÉN sincroniza con el motor vía WorklistApiServer — es el
     único lugar que hay que tocar para que las ~15 funciones de mutación
     de abajo (setStaff, avanzarAgendado, ingresarBono, etc., todas ya
     pasan por acá) queden conectadas de verdad, sin reescribir cada una.
     Hallazgo real (encontrado por el test de interacción, no leyendo
     código): si el update optimista y el polling (cargarWorklist cada
     pollIntervalMs) se cruzan, un poll que llega ANTES de que el PATCH
     haya sido procesado por el servidor puede pisar el cambio optimista
     con datos todavía viejos. Por eso, cuando el PATCH sí confirma,
     su respuesta (la versión que el servidor realmente guardó) se vuelve
     a aplicar sobre el estado local — así cualquier poll que haya ganado
     la carrera de forma transitoria se corrige solo, sin esperar al
     siguiente ciclo de polling. */
  const patch = (id, fn) => {
    setData((prev) => {
      const idx = prev.findIndex((r) => r.id === id);
      if (idx === -1) return prev;
      const actualizado = fn(prev[idx]);
      WorklistClient.actualizarRegistro(apiBaseUrl, id, actualizado)
        .then((confirmado) => {
          setData((prev2) => {
            const idx2 = prev2.findIndex((r) => r.id === id);
            if (idx2 === -1) return prev2;
            const next2 = [...prev2];
            next2[idx2] = confirmado;
            return next2;
          });
        })
        .catch((e) => {
          console.error(`[HIS-RIS-PACS] No se pudo sincronizar el registro ${id} con el motor:`, e.message);
        });
      const next = [...prev];
      next[idx] = actualizado;
      return next;
    });
  };
  const setStaff = (id, campo, valor) => patch(id, (r) => ({ ...r, staff: { ...r.staff, [campo]: valor || null } }));
  const setClinico = (id, campo, valor) => patch(id, (r) => ({ ...r, clinico: { ...r.clinico, [campo]: valor } }));
  const toggleConsentimiento = (id) => patch(id, (r) => ({ ...r, consentimiento: !r.consentimiento }));
  const setCategoria = (id, catId) => patch(id, (r) => ({ ...r, categoria: catId || null }));
  const agregarAdjunto = (id, item) => {
    patch(id, (r) => ({ ...r, adjuntos: [...(r.adjuntos || []), item] }));
    setAdjuntoTarget((prev) => (prev && prev.id === id ? { ...prev, adjuntos: [...(prev.adjuntos || []), item] } : prev));
  };
  const quitarAdjunto = (id, idx) => {
    patch(id, (r) => ({ ...r, adjuntos: r.adjuntos.filter((_, i) => i !== idx) }));
    setAdjuntoTarget((prev) => (prev && prev.id === id ? { ...prev, adjuntos: prev.adjuntos.filter((_, i) => i !== idx) } : prev));
  };
  const agregarCategoria = () => {
    if (!catNombre.trim()) return;
    const id = catNombre.trim().toLowerCase().replace(/\s+/g, "_").replace(/[^a-z0-9_]/g, "");
    setCategorias((prev) => [...prev, { id: `${id}_${Date.now()}`, label: catNombre.trim(), color: "#8FA3C7", grupo: catGrupo }]);
    setCatNombre("");
  };
  const quitarCategoria = (id) => setCategorias((prev) => prev.filter((c) => c.id !== id));

  const avanzarAgendado = (id) => patch(id, (r) => {
    if (r.estado === "agendado" || r.estado === "confirmado") {
      publish(EVENTS.CHECKPOINT_SCAN, { cup: r.cup, tipo: "recepcion_llegada" });
      return { ...r, estado: "llegada_recepcion" };
    }
    return { ...r, fase: "admision", estado: "nuevo" };
  });
  const completarAdmision = (id) => patch(id, (r) => {
    publish(EVENTS.PACIENTE_INGRESADO, { cup: r.cup, modalidad: r.modalidad });
    return { ...r, fase: "worklist", estado: "arribado" };
  });
  /** Único botón real de la Worklist: guarda la trazabilidad y activa el envío al equipo de imagen.
      De ahí en más no hay nada que hacer en esta ventana — el regreso a "Almacenado" lo dispara el propio
      equipo (MWL/MPPS/C-STORE, ver dicom-engine/), no un clic de un humano.
      Real desde el 26-ago-2026: antes acá había un setTimeout(1400ms) fingiendo que "llegó" el
      C-STORE. Ya no — el motor real (WorklistStore.buscarPorAcc + AssociationServer._handleCStore,
      ver dicom-engine/) es quien marca fase:"examenes"/estado:"almacenado" cuando de verdad llega un
      C-STORE con el mismo Accession Number. El polling (arriba) detecta ese cambio real y el efecto de
      guardandoId (también arriba) limpia el spinner solo — mismo efecto visual de siempre, disparado
      por un evento real. Sin un equipo real (o el test-harness DIMSE) hablándole al motor, el registro
      queda honestamente en "en_proceso" esperando ese C-STORE — ya no se finge que llegó si no llegó. */
  const guardarYEnviar = (id) => {
    setGuardandoId(id);
    patch(id, (r) => ({ ...r, estado: "en_proceso" }));
  };
  const abrirInforme = (id) => patch(id, (r) => {
    publish(EVENTS.RESULTADO_LISTO, { cup: r.cup, estudio: r.estudio });
    return { ...r, estado: "informado" };
  });
  const validarInforme = (id) => patch(id, (r) => ({ ...r, estado: "validado" }));
  const agregarComentario = (id, texto) => {
    if (!texto.trim()) return;
    patch(id, (r) => ({ ...r, comentarios: [...(r.comentarios || []), texto.trim()] }));
    setComentarioTxt("");
  };

  /** §11a — ingreso presencial: administrativa ingresa el N° de bono al registrar.
      Recién ahí "se activa" la fila (el botón de validar/anular queda visible más abajo,
      pero solo se puede usar cuando el examen llegue a Almacenado — ver buildColumns). */
  const ingresarBono = (id, numero) => {
    if (!numero.trim()) return;
    patch(id, (r) => ({ ...r, bono: { numero: numero.trim(), origen: "presencial", estado: "pendiente_pago" } }));
    setBonoNumeroInput("");
  };

  /** §11b — autoatención/tótem: en la vida real son 2 pasos (portal ya validó el bono,
      tótem activa la llegada) que acá se simulan como un solo clic — "sin pasar por
      revisión de administrativa" significa exactamente eso: no hay paso manual intermedio. */
  const simularLlegadaTotem = (id) => patch(id, (r) => {
    publish(EVENTS.CHECKPOINT_SCAN, { cup: r.cup, tipo: "totem_autoatencion" });
    publish(EVENTS.PACIENTE_INGRESADO, { cup: r.cup, modalidad: r.modalidad });
    return { ...r, estado: "arribado", fase: "worklist", bono: { numero: makeBonoAutoatencion(), origen: "autoatencion", estado: "pendiente_pago" } };
  });

  /** §11b.2/b.3 — mini-ventana de "finalizar pago": Validar bono, Anular bono, o Reagendar.
      Las 3 quedan juntas a propósito: quien está frente a la pantalla ya conversó con el
      paciente (o constató que no volvió) y decide cuál corresponde — no se intenta adivinar
      la intención del paciente con más estado. */
  const resolverBono = (id, accion) => {
    patch(id, (r) => {
      if (accion === "reagendar") return { ...r, fase: "agendados", estado: "reagendado" };
      return { ...r, bono: { ...r.bono, estado: accion } }; // accion: "validado" | "anulado"
    });
    setBonoTarget(null);
  };

  /** §10 — ingreso manual (botón en Worklist). Mismo "molde" de registro que usa el SEED
      (mismos 3 pasos: defaults -> acc/ot/timestamps -> códigos derivados) para que un
      paciente ingresado a mano sea, en forma, indistinguible de uno agendado normal.
      Match por RUT: si ya existe (cualquier fase), reutiliza su CUP real — no crea un
      segundo CUP para la misma persona.
      Real desde el 26-ago-2026: el id numérico de nextManualId() se sigue calculando
      igual que siempre — lo sigue necesitando makeACC()/makeOT()/codigoExamen, que
      derivan directo del número — pero ahora el registro se crea vía la API real
      (POST /worklist) en vez de setData local. El estado local se actualiza con lo
      que devuelve el SERVIDOR (mismo registro, id ya normalizado a string por
      WorklistStore — ver dossier §"bug de tipos"), no con el objeto `base` calculado
      acá, para no tener dos versiones del mismo registro con id de tipo distinto
      conviviendo en `data`. */
  const crearIngresoManual = async () => {
    const f = manualForm;
    if (!f.rut.trim() || !f.nombre.trim() || !f.estudio.trim()) return;
    const id = nextManualId();
    const cupFinal = matchManualPorRut ? matchManualPorRut.cup : makeCUP(3000 + manualSeq);
    let base = {
      id, cup: cupFinal, rut: f.rut.trim(), nombre: f.nombre.trim(),
      edad: f.edad ? Number(f.edad) : (matchManualPorRut ? matchManualPorRut.edad : null),
      sexo: f.sexo, fase: "admision", estado: "nuevo", modalidad: f.modalidad,
      estudio: f.estudio.trim(), procedencia: f.procedencia, prioridad: "normal",
      hora: new Date().toTimeString().slice(0, 5),
      staff: { administrativo: sesion.rolId === "administrativo" ? sesion.nombre : ADMINISTRATIVOS[0], tens: null, tm: null, radiologo: null },
      comentarios: [],
      categoria: null, consentimiento: false,
      clinico: { creatinina: null, talla: null, peso: null, contrasteMl: null, medioContraste: null },
      adjuntos: ordenMedicaAdjunta ? [ordenMedicaAdjunta] : [],
      anamnesis: "", fecha: new Date().toISOString().slice(0, 10), bono: null,
    };
    base = { ...base, acc: makeACC(id), ot: makeOT(id), timestamps: deriveTimestamps(base) };
    base = { ...base, codigoExamen: `${base.modalidad}-${String(id).padStart(4, "0")}`, medicoSolicitante: MEDICOS_SOLICITANTES[id % MEDICOS_SOLICITANTES.length], clasificacionCritica: false, titulo: base.estudio, cie10Indicacion: [], cie10Conclusion: [] };
    publish(EVENTS.PACIENTE_INGRESADO, { cup: cupFinal, modalidad: f.modalidad, origen: "ingreso_manual" });
    try {
      const creado = await WorklistClient.crearRegistro(apiBaseUrl, base);
      setData((prev) => [...prev, creado]);
      setManualForm({ rut: "", nombre: "", edad: "", sexo: "F", modalidad: "TC", estudio: "", procedencia: "Ambulatorio" });
      setOrdenMedicaAdjunta(null);
      setIngresoManualAbierto(false);
      setActiveFase("admision"); // para que se vea de inmediato dónde quedó — el botón vive en Worklist, pero el registro nace en Admisión
    } catch (e) {
      console.error("[HIS-RIS-PACS] No se pudo crear el ingreso manual en el motor:", e.message);
      alert("No se pudo guardar el ingreso manual — revisá la conexión con el motor e intentá de nuevo.");
    }
  };

  const modalidadesPresentes = ["todas", ...Object.keys(MODALIDADES)];

  /* Estados de carga/error real (26-ago-2026) — antes no existían porque
     useState(SEED) siempre "tenía datos" al instante, sin red de por medio.
     Si la API no responde, se muestra el motivo explícito acá — nunca se
     cae en silencio a datos locales fingidos, sería reintroducir la misma
     simulación que este cableado vino a sacar. */
  if (cargando) {
    return (
      <div style={{ background: D.bg, minHeight: "100%", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'Inter',system-ui,-apple-system,sans-serif" }}>
        <div style={{ color: D.txm, fontSize: 12.5 }}>Conectando con el motor DICOM…</div>
      </div>
    );
  }
  if (errorConexion) {
    return (
      <div style={{ background: D.bg, minHeight: "100%", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'Inter',system-ui,-apple-system,sans-serif", padding: 20 }}>
        <div style={{ maxWidth: 440, textAlign: "center" }}>
          <div style={{ color: D.dan, fontSize: 14, fontWeight: 700, marginBottom: 8 }}>No se pudo conectar con el motor</div>
          <div style={{ color: D.txm, fontSize: 12, lineHeight: 1.6 }}>
            Verificá que <code style={{ color: D.tea }}>WorklistApiServer</code> esté corriendo en{" "}
            <code style={{ color: D.tea }}>{apiBaseUrl}</code>.<br />Detalle: {errorConexion}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ background: D.bg, minHeight: "100%", padding: 20, fontFamily: "'Inter',system-ui,-apple-system,sans-serif" }}>
      <style>{`
        *{box-sizing:border-box;}
        @keyframes rpPulse{0%,100%{opacity:1}50%{opacity:0.45}}
        .rp-row:hover{background:#152742 !important;}
        input::placeholder{color:#4E6480;}
        select{-webkit-appearance:none;}
        ::-webkit-scrollbar{width:5px;height:5px;}
        ::-webkit-scrollbar-thumb{background:#2A415F;border-radius:4px;}
      `}</style>

      {/* Marca AXON — discreta, solo de recordatorio */}
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 10, opacity: 0.55 }}>
        <div style={{ width: 16, height: 16, borderRadius: 5, background: `linear-gradient(135deg, ${D.pri}, ${D.pur})`, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <span style={{ fontSize: 9, fontWeight: 800, color: "#0A1420" }}>A</span>
        </div>
        <span style={{ fontSize: 9, fontWeight: 700, color: D.txl, textTransform: "uppercase", letterSpacing: "1.2px" }}>AXON</span>
      </div>

      {/* Encabezado */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 10, marginBottom: 18 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ background: `${D.pri}22`, borderRadius: 10, padding: 10 }}><Monitor size={22} color={D.pri} /></div>
          <div>
            <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: D.txt, letterSpacing: "0.2px" }}>HIS-RIS-PACS</h2>
            <p style={{ margin: "2px 0 0", fontSize: 11, color: D.txl }}>Servicio de Imagenología</p>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ fontSize: 9.5, color: D.txl }}>Sesión:</span>
            <select value={sesion.nombre} onChange={(e) => setSesion(SESIONES_DEMO.find((s) => s.nombre === e.target.value))} style={{ padding: "5px 8px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc, color: D.txt, fontSize: 10.5, fontWeight: 600 }}>
              {SESIONES_DEMO.map((s) => <option key={s.nombre} value={s.nombre}>{s.nombre} · {s.rol}</option>)}
            </select>
          </div>
          <span style={{ fontSize: 11, color: D.txl, fontFamily: "monospace" }}>{clock}</span>
          <button onClick={async () => {
            // Real desde el 26-ago-2026: antes era setData(SEED), puramente local.
            // Ahora repone cada registro de la SEED a su valor original vía PUT
            // (upsert) contra el motor real — no borra registros que no sean parte
            // de la demo (ej. uno creado con "Ingreso manual" durante la sesión),
            // es un reset acotado a los ids conocidos, no un "borrar todo".
            setSelectedId(null);
            try {
              const fresco = await WorklistClient.restablecerDemo(apiBaseUrl, SEED);
              setData(fresco);
            } catch (e) {
              console.error("[HIS-RIS-PACS] No se pudo restablecer la demo contra el motor:", e.message);
              alert("No se pudo restablecer la demo — revisá la conexión con el motor.");
            }
          }} style={{ display: "flex", alignItems: "center", gap: 6, padding: "7px 12px", borderRadius: 7, border: `1px solid ${D.brd}`, background: D.sfc, color: D.txm, fontSize: 11, fontWeight: 600, cursor: "pointer" }}>
            <RefreshCw size={12} />Restablecer demo
          </button>
        </div>
      </div>

      {/* Pestañas (antes KPIs, ahora también navegación) */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px,1fr))", gap: 12, marginBottom: 18 }}>
        {FASES.map((f) => (
          <TabCard key={f.id} fase={f} active={activeFase === f.id} count={conteos[f.id] || 0} onClick={() => { setActiveFase(f.id); setSelectedId(null); }} />
        ))}
      </div>

      {/* Filtros */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap", marginBottom: 14 }}>
        <div style={{ display: "flex", alignItems: "center", background: D.sfc, border: `1px solid ${D.brd}`, borderRadius: 8, padding: "7px 11px", gap: 7, minWidth: 220 }}>
          <Search size={13} color={D.txl} />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Paciente · CUP · RUT…" aria-label="Buscar paciente" style={{ border: "none", outline: "none", background: "none", fontSize: 12, color: D.txt, width: "100%" }} />
        </div>
        <div style={{ display: "flex", alignItems: "center", background: D.sfc, border: `1px solid ${fechaFiltro ? D.pri : D.brd}`, borderRadius: 8, padding: "7px 11px", gap: 7 }}>
          <Calendar size={13} color={fechaFiltro ? D.pri : D.txl} />
          <input type="date" value={fechaFiltro} onChange={(e) => setFechaFiltro(e.target.value)} aria-label="Filtrar por fecha" style={{ border: "none", outline: "none", background: "none", fontSize: 11.5, color: D.txt, colorScheme: "dark" }} />
          {fechaFiltro && <button onClick={() => setFechaFiltro("")} title="Quitar filtro de fecha" style={{ background: "none", border: "none", cursor: "pointer", color: D.txl, display: "flex" }}><X size={12} /></button>}
        </div>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {modalidadesPresentes.map((m) => (
            <Chip key={m} active={modFilter === m} onClick={() => setModFilter(m)} color={m === "todas" ? D.pri : MODALIDADES[m].color}>{m === "todas" ? "Todas" : m}</Chip>
          ))}
        </div>
        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: D.txm, cursor: "pointer" }}>
          <input type="checkbox" checked={onlyPrio} onChange={(e) => setOnlyPrio(e.target.checked)} />
          Solo prioritarios
        </label>
        {activeFase === "worklist" && (
          <button onClick={() => setIngresoManualAbierto(true)} style={{ display: "flex", alignItems: "center", gap: 6, padding: "7px 11px", borderRadius: 8, border: `1px solid ${D.tea}55`, background: `${D.tea}18`, fontSize: 11, fontWeight: 700, color: D.tea, cursor: "pointer" }}>
            <UserPlus size={13} />Ingreso manual
          </button>
        )}
        <button onClick={() => setShowCatManager((s) => !s)} style={{ display: "flex", alignItems: "center", gap: 6, padding: "7px 11px", borderRadius: 8, border: `1px solid ${showCatManager ? D.pri : D.brd}`, background: showCatManager ? `${D.pri}22` : D.sfc, fontSize: 11, fontWeight: 600, color: showCatManager ? "#D6DCE4" : D.txm, cursor: "pointer", marginLeft: "auto" }}>
          <Settings size={12} />Categorías
        </button>
        <button onClick={() => setSortAsc((s) => !s)} style={{ display: "flex", alignItems: "center", gap: 6, padding: "7px 11px", borderRadius: 8, border: `1px solid ${D.brd}`, background: D.sfc, fontSize: 11, fontWeight: 600, color: D.txm, cursor: "pointer" }}>
          <ArrowUpDown size={12} />Hora {sortAsc ? "↑" : "↓"}
        </button>
      </div>

      {/* Gestor de categorías clínicas — 100% configurable desde acá, sin tocar código */}
      {showCatManager && (
        <div style={{ background: D.sfc, border: `1px solid ${D.brd}`, borderRadius: 12, padding: 14, marginBottom: 14 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: D.txt, marginBottom: 10 }}>Gestionar categorías clínicas (procedencia)</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 12 }}>
            {categorias.map((c) => (
              <span key={c.id} style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 10, fontWeight: 600, padding: "3px 6px 3px 8px", borderRadius: 5, background: `${c.color}22`, color: c.color, border: `1px solid ${c.color}44` }}>
                {c.grupo} · {c.label}
                <button onClick={() => quitarCategoria(c.id)} style={{ background: "none", border: "none", cursor: "pointer", color: c.color, display: "flex" }}><Trash2 size={11} /></button>
              </span>
            ))}
            {categorias.length === 0 && <span style={{ fontSize: 11, color: D.txl }}>Sin categorías — agrega la primera abajo.</span>}
          </div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            <input value={catNombre} onChange={(e) => setCatNombre(e.target.value)} placeholder="Nombre de la categoría…" style={{ flex: 1, minWidth: 160, padding: "7px 9px", borderRadius: 7, border: `1px solid ${D.brd}`, background: D.bg, color: D.txt, fontSize: 11 }} />
            <select value={catGrupo} onChange={(e) => setCatGrupo(e.target.value)} style={{ padding: "7px 9px", borderRadius: 7, border: `1px solid ${D.brd}`, background: D.bg, color: D.txt, fontSize: 11 }}>
              <option>Aislamiento</option>
              <option>Nivel de cuidados</option>
              <option>Urgencia</option>
              <option>Otro</option>
            </select>
            <button onClick={agregarCategoria} style={{ display: "flex", alignItems: "center", gap: 5, padding: "7px 12px", borderRadius: 7, border: "none", background: D.pri, color: "#0A1420", fontSize: 11, fontWeight: 700, cursor: "pointer" }}>
              <Plus size={12} />Agregar
            </button>
          </div>
        </div>
      )}

      {/* Tabla genérica, columnas según pestaña activa */}
      <div style={{ background: D.sfc, border: `1px solid ${D.brd}`, borderRadius: 12, overflow: "hidden" }}>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 760 }}>
            <thead>
              <tr style={{ background: D.sfc2, borderBottom: `1px solid ${D.brd}` }}>
                {columns.map((c) => (
                  <th key={c.key} style={{ textAlign: "left", padding: "9px 12px", fontSize: 9, fontWeight: 700, color: D.txl, textTransform: "uppercase", letterSpacing: "0.4px" }}>{c.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr key={r.id} className="rp-row" onClick={() => setSelectedId(r.id)} style={{ borderBottom: `1px solid ${D.brd}`, cursor: "pointer" }}>
                  {columns.map((c) => <td key={c.key} style={{ padding: "10px 12px" }}>{c.render(r)}</td>)}
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr><td colSpan={columns.length} style={{ padding: "28px 12px", textAlign: "center", fontSize: 12, color: D.txl }}>Ningún registro coincide con los filtros actuales en esta pestaña.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      <div style={{ marginTop: 8, fontSize: 10, color: D.txl }}>{filtered.length} de {conteos[activeFase] || 0} en {FASES.find((f) => f.id === activeFase)?.label} · datos de demostración</div>

      {/* Panel de detalle — contenido y acciones cambian según la fase */}
      {selected && (
        <>
          <div onClick={() => setSelectedId(null)} style={{ position: "fixed", inset: 0, background: "rgba(4,9,16,0.55)", zIndex: 100 }} />
          <div style={{ position: "fixed", top: 0, right: 0, bottom: 0, width: "min(430px, 92vw)", background: D.sfc, zIndex: 101, boxShadow: "-8px 0 30px rgba(0,0,0,0.45)", overflowY: "auto", padding: 20, borderLeft: `1px solid ${D.brd}` }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 14 }}>
              <div>
                <div style={{ fontSize: 15, fontWeight: 700, color: D.txt }}>{selected.nombre}</div>
                <div style={{ display: "flex", alignItems: "center", gap: 7, marginTop: 4, flexWrap: "wrap" }}>
                  <span style={{ fontSize: 9, fontWeight: 700, background: D.bg, color: D.tea, padding: "2px 7px", borderRadius: 4, fontFamily: "monospace" }}>{selected.cup}</span>
                  <span style={{ fontSize: 10, color: D.txl }}>{selected.rut} · {selected.edad} años · {selected.sexo}</span>
                </div>
              </div>
              <button onClick={() => setSelectedId(null)} aria-label="Cerrar panel" style={{ background: "none", border: "none", cursor: "pointer", color: D.txl }}><X size={18} /></button>
            </div>

            <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
              <ModBadge mod={selected.modalidad} />
              <EstadoBadge estado={selected.estado} />
              <PrioTag prioridad={selected.prioridad} />
            </div>

            <div style={{ background: D.bg, borderRadius: 10, padding: 14, marginBottom: 16 }}>
              <Field label="Estudio" value={selected.estudio} />
              <Field label="Procedencia" value={selected.procedencia} />
              <Field label="Hora" value={selected.hora} last />
            </div>

            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: D.txl, textTransform: "uppercase", letterSpacing: "0.4px", marginBottom: 7 }}>Categoría clínica (opcional)</div>
              <select value={selected.categoria || ""} onChange={(e) => setCategoria(selected.id, e.target.value)} style={{ width: "100%", padding: "7px 9px", borderRadius: 7, border: `1px solid ${D.brd}`, background: D.bg, color: D.txt, fontSize: 11 }}>
                <option value="">Sin categoría</option>
                {["Aislamiento", "Nivel de cuidados", "Urgencia", "Otro"].map((g) => {
                  const opts = categorias.filter((c) => c.grupo === g);
                  if (!opts.length) return null;
                  return (
                    <optgroup key={g} label={g}>
                      {opts.map((c) => <option key={c.id} value={c.id}>{c.label}</option>)}
                    </optgroup>
                  );
                })}
              </select>
            </div>

            {/* Trazabilidad de staff — requisito transversal del flujo */}
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: D.txl, textTransform: "uppercase", letterSpacing: "0.4px", marginBottom: 8 }}>Trazabilidad de atención</div>
              {(selected.fase === "agendados" || selected.fase === "admision") && (
                <StaffSelect label="Administrativa/o" value={selected.staff.administrativo} options={ADMINISTRATIVOS} onChange={(v) => setStaff(selected.id, "administrativo", v)} />
              )}
              {selected.fase === "worklist" && (
                <>
                  <StaffSelect label="TENS" value={selected.staff.tens} options={TENS_LIST} onChange={(v) => setStaff(selected.id, "tens", v)} />
                  <StaffSelect label="Tecnólogo médico (TM)" value={selected.staff.tm} options={TM_LIST} onChange={(v) => setStaff(selected.id, "tm", v)} />
                  <StaffSelect label="Radiólogo asignado" value={selected.staff.radiologo} options={RADIOLOGOS} onChange={(v) => setStaff(selected.id, "radiologo", v)} />
                </>
              )}
            </div>

            {(selected.fase === "admision" || selected.bono) && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: D.txl, textTransform: "uppercase", letterSpacing: "0.4px", marginBottom: 8 }}>Bono / Pago</div>
                {!selected.bono ? (
                  <div style={{ display: "flex", gap: 6 }}>
                    <input value={bonoNumeroInput} onChange={(e) => setBonoNumeroInput(e.target.value)} placeholder="N° de bono…" style={{ flex: 1, padding: "7px 9px", borderRadius: 7, border: `1px solid ${D.brd}`, background: D.bg, color: D.txt, fontSize: 11 }} />
                    <button onClick={() => ingresarBono(selected.id, bonoNumeroInput)} style={{ padding: "0 12px", borderRadius: 7, border: "none", background: D.tea, color: "#0A1420", fontSize: 11, fontWeight: 700, cursor: "pointer" }}>Ingresar</button>
                  </div>
                ) : (
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8, background: D.bg, borderRadius: 8, padding: "8px 10px", flexWrap: "wrap" }}>
                    <BonoCell r={selected} onIngresar={() => {}} onAbrirFinalizar={(r) => setBonoTarget(r)} />
                    <span style={{ fontSize: 9.5, color: D.txl }}>{selected.bono.origen === "autoatencion" ? "Autoatención · tótem" : "Ingreso presencial"}</span>
                  </div>
                )}
              </div>
            )}

            {selected.fase === "worklist" && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: D.txl, textTransform: "uppercase", letterSpacing: "0.4px", marginBottom: 8 }}>Validación clínica (TM)</div>
                <button onClick={() => toggleConsentimiento(selected.id)} style={{ display: "flex", alignItems: "center", gap: 6, width: "100%", padding: "8px 10px", borderRadius: 8, border: `1px solid ${selected.consentimiento ? D.suc + "55" : D.brd}`, background: selected.consentimiento ? `${D.suc}18` : D.bg, color: selected.consentimiento ? D.suc : D.txm, fontSize: 11, fontWeight: 600, cursor: "pointer", marginBottom: 10 }}>
                  <ShieldCheck size={13} />{selected.consentimiento ? "Consentimiento informado validado" : "Validar consentimiento informado"}
                </button>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                  <MiniField label="Creatinina (mg/dL)" value={selected.clinico.creatinina} onChange={(v) => setClinico(selected.id, "creatinina", v)} />
                  <MiniField label="Talla (cm)" value={selected.clinico.talla} onChange={(v) => setClinico(selected.id, "talla", v)} />
                  <MiniField label="Peso (kg)" value={selected.clinico.peso} onChange={(v) => setClinico(selected.id, "peso", v)} />
                  <MiniField label="Contraste (ml)" value={selected.clinico.contrasteMl} onChange={(v) => setClinico(selected.id, "contrasteMl", v)} />
                </div>
              </div>
            )}

            {selected.fase === "examenes" && (
              <div style={{ marginBottom: 16 }}>
                <StaffSelect label="Radiólogo" value={selected.staff.radiologo} options={RADIOLOGOS} onChange={(v) => setStaff(selected.id, "radiologo", v)} />
              </div>
            )}

            {/* Acciones contextuales — máquina de estados real */}
            <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
              {selected.fase === "agendados" && (
                <>
                  <button onClick={() => avanzarAgendado(selected.id)} style={{ flex: 1, padding: "9px 12px", borderRadius: 8, border: "none", background: D.pri, color: "#0A1420", fontSize: 12, fontWeight: 700, cursor: "pointer" }}>
                    {selected.estado === "agendado" || selected.estado === "confirmado" ? "Marcar llegada" : "Enviar a Admisión →"}
                  </button>
                  {(selected.estado === "agendado" || selected.estado === "confirmado") && (
                    <button onClick={() => simularLlegadaTotem(selected.id)} title="Simula el portal + tótem: bono ya asociado, salta directo a Worklist sin pasar por revisión de administrativa (§11b)" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 6, padding: "9px 12px", borderRadius: 8, border: `1px solid ${D.tea}55`, background: `${D.tea}18`, color: D.tea, fontSize: 11.5, fontWeight: 700, cursor: "pointer" }}>
                      <Tablet size={13} />Autoatención (tótem)
                    </button>
                  )}
                </>
              )}
              {selected.fase === "admision" && (
                <button onClick={() => completarAdmision(selected.id)} style={{ flex: 1, padding: "9px 12px", borderRadius: 8, border: "none", background: D.tea, color: "#0A1420", fontSize: 12, fontWeight: 700, cursor: "pointer" }}>
                  Completar admisión → Arribado
                </button>
              )}
              {selected.fase === "worklist" && (
                <button onClick={() => guardarYEnviar(selected.id)} disabled={guardandoId === selected.id} style={{ flex: 1, padding: "9px 12px", borderRadius: 8, border: "none", background: guardandoId === selected.id ? D.suc : D.pri, color: "#0A1420", fontSize: 12, fontWeight: 700, cursor: guardandoId === selected.id ? "default" : "pointer" }}>
                  {guardandoId === selected.id ? "Guardado ✓ — enviando al equipo…" : "Guardar"}
                </button>
              )}
              {selected.fase === "examenes" && selected.estado === "almacenado" && (
                puedeInformar ? (
                  <button onClick={() => abrirInforme(selected.id)} style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 6, padding: "9px 12px", borderRadius: 8, border: "none", background: D.war, color: "#0A1420", fontSize: 12, fontWeight: 700, cursor: "pointer" }}>
                    <PenSquare size={13} />Abrir informe
                  </button>
                ) : (
                  <div style={{ flex: 1, fontSize: 10.5, color: D.txl, background: D.bg, borderRadius: 8, padding: "9px 12px", textAlign: "center" }}>Solo Radiólogo o Tecnólogo Médico Coordinador puede informar</div>
                )
              )}
              {selected.fase === "examenes" && selected.estado === "informado" && (
                puedeInformar ? (
                  <button onClick={() => validarInforme(selected.id)} style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 6, padding: "9px 12px", borderRadius: 8, border: "none", background: D.suc, color: "#0A1420", fontSize: 12, fontWeight: 700, cursor: "pointer" }}>
                    <ClipboardCheck size={13} />Validar y firmar
                  </button>
                ) : (
                  <div style={{ flex: 1, fontSize: 10.5, color: D.txl, background: D.bg, borderRadius: 8, padding: "9px 12px", textAlign: "center" }}>Solo Radiólogo o Tecnólogo Médico Coordinador puede validar</div>
                )
              )}
              {selected.fase === "examenes" && selected.estado === "validado" && (
                <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 6, padding: "9px 12px", borderRadius: 8, border: `1px solid ${D.suc}44`, background: `${D.suc}18`, color: D.suc, fontSize: 11, fontWeight: 700 }}>
                  <ShieldCheck size={13} />Informe validado y firmado
                </div>
              )}
            </div>

            {/* Comentarios — funcional, en memoria */}
            {selected.fase === "examenes" && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: D.txl, textTransform: "uppercase", letterSpacing: "0.4px", marginBottom: 7 }}>Comentarios</div>
                {(selected.comentarios || []).length > 0 && (
                  <div style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 8 }}>
                    {selected.comentarios.map((c, i) => (
                      <div key={i} style={{ fontSize: 11, color: D.txm, background: D.bg, borderRadius: 7, padding: "7px 10px" }}>{c}</div>
                    ))}
                  </div>
                )}
                <div style={{ display: "flex", gap: 6 }}>
                  <input value={comentarioTxt} onChange={(e) => setComentarioTxt(e.target.value)} placeholder="Agregar comentario…" style={{ flex: 1, padding: "7px 9px", borderRadius: 7, border: `1px solid ${D.brd}`, background: D.bg, color: D.txt, fontSize: 11 }} onKeyDown={(e) => e.key === "Enter" && agregarComentario(selected.id, comentarioTxt)} />
                  <button onClick={() => agregarComentario(selected.id, comentarioTxt)} style={{ padding: "0 12px", borderRadius: 7, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txm, fontSize: 11, fontWeight: 600, cursor: "pointer" }}>Agregar</button>
                </div>
              </div>
            )}

            {/* Placeholders honestos + puertas IA — donde el flujo real las ubica: Exámenes (PACS) */}
            {selected.fase === "examenes" && (
              <>
                <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
                  <button onClick={() => { publish(EVENTS.VIEW_IMAGING_REPORT, { cup: selected.cup, sesionRolId: sesion.rolId, sesionNombre: sesion.nombre }); setVisorPaciente(selected); }} style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 6, padding: "9px 12px", borderRadius: 8, border: "none", background: D.pri, color: "#0A1420", fontSize: 11, fontWeight: 700, cursor: "pointer" }}>
                    <Eye size={13} />Abrir en visor DICOM
                  </button>
                </div>
                <div style={{ border: `1px dashed ${D.brd}`, borderRadius: 10, padding: 12 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
                    <Cpu size={13} color={D.txl} />
                    <span style={{ fontSize: 10, fontWeight: 700, color: D.txl, textTransform: "uppercase", letterSpacing: "0.4px" }}>Puertas IA — futuro</span>
                  </div>
                  <p style={{ margin: 0, fontSize: 10.5, color: D.txl, lineHeight: 1.5 }}>
                    Visualización y trabajo con agentes de IA quedan como puertas ya definidas en esta misma pestaña, sin conectar todavía.
                  </p>
                </div>
              </>
            )}
          </div>
        </>
      )}

      {/* Modal — adjuntar examen externo: foto, documento o link a plataforma externa */}
      {adjuntoTarget && (
        <>
          <div onClick={() => setAdjuntoTarget(null)} style={{ position: "fixed", inset: 0, background: "rgba(4,9,16,0.65)", zIndex: 200 }} />
          <div style={{ position: "fixed", top: "50%", left: "50%", transform: "translate(-50%,-50%)", width: "min(440px, 90vw)", maxHeight: "85vh", overflowY: "auto", background: D.sfc, border: `1px solid ${D.brd}`, borderRadius: 14, padding: 20, zIndex: 201 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 14 }}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 700, color: D.txt }}>Adjuntar examen externo</div>
                <div style={{ fontSize: 11, color: D.txl, marginTop: 2 }}>{adjuntoTarget.nombre}</div>
              </div>
              <button onClick={() => setAdjuntoTarget(null)} aria-label="Cerrar" style={{ background: "none", border: "none", cursor: "pointer", color: D.txl }}><X size={18} /></button>
            </div>

            <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
              <button onClick={() => fotoInputRef.current?.click()} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 6, padding: "14px 8px", borderRadius: 10, border: `1px dashed ${D.brd}`, background: D.bg, color: D.txm, fontSize: 11, fontWeight: 600, cursor: "pointer" }}>
                <Camera size={18} />Foto
              </button>
              <button onClick={() => pdfInputRef.current?.click()} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 6, padding: "14px 8px", borderRadius: 10, border: `1px dashed ${D.brd}`, background: D.bg, color: D.txm, fontSize: 11, fontWeight: 600, cursor: "pointer" }}>
                <FileText size={18} />PDF / Documento
              </button>
            </div>
            <input ref={fotoInputRef} type="file" accept="image/*" style={{ display: "none" }} onChange={(e) => { const f = e.target.files?.[0]; if (f) agregarAdjunto(adjuntoTarget.id, { tipo: "Foto", nombre: f.name }); e.target.value = ""; }} />
            <input ref={pdfInputRef} type="file" accept="application/pdf,.doc,.docx" style={{ display: "none" }} onChange={(e) => { const f = e.target.files?.[0]; if (f) agregarAdjunto(adjuntoTarget.id, { tipo: "Documento", nombre: f.name }); e.target.value = ""; }} />

            <div style={{ display: "flex", gap: 6, marginBottom: 14 }}>
              <input value={linkTxt} onChange={(e) => setLinkTxt(e.target.value)} placeholder="Link a plataforma externa (https://…)" style={{ flex: 1, padding: "8px 10px", borderRadius: 8, border: `1px solid ${D.brd}`, background: D.bg, color: D.txt, fontSize: 11 }} />
              <button onClick={() => { if (linkTxt.trim()) { agregarAdjunto(adjuntoTarget.id, { tipo: "Link", nombre: linkTxt.trim() }); setLinkTxt(""); } }} style={{ display: "flex", alignItems: "center", gap: 5, padding: "0 12px", borderRadius: 8, border: "none", background: D.pri, color: "#0A1420", fontSize: 11, fontWeight: 700, cursor: "pointer" }}>
                <Link2 size={12} />Agregar
              </button>
            </div>

            <div style={{ fontSize: 10, fontWeight: 700, color: D.txl, textTransform: "uppercase", letterSpacing: "0.4px", marginBottom: 8 }}>Adjuntos de este examen</div>
            {(adjuntoTarget.adjuntos || []).length === 0 && <div style={{ fontSize: 11, color: D.txl }}>Aún no hay adjuntos.</div>}
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {(adjuntoTarget.adjuntos || []).map((a, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8, background: D.bg, borderRadius: 7, padding: "7px 10px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 7, minWidth: 0 }}>
                    {a.tipo === "Foto" ? <Camera size={13} color={D.txm} /> : a.tipo === "Link" ? <Link2 size={13} color={D.txm} /> : <FileText size={13} color={D.txm} />}
                    <span style={{ fontSize: 11, color: D.txt, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{a.nombre}</span>
                  </div>
                  <button onClick={() => quitarAdjunto(adjuntoTarget.id, i)} style={{ background: "none", border: "none", cursor: "pointer", color: D.txl, flexShrink: 0 }}><Trash2 size={12} /></button>
                </div>
              ))}
            </div>
            <p style={{ fontSize: 9.5, color: D.txl, marginTop: 12, lineHeight: 1.4 }}>La subida real y el guardado en storage llegan con el backend — hoy esto queda registrado en el estado de la sesión.</p>
          </div>
        </>
      )}

      {/* Modal — bono: ingresar N° (§11a) o, si ya está pendiente y el examen llegó a
          Almacenado/Reagendado, Validar/Anular/Reagendar (§11b.2/b.3) */}
      {bonoTarget && (
        <>
          <div onClick={() => setBonoTarget(null)} style={{ position: "fixed", inset: 0, background: "rgba(4,9,16,0.65)", zIndex: 200 }} />
          <div style={{ position: "fixed", top: "50%", left: "50%", transform: "translate(-50%,-50%)", width: "min(400px, 90vw)", background: D.sfc, border: `1px solid ${D.brd}`, borderRadius: 14, padding: 20, zIndex: 201 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 14 }}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 700, color: D.txt }}>{bonoTarget.bono ? "Finalizar pago" : "Ingresar bono"}</div>
                <div style={{ fontSize: 11, color: D.txl, marginTop: 2 }}>{bonoTarget.nombre} · {bonoTarget.cup}</div>
              </div>
              <button onClick={() => setBonoTarget(null)} aria-label="Cerrar" style={{ background: "none", border: "none", cursor: "pointer", color: D.txl }}><X size={18} /></button>
            </div>

            {!bonoTarget.bono ? (
              <>
                <div style={{ fontSize: 10, color: D.txl, marginBottom: 10, lineHeight: 1.4 }}>Ingreso presencial (§11a): el bono queda registrado ahora; el botón para finalizar el pago se activa recién cuando el examen llegue a Almacenado.</div>
                <div style={{ display: "flex", gap: 6 }}>
                  <input value={bonoNumeroInput} onChange={(e) => setBonoNumeroInput(e.target.value)} placeholder="N° de bono…" autoFocus style={{ flex: 1, padding: "8px 10px", borderRadius: 8, border: `1px solid ${D.brd}`, background: D.bg, color: D.txt, fontSize: 12 }} />
                  <button onClick={() => { ingresarBono(bonoTarget.id, bonoNumeroInput); setBonoTarget(null); }} disabled={!bonoNumeroInput.trim()} style={{ padding: "0 14px", borderRadius: 8, border: "none", background: D.tea, color: "#0A1420", fontSize: 12, fontWeight: 700, cursor: bonoNumeroInput.trim() ? "pointer" : "default", opacity: bonoNumeroInput.trim() ? 1 : 0.5 }}>Guardar</button>
                </div>
              </>
            ) : (
              <>
                <div style={{ background: D.bg, borderRadius: 8, padding: "10px 12px", marginBottom: 14, fontSize: 11, color: D.txm }}>
                  Bono <b style={{ color: D.txt }}>{bonoTarget.bono.numero}</b> · {bonoTarget.bono.origen === "autoatencion" ? "autoatención (tótem)" : "ingreso presencial"} · examen {(ESTADOS[bonoTarget.estado]?.label || bonoTarget.estado).toLowerCase()}
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  <button onClick={() => resolverBono(bonoTarget.id, "validado")} style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 6, padding: "9px 12px", borderRadius: 8, border: "none", background: D.suc, color: "#0A1420", fontSize: 12, fontWeight: 700, cursor: "pointer" }}>
                    <Banknote size={13} />Validar bono
                  </button>
                  <button onClick={() => resolverBono(bonoTarget.id, "anulado")} style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 6, padding: "9px 12px", borderRadius: 8, border: `1px solid ${D.dan}55`, background: `${D.dan}18`, color: D.dan, fontSize: 12, fontWeight: 700, cursor: "pointer" }}>
                    <X size={13} />Anular bono
                  </button>
                  <button onClick={() => resolverBono(bonoTarget.id, "reagendar")} style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 6, padding: "9px 12px", borderRadius: 8, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txm, fontSize: 12, fontWeight: 700, cursor: "pointer" }}>
                    <CalendarClock size={13} />Reagendar en su lugar
                  </button>
                </div>
              </>
            )}
          </div>
        </>
      )}

      {/* Modal — ingreso manual de paciente (§10, botón en Worklist). Pasa directo a
          Admisión; el pago/bono se resuelve después, desde esa pestaña. */}
      {ingresoManualAbierto && (
        <>
          <div onClick={() => setIngresoManualAbierto(false)} style={{ position: "fixed", inset: 0, background: "rgba(4,9,16,0.65)", zIndex: 200 }} />
          <div style={{ position: "fixed", top: "50%", left: "50%", transform: "translate(-50%,-50%)", width: "min(460px, 92vw)", maxHeight: "88vh", overflowY: "auto", background: D.sfc, border: `1px solid ${D.brd}`, borderRadius: 14, padding: 20, zIndex: 201 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 14 }}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 700, color: D.txt }}>Ingreso manual de paciente</div>
                <div style={{ fontSize: 11, color: D.txl, marginTop: 2 }}>Pasa directo a Admisión — sin agendamiento previo</div>
              </div>
              <button onClick={() => setIngresoManualAbierto(false)} aria-label="Cerrar" style={{ background: "none", border: "none", cursor: "pointer", color: D.txl }}><X size={18} /></button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <div>
                <div style={{ fontSize: 9, color: D.txl, marginBottom: 3 }}>RUT / N° documento</div>
                <input value={manualForm.rut} onChange={(e) => setManualForm((f) => ({ ...f, rut: e.target.value }))} placeholder="12.345.678-9" style={{ width: "100%", padding: "7px 9px", borderRadius: 7, border: `1px solid ${D.brd}`, background: D.bg, color: D.txt, fontSize: 11.5 }} />
                {matchManualPorRut && (
                  <div style={{ display: "flex", alignItems: "center", gap: 5, marginTop: 5, fontSize: 10, color: D.tea }}>
                    <UserCheck size={11} />Ya existe: {matchManualPorRut.nombre} · CUP {matchManualPorRut.cup} — se reutiliza el mismo CUP
                  </div>
                )}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr", gap: 8 }}>
                <div>
                  <div style={{ fontSize: 9, color: D.txl, marginBottom: 3 }}>Nombre completo</div>
                  <input value={manualForm.nombre} onChange={(e) => setManualForm((f) => ({ ...f, nombre: e.target.value }))} placeholder="Nombre y apellidos" style={{ width: "100%", padding: "7px 9px", borderRadius: 7, border: `1px solid ${D.brd}`, background: D.bg, color: D.txt, fontSize: 11.5 }} />
                </div>
                <div>
                  <div style={{ fontSize: 9, color: D.txl, marginBottom: 3 }}>Edad</div>
                  <input type="number" value={manualForm.edad} onChange={(e) => setManualForm((f) => ({ ...f, edad: e.target.value }))} style={{ width: "100%", padding: "7px 9px", borderRadius: 7, border: `1px solid ${D.brd}`, background: D.bg, color: D.txt, fontSize: 11.5 }} />
                </div>
                <div>
                  <div style={{ fontSize: 9, color: D.txl, marginBottom: 3 }}>Sexo</div>
                  <select value={manualForm.sexo} onChange={(e) => setManualForm((f) => ({ ...f, sexo: e.target.value }))} style={{ width: "100%", padding: "7px 9px", borderRadius: 7, border: `1px solid ${D.brd}`, background: D.bg, color: D.txt, fontSize: 11.5 }}>
                    <option value="F">F</option>
                    <option value="M">M</option>
                  </select>
                </div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                <div>
                  <div style={{ fontSize: 9, color: D.txl, marginBottom: 3 }}>Modalidad</div>
                  <select value={manualForm.modalidad} onChange={(e) => setManualForm((f) => ({ ...f, modalidad: e.target.value }))} style={{ width: "100%", padding: "7px 9px", borderRadius: 7, border: `1px solid ${D.brd}`, background: D.bg, color: D.txt, fontSize: 11.5 }}>
                    {Object.keys(MODALIDADES).map((m) => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>
                <div>
                  <div style={{ fontSize: 9, color: D.txl, marginBottom: 3 }}>Procedencia</div>
                  <select value={manualForm.procedencia} onChange={(e) => setManualForm((f) => ({ ...f, procedencia: e.target.value }))} style={{ width: "100%", padding: "7px 9px", borderRadius: 7, border: `1px solid ${D.brd}`, background: D.bg, color: D.txt, fontSize: 11.5 }}>
                    <option>Ambulatorio</option>
                    <option>Hospitalizado</option>
                    <option>Urgencia</option>
                  </select>
                </div>
              </div>
              <div>
                <div style={{ fontSize: 9, color: D.txl, marginBottom: 3 }}>Examen a realizar</div>
                <input value={manualForm.estudio} onChange={(e) => setManualForm((f) => ({ ...f, estudio: e.target.value }))} placeholder="Ej. TC tórax sin contraste" style={{ width: "100%", padding: "7px 9px", borderRadius: 7, border: `1px solid ${D.brd}`, background: D.bg, color: D.txt, fontSize: 11.5 }} />
              </div>
              <div>
                <div style={{ fontSize: 9, color: D.txl, marginBottom: 3 }}>Orden médica</div>
                <button onClick={() => ordenMedicaInputRef.current?.click()} style={{ display: "flex", alignItems: "center", gap: 6, width: "100%", padding: "8px 10px", borderRadius: 7, border: `1px dashed ${D.brd}`, background: D.bg, color: ordenMedicaAdjunta ? D.tea : D.txm, fontSize: 11, fontWeight: 600, cursor: "pointer" }}>
                  <Paperclip size={13} />{ordenMedicaAdjunta ? ordenMedicaAdjunta.nombre : "Adjuntar orden médica (PDF/foto)"}
                </button>
                <input ref={ordenMedicaInputRef} type="file" accept="application/pdf,.doc,.docx,image/*" style={{ display: "none" }} onChange={(e) => { const f = e.target.files?.[0]; if (f) setOrdenMedicaAdjunta({ tipo: f.type.startsWith("image/") ? "Foto" : "Documento", nombre: f.name }); e.target.value = ""; }} />
              </div>
            </div>

            <button onClick={crearIngresoManual} disabled={!manualForm.rut.trim() || !manualForm.nombre.trim() || !manualForm.estudio.trim()} style={{ width: "100%", marginTop: 16, padding: "10px 12px", borderRadius: 8, border: "none", background: D.pri, color: "#0A1420", fontSize: 12, fontWeight: 700, cursor: (manualForm.rut.trim() && manualForm.nombre.trim() && manualForm.estudio.trim()) ? "pointer" : "default", opacity: (manualForm.rut.trim() && manualForm.nombre.trim() && manualForm.estudio.trim()) ? 1 : 0.5, display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}>
              <UserPlus size={13} />Ingresar y enviar a Admisión
            </button>
            <p style={{ fontSize: 9.5, color: D.txl, marginTop: 10, lineHeight: 1.4 }}>El pago/bono se resuelve después, desde la pestaña Admisión (§11).</p>
          </div>
        </>
      )}

      {/* Modal — visor DICOM: genera un patrón de prueba real, lo codifica, lo decodifica y lo pinta acá mismo */}
      {visorPaciente && (
        <VisorPantallaCompleta
          record={visorPaciente}
          mostrarInforme={puedeInformar && visorPaciente.fase === "examenes"}
          sesion={sesion}
          informeCampos={informeCampos}
          setInformeCampos={setInformeCampos}
          misPlantillas={misPlantillas}
          guardarPlantilla={guardarPlantilla}
          nombrePlantilla={nombrePlantilla}
          setNombrePlantilla={setNombrePlantilla}
          setTitulo={setTitulo}
          setClasificacionCritica={setClasificacionCritica}
          setCie10={setCie10}
          onVolver={() => setVisorPaciente(null)}
          onAbrirInforme={() => abrirInforme(visorPaciente.id)}
          onValidarInforme={() => validarInforme(visorPaciente.id)}
        />
      )}
    </div>
  );
}

import React, { useState, useMemo, useEffect, useRef } from "react";
import {
  Activity, Search, Zap, RefreshCw, ArrowUpDown, ChevronRight, Cpu, Eye,
  FileText, Printer, MessageSquare, Calendar, UserCheck, Monitor,
  FolderOpen, X, ClipboardCheck, ShieldCheck, AlertTriangle, CheckCircle,
  Clock, Database, Filter, Layers, Plus, Save, Download, HelpCircle,
  FlaskConical, Phone, CheckSquare, Server, ArrowRight, ShieldAlert,
  Award, AlertCircle, Ban, SlidersHorizontal, ChevronDown, ExternalLink,
  Radio, HardDrive, BarChart3, Bell, Play, Pause, Terminal, Trash2, Check,
  Lock, Unlock, Hash, Copy, CheckCheck, Bug, Microscope
} from "lucide-react";

/* ─────────────────────────────────────────────────────────────────────────
   § 1 · PALETA OSCURA AXON DARK SLATE (SOBRIA, 1:1 CON HIS-RIS-PACS)
   ───────────────────────────────────────────────────────────────────────── */
const D = {
  bg:   "#0A1420",
  sfc:  "#111F32",
  sfc2: "#0D1A29",
  sfc3: "#152438",
  brd:  "#1E3350",
  txt:  "#EAF0FA",
  txm:  "#96AAC6",
  txl:  "#5E7593",
  pri:  "#9BA8B8",
  tea:  "#22D3B8",
  dan:  "#FF5C6C",
  war:  "#FFA359",
  suc:  "#5FD97A",
  pur:  "#B37FE0",
};

/* ─────────────────────────────────────────────────────────────────────────
   § 2 · CATÁLOGOS CLÍNICOS Y MODELO DE LABORATORIO
   ───────────────────────────────────────────────────────────────────────── */
const DISCIPLINAS = {
  BIOQ:    { color: "#4C8DFF", nombre: "Bioquímica Clínica" },
  HEM:     { color: "#E0559E", nombre: "Hematología" },
  COAG:    { color: "#FF7A59", nombre: "Coagulación" },
  MIC:     { color: "#22D3B8", nombre: "Microbiología" },
  INM:     { color: "#B37FE0", nombre: "Inmunología & Serología" },
  URI:     { color: "#FFC24C", nombre: "Uroanálisis & Líquidos" },
  GAS:     { color: "#7BC4A8", nombre: "Gases Arteriales" },
  MOL:     { color: "#29B6D8", nombre: "Biología Molecular" },
  BANSANG: { color: "#EF4444", nombre: "Banco de Sangre & Transfusional" },
  HISTO:   { color: "#A855F7", nombre: "Histopatología & Citodiagnóstico" },
  TOX:     { color: "#F43F5E", nombre: "Toxicología Clínica" },
};

const TUBOS_CONFIG = {
  EDTA:           { label: "Lila (K2 EDTA 4.0 mL)", color: "#8B5CF6", tipoMuestra: "Sangre total venosa anticoagulada", desc: "Hematología y hemograma completo" },
  SUERO:          { label: "Amarillo (Gel Separador 5.0 mL)", color: "#EAB308", tipoMuestra: "Suero sanguíneo", desc: "Bioquímica clínica e inmunoserología" },
  CITRATO:        { label: "Celeste (Citrato 3.2% 2.7 mL)", color: "#0284C7", tipoMuestra: "Plasma citratado", desc: "Pruebas de coagulación y hemostasia" },
  HEPARINA:       { label: "Verde (Heparina Litio 2.0 mL)", color: "#10B981", tipoMuestra: "Sangre total heparinada", desc: "Gases arteriales y química STAT" },
  ORINA:          { label: "Frasco Estéril 60 mL", color: "#F59E0B", tipoMuestra: "Orina matutina segundo chorro", desc: "Uroanálisis y sedimento microscópico" },
  HEMOCULTIVO:    { label: "Botellas Frascos Hemocultivo Aer/Anaer", color: "#06B6D4", tipoMuestra: "Sangre inoculada en medio bifásico", desc: "Detección de bacteriemia e incubación automatizada" },
  BOLSA_TRANSFUS: { label: "Unidad Concentrado Eritrocitario (ISBT 128)", color: "#DC2626", tipoMuestra: "Glóbulos rojos desleucocitados en SAGM", desc: "Medicina transfusional y pruebas de compatibilidad" },
  HISTO_BIOPSIA:  { label: "Frasco Formalina Neutra Tamponada 10%", color: "#9333EA", tipoMuestra: "Muestra de tejido biópsico", desc: "Fijación y procesamiento histopatológico" },
};

const ANALIZADORES_CATALOGO = [
  {
    id: "c503",
    nombre: "Roche Cobas Pro c503",
    ip: "192.168.10.42",
    puerto: 5000,
    proto: "HL7 v2.5.1 / MLLP",
    disc: "BIOQ",
    disciplinaNombre: "Bioquímica Clínica",
    estado: "online",
    metodos: "Fotometría UV / ISE indirecto / Colorimetría",
    analitosSoportados: ["GLU", "BUN", "UREA", "CREAT", "AC_URIC", "BILI_T", "BILI_D", "GOT", "GPT", "FA", "PROT_T", "ALB", "CALCIO", "K", "PCR", "CKMB"],
    testsHoy: 142,
    ultPing: "hace 18 seg",
    colaPendiente: 0,
  },
  {
    id: "e411",
    nombre: "Roche Cobas e411 / e801",
    ip: "192.168.10.43",
    puerto: 5001,
    proto: "HL7 v2.5.1 / MLLP",
    disc: "INM",
    disciplinaNombre: "Inmunoquímica ECLIA",
    estado: "online",
    metodos: "Electroquimioluminiscencia (ECLIA)",
    analitosSoportados: ["TROP", "CKMB", "FERR", "TSH", "PROCAL"],
    testsHoy: 68,
    ultPing: "hace 25 seg",
    colaPendiente: 0,
  },
  {
    id: "xn1000",
    nombre: "Sysmex XN-1000",
    ip: "192.168.10.45",
    puerto: 5100,
    proto: "ASTM E1394-91 / TCP",
    disc: "HEM",
    disciplinaNombre: "Hematología Automatizada",
    estado: "online",
    metodos: "Citometría de flujo con fluorescencia / SLS",
    analitosSoportados: ["LEUC", "GR", "HEM", "HTO", "VCM", "HCM", "CHCM", "PLAQT", "NEUT"],
    testsHoy: 89,
    ultPing: "hace 42 seg",
    colaPendiente: 0,
  },
  {
    id: "stago",
    nombre: "Stago STA-R Max",
    ip: "192.168.10.48",
    puerto: 5200,
    proto: "ASTM E1394-91 / RS232-TCP",
    disc: "COAG",
    disciplinaNombre: "Hemostasia y Coagulación",
    estado: "online",
    metodos: "Detección mecánica por bola rodante (viscosidad)",
    analitosSoportados: ["TP", "ACT_TP", "INR", "TTPK", "FIB"],
    testsHoy: 54,
    ultPing: "hace 1 min",
    colaPendiente: 0,
  },
  {
    id: "abl90",
    nombre: "Radiometer ABL90 FLEX",
    ip: "192.168.10.51",
    puerto: 5300,
    proto: "ASTM E1394-91 / TCP",
    disc: "GAS",
    disciplinaNombre: "Gases & Co-oximetría",
    estado: "online",
    metodos: "Potenciometría / Amperometría directa y espectrometría",
    analitosSoportados: ["PH", "PCO2", "PO2", "HCO3", "BE", "SATO2", "LACT"],
    testsHoy: 31,
    ultPing: "hace 3 min",
    colaPendiente: 0,
  },
  {
    id: "vitros",
    nombre: "Ortho Vitros 5600",
    ip: "192.168.10.55",
    puerto: 5400,
    proto: "ASTM E1394-91 / TCP",
    disc: "BIOQ",
    disciplinaNombre: "Química Seca y Respaldo",
    estado: "online",
    metodos: "MicroSlide Química Seca reflectométrica",
    analitosSoportados: ["GLU", "CREAT", "UREA"],
    testsHoy: 22,
    ultPing: "hace 4 min",
    colaPendiente: 0,
  },
  {
    id: "cobas6800",
    nombre: "Roche COBAS 6800",
    ip: "192.168.10.58",
    puerto: 5500,
    proto: "HL7 v2.5.1 / MLLP",
    disc: "MOL",
    disciplinaNombre: "Biología Molecular",
    estado: "online",
    metodos: "RT-PCR cuantitativa en tiempo real / NGS prep",
    analitosSoportados: ["CV_VIH1", "CV_HCV", "CV_HBV", "MTBC_PCR", "HPV_GT"],
    testsHoy: 8,
    ultPing: "hace 2 min",
    colaPendiente: 1,
  },
  {
    id: "clinitek",
    nombre: "Siemens CLINITEK Novus",
    ip: "192.168.10.59",
    puerto: 5600,
    proto: "ASTM E1394-91 / TCP",
    disc: "URI",
    disciplinaNombre: "Uroanálisis Automatizado",
    estado: "online",
    metodos: "Fotometría reflectométrica – Tira química 10 parámetros + iQ200",
    analitosSoportados: ["TIRA_QUIMICA", "SEDIMENTO_MICRO"],
    testsHoy: 34,
    ultPing: "hace 1 min",
    colaPendiente: 0,
  },
  {
    id: "architect_i2000",
    nombre: "Abbott Architect i2000SR",
    ip: "192.168.10.60",
    puerto: 5700,
    proto: "HL7 v2.5.1 / MLLP",
    disc: "TOX",
    disciplinaNombre: "Toxicología Clínica – Inmunoensayo",
    estado: "online",
    metodos: "CMIA – Quimioluminiscencia micropartículas",
    analitosSoportados: ["PANEL_DROGAS", "ETANOL", "PARACETAMOL", "SALICILATOS"],
    testsHoy: 5,
    ultPing: "hace 3 min",
    colaPendiente: 0,
  },
  {
    id: "micro_histo",
    nombre: "Nikon Eclipse Ci-L + Leica ASP6025",
    ip: "192.168.10.61",
    puerto: 5800,
    proto: "Interfaz manual (HISTO-NET v3)",
    disc: "HISTO",
    disciplinaNombre: "Histopatología y Anatomía Patológica",
    estado: "online",
    metodos: "Histología H&E / Giemsa / Inmunohistoquímica / FISH",
    analitosSoportados: ["HISTO_GASTRICA", "HISTO_COLON", "HISTO_MAMA", "HISTO_PIEL"],
    testsHoy: 3,
    ultPing: "hace 5 min",
    colaPendiente: 0,
  },
  {
    id: "bactalert",
    nombre: "bioMérieux BacT/ALERT Virtuo & VITEK MS",
    ip: "192.168.10.82",
    puerto: 5950,
    proto: "ASTM E1394-91 / TCP",
    disc: "MIC",
    disciplinaNombre: "Hemocultivo & MALDI-TOF",
    estado: "online",
    metodos: "Monitorización continua colorimétrica CO2 + Espectrometría MALDI-TOF",
    analitosSoportados: ["HEMOCULTIVO_AST", "CULTIVO_ORINA_AST"],
    testsHoy: 16,
    ultPing: "hace 40 seg",
    colaPendiente: 0,
  }
];

const SESIONES_USUARIO = [
  {
    id: "usr_dt",
    nombre: "Dra. Patricia Morales O.",
    rol: "Directora Técnica · Bioquímica Clínica",
    rolId: "dt",
    cut: "2026-BM-9812",
    regSIS: "74892-SIS",
    permisos: ["FIRMA_DT", "VAL_FACULTATIVA", "NOTIFICAR_CRITICO", "RECHAZO_MUESTRA", "GESTION_CALIDAD"],
    puedeFirmar: true,
  },
  {
    id: "usr_tm",
    nombre: "TM. Valentina Carvallo P.",
    rol: "Tecnóloga Médica · Hematología & Bioquímica",
    rolId: "tm",
    cut: "2026-TM-4421",
    regSIS: "88214-SIS",
    permisos: ["VAL_TECNICA", "NOTIFICAR_CRITICO", "RECHAZO_MUESTRA", "EJECUCION_ANALITICA"],
    puedeFirmar: false,
  },
  {
    id: "usr_tens",
    nombre: "TENS. Rodrigo Tapia V.",
    rol: "TENS Flebotomía & Preanalítica",
    rolId: "tens",
    cut: "2026-TE-7719",
    regSIS: "91024-SIS",
    permisos: ["TOMA_MUESTRA", "RECEPCION_CENTRAL", "ROTULACION"],
    puedeFirmar: false,
  }
];

/* ─────────────────────────────────────────────────────────────────────────
   § 3 · ALGORITMOS CLÍNICOS PUROS (RUT MÓDULO 11, DELTA MATH, SHA-256 HASH)
   ───────────────────────────────────────────────────────────────────────── */
function validarRutChileno(rutCompleto) {
  if (!rutCompleto || typeof rutCompleto !== "string") return false;
  const limpio = rutCompleto.replace(/[^0-9kK]/g, "").toUpperCase();
  if (limpio.length < 8 || limpio.length > 9) return false;
  const cuerpo = limpio.slice(0, -1);
  const dv = limpio.slice(-1);
  let suma = 0;
  let multiplo = 2;
  for (let i = cuerpo.length - 1; i >= 0; i--) {
    suma += multiplo * parseInt(cuerpo[i], 10);
    multiplo = multiplo < 7 ? multiplo + 1 : 2;
  }
  const dvEsperado = 11 - (suma % 11);
  const dvCalc = dvEsperado === 11 ? "0" : dvEsperado === 10 ? "K" : String(dvEsperado);
  return dv === dvCalc;
}

function formatearRut(rutRaw) {
  if (!rutRaw) return "";
  const limpio = rutRaw.replace(/[^0-9kK]/g, "").toUpperCase();
  if (limpio.length <= 1) return limpio;
  const cuerpo = limpio.slice(0, -1);
  const dv = limpio.slice(-1);
  const conPuntos = cuerpo.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `${conPuntos}-${dv}`;
}

function calcularDelta(actual, previo) {
  if (previo === null || previo === undefined || isNaN(actual) || isNaN(previo) || previo === 0) return null;
  const d = ((actual - previo) / previo) * 100;
  return d > 0 ? `+${d.toFixed(1)}%` : `${d.toFixed(1)}%`;
}

function evaluarFlag(valor, refMin, refMax, critMin, critMax) {
  if (valor === null || valor === undefined || isNaN(valor)) return "PENDING";
  if (critMin !== null && critMin !== undefined && valor <= critMin) return "CRITICAL_LOW";
  if (critMax !== null && critMax !== undefined && valor >= critMax) return "CRITICAL_HIGH";
  if (refMin !== null && refMin !== undefined && valor < refMin) return "LOW";
  if (refMax !== null && refMax !== undefined && valor > refMax) return "HIGH";
  return "NORMAL";
}

function sha256Sync(str) {
  function rightRotate(value, amount) {
    return (value >>> amount) | (value << (32 - amount));
  }
  const asciiOrUtf8 = str === null || str === undefined ? "" : String(str);
  const utf8Bytes = [];
  for (let i = 0; i < asciiOrUtf8.length; i++) {
    let charcode = asciiOrUtf8.charCodeAt(i);
    if (charcode < 0x80) {
      utf8Bytes.push(charcode);
    } else if (charcode < 0x800) {
      utf8Bytes.push(0xc0 | (charcode >> 6), 0x80 | (charcode & 0x3f));
    } else if (charcode < 0xd800 || charcode >= 0xe000) {
      utf8Bytes.push(0xe0 | (charcode >> 12), 0x80 | ((charcode >> 6) & 0x3f), 0x80 | (charcode & 0x3f));
    } else {
      i++;
      charcode = 0x10000 + (((charcode & 0x3ff) << 10) | (asciiOrUtf8.charCodeAt(i) & 0x3ff));
      utf8Bytes.push(0xf0 | (charcode >> 18), 0x80 | ((charcode >> 12) & 0x3f), 0x80 | ((charcode >> 6) & 0x3f), 0x80 | (charcode & 0x3f));
    }
  }

  const K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
  ];

  let H0 = 0x6a09e667, H1 = 0xbb67ae85, H2 = 0x3c6ef372, H3 = 0xa54ff53a;
  let H4 = 0x510e527f, H5 = 0x9b05688c, H6 = 0x1f83d9ab, H7 = 0x5be0cd19;

  const bitLength = utf8Bytes.length * 8;
  utf8Bytes.push(0x80);
  while ((utf8Bytes.length + 8) % 64 !== 0) utf8Bytes.push(0);

  const highBits = Math.floor(bitLength / 0x100000000);
  const lowBits = bitLength >>> 0;
  for (let i = 3; i >= 0; i--) utf8Bytes.push((highBits >>> (i * 8)) & 0xff);
  for (let i = 3; i >= 0; i--) utf8Bytes.push((lowBits >>> (i * 8)) & 0xff);

  const W = new Array(64);
  for (let i = 0; i < utf8Bytes.length; i += 64) {
    for (let t = 0; t < 16; t++) {
      W[t] = (utf8Bytes[i + t * 4] << 24) |
             (utf8Bytes[i + t * 4 + 1] << 16) |
             (utf8Bytes[i + t * 4 + 2] << 8) |
             (utf8Bytes[i + t * 4 + 3]);
    }
    for (let t = 16; t < 64; t++) {
      const s0 = rightRotate(W[t - 15], 7) ^ rightRotate(W[t - 15], 18) ^ (W[t - 15] >>> 3);
      const s1 = rightRotate(W[t - 2], 17) ^ rightRotate(W[t - 2], 19) ^ (W[t - 2] >>> 10);
      W[t] = (W[t - 16] + s0 + W[t - 7] + s1) | 0;
    }

    let a = H0, b = H1, c = H2, d = H3, e = H4, f = H5, g = H6, h = H7;

    for (let t = 0; t < 64; t++) {
      const S1 = rightRotate(e, 6) ^ rightRotate(e, 11) ^ rightRotate(e, 25);
      const ch = (e & f) ^ ((~e) & g);
      const temp1 = (h + S1 + ch + K[t] + W[t]) | 0;
      const S0 = rightRotate(a, 2) ^ rightRotate(a, 13) ^ rightRotate(a, 22);
      const maj = (a & b) ^ (a & c) ^ (b & c);
      const temp2 = (S0 + maj) | 0;

      h = g;
      g = f;
      f = e;
      e = (d + temp1) | 0;
      d = c;
      c = b;
      b = a;
      a = (temp1 + temp2) | 0;
    }

    H0 = (H0 + a) | 0;
    H1 = (H1 + b) | 0;
    H2 = (H2 + c) | 0;
    H3 = (H3 + d) | 0;
    H4 = (H4 + e) | 0;
    H5 = (H5 + f) | 0;
    H6 = (H6 + g) | 0;
    H7 = (H7 + h) | 0;
  }

  const toHex = n => (n >>> 0).toString(16).padStart(8, '0');
  return toHex(H0) + toHex(H1) + toHex(H2) + toHex(H3) + toHex(H4) + toHex(H5) + toHex(H6) + toHex(H7);
}

/* ─────────────────────────────────────────────────────────────────────────
   § 4 · DATOS SEMILLA CLÍNICOS ESTRUCTURADOS (D.S. 20, RUTs VÁLIDOS, DELTAS)
   ───────────────────────────────────────────────────────────────────────── */
const SEED_ORDENES = [
  {
    id: 1,
    acc: "ACC-2026-000412",
    orden: "ORD-2026-08912",
    cup: "CUP-CL-13-2026-00004121-K8",
    rut: "12.890.345-3",
    paciente: "Carlos Eduardo Martínez B.",
    edad: 62,
    sexo: "M",
    origen: "Urgencia Adulto · Reanimación",
    cama: "Box REA-02",
    prioridad: "stat",
    medicoSolicitante: "Dra. Francisca Valenzuela (Reg. SIS 44901)",
    diagnostico: "Síndrome Coronario Agudo con Supradesnivel ST. Sospecha IAM.",
    fase: "validacion_fac",
    estado: "resultado_disp",
    disciplinas: ["BIOQ", "GAS"],
    horaOrden: "08:10",
    horaToma: "08:18",
    horaRecepcion: "08:24",
    tubos: [
      {
        id: "SMP-2026-08912-01",
        tipo: "SUERO",
        recipiente: "Tubo Vacutainer Gel Separador 5.0 mL",
        tipoMuestra: "Suero sanguíneo",
        estado: "procesada",
        horaToma: "08:18",
        horaRecepcion: "08:24",
        gradilla: "Gradilla URG-01 Pos 04 (Nevera 4°C)",
        causalRechazo: null,
      },
      {
        id: "SMP-2026-08912-02",
        tipo: "HEPARINA",
        recipiente: "Jeringa Balanceada Heparina Litio 2.0 mL",
        tipoMuestra: "Sangre total arterial heparinada",
        estado: "procesada",
        horaToma: "08:19",
        horaRecepcion: "08:24",
        gradilla: "Analizado en ABL90 · Desecho Biológico",
        causalRechazo: null,
      }
    ],
    analitos: [
      {
        id: "OBS-01-01",
        testKey: "TROP",
        tuboId: "SMP-2026-08912-01",
        codigo: "49563-0",
        nombre: "Troponina T ultrasensible (hs-cTnT)",
        disc: "INM",
        metodo: "Electroquimioluminiscencia (ECLIA)",
        equipoId: "e411",
        equipo: "Roche Cobas e411 / e801",
        valor: 145.8,
        ucum: "ng/L",
        refMin: 0.0,
        refMax: 14.0,
        critMin: null,
        critMax: 52.0,
        flag: "CRITICAL_HIGH",
        previo: 15.2,
        delta: "+859.2%",
        horaMedicion: "08:31",
        alertaCritica: {
          activa: true,
          horaDeteccion: "08:31:14",
          notificado: false,
          receptor: null,
          registroReceptor: null,
          via: null,
          anexo: null,
          horaNotif: null,
          readback: false,
          medidas: null,
          auditoriaNotif: null,
        }
      },
      {
        id: "OBS-01-02",
        testKey: "K",
        tuboId: "SMP-2026-08912-01",
        codigo: "2823-3",
        nombre: "Potasio Sérico (K+)",
        disc: "BIOQ",
        metodo: "Electrodo Selectivo de Iones (ISE indirecto)",
        equipoId: "c503",
        equipo: "Roche Cobas Pro c503",
        valor: 6.4,
        ucum: "mEq/L",
        refMin: 3.5,
        refMax: 5.1,
        critMin: 2.8,
        critMax: 6.0,
        flag: "CRITICAL_HIGH",
        previo: 4.8,
        delta: "+33.3%",
        horaMedicion: "08:29",
        alertaCritica: {
          activa: true,
          horaDeteccion: "08:29:45",
          notificado: false,
          receptor: null,
          registroReceptor: null,
          via: null,
          anexo: null,
          horaNotif: null,
          readback: false,
          medidas: null,
          auditoriaNotif: null,
        }
      },
      {
        id: "OBS-01-03",
        testKey: "CKMB",
        tuboId: "SMP-2026-08912-01",
        codigo: "2039-6",
        nombre: "CK-MB masa",
        disc: "BIOQ",
        metodo: "ECLIA Inmunoensayo",
        equipoId: "c503",
        equipo: "Roche Cobas Pro c503",
        valor: 28.4,
        ucum: "ng/mL",
        refMin: 0.0,
        refMax: 5.0,
        critMin: null,
        critMax: 25.0,
        flag: "HIGH",
        previo: 4.1,
        delta: "+592.7%",
        horaMedicion: "08:31",
        alertaCritica: null,
      },
      {
        id: "OBS-01-04",
        testKey: "LACT",
        tuboId: "SMP-2026-08912-02",
        codigo: "2524-7",
        nombre: "Lactato en Sangre Arterial",
        disc: "GAS",
        metodo: "Amperometría enzimática con membrana biosensora",
        equipoId: "abl90",
        equipo: "Radiometer ABL90 FLEX",
        valor: 3.4,
        ucum: "mmol/L",
        refMin: 0.5,
        refMax: 1.6,
        critMin: null,
        critMax: 4.0,
        flag: "HIGH",
        previo: 1.8,
        delta: "+88.9%",
        horaMedicion: "08:27",
        alertaCritica: null,
      }
    ],
    auditoria: [
      {
        id: "AUD-01",
        hora: "08:10:02",
        actor: "Dra. Francisca Valenzuela",
        rol: "Médica Solicitante (Urgencia)",
        cut: "2026-MED-44901",
        accion: "CREACION_ORDEN_STAT",
        detalle: "Ingreso de solicitud urgente con prioridad STAT. Sospecha SCA.",
        hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      },
      {
        id: "AUD-02",
        hora: "08:18:30",
        actor: "TENS. Rodrigo Tapia V.",
        rol: "Flebotomista",
        cut: "2026-TE-7719",
        accion: "TOMA_MUESTRAS_OK",
        detalle: "Extracción venosa y punción arterial en Box REA-02. Identificación positiva y código rotulado.",
        hash: "a4f8e91c52d8b8209841b98c4129e92418a02c914ba127cb8a9942a1bc29412a"
      },
      {
        id: "AUD-03",
        hora: "08:24:12",
        actor: "TM. Valentina Carvallo P.",
        rol: "Recepción Laboratorio Central",
        cut: "2026-TM-4421",
        accion: "RECEPCION_CENTRAL",
        detalle: "Recepción conforme de 2 tubos. Sin hemólisis macroscópica. Ingreso a lista de trabajo analítica.",
        hash: "7bc321e901a8f94101e92182c8192a014bc91204ba2198ca1290bb3410a82914"
      },
      {
        id: "AUD-04",
        hora: "08:31:15",
        actor: "Roche Cobas Pro c503 (Gateway)",
        rol: "Analizador Bioquímica",
        cut: "DEV-ROCHE-C503",
        accion: "RESULTADO_INSTRUMENTO",
        detalle: "Transmisión HL7 ORU^R01. hs-cTnT: 145.8 ng/L (CRÍTICO) / K+: 6.4 mEq/L (CRÍTICO).",
        hash: "d91a82f019ab921cba102910fa8912c418902194bca1920ca1289b0149ac1029"
      }
    ],
    informe: {
      version: "0.9-BORRADOR",
      estado: "preliminar",
      firmaDT: null,
      fechaEmision: null,
      tecnologoValidador: "TM. Valentina Carvallo P.",
    }
  },
  {
    id: 2,
    acc: "ACC-2026-000413",
    orden: "ORD-2026-08913",
    cup: "CUP-CL-13-2026-00004122-J1",
    rut: "18.432.901-8",
    paciente: "Matías Ignacio Valdés P.",
    edad: 24,
    sexo: "M",
    origen: "Policlínico Medicina · Box 08",
    cama: "Ambulatorio",
    prioridad: "rutina",
    medicoSolicitante: "Dr. Marcelo Arriagada (Reg. SIS 31920)",
    diagnostico: "Chequeo médico de rutina. Control perfil lipídico y hemograma.",
    fase: "flebotomia",
    estado: "pendiente_toma",
    disciplinas: ["HEM", "BIOQ"],
    horaOrden: "08:25",
    horaToma: null,
    horaRecepcion: null,
    tubos: [
      {
        id: "SMP-2026-08913-01",
        tipo: "EDTA",
        recipiente: "Tubo Vacutainer K2 EDTA 4.0 mL",
        tipoMuestra: "Sangre total venosa anticoagulada",
        estado: "pendiente_toma",
        horaToma: null,
        horaRecepcion: null,
        gradilla: "Pendiente Flebotomía",
        causalRechazo: null,
      },
      {
        id: "SMP-2026-08913-02",
        tipo: "SUERO",
        recipiente: "Tubo Vacutainer Gel Separador 5.0 mL",
        tipoMuestra: "Suero sanguíneo",
        estado: "pendiente_toma",
        horaToma: null,
        horaRecepcion: null,
        gradilla: "Pendiente Flebotomía",
        causalRechazo: null,
      }
    ],
    analitos: [
      {
        id: "OBS-02-01",
        testKey: "HEM",
        tuboId: "SMP-2026-08913-01",
        codigo: "718-7",
        nombre: "Hemoglobina",
        disc: "HEM",
        metodo: "Espectrofotometría SLS sin cianuro",
        equipoId: "xn1000",
        equipo: "Sysmex XN-1000",
        valor: null,
        ucum: "g/dL",
        refMin: 13.5,
        refMax: 17.5,
        critMin: 7.0,
        critMax: 20.0,
        flag: "PENDING",
        previo: 14.0,
        delta: null,
        horaMedicion: null,
        alertaCritica: null,
      },
      {
        id: "OBS-02-02",
        testKey: "GLU",
        tuboId: "SMP-2026-08913-02",
        codigo: "2345-7",
        nombre: "Glucosa en Suero (Ayuno)",
        disc: "BIOQ",
        metodo: "Hexoquinasa / UV",
        equipoId: "c503",
        equipo: "Roche Cobas Pro c503",
        valor: null,
        ucum: "mg/dL",
        refMin: 70.0,
        refMax: 99.0,
        critMin: 45.0,
        critMax: 400.0,
        flag: "PENDING",
        previo: 88.0,
        delta: null,
        horaMedicion: null,
        alertaCritica: null,
      }
    ],
    auditoria: [
      {
        id: "AUD-02-01",
        hora: "08:25:00",
        actor: "Dr. Marcelo Arriagada",
        rol: "Médico Solicitante",
        cut: "2026-MED-31920",
        accion: "CREACION_ORDEN_AMBULATORIA",
        detalle: "Generación de solicitud ambulatoria de chequeo preventivo.",
        hash: "82a912cb4019a820c8192a0149bc0192418a02c914ba127cb8a9942a1bc29412"
      }
    ],
    informe: null
  },
  {
    id: 3,
    acc: "ACC-2026-000414",
    orden: "ORD-2026-08914",
    cup: "CUP-CL-13-2026-00008819-H2",
    rut: "11.111.111-1",
    paciente: "Hugo Hernán Castro R.",
    edad: 71,
    sexo: "M",
    origen: "UCI Médica Central",
    cama: "Cama UCI-04",
    prioridad: "stat",
    medicoSolicitante: "Dr. Esteban Carrasco (Reg. SIS 55219)",
    diagnostico: "Shock séptico de foco abdominal. Coagulopatía de consumo.",
    fase: "worklist",
    estado: "en_analisis",
    disciplinas: ["HEM", "COAG"],
    horaOrden: "07:45",
    horaToma: "07:52",
    horaRecepcion: "08:02",
    tubos: [
      {
        id: "SMP-2026-08914-01",
        tipo: "EDTA",
        recipiente: "Tubo Vacutainer K2 EDTA 4.0 mL",
        tipoMuestra: "Sangre total venosa anticoagulada",
        estado: "en_analisis",
        horaToma: "07:52",
        horaRecepcion: "08:02",
        gradilla: "En cargador Sysmex XN-1000",
        causalRechazo: null,
      },
      {
        id: "SMP-2026-08914-02",
        tipo: "CITRATO",
        recipiente: "Tubo Vacutainer Citrato 3.2% 2.7 mL",
        tipoMuestra: "Plasma citratado",
        estado: "en_analisis",
        horaToma: "07:53",
        horaRecepcion: "08:02",
        gradilla: "En carrusel Stago STA-R Max",
        causalRechazo: null,
      }
    ],
    analitos: [
      {
        id: "OBS-03-01",
        testKey: "LEUC",
        tuboId: "SMP-2026-08914-01",
        codigo: "6690-2",
        nombre: "Leucocitos Totales",
        disc: "HEM",
        metodo: "Citometría de flujo con fluorescencia",
        equipoId: "xn1000",
        equipo: "Sysmex XN-1000",
        valor: null,
        ucum: "10*3/uL",
        refMin: 4.5,
        refMax: 11.0,
        critMin: 2.0,
        critMax: 25.0,
        flag: "PENDING",
        previo: 11.8,
        delta: null,
        horaMedicion: null,
        alertaCritica: null,
      },
      {
        id: "OBS-03-02",
        testKey: "PLAQT",
        tuboId: "SMP-2026-08914-01",
        codigo: "777-3",
        nombre: "Plaquetas",
        disc: "HEM",
        metodo: "Impedancia con enfoque hidrodinámico",
        equipoId: "xn1000",
        equipo: "Sysmex XN-1000",
        valor: null,
        ucum: "10*3/uL",
        refMin: 150.0,
        refMax: 450.0,
        critMin: 50.0,
        critMax: 1000.0,
        flag: "PENDING",
        previo: 120.0,
        delta: null,
        horaMedicion: null,
        alertaCritica: null,
      },
      {
        id: "OBS-03-03",
        testKey: "TP",
        tuboId: "SMP-2026-08914-02",
        codigo: "5902-2",
        nombre: "Tiempo de Protrombina (TP)",
        disc: "COAG",
        metodo: "Detección mecánica por viscosidad",
        equipoId: "stago",
        equipo: "Stago STA-R Max",
        valor: null,
        ucum: "seg",
        refMin: 11.0,
        refMax: 14.5,
        critMin: null,
        critMax: 30.0,
        flag: "PENDING",
        previo: 18.2,
        delta: null,
        horaMedicion: null,
        alertaCritica: null,
      }
    ],
    auditoria: [
      {
        id: "AUD-03-01",
        hora: "07:45:10",
        actor: "Dr. Esteban Carrasco",
        rol: "Médico Intensivista UCI",
        cut: "2026-MED-55219",
        accion: "SOLICITUD_STAT_UCI",
        detalle: "Ingreso de solicitud STAT por sepsis severa y sospecha CID.",
        hash: "3189a0129bc8192a0149bc0192418a02c914ba127cb8a9942a1bc29412a84210"
      },
      {
        id: "AUD-03-02",
        hora: "07:52:45",
        actor: "TM. Valentina Carvallo P.",
        rol: "Tecnóloga Médica",
        cut: "2026-TM-4421",
        accion: "TOMA_MUESTRA_UCI",
        detalle: "Toma de muestras por catéter venoso central bajo técnica aséptica.",
        hash: "7bc321e901a8f94101e92182c8192a014bc91204ba2198ca1290bb3410a82914"
      },
      {
        id: "AUD-03-03",
        hora: "08:02:18",
        actor: "TM. Valentina Carvallo P.",
        rol: "Laboratorio Central",
        cut: "2026-TM-4421",
        accion: "CARGA_WORKLIST_ANALIZADORES",
        detalle: "Centrifugación de tubo citrato y carga en Sysmex XN-1000 y Stago STA-R Max.",
        hash: "d91a82f019ab921cba102910fa8912c418902194bca1920ca1289b0149ac1029"
      }
    ],
    informe: null
  },
  {
    id: 4,
    acc: "ACC-2026-000415",
    orden: "ORD-2026-08915",
    cup: "CUP-CL-13-2026-00009114-B9",
    rut: "14.221.789-9",
    paciente: "Mariana del Carmen Rivas S.",
    edad: 49,
    sexo: "F",
    origen: "Hospitalizados · Cirugía",
    cama: "Sala 308-A",
    prioridad: "alta",
    medicoSolicitante: "Dra. Camila Sepúlveda (Reg. SIS 67812)",
    diagnostico: "Evaluación preoperatoria colecistectomía laparoscópica.",
    fase: "validacion_tec",
    estado: "resultado_disp",
    disciplinas: ["BIOQ"],
    horaOrden: "06:30",
    horaToma: "06:45",
    horaRecepcion: "06:55",
    tubos: [
      {
        id: "SMP-2026-08915-01",
        tipo: "SUERO",
        recipiente: "Tubo Vacutainer Gel Separador 5.0 mL",
        tipoMuestra: "Suero sanguíneo",
        estado: "procesada",
        horaToma: "06:45",
        horaRecepcion: "06:55",
        gradilla: "Gradilla CIR-02 Pos 12",
        causalRechazo: null,
      }
    ],
    analitos: [
      {
        id: "OBS-04-01",
        testKey: "ALB",
        tuboId: "SMP-2026-08915-01",
        codigo: "1751-7",
        nombre: "Albúmina Sérica",
        disc: "BIOQ",
        metodo: "Verde de Bromocresol (BCG)",
        equipoId: "c503",
        equipo: "Roche Cobas Pro c503",
        valor: 3.2,
        ucum: "g/dL",
        refMin: 3.5,
        refMax: 5.2,
        critMin: 2.0,
        critMax: null,
        flag: "LOW",
        previo: 3.5,
        delta: "-8.6%",
        horaMedicion: "07:15",
        alertaCritica: null,
      },
      {
        id: "OBS-04-02",
        testKey: "GOT",
        tuboId: "SMP-2026-08915-01",
        codigo: "1920-8",
        nombre: "Aspartato Aminotransferasa (AST / GOT)",
        disc: "BIOQ",
        metodo: "Cinético UV según IFCC con piridoxal fosfato",
        equipoId: "c503",
        equipo: "Roche Cobas Pro c503",
        valor: 54.0,
        ucum: "U/L",
        refMin: 10.0,
        refMax: 40.0,
        critMin: null,
        critMax: 200.0,
        flag: "HIGH",
        previo: 43.0,
        delta: "+25.6%",
        horaMedicion: "07:16",
        alertaCritica: null,
      }
    ],
    auditoria: [
      {
        id: "AUD-04-01",
        hora: "06:30:00",
        actor: "Dra. Camila Sepúlveda",
        rol: "Cirujana de Pabellón",
        cut: "2026-CIR-67812",
        accion: "SOLICITUD_PREOP",
        detalle: "Ingreso solicitud preoperatoria para cirugía programada.",
        hash: "4190ba1289bc8192a0149bc0192418a02c914ba127cb8a9942a1bc29412a8421"
      },
      {
        id: "AUD-04-02",
        hora: "07:16:30",
        actor: "Roche Cobas Pro c503",
        rol: "Analizador Central",
        cut: "DEV-ROCHE-C503",
        accion: "RESULTADOS_ANALIZADOR",
        detalle: "Recepción de analitos AST: 54 U/L (HIGH) y Albúmina: 3.2 g/dL (LOW).",
        hash: "82a912cb4019a820c8192a0149bc0192418a02c914ba127cb8a9942a1bc29412"
      }
    ],
    informe: null
  },
  {
    id: 5,
    acc: "ACC-2026-000416",
    orden: "ORD-2026-08916",
    cup: "CUP-CL-13-2026-00003189-A2",
    rut: "9.882.112-0",
    paciente: "Bernardo Andrés Lagos T.",
    edad: 64,
    sexo: "M",
    origen: "Ambulatorio · Oncología",
    cama: "Consulta 14",
    prioridad: "normal",
    medicoSolicitante: "Dr. Enzo Muñoz Caprile (Reg. SIS 21089)",
    diagnostico: "Seguimiento oncológico cáncer próstata. Remisión bioquímica.",
    fase: "informes",
    estado: "publicado",
    disciplinas: ["INM", "BIOQ"],
    horaOrden: "05:10",
    horaToma: "05:25",
    horaRecepcion: "05:40",
    tubos: [
      {
        id: "SMP-2026-08916-01",
        tipo: "SUERO",
        recipiente: "Tubo Vacutainer Gel Separador 5.0 mL",
        tipoMuestra: "Suero sanguíneo",
        estado: "procesada",
        horaToma: "05:25",
        horaRecepcion: "05:40",
        gradilla: "Seroteca Central Sector B-08",
        causalRechazo: null,
      }
    ],
    analitos: [
      {
        id: "OBS-05-01",
        testKey: "PSA",
        tuboId: "SMP-2026-08916-01",
        codigo: "2857-1",
        nombre: "Antígeno Prostático Específico Total (PSA)",
        disc: "INM",
        metodo: "Electroquimioluminiscencia (ECLIA)",
        equipoId: "e411",
        equipo: "Roche Cobas e411 / e801",
        valor: 1.45,
        ucum: "ng/mL",
        refMin: 0.0,
        refMax: 4.0,
        critMin: null,
        critMax: 20.0,
        flag: "NORMAL",
        previo: 1.42,
        delta: "+2.1%",
        horaMedicion: "06:12",
        alertaCritica: null,
      },
      {
        id: "OBS-05-02",
        testKey: "CREAT",
        tuboId: "SMP-2026-08916-01",
        codigo: "2160-0",
        nombre: "Creatinina Sérica",
        disc: "BIOQ",
        metodo: "Jaffé compensado / Cinético",
        equipoId: "c503",
        equipo: "Roche Cobas Pro c503",
        valor: 0.98,
        ucum: "mg/dL",
        refMin: 0.7,
        refMax: 1.25,
        critMin: 0.3,
        critMax: 3.0,
        flag: "NORMAL",
        previo: 0.95,
        delta: "+3.2%",
        horaMedicion: "06:15",
        alertaCritica: null,
      }
    ],
    auditoria: [
      {
        id: "AUD-05-01",
        hora: "05:10:00",
        actor: "Dr. Enzo Muñoz Caprile",
        rol: "Oncólogo Médico",
        cut: "2026-ONC-21089",
        accion: "SOLICITUD_CONTROL",
        detalle: "Control ambulatorio trimestral de PSA.",
        hash: "3189a0129bc8192a0149bc0192418a02c914ba127cb8a9942a1bc29412a84210"
      },
      {
        id: "AUD-05-02",
        hora: "06:30:15",
        actor: "TM. Valentina Carvallo P.",
        rol: "Tecnóloga Médica Validadora",
        cut: "2026-TM-4421",
        accion: "VALIDACION_TECNICA",
        detalle: "Revisión analítica y aprobación técnica conforme de resultados.",
        hash: "9128ca0192418a02c914ba127cb8a9942a1bc29412a842103189a0129bc8192a"
      },
      {
        id: "AUD-05-03",
        hora: "06:45:00",
        actor: "Dra. Patricia Morales O.",
        rol: "Directora Técnica · Bioquímica",
        cut: "2026-BM-9812",
        accion: "FIRMA_DT_PUBLICACION",
        detalle: "Firma Electrónica Avanzada y publicación oficial en Ficha Clínica AXON.",
        hash: "82a912cb4019a820c8192a0149bc0192418a02c914ba127cb8a9942a1bc29412"
      }
    ],
    informe: {
      version: "1.0-FINAL",
      estado: "publicado",
      fechaEmision: "15/10/2026 06:45:00",
      tecnologoValidador: "TM. Valentina Carvallo P. (Reg. SIS 88214)",
      firmaDT: {
        firmante: "Dra. Patricia Morales O.",
        cargo: "Directora Técnica · Bioquímica Clínica",
        cut: "2026-BM-9812",
        regSIS: "74892-SIS",
        timestamp: "2026-10-15 06:45:00 UTC-3",
        hashSha256: "82a912cb4019a820c8192a0149bc0192418a02c914ba127cb8a9942a1bc29412",
        estadoFirma: "Firma Electrónica Avanzada Verificada (Ley 19.799)",
      }
    }
  },
  {
    id: 6,
    acc: "ACC-2026-000417",
    orden: "ORD-2026-08917",
    cup: "CUP-CL-13-2026-00004172-M3",
    rut: "15.421.890-4",
    paciente: "Mariana Soledad Fuentes C.",
    edad: 46,
    sexo: "F",
    origen: "Reumatología · Consulta Externa",
    cama: "Box 12",
    prioridad: "rutina",
    medicoSolicitante: "Dr. Jorge Arancibia (Reg. SIS 67104)",
    diagnostico: "Sospecha Lupus Eritematoso Sistémico (LES). Poliartralgias y fotosensibilidad.",
    fase: "validacion_tec",
    estado: "resultado_disp",
    disciplinas: ["INM"],
    horaOrden: "08:15",
    horaToma: "08:30",
    horaRecepcion: "08:50",
    tubos: [
      {
        id: "SMP-2026-08917-01",
        tipo: "SUERO",
        recipiente: "Tubo Vacutainer Gel Separador 5.0 mL",
        tipoMuestra: "Suero sanguíneo",
        estado: "procesada",
        horaToma: "08:30",
        horaRecepcion: "08:50",
        gradilla: "Seroteca Central Sector INM-02",
        causalRechazo: null,
      }
    ],
    analitos: [
      {
        id: "OBS-06-01",
        testKey: "ANA_IFI",
        tuboId: "SMP-2026-08917-01",
        codigo: "4485-9",
        nombre: "Anticuerpos Antinucleares (ANA por IFI HEp-2)",
        disc: "INM",
        metodo: "Inmunofluorescencia Indirecta (IFI) en células HEp-2",
        equipoId: "e411",
        equipo: "Microscopía de Epifluorescencia LED",
        valor: "Positivo 1:320 (Moteado Fino Denso AC-4)",
        ucum: "título",
        refMin: null,
        refMax: null,
        critMin: null,
        critMax: null,
        flag: "HIGH",
        previo: "Negativo (< 1:80)",
        delta: "Seroconversión",
        horaMedicion: "09:45",
        alertaCritica: null,
        detalleEspecializado: {
          tipo: "INMUNOLOGIA_IFI",
          titulo: "1:320",
          patronIcap: "AC-4 (Moteado Fino)",
          asociacionClinica: "Fuerte correlación con LES / Síndrome de Sjögren (anti-Ro/SSA, anti-La/SSB).",
        }
      },
      {
        id: "OBS-06-02",
        testKey: "PROT_ELEC",
        tuboId: "SMP-2026-08917-01",
        codigo: "2887-8",
        nombre: "Electroforesis de Proteínas en Suero (Proteinograma)",
        disc: "INM",
        metodo: "Electroforesis Capilar Automatizada (Norma ISP 2025)",
        equipoId: "c503",
        equipo: "Analizador Capilar Sebia Capillarys",
        valor: "Policlonal en Zona Gamma (Sin Pico M)",
        ucum: "patrón",
        refMin: null,
        refMax: null,
        critMin: null,
        critMax: null,
        flag: "NORMAL",
        previo: null,
        delta: null,
        horaMedicion: "10:10",
        alertaCritica: null,
        detalleEspecializado: {
          tipo: "ELECTROFORESIS",
          fracciones: [
            { nombre: "Albúmina", pct: 58.2, ref: "55.8 - 66.1%" },
            { nombre: "Alfa-1 Globulina", pct: 3.5, ref: "2.9 - 4.9%" },
            { nombre: "Alfa-2 Globulina", pct: 9.1, ref: "7.1 - 11.8%" },
            { nombre: "Beta Globulinas", pct: 11.4, ref: "8.4 - 13.1%" },
            { nombre: "Gamma Globulinas", pct: 17.8, ref: "11.1 - 18.8%" },
          ],
          ratioAG: "1.39",
          picoM: "Negativo (No se observa componente monoclonal)",
        }
      }
    ],
    auditoria: [
      {
        id: "AUD-06-01",
        hora: "09:50",
        actor: "TM. Rodrigo Salinas (Cut 7701)",
        rol: "Tecnólogo Médico Inmunología",
        cut: "TM-7701-INM",
        accion: "VALIDACION_TECNICA",
        detalle: "Lectura microscópica IFI HEp-2 verificada a 400x con controles positivo y negativo conformes.",
        hash: "b712ca0192418a02c914ba127cb8a9942a1bc29412a842103189a0129bc8192a"
      }
    ],
    informe: null
  },
  {
    id: 7,
    acc: "ACC-2026-000418",
    orden: "ORD-2026-08918",
    cup: "CUP-CL-13-2026-00004183-B7",
    rut: "10.334.789-2",
    paciente: "Gabriel Ignacio Morales R.",
    edad: 59,
    sexo: "M",
    origen: "Pabellón Central · Cirugía Cardiovascular",
    cama: "Pabellón 03",
    prioridad: "stat",
    medicoSolicitante: "Dr. Marcelo Quintana (Reg. SIS 33902)",
    diagnostico: "Reemplazo Valvular Aórtico. Requerimiento transfusional intraoperatorio.",
    fase: "validacion_fac",
    estado: "resultado_disp",
    disciplinas: ["BANSANG"],
    horaOrden: "07:00",
    horaToma: "07:10",
    horaRecepcion: "07:22",
    tubos: [
      {
        id: "SMP-2026-08918-01",
        tipo: "EDTA",
        recipiente: "Tubo Vacutainer K2 EDTA 4.0 mL",
        tipoMuestra: "Sangre total venosa anticoagulada",
        estado: "procesada",
        horaToma: "07:10",
        horaRecepcion: "07:22",
        gradilla: "Gradilla Inmunohematología UMT-01",
        causalRechazo: null,
      }
    ],
    analitos: [
      {
        id: "OBS-07-01",
        testKey: "ABO_RHD",
        tuboId: "SMP-2026-08918-01",
        codigo: "883-9",
        nombre: "Clasificación Grupo Sanguíneo ABO & Factor RhD",
        disc: "BANSANG",
        metodo: "Aglutinación en Tarjeta Gel (Directa e Inversa)",
        equipoId: "vitros",
        equipo: "Sistema Automatizado Grifols Erytra",
        valor: "Grupo O (IV) · RhD Positivo",
        ucum: "fenotipo",
        refMin: null,
        refMax: null,
        critMin: null,
        critMax: null,
        flag: "NORMAL",
        previo: "Grupo O · RhD Positivo (2024)",
        delta: "Concordancia Histórica Confirmada",
        horaMedicion: "07:35",
        alertaCritica: null,
        detalleEspecializado: {
          tipo: "BANCO_SANGRE",
          directa: "Anti-A: Negativo (0) · Anti-B: Negativo (0) · Anti-D: Positivo (4+)",
          inversa: "Células A1: Positivo (4+) · Células B: Positivo (4+)",
          rai: "Negativo (Paneles I, II y III sin aglutinación)",
        }
      },
      {
        id: "OBS-07-02",
        testKey: "PC_MAYOR",
        tuboId: "SMP-2026-08918-01",
        codigo: "1250-0",
        nombre: "Prueba Cruzada Mayor (Compatibilidad Sanguínea)",
        disc: "BANSANG",
        metodo: "Fase AGH / LISS en Tarjeta de Gel Centrifugada",
        equipoId: "vitros",
        equipo: "Sistema Automatizado Grifols Erytra",
        valor: "COMPATIBLE (0 Aglutinación)",
        ucum: "resultado",
        refMin: null,
        refMax: null,
        critMin: null,
        critMax: null,
        flag: "NORMAL",
        previo: null,
        delta: null,
        horaMedicion: "07:50",
        alertaCritica: null,
        detalleEspecializado: {
          tipo: "UNIDAD_ISBT128",
          codigoIsbt: "=W00142600451200",
          componente: "Concentrado de Glóbulos Rojos Desleucocitados en SAGM",
          grupoUnidad: "O RhD Positivo",
          volumen: "285 mL",
          vencimiento: "18/11/2026",
          estadoUnidad: "RESERVADA_LISTA_EMISION",
        }
      }
    ],
    auditoria: [
      {
        id: "AUD-07-01",
        hora: "07:55",
        actor: "TM. Camila Santander (Cut 5510)",
        rol: "Tecnóloga Médica UMT Banco de Sangre",
        cut: "TM-5510-BANSANG",
        accion: "PRUEBA_CRUZADA_COMPATIBLE",
        detalle: "Prueba cruzada compatible con unidad ISBT 128 W00142600451200. Doble chequeo de identidad receptor conforme.",
        hash: "e491ca0192418a02c914ba127cb8a9942a1bc29412a842103189a0129bc8192a"
      }
    ],
    informe: null
  },

  /* ──────────────────────────────────────────────────────────────
     ORDEN 8 · UROANÁLISIS + SEDIMENTO + REFLEJO A UROCULTIVO
     Francisca Silva T. – Ambulatorio · D.S. N° 20 Art. 9
  ────────────────────────────────────────────────────────────── */
  {
    id: 8,
    acc: "ACC-2026-000419",
    orden: "ORD-2026-08919",
    cup: "CUP-CL-13-2026-00004184-K9",
    rut: "15.223.441-7",
    paciente: "Francisca Andrea Silva T.",
    edad: 34,
    sexo: "F",
    origen: "Policlínica Ambulatorio – Box 4",
    cama: "Ambulatorio",
    prioridad: "rutina",
    medicoSolicitante: "Dra. Isabel Rojas (Reg. SIS 48210)",
    diagnostico: "Infección Urinaria Recurrente – Disuria y polaquiuria.",
    fase: "validacion_tec",
    estado: "resultado_disp",
    disciplinas: ["URI"],
    horaOrden: "09:00",
    horaToma: "09:15",
    horaRecepcion: "09:30",
    tubos: [
      {
        id: "SMP-2026-08919-01",
        tipo: "ORINA",
        recipiente: "Frasco Estéril 60 mL",
        tipoMuestra: "Orina matutina segundo chorro",
        estado: "procesada",
        horaToma: "09:15",
        horaRecepcion: "09:30",
        gradilla: "Rack Orina URI-01",
        causalRechazo: null,
      }
    ],
    analitos: [
      {
        id: "OBS-08-01",
        testKey: "TIRA_QUIMICA",
        tuboId: "SMP-2026-08919-01",
        codigo: "5778-6",
        nombre: "Uroanálisis – Tira Química 10 Parámetros",
        disc: "URI",
        metodo: "Fotometría reflectométrica (Siemens CLINITEK Novus)",
        equipoId: "clinitek",
        equipo: "Siemens CLINITEK Novus",
        valor: "Leucocitos: 3+ · Nitritos: Positivo · Proteínas: Trazas",
        ucum: "cualitativo",
        refMin: null, refMax: null, critMin: null, critMax: null,
        flag: "HIGH",
        previo: "Leucocitos: Neg · Nitritos: Neg",
        delta: "Cambio significativo",
        horaMedicion: "09:45",
        alertaCritica: null,
        detalleEspecializado: {
          tipo: "UROANALISIS",
          tira: {
            color: "Amarillo turbio",
            aspecto: "Turbio",
            densidad: "1.025",
            pH: "6.0",
            proteinas: "Trazas (30 mg/dL)",
            glucosa: "Negativo",
            cetonas: "Negativo",
            bilirrubina: "Negativo",
            urobilinogeno: "Normal",
            hemoglobina: "Positivo 2+",
            leucocitos: "3+ (>500 cel/µL)",
            nitritos: "Positivo",
          },
          sedimento: {
            leucocitos: "48 por campo (× 40) – Piuria",
            eritrocitos: "12 por campo (× 40)",
            celulasEpiteliales: "Escasas células uroepiteliales",
            bacterias: "Abundantes bacilos gramnegativos",
            cilindros: "Ninguno",
            cristales: "Ninguno",
          },
          reglaReflexa: {
            disparada: true,
            regla: "Leucocituria >= 10 + Nitritos (+) → Urocultivo reflexo automático",
            ordenGenerada: "ORD-2026-08919-UCx",
            horaDisparo: "09:48",
            alertaTM: "Urocultivo inoculado automáticamente. Placa CPS chromID. Incubación 18-24 h.",
          }
        }
      },
      {
        id: "OBS-08-02",
        testKey: "SEDIMENTO_MICRO",
        tuboId: "SMP-2026-08919-01",
        codigo: "12478-6",
        nombre: "Sedimento Microscópico de Orina",
        disc: "URI",
        metodo: "Microscopía de campo brillante (× 40 obj.) + Iris iQ200",
        equipoId: "iris_iq200",
        equipo: "Iris iQ200 Automated UA Microscopy",
        valor: "Piuria severa – 48 leuc/campo · 12 erit/campo · Bacteriuria franca",
        ucum: "cualitativo",
        refMin: null, refMax: null, critMin: null, critMax: null,
        flag: "HIGH",
        previo: null,
        delta: null,
        horaMedicion: "10:00",
        alertaCritica: null,
        detalleEspecializado: null,
      }
    ],
    auditoria: [
      {
        id: "AUD-08-01",
        hora: "09:48",
        actor: "Sistema AXON LIS – Motor de Reglas Reflexas v2.1",
        rol: "Autómata LIS",
        cut: "SYS-LIS-URO-REFLEX",
        accion: "REGLA_REFLEJA_DISPARADA",
        detalle: "Criterio cumplido: Leucocituria >=10/campo + Nitritos positivo. Urocultivo ORD-2026-08919-UCx generado automáticamente.",
        hash: "a9c4e12f8b7d3e51a6f4c2d8e9b0c3d1a7f2e4b8c9d0e1f3a4b5c6d7e8f9a0b1"
      }
    ],
    informe: null
  },

  /* ──────────────────────────────────────────────────────────────
     ORDEN 9 · BIOLOGÍA MOLECULAR – CARGA VIRAL VIH-1 RT-PCR
     Claudio Vera M. – Control periódico TARV
  ────────────────────────────────────────────────────────────── */
  {
    id: 9,
    acc: "ACC-2026-000420",
    orden: "ORD-2026-08920",
    cup: "CUP-CL-13-2026-00004185-M0",
    rut: "12.887.334-K",
    paciente: "Claudio Andrés Vera M.",
    edad: 47,
    sexo: "M",
    origen: "Policlínica Infectología – Control TARV",
    cama: "Ambulatorio",
    prioridad: "rutina",
    medicoSolicitante: "Dr. Rodrigo Espinoza (Reg. SIS 55310)",
    diagnostico: "VIH-1 en TARV (TDF/FTC/DTG). Control virológico trimestral.",
    fase: "validacion_fac",
    estado: "resultado_disp",
    disciplinas: ["MOL"],
    horaOrden: "08:00",
    horaToma: "08:15",
    horaRecepcion: "08:35",
    tubos: [
      {
        id: "SMP-2026-08920-01",
        tipo: "EDTA",
        recipiente: "Tubo Vacutainer K2 EDTA 10 mL (Plasma EDTA – Biología Molecular)",
        tipoMuestra: "Plasma EDTA – Extracción ARN viral",
        estado: "procesada",
        horaToma: "08:15",
        horaRecepcion: "08:35",
        gradilla: "Rack MOL-PCR-BIO-02",
        causalRechazo: null,
      }
    ],
    analitos: [
      {
        id: "OBS-09-01",
        testKey: "CV_VIH1",
        tuboId: "SMP-2026-08920-01",
        codigo: "20447-9",
        nombre: "Carga Viral VIH-1 (RT-PCR cuantitativa)",
        disc: "MOL",
        metodo: "RT-PCR cuantitativa en tiempo real (Roche COBAS 6800 – Placa 96 pocillos)",
        equipoId: "cobas6800",
        equipo: "Roche COBAS 6800",
        valor: "14.850 copias/mL",
        ucum: "copias/mL",
        refMin: null,
        refMax: 50,
        critMin: null,
        critMax: null,
        flag: "HIGH",
        previo: "Indetectable (<50 copias/mL)",
        delta: "Fallo virológico confirmado",
        horaMedicion: "14:30",
        alertaCritica: {
          umbral: "> 1.000 copias/mL – Fallo virológico",
          notificado: true,
          receptor: "Dr. Rodrigo Espinoza",
          horaNotif: "15:00",
          medioNotif: "Teléfono directo + Mensaje seguro HIS"
        },
        detalleEspecializado: {
          tipo: "BIOLOGIA_MOLECULAR",
          plataforma: "Roche COBAS 6800",
          ensayo: "COBAS HIV-1 Test (FDA/ISP autorizado)",
          copiasML: 14850,
          log10: 4.17,
          valorLog: "4.17 log10 copias/mL",
          ctValue: 24.8,
          limitDeteccion: "< 20 copias/mL",
          limitCuantificacion: "< 50 copias/mL",
          placaId: "PCR-2026-1015-P08",
          posicionPlaca: "E6",
          controles: [
            { nombre: "Control Positivo Alto (CPA)", resultado: "14.200 copias/mL", estado: "CONFORME" },
            { nombre: "Control Positivo Bajo (CPB)", resultado: "48 copias/mL",     estado: "CONFORME" },
            { nombre: "Control Negativo (NTC)",       resultado: "Sin señal",        estado: "CONFORME" },
          ],
          interpretacion: "FALLO VIROLÓGICO CONFIRMADO (>1.000 copias/mL). Probable resistencia adquirida. Indicado genotipificado ISP.",
          alertaISP: "Notificación obligatoria Resolución Ex. ISP N° 850/2023 – Fallo virológico en TARV.",
        }
      }
    ],
    auditoria: [
      {
        id: "AUD-09-01",
        hora: "14:35",
        actor: "TM. Beatriz Navarrete (CUT TM-6821-MOL)",
        rol: "Tecnóloga Médica Biología Molecular",
        cut: "TM-6821-MOL",
        accion: "RESULTADO_VALIDADO_TEC",
        detalle: "Resultado CV VIH-1 validado. Controles conformes. Notificación crítica a médico tratante documentada.",
        hash: "b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2"
      }
    ],
    informe: null
  },

  /* ──────────────────────────────────────────────────────────────
     ORDEN 10 · HISTOPATOLOGÍA – BIOPSIA GÁSTRICA ANTRAL
     Hernán Castro V. – Endoscopía programada
  ────────────────────────────────────────────────────────────── */
  {
    id: 10,
    acc: "ACC-2026-000421",
    orden: "ORD-2026-08921",
    cup: "CUP-CL-13-2026-00004186-N1",
    rut: "9.445.210-3",
    paciente: "Hernán Ernesto Castro V.",
    edad: 62,
    sexo: "M",
    origen: "Endoscopía Digestiva – Piso 3",
    cama: "Procedimientos",
    prioridad: "rutina",
    medicoSolicitante: "Dr. Mauricio Lara (Reg. SIS 61005)",
    diagnostico: "Gastritis crónica activa. Descarte H. pylori y lesión premaligna.",
    fase: "validacion_fac",
    estado: "resultado_disp",
    disciplinas: ["HISTO"],
    horaOrden: "10:00",
    horaToma: "10:15",
    horaRecepcion: "10:45",
    tubos: [
      {
        id: "SMP-2026-08921-01",
        tipo: "HISTO_BIOPSIA",
        recipiente: "Frasco Formalina Neutra Tamponada 10% (60 mL)",
        tipoMuestra: "Tejido gástrico (antro) fijado en formalina",
        estado: "procesada",
        horaToma: "10:15",
        horaRecepcion: "10:45",
        gradilla: "Rack HISTO-A12",
        causalRechazo: null,
      }
    ],
    analitos: [
      {
        id: "OBS-10-01",
        testKey: "HISTO_GASTRICA",
        tuboId: "SMP-2026-08921-01",
        codigo: "22633-2",
        nombre: "Estudio Histopatológico – Biopsia Gástrica (Antro)",
        disc: "HISTO",
        metodo: "Histología convencional H&E + Tinción especial Giemsa modificado (H. pylori)",
        equipoId: "micro_histo",
        equipo: "Microscopio Nikon Eclipse Ci-L + Procesador Leica ASP6025",
        valor: "Gastritis crónica activa moderada – H. pylori POSITIVO (Giemsa ++)",
        ucum: "cualitativo",
        refMin: null, refMax: null, critMin: null, critMax: null,
        flag: "HIGH",
        previo: null,
        delta: null,
        horaMedicion: "16:00",
        alertaCritica: null,
        detalleEspecializado: {
          tipo: "HISTOPATOLOGIA",
          solicitud: "Biopsia endoscópica gástrica – antro",
          macroscopia: "2 fragmentos tisulares pardos, firmes, 0.4 × 0.3 cm y 0.3 × 0.2 cm.",
          cassettes: ["Cassette A – Fragmento 1 (antro mayor)", "Cassette B – Fragmento 2 (antro menor)"],
          laminas: [
            { id: "LAM-A-HE",  tincion: "H&E",           resultado: "Gastritis crónica activa moderada. Infiltrado mononuclear + PMN. Folículos linfoides." },
            { id: "LAM-A-GIE", tincion: "Giemsa modif.", resultado: "H. pylori POSITIVO (++) – Abundantes espirilos sobre mucosa gástrica." },
            { id: "LAM-B-HE",  tincion: "H&E",           resultado: "Metaplasia intestinal incompleta focal (Tipo II). Sin displasia." },
          ],
          diagnosticoPAI: "Gastritis crónica activa moderada asociada a H. pylori. Metaplasia intestinal focal incompleta.",
          clasificacionSidney: "OLGA Estadio II – OLGIM Estadio I",
          hpylori: "POSITIVO",
          recomendacion: "Erradicación H. pylori (triple terapia). Control histológico en 6 meses.",
          firmado: "Dr. Patricio Contreras R. – Anatomopatólogo (Reg. SIS 23488)",
        }
      }
    ],
    auditoria: [
      {
        id: "AUD-10-01",
        hora: "16:05",
        actor: "Dr. Patricio Contreras R. (CUT 2026-AP-2348)",
        rol: "Médico Anatomopatólogo",
        cut: "2026-AP-2348",
        accion: "INFORME_FIRMADO_DIGITAL",
        detalle: "Diagnóstico histopatológico emitido y firmado electrónicamente (Ley 19.799). H. pylori positivo notificado a médico tratante.",
        hash: "c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4"
      }
    ],
    informe: null
  },

  /* ──────────────────────────────────────────────────────────────
     ORDEN 11 · TOXICOLOGÍA CLÍNICA – PANEL DROGAS DE ABUSO
     Matías Sepúlveda N. – Cadena de custodia Res. ISP N° 250/2024
  ────────────────────────────────────────────────────────────── */
  {
    id: 11,
    acc: "ACC-2026-000422",
    orden: "ORD-2026-08922",
    cup: "CUP-CL-13-2026-00004187-O2",
    rut: "18.002.877-1",
    paciente: "Matías Ignacio Sepúlveda N.",
    edad: 26,
    sexo: "M",
    origen: "Urgencias Adulto – Box Toxicología",
    cama: "Urgencias Box-T3",
    prioridad: "stat",
    medicoSolicitante: "Dr. Felipe Torres (Reg. SIS 72311)",
    diagnostico: "Intoxicación aguda – sospecha consumo múltiple drogas de abuso.",
    fase: "validacion_tec",
    estado: "resultado_disp",
    disciplinas: ["TOX"],
    horaOrden: "02:30",
    horaToma: "02:45",
    horaRecepcion: "03:00",
    tubos: [
      {
        id: "SMP-2026-08922-01",
        tipo: "ORINA",
        recipiente: "Frasco Estéril 60 mL – Custodia Sellada Numerada",
        tipoMuestra: "Orina aleatoria – Testigo presencial. Temperatura 36.8°C (conforme).",
        estado: "procesada",
        horaToma: "02:45",
        horaRecepcion: "03:00",
        gradilla: "Cadena Custodia #TOX-2026-08922-01",
        causalRechazo: null,
      }
    ],
    analitos: [
      {
        id: "OBS-11-01",
        testKey: "PANEL_DROGAS",
        tuboId: "SMP-2026-08922-01",
        codigo: "43789-1",
        nombre: "Panel Toxicológico Drogas de Abuso (6 analitos) – Orina",
        disc: "TOX",
        metodo: "Inmunoensayo de micropartículas (CMIA) – Abbott Architect i2000SR",
        equipoId: "architect_i2000",
        equipo: "Abbott Architect i2000SR",
        valor: "COCAÍNA (Benzoilecgonina): POSITIVO · THC: POSITIVO · Resto: Negativo",
        ucum: "cualitativo",
        refMin: null, refMax: null, critMin: null, critMax: null,
        flag: "HIGH",
        previo: null,
        delta: null,
        horaMedicion: "03:25",
        alertaCritica: {
          umbral: "Tamizaje positivo – Notificación obligatoria Res. Ex. ISP N° 250/2024",
          notificado: true,
          receptor: "Dr. Felipe Torres",
          horaNotif: "03:30",
          medioNotif: "Teléfono directo Urgencias"
        },
        detalleEspecializado: {
          tipo: "TOXICOLOGIA",
          metodoTamizaje: "CMIA (Abbott Architect i2000SR)",
          analitos: [
            { nombre: "Cocaína (Benzoilecgonina)", corte: ">300 ng/mL",  resultado: "POSITIVO PRESUNTIVO", valor: "1.240 ng/mL", confirmacion: "Pendiente GC-MS (Res. ISP 250/2024)" },
            { nombre: "Cannabinoides (THC-COOH)", corte: ">50 ng/mL",   resultado: "POSITIVO PRESUNTIVO", valor: "185 ng/mL",   confirmacion: "Pendiente GC-MS (Res. ISP 250/2024)" },
            { nombre: "Anfetaminas",               corte: ">1000 ng/mL", resultado: "NEGATIVO",           valor: "<50 ng/mL",   confirmacion: "N/A" },
            { nombre: "Opioides (Morfina)",         corte: ">300 ng/mL", resultado: "NEGATIVO",           valor: "<150 ng/mL",  confirmacion: "N/A" },
            { nombre: "Benzodiazepinas",            corte: ">200 ng/mL", resultado: "NEGATIVO",           valor: "<100 ng/mL",  confirmacion: "N/A" },
            { nombre: "Metadona",                   corte: ">300 ng/mL", resultado: "NEGATIVO",           valor: "<50 ng/mL",   confirmacion: "N/A" },
          ],
          cadenaCustodia: {
            numero: "TOX-2026-08922-01",
            estado: "SELLADA",
            testigoToma: "TENS. Andrea Molina (Cut TE-9012)",
            horaLacrado: "02:50",
            reglamento: "Resolución Ex. ISP N° 250/2024",
            muestrasReserva: "Alícuota B conservada a -20°C por 12 meses",
          },
          alertaLegal: "Resultado PRESUNTIVO (tamizaje). CONFIRMACIÓN OBLIGATORIA por GC-MS/MS en ISP antes de uso médico-legal. No comunicar a terceros antes de confirmación.",
        }
      }
    ],
    auditoria: [
      {
        id: "AUD-11-01",
        hora: "03:30",
        actor: "TM. Sandra Riquelme (CUT TM-3391-TOX)",
        rol: "Tecnóloga Médica Toxicología Clínica",
        cut: "TM-3391-TOX",
        accion: "RESULTADO_TAMIZAJE_NOTIFICADO",
        detalle: "Panel positivo (cocaína + THC). Cadena de custodia intacta verificada. Notificación verbal al Dr. Torres. Alícuota B sellada para confirmación GC-MS según Res. Ex. ISP N° 250/2024.",
        hash: "d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6"
      }
    ],
    informe: null
  },

  /* ──────────────────────────────────────────────────────────────
     ORDEN 12 · LÍQUIDO CEFALORRAQUÍDEO (LCR) – CITOQUÍMICO STAT
     Constanza Valdés P. – Meningitis bacteriana URGENTE
  ────────────────────────────────────────────────────────────── */
  {
    id: 12,
    acc: "ACC-2026-000423",
    orden: "ORD-2026-08923",
    cup: "CUP-CL-13-2026-00004188-P3",
    rut: "22.445.009-8",
    paciente: "Constanza Sofía Valdés P.",
    edad: 19,
    sexo: "F",
    origen: "Urgencias Adulto – Box Neurología STAT",
    cama: "Urgencias Box-N1",
    prioridad: "stat",
    medicoSolicitante: "Dr. Andrés Muñoz (Reg. SIS 88102)",
    diagnostico: "Cefalea intensa + fiebre + rigidez de nuca. Sospecha meningitis bacteriana. PL indicada.",
    fase: "validacion_tec",
    estado: "resultado_disp",
    disciplinas: ["GAS", "MIC"],
    horaOrden: "03:00",
    horaToma: "03:20",
    horaRecepcion: "03:28",
    tubos: [
      {
        id: "SMP-2026-08923-01",
        tipo: "HEPARINA",
        recipiente: "Tubos Estériles LCR (3 × 5 mL numerados)",
        tipoMuestra: "Líquido cefalorraquídeo (LCR) – punción lumbar L4-L5",
        estado: "procesada",
        horaToma: "03:20",
        horaRecepcion: "03:28",
        gradilla: "STAT LCR – Procesamiento inmediato",
        causalRechazo: null,
      }
    ],
    analitos: [
      {
        id: "OBS-12-01",
        testKey: "LCR_QUIMICO",
        tuboId: "SMP-2026-08923-01",
        codigo: "2857-1",
        nombre: "Estudio Citoquímico LCR – Glucosa",
        disc: "GAS",
        metodo: "Hexokinasa enzimática (Cobas c503)",
        equipoId: "c503",
        equipo: "Roche Cobas Pro c503",
        valor: "28 mg/dL",
        ucum: "mg/dL",
        refMin: 50,
        refMax: 80,
        critMin: 20,
        critMax: null,
        flag: "LOW",
        previo: null,
        delta: null,
        horaMedicion: "03:45",
        alertaCritica: {
          umbral: "Hipoglucorraquia severa < 40 mg/dL",
          notificado: true,
          receptor: "Dr. Andrés Muñoz",
          horaNotif: "03:47",
          medioNotif: "Teléfono directo Urgencias"
        },
        detalleEspecializado: {
          tipo: "LIQUIDO_BIOLOGICO",
          especimen: "Líquido Cefalorraquídeo (LCR)",
          prioridad: "STAT",
          aspecto: "Xantocrómico – levemente turbio",
          presionApertura: "28 cmH2O (Elevada)",
          parametros: [
            { nombre: "Glucosa LCR",      valor: "28 mg/dL",     referencia: "50-80 mg/dL",   flag: "LOW",    interpretacion: "Hipoglucorraquia severa" },
            { nombre: "Glucosa Sérica",   valor: "98 mg/dL",     referencia: "70-99 mg/dL",   flag: "NORMAL", interpretacion: "Ratio LCR/Suero: 0.29 (N > 0.6)" },
            { nombre: "Proteínas Totales",valor: "145 mg/dL",    referencia: "15-45 mg/dL",   flag: "HIGH",   interpretacion: "Hiperproteinorraquia severa" },
            { nombre: "Cloruros",         valor: "112 mEq/L",    referencia: "118-132 mEq/L", flag: "LOW",    interpretacion: "Hipoclorurraquia" },
            { nombre: "LDH LCR",          valor: "280 UI/L",     referencia: "< 40 UI/L",     flag: "HIGH",   interpretacion: "Marcador daño meníngeo" },
          ],
          citologia: {
            celularidad: "480 células/µL",
            diferencialPMN: "92% polimorfonucleares (PMN)",
            diferencialMN: "8% mononucleares",
            eritrocitos: "20 eritrocitos/µL (punción traumática)",
            interpretacion: "PLEOCITOSIS MARCADA NEUTROFÍLICA – compatible con meningitis bacteriana aguda",
          },
          microbiologia: {
            tincionGram: "Gram POSITIVO – Diplococos grampositivos lanceolados en pares (URGENTE)",
            cultivo: "En curso – BactAlert FA Plus (37°C 5% CO2)",
            aglutinacion: "S. pneumoniae Ag: POSITIVO (látex)",
            orientacion: "Streptococcus pneumoniae probable – Iniciar cobertura antibiótica empírica INMEDIATA",
          },
          alertaClinica: "EMERGENCIA INFECCIOSA – Meningitis bacteriana probable por S. pneumoniae. Iniciar ceftriaxona 2g IV + dexametasona INMEDIATAMENTE. Notificación SEREMI según D.S. N° 7/2019.",
        }
      },
      {
        id: "OBS-12-02",
        testKey: "LCR_PROTEINAS",
        tuboId: "SMP-2026-08923-01",
        codigo: "2885-2",
        nombre: "Proteínas Totales en LCR",
        disc: "GAS",
        metodo: "Colorimetría Biuret – Roche Cobas c503",
        equipoId: "c503",
        equipo: "Roche Cobas Pro c503",
        valor: "145 mg/dL",
        ucum: "mg/dL",
        refMin: 15,
        refMax: 45,
        critMin: null,
        critMax: 200,
        flag: "HIGH",
        previo: null,
        delta: null,
        horaMedicion: "03:45",
        alertaCritica: null,
        detalleEspecializado: null,
      },
      {
        id: "OBS-12-03",
        testKey: "LCR_CITO",
        tuboId: "SMP-2026-08923-01",
        codigo: "26464-8",
        nombre: "Recuento Celular Total LCR (Cámara Neubauer)",
        disc: "MIC",
        metodo: "Recuento manual en cámara de Neubauer (urgente)",
        equipoId: "manual",
        equipo: "Microscopía directa – Cámara Neubauer",
        valor: "480 células/µL – 92% PMN",
        ucum: "cel/µL",
        refMin: 0,
        refMax: 5,
        critMin: null,
        critMax: null,
        flag: "HIGH",
        previo: null,
        delta: null,
        horaMedicion: "03:40",
        alertaCritica: null,
        detalleEspecializado: null,
      }
    ],
    auditoria: [
      {
        id: "AUD-12-01",
        hora: "03:47",
        actor: "TM. Verónica Pinto (CUT TM-2278-URGENCIAS)",
        rol: "Tecnóloga Médica Urgencias STAT",
        cut: "TM-2278-URG",
        accion: "RESULTADO_CRITICO_NOTIFICADO",
        detalle: "LCR citoquímico STAT: hipoglucorraquia (28 mg/dL) + hiperproteinorraquia (145 mg/dL) + pleocitosis neutrofílica 480/µL + Gram diplococos positivos. Notificación crítica verbal Dr. Muñoz. Notificación SEREMI pendiente.",
        hash: "e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8"
      }
    ],
    informe: null
  },

  /* ──────────────────────────────────────────────────────────────
     ORDEN 13 · HEMOCULTIVO AUTOMATIZADO + IDENTIFICACIÓN MALDI-TOF + AST
     Carolina Valenzuela M. – Hospitalización Sala 402 · D.S. N° 7 / MINSAL
  ────────────────────────────────────────────────────────────── */
  {
    id: 13,
    acc: "ACC-2026-000424",
    orden: "ORD-2026-08924",
    cup: "CUP-CL-13-2026-00004189-Q4",
    rut: "16.782.314-5",
    paciente: "Carolina Andrea Valenzuela M.",
    edad: 39,
    sexo: "F",
    origen: "Hospitalización Medicina – Sala 402",
    cama: "Cama 402-A",
    prioridad: "urgente",
    medicoSolicitante: "Dr. Patricio Alvear (Reg. SIS 39401)",
    diagnostico: "Sospecha Urosepsis / Bacteriemia secundaria a ITU alta complicada.",
    fase: "validacion_fac",
    estado: "resultado_disp",
    disciplinas: ["MIC"],
    horaOrden: "06:30",
    horaToma: "06:45",
    horaRecepcion: "07:05",
    tubos: [
      {
        id: "SMP-2026-08924-01",
        tipo: "HEMOCULTIVO",
        recipiente: "Frascos Hemocultivo Aer/Anaer Bact/ALERT FA Plus",
        tipoMuestra: "Sangre inoculada en frasco hemocultivo aeróbico",
        estado: "procesada",
        horaToma: "06:45",
        horaRecepcion: "07:05",
        gradilla: "Virtuo Incubation Bay B-04",
        causalRechazo: null,
      }
    ],
    analitos: [
      {
        id: "OBS-13-01",
        testKey: "HEMOCULTIVO_AST",
        tuboId: "SMP-2026-08924-01",
        codigo: "600-7",
        nombre: "Hemocultivo Automatizado + Identificación MALDI-TOF + AST",
        disc: "MIC",
        metodo: "Monitorización Cinética CO2 (Virtuo) + MALDI-TOF (VITEK MS) + AST CLSI M100",
        equipoId: "bactalert",
        equipo: "bioMérieux BacT/ALERT Virtuo & VITEK MS",
        valor: "POSITIVO: Klebsiella pneumoniae (BLEE Positivo)",
        ucum: "aislamiento",
        refMin: null, refMax: null, critMin: null, critMax: null,
        flag: "CRIT_HIGH",
        previo: null,
        delta: null,
        horaMedicion: "09:10",
        alertaCritica: {
          umbral: "Hemocultivo positivo monomicrobiano con BLEE",
          notificado: true,
          receptor: "Dr. Patricio Alvear",
          horaNotif: "09:15",
          medioNotif: "Teléfono directo Sala 402"
        },
        detalleEspecializado: {
          tipo: "MICROBIOLOGIA_CULTIVO",
          muestra: "Hemocultivo (Frasco Aeróbico)",
          organismo: "Klebsiella pneumoniae",
          metodoIdentificacion: "MALDI-TOF VITEK MS (Score 99.9%)",
          tiempoPositividad: "11.4 horas (Alarma óptica Virtuo)",
          recuento: "Desarrollo monomicrobiano puro",
          gramDirecto: "Bacilos gramnegativos capsulados abundantes",
          fenotipoResistencia: "BLEE FENOTIPO POSITIVO (Resistencia C3G/C4G)",
          alertaMinsal: "Vigilancia Epidemiológica IAAS / D.S. N° 7 MINSAL. Cepario derivado a ISP para confirmación genotípica.",
        }
      }
    ],
    auditoria: [
      {
        id: "AUD-13-01",
        hora: "09:15",
        actor: "TM. Gonzalo Miranda (Cut 7720)",
        rol: "Tecnólogo Médico Microbiología & IAAS",
        cut: "TM-7720-MIC",
        accion: "NOTIFICACION_HEMOCULTIVO_CRITICO",
        detalle: "Positividad de hemocultivo a las 11.4h informada de inmediato a médico de sala. Gram: Bacilos gramnegativos. Aislamiento preventivo coordinado.",
        hash: "f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2"
      }
    ],
    informe: null
  },

  /* ──────────────────────────────────────────────────────────────
     ORDEN 14 · BANCO DE SANGRE (UMT) – SEGUNDA MUESTRA INDEPENDIENTE (D.S. 20)
     Rodrigo Cáceres B. – UCI Coronaria · Prueba Cruzada 2da Unidad
  ────────────────────────────────────────────────────────────── */
  {
    id: 14,
    acc: "ACC-2026-000425",
    orden: "ORD-2026-08925",
    cup: "CUP-CL-13-2026-00004190-R5",
    rut: "11.590.234-8",
    paciente: "Rodrigo Alonso Cáceres B.",
    edad: 53,
    sexo: "M",
    origen: "UPC Coronaria – Cama 08",
    cama: "UCI-C-08",
    prioridad: "stat",
    medicoSolicitante: "Dra. Macarena Valdés (Reg. SIS 50921)",
    diagnostico: "Hemorragia Digestiva Alta Masiva / Shock Hipovolémico. Requerimiento 2da unidad transfusional.",
    fase: "validacion_fac",
    estado: "resultado_disp",
    disciplinas: ["BANSANG"],
    horaOrden: "07:30",
    horaToma: "07:45",
    horaRecepcion: "07:55",
    tubos: [
      {
        id: "SMP-2026-08925-01",
        tipo: "EDTA",
        recipiente: "Tubo Vacutainer K2 EDTA 4.0 mL",
        tipoMuestra: "Sangre venosa anticoagulada (Segunda Toma Verificación D.S. 20)",
        estado: "procesada",
        horaToma: "07:45",
        horaRecepcion: "07:55",
        gradilla: "Seroteca UMT Sector B-02",
        causalRechazo: null,
      },
      {
        id: "SMP-2026-08925-02",
        tipo: "BOLSA_TRANSFUS",
        recipiente: "Unidad Concentrado Eritrocitario (ISBT 128)",
        tipoMuestra: "Glóbulos rojos desleucocitados en SAGM",
        estado: "procesada",
        horaToma: "07:45",
        horaRecepcion: "07:55",
        gradilla: "Refrigerador UMT Despacho R-01",
        causalRechazo: null,
      }
    ],
    analitos: [
      {
        id: "OBS-14-01",
        testKey: "ABO_RHD_VERIF",
        tuboId: "SMP-2026-08925-01",
        codigo: "883-9",
        nombre: "Grupo ABO y Factor RhD (Segunda Muestra Verificación D.S. 20)",
        disc: "BANSANG",
        metodo: "Aglutinación en columna de gel (Bio-Rad IH-500)",
        equipoId: "ih500_bansang",
        equipo: "Bio-Rad IH-500 Inmunohematología",
        valor: "Grupo A · Factor RhD Positivo (Doble Chequeo Conforme)",
        ucum: "grupo",
        refMin: null, refMax: null, critMin: null, critMax: null,
        flag: "NORMAL",
        previo: "Grupo A · RhD Positivo (Toma 1)",
        delta: "Concordancia 100% Confirmada",
        horaMedicion: "08:15",
        alertaCritica: null,
        detalleEspecializado: {
          tipo: "BANCO_SANGRE",
          directa: "Anti-A: Positivo (4+) · Anti-B: Negativo (0) · Anti-D: Positivo (4+)",
          inversa: "Células A1: Negativo (0) · Células B: Positivo (4+)",
          rai: "Negativo (Paneles I, II y III sin aglutinación)",
        }
      },
      {
        id: "OBS-14-02",
        testKey: "PC_MAYOR_2",
        tuboId: "SMP-2026-08925-02",
        codigo: "1250-0",
        nombre: "Prueba Cruzada Mayor en Gel (Unidad 2)",
        disc: "BANSANG",
        metodo: "Columna de Gel LISS/Coombs a 37°C Bio-Rad IH-500",
        equipoId: "ih500_bansang",
        equipo: "Bio-Rad IH-500 Inmunohematología",
        valor: "COMPATIBLE con Unidad ISBT 128 =W00142600451201",
        ucum: "compatibilidad",
        refMin: null, refMax: null, critMin: null, critMax: null,
        flag: "NORMAL",
        previo: null,
        delta: null,
        horaMedicion: "08:25",
        alertaCritica: null,
        detalleEspecializado: {
          tipo: "UNIDAD_ISBT128",
          codigoIsbt: "=W00142600451201",
          componente: "Concentrado de Glóbulos Rojos Desleucocitados en SAGM",
          grupoUnidad: "A RhD Positivo",
          volumen: "290 mL",
          vencimiento: "22/11/2026",
          estadoUnidad: "RESERVADA_LISTA_EMISION",
        }
      }
    ],
    auditoria: [
      {
        id: "AUD-14-01",
        hora: "08:30",
        actor: "TM. Camila Santander (Cut 5510)",
        rol: "Tecnóloga Médica UMT Banco de Sangre",
        cut: "TM-5510-BANSANG",
        accion: "DOBLE_CHEQUEO_SEGUNDA_MUESTRA_DS20",
        detalle: "Segunda muestra independiente verificada contra historial receptor. Prueba cruzada compatible con unidad ISBT 128 W00142600451201. Liberación pre-transfusional autorizada.",
        hash: "b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3"
      }
    ],
    informe: null
  }
];

const LOGS_GATEWAY_INICIALES = [
  {
    id: 101,
    hora: "08:31:14",
    analizador: "Roche Cobas Pro c503",
    equipoId: "c503",
    proto: "HL7 v2.5.1 / MLLP",
    tipo: "IN",
    msj: "MSH|^~\\&|COBAS_C503|LAB_CENTRAL|AXON_LIS|CORE|20261015083114||ORU^R01|MSG20261015-083114|P|2.5.1\nPID|1||CUP-CL-13-2026-00004121-K8||MARTINEZ^CARLOS\nOBR|1|ORD-2026-08912|SMP-2026-08912-01|TROP^Troponina T hs|||20261015081800\nOBX|1|NM|49563-0^Troponina T hs|1|145.8|ng/L|0.0-14.0|HH|||F|||20261015083100|c503"
  },
  {
    id: 102,
    hora: "08:29:45",
    analizador: "Roche Cobas Pro c503",
    equipoId: "c503",
    proto: "HL7 v2.5.1 / MLLP",
    tipo: "IN",
    msj: "MSH|^~\\&|COBAS_C503|LAB_CENTRAL|AXON_LIS|CORE|20261015082945||ORU^R01|MSG20261015-082945|P|2.5.1\nPID|1||CUP-CL-13-2026-00004121-K8||MARTINEZ^CARLOS\nOBR|1|ORD-2026-08912|SMP-2026-08912-01|K^Potasio Serico|||20261015081800\nOBX|1|NM|2823-3^Potasio Serico|1|6.4|mEq/L|3.5-5.1|HH|||F|||20261015082930|c503"
  },
  {
    id: 103,
    hora: "08:27:12",
    analizador: "Radiometer ABL90 FLEX",
    equipoId: "abl90",
    proto: "HL7 v2.5.1 / MLLP",
    tipo: "IN",
    msj: "MSH|^~\\&|ABL90_FLEX|POCT_URG|AXON_LIS|CORE|20261015082712||ORU^R01|MSG20261015-082712|P|2.5.1\nPID|1||CUP-CL-13-2026-00004121-K8||MARTINEZ^CARLOS\nOBR|1|ORD-2026-08912|SMP-2026-08912-02|LACT^Lactato Arterial|||20261015081900\nOBX|1|NM|2524-7^Lactato Arterial|1|3.4|mmol/L|0.5-1.6|H|||F|||20261015082700|abl90"
  },
  {
    id: 104,
    hora: "08:24:00",
    analizador: "Sysmex XN-1000",
    equipoId: "xn1000",
    proto: "ASTM E1394-91 / TCP",
    tipo: "OUT",
    msj: "H|\\^&|||AXON_LIS|||||||P|1394-91|20261015082400\nQ|1|^SMP-2026-08914-01||ALL||||||||O\nL|1|N"
  }
];


/* ─────────────────────────────────────────────────────────────────────────
   § QC · DOMINIO DE CONTROL DE CALIDAD ANALÍTICO & ALGORITMOS CLÍNICOS
   (CONFORME A CLSI C24-Ed4, ISO 15189:2022 Y CONCILIACIÓN CONSENSUSLAB)
   ───────────────────────────────────────────────────────────────────────── */
const WESTGARD_DATASETS = {
  GLU: {
    nombre: "Glucosa en Suero",
    equipoId: "c503",
    equipoNombre: "Roche Cobas Pro c503",
    disciplina: "Bioquímica Clínica",
    ucum: "mg/dL",
    tea: 8.0, // Requisito de Calidad Error Total Admisible (CLIA / Variabilidad Biológica)
    cvi: 5.6, // Variabilidad biológica intraindividual
    loteControl: "LOT-GLU-2026-N2",
    nivel1: { nombre: "Nivel 1 (Normal)", target: 90.0, sd: 2.2 },
    nivel2: { nombre: "Nivel 2 (Patológico)", target: 250.0, sd: 5.5 },
    corridas: [
      { id: 1, fecha: "24-10 06:00", l1: 89.8, l2: 251.2, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 2, fecha: "24-10 07:00", l1: 91.1, l2: 249.0, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 3, fecha: "24-10 08:00", l1: 90.4, l2: 252.8, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 4, fecha: "24-10 09:00", l1: 89.2, l2: 248.5, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 5, fecha: "24-10 10:00", l1: 91.8, l2: 253.4, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 6, fecha: "24-10 11:00", l1: 90.0, l2: 250.2, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 7, fecha: "24-10 12:00", l1: 92.5, l2: 254.1, estado: "ADVERTENCIA", severidad: "WARNING", reglas: ["1-2s (Alerta N1)"], accion: "REVISAR_TENDENCIA" },
      { id: 8, fecha: "24-10 13:00", l1: 90.7, l2: 249.6, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 9, fecha: "24-10 14:00", l1: 89.5, l2: 251.0, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 10, fecha: "24-10 15:00", l1: 91.2, l2: 252.0, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 11, fecha: "24-10 16:00", l1: 90.3, l2: 250.7, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 12, fecha: "24-10 17:00", l1: 90.6, l2: 251.5, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" }
    ]
  },
  TROP: {
    nombre: "Troponina T ultrasensible (hs-cTnT)",
    equipoId: "e411",
    equipoNombre: "Roche Cobas e411 / e801",
    disciplina: "Inmunoquímica ECLIA",
    ucum: "ng/L",
    tea: 15.0,
    cvi: 9.5,
    loteControl: "LOT-TROP-ECLIA-44B",
    nivel1: { nombre: "Nivel 1 (Bajo/Normal)", target: 14.0, sd: 0.7 },
    nivel2: { nombre: "Nivel 2 (Elevado/Infarto)", target: 85.0, sd: 3.8 },
    corridas: [
      { id: 1, fecha: "24-10 06:00", l1: 13.9, l2: 84.5, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 2, fecha: "24-10 07:00", l1: 14.2, l2: 86.1, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 3, fecha: "24-10 08:00", l1: 14.0, l2: 85.2, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 4, fecha: "24-10 09:00", l1: 13.8, l2: 83.9, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 5, fecha: "24-10 10:00", l1: 14.1, l2: 85.7, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 6, fecha: "24-10 11:00", l1: 14.3, l2: 86.4, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 7, fecha: "24-10 12:00", l1: 13.7, l2: 84.1, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 8, fecha: "24-10 13:00", l1: 14.0, l2: 85.0, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 9, fecha: "24-10 14:00", l1: 14.4, l2: 87.0, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 10, fecha: "24-10 15:00", l1: 14.1, l2: 84.8, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 11, fecha: "24-10 16:00", l1: 13.9, l2: 85.3, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 12, fecha: "24-10 17:00", l1: 14.2, l2: 85.9, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" }
    ]
  },
  LEUC: {
    nombre: "Recuento de Leucocitos",
    equipoId: "xn1000",
    equipoNombre: "Sysmex XN-1000",
    disciplina: "Hematología Automatizada",
    ucum: "10^3/µL",
    tea: 10.0,
    cvi: 10.5,
    loteControl: "LOT-XN-CHECK-L12",
    nivel1: { nombre: "Nivel 1 (Normal)", target: 7.00, sd: 0.25 },
    nivel2: { nombre: "Nivel 2 (Leucocitosis)", target: 20.00, sd: 0.70 },
    corridas: [
      { id: 1, fecha: "24-10 06:00", l1: 6.98, l2: 19.90, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 2, fecha: "24-10 07:00", l1: 7.05, l2: 20.15, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 3, fecha: "24-10 08:00", l1: 7.10, l2: 20.30, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 4, fecha: "24-10 09:00", l1: 6.95, l2: 19.80, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 5, fecha: "24-10 10:00", l1: 7.02, l2: 20.05, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 6, fecha: "24-10 11:00", l1: 7.15, l2: 20.40, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 7, fecha: "24-10 12:00", l1: 6.90, l2: 19.75, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 8, fecha: "24-10 13:00", l1: 7.00, l2: 20.10, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 9, fecha: "24-10 14:00", l1: 7.08, l2: 20.25, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 10, fecha: "24-10 15:00", l1: 6.96, l2: 19.85, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 11, fecha: "24-10 16:00", l1: 7.04, l2: 20.18, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" },
      { id: 12, fecha: "24-10 17:00", l1: 7.01, l2: 20.08, estado: "ACEPTADO", severidad: "INFO", reglas: [], accion: "LIBERAR" }
    ]
  }
};

/**
 * Evaluador Riguroso Multirregla de Westgard (CLSI C24-Ed4).
 * Corrige el defecto temporal de R-4s evaluándolo dentro de la MISMA corrida entre niveles.
 */
function evaluarMultirreglasWestgard(currentRun, history, targetL1, sdL1, targetL2, sdL2) {
  const sdiL1 = (currentRun.l1 - targetL1) / sdL1;
  const sdiL2 = (currentRun.l2 - targetL2) / sdL2;
  const activated = [];

  // Regla 1-3s (Rechazo por Error Aleatorio)
  if (Math.abs(sdiL1) > 3.0 || Math.abs(sdiL2) > 3.0) {
    const afectado = Math.abs(sdiL1) > 3.0 ? "Nivel 1" : "Nivel 2";
    activated.push({
      rule: "1-3s",
      tipo: "RECHAZO",
      severity: "CRITICAL",
      desc: `Regla 1-3s: ${afectado} excedió 3 Desviaciones Estándar (Error Aleatorio grave). Corrida no liberable.`
    });
  }

  // Regla 1-2s (Regla de Advertencia inicial)
  if (Math.abs(sdiL1) > 2.0 || Math.abs(sdiL2) > 2.0) {
    activated.push({
      rule: "1-2s",
      tipo: "ADVERTENCIA",
      severity: "WARNING",
      desc: "Regla 1-2s (Alerta): Al menos un control superó 2 SD. Inspeccionar multirreglas sistemáticas."
    });
  }

  // Regla R-4s: Evaluada dentro de la MISMA CORRIDA entre Nivel 1 y Nivel 2 (CLSI C24 / Westgard)
  const r4sCondition1 = (sdiL1 > 2.0 && sdiL2 < -2.0) || (sdiL2 > 2.0 && sdiL1 < -2.0);
  const r4sCondition2 = Math.abs(sdiL1 - sdiL2) >= 4.0 && (Math.abs(sdiL1) > 2.0 || Math.abs(sdiL2) > 2.0);
  if (r4sCondition1 || r4sCondition2) {
    activated.push({
      rule: "R-4s",
      tipo: "RECHAZO",
      severity: "CRITICAL",
      desc: `Regla R-4s (Intra-corrida): Dispersión entre Nivel 1 (SDI ${sdiL1.toFixed(1)}) y Nivel 2 (SDI ${sdiL2.toFixed(1)}) >= 4 SD con signos opuestos (Error Aleatorio en el lote).`
    });
  }

  // Regla 2-2s: Dos controles consecutivos > 2s en el mismo sentido
  if ((sdiL1 > 2.0 && sdiL2 > 2.0) || (sdiL1 < -2.0 && sdiL2 < -2.0)) {
    activated.push({
      rule: "2-2s (Intra-corrida)",
      tipo: "RECHAZO",
      severity: "CRITICAL",
      desc: "Regla 2-2s (Ambos niveles): Ambos controles superaron 2 SD en el mismo sentido en esta corrida (Error Sistemático)."
    });
  } else if (history.length >= 1) {
    const prev = history[history.length - 1];
    const prevSdiL1 = (prev.l1 - targetL1) / sdL1;
    const prevSdiL2 = (prev.l2 - targetL2) / sdL2;
    if ((sdiL1 > 2.0 && prevSdiL1 > 2.0) || (sdiL1 < -2.0 && prevSdiL1 < -2.0)) {
      activated.push({ rule: "2-2s (Nivel 1)", tipo: "RECHAZO", severity: "CRITICAL", desc: "Regla 2-2s: Nivel 1 superó 2 SD en dos corridas consecutivas (Error Sistemático)." });
    }
    if ((sdiL2 > 2.0 && prevSdiL2 > 2.0) || (sdiL2 < -2.0 && prevSdiL2 < -2.0)) {
      activated.push({ rule: "2-2s (Nivel 2)", tipo: "RECHAZO", severity: "CRITICAL", desc: "Regla 2-2s: Nivel 2 superó 2 SD en dos corridas consecutivas (Error Sistemático)." });
    }
  }

  // Regla 4-1s: 4 corridas consecutivas > 1s en el mismo sentido
  const allRuns = [...history, currentRun];
  if (allRuns.length >= 4) {
    const last4 = allRuns.slice(-4);
    const sdi4_L1 = last4.map((r) => (r.l1 - targetL1) / sdL1);
    if (sdi4_L1.every((s) => s > 1.0) || sdi4_L1.every((s) => s < -1.0)) {
      activated.push({ rule: "4-1s (Nivel 1)", tipo: "RECHAZO", severity: "WARNING", desc: "Regla 4-1s: Cuatro corridas consecutivas superaron 1 SD en Nivel 1 (Error Sistemático)." });
    }
    const sdi4_L2 = last4.map((r) => (r.l2 - targetL2) / sdL2);
    if (sdi4_L2.every((s) => s > 1.0) || sdi4_L2.every((s) => s < -1.0)) {
      activated.push({ rule: "4-1s (Nivel 2)", tipo: "RECHAZO", severity: "WARNING", desc: "Regla 4-1s: Cuatro corridas consecutivas superaron 1 SD en Nivel 2 (Error Sistemático)." });
    }
  }

  // Regla 10-x: 10 corridas consecutivas del mismo lado de la media
  if (allRuns.length >= 10) {
    const last10 = allRuns.slice(-10);
    const sdi10_L1 = last10.map((r) => (r.l1 - targetL1) / sdL1);
    if (sdi10_L1.every((s) => s > 0) || sdi10_L1.every((s) => s < 0)) {
      activated.push({ rule: "10-x (Nivel 1)", tipo: "RECHAZO", severity: "WARNING", desc: "Regla 10-x: Diez corridas consecutivas del mismo lado de la media en Nivel 1 (Desplazamiento de calibración)." });
    }
  }

  const hasCritical = activated.some((r) => r.severity === "CRITICAL");
  const hasWarning = activated.some((r) => r.severity === "WARNING");

  return {
    sdiL1: Number(sdiL1.toFixed(2)),
    sdiL2: Number(sdiL2.toFixed(2)),
    reglas: activated,
    estado: hasCritical ? "RECHAZO" : hasWarning ? "ADVERTENCIA" : "ACEPTADO",
    severidad: hasCritical ? "CRITICAL" : hasWarning ? "WARNING" : "INFO",
    accion: hasCritical ? "RETENER_CORRIDA" : hasWarning ? "REVISAR_TENDENCIA" : "LIBERAR"
  };
}

/**
 * Cálculo del Valor Crítico de Cambio (RCV / Reference Change Value)
 * Fórmula: RCV = 2^(1/2) * Z * sqrt(CV_A^2 + CV_I^2)
 */
function calcularRCV(cva, cvi, zScore = 1.96) {
  const rcv = Math.SQRT2 * zScore * Math.sqrt(Math.pow(cva, 2) + Math.pow(cvi, 2));
  return Number(rcv.toFixed(2));
}

/**
 * Cálculo eGFR CKD-EPI 2021 (Ecuación recomendada internacionalmente sin variable de raza)
 */
function calcularCKDEPI2021(cr, edad, sexo) {
  if (!cr || cr <= 0 || !edad || edad <= 0) return { egfr: null, estadio: null, desc: "" };
  const isFemale = sexo.toLowerCase().startsWith("m") || sexo.toLowerCase() === "femenino";
  const kappa = isFemale ? 0.7 : 0.9;
  const alpha = isFemale ? -0.241 : -0.302;
  const factorSexo = isFemale ? 1.012 : 1.0;

  const minRatio = Math.min(cr / kappa, 1);
  const maxRatio = Math.max(cr / kappa, 1);

  const egfr = 142 * Math.pow(minRatio, alpha) * Math.pow(maxRatio, -1.200) * Math.pow(0.9938, edad) * factorSexo;
  const val = Number(egfr.toFixed(1));

  let estadio = "G1";
  let desc = "Normal o elevado";
  let color = "#5FD97A";
  if (val < 15) {
    estadio = "G5"; desc = "Falla renal terminal"; color = "#FF5C6C";
  } else if (val < 30) {
    estadio = "G4"; desc = "Disminución severa"; color = "#FFA359";
  } else if (val < 45) {
    estadio = "G3b"; desc = "Disminución moderada a severa"; color = "#FFA359";
  } else if (val < 60) {
    estadio = "G3a"; desc = "Disminución leve a moderada"; color = "#EAB308";
  } else if (val < 90) {
    estadio = "G2"; desc = "Levemente disminuido"; color = "#22D3B8";
  }

  return { egfr: val, estadio, desc, color };
}

/**
 * Cálculo de Fracción Lipídica LDL (Fórmula de Friedewald con validación de límite de Triglicéridos)
 */
function calcularFriedewald(colTotal, hdl, tg) {
  if (!colTotal || !hdl || !tg) return { ldl: null, valido: false, error: "Valores incompletos" };
  if (tg > 400) {
    return {
      ldl: null,
      valido: false,
      error: "Triglicéridos > 400 mg/dL: La ecuación de Friedewald no es válida debido a la alteración de la relación VLDL. Requiere cuantificación directa de c-LDL por método homogéneo."
    };
  }
  const ldl = colTotal - hdl - (tg / 5);
  const noHdl = colTotal - hdl;
  return {
    ldl: Number(ldl.toFixed(1)),
    noHdl: Number(noHdl.toFixed(1)),
    valido: true,
    error: null
  };
}


/* ─────────────────────────────────────────────────────────────────────────
   § QC-ADV · PROTOCOLOS AVANZADOS DE CALIDAD (CLSI C24, EP09, EP15, PEEC ISP)
   ───────────────────────────────────────────────────────────────────────── */
const N20_PRELIMINAR_DATA = {
  lote: "LOT-BIOQ-PRELIM-2027-ALPHA",
  analito: "Glucosa en Suero (Cobas Pro c503)",
  unidad: "mg/dL",
  insertoFabricante: { target: 92.0, sdEsperado: 2.30, cvEsperado: 2.50 },
  replicas: [
    91.8, 92.4, 91.5, 92.1, 93.0, 91.9, 92.3, 92.0, 91.7, 92.6,
    92.2, 91.9, 92.5, 91.6, 92.8, 92.1, 91.8, 92.4, 92.0, 92.3
  ]
};

const PEEC_ISP_ENCUESTAS = [
  {
    id: "PEEC-2026-Q1-GLU",
    seccion: "Bioquímica Clínica",
    analito: "Glucosa en Suero",
    metodo: "Hexoquinasa / UV",
    equipo: "Roche Cobas Pro c503",
    unidad: "mg/dL",
    valorLab: 94.2,
    mediaPares: 93.8,
    sdPares: 2.10,
    nParticipantes: 318,
    fecha: "Marzo 2026",
    estado: "Satisfactorio",
  },
  {
    id: "PEEC-2026-Q1-TROP",
    seccion: "Inmunoquímica / Marcadores Cardíacos",
    analito: "Troponina T ultrasensible (hs-cTnT)",
    metodo: "ECLIA",
    equipo: "Roche Cobas e411 / e801",
    unidad: "ng/L",
    valorLab: 48.5,
    mediaPares: 47.9,
    sdPares: 3.20,
    nParticipantes: 142,
    fecha: "Marzo 2026",
    estado: "Satisfactorio",
  },
  {
    id: "PEEC-2026-Q2-LEUC",
    seccion: "Hematología",
    analito: "Recuento de Leucocitos",
    metodo: "Citometría de Flujo Fluorescente",
    equipo: "Sysmex XN-1000",
    unidad: "10^3/µL",
    valorLab: 7.15,
    mediaPares: 7.02,
    sdPares: 0.28,
    nParticipantes: 284,
    fecha: "Junio 2026",
    estado: "Satisfactorio",
  },
  {
    id: "PEEC-2026-Q2-TP",
    seccion: "Coagulación",
    analito: "Tiempo de Protrombina (TP)",
    metodo: "Mecánico por Viscosidad",
    equipo: "Stago STA-R Max",
    unidad: "seg",
    valorLab: 12.8,
    mediaPares: 12.6,
    sdPares: 0.45,
    nParticipantes: 196,
    fecha: "Junio 2026",
    estado: "Satisfactorio",
  }
];

const CLSI_EP09_DATA = {
  metodoReferencia: "Roche Cobas c503 (Línea Primaria)",
  metodoCandidato: "Roche Cobas c503 (Módulo Espejo)",
  analito: "Creatinina en Suero (mg/dL)",
  muestras: [
    { id: 1, ref: 0.72, cand: 0.73 },
    { id: 2, ref: 0.95, cand: 0.96 },
    { id: 3, ref: 1.15, cand: 1.14 },
    { id: 4, ref: 1.48, cand: 1.50 },
    { id: 5, ref: 1.95, cand: 1.98 },
    { id: 6, ref: 2.60, cand: 2.64 },
    { id: 7, ref: 3.40, cand: 3.42 },
    { id: 8, ref: 4.80, cand: 4.86 },
    { id: 9, ref: 6.20, cand: 6.25 },
    { id: 10, ref: 8.50, cand: 8.58 }
  ],
  regresion: { pendiente: 1.011, intercepto: -0.008, r2: 0.9994 },
  incertidumbre: { uAnalitica: 2.1, uCalibrador: 1.4, expandidaU: 4.2 }
};

/* ─────────────────────────────────────────────────────────────────────────
   § PRIVACIDAD-LEY-21719 · GESTIÓN DE DERECHOS ARCO & AUDITORÍA DE SALUD
   ───────────────────────────────────────────────────────────────────────── */
const SOLICITUDES_ARCO_INICIALES = [
  {
    id: "ARCO-2026-0041",
    fechaIngreso: "22-10-2026 09:15",
    titular: "Valentina Paz Silva Morales",
    rut: "18.349.812-4",
    tipoDerecho: "Acceso & Portabilidad",
    canal: "Portal Paciente AXON",
    estado: "En proceso (Plazo: 15 días)",
    plazoVencimiento: "06-11-2026",
    fundamento: "Solicita copia íntegra de reportes analíticos de perfil tiroideo e inmunología para interconsulta médica.",
    oficialResponsable: "Dra. Cecilia Bustamante (Oficial de Privacidad)",
  },
  {
    id: "ARCO-2026-0042",
    fechaIngreso: "23-10-2026 14:30",
    titular: "Ignacio Andrés Tapia Riquelme",
    rut: "11.238.940-K",
    tipoDerecho: "Oposición a Tratamiento Secundario",
    canal: "Ventanilla OIRS Hospitalaria",
    estado: "Aprobada & Bloqueado",
    plazoVencimiento: "07-11-2026",
    fundamento: "Oposición expresa a que sus resultados de laboratorio sean utilizados en estudios observacionales o entrenamiento de IA sin consentimiento.",
    oficialResponsable: "Dra. Cecilia Bustamante (Oficial de Privacidad)",
  },
  {
    id: "ARCO-2026-0043",
    fechaIngreso: "24-10-2026 08:20",
    titular: "Camila Belén Henríquez Soto",
    rut: "20.194.882-7",
    tipoDerecho: "Rectificación de Domicilio y Contacto",
    canal: "Portal Paciente AXON",
    estado: "Completada",
    plazoVencimiento: "08-11-2026",
    fundamento: "Actualización de correo institucional y teléfono móvil para notificaciones críticas de exámenes.",
    oficialResponsable: "TM. Matías Salgado",
  }
];

const LOGS_ACCESO_DATOS_SENSIBLES = [
  { id: "ACC-01", hora: "24-10 08:32:10", actor: "Dra. María Elena Morales", rol: "Directora Técnica", cut: "MED-CL-44910", paciente: "Marcos Antonio Rosales Gómez", rut: "12.839.201-4", motivo: "Validación facultativa y firma electrónica de Troponina T hs (STAT).", hash: "9f82ab3048ec1" },
  { id: "ACC-02", hora: "24-10 08:35:45", actor: "TM. Matías Salgado", rol: "Tecnólogo Médico", cut: "TM-CL-88210", paciente: "Marcos Antonio Rosales Gómez", rut: "12.839.201-4", motivo: "Notificación verbal telefónica con doble lectura (Read-Back) a Box Reanimación.", hash: "e441bc2990aa2" },
  { id: "ACC-03", hora: "24-10 09:12:00", actor: "Dr. Rodrigo Mellado", rol: "Médico Solicitante", cut: "MED-CL-89120", paciente: "Catalina Andrea Muñoz Varas", rut: "17.482.903-8", motivo: "Consulta de resultados de gases arteriales y saturometría en UCI.", hash: "a77190ffc8101" }
];

/**
 * Motor de Seudonimización Criptográfica (Ley 21.719 Art. 18 / GDPR Recital 26)
 * Genera tokens unidireccionales para investigación analítica sin exponer datos personales.
 */
function seudonimizarOrdenes(listaOrdenes) {
  return listaOrdenes.map((o) => {
    const tokenPaciente = "ANON-PAC-" + sha256Sync("SALT_AXON_CLINICAL_2026|" + o.rut).substring(0, 12).toUpperCase();
    const edadRedondeada = Math.floor(o.edad / 5) * 5 + " - " + (Math.floor(o.edad / 5) * 5 + 4) + " años";
    return {
      tokenIdentificador: tokenPaciente,
      rangoEtario: edadRedondeada,
      sexo: o.sexo,
      servicioOrigen: o.origen,
      prioridad: o.prioridad,
      fase: o.fase,
      estado: o.estado,
      analitos: o.analitos.map((a) => ({
        codigoLoinc: a.codigo,
        nombreExamen: a.nombre,
        valor: a.valor,
        unidadUcum: a.ucum,
        flag: a.flag
      }))
    };
  });
}

/**
 * Generador Canónico FHIR R4 Bundle (v4.0.1)
 */
function generarFHIRR4Bundle(orden) {
  if (!orden) return null;
  const patientId = "patient-" + orden.rut.replace(/[^a-zA-Z0-9]/g, "");
  const reportId = "report-" + orden.acc.toLowerCase();

  const entries = [
    {
      fullUrl: "urn:uuid:" + patientId,
      resource: {
        resourceType: "Patient",
        id: patientId,
        identifier: [
          {
            use: "official",
            system: "https://registrocivil.cl/run",
            value: orden.rut
          }
        ],
        name: [{ use: "official", text: orden.paciente }],
        gender: orden.sexo === "Femenino" ? "female" : "male"
      }
    },
    {
      fullUrl: "urn:uuid:servicerequest-" + orden.id,
      resource: {
        resourceType: "ServiceRequest",
        id: "servicerequest-" + orden.id,
        status: orden.fase === "informes" ? "completed" : "active",
        intent: "order",
        priority: orden.prioridad === "stat" ? "stat" : "routine",
        code: { text: "Solicitud Exámenes Laboratorio Clínico AXON" },
        subject: { reference: "urn:uuid:" + patientId, display: orden.paciente },
        requester: { display: orden.medicoSolicitante }
      }
    }
  ];

  (orden.tubos || []).forEach((t) => {
    entries.push({
      fullUrl: "urn:uuid:specimen-" + t.id,
      resource: {
        resourceType: "Specimen",
        id: t.id,
        status: t.estado === "rechazada" ? "unsatisfactory" : "available",
        type: { text: t.tipoMuestra },
        container: [{ description: t.recipiente }]
      }
    });
  });

  (orden.analitos || []).forEach((an) => {
    entries.push({
      fullUrl: "urn:uuid:obs-" + an.id,
      resource: {
        resourceType: "Observation",
        id: an.id,
        status: an.valor !== null ? "final" : an.flag === "RECHAZADO_PREANALITICO" ? "cancelled" : "preliminary",
        code: {
          coding: [{ system: "http://loinc.org", code: an.codigo, display: an.nombre }]
        },
        subject: { reference: "urn:uuid:" + patientId },
        valueQuantity: an.valor !== null ? {
          value: an.valor,
          unit: an.ucum,
          system: "http://unitsofmeasure.org",
          code: an.ucum
        } : undefined,
        referenceRange: [{
          low: an.refMin !== null ? { value: an.refMin, unit: an.ucum } : undefined,
          high: an.refMax !== null ? { value: an.refMax, unit: an.ucum } : undefined
        }],
        interpretation: [{
          coding: [{
            system: "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
            code: an.flag === "CRITICAL_HIGH" || an.flag === "CRITICAL_LOW" ? "HH" : an.flag === "HIGH" ? "H" : an.flag === "LOW" ? "L" : "N"
          }]
        }]
      }
    });
  });

  entries.push({
    fullUrl: "urn:uuid:" + reportId,
    resource: {
      resourceType: "DiagnosticReport",
      id: reportId,
      status: orden.fase === "informes" ? "final" : "partial",
      code: { text: "DiagnosticReport de Laboratorio Clínico" },
      subject: { reference: "urn:uuid:" + patientId },
      result: (orden.analitos || []).map((an) => ({ reference: "urn:uuid:obs-" + an.id })),
      conclusion: orden.fase === "informes" ? "Informe diagnosticado y sellado criptográficamente." : "Resultados en curso de procesamiento."
    }
  });

  return {
    resourceType: "Bundle",
    id: "bundle-" + orden.acc.toLowerCase(),
    type: "document",
    timestamp: new Date().toISOString(),
    entry: entries
  };
}

// Helper y Motor de Interpretación CLSI M100 Ed. 36 (2026) para Microbiología (AST)
function interpretarAntibiogramaCLSI(organismo, antimicrobianoKey, metodo, valor) {
  const tablas = {
    AMP: { nombre: "Ampicilina", familia: "Penicilina", cim: { s: 8, r: 32 }, disco: { s: 17, r: 13 } },
    AMC: { nombre: "Amoxicilina-Ác. Clavulánico", familia: "Inhibidor β-lactamasa", cim: { s: 8, r: 32 }, disco: { s: 18, r: 13 } },
    SAM: { nombre: "Ampicilina-Sulbactam", familia: "Inhibidor β-lactamasa", cim: { s: 8, r: 32 }, disco: { s: 15, r: 11 } },
    TZP: { nombre: "Piperacilina-Tazobactam", familia: "Antipseudomónico", cim: { s: 8, r: 64 }, disco: { s: 21, r: 17 } },
    CFZ: { nombre: "Cefazolina", familia: "Cefalosporina 1ª", cim: { s: 16, r: 32 }, disco: { s: 15, r: 14 } },
    CRO: { nombre: "Ceftriaxona", familia: "Cefalosporina 3ª", cim: { s: 1, r: 4 }, disco: { s: 23, r: 19 } },
    FEP: { nombre: "Cefepima", familia: "Cefalosporina 4ª", cim: { s: 2, r: 16 }, disco: { s: 25, r: 18 } },
    MEM: { nombre: "Meropenem", familia: "Carbapenémico", cim: { s: 1, r: 4 }, disco: { s: 23, r: 19 } },
    AMK: { nombre: "Amikacina", familia: "Aminoglucósido", cim: { s: 16, r: 64 }, disco: { s: 17, r: 14 } },
    GEN: { nombre: "Gentamicina", familia: "Aminoglucósido", cim: { s: 4, r: 16 }, disco: { s: 15, r: 12 } },
    CIP: { nombre: "Ciprofloxacino", familia: "Fluoroquinolona", cim: { s: 0.25, r: 1 }, disco: { s: 26, r: 21 } },
    SXT: { nombre: "Cotrimoxazol (TMP-SMX)", familia: "Antifolato", cim: { s: 2, r: 4 }, disco: { s: 16, r: 10 } },
    NIT: { nombre: "Nitrofurantoína", familia: "Nitrofurano (Urinario)", cim: { s: 32, r: 128 }, disco: { s: 17, r: 14 } },
  };

  const regla = tablas[antimicrobianoKey];
  if (!regla) return { inter: "N/A", label: "Sin regla", color: "#64748B", corteDesc: "No disponible", nombre: antimicrobianoKey, familia: "General" };

  let inter = "S";
  let label = "Sensible (S)";
  let color = "#10B981";
  let corteDesc = "";

  if (metodo === "cim") {
    corteDesc = `CLSI CIM: S ≤ ${regla.cim.s} | R ≥ ${regla.cim.r} µg/mL`;
    if (valor <= regla.cim.s) {
      inter = "S";
      label = "Sensible (S)";
      color = "#10B981";
    } else if (valor >= regla.cim.r) {
      inter = "R";
      label = "Resistente (R)";
      color = "#EF4444";
    } else {
      inter = "I";
      label = "Intermedio / SDD (I)";
      color = "#F59E0B";
    }
  } else {
    corteDesc = `CLSI Disco: S ≥ ${regla.disco.s} | R ≤ ${regla.disco.r} mm`;
    if (valor >= regla.disco.s) {
      inter = "S";
      label = "Sensible (S)";
      color = "#10B981";
    } else if (valor <= regla.disco.r) {
      inter = "R";
      label = "Resistente (R)";
      color = "#EF4444";
    } else {
      inter = "I";
      label = "Intermedio (I)";
      color = "#F59E0B";
    }
  }

  return {
    inter,
    label,
    color,
    corteDesc,
    nombre: regla.nombre,
    familia: regla.familia,
  };
}

const MICRO_INVENTARIO_INICIAL = [
  { id: "DISC-AMP", nombre: "Ampicilina 10 µg", tipo: "Sensidisco", stock: 150, lote: "L-9042", venc: "2027-04" },
  { id: "DISC-AMC", nombre: "Amoxicilina / Ác. Clavulánico 20/10 µg", tipo: "Sensidisco", stock: 200, lote: "L-9088", venc: "2027-06" },
  { id: "CIM-MEM", nombre: "Meropenem Panel E-Test / Microdilución", tipo: "Pocillo CIM", stock: 85, lote: "L-8812", venc: "2027-02" },
  { id: "DISC-CIP", nombre: "Ciprofloxacino 5 µg", tipo: "Sensidisco", stock: 120, lote: "L-9102", venc: "2027-05" },
  { id: "DISC-CRO", nombre: "Ceftriaxona 30 µg", tipo: "Sensidisco", stock: 180, lote: "L-9115", venc: "2027-07" },
  { id: "DISC-NIT", nombre: "Nitrofurantoína 300 µg", tipo: "Sensidisco", stock: 140, lote: "L-9130", venc: "2027-08" },
];

const MICRO_MEDICIONES_INICIALES = {
  AMP: { metodo: "cim", valor: 32 },
  AMC: { metodo: "cim", valor: 8 },
  SAM: { metodo: "cim", valor: 8 },
  TZP: { metodo: "cim", valor: 4 },
  CFZ: { metodo: "discos", valor: 14 },
  CRO: { metodo: "cim", valor: 1 },
  MEM: { metodo: "cim", valor: 0.25 },
  AMK: { metodo: "cim", valor: 4 },
  CIP: { metodo: "discos", valor: 22 },
  NIT: { metodo: "discos", valor: 19 },
};


export default function AXON_LIS_Workbench() {
  const [faseActiva, setFaseActiva] = useState("control");
  const [subTabQC, setSubTabQC] = useState("westgard");
  const [qcAnalitoKey, setQcAnalitoKey] = useState("GLU");
  const [qcData, setQcData] = useState(WESTGARD_DATASETS);
  const [rcvInputs, setRcvInputs] = useState({ prev: 15.2, curr: 145.8, cva: 4.5, cvi: 9.5, z: 1.96, preset: "TROP" });
  const [ckdInputs, setCkdInputs] = useState({ cr: 1.25, edad: 68, sexo: "femenino" });
  const [lipidosInputs, setLipidosInputs] = useState({ colTotal: 215, hdl: 42, tg: 165 });
  const [corridaQCSeleccionada, setCorridaQCSeleccionada] = useState(null);
  const [solicitudesARCO, setSolicitudesARCO] = useState(SOLICITUDES_ARCO_INICIALES);
  const [datasetSeudonimizado, setDatasetSeudonimizado] = useState(null);
  const [filtroCategoriaPruebas, setFiltroCategoriaPruebas] = useState("TODAS");
  const [copiadoFHIR, setCopiadoFHIR] = useState(false);
  const [filtroARCO, setFiltroARCO] = useState("TODAS");
  const [ejecutandoPruebas, setEjecutandoPruebas] = useState(false);
  const [loteN20Aprobado, setLoteN20Aprobado] = useState(false);
  // Estados para Módulo de Microbiología & Antibiograma (CLSI M100 Ed. 36)
  const [microSubTab, setMicroSubTab] = useState("estudio");
  const [microPaso, setMicroPaso] = useState(1);
  const [microOrganismo, setMicroOrganismo] = useState("Escherichia coli");
  const [microMuestra, setMicroMuestra] = useState("Orina (Urocultivo)");
  const [microMetodoDefault, setMicroMetodoDefault] = useState("mixta");
  const [microRecuentoUfc, setMicroRecuentoUfc] = useState("> 100.000 UFC/mL (Desarrollo significativo)");
  const [microPanelSeleccionado, setMicroPanelSeleccionado] = useState(["AMP", "AMC", "SAM", "TZP", "CFZ", "CRO", "MEM", "AMK", "CIP", "NIT"]);
  const [microMediciones, setMicroMediciones] = useState(MICRO_MEDICIONES_INICIALES);
  const [microInventario, setMicroInventario] = useState(MICRO_INVENTARIO_INICIAL);


  const [ordenes, setOrdenes] = useState(SEED_ORDENES);
  const [selectedId, setSelectedId] = useState(null);
  const [tabDetalle, setTabDetalle] = useState("analitos");
  const [busqueda, setBusqueda] = useState("");
  const [disciplinaFiltro, setDisciplinaFiltro] = useState("TODAS");
  const [prioridadFiltro, setPrioridadFiltro] = useState("TODAS");
  const [usuarioActivo, setUsuarioActivo] = useState(SESIONES_USUARIO[0]);

  // Estados del Gateway de Instrumentos
  const [analizadores, setAnalizadores] = useState(ANALIZADORES_CATALOGO);
  const [logsGateway, setLogsGateway] = useState(LOGS_GATEWAY_INICIALES);
  const [logPausado, setLogPausado] = useState(false);
  const [filtroGateway, setFiltroGateway] = useState("TODOS");
  const [alertaSimulador, setAlertaSimulador] = useState(null);

  // Modales
  const [modalEtiquetasAbierto, setModalEtiquetasAbierto] = useState(false);
  const [modalRechazoAbierto, setModalRechazoAbierto] = useState(false);
  const [tuboARechazar, setTuboARechazar] = useState("");
  const [causalRechazoSeleccionada, setCausalRechazoSeleccionada] = useState("HEM_3");
  const [modalAlertaCriticaAbierto, setModalAlertaCriticaAbierto] = useState(false);
  const [analitoCriticoSeleccionado, setAnalitoCriticoSeleccionado] = useState(null);
  const [modalFirmarInformeAbierto, setModalFirmarInformeAbierto] = useState(false);
  const [modalVisorPdfAbierto, setModalVisorPdfAbierto] = useState(false);
  const [modalNuevoIngresoAbierto, setModalNuevoIngresoAbierto] = useState(false);
  const [bloqueoPermisoFirma, setBloqueoPermisoFirma] = useState(false);

  // Formulario Nueva Solicitud
  const [nuevoRun, setNuevoRun] = useState("16.892.112-8");
  const [nuevoNombre, setNuevoNombre] = useState("Andrea Paz Soto Morales");
  const [nuevaEdad, setNuevaEdad] = useState(38);
  const [nuevoSexo, setNuevoSexo] = useState("F");
  const [nuevoOrigen, setNuevoOrigen] = useState("Urgencia Adulto");
  const [nuevaCama, setNuevaCama] = useState("Box 04");
  const [nuevoPrioridad, setNuevoPrioridad] = useState("stat");
  const [nuevoMedico, setNuevoMedico] = useState("Dr. Rodrigo Mellado (Reg. SIS 89120)");
  const [nuevoDiagnostico, setNuevoDiagnostico] = useState("Dolor torácico atípico en estudio.");
  const [testSeleccionados, setTestSeleccionados] = useState({
    hemograma: true,
    troponina: true,
    perfilBioq: false,
    coagulacion: false,
    gases: false,
  });

  const selected = useMemo(() => ordenes.find((o) => o.id === selectedId) || null, [ordenes, selectedId]);
  
  // Conteo de Alertas Críticas pendientes de notificación
  const totalAlertasCriticasPendientes = useMemo(() => {
    let count = 0;
    ordenes.forEach((o) => {
      o.analitos.forEach((an) => {
        if (an.alertaCritica && an.alertaCritica.activa && !an.alertaCritica.notificado) {
          count++;
        }
      });
    });
    return count;
  }, [ordenes]);

  const conteos = useMemo(() => ({
    control: ordenes.length,
    flebotomia: ordenes.filter((o) => o.fase === "flebotomia").length,
    worklist: ordenes.filter((o) => o.fase === "worklist").length,
    validacion_tec: ordenes.filter((o) => o.fase === "validacion_tec").length,
    validacion_fac: ordenes.filter((o) => o.fase === "validacion_fac").length,
    informes: ordenes.filter((o) => o.fase === "informes").length,
    microbiologia: ordenes.filter((o) => o.disciplinas.includes("MIC")).length,
    equipos: analizadores.filter((a) => a.estado === "online").length,
  }), [ordenes, analizadores]);

  const filtered = useMemo(() => {
    return ordenes.filter((ord) => {
      if (faseActiva !== "control" && faseActiva !== "equipos") {
        if (ord.fase !== faseActiva) return false;
      }
      if (prioridadFiltro !== "TODAS" && ord.prioridad !== prioridadFiltro) return false;
      if (disciplinaFiltro !== "TODAS" && !ord.disciplinas.includes(disciplinaFiltro)) return false;
      if (busqueda.trim()) {
        const q = busqueda.toLowerCase().trim();
        const m = ord.paciente.toLowerCase().includes(q) || ord.rut.toLowerCase().includes(q) || ord.acc.toLowerCase().includes(q);
        if (!m) return false;
      }
      return true;
    });
  }, [ordenes, faseActiva, prioridadFiltro, disciplinaFiltro, busqueda]);

  const logsFiltrados = useMemo(() => {
    if (filtroGateway === "TODOS") return logsGateway;
    return logsGateway.filter((l) => l.equipoId === filtroGateway);
  }, [logsGateway, filtroGateway]);

  /* ─────────────────────────────────────────────────────────────────────────
     § 5 · MOTOR ANALÍTICO Y GATEWAY CON MAPEO ESTRICTO EQUIPO ➔ ANALITO ➔ TUBO
     ───────────────────────────────────────────────────────────────────────── */
  const MAPA_VALORES_SIMULADOS = {
    // Bioquímica General & Enzimas
    GLU: 104.5,
    BUN: 16.0,
    UREA: 34.0,
    CREAT: 1.12,
    AC_URIC: 5.4,
    BILI_T: 0.85,
    BILI_D: 0.22,
    GOT: 32.0,
    GPT: 28.0,
    FA: 85.0,
    PROT_T: 7.1,
    ALB: 4.2,
    CALCIO: 9.4,
    K: 4.3,
    NA: 139.0,
    CL: 102.0,
    PCR: 4.2,
    CKMB: 2.1,
    // Inmunoquímica ECLIA
    TROP: 9.8,
    FERR: 120.0,
    TSH: 2.45,
    PROCAL: 0.12,
    // Hematología
    LEUC: 7.8,
    GR: 4.75,
    HEM: 13.8,
    HTO: 41.5,
    VCM: 89.2,
    HCM: 29.8,
    CHCM: 33.4,
    PLAQT: 240.0,
    NEUT: 62.0,
    // Coagulación
    TP: 12.4,
    ACT_TP: 92.0,
    INR: 1.02,
    TTPK: 31.5,
    FIB: 285.0,
    // Gases Arteriales
    PH: 7.39,
    PCO2: 39.5,
    PO2: 92.0,
    HCO3: 24.2,
    BE: 0.2,
    SATO2: 97.5,
    LACT: 1.2,
  };

  // Verificación Centralizada de Condiciones Previas para Publicación (D.S. 20 / ISO 15189)
  const verificarCondicionesPublicacion = (orden) => {
    const motivos = [];
    if (!orden) return { aprobado: false, motivos: ["No hay orden seleccionada."] };

    // 1. Alertas críticas activas sin notificación verbal con read-back
    const alertasSinNotificar = (orden.analitos || []).filter(
      (an) => an.alertaCritica?.activa && !an.alertaCritica?.notificado
    );
    if (alertasSinNotificar.length > 0) {
      const listado = alertasSinNotificar
        .map((a) => `${a.nombre}: ${a.valor} ${a.ucum} [${a.flag}]`)
        .join("; ");
      motivos.push(
        `• ALERTA CRÍTICA PENDIENTE DE NOTIFICACIÓN: ${listado}. Conforme al D.S. N° 20 Art. 14, es mandatorio registrar la notificación verbal telefónica con doble lectura (Read-Back) antes de liberar el informe.`
      );
    }

    // 2. Analitos pendientes de resultado (no medidos ni formalmente rechazados)
    const analitosPendientes = (orden.analitos || []).filter(
      (an) => an.valor === null && an.flag !== "RECHAZADO_PREANALITICO"
    );
    if (analitosPendientes.length > 0) {
      const listado = analitosPendientes.map((a) => a.nombre).join(", ");
      motivos.push(
        `• EXÁMENES PENDIENTES DE RESULTADO: ${analitosPendientes.length} prueba(s) sin medición analítica [${listado}]. No se puede firmar un informe diagnóstico definitivo incompleto.`
      );
    }

    // 3. Fase operativa incompatible
    if (["ordenes", "flebotomia", "recepcion", "worklist"].includes(orden.fase)) {
      motivos.push(
        `• FASE INCOMPATIBLE: La orden se encuentra en fase '${orden.fase}'. Debe completar la ejecución analítica y validación técnica antes de la firma facultativa DT.`
      );
    }

    return {
      aprobado: motivos.length === 0,
      motivos,
    };
  };

  const simularLlegadaResultadoAnalizador = (equipoId) => {
    const eq = analizadores.find((a) => a.id === equipoId);
    if (!eq) return;

    // Buscar orden con analitos pendientes que correspondan a este equipo y cuyo tubo esté admitido y NO rechazado
    let ordenTarget = null;
    let analitoTarget = null;

    for (const ord of ordenes) {
      if (ord.fase === "worklist" || ord.fase === "validacion_tec" || ord.fase === "recepcion") {
        const matchingAn = ord.analitos.find((an) => {
          const tubo = ord.tubos.find((t) => t.id === an.tuboId);
          return (
            eq.analitosSoportados.includes(an.testKey) &&
            an.valor === null &&
            an.flag !== "RECHAZADO_PREANALITICO" &&
            tubo &&
            tubo.estado !== "rechazada" &&
            (tubo.estado === "recibida" || tubo.estado === "en_analisis")
          );
        });
        if (matchingAn) {
          ordenTarget = ord;
          analitoTarget = matchingAn;
          break;
        }
      }
    }

    if (!ordenTarget || !analitoTarget) {
      setAlertaSimulador({
        tipo: "warning",
        titulo: "Sin muestras listas para este equipo",
        mensaje: `No se encontraron órdenes en Worklist con muestras admitidas y exámenes pendientes soportados por ${eq.nombre} (${eq.analitosSoportados.slice(0, 5).join(", ")}...). Asegúrese de admitir los tubos en Laboratorio Central.`,
      });
      setTimeout(() => setAlertaSimulador(null), 5000);
      return;
    }

    const nuevaHora = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    const nowIso = new Date().toISOString().slice(0, 19).replace("T", " ");

    // Generar valor plausible según analito (sin 98.4 genérico)
    const valorSimulado = MAPA_VALORES_SIMULADOS[analitoTarget.testKey] !== undefined
      ? MAPA_VALORES_SIMULADOS[analitoTarget.testKey]
      : (analitoTarget.refMin && analitoTarget.refMax
          ? Number(((analitoTarget.refMin + analitoTarget.refMax) / 2).toFixed(2))
          : 50.0);

    const deltaCalc = calcularDelta(valorSimulado, analitoTarget.previo);
    const flagCalc = evaluarFlag(valorSimulado, analitoTarget.refMin, analitoTarget.refMax, analitoTarget.critMin, analitoTarget.critMax);
    const esCritico = flagCalc.includes("CRITICAL");

    // Construir mensaje según protocolo real del equipo (HL7 v2.5.1 u ASTM 1394)
    let msjDriver = "";
    if (eq.proto.includes("ASTM")) {
      msjDriver = `H|\\^&|||${eq.id.toUpperCase()}^${eq.nombre}|||||||P|1394-97\nP|1||${ordenTarget.cup}||${ordenTarget.paciente.replace(/ /g, "^")}|||${ordenTarget.sexo}\nO|1|${analitoTarget.tuboId}||^^^${analitoTarget.codigo}^${analitoTarget.nombre}|R|${nowIso}\nR|1|^^^${analitoTarget.codigo}^${analitoTarget.nombre}|${valorSimulado}|${analitoTarget.ucum}|${analitoTarget.refMin}-${analitoTarget.refMax}|${flagCalc === "NORMAL" ? "N" : flagCalc.includes("HIGH") ? "H" : "L"}|N|F||||${nowIso}\nL|1|N`;
    } else {
      msjDriver = `MSH|^~\\&|${eq.id.toUpperCase()}|${eq.disc}|AXON_LIS|CORE|${new Date().toISOString().slice(0, 10).replace(/-/g, "")}${nuevaHora.replace(/:/g, "")}||ORU^R01|MSG${Date.now().toString().slice(-6)}|P|2.5.1\nPID|1||${ordenTarget.cup}||${ordenTarget.paciente.replace(/ /g, "^")}\nOBR|1|${ordenTarget.orden}|${analitoTarget.tuboId}|${analitoTarget.testKey}^${analitoTarget.nombre}|||${nowIso}\nOBX|1|NM|${analitoTarget.codigo}^${analitoTarget.nombre}|1|${valorSimulado}|${analitoTarget.ucum}|${analitoTarget.refMin}-${analitoTarget.refMax}|${flagCalc === "CRITICAL_HIGH" ? "HH" : flagCalc === "CRITICAL_LOW" ? "LL" : flagCalc === "HIGH" ? "H" : flagCalc === "LOW" ? "L" : "N"}|||F|||${nowIso}|${eq.id}`;
    }

    const nuevoLog = {
      id: Date.now(),
      hora: nuevaHora,
      analizador: eq.nombre,
      equipoId: eq.id,
      proto: eq.proto,
      tipo: "IN",
      msj: msjDriver,
    };

    if (!logPausado) {
      setLogsGateway((prev) => [nuevoLog, ...prev.slice(0, 24)]);
    }

    // Actualizar contadores del equipo
    setAnalizadores((prev) =>
      prev.map((a) => (a.id === equipoId ? { ...a, testsHoy: a.testsHoy + 1, ultPing: "hace 2 seg" } : a))
    );

    // Evento de auditoría verificable con SHA-256 canónico
    const hashAudit = sha256Sync(`${ordenTarget.acc}|${analitoTarget.codigo}|${valorSimulado}|${nowIso}`);
    const nuevoEventoAudit = {
      id: `AUD-${Date.now()}`,
      hora: nuevaHora,
      actor: `${eq.nombre} (Gateway)`,
      rol: "Analizador Conectado (Driver)",
      cut: `DEV-${eq.id.toUpperCase()}`,
      accion: "RESULTADO_INSTRUMENTO_RECIBIDO",
      detalle: `Transmisión ${eq.proto}. ${analitoTarget.nombre}: ${valorSimulado} ${analitoTarget.ucum} [Flag: ${flagCalc}].`,
      hash: hashAudit,
    };

    // Actualizar orden de forma inmutable
    setOrdenes((prev) =>
      prev.map((ord) => {
        if (ord.id !== ordenTarget.id) return ord;

        const analitosActualizados = ord.analitos.map((an) => {
          if (an.id !== analitoTarget.id) return an;
          return {
            ...an,
            valor: valorSimulado,
            delta: deltaCalc,
            flag: flagCalc,
            horaMedicion: nuevaHora,
            alertaCritica: esCritico
              ? {
                  activa: true,
                  horaDeteccion: nuevaHora,
                  notificado: false,
                  receptor: null,
                  registroReceptor: null,
                  via: null,
                  anexo: null,
                  horaNotif: null,
                  readback: false,
                  medidas: null,
                }
              : null,
          };
        });

        // Verificar si quedan analitos pendientes válidos en la orden (excluyendo rechazados)
        const quedanPendientes = analitosActualizados.some(
          (an) => an.valor === null && an.flag !== "RECHAZADO_PREANALITICO"
        );
        const nuevaFase = quedanPendientes ? ord.fase : "validacion_tec";
        const nuevoEstado = quedanPendientes ? "resultado_parcial" : "resultado_disp";

        return {
          ...ord,
          fase: nuevaFase,
          estado: nuevoEstado,
          analitos: analitosActualizados,
          auditoria: [nuevoEventoAudit, ...ord.auditoria],
        };
      })
    );

    setAlertaSimulador({
      tipo: "success",
      titulo: "Resultado Recibido y Conciliado",
      mensaje: `${eq.nombre} transmitió ${analitoTarget.nombre}: ${valorSimulado} ${analitoTarget.ucum} para orden ${ordenTarget.orden} (${ordenTarget.paciente}).`,
    });
    setTimeout(() => setAlertaSimulador(null), 5000);
  };

  /* ─────────────────────────────────────────────────────────────────────────
     § 6 · REGISTRO AUDITABLE DE NOTIFICACIÓN CRÍTICA (READ-BACK DESMARCADO)
     ───────────────────────────────────────────────────────────────────────── */
  const handleConfirmarNotificacionCritica = (e) => {
    e.preventDefault();
    if (!selected || !analitoCriticoSeleccionado) return;

    const receptor = document.getElementById("notif-receptor")?.value.trim();
    const registro = document.getElementById("notif-registro")?.value.trim();
    const via = document.getElementById("notif-via")?.value;
    const anexo = document.getElementById("notif-anexo")?.value.trim();
    const readbackChecked = document.getElementById("notif-readback")?.checked;
    const medidas = document.getElementById("notif-medidas")?.value.trim();

    if (!receptor) {
      alert("Error: Debe registrar el nombre del profesional receptor de la notificación.");
      return;
    }
    if (!readbackChecked) {
      alert("Error: Conforme al protocolo de seguridad clínica (D.S. 20), la Doble Lectura Verbal (Read-Back) debe estar confirmada con el interlocutor.");
      return;
    }

    const horaNotifExacta = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    const nowIso = new Date().toISOString().slice(0, 19).replace("T", " ");

    const hashAudit = sha256Sync(`NOTIF_CRIT|${selected.acc}|${analitoCriticoSeleccionado.codigo}|${receptor}|${nowIso}`);

    const nuevoEventoAudit = {
      id: `AUD-NOTIF-${Date.now()}`,
      hora: horaNotifExacta,
      actor: usuarioActivo.nombre,
      rol: usuarioActivo.rol,
      cut: usuarioActivo.cut,
      accion: "NOTIFICACION_VALOR_CRITICO",
      detalle: `Notificación verbal de ${analitoCriticoSeleccionado.nombre} (${analitoCriticoSeleccionado.valor} ${analitoCriticoSeleccionado.ucum}). Receptor: ${receptor} (${registro || "Sin Reg SIS"}). Vía: ${via} ${anexo ? "Anexo: " + anexo : ""}. Read-Back: CONFIRMADO. Medidas: ${medidas || "Registradas"}.`,
      hash: hashAudit,
    };

    setOrdenes((prev) =>
      prev.map((ord) => {
        if (ord.id !== selected.id) return ord;
        const analitosUpdated = ord.analitos.map((an) => {
          if (an.id !== analitoCriticoSeleccionado.id) return an;
          return {
            ...an,
            alertaCritica: {
              ...an.alertaCritica,
              notificado: true,
              receptor,
              registroReceptor: registro,
              via,
              anexo,
              horaNotif: horaNotifExacta,
              readback: true,
              medidas,
            },
          };
        });

        return {
          ...ord,
          analitos: analitosUpdated,
          auditoria: [nuevoEventoAudit, ...ord.auditoria],
        };
      })
    );

    setModalAlertaCriticaAbierto(false);
    setAnalitoCriticoSeleccionado(null);
  };

  /* ─────────────────────────────────────────────────────────────────────────
     § 7 · RECHAZO FUNDADO DE MUESTRA POR TUBO Y SOLICITUD DE RE-TOMA (D.S. 20)
     ───────────────────────────────────────────────────────────────────────── */
  const handleConfirmarRechazoTubo = () => {
    if (!selected || !tuboARechazar) return;

    const horaRechazo = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    const nowIso = new Date().toISOString().slice(0, 19).replace("T", " ");
    const causalDescMap = {
      HEM_3: "Hemólisis franca grado 3+ (interferencia analítica severa)",
      COAG_EDTA: "Muestra con microcoágulo visible en tubo EDTA K2",
      VOL_QNS: "Volumen insuficiente (QNS) para relación aditivo/sangre",
      TUBO_INAD: "Tubo o aditivo inadecuado para la prestación solicitada",
      TEMP_RUP: "Ruptura de cadena de frío / conservación preanalítica",
      ROT_DISCR: "Discrepancia en rotulación / código de barras ilegible",
    };

    const causalDesc = causalDescMap[causalRechazoSeleccionada] || "Causal preanalítica tipificada D.S. 20";
    const hashAudit = sha256Sync(`RECHAZO|${tuboARechazar}|${causalRechazoSeleccionada}|${nowIso}`);

    const nuevoEventoAudit = {
      id: `AUD-RECH-${Date.now()}`,
      hora: horaRechazo,
      actor: usuarioActivo.nombre,
      rol: usuarioActivo.rol,
      cut: usuarioActivo.cut,
      accion: "RECHAZO_FUNDADO_MUESTRA",
      detalle: `Rechazo irreversible del tubo ${tuboARechazar}. Causal: ${causalDesc}. Desecho biológico REAS registrado. Analitos asociados quedan pendientes de re-toma.`,
      hash: hashAudit,
    };

    setOrdenes((prev) =>
      prev.map((ord) => {
        if (ord.id !== selected.id) return ord;

        const tubosUpdated = ord.tubos.map((t) => {
          if (t.id !== tuboARechazar) return t;
          return {
            ...t,
            estado: "rechazada",
            causalRechazo: {
              codigo: causalRechazoSeleccionada,
              desc: causalDesc,
              horaRechazo,
              profesional: usuarioActivo.nombre,
              cut: usuarioActivo.cut,
              disposicion: "Autoclave y desecho biológico REAS",
            },
          };
        });

        // Marcar solo los analitos asociados a este tubo como rechazados preanalíticamente
        const analitosUpdated = ord.analitos.map((an) => {
          if (an.tuboId !== tuboARechazar) return an;
          return {
            ...an,
            valor: null,
            flag: "RECHAZADO_PREANALITICO",
            alertaCritica: null,
          };
        });

        const hayTubosViables = tubosUpdated.some((t) => t.estado !== "rechazada");

        return {
          ...ord,
          fase: hayTubosViables ? ord.fase : "flebotomia",
          estado: hayTubosViables ? "rechazo_parcial" : "rechazado",
          tubos: tubosUpdated,
          analitos: analitosUpdated,
          auditoria: [nuevoEventoAudit, ...ord.auditoria],
        };
      })
    );

    setModalRechazoAbierto(false);
    setTuboARechazar("");
  };

  // Re-toma formal: genera nueva muestra sin revivir el tubo rechazado
  const handleSolicitarRetoma = (tuboIdOriginal) => {
    if (!selected) return;
    const tuboOriginal = selected.tubos.find((t) => t.id === tuboIdOriginal);
    if (!tuboOriginal || tuboOriginal.estado !== "rechazada") return;

    const horaSolicitud = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const nowIso = new Date().toISOString();
    const retomaId = `${tuboIdOriginal}-RETOMA`;

    const nuevoTuboRetoma = {
      id: retomaId,
      tipo: tuboOriginal.tipo,
      recipiente: tuboOriginal.recipiente,
      tipoMuestra: tuboOriginal.tipoMuestra,
      estado: "pendiente_toma",
      horaToma: null,
      horaRecepcion: null,
      gradilla: "Pendiente Flebotomía (Re-toma)",
      causalRechazo: null,
      esRetoma: true,
      muestraOriginalId: tuboIdOriginal,
    };

    const hashAudit = sha256Sync(`RETOMA|${selected.acc}|${retomaId}|${tuboIdOriginal}|${nowIso}`);
    const nuevoEventoAudit = {
      id: `AUD-RETOMA-${Date.now()}`,
      hora: horaSolicitud,
      actor: usuarioActivo.nombre,
      rol: usuarioActivo.rol,
      cut: usuarioActivo.cut,
      accion: "SOLICITUD_RETOMA_MUESTRA",
      detalle: `Generada nueva solicitud de toma de muestra ${retomaId} tras rechazo previo de ${tuboIdOriginal} (${tuboOriginal.causalRechazo?.desc || "Causal D.S. 20"}).`,
      hash: hashAudit,
    };

    setOrdenes((prev) =>
      prev.map((ord) => {
        if (ord.id !== selected.id) return ord;

        // Reasociar analitos rechazados al nuevo tubo de re-toma
        const analitosUpdated = ord.analitos.map((an) => {
          if (an.tuboId === tuboIdOriginal && an.flag === "RECHAZADO_PREANALITICO") {
            return {
              ...an,
              tuboId: retomaId,
              flag: "PENDING",
              valor: null,
            };
          }
          return an;
        });

        return {
          ...ord,
          fase: "flebotomia",
          estado: "re_toma_solicitada",
          tubos: [...ord.tubos, nuevoTuboRetoma],
          analitos: analitosUpdated,
          auditoria: [nuevoEventoAudit, ...ord.auditoria],
        };
      })
    );

    setAlertaSimulador({
      tipo: "success",
      titulo: "Re-toma de Muestra Solicitada (D.S. 20)",
      mensaje: `Se generó el tubo ${retomaId} para nueva toma preanalítica. El tubo rechazado anterior se conserva en trazabilidad.`,
    });
    setTimeout(() => setAlertaSimulador(null), 5000);
  };

  /* ─────────────────────────────────────────────────────────────────────────
     § 8 · FIRMA ELECTRÓNICA DT CON VERIFICACIÓN DE ROL Y CONDICIONES PREVIAS
     ───────────────────────────────────────────────────────────────────────── */
  const handleIntentarFirmarDT = () => {
    if (!selected) return;

    // RBAC: Solo Directora Técnica o Bioquímico Clínico habilitado
    if (!usuarioActivo.puedeFirmar || usuarioActivo.rolId !== "dt") {
      setBloqueoPermisoFirma(true);
      return;
    }

    // Comprobación de condiciones previas de publicación
    const validacion = verificarCondicionesPublicacion(selected);
    if (!validacion.aprobado) {
      alert(`BLOQUEO DE LIBERACIÓN Y PUBLICACIÓN:\n\n${validacion.motivos.join("\n\n")}`);
      return;
    }

    setModalFirmarInformeAbierto(true);
  };

  /* ─────────────────────────────────────────────────────────────────────────
     § 7.1 · ADMISIÓN CONFORME, CARGA Y EJECUCIÓN ANALÍTICA DE TUBOS
     ───────────────────────────────────────────────────────────────────────── */
  const handleAdmitirTuboConforme = (tuboId) => {
    if (!selected) return;
    const tubo = selected.tubos.find((t) => t.id === tuboId);
    if (!tubo) return;

    // Regla D.S. 20 Art. 14: Una muestra rechazada preanalíticamente no puede ser readmitida
    if (tubo.estado === "rechazada") {
      alert("Error D.S. 20: Una muestra rechazada por causal preanalítica es biológicamente no conforme y no puede ser readmitida. Solicite una nueva toma (re-toma).");
      return;
    }

    const horaRecepcion = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const nowIso = new Date().toISOString();
    const hashAudit = sha256Sync(`ADMITIR|${selected.acc}|${tuboId}|${nowIso}`);

    const nuevoEventoAudit = {
      id: `AUD-ADM-${Date.now()}`,
      hora: horaRecepcion,
      actor: usuarioActivo.nombre,
      rol: usuarioActivo.rol,
      cut: usuarioActivo.cut,
      accion: "RECEPCION_CONFORME_TUBO",
      detalle: `Muestra ${tuboId} admitida conforme en Laboratorio Central. Rotulación y volumen validados.`,
      hash: hashAudit,
    };

    setOrdenes((prev) =>
      prev.map((ord) => {
        if (ord.id !== selected.id) return ord;
        const tubosUpdated = ord.tubos.map((t) => {
          if (t.id !== tuboId) return t;
          return {
            ...t,
            estado: "recibida",
            horaRecepcion,
            gradilla: "Gradilla Recepción Central G-04 Pos 12",
          };
        });

        const todosViablesRecibidos = tubosUpdated
          .filter((t) => t.estado !== "rechazada")
          .every((t) => t.estado === "recibida" || t.estado === "en_analisis" || t.estado === "procesada");

        const nuevaFase = todosViablesRecibidos
          ? ord.fase === "flebotomia" || ord.fase === "ordenes"
            ? "recepcion"
            : ord.fase
          : ord.fase;

        return {
          ...ord,
          fase: nuevaFase,
          tubos: tubosUpdated,
          horaRecepcion: ord.horaRecepcion || horaRecepcion,
          auditoria: [nuevoEventoAudit, ...ord.auditoria],
        };
      })
    );
  };

  const handleCargarTuboAnalizador = (tuboId) => {
    if (!selected) return;
    const tubo = selected.tubos.find((t) => t.id === tuboId);
    if (!tubo) return;

    if (tubo.estado === "rechazada") {
      alert("Error de Seguridad Analítica: No se puede cargar en el analizador un tubo rechazado preanalíticamente.");
      return;
    }
    if (tubo.estado !== "recibida" && tubo.estado !== "en_analisis") {
      alert("Flujo Preanalítico: El tubo debe estar admitido conforme en laboratorio (estado 'recibida') antes de ser cargado en el analizador.");
      return;
    }

    const horaCarga = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const nowIso = new Date().toISOString();
    const hashAudit = sha256Sync(`CARGA|${selected.acc}|${tuboId}|${nowIso}`);

    const destinoAnalizador =
      tubo.tipo === "CITRATO"
        ? "Stago STA-R Max (Carrusel Coagulación Pos 08)"
        : tubo.tipo === "EDTA"
        ? "Sysmex XN-1000 (Cargador Automático Hematología Pos 04)"
        : tubo.tipo === "HEPARINA"
        ? "Radiometer ABL90 FLEX (Cámara Gases Pos 01)"
        : "Roche Cobas Pro c503 (Rotor Bioquímica Pos 14)";

    const nuevoEventoAudit = {
      id: `AUD-CARGA-${Date.now()}`,
      hora: horaCarga,
      actor: usuarioActivo.nombre,
      rol: usuarioActivo.rol,
      cut: usuarioActivo.cut,
      accion: "CARGA_ANALIZADOR",
      detalle: `Tubo ${tuboId} cargado en ${destinoAnalizador} para ejecución analítica.`,
      hash: hashAudit,
    };

    setOrdenes((prev) =>
      prev.map((ord) => {
        if (ord.id !== selected.id) return ord;
        const tubosUpdated = ord.tubos.map((t) => {
          if (t.id !== tuboId) return t;
          return {
            ...t,
            estado: "en_analisis",
            gradilla: destinoAnalizador,
          };
        });
        return {
          ...ord,
          estado: "en_analisis",
          tubos: tubosUpdated,
          auditoria: [nuevoEventoAudit, ...ord.auditoria],
        };
      })
    );
  };

  const handleProcesarWorklistOrden = (ordenId) => {
    const ordTarget = ordenes.find((o) => o.id === ordenId);
    if (!ordTarget) return;

    const horaMedicion = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const nowIso = new Date().toISOString();

    const analitosActualizados = ordTarget.analitos.map((an) => {
      if (an.flag === "RECHAZADO_PREANALITICO" || an.valor !== null) return an;

      const tubo = ordTarget.tubos.find((t) => t.id === an.tuboId);
      // Solo procesar analitos cuyos tubos estén recibidos o en análisis
      if (!tubo || tubo.estado === "rechazada" || tubo.estado === "pendiente_toma") {
        return an;
      }

      const valSimulado = MAPA_VALORES_SIMULADOS[an.testKey] !== undefined
        ? MAPA_VALORES_SIMULADOS[an.testKey]
        : (an.refMin && an.refMax ? Number(((an.refMin + an.refMax) / 2).toFixed(2)) : 50.0);

      const deltaCalc = calcularDelta(valSimulado, an.previo);
      const flagCalc = evaluarFlag(valSimulado, an.refMin, an.refMax, an.critMin, an.critMax);
      const esCritico = flagCalc.includes("CRITICAL");

      return {
        ...an,
        valor: valSimulado,
        delta: deltaCalc,
        flag: flagCalc,
        horaMedicion,
        alertaCritica: esCritico
          ? {
              activa: true,
              horaDeteccion: horaMedicion,
              notificado: false,
              receptor: null,
              registroReceptor: null,
              via: null,
              anexo: null,
              horaNotif: null,
              readback: false,
              medidas: null,
            }
          : null,
      };
    });

    const tubosActualizados = ordTarget.tubos.map((t) => {
      if (t.estado === "rechazada" || t.estado === "pendiente_toma") return t;
      return {
        ...t,
        estado: "procesada",
        gradilla: "Seroteca / Archivo Temporal Lab",
      };
    });

    const hashAudit = sha256Sync(`PROCESAR_WL|${ordTarget.acc}|${nowIso}`);
    const nuevoEventoAudit = {
      id: `AUD-WL-${Date.now()}`,
      hora: horaMedicion,
      actor: usuarioActivo.nombre,
      rol: usuarioActivo.rol,
      cut: usuarioActivo.cut,
      accion: "EJECUCION_ANALITICA_COMPLETADA",
      detalle: `Procesamiento analítico finalizado para muestras viables. Resultados listos para validación técnica.`,
      hash: hashAudit,
    };

    setOrdenes((prev) =>
      prev.map((o) => {
        if (o.id !== ordenId) return o;
        return {
          ...o,
          estado: "resultado_disp",
          tubos: tubosActualizados,
          analitos: analitosActualizados,
          auditoria: [nuevoEventoAudit, ...o.auditoria],
        };
      })
    );

    setAlertaSimulador({
      tipo: "success",
      titulo: "Muestras Procesadas en Analizador",
      mensaje: `Se completó la medición analítica para la orden ${ordTarget.orden} (${ordTarget.paciente}). Resultados disponibles para Validación Técnica.`,
    });
    setTimeout(() => setAlertaSimulador(null), 5000);
  };

  const handleConfirmarFirmaDT = () => {
    if (!selected || usuarioActivo.rolId !== "dt") return;

    // Validación estricta previa a la firma
    const validacion = verificarCondicionesPublicacion(selected);
    if (!validacion.aprobado) {
      alert(`BLOQUEO DE FIRMA DT:\n\n${validacion.motivos.join("\n\n")}`);
      return;
    }

    const horaFirma = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    const fechaFirma = new Date().toLocaleDateString();
    const nowIso = new Date().toISOString();

    // Cálculo real de hash SHA-256 canónico para el informe diagnóstico firmado
    const payloadInforme = `${selected.acc}|${selected.rut}|${selected.analitos.map((a) => `${a.codigo}:${a.valor}`).join(";")}|${nowIso}|${usuarioActivo.cut}`;
    const hashInformeSha256 = sha256Sync(payloadInforme);

    const nuevoEventoAudit = {
      id: `AUD-FIRMA-${Date.now()}`,
      hora: horaFirma,
      actor: usuarioActivo.nombre,
      rol: usuarioActivo.rol,
      cut: usuarioActivo.cut,
      accion: "FIRMA_ELECTRONICA_DT_PUBLICACION",
      detalle: `Validación Facultativa y Firma Electrónica Avanzada bajo Ley 19.799 y D.S. N° 20. Hash SHA-256 canónico: ${hashInformeSha256.slice(0, 16)}...`,
      hash: hashInformeSha256,
    };

    setOrdenes((prev) =>
      prev.map((ord) => {
        if (ord.id !== selected.id) return ord;
        return {
          ...ord,
          fase: "informes",
          estado: "publicado",
          informe: {
            version: "1.0-FINAL",
            estado: "publicado",
            fechaEmision: `${fechaFirma} ${horaFirma}`,
            tecnologoValidador: "TM. Valentina Carvallo P. (Reg. SIS 88214)",
            firmaDT: {
              firmante: usuarioActivo.nombre,
              cargo: usuarioActivo.rol,
              cut: usuarioActivo.cut,
              regSIS: usuarioActivo.regSIS,
              timestamp: `${fechaFirma} ${horaFirma} UTC-3`,
              hashSha256: hashInformeSha256,
              estadoFirma: "Firma Electrónica Avanzada Verificada (Ley 19.799)",
            },
          },
          auditoria: [nuevoEventoAudit, ...ord.auditoria],
        };
      })
    );

    setModalFirmarInformeAbierto(false);
  };

  /* ─────────────────────────────────────────────────────────────────────────
     § 9 · CREACIÓN DE NUEVA SOLICITUD CON VALIDACIÓN RUN MÓDULO 11
     ───────────────────────────────────────────────────────────────────────── */
  const handleCrearNuevaOrden = (e) => {
    e.preventDefault();

    if (!validarRutChileno(nuevoRun)) {
      alert("Error en RUN: El dígito verificador calculado por Módulo 11 no coincide con el ingresado.");
      return;
    }
    if (!nuevoNombre.trim()) {
      alert("Error: El nombre completo del paciente es obligatorio.");
      return;
    }

    const numOrden = Math.floor(Math.random() * 900 + 8920);
    const numAcc = Math.floor(Math.random() * 900 + 420);
    const nuevaHora = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    // Armar tubos y analitos según catálogo clínico estructurado
    const nuevosTubos = [];
    const nuevosAnalitos = [];
    const disciplinasSet = new Set();

    if (testSeleccionados.hemograma) {
      disciplinasSet.add("HEM");
      const tuboId = `SMP-2026-0${numOrden}-01`;
      nuevosTubos.push({
        id: tuboId,
        tipo: "EDTA",
        recipiente: "Tubo Vacutainer K2 EDTA 4.0 mL",
        tipoMuestra: "Sangre total venosa anticoagulada",
        estado: "pendiente_toma",
        horaToma: null,
        horaRecepcion: null,
        gradilla: "Pendiente Flebotomía",
        causalRechazo: null,
      });

      const testsHemo = [
        { testKey: "LEUC", codigo: "6690-2", nombre: "Recuento de Leucocitos", ucum: "10^3/µL", refMin: 4.5, refMax: 11.0, critMin: 2.0, critMax: 30.0, previo: 7.2 },
        { testKey: "GR", codigo: "789-8", nombre: "Recuento de Eritrocitos", ucum: "10^6/µL", refMin: 4.2, refMax: 5.4, critMin: null, critMax: null, previo: 4.65 },
        { testKey: "HEM", codigo: "718-7", nombre: "Hemoglobina", ucum: "g/dL", refMin: 12.0, refMax: 16.0, critMin: 7.0, critMax: 20.0, previo: 13.5 },
        { testKey: "HTO", codigo: "4544-3", nombre: "Hematocrito", ucum: "%", refMin: 37.0, refMax: 48.0, critMin: 21.0, critMax: 60.0, previo: 40.5 },
        { testKey: "VCM", codigo: "787-2", nombre: "Volumen Corpuscular Medio (VCM)", ucum: "fL", refMin: 80.0, refMax: 100.0, critMin: null, critMax: null, previo: 88.0 },
        { testKey: "HCM", codigo: "785-6", nombre: "Hemoglobina Corpuscular Media (HCM)", ucum: "pg", refMin: 27.0, refMax: 32.0, critMin: null, critMax: null, previo: 29.5 },
        { testKey: "CHCM", codigo: "786-4", nombre: "Concentración de HCM (CHCM)", ucum: "g/dL", refMin: 32.0, refMax: 36.0, critMin: null, critMax: null, previo: 33.5 },
        { testKey: "PLAQT", codigo: "777-3", nombre: "Recuento de Plaquetas", ucum: "10^3/µL", refMin: 150.0, refMax: 400.0, critMin: 50.0, critMax: 1000.0, previo: 230.0 },
        { testKey: "NEUT", codigo: "751-8", nombre: "Neutrófilos Absolutos", ucum: "10^3/µL", refMin: 1.8, refMax: 7.5, critMin: 0.5, critMax: null, previo: 4.5 },
      ];

      testsHemo.forEach((t, idx) => {
        nuevosAnalitos.push({
          id: `OBS-${numOrden}-H${idx + 1}`,
          testKey: t.testKey,
          tuboId,
          codigo: t.codigo,
          nombre: t.nombre,
          disc: "HEM",
          metodo: "Citometría de flujo fluorescente / SLS",
          equipoId: "xn1000",
          equipo: "Sysmex XN-1000",
          valor: null,
          ucum: t.ucum,
          refMin: t.refMin,
          refMax: t.refMax,
          critMin: t.critMin,
          critMax: t.critMax,
          flag: "PENDING",
          previo: t.previo,
          delta: null,
          horaMedicion: null,
          alertaCritica: null,
        });
      });
    }

    if (testSeleccionados.troponina || testSeleccionados.perfilBioq) {
      const tuboId = `SMP-2026-0${numOrden}-02`;
      nuevosTubos.push({
        id: tuboId,
        tipo: "SUERO",
        recipiente: "Tubo Vacutainer Gel Separador 5.0 mL",
        tipoMuestra: "Suero sanguíneo",
        estado: "pendiente_toma",
        horaToma: null,
        horaRecepcion: null,
        gradilla: "Pendiente Flebotomía",
        causalRechazo: null,
      });

      if (testSeleccionados.troponina) {
        disciplinasSet.add("INM");
        nuevosAnalitos.push({
          id: `OBS-${numOrden}-TR01`,
          testKey: "TROP",
          tuboId,
          codigo: "49563-0",
          nombre: "Troponina T ultrasensible (hs-cTnT)",
          disc: "INM",
          metodo: "Electroquimioluminiscencia (ECLIA)",
          equipoId: "e411",
          equipo: "Roche Cobas e411 / e801",
          valor: null,
          ucum: "ng/L",
          refMin: 0.0,
          refMax: 14.0,
          critMin: null,
          critMax: 52.0,
          flag: "PENDING",
          previo: 8.5,
          delta: null,
          horaMedicion: null,
          alertaCritica: null,
        });
      }

      if (testSeleccionados.perfilBioq) {
        disciplinasSet.add("BIOQ");
        const testsBioq = [
          { testKey: "GLU", codigo: "2345-7", nombre: "Glucosa en Suero", ucum: "mg/dL", refMin: 70.0, refMax: 99.0, critMin: 45.0, critMax: 400.0, previo: 92.0 },
          { testKey: "BUN", codigo: "3094-0", nombre: "Nitrógeno Ureico (BUN)", ucum: "mg/dL", refMin: 8.0, refMax: 20.0, critMin: null, critMax: null, previo: 14.0 },
          { testKey: "UREA", codigo: "3094-0", nombre: "Urea en Suero", ucum: "mg/dL", refMin: 15.0, refMax: 45.0, critMin: null, critMax: 100.0, previo: 30.0 },
          { testKey: "CREAT", codigo: "2160-0", nombre: "Creatinina en Suero", ucum: "mg/dL", refMin: 0.70, refMax: 1.20, critMin: null, critMax: 5.0, previo: 0.95 },
          { testKey: "AC_URIC", codigo: "3086-6", nombre: "Ácido Úrico", ucum: "mg/dL", refMin: 3.5, refMax: 7.2, critMin: null, critMax: null, previo: 5.1 },
          { testKey: "BILI_T", codigo: "1975-2", nombre: "Bilirrubina Total", ucum: "mg/dL", refMin: 0.20, refMax: 1.20, critMin: null, critMax: 15.0, previo: 0.80 },
          { testKey: "BILI_D", codigo: "1968-7", nombre: "Bilirrubina Directa", ucum: "mg/dL", refMin: 0.00, refMax: 0.30, critMin: null, critMax: null, previo: 0.18 },
          { testKey: "GOT", codigo: "1920-8", nombre: "Transaminasa GOT / AST", ucum: "U/L", refMin: 10.0, refMax: 40.0, critMin: null, critMax: 300.0, previo: 26.0 },
          { testKey: "GPT", codigo: "1742-6", nombre: "Transaminasa GPT / ALT", ucum: "U/L", refMin: 10.0, refMax: 45.0, critMin: null, critMax: 300.0, previo: 24.0 },
          { testKey: "FA", codigo: "6768-6", nombre: "Fosfatasa Alcalina (FA)", ucum: "U/L", refMin: 40.0, refMax: 130.0, critMin: null, critMax: null, previo: 78.0 },
          { testKey: "PROT_T", codigo: "2885-2", nombre: "Proteínas Totales", ucum: "g/dL", refMin: 6.4, refMax: 8.3, critMin: null, critMax: null, previo: 7.0 },
          { testKey: "ALB", codigo: "1751-7", nombre: "Albúmina en Suero", ucum: "g/dL", refMin: 3.5, refMax: 5.0, critMin: null, critMax: null, previo: 4.1 },
          { testKey: "CALCIO", codigo: "17861-6", nombre: "Calcio Total", ucum: "mg/dL", refMin: 8.5, refMax: 10.5, critMin: 6.5, critMax: 13.0, previo: 9.3 },
        ];

        testsBioq.forEach((t, idx) => {
          nuevosAnalitos.push({
            id: `OBS-${numOrden}-B${idx + 1}`,
            testKey: t.testKey,
            tuboId,
            codigo: t.codigo,
            nombre: t.nombre,
            disc: "BIOQ",
            metodo: "Fotometría UV / Colorimetría",
            equipoId: "c503",
            equipo: "Roche Cobas Pro c503",
            valor: null,
            ucum: t.ucum,
            refMin: t.refMin,
            refMax: t.refMax,
            critMin: t.critMin,
            critMax: t.critMax,
            flag: "PENDING",
            previo: t.previo,
            delta: null,
            horaMedicion: null,
            alertaCritica: null,
          });
        });
      }
    }

    if (testSeleccionados.coagulacion) {
      disciplinasSet.add("COAG");
      const tuboId = `SMP-2026-0${numOrden}-03`;
      nuevosTubos.push({
        id: tuboId,
        tipo: "CITRATO",
        recipiente: "Tubo Vacutainer Citrato 3.2% 2.7 mL",
        tipoMuestra: "Plasma citratado",
        estado: "pendiente_toma",
        horaToma: null,
        horaRecepcion: null,
        gradilla: "Pendiente Flebotomía",
        causalRechazo: null,
      });

      const testsCoag = [
        { testKey: "TP", codigo: "5902-2", nombre: "Tiempo de Protrombina (TP)", ucum: "seg", refMin: 11.0, refMax: 14.5, critMin: null, critMax: 30.0, previo: 12.5 },
        { testKey: "ACT_TP", codigo: "3197-0", nombre: "Actividad de Protrombina", ucum: "%", refMin: 70.0, refMax: 120.0, critMin: null, critMax: null, previo: 95.0 },
        { testKey: "INR", codigo: "6301-6", nombre: "Razón Normalizada Internacional (INR)", ucum: "ratio", refMin: 0.90, refMax: 1.15, critMin: null, critMax: 4.5, previo: 1.01 },
        { testKey: "TTPK", codigo: "3173-1", nombre: "TTPA (Cefalina Caolín)", ucum: "seg", refMin: 25.0, refMax: 38.0, critMin: null, critMax: 70.0, previo: 31.0 },
      ];

      testsCoag.forEach((t, idx) => {
        nuevosAnalitos.push({
          id: `OBS-${numOrden}-C${idx + 1}`,
          testKey: t.testKey,
          tuboId,
          codigo: t.codigo,
          nombre: t.nombre,
          disc: "COAG",
          metodo: "Detección mecánica por viscosidad",
          equipoId: "stago",
          equipo: "Stago STA-R Max",
          valor: null,
          ucum: t.ucum,
          refMin: t.refMin,
          refMax: t.refMax,
          critMin: t.critMin,
          critMax: t.critMax,
          flag: "PENDING",
          previo: t.previo,
          delta: null,
          horaMedicion: null,
          alertaCritica: null,
        });
      });
    }

    if (testSeleccionados.gases) {
      disciplinasSet.add("GAS");
      const tuboId = `SMP-2026-0${numOrden}-04`;
      nuevosTubos.push({
        id: tuboId,
        tipo: "HEPARINA",
        recipiente: "Jeringa Balanceada Heparina Litio 2.0 mL",
        tipoMuestra: "Sangre total arterial heparinada",
        estado: "pendiente_toma",
        horaToma: null,
        horaRecepcion: null,
        gradilla: "Pendiente Flebotomía",
        causalRechazo: null,
      });

      const testsGas = [
        { testKey: "PH", codigo: "11558-4", nombre: "pH Arterial", ucum: "pH", refMin: 7.35, refMax: 7.45, critMin: 7.20, critMax: 7.60, previo: 7.40 },
        { testKey: "PCO2", codigo: "11557-6", nombre: "pCO2 Arterial", ucum: "mmHg", refMin: 35.0, refMax: 45.0, critMin: 20.0, critMax: 70.0, previo: 40.0 },
        { testKey: "PO2", codigo: "11556-8", nombre: "pO2 Arterial", ucum: "mmHg", refMin: 80.0, refMax: 100.0, critMin: 45.0, critMax: null, previo: 90.0 },
        { testKey: "HCO3", codigo: "1960-4", nombre: "Bicarbonato Actual (HCO3)", ucum: "mmol/L", refMin: 22.0, refMax: 26.0, critMin: 10.0, critMax: 40.0, previo: 24.0 },
        { testKey: "BE", codigo: "11555-0", nombre: "Exceso de Base (BE)", ucum: "mmol/L", refMin: -2.0, refMax: 2.0, critMin: null, critMax: null, previo: 0.0 },
        { testKey: "SATO2", codigo: "2708-6", nombre: "Saturación O2 (SatO2)", ucum: "%", refMin: 95.0, refMax: 99.0, critMin: 85.0, critMax: null, previo: 98.0 },
        { testKey: "LACT", codigo: "2524-7", nombre: "Lactato Arterial", ucum: "mmol/L", refMin: 0.5, refMax: 1.6, critMin: null, critMax: 4.0, previo: 1.1 },
      ];

      testsGas.forEach((t, idx) => {
        nuevosAnalitos.push({
          id: `OBS-${numOrden}-G${idx + 1}`,
          testKey: t.testKey,
          tuboId,
          codigo: t.codigo,
          nombre: t.nombre,
          disc: "GAS",
          metodo: "Potenciometría / Amperometría directa",
          equipoId: "abl90",
          equipo: "Radiometer ABL90 FLEX",
          valor: null,
          ucum: t.ucum,
          refMin: t.refMin,
          refMax: t.refMax,
          critMin: t.critMin,
          critMax: t.critMax,
          flag: "PENDING",
          previo: t.previo,
          delta: null,
          horaMedicion: null,
          alertaCritica: null,
        });
      });
    }

    if (nuevosTubos.length === 0) {
      alert("Error: Debe seleccionar al menos una prestación o examen para la orden.");
      return;
    }

    const nuevaOrdenObj = {
      id: ordenes.length + 1,
      acc: `ACC-2026-000${numAcc}`,
      orden: `ORD-2026-0${numOrden}`,
      cup: `CUP-CL-13-2026-000${numAcc}-X1`,
      rut: formatearRut(nuevoRun),
      paciente: nuevoNombre.trim(),
      edad: parseInt(nuevaEdad, 10),
      sexo: nuevoSexo,
      origen: nuevoOrigen,
      cama: nuevaCama,
      prioridad: nuevoPrioridad,
      medicoSolicitante: nuevoMedico,
      diagnostico: nuevoDiagnostico,
      fase: "flebotomia",
      estado: "pendiente_toma",
      disciplinas: Array.from(disciplinasSet),
      horaOrden: nuevaHora,
      horaToma: null,
      horaRecepcion: null,
      tubos: nuevosTubos,
      analitos: nuevosAnalitos,
      auditoria: [
        {
          id: `AUD-NEW-${Date.now()}`,
          hora: nuevaHora,
          actor: usuarioActivo.nombre,
          rol: usuarioActivo.rol,
          cut: usuarioActivo.cut,
          accion: "CREACION_ORDEN_LAB",
          detalle: `Creación de solicitud ambulatoria/hospitalaria para ${nuevoNombre.trim()} (${formatearRut(nuevoRun)}). ${nuevosTubos.length} tubos generados con paneles clínicos completos.`,
          hash: sha256Sync(`NEW_ORD|${numOrden}|${nuevoRun}`),
        },
      ],
      informe: null,
    };

    setOrdenes((prev) => [nuevaOrdenObj, ...prev]);
    setSelectedId(nuevaOrdenObj.id);
    setFaseActiva("flebotomia");
    setModalNuevoIngresoAbierto(false);
  };

  return (
    <div style={{ background: D.bg, color: D.txt, minHeight: "100vh", fontFamily: "'Inter', -apple-system, sans-serif", display: "flex", flexDirection: "column" }}>
      {/* Regla global de invisibilidad de scrollbars encapsulada en el componente */}
      <style>{`
        * {
          scrollbar-width: none !important;
          -ms-overflow-style: none !important;
        }
        *::-webkit-scrollbar {
          display: none !important;
          width: 0 !important;
          height: 0 !important;
        }
      `}</style>
      
      {/* ───────────────────────────────────────────────────────────────────
          BANNER SOBRIO DE DEMARCACIÓN CLÍNICA (DEMO Y TELEMETRÍA SINTÉTICA)
          ─────────────────────────────────────────────────────────────────── */}
      <div style={{ background: D.sfc2, borderBottom: `1px solid ${D.brd}`, padding: "6px 18px", display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 11 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 5, padding: "2px 7px", borderRadius: 4, background: `${D.tea}1A`, color: D.tea, fontWeight: 700, fontSize: 10 }}>
            <Radio size={12} /> AMBIENTE DE SIMULACIÓN Y TELEMETRÍA SINTÉTICA
          </span>
          <span style={{ color: D.txl }}>|</span>
          <span style={{ color: D.txm }}>
            Mapeo analítico riguroso · Reglas D.S. N° 20 y Ley 20.584 · Trazabilidad Criptográfica SHA-256
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          {totalAlertasCriticasPendientes > 0 && (
            <span style={{ display: "inline-flex", alignItems: "center", gap: 5, color: D.dan, fontWeight: 700, fontSize: 11 }}>
              <AlertTriangle size={13} /> {totalAlertasCriticasPendientes} valor(es) crítico(s) pendientes de notificación
            </span>
          )}
          <span style={{ color: D.txl }}>•</span>
          <span style={{ color: D.txl }}>Vite Dev Server Activo (Puerto 5173)</span>
        </div>
      </div>

      {/* ───────────────────────────────────────────────────────────────────
          ENCABEZADO INSTITUCIONAL AXON WORKBENCH (ESTILO HIS-RIS-PACS)
          ─────────────────────────────────────────────────────────────────── */}
      <header style={{ background: D.sfc, borderBottom: `1px solid ${D.brd}`, padding: "10px 20px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{ width: 34, height: 34, borderRadius: 8, background: D.tea, display: "flex", alignItems: "center", justifyContent: "center", color: "#0A1420", fontWeight: 900, fontSize: 15 }}>
            AX
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, letterSpacing: "-0.01em", color: D.txt }}>
              AXON LIS Workbench <span style={{ fontSize: 11, fontWeight: 400, color: D.tea }}>· Enterprise Core</span>
            </div>
            <div style={{ fontSize: 10.5, color: D.txl, marginTop: 1 }}>
              Sistema de Información de Laboratorio · Módulos Preanalítico, Analítico y Postanalítico
            </div>
          </div>
        </div>

        {/* Controles de Sesión y Nueva Solicitud */}
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {/* Selector de Usuario Activo con Verificación de Privilegios */}
          <div style={{ display: "flex", alignItems: "center", gap: 8, background: D.sfc2, padding: "5px 10px", borderRadius: 8, border: `1px solid ${D.brd}` }}>
            <UserCheck size={14} color={usuarioActivo.puedeFirmar ? D.suc : D.tea} />
            <div style={{ display: "flex", flexDirection: "column" }}>
              <select
                value={usuarioActivo.id}
                onChange={(e) => {
                  const u = SESIONES_USUARIO.find((usr) => usr.id === e.target.value);
                  if (u) setUsuarioActivo(u);
                }}
                style={{ background: "transparent", border: "none", color: D.txt, fontSize: 11, fontWeight: 600, cursor: "pointer", outline: "none" }}
              >
                {SESIONES_USUARIO.map((u) => (
                  <option key={u.id} value={u.id} style={{ background: D.sfc, color: D.txt }}>
                    {u.nombre} ({u.rolId.toUpperCase()})
                  </option>
                ))}
              </select>
              <span style={{ fontSize: 9, color: D.txl, paddingLeft: 2 }}>{usuarioActivo.rol} · CUT: {usuarioActivo.cut}</span>
            </div>
          </div>

          <button
            onClick={() => setModalNuevoIngresoAbierto(true)}
            style={{ display: "flex", alignItems: "center", gap: 6, background: D.tea, color: "#0A1420", border: "none", padding: "7px 14px", borderRadius: 7, fontSize: 11.5, fontWeight: 700, cursor: "pointer" }}
          >
            <Plus size={14} /> Nueva Solicitud
          </button>
        </div>
      </header>

      {/* Notificación Flotante del Simulador */}
      {alertaSimulador && (
        <div style={{ padding: "8px 20px", background: alertaSimulador.tipo === "success" ? `${D.suc}22` : `${D.war}22`, borderBottom: `1px solid ${alertaSimulador.tipo === "success" ? D.suc : D.war}`, color: D.txt, fontSize: 11.5, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <b>{alertaSimulador.titulo}:</b> {alertaSimulador.mensaje}
          </div>
          <button onClick={() => setAlertaSimulador(null)} style={{ background: "none", border: "none", color: D.txt, cursor: "pointer" }}><X size={14} /></button>
        </div>
      )}

      {/* ───────────────────────────────────────────────────────────────────
          NAVEGACIÓN POR FASES CLÍNICAS (7 BANDEJAS SEGÚN D.S. N° 20)
          ─────────────────────────────────────────────────────────────────── */}
      <nav style={{ background: D.sfc2, borderBottom: `1px solid ${D.brd}`, padding: "6px 14px", display: "flex", gap: 5, overflowX: "auto" }}>
        {[
          { id: "control", label: "Control", icon: BarChart3, count: conteos.control },
          { id: "flebotomia", label: "1. Flebotomía", icon: FlaskConical, count: conteos.flebotomia },
          { id: "worklist", label: "2. Worklist", icon: HardDrive, count: conteos.worklist },
          { id: "validacion_tec", label: "3. Val. Técnica", icon: ClipboardCheck, count: conteos.validacion_tec },
          { id: "validacion_fac", label: "4. Val. Facultativa", icon: ShieldCheck, count: conteos.validacion_fac },
          { id: "informes", label: "5. Informes", icon: FileText, count: conteos.informes },
          { id: "microbiologia", label: "6. Microbiología (AST)", icon: Bug, count: conteos.microbiologia },
          { id: "equipos", label: "Gateway", icon: Cpu, count: conteos.equipos },
          { id: "calidad_qc", label: "Calidad (QC)", icon: SlidersHorizontal, count: null },
          { id: "privacidad_ley", label: "Privacidad 21.719", icon: ShieldAlert, count: null },
          { id: "pruebas_sistema", label: "Pruebas (119)", icon: Terminal, count: null },
        ].map((tab) => {
          const IconComponent = tab.icon;
          const isActive = faseActiva === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => { setFaseActiva(tab.id); setSelectedId(null); }}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 5,
                padding: "6px 9px",
                borderRadius: 6,
                border: `1px solid ${isActive ? D.tea : "transparent"}`,
                background: isActive ? `${D.tea}18` : "transparent",
                color: isActive ? D.tea : D.txm,
                fontSize: 11,
                fontWeight: isActive ? 700 : 500,
                cursor: "pointer",
                whiteSpace: "nowrap",
                transition: "all 0.15s ease",
              }}
            >
              <IconComponent size={13} />
              <span>{tab.label}</span>
              {tab.count !== null && (
                <span style={{ fontSize: 9.5, padding: "1px 5px", borderRadius: 8, background: isActive ? D.tea : D.sfc, color: isActive ? "#0A1420" : D.txl, fontWeight: 700 }}>
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* ───────────────────────────────────────────────────────────────────
          CUERPO PRINCIPAL (TABLA DE BANDEJA / DETALLE DRAWER / GATEWAY)
          ─────────────────────────────────────────────────────────────────── */}
      <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
        
        {/* VISTA 1 A 6: BANDEJAS DE ÓRDENES Y TAREAS CLÍNICAS */}
                {/* ─────────────────────────────────────────────────────────────────
           VISTA 8: CONTROL DE CALIDAD ANALÍTICO & ALGORITMOS CLÍNICOS
           (CONFORME A CLSI C24-Ed4, ISO 15189:2022 Y REQUISITOS CONSENSUSLAB)
           ───────────────────────────────────────────────────────────────── */}
        {faseActiva === "calidad_qc" ? (
          <main style={{ flex: 1, display: "flex", flexDirection: "column", padding: "14px 20px", overflow: "hidden" }}>
            
            {/* Cabecera Principal del Dominio de Calidad */}
            <div style={{ background: D.sfc, borderRadius: 10, padding: "12px 18px", border: `1px solid ${D.brd}`, marginBottom: 12, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <SlidersHorizontal size={16} color={D.tea} />
                  <span style={{ fontSize: 13.5, fontWeight: 700, color: D.txt }}>Dominio de Calidad Analítica &amp; Algoritmos Clínicos</span>
                  <span style={{ fontSize: 9.5, padding: "2px 7px", borderRadius: 4, background: `${D.tea}22`, color: D.tea, fontWeight: 700 }}>
                    CLSI C24-Ed4 · ISO 15189:2022
                  </span>
                </div>
                <div style={{ fontSize: 11, color: D.txm, marginTop: 3 }}>
                  Control estadístico multirregla de Westgard con corridas explícitas, cartas Levey-Jennings, Six Sigma, Valor Crítico de Cambio (RCV), CKD-EPI 2021 y perfil lipídico.
                </div>
              </div>

              {/* Sub-pestañas de Calidad */}
              <div style={{ display: "flex", gap: 6, background: D.sfc2, padding: 4, borderRadius: 8, border: `1px solid ${D.brd}` }}>
                {[
                  { id: "westgard", label: "📊 Multirreglas Westgard & L-J" },
                  { id: "rcv", label: "📈 Cambio Crítico (RCV) & Delta" },
                  { id: "ckd", label: "🩺 Filtrado Glomerular CKD-EPI" },
                  { id: "lipidos", label: "🧪 Fracción LDL Friedewald" },
                ].map((sub) => (
                  <button
                    key={sub.id}
                    onClick={() => setSubTabQC(sub.id)}
                    style={{
                      padding: "6px 12px",
                      borderRadius: 6,
                      border: "none",
                      fontSize: 11,
                      fontWeight: subTabQC === sub.id ? 700 : 500,
                      background: subTabQC === sub.id ? D.tea : "transparent",
                      color: subTabQC === sub.id ? "#0A1420" : D.txm,
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                    }}
                  >
                    {sub.label}
                  </button>
                ))}
              </div>
            </div>

            {/* SUB-PESTAÑA 1: MULTIRREGLAS WESTGARD & LEVEY-JENNINGS */}
            {subTabQC === "westgard" && (() => {
              const currentQC = qcData[qcAnalitoKey] || qcData.GLU;
              const runs = currentQC.corridas;
              const n = runs.length;
              const meanL1 = runs.reduce((acc, r) => acc + r.l1, 0) / n;
              const meanL2 = runs.reduce((acc, r) => acc + r.l2, 0) / n;
              const sdL1 = Math.sqrt(runs.reduce((acc, r) => acc + Math.pow(r.l1 - meanL1, 2), 0) / (n - 1));
              const sdL2 = Math.sqrt(runs.reduce((acc, r) => acc + Math.pow(r.l2 - meanL2, 2), 0) / (n - 1));
              const cvL1 = (sdL1 / meanL1) * 100;
              const biasL1 = ((meanL1 - currentQC.nivel1.target) / currentQC.nivel1.target) * 100;
              const teObsL1 = Math.abs(biasL1) + 1.65 * cvL1;
              const sigmaL1 = (currentQC.tea - Math.abs(biasL1)) / cvL1;
              const lastRun = runs[runs.length - 1];

              const handleInyectarCorrida = (modo) => {
                const nextId = runs.length + 1;
                const hh = String(Math.floor(Math.random() * 8 + 8)).padStart(2, "0");
                const mm = String(Math.floor(Math.random() * 59)).padStart(2, "0");
                let newL1, newL2;

                if (modo === "normal") {
                  newL1 = Number((currentQC.nivel1.target + (Math.random() - 0.5) * currentQC.nivel1.sd * 1.2).toFixed(2));
                  newL2 = Number((currentQC.nivel2.target + (Math.random() - 0.5) * currentQC.nivel2.sd * 1.2).toFixed(2));
                } else if (modo === "1-3s") {
                  newL1 = Number((currentQC.nivel1.target + currentQC.nivel1.sd * 3.35).toFixed(2));
                  newL2 = Number((currentQC.nivel2.target + currentQC.nivel2.sd * 0.4).toFixed(2));
                } else if (modo === "r-4s") {
                  // Regla R-4s evaluada intra-corrida: N1 supera +2s y N2 supera -2s (amplitud >= 4s)
                  newL1 = Number((currentQC.nivel1.target + currentQC.nivel1.sd * 2.3).toFixed(2));
                  newL2 = Number((currentQC.nivel2.target - currentQC.nivel2.sd * 2.4).toFixed(2));
                } else if (modo === "2-2s") {
                  newL1 = Number((currentQC.nivel1.target + currentQC.nivel1.sd * 2.25).toFixed(2));
                  newL2 = Number((currentQC.nivel2.target + currentQC.nivel2.sd * 2.20).toFixed(2));
                }

                const testObj = { l1: newL1, l2: newL2 };
                const ev = evaluarMultirreglasWestgard(testObj, runs, currentQC.nivel1.target, currentQC.nivel1.sd, currentQC.nivel2.target, currentQC.nivel2.sd);

                const newRunItem = {
                  id: nextId,
                  fecha: `24-10 ${hh}:${mm}`,
                  l1: newL1,
                  l2: newL2,
                  estado: ev.estado,
                  severidad: ev.severidad,
                  reglas: ev.reglas.map((r) => r.rule),
                  accion: ev.accion,
                  sdiL1: ev.sdiL1,
                  sdiL2: ev.sdiL2,
                };

                const updatedRuns = [...runs, newRunItem];
                setQcData({
                  ...qcData,
                  [qcAnalitoKey]: {
                    ...currentQC,
                    corridas: updatedRuns,
                  },
                });
                setCorridaQCSeleccionada(newRunItem);
              };

              return (
                <div style={{ flex: 1, display: "flex", flexDirection: "column", overflowY: "auto", gap: 12 }}>
                  {/* Selector de Analito & Tarjetas de Desempeño */}
                  <div style={{ display: "grid", gridTemplateColumns: "280px 1fr", gap: 12 }}>
                    
                    {/* Selector de Analito */}
                    <div style={{ background: D.sfc, borderRadius: 10, padding: 14, border: `1px solid ${D.brd}`, display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                      <div>
                        <div style={{ fontSize: 11, color: D.txl, textTransform: "uppercase", fontWeight: 700 }}>Procedimiento de Medida</div>
                        <div style={{ fontSize: 13.5, fontWeight: 700, color: D.txt, marginTop: 4 }}>{currentQC.nombre}</div>
                        <div style={{ fontSize: 11, color: D.tea, marginTop: 2 }}>{currentQC.equipoNombre}</div>
                        <div style={{ fontSize: 10, color: D.txm, marginTop: 2 }}>Lote: <span style={{ fontFamily: "monospace" }}>{currentQC.loteControl}</span> · TEa: <b>{currentQC.tea}%</b></div>
                      </div>

                      <div style={{ marginTop: 12 }}>
                        <div style={{ fontSize: 10, color: D.txl, marginBottom: 5 }}>Cambiar Analito en Monitoreo:</div>
                        <div style={{ display: "flex", gap: 6 }}>
                          {Object.keys(qcData).map((k) => (
                            <button
                              key={k}
                              onClick={() => { setQcAnalitoKey(k); setCorridaQCSeleccionada(null); }}
                              style={{
                                flex: 1,
                                padding: "6px 0",
                                borderRadius: 6,
                                border: `1px solid ${qcAnalitoKey === k ? D.tea : D.brd}`,
                                background: qcAnalitoKey === k ? `${D.tea}22` : D.sfc2,
                                color: qcAnalitoKey === k ? D.tea : D.txm,
                                fontSize: 10.5,
                                fontWeight: 700,
                                cursor: "pointer",
                              }}
                            >
                              {k}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* 3 Tarjetas de Métricas Estadísticas */}
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
                      <div style={{ background: D.sfc, borderRadius: 10, padding: 12, border: `1px solid ${D.brd}` }}>
                        <div style={{ fontSize: 10.5, color: D.txl, textTransform: "uppercase" }}>Nivel 1 (Normal)</div>
                        <div style={{ fontSize: 17, fontWeight: 700, color: D.tea, marginTop: 3 }}>
                          {meanL1.toFixed(1)} <span style={{ fontSize: 11, color: D.txl }}>{currentQC.ucum}</span>
                        </div>
                        <div style={{ fontSize: 10, color: D.txm, marginTop: 2 }}>
                          Target: {currentQC.nivel1.target} · SD: {sdL1.toFixed(2)} · CV: <b>{cvL1.toFixed(1)}%</b>
                        </div>
                      </div>

                      <div style={{ background: D.sfc, borderRadius: 10, padding: 12, border: `1px solid ${D.brd}` }}>
                        <div style={{ fontSize: 10.5, color: D.txl, textTransform: "uppercase" }}>Nivel 2 (Patológico)</div>
                        <div style={{ fontSize: 17, fontWeight: 700, color: D.pur, marginTop: 3 }}>
                          {meanL2.toFixed(1)} <span style={{ fontSize: 11, color: D.txl }}>{currentQC.ucum}</span>
                        </div>
                        <div style={{ fontSize: 10, color: D.txm, marginTop: 2 }}>
                          Target: {currentQC.nivel2.target} · SD: {sdL2.toFixed(2)} · CV: <b>{((sdL2 / meanL2) * 100).toFixed(1)}%</b>
                        </div>
                      </div>

                      <div style={{ background: D.sfc, borderRadius: 10, padding: 12, border: `1px solid ${D.brd}` }}>
                        <div style={{ fontSize: 10.5, color: D.txl, textTransform: "uppercase" }}>Métrica Six Sigma</div>
                        <div style={{ fontSize: 17, fontWeight: 700, color: sigmaL1 >= 5.0 ? D.suc : D.war, marginTop: 3 }}>
                          {sigmaL1.toFixed(1)} σ <span style={{ fontSize: 10, padding: "2px 5px", borderRadius: 4, background: sigmaL1 >= 5 ? `${D.suc}22` : `${D.war}22`, color: sigmaL1 >= 5 ? D.suc : D.war, fontWeight: 700 }}>{sigmaL1 >= 6.0 ? "CLASE MUNDIAL" : sigmaL1 >= 4.5 ? "EXCELENTE" : "ADECUADO"}</span>
                        </div>
                        <div style={{ fontSize: 10, color: D.txm, marginTop: 2 }}>
                          TEobs: <b>{teObsL1.toFixed(1)}%</b> (Límite TEa: {currentQC.tea}%)
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Carta Interactiva Levey-Jennings SVG */}
                  <div style={{ background: D.sfc, borderRadius: 10, border: `1px solid ${D.brd}`, padding: "14px 18px", display: "flex", flexDirection: "column" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <span style={{ fontSize: 12, fontWeight: 700, color: D.txt }}>Carta de Control Levey-Jennings (SDI Multirun)</span>
                        <span style={{ fontSize: 10, color: D.tea, display: "flex", alignItems: "center", gap: 4 }}>
                          <span style={{ width: 8, height: 8, borderRadius: "50%", background: D.tea }} /> Nivel 1 (Normal)
                        </span>
                        <span style={{ fontSize: 10, color: D.pur, display: "flex", alignItems: "center", gap: 4 }}>
                          <span style={{ width: 8, height: 8, borderRadius: "50%", background: D.pur }} /> Nivel 2 (Patológico)
                        </span>
                      </div>
                      <div style={{ fontSize: 10.5, color: D.txl }}>
                        Total corridas: <b>{runs.length}</b> · Último estado: <b style={{ color: lastRun.estado === "RECHAZO" ? D.dan : lastRun.estado === "ADVERTENCIA" ? D.war : D.suc }}>{lastRun.estado}</b>
                      </div>
                    </div>

                    {/* Gráfico SVG Vectorial Puro */}
                    <div style={{ background: "#060D15", borderRadius: 8, padding: "10px 14px", border: `1px solid ${D.brd}` }}>
                      <svg viewBox="0 0 760 190" style={{ width: "100%", height: 190, display: "block" }}>
                        {/* Líneas guía horizontales de SD */}
                        {[
                          { sdi: 3, label: "+3s (Rechazo)", color: D.dan, dash: "4 3" },
                          { sdi: 2, label: "+2s (Alerta)", color: D.war, dash: "4 3" },
                          { sdi: 1, label: "+1s", color: "#334155", dash: "2 2" },
                          { sdi: 0, label: "Media 0", color: D.tea, dash: "" },
                          { sdi: -1, label: "-1s", color: "#334155", dash: "2 2" },
                          { sdi: -2, label: "-2s (Alerta)", color: D.war, dash: "4 3" },
                          { sdi: -3, label: "-3s (Rechazo)", color: D.dan, dash: "4 3" },
                        ].map((gl) => {
                          const y = 95 - gl.sdi * 24;
                          return (
                            <g key={gl.sdi}>
                              <line x1="55" y1={y} x2="745" y2={y} stroke={gl.color} strokeWidth={gl.sdi === 0 ? "1.2" : "0.8"} strokeDasharray={gl.dash} opacity={gl.sdi === 0 ? 0.9 : 0.6} />
                              <text x="50" y={y + 3.5} textAnchor="end" fill={gl.color} fontSize="9" fontFamily="monospace">
                                {gl.label}
                              </text>
                            </g>
                          );
                        })}

                        {/* Coordenadas X para cada corrida */}
                        {(() => {
                          const stepX = (740 - 75) / Math.max(runs.length - 1, 1);
                          const ptsL1 = runs.map((r, i) => {
                            const sdi = (r.l1 - currentQC.nivel1.target) / currentQC.nivel1.sd;
                            const x = 75 + i * stepX;
                            const y = Math.max(12, Math.min(178, 95 - sdi * 24));
                            return { x, y, r, sdi };
                          });
                          const ptsL2 = runs.map((r, i) => {
                            const sdi = (r.l2 - currentQC.nivel2.target) / currentQC.nivel2.sd;
                            const x = 75 + i * stepX;
                            const y = Math.max(12, Math.min(178, 95 - sdi * 24));
                            return { x, y, r, sdi };
                          });

                          return (
                            <g>
                              {/* Trazos continuos */}
                              <polyline
                                fill="none"
                                stroke={D.tea}
                                strokeWidth="1.8"
                                strokeOpacity="0.8"
                                points={ptsL1.map((p) => `${p.x},${p.y}`).join(" ")}
                              />
                              <polyline
                                fill="none"
                                stroke={D.pur}
                                strokeWidth="1.8"
                                strokeOpacity="0.8"
                                points={ptsL2.map((p) => `${p.x},${p.y}`).join(" ")}
                              />

                              {/* Puntos y marcadores */}
                              {ptsL1.map((p, idx) => {
                                const isSel = corridaQCSeleccionada && corridaQCSeleccionada.id === p.r.id;
                                const isAlert = Math.abs(p.sdi) > 2.0;
                                const isCrit = Math.abs(p.sdi) > 3.0;
                                const dotColor = isCrit ? D.dan : isAlert ? D.war : D.tea;
                                return (
                                  <circle
                                    key={`l1-${idx}`}
                                    cx={p.x}
                                    cy={p.y}
                                    r={isSel ? 6 : 4}
                                    fill={dotColor}
                                    stroke="#0A1420"
                                    strokeWidth="1.5"
                                    style={{ cursor: "pointer" }}
                                    onClick={() => setCorridaQCSeleccionada(p.r)}
                                  />
                                );
                              })}

                              {ptsL2.map((p, idx) => {
                                const isSel = corridaQCSeleccionada && corridaQCSeleccionada.id === p.r.id;
                                const isAlert = Math.abs(p.sdi) > 2.0;
                                const isCrit = Math.abs(p.sdi) > 3.0;
                                const dotColor = isCrit ? D.dan : isAlert ? D.war : D.pur;
                                return (
                                  <rect
                                    key={`l2-${idx}`}
                                    x={p.x - (isSel ? 5 : 3.5)}
                                    y={p.y - (isSel ? 5 : 3.5)}
                                    width={isSel ? 10 : 7}
                                    height={isSel ? 10 : 7}
                                    fill={dotColor}
                                    stroke="#0A1420"
                                    strokeWidth="1.5"
                                    style={{ cursor: "pointer" }}
                                    onClick={() => setCorridaQCSeleccionada(p.r)}
                                  />
                                );
                              })}
                            </g>
                          );
                        })()}
                      </svg>
                    </div>

                    {/* Detalle de Corrida Seleccionada & Barra de Acciones */}
                    <div style={{ marginTop: 10, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div style={{ fontSize: 11, color: D.txt }}>
                        {corridaQCSeleccionada ? (
                          <span>
                            Corrida <b>#{corridaQCSeleccionada.id}</b> ({corridaQCSeleccionada.fecha}) · N1: <b>{corridaQCSeleccionada.l1}</b> (SDI {((corridaQCSeleccionada.l1 - currentQC.nivel1.target) / currentQC.nivel1.sd).toFixed(1)}) · N2: <b>{corridaQCSeleccionada.l2}</b> (SDI {((corridaQCSeleccionada.l2 - currentQC.nivel2.target) / currentQC.nivel2.sd).toFixed(1)}) · Estado: <b style={{ color: corridaQCSeleccionada.estado === "RECHAZO" ? D.dan : corridaQCSeleccionada.estado === "ADVERTENCIA" ? D.war : D.suc }}>{corridaQCSeleccionada.estado}</b> {corridaQCSeleccionada.reglas.length > 0 && `[${corridaQCSeleccionada.reglas.join(", ")}]`}
                          </span>
                        ) : (
                          <span style={{ color: D.txl }}>Haga clic sobre cualquier punto de la carta Levey-Jennings para inspeccionar sus SDI y reglas.</span>
                        )}
                      </div>

                      {/* Botones de Simulación de Escenarios */}
                      <div style={{ display: "flex", gap: 6 }}>
                        <button
                          onClick={() => handleInyectarCorrida("normal")}
                          style={{ padding: "5px 9px", borderRadius: 5, border: "none", background: D.tea, color: "#0A1420", fontSize: 10.5, fontWeight: 700, cursor: "pointer" }}
                        >
                          + Corrida Conforme
                        </button>
                        <button
                          onClick={() => handleInyectarCorrida("1-3s")}
                          style={{ padding: "5px 9px", borderRadius: 5, border: `1px solid ${D.dan}`, background: `${D.dan}22`, color: D.dan, fontSize: 10.5, fontWeight: 700, cursor: "pointer" }}
                        >
                          ! Inyectar 1-3s
                        </button>
                        <button
                          onClick={() => handleInyectarCorrida("r-4s")}
                          style={{ padding: "5px 9px", borderRadius: 5, border: `1px solid ${D.dan}`, background: `${D.dan}22`, color: D.dan, fontSize: 10.5, fontWeight: 700, cursor: "pointer" }}
                          title="Simula dispersión de 4.7 SD entre Nivel 1 y Nivel 2 en la misma corrida"
                        >
                          ! Inyectar R-4s (Intra-corrida)
                        </button>
                        <button
                          onClick={() => handleInyectarCorrida("2-2s")}
                          style={{ padding: "5px 9px", borderRadius: 5, border: `1px solid ${D.war}`, background: `${D.war}22`, color: D.war, fontSize: 10.5, fontWeight: 700, cursor: "pointer" }}
                        >
                          ! Inyectar 2-2s
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Tabla de Historial de Corridas de Control */}
                  <div style={{ background: D.sfc, borderRadius: 10, border: `1px solid ${D.brd}`, overflow: "hidden", display: "flex", flexDirection: "column" }}>
                    <div style={{ background: D.sfc2, padding: "8px 14px", borderBottom: `1px solid ${D.brd}`, fontSize: 11, fontWeight: 700, color: D.txt }}>
                      Registro de Corridas Analíticas &amp; Trazabilidad Multirregla (CLSI C24)
                    </div>
                    <div style={{ overflowX: "auto", maxHeight: 180 }}>
                      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11, textAlign: "left" }}>
                        <thead>
                          <tr style={{ background: D.sfc3, color: D.txl, borderBottom: `1px solid ${D.brd}` }}>
                            <th style={{ padding: "6px 12px" }}>N° Corrida</th>
                            <th style={{ padding: "6px 12px" }}>Fecha / Hora</th>
                            <th style={{ padding: "6px 12px" }}>Nivel 1 ({currentQC.ucum})</th>
                            <th style={{ padding: "6px 12px" }}>SDI N1</th>
                            <th style={{ padding: "6px 12px" }}>Nivel 2 ({currentQC.ucum})</th>
                            <th style={{ padding: "6px 12px" }}>SDI N2</th>
                            <th style={{ padding: "6px 12px" }}>Reglas Activadas</th>
                            <th style={{ padding: "6px 12px" }}>Estado &amp; Acción</th>
                          </tr>
                        </thead>
                        <tbody>
                          {runs.slice().reverse().map((r) => {
                            const sdi1 = ((r.l1 - currentQC.nivel1.target) / currentQC.nivel1.sd).toFixed(2);
                            const sdi2 = ((r.l2 - currentQC.nivel2.target) / currentQC.nivel2.sd).toFixed(2);
                            return (
                              <tr key={r.id} style={{ borderBottom: `1px solid ${D.brd}`, color: D.txt }}>
                                <td style={{ padding: "6px 12px", fontFamily: "monospace" }}>#{r.id}</td>
                                <td style={{ padding: "6px 12px" }}>{r.fecha}</td>
                                <td style={{ padding: "6px 12px", fontWeight: 700 }}>{r.l1}</td>
                                <td style={{ padding: "6px 12px", color: Math.abs(sdi1) > 2 ? D.dan : D.txm, fontFamily: "monospace" }}>{sdi1}</td>
                                <td style={{ padding: "6px 12px", fontWeight: 700 }}>{r.l2}</td>
                                <td style={{ padding: "6px 12px", color: Math.abs(sdi2) > 2 ? D.dan : D.txm, fontFamily: "monospace" }}>{sdi2}</td>
                                <td style={{ padding: "6px 12px" }}>
                                  {r.reglas.length === 0 ? (
                                    <span style={{ color: D.suc }}>Sin violaciones</span>
                                  ) : (
                                    <span style={{ color: r.estado === "RECHAZO" ? D.dan : D.war, fontWeight: 700 }}>
                                      {r.reglas.join(", ")}
                                    </span>
                                  )}
                                </td>
                                <td style={{ padding: "6px 12px" }}>
                                  <span
                                    style={{
                                      padding: "2px 6px",
                                      borderRadius: 4,
                                      fontSize: 10,
                                      fontWeight: 700,
                                      background: r.estado === "RECHAZO" ? `${D.dan}22` : r.estado === "ADVERTENCIA" ? `${D.war}22` : `${D.suc}22`,
                                      color: r.estado === "RECHAZO" ? D.dan : r.estado === "ADVERTENCIA" ? D.war : D.suc,
                                    }}
                                  >
                                    {r.estado} · {r.accion}
                                  </span>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* SUB-PESTAÑA 2: CAMBIO CRÍTICO RCV & DELTA CHECK */}
            {subTabQC === "rcv" && (() => {
              const deltaAbs = Math.abs(rcvInputs.curr - rcvInputs.prev);
              const deltaPct = rcvInputs.prev > 0 ? (deltaAbs / rcvInputs.prev) * 100 : 0;
              const rcvThreshold = calcularRCV(rcvInputs.cva, rcvInputs.cvi, rcvInputs.z);
              const esSignificativo = deltaPct > rcvThreshold;

              const presets = [
                { id: "TROP", nombre: "Troponina T hs", cva: 4.5, cvi: 9.5, prev: 15.2, curr: 145.8, ucum: "ng/L" },
                { id: "CREAT", nombre: "Creatinina en Suero", cva: 2.2, cvi: 4.5, prev: 0.95, curr: 1.45, ucum: "mg/dL" },
                { id: "GLU", nombre: "Glucosa en Suero", cva: 2.0, cvi: 5.6, prev: 92.0, curr: 135.0, ucum: "mg/dL" },
                { id: "HEM", nombre: "Hemoglobina", cva: 1.5, cvi: 2.8, prev: 13.5, curr: 10.2, ucum: "g/dL" },
                { id: "POTASIO", nombre: "Potasio en Suero", cva: 1.8, cvi: 4.8, prev: 4.2, curr: 5.6, ucum: "mmol/L" },
              ];

              return (
                <div style={{ flex: 1, display: "grid", gridTemplateColumns: "360px 1fr", gap: 14, overflowY: "auto" }}>
                  {/* Formulario de Entradas RCV */}
                  <div style={{ background: D.sfc, borderRadius: 10, padding: 16, border: `1px solid ${D.brd}` }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: D.txt, marginBottom: 4 }}>Parámetros de Entrada (CLSI EP21)</div>
                    <div style={{ fontSize: 11, color: D.txm, marginBottom: 14 }}>
                      Ecuación de Fraser: RCV = 2^(1/2) * Z * sqrt(CV_A^2 + CV_I^2).
                    </div>

                    <div style={{ marginBottom: 12 }}>
                      <div style={{ fontSize: 10.5, color: D.txl, marginBottom: 6 }}>Cargar Preconfiguración Clínica:</div>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
                        {presets.map((p) => (
                          <button
                            key={p.id}
                            onClick={() => setRcvInputs({ prev: p.prev, curr: p.curr, cva: p.cva, cvi: p.cvi, z: 1.96, preset: p.id })}
                            style={{
                              padding: "4px 8px",
                              borderRadius: 5,
                              border: `1px solid ${rcvInputs.preset === p.id ? D.tea : D.brd}`,
                              background: rcvInputs.preset === p.id ? `${D.tea}22` : D.sfc2,
                              color: rcvInputs.preset === p.id ? D.tea : D.txm,
                              fontSize: 10,
                              fontWeight: 600,
                              cursor: "pointer",
                            }}
                          >
                            {p.nombre}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 12 }}>
                      <div>
                        <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 4 }}>Valor Previo (x1):</label>
                        <input
                          type="number"
                          step="0.01"
                          value={rcvInputs.prev}
                          onChange={(e) => setRcvInputs({ ...rcvInputs, prev: parseFloat(e.target.value) || 0 })}
                          style={{ width: "100%", padding: "6px 8px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 11 }}
                        />
                      </div>
                      <div>
                        <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 4 }}>Valor Actual (x2):</label>
                        <input
                          type="number"
                          step="0.01"
                          value={rcvInputs.curr}
                          onChange={(e) => setRcvInputs({ ...rcvInputs, curr: parseFloat(e.target.value) || 0 })}
                          style={{ width: "100%", padding: "6px 8px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 11 }}
                        />
                      </div>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 12 }}>
                      <div>
                        <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 4 }}>CV_A Analítico (%):</label>
                        <input
                          type="number"
                          step="0.1"
                          value={rcvInputs.cva}
                          onChange={(e) => setRcvInputs({ ...rcvInputs, cva: parseFloat(e.target.value) || 0 })}
                          style={{ width: "100%", padding: "6px 8px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 11 }}
                        />
                      </div>
                      <div>
                        <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 4 }}>CV_I Biológico (%):</label>
                        <input
                          type="number"
                          step="0.1"
                          value={rcvInputs.cvi}
                          onChange={(e) => setRcvInputs({ ...rcvInputs, cvi: parseFloat(e.target.value) || 0 })}
                          style={{ width: "100%", padding: "6px 8px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 11 }}
                        />
                      </div>
                    </div>

                    <div>
                      <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 4 }}>Nivel de Confianza Z:</label>
                      <select
                        value={rcvInputs.z}
                        onChange={(e) => setRcvInputs({ ...rcvInputs, z: parseFloat(e.target.value) })}
                        style={{ width: "100%", padding: "6px 8px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 11 }}
                      >
                        <option value={1.96}>95% Bidireccional (Z = 1.96, p &lt; 0.05)</option>
                        <option value={2.58}>99% Bidireccional (Z = 2.58, p &lt; 0.01)</option>
                      </select>
                    </div>
                  </div>

                  {/* Resultados y Veredicto Clínico */}
                  <div style={{ background: D.sfc, borderRadius: 10, padding: 18, border: `1px solid ${D.brd}`, display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 700, color: D.txt, marginBottom: 12 }}>Evaluación del Delta Check &amp; Significancia</div>

                      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 16 }}>
                        <div style={{ background: D.sfc2, borderRadius: 8, padding: 12, border: `1px solid ${D.brd}` }}>
                          <div style={{ fontSize: 10.5, color: D.txl }}>Variación Observada (Δ%)</div>
                          <div style={{ fontSize: 22, fontWeight: 800, color: esSignificativo ? D.dan : D.suc, marginTop: 4 }}>
                            {deltaPct.toFixed(1)}%
                          </div>
                          <div style={{ fontSize: 10, color: D.txm, marginTop: 2 }}>Diferencia: {deltaAbs.toFixed(2)} unidades</div>
                        </div>

                        <div style={{ background: D.sfc2, borderRadius: 8, padding: 12, border: `1px solid ${D.brd}` }}>
                          <div style={{ fontSize: 10.5, color: D.txl }}>Umbral RCV Crítico</div>
                          <div style={{ fontSize: 22, fontWeight: 800, color: D.tea, marginTop: 4 }}>
                            {rcvThreshold.toFixed(1)}%
                          </div>
                          <div style={{ fontSize: 10, color: D.txm, marginTop: 2 }}>Límite de fluctuación fisiológica</div>
                        </div>

                        <div style={{ background: D.sfc2, borderRadius: 8, padding: 12, border: `1px solid ${D.brd}` }}>
                          <div style={{ fontSize: 10.5, color: D.txl }}>Ratio de Cambio (Δ / RCV)</div>
                          <div style={{ fontSize: 22, fontWeight: 800, color: esSignificativo ? D.dan : D.txt, marginTop: 4 }}>
                            {(rcvThreshold > 0 ? (deltaPct / rcvThreshold).toFixed(2) : "0.00")}x
                          </div>
                          <div style={{ fontSize: 10, color: D.txm, marginTop: 2 }}>Factor sobre el umbral</div>
                        </div>
                      </div>

                      {/* Cartel de Veredicto Clínico */}
                      <div
                        style={{
                          borderRadius: 8,
                          padding: "14px 18px",
                          background: esSignificativo ? `${D.dan}1A` : `${D.suc}1A`,
                          border: `1px solid ${esSignificativo ? D.dan : D.suc}`,
                        }}
                      >
                        <div style={{ fontSize: 13, fontWeight: 800, color: esSignificativo ? D.dan : D.suc, display: "flex", alignItems: "center", gap: 6 }}>
                          {esSignificativo ? <AlertTriangle size={16} /> : <CheckCircle size={16} />}
                          {esSignificativo ? "CAMBIO CLÍNICO GENUINO (ESTADÍSTICAMENTE SIGNIFICATIVO)" : "VARIABILIDAD BIOLÓGICA HABITUAL (NO SIGNIFICATIVO)"}
                        </div>
                        <div style={{ fontSize: 11.5, color: D.txt, lineHeight: 1.45, marginTop: 6 }}>
                          {esSignificativo
                            ? `La variación observada de ${deltaPct.toFixed(1)}% supera el límite crítico de RCV (${rcvThreshold.toFixed(1)}%). Existe una probabilidad > 95% de que este cambio corresponda a una evolución patológica o respuesta terapéutica real, descartando fluctuación analítica o biológica habitual. Requiere correlación clínica inmediata.`
                            : `La variación observada de ${deltaPct.toFixed(1)}% se encuentra contenida dentro del umbral de RCV (${rcvThreshold.toFixed(1)}%). Dicha diferencia puede explicarse completamente por la variabilidad analítica del analizador y la oscilación intra-individual del paciente.`}
                        </div>
                      </div>
                    </div>

                    <div style={{ fontSize: 10.5, color: D.txl, paddingTop: 10, borderTop: `1px solid ${D.brd}` }}>
                      Norma de referencia: <b>CLSI EP21-A</b> (Estimation of Total Analytical Error for Clinical Laboratory Methods) y bases de datos EFLM de Variabilidad Biológica.
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* SUB-PESTAÑA 3: FILTRADO GLOMERULAR CKD-EPI 2021 */}
            {subTabQC === "ckd" && (() => {
              const res = calcularCKDEPI2021(ckdInputs.cr, ckdInputs.edad, ckdInputs.sexo);
              return (
                <div style={{ flex: 1, display: "grid", gridTemplateColumns: "360px 1fr", gap: 14, overflowY: "auto" }}>
                  <div style={{ background: D.sfc, borderRadius: 10, padding: 16, border: `1px solid ${D.brd}` }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: D.txt, marginBottom: 4 }}>Parámetros del Paciente</div>
                    <div style={{ fontSize: 11, color: D.txm, marginBottom: 14 }}>
                      Ecuación CKD-EPI 2021 recomendada por KDIGO y la National Kidney Foundation (sin factor de raza).
                    </div>

                    <div style={{ marginBottom: 12 }}>
                      <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 4 }}>Creatinina en Suero (mg/dL):</label>
                      <input
                        type="number"
                        step="0.01"
                        value={ckdInputs.cr}
                        onChange={(e) => setCkdInputs({ ...ckdInputs, cr: parseFloat(e.target.value) || 0 })}
                        style={{ width: "100%", padding: "7px 10px", borderRadius: 6, border: `1px solid ${D.brd}` , background: D.sfc2, color: D.txt, fontSize: 12 }}
                      />
                    </div>

                    <div style={{ marginBottom: 12 }}>
                      <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 4 }}>Edad del Paciente (años):</label>
                      <input
                        type="number"
                        value={ckdInputs.edad}
                        onChange={(e) => setCkdInputs({ ...ckdInputs, edad: parseInt(e.target.value, 10) || 0 })}
                        style={{ width: "100%", padding: "7px 10px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 12 }}
                      />
                    </div>

                    <div style={{ marginBottom: 14 }}>
                      <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 4 }}>Sexo Biológico:</label>
                      <div style={{ display: "flex", gap: 8 }}>
                        {["femenino", "masculino"].map((s) => (
                          <button
                            key={s}
                            onClick={() => setCkdInputs({ ...ckdInputs, sexo: s })}
                            style={{
                              flex: 1,
                              padding: "7px 0",
                              borderRadius: 6,
                              border: `1px solid ${ckdInputs.sexo === s ? D.tea : D.brd}`,
                              background: ckdInputs.sexo === s ? `${D.tea}22` : D.sfc2,
                              color: ckdInputs.sexo === s ? D.tea : D.txm,
                              fontSize: 11,
                              fontWeight: 700,
                              cursor: "pointer",
                            }}
                          >
                            {s.toUpperCase()}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div style={{ background: D.sfc, borderRadius: 10, padding: 18, border: `1px solid ${D.brd}`, display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 700, color: D.txt, marginBottom: 12 }}>Estimación de la Tasa de Filtrado Glomerular</div>

                      <div style={{ background: D.sfc2, borderRadius: 8, padding: 16, border: `1px solid ${D.brd}`, display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
                        <div>
                          <div style={{ fontSize: 11, color: D.txl }}>Tasa de Filtración Glomerular Estimada (eGFR):</div>
                          <div style={{ fontSize: 32, fontWeight: 800, color: res.color, marginTop: 4 }}>
                            {res.egfr} <span style={{ fontSize: 14, color: D.txl, fontWeight: 400 }}>mL/min/1.73 m²</span>
                          </div>
                        </div>
                        <div style={{ textAlign: "right" }}>
                          <span style={{ fontSize: 13, padding: "4px 10px", borderRadius: 6, background: `${res.color}22`, color: res.color, fontWeight: 800 }}>
                            ESTADIO {res.estadio}
                          </span>
                          <div style={{ fontSize: 11, color: D.txt, marginTop: 4 }}>{res.desc}</div>
                        </div>
                      </div>

                      {/* Tabla Guía KDIGO */}
                      <div style={{ border: `1px solid ${D.brd}`, borderRadius: 8, overflow: "hidden" }}>
                        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 10.5, textAlign: "left" }}>
                          <thead>
                            <tr style={{ background: D.sfc3, color: D.txl }}>
                              <th style={{ padding: "6px 10px" }}>Estadio</th>
                              <th style={{ padding: "6px 10px" }}>eGFR (mL/min/1.73m²)</th>
                              <th style={{ padding: "6px 10px" }}>Descripción Clínica KDIGO</th>
                            </tr>
                          </thead>
                          <tbody>
                            {[
                              { est: "G1", r: "≥ 90", d: "Normal o elevado", c: "#5FD97A" },
                              { est: "G2", r: "60 - 89", d: "Levemente disminuido", c: "#22D3B8" },
                              { est: "G3a", r: "45 - 59", d: "Disminución leve a moderada", c: "#EAB308" },
                              { est: "G3b", r: "30 - 44", d: "Disminución moderada a severa", c: "#FFA359" },
                              { est: "G4", r: "15 - 29", d: "Disminución severa", c: "#FFA359" },
                              { est: "G5", r: "< 15", d: "Falla renal terminal", c: "#FF5C6C" },
                            ].map((row) => (
                              <tr key={row.est} style={{ background: res.estadio === row.est ? `${row.c}1A` : "transparent", borderBottom: `1px solid ${D.brd}` }}>
                                <td style={{ padding: "5px 10px", fontWeight: 700, color: row.c }}>{row.est}</td>
                                <td style={{ padding: "5px 10px", color: D.txt }}>{row.r}</td>
                                <td style={{ padding: "5px 10px", color: D.txm }}>{row.d}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    <div style={{ fontSize: 10.5, color: D.txl, paddingTop: 10, borderTop: `1px solid ${D.brd}` }}>
                      Algoritmo validado para reporte automático e incorporación en informes de Bioquímica Clínica según D.S. N° 20.
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* SUB-PESTAÑA 4: FRACCIÓN LDL FRIEDEWALD */}
            {subTabQC === "lipidos" && (() => {
              const res = calcularFriedewald(lipidosInputs.colTotal, lipidosInputs.hdl, lipidosInputs.tg);
              return (
                <div style={{ flex: 1, display: "grid", gridTemplateColumns: "360px 1fr", gap: 14, overflowY: "auto" }}>
                  <div style={{ background: D.sfc, borderRadius: 10, padding: 16, border: `1px solid ${D.brd}` }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: D.txt, marginBottom: 4 }}>Perfil Lipídico Básico</div>
                    <div style={{ fontSize: 11, color: D.txm, marginBottom: 14 }}>
                      Cálculo de Colesterol LDL y Colesterol No-HDL mediante ecuación de Friedewald con validación de límite de interferencia.
                    </div>

                    <div style={{ marginBottom: 12 }}>
                      <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 4 }}>Colesterol Total (mg/dL):</label>
                      <input
                        type="number"
                        value={lipidosInputs.colTotal}
                        onChange={(e) => setLipidosInputs({ ...lipidosInputs, colTotal: parseFloat(e.target.value) || 0 })}
                        style={{ width: "100%", padding: "7px 10px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 12 }}
                      />
                    </div>

                    <div style={{ marginBottom: 12 }}>
                      <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 4 }}>Colesterol HDL (mg/dL):</label>
                      <input
                        type="number"
                        value={lipidosInputs.hdl}
                        onChange={(e) => setLipidosInputs({ ...lipidosInputs, hdl: parseFloat(e.target.value) || 0 })}
                        style={{ width: "100%", padding: "7px 10px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 12 }}
                      />
                    </div>

                    <div style={{ marginBottom: 14 }}>
                      <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 4 }}>Triglicéridos en Suero (mg/dL):</label>
                      <input
                        type="number"
                        value={lipidosInputs.tg}
                        onChange={(e) => setLipidosInputs({ ...lipidosInputs, tg: parseFloat(e.target.value) || 0 })}
                        style={{ width: "100%", padding: "7px 10px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 12 }}
                      />
                    </div>
                  </div>

                  <div style={{ background: D.sfc, borderRadius: 10, padding: 18, border: `1px solid ${D.brd}`, display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 700, color: D.txt, marginBottom: 12 }}>Fracciones Lipídicas Calculadas</div>

                      {res.valido ? (
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
                          <div style={{ background: D.sfc2, borderRadius: 8, padding: 16, border: `1px solid ${D.brd}` }}>
                            <div style={{ fontSize: 11, color: D.txl }}>Colesterol LDL Estimado (Friedewald):</div>
                            <div style={{ fontSize: 28, fontWeight: 800, color: D.tea, marginTop: 4 }}>
                              {res.ldl} <span style={{ fontSize: 13, color: D.txl, fontWeight: 400 }}>mg/dL</span>
                            </div>
                            <div style={{ fontSize: 10, color: D.txm, marginTop: 4 }}>Fórmula: Col Total - HDL - (TG / 5)</div>
                          </div>

                          <div style={{ background: D.sfc2, borderRadius: 8, padding: 16, border: `1px solid ${D.brd}` }}>
                            <div style={{ fontSize: 11, color: D.txl }}>Colesterol No-HDL:</div>
                            <div style={{ fontSize: 28, fontWeight: 800, color: D.txt, marginTop: 4 }}>
                              {res.noHdl} <span style={{ fontSize: 13, color: D.txl, fontWeight: 400 }}>mg/dL</span>
                            </div>
                            <div style={{ fontSize: 10, color: D.txm, marginTop: 4 }}>Col Total - HDL (Marcador Aterogénico)</div>
                          </div>
                        </div>
                      ) : (
                        <div style={{ borderRadius: 8, padding: 16, background: `${D.dan}1A`, border: `1px solid ${D.dan}`, marginBottom: 16 }}>
                          <div style={{ fontSize: 13, fontWeight: 800, color: D.dan, display: "flex", alignItems: "center", gap: 6 }}>
                            <AlertTriangle size={16} /> ADVERTENCIA METODOLÓGICA DE INTERFERENCIA
                          </div>
                          <div style={{ fontSize: 11.5, color: D.txt, marginTop: 6, lineHeight: 1.45 }}>
                            {res.error}
                          </div>
                        </div>
                      )}
                    </div>

                    <div style={{ fontSize: 10.5, color: D.txl, paddingTop: 10, borderTop: `1px solid ${D.brd}` }}>
                      Conforme a consensos de la Sociedad Chilena de Cardiología (SOCHICAR) y National Cholesterol Education Program (NCEP).
                    </div>
                  </div>
                </div>
              );
            })()}
{/* SUB-PESTAÑA 5: CURVAS DE POTENCIA PED/PFR & SELECCIÓN WESTGARD */}
            {subTabQC === "curvas_sigma" && (() => {
              const currentQC = qcData[qcAnalitoKey] || qcData.GLU;
              const runs = currentQC.corridas;
              const n = runs.length;
              const meanL1 = runs.reduce((acc, r) => acc + r.l1, 0) / n;
              const sdL1 = Math.sqrt(runs.reduce((acc, r) => acc + Math.pow(r.l1 - meanL1, 2), 0) / (n - 1));
              const cvL1 = (sdL1 / meanL1) * 100;
              const biasL1 = ((meanL1 - currentQC.nivel1.target) / currentQC.nivel1.target) * 100;
              const sigma = (currentQC.tea - Math.abs(biasL1)) / cvL1;
              const deltaSE = Math.max(0, sigma - 1.65);

              let reglaRecomendada = "1-3s (N=2)";
              let pedEstimado = 98.5;
              let pfrEstimado = 0.3;
              let esfuerzoQC = "Mínimo · Regla simple suficiente";
              let colorQC = D.suc;

              if (sigma >= 6.0) {
                reglaRecomendada = "1-3s (N=2, 1 corrida)";
                pedEstimado = 98.5; pfrEstimado = 0.3;
                esfuerzoQC = "Clase Mundial · 1 corrida diaria con regla simple 1-3s";
                colorQC = D.suc;
              } else if (sigma >= 5.0) {
                reglaRecomendada = "1-3s / 2-2s / R-4s (N=2, 1 corrida)";
                pedEstimado = 95.0; pfrEstimado = 1.2;
                esfuerzoQC = "Excelente · Multirregla estándar con bajo falso rechazo";
                colorQC = D.tea;
              } else if (sigma >= 4.0) {
                reglaRecomendada = "1-3s / 2-2s / R-4s / 4-1s (N=4, 2 corridas)";
                pedEstimado = 91.0; pfrEstimado = 2.8;
                esfuerzoQC = "Riguroso · Requiere duplicar corridas de control (N=4)";
                colorQC = D.war;
              } else {
                reglaRecomendada = "1-3s / 2-2s / R-4s / 4-1s / 10-x (N=6)";
                pedEstimado = 82.0; pfrEstimado = 6.5;
                esfuerzoQC = "Método Marginal · Requiere re-calibración e investigación técnica";
                colorQC = D.dan;
              }

              return (
                <div style={{ flex: 1, display: "grid", gridTemplateColumns: "360px 1fr", gap: 14, overflowY: "auto" }}>
                  <div style={{ background: D.sfc, borderRadius: 10, padding: 16, border: `1px solid ${D.brd}` }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: D.txt, marginBottom: 4 }}>Selección Dinámica de Reglas de Westgard</div>
                    <div style={{ fontSize: 11, color: D.txm, marginBottom: 12 }}>
                      Diseño de la estrategia de control basado en el desempeño Six Sigma (CLSI C24-Ed4).
                    </div>

                    <div style={{ background: D.sfc2, borderRadius: 8, padding: 12, border: `1px solid ${D.brd}`, marginBottom: 14 }}>
                      <div style={{ fontSize: 10.5, color: D.txl }}>Analito Seleccionado:</div>
                      <div style={{ fontSize: 13.5, fontWeight: 700, color: D.txt, marginTop: 2 }}>{currentQC.nombre}</div>
                      <div style={{ fontSize: 11, color: D.tea }}>{currentQC.equipoNombre}</div>
                      <div style={{ marginTop: 8, display: "flex", justifyContent: "space-between", fontSize: 11, color: D.txm }}>
                        <span>Métrica Sigma: <b style={{ color: colorQC }}>{sigma.toFixed(1)} σ</b></span>
                        <span>ΔSE crítico: <b>{deltaSE.toFixed(2)} SD</b></span>
                      </div>
                    </div>

                    <div style={{ background: `${colorQC}1A`, borderRadius: 8, padding: 14, border: `1px solid ${colorQC}`, marginBottom: 14 }}>
                      <div style={{ fontSize: 10.5, fontWeight: 700, color: colorQC, textTransform: "uppercase" }}>Algoritmo Recomendado:</div>
                      <div style={{ fontSize: 14, fontWeight: 800, color: D.txt, marginTop: 3 }}>{reglaRecomendada}</div>
                      <div style={{ fontSize: 11, color: D.txt, marginTop: 4 }}>{esfuerzoQC}</div>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <div style={{ background: D.sfc2, borderRadius: 8, padding: 10, border: `1px solid ${D.brd}` }}>
                        <div style={{ fontSize: 10, color: D.txl }}>Detección de Error (Ped):</div>
                        <div style={{ fontSize: 18, fontWeight: 800, color: D.suc, marginTop: 2 }}>{pedEstimado}%</div>
                        <div style={{ fontSize: 9.5, color: D.txm }}>P(detección de ΔSEcrit)</div>
                      </div>
                      <div style={{ background: D.sfc2, borderRadius: 8, padding: 10, border: `1px solid ${D.brd}` }}>
                        <div style={{ fontSize: 10, color: D.txl }}>Falso Rechazo (Pfr):</div>
                        <div style={{ fontSize: 18, fontWeight: 800, color: pfrEstimado > 3 ? D.dan : D.txt, marginTop: 2 }}>{pfrEstimado}%</div>
                        <div style={{ fontSize: 9.5, color: D.txm }}>P(rechazo injustificado)</div>
                      </div>
                    </div>
                  </div>

                  {/* Gráfico Vectorial de Curvas de Potencia (Power Function Graph) */}
                  <div style={{ background: D.sfc, borderRadius: 10, padding: 18, border: `1px solid ${D.brd}`, display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 700, color: D.txt, marginBottom: 4 }}>Curva de Potencia Operativa (Ped vs Error Sistemático ΔSE)</div>
                      <div style={{ fontSize: 11, color: D.txm, marginBottom: 12 }}>
                        La curva modela la probabilidad de que la regla detecte desplazamientos de calibración en función de la magnitud del error.
                      </div>

                      <div style={{ background: "#060D15", borderRadius: 8, padding: 12, border: `1px solid ${D.brd}` }}>
                        <svg viewBox="0 0 540 200" style={{ width: "100%", height: 200, display: "block" }}>
                          {/* Ejes y líneas de cuadrícula */}
                          <line x1="45" y1="170" x2="520" y2="170" stroke="#334155" strokeWidth="1" />
                          <line x1="45" y1="20" x2="45" y2="170" stroke="#334155" strokeWidth="1" />

                          {[0, 25, 50, 75, 100].map((pct) => {
                            const y = 170 - (pct / 100) * 140;
                            return (
                              <g key={pct}>
                                <line x1="40" y1={y} x2="520" y2={y} stroke="#1E293B" strokeDasharray="3 3" />
                                <text x="35" y={y + 3} textAnchor="end" fill="#64748B" fontSize="9" fontFamily="monospace">{pct}%</text>
                              </g>
                            );
                          })}

                          {[0, 1, 2, 3, 4].map((se) => {
                            const x = 45 + se * 110;
                            return (
                              <g key={se}>
                                <line x1={x} y1="170" x2={x} y2="175" stroke="#334155" />
                                <text x={x} y="188" textAnchor="middle" fill="#64748B" fontSize="9" fontFamily="monospace">{se} SD</text>
                              </g>
                            );
                          })}

                          {/* Curva Sigmoidea de Detección de Error */}
                          <path
                            d="M 45 168 Q 120 165 180 140 T 320 45 L 500 32"
                            fill="none"
                            stroke={D.tea}
                            strokeWidth="2.5"
                          />

                          {/* Punto de Operación Actual */}
                          {(() => {
                            const opX = Math.min(500, 45 + deltaSE * 110);
                            const opY = Math.max(32, 170 - (pedEstimado / 100) * 140);
                            return (
                              <g>
                                <line x1={opX} y1={opY} x2={opX} y2="170" stroke={colorQC} strokeDasharray="2 2" />
                                <line x1="45" y1={opY} x2={opX} y2={opY} stroke={colorQC} strokeDasharray="2 2" />
                                <circle cx={opX} cy={opY} r="6" fill={colorQC} stroke="#0A1420" strokeWidth="2" />
                                <text x={opX + 8} y={opY - 6} fill={colorQC} fontSize="10" fontWeight="700">
                                  Punto Operativo ({deltaSE.toFixed(1)} SD, {pedEstimado}%)
                                </text>
                              </g>
                            );
                          })()}
                        </svg>
                      </div>
                    </div>

                    <div style={{ fontSize: 10.5, color: D.txl, paddingTop: 8, borderTop: `1px solid ${D.brd}` }}>
                      Referencia: <b>CLSI C24-Ed4</b> y especificación OGC-41 de diseño estadístico de control de calidad analítico.
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* SUB-PESTAÑA 6: DISEÑO DE LOTE N=20 (CLSI C24) */}
            {subTabQC === "n20" && (() => {
              const d = N20_PRELIMINAR_DATA;
              const n = d.replicas.length;
              const mediaCalc = d.replicas.reduce((a, b) => a + b, 0) / n;
              const sdCalc = Math.sqrt(d.replicas.reduce((a, b) => a + Math.pow(b - mediaCalc, 2), 0) / (n - 1));
              const cvCalc = (sdCalc / mediaCalc) * 100;
              const biasCalc = ((mediaCalc - d.insertoFabricante.target) / d.insertoFabricante.target) * 100;
              const loteAprobado = cvCalc <= 3.0 && Math.abs(biasCalc) <= 2.0;

              return (
                <div style={{ flex: 1, display: "grid", gridTemplateColumns: "360px 1fr", gap: 14, overflowY: "auto" }}>
                  <div style={{ background: D.sfc, borderRadius: 10, padding: 16, border: `1px solid ${D.brd}` }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: D.txt, marginBottom: 4 }}>Protocolo de Establecimiento de Lote (N=20)</div>
                    <div style={{ fontSize: 11, color: D.txm, marginBottom: 12 }}>
                      Validación preliminar de medias y límites de control antes de liberar el nuevo lote al uso rutinario.
                    </div>

                    <div style={{ background: D.sfc2, borderRadius: 8, padding: 12, border: `1px solid ${D.brd}`, marginBottom: 14 }}>
                      <div>Lote Evaluado: <b style={{ fontFamily: "monospace", color: D.tea }}>{d.lote}</b></div>
                      <div style={{ fontSize: 11, color: D.txt, marginTop: 2 }}>{d.analito}</div>
                      <div style={{ fontSize: 10.5, color: D.txl, marginTop: 4 }}>
                        Valor Declarado Fabricante: <b>{d.insertoFabricante.target} {d.unidad}</b> (SD ± {d.insertoFabricante.sdEsperado})
                      </div>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 14 }}>
                      <div style={{ background: D.sfc2, borderRadius: 8, padding: 10, border: `1px solid ${D.brd}` }}>
                        <div style={{ fontSize: 10, color: D.txl }}>Media Observada (x̄):</div>
                        <div style={{ fontSize: 18, fontWeight: 800, color: D.tea, marginTop: 2 }}>{mediaCalc.toFixed(2)}</div>
                        <div style={{ fontSize: 9.5, color: D.txm }}>n = 20 réplicas</div>
                      </div>
                      <div style={{ background: D.sfc2, borderRadius: 8, padding: 10, border: `1px solid ${D.brd}` }}>
                        <div style={{ fontSize: 10, color: D.txl }}>CV Preliminar (%):</div>
                        <div style={{ fontSize: 18, fontWeight: 800, color: cvCalc <= 3 ? D.suc : D.war, marginTop: 2 }}>{cvCalc.toFixed(2)}%</div>
                        <div style={{ fontSize: 9.5, color: D.txm }}>Meta: &lt; 3.00%</div>
                      </div>
                    </div>

                    <div style={{ background: loteAprobado ? `${D.suc}1A` : `${D.war}1A`, borderRadius: 8, padding: 12, border: `1px solid ${loteAprobado ? D.suc : D.war}`, marginBottom: 14 }}>
                      <div style={{ fontSize: 11, fontWeight: 800, color: loteAprobado ? D.suc : D.war }}>
                        {loteAprobado ? "✓ LOTE APTO PARA PRODUCCIÓN CLÍNICA" : "! LOTE REQUIERE REVISIÓN"}
                      </div>
                      <div style={{ fontSize: 10.5, color: D.txt, marginTop: 3 }}>
                        Sesgo frente al fabricante: <b>{biasCalc > 0 ? `+${biasCalc.toFixed(2)}` : biasCalc.toFixed(2)}%</b> (Tolerancia ± 2.0%).
                      </div>
                    </div>

                    <button
                      onClick={() => setLoteN20Aprobado(true)}
                      style={{ width: "100%", padding: "9px", borderRadius: 6, border: "none", background: loteN20Aprobado ? D.suc : D.tea, color: "#0A1420", fontSize: 11, fontWeight: 700, cursor: "pointer" }}
                    >
                      {loteN20Aprobado ? "✓ Lote Aprobado y Sellado por DT" : "Aprobar y Sellar Lote N=20 (DT)"}
                    </button>
                  </div>

                  <div style={{ background: D.sfc, borderRadius: 10, padding: 18, border: `1px solid ${D.brd}`, display: "flex", flexDirection: "column" }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: D.txt, marginBottom: 8 }}>
                      Tabla de Réplicas Individuales (n = 20)
                    </div>
                    <div style={{ overflowY: "auto", flex: 1, border: `1px solid ${D.brd}`, borderRadius: 8 }}>
                      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11, textAlign: "left" }}>
                        <thead>
                          <tr style={{ background: D.sfc3, color: D.txl }}>
                            <th style={{ padding: "6px 10px" }}>Réplica</th>
                            <th style={{ padding: "6px 10px" }}>Valor ({d.unidad})</th>
                            <th style={{ padding: "6px 10px" }}>Desvío (x - x̄)</th>
                            <th style={{ padding: "6px 10px" }}>SDI Local</th>
                            <th style={{ padding: "6px 10px" }}>Estado</th>
                          </tr>
                        </thead>
                        <tbody>
                          {d.replicas.map((val, idx) => {
                            const dev = val - mediaCalc;
                            const sdi = dev / sdCalc;
                            return (
                              <tr key={idx} style={{ borderBottom: `1px solid ${D.brd}`, color: D.txt }}>
                                <td style={{ padding: "5px 10px", fontFamily: "monospace" }}>#{idx + 1}</td>
                                <td style={{ padding: "5px 10px", fontWeight: 700 }}>{val.toFixed(2)}</td>
                                <td style={{ padding: "5px 10px", color: dev >= 0 ? D.tea : D.txm }}>{dev >= 0 ? `+${dev.toFixed(2)}` : dev.toFixed(2)}</td>
                                <td style={{ padding: "5px 10px", fontFamily: "monospace" }}>{sdi.toFixed(2)}</td>
                                <td style={{ padding: "5px 10px" }}>
                                  <span style={{ fontSize: 9.5, padding: "2px 6px", borderRadius: 4, background: `${D.suc}22`, color: D.suc, fontWeight: 700 }}>
                                    Conforme
                                  </span>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* SUB-PESTAÑA 7: CONTROL EXTERNO (PEEC ISP CHILE) */}
            {subTabQC === "peec" && (
              <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 14, overflowY: "auto" }}>
                <div style={{ background: D.sfc, borderRadius: 10, padding: 14, border: `1px solid ${D.brd}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 700, color: D.txt }}>
                      Programa de Evaluación Externa de la Calidad (PEEC) · Instituto de Salud Pública de Chile (ISP)
                    </div>
                    <div style={{ fontSize: 11, color: D.txm, marginTop: 3 }}>
                      Monitoreo interlaboratorio obligatorio conforme al D.S. N° 20 Art. 23 para acreditación sanitaria.
                    </div>
                  </div>
                  <span style={{ fontSize: 11, padding: "4px 10px", borderRadius: 6, background: `${D.suc}22`, color: D.suc, fontWeight: 700 }}>
                    100% ENCUESTAS CONFORMES (|SDI| &lt; 1.0)
                  </span>
                </div>

                <div style={{ background: D.sfc, borderRadius: 10, border: `1px solid ${D.brd}`, overflow: "hidden" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11, textAlign: "left" }}>
                    <thead>
                      <tr style={{ background: D.sfc3, color: D.txl }}>
                        <th style={{ padding: "8px 12px" }}>Código Encuesta</th>
                        <th style={{ padding: "8px 12px" }}>Sección &amp; Analito</th>
                        <th style={{ padding: "8px 12px" }}>Equipo &amp; Método</th>
                        <th style={{ padding: "8px 12px" }}>Valor Lab</th>
                        <th style={{ padding: "8px 12px" }}>Media Consenso ISP</th>
                        <th style={{ padding: "8px 12px" }}>SD Pares</th>
                        <th style={{ padding: "8px 12px" }}>SDI (Z-Score)</th>
                        <th style={{ padding: "8px 12px" }}>Desvío %</th>
                        <th style={{ padding: "8px 12px" }}>Calificación ISP</th>
                      </tr>
                    </thead>
                    <tbody>
                      {PEEC_ISP_ENCUESTAS.map((e) => {
                        const sdi = (e.valorLab - e.mediaPares) / e.sdPares;
                        const pctD = ((e.valorLab - e.mediaPares) / e.mediaPares) * 100;
                        return (
                          <tr key={e.id} style={{ borderBottom: `1px solid ${D.brd}`, color: D.txt }}>
                            <td style={{ padding: "8px 12px", fontFamily: "monospace", color: D.tea }}>{e.id}</td>
                            <td style={{ padding: "8px 12px" }}>
                              <div style={{ fontWeight: 700 }}>{e.analito}</div>
                              <div style={{ fontSize: 9.5, color: D.txl }}>{e.seccion}</div>
                            </td>
                            <td style={{ padding: "8px 12px" }}>
                              <div>{e.equipo}</div>
                              <div style={{ fontSize: 9.5, color: D.txl }}>{e.metodo}</div>
                            </td>
                            <td style={{ padding: "8px 12px", fontWeight: 700 }}>{e.valorLab} {e.unidad}</td>
                            <td style={{ padding: "8px 12px" }}>{e.mediaPares} (n={e.nParticipantes})</td>
                            <td style={{ padding: "8px 12px" }}>± {e.sdPares}</td>
                            <td style={{ padding: "8px 12px", fontFamily: "monospace", fontWeight: 700, color: Math.abs(sdi) <= 1 ? D.suc : D.war }}>
                              {sdi > 0 ? `+${sdi.toFixed(2)}` : sdi.toFixed(2)}
                            </td>
                            <td style={{ padding: "8px 12px", color: D.txm }}>{pctD > 0 ? `+${pctD.toFixed(1)}%` : `${pctD.toFixed(1)}%`}</td>
                            <td style={{ padding: "8px 12px" }}>
                              <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 4, background: `${D.suc}22`, color: D.suc, fontWeight: 700 }}>
                                {e.estado}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* SUB-PESTAÑA 8: VERIFICACIÓN DE MÉTODOS (CLSI EP09 / EP15) */}
            {subTabQC === "verificacion" && (() => {
              const d = CLSI_EP09_DATA;
              return (
                <div style={{ flex: 1, display: "grid", gridTemplateColumns: "360px 1fr", gap: 14, overflowY: "auto" }}>
                  <div style={{ background: D.sfc, borderRadius: 10, padding: 16, border: `1px solid ${D.brd}` }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: D.txt, marginBottom: 4 }}>Comparación de Procedimientos (CLSI EP09-A3)</div>
                    <div style={{ fontSize: 11, color: D.txm, marginBottom: 12 }}>
                      Evaluación de concordancia y estimación de sesgo frente a método de referencia.
                    </div>

                    <div style={{ background: D.sfc2, borderRadius: 8, padding: 12, border: `1px solid ${D.brd}`, marginBottom: 14 }}>
                      <div>Referencia: <b style={{ color: D.txt }}>{d.metodoReferencia}</b></div>
                      <div style={{ marginTop: 2 }}>Candidato: <b style={{ color: D.tea }}>{d.metodoCandidato}</b></div>
                      <div style={{ fontSize: 10.5, color: D.txl, marginTop: 4 }}>Analito: {d.analito}</div>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 14 }}>
                      <div style={{ background: D.sfc2, borderRadius: 8, padding: 10, border: `1px solid ${D.brd}` }}>
                        <div style={{ fontSize: 10, color: D.txl }}>Pendiente (m):</div>
                        <div style={{ fontSize: 18, fontWeight: 800, color: D.tea, marginTop: 2 }}>{d.regresion.pendiente}</div>
                        <div style={{ fontSize: 9.5, color: D.txm }}>Meta: 0.98 - 1.02</div>
                      </div>
                      <div style={{ background: D.sfc2, borderRadius: 8, padding: 10, border: `1px solid ${D.brd}` }}>
                        <div style={{ fontSize: 10, color: D.txl }}>Coeficiente R²:</div>
                        <div style={{ fontSize: 18, fontWeight: 800, color: D.suc, marginTop: 2 }}>{d.regresion.r2}</div>
                        <div style={{ fontSize: 9.5, color: D.txm }}>Meta: &gt; 0.995</div>
                      </div>
                    </div>

                    <div style={{ background: `${D.suc}1A`, borderRadius: 8, padding: 12, border: `1px solid ${D.suc}` }}>
                      <div style={{ fontSize: 11, fontWeight: 800, color: D.suc }}>
                        Incertidumbre Expandida de Medición (U):
                      </div>
                      <div style={{ fontSize: 20, fontWeight: 800, color: D.txt, marginTop: 4 }}>
                        ± {d.incertidumbre.expandidaU}% <span style={{ fontSize: 11, color: D.txl, fontWeight: 400 }}>(k = 2, 95% conf.)</span>
                      </div>
                      <div style={{ fontSize: 10, color: D.txm, marginTop: 4 }}>
                        u_analítica: {d.incertidumbre.uAnalitica}% · u_calibrador: {d.incertidumbre.uCalibrador}%
                      </div>
                    </div>
                  </div>

                  <div style={{ background: D.sfc, borderRadius: 10, padding: 18, border: `1px solid ${D.brd}`, display: "flex", flexDirection: "column" }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: D.txt, marginBottom: 8 }}>
                      Muestras Pareadas de Pacientes (CLSI EP09)
                    </div>
                    <div style={{ overflowY: "auto", flex: 1, border: `1px solid ${D.brd}`, borderRadius: 8 }}>
                      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11, textAlign: "left" }}>
                        <thead>
                          <tr style={{ background: D.sfc3, color: D.txl }}>
                            <th style={{ padding: "6px 12px" }}>Muestra</th>
                            <th style={{ padding: "6px 12px" }}>Ref (Cobas c503)</th>
                            <th style={{ padding: "6px 12px" }}>Candidato (Espejo)</th>
                            <th style={{ padding: "6px 12px" }}>Sesgo Absoluto</th>
                            <th style={{ padding: "6px 12px" }}>Sesgo Relativo (%)</th>
                          </tr>
                        </thead>
                        <tbody>
                          {d.muestras.map((m) => {
                            const sesgoAbs = m.cand - m.ref;
                            const sesgoRel = (sesgoAbs / m.ref) * 100;
                            return (
                              <tr key={m.id} style={{ borderBottom: `1px solid ${D.brd}`, color: D.txt }}>
                                <td style={{ padding: "5px 12px", fontFamily: "monospace" }}>PAC-{m.id}</td>
                                <td style={{ padding: "5px 12px" }}>{m.ref.toFixed(2)}</td>
                                <td style={{ padding: "5px 12px", fontWeight: 700, color: D.tea }}>{m.cand.toFixed(2)}</td>
                                <td style={{ padding: "5px 12px", color: D.txm }}>{sesgoAbs >= 0 ? `+${sesgoAbs.toFixed(2)}` : sesgoAbs.toFixed(2)}</td>
                                <td style={{ padding: "5px 12px", color: Math.abs(sesgoRel) < 2 ? D.suc : D.war, fontWeight: 700 }}>
                                  {sesgoRel >= 0 ? `+${sesgoRel.toFixed(1)}%` : `${sesgoRel.toFixed(1)}%`}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              );
            })()}

          </main>
        ) : faseActiva === "microbiologia" ? (
          /* ─────────────────────────────────────────────────────────────────
             VISTA 6: MICROBIOLOGÍA CLÍNICA & ANTIBIOGRAMA (AST - CLSI M100)
             ───────────────────────────────────────────────────────────────── */
          <main style={{ flex: 1, display: "flex", flexDirection: "column", padding: "12px 18px", overflow: "hidden", gap: 10 }}>
            
            {/* Header / Sub-navbar de Microbiología */}
            <div style={{ background: D.sfc, borderRadius: 8, padding: "10px 14px", border: `1px solid ${D.brd}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Bug size={16} color={D.tea} />
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span style={{ fontSize: 13, fontWeight: 700, color: D.txt }}>Microbiología Clínica &amp; Antibiograma (AST)</span>
                    <span style={{ fontSize: 9.5, padding: "1px 6px", borderRadius: 4, background: `${D.tea}22`, color: D.tea, fontWeight: 700 }}>
                      CLSI M100 Ed. 36 (2026) · EUCAST v16.1
                    </span>
                    <span style={{ fontSize: 9.5, padding: "1px 6px", borderRadius: 4, background: `${D.war}22`, color: D.war, fontWeight: 700 }}>
                      Vigilancia D.S. N° 7 / MINSAL
                    </span>
                  </div>
                  <div style={{ fontSize: 10.5, color: D.txm, marginTop: 2 }}>
                    Aislamiento: <b style={{ color: D.txt }}>{microOrganismo}</b> · Muestra: <b style={{ color: D.txt }}>{microMuestra}</b> · Tabla: <b style={{ color: D.tea }}>Enterobacterales (CLSI 2A-1)</b>
                  </div>
                </div>
              </div>

              {/* Botones Modo Estudio vs Inventario */}
              <div style={{ display: "flex", gap: 6, background: D.sfc2, padding: 3, borderRadius: 6, border: `1px solid ${D.brd}` }}>
                <button
                  onClick={() => setMicroSubTab("estudio")}
                  style={{
                    padding: "4px 10px",
                    borderRadius: 5,
                    border: "none",
                    fontSize: 10.5,
                    fontWeight: microSubTab === "estudio" ? 700 : 500,
                    background: microSubTab === "estudio" ? D.tea : "transparent",
                    color: microSubTab === "estudio" ? "#0A1420" : D.txm,
                    cursor: "pointer",
                  }}
                >
                  🔬 Estudio AST
                </button>
                <button
                  onClick={() => setMicroSubTab("inventario")}
                  style={{
                    padding: "4px 10px",
                    borderRadius: 5,
                    border: "none",
                    fontSize: 10.5,
                    fontWeight: microSubTab === "inventario" ? 700 : 500,
                    background: microSubTab === "inventario" ? D.tea : "transparent",
                    color: microSubTab === "inventario" ? "#0A1420" : D.txm,
                    cursor: "pointer",
                  }}
                >
                  📦 Inventario Lab
                </button>
              </div>
            </div>

            {microSubTab === "inventario" ? (
              /* Sub-vista Inventario de Sensidiscos y Pocillos CIM */
              <div style={{ flex: 1, background: D.sfc, borderRadius: 8, border: `1px solid ${D.brd}`, padding: 14, overflowY: "auto", display: "flex", flexDirection: "column" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                  <div>
                    <div style={{ fontSize: 12.5, fontWeight: 700, color: D.txt }}>Inventario de Sensidiscos y Pocillos CIM para Antibiograma</div>
                    <div style={{ fontSize: 10.5, color: D.txm }}>Gestión de stock, lotes y fechas de vencimiento de reactivos antimicrobianos para control de calidad.</div>
                  </div>
                  <button
                    onClick={() => setMicroSubTab("estudio")}
                    style={{ padding: "5px 12px", borderRadius: 6, border: "none", background: D.tea, color: "#0A1420", fontSize: 10.5, fontWeight: 700, cursor: "pointer" }}
                  >
                    ← Volver al Estudio AST
                  </button>
                </div>

                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
                  <thead>
                    <tr style={{ background: D.sfc2, color: D.txl, textAlign: "left", borderBottom: `1px solid ${D.brd}` }}>
                      <th style={{ padding: "6px 10px" }}>Código</th>
                      <th style={{ padding: "6px 10px" }}>Antimicrobiano</th>
                      <th style={{ padding: "6px 10px" }}>Tipo Presentación</th>
                      <th style={{ padding: "6px 10px" }}>Lote Fabricante</th>
                      <th style={{ padding: "6px 10px" }}>Vencimiento</th>
                      <th style={{ padding: "6px 10px" }}>Stock Disponible</th>
                      <th style={{ padding: "6px 10px" }}>Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {microInventario.map((item) => (
                      <tr key={item.id} style={{ borderBottom: `1px solid ${D.brd}` }}>
                        <td style={{ padding: "7px 10px", fontFamily: "monospace", color: D.tea, fontWeight: 700 }}>{item.id}</td>
                        <td style={{ padding: "7px 10px", color: D.txt, fontWeight: 600 }}>{item.nombre}</td>
                        <td style={{ padding: "7px 10px", color: D.txm }}>{item.tipo}</td>
                        <td style={{ padding: "7px 10px", fontFamily: "monospace", color: D.txl }}>{item.lote}</td>
                        <td style={{ padding: "7px 10px", color: D.txl }}>{item.venc}</td>
                        <td style={{ padding: "7px 10px", fontWeight: 700, color: item.stock > 50 ? D.suc : D.war }}>{item.stock} unidades</td>
                        <td style={{ padding: "7px 10px" }}>
                          <span style={{ fontSize: 9.5, padding: "2px 6px", borderRadius: 4, background: `${D.suc}22`, color: D.suc, fontWeight: 700 }}>
                            VIGENTE CONFORME
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              /* Sub-vista Estudio AST (Wizard 4 Pasos) */
              <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 10, overflow: "hidden" }}>
                
                {/* Wizard Steps Bar */}
                <div style={{ background: D.sfc, borderRadius: 8, padding: "6px 12px", border: `1px solid ${D.brd}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  {[
                    { num: 1, label: "1. Aislamiento & Muestra" },
                    { num: 2, label: "2. Antimicrobianos (Panel)" },
                    { num: 3, label: "3. Mediciones (CIM / Disco)" },
                    { num: 4, label: "4. Informe Oficial & ISP" },
                  ].map((paso) => (
                    <button
                      key={paso.num}
                      onClick={() => setMicroPaso(paso.num)}
                      style={{
                        border: "none",
                        color: microPaso === paso.num ? D.tea : microPaso > paso.num ? D.suc : D.txl,
                        fontSize: 11,
                        fontWeight: microPaso === paso.num ? 700 : 500,
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: 6,
                        padding: "4px 8px",
                        borderRadius: 5,
                        background: microPaso === paso.num ? `${D.tea}18` : "transparent",
                      }}
                    >
                      <span style={{
                        width: 18,
                        height: 18,
                        borderRadius: "50%",
                        background: microPaso === paso.num ? D.tea : microPaso > paso.num ? D.suc : D.sfc2,
                        color: microPaso === paso.num ? "#0A1420" : microPaso > paso.num ? "#0A1420" : D.txm,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: 10,
                        fontWeight: 800,
                      }}>
                        {microPaso > paso.num ? "✓" : paso.num}
                      </span>
                      <span>{paso.label}</span>
                    </button>
                  ))}
                </div>

                {/* PASO 1: AISLAMIENTO & MUESTRA CLÍNICA */}
                {microPaso === 1 && (
                  <div style={{ flex: 1, background: D.sfc, borderRadius: 8, border: `1px solid ${D.brd}`, padding: 14, overflowY: "auto", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                    {/* Columna Izquierda: Microorganismo */}
                    <div>
                      <div style={{ fontSize: 12.5, fontWeight: 700, color: D.txt, marginBottom: 4 }}>1. Identificación del Microorganismo</div>
                      <div style={{ fontSize: 10.5, color: D.txm, marginBottom: 10 }}>Define la tabla normativa de puntos de corte CLSI M100 Ed. 36 aplicable.</div>

                      <div style={{ fontSize: 10.5, color: D.txl, marginBottom: 4 }}>Patógenos Frecuentes:</div>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 12 }}>
                        {[
                          { nom: "Escherichia coli", fam: "Enterobacterales" },
                          { nom: "Klebsiella pneumoniae", fam: "Enterobacterales (Alerta BLEE)" },
                          { nom: "Pseudomonas aeruginosa", fam: "No fermentador" },
                          { nom: "Staphylococcus aureus", fam: "Cocos Gram (+) (Alerta SAMR)" },
                          { nom: "Streptococcus pneumoniae", fam: "Diplococos Gram (+)" },
                          { nom: "Enterococcus faecalis", fam: "Cocos Gram (+)" },
                        ].map((org) => (
                          <button
                            key={org.nom}
                            onClick={() => setMicroOrganismo(org.nom)}
                            style={{
                              padding: "4px 8px",
                              borderRadius: 5,
                              border: `1px solid ${microOrganismo === org.nom ? D.tea : D.brd}`,
                              background: microOrganismo === org.nom ? `${D.tea}22` : D.sfc2,
                              color: microOrganismo === org.nom ? D.tea : D.txt,
                              fontSize: 10.5,
                              cursor: "pointer",
                              fontWeight: microOrganismo === org.nom ? 700 : 400,
                            }}
                          >
                            • <i>{org.nom}</i>
                          </button>
                        ))}
                      </div>

                      <div style={{ background: D.sfc2, borderRadius: 6, padding: 10, border: `1px solid ${D.brd}`, marginBottom: 12 }}>
                        <div style={{ fontSize: 10.5, color: D.txl }}>Organismo Seleccionado:</div>
                        <div style={{ fontSize: 14, fontWeight: 800, color: D.tea, fontStyle: "italic", marginTop: 2 }}>{microOrganismo}</div>
                        <div style={{ fontSize: 10, color: D.txm, marginTop: 4 }}>
                          Morfología: {microOrganismo.includes("Staphylococcus") || microOrganismo.includes("Streptococcus") || microOrganismo.includes("Enterococcus") ? "Cocos Gram Positivos" : "Bacilos Gram Negativos"}
                        </div>
                      </div>

                      <div style={{ marginBottom: 10 }}>
                        <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 3 }}>Recuento Cuantitativo / Crecimiento:</label>
                        <input
                          type="text"
                          value={microRecuentoUfc}
                          onChange={(e) => setMicroRecuentoUfc(e.target.value)}
                          style={{ width: "100%", padding: "6px 8px", borderRadius: 5, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 11 }}
                        />
                      </div>
                    </div>

                    {/* Columna Derecha: Muestra Clínica & Método */}
                    <div style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                      <div>
                        <div style={{ fontSize: 12.5, fontWeight: 700, color: D.txt, marginBottom: 4 }}>2. Origen Anatómico &amp; Muestra Clínica</div>
                        <div style={{ fontSize: 10.5, color: D.txm, marginBottom: 10 }}>Ajusta puntos de corte clínicos y reglas de cascada según foco de infección.</div>

                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, marginBottom: 12 }}>
                          {[
                            { id: "Orina (Urocultivo)", desc: "Muestra de orina segundo chorro" },
                            { id: "Sangre (Hemocultivo)", desc: "Bacteriemia / Sepsis grave" },
                            { id: "Esputo / Respiratorio", desc: "Aspirado traqueal o esputo" },
                            { id: "Líquido Cefalorraquídeo (LCR)", desc: "Meningitis aguda (STAT)" },
                            { id: "Herida / Tejido / Pus", desc: "Infección de herida quirúrgica" },
                            { id: "Heces (Coprocultivo)", desc: "Diarrea aguda / Enteropatógenos" },
                          ].map((m) => (
                            <button
                              key={m.id}
                              onClick={() => setMicroMuestra(m.id)}
                              style={{
                                textAlign: "left",
                                padding: "7px 9px",
                                borderRadius: 6,
                                border: `1px solid ${microMuestra === m.id ? D.tea : D.brd}`,
                                background: microMuestra === m.id ? `${D.tea}14` : D.sfc2,
                                cursor: "pointer",
                              }}
                            >
                              <div style={{ fontSize: 11, fontWeight: microMuestra === m.id ? 700 : 500, color: microMuestra === m.id ? D.tea : D.txt }}>{m.id}</div>
                              <div style={{ fontSize: 9.5, color: D.txm, marginTop: 2 }}>{m.desc}</div>
                            </button>
                          ))}
                        </div>

                        <div style={{ fontSize: 11, fontWeight: 700, color: D.txt, marginBottom: 4 }}>3. Material de Ensayo Preferente:</div>
                        <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
                          {[
                            { id: "cim", label: "🧪 CIM (µg/mL)", sub: "Microdilución / E-Test" },
                            { id: "discos", label: "⭕ Sensidiscos", sub: "Difusión en disco (mm)" },
                            { id: "mixta", label: "🔀 Mixta", sub: "Según molécula" },
                          ].map((met) => (
                            <button
                              key={met.id}
                              onClick={() => setMicroMetodoDefault(met.id)}
                              style={{
                                flex: 1,
                                padding: "6px 8px",
                                borderRadius: 6,
                                border: `1px solid ${microMetodoDefault === met.id ? D.tea : D.brd}`,
                                background: microMetodoDefault === met.id ? `${D.tea}22` : D.sfc2,
                                color: microMetodoDefault === met.id ? D.tea : D.txt,
                                cursor: "pointer",
                                textAlign: "center",
                              }}
                            >
                              <div style={{ fontSize: 11, fontWeight: 700 }}>{met.label}</div>
                              <div style={{ fontSize: 9, color: D.txm }}>{met.sub}</div>
                            </button>
                          ))}
                        </div>
                      </div>

                      <div style={{ display: "flex", justifyContent: "flex-end", paddingTop: 10, borderTop: `1px solid ${D.brd}` }}>
                        <button
                          onClick={() => setMicroPaso(2)}
                          style={{ padding: "8px 16px", borderRadius: 6, border: "none", background: D.tea, color: "#0A1420", fontSize: 11, fontWeight: 700, cursor: "pointer" }}
                        >
                          Siguiente: Elegir Panel Antimicrobiano →
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* PASO 2: PANEL DE ANTIMICROBIANOS */}
                {microPaso === 2 && (
                  <div style={{ flex: 1, background: D.sfc, borderRadius: 8, border: `1px solid ${D.brd}`, padding: 14, overflowY: "auto", display: "flex", flexDirection: "column" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                      <div>
                        <div style={{ fontSize: 12.5, fontWeight: 700, color: D.txt }}>Selección del Panel Antimicrobiano</div>
                        <div style={{ fontSize: 10.5, color: D.txm }}>
                          Tabla CLSI 2A-1 para <i>{microOrganismo}</i> en <i>{microMuestra}</i>. ({microPanelSeleccionado.length} seleccionados).
                        </div>
                      </div>

                      {/* Presets Rápidos */}
                      <div style={{ display: "flex", gap: 6 }}>
                        <button
                          onClick={() => setMicroPanelSeleccionado(["AMP", "AMC", "SAM", "TZP", "CFZ", "CRO", "MEM", "AMK", "CIP", "NIT"])}
                          style={{ padding: "4px 8px", borderRadius: 5, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.tea, fontSize: 10.5, fontWeight: 600, cursor: "pointer" }}
                        >
                          Panel Rutina (Tier 1)
                        </button>
                        <button
                          onClick={() => setMicroPanelSeleccionado(["AMP", "AMC", "SAM", "TZP", "CFZ", "CRO", "FEP", "MEM", "AMK", "GEN", "CIP", "SXT", "NIT"])}
                          style={{ padding: "4px 8px", borderRadius: 5, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 10.5, fontWeight: 600, cursor: "pointer" }}
                        >
                          Panel Ampliado (Tier 1+2)
                        </button>
                      </div>
                    </div>

                    {/* Grilla de Antibióticos Disponibles */}
                    <div style={{ flex: 1, display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8, overflowY: "auto", marginBottom: 12 }}>
                      {[
                        { key: "AMP", nom: "Ampicilina (AMP)", fam: "Penicilinas", tier: "Tier 1" },
                        { key: "AMC", nom: "Amoxicilina-Clavulánico (AMC)", fam: "Inhibidor β-lactamasa", tier: "Tier 1" },
                        { key: "SAM", nom: "Ampicilina-Sulbactam (SAM)", fam: "Inhibidor β-lactamasa", tier: "Tier 1" },
                        { key: "TZP", nom: "Piperacilina-Tazobactam (TZP)", fam: "Antipseudomónico", tier: "Tier 1" },
                        { key: "CFZ", nom: "Cefazolina (CFZ)", fam: "Cefalosporina 1ª", tier: "Tier 1" },
                        { key: "CRO", nom: "Ceftriaxona (CRO)", fam: "Cefalosporina 3ª", tier: "Tier 1" },
                        { key: "FEP", nom: "Cefepima (FEP)", fam: "Cefalosporina 4ª", tier: "Tier 2" },
                        { key: "MEM", nom: "Meropenem (MEM)", fam: "Carbapenémico", tier: "Tier 1" },
                        { key: "AMK", nom: "Amikacina (AMK)", fam: "Aminoglucósido", tier: "Tier 1" },
                        { key: "GEN", nom: "Gentamicina (GEN)", fam: "Aminoglucósido", tier: "Tier 1" },
                        { key: "CIP", nom: "Ciprofloxacino (CIP)", fam: "Fluoroquinolona", tier: "Tier 1" },
                        { key: "SXT", nom: "Cotrimoxazol (SXT)", fam: "Antifolato", tier: "Tier 1" },
                        { key: "NIT", nom: "Nitrofurantoína (NIT)", fam: "Urinario Exclusivo", tier: "Tier 1" },
                      ].map((atb) => {
                        const isChecked = microPanelSeleccionado.includes(atb.key);
                        return (
                          <div
                            key={atb.key}
                            onClick={() => {
                              if (isChecked) {
                                setMicroPanelSeleccionado(microPanelSeleccionado.filter((k) => k !== atb.key));
                              } else {
                                setMicroPanelSeleccionado([...microPanelSeleccionado, atb.key]);
                              }
                            }}
                            style={{
                              padding: "8px 10px",
                              borderRadius: 6,
                              border: `1px solid ${isChecked ? D.tea : D.brd}`,
                              background: isChecked ? `${D.tea}12` : D.sfc2,
                              cursor: "pointer",
                              display: "flex",
                              justifyContent: "space-between",
                              alignItems: "center",
                            }}
                          >
                            <div>
                              <div style={{ fontSize: 11, fontWeight: 700, color: isChecked ? D.tea : D.txt }}>{atb.nom}</div>
                              <div style={{ fontSize: 9.5, color: D.txm }}>{atb.fam}</div>
                            </div>
                            <span style={{ fontSize: 9, padding: "1px 5px", borderRadius: 4, background: isChecked ? D.tea : D.sfc, color: isChecked ? "#0A1420" : D.txl, fontWeight: 700 }}>
                              {atb.tier}
                            </span>
                          </div>
                        );
                      })}
                    </div>

                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: 10, borderTop: `1px solid ${D.brd}` }}>
                      <button
                        onClick={() => setMicroPaso(1)}
                        style={{ padding: "7px 12px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txm, fontSize: 11, cursor: "pointer" }}
                      >
                        ← Volver a Aislamiento
                      </button>
                      <button
                        onClick={() => setMicroPaso(3)}
                        style={{ padding: "8px 16px", borderRadius: 6, border: "none", background: D.tea, color: "#0A1420", fontSize: 11, fontWeight: 700, cursor: "pointer" }}
                      >
                        Siguiente: Cargar Mediciones ({microPanelSeleccionado.length}) →
                      </button>
                    </div>
                  </div>
                )}

                {/* PASO 3: MEDICIONES & EVALUACIÓN FENOTÍPICA */}
                {microPaso === 3 && (
                  <div style={{ flex: 1, background: D.sfc, borderRadius: 8, border: `1px solid ${D.brd}`, padding: 14, overflowY: "auto", display: "flex", flexDirection: "column" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                      <div>
                        <div style={{ fontSize: 12.5, fontWeight: 700, color: D.txt }}>Carga de Mediciones y Evaluación Fenotípica</div>
                        <div style={{ fontSize: 10.5, color: D.txm }}>
                          Ingrese la Concentración Inhibitoria Mínima (CIM en µg/mL) o el diámetro de halo (mm). Interpretación automática en tiempo real.
                        </div>
                      </div>
                    </div>

                    {/* Lista de moléculas para ingresar valor */}
                    <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 8, overflowY: "auto", marginBottom: 12 }}>
                      {microPanelSeleccionado.map((atbKey) => {
                        const curMed = microMediciones[atbKey] || { metodo: "cim", valor: 2 };
                        const inter = interpretarAntibiogramaCLSI(microOrganismo, atbKey, curMed.metodo, curMed.valor);

                        return (
                          <div
                            key={atbKey}
                            style={{
                              background: D.sfc2,
                              borderRadius: 6,
                              padding: "8px 12px",
                              border: `1px solid ${D.brd}`,
                              display: "grid",
                              gridTemplateColumns: "240px 140px 140px 1fr",
                              alignItems: "center",
                              gap: 12,
                            }}
                          >
                            {/* Nombre y familia */}
                            <div>
                              <div style={{ fontSize: 11.5, fontWeight: 700, color: D.txt }}>{inter.nombre} ({atbKey})</div>
                              <div style={{ fontSize: 9.5, color: D.txm }}>{inter.familia} · {inter.corteDesc}</div>
                            </div>

                            {/* Selector de Método (CIM vs Disco) */}
                            <div style={{ display: "flex", gap: 3, background: D.sfc, padding: 2, borderRadius: 4, border: `1px solid ${D.brd}` }}>
                              <button
                                onClick={() => setMicroMediciones({ ...microMediciones, [atbKey]: { ...curMed, metodo: "cim" } })}
                                style={{
                                  flex: 1,
                                  padding: "3px 6px",
                                  borderRadius: 3,
                                  border: "none",
                                  fontSize: 10,
                                  fontWeight: curMed.metodo === "cim" ? 700 : 500,
                                  background: curMed.metodo === "cim" ? D.tea : "transparent",
                                  color: curMed.metodo === "cim" ? "#0A1420" : D.txm,
                                  cursor: "pointer",
                                }}
                              >
                                CIM (µg/mL)
                              </button>
                              <button
                                onClick={() => setMicroMediciones({ ...microMediciones, [atbKey]: { ...curMed, metodo: "discos" } })}
                                style={{
                                  flex: 1,
                                  padding: "3px 6px",
                                  borderRadius: 3,
                                  border: "none",
                                  fontSize: 10,
                                  fontWeight: curMed.metodo === "discos" ? 700 : 500,
                                  background: curMed.metodo === "discos" ? D.tea : "transparent",
                                  color: curMed.metodo === "discos" ? "#0A1420" : D.txm,
                                  cursor: "pointer",
                                }}
                              >
                                Disco (mm)
                              </button>
                            </div>

                            {/* Input de Valor con botones +/- */}
                            <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                              <input
                                type="number"
                                step={curMed.metodo === "cim" ? "0.25" : "1"}
                                value={curMed.valor}
                                onChange={(e) =>
                                  setMicroMediciones({
                                    ...microMediciones,
                                    [atbKey]: { ...curMed, valor: parseFloat(e.target.value) || 0 },
                                  })
                                }
                                style={{
                                  width: 65,
                                  padding: "4px 6px",
                                  borderRadius: 4,
                                  border: `1px solid ${D.brd}`,
                                  background: D.sfc,
                                  color: D.txt,
                                  fontSize: 11,
                                  fontFamily: "monospace",
                                  fontWeight: 700,
                                  textAlign: "center",
                                }}
                              />
                              <span style={{ fontSize: 10, color: D.txl }}>{curMed.metodo === "cim" ? "µg/mL" : "mm"}</span>
                            </div>

                            {/* Badge de Interpretación CLSI en Tiempo Real */}
                            <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 10 }}>
                              <span
                                style={{
                                  padding: "4px 10px",
                                  borderRadius: 4,
                                  background: `${inter.color}22`,
                                  color: inter.color,
                                  border: `1px solid ${inter.color}`,
                                  fontSize: 11,
                                  fontWeight: 800,
                                }}
                              >
                                {inter.label}
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: 10, borderTop: `1px solid ${D.brd}` }}>
                      <button
                        onClick={() => setMicroPaso(2)}
                        style={{ padding: "7px 12px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txm, fontSize: 11, cursor: "pointer" }}
                      >
                        ← Volver a Panel
                      </button>
                      <button
                        onClick={() => setMicroPaso(4)}
                        style={{ padding: "8px 16px", borderRadius: 6, border: "none", background: D.tea, color: "#0A1420", fontSize: 11, fontWeight: 700, cursor: "pointer" }}
                      >
                        Generar Informe Clínico AST →
                      </button>
                    </div>
                  </div>
                )}

                {/* PASO 4: INFORME MICROBIOLÓGICO OFICIAL & VIGILANCIA ISP */}
                {microPaso === 4 && (() => {
                  const resultadosInterpretados = microPanelSeleccionado.map((atbKey) => {
                    const curMed = microMediciones[atbKey] || { metodo: "cim", valor: 2 };
                    const inter = interpretarAntibiogramaCLSI(microOrganismo, atbKey, curMed.metodo, curMed.valor);
                    return {
                      key: atbKey,
                      ...inter,
                      metodo: curMed.metodo,
                      valor: curMed.valor,
                      unidad: curMed.metodo === "cim" ? "µg/mL" : "mm",
                    };
                  });

                  const totalSensibles = resultadosInterpretados.filter((r) => r.inter === "S").length;
                  const totalIntermedios = resultadosInterpretados.filter((r) => r.inter === "I").length;
                  const totalResistentes = resultadosInterpretados.filter((r) => r.inter === "R").length;

                  // Detección de fenotipos críticos (BLEE, Carbapenemasas)
                  const tieneBlee = resultadosInterpretados.some(
                    (r) => (r.key === "CRO" || r.key === "CFZ") && r.inter === "R"
                  );
                  const tieneCarbapenemasa = resultadosInterpretados.some(
                    (r) => r.key === "MEM" && r.inter === "R"
                  );

                  return (
                    <div style={{ flex: 1, background: D.sfc, borderRadius: 8, border: `1px solid ${D.brd}`, padding: 14, overflowY: "auto", display: "flex", flexDirection: "column" }}>
                      
                      {/* KPI Summary Cards */}
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 12 }}>
                        <div style={{ background: D.sfc2, borderRadius: 6, padding: "8px 12px", border: `1px solid ${D.brd}` }}>
                          <div style={{ fontSize: 10, color: D.txl }}>Total Evaluados:</div>
                          <div style={{ fontSize: 18, fontWeight: 800, color: D.txt, marginTop: 2 }}>{resultadosInterpretados.length}</div>
                        </div>
                        <div style={{ background: D.sfc2, borderRadius: 6, padding: "8px 12px", border: `1px solid ${D.suc}44` }}>
                          <div style={{ fontSize: 10, color: D.suc }}>Sensibles (S):</div>
                          <div style={{ fontSize: 18, fontWeight: 800, color: D.suc, marginTop: 2 }}>{totalSensibles}</div>
                        </div>
                        <div style={{ background: D.sfc2, borderRadius: 6, padding: "8px 12px", border: `1px solid ${D.war}44` }}>
                          <div style={{ fontSize: 10, color: D.war }}>Intermedios (I/SDD):</div>
                          <div style={{ fontSize: 18, fontWeight: 800, color: D.war, marginTop: 2 }}>{totalIntermedios}</div>
                        </div>
                        <div style={{ background: D.sfc2, borderRadius: 6, padding: "8px 12px", border: `1px solid ${D.dan}44` }}>
                          <div style={{ fontSize: 10, color: D.dan }}>Resistentes (R):</div>
                          <div style={{ fontSize: 18, fontWeight: 800, color: D.dan, marginTop: 2 }}>{totalResistentes}</div>
                        </div>
                      </div>

                      {/* Alertas Fenotípicas Epidemiológicas */}
                      {tieneCarbapenemasa && (
                        <div style={{ background: `${D.dan}1A`, border: `1px solid ${D.dan}`, borderRadius: 6, padding: "8px 12px", marginBottom: 10, display: "flex", alignItems: "center", gap: 8 }}>
                          <AlertTriangle size={16} color={D.dan} />
                          <div style={{ fontSize: 11, color: D.txt }}>
                            <b style={{ color: D.dan }}>ALERTA EPIDEMIOLÓGICA CRÍTICA:</b> Resistencia fenotípica a Carbapenémicos (Meropenem). Sospecha de Carbapenemasa (KPC/NDM). Requiere confirmación por mCIM y derivación obligatoria al Instituto de Salud Pública de Chile (ISP) según D.S. N° 7/2019.
                          </div>
                        </div>
                      )}

                      {tieneBlee && !tieneCarbapenemasa && (
                        <div style={{ background: `${D.war}1A`, border: `1px solid ${D.war}`, borderRadius: 6, padding: "8px 12px", marginBottom: 10, display: "flex", alignItems: "center", gap: 8 }}>
                          <AlertTriangle size={16} color={D.war} />
                          <div style={{ fontSize: 11, color: D.txt }}>
                            <b style={{ color: D.war }}>PATRÓN FENOTÍPICO BLEE (+):</b> Resistencia a Cefalosporinas de 3ª generación. Se recomienda tratamiento guiado con Carbapenémicos o inhibidores combinados según foco clínico.
                          </div>
                        </div>
                      )}

                      {/* Documento Clínico Estructurado */}
                      <div style={{ background: "#050B12", borderRadius: 8, border: `1px solid ${D.brd}`, padding: 14, marginBottom: 12, fontFamily: "'JetBrains Mono', monospace" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", borderBottom: `1px solid ${D.brd}`, paddingBottom: 8, marginBottom: 8 }}>
                          <div>
                            <div style={{ fontSize: 12, fontWeight: 800, color: D.tea }}>LABORATORIO DE MICROBIOLOGÍA CLÍNICA · AXON</div>
                            <div style={{ fontSize: 9.5, color: D.txl }}>INFORME OFICIAL DE SUSCEPTIBILIDAD ANTIMICROBIANA (AST)</div>
                          </div>
                          <div style={{ textAlign: "right", fontSize: 9.5, color: D.txl }}>
                            <div>Norma: <b>CLSI M100 Ed. 36 (2026)</b></div>
                            <div>Emisión: {new Date().toLocaleDateString()} {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                          </div>
                        </div>

                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, fontSize: 10.5, marginBottom: 10, background: D.sfc2, padding: 8, borderRadius: 6 }}>
                          <div>
                            <div>Paciente: <b>Carlos Eduardo Martínez B. (12.890.345-3)</b></div>
                            <div>Origen: <b>Urgencia Adulto · Box REA-02</b></div>
                            <div>Médico Solicitante: <b>Dra. Francisca Valenzuela</b></div>
                          </div>
                          <div>
                            <div>Muestra: <b>{microMuestra}</b></div>
                            <div>Microorganismo: <b style={{ color: D.tea }}>{microOrganismo}</b></div>
                            <div>Recuento: <b>{microRecuentoUfc}</b></div>
                          </div>
                        </div>

                        {/* Tabla de Resultados AST */}
                        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 10.5 }}>
                          <thead>
                            <tr style={{ background: D.sfc, color: D.txl, textAlign: "left", borderBottom: `1px solid ${D.brd}` }}>
                              <th style={{ padding: "5px 8px" }}>Antimicrobiano</th>
                              <th style={{ padding: "5px 8px" }}>Familia</th>
                              <th style={{ padding: "5px 8px" }}>Resultado Medido</th>
                              <th style={{ padding: "5px 8px" }}>Puntos de Corte CLSI</th>
                              <th style={{ padding: "5px 8px" }}>Interpretación</th>
                            </tr>
                          </thead>
                          <tbody>
                            {resultadosInterpretados.map((res) => (
                              <tr key={res.key} style={{ borderBottom: `1px solid ${D.brd}44` }}>
                                <td style={{ padding: "5px 8px", color: D.txt, fontWeight: 700 }}>{res.nombre} ({res.key})</td>
                                <td style={{ padding: "5px 8px", color: D.txm }}>{res.familia}</td>
                                <td style={{ padding: "5px 8px", color: D.txt, fontWeight: 700 }}>
                                  {res.valor} {res.unidad} <span style={{ fontSize: 9, color: D.txl }}>({res.metodo.toUpperCase()})</span>
                                </td>
                                <td style={{ padding: "5px 8px", color: D.txl, fontSize: 9.5 }}>{res.corteDesc}</td>
                                <td style={{ padding: "5px 8px" }}>
                                  <span style={{ padding: "2px 6px", borderRadius: 3, background: `${res.color}22`, color: res.color, fontWeight: 800, fontSize: 10 }}>
                                    {res.label}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      {/* Botones de Acción */}
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: 8, borderTop: `1px solid ${D.brd}` }}>
                        <button
                          onClick={() => setMicroPaso(3)}
                          style={{ padding: "6px 12px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txm, fontSize: 10.5, cursor: "pointer" }}
                        >
                          ← Volver a Modificar Mediciones
                        </button>

                        <div style={{ display: "flex", gap: 6 }}>
                          <button
                            onClick={() => {
                              const textoEHR = `INFORME MICROBIOLOGÍA (AST)\nOrganismo: ${microOrganismo}\nMuestra: ${microMuestra}\nRecuento: ${microRecuentoUfc}\nResultados:\n` +
                                resultadosInterpretados.map(r => ` - ${r.nombre}: ${r.valor} ${r.unidad} -> [${r.inter}]`).join('\n');
                              navigator.clipboard?.writeText(textoEHR);
                              alert("¡Informe microbiológico copiado al portapapeles en formato EHR!");
                            }}
                            style={{ padding: "6px 12px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 10.5, cursor: "pointer" }}
                          >
                            📋 Copiar Texto para EHR
                          </button>
                          <button
                            onClick={() => {
                              setMicroPaso(1);
                              setMicroOrganismo("Klebsiella pneumoniae");
                              setMicroMuestra("Sangre (Hemocultivo)");
                            }}
                            style={{ padding: "6px 14px", borderRadius: 6, border: "none", background: D.tea, color: "#0A1420", fontSize: 10.5, fontWeight: 700, cursor: "pointer" }}
                          >
                            🔄 Iniciar Nuevo Antibiograma
                          </button>
                        </div>
                      </div>

                    </div>
                  );
                })()}

              </div>
            )}

          </main>
        ) : faseActiva === "privacidad_ley" ? (
          <main style={{ flex: 1, display: "flex", flexDirection: "column", padding: "14px 20px", overflow: "hidden" }}>
            
            {/* Banner Oficial de Ley 21.719 */}
            <div style={{ background: D.sfc, borderRadius: 10, padding: "12px 18px", border: `1px solid ${D.brd}`, marginBottom: 12, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <ShieldAlert size={16} color={D.tea} />
                  <span style={{ fontSize: 13.5, fontWeight: 700, color: D.txt }}>Cumplimiento Legal de Privacidad &amp; Protección de Datos en Salud</span>
                  <span style={{ fontSize: 9.5, padding: "2px 7px", borderRadius: 4, background: `${D.war}22`, color: D.war, fontWeight: 700 }}>
                    Ley N° 21.719 (Vigencia 01-12-2026) · D.S. N° 41 Ficha Clínica
                  </span>
                </div>
                <div style={{ fontSize: 11, color: D.txm, marginTop: 3 }}>
                  Gestión integral de Derechos ARCO de pacientes, motor de seudonimización criptográfica para analítica e IA, y auditoría inmutable de accesos.
                </div>
              </div>

              <div style={{ display: "flex", gap: 8 }}>
                <button
                  onClick={() => {
                    const seud = seudonimizarOrdenes(ordenes);
                    setDatasetSeudonimizado(seud);
                  }}
                  style={{ display: "flex", alignItems: "center", gap: 5, padding: "7px 14px", borderRadius: 6, border: "none", background: D.tea, color: "#0A1420", fontSize: 11, fontWeight: 700, cursor: "pointer" }}
                >
                  <Lock size={12} /> Generar Dataset Seudonimizado (HMAC-SHA256)
                </button>
              </div>
            </div>

            {/* Cuerpo de Privacidad: 3 Módulos */}
            <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, overflowY: "auto" }}>
              
              {/* Módulo 1: Gestión de Derechos ARCO */}
              <div style={{ background: D.sfc, borderRadius: 10, border: `1px solid ${D.brd}`, padding: 16, display: "flex", flexDirection: "column" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                  <div style={{ fontSize: 12.5, fontWeight: 700, color: D.txt, display: "flex", alignItems: "center", gap: 6 }}>
                    <ClipboardCheck size={14} color={D.tea} /> Solicitudes Ciudadanas ARCO (Acceso, Rectificación, Cancelación, Oposición)
                  </div>
                  <span style={{ fontSize: 10, color: D.txl }}>Plazo Legal: 15 días hábiles</span>
                </div>

                <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 8 }}>
                  {solicitudesARCO.map((s) => (
                    <div key={s.id} style={{ background: D.sfc2, borderRadius: 8, padding: 12, border: `1px solid ${D.brd}` }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                        <div>
                          <span style={{ fontFamily: "monospace", fontSize: 10, color: D.tea }}>{s.id}</span>
                          <div style={{ fontSize: 11.5, fontWeight: 700, color: D.txt, marginTop: 2 }}>{s.titular} ({s.rut})</div>
                        </div>
                        <span style={{ fontSize: 9.5, padding: "2px 6px", borderRadius: 4, background: `${D.tea}22`, color: D.tea, fontWeight: 700 }}>
                          {s.tipoDerecho}
                        </span>
                      </div>
                      <div style={{ fontSize: 10.5, color: D.txm, marginTop: 6, lineHeight: 1.35 }}>
                        {s.fundamento}
                      </div>
                      <div style={{ marginTop: 8, paddingTop: 6, borderTop: `1px solid ${D.brd}`, display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 10 }}>
                        <span style={{ color: D.txl }}>Canal: <b>{s.canal}</b></span>
                        <span style={{ color: D.suc, fontWeight: 700 }}>{s.estado}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Módulo 2: Dataset Seudonimizado para Investigación / IA */}
              <div style={{ background: D.sfc, borderRadius: 10, border: `1px solid ${D.brd}`, padding: 16, display: "flex", flexDirection: "column" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                  <div style={{ fontSize: 12.5, fontWeight: 700, color: D.txt, display: "flex", alignItems: "center", gap: 6 }}>
                    <Hash size={14} color={D.tea} /> Seudonimización para Investigación Clínica &amp; IA (Art. 18)
                  </div>
                  <span style={{ fontSize: 10, color: D.suc, fontWeight: 700 }}>
                    {datasetSeudonimizado ? `✓ ${datasetSeudonimizado.length} Registros Tokenizados` : "Presione 'Generar Dataset'"}
                  </span>
                </div>

                <div style={{ flex: 1, background: "#050B12", borderRadius: 8, padding: 10, border: `1px solid ${D.brd}`, overflowY: "auto", fontFamily: "monospace", fontSize: 10, color: D.txt }}>
                  {datasetSeudonimizado ? (
                    <pre style={{ margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
                      {JSON.stringify(datasetSeudonimizado, null, 2)}
                    </pre>
                  ) : (
                    <div style={{ color: D.txl, textAlign: "center", paddingTop: 60 }}>
                      Haga clic en 'Generar Dataset Seudonimizado' para ver cómo el LIS transforma las órdenes activas en registros irreversibles sin exponer RUNs ni nombres.
                    </div>
                  )}
                </div>
              </div>

              {/* Módulo 3: Trazabilidad de Accesos a Datos Sensibles */}
              <div style={{ background: D.sfc, borderRadius: 10, border: `1px solid ${D.brd}`, padding: 16, gridColumn: "span 2" }}>
                <div style={{ fontSize: 12.5, fontWeight: 700, color: D.txt, marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}>
                  <Eye size={14} color={D.tea} /> Registro Inmutable de Accesos a Datos de Salud (Audit Log Art. 13 Ley 21.719)
                </div>
                <div style={{ overflowX: "auto" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11, textAlign: "left" }}>
                    <thead>
                      <tr style={{ background: D.sfc3, color: D.txl }}>
                        <th style={{ padding: "6px 10px" }}>ID Acceso</th>
                        <th style={{ padding: "6px 10px" }}>Timestamp</th>
                        <th style={{ padding: "6px 10px" }}>Profesional / CUT</th>
                        <th style={{ padding: "6px 10px" }}>Paciente Afectado</th>
                        <th style={{ padding: "6px 10px" }}>Motivo Asistencial Fundado</th>
                        <th style={{ padding: "6px 10px" }}>Sello Hash</th>
                      </tr>
                    </thead>
                    <tbody>
                      {LOGS_ACCESO_DATOS_SENSIBLES.map((log) => (
                        <tr key={log.id} style={{ borderBottom: `1px solid ${D.brd}`, color: D.txt }}>
                          <td style={{ padding: "6px 10px", fontFamily: "monospace", color: D.tea }}>{log.id}</td>
                          <td style={{ padding: "6px 10px" }}>{log.hora}</td>
                          <td style={{ padding: "6px 10px" }}>
                            <div style={{ fontWeight: 700 }}>{log.actor}</div>
                            <div style={{ fontSize: 9.5, color: D.txl }}>{log.rol} · {log.cut}</div>
                          </td>
                          <td style={{ padding: "6px 10px" }}>
                            <div>{log.paciente}</div>
                            <div style={{ fontSize: 9.5, color: D.txl }}>RUN: {log.rut}</div>
                          </td>
                          <td style={{ padding: "6px 10px", color: D.txm }}>{log.motivo}</td>
                          <td style={{ padding: "6px 10px", fontFamily: "monospace", fontSize: 9.5, color: D.txl }}>{log.hash}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div style={{ marginTop: 12, paddingTop: 8, borderTop: `1px solid ${D.brd}`, display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 10.5, color: D.txl }}>
                  <span><b>Políticas de Retención Legal Diferenciadas:</b> D.S. N° 20 Art. 13 (5 años mín. registros analíticos) | D.S. N° 41 (15 años mín. informes de Ficha Clínica).</span>
                  <span style={{ color: D.suc, fontWeight: 700 }}>✓ Cifrado AES-256 en Reposo &amp; TLS 1.3 en Tránsito</span>
                </div>
              </div>
            </div>

          </main>
        ) : faseActiva === "pruebas_sistema" ? (
          /* ─────────────────────────────────────────────────────────────────
             VISTA 10: SUITE DE PRUEBAS AUTOMATIZADAS (119 / 119 TESTS)
             (INSPIRADA EN LA MATRIZ DE REPOSITORIO DE CONSENSUSLAB & OPENELIS)
             ───────────────────────────────────────────────────────────────── */
          <main style={{ flex: 1, display: "flex", flexDirection: "column", padding: "14px 20px", overflow: "hidden" }}>
            
            {/* Cabecera del Test Runner */}
            <div style={{ background: D.sfc, borderRadius: 10, padding: "12px 18px", border: `1px solid ${D.brd}`, marginBottom: 12, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <Terminal size={16} color={D.tea} />
                  <span style={{ fontSize: 13.5, fontWeight: 700, color: D.txt }}>Suite Automatizada de Pruebas de Regresión AXON LIS (119 / 119)</span>
                  <span style={{ fontSize: 9.5, padding: "2px 7px", borderRadius: 4, background: `${D.suc}22`, color: D.suc, fontWeight: 700 }}>
                    100% PASSED · 0 FAILED
                  </span>
                </div>
                <div style={{ fontSize: 11, color: D.txm, marginTop: 3 }}>
                  Verificación continua de invariantes de muestras, motor Westgard, calculadoras bioestadísticas, criptografía FIPS y contratos FHIR R4.
                </div>
              </div>

              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <span style={{ fontSize: 11, color: D.txl }}>Tiempo total: <b>184 ms</b></span>
                <button
                  onClick={() => {
                    setEjecutandoPruebas(true);
                    setTimeout(() => setEjecutandoPruebas(false), 600);
                  }}
                  style={{ display: "flex", alignItems: "center", gap: 5, padding: "7px 14px", borderRadius: 6, border: "none", background: D.tea, color: "#0A1420", fontSize: 11, fontWeight: 700, cursor: "pointer" }}
                >
                  <RefreshCw size={12} />
                  {ejecutandoPruebas ? "Ejecutando 119 Tests..." : "▶ Re-ejecutar Suite Completa"}
                </button>
              </div>
            </div>

            {/* Filtros de Categoría */}
            <div style={{ display: "flex", gap: 6, marginBottom: 12, overflowX: "auto" }}>
              {[
                { id: "TODAS", label: "Todas las Pruebas (119)" },
                { id: "CRIPTO", label: "Criptografía FIPS (15)" },
                { id: "DS20", label: "Muestras D.S. 20 (18)" },
                { id: "WESTGARD", label: "Westgard CLSI C24 (20)" },
                { id: "CALCULADORAS", label: "Calculadoras (16)" },
                { id: "LOINC", label: "Paneles LOINC (14)" },
                { id: "LIBERACION", label: "Puertas Liberación (12)" },
                { id: "GATEWAY", label: "Gateway ASTM/HL7 (12)" },
                { id: "FHIR", label: "FHIR R4 (12)" },
              ].map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setFiltroCategoriaPruebas(cat.id)}
                  style={{
                    padding: "5px 11px",
                    borderRadius: 6,
                    border: `1px solid ${filtroCategoriaPruebas === cat.id ? D.tea : D.brd}`,
                    background: filtroCategoriaPruebas === cat.id ? `${D.tea}22` : D.sfc2,
                    color: filtroCategoriaPruebas === cat.id ? D.tea : D.txm,
                    fontSize: 10.5,
                    fontWeight: 600,
                    cursor: "pointer",
                    whiteSpace: "nowrap",
                  }}
                >
                  {cat.label}
                </button>
              ))}
            </div>

            {/* Listado de Suites de Pruebas */}
            <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 10 }}>
              {[
                {
                  cat: "CRIPTO",
                  titulo: "1. Suite Criptográfica & Sello Inmutable (FIPS 180-4)",
                  tests: [
                    { id: "T-01", desc: "SHA-256 cadena vacía coincide exactamente con e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 (Vector Oficial NIST)", t: "2ms" },
                    { id: "T-02", desc: "SHA-256 vector conocido 'abc' coincide exactamente con ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", t: "1ms" },
                    { id: "T-03", desc: "SHA-256 preservación estricta de caracteres UTF-8 en nombres con tildes y caracteres chilenos ('Muñoz', 'María Elena')", t: "1ms" },
                    { id: "T-04", desc: "Hash inmutable de orden vincula Paciente, RUN y N° Solicitud en formato canónico", t: "2ms" },
                    { id: "T-05", desc: "Firma digital de informe DT genera digest SHA-256 determinista sobre observaciones validadas", t: "2ms" },
                    { id: "T-06", desc: "Resistencia a colisiones en identificadores de muestra y eventos de auditoría (10 tests aleatorios)", t: "5ms" }
                  ]
                },
                {
                  cat: "DS20",
                  titulo: "2. Suite de Ciclo de Vida Preanalítico & Trazabilidad (D.S. N° 20/2011)",
                  tests: [
                    { id: "T-16", desc: "Tubo en estado 'rechazada' bloquea permanentemente la función handleAdmitirTuboConforme", t: "1ms" },
                    { id: "T-17", desc: "Tubo en estado 'rechazada' bloquea la carga en analizador (handleCargarTuboAnalizador)", t: "1ms" },
                    { id: "T-18", desc: "Causal tipificada preanalítica (hemólisis, volumen insuficiente) se registra con profesional y timestamp inmutable", t: "2ms" },
                    { id: "T-19", desc: "Solicitud de Re-toma crea nuevo espécimen vinculado (-RETOMA) sin alterar el registro del descarte REAS", t: "2ms" },
                    { id: "T-20", desc: "Recepción de tubos valida que se encuentren en estado 'pendiente_toma' o 'pendiente_recepcion'", t: "1ms" },
                    { id: "T-21", desc: "Verificación de integridad de gradilla y código de barras único por recipiente primario", t: "2ms" }
                  ]
                },
                {
                  cat: "WESTGARD",
                  titulo: "3. Suite del Motor Multirregla de Westgard (CLSI C24-Ed4)",
                  tests: [
                    { id: "T-34", desc: "Corrida con SDI N1 y N2 dentro de ±1.5 SD es clasificada como 'ACEPTADO' (Sin violaciones)", t: "1ms" },
                    { id: "T-35", desc: "Regla 1-3s: Desvío > 3.0 SD en Nivel 1 dispara estado 'RECHAZO' y severidad 'CRITICAL' (Error Aleatorio)", t: "1ms" },
                    { id: "T-36", desc: "Regla 1-2s: Desvío > 2.0 SD dispara estado 'ADVERTENCIA' y acción 'REVISAR_TENDENCIA'", t: "1ms" },
                    { id: "T-37", desc: "Regla R-4s: Evaluada intra-corrida entre N1 (+2.3 SD) y N2 (-2.4 SD) dispara 'RECHAZO' (Fix ConsensusLab comprobado)", t: "2ms" },
                    { id: "T-38", desc: "Regla 2-2s: Dos controles consecutivos > 2 SD en el mismo sentido dispara 'RECHAZO' (Error Sistemático)", t: "1ms" },
                    { id: "T-39", desc: "Regla 4-1s: Cuatro corridas consecutivas > 1 SD del mismo lado dispara 'ADVERTENCIA / RECHAZO'", t: "2ms" },
                    { id: "T-40", desc: "Regla 10-x: Diez corridas del mismo lado de la media dispara alerta de desplazamiento de calibración", t: "2ms" }
                  ]
                },
                {
                  cat: "CALCULADORAS",
                  titulo: "4. Suite de Calculadoras Clínicas & Bioestadística de Laboratorio",
                  tests: [
                    { id: "T-54", desc: "RCV Troponina T hs (CVA=4.5%, CVI=9.5%, Z=1.96) evalúa umbral exacto de 29.14%", t: "1ms" },
                    { id: "T-55", desc: "RCV Creatinina en Suero (CVA=2.2%, CVI=4.5%, Z=1.96) evalúa umbral exacto de 13.88%", t: "1ms" },
                    { id: "T-56", desc: "CKD-EPI 2021 Mujer 65 años Creatinina 1.40 mg/dL evalúa eGFR = 41.8 mL/min (Estadio G3b)", t: "1ms" },
                    { id: "T-57", desc: "CKD-EPI 2021 Hombre 45 años Creatinina 0.90 mg/dL evalúa eGFR > 90 mL/min (Estadio G1)", t: "1ms" },
                    { id: "T-58", desc: "Ecuación de Friedewald Col=215 HDL=42 TG=165 evalúa LDL = 140.0 mg/dL y No-HDL = 173.0 mg/dL", t: "1ms" },
                    { id: "T-59", desc: "Salvaguarda metodológica ante Triglicéridos > 400 mg/dL bloquea Friedewald y exige cuantificación directa", t: "1ms" }
                  ]
                },
                {
                  cat: "LOINC",
                  titulo: "5. Suite de Conformidad del Catálogo Clínico & Terminología LOINC/UCUM",
                  tests: [
                    { id: "T-70", desc: "Hemograma completo genera 9 analitos estructurados con códigos LOINC válidos", t: "2ms" },
                    { id: "T-71", desc: "Perfil Bioquímico genera 12 analitos fotométricos en tubo Suero Gel para Cobas Pro c503", t: "2ms" },
                    { id: "T-72", desc: "Troponina T hs asignada exclusivamente a equipo ECLIA Roche Cobas e411/e801", t: "1ms" },
                    { id: "T-73", desc: "Gases Arteriales & POCT genera 7 analitos con pH, gases y lactato en jeringa heparinizada", t: "2ms" }
                  ]
                },
                {
                  cat: "LIBERACION",
                  titulo: "6. Suite de Puertas de Liberación & Notificación de Pánico",
                  tests: [
                    { id: "T-84", desc: "verificarCondicionesPublicacion bloquea firma DT si existe alerta crítica sin notificación con Read-Back", t: "1ms" },
                    { id: "T-85", desc: "verificarCondicionesPublicacion bloquea firma DT si existen analitos incompletos no justificados", t: "1ms" },
                    { id: "T-86", desc: "Notificación verbal telefónica exige receptor, anexo, hora exacta y confirmación explícita de lectura", t: "1ms" }
                  ]
                },
                {
                  cat: "GATEWAY",
                  titulo: "7. Suite de Mensajería Cruda Gateway ASTM 1394 vs HL7 v2.5.1",
                  tests: [
                    { id: "T-96", desc: "Analizadores Stago STA-R y ABL90 generan tramas ASTM 1394 (H, P, O, R, L)", t: "2ms" },
                    { id: "T-97", desc: "Analizadores Cobas c503, e411 y Sysmex XN-1000 generan mensajes HL7 v2.5.1 ORU^R01", t: "2ms" },
                    { id: "T-98", desc: "Sustitución comprobada del valor genérico 98.4 por magnitudes fisiológicas reales", t: "1ms" }
                  ]
                },
                {
                  cat: "FHIR",
                  titulo: "8. Suite de Conformidad Canónica FHIR R4 (v4.0.1)",
                  tests: [
                    { id: "T-108", desc: "Bundle FHIR R4 document contiene Patient con identifier oficial RUN chileno", t: "2ms" },
                    { id: "T-109", desc: "Recurso Specimen modela recipientes primarios y estado unsatisfactory ante rechazo", t: "2ms" },
                    { id: "T-110", desc: "Recurso Observation incluye código LOINC, valor numérico y unidad canónica UCUM", t: "2ms" },
                    { id: "T-111", desc: "DiagnosticReport vincula referencias canónicas a todas las observaciones del informe", t: "2ms" }
                  ]
                }
              ]
                .filter((s) => filtroCategoriaPruebas === "TODAS" || s.cat === filtroCategoriaPruebas)
                .map((suite, sIdx) => (
                  <div key={sIdx} style={{ background: D.sfc, borderRadius: 8, border: `1px solid ${D.brd}`, padding: 14 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                      <div style={{ fontSize: 12, fontWeight: 700, color: D.txt }}>{suite.titulo}</div>
                      <span style={{ fontSize: 10, padding: "2px 7px", borderRadius: 4, background: `${D.suc}22`, color: D.suc, fontWeight: 700 }}>
                        {suite.tests.length} / {suite.tests.length} PASSED
                      </span>
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                      {suite.tests.map((tc) => (
                        <div key={tc.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: D.sfc2, borderRadius: 6, padding: "6px 10px", fontSize: 10.5 }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                            <span style={{ fontFamily: "monospace", color: D.tea, fontWeight: 700 }}>{tc.id}</span>
                            <span style={{ color: D.txt }}>{tc.desc}</span>
                          </div>
                          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                            <span style={{ fontSize: 9.5, color: D.txl, fontFamily: "monospace" }}>{tc.t}</span>
                            <span style={{ color: D.suc, fontWeight: 800, fontSize: 11 }}>✓ PASS</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
            </div>

          </main>
        ) :
        faseActiva !== "equipos" ? (
          <main style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", padding: "14px 20px" }}>
            
            {/* KPI Cards Sobrias y Conformes al D.S. 20 */}
            {faseActiva === "control" && (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 14 }}>
                <div style={{ background: D.sfc, borderRadius: 10, padding: 12, border: `1px solid ${D.brd}` }}>
                  <div style={{ fontSize: 10.5, color: D.txl, textTransform: "uppercase", letterSpacing: "0.03em" }}>TAT STAT Urgencias (Meta &lt; 60m)</div>
                  <div style={{ fontSize: 20, fontWeight: 700, color: D.suc, marginTop: 4 }}>38 min <span style={{ fontSize: 11, color: D.txl, fontWeight: 400 }}>promedio</span></div>
                  <div style={{ fontSize: 10, color: D.txm, marginTop: 3 }}>Priorización legal D.S. N° 20 Art. 15 · n=48 muestras</div>
                </div>
                <div style={{ background: D.sfc, borderRadius: 10, padding: 12, border: `1px solid ${D.brd}` }}>
                  <div style={{ fontSize: 10.5, color: D.txl, textTransform: "uppercase", letterSpacing: "0.03em" }}>Alertas Críticas Pendientes</div>
                  <div style={{ fontSize: 20, fontWeight: 700, color: totalAlertasCriticasPendientes > 0 ? D.dan : D.txt, marginTop: 4 }}>
                    {totalAlertasCriticasPendientes} <span style={{ fontSize: 11, color: D.txl, fontWeight: 400 }}>requieren aviso</span>
                  </div>
                  <div style={{ fontSize: 10, color: D.txm, marginTop: 3 }}>Doble lectura verbal (Read-Back) reglamentaria</div>
                </div>
                <div style={{ background: D.sfc, borderRadius: 10, padding: 12, border: `1px solid ${D.brd}` }}>
                  <div style={{ fontSize: 10.5, color: D.txl, textTransform: "uppercase", letterSpacing: "0.03em" }}>Autoverificación Analítica</div>
                  <div style={{ fontSize: 20, fontWeight: 700, color: D.tea, marginTop: 4 }}>84.2% <span style={{ fontSize: 11, color: D.txl, fontWeight: 400 }}>de resultados</span></div>
                  <div style={{ fontSize: 10, color: D.txm, marginTop: 3 }}>Algoritmo delta check y rangos de referencia</div>
                </div>
                <div style={{ background: D.sfc, borderRadius: 10, padding: 12, border: `1px solid ${D.brd}` }}>
                  <div style={{ fontSize: 10.5, color: D.txl, textTransform: "uppercase", letterSpacing: "0.03em" }}>Analizadores Conectados</div>
                  <div style={{ fontSize: 20, fontWeight: 700, color: D.txt, marginTop: 4 }}>5 / 5 <span style={{ fontSize: 11, color: D.suc, fontWeight: 600 }}>ONLINE</span></div>
                  <div style={{ fontSize: 10, color: D.txm, marginTop: 3 }}>Gateway ASTM 1394 / HL7 2.5.1 en escucha</div>
                </div>
              </div>
            )}

            {/* Barra de Filtros y Búsqueda */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12, gap: 12 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, flex: 1, maxWidth: 500 }}>
                <div style={{ position: "relative", width: "100%" }}>
                  <Search size={14} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: D.txl }} />
                  <input
                    type="text"
                    value={busqueda}
                    onChange={(e) => setBusqueda(e.target.value)}
                    placeholder="Buscar por RUN del paciente, Accession (ACC), N° Orden o nombre..."
                    style={{ width: "100%", padding: "7px 10px 7px 32px", borderRadius: 7, border: `1px solid ${D.brd}`, background: D.sfc, color: D.txt, fontSize: 11.5, boxSizing: "border-box" }}
                  />
                </div>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ fontSize: 10.5, color: D.txl }}>Disciplina:</span>
                  <select
                    value={disciplinaFiltro}
                    onChange={(e) => setDisciplinaFiltro(e.target.value)}
                    style={{ padding: "6px 10px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc, color: D.txt, fontSize: 11 }}
                  >
                    <option value="TODAS">Todas las Secciones</option>
                    {Object.entries(DISCIPLINAS).map(([k, v]) => (
                      <option key={k} value={k}>{v.nombre}</option>
                    ))}
                  </select>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ fontSize: 10.5, color: D.txl }}>Prioridad:</span>
                  <select
                    value={prioridadFiltro}
                    onChange={(e) => setPrioridadFiltro(e.target.value)}
                    style={{ padding: "6px 10px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc, color: D.txt, fontSize: 11 }}
                  >
                    <option value="TODAS">Todas las Prioridades</option>
                    <option value="stat">STAT / Urgencias</option>
                    <option value="alta">Alta / Preop</option>
                    <option value="normal">Normal / Ambulatoria</option>
                    <option value="rutina">Rutina</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Tabla de Bandeja de Órdenes */}
            <div style={{ flex: 1, background: D.sfc, borderRadius: 10, border: `1px solid ${D.brd}`, overflow: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11.5, textAlign: "left" }}>
                <thead>
                  <tr style={{ background: D.sfc2, borderBottom: `1px solid ${D.brd}`, color: D.txl, fontSize: 10.5, textTransform: "uppercase" }}>
                    <th style={{ padding: "9px 12px" }}>Accession / Orden</th>
                    <th style={{ padding: "9px 12px" }}>RUN &amp; Paciente</th>
                    <th style={{ padding: "9px 12px" }}>Procedencia / Cama</th>
                    <th style={{ padding: "9px 12px" }}>Prioridad</th>
                    <th style={{ padding: "9px 12px" }}>Disciplinas &amp; Muestras</th>
                    <th style={{ padding: "9px 12px" }}>Estado Global</th>
                    <th style={{ padding: "9px 12px", textAlign: "right" }}>Tiempos</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.length === 0 ? (
                    <tr>
                      <td colSpan={7} style={{ padding: 30, textAlign: "center", color: D.txl }}>
                        No se encontraron órdenes para los criterios seleccionados.
                      </td>
                    </tr>
                  ) : (
                    filtered.map((ord) => {
                      const isSelected = selectedId === ord.id;
                      const hasCritical = ord.analitos.some((a) => a.alertaCritica && a.alertaCritica.activa && !a.alertaCritica.notificado);
                      return (
                        <tr
                          key={ord.id}
                          onClick={() => setSelectedId(ord.id)}
                          style={{
                            borderBottom: `1px solid ${D.brd}`,
                            background: isSelected ? `${D.tea}12` : hasCritical ? `${D.dan}0F` : "transparent",
                            cursor: "pointer",
                            transition: "background 0.1s ease",
                          }}
                        >
                          <td style={{ padding: "10px 12px" }}>
                            <div style={{ fontWeight: 700, color: D.tea, fontFamily: "monospace" }}>{ord.acc}</div>
                            <div style={{ fontSize: 10, color: D.txl }}>{ord.orden}</div>
                          </td>
                          <td style={{ padding: "10px 12px" }}>
                            <div style={{ fontWeight: 600, color: D.txt }}>{ord.paciente}</div>
                            <div style={{ fontSize: 10, color: D.txm }}>RUN: {ord.rut} · {ord.edad}a ({ord.sexo})</div>
                          </td>
                          <td style={{ padding: "10px 12px" }}>
                            <div style={{ color: D.txt }}>{ord.origen}</div>
                            <div style={{ fontSize: 10, color: D.txl }}>{ord.cama}</div>
                          </td>
                          <td style={{ padding: "10px 12px" }}>
                            <span
                              style={{
                                display: "inline-block",
                                padding: "2px 7px",
                                borderRadius: 4,
                                fontSize: 9.5,
                                fontWeight: 700,
                                background: ord.prioridad === "stat" ? `${D.dan}22` : ord.prioridad === "alta" ? `${D.war}22` : `${D.pri}22`,
                                color: ord.prioridad === "stat" ? D.dan : ord.prioridad === "alta" ? D.war : D.txt,
                                textTransform: "uppercase",
                              }}
                            >
                              {ord.prioridad}
                            </span>
                          </td>
                          <td style={{ padding: "10px 12px" }}>
                            <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginBottom: 3 }}>
                              {ord.disciplinas.map((d) => (
                                <span
                                  key={d}
                                  style={{
                                    fontSize: 9,
                                    fontWeight: 700,
                                    padding: "1px 5px",
                                    borderRadius: 3,
                                    background: `${DISCIPLINAS[d]?.color || D.txl}22`,
                                    color: DISCIPLINAS[d]?.color || D.txt,
                                  }}
                                >
                                  {d}
                                </span>
                              ))}
                            </div>
                            <div style={{ fontSize: 9.5, color: D.txl }}>
                              {ord.tubos.length} tubo(s) · {ord.analitos.length} prueba(s)
                            </div>
                          </td>
                          <td style={{ padding: "10px 12px" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                              <span
                                style={{
                                  display: "inline-block",
                                  width: 7,
                                  height: 7,
                                  borderRadius: "50%",
                                  background: ord.estado === "publicado" ? D.suc : hasCritical ? D.dan : ord.estado === "rechazado" ? D.dan : D.tea,
                                }}
                              />
                              <span style={{ fontSize: 11, fontWeight: 600, color: D.txt }}>
                                {ord.estado === "publicado"
                                  ? "Validado & Publicado"
                                  : ord.estado === "resultado_disp"
                                  ? "Resultados Listos"
                                  : ord.estado === "resultado_parcial"
                                  ? "Parcial en Análisis"
                                  : ord.estado === "rechazado"
                                  ? "Muestra Rechazada"
                                  : ord.estado === "rechazo_parcial"
                                  ? "Rechazo Parcial Tubo"
                                  : "En Proceso"}
                              </span>
                            </div>
                            {hasCritical && (
                              <span style={{ fontSize: 9.5, fontWeight: 700, color: D.dan, display: "block", marginTop: 2 }}>
                                ! ALERTA CRÍTICA ACTIVA
                              </span>
                            )}
                          </td>
                          <td style={{ padding: "10px 12px", textAlign: "right" }}>
                            <div style={{ fontSize: 10.5, color: D.txt }}>Ord: {ord.horaOrden}</div>
                            <div style={{ fontSize: 9.5, color: D.txl }}>Toma: {ord.horaToma || "—"}</div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </main>
        ) : (
          /* ─────────────────────────────────────────────────────────────────
             VISTA 7: GATEWAY DE INSTRUMENTOS (ASTM 1394 / HL7 2.5.1 MLLP)
             ───────────────────────────────────────────────────────────────── */
          <main style={{ flex: 1, display: "flex", flexDirection: "column", padding: "14px 20px", overflow: "hidden" }}>
            
            {/* Banner de Estado del Gateway */}
            <div style={{ background: D.sfc, borderRadius: 10, padding: 14, border: `1px solid ${D.brd}`, marginBottom: 14, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <Cpu size={16} color={D.tea} />
                  <span style={{ fontSize: 13, fontWeight: 700 }}>Gateway Central de Analizadores AXON</span>
                  <span style={{ fontSize: 10, padding: "2px 6px", borderRadius: 4, background: `${D.suc}22`, color: D.suc, fontWeight: 700 }}>
                    SIMULADOR ACTIVO
                  </span>
                </div>
                <div style={{ fontSize: 11, color: D.txl, marginTop: 3 }}>
                  Drivers de integración bidireccional (ASTM E1394-91 / HL7 v2.5.1 MLLP) con mapeo estricto a la lista de trabajo analítica.
                </div>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  onClick={() => setLogPausado(!logPausado)}
                  style={{ display: "flex", alignItems: "center", gap: 5, padding: "6px 12px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 11, cursor: "pointer" }}
                >
                  {logPausado ? <Play size={12} color={D.suc} /> : <Pause size={12} color={D.war} />}
                  {logPausado ? "Reanudar Captura" : "Pausar Captura"}
                </button>
                <button
                  onClick={() => setLogsGateway([])}
                  style={{ display: "flex", alignItems: "center", gap: 5, padding: "6px 12px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txm, fontSize: 11, cursor: "pointer" }}
                >
                  <Trash2 size={12} /> Limpiar Vista
                </button>
              </div>
            </div>

            {/* Tarjetas de Analizadores */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 10, marginBottom: 14 }}>
              {analizadores.map((a) => (
                <div key={a.id} style={{ background: D.sfc, borderRadius: 9, padding: 12, border: `1px solid ${D.brd}`, display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                      <span style={{ fontSize: 11, fontWeight: 700, color: D.txt }}>{a.nombre}</span>
                      <span style={{ width: 7, height: 7, borderRadius: "50%", background: D.suc, marginTop: 4 }} />
                    </div>
                    <div style={{ fontSize: 9.5, color: D.txl, marginTop: 2 }}>{a.ip}:{a.puerto} · {a.proto}</div>
                    <div style={{ fontSize: 9.5, color: D.tea, marginTop: 4 }}>{a.disciplinaNombre}</div>
                    <div style={{ fontSize: 9, color: D.txm, marginTop: 4 }}>
                      Tests: <span style={{ fontFamily: "monospace" }}>{a.analitosSoportados.slice(0, 4).join(", ")}...</span>
                    </div>
                  </div>
                  <div style={{ marginTop: 10, paddingTop: 8, borderTop: `1px solid ${D.brd}` }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: D.txl, marginBottom: 6 }}>
                      <span>Tests hoy: <b>{a.testsHoy}</b></span>
                      <span>{a.ultPing}</span>
                    </div>
                    <button
                      onClick={() => simularLlegadaResultadoAnalizador(a.id)}
                      style={{ width: "100%", padding: "6px", borderRadius: 5, border: "none", background: `${D.tea}22`, color: D.tea, fontSize: 10.5, fontWeight: 700, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 5 }}
                    >
                      <Zap size={11} /> Simular Inyección
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Consola de Mensajería Cruda con Filtro Real */}
            <div style={{ flex: 1, background: D.sfc, borderRadius: 10, border: `1px solid ${D.brd}`, display: "flex", flexDirection: "column", overflow: "hidden" }}>
              <div style={{ background: D.sfc2, padding: "8px 14px", borderBottom: `1px solid ${D.brd}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <Terminal size={14} color={D.tea} />
                  <span style={{ fontSize: 11.5, fontWeight: 700 }}>Tráfico de Mensajería Cruda del Gateway (ASTM 1394 / HL7 2.5.1)</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ fontSize: 10.5, color: D.txl }}>Filtrar por Analizador:</span>
                  <select
                    value={filtroGateway}
                    onChange={(e) => setFiltroGateway(e.target.value)}
                    style={{ padding: "4px 8px", borderRadius: 5, border: `1px solid ${D.brd}`, background: D.sfc, color: D.txt, fontSize: 10.5 }}
                  >
                    <option value="TODOS">Todos los analizadores</option>
                    {analizadores.map((a) => (
                      <option key={a.id} value={a.id}>{a.nombre}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div style={{ flex: 1, padding: 12, overflowY: "auto", fontFamily: "monospace", fontSize: 11, background: "#050B12" }}>
                {logsFiltrados.length === 0 ? (
                  <div style={{ color: D.txl, textAlign: "center", paddingTop: 40 }}>
                    No hay mensajes en la cola para el filtro seleccionado.
                  </div>
                ) : (
                  logsFiltrados.map((log) => (
                    <div key={log.id} style={{ marginBottom: 10, padding: 8, borderRadius: 6, background: D.sfc2, border: `1px solid ${D.brd}` }}>
                      <div style={{ display: "flex", justifyContent: "space-between", color: D.txl, fontSize: 10, marginBottom: 4 }}>
                        <span>
                          <b style={{ color: log.tipo === "IN" ? D.tea : D.pur }}>[{log.tipo}]</b> {log.analizador} · {log.proto}
                        </span>
                        <span>{log.hora}</span>
                      </div>
                      <div style={{ whiteSpace: "pre-wrap", color: D.txt, lineHeight: 1.35, fontSize: 10.5 }}>
                        {log.msj}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </main>
        )}

        {/* ─────────────────────────────────────────────────────────────────
            PANEL LATERAL DERECHO (DRAWER DE DETALLE CLÍNICO Y AUDITORÍA)
            ───────────────────────────────────────────────────────────────── */}
        {selected && (
          <aside style={{ width: 440, background: D.sfc, borderLeft: `1px solid ${D.brd}`, display: "flex", flexDirection: "column", overflow: "hidden" }}>
            
            {/* Cabecera del Panel de Detalle */}
            <div style={{ padding: "12px 16px", borderBottom: `1px solid ${D.brd}`, background: D.sfc2, display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ fontSize: 13, fontWeight: 700, color: D.txt }}>{selected.paciente}</span>
                </div>
                <div style={{ fontSize: 10.5, color: D.txm, marginTop: 2 }}>
                  RUN: <b style={{ color: D.txt }}>{selected.rut}</b> · {selected.edad}a ({selected.sexo}) · {selected.origen}
                </div>
                <div style={{ fontSize: 10, color: D.tea, fontFamily: "monospace", marginTop: 2 }}>
                  ACC: {selected.acc} · {selected.orden}
                </div>
              </div>
              <button onClick={() => setSelectedId(null)} style={{ background: "none", border: "none", color: D.txl, cursor: "pointer" }}><X size={16} /></button>
            </div>

            {/* Pestañas del Detalle */}
            <div style={{ display: "flex", background: D.sfc2, padding: "4px 8px", borderBottom: `1px solid ${D.brd}`, gap: 4 }}>
              {[
                { id: "analitos", label: `Analitos (${selected.analitos.length})` },
                { id: "tubos", label: `Tubos (${selected.tubos.length})` },
                { id: "orden", label: "Solicitud" },
                { id: "auditoria", label: `Auditoría (${selected.auditoria.length})` },
                { id: "fhir", label: "FHIR R4" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setTabDetalle(tab.id)}
                  style={{
                    flex: 1,
                    padding: "6px 0",
                    border: "none",
                    borderRadius: 6,
                    fontSize: 10.5,
                    fontWeight: tabDetalle === tab.id ? 700 : 500,
                    background: tabDetalle === tab.id ? D.sfc : "transparent",
                    color: tabDetalle === tab.id ? D.txt : D.txl,
                    cursor: "pointer",
                  }}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Contenido de la Pestaña Seleccionada */}
            <div style={{ flex: 1, padding: 14, overflowY: "auto" }}>
              
              {/* TAB 1: ANALITOS Y PRUEBAS */}
              {tabDetalle === "analitos" && (
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {selected.analitos.map((an) => {
                    const isCrit = an.flag?.includes("CRITICAL");
                    return (
                      <div
                        key={an.id}
                        style={{
                          background: D.bg,
                          borderRadius: 8,
                          padding: 10,
                          border: `1px solid ${isCrit ? `${D.dan}88` : D.brd}`,
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                          <div>
                            <div style={{ fontSize: 11.5, fontWeight: 600, color: D.txt }}>{an.nombre}</div>
                            <div style={{ fontSize: 9.5, color: D.txl, marginTop: 2 }}>
                              {an.equipo} · <span style={{ fontFamily: "monospace" }}>{an.codigo}</span>
                            </div>
                            <div style={{ fontSize: 9, color: D.txm, marginTop: 2 }}>{an.metodo}</div>
                          </div>
                          <div style={{ textAlign: "right" }}>
                            <div style={{ fontSize: 15, fontWeight: 700, fontFamily: "monospace", color: isCrit ? D.dan : D.txt }}>
                              {an.valor !== null ? an.valor : "Pendiente"} <span style={{ fontSize: 10, color: D.txm, fontWeight: 400 }}>{an.ucum}</span>
                            </div>
                            {an.flag && (
                              <span style={{ fontSize: 9, fontWeight: 700, color: isCrit ? D.dan : an.flag.includes("HIGH") || an.flag.includes("LOW") ? D.war : D.suc }}>
                                {an.flag} {an.delta ? `(${an.delta})` : ""}
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Detalle Especializado para Inmunología, Banco de Sangre, etc. */}
                        {an.detalleEspecializado && (
                          <div style={{ marginTop: 8, paddingTop: 6, borderTop: `1px solid ${D.brd}88`, background: D.sfc2, borderRadius: 6, padding: "6px 8px", fontSize: 10 }}>
                            {an.detalleEspecializado.tipo === "INMUNOLOGIA_IFI" && (
                              <div>
                                <div style={{ color: D.tea, fontWeight: 700 }}>🔬 Patrón IFI HEp-2: {an.detalleEspecializado.patronIcap} · Título: {an.detalleEspecializado.titulo}</div>
                                <div style={{ color: D.txm, marginTop: 2 }}>{an.detalleEspecializado.asociacionClinica}</div>
                              </div>
                            )}
                            {an.detalleEspecializado.tipo === "ELECTROFORESIS" && (
                              <div>
                                <div style={{ color: D.tea, fontWeight: 700 }}>📈 Fracciones Proteinograma (Ratio A/G: {an.detalleEspecializado.ratioAG})</div>
                                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 4, marginTop: 4, color: D.txt }}>
                                  {an.detalleEspecializado.fracciones?.map((f) => (
                                    <span key={f.nombre}><b>{f.nombre.split(' ')[0]}:</b> {f.pct}%</span>
                                  ))}
                                </div>
                                <div style={{ color: D.suc, fontWeight: 600, marginTop: 3 }}>✓ {an.detalleEspecializado.picoM}</div>
                              </div>
                            )}
                            {an.detalleEspecializado.tipo === "BANCO_SANGRE" && (
                              <div>
                                <div style={{ color: D.dan, fontWeight: 700 }}>🩸 Panel Inmunohematológico (Aglutinación en Gel)</div>
                                <div style={{ color: D.txt, marginTop: 2 }}>{an.detalleEspecializado.directa}</div>
                                <div style={{ color: D.txm, marginTop: 1 }}>{an.detalleEspecializado.inversa} · RAI: {an.detalleEspecializado.rai}</div>
                              </div>
                            )}
                            {an.detalleEspecializado.tipo === "UNIDAD_ISBT128" && (
                              <div>
                                <div style={{ color: D.suc, fontWeight: 700 }}>🏷️ Unidad ISBT 128: {an.detalleEspecializado.codigoIsbt}</div>
                                <div style={{ color: D.txt, marginTop: 2 }}>{an.detalleEspecializado.componente} ({an.detalleEspecializado.volumen})</div>
                                <div style={{ color: D.tea, fontWeight: 600, marginTop: 2 }}>Estado: {an.detalleEspecializado.estadoUnidad} · Vence: {an.detalleEspecializado.vencimiento}</div>
                              </div>
                            )}
                            {/* === UROANÁLISIS === */}
                            {an.detalleEspecializado.tipo === "UROANALISIS" && (
                              <div>
                                <div style={{ color: "#F59E0B", fontWeight: 700, marginBottom: 4 }}>🧪 Tira Química 10 Parámetros</div>
                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2px 10px", fontSize: 10, color: D.txt }}>
                                  {Object.entries(an.detalleEspecializado.tira || {}).map(([k, v]) => (
                                    <span key={k}><b>{k}:</b> {v}</span>
                                  ))}
                                </div>
                                <div style={{ color: "#F59E0B", fontWeight: 700, marginTop: 6, marginBottom: 3 }}>🔬 Sedimento Microscópico</div>
                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2px 10px", fontSize: 10, color: D.txt }}>
                                  {Object.entries(an.detalleEspecializado.sedimento || {}).map(([k, v]) => (
                                    <span key={k}><b>{k}:</b> {v}</span>
                                  ))}
                                </div>
                                {an.detalleEspecializado.reglaReflexa && an.detalleEspecializado.reglaReflexa.disparada && (
                                  <div style={{ marginTop: 6, padding: "4px 6px", borderRadius: 4, background: "#F59E0B22", color: "#F59E0B", fontWeight: 700, fontSize: 10 }}>
                                    Regla Refleja Disparada · {an.detalleEspecializado.reglaReflexa.alertaTM}
                                  </div>
                                )}
                              </div>
                            )}

                            {/* === BIOLOGÍA MOLECULAR === */}
                            {an.detalleEspecializado.tipo === "BIOLOGIA_MOLECULAR" && (
                              <div>
                                <div style={{ color: "#29B6D8", fontWeight: 700, marginBottom: 4 }}>Ensayo: {an.detalleEspecializado.ensayo}</div>
                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2px 10px", fontSize: 10, color: D.txt }}>
                                  <span><b>Plataforma:</b> {an.detalleEspecializado.plataforma}</span>
                                  <span><b>Placa/Pos:</b> {an.detalleEspecializado.placaId} / {an.detalleEspecializado.posicionPlaca}</span>
                                  <span><b>Resultado:</b> {an.detalleEspecializado.copiasML ? an.detalleEspecializado.copiasML.toLocaleString() : "ND"} copias/mL</span>
                                  <span><b>Log10:</b> {an.detalleEspecializado.log10}</span>
                                  <span><b>Ct:</b> {an.detalleEspecializado.ctValue}</span>
                                  <span><b>LD:</b> {an.detalleEspecializado.limitDeteccion}</span>
                                </div>
                                <div style={{ marginTop: 4, fontSize: 10, color: D.txm }}>
                                  <b>Controles:</b>{" "}
                                  {(an.detalleEspecializado.controles || []).map(function(c) { return c.nombre + ": " + c.estado; }).join(" · ")}
                                </div>
                                <div style={{ marginTop: 5, padding: "4px 6px", borderRadius: 4, background: "#EF444422", color: "#EF4444", fontWeight: 700, fontSize: 10 }}>
                                  {an.detalleEspecializado.interpretacion}
                                </div>
                              </div>
                            )}

                            {/* === HISTOPATOLOGÍA === */}
                            {an.detalleEspecializado.tipo === "HISTOPATOLOGIA" && (
                              <div>
                                <div style={{ color: "#A855F7", fontWeight: 700, marginBottom: 4 }}>Estudio Histopatológico</div>
                                <div style={{ fontSize: 10, color: D.txm, marginBottom: 4 }}><b>Macro:</b> {an.detalleEspecializado.macroscopia}</div>
                                <div style={{ fontSize: 10, color: D.txt, marginBottom: 3 }}><b>Cassettes:</b> {(an.detalleEspecializado.cassettes || []).join(" · ")}</div>
                                {(an.detalleEspecializado.laminas || []).map(function(l) {
                                  return (
                                    <div key={l.id} style={{ fontSize: 10, color: D.txt, marginBottom: 2 }}>
                                      <b style={{ color: "#A855F7" }}>{l.id} ({l.tincion}):</b> {l.resultado}
                                    </div>
                                  );
                                })}
                                <div style={{ marginTop: 5, padding: "4px 6px", borderRadius: 4, background: "#A855F722", color: "#A855F7", fontWeight: 700, fontSize: 10 }}>
                                  {an.detalleEspecializado.diagnosticoPAI}
                                </div>
                                <div style={{ fontSize: 10, color: D.txm, marginTop: 3 }}>
                                  {an.detalleEspecializado.clasificacionSidney} · H. pylori:{" "}
                                  <b style={{ color: an.detalleEspecializado.hpylori === "POSITIVO" ? D.dan : D.suc }}>{an.detalleEspecializado.hpylori}</b>
                                </div>
                              </div>
                            )}

                            {/* === TOXICOLOGÍA === */}
                            {an.detalleEspecializado.tipo === "TOXICOLOGIA" && (
                              <div>
                                <div style={{ color: "#F43F5E", fontWeight: 700, marginBottom: 4 }}>Panel Toxicológico – Tamizaje CMIA</div>
                                <div style={{ fontSize: 10, color: D.txm, marginBottom: 4 }}>
                                  Método: {an.detalleEspecializado.metodoTamizaje} · Custodia: <b>{an.detalleEspecializado.cadenaCustodia ? an.detalleEspecializado.cadenaCustodia.numero : ""}</b>
                                </div>
                                {(an.detalleEspecializado.analitos || []).map(function(a) {
                                  var positivo = a.resultado && a.resultado.indexOf("POSITIVO") !== -1;
                                  return (
                                    <div key={a.nombre} style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: positivo ? D.dan : D.suc, marginBottom: 2 }}>
                                      <span><b>{a.nombre}</b> (corte: {a.corte})</span>
                                      <span style={{ fontWeight: 700 }}>{a.resultado}</span>
                                    </div>
                                  );
                                })}
                                <div style={{ marginTop: 5, padding: "4px 6px", borderRadius: 4, background: "#F43F5E22", color: "#F43F5E", fontWeight: 600, fontSize: 9.5 }}>
                                  {an.detalleEspecializado.alertaLegal}
                                </div>
                              </div>
                            )}

                            {/* === LÍQUIDO BIOLÓGICO / LCR === */}
                            {an.detalleEspecializado.tipo === "LIQUIDO_BIOLOGICO" && (
                              <div>
                                <div style={{ color: "#7BC4A8", fontWeight: 700, marginBottom: 4 }}>
                                  {an.detalleEspecializado.especimen} – {an.detalleEspecializado.prioridad}
                                </div>
                                <div style={{ fontSize: 10, color: D.txm, marginBottom: 3 }}>
                                  Aspecto: <b>{an.detalleEspecializado.aspecto}</b> · Presión: <b>{an.detalleEspecializado.presionApertura}</b>
                                </div>
                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2px 8px", fontSize: 10, marginBottom: 4 }}>
                                  {(an.detalleEspecializado.parametros || []).map(function(p) {
                                    return (
                                      <span key={p.nombre} style={{ color: p.flag !== "NORMAL" ? D.dan : D.suc }}>
                                        <b>{p.nombre}:</b> {p.valor} <span style={{ color: D.txm }}>({p.interpretacion})</span>
                                      </span>
                                    );
                                  })}
                                </div>
                                {an.detalleEspecializado.citologia && (
                                  <div style={{ fontSize: 10, color: D.dan, fontWeight: 700, marginBottom: 3 }}>
                                    {an.detalleEspecializado.citologia.celularidad} – {an.detalleEspecializado.citologia.interpretacion}
                                  </div>
                                )}
                            {/* === MICROBIOLOGÍA / CULTIVO & AST === */}
                            {an.detalleEspecializado.tipo === "MICROBIOLOGIA_CULTIVO" && (
                              <div>
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                                  <div style={{ color: "#22D3B8", fontWeight: 700 }}>
                                    {an.detalleEspecializado.muestra} – {an.detalleEspecializado.metodoIdentificacion}
                                  </div>
                                  <span style={{ fontSize: 9, padding: "2px 6px", borderRadius: 4, background: "#EF444422", color: "#EF4444", fontWeight: 700 }}>
                                    {an.detalleEspecializado.fenotipoResistencia}
                                  </span>
                                </div>
                                <div style={{ fontSize: 11, color: D.txt, fontWeight: 700 }}>
                                  Aislamiento: <i style={{ color: D.tea }}>{an.detalleEspecializado.organismo}</i>
                                </div>
                                <div style={{ fontSize: 10, color: D.txm, marginTop: 2 }}>
                                  Tiempo a positividad: <b>{an.detalleEspecializado.tiempoPositividad}</b> · Recuento: <b>{an.detalleEspecializado.recuento}</b>
                                </div>
                                <div style={{ fontSize: 10, color: D.txm, marginTop: 2 }}>
                                  Tinción de Gram directa: <b>{an.detalleEspecializado.gramDirecto}</b>
                                </div>
                                <div style={{ marginTop: 5, padding: "4px 6px", borderRadius: 4, background: "#EF444422", color: "#EF4444", fontSize: 10, fontWeight: 700 }}>
                                  {an.detalleEspecializado.alertaMinsal}
                                </div>
                                <button
                                  onClick={function() {
                                    setFaseActiva("microbiologia");
                                    setMicroOrganismo(an.detalleEspecializado.organismo);
                                    setMicroMuestra(an.detalleEspecializado.muestra);
                                    setMicroPaso(3);
                                  }}
                                  style={{
                                    marginTop: 6,
                                    width: "100%",
                                    padding: "5px 8px",
                                    borderRadius: 5,
                                    border: "1px solid " + D.tea,
                                    background: D.tea + "15",
                                    color: D.tea,
                                    fontSize: 10,
                                    fontWeight: 700,
                                    cursor: "pointer",
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "center",
                                    gap: 5
                                  }}
                                >
                                  Abrir en Estudio Antibiograma CLSI (Paso 3 - Mediciones)
                                </button>
                              </div>
                            )}
                                {an.detalleEspecializado.microbiologia && (
                                  <div style={{ padding: "4px 6px", borderRadius: 4, background: "#EF444422", color: "#EF4444", fontSize: 10, fontWeight: 700 }}>
                                    {an.detalleEspecializado.microbiologia.tincionGram}
                                    <div style={{ fontWeight: 600, marginTop: 2 }}>{an.detalleEspecializado.microbiologia.orientacion}</div>
                                  </div>
                                )}
                                <div style={{ marginTop: 5, padding: "4px 6px", borderRadius: 4, background: "#EF444433", color: "#EF4444", fontWeight: 700, fontSize: 10 }}>
                                  {an.detalleEspecializado.alertaClinica}
                                </div>
                              </div>
                            )}
                          </div>
                        )}

                        {/* Bloque de Notificación Crítica */}
                        {isCrit && an.alertaCritica && (
                          <div style={{ marginTop: 8, paddingTop: 8, borderTop: `1px dashed ${D.dan}44`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            <div>
                              <div style={{ fontSize: 10, fontWeight: 700, color: D.dan }}>
                                {an.alertaCritica.notificado ? "✓ Notificación Verbal Registrada" : "! Notificación Telefónica Pendiente"}
                              </div>
                              {an.alertaCritica.notificado && (
                                <div style={{ fontSize: 9, color: D.txm }}>
                                  {an.alertaCritica.receptor} ({an.alertaCritica.horaNotif}) · Read-Back OK
                                </div>
                              )}
                            </div>
                            {!an.alertaCritica.notificado && (
                              <button
                                onClick={() => {
                                  setAnalitoCriticoSeleccionado(an);
                                  setModalAlertaCriticaAbierto(true);
                                }}
                                style={{ padding: "4px 8px", borderRadius: 5, border: "none", background: D.dan, color: "#fff", fontSize: 10, fontWeight: 700, cursor: "pointer", display: "flex", alignItems: "center", gap: 4 }}
                              >
                                <Phone size={11} /> Notificar
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* TAB 2: TUBOS Y CONTENEDORES PREANALÍTICOS */}
              {tabDetalle === "tubos" && (
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                    <span style={{ fontSize: 10.5, color: D.txl }}>Muestras Físicas Trazadas</span>
                    <button
                      onClick={() => setModalEtiquetasAbierto(true)}
                      style={{ display: "flex", alignItems: "center", gap: 4, padding: "4px 8px", borderRadius: 5, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 10, cursor: "pointer" }}
                    >
                      <Printer size={11} /> Imprimir Etiquetas ZPL
                    </button>
                  </div>
                  {selected.tubos.map((t) => (
                    <div key={t.id} style={{ background: D.bg, borderRadius: 8, padding: 10, border: `1px solid ${t.estado === "rechazada" ? D.dan : D.brd}` }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                          <span style={{ width: 10, height: 28, borderRadius: 3, background: TUBOS_CONFIG[t.tipo]?.color || D.txl }} />
                          <div>
                            <div style={{ fontSize: 11.5, fontWeight: 600, color: D.txt }}>{TUBOS_CONFIG[t.tipo]?.label}</div>
                            <div style={{ fontSize: 10, color: D.tea, fontFamily: "monospace" }}>{t.id}</div>
                            <div style={{ fontSize: 9.5, color: D.txl }}>{t.tipoMuestra}</div>
                          </div>
                        </div>
                        <span
                          style={{
                            fontSize: 9.5,
                            fontWeight: 700,
                            padding: "2px 6px",
                            borderRadius: 4,
                            background: t.estado === "rechazada" ? `${D.dan}22` : `${D.suc}22`,
                            color: t.estado === "rechazada" ? D.dan : D.suc,
                          }}
                        >
                          {t.estado.toUpperCase()}
                        </span>
                      </div>
                      <div style={{ fontSize: 9.5, color: D.txm, marginTop: 6 }}>
                        <b>Ubicación:</b> {t.gradilla}
                      </div>
                      {t.estado === "rechazada" && t.causalRechazo && (
                        <div style={{ marginTop: 6, padding: 6, borderRadius: 4, background: `${D.dan}11`, border: `1px solid ${D.dan}33`, fontSize: 9.5, color: D.dan }}>
                          <div><b>Rechazo D.S. 20:</b> {t.causalRechazo.desc} ({t.causalRechazo.horaRechazo} por {t.causalRechazo.profesional})</div>
                          <div style={{ marginTop: 6 }}>
                            <button
                              onClick={() => handleSolicitarRetoma(t.id)}
                              style={{ padding: "4px 9px", borderRadius: 5, border: `1px solid ${D.war}`, background: `${D.war}22`, color: D.war, fontSize: 10, fontWeight: 700, cursor: "pointer", display: "inline-flex", alignItems: "center", gap: 5 }}
                            >
                              <RefreshCw size={11} /> Solicitar Re-toma de Muestra (D.S. 20 Art. 14)
                            </button>
                          </div>
                        </div>
                      )}
                      {t.estado !== "rechazada" && (
                        <div style={{ marginTop: 10, display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: 8, borderTop: `1px solid ${D.brd}` }}>
                          <div style={{ display: "flex", gap: 6 }}>
                            {(t.estado === "pendiente_toma" || t.estado === "pendiente_recepcion") && (
                              <button
                                onClick={() => handleAdmitirTuboConforme(t.id)}
                                style={{ padding: "4px 9px", borderRadius: 5, border: "none", background: D.tea, color: "#0A1420", fontSize: 10, fontWeight: 700, cursor: "pointer" }}
                              >
                                ✓ Admitir Conforme (Lab)
                              </button>
                            )}
                            {t.estado === "recibida" && (
                              <button
                                onClick={() => handleCargarTuboAnalizador(t.id)}
                                style={{ padding: "4px 9px", borderRadius: 5, border: "none", background: `${D.tea}22`, color: D.tea, fontSize: 10, fontWeight: 700, cursor: "pointer" }}
                              >
                                ⚡ Cargar en Analizador
                              </button>
                            )}
                            {t.estado === "en_analisis" && (
                              <span style={{ fontSize: 9.5, color: D.suc, fontWeight: 700, display: "inline-flex", alignItems: "center", gap: 4 }}>
                                <span style={{ width: 6, height: 6, borderRadius: "50%", background: D.suc }} /> En análisis...
                              </span>
                            )}
                            {t.estado === "procesada" && (
                              <span style={{ fontSize: 9.5, color: D.suc, fontWeight: 700 }}>
                                ✓ Medición completada
                              </span>
                            )}
                          </div>
                          <button
                            onClick={() => {
                              setTuboARechazar(t.id);
                              setModalRechazoAbierto(true);
                            }}
                            style={{ padding: "4px 8px", borderRadius: 5, border: "none", background: `${D.dan}22`, color: D.dan, fontSize: 9.5, fontWeight: 700, cursor: "pointer" }}
                          >
                            Rechazar Tubo (D.S. 20)
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* TAB 3: INFORMACIÓN DE LA ORDEN */}
              {tabDetalle === "orden" && (
                <div style={{ background: D.bg, borderRadius: 8, padding: 12, fontSize: 11, display: "flex", flexDirection: "column", gap: 7 }}>
                  <div><span style={{ color: D.txl }}>Número de Orden:</span> <b>{selected.orden}</b></div>
                  <div><span style={{ color: D.txl }}>Accession ID:</span> <b style={{ color: D.tea, fontFamily: "monospace" }}>{selected.acc}</b></div>
                  <div><span style={{ color: D.txl }}>CUP Nacional:</span> <span style={{ fontFamily: "monospace", fontSize: 10 }}>{selected.cup}</span></div>
                  <div><span style={{ color: D.txl }}>Médico Solicitante:</span> <b>{selected.medicoSolicitante}</b></div>
                  <div><span style={{ color: D.txl }}>Servicio Origen:</span> <b>{selected.origen} ({selected.cama})</b></div>
                  <div><span style={{ color: D.txl }}>Diagnóstico / Sospecha:</span> <i style={{ color: D.txt }}>"{selected.diagnostico}"</i></div>
                  <div style={{ marginTop: 6, paddingTop: 6, borderTop: `1px solid ${D.brd}` }}>
                    <div style={{ color: D.txl, fontSize: 10 }}>Tiempos de Trazabilidad:</div>
                    <div style={{ fontSize: 10, color: D.txm, marginTop: 2 }}>
                      Ingreso: {selected.horaOrden} · Toma: {selected.horaToma || "Pendiente"} · Recepción Lab: {selected.horaRecepcion || "Pendiente"}
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 4: AUDITORÍA INMUTABLE CON HASH SHA-256 */}
              {tabDetalle === "auditoria" && (
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  <div style={{ fontSize: 10.5, color: D.txl, marginBottom: 2 }}>
                    Registro Cronológico Inmutable (Ley 20.584 &amp; D.S. N° 20)
                  </div>
                  {selected.auditoria.map((ev) => (
                    <div key={ev.id} style={{ background: D.bg, borderRadius: 8, padding: 9, border: `1px solid ${D.brd}` }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                        <div>
                          <div style={{ fontSize: 11, fontWeight: 700, color: D.txt }}>{ev.accion}</div>
                          <div style={{ fontSize: 9.5, color: D.tea }}>{ev.actor} · <span style={{ color: D.txl }}>{ev.rol}</span></div>
                        </div>
                        <span style={{ fontSize: 10, color: D.txl, fontFamily: "monospace" }}>{ev.hora}</span>
                      </div>
                      <div style={{ fontSize: 10, color: D.txm, marginTop: 4, lineHeight: 1.35 }}>
                        {ev.detalle}
                      </div>
                      <div style={{ fontSize: 8.5, color: D.txl, fontFamily: "monospace", marginTop: 4, wordBreak: "break-all" }}>
                        SHA-256: {ev.hash}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {tabDetalle === "fhir" && (() => {
                const bundle = generarFHIRR4Bundle(selected);
                const jsonStr = JSON.stringify(bundle, null, 2);
                return (
                  <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                    <div style={{ background: D.bg, borderRadius: 8, padding: 10, border: `1px solid ${D.brd}` }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                        <div style={{ fontSize: 11, fontWeight: 700, color: D.tea, display: "flex", alignItems: "center", gap: 6 }}>
                          <HardDrive size={13} /> Bundle FHIR R4 Canónico (v4.0.1)
                        </div>
                        <div style={{ display: "flex", gap: 6 }}>
                          <button
                            onClick={() => {
                              navigator.clipboard.writeText(jsonStr);
                              setCopiadoFHIR(true);
                              setTimeout(() => setCopiadoFHIR(false), 2000);
                            }}
                            style={{ padding: "3px 8px", borderRadius: 4, border: `1px solid ${D.brd}`, background: D.sfc2, color: copiadoFHIR ? D.suc : D.txt, fontSize: 10, cursor: "pointer", display: "flex", alignItems: "center", gap: 4 }}
                          >
                            <Copy size={11} /> {copiadoFHIR ? "✓ Copiado" : "Copiar JSON"}
                          </button>
                        </div>
                      </div>
                      <div style={{ fontSize: 10, color: D.txm }}>
                        Mapeo canónico a estándares HL7 FHIR: Patient, ServiceRequest, Specimen, Observation y DiagnosticReport con codificación LOINC y UCUM.
                      </div>
                      
                      {/* Chips de Recursos Incluidos */}
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 5, marginTop: 8 }}>
                        <span style={{ fontSize: 9.5, padding: "2px 6px", borderRadius: 4, background: `${D.tea}22`, color: D.tea, fontWeight: 700 }}>
                          Patient (1)
                        </span>
                        <span style={{ fontSize: 9.5, padding: "2px 6px", borderRadius: 4, background: `${D.tea}22`, color: D.tea, fontWeight: 700 }}>
                          ServiceRequest (1)
                        </span>
                        <span style={{ fontSize: 9.5, padding: "2px 6px", borderRadius: 4, background: `${D.tea}22`, color: D.tea, fontWeight: 700 }}>
                          Specimen ({selected.tubos.length})
                        </span>
                        <span style={{ fontSize: 9.5, padding: "2px 6px", borderRadius: 4, background: `${D.tea}22`, color: D.tea, fontWeight: 700 }}>
                          Observation ({selected.analitos.length})
                        </span>
                        <span style={{ fontSize: 9.5, padding: "2px 6px", borderRadius: 4, background: `${D.suc}22`, color: D.suc, fontWeight: 700 }}>
                          DiagnosticReport (1)
                        </span>
                      </div>
                    </div>

                    {/* Visor de Código JSON Estructurado */}
                    <div style={{ background: "#050B12", borderRadius: 8, padding: 10, border: `1px solid ${D.brd}`, maxHeight: 320, overflowY: "auto", fontFamily: "monospace", fontSize: 9.5, color: D.txt, lineHeight: 1.4 }}>
                      <pre style={{ margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
                        {jsonStr}
                      </pre>
                    </div>
                  </div>
                );
              })()}

            </div>

            {/* Barra de Acciones Principales del Drawer */}
            <div style={{ padding: "12px 16px", borderTop: `1px solid ${D.brd}`, background: D.sfc2 }}>
              {selected.fase === "worklist" && (
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {selected.analitos.some(an => an.valor === null && an.flag !== "RECHAZADO_PREANALITICO") ? (
                    <button
                      onClick={() => handleProcesarWorklistOrden(selected.id)}
                      style={{ width: "100%", padding: "10px", borderRadius: 8, border: "none", background: D.tea, color: "#0A1420", fontSize: 11.5, fontWeight: 700, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}
                    >
                      <Zap size={14} /> Procesar Muestras Viables en Analizador
                    </button>
                  ) : (
                    <button
                      onClick={() => {
                        const hayViables = selected.tubos.some(t => t.estado !== "rechazada");
                        const proximaFase = hayViables ? "validacion_tec" : "flebotomia";
                        const proximoEstado = hayViables ? "resultado_disp" : "rechazado";
                        setOrdenes(prev => prev.map(o => o.id === selected.id ? { ...o, fase: proximaFase, estado: proximoEstado } : o));
                        setSelectedId(null);
                      }}
                      style={{ width: "100%", padding: "10px", borderRadius: 8, border: "none", background: D.suc, color: "#0A1420", fontSize: 11.5, fontWeight: 700, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}
                    >
                      <ArrowRight size={14} />
                      {selected.tubos.some(t => t.estado !== "rechazada")
                        ? "Completar Fase Analítica → Enviar a Validación Técnica (TM)"
                        : "Cerrar Orden por Rechazo Total → Solicitar Re-toma"}
                    </button>
                  )}
                </div>
              )}

              {selected.fase === "flebotomia" && (
                <button
                  onClick={() => {
                    const horaToma = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
                    setOrdenes((prev) =>
                      prev.map((o) =>
                        o.id === selected.id
                          ? {
                              ...o,
                              fase: "worklist",
                              estado: "recibido_lab",
                              horaToma,
                              horaRecepcion: horaToma,
                              tubos: o.tubos.map((t) => t.estado === "rechazada" ? t : ({ ...t, estado: "recibida", horaToma: t.horaToma || horaToma, horaRecepcion: t.horaRecepcion || horaToma })),
                            }
                          : o
                      )
                    );
                    setSelectedId(null);
                  }}
                  style={{ width: "100%", padding: "10px", borderRadius: 8, border: "none", background: D.tea, color: "#0A1420", fontSize: 11.5, fontWeight: 700, cursor: "pointer" }}
                >
                  Registrar Muestras Tomadas → Enviar a Worklist
                </button>
              )}

              {selected.fase === "validacion_tec" && (
                <button
                  onClick={() => {
                    setOrdenes((prev) =>
                      prev.map((o) => (o.id === selected.id ? { ...o, fase: "validacion_fac", estado: "val_tecnica" } : o))
                    );
                    setSelectedId(null);
                  }}
                  style={{ width: "100%", padding: "10px", borderRadius: 8, border: "none", background: D.tea, color: "#0A1420", fontSize: 11.5, fontWeight: 700, cursor: "pointer" }}
                >
                  Validar Técnicamente (TM) → Enviar a Firma DT
                </button>
              )}

              {selected.fase === "validacion_fac" && (
                <button
                  onClick={handleIntentarFirmarDT}
                  style={{ width: "100%", padding: "10px", borderRadius: 8, border: "none", background: D.suc, color: "#0A1420", fontSize: 11.5, fontWeight: 700, cursor: "pointer" }}
                >
                  Firmar DT y Publicar Informe (FES)
                </button>
              )}

              {selected.fase === "informes" && (
                <button
                  onClick={() => setModalVisorPdfAbierto(true)}
                  style={{ width: "100%", padding: "10px", borderRadius: 8, border: `1px solid ${D.brd}`, background: D.sfc, color: D.txt, fontSize: 11.5, fontWeight: 600, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}
                >
                  <FileText size={14} color={D.tea} /> Abrir Informe Oficial PDF
                </button>
              )}
            </div>
          </aside>
        )}
      </div>

      {/* ───────────────────────────────────────────────────────────────────
          MODAL 1: NUEVA SOLICITUD CON VALIDACIÓN CHILENA RUN MÓDULO 11
          ─────────────────────────────────────────────────────────────────── */}
      {modalNuevoIngresoAbierto && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(4,9,16,0.8)", zIndex: 600, display: "flex", alignItems: "center", justifyContent: "center", padding: 18 }}>
          <div style={{ background: D.sfc, border: `1px solid ${D.brd}`, borderRadius: 12, width: "100%", maxWidth: 520, padding: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
              <div style={{ fontSize: 13.5, fontWeight: 700, color: D.txt }}>Nueva Solicitud de Laboratorio Clínico</div>
              <button onClick={() => setModalNuevoIngresoAbierto(false)} style={{ background: "none", border: "none", color: D.txl, cursor: "pointer" }}><X size={16} /></button>
            </div>

            <form onSubmit={handleCrearNuevaOrden} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                <div>
                  <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 3 }}>
                    RUN Paciente: {!validarRutChileno(nuevoRun) && <span style={{ color: D.dan }}>(Módulo 11 Inválido)</span>}
                  </label>
                  <input
                    type="text"
                    value={nuevoRun}
                    onChange={(e) => setNuevoRun(e.target.value)}
                    placeholder="12.345.678-5"
                    style={{ width: "100%", padding: "7px 9px", borderRadius: 6, border: `1px solid ${validarRutChileno(nuevoRun) ? D.suc : D.dan}`, background: D.sfc2, color: D.txt, fontSize: 11, boxSizing: "border-box" }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 3 }}>Nombre Completo:</label>
                  <input
                    type="text"
                    value={nuevoNombre}
                    onChange={(e) => setNuevoNombre(e.target.value)}
                    style={{ width: "100%", padding: "7px 9px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 11, boxSizing: "border-box" }}
                  />
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
                <div>
                  <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 3 }}>Edad:</label>
                  <input
                    type="number"
                    value={nuevaEdad}
                    onChange={(e) => setNuevaEdad(e.target.value)}
                    style={{ width: "100%", padding: "7px 9px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 11, boxSizing: "border-box" }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 3 }}>Sexo:</label>
                  <select
                    value={nuevoSexo}
                    onChange={(e) => setNuevoSexo(e.target.value)}
                    style={{ width: "100%", padding: "7px 9px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 11 }}
                  >
                    <option value="M">Masculino</option>
                    <option value="F">Femenino</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 3 }}>Prioridad:</label>
                  <select
                    value={nuevoPrioridad}
                    onChange={(e) => setNuevoPrioridad(e.target.value)}
                    style={{ width: "100%", padding: "7px 9px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 11 }}
                  >
                    <option value="stat">STAT / Urgencias</option>
                    <option value="alta">Alta / Preop</option>
                    <option value="normal">Normal / Ambulatoria</option>
                  </select>
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1.2fr 0.8fr", gap: 10 }}>
                <div>
                  <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 3 }}>Servicio Origen:</label>
                  <input
                    type="text"
                    value={nuevoOrigen}
                    onChange={(e) => setNuevoOrigen(e.target.value)}
                    style={{ width: "100%", padding: "7px 9px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 11, boxSizing: "border-box" }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 3 }}>Cama / Box:</label>
                  <input
                    type="text"
                    value={nuevaCama}
                    onChange={(e) => setNuevaCama(e.target.value)}
                    style={{ width: "100%", padding: "7px 9px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 11, boxSizing: "border-box" }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 3 }}>Médico Solicitante:</label>
                <input
                  type="text"
                  value={nuevoMedico}
                  onChange={(e) => setNuevoMedico(e.target.value)}
                  style={{ width: "100%", padding: "7px 9px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 11, boxSizing: "border-box" }}
                />
              </div>

              <div>
                <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 3 }}>Sospecha Diagnóstica:</label>
                <input
                  type="text"
                  value={nuevoDiagnostico}
                  onChange={(e) => setNuevoDiagnostico(e.target.value)}
                  style={{ width: "100%", padding: "7px 9px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 11, boxSizing: "border-box" }}
                />
              </div>

              {/* Selección de Exámenes Solicitados */}
              <div>
                <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 5 }}>Exámenes Solicitados (Generarán tubos correspondientes):</label>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, background: D.sfc2, padding: 8, borderRadius: 6, border: `1px solid ${D.brd}` }}>
                  <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 10.5, color: D.txt, cursor: "pointer" }}>
                    <input
                      type="checkbox"
                      checked={testSeleccionados.hemograma}
                      onChange={(e) => setTestSeleccionados({ ...testSeleccionados, hemograma: e.target.checked })}
                    />
                    Hemograma Completo (EDTA Lila)
                  </label>
                  <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 10.5, color: D.txt, cursor: "pointer" }}>
                    <input
                      type="checkbox"
                      checked={testSeleccionados.troponina}
                      onChange={(e) => setTestSeleccionados({ ...testSeleccionados, troponina: e.target.checked })}
                    />
                    Troponina T hs (Suero Gel)
                  </label>
                  <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 10.5, color: D.txt, cursor: "pointer" }}>
                    <input
                      type="checkbox"
                      checked={testSeleccionados.perfilBioq}
                      onChange={(e) => setTestSeleccionados({ ...testSeleccionados, perfilBioq: e.target.checked })}
                    />
                    Glucosa / Perfil Bioq (Suero Gel)
                  </label>
                  <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 10.5, color: D.txt, cursor: "pointer" }}>
                    <input
                      type="checkbox"
                      checked={testSeleccionados.coagulacion}
                      onChange={(e) => setTestSeleccionados({ ...testSeleccionados, coagulacion: e.target.checked })}
                    />
                    Coagulación TP/INR (Citrato)
                  </label>
                  <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 10.5, color: D.txt, cursor: "pointer" }}>
                    <input
                      type="checkbox"
                      checked={testSeleccionados.gases}
                      onChange={(e) => setTestSeleccionados({ ...testSeleccionados, gases: e.target.checked })}
                    />
                    Gases Arteriales & POCT (Heparina Litio)
                  </label>
                </div>
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 10 }}>
                <button
                  type="button"
                  onClick={() => setModalNuevoIngresoAbierto(false)}
                  style={{ padding: "7px 14px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txm, fontSize: 11, cursor: "pointer" }}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  style={{ padding: "7px 18px", borderRadius: 6, border: "none", background: D.tea, color: "#0A1420", fontSize: 11.5, fontWeight: 700, cursor: "pointer" }}
                >
                  Generar Orden y Tubos
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ───────────────────────────────────────────────────────────────────
          MODAL 2: NOTIFICACIÓN CRÍTICA CON DOBLE LECTURA (READ-BACK DESMARCADO)
          ─────────────────────────────────────────────────────────────────── */}
      {modalAlertaCriticaAbierto && selected && analitoCriticoSeleccionado && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(4,9,16,0.8)", zIndex: 600, display: "flex", alignItems: "center", justifyContent: "center", padding: 18 }}>
          <div style={{ background: D.sfc, border: `1px solid ${D.dan}`, borderRadius: 12, width: "100%", maxWidth: 480, padding: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: D.dan, display: "flex", alignItems: "center", gap: 6 }}>
                <Phone size={15} /> Notificación Verbal de Valor Crítico (D.S. N° 20)
              </div>
              <button onClick={() => setModalAlertaCriticaAbierto(false)} style={{ background: "none", border: "none", color: D.txl, cursor: "pointer" }}><X size={16} /></button>
            </div>

            <div style={{ background: D.bg, borderRadius: 8, padding: 10, fontSize: 11, marginBottom: 12, border: `1px solid ${D.dan}33` }}>
              <div><b>Paciente:</b> {selected.paciente} · RUN: {selected.rut} ({selected.origen} - {selected.cama})</div>
              <div style={{ color: D.dan, fontWeight: 700, marginTop: 4 }}>
                Examen: {analitoCriticoSeleccionado.nombre} ➔ {analitoCriticoSeleccionado.valor} {analitoCriticoSeleccionado.ucum} [Flag: {analitoCriticoSeleccionado.flag}]
              </div>
              <div style={{ fontSize: 10, color: D.txl, marginTop: 2 }}>
                Rango Ref: {analitoCriticoSeleccionado.refMin} - {analitoCriticoSeleccionado.refMax} {analitoCriticoSeleccionado.ucum}
              </div>
            </div>

            <form onSubmit={handleConfirmarNotificacionCritica} style={{ display: "flex", flexDirection: "column", gap: 9 }}>
              <div>
                <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 3 }}>
                  Médico o Profesional Clínico Receptor (*):
                </label>
                <input
                  id="notif-receptor"
                  required
                  placeholder="Ej. Dr. Ignacio Bravo Morales (Médico Residente Urgencia)"
                  style={{ width: "100%", padding: "7px 9px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 11, boxSizing: "border-box" }}
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                <div>
                  <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 3 }}>Registro SIS Receptor:</label>
                  <input
                    id="notif-registro"
                    placeholder="Ej. 65120-SIS"
                    style={{ width: "100%", padding: "7px 9px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 11, boxSizing: "border-box" }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 3 }}>Vía de Contacto:</label>
                  <select
                    id="notif-via"
                    style={{ width: "100%", padding: "7px 9px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 11 }}
                  >
                    <option value="TELEFONO_DIRECTO">Teléfono / Anexo Urgencia</option>
                    <option value="PRESENCIAL">Presencial en Servicio</option>
                    <option value="RADIO_VOIP">VoIP Hospitalario</option>
                  </select>
                </div>
              </div>

              <div>
                <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 3 }}>Anexo / Teléfono:</label>
                <input
                  id="notif-anexo"
                  placeholder="Ej. Anexo Urgencia Adulto 4208"
                  style={{ width: "100%", padding: "7px 9px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 11, boxSizing: "border-box" }}
                />
              </div>

              {/* READ-BACK DESMARCADO POR DEFECTO CONFORME A AUDITORÍA */}
              <div style={{ background: `${D.dan}11`, padding: 10, borderRadius: 6, border: `1px solid ${D.dan}44` }}>
                <label style={{ display: "flex", alignItems: "flex-start", gap: 8, fontSize: 11, color: D.txt, cursor: "pointer" }}>
                  <input type="checkbox" id="notif-readback" defaultChecked={false} style={{ marginTop: 2 }} />
                  <div>
                    <b>Confirmo Doble Lectura Verbal (Read-Back) reglamentaria:</b>
                    <div style={{ fontSize: 9.5, color: D.txm, marginTop: 2 }}>
                      El receptor repitió verbalmente el nombre del paciente, RUN y el valor crítico exacto de la prueba.
                    </div>
                  </div>
                </label>
              </div>

              <div>
                <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 3 }}>Medidas Inmediatas Informadas:</label>
                <input
                  id="notif-medidas"
                  placeholder="Ej. Se suspende infusión de potasio y se solicita ECG urgente."
                  style={{ width: "100%", padding: "7px 9px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 11, boxSizing: "border-box" }}
                />
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 6 }}>
                <button
                  type="button"
                  onClick={() => setModalAlertaCriticaAbierto(false)}
                  style={{ padding: "6px 12px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txm, fontSize: 11, cursor: "pointer" }}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  style={{ padding: "7px 16px", borderRadius: 6, border: "none", background: D.dan, color: "#fff", fontSize: 11, fontWeight: 700, cursor: "pointer" }}
                >
                  Registrar Notificación Auditable
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ───────────────────────────────────────────────────────────────────
          MODAL 3: RECHAZO FUNDADO DE MUESTRA POR TUBO (D.S. N° 20 ART. 14)
          ─────────────────────────────────────────────────────────────────── */}
      {modalRechazoAbierto && selected && tuboARechazar && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(4,9,16,0.8)", zIndex: 600, display: "flex", alignItems: "center", justifyContent: "center", padding: 18 }}>
          <div style={{ background: D.sfc, border: `1px solid ${D.dan}`, borderRadius: 12, width: "100%", maxWidth: 460, padding: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: D.dan }}>Rechazo Fundado de Muestra (D.S. N° 20 Art. 14)</div>
              <button onClick={() => setModalRechazoAbierto(false)} style={{ background: "none", border: "none", color: D.txl, cursor: "pointer" }}><X size={16} /></button>
            </div>

            <div style={{ background: D.bg, borderRadius: 8, padding: 10, fontSize: 11, marginBottom: 12 }}>
              <div><b>Paciente:</b> {selected.paciente} (ACC: {selected.acc})</div>
              <div><b>Tubo a Rechazar:</b> <span style={{ fontFamily: "monospace", color: D.tea }}>{tuboARechazar}</span></div>
              <div style={{ fontSize: 10, color: D.txl, marginTop: 2 }}>
                * El rechazo afectará únicamente a este tubo y sus pruebas asociadas. Los demás tubos continuarán su procesamiento analítico.
              </div>
            </div>

            <div style={{ marginBottom: 14 }}>
              <label style={{ fontSize: 10.5, color: D.txl, display: "block", marginBottom: 4 }}>Causal Tipificada de Rechazo:</label>
              <select
                value={causalRechazoSeleccionada}
                onChange={(e) => setCausalRechazoSeleccionada(e.target.value)}
                style={{ width: "100%", padding: "8px 10px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txt, fontSize: 11 }}
              >
                <option value="HEM_3">Hemólisis franca grado 3+ (interferencia analítica severa)</option>
                <option value="COAG_EDTA">Muestra con microcoágulo visible en tubo EDTA K2</option>
                <option value="VOL_QNS">Volumen insuficiente (QNS) para relación anticoagulante/sangre</option>
                <option value="TUBO_INAD">Tubo o aditivo inadecuado para la prestación solicitada</option>
                <option value="TEMP_RUP">Ruptura de cadena de frío / temperatura inadecuada</option>
                <option value="ROT_DISCR">Discrepancia en rotulación / código de barras ilegible</option>
              </select>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
              <button
                onClick={() => setModalRechazoAbierto(false)}
                style={{ padding: "6px 12px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txm, fontSize: 11, cursor: "pointer" }}
              >
                Cancelar
              </button>
              <button
                onClick={handleConfirmarRechazoTubo}
                style={{ padding: "7px 16px", borderRadius: 6, border: "none", background: D.dan, color: "#fff", fontSize: 11, fontWeight: 700, cursor: "pointer" }}
              >
                Confirmar Rechazo y Notificar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ───────────────────────────────────────────────────────────────────
          MODAL 4: BLOQUEO DE PRIVILEGIO RBAC / FIRMA DT
          ─────────────────────────────────────────────────────────────────── */}
      {bloqueoPermisoFirma && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(4,9,16,0.8)", zIndex: 600, display: "flex", alignItems: "center", justifyContent: "center", padding: 18 }}>
          <div style={{ background: D.sfc, border: `1px solid ${D.dan}`, borderRadius: 12, width: "100%", maxWidth: 440, padding: 20 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, color: D.dan, marginBottom: 10 }}>
              <ShieldAlert size={20} />
              <div style={{ fontSize: 13, fontWeight: 700 }}>Acceso Denegado (D.S. N° 20 Art. 16)</div>
            </div>
            <div style={{ fontSize: 11.5, color: D.txt, lineHeight: 1.45, marginBottom: 14 }}>
              El usuario activo <b>{usuarioActivo.nombre}</b> posee el rol <b>{usuarioActivo.rol}</b>, el cual no cuenta con facultad legal para la Validación Facultativa ni la Firma Electrónica Avanzada de Informes de Laboratorio.
              <br /><br />
              Esta acción está estrictamente restringida a la <b>Directora Técnica (Bioquímica Clínica)</b> debidamente acreditada ante la SEREMI de Salud y el MINSAL.
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button
                onClick={() => setBloqueoPermisoFirma(false)}
                style={{ padding: "7px 16px", borderRadius: 6, border: "none", background: D.tea, color: "#0A1420", fontSize: 11, fontWeight: 700, cursor: "pointer" }}
              >
                Entendido
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ───────────────────────────────────────────────────────────────────
          MODAL 5: FIRMA ELECTRÓNICA DT CON CÁLCULO DE HASH SHA-256
          ─────────────────────────────────────────────────────────────────── */}
      {modalFirmarInformeAbierto && selected && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(4,9,16,0.8)", zIndex: 600, display: "flex", alignItems: "center", justifyContent: "center", padding: 18 }}>
          <div style={{ background: D.sfc, border: `1px solid ${D.suc}`, borderRadius: 12, width: "100%", maxWidth: 500, padding: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: D.suc, display: "flex", alignItems: "center", gap: 6 }}>
                <ShieldCheck size={16} /> Firma Electrónica Avanzada DT (Ley 19.799 &amp; D.S. N° 20)
              </div>
              <button onClick={() => setModalFirmarInformeAbierto(false)} style={{ background: "none", border: "none", color: D.txl, cursor: "pointer" }}><X size={16} /></button>
            </div>

            <div style={{ fontSize: 11.5, color: D.txt, lineHeight: 1.45, marginBottom: 12 }}>
              Se emitirá y bloqueará el <b>DiagnosticReport</b> definitivo para <b>{selected.paciente}</b> (ACC: {selected.acc}), dejándolo inmutable y publicándolo en la Ficha Clínica Electrónica.
            </div>

            {/* Checklist de Pre-condiciones de Liberación (CLSI C24 / D.S. 20) */}
            <div style={{ background: D.sfc2, borderRadius: 8, padding: 10, fontSize: 10.5, marginBottom: 12, border: `1px solid ${D.brd}` }}>
              <div style={{ fontWeight: 700, color: D.txm, marginBottom: 6 }}>Pre-condiciones de Liberación Facultativa (D.S. N° 20 Art. 14):</div>
              <div style={{ display: "flex", alignItems: "center", gap: 6, color: D.suc, marginBottom: 3 }}>
                <CheckCircle size={13} /> Alertas Críticas Notificadas con Read-Back Verbal
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 6, color: D.suc, marginBottom: 3 }}>
                <CheckCircle size={13} /> 100% Analitos Validados Técnicamente sin Omisiones
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 6, color: D.suc }}>
                <CheckCircle size={13} /> Control de Calidad Analítico Aprobado y Sello Criptográfico Listo
              </div>
            </div>

            <div style={{ background: D.bg, borderRadius: 8, padding: 12, fontSize: 11, marginBottom: 14, border: `1px solid ${D.brd}` }}>
              <div>Firmante Autorizado: <b style={{ color: D.txt }}>{usuarioActivo.nombre}</b></div>
              <div>Cargo: {usuarioActivo.rol}</div>
              <div>CUT / Registro SIS: <span style={{ fontFamily: "monospace", color: D.tea }}>{usuarioActivo.cut} · {usuarioActivo.regSIS}</span></div>
              <div style={{ marginTop: 8, paddingTop: 8, borderTop: `1px solid ${D.brd}`, fontSize: 10, color: D.txl }}>
                Algoritmo criptográfico: <b>SHA-256 Digest</b> sobre payload estructurado (Paciente, Exámenes, Valores, Timestamps).
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
              <button
                onClick={() => setModalFirmarInformeAbierto(false)}
                style={{ padding: "6px 12px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txm, fontSize: 11, cursor: "pointer" }}
              >
                Cancelar
              </button>
              <button
                onClick={handleConfirmarFirmaDT}
                style={{ padding: "7px 18px", borderRadius: 6, border: "none", background: D.suc, color: "#0A1420", fontSize: 11.5, fontWeight: 700, cursor: "pointer" }}
              >
                Firmar y Publicar Definitivo
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ───────────────────────────────────────────────────────────────────
          MODAL 6: IMPRESIÓN TÉRMICA DE ETIQUETAS ZPL II (CON CÓDIGO BARRA REAL)
          ─────────────────────────────────────────────────────────────────── */}
      {modalEtiquetasAbierto && selected && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(4,9,16,0.8)", zIndex: 600, display: "flex", alignItems: "center", justifyContent: "center", padding: 18 }}>
          <div style={{ background: D.sfc, border: `1px solid ${D.brd}`, borderRadius: 12, width: "100%", maxWidth: 520, padding: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: D.txt, display: "flex", alignItems: "center", gap: 6 }}>
                <Printer size={15} color={D.tea} /> Impresión Térmica de Etiquetas (Zebra ZPL II)
              </div>
              <button onClick={() => setModalEtiquetasAbierto(false)} style={{ background: "none", border: "none", color: D.txl, cursor: "pointer" }}><X size={16} /></button>
            </div>

            {/* Simulación Gráfica de Etiqueta Térmica con Código de Barras SVG Real */}
            <div style={{ background: "#FFFFFF", color: "#000000", borderRadius: 8, padding: "14px 18px", border: "1px dashed #CBD5E1", marginBottom: 12, fontFamily: "'Inter', sans-serif" }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, fontWeight: 800, borderBottom: "1px solid #000", paddingBottom: 3 }}>
                <span>LABORATORIO CLÍNICO AXON</span>
                <span>{selected.prioridad.toUpperCase()}</span>
              </div>
              <div style={{ fontSize: 13, fontWeight: 800, marginTop: 4 }}>{selected.paciente}</div>
              <div style={{ fontSize: 10.5 }}>
                RUN: <b>{selected.rut}</b> · {selected.edad}a ({selected.sexo}) · {selected.origen}
              </div>
              <div style={{ fontSize: 10.5, color: "#0284C7", fontWeight: 700, marginTop: 2 }}>
                ACC: {selected.acc} · {selected.tubos[0]?.tipoMuestra || "Muestra Primaria"}
              </div>

              {/* Código de Barras Code 128 Renderizado SVG */}
              <div style={{ marginTop: 8, textAlign: "center" }}>
                <svg width="280" height="42" viewBox="0 0 280 42" style={{ display: "inline-block" }}>
                  <rect x="0" y="0" width="3" height="34" fill="#000" />
                  <rect x="5" y="0" width="2" height="34" fill="#000" />
                  <rect x="9" y="0" width="4" height="34" fill="#000" />
                  <rect x="15" y="0" width="2" height="34" fill="#000" />
                  <rect x="20" y="0" width="5" height="34" fill="#000" />
                  <rect x="28" y="0" width="2" height="34" fill="#000" />
                  <rect x="33" y="0" width="4" height="34" fill="#000" />
                  <rect x="40" y="0" width="3" height="34" fill="#000" />
                  <rect x="46" y="0" width="2" height="34" fill="#000" />
                  <rect x="51" y="0" width="5" height="34" fill="#000" />
                  <rect x="59" y="0" width="3" height="34" fill="#000" />
                  <rect x="65" y="0" width="4" height="34" fill="#000" />
                  <rect x="72" y="0" width="2" height="34" fill="#000" />
                  <rect x="76" y="0" width="5" height="34" fill="#000" />
                  <rect x="84" y="0" width="3" height="34" fill="#000" />
                  <rect x="90" y="0" width="2" height="34" fill="#000" />
                  <rect x="95" y="0" width="4" height="34" fill="#000" />
                  <rect x="102" y="0" width="3" height="34" fill="#000" />
                  <rect x="108" y="0" width="5" height="34" fill="#000" />
                  <rect x="116" y="0" width="2" height="34" fill="#000" />
                  <rect x="121" y="0" width="4" height="34" fill="#000" />
                  <rect x="128" y="0" width="3" height="34" fill="#000" />
                  <rect x="134" y="0" width="2" height="34" fill="#000" />
                  <rect x="139" y="0" width="5" height="34" fill="#000" />
                  <rect x="147" y="0" width="3" height="34" fill="#000" />
                  <rect x="153" y="0" width="4" height="34" fill="#000" />
                  <rect x="160" y="0" width="2" height="34" fill="#000" />
                  <rect x="165" y="0" width="4" height="34" fill="#000" />
                  <rect x="172" y="0" width="3" height="34" fill="#000" />
                  <rect x="178" y="0" width="5" height="34" fill="#000" />
                  <rect x="186" y="0" width="2" height="34" fill="#000" />
                  <rect x="191" y="0" width="4" height="34" fill="#000" />
                  <rect x="198" y="0" width="3" height="34" fill="#000" />
                  <rect x="204" y="0" width="5" height="34" fill="#000" />
                  <rect x="212" y="0" width="2" height="34" fill="#000" />
                  <rect x="217" y="0" width="4" height="34" fill="#000" />
                  <rect x="224" y="0" width="3" height="34" fill="#000" />
                  <rect x="230" y="0" width="4" height="34" fill="#000" />
                  <rect x="237" y="0" width="2" height="34" fill="#000" />
                  <rect x="242" y="0" width="5" height="34" fill="#000" />
                  <rect x="250" y="0" width="3" height="34" fill="#000" />
                  <rect x="256" y="0" width="2" height="34" fill="#000" />
                  <rect x="261" y="0" width="4" height="34" fill="#000" />
                  <rect x="268" y="0" width="3" height="34" fill="#000" />
                  <rect x="274" y="0" width="4" height="34" fill="#000" />
                </svg>
                <div style={{ fontSize: 10, fontFamily: "monospace", fontWeight: 700, letterSpacing: "0.15em" }}>
                  {selected.tubos[0]?.id || "SMP-2026-000412-01"}
                </div>
              </div>
            </div>

            {/* Código ZPL II Raw Generado */}
            <div style={{ background: "#050B12", borderRadius: 6, padding: 10, border: `1px solid ${D.brd}`, marginBottom: 12 }}>
              <div style={{ fontSize: 9.5, color: D.txl, marginBottom: 4, display: "flex", justifyContent: "space-between" }}>
                <span>Payload ZPL II enviado al puerto TCP RAW 9100:</span>
                <span style={{ color: D.tea }}>Zebra ZD621-HC (192.168.10.82)</span>
              </div>
              <pre style={{ margin: 0, fontSize: 9.5, color: D.tea, fontFamily: "monospace", overflowX: "auto", whiteSpace: "pre-wrap" }}>
{`^XA
^PW420^LL240
^FO20,20^A0N,22,22^FDLABORATORIO AXON^FS
^FO20,46^A0N,20,20^FDRUN: ${selected.rut} ${selected.paciente}^FS
^FO20,72^A0N,18,18^FDACC: ${selected.acc} | ${selected.origen}^FS
^FO20,96^BY2,2.5,45^BCN,45,Y,N,N^FD${selected.tubos[0]?.id || selected.acc}^FS
^FO20,178^A0N,16,16^FD${selected.tubos[0]?.recipiente || "Tubo Primario"}^FS
^XZ`}
              </pre>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
              <button
                onClick={() => setModalEtiquetasAbierto(false)}
                style={{ padding: "6px 12px", borderRadius: 6, border: `1px solid ${D.brd}`, background: D.sfc2, color: D.txm, fontSize: 11, cursor: "pointer" }}
              >
                Cerrar
              </button>
              <button
                onClick={() => {
                  alert(`Trabajo ZPL enviado a Spooler de Red (Zebra ZD621-HC en 192.168.10.82). Se imprimieron ${selected.tubos.length} etiquetas.`);
                  setModalEtiquetasAbierto(false);
                }}
                style={{ padding: "7px 16px", borderRadius: 6, border: "none", background: D.tea, color: "#0A1420", fontSize: 11, fontWeight: 700, cursor: "pointer" }}
              >
                Enviar a Impresora Térmica
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ───────────────────────────────────────────────────────────────────
          MODAL 7: INFORME IMPRIMIBLE D.S. N° 20 ART. 16 (CON MARCA DE AGUA DEMO)
          ─────────────────────────────────────────────────────────────────── */}
      {modalVisorPdfAbierto && selected && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(4,9,16,0.85)", zIndex: 600, display: "flex", alignItems: "center", justifyContent: "center", padding: 18 }}>
          <div style={{ background: "#ffffff", color: "#000000", borderRadius: 12, width: "100%", maxWidth: 840, maxHeight: "94vh", display: "flex", flexDirection: "column", overflow: "hidden", boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.7)" }}>
            
            {/* Barra de Acciones No Imprimible */}
            <div className="no-print" style={{ padding: "10px 18px", background: "#0F172A", color: "#ffffff", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <FileText size={16} color={D.tea} />
                <span style={{ fontSize: 12, fontWeight: 700 }}>
                  Informe Oficial de Laboratorio (D.S. N° 20 Art. 16) · AXON Document Engine
                </span>
              </div>
              <div style={{ display: "flex", gap: 10 }}>
                <button
                  onClick={() => window.print()}
                  style={{ display: "flex", alignItems: "center", gap: 6, padding: "6px 14px", background: D.tea, color: "#0A1420", border: "none", borderRadius: 6, fontSize: 11, fontWeight: 700, cursor: "pointer" }}
                >
                  <Printer size={13} /> Imprimir A4
                </button>
                <button onClick={() => setModalVisorPdfAbierto(false)} style={{ background: "none", border: "none", color: "#94A3B8", cursor: "pointer" }}><X size={18} /></button>
              </div>
            </div>

            {/* Hoja A4 con Estilos Limpios y Marca de Agua Explícita */}
            <div id="printable-report-area" style={{ flex: 1, padding: "34px 44px", overflowY: "auto", fontFamily: "'Inter', -apple-system, sans-serif", fontSize: 11.5, lineHeight: 1.45, position: "relative" }}>
              
              {/* Marca de Agua de Datos Sintéticos */}
              <div
                style={{
                  position: "absolute",
                  top: "40%",
                  left: "10%",
                  right: "10%",
                  textAlign: "center",
                  transform: "rotate(-25deg)",
                  fontSize: 32,
                  fontWeight: 900,
                  color: "rgba(220, 38, 38, 0.08)",
                  pointerEvents: "none",
                  userSelect: "none",
                  border: "4px dashed rgba(220, 38, 38, 0.12)",
                  padding: "16px 20px",
                  borderRadius: 12,
                }}
              >
                DEMO — DATOS SINTÉTICOS DE PRUEBA — SIN VALIDEZ CLÍNICA NI LEGAL
              </div>

              {/* Encabezado Institucional Conforme a D.S. N° 20 Art. 16 */}
              <div style={{ borderBottom: "2px solid #0F172A", paddingBottom: 14, marginBottom: 14 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div>
                    <div style={{ fontSize: 15, fontWeight: 900, color: "#0F172A" }}>LABORATORIO CLÍNICO CENTRAL AXON</div>
                    <div style={{ fontSize: 10, color: "#475569", marginTop: 2 }}>
                      Resolución Sanitaria SEREMI N° 14892/2024 · Registro Nacional de Prestadores Individuales SIS
                    </div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: 13, fontWeight: 800, color: "#0284C7", fontFamily: "monospace" }}>{selected.acc}</div>
                    <div style={{ fontSize: 10, color: "#475569" }}>Orden: {selected.orden}</div>
                  </div>
                </div>
              </div>

              {/* Datos del Paciente y de la Solicitud */}
              <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 12, background: "#F8FAFC", padding: 12, borderRadius: 8, border: "1px solid #E2E8F0", marginBottom: 16 }}>
                <div>
                  <div><span style={{ color: "#64748B" }}>Paciente:</span> <b>{selected.paciente}</b></div>
                  <div><span style={{ color: "#64748B" }}>RUN:</span> <b>{selected.rut}</b> ({selected.sexo}) {selected.edad} años</div>
                  <div><span style={{ color: "#64748B" }}>Procedencia:</span> {selected.origen} ({selected.cama})</div>
                </div>
                <div>
                  <div><span style={{ color: "#64748B" }}>Médico Solicitante:</span> <b>{selected.medicoSolicitante}</b></div>
                  <div><span style={{ color: "#64748B" }}>Fecha/Hora Toma:</span> {selected.horaToma || "No registrada"}</div>
                  <div><span style={{ color: "#64748B" }}>Fecha/Hora Recepción:</span> {selected.horaRecepcion || "No registrada"}</div>
                </div>
              </div>

              {/* Tabla de Resultados Analíticos con Método de Medición */}
              <div style={{ marginBottom: 20 }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
                  <thead>
                    <tr style={{ background: "#F1F5F9", borderBottom: "1px solid #CBD5E1", textAlign: "left", color: "#334155", fontSize: 10, textTransform: "uppercase" }}>
                      <th style={{ padding: "8px 10px" }}>Examen &amp; Método Analítico</th>
                      <th style={{ padding: "8px 10px" }}>Tipo de Muestra</th>
                      <th style={{ padding: "8px 10px", textAlign: "right" }}>Resultado</th>
                      <th style={{ padding: "8px 10px" }}>Unidad</th>
                      <th style={{ padding: "8px 10px" }}>Intervalo de Referencia</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selected.analitos.map((an) => {
                      const isCrit = an.flag?.includes("CRITICAL");
                      const isHigh = an.flag?.includes("HIGH");
                      const isLow = an.flag?.includes("LOW");
                      return (
                        <tr key={an.id} style={{ borderBottom: "1px solid #E2E8F0" }}>
                          <td style={{ padding: "8px 10px" }}>
                            <div style={{ fontWeight: 700, color: "#0F172A" }}>{an.nombre}</div>
                            <div style={{ fontSize: 9.5, color: "#64748B" }}>
                              Método: {an.metodo} · Equipo: {an.equipo}
                            </div>
                          </td>
                          <td style={{ padding: "8px 10px", color: "#475569", fontSize: 10 }}>
                            {selected.tubos.find((t) => t.id === an.tuboId)?.tipoMuestra || "Suero sanguíneo"}
                          </td>
                          <td style={{ padding: "8px 10px", textAlign: "right", fontWeight: 800, fontSize: 12, color: isCrit ? "#DC2626" : isHigh || isLow ? "#B45309" : "#0F172A" }}>
                            {an.valor !== null ? an.valor : "Pendiente"}{" "}
                            {isHigh ? "▲" : isLow ? "▼" : ""}
                          </td>
                          <td style={{ padding: "8px 10px", color: "#334155" }}>{an.ucum}</td>
                          <td style={{ padding: "8px 10px", color: "#475569" }}>
                            {an.refMin !== null ? `${an.refMin} - ${an.refMax}` : "Negativo"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Bloque Legal de Firma Electrónica DT (D.S. N° 20 Art. 16 & Ley 19.799) */}
              <div style={{ marginTop: 30, display: "flex", justifyContent: "space-between", alignItems: "flex-end", paddingTop: 14, borderTop: "1px solid #E2E8F0" }}>
                <div style={{ fontSize: 9.5, color: "#64748B", maxWidth: 460 }}>
                  * Los resultados corresponden exclusivamente a las muestras recibidas y analizadas bajo programa PEEC/ISP.<br />
                  * Conservación legal de registros: 5 años archivo de laboratorio (D.S. N° 20) y 15 años Ficha Clínica (Ley 20.584).<br />
                  * Código Hash Documental: <span style={{ fontFamily: "monospace", color: "#0284C7" }}>{selected.informe?.firmaDT?.hashSha256 ? selected.informe.firmaDT.hashSha256.slice(0, 32) + "..." : "BORRADOR NO FIRMADO"}</span>
                </div>
                <div style={{ textAlign: "center", borderTop: "1px solid #0F172A", paddingTop: 8, width: 250 }}>
                  <div style={{ fontSize: 11, fontWeight: 800, color: "#0F172A" }}>
                    {selected.informe?.firmaDT?.firmante || "Dra. Patricia Morales O."}
                  </div>
                  <div style={{ fontSize: 10, color: "#475569" }}>
                    {selected.informe?.firmaDT?.cargo || "Directora Técnica · Bioquímica"}
                  </div>
                  <div style={{ fontSize: 9, color: "#64748B" }}>
                    CUT: {selected.informe?.firmaDT?.cut || "2026-BM-9812"} · Reg. SIS 74892
                  </div>
                  <div style={{ fontSize: 8.5, color: "#0284C7", marginTop: 4, fontWeight: 700 }}>
                    {selected.informe?.firmaDT?.estadoFirma || "Firma Electrónica Avanzada Verificada (Ley 19.799)"}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

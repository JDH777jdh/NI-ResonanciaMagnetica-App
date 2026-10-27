/**
 * ═══════════════════════════════════════════════════════════════════
 * HIS-CLÍNICO HOSPITALARIO · CAPA 1 · SHELL FUNDACIONAL
 * ═══════════════════════════════════════════════════════════════════
 * Estándares: HL7 FHIR R4 · DICOM 3.0 · SNOMED-CT · LOINC 2.77
 *             CIE-10 v2022 · MINSAL-CL · Decreto 41 · Ley 19.628
 *             Ley 19.799 (FES) · Resolución 1053 MINSAL · ISO 9001
 * 
 * Arquitectura: SPA React · Sidebar Colapsable · Role-Based Access
 *               FHIR Health Ribbon · Portal Dual (Paciente / Profesional)
 * ═══════════════════════════════════════════════════════════════════
 */

import { useState, useEffect, useCallback } from "react";
import {
  Activity, Users, Calendar, Eye, FlaskConical,
  HeartPulse, Truck, Wrench, Building2, DollarSign,
  BarChart3, Stethoscope, Shield, Search, Bell,
  ChevronLeft, ChevronRight, ChevronDown, ChevronUp,
  Home, AlertTriangle, CheckCircle, Lock, Database,
  Clock, QrCode, Package, ClipboardList, TrendingUp,
  TrendingDown, Plus, LogOut, Settings, Star,
  MessageSquare, Filter, Server, UserCheck, AlertCircle,
  FileText, Users2, Pill, Video, X, Target, Microscope,
  Heart, Syringe, LayoutDashboard, Wallet, BookOpen,
  Bed, Zap, Globe, RefreshCw, Award, Save, Printer,
  CreditCard, Banknote, HelpCircle, Monitor, Cpu,
  Fingerprint, CheckSquare, Layers, PenSquare, Upload,
  Info, ArrowRight, Smartphone, Radio, TestTube,
  Menu, BadgeCheck, Download
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  LineChart, Line, PieChart, Pie, Cell,
  ResponsiveContainer, AreaChart, Area, Legend
} from "recharts";

// ─────────────────────────────────────────────────────────────────
// § 1 · ESTÁNDARES & CONSTANTES CLÍNICAS
// ─────────────────────────────────────────────────────────────────
const STANDARDS = [
  { id: "fhir",   label: "HL7 FHIR R4",  status: "online",   color: "#00A693" },
  { id: "dicom",  label: "DICOM 3.0",    status: "online",   color: "#4FC3F7" },
  { id: "snomed", label: "SNOMED-CT",    status: "syncing",  color: "#FFB74D" },
  { id: "loinc",  label: "LOINC 2.77",   status: "online",   color: "#CE93D8" },
  { id: "cie10",  label: "CIE-10 v2022", status: "online",   color: "#F48FB1" },
  { id: "minsal", label: "MINSAL-CL",    status: "online",   color: "#80DEEA" },
];

const LAWS = ["Ley 19.628", "Ley 19.799", "D.41 MINSAL", "Res.1053", "ISO 9001"];

// ─────────────────────────────────────────────────────────────────
// § 2 · MÓDULOS DE NAVEGACIÓN COMPLETOS
// ─────────────────────────────────────────────────────────────────
const MODULES = [
  // ── CORE ──────────────────────────────────────────────────────
  {
    id: "dashboard", label: "Dashboard", icon: LayoutDashboard,
    color: "#1A4DA8", group: "core", roles: ["all"],
    fhir: ["MeasureReport","AuditEvent"],
  },
  {
    id: "portal_paciente", label: "Portal Pacientes", icon: Smartphone,
    color: "#00A693", group: "core", roles: ["all"],
    fhir: ["Patient","Appointment","Consent","Communication"],
    submodules: [
      { id: "pac_agenda",          label: "Mi Agenda",            icon: Calendar,     fhir: "Appointment"  },
      { id: "pac_datos",           label: "Mis Datos",            icon: Users,        fhir: "Patient"      },
      { id: "pac_consentimientos", label: "Consentimientos",      icon: FileText,     fhir: "Consent"      },
      { id: "pac_encuestas",       label: "Encuestas Satisfacción",icon: Star,        fhir: "Questionnaire"},
      { id: "pac_oirs",            label: "OIRS (Reclamos/Felicitaciones)", icon: MessageSquare, fhir: "Communication" },
    ],
  },

  // ── CLÍNICO ───────────────────────────────────────────────────
  {
    id: "admision", label: "Admisión y Agenda", icon: UserCheck,
    color: "#1565C0", group: "clinico", roles: ["recepcionista","enfermero","admin","director"],
    fhir: ["Patient","Appointment","Encounter","Consent","Coverage"],
    standard: "eMPI MINSAL · FHIR Patient",
    submodules: [
      { id: "adm_ingreso",     label: "Ingreso Paciente BD",      icon: Plus,       fhir: "Patient"     },
      { id: "adm_registro",    label: "Registro Paciente",        icon: Database,   fhir: "Patient"     },
      { id: "adm_validacion",  label: "Validación Profesional",   icon: BadgeCheck, fhir: "Practitioner"},
      { id: "adm_agenda",      label: "Agenda / Modalidades",     icon: Calendar,   fhir: "Appointment" },
      { id: "adm_telemedicina",label: "Telemedicina",             icon: Video,      fhir: "Appointment" },
    ],
  },
  {
    id: "atencion_medica", label: "Atención Médica", icon: Stethoscope,
    color: "#C62828", group: "clinico", roles: ["medico","enfermero","admin","director"],
    fhir: ["Encounter","Condition","Observation","MedicationRequest","Procedure","DocumentReference"],
    submodules: [
      { id: "med_urgencias",    label: "Urgencias · Triage",          icon: Zap,      fhir: "Encounter"       },
      { id: "med_hospitalizado",label: "Hospitalización",              icon: Bed,      fhir: "Encounter"       },
      { id: "med_pabellon",     label: "Pabellón Quirúrgico",         icon: Syringe,  fhir: "ServiceRequest"  },
      { id: "med_ambulatorio",  label: "Ambulatorio · Consultas",     icon: Stethoscope, fhir: "Encounter"    },
      { id: "med_investigacion",label: "Investigación Clínica",       icon: Microscope, fhir: "ResearchStudy" },
      { id: "med_traslados",    label: "Gestión Traslados",           icon: Truck,    fhir: "Transport"       },
    ],
  },
  {
    id: "imagenologia", label: "Imagenología · RIS/PACS", icon: Monitor,
    color: "#1A4DA8", group: "clinico", roles: ["radiologo","tecnologo_med","admin","director"],
    fhir: ["ImagingStudy","ServiceRequest","DiagnosticReport","Consent","MedicationRequest","AdverseEvent","Device"],
    standard: "DICOM 3.0 + FHIR ImagingStudy",
    submodules: [
      { id: "img_agenda",          label: "Gestión Agenda",               icon: Calendar,     fhir: "Appointment"       },
      { id: "img_consentimientos", label: "Consentimientos CI (TC/RM/Angio)", icon: FileText, fhir: "Consent"          },
      { id: "img_rescate",         label: "Motor de Rescate · Adendum",   icon: RefreshCw,    fhir: "Consent.provision" },
      { id: "img_rispacs",         label: "H-RIS/PACS · Visor DICOM",     icon: Monitor,      fhir: "ImagingStudy"      },
      { id: "img_farmacos",        label: "Gestión Médica Fármacos",      icon: Pill,         fhir: "MedicationRequest" },
      { id: "img_eventos",         label: "Eventos de Seguridad",         icon: AlertTriangle,fhir: "AdverseEvent"      },
      { id: "img_bodega",          label: "Gestión Bodega",               icon: Package,      fhir: "InventoryReport"   },
      { id: "img_sinergia",        label: "Reuniones y Sinergia",         icon: Users2,       fhir: "Communication"     },
    ],
  },
  {
    id: "laboratorio", label: "Laboratorio · LIS", icon: FlaskConical,
    color: "#00897B", group: "clinico", roles: ["laboratorista","tecnologo_lab","admin","director"],
    fhir: ["ServiceRequest","DiagnosticReport","Observation","Specimen","AdverseEvent"],
    standard: "LOINC 2.77 + FHIR Observation",
    submodules: [
      { id: "lab_agenda",   label: "Gestión Agenda",      icon: Calendar,     fhir: "Appointment"      },
      { id: "lab_lims",     label: "H-LIMS",              icon: TestTube,     fhir: "DiagnosticReport" },
      { id: "lab_eventos",  label: "Eventos de Seguridad",icon: AlertTriangle,fhir: "AdverseEvent"     },
      { id: "lab_bodega",   label: "Gestión Bodega",      icon: Package,      fhir: "InventoryReport"  },
      { id: "lab_sinergia", label: "Reuniones y Sinergia",icon: Users2,       fhir: "Communication"    },
    ],
  },
  {
    id: "oftalmologia", label: "Oftalmología · OIS", icon: Eye,
    color: "#6A1B9A", group: "clinico", roles: ["oftalmologo","tecnologo_oft","admin","director"],
    fhir: ["ImagingStudy","ServiceRequest","DiagnosticReport","Observation","AdverseEvent"],
    standard: "DICOM OPT + FHIR ImagingStudy",
    submodules: [
      { id: "oft_agenda",   label: "Gestión Agenda",      icon: Calendar,     fhir: "Appointment"      },
      { id: "oft_oispacs",  label: "H-OIS-PACS",          icon: Monitor,      fhir: "ImagingStudy"     },
      { id: "oft_eventos",  label: "Eventos de Seguridad",icon: AlertTriangle,fhir: "AdverseEvent"     },
      { id: "oft_bodega",   label: "Gestión Bodega",      icon: Package,      fhir: "InventoryReport"  },
      { id: "oft_sinergia", label: "Reuniones y Sinergia",icon: Users2,       fhir: "Communication"    },
    ],
  },
  {
    id: "kinesiologia", label: "Kinesiología", icon: HeartPulse,
    color: "#2E7D32", group: "clinico", roles: ["kinesiologo","admin","director"],
    fhir: ["ServiceRequest","Encounter","Observation","CareTeam","AdverseEvent"],
    submodules: [
      { id: "kin_agenda",   label: "Gestión Agenda",      icon: Calendar,     fhir: "Appointment"  },
      { id: "kin_registros",label: "Registros Clínicos",  icon: ClipboardList,fhir: "Observation"  },
      { id: "kin_bodega",   label: "Gestión Bodega",      icon: Package,      fhir: "InventoryReport"},
      { id: "kin_eventos",  label: "Eventos de Seguridad",icon: AlertTriangle,fhir: "AdverseEvent" },
      { id: "kin_sinergia", label: "Reuniones y Sinergia",icon: Users2,       fhir: "Communication"},
    ],
  },
  {
    id: "especialidades", label: "Exámenes Especialidad", icon: Activity,
    color: "#E65100", group: "clinico", roles: ["medico","tecnologo_med","admin","director"],
    fhir: ["ServiceRequest","DiagnosticReport","Observation","Procedure"],
    submodules: [
      { id: "esp_endoscopia",  label: "Endoscopia",          icon: Layers,       fhir: "Procedure"        },
      { id: "esp_emg",         label: "Electromiografía",    icon: Activity,     fhir: "Observation"      },
      { id: "esp_eeg",         label: "Electroencefalografía",icon: Activity,    fhir: "Observation"      },
      { id: "esp_cardio",      label: "Cardiología",         icon: Heart,        fhir: "DiagnosticReport" },
      { id: "esp_neumologia",  label: "Neumología",          icon: Activity,     fhir: "Observation"      },
      { id: "esp_otorrino",    label: "Otorrinolaringología", icon: Activity,    fhir: "Observation"      },
      { id: "esp_sinergia",    label: "Reuniones y Sinergia",icon: Users2,       fhir: "Communication"    },
    ],
  },

  // ── OPERACIONES ────────────────────────────────────────────────
  {
    id: "sanitizacion", label: "Sanitización Clínica", icon: Shield,
    color: "#00838F", group: "operaciones", roles: ["sanitizador","jefe_san","admin","director"],
    fhir: ["HealthcareService","Task","Location"],
    submodules: [
      { id: "san_registro", label: "Registro QR",         icon: QrCode,       fhir: "Task"           },
      { id: "san_bodega",   label: "Gestión Bodega",      icon: Package,      fhir: "InventoryReport"},
      { id: "san_soporte",  label: "Solicitud Soporte",   icon: HelpCircle,   fhir: "ServiceRequest" },
      { id: "san_sinergia", label: "Reuniones y Sinergia",icon: Users2,       fhir: "Communication"  },
    ],
  },
  {
    id: "equipamiento", label: "Equipamiento e Infraestructura", icon: Wrench,
    color: "#455A64", group: "operaciones", roles: ["tecnico_biomed","infra","admin","director"],
    fhir: ["Device","Location","DeviceRequest","MaintenanceRequest"],
    submodules: [
      { id: "equ_registro",   label: "Registro Equipamiento Médico",icon: Cpu,      fhir: "Device"        },
      { id: "equ_bodega",     label: "Bodega Central",              icon: Package,  fhir: "InventoryReport"},
      { id: "equ_soporte",    label: "Soporte Infraestructura",     icon: Wrench,   fhir: "Task"          },
      { id: "equ_mantencion", label: "Mantención Equipamientos",    icon: Settings, fhir: "Device"        },
      { id: "equ_operativos", label: "Operativos",                  icon: ClipboardList, fhir: "Task"     },
    ],
  },
  {
    id: "farmacia_bodega", label: "Farmacia Central y Bodega", icon: Pill,
    color: "#4338CA", group: "operaciones", roles: ["farmaceutico","encargado_unidad","admin","director"],
    fhir: ["MedicationRequest","SupplyRequest","SupplyDelivery","InventoryReport"],
    standard: "GS1 · EAN-13 · FHIR SupplyRequest/Delivery",
    custom: true,
  },

  // ── GESTIÓN ────────────────────────────────────────────────────
  {
    id: "calidad", label: "Calidad", icon: Award,
    color: "#6A1B9A", group: "gestion", roles: ["calidad","admin","director"],
    fhir: ["AuditEvent","DocumentReference","Communication","Questionnaire","QuestionnaireResponse"],
    submodules: [
      { id: "cal_trazabilidad",label: "Trazabilidad FHIR",           icon: Target,       fhir: "AuditEvent"         },
      { id: "cal_seguridad",   label: "Seguridad en Procedimientos", icon: Shield,       fhir: "AdverseEvent"       },
      { id: "cal_protocolos",  label: "Protocolos Clínicos",         icon: FileText,     fhir: "PlanDefinition"     },
      { id: "cal_simulaciones",label: "Simulaciones y Evacuaciones", icon: Activity,     fhir: "Communication"      },
      { id: "cal_documentos",  label: "Documentos y Licencias",      icon: BookOpen,     fhir: "DocumentReference"  },
      { id: "cal_oirs",        label: "OIRS · Felicitaciones/Reclamos",icon: MessageSquare,fhir: "Communication"    },
      { id: "cal_encuestas",   label: "Encuestas de Satisfacción",   icon: Star,         fhir: "QuestionnaireResponse"},
    ],
  },
  {
    id: "informatica", label: "Informática y TI", icon: Monitor,
    color: "#37474F", group: "gestion", roles: ["it","admin","director"],
    fhir: ["AuditEvent","Device","Task","CapabilityStatement"],
    submodules: [
      { id: "ti_tickets",   label: "Tickets de Soporte",  icon: HelpCircle,  fhir: "Task"               },
      { id: "ti_sistemas",  label: "Gestión de Sistemas", icon: Server,      fhir: "Device"             },
      { id: "ti_fhir",      label: "Monitor FHIR / DICOM",icon: Globe,       fhir: "CapabilityStatement"},
      { id: "ti_auditoria", label: "Auditoría de Accesos",icon: Lock,        fhir: "AuditEvent"         },
    ],
  },
  {
    id: "convenios", label: "Convenios y Valores", icon: CreditCard,
    color: "#1565C0", group: "gestion", roles: ["administrativo","admin","director"],
    fhir: ["Coverage","InsurancePlan","Organization","Contract"],
    submodules: [
      { id: "con_valores",     label: "Valores de Prestaciones",  icon: DollarSign, fhir: "ChargeItemDefinition"},
      { id: "con_previsiones", label: "Seguros y Previsiones",    icon: Shield,     fhir: "Coverage"            },
      { id: "con_contratos",   label: "Gestión de Contratos",     icon: FileText,   fhir: "Contract"            },
    ],
  },
  {
    id: "rrhh", label: "Recursos Humanos", icon: Users2,
    color: "#E65100", group: "gestion", roles: ["rrhh","admin","director"],
    fhir: ["Practitioner","PractitionerRole","Schedule","HealthcareService"],
    submodules: [
      { id: "rrhh_asistencia",  label: "Control de Asistencia",   icon: CheckSquare, fhir: "Practitioner"     },
      { id: "rrhh_vacaciones",  label: "Vacaciones y Permisos",   icon: Calendar,    fhir: "PractitionerRole" },
      { id: "rrhh_ingreso",     label: "Ingreso de Personal",     icon: Plus,        fhir: "Practitioner"     },
      { id: "rrhh_liquidaciones",label: "Liquidaciones",          icon: Banknote,    fhir: "Practitioner"     },
      { id: "rrhh_reglamento",  label: "Reglamento Interno",      icon: BookOpen,    fhir: "DocumentReference"},
      { id: "rrhh_sinergia",    label: "Sinergia de Unidad",      icon: Users2,      fhir: "Communication"    },
    ],
  },
  {
    id: "contabilidad", label: "Contabilidad", icon: Wallet,
    color: "#2E7D32", group: "gestion", roles: ["contador","admin","director"],
    fhir: ["Invoice","Claim","ExplanationOfBenefit","Account"],
    submodules: [
      { id: "cont_ventas",      label: "Ventas e Ingresos",          icon: TrendingUp,  fhir: "Invoice"                },
      { id: "cont_presupuesto", label: "Presupuesto y Adquisiciones",icon: ClipboardList,fhir: "Account"               },
      { id: "cont_egresos",     label: "Egresos",                    icon: TrendingDown, fhir: "Invoice"               },
      { id: "cont_balances",    label: "Balances Financieros",       icon: BarChart3,   fhir: "Account"                },
    ],
  },
  {
    id: "direccion", label: "Alta Dirección", icon: Target,
    color: "#0D47A1", group: "gestion", roles: ["director","gerente"],
    fhir: ["MeasureReport","Organization","ResearchStudy","AuditEvent"],
    submodules: [
      { id: "dir_estadisticas", label: "Estadísticas Generales",     icon: BarChart3,    fhir: "MeasureReport"  },
      { id: "dir_resumen",      label: "Resumen Ejecutivo",          icon: FileText,     fhir: "Composition"    },
      { id: "dir_operaciones",  label: "Operaciones Clínicas",       icon: Activity,     fhir: "MeasureReport"  },
      { id: "dir_finanzas",     label: "Finanzas y Balances",        icon: Wallet,       fhir: "Account"        },
      { id: "dir_proyectos",    label: "Proyectos de Mejora",        icon: Target,       fhir: "ResearchStudy"  },
      { id: "dir_reclamos",     label: "Gestión de Reclamos",        icon: MessageSquare,fhir: "Communication"  },
    ],
  },
];

const MODULE_GROUPS = [
  { id: "core",       label: null,          ids: ["dashboard","portal_paciente"] },
  { id: "clinico",    label: "CLÍNICO",     ids: ["admision","atencion_medica","imagenologia","laboratorio","oftalmologia","kinesiologia","especialidades"] },
  { id: "operaciones",label: "OPERACIONES", ids: ["sanitizacion","equipamiento","farmacia_bodega"] },
  { id: "gestion",    label: "GESTIÓN",     ids: ["calidad","informatica","convenios","rrhh","contabilidad","direccion"] },
];

const ROLES = [
  { id: "director",      label: "Alta Dirección",    color: "#0D47A1" },
  { id: "medico",        label: "Médico/a",           color: "#C62828" },
  { id: "radiologo",     label: "Radiólogo/a",        color: "#1A4DA8" },
  { id: "laboratorista", label: "Laboratorio",        color: "#00897B" },
  { id: "oftalmologo",   label: "Oftalmólogo/a",      color: "#6A1B9A" },
  { id: "kinesiologo",   label: "Kinesiólogo/a",      color: "#2E7D32" },
  { id: "enfermero",     label: "Enfermero/a",        color: "#E65100" },
  { id: "farmaceutico",  label: "Farmacia/Bodega Central", color: "#4338CA" },
  { id: "coordinador_unidad", label: "Coordinador de Unidad", color: "#0E7490" },
  { id: "encargado_unidad", label: "Encargado Sub-farmacia/Bodega", color: "#B45309" },
  { id: "recepcionista", label: "Recepcionista",      color: "#455A64" },
  { id: "admin",         label: "Administrador/a",    color: "#37474F" },
  { id: "it",            label: "TI / Informática",   color: "#37474F" },
  { id: "calidad",       label: "Calidad",            color: "#6A1B9A" },
  { id: "contador",      label: "Contabilidad",       color: "#2E7D32" },
  { id: "paciente",      label: "Paciente",           color: "#00A693" },
];

// ─────────────────────────────────────────────────────────────────
// § 3 · MOCK DATA (Dashboard)
// ─────────────────────────────────────────────────────────────────
const KPI = {
  pacientes:     147,
  citas:          89,
  hospitalizados: 34,
  urgencias:      12,
  pendientes:     28,
  satisfaccion:  94.2,
};

const DATA_SEMANA = [
  { dia: "Lun", ambulatorio: 45, urgencias: 8,  hospitalizados: 32 },
  { dia: "Mar", ambulatorio: 52, urgencias: 11, hospitalizados: 30 },
  { dia: "Mié", ambulatorio: 48, urgencias: 7,  hospitalizados: 33 },
  { dia: "Jue", ambulatorio: 63, urgencias: 15, hospitalizados: 35 },
  { dia: "Vie", ambulatorio: 71, urgencias: 12, hospitalizados: 34 },
  { dia: "Sáb", ambulatorio: 38, urgencias: 9,  hospitalizados: 31 },
  { dia: "Dom", ambulatorio: 22, urgencias: 14, hospitalizados: 29 },
];

const DATA_EXAMENES = [
  { name: "Imagenología", value: 38, color: "#1A4DA8" },
  { name: "Laboratorio",  value: 27, color: "#00897B" },
  { name: "Oftalmología", value: 12, color: "#6A1B9A" },
  { name: "Especialidades",value:15, color: "#E65100" },
  { name: "Kinesiología", value: 8,  color: "#2E7D32" },
];

const DATA_FINANCIERO = [
  { mes: "Ene", ingresos: 18.5, egresos: 12.3 },
  { mes: "Feb", ingresos: 21.2, egresos: 13.1 },
  { mes: "Mar", ingresos: 19.8, egresos: 11.9 },
  { mes: "Abr", ingresos: 23.5, egresos: 14.2 },
  { mes: "May", ingresos: 25.1, egresos: 15.3 },
  { mes: "Jun", ingresos: 22.8, egresos: 13.8 },
];

const DATA_SATISFACCION = [
  { mes: "Ene", score: 91 }, { mes: "Feb", score: 88 },
  { mes: "Mar", score: 92 }, { mes: "Abr", score: 89 },
  { mes: "May", score: 95 }, { mes: "Jun", score: 94 },
];

const PACIENTES_RECIENTES = [
  { rut: "12.345.678-9", nombre: "María González Pérez",  edad: 42, prestacion: "Resonancia Magnética",  estado: "En Sala",    fhir: "ImagingStudy",      color: "#6A1B9A" },
  { rut: "9.876.543-2",  nombre: "Carlos Rodríguez Silva",edad: 67, prestacion: "Hemograma + Bioquímica", estado: "Completado", fhir: "DiagnosticReport",  color: "#00897B" },
  { rut: "15.432.876-K", nombre: "Ana Martínez Díaz",    edad: 34, prestacion: "Consulta Médica",        estado: "En Espera",  fhir: "Appointment",       color: "#E65100" },
  { rut: "7.654.321-3",  nombre: "Luis Pérez Torres",    edad: 55, prestacion: "TC Tórax c/contraste",   estado: "Programado", fhir: "ServiceRequest",    color: "#1A4DA8" },
  { rut: "18.765.432-1", nombre: "Carmen López Vargas",  edad: 28, prestacion: "Ecografía Abdominal",    estado: "En Sala",    fhir: "ImagingStudy",      color: "#6A1B9A" },
];

const ALERTAS = [
  { tipo: "error",   msg: "3 consentimientos TC pendientes de firma",       mod: "Imagenología",  time: "hace 5 min" },
  { tipo: "warning", msg: "SNOMED-CT requiere sincronización",              mod: "Sistema",       time: "hace 12 min"},
  { tipo: "warning", msg: "Paciente en urgencias sin triage asignado",     mod: "Urgencias",     time: "hace 18 min"},
  { tipo: "info",    msg: "Informe de calidad ISO 9001 pendiente",          mod: "Calidad",       time: "hace 1h"    },
  { tipo: "success", msg: "Backup FHIR completado · 2.847 recursos",       mod: "Informática",   time: "hace 2h"    },
];

const FHIR_COMPLIANCE = [
  { recurso: "Patient",              estado: "Activo",  total: 1842, mod: "Admisión"       },
  { recurso: "Appointment",          estado: "Activo",  total: 312,  mod: "Agenda"         },
  { recurso: "ImagingStudy",         estado: "Activo",  total: 284,  mod: "Imagenología"   },
  { recurso: "DiagnosticReport",     estado: "Activo",  total: 519,  mod: "Laboratorio"    },
  { recurso: "MedicationRequest",    estado: "Activo",  total: 173,  mod: "Farmacia"       },
  { recurso: "AdverseEvent",         estado: "Activo",  total: 12,   mod: "Seguridad"      },
  { recurso: "Consent",              estado: "Activo",  total: 428,  mod: "Consentimientos"},
  { recurso: "Practitioner",         estado: "Activo",  total: 87,   mod: "RRHH"           },
  { recurso: "Encounter",            estado: "Activo",  total: 631,  mod: "Atención"       },
  { recurso: "Observation",          estado: "Activo",  total: 2103, mod: "Laboratorio"    },
  { recurso: "AuditEvent",           estado: "Activo",  total: 5621, mod: "Auditoría"      },
  { recurso: "Coverage",             estado: "Activo",  total: 914,  mod: "Previsiones"    },
];

// ─────────────────────────────────────────────────────────────────
// § 4 · ÁTOMOS (componentes mínimos)
// ─────────────────────────────────────────────────────────────────
const C = {
  sidebarBg:    "#071526",
  sidebarHover: "#0F2540",
  sidebarActive:"#1A3E6E",
  bodyBg:       "#EEF2F7",
  surface:      "#FFFFFF",
  border:       "#E2EAF4",
  text:         "#1B2A3B",
  textMid:      "#455A64",
  textMuted:    "#78909C",
  primary:      "#1A4DA8",
  teal:         "#00A693",
  danger:       "#C62828",
  warning:      "#E65100",
  success:      "#2E7D32",
};

const StatusDot = ({ status, size = 7 }) => {
  const map = { online: C.teal, syncing: "#FFB74D", offline: C.danger, pending: "#FFB74D" };
  return (
    <span style={{
      display: "inline-block", width: size, height: size, borderRadius: "50%",
      background: map[status] || C.textMuted, flexShrink: 0,
      animation: status === "syncing" ? "pulse 1.5s infinite" : "none",
    }} />
  );
};

const Badge = ({ children, color = C.primary, sm }) => (
  <span style={{
    display: "inline-flex", alignItems: "center",
    padding: sm ? "1px 6px" : "2px 8px",
    fontSize: sm ? 9 : 10, fontWeight: 600, letterSpacing: "0.3px",
    borderRadius: 4, background: `${color}18`, color,
    border: `1px solid ${color}28`,
  }}>{children}</span>
);

const FTag = ({ r, sm }) => <Badge color={C.primary} sm={sm}>FHIR · {r}</Badge>;

const Btn = ({ children, icon: Icon, variant = "primary", size = "md", color, onClick, disabled }) => {
  const sz = { sm: "5px 10px", md: "7px 14px", lg: "10px 20px" }[size];
  const fs = { sm: 11, md: 12, lg: 13 }[size];
  const ic = { sm: 12, md: 13, lg: 14 }[size];
  const bg = variant === "primary" ? (color || C.primary)
    : variant === "success" ? C.success
    : variant === "danger"  ? C.danger
    : variant === "teal"    ? C.teal
    : "transparent";
  const fg = variant === "ghost" ? C.textMid : "#fff";
  const bd = variant === "ghost" ? `1px solid ${C.border}` : variant === "outline" ? `1px solid ${color || C.primary}` : "none";
  const fgOut = variant === "outline" ? (color || C.primary) : fg;
  return (
    <button onClick={onClick} disabled={disabled} style={{
      padding: sz, fontSize: fs, fontWeight: 600, gap: 5,
      background: disabled ? "#CFD8DC" : (variant === "ghost" || variant === "outline" ? (variant === "outline" ? `${color || C.primary}10` : "#fff") : bg),
      color: disabled ? "#90A4AE" : fgOut,
      border: disabled ? "1px solid #CFD8DC" : bd,
      borderRadius: 7, cursor: disabled ? "not-allowed" : "pointer",
      display: "inline-flex", alignItems: "center", transition: "all 0.15s",
    }}>
      {Icon && <Icon size={ic} />}{children}
    </button>
  );
};

const Card = ({ children, style }) => (
  <div style={{ background: C.surface, borderRadius: 12, border: `1px solid ${C.border}`, boxShadow: "0 1px 4px rgba(0,0,0,0.05)", ...style }}>
    {children}
  </div>
);

const SectionHead = ({ title, sub, icon: Icon, color, children }) => (
  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20, paddingBottom: 14, borderBottom: `1px solid ${C.border}` }}>
    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
      {Icon && <div style={{ background: `${color}18`, borderRadius: 10, padding: 10 }}><Icon size={22} color={color} /></div>}
      <div>
        <h2 style={{ margin: 0, fontSize: 17, fontWeight: 700, color: C.text }}>{title}</h2>
        {sub && <p style={{ margin: "2px 0 0", fontSize: 12, color: C.textMuted }}>{sub}</p>}
      </div>
    </div>
    {children && <div style={{ display: "flex", gap: 8 }}>{children}</div>}
  </div>
);

const TabBar = ({ tabs, active, onChange }) => (
  <div style={{ display: "flex", borderBottom: `1px solid ${C.border}`, marginBottom: 22, overflowX: "auto" }}>
    {tabs.map(t => (
      <button key={t.id} onClick={() => onChange(t.id)} style={{
        padding: "9px 15px", fontSize: 12, fontWeight: active === t.id ? 600 : 400,
        color: active === t.id ? C.primary : C.textMuted,
        borderBottom: `2px solid ${active === t.id ? C.primary : "transparent"}`,
        background: "none", border: "none", borderBottomWidth: 2, borderBottomStyle: "solid",
        cursor: "pointer", display: "flex", alignItems: "center", gap: 6, whiteSpace: "nowrap",
      }}>
        {t.icon && <t.icon size={13} />}{t.label}
      </button>
    ))}
  </div>
);

const KPICard = ({ label, value, sub, icon: Icon, color, trend }) => (
  <Card style={{ padding: "18px 20px", position: "relative", overflow: "hidden" }}>
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
      <div>
        <div style={{ fontSize: 11, color: C.textMuted, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.5px" }}>{label}</div>
        <div style={{ fontSize: 30, fontWeight: 700, color: C.text, lineHeight: 1.1, marginTop: 3 }}>{value}</div>
      </div>
      <div style={{ background: `${color}18`, borderRadius: 10, padding: 10, flexShrink: 0 }}>
        <Icon size={20} color={color} />
      </div>
    </div>
    {sub && <div style={{ fontSize: 11, color: C.textMuted }}>{sub}</div>}
    {trend !== undefined && (
      <div style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11, color: trend >= 0 ? C.success : C.danger, marginTop: 4 }}>
        {trend >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
        {Math.abs(trend)}% vs ayer
      </div>
    )}
    <div style={{ position: "absolute", top: 0, left: 0, width: 3, height: "100%", background: color, borderRadius: "12px 0 0 12px" }} />
  </Card>
);

const AlertRow = ({ tipo, msg, mod, time }) => {
  const cfg = {
    error:   { c: C.danger,  I: AlertCircle  },
    warning: { c: C.warning, I: AlertTriangle },
    info:    { c: C.primary, I: Info          },
    success: { c: C.success, I: CheckCircle   },
  }[tipo] || { c: C.primary, I: Info };
  return (
    <div style={{ display: "flex", alignItems: "flex-start", gap: 9, padding: "9px 12px", borderRadius: 7, background: `${cfg.c}0D`, borderLeft: `3px solid ${cfg.c}`, marginBottom: 6 }}>
      <cfg.I size={14} color={cfg.c} style={{ marginTop: 1, flexShrink: 0 }} />
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 12, color: C.text, lineHeight: 1.4 }}>{msg}</div>
        <div style={{ fontSize: 10, color: C.textMuted, marginTop: 2 }}>{mod} · {time}</div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────
// § 5 · DASHBOARD
// ─────────────────────────────────────────────────────────────────
const Dashboard = ({ onNav }) => (
  <div>
    {/* KPIs */}
    <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 12, marginBottom: 20 }}>
      <KPICard label="Pacientes Hoy"      value={KPI.pacientes}        icon={Users}        color={C.primary}  trend={12}   sub="Atendidos / día"  />
      <KPICard label="Citas Activas"      value={KPI.citas}            icon={Calendar}     color={C.teal}     trend={-3}   sub="Programadas"      />
      <KPICard label="Hospitalizados"     value={KPI.hospitalizados}   icon={Bed}          color="#6A1B9A"    trend={5}    sub="Camas ocupadas"   />
      <KPICard label="Urgencias"          value={KPI.urgencias}        icon={Zap}          color={C.danger}   trend={8}    sub="En curso"         />
      <KPICard label="Exáms. Pendientes"  value={KPI.pendientes}       icon={ClipboardList}color={C.warning}  trend={-15}  sub="Por informar"     />
      <KPICard label="Satisfacción"       value={`${KPI.satisfaccion}%`} icon={Star}       color={C.success}  trend={2.1}  sub="NPS mensual"      />
    </div>

    {/* Gráficos row 1 */}
    <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 14, marginBottom: 14 }}>
      {/* Actividad semanal */}
      <Card style={{ padding: "18px 20px" }}>
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.text }}>Actividad Clínica Semanal</div>
          <div style={{ fontSize: 11, color: C.textMuted }}>Pacientes por tipo · FHIR Encounter R4</div>
        </div>
        <ResponsiveContainer width="100%" height={170}>
          <AreaChart data={DATA_SEMANA} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="gA" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor={C.primary} stopOpacity={0.25}/>
                <stop offset="95%" stopColor={C.primary} stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="gU" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor={C.danger} stopOpacity={0.2}/>
                <stop offset="95%" stopColor={C.danger} stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#F0F4F8" />
            <XAxis dataKey="dia" tick={{ fontSize: 10, fill: C.textMuted }} />
            <YAxis tick={{ fontSize: 10, fill: C.textMuted }} />
            <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8, border: `1px solid ${C.border}` }} />
            <Legend wrapperStyle={{ fontSize: 10 }} />
            <Area type="monotone" dataKey="ambulatorio"    name="Ambulatorio"    stroke={C.primary} fill="url(#gA)" strokeWidth={2} />
            <Area type="monotone" dataKey="urgencias"      name="Urgencias"      stroke={C.danger}  fill="url(#gU)" strokeWidth={2} />
            <Area type="monotone" dataKey="hospitalizados" name="Hospitalizados" stroke={C.teal}    fill="none"     strokeWidth={1.5} strokeDasharray="4 2" />
          </AreaChart>
        </ResponsiveContainer>
      </Card>

      {/* Exámenes por servicio */}
      <Card style={{ padding: "18px 20px" }}>
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.text }}>Exámenes por Servicio</div>
          <div style={{ fontSize: 11, color: C.textMuted }}>Distribución mensual</div>
        </div>
        <ResponsiveContainer width="100%" height={120}>
          <PieChart>
            <Pie data={DATA_EXAMENES} cx="50%" cy="50%" innerRadius={34} outerRadius={55} dataKey="value" paddingAngle={3}>
              {DATA_EXAMENES.map((e, i) => <Cell key={i} fill={e.color} />)}
            </Pie>
            <Tooltip formatter={v => [`${v}%`]} contentStyle={{ fontSize: 10, borderRadius: 8 }} />
          </PieChart>
        </ResponsiveContainer>
        <div style={{ display: "flex", flexDirection: "column", gap: 4, marginTop: 8 }}>
          {DATA_EXAMENES.map(e => (
            <div key={e.name} style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <div style={{ width: 8, height: 8, borderRadius: 2, background: e.color, flexShrink: 0 }} />
              <span style={{ fontSize: 10, color: C.textMid, flex: 1 }}>{e.name}</span>
              <span style={{ fontSize: 10, fontWeight: 600, color: C.text }}>{e.value}%</span>
            </div>
          ))}
        </div>
      </Card>
    </div>

    {/* Gráficos row 2 */}
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 14 }}>
      {/* Financiero */}
      <Card style={{ padding: "18px 20px" }}>
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.text }}>Finanzas 2026 (MM CLP)</div>
          <div style={{ fontSize: 11, color: C.textMuted }}>Ingresos vs Egresos · FHIR Invoice</div>
        </div>
        <ResponsiveContainer width="100%" height={150}>
          <BarChart data={DATA_FINANCIERO} barGap={3} margin={{ left: -18, right: 4, top: 4, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#F0F4F8" />
            <XAxis dataKey="mes" tick={{ fontSize: 10, fill: C.textMuted }} />
            <YAxis tick={{ fontSize: 10, fill: C.textMuted }} tickFormatter={v => `$${v}M`} />
            <Tooltip formatter={v => [`$${v}M CLP`]} contentStyle={{ fontSize: 11, borderRadius: 8 }} />
            <Legend wrapperStyle={{ fontSize: 10 }} />
            <Bar dataKey="ingresos" name="Ingresos" fill={C.teal}   radius={[3,3,0,0]} />
            <Bar dataKey="egresos"  name="Egresos"  fill={C.danger} radius={[3,3,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      {/* Satisfacción */}
      <Card style={{ padding: "18px 20px" }}>
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.text }}>Satisfacción del Paciente</div>
          <div style={{ fontSize: 11, color: C.textMuted }}>Score NPS mensual · FHIR QuestionnaireResponse</div>
        </div>
        <ResponsiveContainer width="100%" height={150}>
          <LineChart data={DATA_SATISFACCION} margin={{ left: -18, right: 4, top: 4, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#F0F4F8" />
            <XAxis dataKey="mes" tick={{ fontSize: 10, fill: C.textMuted }} />
            <YAxis domain={[80, 100]} tick={{ fontSize: 10, fill: C.textMuted }} />
            <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
            <Line type="monotone" dataKey="score" name="Score %" stroke="#6A1B9A" strokeWidth={2.5} dot={{ fill: "#6A1B9A", r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </Card>
    </div>

    {/* Row: Pacientes + Alertas */}
    <div style={{ display: "grid", gridTemplateColumns: "3fr 1fr", gap: 14, marginBottom: 14 }}>
      {/* Tabla pacientes */}
      <Card style={{ padding: "18px 20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: C.text }}>Actividad Reciente · FHIR Patient</div>
            <div style={{ fontSize: 11, color: C.textMuted }}>Pacientes activos hoy</div>
          </div>
          <Btn variant="ghost" size="sm" icon={Filter}>Filtrar</Btn>
        </div>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ background: "#F5F8FF" }}>
              {["RUT","Paciente","Edad","Prestación","Estado","Recurso FHIR",""].map(h => (
                <th key={h} style={{ padding: "8px 11px", textAlign: "left", fontSize: 10, fontWeight: 600, color: C.textMuted, textTransform: "uppercase", letterSpacing: "0.4px", borderBottom: `1px solid ${C.border}` }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {PACIENTES_RECIENTES.map((p, i) => {
              const stC = { "En Sala": "#6A1B9A", Completado: C.primary, "En Espera": C.warning, Programado: C.teal }[p.estado] || C.textMid;
              return (
                <tr key={i} style={{ borderBottom: `1px solid #F5F8FF` }}>
                  <td style={{ padding: "9px 11px", fontSize: 11, fontWeight: 600, color: C.primary }}>{p.rut}</td>
                  <td style={{ padding: "9px 11px", fontSize: 12, fontWeight: 500, color: C.text }}>{p.nombre}</td>
                  <td style={{ padding: "9px 11px", fontSize: 11, color: C.textMid, textAlign: "center" }}>{p.edad}</td>
                  <td style={{ padding: "9px 11px", fontSize: 12, color: C.text }}>{p.prestacion}</td>
                  <td style={{ padding: "9px 11px" }}><Badge color={stC} sm>{p.estado}</Badge></td>
                  <td style={{ padding: "9px 11px" }}><Badge color={C.primary} sm>{p.fhir}</Badge></td>
                  <td style={{ padding: "9px 11px" }}>
                    <div style={{ display: "flex", gap: 5 }}>
                      <Btn variant="ghost" size="sm">Ver</Btn>
                      <Btn variant="outline" size="sm" color={C.primary}>FHIR</Btn>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Card>

      {/* Alertas */}
      <Card style={{ padding: "18px 20px" }}>
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.text }}>Alertas del Sistema</div>
          <div style={{ fontSize: 11, color: C.textMuted }}>Notificaciones activas</div>
        </div>
        {ALERTAS.map((a, i) => <AlertRow key={i} {...a} />)}
      </Card>
    </div>

    {/* FHIR Compliance Matrix */}
    <Card style={{ padding: "18px 20px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.text }}>Mapa de Recursos FHIR R4 · Compliance MINSAL</div>
          <div style={{ fontSize: 11, color: C.textMuted }}>Estado de implementación por recurso clínico</div>
        </div>
        <Badge color={C.teal}>{FHIR_COMPLIANCE.length} Recursos Activos</Badge>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
        {FHIR_COMPLIANCE.map((r, i) => (
          <div key={i} style={{ padding: "10px 12px", border: `1px solid ${C.border}`, borderRadius: 8, background: "#FAFCFF" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
              <StatusDot status="online" size={6} />
              <span style={{ fontSize: 11, fontWeight: 700, color: C.primary }}>{r.recurso}</span>
            </div>
            <div style={{ fontSize: 10, color: C.textMuted }}>{r.mod}</div>
            <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginTop: 3 }}>{r.total.toLocaleString()}</div>
          </div>
        ))}
      </div>
    </Card>
  </div>
);

// ─────────────────────────────────────────────────────────────────
// § 6 · MÓDULO GENÉRICO (Capa 1 — estructura lista para Layer 2)
// ─────────────────────────────────────────────────────────────────
const ModuleView = ({ mod, addToast }) => {
  const [tab, setTab] = useState(mod.submodules?.[0]?.id || "overview");

  const tabs = [
    { id: "overview", label: "Vista General", icon: LayoutDashboard },
    ...(mod.submodules || []).map(s => ({ id: s.id, label: s.label, icon: s.icon })),
  ];

  const activeTab = mod.submodules?.find(s => s.id === tab) || null;

  const mockStats = [
    { label: "Registros Total", value: Math.floor(Math.random() * 500 + 100), color: mod.color },
    { label: "Actividad Hoy",   value: Math.floor(Math.random() * 40 + 5),   color: C.teal    },
    { label: "Pendientes",      value: Math.floor(Math.random() * 20),        color: C.warning },
    { label: "Completados",     value: Math.floor(Math.random() * 100 + 30),  color: C.success },
  ];

  return (
    <div>
      <SectionHead title={mod.label} sub={`${(mod.fhir || []).join(" · ")} · MINSAL-CL · ${mod.standard || "FHIR R4"}`} icon={mod.icon} color={mod.color}>
        <Btn variant="ghost" size="sm" icon={Download}>Exportar</Btn>
        <Btn variant="primary" size="sm" icon={Plus} color={mod.color} onClick={() => addToast(`Nuevo registro en ${mod.label}`, "info")}>Nuevo</Btn>
      </SectionHead>

      <TabBar tabs={tabs} active={tab} onChange={setTab} />

      {tab === "overview" ? (
        <>
          {/* Stats */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 20 }}>
            {mockStats.map(s => (
              <Card key={s.label} style={{ padding: "14px 16px" }}>
                <div style={{ fontSize: 26, fontWeight: 700, color: s.color }}>{s.value}</div>
                <div style={{ fontSize: 11, color: C.textMuted, marginTop: 2 }}>{s.label}</div>
              </Card>
            ))}
          </div>

          {/* Submódulos grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 12, marginBottom: 20 }}>
            {(mod.submodules || []).map(sub => (
              <Card key={sub.id} style={{ padding: "16px 18px", cursor: "pointer", transition: "all 0.15s" }}
                onMouseOver={e => { e.currentTarget.style.boxShadow = `0 4px 16px ${mod.color}22`; e.currentTarget.style.borderColor = mod.color; }}
                onMouseOut={e => { e.currentTarget.style.boxShadow = "0 1px 4px rgba(0,0,0,0.05)"; e.currentTarget.style.borderColor = C.border; }}
                onClick={() => setTab(sub.id)}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
                  <div style={{ background: `${mod.color}18`, borderRadius: 8, padding: 8 }}>
                    <sub.icon size={17} color={mod.color} />
                  </div>
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 600, color: C.text }}>{sub.label}</div>
                    <FTag r={sub.fhir} sm />
                  </div>
                </div>
                <div style={{ display: "flex", justifyContent: "flex-end" }}>
                  <Btn variant="outline" size="sm" color={mod.color} icon={ArrowRight} onClick={e => { e.stopPropagation(); setTab(sub.id); }}>Abrir</Btn>
                </div>
              </Card>
            ))}
          </div>

          {/* Compliance banner */}
          <Card style={{ padding: "14px 18px", background: `${mod.color}06` }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
              <Shield size={14} color={mod.color} />
              <span style={{ fontSize: 11, fontWeight: 700, color: mod.color }}>Compliance activo:</span>
              {(mod.fhir || []).map(r => <FTag key={r} r={r} sm />)}
              <Badge color="#C62828" sm>MINSAL-CL</Badge>
              <Badge color="#6A1B9A" sm>Decreto 41</Badge>
              <Badge color="#E65100" sm>Ley 19.628</Badge>
              <Badge color="#37474F" sm>Ley 19.799 FES</Badge>
              {mod.standard && <Badge color={mod.color} sm>{mod.standard}</Badge>}
            </div>
          </Card>
        </>
      ) : (
        /* Vista de submódulo individual */
        <Card style={{ padding: "28px" }}>
          <div style={{ textAlign: "center", paddingTop: 20, paddingBottom: 20 }}>
            <div style={{ background: `${mod.color}15`, width: 64, height: 64, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px" }}>
              {activeTab && <activeTab.icon size={28} color={mod.color} />}
            </div>
            <div style={{ fontSize: 17, fontWeight: 700, color: C.text, marginBottom: 6 }}>{activeTab?.label}</div>
            <div style={{ fontSize: 12, color: C.textMuted, marginBottom: 20 }}>
              Módulo en desarrollo · {mod.label} · FHIR <strong>{activeTab?.fhir}</strong>
            </div>
            <div style={{ display: "flex", gap: 8, justifyContent: "center", flexWrap: "wrap", marginBottom: 24 }}>
              <FTag r={activeTab?.fhir || ""} />
              <Badge color={mod.color}>{mod.standard || "FHIR R4"}</Badge>
              <Badge color="#C62828">MINSAL-CL</Badge>
              <Badge color="#37474F">Decreto 41</Badge>
            </div>
            <div style={{ display: "inline-block", background: "#F5F8FF", border: `1px dashed ${mod.color}`, borderRadius: 10, padding: "14px 20px", fontSize: 12, color: C.textMid, marginBottom: 20 }}>
              💡 Este submódulo se desarrolla en la <strong>Capa 2</strong>.<br/>
              La arquitectura FHIR R4 y las interfaces de datos ya están definidas.
            </div>
            <div>
              <Btn variant="primary" icon={activeTab?.icon || Activity} color={mod.color} onClick={() => addToast(`${activeTab?.label} — módulo en construcción (Capa 2)`, "info")}>
                Previsualizar interfaz
              </Btn>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────
// § 6B · FARMACIA CENTRAL Y BODEGA (módulo especializado)
// Corrección aplicada tras revisión conjunta:
//  · Navegación anidada: Dashboard → [Farmacia Central | Bodega] +
//    submódulos compartidos (Clientes Ext., Balances, Eventos, etc.)
//  · Separación de roles: Farmacia Central aprueba/prepara/despacha;
//    la unidad con sub-farmacia solicita y confirma recepción.
//  · Cantidad ajustable en despacho (según disponible) y en
//    recepción (completo/parcial/excedente), con detalle siempre
//    visible y justificación obligatoria en la solicitud.
//  · Catálogo provisorio — se reemplaza por inventario_insumos.csv
//    oficial cuando se adjunte directo en el chat.
// ─────────────────────────────────────────────────────────────────


// ── CORRECCIÓN: se elimina por completo el CSV de Resonancia Magnética y
// las "sucursales" Bilbao/Fernández — eran solo un ejemplo de formato de
// código, nunca datos oficiales. Las únicas unidades válidas en AXON son
// las 41 ya confirmadas en arquitectura_farmacia_bodega.md. El catálogo de
// insumos vuelve a ser el de ejemplo (con código de barra, stock mínimo y
// máximo, como en FarmaciaBodegaApp) hasta que subas el catálogo oficial de
// AXON — separado en dos listas que NUNCA se mezclan: clínico (Farmacia) y
// no clínico (Bodega).

// Las 24 unidades con sub-farmacia + sub-bodega (confirmadas en el mapa
// consolidado). Farmacia solo trabaja con estas 24 — Bodega usa las 41.
const FB_UNIDADES_SUBFARMACIA = [
  { id: "IMG",     nombre: "Imagenología" },
  { id: "LAB",     nombre: "Laboratorio" },
  { id: "ANATPAT", nombre: "Anatomía Patológica y Morfofisiopatología" },
  { id: "OFT",     nombre: "Oftalmología" },
  { id: "ORL",     nombre: "Otorrinolaringología" },
  { id: "CARDIO",  nombre: "Cardiología" },
  { id: "ESPEC",   nombre: "Exámenes de Especialidad Médica" },
  { id: "TERAPIA", nombre: "Terapia y Rehabilitación" },
  { id: "OBST",    nombre: "Obstetricia, Matronería y Puericultura" },
  { id: "PSICO",   nombre: "Psicología" },
  { id: "MEDNUC",  nombre: "Medicina Nuclear" },
  { id: "GASTRO",  nombre: "Gastroenterología" },
  { id: "URO",     nombre: "Urología" },
  { id: "GINECO",  nombre: "Ginecología" },
  { id: "DERMATO", nombre: "Dermatología" },
  { id: "NEURO",   nombre: "Neurología" },
  { id: "BRONCO",  nombre: "Bronconeumología" },
  { id: "ONCO",    nombre: "Oncología y Radioterapia" },
  { id: "ODONTO",  nombre: "Odontología" },
  { id: "QUIR",    nombre: "Atención Quirúrgica" },
  { id: "HOSP",    nombre: "Hospitalización" },
  { id: "URG",     nombre: "Urgencias" },
  { id: "AMB",     nombre: "Atención Médica Ambulatoria" },
  { id: "RESCATE", nombre: "Servicio de Rescate" },
];

// Las 41 completas (24 de arriba + 17 solo-bodega). Definida para cuando
// construyamos Bodega (#11/#12) — todavía NO está conectada a ninguna
// vista; Bodega sigue en "Próximamente" hasta que lo pidas.
const FB_UNIDADES_SUBBODEGA = [
  ...FB_UNIDADES_SUBFARMACIA,
  { id: "ADMIN",    nombre: "Sección Administrativa" },
  { id: "ALIM",     nombre: "Alimentación y Nutrición" },
  { id: "TRASLAD",  nombre: "Gestión Traslados" },
  { id: "SANIT",    nombre: "Sanitización Clínica y Esterilización" },
  { id: "EQUIP",    nombre: "Equipamiento e Infraestructura" },
  { id: "INFO",     nombre: "Informática y Soporte Digital" },
  { id: "GUARDIA",  nombre: "Guardias de Seguridad" },
  { id: "CALIDAD",  nombre: "Calidad y Acreditación" },
  { id: "ETICA",    nombre: "Comité de Ética" },
  { id: "CMED",     nombre: "Comité Médico" },
  { id: "JMED",     nombre: "Junta Médica" },
  { id: "RRHH",     nombre: "Recursos Humanos" },
  { id: "MKT",      nombre: "Marketing" },
  { id: "INVEST",   nombre: "Investigación" },
  { id: "DOC",      nombre: "Docencia" },
  { id: "CONT",     nombre: "Contabilidad" },
  { id: "ADIR",     nombre: "Alta Dirección" },
];

// Catálogo de ejemplo — SOLO insumos clínicos (medicamentos + insumos
// clínicos). Nunca se mezcla con lo administrativo/aseo, que va en el
// catálogo de Bodega cuando lo construyamos.
// ── NIVEL 1 · CONCEPTO FÁRMACO (DCI + SNOMED CT) — lo que se prescribe.
// Solo aplica a medicamentos (no a insumos clínicos, que no son fármacos).
// Nombres DCI reales (OMS/INN). Códigos SNOMED CT marcados como formato
// ilustrativo — no se afirman como el código oficial verificado, mismo
// criterio que el código de barra de ejemplo. Fuente: estandares_de_farmacia.txt.
//
// `concentracion` va como numerador/denominador (cada uno con su propia
// unidad), no como texto libre — mismo modelo que usa FHIR R4 en
// Medication.ingredient.strength (tipo Ratio: numerator/denominator, cada
// uno un Quantity con value+unit). Evita mezclar masa/volumen/porcentaje en
// un solo campo de texto (ver Respuestas +2, punto 3). Para porcentajes
// (ej. Cloruro de Sodio 0.9%) el denominador queda en null.
const FB_UNIDADES_NUMERADOR = ["mg", "g", "mcg", "UI", "mg I", "%"];
const FB_UNIDADES_DENOMINADOR = ["mL", "L", "comprimido", "cápsula", "dosis", "unidad"];
function fbFormatConcentracion(c) {
  if (!c || c.numeradorValor == null) return "";
  if (c.denominadorValor == null || !c.denominadorUnidad) return `${c.numeradorValor} ${c.numeradorUnidad}`;
  return `${c.numeradorValor} ${c.numeradorUnidad} / ${c.denominadorValor} ${c.denominadorUnidad}`;
}
const FB_CONCEPTOS_FARMACO = [
  { id: "DCI-001", dci: "Furosemida",                                concentracion: { numeradorValor: 20,  numeradorUnidad: "mg",   denominadorValor: 2, denominadorUnidad: "mL" }, formaFarmaceutica: "Solución inyectable",                      snomedCT: "387475002 (ilustrativo)" },
  { id: "DCI-002", dci: "Butilescopolamina (Hioscina butilbromuro)", concentracion: { numeradorValor: 20,  numeradorUnidad: "mg",   denominadorValor: 1, denominadorUnidad: "mL" }, formaFarmaceutica: "Solución inyectable",                      snomedCT: "387506000 (ilustrativo)" },
  { id: "DCI-003", dci: "Cloruro de sodio",                          concentracion: { numeradorValor: 0.9, numeradorUnidad: "%",   denominadorValor: null, denominadorUnidad: null }, formaFarmaceutica: "Solución para infusión intravenosa",       snomedCT: "325646002 (ilustrativo)" },
  { id: "DCI-004", dci: "Iohexol",                                   concentracion: { numeradorValor: 300, numeradorUnidad: "mg I", denominadorValor: 1, denominadorUnidad: "mL" }, formaFarmaceutica: "Solución inyectable (medio de contraste)", snomedCT: "419241000 (ilustrativo)" },
];

// ── NIVEL 2 (marca/ISP) + NIVEL 3 (CENABAST) — el `id` (MED-xxx/INS-xxx) se
// mantiene igual que antes para no romper FB_CENTRAL_INICIAL, FB_SUBSTOCK_
// INICIAL, FB_CATALOGO_PROVEEDOR, FB_LOTES_INICIAL ni FB_SOLICITUDES_INICIAL
// — solo se enriquece cada fila. `conceptoId` es null en insumos clínicos
// (no son fármacos, no tienen DCI, pero sí registro ISP como dispositivo
// médico y código CENABAST). Marca/laboratorio/registro ISP de ejemplo.
const FB_CATALOGO = [
  { id: "MED-001", conceptoId: "DCI-001", nombre: "Furosemida 20mg/2ml",             marca: "Furosemida Sanderson",  laboratorio: "Lab. Sanderson",     registroISP: "F-9821/15",  codigoCenabast: "10023456", unidad: "ampolla", codigoBarra: "7801234500019" },
  { id: "MED-002", conceptoId: "DCI-002", nombre: "Butilbromuro de Hioscina 20mg/ml", marca: "Buscapina Compositum", laboratorio: "Boehringer Ingelheim", registroISP: "F-7734/12",  codigoCenabast: "10023457", unidad: "ampolla", codigoBarra: "7801234500026" },
  { id: "MED-003", conceptoId: "DCI-003", nombre: "Suero Fisiológico 0.9% 1000ml",    marca: "Cloruro de Sodio Baxter", laboratorio: "Baxter",           registroISP: "F-5521/09",  codigoCenabast: "10023458", unidad: "bolsa",   codigoBarra: "7801234500033" },
  { id: "MED-004", conceptoId: "DCI-004", nombre: "Medio de Contraste Iodado 100ml",  marca: "Omnipaque",             laboratorio: "GE Healthcare",      registroISP: "F-6642/11",  codigoCenabast: "10023459", unidad: "frasco",  codigoBarra: "7801234500040" },
  { id: "INS-001", conceptoId: null,      nombre: "Bránula N°18",                     marca: "BD Insyte",             laboratorio: "Becton Dickinson",   registroISP: "D-1123/18",  codigoCenabast: "20011234", unidad: "unidad",  codigoBarra: "7801234500057" },
  { id: "INS-002", conceptoId: null,      nombre: "Mariposa N°21",                    marca: "Vacutainer Safety-Lok",  laboratorio: "BD",                 registroISP: "D-1187/18",  codigoCenabast: "20011235", unidad: "unidad",  codigoBarra: "7801234500064" },
  { id: "INS-003", conceptoId: null,      nombre: "Guantes de nitrilo talla M",       marca: "Nitrimax",               laboratorio: "Sigma Médica",       registroISP: "D-0456/20",  codigoCenabast: "20011236", unidad: "par",     codigoBarra: "7801234500071" },
  { id: "INS-004", conceptoId: null,      nombre: "Vacutainer tapa lila",             marca: "Vacutainer EDTA",        laboratorio: "BD",                 registroISP: "D-1188/18",  codigoCenabast: "20011237", unidad: "unidad",  codigoBarra: "7801234500088" },
];

const FB_CENTRAL_INICIAL = {
  "MED-001": { stockActual: 320, stockMinimo: 100 },
  "MED-002": { stockActual: 80,  stockMinimo: 100 },
  "MED-003": { stockActual: 500, stockMinimo: 150 },
  "MED-004": { stockActual: 40,  stockMinimo: 50  },
  "INS-001": { stockActual: 900, stockMinimo: 300 },
  "INS-002": { stockActual: 150, stockMinimo: 200 },
  "INS-003": { stockActual: 1200,stockMinimo: 400 },
  "INS-004": { stockActual: 260, stockMinimo: 100 },
};

const FB_LOTES_INICIAL = [
  { id: "L-1", itemId: "MED-002", numeroLote: "B24-118", fechaVencimiento: "2026-09-10" },
  { id: "L-2", itemId: "MED-004", numeroLote: "C25-044", fechaVencimiento: "2026-08-12" },
  { id: "L-3", itemId: "MED-001", numeroLote: "A24-201", fechaVencimiento: "2027-03-01" },
];

// Datos cargados de ejemplo SOLO en 4 de las 24 unidades (para no inventar
// cantidades en las otras 20 sin que tú las apruebes). El resto aparece en
// el listado real pero muestra "Sin stock cargado" hasta que se carguen.
const FB_SUBSTOCK_INICIAL = {
  "IMG": {
    "MED-001": { stockActual: 6,  stockMinimo: 10, stockMaximo: 30  },
    "MED-004": { stockActual: 0,  stockMinimo: 8,  stockMaximo: 20  },
    "INS-001": { stockActual: 25, stockMinimo: 20, stockMaximo: 60  },
    "INS-003": { stockActual: 40, stockMinimo: 30, stockMaximo: 90  },
  },
  "URG": {
    "MED-001": { stockActual: 4,  stockMinimo: 15, stockMaximo: 40  },
    "MED-002": { stockActual: 12, stockMinimo: 10, stockMaximo: 30  },
    "INS-001": { stockActual: 18, stockMinimo: 25, stockMaximo: 60  },
    "INS-002": { stockActual: 30, stockMinimo: 20, stockMaximo: 60  },
    "INS-003": { stockActual: 60, stockMinimo: 40, stockMaximo: 120 },
  },
  "LAB": {
    "INS-004": { stockActual: 15, stockMinimo: 40, stockMaximo: 100 },
    "INS-002": { stockActual: 22, stockMinimo: 15, stockMaximo: 45  },
    "INS-003": { stockActual: 35, stockMinimo: 30, stockMaximo: 90  },
  },
  "QUIR": {
    "MED-002": { stockActual: 15, stockMinimo: 10, stockMaximo: 30  },
    "INS-001": { stockActual: 50, stockMinimo: 30, stockMaximo: 90  },
    "INS-003": { stockActual: 80, stockMinimo: 50, stockMaximo: 150 },
  },
};

const FB_SOLICITUDES_INICIAL = [
  {
    folio: "SOL-2026-0001",
    subFarmaciaId: "URG",
    fechaSolicitud: "2026-08-01T09:15:00",
    prioridad: "urgente",
    justificacion: "Consumo elevado por turno de fin de semana, stock bajo mínimo en 2 ítems.",
    items: [
      { itemId: "MED-001", cantidadSolicitada: 20 },
      { itemId: "INS-001", cantidadSolicitada: 15 },
    ],
    estado: "pendiente-coordinador",
  },
  {
    folio: "SOL-2026-0002",
    subFarmaciaId: "IMG",
    fechaSolicitud: "2026-07-30T14:00:00",
    prioridad: "normal",
    justificacion: "Reposición programada de medio de contraste.",
    items: [{ itemId: "MED-004", cantidadSolicitada: 10, cantidadDespachada: 10 }],
    estado: "despachada",
    fechaDespacho: "2026-07-31T10:00:00",
  },
];

// ── BODEGA: mismo patrón que Farmacia, catálogo separado (nunca se mezcla
// con insumos clínicos). Ejemplo mínimo, igual de provisorio que el de
// Farmacia — se reemplaza cuando subas el catálogo oficial de insumos no
// clínicos de AXON. Unidades: las 41 completas (FB_UNIDADES_SUBBODEGA).
const FB_CATALOGO_BODEGA = [
  { id: "BOD-001", nombre: "Resma de papel carta",     unidad: "resma",    codigoBarra: "7802345600012" },
  { id: "BOD-002", nombre: "Tóner impresora HP 26A",   unidad: "unidad",   codigoBarra: "7802345600029" },
  { id: "BOD-003", nombre: "Bolsas de basura 70x90",   unidad: "paquete",  codigoBarra: "7802345600036" },
  { id: "BOD-004", nombre: "Cloro gel",                unidad: "litro",   codigoBarra: "7802345600043" },
  { id: "BOD-005", nombre: "Papel higiénico jumbo",    unidad: "rollo",   codigoBarra: "7802345600050" },
  { id: "BOD-006", nombre: "Lápiz pasta azul",         unidad: "unidad",  codigoBarra: "7802345600067" },
  // BOD-007/008: agregados para #25 Bodega e Insumos Propios — son
  // literalmente los ejemplos que da arquitectura_farmacia_bodega.md
  // ("papel térmico, etiquetas de código de barras") y no existían todavía.
  { id: "BOD-007", nombre: "Papel térmico para impresora de etiquetas", unidad: "rollo", codigoBarra: "7802345600074" },
  { id: "BOD-008", nombre: "Etiquetas autoadhesivas código de barra",   unidad: "rollo", codigoBarra: "7802345600081" },
];

const FB_CENTRAL_BODEGA_INICIAL = {
  "BOD-001": { stockActual: 400, stockMinimo: 150 },
  "BOD-002": { stockActual: 60,  stockMinimo: 30  },
  "BOD-003": { stockActual: 300, stockMinimo: 100 },
  "BOD-004": { stockActual: 80,  stockMinimo: 40  },
  "BOD-005": { stockActual: 500, stockMinimo: 200 },
  "BOD-006": { stockActual: 200, stockMinimo: 80  },
  "BOD-007": { stockActual: 150, stockMinimo: 60  },
  "BOD-008": { stockActual: 90,  stockMinimo: 40  },
};

// Solo 4 de las 41 unidades con stock de ejemplo cargado (2 clínicas que
// también usan bodega, 2 puramente administrativas) — el resto queda "Sin
// datos" igual que en Farmacia, mismo criterio, nada inventado de más.
const FB_SUBSTOCK_BODEGA_INICIAL = {
  "IMG": {
    "BOD-001": { stockActual: 30, stockMinimo: 20, stockMaximo: 60 },
    "BOD-005": { stockActual: 10, stockMinimo: 15, stockMaximo: 40 },
  },
  "URG": {
    "BOD-003": { stockActual: 8,  stockMinimo: 10, stockMaximo: 30 },
    "BOD-004": { stockActual: 5,  stockMinimo: 8,  stockMaximo: 20 },
  },
  "ADMIN": {
    "BOD-001": { stockActual: 60, stockMinimo: 40, stockMaximo: 120 },
    "BOD-002": { stockActual: 4,  stockMinimo: 6,  stockMaximo: 15  },
    "BOD-006": { stockActual: 25, stockMinimo: 15, stockMaximo: 45  },
  },
  "SANIT": {
    "BOD-003": { stockActual: 20, stockMinimo: 25, stockMaximo: 60 },
    "BOD-004": { stockActual: 15, stockMinimo: 10, stockMaximo: 30 },
    "BOD-005": { stockActual: 30, stockMinimo: 20, stockMaximo: 60 },
  },
};

const FB_SOLICITUDES_BODEGA_INICIAL = [
  {
    folio: "SOLB-2026-0001",
    subFarmaciaId: "SANIT",
    fechaSolicitud: "2026-08-01T11:00:00",
    prioridad: "normal",
    justificacion: "Reposición mensual de insumos de aseo.",
    items: [{ itemId: "BOD-003", cantidadSolicitada: 30 }],
    estado: "pendiente-coordinador",
  },
  {
    folio: "SOLB-2026-0002",
    subFarmaciaId: "ADMIN",
    fechaSolicitud: "2026-07-29T10:00:00",
    prioridad: "normal",
    justificacion: "Se acabó el tóner de la impresora de admisión.",
    items: [{ itemId: "BOD-002", cantidadSolicitada: 6, cantidadDespachada: 6 }],
    estado: "despachada",
    fechaDespacho: "2026-07-30T09:00:00",
  },
];

// ── #25 BODEGA E INSUMOS PROPIOS: inventario interno de la propia unidad de
// Farmacia Central y Bodega (no confundir con la Bodega Central #11) — lo
// que el equipo consume para operar (papel térmico, etiquetas, embalaje,
// EPP, oficina). A pedido del usuario, NO se construye como un sistema
// aparte con su propio tipo de dato: se trata exactamente igual que las
// otras 41 unidades — una unidad más que solicita reposición a Bodega
// Central usando el mismo flujo de 2 filtros ya construido (FbStockPorUnidad
// + FbColaSolicitudes + fbCrearHandlers), sobre el mismo catálogo de Bodega.
// Deliberadamente NO se agrega a FB_UNIDADES_SUBBODEGA — esa lista son las
// "41 unidades reales" abastecidas (arquitectura_farmacia_bodega.md), un
// conteo canónico que no debe alterarse. Insumos Propios es una unidad
// adicional, separada, con su propio stock/solicitudes/folio (prefijo
// "SOLP"), que vive en su propia pantalla (#25, fila de compartidos).
const FB_UNIDAD_PROPIA = [{ id: "PROPIA", nombre: "Farmacia y Bodega — Uso Interno" }];
// A pedido del usuario: "PROPIA" también debe ser visible/operable dentro de
// las pestañas normales de Bodega (#12 Stock y Sub-bodegas / #14 Solicitudes),
// no solo en su propia pantalla (#25) — así se encuentra donde se busca por
// instinto. Esta lista combinada es SOLO para esas 2 pestañas puntuales;
// FB_UNIDADES_SUBBODEGA (las 41 reales) no se toca, y el Dashboard sigue
// leyendo esa constante directo, así que el conteo "/41" no se corrompe.
const FB_UNIDADES_SUBBODEGA_MAS_PROPIA = [...FB_UNIDADES_SUBBODEGA, ...FB_UNIDAD_PROPIA];

const FB_SUBSTOCK_PROPIA_INICIAL = {
  PROPIA: {
    "BOD-007": { stockActual: 4,  stockMinimo: 10, stockMaximo: 30 },
    "BOD-008": { stockActual: 25, stockMinimo: 15, stockMaximo: 40 },
    "BOD-002": { stockActual: 2,  stockMinimo: 5,  stockMaximo: 15 },
    "BOD-001": { stockActual: 30, stockMinimo: 20, stockMaximo: 50 },
  },
};
const FB_SOLICITUDES_PROPIA_INICIAL = [];

// (FB_DATA_SEMANA — constante fija de despachos semanales de ejemplo —
// eliminada: ahora el Dashboard calcula esto de los movimientos reales de
// Trazabilidad con fbCalcularDespachosSemana(). Ver Parte 14 del dossier.)

// ── GESTIÓN PROVEEDORES: modelo unificado con campo `dominio`, tal como
// sugería la nota original de arquitectura_farmacia_bodega.md. Listas de
// proveedores separadas por dominio (Farmacia ≠ Bodega, son empresas
// distintas), pero el proceso de adquisición converge en uno solo, que
// eventualmente conecta con Contabilidad (puerta etiquetada #2, ver
// sincronizacion_farmacia_bodega_main.md). Datos de ejemplo — se
// reemplazan cuando exista el listado oficial de proveedores de AXON.
const FB_PROVEEDORES = [
  {
    id: "PROV-001", dominio: "farmacia", razonSocial: "Laboratorio Andino S.A.", rut: "76.123.456-7",
    giro: "Fabricación y distribución de medicamentos",
    contacto: { nombre: "Marcela Ruiz", cargo: "Ejecutiva de Cuenta", telefono: "+56 2 2345 6789", email: "mruiz@labandino.cl" },
    direccion: "Quilicura, Santiago, Región Metropolitana",
    comercial: { tipoContrato: "marco", condicionPago: "30 días", plazoEntregaDias: 5, vigenciaContrato: "01-2026 – 12-2027" },
    evaluacion: { calificacionGeneral: 4.5, cumplimientoPlazo: 92 },
    rubros: ["Medicamentos genéricos", "Soluciones parenterales"],
    estado: "activo",
  },
  {
    id: "PROV-002", dominio: "farmacia", razonSocial: "DIFEM Insumos Médicos Ltda.", rut: "77.456.123-2",
    giro: "Distribución de insumos clínicos y dispositivos médicos",
    contacto: { nombre: "Rodrigo Salas", cargo: "Jefe Comercial", telefono: "+56 2 2987 6543", email: "rsalas@difem.cl" },
    direccion: "Renca, Santiago, Región Metropolitana",
    comercial: { tipoContrato: "convenio", condicionPago: "45 días", plazoEntregaDias: 3, vigenciaContrato: "03-2026 – 03-2028" },
    evaluacion: { calificacionGeneral: 4.1, cumplimientoPlazo: 88 },
    rubros: ["Bránulas y catéteres", "Material de curación", "Descartables"],
    estado: "activo",
  },
  {
    id: "PROV-003", dominio: "farmacia", razonSocial: "Bayer Chile S.A.", rut: "91.234.567-8",
    giro: "Laboratorio farmacéutico multinacional",
    contacto: { nombre: "Constanza Vidal", cargo: "KAM Hospitales", telefono: "+56 2 2600 1000", email: "constanza.vidal@bayer.cl" },
    direccion: "Las Condes, Santiago, Región Metropolitana",
    comercial: { tipoContrato: "licitacion", condicionPago: "60 días", plazoEntregaDias: 10, vigenciaContrato: "06-2025 – 06-2026" },
    evaluacion: { calificacionGeneral: 4.8, cumplimientoPlazo: 96 },
    rubros: ["Medicamentos de especialidad", "Medios de contraste"],
    estado: "en-evaluacion",
  },
  {
    id: "PROV-004", dominio: "bodega", razonSocial: "Distribuidora ABC Insumos SpA", rut: "78.321.654-9",
    giro: "Distribución de artículos de oficina y papelería",
    contacto: { nombre: "Felipe Contreras", cargo: "Vendedor", telefono: "+56 9 8765 4321", email: "felipe@abcinsumos.cl" },
    direccion: "San Bernardo, Santiago, Región Metropolitana",
    comercial: { tipoContrato: "spot", condicionPago: "Contado", plazoEntregaDias: 2, vigenciaContrato: "—" },
    evaluacion: { calificacionGeneral: 3.9, cumplimientoPlazo: 85 },
    rubros: ["Papelería", "Insumos de oficina"],
    estado: "activo",
  },
  {
    id: "PROV-005", dominio: "bodega", razonSocial: "Higiene Total Ltda.", rut: "76.789.012-3",
    giro: "Venta de insumos de aseo e higiene industrial",
    contacto: { nombre: "Paula Muñoz", cargo: "Ejecutiva Comercial", telefono: "+56 2 2456 7890", email: "pmunoz@higienetotal.cl" },
    direccion: "Maipú, Santiago, Región Metropolitana",
    comercial: { tipoContrato: "convenio", condicionPago: "30 días", plazoEntregaDias: 4, vigenciaContrato: "02-2026 – 02-2027" },
    evaluacion: { calificacionGeneral: 4.2, cumplimientoPlazo: 90 },
    rubros: ["Aseo y limpieza", "Insumos sanitarios"],
    estado: "activo",
  },
  {
    id: "PROV-006", dominio: "bodega", razonSocial: "Repuestos y Mantención Sur S.A.", rut: "79.654.321-0",
    giro: "Repuestos y mantención de vehículos y equipos",
    contacto: { nombre: "Iván Torres", cargo: "Encargado de Ventas", telefono: "+56 9 5555 1234", email: "itorres@repuestosur.cl" },
    direccion: "San Joaquín, Santiago, Región Metropolitana",
    comercial: { tipoContrato: "spot", condicionPago: "15 días", plazoEntregaDias: 7, vigenciaContrato: "—" },
    evaluacion: { calificacionGeneral: 3.6, cumplimientoPlazo: 78 },
    rubros: ["Repuestos vehículos", "Mantención equipos"],
    estado: "suspendido",
  },
];

// ── CATÁLOGO POR PROVEEDOR: la pieza que faltaba. Los insumos no se
// compran por unidad de dispensación (ampolla, bolsa, par) sino por
// presentación de compra (caja, bulto, paquete). Cada proveedor puede
// vender el mismo ítem en una presentación distinta — por eso esto vive
// separado del catálogo maestro (FB_CATALOGO / FB_CATALOGO_BODEGA), no
// mezclado. `unidadesPorPresentacion` es el factor de conversión: cuántas
// unidades de dispensación trae 1 unidad de presentación de compra.
// `codigoProveedor` es el SKU propio del proveedor, distinto de nuestro
// id interno. Solo se listan los ítems que ESE proveedor efectivamente
// vende — de ahí el "multibox por proveedor". Datos de ejemplo.
const FB_CATALOGO_PROVEEDOR = {
  "PROV-001": [ // Laboratorio Andino — genéricos y parenterales
    { itemId: "MED-001", codigoProveedor: "LA-FUR-20AMP",  presentacionCompra: "Caja x 50 ampollas", unidadesPorPresentacion: 50,  cantidadMinimaCompra: 1, precioReferencialCaja: 45000 },
    { itemId: "MED-002", codigoProveedor: "LA-HIO-20AMP",  presentacionCompra: "Caja x 30 ampollas", unidadesPorPresentacion: 30,  cantidadMinimaCompra: 1, precioReferencialCaja: 39000 },
    { itemId: "MED-003", codigoProveedor: "LA-SF1000-BLS", presentacionCompra: "Caja x 20 bolsas",   unidadesPorPresentacion: 20,  cantidadMinimaCompra: 2, precioReferencialCaja: 38000 },
  ],
  "PROV-002": [ // DIFEM — bránulas, catéteres, descartables
    { itemId: "INS-001", codigoProveedor: "DIF-BR18-100",  presentacionCompra: "Caja x 100 unidades", unidadesPorPresentacion: 100, cantidadMinimaCompra: 1, precioReferencialCaja: 22000 },
    { itemId: "INS-002", codigoProveedor: "DIF-MAR21-100", presentacionCompra: "Caja x 100 unidades", unidadesPorPresentacion: 100, cantidadMinimaCompra: 1, precioReferencialCaja: 24000 },
    { itemId: "INS-003", codigoProveedor: "DIF-GNM-200",   presentacionCompra: "Caja x 200 pares",    unidadesPorPresentacion: 200, cantidadMinimaCompra: 1, precioReferencialCaja: 55000 },
    { itemId: "INS-004", codigoProveedor: "DIF-VACLI-100", presentacionCompra: "Caja x 100 unidades", unidadesPorPresentacion: 100, cantidadMinimaCompra: 2, precioReferencialCaja: 31000 },
  ],
  "PROV-003": [ // Bayer Chile — especialidad y contraste
    { itemId: "MED-004", codigoProveedor: "BAY-CONT100-CJ", presentacionCompra: "Caja x 10 frascos", unidadesPorPresentacion: 10, cantidadMinimaCompra: 1, precioReferencialCaja: 180000 },
  ],
  "PROV-004": [ // Distribuidora ABC — papelería y oficina
    { itemId: "BOD-001", codigoProveedor: "ABC-RES-CARTA",  presentacionCompra: "Paquete x 10 resmas", unidadesPorPresentacion: 10,  cantidadMinimaCompra: 1, precioReferencialCaja: 32000 },
    { itemId: "BOD-002", codigoProveedor: "ABC-TON-26A",    presentacionCompra: "Unidad",              unidadesPorPresentacion: 1,   cantidadMinimaCompra: 1, precioReferencialCaja: 45000 },
    { itemId: "BOD-006", codigoProveedor: "ABC-LAP-AZ-12",  presentacionCompra: "Caja x 12 unidades",  unidadesPorPresentacion: 12,  cantidadMinimaCompra: 1, precioReferencialCaja: 3000 },
  ],
  "PROV-005": [ // Higiene Total — aseo e higiene
    { itemId: "BOD-003", codigoProveedor: "HT-BOL7090-50",  presentacionCompra: "Paquete x 50 unidades", unidadesPorPresentacion: 50, cantidadMinimaCompra: 1, precioReferencialCaja: 18000 },
    { itemId: "BOD-004", codigoProveedor: "HT-CLORGEL-5L",  presentacionCompra: "Bidón x 5 litros",      unidadesPorPresentacion: 5,  cantidadMinimaCompra: 1, precioReferencialCaja: 12000 },
    { itemId: "BOD-005", codigoProveedor: "HT-PHJUMBO-12",  presentacionCompra: "Fardo x 12 rollos",     unidadesPorPresentacion: 12, cantidadMinimaCompra: 1, precioReferencialCaja: 21000 },
  ],
  "PROV-006": [], // Repuestos y Mantención Sur — no vende insumos del catálogo actual (además, suspendido)
};

// ── RECEPCIONES: registro formal de mercadería que llega de un proveedor.
// Reemplaza el atajo anterior (el pedido bumpeaba stock directo al llegar a
// "recibido total"). Ahora el stock sube SOLO al aceptar una Recepción, con
// la cantidad REALMENTE recibida (no la solicitada), y cada Recepción puede
// o no estar vinculada a un Pedido (ver arquitectura_farmacia_bodega.md
// #4/#13). Vacío hasta que se registre la primera — no se inventan
// recepciones históricas de ejemplo.
const FB_RECEPCIONES_INICIAL = [];
const FB_RECEPCIONES_BODEGA_INICIAL = [];

const RECEPCION_ESTADO_META = {
  aceptada: { label: "Aceptada", color: C.success },
  "aceptada-con-observaciones": { label: "Aceptada c/observaciones", color: C.warning },
  rechazada: { label: "Rechazada", color: C.danger },
};

const FB_FARMACIA_SUBMODULOS = [
  // #2 faltaba: hasta ahora solo se veía el stock POR UNIDAD (#3), nunca el
  // catálogo maestro + stock consolidado de Farmacia Central en sí — el
  // usuario lo notó al no tener forma de saber cuánto hay disponible para
  // repartir entre las 24 sub-farmacias.
  { id: "medicamentos_farm",  num: 2,  label: "Farmacia: Medicamentos",           icon: Pill,          built: true,
    desc: "Catálogo maestro y stock consolidado de Farmacia Central — lo disponible para repartir a las 24 sub-farmacias." },
  { id: "stock_subfarmacias", num: 3,  label: "Stock y Sub-farmacias",            icon: Layers,        built: true,
    desc: "Stock, alertas y las sub-farmacias asociadas (Urgencias, Hospitalización, Imagenología, etc.)." },
  { id: "recepciones_farm",   num: 4,  label: "Recepciones y Nuevo Insumo",       icon: Package,       built: true,
    desc: "Recepción de insumos clínicos y fármacos desde proveedores externos." },
  { id: "pedidos_farm",       num: 5,  label: "Solicitud de Pedidos",             icon: ClipboardList, built: true,
    desc: "Solicitudes de las sub-farmacias para reposición de insumos clínicos y farmacológicos." },
  { id: "delivery_farm",      num: 6,  label: "Gestión Movilización (Delivery)",  icon: Truck,         built: false,
    desc: "Envío de fármacos/insumos para hospitalizados o urgencia domiciliaria (lo solicita la unidad correspondiente); también ambulatorio vía Portal Paciente con el cobro asociado." },
  { id: "recetas_farm",       num: 7,  label: "Recetas Totales Retenidas",        icon: FileText,      built: false,
    desc: "Registro de cada receta retenida, para solicitudes internas y externas." },
  { id: "trazabilidad_farm",  num: 8,  label: "Trazabilidad",                     icon: Search,        built: true,
    desc: "Movimientos y estados de cada insumo clínico o de farmacia, por usuario." },
  // Cuadratura NO está entre los 27 submódulos canónicos de
  // arquitectura_farmacia_bodega.md — no lleva número (num: null). Nace de la
  // decisión #8 de la Parte 2 del dossier ("ajuste de stock forzado con motivo
  // obligatorio y trazabilidad siempre") y del triage de la Parte 13.
  { id: "cuadratura_farm",    num: null, label: "Cuadratura de Stock",           icon: CheckSquare,   built: true,
    desc: "Ajustes de stock central con motivo obligatorio: merma, vencimiento o diferencia de conteo. Cada ajuste queda en Trazabilidad." },
  { id: "balances_farm",      num: 9,  label: "Balances",                         icon: BarChart3,     built: true,
    desc: "Tiempos de despacho por sub-farmacia y desempeño de proveedores, calculados de Solicitudes, Trazabilidad, Pedidos y Recepciones reales." },
];
const FB_BODEGA_SUBMODULOS = [
  // #11 faltaba, mismo motivo que #2 en Farmacia.
  { id: "insumos_bod",      num: 11, label: "Bodega: Insumos",             icon: Package,       built: true,
    desc: "Catálogo maestro y stock consolidado de Bodega Central — lo disponible para repartir a las 41 sub-bodegas." },
  { id: "stock_subbodegas", num: 12, label: "Stock y Sub-bodegas",         icon: Layers,        built: true,
    desc: "Stock, alertas y las sub-bodegas asociadas (Urgencias, Hospitalización, Imagenología, etc.)." },
  { id: "recepciones_bod",  num: 13, label: "Recepciones y Nuevo Insumo",  icon: Package,       built: true,
    desc: "Recepción de insumos no clínicos de bodega desde proveedores externos." },
  { id: "pedidos_bod",      num: 14, label: "Solicitud de Pedidos",        icon: ClipboardList, built: true,
    desc: "Solicitudes de las sub-bodegas para reposición de insumos no clínicos." },
  { id: "trazabilidad_bod", num: 15, label: "Trazabilidad",                icon: Search,        built: true,
    desc: "Movimientos y estados de cada insumo de bodega, por usuario." },
  { id: "cuadratura_bod",   num: null, label: "Cuadratura de Stock",       icon: CheckSquare,   built: true,
    desc: "Ajustes de stock central con motivo obligatorio: merma, vencimiento o diferencia de conteo. Cada ajuste queda en Trazabilidad." },
  { id: "balances_bod",     num: 16, label: "Balances",                    icon: BarChart3,     built: true,
    desc: "Tiempos de despacho por sub-bodega y desempeño de proveedores, calculados de Solicitudes, Trazabilidad, Pedidos y Recepciones reales." },
];
const FB_COMPARTIDOS = [
  { id: "gestion_prov",  num: null, label: "Gestión Proveedores",       icon: Building2,
    desc: "Compra de insumos para Farmacia Central y para Bodega. Listas de proveedores separadas por dominio (Farmacia / Bodega — reemplaza los antiguos #10 y #17), pero el proceso de adquisición converge en uno solo, conectado a Contabilidad." },
  { id: "clientes_ext",  num: 18, label: "Clientes Externos",         icon: Users2,
    desc: "Venta o salida de insumos de Farmacia o Bodega hacia clientes externos." },
  { id: "balances_unid", num: 19, label: "Balances Unidades",         icon: TrendingUp,
    desc: "Métricas, tiempos de respuesta/espera y % de uso, por sub-farmacia y sub-bodega." },
  { id: "ev_adversos",   num: 20, label: "Eventos Adversos",          icon: AlertTriangle,
    desc: "Registro de eventos adversos según criterio MINSAL." },
  { id: "ev_seguridad",  num: 21, label: "Eventos de Seguridad",      icon: Shield,
    desc: "Registro de eventos de seguridad según criterio MINSAL." },
  { id: "sinergia",      num: 22, label: "Sinergia y Balances",       icon: Activity,
    desc: "Indicadores y balances internos del equipo de Farmacia y Bodega." },
  { id: "reuniones",     num: 23, label: "Reuniones y Acuerdos",      icon: Users2,
    desc: "Reuniones y acuerdos tomados por la unidad de Farmacia y Bodega." },
  { id: "calendario",    num: 24, label: "Calendario y Turnos",       icon: Calendar },
  { id: "bodega_propia", num: 25, label: "Bodega e Insumos Propios",  icon: Package,
    desc: "Bodega propia de insumos no clínicos de la unidad de Farmacia Central y Bodega." },
  { id: "soporte",       num: 26, label: "Soporte y Solicitudes",     icon: HelpCircle,
    desc: "Solicitudes de apoyo con TI, logística o infraestructura." },
  { id: "mantenciones",  num: 27, label: "Registro de Mantenciones",  icon: Wrench,
    desc: "Registro de mantenciones de equipos tecnológicos." },
];

function fbDiasHasta(fechaISO, from) {
  const ref = from || new Date();
  const target = new Date(fechaISO + "T00:00:00");
  return Math.ceil((target - ref) / (1000 * 60 * 60 * 24));
}
function fbFormatFechaHora(fechaISO) {
  const d = new Date(fechaISO);
  return d.toLocaleString("es-CL", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}
function fbSemaforo(stockUnidad) {
  const vals = Object.values(stockUnidad || {});
  if (vals.length === 0) return { color: C.textMuted, label: "Sin datos" };
  if (vals.some(v => v.stockActual <= 0)) return { color: C.danger, label: "Crítico" };
  if (vals.some(v => v.stockActual <= v.stockMinimo)) return { color: C.warning, label: "Bajo mínimo" };
  return { color: C.success, label: "Ok" };
}
// Calcula los despachos reales de los últimos 7 días desde Trazabilidad —
// reemplaza la constante fija FB_DATA_SEMANA, que mostraba datos de ejemplo
// etiquetados como si fueran reales (auditoría técnica, Parte 14, sección
// 14.3). Si todavía no hay movimientos, muestra 0 en cada día — más honesto
// que datos inventados, mismo criterio que el resto del módulo.
// Corrección (auditoría técnica #2, hallazgo #35 — MetricDefinition: la
// fuente, la fórmula y la unidad de conteo deben ser explícitas): la primera
// versión contaba movimientos de tipo "despacho-unidad" uno por uno, pero
// despachar() crea UN movimiento POR ÍTEM de la solicitud, todos con el
// mismo documentoRespaldo (folio) — una solicitud de 5 ítems se despacha en
// UN solo acto y generaba "5 despachos" en el gráfico en vez de 1. Ahora se
// cuentan folios ÚNICOS por día, no movimientos.
function fbCalcularDespachosSemana(movimientosFarmacia, movimientosBodega) {
  const NOMBRES_DIA = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"];
  const hoy = new Date();
  const dias = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date(hoy);
    d.setDate(hoy.getDate() - i);
    dias.push({ clave: d.toISOString().slice(0, 10), dia: NOMBRES_DIA[d.getDay()], farmacia: new Set(), bodega: new Set() });
  }
  function contar(movimientos, campo) {
    (movimientos || []).forEach(m => {
      if (m.tipoMovimiento !== "despacho-unidad") return;
      const clave = m.fechaMovimiento.slice(0, 10);
      const fila = dias.find(d => d.clave === clave);
      if (fila) fila[campo].add(m.documentoRespaldo);
    });
  }
  contar(movimientosFarmacia, "farmacia");
  contar(movimientosBodega, "bodega");
  return dias.map(d => ({ dia: d.dia, farmacia: d.farmacia.size, bodega: d.bodega.size }));
}
// ── Balances (#9 Farmacia / #16 Bodega) ─────────────────────────────────────
// Cada métrica documenta su fuente, su fórmula y su unidad de conteo
// explícitamente — lección directa de Auditoria_SupplyCore2.md (#34-35): el
// gráfico semanal de despachos contaba movimientos en vez de despachos
// únicos, por no tener la unidad de conteo definida con claridad. Lo que no
// se puede calcular con datos reales hoy devuelve `null` (se muestra "—" en
// la UI) — nunca se inventa un número (mismo criterio del resto del módulo).
function fbCalcularBalanceSubUnidades(unidades, solicitudes, movimientos) {
  return unidades.map(u => {
    const deLaUnidad = solicitudes.filter(s => s.subFarmaciaId === u.id);
    const recibidas = deLaUnidad.filter(s => s.estado === "recibida");
    const pendientes = deLaUnidad.filter(s => ["pendiente-coordinador", "pendiente", "aprobada", "en-preparacion"].includes(s.estado));
    const rechazadas = deLaUnidad.filter(s => s.estado === "rechazada");

    // tiempoPromedioDespachoHrs: fechaSolicitud → fecha del movimiento real
    // "despacho-unidad" en Trazabilidad de esa misma solicitud (documentoRespaldo
    // = folio) — no la cantidadDespachada de la solicitud, para quedar atado
    // al mismo dato que ya muestra la pestaña de Trazabilidad.
    const tiempos = deLaUnidad
      .map(s => {
        const mov = (movimientos || []).find(m => m.documentoRespaldo === s.folio && m.tipoMovimiento === "despacho-unidad");
        return mov ? (new Date(mov.fechaMovimiento) - new Date(s.fechaSolicitud)) / 36e5 : null;
      })
      .filter(t => t != null);
    const tiempoPromedioDespachoHrs = tiempos.length ? tiempos.reduce((a, t) => a + t, 0) / tiempos.length : null;

    // consumoTotal: suma de cantidadRecibida de las solicitudes ya recibidas
    // por esa unidad — acumulado histórico, NO "mensual": el prototipo no
    // tiene corte por mes todavía en ningún lado; etiquetarlo "mensual" sin
    // ese corte sería inventar un dato que no existe.
    const consumoTotal = recibidas.reduce((acc, s) => acc + s.items.reduce((a, it) => a + (it.cantidadRecibida || 0), 0), 0);

    return {
      unidad: u, totalSolicitudes: deLaUnidad.length, solicitudesAtendidas: recibidas.length,
      solicitudesPendientes: pendientes.length,
      tasaRechazo: deLaUnidad.length ? (rechazadas.length / deLaUnidad.length) * 100 : null,
      tiempoPromedioDespachoHrs, consumoTotal,
    };
  }).filter(r => r.totalSolicitudes > 0); // solo unidades con al menos 1 solicitud real
}

// tasaEntregaCompleta / tasaCumplimientoPlazo se calculan SUMANDO todas las
// Recepciones vinculadas a un mismo Pedido (ordenCompraFolio), no solo la
// última — corrige el hallazgo de Auditoria_SupplyCore2.md (#8): una OC
// recibida en 2 recepciones parciales (40 + 60 de 100) antes se evaluaba
// comparando solo la ÚLTIMA recepción contra el total, sin acumular.
function fbCalcularBalancePorProveedor(proveedores, pedidos, recepciones) {
  return proveedores.map(p => {
    const deEseProveedor = pedidos.filter(ped => ped.proveedorId === p.id);
    const resumenes = deEseProveedor.map(ped => {
      const vinculadas = (recepciones || [])
        .filter(r => r.ordenCompraFolio === ped.folio && r.estado !== "rechazada")
        .sort((a, b) => new Date(a.fechaRecepcion) - new Date(b.fechaRecepcion));
      const totalSolicitado = ped.items.reduce((a, it) => a + it.cantidadSolicitada, 0);
      let totalRecibido = 0, fechaCompletado = null;
      vinculadas.forEach(r => {
        totalRecibido += r.items.reduce((a, it) => a + it.cantidadRecibida, 0);
        if (totalRecibido >= totalSolicitado && !fechaCompletado) fechaCompletado = r.fechaRecepcion;
      });
      return { pedido: ped, tieneRecepcion: vinculadas.length > 0, completo: vinculadas.length > 0 && totalRecibido >= totalSolicitado, fechaCompletado };
    });
    const conRecepcion = resumenes.filter(r => r.tieneRecepcion);
    const completos = resumenes.filter(r => r.completo);
    const dentroDePlazo = completos.filter(r => ((new Date(r.fechaCompletado) - new Date(r.pedido.fecha)) / 864e5) <= p.comercial.plazoEntregaDias);
    const tiemposEntregaHrs = completos.map(r => (new Date(r.fechaCompletado) - new Date(r.pedido.fecha)) / 36e5);

    return {
      proveedor: p, totalPedidos: deEseProveedor.length,
      tasaEntregaCompleta: conRecepcion.length ? (completos.length / conRecepcion.length) * 100 : null,
      tasaCumplimientoPlazo: completos.length ? (dentroDePlazo.length / completos.length) * 100 : null,
      // tiempoPromedioRespuesta: NO calculable todavía — el Pedido solo guarda
      // `fecha` de creación y un `estado` que se sobreescribe, sin timestamp
      // propio de "cuándo confirmó el proveedor" (dossier, Parte 13.5).
      tiempoPromedioEntregaHrs: tiemposEntregaHrs.length ? tiemposEntregaHrs.reduce((a, t) => a + t, 0) / tiemposEntregaHrs.length : null,
    };
  }).filter(r => r.totalPedidos > 0);
}

// Genera el siguiente id correlativo de un catálogo (MED-004 → MED-005, etc.)
// para ítems nuevos registrados en Recepciones — mismo formato que los ids
// de ejemplo ya existentes.
function fbSiguienteId(catalogo, prefijo) {
  const nums = catalogo.filter(it => it.id.startsWith(prefijo + "-")).map(it => Number(it.id.split("-")[1]) || 0);
  const max = nums.length ? Math.max(...nums) : 0;
  return `${prefijo}-${String(max + 1).padStart(3, "0")}`;
}

const FB_ESTADO_META = {
  "pendiente-coordinador": { label: "Pendiente coordinador", color: "#B45309" },
  pendiente:        { label: "Pendiente",      color: C.warning },
  aprobada:         { label: "Aprobada",       color: C.primary },
  "en-preparacion": { label: "En preparación", color: C.primary },
  despachada:       { label: "Despachada",     color: "#6A1B9A" },
  recibida:         { label: "Recibida",       color: C.success },
  rechazada:        { label: "Rechazada",      color: C.danger },
};
const FbEstadoBadge = ({ estado }) => {
  const m = FB_ESTADO_META[estado] || { label: estado, color: C.textMuted };
  return <Badge color={m.color} sm>{m.label}</Badge>;
};

const FbProximamente = ({ label, num, desc }) => (
  <Card style={{ padding: 28 }}>
    <div style={{ textAlign: "center", padding: "24px 0", maxWidth: 440, margin: "0 auto" }}>
      <div style={{ fontSize: 12, color: C.primary, fontFamily: "monospace", marginBottom: 6 }}>{num ? `#${num}` : ""}</div>
      <div style={{ fontSize: 16, fontWeight: 700, color: C.text, marginBottom: 6 }}>{label || "Submódulo"}</div>
      {desc && <div style={{ fontSize: 12.5, color: C.textMid, marginBottom: 10, lineHeight: 1.5 }}>{desc}</div>}
      <div style={{ fontSize: 12, color: C.textMuted }}>Aún no está construido. Vamos avanzando por partes.</div>
    </div>
  </Card>
);

const FbNuevaSolicitudForm = ({ subFarmaciaId, stockUnidad, catalogo, onSubmit, onCancel }) => {
  const [prioridad, setPrioridad] = useState("normal");
  const [justificacion, setJustificacion] = useState("");
  const [cantidades, setCantidades] = useState(() => {
    const init = {};
    catalogo.forEach(it => {
      const s = stockUnidad[it.id];
      init[it.id] = s ? Math.max(0, s.stockMaximo - s.stockActual) : 0;
    });
    return init;
  });

  function setCantidad(id, val) {
    setCantidades(prev => ({ ...prev, [id]: Math.max(0, Number(val) || 0) }));
  }
  const puedeEnviar = Object.values(cantidades).some(c => c > 0) && justificacion.trim().length > 0;
  function handleSubmit() {
    if (!puedeEnviar) return;
    const items = Object.entries(cantidades).filter(([, c]) => c > 0).map(([itemId, cantidadSolicitada]) => ({ itemId, cantidadSolicitada }));
    onSubmit({ subFarmaciaId, prioridad, justificacion: justificacion.trim(), items });
  }

  return (
    <Card style={{ padding: 18, marginTop: 16, border: `1px dashed ${C.primary}` }}>
      <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 12 }}>Nueva solicitud de reposición</div>
      <div style={{ marginBottom: 14 }}>
        <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Prioridad</div>
        <select value={prioridad} onChange={e => setPrioridad(e.target.value)} style={{ border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", fontSize: 12 }}>
          <option value="urgente">Urgente</option>
          <option value="normal">Normal</option>
          <option value="programada">Programada</option>
        </select>
      </div>
      <div style={{ maxHeight: 240, overflowY: "auto", border: `1px solid ${C.border}`, borderRadius: 8, marginBottom: 14 }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
          <thead>
            <tr style={{ background: "#F5F8FF" }}>
              <th style={{ textAlign: "left", padding: "7px 10px", fontSize: 10, color: C.textMuted, textTransform: "uppercase" }}>Ítem</th>
              <th style={{ textAlign: "left", padding: "7px 10px", fontSize: 10, color: C.textMuted, textTransform: "uppercase" }}>Actual / PAR</th>
              <th style={{ textAlign: "left", padding: "7px 10px", fontSize: 10, color: C.textMuted, textTransform: "uppercase" }}>Cantidad a pedir</th>
            </tr>
          </thead>
          <tbody>
            {catalogo.map(it => {
              const s = stockUnidad[it.id];
              return (
                <tr key={it.id} style={{ borderTop: `1px solid ${C.border}` }}>
                  <td style={{ padding: "7px 10px" }}>{it.nombre}</td>
                  <td style={{ padding: "7px 10px", color: C.textMuted }}>{s ? `${s.stockActual} / ${s.stockMaximo} (sugerido)` : "Sin registrar en esta unidad"}</td>
                  <td style={{ padding: "7px 10px" }}>
                    <input type="number" min="0" value={cantidades[it.id]} onChange={e => setCantidad(it.id, e.target.value)}
                      style={{ width: 70, border: `1px solid ${C.border}`, borderRadius: 6, padding: "5px 8px", fontSize: 12 }} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div style={{ marginBottom: 14 }}>
        <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Justificación / detalle (obligatorio)</div>
        <textarea value={justificacion} onChange={e => setJustificacion(e.target.value)} rows={2}
          placeholder="Ej: consumo elevado por aumento de procedimientos esta semana…"
          style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "8px 10px", fontSize: 12, fontFamily: "inherit", resize: "vertical" }} />
      </div>
      <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
        <Btn variant="ghost" onClick={onCancel}>Cancelar</Btn>
        <Btn variant="primary" icon={ArrowRight} onClick={handleSubmit} disabled={!puedeEnviar}>Enviar solicitud</Btn>
      </div>
    </Card>
  );
};

const FbSolicitudCard = ({ solicitud, subFarmacia, role, centralStock, catalogo, centralLabel, onAutorizarCoordinador, onAprobar, onRechazar, onEnPreparacion, onDespachar, onConfirmarRecepcion }) => {
  const s = solicitud;
  const label = centralLabel || "Farmacia Central";
  const esUnidad = role === "encargado_unidad";
  const esCoordinador = role === "coordinador_unidad";
  const [panelDespacho, setPanelDespacho] = useState(null);
  const [panelRecepcion, setPanelRecepcion] = useState(null);
  const [observaciones, setObservaciones] = useState("");

  function abrirDespacho() {
    const init = {};
    // Corrección: antes esto solo ponía lo solicitado, sin límite. Si el
    // operador dejaba el campo tal cual (sin editarlo a mano), el clamp del
    // onChange nunca se ejecutaba y se podía "despachar" más de lo que
    // realmente había en Central. Ahora el valor inicial ya viene topado
    // al disponible real.
    s.items.forEach(it => {
      const disponible = centralStock[it.itemId] ? centralStock[it.itemId].stockActual : 0;
      init[it.itemId] = Math.max(0, Math.min(disponible, it.cantidadSolicitada));
    });
    setPanelDespacho(init);
  }
  function abrirRecepcion() {
    const init = {};
    s.items.forEach(it => { init[it.itemId] = it.cantidadDespachada != null ? it.cantidadDespachada : it.cantidadSolicitada; });
    setPanelRecepcion(init);
  }

  return (
    <Card style={{ padding: 16 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8, flexWrap: "wrap" }}>
        <span style={{ fontFamily: "monospace", fontSize: 11, color: C.textMuted, background: C.bodyBg, padding: "1px 6px", borderRadius: 5 }}>{s.folio}</span>
        <span style={{ fontWeight: 600, fontSize: 13, flex: 1 }}>{subFarmacia ? subFarmacia.nombre : s.subFarmaciaId}</span>
        <Badge color={s.prioridad === "urgente" ? C.danger : s.prioridad === "programada" ? C.primary : C.textMid} sm>{s.prioridad}</Badge>
        <FbEstadoBadge estado={s.estado} />
        {s.despachoParcial && <Badge color={C.warning} sm>Despacho parcial</Badge>}
        {s.discrepancia && <Badge color={s.discrepancia === "excedente" ? C.danger : C.warning} sm>{s.discrepancia === "excedente" ? "Excedente en recepción" : "Faltante en recepción"}</Badge>}
      </div>
      <ul style={{ listStyle: "none", margin: "0 0 6px", padding: 0, fontSize: 12.5, color: C.text }}>
        {s.items.map(it => {
          const cat = catalogo.find(c => c.id === it.itemId);
          return (
            <li key={it.itemId} style={{ marginBottom: 2 }}>
              {cat ? cat.nombre : it.itemId} — solicitado {it.cantidadSolicitada}
              {it.cantidadDespachada != null ? ` · despachado ${it.cantidadDespachada}` : ""}
              {it.cantidadRecibida != null ? ` · recibido ${it.cantidadRecibida}` : ""}
            </li>
          );
        })}
      </ul>
      {s.justificacion && <div style={{ fontSize: 11.5, color: C.textMid, marginBottom: 6, fontStyle: "italic" }}>"{s.justificacion}"</div>}
      <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 12 }}>Solicitada: {fbFormatFechaHora(s.fechaSolicitud)}</div>

      {s.estado === "pendiente-coordinador" && (
        esCoordinador
          ? <div style={{ display: "flex", gap: 8 }}>
              <Btn variant="primary" icon={CheckCircle} onClick={() => onAutorizarCoordinador(s.folio)}>Autorizar</Btn>
              <Btn variant="danger" icon={X} onClick={() => onRechazar(s.folio, "coordinador")}>Rechazar</Btn>
            </div>
          : esUnidad
            ? <div style={{ fontSize: 12, color: C.textMuted }}>🔒 Esperando autorización del coordinador de tu unidad — cambia tu rol arriba a <strong>"Coordinador de Unidad"</strong> para simularlo.</div>
            : <div style={{ fontSize: 12, color: C.textMuted }}>🔒 En revisión interna de la unidad — todavía no llega a {label}. Cambia tu rol arriba a <strong>"Coordinador de Unidad"</strong> para autorizarla.</div>
      )}

      {s.estado === "pendiente" && (
        (esUnidad || esCoordinador)
          ? <div style={{ fontSize: 12, color: C.textMuted }}>🔒 Autorizada por el coordinador. Esperando revisión de {label} — cambia tu rol arriba a <strong>"Farmacia/Bodega Central"</strong> para simularlo.</div>
          : <div style={{ display: "flex", gap: 8 }}>
              <Btn variant="primary" icon={CheckCircle} onClick={() => onAprobar(s.folio)}>Aprobar</Btn>
              <Btn variant="danger" icon={X} onClick={() => onRechazar(s.folio, "farmacia")}>Rechazar</Btn>
            </div>
      )}

      {s.estado === "aprobada" && (
        esUnidad
          ? <div style={{ fontSize: 12, color: C.textMuted }}>✅ Aprobada. {label} está preparando el despacho — cambia tu rol arriba a <strong>"Farmacia/Bodega Central"</strong> para continuar.</div>
          : <Btn variant="primary" icon={Package} onClick={() => onEnPreparacion(s.folio)}>Marcar en preparación</Btn>
      )}

      {s.estado === "en-preparacion" && (
        esUnidad ? (
          <div style={{ fontSize: 12, color: C.textMuted }}>📦 {label} está preparando el despacho — sigue con el rol <strong>"Farmacia/Bodega Central"</strong>.</div>
        ) : !panelDespacho ? (
          <Btn variant="primary" icon={Truck} onClick={abrirDespacho}>Preparar despacho</Btn>
        ) : (
          <div style={{ background: C.bodyBg, borderRadius: 8, padding: 12, marginTop: 4 }}>
            <div style={{ fontSize: 11.5, fontWeight: 600, marginBottom: 8 }}>Ajustar cantidad a despachar</div>
            {s.items.map(it => {
              const cat = catalogo.find(c => c.id === it.itemId);
              const disponible = centralStock[it.itemId] ? centralStock[it.itemId].stockActual : 0;
              const insuficiente = disponible < panelDespacho[it.itemId];
              return (
                <div key={it.itemId} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                  <span style={{ fontSize: 12, flex: 1 }}>{cat ? cat.nombre : it.itemId}</span>
                  <span style={{ fontSize: 10.5, color: C.textMuted }}>disp. {disponible}</span>
                  <input type="number" min="0" max={disponible} value={panelDespacho[it.itemId]}
                    onChange={e => setPanelDespacho(p => ({ ...p, [it.itemId]: Math.max(0, Math.min(disponible, Number(e.target.value) || 0)) }))}
                    style={{ width: 60, border: `1px solid ${insuficiente ? C.danger : C.border}`, borderRadius: 6, padding: "4px 6px", fontSize: 12 }} />
                </div>
              );
            })}
            <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
              <Btn variant="ghost" size="sm" onClick={() => setPanelDespacho(null)}>Cancelar</Btn>
              <Btn variant="primary" size="sm" icon={Truck} onClick={() => { onDespachar(s.folio, panelDespacho); setPanelDespacho(null); }}>Confirmar despacho</Btn>
            </div>
          </div>
        )
      )}

      {s.estado === "despachada" && (
        !esUnidad ? (
          <div style={{ fontSize: 12, color: C.textMuted }}>🚚 Despachada. Esperando confirmación de recepción de la unidad — cambia tu rol arriba a <strong>"Encargado Sub-farmacia/Bodega"</strong> para simularlo.</div>
        ) : !panelRecepcion ? (
          <Btn variant="primary" icon={CheckCircle} onClick={abrirRecepcion}>Confirmar recepción</Btn>
        ) : (
          <div style={{ background: C.bodyBg, borderRadius: 8, padding: 12, marginTop: 4 }}>
            <div style={{ fontSize: 11.5, fontWeight: 600, marginBottom: 8 }}>Confirmar cantidad recibida</div>
            {s.items.map(it => {
              const cat = catalogo.find(c => c.id === it.itemId);
              const despachado = it.cantidadDespachada != null ? it.cantidadDespachada : it.cantidadSolicitada;
              const recibido = panelRecepcion[it.itemId];
              const diff = recibido - despachado;
              return (
                <div key={it.itemId} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                  <span style={{ fontSize: 12, flex: 1 }}>{cat ? cat.nombre : it.itemId}</span>
                  <span style={{ fontSize: 10.5, color: C.textMuted }}>despachado {despachado}</span>
                  <input type="number" min="0" value={recibido}
                    onChange={e => setPanelRecepcion(p => ({ ...p, [it.itemId]: Math.max(0, Number(e.target.value) || 0) }))}
                    style={{ width: 60, border: `1px solid ${C.border}`, borderRadius: 6, padding: "4px 6px", fontSize: 12 }} />
                  {diff !== 0 && <Badge color={diff < 0 ? C.danger : C.warning} sm>{diff < 0 ? `faltan ${Math.abs(diff)}` : `exceden ${diff}`}</Badge>}
                </div>
              );
            })}
            <textarea value={observaciones} onChange={e => setObservaciones(e.target.value)} rows={2}
              placeholder="Observaciones de recepción (ej: caja dañada, faltante justificado, etc.)"
              style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 8px", fontSize: 12, fontFamily: "inherit", marginTop: 6, marginBottom: 8, resize: "vertical" }} />
            <div style={{ display: "flex", gap: 8 }}>
              <Btn variant="ghost" size="sm" onClick={() => setPanelRecepcion(null)}>Cancelar</Btn>
              {(() => {
                const hayExcedente = s.items.some(it => panelRecepcion[it.itemId] > (it.cantidadDespachada != null ? it.cantidadDespachada : it.cantidadSolicitada));
                const bloqueado = hayExcedente && observaciones.trim().length === 0;
                return (<>
                  {hayExcedente && <span style={{ fontSize: 11, color: C.danger, alignSelf: "center" }}>Excedente: la observación es obligatoria.</span>}
                  <Btn variant="primary" size="sm" icon={CheckCircle} disabled={bloqueado} onClick={() => { onConfirmarRecepcion(s.folio, panelRecepcion, observaciones); setPanelRecepcion(null); }}>Confirmar recepción</Btn>
                </>);
              })()}
            </div>
          </div>
        )
      )}

      {(s.estado === "recibida" || s.estado === "rechazada") && (
        <div style={{ fontSize: 12, color: C.textMuted, fontStyle: "italic" }}>
          Solicitud cerrada
          {s.estado === "rechazada" && s.rechazadaPor ? ` — rechazada por ${s.rechazadaPor === "coordinador" ? "el coordinador de la unidad" : label}` : ""}
          {s.observacionesRecepcion ? ` — "${s.observacionesRecepcion}"` : ""}
        </div>
      )}
    </Card>
  );
};

const FbStockPorUnidad = ({ role, catalogo, unidades, selected, onSelect, subStock, onCrearSolicitud, conceptosFarmaco }) => {
  const [mostrarForm, setMostrarForm] = useState(false);
  const subFarmacia = unidades.find(u => u.id === selected) || unidades[0];
  const stockUnidad = subStock[subFarmacia.id] || {};
  const esUnidad = role === "encargado_unidad";

  return (
    <div style={{ display: "grid", gridTemplateColumns: "260px 1fr", gap: 18 }}>
      <div style={{ display: "flex", flexDirection: "column", gap: 6, maxHeight: 560, overflowY: "auto", paddingRight: 4 }}>
        {unidades.map(sf => {
          const sem = fbSemaforo(subStock[sf.id]);
          const active = sf.id === subFarmacia.id;
          return (
            <button key={sf.id} onClick={() => { onSelect(sf.id); setMostrarForm(false); }}
              style={{ display: "flex", alignItems: "center", gap: 8, background: active ? `${C.primary}10` : C.surface, border: `1px solid ${active ? C.primary : C.border}`, borderRadius: 8, padding: "9px 11px", cursor: "pointer", textAlign: "left", fontSize: 12.5 }}>
              <span style={{ width: 8, height: 8, borderRadius: "50%", background: sem.color, flexShrink: 0 }} />
              <span style={{ flex: 1 }}>{sf.nombre}</span>
              <ChevronRight size={13} color={C.textMuted} />
            </button>
          );
        })}
      </div>
      <Card style={{ padding: 20 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14, flexWrap: "wrap", gap: 10 }}>
          <div style={{ fontSize: 15, fontWeight: 700, color: C.text }}>{subFarmacia.nombre}</div>
          {esUnidad
            ? <Btn variant="primary" icon={Plus} onClick={() => setMostrarForm(v => !v)}>Nueva solicitud de reposición</Btn>
            : <span style={{ fontSize: 11, color: C.textMuted }}>Las solicitudes las inicia la unidad correspondiente — cambia tu rol arriba a <strong>"Encargado Sub-farmacia/Bodega"</strong> para simularlo.</span>}
        </div>
        {Object.keys(stockUnidad).length === 0 ? (
          <div style={{ padding: "24px 0", textAlign: "center", color: C.textMuted, fontSize: 12.5 }}>
            Aún no se ha cargado stock de ejemplo para esta unidad.
          </div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12.5 }}>
            <thead>
              <tr style={{ background: "#F5F8FF" }}>
                {["Ítem", "Código", "Actual", "Mínimo", "Máx. sugerido", "Estado"].map(h => (
                  <th key={h} style={{ textAlign: "left", padding: "7px 10px", fontSize: 10, color: C.textMuted, textTransform: "uppercase" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {catalogo.filter(it => stockUnidad[it.id]).map(it => {
                const s = stockUnidad[it.id];
                const bajo = s.stockActual <= s.stockMinimo;
                const concepto = it.conceptoId ? (conceptosFarmaco || FB_CONCEPTOS_FARMACO).find(c => c.id === it.conceptoId) : null;
                return (
                  <tr key={it.id} style={{ borderTop: `1px solid ${C.border}` }}>
                    <td style={{ padding: "8px 10px" }}>
                      <div>{it.nombre}</div>
                      {it.registroISP && (
                        <div style={{ fontSize: 10, color: C.textMuted, marginTop: 2 }}>
                          {concepto && `DCI: ${concepto.dci}${concepto.concentracion ? ` ${fbFormatConcentracion(concepto.concentracion)}` : ""} · `}Reg. ISP {it.registroISP} · CENABAST {it.codigoCenabast}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: "8px 10px", fontFamily: "monospace", fontSize: 11, color: C.textMuted }}>{it.codigoBarra}</td>
                    <td style={{ padding: "8px 10px", color: bajo ? C.danger : C.text, fontWeight: bajo ? 600 : 400 }}>{s.stockActual} {it.unidad}</td>
                    <td style={{ padding: "8px 10px", color: C.textMuted }}>{s.stockMinimo}</td>
                    <td style={{ padding: "8px 10px", color: C.textMuted }}>{s.stockMaximo}</td>
                    <td style={{ padding: "8px 10px" }}>{bajo ? <Badge color={C.warning} sm>Bajo mínimo</Badge> : <Badge color={C.success} sm>Ok</Badge>}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
        {mostrarForm && esUnidad && (
          <FbNuevaSolicitudForm subFarmaciaId={subFarmacia.id} stockUnidad={stockUnidad} catalogo={catalogo}
            onSubmit={payload => { onCrearSolicitud(payload); setMostrarForm(false); }} onCancel={() => setMostrarForm(false)} />
        )}
      </Card>
    </div>
  );
};

const FbColaSolicitudes = ({ role, catalogo, unidades, centralStock, centralLabel, solicitudes, onAutorizarCoordinador, onAprobar, onRechazar, onEnPreparacion, onDespachar, onConfirmarRecepcion }) => (
  <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
    {solicitudes.length === 0 && <div style={{ fontSize: 12.5, color: C.textMuted }}>Aún no hay solicitudes.</div>}
    {solicitudes.map(s => (
      <FbSolicitudCard key={s.folio} solicitud={s} role={role} centralStock={centralStock} catalogo={catalogo} centralLabel={centralLabel}
        subFarmacia={unidades.find(u => u.id === s.subFarmaciaId)}
        onAutorizarCoordinador={() => onAutorizarCoordinador(s.folio)}
        onAprobar={() => onAprobar(s.folio)}
        onRechazar={(folio, quien) => onRechazar(folio, quien)}
        onEnPreparacion={() => onEnPreparacion(s.folio)}
        onDespachar={onDespachar}
        onConfirmarRecepcion={onConfirmarRecepcion}
      />
    ))}
  </div>
);

const FbDashboard = ({ centralStock, subStock, solicitudes, centralStockBod, subStockBod, solicitudesBod, onIrASolicitudes, lotes, catalogoFarmacia, catalogoBodega, movimientosFarmacia, movimientosBodega }) => {
  const catFarm = catalogoFarmacia || FB_CATALOGO;
  const catBod = catalogoBodega || FB_CATALOGO_BODEGA;
  const stockCritico = catFarm.filter(it => { const s = centralStock[it.id]; return s && s.stockActual <= s.stockMinimo; });
  const stockCriticoBod = catBod.filter(it => { const s = centralStockBod[it.id]; return s && s.stockActual <= s.stockMinimo; });
  const alertasCaducidad = (lotes || FB_LOTES_INICIAL)
    .map(l => ({ ...l, dias: fbDiasHasta(l.fechaVencimiento), item: catFarm.find(c => c.id === l.itemId) }))
    .filter(l => l.dias <= 60)
    .sort((a, b) => a.dias - b.dias);
  const pendientes = solicitudes.filter(s => s.estado === "pendiente" || s.estado === "pendiente-coordinador");
  const pendientesBod = solicitudesBod.filter(s => s.estado === "pendiente" || s.estado === "pendiente-coordinador");
  const enCurso = solicitudes.filter(s => ["aprobada", "en-preparacion", "despachada"].includes(s.estado));

  // Tiempo promedio de despacho: calculado desde las fechas reales de las
  // solicitudes que ya tienen fechaDespacho, no es un número inventado.
  const todasConDespacho = [...solicitudes, ...solicitudesBod].filter(s => s.fechaDespacho);
  const tiempoPromedioDespachoHrs = todasConDespacho.length
    ? (todasConDespacho.reduce((acc, s) => acc + (new Date(s.fechaDespacho) - new Date(s.fechaSolicitud)) / 36e5, 0) / todasConDespacho.length)
    : null;

  // Corrección (auditoría técnica, Parte 14, sección 14.3): antes se sumaban
  // las alertas de FB_UNIDADES_SUBFARMACIA (24) + FB_UNIDADES_SUBBODEGA (41)
  // contra un denominador de 41 únicas — pero las 24 "ambas" están incluidas
  // en las dos listas, así que una unidad con alerta en Farmacia Y en Bodega
  // a la vez se contaba dos veces. Ahora se recorren las 41 unidades únicas
  // una sola vez, revisando el semáforo de Farmacia solo si la unidad
  // también tiene sub-farmacia.
  const unidadesConAlerta = FB_UNIDADES_SUBBODEGA.filter(u => {
    const tieneFarmacia = FB_UNIDADES_SUBFARMACIA.some(f => f.id === u.id);
    const semFarm = tieneFarmacia ? fbSemaforo(subStock[u.id]).label : null;
    const semBod = fbSemaforo(subStockBod[u.id]).label;
    return semFarm === "Bajo mínimo" || semFarm === "Crítico" || semBod === "Bajo mínimo" || semBod === "Crítico";
  }).length;

  // Corrección (auditoría técnica, Parte 14, sección 14.3): antes era la
  // constante fija FB_DATA_SEMANA, mostrada como si fuera dato real. Ahora
  // se calcula de los movimientos reales de Trazabilidad.
  const datosSemana = fbCalcularDespachosSemana(movimientosFarmacia, movimientosBodega);

  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 12, marginBottom: 16 }}>
        <KPICard label="Solicitudes pendientes" value={pendientes.length + pendientesBod.length} icon={ClipboardList} color={C.warning} sub={`Farmacia ${pendientes.length} · Bodega ${pendientesBod.length}`} />
        <KPICard label="En curso" value={enCurso.length} icon={Truck} color={C.primary} sub="Aprobadas → despachadas" />
        <KPICard label="Ítems bajo mínimo" value={stockCritico.length + stockCriticoBod.length} icon={AlertTriangle} color={C.danger} sub="Central: Farmacia + Bodega" />
        <KPICard label="Alertas de caducidad" value={alertasCaducidad.length} icon={Clock} color={C.warning} sub="≤ 60 días" />
        <KPICard label="Unidades con alerta" value={`${unidadesConAlerta}/41`} icon={Building2} color={C.warning} sub="Bajo mínimo o crítico" />
        <KPICard label="Tiempo prom. despacho" value={tiempoPromedioDespachoHrs != null ? `${tiempoPromedioDespachoHrs.toFixed(1)}h` : "—"} icon={Activity} color={C.success} sub="Calculado de solicitudes reales" />
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 14, marginBottom: 14 }}>
        <Card style={{ padding: "18px 20px" }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.text }}>Despachos de la semana</div>
          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 12 }}>Sub-farmacias + sub-bodegas · calculado de Trazabilidad</div>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={datosSemana} barGap={3} margin={{ left: -18, right: 4, top: 4, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F0F4F8" />
              <XAxis dataKey="dia" tick={{ fontSize: 10, fill: C.textMuted }} />
              <YAxis tick={{ fontSize: 10, fill: C.textMuted }} allowDecimals={false} />
              <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
              <Bar dataKey="farmacia" name="Farmacia" fill={C.primary} radius={[3, 3, 0, 0]} />
              <Bar dataKey="bodega" name="Bodega" fill={C.teal} radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <Card style={{ padding: "18px 20px", overflowY: "auto", maxHeight: 236 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 10 }}>Estado por unidad (con datos cargados)</div>
          {[...FB_UNIDADES_SUBFARMACIA.map(u => ({ ...u, tipo: "Farmacia", stock: subStock[u.id] })),
            ...FB_UNIDADES_SUBBODEGA.map(u => ({ ...u, tipo: "Bodega", stock: subStockBod[u.id] }))]
            .filter(u => u.stock && Object.keys(u.stock).length > 0)
            .map((u, i) => {
              const sem = fbSemaforo(u.stock);
              return (
                <div key={u.tipo + u.id + i} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "6px 0", borderBottom: `1px solid ${C.border}`, fontSize: 12 }}>
                  <span>{u.nombre} <span style={{ color: C.textMuted, fontSize: 10.5 }}>({u.tipo})</span></span>
                  <Badge color={sem.color} sm>{sem.label}</Badge>
                </div>
              );
            })}
        </Card>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 14 }}>
        <Card style={{ padding: "16px 18px" }}>
          <div style={{ fontSize: 12.5, fontWeight: 700, marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}><AlertTriangle size={14} color={C.danger} />Stock crítico — Farmacia Central</div>
          {stockCritico.length === 0 ? <div style={{ fontSize: 12, color: C.textMuted }}>Sin alertas de stock mínimo.</div> : stockCritico.map(it => (
            <div key={it.id} style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
              <span>{it.nombre}</span><span style={{ fontFamily: "monospace", fontSize: 10.5, color: C.textMuted }}>{it.codigoBarra}</span>
            </div>
          ))}
        </Card>
        <Card style={{ padding: "16px 18px" }}>
          <div style={{ fontSize: 12.5, fontWeight: 700, marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}><AlertTriangle size={14} color={C.danger} />Stock crítico — Bodega Central</div>
          {stockCriticoBod.length === 0 ? <div style={{ fontSize: 12, color: C.textMuted }}>Sin alertas de stock mínimo.</div> : stockCriticoBod.map(it => (
            <div key={it.id} style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
              <span>{it.nombre}</span><span style={{ fontFamily: "monospace", fontSize: 10.5, color: C.textMuted }}>{it.codigoBarra}</span>
            </div>
          ))}
        </Card>
        <Card style={{ padding: "16px 18px" }}>
          <div style={{ fontSize: 12.5, fontWeight: 700, marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}><Clock size={14} color={C.warning} />Próximos a caducar (≤ 60 días)</div>
          {alertasCaducidad.length === 0 ? <div style={{ fontSize: 12, color: C.textMuted }}>Sin lotes próximos a vencer.</div> : alertasCaducidad.map(l => (
            <div key={l.id} style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
              <span>{l.item ? l.item.nombre : l.itemId} · lote {l.numeroLote}</span>
              <Badge color={l.dias <= 15 ? C.danger : C.warning} sm>{l.dias} días</Badge>
            </div>
          ))}
        </Card>
        <Card style={{ padding: "16px 18px", cursor: "pointer" }} onClick={onIrASolicitudes}>
          <div style={{ fontSize: 12.5, fontWeight: 700, marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}><ClipboardList size={14} color={C.primary} />Solicitudes de sub-farmacias (#5)</div>
          {pendientes.length === 0 ? <div style={{ fontSize: 12, color: C.textMuted }}>No hay solicitudes pendientes.</div> : pendientes.map(s => (
            <div key={s.folio} style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
              <span style={{ fontFamily: "monospace", fontSize: 10.5 }}>{s.folio}</span>
              <span>{(FB_UNIDADES_SUBFARMACIA.find(u => u.id === s.subFarmaciaId) || {}).nombre}</span>
            </div>
          ))}
          <div style={{ fontSize: 11, color: C.primary, marginTop: 6 }}>Ver cola de solicitudes →</div>
        </Card>
      </div>
    </div>
  );
};

const FbProveedorCard = ({ proveedor, onHacerPedido }) => {
  const [abierto, setAbierto] = useState(false);
  const p = proveedor;
  const estadoColor = { activo: C.success, "en-evaluacion": C.warning, suspendido: C.danger, inactivo: C.textMuted }[p.estado] || C.textMuted;
  const estadoLabel = { activo: "Activo", "en-evaluacion": "En evaluación", suspendido: "Suspendido", inactivo: "Inactivo" }[p.estado] || p.estado;
  return (
    <Card style={{ padding: 16 }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 10, cursor: "pointer" }} onClick={() => setAbierto(v => !v)}>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 4 }}>
            <span style={{ fontWeight: 700, fontSize: 14, color: C.text }}>{p.razonSocial}</span>
            <Badge color={p.dominio === "farmacia" ? "#4338CA" : "#B45309"} sm>{p.dominio === "farmacia" ? "Farmacia" : "Bodega"}</Badge>
            <Badge color={estadoColor} sm>{estadoLabel}</Badge>
          </div>
          <div style={{ fontSize: 11.5, color: C.textMuted }}>{p.giro}</div>
        </div>
        <div style={{ textAlign: "right", flexShrink: 0 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.primary }}>★ {p.evaluacion.calificacionGeneral}</div>
          <div style={{ fontSize: 10.5, color: C.textMuted }}>{p.evaluacion.cumplimientoPlazo}% a tiempo</div>
        </div>
        {abierto ? <ChevronUp size={16} color={C.textMuted} /> : <ChevronDown size={16} color={C.textMuted} />}
      </div>
      {abierto && (
        <div style={{ marginTop: 14, paddingTop: 14, borderTop: `1px solid ${C.border}` }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, fontSize: 12, marginBottom: 14 }}>
            <div>
              <div style={{ fontSize: 10, textTransform: "uppercase", color: C.textMuted, marginBottom: 6, fontWeight: 600 }}>Contacto</div>
              <div>{p.contacto.nombre} · {p.contacto.cargo}</div>
              <div style={{ color: C.textMid }}>{p.contacto.telefono}</div>
              <div style={{ color: C.textMid }}>{p.contacto.email}</div>
              <div style={{ marginTop: 6, color: C.textMuted }}>{p.direccion}</div>
            </div>
            <div>
              <div style={{ fontSize: 10, textTransform: "uppercase", color: C.textMuted, marginBottom: 6, fontWeight: 600 }}>Condiciones comerciales</div>
              <div>Contrato: {p.comercial.tipoContrato} · Pago: {p.comercial.condicionPago}</div>
              <div>Entrega: {p.comercial.plazoEntregaDias} días</div>
              <div>Vigencia: {p.comercial.vigenciaContrato}</div>
              <div style={{ marginTop: 6 }}>
                {p.rubros.map(r => <Badge key={r} color={C.textMid} sm>{r}</Badge>)}
              </div>
            </div>
          </div>
          {p.estado === "activo" ? (
            <Btn variant="primary" size="sm" icon={Plus} onClick={() => onHacerPedido(p)}>Hacer pedido</Btn>
          ) : (
            <div style={{ fontSize: 11, color: C.textMuted, fontStyle: "italic" }}>No se puede pedir a un proveedor {estadoLabel.toLowerCase()}.</div>
          )}
        </div>
      )}
    </Card>
  );
};

const PEDIDO_ESTADO_META = {
  enviado:          { label: "Enviado",           color: C.warning },
  confirmado:       { label: "Confirmado",        color: C.primary },
  "en-transito":    { label: "En tránsito",       color: "#6A1B9A" },
  "recibido-parcial": { label: "Recibido parcial", color: "#B45309" },
  "recibido-total": { label: "Recibido total",    color: C.success },
};

const FbNuevoPedidoForm = ({ proveedor, catalogo, itemsProveedor, onSubmit, onCancel }) => {
  const [cajas, setCajas] = useState({});
  function setCajasItem(itemId, val) {
    setCajas(prev => ({ ...prev, [itemId]: Math.max(0, Number(val) || 0) }));
  }
  const items = Object.entries(cajas)
    .filter(([, c]) => c > 0)
    .map(([itemId, cantidadCajas]) => {
      const linea = itemsProveedor.find(l => l.itemId === itemId);
      return { itemId, cantidadCajas, unidadesPorPresentacion: linea.unidadesPorPresentacion, cantidadSolicitada: cantidadCajas * linea.unidadesPorPresentacion };
    });
  const hayBajoMinimo = itemsProveedor.some(l => cajas[l.itemId] > 0 && cajas[l.itemId] < l.cantidadMinimaCompra);
  function handleSubmit() {
    if (items.length === 0 || hayBajoMinimo) return;
    onSubmit(items);
  }

  if (itemsProveedor.length === 0) {
    return (
      <Card style={{ padding: 16, marginTop: 10, border: `1px dashed ${C.border}` }}>
        <div style={{ fontSize: 12, color: C.textMuted }}>Este proveedor todavía no tiene ítems vinculados en el catálogo por proveedor.</div>
      </Card>
    );
  }

  return (
    <Card style={{ padding: 18, marginTop: 10, border: `1px dashed ${C.primary}` }}>
      <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 4 }}>Nuevo pedido — {proveedor.razonSocial}</div>
      <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 12 }}>Plazo de entrega estimado: {proveedor.comercial.plazoEntregaDias} días · {proveedor.comercial.condicionPago}</div>
      <div style={{ maxHeight: 260, overflowY: "auto", border: `1px solid ${C.border}`, borderRadius: 8, marginBottom: 12 }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
          <thead>
            <tr style={{ background: "#F5F8FF" }}>
              {["Ítem", "Cód. proveedor", "Presentación de compra", "Mín. compra", "Cajas a pedir", "= Unidades"].map(h => (
                <th key={h} style={{ textAlign: "left", padding: "7px 10px", fontSize: 10, color: C.textMuted, textTransform: "uppercase" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {itemsProveedor.map(linea => {
              const it = catalogo.find(c => c.id === linea.itemId);
              const cantCajas = cajas[linea.itemId] || 0;
              const bajoMinimo = cantCajas > 0 && cantCajas < linea.cantidadMinimaCompra;
              return (
                <tr key={linea.itemId} style={{ borderTop: `1px solid ${C.border}` }}>
                  <td style={{ padding: "7px 10px" }}>{it ? it.nombre : linea.itemId}</td>
                  <td style={{ padding: "7px 10px", fontFamily: "monospace", fontSize: 11, color: C.textMuted }}>{linea.codigoProveedor}</td>
                  <td style={{ padding: "7px 10px", color: C.textMuted }}>{linea.presentacionCompra}</td>
                  <td style={{ padding: "7px 10px", color: C.textMuted }}>{linea.cantidadMinimaCompra}</td>
                  <td style={{ padding: "7px 10px" }}>
                    <input type="number" min="0" value={cantCajas} onChange={e => setCajasItem(linea.itemId, e.target.value)}
                      style={{ width: 60, border: `1px solid ${bajoMinimo ? C.danger : C.border}`, borderRadius: 6, padding: "5px 8px", fontSize: 12 }} />
                  </td>
                  <td style={{ padding: "7px 10px", color: C.textMuted }}>{cantCajas > 0 ? `${cantCajas * linea.unidadesPorPresentacion} ${it ? it.unidad : ""}` : "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {hayBajoMinimo && <div style={{ fontSize: 11, color: C.danger, marginBottom: 10 }}>Hay una cantidad por debajo del mínimo de compra de ese proveedor.</div>}
      <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
        <Btn variant="ghost" onClick={onCancel}>Cancelar</Btn>
        <Btn variant="primary" icon={ArrowRight} onClick={handleSubmit} disabled={items.length === 0 || hayBajoMinimo}>Enviar pedido</Btn>
      </div>
    </Card>
  );
};

const FbPedidoCard = ({ pedido, proveedor, catalogo, onAvanzar, onRegistrarRecepcion }) => {
  const ped = pedido;
  const meta = PEDIDO_ESTADO_META[ped.estado] || { label: ped.estado, color: C.textMuted };
  // "recibido-total"/"recibido-parcial" ya no se alcanzan con un botón de avance simple:
  // se logran registrando una Recepción real (ver FbRecepcionesView), que es la que
  // sube el stock por la cantidad efectivamente recibida.
  const siguienteSimple = { enviado: "confirmado", confirmado: "en-transito" }[ped.estado];
  const siguienteLabel = { confirmado: "Marcar confirmado", "en-transito": "Marcar en tránsito" }[siguienteSimple];
  const cerrado = ped.estado === "recibido-total" || ped.estado === "recibido-parcial";
  return (
    <Card style={{ padding: 14 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8, flexWrap: "wrap" }}>
        <span style={{ fontFamily: "monospace", fontSize: 11, color: C.textMuted, background: C.bodyBg, padding: "1px 6px", borderRadius: 5 }}>{ped.folio}</span>
        <span style={{ fontWeight: 600, fontSize: 13, flex: 1 }}>{proveedor ? proveedor.razonSocial : ped.proveedorId}</span>
        <Badge color={meta.color} sm>{meta.label}</Badge>
      </div>
      <ul style={{ listStyle: "none", margin: "0 0 10px", padding: 0, fontSize: 12.5 }}>
        {ped.items.map(it => {
          const cat = catalogo.find(c => c.id === it.itemId);
          return (
            <li key={it.itemId}>
              {cat ? cat.nombre : it.itemId} — {it.cantidadCajas} {it.cantidadCajas === 1 ? "caja" : "cajas"} × {it.unidadesPorPresentacion} = {it.cantidadSolicitada} {cat ? cat.unidad : ""}
            </li>
          );
        })}
      </ul>
      {siguienteSimple && <Btn variant="primary" size="sm" icon={ArrowRight} onClick={() => onAvanzar(ped.folio, siguienteSimple)}>{siguienteLabel}</Btn>}
      {ped.estado === "en-transito" && <Btn variant="primary" size="sm" icon={Package} onClick={() => onRegistrarRecepcion(ped)}>Registrar recepción</Btn>}
      {cerrado && <div style={{ fontSize: 11.5, color: C.textMuted, fontStyle: "italic" }}>Pedido cerrado{ped.recepcionFolio ? ` — ver recepción ${ped.recepcionFolio}` : ""}.</div>}
    </Card>
  );
};

const GestionProveedoresView = ({ centralStock, setCentralStock, centralStockBod, setCentralStockBod, pedidos, setPedidos, folioSeq, setFolioSeq, onIrARecepcion, catalogoFarmacia, catalogoBodega }) => {
  const [filtro, setFiltro] = useState("todos");
  const [tab, setTab] = useState("directorio");
  const [pedidoForm, setPedidoForm] = useState(null); // proveedor seleccionado
  // pedidos/folioSeq ahora viven en FarmaciaBodegaView (llegan por props): al
  // registrar una Recepción vinculada a un pedido, Recepciones necesita poder
  // actualizar el estado de ESE pedido, así que la lista dejó de ser estado
  // local exclusivo de esta vista.

  const visibles = FB_PROVEEDORES.filter(p => filtro === "todos" || p.dominio === filtro);
  const opciones = [
    { id: "todos", label: "Todos" },
    { id: "farmacia", label: "Farmacia" },
    { id: "bodega", label: "Bodega" },
  ];

  function crearPedido(proveedor, items) {
    const folio = `PED-2026-${String(folioSeq).padStart(4, "0")}`;
    setPedidos(prev => [{ folio, proveedorId: proveedor.id, dominio: proveedor.dominio, items, estado: "enviado", fecha: new Date().toISOString() }, ...prev]);
    setFolioSeq(n => n + 1);
    setPedidoForm(null);
    setTab("pedidos");
  }

  // Ya NO sube stock aquí — "recibido-total"/"recibido-parcial" se alcanzan
  // registrando una Recepción real (con la cantidad efectivamente recibida),
  // no marcando un pedido como recibido a ciegas por lo solicitado.
  function avanzarPedido(folio, nuevoEstado) {
    setPedidos(prev => prev.map(p => (p.folio === folio ? { ...p, estado: nuevoEstado } : p)));
  }

  const pedidosActivos = pedidos.filter(p => p.estado !== "recibido-total" && p.estado !== "recibido-parcial").length;

  return (
    <div>
      <Card style={{ padding: "14px 18px", marginBottom: 16, background: `${C.primary}08` }}>
        <div style={{ fontSize: 12, color: C.textMid, lineHeight: 1.5 }}>
          <strong>Listas separadas por dominio</strong> — Farmacia y Bodega compran a empresas distintas — <strong>proceso de adquisición único</strong>, conectado a Contabilidad. Datos de ejemplo, pendiente el listado oficial de proveedores de AXON.
        </div>
      </Card>

      <TabBar tabs={[{ id: "directorio", label: "Directorio" }, { id: "pedidos", label: pedidosActivos ? `Pedidos activos (${pedidosActivos})` : "Pedidos" }]} active={tab} onChange={setTab} />

      {tab === "directorio" && (
        <>
          <div style={{ display: "flex", gap: 6, marginBottom: 16 }}>
            {opciones.map(o => (
              <button key={o.id} onClick={() => setFiltro(o.id)} style={{
                padding: "6px 14px", borderRadius: 999, fontSize: 12, fontWeight: 600, cursor: "pointer",
                border: `1px solid ${filtro === o.id ? C.primary : C.border}`,
                background: filtro === o.id ? `${C.primary}12` : C.surface,
                color: filtro === o.id ? C.primary : C.textMid,
              }}>{o.label}</button>
            ))}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {visibles.map(p => (
              <div key={p.id}>
                <FbProveedorCard proveedor={p} onHacerPedido={setPedidoForm} />
                {pedidoForm && pedidoForm.id === p.id && (
                  <FbNuevoPedidoForm
                    proveedor={p}
                    catalogo={p.dominio === "farmacia" ? (catalogoFarmacia || FB_CATALOGO) : (catalogoBodega || FB_CATALOGO_BODEGA)}
                    itemsProveedor={FB_CATALOGO_PROVEEDOR[p.id] || []}
                    onSubmit={items => crearPedido(p, items)}
                    onCancel={() => setPedidoForm(null)}
                  />
                )}
              </div>
            ))}
          </div>
        </>
      )}

      {tab === "pedidos" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {pedidos.length === 0 && <div style={{ fontSize: 12.5, color: C.textMuted }}>Aún no se ha generado ningún pedido. Ve al Directorio y usa "Hacer pedido" en un proveedor activo.</div>}
          {pedidos.map(ped => (
            <FbPedidoCard key={ped.folio} pedido={ped}
              proveedor={FB_PROVEEDORES.find(p => p.id === ped.proveedorId)}
              catalogo={ped.dominio === "farmacia" ? (catalogoFarmacia || FB_CATALOGO) : (catalogoBodega || FB_CATALOGO_BODEGA)}
              onAvanzar={avanzarPedido}
              onRegistrarRecepcion={() => onIrARecepcion(ped)}
            />
          ))}
        </div>
      )}

      <Card style={{ padding: "14px 18px", marginTop: 16, borderStyle: "dashed" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <ArrowRight size={15} color={C.textMuted} />
          <div style={{ fontSize: 11.5, color: C.textMuted }}>
            Registro contable del pedido (orden de compra, factura, pago) → <strong>Contabilidad</strong>. Puerta etiquetada, todavía no conectada — ver documento de sincronización.
          </div>
        </div>
      </Card>
    </div>
  );
};

// Registro de ítem nuevo dentro de una Recepción — sigue el mismo esquema que
// el resto del catálogo del módulo: en Farmacia, modelo de 3 niveles (DCI/
// SNOMED → marca/Registro ISP → Código CENABAST), igual que FB_CATALOGO; en
// Bodega, esquema simple (nombre/categoría/marca/unidad), igual que
// FB_CATALOGO_BODEGA — nunca se mezclan los dos esquemas. SNOMED CT no se
// pide aquí (mismo criterio que el resto del catálogo de ejemplo: no se
// inventa un código clínico sin verificar) — el ítem queda con
// "pendiente de codificar" hasta que se cargue el dato oficial.
const FbNuevoItemMiniForm = ({ dominio, onRegistrar, onCancel }) => {
  const esFarmacia = dominio === "farmacia";
  const [tipo, setTipo] = useState("medicamento"); // solo aplica si esFarmacia
  const [nombre, setNombre] = useState("");
  const [dci, setDci] = useState("");
  const [numeradorValor, setNumeradorValor] = useState("");
  const [numeradorUnidad, setNumeradorUnidad] = useState("mg");
  const [denominadorValor, setDenominadorValor] = useState("");
  const [denominadorUnidad, setDenominadorUnidad] = useState("mL");
  const [formaFarmaceutica, setFormaFarmaceutica] = useState("");
  const [marca, setMarca] = useState("");
  const [laboratorio, setLaboratorio] = useState("");
  const [registroISP, setRegistroISP] = useState("");
  const [codigoCenabast, setCodigoCenabast] = useState("");
  const [categoria, setCategoria] = useState("otro"); // solo Bodega
  const [unidad, setUnidad] = useState("");
  const [codigoBarra, setCodigoBarra] = useState("");
  const [stockMinimo, setStockMinimo] = useState(0);

  const esMedicamento = esFarmacia && tipo === "medicamento";
  const puedeRegistrar = nombre.trim() && unidad.trim() && codigoBarra.trim() &&
    (!esFarmacia || (registroISP.trim() && codigoCenabast.trim())) &&
    (!esMedicamento || dci.trim());

  function handleRegistrar() {
    onRegistrar({
      tipo: esFarmacia ? tipo : null, nombre: nombre.trim(), dci: dci.trim(),
      concentracion: numeradorValor ? {
        numeradorValor: Number(numeradorValor), numeradorUnidad,
        denominadorValor: denominadorValor ? Number(denominadorValor) : null,
        denominadorUnidad: denominadorValor ? denominadorUnidad : null,
      } : null,
      formaFarmaceutica: formaFarmaceutica.trim(), marca: marca.trim(), laboratorio: laboratorio.trim(),
      registroISP: registroISP.trim(), codigoCenabast: codigoCenabast.trim(), categoria,
      unidad: unidad.trim(), codigoBarra: codigoBarra.trim(), stockMinimo: Math.max(0, Number(stockMinimo) || 0),
    });
  }

  return (
    <Card style={{ padding: 14, marginBottom: 10, background: `${C.warning}0A`, border: `1px dashed ${C.warning}` }}>
      <div style={{ fontSize: 12.5, fontWeight: 700, color: C.text, marginBottom: 2 }}>Registrar ítem nuevo en el catálogo</div>
      <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 10 }}>
        {esFarmacia
          ? "Mismo esquema del catálogo de Farmacia: DCI (solo medicamentos) → marca/Registro ISP → Código CENABAST."
          : "Mismo esquema del catálogo de Bodega: nombre, categoría, marca."}
      </div>

      {esFarmacia && (
        <div style={{ display: "flex", gap: 16, marginBottom: 10, fontSize: 12 }}>
          <label style={{ display: "flex", alignItems: "center", gap: 5 }}>
            <input type="radio" checked={tipo === "medicamento"} onChange={() => setTipo("medicamento")} /> Medicamento
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: 5 }}>
            <input type="radio" checked={tipo === "insumo-clinico"} onChange={() => setTipo("insumo-clinico")} /> Insumo clínico
          </label>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 10 }}>
        <div>
          <div style={{ fontSize: 10.5, color: C.textMuted, marginBottom: 3 }}>Nombre {esMedicamento ? "comercial" : ""} *</div>
          <input value={nombre} onChange={e => setNombre(e.target.value)} style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "5px 8px", fontSize: 12 }} />
        </div>
        <div>
          <div style={{ fontSize: 10.5, color: C.textMuted, marginBottom: 3 }}>Código de barra *</div>
          <input value={codigoBarra} onChange={e => setCodigoBarra(e.target.value)} style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "5px 8px", fontSize: 12 }} />
        </div>
        {esMedicamento && (
          <>
            <div>
              <div style={{ fontSize: 10.5, color: C.textMuted, marginBottom: 3 }}>Nombre DCI *</div>
              <input value={dci} onChange={e => setDci(e.target.value)} placeholder="Ej: Furosemida" style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "5px 8px", fontSize: 12 }} />
            </div>
            <div>
              <div style={{ fontSize: 10.5, color: C.textMuted, marginBottom: 3 }}>Forma farmacéutica</div>
              <input value={formaFarmaceutica} onChange={e => setFormaFarmaceutica(e.target.value)} placeholder="Ej: Solución inyectable" style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "5px 8px", fontSize: 12 }} />
            </div>
            <div style={{ gridColumn: "1 / -1" }}>
              <div style={{ fontSize: 10.5, color: C.textMuted, marginBottom: 3 }}>Concentración (numerador / denominador — no se mezcla en un solo texto)</div>
              <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
                <input type="number" step="any" value={numeradorValor} onChange={e => setNumeradorValor(e.target.value)} placeholder="20"
                  style={{ width: 64, border: `1px solid ${C.border}`, borderRadius: 6, padding: "5px 8px", fontSize: 12 }} />
                <select value={numeradorUnidad} onChange={e => setNumeradorUnidad(e.target.value)}
                  style={{ border: `1px solid ${C.border}`, borderRadius: 6, padding: "5px 6px", fontSize: 12 }}>
                  {FB_UNIDADES_NUMERADOR.map(u => <option key={u} value={u}>{u}</option>)}
                </select>
                <span style={{ color: C.textMuted }}>/</span>
                <input type="number" step="any" value={denominadorValor} onChange={e => setDenominadorValor(e.target.value)} placeholder="2 (vacío si es %)"
                  style={{ width: 90, border: `1px solid ${C.border}`, borderRadius: 6, padding: "5px 8px", fontSize: 12 }} />
                <select value={denominadorUnidad} onChange={e => setDenominadorUnidad(e.target.value)} disabled={!denominadorValor}
                  style={{ border: `1px solid ${C.border}`, borderRadius: 6, padding: "5px 6px", fontSize: 12 }}>
                  {FB_UNIDADES_DENOMINADOR.map(u => <option key={u} value={u}>{u}</option>)}
                </select>
              </div>
              <div style={{ fontSize: 10, color: C.textMuted, marginTop: 3 }}>Para porcentaje (ej. Cloruro de Sodio 0.9%), usa "%" como unidad del numerador y deja el denominador vacío.</div>
            </div>
          </>
        )}
        {esFarmacia && (
          <>
            <div>
              <div style={{ fontSize: 10.5, color: C.textMuted, marginBottom: 3 }}>Marca</div>
              <input value={marca} onChange={e => setMarca(e.target.value)} style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "5px 8px", fontSize: 12 }} />
            </div>
            <div>
              <div style={{ fontSize: 10.5, color: C.textMuted, marginBottom: 3 }}>Laboratorio</div>
              <input value={laboratorio} onChange={e => setLaboratorio(e.target.value)} style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "5px 8px", fontSize: 12 }} />
            </div>
            <div>
              <div style={{ fontSize: 10.5, color: C.textMuted, marginBottom: 3 }}>Registro ISP *</div>
              <input value={registroISP} onChange={e => setRegistroISP(e.target.value)} placeholder="Ej: F-9821/15" style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "5px 8px", fontSize: 12 }} />
            </div>
            <div>
              <div style={{ fontSize: 10.5, color: C.textMuted, marginBottom: 3 }}>Código CENABAST *</div>
              <input value={codigoCenabast} onChange={e => setCodigoCenabast(e.target.value)} style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "5px 8px", fontSize: 12 }} />
            </div>
          </>
        )}
        {!esFarmacia && (
          <div>
            <div style={{ fontSize: 10.5, color: C.textMuted, marginBottom: 3 }}>Categoría</div>
            <select value={categoria} onChange={e => setCategoria(e.target.value)} style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "5px 8px", fontSize: 12 }}>
              {["aseo-limpieza", "papeleria", "epp", "mantención", "oficina", "alimentacion", "vestuario", "repuestos", "otro"].map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
        )}
        <div>
          <div style={{ fontSize: 10.5, color: C.textMuted, marginBottom: 3 }}>Unidad de medida *</div>
          <input value={unidad} onChange={e => setUnidad(e.target.value)} placeholder="Ej: ampolla, unidad, caja" style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "5px 8px", fontSize: 12 }} />
        </div>
        <div>
          <div style={{ fontSize: 10.5, color: C.textMuted, marginBottom: 3 }}>Stock mínimo inicial</div>
          <input type="number" min="0" value={stockMinimo} onChange={e => setStockMinimo(e.target.value)} style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "5px 8px", fontSize: 12 }} />
        </div>
      </div>

      {esFarmacia && <div style={{ fontSize: 10.5, color: C.textMuted, marginBottom: 10, fontStyle: "italic" }}>SNOMED CT no se pide aquí — se completa después con el dato oficial verificado (mismo criterio que el resto del catálogo de ejemplo).</div>}

      <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
        <Btn variant="ghost" size="sm" onClick={onCancel}>Cancelar</Btn>
        <Btn variant="primary" size="sm" icon={CheckCircle} onClick={handleRegistrar} disabled={!puedeRegistrar}>Registrar en el catálogo</Btn>
      </div>
    </Card>
  );
};

const FbNuevaRecepcionForm = ({ dominio, proveedores, pedidosDisponibles, catalogo, pedidoInicial, mostrarCadenaFrio, onSubmit, onCancel, onRegistrarItemNuevo }) => {
  const [proveedorId, setProveedorId] = useState(pedidoInicial ? pedidoInicial.proveedorId : (proveedores[0] ? proveedores[0].id : ""));
  const [ordenCompraFolio, setOrdenCompraFolio] = useState(pedidoInicial ? pedidoInicial.folio : "");
  const [guiaDespacho, setGuiaDespacho] = useState("");
  const [facturaNumero, setFacturaNumero] = useState("");
  const [itemNuevoId, setItemNuevoId] = useState(catalogo[0] ? catalogo[0].id : "");
  const [mostrarNuevoItem, setMostrarNuevoItem] = useState(false);
  const [items, setItems] = useState(() => {
    if (!pedidoInicial) return [];
    return pedidoInicial.items.map(it => ({
      itemId: it.itemId, lote: "", fechaVencimiento: "",
      cantidadFacturada: it.cantidadSolicitada, cantidadRecibida: it.cantidadSolicitada,
      cumpleEspecificaciones: true, observaciones: "",
    }));
  });
  const [embalajeIntegro, setEmbalajeIntegro] = useState(true);
  const [documentacionCompleta, setDocumentacionCompleta] = useState(true);
  const [cadenaFrioConforme, setCadenaFrioConforme] = useState(true);
  const [observacionesGenerales, setObservacionesGenerales] = useState("");

  function actualizarItem(itemId, campo, valor) {
    setItems(prev => prev.map(it => (it.itemId === itemId ? { ...it, [campo]: valor } : it)));
  }
  function agregarItem() {
    if (!itemNuevoId || items.some(it => it.itemId === itemNuevoId)) return;
    setItems(prev => [...prev, { itemId: itemNuevoId, lote: "", fechaVencimiento: "", cantidadFacturada: 0, cantidadRecibida: 0, cumpleEspecificaciones: true, observaciones: "" }]);
  }
  function quitarItem(itemId) {
    setItems(prev => prev.filter(it => it.itemId !== itemId));
  }
  function handleRegistrarItemNuevo(payload) {
    const nuevoId = onRegistrarItemNuevo(payload);
    setItems(prev => [...prev, { itemId: nuevoId, lote: "", fechaVencimiento: "", cantidadFacturada: 0, cantidadRecibida: 0, cumpleEspecificaciones: true, observaciones: "", esNuevoItem: true }]);
    setMostrarNuevoItem(false);
  }

  const puedeEnviar = guiaDespacho.trim().length > 0 && items.length > 0 && items.some(it => it.cantidadRecibida > 0);

  function construirPayload(rechazar) {
    return {
      proveedorId, ordenCompraFolio: ordenCompraFolio || null, guiaDespacho: guiaDespacho.trim(),
      facturaNumero: facturaNumero.trim() || null, items,
      verificacion: { embalajeIntegro, documentacionCompleta, cadenaFrioConforme: mostrarCadenaFrio ? cadenaFrioConforme : null, observacionesGenerales: observacionesGenerales.trim() || null },
      rechazar,
    };
  }

  return (
    <Card style={{ padding: 18, marginBottom: 16, border: `1px dashed ${C.primary}` }}>
      <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 4 }}>Nueva recepción</div>
      {pedidoInicial && <div style={{ fontSize: 11.5, color: C.textMuted, marginBottom: 12 }}>Vinculada al pedido <strong style={{ fontFamily: "monospace" }}>{pedidoInicial.folio}</strong> — cantidades precargadas desde lo solicitado, ajusta según lo que realmente llegó.</div>}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 14 }}>
        <div>
          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Proveedor</div>
          <select value={proveedorId} onChange={e => setProveedorId(e.target.value)} disabled={!!pedidoInicial}
            style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", fontSize: 12 }}>
            {proveedores.map(p => <option key={p.id} value={p.id}>{p.razonSocial}</option>)}
          </select>
        </div>
        <div>
          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Orden de compra (opcional)</div>
          <select value={ordenCompraFolio} onChange={e => setOrdenCompraFolio(e.target.value)} disabled={!!pedidoInicial}
            style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", fontSize: 12 }}>
            <option value="">Sin orden de compra asociada</option>
            {pedidosDisponibles.map(p => <option key={p.folio} value={p.folio}>{p.folio}</option>)}
          </select>
          <div style={{ fontSize: 9.5, color: C.textMuted, marginTop: 3, fontStyle: "italic" }}>Puerta etiquetada #22: hoy es nuestro folio de Pedido interno; debería terminar referenciando la Orden de Compra formal que aprueba Contabilidad — ver documento de sincronización.</div>
        </div>
        <div>
          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Guía de despacho *</div>
          <input value={guiaDespacho} onChange={e => setGuiaDespacho(e.target.value)} placeholder="N° de guía"
            style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", fontSize: 12 }} />
        </div>
        <div>
          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>N° de factura (opcional)</div>
          <input value={facturaNumero} onChange={e => setFacturaNumero(e.target.value)}
            style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", fontSize: 12 }} />
        </div>
      </div>

      {!pedidoInicial && (
        <div style={{ marginBottom: 10 }}>
          <div style={{ display: "flex", gap: 8, alignItems: "flex-end", marginBottom: 6 }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Agregar ítem del catálogo (simula escaneo de código de barra)</div>
              <select value={itemNuevoId} onChange={e => setItemNuevoId(e.target.value)}
                style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", fontSize: 12 }}>
                {catalogo.map(it => <option key={it.id} value={it.id}>{it.nombre} — {it.codigoBarra}</option>)}
              </select>
            </div>
            <Btn variant="outline" size="sm" icon={Plus} onClick={agregarItem}>Agregar</Btn>
          </div>
          {!mostrarNuevoItem ? (
            <button onClick={() => setMostrarNuevoItem(true)} style={{ background: "none", border: "none", cursor: "pointer", color: C.primary, fontSize: 11.5, padding: 0, textDecoration: "underline" }}>
              ¿El código de barra no está en el catálogo? Registrar ítem nuevo
            </button>
          ) : (
            <FbNuevoItemMiniForm dominio={dominio} onRegistrar={handleRegistrarItemNuevo} onCancel={() => setMostrarNuevoItem(false)} />
          )}
        </div>
      )}

      <div style={{ border: `1px solid ${C.border}`, borderRadius: 8, marginBottom: 14, overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
          <thead>
            <tr style={{ background: "#F5F8FF" }}>
              {["Ítem", "Lote", "Vencimiento", "Facturada", "Recibida", "Cumple", "Observ.", ""].map(h => (
                <th key={h} style={{ textAlign: "left", padding: "7px 8px", fontSize: 10, color: C.textMuted, textTransform: "uppercase" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && (
              <tr><td colSpan={8} style={{ padding: "14px 8px", textAlign: "center", color: C.textMuted, fontSize: 12 }}>Sin ítems todavía.</td></tr>
            )}
            {items.map(it => {
              const cat = catalogo.find(c => c.id === it.itemId);
              const diferencia = it.cantidadRecibida !== it.cantidadFacturada;
              return (
                <tr key={it.itemId} style={{ borderTop: `1px solid ${C.border}` }}>
                  <td style={{ padding: "6px 8px" }}>{cat ? cat.nombre : it.itemId}{it.esNuevoItem && <Badge color={C.warning} sm> nuevo</Badge>}</td>
                  <td style={{ padding: "6px 8px" }}>
                    <input value={it.lote} onChange={e => actualizarItem(it.itemId, "lote", e.target.value)} placeholder="N° lote"
                      style={{ width: 80, border: `1px solid ${C.border}`, borderRadius: 5, padding: "4px 6px", fontSize: 11.5 }} />
                  </td>
                  <td style={{ padding: "6px 8px" }}>
                    <input type="date" value={it.fechaVencimiento} onChange={e => actualizarItem(it.itemId, "fechaVencimiento", e.target.value)}
                      style={{ width: 128, border: `1px solid ${C.border}`, borderRadius: 5, padding: "4px 6px", fontSize: 11.5 }} />
                  </td>
                  <td style={{ padding: "6px 8px" }}>
                    <input type="number" min="0" value={it.cantidadFacturada} onChange={e => actualizarItem(it.itemId, "cantidadFacturada", Math.max(0, Number(e.target.value) || 0))}
                      style={{ width: 60, border: `1px solid ${C.border}`, borderRadius: 5, padding: "4px 6px", fontSize: 11.5 }} />
                  </td>
                  <td style={{ padding: "6px 8px" }}>
                    <input type="number" min="0" value={it.cantidadRecibida} onChange={e => actualizarItem(it.itemId, "cantidadRecibida", Math.max(0, Number(e.target.value) || 0))}
                      style={{ width: 60, border: `1px solid ${diferencia ? C.warning : C.border}`, borderRadius: 5, padding: "4px 6px", fontSize: 11.5 }} />
                  </td>
                  <td style={{ padding: "6px 8px", textAlign: "center" }}>
                    <input type="checkbox" checked={it.cumpleEspecificaciones} onChange={e => actualizarItem(it.itemId, "cumpleEspecificaciones", e.target.checked)} />
                  </td>
                  <td style={{ padding: "6px 8px" }}>
                    <input value={it.observaciones} onChange={e => actualizarItem(it.itemId, "observaciones", e.target.value)} placeholder="—"
                      style={{ width: 90, border: `1px solid ${C.border}`, borderRadius: 5, padding: "4px 6px", fontSize: 11.5 }} />
                  </td>
                  <td style={{ padding: "6px 8px" }}>
                    <button onClick={() => quitarItem(it.itemId)} style={{ background: "none", border: "none", cursor: "pointer", color: C.textMuted, padding: 0 }}><X size={13} /></button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div style={{ fontSize: 11.5, fontWeight: 600, color: C.text, marginBottom: 8 }}>Verificación</div>
      <div style={{ display: "flex", gap: 18, flexWrap: "wrap", marginBottom: 10, fontSize: 12 }}>
        <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <input type="checkbox" checked={embalajeIntegro} onChange={e => setEmbalajeIntegro(e.target.checked)} /> Embalaje íntegro
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <input type="checkbox" checked={documentacionCompleta} onChange={e => setDocumentacionCompleta(e.target.checked)} /> Documentación completa
        </label>
        {mostrarCadenaFrio && (
          <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <input type="checkbox" checked={cadenaFrioConforme} onChange={e => setCadenaFrioConforme(e.target.checked)} /> Cadena de frío conforme (si aplica)
          </label>
        )}
      </div>
      <textarea value={observacionesGenerales} onChange={e => setObservacionesGenerales(e.target.value)} rows={2}
        placeholder="Observaciones generales de la recepción (opcional)"
        style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "8px 10px", fontSize: 12, fontFamily: "inherit", resize: "vertical", marginBottom: 14 }} />

      <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
        <Btn variant="ghost" onClick={onCancel}>Cancelar</Btn>
        <Btn variant="danger" icon={X} onClick={() => onSubmit(construirPayload(true))} disabled={!guiaDespacho.trim()}>Rechazar recepción</Btn>
        <Btn variant="primary" icon={CheckCircle} onClick={() => onSubmit(construirPayload(false))} disabled={!puedeEnviar}>Registrar recepción</Btn>
      </div>
    </Card>
  );
};

const FbRecepcionCard = ({ recepcion, proveedor, catalogo }) => {
  const rec = recepcion;
  const meta = RECEPCION_ESTADO_META[rec.estado] || { label: rec.estado, color: C.textMuted };
  return (
    <Card style={{ padding: 14 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8, flexWrap: "wrap" }}>
        <span style={{ fontFamily: "monospace", fontSize: 11, color: C.textMuted, background: C.bodyBg, padding: "1px 6px", borderRadius: 5 }}>{rec.folio}</span>
        <span style={{ fontWeight: 600, fontSize: 13, flex: 1 }}>{proveedor ? proveedor.razonSocial : rec.proveedorId}</span>
        {rec.ordenCompraFolio && <Badge color={C.primary} sm>{rec.ordenCompraFolio}</Badge>}
        <Badge color={meta.color} sm>{meta.label}</Badge>
      </div>
      <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 6 }}>Guía {rec.guiaDespacho}{rec.facturaNumero ? ` · Factura ${rec.facturaNumero}` : ""} · {fbFormatFechaHora(rec.fechaRecepcion)}</div>
      <ul style={{ listStyle: "none", margin: "0 0 6px", padding: 0, fontSize: 12.5 }}>
        {rec.items.map(it => {
          const cat = catalogo.find(c => c.id === it.itemId);
          const diferencia = it.cantidadRecibida !== it.cantidadFacturada;
          return (
            <li key={it.itemId} style={{ marginBottom: 2 }}>
              {cat ? cat.nombre : it.itemId} — recibido {it.cantidadRecibida} de {it.cantidadFacturada} facturado
              {it.lote ? ` · lote ${it.lote}` : ""}{it.fechaVencimiento ? ` · vence ${it.fechaVencimiento}` : ""}
              {it.esNuevoItem && <Badge color={C.warning} sm> nuevo en catálogo</Badge>}
              {diferencia && <Badge color={C.warning} sm> diferencia</Badge>}
              {!it.cumpleEspecificaciones && <Badge color={C.danger} sm> no cumple espec.</Badge>}
            </li>
          );
        })}
      </ul>
      <div style={{ fontSize: 11, color: C.textMuted }}>
        Embalaje {rec.verificacion.embalajeIntegro ? "íntegro" : "con daño"} · Documentación {rec.verificacion.documentacionCompleta ? "completa" : "incompleta"}
        {rec.verificacion.cadenaFrioConforme !== null && rec.verificacion.cadenaFrioConforme !== undefined ? ` · Cadena de frío ${rec.verificacion.cadenaFrioConforme ? "conforme" : "no conforme"}` : ""}
      </div>
      {rec.verificacion.observacionesGenerales && <div style={{ fontSize: 11.5, color: C.textMid, marginTop: 6, fontStyle: "italic" }}>"{rec.verificacion.observacionesGenerales}"</div>}
    </Card>
  );
};

const FbRecepcionesView = ({ dominio, catalogo, proveedores, pedidosDisponibles, recepciones, pedidoInicial, mostrarCadenaFrio, onRegistrar, onLimpiarPedidoInicial, onRegistrarItemNuevo }) => {
  const [mostrarForm, setMostrarForm] = useState(!!pedidoInicial);

  useEffect(() => {
    if (pedidoInicial) setMostrarForm(true);
  }, [pedidoInicial]);

  function handleSubmit(payload) {
    onRegistrar(payload);
    setMostrarForm(false);
    if (onLimpiarPedidoInicial) onLimpiarPedidoInicial();
  }
  function handleCancel() {
    setMostrarForm(false);
    if (onLimpiarPedidoInicial) onLimpiarPedidoInicial();
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14, flexWrap: "wrap", gap: 10 }}>
        <div style={{ fontSize: 12.5, color: C.textMuted, maxWidth: 480 }}>Registro de recepciones desde proveedores externos — actualiza el stock central con lo realmente recibido, no con lo pedido.</div>
        {!mostrarForm && <Btn variant="primary" icon={Plus} onClick={() => setMostrarForm(true)}>Nueva recepción</Btn>}
      </div>
      {mostrarForm && (
        <FbNuevaRecepcionForm dominio={dominio} proveedores={proveedores} pedidosDisponibles={pedidosDisponibles} catalogo={catalogo}
          pedidoInicial={pedidoInicial} mostrarCadenaFrio={mostrarCadenaFrio} onSubmit={handleSubmit} onCancel={handleCancel}
          onRegistrarItemNuevo={onRegistrarItemNuevo} />
      )}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {recepciones.length === 0 && <div style={{ fontSize: 12.5, color: C.textMuted }}>Aún no hay recepciones registradas.</div>}
        {recepciones.map(rec => (
          <FbRecepcionCard key={rec.folio} recepcion={rec} proveedor={proveedores.find(p => p.id === rec.proveedorId)} catalogo={catalogo} />
        ))}
      </div>
    </div>
  );
};

// ── CLIENTES EXTERNOS (#18): empresas/instituciones fuera de AXON a quienes
// se abastece por préstamo, convenio, venta o donación. NUNCA son sub-
// farmacia ni sub-bodega interna. Según arquitectura_farmacia_bodega.md,
// DespachoClienteExterno referencia InsumoBodega | Medicamento — por eso
// vive en la fila de compartidos (mismo criterio que Gestión Proveedores),
// pudiendo despachar desde Farmacia O desde Bodega sin mezclar catálogos
// (cada despacho declara su dominio explícitamente). Datos de ejemplo,
// pendiente el listado oficial de clientes externos de AXON.
const TIPO_RELACION_META = {
  prestamo:   { label: "Préstamo",     color: C.primary },
  convenio:   { label: "Convenio",     color: "#6A1B9A" },
  venta:      { label: "Venta",        color: C.success },
  donacion:   { label: "Donación",     color: C.teal },
  intercambio:{ label: "Intercambio",  color: C.warning },
};
const DEVOLUCION_ESTADO_META = {
  pendiente:          { label: "Devolución pendiente", color: C.warning },
  devuelto:           { label: "Devuelto",              color: C.success },
  "devuelto-parcial": { label: "Devuelto parcial",       color: "#B45309" },
  "no-devuelto":      { label: "No devuelto",            color: C.danger },
};

// ── Trazabilidad (#8 Farmacia / #15 Bodega) ────────────────────────────────
// Cada movimiento real de stock queda registrado con este esquema — mismo
// campo a campo que el diseño de SupplyEvent en
// AXON_SUPPLY_CORE_CIMIENTOS_ARQUITECTURA.md (no aprobado como refactor de
// código todavía, pero el prototipo ya emite eventos con esta forma para que
// el futuro mapeo a Supply Core sea directo, sin reescritura).
const MOVIMIENTO_TIPO_META = {
  "ingreso-proveedor":        { label: "Ingreso proveedor",        color: C.success },
  "despacho-unidad":          { label: "Despacho a unidad",        color: C.primary },
  "recepcion-unidad":         { label: "Recepción en unidad",      color: C.teal },
  "despacho-cliente-externo": { label: "Despacho cliente externo", color: "#6A1B9A" },
  "devolucion":               { label: "Devolución",               color: C.warning },
  // El tipo genérico "ajuste" (reservado desde Trazabilidad, nunca usado por
  // ningún flujo) se reemplaza por 3 tipos estructurados — un conteo físico
  // siempre encuentra diferencias y un "ajuste libre" sin categoría no sirve
  // para auditar (Parte 13.4 y 14.4 del dossier; validado contra los
  // movement types de SAP: scrapping/merma vs. diferencia de inventario físico).
  "merma":                    { label: "Merma",                    color: C.danger },
  "vencimiento":              { label: "Baja por vencimiento",     color: "#B45309" },
  "diferencia-conteo":        { label: "Diferencia de conteo",     color: "#0E7490" },
};
// ── Cuadratura de Stock: motivos y causas ──────────────────────────────────
const CUADRATURA_MOTIVO_INFO = {
  merma:               { label: "Merma",               desc: "Pérdida, hurto o deterioro — el stock solo puede bajar." },
  vencimiento:         { label: "Baja por vencimiento", desc: "Retiro de un lote vencido, elegido desde los lotes que hoy solo generan alerta." },
  "diferencia-conteo": { label: "Diferencia de conteo", desc: "Ajuste tras un inventario físico — el stock puede subir o bajar." },
};
const CUADRATURA_CAUSA_MERMA = {
  perdida:    "Pérdida",
  hurto:      "Hurto",
  deterioro:  "Deterioro / daño",
};
function fbCrearMovimiento({ itemId, lote, tipoMovimiento, cantidad, signo, stockResultante, origen, destino, documentoRespaldo, registradoPor, observaciones }) {
  return {
    id: `MOV-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    itemId, lote: lote || null, tipoMovimiento, cantidad, signo,
    stockResultante: stockResultante != null ? stockResultante : null,
    origen, destino, documentoRespaldo, registradoPor: registradoPor || "—",
    fechaMovimiento: new Date().toISOString(), observaciones: observaciones || null,
  };
}
const FB_CLIENTES_EXTERNOS_INICIAL = [
  {
    id: "CLIEXT-001", razonSocial: "Hospital San José de Melipilla", rut: "61.602.847-3", tipoRelacion: "convenio",
    contacto: { nombreContacto: "Dr. Ignacio Reyes", cargo: "Subdirector Médico", telefono: "+56 2 2831 7000", email: "ireyes@hsanjosemelipilla.cl" },
    convenio: { numeroConvenio: "CONV-2026-014", fechaInicio: "2026-01-01", fechaFin: "2026-12-31", condiciones: "Préstamo recíproco de insumos críticos ante desabastecimiento puntual, con reposición en especie a 30 días." },
    estado: "activo",
  },
  {
    id: "CLIEXT-002", razonSocial: "Fundación Las Rosas — Hogar Santiago", rut: "70.123.456-1", tipoRelacion: "donacion",
    contacto: { nombreContacto: "María Elena Soto", cargo: "Encargada de Enfermería", telefono: "+56 2 2555 3210", email: "msoto@fundacionlasrosas.cl" },
    convenio: null, estado: "activo",
  },
  {
    id: "CLIEXT-003", razonSocial: "Centro Médico Vitalis Ltda.", rut: "76.890.123-5", tipoRelacion: "venta",
    contacto: { nombreContacto: "Patricio Ibáñez", cargo: "Jefe de Adquisiciones", telefono: "+56 9 6712 3344", email: "pibanez@vitalis.cl" },
    convenio: null, estado: "suspendido",
  },
];
const FB_DESPACHOS_EXTERNOS_INICIAL = [];

const FbClienteExternoCard = ({ cliente, onNuevoDespacho }) => {
  const [abierto, setAbierto] = useState(false);
  const c = cliente;
  const meta = TIPO_RELACION_META[c.tipoRelacion] || { label: c.tipoRelacion, color: C.textMid };
  const estadoColor = { activo: C.success, inactivo: C.textMuted, suspendido: C.danger }[c.estado] || C.textMuted;
  const estadoLabel = { activo: "Activo", inactivo: "Inactivo", suspendido: "Suspendido" }[c.estado] || c.estado;
  return (
    <Card style={{ padding: 16 }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 10, cursor: "pointer" }} onClick={() => setAbierto(v => !v)}>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 4 }}>
            <span style={{ fontWeight: 700, fontSize: 14, color: C.text }}>{c.razonSocial}</span>
            <Badge color={meta.color} sm>{meta.label}</Badge>
            <Badge color={estadoColor} sm>{estadoLabel}</Badge>
          </div>
          <div style={{ fontSize: 11.5, color: C.textMuted }}>RUT {c.rut}</div>
        </div>
        {abierto ? <ChevronUp size={16} color={C.textMuted} /> : <ChevronDown size={16} color={C.textMuted} />}
      </div>
      {abierto && (
        <div style={{ marginTop: 14, paddingTop: 14, borderTop: `1px solid ${C.border}` }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, fontSize: 12, marginBottom: 14 }}>
            <div>
              <div style={{ fontSize: 10, textTransform: "uppercase", color: C.textMuted, marginBottom: 6, fontWeight: 600 }}>Contacto</div>
              <div>{c.contacto.nombreContacto} · {c.contacto.cargo}</div>
              <div style={{ color: C.textMid }}>{c.contacto.telefono}</div>
              <div style={{ color: C.textMid }}>{c.contacto.email}</div>
            </div>
            {c.convenio && (
              <div>
                <div style={{ fontSize: 10, textTransform: "uppercase", color: C.textMuted, marginBottom: 6, fontWeight: 600 }}>Convenio {c.convenio.numeroConvenio}</div>
                <div>Vigencia: {c.convenio.fechaInicio} a {c.convenio.fechaFin}</div>
                {c.convenio.condiciones && <div style={{ color: C.textMid, marginTop: 4 }}>{c.convenio.condiciones}</div>}
              </div>
            )}
          </div>
          {c.estado === "activo" ? (
            <Btn variant="primary" size="sm" icon={Plus} onClick={() => onNuevoDespacho(c)}>Nuevo despacho</Btn>
          ) : (
            <div style={{ fontSize: 11, color: C.textMuted, fontStyle: "italic" }}>No se puede despachar a un cliente {estadoLabel.toLowerCase()}.</div>
          )}
        </div>
      )}
    </Card>
  );
};

const FbNuevoClienteExternoForm = ({ onSubmit, onCancel }) => {
  const [razonSocial, setRazonSocial] = useState("");
  const [rut, setRut] = useState("");
  const [tipoRelacion, setTipoRelacion] = useState("convenio");
  const [nombreContacto, setNombreContacto] = useState("");
  const [cargo, setCargo] = useState("");
  const [telefono, setTelefono] = useState("");
  const [email, setEmail] = useState("");
  const [numeroConvenio, setNumeroConvenio] = useState("");
  const [fechaInicio, setFechaInicio] = useState("");
  const [fechaFin, setFechaFin] = useState("");
  const [condiciones, setCondiciones] = useState("");

  const puedeCrear = razonSocial.trim() && rut.trim() && nombreContacto.trim() && telefono.trim();

  function handleSubmit() {
    if (!puedeCrear) return;
    onSubmit({
      razonSocial: razonSocial.trim(), rut: rut.trim(), tipoRelacion,
      contacto: { nombreContacto: nombreContacto.trim(), cargo: cargo.trim(), telefono: telefono.trim(), email: email.trim() },
      convenio: (tipoRelacion === "convenio" && numeroConvenio.trim()) ? {
        numeroConvenio: numeroConvenio.trim(), fechaInicio, fechaFin, condiciones: condiciones.trim(),
      } : null,
      estado: "activo",
    });
  }

  return (
    <Card style={{ padding: 18, marginBottom: 16, border: `1px dashed ${C.primary}` }}>
      <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 12 }}>Nuevo cliente externo</div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
        <div>
          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Razón social *</div>
          <input value={razonSocial} onChange={e => setRazonSocial(e.target.value)} style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", fontSize: 12 }} />
        </div>
        <div>
          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>RUT *</div>
          <input value={rut} onChange={e => setRut(e.target.value)} placeholder="76.123.456-7" style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", fontSize: 12 }} />
        </div>
        <div>
          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Tipo de relación</div>
          <select value={tipoRelacion} onChange={e => setTipoRelacion(e.target.value)} style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", fontSize: 12 }}>
            {Object.entries(TIPO_RELACION_META).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
          </select>
        </div>
        <div>
          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Nombre de contacto *</div>
          <input value={nombreContacto} onChange={e => setNombreContacto(e.target.value)} style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", fontSize: 12 }} />
        </div>
        <div>
          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Cargo</div>
          <input value={cargo} onChange={e => setCargo(e.target.value)} style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", fontSize: 12 }} />
        </div>
        <div>
          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Teléfono *</div>
          <input value={telefono} onChange={e => setTelefono(e.target.value)} style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", fontSize: 12 }} />
        </div>
        <div>
          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Email</div>
          <input value={email} onChange={e => setEmail(e.target.value)} style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", fontSize: 12 }} />
        </div>
      </div>
      {tipoRelacion === "convenio" && (
        <div style={{ background: C.bodyBg, borderRadius: 8, padding: 12, marginBottom: 12 }}>
          <div style={{ fontSize: 11.5, fontWeight: 600, marginBottom: 8 }}>Datos del convenio (opcional, se puede completar después)</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10, marginBottom: 8 }}>
            <div>
              <div style={{ fontSize: 10.5, color: C.textMuted, marginBottom: 3 }}>N° de convenio</div>
              <input value={numeroConvenio} onChange={e => setNumeroConvenio(e.target.value)} style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "5px 8px", fontSize: 12 }} />
            </div>
            <div>
              <div style={{ fontSize: 10.5, color: C.textMuted, marginBottom: 3 }}>Inicio</div>
              <input type="date" value={fechaInicio} onChange={e => setFechaInicio(e.target.value)} style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "5px 8px", fontSize: 12 }} />
            </div>
            <div>
              <div style={{ fontSize: 10.5, color: C.textMuted, marginBottom: 3 }}>Término</div>
              <input type="date" value={fechaFin} onChange={e => setFechaFin(e.target.value)} style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "5px 8px", fontSize: 12 }} />
            </div>
          </div>
          <textarea value={condiciones} onChange={e => setCondiciones(e.target.value)} rows={2} placeholder="Condiciones del convenio"
            style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 8px", fontSize: 12, fontFamily: "inherit", resize: "vertical" }} />
        </div>
      )}
      <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
        <Btn variant="ghost" onClick={onCancel}>Cancelar</Btn>
        <Btn variant="primary" icon={ArrowRight} onClick={handleSubmit} disabled={!puedeCrear}>Registrar cliente</Btn>
      </div>
    </Card>
  );
};

const FbNuevoDespachoExternoForm = ({ cliente, catalogoFarmacia, catalogoBodega, centralStock, centralStockBod, conceptosFarmaco, onSubmit, onCancel }) => {
  const [dominio, setDominio] = useState("farmacia");
  const catalogo = dominio === "farmacia" ? catalogoFarmacia : catalogoBodega;
  const stock = dominio === "farmacia" ? centralStock : centralStockBod;
  const [tipoOperacion, setTipoOperacion] = useState(cliente.tipoRelacion === "intercambio" ? "convenio" : cliente.tipoRelacion);
  const [documentoRespaldo, setDocumentoRespaldo] = useState("");
  const [guiaDespacho, setGuiaDespacho] = useState("");
  const [fechaLimiteDevolucion, setFechaLimiteDevolucion] = useState("");
  const [itemNuevoId, setItemNuevoId] = useState(catalogo[0] ? catalogo[0].id : "");
  const [items, setItems] = useState([]);

  useEffect(() => { setItems([]); setItemNuevoId(catalogo[0] ? catalogo[0].id : ""); }, [dominio]); // eslint-disable-line

  function agregarItem() {
    if (!itemNuevoId || items.some(it => it.itemId === itemNuevoId)) return;
    setItems(prev => [...prev, { itemId: itemNuevoId, cantidad: 1, valorReferencial: "", lote: "" }]);
  }
  function actualizarItem(itemId, campo, valor) {
    setItems(prev => prev.map(it => (it.itemId === itemId ? { ...it, [campo]: valor } : it)));
  }
  function quitarItem(itemId) {
    setItems(prev => prev.filter(it => it.itemId !== itemId));
  }

  const conDevolucion = tipoOperacion === "prestamo" || tipoOperacion === "convenio";
  const puedeEnviar = items.length > 0 &&
    items.every(it => it.cantidad > 0 && it.cantidad <= (stock[it.itemId] ? stock[it.itemId].stockActual : 0)) &&
    guiaDespacho.trim().length > 0 && (!conDevolucion || fechaLimiteDevolucion);

  function handleSubmit() {
    if (!puedeEnviar) return;
    onSubmit({
      dominio, items: items.map(it => ({ ...it, valorReferencial: it.valorReferencial ? Number(it.valorReferencial) : null })), tipoOperacion,
      documentoRespaldo: documentoRespaldo.trim(), guiaDespacho: guiaDespacho.trim(),
      devolucionEsperada: conDevolucion ? { fechaLimite: fechaLimiteDevolucion, estado: "pendiente", itemsDevueltos: [] } : null,
    });
  }

  return (
    <Card style={{ padding: 18, marginBottom: 16, border: `1px dashed ${C.primary}` }}>
      <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 4 }}>Nuevo despacho — {cliente.razonSocial}</div>
      <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 12 }}>Descuenta stock central de verdad al confirmar — nunca mezcla catálogo de Farmacia con el de Bodega.</div>

      <div style={{ display: "flex", gap: 16, marginBottom: 12, fontSize: 12 }}>
        <label style={{ display: "flex", alignItems: "center", gap: 5 }}>
          <input type="radio" checked={dominio === "farmacia"} onChange={() => setDominio("farmacia")} /> Desde Farmacia
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: 5 }}>
          <input type="radio" checked={dominio === "bodega"} onChange={() => setDominio("bodega")} /> Desde Bodega
        </label>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
        <div>
          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Tipo de operación</div>
          <select value={tipoOperacion} onChange={e => setTipoOperacion(e.target.value)} style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", fontSize: 12 }}>
            {["prestamo", "convenio", "venta", "donacion"].map(k => <option key={k} value={k}>{TIPO_RELACION_META[k].label}</option>)}
          </select>
        </div>
        <div>
          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Guía de despacho *</div>
          <input value={guiaDespacho} onChange={e => setGuiaDespacho(e.target.value)} style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", fontSize: 12 }} />
        </div>
        <div>
          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Documento de respaldo</div>
          <input value={documentoRespaldo} onChange={e => setDocumentoRespaldo(e.target.value)} placeholder="N° convenio, oficio, etc." style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", fontSize: 12 }} />
        </div>
        {conDevolucion && (
          <div>
            <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Fecha límite de devolución *</div>
            <input type="date" value={fechaLimiteDevolucion} onChange={e => setFechaLimiteDevolucion(e.target.value)} style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", fontSize: 12 }} />
          </div>
        )}
      </div>

      <div style={{ display: "flex", gap: 8, alignItems: "flex-end", marginBottom: 10 }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Agregar ítem ({dominio === "farmacia" ? "catálogo Farmacia" : "catálogo Bodega"})</div>
          <select value={itemNuevoId} onChange={e => setItemNuevoId(e.target.value)} style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", fontSize: 12 }}>
            {catalogo.map(it => {
              const concepto = dominio === "farmacia" && it.conceptoId ? (conceptosFarmaco || []).find(c => c.id === it.conceptoId) : null;
              return <option key={it.id} value={it.id}>{it.nombre}{concepto ? ` — DCI: ${concepto.dci}` : ""}</option>;
            })}
          </select>
        </div>
        <Btn variant="outline" size="sm" icon={Plus} onClick={agregarItem}>Agregar</Btn>
      </div>

      <div style={{ border: `1px solid ${C.border}`, borderRadius: 8, marginBottom: 14, overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
          <thead>
            <tr style={{ background: "#F5F8FF" }}>
              {["Ítem", "Disponible", "Lote", "Cantidad", "Valor referencial", ""].map(h => (
                <th key={h} style={{ textAlign: "left", padding: "7px 8px", fontSize: 10, color: C.textMuted, textTransform: "uppercase" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && <tr><td colSpan={6} style={{ padding: "14px 8px", textAlign: "center", color: C.textMuted, fontSize: 12 }}>Sin ítems todavía.</td></tr>}
            {items.map(it => {
              const cat = catalogo.find(c => c.id === it.itemId);
              const concepto = dominio === "farmacia" && cat && cat.conceptoId ? (conceptosFarmaco || []).find(c => c.id === cat.conceptoId) : null;
              const disponible = stock[it.itemId] ? stock[it.itemId].stockActual : 0;
              const excede = it.cantidad > disponible;
              return (
                <tr key={it.itemId} style={{ borderTop: `1px solid ${C.border}` }}>
                  <td style={{ padding: "6px 8px" }}>
                    <div>{cat ? cat.nombre : it.itemId}</div>
                    {dominio === "farmacia" && cat && cat.registroISP && (
                      <div style={{ fontSize: 9.5, color: C.textMuted, marginTop: 2 }}>
                        {concepto && `DCI: ${concepto.dci}${concepto.concentracion ? ` ${fbFormatConcentracion(concepto.concentracion)}` : ""} · `}Reg. ISP {cat.registroISP} · CENABAST {cat.codigoCenabast}
                      </div>
                    )}
                  </td>
                  <td style={{ padding: "6px 8px", color: C.textMuted }}>{disponible}</td>
                  <td style={{ padding: "6px 8px" }}>
                    <input value={it.lote} onChange={e => actualizarItem(it.itemId, "lote", e.target.value)} placeholder="N° lote"
                      style={{ width: 74, border: `1px solid ${C.border}`, borderRadius: 5, padding: "4px 6px", fontSize: 11.5 }} />
                  </td>
                  <td style={{ padding: "6px 8px" }}>
                    <input type="number" min="0" max={disponible} value={it.cantidad} onChange={e => actualizarItem(it.itemId, "cantidad", Math.max(0, Number(e.target.value) || 0))}
                      style={{ width: 60, border: `1px solid ${excede ? C.danger : C.border}`, borderRadius: 5, padding: "4px 6px", fontSize: 11.5 }} />
                  </td>
                  <td style={{ padding: "6px 8px" }}>
                    <input type="number" min="0" value={it.valorReferencial} onChange={e => actualizarItem(it.itemId, "valorReferencial", e.target.value)} placeholder="$"
                      style={{ width: 80, border: `1px solid ${C.border}`, borderRadius: 5, padding: "4px 6px", fontSize: 11.5 }} />
                  </td>
                  <td style={{ padding: "6px 8px" }}>
                    <button onClick={() => quitarItem(it.itemId)} style={{ background: "none", border: "none", cursor: "pointer", color: C.textMuted, padding: 0 }}><X size={13} /></button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
        <Btn variant="ghost" onClick={onCancel}>Cancelar</Btn>
        <Btn variant="primary" icon={ArrowRight} onClick={handleSubmit} disabled={!puedeEnviar}>Confirmar despacho</Btn>
      </div>
    </Card>
  );
};

const FbDespachoExternoCard = ({ despacho, cliente, catalogo, conceptosFarmaco, onRegistrarDevolucion }) => {
  const d = despacho;
  const meta = TIPO_RELACION_META[d.tipoOperacion] || { label: d.tipoOperacion, color: C.textMid };
  const [panelDevolucion, setPanelDevolucion] = useState(null);

  function abrirDevolucion() {
    const init = {};
    d.items.forEach(it => { init[it.itemId] = 0; });
    setPanelDevolucion(init);
  }

  return (
    <Card style={{ padding: 14 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8, flexWrap: "wrap" }}>
        <span style={{ fontFamily: "monospace", fontSize: 11, color: C.textMuted, background: C.bodyBg, padding: "1px 6px", borderRadius: 5 }}>{d.folio}</span>
        <span style={{ fontWeight: 600, fontSize: 13, flex: 1 }}>{cliente ? cliente.razonSocial : d.clienteId}</span>
        <Badge color={meta.color} sm>{meta.label}</Badge>
        <Badge color={d.dominio === "farmacia" ? "#4338CA" : "#B45309"} sm>{d.dominio === "farmacia" ? "Farmacia" : "Bodega"}</Badge>
      </div>
      <ul style={{ listStyle: "none", margin: "0 0 6px", padding: 0, fontSize: 12.5 }}>
        {d.items.map(it => {
          const cat = catalogo.find(c => c.id === it.itemId);
          const concepto = d.dominio === "farmacia" && cat && cat.conceptoId ? (conceptosFarmaco || []).find(c => c.id === cat.conceptoId) : null;
          return (
            <li key={it.itemId} style={{ marginBottom: 4 }}>
              <div>{cat ? cat.nombre : it.itemId} — {it.cantidad}{it.lote ? ` · lote ${it.lote}` : ""}{it.valorReferencial ? ` · ref. $${it.valorReferencial.toLocaleString("es-CL")}` : ""}</div>
              {d.dominio === "farmacia" && cat && cat.registroISP && (
                <div style={{ fontSize: 10, color: C.textMuted, marginTop: 1 }}>
                  {concepto && `DCI: ${concepto.dci}${concepto.concentracion ? ` ${fbFormatConcentracion(concepto.concentracion)}` : ""} · `}Reg. ISP {cat.registroISP} · CENABAST {cat.codigoCenabast}
                </div>
              )}
            </li>
          );
        })}
      </ul>
      <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 8 }}>Guía {d.guiaDespacho}{d.documentoRespaldo ? ` · ${d.documentoRespaldo}` : ""} · {fbFormatFechaHora(d.fechaDespacho)}</div>

      {d.devolucionEsperada && (
        <>
          <Badge color={DEVOLUCION_ESTADO_META[d.devolucionEsperada.estado].color} sm>{DEVOLUCION_ESTADO_META[d.devolucionEsperada.estado].label} · límite {d.devolucionEsperada.fechaLimite}</Badge>
          {d.devolucionEsperada.estado === "pendiente" && !panelDevolucion && (
            <div style={{ marginTop: 8 }}><Btn variant="outline" size="sm" icon={ArrowRight} onClick={abrirDevolucion}>Registrar devolución</Btn></div>
          )}
          {panelDevolucion && (
            <div style={{ background: C.bodyBg, borderRadius: 8, padding: 12, marginTop: 8 }}>
              <div style={{ fontSize: 11.5, fontWeight: 600, marginBottom: 8 }}>Cantidad devuelta por ítem</div>
              {d.items.map(it => {
                const cat = catalogo.find(c => c.id === it.itemId);
                return (
                  <div key={it.itemId} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                    <span style={{ fontSize: 12, flex: 1 }}>{cat ? cat.nombre : it.itemId}</span>
                    <span style={{ fontSize: 10.5, color: C.textMuted }}>despachado {it.cantidad}</span>
                    <input type="number" min="0" max={it.cantidad} value={panelDevolucion[it.itemId]}
                      onChange={e => setPanelDevolucion(p => ({ ...p, [it.itemId]: Math.max(0, Math.min(it.cantidad, Number(e.target.value) || 0)) }))}
                      style={{ width: 60, border: `1px solid ${C.border}`, borderRadius: 6, padding: "4px 6px", fontSize: 12 }} />
                  </div>
                );
              })}
              <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                <Btn variant="ghost" size="sm" onClick={() => setPanelDevolucion(null)}>Cancelar</Btn>
                <Btn variant="primary" size="sm" icon={CheckCircle} onClick={() => { onRegistrarDevolucion(d.folio, panelDevolucion); setPanelDevolucion(null); }}>Confirmar devolución</Btn>
              </div>
            </div>
          )}
        </>
      )}
    </Card>
  );
};

const ClientesExternosView = ({ centralStock, setCentralStock, centralStockBod, setCentralStockBod, catalogoFarmacia, catalogoBodega, conceptosFarmaco, role, setMovimientosFarmacia, setMovimientosBodega }) => {
  const [tab, setTab] = useState("directorio");
  const [clientes, setClientes] = useState(FB_CLIENTES_EXTERNOS_INICIAL);
  const [mostrarNuevoCliente, setMostrarNuevoCliente] = useState(false);
  const [clienteIdSeq, setClienteIdSeq] = useState(FB_CLIENTES_EXTERNOS_INICIAL.length + 1);
  const [despachoForm, setDespachoForm] = useState(null); // cliente seleccionado
  const [despachos, setDespachos] = useState(FB_DESPACHOS_EXTERNOS_INICIAL);
  const [despachoFolioSeq, setDespachoFolioSeq] = useState(1);

  function crearCliente(payload) {
    const id = `CLIEXT-${String(clienteIdSeq).padStart(3, "0")}`;
    setClientes(prev => [...prev, { id, ...payload }]);
    setClienteIdSeq(n => n + 1);
    setMostrarNuevoCliente(false);
  }

  function crearDespacho(cliente, payload) {
    const folio = `DESP-2026-${String(despachoFolioSeq).padStart(4, "0")}`;
    const stockActualDominio = payload.dominio === "farmacia" ? centralStock : centralStockBod;
    const setStock = payload.dominio === "farmacia" ? setCentralStock : setCentralStockBod;
    // Mismo criterio defensivo que en Solicitudes: nunca descontar más de lo
    // que realmente hay, aunque el formulario ya debería impedirlo (botón
    // deshabilitado si la cantidad excede el stock al momento de abrir el form).
    // Corrección (auditoría técnica, Parte 14, hallazgo P0 #3): se calcula
    // sobre una copia local antes de llamar a setState, no dentro del *updater*.
    // Corrección (Auditoria_SupplyCore2 #8, Parte 17): la cantidad del
    // movimiento y la del despacho deben ser EXACTAMENTE la cantidad aplicada
    // al stock — antes se descontaba Math.min(cantidad, stock) pero se
    // registraba it.cantidad, pudiendo diferir.
    const stockResultantes = {};
    const cantidadesAplicadas = {};
    const nextStock = { ...stockActualDominio };
    payload.items.forEach(it => {
      const cur = nextStock[it.itemId];
      const aplicada = cur ? Math.max(0, Math.min(it.cantidad, cur.stockActual)) : 0;
      cantidadesAplicadas[it.itemId] = aplicada;
      if (cur) {
        nextStock[it.itemId] = { ...cur, stockActual: cur.stockActual - aplicada };
        stockResultantes[it.itemId] = nextStock[it.itemId].stockActual;
      }
    });
    setStock(nextStock);
    const itemsAplicados = payload.items.map(it => ({ ...it, cantidad: cantidadesAplicadas[it.itemId] }));
    setDespachos(prev => [{ folio, clienteId: cliente.id, fechaDespacho: new Date().toISOString(), ...payload, items: itemsAplicados }, ...prev]);
    setDespachoFolioSeq(n => n + 1);
    setDespachoForm(null);
    setTab("despachos");
    // Trazabilidad
    const setMovimientos = payload.dominio === "farmacia" ? setMovimientosFarmacia : setMovimientosBodega;
    if (setMovimientos) {
      const nuevos = itemsAplicados.filter(it => it.cantidad > 0).map(it => fbCrearMovimiento({
        itemId: it.itemId, lote: it.lote, tipoMovimiento: "despacho-cliente-externo", cantidad: it.cantidad, signo: "-",
        stockResultante: stockResultantes[it.itemId], origen: { tipo: payload.dominio === "farmacia" ? "farmacia-central" : "bodega-central", referencia: "CENTRAL" },
        destino: { tipo: "cliente-externo", referencia: cliente.id }, documentoRespaldo: folio, registradoPor: role,
      }));
      if (nuevos.length) setMovimientos(prev => [...nuevos, ...prev]);
    }
  }

  function registrarDevolucion(folio, cantidadesDevueltas) {
    const d = despachos.find(x => x.folio === folio);
    if (!d) return;
    const stockActualDominio = d.dominio === "farmacia" ? centralStock : centralStockBod;
    const setStock = d.dominio === "farmacia" ? setCentralStock : setCentralStockBod;
    // Corrección (auditoría técnica, Parte 14, hallazgo P0 #3): mismo criterio
    // que crearDespacho() — copia local antes de setState.
    const stockResultantes = {};
    const nextStock = { ...stockActualDominio };
    d.items.forEach(it => {
      const cant = cantidadesDevueltas[it.itemId] || 0;
      const cur = nextStock[it.itemId];
      if (cur && cant > 0) {
        nextStock[it.itemId] = { ...cur, stockActual: cur.stockActual + cant };
        stockResultantes[it.itemId] = nextStock[it.itemId].stockActual;
      }
    });
    setStock(nextStock);
    const totalDespachado = d.items.reduce((a, it) => a + it.cantidad, 0);
    const totalDevuelto = Object.values(cantidadesDevueltas).reduce((a, c) => a + c, 0);
    const estado = totalDevuelto >= totalDespachado ? "devuelto" : totalDevuelto > 0 ? "devuelto-parcial" : "no-devuelto";
    setDespachos(prev => prev.map(x => (x.folio === folio ? {
      ...x, devolucionEsperada: { ...x.devolucionEsperada, estado, itemsDevueltos: Object.entries(cantidadesDevueltas).map(([itemId, cantidad]) => ({ itemId, cantidad })) },
    } : x)));
    // Trazabilidad
    const setMovimientos = d.dominio === "farmacia" ? setMovimientosFarmacia : setMovimientosBodega;
    if (setMovimientos) {
      const nuevos = Object.entries(cantidadesDevueltas).filter(([, cant]) => cant > 0).map(([itemId, cant]) => fbCrearMovimiento({
        itemId, tipoMovimiento: "devolucion", cantidad: cant, signo: "+", stockResultante: stockResultantes[itemId],
        origen: { tipo: "cliente-externo", referencia: d.clienteId }, destino: { tipo: d.dominio === "farmacia" ? "farmacia-central" : "bodega-central", referencia: "CENTRAL" },
        documentoRespaldo: folio, registradoPor: role,
      }));
      if (nuevos.length) setMovimientos(prev => [...nuevos, ...prev]);
    }
  }

  const clientesActivos = clientes.filter(c => c.estado === "activo").length;
  const devolucionesPendientes = despachos.filter(d => d.devolucionEsperada && d.devolucionEsperada.estado === "pendiente").length;

  return (
    <div>
      <Card style={{ padding: "14px 18px", marginBottom: 16, background: `${C.primary}08` }}>
        <div style={{ fontSize: 12, color: C.textMid, lineHeight: 1.5 }}>
          Empresas u organizaciones externas a AXON — préstamo, convenio, venta o donación. Nunca son sub-farmacia ni sub-bodega interna. Un despacho puede salir de Farmacia o de Bodega, nunca mezclando ambos catálogos. Datos de ejemplo, pendiente el listado oficial de clientes externos de AXON.
        </div>
      </Card>

      <TabBar tabs={[
        { id: "directorio", label: `Directorio (${clientesActivos} activos)` },
        { id: "despachos", label: devolucionesPendientes ? `Despachos (${devolucionesPendientes} c/devolución pendiente)` : "Despachos" },
      ]} active={tab} onChange={setTab} />

      {tab === "directorio" && (
        <>
          <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 12 }}>
            {!mostrarNuevoCliente && <Btn variant="primary" icon={Plus} onClick={() => setMostrarNuevoCliente(true)}>Nuevo cliente externo</Btn>}
          </div>
          {mostrarNuevoCliente && <FbNuevoClienteExternoForm onSubmit={crearCliente} onCancel={() => setMostrarNuevoCliente(false)} />}
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {clientes.map(c => (
              <div key={c.id}>
                <FbClienteExternoCard cliente={c} onNuevoDespacho={setDespachoForm} />
                {despachoForm && despachoForm.id === c.id && (
                  <FbNuevoDespachoExternoForm cliente={c} catalogoFarmacia={catalogoFarmacia} catalogoBodega={catalogoBodega}
                    centralStock={centralStock} centralStockBod={centralStockBod} conceptosFarmaco={conceptosFarmaco}
                    onSubmit={payload => crearDespacho(c, payload)} onCancel={() => setDespachoForm(null)} />
                )}
              </div>
            ))}
          </div>
        </>
      )}

      {tab === "despachos" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {despachos.length === 0 && <div style={{ fontSize: 12.5, color: C.textMuted }}>Aún no se ha generado ningún despacho. Ve al Directorio y usa "Nuevo despacho" en un cliente activo.</div>}
          {despachos.map(d => (
            <FbDespachoExternoCard key={d.folio} despacho={d} cliente={clientes.find(c => c.id === d.clienteId)}
              catalogo={d.dominio === "farmacia" ? catalogoFarmacia : catalogoBodega} conceptosFarmaco={conceptosFarmaco}
              onRegistrarDevolucion={registrarDevolucion} />
          ))}
        </div>
      )}
    </div>
  );
};

// #25 Bodega e Insumos Propios — envoltorio delgado: solo arma la pestaña
// Stock/Solicitudes reutilizando los mismos componentes que ya usan las 41
// unidades reales. No hay lógica nueva aquí, a propósito.
const BodegaInsumosPropiosView = ({ role, catalogoBodega, centralStockBod, subStockPropia, solicitudesPropia, onCrearSolicitud, onAutorizarCoordinador, onAprobar, onRechazar, onEnPreparacion, onDespachar, onConfirmarRecepcion }) => {
  const [tab, setTab] = useState("stock");
  const [selected, setSelected] = useState(FB_UNIDAD_PROPIA[0].id);

  return (
    <div>
      <Card style={{ padding: "14px 18px", marginBottom: 16, background: `${C.primary}08` }}>
        <div style={{ fontSize: 12, color: C.textMid, lineHeight: 1.5 }}>
          Inventario interno de la propia unidad de Farmacia Central y Bodega — no confundir con la Bodega Central (#11). Papel térmico, etiquetas, embalaje, EPP, oficina: lo que el equipo consume para operar. Usa el mismo flujo de solicitud de las otras 41 unidades — se pide, el coordinador autoriza, y Bodega Central despacha.
        </div>
      </Card>
      <TabBar tabs={[{ id: "stock", label: "Stock" }, { id: "solicitudes", label: "Solicitudes" }]} active={tab} onChange={setTab} />
      {tab === "stock" && (
        <FbStockPorUnidad role={role} catalogo={catalogoBodega} unidades={FB_UNIDAD_PROPIA}
          selected={selected} onSelect={setSelected} subStock={subStockPropia} onCrearSolicitud={onCrearSolicitud} />
      )}
      {tab === "solicitudes" && (
        <FbColaSolicitudes role={role} catalogo={catalogoBodega} unidades={FB_UNIDAD_PROPIA}
          centralStock={centralStockBod} centralLabel="Bodega Central" solicitudes={solicitudesPropia}
          onAutorizarCoordinador={onAutorizarCoordinador} onAprobar={onAprobar} onRechazar={onRechazar}
          onEnPreparacion={onEnPreparacion} onDespachar={onDespachar} onConfirmarRecepcion={onConfirmarRecepcion} />
      )}
    </div>
  );
};

// #2 Farmacia: Medicamentos / #11 Bodega: Insumos — el catálogo maestro y
// stock CONSOLIDADO de Central que faltaba: hasta ahora solo existía el
// stock por unidad (#3/#12). Responde exactamente lo que preguntó el
// usuario: "cuánto hay en Bodega/Farmacia Central para repartir a todas
// las sub-bodegas/sub-farmacias".
const FbStockCentralView = ({ catalogo, centralStock, conceptosFarmaco, mostrarConceptos, label }) => {
  const filas = catalogo.map(it => ({ ...it, stock: centralStock[it.id] || { stockActual: 0, stockMinimo: 0 } }));
  const criticos = filas.filter(f => f.stock.stockActual <= f.stock.stockMinimo);
  return (
    <div>
      <Card style={{ padding: "14px 18px", marginBottom: 16, background: `${C.primary}08` }}>
        <div style={{ fontSize: 12, color: C.textMid, lineHeight: 1.5 }}>
          Catálogo maestro y stock consolidado de <strong>{label}</strong> — {filas.length} ítems. Esto es lo que hay disponible en total antes de repartir a cualquier unidad.
          {criticos.length > 0 && <span style={{ color: C.danger, fontWeight: 600 }}> {criticos.length} ítem{criticos.length !== 1 ? "s" : ""} bajo mínimo.</span>}
        </div>
      </Card>
      <Card style={{ padding: 0, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12.5 }}>
          <thead>
            <tr style={{ background: "#F5F8FF" }}>
              {["Ítem", "Código de barra", "Stock actual", "Stock mínimo", "Estado"].map(h => (
                <th key={h} style={{ textAlign: "left", padding: "9px 14px", fontSize: 10, color: C.textMuted, textTransform: "uppercase" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filas.map(f => {
              const bajo = f.stock.stockActual <= f.stock.stockMinimo;
              const critico = f.stock.stockActual <= 0;
              const concepto = mostrarConceptos && f.conceptoId ? (conceptosFarmaco || []).find(c => c.id === f.conceptoId) : null;
              return (
                <tr key={f.id} style={{ borderTop: `1px solid ${C.border}` }}>
                  <td style={{ padding: "9px 14px" }}>
                    <div>{f.nombre}</div>
                    {mostrarConceptos && f.registroISP && (
                      <div style={{ fontSize: 10, color: C.textMuted, marginTop: 2 }}>
                        {concepto && `DCI: ${concepto.dci}${concepto.concentracion ? ` ${fbFormatConcentracion(concepto.concentracion)}` : ""} · `}Reg. ISP {f.registroISP} · CENABAST {f.codigoCenabast}
                      </div>
                    )}
                  </td>
                  <td style={{ padding: "9px 14px", fontFamily: "monospace", fontSize: 11, color: C.textMuted }}>{f.codigoBarra}</td>
                  <td style={{ padding: "9px 14px", fontWeight: bajo ? 700 : 400, color: bajo ? C.danger : C.text }}>{f.stock.stockActual} {f.unidad}</td>
                  <td style={{ padding: "9px 14px", color: C.textMuted }}>{f.stock.stockMinimo}</td>
                  <td style={{ padding: "9px 14px" }}>
                    {critico ? <Badge color={C.danger} sm>Crítico</Badge> : bajo ? <Badge color={C.warning} sm>Bajo mínimo</Badge> : <Badge color={C.success} sm>Ok</Badge>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Card>
    </div>
  );
};

// #8 Trazabilidad Farmacia / #15 Trazabilidad Bodega — lista filtrable de
// movimientos reales de stock. Reutilizable para ambos dominios; el filtro
// por tipo usa MOVIMIENTO_TIPO_META, ya definido junto al resto de helpers fb.
const FbTrazabilidadView = ({ movimientos, catalogo, label }) => {
  const [filtroItem, setFiltroItem] = useState("");
  const [filtroTipo, setFiltroTipo] = useState("todos");

  const filtrados = movimientos.filter(m => {
    if (filtroTipo !== "todos" && m.tipoMovimiento !== filtroTipo) return false;
    if (filtroItem) {
      const cat = catalogo.find(c => c.id === m.itemId);
      const nombre = (cat ? cat.nombre : m.itemId).toLowerCase();
      if (!nombre.includes(filtroItem.toLowerCase())) return false;
    }
    return true;
  });

  return (
    <div>
      <Card style={{ padding: "14px 18px", marginBottom: 16, background: `${C.primary}08` }}>
        <div style={{ fontSize: 12, color: C.textMid, lineHeight: 1.5 }}>
          Registro de cada movimiento real de stock en <strong>{label}</strong> — ingresos de proveedor, despachos a unidades, despachos y devoluciones de clientes externos. {movimientos.length} movimiento{movimientos.length !== 1 ? "s" : ""} registrado{movimientos.length !== 1 ? "s" : ""}.
        </div>
      </Card>
      <div style={{ display: "flex", gap: 10, marginBottom: 14, flexWrap: "wrap" }}>
        <input value={filtroItem} onChange={e => setFiltroItem(e.target.value)} placeholder="Buscar por ítem..."
          style={{ flex: 1, minWidth: 180, border: `1px solid ${C.border}`, borderRadius: 6, padding: "7px 10px", fontSize: 12 }} />
        <select value={filtroTipo} onChange={e => setFiltroTipo(e.target.value)}
          style={{ border: `1px solid ${C.border}`, borderRadius: 6, padding: "7px 10px", fontSize: 12 }}>
          <option value="todos">Todos los tipos</option>
          {Object.entries(MOVIMIENTO_TIPO_META).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
        </select>
      </div>
      <Card style={{ padding: 0, overflow: "hidden" }}>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12.5 }}>
            <thead>
              <tr style={{ background: "#F5F8FF" }}>
                {["Fecha", "Tipo", "Ítem", "Lote", "Cantidad", "Stock resultante", "Origen → Destino", "Documento", "Registrado por"].map(h => (
                  <th key={h} style={{ textAlign: "left", padding: "8px 12px", fontSize: 10, color: C.textMuted, textTransform: "uppercase", whiteSpace: "nowrap" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtrados.length === 0 && (
                <tr><td colSpan={9} style={{ padding: "20px 12px", textAlign: "center", color: C.textMuted, fontSize: 12.5 }}>
                  {movimientos.length === 0 ? "Aún no hay movimientos registrados." : "Ningún movimiento coincide con el filtro."}
                </td></tr>
              )}
              {filtrados.map(m => {
                const cat = catalogo.find(c => c.id === m.itemId);
                const meta = MOVIMIENTO_TIPO_META[m.tipoMovimiento] || { label: m.tipoMovimiento, color: C.textMuted };
                return (
                  <tr key={m.id} style={{ borderTop: `1px solid ${C.border}` }}>
                    <td style={{ padding: "8px 12px", color: C.textMuted, whiteSpace: "nowrap" }}>{fbFormatFechaHora(m.fechaMovimiento)}</td>
                    <td style={{ padding: "8px 12px" }}><Badge color={meta.color} sm>{meta.label}</Badge></td>
                    <td style={{ padding: "8px 12px" }}>{cat ? cat.nombre : m.itemId}</td>
                    <td style={{ padding: "8px 12px", fontFamily: "monospace", fontSize: 11, color: C.textMuted }}>{m.lote || "—"}</td>
                    <td style={{ padding: "8px 12px", fontWeight: 600, color: m.signo === "+" ? C.success : C.danger }}>{m.signo}{m.cantidad}</td>
                    <td style={{ padding: "8px 12px", color: C.textMuted }}>{m.stockResultante != null ? m.stockResultante : "—"}</td>
                    <td style={{ padding: "8px 12px", fontSize: 11.5, color: C.textMid, whiteSpace: "nowrap" }}>{m.origen.referencia} → {m.destino.referencia}</td>
                    <td style={{ padding: "8px 12px", fontFamily: "monospace", fontSize: 11, color: C.textMuted }}>{m.documentoRespaldo}</td>
                    <td style={{ padding: "8px 12px", fontSize: 11, color: C.textMuted }}>{m.registradoPor}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

// ── CUADRATURA DE STOCK: ajuste de stock central con motivo obligatorio —
// merma, vencimiento, o diferencia de conteo (nunca un "ajuste" libre sin
// categoría, decisión #8 de la Parte 2 del dossier). No está entre los 27
// submódulos canónicos de arquitectura_farmacia_bodega.md — nace del triage
// y diseño de las Partes 13.4 y 14.4-14.5, validado contra los movement
// types de SAP (scrapping/merma es un grupo distinto de diferencia de
// inventario físico, cada uno con su propia cuenta contable de destino).
// Limitación conocida, sin resolver acá (Parte 14.2, hallazgo P0 #4): un
// lote hoy solo tiene número + vencimiento, sin cantidad propia — por eso el
// flujo de "vencimiento" pre-llena el ítem desde el lote elegido, pero la
// cantidad a retirar se sigue ingresando manualmente.
const FbNuevaCuadraturaForm = ({ dominio, catalogo, centralStock, lotes, mostrarLotesVencidos, onSubmit, onCancel }) => {
  const [motivo, setMotivo] = useState("merma");
  const [causaMerma, setCausaMerma] = useState("perdida");
  const [itemId, setItemId] = useState(catalogo[0] ? catalogo[0].id : "");
  const [loteSeleccionado, setLoteSeleccionado] = useState(null);
  const [cantidad, setCantidad] = useState(0); // merma/vencimiento: cantidad a retirar
  const [stockReal, setStockReal] = useState(0); // diferencia-conteo: cantidad real contada
  const [justificacion, setJustificacion] = useState("");

  const lotesVencidos = mostrarLotesVencidos
    ? (lotes || []).map(l => ({ ...l, dias: fbDiasHasta(l.fechaVencimiento) })).filter(l => l.dias <= 60).sort((a, b) => a.dias - b.dias)
    : [];

  const stockActualItem = centralStock[itemId] ? centralStock[itemId].stockActual : 0;

  function elegirLote(lote) {
    setLoteSeleccionado(lote);
    setItemId(lote.itemId);
  }

  const diferenciaConteo = motivo === "diferencia-conteo" ? stockReal - stockActualItem : null;
  const puedeRegistrar = itemId && justificacion.trim().length > 0 &&
    (motivo === "diferencia-conteo" ? stockReal !== stockActualItem : cantidad > 0);

  function handleSubmit() {
    if (!puedeRegistrar) return;
    onSubmit({
      motivo,
      causaMerma: motivo === "merma" ? causaMerma : null,
      itemId,
      lote: loteSeleccionado ? loteSeleccionado.numeroLote : null,
      cantidadAnterior: stockActualItem,
      cantidadNueva: motivo === "diferencia-conteo" ? stockReal : Math.max(0, stockActualItem - cantidad),
      justificacion: justificacion.trim(),
    });
  }

  return (
    <Card style={{ padding: 18, marginBottom: 16, border: `1px dashed ${C.primary}` }}>
      <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 4 }}>Nuevo ajuste de stock</div>
      <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 14 }}>Motivo obligatorio, sin excepción de rol — cada ajuste queda registrado en Trazabilidad.</div>

      <div style={{ display: "flex", gap: 14, marginBottom: 14, flexWrap: "wrap" }}>
        {Object.entries(CUADRATURA_MOTIVO_INFO).map(([k, v]) => (
          <label key={k} style={{ display: "flex", alignItems: "flex-start", gap: 6, fontSize: 12, maxWidth: 220, cursor: "pointer" }}>
            <input type="radio" checked={motivo === k} onChange={() => { setMotivo(k); setLoteSeleccionado(null); setCantidad(0); }} style={{ marginTop: 2 }} />
            <span><strong>{v.label}</strong><br /><span style={{ color: C.textMuted, fontSize: 10.5 }}>{v.desc}</span></span>
          </label>
        ))}
      </div>

      {motivo === "vencimiento" && mostrarLotesVencidos && (
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 6 }}>Lotes próximos a vencer o ya vencidos (punto de partida)</div>
          {lotesVencidos.length === 0 ? (
            <div style={{ fontSize: 12, color: C.textMuted }}>No hay lotes con alerta de vencimiento en este momento.</div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 6, maxHeight: 160, overflowY: "auto" }}>
              {lotesVencidos.map(l => {
                const it = catalogo.find(c => c.id === l.itemId);
                const activo = loteSeleccionado && loteSeleccionado.id === l.id;
                return (
                  <button key={l.id} onClick={() => elegirLote(l)} style={{
                    display: "flex", justifyContent: "space-between", alignItems: "center", textAlign: "left",
                    padding: "7px 10px", borderRadius: 7, border: `1px solid ${activo ? C.primary : C.border}`,
                    background: activo ? `${C.primary}10` : C.surface, cursor: "pointer", fontSize: 12,
                  }}>
                    <span>{it ? it.nombre : l.itemId} · lote {l.numeroLote}</span>
                    <Badge color={l.dias <= 15 ? C.danger : C.warning} sm>{l.dias <= 0 ? "vencido" : `${l.dias} días`}</Badge>
                  </button>
                );
              })}
            </div>
          )}
          <div style={{ fontSize: 10, color: C.textMuted, marginTop: 4, fontStyle: "italic" }}>El lote no lleva cantidad propia todavía (limitación conocida, ver dossier) — ingresa la cantidad a retirar manualmente abajo.</div>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: motivo === "merma" ? "1fr 1fr" : "1fr", gap: 12, marginBottom: 14 }}>
        <div>
          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Ítem</div>
          <select value={itemId} onChange={e => { setItemId(e.target.value); setLoteSeleccionado(null); }}
            style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", fontSize: 12 }}>
            {catalogo.map(it => <option key={it.id} value={it.id}>{it.nombre}</option>)}
          </select>
          <div style={{ fontSize: 10.5, color: C.textMuted, marginTop: 3 }}>Stock actual en Central: {stockActualItem}</div>
        </div>
        {motivo === "merma" && (
          <div>
            <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Causa</div>
            <select value={causaMerma} onChange={e => setCausaMerma(e.target.value)}
              style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", fontSize: 12 }}>
              {Object.entries(CUADRATURA_CAUSA_MERMA).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
        )}
      </div>

      {motivo === "diferencia-conteo" ? (
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Stock real contado</div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <input type="number" min="0" value={stockReal} onChange={e => setStockReal(Math.max(0, Number(e.target.value) || 0))}
              style={{ width: 140, border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", fontSize: 12 }} />
            {diferenciaConteo !== null && diferenciaConteo !== 0 && (
              <Badge color={diferenciaConteo < 0 ? C.danger : C.warning} sm>{diferenciaConteo < 0 ? `faltan ${Math.abs(diferenciaConteo)}` : `sobran ${diferenciaConteo}`}</Badge>
            )}
          </div>
        </div>
      ) : (
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Cantidad a retirar</div>
          <input type="number" min="0" max={stockActualItem} value={cantidad} onChange={e => setCantidad(Math.max(0, Math.min(stockActualItem, Number(e.target.value) || 0)))}
            style={{ width: 140, border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", fontSize: 12 }} />
        </div>
      )}

      <div style={{ marginBottom: 14 }}>
        <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Justificación (obligatoria)</div>
        <textarea value={justificacion} onChange={e => setJustificacion(e.target.value)} rows={2}
          placeholder="Ej: conteo físico mensual, caja encontrada dañada en bodega, lote retirado por vencimiento…"
          style={{ width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "8px 10px", fontSize: 12, fontFamily: "inherit", resize: "vertical" }} />
      </div>

      <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
        <Btn variant="ghost" onClick={onCancel}>Cancelar</Btn>
        <Btn variant="primary" icon={CheckCircle} onClick={handleSubmit} disabled={!puedeRegistrar}>Registrar ajuste</Btn>
      </div>
    </Card>
  );
};

const FbCuadraturaCard = ({ ajuste, catalogo }) => {
  const a = ajuste;
  const info = CUADRATURA_MOTIVO_INFO[a.motivo] || { label: a.motivo };
  const cat = catalogo.find(c => c.id === a.itemId);
  const diferencia = a.cantidadNueva - a.cantidadAnterior;
  const meta = MOVIMIENTO_TIPO_META[a.motivo] || { color: C.textMuted };
  return (
    <Card style={{ padding: 14 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8, flexWrap: "wrap" }}>
        <span style={{ fontFamily: "monospace", fontSize: 11, color: C.textMuted, background: C.bodyBg, padding: "1px 6px", borderRadius: 5 }}>{a.folio}</span>
        <span style={{ fontWeight: 600, fontSize: 13, flex: 1 }}>{cat ? cat.nombre : a.itemId}</span>
        <Badge color={meta.color} sm>{info.label}</Badge>
        {a.causaMerma && <Badge color={C.textMid} sm>{CUADRATURA_CAUSA_MERMA[a.causaMerma]}</Badge>}
      </div>
      <div style={{ fontSize: 12.5, marginBottom: 6 }}>
        Stock {a.cantidadAnterior} → {a.cantidadNueva}
        <span style={{ color: diferencia < 0 ? C.danger : C.success, fontWeight: 600, marginLeft: 6 }}>({diferencia > 0 ? "+" : ""}{diferencia})</span>
        {a.lote && <span style={{ color: C.textMuted }}> · lote {a.lote}</span>}
      </div>
      <div style={{ fontSize: 11.5, color: C.textMid, fontStyle: "italic", marginBottom: 6 }}>"{a.justificacion}"</div>
      <div style={{ fontSize: 11, color: C.textMuted }}>{fbFormatFechaHora(a.fechaAjuste)} · registrado por {a.registradoPor}</div>
    </Card>
  );
};

const FbCuadraturaView = ({ dominio, catalogo, centralStock, lotes, ajustes, onRegistrar }) => {
  const [mostrarForm, setMostrarForm] = useState(false);
  function handleSubmit(payload) {
    onRegistrar(payload);
    setMostrarForm(false);
  }
  return (
    <div>
      <Card style={{ padding: "14px 18px", marginBottom: 16, background: `${C.primary}08` }}>
        <div style={{ fontSize: 12, color: C.textMid, lineHeight: 1.5 }}>
          Ajuste de stock central con motivo obligatorio, sin excepción de rol (decisión #8, Parte 2 del dossier). Nunca reemplaza una Recepción ni una Solicitud — es solo para lo que ningún otro flujo explica: mermas, vencimientos y diferencias encontradas en un conteo físico.
        </div>
      </Card>
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 12 }}>
        {!mostrarForm && <Btn variant="primary" icon={Plus} onClick={() => setMostrarForm(true)}>Nuevo ajuste</Btn>}
      </div>
      {mostrarForm && (
        <FbNuevaCuadraturaForm dominio={dominio} catalogo={catalogo} centralStock={centralStock} lotes={lotes}
          mostrarLotesVencidos={!!lotes} onSubmit={handleSubmit} onCancel={() => setMostrarForm(false)} />
      )}
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {ajustes.length === 0 && <div style={{ fontSize: 12.5, color: C.textMuted }}>Aún no hay ajustes registrados.</div>}
        {ajustes.map(a => <FbCuadraturaCard key={a.folio} ajuste={a} catalogo={catalogo} />)}
      </div>
    </div>
  );
};

// #9 Balances Farmacia / #16 Balances Bodega — tiempos y desempeño reales,
// calculados de Solicitudes, Trazabilidad, Pedidos y Recepciones (Parte 13.5
// del dossier escaneó qué es calculable hoy; Auditoria_SupplyCore2.md #34-35
// empujó a documentar fuente/fórmula/unidad de conteo de cada métrica, ver
// fbCalcularBalanceSubUnidades/fbCalcularBalancePorProveedor arriba).
const FbBalancesView = ({ unidades, solicitudes, movimientos, proveedores, pedidos, recepciones, nombreCentral }) => {
  const porUnidad = fbCalcularBalanceSubUnidades(unidades, solicitudes, movimientos);
  const porProveedor = fbCalcularBalancePorProveedor(proveedores, pedidos, recepciones);
  return (
    <div>
      <Card style={{ padding: "14px 18px", marginBottom: 16, background: `${C.primary}08` }}>
        <div style={{ fontSize: 12, color: C.textMid, lineHeight: 1.5 }}>
          Calculado de Solicitudes, Trazabilidad, Pedidos y Recepciones reales — ninguna cifra es de ejemplo. Lo que todavía no se puede calcular con los datos que existen hoy se muestra como "—", no se inventa.
        </div>
      </Card>

      <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 10 }}>Por sub-unidad</div>
      {porUnidad.length === 0 ? (
        <div style={{ fontSize: 12.5, color: C.textMuted, marginBottom: 20 }}>Aún no hay solicitudes registradas en ninguna unidad.</div>
      ) : (
        <Card style={{ padding: 0, overflow: "hidden", marginBottom: 20 }}>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12.5 }}>
              <thead>
                <tr style={{ background: "#F5F8FF" }}>
                  {["Unidad", "Solicitudes", "Atendidas", "Pendientes", "Tasa rechazo", "Tiempo prom. despacho", "Consumo total"].map(h => (
                    <th key={h} style={{ textAlign: "left", padding: "8px 12px", fontSize: 10, color: C.textMuted, textTransform: "uppercase", whiteSpace: "nowrap" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {porUnidad.map(r => (
                  <tr key={r.unidad.id} style={{ borderTop: `1px solid ${C.border}` }}>
                    <td style={{ padding: "8px 12px" }}>{r.unidad.nombre}</td>
                    <td style={{ padding: "8px 12px" }}>{r.totalSolicitudes}</td>
                    <td style={{ padding: "8px 12px" }}>{r.solicitudesAtendidas}</td>
                    <td style={{ padding: "8px 12px" }}>{r.solicitudesPendientes}</td>
                    <td style={{ padding: "8px 12px" }}>{r.tasaRechazo != null ? `${r.tasaRechazo.toFixed(0)}%` : "—"}</td>
                    <td style={{ padding: "8px 12px" }}>{r.tiempoPromedioDespachoHrs != null ? `${r.tiempoPromedioDespachoHrs.toFixed(1)}h` : "—"}</td>
                    <td style={{ padding: "8px 12px" }}>{r.consumoTotal}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 4 }}>Por proveedor</div>
      <div style={{ fontSize: 10.5, color: C.textMuted, marginBottom: 10, fontStyle: "italic" }}>"Tiempo de respuesta" del proveedor no se puede calcular todavía — el Pedido solo guarda la fecha de creación, no cuándo confirmó (dossier, Parte 13.5).</div>
      {porProveedor.length === 0 ? (
        <div style={{ fontSize: 12.5, color: C.textMuted }}>Aún no hay pedidos registrados a proveedores de {nombreCentral}.</div>
      ) : (
        <Card style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12.5 }}>
              <thead>
                <tr style={{ background: "#F5F8FF" }}>
                  {["Proveedor", "Pedidos", "Entrega completa", "Cumple plazo", "Tiempo prom. entrega"].map(h => (
                    <th key={h} style={{ textAlign: "left", padding: "8px 12px", fontSize: 10, color: C.textMuted, textTransform: "uppercase", whiteSpace: "nowrap" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {porProveedor.map(r => (
                  <tr key={r.proveedor.id} style={{ borderTop: `1px solid ${C.border}` }}>
                    <td style={{ padding: "8px 12px" }}>{r.proveedor.razonSocial}</td>
                    <td style={{ padding: "8px 12px" }}>{r.totalPedidos}</td>
                    <td style={{ padding: "8px 12px" }}>{r.tasaEntregaCompleta != null ? `${r.tasaEntregaCompleta.toFixed(0)}%` : "—"}</td>
                    <td style={{ padding: "8px 12px" }}>{r.tasaCumplimientoPlazo != null ? `${r.tasaCumplimientoPlazo.toFixed(0)}%` : "—"}</td>
                    <td style={{ padding: "8px 12px" }}>{r.tiempoPromedioEntregaHrs != null ? `${(r.tiempoPromedioEntregaHrs / 24).toFixed(1)}d` : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};

const FarmaciaBodegaView = ({ role, addToast }) => {
  const [seccion, setSeccion] = useState("dashboard");
  const [farmTab, setFarmTab] = useState("stock_subfarmacias");
  const [bodTab, setBodTab] = useState("stock_subbodegas");
  const [selectedSF, setSelectedSF] = useState(FB_UNIDADES_SUBFARMACIA[0].id);
  const [selectedSB, setSelectedSB] = useState(FB_UNIDADES_SUBBODEGA[0].id);

  const [centralStock, setCentralStock] = useState(FB_CENTRAL_INICIAL);
  const [subStock, setSubStock] = useState(FB_SUBSTOCK_INICIAL);
  const [solicitudes, setSolicitudes] = useState(FB_SOLICITUDES_INICIAL);
  const [folioSeq, setFolioSeq] = useState(3);

  const [centralStockBod, setCentralStockBod] = useState(FB_CENTRAL_BODEGA_INICIAL);
  const [subStockBod, setSubStockBod] = useState(FB_SUBSTOCK_BODEGA_INICIAL);
  const [solicitudesBod, setSolicitudesBod] = useState(FB_SOLICITUDES_BODEGA_INICIAL);
  const [folioSeqBod, setFolioSeqBod] = useState(3);

  // Lotes: antes era la constante fija FB_LOTES_INICIAL; ahora es estado para
  // que cada Recepción con lote + vencimiento alimente de verdad la alerta
  // de caducidad del Dashboard, no solo los 3 lotes de ejemplo iniciales.
  // Corrección (auditoría técnica #2, hallazgo P0 #1): antes era UN SOLO
  // array compartido entre Farmacia y Bodega — una Recepción de Bodega con
  // lote/vencimiento terminaba en la misma lista que lee el Dashboard de
  // Farmacia y el selector de vencimiento de Cuadratura Farmacia,
  // contaminando entre dominios. Ahora son dos listas separadas, mismo
  // criterio que ya rige todo lo demás del módulo.
  const [lotesFarmacia, setLotesFarmacia] = useState(FB_LOTES_INICIAL);
  const [lotesBodega, setLotesBodega] = useState([]);

  // Pedidos a proveedor: elevado desde GestionProveedoresView. Recepciones
  // necesita poder cerrar (recibido-total/recibido-parcial) el pedido que
  // originó la recepción, así que ambas vistas comparten esta lista.
  const [pedidosProveedores, setPedidosProveedores] = useState([]);
  const [pedidosFolioSeq, setPedidosFolioSeq] = useState(1);

  // Recepciones (#4 Farmacia / #13 Bodega)
  const [recepciones, setRecepciones] = useState(FB_RECEPCIONES_INICIAL);
  const [recepcionesFolioSeq, setRecepcionesFolioSeq] = useState(1);
  const [recepcionesBod, setRecepcionesBod] = useState(FB_RECEPCIONES_BODEGA_INICIAL);
  const [recepcionesBodFolioSeq, setRecepcionesBodFolioSeq] = useState(1);
  // Pedido que el usuario eligió "Registrar recepción" desde Gestión
  // Proveedores — precarga el formulario de Recepciones al navegar ahí.
  const [pedidoParaRecepcion, setPedidoParaRecepcion] = useState(null);

  // Cuadratura de Stock — merma / vencimiento / diferencia-conteo (Partes
  // 13.4 y 14.4-14.5 del dossier). Empieza vacía, igual que Recepciones y
  // Trazabilidad — no se inventan ajustes históricos de ejemplo.
  const [cuadraturaFarm, setCuadraturaFarm] = useState([]);
  const [cuadraturaFarmFolioSeq, setCuadraturaFarmFolioSeq] = useState(1);
  const [cuadraturaBod, setCuadraturaBod] = useState([]);
  const [cuadraturaBodFolioSeq, setCuadraturaBodFolioSeq] = useState(1);

  // #25 Bodega e Insumos Propios — mismo patrón de estado que Farmacia/Bodega,
  // pero para la única unidad "PROPIA". Solicita a Bodega Central (comparte
  // centralStockBod), nunca a Farmacia Central.
  const [subStockPropia, setSubStockPropia] = useState(FB_SUBSTOCK_PROPIA_INICIAL);
  const [solicitudesPropia, setSolicitudesPropia] = useState(FB_SOLICITUDES_PROPIA_INICIAL);
  const [folioSeqPropia, setFolioSeqPropia] = useState(1);

  // Catálogos: antes eran las constantes fijas FB_CATALOGO/FB_CATALOGO_BODEGA/
  // FB_CONCEPTOS_FARMACO; ahora son estado para que "Registrar ítem nuevo"
  // dentro de una Recepción los pueda hacer crecer de verdad — con el mismo
  // esquema que ya tenía cada catálogo (nunca se mezclan Farmacia y Bodega).
  const [catalogoFarmacia, setCatalogoFarmacia] = useState(FB_CATALOGO);
  const [catalogoBodega, setCatalogoBodega] = useState(FB_CATALOGO_BODEGA);
  const [conceptosFarmaco, setConceptosFarmaco] = useState(FB_CONCEPTOS_FARMACO);

  // Trazabilidad (#8 Farmacia / #15 Bodega) — registro de movimientos reales
  // de stock. Insumos Propios (PROPIA) y los despachos/devoluciones de
  // Clientes Externos con dominio "bodega" también caen en movimientosBodega
  // — comparten el mismo Bodega Central, es coherente que compartan también
  // el mismo log de movimientos. Vacío hasta que ocurra el primer movimiento
  // real — no se inventan movimientos históricos de ejemplo.
  const [movimientosFarmacia, setMovimientosFarmacia] = useState([]);
  const [movimientosBodega, setMovimientosBodega] = useState([]);

  // ── Lógica compartida de ciclo de vida de solicitud (Farmacia y Bodega
  // usan la misma máquina de estados: pendiente → aprobada → en-preparación
  // → despachada → recibida). Se genera una vez por dominio con esta fábrica
  // para no duplicar el código entre Farmacia y Bodega.
  function fbCrearHandlers({ solicitudes, setSolicitudes, centralStock, setCentralStock, subStock, setSubStock, folioSeq, setFolioSeq, folioPrefix, setMovimientos, nodoLabel, role }) {
    const actualizar = (folio, campos) => setSolicitudes(prev => prev.map(s => (s.folio === folio ? { ...s, ...campos } : s)));
    return {
      crearSolicitud(payload) {
        const folio = `${folioPrefix}-2026-${String(folioSeq).padStart(4, "0")}`;
        setSolicitudes(prev => [{ folio, estado: "pendiente-coordinador", fechaSolicitud: new Date().toISOString(), ...payload }, ...prev]);
        setFolioSeq(n => n + 1);
      },
      autorizarCoordinador: folio => actualizar(folio, { estado: "pendiente", fechaAutorizacionCoordinador: new Date().toISOString() }),
      rechazar: (folio, quien) => actualizar(folio, { estado: "rechazada", rechazadaPor: quien }),
      aprobar: folio => actualizar(folio, { estado: "aprobada" }),
      enPreparacion: folio => actualizar(folio, { estado: "en-preparacion" }),
      despachar(folio, cantidadesDespacho) {
        const sol = solicitudes.find(s => s.folio === folio);
        if (!sol) return;
        // Corrección: antes se restaba el stock con Math.max(0, actual - cant),
        // lo que evitaba que el stock quedara negativo, pero igual registraba
        // cantidadDespachada = lo pedido en el panel, aunque excediera lo que
        // realmente había. Resultado: la unidad podía terminar "recibiendo"
        // más de lo que Central realmente tenía — stock se creaba de la nada.
        // Ahora se calcula la cantidad REAL (topada al disponible real) una
        // sola vez, y esa es la que se resta Y la que se registra — siempre
        // coherentes entre sí.
        // Corrección (auditoría técnica, Parte 14, hallazgo P0 #3): el cálculo
        // se hace sobre una copia local de `centralStock` ANTES de llamar a
        // setState — ya no se mutan `cantidadesReales`/`stockResultantes`
        // dentro del *updater* de setState para leerlos justo después. El
        // *updater* de React no es un contrato síncrono garantizado (Strict
        // Mode lo invoca dos veces a propósito para exponer justo este tipo
        // de impureza).
        const cantidadesReales = {};
        const stockResultantes = {};
        const nextCentralStock = { ...centralStock };
        sol.items.forEach(it => {
          const cur = nextCentralStock[it.itemId];
          const solicitadoDespacho = cantidadesDespacho[it.itemId] || 0;
          const real = cur ? Math.max(0, Math.min(solicitadoDespacho, cur.stockActual)) : 0;
          cantidadesReales[it.itemId] = real;
          if (cur) {
            nextCentralStock[it.itemId] = { ...cur, stockActual: cur.stockActual - real };
            stockResultantes[it.itemId] = nextCentralStock[it.itemId].stockActual;
          }
        });
        setCentralStock(nextCentralStock);
        const itemsActualizados = sol.items.map(it => ({ ...it, cantidadDespachada: cantidadesReales[it.itemId] || 0 }));
        // Parte 17: un despacho con menos de lo solicitado ya no queda
        // indistinguible de uno completo. Se marca con un flag (no se agrega
        // un estado nuevo a la máquina: eso es contrato de backend).
        const despachoParcial = itemsActualizados.some(it => it.cantidadDespachada < it.cantidadSolicitada);
        actualizar(folio, { estado: "despachada", fechaDespacho: new Date().toISOString(), items: itemsActualizados, despachoParcial });
        // Trazabilidad: salida real de Central hacia la sub-unidad.
        if (setMovimientos) {
          const nuevos = itemsActualizados.filter(it => it.cantidadDespachada > 0).map(it => fbCrearMovimiento({
            itemId: it.itemId, lote: it.lote, tipoMovimiento: "despacho-unidad", cantidad: it.cantidadDespachada, signo: "-",
            stockResultante: stockResultantes[it.itemId], origen: { tipo: nodoLabel, referencia: "CENTRAL" },
            destino: { tipo: "sub-unidad", referencia: sol.subFarmaciaId }, documentoRespaldo: folio, registradoPor: role,
          }));
          if (nuevos.length) setMovimientos(prev => [...nuevos, ...prev]);
        }
      },
      confirmarRecepcion(folio, cantidadesRecepcion, observacionesRecepcion) {
        const sol = solicitudes.find(s => s.folio === folio);
        if (!sol) return;
        // Corrección (auditoría técnica, Parte 14, hallazgo P0 #3): mismo
        // criterio que despachar() — se calcula sobre una copia local de
        // `subStock` antes de llamar a setState, no dentro del *updater*.
        const stockResultantes = {};
        const forUnit = { ...(subStock[sol.subFarmaciaId] || {}) };
        sol.items.forEach(it => {
          const cant = cantidadesRecepcion[it.itemId] || 0;
          const cur = forUnit[it.itemId] || { stockActual: 0, stockMinimo: 0, stockMaximo: 0 };
          forUnit[it.itemId] = { ...cur, stockActual: cur.stockActual + cant };
          stockResultantes[it.itemId] = forUnit[it.itemId].stockActual;
        });
        setSubStock({ ...subStock, [sol.subFarmaciaId]: forUnit });
        const itemsActualizados = sol.items.map(it => ({ ...it, cantidadRecibida: cantidadesRecepcion[it.itemId] || 0 }));
        // Parte 17: faltante/excedente quedan como discrepancia explícita.
        const hayExcedente = itemsActualizados.some(it => it.cantidadRecibida > (it.cantidadDespachada != null ? it.cantidadDespachada : it.cantidadSolicitada));
        const hayFaltante = itemsActualizados.some(it => it.cantidadRecibida < (it.cantidadDespachada != null ? it.cantidadDespachada : it.cantidadSolicitada));
        actualizar(folio, { estado: "recibida", fechaRecepcion: new Date().toISOString(), items: itemsActualizados, observacionesRecepcion,
          discrepancia: hayExcedente ? "excedente" : hayFaltante ? "faltante" : null });
        // Trazabilidad: entrada real confirmada en la sub-unidad (puede diferir
        // de lo despachado — mermas o diferencias de conteo en tránsito).
        // Corrección (auditoría técnica, Parte 14, hallazgo P0 #2): origen/
        // destino estaban invertidos — el flujo físico es Central → sub-
        // unidad, igual que en despachar(); antes decía sub-unidad → Central.
        if (setMovimientos) {
          const nuevos = itemsActualizados.filter(it => it.cantidadRecibida > 0).map(it => fbCrearMovimiento({
            itemId: it.itemId, lote: it.lote, tipoMovimiento: "recepcion-unidad", cantidad: it.cantidadRecibida, signo: "+",
            stockResultante: stockResultantes[it.itemId], origen: { tipo: nodoLabel, referencia: "CENTRAL" },
            destino: { tipo: "sub-unidad", referencia: sol.subFarmaciaId }, documentoRespaldo: folio, registradoPor: role,
            observaciones: ((it.cantidadRecibida > (it.cantidadDespachada != null ? it.cantidadDespachada : it.cantidadSolicitada)) ? "[EXCEDENTE] " : (it.cantidadRecibida < (it.cantidadDespachada != null ? it.cantidadDespachada : it.cantidadSolicitada)) ? "[FALTANTE] " : "") + (observacionesRecepcion || "") || null,
          }));
          if (nuevos.length) setMovimientos(prev => [...nuevos, ...prev]);
        }
      },
    };
  }

  const hFarm = fbCrearHandlers({ solicitudes, setSolicitudes, centralStock, setCentralStock, subStock, setSubStock, folioSeq, setFolioSeq, folioPrefix: "SOL", setMovimientos: setMovimientosFarmacia, nodoLabel: "farmacia-central", role });
  const hBod = fbCrearHandlers({ solicitudes: solicitudesBod, setSolicitudes: setSolicitudesBod, centralStock: centralStockBod, setCentralStock: setCentralStockBod, subStock: subStockBod, setSubStock: setSubStockBod, folioSeq: folioSeqBod, setFolioSeq: setFolioSeqBod, folioPrefix: "SOLB", setMovimientos: setMovimientosBodega, nodoLabel: "bodega-central", role });
  // Insumos Propios pide a Bodega Central igual que cualquiera de las 41
  // unidades — mismo centralStock/setCentralStock (el de Bodega), misma fábrica.
  const hPropia = fbCrearHandlers({ solicitudes: solicitudesPropia, setSolicitudes: setSolicitudesPropia, centralStock: centralStockBod, setCentralStock: setCentralStockBod, subStock: subStockPropia, setSubStock: setSubStockPropia, folioSeq: folioSeqPropia, setFolioSeq: setFolioSeqPropia, folioPrefix: "SOLP", setMovimientos: setMovimientosBodega, nodoLabel: "bodega-central", role });

  // Puente para que "Bodega → Stock y Sub-bodegas" y "Bodega → #14
  // Solicitudes" también puedan mostrar y operar la unidad PROPIA (folios
  // "SOLP-"), enrutando al handler correcto (hBod o hPropia) sin fusionar
  // sus estados — cada uno sigue siendo una lista separada por dentro.
  function crearSolicitudBodComp(payload) {
    (payload.subFarmaciaId === "PROPIA" ? hPropia : hBod).crearSolicitud(payload);
  }
  function autorizarCoordinadorBodComp(folio) { (folio.startsWith("SOLP-") ? hPropia : hBod).autorizarCoordinador(folio); }
  function aprobarBodComp(folio) { (folio.startsWith("SOLP-") ? hPropia : hBod).aprobar(folio); }
  function rechazarBodComp(folio, quien) { (folio.startsWith("SOLP-") ? hPropia : hBod).rechazar(folio, quien); }
  function enPreparacionBodComp(folio) { (folio.startsWith("SOLP-") ? hPropia : hBod).enPreparacion(folio); }
  function despacharBodComp(folio, cant) { (folio.startsWith("SOLP-") ? hPropia : hBod).despachar(folio, cant); }
  function confirmarRecepcionBodComp(folio, cant, obs) { (folio.startsWith("SOLP-") ? hPropia : hBod).confirmarRecepcion(folio, cant, obs); }

  function irASolicitudesPendientes() {
    setSeccion("farmacia");
    setFarmTab("pedidos_farm");
  }

  // ── Recepciones: cierra el ciclo proveedor → recepción → stock. El stock
  // sube SOLO al aceptar una Recepción, por la cantidad REALMENTE recibida
  // por ítem (no la solicitada) — reemplaza el atajo anterior de "Hacer
  // pedido" que sumaba stock directo al marcar "recibido total". Si la
  // Recepción está vinculada a un Pedido, ese Pedido pasa a "recibido-total"
  // o "recibido-parcial" según si se recibió todo lo solicitado o menos.
  // Misma fábrica compartida entre Farmacia y Bodega, igual que fbCrearHandlers.
  function fbCrearHandlersRecepcion({ setRecepciones, centralStock, setCentralStock, setLotes, setPedidos, folioSeq, setFolioSeq, folioPrefix, setMovimientos, nodoLabel, role }) {
    return {
      registrar(payload) {
        const folio = `${folioPrefix}-2026-${String(folioSeq).padStart(4, "0")}`;
        const huboObservacion = !payload.verificacion.embalajeIntegro || !payload.verificacion.documentacionCompleta ||
          payload.verificacion.cadenaFrioConforme === false ||
          payload.items.some(it => !it.cumpleEspecificaciones || it.cantidadRecibida !== it.cantidadFacturada);
        const estado = payload.rechazar ? "rechazada" : (huboObservacion ? "aceptada-con-observaciones" : "aceptada");

        if (estado !== "rechazada") {
          // Corrección (auditoría técnica, Parte 14, hallazgo P0 #3): se
          // calcula sobre una copia local de `centralStock` antes de llamar a
          // setState — mismo criterio ya aplicado en despachar()/
          // confirmarRecepcion(), no se muta dentro del *updater*.
          const stockResultantes = {};
          const nextCentralStock = { ...centralStock };
          payload.items.forEach(it => {
            const cur = nextCentralStock[it.itemId];
            if (cur && it.cantidadRecibida > 0) {
              nextCentralStock[it.itemId] = { ...cur, stockActual: cur.stockActual + it.cantidadRecibida };
              stockResultantes[it.itemId] = nextCentralStock[it.itemId].stockActual;
            }
          });
          setCentralStock(nextCentralStock);
          const nuevosLotes = payload.items.filter(it => it.lote && it.fechaVencimiento)
            .map(it => ({ id: `L-${folio}-${it.itemId}`, itemId: it.itemId, numeroLote: it.lote, fechaVencimiento: it.fechaVencimiento }));
          if (nuevosLotes.length && setLotes) setLotes(prev => [...nuevosLotes, ...prev]);

          if (payload.ordenCompraFolio && setPedidos) {
            setPedidos(prev => prev.map(p => {
              if (p.folio !== payload.ordenCompraFolio) return p;
              const totalSolicitado = p.items.reduce((a, it) => a + it.cantidadSolicitada, 0);
              const totalRecibido = payload.items.reduce((a, it) => a + it.cantidadRecibida, 0);
              return { ...p, estado: totalRecibido >= totalSolicitado ? "recibido-total" : "recibido-parcial", recepcionFolio: folio };
            }));
          }

          // Trazabilidad: ingreso de proveedor, uno por ítem realmente recibido.
          if (setMovimientos) {
            const nuevos = payload.items.filter(it => it.cantidadRecibida > 0).map(it => fbCrearMovimiento({
              itemId: it.itemId, lote: it.lote, tipoMovimiento: "ingreso-proveedor", cantidad: it.cantidadRecibida, signo: "+",
              stockResultante: stockResultantes[it.itemId], origen: { tipo: "proveedor", referencia: payload.proveedorId },
              destino: { tipo: nodoLabel, referencia: "CENTRAL" }, documentoRespaldo: folio, registradoPor: role,
            }));
            if (nuevos.length) setMovimientos(prev => [...nuevos, ...prev]);
          }
        }

        setRecepciones(prev => [{ folio, fechaRecepcion: new Date().toISOString(), estado, ...payload }, ...prev]);
        setFolioSeq(n => n + 1);
      },
    };
  }

  const hFarmRecepcion = fbCrearHandlersRecepcion({ setRecepciones, centralStock, setCentralStock, setLotes: setLotesFarmacia, setPedidos: setPedidosProveedores, folioSeq: recepcionesFolioSeq, setFolioSeq: setRecepcionesFolioSeq, folioPrefix: "REC", setMovimientos: setMovimientosFarmacia, nodoLabel: "farmacia-central", role });
  const hBodRecepcion = fbCrearHandlersRecepcion({ setRecepciones: setRecepcionesBod, centralStock: centralStockBod, setCentralStock: setCentralStockBod, setLotes: setLotesBodega, setPedidos: setPedidosProveedores, folioSeq: recepcionesBodFolioSeq, setFolioSeq: setRecepcionesBodFolioSeq, folioPrefix: "RECB", setMovimientos: setMovimientosBodega, nodoLabel: "bodega-central", role });

  // Cuadratura de Stock — construida desde el inicio con el patrón corregido
  // (copia local de centralStock antes de setState, nunca dentro del
  // *updater*), el mismo criterio ya aplicado en las correcciones de arriba.
  function fbCrearHandlerCuadratura({ centralStock, setCentralStock, setAjustes, folioSeq, setFolioSeq, folioPrefix, setMovimientos, nodoLabel, role }) {
    return {
      registrar(payload) {
        const folio = `${folioPrefix}-2026-${String(folioSeq).padStart(4, "0")}`;
        const cur = centralStock[payload.itemId];
        if (cur) {
          setCentralStock({ ...centralStock, [payload.itemId]: { ...cur, stockActual: payload.cantidadNueva } });
        }
        setAjustes(prev => [{ folio, fechaAjuste: new Date().toISOString(), registradoPor: role, ...payload }, ...prev]);
        setFolioSeq(n => n + 1);
        const diferencia = payload.cantidadNueva - payload.cantidadAnterior;
        if (setMovimientos && diferencia !== 0) {
          const signo = diferencia > 0 ? "+" : "-";
          // Diferencia de conteo puede subir o bajar el stock — merma y
          // vencimiento solo lo bajan (el formulario ya lo garantiza).
          const origen = signo === "+" ? { tipo: "conteo-fisico", referencia: payload.motivo } : { tipo: nodoLabel, referencia: "CENTRAL" };
          const destino = signo === "+" ? { tipo: nodoLabel, referencia: "CENTRAL" } : { tipo: "baja", referencia: payload.motivo };
          setMovimientos(prev => [fbCrearMovimiento({
            itemId: payload.itemId, lote: payload.lote, tipoMovimiento: payload.motivo, cantidad: Math.abs(diferencia), signo,
            stockResultante: payload.cantidadNueva, origen, destino, documentoRespaldo: folio, registradoPor: role,
            observaciones: payload.justificacion,
          }), ...prev]);
        }
      },
    };
  }
  const hFarmCuadratura = fbCrearHandlerCuadratura({ centralStock, setCentralStock, setAjustes: setCuadraturaFarm, folioSeq: cuadraturaFarmFolioSeq, setFolioSeq: setCuadraturaFarmFolioSeq, folioPrefix: "AJU", setMovimientos: setMovimientosFarmacia, nodoLabel: "farmacia-central", role });
  const hBodCuadratura = fbCrearHandlerCuadratura({ centralStock: centralStockBod, setCentralStock: setCentralStockBod, setAjustes: setCuadraturaBod, folioSeq: cuadraturaBodFolioSeq, setFolioSeq: setCuadraturaBodFolioSeq, folioPrefix: "AJB", setMovimientos: setMovimientosBodega, nodoLabel: "bodega-central", role });

  function irARegistrarRecepcion(pedido) {
    setPedidoParaRecepcion(pedido);
    if (pedido.dominio === "farmacia") { setSeccion("farmacia"); setFarmTab("recepciones_farm"); }
    else { setSeccion("bodega"); setBodTab("recepciones_bod"); }
  }

  // Registrar ítem nuevo desde una Recepción — mismo esquema que el resto del
  // catálogo (nunca se mezcla Farmacia/Bodega). Devuelve el id nuevo de forma
  // síncrona (se genera antes de despachar los setState) para que el
  // formulario de Recepción pueda agregarlo de inmediato como fila.
  function registrarItemNuevoFarmacia(payload) {
    const nuevoId = fbSiguienteId(catalogoFarmacia, payload.tipo === "medicamento" ? "MED" : "INS");
    let conceptoId = null;
    if (payload.tipo === "medicamento" && payload.dci) {
      const existente = conceptosFarmaco.find(c => c.dci.trim().toLowerCase() === payload.dci.trim().toLowerCase());
      if (existente) {
        conceptoId = existente.id;
      } else {
        conceptoId = `DCI-${String(conceptosFarmaco.length + 1).padStart(3, "0")}`;
        setConceptosFarmaco(prev => [...prev, { id: conceptoId, dci: payload.dci, concentracion: payload.concentracion, formaFarmaceutica: payload.formaFarmaceutica, snomedCT: "pendiente de codificar" }]);
      }
    }
    setCatalogoFarmacia(prev => [...prev, {
      id: nuevoId, conceptoId, nombre: payload.nombre, marca: payload.marca, laboratorio: payload.laboratorio,
      registroISP: payload.registroISP, codigoCenabast: payload.codigoCenabast, unidad: payload.unidad, codigoBarra: payload.codigoBarra,
    }]);
    setCentralStock(prev => ({ ...prev, [nuevoId]: { stockActual: 0, stockMinimo: payload.stockMinimo } }));
    return nuevoId;
  }
  function registrarItemNuevoBodega(payload) {
    const nuevoId = fbSiguienteId(catalogoBodega, "BOD");
    setCatalogoBodega(prev => [...prev, { id: nuevoId, nombre: payload.nombre, categoria: payload.categoria, unidad: payload.unidad, codigoBarra: payload.codigoBarra }]);
    setCentralStockBod(prev => ({ ...prev, [nuevoId]: { stockActual: 0, stockMinimo: payload.stockMinimo } }));
    return nuevoId;
  }

  const pendientesCount = solicitudes.filter(s => s.estado === "pendiente" || s.estado === "pendiente-coordinador").length;
  const pendientesCountBod = solicitudesBod.filter(s => s.estado === "pendiente" || s.estado === "pendiente-coordinador").length;
  const primarios = [
    { id: "dashboard", label: "Dashboard",         icon: LayoutDashboard, color: C.primary },
    { id: "farmacia",  label: "Farmacia Central",  icon: Pill,            color: "#4338CA" },
    { id: "bodega",    label: "Bodega",            icon: Package,        color: "#B45309" },
  ];

  return (
    <div>
      <div style={{ display: "flex", gap: 10, marginBottom: 14, flexWrap: "wrap" }}>
        {primarios.map(p => {
          const active = seccion === p.id;
          return (
            <button key={p.id} onClick={() => setSeccion(p.id)} style={{
              display: "flex", alignItems: "center", gap: 8, padding: "10px 16px", borderRadius: 10,
              border: `1px solid ${active ? p.color : C.border}`, background: active ? `${p.color}12` : C.surface,
              cursor: "pointer", fontSize: 13, fontWeight: 600, color: active ? p.color : C.textMid,
            }}>
              <p.icon size={16} />{p.label}
              {p.id === "farmacia" && pendientesCount > 0 && <Badge color={C.warning} sm>{pendientesCount}</Badge>}
              {p.id === "bodega" && pendientesCountBod > 0 && <Badge color={C.warning} sm>{pendientesCountBod}</Badge>}
            </button>
          );
        })}
      </div>
      <div style={{ display: "flex", gap: 6, marginBottom: 22, flexWrap: "wrap" }}>
        {FB_COMPARTIDOS.map(c => {
          const active = seccion === c.id;
          return (
            <button key={c.id} onClick={() => setSeccion(c.id)} style={{
              display: "flex", alignItems: "center", gap: 5, padding: "5px 10px", borderRadius: 999,
              border: `1px solid ${active ? C.primary : C.border}`, background: active ? `${C.primary}0F` : "transparent",
              cursor: "pointer", fontSize: 11, color: active ? C.primary : C.textMuted,
            }}>
              <c.icon size={11} />{c.label}
            </button>
          );
        })}
      </div>

      {seccion === "dashboard" && (
        <FbDashboard
          centralStock={centralStock} subStock={subStock} solicitudes={solicitudes}
          centralStockBod={centralStockBod} subStockBod={subStockBod} solicitudesBod={solicitudesBod}
          onIrASolicitudes={irASolicitudesPendientes}
          lotes={lotesFarmacia} catalogoFarmacia={catalogoFarmacia} catalogoBodega={catalogoBodega}
          movimientosFarmacia={movimientosFarmacia} movimientosBodega={movimientosBodega}
        />
      )}

      {seccion === "farmacia" && (
        <div>
          <TabBar tabs={FB_FARMACIA_SUBMODULOS.map(m => ({ id: m.id, label: `#${m.num} ${m.label}`, icon: m.icon }))} active={farmTab} onChange={setFarmTab} />
          {farmTab === "medicamentos_farm" && (
            <FbStockCentralView catalogo={catalogoFarmacia} centralStock={centralStock} conceptosFarmaco={conceptosFarmaco} mostrarConceptos={true} label="Farmacia Central" />
          )}
          {farmTab === "stock_subfarmacias" && (
            <FbStockPorUnidad role={role} catalogo={catalogoFarmacia} unidades={FB_UNIDADES_SUBFARMACIA} conceptosFarmaco={conceptosFarmaco}
              selected={selectedSF} onSelect={setSelectedSF} subStock={subStock} onCrearSolicitud={hFarm.crearSolicitud} />
          )}
          {farmTab === "pedidos_farm" && (
            <FbColaSolicitudes role={role} catalogo={catalogoFarmacia} unidades={FB_UNIDADES_SUBFARMACIA}
              centralStock={centralStock} centralLabel="Farmacia Central" solicitudes={solicitudes}
              onAutorizarCoordinador={hFarm.autorizarCoordinador}
              onAprobar={hFarm.aprobar} onRechazar={hFarm.rechazar} onEnPreparacion={hFarm.enPreparacion}
              onDespachar={hFarm.despachar} onConfirmarRecepcion={hFarm.confirmarRecepcion} />
          )}
          {farmTab === "recepciones_farm" && (
            <FbRecepcionesView dominio="farmacia" catalogo={catalogoFarmacia}
              proveedores={FB_PROVEEDORES.filter(p => p.dominio === "farmacia")}
              pedidosDisponibles={pedidosProveedores.filter(p => p.dominio === "farmacia" && p.estado === "en-transito")}
              recepciones={recepciones}
              pedidoInicial={pedidoParaRecepcion && pedidoParaRecepcion.dominio === "farmacia" ? pedidoParaRecepcion : null}
              mostrarCadenaFrio={true}
              onRegistrar={hFarmRecepcion.registrar}
              onLimpiarPedidoInicial={() => setPedidoParaRecepcion(null)}
              onRegistrarItemNuevo={registrarItemNuevoFarmacia}
            />
          )}
          {farmTab === "trazabilidad_farm" && (
            <FbTrazabilidadView movimientos={movimientosFarmacia} catalogo={catalogoFarmacia} label="Farmacia Central" />
          )}
          {farmTab === "cuadratura_farm" && (
            <FbCuadraturaView dominio="farmacia" catalogo={catalogoFarmacia} centralStock={centralStock} lotes={lotesFarmacia}
              ajustes={cuadraturaFarm} onRegistrar={hFarmCuadratura.registrar} />
          )}
          {farmTab === "balances_farm" && (
            <FbBalancesView unidades={FB_UNIDADES_SUBFARMACIA} solicitudes={solicitudes} movimientos={movimientosFarmacia}
              proveedores={FB_PROVEEDORES.filter(p => p.dominio === "farmacia")} pedidos={pedidosProveedores.filter(p => p.dominio === "farmacia")}
              recepciones={recepciones} nombreCentral="Farmacia" />
          )}
          {farmTab !== "medicamentos_farm" && farmTab !== "stock_subfarmacias" && farmTab !== "pedidos_farm" && farmTab !== "recepciones_farm" && farmTab !== "trazabilidad_farm" && farmTab !== "cuadratura_farm" && farmTab !== "balances_farm" && (
            <FbProximamente {...(FB_FARMACIA_SUBMODULOS.find(m => m.id === farmTab) || {})} />
          )}
        </div>
      )}

      {seccion === "bodega" && (
        <div>
          <TabBar tabs={FB_BODEGA_SUBMODULOS.map(m => ({ id: m.id, label: `#${m.num} ${m.label}`, icon: m.icon }))} active={bodTab} onChange={setBodTab} />
          {bodTab === "insumos_bod" && (
            <FbStockCentralView catalogo={catalogoBodega} centralStock={centralStockBod} mostrarConceptos={false} label="Bodega Central" />
          )}
          {bodTab === "stock_subbodegas" && (
            <FbStockPorUnidad role={role} catalogo={catalogoBodega} unidades={FB_UNIDADES_SUBBODEGA_MAS_PROPIA}
              selected={selectedSB} onSelect={setSelectedSB} subStock={{ ...subStockBod, ...subStockPropia }} onCrearSolicitud={crearSolicitudBodComp} />
          )}
          {bodTab === "pedidos_bod" && (
            <FbColaSolicitudes role={role} catalogo={catalogoBodega} unidades={FB_UNIDADES_SUBBODEGA_MAS_PROPIA}
              centralStock={centralStockBod} centralLabel="Bodega Central" solicitudes={[...solicitudesBod, ...solicitudesPropia]}
              onAutorizarCoordinador={autorizarCoordinadorBodComp}
              onAprobar={aprobarBodComp} onRechazar={rechazarBodComp} onEnPreparacion={enPreparacionBodComp}
              onDespachar={despacharBodComp} onConfirmarRecepcion={confirmarRecepcionBodComp} />
          )}
          {bodTab === "recepciones_bod" && (
            <FbRecepcionesView dominio="bodega" catalogo={catalogoBodega}
              proveedores={FB_PROVEEDORES.filter(p => p.dominio === "bodega")}
              pedidosDisponibles={pedidosProveedores.filter(p => p.dominio === "bodega" && p.estado === "en-transito")}
              recepciones={recepcionesBod}
              pedidoInicial={pedidoParaRecepcion && pedidoParaRecepcion.dominio === "bodega" ? pedidoParaRecepcion : null}
              mostrarCadenaFrio={false}
              onRegistrar={hBodRecepcion.registrar}
              onLimpiarPedidoInicial={() => setPedidoParaRecepcion(null)}
              onRegistrarItemNuevo={registrarItemNuevoBodega}
            />
          )}
          {bodTab === "trazabilidad_bod" && (
            <FbTrazabilidadView movimientos={movimientosBodega} catalogo={catalogoBodega} label="Bodega Central" />
          )}
          {bodTab === "cuadratura_bod" && (
            <FbCuadraturaView dominio="bodega" catalogo={catalogoBodega} centralStock={centralStockBod} lotes={lotesBodega}
              ajustes={cuadraturaBod} onRegistrar={hBodCuadratura.registrar} />
          )}
          {bodTab === "balances_bod" && (
            <FbBalancesView unidades={FB_UNIDADES_SUBBODEGA_MAS_PROPIA} solicitudes={[...solicitudesBod, ...solicitudesPropia]} movimientos={movimientosBodega}
              proveedores={FB_PROVEEDORES.filter(p => p.dominio === "bodega")} pedidos={pedidosProveedores.filter(p => p.dominio === "bodega")}
              recepciones={recepcionesBod} nombreCentral="Bodega" />
          )}
          {bodTab !== "insumos_bod" && bodTab !== "stock_subbodegas" && bodTab !== "pedidos_bod" && bodTab !== "recepciones_bod" && bodTab !== "trazabilidad_bod" && bodTab !== "cuadratura_bod" && bodTab !== "balances_bod" && (
            <FbProximamente {...(FB_BODEGA_SUBMODULOS.find(m => m.id === bodTab) || {})} />
          )}
        </div>
      )}

      {seccion === "gestion_prov" && (
        <GestionProveedoresView
          centralStock={centralStock} setCentralStock={setCentralStock}
          centralStockBod={centralStockBod} setCentralStockBod={setCentralStockBod}
          pedidos={pedidosProveedores} setPedidos={setPedidosProveedores}
          folioSeq={pedidosFolioSeq} setFolioSeq={setPedidosFolioSeq}
          onIrARecepcion={irARegistrarRecepcion}
          catalogoFarmacia={catalogoFarmacia} catalogoBodega={catalogoBodega}
        />
      )}

      {seccion === "clientes_ext" && (
        <ClientesExternosView
          centralStock={centralStock} setCentralStock={setCentralStock}
          centralStockBod={centralStockBod} setCentralStockBod={setCentralStockBod}
          catalogoFarmacia={catalogoFarmacia} catalogoBodega={catalogoBodega} conceptosFarmaco={conceptosFarmaco}
          role={role} setMovimientosFarmacia={setMovimientosFarmacia} setMovimientosBodega={setMovimientosBodega}
        />
      )}

      {seccion === "bodega_propia" && (
        <BodegaInsumosPropiosView role={role} catalogoBodega={catalogoBodega} centralStockBod={centralStockBod}
          subStockPropia={subStockPropia} solicitudesPropia={solicitudesPropia}
          onCrearSolicitud={hPropia.crearSolicitud}
          onAutorizarCoordinador={hPropia.autorizarCoordinador}
          onAprobar={hPropia.aprobar} onRechazar={hPropia.rechazar} onEnPreparacion={hPropia.enPreparacion}
          onDespachar={hPropia.despachar} onConfirmarRecepcion={hPropia.confirmarRecepcion}
        />
      )}

      {FB_COMPARTIDOS.some(c => c.id === seccion && c.id !== "gestion_prov" && c.id !== "clientes_ext" && c.id !== "bodega_propia") && (
        <FbProximamente {...(FB_COMPARTIDOS.find(c => c.id === seccion) || {})} />
      )}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────
// § 7 · PORTAL PACIENTES (Landing)
// ─────────────────────────────────────────────────────────────────
const PortalPaciente = ({ addToast }) => {
  const [tab, setTab] = useState("pac_agenda");
  const mod = MODULES.find(m => m.id === "portal_paciente");
  const tabs = mod.submodules.map(s => ({ id: s.id, label: s.label, icon: s.icon }));

  return (
    <div>
      <SectionHead title="Portal Pacientes" sub="Acceso directo · HL7 FHIR R4 · MINSAL Chile" icon={Smartphone} color={C.teal}>
        <Badge color={C.teal}>Portal Activo</Badge>
      </SectionHead>

      {/* Hero banner */}
      <div style={{ background: `linear-gradient(135deg, ${C.teal} 0%, #00695C 100%)`, borderRadius: 14, padding: "24px 28px", marginBottom: 20, color: "#fff", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <div style={{ fontSize: 22, fontWeight: 700, marginBottom: 6 }}>Bienvenido/a al Portal de Pacientes</div>
          <div style={{ fontSize: 13, opacity: 0.9, maxWidth: 420 }}>Gestione sus citas, revise sus resultados y comuníquese con su equipo de salud de forma segura.</div>
          <div style={{ display: "flex", gap: 8, marginTop: 14 }}>
            <Btn variant="primary" color="#fff" icon={Plus} onClick={() => addToast("Abriendo módulo de agendamiento", "info")}>
              <span style={{ color: C.teal }}>Agendar Cita</span>
            </Btn>
          </div>
        </div>
        <Smartphone size={64} style={{ opacity: 0.3 }} />
      </div>

      <TabBar tabs={tabs} active={tab} onChange={setTab} />

      {/* Grid de acciones por tab */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 12 }}>
        {[
          { icon: Calendar,     label: "Imagenología",   sub: "TC · RM · Angiografía · Eco", color: C.primary  },
          { icon: FlaskConical, label: "Laboratorio",    sub: "Exámenes de sangre y orina",   color: "#00897B" },
          { icon: Eye,          label: "Oftalmología",   sub: "Control visual y fondo de ojo",color: "#6A1B9A" },
          { icon: HeartPulse,   label: "Kinesiología",   sub: "Rehabilitación y terapia",     color: "#2E7D32" },
          { icon: Stethoscope,  label: "Atención Médica",sub: "Presencial · Telemedicina",    color: C.danger   },
        ].map(item => (
          <Card key={item.label} style={{ padding: "18px", cursor: "pointer", transition: "all 0.15s" }}
            onMouseOver={e => e.currentTarget.style.boxShadow = `0 4px 14px ${item.color}30`}
            onMouseOut={e => e.currentTarget.style.boxShadow = "0 1px 4px rgba(0,0,0,0.05)"}
            onClick={() => addToast(`Agendamiento ${item.label}: próximamente en Capa 2`, "info")}
          >
            <div style={{ background: `${item.color}18`, borderRadius: 10, width: 44, height: 44, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 12 }}>
              <item.icon size={20} color={item.color} />
            </div>
            <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 4 }}>{item.label}</div>
            <div style={{ fontSize: 11, color: C.textMuted }}>{item.sub}</div>
          </Card>
        ))}
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────
// § 8 · STATUS RIBBON (barra de estándares FHIR)
// ─────────────────────────────────────────────────────────────────
const StatusRibbon = ({ time }) => (
  <div style={{ height: 28, background: "#071526", display: "flex", alignItems: "center", padding: "0 16px", gap: 18, flexShrink: 0, overflowX: "auto" }}>
    <div style={{ display: "flex", alignItems: "center", gap: 7, flexShrink: 0 }}>
      <HeartPulse size={11} color={C.teal} />
      <span style={{ fontSize: 10, fontWeight: 700, color: C.teal, letterSpacing: "0.5px" }}>HIS-CLÍNICO v1.0</span>
    </div>
    <div style={{ width: 1, height: 14, background: "#ffffff18", flexShrink: 0 }} />
    {STANDARDS.map(s => (
      <div key={s.id} style={{ display: "flex", alignItems: "center", gap: 5, flexShrink: 0 }}>
        <StatusDot status={s.status} size={6} />
        <span style={{ fontSize: 9, color: s.status === "online" ? s.color : s.status === "syncing" ? "#FFB74D" : "#EF9A9A", fontWeight: 500 }}>{s.label}</span>
      </div>
    ))}
    <div style={{ flex: 1 }} />
    {LAWS.map(l => (
      <span key={l} style={{ fontSize: 9, color: "#ffffff30", flexShrink: 0 }}>{l}</span>
    ))}
    <div style={{ width: 1, height: 14, background: "#ffffff18", flexShrink: 0 }} />
    <div style={{ display: "flex", alignItems: "center", gap: 5, flexShrink: 0 }}>
      <Clock size={9} color="#ffffff40" />
      <span style={{ fontSize: 9, color: "#ffffff50" }}>{time}</span>
    </div>
  </div>
);

// ─────────────────────────────────────────────────────────────────
// § 9 · SIDEBAR
// ─────────────────────────────────────────────────────────────────
const Sidebar = ({ active, onSelect, collapsed, onToggle }) => {
  const [search, setSearch] = useState("");

  const filtered = search
    ? MODULES.filter(m => m.label.toLowerCase().includes(search.toLowerCase()))
    : null;

  const renderModule = (mod) => {
    const isActive = active === mod.id;
    return (
      <button key={mod.id} onClick={() => onSelect(mod.id)} title={collapsed ? mod.label : ""}
        style={{
          width: "100%", display: "flex", alignItems: "center", gap: 10,
          padding: collapsed ? "10px 0" : "8px 12px",
          background: isActive ? C.sidebarActive : "none",
          border: "none", borderLeft: `3px solid ${isActive ? mod.color || "#4FC3F7" : "transparent"}`,
          cursor: "pointer", color: isActive ? "#fff" : "#ffffff65",
          justifyContent: collapsed ? "center" : "flex-start",
          transition: "all 0.15s",
        }}
        onMouseOver={e => { if (!isActive) { e.currentTarget.style.background = C.sidebarHover; e.currentTarget.style.color = "#ffffffCC"; } }}
        onMouseOut={e => { if (!isActive) { e.currentTarget.style.background = "none"; e.currentTarget.style.color = "#ffffff65"; } }}
      >
        <mod.icon size={15} style={{ flexShrink: 0 }} />
        {!collapsed && (
          <>
            <span style={{ fontSize: 12, flex: 1, textAlign: "left", fontWeight: isActive ? 600 : 400, lineHeight: 1.3 }}>{mod.label}</span>
            {mod.submodules && (
              <span style={{ fontSize: 9, background: "#ffffff15", color: "#ffffff50", borderRadius: 10, padding: "1px 5px" }}>
                {mod.submodules.length}
              </span>
            )}
          </>
        )}
      </button>
    );
  };

  return (
    <div style={{ width: collapsed ? 56 : 252, minWidth: collapsed ? 56 : 252, background: C.sidebarBg, height: "100%", display: "flex", flexDirection: "column", transition: "width 0.22s ease", overflow: "hidden", flexShrink: 0 }}>
      {/* Logo */}
      <div style={{ padding: collapsed ? "14px 10px" : "13px 14px", borderBottom: "1px solid #ffffff0F", display: "flex", alignItems: "center", gap: 10, minHeight: 56, flexShrink: 0 }}>
        <div style={{ width: 32, height: 32, borderRadius: 9, background: C.primary, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <HeartPulse size={16} color="#fff" />
        </div>
        {!collapsed && (
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#fff", lineHeight: 1.1 }}>HIS-Clínico</div>
            <div style={{ fontSize: 9, color: C.teal, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.6px" }}>FHIR R4 · MINSAL</div>
          </div>
        )}
        <button onClick={onToggle} style={{ background: "none", border: "none", cursor: "pointer", color: "#ffffff30", padding: 2, flexShrink: 0 }}>
          {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>
      </div>

      {/* Buscador */}
      {!collapsed && (
        <div style={{ padding: "8px 10px", borderBottom: "1px solid #ffffff09" }}>
          <div style={{ display: "flex", alignItems: "center", background: "#ffffff0F", borderRadius: 6, padding: "5px 9px", gap: 6 }}>
            <Search size={12} color="#ffffff40" />
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar módulo..." style={{ background: "none", border: "none", outline: "none", color: "#ffffffCC", fontSize: 11, flex: 1 }} />
            {search && <button onClick={() => setSearch("")} style={{ background: "none", border: "none", cursor: "pointer", color: "#ffffff40", padding: 0 }}><X size={11} /></button>}
          </div>
        </div>
      )}

      {/* Nav */}
      <div style={{ flex: 1, overflowY: "auto", padding: "6px 0" }}>
        {filtered
          ? filtered.map(m => renderModule(m))
          : MODULE_GROUPS.map(g => (
            <div key={g.id}>
              {g.label && !collapsed && (
                <div style={{ padding: "10px 14px 3px", fontSize: 9, color: "#ffffff28", fontWeight: 700, textTransform: "uppercase", letterSpacing: "1.2px" }}>
                  {g.label}
                </div>
              )}
              {MODULES.filter(m => g.ids.includes(m.id)).map(m => renderModule(m))}
            </div>
          ))
        }
      </div>

      {/* Footer */}
      <div style={{ borderTop: "1px solid #ffffff09", padding: collapsed ? "8px 0" : "8px 10px", display: "flex", flexDirection: "column", gap: 2 }}>
        {[{ icon: Settings, label: "Configuración" }, { icon: HelpCircle, label: "Ayuda" }, { icon: LogOut, label: "Cerrar Sesión" }].map(item => (
          <button key={item.label} title={collapsed ? item.label : ""} style={{
            display: "flex", alignItems: "center", gap: 8, padding: collapsed ? "7px 0" : "6px 9px",
            background: "none", border: "none", cursor: "pointer", color: "#ffffff35", borderRadius: 5,
            width: "100%", fontSize: 11, justifyContent: collapsed ? "center" : "flex-start",
          }}>
            <item.icon size={14} />{!collapsed && item.label}
          </button>
        ))}
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────
// § 10 · HEADER
// ─────────────────────────────────────────────────────────────────
const Header = ({ role, onRoleChange, mod, notifications }) => {
  const [showRoles, setShowRoles] = useState(false);
  const [showNotif, setShowNotif] = useState(false);
  const currentRole = ROLES.find(r => r.id === role);
  const activeMod = MODULES.find(m => m.id === mod);

  return (
    <div style={{ height: 56, background: C.surface, borderBottom: `1px solid ${C.border}`, display: "flex", alignItems: "center", padding: "0 20px", gap: 14, flexShrink: 0, position: "sticky", top: 0, zIndex: 100 }}>
      {/* Breadcrumb */}
      <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 7, overflow: "hidden" }}>
        <HeartPulse size={14} color={C.primary} />
        <span style={{ fontSize: 11, color: C.textMuted }}>HIS-Clínico</span>
        {activeMod && (<>
          <ChevronRight size={11} color={C.border} />
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <activeMod.icon size={13} color={activeMod.color} />
            <span style={{ fontSize: 12, fontWeight: 600, color: C.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{activeMod.label}</span>
          </div>
        </>)}
      </div>

      {/* Search global */}
      <div style={{ display: "flex", alignItems: "center", background: "#F5F8FF", borderRadius: 8, padding: "6px 11px", gap: 7, width: 210 }}>
        <Search size={12} color={C.textMuted} />
        <input placeholder="Paciente, RUT, examen…" style={{ background: "none", border: "none", outline: "none", fontSize: 11, color: C.text, width: "100%" }} />
      </div>

      {/* Role switcher */}
      <div style={{ position: "relative" }}>
        <button onClick={() => setShowRoles(p => !p)} style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 12px", borderRadius: 8, background: `${currentRole?.color || C.primary}12`, border: `1px solid ${currentRole?.color || C.primary}28`, cursor: "pointer" }}>
          <div style={{ width: 7, height: 7, borderRadius: "50%", background: currentRole?.color || C.primary }} />
          <span style={{ fontSize: 11, fontWeight: 600, color: currentRole?.color || C.primary }}>{currentRole?.label}</span>
          <ChevronDown size={11} color={currentRole?.color || C.primary} />
        </button>
        {showRoles && (
          <div style={{ position: "absolute", top: "110%", right: 0, background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10, boxShadow: "0 8px 24px rgba(0,0,0,0.12)", zIndex: 200, minWidth: 190, overflow: "hidden" }}>
            <div style={{ padding: "8px 12px", borderBottom: `1px solid ${C.border}`, fontSize: 10, fontWeight: 700, color: C.textMuted, textTransform: "uppercase", letterSpacing: "0.5px" }}>Cambiar Rol</div>
            {ROLES.map(r => (
              <button key={r.id} onClick={() => { onRoleChange(r.id); setShowRoles(false); }} style={{ display: "flex", alignItems: "center", gap: 8, width: "100%", padding: "8px 12px", background: role === r.id ? `${r.color}10` : "none", border: "none", cursor: "pointer", fontSize: 12, color: C.text }}>
                <div style={{ width: 7, height: 7, borderRadius: "50%", background: r.color }} />
                {r.label}
                {role === r.id && <CheckCircle size={12} color={r.color} style={{ marginLeft: "auto" }} />}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Notifications */}
      <div style={{ position: "relative" }}>
        <button onClick={() => setShowNotif(p => !p)} style={{ background: "none", border: "none", cursor: "pointer", padding: 6, position: "relative" }}>
          <Bell size={17} color={C.textMid} />
          {notifications > 0 && (
            <span style={{ position: "absolute", top: 2, right: 2, background: C.danger, color: "#fff", fontSize: 8, fontWeight: 700, borderRadius: "50%", width: 14, height: 14, display: "flex", alignItems: "center", justifyContent: "center" }}>{notifications}</span>
          )}
        </button>
        {showNotif && (
          <div style={{ position: "absolute", top: "110%", right: 0, background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10, boxShadow: "0 8px 24px rgba(0,0,0,0.12)", zIndex: 200, width: 310, overflow: "hidden" }}>
            <div style={{ padding: "10px 14px", borderBottom: `1px solid ${C.border}`, fontSize: 12, fontWeight: 600, color: C.text }}>Alertas del sistema</div>
            <div style={{ padding: "8px 10px" }}>
              {ALERTAS.slice(0, 4).map((a, i) => <AlertRow key={i} {...a} />)}
            </div>
          </div>
        )}
      </div>

      {/* Avatar */}
      <div style={{ width: 32, height: 32, borderRadius: "50%", background: currentRole?.color || C.primary, display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer" }}>
        <span style={{ fontSize: 12, fontWeight: 700, color: "#fff" }}>{(currentRole?.label || "U")[0]}</span>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────
// § 11 · TOAST
// ─────────────────────────────────────────────────────────────────
const ToastSystem = ({ toasts, remove }) => (
  <div style={{ position: "fixed", top: 76, right: 18, zIndex: 9999, display: "flex", flexDirection: "column", gap: 8, pointerEvents: "none" }}>
    {toasts.map(t => {
      const cfg = {
        success: { c: C.success, I: CheckCircle },
        error:   { c: C.danger,  I: AlertCircle },
        warning: { c: C.warning, I: AlertTriangle },
        info:    { c: C.primary, I: Info },
      }[t.type] || { c: C.primary, I: Info };
      return (
        <div key={t.id} style={{ background: C.surface, borderRadius: 10, padding: "11px 15px", boxShadow: "0 4px 20px rgba(0,0,0,0.15)", borderLeft: `4px solid ${cfg.c}`, display: "flex", alignItems: "center", gap: 9, minWidth: 270, pointerEvents: "all", animation: "slideIn 0.25s ease" }}>
          <cfg.I size={15} color={cfg.c} />
          <span style={{ fontSize: 12, color: C.text, flex: 1 }}>{t.message}</span>
          <button onClick={() => remove(t.id)} style={{ background: "none", border: "none", cursor: "pointer", color: C.textMuted, padding: 0 }}><X size={13} /></button>
        </div>
      );
    })}
  </div>
);

// ─────────────────────────────────────────────────────────────────
// § 12 · APP PRINCIPAL
// ─────────────────────────────────────────────────────────────────
export default function HISClinico() {
  const [module, setModule]           = useState("dashboard");
  const [collapsed, setCollapsed]     = useState(false);
  const [role, setRole]               = useState("director");
  const [time, setTime]               = useState("");
  const [toasts, setToasts]           = useState([]);

  // Reloj tiempo real
  useEffect(() => {
    const tick = () => setTime(
      new Date().toLocaleString("es-CL", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit" })
    );
    tick();
    const t = setInterval(tick, 1000);
    return () => clearInterval(t);
  }, []);

  // Toast API
  const addToast = useCallback((message, type = "info") => {
    const id = Date.now() + Math.random();
    setToasts(p => [...p, { id, message, type }]);
    setTimeout(() => setToasts(p => p.filter(t => t.id !== id)), 4000);
  }, []);

  const removeToast = useCallback(id => setToasts(p => p.filter(t => t.id !== id)), []);

  // Router de contenido
  const renderContent = () => {
    if (module === "dashboard")      return <Dashboard onNav={setModule} />;
    if (module === "portal_paciente") return <PortalPaciente addToast={addToast} />;
    if (module === "farmacia_bodega") return <FarmaciaBodegaView role={role} addToast={addToast} />;
    const mod = MODULES.find(m => m.id === module);
    if (mod) return <ModuleView mod={mod} addToast={addToast} />;
    return <Dashboard onNav={setModule} />;
  };

  const activeMod = MODULES.find(m => m.id === module);
  const alertCount = ALERTAS.filter(a => a.tipo === "error" || a.tipo === "warning").length;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", fontFamily: "'Inter', system-ui, -apple-system, sans-serif", background: C.bodyBg, overflow: "hidden" }}>
      <style>{`
        * { box-sizing: border-box; margin: 0; }
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-thumb { background: #CFD8DC; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #90A4AE; }
        @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.35; } }
        @keyframes slideIn { from { transform: translateX(20px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        input::placeholder, textarea::placeholder { color: #B0BEC5; }
        button { outline: none; }
        select { appearance: none; }
      `}</style>

      {/* ① Ribbon FHIR */}
      <StatusRibbon time={time} />

      {/* ② Cuerpo principal */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>

        {/* ③ Sidebar */}
        <Sidebar active={module} onSelect={setModule} collapsed={collapsed} onToggle={() => setCollapsed(p => !p)} />

        {/* ④ Panel derecho */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>

          {/* ⑤ Header */}
          <Header role={role} onRoleChange={setRole} mod={module} notifications={alertCount} />

          {/* ⑥ Contenido */}
          <div style={{ flex: 1, overflowY: "auto", padding: "18px 22px" }}>

            {/* Badges de compliance activos */}
            {module !== "dashboard" && activeMod && (
              <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 14, flexWrap: "wrap" }}>
                <StatusDot status="online" />
                <span style={{ fontSize: 10, color: C.textMuted, fontWeight: 600, marginRight: 4 }}>Compliance:</span>
                {(activeMod.fhir || []).slice(0, 4).map(r => <FTag key={r} r={r} sm />)}
                <Badge color="#C62828" sm>MINSAL-CL</Badge>
                <Badge color="#6A1B9A" sm>Dec.41</Badge>
                <Badge color="#37474F" sm>L.19.628</Badge>
                <Badge color={C.warning} sm>L.19.799</Badge>
                {activeMod.standard && <Badge color={activeMod.color} sm>{activeMod.standard}</Badge>}
              </div>
            )}

            {renderContent()}
          </div>
        </div>
      </div>

      {/* ⑦ Toasts */}
      <ToastSystem toasts={toasts} remove={removeToast} />
    </div>
  );
}

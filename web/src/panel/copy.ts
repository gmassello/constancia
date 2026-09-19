import type { Lang } from "../prefs"

export type Copy = {
  brand: string
  dataSeed: string
  dataPostgres: string
  phoneReady: string
  phoneNoKeys: string
  noPatients: string

  followedSince: (day: string) => string
  memory: string
  modeScripted: string
  modeReplay: string
  modeLive: string
  modeLiveDisabled: string
  callNow: string

  liveTitle: string
  liveNow: string
  liveEnded: string
  liveDialling: string
  agent: string
  patient: string

  activity: string
  waitingForCall: string

  weeklyTitle: string
  weekLabel: (year: string, week: string) => string
  noNumbers: string

  fileTitle: string
  noHistory: string
  quoteMeta: (quote: string, turn: number, day: string) => string
  retiredOn: (day: string) => string

  keytermsTitle: string
  firstCall: string
  callsTitle: string
  noCalls: string
  callMeta: (day: string, memory: boolean) => string

  themeToLight: string
  themeToDark: string

  railRecall: string
  railRecallText: (facts: number) => string
  railStored: string
  railQuote: (quote: string, turn: number) => string
  railSuperseded: string
  railSupersededText: string
  railRejected: string
  railAlarm: string
  railMemoryOff: string
  railMemoryOffText: (phase: string) => string
  railSummary: string
  railAnalysis: string
  railAnalysisText: (entities: number) => string
  railExtracted: string
  railExtractedText: (count: number) => string
  railCall: string
  railCallStarted: (memory: boolean) => string
  railCallEnded: string

  category: Record<string, string>
  program: Record<string, string>
  rule: Record<string, string>
  phase: Record<string, string>
  reason: Record<string, string>
}

const en: Copy = {
  brand: "constancia",
  dataSeed: "data: local seed",
  dataPostgres: "data: postgres",
  phoneReady: "phone: ready",
  phoneNoKeys: "phone: no keys",
  noPatients: "No patients loaded.",

  followedSince: (day) => `in follow-up since ${day}`,
  memory: "memory",
  modeScripted: "scripted",
  modeReplay: "recorded",
  modeLive: "live",
  modeLiveDisabled: "live (no keys)",
  callNow: "Call now",

  liveTitle: "Call in progress",
  liveNow: "live",
  liveEnded: "ended",
  liveDialling: "Dialling…",
  agent: "agent",
  patient: "patient",

  activity: "Activity",
  waitingForCall: "Waiting for the call…",

  weeklyTitle: "Weekly evolution",
  weekLabel: (year, week) => `${year} w${week}`,
  noNumbers: "No numeric value to chart yet.",

  fileTitle: "Patient file",
  noHistory: "No history: this is the first call.",
  quoteMeta: (quote, turn, day) => `«${quote}» · turn ${turn} · ${day}`,
  retiredOn: (day) => ` · retired ${day}`,

  keytermsTitle: "Key terms that fed the STT",
  firstCall: "First call: nothing on file.",
  callsTitle: "Calls",
  noCalls: "No calls yet.",
  callMeta: (day, memory) => `${day} · memory ${memory ? "on" : "off"}`,

  themeToLight: "Switch to the light theme",
  themeToDark: "Switch to the dark theme",

  railRecall: "recall",
  railRecallText: (facts) => `${facts} facts on file`,
  railStored: "new fact",
  railQuote: (quote, turn) => `«${quote}» · turn ${turn}`,
  railSuperseded: "fact retired",
  railSupersededText: "the previous value stays, struck through",
  railRejected: "discarded",
  railAlarm: "red flag",
  railMemoryOff: "memory off",
  railMemoryOffText: (phase) => `${phase} skipped`,
  railSummary: "summary",
  railAnalysis: "analysis",
  railAnalysisText: (entities) => `${entities} entities`,
  railExtracted: "extraction",
  railExtractedText: (count) => `${count} facts from the transcript`,
  railCall: "call",
  railCallStarted: (memory) => `started · memory ${memory ? "on" : "off"}`,
  railCallEnded: "ended",

  category: {
    symptom: "symptom",
    adherence: "adherence",
    mood: "mood",
    clinical_value: "clinical value",
    red_flag: "red flag",
  },
  program: { rehab: "rehab", postpartum: "postpartum", chronic: "chronic" },
  rule: {
    sudden_sharp_pain: "sudden sharp pain",
    fall: "a fall",
    swelling_with_fever: "swelling with fever",
    numbness: "numbness or tingling",
    heavy_bleeding: "heavy bleeding",
    chest_pain: "chest pain or breathlessness",
  },
  phase: {
    recall: "recall",
    greet: "greeting",
    converse: "questions",
    extract: "extraction",
    store: "storage",
    summarize: "summary",
  },
  reason: {
    "not grounded": "no verbatim quote backs it",
    "memory disabled for this call": "memory disabled for this call",
    "no memory store configured": "no memory store configured",
  },
}

const es: Copy = {
  brand: "constancia",
  dataSeed: "datos: seed local",
  dataPostgres: "datos: postgres",
  phoneReady: "teléfono: listo",
  phoneNoKeys: "teléfono: sin claves",
  noPatients: "No hay pacientes cargados.",

  followedSince: (day) => `en seguimiento desde ${day}`,
  memory: "memoria",
  modeScripted: "simulada",
  modeReplay: "grabada",
  modeLive: "real",
  modeLiveDisabled: "real (sin claves)",
  callNow: "Llamar ahora",

  liveTitle: "Llamada en curso",
  liveNow: "en vivo",
  liveEnded: "terminada",
  liveDialling: "Marcando…",
  agent: "agente",
  patient: "paciente",

  activity: "Actividad",
  waitingForCall: "Esperando la llamada…",

  weeklyTitle: "Evolución semanal",
  weekLabel: (year, week) => `${year} s${week}`,
  noNumbers: "Todavía no hay ningún valor numérico para graficar.",

  fileTitle: "Ficha del paciente",
  noHistory: "Sin antecedentes: es la primera vez que hablan.",
  quoteMeta: (quote, turn, day) => `«${quote}» · turno ${turn} · ${day}`,
  retiredOn: (day) => ` · retirado ${day}`,

  keytermsTitle: "Key terms que alimentaron el STT",
  firstCall: "Primera llamada: no había nada en ficha.",
  callsTitle: "Llamadas",
  noCalls: "Todavía no hubo ninguna llamada.",
  callMeta: (day, memory) => `${day} · memoria ${memory ? "on" : "off"}`,

  themeToLight: "Cambiar al tema claro",
  themeToDark: "Cambiar al tema oscuro",

  railRecall: "memoria",
  railRecallText: (facts) => `${facts} datos en ficha`,
  railStored: "dato nuevo",
  railQuote: (quote, turn) => `«${quote}» · turno ${turn}`,
  railSuperseded: "dato retirado",
  railSupersededText: "el valor anterior queda tachado en la ficha",
  railRejected: "descartado",
  railAlarm: "señal de alarma",
  railMemoryOff: "memoria off",
  railMemoryOffText: (phase) => `${phase} salteada`,
  railSummary: "resumen",
  railAnalysis: "análisis",
  railAnalysisText: (entities) => `${entities} entidades`,
  railExtracted: "extracción",
  railExtractedText: (count) => `${count} datos del transcript`,
  railCall: "llamada",
  railCallStarted: (memory) => `empezó · memoria ${memory ? "on" : "off"}`,
  railCallEnded: "terminó",

  category: {
    symptom: "síntoma",
    adherence: "adherencia",
    mood: "ánimo",
    clinical_value: "valor clínico",
    red_flag: "señal de alarma",
  },
  program: { rehab: "rehabilitación", postpartum: "puerperio", chronic: "crónicos" },
  rule: {
    sudden_sharp_pain: "dolor repentino y fuerte",
    fall: "una caída",
    swelling_with_fever: "hinchazón con fiebre",
    numbness: "hormigueo o pérdida de sensibilidad",
    heavy_bleeding: "sangrado abundante",
    chest_pain: "dolor en el pecho o falta de aire",
  },
  phase: {
    recall: "memoria",
    greet: "saludo",
    converse: "preguntas",
    extract: "extracción",
    store: "guardado",
    summarize: "resumen",
  },
  reason: {
    "not grounded": "ninguna cita textual lo respalda",
    "memory disabled for this call": "memoria desactivada en esta llamada",
    "no memory store configured": "no hay almacén de memoria configurado",
  },
}

const base: Record<Lang, Copy> = { en, es }

export function copy(lang: Lang): Copy {
  return base[lang]
}

export function label(map: Record<string, string>, key: unknown): string {
  const raw = String(key ?? "")
  return map[raw] ?? raw.replace(/_/g, " ")
}

import type { Lang } from "../prefs"
import { speech } from "./content"

type Strings = {
  brand: string
  home: string
  dataSeed: string
  dataPostgres: string
  phoneReady: string
  phoneNoKeys: string
  noPatients: string
  backendDown: string
  loadFailed: (status: number, detail: string | null) => string

  followedSince: (day: string) => string
  callWithoutMemory: string
  callWithMemory: string
  callHint: string
  callSameWithoutMemory: string
  callReplay: string
  callAlarm: string
  callLiveWithoutMemory: string
  callLiveWithMemory: string
  callLiveHint: string

  liveTitle: string
  liveNow: string
  liveEnded: string
  liveDialling: string
  liveLost: string
  liveLostDetail: string
  liveUnanswered: string
  liveFailed: string
  turnUnheard: string
  railErrorDetail: string
  agent: string
  patient: string

  activity: string
  waitingForCall: string

  weeklyTitle: string
  noNumbers: string
  measure: Record<string, string>
  unit: Record<string, string>
  better: string
  worse: string
  same: string
  changeBy: (amount: number, verdict: string) => string
  onlyOneCall: string
  scaleNote: (max: number) => string

  fileTitle: string
  fileLede: string
  fileNote: string
  noHistory: string
  factCurrent: string
  factRetired: string
  saidOn: (day: string, turn: number) => string
  heldUntil: (day: string) => string

  keytermsTitle: string
  keytermsLede: string
  keytermsFile: string
  keytermsPass: string
  keytermsHear: string
  keytermsNote: string
  firstCall: string
  callsTitle: string
  callsLede: string
  noCalls: string
  callWithMemoryTag: string
  callWithoutMemoryTag: string
  callEscalated: string
  noSummary: string
  showTranscript: (turns: number) => string

  themeToLight: string
  themeToDark: string

  railRecall: string
  railRecallText: (facts: number) => string
  railStored: string
  railQuote: (quote: string, turn: number) => string
  railSuperseded: string
  railSupersededText: string
  railRejected: string
  railCritic: string
  railRecalled: string
  railRecalledText: string
  playQuote: string
  questionsTitle: string
  questionsLede: string
  questionsNone: string
  questionFailed: string
  answerLabel: string
  answerNote: string
  answerPlaceholder: string
  answerAction: string
  dismissAction: string
  railDoubted: string
  railDoubtedText: (words: string) => string
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
  railHungUp: string
  railFailed: string
  railRetry: string
  railRetryText: (attempt: number) => string
  railRecording: string
  railRecordingReady: string
  railFactsLost: (count: number) => string
  understandingTitle: string
  understandingLede: string

  category: Record<string, string>
  mood: Record<string, string>
  program: Record<string, string>
  rule: Record<string, string>
  phase: Record<string, string>
  reason: Record<string, string>
  questionStatus: Record<string, string>
}

const en = {
  brand: "constancia",
  home: "Home",
  dataSeed: "data: local seed",
  dataPostgres: "data: postgres",
  phoneReady: "phone: ready",
  phoneNoKeys: "phone: no keys",
  noPatients: "No patients loaded.",
  backendDown: "Could not reach the service.",
  loadFailed: (status, detail) =>
    detail ? `The service answered ${status}: ${detail}` : `The service answered ${status}.`,

  followedSince: (day) => `in follow-up since ${day}`,
  callWithoutMemory: "Call without memory",
  callWithMemory: "Call with memory",
  callHint:
    "Same questions either way. With memory the call opens with what she said last week, and a fact that contradicts an old one retires it.",
  callSameWithoutMemory: "the same call without memory",
  callReplay: "replay a recorded call",
  callAlarm: "call with a red flag",
  callLiveWithoutMemory: "Real phone, no memory",
  callLiveWithMemory: "Real phone, with memory",
  callLiveHint: "These ring an actual number and spend credit.",

  liveTitle: "Call in progress",
  liveNow: "live",
  liveEnded: "ended",
  liveDialling: "Dialling…",
  liveLost: "lost",
  liveLostDetail: "Lost the live feed for this call. Reload to see what was recorded.",
  liveUnanswered: "Nobody picked up. Twilio ended the call as",
  liveFailed: "The call ended before the audio stream started:",
  turnUnheard: "the agent was talking and did not answer this",
  railErrorDetail: "the technical detail is in the call trace",
  agent: "agent",
  patient: "patient",

  activity: "Activity",
  waitingForCall: "Waiting for the call…",

  weeklyTitle: "How she is doing",
  noNumbers: "No numeric value to chart yet.",
  measure: { symptom: "pain", adherence: "sessions", clinical_value: "reading", mood: "mood" },
  unit: { symptom: "out of 10", adherence: "a week", clinical_value: "", mood: "out of 10" },
  better: "better",
  worse: "worse",
  same: "no change",
  changeBy: (amount, verdict) => `${amount} since last week · ${verdict}`,
  onlyOneCall: "One call so far — nothing to compare against yet.",
  scaleNote: (max) => `scale 0 to ${max}`,

  fileTitle: "What the agent remembers",
  fileLede: "Every line came out of a call and keeps the words the patient used.",
  fileNote:
    "Nothing is deleted. A retired fact keeps its quote, its turn and the window it was true for.",
  noHistory: "No history: this is the first call.",
  factCurrent: "current",
  factRetired: "retired",
  saidOn: (day, turn) => `said on ${day} · turn ${turn}`,
  heldUntil: (day) => ` · held until ${day}`,

  keytermsTitle: "Words the agent listened for",
  keytermsLede:
    "Before dialling, the agent hands the speech recogniser the words from the call before, so it writes them down right.",
  keytermsFile: "last week's file",
  keytermsPass: "handed over before dialling",
  keytermsHear: "heard right on the call",
  keytermsNote: "AssemblyAI Universal-Streaming · keyterms_prompt, updated live during the call.",
  firstCall: "This was the first call: the file was empty, so there was nothing to listen for.",
  callsTitle: "Calls so far",
  callsLede:
    "One line per call. The summary is what the agent wrote for the professional right after hanging up.",
  noCalls: "No calls yet.",
  callWithMemoryTag: "with memory",
  callWithoutMemoryTag: "without memory",
  callEscalated: "escalated",
  noSummary: "No summary: the call did not get that far.",
  showTranscript: (turns) => `see the conversation (${turns} turns)`,

  themeToLight: "Switch to the light theme",
  themeToDark: "Switch to the dark theme",

  railRecall: "recall",
  railRecallText: (facts) => `${facts} facts on file`,
  railStored: "new fact",
  railQuote: (quote, turn) => `«${quote}» · turn ${turn}`,
  railSuperseded: "fact retired",
  railSupersededText: "the previous value stays, struck through",
  railRejected: "discarded",
  railCritic: "reworded",
  railRecalled: "second opinion",
  railRecalledText: "the rehab wording missed this promise; the typed model recognised it",
  playQuote: "play what the patient said",
  questionsTitle: "What the patient asked",
  questionsLede: "Questions the agent would not answer. What you write here is read out word for word on the next call.",
  questionsNone: "Nothing has been asked yet.",
  questionFailed: "That did not go through. Try again.",
  answerLabel: "Your answer",
  answerNote: "Spoken exactly as written. The agent never rephrases it.",
  answerPlaceholder: "A click with no pain is normal at this stage.",
  answerAction: "Send to the next call",
  dismissAction: "Dismiss",
  railDoubted: "read back",
  railDoubtedText: (words) => `heard "${words}" and was not sure`,
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
  railHungUp: "the patient hung up",
  railFailed: "failed",
  railRetry: "retry",
  railRetryText: (attempt) => `attempt ${attempt}`,
  railRecording: "recording",
  railRecordingReady: "ready",
  railFactsLost: (count) => `${count} facts were not saved`,
  understandingTitle: "What AssemblyAI heard in the recording",
  understandingLede: "Entity detection and sentiment over the call audio, after hangup.",

  category: {
    symptom: "symptom",
    adherence: "adherence",
    mood: "mood",
    clinical_value: "clinical value",
    red_flag: "red flag",
    commitment: "promise",
  },
  mood: { POSITIVE: "positive", NEUTRAL: "neutral", NEGATIVE: "negative" },
  program: { rehab: "rehab", postpartum: "postpartum", chronic: "chronic" },
  rule: {
    sudden_sharp_pain: "sudden sharp pain",
    fall: "a fall",
    swelling_with_fever: "swelling with fever",
    numbness: "numbness or tingling",
    heavy_bleeding: "heavy bleeding",
    fever: "a fever",
    bad_headache: "a bad headache",
    chest_pain: "chest pain or breathlessness",
    vision: "blurred or double vision",
  },
  phase: {
    recall: "recall",
    greet: "greeting",
    converse: "questions",
    extract: "extraction",
    store: "storage",
    summarize: "summary",
    analysis: "analysis",
    channel: "the phone channel",
    twilio_reader: "the Twilio stream",
    stt_reader: "speech recognition",
    tts: "the voice",
  },
  reason: {
    "no-answer": "no answer",
    busy: "busy",
    failed: "failed",
    canceled: "canceled",
    "media-stream-timeout": "audio stream timeout",
    "not grounded": "no verbatim quote backs it",
    out_of_range: "the reading is off the pack's scale",
    "clinical advice": "it gave clinical advice",
    "more than two sentences": "more than two sentences for a phone call",
    "asks nothing": "it asked nothing",
    "empty reply": "the model said nothing",
    "ungrounded number": "it used a number that is on no file",
    "memory disabled for this call": "memory disabled for this call",
    "no memory store configured": "no memory store configured",
  },
  questionStatus: {
    open: "waiting for you",
    answered: "queued for the next call",
    delivered: "read out",
    dismissed: "dismissed",
  },
} satisfies Strings

const es = {
  brand: "constancia",
  home: "Inicio",
  dataSeed: "datos: seed local",
  dataPostgres: "datos: postgres",
  phoneReady: "teléfono: listo",
  phoneNoKeys: "teléfono: sin claves",
  noPatients: "No hay pacientes cargados.",
  backendDown: "No se pudo contactar al servicio.",
  loadFailed: (status, detail) =>
    detail ? `El servicio respondió ${status}: ${detail}` : `El servicio respondió ${status}.`,

  followedSince: (day) => `en seguimiento desde ${day}`,
  callWithoutMemory: "Llamar sin memoria",
  callWithMemory: "Llamar con memoria",
  callHint:
    "Las mismas preguntas en los dos casos. Con memoria la llamada abre con lo que contó la semana pasada, y un dato que contradice a uno viejo lo retira.",
  callSameWithoutMemory: "la misma llamada sin memoria",
  callReplay: "reproducir una llamada grabada",
  callAlarm: "llamada con señal de alarma",
  callLiveWithoutMemory: "Teléfono real, sin memoria",
  callLiveWithMemory: "Teléfono real, con memoria",
  callLiveHint: "Estas hacen sonar un número de verdad y gastan crédito.",

  liveTitle: "Llamada en curso",
  liveNow: "en vivo",
  liveEnded: "terminada",
  liveDialling: "Marcando…",
  liveLost: "sin señal",
  liveLostDetail: "Se perdió el seguimiento en vivo de esta llamada. Recargá para ver lo que quedó registrado.",
  liveUnanswered: "Nadie atendió. Twilio terminó la llamada como",
  liveFailed: "La llamada terminó antes de que arrancara el audio:",
  turnUnheard: "el agente estaba hablando y no respondió a esto",
  railErrorDetail: "el detalle técnico está en la traza de la llamada",
  agent: "agente",
  patient: "paciente",

  activity: "Actividad",
  waitingForCall: "Esperando la llamada…",

  weeklyTitle: "Cómo viene",
  noNumbers: "Todavía no hay ningún valor numérico para graficar.",
  measure: { symptom: "dolor", adherence: "sesiones", clinical_value: "medición", mood: "ánimo" },
  unit: { symptom: "de 10", adherence: "por semana", clinical_value: "", mood: "de 10" },
  better: "mejor",
  worse: "peor",
  same: "sin cambio",
  changeBy: (amount, verdict) => `${amount} desde la semana pasada · ${verdict}`,
  onlyOneCall: "Una sola llamada hasta ahora — todavía no hay con qué comparar.",
  scaleNote: (max) => `escala 0 a ${max}`,

  fileTitle: "Lo que el agente recuerda",
  fileLede: "Cada línea salió de una llamada y conserva las palabras que usó el paciente.",
  fileNote:
    "No se borra nada. Un dato retirado conserva su cita, su turno y la ventana en que fue cierto.",
  noHistory: "Sin antecedentes: es la primera vez que hablan.",
  factCurrent: "vigente",
  factRetired: "retirado",
  saidOn: (day, turn) => `lo dijo el ${day} · turno ${turn}`,
  heldUntil: (day) => ` · vigente hasta el ${day}`,

  keytermsTitle: "Las palabras que el agente esperaba oír",
  keytermsLede:
    "Antes de marcar, el agente le pasa al reconocedor de voz las palabras de la llamada anterior, para que las escriba bien.",
  keytermsFile: "la ficha de la semana pasada",
  keytermsPass: "se las pasa antes de marcar",
  keytermsHear: "las escucha bien en la llamada",
  keytermsNote: "AssemblyAI Universal-Streaming · keyterms_prompt, actualizado en vivo durante la llamada.",
  firstCall: "Era la primera llamada: la ficha estaba vacía, así que no había nada que esperar.",
  callsTitle: "Las llamadas hasta ahora",
  callsLede:
    "Una línea por llamada. El resumen es lo que el agente le dejó escrito al profesional apenas cortó.",
  noCalls: "Todavía no hubo ninguna llamada.",
  callWithMemoryTag: "con memoria",
  callWithoutMemoryTag: "sin memoria",
  callEscalated: "escaló",
  noSummary: "Sin resumen: la llamada no llegó hasta ahí.",
  showTranscript: (turns) => `ver la conversación (${turns} turnos)`,

  themeToLight: "Cambiar al tema claro",
  themeToDark: "Cambiar al tema oscuro",

  railRecall: "memoria",
  railRecallText: (facts) => `${facts} datos en ficha`,
  railStored: "dato nuevo",
  railQuote: (quote, turn) => `«${quote}» · turno ${turn}`,
  railSuperseded: "dato retirado",
  railSupersededText: "el valor anterior queda tachado en la ficha",
  railRejected: "descartado",
  railCritic: "reformulado",
  railRecalled: "segunda opinión",
  railRecalledText: "la redacción de rehabilitación no vio esta promesa; el modelo tipado sí",
  playQuote: "escuchar lo que dijo el paciente",
  questionsTitle: "Lo que preguntó la paciente",
  questionsLede: "Preguntas que el agente no respondió. Lo que escribas acá se lee textual en la próxima llamada.",
  questionsNone: "Todavía no preguntó nada.",
  questionFailed: "No se pudo guardar. Probá de nuevo.",
  answerLabel: "Tu respuesta",
  answerNote: "Se dice tal cual está escrita. El agente nunca la reformula.",
  answerPlaceholder: "Un chasquido sin dolor es normal en esta etapa.",
  answerAction: "Enviar a la próxima llamada",
  dismissAction: "Descartar",
  railDoubted: "repreguntado",
  railDoubtedText: (words) => `escuchó "${words}" sin estar seguro`,
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
  railHungUp: "el paciente cortó",
  railFailed: "falló",
  railRetry: "reintento",
  railRetryText: (attempt) => `intento ${attempt}`,
  railRecording: "grabación",
  railRecordingReady: "lista",
  railFactsLost: (count) => `${count} datos no se guardaron`,
  understandingTitle: "Lo que AssemblyAI escuchó en la grabación",
  understandingLede: "Detección de entidades y sentimiento sobre el audio, después de colgar.",

  category: {
    symptom: "síntoma",
    adherence: "adherencia",
    mood: "ánimo",
    clinical_value: "valor clínico",
    red_flag: "señal de alarma",
    commitment: "promesa",
  },
  mood: { POSITIVE: "positivo", NEUTRAL: "neutro", NEGATIVE: "negativo" },
  program: { rehab: "rehabilitación", postpartum: "puerperio", chronic: "crónicos" },
  rule: {
    sudden_sharp_pain: "dolor repentino y fuerte",
    fall: "una caída",
    swelling_with_fever: "hinchazón con fiebre",
    numbness: "hormigueo o pérdida de sensibilidad",
    heavy_bleeding: "sangrado abundante",
    fever: "fiebre",
    bad_headache: "dolor de cabeza fuerte",
    chest_pain: "dolor en el pecho o falta de aire",
    vision: "visión borrosa o doble",
  },
  phase: {
    recall: "memoria",
    greet: "saludo",
    converse: "preguntas",
    extract: "extracción",
    store: "guardado",
    summarize: "resumen",
    analysis: "análisis",
    channel: "el canal telefónico",
    twilio_reader: "el stream de Twilio",
    stt_reader: "el reconocimiento de voz",
    tts: "la voz",
  },
  reason: {
    "no-answer": "sin respuesta",
    busy: "ocupado",
    failed: "falló",
    canceled: "cancelada",
    "media-stream-timeout": "el stream de audio agotó el tiempo de espera",
    "not grounded": "ninguna cita textual lo respalda",
    out_of_range: "la medición se sale de la escala del programa",
    "clinical advice": "daba una indicación clínica",
    "more than two sentences": "más de dos oraciones para una llamada",
    "asks nothing": "no preguntaba nada",
    "empty reply": "el modelo no dijo nada",
    "ungrounded number": "usaba un número que no está en ninguna ficha",
    "memory disabled for this call": "memoria desactivada en esta llamada",
    "no memory store configured": "no hay almacén de memoria configurado",
  },
  questionStatus: {
    open: "esperándote",
    answered: "en cola para la próxima llamada",
    delivered: "ya dicha",
    dismissed: "descartada",
  },
} satisfies Strings

export type Copy = Strings & {
  data: (text: string) => string
  day: (iso: string) => string
  time: (iso: string) => string
}


// ponytail: `Strings` types the nested maps as Record<string, string>, so a key that exists in
// English and not in Spanish compiles and `label()` degrades in silence — the reader just sees the
// raw backend value. `satisfies` above keeps the literal keys; this fails the build when they drift.
type Aligned<A, B> = Exclude<keyof A, keyof B> extends never
  ? Exclude<keyof B, keyof A> extends never
    ? true
    : false
  : false

const parity = {
  measure: true,
  unit: true,
  category: true,
  mood: true,
  program: true,
  rule: true,
  phase: true,
  reason: true,
  questionStatus: true,
} satisfies {
  measure: Aligned<typeof en.measure, typeof es.measure>
  unit: Aligned<typeof en.unit, typeof es.unit>
  category: Aligned<typeof en.category, typeof es.category>
  mood: Aligned<typeof en.mood, typeof es.mood>
  program: Aligned<typeof en.program, typeof es.program>
  rule: Aligned<typeof en.rule, typeof es.rule>
  phase: Aligned<typeof en.phase, typeof es.phase>
  reason: Aligned<typeof en.reason, typeof es.reason>
  questionStatus: Aligned<typeof en.questionStatus, typeof es.questionStatus>
}

void parity

const base: Record<Lang, Strings> = { en, es }

export function copy(lang: Lang): Copy {
  return {
    ...base[lang],
    data: (text) => speech(lang, text),
    day: (iso) => new Intl.DateTimeFormat(lang, { day: "numeric", month: "short" }).format(new Date(iso)),
    time: (iso) =>
      new Intl.DateTimeFormat(lang, { hour: "2-digit", minute: "2-digit" }).format(new Date(iso)),
  }
}

export function label(map: Record<string, string>, key: unknown): string {
  const raw = String(key ?? "")
  return map[raw] ?? raw.replace(/_/g, " ")
}

import type { Lang, Register } from "../prefs"

export type Copy = {
  navHow: string
  navMemory: string
  navStack: string
  navBusiness: string
  navPanel: string

  heroKicker: string
  heroTitleTop: string
  heroTitleBottom: string
  heroBodyProblem: string
  heroBodyProduct: string
  heroCtaDemo: string
  heroCtaRepo: string
  registerLabel: string
  registerTechnical: string
  registerPlain: string
  themeToLight: string
  themeToDark: string

  featurePhoneTitle: string
  featurePhoneBody: string
  featureBargeTitle: string
  featureBargeBody: string
  featureQuoteTitle: string
  featureQuoteBody: string

  demoCaption: string
  demoWeek1: string
  demoWeek2: string
  demoMemoryOn: string
  demoMemoryOff: string
  demoTranscript: string
  demoAgent: string
  demoPatient: string
  demoTurnRef: (quote: string, turn: number) => string
  demoCategory: Record<string, string>
  demoActivity: string
  demoChain: string
  demoChainFirst: string
  demoChainCurrent: string
  demoChainRetired: string
  demoChainNote: string
  demoChainNoteFirst: string
  demoReplay: string
  demoPause: string
  demoResume: string
  demoRestart: string
  demoBack: string
  demoForward: string
  demoEnded: string
  demoEndedFirst: string
  demoStreaming: (turn: number) => string
  demoPaused: (turn: number) => string

  railRecall: string
  railRecallText: string
  railNewFact: string
  railRetired: string
  railRetiredText: string
  railSummary: string
  railSummaryText: string
  railSummaryDetail: string

  statAbandonValue: string
  statAbandonLabel: string
  statVerticalsValue: string
  statVerticalsLabel: string
  statHoursValue: string
  statHoursLabel: string
  statTestsValue: string
  statTestsLabel: string

  howKicker: string
  howTitle: string
  howIntro: string
  step1Title: string
  step1Body: string
  step2Title: string
  step2Body: string
  step3Title: string
  step3Body: string
  step4Title: string
  step4Body: string

  memoryRetireTitle: string
  memoryRetireBody: string
  memoryGroundTitle: string
  memoryGroundBody: string
  memoryModesTitle: string
  memoryModesBody: string
  memoryPacksTitle: string
  memoryPacksBody: string

  stackKicker: string
  stackTitle: string
  stackTwilio: string
  stackAssembly: string
  stackGemini: string
  stackEleven: string
  stackPostgres: string
  stackLimits: string

  businessKicker: string
  businessTitle: string
  businessWhoTitle: string
  businessWhoBody: string
  businessPriceTitle: string
  businessPriceBody: string
  businessCostTitle: string
  businessCostBody: string

  closingTitle: string
  closingBody: string
  closingCtaDemo: string
  closingCtaPanel: string

  footerLicense: string
  footerWarning: string
}

const en = {
  navHow: "How it works",
  navMemory: "Memory",
  navStack: "Stack",
  navBusiness: "Model",
  navPanel: "Open the panel",

  heroKicker: "Voice agent · longitudinal memory",
  heroTitleTop: "The follow-up call",
  heroTitleBottom: "nobody makes.",
  heroBodyProblem:
    "Seven in ten home-rehab patients quit their exercise plan. Nobody phones to ask how the week went, because one professional cannot make forty calls.",
  heroBodyProduct:
    "Constancia places the call, asks the protocol in a fixed order, escalates red flags deterministically — and opens the next call with what the patient told you last week.",
  heroCtaDemo: "Watch week 1 → week 2",
  heroCtaRepo: "Read the repo",
  registerLabel: "Read this as",
  registerTechnical: "Technical",
  registerPlain: "Plain",
  themeToLight: "Switch to the light theme",
  themeToDark: "Switch to the dark theme",

  featurePhoneTitle: "Real phone line",
  featurePhoneBody: "Twilio Media Streams, bidirectional µ-law",
  featureBargeTitle: "Barge-in",
  featureBargeBody: "The patient interrupts, the agent stops",
  featureQuoteTitle: "Every fact quoted",
  featureQuoteBody: "Verbatim span + turn id, or it is discarded",

  demoCaption: "Ana · rehab",
  demoWeek1: "week 1",
  demoWeek2: "week 2",
  demoMemoryOn: "memory on",
  demoMemoryOff: "memory off",
  demoTranscript: "Live transcript",
  demoAgent: "agent",
  demoPatient: "patient",
  demoTurnRef: (quote, turn) => `«${quote}» · turn ${turn}`,
  demoCategory: { symptom: "symptom", adherence: "adherence" },
  demoActivity: "Activity",
  demoChain: "Patient file · supersession chain",
  demoChainFirst: "Patient file · 2 facts on a blank slate",
  demoChainCurrent: "current",
  demoChainRetired: "retired",
  demoChainNote:
    "Nothing is deleted. The retired fact keeps its quote, its turn id and the window it was true for.",
  demoChainNoteFirst:
    "The file was empty before this call. These two facts are what week 2 opens by asking about.",
  demoReplay: "Replay",
  demoPause: "Pause",
  demoResume: "Resume",
  demoRestart: "Start the demo over, from week 1",
  demoBack: "Previous step",
  demoForward: "Next step",
  demoEnded: "call ended · 2 facts stored, 2 retired",
  demoEndedFirst: "call ended · 2 facts stored, nothing to retire",
  demoStreaming: (turn) => `${turn} turns shown · streaming`,
  demoPaused: (turn) => `${turn} turns shown · paused`,

  railRecall: "recall",
  railRecallText: "4 facts on file",
  railNewFact: "new fact",
  railRetired: "retired",
  railRetiredText: "7/10 superseded — the old fact stays, struck through",
  railSummary: "summary",
  railSummaryText: "Pain 7 → 4. Adherence 3 → 5 sessions. No red flags.",
  railSummaryDetail: "sent to the professional",

  statAbandonValue: "70%",
  statAbandonLabel: "of home-rehab patients abandon the plan",
  statVerticalsValue: "3",
  statVerticalsLabel: "verticals on one engine — rehab, postpartum, chronic",
  statHoursValue: "333 h",
  statHoursLabel: "free streaming STT — $0.15/hour after that",
  statTestsValue: "311",
  statTestsLabel: "tests, with no network and no database",

  howKicker: "How it works",
  howTitle: "The code decides. The model only phrases.",
  howIntro:
    "A phase pipeline runs every call in the same order. The LLM never chooses what to ask, and it cannot skip a question.",
  step1Title: "Dial",
  step1Body:
    "An outbound Twilio call opens a bidirectional media stream. µ-law at 8 kHz, both directions, one socket.",
  step2Title: "Listen",
  step2Body:
    "Universal-Streaming v3 transcribes in English, end-of-turn driven, primed with the patient's own key terms.",
  step3Title: "Decide",
  step3Body:
    "The orchestrator picks the next question. A deterministic guard catches red flags with negation handling and escalates.",
  step4Title: "Remember",
  step4Body:
    "After hangup the transcript becomes facts, each grounded in a verbatim quote. Contradictions retire the old fact.",

  memoryRetireTitle: "Memory that retires itself",
  memoryRetireBody:
    "A new fact that contradicts an old one supersedes it — superseded_by and valid_until, never a delete. The professional sees the whole chain.",
  memoryGroundTitle: "Grounded or discarded",
  memoryGroundBody:
    "Every stored fact carries the patient's verbatim words and the turn they said them in. No span, no fact — extraction rejects it.",
  memoryModesTitle: "Three modes, one pipeline",
  memoryModesBody:
    "Live dials a phone. Scripted runs the full loop with no keys. Replay plays a recorded call at its original pace — the demo survives an outage.",
  memoryPacksTitle: "Packs, not forks",
  memoryPacksBody:
    "Rehab, postpartum and chronic care are config: questions, red flags and phrasing. New vertical, same engine.",

  stackKicker: "The line",
  stackTitle: "Five services, one turn, about a second.",
  stackTwilio: "Media Streams — the phone line, in and out",
  stackAssembly: "Universal-Streaming v3 live, Speech Understanding after hangup",
  stackGemini: "Phrasing and extraction only — never the decision",
  stackEleven: "µ-law voice straight onto the call",
  stackPostgres: "The fact store and its supersession chain",
  stackLimits:
    "Honest limits: extraction runs after hangup, not during the call. About 1–1.5 s of silence per turn while the sentence is written before the voice starts — sentence-level streaming is the next step. One worker: calls live in process.",

  businessKicker: "The model",
  businessTitle: "Sold per professional, not per patient.",
  businessWhoTitle: "Who pays",
  businessWhoBody:
    "An independent physiotherapist carrying 30 to 40 patients in follow-up. The tools that do anything like this start at clinic size and clinic price, so nobody is selling to them.",
  businessPriceTitle: "What it costs",
  businessPriceBody:
    "A monthly subscription per professional, tiered by patients in active follow-up: up to 20, up to 50, unlimited. Synthflow, the nearest comparable, starts at US$99 a month and aims at mid-size clinics — the entry tier here sits below it.",
  businessCostTitle: "What it costs to run",
  businessCostBody:
    "Cents per call. The recogniser is billed by the hour and a weekly check-in is minutes of audio per patient, so the variable cost stays well under the subscription as a practice grows.",

  closingTitle: "Two calls. One patient. That is the whole demo.",
  closingBody:
    "Week one with memory off, week two with it on. Same patient, same questions — and the 7/10 knee struck through by the 4/10.",
  closingCtaDemo: "Replay the call",
  closingCtaPanel: "Open the panel",

  footerLicense: "constancia · MIT licensed",
  footerWarning: "Hackathon demo on fictitious data — no authentication, not a product.",
} satisfies Copy

const es = {
  navHow: "Cómo funciona",
  navMemory: "Memoria",
  navStack: "Stack",
  navBusiness: "Modelo",
  navPanel: "Abrir el panel",

  heroKicker: "Agente de voz · memoria longitudinal",
  heroTitleTop: "La llamada de seguimiento",
  heroTitleBottom: "que nadie hace.",
  heroBodyProblem:
    "Siete de cada diez pacientes en rehabilitación domiciliaria abandonan el plan de ejercicios. Nadie llama para preguntar cómo fue la semana, porque un profesional solo no puede hacer cuarenta llamadas.",
  heroBodyProduct:
    "Constancia hace la llamada, pregunta el protocolo en un orden fijo, escala las señales de alarma de forma determinista — y abre la llamada siguiente con lo que el paciente contó la semana pasada.",
  heroCtaDemo: "Ver semana 1 → semana 2",
  heroCtaRepo: "Leer el repositorio",
  registerLabel: "Leer esto en modo",
  registerTechnical: "Técnico",
  registerPlain: "Simple",
  themeToLight: "Cambiar al tema claro",
  themeToDark: "Cambiar al tema oscuro",

  featurePhoneTitle: "Teléfono de verdad",
  featurePhoneBody: "Twilio Media Streams, µ-law bidireccional",
  featureBargeTitle: "Interrupción",
  featureBargeBody: "El paciente interrumpe y el agente se calla",
  featureQuoteTitle: "Todo dato, citado",
  featureQuoteBody: "Cita textual y número de turno, o se descarta",

  demoCaption: "Ana · rehab",
  demoWeek1: "semana 1",
  demoWeek2: "semana 2",
  demoMemoryOn: "memoria activa",
  demoMemoryOff: "memoria apagada",
  demoTranscript: "Transcripción en vivo",
  demoAgent: "agente",
  demoPatient: "paciente",
  demoTurnRef: (quote, turn) => `«${quote}» · turno ${turn}`,
  demoCategory: { symptom: "síntoma", adherence: "adherencia" },
  demoActivity: "Actividad",
  demoChain: "Ficha del paciente · cadena de supersesión",
  demoChainFirst: "Ficha del paciente · 2 datos sobre una ficha vacía",
  demoChainCurrent: "vigente",
  demoChainRetired: "retirado",
  demoChainNote:
    "No se borra nada. El dato retirado conserva su cita, su turno y la ventana en que fue cierto.",
  demoChainNoteFirst:
    "Antes de esta llamada la ficha estaba vacía. Con estos dos datos arranca la semana 2.",
  demoReplay: "Repetir",
  demoPause: "Pausar",
  demoResume: "Reanudar",
  demoRestart: "Empezar la demo de cero, desde la semana 1",
  demoBack: "Paso anterior",
  demoForward: "Paso siguiente",
  demoEnded: "llamada terminada · 2 datos nuevos, 2 retirados",
  demoEndedFirst: "llamada terminada · 2 datos nuevos, nada que retirar",
  demoStreaming: (turn) => `${turn} turnos visibles · en curso`,
  demoPaused: (turn) => `${turn} turnos visibles · pausado`,

  railRecall: "memoria",
  railRecallText: "4 datos en ficha",
  railNewFact: "dato nuevo",
  railRetired: "retirado",
  railRetiredText: "el 7/10 queda reemplazado y tachado, no borrado",
  railSummary: "resumen",
  railSummaryText: "Dolor 7 → 4. Adherencia 3 → 5 sesiones. Sin señales de alarma.",
  railSummaryDetail: "enviado al profesional",

  statAbandonValue: "70%",
  statAbandonLabel: "de los pacientes en rehabilitación domiciliaria abandonan el plan",
  statVerticalsValue: "3",
  statVerticalsLabel: "verticales sobre un solo motor — rehab, puerperio, crónicos",
  statHoursValue: "333 h",
  statHoursLabel: "de STT en streaming gratis — después, US$0,15 por hora",
  statTestsValue: "311",
  statTestsLabel: "tests, sin red y sin base de datos",

  howKicker: "Cómo funciona",
  howTitle: "El código decide. El modelo solo redacta.",
  howIntro:
    "Cada llamada corre las mismas fases en el mismo orden. El modelo nunca elige qué preguntar, y no puede saltearse una pregunta.",
  step1Title: "Marcar",
  step1Body:
    "Una llamada saliente de Twilio abre un media stream bidireccional. µ-law a 8 kHz, en los dos sentidos, un solo socket.",
  step2Title: "Escuchar",
  step2Body:
    "Universal-Streaming v3 transcribe en inglés, disparado por fin de turno, cebado con los términos del propio paciente.",
  step3Title: "Decidir",
  step3Body:
    "El orquestador elige la pregunta siguiente. Un guard determinista detecta señales de alarma, maneja las negaciones y escala.",
  step4Title: "Recordar",
  step4Body:
    "Al cortar, la transcripción se convierte en datos, cada uno anclado a una cita textual. Una contradicción retira el dato viejo.",

  memoryRetireTitle: "Una memoria que se retira sola",
  memoryRetireBody:
    "Un dato nuevo que contradice a uno viejo lo reemplaza — superseded_by y valid_until, nunca un delete. El profesional ve la cadena entera.",
  memoryGroundTitle: "Anclado o descartado",
  memoryGroundBody:
    "Cada dato guardado lleva las palabras textuales del paciente y el turno en que las dijo. Sin cita no hay dato: la extracción lo rechaza.",
  memoryModesTitle: "Tres modos, un solo pipeline",
  memoryModesBody:
    "El modo real marca un teléfono. El simulado corre el loop entero sin claves. El grabado reproduce una llamada a su ritmo original — la demo sobrevive a una caída.",
  memoryPacksTitle: "Packs, no forks",
  memoryPacksBody:
    "Rehabilitación, puerperio y crónicos son configuración: preguntas, señales de alarma y redacción. Vertical nueva, mismo motor.",

  stackKicker: "La línea",
  stackTitle: "Cinco servicios, un turno, alrededor de un segundo.",
  stackTwilio: "Media Streams — la línea telefónica, ida y vuelta",
  stackAssembly: "Universal-Streaming v3 en vivo, Speech Understanding al cortar",
  stackGemini: "Redacción y extracción, nada más — nunca la decisión",
  stackEleven: "Voz en µ-law directo sobre la llamada",
  stackPostgres: "El almacén de datos y su cadena de supersesión",
  stackLimits:
    "Límites honestos: la extracción corre después de cortar, no durante la llamada. Alrededor de 1 a 1,5 s de silencio por turno mientras se escribe la frase antes de que arranque la voz — el streaming por oraciones es el paso siguiente. Un solo worker: las llamadas viven en el proceso.",

  businessKicker: "El modelo",
  businessTitle: "Se vende por profesional, no por paciente.",
  businessWhoTitle: "Quién paga",
  businessWhoBody:
    "Un kinesiólogo independiente con 30 a 40 pacientes en seguimiento. Las herramientas que hacen algo parecido arrancan en tamaño y precio de clínica, así que nadie le vende a él.",
  businessPriceTitle: "Cuánto cuesta",
  businessPriceBody:
    "Suscripción mensual por profesional, por tramos de pacientes en seguimiento activo: hasta 20, hasta 50, ilimitado. Synthflow, lo más comparable, arranca en US$99 por mes y apunta a clínicas medianas — acá el tramo de entrada queda por debajo.",
  businessCostTitle: "Cuánto cuesta operarlo",
  businessCostBody:
    "Centavos por llamada. El reconocedor se factura por hora y un control semanal son minutos de audio por paciente, así que el costo variable queda muy por debajo de la suscripción a medida que el consultorio crece.",

  closingTitle: "Dos llamadas. Un paciente. Esa es toda la demo.",
  closingBody:
    "Semana uno con la memoria apagada, semana dos con la memoria prendida. Mismo paciente, mismas preguntas — y la rodilla 7/10 tachada por el 4/10.",
  closingCtaDemo: "Repetir la llamada",
  closingCtaPanel: "Abrir el panel",

  footerLicense: "constancia · licencia MIT",
  footerWarning: "Demo de hackathon con datos ficticios — sin autenticación, no es un producto.",
} satisfies Copy

const enPlain = {
  demoChain: "What Ana said before, and what she says now",
  demoChainFirst: "What Ana told us on the very first call",
  demoChainCurrent: "now",
  demoChainRetired: "replaced",
  demoChainNote:
    "The old answer is not erased. It stays, crossed out, next to the dates it was true between, so you can always see what changed and when.",
  demoChainNoteFirst:
    "Nobody had asked her any of this before. Next week the call starts from these two answers instead of from zero.",

  heroKicker: "A phone call that remembers",
  heroBodyProduct:
    "Constancia phones your patients once a week, asks the same questions every time, tells you straight away if something sounds wrong — and starts the next call with what they told you last week.",
  heroCtaDemo: "See how a second call goes",

  featurePhoneTitle: "A real phone call",
  featurePhoneBody: "Their phone rings. No app to install.",
  featureBargeTitle: "You can cut in",
  featureBargeBody: "Start talking and it stops, like a person would",
  featureQuoteTitle: "It shows its work",
  featureQuoteBody: "Every note comes with the sentence it came from",

  howTitle: "The questions are fixed. Only the wording is not.",
  howIntro:
    "Every call follows the same steps in the same order. The AI chooses how to say things, never what to ask, and it cannot skip a question.",
  step1Title: "It calls",
  step1Body: "The patient's phone rings, like any other call. Nothing to install, nothing to log into.",
  step2Title: "It listens",
  step2Body:
    "It understands the patient speaking and knows when they have finished, so it does not interrupt.",
  step3Title: "It asks",
  step3Body:
    "It works through your questions in order. If the patient mentions a fall or a sudden pain, it stops and tells them to contact you today.",
  step4Title: "It remembers",
  step4Body:
    "When the call ends it writes down what matters, quoting the patient word for word. If something changed, the old note is kept and marked as no longer true.",

  memoryRetireTitle: "Nothing gets erased",
  memoryRetireBody:
    "When a patient says the pain dropped from 7 to 4, the 7 is not deleted. It stays, crossed out, so you see the whole progression instead of just today's number.",
  memoryGroundTitle: "You can check everything",
  memoryGroundBody:
    "Every note shows the exact words the patient said and which moment of the call they said them in. If it cannot point at a sentence, it does not write the note.",
  memoryModesTitle: "It works without a phone",
  memoryModesBody:
    "There is a rehearsal mode that plays a whole call with no phone and no accounts, and a recording mode that replays a real one. The demo works even if the internet does not.",
  memoryPacksTitle: "Not only physiotherapy",
  memoryPacksBody:
    "Postpartum check-ins and chronic conditions use the same system with different questions. Nothing is rebuilt.",

  stackKicker: "What it runs on",
  stackTitle: "Five pieces, about a second between question and answer.",
  stackTwilio: "Places the call and carries the audio",
  stackAssembly: "Turns the patient's speech into text while they talk",
  stackGemini: "Writes the sentences the agent says out loud",
  stackEleven: "Gives the agent its voice",
  stackPostgres: "Keeps the patient's history",
  stackLimits:
    "Being honest: the notes are written a few seconds after the call ends, not during it. There is about a second of pause before each reply, which sounds like someone thinking. And this is one machine — it is a demo, not a service.",

  closingBody:
    "The first week it knows nothing and asks from scratch. The second week it opens by asking about the knee she mentioned — and when she says it is better, the old number gets crossed out in front of you.",
} satisfies Partial<Copy>

type PlainKey = keyof typeof enPlain

const esPlain: Record<PlainKey, string> = {
  demoChain: "Lo que Ana dijo antes, y lo que dice ahora",
  demoChainFirst: "Lo que Ana contó en la primera llamada",
  demoChainCurrent: "ahora",
  demoChainRetired: "reemplazado",
  demoChainNote:
    "La respuesta vieja no se borra. Queda tachada, al lado de las fechas entre las que fue cierta, así siempre se ve qué cambió y cuándo.",
  demoChainNoteFirst:
    "Nadie le había preguntado nada de esto antes. La semana que viene la llamada arranca de estas dos respuestas y no de cero.",

  heroKicker: "Una llamada que se acuerda",
  heroBodyProduct:
    "Constancia llama a tus pacientes una vez por semana, hace siempre las mismas preguntas, te avisa enseguida si algo suena mal — y arranca la llamada siguiente con lo que te contaron la semana pasada.",
  heroCtaDemo: "Ver cómo sale la segunda llamada",

  featurePhoneTitle: "Una llamada de verdad",
  featurePhoneBody: "Les suena el teléfono. No hay que instalar nada.",
  featureBargeTitle: "Le podés cortar",
  featureBargeBody: "Si empezás a hablar, se calla, como una persona",
  featureQuoteTitle: "Muestra de dónde lo sacó",
  featureQuoteBody: "Cada dato viene con la frase que lo respalda",

  howTitle: "Las preguntas están fijas. Lo único suelto es cómo se dicen.",
  howIntro:
    "Todas las llamadas siguen los mismos pasos en el mismo orden. La inteligencia artificial elige cómo decir las cosas, nunca qué preguntar, y no puede saltearse ninguna.",
  step1Title: "Llama",
  step1Body:
    "Al paciente le suena el teléfono, como cualquier llamada. Nada que instalar, ninguna cuenta que crear.",
  step2Title: "Escucha",
  step2Body:
    "Entiende al paciente hablando y se da cuenta de cuándo terminó, así que no lo interrumpe.",
  step3Title: "Pregunta",
  step3Body:
    "Recorre tus preguntas en orden. Si el paciente menciona una caída o un dolor repentino, frena y le dice que te contacte hoy mismo.",
  step4Title: "Se acuerda",
  step4Body:
    "Cuando la llamada termina, anota lo que importa citando al paciente palabra por palabra. Si algo cambió, la nota vieja se conserva y queda marcada como que ya no es cierta.",

  memoryRetireTitle: "No se borra nada",
  memoryRetireBody:
    "Cuando la paciente dice que el dolor bajó de 7 a 4, el 7 no se borra. Queda, tachado, así ves la evolución completa y no solo el número de hoy.",
  memoryGroundTitle: "Podés verificar todo",
  memoryGroundBody:
    "Cada nota muestra las palabras exactas que dijo el paciente y en qué momento de la llamada las dijo. Si no puede señalar una frase, no escribe la nota.",
  memoryModesTitle: "Funciona sin teléfono",
  memoryModesBody:
    "Hay un modo ensayo que reproduce una llamada entera sin teléfono ni cuentas, y un modo grabación que repite una real. La demo funciona aunque no ande internet.",
  memoryPacksTitle: "No solo kinesiología",
  memoryPacksBody:
    "El seguimiento de puerperio y el de enfermedades crónicas usan el mismo sistema con otras preguntas. No se rehace nada.",

  stackKicker: "Con qué está hecho",
  stackTitle: "Cinco piezas, alrededor de un segundo entre pregunta y respuesta.",
  stackTwilio: "Hace la llamada y lleva el audio",
  stackAssembly: "Convierte lo que dice el paciente en texto mientras habla",
  stackGemini: "Escribe las frases que el agente dice en voz alta",
  stackEleven: "Le pone la voz al agente",
  stackPostgres: "Guarda la historia del paciente",
  stackLimits:
    "Siendo honestos: las notas se escriben unos segundos después de que termina la llamada, no durante. Hay como un segundo de pausa antes de cada respuesta, que suena a alguien pensando. Y esto corre en una sola máquina: es una demo, no un servicio.",

  closingBody:
    "La primera semana no sabe nada y pregunta de cero. La segunda abre preguntando por la rodilla que ella mencionó — y cuando dice que está mejor, el número viejo se tacha delante tuyo.",
}

// ponytail: `Copy` types demoCategory as Record<string, string>, so a key in one language and not
// the other compiles and the card falls back to the raw backend value in silence. `satisfies` above
// keeps the literal keys; this fails the build when they drift. The twin of web/src/panel/copy.ts.
type Aligned<A, B> = Exclude<keyof A, keyof B> extends never
  ? Exclude<keyof B, keyof A> extends never
    ? true
    : false
  : false

const parity = { demoCategory: true } satisfies {
  demoCategory: Aligned<typeof en.demoCategory, typeof es.demoCategory>
}

void parity

const base: Record<Lang, Copy> = { en, es }
const plain: Record<Lang, Record<PlainKey, string>> = { en: enPlain, es: esPlain }

export function copy(lang: Lang, register: Register): Copy {
  return register === "plain" ? { ...base[lang], ...plain[lang] } : base[lang]
}

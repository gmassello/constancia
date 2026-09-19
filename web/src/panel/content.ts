import type { Lang } from "../prefs"

const EN: Record<string, string> = {
  "Hola Ana, soy el asistente de seguimiento de tu kinesiólogo. Te llamo para ver cómo viene la recuperación esta semana.":
    "Hi Ana, I am your physio's follow-up assistant. I am calling to see how your recovery is going this week.",
  "Hola Ana, soy el asistente de seguimiento de tu kinesiólogo. Te llamo para ver cómo venís con la recuperación esta semana.":
    "Hi Ana, I am your physio's follow-up assistant. I am calling to see how you are doing with your recovery this week.",
  "Hola Ana, soy el asistente de seguimiento de tu kinesiólogo. La semana pasada me contaste que la rodilla te dolía siete de diez al subir escaleras, así que te llamo para ver cómo viene esta semana.":
    "Hi Ana, I am your physio's follow-up assistant. Last week you told me your knee hurt seven out of ten climbing stairs, so I am calling to see how it has been this week.",
  "Hola, sí, soy Ana.": "Hello, yes, this is Ana.",

  "¿Cuánto te duele hoy del uno al diez, y en qué momento lo sentís más?":
    "How much does it hurt today from one to ten, and when do you feel it most?",
  "Contame, ¿cuánto te duele hoy del uno al diez, y en qué momento o con qué movimiento lo notás más?":
    "Tell me, how much does it hurt today from one to ten, and at what moment or with what movement do you notice it most?",
  "Contame, ¿cuánto te duele hoy del uno al diez al subir escaleras?":
    "Tell me, how much does it hurt today from one to ten climbing stairs?",
  "La rodilla derecha me duele siete de diez, sobre todo cuando subo escaleras.":
    "My right knee hurts seven out of ten, especially when I climb stairs.",
  "La rodilla mejoró bastante, ahora me duele cuatro de diez al subir escaleras.":
    "My knee is a lot better, it is four out of ten on the stairs now.",

  "¿Cuántas veces pudiste hacer los ejercicios esta semana?":
    "How many times did you manage the exercises this week?",
  "¿Cuántas veces pudiste hacer los ejercicios esta semana? ¿Te costó sostener la rutina?":
    "How many times did you manage the exercises this week? Was it hard to keep the routine up?",
  "La semana pasada los ejercicios los hiciste tres veces. ¿Cuántas veces pudiste esta semana?":
    "Last week you did the exercises three times. How many times did you manage this week?",
  "Los hice tres veces, me salté dos días porque estuve con mucho trabajo.":
    "I did them three times, I skipped two days because I had a lot of work.",
  "Los ejercicios los hice tres veces, me salté dos días porque estuve con mucho trabajo.":
    "I did the exercises three times, I skipped two days because I had a lot of work.",
  "Esta semana los hice cinco veces, me organicé mejor.":
    "I did them five times this week, I got myself better organised.",

  "¿Tuviste alguna molestia nueva después de los ejercicios?":
    "Did you have any new discomfort after the exercises?",
  "¿Tuviste alguna molestia nueva después de los ejercicios, algo de hinchazón o rigidez?":
    "Did you have any new discomfort after the exercises, any swelling or stiffness?",
  "Después de los ejercicios me queda un poco rígida, nada raro.":
    "After the exercises it stays a little stiff, nothing strange.",
  "No, ninguna molestia nueva.": "No, no new discomfort.",

  "¿Y tuviste alguna caída o algo que te haya asustado?":
    "And did you have a fall, or anything that scared you?",
  "Una última: ¿tuviste alguna caída, un dolor repentino y fuerte, o algo que te haya asustado?":
    "One last one: did you have a fall, a sudden sharp pain, or anything that scared you?",
  "Hace tres semanas me caí en el baño, pero desde que empecé el plan no me pasó nada.":
    "Three weeks ago I fell in the bathroom, but nothing has happened since I started the plan.",
  "No, caídas no tuve, nada de eso.": "No, no falls, nothing like that.",
  "No, nada de eso.": "No, nothing like that.",

  "Listo, eso era todo por hoy. Le paso el resumen a tu kinesiólogo. Cuidate, hablamos la semana que viene.":
    "That is everything for today. I will send the summary to your physio. Take care, we will talk next week.",

  "Primera semana de seguimiento. Dolor de rodilla derecha 7/10 al subir escaleras. Hizo los ejercicios tres veces y se salteó dos días por trabajo. Rigidez leve después de los ejercicios. Refiere una caída en el baño hace tres semanas, anterior al plan.":
    "First follow-up week. Right knee pain 7/10 climbing stairs. Did the exercises three times and skipped two days for work. Mild stiffness after the exercises. Reports a bathroom fall three weeks ago, before the plan started.",
  "Primera llamada de seguimiento. Refiere dolor en rodilla derecha 7/10 al subir escaleras. Hizo los ejercicios tres veces y se salteó dos días por trabajo. Rigidez leve después de los ejercicios, sin señales de alarma.":
    "First follow-up call. Reports right knee pain 7/10 climbing stairs. Did the exercises three times and skipped two days for work. Mild stiffness after the exercises, no red flags.",
  "Segunda llamada de seguimiento. El dolor en rodilla derecha bajó de 7/10 a 4/10 al subir escaleras. Mejoró la adherencia: cinco sesiones esta semana contra tres la anterior. Sin molestias nuevas ni señales de alarma.":
    "Second follow-up call. Right knee pain dropped from 7/10 to 4/10 climbing stairs. Adherence improved: five sessions this week against three the week before. No new discomfort and no red flags.",

  "dolor en la rodilla derecha 7/10 al subir escaleras": "right knee pain 7/10 climbing stairs",
  "dolor en la rodilla derecha 4/10 al subir escaleras": "right knee pain 4/10 climbing stairs",
  "hizo los ejercicios tres veces en la semana y se salteó dos días por trabajo":
    "did the exercises three times, skipped two days for work",
  "hizo los ejercicios tres veces en la semana": "did the exercises three times this week",
  "hizo los ejercicios cinco veces en la semana": "did the exercises five times this week",
  "rigidez en la rodilla después de los ejercicios": "knee stiffness after the exercises",
  "se cayó en el baño hace tres semanas, antes de empezar el plan":
    "fell in the bathroom three weeks ago, before starting the plan",

  "rodilla derecha": "right knee",
  "ejercicios en casa": "home exercises",
  rigidez: "stiffness",
  "caída en el baño": "bathroom fall",

  "La rodilla derecha me duele siete de diez": "My right knee hurts seven out of ten",
  "me duele siete de diez": "hurts seven out of ten",
  "me duele cuatro de diez": "it is four out of ten",
  "Los hice tres veces, me salté dos días": "I did them three times, I skipped two days",
  "los hice tres veces": "I did the exercises three times",
  "los hice cinco veces": "I did them five times",
  "me queda un poco rígida": "it stays a little stiff",
  "me caí en el baño": "I fell in the bathroom",
}

export function speech(lang: Lang, text: string): string {
  // ponytail: keyed by the Spanish string, so anything the extractor produces live
  // falls through untranslated instead of showing the wrong sentence.
  return lang === "en" ? (EN[text] ?? text) : text
}

import type { Lang } from "../prefs"

const ES: Record<string, string> = {
  "Hi Ana, I am your physio's follow-up assistant. I am calling to see how your recovery is going this week.":
    "Hola Ana, soy el asistente de seguimiento de tu kinesiólogo. Te llamo para ver cómo viene la recuperación esta semana.",
  "Hi Ana, I am your physio's follow-up assistant. I am calling to see how you are doing with your recovery this week.":
    "Hola Ana, soy el asistente de seguimiento de tu kinesiólogo. Te llamo para ver cómo venís con la recuperación esta semana.",
  "Hi Ana, I am your physio's follow-up assistant. Last week you told me your knee hurt seven out of ten climbing stairs, so I am calling to see how it has been this week.":
    "Hola Ana, soy el asistente de seguimiento de tu kinesiólogo. La semana pasada me contaste que la rodilla te dolía siete de diez al subir escaleras, así que te llamo para ver cómo viene esta semana.",
  "Hello, yes, this is Ana.": "Hola, sí, soy Ana.",

  "How much does it hurt today from one to ten, and when do you feel it most?":
    "¿Cuánto te duele hoy del uno al diez, y en qué momento lo sentís más?",
  "Tell me, how much does it hurt today from one to ten, and at what moment or with what movement do you notice it most?":
    "Contame, ¿cuánto te duele hoy del uno al diez, y en qué momento o con qué movimiento lo notás más?",
  "Tell me, how much does it hurt today from one to ten climbing stairs?":
    "Contame, ¿cuánto te duele hoy del uno al diez al subir escaleras?",
  "My right knee hurts seven out of ten, especially when I climb stairs.":
    "La rodilla derecha me duele siete de diez, sobre todo cuando subo escaleras.",
  "My knee is a lot better, it is four out of ten on the stairs now.":
    "La rodilla mejoró bastante, ahora me duele cuatro de diez al subir escaleras.",

  "How many times did you manage the exercises this week?":
    "¿Cuántas veces pudiste hacer los ejercicios esta semana?",
  "How many times did you manage the exercises this week? Was it hard to keep the routine up?":
    "¿Cuántas veces pudiste hacer los ejercicios esta semana? ¿Te costó sostener la rutina?",
  "Last week you did the exercises three times. How many times did you manage this week?":
    "La semana pasada los ejercicios los hiciste tres veces. ¿Cuántas veces pudiste esta semana?",
  "I did them three times, I skipped two days because I had a lot of work.":
    "Los hice tres veces, me salté dos días porque estuve con mucho trabajo.",
  "I did the exercises three times, I skipped two days because I had a lot of work.":
    "Los ejercicios los hice tres veces, me salté dos días porque estuve con mucho trabajo.",
  "I did them five times this week, I got myself better organised.":
    "Esta semana los hice cinco veces, me organicé mejor.",

  "Did you have any new discomfort after the exercises?":
    "¿Tuviste alguna molestia nueva después de los ejercicios?",
  "Did you have any new discomfort after the exercises, any swelling or stiffness?":
    "¿Tuviste alguna molestia nueva después de los ejercicios, algo de hinchazón o rigidez?",
  "After the exercises it stays a little stiff, nothing strange.":
    "Después de los ejercicios me queda un poco rígida, nada raro.",
  "No, no new discomfort.": "No, ninguna molestia nueva.",

  "And did you have a fall, or anything that scared you?":
    "¿Y tuviste alguna caída o algo que te haya asustado?",
  "One last one: did you have a fall, a sudden sharp pain, or anything that scared you?":
    "Una última: ¿tuviste alguna caída, un dolor repentino y fuerte, o algo que te haya asustado?",
  "Three weeks ago I fell in the bathroom, but nothing has happened since I started the plan.":
    "Hace tres semanas me caí en el baño, pero desde que empecé el plan no me pasó nada.",
  "No, no falls, nothing like that.": "No, caídas no tuve, nada de eso.",
  "The knee is about the same, five out of ten climbing stairs.":
    "La rodilla viene parecida, cinco de diez al subir escaleras.",
  "I only did them twice, because on Tuesday I fell coming down the stairs and I was left sore.":
    "Los hice dos veces nada más, porque el martes me caí bajando la escalera y quedé dolorida.",
  "Ana, a fall is something that has to be looked at today. Please contact your physio now and tell them what you told me; I am flagging this call so they see it. Take good care.":
    "Ana, una caída es algo que hay que ver hoy mismo. Por favor contactá ahora a tu kinesiólogo y contale lo que me dijiste; yo dejo esta llamada marcada para que la vea. Cuidate mucho.",
  "No, nothing like that.": "No, nada de eso.",

  "That is everything for today. I will send the summary to your physio. Take care, we will talk next week.":
    "Listo, eso era todo por hoy. Le paso el resumen a tu kinesiólogo. Cuidate, hablamos la semana que viene.",

  "First follow-up week. Right knee pain 7/10 climbing stairs. Did the exercises three times and skipped two days for work. Mild stiffness after the exercises. Reports a bathroom fall three weeks ago, before the plan started.":
    "Primera semana de seguimiento. Dolor de rodilla derecha 7/10 al subir escaleras. Hizo los ejercicios tres veces y se salteó dos días por trabajo. Rigidez leve después de los ejercicios. Refiere una caída en el baño hace tres semanas, anterior al plan.",
  "First follow-up call. Reports right knee pain 7/10 climbing stairs. Did the exercises three times and skipped two days for work. Mild stiffness after the exercises, no red flags.":
    "Primera llamada de seguimiento. Refiere dolor en rodilla derecha 7/10 al subir escaleras. Hizo los ejercicios tres veces y se salteó dos días por trabajo. Rigidez leve después de los ejercicios, sin señales de alarma.",
  "Second follow-up call. Right knee pain dropped from 7/10 to 4/10 climbing stairs. Adherence improved: five sessions this week against three the week before. No new discomfort and no red flags.":
    "Segunda llamada de seguimiento. El dolor en rodilla derecha bajó de 7/10 a 4/10 al subir escaleras. Mejoró la adherencia: cinco sesiones esta semana contra tres la anterior. Sin molestias nuevas ni señales de alarma.",
  "Follow-up call. Reports right knee pain 4/10 climbing stairs. Did the exercises five times. No new discomfort and no red flags.":
    "Llamada de seguimiento. Refiere dolor en rodilla derecha 4/10 al subir escaleras. Hizo los ejercicios cinco veces. Sin molestias nuevas ni señales de alarma.",
  "Follow-up call cut short by a red flag. Right knee pain 5/10 climbing stairs. Did the exercises twice. Reports a fall coming down the stairs on Tuesday: she was asked to contact her physio today and the call was flagged.":
    "Llamada de seguimiento interrumpida por señal de alarma. Dolor de rodilla derecha 5/10 al subir escaleras. Hizo los ejercicios dos veces. Refiere una caída bajando la escalera el martes: se le pidió contactar al kinesiólogo hoy mismo y la llamada quedó marcada.",

  "right knee pain 7/10 climbing stairs": "dolor en la rodilla derecha 7/10 al subir escaleras",
  "right knee pain 4/10 climbing stairs": "dolor en la rodilla derecha 4/10 al subir escaleras",
  "right knee pain 5/10 climbing stairs": "dolor en la rodilla derecha 5/10 al subir escaleras",
  "did the exercises twice this week": "hizo los ejercicios dos veces en la semana",
  "fell coming down the stairs on Tuesday": "se cayó bajando la escalera el martes",
  "did the exercises three times, skipped two days for work":
    "hizo los ejercicios tres veces en la semana y se salteó dos días por trabajo",
  "did the exercises three times this week": "hizo los ejercicios tres veces en la semana",
  "did the exercises five times this week": "hizo los ejercicios cinco veces en la semana",
  "knee stiffness after the exercises": "rigidez en la rodilla después de los ejercicios",
  "fell in the bathroom three weeks ago, before starting the plan":
    "se cayó en el baño hace tres semanas, antes de empezar el plan",

  "right knee": "rodilla derecha",
  "home exercises": "ejercicios en casa",
  "stiffness": "rigidez",
  "bathroom fall": "caída en el baño",
  "stairs fall": "caída en escalera",

  "My right knee hurts seven out of ten": "La rodilla derecha me duele siete de diez",
  "hurts seven out of ten": "me duele siete de diez",
  "it is four out of ten": "me duele cuatro de diez",
  "I did them three times, I skipped two days": "Los hice tres veces, me salté dos días",
  "I did the exercises three times": "los hice tres veces",
  "I did them five times": "los hice cinco veces",
  "it stays a little stiff": "me queda un poco rígida",
  "I fell in the bathroom": "me caí en el baño",
  "five out of ten": "cinco de diez",
  "did them twice": "Los hice dos veces",
  "I fell coming down the stairs": "me caí bajando la escalera",
}

export function speech(lang: Lang, text: string): string {
  // ponytail: keyed by the English string the call actually produces, so anything the
  // extractor writes live falls through untranslated instead of showing a wrong sentence.
  return lang === "es" ? (ES[text] ?? text) : text
}

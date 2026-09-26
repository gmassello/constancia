import { useCallback, useEffect, useState } from "react"

export type Theme = "dark" | "light"
export type Lang = "en" | "es"
export type Register = "technical" | "plain"

const THEME_KEY = "constancia.theme"
const LANG_KEY = "constancia.lang"
const REGISTER_KEY = "constancia.register"

function read(key: string): string | null {
  try {
    return window.localStorage.getItem(key)
  } catch {
    return null
  }
}

function write(key: string, value: string): void {
  try {
    window.localStorage.setItem(key, value)
  } catch {}
}

function queryLang(): Lang | null {
  const asked = new URLSearchParams(window.location.search).get("lang")
  return asked === "es" || asked === "en" ? asked : null
}

export function initialTheme(): Theme {
  return read(THEME_KEY) === "dark" ? "dark" : "light"
}

export function initialLang(): Lang {
  return queryLang() ?? (read(LANG_KEY) === "es" ? "es" : "en")
}

export function initialRegister(): Register {
  return read(REGISTER_KEY) === "technical" ? "technical" : "plain"
}

export function prefersReducedMotion(): boolean {
  return window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false
}

export function usePrefs() {
  const [theme, setThemeState] = useState<Theme>(initialTheme)
  const [lang, setLangState] = useState<Lang>(initialLang)
  const [register, setRegisterState] = useState<Register>(initialRegister)

  useEffect(() => {
    document.documentElement.dataset.theme = theme
  }, [theme])

  useEffect(() => {
    document.documentElement.lang = lang
  }, [lang])

  const setTheme = useCallback((next: Theme) => {
    write(THEME_KEY, next)
    setThemeState(next)
  }, [])

  const setLang = useCallback((next: Lang) => {
    write(LANG_KEY, next)
    setLangState(next)
  }, [])

  const setRegister = useCallback((next: Register) => {
    write(REGISTER_KEY, next)
    setRegisterState(next)
  }, [])

  return { theme, setTheme, lang, setLang, register, setRegister }
}

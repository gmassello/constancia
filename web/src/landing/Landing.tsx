import { useEffect, useRef, useState } from "react"

import DemoCard from "./DemoCard"
import { copy } from "./copy"
import { prefersReducedMotion, usePrefs, type Lang, type Register } from "../prefs"

const REPO = "https://github.com/gmassello/constancia"
const COUNT_MS = 900
const FIGURE = /^(\d+)(.*)$/
const SECTIONS = ["how", "memory", "stack", "business"] as const

function useNav() {
  const [scrolled, setScrolled] = useState(false)
  const [current, setCurrent] = useState("")
  const showing = useRef(new Set<string>())

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 0)
    onScroll()
    window.addEventListener("scroll", onScroll, { passive: true })

    // ponytail: the topmost section inside a strip under the header wins. The strip starts at 88px
    // and not at the header's 64, because the sections carry `scroll-margin-top: 80px`: a nav click
    // parks the boundary between two of them at exactly 80, and a strip that reaches it keeps the
    // outgoing section intersecting by a few pixels, so the nav marks the one you just left.
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) showing.current.add(entry.target.id)
          else showing.current.delete(entry.target.id)
        }
        setCurrent(SECTIONS.find((id) => showing.current.has(id)) ?? "")
      },
      { rootMargin: "-88px 0px -70% 0px" },
    )
    for (const id of SECTIONS) {
      const node = document.getElementById(id)
      if (node) observer.observe(node)
    }

    return () => {
      window.removeEventListener("scroll", onScroll)
      observer.disconnect()
    }
  }, [])

  return { scrolled, current }
}

const SUN = "M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10Zm0-14v2m0 18v-2M3 12h2m14 0h2M5.6 5.6l1.4 1.4m10 10 1.4 1.4m0-12.8-1.4 1.4m-10 10-1.4 1.4"
const MOON = "M21 13a9 9 0 1 1-10-10 7 7 0 0 0 10 10Z"

function Kicker({ text }: { text: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
      <span className="rule-mark" />
      <h6 style={{ margin: 0, color: "var(--text-accent)" }}>{text}</h6>
    </div>
  )
}

function Step({ index, title, body }: { index: string; title: string; body: string }) {
  return (
    <div className="step-column">
      <div className="caption" style={{ color: "var(--color-accent)", marginBottom: 14 }}>
        {index}
      </div>
      <h4 style={{ margin: "0 0 8px" }}>{title}</h4>
      <p className="body-sm" style={{ margin: 0, color: "var(--text-secondary)" }}>
        {body}
      </p>
    </div>
  )
}

function Pillar({ title, body }: { title: string; body: string }) {
  return (
    <div className="step-column">
      <h4 style={{ margin: "0 0 9px" }}>{title}</h4>
      <p className="body-sm" style={{ margin: 0, color: "var(--text-secondary)" }}>
        {body}
      </p>
    </div>
  )
}

function Stat({ value, label, lang }: { value: string; label: string; lang: Lang }) {
  const found = FIGURE.exec(value)
  const target = found ? Number(found[1]) : null
  const suffix = found ? found[2] : ""
  const [shown, setShown] = useState(() => (target !== null && !prefersReducedMotion() ? 0 : target))
  const node = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (target === null || prefersReducedMotion() || !node.current) return
    // ponytail: the timeout is the backstop, not a second clock. A hidden tab suspends
    // requestAnimationFrame outright, so a counter that started counting and then lost the frames
    // freezes at whatever it reached — 3% where the page claims 70%. The timeout is throttled but
    // still fires, and it writes the value the animation would have landed on anyway.
    let landed = 0
    const observer = new IntersectionObserver(
      (entries) => {
        if (!entries[0].isIntersecting) return
        observer.disconnect()
        const from = performance.now()
        const step = (now: number) => {
          const through = Math.min((now - from) / COUNT_MS, 1)
          setShown(Math.round(target * (1 - (1 - through) ** 3)))
          if (through < 1) requestAnimationFrame(step)
        }
        requestAnimationFrame(step)
        landed = window.setTimeout(() => setShown(target), COUNT_MS)
      },
      { threshold: 0.5 },
    )
    observer.observe(node.current)
    return () => {
      observer.disconnect()
      window.clearTimeout(landed)
    }
  }, [target])

  return (
    <div ref={node}>
      <div className="display-md" style={{ color: "var(--section-ink)" }}>
        {shown === null ? value : `${new Intl.NumberFormat(lang).format(shown)}${suffix}`}
      </div>
      <div
        className="caption"
        style={{ marginTop: 6, color: "color-mix(in srgb, var(--section-ink) 80%, transparent)" }}
      >
        {label}
      </div>
    </div>
  )
}

function StackCard({ name, body, focus }: { name: string; body: string; focus?: boolean }) {
  return (
    <div className={focus ? "stack-card is-focus" : "stack-card"}>
      <div className="body-sm" style={{ fontWeight: 500, marginBottom: 5 }}>
        {name}
      </div>
      <div
        className="caption"
        style={{ color: focus ? "var(--text-secondary)" : "var(--text-muted)" }}
      >
        {body}
      </div>
    </div>
  )
}

export default function Landing() {
  const { theme, setTheme, lang, setLang, register, setRegister } = usePrefs()
  const c = copy(lang, register)
  const dark = theme === "dark"
  const { scrolled, current } = useNav()
  const navText = {
    how: c.navHow,
    memory: c.navMemory,
    stack: c.navStack,
    business: c.navBusiness,
  }

  return (
    <div className="landing-shell">
      <header className={scrolled ? "landing-header scrolled" : "landing-header"}>
        <div style={{ display: "flex", alignItems: "center", gap: 9, marginRight: "auto" }}>
          <span
            style={{
              width: 9,
              height: 9,
              borderRadius: "50%",
              background: "var(--color-accent)",
              boxShadow: "0 0 12px var(--color-accent)",
            }}
          />
          <span className="card-title">constancia</span>
        </div>
        <nav className="landing-nav">
          {SECTIONS.map((id) => (
            <a
              key={id}
              href={`#${id}`}
              className={current === id ? "on" : undefined}
              aria-current={current === id ? "true" : undefined}
            >
              {navText[id]}
            </a>
          ))}
        </nav>
        <div className="seg">
          {(["en", "es"] as Lang[]).map((option) => (
            <label className="seg-opt" key={option}>
              <input
                type="radio"
                name="lang"
                checked={lang === option}
                onChange={() => setLang(option)}
              />
              {option.toUpperCase()}
            </label>
          ))}
        </div>
        <button
          className="btn btn-secondary btn-icon"
          onClick={() => setTheme(dark ? "light" : "dark")}
          aria-label={dark ? c.themeToLight : c.themeToDark}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
            <path d={dark ? SUN : MOON} strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        <a className="btn btn-primary" href="/panel">
          {c.navPanel}
        </a>
      </header>

      <section
        style={{
          position: "relative",
          padding: "var(--section-pad)",
        }}
      >
        <div
          className="glow"
          style={{
            top: -180,
            left: -120,
            width: 620,
            height: 620,
            background: "radial-gradient(circle, var(--orb-mint), transparent 68%)",
          }}
        />
        <div
          className="hero-grid"
          style={{
            position: "relative",
            maxWidth: "var(--container)",
            margin: "0 auto",
            display: "grid",
            gridTemplateColumns: "minmax(0, 1.02fr) minmax(0, 1fr)",
            gap: "clamp(28px, 4vw, 56px)",
            alignItems: "start",
          }}
        >
          <div style={{ minWidth: 0 }}>
            <Kicker text={c.heroKicker} />
            <h1 className="display-xl" style={{ margin: "0 0 20px", textWrap: "pretty" }}>
              {c.heroTitleTop}
              <br />
              {c.heroTitleBottom}
            </h1>
            <p
              className="body-lg"
              style={{ maxWidth: "46ch", color: "var(--text-secondary)", margin: "0 0 14px" }}
            >
              {c.heroBodyProblem}
            </p>
            <p
              className="body-lg"
              style={{ maxWidth: "46ch", color: "var(--text-secondary)", margin: "0 0 20px" }}
            >
              {c.heroBodyProduct}
            </p>

            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 28 }}>
              <span className="caption" style={{ color: "var(--text-muted)" }}>
                {c.registerLabel}
              </span>
              <div className="seg">
                {(
                  [
                    ["technical", c.registerTechnical],
                    ["plain", c.registerPlain],
                  ] as Array<[Register, string]>
                ).map(([option, label]) => (
                  <label className="seg-opt" key={option}>
                    <input
                      type="radio"
                      name="register"
                      checked={register === option}
                      onChange={() => setRegister(option)}
                    />
                    {label}
                  </label>
                ))}
              </div>
            </div>

            <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginBottom: 34 }}>
              <a className="btn btn-primary" href="#demo" style={{ padding: "11px 20px" }}>
                {c.heroCtaDemo}
              </a>
              <a className="btn btn-secondary" href={REPO} style={{ padding: "11px 20px" }}>
                {c.heroCtaRepo}
              </a>
            </div>

            <div
              style={{
                height: 1,
                background:
                  "linear-gradient(to right, var(--color-divider), var(--color-divider) calc(100% - 48px), transparent)",
                marginBottom: 22,
              }}
            />
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
                gap: 18,
              }}
            >
              {[
                [c.featurePhoneTitle, c.featurePhoneBody],
                [c.featureBargeTitle, c.featureBargeBody],
                [c.featureQuoteTitle, c.featureQuoteBody],
              ].map(([title, body]) => (
                <div key={title}>
                  <div className="body-sm" style={{ fontWeight: 500, marginBottom: 3 }}>
                    {title}
                  </div>
                  <div className="caption" style={{ color: "var(--text-muted)" }}>
                    {body}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <DemoCard copy={c} lang={lang} />
        </div>
      </section>

      <section
        style={{
          background: "linear-gradient(120deg, var(--color-section), var(--color-section-glow))",
          padding: "clamp(30px, 4vw, 46px) var(--gutter)",
        }}
      >
        <div
          style={{
            maxWidth: "var(--container)",
            margin: "0 auto",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            gap: 26,
          }}
        >
          <Stat value={c.statAbandonValue} label={c.statAbandonLabel} lang={lang} />
          <Stat value={c.statVerticalsValue} label={c.statVerticalsLabel} lang={lang} />
          <Stat value={c.statHoursValue} label={c.statHoursLabel} lang={lang} />
          <Stat value={c.statTestsValue} label={c.statTestsLabel} lang={lang} />
        </div>
      </section>

      <section
        id="how"
        style={{ padding: "var(--section-pad)", scrollMarginTop: 80 }}
      >
        <div style={{ maxWidth: "var(--container)", margin: "0 auto" }}>
          <Kicker text={c.howKicker} />
          <h2 className="display-lg" style={{ margin: "0 0 12px", maxWidth: "22ch" }}>
            {c.howTitle}
          </h2>
          <p
            className="body"
            style={{ maxWidth: "56ch", color: "var(--text-secondary)", margin: "0 0 40px" }}
          >
            {c.howIntro}
          </p>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(212px, 1fr))",
              gap: 28,
            }}
          >
            <Step index="01" title={c.step1Title} body={c.step1Body} />
            <Step index="02" title={c.step2Title} body={c.step2Body} />
            <Step index="03" title={c.step3Title} body={c.step3Body} />
            <Step index="04" title={c.step4Title} body={c.step4Body} />
          </div>
        </div>
      </section>

      <section
        id="memory"
        style={{
          padding: "var(--section-pad)",
          scrollMarginTop: 80,
          borderTop: "1px solid var(--color-divider)",
        }}
      >
        <div
          style={{
            maxWidth: "var(--container)",
            margin: "0 auto",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
            gap: 28,
          }}
        >
          <Pillar title={c.memoryRetireTitle} body={c.memoryRetireBody} />
          <Pillar title={c.memoryGroundTitle} body={c.memoryGroundBody} />
          <Pillar title={c.memoryModesTitle} body={c.memoryModesBody} />
          <Pillar title={c.memoryPacksTitle} body={c.memoryPacksBody} />
        </div>
      </section>

      <section
        id="stack"
        style={{ padding: "var(--section-pad)", scrollMarginTop: 80 }}
      >
        <div style={{ maxWidth: "var(--container)", margin: "0 auto" }}>
          <Kicker text={c.stackKicker} />
          <h2 className="display-lg" style={{ margin: "0 0 32px", maxWidth: "26ch" }}>
            {c.stackTitle}
          </h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(184px, 1fr))",
              gap: 12,
            }}
          >
            <StackCard name="Twilio" body={c.stackTwilio} />
            <StackCard name="AssemblyAI" body={c.stackAssembly} focus />
            <StackCard name="Gemini Flash" body={c.stackGemini} />
            <StackCard name="ElevenLabs" body={c.stackEleven} />
            <StackCard name="Postgres · pgvector" body={c.stackPostgres} />
          </div>
          <div className="hr" style={{ margin: "34px 0 20px" }} />
          <p
            className="body-sm"
            style={{ margin: 0, color: "var(--text-muted)", maxWidth: "var(--measure)" }}
          >
            {c.stackLimits}
          </p>
        </div>
      </section>

      <section
        id="business"
        style={{
          padding: "var(--section-pad)",
          scrollMarginTop: 80,
          borderTop: "1px solid var(--color-divider)",
        }}
      >
        <div style={{ maxWidth: "var(--container)", margin: "0 auto" }}>
          <Kicker text={c.businessKicker} />
          <h2 className="display-lg" style={{ margin: "0 0 32px", maxWidth: "26ch" }}>
            {c.businessTitle}
          </h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
              gap: 28,
            }}
          >
            <Pillar title={c.businessWhoTitle} body={c.businessWhoBody} />
            <Pillar title={c.businessPriceTitle} body={c.businessPriceBody} />
            <Pillar title={c.businessCostTitle} body={c.businessCostBody} />
          </div>
        </div>
      </section>

      <section
        style={{
          padding: "var(--section-pad)",
          borderTop: "1px solid var(--color-divider)",
          position: "relative",
          overflow: "hidden",
        }}
      >
        <div
          className="glow"
          style={{
            bottom: -260,
            right: -140,
            width: 560,
            height: 560,
            background: "radial-gradient(circle, var(--orb-sky), transparent 70%)",
          }}
        />
        <div style={{ position: "relative", maxWidth: "var(--container)", margin: "0 auto" }}>
          <h2 className="display-lg" style={{ margin: "0 0 16px", maxWidth: "24ch" }}>
            {c.closingTitle}
          </h2>
          <p
            className="body"
            style={{ maxWidth: "50ch", color: "var(--text-secondary)", margin: "0 0 28px" }}
          >
            {c.closingBody}
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
            <a className="btn btn-primary" href="#demo" style={{ padding: "11px 20px" }}>
              {c.closingCtaDemo}
            </a>
            <a className="btn btn-secondary" href="/panel" style={{ padding: "11px 20px" }}>
              {c.closingCtaPanel}
            </a>
          </div>
        </div>
      </section>

      <footer
        className="body-sm"
        style={{
          padding: "var(--space-6) var(--gutter)",
          borderTop: "1px solid var(--color-divider)",
          display: "flex",
          flexWrap: "wrap",
          gap: 14,
          alignItems: "center",
          color: "var(--text-muted)",
        }}
      >
        <span>{c.footerLicense}</span>
        <span style={{ marginLeft: "auto" }}>{c.footerWarning}</span>
      </footer>
    </div>
  )
}

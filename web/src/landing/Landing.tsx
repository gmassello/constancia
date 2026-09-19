import DemoCard from "./DemoCard"
import { copy } from "./copy"
import { usePrefs, type Lang, type Register } from "../prefs"

const REPO = "https://github.com/gmassello/constancia"

const SUN = "M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10Zm0-14v2m0 18v-2M3 12h2m14 0h2M5.6 5.6l1.4 1.4m10 10 1.4 1.4m0-12.8-1.4 1.4m-10 10-1.4 1.4"
const MOON = "M21 13a9 9 0 1 1-10-10 7 7 0 0 0 10 10Z"

function Kicker({ text }: { text: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
      <span className="rule-mark" />
      <h6 style={{ margin: 0, fontSize: 11, color: "var(--text-accent)" }}>{text}</h6>
    </div>
  )
}

function Step({ index, title, body }: { index: string; title: string; body: string }) {
  return (
    <div className="step-column">
      <div
        style={{
          fontFamily: "var(--font-heading)",
          fontSize: 12,
          color: "var(--color-accent)",
          marginBottom: 14,
        }}
      >
        {index}
      </div>
      <h4 style={{ margin: "0 0 8px", fontSize: 18 }}>{title}</h4>
      <p style={{ margin: 0, fontSize: 13.5, lineHeight: 1.6, color: "var(--text-secondary)" }}>{body}</p>
    </div>
  )
}

function Pillar({ title, body }: { title: string; body: string }) {
  return (
    <div className="step-column">
      <h4 style={{ margin: "0 0 9px", fontSize: 19 }}>{title}</h4>
      <p style={{ margin: 0, fontSize: 13.5, lineHeight: 1.65, color: "var(--text-secondary)" }}>{body}</p>
    </div>
  )
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <div
        style={{
          fontFamily: "var(--font-heading)",
          fontSize: "clamp(30px, 3.4vw, 42px)",
          letterSpacing: "-0.02em",
          lineHeight: 1,
          color: "var(--section-ink)",
        }}
      >
        {value}
      </div>
      <div
        style={{
          fontSize: 12.5,
          marginTop: 6,
          color: "color-mix(in srgb, var(--section-ink) 80%, transparent)",
        }}
      >
        {label}
      </div>
    </div>
  )
}

function StackCard({ name, body, focus }: { name: string; body: string; focus?: boolean }) {
  return (
    <div className={focus ? "stack-card is-focus" : "stack-card"}>
      <div style={{ fontFamily: "var(--font-heading)", fontSize: 14.5, marginBottom: 5 }}>{name}</div>
      <div
        style={{
          fontSize: 11.5,
          lineHeight: 1.5,
          color: focus ? "var(--text-secondary)" : "var(--text-muted)",
        }}
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

  return (
    <div className="landing-shell">
      <header className="landing-header">
        <div style={{ display: "flex", alignItems: "center", gap: 9, marginRight: "auto" }}>
          <span
            className="noc-pulse"
            style={{
              width: 9,
              height: 9,
              borderRadius: "50%",
              background: "var(--color-accent)",
              boxShadow: "0 0 12px var(--color-accent)",
            }}
          />
          <span
            style={{
              fontFamily: "var(--font-heading)",
              fontWeight: 500,
              fontSize: 16,
              letterSpacing: "-0.01em",
            }}
          >
            constancia
          </span>
        </div>
        <nav className="landing-nav">
          <a href="#how">{c.navHow}</a>
          <a href="#memory">{c.navMemory}</a>
          <a href="#stack">{c.navStack}</a>
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
          aria-pressed={!dark}
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
          padding: "clamp(48px, 7vw, 96px) clamp(20px, 5vw, 64px) clamp(40px, 6vw, 80px)",
        }}
      >
        <div
          className="glow noc-breathe"
          style={{
            top: -180,
            left: -120,
            width: 620,
            height: 620,
            background:
              "radial-gradient(circle, color-mix(in srgb, var(--color-accent) 20%, transparent), transparent 68%)",
          }}
        />
        <div
          className="hero-grid"
          style={{
            position: "relative",
            maxWidth: 1180,
            margin: "0 auto",
            display: "grid",
            gridTemplateColumns: "minmax(0, 1.02fr) minmax(0, 1fr)",
            gap: "clamp(28px, 4vw, 56px)",
            alignItems: "start",
          }}
        >
          <div style={{ minWidth: 0 }}>
            <Kicker text={c.heroKicker} />
            <h1
              style={{
                fontSize: "clamp(38px, 5.4vw, 66px)",
                lineHeight: 1.04,
                letterSpacing: "-0.03em",
                margin: "0 0 20px",
                textWrap: "pretty",
              }}
            >
              {c.heroTitleTop}
              <br />
              {c.heroTitleBottom}
            </h1>
            <p
              style={{
                fontSize: "clamp(16px, 1.5vw, 19px)",
                lineHeight: 1.6,
                maxWidth: "46ch",
                color: "var(--text-secondary)",
                margin: "0 0 14px",
              }}
            >
              {c.heroBodyProblem}
            </p>
            <p
              style={{
                fontSize: "clamp(16px, 1.5vw, 19px)",
                lineHeight: 1.6,
                maxWidth: "46ch",
                color: "var(--text-secondary)",
                margin: "0 0 20px",
              }}
            >
              {c.heroBodyProduct}
            </p>

            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 28 }}>
              <span style={{ fontSize: 12, color: "var(--text-muted)" }}>{c.registerLabel}</span>
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
              <a className="btn btn-primary" href="#demo" style={{ fontSize: 15, padding: "11px 20px" }}>
                {c.heroCtaDemo}
              </a>
              <a className="btn btn-secondary" href={REPO} style={{ fontSize: 15, padding: "11px 20px" }}>
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
                  <div style={{ fontFamily: "var(--font-heading)", fontSize: 15, marginBottom: 3 }}>
                    {title}
                  </div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{body}</div>
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
          padding: "clamp(30px, 4vw, 46px) clamp(20px, 5vw, 64px)",
        }}
      >
        <div
          style={{
            maxWidth: 1180,
            margin: "0 auto",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            gap: 26,
          }}
        >
          <Stat value={c.statAbandonValue} label={c.statAbandonLabel} />
          <Stat value={c.statVerticalsValue} label={c.statVerticalsLabel} />
          <Stat value={c.statHoursValue} label={c.statHoursLabel} />
          <Stat value={c.statTestsValue} label={c.statTestsLabel} />
        </div>
      </section>

      <section
        id="how"
        style={{ padding: "clamp(56px, 7vw, 96px) clamp(20px, 5vw, 64px)", scrollMarginTop: 80 }}
      >
        <div style={{ maxWidth: 1180, margin: "0 auto" }}>
          <Kicker text={c.howKicker} />
          <h2
            style={{
              fontSize: "clamp(28px, 3.4vw, 42px)",
              letterSpacing: "-0.025em",
              margin: "0 0 12px",
              maxWidth: "22ch",
            }}
          >
            {c.howTitle}
          </h2>
          <p
            style={{
              maxWidth: "56ch",
              fontSize: 15.5,
              color: "var(--text-secondary)",
              margin: "0 0 40px",
            }}
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
          padding: "clamp(48px, 6vw, 86px) clamp(20px, 5vw, 64px)",
          scrollMarginTop: 80,
          borderTop: "1px solid var(--color-divider)",
        }}
      >
        <div
          style={{
            maxWidth: 1180,
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
        style={{ padding: "clamp(48px, 6vw, 86px) clamp(20px, 5vw, 64px)", scrollMarginTop: 80 }}
      >
        <div style={{ maxWidth: 1180, margin: "0 auto" }}>
          <Kicker text={c.stackKicker} />
          <h2
            style={{
              fontSize: "clamp(26px, 3vw, 36px)",
              letterSpacing: "-0.025em",
              margin: "0 0 32px",
              maxWidth: "26ch",
            }}
          >
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
          <p style={{ margin: 0, fontSize: 13, color: "var(--text-muted)", maxWidth: "70ch" }}>
            {c.stackLimits}
          </p>
        </div>
      </section>

      <section
        style={{
          padding: "clamp(56px, 7vw, 100px) clamp(20px, 5vw, 64px) clamp(64px, 8vw, 110px)",
          borderTop: "1px solid var(--color-divider)",
          position: "relative",
          overflow: "hidden",
        }}
      >
        <div
          className="glow noc-breathe"
          style={{
            bottom: -260,
            right: -140,
            width: 560,
            height: 560,
            background:
              "radial-gradient(circle, color-mix(in srgb, var(--color-accent) 16%, transparent), transparent 70%)",
            animationDuration: "11s",
          }}
        />
        <div style={{ position: "relative", maxWidth: 1180, margin: "0 auto" }}>
          <h2
            style={{
              fontSize: "clamp(30px, 4vw, 50px)",
              letterSpacing: "-0.03em",
              lineHeight: 1.06,
              margin: "0 0 16px",
              maxWidth: "24ch",
            }}
          >
            {c.closingTitle}
          </h2>
          <p
            style={{
              maxWidth: "50ch",
              fontSize: 16,
              lineHeight: 1.6,
              color: "var(--text-secondary)",
              margin: "0 0 28px",
            }}
          >
            {c.closingBody}
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
            <a className="btn btn-primary" href="#demo" style={{ fontSize: 15, padding: "11px 20px" }}>
              {c.closingCtaDemo}
            </a>
            <a className="btn btn-secondary" href="/panel" style={{ fontSize: 15, padding: "11px 20px" }}>
              {c.closingCtaPanel}
            </a>
          </div>
        </div>
      </section>

      <footer
        style={{
          padding: "20px clamp(20px, 5vw, 64px)",
          borderTop: "1px solid var(--color-divider)",
          display: "flex",
          flexWrap: "wrap",
          gap: 14,
          alignItems: "center",
          fontSize: 11.5,
          color: "var(--text-muted)",
        }}
      >
        <span>{c.footerLicense}</span>
        <span style={{ marginLeft: "auto" }}>{c.footerWarning}</span>
      </footer>
    </div>
  )
}

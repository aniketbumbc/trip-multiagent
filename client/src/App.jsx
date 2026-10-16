import { useEffect, useState } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { checkHealth, planTrip } from "./api.js"
import { formatAgentText } from "./formatAnswer.js"

const PROMPTS = [
  {
    label: "Kyoto, slowly",
    query: "Plan 6 days in Kyoto from Mumbai. Mid-range hotels, food first, and not too many temple hops in one day.",
  },
  {
    label: "Lisbon weekend",
    query: "Long weekend in Lisbon from Delhi. Walkable neighborhoods, one sunset viewpoint, and a practical budget.",
  },
  {
    label: "New York in winter",
    query: "5 days in New York from Mumbai in December. One splurge dinner, easy transit, and a clear daily plan.",
  },
]

const STEPS = [
  { label: "Flights", detail: "Checking the route" },
  { label: "Hotels", detail: "Reading stay notes" },
  { label: "Days", detail: "Laying out the trip" },
  { label: "Write-up", detail: "Putting it in one piece" },
]

const PANELS = [
  { id: "answer", label: "The plan" },
  { id: "flights", label: "Flights" },
  { id: "hotels", label: "Hotels" },
  { id: "itinerary", label: "Day by day" },
]

function isThin(text) {
  const value = (text || "").toLowerCase()
  return value.includes("failed") || value.includes("could not") || value.includes("not available")
}

export default function App() {
  const [query, setQuery] = useState("")
  const [threadId, setThreadId] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const [online, setOnline] = useState(null)
  const [step, setStep] = useState(0)
  const [panel, setPanel] = useState("answer")

  useEffect(() => {
    let cancelled = false
    checkHealth()
      .then(() => {
        if (!cancelled) setOnline(true)
      })
      .catch(() => {
        if (!cancelled) setOnline(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!loading) return undefined
    const timer = setInterval(() => {
      setStep((current) => (current + 1) % STEPS.length)
    }, 2200)
    return () => clearInterval(timer)
  }, [loading])

  async function submitTrip(event) {
    event.preventDefault()
    const userQuery = query.trim()
    if (!userQuery || loading) return

    setLoading(true)
    setError("")
    setStep(0)
    setPanel("answer")

    try {
      const data = await planTrip(userQuery, threadId)
      setResult({ ...data, userQuery })
      setThreadId(data.thread_id)
      setOnline(true)
    } catch (err) {
      setError(err.message || "The planner could not finish this trip.")
      if (err instanceof TypeError) setOnline(false)
    } finally {
      setLoading(false)
    }
  }

  function startOver() {
    setThreadId(null)
    setResult(null)
    setError("")
    setQuery("")
    setPanel("answer")
  }

  const panelText = {
    answer: result?.answer,
    flights: result?.flight_results,
    hotels: result?.hotel_results,
    itinerary: result?.itinerary,
  }[panel]

  return (
    <main className="relative mx-auto min-h-screen max-w-6xl px-5 py-6 sm:px-8 sm:py-8">
      <header className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-full border border-ink/15 bg-cream font-display text-lg text-clay">
            T
          </span>
          <div>
            <p className="font-display text-xl leading-none">TripMate</p>
            <p className="mt-1 text-xs tracking-[0.16em] text-ink/55 uppercase">Four agents, one trip</p>
          </div>
        </div>
        <p className="flex items-center gap-2 text-sm text-ink/70">
          <span className={`h-2 w-2 rounded-full ${online ? "bg-moss" : online === false ? "bg-clay" : "bg-gold"}`} />
          {online ? "Planner is up" : online === false ? "Planner is offline" : "Checking planner"}
        </p>
      </header>

      <section className="mt-10 grid items-end gap-8 lg:grid-cols-[1.15fr_0.85fr]">
        <div>
          <p className="text-sm font-medium tracking-[0.18em] text-sea uppercase">A small crew for the whole trip</p>
          <h1 className="mt-3 max-w-xl font-display text-5xl leading-[0.95] text-ink sm:text-6xl">
            Tell us where. We’ll sort the rest.
          </h1>
          <p className="mt-5 max-w-lg text-lg leading-relaxed text-ink/75">
            Flights, a place to sleep, the shape of the days, then one write-up you can actually follow.
          </p>
        </div>
        <ol className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-2">
          {STEPS.map((item, index) => (
            <li key={item.label} className="rounded-2xl border border-ink/10 bg-cream/80 px-4 py-3">
              <p className="font-display text-2xl text-clay">0{index + 1}</p>
              <p className="mt-1 font-medium">{item.label}</p>
              <p className="text-sm text-ink/60">{item.detail}</p>
            </li>
          ))}
        </ol>
      </section>

      <form onSubmit={submitTrip} className="mt-8 rounded-[28px] border border-ink/10 bg-cream p-4 shadow-[0_20px_50px_rgba(28,23,18,0.06)] sm:p-5">
        <label htmlFor="trip" className="px-1 text-sm font-medium text-ink/70">
          The trip, in one breath
        </label>
        <textarea
          id="trip"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          rows={4}
          placeholder="7 days in Kyoto from Mumbai, mid-range, with time left over to get lost."
          className="mt-2 w-full resize-none bg-transparent px-1 text-lg leading-relaxed text-ink outline-none placeholder:text-ink/35"
        />
        <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap gap-2">
            {PROMPTS.map((prompt) => (
              <button
                key={prompt.label}
                type="button"
                onClick={() => setQuery(prompt.query)}
                className="rounded-full border border-ink/10 bg-paper px-3 py-1.5 text-sm text-ink/80 transition hover:border-clay/40 hover:text-ink"
              >
                {prompt.label}
              </button>
            ))}
          </div>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="rounded-full bg-clay px-5 py-2.5 text-sm font-semibold text-cream transition hover:bg-[#a33e20] disabled:cursor-not-allowed disabled:bg-sand disabled:text-ink/40"
          >
            {loading ? "The crew is out…" : threadId ? "Continue this trip" : "Plan this trip"}
          </button>
        </div>
        {threadId && (
          <div className="mt-3 flex items-center justify-between gap-3 px-1 text-sm text-ink/60">
            <p>Continuing thread {threadId.slice(0, 14)}</p>
            <button type="button" onClick={startOver} className="underline decoration-ink/30 underline-offset-4">
              Start a new trip
            </button>
          </div>
        )}
      </form>

      {loading && (
        <section className="mt-6 rounded-[28px] border border-ink/10 bg-sea px-5 py-6 text-cream">
          <p className="text-sm tracking-[0.16em] text-cream/70 uppercase">On the road</p>
          <div className="mt-4 grid gap-3 sm:grid-cols-4">
            {STEPS.map((item, index) => {
              const active = index === step
              const done = index < step
              return (
                <div key={item.label} className="relative flex items-center gap-3">
                  <span className={`relative grid h-8 w-8 place-items-center rounded-full text-sm ${active ? "step-live bg-clay text-cream" : done ? "bg-gold text-ink" : "bg-cream/15 text-cream/80"}`}>
                    {index + 1}
                  </span>
                  <div>
                    <p className="font-medium">{item.label}</p>
                    <p className="text-sm text-cream/65">{active ? item.detail : done ? "Done" : "Waiting"}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      )}

      {error && (
        <p className="mt-6 rounded-2xl border border-clay/30 bg-[#fde8df] px-4 py-3 text-[#8a3418]">
          {error} Start the API with <span className="font-medium">python app.py</span> in the server folder, then try again.
        </p>
      )}

      {result && !loading && (
        <section className="mt-8">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-sm tracking-[0.16em] text-sea uppercase">Field notes</p>
              <h2 className="mt-1 max-w-2xl font-display text-3xl leading-tight">{result.userQuery}</h2>
            </div>
            <p className="text-sm text-ink/55">{result.llm_calls || 0} model calls</p>
          </div>

          <div className="mt-5 flex gap-2 overflow-x-auto">
            {PANELS.map((item) => {
              const text = {
                answer: result.answer,
                flights: result.flight_results,
                hotels: result.hotel_results,
                itinerary: result.itinerary,
              }[item.id]
              const thin = item.id !== "answer" && isThin(text)
              const selected = panel === item.id
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setPanel(item.id)}
                  className={`shrink-0 rounded-full px-4 py-2 text-sm font-medium transition ${selected ? "bg-ink text-cream" : "bg-cream text-ink/75 hover:bg-sand"}`}
                >
                  {item.label}
                  {thin ? " · partial" : ""}
                </button>
              )
            })}
          </div>

          <article className="prose prose-trip mt-4 max-w-none rounded-[28px] border border-ink/10 bg-cream px-5 py-6 sm:px-8">
            {panelText?.trim() ? (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  table: ({ children }) => (
                    <div className="not-prose overflow-x-auto">
                      <table className="w-full border-collapse text-sm">{children}</table>
                    </div>
                  ),
                  th: ({ children, node, ...props }) => (
                    <th className="border-b border-ink/15 bg-paper px-3 py-2 text-left font-medium" {...props}>{children}</th>
                  ),
                  td: ({ children, node, ...props }) => (
                    <td className="border-b border-ink/10 px-3 py-2 align-top" {...props}>{children}</td>
                  ),
                }}
              >
                {formatAgentText(panelText)}
              </ReactMarkdown>
            ) : (
              <p className="text-ink/60">Nothing came back for this part. The other notes may still be useful.</p>
            )}
          </article>
        </section>
      )}
    </main>
  )
}

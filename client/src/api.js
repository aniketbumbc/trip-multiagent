export async function checkHealth() {
  const response = await fetch("/api/health")
  if (!response.ok) {
    throw new Error("Planner is offline")
  }
  return response.json()
}

function readSseBlock(block) {
  let event = "message"
  const dataLines = []
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim()
    if (line.startsWith("data:")) dataLines.push(line.slice(5).trim())
  }
  if (!dataLines.length) return null
  return { event, data: JSON.parse(dataLines.join("\n")) }
}

export async function planTripStream(userQuery, threadId, onStep) {
  const response = await fetch("/api/travel/stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({
      user_query: userQuery,
      thread_id: threadId,
    }),
  })

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    const detail = Array.isArray(data.detail) ? data.detail[0]?.msg : data.detail
    throw new Error(data.error || detail || "The planner could not start this trip.")
  }
  if (!response.body) {
    throw new Error("The planner did not stream any progress.")
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  let result = null

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const blocks = buffer.split("\n\n")
    buffer = blocks.pop() || ""
    for (const block of blocks) {
      const message = readSseBlock(block)
      if (!message) continue
      if (message.event === "step") onStep(message.data)
      if (message.event === "result") result = message.data
      if (message.event === "error") {
        throw new Error(message.data.error || "The planner could not finish this trip.")
      }
    }
  }

  if (!result) {
    throw new Error("The planner ended without a result.")
  }
  return result
}

export async function planTrip(userQuery, threadId) {
  const response = await fetch("/api/travel", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_query: userQuery,
      thread_id: threadId,
    }),
  })

  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = Array.isArray(data.detail) ? data.detail[0]?.msg : data.detail
    throw new Error(data.error || detail || "The planner could not finish this trip.")
  }
  return data
}

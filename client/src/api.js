export async function checkHealth() {
  const response = await fetch("/api/health")
  if (!response.ok) {
    throw new Error("Planner is offline")
  }
  return response.json()
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

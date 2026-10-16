function isCollapsedTable(line) {
  return line.includes("| |") && /-{3,}/.test(line) && (line.match(/\|/g) || []).length >= 4
}

function expandTable(line) {
  const start = line.indexOf("|")
  const prefix = line.slice(0, start).trimEnd()
  const rows = line
    .slice(start)
    .split("| |")
    .map((part) => {
      let row = part.trim()
      if (!row.startsWith("|")) row = `| ${row}`
      if (!row.endsWith("|")) row = `${row} |`
      return row
    })

  const markdown = rows.join("\n")
  return prefix ? `${prefix}\n\n${markdown}` : markdown
}

const ISO_TIME = /\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})/g

const clock = new Intl.DateTimeFormat(undefined, {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "numeric",
  minute: "2-digit",
  timeZoneName: "short",
})

export function formatClockTime(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return clock.format(date)
}

function formatTimes(text) {
  return text.replace(ISO_TIME, (value) => formatClockTime(value))
}

export function formatAgentText(text) {
  if (!text) return ""
  return formatTimes(text)
    .split("\n")
    .map((line) => (isCollapsedTable(line) ? expandTable(line) : line))
    .join("\n")
}

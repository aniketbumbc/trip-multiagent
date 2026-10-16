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

export function formatAgentText(text) {
  if (!text) return ""
  return text
    .split("\n")
    .map((line) => (isCollapsedTable(line) ? expandTable(line) : line))
    .join("\n")
}

export function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

export function groupRecords(items) {
  if (!Array.isArray(items)) return []
  const map = new Map()
  for (const it of items) {
    const name = ((it.group_name || '') + '').trim() || '未分组'
    if (!map.has(name)) map.set(name, [])
    map.get(name).push(it)
  }
  const named = [...map.keys()]
    .filter((n) => n !== '未分组')
    .sort((a, b) => a.localeCompare(b))
  const result = named.map((name) => ({ name, records: map.get(name) }))
  if (map.has('未分组')) result.push({ name: '未分组', records: map.get('未分组') })
  return result
}

export function todayStr() {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

export function issueLabel(item) {
  if (!item) return ''
  return item.draw_date ? `${item.issue}期 ${item.draw_date}` : `${item.issue}期`
}

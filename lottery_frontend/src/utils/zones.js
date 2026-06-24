const KEY_LABELS = { red: '红球', blue: '蓝球', main: '号码' }
const KEY_COLORS = { red: '#e53935', blue: '#1e88e5', main: '#fb8c00' }

export function getZones(ruleConfig) {
  if (!ruleConfig) return []
  if (Array.isArray(ruleConfig.zones)) return ruleConfig.zones
  const zones = []
  for (const key of ['red', 'blue']) {
    const r = ruleConfig[key]
    if (!r) continue
    zones.push({ key, label: KEY_LABELS[key], color: KEY_COLORS[key], ...r })
  }
  return zones
}

export function zoneLabel(key) {
  return KEY_LABELS[key] || key
}

export function zoneColor(key) {
  return KEY_COLORS[key] || '#9e9e9e'
}

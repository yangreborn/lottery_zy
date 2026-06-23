import { request } from './request.js'

export function getGuideList(code, type) {
  const data = {}
  if (code) data.code = code
  if (type) data.type = type
  return request('/api/openapi/guide/list', { data })
}

export function getGuideDetail(id) {
  return request('/api/openapi/guide/detail', { data: { id } })
}

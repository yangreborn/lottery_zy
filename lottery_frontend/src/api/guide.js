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

// 通知列表：后端按「重点在前 → 发布时间倒序」排序。首页横幅取第一条即
// 「有重点显示重点，否则显示最新」。
export function getNotices(code) {
  const data = { type: 'activity,notice' }
  if (code) data.code = code
  return request('/api/openapi/guide/list', { data })
}

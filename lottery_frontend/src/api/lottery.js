import { request } from './request.js'

export function getLotteryList() {
  return request('/api/openapi/lottery/list')
}

export function getLatest(code) {
  return request('/api/openapi/draw/latest', { data: { code } })
}

export function getHistory(code, params = {}) {
  return request('/api/openapi/draw/history', { data: { code, ...params } })
}

export function getDetail(code, issue) {
  return request('/api/openapi/draw/detail', { data: { code, issue } })
}

export function getStats(code, periods) {
  return request('/api/openapi/draw/stats', { data: { code, periods } })
}

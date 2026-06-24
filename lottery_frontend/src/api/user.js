import { request } from './request.js'
import { authState, setToken } from '../store/auth.js'
import { getOrCreateDeviceCode } from '../utils/device.js'

export function login(code) {
  return request('/api/user/login', { method: 'POST', data: { code } })
}

export function createNumber(payload) {
  return request('/api/user/number/create', { method: 'POST', data: payload })
}

export function listNumbers(code) {
  return request('/api/user/number/list', { data: code ? { code } : {} })
}

export function deleteNumber(id) {
  return request(`/api/user/number/${id}`, { method: 'DELETE' })
}

export function checkNumber(id) {
  return request('/api/user/number/check', { data: { id } })
}

export async function ensureLogin() {
  if (authState.token) return authState.token
  const code = getOrCreateDeviceCode()
  const res = await login(code)
  setToken(res.token)
  return res.token
}

export function generateNumbers(code, count) {
  return request('/api/user/number/generate', { method: 'POST', data: { code, count } })
}

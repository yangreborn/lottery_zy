import { request } from './request.js'
import { authState, setToken } from '../store/auth.js'
import { getOrCreateDeviceCode } from '../utils/device.js'

export function login(code) {
  return request('/api/user/login', { method: 'POST', data: { code } })
}

export function wechatLogin(code) {
  return request('/api/user/login/wechat', { method: 'POST', data: { code } })
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

export function generateNumbers(code, count, picks) {
  return request('/api/user/number/generate', { method: 'POST', data: { code, count, picks } })
}

export function setGroup(id, group_name) {
  return request('/api/user/number/group', { method: 'POST', data: { id, group_name } })
}

export function submitFeedback({ content, contact }) {
  return request('/api/user/feedback', { method: 'POST', data: { content, contact } })
}

export function batchDelete(ids) {
  return request('/api/user/number/batch_delete', { method: 'POST', data: { ids } })
}

export function batchGroup(ids, group_name) {
  return request('/api/user/number/batch_group', { method: 'POST', data: { ids, group_name } })
}

export function purchaseCreate(payload) {
  return request('/api/user/purchase/create', { method: 'POST', data: payload })
}

export function purchaseList(code) {
  return request('/api/user/purchase/list', { data: code ? { code } : {} })
}

export function purchaseDelete(id) {
  return request(`/api/user/purchase/${id}`, { method: 'DELETE' })
}

export function getProfile() {
  return request('/api/user/profile')
}

export function setProfile(nickname) {
  return request('/api/user/profile', { method: 'POST', data: { nickname } })
}

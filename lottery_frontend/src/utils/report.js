import { request } from '../api/request.js'

export function reportAccess(path, opts = {}) {
  return request('/api/openapi/log', {
    method: 'POST',
    data: {
      path,
      lottery_code: opts.lottery_code || '',
      action: opts.action || 'view',
    },
  }).catch(() => {})
}

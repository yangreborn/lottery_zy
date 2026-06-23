const BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

export function request(path, { method = 'GET', data } = {}) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE + path,
      method,
      data,
      success: (res) => {
        if (res.statusCode !== 200) {
          reject({ code: -1, msg: `HTTP ${res.statusCode}` })
          return
        }
        const body = res.data || {}
        if (body.code === 0) {
          resolve(body.data)
        } else {
          reject({ code: body.code, msg: body.msg || '请求失败' })
        }
      },
      fail: (err) => reject({ code: -1, msg: (err && err.errMsg) || '网络错误' }),
    })
  })
}

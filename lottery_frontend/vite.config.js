import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'
// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    uni(),
  ],
  // 绑所有接口(含 IPv4)避免默认 IPv6-only 导致 127.0.0.1 连不上;
  // 用非默认端口 5199 避开常被占用的 5173
  server: {
    host: true,
    port: 5199,
  },
})

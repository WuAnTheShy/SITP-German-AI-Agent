// 文件: frontend/vite.config.js
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // 加载 .env.[mode] 文件中的环境变量
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react()],
    // 使用相对路径 './'。
    // 因为使用了 HashRouter，能自动适应任何仓库名或子路径。
    base: './',
    server: {
      proxy: {
        // 开发模式下，将所有 /api 请求代理到后端
        // 默认代理到 localhost:8000，可在 .env.development 或
        // .env.development.local 中修改 VITE_DEV_PROXY_TARGET
        '/api': {
          target: env.VITE_DEV_PROXY_TARGET || 'http://localhost:8000',
          changeOrigin: true,
        }
      }
    }
  }
})

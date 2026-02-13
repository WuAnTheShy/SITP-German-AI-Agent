import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // 核心修改：只有当环境变量 GITHUB_PAGES 为 'true' 时，才使用仓库名作为路径
  // 这样 Docker 即使是 Production 模式，也会用 '/'，保证本地运行正常
  base: process.env.GITHUB_PAGES === 'true' ? '/SITP-German-AI-Agent/' : '/',
})
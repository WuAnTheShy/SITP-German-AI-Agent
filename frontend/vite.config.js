// 文件: frontend/vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // [修改] 使用相对路径 './'。
  // 因为你使用了 HashRouter，这能自动适应任何仓库名或子路径，
  // 避免因仓库名称大小写不一致导致的 404 问题。
  base: './',
})
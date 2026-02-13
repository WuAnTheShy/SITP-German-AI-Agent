# Dockerfile (位于根目录)

# --- 阶段 1: 构建 (Build) ---
FROM node:20-alpine as build-stage

# 设置工作目录
WORKDIR /app

# 先复制 package.json 安装依赖，利用缓存加速
COPY package*.json ./
RUN npm install

# 复制源代码并打包
COPY . .
RUN npm run build

# --- 阶段 2: 运行 (Run) ---
FROM nginx:alpine as production-stage

# 把刚才打包好的文件 (dist目录) 复制到 Nginx 目录
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 复制我们自定义的 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露 80 端口
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
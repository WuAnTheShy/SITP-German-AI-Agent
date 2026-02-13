# server/Dockerfile

# 使用 Python 3.13 作为基础镜像
FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖 (不使用缓存，减小体积)
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端所有代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
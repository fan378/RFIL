# EMR

## 前端

### 安装依赖
```bash
pnpm install
```

### 启动开发环境
```bash
pnpm dev
```

## 后端

### 启动后端服务
```bash
python manage.py runserver 0.0.0.0:8047 --noreload
```

## 注意事项

1. **在93服务器上启动后端**
   - 注意模型的加载地址和后端的最终启动端口
   - 启动命令：
     ```bash
     python manage.py runserver 0.0.0.0:8047
     ```

2. **访问容器服务**
   - 找到93服务器的 `user_scripts/` 目录
   - 访问容器服务并从校园网访问 `.ipynb` 文件
   - 修改端口为 `8047`，然后运行

3. **配置本地前端**
   - 将本地前端的 `.env.test` 文件修改为：
     ```
     http://172.20.137.216:8047
     ```
   - 然后运行前端开发环境
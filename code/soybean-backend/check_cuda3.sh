#!/bin/bash

while true; do
    # 检查容器是否已经运行
    if docker ps --format '{{.Names}}' | grep -q '^soybean$'; then
        echo "Docker container 'soybean' is already running. Exiting loop."
        exit 0
    fi

    # 获取 GPU 3 的当前使用情况
    GPU_ID=3
    USAGE=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | sed -n "$((GPU_ID+1))p")

    # 设置空闲的阈值 (例如 GPU 使用率低于 10% 认为空闲)
    THRESHOLD=10

    if [ "$USAGE" -lt "$THRESHOLD" ]; then
        echo "GPU $GPU_ID is idle, starting Docker container..."
        docker run --restart always --gpus all -it -d -p 8000:8000 --name soybean myproject python manage.py runserver --noreload 0.0.0.0:8000        # docker restart soybean
        exit 0  # 容器启动后退出循环
    else
        echo "GPU $GPU_ID is busy (Usage: $USAGE%)"
    fi

    # 等待 60 秒后再次检查
    sleep 60
done
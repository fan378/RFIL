# 复制文件
docker cp /home/yuancheng/soybean-backend/soybeanBackend/views.py soybean:/code/soybeanBackend/views.py
docker cp /home/yuancheng/soybean-backend/codes/commons/frontend_constants.py soybean:/code/codes/commons/frontend_constants.py
docker cp /home/yuancheng/soybean-backend/soybeanBackend/views.py soybean1:/code/soybeanBackend/views.py
docker cp /home/yuancheng/soybean-backend/static/assets soybean:/code/static/assets
docker cp /data/yuancheng/yc/ruijin_model/0229_ck36000_sft_stage4_lora_03-27-09-27-27_export_model soybean:/code/ruijin_model

# 构建 Docker 镜像
docker build -t myproject .

# 运行 Docker 镜像
docker run --restart always --gpus all -it -d -p 8000:8000 --name soybean myproject python manage.py runserver --noreload 0.0.0.0:8000
docker run --gpus all -it -p 8001:8001 --name soybean1 myproject bash
docker run --gpus all -it -p 8002:8002 --name soybean2 myproject bash

# 运行时挂载路径：
docker run -d --name soybean -v /home/yuancheng/soybean-backend:/code myproject python manage.py runserver --noreload  0.0.0.0:8000


# 启动容器
docker start -ai soybean

# 重启
docker restart soybean

# 进入容器
docker exec -it soybean /bin/bash
docker exec -it soybean1 /bin/bash

# 更新镜像
docker commit soybean1 myproject:latest

# 查看报错
docker logs soybean

# 退出
exit

# 删除容器
docker stop soybean
docker rm soybean

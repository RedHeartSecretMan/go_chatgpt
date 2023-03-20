# 基础镜像
FROM python:3.8

# 设置工作目录
WORKDIR /app

# 将文件复制到容器中
COPY chatgpter ./chatgpter
COPY requirements.txt .

# 安装依赖库
RUN pip install --no-cache-dir -r requirements.txt

# 告知守护进程暴露的端口号
EXPOSE 7860
EXPOSE 7890

# 设置系统的环境变量参数
ENV api_key="please_run_docker_set_your_api_key"
ENV model="gpt-3.5-turbo"
ENV model_trend="general"
ENV request_method="post"
ENV server_name="0.0.0.0" 
ENV server_port=7860
ENV proxy_name="192.168.1.7" 
ENV proxy_port=7890 
ENV share=False
ENV debug=False

# 安装启动脚本
RUN echo "#!/bin/bash" > ./start.sh && \
    echo "python -m chatgpter -ak \${api_key} -m \${model} -mt \${model_trend} -rm \${request_method} -sn \${server_name} -sp \${server_port} -pn \${proxy_name} -pp \${proxy_port} -s \${share} -d \${debug}" >> ./start.sh && \
    chmod +x ./start.sh

# 设置启动命令
CMD ["bash", "-c", "echo 'App include the following file:'; ls; echo '\nCreating the server'; ./start.sh"]

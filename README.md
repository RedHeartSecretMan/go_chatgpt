# Go ChatGPT


## Quick start
***「go_chatgpt」* 是一个快速调用 openai chatgpt api 的网页封装**

> ***「go_subtitle」 is a quick call to openai chatgpt api web page encapsulation***

<img src="./assets/chat.jpg" alt="chat" width="800;" />

<img src="./assets/ask.jpg" alt="ask" width="800;" />



### Setup

**项目需要运行在包含 *[python3.8.16](https://www.python.org/downloads/release/python-3816/)* 的环境中**

> ***The project needs runs in an environment containing [python3.8.16](https://www.python.org/downloads/release/python-3816/)***

**建议通过 *[miniconda](https://docs.conda.io/en/latest/miniconda.html)* 安装 *python* 以便管理环境**

> **It is recommended to install python through *[miniconda](https://docs.conda.io/en/latest/miniconda.html)* to manage the environment**

```shell
conda create -n chatgpt python=3.8 
```

**你可以通过下面的命令安装此项目最新的版本**

> ***You can install the project latest version using the following command***

```shell
# 从PyPI安装
pip install -U go_chatgpt

# 从GitHub安装
pip install git+https://github.com/RedHeartSecretMan/go_chatgpt.git
```

**你需要创建 *OpenAI* 账号获取 *api-key* 以使用**
> ***You need to create an OpenAI account to get the api-key to use***

**项目中的 *deploy* 文件夹包含了在 *Linux、macOS* 和 *Windows* 平台上的快速部署脚本**
> ***The deploy folder in the project contains rapid deployment script for the Linux, macOS and Windows platforms***

### Docker
**你可以通过以下命令获取 *docker* 镜像**
> ***You can obtain the docker image with the following command***
```shell
docker pull 1046911101/go_chatgpt:latest 
```

**你需要为该镜像创建一个容器并启动，常用的参数都被设置成了环境变量，可根据需要调整**

> ***You need to create a container for the image and start it and the usual parameters are set to environment variables and adjusted as needed***
```shell
docker run -e api_key="write_yourself_api_key_from_openai.com" -e request_method="official" --name go_chatgpt_0319 -p 7860:7860 -it 1046911101/go_chatgpt:latest
```
> **Tips：默认的服务器地址设置为 *0.0.0.0*， 默认的请求方法设置为 *post*，默认设置为流式传输数据，默认的密钥设置为 *write_yourself_api_key_from_openai.com* 应用一串类似 *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* 的代码替换**

**如果网路无法访问则需要为容器设置代理，建议使用宿主机的代理服务器**

> ***If the network is inaccessible, you need to set up a proxy for the container. You can use the proxy service of the host***
```shell
docker run -e api_key="write_yourself_api_key_from_openai.com" -e proxy_name="192.168.1.7" -e proxy_port=7890 --name go_chatgpt_0319 -p 7860:7860 -it 1046911101/go_chatgpt:latest
```
> **Tips:：其中 *192.168.1.7* 是局域网中网关分配给宿主机的 *IP* 地址，*7890* 是宿主机被代理的端口，因为容器默认使用 *Bridge* 网络模式，因此只需在宿主机的代理服务器上开启允许局域网连接，容器即可通过局域网使用宿主机的代理服务器**

### End

**项目现在是一个可用的*demo*，计划在*23*年*6*月份左右完善**

> ***The project is now an available demo, which is planned to be completed around June in 23***

<div align="center"><img src="./assets/avatar.jpeg" width="100" height="100" /></div>
<div align="center"><font face="楷体" size="3">作者 昊大侠</font></div>


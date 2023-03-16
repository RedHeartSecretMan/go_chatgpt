#!/bin/bash

# 定义 Miniconda 版本号和要安装的包
minicondaVersion="Miniconda3-latest-Linux-x86_64.sh"
packages=("go_chatgpt")

# 下载 Miniconda 安装程序
wget "https://repo.anaconda.com/miniconda/$minicondaVersion" -O "/tmp/$minicondaVersion"

# 安装 Miniconda
bash "/tmp/$minicondaVersion" -b -p "$HOME/miniconda"

# 更新 conda
"$HOME/miniconda/bin/conda" update -y conda

# 安装包
for package in "${packages[@]}"
do
    "$HOME/miniconda/bin/conda" install -y "$package"
done


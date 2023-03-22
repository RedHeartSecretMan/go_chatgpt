# 定义 Miniconda 版本号和要安装的包
$minicondaVersion = "Miniconda3-latest-Windows-x86_64.exe"
$packages = "go_chatgpt"

# 下载 Miniconda 安装程序
Invoke-WebRequest -Uri "https://repo.anaconda.com/miniconda/$minicondaVersion" -OutFile "$env:TEMP\$minicondaVersion"

# 安装 Miniconda
& "$env:TEMP\$minicondaVersion" /InstallationType=JustMe /RegisterPython=0 /S /D=C:\Miniconda3

# 更新 conda
conda update -y conda

# 更新 pip
python -m pip install --upgrade pip

# 安装包
foreach ($package in $packages) {
    python -m pip install $package
}

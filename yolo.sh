#!/bin/bash

# 初始化 conda（根据你的安装路径）
source /home/xuan/anaconda3/etc/profile.d/conda.sh

# 激活指定的 conda 环境
conda activate yolo_printer

# 进入项目目录
cd /home/xuan/008

# 执行 Python 脚本
python yolo_nebulizer.py

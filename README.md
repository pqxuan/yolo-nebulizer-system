# YOLO与雾化器联动系统

## 项目概述

本项目实现了一个基于YOLO目标检测与雾化器联动的系统，当检测到特定类别的物体（pj、tz、zq、yd、td）且置信度大于0.85并持续超过指定时间时，通过GPIO控制对应的雾化器开启3秒后自动关闭。

## 系统组成

系统由两部分组成：

1. **运行在X4开发板Ubuntu系统上的Python检测程序**：使用YOLO模型进行目标检测
2. **运行在RP2040微控制器上的固件程序**：控制雾化器的开关

这两部分通过串口通信，当Python程序检测到目标时，发送命令给RP2040控制相应的雾化器。

## 硬件连接

雾化器模块通常有三个接线端子：

- G：接地（Ground）
- V：电源（VCC，通常是3.3V或5V）
- S：信号（Signal，用于控制雾化器）

连接方式：

1. 将5个雾化器的G端子连接到RP2040的GND引脚
2. 将5个雾化器的V端子连接到RP2040的3.3V或5V引脚（根据雾化器的工作电压选择）
3. 将5个雾化器的S端子分别连接到RP2040的GPIO引脚：
   - 雾化器1（对应pj）：连接到GPIO16
   - 雾化器2（对应tz）：连接到GPIO17
   - 雾化器3（对应zq）：连接到GPIO18
   - 雾化器4（对应yd）：连接到GPIO19
   - 雾化器5（对应td）：连接到GPIO20

## 软件组件

### 1. Python检测程序 (yolo_nebulizer.py)

- 使用YOLO模型进行实时目标检测
- 当检测到特定类别且置信度大于阈值并持续超过指定时间时，通过串口发送命令给RP2040
- 支持热敏打印机打印检测结果

### 2. RP2040固件程序 (nebulizer_firmware.c)

- 通过串口接收命令控制5个雾化器
- 支持定时自动关闭雾化器
- 提供状态反馈

## 使用方法

1. 编译并烧录RP2040固件
2. 连接雾化器到RP2040的对应GPIO引脚
3. 运行Python检测程序

```bash
python yolo_nebulizer.py
```

## 依赖项

- Python 3.x
- PyTorch
- OpenCV
- Ultralytics YOLO
- PySerial
- escpos (用于热敏打印机)

## 配置参数

可在Python程序中调整以下参数：

- `CONFIDENCE_THRESHOLD`: 置信度阈值（默认0.85）
- `DETECTION_DURATION_THRESHOLD`: 检测持续时间阈值（默认2.0秒）
- `RESET_INTERVAL`: 重置检测记录的时间间隔（默认10秒）

## 许可证

MIT
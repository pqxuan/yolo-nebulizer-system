# YOLO与雾化器联动系统实现方案
根据您的需求，我将设计一套系统，实现当YOLO检测到特定类别的图像（pj、tz、zq、yd、td）且置信度大于0.85并持续超过1秒时，通过GPIO控制对应的雾化器开启3秒后自动关闭。下面是详细的实现方案。

## 一、系统概述
系统由两部分组成：

1. 运行在X4开发板Ubuntu系统上的Python检测程序（使用YOLO模型）
2. 运行在RP2040微控制器上的固件程序（控制雾化器）
这两部分通过串口通信，当Python程序检测到目标时，发送命令给RP2040控制相应的雾化器。

## 二、硬件连接方案
### 1. 雾化器接线方案
根据您的需求，需要控制5个雾化器，每个雾化器对应一个检测类别。雾化器模块通常有三个接线端子：

- G：接地（Ground）
- V：电源（VCC，通常是3.3V或5V）
- S：信号（Signal，用于控制雾化器）
连接方式：

1. 将5个雾化器的G端子连接到RP2040的GND引脚
2. 将5个雾化器的V端子连接到RP2040的3.3V或5V引脚（根据雾化器的工作电压选择）
3. 将5个雾化器的S端子分别连接到RP2040的GPIO引脚：
   - 雾化器1（对应mwen）：连接到GPIO16
   - 雾化器2（对应qgan）：连接到GPIO17
   - 雾化器3（对应qnian）：连接到GPIO18
   - 雾化器4（对应sye）：连接到GPIO19
   - 雾化器5（对应xyu）：连接到GPIO20
## 三、RP2040固件程序开发
### 1. 创建工作目录
```
mkdir -p /home/xuan/007测试yolo与雾化器联动/nebulizer_control
cd /home/xuan/007测试yolo与雾化器联动/nebulizer_control
```
### 2. 创建RP2040固件程序
创建一个名为 nebulizer_firmware.c 的文件：
```
nano /home/xuan/007测试yolo与雾化器联动/nebulizer_control/nebulizer_firmware.c
```
nebulizer_firmware.c  :
```
/**
 * 雾化器控制程序 - RP2040固件
 * 通过串口接收命令控制5个雾化器
 */
#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "pico/time.h"

// 定义雾化器连接的GPIO引脚
#define NEBULIZER_1_PIN 16  // mwen
#define NEBULIZER_2_PIN 17  // qgan
#define NEBULIZER_3_PIN 18  // qnian
#define NEBULIZER_4_PIN 19  // sye
#define NEBULIZER_5_PIN 20  // xyu

// 雾化器开启时间（毫秒）
#define NEBULIZER_ON_TIME_MS 3000

// 雾化器状态数组
bool nebulizer_status[5] = {false, false, false, false, false};

// 雾化器定时器数组，用于自动关闭
alarm_id_t nebulizer_timers[5] = {-1, -1, -1, -1, -1};

// 初始化GPIO引脚
void init_gpio() {
    // 初始化雾化器控制引脚
    gpio_init(NEBULIZER_1_PIN);
    gpio_init(NEBULIZER_2_PIN);
    gpio_init(NEBULIZER_3_PIN);
    gpio_init(NEBULIZER_4_PIN);
    gpio_init(NEBULIZER_5_PIN);
    
    // 设置为输出模式
    gpio_set_dir(NEBULIZER_1_PIN, GPIO_OUT);
    gpio_set_dir(NEBULIZER_2_PIN, GPIO_OUT);
    gpio_set_dir(NEBULIZER_3_PIN, GPIO_OUT);
    gpio_set_dir(NEBULIZER_4_PIN, GPIO_OUT);
    gpio_set_dir(NEBULIZER_5_PIN, GPIO_OUT);
    
    // 初始状态设为低电平（关闭）
    gpio_put(NEBULIZER_1_PIN, 0);
    gpio_put(NEBULIZER_2_PIN, 0);
    gpio_put(NEBULIZER_3_PIN, 0);
    gpio_put(NEBULIZER_4_PIN, 0);
    gpio_put(NEBULIZER_5_PIN, 0);
}

// 定时器回调函数，用于自动关闭雾化器
int64_t nebulizer_timer_callback(alarm_id_t id, void *user_data) {
    int nebulizer_id = *((int*)user_data);
    
    // 根据ID选择对应的引脚
    int pin;
    switch(nebulizer_id) {
        case 1: pin = NEBULIZER_1_PIN; break;
        case 2: pin = NEBULIZER_2_PIN; break;
        case 3: pin = NEBULIZER_3_PIN; break;
        case 4: pin = NEBULIZER_4_PIN; break;
        case 5: pin = NEBULIZER_5_PIN; break;
        default: return 0;
    }
    
    // 关闭雾化器
    gpio_put(pin, 0);
    nebulizer_status[nebulizer_id-1] = false;
    
    // 发送确认信息
    printf("雾化器 %d 已自动停止\n", nebulizer_id);
    
    // 清除定时器ID
    nebulizer_timers[nebulizer_id-1] = -1;
    
    return 0;
}

// 控制雾化器开关
void control_nebulizer(int id, bool state) {
    if (id < 1 || id > 5) {
        printf("错误：雾化器ID必须在1-5之间\n");
        return;
    }
    
    // 根据ID选择对应的引脚
    int pin;
    switch(id) {
        case 1: pin = NEBULIZER_1_PIN; break;
        case 2: pin = NEBULIZER_2_PIN; break;
        case 3: pin = NEBULIZER_3_PIN; break;
        case 4: pin = NEBULIZER_4_PIN; break;
        case 5: pin = NEBULIZER_5_PIN; break;
        default: return;
    }
    
    // 设置引脚状态
    gpio_put(pin, state ? 1 : 0);
    nebulizer_status[id-1] = state;
    
    // 发送确认信息
    printf("雾化器 %d %s\n", id, state ? "已启动" : "已停止");
    
    // 如果是开启雾化器，设置定时器自动关闭
    if (state) {
        // 如果已经有定时器，先取消
        if (nebulizer_timers[id-1] != -1) {
            cancel_alarm(nebulizer_timers[id-1]);
        }
        
        // 创建新的定时器
        static int timer_ids[5] = {1, 2, 3, 4, 5};
        nebulizer_timers[id-1] = add_alarm_in_ms(NEBULIZER_ON_TIME_MS, 
                                                nebulizer_timer_callback, 
                                                &timer_ids[id-1], 
                                                false);
    } else {
        // 如果是手动关闭，取消定时器
        if (nebulizer_timers[id-1] != -1) {
            cancel_alarm(nebulizer_timers[id-1]);
            nebulizer_timers[id-1] = -1;
        }
    }
}

int main() {
    // 初始化标准库（包括串口）
    stdio_init_all();
    
    // 初始化GPIO
    init_gpio();
    
    printf("雾化器控制系统已启动\n");
    printf("命令格式: [雾化器ID] [1=开启/0=关闭]\n");
    
    char buffer[10];
    int pos = 0;
    
    while (true) {
        // 检查是否有串口数据
        int c = getchar_timeout_us(0);
        if (c != PICO_ERROR_TIMEOUT) {
            // 收到字符
            if (c == '\n' || c == '\r') {
                // 命令结束，处理命令
                buffer[pos] = '\0';
                
                // 解析命令
                int id, state;
                if (sscanf(buffer, "%d %d", &id, &state) == 2) {
                    if (id >= 1 && id <= 5) {
                        control_nebulizer(id, state == 1);
                    } else {
                        printf("错误：雾化器ID必须在1-5之间\n");
                    }
                } else {
                    printf("错误：命令格式不正确\n");
                }
                
                // 重置缓冲区
                pos = 0;
            } else if (pos < sizeof(buffer) - 1) {
                // 存储字符
                buffer[pos++] = (char)c;
            }
        }
        
        // 短暂延时，避免CPU占用过高
        sleep_ms(10);
    }
    
    return 0;
}
```

### 3. 创建CMakeLists.txt文件
创建一个名为 CMakeLists.txt 的文件：
```
nano /home/xuan/007测试yolo与雾化器联动/nebulizer_control/CMakeLists.txt
```
将以下内容复制到文件中：
```
cmake_minimum_required(VERSION 3.12)

# 导入Pico SDK
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

# 项目名称
project(nebulizer_control C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# 初始化Pico SDK
pico_sdk_init()

# 添加可执行文件
add_executable(nebulizer_firmware
    nebulizer_firmware.c
)

# 启用USB和UART输出
pico_enable_stdio_usb(nebulizer_firmware 1)
pico_enable_stdio_uart(nebulizer_firmware 1)

# 链接库
target_link_libraries(nebulizer_firmware
    pico_stdlib
    hardware_gpio
)

# 创建额外的输出文件（.uf2等）
pico_add_extra_outputs(nebulizer_firmware)
```

## 四、编译RP2040程序
### 1. 编译程序
您已经设置好了Pico SDK，所以可以直接编译RP2040程序：

```
cd /home/xuan/007测试yolo与雾化器联动/nebulizer_control
mkdir build
cd build
cmake ..
make
```

编译成功后，将在 build 目录下生成 nebulizer_firmware.uf2 文件，这是需要上传到RP2040的固件文件。

## 五、上传程序到RP2040
### 1. 将RP2040设置为bootloader模式
您可以使用已有的 usb.sh 脚本将RP2040设置为bootloader模式：
```
cd /home/xuan/007测试yolo与雾化器联动
sudo bash usb.sh
```

或者按住RP2040上的BOOTSEL按钮，然后连接USB线或按下RESET按钮。保持按住BOOTSEL按钮，直到计算机识别出一个新的USB存储设备。

### 2. 复制固件文件到RP2040
将生成的 .uf2 文件复制到RP2040（它会显示为一个USB存储设备）：
```
cp /home/xuan/007测试yolo与雾化器联动/nebulizer_control/build/nebulizer_firmware.uf2 /media/xuan/RPI-RP2
```
注意： /media/xuan/RPI-RP2 是RP2040在bootloader模式下的挂载点，可能会有所不同。请根据实际情况调整路径。

复制完成后，RP2040将自动重启并运行新的固件。

## 六、Python检测与控制程序
创建一个Python程序，用于检测目标并控制雾化器：
```
nano /home/xuan/007测试yolo与雾化器联动/yolo_nebulizer_control.py
```
将以下代码复制到文件中：

```
#!/usr/bin/env python3
"""
YOLO与雾化器联动系统 - Python控制程序
当检测到特定类别的图像且置信度大于0.85并持续超过1秒时，控制对应的雾化器开启
"""
import cv2
import time
import torch
from ultralytics import YOLO
import serial
import logging
import datetime

# 启用调试日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 类别名称及对应的雾化器ID
CLASS_NAMES = {
    0: "pj",   # 对应雾化器1
    1: "ta",   # 对应雾化器2
    2: "zq",  # 对应雾化器3
    3: "yd",    # 对应雾化器4
    4: "td"     # 对应雾化器5
}

# 类别ID到雾化器ID的映射
CLASS_TO_NEBULIZER = {
    0: 1,  # pj -> 雾化器1
    1: 2,  # tz -> 雾化器2
    2: 3,  # zq -> 雾化器3
    3: 4,  # yd -> 雾化器4
    4: 5   # td -> 雾化器5
}

# 重置检测记录的时间间隔（秒）
RESET_INTERVAL = 10
# 持续检测时间阈值（秒）
DETECTION_DURATION_THRESHOLD = 1.0  # 改为1秒
# 置信度阈值
CONFIDENCE_THRESHOLD = 0.85  # 改为0.85
# 检测持续时间字典 {class_id: (start_time, last_seen_time)}
detection_durations = {}
# 已触发的类别集合，避免重复触发
triggered_classes = set()
# 上次重置触发记录的时间
last_trigger_reset_time = 0
# 触发重置间隔（秒）
TRIGGER_RESET_INTERVAL = 5

def connect_to_rp2040():
    """连接到RP2040"""
    # 尝试常见的串口设备
    possible_ports = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0', '/dev/ttyUSB1']
    
    for port in possible_ports:
        try:
            ser = serial.Serial(port, 115200, timeout=1)
            logger.info(f"已连接到 {port}")
            return ser
        except:
            continue
    
    logger.error("错误：无法连接到RP2040")
    logger.error("请确保RP2040已正确连接到X4开发板")
    return None

def send_command(ser, nebulizer_id, state):
    """发送命令到RP2040"""
    if not ser:
        logger.error("错误：串口未连接")
        return False
    
    command = f"{nebulizer_id} {1 if state else 0}\n"
    try:
        ser.write(command.encode())
        time.sleep(0.1)  # 等待响应
        
        # 读取响应
        response = ""
        while ser.in_waiting:
            response += ser.read(ser.in_waiting).decode()
        
        if response:
            logger.info(response.strip())
        
        return True
    except Exception as e:
        logger.error(f"发送命令出错: {e}")
        return False

def main():
    global detection_durations, triggered_classes, last_trigger_reset_time
    
    # 连接到RP2040
    ser = connect_to_rp2040()
    if not ser:
        logger.error("无法连接到RP2040，程序退出")
        return
    
    # 等待RP2040初始化
    time.sleep(2)
    
    # 清空缓冲区
    ser.reset_input_buffer()
    
    # 加载YOLOv8模型
    logger.info("正在加载YOLOv8模型...")
    model = YOLO('test_model.pt')
    logger.info("模型加载完成")
    
    # 打开摄像头
    cap = cv2.VideoCapture(0)
    
    # 检查摄像头是否打开
    if not cap.isOpened():
        logger.error("无法打开摄像头")
        ser.close()
        return
    
    # 获取视频帧的宽度和高度
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # 计时器和FPS初始化
    prev_time = 0
    fps = 0
    last_reset_time = time.time()
    
    logger.info("开始实时检测...")
    
    try:
        while True:
            # 读取帧
            ret, frame = cap.read()
            
            if not ret:
                logger.error("无法读取帧")
                break
            
            # 将帧传递给模型进行预测
            results = model(frame, device='cpu')
            
            # 当前时间
            current_time = time.time()
            
            # 每隔RESET_INTERVAL秒重置检测记录
            if current_time - last_reset_time > RESET_INTERVAL:
                detection_durations.clear()
                last_reset_time = current_time
            
            # 每隔TRIGGER_RESET_INTERVAL秒重置触发记录
            if current_time - last_trigger_reset_time > TRIGGER_RESET_INTERVAL:
                triggered_classes.clear()
                last_trigger_reset_time = current_time
            
            # 创建当前帧检测到的类别集合
            current_frame_classes = set()
            
            # 获取预测结果并绘制在帧上
            for result in results:
                boxes = result.boxes.xyxy.cpu().numpy()
                confidences = result.boxes.conf.cpu().numpy()
                class_ids = result.boxes.cls.cpu().numpy().astype(int)
                
                for i in range(len(boxes)):
                    box = boxes[i]
                    x1, y1, x2, y2 = map(int, box[:4])
                    confidence = confidences[i]
                    class_id = class_ids[i]
                    
                    # 获取类别名称
                    if class_id in CLASS_NAMES:
                        label = CLASS_NAMES[class_id]
                    else:
                        label = f"Class {class_id}"
                    
                    # 绘制边界框和标签
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f'{label} {confidence:.2f}', (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
                    
                    # 记录当前帧检测到的类别
                    current_frame_classes.add(class_id)
                    
                    # 如果检测到目标类别且置信度大于阈值
                    if class_id in CLASS_NAMES.keys() and confidence > CONFIDENCE_THRESHOLD:
                        # 更新检测持续时间
                        if class_id in detection_durations:
                            start_time, _ = detection_durations[class_id]
                            detection_durations[class_id] = (start_time, current_time)
                        else:
                            detection_durations[class_id] = (current_time, current_time)
                        
                        # 检查是否持续检测超过阈值时间
                        start_time, last_seen_time = detection_durations[class_id]
                        detection_duration = last_seen_time - start_time
                        
                        # 如果持续检测时间超过阈值且该类别尚未触发
                        if detection_duration >= DETECTION_DURATION_THRESHOLD and class_id not in triggered_classes:
                            # 标记为已触发
                            triggered_classes.add(class_id)
                            
                            # 获取对应的雾化器ID
                            nebulizer_id = CLASS_TO_NEBULIZER.get(class_id)
                            
                            # 发送命令开启雾化器
                            if nebulizer_id:
                                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                logger.info(f"检测到 {label} 持续 {detection_duration:.2f} 秒，置信度: {confidence:.2f}，开启雾化器 {nebulizer_id}")
                                send_command(ser, nebulizer_id, True)
                                # 注意：雾化器将由RP2040固件自动关闭
            
            # 清理不再出现在当前帧中的类别的持续时间记录
            classes_to_remove = []
            for class_id in detection_durations:
                if class_id not in current_frame_classes:
                    classes_to_remove.append(class_id)
            
            for class_id in classes_to_remove:
                del detection_durations[class_id]
            
            # 计算FPS
            curr_time = time.time()
            fps = 1 / (curr_time - prev_time)
            prev_time = curr_time
            
            # 将FPS绘制在帧的左上角
            cv2.putText(frame, f'FPS: {fps:.2f}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # 显示帧
            cv2.imshow('YOLO与雾化器联动系统', frame)
            
            # 按下'Q'键退出循环
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    except KeyboardInterrupt:
        logger.info("用户中断程序")
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
    finally:
        # 关闭所有雾化器
        for nebulizer_id in range(1, 6):
            send_command(ser, nebulizer_id, False)
        
        # 释放资源
        cap.release()
        cv2.destroyAllWindows()
        ser.close()
        
        logger.info("程序已退出")

if __name__ == "__main__":
    main()
```
### 安装Python依赖
运行Python程序前，需要安装pyserial库：
```
pip3 install pyserial
```

## 七、运行系统
### 1. 确保硬件连接正确
- 雾化器的G端子连接到RP2040的GND
- 雾化器的V端子连接到RP2040的电源（3.3V或5V）
- 雾化器的S端子分别连接到RP2040的GPIO16-20
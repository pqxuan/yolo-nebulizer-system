/**
 * 雾化器控制程序 - RP2040固件
 * 通过串口接收命令控制5个雾化器
 */
#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "pico/time.h"

// 定义雾化器连接的GPIO引脚
#define NEBULIZER_1_PIN 16  // pj
#define NEBULIZER_2_PIN 17  // tz
#define NEBULIZER_3_PIN 18  // zq
#define NEBULIZER_4_PIN 19  // yd
#define NEBULIZER_5_PIN 20  // td

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
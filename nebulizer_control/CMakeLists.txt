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

# 生成额外的输出文件
pico_add_extra_outputs(nebulizer_firmware)
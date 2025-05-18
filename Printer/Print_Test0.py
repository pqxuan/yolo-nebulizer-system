from escpos.printer import Usb
import logging
import os
import sys
import time  # 导入time模块用于添加延迟

# 启用调试日志
logging.basicConfig(level=logging.DEBUG)

# 根据 lsusb 输出的信息，设置正确的 Vendor ID 和 Product ID
VENDOR_ID = 0x28e9  # GDMicroelectronics micro-printer 的供应商ID
PRODUCT_ID = 0x0289  # GDMicroelectronics micro-printer 的产品ID

# 根据 find_endpoints.py 输出的结果，设置正确的端点地址
in_ep = 0x81  # 输入端点地址
out_ep = 0x03  # 输出端点地址

def get_md_files():
    """获取当前目录下的所有 .md 文件"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    md_files = [f for f in os.listdir(current_dir) if f.endswith('.md')]
    return md_files

def display_menu(files):
    """显示文件选择菜单"""
    print("\n===== 打印文件选择 =====")
    for i, file in enumerate(files, 1):
        print(f"{i}. {file}")
    print("0. 退出程序")
    print("========================\n")

def read_md_file(file_path):
    """读取 .md 文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"读取文件失败: {e}")
        return None

def print_file(printer, content):
    """打印文件内容"""
    try:
        # 发送初始化命令
        printer._raw(b'\x1B\x40')  # ESC @ - 初始化打印机
        time.sleep(0.5)  # 初始化后等待0.5秒

        # 设置波特率 - 降低波特率以减慢打印速度
        printer._raw(b'\x1B\x52\x00')  # 设置波特率为 9600
        time.sleep(0.5)  # 设置波特率后等待0.5秒

        # 增加调试信息
        logging.debug("开始打印...")

        # 设置居中对齐
        printer.set(align='center')
        time.sleep(0.3)  # 设置对齐后等待0.3秒
        
        # 设置行距 (30点, 约3.75mm)
        printer._raw(b'\x1B\x33\x1E')  # ESC 3 n - 设置行距为n点
        time.sleep(0.3)  # 设置行距后等待0.3秒
        
        # 设置打印速度为最快
        printer._raw(b'\x1B\x73\x02')  # ESC s n - 设置打印速度 (0最慢，1中速，2最快)
        time.sleep(0.2)  # 设置打印速度后等待0.2秒
        
        # 打印文件内容 - 只打印内容，不打印文件名和路径
        lines = content.split('\n')
        line_count = 0  # 用于跟踪实际打印的行数（不包括空行）
        
        for i, line in enumerate(lines):
            # 跳过空行，但不计入行数
            if not line.strip():
                printer.text('\n')
                time.sleep(0.2)  # 空行等待0.2秒
                logging.debug("打印空行")
                continue
                
            # 增加行数计数（只计算非空行）
            line_count += 1
            
            # 如果是第三行（行数计数为3），则设置为加粗
            if line_count == 2:
                printer.set(bold=True)
                logging.debug(f"第三行加粗: {line}")
            
            # 每行打印后添加延迟
            printer.text(line)
            time.sleep(0.2)  # 每行文本打印后等待0.2秒
            printer.text('\n')
            time.sleep(0.2)  # 换行后等待0.2秒
            logging.debug(f"打印行: {line}")
            
            # 如果刚刚打印了加粗的第三行，恢复正常字体
            if line_count == 3:
                printer.set(bold=False)
                logging.debug("恢复正常字体")
        
        # 打印结束后等待
        time.sleep(0.50)
        
        # 恢复默认设置
        printer.set(align='left')
        time.sleep(0.3)
        printer._raw(b'\x1B\x32')  # ESC 2 - 恢复默认行距
        time.sleep(0.3)
        
        # 打印结束后走纸
        printer.text('\n\n')
        time.sleep(0.5)
        
        # 切纸前等待
        time.sleep(1)
        
        # 切纸
        printer.cut()
        
        print("打印成功！")
        
    except Exception as e:
        print(f"打印失败: {e}")

def main():
    # 获取可打印的 .md 文件
    md_files = get_md_files()
    
    if not md_files:
        print("未找到可打印的 .md 文件！")
        return
    
    try:
        # 初始化打印机对象，并指定正确的端点地址
        p = Usb(VENDOR_ID, PRODUCT_ID, in_ep=in_ep, out_ep=out_ep)
        
        while True:
            # 显示菜单
            display_menu(md_files)
            
            # 获取用户选择
            choice = input("请选择要打印的文件编号: ")
            
            try:
                choice = int(choice)
                
                if choice == 0:
                    print("退出程序")
                    break
                
                if 1 <= choice <= len(md_files):
                    selected_file = md_files[choice - 1]
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    file_path = os.path.join(current_dir, selected_file)
                    
                    print(f"您选择了: {selected_file}")
                    content = read_md_file(file_path)
                    
                    if content:
                        print_file(p, content)
                else:
                    print("无效的选择，请重新输入！")
            
            except ValueError:
                print("请输入有效的数字！")
    
    except Exception as e:
        print(f"打印机初始化失败: {e}")

if __name__ == "__main__":
    main()
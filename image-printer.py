from escpos.printer import Usb
import logging
import os
from PIL import Image, ImageOps

# 启用调试日志
logging.basicConfig(level=logging.DEBUG)

# 根据新的 lsusb 输出信息，设置正确的 Vendor ID 和 Product ID
# 请将下面的值替换为您新打印机的正确ID
VENDOR_ID = 0x0fe6  # 示例：ICS Advent Parallel Adapter 的ID
PRODUCT_ID = 0x811e  # 示例：ICS Advent Parallel Adapter 的ID

# 根据 find_endpoints.py 输出的结果，设置正确的端点地址
in_ep = 0x82  # 输入端点地址
out_ep = 0x02  # 输出端点地址

# 指定要打印的图片路径
image_path = '/home/xuan/007测试yolo与雾化器联动/logo2.png'

# 58mm热敏打印纸的有效打印宽度（像素）
# 通常58mm打印机的有效打印宽度约为384像素（48mm）
PRINTER_WIDTH_PIXELS = 384

try:
    # 检查图片文件是否存在
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片文件不存在: {image_path}")
    
    # 初始化打印机对象，并指定正确的端点地址
    p = Usb(VENDOR_ID, PRODUCT_ID, in_ep=in_ep, out_ep=out_ep)

    # 发送初始化命令
    p._raw(b'\x1B\x40')  # ESC @ - 初始化打印机

    # 设置波特率
    p._raw(b'\x1B\x52\x00')  # 设置波特率为 9600

    # 增加调试信息
    logging.debug("开始打印...")
    
    # 打印标题
    p.set(align='center')
    p.text("图片打印测试\n\n")
    
    # 打印图像
    try:
        from PIL import Image
        logging.debug(f"正在打开图片: {image_path}")
        img = Image.open(image_path)
        logging.debug(f"图片已打开，原始尺寸: {img.size}，格式: {img.format}")
        
        # 转换为灰度图像
        img = ImageOps.grayscale(img)
        logging.debug("图片已转换为灰度")
        
        # 调整图片大小以适应打印机宽度，保持宽高比
        width_percent = (PRINTER_WIDTH_PIXELS / float(img.size[0]))
        new_height = int((float(img.size[1]) * float(width_percent)))
        img = img.resize((PRINTER_WIDTH_PIXELS, new_height), Image.LANCZOS)
        logging.debug(f"图片已调整大小为: {img.size}")
        
        # 打印图像信息
        p.text(f"原始图片: {image_path}\n")
        p.text(f"调整后尺寸: {img.size[0]}x{img.size[1]} 像素\n\n")
        
        # 居中打印图像
        p.set(align='center')
        logging.debug("开始打印图片...")
        p.image(img)
        logging.debug("图片打印完成")
        
    except ImportError:
        print("PIL (Pillow) 库未安装，无法打印图像")
        logging.error("PIL (Pillow) 库未安装，无法打印图像")
    except Exception as e:
        print(f"图像打印失败: {e}")
        logging.error(f"图像打印失败: {e}")

    # 打印结束信息
    p.text("\n\n")
    p.set(align='center')
    p.text("--- 打印测试结束 ---\n")
    
    # 切纸
    p.cut()

    print("打印成功！")

except Exception as e:
    print(f"打印失败: {e}")
    logging.error(f"打印失败: {e}")

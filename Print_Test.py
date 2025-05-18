from escpos.printer import Usb
import logging

# 启用调试日志
logging.basicConfig(level=logging.DEBUG)

# 根据 lsusb 输出的信息，设置正确的 Vendor ID 和 Product ID
VENDOR_ID = 0x0fe6  # 示例：ICS Advent Parallel Adapter 的ID
PRODUCT_ID = 0x811e  # 示例：ICS Advent Parallel Adapter 的ID

# 根据 find_endpoints.py 输出的结果，设置正确的端点地址
in_ep = 0x82  # 输入端点地址
out_ep = 0x02  # 输出端点地址

try:
    # 初始化打印机对象，并指定正确的端点地址
    p = Usb(VENDOR_ID, PRODUCT_ID, in_ep=in_ep, out_ep=out_ep)

    # 发送初始化命令
    p._raw(b'\x1B\x40')  # ESC @ - 初始化打印机

    # 设置波特率
    p._raw(b'\x1B\x52\x00')  # 设置波特率为 9600

    # 增加调试信息
    logging.debug("开始打印...")

    # 打印多行文本
    p.text("测试打印\n")
    logging.debug("完成第一行文本打印")
    p.text("第一行文本\n")
    logging.debug("完成第二行文本打印")
    p.text("第二行文本\n")
    logging.debug("完成第三行文本打印")
    p.text("第三行文本\n")
    logging.debug("完成所有文本打印")

    # 打印加粗文本
    p.set(align='left', bold=True)
    p.text("加粗文本\n")
    p.set(bold=False)  # 恢复默认设置

    # 打印居中文本
    p.set(align='center')
    p.text("居中文本\n")
    p.set(align='left')  # 恢复默认设置

    # 打印右对齐文本
    p.set(align='right')
    p.text("右对齐文本\n")
    p.set(align='left')  # 恢复默认设置

    # 打印下划线文本
    p.set(underline=1)
    p.text("下划线文本\n")
    p.set(underline=0)  # 恢复默认设置

    # 打印条形码
    p.barcode('123456789012', 'EAN13', 64, 2, '', '')

    # 打印二维码
    p.qr('https://example.com')

    # 打印图像（如果有图像文件）
    try:
        from PIL import Image
        img = Image.open('test_image.png')  # 替换为你的图像路径
        p.image(img)
    except ImportError:
        print("PIL (Pillow) 库未安装，跳过图像打印")
    except Exception as e:
        print(f"图像打印失败: {e}")
        
    # --- 新增测试内容开始 ---
    
    # 打印分隔线
    p.text("\n" + "-" * 32 + "\n")
    
    # 测试不同字体大小
    p.set(font='a')
    p.text("标准字体A\n")
    p.set(font='b')
    p.text("标准字体B\n")
    p.set(font='a')  # 恢复默认字体
    
    # 测试不同字体宽度和高度
    p.set(width=2, height=2)
    p.text("放大字体\n")
    p.set(width=1, height=1)  # 恢复默认大小
    
    # 测试倒置打印
    p.set(flip=True)
    p.text("倒置文本\n")
    p.set(flip=False)  # 恢复正常
    
    # 测试白底黑字
    p.set(reverse=True)
    p.text("反色文本\n")
    p.set(reverse=False)  # 恢复正常
    
    # 测试不同行间距
    p.set(spacing=8)
    p.text("增加行间距的文本\n第二行\n")
    p.set(spacing=0)  # 恢复默认行间距
    
    # 测试打印中文和特殊字符
    p.text("中文打印测试：你好，世界！\n")
    p.text("特殊字符：!@#$%^&*()_+\n")
    
    # 测试打印表格
    p.text("\n简单表格测试:\n")
    p.text("+------------+------------+\n")
    p.text("| 商品       | 价格       |\n")
    p.text("+------------+------------+\n")
    p.text("| 苹果       | ¥5.00      |\n")
    p.text("| 香蕉       | ¥3.50      |\n")
    p.text("| 橙子       | ¥4.20      |\n")
    p.text("+------------+------------+\n\n")
    
    # 测试打印收据格式
    p.set(align='center')
    p.text("收据测试\n")
    p.text("================\n")
    p.set(align='left')
    p.text("日期: 2023-10-15\n")
    p.text("时间: 14:30:45\n")
    p.text("交易号: TX12345678\n\n")
    p.text("商品清单:\n")
    p.text("商品A  x2  ¥10.00\n")
    p.text("商品B  x1  ¥15.50\n")
    p.text("商品C  x3  ¥20.00\n\n")
    p.set(align='right')
    p.text("总计: ¥45.50\n\n")
    p.set(align='center')
    p.text("谢谢惠顾，欢迎再次光临！\n")
    p.set(align='left')  # 恢复默认对齐
    
    # 测试打印不同的条形码类型
    p.text("\n不同类型条形码测试:\n")
    p.barcode('1234567890', 'CODE39', 60, 2, '', '')
    p.text("\nCODE39条形码\n\n")
    
    p.barcode('1234567890', 'CODE128', 60, 2, '', '')
    p.text("\nCODE128条形码\n\n")
    
    # 测试打印多个二维码
    p.text("\n多个二维码测试:\n")
    p.qr('https://www.baidu.com', size=6)
    p.text("\n百度网址\n\n")
    
    p.qr('tel:+8612345678901', size=6)
    p.text("\n电话号码\n\n")
    
    # --- 新增测试内容结束 ---

    # 切纸
    p.cut()

    print("打印成功！")

except Exception as e:
    print(f"打印失败: {e}")

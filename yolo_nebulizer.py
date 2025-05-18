import cv2
import time
import torch
import serial
import logging
import datetime
import numpy as np
import os
from collections import deque
from ultralytics import YOLO
from PIL import Image, ImageOps
from escpos.printer import Usb

# 启用调试日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 类别名称
CLASS_NAMES = {
    0: "pj",
    1: "tz",
    2: "zq",
    3: "yd",
    4: "td"
}

# 打印机设置
VENDOR_ID = 0x0fe6  # 热敏打印机的Vendor ID
PRODUCT_ID = 0x811e  # 热敏打印机的Product ID
in_ep = 0x82  # 输入端点地址
out_ep = 0x02  # 输出端点地址
PRINTER_WIDTH_PIXELS = 384  # 58mm热敏打印纸的有效打印宽度（像素）
LOGO_PATH = '/home/xuan/008/logo2.png'  # Logo图片路径

# 重置检测记录的时间间隔（秒）
RESET_INTERVAL = 10
# 持续检测时间阈值（秒）- 修改为3秒
DETECTION_DURATION_THRESHOLD = 2.0
# 置信度阈值
CONFIDENCE_THRESHOLD = 0.85
# 置信度历史记录长度
CONFIDENCE_HISTORY_LENGTH = 10
# 检测持续时间字典 {class_id: (start_time, last_seen_time)}
detection_durations = {}
# 已触发的类别集合，避免重复触发
triggered_classes = set()
# 置信度历史记录 {class_id: deque([confidence1, confidence2, ...])}
confidence_histories = {}

# 初始化串口通信
def init_serial():
    try:
        # 根据实际情况修改串口设备名称和波特率
        ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
        logger.info("串口连接成功")
        return ser
    except Exception as e:
        logger.error(f"串口连接失败: {e}")
        return None

# 发送命令到RP2040
def send_command(ser, nebulizer_id, state):
    if ser is None:
        logger.error("串口未连接")
        return False
    
    try:
        command = f"{nebulizer_id} {1 if state else 0}\n"
        ser.write(command.encode())
        logger.info(f"发送命令: {command.strip()}")
        return True
    except Exception as e:
        logger.error(f"发送命令失败: {e}")
        return False

# 更新置信度历史记录并计算平均值
def update_confidence_history(class_id, confidence):
    if class_id not in confidence_histories:
        confidence_histories[class_id] = deque(maxlen=CONFIDENCE_HISTORY_LENGTH)
    
    confidence_histories[class_id].append(confidence)
    
    # 计算平均置信度
    return np.mean(confidence_histories[class_id])

# 初始化打印机
def init_printer():
    try:
        # 初始化打印机对象，并指定正确的端点地址
        p = Usb(VENDOR_ID, PRODUCT_ID, in_ep=in_ep, out_ep=out_ep)
        
        # 发送初始化命令
        p._raw(b'\x1B\x40')  # ESC @ - 初始化打印机
        
        # 设置波特率
        p._raw(b'\x1B\x52\x00')  # 设置波特率为 9600
        
        logger.info("打印机初始化成功")
        return p
    except Exception as e:
        logger.error(f"打印机初始化失败: {e}")
        return None

# 打印Logo图片
def print_logo(printer):
    if printer is None:
        logger.error("打印机未连接")
        return False
    
    try:
        # 检查图片文件是否存在
        if not os.path.exists(LOGO_PATH):
            logger.error(f"Logo图片文件不存在: {LOGO_PATH}")
            return False
        
        # 打印标题
        printer.set(align='center')
        printer.text("青岛老城区气味地图\n\n")
        
        # 打印图像
        logger.info(f"正在打印Logo: {LOGO_PATH}")
        img = Image.open(LOGO_PATH)
        
        # 转换为灰度图像
        img = ImageOps.grayscale(img)
        
        # 调整图片大小以适应打印机宽度，保持宽高比
        width_percent = (PRINTER_WIDTH_PIXELS / float(img.size[0]))
        new_height = int((float(img.size[1]) * float(width_percent)))
        img = img.resize((PRINTER_WIDTH_PIXELS, new_height), Image.LANCZOS)
        
        # 居中打印图像
        printer.set(align='center')
        printer.image(img)
        printer.text("\n")
        
        return True
    except Exception as e:
        logger.error(f"打印Logo失败: {e}")
        return False

# 打印检测信息和内容
def print_detection_info(printer, class_id, confidence):
    if printer is None:
        logger.error("打印机未连接")
        return False
    
    try:
        # 获取当前时间
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 获取类别名称
        label = CLASS_NAMES.get(class_id, f"未知类别 {class_id}")
        
        # 打印时间和检测信息
        printer.set(align='center')
        printer.text("\n" + "-" * 32 + "\n")
        printer.text(f"时间: {current_time}\n")
        printer.text("-" * 32 + "\n\n")
        
        # 根据不同类别打印不同内容
        if class_id == 0:  # pj
            printer.set(align='center', bold=True)
            printer.text("青岛啤酒博物馆\n\n")
            printer.set(bold=False)
            
            printer.set(align='left')
            printer.text("建筑：\n")
            printer.text("1903年德建厂址\n")
            printer.text("发酵罐工业长廊\n")
            printer.text("回廊陈列原始设备\n")
            printer.text("地下酒窖保存百年酵母\n\n")
            
            printer.text("工艺：\n")
            printer.text("传承德国纯酿法\n")
            printer.text("采用慕尼黑啤酒酵母\n")
            printer.text("酿造周期长达72小时\n\n")
            
            printer.text("展品：\n")
            printer.text("1906年慕尼黑金奖\n")
            printer.text("1930年代德制生产线\n")
            printer.text("历代包装设计展示\n\n")
            
            printer.text("体验：\n")
            printer.text("醉酒小屋(15度倾斜)\n")
            printer.text("生啤原浆品鉴区\n")
            printer.text("互动酿酒体验台\n\n")
            
            printer.text("气味构成：\n")
            printer.text("烘焙大麦(20%)\n")
            printer.text("啤酒花(30%)\n")
            printer.text("橡木桶陈香(50%)\n")
            
        elif class_id == 1:  # tz
            printer.set(align='center', bold=True)
            printer.text("圣弥厄尔天主教堂\n\n")
            printer.set(bold=False)
            
            printer.set(align='left')
            printer.text("建筑：\n")
            printer.text("德国毕娄哈设计\n")
            printer.text("哥特式双塔高56米\n")
            printer.text("红砖砌筑德式传统\n\n")
            
            printer.text("历史：\n")
            printer.text("1932-1934年建造\n")
            printer.text("文革时期钟楼损毁\n")
            printer.text("2008年恢复礼拜功能\n\n")
            
            printer.text("特色：\n")
            printer.text("德国制彩色玻璃窗\n")
            printer.text("崂山花岗岩外墙\n")
            printer.text("亚洲最大管风琴之一\n")
            printer.text("周日传统弥撒仪式\n\n")
            
            printer.text("地位：\n")
            printer.text("中国唯一祝圣教堂\n")
            printer.text("山东最大天主教堂\n")
            printer.text("青岛宗教文化地标\n\n")
            
            printer.text("气味构成：\n")
            printer.text("檀香(圣像祭坛)\n")
            printer.text("石蜡(烛台照明)\n")
            printer.text("老木香(管风琴木材)\n")
            
        elif class_id == 2:  # zq
            printer.set(align='center', bold=True)
            printer.text("栈桥海域\n\n")
            printer.set(bold=False)
            
            printer.set(align='left')
            printer.text("建筑：\n")
            printer.text("440米探海长廊\n")
            printer.text("回澜阁琉璃瓦\n")
            printer.text("八角阁楼循环系统\n\n")
            
            printer.text("生态：\n")
            printer.text("每年10万只海鸥\n")
            printer.text("冬季迁徙停留点\n")
            printer.text("黄渤海特色鱼类\n\n")
            
            printer.text("奇观：\n")
            printer.text("四月平流雾\n")
            printer.text("\"海上仙山\"景象\n")
            printer.text("独特礁石景观\n\n")
            
            printer.text("文化：\n")
            printer.text("毛泽东诗作取景地\n")
            printer.text("端午龙舟赛举办地\n\n")
            
            printer.text("气味构成：\n")
            printer.text("死海盐(潮汐矿物)\n")
            printer.text("椰子油(渔民防晒)\n")
            printer.text("海藻腥味(涨潮残留)\n")
            
        elif class_id == 3:  # yd
            printer.set(align='center', bold=True)
            printer.text("青岛邮电博物馆\n\n")
            printer.set(bold=False)
            
            printer.set(align='left')
            printer.text("建筑：\n")
            printer.text("德式红砖钟楼\n")
            printer.text("德国进口柚木楼梯\n")
            printer.text("保留98%原始构件\n\n")
            
            printer.text("功能：\n")
            printer.text("最早德式邮局\n")
            printer.text("仍在日常营业\n")
            printer.text("传统邮政服务体验\n\n")
            
            printer.text("展品：\n")
            printer.text("1897年大龙邮票\n")
            printer.text("德占时期邮筒\n")
            printer.text("民国时期绿邮筒\n\n")
            
            printer.text("技术：\n")
            printer.text("活字印刷体验\n")
            printer.text("摩尔斯电码实物\n")
            printer.text("通信设备演进展示\n\n")
            
            printer.text("气味构成：\n")
            printer.text("铅印油墨(印刷车间)\n")
            printer.text("广藿香(邮包陈香)\n")
            printer.text("氧化铁(红砖气息)\n")
            
        elif class_id == 4:  # td
            printer.set(align='center', bold=True)
            printer.text("团岛农贸市场\n\n")
            printer.set(bold=False)
            
            printer.set(align='left')
            printer.text("历史：\n")
            printer.text("1902年德建菜场\n")
            printer.text("三次大规模改造\n")
            printer.text("保留早期拱券结构\n\n")
            
            printer.text("分区：\n")
            printer.text("海产码头直供区\n")
            printer.text("王姐烧烤档25年\n")
            printer.text("海鲜现场加工区\n\n")
            
            printer.text("时令：\n")
            printer.text("春季鲅鱼汛(4-6月)\n")
            printer.text("秋冬海蛎子丰收\n")
            printer.text("夏季皮皮虾旺季\n\n")
            
            printer.text("特色：\n")
            printer.text("塑料袋装鲜啤\n")
            printer.text("现开海胆刺身\n")
            printer.text("海鲜拼盘自助区\n\n")
            
            printer.text("气味构成：\n")
            printer.text("海带液(淡盐水)\n")
            printer.text("八角油(卤煮香气)\n")
            printer.text("乙酸异戊酯(香蕉味)\n")
        
        # 打印结束
        printer.text("\n\n")
        printer.set(align='center')
        printer.text("-" * 32 + "\n")
        printer.text("青岛老城区气味地图\n")
        printer.text("-" * 32 + "\n\n")
        
        # 切纸
        printer.cut()
        
        logger.info(f"成功打印类别 {label} 的信息")
        return True
    except Exception as e:
        logger.error(f"打印检测信息失败: {e}")
        return False

# 主函数
def main():
    global detection_durations, triggered_classes, confidence_histories
    
    # 加载YOLOv8模型
    logger.info("正在加载YOLOv8模型...")
    model = YOLO('test_model.pt')
    logger.info("模型加载完成")
    
    # 初始化串口
    ser = init_serial()
    if ser is None:
        logger.error("无法继续，程序退出")
        return
    
    # 初始化打印机
    printer = init_printer()
    if printer is None:
        logger.warning("打印机初始化失败，将继续运行但不执行打印功能")
    
    # 打开摄像头
    cap = cv2.VideoCapture(0)
    
    # 检查摄像头是否打开
    if not cap.isOpened():
        logger.error("无法打开摄像头")
        return
    
    # 获取视频帧的宽度和高度
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # 设置窗口大小
    cv2.namedWindow('YOLOv8 实时目标检测与雾化器控制', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('YOLOv8 实时目标检测与雾化器控制', width*2, height*2)
    
    # 计时器和FPS初始化
    prev_time = 0
    fps = 0
    last_reset_time = time.time()
    
    # 添加暂停检测的标志和计时器
    paused_until = 0
    # 添加摄像头状态标志
    camera_closed = False
    # 添加最后一帧的缓存
    last_frame = None
    
    logger.info("开始实时检测...")
    
    try:
        while True:
            current_time = time.time()
            
            # 检查是否处于暂停状态
            if current_time < paused_until:
                # 计算剩余暂停时间
                remaining_time = int(paused_until - current_time)
                
                # 暂停开始后1秒关闭摄像头
                if not camera_closed and remaining_time < 9:  # 10-1=9秒
                    logger.info("暂停检测1秒后，关闭摄像头")
                    cap.release()
                    camera_closed = True
                
                # 暂停结束前1秒重新打开摄像头
                if camera_closed and remaining_time <= 1:
                    logger.info("暂停结束前1秒，重新打开摄像头")
                    cap = cv2.VideoCapture(0)
                    if not cap.isOpened():
                        logger.error("无法重新打开摄像头")
                        break
                    camera_closed = False
                    
                    # 清除所有检测持续时间记录和置信度历史
                    detection_durations.clear()
                    confidence_histories.clear()
                    logger.info("暂停结束，已清除所有检测记录")
                
                # 如果摄像头已关闭，使用最后一帧
                if camera_closed and last_frame is not None:
                    frame = last_frame.copy()
                else:
                    # 读取帧
                    ret, frame = cap.read()
                    if not ret:
                        if camera_closed:
                            # 如果摄像头已关闭且没有最后一帧，创建一个黑色帧
                            if last_frame is None:
                                frame = np.zeros((height, width, 3), dtype=np.uint8)
                            else:
                                frame = last_frame.copy()
                        else:
                            logger.error("无法读取帧")
                            break
                
                # 在帧上显示暂停状态
                cv2.putText(frame, f'检测已暂停，等待打印完成: {remaining_time}秒', 
                            (10, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 
                            1, (0, 0, 255), 2)
                
                if camera_closed:
                    cv2.putText(frame, '摄像头已关闭', (10, height - 60), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                # 计算FPS
                curr_time = time.time()
                fps = 1 / (curr_time - prev_time)
                prev_time = curr_time
                
                # 将FPS绘制在帧的左上角
                cv2.putText(frame, f'FPS: {fps:.2f}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # 显示帧
                cv2.imshow('YOLOv8 实时目标检测与雾化器控制', frame)
                
                # 按下'Q'键退出循环
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
                continue  # 跳过检测，直接进入下一帧
            
            # 读取帧
            ret, frame = cap.read()
            
            if not ret:
                logger.error("无法读取帧")
                break
            
            # 保存最后一帧用于暂停期间显示
            last_frame = frame.copy()
            
            # 每隔RESET_INTERVAL秒重置检测记录和触发记录
            if current_time - last_reset_time > RESET_INTERVAL:
                triggered_classes.clear()
                last_reset_time = current_time
            
            # 将帧传递给模型进行预测
            results = model(frame, device='cpu')
            
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
                    
                    # 如果检测到目标类别
                    if class_id in CLASS_NAMES.keys():
                        # 更新置信度历史记录并计算平均置信度
                        avg_confidence = update_confidence_history(class_id, confidence)
                        
                        # 更新检测持续时间
                        if class_id in detection_durations:
                            start_time, _ = detection_durations[class_id]
                            detection_durations[class_id] = (start_time, current_time)
                        else:
                            detection_durations[class_id] = (current_time, current_time)
                        
                        # 检查是否持续检测超过阈值时间
                        start_time, last_seen_time = detection_durations[class_id]
                        detection_duration = last_seen_time - start_time
                        
                        # 在帧上显示平均置信度和持续时间
                        info_text = f"Avg: {avg_confidence:.2f}, Time: {detection_duration:.1f}s"
                        cv2.putText(frame, info_text, (x1, y2 + 20), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                        
                        # 如果持续检测时间超过阈值且平均置信度大于阈值且该类别尚未触发
                        if (detection_duration >= DETECTION_DURATION_THRESHOLD and 
                            avg_confidence > CONFIDENCE_THRESHOLD and 
                            class_id not in triggered_classes):
                            
                            nebulizer_id = class_id + 1  # 雾化器ID从1开始
                            logger.info(f"检测到 {label} 持续 {detection_duration:.2f} 秒，平均置信度: {avg_confidence:.2f}，触发雾化器 {nebulizer_id}")
                            
                            # 发送命令开启雾化器
                            if send_command(ser, nebulizer_id, True):
                                # 标记该类别已触发
                                triggered_classes.add(class_id)
                                
                                # 执行打印
                                if printer is not None:
                                    # 创建一个新线程来执行打印，避免阻塞主线程
                                    import threading
                                    def print_thread():
                                        try:
                                            # 打印Logo
                                            print_logo(printer)
                                            # 打印检测信息和内容
                                            print_detection_info(printer, class_id, avg_confidence)
                                            logger.info(f"类别 {label} 的打印任务已完成")
                                        except Exception as e:
                                            logger.error(f"打印线程出错: {e}")
                                    
                                    # 启动打印线程
                                    threading.Thread(target=print_thread).start()
                                    logger.info(f"已启动打印线程，打印类别 {label} 的信息")
                                    
                                    # 设置暂停检测10秒
                                    paused_until = current_time + 10
                                    logger.info(f"检测已暂停，将在10秒后恢复")
                                    
                                    # 在帧上显示暂停状态
                                    cv2.putText(frame, "检测已暂停，等待打印完成: 10秒", 
                                                (10, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 
                                                1, (0, 0, 255), 2)
            
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
            cv2.imshow('YOLOv8 实时目标检测与雾化器控制', frame)
            
            # 按下'Q'键退出循环
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    except KeyboardInterrupt:
        logger.info("用户中断程序")
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
    finally:
        # 关闭所有雾化器
        if ser is not None:
            for i in range(1, 6):
                send_command(ser, i, False)
            ser.close()
        
        # 释放资源
        cap.release()
        cv2.destroyAllWindows()
        
        logger.info("程序已退出")

if __name__ == "__main__":
    main()
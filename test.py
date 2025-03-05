import time
import pyautogui
import keyboard
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def find_and_click(image_path):
    """查找并点击指定的图片"""
    logger.debug(f"查找图片: {image_path}")
    while True:
        # 查找图片
        location = pyautogui.locateOnScreen(image_path, confidence=0.8)
        if location:
            logger.info(f"找到图片: {image_path}，位置: {location}")
            # 点击图片中心
            pyautogui.click(location.left + location.width / 2, location.top + location.height / 2)
            logger.info(f"点击图片: {image_path}")
            break
        else:
            logger.warning(f"未找到图片: {image_path}，继续查找...")
            time.sleep(1)  # 每秒查找一次

def main():
    """主函数"""
    images = ['a.jpg', 'b.jpg', 'c.jpg']  # 图片列表
    logger.info("按F9开始识别图片...")

    # 等待F9键按下
    keyboard.wait('F9')
    logger.info("开始识别图片")

    for image in images:
        find_and_click(image)
        time.sleep(1)  # 等待1秒

if __name__ == '__main__':
    main() 
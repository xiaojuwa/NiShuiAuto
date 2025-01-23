import sys
import cv2
import numpy as np
import pyautogui
import win32gui
import win32con
import time
import logging
from PIL import ImageGrab
import keyboard
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, 
                           QVBoxLayout, QWidget, QLineEdit, QHBoxLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon
import os

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class BattleThread(QThread):
    """战场自动化线程"""
    log_signal = pyqtSignal(str)  # 日志信号
    status_signal = pyqtSignal(str)  # 状态信号

    def __init__(self):
        super().__init__()
        self.running = False
        self.config = {
            'skill_key': 'f4',  # 默认F4键
            'check_interval': 1,
            'exit_key': 'esc',
            'follow_key': 'g',  # 添加跟随键
            'first_follow_duration': 30,  # 首次进入战场的跟随时间（秒）
            'follow_duration': 15,  # 复活后的跟随持续时间（秒）
            'tab_interval': 5,  # Tab键按下间隔（秒）
            'loading_wait': 30,  # 进入战场loading等待时间（秒）
            'power_key': 'f',  # 激活强力状态的按键
            # 为不同类型的图片设置不同的置信度要求
            'confidence_levels': {
                'battle_icon': [0.8, 0.7],      # 战场图标识别
                'in_battle': [0.9, 0.8, 0.7],   # 战场内状态识别
                'match_button': [0.8, 0.7],     # 匹配按钮识别
                'matching': [0.8, 0.7],         # 匹配中状态识别
                'others': [0.8, 0.7]            # 其他图片识别
            }
        }
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5
        self.battle_count = 0
        logger.debug("BattleThread初始化完成")

    def find_image(self, image_path, image_type='others', custom_confidence_levels=None):
        """查找图片，根据图片类型使用不同的置信度
        
        Args:
            image_path: 图片路径
            image_type: 图片类型，用于选择对应的置信度列表
            custom_confidence_levels: 自定义置信度列表，优先级高于预设值
            
        Returns:
            找到的图片位置，如果未找到返回None
        """
        confidence_levels = custom_confidence_levels if custom_confidence_levels else \
                          self.config['confidence_levels'].get(image_type, self.config['confidence_levels']['others'])
            
        for confidence in confidence_levels:
            try:
                result = pyautogui.locateOnScreen(image_path, confidence=confidence)
                if result:
                    logger.debug(f"找到图片 {image_path}，置信度: {confidence}")
                    return result
            except Exception as e:
                logger.error(f"查找图片 {image_path} 时发生错误: {str(e)}")
        return None

    def find_all_images(self, image_path, confidence_levels=None):
        """查找所有匹配的图片，尝试多个置信度
        
        Args:
            image_path: 图片路径
            confidence_levels: 置信度列表，如果为None则使用默认配置
            
        Returns:
            找到的所有图片位置列表
        """
        if confidence_levels is None:
            confidence_levels = self.config['confidence_levels']
            
        for confidence in confidence_levels:
            try:
                results = list(pyautogui.locateAllOnScreen(image_path, confidence=confidence))
                if results:
                    logger.debug(f"找到 {len(results)} 个图片 {image_path}，置信度: {confidence}")
                    return results
            except Exception as e:
                logger.error(f"查找图片 {image_path} 时发生错误: {str(e)}")
        return []

    def check_battle_time(self):
        """检查当前是否在战场开放时间内"""
        current_time = time.localtime()
        current_hour = current_time.tm_hour
        current_wday = current_time.tm_wday  # 0-6, 0是周一
        
        logger.debug(f"检查战场时间 - 当前时间：{current_hour}点，星期{current_wday + 1}")
        
        # 检查周六周日上午
        if current_wday in [5, 6] and current_hour < 10:  # 5是周六，6是周日
            return False, "周六、周日上午10点前战场暂时关闭"
            
        # 检查是否在开放时间段
        if 12 <= current_hour < 18:
            return True, "当前处于下午场开放时间"
        elif current_wday == 4:  # 周五
            if 22 <= current_hour or current_hour < 2:
                return True, "当前处于周五晚场开放时间"
        else:  # 其他日期
            if 20 <= current_hour or current_hour < 2:
                return True, "当前处于晚场开放时间"
                
        return False, "当前不在战场开放时间范围内"

    def run(self):
        """线程运行函数"""
        self.running = True
        self.log_signal.emit(f"脚本已启动，使用 {self.config['skill_key'].upper()} 键作为连招按键")
        
        # 检查时间
        is_open, message = self.check_battle_time()
        if not is_open:
            self.log_signal.emit(message)
            self.status_signal.emit("已停止：不在开放时间")
            self.running = False
            return
            
        self.log_signal.emit(message)
        
        while self.running:
            try:
                if keyboard.is_pressed(self.config['exit_key']):
                    self.stop()
                    break
                
                self.main_loop()
                time.sleep(self.config['check_interval'])
                
            except Exception as e:
                self.log_signal.emit(f"发生错误: {str(e)}")
                time.sleep(5)

    def stop(self):
        """停止脚本"""
        self.running = False
        self.log_signal.emit("脚本已停止")
        self.release_skill_key()

    def click_position(self, x, y):
        """模拟鼠标点击"""
        pyautogui.click(x, y)
        time.sleep(0.5)

    def press_skill_key(self):
        """按下技能键"""
        keyboard.press(self.config['skill_key'])
        
    def release_skill_key(self):
        """释放技能键"""
        keyboard.release(self.config['skill_key'])

    def follow_teammate(self):
        """按G键跟随队友"""
        logger.debug("按下G键开始跟随")
        keyboard.press(self.config['follow_key'])
        time.sleep(0.1)
        keyboard.release(self.config['follow_key'])

    def check_death(self):
        """检查是否死亡"""
        try:
            death_icon = self.find_image('assets/healing_point.png')
            logger.debug(f"死亡检测结果: {death_icon}")
            return death_icon is not None
        except Exception as e:
            logger.error(f"检测死亡状态时发生错误: {str(e)}")
            return False

    def check_ready_button(self):
        """检查是否出现就位确认按钮"""
        try:
            ready_button = self.find_image('assets/ready_button.png')
            logger.debug(f"就位按钮检测结果: {ready_button}")
            if ready_button:
                self.log_signal.emit("检测到就位按钮，自动确认...")
                self.click_position(ready_button.left + ready_button.width/2,
                                 ready_button.top + ready_button.height/2)
                return True
        except Exception as e:
            logger.error(f"检测就位按钮时发生错误: {str(e)}")
        return False

    def switch_target(self):
        """切换目标"""
        logger.debug("按下Tab键切换目标")
        keyboard.press('tab')
        time.sleep(0.1)
        keyboard.release('tab')

    def check_power_state(self):
        """检查是否可以激活强力状态"""
        try:
            power_icon = self.find_image('assets/power_state.png')
            logger.debug(f"强力状态检测结果: {power_icon}")
            if power_icon:
                self.log_signal.emit("检测到可激活强力状态，正在激活...")
                self.activate_power_state()
                return True
        except Exception as e:
            logger.error(f"检测强力状态时发生错误: {str(e)}")
        return False

    def activate_power_state(self):
        """激活强力状态"""
        logger.debug("按下F键激活强力状态")
        keyboard.press(self.config['power_key'])
        time.sleep(0.1)
        keyboard.release(self.config['power_key'])

    def close_all_windows(self):
        """关闭所有结算界面
        
        Returns:
            bool: 是否成功关闭所有界面
        """
        retry_count = 0
        max_retries = 5  # 最大重试次数
        
        while retry_count < max_retries:
            try:
                # 查找所有关闭按钮
                close_buttons = self.find_all_images('assets/close_button.png')
                logger.debug(f"找到 {len(close_buttons)} 个关闭按钮")
                
                if not close_buttons:  # 如果没有找到任何关闭按钮
                    if retry_count > 0:  # 如果不是第一次检查，说明之前的按钮都已经关闭
                        logger.debug("没有找到更多关闭按钮，认为已全部关闭")
                        return True
                    else:  # 如果是第一次检查就没找到，可能是图片识别问题
                        logger.debug("未找到任何关闭按钮，等待后重试")
                        time.sleep(1)
                        retry_count += 1
                        continue
                
                # 点击所有找到的关闭按钮
                for button in close_buttons:
                    self.log_signal.emit(f"正在关闭结算界面 ({close_buttons.index(button) + 1}/{len(close_buttons)})...")
                    self.click_position(button.left + button.width/2,
                                     button.top + button.height/2)
                    time.sleep(0.5)  # 等待动画效果
                
                time.sleep(1)  # 等待界面完全关闭
                retry_count += 1
                
            except Exception as e:
                logger.error(f"关闭结算界面时发生错误: {str(e)}")
                return False
        
        # 最后再检查一次是否还有未关闭的界面
        try:
            remaining_buttons = self.find_all_images('assets/close_button.png')
            if remaining_buttons:
                logger.error(f"仍有 {len(remaining_buttons)} 个界面未能关闭")
                return False
        except Exception as e:
            logger.error(f"最终检查时发生错误: {str(e)}")
            return False
            
        return True

    def check_buy_medicine(self):
        """检查是否出现购买药品界面"""
        try:
            buy_medicine = self.find_image('assets/buy_medicine.png')
            logger.debug(f"购买药品界面检测结果: {buy_medicine}")
            if buy_medicine:
                self.log_signal.emit("检测到购买药品界面，点击取消...")
                # 查找取消按钮
                try:
                    cancel_button = self.find_image('assets/medicine_cancel.png')
                    if cancel_button:
                        self.click_position(cancel_button.left + cancel_button.width/2,
                                         cancel_button.top + cancel_button.height/2)
                        return True
                except Exception as e:
                    logger.error(f"查找药品界面取消按钮时发生错误: {str(e)}")
        except Exception as e:
            logger.error(f"检测购买药品界面时发生错误: {str(e)}")
        return False

    def battle_cycle(self):
        """单次战斗循环"""
        # 开始跟随
        self.log_signal.emit("开始跟随队友...")
        self.follow_teammate()
        
        # 第一次进入战场时等待1分钟让队伍集合
        self.log_signal.emit("等待60秒让队伍集合...")
        time.sleep(self.config['first_follow_duration'])
        
        # 开始战斗（保持跟随状态）
        self.log_signal.emit("开始战斗...")
        self.press_skill_key()
        
        battle_end_detected = False  # 用于标记是否检测到战斗结束
        last_tab_time = time.time()  # 记录上次按Tab键的时间
        
        while self.running:
            current_time = time.time()
            
            # 检查是否需要切换目标
            if current_time - last_tab_time >= self.config['tab_interval']:
                self.switch_target()
                last_tab_time = current_time
            
            # 检查是否死亡
            if self.check_death():
                self.log_signal.emit("检测到死亡状态，等待复活...")
                self.release_skill_key()
                
                # 等待复活
                while self.running and self.check_death():
                    time.sleep(1)
                
                if not self.running:
                    return
                
                self.log_signal.emit("已复活，重新开始战斗循环...")
                # 重新开始跟随（复活后只等待15秒）
                self.follow_teammate()
                self.log_signal.emit("等待15秒让队伍集合...")
                time.sleep(self.config['follow_duration'])
                self.press_skill_key()
                last_tab_time = time.time()  # 重置Tab键计时器
            
            # 检查是否需要就位确认
            self.check_ready_button()
            
            # 检查是否可以激活强力状态
            self.check_power_state()
            
            # 检查是否出现购买药品界面
            self.check_buy_medicine()
            
            # 检查战斗是否结束
            try:
                battle_end = self.find_image('assets/battle_end.png')
                in_battle = self.find_image('assets/in_battle.png')
                if not in_battle:
                    in_battle = self.find_image('assets/in_battle.png', confidence=0.6)
                
                # 检测到战斗结束图标
                if battle_end and not battle_end_detected:
                    self.log_signal.emit("检测到战斗结束，等待退出战场...")
                    battle_end_detected = True
                    self.release_skill_key()
                
                # 如果已经检测到战斗结束，且已经退出战场（in_battle图标消失）
                if battle_end_detected and not in_battle:
                    self.log_signal.emit("已退出战场，处理结算...")
                    self.battle_count += 1
                    self.status_signal.emit(f"已完成 {self.battle_count} 场战斗")
                    
                    # 等待3秒确保结算界面完全加载
                    time.sleep(3)
                    
                    # 关闭所有结算界面
                    if not self.close_all_windows():
                        self.log_signal.emit("无法完全关闭结算界面，重试中...")
                        return
                    
                    # 等待2秒确保界面完全关闭
                    time.sleep(2)
                    
                    # 检查时间
                    is_open, message = self.check_battle_time()
                    if not is_open:
                        self.log_signal.emit(message)
                        self.stop()
                    else:
                        self.log_signal.emit(message)
                    
                    return
                    
            except Exception as e:
                logger.error(f"检查战斗状态时发生错误: {str(e)}")
            
            time.sleep(1)

    def main_loop(self):
        """主循环逻辑"""
        try:
            # 首先检查是否已在战场中
            in_battle = self.find_image('assets/in_battle.png', 'in_battle')
            
            # 如果已在战场中，直接进入战斗循环
            if in_battle:
                self.log_signal.emit("检测到已在战场中，开始战斗循环...")
                logger.debug("检测到已在战场状态，直接开始战斗循环")
                self.battle_cycle()
                return

            # 如果不在战场中，执行正常的进入战场流程
            self.status_signal.emit("寻找战场图标...")
            logger.debug("开始查找战场图标...")
            
            battle_icon = self.find_image('assets/battle_icon.png', 'battle_icon')
            
            if battle_icon:
                self.log_signal.emit("找到战场图标，点击进入...")
                logger.debug(f"战场图标位置: x={battle_icon.left}, y={battle_icon.top}")
                self.click_position(battle_icon.left + battle_icon.width/2, 
                                 battle_icon.top + battle_icon.height/2)
                time.sleep(2)
                
                # 2. 查找并点击单人匹配按钮
                self.status_signal.emit("查找单人匹配按钮...")
                match_button = self.find_image('assets/match_button.png', 'match_button')
                
                if match_button:
                    self.log_signal.emit("找到单人匹配按钮，开始匹配...")
                    logger.debug(f"匹配按钮位置: x={match_button.left}, y={match_button.top}")
                    self.click_position(match_button.left + match_button.width/2,
                                     match_button.top + match_button.height/2)
                    time.sleep(2)
                else:
                    self.log_signal.emit("未找到单人匹配按钮，重试中...")
                    return
                
                # 3. 等待匹配
                self.status_signal.emit("等待匹配中...")
                wait_match_time = time.time()
                match_success = False
                
                while self.running:
                    matching_icon = self.find_image('assets/matching.png', 'matching')
                    logger.debug(f"匹配中图标查找结果: {matching_icon}")
                    
                    if matching_icon:
                        current_wait_time = time.time() - wait_match_time
                        if current_wait_time > 300:  # 5分钟超时
                            self.log_signal.emit("匹配超时，重新开始...")
                            logger.debug(f"匹配超时，已等待: {current_wait_time:.1f}秒")
                            cancel_button = self.find_image('assets/cancel_match.png')
                            if cancel_button:
                                self.click_position(cancel_button.left + cancel_button.width/2,
                                                 cancel_button.top + cancel_button.height/2)
                            time.sleep(2)
                            return
                        time.sleep(1)
                        continue
                    
                    if not match_success:
                        self.log_signal.emit("匹配成功，等待进入战场...")
                        logger.debug("检测到匹配界面消失，进入loading等待状态")
                        match_success = True
                        time.sleep(self.config['loading_wait'])  # 等待loading
                        logger.debug("loading等待完成，开始检查战场状态")
                    
                    # 检查是否已进入战场
                    in_battle = self.find_image('assets/in_battle.png', 'in_battle')
                    
                    if in_battle:
                        self.log_signal.emit("已进入战场，开始战斗循环...")
                        logger.debug("成功识别到战场状态，开始战斗循环")
                        self.battle_cycle()  # 使用新的战斗循环
                        break
                    
                    current_total_time = time.time() - wait_match_time
                    if match_success and current_total_time > 60:  # 给60秒的总缓冲时间
                        self.log_signal.emit("进入战场超时，重新开始...")
                        logger.debug(f"进入战场超时，已等待: {current_total_time:.1f}秒")
                        return
                    
                    time.sleep(1)
                
        except Exception as e:
            logger.exception("执行过程中发生异常")
            self.log_signal.emit(f"执行过程中出错: {str(e)}")
            self.release_skill_key()

class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.battle_thread = None
        # 定义支持的按键映射
        self.key_mapping = {
            # 字母键
            'A': 'a', 'B': 'b', 'C': 'c', 'D': 'd', 'E': 'e',
            'F': 'f', 'G': 'g', 'H': 'h', 'I': 'i', 'J': 'j',
            'K': 'k', 'L': 'l', 'M': 'm', 'N': 'n', 'O': 'o',
            'P': 'p', 'Q': 'q', 'R': 'r', 'S': 's', 'T': 't',
            'U': 'u', 'V': 'v', 'W': 'w', 'X': 'x', 'Y': 'y', 'Z': 'z',
            # 功能键
            'F1': 'f1', 'F2': 'f2', 'F3': 'f3', 'F4': 'f4',
            'F5': 'f5', 'F6': 'f6', 'F7': 'f7', 'F8': 'f8',
            'F9': 'f9', 'F10': 'f10', 'F11': 'f11', 'F12': 'f12',
            # 数字键
            '0': '0', '1': '1', '2': '2', '3': '3', '4': '4',
            '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',
            # 小键盘
            'NUM0': 'num0', 'NUM1': 'num1', 'NUM2': 'num2', 'NUM3': 'num3',
            'NUM4': 'num4', 'NUM5': 'num5', 'NUM6': 'num6', 'NUM7': 'num7',
            'NUM8': 'num8', 'NUM9': 'num9',
            # 其他常用键
            'SPACE': 'space', 'TAB': 'tab', 'SHIFT': 'shift',
            'CTRL': 'ctrl', 'ALT': 'alt'
        }
        
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.initUI()
        
    def initUI(self):
        """初始化UI"""
        self.setWindowTitle('逆水寒战场助手')
        self.setFixedSize(400, 400)  # 增加窗口高度
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 按键设置区域
        key_layout = QVBoxLayout()
        
        # 按键输入说明
        key_help = QLabel('支持的按键格式：\n'
                         '- 字母键：直接输入字母（如：A、B、V）\n'
                         '- 功能键：直接输入F+数字（如：F4、F5）\n'
                         '- 小键盘：输入NUM+数字（如：NUM1、NUM0）\n'
                         '- 数字键：直接输入数字（如：1、2、3）')
        key_help.setStyleSheet('color: gray;')
        key_layout.addWidget(key_help)
        
        # 按键输入框
        input_layout = QHBoxLayout()
        key_label = QLabel('连招按键:')
        self.key_input = QLineEdit('F4')
        self.key_input.setMaximumWidth(100)
        self.key_input.textChanged.connect(self.validate_key_input)
        input_layout.addWidget(key_label)
        input_layout.addWidget(self.key_input)
        input_layout.addStretch()
        key_layout.addLayout(input_layout)
        
        layout.addLayout(key_layout)
        
        # 状态标签
        self.status_label = QLabel('当前状态: 未运行')
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 战斗次数标签
        self.count_label = QLabel('战斗次数: 0')
        self.count_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.count_label)
        
        # 日志标签
        self.log_label = QLabel('日志')
        self.log_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.log_label)
        
        # 开始按钮
        self.start_button = QPushButton('开始')
        self.start_button.clicked.connect(self.toggle_script)
        layout.addWidget(self.start_button)
        
    def validate_key_input(self):
        """验证按键输入"""
        key = self.key_input.text().upper()
        if key in self.key_mapping:
            self.key_input.setStyleSheet('')
            self.start_button.setEnabled(True)
        else:
            self.key_input.setStyleSheet('background-color: #FFE4E1;')
            self.start_button.setEnabled(False)
            
    def toggle_script(self):
        """切换脚本运行状态"""
        if self.battle_thread is None or not self.battle_thread.running:
            self.start_script()
        else:
            self.stop_script()
            
    def start_script(self):
        """启动脚本"""
        self.battle_thread = BattleThread()
        # 设置连招按键
        key = self.key_input.text().upper()
        if key in self.key_mapping:
            self.battle_thread.config['skill_key'] = self.key_mapping[key]
            self.battle_thread.log_signal.connect(self.update_log)
            self.battle_thread.status_signal.connect(self.update_status)
            self.battle_thread.start()
            self.start_button.setText('停止')
            self.status_label.setText('当前状态: 运行中')
            # 禁用按键输入
            self.key_input.setEnabled(False)
        else:
            self.log_label.setText('错误：无效的按键设置')
        
    def stop_script(self):
        """停止脚本"""
        if self.battle_thread:
            self.battle_thread.stop()
            self.battle_thread.wait()
            self.battle_thread = None
        self.start_button.setText('开始')
        self.status_label.setText('当前状态: 已停止')
        # 启用按键输入
        self.key_input.setEnabled(True)
        
    def update_log(self, message):
        """更新日志"""
        self.log_label.setText(message)
        
    def update_status(self, status):
        """更新状态"""
        if status.startswith('已完成'):
            self.count_label.setText(status)
        else:
            self.status_label.setText(f'当前状态: {status}')
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.stop_script()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
import sys
import cv2
import numpy as np
import pyautogui
import win32gui
import win32con
import time
from PIL import ImageGrab
import keyboard
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, 
                           QVBoxLayout, QWidget, QLineEdit, QHBoxLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

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
        }
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5
        self.battle_count = 0

    def check_battle_time(self):
        """检查当前是否在战场开放时间内"""
        current_time = time.localtime()
        current_hour = current_time.tm_hour
        current_wday = current_time.tm_wday  # 0-6, 0是周一
        
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
                
                # 定期检查时间（每10分钟检查一次）
                if self.battle_count % 10 == 0:
                    is_open, message = self.check_battle_time()
                    if not is_open:
                        self.log_signal.emit(message)
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

    def main_loop(self):
        """主循环逻辑"""
        try:
            # 1. 查找战场图标
            self.status_signal.emit("寻找战场图标...")
            battle_icon = pyautogui.locateOnScreen('assets/battle_icon.png', confidence=0.8)
            if battle_icon:
                self.log_signal.emit("找到战场图标，点击进入...")
                self.click_position(battle_icon.left + battle_icon.width/2, 
                                 battle_icon.top + battle_icon.height/2)
                time.sleep(2)
                
                # 2. 查找并点击单人匹配按钮
                self.status_signal.emit("查找单人匹配按钮...")
                match_button = pyautogui.locateOnScreen('assets/match_button.png', confidence=0.8)
                if match_button:
                    self.log_signal.emit("找到单人匹配按钮，开始匹配...")
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
                    # 检查是否在匹配中
                    if pyautogui.locateOnScreen('assets/matching.png', confidence=0.8):
                        if time.time() - wait_match_time > 300:  # 5分钟超时
                            self.log_signal.emit("匹配超时，重新开始...")
                            # 点击取消匹配按钮
                            cancel_button = pyautogui.locateOnScreen('assets/cancel_match.png', confidence=0.8)
                            if cancel_button:
                                self.click_position(cancel_button.left + cancel_button.width/2,
                                                 cancel_button.top + cancel_button.height/2)
                            time.sleep(2)
                            return
                        time.sleep(1)
                        continue
                        
                    # 如果匹配界面消失，说明可能进入了loading状态
                    if not match_success:
                        self.log_signal.emit("匹配成功，等待进入战场...")
                        match_success = True
                        # 给loading界面足够的时间
                        time.sleep(15)  # 等待15秒让loading完成
                        
                    # 检查是否已进入战场（尝试多个特征图片）
                    if (pyautogui.locateOnScreen('assets/in_battle.png', confidence=0.8) or 
                        pyautogui.locateOnScreen('assets/in_battle_alt.png', confidence=0.8)):
                        self.log_signal.emit("已进入战场，开始自动战斗...")
                        self.press_skill_key()
                        break
                        
                    # 如果既没有匹配中的提示，也没有进入战场，且已经过了loading时间
                    if match_success and time.time() - wait_match_time > 30:  # 给30秒的总缓冲时间
                        self.log_signal.emit("进入战场超时，重新开始...")
                        return
                        
                    time.sleep(1)
                
                # 4. 检测战斗结束
                self.status_signal.emit("战斗中...")
                battle_start_time = time.time()
                while self.running:
                    # 检查战斗是否结束
                    if pyautogui.locateOnScreen('assets/battle_end.png', confidence=0.8):
                        self.log_signal.emit("战斗结束，处理结算...")
                        self.release_skill_key()
                        self.battle_count += 1
                        self.status_signal.emit(f"已完成 {self.battle_count} 场战斗")
                        # 点击关闭结算界面
                        self.click_position(960, 540)
                        time.sleep(2)
                        break
                    
                    # 战斗超时保护（10分钟）
                    if time.time() - battle_start_time > 600:
                        self.log_signal.emit("战斗时间过长，可能出现异常，重新开始...")
                        self.release_skill_key()
                        return
                        
                    time.sleep(1)
                    
        except Exception as e:
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
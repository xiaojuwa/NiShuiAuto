# 逆水寒战场助手

这是一个用于逆水寒游戏的战场自动化助手程序。它可以帮助玩家自动进行战场战斗，解放双手。

## 主要功能

- ✨ 自动检测战场开放时间
  - 下午场 (12:00-18:00)
  - 晚场 (20:00-02:00，周五为22:00-02:00)
  - 自动识别周六周日上午关闭时间
- 🎮 全自动战场流程
  - 自动点击战场图标
  - 自动进行单人匹配
  - 自动检测匹配状态
  - 自动处理超时情况
- ⚔️ 自动战斗
  - 支持自定义连招按键（默认F4）
  - 自动处理战斗结算
- 📊 状态监控
  - 实时显示运行状态
  - 显示战斗次数统计
  - 详细的日志记录

## 环境要求

- Windows 10/11
- Python 3.8 或更高版本
- 游戏分辨率：1920x1080
- 游戏需要在前台运行

## 编译步骤

1. 克隆或下载本项目：
```bash
git clone [项目地址]
cd NiShuiAuto
```

2. 安装依赖：
```bash
pip install -r requirements.txt
pip install pyinstaller
```

3. 准备资源文件：
   - 在游戏中截取以下界面元素，保存到 `assets` 目录：
     - `battle_icon.png`: 战场图标
     - `match_button.png`: 单人匹配按钮
     - `matching.png`: 匹配中状态提示
     - `cancel_match.png`: 取消匹配按钮
     - `in_battle.png`: 战场内的特征图像
     - `battle_end.png`: 结算界面特征图像

4. 编译程序：
```bash
python build.py
```
编译完成后，可执行文件将生成在 `dist` 目录下。

## 安装使用

1. 从 `dist` 目录获取 `NiShuiAuto.exe`
2. 确保 `assets` 目录与exe文件在同一目录下
3. 双击运行 `NiShuiAuto.exe`

## 使用说明

1. 运行前准备：
   - 打开逆水寒游戏
   - 确保游戏分辨率为1920x1080
   - 确保游戏窗口在最前端
   - 确保战场图标可见
   - 确保游戏内连招快捷键与程序设置一致

2. 按键设置说明：
   - 字母键设置：
     - 直接输入字母即可，如：V、B、C等
     - 不区分大小写
   - 功能键设置：
     - 直接输入F+数字，如：F4、F5、F12等
   - 小键盘数字设置：
     - 输入NUM+数字，如：NUM1、NUM2、NUM0等
     - 必须大写NUM
   - 普通数字键设置：
     - 直接输入数字即可，如：1、2、3等
   - 其他特殊键：
     - 空格键：输入SPACE
     - Tab键：输入TAB
     - Shift键：输入SHIFT
     - Ctrl键：输入CTRL
     - Alt键：输入ALT

3. 使用步骤：
   - 启动程序
   - 在连招按键输入框中设置你想要的按键
   - 输入正确时输入框显示正常，错误时显示红色背景
   - 点击"开始"按钮（无效按键时按钮会被禁用）
   - 程序会自动检查时间并开始运行
   - 可以随时点击"停止"按钮或按ESC键停止

4. 注意事项：
   - 运行过程中请勿遮挡游戏界面
   - 请勿在游戏最小化时运行
   - 建议在安全环境下使用
   - 如果识别不准确，可能需要重新截取特征图片
   - 按键设置后无法在运行时更改，需要停止后才能修改

## 常见问题

1. 程序无法启动
   - 检查是否已安装所需的依赖
   - 检查assets目录是否完整

2. 识别不准确
   - 重新截取特征图片
   - 确保游戏分辨率正确
   - 检查游戏界面是否被遮挡

3. 按键无响应
   - 确保游戏窗口在最前端
   - 检查设置的按键是否被其他程序占用
   - 确认游戏内连招快捷键设置是否正确
   - 检查按键输入格式是否正确（参考按键设置说明）

4. 按键输入显示红色
   - 检查输入格式是否正确
   - 确认是否使用了支持的按键
   - 小键盘数字需要加上"NUM"前缀

## 免责声明

本程序仅供学习交流使用，请勿用于商业用途。使用本程序可能违反游戏用户协议，请谨慎使用，风险自负。
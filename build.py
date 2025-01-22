import PyInstaller.__main__
import os
import shutil
import sys

def build_exe(debug=False):
    # 清理之前的构建
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')
        
    # 基本打包选项
    options = [
        'src/main.py',
        '--name=NiShuiAuto',
        '--onefile',
        '--icon=assets/icon.ico',
        '--add-data=assets;assets',
    ]
    
    # 调试模式特定选项
    if debug:
        options.extend([
            '--console',  # 显示控制台窗口
            '--debug=all',  # 启用所有调试选项
            '--name=NiShuiAuto_debug',  # 调试版本使用不同的名称
        ])
    else:
        options.extend([
            '--windowed',
            '--noconsole',
        ])
    
    # PyInstaller打包命令
    PyInstaller.__main__.run(options)
    
    # 复制必要文件到dist目录
    shutil.copytree('assets', 'dist/assets', dirs_exist_ok=True)
    
    # 输出提示信息
    exe_name = 'NiShuiAuto_debug.exe' if debug else 'NiShuiAuto.exe'
    print(f"\n构建完成！可执行文件位置: dist/{exe_name}")
    if debug:
        print("调试模式已启用，程序运行时将显示控制台窗口和详细日志")
    
if __name__ == '__main__':
    # 解析命令行参数
    debug_mode = '--debug' in sys.argv
    build_exe(debug=debug_mode) 
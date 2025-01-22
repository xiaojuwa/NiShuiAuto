import PyInstaller.__main__
import os
import shutil

def build_exe():
    # 清理之前的构建
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')
        
    # PyInstaller打包命令
    PyInstaller.__main__.run([
        'src/main.py',
        '--name=NiShuiAuto',
        '--windowed',
        '--onefile',
        '--icon=assets/icon.ico',
        '--add-data=assets;assets',
        '--noconsole',
    ])
    
    # 复制必要文件到dist目录
    shutil.copytree('assets', 'dist/assets', dirs_exist_ok=True)
    
if __name__ == '__main__':
    build_exe() 
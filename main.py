import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.styles.style_manager import StyleManager

def main():
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 应用样式
    StyleManager.apply_style(app)
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 启动事件循环
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 